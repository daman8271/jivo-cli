/**
 * charts.js — hand-written SVG charts for the JIVO Accounts Board v2.
 *
 * No library, no CDN, no build step. Every export is a pure function that
 * returns a DOM element you can append straight into a card.
 *
 * ── The contract every chart honours ──────────────────────────────────────
 *  • Returns an element. With `{table:false}` that element is the `<svg>`;
 *    otherwise (the default — see below) it is a `.chartwrap` `<div>` holding
 *    the SVG plus a `<details>` disclosure containing the same numbers as a
 *    `<table>`. Either way the returned node exposes `.chartSvg`.
 *  • **The table is ON by default.** Two steps of the ageing ramp sit under
 *    3:1 on cream, so the numbers must always be reachable without colour.
 *    `sparkline()` is the one exception (it is a micro-mark inside a KPI tile
 *    whose value is already printed beside it) — pass `{table:true}` there.
 *  • Responsive: `viewBox` + `preserveAspectRatio`, `width:100%`. The chart
 *    re-renders at its measured pixel width (ResizeObserver), so one SVG user
 *    unit is one CSS pixel and 12px text is 12px at 390px wide and at 1100px.
 *  • Every mark carries a visible value label where the label fits, and always
 *    a `<title>`; the SVG carries an `aria-label`. Nothing relies on colour.
 *  • Colours are resolved from CSS variables AT RENDER TIME. Marks are painted
 *    with live `var(--x)` references so a theme flip repaints instantly, and
 *    `getComputedStyle` values are used for the decisions that need a real
 *    colour (label ink over a fill, ramp mixing). `retheme()` re-resolves and
 *    re-renders every live chart; it is also wired to `data-theme` changes
 *    automatically, so pages normally need not call it.
 *  • Categorical series take `--c1..--c6` in fixed order and are never cycled;
 *    a 7th category folds into "Other (n)" and the n is stated.
 *  • Ageing takes `--age-nd` (not due — a state, brand green) then
 *    `--age1..--age6`, in that order, never reordered.
 *  • `--ok/--warn/--bad/--info/--dead` are status only, never a data series.
 *  • `{href:(item,i)=>url}` makes marks clickable, keyboard reachable and
 *    focus-ringed.
 *  • Empty input, a single point, all zeros, negatives and one value 1000x the
 *    rest all render something honest — never blank, never broken.
 *
 * Shared options (every chart):
 *   title       string   small heading drawn inside the SVG
 *   note        string   muted footnote under the plot
 *   table       boolean  emit the `<details>` table (default true)
 *   href        fn       (item, index) -> url, makes marks links
 *   format      fn       (value) -> string, overrides the money formatter
 *                        (pass `money` from core.js to share one formatter)
 *   unit        'INR'|'n'|'%'|'d'   used when `format` is absent (default INR)
 *   width       number   force a design width instead of measuring
 *   height      number   plot height where the chart has a free height
 *   ariaLabel   string   overrides the generated description
 *
 * @module charts
 */

/* ══ 1. tokens ═══════════════════════════════════════════════════════════ */

const NS = 'http://www.w3.org/2000/svg';
const FONT = 'system-ui,-apple-system,"Segoe UI",Roboto,sans-serif';

/** Fixed categorical order. Never cycled — a 7th series becomes "Other". */
const CAT = ['--c1', '--c2', '--c3', '--c4', '--c5', '--c6'];
/** Ageing ramp. "Not due" is a STATE (brand green), then the ramp. Never reordered. */
const AGE = ['--age-nd', '--age1', '--age2', '--age3', '--age4', '--age5', '--age6'];

const TOKENS = [
  '--brand', '--brand-deep', '--ink', '--sage', '--soft', '--cream', '--card',
  '--card-warm', '--line', '--line-soft',
  '--c1', '--c2', '--c3', '--c4', '--c5', '--c6',
  '--age-nd', '--age1', '--age2', '--age3', '--age4', '--age5', '--age6',
  '--ok', '--warn', '--bad', '--info', '--dead'
];

/**
 * Last-resort values (CONTRACT §6, daylight). These are NOT the palette — the
 * palette is read live from CSS. They are used only when `getComputedStyle`
 * returns nothing at all (stylesheet not yet applied, or a non-browser test
 * harness), so a chart still draws instead of coming out invisible.
 */
const FALLBACK = {
  '--brand': '#0A7D3F', '--brand-deep': '#1F3524', '--ink': '#22301F',
  '--sage': '#586055', '--soft': '#8B9184', '--cream': '#F5F4EF',
  '--card': '#FFFFFF', '--card-warm': '#FAF9F4', '--line': '#E4E2D6',
  '--line-soft': '#ECEAE0',
  '--c1': '#0A7D3F', '--c2': '#1D63C4', '--c3': '#C2610A',
  '--c4': '#8B2E9E', '--c5': '#0894B0', '--c6': '#B01253',
  '--age-nd': '#0A7D3F', '--age1': '#D99A4E', '--age2': '#C97F2E',
  '--age3': '#B5651B', '--age4': '#9A4D12', '--age5': '#7D370D', '--age6': '#5A2108',
  '--ok': '#0A7D3F', '--warn': '#935800', '--bad': '#B3261E',
  '--info': '#1D5F8A', '--dead': '#7D786C'
};

let PAL = null;
let PAL_KEY = '';

function themeKey() {
  try {
    return (document.documentElement.getAttribute('data-theme') || 'dark') + '|' +
           (document.documentElement.getAttribute('class') || '');
  } catch (e) { return 'none'; }
}

/**
 * Resolve every design token against the live stylesheet.
 * @param {Element} [node] element to resolve against (picks up local overrides)
 * @returns {Object<string,string>} token name -> resolved colour
 */
function palette(node) {
  const key = themeKey();
  if (PAL && PAL_KEY === key) return PAL;
  const out = Object.assign({}, FALLBACK);
  try {
    const el = (node && node.isConnected) ? node : document.documentElement;
    const cs = getComputedStyle(el);
    for (const t of TOKENS) {
      const v = (cs.getPropertyValue(t) || '').trim();
      if (v) out[t] = v;
    }
  } catch (e) { /* keep the fallback */ }
  PAL = out; PAL_KEY = key;
  watchTheme();
  return out;
}

/** A live CSS reference, so a theme flip repaints without a re-render. */
function v(token) { return 'var(' + token + ')'; }

/* ── colour maths (needs the resolved value, not the var reference) ─────── */

function parseColor(c) {
  if (!c) return null;
  c = String(c).trim();
  let m = /^#([0-9a-f]{3})$/i.exec(c);
  if (m) return [parseInt(m[1][0] + m[1][0], 16), parseInt(m[1][1] + m[1][1], 16), parseInt(m[1][2] + m[1][2], 16)];
  m = /^#([0-9a-f]{6})$/i.exec(c);
  if (m) return [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4, 6), 16)];
  m = /^rgba?\(([^)]+)\)$/i.exec(c);
  if (m) {
    const p = m[1].split(/[,/\s]+/).filter(Boolean).map(Number);
    if (p.length >= 3 && p.every(n => isFinite(n))) return [p[0], p[1], p[2]];
  }
  return null;
}

function lum(c) {
  const rgb = parseColor(c);
  if (!rgb) return 0.5;
  const f = rgb.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
  return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
}

function contrast(a, b) {
  const l1 = lum(a), l2 = lum(b);
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
}

/** Ink for text sitting ON a coloured fill: whichever token contrasts better. */
function inkOn(pal, fill) {
  return contrast(fill, pal['--card']) >= contrast(fill, pal['--ink'])
    ? pal['--card'] : pal['--ink'];
}

function hexMix(a, b, t) {
  const A = parseColor(a) || [0, 0, 0], B = parseColor(b) || [255, 255, 255];
  const p = i => Math.round(A[i] * t + B[i] * (1 - t));
  return 'rgb(' + p(0) + ',' + p(1) + ',' + p(2) + ')';
}

let MIX_OK = null;
/**
 * A step of a single-hue sequential ramp: `pct`% of `token` over the surface.
 * Uses CSS `color-mix` (stays live through a theme flip) and falls back to a
 * numeric mix of the resolved colours where `color-mix` is unavailable.
 */
function ramp(pal, token, pct, surface) {
  const surf = surface || '--card';
  if (MIX_OK === null) {
    try { MIX_OK = !!(window.CSS && CSS.supports && CSS.supports('color', 'color-mix(in oklab, red 50%, blue)')); }
    catch (e) { MIX_OK = false; }
  }
  const p = Math.max(0, Math.min(100, pct));
  if (MIX_OK) return 'color-mix(in oklab, ' + v(token) + ' ' + p.toFixed(1) + '%, ' + v(surf) + ')';
  return hexMix(pal[token], pal[surf], p / 100);
}

/* ══ 2. live registry — resize and theme ═════════════════════════════════ */

const STATES = typeof WeakMap === 'function' ? new WeakMap() : new Map();
const LIVE = new Set();
let RO = null, MO = null;

function observe(state) {
  LIVE.add(state);
  try {
    if (typeof ResizeObserver === 'undefined') return;
    if (!RO) {
      RO = new ResizeObserver(entries => {
        for (const e of entries) {
          const st = STATES.get(e.target);
          if (!st) continue;
          const w = Math.round((e.contentRect && e.contentRect.width) || 0);
          if (!w || Math.abs(w - st.lastW) < 8) continue;
          render(st);
        }
      });
    }
    RO.observe(state.svg);
  } catch (e) { /* no observer: the chart still draws at its fallback width */ }
}

function watchTheme() {
  if (MO || typeof MutationObserver === 'undefined') return;
  try {
    MO = new MutationObserver(() => retheme());
    MO.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class', 'style'] });
    if (window.matchMedia) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      if (mq.addEventListener) mq.addEventListener('change', () => retheme());
    }
  } catch (e) { /* ignore */ }
}

/**
 * Re-resolve the palette and re-render every chart currently on the page.
 * Wired to `data-theme` automatically; call it by hand after swapping a
 * stylesheet or moving a chart into a differently-themed subtree.
 *
 * @param {Element} [root] element to resolve tokens against (default `<html>`)
 * @example
 *   document.getElementById('themeToggle').addEventListener('click', () => {
 *     document.documentElement.setAttribute('data-theme', 'light');
 *     retheme();                       // charts repaint in daylight tokens
 *   });
 */
export function retheme(root) {
  PAL = null; PAL_KEY = '';
  if (root) palette(root);
  for (const st of Array.from(LIVE)) {
    try {
      if (!st.svg || (st.svg.isConnected === false && st.wrap.isConnected === false)) { LIVE.delete(st); continue; }
      st.root = root || st.root;
      render(st);
    } catch (e) { LIVE.delete(st); }
  }
}

/* ══ 3. SVG + text helpers ═══════════════════════════════════════════════ */

function S(tag, attrs, kids) {
  const el = document.createElementNS(NS, tag);
  if (attrs) for (const k in attrs) {
    const val = attrs[k];
    if (val === null || val === undefined || val === false) continue;
    el.setAttribute(k, String(val));
  }
  if (kids) for (const k of [].concat(kids)) if (k) el.appendChild(k);
  return el;
}

function fill(el, token) { el.style.fill = token.charAt(0) === '-' ? v(token) : token; return el; }
function stroke(el, token) { el.style.stroke = token.charAt(0) === '-' ? v(token) : token; return el; }

function tip(el, text) {
  if (!text) return el;
  const t = document.createElementNS(NS, 'title');
  t.textContent = String(text);
  el.insertBefore(t, el.firstChild);
  return el;
}

/**
 * A text node.
 * @param {string} s
 * @param {number} x @param {number} y
 * @param {Object} [o] {size, weight, color, anchor, halo, tabular, baseline, opacity}
 */
function TXT(s, x, y, o) {
  o = o || {};
  const el = S('text', {
    x: r2(x), y: r2(y),
    'text-anchor': o.anchor || 'start',
    'dominant-baseline': o.baseline || 'alphabetic'
  });
  el.style.font = (o.weight || 400) + ' ' + (o.size || 12) + 'px ' + FONT;
  el.style.fill = v(o.color || '--sage');
  if (o.opacity != null) el.style.opacity = String(o.opacity);
  if (o.tabular) el.style.fontVariantNumeric = 'tabular-nums';
  if (o.halo) {
    el.style.paintOrder = 'stroke';
    el.style.stroke = v(o.haloColor || '--card');
    el.style.strokeWidth = (o.haloWidth || 3) + 'px';
    el.style.strokeLinejoin = 'round';
  }
  el.textContent = String(s);
  return el;
}

function r2(n) { return Math.round(n * 100) / 100; }

let CTX2D = null;
/** Real text width where a canvas exists; a conservative estimate otherwise. */
function tw(s, size, weight) {
  s = String(s == null ? '' : s);
  try {
    if (!CTX2D) CTX2D = document.createElement('canvas').getContext('2d');
    if (CTX2D) { CTX2D.font = (weight || 400) + ' ' + (size || 12) + 'px ' + FONT; return CTX2D.measureText(s).width; }
  } catch (e) { /* fall through */ }
  return s.length * (size || 12) * 0.56;
}

/** Truncate to fit `px`, with an ellipsis. Returns '' when nothing fits. */
function fit(s, px, size, weight) {
  s = String(s == null ? '' : s);
  if (px <= 4) return '';
  if (tw(s, size, weight) <= px) return s;
  let lo = 0, hi = s.length;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (tw(s.slice(0, mid) + '…', size, weight) <= px) lo = mid; else hi = mid - 1;
  }
  return lo > 0 ? s.slice(0, lo) + '…' : '';
}

function roundRect(x, y, w, h, r, corners) {
  const c = corners || 'all';
  const rr = Math.max(0, Math.min(r, h / 2, w));
  const tl = (c === 'all' || c === 'left') ? rr : 0;
  const bl = (c === 'all' || c === 'left') ? rr : 0;
  const tr = (c === 'all' || c === 'right') ? rr : 0;
  const br = (c === 'all' || c === 'right') ? rr : 0;
  return 'M' + r2(x + tl) + ',' + r2(y) +
    'H' + r2(x + w - tr) + (tr ? 'a' + tr + ',' + tr + ' 0 0 1 ' + tr + ',' + tr : '') +
    'V' + r2(y + h - br) + (br ? 'a' + br + ',' + br + ' 0 0 1 ' + (-br) + ',' + br : '') +
    'H' + r2(x + bl) + (bl ? 'a' + bl + ',' + bl + ' 0 0 1 ' + (-bl) + ',' + (-bl) : '') +
    'V' + r2(y + tl) + (tl ? 'a' + tl + ',' + tl + ' 0 0 1 ' + tl + ',' + (-tl) : '') + 'Z';
}

/** Wrap a mark in a focusable link when `opts.href` yields one. */
function link(ctx, node, item, i, label) {
  let href = null;
  try { href = typeof ctx.opts.href === 'function' ? ctx.opts.href(item, i) : null; } catch (e) { href = null; }
  if (!href) return node;
  const a = S('a', { href: href, tabindex: '0', role: 'link', 'aria-label': label || undefined });
  a.appendChild(node);
  return a;
}

/* ══ 4. numbers ══════════════════════════════════════════════════════════ */

function inGroup(s) {                       // 12345678 -> 1,23,45,678
  s = String(s);
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  let rest = s.slice(0, -3), out = '';
  while (rest.length > 2) { out = ',' + rest.slice(-2) + out; rest = rest.slice(0, -2); }
  return (rest ? rest + out : out.replace(/^,/, '')) + ',' + last3;
}

function money(n, exact) {
  if (n === null || n === undefined || n === '' || isNaN(n)) return '—';
  n = Number(n);
  const sign = n < 0 ? '−' : '', a = Math.abs(n);
  if (!exact) {
    if (a >= 1e7) return sign + '₹' + (a / 1e7).toFixed(2) + ' Cr';
    if (a >= 1e5) return sign + '₹' + (a / 1e5).toFixed(2) + ' L';
  }
  return sign + '₹' + inGroup(Math.round(a));
}

function num(n) {
  if (n === null || n === undefined || n === '' || isNaN(n)) return '—';
  n = Number(n);
  const s = n < 0 ? '−' : '';
  return s + inGroup(Math.abs(n) < 100 && Math.round(n) !== n ? Math.abs(n).toFixed(1) : Math.round(Math.abs(n)));
}

/** Format one value with the chart's `format`/`unit` options. */
function fmt(val, opts) {
  opts = opts || {};
  if (typeof opts.format === 'function') {
    try { const s = opts.format(val); if (s != null) return String(s); } catch (e) { /* fall back */ }
  }
  if (val === null || val === undefined || val === '' || isNaN(val)) return '—';
  const u = opts.unit || 'INR';
  if (u === 'INR') return money(val);
  if (u === '%' || u === 'pct') return (Number(val)).toFixed(opts.dp == null ? 1 : opts.dp) + '%';
  if (u === 'd' || u === 'days') return num(val) + ' d';
  if (u === 'n' || u === 'count') return num(val);
  return num(val) + ' ' + u;
}

