/* JIVO Kit — "The Blue Folder".
   Renders ONLY from GET /api/manifest: no hardcoded tool list, names, sizes,
   targets or auth labels (distribution/API.md, "The one rule"). GROUPS below is
   presentation order only — any component whose id is not listed still renders,
   under OTHER TOOLS. */
"use strict";

const GROUPS = [
  { head: "SAP & BOOKS", ids: ["sap-b1", "hana-sql"] },
  { head: "OPS SYSTEMS", ids: ["ecom-cli", "oms-cli", "factory-cli", "exim", "jsap-cli", "control-panel", "dsr-cli", "postsql"] },
  { head: "SELLER PORTALS", ids: ["portals"] },
  { head: "DESK TOOLS", ids: ["jivo-scraping-cli"] },
];

/* The four auth_modes of API.md §auth_mode, plus the two the UI must handle but
   never celebrate. Only baked-env may read as ready. */
const AUTH = {
  "baked-env": { label: "READY TO USE", tone: "ok" },
  "auth-login": { label: "ONE LOGIN NEEDED", tone: "warn" },
  "home-config-install": { label: "ONE FILE TO INSTALL", tone: "warn" },
  "external-token": { label: "LIMITED ACCESS", tone: "warn" },
  unconfigured: { label: "NO CREDENTIAL PLAN", tone: "bad" },
  preview: { label: "PREVIEW — NO SERVER", tone: "dim" },
};

const MAX_PAPERS = 7;
const JITTER = [-1.6, 1.1, -0.7, 1.8, -1.2, 0.6, -1.9];

const state = {
  manifest: null,
  target: "",
  selected: new Set(),
  building: false,
  preview: false, // true when the server API is absent and we render raw manifest.json
};

const tiles = new Map(); // id -> { el, input, top, notesBody, notesToggle }
const papers = new Map(); // id -> paper element

const $ = (id) => document.getElementById(id);
const gridEl = $("grid-groups");
const folderEl = $("folder");
const stackEl = $("stack");
const mouthEl = $("folder-mouth");
const countEl = $("folder-count");
const meterEl = $("meter");
const statusEl = $("status");
const extractBtn = $("extract");
const targetsEl = $("targets");
const globalWarnEl = $("global-warn");
const bannerEl = $("banner");

const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
const still = () => reduced.matches;

/* ---------- formatting ---------- */

function fmtSize(bytes) {
  if (!bytes || typeof bytes !== "number") return "—";
  const mb = bytes / (1024 * 1024);
  return mb >= 100 ? `${Math.round(mb)} MB` : `${mb.toFixed(1)} MB`;
}

/* est_size_bytes is a per-target map ({"mac-arm64": N, "windows": N}). */
function sizeFor(c) {
  const v = c.est_size_bytes;
  if (v && typeof v === "object") return v[state.target] || 0;
  return v || 0;
}

function fmtAge(seconds) {
  if (seconds == null) return "";
  if (seconds < 90) return "just now";
  if (seconds < 5400) return `${Math.round(seconds / 60)} min ago`;
  if (seconds < 129600) return `${Math.round(seconds / 3600)} hr ago`;
  return `${Math.round(seconds / 86400)} d ago`;
}

/* Targets are data, not constants: "mac-arm64" -> MAC, "windows" -> WINDOWS. */
function targetLabel(t) {
  return String(t).split("-")[0].toUpperCase();
}

function comp(id) {
  return state.manifest ? state.manifest.components.find((c) => c.id === id) : null;
}

function avail(c) {
  return (c.availability && c.availability[state.target]) || { ok: false, warnings: ["no availability data for this target"] };
}

/* ---------- load ---------- */

async function loadManifest() {
  try {
    const r = await fetch("/api/manifest");
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    state.manifest = await r.json();
  } catch {
    try {
      const r = await fetch("../manifest.json");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      state.manifest = adaptRaw(await r.json());
      state.preview = true;
    } catch {
      $("mb-right").textContent = "no server";
      banner("The builder is not running. Start it with ./jivodist in distribution/, then reload this page.", true);
      $("foot-note").textContent = "nothing can be built until the server is up";
      $("foot-note").classList.add("err");
      return;
    }
  }

  const targets = state.manifest.targets || [];
  if (!targets.includes(state.target)) state.target = targets[0] || "";

  if (state.preview) {
    banner("PREVIEW — read straight from distribution/manifest.json with no server: sizes, availability and EXTRACT are all unavailable until ./jivodist is running.", false);
    $("mb-right").textContent = "preview · no server";
  } else {
    const when = state.manifest.generated_at ? new Date(state.manifest.generated_at) : null;
    $("mb-right").textContent =
      `${state.manifest.components.length} tools · read ${when && !isNaN(when) ? when.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : "live"}`;
  }

  renderTargets();
  renderGrid();
  renderGlobalWarnings();
  renderMeter();
  loadPast();
}

