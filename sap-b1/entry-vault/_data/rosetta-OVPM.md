# Rosetta — `VendorPayments` (API) ↔ `OVPM` (HANA) · OIL

Derived by value-matching 8 real document(s) (`DocEntry` 27731, 27728, 27727, 27725, 27723, 27722, 27721, 27716) read through both doors. A pair had to agree on **every** document to be reported.

- **19** properties mapped to exactly one column
- **8** of those have a **different name** on the two sides ← the dangerous ones
- 9 ambiguous (several columns held the same value)
- 20 with no column (computed, or on a child table)

## The names that differ — memorise these or look them up

| API property (what you send) | HANA column (what you query) |
|---|---|
| `AttachmentEntry` | **`AtcEntry`** |
| `BPLID` | **`BPLId`** |
| `ContactPersonCode` | **`CntctCode`** |
| `ControlAccount` | **`BpAct`** |
| `DocCurrency` | **`DocCurr`** |
| `JournalRemarks` | **`JrnlMemo`** |
| `Remarks` | **`Comments`** |
| `TransferAccount` | **`TrsfrAcct`** |

## Same name on both sides (11)

`BPLName`, `CardCode`, `CardName`, `DocEntry`, `PayToCode`, `Series`, `U_Adv_Settl_Dt`, `U_Pymnt_Mode`, `U_Type_of_Advance`, `U_URGENCY`, `VATRegNum`

## Ambiguous — value matched more than one column

Usually a field SAP stores twice (document currency and system currency), or two flags that happen to agree. Add `--n` to break the tie.

| API property | Candidate columns |
|---|---|
| `DocDate` | `DocDate`, `DocDueDate`, `TaxDate`, `TrsfrDate` |
| `DocNum` | `BoeNum`, `DocNum`, `Ref1` |
| `DueDate` | `DocDate`, `DocDueDate`, `TaxDate`, `TrsfrDate` |
| `Reference1` | `BoeNum`, `DocNum`, `Ref1` |
| `TaxDate` | `DocDate`, `DocDueDate`, `TaxDate`, `TrsfrDate` |
| `TransferDate` | `DocDate`, `DocDueDate`, `TaxDate`, `TrsfrDate` |
| `TransferSum` | `DocTotal`, `DocTotalSy`, `NoDocSum`, `NoDocSumSy`, `TrsfrSum`, `TrsfrSumSy` |
| `U_Pay_Report_Gen` | `ApplyVAT`, `Canceled`, `DPPStatus`, `DiffCurr`, `DigPayment`, `EnblDpmTax`, `Handwrtten`, `IsPaytoBnk`, `PaymType`, `PmntWTCert`, `Printed`, `Proforma`, `SpiltTrans`, `SpltCredLn`, `Status`, `Submitted`, `U_Pay_Report_Gen`, `WizDunBlck`, `confirmed` |
| `VatDate` | `CreateDate`, `UpdateDate`, `VatDate` |

## No column found (20)

Computed by the Service Layer, held on a child table, or genuinely absent from the header. Not a bug — just not queryable from this table.

`Address`, `ApplyVAT`, `AuthorizationStatus`, `CancelStatus`, `Cancelled`, `CurrencyIsLocal`, `DigitalPayments`, `DocObjectCode`, `DocType`, `DocTypte`, `HandWritten`, `IsPayToBank`, `LocalCurrency`, `PaymentByWTCertif`, `PaymentPriority`, `PaymentType`, `Printed`, `Proforma`, `SplitTransaction`, `SplitVendorCreditRow`
