package domain

import (
	"context"
	"fmt"
	"math"
	"os"
	"sort"
	"strings"
	"testing"
	"time"

	"hana-sql/internal/config"
	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// The live acceptance suite for the domain tools. It runs only with
// HANA_TEST_LIVE=1 and only where HANA is reachable (in practice the VPS,
// through the office reverse tunnel):
//
//	HANA_TEST_LIVE=1 HANA_ENV=/opt/jivo-truth/hana.env ./domain-live.test -test.v
//
// Why it exists. The unit tests prove the generated SQL is the text we intended
// and that the binds are ordered; they cannot prove that text means what we
// think against JIVO's actual books. Three things in this package are claims
// about a live database and nothing else:
//
//  1. that TO_DATE(?) with a 'YYYY-MM-DD' string bind compares correctly against
//     the TIMESTAMP "DocDate" columns (the plan flagged this UNVERIFIED),
//  2. that OITM."U_TYPE" / "U_Sub_Group" exist in all THREE company schemas —
//     they are per-company UDFs, and a missing one hard-errors the ALL query,
//  3. that OVPM/ORCT."DocType" really is S / C / A and that 'A' is real cash with
//     no business partner (the payment-scoping defect the tool exists to close).
//
// Every statement here is a READ. Nothing in this file, or anywhere else in the
// shipped code, attempts a write — the two figures-carrying tests call the very
// same exported functions the MCP tools call, so what is measured here is the
// tool, not a hand-written approximation of it.
func liveDB(t *testing.T) *hana.DB {
	t.Helper()
	if os.Getenv("HANA_TEST_LIVE") != "1" {
		t.Skip("set HANA_TEST_LIVE=1 (and HANA_ENV) to run the live domain suite")
	}
	cfg, err := config.Load(config.Find(""))
	if err != nil {
		t.Fatalf("config: %v", err)
	}
	db := hana.New(cfg, hana.Options{
		// The SAME row cap production runs (hana.DefaultMaxRows = 1000). It used to
		// be 5000, which meant the acceptance suite could not observe a truncation
		// the deployed server would hit — an acceptance run has to fail the way
		// production fails. The timeout is longer only because a live sweep over
		// four months of INV1 is slower than an interactive question, and a
		// deadline is not a correctness boundary the way a row cap is.
		Limits:        hana.Limits{MaxRows: hana.DefaultMaxRows, MaxBytes: hana.DefaultMaxBytes, Timeout: 180 * time.Second},
		MaxConcurrent: 2,
		AppName:       "hana-sql-domain-live-test",
	})
	t.Cleanup(func() { db.Close() })
	return db
}

func liveRows(t *testing.T, db *hana.DB, stmt string, args ...any) []map[string]any {
	t.Helper()
	res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, hana.Limits{}, stmt, args...)
	if err != nil {
		t.Fatalf("query failed: %v\n%s", err, stmt)
	}
	return res.Rows
}

// num pulls a number out of a driver value. ROUND(TO_DOUBLE(…)) arrives as a
// float64 and COUNT(*) as an int64; a DECIMAL would arrive as an exact string.
func num(t *testing.T, v any) float64 {
	t.Helper()
	switch x := v.(type) {
	case float64:
		return x
	case int64:
		return float64(x)
	case string:
		var f float64
		if _, err := fmt.Sscanf(x, "%g", &f); err != nil {
			t.Fatalf("value %q is not a number: %v", x, err)
		}
		return f
	case nil:
		return 0
	}
	t.Fatalf("value %#v (%T) is not a number", v, v)
	return 0
}

func crore(v float64) string { return fmt.Sprintf("Rs %.2f Cr", v/1e7) }

// findRow returns the first row in a company block matching a column value.
func findRow(blk CompanyBlock, col, val string) map[string]any {
	for _, r := range blk.Rows {
		if s, _ := r[col].(string); s == val {
			return r
		}
	}
	return nil
}

func blockOf(res *Response, company string) (CompanyBlock, bool) {
	for _, b := range res.Companies {
		if b.Company == company {
			return b, true
		}
	}
	return CompanyBlock{}, false
}

// --- STEP 0(b): the UDF columns exist in every company --------------------------

// OITM."U_TYPE" and "U_Sub_Group" are USER-DEFINED fields, added per company
// database. If Beverages is missing them, the ALL-companies UNION does not
// return a partial answer — it hard-errors for everyone, including the Oil-only
// callers who share the statement builder. That is worth one cheap catalog read.
func TestLiveVarietyUDFsExistInEveryCompany(t *testing.T) {
	db := liveDB(t)
	for _, c := range Companies() {
		rows := liveRows(t, db, `SELECT COLUMN_NAME, DATA_TYPE_NAME, LENGTH FROM SYS.TABLE_COLUMNS
		  WHERE SCHEMA_NAME = ? AND TABLE_NAME = 'OITM' AND COLUMN_NAME IN ('U_TYPE', 'U_Sub_Group')
		  ORDER BY COLUMN_NAME`, c.Schema)
		have := map[string]bool{}
		for _, r := range rows {
			n, _ := r["COLUMN_NAME"].(string)
			have[n] = true
			t.Logf("%-24s OITM.%-12s %v(%v)", c.Schema, n, r["DATA_TYPE_NAME"], r["LENGTH"])
		}
		for _, col := range []string{"U_TYPE", "U_Sub_Group"} {
			if !have[col] {
				t.Errorf("%s (%s) has no OITM.%q — the ALL-companies statement would hard-error for every caller, not just this company", c.Schema, c.Name, col)
			}
		}
	}

	// OITB."ItmsGrpNam"/"ItmsGrpCod" carry the combo-pack split (C-0004).
	for _, c := range Companies() {
		rows := liveRows(t, db, `SELECT COUNT(*) AS N FROM SYS.TABLE_COLUMNS
		  WHERE SCHEMA_NAME = ? AND TABLE_NAME = 'OITB' AND COLUMN_NAME IN ('ItmsGrpCod', 'ItmsGrpNam')`, c.Schema)
		if n := num(t, rows[0]["N"]); n != 2 {
			t.Errorf("%s: OITB is missing ItmsGrpCod/ItmsGrpNam (found %v of 2)", c.Schema, n)
		}
	}
}

// --- STEP 0(c): the variety catalogue the typo refusal is built on ---------------

