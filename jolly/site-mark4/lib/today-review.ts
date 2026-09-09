import cartonEvidence from "../data/carton-evidence.json" with { type: "json" };
import type { FactoryNow, FactoryRun, ShiftBaseline } from "./shift-types.ts";
import { istDate, recent } from "./shift-validation.ts";

const verifiedCartons = cartonEvidence.mappings.filter(row => row.status === "verified" && row.new_code);
const family = (code: string) => verifiedCartons.find(row => row.old_code === code)?.new_code ?? code;
const instant = (value: string | null | undefined) => value && /T.*(?:Z|[+-]\d\d:\d\d)$/.test(value) ? Date.parse(value) : NaN;
export function runStarted(run: FactoryRun): boolean {
  return run.liveStatus !== "NOT_STARTED" && (Number.isFinite(instant(run.firstStartedAt)) || Number.isFinite(instant(run.activeSegment?.startedAt)) || ["RUNNING", "STOPPED", "PAUSED", "BREAKDOWN", "COMPLETED"].includes(run.liveStatus));
}
export function firstStart(run: FactoryRun): string | null {
  // The active segment is the latest segment; it cannot prove the first start.
  return Number.isFinite(instant(run.firstStartedAt)) ? run.firstStartedAt! : null;
}
export function timingOverlaps(runs: FactoryRun[], asOf: string | null): boolean {
  const segments = runs.flatMap(run => (run.timingSegments?.length ? run.timingSegments : (run.activeSegment ? [run.activeSegment] : [])).map(segment => ({ start: instant(segment.startedAt), end: instant(segment.endedAt ?? asOf) })));
  if (segments.some(s => Number.isFinite(s.start) && Number.isFinite(s.end) && s.end < s.start)) return true;
  const valid = segments.filter(s => Number.isFinite(s.start) && Number.isFinite(s.end) && s.end > s.start).sort((a, b) => a.start - b.start);
  return valid.some((s, i) => valid.slice(0, i).some(previous => previous.end > s.start));
}
export function deriveTodayReview(factory: FactoryNow, saved: ShiftBaseline | null, date: string, now = Date.now(), failed = false) {
  const currentDate = istDate(now);
  const baseline = saved?.date === date && saved.day.date === date ? saved : null;
  const dated = factory.date === date;
  const fresh = dated && !failed && factory.ok && recent(factory.asOf, now);
  const rows = factory.lines.map(line => {
    const datedRuns = dated ? line.runs.filter(run => run.date === date) : [];
    const actual = datedRuns.filter(runStarted);
    const drafts = datedRuns.filter(run => run.liveStatus === "NOT_STARTED");
    const unknown = datedRuns.filter(run => !runStarted(run) && run.liveStatus !== "NOT_STARTED");
    const planned = baseline?.day.runs.filter(run => run.line === line.line) ?? [];
    const blockers = baseline?.day.blockers.filter(blocker => blocker.line === line.line) ?? [];
    const sameLine = new Set(planned.map(run => family(run.code)));
    const elsewhere = new Set(baseline?.day.runs.filter(run => run.line !== line.line).map(run => family(run.code)));
    const products = actual.map(run => ({ run, cartonMapping: verifiedCartons.find(mapping => mapping.new_code === run.code || mapping.old_code === run.code) ?? null, overlap: !baseline || !run.code ? "unknown" as const : sameLine.has(family(run.code)) ? "same_line" as const : elsewhere.has(family(run.code)) ? "other_line" as const : "not_in_plan" as const }));
    return { line: line.line, coverage: line.coverage, note: line.note, actual, drafts, unknown, planned, blockers, products, timingConflict: timingOverlaps(actual, factory.asOf) };
  });
  const runs = rows.flatMap(row => row.actual);
  const starts = runs.map(firstStart);
  const earliest = starts.filter((s): s is string => s !== null).sort((a, b) => instant(a) - instant(b))[0] ?? null;
  const captured = instant(baseline?.capturedAt);
  const witnessedStarts = runs.flatMap(run => [run.firstStartedAt, run.activeSegment?.startedAt, ...(run.timingSegments ?? []).map(s => s.startedAt)]).filter((s): s is string => typeof s === "string" && Number.isFinite(instant(s)) && istDate(instant(s)) === date);
  const alreadyStartedAt = witnessedStarts.sort((a, b) => instant(a) - instant(b))[0] ?? null;
  const lateCapture = !!baseline && !!alreadyStartedAt && captured >= instant(alreadyStartedAt);
  const timingKnown = runs.length > 0 && starts.every(s => s !== null && istDate(instant(s)) === date && instant(s) <= instant(factory.asOf));
  const beforeRecordedActivity = !!baseline && timingKnown && !lateCapture && captured < instant(earliest);
  const knownLitres = runs.filter(run => run.producedLitres !== null);
  const missingQuantityRuns = runs.filter(run => run.producedLitres === null).length;
  const matchedProducts = new Set(rows.flatMap(row => row.products.filter(p => p.overlap === "same_line").map(p => `${row.line}:${family(p.run.code!)}`))).size;
  const recordedProducts = new Set(rows.flatMap(row => row.actual.filter(run => run.code).map(run => `${row.line}:${family(run.code!)}`))).size;
  return { date, currentDate, isToday: date === currentDate, dated, fresh, baseline, rows, earliest, alreadyStartedAt, lateCapture, beforeRecordedActivity, timingKnown,
    knownLitres: knownLitres.length ? knownLitres.reduce((sum, run) => sum + run.producedLitres!, 0) : null,
    missingQuantityRuns, startedRuns: runs.length, recordedProducts, matchedProducts,
    unknownSkuRuns: runs.filter(run => !run.code).length,
    unreportedLines: rows.filter(row => row.coverage !== "reported").length,
    timingConflict: rows.some(row => row.timingConflict),
    winner: "Not established" as const };
}
