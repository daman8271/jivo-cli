package domain

import (
	"context"
	"strings"
	"testing"

	"hana-sql/internal/hana"
)

// --- C-0002 is not one card code ------------------------------------------------

// THE DEFECT. The split was `CardCode <> 'CUSTA000606'` in every company, and
// the package documented itself as encoding correction C-0002. C-0002's evidence
// says in as many words that Mart's books "also carry JIVO MART branch cards
// (DL/PB/HR/KT/KR/RJ/UP) and a JIVO WELLNESS PVT LTD card needing the same
// treatment" — so the code encoded a third of the correction it cited, and every
// branch card was reported as an EXTERNAL sale.
//
// Measured live 2026-08-01, April–July 2026 (INV1."LineTotal", "CANCELED" = 'N'):
//
//	Mart CUSTA000874 JIVO MART PVT LTD - DL   Rs 9,57,70,230
//	Mart CUSTA000001 JIVO WELLNESS PVT LTD    Rs 1,94,21,973
//	Mart CUSTA000827 JIVO MART PVT LTD - HR   Rs 1,65,05,824
//
// all of it inside EXTERNAL_NET. The flagship figure carried it: Mart's June-2026
// OLIVE "external" of Rs 11,99,84,544.83 included Rs 1,52,91,011.60 (12.7%)
// billed to Mart's own Delhi branch.
func TestRelatedPartySplitCoversBranchCardsNotJustCUSTA000606(t *testing.T) {
	// Mart's own books have no CUSTA000606 at all, so the old rule's internal
	// bucket for Mart was necessarily empty: EXTERNAL was gross.
	mart := RelatedPartyCards("JIVO_MART_HANADB")
	if len(mart) < 2 {
		t.Fatalf("Mart has %d related-party cards catalogued; C-0002's evidence names a JIVO WELLNESS card AND the branch cards", len(mart))
	}
	want := map[string]bool{
		"CUSTA000874": false, // JIVO MART PVT LTD - DL, the Rs 9.58 Cr card
		"CUSTA000827": false, // JIVO MART PVT LTD - HR
		"CUSTA000001": false, // JIVO WELLNESS PVT LTD
	}
	for _, c := range mart {
		if _, ok := want[c.CardCode]; ok {
			want[c.CardCode] = true
		}
	}
	for code, found := range want {
		if !found {
			t.Errorf("Mart card %s is not classified as related-party, so its sales are still reported as EXTERNAL", code)
		}
	}

	// And the SQL actually uses the whole set, in both tools.
	w := Window{fromBind: "2026-06-01", toBind: "2026-07-01"}
	sales, _ := buildSales(Companies(), w, "", false, true, comboAll())
	turnover, _ := buildTurnover(Companies(), w)
	for label, stmt := range map[string]string{"sales": sales, "turnover": turnover} {
		for _, c := range mart {
			if !strings.Contains(stmt, "'"+c.CardCode+"'") {
				t.Errorf("%s never mentions Mart's related-party card %s (%s):\n%s", label, c.CardCode, c.CardName, stmt)
			}
		}
		// The old single-code shape must not come back.
		if strings.Contains(stmt, "<> '"+InternalCardCode+"'") {
			t.Errorf("%s is back to splitting on %s alone:\n%s", label, InternalCardCode, stmt)
		}
	}
}

// Card codes are SCHEMA-LOCAL, and applying one company's list to another is how
// a party gets stripped out of EXTERNAL under the wrong name. CUSTA000827 is JIVO
// MART - HR in Mart's books and JIVO MART PRIVATE LIMITED (HARYANA) in Oil's;
// CUSTA000874 exists only in Mart's.
func TestRelatedPartyListsAreKeptPerSchema(t *testing.T) {
	oil := codesOf(RelatedPartyCards("JIVO_OIL_HANADB"))
	mart := codesOf(RelatedPartyCards("JIVO_MART_HANADB"))
	if oil["CUSTA000874"] {
		t.Error("Oil's list contains CUSTA874, which is a card in MART's books; card codes are schema-local")
	}
	if !mart["CUSTA000874"] {
		t.Error("Mart's list lost CUSTA000874")
	}
	if !oil["CUSTA000606"] {
		t.Error("Oil's list lost CUSTA000606, the card correction C-0002 is actually about")
	}

	// The statement for one company may only carry that company's codes.
	stmt, _ := buildSales([]Company{{Name: "Oil", Schema: "JIVO_OIL_HANADB"}},
		Window{fromBind: "2026-06-01", toBind: "2026-07-01"}, "", false, false, comboOil())
	if strings.Contains(stmt, "CUSTA000874") {
		t.Errorf("an Oil-only statement carries a Mart card code:\n%s", stmt)
	}
}

