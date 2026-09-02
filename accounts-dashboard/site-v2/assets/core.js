/**
 * JIVO Accounts Board v2 — `assets/core.js`
 *
 * The data, formatting and linking half of CONTRACT.md §3. Every page imports
 * from this one module; the rendering half (`shell`, `kpiRow`, `table`, …)
 * lives in `./ui.js` and is re-exported from the last line of this file, so a
 * page only ever writes:
 *
 *     import { shell, slice, company, money, onRefresh } from './assets/core.js';
 *
 * Rules this module exists to enforce (CONTRACT §0, §2, §4, §6.1):
 *
 *   • **The column name carries the unit.** `scale(v, col)` matches the suffix
 *     ANCHORED at the end of the name — `/_CR$/` → crores, `/_L$/` → lakhs,
 *     everything else rupees. A substring test would read `OUTSTANDING_CR_L`
 *     (lakhs) as crores and print a figure 100× too big.
 *   • **Nil is not unknown.** `money(null)` returns `null`, never `"₹0"` and
 *     never `"—"`, so a caller can render `empty("not computed — <reason>")`
 *     instead of a confident zero.
 *   • **Stale data must announce itself.** On 2026-08-22 this board served
 *     5-hour-old numbers that looked live. `isStale()` is the guarantee the
 *     whole board rests on, and `onRefresh()` re-renders in place the moment
 *     `generated_at` actually moves.
 *
 * No dependencies, no build step, no DOM access at module scope (so the file
 * can be syntax-checked under plain `node`).
 *
 * Read-only: nothing here writes to SAP, and nothing here issues a query.
 * Everything comes from the pre-built JSON in `site-v2/data/`.
 */

/* ══════════════════════════════════════════════════════════════════════════
   Constants
   ══════════════════════════════════════════════════════════════════════════ */

/** localStorage key holding the operator's chosen company. @type {string} */
const CO_KEY = 'jivo-accounts-co';
/** localStorage key holding the theme override (CONTRACT §6.1). @type {string} */
const THEME_KEY = 'jivo-theme';
/** Company used when nothing else says otherwise. @type {string} */
const DEFAULT_CO = 'oil';
/** Company keys known without the manifest (it is the source of truth). */
const FALLBACK_COMPANIES = ['oil', 'mart', 'bev'];
/** How often `onRefresh` re-reads `data/manifest.json`, in ms. */
const POLL_MS = 60000;
/** A build older than this many minutes is stale during office hours. */
const STALE_MINUTES = 30;
/** Local-clock window in which staleness matters: 07:00 … 22:59. */
const OFFICE_FROM = 7;
const OFFICE_TO = 23;

const RUPEE = '₹';   // ₹
const MINUS = '−';   // − (true minus, never a hyphen, never brackets)

/**
 * section id (as it appears in `manifest.sections` and in every
 * `data/<section>.<company>.json`) → the page that renders it.
 * Sections with no page of their own fall back to an anchor on the board.
 * Page names are also accepted as keys so `hrefSection('payables')` works.
 */
const SECTION_PAGE = {
  'customer-ageing': 'receivables.html',
  'vendor-ageing':   'payables.html',
  'open-item-list':  'open-items.html',
  'grpo':            'grpo.html',
  'goods-return':    'goods-return.html',
  'return-note':     'return-note.html',
  'provisions':      'provisions.html',
  'cash-sale':       'cash-sale.html',
  'bank-accounts':   'banks.html',
  'bank-reco':       'bank-reco.html',
  'transporter':     'transporter.html',
  // aliases, so a page id may be used interchangeably with a section id
  'receivables':     'receivables.html',
  'payables':        'payables.html',
  'open-items':      'open-items.html',
  'banks':           'banks.html',
  'index':           'index.html',
  'methodology':     'methodology.html',
  'health':          'health.html',
  'search':          'search.html'
};

/* ══════════════════════════════════════════════════════════════════════════
   Module state — all caching lives here
   ══════════════════════════════════════════════════════════════════════════ */

/** @type {object|null} last manifest we successfully read (or a stale stand-in). */
let _manifest = null;
/** @type {Promise<object>|null} in-flight manifest fetch, so N callers = 1 request. */
let _manifestInFlight = null;
/**
 * Last `generated_at` we have observed.
 *   `undefined` → never observed (do not fire refresh listeners)
 *   `null`      → observed, but the manifest was unreachable
 * @type {string|null|undefined}
 */
