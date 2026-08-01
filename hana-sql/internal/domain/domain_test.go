package domain

import (
	"context"
	"fmt"
	"reflect"
	"strings"
	"testing"
	"time"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// --- a fake Runner -------------------------------------------------------------

// recordingRunner stands in for *hana.DB. It records exactly what would have been
// sent — statement, binds, policy — so the SQL can be asserted with no database
// in the process, and so the tests can prove the domain tools go through
// guard.MCPPolicy like every other query.
type recordingRunner struct {
	stmts    []string
	args     [][]any
	policies []guard.Policy

	catalog *hana.Result // answer for the variety pre-check
	combo   *hana.Result // answer for the combo item-group pre-check
	agg     *hana.Result // answer for the aggregate statement
	err     error
}

func newRecordingRunner(agg *hana.Result) *recordingRunner {
	return &recordingRunner{catalog: varietyCatalogResult(), combo: comboCatalogResult(), agg: agg}
}

func (r *recordingRunner) QueryReadOnly(_ context.Context, p guard.Policy, _ hana.Limits, stmt string, args ...any) (*hana.Result, error) {
	r.stmts = append(r.stmts, stmt)
	r.args = append(r.args, args)
	r.policies = append(r.policies, p)
	if r.err != nil {
		return nil, r.err
	}
	if strings.HasPrefix(strings.TrimSpace(stmt), "WITH AGG") {
		if r.agg == nil {
			return emptyAggResult(), nil
		}
		return r.agg, nil
	}
	if strings.Contains(stmt, "GRP_CODE") {
		if r.combo == nil {
			return comboCatalogResult(), nil
		}
		return r.combo, nil
	}
	return r.catalog, nil
}

// comboCatalogResult is what OITB answers for the combo group: code 109 in each
// of the three companies, verified live 2026-08-01.
func comboCatalogResult() *hana.Result {
	rows := []map[string]any{
		{"COMPANY": "Oil", "GRP_CODE": int64(109)},
		{"COMPANY": "Mart", "GRP_CODE": int64(109)},
		{"COMPANY": "Beverages", "GRP_CODE": int64(109)},
	}
	return &hana.Result{Rows: rows, RowCount: len(rows)}
}

// comboOil / comboAll are the resolved-group maps the buildSales tests pass in
// place of a live OITB lookup.
func comboOil() map[string][]int64 {
	return map[string][]int64{"JIVO_OIL_HANADB": {109}}
}

func comboAll() map[string][]int64 {
	out := map[string][]int64{}
	for _, c := range Companies() {
		out[c.Schema] = []int64{109}
	}
	return out
}

func (r *recordingRunner) lastStmt() string {
	if len(r.stmts) == 0 {
		return ""
	}
	return r.stmts[len(r.stmts)-1]
}

func (r *recordingRunner) lastArgs() []any {
	if len(r.args) == 0 {
		return nil
	}
	return r.args[len(r.args)-1]
}

const fakeAsOf = "2026-08-01T09:42:13Z"

func varietyCatalogResult() *hana.Result {
	rows := []map[string]any{
		{"COMPANY": "Oil", "VARIETY": "OLIVE", "ITEMS": int64(185)},
		{"COMPANY": "Oil", "VARIETY": "CANOLA", "ITEMS": int64(90)},
		{"COMPANY": "Oil", "VARIETY": "MUSTARD", "ITEMS": int64(120)},
		{"COMPANY": "Mart", "VARIETY": "OLIVE", "ITEMS": int64(151)},
	}
	return &hana.Result{Rows: rows, RowCount: len(rows)}
}

func salesResult() *hana.Result {
	rows := []map[string]any{
		{
			AsOfColumn: fakeAsOf, "COMPANY": "Oil", "VARIETY": "OLIVE",
			"EXTERNAL_NET": 39909813.16, "INTERNAL_RELATED_PARTY": 75586610.0,
			"GROSS_NET_OF_GST": 115496423.16, "OF_WHICH_COMBO_PACKS": 0.0,
			"QTY_UNITS_EXTERNAL": 95074.0, "QTY_UNITS_INTERNAL": 170414.0,
			"LINE_COUNT": int64(4211),
		},
	}
	return &hana.Result{Rows: rows, RowCount: len(rows), Elapsed: 412 * time.Millisecond}
}

func turnoverResult() *hana.Result {
	rows := []map[string]any{
		{
			AsOfColumn: fakeAsOf, "COMPANY": "Oil",
			"EXTERNAL_TURNOVER": 163602701.47, "INTERNAL_RELATED_PARTY": 120974137.2,
			"GROSS_TURNOVER": 284576838.67, "INVOICES_NET": 381965248.39,
			"CREDIT_NOTES_NET": 97388409.71, "INVOICE_COUNT": int64(512), "CREDIT_NOTE_COUNT": int64(123),
		},
	}
	return &hana.Result{Rows: rows, RowCount: len(rows)}
}

func paymentsResult() *hana.Result {
	rows := []map[string]any{
		{AsOfColumn: fakeAsOf, "COMPANY": "Oil", "DOC_TYPE": "(ALL)", "PAYMENTS": int64(483), "TOTAL": 735581753.89, "ROWS_WITH_NO_BUSINESS_PARTNER": int64(150)},
		{AsOfColumn: fakeAsOf, "COMPANY": "Oil", "DOC_TYPE": "A", "PAYMENTS": int64(150), "TOTAL": 308302438.54, "ROWS_WITH_NO_BUSINESS_PARTNER": int64(150)},
		{AsOfColumn: fakeAsOf, "COMPANY": "Oil", "DOC_TYPE": "S", "PAYMENTS": int64(333), "TOTAL": 427279315.35, "ROWS_WITH_NO_BUSINESS_PARTNER": int64(0)},
	}
	return &hana.Result{Rows: rows, RowCount: len(rows)}
}

// emptyAggResult is what the clock LEFT JOIN produces when the aggregate matches
// nothing: ONE row, the server clock present, every other column NULL.
func emptyAggResult() *hana.Result {
	return &hana.Result{
		Rows: []map[string]any{{
			AsOfColumn: fakeAsOf, "COMPANY": nil, "VARIETY": nil,
			"EXTERNAL_NET": nil, "INTERNAL_RELATED_PARTY": nil, "GROSS_NET_OF_GST": nil,
			"OF_WHICH_COMBO_PACKS": nil, "QTY_UNITS_EXTERNAL": nil,
			"QTY_UNITS_INTERNAL": nil, "LINE_COUNT": nil,
		}},
		RowCount: 1,
	}
}

func mustSales(t *testing.T, r *recordingRunner, req SalesRequest) *Response {
	t.Helper()
	res, err := SalesByVariety(context.Background(), r, req)
	if err != nil {
		t.Fatalf("SalesByVariety(%+v): %v", req, err)
	}
	return res
}

// --- the generated SQL is fixed text with binds ---------------------------------

// The golden statement. If this changes, the change was deliberate and the live
// acceptance run must be repeated — the figures it produces are pinned against
// the June-2026 olive numbers measured on the live database.
const goldenSalesOilOlive = `WITH AGG AS (
SELECT 'Oil' AS COMPANY,
       COALESCE(NULLIF(TRIM(itm."U_Sub_Group"), ''), '(UNTAGGED)') AS VARIETY,
       ROUND(TO_DOUBLE(SUM(CASE WHEN COALESCE(t.CC, '') NOT IN (%[1]s) THEN t.AMT ELSE 0 END)), 2) AS EXTERNAL_NET,
       ROUND(TO_DOUBLE(SUM(CASE WHEN COALESCE(t.CC, '') IN (%[1]s) THEN t.AMT ELSE 0 END)), 2) AS INTERNAL_RELATED_PARTY,
       ROUND(TO_DOUBLE(SUM(t.AMT)), 2) AS GROSS_NET_OF_GST,
       ROUND(TO_DOUBLE(SUM(CASE WHEN itm."ItmsGrpCod" IN (109) THEN t.AMT ELSE 0 END)), 2) AS OF_WHICH_COMBO_PACKS,
       ROUND(TO_DOUBLE(SUM(CASE WHEN UPPER(COALESCE(bp."CardName", '')) LIKE '%%JIVO%%' AND COALESCE(t.CC, '') NOT IN (%[1]s) THEN t.AMT ELSE 0 END)), 2) AS UNLISTED_JIVO_CARD_NET,
       ROUND(TO_DOUBLE(SUM(CASE WHEN COALESCE(t.CC, '') NOT IN (%[1]s) THEN t.QTY ELSE 0 END)), 2) AS QTY_UNITS_EXTERNAL,
       ROUND(TO_DOUBLE(SUM(CASE WHEN COALESCE(t.CC, '') IN (%[1]s) THEN t.QTY ELSE 0 END)), 2) AS QTY_UNITS_INTERNAL,
       COUNT(*) AS LINE_COUNT
FROM (SELECT h."CardCode" CC, l."LineTotal" AMT, l."Quantity" QTY, l."ItemCode" IC
      FROM "JIVO_OIL_HANADB"."INV1" l
      JOIN "JIVO_OIL_HANADB"."OINV" h ON h."DocEntry" = l."DocEntry"
      WHERE h."CANCELED" = 'N' AND h."DocDate" >= TO_DATE(?) AND h."DocDate" < TO_DATE(?)) t
LEFT OUTER JOIN "JIVO_OIL_HANADB"."OITM" itm ON itm."ItemCode" = t.IC
LEFT OUTER JOIN "JIVO_OIL_HANADB"."OCRD" bp ON bp."CardCode" = t.CC
WHERE (? = '' OR UPPER(TRIM(COALESCE(itm."U_Sub_Group", ''))) = UPPER(TRIM(?)))
GROUP BY COALESCE(NULLIF(TRIM(itm."U_Sub_Group"), ''), '(UNTAGGED)')
)
SELECT c.AS_OF_UTC AS AS_OF_UTC,
       a.COMPANY AS COMPANY,
       a.VARIETY AS VARIETY,
       a.EXTERNAL_NET AS EXTERNAL_NET,
       a.INTERNAL_RELATED_PARTY AS INTERNAL_RELATED_PARTY,
       a.GROSS_NET_OF_GST AS GROSS_NET_OF_GST,
       a.OF_WHICH_COMBO_PACKS AS OF_WHICH_COMBO_PACKS,
       a.UNLISTED_JIVO_CARD_NET AS UNLISTED_JIVO_CARD_NET,
       a.QTY_UNITS_EXTERNAL AS QTY_UNITS_EXTERNAL,
       a.QTY_UNITS_INTERNAL AS QTY_UNITS_INTERNAL,
       a.LINE_COUNT AS LINE_COUNT
FROM (SELECT TO_VARCHAR(CURRENT_UTCTIMESTAMP, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS AS_OF_UTC FROM DUMMY) c
LEFT OUTER JOIN AGG a ON 1 = 1
ORDER BY a.COMPANY, a.VARIETY`

// goldenSales is the golden statement with Oil's related-party IN list filled in,
// so the fixture cannot drift from the catalogue it is supposed to pin.
func goldenSales() string {
	return fmt.Sprintf(goldenSalesOilOlive, "'"+strings.Join(oilCardCodes(), "', '")+"'")
}

func oilCardCodes() []string {
	var out []string
	for _, c := range RelatedPartyCards("JIVO_OIL_HANADB") {
		out = append(out, c.CardCode)
	}
	return out
}

func TestSalesStatementIsGoldenAndBindsAreOrdered(t *testing.T) {
	r := newRecordingRunner(salesResult())
	res := mustSales(t, r, SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil", Variety: "OLIVE"})

	if got, want := r.lastStmt(), goldenSales(); got != want {
		t.Fatalf("generated SQL changed.\n--- got ---\n%s\n--- want ---\n%s", got, want)
	}
	want := []any{"2026-06-01", "2026-07-01", "OLIVE", "OLIVE"}
	if !reflect.DeepEqual(r.lastArgs(), want) {
		t.Fatalf("binds = %v, want %v", r.lastArgs(), want)
	}
	// The response echoes exactly what was executed, so the answer is auditable.
	if res.SQL != goldenSales() {
		t.Fatal("the response does not carry the statement that was executed")
	}
	if !reflect.DeepEqual(res.Params, want) {
		t.Fatalf("res.Params = %v, want the values actually bound %v", res.Params, want)
	}
	// No caller text may be interpolated: the only single-quoted literals are the
	// company label, the intercompany CardCode and the combo item group.
	for _, forbidden := range []string{"'OLIVE'", "'2026-06-01'", "'2026-07-01'"} {
		if strings.Contains(res.SQL, forbidden) {
			t.Fatalf("caller input %s was interpolated into the statement instead of bound", forbidden)
		}
	}
}

func TestNetCreditNotesControlsTheCreditNoteBlock(t *testing.T) {
	off := newRecordingRunner(salesResult())
	mustSales(t, off, SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil", NetCreditNotes: false})
	if strings.Contains(off.lastStmt(), "RIN1") || strings.Contains(off.lastStmt(), "ORIN") {
		t.Fatalf("net_credit_notes=false still queries credit notes:\n%s", off.lastStmt())
	}
	if n := len(off.lastArgs()); n != 4 {
		t.Fatalf("net_credit_notes=false bound %d params, want 4 (from, to, variety, variety)", n)
	}

	on := newRecordingRunner(salesResult())
	res := mustSales(t, on, SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil", NetCreditNotes: true})
	for _, must := range []string{`"JIVO_OIL_HANADB"."RIN1"`, `"JIVO_OIL_HANADB"."ORIN"`, `-r."LineTotal"`, `-r."Quantity"`} {
		if !strings.Contains(on.lastStmt(), must) {
			t.Fatalf("net_credit_notes=true is missing %q:\n%s", must, on.lastStmt())
		}
	}
	if n := len(on.lastArgs()); n != 6 {
		t.Fatalf("net_credit_notes=true bound %d params, want 6 (two windows + variety twice)", n)
	}
	if !strings.Contains(res.Basis, "credit notes netted off") {
		t.Fatalf("basis does not state that credit notes were netted off: %s", res.Basis)
	}
	// ... and the opposite basis says so just as plainly, because a figure before
	// returns and a figure after returns are different numbers.
	offRes := mustSales(t, newRecordingRunner(salesResult()),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil", NetCreditNotes: false})
	if !strings.Contains(offRes.Basis, "NOT netted off") {
		t.Fatalf("basis does not warn that credit notes were excluded: %s", offRes.Basis)
	}
}

func TestIncludeTypeAddsUTypeToSelectAndGrouping(t *testing.T) {
	r := newRecordingRunner(salesResult())
	mustSales(t, r, SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil", IncludeType: true})
	stmt := r.lastStmt()
	for _, must := range []string{`itm."U_TYPE" AS U_TYPE`, `GROUP BY ` + varietyExpr + `, itm."U_TYPE"`, "a.U_TYPE AS U_TYPE", "ORDER BY a.COMPANY, a.VARIETY, a.U_TYPE"} {
		if !strings.Contains(stmt, must) {
			t.Fatalf("include_type is missing %q:\n%s", must, stmt)
		}
	}
	plain := newRecordingRunner(salesResult())
	mustSales(t, plain, SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil"})
	if strings.Contains(plain.lastStmt(), "U_TYPE") {
		t.Fatalf("include_type=false still selects U_TYPE:\n%s", plain.lastStmt())
	}
}

// ALL companies is ONE statement — one snapshot, one as_of, one auditable SQL —
// with a literal company label per block and NO cross-company aggregation.
func TestAllCompaniesIsOneStatementPerCompanyNeverSummed(t *testing.T) {
	r := newRecordingRunner(salesResult())
	res := mustSales(t, r, SalesRequest{From: "2026-06-01", To: "2026-06-30"}) // company omitted => ALL
	// One AGGREGATE statement — one snapshot, one as_of. The combo item-group
	// lookup is a separate, tiny master-data read that carries no figures.
	if len(r.stmts) != 2 {
		t.Fatalf("ALL companies took %d statements; it must be the combo-group lookup plus ONE aggregate snapshot", len(r.stmts))
	}
	for _, s := range hana.Schemas {
		if !strings.Contains(r.lastStmt(), `"`+s+`"`) {
			t.Fatalf("the ALL statement does not read %s:\n%s", s, r.lastStmt())
		}
	}
	// One literal company label per block — the projection's own "a.COMPANY AS
	// COMPANY" is excluded by requiring the closing quote of the literal.
	if n := strings.Count(r.lastStmt(), "' AS COMPANY"); n != 3 {
		t.Fatalf("expected one COMPANY literal per company block, got %d", n)
	}
	if strings.Contains(r.lastStmt(), "SUM(") && strings.Count(r.lastStmt(), "GROUP BY") != 3 {
		t.Fatalf("expected one GROUP BY per company block, got %d — a cross-company aggregate would double-count the Oil-to-Mart transfer", strings.Count(r.lastStmt(), "GROUP BY"))
	}
	if len(res.Companies) != 3 {
		t.Fatalf("got %d company blocks, want 3 reported separately", len(res.Companies))
	}
	for i, c := range Companies() {
		if res.Companies[i].Company != c.Name || res.Companies[i].Schema != c.Schema {
			t.Fatalf("block %d = %+v, want %+v", i, res.Companies[i], c)
		}
	}
}

// --- company resolution ---------------------------------------------------------

func TestCompanyResolution(t *testing.T) {
	for _, in := range []string{"", "ALL", "all", "Oil", "oil", "JIVO_MART_HANADB", "jivo_mart_hanadb", " Beverages "} {
		if _, err := ResolveCompanies(in); err != nil {
			t.Fatalf("ResolveCompanies(%q) = %v, want it accepted", in, err)
		}
	}
	if got, _ := ResolveCompanies(""); len(got) != 3 {
		t.Fatalf(`ResolveCompanies("") returned %d companies, want all three`, len(got))
	}
	if got, _ := ResolveCompanies("oil"); len(got) != 1 || got[0].Schema != "JIVO_OIL_HANADB" {
		t.Fatalf(`ResolveCompanies("oil") = %+v`, got)
	}
}

// A typo must never read as "this company sold nothing".
func TestUnknownCompanyIsRefusedWithADidYouMean(t *testing.T) {
	cases := []struct{ in, hint string }{
		{"Bevrages", "Beverages"},
		{"Mrt", "Mart"},
		{"JIVO_BEVERAGE_HANADB", "Beverages"},
		{"nonsense", ""},
	}
	for _, c := range cases {
		got, err := ResolveCompanies(c.in)
		if err == nil {
			t.Fatalf("ResolveCompanies(%q) = %+v with no error", c.in, got)
		}
		if got != nil {
			t.Fatalf("ResolveCompanies(%q) returned companies alongside the error", c.in)
		}
		if !strings.Contains(err.Error(), "refusing rather than returning an empty result") {
			t.Fatalf("the refusal for %q does not say why: %v", c.in, err)
		}
		for _, s := range hana.Schemas {
			if !strings.Contains(err.Error(), s) {
				t.Fatalf("the refusal for %q does not name %s: %v", c.in, s, err)
			}
		}
		if c.hint != "" && !strings.Contains(err.Error(), `Did you mean "`+c.hint+`"`) {
			t.Fatalf("ResolveCompanies(%q) = %v, want a did-you-mean %q", c.in, err, c.hint)
		}
	}
}

// --- the window -----------------------------------------------------------------

// `to` is INCLUSIVE because that is how a person asks. The statement binds
// to+1 day, and the applied window is echoed so the boundary can be checked.
func TestWindowIsInclusiveAndBoundHalfOpen(t *testing.T) {
	w, err := ParseWindow("2026-06-01", "2026-06-30")
	if err != nil {
		t.Fatal(err)
	}
	if w.fromBind != "2026-06-01" || w.toBind != "2026-07-01" {
		t.Fatalf("binds = (%s, %s), want (2026-06-01, 2026-07-01)", w.fromBind, w.toBind)
	}
	if w.From != "2026-06-01" || w.To != "2026-06-30" {
		t.Fatalf("the window must echo the dates as asked, got %s..%s", w.From, w.To)
	}
	want := `"DocDate" >= '2026-06-01' AND "DocDate" < '2026-07-01'`
	if w.Applied != want {
		t.Fatalf("applied = %q, want %q", w.Applied, want)
	}
	// A single day is a legal window.
	if _, err := ParseWindow("2026-06-01", "2026-06-01"); err != nil {
		t.Fatalf("a one-day window was refused: %v", err)
	}
	// Month ends roll over correctly.
	dec, _ := ParseWindow("2026-12-01", "2026-12-31")
	if dec.toBind != "2027-01-01" {
		t.Fatalf("December's exclusive bound = %s, want 2027-01-01", dec.toBind)
	}
}

func TestBadWindowsAreRefused(t *testing.T) {
	cases := []struct{ from, to, wantIn string }{
		{"", "2026-06-30", "missing required argument: from"},
		{"2026-06-01", "", "missing required argument: to"},
		{"01-06-2026", "2026-06-30", "not a date in YYYY-MM-DD form"},
		{"2026-6-1", "2026-06-30", "not a date in YYYY-MM-DD form"},
		{"2026-13-01", "2026-06-30", "not a date in YYYY-MM-DD form"},
		{"2026-06-30", "2026-06-01", "runs backwards"},
	}
	for _, c := range cases {
		_, err := ParseWindow(c.from, c.to)
		if err == nil {
			t.Fatalf("ParseWindow(%q, %q) was accepted", c.from, c.to)
		}
		if !strings.Contains(err.Error(), c.wantIn) {
			t.Fatalf("ParseWindow(%q, %q) = %v, want it to mention %q", c.from, c.to, err, c.wantIn)
		}
	}
}

// --- the variety pre-check -------------------------------------------------------

// This is correction C-0003 turned inside out. Name-matching quietly returned a
// smaller number; a mis-typed TAG would quietly return zero. Both read as an
// answer, so a filter that matches nothing is refused.
func TestUnknownVarietyIsRefusedWithTheValidList(t *testing.T) {
	r := newRecordingRunner(salesResult())
	_, err := SalesByVariety(context.Background(), r, SalesRequest{
		From: "2026-06-01", To: "2026-06-30", Company: "Oil", Variety: "OLVE"})
	if err == nil {
		t.Fatal("a variety that tags no item was accepted; a typo must not read as zero sales")
	}
	msg := err.Error()
	for _, must := range []string{"refusing rather than reporting zero sales", "OLIVE", "CANOLA", "MUSTARD", `Did you mean "OLIVE"`} {
		if !strings.Contains(msg, must) {
			t.Fatalf("the refusal is missing %q: %s", must, msg)
		}
	}
	// And nothing was aggregated: the pre-check refused before the money query.
	for _, s := range r.stmts {
		if strings.HasPrefix(s, "WITH AGG") {
			t.Fatal("the aggregate ran despite the unknown variety")
		}
	}
}

func TestKnownVarietyPassesThePreCheckCaseInsensitively(t *testing.T) {
	for _, v := range []string{"OLIVE", "olive", " Olive "} {
		r := newRecordingRunner(salesResult())
		res := mustSales(t, r, SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil", Variety: v})
		if len(r.stmts) != 3 {
			t.Fatalf("variety %q took %d statements, want 3 (variety pre-check + combo-group lookup + aggregate)", v, len(r.stmts))
		}
		if !strings.Contains(res.Basis, `"OLIVE"`) {
			t.Fatalf("basis does not name the variety applied: %s", res.Basis)
		}
	}
	// With no variety there is no VARIETY pre-check round trip; the combo-group
	// lookup still runs, because OF_WHICH_COMBO_PACKS is on every answer.
	r := newRecordingRunner(salesResult())
	mustSales(t, r, SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil"})
	if len(r.stmts) != 2 {
		t.Fatalf("an unfiltered call took %d statements, want 2 (combo-group lookup + aggregate)", len(r.stmts))
	}
	for _, stmt := range r.stmts {
		if strings.Contains(stmt, "AS ITEMS") {
			t.Fatalf("an unfiltered call still ran the variety pre-check:\n%s", stmt)
		}
	}
}

// The typo-suggestion helper must prefer a containment match, so "olive oil"
// finds OLIVE rather than a spelling near-miss.
func TestClosestVarietyPrefersContainment(t *testing.T) {
	names := []string{"OLIVE", "CANOLA", "MUSTARD"}
	if got := closestVariety("olive oil", names); got != "OLIVE" {
		t.Fatalf(`closestVariety("olive oil") = %q, want "OLIVE"`, got)
	}
	if got := closestVariety("MUSTRD", names); got != "MUSTARD" {
		t.Fatalf(`closestVariety("MUSTRD") = %q, want "MUSTARD"`, got)
	}
	if got := closestVariety("zzzzzzzz", names); got != "" {
		t.Fatalf(`closestVariety("zzzzzzzz") = %q, want no guess`, got)
	}
}

// --- the server clock -------------------------------------------------------------

// The whole point of the clock LEFT JOIN: a zero-row answer must still be
// stamped. "No sales" and "no answer" must not look the same, and a month-end
// close has to be reproducible against a stated instant.
func TestZeroRowsStillCarriesTheServerClock(t *testing.T) {
	r := newRecordingRunner(emptyAggResult())
	res := mustSales(t, r, SalesRequest{From: "2026-06-01", To: "2026-06-30"})
	if res.AsOf != fakeAsOf {
		t.Fatalf("as_of = %q on a zero-row answer, want the server clock %q", res.AsOf, fakeAsOf)
	}
	if res.AsOfSource != AsOfSource || !strings.Contains(res.AsOfSource, "hana-server-clock") {
		t.Fatalf("as_of_source = %q", res.AsOfSource)
	}
	if len(res.Companies) != 3 {
		t.Fatalf("got %d company blocks on a zero-row answer, want all three still named", len(res.Companies))
	}
	for _, b := range res.Companies {
		if len(b.Rows) != 0 {
			t.Fatalf("%s has rows on a zero-row answer: %+v", b.Company, b.Rows)
		}
		if !strings.Contains(b.Note, "genuine zero") && !strings.Contains(b.Note, "real zero") {
			t.Fatalf("%s's empty block does not say the zero is real: %q", b.Company, b.Note)
		}
	}
}

// The clock is envelope metadata, not data. Repeating it on every row invites a
// model to treat it as a column of the answer.
func TestAsOfNeverLeaksIntoRows(t *testing.T) {
	res := mustSales(t, newRecordingRunner(salesResult()),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: "Oil"})
	for _, b := range res.Companies {
		for _, row := range b.Rows {
			if _, ok := row[AsOfColumn]; ok {
				t.Fatalf("%s carries %s inside a row", b.Company, AsOfColumn)
			}
			if _, ok := row["COMPANY"]; ok {
				t.Fatalf("%s repeats COMPANY inside a row; it is already the block's identity", b.Company)
			}
		}
	}
	if res.AsOf != fakeAsOf {
		t.Fatalf("as_of = %q", res.AsOf)
	}
}

// --- the read-only pipeline --------------------------------------------------------

// Every domain query goes out under guard.MCPPolicy, exactly like a user's SQL.
func TestEveryQueryUsesTheMCPPolicy(t *testing.T) {
	r := newRecordingRunner(salesResult())
	mustSales(t, r, SalesRequest{From: "2026-06-01", To: "2026-06-30", Variety: "OLIVE"})
	if _, err := Turnover(context.Background(), r, TurnoverRequest{From: "2026-07-01", To: "2026-07-28"}); err != nil {
		t.Fatal(err)
	}
	r.agg = paymentsResult()
	if _, err := Payments(context.Background(), r, PaymentsRequest{Direction: Outgoing, From: "2026-07-01", To: "2026-07-31"}); err != nil {
		t.Fatal(err)
	}
	if len(r.policies) < 4 {
		t.Fatalf("only %d queries were recorded", len(r.policies))
	}
	for i, p := range r.policies {
		if p.Name != guard.MCPPolicy.Name {
			t.Fatalf("query %d ran under policy %q, want %q — there is no privileged path", i, p.Name, guard.MCPPolicy.Name)
		}
	}
}

// --- turnover ----------------------------------------------------------------------

func TestTurnoverEncodesTheCanonicalFormula(t *testing.T) {
	r := newRecordingRunner(turnoverResult())
	res, err := Turnover(context.Background(), r, TurnoverRequest{From: "2026-07-01", To: "2026-07-28", Company: "Oil"})
	if err != nil {
		t.Fatal(err)
	}
	stmt := r.lastStmt()
	for _, must := range []string{
		`"DocTotal" - "VatSum"`,
		`-("DocTotal" - "VatSum")`,
		`"JIVO_OIL_HANADB"."OINV"`,
		`"JIVO_OIL_HANADB"."ORIN"`,
		`"CANCELED" = 'N'`,
		`CASE WHEN COALESCE(t.CC, '') NOT IN ('CUSTA000001', 'CUSTA000002', 'CUSTA000003', 'CUSTA000004', 'CUSTA000606', 'CUSTA000827', 'CUSTA000906', 'CUSTA001099', 'CUSTA001113')`,
		"AS INVOICE_COUNT",
		"AS CREDIT_NOTE_COUNT",
	} {
		if !strings.Contains(stmt, must) {
			t.Fatalf("the turnover statement is missing %q:\n%s", must, stmt)
		}
	}
	want := []any{"2026-07-01", "2026-07-29", "2026-07-01", "2026-07-29"}
	if !reflect.DeepEqual(r.lastArgs(), want) {
		t.Fatalf("turnover binds = %v, want %v (to is INCLUSIVE, so 28 Jul binds 29 Jul)", r.lastArgs(), want)
	}
	for _, must := range []string{"HEADER level", `"CANCELED" = 'N'`, "JIVO-group card list", "internal_cards", "C-0002"} {
		if !strings.Contains(res.Basis, must) {
			t.Fatalf("turnover basis is missing %q: %s", must, res.Basis)
		}
	}
	// The two sales tools use different bases, and both say so — otherwise a model
	// that finds a gap between them starts flip-flopping, which is exactly what
	// the olive incident looked like from the operator's side.
	sales := mustSales(t, newRecordingRunner(salesResult()), SalesRequest{From: "2026-07-01", To: "2026-07-28", Company: "Oil"})
	if !strings.Contains(sales.Basis, "LINE level") {
		t.Fatalf("the sales basis does not state its own formula: %s", sales.Basis)
	}
}

// hana_turnover deliberately has no knobs: the canonical figure has one
// definition, and credit-note netting is part of it.
func TestTurnoverHasNoOptionalBasisArguments(t *testing.T) {
	tp := reflect.TypeOf(TurnoverRequest{})
	want := map[string]bool{"From": true, "To": true, "Company": true}
	for i := 0; i < tp.NumField(); i++ {
		if !want[tp.Field(i).Name] {
			t.Fatalf("TurnoverRequest gained the field %q — the canonical figure must not become configurable", tp.Field(i).Name)
		}
	}
}

// --- payments -----------------------------------------------------------------------

func TestPaymentsAlwaysReturnsTheAllRowAndTheMeanings(t *testing.T) {
	r := newRecordingRunner(paymentsResult())
	res, err := Payments(context.Background(), r, PaymentsRequest{
		Direction: Outgoing, From: "2026-07-01", To: "2026-07-31", Company: "Oil"})
	if err != nil {
		t.Fatal(err)
	}
	stmt := r.lastStmt()
	for _, must := range []string{
		`"JIVO_OIL_HANADB"."OVPM"`,
		`p."Canceled" = 'N'`, // ONE l on the payment tables
		`GROUP BY p."DocType"`,
		`'(ALL)' AS DOC_TYPE`,
		`ROUND(TO_DOUBLE(COALESCE(SUM(p."DocTotal"), 0)), 2)`,
	} {
		if !strings.Contains(stmt, must) {
			t.Fatalf("the payments statement is missing %q:\n%s", must, stmt)
		}
	}
	if strings.Contains(stmt, "CashSum") || strings.Contains(stmt, "TransferSum") {
		t.Fatal("the payments statement assembles the total from payment means; \"DocTotal\" exists in HANA")
	}

	rows := res.Companies[0].Rows
	seen := map[string]bool{}
	for _, row := range rows {
		dt, _ := row["DOC_TYPE"].(string)
		seen[dt] = true
		meaning, _ := row["MEANING"].(string)
		if meaning == "" {
			t.Fatalf("DocType %q has no meaning attached", dt)
		}
	}
	if !seen[AllDocTypes] {
		t.Fatalf("no %q row came back; a total that can be a subset is the defect", AllDocTypes)
	}
	for _, must := range []string{AllDocTypes, "72.06 lakh", "1,74,90,480", "G/L account", "Say which scope you quoted"} {
		if !strings.Contains(res.Note, must) {
			t.Fatalf("the payments note is missing %q: %s", must, res.Note)
		}
	}
}

// There is no argument that can narrow the answer.
func TestPaymentsHasNoScopingArgument(t *testing.T) {
	tp := reflect.TypeOf(PaymentsRequest{})
	want := map[string]bool{"Direction": true, "From": true, "To": true, "Company": true}
	for i := 0; i < tp.NumField(); i++ {
		if !want[tp.Field(i).Name] {
			t.Fatalf("PaymentsRequest gained the field %q — the breakdown must not become narrowable", tp.Field(i).Name)
		}
	}
}

func TestPaymentDirection(t *testing.T) {
	for _, in := range []string{"outgoing", "OUTGOING", " Outgoing "} {
		if d, err := ParseDirection(in); err != nil || d != Outgoing {
			t.Fatalf("ParseDirection(%q) = (%q, %v)", in, d, err)
		}
	}
	if d, _ := ParseDirection("incoming"); d.table() != "ORCT" {
		t.Fatalf("incoming reads %s, want ORCT", d.table())
	}
	if d, _ := ParseDirection("outgoing"); d.table() != "OVPM" {
		t.Fatalf("outgoing reads %s, want OVPM", d.table())
	}
	if _, err := ParseDirection(""); err == nil || !strings.Contains(err.Error(), "missing required argument: direction") {
		t.Fatalf(`ParseDirection("") = %v`, err)
	}
	if _, err := ParseDirection("sideways"); err == nil || !strings.Contains(err.Error(), "OVPM") {
		t.Fatalf("ParseDirection(\"sideways\") = %v, want a refusal that names the valid values", err)
	}
	r := newRecordingRunner(paymentsResult())
	if _, err := Payments(context.Background(), r, PaymentsRequest{
		Direction: "sideways", From: "2026-07-01", To: "2026-07-31"}); err == nil {
		t.Fatal("Payments accepted an invalid direction")
	}
}

// The DocType meanings were measured live on 2026-08-01, not recalled. 'A' rows
// carry a G/L ACCOUNT code in "CardCode" that has no row in OCRD — in BOTH
// tables. The plan predicted a NULL "CardCode", which is wrong.
func TestDocTypeMeaningsAreTheVerifiedOnes(t *testing.T) {
	out := docTypeMeaning(Outgoing, "S")
	if !strings.Contains(out, "supplier") || !strings.Contains(out, "paid TO") {
		t.Fatalf("outgoing S = %q", out)
	}
	in := docTypeMeaning(Incoming, "C")
	if !strings.Contains(in, "customer") || !strings.Contains(in, "received FROM") {
		t.Fatalf("incoming C = %q", in)
	}
	a := docTypeMeaning(Outgoing, "A")
	for _, must := range []string{"G/L ACCOUNT", "NO row in OCRD", "real cash"} {
		if !strings.Contains(a, must) {
			t.Fatalf("the 'A' meaning is missing %q: %s", must, a)
		}
	}
	if strings.Contains(a, `"CardCode" is NULL`) {
		t.Fatalf("the 'A' meaning repeats the unverified NULL-CardCode claim: %s", a)
	}
	if all := docTypeMeaning(Outgoing, AllDocTypes); !strings.Contains(all, "EVERY DocType") {
		t.Fatalf("the (ALL) meaning = %q", all)
	}
	// An unseen code fails loud rather than being guessed at.
	if u := docTypeMeaning(Outgoing, "X"); !strings.Contains(u, "UNKNOWN DocType") {
		t.Fatalf("an unknown DocType = %q, want an explicit warning", u)
	}
}

// The direction-specific half of the census, and the reason the tool reports
// OCRD membership rather than an empty name.
//
// Live 2026-08-01: on OVPM, 4590 of Oil's 4592 'A' rows have an empty
// "CardName"; on ORCT, ZERO of the 1899 'A' rows do — they all carry a name.
// An earlier draft asserted the empty name in both directions, which would have
// sent a model looking for the wrong signal on every incoming-payment question.
func TestTheEmptyCardNameClaimIsNotMadeForIncoming(t *testing.T) {
	in := docTypeMeaning(Incoming, "A")
	if strings.Contains(in, `"CardName" is empty`) {
		t.Fatalf("the incoming 'A' meaning claims an empty \"CardName\", which is false on ORCT — all 1899 of Oil's 'A' receipts carry one: %s", in)
	}
	if !strings.Contains(in, "NO row in OCRD") {
		t.Fatalf("the incoming 'A' meaning does not state the discriminator that IS true in both directions: %s", in)
	}
	if !strings.Contains(in, `"CardName" is still filled in`) {
		t.Fatalf("the incoming 'A' meaning should warn that the name is present on ORCT, so nobody reuses the OVPM signal: %s", in)
	}
	// The outgoing side may state it, because there it is true.
	if out := docTypeMeaning(Outgoing, "A"); !strings.Contains(out, `"CardName" is empty`) {
		t.Fatalf("the outgoing 'A' meaning dropped the verified empty-name observation: %s", out)
	}
}

// The count the payload reports must be the verified discriminator (OCRD
// membership), not the name — in the SQL, not just in the prose.
func TestPaymentsCountsPartnerlessRowsByOCRDMembership(t *testing.T) {
	for _, d := range []Direction{Outgoing, Incoming} {
		stmt, _ := buildPayments(Companies(), d, Window{fromBind: "2026-07-01", toBind: "2026-08-01"})
		if !strings.Contains(stmt, `COALESCE(SUM(CASE WHEN bp."CardCode" IS NULL THEN 1 ELSE 0 END), 0) AS ROWS_WITH_NO_BUSINESS_PARTNER`) {
			t.Fatalf("%s: the partnerless count is not measured against OCRD:\n%s", d, stmt)
		}
		if strings.Contains(stmt, `p."CardName"`) {
			t.Fatalf("%s: the statement still discriminates on \"CardName\", which is only empty on OVPM:\n%s", d, stmt)
		}
		// The join must be an OUTER one on OCRD's key, or it would silently drop
		// exactly the G/L-account rows this tool exists to keep.
		for _, c := range Companies() {
			want := fmt.Sprintf("LEFT OUTER JOIN \"%s\".\"OCRD\" bp ON bp.\"CardCode\" = p.\"CardCode\"", c.Schema)
			if strings.Count(stmt, want) != 2 { // the per-DocType block and the (ALL) block
				t.Fatalf("%s: %s should join OCRD in both its blocks, found %d:\n%s", d, c.Name, strings.Count(stmt, want), stmt)
			}
		}
	}
}

// --- notes ---------------------------------------------------------------------------

// The sentence the olive incident needed and did not have, on every
// sales-shaped answer.
func TestNotesCarryTheSettledCorrections(t *testing.T) {
	sales := mustSales(t, newRecordingRunner(salesResult()), SalesRequest{From: "2026-06-01", To: "2026-06-30"})
	for _, must := range []string{
		"CUSTA000606", "intercompany", "NEVER add", "say which one you quoted",
		"saleable UNITS", "20 PCS", "SALES BOM", "(UNTAGGED)",
	} {
		if !strings.Contains(sales.Note, must) {
			t.Fatalf("the sales note is missing %q:\n%s", must, sales.Note)
		}
	}
	turn, err := Turnover(context.Background(), newRecordingRunner(turnoverResult()),
		TurnoverRequest{From: "2026-07-01", To: "2026-07-28"})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(turn.Note, "CUSTA000606") || !strings.Contains(turn.Note, "NEVER add") {
		t.Fatalf("the turnover note lost the intercompany rule:\n%s", turn.Note)
	}
}

// A truncated result must not be presented as a whole answer.
func TestTruncationSurvivesIntoTheResponse(t *testing.T) {
	res := salesResult()
	res.Truncated = true
	res.Note = "row cap reached (1000 rows), so this answer is INCOMPLETE"
	out := mustSales(t, newRecordingRunner(res), SalesRequest{From: "2026-06-01", To: "2026-06-30"})
	if !out.Truncated {
		t.Fatal("truncated was dropped on the way out")
	}
	if !strings.Contains(out.Note, "INCOMPLETE") {
		t.Fatalf("the truncation note was dropped: %s", out.Note)
	}
}

// A database error is returned, never swallowed into an empty-looking answer.
func TestDatabaseErrorsPropagate(t *testing.T) {
	r := newRecordingRunner(salesResult())
	r.err = context.DeadlineExceeded
	if _, err := SalesByVariety(context.Background(), r, SalesRequest{From: "2026-06-01", To: "2026-06-30"}); err == nil {
		t.Fatal("a failed query produced an answer")
	}
	if _, err := Turnover(context.Background(), r, TurnoverRequest{From: "2026-06-01", To: "2026-06-30"}); err == nil {
		t.Fatal("a failed turnover query produced an answer")
	}
	if _, err := Payments(context.Background(), r, PaymentsRequest{Direction: Outgoing, From: "2026-06-01", To: "2026-06-30"}); err == nil {
		t.Fatal("a failed payments query produced an answer")
	}
}