func codesOf(cards []RelatedParty) map[string]bool {
	out := map[string]bool{}
	for _, c := range cards {
		out[c.CardCode] = true
	}
	return out
}

// EXTERNAL + INTERNAL = GROSS must survive the change: the two CASE predicates
// have to be exact complements, or money leaks between the buckets.
func TestExternalAndInternalPredicatesAreComplements(t *testing.T) {
	for _, s := range []string{"JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB"} {
		in, out := internalCaseExpr(s), externalCaseExpr(s)
		if in != strings.Replace(out, " NOT IN (", " IN (", 1) {
			t.Errorf("%s: internal %q is not the exact complement of external %q", s, in, out)
		}
	}
}

// The codes are interpolated into an IN list rather than bound, so they must be
// incapable of carrying a quote. This is the tripwire that keeps that true.
func TestRelatedPartyCardCodesAreInert(t *testing.T) {
	seen := 0
	for schema, cards := range relatedPartyCards {
		if len(cards) == 0 {
			t.Errorf("%s has an empty related-party list; drop the key rather than leaving an empty one", schema)
		}
		for _, c := range cards {
			seen++
			if !cardCodePattern.MatchString(c.CardCode) {
				t.Errorf("%s: CardCode %q is not of the inert form LETTERS+DIGITS and must never be interpolated into SQL", schema, c.CardCode)
			}
			if strings.ContainsAny(c.CardCode, "'\"\\;-") {
				t.Errorf("%s: CardCode %q carries a SQL metacharacter", schema, c.CardCode)
			}
			if strings.TrimSpace(c.CardName) == "" {
				t.Errorf("%s: CardCode %q has no CardName, so the answer cannot say what it is", schema, c.CardCode)
			}
		}
	}
	if seen == 0 {
		t.Fatal("no related-party cards at all; the assertion is vacuous")
	}
}

// The answer has to be auditable from the answer alone: which cards a company's
// INTERNAL column was summed over travels with the figures.
func TestEveryCompanyBlockNamesItsInternalCards(t *testing.T) {
	sales := mustSales(t, newRecordingRunner(salesResult()),
		SalesRequest{From: "2026-06-01", To: "2026-06-30", Company: AllCompanies})
	for _, b := range sales.Companies {
		if len(b.InternalCards) == 0 {
			t.Errorf("%s's block does not say which cards INTERNAL_RELATED_PARTY covers", b.Company)
		}
		for _, c := range b.InternalCards {
			if c.CardName == "" {
				t.Errorf("%s: card %s has no name in the payload", b.Company, c.CardCode)
			}
		}
	}
	// And the label no longer claims the bucket is only JIVO Mart.
	for _, c := range salesColumns(false) {
		if c == "TO_JIVO_MART_INTERNAL" {
			t.Error("the internal column is still called TO_JIVO_MART_INTERNAL while it now also holds branch and JIVO WELLNESS sales")
		}
	}
}

// --- the drift alarm ------------------------------------------------------------

// A catalogue of codes is a frozen constant, and a frozen constant is exactly how
// CUSTA000874 came to be missing in the first place. UNLISTED_JIVO_CARD_NET is
// the runtime tripwire: money inside EXTERNAL that went to a card whose OCRD
// "CardName" says JIVO but which is not catalogued. It is the ONLY name match in
// the package and it can only add a warning — C-0003 forbids name matching as a
// classifier, not as an alarm.
func TestUnlistedRelatedPartyAlarmIsPresentAndCannotClassify(t *testing.T) {
	w := Window{fromBind: "2026-06-01", toBind: "2026-07-01"}
	sales, _ := buildSales(Companies(), w, "", false, true, comboAll())
	turnover, _ := buildTurnover(Companies(), w)

	for label, stmt := range map[string]string{"sales": sales, "turnover": turnover} {
		if !strings.Contains(stmt, "UNLISTED_JIVO_CARD_NET") {
			t.Fatalf("%s has no drift alarm column, so a new branch card lands in EXTERNAL silently:\n%s", label, stmt)
		}
		if !strings.Contains(stmt, `LIKE '`+JivoNamePattern+`'`) {
			t.Errorf("%s's alarm does not look at OCRD.\"CardName\":\n%s", label, stmt)
		}
		if !strings.Contains(stmt, `"OCRD" bp ON bp."CardCode"`) {
			t.Errorf("%s does not join OCRD, so the alarm has no name to read:\n%s", label, stmt)
		}
		// The name pattern must NOT appear in either money bucket's predicate.
		for _, bucket := range []string{"AS EXTERNAL_NET", "AS INTERNAL_RELATED_PARTY", "AS EXTERNAL_TURNOVER"} {
			if i := strings.Index(stmt, bucket); i >= 0 {
				line := stmt[strings.LastIndex(stmt[:i], "\n")+1 : i]
				if strings.Contains(line, "CardName") {
					t.Errorf("%s classifies money by NAME in %s, which correction C-0003 forbids: %s", label, bucket, line)
				}
			}
		}
	}

	// And the shipped prose tells the model what a non-zero alarm means.
	for _, must := range []string{"UNLISTED_JIVO_CARD_NET", "UPPER BOUND", "drift alarm"} {
		if !strings.Contains(InternalSplitNote, must) {
			t.Errorf("InternalSplitNote does not explain the alarm (%q):\n%s", must, InternalSplitNote)
		}
	}
	// The admission that branch cards were NOT handled must be gone.
	for _, dead := range []string{"arguably need the same treatment", "does NOT classify those as internal", "external-of-CUSTA000606 only"} {
		if strings.Contains(InternalSplitNote, dead) {
			t.Errorf("InternalSplitNote still says %q, which is no longer true:\n%s", dead, InternalSplitNote)
		}
	}
}

