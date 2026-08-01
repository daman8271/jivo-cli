package mcpsrv

import (
	"fmt"
	"strings"
	"time"
)

// This file is the single source of truth for the domain knowledge the tool
// descriptions carry. It exists so the crib sheet cannot drift between tools or
// rot silently: TestDescriptionsCarryFacts asserts the load-bearing sentences
// are actually present in what tools/list advertises.
//
// Everything here is verified against the live database (see
// mcp-benchmark/truth-key.json and hana-sql/queries/turnover-oil-july.sql), not
// recalled from the Service Layer's different field names.

// ReadOnlyLine is repeated in every tool description.
const ReadOnlyLine = "READ-ONLY: this server can only read. Writes are refused before the statement is sent, and every query runs inside a HANA READ ONLY transaction that is always rolled back."

// SchemaLines names the three companies.
const SchemaLines = `  "JIVO_OIL_HANADB"        Oil
  "JIVO_MART_HANADB"       Mart
  "JIVO_BEVERAGES_HANADB"  Beverages`

// TurnoverRecipe is the exact rounding recipe for money answers.
const TurnoverRecipe = `ROUND(TO_DOUBLE(SUM("DocTotal" - "VatSum")), 2)`

// CancelFlag is the mixed-case trap, spelled out.
const CancelFlag = `"CANCELED" = 'N'`

// CancelFlagPayments is the SAME flag under a DIFFERENT spelling on the payment
// tables. Verified live 2026-07-30 against SYS.TABLE_COLUMNS: OINV/ORIN/ORDR
// spell it CANCELED (all caps), while ORCT and OVPM spell it Canceled (mixed
// case). Getting this wrong is an "invalid column name" error, not a wrong
// number, but it costs the model a round trip every time.
const CancelFlagPayments = `"Canceled" = 'N'`

// The three sentences below are JIVO's settled corrections, recorded by
// operators against live data (harness/corrections/). They are repeated in the
// domain tool descriptions because a correction that only exists in a local CLI
// session reaches nobody asking from a phone — which is exactly how the olive
// incident happened.
const (
	// IntercompanyFact is correction C-0002 — ALL of it.
	//
	// It used to name 'CUSTA000606' and stop there, which is the rule line of
	// C-0002 without its evidence. The record also says Mart's books "carry JIVO
	// MART branch cards (DL/PB/HR/KT/KR/RJ/UP) and a JIVO WELLNESS PVT LTD card
	// needing the same treatment", and this description is what a model reads when
	// it decides which tool to call and how to read the answer — so leaving the
	// branch cards out of it left the model believing EXTERNAL meant outside sales
	// when for Mart it did not. Measured live 2026-08-01: Rs 9.58 Cr to
	// CUSTA000874 alone in April–July.
	IntercompanyFact = "JIVO bills its OWN companies and branches through ordinary customer cards — INTERCOMPANY / branch transfers, not outside sales, and NOT one card code: 'CUSTA000606' is Mart buying from Oil; Mart's own books carry JIVO MART branch cards (CUSTA000874 DL took Rs 9.58 Cr of Mart's 'external' Apr–Jul 2026 sales, CUSTA000827 HR, plus PB/KR/RJ/UP) and a JIVO WELLNESS card. INTERNAL_RELATED_PARTY holds all of them; every company block lists its own cards"
	// SegmentationFact is correction C-0003.
	//
	// The direction matters and is stated on purpose. Measured live 2026-08-01 on
	// June-2026 olive: name matching MISSED Rs 1.62 Cr of Mart's tagged sales but
	// OVER-counted Oil's by Rs 1.54 Cr. Saying only that it under-reports invites
	// a model to treat it as a safe lower bound, which it is not.
	SegmentationFact = "NEVER classify products by matching item names: SAP tags every item, and name matching is measurably wrong in BOTH directions (one month's olive: missed Rs 1.62 Cr of one company's tagged sales, over-counted another's by Rs 1.54 Cr), so it is not even a safe lower bound — COLD PRESS 1 LTR is SAP-tagged CANOLA with no 'canola' in its name"
	// BottlesFact is correction C-0001.
	//
	// It used to say "quantities are single BOTTLES (InvntryUom=PCS)". The
	// carton half is verified and is what the correction is actually about —
	// "NumInSale" is 1 on every item, so INV1."Quantity" is saleable units and
	// the x20 carton error cannot happen. The bottle half is not: of 185 Oil
	// olive-tagged items, 111 are PCS, 62 carry no UoM, 10 are LTR, 1 DRM and 1
	// SET, and one month's answer counted 1,640 Mart 'SET' units and 5 Oil 'DRM'
	// drums as bottles. Units, not bottles.
	BottlesFact = "INV1.\"Quantity\" is saleable UNITS, never cartons (\"NumInSale\" = 1 on every item) — the '20 PCS' in an item name is carton configuration and multiplying by it inflates volume ~20x. Mostly single bottles (PCS), but some SKUs are LTR/DRM/SET or carry no UoM, so it is units across mixed UoMs: do not call it a bottle count"

	// BasisGapFact is why hana_turnover and hana_sales_by_variety disagree.
	//
	// It used to be one line saying "header freight" and calling the gap slight —
	// both empirically false; see domain.BasisGapNote for the live measurement. A
	// wrong reason costs more than a long one: a model that repeats it hands
	// Accounts a confident explanation they cannot reconcile against anything in
	// SAP. The magnitude belongs here too, because a model told the difference is
	// "slight" will pick whichever figure it saw first and defend it — asked for
	// Mart's June sales it can get Rs 23.18 Cr or Rs 27.97 Cr, 17% apart.
	BasisGapFact = "DIFFERENT BASES, and the gap is MATERIAL, not slight: hana_turnover is HEADER level (\"DocTotal\" - \"VatSum\"), hana_sales_by_variety is LINE level (INV1/RIN1) — Mart Apr–Jul 2026, Rs 76.50 Cr vs Rs 87.72 Cr (12.8%; 17.1% in June). NOT freight (\"TotalExpns\" totals Rs 22,500 all-time on 3 Oil invoices, Rs 0 elsewhere, 2026-08-01): it is BRANCH STOCK-TRANSFER invoices, whose header is GST-only so it nets to ~0 while the lines keep full value, which is why LINE is the HIGHER one. All of it sits on two JIVO MART branch cards, so compare EXTERNAL to EXTERNAL and the two tools agree to the rupee"
	// PaymentScopeFact is the measured payment-scoping defect.
	//
	// The discriminator is OCRD membership, not the name: verified live
	// 2026-08-01 across all 18 company x table x DocType groups, every 'A' row's
	// "CardCode" is absent from OCRD, while "CardName" is empty on OVPM but
	// FILLED IN on ORCT. A model told to look at the name gets the wrong answer
	// in the incoming direction.
	PaymentScopeFact = "OVPM/ORCT \"DocType\": 'S' = supplier business partner, 'C' = customer, 'A' = booked straight to a G/L account (\"CardCode\" is an ACCOUNT code with no row in OCRD — on OVPM \"CardName\" is empty too, but on ORCT it is filled in, so OCRD membership is the tell, not the name) — 'A' is still real cash, so a payments total must include all three"
)

