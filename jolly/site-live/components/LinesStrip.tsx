"use client";

// The overview, line by line — Mark 4's change of shape.
//
// The front page used to be one number for the whole plant. A planner does not
// run a plant, he runs six machines, so this is one strip per machine: what is
// on it right now, what the plan gives it today, how many of its allowed hours
// that fills, and what the factory app has actually recorded against it.
//
// Two worlds meet here and they are joined by NAME:
//   plan   overview.lines_today          — what the planner decided
//   plant  state.factory_production      — what the machine is doing
// A name in one and not the other gets its own row saying exactly that. It is
// never dropped: a machine the plan has never heard of is the most interesting
// row on the page.

import { asOverview, asState, useLive } from "../lib/live";
import { maskDigits, prefWords } from "../lib/labels";
import { inr, litres, money, orUnknown, plural } from "../lib/fmt";
import { AsOf, Live, SourceLine } from "./Freshness";
import { Panel, Pill } from "./Card";
import SimBadge from "./SimBadge";

const hrs = (h: number | null | undefined) =>
  typeof h === "number" && Number.isFinite(h) ? `${h.toFixed(1)} h` : "—";

export default function LinesStrip() {
  const live = useLive(["overview", "state"]);
  const o = asOverview(live.overview);
  const st = asState(live.state);

  const prod = st?.factory_production;
  const byLine = prod?.by_line_today ?? {};
  const runningLines = new Set((prod?.running_now ?? []).map((r) => r.line));
  const planned = o?.lines_today ?? [];
  const night = o?.night_line ?? null;

  // every machine either side knows about, plan order first
  const names = [...planned.map((l) => l.line)];
  for (const n of Object.keys(byLine)) if (!names.includes(n)) names.push(n);

  const maxLitres = Math.max(1, ...planned.map((l) => l.litres));

  return (
    <Live rec={live.overview} what="today's machines">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
            <SimBadge kind="plan" />
            <span>what the planner gives each machine today</span>
            <SimBadge kind="live" />
            <span>what the machine is really doing</span>
          </div>
          <AsOf rec={live.overview} />
        </div>

        {names.map((name) => {
          const p = planned.find((l) => l.line === name) ?? null;
          const today = byLine[name] ?? null;
          const isRunning = runningLines.has(name);
          const isNight = p?.night === true || night?.line === name;
          const fillPct = p ? Math.min(100, (p.litres / maxLitres) * 100) : 0;

          return (
            <div key={name} className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-semibold text-zinc-200">{name}</h3>
                {isRunning && (
                  <Pill tone="green">
                    <span className="m3-live mr-1 inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 align-middle" />
                    running now
                  </Pill>
                )}
                {isNight && (
                  <Pill tone="violet" title={night?.reason ? maskDigits(night.reason) : "the one machine given a second session today"}>
                    second session tonight
                  </Pill>
                )}
                {!p && (
                  <Pill tone="amber" title="the factory app has this machine, the plan does not name it — it is shown rather than dropped">
                    not in the plan today
                  </Pill>
                )}
                {p && !today && (
                  <Pill tone="zinc" title="the plan gives this machine work today; the factory app has recorded nothing on it yet">
                    nothing recorded yet
                  </Pill>
                )}
                <span className="ml-auto">
                  <SourceLine src="factory_production" />
                </span>
              </div>

              {p && (
                <div className="mt-2 h-1.5 overflow-hidden rounded bg-zinc-800">
                  <div className={`h-full ${isNight ? "bg-violet-400" : "bg-violet-500"}`} style={{ width: `${fillPct}%` }} />
                </div>
              )}

              <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-4">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">The plan gives it</div>
                  <div className="tabular-nums text-zinc-100">{p ? litres(p.litres) : "nothing today"}</div>
                  {p && <div className="text-[10px] text-zinc-500">{money(p.value_rs)}</div>}
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">Hours it fills</div>
                  <div className="tabular-nums text-zinc-100">
                    {p ? `${hrs(p.hours_planned)} of ${hrs(p.hours_available)}` : "—"}
                  </div>
                  {p && p.hours_available > p.hours_planned && (
                    <div className="text-[10px] text-zinc-500">
                      {hrs(p.hours_available - p.hours_planned)} standing idle
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">Recorded today</div>
                  <div className="tabular-nums text-zinc-100">
                    {today ? litres(today.litres) : orUnknown(null, litres, "nothing yet")}
                  </div>
                  {today && (
                    <div className="text-[10px] text-zinc-500">
                      {inr(today.cases)} cases · {today.runs} {plural(today.runs, "run", "runs")}
                      {today.breakdown_minutes ? ` · ${today.breakdown_minutes} min stopped` : ""}
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-500">Product changes</div>
                  <div className="tabular-nums text-zinc-100">
                    {p?.product_changes != null ? inr(p.product_changes) : "—"}
                  </div>
                  <div className="text-[10px] text-zinc-500">each one costs an oil change</div>
                </div>
              </div>

              {p?.products && p.products.length > 0 && (
                <ul className="mt-2 space-y-0.5 border-t border-zinc-800 pt-2 text-xs">
                  {p.products.map((pr, i) => (
                    <li key={`${pr.code}-${i}`} className="flex flex-wrap items-baseline gap-x-2">
                      <span className="font-mono text-[11px] text-zinc-500">{pr.code}</span>
                      <span className="text-zinc-300">{pr.sku}</span>
                      {pr.family && (
                        <Pill tone="zinc" title="the bottle or container family the rulebook lets this machine take">
                          {pr.family}
                        </Pill>
                      )}
                      {pr.pref != null && pr.pref > 1 && (
                        <Pill tone="amber" title="it opened here only because every better machine was full">
                          {prefWords(pr.pref)}
                        </Pill>
                      )}
                      {pr.po_backed === false && (
                        <Pill tone="violet" title="no customer order behind it — it is made to the month's target">
                          no order behind it
                        </Pill>
                      )}
                      <span className="ml-auto tabular-nums text-zinc-400">
                        {litres(pr.litres)} · {hrs(pr.hours)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}

        {names.length === 0 && (
          <Panel title="Line by line" asOf={<AsOf rec={live.overview} />}>
            <p className="text-sm text-zinc-500">
              This plan does not break today down machine by machine, and the factory app has no machine list this
              cycle either.
            </p>
          </Panel>
        )}

        {night?.line && (
          <p className="text-xs text-zinc-500">
            Tonight&rsquo;s second session goes to <span className="text-zinc-300">{night.line}</span>
            {night.reason ? ` — ${maskDigits(night.reason)}` : ""}. One machine a day, at most, and the plant can
            overrule it.
          </p>
        )}
      </div>
    </Live>
  );
}
