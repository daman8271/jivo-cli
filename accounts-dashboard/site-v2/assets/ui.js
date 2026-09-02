/**
 * @file assets/ui.js - the rendering half of the v2 build contract (CONTRACT.md
 * section 3). Every page imports these through `core.js`, which re-exports this
 * module on its last line.
 *
 * House rules this file enforces so that no page has to remember them:
 *
 *  - **Never a confident zero.** A KPI whose value is null renders NOTHING AT
 *    ALL - no card, no dash, no zero. A table with no rows renders `empty()`
 *    with a reason. Nil and unknown must never look alike.
 *  - **Every number is a link.** Any item carrying a derivation id gets its
 *    label linked to `derivation.html?k=<id>&co=<company>` and a check dot.
 *  - **A red dot never hides the number.** `checkDot()` sits *beside* the
 *    figure. A failed cross-check is a warning, not a censor.
 *  - **No horizontal overflow.** Wide tables scroll inside their own container.
 *  - **Escape first, format second.** `note()` escapes the whole markdown source
 *    before a single formatting rule runs; raw input never reaches innerHTML.
 *
 * Dependencies: none. Formatting, data and linking helpers come from `core.js`,
 * imported as a namespace so that a helper this file does not need - or one that
 * `core.js` has not shipped yet - can never break module linking. `core.js`
 * re-exports this module, so this file must never import from `ui.js`.
 *
 * @module ui
 */

import * as core from './core.js';

/* == constants =========================================================== */

/** Company names used until `manifest()` resolves and supplies the real ones. */
const COMPANY_FALLBACK = {
  oil: 'JIVO Wellness (Oil)',
  mart: 'JIVO Mart',
  bev: 'JIVO Beverages'
};

/** Fallback company roster. @type {Array<{key:string,lg:string,sm:string,full:string}>} */
const COMPANIES = ['oil', 'mart', 'bev'].map(function (k) {
  return companyLabels(k, COMPANY_FALLBACK[k]);
});

/** Section order in the nav. Anything the manifest reports that is not here is appended. */
const SECTION_ORDER = [
  'customer-ageing', 'vendor-ageing', 'open-item-list', 'grpo', 'goods-return',
  'return-note', 'provisions', 'cash-sale', 'bank-accounts', 'bank-reco',
  'transporter', 'budget-heads', 'factory-indirect'
];

/** Human nav labels. A section id with no entry falls back to its id. */
const SECTION_LABEL = {
  'customer-ageing': 'Receivables',
  'vendor-ageing': 'Payables',
  'open-item-list': 'Open items',
  'grpo': 'GRPO',
  'goods-return': 'Goods return',
  'return-note': 'Return note',
  'provisions': 'Provisions',
  'cash-sale': 'Cash sale',
  'bank-accounts': 'Banks',
  'bank-reco': 'Bank reco',
  'transporter': 'Transporter',
  'budget-heads': 'Budget heads',
  'factory-indirect': 'Factory indirect'
};

/**
 * Section id -> page file. Only used when `core.hrefSection()` is unavailable;
 * core owns the real mapping. `budget-heads` and `factory-indirect` have no page
 * of their own in CONTRACT section 1, so - exactly as core does - they fall back
 * to their anchor on the board, which never 404s.
 */
const SECTION_PAGE = {
  'customer-ageing': 'receivables.html',
  'vendor-ageing': 'payables.html',
  'open-item-list': 'open-items.html',
  'grpo': 'grpo.html',
  'goods-return': 'goods-return.html',
  'return-note': 'return-note.html',
  'provisions': 'provisions.html',
  'cash-sale': 'cash-sale.html',
  'bank-accounts': 'banks.html',
  'bank-reco': 'bank-reco.html',
  'transporter': 'transporter.html'
};

/** The three pages that are not sections but always sit in the nav. */
const TAIL_NAV = [
  { id: 'methodology', label: 'Methodology', page: 'methodology.html' },
  { id: 'health',      label: 'Health',      page: 'health.html' },
  { id: 'search',      label: 'Search',      page: 'search.html' }
];

/** id -> label for the tail pages, for the masthead context line. */
const TAIL_LABEL = {};
TAIL_NAV.forEach(function (t) { TAIL_LABEL[t.id] = t.label; });

/** Client-side paging kicks in above this many rows. */
const PAGE_AT = 200;

/* Glyphs kept as escapes so the file stays 7-bit clean end to end. */
const GLYPH_SUN  = '☀';   // sun
const GLYPH_MOON = '☽';   // moon
const TIMES      = '×';   // multiplication sign, the filter's clear button
const DASH       = '—';   // em dash
const MINUS      = '−';   // true minus
const RUPEE      = '₹';
const ELLIPSIS   = '…';
const ARROWS     = '▲▼';
const ENDASH     = '–';

/* == tiny DOM + string idioms (kept identical to v1's) =================== */

/**
 * v1's escaper, plus the apostrophe. Used only when `core.esc` is unavailable,
 * so that escaping - the one security-critical primitive here - can never be
 * undefined because of module load order.
 * @param {*} s
 * @returns {string}
 */