let _lastGen;

/** @type {Map<string, Promise<object>>} `section|company|generated_at` → slice. */
const _sliceCache = new Map();
/** @type {Map<string, Promise<object>>} `company|generated_at` → derivations. */
const _derivCache = new Map();
/** @type {Map<string, Promise<Array>>} `company|generated_at` → parties. */
const _partyCache = new Map();

/** @type {Set<Function>} callbacks registered through {@link onRefresh}. */
const _listeners = new Set();
/** @type {*} handle of the 60s poll timer; null while no listener is registered. */
let _timer = null;
/** Guard so a slow poll never stacks on top of itself. */
let _polling = false;
/** Set once, so repeated onRefresh() calls do not stack visibility listeners. */
let _visibilityHooked = false;

/* ══════════════════════════════════════════════════════════════════════════
   Safe browser access — a private window throws on localStorage (CONTRACT §6.1)
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Read a localStorage key, returning null instead of throwing.
 * @param {string} k
 * @returns {string|null}
 */
function lsGet(k) {
  try { return localStorage.getItem(k); } catch (e) { return null; }
}

/**
 * Write a localStorage key, swallowing quota/private-mode failures.
 * @param {string} k
 * @param {string} v
 * @returns {boolean} true when it stuck
 */
function lsSet(k, v) {
  try { localStorage.setItem(k, v); return true; } catch (e) { return false; }
}

/** @returns {boolean} true when a real DOM is present. */
function hasDOM() {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

/**
 * Absolute URL of a file in `site-v2/data/`, resolved against this module so it
 * is correct no matter which directory the importing page sits in.
 * @param {string} name e.g. `'manifest.json'`
 * @returns {string}
 */
function dataURL(name) {
  try { return new URL('../data/' + name, import.meta.url).href; }
  catch (e) { return 'data/' + name; }
}

/**
 * Fetch and parse one JSON file.
 * @param {string} url
 * @param {boolean} [noStore] bypass the HTTP cache entirely (used for the manifest)
 * @returns {Promise<*>}
 * @throws {Error} on a network failure or a non-2xx status
 */
async function getJSON(url, noStore) {
  const res = await fetch(url, noStore ? { cache: 'no-store' } : undefined);
  if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + url);
  return res.json();
}

/* ══════════════════════════════════════════════════════════════════════════
   Theme (CONTRACT §6.1) — dark is the default; only the literal 'light' isn't
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * The active theme. Mirrors the no-flash bootstrap in every page `<head>`:
 * anything other than the literal string `light` means dark.
 * @returns {'light'|'dark'}
 */
export function theme() {
  return lsGet(THEME_KEY) === 'light' ? 'light' : 'dark';
}

/**
 * Apply and persist a theme. Sets `data-theme` on `<html>`, writes
 * `localStorage['jivo-theme']` (inside try/catch) and dispatches a
 * `jivo:theme` event on `window` so charts can re-resolve their CSS
 * variables — charts must never bake hex literals (CONTRACT §6.1).
 * @param {'light'|'dark'|string} t anything but `'light'` is treated as dark
 * @returns {'light'|'dark'} the theme actually applied
 */
export function setTheme(t) {
  const next = t === 'light' ? 'light' : 'dark';
  lsSet(THEME_KEY, next);
  if (hasDOM()) {
    document.documentElement.setAttribute('data-theme', next);
    try {
      window.dispatchEvent(new CustomEvent('jivo:theme', { detail: { theme: next } }));
    } catch (e) { /* very old browser: the attribute is what matters */ }
  }
  return next;
}

/* ══════════════════════════════════════════════════════════════════════════
   Company
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Company keys the manifest declares, falling back to the three JIVO books
 * before the manifest has loaded.
 * @returns {string[]}
 */
function companyKeys() {
  const list = _manifest && Array.isArray(_manifest.companies)
    ? _manifest.companies.map(c => c && c.key).filter(Boolean)
    : null;
  return (list && list.length) ? list : FALLBACK_COMPANIES;
}

/**
 * @param {*} k
 * @returns {boolean} true when `k` names one of the three company books
 */
function isCompany(k) {
  return typeof k === 'string' && companyKeys().indexOf(k) !== -1;
}

