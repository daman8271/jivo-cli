# Worked example — HSBC 166-79XXXX-001, 31-Aug-2026

The statement this skill was built from. Load it when the shape of a real one
would help; the rules themselves are in `SKILL.md`.

Export: `AISTMTPRINT2026-08-31-17.35.56.xlsx`, 7 lines, JIVO WELLNESS PRIVATE LTD
(= Oil), INR.

## The statement

Opening (brought forward 30-Aug) ₹12,07,85,948.76 → closing ₹10,49,22,908.76.
Newest first, as bank exports usually are.

| Time | Narrative | TRN | In | Out |
|---|---|---|---|---|
| 16:57 | JIVO WELLNESS PVT LTD 83457J300TFC **/70072XXX27** | TFR- | | 1,70,00,000 |
| 16:57 | JIVO WELLNESS PVT LTD 40407J300SFP **/70072XXX27** | TFR- | | 1,80,00,000 |
| 16:57 | TATA AIG GENERAL INSURANCE CO LTD …/60003XXX46 | TFR- | | 2,10,040 |
| 14:39 | JIVO MART PRIVATE LIMITE TFR+ | TFR+ | 20,00,000 | |
| 13:58 | JIVO MART PRIVATE LIMITE TFR+ | TFR+ | 50,00,000 | |
| 12:05 | JIVO MART PRIVATE LIMITE TFR+ | TFR+ | 61,73,000 | |
| 12:04 | JIVO MART PRIVATE LIMITE TFR+ | TFR+ | 61,74,000 | |

Ties exactly: 12,07,85,948.76 + 1,93,47,000 − 3,52,10,040 = 10,49,22,908.76.

## What each line actually was

- **The four TFR+** — intercompany receipts from Mart. `CUSTA000606 JIVO MART PVT
  LTD` in Oil's book, `rCustomer`, series 2564, BPLID 2 FACTORY, GSTIN
  06AACCJ4223F1Z0 (Haryana). On-account: no `RCT2`, no `RCT4`.
- **The two /70072XXX27** — **not** payments to a party called Jivo Wellness.
  JIVO moving ₹3.5 Cr from its own HSBC to its own Indian Bank CC account.
  `rAccount`, series 2600, BPLID 1 DELHI, GSTIN 07AACCJ4223F1ZY (Delhi), with a
  `PaymentAccounts` row: `2201101`, `ProfitCenter: CANOLA`,
  `ProfitCenter2: 08-2026`.
- **Tata AIG** — a real vendor payment, `VENDA000462`, `rSupplier`,
  `ControlAccount 2110004`. On-account (an advance): their ledger sits at
  **+₹2,29,933**, i.e. JIVO is ahead, so nothing was applied.

## The finding

**All 7 were already posted** — receipts 22161/22162/22166/22167 by USER11
(Preshit), payments 27993/27994/27996 by USER05 (Taran), the same morning. One
posted receipt even carries the statement's own narrative verbatim as its
`Remarks`: `JIVO MART PRIVATE LIMITE TFR+`.

The reconciliation is where the value was:

```
SAP ledger 2201105 at 31-Aug            8,57,64,570.39
add back: in SAP, not yet at the bank  +1,90,15,748.00   3 ARORA AGRI payments
                                                          (28001/28002/28003)
                                       ───────────────
                                       10,47,80,318.39
statement closing                      10,49,22,908.76
still unexplained                          1,42,590.37
```

The ₹1,42,590.37 was proved to predate the statement: SAP's balance at 30-Aug
(₹12,06,43,358.39) vs the statement's opening (₹12,07,85,948.76) differs by the
same figure. So it is old, and not this statement's problem.

## What SAP refused, and why

Four receipt drafts were rejected outright:

```
Error: [SAP -1116] (46000071) Please select Payment Mode
```

A JIVO `SBO_SP_TransactionNotification` validation on `U_Pymnt_Mode` — while
**14,195 posted `ORCT` rows have it NULL**, including the four Preshit keyed in
the client hours earlier. The client path does not enforce it; the Service Layer
path does. Setting `U_Pymnt_Mode: "RTGS"` fixed all four.

## The false leads on "the draft opens blank"

Draft 2183 (Tata AIG) opened with an empty Contents grid. Ruled out in order:

| Suspected | Verdict |
|---|---|
| `OpenBal` 0 vs 210040 on the posted doc | **not it** — `OpenBal` is 0 on *every* draft, including human-made 2178–2181. SAP computes it at Add. |
| `DataSource` `S` vs `I` | **not it** — just Service Layer vs client provenance. |
| Missing `AttachmentEntry` | **not it** — deliberately not cloned; two documents must never share one `Attachments2` row. |
| **No Contents rows** | **this was it.** Posted 27993 has no `VPM2`/`VPM4` either — an on-account payment legitimately has an empty grid, and the money shows in Payment Means. The human-made drafts 2178–2181 all *do* carry `PDF4` rows (GL 5610003 BANK CHARGES), which is why they look normal. |

## The 7 demonstration drafts

Created then deleted. Note the DocNum collision:

| DocEntry | DocNum | Type | Amount |
|---|---|---|---|
| 2183 | 826467038 | `S` Tata AIG | 2,10,040 |
| 2185 | 826467038 | `A` → 2201101 | 1,70,00,000 |
| 2186 | 826467038 | `A` → 2201101 | 1,80,00,000 |
| 2191 | 826246813 | `C` Mart | 61,74,000 |
| 2192 | 826246813 | `C` Mart | 61,73,000 |
| 2193 | 826246813 | `C` Mart | 50,00,000 |
| 2194 | 826246813 | `C` Mart | 20,00,000 |

Three outgoing drafts share one DocNum, four incoming share another — the series'
next number, reserved but not consumed until Add.
