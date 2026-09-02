/**
 * core.js — the shared ES module for the JIVO "Transporter-wise Details" board.
 *
 * Every page imports this and nothing else. No framework, no CDN, no build step.
 * Pure ES module; no imports. Works from a static host (Vercel) and from a local
 * static server. NOTE: opened straight from disk (file://) every mainstream
 * browser blocks fetch() of the data files — loadCompany() then returns a
 * structured error with the fix in `error.hint` instead of a blank page.
 *
 * DATA CONTRACT (read from the real files in site/data/, 2026-08-22 build).
 * Column names are SQL-cased exactly as the pipeline writes them — never
 * lowercased or renamed here. All DocEntry / DocNum keys are STRINGS.
 *
 *   <section>.<co>.json = { section, company, company_label, schema, as_of,
 *                           generated_at, sql_file, columns[], numeric_columns[],
 *                           rows[], row_count, error }        (error: null | "reason")
 *   A failed refresh ships rows:[] + error:"reason" (or keeps the previous good
 *   file and the manifest entry says kept_previous / stale_since).
 *
 *   master      CARD_CODE CARD_NAME FIRST_ACTIVITY LAST_ACTIVITY INV_CNT INV_GROSS
 *               INV_TDS INV_DISC PAY_CNT PAY_TOTAL MATCHED_APPLIED ONACCT_PAY_CNT
 *               ONACCT_PAY_AMT BALANCE OPEN_INV_CNT FLAG_CNT
 *               (BALANCE = OCRD."Balance" verbatim, all-time, not windowed)
 *   invoices    DOC_ENTRY DOC_NUM CARD_CODE CARD_NAME DOC_DATE TAX_DATE DUE_DATE
 *               VENDOR_BILL BRANCH GROSS VAT BASE TDS TDS_APPLIED DISCOUNT NET_PAID
 *               OTHER_DEDUCTION RESIDUAL_FLAG PAID_TO_DATE DOC_STATUS PAY_CNT
 *               PAY_NUMS SETTLED_BY
 *               (OTHER_DEDUCTION is NULL — never 0 — on every PAY_CNT=0 row;
 *                PAY_NUMS is a comma-joined list of payment DOC_NUMs, '' if none)
 *   payments    DOC_ENTRY DOC_NUM CARD_CODE CARD_NAME DOC_DATE PAY_TOTAL CASH_SUM
 *               CHECK_SUM TRSFR_SUM TRSFR_REF TRSFR_DATE ALLOC_CNT ALLOC_TOTAL
 *               INV_CNT INV_APPLIED CN_APPLIED JE_APPLIED OTHER_APPLIED UNALLOCATED
 *               MATCH_FLAG REMARKS
 *   allocations PAY_DOC_ENTRY PAY_DOC_NUM PAY_DATE CARD_CODE CARD_NAME INV_TYPE
 *               INV_TYPE_LABEL TGT_DOC_ENTRY TGT_DOC_NUM TGT_DATE TGT_VENDOR_BILL
 *               TGT_GROSS TGT_TDS SUM_APPLIED WT_APPLD DCNT_SUM IN_WINDOW
 *               (one row per VPM2 line; (payment, type, target) is NOT unique — a
 *                payment can hit several lines of one JE. NEVER dedupe.
 *                TGT_* are null when IN_WINDOW='N' or the type is not an invoice.
 *                SUM_APPLIED is negative on InvType 46 and sometimes 30: real.)
 *
 * FLAG VOCABULARY (FACTS §9 / §5):
 *   RESIDUAL_FLAG  UNPAID | OK | GROSS_PAID | SHORT | OVER | PART_TDS
 *   MATCH_FLAG     MATCHED | ON_ACCOUNT | PARTIAL
 *   INV_TYPE       18 A/P Invoice · 19 A/P Credit Note · 30 Journal Entry ·
 *                  46 Outgoing Payment · 24/13/14 contra · anything else = OTHER
 */

export const VERSION = '2026-08-22.1';
export const NOT_COMPUTED = 'not computed';

/* ───────────────────────────── companies & theme ───────────────────────────── */

export const COMPANIES = Object.freeze({
  oil:  Object.freeze({ key: 'oil',  label: 'JIVO Wellness (Oil)', short: 'Oil',       schema: 'JIVO_OIL_HANADB',       accent: '#b45309' }),
  mart: Object.freeze({ key: 'mart', label: 'JIVO Mart',           short: 'Mart',      schema: 'JIVO_MART_HANADB',      accent: '#6d28d9' }),
  bev:  Object.freeze({ key: 'bev',  label: 'JIVO Beverages',      short: 'Beverages', schema: 'JIVO_BEVERAGES_HANADB', accent: '#0e7490' }),
});
export const COMPANY_ORDER = Object.freeze(['oil', 'mart', 'bev']);
export const SECTIONS = Object.freeze(['master', 'invoices', 'payments', 'allocations']);

/** Semantic colours from the shared design direction. */
export const COLORS = Object.freeze({
  ok: '#067647', warn: '#b54708', danger: '#b42318', neutral: '#475467', onacct: '#6941c6',
  ink: '#14181f', muted: '#667085', hairline: '#eaecf0', border: '#e3e6ea', page: '#f6f7f9', card: '#ffffff',
});

/** Normalise any spelling of a company to its key, or null. Accepts 'Oil', 'bev', 'JIVO_MART_HANADB'… */
export function companyKey(x) {
  if (x == null) return null;
  const s = String(x).trim().toLowerCase();
  if (COMPANIES[s]) return s;
  for (const c of COMPANY_ORDER) {
    const co = COMPANIES[c];
    if (s === co.schema.toLowerCase() || s === co.label.toLowerCase() || s === co.short.toLowerCase()) return c;
  }
  if (s.startsWith('bev')) return 'bev';
  if (s.startsWith('oil') || s.includes('wellness')) return 'oil';
  if (s.startsWith('mart')) return 'mart';
  return null;
}
export function companyOf(x) { const k = companyKey(x); return k ? COMPANIES[k] : null; }

/** Tint the document for one company: sets data-company and --accent on <html>. Safe without a DOM. */
export function applyCompany(co) {
  const c = companyOf(co);
  if (!c || typeof document === 'undefined' || !document.documentElement) return c;
  const root = document.documentElement;
  root.dataset.company = c.key;
  root.style.setProperty('--accent', c.accent);
  return c;
}

/* ───────────────────────────── fiscal years ───────────────────────────── */
/* JIVO names a fiscal year by its STARTING calendar year: FY26 = 1 Apr 2026 – 31 Mar 2027. */

export const FY = Object.freeze({
  FY26: Object.freeze({ key: 'FY26', label: 'FY26 (Apr 2026 – Mar 2027)', short: 'FY26', from: '2026-04-01', to: '2027-03-31' }),
  FY25: Object.freeze({ key: 'FY25', label: 'FY25 (Apr 2025 – Mar 2026)', short: 'FY25', from: '2025-04-01', to: '2026-03-31' }),
  ALL:  Object.freeze({ key: 'ALL',  label: 'Both years (Apr 2025 onwards)', short: 'All', from: '2025-04-01', to: null }),
});
export const FY_ORDER = Object.freeze(['FY26', 'FY25', 'ALL']);
export const DEFAULT_FY = 'FY26';
export const FETCH_WINDOW_FROM = '2025-04-01';

/** 'YYYY-MM-DD' -> 'FY26' (Apr–Mar). Returns null when the string is not a date. */
export function fyOf(dateStr) {
  const p = parseDate(dateStr);
  if (!p) return null;
  const start = p.m >= 4 ? p.y : p.y - 1;
  return 'FY' + String(start).slice(-2);
}
export function fyKey(x) {
  if (x == null) return DEFAULT_FY;
  const s = String(x).trim().toUpperCase();
  if (FY[s]) return s;
  if (/^FY\d\d$/.test(s)) return s;
  return DEFAULT_FY;
}
export function inFY(dateStr, key) {
  const k = fyKey(key);
  if (k === 'ALL') return true;
  const f = FY[k];
  if (f) return typeof dateStr === 'string' && dateStr >= f.from && (!f.to || dateStr <= f.to);
  return fyOf(dateStr) === k;
}
/** Filter rows whose `field` (default DOC_DATE) falls in the fiscal year. Allocations use PAY_DATE. */
export function filterFY(rows, key, field = 'DOC_DATE') {
  const k = fyKey(key);
  if (k === 'ALL') return rows.slice();
  return rows.filter(r => inFY(r[field], k));
}

/* ───────────────────────────── numbers & money ───────────────────────────── */

