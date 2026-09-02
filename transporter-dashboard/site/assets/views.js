/* ============================================================================
   views.js — table + drawer views for the JIVO "Transporter-wise Details" board
   ----------------------------------------------------------------------------
   Exports
     renderVendorList(container, ctx)   the transporter roster (sortable, selectable)
     renderInvoices(container, ctx)     A/P invoice table, vendor-bill first
     renderPayments(container, ctx)     outgoing payments, click to expand the bills
     openDrawer(kind, docEntry, ctx)    full record for one invoice / payment
     renderFlags(container, ctx)        "needs a look": everything that does not reconcile
     closeDrawer()                      convenience for the shell

   Plain ES module. No framework, no build step, no network call of any kind —
   this file never touches SAP; it only draws what pipeline/build.py already
   wrote to site/data/*.json. Read-only by construction (FACTS §8.1, RULE 0).

   ctx — what the shell passes in (every key optional; sensible fallbacks):
     company        'oil' | 'mart' | 'bev'   (also read: ctx.co, ctx.book,
                                              ctx.data.master.company)
     data           { master, invoices, payments, allocations, manifest }
                    each section = the loaded JSON file ({rows,…}) or a bare
                    rows array. Also accepted flat on ctx (ctx.invoices …).
     fy             'FY26' (default) | 'FY25' | 'ALL' | {from,to,label}
                    FY26 = DocDate >= 2026-04-01 (FACTS §6). Also ctx.period,
                    ctx.filters.fy, ctx.state.fy.
     vendor         CARD_CODE of the selected transporter, or null = all.
                    Also ctx.selectedVendor, ctx.cardCode, ctx.filters.vendor.
     search         initial free-text filter (vendor bill / DocNum / name).
     onSelectVendor(cardCode, masterRow)   optional callback
     openDrawer(kind, docEntry, ctx)       optional override of this module's
     hideSearch     true → renderInvoices does not draw its own search box

   Every user action ALSO bubbles a DOM CustomEvent from the container so a
   shell that prefers events can listen instead of passing callbacks:
     'transporter:select-vendor'  detail {cardCode, row}
     'transporter:open'           detail {kind, docEntry}

   Data facts this file renders (transporter-dashboard/FACTS.md — binding):
     §4  TDS lives on the invoice (TDS = OPCH.WTSum). OTHER_DEDUCTION is a
         residual, never a verified deduction; it is NULL when nothing was
         applied → "not computed". Label: "unexplained — shortage/damage claim
         or settled by journal".
     §5  ON_ACCOUNT payments (no VPM2 line) get their own explicit bucket.
     §6  Out-of-window targets render "(invoice outside window)" + DocEntry.
     §9  RESIDUAL_FLAG vocabulary: UNPAID / OK / GROSS_PAID / SHORT / OVER /
         PART_TDS. GROSS_PAID is a warning (TDS-compliance), never "overpaid".
     SQL header facts: SETTLED_BY can only be '18' or '' (VPM2 cannot express
         a per-invoice journal settlement); the journal/CN/reconciliation
         signal is PAY_CNT = 0 AND PAID_TO_DATE > 0, so the UNPAID bucket is
         always shown split on PAID_TO_DATE. A PARTIAL payment that carries an
         A/P credit-note line nets exactly (INV − CN + JE + OTHER = total)
         because SAP stores the CN line positive — shown as "nets", not chased.
         TRSFR_REF is '' on every transporter payment → "not recorded".
         OCRD.Balance: NEGATIVE = JIVO owes the transporter; all-time, not
         windowed.
   ============================================================================ */

import * as core from './core.js';
import * as mapping from './mapping.js';

/* ───────────────────────────── helpers ─────────────────────────────────── */

const MINUS = '−';
const RUPEE = '₹';

function fromCore(names, fallback) {
  for (const n of names) {
    const f = core && core[n];
    if (typeof f === 'function') return f;
  }
  return fallback;
}

