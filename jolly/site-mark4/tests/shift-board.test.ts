import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { buildModel } from "../lib/model.ts";
import { buildShiftBoard, unavailableFactory } from "../lib/shift-board.ts";
import { captureBaseline } from "../lib/shift-baseline.ts";
import { displayFresh, istDate, recent, validateBaseline, validateFactory } from "../lib/shift-validation.ts";
import type { Mark4Input } from "../lib/types.ts";
import type { FactoryNow, ShiftBaseline } from "../lib/shift-types.ts";
const now = Date.parse("2026-09-08T08:00:00Z"), stamp = new Date(now).toISOString();
function input(): Mark4Input {
  return { schemaVersion: 1, meta: { as_of: "2026-09-08", state_collected_at: stamp }, plan: ["A", "B"].map(code => ({ code, sku: `MUSTARD ${code} 1 LTR 20 PCS`, category: "MUSTARD", pack_type: "PET", litres_per_piece: 1, pieces: 20000 })), bom: { A: [["OIL", 1], ["BOTTLE", 1]], B: [["OIL", 1], ["BOTTLE", 1]] }, blends: {}, items: { A: { name: "MUSTARD A 1 LTR 20 PCS", uom: "PCS" }, B: { name: "MUSTARD B 1 LTR 20 PCS", uom: "PCS" }, OIL: { name: "OIL", uom: "L" }, BOTTLE: { name: "BOTTLE 1 LTR 40 GM", uom: "PCS" } }, realise: { A: 100, B: 100 }, opening: { stock: { OIL: 40000, BOTTLE: 40000 }, fg: {}, fg_other_l: 0, standing_l: 0 }, orders: [], inbound_prebooked: {}, lines: {}, history: { days: [], missing_dates: [], status: "partial" }, sources: [{ id: "stock", label: "Factory stock", asOf: stamp, ok: true }] };
}
function factory(): FactoryNow {
  const f = unavailableFactory("", now); Object.assign(f, { ok: true, complete: true, asOf: stamp, error: null });
  for (const line of f.lines) { line.coverage = "reported"; line.status = "STOPPED"; }
  const jp = f.lines[0]; jp.status = "RUNNING"; jp.runs = [{ id: "run-a", code: "A", product: "MUSTARD A", date: "2026-09-08", sourceUpdatedAt: "2026-09-08T04:00:00Z", liveStatus: "RUNNING", activeSegment: { startedAt: "2026-09-08T04:00:00Z", endedAt: null, isActive: true }, producedPieces: 100, producedLitres: 100, quantityBasis: "segments × pieces per case" }];
  return f;
}
function baseline(i = input()): ShiftBaseline {
  const m = buildModel(i, undefined, "live");
  return { version: 1, id: "baseline", date: "2026-09-08", timeZone: "Asia/Kolkata", capturedAt: "2026-09-08T03:30:00Z", inputAsOf: "2026-09-08", inputRevision: "content-hash", engineVersion: m.meta.engine, captureKind: "start_of_day", scenario: m.scenario, day: m.days[0], sources: m.sources, feedStatus: "live" };
}
const board = (i = input(), f = factory(), b: ShiftBaseline | null = baseline(i)) => buildShiftBoard(i, buildModel(i, undefined, "live"), f, b, null, now);
test("fresh factory poll supports a long-running campaign; event age is not poll age", () => {
  const b = board(); assert.equal(b.rows[0].advice.action, "continue"); assert.equal(b.rows[0].match, "matches"); assert.equal(b.rows[0].plannedProgress[0].madePieces, 100);
});
test("stale, failed, future and yesterday factory snapshots never give categorical advice", () => {
  for (const change of [{ asOf: "2026-09-08T07:00:00Z" }, { asOf: "2026-09-08T09:00:00Z" }, { ok: false }, { date: "2026-09-07" }]) {
    const f = Object.assign(factory(), change); assert.ok(board(input(), f).rows.every(r => r.advice.action === "cannot_verify"));
  }
});
test("multiple active segments and conflicting coverage cannot verify; future event is rejected", () => {
  for (const kind of ["duplicate", "conflict", "future"]) {
    const f = factory();
    if (kind === "duplicate") f.lines[0].runs.push({ ...f.lines[0].runs[0], id: "second" });
    if (kind === "conflict") f.lines[0].coverage = "conflict";
    if (kind === "future") f.lines[0].runs[0].sourceUpdatedAt = "2026-09-08T12:00:00Z";
    assert.equal(board(input(), f).rows[0].advice.action, "cannot_verify");
  }
});
test("similar product names and different carton SKU never establish identity", () => {
  const f = factory(); f.lines[0].runs[0].code = "A-16-CARTON";
  const row = board(input(), f).rows[0]; assert.equal(row.match, "different"); assert.notEqual(row.advice.action, "continue"); assert.notEqual(row.advice.action, "switch_next");
});
test("finished daily baseline quantity prevents suggesting its full-day run again", () => {
  const i = input(), f = factory(), b = baseline(i);
  const planned = b.day.runs.find(r => r.line === "JP Machine" && r.code === "A")!;
  f.lines[0].runs[0].producedPieces = planned.pieces;
  const row = board(i, f, b).rows[0]; assert.equal(row.plannedProgress.find(r => r.code === "A")?.remainingPieces, 0); assert.notEqual(row.advice.candidate?.code, "A");
});
test("only observed production on this line and today counts against saved progress", () => {
  const f = factory(); f.lines[0].runs.push({ ...f.lines[0].runs[0], id: "yesterday", date: "2026-09-07", producedPieces: 10000, activeSegment: null, liveStatus: "COMPLETED" });
  assert.equal(board(input(), f).rows[0].plannedProgress[0].madePieces, 100);
});
test("future arrivals and simulated same-day dispatch never fund ready-now advice", () => {
  const i = input(); i.opening.stock.BOTTLE = 0; i.inbound_prebooked["2026-09-08"] = { BOTTLE: 40000 };
  assert.ok(board(i).rows.every(r => r.advice.candidate === null));
  const full = input(); full.opening.standing_l = 827000;
  assert.ok(board(full).rows.every(r => r.advice.candidate === null));
});
test("recommendations share the material ledger rather than each spending the same stock", () => {
  const i = input(); i.opening.stock.BOTTLE = 6000;
  const rows = board(i).rows;
  assert.ok(rows.reduce((n, r) => n + (r.advice.candidate?.materials.find(m => m.code === "BOTTLE")?.quantity ?? 0), 0) <= 6000);
  assert.ok(rows.every(r => !r.advice.candidate || r.advice.candidate.hours <= 1));
});
test("malformed factory data, duplicate lines/runs and NaN quantities are rejected", () => {
  validateFactory(factory());
  for (const kind of ["duplicate-line", "duplicate-run", "quantity", "missing-segment"]) {
    const f = factory();
    if (kind === "duplicate-line") f.lines[1] = f.lines[0];
    if (kind === "duplicate-run") f.lines[1].runs = f.lines[0].runs;
    if (kind === "quantity") f.lines[0].runs[0].producedPieces = NaN;
    if (kind === "missing-segment") delete (f.lines[0].runs[0] as Partial<typeof f.lines[0]["runs"][number]>).activeSegment;
    assert.throws(() => validateFactory(f));
  }
});
test("refresh failures retain bytes but immediately invalidate displayed advice; clocks expire in-tab", () => {
  const b = board(); assert.equal(displayFresh(b, false, now), true); assert.equal(displayFresh(b, true, now), false); assert.equal(displayFresh(b, false, now + 151000), false);
  assert.equal(recent("invalid", now), false); assert.equal(recent("2026-09-08", now), false);
});
test("factory target, speed and recorded duration accept old feeds but reject invalid new metrics", () => {
  validateFactory(factory());
  for (const field of ["targetPieces", "targetLitres", "recordedRunningMinutes", "ratedSpeedPiecesPerHour"] as const) {
    for (const value of [undefined, null, 0, 20000]) {
      const f = factory(); f.lines[0].runs[0][field] = value; validateFactory(f);
    }
    for (const value of [NaN, Infinity, -1]) {
      const f = factory(); f.lines[0].runs[0][field] = value;
      assert.throws(() => validateFactory(f), /target, speed or recorded duration/);
    }
  }
});
test("IST midnight discards yesterday baseline and never claims yesterday as today", () => {
  assert.equal(istDate(Date.parse("2026-09-08T18:29:59Z")), "2026-09-08"); assert.equal(istDate(Date.parse("2026-09-08T18:30:00Z")), "2026-09-09");
  assert.throws(() => validateBaseline(baseline(), Date.parse("2026-09-08T18:30:00Z")));
  assert.equal(displayFresh(board(), false, Date.parse("2026-09-08T18:30:00Z")), false);
});
test("shared daily baseline is immutable under input, scenario and competing capture changes", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "mark4-baseline-"));
  try {
    const i = input(); const results = await Promise.all([captureBaseline(i, directory, now), captureBaseline(i, directory, now)]);
    assert.equal(results.filter(r => r.created).length, 1);
    const before = await readFile(path.join(directory, "2026-09-08.json"), "utf8");
    i.plan[0].pieces *= 2;
    buildModel(i, { nightLine: null, allowProvisionalRecipes: true });
    const again = await captureBaseline(i, directory, now + 60000);
    assert.equal(again.created, false); assert.equal(await readFile(path.join(directory, "2026-09-08.json"), "utf8"), before);
    assert.equal(again.baseline.captureKind, "first_capture");
    await assert.rejects(captureBaseline(i, directory, Date.parse("2026-09-08T18:30:00Z")), /old|future/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});

