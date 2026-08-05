/* JIVO Godown Board — shared core. Exposes window.JG.
   Load as a plain script BEFORE the page's inline script:
     <script src="/assets/core.js"></script>
   Data contract: fetchData() resolves site/data.json (see pipeline/build_data.py).
   Money is INR (Cr/L), quantities are PIECES ("pcs"), never cartons. */
(function () {
'use strict';

/* ============ formatting ============ */
const inr = new Intl.NumberFormat('en-IN', {maximumFractionDigits: 0});
function money(v) {
  const a = Math.abs(v), s = v < 0 ? '−' : '';
  if (a >= 1e7) return s + '₹' + (a / 1e7).toFixed(2) + ' Cr';
  if (a >= 1e5) return s + '₹' + (a / 1e5).toFixed(1) + ' L';
  return s + '₹' + inr.format(Math.round(a));
}
function qty(v) { const s = v < 0 ? '−' : ''; return s + inr.format(Math.round(Math.abs(v))); }
/* approximate weight: "≈ 1,234 t" (1dp under 10 t, else 0dp, en-IN grouping) */
function tonnes(v) {
  const a = Math.abs(v), s = v < 0 ? '−' : '';
  return '≈ ' + s + (a < 10 ? a.toFixed(1) : inr.format(Math.round(a))) + ' t';
}
/* row-level tons-first quantity cell (the owner's standing preference): when an
   item has a computable weight (kgpu, kg per piece), tonnage leads semibold and
   the pieces figure drops to the small second line. ≥100 t → 0dp, 10–100 → 1dp,
   <10 → 2dp; en-IN grouping, "≈" prefix. No kgpu (packaging, unparseable pack
   size) → exactly the plain pcs cell, never a guessed weight. */
function rowTonnes(t) {
  const a = Math.abs(t), s = t < 0 ? '−' : '';
  return '≈ ' + s + (a >= 100 ? inr.format(Math.round(a)) : a.toFixed(a >= 10 ? 1 : 2)) + ' t';
}
function qtyCellHTML(pcs, kgpu) {
  /* zero qty: "≈ 0.00 t" would lead with noise — keep the plain pcs cell */
  if (!kgpu || !pcs) return qty(pcs) + ' <span class="u">pcs</span>';
  return '<span class="tt">' + rowTonnes(pcs * kgpu / 1000) + '</span>' +
         '<span class="u pcs">' + qty(pcs) + ' pcs</span>';
}
function coverTxt(it) {
  if (it.status === 'DEAD' || it.status === 'OUT' || it.cover == null) return '—';
  const c = Math.max(it.cover, 0);
  return (c >= 100 ? inr.format(Math.round(c)) : c.toFixed(c < 10 ? 1 : 0)) + ' d';
}
function vsTxt(it) {
  const v = it.vs_normal_pct;
  /* "no base" = stocked for under half the 6-month window, so there is no
     baseline to call it high or low against (a genuinely new item, or an old
     one back after months at zero). Distinct from "—", which means no data. */
  if (v == null) return it.nobase ? 'no base' : '—';
  if (v > 999) return '>+999%';
  return (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(0) + '%';
}
const SEV = {OUT: 0, LOW: 1, HIGH: 2, DEAD: 3, NORMAL: 4};
const esc = s => s == null ? '' : String(s);

/* "02 Aug 2026 · 01:14 IST" from data.json's as_of */
const MON2 = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function fmtAsOf(as_of) {
  const m = String(as_of || '').match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (!m) return '—';
  return m[3] + ' ' + MON2[+m[2] - 1] + ' ' + m[1] + ' · ' + m[4] + ':' + m[5] + ' IST';
}

/* ============ data ============ */
function fetchData() {
  return fetch('/data.json', {cache: 'no-cache'}).then(r => {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  });
}

/* ============ status pill ============ */
function statusPill(status) {
  return '<span class="lamp ' + status + '">' + (status === 'NORMAL' ? 'OK' : status) + '</span>';
}

/* ============ item rows + sub-row toggle ============ */
/* One expanded row per page; clicking another row (or the same one) closes it. */
let openRow = null;
function closeSub() {
  if (!openRow) return;
  openRow.tr.classList.remove('open');
  openRow.btn.setAttribute('aria-expanded', 'false');
  openRow.sub.remove();
  openRow = null;
}
/* whsNameLookup: map keyed "co|whsCode" -> name, or a function (co, whsCode) -> name */
function whsLabel(lookup, co, w) {
  if (typeof lookup === 'function') return lookup(co, w) || w;
  if (lookup) return lookup[co + '|' + w] || w;
  return w;
}
function toggleSub(tr, btn, it, span, lookup) {
  const wasOpen = tr.classList.contains('open');
  closeSub();
  if (wasOpen) return;
  const sub = document.createElement('tr'); sub.className = 'sub';
  const td = document.createElement('td'); td.colSpan = span;
  const wrap = document.createElement('div'); wrap.className = 'subwrap';
  const chips = document.createElement('div'); chips.className = 'whschips';
  for (const w of (it.whs || [])) {
    const c = document.createElement('span'); c.className = 'chip';
    const nm = document.createElement('span'); nm.textContent = whsLabel(lookup, it.co, w.w);
    const em = document.createElement('em'); em.textContent = ' — ' + qty(w.q) + ' pcs';
    c.appendChild(nm); c.appendChild(em); c.append(' · ' + money(w.v));
    chips.appendChild(c);
  }
  const meta = document.createElement('div'); meta.className = 'meta';
  const bits = ['90-day out ' + qty(it.out90 || 0) + ' pcs'];
  if (it.t) bits.push(tonnes(it.t) + ' on hand');
  if (it.hist_avg != null) bits.push('6-mo avg level ' + qty(it.hist_avg) + ' pcs');
  if (it.committed) bits.push('Committed ' + qty(it.committed) + ' pcs');
  if (it.onorder) bits.push('On order ' + qty(it.onorder) + ' pcs');
  if (it.grp) bits.push(esc(it.grp));
  if (it.utype) bits.push(esc(it.utype));
  if (it.frozen) bits.push('Frozen item');
  meta.textContent = bits.join('  ·  ');
  wrap.appendChild(chips); wrap.appendChild(meta); td.appendChild(wrap); sub.appendChild(td);
  tr.after(sub); tr.classList.add('open'); btn.setAttribute('aria-expanded', 'true');
  openRow = {tr, btn, sub};
}
/* cols: array drawn from 'qty' | 'cover' | 'out90' | 'vs' | 'value' (order = column order).
   Rendered row = item cell + co cell + cols + status cell. */
function itemRow(it, cols, whsNameLookup) {
  const tr = document.createElement('tr');
  tr.className = 'itm ' + it.status;
  const tdI = document.createElement('td'); tdI.className = 'item';
  const btn = document.createElement('button'); btn.className = 'x'; btn.setAttribute('aria-expanded', 'false');
  btn.innerHTML = '<div class="nm"></div><div class="cd"></div>';
  btn.querySelector('.nm').textContent = esc(it.name) || it.code;
  btn.querySelector('.cd').textContent = it.code + (it.variety ? ' · ' + it.variety : '');
  tdI.appendChild(btn); tr.appendChild(tdI);
  const tdC = document.createElement('td'); tdC.className = 'co'; tdC.textContent = it.co.toUpperCase(); tr.appendChild(tdC);
  for (const col of cols) {
    const td = document.createElement('td'); td.className = 'num';
    if (col === 'qty') { td.innerHTML = qtyCellHTML(it.onhand, it.kgpu); if (it.onhand < 0) td.classList.add('neg'); }
    else if (col === 'cover') { td.textContent = coverTxt(it); }
    else if (col === 'out90') { td.innerHTML = it.out90 ? qtyCellHTML(it.out90, it.kgpu) : '—'; }
    else if (col === 'vs') {
      td.textContent = vsTxt(it);
      if (it.vs_normal_pct > 0 && (it.status === 'HIGH' || it.status === 'DEAD')) td.classList.add('pos-hi');
      if (it.vs_normal_pct < 0) td.classList.add('pos-lo');
    }
    else if (col === 'value') { td.textContent = money(it.value); if (it.value < 0) td.classList.add('neg'); }
    tr.appendChild(td);
  }
  const tdS = document.createElement('td');
  tdS.innerHTML = statusPill(it.status);
  tr.appendChild(tdS);

  btn.addEventListener('click', () => toggleSub(tr, btn, it, cols.length + 3, whsNameLookup));
  return tr;
}

/* ============ shared definitions footer ============ */
/* Inner HTML of the notices card — identical on every page. The three empty
   spans (#unlisted-note, #fa-note, #asof-note) are filled by the page if it
   has the numbers; they render as nothing otherwise. */
function noticesHTML() {
  return `    <h2>Notices — how to read this board</h2>
    <dl>
      <dt><span class="lamp OUT">OUT</span></dt><dd>No stock on hand, but the item moved in the last 90 days: it is selling and the shelf is empty.</dd>
      <dt><span class="lamp LOW">LOW</span></dt><dd>Under 15 days of cover at the item's own 90-day consumption rate.</dd>
      <dt><span class="lamp NORMAL">OK</span></dt><dd>15–60 days of cover. Normal.</dd>
      <dt><span class="lamp HIGH">HIGH</span></dt><dd>Over 60 days of cover, more stock than its demand justifies.</dd>
      <dt><span class="lamp DEAD">DEAD</span></dt><dd>Stock on hand, zero outbound movement in 90 days.</dd>
    </dl>
    <p><b>"Normal" is computed two ways</b>, because SAP's min/max stock levels are not maintained: (1) days of cover: today's stock ÷ the item's average daily outbound over the last 90 days (all movements excluding internal godown-to-godown transfers, net of sales returns); (2) VS NORMAL: today's stock against the item's own average level over the last six month-ends, reconstructed from SAP's movement ledger.</p>
    <p><b>Quantities are pieces (bottles), never cartons</b> (team correction C-0001). Money is INR: ₹1 Cr = 1,00,00,000 and ₹1 L = 1,00,000. Values are SAP's own per-warehouse StockValue, shown raw; per-warehouse cost pools drift by design, so negative value pools appear and are not hidden. <span id="unlisted-note"></span></p>
    <p><b>Tonnes are approximate.</b> Weight comes from each item's pack size, with litres converted at oil density 0.91 kg/L (water and beverages at 1.0 kg/L). Items without a computable pack size are left out<span id="t-cov"></span>. Packaging materials — labels, cartons, empty bottles, caps — deliberately carry no tonnage, so a label printed "250 ML" never counts as liquid.</p>
    <p><b>Expiry counts only what SAP knows.</b> Only batches with a recorded expiry date are counted; Mart records none at all, so real expired stock is likely higher than shown.</p>
    <p id="fa-note"></p>
    <p><b>Source:</b> live SAP B1 HANA (OITW · OINM · OITM · OWHS), three companies: JIVO Oil, JIVO Mart, JIVO Beverages. Refreshed daily by a deterministic read-only script; company totals verified against SAP to the rupee by independent re-derivation (76 checks). <span id="asof-note"></span></p>
    <p><b>Full method:</b> <a href="/#method">How "normal" is decided →</a></p>
`;
}

window.JG = {inr, money, qty, tonnes, qtyCellHTML, coverTxt, vsTxt, SEV, esc,
             fetchData, itemRow, closeSub, statusPill, noticesHTML, fmtAsOf};
})();

/* Vercel Web Analytics — counts visitors on all pages.
   "Except us": open any page with #team once on a device and that device is
   marked internal (localStorage) and never counted again. */
(function(){try{
  if(location.hash==='#team'){
    localStorage.setItem('jg-team','1');
    document.title='(team device — not counted) '+document.title;
  }
  if(!localStorage.getItem('jg-team')){
    var s=document.createElement('script');
    s.defer=true;s.src='/_vercel/insights/script.js';
    document.head.appendChild(s);
  }
}catch(e){}})();