/** number | numeric string -> finite number, else null. Never coerces null/'' to 0. */
export function toNum(v) {
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'string' && v.trim() !== '') {
    const n = Number(v.replace(/,/g, ''));
    return Number.isFinite(n) ? n : null;
  }
  return null;
}
export function isNum(v) { return typeof v === 'number' && Number.isFinite(v); }

/** '1234567' -> '12,34,567' (Indian grouping; digits-only input). */
export function groupIndian(intStr) {
  const s = String(intStr);
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  let rest = s.slice(0, -3);
  const parts = [];
  while (rest.length > 2) { parts.unshift(rest.slice(-2)); rest = rest.slice(0, -2); }
  if (rest) parts.unshift(rest);
  return parts.join(',') + ',' + last3;
}

/**
 * Rupees with Indian grouping. 0 dp unless opts.paise (2 dp) or opts.dp.
 * null/undefined/NaN -> 'not computed' (opts.empty to override). Negative -> leading '-'.
 * opts.symbol -> '₹' prefix ( '-₹1,234' when negative ). opts.sign -> '+' on positives.
 */
export function fmtINR(n, opts = {}) {
  const v = toNum(n);
  if (v === null) return opts.empty !== undefined ? opts.empty : NOT_COMPUTED;
  const dp = opts.paise ? 2 : (isNum(opts.dp) ? opts.dp : 0);
  const fixed = Math.abs(v).toFixed(dp);
  const neg = v < 0 && Number(fixed) !== 0;
  const [int, frac] = fixed.split('.');
  let out = groupIndian(int) + (frac ? '.' + frac : '');
  if (opts.symbol) out = '₹' + out;
  if (neg) out = '-' + out;
  else if (opts.sign && v > 0) out = '+' + out;
  return out;
}
/** Plain number, Indian grouping, opts.dp decimals (default 0). null -> 'not computed'. */
export function fmtNum(n, opts = {}) { return fmtINR(n, { dp: 0, ...opts, symbol: false }); }

function fmtScaled(n, div, suffix, opts) {
  const v = toNum(n);
  if (v === null) return opts.empty !== undefined ? opts.empty : NOT_COMPUTED;
  const dp = isNum(opts.dp) ? opts.dp : 2;
  return fmtINR(v / div, { ...opts, dp }) + suffix;
}
/** Lakhs, 2 dp: 9701234 -> '97.01 L'. Headline use only — never mix units inside one column. */
export function fmtLakh(n, opts = {}) { return fmtScaled(n, 1e5, opts.unit !== undefined ? opts.unit : ' L', opts); }
/** Crores, 2 dp: 12345678 -> '1.23 Cr'. */
export function fmtCr(n, opts = {}) { return fmtScaled(n, 1e7, opts.unit !== undefined ? opts.unit : ' Cr', opts); }
/** Picks Cr / L / exact rupees by magnitude. KPI tiles only. */
export function fmtCompact(n, opts = {}) {
  const v = toNum(n);
  if (v === null) return opts.empty !== undefined ? opts.empty : NOT_COMPUTED;
  const a = Math.abs(v);
  if (a >= 1e7) return fmtCr(v, opts);
  if (a >= 1e5) return fmtLakh(v, opts);
  return fmtINR(v, opts);
}
export function fmtPct(n, dp = 1, opts = {}) {
  const v = toNum(n);
  if (v === null) return opts.empty !== undefined ? opts.empty : NOT_COMPUTED;
  return v.toFixed(dp) + '%';
}
/** 'neg' | 'pos' | '' — for colouring a figure. */
export function signClass(n) { const v = toNum(n); return v === null ? '' : v < 0 ? 'neg' : v > 0 ? 'pos' : ''; }

/* ───────────────────────────── dates ───────────────────────────── */

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTH_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

/** Parses 'YYYY-MM-DD' or an ISO datetime string (or a Date) -> {y,m,d,hh,mm,tz} without timezone shifting. */
export function parseDate(s) {
  if (s instanceof Date) {
    if (isNaN(s)) return null;
    return { y: s.getFullYear(), m: s.getMonth() + 1, d: s.getDate(), hh: s.getHours(), mm: s.getMinutes(), tz: null };
  }
  if (typeof s !== 'string') return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?\s*(Z|[+-]\d{2}:?\d{2})?)?/.exec(s.trim());
  if (!m) return null;
  const y = +m[1], mo = +m[2], d = +m[3];
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
  return { y, m: mo, d, hh: m[4] != null ? +m[4] : null, mm: m[5] != null ? +m[5] : null, tz: m[6] || null };
}
/** '2026-08-04' -> '04 Aug 2026'. opts.style: 'short' -> '04 Aug 26', 'long' -> '4 August 2026', 'numeric' -> '04-08-2026'. Missing -> '—'. */
export function fmtDate(s, opts = {}) {
  const p = parseDate(s);
  if (!p) return opts.empty !== undefined ? opts.empty : '—';
  const dd = String(p.d).padStart(2, '0');
  const MM = String(p.m).padStart(2, '0');
  switch (opts.style) {
    case 'short':   return `${dd} ${MON[p.m - 1]} ${String(p.y).slice(-2)}`;
    case 'long':    return `${p.d} ${MONTH_LONG[p.m - 1]} ${p.y}`;
    case 'numeric': return `${dd}-${MM}-${p.y}`;
    case 'iso':     return `${p.y}-${MM}-${dd}`;
    default:        return `${dd} ${MON[p.m - 1]} ${p.y}`;
  }
}
/** '2026-08-22T22:50:30+05:30' -> '22 Aug 2026, 22:50 IST'. Printed from the string — no timezone shift. */
export function fmtDateTime(s, opts = {}) {
  const p = parseDate(s);
  if (!p) return opts.empty !== undefined ? opts.empty : '—';
  const date = fmtDate(s, opts);
  if (p.hh == null) return date;
  const tz = p.tz === '+05:30' || p.tz === '+0530' ? 'IST' : p.tz === 'Z' ? 'UTC' : p.tz ? 'UTC' + p.tz : '';
  return `${date}, ${String(p.hh).padStart(2, '0')}:${String(p.mm).padStart(2, '0')}${tz ? ' ' + tz : ''}`;
}
/** Whole days from a to b ('YYYY-MM-DD' strings or Dates). null when either is missing. */
export function daysBetween(a, b) {
  const pa = parseDate(a), pb = parseDate(b);
  if (!pa || !pb) return null;
  return Math.round((Date.UTC(pb.y, pb.m - 1, pb.d) - Date.UTC(pa.y, pa.m - 1, pa.d)) / 86400000);
}
/** Age in days of a dated row as of `asOf` (defaults to today). */
export function ageDays(dateStr, asOf) {
  return daysBetween(dateStr, asOf || todayISO());
}
export function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/* ───────────────────────────── flags & chips ───────────────────────────── */

/** RESIDUAL_FLAG vocabulary (FACTS §9) in evaluation order. Never call GROSS_PAID "overpaid". */
export const RESIDUAL_FLAGS = Object.freeze({
  UNPAID:     Object.freeze({ flag: 'UNPAID',     kind: 'invoice', tone: 'neutral', cls: 'chip chip-neutral', label: 'Unpaid',
                              title: 'No payment touches this bill (no non-cancelled allocation line).' }),
  OK:         Object.freeze({ flag: 'OK',         kind: 'invoice', tone: 'ok',      cls: 'chip chip-ok',      label: 'Reconciles',
                              title: 'Paid net of TDS: gross − TDS − discount = net paid (within ₹1).' }),
  GROSS_PAID: Object.freeze({ flag: 'GROSS_PAID', kind: 'invoice', tone: 'warn',    cls: 'chip chip-warn',    label: 'Paid gross — TDS not deducted',
                              title: 'Paid in full. The TDS held on the bill (WTSum) was not deducted at payment — WTApplied = 0 on this invoice in SAP. A TDS-compliance question, not an overpayment.' }),
  SHORT:      Object.freeze({ flag: 'SHORT',      kind: 'invoice', tone: 'warn',    cls: 'chip chip-warn',    label: 'Short-paid',
                              title: 'Paid less than gross − TDS. The gap is unexplained — shortage/damage claim or settled by journal. Look at it.' }),
  OVER:       Object.freeze({ flag: 'OVER',       kind: 'invoice', tone: 'danger',  cls: 'chip chip-danger',  label: 'Paid above bill',
                              title: 'Net paid exceeds the gross bill by more than ₹1 — genuinely over-paid.' }),
  PART_TDS:   Object.freeze({ flag: 'PART_TDS',   kind: 'invoice', tone: 'warn',    cls: 'chip chip-warn',    label: 'Partial TDS',
                              title: 'Something was deducted at payment, but less than the TDS on the bill.' }),
});
export const RESIDUAL_ORDER = Object.freeze(['UNPAID', 'OK', 'GROSS_PAID', 'SHORT', 'OVER', 'PART_TDS']);

