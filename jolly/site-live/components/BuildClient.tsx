"use client";

// /build — what Gautam is running RIGHT NOW, beside what the plan would run.
//
// The two halves come from two different worlds and they are never blended:
//   left   factory_production.running_now — the MES, minutes old
//   right  plan/days/day-01.json runs     — what the planner decided from it
// Where they disagree the row is marked. A planner that hides the disagreement
// is a planner nobody checks.

import { asDay, asHonesty, asOverview, asState, dayId, useLive } from "../lib/live";
import { isRealiseOutlier, maskDigits, prefWords, realiseOutlier } from "../lib/labels";
import { inr, litres, money, orUnknown, plural } from "../lib/fmt";
import { AsOf, Live, LiveSource, SourceLine } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";
import type { PlanRun, RunNow } from "../lib/types";

const TODAY = dayId(1);

export default function BuildClient() {
  const live = useLive(["state", TODAY, "honesty", "overview"]);
  const st = asState(live.state);
  const day = asDay(live[TODAY]);
  const h = asHonesty(live.honesty);
  const o = asOverview(live.overview);
  const outlier = realiseOutlier(h);
  // the one machine allowed a second session tonight, from the plan itself
  const night = o?.night_line ?? day?.night_line ?? null;

  const prod = st?.factory_production;
  const running: RunNow[] = prod?.running_now ?? [];
  const byLineToday = prod?.by_line_today ?? {};

  // Every line either half knows about, in one list.
  const lines = Array.from(
    new Set([...Object.keys(byLineToday), ...running.map((r) => r.line), ...(day?.runs ?? []).map((r) => r.line)]),
  ).sort();

  const planByLine = new Map<string, PlanRun[]>();
  for (const r of day?.runs ?? []) planByLine.set(r.line, [...(planByLine.get(r.line) ?? []), r]);
  const nowByLine = new Map<string, RunNow[]>();
  for (const r of running) nowByLine.set(r.line, [...(nowByLine.get(r.line) ?? []), r]);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Running now</h1>
        <SimBadge kind="live" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        On the left, what is actually on each machine — read off the factory app minutes ago. On the right, what the
        planner would put there. Where they differ the row says so.
      </p>

      <div className="mt-6 grid gap-3 md:grid-cols-3">
        <Panel title="On a machine right now" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_production" />}>
          <LiveSource src="factory_production" what="the machines">
            <div className="text-2xl font-semibold tabular-nums text-emerald-300">
              {running.length} {plural(running.length, "machine", "machines")}
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              filled today {orUnknown(prod?.made_today_l, litres)} · {orUnknown(prod?.made_today_cases, (v) => `${inr(v)} cases`)}
            </div>
          </LiveSource>
        </Panel>

        <Panel title="Booked into the godown today" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_production" />}>
          <LiveSource src="factory_production" what="the goods receipts">
            <div className="text-2xl font-semibold tabular-nums">
              {orUnknown(prod?.booked_today?.litres, litres)}
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              {orUnknown(prod?.booked_today?.receipts, (v) => `${inr(v)} ${plural(v, "receipt", "receipts")}`)} ·{" "}
              {orUnknown(prod?.booked_today?.value_inr, money)}
            </div>
            {prod?.booked_today?.note && (
              <p className="mt-2 text-xs text-amber-300/70">{maskDigits(prod.booked_today.note)}</p>
            )}
          </LiveSource>
        </Panel>

        <Panel title="The plan for today" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live[TODAY]} />}>
          <Live rec={live[TODAY]} what="today's plan">
            {day && (
              <>
                <div className="text-2xl font-semibold tabular-nums text-violet-300">{litres(day.made_litres)}</div>
                <div className="mt-1 text-xs text-zinc-400">
                  {day.runs.length} {plural(day.runs.length, "run", "runs")} · {day.flushes}{" "}
                  {plural(day.flushes, "oil change", "oil changes")} · machines busy {day.line_util}%
                </div>
              </>
            )}
          </Live>
        </Panel>
      </div>

      {/* ── machine by machine ───────────────────────────────────── */}
      <div className="mt-6 space-y-3">
        {lines.map((line) => {
          const now = nowByLine.get(line) ?? [];
          const plan = planByLine.get(line) ?? [];
          const today = byLineToday[line];
          const nowSkus = new Set(now.map((r) => r.sku_code));
          const planSkus = new Set(plan.map((r) => r.code));
          const agree = now.length > 0 && plan.length > 0 && [...nowSkus].some((c) => planSkus.has(c));
          const differ = now.length > 0 && plan.length > 0 && !agree;

          return (
            <div key={line} className="rounded-xl border border-zinc-800 bg-zinc-900/40">
              <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 px-4 py-2">
                <h3 className="text-sm font-semibold">{line}</h3>
                {now.length > 0 && (
                  <span className="inline-flex items-center gap-1 text-[11px] text-emerald-300">
                    <span className="m3-live inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" /> running
                  </span>
                )}
                {differ && (
                  <Pill tone="amber" title="The machine is not on the product the plan picked. Neither is wrong — the plan is a suggestion; this says they differ.">
                    running something else
                  </Pill>
                )}
                {agree && <Pill tone="green">on plan</Pill>}
                {night?.line === line && (
                  <Pill
                    tone="violet"
                    title={night.reason ? `picked because it has ${maskDigits(night.reason)}` : "the one machine given a second session tonight"}
                  >
                    second session tonight
                  </Pill>
                )}
                {/* right-hand end of the header: today's tally, then this
                    machine's own freshness line — the left half of the panel
                    below is read live off the factory app, so it says when */}
                <span className="ml-auto flex flex-wrap items-center gap-x-3 gap-y-1">
                  {today && (
                    <span className="text-[11px] text-zinc-500">
                      today: {inr(today.cases)} cases · {litres(today.litres)}
                      {today.breakdown_minutes ? ` · ${today.breakdown_minutes} min stopped` : ""}
                    </span>
                  )}
                  <SourceLine src="factory_production" />
                </span>
              </div>

              <div className="grid gap-px bg-zinc-800 md:grid-cols-2">
                {/* NOW */}
                <div className="bg-zinc-900/60 p-3">
                  <div className="mb-2 text-[10px] uppercase tracking-wider text-emerald-400/80">On it now</div>
                  {now.length === 0 ? (
                    <p className="text-sm text-zinc-500">Nothing on this machine at the moment.</p>
                  ) : (
                    <ul className="space-y-2">
                      {now.map((r) => (
                        <li key={r.run_id} className="text-sm">
                          <div className="font-medium">{r.sku}</div>
                          <div className="mt-0.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-400">
                            <span>{inr(r.cases)} cases</span>
                            <span>{litres(r.litres)}</span>
                            {r.running_minutes != null && <span>{r.running_minutes} min in</span>}
                            {r.breakdown_minutes ? <span className="text-red-300">{r.breakdown_minutes} min stopped</span> : null}
                            {r.required_qty != null && <span>asked for {inr(r.required_qty)}</span>}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* PLAN */}
                <div className="bg-zinc-900/40 p-3">
                  <div className="mb-2 text-[10px] uppercase tracking-wider text-violet-400/80">The plan would run</div>
                  {plan.length === 0 ? (
                    <p className="text-sm text-zinc-500">The planner leaves this machine idle today.</p>
                  ) : (
                    <ul className="space-y-2">
                      {plan.map((r, i) => (
                        <li key={`${r.code}-${i}`} className="text-sm">
                          <div className="flex flex-wrap items-baseline gap-2">
                            <span className="font-medium">{r.sku}</span>
                            {nowSkus.has(r.code) && <Pill tone="green">this one is on</Pill>}
                            {isRealiseOutlier(h, r.code) && (
                              <Pill tone="amber" title={outlier.note ?? ""}>
                                odd price — see note
                              </Pill>
                            )}
                          </div>
                          <div className="mt-0.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-400">
                            <span>{inr(r.pieces)} pcs</span>
                            <span>{litres(r.litres)}</span>
                            <span>{r.hours.toFixed(1)} h</span>
                            {r.flush_min > 0 && <span className="text-amber-300">{r.flush_min} min oil change</span>}
                            {r.value != null && <span>{money(r.value)}</span>}
                            {r.family && <span className="text-zinc-500">{r.family}</span>}
                            {r.pref != null && r.pref > 1 && (
                              <span className="text-amber-300" title="every machine it would rather be on was full">
                                {prefWords(r.pref)}
                              </span>
                            )}
                            {r.night && <span className="text-violet-300">on the second session</span>}
                            {r.po_backed === false && <span className="text-violet-300">no order behind it</span>}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        {lines.length === 0 && (
          <Live rec={live.state} what="the machines">
            <p className="text-sm text-zinc-500">No machine list came back this cycle.</p>
          </Live>
        )}
      </div>

      {outlier.note && (
        <p className="mt-4 text-xs text-amber-300/70">
          {outlier.code}: {maskDigits(outlier.note)}
        </p>
      )}
      {prod?.mes_coverage_note && (
        <p className="mt-2 text-xs text-zinc-500">{maskDigits(prod.mes_coverage_note)}</p>
      )}

      {prod?.recent_runs && prod.recent_runs.length > 0 && (
        <div className="mt-6">
          <Panel title="The last few runs the factory app recorded" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_production" />}>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                    <th className="py-1 font-normal">Day</th>
                    <th className="py-1 font-normal">Machine</th>
                    <th className="py-1 font-normal">Product</th>
                    <th className="py-1 font-normal">State</th>
                    <th className="py-1 text-right font-normal">Minutes</th>
                  </tr>
                </thead>
                <tbody>
                  {prod.recent_runs.map((r) => (
                    <tr key={r.run_id} className="border-t border-zinc-800/60">
                      <td className="py-1 text-zinc-400">{r.date ?? "—"}</td>
                      <td className="py-1">{r.line}</td>
                      <td className="py-1 max-w-[22rem] truncate text-zinc-300">{r.sku}</td>
                      <td className="py-1">
                        <Pill tone={r.live_status === "RUNNING" ? "green" : "zinc"}>
                          {(r.live_status ?? r.status ?? "").toLowerCase().replace(/_/g, " ")}
                        </Pill>
                      </td>
                      <td className="py-1 text-right tabular-nums">
                        {r.running_minutes ?? "—"}
                        {r.breakdown_minutes ? <span className="text-red-300"> +{r.breakdown_minutes} stopped</span> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      )}

      <div className="mt-4">
        <Stat k="Stock moved in and out of the godown today" v={orUnknown(prod?.warehouse_flow_today?.entries, (v) => `${inr(v)} moves`)} />
      </div>
    </div>
  );
}
