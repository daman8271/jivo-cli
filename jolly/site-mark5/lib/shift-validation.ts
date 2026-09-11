import { LINE_IDS } from "./rules.ts";
import { MACHINES } from "./machine-policy.ts";
import type { FactoryNow, ShiftBaseline, ShiftBoard } from "./shift-types.ts";
export const istDate = (now = Date.now()) => new Date(now + 330 * 60000).toISOString().slice(0, 10);
export function recent(stamp: string | null | undefined, now: number, seconds = 150): boolean {
  if (!stamp || !/T.*(?:Z|[+-]\d\d:\d\d)$/.test(stamp)) return false;
  const age = now - Date.parse(stamp);
  return Number.isFinite(age) && age >= -30000 && age <= seconds * 1000;
}
const record = (v: unknown): v is Record<string, unknown> => !!v && typeof v === "object" && !Array.isArray(v);
const nullableString = (v: unknown) => v === null || typeof v === "string";
const quantity = (v: unknown) => v === null || typeof v === "number" && Number.isFinite(v) && v >= 0;
export function validateFactory(value: unknown): asserts value is FactoryNow {
  if (!record(value) || value.version !== 1 || typeof value.revision !== "string" || typeof value.date !== "string" || typeof value.attemptedAt !== "string" || !nullableString(value.asOf) || (value.asOf !== null && !Number.isFinite(Date.parse(String(value.asOf)))) || typeof value.expectedRefreshSeconds !== 'number' || !Number.isFinite(value.expectedRefreshSeconds) || value.expectedRefreshSeconds <= 0 || typeof value.ok !== "boolean" || typeof value.complete !== "boolean" || !Array.isArray(value.lines) || value.lines.length > 9) throw new Error("Factory response is incomplete.");
  const allowedLines=new Set<string>([...LINE_IDS,...MACHINES,'Pouch Hitech','Pouch Samarpan']);
  const lines = new Set<string>(), ids = new Set<string>();
  for (const line of value.lines) {
    if (!record(line) || typeof line.line !== "string" || !allowedLines.has(line.line) || lines.has(line.line) || !["reported", "unreported", "conflict"].includes(String(line.coverage)) || !["RUNNING", "STOPPED", "PAUSED", "BREAKDOWN", "COMPLETED", "UNKNOWN"].includes(String(line.status)) || !Array.isArray(line.runs) || line.runs.length > 500 || typeof line.note !== "string") throw new Error("Factory line is invalid or duplicated.");
    lines.add(line.line);
    for (const run of line.runs) {
      if (!record(run) || typeof run.id !== "string" || ids.has(run.id) || !nullableString(run.code) || !nullableString(run.product) || !nullableString(run.date) || !nullableString(run.sourceUpdatedAt) || !quantity(run.producedPieces) || !quantity(run.producedLitres) || typeof run.quantityBasis !== "string" || typeof run.liveStatus !== "string") throw new Error("Factory run is invalid or duplicated.");
      ids.add(run.id);
      for (const field of ["targetPieces", "targetLitres", "recordedRunningMinutes", "ratedSpeedPiecesPerHour"]) {
        if (run[field] !== undefined && !quantity(run[field])) throw new Error("Factory target, speed or recorded duration is invalid.");
      }
      const validTime = (v: unknown) => v === null || typeof v === "string" && /T.*(?:Z|[+-]\d\d:\d\d)$/.test(v) && Number.isFinite(Date.parse(v));
      if (run.firstStartedAt !== undefined && !validTime(run.firstStartedAt)) throw new Error("Factory first start is invalid.");
      if (run.timingSegments !== undefined && (!Array.isArray(run.timingSegments) || run.timingSegments.length > 500 || run.timingSegments.some(s => !record(s) || !validTime(s.startedAt) || !validTime(s.endedAt) || !nullableString(s.note) || typeof s.note === "string" && s.note.length > 180))) throw new Error("Factory timing evidence is invalid.");
      const segment = run.activeSegment;
      if (segment !== null && (!record(segment) || typeof segment.isActive !== "boolean" || !nullableString(segment.startedAt) || !nullableString(segment.endedAt))) throw new Error("Factory segment is invalid.");
    }
  }
}
export function validateBaseline(value: unknown, now = Date.now()): asserts value is ShiftBaseline {
  if (!record(value) || value.version !== 1 || value.date !== istDate(now) || value.timeZone !== "Asia/Kolkata" || typeof value.capturedAt !== "string" || !recent(value.capturedAt, now, 86400) || istDate(Date.parse(value.capturedAt)) !== value.date || typeof value.id !== "string" || typeof value.inputRevision !== "string" || typeof value.engineVersion !== "string" || typeof value.inputAsOf !== "string" || value.inputAsOf.slice(0, 10) !== value.date || !["first_capture", "start_of_day"].includes(String(value.captureKind)) || !["live", "stale"].includes(String(value.feedStatus)) || !record(value.scenario) || !Array.isArray(value.sources) || !record(value.day) || value.day.date !== value.date || !Array.isArray(value.day.runs) || value.day.runs.length > 100) throw new Error("Today's saved plan is unavailable or invalid.");
  if (value.factoryAtCapture !== undefined) {
    const capture = value.factoryAtCapture;
    if (!record(capture) || typeof capture.asOf !== "string" || !recent(capture.asOf, Date.parse(value.capturedAt), 150) || (capture.complete !== undefined && typeof capture.complete !== "boolean") || !Array.isArray(capture.lines) || capture.lines.length !== LINE_IDS.length) throw new Error("Saved factory counters are invalid.");
    const lines = new Set(), ids = new Set();
    for (const line of capture.lines) {
      if (!record(line) || !LINE_IDS.includes(String(line.line)) || lines.has(line.line) || !["reported", "unreported", "conflict"].includes(String(line.coverage)) || !Array.isArray(line.runs) || line.runs.length > 500) throw new Error("Saved factory counter lines are invalid or duplicated.");
      lines.add(line.line);
      for (const run of line.runs) {
        if (!record(run) || typeof run.id !== "string" || ids.has(run.id) || !nullableString(run.code) || !quantity(run.pieces)) throw new Error("Saved factory run counters are invalid or duplicated.");
        ids.add(run.id);
      }
    }
  }
  for (const run of value.day.runs) if (!record(run) || !LINE_IDS.includes(String(run.line)) || typeof run.code !== "string" || typeof run.product !== "string" || typeof run.pieces !== "number" || !Number.isFinite(run.pieces) || run.pieces < 0 || typeof run.litres !== "number" || !Number.isFinite(run.litres) || run.litres < 0) throw new Error("Saved plan contains an invalid run.");
}
export function validateShiftBoard(value: unknown): asserts value is ShiftBoard {
  if (!record(value) || value.version !== 1 || typeof value.date !== "string" || !recent(String(value.generatedAt), Date.now(), 150) || !Array.isArray(value.rows) || value.rows.length !== LINE_IDS.length) throw new Error("Live comparison returned an invalid response.");
  validateFactory(value.factory);
  if (value.baseline !== null) validateBaseline(value.baseline);
  const seen = new Set();
  for (const row of value.rows) {
    if (!record(row) || !LINE_IDS.includes(String(row.line)) || seen.has(row.line) || !record(row.actual) || !Array.isArray(row.plannedRuns) || !Array.isArray(row.plannedProgress) || !record(row.advice) || !Array.isArray(row.advice.limitations) || typeof row.advice.reason !== "string" || typeof row.advice.title !== "string") throw new Error("Live comparison contains an invalid line.");
    seen.add(row.line);
  }
}
export function displayFresh(board: ShiftBoard, failed: boolean, now: number): boolean {
  return !failed && board.date === istDate(now) && board.factory.ok && recent(board.factory.asOf, now) && recent(board.generatedAt, now);
}
