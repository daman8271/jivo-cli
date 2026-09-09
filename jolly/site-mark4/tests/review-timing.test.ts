import test from "node:test";
import assert from "node:assert/strict";
import { recordedTiming, intervalHours, reviewTime, estimatedFilling } from "../lib/review-timing.ts";
import type { FactoryRun } from "../lib/shift-types.ts";
const start = "2026-09-09T11:00:00+05:30", stop = "2026-09-09T11:20:00+05:30", resume = "2026-09-09T11:30:00+05:30", asOf = "2026-09-09T12:30:00+05:30";
const run = { liveStatus: "RUNNING", activeSegment: { startedAt: resume, endedAt: null, isActive: true }, timingSegments: [{ startedAt: start, endedAt: stop, note: "tea" }, { startedAt: resume, endedAt: null, note: null }] } as FactoryRun;
test("time list excludes stopped gap and bounds open interval at source observation", () => {
 const r = recordedTiming(run, asOf); assert.equal(r.rows[0].hours, 1/3); assert.equal(r.rows[1].hours, 1); assert.equal(r.totalHours, 4/3);
 assert.equal(r.rows[1].observedUntil, asOf);
});
test("missing, reversed, conflicting or unconfirmed end is not fabricated duration", () => {
 assert.equal(intervalHours(stop,start),null); assert.equal(intervalHours(null,stop),null);
 assert.equal(recordedTiming(run,asOf,true).totalHours,null);
 assert.equal(recordedTiming({...run,liveStatus:"PAUSED"},asOf).rows[1].hours,null);
 assert.equal(recordedTiming(run,null).totalHours,null);
 assert.equal(intervalHours(undefined,undefined),null);
});
test("cross-midnight intervals keep dates and IST time", () => {
 assert.equal(intervalHours("2026-09-09T23:00:00+05:30","2026-09-10T01:00:00+05:30"),2);
 assert.match(reviewTime("2026-09-09T19:30:00Z"), /10 Sept.*01:00.*IST/);
});

const batch = { ...run, targetPieces: 18000, producedPieces: 11700, ratedSpeedPiecesPerHour: 5400 };
test("source target and piece speed give filling hours without using elapsed time", () => {
 const result = estimatedFilling(batch);
 assert.equal(result.totalHours, 10/3); assert.equal(result.remainingPieces, 6300); assert.equal(result.remainingHours, 7/6);
 assert.deepEqual(estimatedFilling({...batch, sourceUpdatedAt: "2020-01-01T00:00:00Z", liveStatus: "STOPPED"}), result);
});
test("missing or unusable speed and target never invent filling hours", () => {
 for (const speed of [undefined, null, 0, -1, NaN, Infinity]) assert.equal(estimatedFilling({...batch, ratedSpeedPiecesPerHour: speed}).totalHours, null);
 for (const target of [undefined, null, 0, -1, NaN, Infinity]) assert.equal(estimatedFilling({...batch, targetPieces: target}).remainingHours, null);
 assert.equal(estimatedFilling({...batch, ratedSpeedPiecesPerHour: Number.MIN_VALUE}).totalHours, null);
});
test("unknown output keeps full-batch estimate but never treats remaining output as zero", () => {
 for (const produced of [null, -1, NaN, Infinity]) {
  const result = estimatedFilling({...batch, producedPieces: produced});
  assert.equal(result.totalHours, 10/3); assert.equal(result.remainingPieces, null); assert.equal(result.remainingHours, null);
 }
 assert.equal(estimatedFilling({...batch, producedPieces: 0}).remainingHours, 10/3);
});
test("target reached clamps remaining to zero and conflicting records suppress estimates", () => {
 for (const produced of [18000, 19000]) assert.equal(estimatedFilling({...batch, producedPieces: produced}).remainingHours, 0);
 const result = estimatedFilling(batch, true);
 assert.equal(result.totalHours, null); assert.equal(result.remainingHours, null); assert.equal(result.remainingPieces, null);
});