/* Adapter: raw distribution/manifest.json → API shape, for serverless preview only.
   Auth modes are the server's truth (envbake.go) — preview does not guess them. */
function adaptRaw(raw) {
  return {
    targets: ["mac-arm64", "windows"],
    components: raw.components
      .filter((c) => c.distributable)
      .map((c) => {
        const availability = {};
        for (const t of ["mac-arm64", "windows"]) {
          let inc = 0, skip = 0;
          for (const tool of c.tools || []) {
            const hit = (tool.binaries || []).some((b) => b.os === t && b.exists !== false);
            if (hit) inc += 1; else skip += 1;
          }
          availability[t] = {
            ok: inc > 0,
            tools_included: inc,
            tools_skipped: skip,
            warnings: inc > 0 && skip > 0 ? [`${skip} tool(s) have no ${t} build — will be skipped`] : inc === 0 ? [`no ${t} binaries prebuilt`] : [],
          };
        }
        return {
          id: c.component,
          ui_name: c.ui_name,
          ui_description: c.ui_description,
          auth_mode: "preview",
          sensitive: false,
          availability,
          est_size_bytes: { "mac-arm64": 0, windows: 0 },
        };
      }),
  };
}

function banner(text, bad) {
  bannerEl.textContent = text;
  bannerEl.classList.toggle("bad", !!bad);
  bannerEl.hidden = false;
}

/* ---------- targets ---------- */

function renderTargets() {
  targetsEl.textContent = "";
  for (const t of state.manifest.targets || []) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "target";
    b.dataset.target = t;
    b.textContent = targetLabel(t);
    b.title = t;
    b.setAttribute("aria-pressed", String(t === state.target));
    b.addEventListener("click", () => switchTarget(t));
    targetsEl.appendChild(b);
  }
}

function switchTarget(t) {
  if (state.target === t || state.building) return;
  state.target = t;
  for (const b of targetsEl.querySelectorAll(".target"))
    b.setAttribute("aria-pressed", String(b.dataset.target === t));

  // A tool with no binary for this target can't stay in the folder: a
  // ticked-but-disabled tile would be stuck AND would still get POSTed.
  const doomed = [...state.selected].filter((id) => {
    const c = comp(id);
    return c && !avail(c).ok;
  });

  renderGrid(); // tiles are rebuilt for the new target before the chips fly back
  for (const id of doomed) setSelected(id, false);
  renderMeter();
}

/* ---------- the grid ---------- */

function renderGrid() {
  gridEl.textContent = "";
  tiles.clear();

  const seen = new Set();
  const groups = GROUPS.map((g) => ({ ...g, ids: g.ids.filter((id) => comp(id) && seen.add(id)) }));
  const rest = state.manifest.components.map((c) => c.id).filter((id) => !seen.has(id));
  if (rest.length) groups.push({ head: "OTHER TOOLS", ids: rest });

  for (const g of groups) {
    if (!g.ids.length) continue;
    const sec = document.createElement("section");
    sec.className = "group";
    const h = document.createElement("h2");
    h.className = "sec-head";
    h.textContent = g.head;
    const ul = document.createElement("ul");
    ul.className = "tiles";
    for (const id of g.ids) ul.appendChild(renderTile(comp(id)));
    sec.append(h, ul);
    gridEl.appendChild(sec);
  }
}

