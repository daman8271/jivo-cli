# Session log — accounts data entry

Raw capture. Written *while* the work happens, not reconstructed after.
Each document type gets a block. A block is ready to become a skill when the
"unknowns" list is empty and it's been done twice.

Template for each block:

```
## <document type> — <date>

**Operator:** <who> · **Company:** <Oil/Mart/Bev> · **Login:** <USERxx>

### The paper
<what the source document is, every field on it, including handwriting>

### Where each field goes
| On the paper | SAP field | How it's resolved | Trap |

### What SAP needed that wasn't on the paper
<branch, series, GL, item codes, base document — and how we found each>

### Duplicate check
<what we searched to prove it wasn't already keyed>

### The write
<exact command + payload + what SAP returned>

### Read-back diff
<what SAP stored vs the paper — every gap>

### Unknowns still open
<anything we guessed or worked around>
```

---

## Session start — 2026-08-22

- Bridge up (`connections/sap-home-bridge.sh`), SL on `127.0.0.1:15000`.
- `sapb1 doctor` green: `JIVO_OIL_HANADB` as `USER36`.
- Workbench created. Waiting on the operator for the first document type.

---

## A/P invoice from a vendor bill — 2026-08-22

**Operator:** Daman, sitting with Accounts · **Company:** JIVO_OIL_HANADB · **Login:** USER36 (Navdeep)
**Document made:** draft **626084155** (DocEntry 54983) — TPAC Packaging, ₹2,53,110

### The paper
TPAC PACKAGING INDIA PVT LTD - HARIDWAR U2 tax invoice `2606000806` dt 13.08.2026.
GSTIN 05AAGCT4816J1Z8 (Uttarakhand 05) → buyer 06AACCJ4223F1Z0 (Haryana 06) ⇒ **IGST**, interstate.
1 line: `1LT BOT SQ NAT 26G 29/21MM JIVO 78 PB`, HSN 39233090, 550 packs × 78 = 42,900 PC @ ₹5.00
= ₹2,14,500 + IGST 18% ₹38,610 = **₹2,53,110**. PO 220726021. E-way 352312357085. Veh HR67C9554.
Handwriting: JIVO gate stamp **G.No 154, 14/8/26**; TPAC "MATERIAL OUT" entry 1318 dt 13/08/26;
quantity + rate check signed, quality check blank; "Approved by … on mail" in the margin.

### Where each field went
| On the paper | SAP field | How resolved | Trap |
|---|---|---|---|
| invoice no | `NumAtCard` | typed | the GRPO already carried it — a free cross-check |
| invoice date 13.08 | `TaxDate` | typed | **not** DocDate (C-0017) |
| gate stamp 14/8 | `DocDate` | matched the GRPO's DocDate | posting = gate-in, not today, not vendor's |
| vendor | `CardCode` | **read off the GRPO** | name search gave 2 hits (VENDA000937 / 000939) — ambiguous |
| buyer GSTIN | `BPL_IDAssignedToInvoice` | GRPO's branch = 2 FACTORY | that GSTIN sits on 3 branches; only the GRPO disambiguates |
| item | `ItemCode` | GRPO line → PM0000851 | paper name and SAP name share **0%** overlap; qty/rate/value are the proof |
| — | `Series` 3684 + `bod_GSTTaxInvoice` | 40/40 branch-2 GST bills this month | omit either → `-10` / `-4002` |
| — | `WarehouseCode` BH-PM, `CostingCode` MUSTARD | GRPO line | never invent these |

### What decided the document that wasn't on the paper
**TDS.** BP master says `SubjectToWithholdingTax=boYES`, code 1031 (194Q, 0.1%) ⇒ ₹214.
But JIVO's last 3 posted TPAC invoices are all `WTLiable tNO`, TDS 0. **Operator chose: no TDS.**
⇒ New rule: *precedent on the vendor beats the BP master flag; always show the operator both.*
The read-back then flags "TDS is 0 but vendor is TDS-liable" — a false positive once overruled.