/**
 * The company this page is showing: `?co=` wins, then
 * `localStorage['jivo-accounts-co']`, then `'oil'`.
 * A valid `?co=` is written back to localStorage so drilling into another page
 * without the parameter stays on the same book.
 * @returns {string} one of `oil` | `mart` | `bev`
 */
export function company() {
  let q = null;
  if (hasDOM()) {
    try { q = new URLSearchParams(window.location.search).get('co'); } catch (e) { q = null; }
  }
  if (isCompany(q)) {
    lsSet(CO_KEY, q);
    return q;
  }
  const saved = lsGet(CO_KEY);
  if (isCompany(saved)) return saved;
  return DEFAULT_CO;
}

/**
 * Human label for a company key, from the manifest when it is loaded.
 * @param {string} [key] defaults to the current company
 * @returns {string} e.g. `'JIVO Wellness (Oil)'`
 */
export function companyLabel(key) {
  const k = key || company();
  const rec = _manifest && Array.isArray(_manifest.companies)
    ? _manifest.companies.find(c => c && c.key === k) : null;
  return (rec && rec.label) || k;
}

/**
 * Switch company **in place**: rewrites `?co=` with `history.replaceState`
 * (no navigation, no reload), persists the choice, drops the memory caches for
 * the old book and re-runs every {@link onRefresh} callback so the page
 * re-renders itself.
 * @param {string} key `oil` | `mart` | `bev`
 * @returns {string} the company now in effect (unchanged if `key` was invalid)
 */
export function setCompany(key) {
  if (!isCompany(key)) return company();
  if (key === company()) return key;

  lsSet(CO_KEY, key);

  if (hasDOM()) {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('co', key);
      window.history.replaceState(window.history.state, '', url.pathname + url.search + url.hash);
    } catch (e) { /* a browser without URL/history still re-renders below */ }
  }

  emit({ reason: 'company', company: key, manifest: _manifest, restoreScroll: false });
  return key;
}

/* ══════════════════════════════════════════════════════════════════════════
   Data
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Build-stamp used as the cache key and cache-buster for every data file.
 * @returns {string}
 */
function genKey() {
  return (_manifest && _manifest.generated_at) || '0';
}

/**
 * Append the build stamp so a new build is never served from the HTTP cache,
 * and the previous build's copy is never reused.
 * @param {string} name file name inside `data/`
 * @returns {string}
 */
function stampedURL(name) {
  return dataURL(name) + '?v=' + encodeURIComponent(genKey());
}

/** Drop every memoised slice/derivation/party set (a new build landed). */
function invalidate() {
  _sliceCache.clear();
  _derivCache.clear();
  _partyCache.clear();
}

/**
 * A stand-in manifest for when `data/manifest.json` cannot be read at all.
 * It is deliberately marked stale so the freshness banner shouts rather than
 * showing an empty board that looks healthy.
 * @param {string} why
 * @returns {object}
 */
function unreachableManifest(why) {
  return {
    generated_at: null,
    as_of: null,
    build_seconds: null,
    stale: true,
    stale_reason: why,
    error: why,
    companies: FALLBACK_COMPANIES.map(k => ({ key: k, label: k, schema: null })),
    sections: {},
    kpis: {},
    alerts: [],
    history_points: 0
  };
}

/**
 * The build manifest — `generated_at`, `as_of`, per-section status/row counts,
 * every KPI headline value and its cross-check (CONTRACT §2).
 *
 * Cached in memory and revalidated by the {@link onRefresh} poll. Never
 * throws: if the file is unreachable it resolves to a manifest flagged
 * `stale:true` with `error` set, so the page can still render its shell.
 *
 * @param {{force?: boolean}} [opts] `force:true` re-reads immediately
 * @returns {Promise<object>}
 */
export async function manifest(opts) {
  const force = !!(opts && opts.force);
  if (_manifest && !force && !_manifest.error) return _manifest;
  if (_manifestInFlight && !force) return _manifestInFlight;

  _manifestInFlight = (async () => {
    try {
      const m = await getJSON(dataURL('manifest.json'), true);
      observe(m);
      return _manifest;
    } catch (e) {
      const why = 'manifest.json could not be read (' + (e && e.message ? e.message : e) + ')';
      // Keep a good manifest if we had one — a blip must not blank the board,
      // but it must not be reported as fresh either.
      if (_manifest && !_manifest.error) return _manifest;
      _manifest = unreachableManifest(why);
      if (_lastGen === undefined) _lastGen = null;
      return _manifest;
    } finally {
      _manifestInFlight = null;
    }
  })();

  return _manifestInFlight;
}