// checkVariety refuses an unknown variety by listing the valid ones. That list
// comes from this statement, so what it actually returns is part of the tool's
// behaviour, not a detail.
func TestLiveVarietyCatalogue(t *testing.T) {
	db := liveDB(t)
	rows := liveRows(t, db, buildVarietyCatalog(Companies()))

	perCompany := map[string]int{}
	olive := map[string]float64{}
	for _, r := range rows {
		c, _ := r["COMPANY"].(string)
		v, _ := r["VARIETY"].(string)
		perCompany[c]++
		if strings.EqualFold(v, "OLIVE") {
			olive[c] = num(t, r["ITEMS"])
		}
	}
	for _, c := range Companies() {
		t.Logf("%-9s %3d distinct U_Sub_Group values, OLIVE tags %v items", c.Name, perCompany[c.Name], olive[c.Name])
	}
	if perCompany["Oil"] == 0 {
		t.Fatal("Oil has no U_Sub_Group values at all — the unknown-variety refusal would refuse everything")
	}
	// The ground truth quoted in the olive incident: 185 olive-tagged items in
	// Oil, 151 in Mart. The master is live, so drift is logged, not failed.
	for company, want := range map[string]float64{"Oil": 185, "Mart": 151} {
		if got := olive[company]; got != want {
			t.Logf("NOTE: %s OLIVE item count is %v, the incident write-up measured %v (item master is live; not a code defect)", company, got, want)
		} else {
			t.Logf("%s OLIVE item count %v matches the incident write-up", company, got)
		}
	}
}

// --- STEP 0(a): what OVPM/ORCT."DocType" actually is -----------------------------

// The payment-scoping defect in one test. The tool's description tells a model
// that 'A' is real cash with no business partner; that sentence is only worth
// anything if it is true of these books.
func TestLivePaymentDocTypeCensus(t *testing.T) {
	db := liveDB(t)

	for _, tbl := range []string{"OVPM", "ORCT"} {
		for _, c := range Companies() {
			stmt := fmt.Sprintf(`SELECT p."DocType" AS DOC_TYPE,
			    COUNT(*) AS N,
			    ROUND(TO_DOUBLE(SUM(p."DocTotal")), 2) AS TOTAL,
			    SUM(CASE WHEN p."CardCode" IS NULL OR p."CardCode" = '' THEN 1 ELSE 0 END) AS NO_CARDCODE,
			    SUM(CASE WHEN p."CardName" IS NULL OR p."CardName" = '' THEN 1 ELSE 0 END) AS NO_CARDNAME,
			    SUM(CASE WHEN bp."CardCode" IS NULL THEN 1 ELSE 0 END) AS NOT_IN_OCRD
			  FROM "%s"."%s" p
			  LEFT OUTER JOIN "%s"."OCRD" bp ON bp."CardCode" = p."CardCode"
			  WHERE p."Canceled" = 'N'
			  GROUP BY p."DocType" ORDER BY p."DocType"`, c.Schema, tbl, c.Schema)

			rows := liveRows(t, db, stmt)
			for _, r := range rows {
				dt, _ := r["DOC_TYPE"].(string)
				t.Logf("%-9s %s DocType=%-3q n=%-6v total=%-16s no_CardCode=%-5v no_CardName=%-5v not_in_OCRD=%v",
					c.Name, tbl, dt, r["N"], crore(num(t, r["TOTAL"])), r["NO_CARDCODE"], r["NO_CARDNAME"], r["NOT_IN_OCRD"])

				// Anything outside S/C/A means docTypeMeaning() would hand a model
				// "UNKNOWN DocType" on real data.
				if m := docTypeMeaning(Outgoing, dt); strings.HasPrefix(m, "UNKNOWN") {
					t.Errorf("%s.%s has DocType %q, which internal/domain/payments.go does not describe — the tool would tell a model it is unknown", c.Schema, tbl, dt)
				}
			}
		}
	}

	// The load-bearing claim, asserted rather than eyeballed: in Oil's OVPM the
	// 'A' rows have no business partner. If this stops being true, the sentence
	// in PaymentsFacts() and docTypeMeaning() has to change with it.
	rows := liveRows(t, db, `SELECT COUNT(*) AS N,
	    SUM(CASE WHEN p."CardName" IS NULL OR p."CardName" = '' THEN 1 ELSE 0 END) AS NO_NAME,
	    SUM(CASE WHEN bp."CardCode" IS NULL THEN 1 ELSE 0 END) AS NOT_IN_OCRD
	  FROM "JIVO_OIL_HANADB"."OVPM" p
	  LEFT OUTER JOIN "JIVO_OIL_HANADB"."OCRD" bp ON bp."CardCode" = p."CardCode"
	  WHERE p."Canceled" = 'N' AND p."DocType" = 'A'`)
	n, noName, notInOCRD := num(t, rows[0]["N"]), num(t, rows[0]["NO_NAME"]), num(t, rows[0]["NOT_IN_OCRD"])
	t.Logf("Oil OVPM DocType='A': %v rows, %v with an empty CardName, %v whose CardCode is not a business partner in OCRD", n, noName, notInOCRD)
	if n == 0 {
		t.Fatal("no DocType='A' rows at all in Oil's OVPM — then the whole payment-scoping premise needs re-checking")
	}
	if notInOCRD != n {
		t.Errorf("%v of %v 'A' rows DO resolve to a business partner in OCRD; the description says the CardCode on an 'A' row is a G/L account code, and that is now wrong", n-notInOCRD, n)
	}
}

// --- STEP 0(e) + STEP 7: the acceptance targets, through the real tools ----------

