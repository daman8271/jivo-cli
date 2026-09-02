/*
 * mapping.js — JIVO "Transporter-wise Details" board: THE MAPPING DIAGRAM
 * ---------------------------------------------------------------------------
 * Hand-written inline SVG. No library, no CDN, no build step. ES module.
 *
 *   renderMapping(container, ctx)     one transporter: bills <-> payments
 *   renderPaymentMap(container, ctx)  one payment: how it decomposed
 *   buildMappingModel(ctx)            the node/link model (exported for the
 *                                     page and for tests)
 *
 * Data contract (the REAL files in site/data/, all rows of one book):
 *   invoices.<co>.json    rows keyed DOC_ENTRY, one per A/P invoice (OPCH)
 *   payments.<co>.json    rows keyed DOC_ENTRY, one per outgoing payment (OVPM)
 *   allocations.<co>.json ONE ROW PER VPM2 LINE. (PAY_DOC_ENTRY, INV_TYPE,
 *                         TGT_DOC_ENTRY) is NOT unique (a JE settles several
 *                         lines). Rows are summed per link, never deduped.
 *   IN_WINDOW='N'  -> TGT_DOC_NUM/TGT_DATE/TGT_GROSS are null: the target is
 *                     a bill dated before 2025-04-01 (rendered "(invoice
 *                     outside window) DocEntry n") or a JE / consumed
 *                     on-account payment / contra line (rendered by type).
 *   SUM_APPLIED    -> negative on InvType 46 and on some 30. Real. Not abs()'d
 *                     for display; only the stroke WIDTH uses |amount|.
 *   OTHER_DEDUCTION-> a RESIDUAL (GROSS - TDS - DISCOUNT - NET_PAID). null on
 *                     every unpaid bill. Labelled "unexplained — shortage/
 *                     damage claim or settled by journal", never a known
 *                     deduction, never a confident zero.
 *
 * ctx for renderMapping — lenient on purpose, the page owns the data loading:
 *   {
 *     company:   'oil' | 'mart' | 'bev',         // accent colour only
 *     cardCode:  'VENDA000636',                  // the transporter (aliases: vendor, card)
 *     cardName?: 'DELHI PUNJAB TRANSPORT CO',
 *     invoices:  rows | {rows},                  // whole-book slices are fine —
 *     payments:  rows | {rows},                  // filtered by cardCode here
 *     allocations: rows | {rows},                // (or ctx.data = {invoices,…})
 *     fy?: 'FY26' | 'FY25' | 'ALL',              // view window; or dateFrom/dateTo
 *     asOf?: '2026-08-22',
 *     selected?: {kind, docEntry},               // initial pin
 *     onSelect?: (sel | null) => void            // sel = {kind, docEntry, docNum, id}
 *   }
 *   kind is one of 'invoice' | 'payment' | 'creditnote' | 'journal' |
 *   'onaccount' | 'other'. Returns a controller:
 *     { select({kind,docEntry}|id|null), clear(), destroy(), model }
 *   select() from the page does NOT echo onSelect back.
 *
 * ctx for renderPaymentMap: same data fields plus
 *   payment: row | DOC_ENTRY | DOC_NUM      (aliases: docEntry, payDocEntry)
 * Both renderers also accept the views.js call shape
 *   renderPaymentMap(el, String(DOC_ENTRY), ctx) / renderMapping(el, cardCode, ctx)
 * and resolve the vendor from ctx.cardCode | vendor | selectedVendor |
 * filters.vendor | state.vendor (string or {CARD_CODE}) and the view from
 * ctx.fy | filters.fy | state.fy.
 *
 * Three books are separate. This module never sees more than one at a time
 * and never sums across books.
 * ---------------------------------------------------------------------------
 */
import * as core from './core.js';

const NS = 'http://www.w3.org/2000/svg';
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const FONT = 'ui-sans-serif,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';

const C = Object.freeze({
  page: '#f6f7f9', card: '#ffffff', border: '#e3e6ea', hair: '#eaecf0',
  ink: '#14181f', muted: '#667085',
  ok: '#067647', warn: '#b54708', danger: '#b42318', neutral: '#475467', onacct: '#6941c6',
  oil: '#b45309', bev: '#0e7490', mart: '#6d28d9',
  linkInv: '#667085', grossFill: '#e4e7ec',
});
const ACCENT = { oil: C.oil, mart: C.mart, bev: C.bev, beverages: C.bev };

// VPM2."InvType" — what a payment line can attach to (FACTS §3). Nothing is
// dropped: an unknown type becomes "Other (InvType=nn)" and is still drawn.
const TYPES = {
  '18': { kind: 'invoice',    label: 'A/P invoice',     short: 'BILL',         color: C.linkInv },
  '19': { kind: 'creditnote', label: 'A/P credit note', short: 'CREDIT NOTE',  color: C.danger },
  '30': { kind: 'journal',    label: 'Journal entry',   short: 'JOURNAL',      color: C.warn },
  '46': { kind: 'onaccount',  label: 'On-account payment used', short: 'ON-ACCT USED', color: C.onacct },
  '24': { kind: 'other',      label: 'Incoming payment (contra)', short: 'CONTRA', color: C.warn },
  '13': { kind: 'other',      label: 'A/R invoice (contra)',      short: 'CONTRA', color: C.warn },
  '14': { kind: 'other',      label: 'A/R credit note (contra)',  short: 'CONTRA', color: C.warn },
};
function typeInfo(t) {
  const k = str(t);
  return TYPES[k] || { kind: 'other', label: `Other (InvType=${k || '?'})`, short: `OTHER ${k || '?'}`, color: C.warn };
}

// RESIDUAL_FLAG vocabulary — FACTS §9. GROSS_PAID is a TDS question, not an
// overpayment; it is never labelled "overpaid".
const FLAG = {
  UNPAID:     { tone: C.neutral, chip: 'UNPAID',     text: 'no payment touches this bill' },
  OK:         { tone: C.ok,      chip: 'OK',         text: 'paid gross − TDS − discount · reconciles (the TDS may be zero on the bill)' },
  GROSS_PAID: { tone: C.warn,    chip: 'GROSS PAID', text: 'paid in full — the TDS on the bill was not deducted at payment (WTApplied = 0)' },
  SHORT:      { tone: C.warn,    chip: 'SHORT',      text: 'paid less than gross − TDS; the gap is unexplained' },
  OVER:       { tone: C.danger,  chip: 'OVER',       text: 'paid above the bill' },
  PART_TDS:   { tone: C.warn,    chip: 'PART TDS',   text: 'something was deducted, but less than the TDS on the bill' },
};
const MATCH = {
  MATCHED:    { tone: C.ok,     chip: 'MATCHED',    text: 'fully applied to documents' },
  PARTIAL:    { tone: C.warn,   chip: 'PARTIAL',    text: 'part of the money is not applied to any document' },
  ON_ACCOUNT: { tone: C.onacct, chip: 'ON ACCOUNT', text: 'paid against no document — not matched to any bill' },
};

/* ---------------------------------------------------------------- helpers */

// Prefer core.js helpers when they exist; never hard-depend on a name we
// cannot see (a missing named import is a link-time error for the whole page).
function pickFn(names) {
  for (const n of names) if (typeof core[n] === 'function') return core[n];
  return null;
}
const coreMoney = pickFn(['moneyFull', 'fmtINR', 'formatINR', 'inr']);
const coreEsc = pickFn(['escapeHTML', 'esc', 'escapeHtml', 'escHtml']);

function str(v) { return v === null || v === undefined ? '' : String(v); }
function num(v) {
  if (v === null || v === undefined || v === '' || v === 'NULL') return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function esc(s) {
  if (coreEsc) { try { return coreEsc(str(s)); } catch (e) { /* fall through */ } }
  return str(s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}
// Indian digit grouping. Exact rupees; paise only when present. Unicode minus.
function localINR(n) {
  const neg = n < 0;
  const r = Math.round(Math.abs(n) * 100) / 100;
  const int = Math.floor(r);
  const paise = Math.round((r - int) * 100);
  let s = String(int);
  if (s.length > 3) {
    const last3 = s.slice(-3);
    const rest = s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',');
    s = rest + ',' + last3;
  }
  if (paise) s += '.' + String(paise).padStart(2, '0');
  return (neg ? '−' : '') + s;
}
// money(null) is NEVER "0". It says so.
function money(v, nullText = 'not computed') {
  const n = num(v);
  if (n === null) return nullText;
  if (coreMoney) {
    try { const s = coreMoney(n, { paise: Math.round(Math.abs(n) * 100) % 100 !== 0 }); if (typeof s === 'string' && s.trim()) return s; } catch (e) { /* fall through */ }
  }
  return localINR(n);
}
function fmtDate(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(str(s));
  if (!m) return str(s) || '';
  return `${m[3]} ${MON[Number(m[2]) - 1] || m[2]} ${m[1].slice(2)}`;
}
// Approximate text width for the system sans stack (good enough to truncate).
function textW(s, px) { return str(s).length * px * 0.58; }
function fit(s, maxPx, px) {
  s = str(s);
  const max = Math.floor(maxPx / (px * 0.58));
  if (max <= 1) return '';
  if (s.length <= max) return s;
  return s.slice(0, Math.max(1, max - 1)) + '…';
}
function rowsOf(x) {
  if (Array.isArray(x)) return x;
  if (x && Array.isArray(x.rows)) return x.rows;
  return [];
}
function resolveEl(container) {
  const el = typeof container === 'string' ? document.querySelector(container) : container;
  if (!el) throw new Error('mapping.js: container not found');
  return el;
}
function svgEl(tag, attrs, parent) {
  const el = document.createElementNS(NS, tag);
  for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) el.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(el);
  return el;
}
function svgText(parent, x, y, text, attrs) {
  const t = svgEl('text', Object.assign({ x, y }, attrs), parent);
  t.textContent = text;
  return t;
}
function htmlEl(tag, cls, parent, text) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text !== undefined) el.textContent = text;
  if (parent) parent.appendChild(el);
  return el;
}
function byDateDesc(a, b) {
  return (str(b.date) > str(a.date) ? 1 : str(b.date) < str(a.date) ? -1 : 0) || (Number(b.docNum) || 0) - (Number(a.docNum) || 0);
}
function vendorCodeOf(ctx) {
  let v = ctx.cardCode ?? ctx.vendor ?? ctx.selectedVendor ?? ctx.card ?? ctx.CARD_CODE ??
    (ctx.filters && ctx.filters.vendor) ?? (ctx.state && ctx.state.vendor) ?? null;
  if (v && typeof v === 'object') v = v.CARD_CODE || v.cardCode || v.code || null;
  return str(v);
}
function windowOf(ctx) {
  let from = ctx.dateFrom || ctx.from || null;
  let to = ctx.dateTo || ctx.to || null;
  const fy = str(ctx.fy ?? (ctx.filters && ctx.filters.fy) ?? (ctx.state && ctx.state.fy) ?? '').toUpperCase();
  if (!from && !to && fy && fy !== 'ALL') {
    const m = /^(?:FY)?(\d{2})(?:-\d{2})?$/.exec(fy);
    if (m) {
      const y = 2000 + Number(m[1]);
      from = `${y}-04-01`;
      to = `${y + 1}-04-01`;
    }
  }
  return (from || to) ? { from, to } : null;
}
function windowLabel(win) {
  if (!win) return 'all fetched dates (from 01 Apr 25)';
  return `${win.from ? fmtDate(win.from) : 'start'} → ${win.to ? 'before ' + fmtDate(win.to) : 'today'}`;
}
function payMethod(r) {
  const parts = [];
  if ((num(r.TRSFR_SUM) || 0) > 0) parts.push('transfer');
  if ((num(r.CHECK_SUM) || 0) > 0) parts.push('cheque');
  if ((num(r.CASH_SUM) || 0) > 0) parts.push('cash');
  return parts.length ? parts.join(' + ') : 'method not recorded';
}
function plural(n, one, many) { return `${n} ${n === 1 ? one : (many || one + 's')}`; }