function escFallback(s) {
  return String(s === null || s === undefined ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/** @param {*} s @returns {string} HTML-escaped text. */
function esc(s) {
  return typeof core.esc === 'function' ? String(core.esc(s)) : escFallback(s);
}

/**
 * v1's `el()`: build one element from an HTML string.
 * @param {string} html
 * @returns {HTMLElement}
 */
function el(html) {
  const d = document.createElement('div');
  d.innerHTML = String(html).trim();
  return /** @type {HTMLElement} */ (d.firstElementChild || document.createElement('span'));
}

/** @param {*} v @returns {boolean} true for null / undefined / '' / NaN. */
function isNil(v) {
  return v === null || v === undefined || v === '' ||
         (typeof v === 'number' && !isFinite(v));
}

/** Indian digit grouping: 12345678 -> "1,23,45,678". @param {number|string} s @returns {string} */
function inGroup(s) {
  s = String(s);
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  let rest = s.slice(0, -3), out = '';
  while (rest.length > 2) { out = ',' + rest.slice(-2) + out; rest = rest.slice(0, -2); }
  return (rest ? rest + out : out.replace(/^,/, '')) + ',' + last3;
}

/* -- core proxies. core.js owns these; each falls back so a page still
      renders if core has not shipped one of them yet. -------------------- */

/** @param {number} n @param {{exact?:boolean}} [opts] @returns {string} */
function money(n, opts) {
  if (typeof core.money === 'function') {
    const out = core.money(n, opts);
    if (out !== null && out !== undefined) return String(out);
  }
  if (isNil(n) || isNaN(Number(n))) return DASH;
  n = Number(n);
  const sign = n < 0 ? MINUS : '', a = Math.abs(n);
  if (!(opts && opts.exact)) {
    if (a >= 1e7) return sign + RUPEE + (a / 1e7).toFixed(2) + ' Cr';
    if (a >= 1e5) return sign + RUPEE + (a / 1e5).toFixed(2) + ' L';
  }
  return sign + RUPEE + inGroup(Math.round(a));
}

/** @param {number} n @returns {string} Indian-grouped integer. */
function num(n) {
  if (typeof core.num === 'function') {
    const out = core.num(n);
    if (out !== null && out !== undefined) return String(out);
  }
  if (isNil(n) || isNaN(Number(n))) return DASH;
  const v = Number(n), sign = v < 0 ? MINUS : '';
  return sign + inGroup(Math.round(Math.abs(v)));
}

/**
 * Lift a stored value to rupees using the column-name suffix (CONTRACT section 4).
 * @param {number} v @param {string} col @returns {number}
 */
function scale(v, col) {
  if (typeof core.scale === 'function') {
    const out = core.scale(v, col);
    if (typeof out === 'number' && isFinite(out)) return out;
  }
  if (isNil(v) || isNaN(Number(v))) return NaN;
  if (/_CR$/i.test(col)) return Number(v) * 1e7;
  if (/_L$/i.test(col)) return Number(v) * 1e5;
  return Number(v);
}

/** @param {string} iso @returns {string} e.g. "6 min ago" */
function ago(iso) {
  if (typeof core.ago === 'function') {
    const out = core.ago(iso);
    if (out) return String(out);
  }
  const d = new Date(iso);
  if (isNaN(d.getTime())) return 'unknown';
  const s = Math.max(0, (Date.now() - d.getTime()) / 1000);
  if (s < 90) return 'just now';
  if (s < 5400) return Math.round(s / 60) + ' min ago';
  if (s < 172800) return Math.round(s / 3600) + ' h ago';
  return Math.round(s / 86400) + ' d ago';
}

/** Current company key. @returns {string} */
function co() {
  if (typeof core.company === 'function') {
    const c = core.company();
    if (c) return String(c);
  }
  try {
    const q = new URLSearchParams(location.search).get('co');
    if (q) return q;
  } catch (e) { /* no search string */ }
  try {
    const s = localStorage.getItem('jivo-company') || localStorage.getItem('jivo-co');
    if (s) return s;
  } catch (e) { /* private window throws */ }
  return 'oil';
}

/** @param {string} kpiId @param {string} [c] @returns {string} */
function hrefDerivation(kpiId, c) {
  c = c || co();
  if (typeof core.hrefDerivation === 'function') return core.hrefDerivation(kpiId, c);
  return 'derivation.html?k=' + encodeURIComponent(kpiId) + '&co=' + encodeURIComponent(c);
}

/** @param {string} card @param {string} [c] @returns {string} */
function hrefParty(card, c) {
  c = c || co();
  if (typeof core.hrefParty === 'function') return core.hrefParty(card, c);
  return 'party.html?card=' + encodeURIComponent(card) + '&co=' + encodeURIComponent(c);
}

/** @param {string|number} objType @param {string|number} docEntry @param {string} [c] @returns {string} */
function hrefDocument(objType, docEntry, c) {
  c = c || co();
  if (typeof core.hrefDocument === 'function') return core.hrefDocument(objType, docEntry, c);
  return 'document.html?ot=' + encodeURIComponent(objType) +
         '&de=' + encodeURIComponent(docEntry) + '&co=' + encodeURIComponent(c);
}

/** @param {string} acct @param {string} [c] @returns {string} */
function hrefBank(acct, c) {
  c = c || co();
  if (typeof core.hrefBank === 'function') return core.hrefBank(acct, c);
  return 'bank-account.html?acct=' + encodeURIComponent(acct) + '&co=' + encodeURIComponent(c);
}

/** @param {string} acct @param {string} [c] @returns {string} */
function hrefGL(acct, c) {
  c = c || co();
  if (typeof core.hrefGL === 'function') return core.hrefGL(acct, c);
  return 'gl-account.html?acct=' + encodeURIComponent(acct) + '&co=' + encodeURIComponent(c);
}

/** @param {string} sectionId @param {string} [c] @param {Object} [params] @returns {string} */
function hrefSection(sectionId, c, params) {
  c = c || co();
  if (typeof core.hrefSection === 'function') return core.hrefSection(sectionId, c, params);
  const q = new URLSearchParams();
  q.set('co', c);
  if (params) {
    for (const k in params) {
      if (params[k] !== undefined && params[k] !== null) q.set(k, params[k]);
    }
  }
  const page = SECTION_PAGE[sectionId];
  return page ? page + '?' + q.toString()
              : 'index.html?' + q.toString() + '#' + encodeURIComponent(sectionId);
}

/* == column heuristics (v1's, extended) ================================== */

/** Identifiers are numerals, not quantities - print them exactly as stored. */
function isIdCol(c) {
  return /(_code|_num|_no|_entry|_id|_ref|_key|_type|_masked|_gstin|_pan)$/i.test(c) &&
         !/(_pct|_amt)$/i.test(c);
}

/** Which columns are money at all (three agents each picked their own suffix). */
function isMoneyCol(c) {
  return (/(_inr|_cr|_l|_amt|_gross|_net|_gst|_cost|amount|total|balance|_bal|value|payable|open|credit|debit|paid|advance|sum)$/i.test(c) ||
          /^(ub|unrec)_\d/i.test(c) || /^(b\d_|adj_)/i.test(c)) &&
         !/(_cnt|_docs|_count|_pct|_n|_lines|_rank|_days|_flag|_sign|_date|_state|_kind|_series)$/i.test(c) &&
         !/_docs_/i.test(c) && !isIdCol(c);
}

/**
 * Classify a column once, so the cell, the sort and the totals row all agree.
 * @param {string} c column key
 * @param {Array<Object>} rows sample rows
 * @param {Object<string,string>} [units] caller overrides, col -> kind
 * @returns {'INR'|'pct'|'days'|'count'|'date'|'code'|'text'}
 */
function colKind(c, rows, units) {
  const u = units && units[c];
  if (u) return u;
  if (/(_pct|_share|_ratio)$/i.test(c)) return 'pct';
  if (/_date$/i.test(c) || /^(date|doc_date|due_date)$/i.test(c)) return 'date';
  if (isIdCol(c)) return 'code';
  if (/(_days|_age|_ndigits)$/i.test(c) || /^(days|age_days)/i.test(c)) return 'days';
  if (isMoneyCol(c)) return 'INR';
  // fall back to the data: an all-numeric column is a count, anything else text
  let seen = 0, numeric = 0;
  for (let i = 0; i < rows.length && seen < 25; i++) {
    const v = rows[i][c];
    if (isNil(v)) continue;
    seen++;
    if (typeof v === 'number' || (typeof v === 'string' && !isNaN(Number(v)))) numeric++;
  }
  if (seen && numeric === seen) return 'count';
  return 'text';
}

/** The kinds that are right-aligned numerals. @param {string} k @returns {boolean} */
function isNumericKind(k) {
  return k === 'INR' || k === 'count' || k === 'days' || k === 'pct';
}

/**
 * Format one cell value, honouring the column unit.
 * @param {*} v @param {string} col @param {string} kind
 * @returns {string} HTML-safe text (no markup)
 */
function fmtCell(v, col, kind) {
  if (isNil(v)) return DASH;
  const n = Number(v);
  switch (kind) {
    case 'INR': return esc(money(scale(n, col)));
    case 'pct': return isNaN(n) ? esc(v) : esc(n.toFixed(2) + '%');
    case 'days': return isNaN(n) ? esc(v) : esc(num(n));
    case 'count': return isNaN(n) ? esc(v) : esc(num(n));
    default: return esc(v);
  }
}

/**
 * Format a bare KPI value by its declared unit.
 * @param {number} v @param {string} [unit] 'INR' | 'pct' | 'count' | 'days'
 * @returns {string}
 */
function fmtByUnit(v, unit) {
  if (isNil(v)) return DASH;
  const n = Number(v);
  if (isNaN(n)) return String(v);
  switch (unit) {
    case 'INR': return money(n);
    case 'pct': return n.toFixed(2) + '%';
    case 'days': return num(n) + (Math.abs(n) === 1 ? ' day' : ' days');
    case 'count': return num(n);
    default: return money(n);
  }
}

/* == shell =============================================================== */

let _refreshWired = false;   // core.onRefresh has no unsubscribe - subscribe once
let _stampTimer = null;      // "updated N min ago" must tick without a rebuild
let _shellOpts = {};
let _lastManifest = null;

/**
 * The spine. Renders the masthead (brandmark "JIVO Accounts", the company
 * segmented control, the theme toggle, the "updated N min ago" stamp with its
 * live dot), the always-on freshness bar - quiet when the build is current,
 * red and naming the reason when it is not - and the section nav. Identical on
 * every page, by design.
 *
 * Called synchronously at page boot: the frame paints immediately and the
 * manifest-driven parts (real company labels, the section list, the stamp, the
 * banner) fill in when `core.manifest()` resolves.
 *
 * @param {Object} o
 * @param {string} [o.title] page title, e.g. "Payables". Also sets document.title.
 * @param {string} [o.subtitle] one line under the title.
 * @param {string} [o.section] current section id, or a tail-nav key
 *   ('methodology' | 'health' | 'search' | 'index') - marked with aria-current.
 * @returns {HTMLElement} the shell host element.
 */
export function shell(o) {
  o = _shellOpts = o || {};
  let host = document.getElementById('shell');
  if (!host) {
    host = document.createElement('div');
    host.id = 'shell';
    document.body.insertBefore(host, document.body.firstChild);
  }

  if (o.title) document.title = String(o.title) + ' · JIVO Accounts';

  const cur = co();
  host.innerHTML =
    '<div class="wrap">' +
      '<header class="mast">' +
        '<div class="mast-top">' +
          '<a class="brandmark" href="index.html?co=' + esc(cur) + '">JIVO <span>Accounts</span></a>' +
          '<div class="stamp" id="stamp"></div>' +
        '</div>' +
        '<div class="pagehead">' +
          '<div class="ctx" id="pageCtx"></div>' +
          (o.title ? '<h1>' + esc(o.title) + '</h1>' : '') +
          (o.subtitle ? '<p class="lede">' + esc(o.subtitle) + '</p>' : '') +
        '</div>' +
        '<div class="ctrls">' +
          '<div class="seg" id="companySwitch" role="group" aria-label="Company"></div>' +
          '<span class="spacer"></span>' +
          '<button class="themetog" id="themeToggle" type="button">' +
            '<span class="ic" aria-hidden="true">' + GLYPH_SUN + '</span>' +
            '<span class="tl">Light</span>' +
          '</button>' +
        '</div>' +
        // board.css section 5: this bar ALWAYS renders, quiet when healthy and
        // loud when not, so nobody learns to ignore it.
        '<div class="freshbar" id="freshBanner" role="status"></div>' +
      '</header>' +
    '</div>' +
    '<nav class="navbar" aria-label="Sections"><div class="wrap">' +
      '<div class="navrow" id="navrow"></div>' +
    '</div></nav>';

  paintCompanies(COMPANIES);
  paintNav(SECTION_ORDER, o.section);
  paintCtx(null);
  wireTheme();
  paintStamp(null);
  paintFreshness(null);

  if (_stampTimer) clearInterval(_stampTimer);
  _stampTimer = setInterval(function () { paintStamp(_lastManifest); }, 30000);

  hydrate();
  if (!_refreshWired && typeof core.onRefresh === 'function') {
    _refreshWired = true;
    try {
      core.onRefresh(function () {
        // a new build means new cross-checks: drop the cached derivations so a
        // dot cannot keep showing the previous build's verdict.
        for (const key in _derivCache) delete _derivCache[key];
        hydrate();
      });
    } catch (e) { /* core not ready to take subscribers */ }
  }
  return host;
}

/** Fill the shell from the manifest once it lands. @returns {Promise<void>} */
async function hydrate() {
  let m = null;
  try {
    m = typeof core.manifest === 'function' ? await core.manifest() : null;
  } catch (e) { m = null; }
  _lastManifest = m;

  if (m && Array.isArray(m.companies) && m.companies.length) {
    paintCompanies(m.companies.map(function (c) {
      return companyLabels(c.key, c.label);
    }));
  }
  if (m && m.sections) {
    const known = SECTION_ORDER.filter(function (id) { return id in m.sections; });
    const extra = Object.keys(m.sections).filter(function (id) {
      return SECTION_ORDER.indexOf(id) < 0;
    }).sort();
    paintNav(known.concat(extra), _shellOpts.section, m.sections);
  }
  paintCtx(m);
  paintStamp(m);
  paintFreshness(m);
}

/**
 * Split a company label into the long and short forms board.css switches
 * between (`.seg .lg` / `.seg .sm`): "JIVO Wellness (Oil)" -> "Wellness (Oil)"
 * on a desktop, "Oil" on a phone.
 * @param {string} key @param {string} [label]
 * @returns {{key:string, lg:string, sm:string, full:string}}
 */
function companyLabels(key, label) {
  const full = String(label || key || '');
  const paren = full.match(/\(([^)]+)\)/);
  const lg = full.replace(/^JIVO\s*/i, '') || key;
  const sm = paren ? paren[1] : (lg.split(/\s+/)[0] || key);
  return { key: key, lg: lg, sm: sm, full: full || key };
}

/**
 * The masthead context line: which book, and which section of it. board.css
 * puts it above the page title (`.pagehead .ctx`).
 * @param {Object} m manifest, or null before it loads
 */
function paintCtx(m) {
  const host = document.getElementById('pageCtx');
  if (!host) return;
  const c = co();
  const rec = (m && Array.isArray(m.companies))
    ? m.companies.filter(function (x) { return x && x.key === c; })[0] : null;
  const coName = rec ? companyLabels(rec.key, rec.label).lg
                     : companyLabels(c, COMPANY_FALLBACK[c] || c).lg;
  const sec = _shellOpts.section;
  const secName = sec ? (SECTION_LABEL[sec] || TAIL_LABEL[sec] || String(sec).replace(/-/g, ' ')) : null;
  host.innerHTML = esc(coName) +
    (secName ? '<span class="sep" aria-hidden="true">·</span>' + esc(secName) : '');
}

/**
 * The segmented company control. Each button carries both label lengths -
 * board.css shows `.lg` from 820px and `.sm` below it, so "Beverages" never
 * squeezes "Oil" off a phone.
 * @param {Array<{key:string,lg:string,sm:string,full:string}>} list
 */
function paintCompanies(list) {
  const host = document.getElementById('companySwitch');
  if (!host) return;
  const cur = co();
  host.innerHTML = list.map(function (c) {
    return '<button type="button" data-k="' + esc(c.key) + '" aria-pressed="' +
           (c.key === cur) + '" title="' + esc(c.full || c.lg) + '">' +
           '<span class="lg">' + esc(c.lg) + '</span>' +
           '<span class="sm">' + esc(c.sm) + '</span></button>';
  }).join('');
  host.querySelectorAll('button').forEach(function (b) {
    b.addEventListener('click', function () {
      const k = b.dataset.k;
      if (k === co()) return;
      if (typeof core.setCompany === 'function') { core.setCompany(k); return; }
      try { localStorage.setItem('jivo-company', k); } catch (e) { /* private window */ }
      const u = new URL(location.href);
      u.searchParams.set('co', k);
      location.href = u.toString();
    });
  });
}

/**
 * @param {string[]} ids section ids in nav order
 * @param {string} [current] section id or tail-nav key to mark
 * @param {Object} [sections] manifest.sections, for the failed-section marker
 */
function paintNav(ids, current, sections) {
  const host = document.getElementById('navrow');
  if (!host) return;
  const c = co();
  const here = String(current || '');
  const page = (location.pathname.split('/').pop() || 'index.html');
  const homeHere = (here === 'index' || here === 'overview' ||
                    (!here && /^(index\.html)?$/.test(page)));

  const home = '<a href="index.html?co=' + encodeURIComponent(c) + '"' +
    (homeHere ? ' aria-current="page" class="is-here"' : '') + '>Overview</a>';

  const secs = ids.map(function (id) {
    const st = sections && sections[id] ? sections[id].status : null;
    const mark = st === 'error' ? ' !' : '';
    const cls = (id === here) ? ' aria-current="page" class="is-here"' : '';
    const title = (st && st !== 'ok') ? ' title="' + esc('section status: ' + st) + '"' : '';
    return '<a href="' + esc(hrefSection(id, c)) + '"' + cls + title + '>' +
           esc(SECTION_LABEL[id] || id.replace(/-/g, ' ')) + mark + '</a>';
  }).join('');

  const tail = TAIL_NAV.map(function (t) {
    const on = (t.id === here || page === t.page);
    return '<a href="' + esc(t.page + '?co=' + encodeURIComponent(c)) + '"' +
           (on ? ' aria-current="page" class="is-here"' : '') + '>' + esc(t.label) + '</a>';
  }).join('');

  host.innerHTML = home + secs + tail;
}

/** @param {Object} m manifest (null before it loads) */
function paintStamp(m) {
  const host = document.getElementById('stamp');
  if (!host) return;
  if (!m) {
    host.innerHTML = '<span class="live"><i></i>loading SAP data' + ELLIPSIS + '</span>';
    return;
  }
  host.innerHTML =
    'Position as at <b>' + esc(m.as_of || 'unknown') + '</b><br>' +
    '<span class="live" title="' + esc(String(m.generated_at || '')) + '"><i></i>updated ' +
      esc(m.generated_at ? ago(m.generated_at) : 'unknown') + '</span><br>' +
    '<span style="color:var(--soft)">read-only from SAP HANA</span>';
}

/**
 * The freshness bar (board.css section 5). It renders on every page in every
 * state - quiet when the build is current, loud and red when it is not - so
 * that nobody learns to ignore it. When stale it NAMES the reason: v1 froze
 * for five hours and went on serving 13:42 numbers as if they were live.
 *
 * It never hides the figures. The operator still needs them; the bar only
 * stops them being read as live.
 *
 * @param {Object} m manifest, or null before it loads
 */
function paintFreshness(m) {
  const host = document.getElementById('freshBanner');
  if (!host) return;

  // pass the manifest we just read, so the bar and the stamp can never
  // disagree about which build they are describing
  let s = null;
  try { if (typeof core.isStale === 'function') s = core.isStale(m || undefined); }
  catch (e) { s = null; }
  if (s === true) s = { stale: true };
  else if (s === false) s = { stale: false };
  if (!s || typeof s !== 'object') {
    s = m ? { stale: !!m.stale, reason: m.stale_reason, unknown: false }
          : { stale: false, unknown: true };
  }

  const gen = s.generated_at || (m && m.generated_at) || null;
  const age = gen ? ago(gen) : null;
  const canRefresh = typeof core.refreshNow === 'function';
  const btnHtml = canRefresh
    ? '<span class="spacer"></span><button type="button" class="btn freshnow">Check now</button>'
    : '';

  if (!m) {
    host.className = 'freshbar is-building';
    host.innerHTML = '<b>Reading the build stamp' + ELLIPSIS + '</b> ' +
      'nothing on this page is confirmed current until data/manifest.json is read.';
    return;
  }

  if (!s.stale) {
    host.className = 'freshbar';
    host.innerHTML =
      '<b>Live from SAP HANA' + (age ? ' · built ' + esc(age) : '') + '.</b> ' +
      'Position as at ' + esc(m.as_of || 'unknown') + ', read-only.' + btnHtml;
  } else {
    const reason = s.reason || s.stale_reason || (m && m.stale_reason) ||
                   'the pipeline did not record a reason';
    host.className = 'freshbar is-stale';
    host.innerHTML =
      '<b>These figures are stale' + (age ? ' · last built ' + esc(age) : '') + '.</b> ' +
      esc(sentence(String(reason))) + ' ' +
      'Read every number on this page as of that build, not as of now.' + btnHtml;
  }

  const btn = host.querySelector('.freshnow');
  if (btn) {
    btn.addEventListener('click', function () {
      btn.disabled = true;
      btn.textContent = 'Checking' + ELLIPSIS;
      Promise.resolve(core.refreshNow()).then(function () {
        // the poll fires onRefresh only when the build actually MOVED, so
        // repaint from the manifest either way rather than leave a dead button
        hydrate();
      }, function () {
        btn.disabled = false;
        btn.textContent = 'Check failed - retry';
      });
    });
  }
}

/**
 * One reason, as one sentence: capitalised, single trailing stop. A reason
 * lifted from a pipeline field reads as a fragment otherwise.
 * @param {string} t @returns {string}
 */
function sentence(t) {
  const s = String(t || '').trim().replace(/\.\s*$/, '');
  if (!s) return '';
  return s.charAt(0).toUpperCase() + s.slice(1) + '.';
}

/** Theme toggle: flips data-theme, persists to localStorage inside try/catch. */
function wireTheme() {
  const root = document.documentElement;
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  function paint() {
    const dark = root.getAttribute('data-theme') !== 'light';
    const ic = btn.querySelector('.ic'), tl = btn.querySelector('.tl');
    if (ic) ic.textContent = dark ? GLYPH_SUN : GLYPH_MOON;
    if (tl) tl.textContent = dark ? 'Light' : 'Dark';
    btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    btn.title = btn.getAttribute('aria-label');
  }
  btn.addEventListener('click', function () {
    const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    // core.setTheme is the single source of truth when it exists: it sets the
    // attribute, persists the choice and fires 'jivo:theme' for the charts.
    if (typeof core.setTheme === 'function') {
      core.setTheme(next);
    } else {
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('jivo-theme', next); } catch (e) { /* private window */ }
      try {
        window.dispatchEvent(new CustomEvent('jivo:theme', { detail: { theme: next } }));
      } catch (e) { /* older browser */ }
    }
    paint();
  });
  paint();
}