// The figures the whole exercise is measured against, produced by calling
// SalesByVariety exactly as the MCP tool calls it — same builder, same TO_DATE(?)
// binds, same guard, same read-only transaction. That is also the proof of Step
// 0(e): if a 'YYYY-MM-DD' string bind did not compare correctly against the
// TIMESTAMP "DocDate", these numbers would not land.
//
//	June 2026, U_Sub_Group = 'OLIVE', line-level, CANCELED = 'N', credit notes OFF
//	  Oil  EXTERNAL_NET           =  39,893,584.59
//	  Oil  INTERNAL_RELATED_PARTY =  75,602,838.57
//	  Oil  GROSS_NET_OF_GST       = 115,496,423.16
//	  Mart EXTERNAL_NET           = 104,693,533.23
//	  Mart INTERNAL_RELATED_PARTY =  15,291,011.60
//	  Mart GROSS_NET_OF_GST       = 119,984,544.83
//
// THE TARGETS MOVED ON 2026-08-01, and the old ones are kept below as checksums
// rather than deleted, because the move was a CORRECTION and not a book change.
// The originals were
//
//	Oil  external (CardCode <> CUSTA000606) =  39,909,813.16
//	Oil  to CUSTA000606                     =  75,586,610.00
//	Mart external (CardCode <> CUSTA000606) = 119,984,544.83
//
// measured against a split that knew only ONE card code. Correcting it to the
// full related-party catalogue (C-0002's evidence, not just its rule line) moves
// Rs 16,228.57 of Oil from external to internal — JIVO WELLNESS branches — and
// Rs 1,52,91,011.60 of Mart, which is its own Delhi branch and 12.7% of a figure
// that was being reported as an outside sale. Both old numbers are still
// reproducible from the new ones, and the test asserts that they are:
//
//	Oil  EXTERNAL + 16,228.57                 = 39,909,813.16   (old Oil external)
//	Mart EXTERNAL + INTERNAL_RELATED_PARTY    = 119,984,544.83  (old Mart external)
//
// so a run that lands the new figures also proves it did not simply lose money.
//
// THE DEFAULT USED TO BE NOT TO FAIL. Every mismatch was downgraded to t.Logf
// unless HANA_TEST_STRICT_TRUTH=1 was set, so a green live run proved nothing
// about the figures — the acceptance targets did not gate anything, which is the
// one job an acceptance target has.
//
// The default is now inverted. A mismatch FAILS. The original concern is real —
// the books are open, a late credit note is not a code defect, and a test that
// cries wolf every month gets ignored — so an operator who has looked and knows
// the books moved sets HANA_TEST_ALLOW_DRIFT=1. Even then, drift beyond
// driftTolerance still fails: a late credit note moves a figure by a fraction of
// a percent, while a broken join moves it by a lot, and only the second one is
// what this test is for.
const driftTolerance = 0.005 // 0.5%

func TestLiveSalesByVarietyHitsTheAcceptanceTargets(t *testing.T) {
	db := liveDB(t)
	allowDrift := os.Getenv("HANA_TEST_ALLOW_DRIFT") == "1"

	res, err := SalesByVariety(context.Background(), db, SalesRequest{
		From: "2026-06-01", To: "2026-06-30", Company: AllCompanies,
		Variety: "OLIVE", NetCreditNotes: false,
	})
	if err != nil {
		t.Fatalf("SalesByVariety: %v", err)
	}
	t.Logf("as_of=%s (%s) elapsed=%dms", res.AsOf, res.AsOfSource, res.ElapsedMS)
	t.Logf("window applied: %s   params=%v", res.Window.Applied, res.Params)
	if res.AsOf == "" {
		t.Error("as_of is empty — the clock join is the one thing guaranteed to return a row")
	}

	check := func(name string, got, want float64) {
		if fmt.Sprintf("%.2f", got) == fmt.Sprintf("%.2f", want) {
			t.Logf("MATCH  %-28s %15.2f  (%s)", name, got, crore(got))
			return
		}
		rel := math.Abs(got-want) / math.Abs(want)
		msg := "DRIFT  %-28s %15.2f  want %15.2f  (delta %+.2f, %.3f%%)"
		if allowDrift && rel <= driftTolerance {
			t.Logf(msg+"  — within the %.1f%% tolerance and HANA_TEST_ALLOW_DRIFT=1; late credit notes/cancellations are the usual cause",
				name, got, want, got-want, rel*100, driftTolerance*100)
			return
		}
		hint := "  — set HANA_TEST_ALLOW_DRIFT=1 only after checking the books for late credit notes/cancellations"
		if rel > driftTolerance {
			hint = fmt.Sprintf("  — %.3f%% is past the %.1f%% tolerance, so this is not book movement: suspect the SQL", rel*100, driftTolerance*100)
		}
		t.Errorf(msg+hint, name, got, want, got-want, rel*100)
	}

	for _, tc := range []struct {
		company, col string
		want         float64
	}{
		{"Oil", "EXTERNAL_NET", 39893584.59},
		{"Oil", "INTERNAL_RELATED_PARTY", 75602838.57},
		{"Oil", "GROSS_NET_OF_GST", 115496423.16},
		{"Mart", "EXTERNAL_NET", 104693533.23},
		{"Mart", "INTERNAL_RELATED_PARTY", 15291011.60},
		{"Mart", "GROSS_NET_OF_GST", 119984544.83},
	} {
		blk, ok := blockOf(res, tc.company)
		if !ok {
			t.Fatalf("no company block for %s; blocks = %+v", tc.company, res.Companies)
		}
		row := findRow(blk, "VARIETY", "OLIVE")
		if row == nil {
			t.Fatalf("%s has no OLIVE row; rows = %+v", tc.company, blk.Rows)
		}
		check(tc.company+" "+tc.col, num(t, row[tc.col]), tc.want)
	}

	// The whole point of C-0002: the two must be reported apart, and adding Oil's
	// gross to Mart's would double-count the transfer.
	oil, _ := blockOf(res, "Oil")
	mart, _ := blockOf(res, "Mart")
	oilRow, martRow := findRow(oil, "VARIETY", "OLIVE"), findRow(mart, "VARIETY", "OLIVE")
	if oilRow != nil && martRow != nil {
		oilGross := num(t, oilRow["GROSS_NET_OF_GST"])
		martExt := num(t, martRow["EXTERNAL_NET"])
		t.Logf("C-0002 in numbers: naive Oil gross + Mart external = %s, of which %s is the SAME oil moved between two JIVO companies",
			crore(oilGross+martExt), crore(num(t, oilRow["INTERNAL_RELATED_PARTY"])))

		// The old single-card targets, reproduced from the new split. This is what
		// makes the 2026-08-01 correction auditable rather than a number that
		// changed: money moved between the buckets, none of it left.
		checkSum := func(name string, got, want float64) {
			if fmt.Sprintf("%.2f", got) != fmt.Sprintf("%.2f", want) {
				t.Errorf("checksum %s = %.2f, want %.2f. The related-party split is meant to REDISTRIBUTE the old figures, not change the total — a mismatch here means money entered or left the answer.", name, got, want)
			} else {
				t.Logf("CHECKSUM %-34s %15.2f reproduces the pre-correction target", name, got)
			}
		}
		checkSum("Mart EXTERNAL + INTERNAL (old Mart external)",
			martExt+num(t, martRow["INTERNAL_RELATED_PARTY"]), 119984544.83)
		checkSum("Oil EXTERNAL + INTERNAL (Oil gross)",
			num(t, oilRow["EXTERNAL_NET"])+num(t, oilRow["INTERNAL_RELATED_PARTY"]), oilGross)

		// The drift alarm must be quiet: a non-zero value means SAP holds a
		// JIVO-named card the catalogue has not been told about, which is exactly
		// the state these figures were measured out of.
		for _, r := range []map[string]any{oilRow, martRow} {
			if v, ok := r["UNLISTED_JIVO_CARD_NET"]; ok && num(t, v) != 0 {
				t.Errorf("UNLISTED_JIVO_CARD_NET = %.2f: a JIVO-named card is missing from domain.relatedPartyCards, so EXTERNAL_NET is an upper bound. See TestLiveRelatedPartyCatalogueMatchesOCRD.", num(t, v))
			}
		}
		t.Logf("C-0004 in numbers: Oil combo packs inside that OLIVE figure = %s; Mart combo packs = %s",
			crore(num(t, oilRow["OF_WHICH_COMBO_PACKS"])), crore(num(t, martRow["OF_WHICH_COMBO_PACKS"])))
		t.Logf("C-0001 in numbers: Oil OLIVE external quantity = %.0f saleable UNITS (x20 would read %.0f, the carton error). Units, not bottles: a minority of these SKUs are LTR/DRM/SET.",
			num(t, oilRow["QTY_UNITS_EXTERNAL"]), num(t, oilRow["QTY_UNITS_EXTERNAL"])*20)
	}
}

