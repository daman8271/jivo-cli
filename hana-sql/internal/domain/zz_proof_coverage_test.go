package domain

// Proof's independent tests. Not the author's suite.
//
// TestDomainStatementsPassGuard proves every statement in Statements() clears
// the guard. It does NOT prove that Statements() is the set of statements that
// actually run — so a new template, or a new branch inside one, could execute
// against production while the guard proof quietly kept passing on the old set.
// These tests close that gap from the other end: drive the PUBLIC entry points,
// capture the SQL really handed to the Runner, and require each captured
// statement to be guard-clean AND present in Statements().

import (
	"context"
	"strings"
	"testing"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// proofRunner captures every statement executed and answers the variety
// pre-check so SalesByVariety can get past it with no database.
type proofRunner struct {
	stmts []string
	args  [][]any
}

func (r *proofRunner) QueryReadOnly(_ context.Context, p guard.Policy, _ hana.Limits, stmt string, args ...any) (*hana.Result, error) {
	r.stmts = append(r.stmts, stmt)
	r.args = append(r.args, args)
	// The variety catalogue pre-check: hand back a row per company so any
	// variety used below is considered known.
	if strings.Contains(stmt, `AS VARIETY, COUNT(*) AS ITEMS`) {
		var rows []map[string]any
		for _, c := range Companies() {
			rows = append(rows, map[string]any{"COMPANY": c.Name, "VARIETY": "OLIVE", "ITEMS": int64(66)})
		}
		return &hana.Result{Rows: rows}, nil
	}
	return &hana.Result{}, nil
}

// normalise strips the whitespace differences that carry no meaning, so the
// comparison is about the statement, not its formatting.
func normalise(s string) string { return strings.Join(strings.Fields(s), " ") }

// TestProofExecutedStatementsAreAllCoveredByTheGuardProof is the completeness
// check the author's suite is missing.
func TestProofExecutedStatementsAreAllCoveredByTheGuardProof(t *testing.T) {
	covered := map[string]bool{}
	for _, s := range Statements() {
		covered[normalise(s)] = true
	}

	ctx := context.Background()
	companies := []string{"", "ALL", "Oil", "Mart", "Beverages", "JIVO_OIL_HANADB"}

	r := &proofRunner{}
	for _, co := range companies {
		for _, withType := range []bool{false, true} {
			for _, netCN := range []bool{false, true} {
				for _, variety := range []string{"", "OLIVE", "olive"} {
					if _, err := SalesByVariety(ctx, r, SalesRequest{
						From: "2026-06-01", To: "2026-06-30", Company: co,
						Variety: variety, IncludeType: withType, NetCreditNotes: netCN,
					}); err != nil {
						t.Fatalf("SalesByVariety(company=%q variety=%q) failed: %v", co, variety, err)
					}
				}
			}
		}
		if _, err := Turnover(ctx, r, TurnoverRequest{From: "2026-07-01", To: "2026-07-28", Company: co}); err != nil {
			t.Fatalf("Turnover(company=%q) failed: %v", co, err)
		}
		for _, d := range []Direction{Outgoing, Incoming} {
			if _, err := Payments(ctx, r, PaymentsRequest{
				Direction: d, From: "2026-07-01", To: "2026-07-31", Company: co,
			}); err != nil {
				t.Fatalf("Payments(company=%q dir=%q) failed: %v", co, d, err)
			}
		}
	}

	if len(r.stmts) == 0 {
		t.Fatal("captured no statements at all — the test drove nothing")
	}
	seen := map[string]bool{}
	for i, s := range r.stmts {
		n := normalise(s)
		if seen[n] {
			continue
		}
		seen[n] = true
		if err := guard.Check(s, guard.MCPPolicy); err != nil {
			t.Errorf("executed statement %d is REFUSED by the read-only guard: %v\n%s", i, err, s)
		}
		if !covered[n] {
			t.Errorf("executed statement %d is NOT in Statements(), so the guard proof does not cover it:\n%s", i, s)
		}
	}
	t.Logf("drove %d executions, %d distinct statements, all guard-clean and all covered by Statements()",
		len(r.stmts), len(seen))
}

// TestProofEveryCallerValueIsBoundNeverInterpolated: no caller-supplied text may
// appear in the statement TEXT. Dates and varieties must arrive as binds.
func TestProofEveryCallerValueIsBoundNeverInterpolated(t *testing.T) {
	r := &proofRunner{}
	const marker = "OLIVE"
	if _, err := SalesByVariety(context.Background(), r, SalesRequest{
		From: "2026-06-01", To: "2026-06-30", Company: "Oil",
		Variety: marker, NetCreditNotes: true,
	}); err != nil {
		t.Fatal(err)
	}
	// The last statement is the sales query (the first is the variety catalogue,
	// which legitimately contains no caller text either).
	last := r.stmts[len(r.stmts)-1]
	for _, bad := range []string{"2026-06-01", "2026-06-30", "2026-07-01"} {
		if strings.Contains(last, bad) {
			t.Errorf("caller date %q was INTERPOLATED into the statement text, not bound:\n%s", bad, last)
		}
	}
	if strings.Contains(last, "'"+marker+"'") {
		t.Errorf("variety %q was interpolated as a literal, not bound:\n%s", marker, last)
	}
	args := r.args[len(r.args)-1]
	var found bool
	for _, a := range args {
		if s, ok := a.(string); ok && s == marker {
			found = true
		}
	}
	if !found {
		t.Errorf("variety %q never appeared in the bind parameters %v", marker, args)
	}
}

// TestProofWindowUpperBoundIsExclusiveNextDay checks the boundary arithmetic on
// the dates people actually get wrong: month ends, a leap day, a year end.
func TestProofWindowUpperBoundIsExclusiveNextDay(t *testing.T) {
	cases := []struct{ from, to, wantToBind string }{
		{"2026-06-01", "2026-06-30", "2026-07-01"},
		{"2026-01-01", "2026-12-31", "2027-01-01"},
		{"2024-02-01", "2024-02-29", "2024-03-01"}, // leap year
		{"2026-02-01", "2026-02-28", "2026-03-01"},
		{"2026-06-15", "2026-06-15", "2026-06-16"}, // single day
	}
	for _, c := range cases {
		w, err := ParseWindow(c.from, c.to)
		if err != nil {
			t.Fatalf("ParseWindow(%q,%q): %v", c.from, c.to, err)
		}
		if w.toBind != c.wantToBind {
			t.Errorf("ParseWindow(%q,%q) toBind = %q, want %q", c.from, c.to, w.toBind, c.wantToBind)
		}
		if !strings.Contains(w.Applied, c.wantToBind) {
			t.Errorf("Applied %q does not echo the bind %q it actually used", w.Applied, c.wantToBind)
		}
	}
	// 29 Feb in a NON-leap year must be refused, not silently rolled to 1 March.
	if _, err := ParseWindow("2026-02-01", "2026-02-29"); err == nil {
		t.Error("ParseWindow accepted 2026-02-29, a date that does not exist")
	}
}

// TestProofUnknownCompanyIsNeverAnEmptyAnswer: every near-miss must error.
func TestProofUnknownCompanyIsNeverAnEmptyAnswer(t *testing.T) {
	for _, bad := range []string{"Oill", "JIVO_BEVERAGE_HANADB", "oil ", "Beverage", "NOPE", "0", "ALL "} {
		got, err := ResolveCompanies(bad)
		if err != nil {
			continue // refusal: correct
		}
		// The only acceptable non-error results are the legitimate trims.
		switch strings.TrimSpace(bad) {
		case "oil", "Oil", "ALL":
		default:
			t.Errorf("ResolveCompanies(%q) returned %v with no error — a typo must never read as a real company set", bad, got)
		}
	}
}