/* == KPI row ============================================================= */

/**
 * @typedef {Object} KpiItem
 * @property {string} [id] derivation id. Links the label and adds a check dot.
 * @property {string} label
 * @property {string|number|null} value pre-formatted string, or a number
 *   formatted by `unit`. **null renders nothing at all** - no card, no zero.
 * @property {string} [unit] 'INR' | 'pct' | 'count' | 'days' (numbers only).
 * @property {string} [sub] one line under the figure.
 * @property {'ok'|'warn'|'bad'|'info'} [tone] colours the figure.
 * @property {number[]|SVGElement|string} [spark] trend. An array draws a micro
 *   sparkline here; pass a charts.js `<svg>` element for the full one.
 * @property {string|number} [corr] the figure SAP reports, struck through beside
 *   the true one. The correction IS the information.
 * @property {string} [href] overrides the derivation link.
 * @property {string} [title] tooltip on the card.
 */

/**
 * A row of headline figures.
 *
 * Carries v1's rule verbatim: an item whose value is null renders NOTHING -
 * never a confident zero, never a dash that reads like nil. An item with an
 * `id` gets its label linked to the derivation and a `checkDot()` appended, so
 * every headline number is one click from the SQL that made it.
 *
 * @param {KpiItem[]} items
 * @returns {HTMLElement} `<div class="kpis">` (empty if every item was null)
 */
