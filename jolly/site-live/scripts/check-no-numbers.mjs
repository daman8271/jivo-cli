// "Never type a business number into JSX, copy or markdown."
//
// Mark 2 enforced this by hand. Mark 3 can enforce it mechanically, because
// there IS no data at build time: any long digit run inside app/ or components/
// is either a UI constant or a mistake, and this prints every one so a human
// decides which.
//
// It also runs the phone scan the honesty file demands (`numbers-masked`).
//
//   node scripts/check-no-numbers.mjs         # report, exit 1 on a hit
//   node scripts/check-no-numbers.mjs --list  # report every hit, exit 0

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SCAN = ["app", "components"];        // lib/ and fixtures/ are out of scope by rule
const EXT = new Set([".tsx", ".ts", ".jsx", ".js", ".md", ".mdx"]);

/** A run of four or more digits. */
const DIGITS = /\d{4,}/g;
/** A phone-shaped run: 7+ digits, optionally spaced or dashed. */
const PHONE = /(?:\+?\d[\d\s-]{7,}\d)/g;

/** Things that are allowed to contain a long digit run. */
const ALLOWED = [
  /^\d{4}-\d{2}-\d{2}$/,                 // an ISO date (dates are not business numbers)
  /^9999-99-99$/,                        // the "sorts last" sentinel
];

const lines = [];
const walk = (dir) => {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === "node_modules" || e.name.startsWith(".")) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (EXT.has(path.extname(e.name))) lines.push(p);
  }
};
for (const d of SCAN) {
  const p = path.join(root, d);
  if (fs.existsSync(p)) walk(p);
}

const hits = [];
const phones = [];

for (const file of lines) {
  const text = fs.readFileSync(file, "utf8");
  text.split("\n").forEach((line, i) => {
    // a data- attribute may carry anything; Tailwind arbitrary values are UI
    const scrubbed = line
      .replace(/\bdata-[a-z-]+="[^"]*"/g, "")
      .replace(/\[[0-9.]+(rem|px|em|%|vh|vw|ch)\]/g, "");
    for (const m of scrubbed.matchAll(DIGITS)) {
      if (ALLOWED.some((re) => re.test(m[0]))) continue;
      hits.push({ file: path.relative(root, file), line: i + 1, text: line.trim(), match: m[0] });
    }
    for (const m of scrubbed.matchAll(PHONE)) {
      phones.push({ file: path.relative(root, file), line: i + 1, match: m[0].trim() });
    }
  });
}

if (phones.length) {
  console.error(`\nPHONE-SHAPED DIGITS in JSX — ${phones.length}:`);
  for (const p of phones) console.error(`  ${p.file}:${p.line}  ${p.match}`);
}
if (hits.length) {
  console.error(`\nDIGIT RUNS >= 4 in app/ or components/ — ${hits.length}:`);
  for (const hit of hits) console.error(`  ${hit.file}:${hit.line}  [${hit.match}]  ${hit.text.slice(0, 120)}`);
} else {
  console.log("no digit run of four or more in app/ or components/ — clean");
}

const bad = hits.length + phones.length;
if (bad && !process.argv.includes("--list")) process.exit(1);