### Duplicate check (4 searches, all needed)
1. `PurchaseInvoices` by NumAtCard → none
2. `Drafts` by NumAtCard → 1 hit, but `oPurchaseDeliveryNotes` (a draft **GRPO**), status `bost_Close` = already converted. **Not** a duplicate.
3. `Drafts` where `DocObjectCode eq 'oPurchaseInvoices'` for the vendor → only May-2026, older `HAR2/26-27/…` ref format
4. GRPO still `bost_Open` with all 42,900 unbilled

### The write
`sapb1 draft purchase-invoice --data-file … --yes` → DocEntry 54983, DocNum 626084155.
Read-back reconciled to the rupee. SAP filled DocDueDate 14-09-2026 from the vendor's terms.

### ATTACHMENTS — the day's real finding
The draft came out with `AttachmentEntry: null`. Establishing why took a 21-agent workflow:

- **The Service Layer cannot upload attachments at all on this installation.**
  `GET Attachments2(N)/$value` → 404 *"Fail to get the LINUX mount point for AttachmentsFolderPath"*;
  `POST /Attachments2` → -5002 *"Attachments folder not defined"*. Cause: SL runs on Linux (SLES 15 SP5),
  the attachment folder is a Windows UNC (`\\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments\`).
- **A CIFS mount fixes only the READ half.** Disassembly of `libB1_Engine.so` / `libServiceLayer.so`:
  `_FILE_GetMountPoint` reads `/proc/mounts` per request — but has exactly **two call sites, both on the
  download path**. The upload path (`AttachmentStreamHandler::AddEntity`) never calls it, and
  `SLFile::isFullPath` accepts only a leading `/` or `smb:`, so a `\\host\share` UNC can never resolve.
  ⇒ mounting = ~93% fixes GET, ~15% fixes POST. **Do not spend a change window on it for uploads.**
  (Relevant SAP docs: Note 3003664; and KBA **3631883** "Unable to POST the attachments using the
  Service Layer", 10.0 FP2311+ — not yet read, needs an S-user.)
- **The bill is already in SAP.** The factory attaches the scanned vendor invoice to the GRPO at gate-in.
  Verified: GRPO 25714 → `AttachmentEntry 170187` → `80617082026120421928651.pdf`, 736,280 bytes —
  pulled it over SMB and it is the *same* TPAC bill (same IRN, same ₹2,53,110, same G.No 154 stamp).
  Of **623/623** GRPO-based Oil A/P drafts since 1 Jul, every one had a GRPO carrying an attachment.
- **Every human-keyed draft has an attachment; every API-created one has none.** The B1 client copies
  the GRPO's attachment forward on copy-to-target (`CopyToTargetDoc tYES`); the Service Layer does not.
- ⇒ **Proposed fix: `PATCH Drafts(N) {"AttachmentEntry": <GRPO's AtcEntry>}`.** One integer. No file
  operation, no mount, no root, no restart, no vendor. **UNTESTED** — the network dropped before the
  experiment. Sharp edge: draft and GRPO then share one Attachments2 row, so a file added later on the
  draft's Attachments tab also appears on the GRPO. Does not help expense/imprest bills (no GRPO).

### Unknowns still open
- ~~Does the Service Layer accept `PATCH Drafts(N) {"AttachmentEntry": …}`?~~ **YES — proven 2026-08-24**: 204, draft 54983 → 170187, GRPO 25714 unchanged.
- ~~Can `AttachmentEntry` be set back to null (i.e. does rollback work)?~~ **YES — proven 2026-08-24**: null → 204 → reads null; restore → 204. Six writes in `queries/USER36/sap-writes.jsonl`.
- Does the borrowed record survive the draft→invoice copy when a human presses Add?
- USER07's password is wrong; needed for drafts to land in Neetu's own Document Drafts list
- Separate concern surfaced by recon: the Service Layer is reportedly aborting workers ~150×/day
  with heap corruption. Unrelated to attachments — worth its own support ticket.