function localEsc(s) {
  return String(s === null || s === undefined ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
const esc = fromCore(['esc', 'escapeHtml', 'escapeHTML'], localEsc);

/* Indian digit grouping: 1234567 → "12,34,567". Always local — a detail
   column must never mix rupees with lakhs/crores (FACTS §8.5), so this file
   does not delegate money formatting to a helper whose scaling it cannot see. */
function inGroup(intAbs) {
  const s = String(intAbs);
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  const rest = s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',');
  return rest + ',' + last3;
}

function isNil(n) {
  return n === null || n === undefined || n === '' || Number.isNaN(Number(n));
}

/* Exact rupees. Tables: whole rupees. Drawer / reconciliation: paise kept
   when present. Never returns a value for a nil input — callers use amt(). */
function inr(n, exact) {
  const v = Number(n);
  if (exact) {
    const abs = Math.abs(v);
    const whole = Math.floor(abs + 1e-9);
    const paise = Math.round((abs - whole) * 100);
    const body = paise ? inGroup(whole) + '.' + String(paise).padStart(2, '0') : inGroup(whole);
    const neg = v < 0 && (whole > 0 || paise > 0);
    return (neg ? MINUS : '') + RUPEE + body;
  }
  const r = Math.round(v);
  return (r < 0 ? MINUS : '') + RUPEE + inGroup(Math.abs(r));
}

/* "not computed" — always with the reason, never a bare dash. */
function nc(reason) {
  return `<span class="tv-nc" title="${esc(reason)}">not computed</span>`;
}

/* Money cell. Nil → not computed (reason required). Negative → danger colour. */
function amt(n, reason, exact) {
  if (isNil(n)) return nc(reason || 'value missing in the data file');
  const v = Number(n);
  const s = inr(v, exact);
  const neg = exact ? (v < -0.005) : (Math.round(v) < 0);
  return neg ? `<span class="tv-neg">${s}</span>` : s;
}

function count(n, reason) {
  if (isNil(n)) return nc(reason || 'count missing in the data file');
  return inGroup(Math.abs(Math.round(Number(n))));
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function localDate(iso) {
  if (!iso || typeof iso !== 'string' || iso.length < 10) return null;
  const y = iso.slice(0, 4), m = Number(iso.slice(5, 7)), d = iso.slice(8, 10);
  if (!m || m < 1 || m > 12) return iso;
  return `${d} ${MONTHS[m - 1]} ${y}`;
}
function dateCell(iso, reason) {
  const s = localDate(iso);
  return s ? `<span title="${esc(iso)}">${esc(s)}</span>` : nc(reason || 'date missing in SAP');
}

const COMPANY = {
  oil:  { label: 'JIVO Wellness (Oil)', accent: '#b45309' },
  mart: { label: 'JIVO Mart',           accent: '#6d28d9' },
  bev:  { label: 'JIVO Beverages',      accent: '#0e7490' },
};

const FY = {
  FY26: { key: 'FY26', from: '2026-04-01', to: '2027-04-01', label: 'FY26 (from 1 Apr 2026)' },
  FY25: { key: 'FY25', from: '2025-04-01', to: '2026-04-01', label: 'FY25 (1 Apr 2025 – 31 Mar 2026)' },
  ALL:  { key: 'ALL',  from: null,         to: null,         label: 'everything fetched (from 1 Apr 2025)' },
};

/* ─────────────────────────── ctx readers ───────────────────────────────── */

function companyOf(ctx) {
  const c = ctx && (ctx.company || ctx.co || ctx.book || (ctx.data && ctx.data.master && ctx.data.master.company));
  const k = String(c || 'oil').toLowerCase();
  if (k.startsWith('bev')) return 'bev';
  if (k.startsWith('mart')) return 'mart';
  return 'oil';
}

function companyLabel(ctx, co) {
  // a loadCompany() result carries {company, label}; accept it flat or under ctx.data
  for (const d of [ctx, ctx && ctx.data]) {
    if (d && typeof d.label === 'string' && d.label && companyOf({ company: d.company || co }) === co) return d.label;
  }
  const m = ctx && ctx.data && ctx.data.master;
  if (m && m.company_label && (m.company || co) === co) return m.company_label;
  const f = fromCore(['companyLabel'], null);
  if (f) { try { const s = f(co); if (s) return String(s); } catch (e) { /* fall through */ } }
  return COMPANY[co].label;
}

function sectionOf(ctx, name) {
  if (!ctx) return null;
  const pools = [ctx.data, ctx.sections, ctx];
  for (const p of pools) {
    if (!p) continue;
    const s = p[name];
    if (Array.isArray(s)) return { rows: s, error: null, loaded: true };
    if (s && typeof s === 'object' && Array.isArray(s.rows)) return { rows: s.rows, error: s.error || null, loaded: true };
    if (s && typeof s === 'object' && s.error) return { rows: [], error: s.error, loaded: false };
  }
  return { rows: [], error: null, loaded: false };
}

function manifestError(ctx, name, co) {
  const m = (ctx && (ctx.manifest || (ctx.data && ctx.data.manifest))) || null;
  try {
    const e = m && m.sections && m.sections[name] && m.sections[name][co] && m.sections[name][co].error;
    return e ? String(e) : null;
  } catch (e) { return null; }
}

/* Per-section status as core.loadCompany() reports it:
   {section, file, ok, rows:<count>, error, code, hint, stale, stale_since, kept_previous}. */
function sectionMeta(ctx, name) {
  for (const d of [ctx, ctx && ctx.data]) {
    const s = d && d.sections && d.sections[name];
    if (s && typeof s === 'object' && !Array.isArray(s) && !Array.isArray(s.rows)) return s;
  }
  return null;
}

function periodOf(ctx) {
  const raw = ctx && (ctx.fy ?? ctx.period ?? (ctx.filters && ctx.filters.fy) ?? (ctx.state && ctx.state.fy));
  if (raw === undefined || raw === null) return FY.FY26;
  if (typeof raw === 'object') {
    const from = raw.from || null, to = raw.to || null;
    return { key: raw.key || 'custom', from, to,
      label: raw.label || `${from ? localDate(from) : 'start'} → ${to ? localDate(to) : 'today'}` };
  }
  const k = String(raw).toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (k === '' || k === 'ALL' || k === 'ANY') return FY.ALL;
  if (/^(FY)?(26|2026|202627|202627)$/.test(k)) return FY.FY26;
  if (/^(FY)?(25|2025|202526)$/.test(k)) return FY.FY25;
  return { key: 'ALL', from: null, to: null, label: `period "${raw}" not understood — showing everything fetched` };
}

function inPeriod(iso, p) {
  if (!iso) return false;
  if (p.from && iso < p.from) return false;
  if (p.to && iso >= p.to) return false;
  return true;
}

function vendorOf(ctx) {
  const v = ctx && (ctx.vendor ?? ctx.selectedVendor ?? ctx.cardCode ?? (ctx.filters && ctx.filters.vendor) ?? (ctx.state && ctx.state.vendor) ?? null);
  if (!v) return null;
  if (typeof v === 'object') return v.CARD_CODE || v.cardCode || v.code || null;
  return String(v);
}

/* core.js names the search "q" in its state/URL; "search" is accepted too. */
function pushedSearch(ctx) {
  if (!ctx) return undefined;
  const cands = [ctx.search, ctx.q, ctx.filters && ctx.filters.search, ctx.filters && ctx.filters.q, ctx.state && ctx.state.q, ctx.state && ctx.state.search];
  for (const c of cands) if (c !== undefined && c !== null) return String(c);
  return undefined;
}
function searchOf(ctx) { return pushedSearch(ctx) || ''; }

/* core.js state.flag: one RESIDUAL_FLAG or MATCH_FLAG applied to whichever
   table owns it (mirrors core.applyFilters). '' = no flag filter. */
function flagOf(ctx) {
  const f = ctx && (ctx.flag ?? (ctx.filters && ctx.filters.flag) ?? (ctx.state && ctx.state.flag));
  return f ? String(f).trim().toUpperCase() : '';
}

/* One consolidated read of everything a view needs. */
function readCtx(ctx) {
  ctx = ctx || {};
  const co = companyOf(ctx);
  const master = sectionOf(ctx, 'master');
  const invoices = sectionOf(ctx, 'invoices');
  const payments = sectionOf(ctx, 'payments');
  const allocations = sectionOf(ctx, 'allocations');
  const vendorName = new Map();
  for (const r of master.rows) vendorName.set(r.CARD_CODE, r.CARD_NAME);
  for (const r of invoices.rows) if (!vendorName.has(r.CARD_CODE)) vendorName.set(r.CARD_CODE, r.CARD_NAME);
  for (const r of payments.rows) if (!vendorName.has(r.CARD_CODE)) vendorName.set(r.CARD_CODE, r.CARD_NAME);
  const payByNum = new Map();
  const payByEntry = new Map();
  for (const r of payments.rows) { payByNum.set(String(r.DOC_NUM), r); payByEntry.set(String(r.DOC_ENTRY), r); }
  const invByEntry = new Map();
  for (const r of invoices.rows) invByEntry.set(String(r.DOC_ENTRY), r);
  const allocByPay = new Map();
  const allocByInv = new Map();
  for (const a of allocations.rows) {
    const pk = String(a.PAY_DOC_ENTRY);
    if (!allocByPay.has(pk)) allocByPay.set(pk, []);
    allocByPay.get(pk).push(a);
    if (String(a.INV_TYPE) === '18') {
      const ik = String(a.TGT_DOC_ENTRY);
      if (!allocByInv.has(ik)) allocByInv.set(ik, []);
      allocByInv.get(ik).push(a);
    }
  }
  const man = (ctx.manifest || (ctx.data && ctx.data.manifest)) || null;
  const secObj = (ctx.data && ctx.data.invoices && !Array.isArray(ctx.data.invoices)) ? ctx.data.invoices : (ctx.invoices && !Array.isArray(ctx.invoices) ? ctx.invoices : null);
  const asOf = ctx.asOf || ctx.as_of || (ctx.data && (ctx.data.asOf || ctx.data.as_of)) || (man && man.as_of) || (secObj && secObj.as_of) || null;
  return {
    ctx, co, label: companyLabel(ctx, co), accent: COMPANY[co].accent, asOf,
    period: periodOf(ctx), vendor: vendorOf(ctx), search: searchOf(ctx),
    master, invoices, payments, allocations,
    vendorName, payByNum, payByEntry, invByEntry, allocByPay, allocByInv,
  };
}

/* ─────────────────────────── vocabulary ────────────────────────────────── */

/* Chip vocabulary. Defaults below; when core.js exports chipFor() its label /
   title / tone are adopted at module load so every view on the board uses
   the same words for the same flag. Tone names are shared (neutral / ok /
   warn / danger / onacct); the chip styling itself stays in this file. */
const INV_FLAG = {
  UNPAID:     { tone: 'neutral', label: 'Unpaid',           hint: 'No non-cancelled payment line touches this bill.' },
  OK:         { tone: 'ok',      label: 'Reconciles',       hint: 'Paid net of TDS: gross − TDS − discount = net paid (within ₹1).' },
  GROSS_PAID: { tone: 'warn',    label: 'Paid gross — TDS not deducted', hint: 'Paid in full. The TDS on the bill was not deducted at payment (SAP WTApplied = 0). A TDS-compliance question, not an overpayment.' },
  SHORT:      { tone: 'warn',    label: 'Short-paid',       hint: 'Paid less than gross − TDS. The gap is unexplained — shortage/damage claim or settled by journal.' },
  OVER:       { tone: 'danger',  label: 'Paid above bill',  hint: 'Genuinely paid above the bill.' },
  PART_TDS:   { tone: 'warn',    label: 'Partial TDS',      hint: 'Something was deducted at payment, but less than the TDS on the bill.' },
};
const UNPAID_RECON = { tone: 'onacct', label: 'Settled without payment', hint: 'No payment line, but SAP PaidToDate > 0: settled by reconciliation — journal, credit note, or an on-account payment matched later. Not unpaid in the cash sense.' };
const UNPAID_NONE  = { tone: 'neutral', label: 'Unpaid · untouched', hint: 'No payment line and SAP PaidToDate = 0. Nothing has been applied to this bill.' };

const PAY_FLAG = {
  MATCHED:    { tone: 'ok',     label: 'Matched',    hint: 'Allocation lines equal the payment total (within ₹1).' },
  ON_ACCOUNT: { tone: 'onacct', label: 'Paid, not yet matched to a bill', hint: 'No allocation line at all — paid against no bill. Sits on account until matched.' },
  PARTIAL:    { tone: 'warn',   label: 'Partly matched', hint: 'Allocation lines do not equal the payment total.' },
};
const PAY_NETS = { tone: 'ok', label: 'Matched net of credit note', hint: 'Lines exceed the total only because SAP stores the A/P credit-note line positive. Invoices − CN + JE + other = payment total exactly. Nothing to chase.' };

(function adoptCoreChips() {
  const f = core && typeof core.chipFor === 'function' ? core.chipFor : null;
  if (!f) return;
  const TONES = new Set(['neutral', 'ok', 'warn', 'danger', 'onacct']);
  for (const table of [INV_FLAG, PAY_FLAG]) {
    for (const key of Object.keys(table)) {
      let c = null;
      try { c = f(key); } catch (e) { continue; }
      if (!c || !c.label || String(c.flag || key).toUpperCase() !== key) continue;
      table[key].label = String(c.label);
      if (c.title) table[key].hint = String(c.title);
      if (TONES.has(c.tone)) table[key].tone = c.tone;
    }
  }
  if (INV_FLAG.GROSS_PAID.tone === 'danger') INV_FLAG.GROSS_PAID.tone = 'warn';   // FACTS §9: never a danger/overpaid reading
})();

function invoiceMeta(flag) {
  return INV_FLAG[flag] || { tone: 'neutral', label: flag || 'no flag', hint: 'RESIDUAL_FLAG value not in the documented vocabulary — shown raw.' };
}

const INV_TYPE_LABEL = {
  '18': 'A/P Invoice', '19': 'A/P Credit Note', '30': 'Journal Entry', '46': 'Outgoing Payment (on-account applied)',
  '24': 'Incoming Payment (contra)', '13': 'A/R Invoice (contra)', '14': 'A/R Credit Note (contra)',
};
function invTypeLabel(a) {
  if (a && a.INV_TYPE_LABEL) return String(a.INV_TYPE_LABEL);
  const t = a ? String(a.INV_TYPE ?? '') : '';
  return INV_TYPE_LABEL[t] || `OTHER (InvType=${t || 'null'})`;
}

function chip(meta, extraTitle) {
  const title = extraTitle ? `${meta.hint} ${extraTitle}` : meta.hint;
  return `<span class="tv-chip ${meta.tone}" title="${esc(title)}">${esc(meta.label)}</span>`;
}

/* Invoice status meta, with the UNPAID split on PAID_TO_DATE (SQL header). */
function invoiceStatus(r) {
  const f = String(r.RESIDUAL_FLAG || '');
  if (f === 'UNPAID') {
    const ptd = Number(r.PAID_TO_DATE);
    if (!isNil(r.PAID_TO_DATE) && ptd > 0) return UNPAID_RECON;
    return UNPAID_NONE;
  }
  return invoiceMeta(f);
}

/* Payment status meta, with the credit-note netting recovered (SQL header). */
function paymentNets(p) {
  const net = Number(p.INV_APPLIED || 0) - Number(p.CN_APPLIED || 0) + Number(p.JE_APPLIED || 0) + Number(p.OTHER_APPLIED || 0);
  return { net, ties: Math.abs(net - Number(p.PAY_TOTAL || 0)) <= 1 };
}
function paymentStatus(p) {
  const f = String(p.MATCH_FLAG || '');
  if (f === 'PARTIAL' && Number(p.CN_APPLIED) > 0 && paymentNets(p).ties) return PAY_NETS;
  return PAY_FLAG[f] || { tone: 'neutral', label: f || 'no flag', hint: 'MATCH_FLAG value not in the documented vocabulary — shown raw.' };
}

function payMode(p) {
  const parts = [];
  if (Number(p.TRSFR_SUM) > 0) parts.push('Transfer');
  if (Number(p.CHECK_SUM) > 0) parts.push('Cheque');
  if (Number(p.CASH_SUM) > 0) parts.push('Cash');
  if (!parts.length) return { mode: 'not recorded', ref: '', title: 'CashSum, CheckSum and TrsfrSum are all 0 on this payment.' };
  const ref = p.TRSFR_REF ? String(p.TRSFR_REF) : '';
  return { mode: parts.join(' + '), ref, title: ref ? `Reference ${ref}` : 'Transfer reference not recorded in SAP (blank on every transporter payment).' };
}

/* SETTLED_BY column text — the "column of last resort". */
function settledBy(r) {
  const codes = String(r.SETTLED_BY || '').split(',').map(s => s.trim()).filter(Boolean);
  const ptd = isNil(r.PAID_TO_DATE) ? null : Number(r.PAID_TO_DATE);
  const net = isNil(r.NET_PAID) ? 0 : Number(r.NET_PAID);
  if (!codes.length) {
    if (ptd !== null && ptd > 0) return { text: 'Reconciliation (JE / CN / on-account)', tone: 'onacct', title: `No payment line. SAP PaidToDate = ${inr(ptd, true)} — closed by internal reconciliation, journal or credit note.` };
    return { text: '—  nothing applied', tone: 'muted', title: 'No payment line and PaidToDate = 0.' };
  }
  const names = codes.map(c => INV_TYPE_LABEL[c] ? INV_TYPE_LABEL[c].replace(/ \(.*\)$/, '') : `InvType ${c}`);
  let text = names.map(n => n === 'A/P Invoice' ? 'Payment' : n).join(' + ');
  let title = `VPM2 line types on this bill: ${codes.join(', ')}.`;
  let tone = 'ink';
  if (ptd !== null && ptd > net + 1) {
    text += ' + other';
    tone = 'onacct';
    title += ` SAP PaidToDate ${inr(ptd, true)} exceeds payment lines ${inr(net, true)} by ${inr(ptd - net, true)} — that gap was closed by something other than a payment (reconciliation / JE / CN).`;
  }
  return { text, tone, title };
}

/* ─────────────────────────── per-container state ───────────────────────── */

const STATE = new WeakMap();
function stateOf(container, view, co) {
  let s = STATE.get(container);
  if (!s) { s = { bound: false, sort: {}, expanded: new Set(), search: null, flagFilter: 'ALL', co: null }; STATE.set(container, s); }
  if (s.co !== co) { s.expanded = new Set(); s.co = co; }
  s.view = view;
  return s;
}

/* The search box is owned locally between renders (the operator is typing);
   a value the shell pushes in ctx.search is adopted whenever it CHANGES, so
   a shell-driven "find bill X" wins, and a re-render that merely repeats the
   last pushed value does not wipe what the operator typed. */
function adoptSearch(state, ctx) {
  const pushed = pushedSearch(ctx);
  if (state.search === null) { state.search = pushed === undefined ? '' : pushed; state.pushedSearch = pushed; return; }
  if (pushed !== undefined && pushed !== state.pushedSearch) { state.search = pushed; state.pushedSearch = pushed; }
}
/* Same rule for the flags view's bucket: the chip row is local, a pushed
   ctx.flag is adopted when it changes. */
function adoptFlag(state, ctx) {
  const pushed = flagOf(ctx);
  if (state.pushedFlag === undefined) { state.flagFilter = pushed || 'ALL'; state.pushedFlag = pushed; return; }
  if (pushed !== state.pushedFlag) { state.flagFilter = pushed || 'ALL'; state.pushedFlag = pushed; }
}

function emit(container, name, detail) {
  try { container.dispatchEvent(new CustomEvent(name, { detail, bubbles: true })); } catch (e) { /* old browser */ }
}

function doOpen(container, ctx, kind, docEntry) {
  emit(container, 'transporter:open', { kind, docEntry });
  if (ctx && typeof ctx.openDrawer === 'function') { try { ctx.openDrawer(kind, docEntry, ctx); return; } catch (e) { console.warn('[views] ctx.openDrawer threw; using built-in drawer', e); } }
  openDrawer(kind, docEntry, ctx);
}

/* ─────────────────────────── sorting ───────────────────────────────────── */

function cmp(a, b, key, num) {
  const x = a[key], y = b[key];
  const xn = x === null || x === undefined || x === '', yn = y === null || y === undefined || y === '';
  if (xn && yn) return 0;
  if (xn) return 1;           // nulls last in both directions
  if (yn) return -1;
  if (num) return Number(x) - Number(y);
  return String(x).localeCompare(String(y), undefined, { numeric: true, sensitivity: 'base' });
}
function sortRows(rows, cols, sort) {
  const col = cols.find(c => c.key === sort.key);
  if (!col) return rows;
  const dir = sort.dir === 'asc' ? 1 : -1;
  return rows.slice().sort((a, b) => {
    const r = cmp(a, b, col.key, !!col.num);
    if (r !== 0) {
      const xn = a[col.key] === null || a[col.key] === undefined || a[col.key] === '';
      const yn = b[col.key] === null || b[col.key] === undefined || b[col.key] === '';
      if (xn || yn) return r;   // keep nulls last regardless of direction
      return r * dir;
    }
    const t = col.tie || 'DOC_ENTRY';
    const numericTie = Number.isFinite(Number(a[t])) && Number.isFinite(Number(b[t])) && a[t] !== '' && b[t] !== '';
    return cmp(a, b, t, numericTie) * -1;
  });
}

function headerCells(cols, sort) {
  return cols.map(c => {
    const active = sort.key === c.key;
    const aria = active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none';
    const cls = [c.num ? 'num' : '', c.cls || '', active ? 'is-sorted' : ''].filter(Boolean).join(' ');
    const sub = c.sub ? `<small>${esc(c.sub)}</small>` : '';
    const body = `<span class="tv-th-label">${esc(c.label)}${sub}</span><span class="tv-arrow" aria-hidden="true">${active ? (sort.dir === 'asc' ? '▲' : '▼') : ''}</span>`;
    if (c.sortable === false) return `<th class="${cls}" title="${esc(c.title || '')}">${body}</th>`;
    return `<th class="${cls}" aria-sort="${aria}" title="${esc(c.title || ('Sort by ' + c.label))}"><button type="button" class="tv-sortbtn" data-sort="${esc(c.key)}">${body}</button></th>`;
  }).join('');
}

function toggleSort(state, view, key, defaultDir) {
  const cur = state.sort[view] || {};
  if (cur.key === key) state.sort[view] = { key, dir: cur.dir === 'asc' ? 'desc' : 'asc' };
  else state.sort[view] = { key, dir: defaultDir || 'desc' };
}

/* ─────────────────────────── shared chrome ─────────────────────────────── */

function emptyState(title, lines) {
  return `<div class="tv-empty"><div class="tv-empty-title">${esc(title)}</div>${lines.map(l => `<div class="tv-empty-line">${l}</div>`).join('')}</div>`;
}

function loadProblem(R, sec, name) {
  if (sec.loaded && !sec.error) return null;
  const meta = sectionMeta(R.ctx, name);
  const merr = manifestError(R.ctx, name, R.co);
  const why = sec.error || (meta && meta.error) || merr;
  const hint = meta && meta.hint ? String(meta.hint) : '';
  return emptyState(`${name}.${R.co}.json did not load`, [
    why ? `Pipeline error: <code>${esc(why)}</code>${hint ? ' — ' + esc(hint) : ''}` : 'The section is missing from the page context — the shell has not loaded it for this book yet, or the file was not written by pipeline/build.py.',
    `Nothing is shown rather than a zero. Book: ${esc(R.label)}.`,
  ]);
}

/* A section that core.loadCompany() kept from a previous build because the
   last refresh failed is still shown — with that said out loud. */
function staleNote(R) {
  const names = [];
  for (const n of ['master', 'invoices', 'payments', 'allocations']) {
    const m = sectionMeta(R.ctx, n);
    if (m && m.stale) names.push(n + (m.stale_since ? ' since ' + (localDate(String(m.stale_since).slice(0, 10)) || m.stale_since) : ''));
  }
  return names.length ? ` <span class="tv-warntext tv-asof" title="core.loadCompany reports these sections as kept from a previous build because the last refresh failed">· previous build shown for ${esc(names.join(', '))}</span>` : '';
}

function vendorHeading(R) {
  if (!R.vendor) return asOfNote(R);
  const nm = R.vendorName.get(R.vendor) || '(name not in master)';
  return `<span class="tv-pill">${esc(nm)} <code>${esc(R.vendor)}</code></span>${asOfNote(R)}`;
}

function asOfNote(R) {
  const d = R.asOf ? localDate(String(R.asOf).slice(0, 10)) : null;
  return (d ? `<span class="tv-asof" title="as_of stamp of the data files">· data as of ${esc(d)}</span>` : '') + staleNote(R);
}

function totalsNote(n, extra) {
  return `<div class="tv-foot">${n} row${n === 1 ? '' : 's'}${extra ? ' · ' + extra : ''}</div>`;
}

function matchesSearch(r, q, fields) {
  if (!q) return true;
  const needle = q.toLowerCase();
  for (const f of fields) {
    const v = r[f];
    if (v !== null && v !== undefined && String(v).toLowerCase().includes(needle)) return true;
  }
  return false;
}

function rootOpen(R, viewCls) {
  return `<div class="tv ${viewCls}" data-company="${esc(R.co)}" style="--tv-accent:${esc(R.accent)}">`;
}

/* ═══════════════════════════ 1. VENDOR LIST ════════════════════════════ */

const VENDOR_COLS = [
  { key: 'CARD_NAME',  label: 'Transporter', tie: 'CARD_CODE', title: 'Vendor card name and code (OCRD, GroupCode 102)' },
  { key: 'INV_CNT',    label: 'Invoices',  num: true, title: 'Non-cancelled A/P invoices in the period' },
  { key: 'INV_GROSS',  label: 'Gross',     num: true, title: 'Σ OPCH.DocTotal in the period' },
  { key: 'INV_TDS',    label: 'TDS',       num: true, title: 'Σ OPCH.WTSum — TDS on the bills (lives on the invoice, not the payment)' },
  { key: 'PAY_TOTAL',  label: 'Paid',      num: true, sub: 'all payments', title: 'Σ OVPM.DocTotal of non-cancelled payments dated in the period — includes money that settled prior-year bills' },
  { key: 'ONACCT_AMT', label: 'On account', num: true, sub: 'no bill matched', title: 'Payments with no allocation line at all — paid against no bill (FACTS §5)' },
  { key: 'BALANCE',    label: 'Balance',   num: true, sub: 'ledger, all-time', title: 'OCRD.Balance, sign as SAP holds it: negative = JIVO owes the transporter; positive = advance held. All-time, not windowed.' },
  { key: 'FLAG_CNT',   label: 'Flags',     num: true, title: 'Invoices whose residual does not reconcile (SHORT / OVER / PART_TDS / GROSS_PAID) in the period' },
];

/* Roster is derived from the detail rows for the selected period — one code
   path for FY26 / FY25 / ALL. Master contributes the all-time ledger balance
   and first/last activity; in ALL mode the derived counts are cross-checked
   against master and any disagreement is said out loud. */
function buildRoster(R) {
  const byCode = new Map();
  const get = (code, name) => {
    let v = byCode.get(code);
    if (!v) { v = { CARD_CODE: code, CARD_NAME: name || R.vendorName.get(code) || code, INV_CNT: 0, INV_GROSS: 0, INV_TDS: 0, INV_DISC: 0, PAY_CNT: 0, PAY_TOTAL: 0, ONACCT_CNT: 0, ONACCT_AMT: 0, FLAG_CNT: 0, UNPAID_CNT: 0, BALANCE: null, FIRST_ACTIVITY: null, LAST_ACTIVITY: null, GROSS_PAID_CNT: 0, SHORT_CNT: 0, PART_TDS_CNT: 0, OVER_CNT: 0 }; byCode.set(code, v); }
    return v;
  };
  for (const r of R.invoices.rows) {
    if (!inPeriod(r.DOC_DATE, R.period)) continue;
    const v = get(r.CARD_CODE, r.CARD_NAME);
    v.INV_CNT += 1;
    v.INV_GROSS += Number(r.GROSS || 0);
    v.INV_TDS += Number(r.TDS || 0);
    v.INV_DISC += Number(r.DISCOUNT || 0);
    const f = String(r.RESIDUAL_FLAG || '');
    if (f === 'UNPAID') v.UNPAID_CNT += 1;
    else if (f !== 'OK') v.FLAG_CNT += 1;
    if (f === 'GROSS_PAID') v.GROSS_PAID_CNT += 1;
    if (f === 'SHORT') v.SHORT_CNT += 1;
    if (f === 'PART_TDS') v.PART_TDS_CNT += 1;
    if (f === 'OVER') v.OVER_CNT += 1;
  }
  for (const p of R.payments.rows) {
    if (!inPeriod(p.DOC_DATE, R.period)) continue;
    const v = get(p.CARD_CODE, p.CARD_NAME);
    v.PAY_CNT += 1;
    v.PAY_TOTAL += Number(p.PAY_TOTAL || 0);
    if (String(p.MATCH_FLAG) === 'ON_ACCOUNT') { v.ONACCT_CNT += 1; v.ONACCT_AMT += Number(p.PAY_TOTAL || 0); }
  }
  const masterBy = new Map(R.master.rows.map(m => [m.CARD_CODE, m]));
  for (const v of byCode.values()) {
    const m = masterBy.get(v.CARD_CODE);
    if (m) {
      v.BALANCE = isNil(m.BALANCE) ? null : Number(m.BALANCE);
      v.FIRST_ACTIVITY = m.FIRST_ACTIVITY || null;
      v.LAST_ACTIVITY = m.LAST_ACTIVITY || null;
      v.IN_MASTER = true;
    } else { v.IN_MASTER = false; }
  }
  let tieNote = null;
  if (R.period.key === 'ALL' && R.master.loaded) {
    let off = 0;
    for (const m of R.master.rows) {
      const v = byCode.get(m.CARD_CODE);
      const ic = v ? v.INV_CNT : 0, pc = v ? v.PAY_CNT : 0;
      if (ic !== Number(m.INV_CNT) || pc !== Number(m.PAY_CNT)) off += 1;
    }
    const silent = R.master.rows.length - byCode.size;
    tieNote = off === 0 ? `ties to master.${R.co}.json (${R.master.rows.length} vendors)` : `<span class="tv-warntext">${off} vendor${off === 1 ? '' : 's'} differ from master.${R.co}.json — detail files and master were not built from the same run</span>`;
    if (silent > 0) tieNote += ` · ${silent} in master with no detail rows`;
  }
  return { rows: [...byCode.values()], tieNote, masterCount: R.master.rows.length };
}

export function renderVendorList(container, ctx) {
  const R = readCtx(ctx);
  const state = stateOf(container, 'vendors', R.co);
  state.ctx = ctx;
  bind(container);

  const problem = loadProblem(R, R.invoices, 'invoices') || loadProblem(R, R.payments, 'payments');
  if (problem) { container.innerHTML = rootOpen(R, 'tv-vendors') + problem + '</div>'; return; }

  const roster = buildRoster(R);
  const sort = state.sort.vendors || (state.sort.vendors = { key: 'INV_GROSS', dir: 'desc' });
  const rows = sortRows(roster.rows, VENDOR_COLS, sort);

  let html = rootOpen(R, 'tv-vendors');
  html += `<div class="tv-bar"><div class="tv-kicker">Transporters · ${esc(R.label)} · ${esc(R.period.label)} ${asOfNote(R)}</div>`;
  html += `<div class="tv-bar-right">${R.vendor ? `<button type="button" class="tv-btn" data-clear-vendor>Show all transporters</button>` : ''}</div></div>`;

  if (!rows.length) {
    html += emptyState('No transporter activity in this period', [
      `No non-cancelled A/P invoice or outgoing payment for a GroupCode-102 vendor is dated in ${esc(R.period.label)} in ${esc(R.label)}.`,
      roster.masterCount ? `${roster.masterCount} transporter${roster.masterCount === 1 ? '' : 's'} have activity somewhere in the fetched window (from 1 Apr 2025) — switch the period to see them.` : 'master.json lists no transporter with activity since 1 Apr 2025 either.',
    ]) + '</div>';
    container.innerHTML = html;
    return;
  }

  html += `<div class="tblbox tv-tblbox"><table class="tv-table tv-roster"><thead><tr>${headerCells(VENDOR_COLS, sort)}</tr></thead><tbody>`;
  for (const v of rows) {
    const sel = R.vendor && R.vendor === v.CARD_CODE;
    const flagTitle = `${v.FLAG_CNT} flagged (${v.GROSS_PAID_CNT} gross-paid/TDS not deducted, ${v.SHORT_CNT} short${v.PART_TDS_CNT ? `, ${v.PART_TDS_CNT} part-TDS` : ''}${v.OVER_CNT ? `, ${v.OVER_CNT} over` : ''}) · ${v.UNPAID_CNT} unpaid`;
    html += `<tr class="tv-row is-select${sel ? ' is-selected' : ''}" data-card="${esc(v.CARD_CODE)}" tabindex="0" role="button" aria-pressed="${sel ? 'true' : 'false'}" title="${esc('Select ' + v.CARD_NAME)}">`;
    html += `<td class="tv-name"><span class="tv-vname">${esc(v.CARD_NAME)}</span><span class="tv-vcode">${esc(v.CARD_CODE)}${v.IN_MASTER ? '' : ' · not in master'}</span></td>`;
    html += `<td class="num">${count(v.INV_CNT)}</td>`;
    html += `<td class="num">${v.INV_CNT ? amt(v.INV_GROSS) : '<span class="tv-muted" title="no invoice in the period — payments only">no bills</span>'}</td>`;
    html += `<td class="num">${v.INV_CNT ? amt(v.INV_TDS) : '<span class="tv-muted" title="no invoice in the period — payments only">no bills</span>'}</td>`;
    html += `<td class="num" title="${esc(v.PAY_CNT + ' payment' + (v.PAY_CNT === 1 ? '' : 's'))}">${v.PAY_CNT ? amt(v.PAY_TOTAL) : '<span class="tv-muted" title="no payment dated in the period">none</span>'}</td>`;
    html += `<td class="num">${v.ONACCT_CNT ? `<span class="tv-onacct">${amt(v.ONACCT_AMT)}</span> <span class="tv-sub">${v.ONACCT_CNT}</span>` : (v.PAY_CNT ? '<span class="tv-muted" title="every payment in the period carries an allocation line">none</span>' : '<span class="tv-muted" title="no payment dated in the period">no payments</span>')}</td>`;
    html += `<td class="num" title="${esc(balanceTitle(v.BALANCE))}">${v.IN_MASTER ? amt(v.BALANCE, 'SAP holds NULL in OCRD.Balance for this card') : nc('vendor card not in master.json')}</td>`;
    html += `<td class="num" title="${esc(flagTitle)}">${v.FLAG_CNT ? `<span class="tv-warntext">${count(v.FLAG_CNT)}</span>` : (v.INV_CNT ? '<span class="tv-oktext" title="every paid bill reconciles or is unpaid">0</span>' : '<span class="tv-muted" title="no invoice in the period">no bills</span>')}</td>`;
    html += `</tr>`;
  }
  html += `</tbody></table></div>`;
  const hidden = roster.masterCount - roster.rows.length;
  html += totalsNote(rows.length, [
    roster.tieNote,
    (R.period.key !== 'ALL' && hidden > 0) ? `${hidden} more transporter${hidden === 1 ? '' : 's'} with activity only outside ${esc(R.period.key)}` : null,
    'click a row to select · click a heading to sort · balance is SAP’s all-time ledger figure, negative = JIVO owes',
  ].filter(Boolean).join(' · '));
  html += '</div>';
  container.innerHTML = html;
}

function balanceTitle(b) {
  if (isNil(b)) return 'OCRD.Balance is NULL in SAP';
  const v = Number(b);
  if (v < 0) return `JIVO owes the transporter ${inr(v, true).replace(MINUS, '')} (net credit, all-time ledger)`;
  if (v > 0) return `Advance held / transporter owes JIVO ${inr(v, true)} (net debit, all-time ledger)`;
  return 'Ledger balance is exactly zero (all-time)';
}

/* ═══════════════════════════ 2. INVOICES ═══════════════════════════════ */

const INVOICE_COLS = [
  { key: 'DOC_DATE',       label: 'Date',         tie: 'DOC_NUM', title: 'OPCH.DocDate' },
  { key: 'DOC_NUM',        label: 'DocNum',        title: 'SAP A/P invoice number' },
  { key: 'VENDOR_BILL',    label: 'Vendor bill',   cls: 'tv-col-bill', title: 'OPCH.NumAtCard — the transporter’s own bill number' },
  { key: 'CARD_NAME',      label: 'Transporter',   cls: 'tv-col-vendor' },
  { key: 'GROSS',          label: 'Gross',         num: true, title: 'OPCH.DocTotal' },
  { key: 'TDS',            label: 'TDS',           num: true, sub: 'on bill', title: 'OPCH.WTSum — TDS lives on the invoice, not the payment' },
  { key: 'DISCOUNT',       label: 'Discount',      num: true, title: 'OPCH.DiscSum (0 on every row today; column kept for the reconciliation line)' },
  { key: 'OTHER_DEDUCTION', label: 'Other deduction', num: true, sub: 'residual · unexplained', title: 'GROSS − TDS − DISCOUNT − NET PAID. A balancing figure, not a verified deduction: unexplained — shortage/damage claim or settled by journal. Not computed when nothing was applied.' },
  { key: 'NET_PAID',       label: 'Net paid',      num: true, title: 'Σ VPM2.SumApplied (InvType 18) from non-cancelled payments' },
  { key: 'RESIDUAL_FLAG',  label: 'Status',        title: 'Reconciliation result (FACTS §9)' },
  { key: 'PAY_NUMS',       label: 'Payments',      sortable: false, title: 'Outgoing payments that settled this bill — click to open' },
  { key: 'SETTLED_BY',     label: 'Settled by',    title: 'Column of last resort: what closed the bill' },
];

function payNumChips(R, container, r) {
  const nums = String(r.PAY_NUMS || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!nums.length) return `<span class="tv-muted" title="PAY_CNT = 0">none</span>`;
  return nums.map(n => {
    if (n.endsWith('...')) return `<span class="tv-muted" title="list truncated by the pipeline at 200 characters">…</span>`;
    const p = R.payByNum.get(n);
    if (p) return `<button type="button" class="tv-doclink" data-open-pay="${esc(p.DOC_ENTRY)}" title="${esc('Open payment ' + n + ' · ' + localDate(p.DOC_DATE) + ' · ' + inr(p.PAY_TOTAL, true))}">${esc(n)}</button>`;
    return `<span class="tv-doclink is-dead" title="payment ${esc(n)} is not in the payments file — dated before 1 Apr 2025, or the list was truncated — so it cannot be opened here">${esc(n)}</span>`;
  }).join(' ');
}

export function renderInvoices(container, ctx) {
  const R = readCtx(ctx);
  const state = stateOf(container, 'invoices', R.co);
  state.ctx = ctx;
  bind(container);
  adoptSearch(state, ctx);

  const problem = loadProblem(R, R.invoices, 'invoices');
  if (problem) { container.innerHTML = rootOpen(R, 'tv-invoices') + problem + '</div>'; return; }

  const all = R.invoices.rows;
  const byVendor = R.vendor ? all.filter(r => r.CARD_CODE === R.vendor) : all;
  const byPeriod = byVendor.filter(r => inPeriod(r.DOC_DATE, R.period));
  const flag = flagOf(ctx);
  const invFlag = flag && INV_FLAG[flag] ? flag : '';          // a MATCH_FLAG belongs to the payments table, ignore it here
  const byFlag = invFlag ? byPeriod.filter(r => String(r.RESIDUAL_FLAG) === invFlag) : byPeriod;
  const q = (state.search || '').trim();
  const visible = byFlag.filter(r => matchesSearch(r, q, ['VENDOR_BILL', 'DOC_NUM', 'CARD_NAME', 'CARD_CODE', 'PAY_NUMS', 'DOC_ENTRY']));
  const sort = state.sort.invoices || (state.sort.invoices = { key: 'DOC_DATE', dir: 'desc' });
  const rows = sortRows(visible, INVOICE_COLS, sort);

  let html = rootOpen(R, 'tv-invoices');
  html += `<div class="tv-bar"><div class="tv-kicker">A/P invoices · ${esc(R.label)} · ${esc(R.period.label)} ${vendorHeading(R)}${invFlag ? ` <span class="tv-pill" title="flag filter from the board">${chip(invoiceMeta(invFlag))} only</span>` : ''}</div>`;
  if (!ctx || !ctx.hideSearch) {
    html += `<div class="tv-bar-right"><label class="tv-search"><span class="tv-srlabel">Find bill</span><input type="search" data-search placeholder="vendor bill no, DocNum, transporter" value="${esc(state.search || '')}" autocomplete="off" spellcheck="false"></label></div>`;
  }
  html += `</div>`;

  if (!rows.length) {
    const lines = [];
    if (q) lines.push(`No invoice in view matches “${esc(q)}” on vendor bill, DocNum, transporter or payment number. ${byFlag.length} invoice${byFlag.length === 1 ? '' : 's'} are in view before the search.`);
    else if (invFlag && byPeriod.length) lines.push(`${byPeriod.length} invoice${byPeriod.length === 1 ? '' : 's'} in the period, none flagged ${esc(invFlag)}. Clear the flag filter to see them.`);
    else if (R.vendor && !byVendor.length) lines.push(`${esc(R.vendorName.get(R.vendor) || R.vendor)} has no non-cancelled A/P invoice in the fetched window (from 1 Apr 2025) in ${esc(R.label)}. It may appear here through payments only.`);
    else if (R.vendor) lines.push(`${esc(R.vendorName.get(R.vendor) || R.vendor)} has ${byVendor.length} invoice${byVendor.length === 1 ? '' : 's'} in the fetched window, none dated in ${esc(R.period.label)}. Switch the period.`);
    else if (!all.length) lines.push(`invoices.${esc(R.co)}.json loaded with zero rows — no transporter A/P invoice since 1 Apr 2025 in ${esc(R.label)}.`);
    else lines.push(`${all.length} invoice${all.length === 1 ? '' : 's'} are in the fetched window, none dated in ${esc(R.period.label)}.`);
    html += emptyState('No invoices to show', lines) + '</div>';
    container.innerHTML = html;
    return;
  }

  const showVendor = !R.vendor;
  const cols = showVendor ? INVOICE_COLS : INVOICE_COLS.filter(c => c.key !== 'CARD_NAME');
  html += `<div class="tblbox tv-tblbox"><table class="tv-table tv-invtable"><thead><tr>${headerCells(cols, sort)}</tr></thead><tbody>`;
  const tot = { GROSS: 0, TDS: 0, DISCOUNT: 0, NET_PAID: 0, OTHER: 0, OTHER_POS: 0, OTHER_NEG: 0, otherN: 0, flags: {} };
  for (const r of rows) {
    const st = invoiceStatus(r);
    tot.GROSS += Number(r.GROSS || 0); tot.TDS += Number(r.TDS || 0); tot.DISCOUNT += Number(r.DISCOUNT || 0); tot.NET_PAID += Number(r.NET_PAID || 0);
    if (!isNil(r.OTHER_DEDUCTION)) { const _od = Number(r.OTHER_DEDUCTION); tot.OTHER += _od; if (_od > 0) tot.OTHER_POS += _od; else tot.OTHER_NEG += _od; tot.otherN += 1; }
    tot.flags[st.label] = (tot.flags[st.label] || 0) + 1;
    const sb = settledBy(r);
    html += `<tr class="tv-row" data-inv="${esc(r.DOC_ENTRY)}">`;
    html += `<td>${dateCell(r.DOC_DATE)}</td>`;
    html += `<td><button type="button" class="tv-doclink" data-open-inv="${esc(r.DOC_ENTRY)}" title="Open invoice DocEntry ${esc(r.DOC_ENTRY)}">${esc(r.DOC_NUM)}</button></td>`;
    html += `<td class="tv-col-bill"><button type="button" class="tv-bill" data-open-inv="${esc(r.DOC_ENTRY)}" title="${esc('Vendor bill ' + (r.VENDOR_BILL || '(none)') + ' — open')}">${esc(r.VENDOR_BILL || '(none)')}</button></td>`;
    if (showVendor) html += `<td class="tv-col-vendor"><span class="tv-ellip" title="${esc(r.CARD_NAME + ' · ' + r.CARD_CODE + ' · branch ' + (r.BRANCH || '(no branch)'))}">${esc(r.CARD_NAME)}</span></td>`;
    html += `<td class="num">${amt(r.GROSS, 'OPCH.DocTotal missing')}</td>`;
    html += `<td class="num" title="${esc(isNil(r.TDS_APPLIED) ? '' : 'WTApplied (cross-check) = ' + inr(r.TDS_APPLIED, true))}">${amt(r.TDS, 'OPCH.WTSum missing')}</td>`;
    html += `<td class="num">${amt(r.DISCOUNT, 'OPCH.DiscSum missing')}</td>`;
    html += `<td class="num" title="${esc(otherTitle(r))}">${isNil(r.OTHER_DEDUCTION) ? nc('no payment applied to this bill — a residual against nothing is meaningless') : amt(r.OTHER_DEDUCTION)}</td>`;
    html += `<td class="num">${isNil(r.NET_PAID) ? nc('NET_PAID missing') : (Number(r.PAY_CNT) > 0 ? amt(r.NET_PAID) : `<span class="tv-muted" title="${esc(Number(r.PAID_TO_DATE || 0) > 0 ? 'no payment line — SAP PaidToDate ' + inr(r.PAID_TO_DATE, true) + ' (settled by reconciliation)' : 'no payment line, nothing reconciled')}">no payment line</span>`)}</td>`;
    html += `<td>${chip(st, r.RESIDUAL_FLAG === 'GROSS_PAID' && !isNil(r.TDS_APPLIED) ? `WTApplied on this row = ${inr(r.TDS_APPLIED, true)}.` : '')}</td>`;
    html += `<td class="tv-paynums">${payNumChips(R, container, r)}</td>`;
    html += `<td><span class="tv-settled ${sb.tone}" title="${esc(sb.title)}">${esc(sb.text)}</span></td>`;
    html += `</tr>`;
  }
  html += `</tbody><tfoot><tr class="tv-total"><td colspan="${showVendor ? 4 : 3}">Total of ${rows.length} shown · ${esc(R.label)} only</td>`;
  html += `<td class="num">${amt(tot.GROSS)}</td><td class="num">${amt(tot.TDS)}</td><td class="num">${amt(tot.DISCOUNT)}</td>`;
  html += `<td class="num" title="not one figure: short-paid gaps (+) and TDS-not-withheld (−) are different phenomena and are never netted here">${tot.otherN ? `<span class="tv-sub">${tot.otherN} rows · short +${inr(tot.OTHER_POS)} · TDS not withheld −${inr(Math.abs(tot.OTHER_NEG))}</span>` : nc('no row in view has a payment applied')}</td>`;
  html += `<td class="num">${amt(tot.NET_PAID)}</td><td colspan="3" class="tv-flagsum">${Object.entries(tot.flags).map(([k, n]) => `${n} ${esc(k)}`).join(' · ')}</td></tr></tfoot></table></div>`;
  html += totalsNote(rows.length, 'click the vendor bill or DocNum for the full record · payment numbers open the payment · Other deduction is a residual, never a verified figure');
  html += '</div>';
  container.innerHTML = html;
}

function otherTitle(r) {
  if (isNil(r.OTHER_DEDUCTION)) return 'not computed — no payment applied';
  const v = Number(r.OTHER_DEDUCTION);
  const base = 'GROSS − TDS − DISCOUNT − NET PAID. Unexplained — shortage/damage claim or settled by journal.';
  if (Math.abs(v) <= 1) return base + ' Within ₹1: reconciles.';
  if (v < 0 && !isNil(r.TDS) && Math.abs(v + Number(r.TDS)) <= 1) return base + ' Equals −TDS exactly: the full gross was paid and the TDS on the bill was not deducted at payment.';
  if (v < 0) return base + ' Negative: more was paid than gross − TDS.';
  return base;
}

/* ═══════════════════════════ 3. PAYMENTS ═══════════════════════════════ */

const PAYMENT_COLS = [
  { key: '_exp',        label: '',           sortable: false, cls: 'tv-col-exp' },
  { key: 'DOC_DATE',    label: 'Date',       tie: 'DOC_NUM', title: 'OVPM.DocDate' },
  { key: 'DOC_NUM',     label: 'DocNum',     title: 'SAP outgoing payment number' },
  { key: 'CARD_NAME',   label: 'Transporter', cls: 'tv-col-vendor' },
  { key: 'PAY_TOTAL',   label: 'Total',      num: true, title: 'OVPM.DocTotal' },
  { key: '_mode',       label: 'How paid',   sortable: false, title: 'CashSum / CheckSum / TrsfrSum split + transfer reference' },
  { key: 'INV_CNT',     label: 'Bills',      num: true, title: 'Distinct A/P invoices (InvType 18) this payment applies to' },
  { key: 'ALLOC_TOTAL', label: 'Applied',    num: true, sub: 'all line types', title: 'Σ VPM2.SumApplied across every InvType (18 invoice, 19 CN, 30 JE, 46 on-account, other) — nothing dropped' },
  { key: 'UNALLOCATED', label: 'Unallocated', num: true, title: 'PAY_TOTAL − Applied. Negative when the lines exceed the total (credit-note sign — see status).' },
  { key: 'MATCH_FLAG',  label: 'Match',      title: 'MATCHED / ON_ACCOUNT / PARTIAL (FACTS §5)' },
];

export function renderPayments(container, ctx) {
  const R = readCtx(ctx);
  const state = stateOf(container, 'payments', R.co);
  state.ctx = ctx;
  bind(container);

  const problem = loadProblem(R, R.payments, 'payments');
  if (problem) { container.innerHTML = rootOpen(R, 'tv-payments') + problem + '</div>'; return; }

  const all = R.payments.rows;
  const byVendor = R.vendor ? all.filter(p => p.CARD_CODE === R.vendor) : all;
  const byPeriod = byVendor.filter(p => inPeriod(p.DOC_DATE, R.period));
  const flag = flagOf(ctx);
  const payFlag = flag && PAY_FLAG[flag] ? flag : '';          // a RESIDUAL_FLAG belongs to the invoices table, ignore it here
  const byFlag = payFlag ? byPeriod.filter(p => String(p.MATCH_FLAG) === payFlag) : byPeriod;
  const sort = state.sort.payments || (state.sort.payments = { key: 'DOC_DATE', dir: 'desc' });
  const rows = sortRows(byFlag, PAYMENT_COLS, sort);

  let html = rootOpen(R, 'tv-payments');
  html += `<div class="tv-bar"><div class="tv-kicker">Outgoing payments · ${esc(R.label)} · ${esc(R.period.label)} ${vendorHeading(R)}${payFlag ? ` <span class="tv-pill" title="flag filter from the board">${chip(PAY_FLAG[payFlag])} only</span>` : ''}</div>`;
  const onacct = byPeriod.filter(p => String(p.MATCH_FLAG) === 'ON_ACCOUNT');
  const onacctAmt = onacct.reduce((s, p) => s + Number(p.PAY_TOTAL || 0), 0);
  html += `<div class="tv-bar-right">${byPeriod.length ? `<span class="tv-pill onacct" title="Payments with no allocation line at all — money paid against no bill (FACTS §5)">${onacct.length} on account · ${onacct.length ? inr(onacctAmt) : 'nil'}</span>` : ''}</div></div>`;

  if (!rows.length) {
    const lines = [];
    if (payFlag && byPeriod.length) lines.push(`${byPeriod.length} payment${byPeriod.length === 1 ? '' : 's'} in the period, none flagged ${esc(payFlag)}. Clear the flag filter to see them.`);
    else if (R.vendor && !byVendor.length) lines.push(`${esc(R.vendorName.get(R.vendor) || R.vendor)} has no non-cancelled outgoing payment in the fetched window (from 1 Apr 2025) in ${esc(R.label)}.`);
    else if (R.vendor) lines.push(`${esc(R.vendorName.get(R.vendor) || R.vendor)} has ${byVendor.length} payment${byVendor.length === 1 ? '' : 's'} in the fetched window, none dated in ${esc(R.period.label)}. Switch the period.`);
    else if (!all.length) lines.push(`payments.${esc(R.co)}.json loaded with zero rows — no transporter payment since 1 Apr 2025 in ${esc(R.label)}.`);
    else lines.push(`${all.length} payment${all.length === 1 ? '' : 's'} are in the fetched window, none dated in ${esc(R.period.label)}.`);
    html += emptyState('No payments to show', lines) + '</div>';
    container.innerHTML = html;
    return;
  }

  const showVendor = !R.vendor;
  const cols = showVendor ? PAYMENT_COLS : PAYMENT_COLS.filter(c => c.key !== 'CARD_NAME');
  const span = cols.length;
  html += `<div class="tblbox tv-tblbox"><table class="tv-table tv-paytable"><thead><tr>${headerCells(cols, sort)}</tr></thead><tbody>`;
  const tot = { PAY_TOTAL: 0, ALLOC_TOTAL: 0, UNALLOCATED: 0, INV_CNT: 0 };
  for (const p of rows) {
    const key = String(p.DOC_ENTRY);
    const open = state.expanded.has(key);
    const st = paymentStatus(p);
    const mode = payMode(p);
    tot.PAY_TOTAL += Number(p.PAY_TOTAL || 0); tot.ALLOC_TOTAL += Number(p.ALLOC_TOTAL || 0); tot.UNALLOCATED += Number(p.UNALLOCATED || 0); tot.INV_CNT += Number(p.INV_CNT || 0);
    html += `<tr class="tv-row is-expandable${open ? ' is-open' : ''}" data-pay="${esc(key)}" aria-expanded="${open ? 'true' : 'false'}" title="Click to show the bills this payment settled">`;
    html += `<td class="tv-col-exp"><span class="tv-caret" aria-hidden="true">${open ? '▾' : '▸'}</span></td>`;
    html += `<td>${dateCell(p.DOC_DATE)}</td>`;
    html += `<td><button type="button" class="tv-doclink" data-open-pay="${esc(key)}" title="Open payment DocEntry ${esc(key)}">${esc(p.DOC_NUM)}</button></td>`;
    if (showVendor) html += `<td class="tv-col-vendor"><span class="tv-ellip" title="${esc(p.CARD_NAME + ' · ' + p.CARD_CODE)}">${esc(p.CARD_NAME)}</span></td>`;
    html += `<td class="num"><strong>${amt(p.PAY_TOTAL, 'OVPM.DocTotal missing')}</strong></td>`;
    html += `<td title="${esc(mode.title)}">${esc(mode.mode)}${mode.ref ? ` <span class="tv-sub">${esc(mode.ref)}</span>` : ' <span class="tv-sub">ref not recorded</span>'}</td>`;
    html += `<td class="num">${String(p.MATCH_FLAG) === 'ON_ACCOUNT' ? '<span class="tv-onacct" title="no allocation line">0</span>' : count(p.INV_CNT)}</td>`;
    html += `<td class="num" title="${esc(allocTitle(p))}">${String(p.MATCH_FLAG) === 'ON_ACCOUNT' ? '<span class="tv-onacct" title="no allocation line — nothing applied">nothing</span>' : amt(p.ALLOC_TOTAL, 'ALLOC_TOTAL missing')}</td>`;
    html += `<td class="num">${unallocCell(p, st)}</td>`;
    html += `<td>${chip(st)}</td>`;
    html += `</tr>`;
    if (open) html += `<tr class="tv-subrow" data-sub-for="${esc(key)}"><td colspan="${span}">${allocationPanel(R, p, true)}</td></tr>`;
  }
  html += `</tbody><tfoot><tr class="tv-total"><td colspan="${showVendor ? 4 : 3}">Total of ${rows.length} shown · ${esc(R.label)} only</td>`;
  html += `<td class="num">${amt(tot.PAY_TOTAL)}</td><td></td><td class="num">${count(tot.INV_CNT)}</td><td class="num">${amt(tot.ALLOC_TOTAL)}</td><td class="num">${amt(tot.UNALLOCATED)}</td><td>${onacct.length ? `<span class="tv-onacct">${onacct.length} on account</span>` : ''}</td></tr></tfoot></table></div>`;
  html += totalsNote(rows.length, 'click a row to attach its bills inline · DocNum opens the full record with the mapping · every VPM2 line type is counted, none dropped');
  html += '</div>';
  container.innerHTML = html;
}

function allocTitle(p) {
  return `Invoices ${inr(p.INV_APPLIED || 0, true)} · credit notes ${inr(p.CN_APPLIED || 0, true)} · journal ${inr(p.JE_APPLIED || 0, true)} · other ${inr(p.OTHER_APPLIED || 0, true)} · lines ${p.ALLOC_CNT}`;
}

function unallocCell(p, st) {
  if (String(p.MATCH_FLAG) === 'ON_ACCOUNT') return `<span class="tv-onacct" title="the whole payment sits on account — no bill matched">${amt(p.PAY_TOTAL)}</span>`;
  if (isNil(p.UNALLOCATED)) return nc('UNALLOCATED missing');
  if (st === PAY_NETS) return `<span class="tv-muted" title="${esc(PAY_NETS.hint + ' Raw UNALLOCATED = ' + inr(p.UNALLOCATED, true))}">nets</span>`;
  const v = Number(p.UNALLOCATED);
  if (Math.abs(v) <= 1) return `<span class="tv-oktext">${inr(0)}</span>`;
  return amt(v);
}

/* Inline panel: the bills (and every other line) attached to one payment. */
function allocationPanel(R, p, compact) {
  const lines = R.allocByPay.get(String(p.DOC_ENTRY)) || [];
  if (!lines.length) {
    if (String(p.MATCH_FLAG) === 'ON_ACCOUNT' || Number(p.ALLOC_CNT) === 0) {
      return `<div class="tv-panel onacct"><strong>Paid, not yet matched to a bill.</strong> This payment has no VPM2 allocation line at all — ${amt(p.PAY_TOTAL, 'OVPM.DocTotal missing')} was paid to ${esc(p.CARD_NAME)} against no document. It stays on account until Accounts reconciles it.${p.REMARKS ? ` <span class="tv-muted">Remarks: ${esc(p.REMARKS)}</span>` : ''}</div>`;
    }
    if (!R.allocations.loaded) return `<div class="tv-panel">${nc('allocations.' + R.co + '.json did not load, so the lines cannot be listed')} — SAP says this payment has ${count(p.ALLOC_CNT)} line${Number(p.ALLOC_CNT) === 1 ? '' : 's'} applying ${amt(p.ALLOC_TOTAL)}.</div>`;
    return `<div class="tv-panel warn">SAP counts ${count(p.ALLOC_CNT)} allocation line${Number(p.ALLOC_CNT) === 1 ? '' : 's'} on this payment but allocations.${esc(R.co)}.json carries none for DocEntry ${esc(p.DOC_ENTRY)} — the two files were not built from the same run. ${nc('lines unavailable')}</div>`;
  }
  let html = `<div class="tv-panel"><table class="tv-table tv-lines"><thead><tr><th>Type</th><th>Document</th><th>Doc date</th><th class="tv-col-bill">Vendor bill</th><th class="num">Bill gross</th><th class="num">TDS on bill</th><th class="num">Applied</th><th>Note</th></tr></thead><tbody>`;
  let sum = 0;
  for (const a of lines) {
    const t = String(a.INV_TYPE);
    const inWin = a.IN_WINDOW === 'Y';
    const isInv = t === '18';
    const inv = isInv ? R.invByEntry.get(String(a.TGT_DOC_ENTRY)) : null;
    sum += Number(a.SUM_APPLIED || 0);
    let doc;
    if (isInv && inv) doc = `<button type="button" class="tv-doclink" data-open-inv="${esc(inv.DOC_ENTRY)}" title="Open invoice">${esc(inv.DOC_NUM)}</button>`;
    else if (isInv && !inWin) doc = `<span class="tv-muted" title="dated before 1 Apr 2025 — not in invoices.${esc(R.co)}.json">(invoice outside window) DocEntry ${esc(a.TGT_DOC_ENTRY)}</span>`;
    else if (isInv) doc = `<span class="tv-muted" title="IN_WINDOW = Y but the row is not in invoices.${esc(R.co)}.json — files from different runs, or the invoice is cancelled">invoice DocEntry ${esc(a.TGT_DOC_ENTRY)} (not in file)</span>`;
    else doc = `<span title="${esc(invTypeLabel(a))} DocEntry ${esc(a.TGT_DOC_ENTRY)}">${a.TGT_DOC_NUM ? esc(a.TGT_DOC_NUM) : `DocEntry ${esc(a.TGT_DOC_ENTRY)}`}</span>`;
    const note = lineNote(a, inv);
    html += `<tr><td><span class="tv-type ${esc(t)}">${esc(invTypeLabel(a))}</span></td><td>${doc}</td><td>${a.TGT_DATE ? dateCell(a.TGT_DATE) : `<span class="tv-muted">${isInv ? 'outside window' : 'n/a'}</span>`}</td>`;
    html += `<td class="tv-col-bill">${a.TGT_VENDOR_BILL ? `<strong>${esc(a.TGT_VENDOR_BILL)}</strong>` : `<span class="tv-muted">${isInv ? (inWin ? '(none)' : 'outside window') : 'n/a'}</span>`}</td>`;
    html += `<td class="num">${isInv ? (isNil(a.TGT_GROSS) ? nc('invoice outside the fetched window') : amt(a.TGT_GROSS)) : (isNil(a.TGT_GROSS) ? '<span class="tv-muted">n/a</span>' : amt(a.TGT_GROSS))}</td>`;
    html += `<td class="num">${isInv ? (isNil(a.TGT_TDS) ? nc('invoice outside the fetched window') : amt(a.TGT_TDS)) : '<span class="tv-muted">n/a</span>'}</td>`;
    html += `<td class="num"><strong>${amt(a.SUM_APPLIED, 'VPM2.SumApplied missing')}</strong></td><td class="tv-note">${note}</td></tr>`;
  }
  html += `</tbody><tfoot><tr class="tv-total"><td colspan="6">${lines.length} line${lines.length === 1 ? '' : 's'} · payment total ${amt(p.PAY_TOTAL)}</td><td class="num">${amt(sum)}</td><td class="tv-note">${lineSumNote(p, sum)}</td></tr></tfoot></table>`;
  if (!compact && p.REMARKS) html += `<div class="tv-remarks">Remarks: ${esc(p.REMARKS)}</div>`;
  html += `</div>`;
  return html;
}

function lineNote(a, inv) {
  const t = String(a.INV_TYPE);
  const applied = Number(a.SUM_APPLIED || 0);
  if (t === '18') {
    if (isNil(a.TGT_GROSS)) return `<span class="tv-muted">bill itself not fetched</span>`;
    const gross = Number(a.TGT_GROSS), tds = Number(a.TGT_TDS || 0);
    if (Math.abs(applied - gross) <= 1) return tds > 0 ? `<span class="tv-warntext">full gross paid — TDS ${inr(tds)} not deducted here</span>` : `<span class="tv-oktext">full amount</span>`;
    if (Math.abs(applied - (gross - tds)) <= 1) return `<span class="tv-oktext">gross − TDS</span>`;
    if (applied < gross - tds) return `<span class="tv-warntext">short by ${inr(gross - tds - applied)} vs gross − TDS</span>`;
    if (applied > gross + 1) return `<span class="tv-dangertext">above the bill by ${inr(applied - gross)}</span>`;
    return `<span class="tv-warntext">deducted ${inr(gross - applied)} of TDS ${inr(tds)}</span>`;
  }
  if (t === '19') return `<span class="tv-muted">credit note — reduces what is owed; SAP stores it positive</span>`;
  if (t === '30') return `<span class="tv-onacct">settled by journal entry${applied < 0 ? ' (negative line)' : ''}</span>`;
  if (t === '46') return `<span class="tv-onacct">earlier on-account payment consumed${applied < 0 ? ' (negative, as SAP stores it)' : ''}</span>`;
  return `<span class="tv-muted">contra / uncommon line type — shown, not dropped</span>`;
}

function lineSumNote(p, sum) {
  const tot = Number(p.PAY_TOTAL || 0);
  if (Math.abs(sum - tot) <= 1) return `<span class="tv-oktext">lines = payment</span>`;
  const n = paymentNets(p);
  if (Number(p.CN_APPLIED) > 0 && n.ties) return `<span class="tv-oktext" title="${esc(PAY_NETS.hint)}">nets with the credit-note sign flipped</span>`;
  return `<span class="tv-warntext">lines ${sum > tot ? 'exceed' : 'fall short of'} the payment by ${inr(Math.abs(sum - tot))}</span>`;
}

/* ═══════════════════════════ 4. DRAWER ═════════════════════════════════ */

let drawerEl = null;
let drawerCtx = null;
let lastFocus = null;

function ensureDrawer() {
  if (drawerEl && document.body.contains(drawerEl)) return drawerEl;
  injectCss();
  drawerEl = document.createElement('div');
  drawerEl.className = 'tv tv-drawer-root';
  drawerEl.innerHTML = `<div class="tv-backdrop" data-close></div><aside class="tv-drawer" role="dialog" aria-modal="true" aria-labelledby="tv-drawer-title" tabindex="-1"><div class="tv-drawer-bar"><div class="tv-drawer-heading"><div class="tv-kicker" data-kicker></div><h2 id="tv-drawer-title" data-title></h2></div><button type="button" class="tv-close" data-close aria-label="Close">×</button></div><div class="tv-drawer-body" data-body></div></aside>`;
  document.body.appendChild(drawerEl);
  drawerEl.addEventListener('click', (ev) => {
    const t = ev.target.closest('[data-close],[data-open-inv],[data-open-pay],[data-select-vendor]');
    if (!t) return;
    if (t.hasAttribute('data-close')) { closeDrawer(); return; }
    if (t.hasAttribute('data-open-inv')) { emit(document, 'transporter:open', { kind: 'invoice', docEntry: t.getAttribute('data-open-inv') }); openDrawer('invoice', t.getAttribute('data-open-inv'), drawerCtx); return; }
    if (t.hasAttribute('data-open-pay')) { emit(document, 'transporter:open', { kind: 'payment', docEntry: t.getAttribute('data-open-pay') }); openDrawer('payment', t.getAttribute('data-open-pay'), drawerCtx); return; }
    if (t.hasAttribute('data-select-vendor')) {
      const code = t.getAttribute('data-select-vendor');
      if (drawerCtx && typeof drawerCtx.onSelectVendor === 'function') drawerCtx.onSelectVendor(code, null);
      document.dispatchEvent(new CustomEvent('transporter:select-vendor', { detail: { cardCode: code, row: null }, bubbles: true }));
      closeDrawer();
    }
  });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && drawerEl && drawerEl.classList.contains('is-open')) closeDrawer(); });
  return drawerEl;
}

