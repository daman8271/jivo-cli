"use client";
import { useEffect, useRef, useState } from "react";
import type { FactoryRun, ShiftBoard } from "@/lib/shift-types";
import { formatDuration } from "@/lib/duration";
import { displayFresh, istDate, validateShiftBoard } from "@/lib/shift-validation";
import { ActualTiming, PlannedTiming } from "./RunTiming";
import { timingOverlaps } from "@/lib/today-review";
import reviewExplanations from "@/data/review-explanations.json";
const number = (n: number) => Math.round(n).toLocaleString("en-IN");
const time = (value: string | null | undefined) => value && Number.isFinite(Date.parse(value)) ? new Date(value).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit" }) + " IST" : "unavailable";
const age = (value: string | null | undefined, now: number) => { const ms = value ? now - Date.parse(value) : NaN; return !Number.isFinite(ms) ? "time unavailable" : ms < -30000 ? "invalid future time" : ms < 60000 ? "just now" : `${Math.floor(ms / 60000)} min ago`; };
function FactoryRunBar({ run, current, reliable, asOf, conflict, line }: { run: FactoryRun; current: boolean; reliable: boolean; asOf: string | null; conflict: boolean; line: string }) {
  const explanation = reviewExplanations.find(note => note.date === run.date && note.line === line && note.code === run.code);
  return <div className={`live-run-bar ${current && reliable ? "actual" : "muted"}`}>
    <span className="live-bar-caption">{current ? reliable ? "Current production run" : "Retained run · status unverified" : reliable ? "Last reported run · not running now" : "Last reported run · status unverified"}</span>
    <strong>{run.product || "Product not reported"}</strong>
    <code>{run.code || "SKU unknown"}</code>
    <p>{run.producedPieces === null ? "Output unavailable" : `${number(run.producedPieces)} pieces recorded`}{run.producedLitres !== null ? ` · ${number(run.producedLitres)} L` : ""}</p>
    <p>{run.targetPieces != null ? `Run target: ${number(run.targetPieces)} pieces${run.targetLitres != null ? ` · ${number(run.targetLitres)} L` : ""}` : "Run target not reported"}</p>
    <ActualTiming run={run} asOf={asOf} conflict={conflict} />
    {run.recordedRunningMinutes != null && <small>Factory counter for completed segments: {formatDuration(run.recordedRunningMinutes / 60)}. This excludes the open segment and may round down.</small>}
    {current && <p><strong>Factory-confirmed finish time: Not supplied</strong>Filling estimates above exclude stops and waiting.</p>}
    {explanation && <p><strong>Reason given by Daman:</strong> {explanation.reason}</p>}
    <small>Recorded output may be incomplete.</small>
  </div>;
}
export default function LiveShiftBoard() {
  const [board, setBoard] = useState<ShiftBoard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());
  const [busy, setBusy] = useState(false);
  const refreshRef = useRef<() => void>(() => {});
  useEffect(() => {
    let alive = true, pending = false;
    let controller: AbortController | null = null;
    async function refresh() {
      if (pending) return;
      pending = true; setBusy(true);
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller?.abort(), 25000);
      try {
        const response = await fetch("/api/shift-board", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("The live update failed. Previous readings are kept below with their original time.");
        const next: unknown = await response.json(); validateShiftBoard(next);
        if (alive) { setBoard(next); setError(null); setNow(Date.now()); }
      } catch (e) { if (alive) setError(e instanceof Error && e.name !== "AbortError" ? e.message : "Live update timed out. Previous readings are retained; advice needs rechecking."); }
      finally { window.clearTimeout(timeout); pending = false; if (alive) setBusy(false); }
    }
    refreshRef.current = () => { void refresh(); };
    void refresh();
    const timer = window.setInterval(() => { if (document.visibilityState === "visible") void refresh(); }, 30000);
    const clock = window.setInterval(() => setNow(Date.now()), 1000);
    const visible = () => { if (document.visibilityState === "visible") void refresh(); };
    document.addEventListener("visibilitychange", visible);
    window.addEventListener("online", visible);
    return () => { alive = false; controller?.abort(); clearInterval(timer); clearInterval(clock); document.removeEventListener("visibilitychange", visible); window.removeEventListener("online", visible); };
  }, []);
  const fresh = board ? displayFresh(board, !!error, now) : false;
  const today = board?.date === istDate(now);
  return <section className="live-shift" aria-labelledby="live-shift-title">
    <div className="live-shift-heading"><div><div className="live-kicker"><span className={fresh ? "live-dot" : "live-dot stale"} /> {fresh ? "Latest factory report" : "Waiting for verified live status"}</div><h2 id="live-shift-title">Running now · plan · what to do next</h2><p>Factory status is checked every minute. This view checks for updates every 30 seconds.</p></div><button type="button" className="subtle-button" onClick={() => refreshRef.current()} disabled={busy}>{busy ? "Checking…" : "Refresh now"}</button></div>
    <div className="live-times"><span>Factory read: <strong>{time(board?.factory.asOf)}</strong> · {age(board?.factory.asOf, now)}</span><span>Advice checked: <strong>{time(board?.generatedAt)}</strong></span></div>
    <p className="live-baseline">{board?.baseline && today ? <>Original plan saved at <strong>{time(board.baseline.capturedAt)}</strong> on {board.baseline.date}. {board.baseline.captureKind === "first_capture" ? "First capture today; earlier plans were not recorded." : "Start-of-day capture."} This stays fixed for everyone while the factory report and advice update.</> : board?.baselineError || "Loading today's shared original plan…"}</p>
    {error && <p className="notice warning" role="status">{error}</p>}
    {board && !today && <p className="notice warning">These retained readings are from {board.date}. Today's comparison is waiting for an update.</p>}
    {board && !fresh && <p className="notice warning">{board.factory.error || "Factory status is stale or unavailable."} Do not act on retained recommendations without checking the floor.</p>}
    {!board ? <p className="live-loading" role="status">{error ? "Live comparison unavailable. Retrying automatically." : "Reading the factory and today's saved plan…"}</p> : <div className="live-table">{board.rows.map(row => {
      const active = row.actual.runs.filter(r => r.date === board.date && r.activeSegment?.isActive && !r.activeSegment.endedAt && r.liveStatus === "RUNNING");
      const latest = row.actual.runs.filter(r => r.date === board.date && r.liveStatus !== "NOT_STARTED" && r.liveStatus !== "DRAFT" && !r.activeSegment?.isActive).sort((a, b) => (Date.parse(b.sourceUpdatedAt || "") || 0) - (Date.parse(a.sourceUpdatedAt || "") || 0))[0];
      const reliable = fresh && row.actual.coverage === "reported" && row.advice.action !== "cannot_verify";
      const candidate = row.advice.candidate;
      const conflict = row.actual.coverage === "conflict" || timingOverlaps(row.actual.runs.filter(run => run.date === board.date), board.factory.asOf);
      return <article className="live-machine" key={row.line}>
        <div className="live-machine-name"><h3>{row.line}</h3><span className="live-match">{row.match === "matches" ? "In the saved plan" : row.match === "different" ? "Different from plan" : row.match === "not_planned" ? "No saved run" : "Match unverified"}</span></div>
        <div className="live-cell">
          <h4 className="live-column-label">Running now</h4>
          <span className={`live-status ${row.actual.status === "RUNNING" && reliable ? "running" : ""}`}>{!fresh ? "Status unverified" : row.actual.coverage === "conflict" ? "Conflicting reports" : row.actual.coverage === "unreported" ? "Not reported" : row.actual.status === "RUNNING" ? "Factory reports running" : row.actual.status.replaceAll("_", " ").toLowerCase()}</span>
          {active.map(run => <FactoryRunBar key={run.id} run={run} current reliable={reliable} asOf={board.factory.asOf} conflict={conflict} line={row.line} />)}
          {!active.length && <><p className="live-empty-note">{row.actual.status === "STOPPED" || row.actual.status === "COMPLETED" ? "No active production segment reported." : "No single active run is confirmed."}</p>{latest && <FactoryRunBar run={latest} current={false} reliable={reliable} asOf={board.factory.asOf} conflict={conflict} line={row.line} />}</>}
          <details><summary>Factory records today</summary><p>{row.actual.note}</p>{row.actual.runs.map(run => <p key={run.id}>{run.product || run.code || "Unknown SKU"} · {run.liveStatus} · {run.producedPieces === null ? "quantity unavailable" : `${number(run.producedPieces)} pieces`}<br/><small>{run.quantityBasis}</small><br/><small>Run edited {time(run.sourceUpdatedAt)} · {age(run.sourceUpdatedAt, now)}</small></p>)}</details>
        </div>
        <div className="live-cell">
          <h4 className="live-column-label">Original daily plan</h4>
          <span className="live-bar-meta">{board.baseline && today ? `${board.baseline.date} · saved plan` : "Saved plan unavailable"}</span>
          {today && board.baseline ? row.plannedRuns.length ? row.plannedRuns.map((run, i) => { const progress = row.plannedProgress[i]; return <div className="live-run-bar planned" key={`${run.code}-${i}`}>
            <strong>{run.product}</strong><code>{run.code}</code>
            <p>{number(run.pieces)} pieces · {number(run.litres)} L planned</p>
            <PlannedTiming run={run} />
            <small>{progress?.madePieces === null || !progress ? "Since-save progress unavailable" : `${number(progress.madePieces)} made since save · ${number(progress.remainingPieces ?? 0)} left against this plan`}</small>
          </div>; }) : <div className="live-run-bar muted">No run in the saved daily plan.</div> : <div className="live-run-bar muted">Today's original plan is unavailable.</div>}
        </div>
        <div className="live-cell live-advice">
          <h4 className="live-column-label">Recommendation</h4>
          <div className="live-advice-status"><strong className="live-advice-title">{fresh ? row.advice.title : "Recheck before acting"}</strong>{row.advice.conditional && <span className="live-conditional">Needs confirmation</span>}</div>
          {candidate ? <div className={`live-run-bar ${fresh ? "recommended" : "muted"}`}>
            <strong>{candidate.product}</strong><code>{candidate.code}</code>
            <p>Up to {number(candidate.pieces)} pieces · {number(candidate.litres)} L in the next batch</p>
            <p>Estimated filling: {formatDuration(candidate.hours)}</p>
            <p>Setup: {candidate.setupHours === null ? "Unknown — confirm with operator" : formatDuration(candidate.setupHours)}</p>
            {candidate.setupHours !== null && <p>Estimated total line time: {formatDuration(candidate.hours + candidate.setupHours)}</p>}
            <p className="live-demand-split"><span>{number(candidate.confirmedPieces)} for open orders</span><span>{number(candidate.forecastPieces)} forecast / monthly reserve</span></p>
          </div> : <div className="live-run-bar muted">{fresh ? row.advice.reason : "Wait for a fresh reading or confirm with the floor operator."}</div>}
          <details><summary>Why · source times · checks</summary><p>{fresh ? row.advice.reason : "This recommendation was calculated earlier. Wait for a fresh reading or confirm it with the floor operator."}</p>{candidate && <><p>{candidate.reason}</p><p>Recorded stock only; shared materials and space reserved across these suggestions.</p></>}{row.advice.limitations.map((s, i) => <p key={i}>{s}</p>)}{row.advice.basedOn.map((s, i) => <p key={`s-${i}`}>{s.source}: {time(s.asOf)} · {age(s.asOf, now)} · {s.status}</p>)}</details>
        </div>
      </article>;
    })}</div>}
    <p className="live-footnote">Factory reports come from ji.jivo.in; they are operator records, not machine sensors. Advice supports the next decision and does not change the factory schedule automatically.</p>
  </section>;
}
