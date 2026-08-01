package domain

import (
	"context"
	"errors"
	"fmt"
	"sort"
	"strconv"
	"strings"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// SalesRequest is one hana_sales_by_variety call.
type SalesRequest struct {
	// From and To are YYYY-MM-DD and BOTH INCLUSIVE.
	From, To string
	// Company is Oil / Mart / Beverages / ALL (or a full schema name).
	Company string
	// Variety filters on OITM."U_Sub_Group", case-insensitively. A value that
	// matches no item is an error, never an empty result.
	Variety string
	// IncludeType adds OITM."U_TYPE" (PREMIUM / COMMODITY / OTHERS) to the
	// grouping.
	IncludeType bool
	// NetCreditNotes subtracts credit-note lines (RIN1). Default true at the
	// tool boundary; this struct is already resolved.
	NetCreditNotes bool
}

// salesColumns is the fixed result shape, in the order it is selected.
func salesColumns(includeType bool) []string {
	cols := []string{"COMPANY", "VARIETY"}
	if includeType {
		cols = append(cols, "U_TYPE")
	}
	return append(cols,
		"EXTERNAL_NET",
		"INTERNAL_RELATED_PARTY",
		"GROSS_NET_OF_GST",
		"OF_WHICH_COMBO_PACKS",
		"UNLISTED_JIVO_CARD_NET",
		"QTY_UNITS_EXTERNAL",
		"QTY_UNITS_INTERNAL",
		"LINE_COUNT")
}

// varietyExpr is the VARIETY label, and the expression the rows are grouped by.
// It is one const so the SELECT and the GROUP BY can never drift apart.
//
// TRIM, then NULLIF, then COALESCE, and each one is load-bearing:
//
//   - NULLIF because COALESCE alone handles only NULL. An item tagged with the
//     EMPTY STRING produced a third, nameless bucket whose VARIETY rendered as
//     an empty string: not the (UNTAGGED) label, not in the variety catalogue
//     (which explicitly excludes blank tags), not offerable by the did-you-mean
//     path, and not filterable either, since an empty variety argument is the
//     no-filter sentinel. A model reading a blank variety row with real money in
//     it had no way to interpret it.
//   - TRIM because 'OLIVE ' and 'OLIVE' are the same variety typed twice. Left
//     untrimmed they split into two buckets, and the trailing-space one could
//     never be filtered for: neither side of the comparison was trimmed, so an
//     operator asking for OLIVE got it refused as an unknown tag.
const varietyExpr = `COALESCE(NULLIF(TRIM(itm."U_Sub_Group"), ''), '(UNTAGGED)')`

// varietyFilterExpr is the same tag as the filter compares it: trimmed and
// upper-cased on BOTH sides, so a stray space in SAP cannot make a valid variety
// unmatchable.
const varietyFilterExpr = `UPPER(TRIM(COALESCE(itm."U_Sub_Group", '')))`

// cardCodeExpr is the null-safe CardCode every internal/external split compares.
//
// A bare `t.CC IN (…)` AND a bare `t.CC NOT IN (…)` both evaluate to NULL when
// "CardCode" is NULL, so neither CASE fires: that document's money landed in
// GROSS and in NEITHER bucket, and the invariant EXTERNAL + INTERNAL = GROSS
// quietly stopped holding. "CardCode" is mandatory on OINV/ORIN so this is
// unlikely, but "money that disappears from a total" is the exact failure this
// package exists to prevent, and COALESCE costs nothing. A document with no
// business partner is external by definition — no NULL is a JIVO group company.
const cardCodeExpr = `COALESCE(t.CC, '')`

// buildSales assembles the statement and its bind parameters.
//
// Everything that varies with the caller — the dates, the variety — is a ? bind.
// The only interpolated values are the schema name and the company label, both
// taken from the compile-time hana.Schemas list.
//
// The joins to OITM and OCRD are LEFT OUTER on purpose: an inner join silently
// drops any invoice line with no item master row (freight, service and text
// lines), and money that disappears from a total is the failure mode this whole
// package exists to prevent. Those lines land in the '(UNTAGGED)' bucket instead.
//
// combo maps schema -> the "ItmsGrpCod" values of the combo/bundle item group,
// resolved from OITB at call time (see resolveComboGroups). A schema absent from
// the map gets a NULL OF_WHICH_COMBO_PACKS, never a 0.00 — see comboSelect.
func buildSales(companies []Company, w Window, variety string, includeType bool, netCreditNotes bool, combo map[string][]int64) (string, []any) {
	var blocks []string
	var args []any
	for _, c := range companies {
		var b strings.Builder
		fmt.Fprintf(&b, "SELECT '%s' AS COMPANY,\n", c.Name)
		b.WriteString("       " + varietyExpr + " AS VARIETY,\n")
		if includeType {
			b.WriteString(`       itm."U_TYPE" AS U_TYPE,` + "\n")
		}
		ext, internal := externalCaseExpr(c.Schema), internalCaseExpr(c.Schema)
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(SUM(CASE WHEN %s THEN t.AMT ELSE 0 END)), 2) AS EXTERNAL_NET,\n", ext)
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(SUM(CASE WHEN %s THEN t.AMT ELSE 0 END)), 2) AS INTERNAL_RELATED_PARTY,\n", internal)
		b.WriteString("       ROUND(TO_DOUBLE(SUM(t.AMT)), 2) AS GROSS_NET_OF_GST,\n")
		b.WriteString("       " + comboSelect(combo[c.Schema]) + " AS OF_WHICH_COMBO_PACKS,\n")
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(SUM(CASE WHEN %s THEN t.AMT ELSE 0 END)), 2) AS UNLISTED_JIVO_CARD_NET,\n", UnlistedRelatedPartyExpr(c.Schema, "bp"))
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(SUM(CASE WHEN %s THEN t.QTY ELSE 0 END)), 2) AS QTY_UNITS_EXTERNAL,\n", ext)
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(SUM(CASE WHEN %s THEN t.QTY ELSE 0 END)), 2) AS QTY_UNITS_INTERNAL,\n", internal)
		b.WriteString("       COUNT(*) AS LINE_COUNT\n")

		b.WriteString("FROM (SELECT h.\"CardCode\" CC, l.\"LineTotal\" AMT, l.\"Quantity\" QTY, l.\"ItemCode\" IC\n")
		fmt.Fprintf(&b, "      FROM \"%s\".\"INV1\" l\n      JOIN \"%s\".\"OINV\" h ON h.\"DocEntry\" = l.\"DocEntry\"\n", c.Schema, c.Schema)
		b.WriteString("      WHERE h.\"CANCELED\" = 'N' AND h.\"DocDate\" >= TO_DATE(?) AND h.\"DocDate\" < TO_DATE(?)")
		args = append(args, w.fromBind, w.toBind)
		if netCreditNotes {
			b.WriteString("\n      UNION ALL\n")
			b.WriteString("      SELECT h.\"CardCode\", -r.\"LineTotal\", -r.\"Quantity\", r.\"ItemCode\"\n")
			fmt.Fprintf(&b, "      FROM \"%s\".\"RIN1\" r\n      JOIN \"%s\".\"ORIN\" h ON h.\"DocEntry\" = r.\"DocEntry\"\n", c.Schema, c.Schema)
			b.WriteString("      WHERE h.\"CANCELED\" = 'N' AND h.\"DocDate\" >= TO_DATE(?) AND h.\"DocDate\" < TO_DATE(?)")
			args = append(args, w.fromBind, w.toBind)
		}
		b.WriteString(") t\n")
		fmt.Fprintf(&b, "LEFT OUTER JOIN \"%s\".\"OITM\" itm ON itm.\"ItemCode\" = t.IC\n", c.Schema)
		fmt.Fprintf(&b, "LEFT OUTER JOIN \"%s\".\"OCRD\" bp ON bp.\"CardCode\" = t.CC\n", c.Schema)
		b.WriteString("WHERE (? = '' OR " + varietyFilterExpr + " = UPPER(TRIM(?)))\n")
		args = append(args, variety, variety)
		b.WriteString("GROUP BY " + varietyExpr)
		if includeType {
			b.WriteString(", itm.\"U_TYPE\"")
		}
		blocks = append(blocks, b.String())
	}

	orderBy := "a.COMPANY, a.VARIETY"
	if includeType {
		orderBy += ", a.U_TYPE"
	}
	return clockWrap(unionAll(blocks), salesColumns(includeType), orderBy), args
}