/* ---------------------------------------------------------------- css */

let cssDone = false;
function injectCSS() {
  if (cssDone || typeof document === 'undefined') return;
  if (document.getElementById('tpm-css')) { cssDone = true; return; }
  const st = document.createElement('style');
  st.id = 'tpm-css';
  st.textContent = `
.tpm{font-family:${FONT};color:${C.ink};font-variant-numeric:tabular-nums;max-width:100%}
.tpm *{box-sizing:border-box;min-width:0}
.tpm-top{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px;margin:0 0 8px}
.tpm-vendor{font-size:14px;font-weight:600;color:${C.ink}}
.tpm-window{font-size:12px;color:${C.muted}}
.tpm-legend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;color:${C.muted};margin:0 0 10px}
.tpm-legend span{white-space:nowrap}
.tpm-legend i{display:inline-block;width:18px;height:0;border-top:3px solid;vertical-align:middle;margin-right:5px;border-radius:2px}
.tpm-legend i.dash{border-top-style:dashed}
.tpm-legend b{display:inline-block;width:10px;height:10px;border-radius:2px;vertical-align:-1px;margin-right:5px}
.tpm-banner{font-size:12.5px;color:${C.warn};background:rgba(181,71,8,.07);border:1px solid rgba(181,71,8,.25);border-radius:8px;padding:7px 10px;margin:0 0 10px}
.tpm-note{font-size:12px;color:${C.muted};margin:6px 0 0;line-height:1.45}
.tpm-svgwrap{width:100%;overflow:hidden}
.tpm-svg{display:block;width:100%;height:auto;font-family:${FONT};font-variant-numeric:tabular-nums;user-select:none;-webkit-user-select:none}
.tpm-hdr{font-size:12px;fill:${C.muted};letter-spacing:.04em}
.tpm-sub{font-size:11px;fill:${C.muted}}
.tpm-node{cursor:pointer;outline:none}
.tpm-node .tpm-box{fill:${C.card};stroke:${C.border};stroke-width:1;transition:stroke .12s}
.tpm-node:hover .tpm-box,.tpm-node.is-on .tpm-box{stroke:${C.ink}}
.tpm-node:focus-visible .tpm-box{stroke:${C.ink};stroke-width:2}
.tpm-node.is-pin .tpm-box{stroke:${C.ink};stroke-width:2}
.tpm-node.is-dim{opacity:.26}
.tpm-t1{font-size:13px;fill:${C.ink}}
.tpm-t2{font-size:11px;fill:${C.muted}}
.tpm-money{font-size:13px;fill:${C.ink};text-anchor:end}
.tpm-money.neg{fill:${C.danger}}
.tpm-money.na{fill:${C.muted};font-size:11px}
.tpm-chip-t{font-size:9.5px;letter-spacing:.05em;text-anchor:middle;font-weight:600}
.tpm-link{fill:none;stroke-opacity:.38;stroke-linecap:round;stroke-linejoin:round;transition:stroke-opacity .12s}
.tpm-link.is-on{stroke-opacity:.95}
.tpm-link.is-dim{stroke-opacity:.05}
.tpm-lbl{display:none;font-size:11px;fill:${C.ink};text-anchor:middle;paint-order:stroke;stroke:#fff;stroke-width:3.5px;stroke-linejoin:round;pointer-events:none}
.tpm-lbl.is-on{display:block}
.tpm-lbl.neg{fill:${C.danger}}
.tpm-caption{margin:8px 0 0;font-size:12.5px;color:${C.neutral};line-height:1.45;min-height:18px}
.tpm-caption b{color:${C.ink};font-weight:600}
.tpm-empty{padding:18px;border:1px dashed ${C.border};border-radius:10px;color:${C.muted};font-size:13px;background:${C.card};line-height:1.5}
.tpm-empty b{color:${C.ink}}
.tpm-pm-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px;margin:0 0 6px}
.tpm-pm-head .t{font-size:15px;font-weight:600}
.tpm-pm-head .m{font-size:15px;font-weight:600;font-variant-numeric:tabular-nums}
.tpm-pm-head .s{font-size:12px;color:${C.muted}}
.tpm-chip{display:inline-block;font-size:10px;letter-spacing:.05em;font-weight:600;padding:1px 6px;border-radius:4px;vertical-align:1px}
.tpm-sec{font-size:12px;fill:${C.muted};letter-spacing:.04em}
.tpm-lab{font-size:12px;fill:${C.neutral}}
.tpm-lab.k{fill:${C.ink};font-weight:600}
.tpm-amt{font-size:12.5px;fill:${C.ink};text-anchor:end}
.tpm-amt.neg{fill:${C.danger}}
.tpm-amt.warn{fill:${C.warn}}
.tpm-amt.na{fill:${C.muted};text-anchor:start;font-size:11.5px}
.tpm-exp{font-size:11px;fill:${C.muted}}
.tpm-exp.warn{fill:${C.warn}}
.tpm-exp.danger{fill:${C.danger}}
.tpm-seg{cursor:default}
.tpm-seg-t{font-size:11px;fill:#fff;pointer-events:none}
.tpm-row{cursor:pointer;outline:none}
.tpm-row:focus-visible .tpm-rowbox{stroke:${C.ink};stroke-width:1.5}
.tpm-row:hover .tpm-rowbox{stroke:${C.ink}}
.tpm-rowbox{fill:${C.card};stroke:${C.border}}
.tpm-tick{stroke:${C.hair};stroke-width:1}
`;
  document.head.appendChild(st);
  cssDone = true;
}

/* ---------------------------------------------------------------- model */

function invoiceNode(r) {
  const n = {
    id: 'inv:' + str(r.DOC_ENTRY), side: 'L', kind: 'invoice', type: '18',
    docEntry: str(r.DOC_ENTRY), docNum: str(r.DOC_NUM), bill: str(r.VENDOR_BILL) || '(none)',
    date: str(r.DOC_DATE), gross: num(r.GROSS), tds: num(r.TDS), tdsApplied: num(r.TDS_APPLIED),
    disc: num(r.DISCOUNT), netPaid: num(r.NET_PAID), other: num(r.OTHER_DEDUCTION),
    flag: str(r.RESIDUAL_FLAG) || 'UNPAID', payCnt: Number(r.PAY_CNT) || 0,
    paidToDate: num(r.PAID_TO_DATE), payNums: str(r.PAY_NUMS), docStatus: str(r.DOC_STATUS),
    branch: str(r.BRANCH), cardName: str(r.CARD_NAME),
    outsideWindow: false, inView: true, links: [], hidden: 0, row: r,
  };
  return n;
}
function stubInvoiceNode(a) {
  // A bill referenced by a payment line but not in the fetched invoice set —
  // dated before 2025-04-01 (FACTS §6). Still rendered, with its DocEntry.
  return {
    id: 'inv:' + str(a.TGT_DOC_ENTRY), side: 'L', kind: 'invoice', type: '18',
    docEntry: str(a.TGT_DOC_ENTRY), docNum: str(a.TGT_DOC_NUM), bill: str(a.TGT_VENDOR_BILL),
    date: str(a.TGT_DATE), gross: num(a.TGT_GROSS), tds: num(a.TGT_TDS), tdsApplied: null,
    disc: null, netPaid: null, other: null, flag: '', payCnt: 0, paidToDate: null, payNums: '',
    docStatus: '', branch: '', cardName: str(a.CARD_NAME),
    outsideWindow: true, inView: false, links: [], hidden: 0, row: null,
  };
}
function targetNode(a) {
  const ti = typeInfo(a.INV_TYPE);
  return {
    id: `tgt:${str(a.INV_TYPE)}:${str(a.TGT_DOC_ENTRY)}`, side: 'L', kind: ti.kind, type: str(a.INV_TYPE),
    typeLabel: ti.label, typeShort: ti.short, color: ti.color,
    docEntry: str(a.TGT_DOC_ENTRY), docNum: str(a.TGT_DOC_NUM), bill: '', date: str(a.TGT_DATE),
    gross: num(a.TGT_GROSS), tds: num(a.TGT_TDS), cardName: str(a.CARD_NAME),
    outsideWindow: str(a.IN_WINDOW) !== 'Y', inView: false, links: [], hidden: 0, row: null,
  };
}
function paymentNode(r) {
  const n = {
    id: 'pay:' + str(r.DOC_ENTRY), side: 'R', kind: 'payment', type: 'pay',
    docEntry: str(r.DOC_ENTRY), docNum: str(r.DOC_NUM), date: str(r.DOC_DATE),
    total: num(r.PAY_TOTAL), method: payMethod(r), ref: str(r.TRSFR_REF),
    allocCnt: Number(r.ALLOC_CNT) || 0, allocTotal: num(r.ALLOC_TOTAL), invCnt: Number(r.INV_CNT) || 0,
    invApplied: num(r.INV_APPLIED), cnApplied: num(r.CN_APPLIED), jeApplied: num(r.JE_APPLIED),
    otherApplied: num(r.OTHER_APPLIED), unallocated: num(r.UNALLOCATED),
    matchFlag: str(r.MATCH_FLAG) || (Number(r.ALLOC_CNT) ? 'MATCHED' : 'ON_ACCOUNT'),
    remarks: str(r.REMARKS), cardName: str(r.CARD_NAME),
    outsideWindow: false, inView: true, links: [], hidden: 0, row: r,
  };
  // Netted view (payments.sql): a credit-note line is stored POSITIVE by SAP
  // although it REDUCES what the payment covers. INV − CN + JE + OTHER ties
  // to PAY_TOTAL to the paisa; the file's UNALLOCATED on those rows is an
  // artifact, not money to chase.
  if (n.total !== null && n.invApplied !== null) {
    const netted = n.invApplied - (n.cnApplied || 0) + (n.jeApplied || 0) + (n.otherApplied || 0);
    n.netUnallocated = Math.round((n.total - netted) * 100) / 100;
  } else n.netUnallocated = n.unallocated;
  return n;
}
function stubPaymentNode(a) {
  return {
    id: 'pay:' + str(a.PAY_DOC_ENTRY), side: 'R', kind: 'payment', type: 'pay',
    docEntry: str(a.PAY_DOC_ENTRY), docNum: str(a.PAY_DOC_NUM), date: str(a.PAY_DATE),
    total: null, method: 'not in payment file', ref: '', allocCnt: 0, allocTotal: null, invCnt: 0,
    invApplied: null, cnApplied: null, jeApplied: null, otherApplied: null, unallocated: null,
    netUnallocated: null, matchFlag: '', remarks: '', cardName: str(a.CARD_NAME),
    outsideWindow: true, inView: false, links: [], hidden: 0, row: null,
  };
}