export function closeDrawer() {
  if (!drawerEl) return;
  drawerEl.classList.remove('is-open');
  drawerEl.setAttribute('aria-hidden', 'true');
  if (lastFocus && typeof lastFocus.focus === 'function') { try { lastFocus.focus(); } catch (e) { /* gone */ } }
  lastFocus = null;
}

export function openDrawer(kind, docEntry, ctx) {
  const R = readCtx(ctx);
  drawerCtx = ctx;
  const el = ensureDrawer();
  el.style.setProperty('--tv-accent', R.accent);
  el.setAttribute('data-company', R.co);
  const body = el.querySelector('[data-body]');
  const title = el.querySelector('[data-title]');
  const kicker = el.querySelector('[data-kicker]');
  const key = String(docEntry);
  const k = String(kind || '').toLowerCase();

  if (!el.classList.contains('is-open')) lastFocus = document.activeElement;

  if (k.startsWith('inv')) {
    const r = R.invByEntry.get(key);
    kicker.textContent = `A/P invoice · ${R.label}`;
    if (!r) {
      const refs = R.allocByInv.get(key) || [];
      title.textContent = `Invoice DocEntry ${key}`;
      body.innerHTML = invoiceMissing(R, key, refs);
    } else {
      title.textContent = `${r.DOC_NUM} · bill ${r.VENDOR_BILL || '(none)'}`;
      body.innerHTML = invoiceDrawer(R, r);
    }
  } else if (k.startsWith('pay')) {
    const p = R.payByEntry.get(key);
    kicker.textContent = `Outgoing payment · ${R.label}`;
    if (!p) {
      title.textContent = `Payment DocEntry ${key}`;
      body.innerHTML = emptyState('Payment not in the fetched window', [
        `payments.${esc(R.co)}.json holds non-cancelled transporter payments dated from 1 Apr 2025; DocEntry ${esc(key)} is not among them. It is older, cancelled, or not a transporter payment.`,
      ]);
    } else {
      title.textContent = `${p.DOC_NUM} · ${inr(p.PAY_TOTAL, true)}`;
      body.innerHTML = paymentDrawer(R, p);
      mountMap(R, p, body.querySelector('[data-map]'));
    }
  } else {
    kicker.textContent = R.label;
    title.textContent = 'Unknown record kind';
    body.innerHTML = emptyState(`openDrawer("${esc(kind)}") is not a kind this drawer knows`, ['Use "invoice" or "payment".']);
  }
  el.classList.add('is-open');
  el.removeAttribute('aria-hidden');
  const panel = el.querySelector('.tv-drawer');
  panel.scrollTop = 0;
  try { el.querySelector('.tv-close').focus({ preventScroll: true }); } catch (e) { /* ok */ }
}