test("overdue orders already covered by FG do not trigger an urgent changeover", () => {
  const i = input(); i.orders = [
    { docnum: "past", code: "B", date: "2026-09-01", due: "2026-09-07", pieces: 100, channel: "OIL", _src: "OMS", is_exact_sku_due: true },
    { docnum: "future", code: "B", date: "2026-09-01", due: "2026-09-20", pieces: 100, channel: "OIL", _src: "OMS", is_exact_sku_due: true },
  ]; i.opening.fg.B = 100;
  const row = board(i).rows[0]; assert.equal(row.advice.action, "continue"); assert.equal(row.advice.candidate?.code, "A");
});
test("quarantined/expired/forecast raw orders cannot manufacture urgency", () => {
  for (const change of [{ code_mapping_verified: false }, { expiresAt: "2026-09-01T00:00:00Z" }, { _src: "FORECAST" }, { docnum: "FCST-1" }, { channel: "MART" }]) {
    const i = input(); i.orders = [{ docnum: "past", code: "B", date: "2026-09-01", due: "2026-09-07", pieces: 100, channel: "OIL", _src: "OMS", is_exact_sku_due: true, ...change }];
    assert.equal(board(i).rows[0].advice.candidate?.code, "A");
  }
});

test("two lines cannot both promise the same remaining SKU demand", () => {
  const i = input(); i.plan = [i.plan[0]]; i.plan[0].pieces = 100;
  const f = factory(); f.lines[1].status = "RUNNING"; f.lines[1].runs = [{ ...f.lines[0].runs[0], id: "second-line" }];
  const rows = board(i, f, null).rows;
  assert.ok(rows.reduce((n, r) => n + (r.advice.candidate?.code === "A" ? r.advice.candidate.pieces : 0), 0) <= 100);
});

