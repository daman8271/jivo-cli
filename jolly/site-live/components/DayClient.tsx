"use client";

// /days/[n] — one day in full.
//
// Day 1 is today: its opening is the live count and it is the only observed day
// on the site. Days 2..N are the planner's own output stacked on it. The page
// says which it is, every time.

import Link from "next/link";
import { asDay, asHonesty, asOverview, asSpine, dayId, useLive } from "../lib/live";
import { ceilingRule, isRealiseOutlier, maskDigits, P, realiseOutlier } from "../lib/labels";
import { dlabel, inr, litres, money, pct, pct1, plural, weekdayShort } from "../lib/fmt";
import { AsOf, Live, NotLive } from "./Freshness";
import { Card, Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";
import { DispatchSplit, OrderLines } from "./DemandSplit";

export default function DayClient({ n }: { n: number }) {
  const id = dayId(n);
  const live = useLive([id, "spine", "overview", "honesty"]);
  const day = asDay(live[id]);
  const spine = asSpine(live.spine) ?? [];
  const o = asOverview(live.overview);
  const h = asHonesty(live.honesty);
  const ceiling = ceilingRule(h);
  const outlier = realiseOutlier(h);
  const isToday = n === 1;
  const last = spine.length ? spine[spine.length - 1].n : null;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">
          {day ? `${weekdayShort(day.weekday)} ${dlabel(day.date)}` : `Day ${n}`}
        </h1>
        <SimBadge kind={isToday ? "live" : "plan"} />
        {isToday && <Pill tone="green">the only day that has happened</Pill>}
        {day && !day.working && <Pill tone="zinc">factory closed</Pill>}
      </div>

      <div className="mt-2 flex items-center gap-3 text-sm">
        {n > 1 && (
          <Link href={`/days/${n - 1}`} className="text-zinc-400 underline-offset-2 hover:text-zinc-200 hover:underline">
            ← day {n - 1}
          </Link>
        )}
        <Link href="/days" className="text-zinc-400 underline-offset-2 hover:text-zinc-200 hover:underline">
          all days
        </Link>
        {last !== null && n < last && (
          <Link href={`/days/${n + 1}`} className="text-zinc-400 underline-offset-2 hover:text-zinc-200 hover:underline">
            day {n + 1} →
          </Link>
        )}
      </div>

      <p className="mt-2 max-w-3xl text-sm text-zinc-300">
        {isToday
          ? "Today's opening is the live count from the plant. Everything the planner does with it below is a decision, not a record."
          : "Nothing on this page has happened. It is worked out from the day before it, which was worked out from the day before that, back to today's live count."}
      </p>

      <div className="mt-6">
        <Live rec={live[id]} what={`day ${n}`}>
          {day && (
            <div className="space-y-4">
              <div className="flex justify-end">
                <AsOf rec={live[id]} />
              </div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Card
                  title="Filled"
                  value={day.made_litres > 0 ? litres(day.made_litres) : "nothing"}
                  sub={day.made_value_rs > 0 ? money(day.made_value_rs) : undefined}
                  badge={<SimBadge kind={isToday ? "live" : "plan"} />}
                />
                <Card
                  title="Billed out"
                  value={day.shipped_litres > 0 ? litres(day.shipped_litres) : "nothing"}
                  badge={<SimBadge kind="plan" />}
                  sub={
                    <DispatchSplit
                      realL={day.dispatched_real.reduce((a, b) => a + b.litres, 0)}
                      forecastL={day.dispatched_forecast.reduce((a, b) => a + b.litres, 0)}
                    />
                  }
                />
                <Card
                  title="Machines busy"
                  value={pct(day.line_util)}
                  tone={day.line_util >= 80 ? "text-emerald-300" : "text-zinc-100"}
                  badge={<SimBadge kind="plan" />}
                  sub={`${day.runs.length} ${plural(day.runs.length, "run", "runs")}, ${day.flushes} ${plural(
                    day.flushes, "oil change", "oil changes",
                  )}`}
                />
                <Card
                  title="Godown"
                  value={pct1(day.storage.pct)}
                  tone={day.storage.pct >= 95 ? "text-red-400" : day.storage.pct >= 80 ? "text-amber-300" : "text-emerald-300"}
                  badge={<NotLive p={P.ceiling(ceiling.text, "Q2")} />}
                  sub={`${litres(day.storage.physical_l)} against a limit of ${litres(day.storage.ceiling_l)} — a guess`}
                />
              </div>

              {/* oil on hand — the OTHER series, and it says so */}
              <Panel
                title="Oil on hand for this day's recipes"
                badge={<SimBadge kind="plan" />}
                asOf={<AsOf rec={live[id]} />}
                note={
                  o?.opening.oil_l_definition ??
                  "This counts only the oils in this month's recipes. The tank total on the front page counts every oil — they are two different lines and are never drawn as one."
                }
              >
                <div className="flex flex-wrap items-baseline gap-x-8 gap-y-2">
                  <Stat k="In the recipes" v={litres(day.oil_on_hand_l)} />
                  <Stat k="Used this day" v={litres(day.oil_used_l)} />
                  {o && <Stat k="Every oil in the tanks" v={litres(o.opening.oil_l)} tone="text-zinc-400" />}
                </div>
              </Panel>

              {/* runs */}
              <Panel title="What the planner runs" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live[id]} />}>
                {day.runs.length === 0 ? (
                  <p className="text-sm text-zinc-500">No machine runs on this day.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[44rem] text-sm">
                      <thead>
                        <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                          <th className="py-1 font-normal">Machine</th>
                          <th className="py-1 font-normal">Product</th>
                          <th className="py-1 text-right font-normal">Pieces</th>
                          <th className="py-1 text-right font-normal">Litres</th>
                          <th className="py-1 text-right font-normal">Hours</th>
                          <th className="py-1 text-right font-normal">Oil change</th>
                          <th className="py-1 text-right font-normal">Worth</th>
                        </tr>
                      </thead>
                      <tbody>
                        {day.runs.map((r, i) => (
                          <tr key={`${r.code}-${i}`} className="border-t border-zinc-800/60">
                            <td className="py-1">{r.line}</td>
                            <td className="py-1">
                              <span className="mr-2 font-mono text-[11px] text-zinc-500">{r.code}</span>
                              {r.sku}
                              {isRealiseOutlier(h, r.code) && (
                                <Pill tone="amber" title={outlier.note ?? ""}>
                                  odd price
                                </Pill>
                              )}
                              {r.po_backed === false && (
                                <Pill tone="violet" title="no customer order behind this run — it is made to the month's target">
                                  no order behind it
                                </Pill>
                              )}
                            </td>
                            <td className="py-1 text-right tabular-nums">{inr(r.pieces)}</td>
                            <td className="py-1 text-right tabular-nums">{inr(r.litres)}</td>
                            <td className="py-1 text-right tabular-nums">{r.hours.toFixed(1)}</td>
                            <td className="py-1 text-right tabular-nums text-amber-300">
                              {r.flush_min > 0 ? `${r.flush_min} min` : "—"}
                            </td>
                            <td className="py-1 text-right tabular-nums">{r.value ? money(r.value) : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Panel>

              {/* stuck / waiting / landed */}
              <div className="grid gap-3 md:grid-cols-3">
                <Panel title="Could not be started" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live[id]} />}>
                  {day.blocked.length === 0 ? (
                    <p className="text-sm text-zinc-500">Nothing was stopped for want of material.</p>
                  ) : (
                    <ul className="max-h-56 space-y-1 overflow-y-auto text-xs">
                      {day.blocked.map((b, i) => (
                        <li key={`${b.code}-${b.binder}-${i}`}>
                          <span className="text-zinc-300">{b.sku}</span>
                          <span className="text-zinc-500"> — short of {b.binder_name}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>
                <Panel title="Waiting on" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live[id]} />}>
                  {day.waiting_on.length === 0 ? (
                    <p className="text-sm text-zinc-500">Nothing outstanding.</p>
                  ) : (
                    <ul className="max-h-56 space-y-1 overflow-y-auto text-xs">
                      {day.waiting_on.map((w) => (
                        <li key={w.code}>
                          <span className="text-zinc-300">{w.name}</span>
                          <span className="text-zinc-500"> — since {dlabel(w.since)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>
                <Panel title="Landed this day" badge={<SimBadge kind={isToday ? "live" : "plan"} />} asOf={<AsOf rec={live[id]} />}>
                  {day.received.length === 0 ? (
                    <p className="text-sm text-zinc-500">Nothing arrived.</p>
                  ) : (
                    <ul className="max-h-56 space-y-1 overflow-y-auto text-xs">
                      {day.received.map((r) => (
                        <li key={r.code} className="flex justify-between gap-2">
                          <span className="text-zinc-300">{r.name}</span>
                          <span className="tabular-nums text-zinc-500">{inr(r.qty)}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>
              </div>

              {/* the orders that arrived that day, split three ways */}
              <OrderLines
                title="New on the order book that day"
                real={day.orders_real}
                forecast={day.orders_forecast}
                rec={live[id]}
              />

              {/* what the planner bought */}
              {day.bought.length > 0 && (
                <Panel title="What the planner orders that day" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live[id]} />}>
                  <div className="max-h-72 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-zinc-900">
                        <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                          <th className="py-1 font-normal">Material</th>
                          <th className="py-1 text-right font-normal">Quantity</th>
                          <th className="py-1 text-right font-normal">Lands</th>
                        </tr>
                      </thead>
                      <tbody>
                        {day.bought.map((b, i) => (
                          <tr key={`${b.code}-${i}`} className="border-t border-zinc-800/60">
                            <td className="py-1">
                              <span className="mr-2 font-mono text-[11px] text-zinc-500">{b.code}</span>
                              {b.name}
                            </td>
                            <td className="py-1 text-right tabular-nums">
                              {inr(b.qty)} {b.uom.toLowerCase()}
                            </td>
                            <td className="py-1 text-right text-zinc-400">{dlabel(b.lands)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Panel>
              )}

              {/* the day's own honesty block */}
              {day.honesty && (
                <Panel title="What is real on this day, and what is a guess" asOf={<AsOf rec={live[id]} />}>
                  <div className="grid gap-4 text-xs md:grid-cols-2">
                    <div>
                      <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">Measured — real</div>
                      <ul className="space-y-1">
                        {day.honesty.measured.map((m) => (
                          <li key={m} className="flex items-start gap-2">
                            <Pill tone="green">real</Pill>
                            <span className="text-zinc-400">{maskDigits(m)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">
                        Our guess ({day.honesty.assumed.length})
                      </div>
                      <ul className="max-h-52 space-y-1 overflow-y-auto pr-2">
                        {day.honesty.assumed.map((a, i) => (
                          <li key={`${i}-${a.slice(0, 20)}`} className="flex items-start gap-2">
                            <Pill tone="amber">guess</Pill>
                            <span className="text-zinc-400">{maskDigits(a)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Panel>
              )}
            </div>
          )}
        </Live>
      </div>
    </div>
  );
}