/** MATCH_FLAG vocabulary (FACTS §5). */
export const MATCH_FLAGS = Object.freeze({
  MATCHED:    Object.freeze({ flag: 'MATCHED',    kind: 'payment', tone: 'ok',     cls: 'chip chip-ok',     label: 'Matched',
                              title: 'Allocated lines equal the payment (within ₹1).' }),
  ON_ACCOUNT: Object.freeze({ flag: 'ON_ACCOUNT', kind: 'payment', tone: 'onacct', cls: 'chip chip-onacct', label: 'Paid, not yet matched to a bill',
                              title: 'No allocation line at all — money paid against no document (on-account).' }),
  PARTIAL:    Object.freeze({ flag: 'PARTIAL',    kind: 'payment', tone: 'warn',   cls: 'chip chip-warn',   label: 'Partly matched',
                              title: 'Allocated lines do not equal the payment. If a credit note is among the lines the netted view may tie exactly — check before chasing it.' }),
});
export const MATCH_ORDER = Object.freeze(['MATCHED', 'PARTIAL', 'ON_ACCOUNT']);

/** {cls,label,tone,title,flag,kind} for any RESIDUAL_FLAG / MATCH_FLAG value. Unknown -> neutral chip with the raw value; empty -> 'not computed'. */
export function chipFor(flag) {
  if (flag == null || flag === '') {
    return { flag: '', kind: 'unknown', tone: 'neutral', cls: 'chip chip-nc', label: NOT_COMPUTED, title: 'No flag on this row.' };
  }
  const f = String(flag).trim().toUpperCase();
  if (RESIDUAL_FLAGS[f]) return RESIDUAL_FLAGS[f];
  if (MATCH_FLAGS[f]) return MATCH_FLAGS[f];
  return { flag: f, kind: 'unknown', tone: 'neutral', cls: 'chip chip-unknown', label: f, title: 'Flag value not in the board vocabulary — shown raw, not dropped.' };
}

/** VPM2.InvType vocabulary (FACTS §3). Unknown types are labelled, never dropped. */
export const INV_TYPES = Object.freeze({
  '18': Object.freeze({ type: '18', kind: 'invoice',     label: 'A/P Invoice',      short: 'Invoice',      table: 'OPCH' }),
  '19': Object.freeze({ type: '19', kind: 'credit-note', label: 'A/P Credit Note',  short: 'Credit note',  table: 'ORPC', note: 'reduces what is owed' }),
  '30': Object.freeze({ type: '30', kind: 'journal',     label: 'Journal Entry',    short: 'Journal',      table: 'OJDT', note: 'manual settlement — settled by JE' }),
  '46': Object.freeze({ type: '46', kind: 'payment',     label: 'Outgoing Payment', short: 'On-account',   table: 'OVPM', note: 'earlier on-account payment applied here; amount is negative' }),
  '24': Object.freeze({ type: '24', kind: 'contra',      label: 'Incoming Payment', short: 'Incoming pmt', table: 'ORCT', note: 'contra' }),
  '13': Object.freeze({ type: '13', kind: 'contra',      label: 'A/R Invoice',      short: 'A/R invoice',  table: 'OINV', note: 'contra' }),
  '14': Object.freeze({ type: '14', kind: 'contra',      label: 'A/R Credit Note',  short: 'A/R CN',       table: 'ORIN', note: 'contra' }),
});
export function invType(t) {
  const k = t == null ? '' : String(t).trim();
  return INV_TYPES[k] || { type: k, kind: 'other', label: `OTHER (InvType=${k || '?'})`, short: `Other (${k || '?'})`, table: null, note: 'unexpected line type — shown, not dropped' };
}
export function invTypeLabel(t) { return invType(t).label; }

/* ───────────────────────────── state (company + filters) ───────────────────────────── */
/* Persisted (localStorage, try/catch): company, fy, flag, tab.  URL-only: vendor, q.
 * URL query keys: co, fy, vendor, q, flag, tab.  URL beats storage beats defaults at load. */

const STORAGE_KEY = 'jivo.transporter.board.v1';
const PERSIST_KEYS = ['company', 'fy', 'flag', 'tab'];
const URL_KEYS = Object.freeze({ company: 'co', fy: 'fy', vendor: 'vendor', q: 'q', flag: 'flag', tab: 'tab' });
const DEFAULTS = Object.freeze({ company: 'oil', fy: DEFAULT_FY, vendor: '', q: '', flag: '', tab: '' });

function cleanStr(v, max = 200) { return v == null ? '' : String(v).slice(0, max); }
function sanitizeState(s) {
  const out = { ...DEFAULTS };
  out.company = companyKey(s.company) || DEFAULTS.company;
  out.fy = fyKey(s.fy);
  out.vendor = cleanStr(s.vendor, 40).trim();
  out.q = cleanStr(s.q, 200);
  const flag = cleanStr(s.flag, 20).trim().toUpperCase();
  out.flag = flag && (RESIDUAL_FLAGS[flag] || MATCH_FLAGS[flag]) ? flag : '';
  out.tab = cleanStr(s.tab, 40).trim();
  return out;
}
function readStorage() {
  try {
    if (typeof localStorage === 'undefined') return null;
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : null;
  } catch (_) { return null; }
}
function writeStorage(s) {
  try {
    if (typeof localStorage === 'undefined') return;
    const keep = {};
    for (const k of PERSIST_KEYS) keep[k] = s[k];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keep));
  } catch (_) { /* private mode, quota, sandbox — never break the page */ }
}
function readURL() {
  try {
    if (typeof location === 'undefined' || !location.search) return {};
    const p = new URLSearchParams(location.search);
    const out = {};
    for (const [k, q] of Object.entries(URL_KEYS)) if (p.has(q)) out[k] = p.get(q);
    if (p.has('company') && !p.has('co')) out.company = p.get('company');
    return out;
  } catch (_) { return {}; }
}
function queryString(s, extra = {}) {
  const merged = { ...s, ...extra };
  const p = new URLSearchParams();
  // company is always carried (first) so a shared link opens the right book
  p.set('co', companyKey(merged.company) || DEFAULTS.company);
  for (const [k, q] of Object.entries(URL_KEYS)) {
    if (k === 'company') continue;
    const v = merged[k];
    if (v != null && v !== '') p.set(q, String(v));
  }
  return p.toString();
}
function writeURL(s) {
  try {
    if (typeof history === 'undefined' || typeof location === 'undefined') return;
    const qs = queryString(s);
    const next = location.pathname + (qs ? '?' + qs : '') + location.hash;
    if (next !== location.pathname + location.search + location.hash) history.replaceState(history.state, '', next);
  } catch (_) { /* file:// in some browsers refuses replaceState — ignore */ }
}

/** The live state object. Mutate only through setState(); read freely. */
export const state = sanitizeState({ ...DEFAULTS, ...(readStorage() || {}), ...readURL() });

const listeners = new Set();
/** subscribe(fn(state, changedKeys, prevState)) -> unsubscribe. */
export function subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); }
/** Merge a patch, persist, mirror to the URL (opts.url=false to skip), notify subscribers. Returns state. */
export function setState(patch, opts = {}) {
  const prev = { ...state };
  const next = sanitizeState({ ...state, ...(patch || {}) });
  const changed = Object.keys(next).filter(k => next[k] !== prev[k]);
  if (!changed.length) return state;
  Object.assign(state, next);
  writeStorage(state);
  if (opts.url !== false) writeURL(state);
  for (const fn of listeners) {
    try { fn(state, changed, prev); } catch (e) { console.error('[core] subscriber failed', e); }
  }
  return state;
}
export function getState() { return { ...state }; }
export function resetState() { return setState({ ...DEFAULTS }); }
/** Build a link to another page carrying company + filters: hrefFor('vendor.html', {vendor:'VENDA000636'}). Page string is passed through untouched. */
export function hrefFor(page, params = {}) {
  const qs = queryString(state, params);
  let hash = '';
  let base = page || '';
  const h = base.indexOf('#');
  if (h >= 0) { hash = base.slice(h); base = base.slice(0, h); }
  return base + (qs ? '?' + qs : '') + hash;
}
export function isFileProtocol() {
  try { return typeof location !== 'undefined' && location.protocol === 'file:'; } catch (_) { return false; }
}

/* ───────────────────────────── loading ───────────────────────────── */

let dataBase = (() => {
  try { return new URL('../data/', import.meta.url).href; } catch (_) { return 'data/'; }
})();
const companyCache = new Map();
let manifestPromise = null;

