package domain

import (
	"context"
	"strings"
	"testing"

	"hana-sql/internal/hana"
)

// --- a truncated answer may not assert a genuine zero ---------------------------

// THE DEFECT. shape() applied its emptyNote regardless of res.Truncated, and
// every caller's emptyNote asserts a real zero in as many words:
//
//	sales:    "that is a real zero, not a filter that failed … this window
//	           genuinely has no matching sales here"
//	turnover: "a genuine zero, not a filter that failed"
//	payments: "treat this as a fault to investigate, not as a zero"
//
// With Truncated = true, a company whose rows were DROPPED by the row cap got
// that sentence — "genuinely has no matching sales" sitting in the same payload
// as `"truncated": true`. Reachability is low (the widest all-time grouping
// measured 154 rows against a 1000-row cap, and the deployed environment sets no
// override), but the failure mode is the worst one this package has: a confident
// zero for a company that sold something.
func TestTruncatedAnswerNeverClaimsAGenuineZero(t *testing.T) {
	// One row for Oil only, and the cap tripped. Mart and Beverages have no rows —
	// which under truncation proves nothing at all about them.
	truncated := &hana.Result{
		Rows: []map[string]any{{
			AsOfColumn: fakeAsOf, "COMPANY": "Oil", "VARIETY": "OLIVE",
			"EXTERNAL_NET": 39909813.16, "INTERNAL_RELATED_PARTY": 75586610.0,
			"GROSS_NET_OF_GST": 115496423.16, "LINE_COUNT": int64(4211),
		}},
		RowCount:  1,
		Truncated: true,
	}

	sales := mustSales(t, newRecordingRunner(truncated),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: AllCompanies, NetCreditNotes: true})
	if !sales.Truncated {
		t.Fatal("the response does not carry truncated=true; the rest of this test is vacuous")
	}
	assertNoZeroClaim(t, "sales", sales)

	turn, err := Turnover(context.Background(), newRecordingRunner(truncated),
		TurnoverRequest{From: "2026-06-01", To: "2026-06-30", Company: AllCompanies})
	if err != nil {
		t.Fatal(err)
	}
	assertNoZeroClaim(t, "turnover", turn)

	pay, err := Payments(context.Background(), newRecordingRunner(truncated),
		PaymentsRequest{Direction: Outgoing, From: "2026-06-01", To: "2026-06-30", Company: AllCompanies})
	if err != nil {
		t.Fatal(err)
	}
	assertNoZeroClaim(t, "payments", pay)
}

// assertNoZeroClaim fails if an empty block in a TRUNCATED answer still asserts
// the emptiness was measured.
func assertNoZeroClaim(t *testing.T, label string, res *Response) {
	t.Helper()
	empty := 0
	for _, b := range res.Companies {
		if len(b.Rows) > 0 {
			continue
		}
		empty++
		for _, claim := range []string{
			"real zero",
			"genuine zero",
			"genuinely has no matching sales",
			"not a filter that failed",
			"not as a zero",
		} {
			if strings.Contains(b.Note, claim) {
				t.Errorf("%s: %s has no rows in a TRUNCATED answer but its note still claims %q — the rows may simply have been dropped by the row cap: %q",
					label, b.Company, claim, b.Note)
			}
		}
		if !strings.Contains(b.Note, "INCOMPLETE") {
			t.Errorf("%s: %s's empty-block note does not say the answer was truncated: %q", label, b.Company, b.Note)
		}
	}
	if empty == 0 {
		t.Fatalf("%s: no empty company block in the fixture; the assertion is vacuous", label)
	}
}

// The same note is the RIGHT one when nothing was truncated: a genuine zero must
// still be reported as a genuine zero, or the fix has traded one ambiguity for
// another.
func TestUntruncatedEmptyBlockStillAssertsTheZero(t *testing.T) {
	sales := mustSales(t, newRecordingRunner(salesResult()),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: AllCompanies, NetCreditNotes: true})
	if sales.Truncated {
		t.Fatal("fixture is truncated; this test needs a complete answer")
	}
	found := false
	for _, b := range sales.Companies {
		if len(b.Rows) == 0 {
			found = true
			if !strings.Contains(b.Note, "real zero") {
				t.Errorf("%s's empty block no longer states the zero is real: %q", b.Company, b.Note)
			}
			if strings.Contains(b.Note, "INCOMPLETE") {
				t.Errorf("%s's block claims truncation on a complete answer: %q", b.Company, b.Note)
			}
		}
	}
	if !found {
		t.Fatal("no empty company block in the fixture; the assertion is vacuous")
	}
}

// --- the truncation advice must be actionable -----------------------------------

// hana.QueryReadOnly appends "aggregate server-side with SUM/COUNT/GROUP BY
// instead of paging rows" to any capped answer. For a hand-written hana_query
// that is right; inherited by a domain tool it is impossible to follow, because
// the statement IS the server-side aggregate and the caller has no argument that
// reshapes it. It is the same misdirection internal/hana already fixed for the
// catalog listing with catalogAdvice.
func TestDomainTruncationAdviceReplacesTheGenericOne(t *testing.T) {
	generic := hana.QueryTruncationAdvice()
	capped := &hana.Result{
		Rows: []map[string]any{{
			AsOfColumn: fakeAsOf, "COMPANY": "Oil", "VARIETY": "OLIVE",
			"EXTERNAL_NET": 1.0, "GROSS_NET_OF_GST": 1.0,
		}},
		RowCount:  1,
		Truncated: true,
		Note:      "row cap reached (1000 rows), so this answer is INCOMPLETE; " + generic,
	}

	sales := mustSales(t, newRecordingRunner(capped),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: AllCompanies, NetCreditNotes: true})
	turn, err := Turnover(context.Background(), newRecordingRunner(capped),
		TurnoverRequest{From: "2026-06-01", To: "2026-06-30", Company: AllCompanies})
	if err != nil {
		t.Fatal(err)
	}
	pay, err := Payments(context.Background(), newRecordingRunner(capped),
		PaymentsRequest{Direction: Outgoing, From: "2026-06-01", To: "2026-06-30", Company: AllCompanies})
	if err != nil {
		t.Fatal(err)
	}

	for label, note := range map[string]string{
		"sales": sales.Note, "turnover": turn.Note, "payments": pay.Note,
	} {
		if strings.Contains(note, generic) {
			t.Errorf("%s still carries the generic advice %q, which its caller cannot act on — the domain statement is already a server-side aggregate:\n%s", label, generic, note)
		}
		if !strings.Contains(note, DomainTruncationAdvice) {
			t.Errorf("%s does not carry the domain truncation advice, so a capped answer says nothing the caller can do:\n%s", label, note)
		}
		// The row-cap fact itself must survive the swap.
		if !strings.Contains(note, "INCOMPLETE") {
			t.Errorf("%s lost the row-cap warning entirely:\n%s", label, note)
		}
	}

	// The swap is anchored on the exported constant, so it cannot go stale
	// silently if internal/hana rewords its advice.
	if reframeTruncation("x "+generic+" y") != "x "+DomainTruncationAdvice+" y" {
		t.Error("reframeTruncation no longer matches hana.QueryTruncationAdvice()")
	}
	if reframeTruncation("") != "" {
		t.Error("reframeTruncation invented a note where there was none")
	}
}
