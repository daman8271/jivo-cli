package domain

import (
	"context"
	"fmt"
	"strings"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// TurnoverRequest is one hana_turnover call. There are deliberately no options
// beyond the window and the company: the canonical figure has ONE definition,
// and netting off credit notes is part of that definition, not a preference.
type TurnoverRequest struct {
	From, To string
	Company  string
}

func turnoverColumns() []string {
	return []string{
		"COMPANY",
		"EXTERNAL_TURNOVER",
		"INTERNAL_RELATED_PARTY",
		"GROSS_TURNOVER",
		"UNLISTED_JIVO_CARD_NET",
		"INVOICES_NET",
		"CREDIT_NOTES_NET",
		"INVOICE_COUNT",
		"CREDIT_NOTE_COUNT",
	}
}

// buildTurnover assembles the canonical turnover statement.
//
// This is the HEADER-level figure: SUM("DocTotal" − "VatSum") over OINV minus
// the same over ORIN, which is the definition CLAUDE.md and
// queries/turnover-oil-july.sql both state. It can differ from the line-level
// hana_sales_by_variety total; BasisGapNote is the measured reason, and both
// tools carry the same one, because a model that finds two figures and cannot
// explain the gap starts flip-flopping between them — exactly what happened in
// the olive incident.
//
// EVERY SUM IS COALESCED TO 0, and that is not decoration. This block is an
// UNGROUPED aggregate, so an empty window does not return zero rows: it returns
// exactly one row per company with COMPANY set and every SUM NULL. Without the
// COALESCE, EXTERNAL_TURNOVER / GROSS_TURNOVER / INVOICES_NET came back as JSON
// `null` rather than 0 — precisely the "no sales and no answer must not look the
// same" ambiguity the clock join exists to prevent — and it fires in ordinary
// use, on any company=ALL window where Beverages posted nothing.
func buildTurnover(companies []Company, w Window) (string, []any) {
	var blocks []string
	var args []any
	for _, c := range companies {
		var b strings.Builder
		fmt.Fprintf(&b, "SELECT '%s' AS COMPANY,\n", c.Name)
		ext, internal := externalCaseExpr(c.Schema), internalCaseExpr(c.Schema)
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(COALESCE(SUM(CASE WHEN %s THEN t.AMT ELSE 0 END), 0)), 2) AS EXTERNAL_TURNOVER,\n", ext)
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(COALESCE(SUM(CASE WHEN %s THEN t.AMT ELSE 0 END), 0)), 2) AS INTERNAL_RELATED_PARTY,\n", internal)
		b.WriteString("       ROUND(TO_DOUBLE(COALESCE(SUM(t.AMT), 0)), 2) AS GROSS_TURNOVER,\n")
		fmt.Fprintf(&b, "       ROUND(TO_DOUBLE(COALESCE(SUM(CASE WHEN %s THEN t.AMT ELSE 0 END), 0)), 2) AS UNLISTED_JIVO_CARD_NET,\n", UnlistedRelatedPartyExpr(c.Schema, "bp"))
		b.WriteString("       ROUND(TO_DOUBLE(COALESCE(SUM(CASE WHEN t.SRC = 'INV' THEN t.AMT ELSE 0 END), 0)), 2) AS INVOICES_NET,\n")
		b.WriteString("       ROUND(TO_DOUBLE(-COALESCE(SUM(CASE WHEN t.SRC = 'CN' THEN t.AMT ELSE 0 END), 0)), 2) AS CREDIT_NOTES_NET,\n")
		b.WriteString("       COALESCE(SUM(CASE WHEN t.SRC = 'INV' THEN 1 ELSE 0 END), 0) AS INVOICE_COUNT,\n")
		b.WriteString("       COALESCE(SUM(CASE WHEN t.SRC = 'CN' THEN 1 ELSE 0 END), 0) AS CREDIT_NOTE_COUNT\n")
		b.WriteString("FROM (SELECT 'INV' SRC, \"CardCode\" CC, \"DocTotal\" - \"VatSum\" AMT\n")
		fmt.Fprintf(&b, "      FROM \"%s\".\"OINV\"\n", c.Schema)
		b.WriteString("      WHERE \"CANCELED\" = 'N' AND \"DocDate\" >= TO_DATE(?) AND \"DocDate\" < TO_DATE(?)\n")
		b.WriteString("      UNION ALL\n")
		b.WriteString("      SELECT 'CN', \"CardCode\", -(\"DocTotal\" - \"VatSum\")\n")
		fmt.Fprintf(&b, "      FROM \"%s\".\"ORIN\"\n", c.Schema)
		b.WriteString("      WHERE \"CANCELED\" = 'N' AND \"DocDate\" >= TO_DATE(?) AND \"DocDate\" < TO_DATE(?)) t\n")
		fmt.Fprintf(&b, "LEFT OUTER JOIN \"%s\".\"OCRD\" bp ON bp.\"CardCode\" = t.CC", c.Schema)
		args = append(args, w.fromBind, w.toBind, w.fromBind, w.toBind)
		blocks = append(blocks, b.String())
	}
	return clockWrap(unionAll(blocks), turnoverColumns(), "a.COMPANY"), args
}