/**
 * Record a freshly read manifest and report whether the build moved.
 * @param {object} m
 * @returns {boolean} true when `generated_at` changed since the last observation
 */
function observe(m) {
  const gen = (m && m.generated_at) || null;
  const first = _lastGen === undefined;
  const moved = !first && gen !== _lastGen;
  if (moved) invalidate();
  _manifest = m;
  _lastGen = gen;
  return moved;
}

/**
 * One section for one company: `data/<section>.<company>.json`.
 *
 * Column names are **unchanged from SAP/the SQL** (`ADJ_OPEN`, `EFF_OPEN_INR`,
 * `UB_90PLUS_GROSS`) — pass every one of them through {@link scale} with its
 * own name before adding two together.
 *
 * Never throws. A missing or broken file resolves to the same shape with
 * `error` set, so the page renders a reason instead of a confident zero.
 *
 * @param {string} section e.g. `'vendor-ageing'`
 * @param {string} [co] defaults to the current company
 * @returns {Promise<{section:string, company:string, as_of:?string,
 *                    summary:object[], detail:object[], error:?string}>}
 */
export async function slice(section, co) {
  const c = co || company();
  await manifest();
  const key = section + '|' + c + '|' + genKey();
  if (_sliceCache.has(key)) return _sliceCache.get(key);

  const p = (async () => {
    try {
      const d = await getJSON(stampedURL(section + '.' + c + '.json'));
      return {
        section: d.section || section,
        company: d.company || c,
        as_of: d.as_of || (_manifest ? _manifest.as_of : null),
        summary: Array.isArray(d.summary) ? d.summary : [],
        detail: Array.isArray(d.detail) ? d.detail : [],
        error: d.error || null
      };
    } catch (e) {
      const why = 'could not read data/' + section + '.' + c + '.json ('
        + (e && e.message ? e.message : e) + ')';
      if (typeof console !== 'undefined') console.warn('[core] ' + why);
      _sliceCache.delete(key);   // a transient failure must not be cached
      return {
        section, company: c,
        as_of: _manifest ? _manifest.as_of : null,
        summary: [], detail: [], error: why
      };
    }
  })();

  _sliceCache.set(key, p);
  return p;
}

/**
 * Every derivation record for one company, keyed by KPI id — the drill-down
 * spine behind `derivation.html`. Each record carries `.value .label .unit
 * .formula .method .terms .excludes .sql .caveats .closure .rows .drill
 * .section_traps .reproduces_spec_measurement`.
 *
 * Never throws; an unreadable file resolves to `{}` with a non-enumerable
 * `__error` describing why, so `Object.keys()` stays clean.
 *
 * @param {string} [co] defaults to the current company
 * @returns {Promise<Object<string, object>>}
 */
export async function derivations(co) {
  const c = co || company();
  await manifest();
  const key = c + '|' + genKey();
  if (_derivCache.has(key)) return _derivCache.get(key);

  const p = (async () => {
    try {
      const d = await getJSON(stampedURL('derivations.' + c + '.json'));
      return (d && typeof d === 'object') ? d : withError({}, 'derivations file was not an object');
    } catch (e) {
      const why = 'could not read data/derivations.' + c + '.json ('
        + (e && e.message ? e.message : e) + ')';
      if (typeof console !== 'undefined') console.warn('[core] ' + why);
      _derivCache.delete(key);
      return withError({}, why);
    }
  })();

  _derivCache.set(key, p);
  return p;
}

/**
 * One derivation record, or null when that KPI id is not in this company's
 * registry (a KPI can exist in Oil and not in Beverages).
 * @param {string} id KPI id, e.g. `'ap-trade-open'`
 * @param {string} [co]
 * @returns {Promise<object|null>}
 */
export async function derivation(id, co) {
  const all = await derivations(co);
  return (id && Object.prototype.hasOwnProperty.call(all, id)) ? all[id] : null;
}

