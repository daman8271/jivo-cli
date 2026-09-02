export const meta = {
  name: 'jivo-entry-vault-documents',
  description: 'One deeply-mined vault note per SAP document type JIVO actually makes, each adversarially verified against the live books',
  phases: [
    { title: 'Mine',   detail: 'per document type: field profile, GL fingerprint, flow, real examples -> one note' },
    { title: 'Verify', detail: 'adversarial re-check of every number, then fix the note in place' },
  ],
}

// args: { batch: 'core' | 'tail' }
const BATCH = (args && args.batch) || 'core'

const ROOT = '/Users/damanpreetsingh/jivo-cli'
const VAULT = ROOT + '/sap-b1/entry-vault'

const BRIEF = `
You are a miner for JIVO's SAP entry vault. Work from ${ROOT}.

READ FIRST, in this order:
  1. ${VAULT}/bin/AGENT-BRIEF.md            (tools, rules, house style — all of it)
  2. ${VAULT}/_template/document-note.md    (the skeleton for your note)
  3. ${ROOT}/harness/corrections/INDEX.md   (settled truths that outrank you)
  4. ${VAULT}/00-index/Entry-Types-Census.md (the census — do not re-derive it)
  5. ${ROOT}/acc/INVENTORY.md               (who keys what, mined 2026-08-23)
  6. Any note already in ${VAULT}/01-foundations/ that your document depends on —
     series, branches, GL accounts, tax codes, TDS, dimensions, warehouses, UDFs,
     approvals, periods, statuses, attachments. LINK to them, do not restate them.

TOOLS (read-only, run from ${ROOT}):
  python3 sap-b1/entry-vault/bin/profile.py <TABLE>  [--co OIL,MART,BEV] [--days N] [--vocab-max N]
  python3 sap-b1/entry-vault/bin/gl.py <TransType>   [--co OIL] [--days N] [--memo]
  python3 sap-b1/entry-vault/bin/flow.py <OTABLE>    [--co OIL] [--days N]
  python3 sap-b1/entry-vault/bin/sample.py <OTABLE> --n 3 [--co OIL] [--where '"Col"=1']
  ./hana-sql/hana-sql -env connections/hana-office-bridge.env "SELECT ..."
Schemas: JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB.
Quote every SAP column: "DocDate". One statement per call, SELECT/WITH only.
On connection refused / timeout: run  bash sap-b1/entry-vault/bin/bridge.sh  and retry.
NEVER report "no data" from a connection error.

HARD RULES: never write to SAP (read-only tools only — no sapb1 draft/post/patch/delete,
not even a dry run). Every number in the note comes from a query you ran, and the SQL goes
in the note. Mark measured vs inferred explicitly. The repo is PUBLIC: field names, fill
rates, GL codes and names, series numbers and vendor GROUP names are fine; credentials,
GSTINs, bank account numbers, individual pay figures and bulk customer contact lists are not.
Say "I don't know" in Open questions rather than guessing.

WHAT MAKES THIS NOTE WORTH WRITING: an operator sits down tomorrow with the paper in their
hand and reads only your note. It must tell them every field they have to decide, where each
value comes from, what SAP will fill in by itself, what it will silently leave blank, and how
to tell afterwards that they got it right. Field lists are the easy half; the pre-flight list
and the traps are the half that saves time.
`