// DomainToolPointer is the sentence on hana_query that sends a model to the
// tools which cannot get these definitions wrong.
const DomainToolPointer = "PREFER THE DOMAIN TOOLS: hana_sales_by_variety (sales by product variety), hana_turnover (the canonical turnover figure) and hana_payments (payment totals) encode JIVO's settled definitions — corrections C-0001..C-0004 and the payment-scoping rule — so they cannot be gotten wrong. Write SQL here only for something they do not cover."

// SalesByVarietyFacts describes hana_sales_by_variety.
func SalesByVarietyFacts() string {
	return `Net sales (INR, net of GST) by VARIETY = OITM."U_Sub_Group" (optionally "U_TYPE": PREMIUM/COMMODITY/OTHERS), per company, for a date range. ` +
		`USE THIS for any "how much olive/canola/mustard did we sell" question — ` + SegmentationFact + `. ` +
		`EXTERNAL_NET vs INTERNAL_RELATED_PARTY: ` + IntercompanyFact + `. Quote EXTERNAL, say so, never add two companies' gross. ` +
		`UNLISTED_JIVO_CARD_NET is a drift alarm, not a figure: non-zero means a JIVO-named card is missing from the split, so EXTERNAL is an UPPER BOUND. ` +
		`QTY_UNITS_*: ` + BottlesFact + `. ` +
		`OF_WHICH_COMBO_PACKS is the 'SALES BOM' share of GROSS — ONE tag on a mixed pack, so subtract it or say it is counted whole; NULL = unresolved, not zero. ` +
		`Excludes cancelled (` + CancelFlag + `); nets off credit notes by default (net_credit_notes:false = before returns). An unknown variety is an ERROR listing the valid tags. ` +
		`If it disagrees with hana_turnover: ` + BasisGapFact + `. ` +
		`Returns the exact SQL and binds, the basis, and as_of from the HANA server clock. ` + ReadOnlyLine
}