export function kpiRow(items) {
  const c = co();
  const host = document.createElement('div');
  host.className = 'kpis';

  (items || []).forEach(function (it) {
    if (!it) return;
    const raw = it.value;
    // the rule: nothing computed -> nothing rendered.
    if (isNil(raw) || raw === DASH || raw === '-') return;
    const val = (typeof raw === 'number') ? fmtByUnit(raw, it.unit) : String(raw);
    if (!val || val === DASH) return;

    const card = el('<div class="kpi' + (it.tone ? ' is-' + esc(it.tone) : '') + '"' +
      (it.id ? ' data-k="' + esc(it.id) + '"' : '') +
      (it.title ? ' title="' + esc(it.title) + '"' : '') + '></div>');

    const href = it.href || (it.id ? hrefDerivation(it.id, c) : null);

    const lab = document.createElement('div');
    lab.className = 'lab';
    if (it.id) {
      const a = document.createElement('a');
      a.href = href;
      a.textContent = it.label == null ? it.id : String(it.label);
      a.title = 'How this number was derived';
      lab.appendChild(a);
      // .dotlink is pushed to the right edge of the label row by board.css
      lab.appendChild(checkDot(it.id, c));
    } else {
      lab.textContent = it.label == null ? '' : String(it.label);
    }
    card.appendChild(lab);

    // CONTRACT section 0.4: every rendered figure with a derivation id carries
    // data-k and links to its derivation.
    const v = document.createElement('div');
    v.className = 'val';
    if (href) {
      const va = document.createElement('a');
      va.href = href;
      va.setAttribute('data-k', it.id || '');
      va.textContent = val;
      v.appendChild(va);
    } else {
      v.textContent = val;
    }
    card.appendChild(v);

    // the struck-through figure lives in the subtitle, beside the true one
    const bits = [];
    if (!isNil(it.corr)) {
      const cs = typeof it.corr === 'number' ? fmtByUnit(it.corr, it.unit) : String(it.corr);
      bits.push('<s title="' + esc('what SAP reports, before JIVO’s corrections') + '">' +
                esc(cs) + '</s>');
      bits.push(esc(it.sub || 'as SAP reports it'));
    } else if (it.sub) {
      bits.push(esc(it.sub));
    }
    if (bits.length) card.appendChild(el('<div class="sub">' + bits.join(' ') + '</div>'));

    if (it.spark) {
      const sp = document.createElement('div');
      sp.className = 'spark';   // board.css sizes the slot and its <svg>
      if (typeof it.spark === 'string') sp.innerHTML = it.spark;
      else if (Array.isArray(it.spark)) sp.innerHTML = microSpark(it.spark);
      else if (it.spark && it.spark.nodeType === 1) sp.appendChild(it.spark);
      if (sp.firstChild) card.appendChild(sp);
    }

    host.appendChild(card);
  });

  return host;
}

/**
 * A dependency-free micro sparkline for a KPI card. charts.js owns the real
 * one; this exists so `kpiRow` never has to import another agent's module.
 * @param {number[]} values
 * @returns {string} SVG markup, or '' when there is not enough history
 */
function microSpark(values) {
  const v = (values || []).map(Number).filter(function (n) { return isFinite(n); });
  if (v.length < 2) return '';
  const w = 88, h = 22;
  const min = Math.min.apply(null, v), max = Math.max.apply(null, v);
  const span = (max - min) || 1;
  const y = function (n) { return (h - 2 - ((n - min) / span) * (h - 4)).toFixed(1); };
  const pts = v.map(function (n, i) {
    return (i * (w - 2) / (v.length - 1) + 1).toFixed(1) + ',' + y(n);
  }).join(' ');
  const first = v[0], last = v[v.length - 1];
  return '<svg viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" width="' + w +
         '" height="' + h + '" role="img" aria-label="' +
         esc((last >= first ? 'rising' : 'falling') + ' from ' + num(first) + ' to ' + num(last)) +
         '"><polyline fill="none" stroke="var(--brand)" stroke-width="1.5" ' +
         'stroke-linejoin="round" stroke-linecap="round" points="' + pts + '"></polyline>' +
         '<circle cx="' + (w - 1) + '" cy="' + y(last) + '" r="1.8" fill="var(--brand)"></circle></svg>';
}

/* == check dot =========================================================== */

/** @type {Object<string, Promise<Object>>} per-company derivation cache */
const _derivCache = {};

/**
 * The cross-check indicator: did a second, independent route reproduce this
 * figure? Reads `manifest.kpis[co][id].check` for the verdict; when the manifest
 * has no check it falls back to the derivation's `reproduces_spec_measurement`.
 * Either way the two figures named in the tooltip are this board's derived
 * `value` and the spec's own live measurement `spec_live[co]`, because the
 * manifest's check records only `{ok, delta_pct}`.
 *
 *   true -> `--ok` (green) - unknown/null -> `--warn` (amber) - false -> `--bad` (red)
 *
 * The `title` names BOTH routes and the delta between them. The dot is always a
 * sibling of the figure and never replaces it: **a red dot never hides the
 * number** - it says "two routes disagree, go and look", not "this is wrong".
 *
 * Returns synchronously (amber, "checking") and repaints itself when the
 * manifest and derivations land.
 *
 * @param {string} kpiId
 * @param {string} [c] company key; defaults to the current company
 * @returns {HTMLAnchorElement}
 */
export function checkDot(kpiId, c) {
  c = c || co();
  // board.css section 9 owns the shape: a 24px .dotlink hit target wrapping an
  // 8px .dot whose three states differ in FILL as well as hue, so they survive
  // greyscale and deuteranopia.
  const a = document.createElement('a');
  a.className = 'dotlink';
  a.href = hrefDerivation(kpiId, c);
  a.setAttribute('data-k', kpiId);
  a.title = 'Checking this figure against its second route' + ELLIPSIS;
  a.setAttribute('aria-label', a.title);
  a.innerHTML = '<span class="dot is-warn" aria-hidden="true"></span>';
  const dot = a.firstElementChild;

  resolveCheck(kpiId, c).then(function (r) {
    dot.className = 'dot is-' + r.state;
    a.title = r.title;
    a.setAttribute('aria-label', r.title);
  }, function () {
    a.title = 'The cross-check could not be loaded. The figure itself is unaffected.';
    a.setAttribute('aria-label', a.title);
  });

  return a;
}

