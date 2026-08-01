package domain

import (
	"context"
	"strings"
	"testing"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// *hana.DB must satisfy Runner, or the domain tools would need a second, private
// way into the database — which is exactly the privileged bypass this design
// exists to avoid.
var _ Runner = (*hana.DB)(nil)

// TestDomainStatementsPassGuard is the proof that the domain tools are not a
// side door.
//
// Every statement this package can send goes through guard.Check under
// guard.MCPPolicy — the SAME layers 0-3 a user's hana_query SQL passes — and this
// test asserts that all of them clear it. It mirrors internal/hana's
// TestCatalogSQLPassesGuard, and it exists so the fix for a template the guard
// refuses can only ever be the template. NEVER relax internal/guard to make one
// of these pass.
func TestDomainStatementsPassGuard(t *testing.T) {
	stmts := Statements()
	// 4 company sets (ALL + each of the three) x (8 sales variants x 2 combo-group
	// outcomes + 1 turnover + 2 payment directions + 1 variety catalogue + 1 combo
	// catalogue) = 4 x 21 = 84.
	if len(stmts) != 84 {
		t.Fatalf("Statements() returned %d variants, want 84; the guard proof is meant to cover every branch "+
			"(company sets x include_type x net_credit_notes x variety x resolved/unresolved combo group x both payment directions x the two catalogues)", len(stmts))
	}
	for i, s := range stmts {
		if err := guard.Check(s, guard.MCPPolicy); err != nil {
			t.Errorf("statement %d is refused by the read-only guard: %v\n%s", i, err, s)
		}
	}
}

// The guard is genuinely being exercised: a write built the same way is still
// refused. Without this, a broken guard.Check would make the test above pass
// vacuously.
func TestGuardStillRefusesAWriteShapedLikeADomainQuery(t *testing.T) {
	stmt := `WITH AGG AS (SELECT 1 AS X FROM DUMMY) UPDATE "JIVO_OIL_HANADB"."OCRD" SET "Balance" = 0`
	if err := guard.Check(stmt, guard.MCPPolicy); err == nil {
		t.Fatal("the guard accepted a write; the coverage test above proves nothing")
	}
}

// Every statement the public entry points actually SEND must be one of the
// variants Statements() enumerates. Otherwise a new branch could ship with no
// guard coverage while the test above still passes.
func TestEveryStatementSentIsCoveredByStatements(t *testing.T) {
	covered := map[string]bool{}
	for _, s := range Statements() {
		covered[normalizeSQL(s)] = true
	}

	sent := map[string]string{} // normalized -> label
	record := func(label string, r *recordingRunner) {
		for _, s := range r.stmts {
			sent[normalizeSQL(s)] = label
		}
	}

	w := struct{ from, to string }{"2026-06-01", "2026-06-30"}
	// Every company a caller can name, not just ALL and Oil: a Mart-only or
	// Beverages-only statement is a statement this package sends, so it has to be
	// one the guard proof covers.
	for _, company := range []string{"ALL", "Oil", "Mart", "Beverages"} {
		for _, includeType := range []bool{false, true} {
			for _, netCN := range []bool{false, true} {
				for _, variety := range []string{"", "OLIVE"} {
					r := newRecordingRunner(salesResult())
					_, err := SalesByVariety(context.Background(), r, SalesRequest{
						From: w.from, To: w.to, Company: company,
						Variety: variety, IncludeType: includeType, NetCreditNotes: netCN,
					})
					if err != nil {
						t.Fatalf("SalesByVariety(%s, type=%v, cn=%v, variety=%q): %v", company, includeType, netCN, variety, err)
					}
					record("sales", r)
				}
			}
		}
		r := newRecordingRunner(turnoverResult())
		if _, err := Turnover(context.Background(), r, TurnoverRequest{From: w.from, To: w.to, Company: company}); err != nil {
			t.Fatalf("Turnover(%s): %v", company, err)
		}
		record("turnover", r)

		for _, d := range []Direction{Outgoing, Incoming} {
			r := newRecordingRunner(paymentsResult())
			if _, err := Payments(context.Background(), r, PaymentsRequest{
				Direction: d, From: w.from, To: w.to, Company: company}); err != nil {
				t.Fatalf("Payments(%s, %s): %v", company, d, err)
			}
			record("payments", r)
		}
	}

	if len(sent) == 0 {
		t.Fatal("no statements were recorded; the test is not exercising anything")
	}
	for s, label := range sent {
		if !covered[s] {
			t.Errorf("the %s tool sends a statement that Statements() does not enumerate, so it has NO guard coverage:\n%s", label, s)
		}
	}
}

// normalizeSQL compares statements on their tokens, not their whitespace, and
// with the bound dates ignored — Statements() uses representative dates, the
// callers use whatever the operator asked for. Dates are bind parameters, so
// they are not part of the statement text anyway; this only guards against an
// accidental future interpolation being papered over.
func normalizeSQL(s string) string {
	return strings.Join(strings.Fields(s), " ")
}
