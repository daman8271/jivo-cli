package domain

import (
	"context"
	"strings"
	"testing"

	"hana-sql/internal/hana"
)

// --- the empty-string variety bucket --------------------------------------------

// COALESCE handles NULL and only NULL. An item tagged with the EMPTY STRING
// therefore produced a third, nameless bucket: VARIETY rendered as "", which is
// not '(UNTAGGED)', is not in the variety catalogue (buildVarietyCatalog
// explicitly excludes blank tags), is not offerable by the did-you-mean path,
// and cannot be filtered for either, because an empty variety argument is the
// no-filter sentinel. A model reading a blank variety row carrying real money
// has no way to interpret it.
func TestBlankVarietyTagsFallIntoUntagged(t *testing.T) {
	stmt, _ := buildSales([]Company{{Name: "Oil", Schema: "JIVO_OIL_HANADB"}},
		Window{fromBind: "2026-06-01", toBind: "2026-07-01"}, "", false, true, comboOil())

	// NULLIF is what folds the empty string in with NULL, and it has to be in the
	// SELECT and the GROUP BY alike or HANA would not even accept the statement.
	if n := strings.Count(stmt, `COALESCE(NULLIF(TRIM(itm."U_Sub_Group"), ''), '(UNTAGGED)')`); n != 2 {
		t.Fatalf("the variety expression appears %d times, want 2 (SELECT and GROUP BY) — an empty tag must land in '(UNTAGGED)', not in a nameless third bucket:\n%s", n, stmt)
	}
	if strings.Contains(stmt, `COALESCE(itm."U_Sub_Group", '(UNTAGGED)')`) {
		t.Fatalf("the NULL-only COALESCE is back; an item tagged with '' gets its own blank bucket again:\n%s", stmt)
	}
}

// A tag typed with a trailing space is the same variety, on both sides of the
// comparison. Untrimmed, 'OLIVE ' split into its own bucket AND could never be
// filtered for: an operator asking for OLIVE got it refused as an unknown tag.
func TestVarietyMatchingIsTrimmedOnBothSides(t *testing.T) {
	stmt, _ := buildSales([]Company{{Name: "Oil", Schema: "JIVO_OIL_HANADB"}},
		Window{fromBind: "2026-06-01", toBind: "2026-07-01"}, "OLIVE", false, false, comboOil())

	if !strings.Contains(stmt, `UPPER(TRIM(COALESCE(itm."U_Sub_Group", ''))) = UPPER(TRIM(?))`) {
		t.Fatalf("the variety filter does not TRIM both sides:\n%s", stmt)
	}
	catalog := buildVarietyCatalog(Companies())
	if !strings.Contains(catalog, `TRIM(itm."U_Sub_Group") AS VARIETY`) || !strings.Contains(catalog, `GROUP BY TRIM(itm."U_Sub_Group")`) {
		t.Fatalf("the variety catalogue does not TRIM, so 'OLIVE ' and 'OLIVE' would be offered as two valid values:\n%s", catalog)
	}

	// And the Go side accepts a catalogue value that carries the space.
	r := &recordingRunner{
		catalog: &hana.Result{Rows: []map[string]any{
			{"COMPANY": "Oil", "VARIETY": "OLIVE ", "ITEMS": int64(185)},
		}, RowCount: 1},
		agg: salesResult(),
	}
	if err := checkVariety(context.Background(), r, Companies(), "OLIVE"); err != nil {
		t.Fatalf("a tag stored as %q refused the variety %q: %v", "OLIVE ", "OLIVE", err)
	}
}

// --- the truncated variety catalogue --------------------------------------------