/**
 * @param {string} kpiId @param {string} c
 * @returns {Promise<{state:'ok'|'warn'|'bad', title:string}>}
 */
async function resolveCheck(kpiId, c) {
  let m = null;
  try {
    m = typeof core.manifest === 'function' ? await core.manifest() : null;
  } catch (e) { m = null; }

  const k = (m && m.kpis && m.kpis[c]) ? m.kpis[c][kpiId] : null;
  const chk = (k && k.check && typeof k.check === 'object') ? k.check : null;

  let label = kpiField(k, 'label') || kpiId;
  let unit = kpiField(k, 'unit');
  let valA = kpiField(k, 'value');
  let valB = (chk && 'alt_value' in chk) ? chk.alt_value : null;
  let delta = (chk && chk.delta !== undefined && chk.delta !== null) ? chk.delta : null;
  let dpct = (chk && chk.delta_pct !== undefined) ? chk.delta_pct : null;
  let routeA = 'this board’s derivation';
  let routeB = (chk && chk.method) ? 'the ' + chk.method + ' re-derivation'
                                   : 'the spec’s own live measurement';
  // the manifest's check is the first authority on the verdict...
  let state = chk ? (chk.ok === true ? 'ok' : chk.ok === false ? 'bad' : 'warn') : null;

  // ...but it currently carries only {ok, delta_pct}, so the two figures the
  // title has to name come from the derivation record.
  if (state === null || isNil(valA) || isNil(valB)) {
    let ders = null;
    try {
      if (typeof core.derivations === 'function') {
        if (!_derivCache[c]) _derivCache[c] = core.derivations(c);
        ders = await _derivCache[c];
      }
    } catch (e) { ders = null; }

    const d = ders && ders[kpiId];
    if (!d && state === null) {
      return {
        state: 'warn',
        title: 'No derivation record for "' + kpiId + '", so this figure has no second ' +
               'route. It is shown exactly as the pipeline produced it.'
      };
    }
    if (d) {
      if (isNil(valA) && 'value' in d) valA = d.value;
      if (isNil(valB) && d.spec_live && (c in d.spec_live)) valB = d.spec_live[c];
      if (!unit) unit = d.unit;
      if (!label || label === kpiId) label = d.label || label;
      routeA = 'this board’s derivation (' + (d.method || 'pipeline') +
               (d.column ? ', column ' + d.column : '') + ')';
      if (state === null) {
        const rep = d.reproduces_spec_measurement;
        state = rep === true ? 'ok' : rep === false ? 'bad' : 'warn';
      }
    }
  }

  const comparable = !isNil(valA) && !isNil(valB) &&
                     !isNaN(Number(valA)) && !isNaN(Number(valB));
  if (delta === null && comparable) delta = Number(valA) - Number(valB);
  if ((dpct === null || dpct === undefined) && delta !== null && Number(valB)) {
    dpct = delta / Number(valB);
  }

  return {
    state: state || 'warn',
    title: checkTitle(label, routeA, valA, routeB, valB, delta, dpct, unit, state || 'warn')
  };
}

/**
 * Read a manifest KPI field under either key shape. The contract documents
 * `{value,label,unit,section}`; the live pipeline emits `{v,l,u,s}`. Both are
 * accepted so a pipeline change cannot silently blank every check dot.
 * @param {Object} k a manifest KPI entry
 * @param {'value'|'label'|'unit'|'section'} name
 * @returns {*}
 */
function kpiField(k, name) {
  if (!k) return undefined;
  if (k[name] !== undefined) return k[name];
  const short = { value: 'v', label: 'l', unit: 'u', section: 's' }[name];
  return short ? k[short] : undefined;
}

/**
 * Name both routes and the delta, in a sentence an accountant can act on.
 * @param {string} label @param {string} routeA @param {*} valA
 * @param {string} routeB @param {*} valB @param {?number} delta
 * @param {?number} dpct @param {string} [unit] @param {string} state
 * @returns {string}
 */
function checkTitle(label, routeA, valA, routeB, valB, delta, dpct, unit, state) {
  const f = function (v) { return isNil(v) ? 'not computed' : fmtByUnit(v, unit); };
  const head = state === 'ok'
    ? 'Cross-checked - both routes agree.'
    : state === 'bad'
      ? 'The two routes DISAGREE. The figure shown is this board’s derivation; open it and judge for yourself.'
      : 'Not cross-checked - no second route reproduced this figure.';
  const pctTxt = (dpct === null || dpct === undefined || isNaN(Number(dpct)))
    ? ''
    : ' (' + (Math.abs(Number(dpct)) * 100).toFixed(4) + '%)';
  const gap = (delta === null || delta === undefined)
    ? 'delta: not comparable'
    : 'delta ' + fmtByUnit(delta, unit) + pctTxt;
  return label + ' - ' + head + '\n' +
         routeA + ': ' + f(valA) + '\n' +
         routeB + ': ' + f(valB) + '\n' + gap;
}

/* == table =============================================================== */

/**
 * @typedef {Object} TableOpts
 * @property {string[]} [cols] columns to show, in order. Default: keys of row 0.
 * @property {Object<string,string>} [labels] col -> header text.
 * @property {Object<string,string>} [units] col -> 'INR'|'pct'|'days'|'count'|
 *   'code'|'date'|'text'. Overrides the suffix heuristic; use it when a column
 *   name lies about what it holds.
 * @property {Object<string,(string|Object|Function)>} [links] col -> 'party' |
 *   'document' | 'bank' | 'gl' | 'derivation' | 'section', or
 *   `{kind, card, objType, docEntry}` naming the row fields to read, or
 *   `(value, row, co) => href`.
 * @property {string|{col:string,dir:'asc'|'desc'}} [sort] initial sort
 *   ('-COL' means descending).
 * @property {boolean|string} [filter] text filter box (a string is its placeholder).
 * @property {string[]} [facets] columns to offer as facet chips.
 * @property {number|boolean} [page] rows per page; `false` disables paging.
 *   Default: paginate above 200 rows.
 * @property {boolean} [dense] tighter rows.
 * @property {boolean|string[]} [total] totals row; an array limits it to those columns.
 * @property {string} [co] company for links; defaults to the current one.
 * @property {string} [note] a line of prose under the table (a trap, a caveat).
 * @property {string|Object} [empty] what `empty()` should say when `rows` is empty.
 * @property {string} [caption] accessible table caption.
 */

/**
 * The workhorse table: numeric-aware sortable headers, a text filter, optional
 * facet chips, client-side paging above ~200 rows, a totals row that respects
 * each column's unit (values are lifted to rupees with `scale()` before they are
 * summed, so a `_L` column can never add 100,000x wrong), "copy as TSV", and
 * cells that link out to the party / document / bank / GL pages.
 *
 * Numerics are right-aligned, codes are monospace, negatives take `--bad`.
 * The table scrolls inside its own container - the page body never does.
 *
 * @param {Array<Object>} rows
 * @param {TableOpts} [opts]
 * @returns {HTMLElement} `<div class="tblock">` - a `.toolbar`, the table inside
 *   its own `.tablewrap` scroller, then the pager and any note. Returns
 *   `empty()` instead when there is nothing to show, never an empty grid that
 *   reads like a zero.
 */