export function buildMappingModel(ctx = {}) {
  const src = ctx.data || ctx;
  const code = vendorCodeOf(ctx);
  const byCode = r => !code || str(r.CARD_CODE) === code;
  const inv = rowsOf(src.invoices).filter(byCode);
  const pay = rowsOf(src.payments).filter(byCode);
  const al = rowsOf(src.allocations).filter(byCode);
  const win = windowOf(ctx);
  const inView = d => !win || ((!win.from || str(d) >= win.from) && (!win.to || str(d) < win.to));
  const vendorName = str(ctx.cardName) || str((inv[0] || pay[0] || al[0] || {}).CARD_NAME) || code || '(no transporter)';

  const nodes = new Map();
  for (const r of inv) { const n = invoiceNode(r); n.inView = inView(n.date); nodes.set(n.id, n); }
  for (const r of pay) { const n = paymentNode(r); n.inView = inView(n.date); nodes.set(n.id, n); }

  // Links: one per (payment, type, target); every VPM2 row is summed in.
  const links = new Map();
  for (const a of al) {
    const type = str(a.INV_TYPE);
    const ti = typeInfo(type);
    const payId = 'pay:' + str(a.PAY_DOC_ENTRY);
    const tgtId = type === '18' ? 'inv:' + str(a.TGT_DOC_ENTRY) : `tgt:${type}:${str(a.TGT_DOC_ENTRY)}`;
    if (!nodes.has(payId)) { const p = stubPaymentNode(a); p.inView = inView(p.date); nodes.set(payId, p); }
    if (!nodes.has(tgtId)) nodes.set(tgtId, type === '18' ? stubInvoiceNode(a) : targetNode(a));
    const key = payId + '>' + tgtId;
    let l = links.get(key);
    if (!l) {
      l = { id: key, source: tgtId, target: payId, type, kind: ti.kind, color: ti.color, amount: 0, lines: 0, unknown: 0, payDate: str(a.PAY_DATE) };
      links.set(key, l);
    }
    const v = num(a.SUM_APPLIED);
    if (v === null) l.unknown++; else l.amount += v;
    l.lines++;
  }
  for (const l of links.values()) l.amount = Math.round(l.amount * 100) / 100;

  // View: in-window documents, plus whatever an in-window document is linked
  // to (an FY26 payment settling an FY25 bill must still show the bill).
  const payIn = new Set(), leftIn = new Set();
  for (const n of nodes.values()) if (n.inView) (n.side === 'R' ? payIn : leftIn).add(n.id);
  const finalL = new Set(leftIn), finalR = new Set(payIn);
  for (const l of links.values()) {
    if (payIn.has(l.target)) finalL.add(l.source);
    if (leftIn.has(l.source)) finalR.add(l.target);
  }
  const L = [];
  for (const l of links.values()) {
    if (finalL.has(l.source) && finalR.has(l.target)) {
      L.push(l);
      nodes.get(l.source).links.push(l);
      nodes.get(l.target).links.push(l);
    } else {
      if (nodes.has(l.source)) nodes.get(l.source).hidden++;
      if (nodes.has(l.target)) nodes.get(l.target).hidden++;
    }
  }

  const left = [], payments = [];
  for (const n of nodes.values()) {
    if (n.side === 'L' ? !finalL.has(n.id) : !finalR.has(n.id)) continue;
    n.outsideView = !n.inView && !n.outsideWindow;
    n.applied = n.links.reduce((s, l) => s + l.amount, 0);
    if (n.side === 'L') {
      if (n.kind !== 'invoice') n.group = 'matched';
      else if (n.links.length || n.payCnt > 0 || n.outsideWindow) n.group = 'matched';
      else if ((n.paidToDate || 0) > 0) n.group = 'settled_nopay';
      else n.group = 'untouched';
      decorateLeft(n);
      left.push(n);
    } else {
      n.group = n.links.length ? 'matched' : (n.allocCnt > 0 ? 'matched' : 'onaccount');
      decoratePayment(n);
      payments.push(n);
    }
  }

  const sum = (arr, f) => arr.reduce((s, x) => s + (f(x) || 0), 0);
  const nfetch = (arr, f) => arr.filter(n => f(n) === null).length;
  const g = name => left.filter(n => n.group === name);
  const model = {
    vendor: { code, name: vendorName },
    window: win, windowLabel: windowLabel(win),
    left, payments, links: L, nodes,
    groups: {
      matched:       { nodes: g('matched'),       gross: sum(g('matched'), n => n.gross),       na: nfetch(g('matched'), n => n.gross) },
      settled_nopay: { nodes: g('settled_nopay'), gross: sum(g('settled_nopay'), n => n.gross), na: nfetch(g('settled_nopay'), n => n.gross) },
      untouched:     { nodes: g('untouched'),     gross: sum(g('untouched'), n => n.gross),     na: nfetch(g('untouched'), n => n.gross) },
      payMatched:    { nodes: payments.filter(p => p.group === 'matched'),   total: sum(payments.filter(p => p.group === 'matched'), p => p.total), na: nfetch(payments.filter(p => p.group === 'matched'), p => p.total) },
      onaccount:     { nodes: payments.filter(p => p.group === 'onaccount'), total: sum(payments.filter(p => p.group === 'onaccount'), p => p.total) },
    },
    maxAbs: L.reduce((m, l) => Math.max(m, Math.abs(l.amount)), 0),
    shown: new Set([...left, ...payments].map(n => n.id)),
  };
  return model;
}

function decorateLeft(n) {
  if (n.kind === 'invoice') {
    const f = FLAG[n.flag] || (n.outsideWindow ? { tone: C.neutral, chip: 'OUT OF WINDOW', text: 'bill dated before 01 Apr 25 — not in the fetched data' } : { tone: C.neutral, chip: n.flag || '?', text: 'unknown flag' });
    n.tone = f.tone; n.chip = f.chip; n.flagText = f.text;
    if (n.outsideWindow) {
      n.line1 = `(invoice outside window) DocEntry ${n.docEntry}`;
      n.amountText = 'not fetched'; n.amountNA = true;
      n.line2 = `applied ${money(n.applied)} by ${plural(n.links.length, 'payment')} · bill not in data`;
      n.title = `A/P invoice DocEntry ${n.docEntry}: dated before the 01 Apr 25 fetch window, so its gross/TDS are not in the data. ${plural(n.links.length, 'payment')} applied ${money(n.applied)} to it.`;
    } else {
      n.line1 = `${n.docNum} · ${n.bill}`;
      n.amountText = money(n.gross); n.amountNA = n.gross === null;
      const bits = [fmtDate(n.date), `TDS ${money(n.tds)}`];
      if (n.group === 'matched') {
        bits.push(`net paid ${money(n.netPaid)}`);
        if (n.links.length > 1) bits.push(`split: ${plural(n.links.length, 'payment')}`);
        if (n.hidden) bits.push(`+${n.hidden} outside view`);
        if (!n.links.length && n.payCnt > 0) bits.push('payment lines not in data');
      } else if (n.group === 'settled_nopay') {
        n.chip = 'SETTLED · NO PAY'; n.flagText = 'no payment line, but SAP PaidToDate shows it settled by reconciliation (JE / CN / on-account) — not unpaid in the cash sense';
        bits.push(`PaidToDate ${money(n.paidToDate)} — reconciled without a payment`);
      } else {
        bits.push('no payment, nothing reconciled');
      }
      n.line2 = bits.join(' · ');
      const chain = n.other === null
        ? 'other deduction not computed (no payment line)'
        : `other deduction ${money(n.other)} (residual — unexplained: shortage/damage claim or settled by journal)`;
      n.title = `A/P invoice ${n.docNum} (vendor bill ${n.bill}) dated ${fmtDate(n.date)}: gross ${money(n.gross)}, TDS on bill ${money(n.tds)}, discount ${money(n.disc)}, net paid ${money(n.netPaid)}; ${chain}. ${n.chip}: ${n.flagText}.`;
    }
  } else {
    n.tone = n.color; n.chip = n.typeShort;
    const idTxt = n.docNum ? n.docNum : `DocEntry ${n.docEntry}`;
    n.line1 = `${n.typeLabel} ${idTxt}`;
    if (n.kind === 'creditnote') { n.amountText = money(n.gross); n.amountNA = n.gross === null; }
    else { n.amountText = money(n.applied); n.amountNA = false; }
    const lines = n.links.reduce((s, l) => s + l.lines, 0);
    const bits = [];
    if (n.date) bits.push(fmtDate(n.date));
    bits.push(`applied ${money(n.applied)}`);
    if (lines > n.links.length) bits.push(`${lines} lines`);
    if (n.kind === 'journal') bits.push('settled by JE — manual');
    else if (n.kind === 'onaccount') bits.push('earlier on-account money used');
    else if (n.kind === 'creditnote') bits.push('reduces what is owed');
    else bits.push('contra / other — shown, not interpreted');
    n.line2 = bits.join(' · ');
    n.title = `${n.typeLabel} ${idTxt}: ${plural(n.links.length, 'payment')} applied ${money(n.applied)}${lines > n.links.length ? ` across ${lines} lines` : ''}.` +
      (n.kind === 'journal' ? ' A manual journal settlement (OJDT TransId), not a bill — look it up in SAP.' :
       n.kind === 'onaccount' ? ' Negative: an earlier on-account payment being consumed by this one.' :
       n.kind === 'creditnote' ? ' An A/P credit note reduces what JIVO owes; SAP stores its applied sum positive.' : '');
  }
  n.aria = n.title;
}
function decoratePayment(n) {
  const m = MATCH[n.matchFlag] || (n.outsideWindow ? { tone: C.neutral, chip: 'NOT IN FILE', text: 'payment not in the fetched file' } : MATCH.MATCHED);
  n.tone = n.group === 'onaccount' ? C.onacct : (n.netUnallocated !== null && Math.abs(n.netUnallocated) > 1 ? C.warn : m.tone);
  n.chip = n.group === 'onaccount' ? 'ON ACCOUNT' : (n.netUnallocated !== null && Math.abs(n.netUnallocated) > 1 ? 'PARTIAL' : (n.matchFlag === 'PARTIAL' ? 'MATCHED · NET CN' : m.chip));
  n.line1 = n.docNum || `DocEntry ${n.docEntry}`;
  n.amountText = money(n.total, 'not fetched'); n.amountNA = n.total === null;
  const bits = [fmtDate(n.date), n.method];
  const bills = n.links.filter(l => l.kind === 'invoice').length;
  const others = n.links.length - bills;
  if (n.group === 'onaccount') bits.push('no document attached');
  else {
    if (bills) bits.push(plural(bills, 'bill'));
    if (others) bits.push(`${others} other`);
    if (n.netUnallocated !== null && Math.abs(n.netUnallocated) > 1) bits.push(`unapplied ${money(n.netUnallocated)}`);
    if (n.hidden) bits.push(`+${n.hidden} outside view`);
    if (!n.links.length && n.allocCnt > 0) bits.push('lines not in data');
  }
  n.line2 = bits.join(' · ');
  n.title = `Outgoing payment ${n.docNum} dated ${fmtDate(n.date)}: ${money(n.total, 'amount not fetched')} by ${n.method}. ` +
    (n.group === 'onaccount' ? 'ON ACCOUNT — paid against no document; not matched to any bill.' :
      `Applied to ${plural(n.links.length, 'document')}${n.netUnallocated !== null && Math.abs(n.netUnallocated) > 1 ? `; ${money(n.netUnallocated)} not applied to any document` : ''}.`) +
    (n.remarks ? ` Remarks: ${n.remarks}` : '');
  n.aria = n.title;
}