/** Point the loader at another data folder (absolute or relative URL). Clears caches. */
export function setDataBase(url) {
  dataBase = String(url).endsWith('/') ? String(url) : String(url) + '/';
  companyCache.clear();
  manifestPromise = null;
}
export function getDataBase() { return dataBase; }
export function dataURL(file) { return dataBase + file; }
export function clearCache() { companyCache.clear(); manifestPromise = null; }

function fetchHint(url) {
  if (isFileProtocol()) {
    return 'Opened from disk: browsers block reading data/*.json over file://. Serve the site folder instead — '
      + '`cd site && python3 -m http.server 8000` then open http://localhost:8000/ — or open the Vercel URL.';
  }
  return `Could not reach ${url}. Check the network, or that site/data/ was deployed with the page.`;
}

async function readJSON(file) {
  // A page may pre-load data as <script> globals (globalThis.__TRANSPORTER_DATA__[file] = {...}); honoured first.
  try {
    const pre = typeof globalThis !== 'undefined' ? globalThis.__TRANSPORTER_DATA__ : null;
    if (pre && pre[file] && typeof pre[file] === 'object') return { ok: true, json: pre[file], url: 'preloaded:' + file };
  } catch (_) { /* ignore */ }
  const url = dataURL(file);
  if (typeof fetch !== 'function') return { ok: false, code: 'NO_FETCH', message: 'fetch() is not available in this environment', url, hint: '' };
  let res;
  try {
    res = await fetch(url, { cache: 'no-cache' });
  } catch (e) {
    return { ok: false, code: 'FETCH_FAILED', message: (e && e.message) || String(e), url, hint: fetchHint(url) };
  }
  if (!res.ok) {
    return {
      ok: false, code: 'HTTP_' + res.status, message: `HTTP ${res.status} ${res.statusText || ''}`.trim(), url,
      hint: res.status === 404 ? `${file} is missing — run pipeline/build.py and redeploy.` : 'The data host answered with an error.',
    };
  }
  try {
    return { ok: true, json: await res.json(), url };
  } catch (e) {
    return { ok: false, code: 'BAD_JSON', message: (e && e.message) || String(e), url, hint: `${file} is not valid JSON — a half-written build?` };
  }
}

/** manifest.json -> {ok:true, manifest} | {ok:false, error:{code,message,hint,url}}. Cached. */
export function loadManifest(opts = {}) {
  if (!manifestPromise || opts.force) {
    manifestPromise = readJSON('manifest.json').then(r => (r.ok ? { ok: true, manifest: r.json } : { ok: false, manifest: null, error: r }));
  }
  return manifestPromise;
}

/** Columns every page relies on. Missing ones are reported as warnings, not silently undefined. */
const REQUIRED_COLUMNS = Object.freeze({
  master: ['CARD_CODE', 'CARD_NAME', 'INV_CNT', 'INV_GROSS', 'INV_TDS', 'PAY_CNT', 'PAY_TOTAL', 'ONACCT_PAY_CNT', 'ONACCT_PAY_AMT', 'BALANCE', 'FLAG_CNT'],
  invoices: ['DOC_ENTRY', 'DOC_NUM', 'CARD_CODE', 'CARD_NAME', 'DOC_DATE', 'VENDOR_BILL', 'GROSS', 'TDS', 'DISCOUNT', 'NET_PAID', 'OTHER_DEDUCTION', 'RESIDUAL_FLAG', 'PAY_CNT'],
  payments: ['DOC_ENTRY', 'DOC_NUM', 'CARD_CODE', 'CARD_NAME', 'DOC_DATE', 'PAY_TOTAL', 'ALLOC_CNT', 'ALLOC_TOTAL', 'UNALLOCATED', 'MATCH_FLAG'],
  allocations: ['PAY_DOC_ENTRY', 'PAY_DOC_NUM', 'PAY_DATE', 'CARD_CODE', 'INV_TYPE', 'TGT_DOC_ENTRY', 'SUM_APPLIED', 'IN_WINDOW'],
});

function errorResult(co, code, message, hint = '') {
  const c = companyOf(co);
  const d = {
    ok: false, company: c ? c.key : String(co), label: c ? c.label : String(co), short: c ? c.short : String(co),
    schema: c ? c.schema : null, accent: c ? c.accent : COLORS.neutral,
    as_of: null, generated_at: null, manifest: null, manifestError: null,
    files: {}, sections: {}, errors: [{ section: null, file: null, code, message, hint }], warnings: [],
    master: [], invoices: [], payments: [], allocations: [],
    error: { code, message, hint, sections: [] },
  };
  for (const s of SECTIONS) d.sections[s] = { section: s, file: null, ok: false, rows: 0, error: message, code, hint, stale: false, stale_since: null, kept_previous: false };
  d.idx = buildIndexes(d);
  return d;
}

async function doLoad(key) {
  const c = COMPANIES[key];
  const [mf, ...secs] = await Promise.all([loadManifest(), ...SECTIONS.map(s => readJSON(`${s}.${key}.json`))]);
  const manifest = mf.ok ? mf.manifest : null;
  const d = {
    ok: true, company: key, label: c.label, short: c.short, schema: c.schema, accent: c.accent,
    as_of: null, generated_at: null, manifest, manifestError: mf.ok ? null : mf.error,
    buildOk: manifest ? manifest.ok !== false : null,
    files: {}, sections: {}, errors: [], warnings: [],
    master: [], invoices: [], payments: [], allocations: [],
    error: null, idx: null,
  };
  if (!mf.ok) d.warnings.push(`manifest.json not loaded (${mf.error.code}: ${mf.error.message}) — freshness unknown`);
  if (manifest && Array.isArray(manifest.errors)) for (const e of manifest.errors) d.warnings.push(`last build: ${e}`);

  SECTIONS.forEach((s, i) => {
    const r = secs[i];
    const file = `${s}.${key}.json`;
    const mfe = manifest && manifest.sections && manifest.sections[s] ? (manifest.sections[s][key] || null) : null;
    const st = {
      section: s, file, ok: false, rows: 0, error: null, code: null, hint: '',
      stale: false, stale_since: null, kept_previous: false,
      sha256: mfe && mfe.sha256 ? mfe.sha256 : null, seconds: mfe && isNum(mfe.seconds) ? mfe.seconds : null,
      source: r.ok ? r.url : null,
    };
    if (!r.ok) {
      st.error = r.message; st.code = r.code; st.hint = r.hint || '';
      d.errors.push({ section: s, file, code: r.code, message: r.message, hint: r.hint || '', url: r.url });
    } else {
      const j = r.json && typeof r.json === 'object' ? r.json : {};
      d.files[s] = j;
      const rows = Array.isArray(j.rows) ? j.rows : [];
      if (j.error) {
        st.error = String(j.error); st.code = 'PIPELINE_ERROR';
        st.hint = 'The last build could not refresh this section and had no previous good file; see manifest.json.';
        d.errors.push({ section: s, file, code: st.code, message: st.error, hint: st.hint });
      } else if (!rows.length) {
        st.error = 'file has no rows'; st.code = 'EMPTY';
        st.hint = 'The pipeline never publishes an empty section on purpose — rebuild.';
        d.errors.push({ section: s, file, code: st.code, message: st.error, hint: st.hint });
      } else {
        st.ok = true; st.rows = rows.length; d[s] = rows;
        if (!d.as_of && j.as_of) d.as_of = j.as_of;
        if (!d.generated_at && j.generated_at) d.generated_at = j.generated_at;
        const cols = Array.isArray(j.columns) && j.columns.length ? j.columns : Object.keys(rows[0] || {});
        const missing = REQUIRED_COLUMNS[s].filter(k => !cols.includes(k));
        if (missing.length) d.warnings.push(`${file}: missing column(s) ${missing.join(', ')} — figures depending on them will show "not computed"`);
        if (j.row_count != null && j.row_count !== rows.length) d.warnings.push(`${file}: row_count ${j.row_count} ≠ ${rows.length} rows in file`);
        if (mfe && mfe.rows != null && mfe.rows !== rows.length) d.warnings.push(`${file}: manifest says ${mfe.rows} rows, file has ${rows.length} — a half-deployed build?`);
      }
      if (mfe && (mfe.kept_previous || mfe.error)) {
        st.stale = true; st.stale_since = mfe.stale_since || null; st.kept_previous = !!mfe.kept_previous;
        d.warnings.push(`${file}: last refresh failed (${mfe.error || 'unknown'}); showing the previous build${mfe.stale_since ? ' from ' + fmtDateTime(mfe.stale_since) : ''}`);
      }
    }
    d.sections[s] = st;
  });

  if (manifest) {
    if (!d.as_of && manifest.as_of) d.as_of = manifest.as_of;
    if (!d.generated_at && manifest.generated_at) d.generated_at = manifest.generated_at;
  }
  d.ok = d.errors.length === 0;
  if (!d.ok) {
    const first = d.errors[0];
    const names = d.errors.map(e => e.section).filter(Boolean);
    d.error = {
      code: first.code,
      message: names.length ? `${names.join(', ')} could not be loaded for ${c.label}: ${first.message}` : first.message,
      hint: first.hint || '',
      sections: names,
    };
  }
  d.idx = buildIndexes(d);
  return d;
}