/** Signed variant — an explicit + or − in front, for deltas. */
function fmtSigned(val, opts) {
  const s = fmt(Math.abs(Number(val) || 0), opts);
  return (Number(val) < 0 ? '−' : '+') + (s.charAt(0) === '−' ? s.slice(1) : s);
}

function pctOf(a, b) { return b ? (100 * a / b) : 0; }

function niceNum(range, round) {
  const exp = Math.floor(Math.log(range) / Math.LN10);
  const f = range / Math.pow(10, exp);
  let nf;
  if (round) nf = f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10;
  else nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
  return nf * Math.pow(10, exp);
}

/** Axis ticks on round numbers. Always safe on degenerate domains. */
function ticks(min, max, n) {
  n = n || 5;
  if (!isFinite(min) || !isFinite(max)) return [0];
  if (min === max) return [min === 0 ? 0 : min];
  const range = niceNum(max - min, false);
  const step = niceNum(range / Math.max(1, n - 1), true);
  const s = Math.floor(min / step) * step, e = Math.ceil(max / step) * step;
  const out = [];
  for (let x = s; x <= e + step * 0.5 && out.length < 40; x += step) out.push(Math.abs(x) < step * 1e-9 ? 0 : x);
  return out;
}

/* ══ 5. page CSS (injected once — charts.js owns no stylesheet) ══════════ */

let CSS_IN = false;
function injectCSS() {
  if (CSS_IN) return;
  CSS_IN = true;
  try {
    if (document.getElementById('jc-charts-css')) return;
    const s = document.createElement('style');
    s.id = 'jc-charts-css';
    s.textContent = [
      '.chartwrap{margin:6px 0 16px;min-width:0;max-width:100%}',
      '.chartwrap .jc-svg{display:block;width:100%;height:auto;min-width:0;font-family:' + FONT + '}',
      '.chartwrap a{cursor:pointer;outline:none}',
      '.chartwrap a:focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:4px}',
      '.chartwrap a:hover .jc-mk,.chartwrap a:focus-visible .jc-mk{opacity:.82}',
      '.chartwrap .jc-mk{transition:opacity .12s ease}',
      '@media (prefers-reduced-motion:reduce){.chartwrap .jc-mk{transition:none}}',
      '.chartwrap .jc-tab{margin-top:6px}',
      '.chartwrap .jc-tab>summary{cursor:pointer;font-size:12px;font-weight:650;color:var(--soft);',
      'list-style:none;padding:4px 0;display:flex;align-items:center;gap:6px}',
      '.chartwrap .jc-tab>summary::-webkit-details-marker{display:none}',
      '.chartwrap .jc-tab>summary::before{content:"\\25B8";font-size:10px;line-height:1}',
      '.chartwrap .jc-tab[open]>summary::before{content:"\\25BE"}',
      '.chartwrap .jc-tab>summary:hover{color:var(--brand)}',
      '.chartwrap .jc-tscroll{overflow-x:auto;overflow-y:auto;max-height:330px;min-width:0;',
      'border:1px solid var(--line-soft);border-radius:10px;margin-top:4px}',
      '.chartwrap .jc-tab table{border-collapse:separate;border-spacing:0;width:100%;font-size:12.5px}',
      '.chartwrap .jc-tab th{position:sticky;top:0;z-index:1;background:var(--card);text-align:left;',
      'font-weight:650;font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--soft);',
      'padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap}',
      '.chartwrap .jc-tab td{padding:6px 10px;border-bottom:1px solid var(--line-soft);',
      'white-space:nowrap;color:var(--ink)}',
      '.chartwrap .jc-tab td.num{text-align:right;font-variant-numeric:tabular-nums}',
      '.chartwrap .jc-tab td.neg{color:var(--bad)}',
      '.chartwrap .jc-tab tr:last-child td{border-bottom:0}',
      '.chartwrap .jc-tab .jc-swatch{display:inline-block;width:9px;height:9px;border-radius:2px;',
      'margin-right:6px;vertical-align:-1px}',
      '.chartwrap .jc-tnote{font-size:11.5px;color:var(--soft);margin-top:6px;line-height:1.5;max-width:80ch}'
    ].join('');
    (document.head || document.documentElement).appendChild(s);
  } catch (e) { /* a page without a head still gets the charts, just unstyled */ }
}

/* ══ 6. the table behind every chart ═════════════════════════════════════ */

/**
 * Build the `<details>` disclosure.
 * @param {{cols:Array, rows:Array, note:string, summary:string}} spec
 *        cols: [{k, label, align:'num'|'txt', swatch:token}]
 */
function tableEl(spec) {
  const det = document.createElement('details');
  det.className = 'jc-tab';
  const rows = spec.rows || [], cols = spec.cols || [];
  const sum = document.createElement('summary');
  sum.textContent = spec.summary || ('The numbers behind this chart (' + rows.length + ' row' + (rows.length === 1 ? '' : 's') + ')');
  det.appendChild(sum);

  const scroll = document.createElement('div');
  scroll.className = 'jc-tscroll';
  const t = document.createElement('table');
  const thead = document.createElement('thead');
  const htr = document.createElement('tr');
  for (const c of cols) {
    const th = document.createElement('th');
    th.textContent = c.label;
    if (c.align === 'num') th.style.textAlign = 'right';
    htr.appendChild(th);
  }
  thead.appendChild(htr); t.appendChild(thead);

  const tb = document.createElement('tbody');
  const cap = spec.max || 250;
  for (const row of rows.slice(0, cap)) {
    const tr = document.createElement('tr');
    for (const c of cols) {
      const td = document.createElement('td');
      const raw = row[c.k];
      if (c.align === 'num') {
        td.className = 'num' + (Number(raw) < 0 ? ' neg' : '');
        td.textContent = row[c.k + '_t'] != null ? row[c.k + '_t'] : (raw == null ? '—' : String(raw));
      } else {
        if (row[c.k + '_c']) {
          const i = document.createElement('i');
          i.className = 'jc-swatch';
          i.style.background = v(row[c.k + '_c']);
          td.appendChild(i);
        }
        td.appendChild(document.createTextNode(raw == null ? '—' : String(raw)));
      }
      tr.appendChild(td);
    }
    tb.appendChild(tr);
  }
  t.appendChild(tb);
  scroll.appendChild(t);
  det.appendChild(scroll);

  const extra = rows.length - cap;
  const notes = [];
  if (extra > 0) notes.push(extra + ' further row' + (extra === 1 ? '' : 's') + ' not listed here.');
  if (spec.note) notes.push(spec.note);
  if (notes.length) {
    const n = document.createElement('div');
    n.className = 'jc-tnote';
    n.textContent = notes.join(' ');
    det.appendChild(n);
  }
  return det;
}

/* ══ 7. mount + render ═══════════════════════════════════════════════════ */

function measureWidth(st) {
  if (st.opts.width) return Math.max(240, Math.round(st.opts.width));
  let w = 0;
  try { w = Math.round(st.svg.getBoundingClientRect().width) || 0; } catch (e) { w = 0; }
  if (!w) { try { w = Math.round(st.wrap.getBoundingClientRect().width) || 0; } catch (e) { w = 0; } }
  if (!w) w = st.opts.fallbackWidth || 720;
  return Math.max(240, Math.min(w, 1600));
}

function render(st) {
  const w = measureWidth(st);
  st.lastW = w;
  const pal = palette(st.wrap && st.wrap.isConnected ? st.wrap : (st.root || null));
  const svg = st.svg;
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  const ctx = {
    svg: svg, w: w, pal: pal, opts: st.opts,
    add: n => { svg.appendChild(n); return n; }
  };
  let h = 0, top = 0;
  try {
    if (st.opts.title) { ctx.add(TXT(fit(st.opts.title, w, 12.5, 650), 0, 12, { size: 12.5, weight: 650, color: '--sage' })); top = 22; }
    ctx.top = top;
    h = Number(st.cfg.draw(ctx)) || top + 40;
    if (st.opts.note) {
      const lines = wrapText(st.opts.note, w, 11.5);
      lines.forEach((ln, i) => ctx.add(TXT(ln, 0, h + 12 + i * 14, { size: 11.5, color: '--soft' })));
      h += 12 + lines.length * 14;
    }
  } catch (err) {
    try { console.warn('[charts] ' + (st.cfg.kind || 'chart') + ' failed to draw:', err); } catch (e) { /* ignore */ }
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    h = drawEmpty(ctx, 'This chart could not be drawn: ' + (err && err.message ? err.message : 'unexpected data shape') + '. The numbers are in the table below.');
  }
  svg.setAttribute('viewBox', '0 0 ' + w + ' ' + Math.max(28, Math.round(h)));
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
}

function wrapText(s, w, size) {
  const words = String(s).split(/\s+/), out = [];
  let line = '';
  for (const word of words) {
    const test = line ? line + ' ' + word : word;
    if (tw(test, size, 400) > w && line) { out.push(line); line = word; } else line = test;
  }
  if (line) out.push(line);
  return out.slice(0, 4);
}

/** The honest empty state — never a blank box, never a confident zero. */
function drawEmpty(ctx, msg) {
  const top = ctx.top || 0;
  const lines = wrapText(msg, ctx.w - 28, 12.5);
  const h = top + Math.max(64, 30 + lines.length * 17);
  const box = S('rect', { x: 0.5, y: top + 0.5, width: Math.max(1, ctx.w - 1), height: Math.max(1, h - top - 1), rx: 10 });
  fill(box, '--card-warm'); stroke(box, '--line-soft'); box.style.strokeWidth = '1px';
  ctx.add(box);
  lines.forEach((ln, i) => ctx.add(TXT(ln, ctx.w / 2, top + 24 + i * 17, { size: 12.5, color: '--soft', anchor: 'middle' })));
  ctx.svg.setAttribute('aria-label', msg);
  return h;
}

/**
 * Create the chart element and keep it alive (resize + theme).
 * @param {Object} cfg {kind, opts, draw(ctx)->height, table()->spec, aria, defaultTable}
 */
function mount(cfg) {
  injectCSS();
  const opts = cfg.opts || {};
  const wantTable = opts.table === undefined ? (cfg.defaultTable !== false) : !!opts.table;

  const wrap = document.createElement('div');
  wrap.className = 'chartwrap' + (opts.className ? ' ' + opts.className : '');

  const svg = S('svg', {
    class: 'jc-svg', xmlns: NS, role: 'img',
    'aria-label': opts.ariaLabel || cfg.aria || 'chart'
  });
  wrap.appendChild(svg);

  const st = { svg: svg, wrap: wrap, cfg: cfg, opts: opts, lastW: 0, root: null };
  STATES.set(svg, st);
  render(st);
  observe(st);

  if (wantTable && cfg.table) {
    try { wrap.appendChild(tableEl(cfg.table())); }
    catch (e) { try { console.warn('[charts] table failed:', e); } catch (e2) { /* ignore */ } }
  }
  const out = wantTable ? wrap : svg;
  try { out.chartSvg = svg; out.chartWrap = wrap; } catch (e) { /* ignore */ }
  return out;
}

/* ══ 8. shared drawing pieces ════════════════════════════════════════════ */

/** A wrapping legend inside the SVG. Returns the height it used. */
function drawLegend(ctx, items, y) {
  if (!items || !items.length) return 0;
  const size = 11.5, gap = 14, sw = 10;
  let x = 0, line = 0;
  for (const it of items) {
    const label = it.value ? it.label + '  ' + it.value : it.label;
    const width = sw + 5 + tw(label, size, it.bold ? 650 : 400);
    if (x > 0 && x + width > ctx.w) { x = 0; line++; }
    const yy = y + line * 18;
    const sq = S('rect', { x: r2(x), y: r2(yy + 1), width: sw, height: sw, rx: 2.5 });
    if (it.color) fill(sq, it.color);
    if (it.pattern) sq.style.opacity = '0.55';
    ctx.add(sq);
    ctx.add(TXT(label, x + sw + 5, yy + 9.5, { size: size, color: '--sage' }));
    x += width + gap;
  }
  return (line + 1) * 18 + 2;
}

/** Width of the left label column shared by the row-shaped charts. */
function labelColW(w, labels, size, weight) {
  let max = 0;
  for (const l of labels) max = Math.max(max, tw(l, size, weight || 400));
  return Math.max(56, Math.min(max + 6, Math.max(70, w * 0.34), 210));
}

/** Width of the right-hand value column. */
function valueColW(w, texts, size, weight) {
  let max = 0;
  for (const t of texts) max = Math.max(max, tw(t, size, weight || 650));
  return Math.max(38, Math.min(max + 8, w * 0.34, 150));
}

function toNum(x) { const n = Number(x); return isFinite(n) ? n : 0; }

/** Fold a categorical tail into "Other (n)" — never a 7th hue. */
function capCategories(items, max, opts) {
  const cap = Math.max(1, max || 6);
  if (items.length <= cap) return { items: items, folded: 0 };
  const head = items.slice(0, cap - 1);
  const tail = items.slice(cap - 1);
  const sum = tail.reduce((a, b) => a + toNum(b.value), 0);
  head.push({
    label: 'Other (' + tail.length + ' more)',
    value: sum, other: true, members: tail,
    _text: 'Other — ' + tail.length + ' smaller item' + (tail.length === 1 ? '' : 's') + ' totalling ' + fmt(sum, opts)
  });
  return { items: head, folded: tail.length };
}

/** Normalise `[{label,value}]` from several shapes callers actually pass. */
function normItems(items, opts) {
  opts = opts || {};
  const lk = opts.labelKey, vk = opts.valueKey;
  return (items || []).map((it, i) => {
    if (it == null) return { label: '—', value: 0, src: it };
    if (typeof it === 'number') return { label: String(i + 1), value: it, src: it };
    if (Array.isArray(it)) return { label: String(it[0]), value: toNum(it[1]), src: it };
    const label = it[lk] != null ? it[lk]
      : it.label != null ? it.label
      : it.name != null ? it.name
      : it.key != null ? it.key
      : it.card != null ? it.card : String(i + 1);
    const value = vk != null ? toNum(it[vk])
      : it.value != null ? toNum(it.value)
      : it.v != null ? toNum(it.v)
      : it.amount != null ? toNum(it.amount) : 0;
    return { label: String(label), value: value, src: it, color: it.color, href: it.href };
  });
}

/* ══ 9. waterfall — the chart that draws the correction itself ═══════════ */

/**
 * The four step kinds, mapped to `--c1..--c4` in fixed order. The mapping is
 * constant: a deduction is always `--c3` whether or not the chart contains an
 * addition, so colour never shifts meaning between two waterfalls.
 */
const WF = {
  base:  { color: '--c1', label: 'Opening balance', signed: false },
  add:   { color: '--c2', label: 'Addition',        signed: true  },
  sub:   { color: '--c3', label: 'Deduction',       signed: true  },
  total: { color: '--c4', label: 'Subtotal',        signed: false }
};

function normSteps(steps) {
  const out = [];
  let run = 0;
  (steps || []).forEach((s, i) => {
    if (s == null) return;
    const label = String(s.label != null ? s.label : (s.name != null ? s.name : 'Step ' + (i + 1)));
    const has = s.value !== null && s.value !== undefined && s.value !== '' && isFinite(Number(s.value));
    const val = toNum(s.value);
    let kind = s.kind || (i === 0 ? 'base' : (val < 0 ? 'sub' : 'add'));
    if (!WF[kind]) kind = val < 0 ? 'sub' : 'add';
    let start, end, delta, stated = null;
    if (kind === 'base') { start = 0; end = val; delta = val; run = val; }
    else if (kind === 'total') {
      start = 0; end = run; delta = run;
      if (has && Math.abs(val - run) > Math.max(1, Math.abs(run) * 0.005)) stated = val;
    } else if (kind === 'sub') { delta = -Math.abs(val); start = run; end = run + delta; run = end; }
    else { kind = 'add'; delta = Math.abs(val); start = run; end = run + delta; run = end; }
    out.push({ label: label, kind: kind, delta: delta, start: start, end: end, run: run, stated: stated, src: s });
  });
  return out;
}

