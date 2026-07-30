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

// QueryFacts is the full crib sheet, carried by hana_query's description only.
// The other three tools stay short so tools/list is cheap behind the gateway.
func QueryFacts(maxRows int, timeout time.Duration) string {
	var b strings.Builder
	fmt.Fprintf(&b, `Run one read-only SQL statement against JIVO's SAP Business One HANA database and get the rows back as JSON. %s

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

AGGREGATE SERVER-SIDE — do not page rows. One SUM / COUNT / GROUP BY answers a
money question in a single call. The row cap is %d rows and the statement
timeout is %s; hitting the cap means the query was shaped wrong, not that you
should page.

Refusals name the layer that refused and why. Only one statement per call.`,
		ReadOnlyLine, SchemaLines, CancelFlag, CancelFlagPayments, CancelFlag, TurnoverRecipe, maxRows, timeout)
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