/**
 * Load + cache one company's master/invoices/payments/allocations + manifest.
 * Always resolves (never rejects) to:
 *   { ok, company, label, short, schema, accent, as_of, generated_at, manifest,
 *     master[], invoices[], payments[], allocations[],      <- ROW ARRAYS
 *     files{section: raw payload}, sections{section: status}, errors[], warnings[],
 *     error: null | {code, message, hint, sections[]},  idx: buildIndexes(d) }
 * Partial failures keep whatever did load (ok=false, error names the sections).
 */
export function loadCompany(co, opts = {}) {
  const key = companyKey(co);
  if (!key) {
    return Promise.resolve(errorResult(co, 'UNKNOWN_COMPANY', `Unknown company "${co}"`, `Use one of ${COMPANY_ORDER.join(', ')}.`));
  }
  if (!opts.force && companyCache.has(key)) return companyCache.get(key);
  const p = doLoad(key).then(
    d => { if (!d.ok) companyCache.delete(key); return d; },
    e => { companyCache.delete(key); return errorResult(key, 'INTERNAL', (e && e.message) || String(e), 'core.js hit an unexpected error while loading — see the console.'); },
  );
  companyCache.set(key, p);
  return p;
}

/** 'as of 22 Aug 2026 · built 22 Aug 2026, 22:50 IST' — or a plain statement that freshness is unknown. */
export function asOfLabel(d) {
  if (!d) return 'freshness unknown';
  const parts = [];
  if (d.as_of) parts.push('as of ' + fmtDate(d.as_of));
  if (d.generated_at) parts.push('built ' + fmtDateTime(d.generated_at));
  return parts.length ? parts.join(' · ') : 'freshness unknown (manifest not loaded)';
}

/* ───────────────────────────── indexes ───────────────────────────── */

const k = v => (v == null ? '' : String(v).trim());
const EMPTY = Object.freeze([]);
function push(map, key, row) { const a = map.get(key); if (a) a.push(row); else map.set(key, [row]); }
function byDateDesc(field) { return (a, b) => (b[field] || '').localeCompare(a[field] || ''); }

/**
 * Build every lookup the board runs on, once, in memory.
 * Allocation lookups are keyed by (INV_TYPE, TGT_DOC_ENTRY): a Journal Entry's DocEntry can
 * collide numerically with an invoice DocEntry, so a bare TGT_DOC_ENTRY key would be wrong.
 */
export function buildIndexes(d) {
  const master = Array.isArray(d.master) ? d.master : [];
  const invoices = Array.isArray(d.invoices) ? d.invoices : [];
  const payments = Array.isArray(d.payments) ? d.payments : [];
  const allocations = Array.isArray(d.allocations) ? d.allocations : [];

  const byInvoiceEntry = new Map(), byInvoiceNum = new Map();
  const byPaymentEntry = new Map(), byPaymentNum = new Map();
  const byVendorCode = new Map();
  const allocsByPayment = new Map(), allocsByInvoice = new Map(), allocsByTarget = new Map();
  const vendorMap = new Map();
  const vend = code => {
    let v = vendorMap.get(code);
    if (!v) { v = { code, name: '', master: null, invoices: [], payments: [], allocations: [] }; vendorMap.set(code, v); }
    return v;
  };

  for (const m of master) {
    const code = k(m.CARD_CODE);
    byVendorCode.set(code, m);
    const v = vend(code); v.master = m; if (m.CARD_NAME) v.name = m.CARD_NAME;
  }
  for (const r of invoices) {
    byInvoiceEntry.set(k(r.DOC_ENTRY), r);
    byInvoiceNum.set(k(r.DOC_NUM), r);
    const v = vend(k(r.CARD_CODE)); v.invoices.push(r); if (!v.name && r.CARD_NAME) v.name = r.CARD_NAME;
  }
  for (const p of payments) {
    byPaymentEntry.set(k(p.DOC_ENTRY), p);
    byPaymentNum.set(k(p.DOC_NUM), p);
    const v = vend(k(p.CARD_CODE)); v.payments.push(p); if (!v.name && p.CARD_NAME) v.name = p.CARD_NAME;
  }
  for (const a of allocations) {
    const type = k(a.INV_TYPE), tgt = k(a.TGT_DOC_ENTRY);
    push(allocsByPayment, k(a.PAY_DOC_ENTRY), a);
    push(allocsByTarget, type + ':' + tgt, a);
    if (type === '18') push(allocsByInvoice, tgt, a);
    const v = vend(k(a.CARD_CODE)); v.allocations.push(a); if (!v.name && a.CARD_NAME) v.name = a.CARD_NAME;
  }
  for (const v of vendorMap.values()) {
    v.invoices.sort(byDateDesc('DOC_DATE'));
    v.payments.sort(byDateDesc('DOC_DATE'));
    v.allocations.sort(byDateDesc('PAY_DATE'));
  }

  const idx = {
    byInvoiceEntry, byInvoiceNum, byPaymentEntry, byPaymentNum, byVendorCode,
    allocsByPayment, allocsByInvoice, allocsByTarget, vendorMap,
    vendors: master.slice(),
    counts: { master: master.length, invoices: invoices.length, payments: payments.length, allocations: allocations.length },

    /** invoice row by DOC_ENTRY (or DOC_NUM), else null */
    invoice(id) { const s = k(id); return byInvoiceEntry.get(s) || byInvoiceNum.get(s) || null; },
    /** payment row by DOC_ENTRY (or DOC_NUM), else null */
    payment(id) { const s = k(id); return byPaymentEntry.get(s) || byPaymentNum.get(s) || null; },
    /** master row by CARD_CODE, else null */
    vendor(code) { return byVendorCode.get(k(code)) || null; },

    /** allocation rows (InvType 18) that pay this invoice DocEntry — every VPM2 line, never deduped */
    paymentsForInvoice(docEntry) { return allocsByInvoice.get(k(docEntry)) || EMPTY; },
    /** every allocation row of this payment DocEntry — ALL InvTypes, nothing dropped */
    invoicesForPayment(docEntry) { return allocsByPayment.get(k(docEntry)) || EMPTY; },
    /** allocation rows for any target: (INV_TYPE, TGT_DOC_ENTRY) */
    allocsFor(type, docEntry) { return allocsByTarget.get(k(type) + ':' + k(docEntry)) || EMPTY; },

    /** distinct payment rows that touched this invoice, newest first; a payment outside the file still appears as {DOC_ENTRY, DOC_NUM, missing:true} */
    paymentsOfInvoice(docEntry) {
      const seen = new Map();
      for (const a of this.paymentsForInvoice(docEntry)) {
        const pe = k(a.PAY_DOC_ENTRY);
        if (seen.has(pe)) continue;
        seen.set(pe, byPaymentEntry.get(pe) || { DOC_ENTRY: pe, DOC_NUM: a.PAY_DOC_NUM, DOC_DATE: a.PAY_DATE, CARD_CODE: a.CARD_CODE, CARD_NAME: a.CARD_NAME, missing: true });
      }
      return [...seen.values()].sort(byDateDesc('DOC_DATE'));
    },
    /** [{alloc, target, invoice|null}] for every line of a payment, in file order */
    invoicesOfPayment(docEntry) {
      return this.invoicesForPayment(docEntry).map(a => ({ alloc: a, target: describeTarget(a, idx), invoice: this.invoiceForAlloc(a) }));
    },
    /** invoice row an allocation line points at (InvType 18 and in window), else null */
    invoiceForAlloc(a) { return k(a.INV_TYPE) === '18' ? (byInvoiceEntry.get(k(a.TGT_DOC_ENTRY)) || null) : null; },
    /** payment row an allocation line belongs to, else null */
    paymentForAlloc(a) { return byPaymentEntry.get(k(a.PAY_DOC_ENTRY)) || null; },
    /** describeTarget shortcut */
    target(a) { return describeTarget(a, idx); },

    /** {code, name, master, invoices[], payments[], allocations[]} — empty lists (and unknown:true) for a code nobody has seen */
    byVendor(cardCode) {
      const v = vendorMap.get(k(cardCode));
      return v || { code: k(cardCode), name: '', master: null, invoices: EMPTY, payments: EMPTY, allocations: EMPTY, unknown: true };
    },
  };
  return idx;
}

