/* JIVO Godown Board — company page (oil / mart / bev).
   The shell sets window.CO ('oil'|'mart'|'bev') and loads /assets/core.js first.
   Renders: breadcrumb hero, uncapped less/more boards, the full filterable
   table, godowns by class, and the shared notices footer. */
(function () {
'use strict';
const {inr, money, qty, SEV} = window.JG;
const CO = window.CO;
const CO_WORD = {oil: 'Oil', mart: 'Mart', bev: 'Beverages'};

/* ---- page-specific styles live here so the three shells stay identical ---- */
const st = document.createElement('style');
st.textContent = `
.crumbnav{margin-bottom:12px}
.crumb{display:inline-block;font-size:.85rem;font-weight:650;color:var(--brand);text-decoration:none;padding:4px 2px}
.crumb:hover{text-decoration:underline}
.hero{margin-top:14px;padding-top:14px;border-top:1px solid var(--line-soft)}
.hero .big{font-family:var(--disp);font-size:clamp(2rem,5.5vw,2.7rem);font-weight:600;color:var(--brand);font-variant-numeric:tabular-nums;letter-spacing:.01em;line-height:1.15}
.hero .sub{font-size:.85rem;color:var(--sage);margin-top:4px}
.hero .mini{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.tscroll.mid{max-height:60vh;overflow-y:auto}
.boards .board{min-width:0}
.toolbar select{max-width:100%}
`;
document.head.appendChild(st);

document.getElementById('co-word').textContent = CO_WORD[CO] || CO;
document.getElementById('notices-body').innerHTML = JG.noticesHTML();

/* ---- state ---- */
let D = null, items = [];
const whsName = {}, byGod = {};
let openGod = null;
const state = {q: '', st: new Set(), utype: 'all', variety: 'all', sort: {k: 'sev', dir: 1}, cls: 'physical'};

JG.fetchData().then(d => { D = d; boot(); }).catch(() => {
  document.getElementById('offline').hidden = false;
  document.querySelectorAll('.skel').forEach(e => e.remove());
});

function boot() {
  items = D.items.filter(i => i.co === CO);
  const c = D.companies.find(x => x.key === CO) ||
    {label: 'JIVO ' + (CO_WORD[CO] || CO), total_value: 0, physical_value: 0, unlisted_value: 0, total_items: 0, status_counts: {}};
  document.getElementById('co-word').textContent = (c.label || '').replace(/^JIVO\s*/, '') || CO_WORD[CO] || CO;

  /* hero */
  const clock = JG.fmtAsOf(D.as_of);
  const ce = document.getElementById('clock');
  ce.textContent = clock;
  ce.setAttribute('aria-label', 'Last updated ' + clock);
  document.getElementById('hero-val').textContent = money(c.total_value);
  document.getElementById('hero-sub').textContent =
    `Total book value · goods ${money(c.physical_value)} · ${inr.format(c.total_items)} items in stock`;
  if (c.tonnes) {
    const tl = document.createElement('div'); tl.className = 'sub';
    tl.textContent = JG.tonnes(c.tonnes) + ' of goods';
    document.getElementById('hero-sub').after(tl);
  }
  const chips = document.getElementById('hero-chips'); chips.textContent = '';
  for (const p of [['OUT', 'r'], ['LOW', 'a'], ['HIGH', 'b'], ['DEAD', 'd'], ['NORMAL', 'g']]) {
    const n = c.status_counts[p[0]] || 0; if (!n) continue;
    const s = document.createElement('span'); s.className = 'chip ' + p[1];
    s.textContent = `${inr.format(n)} ${p[0] === 'NORMAL' ? 'OK' : p[0]}`;
    chips.appendChild(s);
  }

  /* lookups */
  for (const g of D.godowns) whsName[g.co + '|' + g.code] = g.name;
  for (const it of items) for (const w of (it.whs || [])) {
    (byGod[w.w] || (byGod[w.w] = [])).push({it, q: w.q, v: w.v});
  }

  /* notices fill-ins (company-scoped) */
  document.getElementById('asof-note').textContent = 'This snapshot: ' + clock + '.';
  if (c.t_coverage_pct) {
    document.getElementById('t-cov').textContent =
      ` (items with a known size carry ${c.t_coverage_pct}% of this board's goods value)`;
  }
  if (c.unlisted_value) {
    document.getElementById('unlisted-note').textContent =
      `${money(c.unlisted_value)} of ${c.label}'s book value sits on zero-quantity cost-pool rows that list no item here.`;
  }
  const faVal = D.godowns.filter(g => g.co === CO && g.class === 'fixed-assets').reduce((s, g) => s + g.value, 0);
  if (faVal) {
    document.getElementById('fa-note').innerHTML =
      `<b>Fixed-assets godowns hold ${money(faVal)}</b> of ${c.label}'s book value — machinery and equipment tracked as inventory items. Included in the total above, excluded from the goods figure; see Godowns → Fixed assets.`;
  }

  renderBoards();
  initToolbar();
  renderFull();
  initClassTabs();
  renderGod();
}

const itemRow = (it, cols) => JG.itemRow(it, cols, whsName);

/* ---- less / more boards — uncapped, each scrolls in its own container ---- */
function renderBoards() {
  const less = items.filter(i => i.status === 'OUT' || i.status === 'LOW')
    .sort((a, b) => SEV[a.status] - SEV[b.status] || (b.out90 || 0) - (a.out90 || 0));
  const more = items.filter(i => i.status === 'HIGH' || i.status === 'DEAD')
    .sort((a, b) => SEV[a.status] - SEV[b.status] || b.value - a.value);
  const nOut = less.filter(i => i.status === 'OUT').length, nLow = less.length - nOut;
  const nHigh = more.filter(i => i.status === 'HIGH').length, nDead = more.length - nHigh;
  document.getElementById('less-n').textContent =
    `${inr.format(less.length)} items · ${inr.format(nOut)} out + ${inr.format(nLow)} low`;
  document.getElementById('more-n').textContent =
    `${inr.format(more.length)} items · ${inr.format(nHigh)} high + ${inr.format(nDead)} dead`;
  const lb = document.getElementById('less-body'); lb.textContent = '';
  const mb = document.getElementById('more-body'); mb.textContent = '';
  if (!less.length) { const r = document.createElement('tr'); r.className = 'allclear'; r.innerHTML = '<td colspan="6">All clear — nothing short</td>'; lb.appendChild(r); }
  if (!more.length) { const r = document.createElement('tr'); r.className = 'allclear'; r.innerHTML = '<td colspan="6">All clear — nothing piled up</td>'; mb.appendChild(r); }
  const lf = document.createDocumentFragment();
  less.forEach(it => lf.appendChild(itemRow(it, ['qty', 'cover', 'out90'])));
  lb.appendChild(lf);
  const mf = document.createDocumentFragment();
  more.forEach(it => mf.appendChild(itemRow(it, ['qty', 'cover', 'value'])));
  mb.appendChild(mf);
}

/* ---- everything in stock: toolbar + full table ---- */
function initToolbar() {
  const ut = document.getElementById('f-utype');
  for (const u of [...new Set(items.map(i => i.utype).filter(Boolean))].sort()) {
    const o = document.createElement('option'); o.value = u; o.textContent = u; ut.appendChild(o);
  }
  const va = document.getElementById('f-variety');
  for (const v of [...new Set(items.map(i => i.variety).filter(Boolean))].sort()) {
    const o = document.createElement('option'); o.value = v; o.textContent = v; va.appendChild(o);
  }
  document.getElementById('q').addEventListener('input', e => { state.q = e.target.value.trim().toLowerCase(); renderFull(); });
  ut.addEventListener('change', e => { state.utype = e.target.value; renderFull(); });
  va.addEventListener('change', e => { state.variety = e.target.value; renderFull(); });
  document.querySelectorAll('.tgl[data-st]').forEach(t => t.addEventListener('click', () => {
    const s = t.dataset.st;
    if (state.st.has(s)) state.st.delete(s); else state.st.add(s);
    t.setAttribute('aria-pressed', String(state.st.has(s)));
    renderFull();
  }));
  document.querySelectorAll('#full thead button').forEach(b => b.addEventListener('click', () => {
    const k = b.dataset.k;
    if (state.sort.k === k) state.sort.dir *= -1; else { state.sort.k = k; state.sort.dir = 1; }
    renderFull();
  }));
}
const KEYF = {
  name: i => i.name || '', onhand: i => i.onhand, value: i => i.value,
  cover: i => i.cover == null ? 1e9 : i.cover,
  vs: i => i.vs_normal_pct == null ? -1e9 : i.vs_normal_pct,
  sev: i => SEV[i.status],
};
function renderFull() {
  const {q, st, utype, variety, sort} = state;
  const rows = items.filter(i =>
    (!st.size || st.has(i.status)) &&
    (utype === 'all' || i.utype === utype) &&
    (variety === 'all' || i.variety === variety) &&
    (!q || ((i.name || '').toLowerCase().includes(q) || i.code.toLowerCase().includes(q)))
  );
  const f = KEYF[sort.k];
  rows.sort((a, b) => {
    const x = f(a), y = f(b);
    const r = (typeof x === 'string') ? x.localeCompare(y) : x - y;
    return (r || b.value - a.value || (b.out90 || 0) - (a.out90 || 0)) * sort.dir;
  });
  document.querySelectorAll('#full .arr').forEach(a => a.textContent = a.dataset.a === sort.k ? (sort.dir === 1 ? '▲' : '▼') : '');
  JG.closeSub();
  const body = document.getElementById('full-body'); body.textContent = '';
  const frag = document.createDocumentFragment();
  rows.forEach(it => frag.appendChild(itemRow(it, ['qty', 'cover', 'vs', 'value'])));
  if (!rows.length) { const r = document.createElement('tr'); r.className = 'allclear'; r.innerHTML = '<td colspan="7">No entries match — clear a filter</td>'; frag.appendChild(r); }
  body.appendChild(frag);
  document.getElementById('count').textContent = inr.format(rows.length) + ' rows';
}

/* ---- godowns by class, rows expand to the items lying there ---- */
const CLS_LABEL = {physical: 'Physical', 'fixed-assets': 'Fixed assets', 'in-transit': 'In transit',
  virtual: 'Virtual', wastage: 'Wastage', 'non-moving': 'Non-moving', 'other-media': 'Other', dropship: 'Dropship'};
function initClassTabs() {
  const mine = D.godowns.filter(g => g.co === CO);
  const present = [...new Set(mine.map(g => g.class))];
  const order = ['physical', 'fixed-assets', 'in-transit', 'virtual', 'non-moving', 'wastage', 'other-media', 'dropship']
    .filter(c => present.includes(c));
  if (order.length && !order.includes(state.cls)) state.cls = order[0];
  const tabs = document.getElementById('classtabs');
  for (const cls of order) {
    const val = mine.filter(g => g.class === cls).reduce((s, g) => s + g.value, 0);
    const b = document.createElement('button'); b.className = 'tgl'; b.dataset.cls = cls;
    b.setAttribute('aria-pressed', String(cls === state.cls));
    b.textContent = `${CLS_LABEL[cls] || cls} · ${money(val)}`;
    b.addEventListener('click', () => {
      state.cls = cls;
      tabs.querySelectorAll('.tgl').forEach(t => t.setAttribute('aria-pressed', String(t.dataset.cls === cls)));
      renderGod();
    });
    tabs.appendChild(b);
  }
}
function closeGodSub() {
  if (!openGod) return;
  openGod.sub.remove();
  openGod.tr.classList.remove('open');
  openGod.tr.setAttribute('aria-expanded', 'false');
  openGod = null;
}
function renderGod() {
  closeGodSub();
  const body = document.getElementById('god-body'); body.textContent = '';
  const note = document.getElementById('note-fa');
  note.hidden = state.cls !== 'fixed-assets';
  if (state.cls === 'fixed-assets') note.innerHTML = '<b>Not goods.</b> These godowns hold capitalised machinery, equipment and assets entered as inventory items in SAP. They inflate "stock value" but nothing here is sellable product.';
  const gs = D.godowns.filter(g => g.co === CO && g.class === state.cls).sort((a, b) => b.value - a.value);
  for (const g of gs) {
    const tr = document.createElement('tr'); tr.className = 'god';
    tr.innerHTML = '<td><div class="gnm"></div><div class="gcd"></div></td><td class="co"></td><td class="num"></td><td class="num"></td><td class="num" style="color:#7b8087" aria-hidden="true">▸</td>';
    tr.querySelector('.gnm').textContent = g.name || g.code;
    tr.querySelector('.gcd').textContent = g.code;
    tr.querySelector('.co').textContent = g.co.toUpperCase();
    tr.children[2].textContent = inr.format(g.items);
    tr.children[3].textContent = money(g.value);
    if (g.value < 0) tr.children[3].classList.add('neg');
    tr.tabIndex = 0; tr.setAttribute('role', 'button'); tr.setAttribute('aria-expanded', 'false');
    const open = () => toggleGodSub(tr, g);
    tr.addEventListener('click', open);
    tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
    body.appendChild(tr);
  }
  if (!gs.length) { const r = document.createElement('tr'); r.className = 'allclear'; r.innerHTML = '<td colspan="5">No godowns in this class</td>'; body.appendChild(r); }
}
function toggleGodSub(tr, g) {
  const wasOpen = tr.classList.contains('open');
  closeGodSub();
  if (wasOpen) return;
  const rows = (byGod[g.code] || []).filter(x => x.q > 0 || x.v !== 0).sort((a, b) => b.v - a.v);
  const sub = document.createElement('tr'); sub.className = 'sub';
  const td = document.createElement('td'); td.colSpan = 5;
  const chips = document.createElement('div'); chips.className = 'whschips';
  rows.slice(0, 40).forEach(x => {
    const c = document.createElement('span'); c.className = 'chip';
    const nm = document.createElement('span'); nm.textContent = x.it.name || x.it.code;
    const em = document.createElement('em'); em.textContent = ` — ${qty(x.q)} pcs`;
    c.appendChild(nm); c.appendChild(em); c.append(` · ${money(x.v)}`);
    chips.appendChild(c);
  });
  if (rows.length > 40) { const c = document.createElement('span'); c.className = 'chip'; c.textContent = `+ ${inr.format(rows.length - 40)} more items`; chips.appendChild(c); }
  if (!rows.length) { const c = document.createElement('span'); c.className = 'chip'; c.textContent = 'No item rows (value-only cost pools)'; chips.appendChild(c); }
  td.appendChild(chips); sub.appendChild(td);
  tr.after(sub); tr.classList.add('open'); tr.setAttribute('aria-expanded', 'true');
  openGod = {tr, sub};
}
})();