// The C-0003 defect, measured on the live database: what item-name matching
// reports versus what the SAP tag reports. This is the number the olive incident
// got wrong, and it is the argument for the tool existing.
func TestLiveNameMatchingUnderReportsAgainstTheSAPTag(t *testing.T) {
	db := liveDB(t)
	for _, c := range []Company{{Name: "Oil", Schema: "JIVO_OIL_HANADB"}, {Name: "Mart", Schema: "JIVO_MART_HANADB"}} {
		stmt := fmt.Sprintf(`SELECT
		    ROUND(TO_DOUBLE(SUM(CASE WHEN UPPER(itm."U_Sub_Group") = 'OLIVE' THEN l."LineTotal" ELSE 0 END)), 2) AS BY_SAP_TAG,
		    ROUND(TO_DOUBLE(SUM(CASE WHEN UPPER(itm."ItemName") LIKE '%%OLIVE%%' THEN l."LineTotal" ELSE 0 END)), 2) AS BY_ITEM_NAME
		  FROM "%s"."INV1" l
		  JOIN "%s"."OINV" h ON h."DocEntry" = l."DocEntry"
		  LEFT OUTER JOIN "%s"."OITM" itm ON itm."ItemCode" = l."ItemCode"
		  WHERE h."CANCELED" = 'N' AND h."DocDate" >= TO_DATE(?) AND h."DocDate" < TO_DATE(?)`,
			c.Schema, c.Schema, c.Schema)
		rows := liveRows(t, db, stmt, "2026-06-01", "2026-07-01")
		tag, name := num(t, rows[0]["BY_SAP_TAG"]), num(t, rows[0]["BY_ITEM_NAME"])
		t.Logf("%-5s June-2026 olive: SAP tag %s vs item-name matching %s — name matching misses %s",
			c.Name, crore(tag), crore(name), crore(tag-name))
		if name >= tag {
			t.Logf("NOTE: name matching did not under-report in %s this month; C-0003's evidence is a range-wide claim, not a monthly invariant", c.Name)
		}
	}
}

// --- STEP 7: turnover against the anchor query ----------------------------------

// hana_turnover must agree to the paisa with queries/turnover-oil-july.sql, which
// is the written-down definition. Note the anchor uses "DocDate" <= '2026-07-28'
// (inclusive), which is exactly what to=2026-07-28 means at this tool's boundary.
func TestLiveTurnoverMatchesTheAnchorQuery(t *testing.T) {
	db := liveDB(t)

	res, err := Turnover(context.Background(), db, TurnoverRequest{
		From: "2026-07-01", To: "2026-07-28", Company: "Oil",
	})
	if err != nil {
		t.Fatalf("Turnover: %v", err)
	}
	blk, ok := blockOf(res, "Oil")
	if !ok || len(blk.Rows) == 0 {
		t.Fatalf("no Oil turnover row: %+v", res.Companies)
	}
	row := blk.Rows[0]
	t.Logf("as_of=%s window=%s", res.AsOf, res.Window.Applied)

	// The anchor, run in the same session so both see the same books.
	anchor := liveRows(t, db, `SELECT
	    (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OINV"
	       WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N') AS INV_ROWS,
	    (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."ORIN"
	       WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N') AS CN_ROWS,
	    ROUND(TO_DOUBLE(
	      (SELECT COALESCE(SUM("DocTotal" - "VatSum"), 0) FROM "JIVO_OIL_HANADB"."OINV"
	         WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N')
	    - (SELECT COALESCE(SUM("DocTotal" - "VatSum"), 0) FROM "JIVO_OIL_HANADB"."ORIN"
	         WHERE "DocDate" >= '2026-07-01' AND "DocDate" <= '2026-07-28' AND "CANCELED" = 'N')), 2) AS TURNOVER_NET
	  FROM DUMMY`)[0]

	gotGross := num(t, row["GROSS_TURNOVER"])
	wantGross := num(t, anchor["TURNOVER_NET"])
	t.Logf("hana_turnover GROSS  = %15.2f  (%s)", gotGross, crore(gotGross))
	t.Logf("anchor SQL   turnover= %15.2f  (%s)", wantGross, crore(wantGross))
	if fmt.Sprintf("%.2f", gotGross) != fmt.Sprintf("%.2f", wantGross) {
		t.Errorf("hana_turnover disagrees with queries/turnover-oil-july.sql by %+.2f — the tool is supposed to BE that definition", gotGross-wantGross)
	}
	for _, p := range []struct {
		name string
		got  any
		want any
	}{
		{"INVOICE_COUNT", row["INVOICE_COUNT"], anchor["INV_ROWS"]},
		{"CREDIT_NOTE_COUNT", row["CREDIT_NOTE_COUNT"], anchor["CN_ROWS"]},
	} {
		if num(t, p.got) != num(t, p.want) {
			t.Errorf("%s = %v, anchor says %v — the half-open window is not selecting the same documents as the anchor's inclusive <=", p.name, p.got, p.want)
		} else {
			t.Logf("%-18s %v matches the anchor", p.name, p.got)
		}
	}

	// The identity the note promises the reader.
	inv, cn := num(t, row["INVOICES_NET"]), num(t, row["CREDIT_NOTES_NET"])
	if d := inv - cn - gotGross; d > 0.011 || d < -0.011 {
		t.Errorf("INVOICES_NET - CREDIT_NOTES_NET = %.2f but GROSS_TURNOVER = %.2f; the note promises they agree", inv-cn, gotGross)
	}
	ext, internal := num(t, row["EXTERNAL_TURNOVER"]), num(t, row["INTERNAL_RELATED_PARTY"])
	if d := ext + internal - gotGross; d > 0.011 || d < -0.011 {
		t.Errorf("EXTERNAL + INTERNAL = %.2f but GROSS = %.2f; the split must be exhaustive or money is missing", ext+internal, gotGross)
	}
	t.Logf("Oil 1-28 Jul: external %s + related-party %s = gross %s", crore(ext), crore(internal), crore(gotGross))
}

