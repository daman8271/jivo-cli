"use client";
import { useEffect, useRef, useState } from "react";
import { deriveTodayReview } from "@/lib/today-review";
import { istDate } from "@/lib/shift-validation";
import { validReviewDate, validateTodayReview, type TodayReviewData } from "@/lib/today-review-validation";
import { MIN_NEW_CAMPAIGN_HOURS } from "@/lib/rules";
import { formatDuration, formatSetupDuration } from "@/lib/duration";
import reviewExplanations from "@/data/review-explanations.json";
import { ActualTiming, PlannedTiming } from "./RunTiming";
import SavedIdleReasons from "./SavedIdleReasons";
const number = (n: number) => Math.round(n).toLocaleString("en-IN");
const time = (value: string | null | undefined) => value && Number.isFinite(Date.parse(value)) ? new Date(value).toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hour12: false }) + " IST" : "not recorded";
const dateLabel = (date: string) => new Date(`${date}T12:00:00+05:30`).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "numeric", month: "long", year: "numeric" });
const possibleReason = {
  same_line: "The factory may have shared the plan's product and machine preference. The operator's selection reason was not captured.",
  other_line: "The factory may have prioritized the same product on an available machine. Availability, setup and urgent instructions at decision time were not captured.",
  not_in_plan: "An earlier customer instruction or floor constraint may explain this choice; neither was captured with the saved plan.",
  unknown: "SKU identity or the saved plan is missing, so a product-specific explanation cannot be established.",
};
const overlapLabel = { same_line: "Same product and machine in saved plan", other_line: "Same product planned on another machine", not_in_plan: "Product not scheduled in saved plan", unknown: "Product overlap cannot be checked" };
export default function TodayReview() {
  const [date, setDate] = useState(() => {
    const requested = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("reviewDate");
    return requested && validReviewDate(requested) ? requested : istDate();
  });
  useEffect(() => {
    const url = new URL(window.location.href); url.searchParams.set("reviewDate", date);
    window.history.replaceState(window.history.state, "", url);
  }, [date]);
  const [data, setData] = useState<TodayReviewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [factoryFailed, setFactoryFailed] = useState(false);
  const [now, setNow] = useState(Date.now());
  const refreshRef = useRef<() => void>(() => {});
  useEffect(() => {
    let alive = true, pending = false;
    let controller: AbortController | null = null;
    setData(null); setError(null); setFactoryFailed(false);
    async function refresh() {
      if (pending) return;
      pending = true; setBusy(true); controller = new AbortController();
      const timeout = window.setTimeout(() => controller?.abort(), 25000);
      try {
        const response = await fetch(`/api/today-review?date=${encodeURIComponent(date)}`, { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("The review update failed. Retained records keep their original date and time.");
        const next: unknown = await response.json(); validateTodayReview(next, date);
        if (alive) {
          setData(previous => ({ ...next, factory: next.factory ?? previous?.factory ?? null, baseline: next.baseline ?? previous?.baseline ?? null }));
          setFactoryFailed(!!next.factoryError); setError(next.factoryError || next.baselineError); setNow(Date.now());
        }
      } catch (e) { if (alive) { setFactoryFailed(true); setError(e instanceof Error && e.name !== "AbortError" ? e.message : "The review update timed out. Retained records are not a new observation."); } }
      finally { clearTimeout(timeout); pending = false; if (alive) setBusy(false); }
    }
    refreshRef.current = () => { void refresh(); }; void refresh();
    const refreshTimer = window.setInterval(() => { if (document.visibilityState === "visible") void refresh(); }, 60000);
    const clockTimer = window.setInterval(() => setNow(Date.now()), 1000);
    const visible = () => { if (document.visibilityState === "visible") void refresh(); };
    document.addEventListener("visibilitychange", visible); window.addEventListener("online", visible);
    return () => { alive = false; controller?.abort(); clearInterval(refreshTimer); clearInterval(clockTimer); document.removeEventListener("visibilitychange", visible); window.removeEventListener("online", visible); };
  }, [date]);
  const today = istDate(now);
  const review = data?.date === date && data.factory ? deriveTodayReview(data.factory, data.baseline, date, now, factoryFailed) : null;
  const baseline = review?.baseline ?? (data?.date === date ? data.baseline : null);
  return <section className="today-review" aria-labelledby="today-review-title">
    <div className="review-heading"><div><p className="eyebrow">{date === today ? "Today's factory review" : "Historical factory review"} · {dateLabel(date)}</p><h1 id="today-review-title">Actual production vs saved plan</h1><p>What the factory recorded, what MARK IV had saved, and what this evidence can tell us.</p></div><a className="text-button" href="#today">Back to shift board</a></div>
    <div className="review-controls"><label>Review date <input type="date" value={date} min="2026-09-01" max={today} onChange={e => { if (e.target.value && e.target.value <= today && e.target.value >= "2026-09-01") setDate(e.target.value); }} /></label><button className="subtle-button" onClick={() => setDate(istDate(now - 86400000))}>Yesterday</button><button className="subtle-button" onClick={() => setDate(today)}>Today</button><button className="subtle-button" disabled={busy} onClick={() => refreshRef.current()}>{busy ? "Checking…" : "Refresh review"}</button></div>
    {date !== today && <p className="notice">This is the dated record for {dateLabel(date)}. Today is {dateLabel(today)}. Historical output is the last archived reading, which may be before the shift ended.</p>}
    {error && <p className="notice warning" role="status">{error}</p>}
    {review && <p className="review-source">Factory observation: <strong>{dateLabel(date)} at {time(data?.factory?.asOf)}</strong> · {review.isToday ? review.fresh ? "Fresh reading · refreshed every minute" : "Reading stale or unavailable; retained evidence only" : "Archived reading; no claim of final shift totals"}. ji.jivo.in production execution records, Oil scope.</p>}
    <div className="review-verdict"><div><span className="eyebrow">Which choice was better?</span><h2>Not established</h2></div><div>
      {baseline ? <><p>Saved plan: <strong>{dateLabel(baseline.date)} at {time(baseline.capturedAt)}</strong>. {baseline.captureKind === "first_capture" ? "First capture; no earlier plan was recorded by this service." : "Marked as a start-of-day capture."}</p>
      {review?.lateCapture ? <p><strong>Saved after production had already begun.</strong> This is not an earlier daily recommendation. Product overlap is descriptive; it does not prove the factory followed the plan.</p> : review?.beforeRecordedActivity ? <p>The save precedes the first starts in these records. That establishes sequence only, not whether the plan caused the choices or was better.</p> : <p>The available timing evidence cannot establish that this plan was saved before production began.</p>}
      <p>{baseline.factoryAtCapture ? "Factory counters were saved with this plan, but a fair assessment still needs matching time windows and verified constraints." : "No factory output counters were saved at capture. Today's output cannot be subtracted from this saved plan to calculate attainment or missed production."}</p></> : <p>{data?.baselineError || "Reading the saved plan…"}</p>}
      <p>Historical entries preserve earlier recommendations and may predate fixes; use the shift board for current advice.</p><p>Actual product-selection reasons, urgent customer instructions, QC releases and available space at decision time are not recorded here. Material availability uses MARK IV warehouse rules; warehouse scope is under reconciliation. We cannot rank feasibility, profit or productivity from these records.</p>
    </div></div>
    {review ? <>
      <div className="review-summary"><div><span>Recorded segment output</span><strong>{review.knownLitres === null ? "Unknown" : `${number(review.knownLitres)} L`}</strong><p>Known subtotal across {number(review.startedRuns)} started run records. {review.missingQuantityRuns ? `${number(review.missingQuantityRuns)} have unknown litres.` : "Entered quantities only."} Zero entered does not prove zero production.</p></div><div><span>Product overlap on the same machine</span><strong>{baseline ? `${review.matchedProducts} / ${review.recordedProducts}` : "Unknown"}</strong><p>Distinct product + machine pairs among started records, including verified carton substitutions. {review.unknownSkuRuns > 0 && `${review.unknownSkuRuns} records have unknown SKU identity.`} No output-attainment percentage.</p></div><div><span>Coverage</span><strong>{review.unreportedLines ? `${review.unreportedLines} lines need checking` : "Listed lines reported"}</strong><p>MES records cover part of the plant. This is not total factory production; receipts and report-header totals are not added or treated as reconciled.</p></div></div>
      {review.timingConflict && <p className="notice warning">Recorded segments overlap on a machine or contain reversed times. Timing needs checking; hours, speed and a productivity winner cannot be established from these entries.</p>}
      <div className="review-lines">{review.rows.map(row => <article className="review-line" key={row.line}><header><h2>{row.line}</h2><span>{row.coverage === "reported" ? "Dated factory records" : row.coverage === "conflict" ? "Conflicting records — verify" : "Not reported — not proof of idle time"}</span></header><div className="review-columns"><div><h3>What ran · recorded output</h3>
        {row.products.length ? row.products.map(({ run, overlap, cartonMapping }) => <div className="review-product" key={run.id}><strong>{run.product || "Product not reported"}</strong><code>{run.code || "SKU unknown"}</code><p>{run.producedPieces === null ? "Pieces unknown" : run.producedPieces === 0 ? "0 recorded; output may not have been entered" : `${number(run.producedPieces)} pieces recorded`}{run.producedLitres !== null ? ` · ${number(run.producedLitres)} L` : " · litres unknown"}</p><p className="review-overlap">{overlapLabel[overlap]}</p>{cartonMapping && <p>Verified equivalent packs: {cartonMapping.old_pieces_per_case} and {cartonMapping.new_pieces_per_case} pieces per carton. Same oil and bottle size; carton requirements differ.{overlap === "not_in_plan" ? " Neither pack variant was scheduled in this saved plan." : ""}</p>}{reviewExplanations.find(note => note.date === date && note.line === row.line && note.code === run.code) ? <p><strong>Reason given by Daman:</strong> {reviewExplanations.find(note => note.date === date && note.line === row.line && note.code === run.code)!.reason}</p> : <p><strong>Possible reason — unconfirmed:</strong> {possibleReason[overlap]}</p>}<ActualTiming run={run} asOf={data?.factory?.asOf ?? null} conflict={row.timingConflict || row.coverage === "conflict"} />
        </div>) : <p>No started run is established in these records. This does not prove no production.</p>}
        {!!row.drafts.length && <details><summary>{row.drafts.length} not-started draft records · excluded from output and overlap</summary>{row.drafts.map(run => <p key={run.id}>{run.product || run.code || "Unknown product"} · not started</p>)}</details>}
        {!!row.unknown.length && <p>{row.unknown.length} additional records have unverified start status and are excluded.</p>}
        {row.timingConflict && <p className="review-caution">Overlapping or reversed timing records on this machine; no measured productivity comparison.</p>}
      </div><div><h3>What the saved plan contained</h3>{!baseline ? <p>Saved plan unavailable.</p> : row.planned.length ? row.planned.map((run, i) => <div className="review-product" key={`${run.code}-${i}`}><strong>{run.product}</strong><code>{run.code}</code><p>{number(run.pieces)} pieces · {number(run.litres)} L in the archived plan</p><PlannedTiming run={run} /><p>{run.reason || "Selection reason was not saved."}</p>{run.setupHours > 0 && run.hours < MIN_NEW_CAMPAIGN_HOURS && <p className="review-caution">This saved snapshot used an earlier batch rule; current planning requires a viable campaign. The archive is unchanged.</p>}<details><summary>Saved planning assumptions</summary><p>{number(run.confirmedPieces)} pieces for open orders · {number(run.forecastPieces)} forecast / reserve</p><p>Planned filling {formatDuration(run.hours)} · setup {formatSetupDuration(run)}. These are planned durations, not measured actual work.</p><p>{run.value === null ? "Selling worth unavailable." : `Estimated selling worth ₹${number(run.value)}; not profit or realized sales.`}</p><p>{run.rate?.source || "Rate basis not recorded"}</p><p>{run.conditionalRecipe || run.conditionalSupply ? "This run depended on conditional recipe or supply assumptions." : "Subject to the saved stock and warehouse assumptions."}</p><p>{run.materials?.length || 0} material requirements saved; availability at the factory's decision time has not been established.</p></details></div>) : <><p>No run saved for this machine.</p><SavedIdleReasons blockers={row.blockers} storage={baseline.day.storage} /></>}</div></div></article>)}</div>
    </> : <p className="live-loading" role="status">{busy ? "Reading dated factory output and the saved plan…" : data?.factoryError || "Factory review unavailable. Retrying automatically."}</p>}
    {baseline && <details className="review-provenance"><summary>Saved version and evidence</summary><p>Capture {baseline.id}</p><p>Engine {baseline.engineVersion} · input revision {baseline.inputRevision}</p><p>Input date/time {baseline.inputAsOf} · source status {baseline.feedStatus}</p><p>Historical entries preserve earlier recommendations and may predate fixes; they are not the current engine’s recommendations. The archived plan is immutable. A current rerun or browser scenario does not change this comparison.</p></details>}
    <p className="review-links"><a href="https://ji.jivo.in/production/execution" target="_blank" rel="noreferrer">Factory execution</a><a href="https://ji.jivo.in/production/execution/reports/daily" target="_blank" rel="noreferrer">Dated factory report</a><a href="#actuals">What happened · receipts and history</a></p>
  </section>;
}