// TurnoverFacts describes hana_turnover.
func TurnoverFacts() string {
	return `THE canonical JIVO turnover figure — use this, not hand-written SQL, for turnover, total sales or revenue. ` +
		`Fixed definition: A/R invoices (OINV) net of GST ("DocTotal" - "VatSum") MINUS credit notes (ORIN), by "DocDate", cancelled excluded (` + CancelFlag + `). ` +
		`Per company: EXTERNAL_TURNOVER, INTERNAL_RELATED_PARTY (` + IntercompanyFact + `), GROSS_TURNOVER, UNLISTED_JIVO_CARD_NET (a drift alarm, not a figure), ` +
		`plus INVOICES_NET / CREDIT_NOTES_NET and counts for audit. Quote EXTERNAL alongside GROSS and say which; never sum two companies' gross. ` +
		`A company with no invoices returns explicit ZEROS, never nulls, never a missing block. ` +
		`If it disagrees with hana_sales_by_variety: ` + BasisGapFact + `. ` +
		`Returns the exact SQL executed, the basis, and as_of from the HANA server clock. ` + ReadOnlyLine
}

// PaymentsFacts describes hana_payments.
func PaymentsFacts() string {
	return `Payment totals for a date range, per company: direction 'outgoing' = money JIVO paid (OVPM), 'incoming' = money JIVO received (ORCT). ` +
		`Always returns the per-"DocType" breakdown AND the '(ALL)' total, because ` + PaymentScopeFact + `. ` +
		`"Total payouts" means the '(ALL)' row; restricting to DocType='S' understates it — measured on these books, Rs 72.06 lakh and 31 documents missed on one question and Rs 1,74,90,480 on another. Say which scope you quoted. ` +
		`There is no scoping argument, so the breakdown cannot be silently narrowed. ` +
		`On these tables the cancel flag is spelled ` + CancelFlagPayments + ` (one L), and "DocTotal" EXISTS in HANA — never assemble CashSum + TransferSum, that is a Service Layer limitation. Cancelled documents are excluded. ` +
		`Returns the exact SQL executed, the basis, and as_of from the HANA server clock. ` + ReadOnlyLine
}

