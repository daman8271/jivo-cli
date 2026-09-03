// Copy fixtures/ -> public/fixtures/ so the fixtures dev mode can serve them
// over the same origin with no network at all.
//
// fixtures/ is the canonical, committed copy (saved once from the publisher).
// public/fixtures/ is generated and gitignored, so the JSON lives in the repo
// exactly once. Runs from predev and prebuild, so a fresh clone builds green.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const src = path.join(root, "fixtures");
const dst = path.join(root, "public", "fixtures");

if (!fs.existsSync(src)) {
  console.error(`sync-fixtures: no ${src} — nothing to copy`);
  process.exit(0);
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
