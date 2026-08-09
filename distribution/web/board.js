/* JIVO Dispatch board. Renders ONLY from GET /api/manifest — no hardcoded tool list. */
"use strict";

const GROUPS = [
  { head: "SAP & BOOKS", ids: ["sap-b1", "hana-sql"] },
  { head: "OPS SYSTEMS", ids: ["ecom-cli", "oms-cli", "factory-cli", "exim", "jsap-cli", "control-panel", "dsr-cli", "postsql"] },
  { head: "SELLER PORTALS", ids: ["portals"] },
  { head: "DESK TOOLS", ids: ["jivo-scraping-cli"] },
];
const AUTH_LABEL = {
  "baked-env": "READY ON ARRIVAL",
  "auth-login": "LOGIN ONCE",
  "home-config-install": "COPY CONFIG",
  "external-token": "SESSION-BOUND",
  preview: "PREVIEW — NO SERVER",
};

const state = {
  manifest: null,
  target: "mac-arm64",
  selected: new Set(),
  building: false,
  preview: false, // true when server API is absent and we render from raw manifest.json
};

const $ = (id) => document.getElementById(id);
const boardEl = $("board-groups");
const slipItems = $("slip-items");
const slipTotal = $("slip-total");
const slipStatus = $("slip-status");
const dispatchBtn = $("dispatch");

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

function comp(id) {
  return state.manifest.components.find((c) => c.id === id);
}

function avail(c) {
  return (c.availability && c.availability[state.target]) || { ok: false, warnings: ["no availability data"] };
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
      $("foot-note").textContent =
        "board can't reach the server — run ./jivodist in distribution/server, then reload";
      $("foot-note").classList.add("err");
      return;
    }
  }
  if (state.preview) {
    $("foot-note").textContent =
      "PREVIEW — raw manifest, no server: sizes and dispatch are disabled until ./jivodist runs";
  }
  renderBoard();
  renderSlip();
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

/* ---------- board ---------- */

function renderBoard() {
  boardEl.textContent = "";
  const seen = new Set();
  const groups = GROUPS.map((g) => ({ ...g, ids: g.ids.filter((id) => comp(id) && seen.add(id)) }));
  const rest = state.manifest.components.map((c) => c.id).filter((id) => !seen.has(id));
  if (rest.length) groups.push({ head: "UNGROUPED", ids: rest });

  for (const g of groups) {
    if (!g.ids.length) continue;
    const sec = document.createElement("section");
    sec.className = "group";
    const h = document.createElement("h2");
    h.className = "group-head";
    h.textContent = g.head;
    const ul = document.createElement("ul");
    ul.className = "rows";
    for (const id of g.ids) ul.appendChild(renderRow(comp(id)));
    sec.append(h, ul);
    boardEl.appendChild(sec);
  }
}

function renderRow(c) {
  const a = avail(c);
  const li = document.createElement("li");
  li.className = "row" + (a.ok ? "" : " disabled");

  const label = document.createElement("label");
  label.className = "row-line";

  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = state.selected.has(c.id);
  input.disabled = !a.ok;
  input.setAttribute("aria-label", c.ui_name);
  input.addEventListener("change", () => {
    input.checked ? state.selected.add(c.id) : state.selected.delete(c.id);
    renderSlip();
  });

  const tick = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  tick.setAttribute("class", "tickbox");
  tick.setAttribute("viewBox", "0 0 17 17");
  tick.setAttribute("aria-hidden", "true");
  tick.innerHTML = '<rect x="1" y="1" width="15" height="15"/><path d="M3.5 9l3.5 4 6.5-9"/>';

  const name = document.createElement("span");
  name.className = "tool-name";
  name.textContent = c.id;

  const desc = document.createElement("span");
  desc.className = "tool-desc";
  desc.textContent = c.ui_description;
  desc.title = c.ui_description;

  const auth = document.createElement("span");
  auth.className = "tool-auth";
  auth.textContent = AUTH_LABEL[c.auth_mode] || c.auth_mode.toUpperCase();
  if (c.auth_note) auth.title = c.auth_note;

  const size = document.createElement("span");
  size.className = "tool-size";
  size.textContent = fmtSize(sizeFor(c));

  label.append(input, tick, name, desc, auth, size);
  li.appendChild(label);

  const notes = [...(a.warnings || [])];
  if (c.sensitive) notes.push("contains payroll portal — hand to trusted staff only");
  if (notes.length) {
    const warn = document.createElement("div");
    warn.className = "row-warn";
    // Selecting/copying warning text must not toggle the checkbox.
    warn.addEventListener("click", (e) => e.preventDefault());
    const brief = document.createElement("span");
    brief.className = "warn-brief";
    brief.textContent = `※ ${notes.length} chalk note${notes.length > 1 ? "s" : ""}`;
    brief.title = notes.join("\n");
    const full = document.createElement("span");
    full.className = "warn-full";
    notes.forEach((n, i) => {
      if (i) full.append("  ");
      const mark = document.createElement("span");
      mark.className = "warn-mark";
      mark.textContent = "⚠ ";
      full.append(mark, n);
    });
    warn.append(brief, full);
    label.appendChild(warn);
  }
  return li;
}

/* ---------- slip ---------- */

