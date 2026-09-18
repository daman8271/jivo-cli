# Five worked payloads — 2026-08-25 / 08-31 (three Oil, two Beverages)

Copy the shape, never the values. Every per-vendor field below came from that
vendor's own most recent posted payment.

---

## 1. ADVANCE against a contract — AWL AGRI BUSINESS

Mail: Import raised, Ziyaul approved 12:39. 80 MT soyabean @ ₹1,49,000 →
₹1,19,20,000 + 5% GST ₹5,96,000 = ₹1,25,16,000 − TDS 0.1% ₹11,920 = **₹1,25,04,080**.

```json
{
  "DocType": "rSupplier",
  "CardCode": "VENDA000224",
  "CardName": "AWL AGRI BUSINESS LIMITED",
  "DocDate": "2026-08-25", "DueDate": "2026-08-25",
  "TaxDate": "2026-08-25", "VatDate": "2026-08-25",
  "Series": 2600, "BPLID": 2, "DocCurrency": "INR",
  "ControlAccount": "2110001",
  "PayToCode": "AHMEDABAD",
  "ContactPersonCode": 2067,
  "PaymentPriority": "bopp_Priority_6",
  "VATRegNum": "06AACCJ4223F1Z0",
  "TransferAccount": "2201101",
  "TransferDate": "2026-08-25",
  "TransferSum": 12504080,
  "Remarks": "BEING PAYMENT PAID TO AWL AGRI BUSINESS LIMITED",
  "U_Pymnt_Mode": "RTGS",
  "U_Type_of_Advance": "One Time Settlement",
  "U_Adv_Settl_Dt": "2026-08-31"
}
```

No `PaymentInvoices` — verified correct: **all 24 AWL payments in August have
zero `VPM2` rows.** The advance sits against ₹12.65 Cr of undelivered POs.

**TDS:** `OVPM` has no `WTSum` column. The 0.1% (194Q) is handled by paying the
**net** — every precedent does this. The withholding is not booked by the payment.

---

## 2. ADVANCE, second vendor — DHANLAXMI EDIBLES

Same shape, different per-vendor values. Proves the fields are per-vendor:

```
ControlAccount    2110001        (same)
PayToCode         GONDAL         ← differs
ContactPersonCode 2456           ← differs
TransferAccount   2201101
TransferSum       7445802
U_Pymnt_Mode      RTGS
```

42 MT peanut oil @ ₹1,69,000 = ₹70,98,000 + GST ₹3,54,900 − TDS ₹7,098 =
**₹74,45,802**. Always recompute the mail's arithmetic before sending:

```python
base = qty*rate; gst = round(base*0.05); tds = round(base*0.001)
assert base + gst - tds == quoted_net
```

---

## 3. SETTLEMENT of an open bill — ASHOK KITAB GHAR

A stationery supplier. Note how *much* differs from the oil vendors:

```json
{
  "DocType": "rSupplier",
  "CardCode": "VENDA001090",
  "CardName": "ASHOK KITAB GHAR (BFYPK7430L)",
  "DocDate": "2026-08-25", "DueDate": "2026-08-25",
  "TaxDate": "2026-08-25", "VatDate": "2026-08-25",
  "Series": 2600, "BPLID": 2, "DocCurrency": "INR",
  "ControlAccount": "2110005",
  "PayToCode": "ASHOK KITAB GHAR SONIPAT",
  "ContactPersonCode": 4966,
  "PaymentPriority": "bopp_Priority_6",
  "VATRegNum": "06AACCJ4223F1Z0",
  "TransferAccount": "1104107",
  "TransferDate": "2026-08-25",
  "TransferSum": 6868,
  "Remarks": "BEING PAYMENT PAID TO ASHOK KITAB GHAR (BFYPK7430L)",
  "U_Pymnt_Mode": "NEFT",
  "U_Type_of_Advance": "One Time Settlement",
  "PaymentInvoices": [
    { "DocEntry": 49114, "InvoiceType": "it_PurchaseInvoice",
      "InstallmentId": 1, "SumApplied": 6868 }
  ]
}
```

| | oil vendors | this one |
|---|---|---|
| `ControlAccount` | 2110001 | **2110005** |
| `TransferAccount` | 2201101 / 2201106 | **1104107** |
| `U_Pymnt_Mode` | RTGS | **NEFT** |
| `U_Adv_Settl_Dt` | set | **absent** |
| `PaymentInvoices` | absent | **present** |

`PaymentInvoices[].DocEntry` is the **invoice's** DocEntry (49114), not its
DocNum (626074358). Verify after write in `PDF2`.

---

## The ₹6,868 catch — worth reading twice

The request arrived as an 825×22 px screenshot of one ledger row. It read
`-6,868,000`. Upscaled to 4000 px it reads **`−6,868.0000`** — a decimal point and
SAP's four decimal places.