function renderTile(c) {
  const a = avail(c);
  const on = state.selected.has(c.id);

  const li = document.createElement("li");
  li.className = "tile" + (a.ok ? "" : " disabled") + (on ? " on" : "");

  const label = document.createElement("label");
  label.className = "tile-main";

  const top = document.createElement("div");
  top.className = "tile-top";

  const input = document.createElement("input");
  input.type = "checkbox";
  input.className = "tick";
  input.checked = on;
  input.disabled = !a.ok || state.preview;
  input.setAttribute("aria-label", `${c.ui_name} — ${c.id}`);
  input.addEventListener("change", () => setSelected(c.id, input.checked));

  const id = document.createElement("span");
  id.className = "tile-id";
  id.textContent = c.id;

  const size = document.createElement("span");
  size.className = "tile-size";
  size.textContent = fmtSize(sizeFor(c));

  top.append(input, id, size);

  const desc = document.createElement("p");
  desc.className = "tile-desc";
  desc.textContent = c.ui_description || c.ui_name || "";

  const foot = document.createElement("div");
  foot.className = "tile-foot";
  const mode = AUTH[c.auth_mode] || { label: String(c.auth_mode || "UNKNOWN").toUpperCase(), tone: "dim" };
  const badge = document.createElement("span");
  badge.className = "badge " + mode.tone;
  badge.textContent = mode.label;
  foot.appendChild(badge);

  if (a.ok && (a.tools_included || a.tools_skipped)) {
    const tools = document.createElement("span");
    tools.className = "badge tools";
    tools.textContent = a.tools_skipped
      ? `${a.tools_included} TOOL${a.tools_included === 1 ? "" : "S"} · ${a.tools_skipped} SKIPPED`
      : `${a.tools_included} TOOL${a.tools_included === 1 ? "" : "S"}`;
    foot.appendChild(tools);
  }
  if (c.sensitive) {
    const conf = document.createElement("span");
    conf.className = "badge conf";
    conf.textContent = "CONFIDENTIAL";
    foot.appendChild(conf);
  }

  label.append(top, desc, foot);
  li.appendChild(label);

  /* Notes live OUTSIDE the label so reading them never toggles the tick.
     Collapsed by default; open automatically when the tile is ticked, and
     always open (with no toggle) when the tile is unavailable — a disabled
     tile must state its reason in full, never in a tooltip. */
  const notes = collectNotes(c, a);
  if (notes.length) {
    const wrap = document.createElement("div");
    wrap.className = "notes";
    const body = document.createElement("div");
    body.className = "notes-body";
    for (const n of notes) body.appendChild(renderNote(n));

    let toggle = null;
    if (a.ok) {
      toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "notes-toggle";
      const caret = document.createElement("span");
      caret.className = "caret";
      caret.textContent = "›";
      const txt = document.createElement("span");
      txt.textContent = ` ${notes.length} note${notes.length === 1 ? "" : "s"}`;
      toggle.append(caret, txt);
      toggle.setAttribute("aria-expanded", String(on));
      body.hidden = !on;
      toggle.addEventListener("click", () => {
        const open = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!open));
        body.hidden = open;
      });
      wrap.appendChild(toggle);
    } else {
      body.hidden = false;
    }
    wrap.appendChild(body);
    li.appendChild(wrap);
    tiles.set(c.id, { el: li, input, top, notesBody: body, notesToggle: toggle });
  } else {
    tiles.set(c.id, { el: li, input, top, notesBody: null, notesToggle: null });
  }

  return li;
}

function collectNotes(c, a) {
  const notes = [];
  if (!a.ok) notes.push({ tone: "stop", glyph: "✕", text: `Not available for ${targetLabel(state.target)}.` });
  if (c.auth_note) notes.push({ tone: "", glyph: "⌘", text: c.auth_note });
  for (const w of a.warnings || []) notes.push({ tone: "warn", glyph: "⚠", text: w });
  if (c.sensitive) notes.push({ tone: "stop", glyph: "⚑", text: "Carries payroll-grade credentials — hand this zip to cleared staff only." });
  return notes;
}

function renderNote(n) {
  const d = document.createElement("div");
  d.className = "note" + (n.tone ? " " + n.tone : "");
  const g = document.createElement("span");
  g.className = "glyph";
  g.textContent = n.glyph;
  const t = document.createElement("span");
  t.textContent = n.text;
  d.append(g, t);
  return d;
}

/* ---------- selection: tick -> chip flies -> paper lands ---------- */

function setSelected(id, on) {
  if (on) state.selected.add(id);
  else state.selected.delete(id);

  const t = tiles.get(id);
  if (t) {
    t.el.classList.toggle("on", on);
    if (t.input.checked !== on) t.input.checked = on;
    if (t.notesToggle && t.notesBody) {
      // opening on tick; a manual close afterwards still wins
      t.notesToggle.setAttribute("aria-expanded", String(on));
      t.notesBody.hidden = !on;
    }
  }

  folderEl.classList.remove("extracted");
  renderMeter();

  const mouth = mouthEl.getBoundingClientRect();
  const tile = t ? t.top.getBoundingClientRect() : mouth;

  if (on) {
    flyChip(id, tile, mouth, false).then(() => {
      if (state.selected.has(id)) { addPaper(id); receive(); }
    });
  } else {
    removePaper(id);
    flyChip(id, mouth, tile, true);
  }
}

