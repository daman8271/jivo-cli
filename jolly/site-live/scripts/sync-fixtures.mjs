// Copy fixtures/ -> public/fixtures/ so the fixtures dev mode can serve them
// over the same origin with no network at all.
//
// fixtures/ is the canonical, committed copy (saved from the chain's own output).
// public/fixtures/ is generated and gitignored, so the JSON lives in the repo
// exactly once. Runs from predev and prebuild, so a fresh clone builds green.
//
//   node scripts/sync-fixtures.mjs           fixtures/ -> public/fixtures/
//   node scripts/sync-fixtures.mjs --pull    live/state/plan/ -> fixtures/ first
//
// --pull is what refreshes the committed snapshot from the generator, and it is
// OPT-IN on purpose: `live/state/` is gitignored and does not exist on Vercel or
// in a fresh clone, and a prebuild that quietly rewrote committed files on every
// build would make `npm run build` a source change. It refreshes the files the
// snapshot already carries — it never invents a new one — so the committed set
// stays the small, deliberate one it is.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const src = path.join(root, "fixtures");
const dst = path.join(root, "public", "fixtures");
const jolly = path.resolve(root, "..");
const PULL = process.argv.includes("--pull");

if (!fs.existsSync(src)) {
  console.error(`sync-fixtures: no ${src} — nothing to copy`);
  process.exit(0);
}

/** Where the chain's own copy of a fixture lives: fixtures/state.json is
 *  live/state/state.json, and everything under fixtures/plan/ is the same path
 *  under live/state/plan/. */
const fromLive = (rel) =>
  rel === "state.json"
    ? path.join(jolly, "live", "state", "state.json")
    : rel.startsWith("plan/")
      ? path.join(jolly, "live", "state", rel)
      : null;

if (PULL) {
  let pulled = 0;
  const missing = [];
  const pull = (dir, rel = "") => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      if (e.name.startsWith(".")) continue;
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) pull(path.join(dir, e.name), r);
      else if (e.name.endsWith(".json")) {
        const from = fromLive(r);
        if (from && fs.existsSync(from)) {
          fs.copyFileSync(from, path.join(dir, e.name));
          pulled++;
        } else missing.push(r);
      }
    }
  };
  pull(src);
  console.log(`sync-fixtures: pulled ${pulled} file(s) from live/state`);
  if (missing.length) {
    // A fixture with no file behind it is a stale snapshot, not a detail: it is
    // what "the fixture build green-lights a shape that no longer exists" looks
    // like. Name it and refuse rather than copying the old body forward.
    console.error(`sync-fixtures: NOT in live/state — ${missing.join(", ")}`);
    console.error("sync-fixtures: run the offline chain first (freeze_live.py, august_sim.py, gen_live.py)");
    process.exit(1);
  }
}

fs.rmSync(dst, { recursive: true, force: true });
fs.mkdirSync(dst, { recursive: true });

let n = 0;
const walk = (from, to) => {
  fs.mkdirSync(to, { recursive: true });
  for (const e of fs.readdirSync(from, { withFileTypes: true })) {
    if (e.name.startsWith(".")) continue;
    const a = path.join(from, e.name);
    const b = path.join(to, e.name);
    if (e.isDirectory()) walk(a, b);
    else if (e.name.endsWith(".json")) {
      fs.copyFileSync(a, b);
      n++;
    }
  }
};
walk(src, dst);
console.log(`sync-fixtures: ${n} file(s) -> public/fixtures`);
