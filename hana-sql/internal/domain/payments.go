package domain

import (
	"context"
	"fmt"
	"strings"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// Direction is which way the money moved.
type Direction string

const (
	// Outgoing is money JIVO paid — OVPM.
	Outgoing Direction = "outgoing"
	// Incoming is money JIVO received — ORCT.
	Incoming Direction = "incoming"
)

// ParseDirection validates the direction argument.
func ParseDirection(in string) (Direction, error) {
	switch strings.ToLower(strings.TrimSpace(in)) {
	case string(Outgoing):
		return Outgoing, nil
	case string(Incoming):
		return Incoming, nil
	case "":
		return "", fmt.Errorf("missing required argument: direction (%q = money JIVO paid, OVPM; %q = money JIVO received, ORCT)", Outgoing, Incoming)
	}
	return "", fmt.Errorf("unknown direction %q — valid values are %q (money JIVO paid, OVPM) and %q (money JIVO received, ORCT)", in, Outgoing, Incoming)
}

func (d Direction) table() string {
	if d == Incoming {
		return "ORCT"
	}
	return "OVPM"
}

// AllDocTypes is the label of the row that includes every DocType. It exists so
// a "total payments" answer cannot silently be a subset.
const AllDocTypes = "(ALL)"

// docTypeMeaning is the VERIFIED meaning of OVPM/ORCT."DocType".
//
// Measured live 2026-08-01 against all three companies, both tables. The census
// is the reason this tool exists:
//
//	Oil OVPM, not cancelled: S 8837 docs / Rs 3,612.50 Cr   (0 outside OCRD)
//	                         A 4592 docs / Rs   334.07 Cr   (4592 outside OCRD)
//	                         C   79 docs / Rs     4.32 Cr   (0 outside OCRD)
//	Oil ORCT, not cancelled: C 11232 docs / Rs 847.51 Cr    (0 outside OCRD)
//	                         A  1899 docs / Rs 539.19 Cr    (1899 outside OCRD)
//	                         S   288 docs / Rs   7.23 Cr    (0 outside OCRD)
//
// In all EIGHTEEN company x table x DocType groups the split is exact: every 'A'
// row's "CardCode" is absent from OCRD, and every 'S'/'C' row's is present. The
// code in an 'A' row's "CardCode" is a G/L ACCOUNT code (1104107, 2202201,
// 5610003 …), not a business partner. So 'A' is real cash posted straight to a
// G/L account, and dropping it is dropping money.
//
// TWO CLAIMS THAT ARE NOT THE SAME, and getting them mixed up is how this
// description would go stale:
//   - "CardCode" has no OCRD row — TRUE of every 'A' row in BOTH tables. This is
//     the discriminator the tool reports and the one stated here.
//   - "CardName" is empty — true on OVPM (4590 of Oil's 4592) but FALSE on ORCT,
//     where all 1899 'A' rows DO carry a name. The earlier draft of this file
//     asserted the empty name in both directions; the live census says otherwise.
//
// (The plan for this work predicted 'A' rows would carry a NULL "CardCode".
// They do not: only 2 rows in Oil have an empty "CardCode".)
//
// Measured cost of getting the SCOPE wrong, from the 50-question blind benchmark
// and re-verified live 2026-08-01: Mart's July payouts are 156 documents /
// Rs 21.38 Cr, but the DocType='S' subset is 125 / Rs 20.66 Cr — Rs 72,06,576
// and 31 documents short (q30). h17's Rs 1,74,90,480 of duplicate-payment
// exposure is exactly the gap between the inclusive Rs 8,93,93,097 and the
// DocType='S' reading of Rs 7,19,02,617.
func docTypeMeaning(d Direction, code string) string {
	in := d == Incoming
	switch strings.ToUpper(strings.TrimSpace(code)) {
	case "S":
		if in {
			return "received FROM a supplier business partner (a vendor refund)"
		}
		return "paid TO a supplier / vendor business partner"
	case "C":
		if in {
			return "received FROM a customer business partner"
		}
		return "paid TO a customer business partner (a refund)"
	case "A":
		if in {
			return "received straight INTO a G/L account — \"CardCode\" holds a G/L ACCOUNT code with NO row in OCRD, so there is no business partner behind it (on ORCT \"CardName\" is still filled in, so the name is not the tell); still real cash in"
		}
		return "paid straight OUT OF a G/L account — \"CardCode\" holds a G/L ACCOUNT code with NO row in OCRD, so there is no business partner behind it (and on OVPM \"CardName\" is empty too); still real cash out"
	case AllDocTypes:
		return "EVERY DocType together — this row is what \"total payments\" means"
	}
	return "UNKNOWN DocType: not one of S / C / A, which is not something this database has shown before — investigate before quoting any total that includes it"
}

func paymentColumns() []string {
	return []string{"COMPANY", "DOC_TYPE", "PAYMENTS", "TOTAL", "ROWS_WITH_NO_BUSINESS_PARTNER"}
}

// PaymentsRequest is one hana_payments call.
//
// There is deliberately NO scoping argument. The breakdown and the all-types
// total always come back together, in one payload, so a headline can never
// quietly be the narrow number.
type PaymentsRequest struct {
	Direction Direction
	From, To  string
	Company   string
}

// buildPayments assembles the per-DocType breakdown plus an explicit (ALL) row.
//
// The (ALL) row is its own aggregate block over the same WHERE clause, computed
// SERVER-SIDE. It is not the sum of the rounded per-DocType rows (that drifts by
// paise, which an auditor then has to chase) and it is not GROUPING SETS (whose
// NULL group is indistinguishable from a NULL DocType).
//
// Note the cancel flag: on ORCT/OVPM it is "Canceled" with ONE l, unlike
// OINV/ORIN's "CANCELED".
//
// ROWS_WITH_NO_BUSINESS_PARTNER is the evidence for the (ALL) row, carried in the
// payload rather than asserted in prose: it counts payments whose "CardCode" has
// no OCRD row, which live measurement shows is exactly the 'A' population in both
// tables. It is a LEFT OUTER JOIN on OCRD's primary key, so it can match at most
// one row per payment and cannot inflate COUNT(*) or SUM("DocTotal") — the
// TestLivePaymentsAlwaysCarriesTheWholeTotal reconciliation of (ALL) against the
// per-DocType rows is what keeps that honest.
func buildPayments(companies []Company, d Direction, w Window) (string, []any) {
	tbl := d.table()
	var blocks []string
	var args []any

	// Both SUMs are COALESCEd to 0. The (ALL) block below is an UNGROUPED
	// aggregate, so an empty window returns one row per company with COUNT(*) = 0
	// and every SUM NULL — TOTAL came back as JSON `null` rather than 0, which is
	// the same "no payments and no answer look identical" ambiguity the clock
	// join exists to prevent, and it fires on any company=ALL window where one
	// company paid nothing.
	body := func(c Company) string {
		var b strings.Builder
		b.WriteString("       COUNT(*) AS PAYMENTS,\n")
		b.WriteString("       ROUND(TO_DOUBLE(COALESCE(SUM(p.\"DocTotal\"), 0)), 2) AS TOTAL,\n")
		b.WriteString("       COALESCE(SUM(CASE WHEN bp.\"CardCode\" IS NULL THEN 1 ELSE 0 END), 0) AS ROWS_WITH_NO_BUSINESS_PARTNER\n")
		fmt.Fprintf(&b, "FROM \"%s\".\"%s\" p\n", c.Schema, tbl)
		fmt.Fprintf(&b, "LEFT OUTER JOIN \"%s\".\"OCRD\" bp ON bp.\"CardCode\" = p.\"CardCode\"\n", c.Schema)
		b.WriteString("WHERE p.\"Canceled\" = 'N' AND p.\"DocDate\" >= TO_DATE(?) AND p.\"DocDate\" < TO_DATE(?)")
		return b.String()
	}

	for _, c := range companies {
		var agg strings.Builder
		fmt.Fprintf(&agg, "SELECT '%s' AS COMPANY,\n", c.Name)
		agg.WriteString("       p.\"DocType\" AS DOC_TYPE,\n")
		agg.WriteString(body(c))
		agg.WriteString("\nGROUP BY p.\"DocType\"")
		blocks = append(blocks, agg.String())
		args = append(args, w.fromBind, w.toBind)

		var all strings.Builder
		fmt.Fprintf(&all, "SELECT '%s' AS COMPANY,\n", c.Name)
		fmt.Fprintf(&all, "       '%s' AS DOC_TYPE,\n", AllDocTypes)
		all.WriteString(body(c))
		blocks = append(blocks, all.String())
		args = append(args, w.fromBind, w.toBind)
	}
	return clockWrap(unionAll(blocks), paymentColumns(), "a.COMPANY, a.DOC_TYPE"), args
}

// Payments returns the per-DocType breakdown AND the all-types total.
func Payments(ctx context.Context, r Runner, req PaymentsRequest) (*Response, error) {
	companies, err := ResolveCompanies(req.Company)
	if err != nil {
		return nil, err
	}
	w, err := ParseWindow(req.From, req.To)
	if err != nil {
		return nil, err
	}
	if req.Direction != Outgoing && req.Direction != Incoming {
		return nil, fmt.Errorf("unknown direction %q — valid values are %q and %q", req.Direction, Outgoing, Incoming)
	}

	stmt, args := buildPayments(companies, req.Direction, w)
	res, err := r.QueryReadOnly(ctx, guard.MCPPolicy, hana.Limits{}, stmt, args...)
	if err != nil {
		return nil, err
	}

	// The (ALL) block is ungrouped, so every company gets at least that row —
	// PAYMENTS 0, TOTAL 0 — even for a window it paid nothing in. This note is
	// the fallback for a company that returns no row at all, which should not
	// happen; a genuine zero arrives as an explicit zero row instead.
	asOf, blocks, truncated := shape(res, companies,
		fmt.Sprintf("this company made no %s payments at all in this window — a GENUINE ZERO, not a fault. The (ALL) block is an ungrouped aggregate, and measured on live HANA 2026-08-01 an empty window returns NO row through the server-clock join rather than a row of zeros, so an empty block here is the shape of \"nothing happened\". (If the row cap tripped, the note says so instead, because then the emptiness proves nothing.)", req.Direction))
	// Attach the verified meaning to every row, so the breakdown is readable
	// without a lookup and the (ALL) row says out loud what it is.
	for _, blk := range blocks {
		for _, row := range blk.Rows {
			code, _ := row["DOC_TYPE"].(string)
			row["MEANING"] = docTypeMeaning(req.Direction, code)
		}
	}

	verb := "paid"
	if req.Direction == Incoming {
		verb = "received"
	}
	note := fmt.Sprintf("The %q row is the ANSWER to \"total %s payments\": it includes DocType 'S', 'C' and 'A' together. "+
		"Restricting to 'S' understates the total — measured on JIVO's own books, that habit cost Rs 72.06 lakh and 31 documents on one benchmark question and Rs 1,74,90,480 on another. "+
		"DocType 'A' is money %s straight to a G/L account with no business partner behind it — its \"CardCode\" is an account code with no row in OCRD, which is what ROWS_WITH_NO_BUSINESS_PARTNER counts — and it is real cash that belongs in the total. "+
		"Say which scope you quoted. Cancelled documents are excluded (\"Canceled\" = 'N', spelled with ONE l on these tables). "+
		"A company that paid nothing in the window still gets a %q row reading 0 payments / 0.00 — an explicit zero, never a null and never a missing block.",
		AllDocTypes, req.Direction, verb, AllDocTypes)
	if res.Note != "" {
		note += " " + reframeTruncation(res.Note)
	}

	basis := fmt.Sprintf(`total %s payments = SUM(%s."DocTotal") [%s exists in HANA — never assemble CashSum + TransferSum, that is a Service Layer limitation]; %s; "Canceled" = 'N'; the %q row is every DocType together (S + C + A)`,
		req.Direction, req.Direction.table(), `"DocTotal"`, w.Applied, AllDocTypes)

	return &Response{
		AsOf:       asOf,
		AsOfSource: AsOfSource,
		ElapsedMS:  res.Elapsed.Milliseconds(),
		Window:     w,
		Basis:      basis,
		Note:       note,
		Companies:  blocks,
		Truncated:  truncated,
		SQL:        stmt,
		Params:     args,
	}, nil
}