/**
 * The party directory for one company:
 * `[{card, name, group, kind:'TRADE'|'BRANCH'|'INTERCO'|'STAFF', side:'V'|'C', balance}]`.
 * `balance` is `OCRD.CurrentAccountBalance` in **rupees**: positive = debit
 * (they owe JIVO / JIVO holds an advance), negative = credit (JIVO owes them).
 *
 * Never throws; an unreadable file resolves to `[]` with a non-enumerable
 * `__error`.
 *
 * @param {string} [co] defaults to the current company
 * @returns {Promise<object[]>}
 */
export async function parties(co) {
  const c = co || company();
  await manifest();
  const key = c + '|' + genKey();
  if (_partyCache.has(key)) return _partyCache.get(key);

  const p = (async () => {
    try {
      const d = await getJSON(stampedURL('parties.' + c + '.json'));
      return Array.isArray(d) ? d : withError([], 'parties file was not an array');
    } catch (e) {
      const why = 'could not read data/parties.' + c + '.json ('
        + (e && e.message ? e.message : e) + ')';
      if (typeof console !== 'undefined') console.warn('[core] ' + why);
      _partyCache.delete(key);
      return withError([], why);
    }
  })();

  _partyCache.set(key, p);
  return p;
}

/**
 * Attach a non-enumerable `__error` to an empty result.
 * @template T
 * @param {T} obj
 * @param {string} why
 * @returns {T}
 */
function withError(obj, why) {
  try {
    Object.defineProperty(obj, '__error', { value: why, enumerable: false, configurable: true });
  } catch (e) { /* frozen object: the empty result still reads as "no data" */ }
  return obj;
}

/* ══════════════════════════════════════════════════════════════════════════
   Freshness — the guarantee the whole board rests on
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Is what the page is showing old enough to mislead someone?
 *
 * Stale when **either**
 *   • `generated_at` is more than 30 minutes old **and** the local clock reads
 *     07:00–22:59 (nobody is watching the board at 03:00, and a red banner
 *     overnight trains people to ignore it), **or**
 *   • the pipeline itself set `manifest.stale === true`.
 *
 * A manifest that has not loaded, or whose `generated_at` will not parse, is
 * reported as stale with `unknown:true` — never as fresh.
 *
 * Note: a `generated_at` in the future (server clock ahead) clamps to 0 minutes
 * and reads as fresh.
 *
 * @param {object} [m] manifest to judge; defaults to the cached one
 * @returns {{stale:boolean, minutes:(number|null), reason:(string|null),
 *            unknown:boolean, generated_at:(string|null), officeHours:boolean}}
 */
export function isStale(m) {
  const man = m || _manifest;
  const hour = new Date().getHours();
  const officeHours = hour >= OFFICE_FROM && hour < OFFICE_TO;

  if (!man) {
    return { stale: true, minutes: null, unknown: true, generated_at: null, officeHours,
             reason: 'freshness unknown — data/manifest.json has not been read yet' };
  }

  const gen = man.generated_at || null;
  const t = gen ? Date.parse(gen) : NaN;

  if (!gen || isNaN(t)) {
    return { stale: true, minutes: null, unknown: true, generated_at: gen, officeHours,
             reason: man.stale_reason || man.error ||
                     'freshness unknown — the build carries no readable generated_at' };
  }

  const raw = Math.max(0, (Date.now() - t) / 60000);
  const minutes = Math.round(raw);
  const tooOld = raw > STALE_MINUTES && officeHours;
  const flagged = man.stale === true;

  let reason = null;
  if (flagged) {
    reason = man.stale_reason || 'the pipeline marked this build stale';
  } else if (tooOld) {
    reason = 'built ' + ago(gen) + ' — the 2-minute pipeline has not landed a new build';
  }

  return { stale: flagged || tooOld, minutes, unknown: false, generated_at: gen, officeHours, reason };
}

/* ══════════════════════════════════════════════════════════════════════════
   Refresh
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Run every registered callback, preserving the reader's scroll position.
 * Callbacks are awaited one at a time; one that throws never stops the others.
 * @param {{reason:string, company?:string, manifest?:object, restoreScroll?:boolean}} detail
 * @returns {Promise<void>}
 */
async function emit(detail) {
  const dom = hasDOM();
  const x = dom ? window.scrollX : 0;
  const y = dom ? window.scrollY : 0;

  for (const fn of Array.from(_listeners)) {
    try { await fn(detail); }
    catch (e) { if (typeof console !== 'undefined') console.warn('[core] refresh listener failed', e); }
  }

  if (dom) {
    try { window.dispatchEvent(new CustomEvent('jivo:refresh', { detail })); } catch (e) { /* noop */ }
    if (detail.restoreScroll !== false) {
      // The DOM was rebuilt under the reader; put them back where they were.
      const put = () => window.scrollTo(x, y);
      if (typeof requestAnimationFrame === 'function') requestAnimationFrame(put); else put();
    }
  }
}

