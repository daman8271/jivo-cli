// Package domain holds JIVO's settled business definitions as FIXED SQL
// templates, so the definitions cannot be gotten wrong by a model writing its
// own SQL from a phone.
//
// Why this package exists. JIVO records settled truths as corrections in
// harness/corrections/. Those load into local CLI sessions and reach the remote
// MCP not at all, so an operator asking from a phone gets an assistant that has
// never been told any of them. That gap produced a measured failure: asked for
// "olive oil sales last month", the remote assistant classified products by
// MATCHING ITEM NAMES — the exact thing correction C-0003 forbids — reported
// Mart at Rs 9.53 Cr against a true Rs 12.00 Cr, and then flip-flopped across
// four totals in one conversation. A description cannot fix that; only a tool
// that computes the right thing can.
//
// The rules encoded here, each with its correction record:
//
//	C-0001  INV1."Quantity" is saleable UNITS ("NumInSale" = 1), never cartons.
//	        Mostly bottles, but not only — see UnitsCaveat.
//	C-0002  CardCode 'CUSTA000606' is JIVO Mart buying from Oil — an
//	        INTERCOMPANY transfer. Every figure is split external / internal so
//	        the two can never be added together by accident.
//	C-0003  Varieties come from OITM."U_Sub_Group" (and "U_TYPE"), never from
//	        item names.
//	C-0004  A combo pack carries ONE variety tag for a mixed pack, so its whole
//	        value lands in that variety. Reported as its own column rather than
//	        hidden.
//
// READ-ONLY, BY CONSTRUCTION. Nothing here opens a connection or sends SQL. Every
// statement is handed to Runner.QueryReadOnly — which on the real *hana.DB is the
// SAME entry point hana_query uses, so a domain query passes guard.Check layers
// 0-3, the statement deadline, the in-flight semaphore, HANA's READ ONLY
// transaction and the row/byte caps exactly like any user query. There is no
// privileged path. TestDomainStatementsPassGuard proves every template variant
// clears the guard, so a template can never be "fixed" by relaxing the guard.
//
// Statement text is FIXED. The only things interpolated are schema names and
// company labels drawn from hana.Schemas / hana.SchemaCompany — a compile-time
// list. Every caller-supplied value (dates, variety) is a ? bind parameter.
package domain