// SalesByVariety answers "how much <variety> did we sell", the question the
// olive incident got wrong.
func SalesByVariety(ctx context.Context, r Runner, req SalesRequest) (*Response, error) {
	companies, err := ResolveCompanies(req.Company)
	if err != nil {
		return nil, err
	}
	w, err := ParseWindow(req.From, req.To)
	if err != nil {
		return nil, err
	}
	variety := strings.TrimSpace(req.Variety)
	if variety != "" {
		if err := checkVariety(ctx, r, companies, variety); err != nil {
			return nil, err
		}
	}

	combo, comboMissing, err := resolveComboGroups(ctx, r, companies)
	if err != nil {
		return nil, err
	}

	stmt, args := buildSales(companies, w, variety, req.IncludeType, req.NetCreditNotes, combo)
	res, err := r.QueryReadOnly(ctx, guard.MCPPolicy, hana.Limits{}, stmt, args...)
	if err != nil {
		return nil, err
	}

	emptyNote := "no invoice lines matched in this company for this window" + varietyPhrase(variety) +
		" — that is a real zero, not a filter that failed: an unknown variety is refused outright, so this window genuinely has no matching sales here."
	asOf, blocks, truncated := shape(res, companies, emptyNote)
	annotateRelatedParty(blocks, comboMissing)

	return &Response{
		AsOf:       asOf,
		AsOfSource: AsOfSource,
		ElapsedMS:  res.Elapsed.Milliseconds(),
		Window:     w,
		Basis:      salesBasis(w, variety, req.IncludeType, req.NetCreditNotes),
		Note:       salesNote(res, comboMissing),
		Companies:  blocks,
		Truncated:  truncated,
		SQL:        stmt,
		Params:     args,
	}, nil
}

