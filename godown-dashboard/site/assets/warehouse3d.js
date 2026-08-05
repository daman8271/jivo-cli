/* JIVO Godown Board — per-site godown page + 3D warehouse scene.
   Requires: /assets/core.js (window.JG) and /assets/three.min.js (window.THREE, r160 UMD).
   The page sets window.SITE ('bhakharpur' | 'gupta' | 'mayapuri') and calls JGW.boot().
   Data: /data.json — membership of an item at a site = its whs[] entries whose
   "co|w" is in sites[].codes, EXCLUDING fixed-assets-class warehouses (machinery
   is acknowledged in the hero sub-line, never listed as goods).
   All quantities are PIECES, never cartons. Money is INR (Cr/L). */
(function () {
'use strict';

var $ = function (s, r) { return (r || document).querySelector(s); };

/* 3D palette (brand statuses; NORMAL shares OK green) */
var C3D  = {NORMAL: 0x0A7D3F, LOW: 0xFFB400, HIGH: 0x1D5F8A, DEAD: 0xB9B4A8, OUT: 0xB3261E};
var WORD = {NORMAL: 'selling normally', LOW: 'running low', HIGH: 'more than demand',
            DEAD: 'not moving', OUT: 'out everywhere'};

function h32(str) { /* FNV-1a — deterministic per-stack jitter */
  var h = 2166136261;
  for (var i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

/* ============================ page ============================ */

function fail(msg) {
  var o = $('#offline');
  if (o) { o.hidden = false; o.textContent = msg; }
  var b;
  ['#lowB', '#hiB', '#allB'].forEach(function (id) {
    b = $(id); if (b) b.innerHTML = '';
  });
}

function boot() {
  if (!window.JG || !window.SITE) { fail('Scripts failed to load — refresh the page.'); return; }
  window.JG.fetchData().then(build).catch(function () {
    fail('Could not load live data — check the connection and refresh.');
  });
}

function build(data) {
  var J = window.JG;
  var site = null, i;
  for (i = 0; i < data.sites.length; i++) if (data.sites[i].name === window.SITE) site = data.sites[i];
  if (!site) { fail('Site "' + window.SITE + '" not found in data.json.'); return; }

  /* warehouse class + name lookups */
  var cls = {}, wname = {};
  data.godowns.forEach(function (g) {
    cls[g.co + '|' + g.code] = g.class;
    wname[g.co + '|' + g.code] = g.name;
  });
  var goodsCodes = {};
  site.codes.forEach(function (c) { if (cls[c] !== 'fixed-assets') goodsCodes[c] = true; });

  /* rows: every item with goods stock (or a value pool) at this site */
  var rows = [];
  data.items.forEach(function (it) {
    var q = 0, v = 0, w, k, j;
    var whs = it.whs || [];
    for (j = 0; j < whs.length; j++) {
      w = whs[j]; k = it.co + '|' + w.w;
      if (goodsCodes[k]) { q += w.q; v += w.v; }
    }
    if (q !== 0 || Math.abs(v) > 0.5) rows.push({it: it, q: q, v: v});
  });
  rows.sort(function (a, b) { return b.v - a.v; });

  /* ---- hero ---- */
  var allGoods = 0;
  data.sites.forEach(function (s) { allGoods += (s.goods_value || 0); });
  var nStock = 0;
  rows.forEach(function (r) { if (r.q > 0) nStock++; });

  $('#hval').textContent = J.money(site.goods_value);
  $('#hsub').textContent = J.qty(nStock) + ' items in stock here · goods only' +
    (site.tonnes ? ' · ' + J.tonnes(site.tonnes) + ' lying here' : '');
  var mach = $('#hmach');
  if (site.fa_value > 1000) {
    mach.hidden = false;
    mach.textContent = 'plus ' + J.money(site.fa_value) + ' machinery booked as stock';
  }
  var pct = allGoods > 0 ? site.goods_value / allGoods * 100 : 0;
  $('#hbar').style.width = Math.max(1.5, Math.min(100, pct)) + '%';
  $('#hshare').textContent = pct.toFixed(1) + '% of all JIVO goods value';
  $('#hasof').textContent = 'As of ' + J.fmtAsOf(data.as_of) + ' · from SAP';

  /* ---- 3D groups: by variety, fall back to item group ---- */
  var gm = {}, order = [];
  rows.forEach(function (r) {
    var name = r.it.variety || r.it.grp || 'OTHER';
    var e = gm[name];
    if (!e) { e = gm[name] = {name: name, v: 0, q: 0, st: {}}; order.push(e); }
    e.v += r.v; e.q += r.q;
    e.st[r.it.status] = (e.st[r.it.status] || 0) + Math.abs(r.v);
  });
  var groups = order.filter(function (g) { return g.v > 0; })
    .sort(function (a, b) { return b.v - a.v; }).slice(0, 24)
    .map(function (g) {
      var best = 'NORMAL', bw = -1, s;
      for (s in g.st) if (g.st[s] > bw) { bw = g.st[s]; best = s; }
      return {name: g.name, v: g.v, q: g.q, status: best};
    });
  init3D($('#stage'), groups);

  /* ---- less than normal here ---- */
  var low = rows.filter(function (r) { return r.it.status === 'LOW' && r.q > 0; });
  var lowB = $('#lowB'); lowB.innerHTML = '';
  if (!low.length) {
    lowB.innerHTML = '<tr class="allclear"><td colspan="6">All clear — nothing short at this godown.</td></tr>';
  } else {
    var lf = document.createDocumentFragment();
    low.forEach(function (r) { lf.appendChild(rowEl(r, ['q', 'v', 'out90'])); });
    lowB.appendChild(lf);
  }
  $('#lowN').textContent = low.length ? low.length + ' items' : '';
  var outN = 0;
  data.companies.forEach(function (c) { outN += (c.status_counts && c.status_counts.OUT) || 0; });
  var chip = $('#outchip');
  if (outN > 0) {
    chip.hidden = false;
    chip.textContent = outN + ' items OUT — no stock anywhere · see the main board';
  }

  /* ---- more than normal here ---- */
  var hi = rows.filter(function (r) {
    return (r.it.status === 'HIGH' || r.it.status === 'DEAD') && (r.q > 0 || r.v > 0);
  });
  var hiB = $('#hiB'); hiB.innerHTML = '';
  if (!hi.length) {
    hiB.innerHTML = '<tr class="allclear"><td colspan="5">Nothing over normal at this godown.</td></tr>';
  } else {
    var hf = document.createDocumentFragment();
    hi.forEach(function (r) { hf.appendChild(rowEl(r, ['q', 'v'])); });
    hiB.appendChild(hf);
  }
  $('#hiN').textContent = hi.length ? hi.length + ' items' : '';

  /* ---- everything lying here: search + company toggles + sort ---- */
  var state = {q: '', co: {oil: true, mart: true, bev: true}, sort: 'v', dir: -1};
  var allB = $('#allB'), tcount = $('#tcount');

  function renderAll() {
    var needle = state.q.trim().toUpperCase();
    var list = rows.filter(function (r) {
      if (!state.co[r.it.co]) return false;
      if (!needle) return true;
      return ((r.it.name || '') + ' ' + r.it.code + ' ' + (r.it.grp || '') + ' ' +
              (r.it.variety || '')).toUpperCase().indexOf(needle) !== -1;
    });
    list.sort(function (a, b) { return state.dir * ((a[state.sort] || 0) - (b[state.sort] || 0)); });
    var tot = 0;
    list.forEach(function (r) { tot += r.v; });
    allB.innerHTML = '';
    if (!list.length) {
      allB.innerHTML = '<tr class="allclear"><td colspan="5">Nothing matches.</td></tr>';
    } else {
      var f = document.createDocumentFragment();
      list.forEach(function (r) { f.appendChild(rowEl(r, ['q', 'v'])); });
      allB.appendChild(f);
    }
    tcount.textContent = J.qty(list.length) + ' items · ' + J.money(tot) + ' here';
    var aq = $('#arrq'), av = $('#arrv');
    if (aq) aq.textContent = state.sort === 'q' ? (state.dir < 0 ? '▾' : '▴') : '';
    if (av) av.textContent = state.sort === 'v' ? (state.dir < 0 ? '▾' : '▴') : '';
  }

  var deb = 0;
  $('#q').addEventListener('input', function (e) {
    clearTimeout(deb);
    deb = setTimeout(function () { state.q = e.target.value; renderAll(); }, 120);
  });
  document.querySelectorAll('.tgl[data-co]').forEach(function (b) {
    b.addEventListener('click', function () {
      var co = b.getAttribute('data-co');
      state.co[co] = !state.co[co];
      b.setAttribute('aria-pressed', String(state.co[co]));
      renderAll();
    });
  });
  document.querySelectorAll('th button[data-s]').forEach(function (b) {
    b.addEventListener('click', function () {
      var s = b.getAttribute('data-s');
      if (state.sort === s) state.dir = -state.dir; else { state.sort = s; state.dir = -1; }
      renderAll();
    });
  });
  renderAll();

  /* ---- notices footer ---- */
  var noticesEl = $('#notices');
  if (noticesEl) {
    noticesEl.innerHTML = J.noticesHTML();
    var asof = $('#asof-note');
    if (asof) asof.textContent = 'This page: as of ' + J.fmtAsOf(data.as_of) + '.';
    var tcov = $('#t-cov');
    if (tcov && site.t_coverage_pct) {
      tcov.textContent = ' (items with a known size carry ' +
        site.t_coverage_pct + '% of the goods value at this site)';
    }
    var fa = $('#fa-note');
    if (fa && site.fa_value > 1000) {
      fa.innerHTML = '<b>Machinery here:</b> this site also holds ' +
        '<b>' + J.money(site.fa_value) + '</b> of plant &amp; machinery booked in ' +
        '"Fixed Assets" stock warehouses. It is real value on the ground but not saleable goods, ' +
        'so it is kept out of every list and the 3D view above.';
    }
  }

  /* row builder — qty/value are AT THIS SITE, status is the item's company-level status */
  function rowEl(r, cols) {
    var tr = document.createElement('tr');
    tr.className = 'itm ' + r.it.status;
    var tdI = document.createElement('td'); tdI.className = 'item';
    var nm = document.createElement('div'); nm.className = 'nm';
    nm.textContent = r.it.name || r.it.code;
    var cd = document.createElement('div'); cd.className = 'cd';
    cd.textContent = r.it.code + (r.it.variety ? ' · ' + r.it.variety : '');
    tdI.appendChild(nm); tdI.appendChild(cd); tr.appendChild(tdI);
    var tdC = document.createElement('td'); tdC.className = 'co';
    tdC.textContent = r.it.co.toUpperCase(); tr.appendChild(tdC);
    cols.forEach(function (c) {
      var td = document.createElement('td'); td.className = 'num';
      if (c === 'q') {
        /* tons-first from THIS SITE's quantity, never the company total */
        td.innerHTML = J.qtyCellHTML(r.q, r.it.kgpu);
        if (r.q < 0) td.classList.add('neg');
      } else if (c === 'v') {
        td.textContent = J.money(r.v);
        if (r.v < 0) td.classList.add('neg');
      } else if (c === 'out90') {
        td.innerHTML = r.it.out90 ? J.qtyCellHTML(r.it.out90, r.it.kgpu) : '—';
      }
      tr.appendChild(td);
    });
    var tdS = document.createElement('td');
    tdS.innerHTML = J.statusPill(r.it.status);
    tr.appendChild(tdS);
    return tr;
  }
}

/* ============================ 3D warehouse ============================ */

function init3D(stage, groups) {
  var canvas = stage ? stage.querySelector('canvas') : null;
  if (!canvas) return;
  if (!window.THREE || !groups.length) { fallbackSVG(stage, groups); return; }
  var THREE = window.THREE, renderer;
  try {
    renderer = new THREE.WebGLRenderer({canvas: canvas, antialias: true});
  } catch (e) { fallbackSVG(stage, groups); return; }

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  var scene = new THREE.Scene();
  scene.background = new THREE.Color(0xF5F4EF);
  scene.fog = new THREE.Fog(0xF5F4EF, 40, 95);
  var cam = new THREE.PerspectiveCamera(38, 1, 0.1, 220);

  /* floor + grid */
  var floor = new THREE.Mesh(
    new THREE.PlaneGeometry(200, 200),
    new THREE.MeshLambertMaterial({color: 0xEDEBE0})
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);
  var grid = new THREE.GridHelper(64, 32, 0xDDDACB, 0xE6E4D7);
  grid.position.y = 0.02;
  scene.add(grid);

  /* daylight */
  scene.add(new THREE.HemisphereLight(0xFFFFFF, 0xE8E4D2, 1.05));
  var sun = new THREE.DirectionalLight(0xFFF4E0, 2.1);
  sun.position.set(20, 30, 14);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  sun.shadow.camera.left = -26; sun.shadow.camera.right = 26;
  sun.shadow.camera.top = 26; sun.shadow.camera.bottom = -26;
  sun.shadow.camera.near = 5; sun.shadow.camera.far = 80;
  sun.shadow.bias = -0.0004;
  scene.add(sun);

  /* open low-poly shell: slender green posts, top beams, gable rafters, ridge */
  var HW = 15.4, HD = 8.6, PH = 7.2, RIDGE = 8.6;
  var green = new THREE.MeshLambertMaterial({color: 0x0A7D3F});
  var greenSoft = new THREE.MeshLambertMaterial({color: 0x2E6B47});
  var postGeo = new THREE.BoxGeometry(0.24, PH, 0.24);
  var px, side, post;
  for (px = -HW; px <= HW + 0.01; px += HW / 3) {
    for (side = -1; side <= 1; side += 2) {
      post = new THREE.Mesh(postGeo, green);
      post.position.set(px, PH / 2, side * HD);
      post.castShadow = true;
      scene.add(post);
    }
  }
  var beamGeo = new THREE.BoxGeometry(HW * 2 + 0.6, 0.22, 0.28);
  for (side = -1; side <= 1; side += 2) {
    var beam = new THREE.Mesh(beamGeo, green);
    beam.position.set(0, PH, side * HD);
    beam.castShadow = true;
    scene.add(beam);
  }
  var ridge = new THREE.Mesh(new THREE.BoxGeometry(HW * 2 + 0.6, 0.26, 0.26), green);
  ridge.position.set(0, RIDGE, 0);
  ridge.castShadow = true;
  scene.add(ridge);
  var rl = Math.sqrt(HD * HD + (RIDGE - PH) * (RIDGE - PH));
  var rafterGeo = new THREE.BoxGeometry(0.16, 0.16, rl);
  var tilt = Math.atan2(RIDGE - PH, HD);
  for (px = -HW; px <= HW + 0.01; px += HW / 3) {
    for (side = -1; side <= 1; side += 2) {
      var raf = new THREE.Mesh(rafterGeo, greenSoft);
      raf.position.set(px, (PH + RIDGE) / 2 + 0.08, side * HD / 2);
      raf.rotation.x = side * tilt;
      scene.add(raf);
    }
  }

  /* JIVO sign on the back beam — canvas texture, no external asset */
  var sc = document.createElement('canvas'); sc.width = 512; sc.height = 144;
  var sx = sc.getContext('2d');
  if (sx) {
    sx.fillStyle = '#0A7D3F';
    sx.beginPath();
    if (sx.roundRect) sx.roundRect(4, 4, 504, 136, 26); else sx.rect(4, 4, 504, 136);
    sx.fill();
    sx.fillStyle = '#FFFFFF';
    sx.font = '600 92px system-ui, sans-serif';
    sx.textAlign = 'center'; sx.textBaseline = 'middle';
    sx.fillText('JIVO', 256, 78);
    var tex = new THREE.CanvasTexture(sc);
    tex.colorSpace = THREE.SRGBColorSpace;
    var sign = new THREE.Mesh(
      new THREE.PlaneGeometry(5.6, 1.58),
      new THREE.MeshBasicMaterial({map: tex, transparent: true})
    );
    sign.position.set(0, PH - 1.25, -HD + 0.18);
    scene.add(sign);
  }

  /* ---- pallet stacks: one per group, height ~ sqrt(value) ---- */
  var stacks = new THREE.Group();
  scene.add(stacks);
  var n = groups.length;
  var cols = Math.min(6, Math.max(2, Math.ceil(Math.sqrt(n * 1.7))));
  var rowsN = Math.ceil(n / cols);
  var SX = 4.5, SZ = 3.9;
  /* positions sorted centre-out so the tallest stacks sit in the middle */
  var pos = [], r, c;
  for (r = 0; r < rowsN; r++) for (c = 0; c < cols; c++) {
    var x = (c - (cols - 1) / 2) * SX;
    var z = (r - (rowsN - 1) / 2) * SZ;
    pos.push({x: x, z: z, d: x * x * 0.55 + z * z});
  }
  pos.sort(function (a, b) { return a.d - b.d; });

  var vmax = groups[0].v;
  var palletMat = new THREE.MeshLambertMaterial({color: 0xCDBB92});
  var deckGeo = new THREE.BoxGeometry(2.42, 0.13, 2.18);
  var footGeo = new THREE.BoxGeometry(2.42, 0.15, 0.3);
  var boxGeo = new THREE.BoxGeometry(1.04, 0.6, 0.92);
  var LAYER = 0.64, TOPY = 0.28;
  var pickables = [];

  groups.forEach(function (g, gi) {
    var p = pos[gi];
    var seed = h32(g.name);
    var stack = new THREE.Group();
    stack.position.set(p.x + ((seed % 41) / 40 - 0.5) * 0.5,
                       0,
                       p.z + ((seed % 29) / 28 - 0.5) * 0.4);
    stack.rotation.y = ((seed % 17) / 16 - 0.5) * 0.14;

    var base = new THREE.Color(C3D[g.status] || C3D.NORMAL);
    var matA = new THREE.MeshLambertMaterial({color: base.clone()});
    var matB = new THREE.MeshLambertMaterial({color: base.clone().multiplyScalar(0.9)});

    var deck = new THREE.Mesh(deckGeo, palletMat);
    deck.position.y = 0.215; deck.castShadow = true;
    stack.add(deck);
    for (var f = -1; f <= 1; f++) {
      var foot = new THREE.Mesh(footGeo, palletMat);
      foot.position.set(0, 0.075, f * 0.9);
      stack.add(foot);
    }

    var frac = Math.sqrt(g.v / vmax);
    var layers = Math.max(1, Math.round(6 * frac));
    var l, bxi, bzi, m, bx;
    for (l = 0; l < layers; l++) {
      var isTop = (l === layers - 1) && layers > 2;
      var count = isTop ? 1 + (seed % 3) : 4; /* partial top layer for a natural look */
      var placed = 0;
      for (bxi = -1; bxi <= 1 && placed < count; bxi += 2) {
        for (bzi = -1; bzi <= 1 && placed < count; bzi += 2) {
          m = ((l + (bxi + 1) / 2 + (bzi + 1) / 2) % 2) ? matB : matA;
          bx = new THREE.Mesh(boxGeo, m);
          bx.position.set(bxi * 0.58, TOPY + 0.31 + l * LAYER, bzi * 0.52);
          bx.rotation.y = (((seed >> (l + placed)) % 9) / 8 - 0.5) * 0.1;
          bx.castShadow = true;
          bx.receiveShadow = true;
          stack.add(bx);
          placed++;
        }
      }
    }
    stack.userData = {i: gi, matA: matA, matB: matB,
                      baseA: matA.color.clone(), baseB: matB.color.clone()};
    stacks.add(stack);
    pickables.push(stack);
  });

  /* ---- camera orbit + interaction ---- */
  var tgt = new THREE.Vector3(0, 1.9, 0);
  var radius = Math.max(19, cols * SX * 1.05 + 4);
  var theta = -0.65, phi = 1.08, vel = 0, idle = 99;
  var reduced = false;
  try { reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e2) {}
  var AUTO = reduced ? 0 : 0.07;

  function place() {
    var sp = Math.sin(phi);
    cam.position.set(tgt.x + radius * sp * Math.cos(theta),
                     tgt.y + radius * Math.cos(phi),
                     tgt.z + radius * sp * Math.sin(theta));
    cam.lookAt(tgt);
  }

  var tip = stage.querySelector('.w3dtip');
  var ray = new THREE.Raycaster();
  var ndc = new THREE.Vector2();
  var hovered = -1, pending = null;

  function stackOf(obj) {
    while (obj && obj.parent !== stacks) obj = obj.parent;
    return obj;
  }
  function setHover(idx, cx, cy) {
    if (idx === hovered && idx !== -1) { moveTip(cx, cy); return; }
    if (hovered !== -1) {
      var old = pickables[hovered].userData;
      old.matA.color.copy(old.baseA);
      old.matB.color.copy(old.baseB);
    }
    hovered = idx;
    if (idx === -1) { if (tip) tip.style.display = 'none'; canvas.style.cursor = 'grab'; return; }
    var ud = pickables[idx].userData;
    ud.matA.color.copy(ud.baseA).multiplyScalar(1.22);
    ud.matB.color.copy(ud.baseB).multiplyScalar(1.22);
    canvas.style.cursor = 'pointer';
    var g = groups[idx];
    if (tip && window.JG) {
      tip.innerHTML = '<b></b>' + window.JG.money(g.v) + ' · ' + window.JG.qty(g.q) +
        ' pcs<br><span class="tw">' + (WORD[g.status] || g.status) + '</span> ' +
        window.JG.statusPill(g.status);
      tip.querySelector('b').textContent = g.name;
      tip.style.display = 'block';
      moveTip(cx, cy);
    }
  }
  function moveTip(cx, cy) {
    if (!tip || tip.style.display === 'none') return;
    var rct = stage.getBoundingClientRect();
    var x = cx - rct.left + 16, y = cy - rct.top + 12;
    x = Math.min(x, rct.width - tip.offsetWidth - 8);
    y = Math.min(y, rct.height - tip.offsetHeight - 8);
    tip.style.left = Math.max(4, x) + 'px';
    tip.style.top = Math.max(4, y) + 'px';
  }
  function raycast() {
    if (!pending) return;
    var p = pending; pending = null;
    var rct = canvas.getBoundingClientRect();
    if (!rct.width || !rct.height) return;
    ndc.x = ((p.x - rct.left) / rct.width) * 2 - 1;
    ndc.y = -((p.y - rct.top) / rct.height) * 2 + 1;
    ray.setFromCamera(ndc, cam);
    var hits = ray.intersectObjects(pickables, true);
    var st = hits.length ? stackOf(hits[0].object) : null;
    setHover(st ? st.userData.i : -1, p.x, p.y);
  }

  var dragging = false, moved = 0, lx = 0, ly = 0;
  canvas.addEventListener('pointerdown', function (e) {
    dragging = true; moved = 0; lx = e.clientX; ly = e.clientY; idle = 0; vel = 0;
    try { canvas.setPointerCapture(e.pointerId); } catch (e3) {}
  });
  canvas.addEventListener('pointermove', function (e) {
    if (dragging) {
      var dx = e.clientX - lx, dy = e.clientY - ly;
      moved += Math.abs(dx) + Math.abs(dy);
      lx = e.clientX; ly = e.clientY;
      theta += dx * 0.006;
      phi = Math.min(1.35, Math.max(0.55, phi - dy * 0.004));
      vel = dx * 0.006;
      idle = 0;
    } else {
      pending = {x: e.clientX, y: e.clientY};
    }
  });
  function endDrag() { dragging = false; }
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', endDrag);
  canvas.addEventListener('pointerleave', function () { if (!dragging) { pending = null; setHover(-1, 0, 0); } });
  canvas.addEventListener('click', function (e) {
    if (moved > 8) return; /* it was a drag */
    pending = {x: e.clientX, y: e.clientY};
    raycast();
    idle = 0;
  });

  /* size, visibility, loop */
  function size() {
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (w && h) {
      renderer.setSize(w, h, false);
      cam.aspect = w / h;
      cam.updateProjectionMatrix();
    }
  }
  if (window.ResizeObserver) new ResizeObserver(size).observe(canvas);
  window.addEventListener('resize', size);
  size();

  var visible = true, raf = 0, last = 0;
  function tick(t) {
    raf = 0;
    if (!visible || document.hidden) return;
    var dt = Math.min((t - last) / 1000, 0.05); last = t;
    idle += dt;
    if (!dragging) {
      if (Math.abs(vel) > 0.0004) { theta += vel; vel *= 0.93; } /* inertia */
      else if (idle > 4 && hovered === -1) theta += AUTO * dt;   /* slow auto-orbit */
    }
    place();
    raycast();
    renderer.render(scene, cam);
    raf = requestAnimationFrame(tick);
  }
  function play() {
    if (!raf) { last = performance.now(); raf = requestAnimationFrame(tick); }
  }
  if (window.IntersectionObserver) {
    new IntersectionObserver(function (en) {
      visible = en[0].isIntersecting;
      if (visible) play();
    }, {threshold: 0.02}).observe(canvas);
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) play(); });
  place();
  play();
}

/* WebGL unavailable → static branded SVG, page fully usable */
function fallbackSVG(stage, groups) {
  if (!stage) return;
  var J = window.JG;
  var W = 800, H = 340, base = 300;
  var g = groups.slice(0, 16);
  var vmax = g.length ? g[0].v : 1;
  var bw = 34, gap = (W - 80) / Math.max(g.length, 1);
  var bars = '';
  g.forEach(function (e, i) {
    var h = Math.max(16, Math.round(190 * Math.sqrt(e.v / vmax)));
    var x = 46 + i * gap + (gap - bw) / 2;
    var col = '#' + ('00000' + (C3D[e.status] || C3D.NORMAL).toString(16)).slice(-6);
    bars += '<g><title>' + String(e.name).replace(/[<>&"]/g, ' ') + ' — ' +
      (J ? J.money(e.v) : e.v) + '</title>' +
      '<rect x="' + x + '" y="' + (base - h) + '" width="' + bw + '" height="' + h +
      '" rx="4" fill="' + col + '"/>' +
      '<rect x="' + (x - 3) + '" y="' + (base - 4) + '" width="' + (bw + 6) +
      '" height="6" rx="2" fill="#CDBB92"/></g>';
  });
  var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" ' +
    'aria-label="Stacks of goods at this godown, one bar per product group" ' +
    'style="display:block;width:100%;height:auto;background:#F5F4EF;border-radius:12px">' +
    '<line x1="20" y1="' + base + '" x2="' + (W - 20) + '" y2="' + base +
    '" stroke="#E4E2D6" stroke-width="2"/>' +
    '<path d="M30 70 L' + (W / 2) + ' 26 L' + (W - 30) + ' 70" fill="none" stroke="#0A7D3F" stroke-width="5" stroke-linecap="round"/>' +
    '<line x1="30" y1="70" x2="30" y2="' + base + '" stroke="#0A7D3F" stroke-width="5"/>' +
    '<line x1="' + (W - 30) + '" y1="70" x2="' + (W - 30) + '" y2="' + base + '" stroke="#0A7D3F" stroke-width="5"/>' +
    bars +
    '<text x="' + (W / 2) + '" y="' + (H - 12) + '" text-anchor="middle" ' +
    'fill="#8B9184" font-family="system-ui" font-size="13">3D view needs WebGL — showing the same stacks flat. Taller = more value.</text>' +
    '</svg>';
  stage.innerHTML = svg;
}

window.JGW = {boot: boot};
})();
