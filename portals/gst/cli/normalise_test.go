package main

import (
	"encoding/json"
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// Golden tests for the normalisers. Run with -update to regenerate:
//
//	go test ./... -run TestNormalisersMatchGolden -update
//
// The inputs are the scrubbed Haryana fixtures in testdata/ — real shapes with
// synthetic identifiers — so the goldens are what a live pull actually produces,
// not what somebody imagined the portal returns.
var update = flag.Bool("update", false, "rewrite the golden .jsonl files")

// pinClock freezes nowIST so pulled_at and as_of are stable in the goldens.
func pinClock(t *testing.T) {
	t.Helper()
	old := nowIST
	fixed := time.Date(2026, 8, 21, 18, 30, 0, 0, istLoc)
	nowIST = func() time.Time { return fixed }
	t.Cleanup(func() { nowIST = old })
}

func goldenEnvelope() envelope {
	reg := Registration{Idx: "01", State: "Haryana", GSTIN: "06AAAAA0000A1Z0"}
	return newEnvelope(reg, "https://portal.example/endpoint")
}

func TestNormalisersMatchGolden(t *testing.T) {
	pinClock(t)
	e := goldenEnvelope()

	cases := []struct {
		golden  string
		fixture string
		run     func(json.RawMessage) []record
	}{
		{"filing-gstr1.jsonl", "HR-filed-GSTR1-2026-27.json", func(r json.RawMessage) []record { return normFiled(e, r) }},
		{"filing-formdetails.jsonl", "formdetails-gstr3b-072026.json", func(r json.RawMessage) []record { return normFormDetails(e, "GSTR3B", r) }},
		{"ledger-cash-balance.jsonl", "HR-cashbalance.json", func(r json.RawMessage) []record { return normCashBalance(e, r) }},
		{"ledger-cash-statement.jsonl", "HR-cashdetls-fy2627.json", func(r json.RawMessage) []record { return normCashLedger(e, r) }},
		{"ledger-credit-balance.jsonl", "HR-itcbalance.json", func(r json.RawMessage) []record { return normCreditBalance(e, r) }},
		{"ledger-credit-statement.jsonl", "HR-itcdtls-fy2627.json", func(r json.RawMessage) []record { return normCreditLedger(e, r) }},
		{"gstr3b-072026.jsonl", "HR-gstr3b-summary-072026.json", func(r json.RawMessage) []record { return normGSTR3B(e, r) }},
		{"gstr2b-072026.jsonl", "HR-gstr2b-getdata-072026.json", func(r json.RawMessage) []record { return normGSTR2B(e, r) }},
	}

	for _, tc := range cases {
		t.Run(tc.golden, func(t *testing.T) {
			raw, err := os.ReadFile(filepath.Join("testdata", tc.fixture))
			if err != nil {
				t.Fatal(err)
			}
			recs := tc.run(raw)
			if len(recs) == 0 {
				t.Fatalf("%s produced no records from %s", tc.golden, tc.fixture)
			}
			var b strings.Builder
			for _, r := range recs {
				line, err := json.Marshal(r)
				if err != nil {
					t.Fatal(err)
				}
				b.Write(line)
				b.WriteByte('\n')
			}
			path := filepath.Join("testdata", "golden", tc.golden)
			if *update {
				if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(path, []byte(b.String()), 0o644); err != nil {
					t.Fatal(err)
				}
				t.Logf("wrote %s (%d records)", path, len(recs))
				return
			}
			want, err := os.ReadFile(path)
			if err != nil {
				t.Fatalf("%v — run `go test -run TestNormalisersMatchGolden -update` to create it", err)
			}
			if b.String() != string(want) {
				t.Errorf("%s differs from the golden file.\n--- got ---\n%s\n--- want ---\n%s",
					tc.golden, firstLines(b.String(), 3), firstLines(string(want), 3))
			}
		})
	}
}

func firstLines(s string, n int) string {
	lines := strings.Split(s, "\n")
	if len(lines) > n {
		lines = append(lines[:n], "…")
	}
	return strings.Join(lines, "\n")
}

// TestEnvelopeFieldsAlwaysPresent — spec §3 says every record carries the same
// envelope. A missing key is what makes a downstream reconciliation crash on
// row 40,000 instead of row 1.
func TestEnvelopeFieldsAlwaysPresent(t *testing.T) {
	pinClock(t)
	e := goldenEnvelope()
	required := []string{"src", "gstin", "state_code", "period", "fy", "form", "record_kind", "pulled_at", "filing", "portal_ref"}
	kinds := map[string]bool{"document": true, "summary": true, "ledger_entry": true, "balance": true, "status": true}
	forms := map[string]bool{"GSTR1": true, "GSTR3B": true, "GSTR2B": true, "GSTR2A": true,
		"LEDGER_CREDIT": true, "LEDGER_CASH": true, "LEDGER_LIABILITY": true, "FILING": true}

	for _, f := range []struct {
		fixture string
		run     func(json.RawMessage) []record
	}{
		{"HR-filed-GSTR1-2026-27.json", func(r json.RawMessage) []record { return normFiled(e, r) }},
		{"formdetails-gstr3b-072026.json", func(r json.RawMessage) []record { return normFormDetails(e, "GSTR3B", r) }},
		{"HR-cashbalance.json", func(r json.RawMessage) []record { return normCashBalance(e, r) }},
		{"HR-cashdetls-fy2627.json", func(r json.RawMessage) []record { return normCashLedger(e, r) }},
		{"HR-itcbalance.json", func(r json.RawMessage) []record { return normCreditBalance(e, r) }},
		{"HR-itcdtls-fy2627.json", func(r json.RawMessage) []record { return normCreditLedger(e, r) }},
		{"HR-gstr3b-summary-072026.json", func(r json.RawMessage) []record { return normGSTR3B(e, r) }},
		{"HR-gstr2b-getdata-072026.json", func(r json.RawMessage) []record { return normGSTR2B(e, r) }},
	} {
		raw, err := os.ReadFile(filepath.Join("testdata", f.fixture))
		if err != nil {
			t.Fatal(err)
		}
		for i, rec := range f.run(raw) {
			for _, k := range required {
				if _, ok := rec[k]; !ok {
					t.Errorf("%s record %d has no %q", f.fixture, i, k)
				}
			}
			if rec["src"] != "gst-portal" {
				t.Errorf("%s record %d: src = %v", f.fixture, i, rec["src"])
			}
			if !forms[rec["form"].(string)] {
				t.Errorf("%s record %d: form %q is not in the spec's vocabulary", f.fixture, i, rec["form"])
			}
			if !kinds[rec["record_kind"].(string)] {
				t.Errorf("%s record %d: record_kind %q is not in the spec's vocabulary", f.fixture, i, rec["record_kind"])
			}
			if pr, ok := rec["portal_ref"].(record); !ok || pr["endpoint"] == "" {
				t.Errorf("%s record %d: portal_ref is not {endpoint, raw_id}", f.fixture, i)
			}
		}
	}
}

// TestAmountsAreNumbersAndDatesAreISO — the two conversions the SAP side depends
// on. A string "1,234.00" or a dd/mm/yyyy date would silently mis-join.
func TestAmountsAreNumbersAndDatesAreISO(t *testing.T) {
	pinClock(t)
	e := goldenEnvelope()
	raw, err := os.ReadFile(filepath.Join("testdata", "HR-itcdtls-fy2627.json"))
	if err != nil {
		t.Fatal(err)
	}
	recs := normCreditLedger(e, raw)
	if len(recs) < 2 {
		t.Fatal("expected several ledger entries")
	}
	for i, r := range recs {
		for _, k := range []string{"igst", "cgst", "sgst", "cess", "amount"} {
			if _, ok := r[k].(float64); !ok {
				t.Errorf("record %d: %s is %T, want a number", i, k, r[k])
			}
		}
		switch d := r["entry_date"].(type) {
		case nil: // the opening-balance row has "-" for a date, which is null
		case string:
			if _, err := time.Parse("2006-01-02", d); err != nil {
				t.Errorf("record %d: entry_date %q is not ISO", i, d)
			}
		default:
			t.Errorf("record %d: entry_date is %T", i, d)
		}
	}
	// the opening row must be classified, not guessed at
	if recs[0]["entry_class"] != "OPENING" {
		t.Errorf("first credit-ledger row is %v, want OPENING", recs[0]["entry_class"])
	}
	if recs[0]["entry_date"] != nil {
		t.Errorf("the opening row's \"-\" date must be null, got %v", recs[0]["entry_date"])
	}
	// and a real utilisation row must be tagged from its description
	found := false
	for _, r := range recs {
		if r["entry_class"] == "UTILISATION" && r["txn_type"] == "DR" {
			found = true
		}
	}
	if !found {
		t.Error("no UTILISATION entry was classified in a statement that contains set-offs")
	}
}

// TestGSTR3BTablesAreComplete — the rows §C3 names must all be produced from a
// real filed return, or the comparison has holes nobody notices.
func TestGSTR3BTablesAreComplete(t *testing.T) {
	pinClock(t)
	raw, err := os.ReadFile(filepath.Join("testdata", "HR-gstr3b-summary-072026.json"))
	if err != nil {
		t.Fatal(err)
	}
	recs := normGSTR3B(goldenEnvelope(), raw)
	got := map[string]record{}
	for _, r := range recs {
		got[r["section"].(string)+"/"+r["row"].(string)] = r
	}
	for _, want := range []string{
		"3.1/a_outward_taxable", "3.1/b_outward_zero_rated", "3.1/c_outward_nil_exempt",
		"3.1/d_inward_reverse_charge", "3.1/e_non_gst_outward",
		"4/A1_import_goods", "4/A3_reverse_charge", "4/A4_isd", "4/A5_all_other_itc",
		"4/B1_rules_reversal", "4/B2_other_reversal", "4/C_net_itc",
		"4/D1_rules_ineligible", "5.1/interest", "5.1/late_fee", "6.1/payment",
	} {
		if _, ok := got[want]; !ok {
			t.Errorf("GSTR-3B normaliser produced no %s", want)
		}
	}
	// spot-check the figures against the fixture
	a := got["3.1/a_outward_taxable"]
	if a["taxable_value"] != 223098171.32 || a["igst"] != 6086669.17 {
		t.Errorf("3.1(a) = %v / %v", a["taxable_value"], a["igst"])
	}
	pay := got["6.1/payment"]
	if pay["paid_cash"] != 226914.13 || pay["paid_itc"] != 11178071.93 {
		t.Errorf("6.1 = %v", pay)
	}
	// every period was taken from the body, not from the caller
	for _, r := range recs {
		if r["period"] != "072026" || r["fy"] != "2026-27" {
			t.Errorf("record period/fy = %v/%v, want 072026/2026-27", r["period"], r["fy"])
			break
		}
	}
	// 3.2 rows carry a place of supply
	posSeen := false
	for _, r := range recs {
		if r["section"] == "3.2" {
			posSeen = true
			if r["pos"] == "" || r["pos"] == nil {
				t.Error("a 3.2 row has no place of supply")
			}
		}
	}
	if !posSeen {
		t.Error("no 3.2 (inter-state to unregistered) rows were produced")
	}
}

// TestGSTR2BDocumentsCarryTheJoinKeys — §C4 joins on
// (gstin, supplier_gstin, inv_num_norm), so all three have to be there and
// inv_num_norm has to actually normalise.
func TestGSTR2BDocumentsCarryTheJoinKeys(t *testing.T) {
	pinClock(t)
	raw, err := os.ReadFile(filepath.Join("testdata", "HR-gstr2b-getdata-072026.json"))
	if err != nil {
		t.Fatal(err)
	}
	docs := 0
	for _, r := range normGSTR2B(goldenEnvelope(), raw) {
		if r["record_kind"] != "document" {
			continue
		}
		docs++
		for _, k := range []string{"supplier_gstin", "inv_num", "inv_num_norm", "inv_date", "taxable_value", "igst", "itc_available"} {
			if _, ok := r[k]; !ok {
				t.Errorf("2B document is missing %s", k)
			}
		}
		if _, ok := r["itc_available"].(bool); !ok {
			t.Errorf("itc_available is %T, want bool", r["itc_available"])
		}
	}
	if docs != 2 {
		t.Errorf("normalised %d documents, want 2", docs)
	}
}

func TestNormDocNum(t *testing.T) {
	cases := map[string]string{
		"VD/26-27/0412":  "VD/26/27/412",
		" vd-26_27-0412": "VD/26/27/412",
		"INV0001":        "INV0001", // not all-digits: left alone
		"000123":         "123",
		"000":            "0",
		"AB/000/07":      "AB/0/7",
	}
	for in, want := range cases {
		if got := normDocNum(in); got != want {
			t.Errorf("normDocNum(%q) = %q want %q", in, got, want)
		}
	}
}

// TestPeriodOfHandlesTheFinancialYearBoundary — January of FY 2026-27 is
// 012027, not 012026. Getting this wrong misfiles a quarter of every year.
func TestPeriodOfHandlesTheFinancialYearBoundary(t *testing.T) {
	cases := []struct{ month, fy, want string }{
		{"April", "2026-27", "042026"},
		{"December", "2026-27", "122026"},
		{"January", "2026-27", "012027"},
		{"March", "2026-27", "032027"},
		{"july", "2026-27", "072026"},
		{"Not a month", "2026-27", ""},
		{"July", "nonsense", ""},
	}
	for _, c := range cases {
		if got := periodOf(c.month, c.fy); got != c.want {
			t.Errorf("periodOf(%q,%q) = %q want %q", c.month, c.fy, got, c.want)
		}
	}
}

func TestDaysLate(t *testing.T) {
	if got := daysLate("20/08/2026", "19-08-2026"); got != -1 {
		t.Errorf("filed a day early = %v want -1", got)
	}
	if got := daysLate("20/08/2026", "25-08-2026"); got != 5 {
		t.Errorf("filed five days late = %v want 5", got)
	}
	if got := daysLate("", "25-08-2026"); got != nil {
		t.Errorf("a missing due date must give null, got %v", got)
	}
}
