import type { FactoryRun } from "./shift-types.ts";

const instant = (value: string | null | undefined) => value && /T.*(?:Z|[+-]\d\d:\d\d)$/.test(value) ? Date.parse(value) : NaN;
export function reviewTime(value: string | null | undefined): string {
  const at = instant(value);
  return Number.isFinite(at) ? new Date(at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false }) + " IST" : "Not recorded";
}
export function intervalHours(start: string | null | undefined, end: string | null | undefined): number | null {
  const a = instant(start), b = instant(end);
  return Number.isFinite(a) && Number.isFinite(b) && b >= a ? (b - a) / 3600000 : null;
}
export function recordedTiming(run: FactoryRun, asOf: string | null, conflict = false) {
  const segments = run.timingSegments?.length ? run.timingSegments : run.activeSegment ? [{ ...run.activeSegment, note: null }] : [];
  const rows = segments.map(segment => {
    const ongoing = !segment.endedAt && run.liveStatus === "RUNNING" && run.activeSegment?.isActive === true && instant(segment.startedAt) === instant(run.activeSegment.startedAt);
    const end = segment.endedAt ?? (ongoing ? asOf : null);
    const hours = conflict || !Number.isFinite(instant(asOf)) || instant(end) > instant(asOf) ? null : intervalHours(segment.startedAt, end);
    return { ...segment, ongoing, observedUntil: ongoing ? asOf : null, hours };
  });
  return { rows, totalHours: rows.length && rows.every(row => row.hours !== null) ? rows.reduce((sum, row) => sum + row.hours!, 0) : null };
}

// Quantities are pieces; the run's saved speed is pieces/hour. No clock-time forecast.
export function estimatedFilling(run: FactoryRun, conflict = false) {
  const usable = (value: number | null | undefined): value is number => typeof value === "number" && Number.isFinite(value) && value >= 0;
  const target = usable(run.targetPieces) && run.targetPieces > 0 ? run.targetPieces : null;
  const speed = usable(run.ratedSpeedPiecesPerHour) && run.ratedSpeedPiecesPerHour > 0 ? run.ratedSpeedPiecesPerHour : null;
  const remainingPieces = !conflict && target !== null && usable(run.producedPieces) ? Math.max(target - run.producedPieces, 0) : null;
  const hours = (pieces: number | null) => {
    const value = !conflict && pieces !== null && speed !== null ? pieces / speed : NaN;
    return Number.isFinite(value) ? value : null;
  };
  return { totalHours: hours(target), remainingPieces, remainingHours: hours(remainingPieces) };
}
