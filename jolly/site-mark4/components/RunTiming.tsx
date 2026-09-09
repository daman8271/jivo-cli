import { firstStart } from "@/lib/today-review";
import { recordedTiming, reviewTime, intervalHours, estimatedFilling } from "@/lib/review-timing";
import { formatDuration, formatSetupDuration } from "@/lib/duration";
import type { FactoryRun } from "@/lib/shift-types";
import type { Run } from "@/lib/types";
const pieces = (value: number | null | undefined) => value == null || !Number.isFinite(value) || value < 0 ? "Not reported" : value.toLocaleString("en-IN", { maximumFractionDigits: 2 });
export function EstimatedFilling({ run, asOf, conflict }: { run: FactoryRun; asOf: string | null; conflict: boolean }) {
  const estimate = estimatedFilling(run, conflict);
  const completed = run.liveStatus === "COMPLETED";
  const paused = ["STOPPED", "PAUSED", "BREAKDOWN"].includes(run.liveStatus);
  const duration = (value: number | null) => value === null ? "Cannot calculate" : formatDuration(value);
  return <div className="review-timing"><h4>Estimated filling time</h4>
    <p>Full batch: <strong>{duration(estimate.totalHours)}</strong></p>
    <p>{completed ? "Time for recorded shortfall" : "Filling left at this reading"}: <strong>{duration(estimate.remainingHours)}</strong></p>
    <p>Target: <strong>{pieces(run.targetPieces)} pieces</strong><br />Recorded output: <strong>{pieces(run.producedPieces)} pieces</strong><br />{completed ? "Recorded shortfall" : "Pieces left against target"}: <strong>{pieces(estimate.remainingPieces)}</strong></p>
    <p>Saved factory speed: <strong>{pieces(run.ratedSpeedPiecesPerHour)} pieces/hour</strong></p>
    <small>Batch date: {run.date || "Not reported"}. Based on factory reading {reviewTime(asOf)}. These figures do not count down between readings.</small>
    {conflict ? <p>Conflicting factory records: estimates are withheld until checked.</p> : <>
      {run.targetPieces === 0 ? <p>0 target recorded. Confirm the batch target before calculating hours.</p> : estimate.totalHours === null && <p>A positive batch target and saved factory speed are needed to calculate hours.</p>}
      {estimate.totalHours !== null && estimate.remainingPieces === null && <p>Recorded output is missing, so the remaining hours are unknown.</p>}
      {completed ? <p>The factory marked this batch completed. Any shortfall above is a comparison with its target, not more work scheduled.</p> : estimate.remainingPieces === 0 ? <p>The recorded target has been reached. This does not confirm the machine has stopped.</p> : paused ? <p>At the last reading the machine was stopped. Remaining filling hours apply if it resumes at the saved speed; the restart time is unknown.</p> : null}
    </>}
    <small>Calculated as target ÷ speed and remaining pieces ÷ speed. Stops, setup, breaks and slower running add time. Output may not all be entered yet. This is an estimate, not a factory-confirmed finish time.</small>
  </div>;
}
export function ActualTiming({ run, asOf, conflict }: { run: FactoryRun; asOf: string | null; conflict: boolean }) {
  const timing = recordedTiming(run, asOf, conflict);
  return <><EstimatedFilling run={run} asOf={asOf} conflict={conflict} /><details className="review-timing recorded-timing">
    <summary>Recorded intervals: <strong>{timing.totalHours === null ? "Unknown" : formatDuration(timing.totalHours)}</strong> <span>· Details</span></summary>
    <p>First start: <strong>{reviewTime(firstStart(run))}</strong> · {run.liveStatus.toLowerCase().replaceAll("_", " ")} at last reading</p>
    {timing.rows.length ? <ol>{timing.rows.map((row, index) => <li key={index}>
      <span>{reviewTime(row.startedAt)} → {row.endedAt ? reviewTime(row.endedAt) : row.ongoing ? "Running at last reading" : "End not recorded"}</span>
      <strong>{row.hours === null ? "Duration unknown" : formatDuration(row.hours)}{row.ongoing && row.hours !== null ? " elapsed at last reading" : ""}</strong>
      {row.note && <small>Stop note: “{row.note}”</small>}
    </li>)}</ol> : <p>Start/stop intervals were not saved.</p>}
    <small>Through {reviewTime(asOf)}; gaps excluded. Entered intervals, not verified machine uptime.{conflict ? " Conflicting times need checking." : ""}</small>
  </details></>;
}
export function PlannedTiming({ run }: { run: Run }) {
  const elapsed = intervalHours(run.startsAt, run.endsAt);
  return <div className="review-timing"><h4>Planned time</h4>
    <p>Filling time: <strong>{formatDuration(run.hours)}</strong></p>
    <p>Start: <strong>{reviewTime(run.startsAt)}</strong><br />Finish: <strong>{reviewTime(run.endsAt)}</strong></p>
    {elapsed !== null && <p>Start-to-finish window: <strong>{formatDuration(elapsed)}</strong></p>}
    {!run.startsAt && !run.endsAt && <small>This older plan saved the hours, but not start/end clock times.</small>}
    <p>Day filling: <strong>{formatDuration(run.dayHours)}</strong> · Night filling: <strong>{formatDuration(run.nightHours)}</strong></p>
    <p>Setup: <strong>{formatSetupDuration(run)}</strong></p>
    <small>Planned hours, not actual work. Start-to-finish windows can include waiting.</small>
  </div>;
}