/**
 * Waterfall — a running balance taken apart step by step, with connectors, a
 * running subtotal, distinct fills per kind and signed value labels.
 *
 * Rows run top to bottom (it stays readable at 390px, and it keeps v1's
 * `name | bar | value` language). `base` opens the run, `add`/`sub` move it,
 * `total` draws a checkpoint from zero to the running balance. A `total` whose
 * stated value disagrees with the arithmetic above it is drawn at the running
 * value and the disagreement is called out — never silently overwritten.
 *
 * @param {Array<{label:string,value:number,kind:('base'|'add'|'sub'|'total')}>} steps
 *   `kind` may be omitted: the first step is the base, then the sign decides.
 *   `sub` uses the absolute value, so −208.2 and 208.2 both subtract.
 * @param {Object} [opts] shared options; `running:false` hides the running
 *   subtotal annotation.
 * @returns {Element} `.chartwrap` div (or the `<svg>` with `{table:false}`)
 *
 * @example
 * // Oil payables — Rs 310.71 Cr raw open down to Rs 22.68 Cr genuinely owed to trade
 * card.appendChild(waterfall([
 *   {label:'Raw open A/P',        value: 3107100000, kind:'base'},
 *   {label:'Credit applied',      value:  2082000000, kind:'sub'},
 *   {label:'Subtotal',            value:  1025100000, kind:'total'},
 *   {label:'Branch accounts',     value:   775800000, kind:'sub'},
 *   {label:'Intercompany',        value:    22500000, kind:'sub'},
 *   {label:'Owed to trade',       value:   226800000, kind:'total'}
 * ], {title:'What JIVO Oil actually owes its trade vendors',
 *     href:(s)=>s.src.k ? 'derivation.html?k='+s.src.k+'&co=oil' : null}));
 */
export function waterfall(steps, opts) {
  opts = opts || {};
  const rows = normSteps(steps);

  return mount({
    kind: 'waterfall',
    opts: opts,
    aria: rows.length
      ? 'Waterfall. ' + rows.map(r => r.label + ' ' + (WF[r.kind].signed ? fmtSigned(r.delta, opts) : fmt(r.delta, opts))).join(', ') +
        '. Closing balance ' + fmt(rows.length ? rows[rows.length - 1].run : 0, opts) + '.'
      : 'Waterfall with no steps.',
    draw: ctx => {
      if (!rows.length) return drawEmpty(ctx, 'No steps to chart — nothing was passed to the waterfall.');
      const top = ctx.top || 0, w = ctx.w;
      const compact = w < 430;
      const fs = compact ? 11.5 : 12.5;
      const rowH = compact ? 34 : 38, barH = compact ? 15 : 16;

      const labels = rows.map(r => (r.kind === 'total' ? '= ' : '') + r.label);
      const vals = rows.map(r => WF[r.kind].signed ? fmtSigned(r.delta, opts) : fmt(r.delta, opts));
      const runs = rows.map(r => '→ ' + fmt(r.run, opts));
      const showRun = opts.running !== false && !compact;

      let labW = labelColW(w, labels, fs, 600);
      let valW = valueColW(w, vals.concat(showRun ? runs : []), fs, 650);
      let plotX = labW + 10;
      let plotW = w - plotX - valW - 8;
      if (plotW < 60) {                       // very narrow card: give the plot room
        labW = Math.max(46, w * 0.26); plotX = labW + 8; valW = Math.max(34, w * 0.26);
        plotW = Math.max(30, w - plotX - valW - 6);
      }

      let dmin = 0, dmax = 0;
      for (const r of rows) {
        dmin = Math.min(dmin, r.start, r.end); dmax = Math.max(dmax, r.start, r.end);
      }
      if (dmax === dmin) dmax = dmin + 1;
      const x = val => plotX + (val - dmin) / (dmax - dmin) * plotW;
      const zeroX = x(0);

      // zero baseline, behind everything
      const base = S('line', { x1: r2(zeroX), y1: top, x2: r2(zeroX), y2: top + rows.length * rowH });
      stroke(base, '--line'); base.style.strokeWidth = '1px';
      ctx.add(base);

      rows.forEach((r, i) => {
        const y = top + i * rowH;
        const meta = WF[r.kind];
        const isLevel = r.kind === 'base' || r.kind === 'total';

        if (r.kind === 'total') {
          const band = S('rect', { x: 0, y: r2(y + 1), width: w, height: r2(rowH - 3), rx: 7 });
          fill(band, '--card-warm');
          ctx.add(band);
        }

        const x0 = x(Math.min(r.start, r.end)), x1 = x(Math.max(r.start, r.end));
        const bw = Math.max(2.5, x1 - x0);      // a 1000x-dominated step is still visible
        const by = y + (rowH - barH) / 2 - 1;
        const corners = isLevel ? (r.end >= 0 ? 'right' : 'left') : 'all';
        const bar = S('path', { d: roundRect(x0, by, bw, barH, 4, corners), class: 'jc-mk' });
        fill(bar, meta.color);
        const aria = r.label + ' — ' + meta.label + ' ' +
          (meta.signed ? fmtSigned(r.delta, opts) : fmt(r.delta, opts)) +
          ', running balance ' + fmt(r.run, opts);
        tip(bar, aria);
        ctx.add(link(ctx, bar, r.src, i, aria));

        ctx.add(TXT(fit(labels[i], labW, fs, isLevel ? 700 : 500), 0, y + rowH / 2 + 4,
          { size: fs, weight: isLevel ? 700 : 500, color: '--ink' }));

        ctx.add(TXT(vals[i], w, y + rowH / 2 + (showRun && !isLevel ? -1 : 4),
          { size: fs, weight: 650, color: isLevel ? '--brand-deep' : '--ink', anchor: 'end' }));
        if (showRun && !isLevel) {
          ctx.add(TXT(runs[i], w, y + rowH / 2 + 12, { size: 10.5, color: '--soft', anchor: 'end' }));
        }

        // connector: the level this step ended at, carried into the next row
        if (i < rows.length - 1 && rows[i + 1].kind !== 'base') {
          const cx = x(r.end);
          const c = S('line', { x1: r2(cx), y1: r2(by + barH + 1), x2: r2(cx), y2: r2(y + rowH + (rowH - barH) / 2 - 2) });
          stroke(c, '--soft'); c.style.strokeWidth = '1px'; c.style.opacity = '.55';
          ctx.add(c);
        }
      });

      let h = top + rows.length * rowH + 6;
      h += drawLegend(ctx, Array.from(new Set(rows.map(r => r.kind)))
        .map(k => ({ label: WF[k].label, color: WF[k].color })), h);

      const off = rows.filter(r => r.stated != null);
      if (off.length) {
        off.forEach(r => {
          const msg = '“' + r.label + '” is stated as ' + fmt(r.stated, opts) +
            '; the steps above run to ' + fmt(r.run, opts) + '. The chart draws the arithmetic.';
          wrapText(msg, ctx.w, 11.5).forEach((ln, i) => ctx.add(TXT(ln, 0, h + 10 + i * 14, { size: 11.5, color: '--warn' })));
          h += 10 + wrapText(msg, ctx.w, 11.5).length * 14;
        });
      }
      return h;
    },
    table: () => ({
      summary: 'The steps behind this waterfall (' + rows.length + ')',
      cols: [
        { k: 'step', label: 'Step', align: 'txt' },
        { k: 'kind', label: 'Kind', align: 'txt' },
        { k: 'change', label: 'Change', align: 'num' },
        { k: 'run', label: 'Running', align: 'num' }
      ],
      rows: rows.map(r => ({
        step: r.label, step_c: WF[r.kind].color,
        kind: WF[r.kind].label + (r.stated != null ? ' (stated ' + fmt(r.stated, opts) + ')' : ''),
        change: r.delta, change_t: WF[r.kind].signed ? fmtSigned(r.delta, opts) : fmt(r.delta, opts),
        run: r.run, run_t: fmt(r.run, opts)
      })),
      note: opts.tableNote
    })
  });
}

/* ══ 10. sparkline ═══════════════════════════════════════════════════════ */

function normSeriesValues(values) {
  return (values || []).map((p, i) => {
    if (p == null) return null;
    if (typeof p === 'number') return { label: String(i + 1), value: p };
    if (Array.isArray(p)) return { label: String(p[0]), value: toNum(p[1]) };
    return {
      label: String(p.x != null ? p.x : (p.label != null ? p.label : (p.t != null ? p.t : i + 1))),
      value: toNum(p.y != null ? p.y : (p.value != null ? p.value : p.v))
    };
  }).filter(p => p && isFinite(p.value));
}

/**
 * Sparkline — a micro trend for a KPI tile: 2px line, a 10% area wash, an end
 * dot with a 2px surface ring and the latest value printed beside it.
 *
 * The only chart whose table is OFF by default: it lives inside a tile that
 * already prints the current value. Pass `{table:true}` to add the numbers.
 *
 * @param {Array<number|{x:*,y:number}>} values oldest first
 * @param {Object} [opts] `height` (default 40), `label:false` to drop the end
 *   label, `color` (a token name, default `--c1`), `extremes:true` to mark the
 *   high and the low.
 * @returns {Element} `<svg>` (or `.chartwrap` with `{table:true}`)
 *
 * @example
 * tile.appendChild(sparkline([61.2, 63.9, 58.4, 71.0, 73.5], {unit:'INR', height:36}));
 * // and with the numbers reachable:
 * tile.appendChild(sparkline(history.map(h => h.value), {table:true, extremes:true}));
 */
export function sparkline(values, opts) {
  opts = opts || {};
  const pts = normSeriesValues(values);
  const color = opts.color || '--c1';
  const last = pts.length ? pts[pts.length - 1] : null;
  const lo = pts.length ? Math.min.apply(null, pts.map(p => p.value)) : 0;
  const hi = pts.length ? Math.max.apply(null, pts.map(p => p.value)) : 0;

  return mount({
    kind: 'sparkline',
    opts: opts,
    defaultTable: false,
    aria: pts.length
      ? 'Sparkline of ' + pts.length + ' points, from ' + fmt(pts[0].value, opts) + ' to ' + fmt(last.value, opts) +
        ', low ' + fmt(lo, opts) + ', high ' + fmt(hi, opts) + '.'
      : 'Sparkline with no history.',
    draw: ctx => {
      const top = ctx.top || 0, w = ctx.w;
      const h = (opts.height || 40);
      if (!pts.length) return drawEmpty(ctx, 'No history yet — this figure has been measured only once.');

      const labelTxt = opts.label === false ? '' : fmt(last.value, opts);
      const labW = labelTxt ? tw(labelTxt, 11.5, 650) + 7 : 0;
      const plotW = Math.max(12, w - labW - 5);
      const padY = 5;
      const y0 = top + padY, y1 = top + h - padY;

      let span = hi - lo;
      const flat = span <= 0;
      if (flat) span = Math.abs(hi) > 0 ? Math.abs(hi) : 1;
      const yOf = val => flat ? (y0 + y1) / 2 : y1 - (val - lo) / span * (y1 - y0);
      const xOf = i => pts.length === 1 ? plotW / 2 : (i / (pts.length - 1)) * plotW;

      if (pts.length > 1) {
        const d = pts.map((p, i) => (i ? 'L' : 'M') + r2(xOf(i)) + ',' + r2(yOf(p.value))).join('');
        const area = S('path', { d: d + 'L' + r2(xOf(pts.length - 1)) + ',' + r2(y1) + 'L' + r2(xOf(0)) + ',' + r2(y1) + 'Z' });
        fill(area, color); area.style.fillOpacity = '.10';
        ctx.add(area);
        const line = S('path', { d: d, class: 'jc-mk' });
        line.style.fill = 'none'; stroke(line, color);
        line.style.strokeWidth = '2px'; line.style.strokeLinejoin = 'round'; line.style.strokeLinecap = 'round';
        ctx.add(tip(line, ctx.svg.getAttribute('aria-label')));
      }

      if (opts.extremes && pts.length > 2 && !flat) {
        [[lo, 'low'], [hi, 'high']].forEach(([val, what]) => {
          const i = pts.findIndex(p => p.value === val);
          if (i < 0) return;
          const m = S('circle', { cx: r2(xOf(i)), cy: r2(yOf(val)), r: 3 });
          fill(m, color); stroke(m, '--card'); m.style.strokeWidth = '2px';
          ctx.add(tip(m, what + ' ' + pts[i].label + ': ' + fmt(val, opts)));
        });
      }

      const dot = S('circle', { cx: r2(xOf(pts.length - 1)), cy: r2(yOf(last.value)), r: 4, class: 'jc-mk' });
      fill(dot, color); stroke(dot, '--card'); dot.style.strokeWidth = '2px';
      ctx.add(tip(dot, last.label + ': ' + fmt(last.value, opts)));

      if (labelTxt) {
        ctx.add(TXT(labelTxt, w, yOf(last.value) + 4, { size: 11.5, weight: 650, color: '--ink', anchor: 'end' }));
      }
      if (flat && pts.length > 1) {
        ctx.add(TXT('flat', 0, y0 - 1, { size: 10, color: '--soft' }));
      }
      return top + h;
    },
    table: () => ({
      summary: 'The ' + pts.length + ' point' + (pts.length === 1 ? '' : 's') + ' behind this sparkline',
      cols: [{ k: 'when', label: 'Point', align: 'txt' }, { k: 'val', label: 'Value', align: 'num' }],
      rows: pts.map(p => ({ when: p.label, val: p.value, val_t: fmt(p.value, opts) })),
      note: opts.tableNote
    })
  });
}

/* ══ 11. hbars — v1's ranked bar list, kept ══════════════════════════════ */

/**
 * Horizontal ranked bars — `name | track | value`, exactly v1's language: a
 * 15px track in `--line-soft`, a 4px rounded data end, the value printed at
 * the right in `--brand-deep`.
 *
 * One series, one colour (v1 cycled `--c1..--c6` per row; that cycles past six
 * and paints identity onto what is only rank, so bars now share `--c1` unless
 * you pass `color`, or a per-item `color`). Negative values (credits) draw to
 * the left of a zero rule instead of being flattened by `Math.abs`.
 *
 * @param {Array<{name:string,value:number}>} items unsorted is fine — pass
 *   `{sort:true}` to rank them, `{top:N}` to keep the first N (default 20).
 * @param {Object} [opts] plus `color` (token, default `--c1`).
 * @returns {Element}
 *
 * @example
 * card.appendChild(hbars(top.map(r => ({name:r.CardName, value:r.EFF_OPEN_INR})),
 *   {title:'Biggest trade balances', sort:true, top:10, color:'--c3',
 *    href:(it)=> 'party.html?card='+it.src.CardCode+'&co=oil'}));
 */
export function hbars(items, opts) {
  opts = opts || {};
  let list = normItems(items, opts);
  if (opts.sort) list = list.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  const top = opts.top == null ? 20 : opts.top;
  const shown = top ? list.slice(0, top) : list;
  const hidden = list.length - shown.length;

  return mount({
    kind: 'hbars',
    opts: opts,
    aria: shown.length
      ? 'Ranked bars: ' + shown.map(i => i.label + ' ' + fmt(i.value, opts)).join(', ') + '.'
      : 'Ranked bars with no rows.',
    draw: ctx => {
      if (!shown.length) return drawEmpty(ctx, opts.emptyMsg || 'No rows to chart.');
      const t = ctx.top || 0, w = ctx.w;
      const compact = w < 420;
      const fs = compact ? 12 : 13, rowH = compact ? 25 : 26, barH = 15;

      const labels = shown.map(i => i.label);
      const vals = shown.map(i => fmt(i.value, opts));
      let labW = labelColW(w, labels, fs, 400);
      let valW = valueColW(w, vals, 12.5, 650);
      let plotX = labW + 10, plotW = w - plotX - valW - 8;
      if (plotW < 50) { labW = w * 0.3; plotX = labW + 8; valW = w * 0.28; plotW = Math.max(24, w - plotX - valW - 6); }

      const anyNeg = shown.some(i => i.value < 0);
      const maxAbs = Math.max.apply(null, shown.map(i => Math.abs(i.value)).concat([0]));
      const dmax = maxAbs || 1;
      const dmin = anyNeg ? -dmax : 0;
      const x = val => plotX + (val - dmin) / (dmax - dmin) * plotW;
      const zeroX = x(0);
      const allZero = maxAbs === 0;

      shown.forEach((it, i) => {
        const y = t + i * rowH, by = y + (rowH - barH) / 2 - 1;
        const track = S('rect', { x: r2(plotX), y: r2(by), width: r2(plotW), height: barH, rx: 5 });
        fill(track, '--line-soft');
        ctx.add(track);

        if (!allZero && it.value !== 0) {
          const neg = it.value < 0;
          const x0 = neg ? x(it.value) : zeroX;
          const bw = Math.max(2.5, Math.abs(x(it.value) - zeroX));
          const bar = S('path', {
            d: roundRect(neg ? x0 : zeroX, by, bw, barH, 4, neg ? 'left' : 'right'), class: 'jc-mk'
          });
          fill(bar, it.color || opts.color || '--c1');
          const aria = it.label + ': ' + fmt(it.value, opts);
          tip(bar, aria);
          ctx.add(link(ctx, bar, it.src, i, aria));
        }
        ctx.add(TXT(fit(it.label, labW, fs, 400), 0, y + rowH / 2 + 4, { size: fs, color: '--ink' }));
        ctx.add(TXT(vals[i], w, y + rowH / 2 + 4, { size: 12.5, weight: 650, color: '--brand-deep', anchor: 'end' }));
      });

      if (anyNeg) {
        const zl = S('line', { x1: r2(zeroX), y1: t, x2: r2(zeroX), y2: t + shown.length * rowH });
        stroke(zl, '--line'); zl.style.strokeWidth = '1px';
        ctx.add(zl);
      }
      let h = t + shown.length * rowH + 4;
      const notes = [];
      if (allZero) notes.push('Every row is zero — the bars have no length to draw.');
      if (hidden > 0) notes.push(hidden + ' further row' + (hidden === 1 ? '' : 's') + ' below the top ' + shown.length + ', all in the table.');
      if (notes.length) {
        wrapText(notes.join(' '), w, 11.5).forEach((ln, i) => ctx.add(TXT(ln, 0, h + 10 + i * 14, { size: 11.5, color: '--soft' })));
        h += 10 + wrapText(notes.join(' '), w, 11.5).length * 14;
      }
      return h;
    },
    table: () => ({
      summary: 'The ' + list.length + ' row' + (list.length === 1 ? '' : 's') + ' behind these bars',
      cols: [{ k: 'name', label: 'Name', align: 'txt' }, { k: 'val', label: 'Value', align: 'num' }],
      rows: list.map(i => ({ name: i.label, val: i.value, val_t: fmt(i.value, opts) })),
      note: opts.tableNote
    })
  });
}