const CORE = [
  {
    slug: 'AP-Invoice', tables: 'OPCH / PCH1 / PCH12 / PCH3', objtype: 18,
    mandate: `The single most important note in the vault: 24,368 documents, and the entry Accounts
keys most often after receipts. Run profile.py on OPCH and PCH1 (all three books), gl.py 18 with
--memo, flow.py OPCH in each book, and sample.py on at least four genuinely different ones — a
GRPO-copied item bill, a standalone service bill, a staff imprest reimbursement, and one with TDS.
Corrections that already apply and must be honoured and cross-referenced: C-0017 and C-0022 (DocDate
= posting = gate-in = the GRPO's DocDate as a POSTING RULE, while the books only match on 51% of Oil
pairs), C-0018 (Series + DocumentSubType bod_GSTTaxInvoice, TDS comes out 0), C-0025 (service lines
need LocationCode, U_Recvd_Qty, CostingCode3), C-0026 (attachment flags), C-0027 (handwritten
"Common" means CostingCode3 = FACT_COM). Beyond those: the DocType S-versus-I split and what changes
between them; how the vendor's own invoice number is carried (NumAtCard is NULL on a real Oil
example — find out what is used instead and how duplicates are detected); the freight/expense lines
(PCH3?); rounding; the GRNI account 2140001 and the SHORT AND EXCESS 5680014 account that appears on
1,091 of 2,051 recent journals — explain what causes it. Give the full CLI payload skeleton and the
read-back checklist. This note should be long.`,
  },
  {
    slug: 'GRPO', tables: 'OPDN / PDN1 / PDN12', objtype: 20,
    mandate: `The goods receipt: the document an A/P invoice is usually built on, so its quality
decides the invoice's. 19,697 documents. Who raises it (the factory, not Accounts) and what Accounts
inherits from it: vendor, items, quantity, rate, branch, warehouse, and the scanned bill. Cover the
service-GRPO variant (freight and transporter receipts) and how it differs from an item GRPO — 260
of 90 days' A/P invoices come off one. Measure: how often a GRPO carries an attachment; the tax
codes on its lines versus the tax on the invoice built from it (there is a known finding that a GRPO
recorded at 0% GST silently loses the credit when the bill has GST — quantify how often GRPO and
invoice tax disagree); the gap in days between GRPO date and the invoice date; and how many GRPOs
are still uninvoiced right now (the GRNI balance in document terms). Trap territory: correction
C-0021 on three-valued CANCELED, which materially changes Oil OPDN totals.`,
  },
  {
    slug: 'AP-Credit-Memo', tables: 'ORPC / RPC1 / RPC12', objtype: 19,
    mandate: `The debit note to a vendor — short supply, rate difference, returns. 2,624 documents.
Correction C-0024 is the reason this note matters: OriginalRefNo (the original invoice number exactly
as printed on the credit note) and OriginalRefDate must be set, SAP silently accepts null, and
Accounts/GST require them. Measure how often they are actually filled on posted documents, and
whether the ones that are blank correlate with any operator or period. Cover: whether a credit memo
is copied from the invoice it reverses or keyed standalone (flow.py); how the reversal reaches the
GL (gl.py 19); the GST reversal mechanics; what happens to stock when an item credit memo posts; and
the difference between an A/P credit memo and a goods return (ORPD) — when does each get used, with
counts.`,
  },
  {
    slug: 'Outgoing-Payment', tables: 'OVPM / VPM1 / VPM2 / VPM3 / VPM4', objtype: 46,
    mandate: `Paying a vendor: 19,063 documents, and acc/INVENTORY.md establishes that 59% are
on-account with no invoice linked at payment time, that 99.6% are bank transfer, and that 704 go
straight to a GL account rather than to a business partner. Answer: the four VPM line tables and
which is which (cheque / bank transfer / cash / applied-invoices) — a memory note claims the VPM2
keys are backwards, so TEST that rather than repeating it; how an applied payment records which
invoices it settled; how an on-account payment is later matched (OITR internal reconciliation, 30,084
rows in Oil, no UserSign); the GL fingerprint including TDS-at-payment (a memory note says TDS is
mostly NOT withheld at payment — verify it); the payment-draft path (OPDF) versus posting directly;
and the operator rule for "pay the vendor" versus "settle these bills", which acc/INVENTORY.md says
are two separate keying jobs today. Do not print bank account numbers.`,
  },
  {
    slug: 'Incoming-Payment', tables: 'ORCT / RCT1 / RCT2 / RCT3', objtype: 24,
    mandate: `Customer receipts: 29,706 documents, the single highest-volume thing a person keys at
JIVO (about 47 a working day). Answer: the three line tables and which handles cheque, transfer and
cash; the 657 cash receipts in 90 days and how they differ; receipts posted to a GL account rather
than a customer (500 in 90 days) and what those are; how a receipt gets applied to invoices and how
often it is left on account; bounced/dishonoured cheque handling (acc/INVENTORY.md mentions cheque
dishonour appears in manual journals — find how it is really recorded); the GL fingerprint; and the
per-book differences, since Mart runs nearly as many receipts as Oil on a much smaller ledger.`,
  },
  {
    slug: 'AR-Invoice', tables: 'OINV / INV1 / INV12 / INV3', objtype: 13,
    mandate: `The sales invoice: 62,426 documents, the highest-volume document in the books and the
one whose definition drives every turnover number. Honour and cross-reference corrections C-0001
(quantity is in PIECES, single bottles — the "20 PCS" in item names is carton config only, and
multiplying by it inflates volume ~20x), C-0014 (buyer GSTIN is INV12.BpGSTN at invoice level, not
OCRD.LicTradNum which is empty, nor CRD7.TaxId0 which is a PAN), C-0013 (HSN and SAC are mutually
exclusive), C-0021 (three-valued CANCELED), C-0005 (intercompany is 23 group CardCodes). Also state
the house turnover definition — invoices net of GST (DocTotal minus VatSum) minus credit notes, by
DocDate, excluding cancelled — and show the query. Cover: how an invoice arrives (copied from a
delivery or a sales order, or keyed — flow.py); e-invoicing and IRN (the OMS_IRN_LOG and @UTL_ST_EICO
tables) and the e-way bill; the GL fingerprint; and what a person keying one by hand must decide.`,
  },
  {
    slug: 'AR-Credit-Memo', tables: 'ORIN / RIN1 / RIN12', objtype: 14,
    mandate: `Sales returns and rate differences: 11,417 documents, and the deduction side of the
turnover definition. Answer: the split between genuine goods returns and pure rate/claim adjustments
(measure it — an item line with quantity versus a service line without); e-commerce claims, which
acc/INVENTORY.md flags as a driver; whether it is copied from the invoice or the return document
(flow.py); the stock effect; the GST reversal; the GL fingerprint; and the credit-memo-versus-return
(ORDN) decision with counts. Note the per-book skew: Mart runs 4,545 against Oil's 6,434 on a much
smaller sales base — find out why.`,
  },
  {
    slug: 'Journal-Entry', tables: 'OJDT / JDT1', objtype: 30,
    mandate: `The manual journal entry — the entry with no rules, and therefore the one that needs
the most documentation. 8,090 manual JEs (TransType 30) out of 224,982 journals. acc/INVENTORY.md
lists what they are used for: intercompany "OIL TO BEVERAGE", TDS, provisions and their reversals,
salary, incentives, customer-to-vendor balance transfers, cheque dishonour. Turn that list into a
taxonomy WITH counts by mining JDT1 line memos and account pairs (gl.py 30 --memo is the starting
point, then go deeper — cluster the memos). For each recurring type give the actual account pair and
a real example. Then: correction C-0023 (a party ledger comes from JDT1 with OCRD.CardCode =
JDT1.ShortName, never from document extracts — 7,478 JEs worth Rs 3,043 cr are invisible otherwise);
the future-dated year-end provisions found in the census (manual JEs dated 2026-12-31 — find and
explain them); how a reversal is recorded; which dimensions a manual JE must carry; and the
operator rule for when a manual JE is the right answer versus a document.`,
  },
  {
    slug: 'Journal-Voucher', tables: 'OBTF / BTF1', objtype: -1,
    mandate: `The parked journal — 4,933 rows, 527 in 90 days, same inputs as a manual journal entry
but held for review. Answer: what OBTF actually is (a batch header) and how BTF1 lines relate to it;
who parks them and who posts them; how long they sit (measure); what happens on posting — does the
batch become an OJDT with TransType 30, and can you trace a posted voucher back to its batch; how
many are still unposted right now and how old the oldest is; and the operator rule for parking
versus posting directly. Also: is there any CLI path to a journal voucher at all? Say so plainly
either way.`,
  },
  {
    slug: 'Document-Drafts', tables: 'ODRF / DRF1 / DRF12', objtype: -1,
    mandate: `The meta-note on drafting, because a draft is the unit of work at JIVO: 78,492 of them
across 15 document types, and it is what the CLI creates. Answer: how ODRF stores a draft of any
type (ObjType discriminator, DRF1 lines shared across types, which header fields are draft-specific);
the full status vocabulary and what each value means — in particular the dasCancelled state, since a
memory note dated 2026-08-24 claims 817 of 1,053 open Oil A/P drafts are cancelled rather than
pending, and that must be RE-MEASURED not repeated; how a draft becomes a document and what link
survives (draftKey on the posted document — verify); what happens to a draft that is never posted;
how drafts interact with approval; the numbering behaviour (does a draft consume a series number);
which draft fields SAP recomputes on posting; and the practical question for anyone creating drafts
from the CLI: what will the person who opens Document Drafts see, and what makes a draft unusable.
Also cover sapb1 delete draft, which is the one sanctioned DELETE, and its provenance guards.`,
  },
  {
    slug: 'Payment-Draft', tables: 'OPDF / PDF1 / PDF2 / PDF3 / PDF4 / PDF8', objtype: -1,
    mandate: `The payment draft: 1,788 rows, 172 in 90 days, Avtar and Taran between them. A
separate table from ODRF, which is itself worth explaining. Answer: how OPDF mirrors OVPM and which
of the five PDF line tables carries what; who creates them and what happens next; how long they sit
before posting and how many never post; whether an outgoing payment can be traced back to its draft;
the difference in behaviour between a payment draft and a document draft; and the CLI path — sapb1
draft payment exists, so document what it needs and what SAP fills in. Also note sapb1 delete
payment-draft as the second sanctioned DELETE.`,
  },
  {
    slug: 'Purchase-Order', tables: 'OPOR / POR1 / POR12', objtype: 22,
    mandate: `The purchase order: 7,724 documents, raised before goods arrive, and the thing whose
absence blocked a real A/P entry today (an Indiyum Foods bill could not be keyed because there was
no gate entry and no PO). Answer: who raises POs and for what — measure the split by vendor group and
by item versus service; how a PO becomes a GRPO and then a bill (flow.py, and measure the day gaps);
how many POs are still open and how old; whether a bill can be keyed with no PO at all and how often
that happens; the approval requirement (555 PO approval requests in 90 days per acc/INVENTORY.md);
the GL effect, if any, of a PO on its own; and what an operator holding a bill should check about the
PO before keying anything.`,
  },
]