Three independent checks agreed on ₹6,868:

1. `OCRD."Balance"` = −6868.00
2. The paper bill's words: *"Six Thousand Eight Hundred Sixty Eight"*
3. 15 payments to this vendor since Mar-2025, range ₹4,910 – ₹27,470

**One low-resolution glyph was the difference between ₹6,868 and ₹68.68 lakh.**
Never let a screenshot be the sole source of a figure.


---

## 4. ADVANCE in BEVERAGES — CHANCHAL CHEMICALS TRADING

**The first payment this CLI ever made outside Oil.** Draft `PaymentDrafts(296)`,
DocNum 826468050, JIVO_BEVERAGES_HANADB, created as USER05.

Papers: PO 826228022 (20-Aug, header `ONLY FOR BEVERAGES`, ₹24,780) and the
approval mail thread (request 22-Aug, Arvinder Singh approved 22-Aug 13:49,
Bhupinder Singh 25-Aug 12:24). Ethanol 500 ml × 100 @ ₹210 + IGST 18%.

```json
{
  "DocType": "rSupplier",
  "CardCode": "VENDA001062",
  "CardName": "CHANCHAL CHEMICALS TRADING",
  "Address": "PRATAP NAGAR ANDHA MUGHAL  3RD FLOOR HOUSE NO-G-34\rDELHI-110007\rIN",
  "DocDate": "2026-08-25", "DueDate": "2026-08-25",
  "TaxDate": "2026-08-25", "TransferDate": "2026-08-25",
  "DocCurrency": "INR",
  "Series": 2527, "BPLID": 2,
  "ControlAccount": "2110005",
  "PayToCode": "CHANCHAL CHEMICALS TRADING DELHI",
  "ContactPersonCode": 4819,
  "PaymentPriority": "bopp_Priority_6",
  "VATRegNum": "06AACCJ4223F1Z0",
  "TransferAccount": "1104107",
  "TransferSum": 24780,
  "Remarks": "BEING PAYMENT PAID TO CHANCHAL CHEMICALS TRADING",
  "JournalRemarks": "Outgoing Payments - VENDA001062",
  "U_Pymnt_Mode": "NEFT",
  "U_Type_of_Advance": "One Time Settlement",
  "U_Adv_Settl_Dt": "2026-08-31"
}
```

### What Beverages does differently

| | Oil | **Beverages** |
|---|---|---|
| `--company` | default | **`JIVO_BEVERAGES_HANADB`, on every command** |
| Aug-2026 payment series | 2600 | **2527** |
| this vendor's CardCode | VENDA001306 | **VENDA001062** |
| attachment share | `Attachments_Oil\JIVO_OIL` | **`Attachments_Bev\JIVO_BEVERAGES`** |
| password for USER05 | Oil's | **its own** — see C-0031 |

`Series` was **not** guessed from the vendor's own precedent — that payment was
January (series 1439). The live August series was read off other vendors' August
payments in the same company:

```bash
./sapb1 query VendorPayments --company JIVO_BEVERAGES_HANADB \
  --filter "DocDate ge '2026-08-01' and Cancelled eq 'tNO'" \
  --select "DocNum,DocDate,Series,BPLID,TransferAccount" --orderby "DocDate desc" --top 8 --json
# → every August row: Series 2527
```

**When the vendor's own precedent is months old, clone its per-vendor fields but
take `Series` from the current month's traffic in that company.**

### Corroboration — three sources, independently

| | PO | mail | SAP |
|---|---|---|---|
| ₹24,780 | Invoice Total | "Please pay advance Rs.24780/-" | PO DocEntry 4075 DocTotal |
| Beverages | `ONLY FOR BEVERAGES` | "for beverage plant use" | CardCode exists only in Bev |
| advance | goods not received | the word "advance" | no GRPO, PO still `bost_Open` |

### Attachment — proven end to end

`Attachments2` row **41046**, two lines, both stamped:

```
line 1  CHANCHAL-ADV-24780-MAIL-25.08.2026.pdf   191 KB  U_CHK 191  U_CHK2 OK
line 2  CHANCHAL-PO-826228022-20.08.2026.pdf     103 KB  U_CHK 103  U_CHK2 OK
        \\10.10.101.52\Attachments_Bev\JIVO_BEVERAGES\Attachments
$value read-back: HTTP 200, byte-identical to the source PDF
```

POST the mail (201, creates the row), PATCH the PO onto it (204, LineNum 2),
stamp both lines, then PATCH `PaymentDrafts(296).AttachmentEntry`. See
`approval-mail.md` and `ap-rm-pm/reference/attachments-upload.md`.

### The one that got redone