function kv(label, valueHtml, title) {
  return `<div class="tv-kv" ${title ? `title="${esc(title)}"` : ''}><dt>${esc(label)}</dt><dd>${valueHtml}</dd></div>`;
}

function invoiceDrawer(R, r) {
  const st = invoiceStatus(r);
  const sb = settledBy(r);
  const lines = R.allocByInv.get(String(r.DOC_ENTRY)) || [];
  const gross = Number(r.GROSS || 0), tds = Number(r.TDS || 0), disc = Number(r.DISCOUNT || 0), net = Number(r.NET_PAID || 0);
  const paid = Number(r.PAY_CNT) > 0;
  let html = '';
  html += `<section class="tv-sec"><div class="tv-bill-hero"><div class="tv-label">Vendor bill</div><div class="tv-bill-big">${esc(r.VENDOR_BILL || '(none)')}</div><div class="tv-muted">${esc(r.CARD_NAME)} · <button type="button" class="tv-doclink" data-select-vendor="${esc(r.CARD_CODE)}" title="Select this transporter on the board">${esc(r.CARD_CODE)}</button></div></div>`;
  html += `<dl class="tv-kvs">${kv('SAP DocNum', esc(r.DOC_NUM))}${kv('DocEntry', esc(r.DOC_ENTRY))}${kv('Doc date', dateCell(r.DOC_DATE))}${kv('Tax date', dateCell(r.TAX_DATE))}${kv('Due date', dateCell(r.DUE_DATE))}${kv('Branch', esc(r.BRANCH || '(no branch)'))}${kv('Status', chip(st))}${kv('SAP DocStatus', `<code>${esc(r.DOC_STATUS || '?')}</code> <span class="tv-muted">unreliable at JIVO (C-0019) — a bill settled by journal stays O; age from the money</span>`)}</dl></section>`;

  html += `<section class="tv-sec"><h3>Reconciliation</h3><table class="tv-table tv-recon"><tbody>`;
  html += `<tr><td>Gross <span class="tv-muted">OPCH.DocTotal</span></td><td class="num">${amt(r.GROSS, 'DocTotal missing', true)}</td><td class="tv-note">${isNil(r.VAT) ? '' : `incl. GST ${inr(r.VAT, true)} · base ${inr(r.BASE, true)}`}</td></tr>`;
  html += `<tr><td>− TDS on bill <span class="tv-muted">OPCH.WTSum</span></td><td class="num">${amt(r.TDS, 'WTSum missing', true)}</td><td class="tv-note">${isNil(r.TDS_APPLIED) ? '' : `WTApplied = ${inr(r.TDS_APPLIED, true)} (cross-check, not the headline)`}</td></tr>`;
  html += `<tr><td>− Discount <span class="tv-muted">OPCH.DiscSum</span></td><td class="num">${amt(r.DISCOUNT, 'DiscSum missing', true)}</td><td class="tv-note"></td></tr>`;
  html += `<tr><td>− Other deduction <span class="tv-muted">residual</span></td><td class="num">${isNil(r.OTHER_DEDUCTION) ? nc('no payment applied — a residual against nothing is meaningless') : amt(r.OTHER_DEDUCTION, '', true)}</td><td class="tv-note">unexplained — shortage/damage claim or settled by journal</td></tr>`;
  html += `<tr class="tv-total"><td>= Net paid <span class="tv-muted">Σ VPM2.SumApplied</span></td><td class="num">${paid ? amt(r.NET_PAID, 'NET_PAID missing', true) : `<span class="tv-muted">${inr(0, true)} · no payment line</span>`}</td><td class="tv-note">${paid ? `${count(r.PAY_CNT)} payment${Number(r.PAY_CNT) === 1 ? '' : 's'}` : ''}</td></tr>`;
  html += `</tbody></table>`;
  html += `<div class="tv-callout ${st.tone}">${tdsBehaviour(r, st, gross, tds, disc, net)}</div>`;
  const ptd = isNil(r.PAID_TO_DATE) ? null : Number(r.PAID_TO_DATE);
  html += `<dl class="tv-kvs">${kv('SAP PaidToDate', ptd === null ? nc('PaidToDate missing') : amt(ptd, '', true), 'OPCH.PaidToDate — updated by payments AND by internal reconciliation (journal / credit note / on-account matched later)')}${kv('Settled by', `<span class="tv-settled ${sb.tone}">${esc(sb.text)}</span><div class="tv-muted tv-small">${esc(sb.title)}</div>`)}</dl></section>`;

  html += `<section class="tv-sec"><h3>Payments applied to this bill</h3>`;
  if (!lines.length) {
    if (paid) html += `<div class="tv-panel warn">The invoice row counts ${count(r.PAY_CNT)} payment${Number(r.PAY_CNT) === 1 ? '' : 's'} (${esc(r.PAY_NUMS)}) but allocations.${esc(R.co)}.json has no InvType-18 line for DocEntry ${esc(r.DOC_ENTRY)} — ${R.allocations.loaded ? 'the files were not built from the same run, or the payment is dated before 1 Apr 2025 (allocations are fetched by payment date)' : 'the allocations file did not load'}. Payment numbers: ${payNumChips(R, null, r)}</div>`;
    else html += `<div class="tv-panel">No outgoing payment carries a line against this bill.${ptd !== null && ptd > 0 ? ` SAP nevertheless shows PaidToDate ${inr(ptd, true)} — it was closed by reconciliation (journal / credit note / on-account payment matched later), which VPM2 cannot show per bill.` : ' PaidToDate is 0 — untouched.'}</div>`;
  } else {
    html += `<table class="tv-table tv-lines"><thead><tr><th>Payment</th><th>Date</th><th class="num">Applied</th><th class="num">Payment total</th><th>Match</th></tr></thead><tbody>`;
    for (const a of lines) {
      const p = R.payByEntry.get(String(a.PAY_DOC_ENTRY));
      html += `<tr><td><button type="button" class="tv-doclink" data-open-pay="${esc(a.PAY_DOC_ENTRY)}">${esc(a.PAY_DOC_NUM)}</button></td><td>${dateCell(a.PAY_DATE)}</td><td class="num"><strong>${amt(a.SUM_APPLIED, 'SumApplied missing', true)}</strong></td><td class="num">${p ? amt(p.PAY_TOTAL, '', true) : nc('payment not in payments file')}</td><td>${p ? chip(paymentStatus(p)) : '<span class="tv-muted" title="payment dated before 1 Apr 2025 — not in the payments file">not in file</span>'}</td></tr>`;
    }
    html += `</tbody></table>`;
  }
  html += `</section>`;
  return html;
}