test("broken and unreported machines cannot reserve materials ahead of healthy lines", () => {
  for (const unavailable of ["BREAKDOWN", "UNKNOWN"] as const) {
    const i = input(); i.opening.stock.BOTTLE = 1080;
    const f = factory(); f.lines[0].status = unavailable; f.lines[0].runs = []; if (unavailable === "UNKNOWN") f.lines[0].coverage = "unreported";
    const rows = board(i, f, null).rows;
    assert.equal(rows[0].advice.candidate, null);
    assert.equal(rows.find(r => r.line === "6 Head")?.advice.candidate?.pieces, 1080, "unavailable machines must leave stock for a full healthy-line campaign");
  }
});

test("midshift first capture counts only post-save production; legacy captures do not subtract earlier output", () => {
  const i = input(), f = factory(), b = baseline(i); b.captureKind = "first_capture";
  assert.equal(board(i, f, b).rows[0].plannedProgress[0].madePieces, null);
  b.factoryAtCapture = { asOf: stamp, lines: f.lines.map(l => ({ line: l.line, coverage: l.coverage, runs: l.runs.map(r => ({ id: r.id, code: r.code, pieces: 90 })) })) };
  assert.equal(board(i, f, b).rows[0].plannedProgress[0].madePieces, 10);
  f.lines[0].runs[0].producedPieces = 80;
  assert.equal(board(i, f, b).rows[0].plannedProgress[0].madePieces, null);
});

test("a complete midnight read with no recorded runs establishes zero counters without claiming idle", () => {
  const i = input(), f = factory(), b = baseline(i); b.captureKind = "first_capture";
  b.factoryAtCapture = { asOf: b.capturedAt, complete: true, lines: f.lines.map(l => ({ line: l.line, coverage: "unreported", runs: [] })) };
  assert.equal(board(i, f, b).rows[0].plannedProgress[0].madePieces, 100);
  b.factoryAtCapture.complete = false;
  assert.equal(board(i, f, b).rows[0].plannedProgress[0].madePieces, null);
});
test("saved counter validation rejects missing lines, duplicate runs and malformed quantities", () => {
  const b = baseline(); b.captureKind = "first_capture";
  b.factoryAtCapture = { asOf: b.capturedAt, complete: true, lines: factory().lines.map(l => ({ line: l.line, coverage: l.coverage, runs: l.runs.map(r => ({ id: r.id, code: r.code, pieces: r.producedPieces })) })) };
  validateBaseline(b, now);
  for (const kind of ["missing", "duplicate", "negative", "future"]) {
    const bad = structuredClone(b);
    if (kind === "missing") bad.factoryAtCapture!.lines.pop();
    if (kind === "duplicate") bad.factoryAtCapture!.lines[1].runs = bad.factoryAtCapture!.lines[0].runs;
    if (kind === "negative") bad.factoryAtCapture!.lines[0].runs[0].pieces = -1;
    if (kind === "future") bad.factoryAtCapture!.asOf = "2026-09-09T00:00:00Z";
    assert.throws(() => validateBaseline(bad, now));
  }
});