/**
 * One poll: re-read the manifest and, only if `generated_at` actually moved,
 * drop the caches and re-render.
 * @returns {Promise<void>}
 */
async function poll() {
  if (_polling) return;
  _polling = true;
  try {
    const m = await getJSON(dataURL('manifest.json'), true);
    if (observe(m)) {
      await emit({ reason: 'build', company: company(), manifest: m, restoreScroll: true });
    }
  } catch (e) {
    // A failed poll is not a new build. Keep showing the last good numbers;
    // isStale() will start shouting on its own as the clock runs on.
    if (typeof console !== 'undefined') console.warn('[core] manifest poll failed', e);
  } finally {
    _polling = false;
  }
}

/**
 * Re-render when the data behind the page changes.
 *
 * Fires **only** when `manifest.generated_at` actually moves — not on every
 * poll, and not on the first read — and also when {@link setCompany} switches
 * book. The reader's scroll position and chosen company both survive it.
 *
 * Polls `data/manifest.json` every 60s with `cache:'no-store'`; while the tab
 * is hidden the poll is skipped and runs immediately on the tab becoming
 * visible again.
 *
 * @param {function(object=): (void|Promise<void>)} fn usually the page's `render`
 * @returns {function(): void} call it to unsubscribe
 */
export function onRefresh(fn) {
  if (typeof fn !== 'function') return () => {};
  _listeners.add(fn);

  if (!_timer && hasDOM()) {
    _timer = setInterval(() => {
      if (document.hidden) return;   // catch up on visibilitychange instead
      poll();
    }, POLL_MS);

    if (!_visibilityHooked) {
      _visibilityHooked = true;
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden) poll();
      });
    }
  }

  return function off() {
    _listeners.delete(fn);
    if (!_listeners.size && _timer) { clearInterval(_timer); _timer = null; }
  };
}

/**
 * Force an immediate manifest re-read (the freshness banner's "check now").
 * Fires the refresh listeners only if the build moved.
 * @returns {Promise<void>}
 */
export async function refreshNow() {
  await poll();
}

/* ══════════════════════════════════════════════════════════════════════════
   Formatting — carried forward from v1 (`site/index.html`) so that Accounts
   reads the same numbers the same way on both boards
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Indian digit grouping: `12345678` → `1,23,45,678`.
 * @param {string|number} s digits only — sign and decimals are the caller's job
 * @returns {string}
 */
export function inGroup(s) {
  s = String(s);
  if (s.length <= 3) return s;
  const last3 = s.slice(-3);
  let rest = s.slice(0, -3), out = '';
  while (rest.length > 2) { out = ',' + rest.slice(-2) + out; rest = rest.slice(0, -2); }
  return (rest ? rest + out : out.replace(/^,/, '')) + ',' + last3;
}

/**
 * Lift a value to **rupees** using the unit carried by its column name
 * (CONTRACT §4).
 *
 *     FOO_CR → × 1e7 (crores)   FOO_L → × 1e5 (lakhs)   anything else → rupees
 *
 * The match is **anchored at the end of the name**, and that is the whole
 * point: `OUTSTANDING_CR_L` contains `_CR` but is **lakhs**, and a substring
 * test would print it 100× too large. Always `scale()` two columns before
 * adding them.
 *
 * Non-numeric input (null, undefined, '', NaN) is returned untouched, so a
 * blank cell stays blank instead of becoming a zero.
 *
 * @param {number|string|null|undefined} v raw cell value
 * @param {string} col the column name it came from
 * @returns {number|*} rupees, or `v` unchanged when it is not a number
 */
export function scale(v, col) {
  if (v === null || v === undefined || v === '' || isNaN(v)) return v;
  if (/_CR$/i.test(col)) return Number(v) * 1e7;
  if (/_L$/i.test(col)) return Number(v) * 1e5;
  return Number(v);
}