function tdsBehaviour(r, st, gross, tds, disc, net) {
  const f = String(r.RESIDUAL_FLAG || '');
  const wt = isNil(r.TDS_APPLIED) ? null : Number(r.TDS_APPLIED);
  const ptd = isNil(r.PAID_TO_DATE) ? null : Number(r.PAID_TO_DATE);
  if (f === 'UNPAID') {
    if (ptd !== null && ptd > 0) return `<strong>Settled without a payment line.</strong> No outgoing payment applies to this bill, yet SAP PaidToDate = ${inr(ptd, true)}. It was closed by internal reconciliation — a journal, a credit note, or an on-account payment matched later. Not unpaid in the cash sense.`;
    return `<strong>Untouched.</strong> No payment line and PaidToDate = 0. Whether it is overdue is a question for the due date (${localDate(r.DUE_DATE) || 'not set'}), not DocStatus.`;
  }
  if (f === 'OK') return tds > 0
    ? `<strong>TDS withheld at payment.</strong> Net paid ${inr(net, true)} ≈ gross ${inr(gross, true)} − TDS ${inr(tds, true)}${disc ? ` − discount ${inr(disc, true)}` : ''}. Reconciles within ₹1.`
    : `<strong>Reconciles.</strong> No TDS on this bill — paid in full: net paid ${inr(net, true)} ≈ gross ${inr(gross, true)}${disc ? ` − discount ${inr(disc, true)}` : ''}.`;
  if (f === 'GROSS_PAID') return `<strong>Paid in full — TDS on the bill was not deducted at payment.</strong> Net paid ${inr(net, true)} equals the gross. The bill carries TDS ${inr(tds, true)} (WTSum) but SAP's WTApplied is ${wt === null ? 'not in the file' : inr(wt, true)}${wt === 0 ? ' — a field value in the books, not an inference' : wt !== null && wt !== 0 ? ' — note: non-zero on this row, unlike the pattern' : ''}. This is a TDS-compliance question, not an overpayment.`;
  if (f === 'SHORT') return `<strong>Short-paid.</strong> Net paid ${inr(net, true)} is ${inr(gross - tds - disc - net, true)} less than gross − TDS${disc ? ' − discount' : ''} (${inr(gross - tds - disc, true)}). The gap is unexplained — shortage/damage claim or settled by journal. Flagged for a look.`;
  if (f === 'OVER') return `<strong>Paid above the bill.</strong> Net paid ${inr(net, true)} exceeds gross ${inr(gross, true)} by ${inr(net - gross, true)}. Genuine over-payment — check the payment.`;
  if (f === 'PART_TDS') return `<strong>Part of the TDS deducted.</strong> ${inr(gross - net, true)} was held back at payment against TDS ${inr(tds, true)} on the bill — ${inr(tds - (gross - net), true)} less than the TDS. WTApplied = ${wt === null ? 'not in the file' : inr(wt, true)}.`;
  return `RESIDUAL_FLAG <code>${esc(f || 'blank')}</code> is not in the documented vocabulary — the row is shown raw.`;
}

