"use client";

// /lines — the machines.
//
// NOW: what each machine did today, off the factory app.
// FORWARD: how hard the plan works each one, and on what speed — and the speed
// basis is always on screen, because the five bases are not the same claim:
//   capped   a share of the listed speed, then held to the best August run
//   rated    a share of the listed speed — August had nothing long enough
//   typical  the middle August run — the app lists no speed for that pack
//   carried  carried from the last plan and cut back — nothing else exists
//   derived  another pack on the same machine — never timed on its own
//
// The old map only knew three of those words and quietly called the other two
// "the machine's listed speed", which is precisely what they are not.

import Link from "next/link";
import { asHonesty, asLines, asOverview, asState, useLive } from "../lib/live";
import { maskDigits, prefWords, speedBasis, speedRule } from "../lib/labels";
import { inr, litres, money, orUnknown, pct } from "../lib/fmt";
import { AsOf, Live, LiveSource, SourceLine } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

/** A speed, or a dash. A pack nobody has timed is not a pack that runs at zero. */
const rate = (n: number | null | undefined) =>
  typeof n === "number" && Number.isFinite(n) ? `${inr(n)}/h` : "—";

/** The families a slot may take, worst preference last. */
const famList = (families: Record<string, number> | undefined) =>
  Object.entries(families ?? {}).sort((a, b) => a[1] - b[1]);