export function table(rows, opts) {
  opts = opts || {};
  rows = Array.isArray(rows) ? rows.filter(function (r) { return r && typeof r === 'object'; }) : [];

  if (!rows.length) {
    return empty(opts.empty || {
      what: 'No rows for this cut of the data.',
      why: 'The pipeline returned an empty result here. That is not the same as a zero - ' +
           'it means nothing matched the filter, or the section did not run for this company.'
    });
  }

  const company = opts.co || co();
  const cols = (opts.cols && opts.cols.length ? opts.cols.slice() : Object.keys(rows[0]));
  const labels = opts.labels || {};
  const kinds = {};
  cols.forEach(function (c) { kinds[c] = colKind(c, rows, opts.units); });

  const facetCols = (Array.isArray(opts.facets) ? opts.facets : [])
    .filter(function (c) { return c in rows[0]; });
  const per = opts.page === false ? Infinity
            : (typeof opts.page === 'number' && opts.page > 0 ? opts.page : PAGE_AT);

  const state = { col: null, dir: 'desc', q: '', facets: {}, page: 0 };
  if (opts.sort) {
    if (typeof opts.sort === 'string') {
      state.col = opts.sort.replace(/^-/, '');
      state.dir = opts.sort.charAt(0) === '-' ? 'desc' : 'asc';
    } else if (opts.sort.col) {
      state.col = opts.sort.col;
      state.dir = opts.sort.dir === 'asc' ? 'asc' : 'desc';
    }
    if (state.col && cols.indexOf(state.col) < 0) state.col = null;
  }

  /* -- frame --
     The toolbar and the pager sit OUTSIDE the scroller: board.css makes
     .tablewrap a scrollport in both axes so the sticky header can pin, and a
     toolbar inside it would scroll away with the rows. */
  const wrap = el('<div class="tblock"></div>');

  const bar = el('<div class="toolbar"></div>');
  let searchInput = null;
  if (opts.filter) {
    const box = el('<div class="searchbox"></div>');
    searchInput = el('<input type="search" placeholder="' +
      esc(typeof opts.filter === 'string' ? opts.filter : 'Filter these rows' + ELLIPSIS) +
      '" aria-label="Filter rows">');
    searchInput.addEventListener('input', function () {
      state.q = searchInput.value.trim();
      state.page = 0;
      repaint();
    });
    box.appendChild(searchInput);
    const clear = el('<button type="button" class="clear" aria-label="Clear the filter">' +
      TIMES + '</button>');
    clear.addEventListener('click', function () {
      searchInput.value = '';
      state.q = '';
      state.page = 0;
      repaint();
      searchInput.focus();
    });
    box.appendChild(clear);
    bar.appendChild(box);
  }
  const chipHost = el('<div class="chips"></div>');
  if (facetCols.length) bar.appendChild(chipHost);
  const countEl = el('<span class="count"></span>');
  bar.appendChild(countEl);
  const copyBtn = el('<button class="btn tcopy" type="button">Copy as TSV</button>');
  copyBtn.addEventListener('click', function () { copyTsv(copyBtn, cols, viewRows()); });
  bar.appendChild(copyBtn);
  wrap.appendChild(bar);

  // CONTRACT section 0 rule 5 is guaranteed here rather than trusted to a
  // stylesheet another agent owns: wide tables scroll inside THIS box.
  const heightCls = (opts.height === 'tall' || opts.height === 'short' ||
                     opts.height === 'open') ? ' ' + opts.height.replace('open', 'is-open') : '';
  const scroll = el('<div class="tablewrap' + heightCls +
    '" style="overflow-x:auto;max-width:100%"></div>');
  const tbl = document.createElement('table');
  if (opts.dense) tbl.className = 'dense';
  if (opts.caption) {
    const cap = document.createElement('caption');
    cap.textContent = opts.caption;
    tbl.appendChild(cap);
  }

  const thead = document.createElement('thead');
  thead.innerHTML = '<tr>' + cols.map(function (c) {
    return '<th scope="col" data-c="' + esc(c) + '"' +
      (isNumericKind(kinds[c]) ? ' class="num"' : '') +
      ' tabindex="0" aria-sort="none" title="' + esc(c + ' · ' + kinds[c]) + '">' +
      esc(labels[c] || c) + '<span class="ar" aria-hidden="true">' + ARROWS + '</span></th>';
  }).join('') + '</tr>';
  tbl.appendChild(thead);

  const tbody = document.createElement('tbody');
  tbl.appendChild(tbody);
  const tfoot = document.createElement('tfoot');
  tbl.appendChild(tfoot);
  scroll.appendChild(tbl);
  wrap.appendChild(scroll);

  const pager = el('<div class="pager"></div>');
  wrap.appendChild(pager);
  if (opts.note) wrap.appendChild(el('<div class="tnote">' + esc(opts.note) + '</div>'));

  wireSort(thead, state, kinds, repaint);
  paintChips();
  repaint();
  return wrap;

  /* -- behaviour -- */

  /** Rows after facets, filter and sort - what "copy" and the totals both see. */
  function viewRows() {
    let out = rows;
    for (const fc in state.facets) {
      const set = state.facets[fc];
      if (set && set.size) {
        out = out.filter(function (r) { return set.has(keyOf(r[fc])); });
      }
    }
    if (state.q) {
      const q = state.q.toLowerCase();
      out = out.filter(function (r) {
        return cols.some(function (c) {
          const v = r[c];
          return !isNil(v) && String(v).toLowerCase().indexOf(q) >= 0;
        });
      });
    }
    if (state.col) {
      const c = state.col, k = kinds[c], dir = state.dir === 'asc' ? 1 : -1;
      const numeric = isNumericKind(k);
      out = out.slice().sort(function (ra, rb) {
        const x = ra[c], y = rb[c];
        const xn = isNil(x), yn = isNil(y);
        if (xn && yn) return 0;
        if (xn) return 1;            // nulls last, in both directions
        if (yn) return -1;
        if (numeric) {
          const nx = k === 'INR' ? scale(Number(x), c) : Number(x);
          const ny = k === 'INR' ? scale(Number(y), c) : Number(y);
          if (!isNaN(nx) && !isNaN(ny)) return (nx - ny) * dir;
        }
        return String(x).localeCompare(String(y), undefined, { numeric: true }) * dir;
      });
    }
    return out;
  }

  function repaint() {
    const list = viewRows();
    const pages = per === Infinity ? 1 : Math.max(1, Math.ceil(list.length / per));
    if (state.page >= pages) state.page = pages - 1;
    const from = per === Infinity ? 0 : state.page * per;
    const slice = per === Infinity ? list : list.slice(from, from + per);

    tbody.innerHTML = slice.map(function (r) {
      return '<tr>' + cols.map(function (c) { return cellHtml(c, r); }).join('') + '</tr>';
    }).join('');

    countEl.textContent = (list.length === rows.length)
      ? num(rows.length) + ' rows'
      : num(list.length) + ' of ' + num(rows.length) + ' rows';

    tfoot.innerHTML = opts.total ? totalsHtml(list) : '';

    if (pages > 1) {
      pager.hidden = false;
      pager.innerHTML =
        '<button type="button" class="btn pprev"' + (state.page === 0 ? ' disabled' : '') +
          '>Previous</button>' +
        '<span class="pinfo">rows ' + num(from + 1) + ENDASH + num(from + slice.length) +
          ' of ' + num(list.length) + ' · page ' + (state.page + 1) + ' of ' + pages +
        '</span>' +
        '<button type="button" class="btn pnext"' + (state.page >= pages - 1 ? ' disabled' : '') +
          '>Next</button>';
      const p = pager.querySelector('.pprev'), n = pager.querySelector('.pnext');
      if (p) p.addEventListener('click', function () { state.page--; repaint(); scroll.scrollTop = 0; });
      if (n) n.addEventListener('click', function () { state.page++; repaint(); scroll.scrollTop = 0; });
    } else {
      pager.hidden = true;
      pager.innerHTML = '';
    }
  }

  /** One cell, formatted by its column kind and linked if `opts.links` says so. */
  function cellHtml(c, r) {
    const v = r[c], k = kinds[c];
    const numeric = isNumericKind(k);
    const neg = numeric && Number(k === 'INR' ? scale(Number(v), c) : Number(v)) < 0;
    let cls = numeric ? 'num'
            : (k === 'code' ? 'code'
            : (/name|desc|remark|item|label/i.test(c) ? 'nm' : ''));
    if (neg) cls += ' neg';

    if (isNil(v)) {
      // board.css .nc - small, grey, lowercase, reason in the title. It must
      // read as neither a number nor a nil, because at JIVO they are not the
      // same thing and a bare dash cannot tell them apart.
      return '<td class="' + cls + ' nil"><span class="nc" title="' +
             esc('not computed - this column is empty on this row') +
             '">n/c</span></td>';
    }
    let inner = fmtCell(v, c, k);
    // <code> is monospace in every browser's default stylesheet, so a code
    // column reads as a code even if board.css has no rule for it.
    if (k === 'code') inner = '<code>' + inner + '</code>';
    const href = cellHref(c, v, r);
    if (href) inner = '<a href="' + esc(href) + '">' + inner + '</a>';
    return '<td class="' + cls + '">' + inner + '</td>';
  }

  /** @returns {string|null} */
  function cellHref(c, v, r) {
    const spec = opts.links && opts.links[c];
    if (!spec) return null;
    if (typeof spec === 'function') {
      try { return spec(v, r, company) || null; } catch (e) { return null; }
    }
    const cfg = typeof spec === 'string' ? { kind: spec } : (spec || {});
    switch (cfg.kind) {
      case 'party': {
        const card = cfg.card ? r[cfg.card] : v;
        return isNil(card) ? null : hrefParty(card, company);
      }
      case 'bank': return hrefBank(v, company);
      case 'gl': return hrefGL(v, company);
      case 'derivation': return hrefDerivation(v, company);
      case 'section': return hrefSection(v, company);
      case 'document': {
        const ot = cfg.objType ? r[cfg.objType]
                 : (r.OBJ_TYPE !== undefined ? r.OBJ_TYPE : r.OBJTYPE);
        const de = cfg.docEntry ? r[cfg.docEntry]
                 : (r.DOC_ENTRY !== undefined ? r.DOC_ENTRY : v);
        if (isNil(ot) || isNil(de)) return null;
        return hrefDocument(ot, de, company);
      }
      default: return null;
    }
  }

  /**
   * Totals row. Money columns are lifted to rupees with `scale()` BEFORE they
   * are summed; percentages, ages and dates are left blank because their sum
   * means nothing. Totals cover every filtered row, not just the visible page.
   */
  function totalsHtml(list) {
    const only = Array.isArray(opts.total) ? opts.total : null;
    let labelled = false;
    const cells = cols.map(function (c) {
      const k = kinds[c];
      const wanted = only ? (only.indexOf(c) >= 0) : (k === 'INR' || k === 'count');
      if (!wanted) {
        if (!labelled) {
          labelled = true;
          return '<td class="ttot-lab">Total · ' + esc(num(list.length)) + ' rows' +
                 (list.length !== rows.length ? ' (filtered)' : '') + '</td>';
        }
        return '<td></td>';
      }
      let sum = 0, seen = 0;
      for (let i = 0; i < list.length; i++) {
        const v = list[i][c];
        if (isNil(v)) continue;
        const n = (k === 'INR') ? scale(Number(v), c) : Number(v);
        if (!isNaN(n)) { sum += n; seen++; }
      }
      if (!seen) return '<td class="num"></td>';
      const txt = (k === 'INR') ? money(sum) : num(sum);
      return '<td class="num' + (sum < 0 ? ' neg' : '') + '"><b>' + esc(txt) + '</b></td>';
    });
    if (!labelled && cells.length) cells[0] = '<td class="ttot-lab">Total</td>';
    return '<tr class="ttot">' + cells.join('') + '</tr>';
  }

  function paintChips() {
    if (!facetCols.length) return;
    chipHost.innerHTML = '';
    facetCols.forEach(function (c) {
      const counts = new Map();
      rows.forEach(function (r) {
        const k = keyOf(r[c]);
        counts.set(k, (counts.get(k) || 0) + 1);
      });
      // a facet of one value, or of every value, is noise not a filter
      if (counts.size < 2 || counts.size > 24) return;
      const grp = el('<span class="chipgrp"><span class="chiplab">' +
        esc(labels[c] || c) + '</span></span>');
      Array.from(counts.entries())
        .sort(function (a, b) { return b[1] - a[1]; })
        .forEach(function (pair) {
          const val = pair[0], n = pair[1];
          const b = el('<button type="button" class="chip" aria-pressed="false">' +
            esc(val === '' ? '(blank)' : val) + ' <span class="n">' + esc(num(n)) +
            '</span></button>');
          b.addEventListener('click', function () {
            if (!state.facets[c]) state.facets[c] = new Set();
            const set = state.facets[c];
            if (set.has(val)) set.delete(val); else set.add(val);
            b.setAttribute('aria-pressed', String(set.has(val)));
            state.page = 0;
            repaint();
          });
          grp.appendChild(b);
        });
      chipHost.appendChild(grp);
    });
  }
}