/* FLIP: measure both rects in viewport space, then animate transform only. */
function flyChip(text, from, to, reverse) {
  if (still() || !from || !to) return Promise.resolve();

  const chip = document.createElement("div");
  chip.className = "chip";
  chip.textContent = text;
  document.body.appendChild(chip);

  const r = chip.getBoundingClientRect();
  const fx = from.left + from.width / 2 - r.width / 2;
  const fy = from.top + from.height / 2 - r.height / 2;
  chip.style.left = `${fx}px`;
  chip.style.top = `${fy}px`;

  const dx = to.left + to.width / 2 - (fx + r.width / 2);
  const dy = to.top + to.height / 2 - (fy + r.height / 2);
  const lift = Math.min(60, Math.max(18, Math.abs(dx) * 0.12 + 18));

  const frames = reverse
    ? [
        { transform: "translate(0,0) scale(0.35)", opacity: 0 },
        { transform: `translate(${dx * 0.45}px, ${dy * 0.45 - lift}px) scale(0.95)`, opacity: 1, offset: 0.45 },
        { transform: `translate(${dx}px, ${dy}px) scale(0.9)`, opacity: 0 },
      ]
    : [
        { transform: "translate(0,0) scale(1)", opacity: 1 },
        { transform: `translate(${dx * 0.55}px, ${dy * 0.55 - lift}px) scale(0.88)`, opacity: 1, offset: 0.55 },
        { transform: `translate(${dx}px, ${dy}px) scale(0.28)`, opacity: 0 },
      ];

  const anim = chip.animate(frames, {
    duration: 450,
    easing: "cubic-bezier(0.22, 0.61, 0.36, 1)",
    fill: "forwards",
  });
  return anim.finished.catch(() => {}).then(() => chip.remove());
}

function receive() {
  if (still()) return;
  folderEl.classList.remove("receive");
  void folderEl.offsetWidth; // restart the keyframes for a rapid second tick
  folderEl.classList.add("receive");
}
folderEl.addEventListener("animationend", (e) => {
  if (e.animationName === "receive") folderEl.classList.remove("receive");
});

function addPaper(id) {
  if (papers.has(id)) return;
  const p = document.createElement("div");
  p.className = "paper settling";
  stackEl.appendChild(p);
  papers.set(id, p);
  restack();
  requestAnimationFrame(() => p.classList.remove("settling"));
}

function removePaper(id) {
  const p = papers.get(id);
  if (!p) return;
  papers.delete(id);
  p.classList.add("settling");
  window.setTimeout(() => p.remove(), still() ? 0 : 200);
  restack();
}

function restack() {
  let i = 0;
  for (const p of papers.values()) {
    p.style.setProperty("--i", String(Math.min(i, MAX_PAPERS - 1)));
    p.style.setProperty("--j", `${JITTER[i % JITTER.length]}deg`);
    p.classList.toggle("hidden", i >= MAX_PAPERS);
    i += 1;
  }
  countEl.textContent = String(papers.size);
}

/* ---------- meter, warnings, status ---------- */

function renderMeter() {
  const ids = [...state.selected].filter((id) => comp(id));
  let total = 0;
  for (const id of ids) total += sizeFor(comp(id));

  meterEl.textContent = "";
  if (!ids.length) {
    meterEl.textContent = "folder is empty — tick a tool";
  } else {
    const n = document.createElement("b");
    n.textContent = `${ids.length} tool${ids.length === 1 ? "" : "s"}`;
    meterEl.append(n, document.createTextNode(total ? ` · approx ${fmtSize(total)} · ${targetLabel(state.target)}` : ` · ${targetLabel(state.target)}`));
  }
  countEl.textContent = String(papers.size || ids.length);
  extractBtn.disabled = state.building || state.preview || !ids.length;
}

function renderGlobalWarnings() {
  globalWarnEl.textContent = "";
  for (const w of state.manifest.warnings || []) {
    const d = document.createElement("div");
    d.textContent = w;
    globalWarnEl.appendChild(d);
  }
}

function setStatus(text, cls) {
  statusEl.textContent = "";
  if (!text) return;
  const s = document.createElement("div");
  s.className = cls || "ok";
  s.textContent = text;
  statusEl.appendChild(s);
  return s;
}

/* ---------- extract ---------- */