// The catalogue query runs under the same row cap as any other query
// (hana.DefaultMaxRows). A truncated answer means the variety may be sitting in
// the rows that were dropped — so a MISS is not evidence of absence, and
// "no item is tagged X, valid values are …" would be a confident refusal of a
// good variety with an incomplete list of alternatives attached.
func TestTruncatedVarietyCatalogueRefusesForTheRightReason(t *testing.T) {
	partial := &hana.Result{
		Rows:      []map[string]any{{"COMPANY": "Oil", "VARIETY": "CANOLA", "ITEMS": int64(90)}},
		RowCount:  1,
		Truncated: true,
	}
	r := &recordingRunner{catalog: partial, agg: salesResult()}

	err := checkVariety(context.Background(), r, Companies(), "OLIVE")
	if err == nil {
		t.Fatal("a truncated catalogue silently accepted an unchecked variety")
	}
	if !strings.Contains(err.Error(), "TRUNCATED") {
		t.Fatalf("the refusal does not say the list was truncated, so it reads as proof the tag does not exist: %v", err)
	}
	if strings.Contains(err.Error(), "no item is tagged") {
		t.Fatalf("a truncated catalogue still produced the definitive 'no item is tagged' refusal: %v", err)
	}

	// A HIT inside a partial list is still conclusive: finding it proves it exists.
	hit := &hana.Result{
		Rows:      []map[string]any{{"COMPANY": "Oil", "VARIETY": "OLIVE", "ITEMS": int64(185)}},
		RowCount:  1,
		Truncated: true,
	}
	if err := checkVariety(context.Background(), &recordingRunner{catalog: hit, agg: salesResult()}, Companies(), "OLIVE"); err != nil {
		t.Fatalf("a variety found in a truncated list was refused anyway: %v", err)
	}
}

// --- an empty window must read as zero, never as null ---------------------------

// buildTurnover and buildPayments' (ALL) block are UNGROUPED aggregates, so an
// empty window does not return zero rows: it returns exactly one row per company
// with COMPANY set and every SUM NULL. Without COALESCE, EXTERNAL_TURNOVER /
// GROSS_TURNOVER / TOTAL came back as JSON `null` rather than 0 — the same
// "no sales and no answer must not look the same" ambiguity the clock LEFT JOIN
// exists to prevent — and it fires in ordinary use, on any company=ALL window
// where one company posted nothing.
func TestUngroupedAggregatesCoalesceEverySumToZero(t *testing.T) {
	w := Window{fromBind: "2026-07-01", toBind: "2026-07-29"}

	turnover, _ := buildTurnover(Companies(), w)
	assertEverySumCoalesced(t, "turnover", turnover)

	for _, d := range []Direction{Outgoing, Incoming} {
		stmt, _ := buildPayments(Companies(), d, w)
		assertEverySumCoalesced(t, "payments "+string(d), stmt)
	}
}

// assertEverySumCoalesced fails unless every SUM( in the statement is wrapped in
// COALESCE. Counting is the point: a new money column added without the wrapper
// is exactly how a null gets back into an answer.
func assertEverySumCoalesced(t *testing.T, label, stmt string) {
	t.Helper()
	sums := strings.Count(stmt, "SUM(")
	wrapped := strings.Count(stmt, "COALESCE(SUM(")
	if sums == 0 {
		t.Fatalf("%s: no SUM( found at all, the assertion is vacuous:\n%s", label, stmt)
	}
	if sums != wrapped {
		t.Fatalf("%s: %d of %d SUM() are not wrapped in COALESCE, so an empty window returns null instead of 0:\n%s", label, sums-wrapped, sums, stmt)
	}
}

// The prose has to match what the DATABASE does, not what the SQL standard says.
//
// This test has now been wrong in both directions, which is the whole lesson.
// It first asserted that an empty window returns no rows and called that a
// "genuine zero". It was then rewritten to assert the opposite — that an
// ungrouped aggregate "always returns a row", so a missing row is a FAULT — on
// reasoning alone, and the payload started telling operators to "treat this as a
// fault to investigate, not as a zero".
//
// Measured against live HANA on 2026-08-01 (Oil, 1999-01-01..1999-01-02):
//
//	SELECT COUNT(*) FROM AGG                       -> 1
//	FROM (clock) c LEFT OUTER JOIN AGG a ON 1 = 1  -> one row, a.COMPANY NULL
//
// so through the clock join the caller sees NO company row. The reasoning was
// sound and the database disagreed; the database wins. An empty window is a
// genuine zero and must be reported as one, or every quiet month gets flagged to
// Accounts as a fault.
func TestZeroWindowProseSaysAnEmptyBlockIsAGenuineZero(t *testing.T) {
	turn, err := Turnover(context.Background(), newRecordingRunner(turnoverResult()),
		TurnoverRequest{From: "2026-07-01", To: "2026-07-28"})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(turn.Note, "GENUINE ZERO") {
		t.Fatalf("the turnover note does not say an empty block is a genuine zero:\n%s", turn.Note)
	}
	if strings.Contains(turn.Note, "explicit ZEROS") {
		t.Fatalf("the turnover note still promises a row of explicit zeros, which live HANA does not produce:\n%s", turn.Note)
	}
	pay, err := Payments(context.Background(), newRecordingRunner(paymentsResult()),
		PaymentsRequest{Direction: Outgoing, From: "2026-07-01", To: "2026-07-28"})
	if err != nil {
		t.Fatal(err)
	}
	for label, res := range map[string]*Response{"turnover": turn, "payments": pay} {
		for _, b := range res.Companies {
			if len(b.Rows) > 0 {
				continue
			}
			if strings.Contains(b.Note, "treat this as a fault") {
				t.Errorf("%s: %s's empty block is reported as a fault. An ungrouped aggregate over an empty window returns no row through the clock join on live HANA, so this fires on every quiet month: %q",
					label, b.Company, b.Note)
			}
			if !strings.Contains(b.Note, "GENUINE ZERO") {
				t.Errorf("%s: %s's empty block does not say it is a genuine zero: %q", label, b.Company, b.Note)
			}
		}
	}
}