/**
 * Money for reading: `73500000` → `₹7.35 Cr`, `735000` → `₹7.35 L`,
 * `7350` → `₹7,350`. Below ₹1 L rupees, below ₹1 Cr lakhs, else crores, 2 dp,
 * Indian grouping. Negative (a credit) gets a leading `−` (U+2212) — never
 * brackets, never a hyphen.
 *
 * **Returns `null`, not a string, for null/undefined/''/NaN**, so the caller
 * can tell "nil" from "unknown" and render `empty()` with a reason instead of
 * a confident `₹0` (CONTRACT §0.3). `money(0)` is a real zero → `'₹0'`.
 *
 * @param {number|string|null|undefined} n rupees (run {@link scale} first)
 * @param {{exact?: boolean}} [opts] `exact:true` forces full rupees, no Cr/L
 * @returns {string|null}
 */
export function money(n, opts) {
  opts = opts || {};
  if (n === null || n === undefined || n === '' || isNaN(n)) return null;
  n = Number(n);
  const sign = n < 0 ? MINUS : '', a = Math.abs(n);
  if (!opts.exact) {
    if (a >= 1e7) return sign + RUPEE + (a / 1e7).toFixed(2) + ' Cr';
    if (a >= 1e5) return sign + RUPEE + (a / 1e5).toFixed(2) + ' L';
  }
  return sign + RUPEE + inGroup(Math.round(a));
}

/**
 * Money in full rupees, never abbreviated: `73500000` → `₹7,35,00,000`.
 * Use it in tooltips, drill-downs and derivation terms, where the exact figure
 * is the point. Returns `null` for null/undefined/''/NaN, like {@link money}.
 * @param {number|string|null|undefined} n rupees
 * @returns {string|null}
 */
export function moneyFull(n) {
  return money(n, { exact: true });
}

/**
 * Indian-grouped integer for counts and quantities: `12345` → `12,345`.
 * Unknown values render as `—` (a count has no rupee sign to lose).
 * @param {number|string|null|undefined} n
 * @returns {string}
 */
export function num(n) {
  if (n === null || n === undefined || n === '' || isNaN(n)) return '—';
  return inGroup(Math.round(Number(n)));
}

/**
 * A share, one decimal place: `pct(30, 120)` → `'25.0%'`.
 * `part` and `whole` — **not** a ready-made fraction. A zero, missing or
 * unusable denominator gives `—` rather than a division by zero, and a missing
 * numerator gives `—` rather than a confident `0.0%`.
 * @param {number|string|null|undefined} n the part
 * @param {number|string|null|undefined} d the whole
 * @returns {string}
 */
export function pct(n, d) {
  if (n === null || n === undefined || n === '') return '—';
  return (!d || isNaN(n) || isNaN(d)) ? '—' : (100 * Number(n) / Number(d)).toFixed(1) + '%';
}

/**
 * "3 min ago" beats a timestamp on a board that refreshes itself — the reader
 * wants to know it is current, not to do arithmetic.
 * Buckets: `just now` (<90s), `N min ago` (<90m), `N h ago` (<48h), `N d ago`.
 * @param {string|number|Date} iso ISO 8601 string, epoch ms, or a Date
 * @returns {string} `'unknown'` when it will not parse
 */
export function ago(iso) {
  if (iso === null || iso === undefined || iso === '') return 'unknown';
  const t = (iso instanceof Date) ? iso.getTime()
          : (typeof iso === 'number') ? iso
          : Date.parse(iso);
  if (isNaN(t)) return 'unknown';
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 90) return 'just now';
  if (s < 5400) return Math.round(s / 60) + ' min ago';
  if (s < 172800) return Math.round(s / 3600) + ' h ago';
  return Math.round(s / 86400) + ' d ago';
}

/**
 * Escape a value for interpolation into HTML. Party names carry `&` and `'`
 * (`M/S. D'SOUZA & SONS`), so this is not optional.
 * Escapes `& < > " '`.
 * @param {*} s
 * @returns {string}
 */