function renderSlip() {
  $("slip-target").textContent = state.target === "windows" ? "WINDOWS" : "MAC";
  slipItems.textContent = "";
  const ids = [...state.selected].filter((id) => comp(id));

  const glob = $("slip-global");
  glob.textContent = "";
  for (const w of state.manifest.warnings || []) {
    const g = document.createElement("div");
    g.textContent = "⚠ " + w;
    glob.appendChild(g);
  }

  if (!ids.length) {
    const hint = document.createElement("p");
    hint.className = "slip-hint";
    hint.textContent = "nothing chalked up yet — tick tools on the board";
    slipItems.appendChild(hint);
    slipTotal.textContent = "";
    dispatchBtn.disabled = true;
    return;
  }

  let total = 0;
  for (const id of ids) {
    const c = comp(id);
    const a = avail(c);
    total += sizeFor(c);

    const item = document.createElement("div");
    item.className = "slip-item";
    const line = document.createElement("div");
    line.className = "slip-item-line";
    const nm = document.createElement("span");
    nm.textContent = c.id;
    const leader = document.createElement("span");
    leader.className = "leader";
    const sz = document.createElement("span");
    sz.className = "sz";
    sz.textContent = fmtSize(sizeFor(c));
    line.append(nm, leader, sz);
    item.appendChild(line);

    const note = document.createElement("div");
    note.className = "slip-note";
    note.textContent = c.auth_note || (AUTH_LABEL[c.auth_mode] || c.auth_mode).toLowerCase();
    item.appendChild(note);

    for (const w of a.warnings || []) {
      const wn = document.createElement("div");
      wn.className = "slip-note warn";
      wn.textContent = "⚠ " + w;
      item.appendChild(wn);
    }
    slipItems.appendChild(item);
  }

  slipTotal.textContent = "";
  const tl = document.createElement("span");
  tl.textContent = `${ids.length} ITEM${ids.length > 1 ? "S" : ""}`;
  const tr = document.createElement("span");
  tr.textContent = total ? `approx ${fmtSize(total)}` : "";
  slipTotal.append(tl, tr);

  dispatchBtn.disabled = state.building || state.preview;
}

function setStatus(text, cls) {
  slipStatus.textContent = "";
  if (!text) return;
  const s = document.createElement("span");
  s.className = cls;
  s.textContent = text;
  slipStatus.appendChild(s);
}

/* ---------- dispatch ---------- */

async function dispatch() {
  if (state.building || !state.selected.size) return;
  state.building = true;
  dispatchBtn.disabled = true;
  setStatus("packing the kit…", "ok");

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

    let msg = `${res.filename} — ${fmtSize(res.size_bytes)} ready.`;
    if (res.skipped && res.skipped.length) msg += ` skipped ${res.skipped.length} tool(s).`;
    const shown = new Set(state.manifest.warnings || []);
    for (const id of state.selected) {
      const c = comp(id);
      if (c) for (const w of avail(c).warnings || []) shown.add(`${id}: ${w}`);
    }
    const fresh = (res.warnings || []).filter((w) => !shown.has(w));
    if (fresh.length) msg += ` ⚠ ${fresh.join(" · ")}`;
    setStatus(msg, fresh.length ? "err" : "ok");
    const imp = document.createElement("div");
    imp.className = "impression";
    imp.textContent = `DISPATCHED · ${$("slip-date").textContent}`;
    slipStatus.prepend(imp);

    // Warnings (or payroll-grade contents) must be READ before the zip lands
    // in ~/Downloads — the download becomes a deliberate second click.
    const mustAck =
      (res.warnings || []).length > 0 ||
      [...state.selected].some((id) => comp(id) && comp(id).sensitive);
    if (mustAck) {
      const a = document.createElement("a");
      a.className = "collect";
      a.href = res.download_url;
      a.download = res.filename || "";
      a.textContent = "COLLECT ZIP →";
      slipStatus.appendChild(a);
    } else {
      const a = document.createElement("a");
      a.href = res.download_url;
      a.download = res.filename || "";
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    loadPast();
  } catch (e) {
    slipStatus.classList.add("wiping");
    setTimeout(() => {
      slipStatus.classList.remove("wiping");
      setStatus(`dispatch failed — ${e.message}`, "err");
    }, 230);
  } finally {
    state.building = false;
    renderSlip();
  }
}

/* ---------- past bundles ---------- */

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
    li.textContent = "no bundles on this desk — zips land in distribution/dist/, delete them once handed over";
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
    size.textContent = fmtSize(b.size_bytes || b.size);
    const age = document.createElement("span");
    age.textContent = fmtAge(b.age_seconds);
    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "DELETE";
    // Two-step: first click arms, second click wipes. A mis-click must not
    // silently destroy a composed zip.
    del.addEventListener("click", async () => {
      if (!del.classList.contains("armed")) {
        del.classList.add("armed");
        del.textContent = "SURE?";
        setTimeout(() => {
          del.classList.remove("armed");
          del.textContent = "DELETE";
        }, 3000);
        return;
      }
      const r = await fetch(`/api/bundle/${encodeURIComponent(b.id || b.filename || b.name)}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      });
      if (!r.ok) {
        del.textContent = "FAILED";
        setTimeout(loadPast, 1200);
        return;
      }
      li.classList.add("wiping");
      setTimeout(loadPast, 230);
    });
    li.append(name, fill, size, age, del);
    ul.appendChild(li);
  }
}

/* ---------- wiring ---------- */

for (const plate of document.querySelectorAll(".plate")) {
  plate.addEventListener("click", () => {
    if (state.target === plate.dataset.target) return;
    state.target = plate.dataset.target;
    for (const p of document.querySelectorAll(".plate"))
      p.setAttribute("aria-pressed", String(p === plate));
    if (state.manifest) {
      // A tool that doesn't exist for this target can't stay in the kit —
      // a checked+disabled row would be stuck and would still get POSTed.
      for (const id of [...state.selected]) {
        const c = comp(id);
        if (c && !avail(c).ok) state.selected.delete(id);
      }
      renderBoard();
      renderSlip();
    }
  });
}
dispatchBtn.addEventListener("click", dispatch);
$("slip-date").textContent = new Date().toLocaleDateString("en-IN", {
  day: "2-digit", month: "short", year: "numeric",
});

loadManifest();