// --- money must not vanish between EXTERNAL and INTERNAL ------------------------

// `t.CC IN (…)` AND `t.CC NOT IN (…)` both evaluate to NULL when "CardCode" is
// NULL, so neither CASE fires and that document's money lands in GROSS but in
// NEITHER bucket: EXTERNAL + INTERNAL quietly stops equalling GROSS. "CardCode"
// is mandatory on OINV/ORIN, so this is unlikely — but "money that disappears
// from a total" is the failure this package exists to prevent, and the invariant
// was neither enforced in SQL nor asserted anywhere.
func TestInternalExternalSplitIsNullSafe(t *testing.T) {
	w := Window{fromBind: "2026-06-01", toBind: "2026-07-01"}
	stmts := map[string]string{}
	sales, _ := buildSales(Companies(), w, "", false, true, comboAll())
	stmts["sales"] = sales
	turnover, _ := buildTurnover(Companies(), w)
	stmts["turnover"] = turnover

	for label, stmt := range stmts {
		// Every membership test that splits the money must go through the null-safe
		// expression, and the bare column must never appear in one.
		// Only the CARD-CODE membership tests are in scope; the combo item-group
		// IN list keys on an item column and cannot move money between buckets.
		ins := strings.Count(stmt, " IN ('CUSTA")
		safe := strings.Count(stmt, cardCodeExpr+" IN ('CUSTA") + strings.Count(stmt, cardCodeExpr+" NOT IN ('CUSTA")
		if ins == 0 {
			t.Fatalf("%s contains no card-code IN list at all; the assertion is vacuous", label)
		}
		if ins != safe {
			t.Fatalf("%s: %d of %d IN lists are not null-safe, so a NULL \"CardCode\" would drop out of both EXTERNAL and INTERNAL while staying in GROSS:\n%s",
				label, ins-safe, ins, stmt)
		}
		if strings.Contains(stmt, "WHEN t.CC ") {
			t.Fatalf("%s still compares a bare t.CC:\n%s", label, stmt)
		}
	}
}

// --- the basis-gap explanation --------------------------------------------------

