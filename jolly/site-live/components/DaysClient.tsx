"use client";

// /days — the whole re-planned horizon, one row per day.
// Day 1 is TODAY and it is the only day read off the plant. Every row after it
// is computed from the row before it plus what the planner decided, and the
// whole ladder is rebuilt from a fresh count every few minutes. "Today" is
// checked against the calendar, never assumed from n === 1 — a plan the chain
// has stopped rebuilding keeps yesterday's day 1.

import Link from "next/link";
import { useState } from "react";
import { asHonesty, asOverview, asSpine, istToday, useLive, useNow } from "../lib/live";
import { ruleText } from "../lib/labels";
import { dlabel, inr, litres, money, pct, pct1, plural, weekdayShort } from "../lib/fmt";
import { AsOf, Live } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

export default function DaysClient() {
  const live = useLive(["spine", "overview", "honesty"]);
  const spine = asSpine(live.spine) ?? [];
  const o = asOverview(live.overview);
  const h = asHonesty(live.honesty);
  const [hover, setHover] = useState<number | null>(null);
  const now = useNow(10_000);
  const today = istToday(now || undefined);

  const max = Math.max(1, ...spine.map((d) => d.made_l));
  const d = hover === null ? null : spine[hover];

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Day by day</h1>
        <SimBadge kind="plan" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {ruleText(h, "rolling-replan") ?? "Day one is today, read off the plant. Every later day is worked out from it."}
      </p>

      <div className="mt-6 space-y-4">
        <Panel
          title={o ? `${o.totals.days} days left, ${o.totals.working_days} of them working` : "The month ahead"}
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.spine} />}
        >
          <Live rec={live.spine} what="the month">
            {/* read-out — fixed height so nothing jumps when you sweep across */}
            <div className="mb-4 min-h-[66px] border-b border-zinc-800 pb-3">
              {d === null ? (
                <p className="pt-3 text-sm text-zinc-500">
                  Move over a day for its numbers. Click to open it. Bar height is litres filled; colour is how full the
                  godown gets. Only the first bar has happened.
                </p>
              ) : (
                <div className="flex flex-wrap items-start gap-x-6 gap-y-3">
                  <div className="min-w-[120px]">
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                      {d.n === 1
                        ? d.date === today ? "Today — read off the plant" : "Day 1 when the plan was built — not today"
                        : d.working ? "Working day — the plan" : `${d.weekday} — closed`}
                    </div>
                    <div className="mt-0.5 text-sm font-semibold">
                      {weekdayShort(d.weekday)} {dlabel(d.date)}
                    </div>
                  </div>
                  <Stat k="Filled" v={d.made_l > 0 ? litres(d.made_l) : "nothing"} />
                  <Stat k="Worth" v={d.value_rs > 0 ? money(d.value_rs) : "—"} />
                  <Stat k="Billed" v={d.shipped_l > 0 ? litres(d.shipped_l) : "nothing"} />
                  <Stat
                    k="Machines busy"
                    v={pct(d.util)}
                    tone={d.util >= 80 ? "text-emerald-300" : d.util >= 30 ? "text-amber-300" : "text-zinc-100"}
                  />
                  <Stat
                    k="Godown full"
                    v={pct1(d.storage_pct)}
                    tone={d.storage_pct >= 95 ? "text-red-300" : d.storage_pct >= 80 ? "text-amber-300" : "text-emerald-300"}
                  />
                  <Stat k="Runs" v={inr(d.runs)} />
                  <Stat k="Stuck" v={inr(d.blocked)} tone={d.blocked > 0 ? "text-red-300" : "text-zinc-100"} />
                  <Stat k="Ordered lines" v={inr(d.orders.real_rows)} tone="text-emerald-300" />
                  <Stat k="Expected lines" v={inr(d.orders.forecast_rows)} tone="text-violet-300" />
                </div>
              )}
            </div>

            <div className="flex h-56 items-stretch gap-[3px]">
              {spine.map((x, i) => {
                const tone = x.storage_pct >= 95 ? "bg-red-500" : x.storage_pct >= 80 ? "bg-amber-500" : "bg-emerald-500";
                const hgt = x.made_l > 0 ? Math.max(1.5, (x.made_l / max) * 100) : 0;
                return (
                  <Link
                    key={x.date}
                    href={`/days/${x.n}`}
                    onMouseEnter={() => setHover(i)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(i)}
                    onBlur={() => setHover(null)}
                    aria-label={`${dlabel(x.date)} — fills ${inr(x.made_l)} litres, godown ${Math.round(
                      x.storage_pct,
                    )} per cent full`}
                    className={`flex flex-1 flex-col justify-end rounded-sm outline-none transition-colors focus-visible:ring-1 focus-visible:ring-amber-400 ${
                      x.working ? "" : "opacity-40"
                    } ${hover === i ? "bg-zinc-800" : "hover:bg-zinc-900"}`}
                  >
                    <div className={`${tone} rounded-sm`} style={{ height: `${hgt}%` }} />
                    <div className="mt-1 text-center text-[9px] text-zinc-600">{Number(x.date.slice(8, 10))}</div>
                  </Link>
                );
              })}
            </div>
          </Live>
        </Panel>

        <Panel title="Every day, in a table" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live.spine} />}>
          <Live rec={live.spine} what="the month">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[52rem] text-sm">
                <thead>
                  <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                    <th className="py-1 font-normal">Day</th>
                    <th className="py-1 text-right font-normal">Filled</th>
                    <th className="py-1 text-right font-normal">Worth</th>
                    <th className="py-1 text-right font-normal">Billed</th>
                    <th className="py-1 text-right font-normal">Busy</th>
                    <th className="py-1 text-right font-normal">Godown</th>
                    <th className="py-1 text-right font-normal">Runs</th>
                    <th className="py-1 text-right font-normal">Stuck</th>
                    <th className="py-1 text-right font-normal">Ordered</th>
                    <th className="py-1 text-right font-normal">Expected</th>
                  </tr>
                </thead>
                <tbody>
                  {spine.map((x) => (
                    <tr key={x.date} className={`border-t border-zinc-800/60 ${x.working ? "" : "text-zinc-600"}`}>
                      <td className="py-1">
                        <Link href={`/days/${x.n}`} className="underline-offset-2 hover:underline">
                          {weekdayShort(x.weekday)} {dlabel(x.date)}
                        </Link>
                        {x.n === 1 && x.date === today && (
                          <Pill tone="green" title="the only day that is read off the plant">
                            today
                          </Pill>
                        )}
                        {x.n === 1 && x.date !== today && (
                          <Pill tone="amber" title="day 1 of a plan the chain has not rebuilt — its date is not today">
                            day 1, not today
                          </Pill>
                        )}
                      </td>
                      <td className="py-1 text-right tabular-nums">{x.made_l > 0 ? inr(x.made_l) : "—"}</td>
                      <td className="py-1 text-right tabular-nums">{x.value_rs > 0 ? money(x.value_rs) : "—"}</td>
                      <td className="py-1 text-right tabular-nums">{x.shipped_l > 0 ? inr(x.shipped_l) : "—"}</td>
                      <td className="py-1 text-right tabular-nums">{pct(x.util)}</td>
                      <td
                        className={`py-1 text-right tabular-nums ${
                          x.storage_pct >= 95 ? "text-red-300" : x.storage_pct >= 80 ? "text-amber-300" : ""
                        }`}
                      >
                        {pct1(x.storage_pct)}
                      </td>
                      <td className="py-1 text-right tabular-nums">{x.runs}</td>
                      <td className={`py-1 text-right tabular-nums ${x.blocked > 0 ? "text-red-300" : ""}`}>{x.blocked}</td>
                      <td className="py-1 text-right tabular-nums text-emerald-300">{x.orders.real_rows}</td>
                      <td className="py-1 text-right tabular-nums text-violet-300">{x.orders.forecast_rows}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-zinc-500">
              &ldquo;Ordered&rdquo; and &ldquo;Expected&rdquo; are order LINES, not litres — on a quiet day every one of
              them is expected. {o ? `${plural(o.totals.days, "This day is", "These days are")} re-worked every few minutes.` : ""}
            </p>
          </Live>
        </Panel>
      </div>
    </div>
  );
}