// --- STEP 6b: the basis difference, measured where it actually lives -------------

// THIS TEST USED TO BE FOUR LINES OF t.Logf INSIDE THE TURNOVER TEST, on Oil for
// 1-28 July, where the gap is 0.4% — and it asserted nothing at all while
// printing a freight explanation that is false. The gap is a Mart phenomenon:
// Mart April–July 2026 is header Rs 76.50 Cr vs line Rs 87.72 Cr, a 12.8%
// difference, and 17.1% in June alone. A check that runs where the number is small
// and never fails is not assurance, it is decoration.
//
// What is asserted here:
//
//  1. freight is NOT the driver — OINV."TotalExpns" is measured directly, and if
//     it ever grows big enough to explain the gap this fails and the prose has to
//     be rewritten;
//  2. the gap is MATERIAL on Mart, so nothing may go back to calling it slight;
//  3. it is concentrated in the RELATED-PARTY cards, which is the claim
//     domain.BasisGapNote makes and the reason the two tools reconcile on
//     EXTERNAL rather than on GROSS.
func TestLiveBasisGapIsBranchTransfersNotFreight(t *testing.T) {
	db := liveDB(t)
	const from, to = "2026-04-01", "2026-07-31"

	// (1) Freight, measured rather than asserted from memory.
	for _, c := range Companies() {
		rows := liveRows(t, db, fmt.Sprintf(`SELECT ROUND(TO_DOUBLE(COALESCE(SUM("TotalExpns"), 0)), 2) AS FREIGHT,
       COUNT(*) AS DOCS
FROM "%s"."OINV"
WHERE "CANCELED" = 'N' AND "DocDate" >= TO_DATE(?) AND "DocDate" < TO_DATE(?)`, c.Schema), from, "2026-08-01")
		if len(rows) != 1 {
			t.Fatalf("%s: freight probe returned %d rows", c.Name, len(rows))
		}
		freight, docs := num(t, rows[0]["FREIGHT"]), num(t, rows[0]["DOCS"])
		t.Logf("%-10s freight %12.2f over %.0f invoices", c.Name, freight, docs)
		// One lakh is far above the measured Rs 15,000 for Oil and Rs 0 elsewhere,
		// and far below the crores the gap runs to. If freight ever crosses it,
		// BasisGapNote's "not freight" claim needs re-measuring before it ships.
		if freight > 100000 {
			t.Errorf("%s carries Rs %.2f of header freight in %s..%s. domain.BasisGapNote asserts freight is immaterial (measured Rs 15,000 for Oil, Rs 0 for Mart and Beverages on 2026-08-01) — re-measure and rewrite the note before trusting it.",
				c.Name, freight, from, to)
		}
	}

	// (2) and (3): the gap on Mart, and where it sits.
	turn, err := Turnover(context.Background(), db, TurnoverRequest{From: from, To: to, Company: "Mart"})
	if err != nil {
		t.Fatalf("Turnover: %v", err)
	}
	sales, err := SalesByVariety(context.Background(), db, SalesRequest{
		From: from, To: to, Company: "Mart", NetCreditNotes: true,
	})
	if err != nil {
		t.Fatalf("SalesByVariety: %v", err)
	}
	tblk, ok := blockOf(turn, "Mart")
	if !ok || len(tblk.Rows) != 1 {
		t.Fatalf("no Mart turnover row")
	}
	header := num(t, tblk.Rows[0]["GROSS_TURNOVER"])
	headerExt := num(t, tblk.Rows[0]["EXTERNAL_TURNOVER"])

	var line, lineExt float64
	sblk, _ := blockOf(sales, "Mart")
	for _, r := range sblk.Rows {
		line += num(t, r["GROSS_NET_OF_GST"])
		lineExt += num(t, r["EXTERNAL_NET"])
	}
	gross := line - header
	t.Logf("Mart %s..%s  GROSS: header %s vs line %s  gap %s (%.1f%%)",
		from, to, crore(header), crore(line), crore(gross), 100*gross/line)
	t.Logf("Mart %s..%s  EXTERNAL: header %s vs line %s  gap %s",
		from, to, crore(headerExt), crore(lineExt), crore(headerExt-lineExt))

	// (2) The gap is material. "Slight" was the shipped word and it was wrong.
	if line == 0 {
		t.Fatal("Mart line total is zero; the measurement is vacuous")
	}
	if pct := 100 * gross / line; pct < 5 {
		t.Errorf("the Mart GROSS basis gap is now %.1f%%, under the 5%% this repo calls MATERIAL. Measured 2026-08-01 it was 12.8%%. Re-measure before softening domain.BasisGapNote back towards \"slight\".", pct)
	}
	// Freight would make the HEADER figure the larger one. It is not.
	if gross < 0 {
		t.Errorf("the header figure now exceeds the line figure by %s — the shape a header-freight explanation predicts. Re-measure OINV.\"TotalExpns\" before changing domain.BasisGapNote.", crore(-gross))
	}

	// (3) Excluding the related-party cards, the two bases agree. This is the
	// reconciliation the note promises, and it is what makes EXTERNAL the figure
	// to compare across the two tools.
	extGap := headerExt - lineExt
	if extGap < 0 {
		extGap = -extGap
	}
	if lineExt > 0 && 100*extGap/lineExt > 1 {
		t.Errorf("EXTERNAL differs by %s (%.2f%%) between the header and line bases. domain.BasisGapNote claims the divergence lives entirely in the related-party cards, so this is either a new driver or a card missing from the catalogue — check UNLISTED_JIVO_CARD_NET.",
			crore(extGap), 100*extGap/lineExt)
	}

	// And the shipped prose still says all of this.
	for _, must := range []string{"NOT header freight", "BRANCH STOCK-TRANSFER", "MATERIAL"} {
		if !strings.Contains(sales.Note, must) {
			t.Errorf("the sales note no longer gives the measured reason for the basis gap (%q):\n%s", must, sales.Note)
		}
	}
}

// --- STEP 6c: the related-party catalogue against OCRD ---------------------------