// annotateRelatedParty attaches, to every company block, the exact cards its
// INTERNAL_RELATED_PARTY column is made of, plus any combo-group failure.
//
// The list travels WITH the figures rather than only in the shared note because
// the split is per-company and a reader comparing two blocks has to be able to
// see that they were split on different card sets.
func annotateRelatedParty(blocks []CompanyBlock, comboMissing []string) {
	miss := map[string]bool{}
	for _, c := range comboMissing {
		miss[c] = true
	}
	for i := range blocks {
		blocks[i].InternalCards = RelatedPartyCards(blocks[i].Schema)
		if miss[blocks[i].Company] {
			if blocks[i].Note != "" {
				blocks[i].Note += " "
			}
			blocks[i].Note += comboNote(blocks[i].Company)
		}
	}
}

func varietyPhrase(variety string) string {
	if variety == "" {
		return ""
	}
	return fmt.Sprintf(" and variety %q", strings.ToUpper(variety))
}

func salesBasis(w Window, variety string, includeType, netCreditNotes bool) string {
	var b strings.Builder
	b.WriteString(`net sales = SUM(INV1."LineTotal")`)
	if netCreditNotes {
		b.WriteString(` MINUS SUM(RIN1."LineTotal") (credit notes netted off)`)
	} else {
		b.WriteString(` ONLY — credit notes are NOT netted off (net_credit_notes=false), so this is sales before returns`)
	}
	fmt.Fprintf(&b, `; LINE level (SUM over INV1/RIN1), already net of GST; %s; "CANCELED" = 'N'`, w.Applied)
	b.WriteString(`; segmented by OITM."U_Sub_Group"`)
	if includeType {
		b.WriteString(` and OITM."U_TYPE"`)
	}
	if variety != "" {
		fmt.Fprintf(&b, `; filtered to UPPER(TRIM("U_Sub_Group")) = %q`, strings.ToUpper(variety))
	}
	b.WriteString(`; internal = "CardCode" IN this company's JIVO-group card list, external = every other card (C-0002; the per-company list is on each block as internal_cards)`)
	b.WriteString(`; QTY_UNITS_* is SUM(INV1."Quantity") = saleable UNITS (` + UnitsCaveat + `)`)
	b.WriteString(`; corrections C-0001 (units not cartons), C-0002 (intercompany), C-0003 (SAP tags not item names), C-0004 (combo packs)`)
	return b.String()
}