async function extract() {
  if (state.building || !state.selected.size || state.preview) return;
  state.building = true;
  extractBtn.disabled = true;
  extractBtn.textContent = "PACKING…";
  folderEl.classList.remove("extracted");
  folderEl.classList.add("zipping");
  setStatus("closing the folder and packing the zip…", "ok");

  const body = {
    target: state.target,
    components: [...state.selected],
    recipient: $("recipient").value.trim(),
    include_docs: $("include-docs").checked,
  };

  try {
    const r = await fetch("/api/bundle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const res = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(res.error || res.message || `HTTP ${r.status}`);

    statusEl.textContent = "";
    folderEl.classList.add("extracted");

    const file = document.createElement("div");
    file.className = "file";
    file.textContent = `${res.filename} · ${fmtSize(res.size_bytes)}`;
    statusEl.appendChild(file);

    // Warnings and skips are rendered BEFORE the file is offered — that is the
    // whole reason POST /api/bundle answers with JSON instead of the zip.
    for (const w of res.warnings || []) {
      const d = document.createElement("div");
      d.className = "warn";
      d.textContent = w;
      statusEl.appendChild(d);
    }
    if (res.skipped && res.skipped.length) {
      const d = document.createElement("div");
      d.className = "skip";
      d.textContent = res.skipped
        .map((s) => `skipped ${s.tool || s.component}${s.reason ? ` — ${s.reason}` : ""}`)
        .join(" · ");
      statusEl.appendChild(d);
    }

    // A zip carrying warnings, or payroll-grade contents, must be read about
    // before it lands in ~/Downloads: the download becomes a second click.
    const mustAck =
      (res.warnings || []).length > 0 ||
      [...state.selected].some((id) => comp(id) && comp(id).sensitive);

    if (mustAck) {
      const a = document.createElement("a");
      a.className = "collect";
      a.href = res.download_url;
      a.download = res.filename || "";
      a.textContent = "COLLECT ZIP ↓";
      statusEl.appendChild(a);
    } else {
      const a = document.createElement("a");
      a.href = res.download_url;
      a.download = res.filename || "";
      document.body.appendChild(a);
      a.click();
      a.remove();
      const d = document.createElement("div");
      d.className = "ok";
      d.textContent = "downloading — delete it from the desk once it is handed over";
      statusEl.appendChild(d);
    }
    loadPast();
  } catch (e) {
    folderEl.classList.remove("extracted");
    setStatus(`could not build the bundle — ${e.message}`, "err");
  } finally {
    folderEl.classList.remove("zipping");
    state.building = false;
    extractBtn.textContent = "EXTRACT ZIP";
    renderMeter();
  }
}

/* ---------- archives on the desk ---------- */

async function loadPast() {
  const ul = $("past-bundles");
  let list = [];
  try {
    const r = await fetch("/api/bundles");
    if (r.ok) list = await r.json();
  } catch { /* server absent — preview mode */ }

  ul.textContent = "";
  const items = Array.isArray(list) ? list : list.bundles || [];
  if (!items.length) {
    const li = document.createElement("li");
    li.className = "p-empty";
    li.textContent = "no zips on this desk — they are written to distribution/dist/; delete each one once it has been handed over";
    ul.appendChild(li);
    return;
  }

  for (const b of items) {
    const li = document.createElement("li");
    const name = document.createElement("span");
    name.className = "p-name";
    name.textContent = b.filename || b.name || b.id;
    const fill = document.createElement("span");
    fill.className = "p-fill";
    const size = document.createElement("span");
    size.className = "p-size";
    size.textContent = fmtSize(b.size_bytes || b.size);
    const age = document.createElement("span");
    age.className = "p-age";
    age.textContent = fmtAge(b.age_seconds);

    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "DELETE";
    del.setAttribute("aria-label", `delete ${name.textContent}`);
    // Two-step: first click arms, second click deletes. A mis-click must not
    // silently destroy a composed zip. Disarms itself after 3s.
    let timer = 0;
    del.addEventListener("click", async () => {
      if (!del.classList.contains("armed")) {
        del.classList.add("armed");
        del.textContent = "SURE?";
        timer = window.setTimeout(() => {
          del.classList.remove("armed");
          del.textContent = "DELETE";
        }, 3000);
        return;
      }
      window.clearTimeout(timer);
      // Content-Type is required on DELETE too — the server 415s without it.
      const r = await fetch(`/api/bundle/${encodeURIComponent(b.id || b.filename || b.name)}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      });
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        del.textContent = "FAILED";
        del.title = body.error || `HTTP ${r.status}`;
        window.setTimeout(loadPast, 1400);
        return;
      }
      li.classList.add("going");
      window.setTimeout(loadPast, 220);
    });

    li.append(name, fill, size, age, del);
    ul.appendChild(li);
  }
}

/* ---------- wiring ---------- */

extractBtn.addEventListener("click", extract);
loadManifest();