/* ══ 12. stackedBars — the ageing ramp ═══════════════════════════════════ */

const BUCKET_LABEL = {
  B0_NOTDUE: 'Not due', B1_1_30: '1–30 d', B2_31_60: '31–60 d', B3_61_90: '61–90 d',
  B4_91_180: '91–180 d', B5_181_365: '181–365 d', B6_365PLUS: '365 d +',
  NOTDUE_INR: 'Not due', D1_30_INR: '1–30 d', D31_60_INR: '31–60 d', D61_90_INR: '61–90 d',
  D91_180_INR: '91–180 d', D181_365_INR: '181–365 d', D365P_INR: '365 d +',
  AGE_0_30_L: '0–30 d', AGE_31_90_L: '31–90 d', AGE_91_365_L: '91–365 d', AGE_365P_L: '365 d +',
  UB_0_30: '0–30 d', UB_31_60: '31–60 d', UB_61_90: '61–90 d', UB_91_180: '91–180 d',
  UB_181_365: '181–365 d', UB_365PLUS: '365 d +',
  UNREC_0_30_L: '0–30 d', UNREC_31_60_L: '31–60 d', UNREC_61_90_L: '61–90 d', UNREC_90PLUS_L: '90 d +',
  A_notdue: 'Not due', 'B_1-30': '1–30 d', 'C_31-60': '31–60 d', 'D_61-90': '61–90 d',
  'E_91-180': '91–180 d', 'F_181-365': '181–365 d', 'G_365+': '365 d +'
};
const BUCKET_COLOR = {
  B0_NOTDUE: '--age-nd', B1_1_30: '--age1', B2_31_60: '--age2', B3_61_90: '--age3',
  B4_91_180: '--age4', B5_181_365: '--age5', B6_365PLUS: '--age6',
  NOTDUE_INR: '--age-nd', D1_30_INR: '--age1', D31_60_INR: '--age2', D61_90_INR: '--age3',
  D91_180_INR: '--age4', D181_365_INR: '--age5', D365P_INR: '--age6',
  AGE_0_30_L: '--age1', AGE_31_90_L: '--age3', AGE_91_365_L: '--age5', AGE_365P_L: '--age6',
  UB_0_30: '--age1', UB_31_60: '--age2', UB_61_90: '--age3', UB_91_180: '--age4',
  UB_181_365: '--age5', UB_365PLUS: '--age6',
  UNREC_0_30_L: '--age1', UNREC_31_60_L: '--age3', UNREC_61_90_L: '--age4', UNREC_90PLUS_L: '--age6',
  A_notdue: '--age-nd', 'B_1-30': '--age1', 'C_31-60': '--age2', 'D_61-90': '--age3',
  'E_91-180': '--age4', 'F_181-365': '--age5', 'G_365+': '--age6'
};
/* Three naming conventions reached the board from three agents — detect, never
   hard-code, and keep the order (oldest bucket last). */
const BUCKET_SETS = [
  ['B0_NOTDUE', 'B1_1_30', 'B2_31_60', 'B3_61_90', 'B4_91_180', 'B5_181_365', 'B6_365PLUS'],
  ['NOTDUE_INR', 'D1_30_INR', 'D31_60_INR', 'D61_90_INR', 'D91_180_INR', 'D181_365_INR', 'D365P_INR'],
  ['A_notdue', 'B_1-30', 'C_31-60', 'D_61-90', 'E_91-180', 'F_181-365', 'G_365+'],
  ['AGE_0_30_L', 'AGE_31_90_L', 'AGE_91_365_L', 'AGE_365P_L'],
  ['UB_0_30', 'UB_31_60', 'UB_61_90', 'UB_91_180', 'UB_181_365', 'UB_365PLUS'],
  ['UNREC_0_30_L', 'UNREC_31_60_L', 'UNREC_61_90_L', 'UNREC_90PLUS_L']
];

function detectKeys(row) {
  if (!row) return null;
  for (const set of BUCKET_SETS) {
    const have = set.filter(c => c in row);
    if (have.length >= 3) return have;
  }
  return null;
}

/**
 * Stacked bars — one row per party/branch/month, one segment per ageing
 * bucket, separated by a 2px surface gap. The ageing ramp is used in its fixed
 * order (`--age-nd` for not-due, then `--age1..--age6`); `{scheme:'cat'}`
 * switches to the categorical order for non-ageing splits (max 6 + "Other").
 *
 * Every bucket total is printed in the legend — the pale end of the ramp falls
 * under 3:1 on cream, so the numbers never depend on the colour.
 *
 * @param {Array<Object>|Object} rows objects carrying the bucket columns; a
 *   single object renders one bar (v1's `ageStack`).
 * @param {Object} [opts] `keys` (array of column names, or `[{key,label,color}]`),
 *   `labelKey`, `mode:'pct'` to normalise every row to 100%, `top`.
 * @returns {Element}
 *
 * @example
 * // one bar, buckets auto-detected from the SQL column names
 * card.appendChild(stackedBars(summary[0], {title:'Vendor ageing, all branches'}));
 * // one row per branch
 * card.appendChild(stackedBars(detail, {labelKey:'BRANCH', top:12,
 *   keys:['B0_NOTDUE','B1_1_30','B2_31_60','B3_61_90','B4_91_180','B5_181_365','B6_365PLUS']}));
 */
export function stackedBars(rows, opts) {
  opts = opts || {};
  const list = Array.isArray(rows) ? rows.filter(Boolean) : (rows ? [rows] : []);
  const first = list[0] || null;

  let keys = opts.keys || detectKeys(first);
  if (!keys && first) keys = Object.keys(first).filter(k => typeof first[k] === 'number');
  keys = (keys || []).map(k => (typeof k === 'string' ? { key: k } : k)).filter(k => k && k.key);

  const isAge = opts.scheme === 'cat' ? false
    : (opts.scheme === 'age' || keys.some(k => BUCKET_COLOR[k.key]));
  let folded = 0;
  if (!isAge && keys.length > 6) { folded = keys.length - 5; keys = keys.slice(0, 5); }
  keys.forEach((k, i) => {
    k.label = k.label || BUCKET_LABEL[k.key] || String(k.key).replace(/_/g, ' ');
    k.color = k.color || (isAge ? (BUCKET_COLOR[k.key] || AGE[Math.min(i, AGE.length - 1)]) : CAT[Math.min(i, CAT.length - 1)]);
  });
  if (folded) keys.push({ key: '__other__', label: 'Other (' + folded + ' more)', color: '--soft', other: true });

  const labelKey = opts.labelKey ||
    (first ? Object.keys(first).find(k => /^(label|name|card_?name|branch|party|month|group)$/i.test(k)) : null);
  const otherKeys = folded ? (opts.keys || detectKeys(first) || []).slice(5).map(k => (typeof k === 'string' ? k : k.key)) : [];

  const bars = list.map((r, i) => {
    const vals = keys.map(k => k.other
      ? otherKeys.reduce((a, kk) => a + toNum(r[kk]), 0)
      : toNum(r[k.key]));
    return {
      label: String(labelKey && r[labelKey] != null ? r[labelKey] : (r.label != null ? r.label : (list.length === 1 ? 'Total' : 'Row ' + (i + 1)))),
      vals: vals, total: vals.reduce((a, b) => a + Math.max(0, b), 0), src: r
    };
  }).filter(b => b.total > 0 || list.length === 1);

  const ordered = opts.sort === false ? bars : bars.slice().sort((a, b) => b.total - a.total);
  const cap = opts.top == null ? 14 : opts.top;
  const shown = cap ? ordered.slice(0, cap) : ordered;
  const hidden = ordered.length - shown.length;
  const grand = keys.map((k, ki) => bars.reduce((a, b) => a + Math.max(0, b.vals[ki]), 0));
  const grandTotal = grand.reduce((a, b) => a + b, 0);

  return mount({
    kind: 'stackedBars',
    opts: opts,
    aria: grandTotal > 0
      ? 'Stacked bars over ' + keys.length + ' buckets. ' +
        keys.map((k, i) => k.label + ' ' + fmt(grand[i], opts)).join(', ') + '. Total ' + fmt(grandTotal, opts) + '.'
      : 'Stacked bars with nothing outstanding.',
    draw: ctx => {
      if (!shown.length || grandTotal <= 0) return drawEmpty(ctx, opts.emptyMsg || 'Nothing outstanding — every bucket is zero.');
      const t = ctx.top || 0, w = ctx.w;
      const one = shown.length === 1;
      const compact = w < 420;
      const fs = compact ? 11.5 : 12.5;
      const barH = one ? 26 : 20, rowH = one ? 34 : (compact ? 28 : 30);
      const pct = opts.mode === 'pct';

      const labels = shown.map(b => b.label);
      const totals = shown.map(b => fmt(b.total, opts));
      let labW = one ? 0 : labelColW(w, labels, fs, 400);
      let valW = valueColW(w, totals, fs, 650);
      let plotX = one ? 0 : labW + 10;
      let plotW = w - plotX - valW - 8;
      if (plotW < 60) { labW = w * 0.26; plotX = labW + 8; valW = w * 0.26; plotW = Math.max(30, w - plotX - valW - 6); }

      const maxTotal = Math.max.apply(null, shown.map(b => b.total));
      shown.forEach((b, i) => {
        const y = t + i * rowH, by = y + (rowH - barH) / 2 - 1;
        const full = pct ? plotW : plotW * (b.total / (maxTotal || 1));
        const track = S('rect', { x: r2(plotX), y: r2(by), width: r2(Math.max(2, full)), height: barH, rx: 6 });
        fill(track, '--line-soft');
        ctx.add(track);

        let x0 = plotX;
        keys.forEach((k, ki) => {
          const val = Math.max(0, b.vals[ki]);
          if (val <= 0) return;
          const segW = (val / (b.total || 1)) * full;
          const drawW = Math.max(2, segW - 2);        // the 2px surface gap
          const isLast = x0 + segW >= plotX + full - 0.5;
          const corners = x0 <= plotX + 0.5 ? (isLast ? 'all' : 'left') : (isLast ? 'right' : 'none');
          const seg = S('path', { d: roundRect(x0, by, drawW, barH, 6, corners), class: 'jc-mk' });
          fill(seg, k.color);
          const share = pctOf(val, b.total).toFixed(1) + '%';
          const aria = b.label + ' · ' + k.label + ': ' + fmt(val, opts) + ' (' + share + ')';
          tip(seg, aria);
          ctx.add(link(ctx, seg, b.src, i, aria));

          const lbl = pct ? share : fmt(val, opts);
          if (drawW >= tw(lbl, 10.5, 650) + 12 && barH >= 18) {
            ctx.add(TXT(lbl, x0 + drawW / 2, by + barH / 2 + 3.5,
              { size: 10.5, weight: 650, anchor: 'middle', color: inkOn(ctx.pal, ctx.pal[k.color] || ctx.pal['--c1']) }));
          }
          x0 += segW;
        });

        if (!one) ctx.add(TXT(fit(b.label, labW, fs, 400), 0, y + rowH / 2 + 4, { size: fs, color: '--ink' }));
        ctx.add(TXT(totals[i], w, y + rowH / 2 + 4, { size: fs, weight: 650, color: '--brand-deep', anchor: 'end' }));
      });

      let h = t + shown.length * rowH + 6;
      h += drawLegend(ctx, keys.map((k, ki) => ({
        label: k.label, color: k.color, value: fmt(grand[ki], opts)
      })).filter((_, ki) => grand[ki] > 0), h);

      const notes = [];
      if (hidden > 0) notes.push(hidden + ' smaller row' + (hidden === 1 ? '' : 's') + ' not drawn; they are in the table.');
      if (folded) notes.push('The last ' + folded + ' buckets are grouped as “Other” — the categorical palette stops at six.');
      if (bars.some(b => b.vals.some(x2 => x2 < 0))) notes.push('Negative bucket values are excluded from the bars (a stack cannot show them) and shown in the table.');
      if (notes.length) {
        const lines = wrapText(notes.join(' '), w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, h + 10 + i * 14, { size: 11.5, color: '--soft' })));
        h += 10 + lines.length * 14;
      }
      return h;
    },
    table: () => ({
      summary: 'The numbers behind this stack (' + bars.length + ' row' + (bars.length === 1 ? '' : 's') + ')',
      cols: [{ k: 'name', label: 'Row', align: 'txt' }]
        .concat(keys.map((k, i) => ({ k: 'k' + i, label: k.label, align: 'num' })))
        .concat([{ k: 'total', label: 'Total', align: 'num' }]),
      rows: ordered.map(b => {
        const o = { name: b.label, total: b.total, total_t: fmt(b.total, opts) };
        keys.forEach((k, i) => { o['k' + i] = b.vals[i]; o['k' + i + '_t'] = fmt(b.vals[i], opts); });
        return o;
      }),
      note: opts.tableNote
    })
  });
}

/* ══ 13. pareto ══════════════════════════════════════════════════════════ */

/**
 * Pareto — ranked bars with the cumulative line, on ONE axis. Both are plotted
 * as a percentage of the total (bar = this row's share, line = the running
 * share), so there is no second y-scale to invent a correlation; the rupee
 * value is printed beside every bar.
 *
 * @param {Array<{label:string,value:number}>} items
 * @param {Object} [opts] `top` (default 10, the tail folds into "Other (n)"),
 *   `threshold` (default 80 — the reference line).
 * @returns {Element}
 *
 * @example
 * card.appendChild(pareto(vendors.map(v => ({label:v.CardName, value:v.EFF_OPEN_INR})),
 *   {title:'Where the payable sits', top:8,
 *    href:(it)=> it.src && it.src.CardCode ? 'party.html?card='+it.src.CardCode : null}));
 */