/**
 * What an allocation line points at, in operator language. Never blank:
 * an invoice outside the fetch window renders as "(invoice outside window) DocEntry N".
 */
export function describeTarget(a, idx) {
  const t = invType(a.INV_TYPE);
  const docEntry = k(a.TGT_DOC_ENTRY);
  const docNum = a.TGT_DOC_NUM != null && a.TGT_DOC_NUM !== '' ? String(a.TGT_DOC_NUM) : null;
  const inWindow = a.IN_WINDOW === 'Y';
  const invoice = idx && t.kind === 'invoice' ? (idx.byInvoiceEntry.get(docEntry) || null) : null;
  const out = {
    type: t.type, kind: t.kind, typeLabel: a.INV_TYPE_LABEL || t.label, table: t.table, note: t.note || '',
    docEntry, docNum, date: a.TGT_DATE || null, vendorBill: a.TGT_VENDOR_BILL || null,
    gross: toNum(a.TGT_GROSS), tds: toNum(a.TGT_TDS), applied: toNum(a.SUM_APPLIED),
    inWindow, invoice, outsideWindow: false, text: '',
  };
  switch (t.kind) {
    case 'invoice':
      if (invoice || (inWindow && docNum)) {
        out.text = `Invoice ${docNum || (invoice && invoice.DOC_NUM) || 'DocEntry ' + docEntry}`;
        const bill = out.vendorBill || (invoice && invoice.VENDOR_BILL);
        if (bill) out.text += ` · bill ${bill}`;
      } else {
        out.outsideWindow = true;
        out.text = `(invoice outside window) DocEntry ${docEntry}`;
      }
      break;
    case 'credit-note': out.text = `A/P Credit Note ${docNum || 'DocEntry ' + docEntry} — reduces what is owed`; break;
    case 'journal':     out.text = `Journal Entry DocEntry ${docEntry} — settled by JE`; break;
    case 'payment':     out.text = `Earlier on-account payment DocEntry ${docEntry}, applied here`; break;
    case 'contra':      out.text = `${t.label} DocEntry ${docEntry} (contra)`; break;
    default:            out.text = `${t.label} DocEntry ${docEntry}`;
  }
  return out;
}

/* ───────────────────────────── reconciliation helpers ───────────────────────────── */

/**
 * The per-invoice reconciliation line (FACTS §4):
 *   GROSS − TDS − DISCOUNT − OTHER_DEDUCTION = NET_PAID
 * plus WHICH TDS behaviour this bill shows. `residual` is null (not 0) when unpaid.
 * tds: 'UNPAID' | 'NO_TDS' | 'WITHHELD' | 'NOT_WITHHELD' | 'PARTIAL' | 'MORE_THAN_TDS' | 'OVER' | 'UNKNOWN'
 */
export function reconcile(inv) {
  const gross = toNum(inv.GROSS), tds = toNum(inv.TDS), disc = toNum(inv.DISCOUNT), net = toNum(inv.NET_PAID);
  const residual = toNum(inv.OTHER_DEDUCTION);
  const payCnt = toNum(inv.PAY_CNT) || 0;
  const flag = inv.RESIDUAL_FLAG || '';
  const out = {
    gross, tds, discount: disc, netPaid: net, residual, flag, chip: chipFor(flag),
    tdsApplied: toNum(inv.TDS_APPLIED), payCnt, tds: 'UNKNOWN', explain: '',
    residualLabel: residual === null ? NOT_COMPUTED : fmtINR(residual, { paise: true }),
    residualNote: 'unexplained — shortage/damage claim or settled by journal',
  };
  if (payCnt === 0 || flag === 'UNPAID') {
    out.tds = 'UNPAID'; out.explain = 'No payment yet — nothing to reconcile.'; return out;
  }
  if (gross === null || net === null) { out.tds = 'UNKNOWN'; out.explain = 'Gross or net paid missing — cannot reconcile.'; return out; }
  const tdsAmt = tds || 0;
  const gap = gross - net;
  if (tdsAmt <= 0) {
    out.tds = 'NO_TDS';
    out.explain = Math.abs(gap) <= 1 ? 'No TDS on this bill; paid in full.' : gap > 1 ? `No TDS on this bill; short by ${fmtINR(gap)} (unexplained).` : `No TDS on this bill; paid ${fmtINR(-gap)} above it.`;
  } else if (Math.abs(gap - tdsAmt - (disc || 0)) <= 1) {
    out.tds = 'WITHHELD'; out.explain = `TDS ${fmtINR(tdsAmt)} withheld from the payment — reconciles.`;
  } else if (Math.abs(gap) <= 1) {
    out.tds = 'NOT_WITHHELD'; out.explain = `Full gross paid. TDS ${fmtINR(tdsAmt)} on the bill was NOT deducted at payment (WTApplied = ${fmtINR(out.tdsApplied, { empty: '?' })}).`;
  } else if (gap < -1) {
    out.tds = 'OVER'; out.explain = `Paid ${fmtINR(-gap)} above the bill.`;
  } else if (gap > tdsAmt + 1) {
    out.tds = 'MORE_THAN_TDS'; out.explain = `Deducted ${fmtINR(gap)} — that is TDS ${fmtINR(tdsAmt)} plus ${fmtINR(gap - tdsAmt)} unexplained.`;
  } else {
    out.tds = 'PARTIAL'; out.explain = `Deducted ${fmtINR(gap)}, less than the TDS of ${fmtINR(tdsAmt)}.`;
  }
  return out;
}

/**
 * Netted view of a payment (pipeline note): INV_APPLIED − CN_APPLIED + JE_APPLIED + OTHER_APPLIED = PAY_TOTAL
 * holds to the paisa on every payment that carries a credit-note line, even though MATCH_FLAG says PARTIAL.
 * Returns {net, ties, hasCN, diff}. net is null if any component is missing.
 */
export function paymentNet(p) {
  const inv = toNum(p.INV_APPLIED), cn = toNum(p.CN_APPLIED), je = toNum(p.JE_APPLIED), oth = toNum(p.OTHER_APPLIED), tot = toNum(p.PAY_TOTAL);
  if ([inv, cn, je, oth, tot].some(x => x === null)) return { net: null, ties: false, hasCN: !!cn, diff: null };
  const net = inv - cn + je + oth;
  const diff = tot - net;
  return { net, ties: Math.abs(diff) <= 1, hasCN: cn !== 0, diff };
}
/**
 * MATCH_FLAG as the operator should read it: a PARTIAL that ties net of a credit note is reported as
 * {flag:'MATCHED', derived:true, note}. The row's MATCH_FLAG itself is never altered.
 */
export function effectiveMatch(p) {
  const raw = p.MATCH_FLAG || '';
  if (raw === 'PARTIAL') {
    const n = paymentNet(p);
    if (n.hasCN && n.ties) return { flag: 'MATCHED', raw, derived: true, chip: chipFor('MATCHED'), note: 'matched net of credit note' };
  }
  return { flag: raw, raw, derived: false, chip: chipFor(raw), note: '' };
}
/** Meaning of master.BALANCE (OCRD.Balance, all-time): positive = debit (vendor owes JIVO / advance held), negative = credit (JIVO owes vendor). */
export function balanceMeaning(n) {
  const v = toNum(n);
  if (v === null) return { side: null, label: NOT_COMPUTED, short: NOT_COMPUTED };
  if (v > 0) return { side: 'debit', label: 'Vendor owes JIVO / advance held', short: 'Dr' };
  if (v < 0) return { side: 'credit', label: 'JIVO owes vendor', short: 'Cr' };
  return { side: 'nil', label: 'Nil per SAP ledger', short: 'nil' };
}

/* ───────────────────────────── sums & aggregates ───────────────────────────── */

/** {value, n, missing}: value = sum of finite values (0 for an empty list); null only if rows exist and none is finite. */
export function sumInfo(rows, field) {
  let value = 0, n = 0, missing = 0;
  for (const r of rows) { const v = toNum(r[field]); if (v === null) missing++; else { value += v; n++; } }
  if (rows.length && n === 0) value = null;
  return { value, n, missing };
}
export function sum(rows, field) { return sumInfo(rows, field).value; }
export function uniq(arr) { return [...new Set(arr)]; }
/** Stable sort copy. dir 'asc'|'desc'. Nulls always last. Strings compared case-insensitively. */
export function sortRows(rows, field, dir = 'asc') {
  const sgn = dir === 'desc' ? -1 : 1;
  return rows.map((r, i) => [r, i]).sort((a, b) => {
    const va = a[0][field], vb = b[0][field];
    const na = va == null || va === '', nb = vb == null || vb === '';
    if (na && nb) return a[1] - b[1];
    if (na) return 1;
    if (nb) return -1;
    let c;
    if (typeof va === 'number' && typeof vb === 'number') c = va - vb;
    else c = String(va).localeCompare(String(vb), undefined, { numeric: true, sensitivity: 'base' });
    return c !== 0 ? c * sgn : a[1] - b[1];
  }).map(x => x[0]);
}