/** Facet keys are strings, so 0, '0' and null cannot silently merge. */
function keyOf(v) { return isNil(v) ? '' : String(v); }

/**
 * v1's `wireSort`, moved onto the data model: clicking a header sorts by the
 * stored value (money lifted by `scale()`), not by the rendered text, so
 * "7.35 Cr" and "9,00,000" can never sort against each other wrongly.
 * @param {HTMLElement} thead @param {Object} state @param {Object} kinds @param {Function} repaint
 */
function wireSort(thead, state, kinds, repaint) {
  thead.querySelectorAll('th').forEach(function (th) {
    const c = th.dataset.c;
    // an initial sort has to SHOW, or the first click looks like it did nothing
    if (c === state.col) {
      th.setAttribute('aria-sort', state.dir === 'asc' ? 'ascending' : 'descending');
      th.dataset.dir = state.dir;
    }
    const go = function () {
      if (state.col === c) state.dir = (state.dir === 'asc' ? 'desc' : 'asc');
      else { state.col = c; state.dir = isNumericKind(kinds[c]) ? 'desc' : 'asc'; }
      state.page = 0;
      thead.querySelectorAll('th').forEach(function (o) {
        o.setAttribute('aria-sort', 'none');
        delete o.dataset.dir;
      });
      th.setAttribute('aria-sort', state.dir === 'asc' ? 'ascending' : 'descending');
      th.dataset.dir = state.dir;
      repaint();
    };
    th.addEventListener('click', go);
    th.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    });
  });
}

/**
 * Copy the filtered, sorted rows as TSV - raw stored values under raw SAP
 * column names, because that is what an operator pastes back into SAP or Excel.
 * @param {HTMLElement} btn @param {string[]} cols @param {Array<Object>} list
 */
function copyTsv(btn, cols, list) {
  const lines = [cols.join('\t')];
  list.forEach(function (r) {
    lines.push(cols.map(function (c) {
      const v = r[c];
      return isNil(v) ? '' : String(v).replace(/[\t\r\n]+/g, ' ');
    }).join('\t'));
  });
  const text = lines.join('\n');
  const was = btn.textContent;
  const done = function (ok) {
    btn.textContent = ok ? 'Copied ' + num(list.length) + ' rows' : 'Copy failed';
    setTimeout(function () { btn.textContent = was; }, 1800);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(
      function () { done(true); },
      function () { done(fallbackCopy(text)); }
    );
  } else {
    done(fallbackCopy(text));
  }
}

/** @param {string} text @returns {boolean} */
function fallbackCopy(text) {
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
  } catch (e) { return false; }
}

/* == crumb =============================================================== */

/**
 * The drill-down trail. The last entry is the page you are on and is never a
 * link; every earlier entry that carries an href is one.
 * @param {Array<{label:string, href?:string}>} trail
 * @returns {HTMLElement} `<nav class="crumb">`
 */
export function crumb(trail) {
  const items = (trail || []).filter(Boolean);
  const nav = el('<nav class="crumb" aria-label="Breadcrumb"></nav>');
  const ol = document.createElement('ol');
  items.forEach(function (t, i) {
    const li = document.createElement('li');
    const last = (i === items.length - 1);
    if (t.href && !last) {
      const a = document.createElement('a');
      a.href = t.href;
      a.textContent = t.label == null ? '' : String(t.label);
      li.appendChild(a);
    } else {
      const s = document.createElement('span');
      s.textContent = t.label == null ? '' : String(t.label);
      if (last) s.setAttribute('aria-current', 'page');
      li.appendChild(s);
    }
    // no separator element: board.css draws the chevron with
    // `.crumb ol > li + li::before`, so the trail stays one clean list in the
    // DOM and cannot end up double-chevroned.
    ol.appendChild(li);
  });
  nav.appendChild(ol);
  return nav;
}

/* == note ================================================================ */

/**
 * One fetch per note id per page-load, so a note rendered twice - or a note
 * that is not published with the site - costs exactly one request.
 * @type {Object<string, Promise<string>>}
 */
const _noteCache = {};

/**
 * Render `pipeline/notes/<id>.md` inline - the adversarial working note behind
 * a section, in the operator's own board.
 *
 * Safety: the whole file is HTML-escaped FIRST, then a small markdown subset is
 * applied to the escaped text (headings, bold, inline and fenced code, lists,
 * pipe tables, links, blockquotes, rules). Raw input never reaches `innerHTML`,
 * and link targets are restricted to http / https / mailto / relative, so a
 * `javascript:` href written into a note cannot fire.
 *
 * If the file is missing - it is not copied to Vercel - this renders NOTHING.
 * An absent note is not an error worth showing an accountant.
 *
 * @param {string} id note id, e.g. 'grpo' or 'customer-ageing'
 * @returns {HTMLElement} `<div class="note">`, filled asynchronously
 */
export function note(id) {
  const host = el('<div class="note" data-note="' + esc(id) + '"></div>');
  // site-v2/ is the deploy root, so '../pipeline/notes' resolves ABOVE it and
  // 404s in production while working from a repo checkout. The build copies
  // the notes to /notes; the old path stays as a fallback for anyone serving
  // the repo root directly.
  const url = 'notes/' + encodeURIComponent(String(id)) + '.md';
  const fallbackUrl = '../pipeline/notes/' + encodeURIComponent(String(id)) + '.md';
  if (!_noteCache[id]) {
    // Ask the index whether this note exists before fetching it. A fetch-and-fail
    // logs a console 404 the page cannot suppress, and browser-check.sh treats
    // console errors as failures — benign 404s would drown a real one.
    _noteCache[id] = fetch('notes/_index.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (have) {
        if (Array.isArray(have) && have.indexOf(String(id)) === -1) {
          throw new Error('no note published for ' + id);
        }
        return fetch(url, { cache: 'no-cache' })
          .then(function (r) {
            if (r.ok) return r.text();
            // Serving the repo root rather than site-v2? Try where notes live there.
            return fetch(fallbackUrl, { cache: 'no-cache' }).then(function (r2) {
              if (!r2.ok) throw new Error('no note for ' + id);
              return r2.text();
            });
          });
      });
  }
  _noteCache[id]
    .then(function (src) {
      if (!src || !src.trim()) { host.remove(); return; }
      // The note is arbitrary markdown from the pipeline: long SQL lines, wide
      // tables, unbreakable column names. Collapsed it is invisible; OPENED it
      // pushed the page 450px sideways at 390px wide. Its own scroller keeps the
      // overflow inside the disclosure where it belongs.
      host.innerHTML =
        '<details class="note-box">' +
          '<summary>Working note · ' + esc(id) + '</summary>' +
          '<div class="note-body tablewrap">' + mdToHtml(src, 2) + '</div>' +
        '</details>';
    })
    .catch(function () { host.remove(); });
  return host;
}

