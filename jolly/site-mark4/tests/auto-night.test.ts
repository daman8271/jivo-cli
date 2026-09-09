import test from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "../lib/model.ts";
import { campaignEligible } from "../lib/rules.ts";
import type { Mark4Input } from "../lib/types.ts";

function fixture(quantities: Record<string, number>): Mark4Input {
  const input: Mark4Input = {
    schemaVersion: 1, meta: { as_of: "2026-09-30" },
    plan: [], bom: {}, blends: {}, items: { "RM-OIL": { name: "OIL", uom: "L" } }, realise: {},
    opening: { stock: { "RM-OIL": 1000000 }, fg: {}, fg_other_l: 0, standing_l: 0 },
    orders: [], inbound_prebooked: {}, inbound_provenance: {}, lines: {}, history: { days: [], missing_dates: [], status: "partial" }, sources: [],
  };
  for (const [code, pieces] of Object.entries(quantities)) {
    const film = `PM-${code}`;
    input.plan.push({ code, sku: `SUNFLOWER ${code}`, category: "SUNFLOWER", pack_type: "POUCH", litres_per_piece: 1, pieces });
    input.bom[code] = [["RM-OIL", 1], [film, 1]];
    input.items[code] = { name: `SUNFLOWER ${code}`, uom: "PCS" };
    input.items[film] = { name: "POUCH FILM", uom: "PCS" };
    input.realise[code] = 100;
    input.opening.stock[film] = pieces;
  }
  return input;
}

test("automatic night considers a feasible product behind ten material-blocked products", () => {
  const quantities = Object.fromEntries(Array.from({ length: 10 }, (_, i) => [`A${i}`, 100000]));
  quantities.Z = 36000;
  const input = fixture(quantities); input.meta.as_of = "2026-09-29"; // Exercise a full night independently of the month-end midnight cap.
  for (let i = 0; i < 10; i++) input.opening.stock[`PM-A${i}`] = 0;
  const automatic = buildModel(input), explicit = buildModel(input, { nightLine: "Pouch Machine" });
  assert.equal(automatic.days[0].nightLine, "Pouch Machine");
  assert.equal(automatic.days[0].productionLitres, 36000);
  assert.equal(automatic.days[0].productionLitres, explicit.days[0].productionLitres);
});

test("two eight-hour campaigns justify a night even though neither SKU needs ten hours", () => {
  const input = fixture({ A: 14400, B: 14400 }); input.meta.as_of = "2026-09-29";
  const automatic = buildModel(input), explicit = buildModel(input, { nightLine: "Pouch Machine" });
  assert.equal(automatic.days[0].productionLitres, 28800);
  assert.equal(automatic.days[0].productionLitres, explicit.days[0].productionLitres);
  assert.equal(automatic.days[0].runs.reduce((total, run) => total + run.hours + run.setupHours, 0), 17);
  assert.equal(automatic.days[0].runs.reduce((total, run) => total + run.nightHours, 0), 7);
});

test("night preview cannot count shared oil twice or mutate the real material ledger", () => {
  const input = fixture({ A: 14400, B: 14400 });
  input.opening.stock["RM-OIL"] = 16000;
  const before = JSON.stringify(input), result = buildModel(input);
  assert.equal(result.days[0].nightLine, null);
  assert.equal(result.days[0].productionLitres, 14400);
  assert.equal(result.materials.find(row => row.code === "RM-OIL")!.consumed, 14400);
  assert.equal(result.materials.find(row => row.code === "RM-OIL")!.remaining, 1600);
  assert.equal(JSON.stringify(input), before);
  assert.deepEqual(buildModel(input).days, result.days);
});

test("night preview includes physical godown space and minimum new-campaign time", () => {
  const input = fixture({ A: 14400, B: 14400 });
  input.opening.fg_litres = 827000 - 15000;
  const result = buildModel(input);
  assert.equal(result.days[0].nightLine, null);
  assert.equal(result.days[0].productionLitres, 14400);
  assert.equal(result.days[0].storage.closingLitres, 826400);
  const tinySecond = buildModel(fixture({ A: 18000, B: 10 }));
  assert.equal(tinySecond.days[0].nightLine, null);
  assert.equal(tinySecond.days[0].productionLitres, 18000);
});

test("the shared campaign guard preserves continuation and rejects invalid durations", () => {
  assert.equal(campaignEligible(1, false), true);
  assert.equal(campaignEligible(.999, false), false);
  assert.equal(campaignEligible(.001, true), true);
  for (const value of [0, -1, NaN, Infinity]) assert.equal(campaignEligible(value, true), false);
});