test("urgent 10/45-piece switches are deferred before reserving shared stock or interrupting a viable campaign", () => {
  for (const pieces of [10, 45]) {
    const i = input(); i.opening.stock.BOTTLE = 5400;
    i.items["LABEL-B"] = { name: "FRONT LABEL B", uom: "PCS" };
    i.opening.stock["LABEL-B"] = pieces; i.bom.B.push(["LABEL-B", 1]);
    i.orders = [{ docnum: "urgent-B", code: "B", date: "2026-09-01", due: "2026-09-07", pieces, channel: "OIL", _src: "OMS", is_exact_sku_due: true }];
    const rows = board(i, factory(), null).rows;
    const jp = rows.find(r => r.line === "JP Machine")!;
    assert.equal(jp.advice.action, "continue");
    assert.equal(jp.advice.candidate?.code, "A");
    assert.equal(jp.advice.candidate?.pieces, 5400, "rejected urgent switch must not consume shared bottles");
    assert.equal(rows.some(r => r.advice.candidate?.code === "B"), false);
    assert.equal(i.opening.stock["LABEL-B"], pieces);
  }
});

test("verified same-SKU active continuation may finish a short next batch", () => {
  const i = input(); i.plan = [i.plan[0]]; i.plan[0].pieces = 45;
  const jp = board(i, factory(), null).rows[0];
  assert.equal(jp.advice.action, "continue");
  assert.equal(jp.advice.candidate?.pieces, 45);
  assert.equal(jp.advice.candidate?.setupHours, 0);
  assert.equal(jp.advice.candidate?.setupBasis, "continuation");
  assert.equal(jp.advice.candidate?.hours, 45 / 5400);
});

test("stopped or unknown-current lines cannot start tiny campaigns", () => {
  for (const unknownCurrent of [false, true]) {
    const i = input(); i.plan = [i.plan[0]]; i.plan[0].pieces = 45;
    const f = factory();
    if (unknownCurrent) f.lines[0].runs[0].code = "UNMAPPED";
    else { f.lines[0].status = "STOPPED"; f.lines[0].runs = []; }
    assert.ok(board(i, f, null).rows.every(r => r.advice.candidate === null));
  }
});

test("stopped and unmapped-current setup stays unknown; known product change uses its explicit allowance", () => {
  for (const unknownCurrent of [false, true]) {
    const f = factory();
    if (unknownCurrent) f.lines[0].runs[0].code = "UNMAPPED";
    else { f.lines[0].status = "STOPPED"; f.lines[0].runs = []; }
    const next = board(input(), f, null).rows[0].advice.candidate!;
    assert.ok(next); assert.equal(next.setupHours, null); assert.equal(next.setupBasis, "unknown");
  }
  const i = input(); i.orders = [{ docnum: "urgent-B", code: "B", date: "2026-09-01", due: "2026-09-07", pieces: 10000, channel: "OIL", _src: "OMS", is_exact_sku_due: true }];
  const next = board(i, factory(), null).rows[0].advice.candidate!;
  assert.equal(next.code, "B"); assert.equal(next.setupHours, 1); assert.equal(next.setupBasis, "product_change");
});

test("fractional combo throughput rounds to a complete viable next batch instead of permanently deferring", () => {
  const i = input(); i.plan = [i.plan[0]]; i.plan[0].litres_per_piece = 7;
  i.plan[0].sku = "MUSTARD COMBO 7 X 1 LTR"; i.items.A.name = i.plan[0].sku;
  i.bom.A = [["OIL", 7], ["BOTTLE", 7]];
  const f = factory(); f.lines[0].status = "STOPPED"; f.lines[0].runs = [];
  const candidate = board(i, f, null).rows[0].advice.candidate!;
  assert.ok(candidate); assert.equal(candidate.rate.effectivePiecesPerHour, 5400 / 7);
  assert.equal(candidate.pieces, 772);
  assert.ok(candidate.hours >= 1 && candidate.hours < 1 + 1 / candidate.rate.effectivePiecesPerHour);
  assert.equal(candidate.setupHours, null);
});