// salesNote is the fixed steer that travels with every answer.
func salesNote(res *hana.Result, comboMissing []string) string {
	n := InternalSplitNote +
		" QTY_UNITS_* is one row per saleable UNIT, never a carton — " + UnitsCaveat + " (C-0001)." +
		" OF_WHICH_COMBO_PACKS is the part of GROSS coming from the '" + ComboItemGroup + "' item group: a combo pack carries ONE variety tag for a mixed pack, so its whole value is credited to this variety (C-0004) — subtract it, or say it is counted whole. NULL there means the group could not be resolved in that company, which is not the same as 0.00."
	if len(comboMissing) > 0 {
		n += " IT IS NULL RIGHT NOW for " + strings.Join(comboMissing, " / ") + ": see that block's note."
	}
	n += " '(UNTAGGED)' collects lines whose item has no \"U_Sub_Group\" tag at all: lines with no item master row (freight, service and text lines) and items whose tag is NULL or blank. It is money, not a rounding artefact." +
		" " + BasisGapNote
	if res.Note != "" {
		n += " " + reframeTruncation(res.Note)
	}
	return n
}

// --- the combo item group, resolved to a code -----------------------------------
//
// OF_WHICH_COMBO_PACKS used to key on the item-group NAME:
//
//	CASE WHEN grp."ItmsGrpNam" = 'SALES BOM' THEN …
//
// which is verified correct today and fails silently tomorrow. Renaming an item
// group in SAP is a two-click master-data edit; the moment someone does it the
// column returns 0.00 for every company while salesNote keeps telling the model
// to "subtract it, or say it is counted whole" — a confident zero in place of the
// thing correction C-0004 exists to surface.
//
// So the name is resolved ONCE against OITB to its "ItmsGrpCod" (109 in all three
// companies, verified live 2026-08-01) and the aggregate keys on the code. When
// the name resolves to nothing, the column is NULL rather than 0.00, and the
// company's block says why: "not measured" and "measured zero" must not look the
// same, which is the same rule shape() applies to an empty answer and
// checkVariety applies to an unknown tag.

// buildComboGroupCatalog resolves the combo item group in each company.
func buildComboGroupCatalog(companies []Company) string {
	var blocks []string
	for _, c := range companies {
		blocks = append(blocks, fmt.Sprintf(`SELECT '%s' AS COMPANY, grp."ItmsGrpCod" AS GRP_CODE
FROM "%s"."OITB" grp
WHERE UPPER(TRIM(grp."ItmsGrpNam")) = '%s'`, c.Name, c.Schema, ComboItemGroup))
	}
	return unionAll(blocks) + "\nORDER BY COMPANY, GRP_CODE"
}

// comboSelect renders the OF_WHICH_COMBO_PACKS column for one company.
//
// codes are interpolated, not bound, for the same reason the schema names are:
// they came from the database as integers and are re-rendered from int64, so no
// caller text can reach the statement.
func comboSelect(codes []int64) string {
	if len(codes) == 0 {
		// CAST so the UNION ALL across companies keeps one column type even when
		// only some companies resolved the group.
		return "CAST(NULL AS DOUBLE)"
	}
	parts := make([]string, 0, len(codes))
	for _, code := range codes {
		parts = append(parts, strconv.FormatInt(code, 10))
	}
	return fmt.Sprintf(`ROUND(TO_DOUBLE(SUM(CASE WHEN itm."ItmsGrpCod" IN (%s) THEN t.AMT ELSE 0 END)), 2)`,
		strings.Join(parts, ", "))
}