function invoiceMissing(R, key, refs) {
  let html = emptyState('Invoice outside the fetched window', [
    `invoices.${esc(R.co)}.json holds non-cancelled transporter A/P invoices dated from 1 Apr 2025; DocEntry ${esc(key)} is not among them — it is older, cancelled, or belongs to a non-transporter card. Its gross and TDS are therefore ${nc('invoice row not fetched')}.`,
  ]);
  if (refs.length) {
    html += `<section class="tv-sec"><h3>Payments that apply to it</h3><table class="tv-table tv-lines"><thead><tr><th>Payment</th><th>Date</th><th>Transporter</th><th class="num">Applied</th></tr></thead><tbody>`;
    for (const a of refs) html += `<tr><td><button type="button" class="tv-doclink" data-open-pay="${esc(a.PAY_DOC_ENTRY)}">${esc(a.PAY_DOC_NUM)}</button></td><td>${dateCell(a.PAY_DATE)}</td><td>${esc(a.CARD_NAME)}</td><td class="num"><strong>${amt(a.SUM_APPLIED, '', true)}</strong></td></tr>`;
    html += `</tbody></table></section>`;
  }
  return html;
}

function paymentDrawer(R, p) {
  const st = paymentStatus(p);
  const mode = payMode(p);
  const n = paymentNets(p);
  let html = '';
  html += `<section class="tv-sec"><dl class="tv-kvs">${kv('Transporter', `${esc(p.CARD_NAME)} · <button type="button" class="tv-doclink" data-select-vendor="${esc(p.CARD_CODE)}" title="Select this transporter on the board">${esc(p.CARD_CODE)}</button>`)}${kv('SAP DocNum', esc(p.DOC_NUM))}${kv('DocEntry', esc(p.DOC_ENTRY))}${kv('Date', dateCell(p.DOC_DATE))}${kv('Total', `<strong>${amt(p.PAY_TOTAL, 'DocTotal missing', true)}</strong>`)}${kv('How paid', `${esc(mode.mode)} <span class="tv-muted">· ${mode.ref ? 'ref ' + esc(mode.ref) : 'ref not recorded'}${p.TRSFR_DATE ? ' · value date ' + esc(localDate(p.TRSFR_DATE)) : ''}</span>`, mode.title)}${kv('Split', `cash ${inr(p.CASH_SUM || 0, true)} · cheque ${inr(p.CHECK_SUM || 0, true)} · transfer ${inr(p.TRSFR_SUM || 0, true)}`)}${kv('Match', chip(st))}${p.REMARKS ? kv('Remarks', esc(p.REMARKS)) : ''}</dl></section>`;

  html += `<section class="tv-sec"><h3>Allocation summary</h3><table class="tv-table tv-recon"><tbody>`;
  html += `<tr><td>Applied to A/P invoices <span class="tv-muted">InvType 18</span></td><td class="num">${amt(p.INV_APPLIED, '', true)}</td><td class="tv-note">${count(p.INV_CNT)} bill${Number(p.INV_CNT) === 1 ? '' : 's'}</td></tr>`;
  html += `<tr><td>A/P credit notes <span class="tv-muted">InvType 19</span></td><td class="num">${amt(p.CN_APPLIED, '', true)}</td><td class="tv-note">${Number(p.CN_APPLIED) > 0 ? 'stored positive by SAP; reduces what the payment covers' : ''}</td></tr>`;
  html += `<tr><td>Journal entries <span class="tv-muted">InvType 30</span></td><td class="num">${amt(p.JE_APPLIED, '', true)}</td><td class="tv-note">${Number(p.JE_APPLIED) !== 0 ? 'settled by journal' : ''}</td></tr>`;
  html += `<tr><td>Other lines <span class="tv-muted">46 on-account applied, 24/13/14 contra</span></td><td class="num">${amt(p.OTHER_APPLIED, '', true)}</td><td class="tv-note">${Number(p.OTHER_APPLIED) < 0 ? 'negative = an earlier on-account payment consumed' : ''}</td></tr>`;
  html += `<tr class="tv-total"><td>= Applied, all lines</td><td class="num">${amt(p.ALLOC_TOTAL, '', true)}</td><td class="tv-note">${count(p.ALLOC_CNT)} line${Number(p.ALLOC_CNT) === 1 ? '' : 's'}</td></tr>`;
  html += `<tr><td>Unallocated <span class="tv-muted">total − applied</span></td><td class="num">${String(p.MATCH_FLAG) === 'ON_ACCOUNT' ? `<span class="tv-onacct">${amt(p.PAY_TOTAL, '', true)}</span>` : amt(p.UNALLOCATED, '', true)}</td><td class="tv-note">${st === PAY_NETS ? `netted (inv − CN + JE + other) = ${inr(n.net, true)} = total` : (String(p.MATCH_FLAG) === 'ON_ACCOUNT' ? 'paid against no bill — on account' : (Math.abs(Number(p.UNALLOCATED)) <= 1 ? 'ties' : 'does not tie'))}</td></tr>`;
  html += `</tbody></table>`;
  if (String(p.MATCH_FLAG) === 'ON_ACCOUNT') html += `<div class="tv-callout onacct"><strong>Paid, not yet matched to a bill.</strong> ${amt(p.PAY_TOTAL, '', true)} went to ${esc(p.CARD_NAME)} with no VPM2 line. It sits on account until Accounts reconciles it against bills — this is the bucket that causes repeated searching.</div>`;
  else if (st === PAY_NETS) html += `<div class="tv-callout ok"><strong>Nets exactly.</strong> ${PAY_NETS.hint}</div>`;
  else if (String(p.MATCH_FLAG) === 'PARTIAL') html += `<div class="tv-callout warn"><strong>Does not tie.</strong> Lines ${Number(p.UNALLOCATED) < 0 ? 'exceed' : 'fall short of'} the payment by ${inr(Math.abs(Number(p.UNALLOCATED)), true)}. Needs a look.</div>`;
  html += `</section>`;

  html += `<section class="tv-sec"><h3>Mapping — what this payment settled</h3><div class="tv-map" data-map></div>${allocationPanel(R, p, false)}</section>`;
  return html;
}

/* mapping.js draws the payment → document picture:
     renderPaymentMap(container, ctx)  with ctx.payment = row | DOC_ENTRY | DOC_NUM,
     data as rows or {rows}, company / cardCode / fy / asOf, and
     onSelect({kind, docEntry, docNum, id}) when a node is clicked.
   Called defensively: the line table already rendered underneath is the
   complete mapping if the module is absent, throws, or draws nothing. */
function mountMap(R, p, el) {
  if (!el) return;
  const fn = mapping && typeof mapping.renderPaymentMap === 'function' ? mapping.renderPaymentMap : null;
  if (!fn) { el.innerHTML = `<div class="tv-muted tv-small">mapping.js has no renderPaymentMap — the allocation lines below are the complete mapping.</div>`; return; }
  const std = R.period.key === 'FY26' || R.period.key === 'FY25' || R.period.key === 'ALL';
  const richCtx = Object.assign({}, R.ctx || {}, {
    company: R.co,
    cardCode: p.CARD_CODE, cardName: p.CARD_NAME,
    invoices: R.invoices.rows, payments: R.payments.rows, allocations: R.allocations.rows,
    fy: std ? R.period.key : undefined,
    dateFrom: std ? undefined : (R.period.from || undefined), dateTo: std ? undefined : (R.period.to || undefined),
    asOf: R.asOf || undefined,
    payment: p, docEntry: String(p.DOC_ENTRY), payDocEntry: String(p.DOC_ENTRY),
    onSelect: (sel) => {
      if (!sel || !sel.docEntry) return;
      const k = String(sel.kind || '');
      if (k === 'invoice') openDrawer('invoice', sel.docEntry, drawerCtx);
      else if (k === 'payment' || k === 'onaccount') openDrawer('payment', sel.docEntry, drawerCtx);
      // creditnote / journal / other: no record of their own on this board — the line table below carries them
    },
  });
  const note = (why) => { el.innerHTML = `<div class="tv-muted tv-small">${esc(why)} — the allocation lines below are the complete mapping.</div>`; };
  try {
    const r = fn(el, richCtx);
    if (r && typeof r.then === 'function') {
      r.then(() => { if (!el.childNodes.length) note('mapping.js drew nothing for this payment'); })
       .catch((e) => { console.warn('[views] renderPaymentMap rejected', e); note('mapping.js failed on this payment'); });
    } else if (!el.childNodes.length) {
      note('mapping.js drew nothing for this payment');
    }
  } catch (e) {
    console.warn('[views] renderPaymentMap threw', e);
    note('mapping.js failed on this payment');
  }
}

