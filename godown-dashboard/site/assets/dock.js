/* JIVO Godown Board — glass dock navigation, injected on every page.
   Vanilla recreation of the Apple-style dock (React/framer-motion reference,
   user-supplied 2026-08-02): fixed bottom-centre glass pill, macOS-style
   magnification on hover, tooltip labels, active-page dot. No dependencies.
   Physics: per-frame target size from cursor distance ([-150,0,150]px →
   [44,76,44]px, linear) smoothed with a critically-damped lerp (0.2) in a
   rAF loop that only runs while the cursor is over the dock.
   Icons: lucide (ISC), stroke-based, embedded inline. */
(function () {
'use strict';
if (document.getElementById('jg-dock')) return;

var BASE = 44, MAX = 76, RANGE = 150, LERP = 0.2;

var ICONS = {
  home: '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  droplet: '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
  basket: '<path d="m15 11-1 9"/><path d="m19 11-4-7"/><path d="M2 11h20"/><path d="m3.5 11 1.6 7.4a2 2 0 0 0 2 1.6h9.8a2 2 0 0 0 2-1.6l1.7-7.4"/><path d="M4.5 15.5h15"/><path d="m5 11 4-7"/><path d="m9 11 1 9"/>',
  cup: '<path d="m6 8 1.75 12.28a2 2 0 0 0 2 1.72h4.54a2 2 0 0 0 2-1.72L18 8"/><path d="M5 8h14"/><path d="M7 15a6.47 6.47 0 0 1 5 0 6.47 6.47 0 0 0 5 0"/><path d="m12 8 1-6h2"/>',
  factory: '<path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M17 18h1"/><path d="M12 18h1"/><path d="M7 18h1"/>',
  warehouse: '<path d="M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3.26 6.5l8-3.2a2 2 0 0 1 1.48 0l8 3.2A2 2 0 0 1 22 8.35Z"/><path d="M6 22V12h12v10"/><path d="M6 17h12"/>',
  building: '<rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',
  clipboard: '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>'
};

var ITEMS = [
  {href: '/', label: 'Home', icon: 'home'},
  {href: '/oil/', label: 'Oil', icon: 'droplet'},
  {href: '/mart/', label: 'Mart', icon: 'basket'},
  {href: '/bev/', label: 'Beverages', icon: 'cup'},
  {href: '/godown/bhakharpur/', label: 'Bhakharpur', icon: 'factory'},
  {href: '/godown/gupta/', label: 'Gupta', icon: 'warehouse'},
  {href: '/godown/mayapuri/', label: 'Mayapuri', icon: 'building'},
  {href: '/#actions', label: 'Action points', icon: 'clipboard'}
];

function isActive(href) {
  var p = location.pathname.replace(/index\.html$/, '');
  if (href === '/') return p === '/';
  if (href.indexOf('#') !== -1) return false;
  return p === href || p.indexOf(href) === 0;
}

function init() {
  var reduced = false, canHover = false;
  try {
    reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  } catch (e) {}

  var dock = document.createElement('nav');
  dock.id = 'jg-dock';
  dock.className = 'dock';
  dock.setAttribute('role', 'toolbar');
  dock.setAttribute('aria-label', 'Board navigation');

  var els = [];
  ITEMS.forEach(function (it) {
    var a = document.createElement('a');
    a.className = 'dock-item' + (isActive(it.href) ? ' on' : '');
    a.href = it.href;
    a.setAttribute('aria-label', it.label);
    a.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      ICONS[it.icon] + '</svg><span class="dock-tip">' + it.label + '</span>';
    if (a.classList.contains('on')) a.setAttribute('aria-current', 'page');
    /* on the home page, the Action-points item scrolls instead of navigating */
    if (it.href === '/#actions') {
      a.addEventListener('click', function (e) {
        var t = document.getElementById('actions');
        if (t) {
          e.preventDefault();
          t.scrollIntoView({behavior: reduced ? 'auto' : 'smooth'});
        }
      });
    }
    dock.appendChild(a);
    els.push(a);
  });
  document.body.appendChild(dock);

  /* ---- magnification (pointer-fine, motion-ok devices only) ---- */
  if (!canHover || reduced) return;

  var mx = null, raf = 0;
  var sizes = ITEMS.map(function () { return BASE; });

  function tick() {
    raf = 0;
    /* all reads first (rects), then all writes (sizes) — no thrash */
    var rects = els.map(function (el) { return el.getBoundingClientRect(); });
    var settling = false, i, target, d, t;
    for (i = 0; i < els.length; i++) {
      target = BASE;
      if (mx != null) {
        d = Math.abs(mx - (rects[i].left + rects[i].width / 2));
        if (d < RANGE) { t = 1 - d / RANGE; target = BASE + (MAX - BASE) * t; }
      }
      sizes[i] += (target - sizes[i]) * LERP;
      if (Math.abs(target - sizes[i]) > 0.3) settling = true;
      else sizes[i] = target;
      els[i].style.width = sizes[i] + 'px';
      els[i].style.height = sizes[i] + 'px';
    }
    if (mx != null || settling) raf = requestAnimationFrame(tick);
  }
  function play() { if (!raf) raf = requestAnimationFrame(tick); }

  dock.addEventListener('mousemove', function (e) { mx = e.clientX; play(); });
  dock.addEventListener('mouseleave', function () { mx = null; play(); });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
})();