Draft **292** was created first, as `manager` — the only login then believed to
reach Beverages. When USER05's Beverages password turned up, 292 was deleted
(as `manager`, needing no override) and re-cut as 296. Nothing was ever left in a
state where two drafts for one PO could both be Added.

---

## 5. SETTLEMENT that NETS ADVANCES — PYRUM ENGINEERS (Beverages, 2026-08-31)

**The most instructive entry in this file. It broke three rules of this skill and
rewrote them.** Reference = the real posted payment `VendorPayments(5872)`,
`JIVO_BEVERAGES_HANADB`, ₹3,00,000. My own attempt got the company, the amount and
the shape all wrong before reading it.

### What the thread said (`accounts007@jivo.in`, uid 70974)

| When | Who | What |
|---|---|---|
| 22-Aug 11:20 | Vishal Tyagi (Bakharpur) | *"As per sap ledger please pay Rs.250000/- to PYRUM ENGINEERS"* + ledger screenshot |
| 22-Aug 14:07 | **Arvinder Singh** | *"Ok, approved.3lac"* |
| 25-Aug 14:15 | Atul Sharma | *"work completion on **beverage line** for which this payment will be released"* |
| 26-Aug 20:31 | **Bhupinder Singh** | *"Ok"* |
| 31-Aug 12:26 | **GS Approvals** | *"Ok"* |

### The three traps, in the order they fire

**1. The screenshot pointed at the wrong company.** It showed `VENDA001678 …
−250,000.0000`. That is **Oil's** PYRUM, and Oil's balance genuinely is −2,50,000
(invoice 47271 ₹10,39,077 less June advances 3,52,229 + 4,36,848). Every number
corroborated — and it was still the wrong book. The company was named only in
Atul's sentence: **beverage line**. Beverages PYRUM is `VENDA001364`.

**2. The approved figure was not the requested figure.** Request ₹2,50,000,
approval *"3lac"*, entry **₹3,00,000**.

**3. The shape was a settlement that ate two advances**, not an on-account advance
— even though both of this vendor's visible Oil precedents read `PaymentInvoices: []`.

### The real `PaymentInvoices` — copy this shape

```json
"PaymentInvoices": [
  {"LineNum":0,"DocEntry":12545,"DocLine":0,"InvoiceType":"it_PurchaseInvoice","InstallmentId":1,"SumApplied": 746055},
  {"LineNum":1,"DocEntry":12972,"DocLine":0,"InvoiceType":"it_PurchaseInvoice","InstallmentId":1,"SumApplied": 203945},
  {"LineNum":2,"DocEntry":35326,"DocLine":1,"InvoiceType":"it_PaymentAdvice",  "InstallmentId":1,"SumApplied":-300000},
  {"LineNum":3,"DocEntry":35976,"DocLine":1,"InvoiceType":"it_PaymentAdvice",  "InstallmentId":1,"SumApplied":-350000}
]
```
`746055 + 203945 − 300000 − 350000 = 300000 = TransferSum`. The two negatives are
this vendor's own May payments (5119 ₹3,00,000 · 5210 ₹3,50,000) being consumed.

### Header — Beverages, cloned from 5872

```
CardCode VENDA001364 · ContactPersonCode 5487  ← Bev-specific (Oil's PYRUM is 6206)
ControlAccount 2110005 · PayToCode "PYRUM ENGINEERS-HR" · bopp_Priority_6
VATRegNum 06AACCJ4223F1Z0 · BPLID 2 FACTORY · Series 2527 (Aug Bev; Oil's is 2600)
TransferAccount 1104107 · U_Pymnt_Mode RTGS · U_Type_of_Advance "One Time Settlement"
U_Adv_Settl_Dt  ABSENT — it is a settlement, not an advance
```

### What SAP said when the bills were already settled

```
Error: [SAP -10] Invoice is already closed or blocked   [Message 3524-20]
```
Payment 5872 had closed 12545 and 12972 hours earlier. **That error is SAP stopping
a double payment** — treat it as a finding, not an obstacle, and go locate the
payment that already exists.

### Attachment

One line, exactly as on 5872: the full approval thread printed to PDF.
`jmail-acc7 print 70974` → 5 pages / 253 KB → `POST /Attachments2` → `AbsoluteEntry
41268` → `PATCH PaymentDrafts(298) {"AttachmentEntry":41268}` → `$value` read back
byte-identical. SAP auto-renamed on collision
(`Re_ Payment to PYRUM ENGINEERS31082026175752183511.pdf`) — normal, original untouched.
**Beverages `Attachments2` lines carry `U_CHK`/`U_CHK2` = null on the real posted
payment — do not stamp them there.**

### Left open

Oil still owes PYRUM **₹2,50,000** on invoice 47271. Real, unpaid, and unrelated to
this mail. Flag exposures like this rather than folding them into the entry.