// The catalogue in relatedparty.go is a frozen Go constant, and a frozen constant
// is exactly how CUSTA000874 came to be missing: correction C-0002 named Mart's
// branch cards on 2026-07-30 and the code ignored them until 2026-08-01, with
// Rs 9.58 Cr of Mart's own Delhi branch reported as an EXTERNAL sale.
//
// This re-derives the set from OCRD and fails when SAP and the catalogue
// disagree, in EITHER direction: a card SAP has and the code does not is money in
// the wrong bucket; a card the code has and SAP does not is a stale entry whose
// name no longer means what the payload says it means.
func TestLiveRelatedPartyCatalogueMatchesOCRD(t *testing.T) {
	db := liveDB(t)
	for _, c := range Companies() {
		rows := liveRows(t, db, fmt.Sprintf(`SELECT "CardCode" AS CARD_CODE, "CardName" AS CARD_NAME
FROM "%s"."OCRD"
WHERE "CardType" = 'C' AND UPPER("CardName") LIKE '%%JIVO%%'
ORDER BY "CardCode"`, c.Schema))

		live := map[string]string{}
		for _, r := range rows {
			live[stringOf(r["CARD_CODE"])] = stringOf(r["CARD_NAME"])
		}
		cat := map[string]string{}
		for _, card := range RelatedPartyCards(c.Schema) {
			cat[card.CardCode] = card.CardName
		}
		t.Logf("%-10s OCRD has %d JIVO-named customer cards; the catalogue has %d", c.Name, len(live), len(cat))
		if len(live) == 0 {
			t.Errorf("%s: OCRD returned no JIVO-named customer cards at all — the probe is broken, not the books", c.Name)
			continue
		}
		for code, name := range live {
			if _, ok := cat[code]; !ok {
				t.Errorf("%s: OCRD card %s (%s) is JIVO-named but NOT in domain.relatedPartyCards, so its sales are reported as EXTERNAL. Add it (or, if it is genuinely a third party whose name contains JIVO, say so in a comment next to the catalogue).",
					c.Name, code, name)
			}
		}
		for code, name := range cat {
			liveName, ok := live[code]
			if !ok {
				t.Errorf("%s: catalogued card %s (%s) no longer exists in OCRD as a JIVO-named customer; a stale entry strips a real party out of EXTERNAL", c.Name, code, name)
				continue
			}
			if liveName != name {
				t.Errorf("%s: card %s is %q in OCRD but %q in the catalogue; the payload would name it wrongly", c.Name, code, liveName, name)
			}
		}
	}
}

// --- STEP 6d: the combo item group resolves to a code ---------------------------

// OF_WHICH_COMBO_PACKS keys on the item group's CODE, resolved from its name once
// per call. Verified live 2026-08-01: "ItmsGrpCod" 109 in all three companies.
// If the group is ever renamed the column goes NULL and says so — this asserts it
// resolves today, so a NULL in production means a real rename and not a bug here.
func TestLiveComboItemGroupResolves(t *testing.T) {
	db := liveDB(t)
	got, missing, err := resolveComboGroups(context.Background(), db, Companies())
	if err != nil {
		t.Fatalf("resolveComboGroups: %v", err)
	}
	if len(missing) > 0 {
		t.Errorf("the %q item group did not resolve in %v — OF_WHICH_COMBO_PACKS will be NULL there. If SAP renamed it, update domain.ComboItemGroup.", ComboItemGroup, missing)
	}
	for _, c := range Companies() {
		t.Logf("%-10s %q = ItmsGrpCod %v", c.Name, ComboItemGroup, got[c.Schema])
	}
}

// --- STEP 7: payments, and the size of the defect the tool closes ----------------

// hana_payments must return the (ALL) row alongside the breakdown, and (ALL) must
// be the server-side total of the same window — not the sum of the rounded rows.
// The gap between (ALL) and 'S' IS the measured under-report.
func TestLivePaymentsAlwaysCarriesTheWholeTotal(t *testing.T) {
	db := liveDB(t)

	res, err := Payments(context.Background(), db, PaymentsRequest{
		Direction: Outgoing, From: "2026-07-01", To: "2026-07-31", Company: "Oil",
	})
	if err != nil {
		t.Fatalf("Payments: %v", err)
	}
	blk, ok := blockOf(res, "Oil")
	if !ok {
		t.Fatalf("no Oil block: %+v", res.Companies)
	}
	t.Logf("as_of=%s window=%s", res.AsOf, res.Window.Applied)

	var perType float64
	var seen []string
	for _, r := range blk.Rows {
		dt, _ := r["DOC_TYPE"].(string)
		seen = append(seen, dt)
		t.Logf("  DocType=%-6s n=%-6v total=%-16s no_partner=%-5v  %s",
			dt, r["PAYMENTS"], crore(num(t, r["TOTAL"])), r["ROWS_WITH_NO_BUSINESS_PARTNER"], r["MEANING"])
		if dt != AllDocTypes {
			perType += num(t, r["TOTAL"])
		}
		if _, hasMeaning := r["MEANING"]; !hasMeaning {
			t.Errorf("row %v carries no MEANING; the breakdown is unreadable without one", r)
		}

		// The claim the description rests on, asserted per row rather than
		// asserted in prose: 'A' rows are exactly the ones with no business
		// partner, and 'S'/'C' rows are exactly the ones that have one.
		n, noBP := num(t, r["PAYMENTS"]), num(t, r["ROWS_WITH_NO_BUSINESS_PARTNER"])
		switch dt {
		case "A":
			if noBP != n {
				t.Errorf("DocType 'A': %v of %v rows resolve to a business partner in OCRD, but the tool tells a model that an 'A' row has none", n-noBP, n)
			}
		case "S", "C":
			if noBP != 0 {
				t.Errorf("DocType %q: %v rows have no OCRD business partner, but the tool describes them as partner payments", dt, noBP)
			}
		}
	}
	sort.Strings(seen)

	all := findRow(blk, "DOC_TYPE", AllDocTypes)
	if all == nil {
		t.Fatalf("no %q row — the tool's entire purpose is that a total cannot be silently narrowed; got %v", AllDocTypes, seen)
	}
	allTotal := num(t, all["TOTAL"])

	// (ALL) is computed server-side over the same WHERE, so it must equal the sum
	// of the per-type rows to within rounding of the individual rows.
	if d := allTotal - perType; d > 0.5 || d < -0.5 {
		t.Errorf("(ALL) total %.2f differs from the sum of the per-DocType rows %.2f by %+.2f — more than rounding; one of the two blocks has a different WHERE", allTotal, perType, d)
	}

	s := findRow(blk, "DOC_TYPE", "S")
	if s == nil {
		t.Fatal("no DocType='S' row in Oil's July payouts")
	}
	sTotal := num(t, s["TOTAL"])
	t.Logf("THE DEFECT, MEASURED: answering with DocType='S' alone reports %s; the real total is %s — a shortfall of %s across %v documents",
		crore(sTotal), crore(allTotal), crore(allTotal-sTotal), num(t, all["PAYMENTS"])-num(t, s["PAYMENTS"]))
	if allTotal <= sTotal {
		t.Errorf("(ALL) %.2f is not greater than 'S' %.2f — then this tool is solving a problem these books do not have", allTotal, sTotal)
	}

	// Incoming must work too, and must reach ORCT rather than OVPM.
	in, err := Payments(context.Background(), db, PaymentsRequest{
		Direction: Incoming, From: "2026-07-01", To: "2026-07-31", Company: "Oil",
	})
	if err != nil {
		t.Fatalf("Payments(incoming): %v", err)
	}
	if !strings.Contains(in.SQL, `"ORCT"`) || strings.Contains(in.SQL, `"OVPM"`) {
		t.Error("direction=incoming did not switch the table to ORCT")
	}
	inBlk, _ := blockOf(in, "Oil")
	if r := findRow(inBlk, "DOC_TYPE", AllDocTypes); r != nil {
		t.Logf("Oil July receipts (ALL) = %s across %v documents", crore(num(t, r["TOTAL"])), r["PAYMENTS"])
	}
}