// QueryFacts is the full crib sheet, carried by hana_query's description only.
//
// It used to claim "the other tools stay short so tools/list is cheap behind the
// gateway". That stopped being true when the domain tools arrived: measured by
// TestToolsListPayloadStaysBounded, tools/list is now ~17 KB across seven tools,
// of which hana_query alone is ~5.6 KB. The tools are no longer short, and the
// budgets in TestDescriptionsCarryFacts are what actually keeps the payload
// bounded — so that test asserts the total, rather than this comment asserting a
// property nothing checked.
func QueryFacts(maxRows int, timeout time.Duration) string {
	var b strings.Builder
	fmt.Fprintf(&b, `Run one read-only SQL statement against JIVO's SAP Business One HANA database and get the rows back as JSON. %s

%s

JIVO SAP B1 crib sheet — money is INR; present large figures in crores.

SCHEMAS (one login sees all three companies; you reach a company purely by
qualifying the table name — there is NO company/schema parameter on this tool):
%s

TABLES (header / lines):
  OCRD              business partners (customers + vendors) and ledger balances
  OINV / INV1       A/R invoices (sales)
  ORIN / RIN1       A/R credit notes (sales returns)
  ORDR / RDR1       sales orders
  OPOR / POR1       purchase orders
  OPCH / PCH1       A/P invoices (purchases)
  OITM              item master
  OITW              stock per item per warehouse
  OJDT / JDT1       journal entries
  ORCT              incoming payments
  OVPM              outgoing (vendor) payments

IDENTIFIERS: HANA is case-sensitive and SAP B1 column names are mixed case, so
they MUST be double-quoted: "DocTotal", "VatSum", "DocDate", "CardCode".
The traps, all verified against the live database:
  - on OINV / ORIN / ORDR the cancel flag is UPPER CASE: %s
  - on ORCT / OVPM the same flag is spelled with one L: %s
  - OJDT has no "DocDate" at all; its posting date is "RefDate"
  - ORCT / OVPM DO have "DocTotal" here. If you know the SAP Service Layer, that
    is the opposite of what you learned: the Service Layer's Payments entity has
    no DocTotal and forces you to add CashSum + TransferSum + … . Against HANA,
    use "DocTotal" and do not assemble the parts.
  - every SAP B1 date column is declared TIMESTAMP, not DATE, and carries a zero
    clock; this server returns them as a plain "2026-07-30"

VERIFIED COLUMN FACTS (HANA names, which differ from the Service Layer's):
  OCRD."CardType"   'C' customer, 'S' supplier, 'L' lead
  OCRD."Balance"    ledger balance. POSITIVE = DEBIT (the party owes JIVO),
                    NEGATIVE = CREDIT (JIVO owes them). Sum the debits only for
                    receivables; netting understates what is owed.
  OCRD."CreditLine" credit limit (the Service Layer calls this CreditLimit)
  OINV/ORIN/ORDR    "DocStatus" 'O' open / 'C' closed, "CANCELED" 'N'/'Y',
                    "DocTotal", "VatSum", "PaidToDate", "DocDate", "DocDueDate"
  OJDT."RefDate"    posting date
  OITW."OnHand"     stock on hand per item per warehouse; "MinStock" is the
                    reorder level
  OITM."InvntItem"  'Y' = stock-managed (a different number from "validFor" = 'Y', which is "active")

TURNOVER, net of GST = SUM("DocTotal" - "VatSum") over OINV
  MINUS the same over ORIN, filtered on "DocDate" with %s.
  Use a half-open window so the final day is included:
  "DocDate" >= '2026-04-01' AND "DocDate" < '2026-08-01'.

DECIMALS: DECIMAL columns come back as EXACT decimal strings (e.g.
"1074316124.550000") — never a float, never silently rounded. When you want a
rounded number instead, ask the database for it: %s

JIVO'S SETTLED CORRECTIONS — recorded by operators against live data. They
override any assumption you would otherwise make, and they apply to SQL you
write here just as much as to the domain tools:
  - INTERCOMPANY / BRANCH TRANSFERS: %s. Report external (excluding
    every one of those cards) alongside gross, say which one you quoted, and
    never add Oil + Mart gross. Get the card list from hana_sales_by_variety or
    hana_turnover (each company block carries internal_cards) rather than
    guessing, and NEVER classify a party by matching its name.
  - PRODUCT SEGMENTATION: %s. OITM."U_TYPE"
    (PREMIUM/COMMODITY/OTHERS) and OITM."U_Sub_Group" (variety) are the SAP tags.
  - VOLUME: %s.
  - COMBO PACKS: a 'SALES BOM' item carries ONE "U_Sub_Group" tag for a mixed
    pack, so its whole value lands in that variety; split it out or say so.
  - PAYMENT SCOPE: %s.

AGGREGATE SERVER-SIDE — do not page rows. One SUM / COUNT / GROUP BY answers a
money question in a single call. The row cap is %d rows and the statement
timeout is %s; hitting the cap means the query was shaped wrong, not that you
should page.

Refusals name the layer that refused and why. Only one statement per call.`,
		ReadOnlyLine, DomainToolPointer, SchemaLines, CancelFlag, CancelFlagPayments, CancelFlag, TurnoverRecipe,
		IntercompanyFact, SegmentationFact, BottlesFact, PaymentScopeFact, maxRows, timeout)
	return b.String()
}

// TablesFacts, ColumnsFacts and DoctorFacts are the short descriptions.
//
// TablesFacts used to promise "Omit `schema` to search all three companies at
// once". It could not deliver that: there are 9244 tables (Oil 3111 / Mart 3046
// / Beverages 3087), the listing is ordered by schema, and the row cap is 1000 —
// so an unfiltered call returned 1000 Beverages tables and NOTHING from Oil or
// Mart, while the description said otherwise. The description now states the
// shape of the answer the tool can actually give.
func TablesFacts() string {
	return "List tables/views in JIVO_OIL_HANADB (Oil), JIVO_MART_HANADB (Mart), JIVO_BEVERAGES_HANADB " +
		"(Beverages), with live row counts. ~9,200 tables span the three, so an unfiltered call is ONE PAGE, " +
		"not the catalog: narrow it with `like`, pick one company with `schema`, or page with `offset` (a " +
		"partial page's note names the companies it leaves out). An unknown `schema` is an error, never an " +
		"empty result. " + ReadOnlyLine
}

func ColumnsFacts() string {
	return "Show a table's columns with HANA data type, length, scale, nullability and primary-key flag. " +
		"Use it before writing SQL: SAP B1 column names are mixed case and must be double-quoted, " +
		`and the cancel flag changes spelling by table (OINV ` + CancelFlag +
		`, ORCT/OVPM ` + CancelFlagPayments + `). ` + ReadOnlyLine
}

func DoctorFacts() string {
	return "Check the HANA connection: which env file and host are in use, the login, the HANA version, " +
		"server time and clock skew, which of the three company schemas are readable, and the read-only " +
		"limits in force. Never returns a credential value. " + ReadOnlyLine
}