import (
	"context"
	"errors"
	"fmt"
	"sort"
	"strings"
	"time"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// Runner is the one database capability this package needs: the read-only query
// entry point of *hana.DB. Depending on the interface rather than the concrete
// type keeps the SQL testable with no database in the process, and makes it
// impossible for this package to reach any other DB method.
type Runner interface {
	QueryReadOnly(ctx context.Context, p guard.Policy, lim hana.Limits, stmt string, args ...any) (*hana.Result, error)
}

// InternalCardCode is JIVO Mart's customer account in Oil's books (C-0002).
// Sales billed to it are an intercompany stock transfer, not an outside sale;
// adding Oil's and Mart's gross figures double-counts it.
const InternalCardCode = "CUSTA000606"

// ComboItemGroup is the OITB item group that holds combo/bundle SKUs (C-0004).
// Verified live 2026-08-01: 66 olive-tagged SKUs in Oil and 66 in Mart sit in
// this group, each bundling olive with canola or mustard under a single OLIVE
// tag, so their whole value is credited to olive.
const ComboItemGroup = "SALES BOM"

// AsOfColumn is the server-clock column every domain statement selects.
const AsOfColumn = "AS_OF_UTC"

// AsOfSource is what the tools report about their as_of. Unlike the generic
// tools (which stamp answers with the MCP host clock), a domain answer carries
// the database's own clock, read in the SAME statement as the figures — so a
// month-end close can be reproduced against a stated instant.
const AsOfSource = "hana-server-clock (CURRENT_UTCTIMESTAMP selected in the same statement as the figures)"

// clockSelect reads the HANA server clock. It is LEFT-JOINed with the aggregate
// on the clock side so a zero-row answer still carries a timestamp: "no sales"
// and "no answer" must not look the same.
const clockSelect = `(SELECT TO_VARCHAR(CURRENT_UTCTIMESTAMP, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS ` + AsOfColumn + ` FROM DUMMY) c`

// --- companies -----------------------------------------------------------------

// Company is one SAP company database, named the way an operator says it.
type Company struct {
	Name   string `json:"company"`
	Schema string `json:"schema"`
}

// Companies returns all three, in the fixed hana.Schemas order.
func Companies() []Company {
	out := make([]Company, 0, len(hana.Schemas))
	for _, s := range hana.Schemas {
		out = append(out, Company{Name: hana.SchemaCompany[s], Schema: s})
	}
	return out
}

// AllCompanies is the value the `company` argument takes to mean "every company,
// reported separately".
const AllCompanies = "ALL"

// ResolveCompanies turns the caller's company argument into schemas.
//
// An unrecognised value is an ERROR, never an empty result — the same rule
// hana.resolveSchemas enforces, for the same reason: a one-letter typo is
// otherwise indistinguishable from "this company sold nothing".
func ResolveCompanies(in string) ([]Company, error) {
	in = strings.TrimSpace(in)
	if in == "" || strings.EqualFold(in, AllCompanies) {
		return Companies(), nil
	}
	for _, c := range Companies() {
		if strings.EqualFold(c.Name, in) || strings.EqualFold(c.Schema, in) {
			return []Company{c}, nil
		}
	}
	return nil, unknownCompanyError(in)
}

func unknownCompanyError(in string) error {
	msg := fmt.Sprintf("unknown company %q — refusing rather than returning an empty result, because a typo is otherwise indistinguishable from \"this company sold nothing\". Valid values: %s (or the full schema names %s), or %q for every company reported separately.",
		in, "Oil / Mart / Beverages", strings.Join(hana.Schemas, ", "), AllCompanies)
	if best := closestCompany(in); best != "" {
		msg += fmt.Sprintf(" Did you mean %q?", best)
	}
	return errors.New(msg)
}

// closestCompany guesses what the caller meant, so a refusal is self-correcting.
func closestCompany(in string) string {
	up := strings.ToUpper(strings.TrimSpace(in))
	if up == "" {
		return ""
	}
	if len(up) >= 3 {
		hit := ""
		for _, c := range Companies() {
			if strings.Contains(strings.ToUpper(c.Name), up) || strings.Contains(c.Schema, up) {
				if hit != "" {
					return "" // ambiguous: say nothing rather than guess
				}
				hit = c.Name
			}
		}
		if hit != "" {
			return hit
		}
	}
	// Near-miss spelling, measured against BOTH the company name and the full
	// schema name: "JIVO_BEVERAGE_HANADB" (one missing S) is one edit from the
	// schema and nine from the word "Beverages", and it is the typo that actually
	// happens.
	best, bestD := "", 1<<30
	for _, c := range Companies() {
		for _, cand := range []string{strings.ToUpper(c.Name), c.Schema} {
			if d := editDistance(up, cand); d < bestD {
				best, bestD = c.Name, d
			}
		}
	}
	if bestD <= 3 {
		return best
	}
	return ""
}

// editDistance is Levenshtein, used only to say "did you mean".
func editDistance(a, b string) int {
	prev := make([]int, len(b)+1)
	cur := make([]int, len(b)+1)
	for j := range prev {
		prev[j] = j
	}
	for i := 1; i <= len(a); i++ {
		cur[0] = i
		for j := 1; j <= len(b); j++ {
			cost := 1
			if a[i-1] == b[j-1] {
				cost = 0
			}
			cur[j] = min(min(cur[j-1]+1, prev[j]+1), prev[j-1]+cost)
		}
		prev, cur = cur, prev
	}
	return prev[len(b)]
}

// --- the date window ------------------------------------------------------------

const dateLayout = "2006-01-02"

// Window is the date range, as the caller asked for it and as it was applied.
//
// `to` is INCLUSIVE, because that is how a person asks ("1 to 30 June"). The
// statement binds to+1 day and compares half-open, which is the only way to
// include every document on the final day: SAP B1 date columns are TIMESTAMP, so
// `<= '2026-06-30'` silently drops anything stamped later than midnight. Applied
// echoes the comparison actually sent, so the caller can check the boundary
// instead of trusting it.
type Window struct {
	From    string `json:"from"`
	To      string `json:"to"`
	Applied string `json:"applied"`

	fromBind string
	toBind   string
}

// ParseWindow validates the range and computes the half-open binds.
func ParseWindow(from, to string) (Window, error) {
	f, err := parseDate("from", from)
	if err != nil {
		return Window{}, err
	}
	t, err := parseDate("to", to)
	if err != nil {
		return Window{}, err
	}
	if t.Before(f) {
		return Window{}, fmt.Errorf("the window runs backwards: from=%s is after to=%s (both dates are INCLUSIVE)", from, to)
	}
	next := t.AddDate(0, 0, 1).Format(dateLayout)
	return Window{
		From:     f.Format(dateLayout),
		To:       t.Format(dateLayout),
		Applied:  fmt.Sprintf(`"DocDate" >= '%s' AND "DocDate" < '%s'`, f.Format(dateLayout), next),
		fromBind: f.Format(dateLayout),
		toBind:   next,
	}, nil
}

func parseDate(name, v string) (time.Time, error) {
	v = strings.TrimSpace(v)
	if v == "" {
		return time.Time{}, fmt.Errorf("missing required argument: %s (a date as YYYY-MM-DD)", name)
	}
	t, err := time.Parse(dateLayout, v)
	if err != nil || t.Format(dateLayout) != v {
		return time.Time{}, fmt.Errorf("%s=%q is not a date in YYYY-MM-DD form, e.g. \"2026-06-01\"", name, v)
	}
	return t, nil
}

// --- the response ---------------------------------------------------------------

// Response is what every domain tool returns.
//
// SQL and Params carry the EXACT statement sent and the values bound to it, so
// the answer is auditable and re-runnable. They are not interpolated into one
// display string on purpose: a rendered statement that differs from the one
// executed is worse than no statement at all.
type Response struct {
	AsOf       string         `json:"as_of"`
	AsOfSource string         `json:"as_of_source"`
	ElapsedMS  int64          `json:"elapsed_ms"`
	Window     Window         `json:"window"`
	Basis      string         `json:"basis"`
	Note       string         `json:"note"`
	Companies  []CompanyBlock `json:"companies"`
	Truncated  bool           `json:"truncated"`
	SQL        string         `json:"sql"`
	Params     []any          `json:"params"`
}

// CompanyBlock is one company's rows. A company with nothing to report still
// gets a block, with a note saying so — an omitted company reads as an answer
// that covered it.
type CompanyBlock struct {
	Company string           `json:"company"`
	Schema  string           `json:"schema"`
	Rows    []map[string]any `json:"rows"`
	Note    string           `json:"note,omitempty"`
	// InternalCards is exactly which JIVO-group cards this company's
	// INTERNAL_RELATED_PARTY column was summed over. The split is per-company (card
	// codes are schema-local), so a reader comparing two blocks has to be able to
	// see they were split on different sets — and a wrong split is the defect that
	// put Rs 1.53 Cr of Mart's own Delhi branch into "EXTERNAL".
	InternalCards []RelatedParty `json:"internal_cards,omitempty"`
}

// truncatedEmptyNote replaces the "this is a real zero" note when the row cap
// tripped.
//
// A truncated answer had rows dropped, so a company with no rows in the payload
// might simply be one whose rows were cut — and every emptyNote in this package
// says the opposite in as many words ("that is a real zero, not a filter that
// failed", "a genuine zero"). Asserting a zero next to `"truncated": true` in the
// same payload is the confident-wrong-number failure this package exists to
// prevent, so when the cap trips the note says what actually happened.
func truncatedEmptyNote(company string) string {
	return fmt.Sprintf("NOT a zero, and NOT measured: the row cap tripped on this query, so the answer is INCOMPLETE and %s has no rows in what came back. Its rows may simply be among the ones dropped. Re-run for this company alone, or narrow the window, before reporting any figure for it.", company)
}

// shape turns one hana.Result into per-company blocks.
//
// It lifts AS_OF_UTC out of the rows (a timestamp repeated on every row invites
// a model to treat it as data) and drops the all-NULL placeholder row the clock
// LEFT JOIN produces when the aggregate is empty.
func shape(res *hana.Result, companies []Company, emptyNote string) (asOf string, blocks []CompanyBlock, truncated bool) {
	byCompany := map[string][]map[string]any{}
	for _, row := range res.Rows {
		if v, ok := row[AsOfColumn].(string); ok && v != "" && asOf == "" {
			asOf = v
		}
		name, _ := row["COMPANY"].(string)
		if name == "" {
			continue // the placeholder row from the clock join: no aggregate rows
		}
		clean := make(map[string]any, len(row)-1)
		for k, v := range row {
			if k == AsOfColumn || k == "COMPANY" {
				continue
			}
			clean[k] = v
		}
		byCompany[name] = append(byCompany[name], clean)
	}
	for _, c := range companies {
		b := CompanyBlock{Company: c.Name, Schema: c.Schema, Rows: byCompany[c.Name]}
		if len(b.Rows) == 0 {
			b.Rows = []map[string]any{}
			// The caller's emptyNote asserts a genuine zero. That assertion is only
			// available when the whole result was read.
			if res.Truncated {
				b.Note = truncatedEmptyNote(c.Name)
			} else {
				b.Note = emptyNote
			}
		}
		blocks = append(blocks, b)
	}
	return asOf, blocks, res.Truncated
}

// --- statement assembly ---------------------------------------------------------

// unionAll joins the per-company blocks. Blocks are generated from the fixed
// schema list, never from caller text.
func unionAll(blocks []string) string {
	return strings.Join(blocks, "\nUNION ALL\n")
}

// clockWrap wraps an aggregate in the server-clock scaffold.
//
// cols are the aggregate's column names, listed explicitly rather than as a.* so
// the result shape is fixed and reviewable. The join is LEFT OUTER with the
// CLOCK on the driving side, which is what guarantees a timestamp even when the
// aggregate returns nothing.
func clockWrap(agg string, cols []string, orderBy string) string {
	var b strings.Builder
	b.WriteString("WITH AGG AS (\n")
	b.WriteString(agg)
	b.WriteString("\n)\nSELECT c.")
	b.WriteString(AsOfColumn)
	b.WriteString(" AS ")
	b.WriteString(AsOfColumn)
	for _, c := range cols {
		fmt.Fprintf(&b, ",\n       a.%s AS %s", c, c)
	}
	b.WriteString("\nFROM ")
	b.WriteString(clockSelect)
	b.WriteString("\nLEFT OUTER JOIN AGG a ON 1 = 1\nORDER BY ")
	b.WriteString(orderBy)
	return b.String()
}

// --- shared notes ---------------------------------------------------------------

// BasisGapNote explains why hana_turnover and hana_sales_by_variety can disagree.
// It is one const so the two tools cannot tell an operator different stories.
//
// IT USED TO SAY HEADER FREIGHT, and it used to call the gap "slight". Both are
// false on these books, and a model repeating either would hand Accounts a
// confident wrong reason — the exact class of defect this package exists to
// eliminate.
//
// FREIGHT IS NOT THE CAUSE. Measured live 2026-08-01 against OINV."TotalExpns"
// with "CANCELED" = 'N':
//
//	Oil        3 invoices carry freight, Rs 22,500 ALL TIME (Rs 15,000 since
//	           2025-04-01, against 11,982 invoices in that window)
//	Mart       0 invoices, Rs 0
//	Beverages  0 invoices, Rs 0
//
// Freight is therefore real but immaterial — Rs 15,000 cannot explain a gap of
// Rs 11.22 Cr. ("Zero on every invoice" would be tidier and is what an earlier
// revision of this note claimed; it is wrong, and a note that overstates its own
// evidence is not worth more than the one it replaced.) "DiscSum" is likewise
// ~0: 218 Oil and 1,552 Mart documents carry one, totalling under Rs 1.
//
// THE CAUSE IS BRANCH STOCK-TRANSFER INVOICES. On a transfer to JIVO's own
// branch the header carries only the GST, so "DocTotal" is almost exactly
// "VatSum" and the header nets to ~0, while INV1 still carries the full value.
// Mart DocEntry 35662 is the shape of it: "DocTotal" 2,28,748.00, "VatSum"
// 2,28,747.65, header net Rs 0.35, and 16 lines totalling Rs 45,74,953.
//
// THE GAP IS NOT SLIGHT, and it is entirely those cards. Mart, April–July 2026,
// as the two tools actually report it (both net of credit notes): header
// Rs 76.50 Cr vs line Rs 87.72 Cr — Rs 11.23 Cr, 12.8%. June alone: Rs 23.18 Cr
// vs Rs 27.97 Cr, 17.1%. Attributed by card on the invoice side, Rs 9.577 Cr of
// that gap is CUSTA000874 (JIVO MART - DL) and Rs 1.651 Cr is CUSTA000827 (JIVO
// MART - HR); across all 4,059 documents every other card's cumulative gap is
// under Rs 330, i.e. rounding.
//
// And the reconciliation holds exactly. Measured through the tools on
// 2026-08-01, Mart April–July EXTERNAL is Rs 74.55 Cr on BOTH bases — a gap of
// Rs 0.00. That is why this note tells the reader to compare EXTERNAL to
// EXTERNAL: on that column the two tools agree to the rupee, and it is only
// GROSS that diverges.
const BasisGapNote = "hana_turnover and hana_sales_by_variety are computed on DIFFERENT BASES and will not tie out: " +
	"turnover is HEADER level (OINV.\"DocTotal\" - \"VatSum\"), this tool is LINE level (SUM over INV1/RIN1). " +
	"The gap is MATERIAL, not slight — Mart April–July 2026: header Rs 76.50 Cr vs line Rs 87.72 Cr, a Rs 11.23 Cr / 12.8% difference, and 17.1% in June alone. " +
	"It is NOT header freight: measured 2026-08-01, OINV.\"TotalExpns\" is non-zero on just 3 Oil invoices totalling Rs 22,500 all-time and is Rs 0 in Mart and Beverages, and \"DiscSum\" totals under Rs 1 — do not offer freight as the reason. " +
	"What drives it is BRANCH STOCK-TRANSFER invoices, whose header is GST-only (\"DocTotal\" is almost exactly \"VatSum\", so the header nets to ~0) while the lines keep their full value; that is why the LINE total is the HIGHER one. " +
	"Every rupee of Mart's Rs 11.23 Cr gap sits on CUSTA000874 and CUSTA000827, both JIVO MART branch cards; no other card differs by more than Rs 330 in four months. " +
	"So compare EXTERNAL to EXTERNAL: on that column the two tools agree to the rupee (Mart April–July, Rs 74.55 Cr on both bases, gap Rs 0.00), and only GROSS diverges. Quote one basis, say which, and give this as the reason the other figure differs."

// UnitsCaveat is what QTY_UNITS_* actually counts.
//
// The columns were called QTY_BOTTLES_* and the note said "quantities are single
// BOTTLES (InvntryUom=PCS)". The C-0001 half of that is sound and verified —
// "NumInSale" is 1 on every item, so INV1."Quantity" is saleable units and never
// cartons, and the x20 carton error the correction targets is genuinely
// prevented. The "every unit is a bottle" half is not: of 185 Oil olive-tagged
// items, 111 are PCS, 62 have no UoM at all, 10 are LTR, 1 DRM and 1 SET, and a
// June 2026 answer counted 1,640 Mart 'SET' units (Rs 16.63 lakh) and 5 Oil 'DRM'
// drums (Rs 3.00 lakh) as "bottles". Summing across units of measure is the right
// thing for the question people ask; calling the result bottles is not.
const UnitsCaveat = "SUM(INV1.\"Quantity\") with \"NumInSale\" = 1 on every item, so this is saleable UNITS and never cartons — the '20 PCS' in an item name is carton configuration and multiplying by it inflates volume about 20x. " +
	"Most units are single bottles (InvntryUom PCS) but NOT all: a minority of SKUs are LTR, DRM or SET, and some carry no UoM at all, so this is a count of units sold across mixed units of measure, not a bottle count. Do not call it bottles"

// InternalSplitNote is repeated on every sales-shaped answer. It is the sentence
// the olive incident needed and did not have.
//
// It used to describe a split on 'CUSTA000606' alone and then admit, in its own
// last sentence, that Mart's branch cards "arguably need the same treatment" and
// were not getting it. They do need it and they now get it: see relatedparty.go
// for the catalogue, the measurement and why it is keyed on codes rather than
// names.
const InternalSplitNote = "INTERNAL_RELATED_PARTY is sales billed to JIVO's OWN companies and branches — the intercompany/branch-transfer leg, not an outside sale; EXTERNAL is everything else. " +
	"Each company block lists the exact cards in internal_cards, because CardCode numbering is SCHEMA-LOCAL: 'CUSTA000827' is JIVO MART - HR in Mart's books and JIVO MART PRIVATE LIMITED (HARYANA) in Oil's, and Mart's books have no 'CUSTA000606' at all. " +
	"Quote EXTERNAL unless asked for gross, say which one you quoted, and NEVER add two companies' gross together — the Oil-to-Mart transfer would be counted twice (correction C-0002). " +
	"UNLISTED_JIVO_CARD_NET is a drift alarm, not a figure to quote: it is the money inside EXTERNAL that went to a card whose OCRD \"CardName\" says JIVO but which is not in the catalogue. If it is non-zero, SAP has a JIVO-group card this tool has not been told about, so treat EXTERNAL as an UPPER BOUND, say so, and get the card added."

// --- truncation advice ----------------------------------------------------------

// DomainTruncationAdvice replaces the generic row-cap steer on a domain answer.
//
// hana.QueryReadOnly appends "aggregate server-side with SUM/COUNT/GROUP BY
// instead of paging rows" whenever the cap trips. For a hand-written hana_query
// that is exactly right. For a domain tool it is impossible to follow: the
// statement IS a server-side aggregate, and the caller has no knob that reshapes
// it — the only arguments are the window and the company. Telling a model to do
// the thing that has already been done leaves it with nowhere to go, which is the
// same misdirection the catalog listing had before hana grew catalogAdvice.
const DomainTruncationAdvice = "this answer is ALREADY a server-side aggregate and the tool has no argument that reshapes it, so do not try to aggregate or page: ask for ONE company instead of ALL, shorten the window, or (on hana_sales_by_variety) pass a single `variety` — and until then treat any company with no rows as UNMEASURED, not as zero"

// reframeTruncation swaps the generic advice for the domain one.
//
// It is anchored on hana.QueryTruncationAdvice() — the exported constant, not a
// copy of its words — so the two cannot drift apart silently;
// TestDomainTruncationAdviceReplacesTheGenericOne asserts the swap actually
// happens. Doing it here rather than by adding a privileged query path is
// deliberate: every domain statement still goes through the SAME
// Runner.QueryReadOnly, guard.Check and read-only transaction as any other query.
func reframeTruncation(note string) string {
	if note == "" {
		return ""
	}
	return strings.ReplaceAll(note, hana.QueryTruncationAdvice(), DomainTruncationAdvice)
}

// --- guard proof ----------------------------------------------------------------

// Statements returns EVERY statement variant this package can send, so
// TestDomainStatementsPassGuard can prove they all clear guard.Check under
// guard.MCPPolicy. It is the same device internal/hana uses for the catalog SQL,
// and it is what turns "these queries are read-only" from a claim into a test.
//
// Any new template, or any new branch inside an existing one, must be added here
// or the guard proof silently stops covering it.
func Statements() []string {
	var out []string

	// Every company set a caller can select: all three together, and each one on
	// its own. Enumerating the single-company sets is not redundancy — it is what
	// keeps the guard proof honest if a company ever needs its own block (the
	// contingency for a per-company UDF that Beverages turned out not to need),
	// because then its statement would no longer be Oil's with a different schema
	// literal.
	sets := [][]Company{Companies()}
	for _, c := range Companies() {
		sets = append(sets, []Company{c})
	}

	for _, cs := range sets {
		// Both combo-group outcomes: RESOLVED (the normal path, an IN list of item
		// group codes) and UNRESOLVED (the group was renamed in SAP, so the column
		// is CAST(NULL AS DOUBLE)). They are different statement text, so both must
		// clear the guard or the proof covers only the happy path.
		resolved := map[string][]int64{}
		for _, c := range cs {
			resolved[c.Schema] = []int64{109}
		}
		comboVariants := []map[string][]int64{resolved, {}}

		for _, withType := range []bool{false, true} {
			for _, netCN := range []bool{false, true} {
				for _, variety := range []string{"", "OLIVE"} {
					for _, combo := range comboVariants {
						stmt, _ := buildSales(cs, Window{fromBind: "2026-06-01", toBind: "2026-07-01"},
							variety, withType, netCN, combo)
						out = append(out, stmt)
					}
				}
			}
		}
		stmt, _ := buildTurnover(cs, Window{fromBind: "2026-07-01", toBind: "2026-07-29"})
		out = append(out, stmt)
		for _, d := range []Direction{Outgoing, Incoming} {
			stmt, _ := buildPayments(cs, d, Window{fromBind: "2026-07-01", toBind: "2026-08-01"})
			out = append(out, stmt)
		}
		out = append(out, buildVarietyCatalog(cs))
		out = append(out, buildComboGroupCatalog(cs))
	}
	return out
}

// sortedKeys is a small helper used by the error paths that list valid values.
func sortedKeys(m map[string]bool) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