export function pareto(items, opts) {
  opts = opts || {};
  const all = normItems(items, opts);
  const dropped = all.filter(i => !(i.value > 0));
  const pos = all.filter(i => i.value > 0).sort((a, b) => b.value - a.value);
  const capped = capCategories(pos, opts.top == null ? 10 : opts.top, opts);
  const rows = capped.items;
  const total = rows.reduce((a, b) => a + b.value, 0);
  let run = 0;
  rows.forEach(r => { r.share = pctOf(r.value, total); run += r.share; r.cum = run; });
  const threshold = opts.threshold == null ? 80 : opts.threshold;
  const crossed = rows.findIndex(r => r.cum >= threshold);

  return mount({
    kind: 'pareto',
    opts: opts,
    aria: rows.length
      ? 'Pareto of ' + rows.length + ' items totalling ' + fmt(total, opts) + '. ' +
        (crossed >= 0 ? 'The top ' + (crossed + 1) + ' carry ' + rows[crossed].cum.toFixed(0) + '% of it.' : '')
      : 'Pareto with no positive values.',
    draw: ctx => {
      if (!rows.length || total <= 0) {
        return drawEmpty(ctx, dropped.length
          ? 'Nothing to rank — all ' + dropped.length + ' values are zero or negative. They are in the table.'
          : 'Nothing to rank — no rows were passed.');
      }
      const t = ctx.top || 0, w = ctx.w;
      const compact = w < 440;
      const fs = compact ? 11.5 : 12.5;
      const rowH = compact ? 32 : 38, barH = 15;

      const labels = rows.map(r => r.label);
      const vals = rows.map(r => fmt(r.value, opts));
      let labW = labelColW(w, labels, fs, 400);
      let valW = valueColW(w, vals, fs, 650);
      let plotX = labW + 10, plotW = w - plotX - valW - 8;
      if (plotW < 60) { labW = w * 0.26; plotX = labW + 8; valW = w * 0.26; plotW = Math.max(30, w - plotX - valW - 6); }
      const x = p => plotX + (Math.max(0, Math.min(100, p)) / 100) * plotW;
      const plotH = rows.length * rowH;

      [25, 50, 75, 100].forEach(g => {
        const gl = S('line', { x1: r2(x(g)), y1: t, x2: r2(x(g)), y2: t + plotH });
        stroke(gl, '--line-soft'); gl.style.strokeWidth = '1px';
        ctx.add(gl);
      });
      const th = S('line', { x1: r2(x(threshold)), y1: t, x2: r2(x(threshold)), y2: t + plotH });
      stroke(th, '--line'); th.style.strokeWidth = '1px';
      ctx.add(th);
      ctx.add(TXT(threshold + '%', x(threshold), t + plotH + 13, { size: 10.5, color: '--soft', anchor: 'middle' }));
      ctx.add(TXT('0%', plotX, t + plotH + 13, { size: 10.5, color: '--soft' }));
      ctx.add(TXT('100%', x(100), t + plotH + 13, { size: 10.5, color: '--soft', anchor: 'end' }));

      rows.forEach((r, i) => {
        const y = t + i * rowH, by = y + (rowH - barH) / 2 - (compact ? 1 : 5);
        const bw = Math.max(2.5, x(r.share) - plotX);
        const bar = S('path', { d: roundRect(plotX, by, bw, barH, 4, 'right'), class: 'jc-mk' });
        fill(bar, r.other ? '--soft' : '--c1');
        const aria = r.label + ': ' + fmt(r.value, opts) + ' — ' + r.share.toFixed(1) + '% of the total, ' +
          r.cum.toFixed(1) + '% cumulative' + (r.other ? '. ' + r._text : '');
        tip(bar, aria);
        ctx.add(link(ctx, bar, r.src, i, aria));
        ctx.add(TXT(fit(r.label, labW, fs, 400), 0, y + rowH / 2 + (compact ? 4 : 0), { size: fs, color: '--ink' }));
        ctx.add(TXT(vals[i], w, y + rowH / 2 + (compact ? 4 : 0), { size: fs, weight: 650, color: '--brand-deep', anchor: 'end' }));
        if (!compact) {
          ctx.add(TXT(r.share.toFixed(1) + '% · cum ' + r.cum.toFixed(0) + '%', w, y + rowH / 2 + 13,
            { size: 10.5, color: '--soft', anchor: 'end' }));
        }
      });

      const line = S('path', {
        d: rows.map((r, i) => (i ? 'L' : 'M') + r2(x(r.cum)) + ',' + r2(t + i * rowH + rowH / 2)).join('')
      });
      line.style.fill = 'none'; stroke(line, '--c2');
      line.style.strokeWidth = '2px'; line.style.strokeLinejoin = 'round'; line.style.strokeLinecap = 'round';
      ctx.add(line);
      rows.forEach((r, i) => {
        const dot = S('circle', { cx: r2(x(r.cum)), cy: r2(t + i * rowH + rowH / 2), r: 4, class: 'jc-mk' });
        fill(dot, '--c2'); stroke(dot, '--card'); dot.style.strokeWidth = '2px';
        ctx.add(tip(dot, 'Cumulative through ' + r.label + ': ' + r.cum.toFixed(1) + '% (' +
          fmt(rows.slice(0, i + 1).reduce((a, b) => a + b.value, 0), opts) + ')'));
      });

      let h = t + plotH + 20;
      h += drawLegend(ctx, [
        { label: 'Share of the total (bar)', color: '--c1' },
        { label: 'Cumulative share (line)', color: '--c2' }
      ], h);

      const notes = [];
      if (crossed >= 0) notes.push('The top ' + (crossed + 1) + ' of ' + pos.length + ' carry ' + rows[crossed].cum.toFixed(0) + '% of ' + fmt(total, opts) + '.');
      if (capped.folded) notes.push('The smallest ' + capped.folded + ' are grouped as “Other”.');
      if (dropped.length) notes.push(dropped.length + ' zero or negative row' + (dropped.length === 1 ? '' : 's') + ' cannot be ranked as a share and are listed in the table only.');
      if (notes.length) {
        const lines = wrapText(notes.join(' '), w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, h + 10 + i * 14, { size: 11.5, color: '--soft' })));
        h += 10 + lines.length * 14;
      }
      return h;
    },
    table: () => ({
      summary: 'The ranking behind this pareto (' + all.length + ' row' + (all.length === 1 ? '' : 's') + ')',
      cols: [
        { k: 'name', label: 'Item', align: 'txt' },
        { k: 'val', label: 'Value', align: 'num' },
        { k: 'share', label: 'Share', align: 'num' },
        { k: 'cum', label: 'Cumulative', align: 'num' }
      ],
      rows: rows.map(r => ({
        name: r.label, val: r.value, val_t: fmt(r.value, opts),
        share: r.share, share_t: r.share.toFixed(1) + '%',
        cum: r.cum, cum_t: r.cum.toFixed(1) + '%'
      })).concat(dropped.map(d => ({
        name: d.label, val: d.value, val_t: fmt(d.value, opts),
        share: null, share_t: 'not ranked', cum: null, cum_t: '—'
      }))),
      note: opts.tableNote
    })
  });
}

/* ══ 14. treemap ═════════════════════════════════════════════════════════ */

function worstRatio(row, sum, side) {
  let mx = 0, mn = Infinity;
  for (const n of row) { mx = Math.max(mx, n.a); mn = Math.min(mn, n.a); }
  if (!mn || !sum) return Infinity;
  const s2 = side * side, sum2 = sum * sum;
  return Math.max(s2 * mx / sum2, sum2 / (s2 * mn));
}

/** Classic squarified treemap. `nodes` carry a pre-scaled area `a`. */
function squarify(nodes, x, y, w, h, out, depth) {
  if (!nodes.length || w <= 0 || h <= 0 || (depth || 0) > 200) return;
  if (nodes.length === 1) { out.push({ n: nodes[0], x: x, y: y, w: w, h: h }); return; }
  const side = Math.min(w, h);
  const row = [];
  let sum = 0, best = Infinity, i = 0;
  while (i < nodes.length) {
    const cand = row.concat([nodes[i]]);
    const r = worstRatio(cand, sum + nodes[i].a, side);
    if (!row.length || r <= best) { row.push(nodes[i]); sum += nodes[i].a; best = r; i++; } else break;
  }
  const rest = nodes.slice(row.length);
  if (w >= h) {
    const rw = h > 0 ? sum / h : w;
    let yy = y;
    for (const n of row) { const nh = rw > 0 ? n.a / rw : 0; out.push({ n: n, x: x, y: yy, w: rw, h: nh }); yy += nh; }
    squarify(rest, x + rw, y, w - rw, h, out, (depth || 0) + 1);
  } else {
    const rh = w > 0 ? sum / w : h;
    let xx = x;
    for (const n of row) { const nw = rh > 0 ? n.a / rh : 0; out.push({ n: n, x: xx, y: y, w: nw, h: rh }); xx += nw; }
    squarify(rest, x, y + rh, w, h - rh, out, (depth || 0) + 1);
  }
}

/**
 * Treemap — area is the magnitude. Tiles are separated by a 2px surface gap;
 * the name and value sit inside wherever they fit with padding, and every tile
 * carries a `<title>` besides.
 *
 * Default `color:'cat'` paints the six biggest tiles `--c1..--c6` in fixed
 * order and folds the rest into "Other (n)". `color:'single'` treats the tiles
 * as one series (all `--c1`) and then any number of tiles is legitimate — use
 * that when you want the long tail visible.
 *
 * @param {Array<{label:string,value:number}>} items
 * @param {Object} [opts] `color:'cat'|'single'`, `top` (single mode, default 24),
 *   `height` (default ~half the width).
 * @returns {Element}
 *
 * @example
 * card.appendChild(treemap(groups.map(g => ({label:g.GROUP_NAME, value:g.BALANCE_INR})),
 *   {title:'Payables by vendor group', color:'cat'}));
 */
export function treemap(items, opts) {
  opts = opts || {};
  const all = normItems(items, opts);
  const dropped = all.filter(i => !(i.value > 0));
  const pos = all.filter(i => i.value > 0).sort((a, b) => b.value - a.value);
  const single = opts.color === 'single';
  let tiles, folded = 0;
  if (single) { tiles = pos.slice(0, opts.top == null ? 24 : opts.top); folded = 0; }
  else { const c = capCategories(pos, 6, opts); tiles = c.items; folded = c.folded; }
  const hiddenSingle = single ? pos.length - tiles.length : 0;
  const total = tiles.reduce((a, b) => a + b.value, 0);
  tiles.forEach((t2, i) => { t2.color = t2.other ? '--soft' : (single ? '--c1' : CAT[Math.min(i, 5)]); });

  return mount({
    kind: 'treemap',
    opts: opts,
    aria: total > 0
      ? 'Treemap of ' + tiles.length + ' tiles totalling ' + fmt(total, opts) + '. ' +
        tiles.map(t2 => t2.label + ' ' + fmt(t2.value, opts)).join(', ') + '.'
      : 'Treemap with nothing to show.',
    draw: ctx => {
      if (!tiles.length || total <= 0) {
        return drawEmpty(ctx, dropped.length
          ? 'No positive values to lay out — all ' + dropped.length + ' rows are zero or negative (a treemap has no area for them). They are in the table.'
          : 'No rows to lay out.');
      }
      const t = ctx.top || 0, w = ctx.w;
      const h = Math.round(opts.height || Math.max(170, Math.min(w * 0.5, 320)));
      const scale = (w * h) / total;
      const nodes = tiles.map(x => ({ t: x, a: Math.max(1, x.value * scale) }));
      const out = [];
      squarify(nodes, 0, t, w, h, out, 0);

      out.forEach((cell, i) => {
        const it = cell.n.t;
        const x = cell.x + 1, y = cell.y + 1;
        const cw = Math.max(1, cell.w - 2), ch = Math.max(1, cell.h - 2);
        const rect = S('rect', { x: r2(x), y: r2(y), width: r2(cw), height: r2(ch), rx: Math.min(5, cw / 2, ch / 2), class: 'jc-mk' });
        fill(rect, it.color);
        const share = pctOf(it.value, total).toFixed(1) + '%';
        const aria = it.label + ': ' + fmt(it.value, opts) + ' (' + share + ' of ' + fmt(total, opts) + ')' +
          (it.other ? '. ' + it._text : '');
        tip(rect, aria);
        ctx.add(link(ctx, rect, it.src, i, aria));

        const ink = inkOn(ctx.pal, ctx.pal[it.color] || ctx.pal['--c1']);
        const valTxt = fmt(it.value, opts);
        const pad = 7;
        if (ch >= 34 && cw >= tw(valTxt, 12, 700) + pad * 2) {
          const nameTxt = fit(it.label, cw - pad * 2, 11.5, 500);
          if (nameTxt && ch >= 46) {
            ctx.add(TXT(nameTxt, x + pad, y + pad + 11, { size: 11.5, weight: 500, color: ink, opacity: .92 }));
            ctx.add(TXT(valTxt, x + pad, y + pad + 28, { size: 13, weight: 700, color: ink }));
          } else {
            ctx.add(TXT(valTxt, x + pad, y + pad + 12, { size: 12, weight: 700, color: ink }));
          }
          if (ch >= 62 && cw >= tw(share, 10.5, 400) + pad * 2) {
            ctx.add(TXT(share, x + pad, y + pad + 44, { size: 10.5, color: ink, opacity: .8 }));
          }
        } else if (ch >= 18 && cw >= tw(valTxt, 10.5, 650) + 10) {
          ctx.add(TXT(valTxt, x + cw / 2, y + ch / 2 + 3.5, { size: 10.5, weight: 650, color: ink, anchor: 'middle' }));
        }
      });

      let hh = t + h + 8;
      hh += drawLegend(ctx, tiles.map(x => ({ label: x.label, color: x.color, value: fmt(x.value, opts) })), hh);

      const notes = [];
      if (folded) notes.push('The smallest ' + folded + ' are grouped as “Other” — the categorical palette stops at six; pass {color:"single"} to see them all.');
      if (hiddenSingle > 0) notes.push(hiddenSingle + ' smaller tile' + (hiddenSingle === 1 ? '' : 's') + ' not drawn; they are in the table.');
      if (dropped.length) notes.push(dropped.length + ' zero or negative row' + (dropped.length === 1 ? '' : 's') + ' cannot be given an area and are in the table only.');
      if (notes.length) {
        const lines = wrapText(notes.join(' '), w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, hh + 10 + i * 14, { size: 11.5, color: '--soft' })));
        hh += 10 + lines.length * 14;
      }
      return hh;
    },
    table: () => ({
      summary: 'The tiles behind this treemap (' + all.length + ' row' + (all.length === 1 ? '' : 's') + ')',
      cols: [
        { k: 'name', label: 'Item', align: 'txt' },
        { k: 'val', label: 'Value', align: 'num' },
        { k: 'share', label: 'Share', align: 'num' }
      ],
      rows: tiles.map(x => ({
        name: x.label, name_c: x.color, val: x.value, val_t: fmt(x.value, opts),
        share: pctOf(x.value, total), share_t: pctOf(x.value, total).toFixed(1) + '%'
      })).concat(
        (single ? pos.slice(tiles.length) : []).concat(dropped).map(d => ({
          name: d.label, val: d.value, val_t: fmt(d.value, opts), share: null, share_t: '—'
        }))
      ),
      note: opts.tableNote
    })
  });
}

/* ══ 15. donut ═══════════════════════════════════════════════════════════ */

function polar(cx, cy, r, a) { return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; }

function ringSlice(cx, cy, r0, r1, a0, a1) {
  const big = (a1 - a0) > Math.PI ? 1 : 0;
  const p0 = polar(cx, cy, r1, a0), p1 = polar(cx, cy, r1, a1);
  const p2 = polar(cx, cy, r0, a1), p3 = polar(cx, cy, r0, a0);
  return 'M' + r2(p0[0]) + ',' + r2(p0[1]) +
    'A' + r2(r1) + ',' + r2(r1) + ' 0 ' + big + ' 1 ' + r2(p1[0]) + ',' + r2(p1[1]) +
    'L' + r2(p2[0]) + ',' + r2(p2[1]) +
    'A' + r2(r0) + ',' + r2(r0) + ' 0 ' + big + ' 0 ' + r2(p3[0]) + ',' + r2(p3[1]) + 'Z';
}

/**
 * Donut — part-to-whole at a glance, six slices at most (the seventh onwards
 * folds into "Other (n)"). The total sits in the hole, each slice ≥ 9% carries
 * its percentage inside the ring, and the legend prints every rupee value, so
 * nothing is readable only by colour.
 *
 * Use it only when the parts genuinely make a whole and the reader needs the
 * split at a glance; for comparing close values a bar list reads better.
 *
 * @param {Array<{label:string,value:number}>} items
 * @param {Object} [opts] `centerLabel` (default "total"), `height`.
 * @returns {Element}
 *
 * @example
 * card.appendChild(donut([
 *   {label:'Trade',        value: 226800000},
 *   {label:'Branch',       value: 775800000},
 *   {label:'Intercompany', value:  22500000}
 * ], {title:'Who the open A/P is owed to', centerLabel:'open A/P'}));
 */