const TAIL = [
  { slug: 'Delivery', tables: 'ODLN / DLN1', objtype: 15,
    mandate: `9,271 documents and Mart's dominant outbound document (6,126 versus Oil's 2,842 — explain that inversion). Stock effect, the copy-from-sales-order rate, the invoice built on top, e-way bill linkage, and what a person keying one decides.` },
  { slug: 'Sales-Order', tables: 'ORDR / RDR1', objtype: 17,
    mandate: `28,386 documents. Where orders come from (OMS raises them into Oil and Beverages only per correction C-0011, so Mart's 7,675 come from somewhere else — find out); the open-order picture; how much of an order is ever delivered; approval; and the fields a person actually types versus what an integration fills.` },
  { slug: 'Sales-Quotation', tables: 'OQUT / QUT1', objtype: 23,
    mandate: `2,425 documents, none in Mart at all. Who quotes and for what; conversion rate to order (measure via TrgetEntry); why Mart never quotes; and whether this document matters to Accounts at all — say so plainly if it does not.` },
  { slug: 'AR-Return', tables: 'ORDN / RDN1', objtype: 16,
    mandate: `4,065 documents. The goods side of a sales return, versus the money side (A/R credit memo, 11,417). Measure how often a return is followed by a credit memo and how often each stands alone; the stock and GL effects; and the operator decision between them.` },
  { slug: 'Goods-Return', tables: 'ORPD / RPD1', objtype: 21,
    mandate: `Only 209 documents, so also answer WHY it is so rare when A/P credit memos number 2,624. The goods side of a purchase return; how it relates to the credit memo; the GL and stock effects; and when the process actually calls for it.` },
  { slug: 'Stock-Transfer', tables: 'OWTR / WTR1', objtype: 67,
    mandate: `16,132 documents and 15,289 drafts — the third-most-drafted document in the books, and 2,891 approval requests in 90 days. Which warehouses move to which; branch-to-branch versus within-branch; the GST implication of an inter-state stock transfer and the e-way bill; the GL fingerprint (TransType 67); the transfer-request path (OWTQ, 2,503) and how often a transfer has one; and who keys them.` },
  { slug: 'Inventory-Transfer-Request', tables: 'OWTQ / WTQ1', objtype: 1250000001,
    mandate: `2,503 documents, 725 drafted. The request that precedes a stock transfer. Measure the fulfilment rate and the day gap; who raises versus who fulfils; approval; and whether it is required or optional in practice.` },
  { slug: 'Goods-Receipt', tables: 'OIGN / IGN1', objtype: 59,
    mandate: `10,100 documents — stock in with no vendor and no bill (production output, found stock, opening). Nearly absent in Mart (75) — explain. What causes one; the GL fingerprint (TransType 59) and which account absorbs it; the link to production orders; and when Accounts needs to care.` },
  { slug: 'Goods-Issue', tables: 'OIGE / IGE1', objtype: 60,
    mandate: `9,900 documents — stock out with no customer and no invoice (consumption, samples, write-off, production input). The GL fingerprint and which expense accounts absorb it; the samples case, which the JSAP budget register treats as positive ObjType 14 per a memory note; write-offs and who authorises them; and how it pairs with goods receipt for production.` },
  { slug: 'Production-Order', tables: 'OWOR / WOR1', objtype: 202,
    mandate: `9,832 orders and 5,698 journals, essentially Oil only (Mart has 27). How a production order consumes and produces (the goods-issue and goods-receipt pair); the GL fingerprint (TransType 202) and where variance lands; the BOM (product trees) it draws on; the link to the factory app whose GRPO feed a memory note recorded as broken; and what Accounts reads from it at month-end.` },
  { slug: 'Landed-Costs', tables: 'OIPF / IPF1 / IPF2 / IPF3', objtype: 69,
    mandate: `540 documents, Oil-only in practice, 65 of 66 in 90 days keyed by Lovepreet — the import cost entry. Answer: what a landed-cost document does to item cost; which cost buckets exist (the three line tables); the BoE, freight, duty and clearing inputs it needs, and where each comes from; the GL fingerprint (TransType 69); the link to the exim system; and the full pre-flight list for keying one, since one person holds this whole process.` },
  { slug: 'Inventory-Revaluation', tables: 'OMRV / MRV1', objtype: 162,
    mandate: `160 documents, month-end, mostly by manager. What triggers a revaluation; which items and why; the GL fingerprint (TransType 162); how it interacts with the 45 Cr fixed-assets-as-stock finding recorded in memory; and who signs it off.` },
  { slug: 'Bank-Statement', tables: 'OBNK / BNK1', objtype: -1,
    mandate: `259 rows, mostly Oil. Answer whether bank statements are genuinely imported and reconciled or only occasionally used — measure the date coverage and the gaps, and compare against the 6,409 internal reconciliations in 90 days that carry no UserSign. Then say plainly what the real reconciliation process is.` },
  { slug: 'Internal-Reconciliation', tables: 'OITR / ITR1', objtype: -1,
    mandate: `49,840 rows and no UserSign on any of them — the invisible half of Accounts. Answer: what a reconciliation row records; how a payment gets matched to invoices after the fact; whether it is done in the client's reconciliation screen or by an automatic process (the absent UserSign is the clue — chase it); how it interacts with correction C-0019 (DocStatus O is unreliable because documents settled by manual JE or unapplied payment stay open); and how to tell from the data whether a specific bill has actually been settled.` },
  { slug: 'Return-Request', tables: 'ORRR / RRR1', objtype: 1250000025,
    mandate: `Only 33 rows, 32 of them Oil, and worth a short honest note: what it is, who used it, when they stopped, and whether it is dead. A one-page note is the right answer if the data says so — do not inflate it.` },
  { slug: 'Opening-Balance-and-Cutover', tables: 'OJDT (TransType -3) / JDT1', objtype: -3,
    mandate: `952 journals, every one dated 2025-04-01: the SAP go-live cutover, and the reason any history question has a floor. Answer: what was loaded (which accounts, which parties, what totals per book); how opening balances are represented and how to exclude or include them correctly; what "since inception" therefore means in these books; whether any pre-cutover history exists anywhere; and the trap for ageing and party-ledger work — correction C-0023 already notes that document extracts miss pre-cutover postings. Also identify the unidentified posting types from the census: TransType 321 (24 rows in Oil, latest 2026-07-25) and 254000061 / 254000062 (Mart only, 2025) — pull their journals and read what they actually did.` },
]