// THE SHIPPED PROSE WAS EMPIRICALLY FALSE. Both tools explained the gap between
// them as header freight, and called it slight. Measured live 2026-08-01,
// OINV."TotalExpns" with "CANCELED" = 'N' is non-zero on 3 Oil invoices totalling
// Rs 22,500 ALL TIME and is Rs 0 in Mart and Beverages — real, but nowhere near
// the Rs 11.23 Cr it was offered to explain — and the freight story predicts the
// wrong SIGN into the bargain, since the LINE total is the higher one. A model
// asked why hana_turnover and hana_sales_by_variety disagree would confidently
// give Accounts a reason they cannot find in SAP, which is the exact class of
// defect this package exists to eliminate.
//
// The replacement must not overshoot either: an intermediate revision of this
// note claimed "TotalExpns" is 0.00 on EVERY non-cancelled A/R invoice, which is
// also false. This test pins the measured cause (branch stock-transfer invoices
// whose header carries only GST) and the measured magnitude.
func TestBasisGapIsNotExplainedAsFreight(t *testing.T) {
	sales := mustSales(t, newRecordingRunner(salesResult()),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil"})
	turn, err := Turnover(context.Background(), newRecordingRunner(turnoverResult()),
		TurnoverRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil"})
	if err != nil {
		t.Fatal(err)
	}

	texts := map[string]string{
		"sales note":     sales.Note,
		"sales basis":    sales.Basis,
		"turnover note":  turn.Note,
		"turnover basis": turn.Basis,
	}
	// The dead explanations, in the forms they were actually shipped in.
	for label, text := range texts {
		for _, dead := range []string{
			"includes header freight",
			"it includes header freight",
			"EXCLUDES header freight",
			"INCLUDES freight",
		} {
			if strings.Contains(text, dead) {
				t.Errorf("%s still explains the basis gap with %q — measured 2026-08-01, freight totals Rs 22,500 all-time against a Rs 11.23 Cr gap:\n%s", label, dead, text)
			}
		}
	}
	// And the measured reason is actually given, on both tools, identically.
	for _, label := range []string{"sales note", "turnover note"} {
		text := texts[label]
		if !strings.Contains(text, BasisGapNote) {
			t.Errorf("%s does not carry the shared BasisGapNote, so the two tools can tell an operator different stories:\n%s", label, text)
		}
	}
	for _, must := range []string{"NOT header freight", "TotalExpns", "BRANCH STOCK-TRANSFER", "HEADER level", "LINE level"} {
		if !strings.Contains(BasisGapNote, must) {
			t.Fatalf("BasisGapNote is missing %q:\n%s", must, BasisGapNote)
		}
	}
	// The note must not overstate its own evidence in the other direction. Freight
	// is not zero everywhere — it is 3 Oil invoices and Rs 22,500 — and a note that
	// claims more than was measured is the same defect wearing the other hat.
	for _, overreach := range []string{
		"0.00 on every non-cancelled A/R invoice",
		"is 0.00 on all",
		"not one document carries freight",
		"no document carries freight",
	} {
		if strings.Contains(BasisGapNote, overreach) {
			t.Errorf("BasisGapNote claims %q, which is false: 3 Oil invoices carry Rs 22,500 of \"TotalExpns\":\n%s", overreach, BasisGapNote)
		}
	}
	// And it must say the gap is material rather than "slight", because it is 11%
	// over four months and 18% in June.
	if strings.Contains(BasisGapNote, "slight") && !strings.Contains(BasisGapNote, "not slight") {
		t.Errorf("BasisGapNote still calls an 11%% difference slight:\n%s", BasisGapNote)
	}
	for _, must := range []string{"11.23 Cr", "MATERIAL"} {
		if !strings.Contains(BasisGapNote, must) {
			t.Errorf("BasisGapNote does not quantify the gap (%q):\n%s", must, BasisGapNote)
		}
	}
}

// --- quantities are units, not bottles ------------------------------------------

// The columns were QTY_BOTTLES_* and the note said "single BOTTLES
// (InvntryUom=PCS)". The carton half of C-0001 is verified and is what the
// correction is about ("NumInSale" = 1 on every item, so the x20 error cannot
// happen). The bottle half is not: of 185 Oil olive-tagged items, 111 are PCS,
// 62 carry no UoM, 10 are LTR, 1 DRM and 1 SET — and one month's answer counted
// 1,640 Mart 'SET' units and 5 Oil 'DRM' drums as bottles.
func TestQuantityColumnsClaimUnitsNotBottles(t *testing.T) {
	cols := salesColumns(false)
	found := 0
	for _, c := range cols {
		if strings.Contains(c, "BOTTLES") {
			t.Errorf("column %q still calls a mixed-UoM quantity a bottle count", c)
		}
		if c == "QTY_UNITS_EXTERNAL" || c == "QTY_UNITS_INTERNAL" {
			found++
		}
	}
	if found != 2 {
		t.Fatalf("salesColumns = %v, want QTY_UNITS_EXTERNAL and QTY_UNITS_INTERNAL", cols)
	}

	sales := mustSales(t, newRecordingRunner(salesResult()),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil"})
	if strings.Contains(sales.Note, "single BOTTLES") || strings.Contains(sales.Basis, "InvntryUom=PCS)") {
		t.Fatalf("the sales prose still asserts every unit is a bottle:\nnote: %s\nbasis: %s", sales.Note, sales.Basis)
	}
	// The half of C-0001 that IS true has to survive the correction.
	for _, must := range []string{"never cartons", "20 PCS", "20x"} {
		if !strings.Contains(UnitsCaveat, must) {
			t.Fatalf("UnitsCaveat dropped the carton rule (%q), which is what C-0001 is actually for:\n%s", must, UnitsCaveat)
		}
	}
	for _, must := range []string{"LTR", "DRM", "SET", "not a bottle count"} {
		if !strings.Contains(UnitsCaveat, must) {
			t.Fatalf("UnitsCaveat does not say which units are NOT bottles (%q):\n%s", must, UnitsCaveat)
		}
	}
}
