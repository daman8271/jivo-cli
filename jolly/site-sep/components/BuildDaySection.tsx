// One day of the run list, in the voice of out/build-list-sep.json's sample
// lines: per machine, runs in order, oil changes called out between them.
// Server component — no client JS; the picker only toggles visibility.

import Link from "next/link";
import SimBadge from "@/components/SimBadge";
import { dlabel, fmt, money, plainWords, plural } from "@/lib/data";
import type { BuildDay, BuildRun } from "@/lib/types";

type Rules = { flush_litres: number; line_clearance_min: number };
type Changeover = NonNullable<BuildRun["changeover_before"]>;

// The changeover line, in plain words. build.json carries the kind, the minutes
// and a note such as "flush 400 L SEASAME OIL (~9 min, oil reused) + 51.3 min
// line clearance — MUSTARD LOOSE OIL → SEASAME OIL". Nothing is retyped: the
// oils are read out of the record (the note, or the runs either side) and the
// litres come from the plan's rules.
function changeoverText(c: Changeover, prevOil: string | null, run: BuildRun, rules: Rules): string {
  if (c.kind === "OIL CHANGE") {
    const arrow = c.note.match(/—\s*(.+?)\s*→\s*(.+?)\s*$/);
    const from = prevOil ?? arrow?.[1] ?? null;
    const to = run.oil_name ?? arrow?.[2] ?? "the next oil";
    const path = from ? `${from} → ${to}` : `to ${to}`;
    return `OIL CHANGE ${c.minutes} min — ${path} (wash with ${fmt(rules.flush_litres)} L of ${to}, then cleaning)`;
  }
  if (/line start/i.test(c.note)) return `MACHINE START ${c.minutes} min — cleaning before the first run`;
  if (/pack-size|same oil/i.test(c.note)) return `BOTTLE SIZE CHANGE ${c.minutes} min — same oil, cleaning only`;
  return `CLEANING ${c.minutes} min`;
}

export default function BuildDaySection({ n, day, rules }: { n: number; day: BuildDay; rules: Rules }) {
  const allRuns = day.machines.flatMap((m) => m.runs);
  const runsN = allRuns.length;
  const oilN = allRuns.filter((r) => r.changeover_before?.kind === "OIL CHANGE").length;
  const poN = allRuns.filter((r) => r.po_backed).length;
  const unblocked = ((day.news?.unblocked as unknown[]) ?? []).map(String);
  const hasNews = (day.news?.materials_landed ?? 0) > 0 || unblocked.length > 0;
  const when = `${day.weekday} ${dlabel(day.date)}`;

  return (
    <section className="bl-day mt-5 rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      {/* header, in the list's own voice */}
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <div className="font-mono text-sm sm:text-[15px] text-amber-300">
          {day.working ? (
            <>
              GAUTAM — {when} ka plan: {fmt(day.made_litres)} L, machines {day.line_util}% busy
            </>
          ) : (
            <span className="text-zinc-500">
              GAUTAM — {when}: {plainWords(day.note ?? "factory closed")}
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
              · {poN} of {runsN} have a customer order
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

      {/* overnight news — the plan below already counts it */}
      {hasNews && (
        <div className="mt-3 rounded-lg border border-sky-500/25 bg-sky-500/[0.06] p-3 text-xs">
          <div className="font-semibold text-sky-300 uppercase tracking-wide text-[10px]">
            Plan changed — material arrived overnight
          </div>
          <div className="mt-1.5 space-y-1 text-zinc-300">
            {(day.news?.materials_landed ?? 0) > 0 && (
              <div>
                {day.news.materials_landed} material deliveries arrive this morning. Our guess — they come exactly on
                time, nobody has confirmed. Today&rsquo;s list already counts them.
              </div>
            )}
            {unblocked.length > 0 && (
              <div className="text-emerald-300">
                Arrived: {unblocked.join(", ")} — the products these were holding up can run again.
              </div>
            )}
            {((day.news?.real_pos_entering ?? 0) > 0 || (day.news?.forecast_rows ?? 0) > 0) && (
              <div className="text-zinc-500">
                New today:{" "}
                {(day.news?.real_pos_entering ?? 0) > 0 && (
                  <>{fmt(day.news.real_pos_entering)} confirmed customer order {plural(day.news.real_pos_entering, "line", "lines")}</>
                )}
                {(day.news?.real_pos_entering ?? 0) > 0 && (day.news?.forecast_rows ?? 0) > 0 && " · "}
                {(day.news?.forecast_rows ?? 0) > 0 && (
                  <>
                    {day.news.forecast_rows} order {plural(day.news.forecast_rows, "line", "lines")}{" "}
                    <span className="px-1 py-px rounded border border-sky-500/40 text-sky-300 bg-sky-500/10">
                      expected — not ordered yet
                    </span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {!day.working ? (
        <p className="mt-3 text-sm text-zinc-500">{plainWords(day.note ?? "Factory closed.")} Nothing to run.</p>
      ) : (
        day.machines.map((m) => (
          <div key={m.machine} className="mt-4">
            <div className="flex items-baseline gap-2 border-b border-zinc-800 pb-1">
              <span className="font-semibold text-zinc-100">{m.machine}</span>
              <span className="text-xs text-zinc-500 tabular-nums">{m.hours_used.toFixed(1)} h</span>
            </div>
            <div className="font-mono text-[12.5px] leading-relaxed mt-2 space-y-1">
              {m.runs.map((r, i) => (
                <div key={r.seq}>
                  {r.changeover_before && (
                    <div
                      className={`pl-4 ${
                        r.changeover_before.kind === "OIL CHANGE" ? "text-amber-400/90" : "text-zinc-500"
                      }`}
                    >
                      ↻ {changeoverText(r.changeover_before, i > 0 ? m.runs[i - 1].oil_name : null, r, rules)}
                    </div>
                  )}
                  <div className="pl-4 text-zinc-300">
                    <span className="text-zinc-500 tabular-nums">{r.seq}.</span>{" "}
                    <span className="text-zinc-100">{r.sku}</span>
                    <span className="text-zinc-500"> — {r.oil_name ?? "no oil named"} — </span>
                    <span className="tabular-nums">
                      {fmt(r.pieces)} pcs = {fmt(r.litres)} L ({r.hours.toFixed(2)}h)
                    </span>
                    {r.po_backed && (
                      <span className="ml-2 text-[10px] px-1.5 py-px rounded border border-emerald-500/40 text-emerald-300 bg-emerald-500/10">
                        has a customer order
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