// Turnover returns THE canonical JIVO turnover figure for a window.
func Turnover(ctx context.Context, r Runner, req TurnoverRequest) (*Response, error) {
	companies, err := ResolveCompanies(req.Company)
	if err != nil {
		return nil, err
	}
	w, err := ParseWindow(req.From, req.To)
	if err != nil {
		return nil, err
	}

	stmt, args := buildTurnover(companies, w)
	res, err := r.QueryReadOnly(ctx, guard.MCPPolicy, hana.Limits{}, stmt, args...)
	if err != nil {
		return nil, err
	}

	// AN EMPTY WINDOW COMES BACK AS NO ROWS, and the note has to say that is a
	// real zero.
	//
	// The aggregate is UNGROUPED, so in standard SQL it returns exactly one
	// all-zero row for an empty window, and an earlier revision of this file said
	// so in the payload ("explicit ZEROS, never a missing block"). MEASURED
	// AGAINST LIVE HANA ON 2026-08-01, THAT IS NOT WHAT HAPPENS. For Oil over
	// 1999-01-01..1999-01-02:
	//
	//	SELECT COUNT(*) FROM AGG                       -> 1
	//	FROM (clock) c LEFT OUTER JOIN AGG a ON 1 = 1  -> one row, a.COMPANY NULL
	//
	// i.e. through the clock join HANA yields the NULL-extended row instead of the
	// aggregate's own row, so shape() sees no company row and the block is empty.
	// The COALESCE-to-0 on every SUM is still right and still needed — it is what
	// makes a PARTIALLY empty answer read as 0 — it simply cannot be what a
	// caller sees here.
	//
	// So the note must call this what it is. The wording it replaces told the
	// operator to "treat this as a fault to investigate, not as a zero", which
	// fires on every genuinely quiet company or period and is exactly backwards:
	// zero rows out of an ungrouped aggregate means the window held no documents.
	// (If the row cap tripped, shape() overrides this with truncatedEmptyNote,
	// because then the emptiness proves nothing.)
	asOf, blocks, truncated := shape(res, companies,
		"no invoices and no credit notes at all in this company for this window — a GENUINE ZERO, not a filter that failed and not a fault: an ungrouped aggregate over an empty window returns no row through the server-clock join (measured on live HANA 2026-08-01). Report it as zero turnover.")
	annotateRelatedParty(blocks, nil)

	note := InternalSplitNote +
		" CREDIT_NOTES_NET is reported POSITIVE and has already been subtracted from every turnover column; INVOICES_NET − CREDIT_NOTES_NET = GROSS_TURNOVER." +
		" A company with no invoices and no credit notes in the window comes back as a block with NO rows and a note saying so — that is a GENUINE ZERO, not a failed query: read the block note before reporting anything for that company." +
		" " + BasisGapNote
	if res.Note != "" {
		note += " " + reframeTruncation(res.Note)
	}

	basis := fmt.Sprintf(`turnover = SUM(OINV."DocTotal" - OINV."VatSum") MINUS SUM(ORIN."DocTotal" - ORIN."VatSum") [HEADER level: the document's own total net of GST, so any header-level charge is in it — on JIVO's books those are immaterial, see the note]; %s; "CANCELED" = 'N'; internal = "CardCode" IN this company's JIVO-group card list, external = every other card (correction C-0002; the per-company list is on each block as internal_cards); every SUM is COALESCEd to 0 so an empty window reads as zero, never null`,
		w.Applied)

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