/**
 * A deliberately small markdown subset. Escaping happens on the WHOLE source
 * before any rule runs, so every rule below matches already-escaped text
 * (`>` is `&gt;`, `"` is `&quot;`) - which is why the blockquote test looks odd.
 * @param {string} src
 * @param {number} [baseLevel=1] how far to push headings down: `1` makes `#` an
 *   `<h2>` (the masthead owns the only `<h1>`), `2` makes it an `<h3>`, which is
 *   what a note callout wants.
 * @returns {string} safe HTML
 */
function mdToHtml(src, baseLevel) {
  const base = (typeof baseLevel === 'number' && baseLevel >= 1) ? baseLevel : 1;
  const lines = escFallback(String(src).replace(/\r\n?/g, '\n')).split('\n');
  const out = [];
  const para = [];
  let i = 0;

  const flushPara = function () {
    if (para.length) out.push('<p>' + inline(para.join(' ')) + '</p>');
    para.length = 0;
  };

  while (i < lines.length) {
    const line = lines[i];

    // fenced code
    const fence = line.match(/^\s*(```+|~~~+)/);
    if (fence) {
      flushPara();
      const close = fence[1].charAt(0) === '`' ? '```' : '~~~';
      const body = [];
      i++;
      while (i < lines.length && lines[i].indexOf(close) < 0) { body.push(lines[i]); i++; }
      i++;
      out.push('<pre><code>' + body.join('\n') + '</code></pre>');
      continue;
    }

    // blank line
    if (!line.trim()) { flushPara(); i++; continue; }

    // horizontal rule
    if (/^\s*([-*_])\s*(\1\s*){2,}$/.test(line)) { flushPara(); out.push('<hr>'); i++; continue; }

    // heading - never emits a second <h1>, the masthead owns that
    const h = line.match(/^\s*(#{1,6})\s+(.*?)\s*#*\s*$/);
    if (h) {
      flushPara();
      const lvl = Math.min(6, h[1].length + base);
      out.push('<h' + lvl + '>' + inline(h[2]) + '</h' + lvl + '>');
      i++;
      continue;
    }

    // blockquote ('>' reads as '&gt;' after escaping)
    if (/^\s*&gt;/.test(line)) {
      flushPara();
      const body = [];
      while (i < lines.length && /^\s*&gt;/.test(lines[i])) {
        body.push(lines[i].replace(/^\s*&gt;\s?/, ''));
        i++;
      }
      out.push('<blockquote>' +
               mdToHtml(unescapeForNested(body.join('\n')), base) + '</blockquote>');
      continue;
    }

    // pipe table: a header row followed by a |---|---| delimiter
    if (line.indexOf('|') >= 0 && i + 1 < lines.length &&
        /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(lines[i + 1])) {
      flushPara();
      const head = splitRow(line);
      const align = splitRow(lines[i + 1]).map(function (c) {
        const t = c.trim();
        return /^:-+:$/.test(t) ? 'center' : /-+:$/.test(t) ? 'right' : '';
      });
      i += 2;
      const body = [];
      while (i < lines.length && lines[i].indexOf('|') >= 0 && lines[i].trim()) {
        body.push(splitRow(lines[i]));
        i++;
      }
      out.push(
        '<div class="tscroll" style="overflow-x:auto;max-width:100%"><table><thead><tr>' +
        head.map(function (c, ix) {
          return '<th' + (align[ix] ? ' style="text-align:' + align[ix] + '"' : '') + '>' +
                 inline(c) + '</th>';
        }).join('') +
        '</tr></thead><tbody>' +
        body.map(function (r) {
          return '<tr>' + r.map(function (c, ix) {
            return '<td' + (align[ix] ? ' style="text-align:' + align[ix] + '"' : '') + '>' +
                   inline(c) + '</td>';
          }).join('') + '</tr>';
        }).join('') +
        '</tbody></table></div>');
      continue;
    }

    // lists, one level of nesting by indent
    if (/^(\s*)([-*+]|\d+[.)])\s+/.test(line)) {
      flushPara();
      const ordered = /^\s*\d/.test(line);
      const tag = ordered ? 'ol' : 'ul';
      const parts = [];
      let open = 0, depth = -1;
      while (i < lines.length) {
        const m = lines[i].match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/);
        if (!m) {
          // a continuation line indented under the previous item
          if (open && lines[i].trim() && /^\s{2,}\S/.test(lines[i])) {
            parts.push(' ' + inline(lines[i].trim()));
            i++;
            continue;
          }
          break;
        }
        const d = Math.min(1, Math.floor(m[1].replace(/\t/g, '  ').length / 2));
        if (depth < 0) { parts.push('<' + tag + '>'); open = 1; depth = d; }
        else if (d > depth) { parts.push('<' + tag + '>'); open++; depth = d; }
        else if (d < depth && open > 1) { parts.push('</' + tag + '>'); open--; depth = d; }
        parts.push('<li>' + inline(m[3]) + '</li>');
        i++;
      }
      while (open-- > 0) parts.push('</' + tag + '>');
      out.push(parts.join(''));
      continue;
    }

    para.push(line.trim());
    i++;
  }
  flushPara();
  return out.join('\n');
}

/** Split a pipe-table row into cells. @param {string} line @returns {string[]} */
function splitRow(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '')
    .split('|').map(function (c) { return c.trim(); });
}

/**
 * Blockquote bodies are re-parsed, and the parser escapes on entry - so undo
 * the one escaping pass before handing text back in, or `&amp;` doubles up.
 * @param {string} s @returns {string}
 */
function unescapeForNested(s) {
  return s.replace(/&lt;/g, '<').replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
          .replace(/&amp;/g, '&');
}

/**
 * Inline markdown on already-escaped text: code spans first (so nothing inside
 * them is reinterpreted), then links, then bold.
 * @param {string} s @returns {string}
 */
function inline(s) {
  const codes = [];
  let t = String(s).replace(/`([^`]+)`/g, function (m, c) {
    codes.push(c);
    return '@@JIVOCODE' + (codes.length - 1) + '@@';
  });
  t = t.replace(/\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;[^)]*&quot;)?\)/g,
    function (m, text, url) {
      const safe = safeUrl(url);
      if (!safe) return text;
      const ext = /^https?:/i.test(unescapeForNested(safe));
      return '<a href="' + safe + '"' +
             (ext ? ' target="_blank" rel="noopener noreferrer"' : '') + '>' + text + '</a>';
    });
  t = t.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/__([^_]+)__/g, '<b>$1</b>');
  t = t.replace(/@@JIVOCODE(\d+)@@/g, function (m, ix) {
    return '<code>' + codes[Number(ix)] + '</code>';
  });
  return t;
}

/**
 * Only http, https, mailto, in-page anchors and relative paths survive.
 * @param {string} url already-escaped URL text
 * @returns {string|null} the URL (still escaped, safe inside a quoted attribute)
 */
function safeUrl(url) {
  const probe = unescapeForNested(String(url)).replace(/[\s\u0000-\u001f]/g, '').toLowerCase();
  if (/^(javascript|data|vbscript|file):/.test(probe)) return null;
  if (/^[a-z][a-z0-9+.-]*:/.test(probe) && !/^(https?|mailto):/.test(probe)) return null;
  return String(url);
}

/* == empty =============================================================== */

/**
 * The "never a confident zero" renderer: a muted card that says what is missing
 * and why. Use it wherever a panel would otherwise print a zero, a blank or a
 * bare dash - at JIVO those three read identically and none of them is true.
 *
 * @param {string|{what?:string, why?:string, hint?:string, href?:string, hrefLabel?:string}} msg
 * @returns {HTMLElement} `<div class="empty">`
 */
export function empty(msg) {
  const o = (msg == null || typeof msg === 'string') ? { what: msg || 'Not computed.' } : msg;
  // board.css styles `.empty b` as the block heading and the rest as its reason
  let html = '<b>' + esc(o.what || 'Not computed.') + '</b>';
  if (o.why) html += '<div class="empty-why">' + esc(o.why) + '</div>';
  if (o.hint) html += '<div class="empty-hint">' + esc(o.hint) + '</div>';
  if (o.href) {
    html += '<div class="empty-link"><a href="' + esc(o.href) + '">' +
            esc(o.hrefLabel || 'See how this is measured') + '</a></div>';
  }
  return el('<div class="empty">' + html + '</div>');
}