function selectionOf(n) {
  return { kind: n.kind, docEntry: n.docEntry, docNum: n.docNum, type: n.type, id: n.id };
}
function idOfSelection(sel) {
  if (!sel) return null;
  if (typeof sel === 'string') return sel;
  if (sel.id) return sel.id;
  const k = str(sel.kind), e = str(sel.docEntry);
  if (k === 'payment') return 'pay:' + e;
  if (k === 'invoice' || !k) return 'inv:' + e;
  const t = str(sel.type) || ({ creditnote: '19', journal: '30', onaccount: '46' }[k] || '');
  return `tgt:${t}:${e}`;
}

/* ---------------------------------------------------------------- layout */

const PAD = 8, ROW = 34, NODE_H = 30, TOP = 26;

function strokeFor(amount, maxAbs) {
  if (!maxAbs) return 1.5;
  return clamp(1.5 + 12.5 * Math.abs(amount) / maxAbs, 1.5, 14);
}
function groupHeader(out, x, y, w, label, count, totalText, tone) {
  out.headers.push({ x, y, w, label, count, totalText, tone });
  return y + 22;
}

// Two columns: bills on the left, payments on the right, curves between.
function placeTwoCol(model) {
  const W = model.W;
  const band = clamp(W * 0.2, 120, 220);
  const colW = (W - PAD * 2 - band) / 2;
  const lx = PAD, rx = PAD + colW + band;
  const out = { placed: [], headers: [], bands: [], links: [], colTitles: [], mode: 'cols' };
  const G = model.groups;

  // Order: payments by date desc; matched bills by the barycentre of their
  // payments (fewer crossings), ties by date desc.
  const payM = G.payMatched.nodes.slice().sort(byDateDesc);
  const payO = G.onaccount.nodes.slice().sort(byDateDesc);
  const payIdx = new Map(payM.map((p, i) => [p.id, i]));
  const leftM = G.matched.nodes.slice();
  for (const n of leftM) {
    const idx = n.links.map(l => payIdx.get(l.target)).filter(i => i !== undefined);
    n._bary = idx.length ? idx.reduce((a, b) => a + b, 0) / idx.length : Infinity;
  }
  leftM.sort((a, b) => (a._bary - b._bary) || byDateDesc(a, b));
  const leftS = G.settled_nopay.nodes.slice().sort(byDateDesc);
  const leftU = G.untouched.nodes.slice().sort(byDateDesc);

  out.colTitles.push({ x: lx, y: 16, text: 'BILLS · A/P INVOICES', w: colW });
  out.colTitles.push({ x: rx, y: 16, text: 'PAYMENTS · OUTGOING', w: colW });

  const place = (list, x, w, col) => {
    for (const n of list) {
      out.placed.push({ node: n, key: n.id, x, y: col.y, w, h: NODE_H, col: col.name });
      col.y += ROW;
    }
  };
  const Lc = { y: TOP, name: 'L' }, Rc = { y: TOP, name: 'R' };

  // LEFT
  Lc.y = groupHeader(out, lx, Lc.y, colW, 'Matched to a payment', leftM.length, money(G.matched.gross) + (G.matched.na ? ` (+${G.matched.na} not fetched)` : ''), C.neutral);
  if (leftM.length) place(leftM, lx, colW, Lc); else Lc.y += 6;
  Lc.y += 14;
  const unpaidN = leftS.length + leftU.length;
  const unpaidTop = Lc.y;
  Lc.y = groupHeader(out, lx, Lc.y, colW, 'NO PAYMENT LINE', unpaidN, unpaidN ? (leftU.length ? money(G.untouched.gross) + ' truly unpaid' : 'all settled by reconciliation') : 'none in this view', C.neutral);
  if (unpaidN) {
    out.headers.push({ x: lx, y: Lc.y, w: colW, sub: `settled without a payment line · PaidToDate > 0 (JE / CN / on-account) · ${leftS.length} · ${money(G.settled_nopay.gross)}` });
    Lc.y += 16;
    if (leftS.length) place(leftS, lx, colW, Lc); else { out.headers.push({ x: lx, y: Lc.y, w: colW, sub: 'none' }); Lc.y += 16; }
    Lc.y += 4;
    out.headers.push({ x: lx, y: Lc.y, w: colW, sub: `untouched — truly unpaid · ${leftU.length} · ${money(G.untouched.gross)}` });
    Lc.y += 16;
    if (leftU.length) place(leftU, lx, colW, Lc); else { out.headers.push({ x: lx, y: Lc.y, w: colW, sub: 'none' }); Lc.y += 16; }
  }
  out.bands.push({ x: lx - 4, y: unpaidTop - 6, w: colW + 8, h: Lc.y - unpaidTop + 8, tone: C.neutral });

  // RIGHT
  Rc.y = groupHeader(out, rx, Rc.y, colW, 'Matched to bills', payM.length, money(G.payMatched.total) + (G.payMatched.na ? ` (+${G.payMatched.na} not fetched)` : ''), C.neutral);
  if (payM.length) place(payM, rx, colW, Rc); else Rc.y += 6;
  Rc.y += 14;
  const onTop = Rc.y;
  Rc.y = groupHeader(out, rx, Rc.y, colW, 'PAID, NOT MATCHED TO A BILL', payO.length, payO.length ? money(G.onaccount.total) : 'none in this view', C.onacct);
  if (payO.length) {
    out.headers.push({ x: rx, y: Rc.y, w: colW, sub: 'on account — money paid against no document' });
    Rc.y += 16;
    place(payO, rx, colW, Rc);
  }
  out.bands.push({ x: rx - 4, y: onTop - 6, w: colW + 8, h: Rc.y - onTop + 8, tone: C.onacct });

  // LINKS
  const pos = new Map(out.placed.map(p => [p.key, p]));
  for (const l of model.links) {
    const s = pos.get(l.source), t = pos.get(l.target);
    if (!s || !t) continue;
    const x1 = s.x + s.w, y1 = s.y + s.h / 2, x2 = t.x, y2 = t.y + t.h / 2;
    const d = `M${x1},${y1} C${x1 + band / 2},${y1} ${x2 - band / 2},${y2} ${x2},${y2}`;
    out.links.push({ link: l, d, lx: (x1 + x2) / 2, ly: (y1 + y2) / 2 - 5, width: strokeFor(l.amount, model.maxAbs), keys: [s.key, t.key] });
  }
  out.H = Math.max(Lc.y, Rc.y) + PAD;
  return out;
}

// Phone: one column. Each matched payment, then the documents it settled,
// hanging off a spine whose stubs carry the proportional width. A bill split
// across payments appears under each (same data-id, highlights together).
function placeStacked(model) {
  const W = model.W;
  const x0 = PAD, w = W - PAD * 2, indent = 26, spineX = x0 + 11;
  const out = { placed: [], headers: [], bands: [], links: [], colTitles: [], mode: 'stack' };
  const G = model.groups;
  const payM = G.payMatched.nodes.slice().sort(byDateDesc);
  const payO = G.onaccount.nodes.slice().sort(byDateDesc);
  const leftS = G.settled_nopay.nodes.slice().sort(byDateDesc);
  const leftU = G.untouched.nodes.slice().sort(byDateDesc);
  let y = TOP;
  out.colTitles.push({ x: x0, y: 16, text: 'PAYMENT → THE BILLS IT SETTLED', w });

  y = groupHeader(out, x0, y, w, 'Matched payments', payM.length, money(G.payMatched.total) + (G.payMatched.na ? ` (+${G.payMatched.na} not fetched)` : ''), C.neutral);
  const seenBill = new Set();
  for (const p of payM) {
    const pk = p.id;
    out.placed.push({ node: p, key: pk, x: x0, y, w, h: NODE_H, col: 'S' });
    const py = y + NODE_H;
    y += ROW;
    const ls = p.links.slice().sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount));
    for (const l of ls) {
      const n = model.nodes.get(l.source);
      const key = `${n.id}#${p.id}`;
      const cy = y + NODE_H / 2;
      const extra = [];
      if (n.kind === 'invoice' && n.links.length > 1) extra.push(seenBill.has(n.id) ? 'also listed above' : `split: ${plural(n.links.length, 'payment')}`);
      seenBill.add(n.id);
      out.placed.push({ node: n, key, x: x0 + indent, y, w: w - indent, h: NODE_H, col: 'S', line2: `this payment applied ${money(l.amount)}${extra.length ? ' · ' + extra.join(' · ') : ''}` });
      out.links.push({ link: l, d: `M${spineX},${py} V${cy} H${x0 + indent}`, lx: null, width: strokeFor(l.amount, model.maxAbs), keys: [key, pk] });
      y += ROW;
    }
    y += 8;
  }
  if (!payM.length) y += 6;
  y += 10;

  const unpaidN = leftS.length + leftU.length;
  const unpaidTop = y;
  y = groupHeader(out, x0, y, w, 'NO PAYMENT LINE', unpaidN, unpaidN ? (leftU.length ? money(G.untouched.gross) + ' truly unpaid' : 'all settled by reconciliation') : 'none in this view', C.neutral);
  if (unpaidN) {
    out.headers.push({ x: x0, y, w, sub: `settled without a payment line · PaidToDate > 0 · ${leftS.length} · ${money(G.settled_nopay.gross)}` });
    y += 16;
    for (const n of leftS) { out.placed.push({ node: n, key: n.id, x: x0, y, w, h: NODE_H, col: 'S' }); y += ROW; }
    if (!leftS.length) { out.headers.push({ x: x0, y, w, sub: 'none' }); y += 16; }
    y += 4;
    out.headers.push({ x: x0, y, w, sub: `untouched — truly unpaid · ${leftU.length} · ${money(G.untouched.gross)}` });
    y += 16;
    for (const n of leftU) { out.placed.push({ node: n, key: n.id, x: x0, y, w, h: NODE_H, col: 'S' }); y += ROW; }
    if (!leftU.length) { out.headers.push({ x: x0, y, w, sub: 'none' }); y += 16; }
  }
  out.bands.push({ x: x0 - 4, y: unpaidTop - 6, w: w + 8, h: y - unpaidTop + 8, tone: C.neutral });
  y += 14;

  const onTop = y;
  y = groupHeader(out, x0, y, w, 'PAID, NOT MATCHED TO A BILL', payO.length, payO.length ? money(G.onaccount.total) : 'none in this view', C.onacct);
  if (payO.length) {
    out.headers.push({ x: x0, y, w, sub: 'on account — money paid against no document' });
    y += 16;
    for (const p of payO) { out.placed.push({ node: p, key: p.id, x: x0, y, w, h: NODE_H, col: 'S' }); y += ROW; }
  }
  out.bands.push({ x: x0 - 4, y: onTop - 6, w: w + 8, h: y - onTop + 8, tone: C.onacct });
  out.H = y + PAD;
  return out;
}

