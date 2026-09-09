import test from "node:test";
import assert from "node:assert/strict";
import { buildModel } from "../lib/model.ts";
import { MIN_NEW_CAMPAIGN_HOURS, PRODUCT_CHANGE_SETUP_HOURS, rulebook, DEFAULT_SCENARIO } from "../lib/rules.ts";
import type { Mark4Input } from "../lib/types.ts";

function fixture(pieces = 1800): Mark4Input {
  return {
    schemaVersion: 1, meta: { as_of: "2026-09-30" },
    plan: [{ code: "A", sku: "SUNFLOWER A", category: "SUNFLOWER", pack_type: "POUCH", litres_per_piece: 1, pieces }],
    bom: { A: [["RM-OIL", 1], ["PM-FILM", 1], ["PM-LABEL", 1]] }, blends: {},
    items: { A: { name: "SUNFLOWER A", uom: "PCS" }, "RM-OIL": { name: "SUNFLOWER OIL", uom: "L" }, "PM-FILM": { name: "POUCH FILM", uom: "PCS" }, "PM-LABEL": { name: "FRONT LABEL", uom: "PCS" } },
    realise: { A: 100 }, opening: { stock: { "RM-OIL": 100000, "PM-FILM": 100000, "PM-LABEL": 100000 }, fg: {}, fg_other_l: 0, standing_l: 0 },
    orders: [], inbound_prebooked: {}, inbound_provenance: {}, lines: {}, history: { days: [], missing_dates: [], status: "partial" }, sources: [],
  };
}
function bottle(input: Mark4Input, pack = 1) {
  input.plan[0].litres_per_piece = pack;
  input.plan[0].pack_type = "PET";
  input.items["PM-FILM"].name = `PET BOTTLE ${pack} LTR 40 GM`;
  input.bom.A[0][1] = pack;
}
const model = (input: Mark4Input) => buildModel(input, { nightLine: null });

test("new campaigns require a full productive hour including unknown opening setup", () => {
  assert.equal(MIN_NEW_CAMPAIGN_HOURS, PRODUCT_CHANGE_SETUP_HOURS);
  for (const [pieces, expected] of [[1799, 0], [1800, 1800], [1801, 1801]]) {
    const result = model(fixture(pieces));
    assert.equal(result.summary.plannedLitres, expected);
    if (!expected) assert.match(result.days[0].blockers[0].reason, /Deferred small campaign.*remaining demand.*provisional/);
    else { assert.equal(result.days[0].runs[0].setupHours, 0); assert.ok(result.days[0].runs[0].hours >= 1); }
  }
  const rule = rulebook(DEFAULT_SCENARIO).find(row => row.id === "campaign-minimum")!;
  assert.equal(rule.status, "provisional");
  assert.match(rule.detail, /not a measured factory minimum/);
});

test("45 sunflower bottles are deferred without consuming their limited oil", () => {
  const input = fixture(10000); bottle(input);
  input.opening.stock["RM-OIL"] = 45.41;
  const result = model(input);
  assert.equal(result.summary.plannedLitres, 0);
  assert.equal(result.products[0].unmetPieces, 10000);
  assert.equal(result.materials.find(row => row.code === "RM-OIL")!.remaining, 45.41);
  assert.equal(result.days[0].blockers[0].materialCode, "RM-OIL");
  assert.match(result.days[0].blockers[0].reason, /45 pieces.*SUNFLOWER OIL/);
});

test("10 Gold bottles are deferred and their immediate limiting label is reported", () => {
  const input = fixture(10000); bottle(input);
  input.items.A.name = "GOLD 1 LTR 20 PCS";
  input.opening.stock["RM-OIL"] = 100;
  input.opening.stock["PM-LABEL"] = 10;
  const result = model(input);
  assert.equal(result.summary.plannedLitres, 0);
  assert.equal(result.days[0].blockers[0].materialCode, "PM-LABEL");
  assert.match(result.days[0].blockers[0].reason, /10 pieces.*FRONT LABEL/);
  assert.equal(result.materials.find(row => row.code === "PM-LABEL")!.consumed, 0);
});