export default function LinesClient() {
  const live = useLive(["lines", "state", "honesty", "overview"]);
  const L = asLines(live.lines);
  const st = asState(live.state);
  const h = asHonesty(live.honesty);
  const o = asOverview(live.overview);
  const speed = speedRule(h);

  const prod = st?.factory_production;
  const byLine = prod?.by_line_today ?? {};
  const runningLines = new Set((prod?.running_now ?? []).map((r) => r.line));
  const night = o?.night_line ?? L?.night_line_today ?? null;

  const maxLitres = Math.max(1, ...(L?.lines ?? []).map((l) => l.litres));
  const noSpeedCount = (L?.lines ?? []).reduce((a, l) => a + (l.no_speed_slots?.length ?? 0), 0);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Machines</h1>
        <SimBadge kind="live" />
        {L?.rulebook_version && <Pill tone="violet">rulebook {L.rulebook_version}</Pill>}
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {speed.text ??
          L?.efficiency_note ??
          "Every machine is planned below its listed speed, and never faster than it has really run."}
      </p>

      {/* ── today, off the factory app ───────────────────────────── */}
      <div className="mt-6">
        <Panel title="What each machine did today" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_production" />}>
          <LiveSource src="factory_production" what="the machines">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[44rem] text-sm">
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
            </div>
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
              <div className="flex flex-wrap items-center gap-x-8 gap-y-3 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                <Stat k="Litres the plan fills" v={litres(L.total_litres)} />
                {L.planning_factor != null && (
                  <Stat
                    k="Cut to"
                    v={pct(L.planning_factor * 100)}
                    sub={L.planning_factor_basis ?? "of the speed the factory app lists"}
                  />
                )}
                {L.sustained_hours != null && (
                  <Stat
                    k="Then held to August"
                    v={`${L.sustained_hours} h`}
                    sub="the best run the machine kept for that long — whichever is slower wins"
                  />
                )}
                {L.hours_per_session != null && (
                  <Stat
                    k="A session"
                    v={`${L.hours_per_session} h`}
                    sub="one machine a day may run a second one"
                  />
                )}
                {noSpeedCount > 0 && (
                  <Stat
                    k="Packs with no speed yet"
                    v={inr(noSpeedCount)}
                    tone="text-red-300"
                    sub="a machine may take them, but nobody has given a rate"
                  />
                )}
                <span className="ml-auto">
                  <AsOf rec={live.lines} />
                </span>
              </div>
              {L.total_litres_note && <p className="text-xs text-zinc-500">{maskDigits(L.total_litres_note)}</p>}

              {L.lines.map((l) => {
                const live_now = runningLines.has(l.name);
                const isNight = night?.line === l.name;
                return (
                  <Panel
                    key={l.name}
                    title={l.name}
                    badge={
                      <span className="flex flex-wrap items-center gap-1.5">
                        {live_now ? (
                          <Pill tone="green">
                            <span className="m3-live mr-1 inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 align-middle" />
                            running now
                          </Pill>
                        ) : (
                          <SimBadge kind="plan" />
                        )}
                        {isNight && (
                          <Pill
                            tone="violet"
                            title={night?.reason ? maskDigits(night.reason) : "the one machine given a second session today"}
                          >
                            second session tonight
                          </Pill>
                        )}
                      </span>
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
                      {l.hours_max_today != null && (
                        <Stat
                          k="Allowed today"
                          v={`${l.hours_max_today.toFixed(1)} h`}
                          sub={isNight ? "a second session tonight" : "one session"}
                        />
                      )}
                      {l.night_days && l.night_days.length > 0 && (
                        <Stat
                          k="Nights this month"
                          v={inr(l.night_days.length)}
                          sub="days it is given a second session"
                        />
                      )}
                      <Stat k="Oil changes" v={`${Math.round(l.flush_minutes / 60)} h`} />
                    </div>

                    <div className="mt-3">
                      <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                        Speeds, and where each one comes from
                      </div>
                      <div className="overflow-x-auto">
                        <table className="mt-1 w-full min-w-[42rem] text-sm">
                          <thead>
                            <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-600">
                              <th className="py-1 font-normal">Pack</th>
                              <th className="py-1 text-right font-normal">Listed</th>
                              <th className="py-1 text-right font-normal">August typical</th>
                              <th className="py-1 text-right font-normal">August best</th>
                              <th className="py-1 text-right font-normal">Runs</th>
                              <th className="py-1 text-right font-normal">The plan uses</th>
                              <th className="py-1 font-normal">Where it comes from</th>
                            </tr>
                          </thead>
                          <tbody>
                            {l.slots.map((s) => {
                              const b = speedBasis(s.rate_basis);
                              const fams = famList(s.families);
                              return (
                                <tr key={s.slot} className="border-t border-zinc-800/60 align-top">
                                  <td className="py-1">
                                    <div>{s.slot}</div>
                                    {fams.length > 0 && (
                                      <div className="mt-1 flex flex-wrap gap-1">
                                        {fams.map(([fam, pref]) => (
                                          <Pill
                                            key={fam}
                                            tone={pref === 1 ? "green" : pref === 2 ? "amber" : "zinc"}
                                            title={prefWords(pref)}
                                          >
                                            {fam}
                                          </Pill>
                                        ))}
                                      </div>
                                    )}
                                  </td>
                                  <td className="py-1 text-right tabular-nums">{rate(s.rated ?? null)}</td>
                                  <td className="py-1 text-right tabular-nums">{rate(s.aug_median ?? null)}</td>
                                  <td className="py-1 text-right tabular-nums">{rate(s.aug_best ?? null)}</td>
                                  <td className="py-1 text-right tabular-nums">{s.aug_runs ?? "—"}</td>
                                  <td className="py-1 text-right font-medium tabular-nums">
                                    {rate(s.planning ?? s.effective_rate_per_hr)}
                                    {s.set_of_two_rate_per_hr != null && (
                                      <div
                                        className="text-[10px] font-normal text-zinc-500"
                                        title={s.set_of_two_basis ?? undefined}
                                      >
                                        {rate(s.set_of_two_rate_per_hr)} two at a time
                                      </div>
                                    )}
                                  </td>
                                  <td className="py-1">
                                    <Pill tone={b.tone} title={s.planning_basis ?? s.note ?? b.words}>
                                      {b.label}
                                    </Pill>
                                    <div className="mt-0.5 text-xs text-zinc-500">
                                      {maskDigits(s.note ?? s.planning_basis ?? b.words)}
                                    </div>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {l.no_speed_slots && l.no_speed_slots.length > 0 && (
                      <div className="mt-3 rounded-lg border border-red-500/25 bg-red-500/[0.04] p-3">
                        <div className="text-[10px] uppercase tracking-wider text-red-300/80">
                          This machine may take these, and nobody has given a speed
                        </div>
                        <ul className="mt-1 space-y-1 text-xs">
                          {l.no_speed_slots.map((n) => (
                            <li key={n.slot} className="flex flex-wrap items-baseline gap-2">
                              <span className="text-zinc-200">{n.slot}</span>
                              {famList(n.families).map(([fam, pref]) => (
                                <Pill key={fam} tone="zinc" title={prefWords(pref)}>
                                  {fam}
                                </Pill>
                              ))}
                              <span className="text-zinc-500">{maskDigits(n.why)}</span>
                            </li>
                          ))}
                        </ul>
                        <p className="mt-1 text-xs text-zinc-500">
                          The plan puts nothing here until somebody rules on a rate. It is shown, never dropped.
                        </p>
                      </div>
                    )}

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
        machines recorded, not the whole plant — see the note above the table.{" "}
        Every speed above, and the rule behind it, is on{" "}
        <Link href="/assumptions" className="underline underline-offset-2 hover:text-zinc-300">
          what this plan takes as fact
        </Link>
        .
      </p>
    </div>
  );
}
