// One day of the build list, in the voice of out/build-list-sep.json's sample
// lines: per machine, runs in sequence, changeover callouts between them.
// Server component — no client JS; the picker only toggles visibility.

import Link from "next/link";
import SimBadge from "@/components/SimBadge";
import { fmt, money } from "@/lib/data";
import type { BuildDay } from "@/lib/types";

export default function BuildDaySection({ n, day }: { n: number; day: BuildDay }) {
  const allRuns = day.machines.flatMap((m) => m.runs);
  const runsN = allRuns.length;
  const oilN = allRuns.filter((r) => r.changeover_before?.kind === "OIL CHANGE").length;
  const poN = allRuns.filter((r) => r.po_backed).length;
  const unblocked = ((day.news?.unblocked as unknown[]) ?? []).map(String);
  const hasNews = (day.news?.materials_landed ?? 0) > 0 || unblocked.length > 0;

  return (
    <section className="bl-day mt-5 rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      {/* header, in the list's own voice */}
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <div className="font-mono text-sm sm:text-[15px] text-amber-300">
          {day.working ? (
            <>
              GAUTAM — {day.date} ({day.weekday}) ka plan: {fmt(day.made_litres)} L, lines {day.line_util}%
            </>
          ) : (
            <span className="text-zinc-500">
              GAUTAM — {day.date} ({day.weekday}): {day.note ?? "plant off"}
            </span>
          )}{" "}
          <SimBadge kind="plan" />
        </div>
        {day.working && (
          <div className="text-xs text-zinc-500 tabular-nums flex items-center gap-2 flex-wrap">
            <span>{money(day.made_value)}</span>
            <span>· {runsN} runs</span>
            <span>· {oilN} oil changes</span>
            <span>
              · {poN}/{runsN} PO-backed
            </span>
            <Link
              href={`/days/${n}`}
              className="bl-noprint px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
            >
              Full day →
            </Link>
          </div>
        )}
      </div>

      {/* overnight news — the plan below already reflects it */}
      {hasNews && (
        <div className="mt-3 rounded-lg border border-sky-500/25 bg-sky-500/[0.06] p-3 text-xs">
          <div className="font-semibold text-sky-300 uppercase tracking-wide text-[10px]">
            Plan changed — POs landed overnight
          </div>
          <div className="mt-1.5 space-y-1 text-zinc-300">
            {(day.news?.materials_landed ?? 0) > 0 && (
              <div>
                {day.news.materials_landed} material deliveries land this morning (supply-on-lead-time assumption{" "}
                <SimBadge kind="assumed" />) — today&rsquo;s sequence already counts them.
              </div>
            )}
            {unblocked.length > 0 && (
              <div className="text-emerald-300">
                Back in play: {unblocked.join(", ")} — SKUs these were blocking can run again.
              </div>
            )}
            {((day.news?.real_pos_entering ?? 0) > 0 || (day.news?.forecast_rows ?? 0) > 0) && (
              <div className="text-zinc-500">
                Demand entering the book today:{" "}
                {(day.news?.real_pos_entering ?? 0) > 0 && <>{fmt(day.news.real_pos_entering)} real order lines</>}
                {(day.news?.real_pos_entering ?? 0) > 0 && (day.news?.forecast_rows ?? 0) > 0 && " · "}
                {(day.news?.forecast_rows ?? 0) > 0 && (
                  <>
                    {day.news.forecast_rows} forecast rows <SimBadge kind="forecast" />
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {!day.working ? (
        <p className="mt-3 text-sm text-zinc-500">{day.note ?? "Plant off."} No runs are scheduled.</p>
      ) : (
        day.machines.map((m) => (
          <div key={m.machine} className="mt-4">
            <div className="flex items-baseline gap-2 border-b border-zinc-800 pb-1">
              <span className="font-semibold text-zinc-100">{m.machine}</span>
              <span className="text-xs text-zinc-500 tabular-nums">{m.hours_used.toFixed(1)} h</span>
            </div>
            <div className="font-mono text-[12.5px] leading-relaxed mt-2 space-y-1">
              {m.runs.map((r) => (
                <div key={r.seq}>
                  {r.changeover_before && (
                    <div
                      className={`pl-4 ${
                        r.changeover_before.kind === "OIL CHANGE" ? "text-amber-400/90" : "text-zinc-500"
                      }`}
                    >
                      ↻ {r.changeover_before.kind} {r.changeover_before.minutes} min — {r.changeover_before.note}
                    </div>
                  )}
                  <div className="pl-4 text-zinc-300">
                    <span className="text-zinc-500 tabular-nums">{r.seq}.</span>{" "}
                    <span className="text-zinc-100">{r.sku}</span>
                    <span className="text-zinc-500"> — {r.oil_name ?? "no oil line"} — </span>
                    <span className="tabular-nums">
                      {fmt(r.pieces)} pcs = {fmt(r.litres)} L ({r.hours.toFixed(2)}h)
                    </span>
                    {r.po_backed && (
                      <span className="ml-2 text-[10px] px-1.5 py-px rounded border border-emerald-500/40 text-emerald-300 bg-emerald-500/10">
                        PO-backed
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </section>
  );
}