// --- the combo group is keyed on a code, not a renameable name -------------------

// OF_WHICH_COMBO_PACKS keyed on grp."ItmsGrpNam" = 'SALES BOM'. Renaming an item
// group is a two-click master-data edit, and the moment someone does it the
// column reads 0.00 for every company while salesNote keeps telling the model to
// "subtract it, or say it is counted whole" — a confident zero standing in for
// the very thing C-0004 exists to surface.
func TestComboPacksKeyOnTheGroupCodeNotItsName(t *testing.T) {
	w := Window{fromBind: "2026-06-01", toBind: "2026-07-01"}
	stmt, _ := buildSales(Companies(), w, "", false, true, comboAll())

	if strings.Contains(stmt, `grp."ItmsGrpNam"`) {
		t.Errorf("the aggregate still keys combo packs on the item-group NAME, which a rename in SAP silently turns into 0.00:\n%s", stmt)
	}
	if !strings.Contains(stmt, `itm."ItmsGrpCod" IN (109)`) {
		t.Errorf("the aggregate does not key combo packs on the resolved \"ItmsGrpCod\":\n%s", stmt)
	}
	// The name is used exactly once, to resolve the code.
	cat := buildComboGroupCatalog(Companies())
	if !strings.Contains(cat, ComboItemGroup) || !strings.Contains(cat, `"OITB"`) {
		t.Errorf("the combo group is not resolved from OITB by name:\n%s", cat)
	}
}

// An unresolvable group must produce NULL and a note, never 0.00. "Not measured"
// and "measured zero" must not look the same — the same rule the empty-window and
// unknown-variety paths already follow.
func TestUnresolvableComboGroupIsNullAndSaysSo(t *testing.T) {
	stmt, _ := buildSales(Companies(), Window{fromBind: "2026-06-01", toBind: "2026-07-01"},
		"", false, true, map[string][]int64{})
	if !strings.Contains(stmt, "CAST(NULL AS DOUBLE) AS OF_WHICH_COMBO_PACKS") {
		t.Fatalf("an unresolved combo group still produces a numeric column, so a rename reads as Rs 0 of combo packs:\n%s", stmt)
	}

	// End to end: the group resolves to nothing, and the answer says so per company.
	r := &recordingRunner{
		combo: &hana.Result{Rows: []map[string]any{}, RowCount: 0},
		agg:   salesResult(),
	}
	res, err := SalesByVariety(context.Background(), r, SalesRequest{
		From: "2026-06-01", To: "2026-06-30", Company: "Oil", NetCreditNotes: true,
	})
	if err != nil {
		t.Fatalf("SalesByVariety: %v", err)
	}
	blk := res.Companies[0]
	if !strings.Contains(blk.Note, "NULL for Oil, not 0.00") {
		t.Errorf("Oil's block does not say the combo share is unmeasured rather than zero: %q", blk.Note)
	}
	if !strings.Contains(res.Note, "IT IS NULL RIGHT NOW for Oil") {
		t.Errorf("the response note does not flag the unresolved combo group: %s", res.Note)
	}
}

// A truncated combo catalogue is not evidence a company's group is missing, and
// it could equally have cut a second code off a company that did appear.
func TestTruncatedComboCatalogueIsTreatedAsUnresolved(t *testing.T) {
	r := &recordingRunner{
		combo: &hana.Result{
			Rows:      []map[string]any{{"COMPANY": "Oil", "GRP_CODE": int64(109)}},
			RowCount:  1,
			Truncated: true,
		},
		agg: salesResult(),
	}
	got, missing, err := resolveComboGroups(context.Background(), r, Companies())
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 0 {
		t.Errorf("a truncated catalogue still resolved %d schemas: %v", len(got), got)
	}
	if len(missing) != len(Companies()) {
		t.Errorf("missing = %v, want every company treated as unresolved on a truncated catalogue", missing)
	}
}