test("1530 mustard 2L bottles remain a practical run at 1260 pieces/hour", () => {
  const input = fixture(10000); bottle(input, 2);
  input.items.A.name = "MUSTARD PAKKI GHANI 2 LTR";
  input.opening.stock["RM-OIL"] = 4000;
  input.opening.stock["PM-LABEL"] = 1530;
  const result = model(input), run = result.days[0].runs[0];
  assert.equal(run.line, "10 Head");
  assert.equal(run.pieces, 1530);
  assert.equal(run.hours, 1530 / 1260);
  assert.equal(result.days[0].blockers[0].materialCode, "PM-LABEL", "full remaining-demand oil shortage must not hide the exhausted label");
  assert.equal(result.days[0].blockers[0].missingQuantity, 8470);
  assert.equal(result.materials.find(row => row.code === "PM-LABEL")!.shortage, 8470);
});

test("same-product continuation can finish a short tail without another setup", () => {
  const input = fixture(18010); input.meta.as_of = "2026-09-28";
  const result = model(input);
  assert.equal(result.days[0].runs[0].pieces, 18000);
  assert.equal(result.days[1].runs[0].pieces, 10);
  assert.equal(result.days[1].runs[0].setupHours, 0);
  assert.match(result.days[1].runs[0].reason, /same-product continuation/);
});

test("deferral preserves shared material, order demand and both campaign slots", () => {
  const input = fixture();
  input.opening.stock["PM-LABEL"] = 10;
  input.opening.stock["RM-OIL"] = 3610;
  for (const code of ["B", "C"]) {
    input.plan.push({ ...input.plan[0], code, sku: code });
    input.items[code] = { name: `SUNFLOWER ${code}`, uom: "PCS" };
    input.bom[code] = [["RM-OIL", 1], ["PM-FILM", 1]];
    input.realise[code] = 100;
  }
  input.orders = [{ code: "A", docnum: "ORDER-A", channel: "OIL", _src: "OMS", date: "2026-09-30", due: "2026-09-30", pieces: 1800 }];
  const result = model(input);
  assert.deepEqual(result.days[0].runs.map(run => run.code), ["B", "C"]);
  assert.equal(result.products.find(p => p.code === "A")!.unmetPieces, 1800);
  assert.equal(result.materials.find(row => row.code === "RM-OIL")!.remaining, 10);
  assert.match(result.days[0].blockers.find(row => row.code === "A")!.reason, /Deferred small campaign/);
  assert.equal(result.days[0].runs.reduce((total, run) => total + run.setupHours, 0), 1);
});

test("later material arrival can unblock the deferred campaign and its exact order", () => {
  const input = fixture(); input.meta.as_of = "2026-09-28";
  input.opening.stock["PM-LABEL"] = 10;
  input.inbound_prebooked = { "2026-09-29": { "PM-LABEL": 1790 } };
  input.inbound_provenance = { "2026-09-29": { "PM-LABEL": "EXIM-OTW" } };
  input.orders = [{ code: "A", docnum: "ORDER-A", channel: "OIL", _src: "OMS", date: "2026-09-28", due: "2026-09-28", pieces: 1800 }];
  const result = model(input);
  assert.equal(result.days[0].runs.length, 0);
  assert.equal(result.days[1].runs[0].pieces, 1800);
  assert.equal(result.days[1].runs[0].exactOrderPieces, 1800);
  assert.equal(result.days[1].blockers.length, 0);
});

test("an eligible slower alternative can take a sufficient campaign", () => {
  const input = fixture(1080); bottle(input);
  const result = model(input);
  assert.equal(result.days[0].runs[0].line, "6 Head");
  assert.equal(result.days[0].runs[0].hours, 1);
  assert.equal(result.days[0].blockers.length, 0);
});

test("storage-limited new campaigns remain deferred until space is available", () => {
  const input = fixture(1800); input.opening.fg_litres = 826990;
  const result = model(input);
  assert.equal(result.summary.plannedLitres, 0);
  assert.match(result.days[0].blockers[0].reason, /10 pieces.*godown space/);
});