/* ---------------------------------------------------------------- draw */

function drawNode(svg, P) {
  const n = P.node;
  const g = svgEl('g', { class: 'tpm-node', tabindex: '0', role: 'button', 'data-id': n.id, 'data-key': P.key, 'aria-label': n.aria }, svg);
  const title = svgEl('title', {}, g); title.textContent = n.title;
  const box = svgEl('rect', { class: 'tpm-box', x: P.x, y: P.y, width: P.w, height: P.h, rx: 6 }, g);
  if (n.outsideWindow || n.outsideView) box.setAttribute('stroke-dasharray', '4 3');
  svgEl('rect', { x: P.x, y: P.y + 5, width: 3, height: P.h - 10, rx: 1.5, fill: n.tone }, g);

  const mW = textW(n.amountText, n.amountNA ? 11 : 13) + 6;
  svgText(g, P.x + P.w - 8, P.y + 13, n.amountText, { class: 'tpm-money' + ((n.gross ?? n.total ?? n.applied ?? 0) < 0 && !n.amountNA ? ' neg' : '') + (n.amountNA ? ' na' : '') });

  const chipTxt = n.chip;
  const cW = Math.max(26, textW(chipTxt, 9.5) + 10);
  const cx = P.x + P.w - 8 - cW, cy = P.y + 17;
  svgEl('rect', { x: cx, y: cy, width: cW, height: 11, rx: 3, fill: n.tone, 'fill-opacity': .13 }, g);
  svgText(g, cx + cW / 2, cy + 8.5, chipTxt, { class: 'tpm-chip-t', fill: n.tone });

  svgText(g, P.x + 10, P.y + 13, fit(n.line1, P.w - 10 - mW - 10, 13), { class: 'tpm-t1' });
  svgText(g, P.x + 10, P.y + 25, fit(P.line2 || n.line2, P.w - 10 - cW - 12, 11), { class: 'tpm-t2' });
  return g;
}

function drawLayout(svg, lay, accent) {
  for (const t of lay.colTitles) {
    svgText(svg, t.x, t.y, t.text, { class: 'tpm-hdr' });
    svgEl('rect', { x: t.x, y: t.y + 5, width: t.w, height: 2, fill: accent, rx: 1 }, svg);
  }
  for (const b of lay.bands) {
    svgEl('rect', { x: b.x, y: b.y, width: b.w, height: b.h, rx: 8, fill: b.tone, 'fill-opacity': .06, stroke: b.tone, 'stroke-opacity': .35, 'stroke-dasharray': '5 4' }, svg);
  }
  for (const h of lay.headers) {
    if (h.sub) { svgText(svg, h.x + 2, h.y + 11, fit(h.sub, h.w - 4, 11), { class: 'tpm-sub' }); continue; }
    const label = `${h.label.toUpperCase()} · ${h.count}`;
    svgText(svg, h.x, h.y + 13, fit(label, h.w - textW(h.totalText, 12) - 12, 12), { class: 'tpm-hdr', fill: h.tone });
    svgText(svg, h.x + h.w, h.y + 13, h.totalText, { class: 'tpm-hdr', 'text-anchor': 'end', fill: h.tone });
  }
  const linkEls = [];
  for (const L of lay.links) {
    const p = svgEl('path', { class: 'tpm-link', d: L.d, stroke: L.link.color, 'stroke-width': L.width.toFixed(2), 'data-link': L.link.id }, svg);
    if (L.link.amount < 0) p.setAttribute('stroke-dasharray', '7 5');
    const t = svgEl('title', {}, p);
    const s = lay.placed.find(x => x.key === L.keys[0]).node, tg = lay.placed.find(x => x.key === L.keys[1]).node;
    t.textContent = `${tg.docNum || 'payment ' + tg.docEntry} → ${s.line1}: ${money(L.link.amount)}${L.link.lines > 1 ? ` (${L.link.lines} lines)` : ''}`;
    let lbl = null;
    if (L.lx !== null) {
      lbl = svgText(svg, L.lx, L.ly, money(L.link.amount), { class: 'tpm-lbl' + (L.link.amount < 0 ? ' neg' : '') });
    }
    linkEls.push({ el: p, lbl, keys: L.keys, link: L.link });
  }
  const nodeEls = lay.placed.map(P => ({ el: drawNode(svg, P), P }));
  // labels above nodes
  for (const L of linkEls) if (L.lbl) svg.appendChild(L.lbl);
  return { linkEls, nodeEls };
}

/* ---------------------------------------------------------------- caption */

function captionFor(n, model) {
  const bold = s => `<b>${esc(s)}</b>`;
  if (n.kind === 'payment') {
    const head = `${bold('Payment ' + (n.docNum || n.docEntry))} · ${esc(fmtDate(n.date))} · ${bold(money(n.total, 'amount not fetched'))} · ${esc(n.method)}`;
    if (n.group === 'onaccount') return `${head} → ${bold('on account')}: paid against no document — not matched to any bill.`;
    const parts = n.links.slice().sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount)).map(l => {
      const s = model.nodes.get(l.source);
      const name = s.kind === 'invoice' ? (s.outsideWindow ? `bill DocEntry ${s.docEntry} (outside window)` : `${s.docNum} ${s.bill}`) : `${s.typeLabel} ${s.docNum || 'DocEntry ' + s.docEntry}`;
      return `${esc(name)} ${bold(money(l.amount))}`;
    });
    let tail = '';
    if (n.netUnallocated !== null && Math.abs(n.netUnallocated) > 1) tail = ` · ${bold(money(n.netUnallocated))} not applied to any document`;
    if (n.hidden) tail += ` · ${n.hidden} more line(s) outside this view`;
    return `${head} → ${plural(n.links.length, 'document')}: ${parts.join(' · ')}${tail}`;
  }
  if (n.kind === 'invoice') {
    if (n.outsideWindow) return `${bold('Bill DocEntry ' + n.docEntry)} is dated before 01 Apr 25, so its gross and TDS are not in the data. ${plural(n.links.length, 'payment')} applied ${bold(money(n.applied))}.`;
    const head = `${bold('Bill ' + n.docNum)} (${esc(n.bill)}) · ${esc(fmtDate(n.date))} · gross ${bold(money(n.gross))} · TDS on bill ${esc(money(n.tds))}`;
    if (n.group !== 'matched') {
      return `${head} → ${bold(n.group === 'settled_nopay' ? 'no payment line — settled by reconciliation' : 'not yet paid')}: ` + (n.group === 'settled_nopay'
        ? `no payment line, but SAP PaidToDate is ${esc(money(n.paidToDate))} — reconciled against a journal / credit note / on-account payment.`
        : 'no payment and nothing reconciled.');
    }
    const parts = n.links.slice().sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount)).map(l => {
      const p = model.nodes.get(l.target);
      return `${esc(p.docNum || 'payment ' + p.docEntry)} ${bold(money(l.amount))}`;
    });
    const f = FLAG[n.flag];
    let chain = ` · net paid ${bold(money(n.netPaid))}`;
    if (n.other === null) chain += ' · other deduction not computed';
    else if (Math.abs(n.other) > 1) chain += ` · other deduction ${bold(money(n.other))} (residual — unexplained: shortage/damage claim or settled by journal)`;
    return `${head} ← ${plural(n.links.length, 'payment')}: ${parts.join(' · ')}${chain}${f ? ` · ${bold(f.chip)}: ${esc(f.text)}` : ''}${n.hidden ? ` · ${n.hidden} more payment(s) outside this view` : ''}`;
  }
  const parts = n.links.map(l => { const p = model.nodes.get(l.target); return `${esc(p.docNum || p.docEntry)} ${bold(money(l.amount))}`; });
  return `${bold(n.typeLabel + ' ' + (n.docNum || 'DocEntry ' + n.docEntry))} ← ${parts.join(' · ')}. ${esc(n.title.split('. ').slice(1).join('. '))}`;
}

/* ---------------------------------------------------------------- renderMapping */