/* ═══════════════════════════ 5. FLAGS ══════════════════════════════════ */

const FLAG_BUCKETS = [
  { id: 'SHORT',      kind: 'invoice', meta: INV_FLAG.SHORT,      what: 'Short-paid bills' },
  { id: 'GROSS_PAID', kind: 'invoice', meta: INV_FLAG.GROSS_PAID, what: 'Gross paid, TDS not deducted' },
  { id: 'PART_TDS',   kind: 'invoice', meta: INV_FLAG.PART_TDS,   what: 'Part TDS deducted' },
  { id: 'OVER',       kind: 'invoice', meta: INV_FLAG.OVER,       what: 'Over-paid bills' },
  { id: 'ON_ACCOUNT', kind: 'payment', meta: PAY_FLAG.ON_ACCOUNT, what: 'Payments on account' },
  { id: 'PARTIAL',    kind: 'payment', meta: PAY_FLAG.PARTIAL,    what: 'Payments that do not tie' },
];

export function renderFlags(container, ctx) {
  const R = readCtx(ctx);
  const state = stateOf(container, 'flags', R.co);
  state.ctx = ctx;
  bind(container);
  adoptFlag(state, ctx);

  const problem = loadProblem(R, R.invoices, 'invoices') || loadProblem(R, R.payments, 'payments');
  if (problem) { container.innerHTML = rootOpen(R, 'tv-flags') + problem + '</div>'; return; }

  const items = [];
  for (const r of R.invoices.rows) {
    if (R.vendor && r.CARD_CODE !== R.vendor) continue;
    if (!inPeriod(r.DOC_DATE, R.period)) continue;
    const f = String(r.RESIDUAL_FLAG || '');
    if (f === 'OK' || f === 'UNPAID') continue;
    const bucket = FLAG_BUCKETS.find(b => b.id === f) || { id: f, kind: 'invoice', meta: invoiceStatus(r), what: 'Unknown flag' };
    const gross = Number(r.GROSS || 0), tds = Number(r.TDS || 0), net = Number(r.NET_PAID || 0), other = isNil(r.OTHER_DEDUCTION) ? null : Number(r.OTHER_DEDUCTION);
    let detail, stake;
    if (f === 'SHORT') {
      const ptd = isNil(r.PAID_TO_DATE) ? null : Number(r.PAID_TO_DATE);
      const covered = other !== null && ptd !== null ? Math.max(0, Math.min(other, ptd - net)) : 0;
      stake = other === null ? null : other - covered;
      detail = `gap ${inr(other)} below gross − TDS` + (covered > 1 ? ` · SAP PaidToDate covers ${inr(covered)} (reconciliation) · ${inr(other - covered)} unexplained` : ', unexplained');
    }
    else if (f === 'GROSS_PAID') { stake = tds; detail = `TDS ${inr(tds)} on the bill not deducted at payment (WTApplied ${isNil(r.TDS_APPLIED) ? '?' : inr(r.TDS_APPLIED)})`; }
    else if (f === 'OVER') { stake = net - gross; detail = `paid ${inr(net - gross)} above the bill`; }
    else if (f === 'PART_TDS') { stake = tds - (gross - net); detail = `deducted ${inr(gross - net)} of TDS ${inr(tds)} — ${inr(tds - (gross - net))} less`; }
    else { stake = other; detail = `residual ${other === null ? 'not computed' : inr(other)}`; }
    items.push({ bucket: bucket.id, kind: 'invoice', meta: bucket.meta, date: r.DOC_DATE, docEntry: r.DOC_ENTRY, docNum: r.DOC_NUM, bill: r.VENDOR_BILL || '(none)', card: r.CARD_CODE, name: r.CARD_NAME, amount: gross, stake, detail, pays: r.PAY_NUMS });
  }
  for (const p of R.payments.rows) {
    if (R.vendor && p.CARD_CODE !== R.vendor) continue;
    if (!inPeriod(p.DOC_DATE, R.period)) continue;
    const f = String(p.MATCH_FLAG || '');
    if (f === 'MATCHED') continue;
    const st = paymentStatus(p);
    if (st === PAY_NETS) continue;   // nets exactly — nothing to chase
    const bucket = FLAG_BUCKETS.find(b => b.id === f) || { id: f, kind: 'payment', meta: st, what: 'Unknown flag' };
    let detail, stake;
    if (f === 'ON_ACCOUNT') { stake = Number(p.PAY_TOTAL || 0); detail = `${inr(stake)} paid against no bill — not yet matched`; }
    else { stake = Number(p.UNALLOCATED || 0); detail = `lines ${stake < 0 ? 'exceed' : 'fall short of'} the payment by ${inr(Math.abs(stake))}`; }
    items.push({ bucket: bucket.id, kind: 'payment', meta: bucket.meta, date: p.DOC_DATE, docEntry: p.DOC_ENTRY, docNum: p.DOC_NUM, bill: '', card: p.CARD_CODE, name: p.CARD_NAME, amount: Number(p.PAY_TOTAL || 0), stake, detail, pays: '' });
  }

  const counts = {};
  for (const it of items) { const c = counts[it.bucket] || (counts[it.bucket] = { n: 0, stake: 0 }); c.n += 1; c.stake += Math.abs(Number(it.stake || 0)); }
  const filter = state.flagFilter || 'ALL';
  const shown = (filter === 'ALL' ? items : items.filter(i => i.bucket === filter)).sort((a, b) => (b.date || '').localeCompare(a.date || '') || String(b.docNum).localeCompare(String(a.docNum)));

  let html = rootOpen(R, 'tv-flags');
  html += `<div class="tv-bar"><div class="tv-kicker">Needs a look · ${esc(R.label)} · ${esc(R.period.label)} ${vendorHeading(R)}</div></div>`;
  html += `<div class="tv-chips" role="tablist">`;
  html += `<button type="button" class="tv-fchip${filter === 'ALL' ? ' is-on' : ''}" data-flag="ALL" role="tab" aria-selected="${filter === 'ALL'}">All <span class="tv-n">${items.length}</span></button>`;
  for (const b of FLAG_BUCKETS) {
    const c = counts[b.id];
    html += `<button type="button" class="tv-fchip ${b.meta.tone}${filter === b.id ? ' is-on' : ''}" data-flag="${esc(b.id)}" role="tab" aria-selected="${filter === b.id}" title="${esc(b.meta.hint)}">${esc(b.what)} <span class="tv-n">${c ? c.n : 0}</span>${c && c.stake ? `<span class="tv-stake">${inr(c.stake)}</span>` : ''}</button>`;
  }
  for (const id of Object.keys(counts)) if (!FLAG_BUCKETS.some(b => b.id === id)) html += `<button type="button" class="tv-fchip neutral${filter === id ? ' is-on' : ''}" data-flag="${esc(id)}" role="tab">${esc(id)} <span class="tv-n">${counts[id].n}</span></button>`;
  html += `</div>`;

  if (!items.length) {
    const invN = R.invoices.rows.filter(r => (!R.vendor || r.CARD_CODE === R.vendor) && inPeriod(r.DOC_DATE, R.period)).length;
    const payN = R.payments.rows.filter(p => (!R.vendor || p.CARD_CODE === R.vendor) && inPeriod(p.DOC_DATE, R.period)).length;
    html += emptyState('Nothing flagged', [
      (invN || payN) ? `${invN} invoice${invN === 1 ? '' : 's'} and ${payN} payment${payN === 1 ? '' : 's'} in view; every paid bill reconciles (OK) or is simply unpaid, and every payment is matched or nets.` : `No invoice or payment is in view for ${esc(R.period.label)}${R.vendor ? ' for this transporter' : ''} — so there is nothing to flag, not a clean bill of health.`,
    ]) + '</div>';
    container.innerHTML = html;
    return;
  }
  if (!shown.length) {
    html += emptyState('Nothing in this bucket', [`${items.length} item${items.length === 1 ? '' : 's'} are flagged in other buckets — pick another chip or “All”.`]) + '</div>';
    container.innerHTML = html;
    return;
  }

  html += `<div class="tblbox tv-tblbox"><table class="tv-table tv-flagtable"><thead><tr><th>Date</th><th>Kind</th><th>DocNum</th><th class="tv-col-bill">Vendor bill</th><th class="tv-col-vendor">Transporter</th><th class="num">Amount</th><th>Issue</th><th class="num">At stake</th><th>Detail</th></tr></thead><tbody>`;
  for (const it of shown) {
    const openAttr = it.kind === 'invoice' ? `data-open-inv="${esc(it.docEntry)}"` : `data-open-pay="${esc(it.docEntry)}"`;
    html += `<tr class="tv-row">`;
    html += `<td>${dateCell(it.date)}</td><td><span class="tv-muted">${it.kind === 'invoice' ? 'Invoice' : 'Payment'}</span></td>`;
    html += `<td><button type="button" class="tv-doclink" ${openAttr}>${esc(it.docNum)}</button></td>`;
    html += `<td class="tv-col-bill">${it.kind === 'invoice' ? `<button type="button" class="tv-bill" ${openAttr}>${esc(it.bill)}</button>` : '<span class="tv-muted" title="a payment has no vendor bill of its own">n/a</span>'}</td>`;
    html += `<td class="tv-col-vendor"><span class="tv-ellip" title="${esc(it.name + ' · ' + it.card)}">${esc(it.name)}</span></td>`;
    html += `<td class="num">${amt(it.amount)}</td><td>${chip(it.meta)}</td>`;
    html += `<td class="num">${it.stake === null || it.stake === undefined ? nc('residual not computed') : amt(it.stake)}</td>`;
    html += `<td class="tv-note">${esc(it.detail)}</td></tr>`;
  }
  html += `</tbody></table></div>`;
  html += totalsNote(shown.length, `${items.length} flagged in total · “Gross paid” is a TDS-compliance question, not an overpayment · “Nets (credit note)” payments are excluded because they tie exactly`);
  html += '</div>';
  container.innerHTML = html;
}

/* ═══════════════════════════ event binding ════════════════════════════ */

function rerender(container) {
  const s = STATE.get(container);
  if (!s) return;
  const fn = { vendors: renderVendorList, invoices: renderInvoices, payments: renderPayments, flags: renderFlags }[s.view];
  if (fn) fn(container, s.ctx);
}

function bind(container) {
  injectCss();
  const s = STATE.get(container);
  if (!s || s.bound) return;
  s.bound = true;

  container.addEventListener('click', (ev) => {
    const st = STATE.get(container);
    if (!st) return;
    const ctx = st.ctx;
    const sortBtn = ev.target.closest('[data-sort]');
    if (sortBtn && container.contains(sortBtn)) {
      const view = st.view;
      const cols = { vendors: VENDOR_COLS, invoices: INVOICE_COLS, payments: PAYMENT_COLS }[view] || [];
      const col = cols.find(c => c.key === sortBtn.getAttribute('data-sort'));
      toggleSort(st, view, sortBtn.getAttribute('data-sort'), col && !col.num ? 'asc' : 'desc');
      rerender(container);
      return;
    }
    const openInv = ev.target.closest('[data-open-inv]');
    if (openInv) { ev.stopPropagation(); doOpen(container, ctx, 'invoice', openInv.getAttribute('data-open-inv')); return; }
    const openPay = ev.target.closest('[data-open-pay]');
    if (openPay) { ev.stopPropagation(); doOpen(container, ctx, 'payment', openPay.getAttribute('data-open-pay')); return; }
    const clear = ev.target.closest('[data-clear-vendor]');
    if (clear) { selectVendor(container, ctx, null, null); return; }
    const flag = ev.target.closest('[data-flag]');
    if (flag) { st.flagFilter = flag.getAttribute('data-flag'); rerender(container); return; }
    const row = ev.target.closest('tr[data-card], tr[data-pay]');
    if (!row || !container.contains(row)) return;
    if (row.hasAttribute('data-card')) {
      const code = row.getAttribute('data-card');
      const cur = vendorOf(ctx);
      selectVendor(container, ctx, cur === code ? null : code, row);
      return;
    }
    if (row.hasAttribute('data-pay')) {
      const key = row.getAttribute('data-pay');
      if (st.expanded.has(key)) st.expanded.delete(key); else st.expanded.add(key);
      rerender(container);
    }
  });

  container.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Enter' && ev.key !== ' ') return;
    const row = ev.target.closest && ev.target.closest('tr[data-card], tr[data-pay]');
    if (!row || ev.target !== row) return;
    ev.preventDefault();
    row.click();
  });

  let timer = null;
  container.addEventListener('input', (ev) => {
    const inp = ev.target.closest && ev.target.closest('[data-search]');
    if (!inp) return;
    const st = STATE.get(container);
    if (!st) return;
    st.search = inp.value;
    clearTimeout(timer);
    timer = setTimeout(() => {
      const active = document.activeElement === inp;
      const pos = inp.selectionStart;
      rerender(container);
      if (active) { const again = container.querySelector('[data-search]'); if (again) { again.focus({ preventScroll: true }); try { again.setSelectionRange(pos, pos); } catch (e) { /* ok */ } } }
    }, 160);
  });
}

