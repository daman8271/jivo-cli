import test from "node:test";
import assert from "node:assert/strict";
import { deriveTodayReview, timingOverlaps } from "../lib/today-review.ts";
import { validReviewDate, validateReviewBaseline } from "../lib/today-review-validation.ts";
import { unavailableFactory } from "../lib/shift-board.ts";
import { validateFactory } from "../lib/shift-validation.ts";
import type { FactoryRun, ShiftBaseline } from "../lib/shift-types.ts";
import type { Run } from "../lib/types.ts";
const now = Date.parse("2026-09-08T14:00:00Z"), date = "2026-09-08";
const actual = (extra: Partial<FactoryRun> = {}): FactoryRun => ({ id: "a", date, code: "A", product: "Oil 1 L 20 PCS", sourceUpdatedAt: new Date(now).toISOString(), liveStatus: "COMPLETED", firstStartedAt: "2026-09-08T04:00:00Z", activeSegment: { startedAt: "2026-09-08T05:00:00Z", endedAt: "2026-09-08T06:00:00Z", isActive: false }, producedPieces: 100, producedLitres: 100, quantityBasis: "recorded segments", ...extra });
const plan = (code = "A", line = "JP Machine") => ({ code, line, product: "Oil 1 L 20 PCS", pieces: 200, litres: 200 }) as Run;
function setup(runs = [actual()], planned = [plan()]) {
  const factory = unavailableFactory("", now); Object.assign(factory, { ok: true, complete: true, asOf: new Date(now).toISOString(), error: null });
  factory.lines[0].coverage = "reported"; factory.lines[0].runs = runs;
  const baseline: ShiftBaseline = { version: 1, id: "saved", date, timeZone: "Asia/Kolkata", capturedAt: "2026-09-08T13:00:00Z", inputAsOf: date, inputRevision: "old", engineVersion: "old", captureKind: "first_capture", scenario: { nightLine: null, efficiency: 1, allowProposedSupply: false, allowProvisionalRecipes: false }, sources: [], feedStatus: "live", day: { date, runs: planned, sunday: false, blockers: [], productionLitres: 0, productionValue: null, knownProductionValue: 0, unvaluedLitres: 0, targetValue: 0, targetGap: null, nightLine: null, dispatchLitres: 0, storage: { openingLitres: 0, madeLitres: 0, dispatchedLitres: 0, closingLitres: 0, unbilledLitres: 0, billedWaitingLitres: 0, limitLitres: 0, overLimitLitres: 0 }, arrivals: [] } };
  return { factory, baseline };
}
test("late capture is descriptive and cannot name a winner or claim attainment", () => {
  const { factory, baseline } = setup(); const r = deriveTodayReview(factory, baseline, date, now);
  assert.equal(r.lateCapture, true); assert.equal(r.beforeRecordedActivity, false); assert.equal(r.winner, "Not established");
  assert.equal(r.knownLitres, 100); assert.equal(r.matchedProducts, 1); assert.equal("attainment" in r, false);
});
test("legacy latest segment proves late capture but cannot prove early capture", () => {
  const { factory, baseline } = setup([actual({ firstStartedAt: undefined })]);
  assert.equal(deriveTodayReview(factory, baseline, date, now).lateCapture, true);
  baseline.capturedAt = "2026-09-08T03:00:00Z";
  assert.equal(deriveTodayReview(factory, baseline, date, now).beforeRecordedActivity, false);
});
test("a valid early save establishes order only, never a winner", () => {
  const { factory, baseline } = setup(); baseline.capturedAt = "2026-09-08T03:00:00Z"; baseline.captureKind = "start_of_day";
  const r = deriveTodayReview(factory, baseline, date, now); assert.equal(r.beforeRecordedActivity, true); assert.equal(r.winner, "Not established");
});
test("drafts and other dates are excluded; repeated exact pairs count once", () => {
  const { factory, baseline } = setup([actual(), actual({ id: "b" }), actual({ id: "draft", liveStatus: "NOT_STARTED", producedLitres: 9999 }), actual({ id: "old", date: "2026-09-07", producedLitres: 9999 })]);
  const r = deriveTodayReview(factory, baseline, date, now); assert.equal(r.knownLitres, 200); assert.equal(r.matchedProducts, 1); assert.equal(r.recordedProducts, 1); assert.equal(r.rows[0].drafts.length, 1);
});
test("unknown output is not zero and no observations yield an unknown subtotal", () => {
  const { factory, baseline } = setup([actual({ producedLitres: null, producedPieces: null })]);
  let r = deriveTodayReview(factory, baseline, date, now); assert.equal(r.knownLitres, null); assert.equal(r.missingQuantityRuns, 1);
  factory.lines[0].runs = []; r = deriveTodayReview(factory, baseline, date, now); assert.equal(r.knownLitres, null);
});
test("started zero is retained as an entered zero; unknown SKU is not a mismatch", () => {
  const { factory, baseline } = setup([actual({ producedLitres: 0, producedPieces: 0, code: null })]);
  const r = deriveTodayReview(factory, baseline, date, now); assert.equal(r.startedRuns, 1); assert.equal(r.knownLitres, 0); assert.equal(r.unknownSkuRuns, 1); assert.equal(r.rows[0].products[0].overlap, "unknown");
});
test("same name with different code stays distinct, other-machine exact match is explicit", () => {
  const { factory, baseline } = setup([actual({ code: "B" })], [plan(), plan("B", "10 Head")]);
  let r = deriveTodayReview(factory, baseline, date, now); assert.equal(r.rows[0].products[0].overlap, "other_line"); assert.equal(r.matchedProducts, 0);
  factory.lines[0].runs[0].code = "A-CARTON"; r = deriveTodayReview(factory, baseline, date, now); assert.equal(r.rows[0].products[0].overlap, "not_in_plan");
});
test("overlapping old or new timing records warn without deriving speed", () => {
  const a = actual(), b = actual({ id: "b" }); assert.equal(timingOverlaps([a, b], new Date(now).toISOString()), true);
  b.activeSegment = { startedAt: "2026-09-08T06:00:00Z", endedAt: "2026-09-08T07:00:00Z", isActive: false }; assert.equal(timingOverlaps([a, b], new Date(now).toISOString()), false);
  b.timingSegments = [{ startedAt: "2026-09-08T05:30:00Z", endedAt: "2026-09-08T07:00:00Z", note: "tea time" }]; assert.equal(timingOverlaps([a, b], new Date(now).toISOString()), true);
});
test("failed fetch, expiry and midnight retain dated evidence without a today claim", () => {
  const { factory, baseline } = setup(); assert.equal(deriveTodayReview(factory, baseline, date, now, true).fresh, false);
  assert.equal(deriveTodayReview(factory, baseline, date, now + 151000).fresh, false);
  const r = deriveTodayReview(factory, baseline, date, Date.parse("2026-09-08T18:30:00Z")); assert.equal(r.isToday, false); assert.equal(r.fresh, false); assert.equal(r.knownLitres, 100);
  assert.equal(deriveTodayReview(factory, baseline, "2026-09-09", Date.parse("2026-09-08T18:30:00Z")).knownLitres, null);
});
test("archive validation accepts its own dated baseline but rejects future and malformed dates", () => {
  const { baseline } = setup(); const tomorrow = Date.parse("2026-09-09T05:00:00Z"); validateReviewBaseline(baseline, date, tomorrow);
  for (const value of ["../state", "2026-09-31", "2026-09-10", "2020-01-01"]) assert.equal(validReviewDate(value, tomorrow), false);
  assert.throws(() => validateReviewBaseline(baseline, "2026-09-07", tomorrow));
});
test("optional timing evidence is bounded and validated", () => {
  const { factory } = setup(); validateFactory(factory);
  factory.lines[0].runs[0].timingSegments = [{ startedAt: "yesterday", endedAt: null, note: null }]; assert.throws(() => validateFactory(factory));
});
test("verified 16-to-20 carton family matches without converting bottle quantities", () => {
 const {factory,baseline}=setup([actual({code:"FG0000461"})],[plan("FG0000142")]);
 const r=deriveTodayReview(factory,baseline,date,now);
 assert.equal(r.rows[0].products[0].overlap,"same_line");assert.equal(r.matchedProducts,1);assert.equal(r.knownLitres,100);
 baseline.day.runs=[plan("FG0000143")];
 assert.equal(deriveTodayReview(factory,baseline,date,now).rows[0].products[0].overlap,"not_in_plan");
});

test("empty historical segments still check overlapping active intervals", () => {
 const a=actual({timingSegments:[]}),b=actual({id:"b",timingSegments:[]});
 assert.equal(timingOverlaps([a,b],new Date(now).toISOString()),true);
});

test("idle explanations come only from the matching dated archive and machine", () => {
 const {factory,baseline}=setup([],[]);
 baseline.day.blockers=[{code:"TIN",product:"Oil tin",line:"Tin Head",reason:"Saved storage constraint"},{code:"POUCH",product:"Oil pouch",line:"Pouch Machine",reason:"Saved film shortage"}];
 const original=JSON.stringify(baseline);
 const review=deriveTodayReview(factory,baseline,date,now);
 assert.deepEqual(review.rows.find(row=>row.line==="Tin Head")!.blockers.map(row=>row.code),["TIN"]);
 assert.deepEqual(review.rows.find(row=>row.line==="Pouch Machine")!.blockers.map(row=>row.code),["POUCH"]);
 assert.equal(deriveTodayReview(factory,baseline,"2026-09-09",now).rows.flatMap(row=>row.blockers).length,0);
 assert.equal(JSON.stringify(baseline),original);
});