// --- the refusals, against the real database ------------------------------------

// A typo must not read as "we sold none of it". Against the live item master.
func TestLiveUnknownVarietyIsRefusedNotAnsweredZero(t *testing.T) {
	db := liveDB(t)
	_, err := SalesByVariety(context.Background(), db, SalesRequest{
		From: "2026-06-01", To: "2026-06-30", Company: AllCompanies, Variety: "OLIVEE", NetCreditNotes: true,
	})
	if err == nil {
		t.Fatal(`variety "OLIVEE" was answered instead of refused — a mis-typed tag reading as zero sales is the failure this refusal exists to prevent`)
	}
	t.Logf("refused: %s", err)
	if !strings.Contains(err.Error(), "OLIVE") {
		t.Errorf("the refusal does not offer the correct tag: %v", err)
	}

	// And the correct one, in the wrong case, must still be accepted.
	res, err := SalesByVariety(context.Background(), db, SalesRequest{
		From: "2026-06-01", To: "2026-06-30", Company: "Oil", Variety: "olive", NetCreditNotes: true,
	})
	if err != nil {
		t.Fatalf(`variety "olive" (lower case) was refused: %v`, err)
	}
	if blk, ok := blockOf(res, "Oil"); ok {
		t.Logf(`variety "olive" accepted case-insensitively: %d row(s)`, len(blk.Rows))
	}
}

// An empty window must still carry the server clock, AND must read as a genuine
// zero rather than as a fault.
//
// WHAT THIS TEST HAS LEARNED THE HARD WAY. In standard SQL an ungrouped
// aggregate returns exactly one all-zero row for an empty window, and a previous
// revision asserted that and shipped a payload note calling a missing row a
// FAULT. Live HANA does something else. Measured here, and reproduced by hand on
// 2026-08-01 for Oil over 1999-01-01..1999-01-02:
//
//	SELECT COUNT(*) FROM AGG                       -> 1
//	FROM (clock) c LEFT OUTER JOIN AGG a ON 1 = 1  -> one row, a.COMPANY NULL
//
// Through the clock join HANA yields the NULL-extended row rather than the
// aggregate's own row, so the caller sees NO company row. The clock row itself
// survives, which is the property the join exists for and the property asserted
// first below.
//
// This is a HANA behaviour, not a defect in the templates, and it is asserted
// rather than worked around because the payload text depends on it: if HANA ever
// starts returning the zero row, this fails and the notes in turnover.go and
// payments.go should go back to promising explicit zeros.
func TestLiveEmptyWindowIsAGenuineZeroAndKeepsTheClock(t *testing.T) {
	db := liveDB(t)
	res, err := Turnover(context.Background(), db, TurnoverRequest{
		From: "1999-01-01", To: "1999-01-02", Company: "Oil",
	})
	if err != nil {
		t.Fatalf("Turnover: %v", err)
	}
	// The one thing that must survive an empty aggregate.
	if res.AsOf == "" {
		t.Fatal("a zero-row answer came back with no as_of; the clock-driving LEFT JOIN is the one thing that must survive an empty aggregate")
	}
	if len(res.Companies) != 1 {
		t.Fatalf("want one company block, got %d", len(res.Companies))
	}
	blk := res.Companies[0]
	t.Logf("empty window: as_of=%s rows=%d note=%q", res.AsOf, len(blk.Rows), blk.Note)

	if len(blk.Rows) == 0 {
		// The measured behaviour. The note is then the entire answer, so it has to
		// say "genuine zero" and must not call a quiet month a fault.
		if !strings.Contains(blk.Note, "GENUINE ZERO") {
			t.Errorf("an empty window produced no rows and a note that does not call it a genuine zero: %q", blk.Note)
		}
		if strings.Contains(blk.Note, "treat this as a fault") {
			t.Errorf("an empty window is reported to the operator as a fault: %q", blk.Note)
		}
		return
	}

	// If HANA ever does return the zero row, every money column must read 0 and
	// not null — and the prose that currently explains the empty block should be
	// revisited.
	t.Logf("HANA now returns the ungrouped zero row through the clock join; revisit the empty-window notes in turnover.go and payments.go")
	if len(blk.Rows) != 1 {
		t.Fatalf("want exactly one all-zero row, got %d", len(blk.Rows))
	}
	row := blk.Rows[0]
	for _, col := range turnoverColumns() {
		if col == "COMPANY" {
			continue
		}
		v, ok := row[col]
		if !ok {
			t.Errorf("%s is missing from the zero row", col)
			continue
		}
		if v == nil {
			t.Errorf("%s is null on an empty window; null and \"we could not answer\" are the same thing to a model", col)
			continue
		}
		if n := num(t, v); n != 0 {
			t.Errorf("%s = %v on an empty window, want 0", col, n)
		}
	}
}

// Every generated statement must clear the guard against the real database too —
// the same assertion the unit test makes, but with HANA's own parser behind it.
func TestLiveEveryStatementRunsUnderTheGuard(t *testing.T) {
	db := liveDB(t)
	for i, stmt := range Statements() {
		if err := guard.Check(stmt, guard.MCPPolicy); err != nil {
			t.Fatalf("statement %d was refused by the guard: %v\n%s", i, err, stmt)
		}
	}
	t.Logf("%d generated statement variants all clear guard.Check under MCPPolicy", len(Statements()))

	// And a write shaped like one of ours is still refused, live.
	_, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, hana.Limits{},
		`WITH AGG AS (SELECT 1 AS X FROM DUMMY) UPDATE "JIVO_OIL_HANADB"."OCRD" SET "Balance" = 0 WHERE 1 = 0`)
	if !guard.IsRefusal(err) {
		t.Fatalf("a write wrapped in the domain tools' own WITH-prefix shape was NOT refused: %v", err)
	}
	t.Logf("refused: %s", err)
}