function selectVendor(container, ctx, code, row) {
  let masterRow = null;
  if (code) { const m = sectionOf(ctx, 'master'); masterRow = m.rows.find(r => r.CARD_CODE === code) || null; }
  // local highlight so the roster responds even if the shell does not re-render
  container.querySelectorAll('tr[data-card]').forEach(tr => {
    const on = code && tr.getAttribute('data-card') === code;
    tr.classList.toggle('is-selected', !!on);
    tr.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  emit(container, 'transporter:select-vendor', { cardCode: code, row: masterRow });
  if (ctx && typeof ctx.onSelectVendor === 'function') { try { ctx.onSelectVendor(code, masterRow); } catch (e) { console.warn('[views] onSelectVendor threw', e); } }
}

/* ═══════════════════════════ styles ═══════════════════════════════════ */

const CSS = `
.tv{--tv-bg:#f6f7f9;--tv-card:#ffffff;--tv-line:#e3e6ea;--tv-hair:#eaecf0;--tv-ink:#14181f;--tv-muted:#667085;
  --tv-ok:#067647;--tv-warn:#b54708;--tv-danger:#b42318;--tv-neutral:#475467;--tv-onacct:#6941c6;--tv-accent:#b45309;
  --tv-ok-bg:#ecfdf3;--tv-warn-bg:#fffaeb;--tv-danger-bg:#fef3f2;--tv-neutral-bg:#f2f4f7;--tv-onacct-bg:#f4f3ff;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--tv-ink);
  font-variant-numeric:tabular-nums;font-size:13px;line-height:1.35;min-width:0}
.tv *,.tv *::before,.tv *::after{box-sizing:border-box;min-width:0}
.tv code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;color:var(--tv-muted)}
.tv .tv-bar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 14px;margin:0 0 10px}
.tv .tv-bar-right{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.tv .tv-kicker{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--tv-muted);font-weight:600;display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px}
.tv .tv-label{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--tv-muted);font-weight:600}
.tv .tv-asof{font-weight:500;text-transform:none;letter-spacing:0}
.tv .tv-pill{display:inline-flex;align-items:center;gap:6px;padding:2px 8px;border:1px solid var(--tv-line);border-radius:999px;background:var(--tv-card);font-size:12px;text-transform:none;letter-spacing:0;color:var(--tv-ink);font-weight:600}
.tv .tv-pill.onacct{color:var(--tv-onacct);border-color:currentColor;background:var(--tv-onacct-bg)}
.tv .tv-btn{font:inherit;font-size:12px;font-weight:600;padding:5px 10px;border:1px solid var(--tv-line);border-radius:8px;background:var(--tv-card);color:var(--tv-ink);cursor:pointer}
.tv .tv-btn:hover{border-color:var(--tv-muted)}
.tv .tv-search{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--tv-muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600}
.tv .tv-search input{font:inherit;font-size:13px;text-transform:none;letter-spacing:0;font-weight:400;color:var(--tv-ink);background:var(--tv-card);border:1px solid var(--tv-line);border-radius:8px;padding:6px 10px;width:min(320px,70vw);outline:none}
.tv .tv-search input:focus{border-color:var(--tv-muted);box-shadow:0 0 0 3px rgba(16,24,40,.06)}
.tv .tblbox,.tv .tv-tblbox{overflow:auto;max-height:min(72vh,760px);max-width:100%;border:1px solid var(--tv-line);border-radius:10px;background:var(--tv-card);box-shadow:0 1px 2px rgba(16,24,40,.06);-webkit-overflow-scrolling:touch}
.tv .tv-table{border-collapse:separate;border-spacing:0;width:100%;font-size:13px;background:var(--tv-card)}
.tv .tv-table th{position:sticky;top:0;z-index:2;background:var(--tv-card);font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--tv-muted);font-weight:600;text-align:left;padding:0 10px;height:38px;border-bottom:1px solid var(--tv-line);white-space:nowrap;vertical-align:middle}
.tv .tv-table th small{display:block;font-size:10px;letter-spacing:.02em;text-transform:none;font-weight:500;opacity:.85;line-height:1}
.tv .tv-table td{height:34px;padding:0 10px;border-bottom:1px solid var(--tv-hair);white-space:nowrap;vertical-align:middle}
.tv .tv-table tbody tr:last-child td{border-bottom:0}
.tv .tv-table .num{text-align:right;font-variant-numeric:tabular-nums}
.tv .tv-table th.num .tv-sortbtn{justify-content:flex-end}
.tv .tv-sortbtn{font:inherit;text-transform:inherit;letter-spacing:inherit;color:inherit;font-weight:inherit;background:none;border:0;padding:0;cursor:pointer;display:inline-flex;align-items:center;gap:4px;width:100%;text-align:inherit}
.tv .tv-sortbtn:hover{color:var(--tv-ink)}
.tv th.is-sorted .tv-sortbtn{color:var(--tv-ink)}
.tv .tv-arrow{font-size:9px;width:9px;display:inline-block}
.tv .tv-row.is-select{cursor:pointer}
.tv .tv-row.is-select:hover td,.tv .tv-row.is-expandable:hover td{background:#fafbfc}
.tv .tv-row.is-selected td{background:#eef2f6;font-weight:600}
.tv .tv-row.is-selected td:first-child{box-shadow:inset 3px 0 0 var(--tv-ink)}
.tv .tv-row.is-select:focus-visible{outline:2px solid var(--tv-ink);outline-offset:-2px}
.tv .tv-row.is-expandable{cursor:pointer}
.tv .tv-row.is-open td{background:#fafbfc;border-bottom-color:transparent}
.tv .tv-col-exp{width:24px;padding-right:0}
.tv .tv-caret{color:var(--tv-muted);font-size:11px}
.tv .tv-subrow td{height:auto;padding:0 10px 12px;white-space:normal;background:#fafbfc}
.tv .tv-name{max-width:320px}
.tv .tv-vname{display:block;font-weight:600;overflow:hidden;text-overflow:ellipsis;line-height:1.15}
.tv .tv-vcode{display:block;font-size:11px;color:var(--tv-muted);line-height:1.1;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.tv .tv-col-vendor{max-width:210px}
.tv .tv-ellip{display:block;overflow:hidden;text-overflow:ellipsis;max-width:210px}
.tv .tv-srlabel{white-space:nowrap}
.tv .tv-col-bill{font-weight:700}
.tv .tv-bill{font:inherit;font-weight:700;font-size:13.5px;color:var(--tv-ink);background:var(--tv-neutral-bg);border:1px solid var(--tv-line);border-radius:6px;padding:2px 8px;cursor:pointer;letter-spacing:.01em}
.tv .tv-bill:hover{border-color:var(--tv-ink)}
.tv .tv-doclink{font:inherit;color:var(--tv-ink);background:none;border:0;padding:0;cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px;font-variant-numeric:tabular-nums}
.tv .tv-doclink:hover{text-decoration-style:solid}
.tv .tv-doclink.is-dead{color:var(--tv-muted);cursor:help;text-decoration-style:dashed}
.tv .tv-paynums{white-space:normal;max-width:220px;line-height:1.3}
.tv .tv-paynums .tv-doclink{margin-right:4px}
.tv .tv-sub{font-size:11px;color:var(--tv-muted)}
.tv .tv-small{font-size:11.5px}
.tv .tv-muted{color:var(--tv-muted)}
.tv .tv-neg{color:var(--tv-danger)}
.tv .tv-oktext{color:var(--tv-ok)}
.tv .tv-warntext{color:var(--tv-warn);font-weight:600}
.tv .tv-dangertext{color:var(--tv-danger);font-weight:600}
.tv .tv-onacct{color:var(--tv-onacct);font-weight:600}
.tv .tv-nc{color:var(--tv-muted);font-style:italic;font-size:12px;cursor:help;border-bottom:1px dotted var(--tv-muted)}
.tv .tv-chip{display:inline-flex;align-items:center;height:20px;padding:0 8px;border-radius:999px;font-size:11px;font-weight:600;letter-spacing:.01em;border:1px solid currentColor;white-space:nowrap;cursor:help;line-height:1}
.tv .tv-chip.ok{color:var(--tv-ok);background:var(--tv-ok-bg)}
.tv .tv-chip.warn{color:var(--tv-warn);background:var(--tv-warn-bg)}
.tv .tv-chip.danger{color:var(--tv-danger);background:var(--tv-danger-bg)}
.tv .tv-chip.neutral{color:var(--tv-neutral);background:var(--tv-neutral-bg)}
.tv .tv-chip.onacct{color:var(--tv-onacct);background:var(--tv-onacct-bg)}
.tv .tv-settled{font-size:12px;cursor:help}
.tv .tv-settled.onacct{color:var(--tv-onacct);font-weight:600}
.tv .tv-settled.muted{color:var(--tv-muted)}
.tv .tv-type{font-size:11px;font-weight:600;color:var(--tv-neutral)}
.tv .tv-type.\\31 8{color:var(--tv-ink)}
.tv .tv-type.\\33 0,.tv .tv-type.\\34 6{color:var(--tv-onacct)}
.tv .tv-type.\\31 9{color:var(--tv-warn)}
.tv .tv-total td{background:#fafbfc;font-weight:700;border-top:1px solid var(--tv-line);position:sticky;bottom:0;z-index:1}
.tv .tv-flagsum{font-weight:500;font-size:11.5px;color:var(--tv-muted);white-space:normal}
.tv .tv-foot{margin:8px 2px 0;font-size:11.5px;color:var(--tv-muted)}
.tv .tv-note{white-space:normal;font-size:12px;color:var(--tv-muted);max-width:360px}
.tv .tv-empty{border:1px dashed var(--tv-line);border-radius:10px;background:var(--tv-card);padding:18px 16px;color:var(--tv-muted);font-size:13px}
.tv .tv-empty-title{color:var(--tv-ink);font-weight:700;margin-bottom:4px}
.tv .tv-empty-line{margin-top:4px}
.tv .tv-panel{margin:8px 0 0;padding:10px 12px;border:1px solid var(--tv-line);border-radius:10px;background:var(--tv-card);font-size:12.5px;white-space:normal;overflow-x:auto}
.tv .tv-panel.onacct{border-color:var(--tv-onacct);background:var(--tv-onacct-bg);color:var(--tv-ink)}
.tv .tv-panel.warn{border-color:var(--tv-warn);background:var(--tv-warn-bg)}
.tv .tv-panel .tv-table{font-size:12.5px}
.tv .tv-panel .tv-table th{position:static;height:30px}
.tv .tv-panel .tv-table td{height:30px}
.tv .tv-panel .tv-total td{position:static}
.tv .tv-remarks{margin-top:8px;font-size:12px;color:var(--tv-muted)}
.tv .tv-chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.tv .tv-fchip{font:inherit;font-size:12px;font-weight:600;display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border:1px solid var(--tv-line);border-radius:999px;background:var(--tv-card);color:var(--tv-neutral);cursor:pointer}
.tv .tv-fchip.ok{color:var(--tv-ok)} .tv .tv-fchip.warn{color:var(--tv-warn)} .tv .tv-fchip.danger{color:var(--tv-danger)} .tv .tv-fchip.onacct{color:var(--tv-onacct)}
.tv .tv-fchip .tv-n{font-variant-numeric:tabular-nums;padding:0 6px;border-radius:999px;background:var(--tv-neutral-bg);color:var(--tv-ink);font-size:11px;line-height:16px}
.tv .tv-fchip .tv-stake{font-size:11px;font-weight:500;color:var(--tv-muted)}
.tv .tv-fchip.is-on{border-color:currentColor;box-shadow:inset 0 0 0 1px currentColor}
.tv .tv-fchip:hover{border-color:var(--tv-muted)}
/* drawer */
.tv-drawer-root{position:fixed;inset:0;z-index:1000;pointer-events:none;font-size:13px;overflow:hidden;visibility:hidden}
.tv-drawer-root.is-open{visibility:visible}
.tv-drawer-root .tv-backdrop{position:absolute;inset:0;background:rgba(16,24,40,.35);opacity:0;transition:opacity .18s}
.tv-drawer-root .tv-drawer{position:absolute;top:0;right:0;bottom:0;width:min(620px,100vw);background:var(--tv-card);border-left:1px solid var(--tv-line);box-shadow:-8px 0 24px rgba(16,24,40,.12);transform:translateX(100%);transition:transform .2s ease;display:flex;flex-direction:column;min-width:0;max-width:100vw}
.tv-drawer-root.is-open{pointer-events:auto}
.tv-drawer-root.is-open .tv-backdrop{opacity:1}
.tv-drawer-root.is-open .tv-drawer{transform:none}
.tv-drawer-root .tv-drawer-bar{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:14px 18px 12px;border-bottom:2px solid var(--tv-accent);background:var(--tv-card)}
.tv-drawer-root .tv-drawer-heading h2{margin:2px 0 0;font-size:17px;font-weight:700;line-height:1.25;overflow-wrap:anywhere}
.tv-drawer-root .tv-close{font:inherit;font-size:22px;line-height:1;width:34px;height:34px;border-radius:8px;border:1px solid var(--tv-line);background:var(--tv-card);color:var(--tv-muted);cursor:pointer;flex:0 0 auto}
.tv-drawer-root .tv-close:hover{color:var(--tv-ink);border-color:var(--tv-muted)}
.tv-drawer-root .tv-drawer-body{overflow:auto;padding:4px 18px 28px;flex:1 1 auto;min-width:0;background:var(--tv-bg)}
.tv .tv-sec{background:var(--tv-card);border:1px solid var(--tv-line);border-radius:10px;box-shadow:0 1px 2px rgba(16,24,40,.06);padding:12px 14px;margin:12px 0 0;min-width:0;overflow-x:auto}
.tv .tv-sec h3{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--tv-muted);font-weight:600}
.tv .tv-bill-hero{margin-bottom:10px}
.tv .tv-bill-big{font-size:22px;font-weight:800;letter-spacing:.01em;line-height:1.2;overflow-wrap:anywhere}
.tv .tv-kvs{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px 14px;margin:0}
.tv .tv-kv dt{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--tv-muted);font-weight:600;margin:0}
.tv .tv-kv dd{margin:2px 0 0;font-size:13px;font-weight:500;overflow-wrap:anywhere}
.tv .tv-recon td{white-space:normal}
.tv .tv-recon td:first-child{font-weight:500}
.tv .tv-recon .tv-total td{position:static}
.tv .tv-callout{margin:10px 0 12px;padding:10px 12px;border-radius:8px;border:1px solid var(--tv-line);background:var(--tv-neutral-bg);font-size:12.5px;line-height:1.45;white-space:normal}
.tv .tv-callout.ok{border-color:var(--tv-ok);background:var(--tv-ok-bg)}
.tv .tv-callout.warn{border-color:var(--tv-warn);background:var(--tv-warn-bg)}
.tv .tv-callout.danger{border-color:var(--tv-danger);background:var(--tv-danger-bg)}
.tv .tv-callout.onacct{border-color:var(--tv-onacct);background:var(--tv-onacct-bg)}
.tv .tv-map{min-width:0;overflow-x:auto;margin-bottom:6px}
.tv .tv-lines{font-size:12.5px}
.tv .tv-lines th{position:static;height:30px}
.tv .tv-lines td{height:30px}
@media (max-width:640px){
  .tv .tv-table td{height:32px;padding:0 8px}
  .tv .tv-table th{padding:0 8px}
  .tv .tv-name{max-width:190px}
  .tv .tv-vname{white-space:nowrap}
  .tv .tv-col-vendor,.tv .tv-ellip{max-width:160px}
  .tv .tv-tblbox{max-height:min(70vh,640px)}
  .tv .tv-search input{width:100%}
  .tv .tv-bar{align-items:stretch}
  .tv .tv-bar-right{width:100%}
  .tv .tv-search{width:100%}
  .tv .tv-kvs{grid-template-columns:repeat(2,minmax(0,1fr))}
  .tv-drawer-root .tv-drawer-body{padding:4px 10px 24px}
  .tv .tv-sec{padding:10px}
}
@media (prefers-reduced-motion:reduce){.tv-drawer-root .tv-drawer,.tv-drawer-root .tv-backdrop{transition:none}}
`;

let cssDone = false;
function injectCss() {
  if (cssDone) return;
  if (typeof document === 'undefined') return;
  if (document.getElementById('tv-views-css')) { cssDone = true; return; }
  const s = document.createElement('style');
  s.id = 'tv-views-css';
  s.textContent = CSS;
  document.head.appendChild(s);
  cssDone = true;
}