export function donut(items, opts) {
  opts = opts || {};
  const all = normItems(items, opts);
  const dropped = all.filter(i => !(i.value > 0));
  const pos = all.filter(i => i.value > 0).sort((a, b) => b.value - a.value);
  const capped = capCategories(pos, 6, opts);
  const slices = capped.items;
  slices.forEach((s, i) => { s.color = s.other ? '--soft' : CAT[Math.min(i, 5)]; });
  const total = slices.reduce((a, b) => a + b.value, 0);

  return mount({
    kind: 'donut',
    opts: opts,
    aria: total > 0
      ? 'Donut of ' + fmt(total, opts) + ': ' +
        slices.map(s => s.label + ' ' + fmt(s.value, opts) + ' (' + pctOf(s.value, total).toFixed(0) + '%)').join(', ') + '.'
      : 'Donut with nothing to split.',
    draw: ctx => {
      if (!slices.length || total <= 0) {
        return drawEmpty(ctx, dropped.length
          ? 'Nothing to split — all ' + dropped.length + ' values are zero or negative, and a share of a whole cannot show them. They are in the table.'
          : 'Nothing to split — no rows were passed.');
      }
      const t = ctx.top || 0, w = ctx.w;
      const side = w >= 460;
      const size = Math.round(Math.min(side ? w * 0.42 : w - 8, opts.height || 240, 260));
      const r1 = size / 2, r0 = r1 * 0.62;
      const cx = side ? r1 : w / 2, cy = t + r1;

      let a = -Math.PI / 2;
      slices.forEach((s, i) => {
        const frac = s.value / total;
        const a1 = a + frac * Math.PI * 2;
        let node;
        if (slices.length === 1) {
          node = S('circle', { cx: r2(cx), cy: r2(cy), r: r2((r0 + r1) / 2), class: 'jc-mk' });
          node.style.fill = 'none';
          node.style.stroke = v(s.color);
          node.style.strokeWidth = (r1 - r0) + 'px';
        } else {
          node = S('path', { d: ringSlice(cx, cy, r0, r1, a, a1), class: 'jc-mk' });
          fill(node, s.color);
          stroke(node, '--card'); node.style.strokeWidth = '2px'; node.style.strokeLinejoin = 'round';
        }
        const share = pctOf(s.value, total);
        const aria = s.label + ': ' + fmt(s.value, opts) + ' (' + share.toFixed(1) + '%)' + (s.other ? '. ' + s._text : '');
        tip(node, aria);
        ctx.add(link(ctx, node, s.src, i, aria));

        if (share >= 9 && (r1 - r0) >= 26) {
          const mid = (a + a1) / 2, rm = (r0 + r1) / 2;
          const p = polar(cx, cy, rm, mid);
          ctx.add(TXT(share.toFixed(0) + '%', p[0], p[1] + 4,
            { size: 11.5, weight: 650, anchor: 'middle', color: inkOn(ctx.pal, ctx.pal[s.color] || ctx.pal['--c1']) }));
        }
        a = a1;
      });

      const totalTxt = fmt(total, opts);
      let ts = Math.min(22, Math.max(13, (r0 * 1.75) / Math.max(4, totalTxt.length) * 1.9));
      while (tw(totalTxt, ts, 700) > r0 * 1.8 && ts > 10) ts -= 0.5;
      ctx.add(TXT(totalTxt, cx, cy + (opts.centerLabel === false ? 5 : 1), { size: ts, weight: 700, color: '--brand-deep', anchor: 'middle' }));
      if (opts.centerLabel !== false) {
        ctx.add(TXT(fit(opts.centerLabel || 'total', r0 * 1.7, 10.5, 400), cx, cy + 15,
          { size: 10.5, color: '--soft', anchor: 'middle' }));
      }

      const legendItems = slices.map(s => ({
        label: s.label, color: s.color, value: fmt(s.value, opts) + '  ' + pctOf(s.value, total).toFixed(1) + '%'
      }));
      let h;
      if (side) {
        const lx = size + 22;
        let ly = t + Math.max(0, r1 - legendItems.length * 11);
        legendItems.forEach(li => {
          const sq = S('rect', { x: r2(lx), y: r2(ly + 1), width: 10, height: 10, rx: 2.5 });
          fill(sq, li.color); ctx.add(sq);
          const avail = w - lx - 15;
          ctx.add(TXT(fit(li.label, avail * 0.55, 12, 500), lx + 15, ly + 9.5, { size: 12, weight: 500, color: '--ink' }));
          ctx.add(TXT(li.value, w, ly + 9.5, { size: 11.5, weight: 650, color: '--sage', anchor: 'end' }));
          ly += 22;
        });
        h = Math.max(t + size, ly) + 4;
      } else {
        h = t + size + 10;
        h += drawLegend(ctx, legendItems, h);
      }

      const notes = [];
      if (capped.folded) notes.push('The smallest ' + capped.folded + ' are grouped as “Other”.');
      if (dropped.length) notes.push(dropped.length + ' zero or negative row' + (dropped.length === 1 ? '' : 's') + ' left out of the split; they are in the table.');
      if (notes.length) {
        const lines = wrapText(notes.join(' '), w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, h + 10 + i * 14, { size: 11.5, color: '--soft' })));
        h += 10 + lines.length * 14;
      }
      return h;
    },
    table: () => ({
      summary: 'The split behind this donut (' + all.length + ' row' + (all.length === 1 ? '' : 's') + ')',
      cols: [
        { k: 'name', label: 'Part', align: 'txt' },
        { k: 'val', label: 'Value', align: 'num' },
        { k: 'share', label: 'Share', align: 'num' }
      ],
      rows: slices.map(s => ({
        name: s.label, name_c: s.color, val: s.value, val_t: fmt(s.value, opts),
        share: pctOf(s.value, total), share_t: pctOf(s.value, total).toFixed(1) + '%'
      })).concat(dropped.map(d => ({ name: d.label, val: d.value, val_t: fmt(d.value, opts), share: null, share_t: 'not in the split' }))),
      note: opts.tableNote
    })
  });
}

/* ══ 16. lineArea ════════════════════════════════════════════════════════ */

function normSeries(series, opts) {
  if (!series) return [];
  const arr = Array.isArray(series) ? series : [series];
  if (!arr.length) return [];
  const looksLikeOne = typeof arr[0] === 'number' ||
    (arr[0] && !arr[0].points && !arr[0].values && (arr[0].y != null || arr[0].value != null || arr[0].x != null));
  if (looksLikeOne) return [{ name: (opts && opts.name) || '', points: normSeriesValues(arr) }];
  return arr.filter(Boolean).map((s, i) => ({
    name: String(s.name != null ? s.name : (s.label != null ? s.label : 'Series ' + (i + 1))),
    points: normSeriesValues(s.points || s.values || s.data || []),
    src: s
  })).filter(s => s.points.length);
}

/**
 * Line / area over time. One y-axis, always — two measures of different scale
 * belong in two charts, never on a second axis.
 *
 * A single series gets a 2px line over a 10% area wash and no legend (the
 * title names it); two to six series get lines plus a legend, with the last
 * point of each direct-labelled where the labels do not collide. A seventh
 * series is summed into "Other (n)" rather than taking a seventh hue — pass
 * `{foldTail:false}` to leave it out and say so instead.
 *
 * @param {Array} series `[{name, points:[{x,y}]}]`, or a bare `[y,…]` /
 *   `[{x,y}]` for one series.
 * @param {Object} [opts] `height`, `zero:false` to let the axis float off zero,
 *   `area:false` to drop the wash.
 * @returns {Element}
 *
 * @example
 * card.appendChild(lineArea([
 *   {name:'Oil',  points: months.map(m => ({x:m.MONTH, y:m.TURNOVER_INR}))},
 *   {name:'Mart', points: mart.map(m => ({x:m.MONTH, y:m.TURNOVER_INR}))}
 * ], {title:'Turnover, net of GST', height:220}));
 */
export function lineArea(series, opts) {
  opts = opts || {};
  let all = normSeries(series, opts);
  let folded = 0, foldedNames = [];
  if (all.length > 6) {
    const keep = all.slice(0, 5), tail = all.slice(5);
    folded = tail.length; foldedNames = tail.map(s => s.name);
    if (opts.foldTail !== false) {
      const len = Math.max.apply(null, tail.map(s => s.points.length));
      const pts = [];
      for (let i = 0; i < len; i++) {
        const ref = tail.find(s => s.points[i]);
        pts.push({ label: ref ? ref.points[i].label : String(i + 1), value: tail.reduce((a, s) => a + (s.points[i] ? s.points[i].value : 0), 0) });
      }
      keep.push({ name: 'Other (' + tail.length + ' more)', points: pts, other: true });
    }
    all = keep;
  }
  all.forEach((s, i) => { s.color = s.other ? '--soft' : CAT[Math.min(i, 5)]; });
  const flatAll = all.reduce((a, s) => a.concat(s.points.map(p => p.value)), []);
  const nPts = Math.max.apply(null, all.map(s => s.points.length).concat([0]));

  return mount({
    kind: 'lineArea',
    opts: opts,
    aria: all.length
      ? all.map(s => s.name + (s.name ? ': ' : '') + 'from ' + fmt(s.points[0].value, opts) +
          ' to ' + fmt(s.points[s.points.length - 1].value, opts) + ' over ' + s.points.length + ' points').join('; ') + '.'
      : 'Line chart with no series.',
    draw: ctx => {
      if (!all.length || !flatAll.length) return drawEmpty(ctx, opts.emptyMsg || 'No history to plot yet.');
      const t = ctx.top || 0, w = ctx.w;
      const plotH = Math.round(opts.height || Math.max(150, Math.min(w * 0.42, 300)));
      const single = all.length === 1;

      let lo = Math.min.apply(null, flatAll), hi = Math.max.apply(null, flatAll);
      if (opts.zero !== false && lo > 0) lo = 0;
      if (opts.zero !== false && hi < 0) hi = 0;
      if (lo === hi) { const pad = Math.abs(hi) || 1; lo = hi - pad * 0.5; hi = hi + pad * 0.5; }
      const tk = ticks(lo, hi, 4);
      lo = Math.min(lo, tk[0]); hi = Math.max(hi, tk[tk.length - 1]);

      const tickTxt = tk.map(x => fmt(x, opts));
      const padL = Math.min(w * 0.3, Math.max.apply(null, tickTxt.map(s => tw(s, 10.5, 400))) + 8);
      const endTxts = all.map(s => fmt(s.points[s.points.length - 1].value, opts));
      const padR = Math.min(w * 0.26, Math.max.apply(null, endTxts.map(s => tw(s, 11, 650))) + 12);
      const padB = 20;
      const x0 = padL, x1 = Math.max(padL + 20, w - padR);
      const y0 = t + 6, y1 = t + plotH - padB;

      const Y = val => y1 - (val - lo) / (hi - lo || 1) * (y1 - y0);
      const X = i => nPts <= 1 ? (x0 + x1) / 2 : x0 + (i / (nPts - 1)) * (x1 - x0);

      tk.forEach((val, i) => {
        const y = Y(val);
        const gl = S('line', { x1: r2(x0), y1: r2(y), x2: r2(x1), y2: r2(y) });
        stroke(gl, val === 0 ? '--line' : '--line-soft'); gl.style.strokeWidth = '1px';
        ctx.add(gl);
        ctx.add(TXT(tickTxt[i], x0 - 6, y + 3.5, { size: 10.5, color: '--soft', anchor: 'end', tabular: true }));
      });

      const labels = (all[0] ? all[0].points : []).map(p => p.label);
      let lastX = -Infinity;
      labels.forEach((lb, i) => {
        if (i !== 0 && i !== labels.length - 1 && labels.length > 3) {
          const step = Math.ceil(labels.length / Math.max(2, Math.floor((x1 - x0) / 64)));
          if (i % step) return;
        }
        const xx = X(i), width = tw(lb, 10.5, 400);
        if (xx - width / 2 < lastX + 6) return;
        lastX = xx + width / 2;
        ctx.add(TXT(fit(lb, 84, 10.5, 400), Math.min(Math.max(xx, x0 + width / 2), x1), t + plotH - 4,
          { size: 10.5, color: '--soft', anchor: 'middle' }));
      });

      all.forEach((s, si) => {
        const d = s.points.map((p, i) => (i ? 'L' : 'M') + r2(X(i)) + ',' + r2(Y(p.value))).join('');
        if (single && opts.area !== false && s.points.length > 1) {
          const zeroY = Math.min(y1, Math.max(y0, Y(Math.max(lo, Math.min(0, hi)))));
          const area = S('path', { d: d + 'L' + r2(X(s.points.length - 1)) + ',' + r2(zeroY) + 'L' + r2(X(0)) + ',' + r2(zeroY) + 'Z' });
          fill(area, s.color); area.style.fillOpacity = '.10';
          ctx.add(area);
        }
        if (s.points.length > 1) {
          const line = S('path', { d: d, class: 'jc-mk' });
          line.style.fill = 'none'; stroke(line, s.color);
          line.style.strokeWidth = '2px'; line.style.strokeLinejoin = 'round'; line.style.strokeLinecap = 'round';
          ctx.add(tip(line, s.name || 'series'));
        }
        s.points.forEach((p, i) => {
          const showDot = s.points.length === 1 || i === s.points.length - 1 || s.points.length <= 14;
          if (!showDot) return;
          const dot = S('circle', { cx: r2(X(i)), cy: r2(Y(p.value)), r: i === s.points.length - 1 ? 4 : 3.2, class: 'jc-mk' });
          fill(dot, s.color); stroke(dot, '--card'); dot.style.strokeWidth = '2px';
          const aria = (s.name ? s.name + ' · ' : '') + p.label + ': ' + fmt(p.value, opts);
          tip(dot, aria);
          ctx.add(link(ctx, dot, p, i, aria));
        });
      });

      // end labels, dropped where they would collide
      const taken = [];
      all.slice().sort((a, b) => b.points[b.points.length - 1].value - a.points[a.points.length - 1].value)
        .forEach(s => {
          const last = s.points[s.points.length - 1];
          const yy = Y(last.value);
          if (taken.some(o => Math.abs(o - yy) < 13)) return;
          taken.push(yy);
          ctx.add(TXT(fmt(last.value, opts), Math.min(X(s.points.length - 1) + 7, w), Math.min(Math.max(yy + 4, y0 + 4), y1),
            { size: 11, weight: 650, color: '--ink', halo: true }));
        });

      let h = t + plotH + 4;
      if (!single) h += drawLegend(ctx, all.map(s => ({ label: s.name, color: s.color })), h);

      const notes = [];
      if (nPts === 1) notes.push('Only one point in the history — there is no trend to draw yet.');
      if (flatAll.every(x => x === 0)) notes.push('Every point is zero.');
      if (folded && opts.foldTail !== false) notes.push('The last ' + folded + ' series are summed as “Other” (' + foldedNames.join(', ') + ') — the palette stops at six.');
      if (folded && opts.foldTail === false) notes.push(folded + ' further series are not drawn (' + foldedNames.join(', ') + '); the palette stops at six.');
      if (notes.length) {
        const lines = wrapText(notes.join(' '), w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, h + 10 + i * 14, { size: 11.5, color: '--soft' })));
        h += 10 + lines.length * 14;
      }
      return h;
    },
    table: () => {
      const labels = [];
      all.forEach(s => s.points.forEach((p, i) => { if (labels[i] == null) labels[i] = p.label; }));
      return {
        summary: 'The points behind this chart (' + labels.length + ' × ' + all.length + ')',
        cols: [{ k: 'x', label: 'Point', align: 'txt' }].concat(all.map((s, i) => ({ k: 's' + i, label: s.name || 'Value', align: 'num' }))),
        rows: labels.map((lb, i) => {
          const o = { x: lb };
          all.forEach((s, si) => {
            const p = s.points[i];
            o['s' + si] = p ? p.value : null;
            o['s' + si + '_t'] = p ? fmt(p.value, opts) : '—';
          });
          return o;
        }),
        note: opts.tableNote
      };
    }
  });
}

/* ══ 17. scatter ═════════════════════════════════════════════════════════ */

/**
 * Scatter — one dot per document/party, typically days on x against rupees on
 * y. Dots carry a 2px surface ring so overlaps stay readable, the extremes are
 * direct-labelled, and every dot carries a `<title>`.
 *
 * Dots take `--c1` unless a `group` is given, in which case the groups take
 * `--c1..--c6` in fixed order with a seventh onwards folded into "Other (n)".
 *
 * @param {Array<{x:number,y:number,label:string,group:string,href:string}>} points
 * @param {Object} [opts] `xLabel`, `yLabel`, `xUnit` (default 'd'), `height`,
 *   `labels` (how many extremes to name, default 3).
 * @returns {Element}
 *
 * @example
 * card.appendChild(scatter(open.map(r => ({
 *   x: r.AGE_DAYS, y: r.BALANCE_INR, label: r.CardName, group: r.KIND
 * })), {title:'Open items: age against size', xLabel:'days open', yLabel:'balance'}));
 */