// Accepts (container, ctx) or (container, cardCode, ctx) — views.js style.
export function renderMapping(container, a, b) {
  const ctx = (a && typeof a === 'object') ? a : Object.assign({}, b || {}, a != null && a !== '' ? { cardCode: a } : {});
  const el = resolveEl(container);
  injectCSS();
  if (el.__tpm && el.__tpm.destroy) el.__tpm.destroy();
  el.textContent = '';
  el.classList.add('tpm');

  const model = buildMappingModel(ctx);
  const accent = ACCENT[str(ctx.company).toLowerCase()] || C.neutral;
  const onSelect = typeof ctx.onSelect === 'function' ? ctx.onSelect : null;

  const top = htmlEl('div', 'tpm-top', el);
  htmlEl('span', 'tpm-vendor', top, `${model.vendor.name}${model.vendor.code ? ' · ' + model.vendor.code : ''}`);
  htmlEl('span', 'tpm-window', top, `view: ${model.windowLabel}${ctx.asOf ? ' · data as of ' + fmtDate(ctx.asOf) : ''}`);

  if (!model.left.length && !model.payments.length) {
    const e = htmlEl('div', 'tpm-empty', el);
    e.innerHTML = `<b>Nothing to map.</b> ${esc(model.vendor.name)} has no A/P invoice and no outgoing payment in this view (${esc(model.windowLabel)}). Widen the view to FY25 or all dates, or pick another transporter.`;
    const ctl = { model, select() {}, clear() {}, destroy() { el.__tpm = null; } };
    el.__tpm = ctl;
    return ctl;
  }

  // Legend
  const lg = htmlEl('div', 'tpm-legend', el);
  lg.innerHTML = [
    `<span><i style="border-color:${C.linkInv}"></i>A/P invoice</span>`,
    `<span><i style="border-color:${C.danger}"></i>credit note</span>`,
    `<span><i style="border-color:${C.warn}"></i>journal entry / contra</span>`,
    `<span><i class="dash" style="border-color:${C.onacct}"></i>earlier on-account money used (negative)</span>`,
    `<span><b style="background:${C.neutral};opacity:.35"></b>no payment line</span>`,
    `<span><b style="background:${C.onacct};opacity:.45"></b>paid, not matched to a bill</span>`,
    `<span>line width ∝ amount applied · hover / tap a box to trace it</span>`,
  ].join('');

  if (!model.links.length) {
    htmlEl('div', 'tpm-banner', el, `No payment is matched to any bill for this transporter in this view — every bill below sits in "not yet paid" and every payment in "paid, not matched to a bill". Nothing to draw between the two columns.`);
  }

  const wrap = htmlEl('div', 'tpm-svgwrap', el);
  const caption = htmlEl('div', 'tpm-caption', el);
  caption.setAttribute('aria-live', 'polite');
  const note = htmlEl('p', 'tpm-note', el);
  note.textContent = 'Links are drawn from VPM2 allocation lines (payment DocEntry → target DocEntry). TDS lives on the bill (OPCH.WTSum); at payment WtAppld is 0 across the board. "Other deduction" is a balancing figure, not a known deduction. Bills dated before 01 Apr 25 that an in-view payment settled are shown as "(invoice outside window)" with their DocEntry.';

  const state = { pinned: null, hover: null, widthDrawn: 0, els: null, lay: null, observer: null };

  function measure() {
    const w = wrap.clientWidth || el.clientWidth || (el.parentElement && el.parentElement.clientWidth) || 0;
    return w > 0 ? w : 960;
  }

  function draw() {
    const W = Math.max(320, Math.floor(measure()));
    model.W = W;
    const lay = W < 560 ? placeStacked(model) : placeTwoCol(model);
    wrap.textContent = '';
    const svg = svgEl('svg', { class: 'tpm-svg', viewBox: `0 0 ${W} ${Math.ceil(lay.H)}`, width: W, height: Math.ceil(lay.H), preserveAspectRatio: 'xMinYMin meet', role: 'group', 'aria-label': `Mapping of ${model.left.length} bills and ${model.payments.length} payments for ${model.vendor.name}` }, wrap);
    svg.style.height = 'auto';
    const t = svgEl('title', {}, svg);
    t.textContent = `${model.vendor.name}: ${plural(model.groups.matched.nodes.length, 'matched bill')}, ${plural(model.groups.settled_nopay.nodes.length, 'bill')} settled without a payment, ${plural(model.groups.untouched.nodes.length, 'unpaid bill')}, ${plural(model.groups.payMatched.nodes.length, 'matched payment')}, ${plural(model.groups.onaccount.nodes.length, 'on-account payment')}`;
    state.els = drawLayout(svg, lay, accent);
    state.lay = lay;
    state.widthDrawn = W;
    wire(svg);
    applyHighlight();
  }

  function idsLinked(id) {
    const n = model.nodes.get(id);
    const s = new Set([id]);
    if (n) for (const l of n.links) { s.add(l.source); s.add(l.target); }
    return s;
  }
  function applyHighlight() {
    const active = state.pinned || state.hover;
    const { nodeEls, linkEls } = state.els;
    if (!active) {
      for (const N of nodeEls) N.el.classList.remove('is-on', 'is-dim', 'is-pin');
      for (const L of linkEls) { L.el.classList.remove('is-on', 'is-dim'); if (L.lbl) L.lbl.classList.remove('is-on'); }
      caption.innerHTML = model.links.length
        ? `Hover or tap a bill or a payment to see exactly what it maps to. ${plural(model.links.length, 'link')} drawn.`
        : '';
      return;
    }
    const keep = idsLinked(active);
    for (const N of nodeEls) {
      const on = keep.has(N.P.node.id);
      N.el.classList.toggle('is-on', on);
      N.el.classList.toggle('is-dim', !on);
      N.el.classList.toggle('is-pin', state.pinned === N.P.node.id);
    }
    for (const L of linkEls) {
      const on = L.link.source === active || L.link.target === active;
      L.el.classList.toggle('is-on', on);
      L.el.classList.toggle('is-dim', !on);
      if (L.lbl) L.lbl.classList.toggle('is-on', on);
    }
    const n = model.nodes.get(active);
    caption.innerHTML = n ? captionFor(n, model) : '';
  }

  function wire(svg) {
    const nodes = state.els.nodeEls;
    const order = nodes.map(N => N.P.key);
    const byKey = new Map(nodes.map(N => [N.P.key, N]));
    for (const N of nodes) {
      const id = N.P.node.id;
      N.el.addEventListener('mouseenter', () => { state.hover = id; applyHighlight(); });
      N.el.addEventListener('mouseleave', () => { state.hover = null; applyHighlight(); });
      N.el.addEventListener('focus', () => { state.hover = id; applyHighlight(); });
      N.el.addEventListener('blur', () => { state.hover = null; applyHighlight(); });
      N.el.addEventListener('click', (ev) => { ev.preventDefault(); toggle(id); });
      N.el.addEventListener('keydown', (ev) => {
        const k = ev.key;
        if (k === 'Enter' || k === ' ') { ev.preventDefault(); toggle(id); return; }
        if (k === 'Escape') { ev.preventDefault(); state.pinned = null; applyHighlight(); if (onSelect) onSelect(null); return; }
        if (k === 'ArrowDown' || k === 'ArrowUp') {
          ev.preventDefault();
          const col = N.P.col;
          const same = order.filter(key => byKey.get(key).P.col === col);
          let i = same.indexOf(N.P.key) + (k === 'ArrowDown' ? 1 : -1);
          i = clamp(i, 0, same.length - 1);
          byKey.get(same[i]).el.focus();
          return;
        }
        if (k === 'ArrowRight' || k === 'ArrowLeft') {
          ev.preventDefault();
          const n = N.P.node;
          const wantCol = N.P.col === 'L' ? 'R' : N.P.col === 'R' ? 'L' : 'S';
          const linked = n.links.map(l => (n.side === 'L' ? l.target : l.source));
          let target = null;
          for (const key of order) { const M = byKey.get(key); if (M.P.col === wantCol && linked.includes(M.P.node.id) && key !== N.P.key) { target = M; break; } }
          if (!target) for (const key of order) { const M = byKey.get(key); if (M.P.col === wantCol) { target = M; break; } }
          if (target) target.el.focus();
        }
      });
    }
    svg.addEventListener('click', (ev) => {
      if (ev.target === svg && state.pinned) { state.pinned = null; applyHighlight(); if (onSelect) onSelect(null); }
    });
  }
  function toggle(id) {
    if (state.pinned === id) { state.pinned = null; applyHighlight(); if (onSelect) onSelect(null); return; }
    state.pinned = id; applyHighlight();
    const n = model.nodes.get(id);
    if (onSelect && n) onSelect(selectionOf(n));
  }

  if (ctx.selected) { const id = idOfSelection(ctx.selected); if (model.shown.has(id)) state.pinned = id; }
  draw();

  if (typeof ResizeObserver !== 'undefined') {
    state.observer = new ResizeObserver(() => {
      const w = Math.floor(measure());
      if (Math.abs(w - state.widthDrawn) > 24) draw();
    });
    state.observer.observe(wrap);
  }

  const ctl = {
    model,
    select(sel) {
      const id = idOfSelection(sel);
      state.pinned = id && model.shown.has(id) ? id : null;
      applyHighlight();
      if (id && !state.pinned) {
        const n = model.nodes.get(id);
        const what = n ? (n.kind === 'payment' ? `Payment ${n.docNum || n.docEntry} (${fmtDate(n.date)})` : n.kind === 'invoice' ? `Bill ${n.docNum || 'DocEntry ' + n.docEntry} (${fmtDate(n.date)})` : n.line1) : `Document ${esc(str(id))}`;
        caption.innerHTML = n
          ? `<b>${esc(what)}</b> is outside the current view (${esc(model.windowLabel)}) — switch to FY25 or all dates to see its mapping.`
          : `<b>${what}</b> is not in this transporter's data — nothing to highlight.`;
      }
      if (state.pinned && state.els) {
        const N = state.els.nodeEls.find(x => x.P.node.id === state.pinned);
        if (N && N.el.scrollIntoView) { try { N.el.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } catch (e) { /* ignore */ } }
      }
    },
    clear() { state.pinned = null; state.hover = null; applyHighlight(); },
    destroy() { if (state.observer) state.observer.disconnect(); el.__tpm = null; },
  };
  el.__tpm = ctl;
  return ctl;
}

/* ---------------------------------------------------------------- renderPaymentMap */