const TOPICS = BATCH === 'core' ? CORE : TAIL

const NOTE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['slug', 'written', 'key_learnings', 'confidence', 'open_questions'],
  properties: {
    slug: { type: 'string' },
    written: { type: 'boolean' },
    bytes: { type: 'number' },
    key_learnings: { type: 'array', maxItems: 8, items: { type: 'string' },
      description: 'What you learned that is NOT in SAP documentation and NOT already in the corrections' },
    required_fields_count: { type: 'number', description: 'how many fields you concluded a human must decide' },
    contradicts_correction: { type: 'array', items: { type: 'string' } },
    new_correction_candidates: { type: 'array', items: { type: 'string' } },
    cli_writable: { type: 'string', enum: ['draft', 'post-only', 'no-path', 'unknown'],
      description: 'can this document type be created from the sapb1 CLI today?' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['slug', 'checked', 'wrong_claims', 'verdict'],
  properties: {
    slug: { type: 'string' },
    checked: { type: 'number' },
    wrong_claims: { type: 'array', items: { type: 'string' } },
    unsupported_claims: { type: 'array', items: { type: 'string' } },
    missing_material: { type: 'array', items: { type: 'string' },
      description: 'things an operator would need that the note omits' },
    fixed: { type: 'boolean' },
    verdict: { type: 'string', enum: ['SOLID', 'FIXED', 'NEEDS_REWORK'] },
  },
}

phase('Mine')

const results = await pipeline(
  TOPICS,
  (t) => agent(
    `${BRIEF}

YOUR DOCUMENT: **${t.slug}** — SAP tables ${t.tables}${t.objtype > 0 ? `, ObjType/TransType ${t.objtype}` : ''}

${t.mandate}

Write the note to: ${VAULT}/02-documents/${t.slug}.md

Use the document-note template as a floor, not a ceiling — add whatever sections this
document actually needs and drop any that do not apply (say so rather than leaving a stub).
Run the profilers on every relevant table in every book that has rows. Cross-check the three
books against each other; a figure measured in Oil and asserted for Mart is the classic error.
Chase anything surprising instead of rounding it off. You have plenty of time.`,
    { label: `mine:${t.slug}`, phase: 'Mine', effort: 'high', schema: NOTE_SCHEMA },
  ),
  (note, t) => {
    if (!note || !note.written) return { slug: t.slug, note, verdict: null }
    return agent(
      `You are verifying a vault note written by another miner. Be adversarial: assume it is wrong
until the books say otherwise. Work from ${ROOT}.

Read ${VAULT}/bin/AGENT-BRIEF.md for the tools, then read the note:
  ${VAULT}/02-documents/${t.slug}.md

1. Re-run the note's own SQL. Any figure that does not reproduce is a finding.
2. Find claims stated as fact with no query behind them — verify or mark them inferred.
3. Check it against ${ROOT}/harness/corrections/INDEX.md. Contradicting a settled correction
   is a serious finding.
4. Check every cross-book claim specifically. A number measured in one company and asserted
   for another is the most common error in this work.
5. Judge it as an operator would: with the paper in hand, does this note actually let you key
   the entry? List what is materially missing.

Then FIX the note in place — correct the numbers, mark or remove unsupported claims, and add
what is materially missing. Keep the author's structure. Do not pad it. Read-only against SAP.

NEEDS_REWORK only if the note is substantially unsound.`,
      { label: `verify:${t.slug}`, phase: 'Verify', effort: 'high', schema: VERDICT_SCHEMA },
    ).then((v) => ({ slug: t.slug, note, verdict: v }))
  },
)

const ok = results.filter(Boolean)
log(`documents/${BATCH}: ${ok.length}/${TOPICS.length} returned`)

return {
  batch: BATCH,
  notes: ok.map((r) => ({
    slug: r.slug,
    written: r.note?.written,
    bytes: r.note?.bytes,
    confidence: r.note?.confidence,
    cli_writable: r.note?.cli_writable,
    required_fields: r.note?.required_fields_count,
    key_learnings: r.note?.key_learnings || [],
    contradicts: r.note?.contradicts_correction || [],
    correction_candidates: r.note?.new_correction_candidates || [],
    open_questions: r.note?.open_questions || [],
    verdict: r.verdict?.verdict,
    wrong_claims: r.verdict?.wrong_claims || [],
    unsupported: r.verdict?.unsupported_claims || [],
    missing: r.verdict?.missing_material || [],
  })),
}