export function scatter(points, opts) {
  opts = opts || {};
  const xOpts = { unit: opts.xUnit || 'd', format: opts.xFormat };
  const pts = (points || []).filter(p => p && isFinite(Number(p.x)) && isFinite(Number(p.y)))
    .map((p, i) => ({
      x: Number(p.x), y: Number(p.y),
      label: String(p.label != null ? p.label : (p.name != null ? p.name : i + 1)),
      group: p.group != null ? String(p.group) : null, src: p
    }));
  const groups = [];
  for (const p of pts) if (p.group && groups.indexOf(p.group) < 0) groups.push(p.group);
  const gTotals = groups.map(g => ({ label: g, value: pts.filter(p => p.group === g).length }));
  gTotals.sort((a, b) => b.value - a.value);
  const kept = gTotals.slice(0, 6).map(g => g.label);
  const gColor = g => { const i = kept.indexOf(g); return i >= 0 ? CAT[i] : '--soft'; };
  const foldedGroups = Math.max(0, groups.length - kept.length);

  return mount({
    kind: 'scatter',
    opts: opts,
    aria: pts.length
      ? 'Scatter of ' + pts.length + ' points, ' + (opts.xLabel || 'x') + ' against ' + (opts.yLabel || 'y') + '.'
      : 'Scatter with no points.',
    draw: ctx => {
      if (!pts.length) return drawEmpty(ctx, opts.emptyMsg || 'No points to plot.');
      const t = ctx.top || 0, w = ctx.w;
      const plotH = Math.round(opts.height || Math.max(170, Math.min(w * 0.52, 320)));

      let xlo = Math.min.apply(null, pts.map(p => p.x)), xhi = Math.max.apply(null, pts.map(p => p.x));
      let ylo = Math.min.apply(null, pts.map(p => p.y)), yhi = Math.max.apply(null, pts.map(p => p.y));
      if (ylo > 0) ylo = 0;
      if (yhi < 0) yhi = 0;
      if (xlo === xhi) { xlo -= 1; xhi += 1; }
      if (ylo === yhi) { const pad = Math.abs(yhi) || 1; ylo -= pad * 0.5; yhi += pad * 0.5; }
      const ytk = ticks(ylo, yhi, 4), xtk = ticks(xlo, xhi, 4);
      ylo = Math.min(ylo, ytk[0]); yhi = Math.max(yhi, ytk[ytk.length - 1]);
      xlo = Math.min(xlo, xtk[0]); xhi = Math.max(xhi, xtk[xtk.length - 1]);

      const ytxt = ytk.map(x => fmt(x, opts));
      const padL = Math.min(w * 0.3, Math.max.apply(null, ytxt.map(s => tw(s, 10.5, 400))) + 8);
      const padR = 10, padB = opts.xLabel ? 32 : 20;
      const x0 = padL, x1 = Math.max(padL + 20, w - padR);
      const y0 = t + 8, y1 = t + plotH - padB;
      const X = val => x0 + (val - xlo) / (xhi - xlo || 1) * (x1 - x0);
      const Y = val => y1 - (val - ylo) / (yhi - ylo || 1) * (y1 - y0);

      ytk.forEach((val, i) => {
        const y = Y(val);
        const gl = S('line', { x1: r2(x0), y1: r2(y), x2: r2(x1), y2: r2(y) });
        stroke(gl, val === 0 ? '--line' : '--line-soft'); gl.style.strokeWidth = '1px';
        ctx.add(gl);
        ctx.add(TXT(ytxt[i], x0 - 6, y + 3.5, { size: 10.5, color: '--soft', anchor: 'end', tabular: true }));
      });
      let lastX = -Infinity;
      xtk.forEach(val => {
        const xx = X(val), s = fmt(val, xOpts), width = tw(s, 10.5, 400);
        if (xx - width / 2 < lastX + 8 || xx > x1 + 1) return;
        lastX = xx + width / 2;
        ctx.add(TXT(s, xx, y1 + 14, { size: 10.5, color: '--soft', anchor: 'middle', tabular: true }));
      });
      if (opts.xLabel) ctx.add(TXT(opts.xLabel, (x0 + x1) / 2, y1 + 29, { size: 11, color: '--sage', anchor: 'middle' }));
      if (opts.yLabel) ctx.add(TXT(opts.yLabel, x0 - 6, t + 2, { size: 11, color: '--sage', anchor: 'end' }));

      const rr = opts.r || 5;
      pts.forEach((p, i) => {
        const dot = S('circle', { cx: r2(X(p.x)), cy: r2(Y(p.y)), r: rr, class: 'jc-mk' });
        fill(dot, p.group ? gColor(p.group) : (opts.color || '--c1'));
        stroke(dot, '--card'); dot.style.strokeWidth = '2px';
        const aria = p.label + ' — ' + fmt(p.x, xOpts) + ', ' + fmt(p.y, opts) + (p.group ? ' (' + p.group + ')' : '');
        tip(dot, aria);
        ctx.add(link(ctx, dot, p.src, i, aria));
      });

      const nLab = opts.labels == null ? 3 : opts.labels;
      const taken = [];
      pts.slice().sort((a, b) => Math.abs(b.y) - Math.abs(a.y)).slice(0, nLab).forEach(p => {
        const px = X(p.x), py = Y(p.y);
        if (taken.some(o => Math.abs(o[0] - px) < 70 && Math.abs(o[1] - py) < 14)) return;
        taken.push([px, py]);
        const s = fit(p.label, 130, 10.5, 600) + ' ' + fmt(p.y, opts);
        const right = px < (x0 + x1) / 2;
        ctx.add(TXT(s, right ? px + rr + 5 : px - rr - 5, py + 3.5,
          { size: 10.5, weight: 600, color: '--ink', anchor: right ? 'start' : 'end', halo: true }));
      });

      let h = t + plotH + 2;
      if (kept.length) {
        h += drawLegend(ctx, kept.map(g => ({ label: g, color: gColor(g), value: '(' + pts.filter(p => p.group === g).length + ')' }))
          .concat(foldedGroups ? [{ label: 'Other (' + foldedGroups + ' more groups)', color: '--soft' }] : []), h + 6) + 6;
      }
      return h;
    },
    table: () => ({
      summary: 'The ' + pts.length + ' point' + (pts.length === 1 ? '' : 's') + ' behind this scatter',
      cols: [
        { k: 'name', label: 'Point', align: 'txt' },
        { k: 'gx', label: opts.xLabel || 'X', align: 'num' },
        { k: 'gy', label: opts.yLabel || 'Y', align: 'num' }
      ].concat(kept.length ? [{ k: 'grp', label: 'Group', align: 'txt' }] : []),
      rows: pts.slice().sort((a, b) => Math.abs(b.y) - Math.abs(a.y)).map(p => ({
        name: p.label, gx: p.x, gx_t: fmt(p.x, xOpts), gy: p.y, gy_t: fmt(p.y, opts),
        grp: p.group, grp_c: p.group ? gColor(p.group) : null
      })),
      note: opts.tableNote
    })
  });
}

/* ══ 18. heatmap ═════════════════════════════════════════════════════════ */

function toNumOrNull(x) {
  if (x === null || x === undefined || x === '' || isNaN(x)) return null;
  return Number(x);
}

function normMatrix(matrix, opts) {
  opts = opts || {};
  if (!matrix) return { rows: [], cols: [], get: () => null };
  if (!Array.isArray(matrix) && matrix.values) {
    const rows = (matrix.rows || []).map(String), cols = (matrix.cols || []).map(String);
    return { rows: rows, cols: cols, get: (ri, ci) => (matrix.values[ri] ? toNumOrNull(matrix.values[ri][ci]) : null) };
  }
  const arr = (matrix || []).filter(Boolean);
  if (arr.length && arr[0].col !== undefined && arr[0].row !== undefined) {
    const rows = [], cols = [], map = {};
    for (const c of arr) {
      const r = String(c.row), k = String(c.col);
      if (rows.indexOf(r) < 0) rows.push(r);
      if (cols.indexOf(k) < 0) cols.push(k);
      map[r + '\u0000' + k] = toNumOrNull(c.value != null ? c.value : c.v);
    }
    return {
      rows: rows, cols: cols,
      get: (ri, ci) => { const x = map[rows[ri] + '\u0000' + cols[ci]]; return x === undefined ? null : x; }
    };
  }
  const rowKey = opts.rowKey || (arr[0] ? Object.keys(arr[0]).find(k => typeof arr[0][k] !== 'number') : null);
  const cols = opts.cols || (arr[0] ? Object.keys(arr[0]).filter(k => k !== rowKey && typeof arr[0][k] === 'number') : []);
  const rows = arr.map((r, i) => String(rowKey && r[rowKey] != null ? r[rowKey] : 'Row ' + (i + 1)));
  /* SAP bucket columns get their human label; anything else keeps its name. */
  return {
    rows: rows,
    cols: cols.map(c => BUCKET_LABEL[c] || String(c)),
    get: (ri, ci) => toNumOrNull(arr[ri] ? arr[ri][cols[ci]] : null)
  };
}

/**
 * Heatmap — magnitude as the depth of ONE hue, stepped from the card surface
 * up to `--c1`, so it reads the right way round in both themes. When the
 * values cross zero it switches to a diverging pair — `--c2` below zero,
 * `--c3` above, the bare surface as the neutral middle — because a one-hue
 * ramp cannot say which side of zero a cell is on.
 *
 * Every cell prints its value where the cell is big enough, always carries a
 * `<title>`, and a stepped scale legend sits under the grid. A cell that could
 * not be computed is drawn empty with a dot — never as a zero.
 *
 * @param {{rows:string[],cols:string[],values:number[][]}|Array} matrix also
 *   accepts `[{row,col,value}]`, or row objects plus `{rowKey, cols}`.
 * @param {Object} [opts] `cellH` (default 30), `rowKey`, `cols`.
 * @returns {Element}
 *
 * @example
 * card.appendChild(heatmap({
 *   rows: ['Delhi','Mumbai','Chennai'],
 *   cols: ['Apr','May','Jun'],
 *   values: [[1200000, 800000, 300000], [400000, 900000, 1100000], [0, 100000, 200000]]
 * }, {title:'Overdue by branch and month'}));
 */
export function heatmap(matrix, opts) {
  opts = opts || {};
  const m = normMatrix(matrix, opts);
  const cells = [];
  for (let ri = 0; ri < m.rows.length; ri++) {
    for (let ci = 0; ci < m.cols.length; ci++) {
      const val = m.get(ri, ci);
      if (val !== null) cells.push({ ri: ri, ci: ci, value: val });
    }
  }
  const vals = cells.map(c => c.value);
  const lo = vals.length ? Math.min.apply(null, vals) : 0;
  const hi = vals.length ? Math.max.apply(null, vals) : 0;
  const diverging = lo < 0 && hi > 0;
  const span = Math.max(Math.abs(lo), Math.abs(hi)) || 1;

  function tone(val) {
    if (diverging) return { token: val < 0 ? '--c2' : '--c3', t: Math.min(1, Math.abs(val) / span) };
    const range = (hi - lo) || 1;
    return { token: '--c1', t: Math.min(1, Math.max(0, (val - lo) / range)) };
  }

  return mount({
    kind: 'heatmap',
    opts: opts,
    aria: cells.length
      ? 'Heatmap, ' + m.rows.length + ' rows by ' + m.cols.length + ' columns, from ' + fmt(lo, opts) + ' to ' + fmt(hi, opts) + '.'
      : 'Heatmap with no cells.',
    draw: ctx => {
      if (!cells.length) return drawEmpty(ctx, opts.emptyMsg || 'No cells to colour - the matrix came back empty.');
      const t = ctx.top || 0, w = ctx.w;
      const cellH = opts.cellH || (w < 420 ? 26 : 30);
      const labW = Math.max(52, Math.min(w * 0.3, Math.max.apply(null, m.rows.map(r => tw(r, 11.5, 400))) + 8, 170));
      const gridW = Math.max(40, w - labW - 2);
      const cellW = gridW / Math.max(1, m.cols.length);
      const gridTop = t + 18;
      const everyOther = cellW < 30;

      m.cols.forEach((c, ci) => {
        if (everyOther && ci % 2) return;
        ctx.add(TXT(fit(c, cellW * (everyOther ? 1.9 : 1) - 4, 10.5, 500), labW + ci * cellW + cellW / 2, t + 11,
          { size: 10.5, color: '--soft', anchor: 'middle' }));
      });

      m.rows.forEach((rl, ri) => {
        const y = gridTop + ri * cellH;
        ctx.add(TXT(fit(rl, labW - 8, 11.5, 400), 0, y + cellH / 2 + 4, { size: 11.5, color: '--ink' }));
        m.cols.forEach((cl, ci) => {
          const val = m.get(ri, ci);
          const x = labW + ci * cellW;
          const rect = S('rect', {
            x: r2(x + 1), y: r2(y + 1),
            width: r2(Math.max(1, cellW - 2)), height: r2(Math.max(1, cellH - 2)),
            rx: 3, class: 'jc-mk'
          });
          if (val === null) {
            fill(rect, '--card-warm');
            stroke(rect, '--line-soft'); rect.style.strokeWidth = '1px';
            ctx.add(tip(rect, rl + ' / ' + cl + ': not computed'));
            ctx.add(TXT('·', x + cellW / 2, y + cellH / 2 + 4, { size: 12, color: '--soft', anchor: 'middle' }));
            return;
          }
          const s = tone(val);
          rect.style.fill = ramp(ctx.pal, s.token, 8 + 84 * s.t);
          const aria = rl + ' / ' + cl + ': ' + fmt(val, opts);
          tip(rect, aria);
          ctx.add(link(ctx, rect, { row: rl, col: cl, value: val }, ri * m.cols.length + ci, aria));

          const txt = fmt(val, opts);
          if (cellW >= tw(txt, 10, 600) + 8 && cellH >= 20) {
            const mixed = hexMix(ctx.pal[s.token], ctx.pal['--card'], (8 + 84 * s.t) / 100);
            ctx.add(TXT(txt, x + cellW / 2, y + cellH / 2 + 3.5,
              { size: 10, weight: 600, anchor: 'middle', color: inkOn(ctx.pal, mixed) }));
          }
        });
      });

      let h = gridTop + m.rows.length * cellH + 14;
      const steps = 6;
      const swW = Math.max(10, Math.min(24, (w - 150) / (diverging ? steps * 2 : steps)));
      let lx = 0;
      const strip = (token, from, to) => {
        for (let i = 0; i < steps; i++) {
          const tt = from + (to - from) * (i / (steps - 1));
          const sq = S('rect', { x: r2(lx), y: r2(h - 9), width: r2(swW), height: 9, rx: 2 });
          sq.style.fill = ramp(ctx.pal, token, 8 + 84 * tt);
          ctx.add(tip(sq, fmt(lo + (hi - lo) * tt, opts)));
          lx += swW + 1;
        }
      };
      ctx.add(TXT(fmt(lo, opts), 0, h - 13, { size: 10, color: '--soft' }));
      if (diverging) { strip('--c2', 1, 0); strip('--c3', 0, 1); } else { strip('--c1', 0, 1); }
      ctx.add(TXT(fmt(hi, opts), lx, h - 13, { size: 10, color: '--soft', anchor: 'end' }));
      h += 6;

      const notes = [];
      if (lo === hi) notes.push('Every cell holds the same value (' + fmt(lo, opts) + ') - there is no gradient to read.');
      if (diverging) notes.push('The values cross zero, so the scale runs from one hue below zero to another above it; the palest cells are nearest zero.');
      const blanks = m.rows.length * m.cols.length - cells.length;
      if (blanks > 0) notes.push(blanks + ' cell' + (blanks === 1 ? '' : 's') + ' could not be computed and are drawn empty, not as zero.');
      if (notes.length) {
        const lines = wrapText(notes.join(' '), w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, h + 8 + i * 14, { size: 11.5, color: '--soft' })));
        h += 8 + lines.length * 14;
      }
      return h;
    },
    table: () => ({
      summary: 'The grid behind this heatmap (' + m.rows.length + ' by ' + m.cols.length + ')',
      cols: [{ k: 'r', label: '', align: 'txt' }].concat(m.cols.map((c, i) => ({ k: 'c' + i, label: c, align: 'num' }))),
      rows: m.rows.map((rl, ri) => {
        const o = { r: rl };
        m.cols.forEach((c, ci) => {
          const val = m.get(ri, ci);
          o['c' + ci] = val;
          o['c' + ci + '_t'] = val === null ? 'not computed' : fmt(val, opts);
        });
        return o;
      }),
      note: opts.tableNote
    })
  });
}

/* ══ 19. meter ═══════════════════════════════════════════════════════════ */

