import test from "node:test";
import assert from "node:assert/strict";
import { readBounded } from "../lib/bounded-body.ts";
import { validateScenario, validateInput } from "../lib/model.ts";
import { buildModel } from "../lib/model.ts";
import { readFileSync } from "node:fs";
import type { Mark4Input } from "../lib/types.ts";

test("scenario validation rejects expensive/unrecognized dimensions and canonicalizes floats", () => {
  for (const v of [{ efficiency: NaN }, { efficiency: 0 }, { efficiency: 1.1 }, { efficiency: .801 }, { nightLine: "arbitrary" }, { url: "http://localhost" }, { allowProposedSupply: "yes" }]) assert.throws(() => validateScenario(v));
  assert.equal(validateScenario({ efficiency: .80000000001 }).efficiency, 1);
  assert.equal(validateScenario({ nightLine: null, allowProvisionalRecipes: true }).allowProvisionalRecipes, true);
});

test("body reader counts streamed bytes and cancels once limit is crossed", async () => {
  let cancelled = false;
  const oversized = new ReadableStream<Uint8Array>({ start(c) { c.enqueue(new Uint8Array(1024)); c.enqueue(new Uint8Array(1025)); }, cancel() { cancelled = true; } });
  await assert.rejects(readBounded(oversized, 2048), /exceeds/);
  assert.equal(cancelled, true);
  const small = new ReadableStream<Uint8Array>({ start(c) { c.enqueue(new TextEncoder().encode("₹")); c.close(); } });
  assert.equal(await readBounded(small, 3), "₹");
});

test("input validation refuses absent stock/coverage and unsupported model versions", () => {
  for (const input of [null, {}, { schemaVersion: 2, meta: { as_of: "2026-09-06" } }, { schemaVersion: 1, meta: { as_of: "garbage" } }]) assert.throws(() => validateInput(input));
});

test("no-night scenario emits exact zero night hours, including fractional-rate runs", () => {
  const input = JSON.parse(readFileSync(new URL("../data/seed.json", import.meta.url), "utf8"));
  const model = buildModel(input, { nightLine: null });
  assert.ok(model.days.flatMap(d => d.runs).length > 0);
  assert.ok(model.days.every(d => d.nightLine === null && d.runs.every(r => r.nightHours === 0)));
});

test("changing product across dates costs setup; continuing the same product does not", () => {
  const input: Mark4Input = {
    schemaVersion: 1,
    meta: { as_of: "2026-09-07" },
    plan: ["A", "B"].map(code => ({ code, sku: `MUSTARD ${code}`, category: "MUSTARD", pack_type: "PET", litres_per_piece: 1, pieces: 18000 })),
    bom: { A: [["RM", 1], ["PM-A", 1]], B: [["RM", 1], ["PM-B", 1]] }, blends: {},
    items: { A: { name: "MUSTARD A", uom: "PCS" }, B: { name: "MUSTARD B", uom: "PCS" }, RM: { name: "OIL", uom: "L" }, "PM-A": { name: "POUCH FILM", uom: "PCS" }, "PM-B": { name: "POUCH FILM", uom: "PCS" } },
    realise: { A: 100, B: 100 }, opening: { stock: { RM: 36000, "PM-A": 18000, "PM-B": 0 }, fg: {}, fg_other_l: 0, standing_l: 0 },
    orders: [], inbound_prebooked: { "2026-09-08": { "PM-B": 18000 } }, inbound_provenance: { "2026-09-08": { "PM-B": "EXIM-OTW" } }, lines: { "JP Machine": { "1L": 100 } }, history: { days: [], missing_dates: [], status: "partial" }, sources: [],
  };
  const model = buildModel(input, { nightLine: null });
  const first = model.days.find(d => d.date === "2026-09-07")!.runs.find(r => r.code === "A")!;
  const changed = model.days.find(d => d.date === "2026-09-08")!.runs.find(r => r.code === "B")!;
  const continued = model.days.find(d => d.date === "2026-09-09")!.runs.find(r => r.code === "B")!;
  assert.equal(first.pieces, 18000);
  assert.equal(changed.setupHours, 1);
  assert.equal(changed.pieces, 16200);
  assert.equal(changed.hours + changed.setupHours, 10);
  assert.equal(continued.setupHours, 0);
  assert.equal(continued.pieces, 1800);
});


test("legacy saved scenarios migrate speed while retaining unrelated preferences and recalculating identically", () => {
  const saved = { efficiency: .8, nightLine: null, allowProposedSupply: true, allowProvisionalRecipes: true, arrivalDates: { "PO-TEST": "2026-09-15" } };
  const migrated = validateScenario(saved);
  assert.deepEqual(migrated, { shiftStartHour: 8, includePackagingEstimates: true, ...saved, efficiency: 1, supplyMode: "expected" });
  const input = JSON.parse(readFileSync(new URL("../data/seed.json", import.meta.url), "utf8"));
  input.items["RM-TEST"] = { name: "QA incoming oil", uom: "L" };
  input.inboundEvents = [...(input.inboundEvents ?? []), { id: "PO-TEST", source: "factory_po", code: "RM-TEST", quantity: 100, unit: "L", orderedAt: "2026-09-01", expectedAt: null, asOf: input.meta.as_of, dateBasis: "unverified", status: "open", confidence: "unknown", stockIncluded: false }];
  const legacy = buildModel(input, saved), current = buildModel(input, migrated);
  assert.deepEqual(legacy.scenario, migrated);
  assert.deepEqual(legacy.days, current.days);
  assert.deepEqual(legacy.materials, current.materials);
  assert.equal(legacy.inboundEvents.find(e => e.id === "PO-TEST")?.appliedAt, "2026-09-15");
  assert.deepEqual(legacy.summary, current.summary);
  assert.equal(validateScenario({}).efficiency, 1);
});

test("every new campaign in the full seed has a productive hour; short tails require same-line continuity", () => {
  const input = JSON.parse(readFileSync(new URL("../data/seed.json", import.meta.url), "utf8"));
  for (const nightLine of [null, "JP Machine"]) {
    const model = buildModel(input, { nightLine });
    const previous = new Map<string, string>();
    let checked = 0;
    for (const day of model.days) for (const run of day.runs) {
      if (previous.get(run.line) !== run.code) {
        assert.ok(run.hours >= 1 - 1e-7, `${day.date} ${run.line} ${run.code}: new campaign has only ${run.hours} productive hours`);
        checked++;
      }
      previous.set(run.line, run.code);
    }
    assert.ok(checked > 0, "the invariant must exercise real new campaigns");
  }
});