// resolveComboGroups reads the combo group's code per company.
//
// A failure to resolve is NOT an error: the rest of the answer is still correct
// and useful, and refusing a whole sales figure because one supplementary column
// cannot be computed would trade a real defect for a bigger one. It is reported
// instead — NULL in the column, a sentence in the block note, and the list of
// companies in the response note.
func resolveComboGroups(ctx context.Context, r Runner, companies []Company) (map[string][]int64, []string, error) {
	res, err := r.QueryReadOnly(ctx, guard.MCPPolicy, hana.Limits{}, buildComboGroupCatalog(companies))
	if err != nil {
		return nil, nil, fmt.Errorf("could not resolve the %q item group from OITB: %w", ComboItemGroup, err)
	}
	byName := map[string][]int64{}
	for _, row := range res.Rows {
		name := stringOf(row["COMPANY"])
		if name == "" {
			continue
		}
		byName[name] = append(byName[name], asInt64(row["GRP_CODE"]))
	}
	out := map[string][]int64{}
	var missing []string
	for _, c := range companies {
		// A truncated catalogue is treated as unresolved for every company, not just
		// the ones missing from the page: a partial list cannot prove a company's
		// group is absent, and it could equally have cut a second code off a company
		// that did appear.
		if codes := byName[c.Name]; len(codes) > 0 && !res.Truncated {
			out[c.Schema] = codes
			continue
		}
		missing = append(missing, c.Name)
	}
	return out, missing, nil
}

// comboNote is the sentence that goes on a company whose combo group vanished.
func comboNote(company string) string {
	return fmt.Sprintf("OF_WHICH_COMBO_PACKS is NULL for %s, not 0.00: no OITB item group is named %q in this company any more, so the combo-pack share could not be measured. It is NOT a measured zero — combo revenue, if any, is still inside GROSS_NET_OF_GST and is still credited whole to its tagged variety (C-0004). Find the group's new name in OITB and update domain.ComboItemGroup.",
		company, ComboItemGroup)
}

// --- the variety catalogue and the typo refusal ---------------------------------

// varietyCatalogBlock lists the tagged varieties in one company. The untagged
// bucket is deliberately excluded: it is a rendering label for lines with no
// item, not a value anyone can filter on.
// It TRIMs for the same reason buildSales does: 'OLIVE ' and 'OLIVE' are one
// variety typed twice, and listing them as two valid values would be a worse
// answer than listing one.
func buildVarietyCatalog(companies []Company) string {
	var blocks []string
	for _, c := range companies {
		blocks = append(blocks, fmt.Sprintf(`SELECT '%s' AS COMPANY, TRIM(itm."U_Sub_Group") AS VARIETY, COUNT(*) AS ITEMS
FROM "%s"."OITM" itm
WHERE itm."U_Sub_Group" IS NOT NULL AND TRIM(itm."U_Sub_Group") <> ''
GROUP BY TRIM(itm."U_Sub_Group")`, c.Name, c.Schema))
	}
	return unionAll(blocks) + "\nORDER BY COMPANY, ITEMS DESC, VARIETY"
}