/**
 * Totals for ONE company's rows (never pass two books' rows together).
 * aggregate(invoices, payments) -> { inv:{count, gross, vat, base, tds, discount, netPaid, residual:{value,n,missing}, byFlag},
 *                                    pay:{count, total, cash, cheque, transfer, invApplied, cnApplied, jeApplied, otherApplied,
 *                                         unallocated, onAccount:{count, amount}, byFlag} }
 * byFlag[FLAG] = {count, gross|total, netPaid} with every vocabulary flag present (count 0 when absent) plus any unknown flag seen.
 */
export function aggregate(invoices = [], payments = []) {
  const inv = {
    count: invoices.length,
    gross: sum(invoices, 'GROSS'), vat: sum(invoices, 'VAT'), base: sum(invoices, 'BASE'),
    tds: sum(invoices, 'TDS'), tdsApplied: sum(invoices, 'TDS_APPLIED'), discount: sum(invoices, 'DISCOUNT'),
    netPaid: sum(invoices, 'NET_PAID'), residual: sumInfo(invoices, 'OTHER_DEDUCTION'),
    byFlag: {},
  };
  for (const f of RESIDUAL_ORDER) inv.byFlag[f] = { flag: f, count: 0, gross: 0, netPaid: 0, tds: 0 };
  for (const r of invoices) {
    const f = r.RESIDUAL_FLAG || 'UNKNOWN';
    const b = inv.byFlag[f] || (inv.byFlag[f] = { flag: f, count: 0, gross: 0, netPaid: 0, tds: 0 });
    b.count++; b.gross += toNum(r.GROSS) || 0; b.netPaid += toNum(r.NET_PAID) || 0; b.tds += toNum(r.TDS) || 0;
  }
  const pay = {
    count: payments.length,
    total: sum(payments, 'PAY_TOTAL'), cash: sum(payments, 'CASH_SUM'), cheque: sum(payments, 'CHECK_SUM'), transfer: sum(payments, 'TRSFR_SUM'),
    allocTotal: sum(payments, 'ALLOC_TOTAL'), invApplied: sum(payments, 'INV_APPLIED'), cnApplied: sum(payments, 'CN_APPLIED'),
    jeApplied: sum(payments, 'JE_APPLIED'), otherApplied: sum(payments, 'OTHER_APPLIED'), unallocated: sum(payments, 'UNALLOCATED'),
    onAccount: { count: 0, amount: 0 },
    byFlag: {},
  };
  for (const f of MATCH_ORDER) pay.byFlag[f] = { flag: f, count: 0, total: 0 };
  for (const p of payments) {
    const f = p.MATCH_FLAG || 'UNKNOWN';
    const b = pay.byFlag[f] || (pay.byFlag[f] = { flag: f, count: 0, total: 0 });
    b.count++; b.total += toNum(p.PAY_TOTAL) || 0;
    if (f === 'ON_ACCOUNT') { pay.onAccount.count++; pay.onAccount.amount += toNum(p.PAY_TOTAL) || 0; }
  }
  return { inv, pay };
}

/**
 * Apply the board's filters consistently to one company's data.
 * filters: {fy, vendor, flag}. Invoices/payments filter on DOC_DATE, allocations on PAY_DATE.
 * `flag` applies to whichever table owns it (RESIDUAL_FLAG -> invoices, MATCH_FLAG -> payments).
 */
export function applyFilters(d, filters = {}) {
  const fy = fyKey(filters.fy || state.fy);
  const vendor = k(filters.vendor);
  const flag = (filters.flag || '').toUpperCase();
  const keep = (row, dateField) => inFY(row[dateField], fy) && (!vendor || k(row.CARD_CODE) === vendor);
  let invoices = (d.invoices || []).filter(r => keep(r, 'DOC_DATE'));
  let payments = (d.payments || []).filter(r => keep(r, 'DOC_DATE'));
  const allocations = (d.allocations || []).filter(r => keep(r, 'PAY_DATE'));
  if (flag && RESIDUAL_FLAGS[flag]) invoices = invoices.filter(r => r.RESIDUAL_FLAG === flag);
  if (flag && MATCH_FLAGS[flag]) payments = payments.filter(r => r.MATCH_FLAG === flag);
  return { fy, vendor, flag, invoices, payments, allocations, totals: aggregate(invoices, payments) };
}

/** One vendor, one fiscal year: {vendor, master, invoices, payments, allocations, totals, firstActivity, lastActivity}. */
export function vendorSummary(d, cardCode, fy) {
  const idx = d.idx || buildIndexes(d);
  const v = idx.byVendor(cardCode);
  const f = applyFilters({ invoices: v.invoices, payments: v.payments, allocations: v.allocations }, { fy, vendor: v.code });
  const dates = [...f.invoices.map(r => r.DOC_DATE), ...f.payments.map(r => r.DOC_DATE)].filter(Boolean).sort();
  return {
    vendor: v.code, name: v.name || (v.master && v.master.CARD_NAME) || '', master: v.master, unknown: !!v.unknown,
    fy: f.fy, invoices: f.invoices, payments: f.payments, allocations: f.allocations, totals: f.totals,
    firstActivity: dates[0] || null, lastActivity: dates[dates.length - 1] || null,
  };
}

/* ───────────────────────────── search ───────────────────────────── */

function norm(s) { return s == null ? '' : String(s).toLowerCase().replace(/\s+/g, ' ').trim(); }
function scoreField(hay, q) {
  if (!hay) return 0;
  if (hay === q) return 3;
  if (hay.startsWith(q)) return 2;
  if (hay.includes(q)) return 1;
  return 0;
}
function scoreRow(fields, q, tokens) {
  let best = 0;
  for (const f of fields) { const s = scoreField(f, q); if (s > best) best = s; }
  if (best) return best;
  if (tokens.length > 1) { const joined = fields.join(' '); if (tokens.every(t => joined.includes(t))) return 1; }
  return 0;
}
const TYPE_RANK = { vendor: 0, invoice: 1, payment: 2, target: 3 };

/**
 * One search box across vendor name/code, invoice DocNum + vendor bill number, payment DocNum.
 * Case-insensitive substring (exact > prefix > substring; multi-word queries also match as AND).
 * opts: {limit=50, fy, vendor, deep} — deep also scans payment REMARKS / TRSFR_REF.
 * Returns typed hits: {type:'vendor'|'invoice'|'payment'|'target', key, title, sub, date, amount, flag, score, row, params}
 * `params` is ready for hrefFor(page, params).
 */