export function esc(s) {
  return String(s === null || s === undefined ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/* ══════════════════════════════════════════════════════════════════════════
   Linking — the drill-down spine (CONTRACT §0.4)

   Every one of these returns a string, always. A missing key is simply left
   out of the query rather than producing `href="null"`; the target page then
   says what it could not find. Values are percent-encoded, so an href is safe
   to interpolate into a quoted attribute.
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * `{a:1, b:null}` → `'a=1'`.
 * @param {Object<string, *>} params
 * @returns {string}
 */
function qs(params) {
  const out = [];
  for (const k in params) {
    if (!Object.prototype.hasOwnProperty.call(params, k)) continue;
    const v = params[k];
    if (v === null || v === undefined || v === '') continue;
    out.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
  }
  return out.join('&');
}

/**
 * `page` + `?…`, dropping the `?` when there is nothing to pass.
 * @param {string} page
 * @param {Object<string, *>} params
 * @returns {string}
 */
function link(page, params) {
  const q = qs(params);
  return q ? page + '?' + q : page;
}

/**
 * Where a rendered figure goes when the reader asks "where did this come
 * from?" — the KPI's full derivation: formula, terms, exclusions, the SQL and
 * its caveats.
 * @param {string} kpiId e.g. `'ar-trade-open'`
 * @param {string} [co] defaults to the current company
 * @returns {string} `derivation.html?k=…&co=…`
 */
export function hrefDerivation(kpiId, co) {
  return link('derivation.html', { k: kpiId, co: co || company() });
}

/**
 * One customer or vendor: ledger position, raw→adjusted waterfall, buckets,
 * open documents.
 * @param {string} card CardCode, e.g. `'VENDA000483'`
 * @param {string} [co]
 * @returns {string} `party.html?co=…&card=…`
 */
export function hrefParty(card, co) {
  return link('party.html', { co: co || company(), card });
}

/**
 * One document — invoice, bill, GRPO, return, payment.
 * @param {string|number} objType SAP `ObjType` (13 A/R invoice, 18 A/P invoice,
 *   20 GRPO, 21 goods return, 16 A/R credit note, …)
 * @param {string|number} docEntry SAP `DocEntry` (**not** `DocNum`)
 * @param {string} [co]
 * @returns {string} `document.html?co=…&type=…&entry=…`
 */
export function hrefDocument(objType, docEntry, co) {
  return link('document.html', { co: co || company(), type: objType, entry: docEntry });
}

/**
 * The page that owns a section, with any filter/sort the caller wants applied.
 * Accepts a section id (`'vendor-ageing'`) or a page id (`'payables'`); a name
 * already ending in `.html` is used as-is. A section with no page of its own
 * (`factory-indirect`, `budget-heads`) falls back to its anchor on the board,
 * which never 404s.
 * @param {string} sectionId
 * @param {string} [co]
 * @param {Object<string, *>} [params] e.g. `{kind:'TRADE', sort:'ADJ_OPEN', dir:'desc'}`
 * @returns {string}
 */
export function hrefSection(sectionId, co, params) {
  const id = String(sectionId || '').trim();
  const all = Object.assign({ co: co || company() }, params || {});
  if (/\.html$/i.test(id)) return link(id, all);
  const page = SECTION_PAGE[id];
  if (page) return link(page, all);
  // A section with no hand-built page (budget-heads and factory-indirect arrived
  // on 2026-08-22, and the pipeline is section-agnostic so more will) goes to the
  // generic renderer, which shows the real rows and says plainly that it does not
  // know the section's traps. An index anchor would point at nothing.
  if (id) return link('section.html', Object.assign({ sec: id }, all));
  return link('index.html', all);
}

/**
 * One bank account: 12-month in/out/net, reco history, unreconciled ageing.
 * @param {string|number} acct the account key as the section reports it
 * @param {string} [co]
 * @returns {string} `bank-account.html?co=…&acct=…`
 */
export function hrefBank(acct, co) {
  return link('bank-account.html', { co: co || company(), acct });
}

/**
 * One GL / provision account: created vs reversed vs standing, ageing,
 * posting history.
 * @param {string|number} acct GL account code, e.g. `'2161007'`
 * @param {string} [co]
 * @returns {string} `gl-account.html?co=…&acct=…`
 */
export function hrefGL(acct, co) {
  return link('gl-account.html', { co: co || company(), acct });
}

/**
 * A caveat code → where its text lives. `C-00xx` are the global JIVO
 * corrections; section-local codes (`P-LAKHS`, `P-FIFO`) resolve on the same
 * page (CONTRACT §8).
 * @param {string} code
 * @returns {string} `methodology.html#C-0019`
 */
export function hrefCaveat(code) {
  return 'methodology.html#' + encodeURIComponent(String(code || '').trim());
}

/* ── the rendering half. One import point per page (CONTRACT §3). ────────── */
export * from './ui.js';