// Accepts (container, ctx) or (container, payDocEntry, ctx) — views.js calls
// it as renderPaymentMap(el, String(p.DOC_ENTRY), richCtx) with richCtx.payment = the row.
export function renderPaymentMap(container, a, b) {
  const ctx = (a && typeof a === 'object') ? a : Object.assign({}, b || {}, a != null && a !== '' && !(b && b.payment) ? { payment: a } : {});
  const el = resolveEl(container);
  injectCSS();
  if (el.__tpm && el.__tpm.destroy) el.__tpm.destroy();
  el.textContent = '';
  el.classList.add('tpm');
  const accent = ACCENT[str(ctx.company).toLowerCase()] || C.neutral;
  const onSelect = typeof ctx.onSelect === 'function' ? ctx.onSelect : null;

  const src = ctx.data || ctx;
  const payRows = rowsOf(src.payments), invRows = rowsOf(src.invoices), alRows = rowsOf(src.allocations);
  let row = null;
  const want = ctx.payment;
  if (want && typeof want === 'object') row = want;
  else {
    const key = str(want ?? ctx.docEntry ?? ctx.payDocEntry ?? '');
    row = payRows.find(r => str(r.DOC_ENTRY) === key) || payRows.find(r => str(r.DOC_NUM) === key) || null;
    if (!row && key) {
      const a = alRows.find(r => str(r.PAY_DOC_ENTRY) === key || str(r.PAY_DOC_NUM) === key);
      if (a) row = { DOC_ENTRY: a.PAY_DOC_ENTRY, DOC_NUM: a.PAY_DOC_NUM, DOC_DATE: a.PAY_DATE, CARD_CODE: a.CARD_CODE, CARD_NAME: a.CARD_NAME, _stub: true };
    }
  }
  if (!row) {
    const e = htmlEl('div', 'tpm-empty', el);
    e.innerHTML = `<b>Payment not found.</b> No outgoing payment with DocEntry/DocNum ${esc(str(want ?? ctx.docEntry ?? ''))} in the loaded data — nothing to break down.`;
    return { destroy() {} };
  }
  const p = paymentNode(row);
  if (row._stub) { p.total = null; p.outsideWindow = true; }
  const lines = alRows.filter(a => str(a.PAY_DOC_ENTRY) === p.docEntry);
  const invBy = new Map(invRows.map(r => [str(r.DOC_ENTRY), r]));

  // Aggregate lines per target (JE lines repeat on the same key — summed).
  const segs = [];
  const segBy = new Map();
  for (const a of lines) {
    const type = str(a.INV_TYPE), ti = typeInfo(type);
    const key = `${type}:${str(a.TGT_DOC_ENTRY)}`;
    let s = segBy.get(key);
    if (!s) {
      s = { key, type, ti, tgtEntry: str(a.TGT_DOC_ENTRY), tgtNum: str(a.TGT_DOC_NUM), tgtDate: str(a.TGT_DATE), bill: str(a.TGT_VENDOR_BILL), tgtGross: num(a.TGT_GROSS), tgtTds: num(a.TGT_TDS), inWindow: str(a.IN_WINDOW) === 'Y', amount: 0, lines: 0, inv: type === '18' ? invBy.get(str(a.TGT_DOC_ENTRY)) || null : null };
      segBy.set(key, s); segs.push(s);
    }
    s.amount += num(a.SUM_APPLIED) || 0; s.lines++;
  }
  for (const s of segs) s.amount = Math.round(s.amount * 100) / 100;
  segs.sort((a, b) => (a.type === '18' ? 0 : 1) - (b.type === '18' ? 0 : 1) || Math.abs(b.amount) - Math.abs(a.amount));
  const unapplied = p.netUnallocated;
  const hasUnapplied = unapplied !== null && Math.abs(unapplied) > 1;
  const cnPresent = segs.some(s => s.type === '19');

  // Header
  const head = htmlEl('div', 'tpm-pm-head', el);
  htmlEl('span', 't', head, `Payment ${p.docNum || p.docEntry}`);
  htmlEl('span', 'm', head, money(p.total, 'amount not fetched'));
  htmlEl('span', 's', head, `${fmtDate(p.date)} · ${p.cardName}${p.method ? ' · ' + p.method : ''}${p.ref ? ' · ref ' + p.ref : ''}`);
  const chip = htmlEl('span', 'tpm-chip', head, p.chip || (segs.length ? (hasUnapplied ? 'PARTIAL' : 'MATCHED') : 'ON ACCOUNT'));
  const tone = segs.length ? (hasUnapplied ? C.warn : C.ok) : C.onacct;
  chip.style.color = tone; chip.style.background = tone + '22';
  if (p.remarks) htmlEl('span', 's', head, p.remarks);

  const wrap = htmlEl('div', 'tpm-svgwrap', el);
  const note = htmlEl('p', 'tpm-note', el);
  note.textContent = 'Chain per bill: GROSS (DocTotal) − TDS (WTSum, on the bill) − DISCOUNT (DiscSum) − OTHER DEDUCTION = NET PAID (Σ SumApplied on that bill, all payments). OTHER DEDUCTION is the balancing figure — it is not a recorded deduction. A negative one equal to the TDS means the full gross was paid and TDS was not withheld at payment (WTApplied = 0 on those bills).';

  const state = { observer: null, widthDrawn: 0 };
  function measure() {
    const w = wrap.clientWidth || el.clientWidth || (el.parentElement && el.parentElement.clientWidth) || 0;
    return w > 0 ? w : 960;
  }

  function draw() {
    const W = Math.max(320, Math.floor(measure()));
    const narrow = W < 560;
    wrap.textContent = '';
    const svg = svgEl('svg', { class: 'tpm-svg', preserveAspectRatio: 'xMinYMin meet', role: 'group', 'aria-label': `How payment ${p.docNum} of ${money(p.total)} was applied` }, wrap);
    svg.style.height = 'auto';
    const labW = narrow ? 0 : 232;
    const amtW = 96;
    const barX = PAD + labW, barW = Math.max(80, W - barX - PAD - amtW - 8);
    const amtX = W - PAD;
    let y = 8;

    // ---- Section 1: the payment total split across what it was applied to
    svgText(svg, PAD, y + 11, fit(`HOW THE ${money(p.total, 'PAYMENT').toUpperCase()} WAS APPLIED`, W - PAD * 2, 12), { class: 'tpm-sec' });
    svgEl('rect', { x: PAD, y: y + 16, width: W - PAD * 2, height: 2, fill: accent, rx: 1 }, svg);
    y += 28;
    const pieces = segs.map(s => ({ label: s.type === '18' ? (s.inv ? `${s.inv.DOC_NUM}` : `DocEntry ${s.tgtEntry}`) : (s.tgtNum || `${s.ti.short}`), color: s.ti.color, amount: s.amount, seg: s }));
    if (hasUnapplied && segs.length) pieces.push({ label: 'not applied', color: C.onacct, amount: unapplied, unapplied: true });
    if (!segs.length) pieces.push({ label: 'ON ACCOUNT', color: C.onacct, amount: p.total, onacct: true });
    const totalAbs = pieces.reduce((s, x) => s + Math.abs(x.amount || 0), 0);
    let x = PAD;
    const fullW = W - PAD * 2;
    if (totalAbs > 0) {
      for (const pc of pieces) {
        const w = fullW * Math.abs(pc.amount) / totalAbs;
        const r = svgEl('rect', { class: 'tpm-seg', x, y, width: Math.max(1, w - (pc === pieces[pieces.length - 1] ? 0 : 1.5)), height: 24, fill: pc.color, 'fill-opacity': pc.unapplied || pc.onacct ? .55 : .9, rx: 3 }, svg);
        if (pc.amount < 0) r.setAttribute('stroke-dasharray', '4 3'), r.setAttribute('stroke', pc.color), r.setAttribute('fill-opacity', .35);
        const tt = svgEl('title', {}, r); tt.textContent = `${pc.label}: ${money(pc.amount)}`;
        const txt = `${pc.label} ${money(pc.amount)}`;
        if (w > textW(txt, 11) + 10) svgText(svg, x + 6, y + 15.5, txt, { class: 'tpm-seg-t' });
        else if (w > textW(pc.label, 11) + 8) svgText(svg, x + 6, y + 15.5, pc.label, { class: 'tpm-seg-t' });
        x += w;
      }
    } else {
      svgText(svg, PAD, y + 15, 'no amounts to draw', { class: 'tpm-exp' });
    }
    y += 32;
    // list of pieces
    for (const pc of pieces) {
      svgEl('rect', { x: PAD, y: y + 3, width: 10, height: 10, rx: 2, fill: pc.color, 'fill-opacity': pc.unapplied || pc.onacct ? .55 : .9 }, svg);
      let txt, exp = '';
      if (pc.onacct) { txt = 'On account — paid against no document, not matched to any bill'; }
      else if (pc.unapplied) { txt = 'Not applied to any document (netted: invoices − credit notes + journals + other)'; }
      else {
        const s = pc.seg;
        if (s.type === '18') {
          txt = s.inv
            ? (narrow ? `Bill ${s.inv.DOC_NUM} · ${str(s.inv.VENDOR_BILL) || '(none)'}` : `A/P invoice ${s.inv.DOC_NUM} · ${str(s.inv.VENDOR_BILL) || '(none)'} · ${fmtDate(s.inv.DOC_DATE)}`)
            : (narrow ? `Bill DocEntry ${s.tgtEntry} (outside window)` : `A/P invoice DocEntry ${s.tgtEntry} — (invoice outside window)`);
        } else if (s.type === '19') {
          txt = `A/P credit note ${s.tgtNum || 'DocEntry ' + s.tgtEntry}${s.tgtDate ? ' · ' + fmtDate(s.tgtDate) : ''} · CN total ${money(s.tgtGross, 'not fetched')}`; exp = 'reduces what is owed; SAP stores the applied sum positive';
        } else if (s.type === '30') {
          txt = `Journal entry TransId ${s.tgtEntry}${s.lines > 1 ? ` · ${s.lines} JE lines` : ''}`; exp = 'settled by journal — manual, look it up in SAP (OJDT)';
        } else if (s.type === '46') {
          txt = narrow ? `On-acct pmt used · DocEntry ${s.tgtEntry}` : `On-account payment used — earlier payment DocEntry ${s.tgtEntry} consumed`; exp = 'negative: money already paid on account, now used';
        } else {
          txt = `${s.ti.label} DocEntry ${s.tgtEntry}`; exp = 'shown, not interpreted';
        }
      }
      const t = svgText(svg, PAD + 16, y + 12, fit(txt, W - PAD * 2 - 16 - amtW - 6, 12.5), { class: 'tpm-lab' });
      svgText(svg, amtX, y + 12, money(pc.amount), { class: 'tpm-amt' + (pc.amount < 0 ? ' neg' : '') });
      if (pc.seg && pc.seg.type === '18' && pc.seg.inv && onSelect) {
        t.style.cursor = 'pointer';
        t.addEventListener('click', () => onSelect({ kind: 'invoice', docEntry: str(pc.seg.inv.DOC_ENTRY), docNum: str(pc.seg.inv.DOC_NUM), id: 'inv:' + str(pc.seg.inv.DOC_ENTRY) }));
      }
      y += 20;
      if (exp) { svgText(svg, PAD + 16, y + 8, fit(exp, W - PAD * 2 - 16, 11), { class: 'tpm-exp' }); y += 16; }
    }
    if (cnPresent) {
      svgText(svg, PAD, y + 10, fit(`credit-note line present: the file's UNALLOCATED (${money(p.unallocated)}) is an artifact of SAP storing it positive; netted, the money ties${hasUnapplied ? '' : ' to the paisa'}.`, W - PAD * 2, 11), { class: 'tpm-exp' });
      y += 18;
    }
    if (p.total !== null && segs.length) {
      const applied = segs.reduce((s, x) => s + (x.type === '19' ? -x.amount : x.amount), 0);
      svgText(svg, PAD, y + 10, fit(`check: payment ${money(p.total)} = applied (netted) ${money(Math.round(applied * 100) / 100)}${hasUnapplied ? ` + not applied ${money(unapplied)}` : ''}`, W - PAD * 2, 11), { class: 'tpm-exp' });
      y += 18;
    }
    y += 12;

    // ---- Section 2: per-bill chain GROSS → TDS → DISCOUNT → OTHER → NET PAID
    const bills = segs.filter(s => s.type === '18');
    if (bills.length) {
      svgText(svg, PAD, y + 11, fit(narrow ? 'PER BILL: GROSS → TDS → DISC → OTHER → NET PAID' : 'PER BILL: GROSS → TDS → DISCOUNT → OTHER DEDUCTION → NET PAID', W - PAD * 2, 12), { class: 'tpm-sec' });
      svgEl('rect', { x: PAD, y: y + 16, width: W - PAD * 2, height: 2, fill: accent, rx: 1 }, svg);
      y += 30;
    }
    const RH = narrow ? 36 : 24;      // row pitch
    const BH = 14;                    // bar height
    for (const s of bills) {
      const inv = s.inv ? invoiceNode(s.inv) : null;
      // title row
      const g = svgEl('g', { class: 'tpm-row', tabindex: '0', role: 'button' }, svg);
      const tt = svgEl('title', {}, g);
      svgEl('rect', { class: 'tpm-rowbox', x: PAD, y, width: W - PAD * 2, height: 26, rx: 6 }, g);
      if (inv) {
        const f = FLAG[inv.flag] || { tone: C.neutral, chip: inv.flag, text: '' };
        svgEl('rect', { x: PAD, y: y + 5, width: 3, height: 16, rx: 1.5, fill: f.tone }, g);
        const cW = Math.max(26, textW(f.chip, 9.5) + 10);
        svgEl('rect', { x: amtX - cW, y: y + 7.5, width: cW, height: 11, rx: 3, fill: f.tone, 'fill-opacity': .13 }, g);
        svgText(g, amtX - cW / 2, y + 16, f.chip, { class: 'tpm-chip-t', fill: f.tone });
        svgText(g, PAD + 10, y + 17, fit(`Bill ${inv.docNum} · ${inv.bill} · ${fmtDate(inv.date)}${inv.branch && !narrow ? ' · ' + inv.branch : ''}`, W - PAD * 2 - cW - 24, 13), { class: 'tpm-lab k' });
        tt.textContent = inv.title;
        g.setAttribute('aria-label', inv.title);
        const sel = () => onSelect && onSelect(selectionOf(inv));
        g.addEventListener('click', sel);
        g.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); sel(); } });
      } else {
        svgEl('rect', { x: PAD, y: y + 5, width: 3, height: 16, rx: 1.5, fill: C.neutral }, g);
        svgText(g, PAD + 10, y + 17, fit(narrow ? `(outside window) DocEntry ${s.tgtEntry} · applied ${money(s.amount)}` : `(invoice outside window) DocEntry ${s.tgtEntry} · this payment applied ${money(s.amount)}`, W - PAD * 2 - 20, 13), { class: 'tpm-lab k' });
        tt.textContent = `A/P invoice DocEntry ${s.tgtEntry} is dated before the 01 Apr 25 fetch window; its gross, TDS and net paid are not in the data.`;
        g.setAttribute('aria-label', tt.textContent);
      }
      y += 32;
      if (!inv) {
        svgText(svg, PAD + 10, y + 6, fit(narrow ? 'chain not computed — bill dated before 01 Apr 25, not fetched' : 'chain not computed — bill dated before 01 Apr 25, not in the fetched data (FACTS §6)', W - PAD * 2 - 10, 11.5), { class: 'tpm-amt na' });
        y += 22;
        continue;
      }
      // scale
      const gross = inv.gross, tds = inv.tds, disc = inv.disc, other = inv.other, net = inv.netPaid;
      const afterTds = gross === null || tds === null ? null : gross - tds;
      const afterDisc = afterTds === null || disc === null ? null : afterTds - disc;
      const maxV = Math.max(gross || 0, net || 0, afterDisc || 0, 1);
      const sx = v => barX + barW * clamp(v, 0, maxV) / maxV;
      const tickTop = y;
      // One chain row. Wide: label | bar | amount, explanation sits left of the
      // bar's start. Narrow: label above the bar; explanation on its own line.
      const wRow = (o) => {
        const by = narrow ? y + 14 : y + 4;
        if (narrow) svgText(svg, barX, y + 10, fit(o.label, W - PAD * 2, 12), { class: 'tpm-lab' + (o.strong ? ' k' : '') });
        else svgText(svg, PAD, by + BH - 3, fit(o.label, labW - 8, 12), { class: 'tpm-lab' + (o.strong ? ' k' : '') });
        for (const b of (o.bars || [])) {
          const x0 = sx(Math.min(b.from, b.to)), x1 = sx(Math.max(b.from, b.to));
          const r = svgEl('rect', { x: x0, y: by, width: Math.max(b.min === undefined ? 1.5 : b.min, x1 - x0), height: BH, fill: b.fill, 'fill-opacity': b.opacity === undefined ? .85 : b.opacity, rx: 2 }, svg);
          if (b.dash) { r.setAttribute('stroke', b.fill); r.setAttribute('stroke-dasharray', b.dash); }
        }
        if (o.amount === null || o.amount === undefined) svgText(svg, barX, by + BH - 3, o.na || 'not computed', { class: 'tpm-amt na' });
        else svgText(svg, amtX, by + BH - 3, o.amount, { class: 'tpm-amt' + (o.amountCls ? ' ' + o.amountCls : '') });
        let extra = 0;
        if (o.exp) {
          const ax = o.expAnchor === undefined ? barX + barW : sx(o.expAnchor);
          const room = ax - barX - 6;
          if (!narrow && room >= textW(o.exp, 11)) {
            svgText(svg, ax - 4, by + BH - 3, o.exp, { class: 'tpm-exp' + (o.expCls ? ' ' + o.expCls : ''), 'text-anchor': 'end' });
          } else {
            svgText(svg, barX, by + BH + 12, fit(o.exp, W - barX - PAD, 11), { class: 'tpm-exp' + (o.expCls ? ' ' + o.expCls : '') });
            extra = 15;
          }
        }
        y += RH + extra;
      };

      // 1. GROSS
      wRow({ label: 'GROSS (DocTotal)', strong: true, bars: gross === null ? [] : [{ from: 0, to: gross, fill: C.grossFill, opacity: 1 }], amount: gross === null ? null : money(gross), na: 'not computed — gross missing on the bill row' });

      // 2. TDS — lives on the bill (WTSum); WtAppld at payment is 0 everywhere
      if (tds !== null && gross !== null) {
        let exp = '', expCls = '';
        if (inv.tdsApplied !== null && Math.abs(inv.tdsApplied - tds) > 0.5) {
          exp = `WTApplied ${money(inv.tdsApplied)}${inv.tdsApplied === 0 ? ' — SAP never applied the TDS' : ' — cross-check only'}`;
          expCls = inv.tdsApplied === 0 ? 'warn' : '';
        }
        wRow({ label: '− TDS (WTSum, on the bill)', bars: [{ from: afterTds, to: gross, fill: C.warn, min: tds > 0 ? 1.5 : 0 }], amount: tds > 0 ? '− ' + money(tds) : money(tds), amountCls: tds > 0 ? 'warn' : '', exp, expCls, expAnchor: afterTds });
      } else wRow({ label: '− TDS (WTSum, on the bill)', amount: null, na: 'not computed — TDS missing on the bill row' });

      // 3. DISCOUNT — 0 on every bill today; the column stays (FACTS §4)
      if (disc !== null && afterTds !== null) {
        wRow({ label: '− DISCOUNT (DiscSum)', bars: disc > 0 ? [{ from: afterDisc, to: afterTds, fill: C.warn, opacity: .6 }] : [], amount: disc > 0 ? '− ' + money(disc) : money(disc), amountCls: disc > 0 ? 'warn' : '', exp: disc === 0 ? 'recorded as 0 on the bill' : '', expAnchor: afterTds });
      } else wRow({ label: '− DISCOUNT (DiscSum)', amount: null, na: 'not computed — discount missing on the bill row' });

      // 4. OTHER DEDUCTION — the residual. Never a known figure, never a
      //    confident zero: null means "no payment line, so no balancing figure".
      if (other === null || afterDisc === null) {
        wRow({ label: '− OTHER DEDUCTION (residual)', amount: null, na: 'not computed — no payment line on this bill, so no balancing figure' });
      } else if (Math.abs(other) <= 1) {
        wRow({ label: '− OTHER DEDUCTION (residual)', amount: money(other), exp: 'reconciles: gross − TDS − discount = net paid', expAnchor: afterDisc });
      } else if (other > 1) {
        wRow({ label: '− OTHER DEDUCTION (residual)', bars: [{ from: afterDisc - other, to: afterDisc, fill: C.danger, opacity: .8 }], amount: '− ' + money(other), amountCls: 'neg', exp: narrow ? 'unexplained — shortage/damage or settled by journal' : 'unexplained — shortage/damage claim or settled by journal', expCls: 'danger', expAnchor: afterDisc - other });
      } else {
        const isTds = tds !== null && Math.abs(-other - tds) <= 1;
        wRow({ label: '− OTHER DEDUCTION (residual)', bars: [{ from: afterDisc, to: afterDisc - other, fill: C.warn, dash: '3 2' }], amount: '+ ' + money(-other), amountCls: 'warn',
          exp: isTds ? (narrow ? 'added back: full gross paid — TDS NOT deducted at payment (WTApplied = 0)' : 'added back: the full gross was paid — TDS on the bill was NOT deducted at payment (WTApplied = 0)') : 'added back: paid above gross − TDS − discount; unexplained', expCls: 'warn', expAnchor: afterDisc });
      }

      // 5. NET PAID — Σ SumApplied on this bill across ALL payments; this
      //    payment's share is the darker segment.
      if (net !== null) {
        const mine = s.amount;
        const bars = [{ from: 0, to: net, fill: C.ok, opacity: .35, min: net > 0 ? 1.5 : 0 }, { from: 0, to: Math.min(mine, net), fill: C.ok, opacity: .85, min: mine > 0 ? 1.5 : 0 }];
        let exp = '';
        if (Math.abs(net - mine) > 1) {
          const others = inv.payNums.split(',').map(v => v.trim()).filter(v => v && v !== p.docNum);
          exp = `this payment ${money(mine)} · rest ${money(net - mine)} by ${others.length ? others.join(', ') : 'other payment(s)'}`;
        }
        wRow({ label: '= NET PAID (all payments)', strong: true, bars, amount: money(net), exp, expAnchor: 0 });
        if (inv.paidToDate !== null && Math.abs(inv.paidToDate - net) > 1) {
          svgText(svg, barX, y + 8, fit(`SAP PaidToDate ${money(inv.paidToDate)} ≠ net paid ${money(net)} — ${narrow ? 'gap closed by JE / credit note / on-account, not a payment' : 'the gap was closed by something other than a payment (JE / credit note / on-account reconciliation)'}`, W - barX - PAD, 11), { class: 'tpm-exp warn' });
          y += 16;
        }
      } else wRow({ label: '= NET PAID (all payments)', strong: true, amount: null });
      svgEl('line', { class: 'tpm-tick', x1: barX, y1: tickTop, x2: barX, y2: y - 6 }, svg);
      y += 10;
    }
    if (!bills.length && segs.length) {
      svgText(svg, PAD, y + 10, 'This payment settled no A/P invoice line — see the documents above.', { class: 'tpm-exp' });
      y += 20;
    }
    if (!segs.length) {
      svgText(svg, PAD, y + 10, 'No allocation line: nothing to break down per bill. The money sits on the vendor account until someone matches it in SAP.', { class: 'tpm-exp' });
      y += 20;
    }
    const H = Math.ceil(y + PAD);
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('width', W);
    svg.setAttribute('height', H);
    state.widthDrawn = W;
  }

  draw();
  if (typeof ResizeObserver !== 'undefined') {
    state.observer = new ResizeObserver(() => {
      const w = Math.floor(measure());
      if (Math.abs(w - state.widthDrawn) > 24) draw();
    });
    state.observer.observe(wrap);
  }
  const ctl = { payment: p, segments: segs, destroy() { if (state.observer) state.observer.disconnect(); el.__tpm = null; } };
  el.__tpm = ctl;
  return ctl;
}

export default { renderMapping, renderPaymentMap, buildMappingModel };