// checkVariety refuses a variety that tags no item.
//
// This is the C-0003 defect turned inside out. Name-matching for "OLIVE" quietly
// returned a smaller number; a mis-typed tag would quietly return zero. Both read
// as an answer. So a filter that matches nothing is an ERROR that lists what the
// valid values actually are.
func checkVariety(ctx context.Context, r Runner, companies []Company, variety string) error {
	stmt := buildVarietyCatalog(companies)
	res, err := r.QueryReadOnly(ctx, guard.MCPPolicy, hana.Limits{}, stmt)
	if err != nil {
		return fmt.Errorf("could not read the variety list from OITM to check %q: %w", variety, err)
	}
	want := strings.ToUpper(strings.TrimSpace(variety))
	known := map[string]bool{}
	items := map[string]int64{}
	for _, row := range res.Rows {
		// TrimSpace on this side too: a positive match must not depend on how
		// tidily the tag was typed into SAP.
		v := strings.TrimSpace(stringOf(row["VARIETY"]))
		if v == "" {
			continue
		}
		up := strings.ToUpper(v)
		known[up] = true
		items[up] += asInt64(row["ITEMS"])
		if up == want {
			return nil // a hit is conclusive even from a partial list
		}
	}
	if len(known) == 0 {
		return fmt.Errorf("could not read any OITM.\"U_Sub_Group\" values, so %q cannot be checked; refusing rather than returning a zero that might be a typo", variety)
	}
	// A MISS is only conclusive if the whole list was read. The catalogue query
	// runs under the same row cap as any other (hana.DefaultMaxRows), so a
	// truncated answer means the variety might be sitting in the rows that were
	// dropped — and "no item is tagged X, valid values are …" would then be a
	// confident refusal of a perfectly good variety, with an incomplete list of
	// alternatives attached. Say what actually happened instead.
	if res.Truncated {
		return fmt.Errorf("the OITM variety list came back TRUNCATED (%d rows, the row cap tripped), so %q could not be checked against the full set of tags in %s — refusing rather than guessing: a miss in a partial list is not evidence the tag does not exist. Widen the row cap, or name a company to shorten the list.",
			len(res.Rows), variety, strings.Join(companyNames(companies), " / "))
	}
	return unknownVarietyError(variety, companies, known, items)
}

// companyNames is the caller-facing list of the companies a message covers.
func companyNames(companies []Company) []string {
	out := make([]string, 0, len(companies))
	for _, c := range companies {
		out = append(out, c.Name)
	}
	return out
}

// stringOf reads a text cell. HANA hands NVARCHAR back as a string, but a
// driver that produced []byte would otherwise silently become an empty variety
// and get skipped.
func stringOf(v any) string {
	switch t := v.(type) {
	case string:
		return t
	case []byte:
		return string(t)
	}
	return ""
}

func unknownVarietyError(variety string, companies []Company, known map[string]bool, items map[string]int64) error {
	names := sortedKeys(known)
	sort.SliceStable(names, func(i, j int) bool { return items[names[i]] > items[names[j]] })

	const show = 30
	shown := names
	more := ""
	if len(names) > show {
		shown = names[:show]
		more = fmt.Sprintf(" …and %d more", len(names)-show)
	}
	where := companyNames(companies)
	msg := fmt.Sprintf("no item is tagged OITM.\"U_Sub_Group\" = %q in %s — refusing rather than reporting zero sales, because a mis-typed variety is otherwise indistinguishable from \"we sold none of it\". Valid varieties, most items first: %s%s.",
		variety, strings.Join(where, " / "), strings.Join(shown, ", "), more)
	if best := closestVariety(variety, names); best != "" {
		msg += fmt.Sprintf(" Did you mean %q?", best)
	}
	return errors.New(msg)
}

// closestVariety offers the nearest tag, preferring a containment match (a
// caller typing "olive oil" means OLIVE) over a spelling near-miss.
func closestVariety(in string, names []string) string {
	up := strings.ToUpper(strings.TrimSpace(in))
	if up == "" {
		return ""
	}
	for _, n := range names {
		if strings.Contains(up, n) || strings.Contains(n, up) {
			return n
		}
	}
	best, bestD := "", 1<<30
	for _, n := range names {
		if d := editDistance(up, n); d < bestD {
			best, bestD = n, d
		}
	}
	if bestD <= 3 {
		return best
	}
	return ""
}

// asInt64 reads a count out of a driver value. HANA hands COUNT(*) back as an
// int64, but a DECIMAL path would arrive as an exact string, so both are read.
func asInt64(v any) int64 {
	switch t := v.(type) {
	case int64:
		return t
	case int:
		return int64(t)
	case float64:
		return int64(t)
	case string:
		var n int64
		fmt.Sscanf(t, "%d", &n)
		return n
	}
	return 0
}