/**
 * Meter — one value against its maximum. The track is a pale step of the fill's
 * own hue (so the state reads across the whole bar), the value and the
 * denominator are printed above it, and the percentage sits at the right.
 *
 * `--ok/--warn/--bad` appear here and nowhere else in this module: a meter's
 * fill is a *state*, not a series. Give `warnAt`/`badAt` as fractions of `max`,
 * and `invert:true` when a HIGH reading is the bad one.
 *
 * @param {number} value
 * @param {number} max must be positive - a zero denominator renders the
 *   "not computed" state rather than a confident empty bar.
 * @param {Object} [opts] `label`, `maxLabel`, `warnAt`, `badAt`, `okAt`,
 *   `invert`, `tone` (token).
 * @returns {Element}
 *
 * @example
 * card.appendChild(meter(226800000, 3107100000, {
 *   title: 'Trade share of raw open A/P',
 *   label: 'owed to trade', maxLabel: 'raw open',
 *   warnAt: 0.5, badAt: 0.8, invert: true }));
 */
export function meter(value, max, opts) {
  opts = opts || {};
  const val = toNum(value), mx = toNum(max);
  const frac = mx > 0 ? val / mx : null;

  return mount({
    kind: 'meter',
    opts: opts,
    aria: mx > 0
      ? fmt(val, opts) + ' of ' + fmt(mx, opts) + ', ' + (100 * val / mx).toFixed(1) + ' per cent.'
      : 'Meter: not computed, the maximum is zero.',
    draw: ctx => {
      if (!(mx > 0)) {
        return drawEmpty(ctx, 'Not computed - the maximum is ' + (max === null || max === undefined ? 'missing' : fmt(mx, opts)) +
          ', so ' + fmt(val, opts) + ' cannot be shown as a share of it.');
      }
      const t = ctx.top || 0, w = ctx.w;
      const barH = 14;
      const over = frac > 1, under = val < 0;
      const shown = Math.max(0, Math.min(1, frac));

      let tone = opts.tone || '--c1';
      if (opts.badAt != null && (opts.invert ? frac >= opts.badAt : frac <= opts.badAt)) tone = '--bad';
      else if (opts.warnAt != null && (opts.invert ? frac >= opts.warnAt : frac <= opts.warnAt)) tone = '--warn';
      else if (opts.okAt != null && (opts.invert ? frac < opts.okAt : frac > opts.okAt)) tone = '--ok';

      const valTxt = fmt(val, opts);
      const pctTxt = (100 * frac).toFixed(Math.abs(frac) < 0.1 ? 2 : 1).replace('-', '\u2212') + '%';
      ctx.add(TXT(valTxt, 0, t + 15, { size: 17, weight: 700, color: '--brand-deep' }));
      const lead = tw(valTxt, 17, 700) + 7;
      const tail = (opts.label ? opts.label + ' ' : '') + 'of ' + fmt(mx, opts) + (opts.maxLabel ? ' ' + opts.maxLabel : '');
      ctx.add(TXT(fit(tail, Math.max(10, w - lead - tw(pctTxt, 12.5, 650) - 12), 11.5, 400), lead, t + 15,
        { size: 11.5, color: '--soft' }));
      ctx.add(TXT(pctTxt, w, t + 15, { size: 12.5, weight: 650, color: '--ink', anchor: 'end' }));

      const by = t + 25;
      const track = S('rect', { x: 0, y: r2(by), width: w, height: barH, rx: 7 });
      track.style.fill = ramp(ctx.pal, tone, 16);
      ctx.add(track);

      if (shown > 0) {
        const bw = Math.max(3, shown * w);
        const bar = S('path', { d: roundRect(0, by, bw, barH, 7, bw >= w - 0.5 ? 'all' : 'right'), class: 'jc-mk' });
        fill(bar, tone);
        const aria = valTxt + ' of ' + fmt(mx, opts) + ' (' + pctTxt + ')';
        tip(bar, aria);
        ctx.add(link(ctx, bar, { value: val, max: mx }, 0, aria));
      }

      [['warnAt', '--warn'], ['badAt', '--bad']].forEach(pair => {
        const f = opts[pair[0]];
        if (f == null || f <= 0 || f > 1) return;
        const x = f * w;
        const tick = S('line', { x1: r2(x), y1: r2(by - 3), x2: r2(x), y2: r2(by + barH + 3) });
        stroke(tick, pair[1]); tick.style.strokeWidth = '2px';
        ctx.add(tip(tick, (pair[0] === 'warnAt' ? 'Warning' : 'Alert') + ' threshold: ' + fmt(f * mx, opts)));
      });

      let h = by + barH + 6;
      const notes = [];
      if (over) notes.push('Over the maximum: ' + valTxt + ' against ' + fmt(mx, opts) + ' (' + pctTxt + ') - the bar is full, the number is not.');
      if (under) notes.push('The value is negative (' + valTxt + '), so the bar is empty; a meter cannot draw below zero.');
      if (notes.length) {
        const lines = wrapText(notes.join(' '), w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, h + 10 + i * 14, { size: 11.5, color: '--warn' })));
        h += 10 + lines.length * 14;
      }
      return h;
    },
    table: () => ({
      summary: 'The numbers behind this meter',
      cols: [{ k: 'what', label: 'Reading', align: 'txt' }, { k: 'val', label: 'Value', align: 'num' }],
      rows: [
        { what: opts.label || 'Value', val: val, val_t: fmt(val, opts) },
        { what: opts.maxLabel || 'Maximum', val: mx, val_t: fmt(mx, opts) },
        { what: 'Share', val: frac === null ? null : frac * 100, val_t: frac === null ? 'not computed' : (100 * frac).toFixed(2) + '%' }
      ].concat(opts.warnAt != null ? [{ what: 'Warning at', val: opts.warnAt * mx, val_t: fmt(opts.warnAt * mx, opts) }] : [])
        .concat(opts.badAt != null ? [{ what: 'Alert at', val: opts.badAt * mx, val_t: fmt(opts.badAt * mx, opts) }] : []),
      note: opts.tableNote
    })
  });
}

/* ══ 20. flow — Sankey-lite ══════════════════════════════════════════════ */

/**
 * Flow (Sankey-lite) — where a total goes, column by column. Ribbon thickness
 * is the value; a ribbon takes the colour of the node it leaves, and the six
 * biggest sources take `--c1..--c6` in fixed order with any others in `--soft`
 * as "Other sources (n)". Node labels carry their value, every ribbon has a
 * `<title>` with both ends and the amount, and a rail under the diagram prints
 * each stage's total with the drop-off from the stage before it — which is the
 * whole point of a PO -> GRPO -> A/P invoice -> payment chart.
 *
 * @param {Array<{id:string,label:string}>|string[]|null} nodes may be `null` -
 *   the nodes are then taken from the links.
 * @param {Array<{source:string,target:string,value:number}>} links `from`/`to`
 *   are accepted as aliases. Zero, negative and self-referential links are
 *   dropped from the picture and the count is stated.
 * @param {Object} [opts] `height`.
 * @returns {Element}
 *
 * @example
 * card.appendChild(flow(null, [
 *   {source:'Raw open A/P', target:'Credit applied', value: 2082000000},
 *   {source:'Raw open A/P', target:'Still open',     value: 1025100000},
 *   {source:'Still open',   target:'Branch',         value:  775800000},
 *   {source:'Still open',   target:'Intercompany',   value:   22500000},
 *   {source:'Still open',   target:'Trade',          value:  226800000}
 * ], {title:'Where the open A/P goes'}));
 */
export function flow(nodes, links, opts) {
  opts = opts || {};
  const L = (links || []).map(l => ({
    s: String(l.source != null ? l.source : l.from),
    t: String(l.target != null ? l.target : l.to),
    v: toNum(l.value != null ? l.value : l.v),
    src: l
  })).filter(l => l.s && l.t && l.s !== 'undefined' && l.t !== 'undefined' && l.v > 0 && l.s !== l.t);
  const dropped = (links || []).length - L.length;

  const N = {}, order = [];
  const touch = (id, label) => {
    if (!N[id]) { N[id] = { id: id, label: label || id, in: 0, out: 0, depth: 0 }; order.push(N[id]); }
    return N[id];
  };
  (nodes || []).forEach(n => {
    if (typeof n === 'string') touch(n, n);
    else if (n) touch(String(n.id != null ? n.id : n.label), String(n.label != null ? n.label : n.id));
  });
  L.forEach(l => { touch(l.s); touch(l.t); N[l.s].out += l.v; N[l.t].in += l.v; });
  for (let pass = 0; pass < Math.min(order.length + 1, 24); pass++) {
    let moved = false;
    L.forEach(l => { if (N[l.t].depth < N[l.s].depth + 1) { N[l.t].depth = N[l.s].depth + 1; moved = true; } });
    if (!moved) break;
  }
  order.forEach(n => { n.value = Math.max(n.in, n.out); });
  const sources = order.filter(n => n.out > 0).sort((a, b) => b.value - a.value).slice(0, 6).map(n => n.id);
  const colorOf = id => { const i = sources.indexOf(id); return i >= 0 ? CAT[i] : '--soft'; };
  const maxDepth = order.reduce((a, n) => Math.max(a, n.depth), 0);
  const cols = [];
  for (let d = 0; d <= maxDepth; d++) cols.push(order.filter(n => n.depth === d).sort((a, b) => b.value - a.value));
  const otherSources = order.filter(n => n.out > 0).length - sources.length;

  return mount({
    kind: 'flow',
    opts: opts,
    aria: L.length
      ? 'Flow diagram: ' + L.map(l => N[l.s].label + ' to ' + N[l.t].label + ' ' + fmt(l.v, opts)).join('; ') + '.'
      : 'Flow diagram with no links.',
    draw: ctx => {
      if (!L.length) {
        return drawEmpty(ctx, dropped
          ? 'Nothing to flow - all ' + dropped + ' links are zero, negative or point at themselves. They are in the table.'
          : 'Nothing to flow - no links were passed.');
      }
      const t = ctx.top || 0, w = ctx.w;
      const h = Math.round(opts.height || Math.max(190, Math.min(w * 0.55, 360)));
      const nodeW = 9, gap = 9;
      const fs = w < 420 ? 10.5 : 11.5;

      const firstLabels = cols[0].map(n => n.label);
      const lastLabels = (cols[cols.length - 1] || []).map(n => n.label);
      const multi = cols.length > 1;
      const padL = multi ? Math.min(w * 0.26, Math.max.apply(null, firstLabels.map(s => tw(s, fs, 600))) + 10) : 0;
      const padR = multi ? Math.min(w * 0.26, Math.max.apply(null, lastLabels.map(s => tw(s, fs, 600))) + 10) : 0;
      const innerW = Math.max(40, w - padL - padR);
      const colX = d => multi ? padL + (d / (cols.length - 1)) * (innerW - nodeW) : padL;

      const colTotals = cols.map(c => c.reduce((a, n) => a + n.value, 0));
      const colMax = Math.max.apply(null, colTotals);
      const tallest = Math.max.apply(null, cols.map(c => c.length));
      const footH = multi ? 30 : 0;
      const usable = Math.max(30, h - (tallest - 1) * gap - 28 - footH);
      const scale = colMax > 0 ? Math.max(0.0001, usable / colMax) : 0;

      cols.forEach(col => {
        let y = t + 20;
        col.forEach(n => {
          n.h = Math.max(3, n.value * scale);
          n.x = colX(n.depth); n.y = y; n.outY = y; n.inY = y;
          y += n.h + gap;
        });
      });

      L.slice().sort((a, b) => b.v - a.v).forEach((l, i) => {
        const s = N[l.s], tg = N[l.t];
        const th = Math.max(1.5, l.v * scale);
        const sy = s.outY, ty = tg.inY;
        s.outY += th; tg.inY += th;
        const x1 = s.x + nodeW, x2 = Math.max(tg.x, x1 + 6), mid = (x1 + x2) / 2;
        const d = 'M' + r2(x1) + ',' + r2(sy) +
          'C' + r2(mid) + ',' + r2(sy) + ' ' + r2(mid) + ',' + r2(ty) + ' ' + r2(x2) + ',' + r2(ty) +
          'L' + r2(x2) + ',' + r2(ty + th) +
          'C' + r2(mid) + ',' + r2(ty + th) + ' ' + r2(mid) + ',' + r2(sy + th) + ' ' + r2(x1) + ',' + r2(sy + th) + 'Z';
        const rib = S('path', { d: d, class: 'jc-mk' });
        fill(rib, colorOf(s.id)); rib.style.fillOpacity = '.34';
        const aria = s.label + ' to ' + tg.label + ': ' + fmt(l.v, opts);
        tip(rib, aria);
        ctx.add(link(ctx, rib, l.src, i, aria));
      });

      order.forEach((n, i) => {
        const rect = S('rect', { x: r2(n.x), y: r2(n.y), width: nodeW, height: r2(n.h), rx: 3, class: 'jc-mk' });
        fill(rect, n.out > 0 ? colorOf(n.id) : '--sage');
        const aria = n.label + ': ' + fmt(n.value, opts) + (n.in && n.out ? ' through' : n.in ? ' received' : ' sent');
        tip(rect, aria);
        ctx.add(link(ctx, rect, n, i, aria));

        const valTxt = fmt(n.value, opts);
        const cy = n.y + n.h / 2;
        if (n.depth === 0 && multi && padL > 12) {
          ctx.add(TXT(fit(n.label, padL - 8, fs, 600), padL - 8, cy - 1, { size: fs, weight: 600, color: '--ink', anchor: 'end', halo: true }));
          ctx.add(TXT(valTxt, padL - 8, cy + 11, { size: 10.5, color: '--sage', anchor: 'end', halo: true }));
        } else if (n.depth === maxDepth && multi && padR > 12) {
          ctx.add(TXT(fit(n.label, padR - 8, fs, 600), n.x + nodeW + 8, cy - 1, { size: fs, weight: 600, color: '--ink', halo: true }));
          ctx.add(TXT(valTxt, n.x + nodeW + 8, cy + 11, { size: 10.5, color: '--sage', halo: true }));
        } else {
          const room = Math.min(190, (innerW / Math.max(1, cols.length - 1)) + 60);
          ctx.add(TXT(fit(n.label + '  ' + valTxt, room, 10.5, 600), n.x + nodeW / 2, Math.max(t + 9, n.y - 5),
            { size: 10.5, weight: 600, color: '--ink', anchor: 'middle', halo: true }));
        }
      });

      // stage rail: what each column carries, and what it lost since the one before
      if (multi) {
        const fy = t + h - 16;
        cols.forEach((col, d) => {
          if (!col.length) return;
          const last = d === cols.length - 1;
          const anchor = d === 0 ? 'start' : (last ? 'end' : 'middle');
          const ax = d === 0 ? 0 : (last ? w : colX(d) + nodeW / 2);
          ctx.add(TXT(fmt(colTotals[d], opts), ax, fy,
            { size: 11, weight: 650, color: '--sage', anchor: anchor, halo: true }));
          let sub = 'starts here';
          let col2 = '--soft';
          if (d > 0) {
            const delta = colTotals[d] - colTotals[d - 1];
            const pctStr = colTotals[d - 1] ? ' (' + (100 * delta / colTotals[d - 1]).toFixed(1).replace('-', '−') + '%)' : '';
            sub = delta === 0 ? 'no drop-off'
              : (delta < 0 ? '−' : '+') + fmt(Math.abs(delta), opts) + pctStr;
            col2 = delta < 0 ? '--warn' : '--soft';
          }
          ctx.add(TXT(fit(sub, Math.max(70, innerW / cols.length + 40), 10.5, 500), ax, fy + 13,
            { size: 10.5, color: col2, anchor: anchor, halo: true }));
        });
      }

      let hh = t + h + 2;
      if (otherSources > 0) {
        hh += drawLegend(ctx, sources.map(id => ({ label: N[id].label, color: colorOf(id) }))
          .concat([{ label: 'Other sources (' + otherSources + ' more)', color: '--soft' }]), hh + 4) + 4;
      }
      if (dropped > 0) {
        const msg = dropped + ' link' + (dropped === 1 ? '' : 's') + ' could not be drawn (zero, negative or self-referential); they are in the table.';
        const lines = wrapText(msg, w, 11.5);
        lines.forEach((ln, i) => ctx.add(TXT(ln, 0, hh + 10 + i * 14, { size: 11.5, color: '--soft' })));
        hh += 10 + lines.length * 14;
      }
      return hh;
    },
    table: () => ({
      summary: 'The ' + L.length + ' link' + (L.length === 1 ? '' : 's') + ' behind this flow',
      cols: [
        { k: 'from', label: 'From', align: 'txt' },
        { k: 'to', label: 'To', align: 'txt' },
        { k: 'val', label: 'Value', align: 'num' }
      ],
      rows: L.slice().sort((a, b) => b.v - a.v).map(l => ({
        from: N[l.s].label, from_c: colorOf(l.s), to: N[l.t].label, val: l.v, val_t: fmt(l.v, opts)
      })),
      note: opts.tableNote
    })
  });
}
