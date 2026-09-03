"use client";

// /lines — the machines.
//
// NOW: what each machine did today, off the factory app.
// FORWARD: how hard the plan works each one, and on what speed — and the speed
// basis is always on screen, because the three are not the same claim:
//   rated     the machine's listed speed
//   observed  a speed we measured ourselves — then the plan halves it AGAIN
//   derived   worked out from another slot, never measured anywhere

import { asHonesty, asLines, asState, useLive } from "../lib/live";
import { derateRule, maskDigits } from "../lib/labels";
import { inr, litres, money, orUnknown, pct } from "../lib/fmt";
import { AsOf, Live, LiveSource, SourceLine } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

const BASIS: Record<string, { tone: string; words: string }> = {
  rated: { tone: "zinc", words: "the machine's listed speed" },
  observed: { tone: "green", words: "a speed we measured ourselves — then halved again" },
  derived: { tone: "amber", words: "worked out from another slot, never measured" },
};

export default function LinesClient() {
  const live = useLive(["lines", "state", "honesty"]);
  const L = asLines(live.lines);
  const st = asState(live.state);
  const h = asHonesty(live.honesty);
  const derate = derateRule(h);

  const prod = st?.factory_production;
  const byLine = prod?.by_line_today ?? {};
  const runningLines = new Set((prod?.running_now ?? []).map((r) => r.line));

  const maxLitres = Math.max(1, ...(L?.lines ?? []).map((l) => l.litres));

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Machines</h1>
        <SimBadge kind="live" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {derate.text ?? "Every machine is run at a fraction of its listed speed — the pace the plant really keeps."}
      </p>

      {/* ── today, off the factory app ───────────────────────────── */}
      <div className="mt-6">
        <Panel title="What each machine did today" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_production" />}>
          <LiveSource src="factory_production" what="the machines">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                  <th className="py-1 font-normal">Machine</th>
                  <th className="py-1 font-normal">On it</th>
                  <th className="py-1 text-right font-normal">Runs</th>
                  <th className="py-1 text-right font-normal">Cases</th>
                  <th className="py-1 text-right font-normal">Litres</th>
                  <th className="py-1 text-right font-normal">Minutes running</th>
                  <th className="py-1 text-right font-normal">Minutes stopped</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(byLine).map(([name, l]) => (
                  <tr key={name} className="border-t border-zinc-800/60">
                    <td className="py-1">
                      {runningLines.has(name) && (
                        <span className="m3-live mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 align-middle" />
                      )}
                      {name}
                    </td>
                    <td className="py-1 max-w-[22rem] truncate text-zinc-400">
                      {(l.skus ?? []).map((s) => s.sku).join(", ") || "—"}
                    </td>
                    <td className="py-1 text-right tabular-nums">{l.runs}</td>
                    <td className="py-1 text-right tabular-nums">{inr(l.cases)}</td>
                    <td className="py-1 text-right tabular-nums">{inr(l.litres)}</td>
                    <td className="py-1 text-right tabular-nums">{l.running_minutes ?? "—"}</td>
                    <td className={`py-1 text-right tabular-nums ${l.breakdown_minutes ? "text-red-300" : ""}`}>
                      {l.breakdown_minutes ?? "—"}
                    </td>
                  </tr>
                ))}
                {Object.keys(byLine).length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-2 text-zinc-500">
                      No machine has recorded a run today.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            {prod?.mes_coverage_note && (
              <p className="mt-2 text-xs text-amber-300/70">{maskDigits(prod.mes_coverage_note)}</p>
            )}
          </LiveSource>
        </Panel>
      </div>

      {/* ── the plan's use of them ───────────────────────────────── */}
      <div className="mt-4">
        <Live rec={live.lines} what="the machine plan">
          {L && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                <Stat k="Litres the plan fills" v={litres(L.total_litres)} />
                <Stat k="Speed the plan uses" v={pct(L.efficiency * 100)} sub="of the listed speed" />
                {L.measured_slots && L.measured_slots.length > 0 && (
                  <Stat
                    k="Slots we measured ourselves"
                    v={String(L.measured_slots.length)}
                    sub={L.measured_slots.join(", ")}
                  />
                )}
                <span className="ml-auto">
                  <AsOf rec={live.lines} />
                </span>
              </div>
              {L.total_litres_note && <p className="text-xs text-zinc-500">{maskDigits(L.total_litres_note)}</p>}

              {L.lines.map((l) => {
                const live_now = runningLines.has(l.name);
                return (
                  <Panel
                    key={l.name}
                    title={l.name}
                    badge={
                      live_now ? (
                        <Pill tone="green">
                          <span className="m3-live mr-1 inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 align-middle" />
                          running now
                        </Pill>
                      ) : (
                        <SimBadge kind="plan" />
                      )
                    }
                    asOf={<AsOf rec={live.lines} />}
                  >
                    <div className="mb-3 h-2 overflow-hidden rounded bg-zinc-800">
                      <div className="h-full bg-violet-500" style={{ width: `${(l.litres / maxLitres) * 100}%` }} />
                    </div>
                    <div className="flex flex-wrap gap-x-6 gap-y-2">
                      <Stat k="Litres in the plan" v={litres(l.litres)} />
                      <Stat k="Worth" v={money(l.value_rs)} />
                      <Stat k="Runs" v={inr(l.runs)} />
                      <Stat
                        k="Hours filling"
                        v={`${l.hours_run.toFixed(1)} of ${l.hours_on_line.toFixed(1)}`}
                        sub="the rest is oil changes and waiting"
                      />
                      <Stat k="Days it works" v={String(l.days_active)} />
                      <Stat k="Oil changes" v={`${Math.round(l.flush_minutes / 60)} h`} />
                    </div>

                    <div className="mt-3">
                      <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                        Speeds, and where each one comes from
                      </div>
                      <table className="mt-1 w-full text-sm">
                        <thead>
                          <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-600">
                            <th className="py-1 font-normal">Pack</th>
                            <th className="py-1 text-right font-normal">Speed on file</th>
                            <th className="py-1 text-right font-normal">Speed the plan uses</th>
                            <th className="py-1 font-normal">Where it comes from</th>
                          </tr>
                        </thead>
                        <tbody>
                          {l.slots.map((s) => {
                            const b = BASIS[s.rate_basis] ?? BASIS.rated;
                            return (
                              <tr key={s.slot} className="border-t border-zinc-800/60">
                                <td className="py-1">{s.slot}</td>
                                <td className="py-1 text-right tabular-nums">{inr(s.stored_rate_per_hr)}/h</td>
                                <td className="py-1 text-right tabular-nums">{inr(s.effective_rate_per_hr)}/h</td>
                                <td className="py-1">
                                  <Pill tone={b.tone} title={s.note}>
                                    {s.rate_basis}
                                  </Pill>
                                  <span className="ml-2 text-xs text-zinc-500">{s.note ?? b.words}</span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {l.top_skus && l.top_skus.length > 0 && (
                      <p className="mt-2 text-xs text-zinc-500">
                        Mostly: {l.top_skus.slice(0, 3).map((s) => s.sku).join(" · ")}
                      </p>
                    )}
                  </Panel>
                );
              })}

              {L.measured_from && <p className="text-xs text-zinc-500">{maskDigits(L.measured_from)}</p>}
            </div>
          )}
        </Live>
      </div>

      <p className="mt-4 text-xs text-zinc-500">
        {orUnknown(
          prod?.made_today_l,
          (v) => `The factory app has ${litres(v)} filled today`,
          "The factory app has no run recorded today",
        )}
        {prod?.made_yesterday_l != null && `, against ${litres(prod.made_yesterday_l)} yesterday`}. That is what the
        machines recorded, not the whole plant — see the note above the table.
      </p>
    </div>
  );
}