export function search(d, q, opts = {}) {
  const nq = norm(q);
  if (!nq) return [];
  const tokens = nq.split(' ').filter(Boolean);
  const limit = isNum(opts.limit) ? opts.limit : 50;
  const fy = opts.fy ? fyKey(opts.fy) : null;
  const vendor = k(opts.vendor);
  const idx = d.idx || buildIndexes(d);
  const hits = [];

  for (const v of idx.vendorMap.values()) {
    if (vendor && v.code !== vendor) continue;
    const s = scoreRow([norm(v.name), norm(v.code)], nq, tokens);
    if (!s) continue;
    const m = v.master;
    hits.push({
      type: 'vendor', key: v.code, title: v.name || v.code, sub: v.code,
      date: m ? m.LAST_ACTIVITY : null, amount: m ? toNum(m.INV_GROSS) : null, flag: '',
      score: s, row: m || v, params: { vendor: v.code },
    });
  }
  for (const r of d.invoices || []) {
    if (fy && !inFY(r.DOC_DATE, fy)) continue;
    if (vendor && k(r.CARD_CODE) !== vendor) continue;
    const entry = k(r.DOC_ENTRY);
    let s = scoreRow([norm(r.DOC_NUM), norm(r.VENDOR_BILL)], nq, tokens);
    if (!s && entry === nq) s = 3;
    if (!s) continue;
    hits.push({
      type: 'invoice', key: entry, title: `Invoice ${r.DOC_NUM}`, sub: `${r.CARD_NAME} · bill ${r.VENDOR_BILL || '—'} · ${fmtDate(r.DOC_DATE)}`,
      date: r.DOC_DATE, amount: toNum(r.GROSS), flag: r.RESIDUAL_FLAG || '',
      score: s, row: r, params: { vendor: k(r.CARD_CODE), inv: entry },
    });
  }
  for (const p of d.payments || []) {
    if (fy && !inFY(p.DOC_DATE, fy)) continue;
    if (vendor && k(p.CARD_CODE) !== vendor) continue;
    const entry = k(p.DOC_ENTRY);
    const fields = [norm(p.DOC_NUM)];
    if (opts.deep) fields.push(norm(p.TRSFR_REF), norm(p.REMARKS));
    let s = scoreRow(fields, nq, tokens);
    if (!s && entry === nq) s = 3;
    if (!s) continue;
    hits.push({
      type: 'payment', key: entry, title: `Payment ${p.DOC_NUM}`, sub: `${p.CARD_NAME} · ${fmtDate(p.DOC_DATE)}`,
      date: p.DOC_DATE, amount: toNum(p.PAY_TOTAL), flag: p.MATCH_FLAG || '',
      score: s, row: p, params: { vendor: k(p.CARD_CODE), pay: entry },
    });
  }
  // Targets a payment points at that are NOT in the invoice file (outside window / other doc types) — still findable.
  const seenTarget = new Set();
  for (const a of d.allocations || []) {
    if (fy && !inFY(a.PAY_DATE, fy)) continue;
    if (vendor && k(a.CARD_CODE) !== vendor) continue;
    if (idx.invoiceForAlloc(a)) continue;
    const tkey = k(a.INV_TYPE) + ':' + k(a.TGT_DOC_ENTRY);
    if (seenTarget.has(tkey)) continue;
    let s = scoreRow([norm(a.TGT_DOC_NUM), norm(a.TGT_VENDOR_BILL)], nq, tokens);
    if (!s && k(a.TGT_DOC_ENTRY) === nq) s = 3;
    if (!s) continue;
    seenTarget.add(tkey);
    const t = describeTarget(a, idx);
    hits.push({
      type: 'target', key: tkey, title: t.text, sub: `${a.CARD_NAME} · via payment ${a.PAY_DOC_NUM} on ${fmtDate(a.PAY_DATE)}`,
      date: a.PAY_DATE, amount: toNum(a.SUM_APPLIED), flag: '',
      score: s, row: a, params: { vendor: k(a.CARD_CODE), pay: k(a.PAY_DOC_ENTRY) },
    });
  }
  hits.sort((a, b) => (b.score - a.score) || (TYPE_RANK[a.type] - TYPE_RANK[b.type]) || ((b.date || '').localeCompare(a.date || '')));
  return hits.slice(0, limit);
}

/* ───────────────────────────── DOM helpers ───────────────────────────── */

const SVG_NS = 'http://www.w3.org/2000/svg';
function isNode(x) { return typeof Node !== 'undefined' && x instanceof Node; }
function appendChildren(node, kids) {
  for (const c of kids) {
    if (c == null || c === false || c === true) continue;
    if (Array.isArray(c)) { appendChildren(node, c); continue; }
    if (isNode(c)) { node.appendChild(c); continue; }
    node.appendChild(document.createTextNode(String(c)));
  }
}
function setAttrs(node, attrs, svg) {
  for (const [key, val] of Object.entries(attrs)) {
    if (val == null || val === false) continue;
    if (key === 'class' || key === 'className') {
      const cls = Array.isArray(val) ? val.filter(Boolean).join(' ') : String(val);
      if (svg) node.setAttribute('class', cls); else node.className = cls;
    } else if (key === 'style') {
      if (typeof val === 'string') node.style.cssText = val; else Object.assign(node.style, val);
    } else if (key === 'dataset') {
      for (const [dk, dv] of Object.entries(val)) if (dv != null) node.dataset[dk] = String(dv);
    } else if (key.startsWith('on') && typeof val === 'function') {
      node.addEventListener(key.slice(2).toLowerCase(), val);
    } else if (key === 'html') {
      node.innerHTML = String(val); // trusted literal markup only (inline SVG icons); never user/data text
    } else if (key === 'text') {
      node.textContent = String(val);
    } else if (!svg && typeof val === 'boolean' && key in node) {
      node[key] = val; // checked, disabled, hidden, selected…
    } else if (val === true) {
      node.setAttribute(key, '');
    } else {
      node.setAttribute(key, String(val));
    }
  }
}
/**
 * el('td', {class:'num money', title:'…', onClick: fn, dataset:{x:1}}, 'text', childNode, [more])
 * Attrs may be omitted: el('span', 'text'). null/false/true children are skipped; arrays flatten.
 */
export function el(tag, attrs, ...children) {
  if (attrs != null && (typeof attrs !== 'object' || Array.isArray(attrs) || isNode(attrs))) { children.unshift(attrs); attrs = null; }
  const node = document.createElement(tag);
  if (attrs) setAttrs(node, attrs, false);
  appendChildren(node, children);
  return node;
}
/** Same as el() for hand-written SVG: svgEl('svg', {viewBox:'0 0 100 10'}, svgEl('rect', {...})). */
export function svgEl(tag, attrs, ...children) {
  if (attrs != null && (typeof attrs !== 'object' || Array.isArray(attrs) || isNode(attrs))) { children.unshift(attrs); attrs = null; }
  const node = document.createElementNS(SVG_NS, tag);
  if (attrs) setAttrs(node, attrs, true);
  appendChildren(node, children);
  return node;
}
export function text(s) { return document.createTextNode(s == null ? '' : String(s)); }
export function clear(node) { while (node && node.firstChild) node.removeChild(node.firstChild); return node; }
/** Replace a node's children. */
export function mount(node, ...children) { clear(node); appendChildren(node, children); return node; }
export function frag(...children) { const f = document.createDocumentFragment(); appendChildren(f, children); return f; }
export function escapeHTML(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}
export function debounce(fn, ms = 150) {
  let t = null;
  return function (...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
}

/**
 * <span class="num money [neg] [nc]">12,34,567</span> — right-align + tabular-nums via the shared CSS.
 * opts: fmtINR opts + {compact:true} (Cr/L with the exact rupees in the title), {reason} for the not-computed tooltip.
 */
export function moneyEl(n, opts = {}) {
  const v = toNum(n);
  const cls = ['num', 'money', opts.class];
  if (v === null) {
    cls.push('nc');
    return el('span', { class: cls, title: opts.reason || 'Not computed — no value for this cell.' }, opts.empty !== undefined ? opts.empty : NOT_COMPUTED);
  }
  if (v < 0) cls.push('neg');
  const label = opts.compact ? fmtCompact(v, opts) : fmtINR(v, opts);
  const title = opts.title !== undefined ? opts.title : (opts.compact ? '₹' + fmtINR(v, { paise: true }) : null);
  return el('span', { class: cls, title }, label);
}
/** <span class="num [neg]">…</span> for counts. */
export function numEl(n, opts = {}) {
  const v = toNum(n);
  if (v === null) return el('span', { class: ['num', 'nc', opts.class], title: opts.reason || 'Not computed.' }, NOT_COMPUTED);
  return el('span', { class: ['num', v < 0 && 'neg', opts.class] }, fmtNum(v, opts));
}
/** <span class="chip chip-warn" data-flag="SHORT" title="…">Short-paid</span>. opts.short uses the raw flag as the label. */
export function chipEl(flag, opts = {}) {
  const c = chipFor(flag);
  return el('span', { class: [c.cls, opts.class], dataset: { flag: c.flag, tone: c.tone }, title: opts.title !== undefined ? opts.title : c.title }, opts.short ? (c.flag || c.label) : c.label);
}
/** <span class="nc" title="reason">not computed</span> — the only way to render an uncomputable figure. */
export function ncEl(reason) {
  return el('span', { class: 'nc', title: reason || 'Not computed.' }, NOT_COMPUTED);
}
/** A standard inline notice: tone 'info'|'warn'|'danger'. */
export function noticeEl(tone, title, detail) {
  return el('div', { class: ['notice', 'notice-' + (tone || 'info')], role: tone === 'danger' ? 'alert' : 'status' },
    el('strong', title), detail ? el('span', { class: 'notice-detail' }, ' ', detail) : null);
}
/** Render a loadCompany() result's problems (errors + stale warnings) as notice elements; [] when all clean. */
export function loadNotices(d) {
  const out = [];
  if (!d) return out;
  if (!d.ok && d.error) out.push(noticeEl('danger', d.error.message, d.error.hint));
  for (const w of d.warnings || []) out.push(noticeEl('warn', w));
  return out;
}