// --- the two risks that unit tests structurally cannot retire --------------------

// EVERY STATEMENT VARIANT, EXECUTED. Until this test existed, not one of the
// generated statements had ever been sent to HANA: internal/hana's live suite
// does not reference this package, every unit test answers from canned rows, and
// guard.Check is a lexer, not a parser. Three tools whose entire justification is
// "a tool that computes the right thing" would have executed for the first time
// in production, on somebody's phone.
//
// Two specific claims are what need a database to settle, and only these:
//
//   - the clock scaffold — WITH AGG (…UNION ALL…) SELECT … FROM (SELECT
//     CURRENT_UTCTIMESTAMP FROM DUMMY) c LEFT OUTER JOIN AGG a ON 1 = 1 — is
//     novel SQL that appears nowhere else in this repo.
//   - OITM."U_Sub_Group" and "U_TYPE" are literal HANA column names, and now
//     TRIM/NULLIF/COALESCE are wrapped around them.
//
// (The `? = ” OR UPPER(x) = UPPER(?)` idiom is already proven live by
// internal/hana/catalog.go, and the OITB/OVPM column names were censused
// 2026-08-01, so neither is retested here.)
//
// The window is two days: this runs 40-odd statements and the point is that HANA
// ACCEPTS and EXECUTES each one, not what they add up to.
func TestLiveEveryStatementVariantExecutesAgainstHANA(t *testing.T) {
	db := liveDB(t)
	const from, to = "2026-06-01", "2026-06-02"

	ran := 0
	for _, company := range []string{AllCompanies, "Oil", "Mart", "Beverages"} {
		for _, includeType := range []bool{false, true} {
			for _, netCN := range []bool{false, true} {
				for _, variety := range []string{"", "OLIVE"} {
					res, err := SalesByVariety(context.Background(), db, SalesRequest{
						From: from, To: to, Company: company,
						Variety: variety, IncludeType: includeType, NetCreditNotes: netCN,
					})
					if err != nil {
						t.Errorf("SalesByVariety(company=%s type=%v cn=%v variety=%q) was REFUSED BY HANA: %v",
							company, includeType, netCN, variety, err)
						continue
					}
					if res.AsOf == "" {
						t.Errorf("SalesByVariety(company=%s type=%v cn=%v variety=%q) executed but carried no as_of; the clock scaffold did not survive",
							company, includeType, netCN, variety)
					}
					ran++
				}
			}
		}
		if res, err := Turnover(context.Background(), db, TurnoverRequest{From: from, To: to, Company: company}); err != nil {
			t.Errorf("Turnover(%s) was REFUSED BY HANA: %v", company, err)
		} else if res.AsOf == "" {
			t.Errorf("Turnover(%s) carried no as_of", company)
		} else {
			ran++
		}
		for _, d := range []Direction{Outgoing, Incoming} {
			if res, err := Payments(context.Background(), db, PaymentsRequest{
				Direction: d, From: from, To: to, Company: company}); err != nil {
				t.Errorf("Payments(%s, %s) was REFUSED BY HANA: %v", company, d, err)
			} else if res.AsOf == "" {
				t.Errorf("Payments(%s, %s) carried no as_of", company, d)
			} else {
				ran++
			}
		}
	}
	if ran == 0 {
		t.Fatal("nothing executed; the test proves nothing")
	}
	t.Logf("%d statement variants executed against live HANA (of %d enumerated by Statements())", ran, len(Statements()))
}

// IS EVERY CATALOGUED CARD REALLY A JIVO COMPANY, IN THAT COMPANY'S OWN BOOKS?
//
// This started as a check on 'CUSTA000606' alone, because InternalCardCode is
// documented as "JIVO Mart's customer account IN OIL'S BOOKS" while the split
// applied it unconditionally to all three schemas — and CardCode numbering is
// SCHEMA-LOCAL. The split now uses a per-schema catalogue, which removes that
// specific hazard and creates the general one: NINE codes in Oil, EIGHT in Mart,
// SIX in Beverages, every one of them a hard-coded string.
//
// The direction asserted here is the dangerous one. A card wrongly IN the
// catalogue strips a real third party's sales out of EXTERNAL and reports them as
// an internal transfer — a wrong number wearing an authoritative label, which is
// the failure class this package exists to prevent. (The opposite direction, a
// JIVO card MISSING from the catalogue, is
// TestLiveRelatedPartyCatalogueMatchesOCRD.)
func TestLiveEveryCatalogedRelatedPartyIsReallyJivo(t *testing.T) {
	db := liveDB(t)
	checked := 0
	for _, c := range Companies() {
		for _, card := range RelatedPartyCards(c.Schema) {
			res, err := db.QueryReadOnly(context.Background(), guard.MCPPolicy, hana.Limits{},
				fmt.Sprintf(`SELECT "CardCode", "CardName", "CardType" FROM %q."OCRD" WHERE "CardCode" = ?`, c.Schema),
				card.CardCode)
			if err != nil {
				t.Fatalf("%s: could not read OCRD: %v", c.Name, err)
			}
			checked++
			if len(res.Rows) == 0 {
				t.Errorf("%s: catalogued card %s (%s) does not exist in OCRD at all — a stale entry excludes a code that may later be issued to a real customer",
					c.Name, card.CardCode, card.CardName)
				continue
			}
			name := stringOf(res.Rows[0]["CardName"])
			kind := stringOf(res.Rows[0]["CardType"])
			if !strings.Contains(strings.ToUpper(name), "JIVO") {
				t.Errorf("%s: catalogued card %s is %q in OCRD, which is NOT a JIVO company. This tool is stripping that party's sales out of EXTERNAL and reporting them as an internal transfer. Remove it from domain.relatedPartyCards before any %s figure is quoted.",
					c.Name, card.CardCode, name, c.Name)
			}
			if kind != "C" {
				t.Errorf("%s: catalogued card %s has \"CardType\" %q, not 'C'; the sales split is customer-side only", c.Name, card.CardCode, kind)
			}
		}
	}
	if checked == 0 {
		t.Fatal("no catalogued cards were checked; the assertion is vacuous")
	}
	t.Logf("%d catalogued related-party cards verified against OCRD", checked)
}
