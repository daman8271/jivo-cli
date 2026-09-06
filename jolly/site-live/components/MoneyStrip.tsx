"use client";

// Money — the day in rupees, against the plant's own floor and target.
//
// The planner's question every morning is not "how many litres" but "are we
// going to make the number today". So the target and the floor are on screen
// beside the day, and both are READ from the rulebook — the site does not know
// what they are and could not type them if it wanted to.
//
// Three different rupee figures live here and they are never added:
//   booked today   goods receipts into the godown dated today. The receipt lags
//                  the filling by a day or so — it is production BOOKED.
//   today's plan   what the planner intends to fill today, at each SKU's price.
//   month to date  the days already gone, off the goods receipts.

import { asHonesty, asOverview, useLive } from "../lib/live";
import { maskDigits, moneyRule } from "../lib/labels";
import { inr, money, orUnknown, pct1, plural } from "../lib/fmt";
import { AsOf, Live } from "./Freshness";
import { Card, Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

export default function MoneyStrip() {
  const live = useLive(["overview", "honesty"]);
  const o = asOverview(live.overview);
  const h = asHonesty(live.honesty);
  const rule = moneyRule(h);

  const m = o?.money ?? null;
  const target = m?.target_rs_per_day ?? rule.targetRsPerDay ?? null;
  const floor = m?.floor_rs_per_day ?? rule.floorRsPerDay ?? null;
  const plan = m?.today_plan_rs ?? null;

  // where today's plan sits between nothing and the target — a UI width only
  const barPct = target && plan !== null ? Math.min(100, Math.max(0, (plan / target) * 100)) : null;
  const floorPct = target && floor ? Math.min(100, (floor / target) * 100) : null;

  const tone = m?.on_target_today ? "text-emerald-300" : m?.above_floor_today ? "text-amber-300" : "text-red-300";
  const mtdPerDay = m?.mtd_made_rs != null && m?.mtd_days ? m.mtd_made_rs / m.mtd_days : null;

  return (
    <Live rec={live.overview} what="the day in rupees">
      {m ? (
        <div className="space-y-3">
          <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
            <p className="max-w-3xl text-xs text-zinc-400">{rule.text ? maskDigits(rule.text) : ""}</p>
            <AsOf rec={live.overview} />
          </div>

          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card
              title="Booked into the godown today"
              value={orUnknown(m.today_booked_rs, money, "nothing booked yet")}
              badge={<SimBadge kind="live" />}
              sub={
                m.today_booked_pieces != null
                  ? `${inr(m.today_booked_pieces)} ${plural(m.today_booked_pieces, "piece", "pieces")} · the receipt lags the filling`
                  : undefined
              }
            />
            <Card
              title="What today's plan is worth"
              value={orUnknown(plan, money)}
              tone={tone}
              badge={<SimBadge kind="plan" />}
              sub={
                target !== null
                  ? m.on_target_today
                    ? `on the target of ${money(target)} a day`
                    : floor !== null && m.above_floor_today
                      ? `under the target of ${money(target)}, above the floor of ${money(floor)}`
                      : `under the floor of ${floor !== null ? money(floor) : "the floor"}`
                  : undefined
              }
            />
            <Card
              title="This month so far"
              value={orUnknown(m.mtd_made_rs, money)}
              badge={<SimBadge kind="measured" />}
              sub={
                m.mtd_days != null
                  ? `over ${inr(m.mtd_days)} ${plural(m.mtd_days, "day", "days")} already gone${
                      mtdPerDay !== null ? ` — ${money(mtdPerDay)} a day` : ""
                    }`
                  : undefined
              }
            />
            <Card
              title="Your own target a day"
              value={orUnknown(target, money)}
              badge={<SimBadge kind="measured" />}
              sub={floor !== null ? `and never below ${money(floor)}` : undefined}
            />
          </div>

          {/* R16 IS A DAILY RULE, SO READ IT OVER THE MONTH. The four tiles above are
              today, and today is the one day the godown still has room in it — a green
              tick there was standing over a month that misses the floor on nearly every
              working day it has left. */}
          {m.month && (
            <Panel title="The whole month against that floor" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live.overview} />}>
              <div className="flex flex-wrap gap-x-8 gap-y-3">
                <Stat
                  k="Working days that keep the floor"
                  v={`${inr(m.month.days_above_floor)} of ${inr(m.month.working_days)}`}
                  tone={m.month.days_below_floor > 0 ? "text-red-300" : "text-emerald-300"}
                  sub={`${inr(m.month.days_on_target)} reach the target`}
                />
                <Stat
                  k="What the whole month is worth"
                  v={money(m.month.plan_rs)}
                  tone="text-amber-300"
                  sub={
                    m.month.target_rs_if_every_working_day_hit_it != null
                      ? `${money(m.month.target_rs_if_every_working_day_hit_it)} if every working day hit the target${
                          m.month.pct_of_a_month_of_targets != null ? ` — ${pct1(m.month.pct_of_a_month_of_targets)} of it` : ""
                        }`
                      : undefined
                  }
                />
                <Stat
                  k="The month's sheet at the same prices"
                  v={money(m.month.sheet_rs_at_the_same_prices)}
                  sub={
                    m.month.plan_pct_of_sheet_rs != null
                      ? `the plan reaches ${pct1(m.month.plan_pct_of_sheet_rs)} of it`
                      : undefined
                  }
                />
              </div>
              <p className="mt-2 text-xs text-zinc-400">{maskDigits(m.month.note)}</p>
            </Panel>
          )}

          {barPct !== null && (
            <Panel title="Today against your target" asOf={<AsOf rec={live.overview} />}>
              <div className="relative h-3 overflow-hidden rounded bg-zinc-800">
                <div
                  className={`h-full ${m.on_target_today ? "bg-emerald-500" : m.above_floor_today ? "bg-amber-500" : "bg-red-500"}`}
                  style={{ width: `${barPct}%` }}
                />
                {floorPct !== null && (
                  <div
                    className="absolute inset-y-0 w-px bg-zinc-300/70"
                    style={{ left: `${floorPct}%` }}
                    title={floor !== null ? `the floor: ${money(floor)} a day` : undefined}
                  />
                )}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-zinc-500">
                <span>nothing</span>
                {floor !== null && <span className="text-zinc-400">floor {money(floor)}</span>}
                {target !== null && <span className="ml-auto text-zinc-300">target {money(target)}</span>}
              </div>
              {m.basis && <p className="mt-2 text-xs text-zinc-500">{maskDigits(m.basis)}</p>}
            </Panel>
          )}

          <div className="grid gap-3 md:grid-cols-2">
            <Panel title="Where the month-to-date figure comes from" asOf={<AsOf rec={live.overview} />}>
              {m.mtd_by_basis && (
                <div className="flex flex-wrap gap-x-8 gap-y-3">
                  {Object.entries(m.mtd_by_basis).map(([k, v]) => (
                    <Stat key={k} k={k.replace(/_rs$/, "").replace(/_/g, " ")} v={money(v)} />
                  ))}
                </div>
              )}
              {m.mtd_basis && <p className="mt-2 text-xs text-zinc-500">{maskDigits(m.mtd_basis)}</p>}
            </Panel>
            <Panel
              title="Booked, not filled"
              badge={<Pill tone="amber">read this one carefully</Pill>}
              asOf={<AsOf rec={live.overview} />}
            >
              <p className="text-xs text-zinc-400">
                {m.booked_basis
                  ? maskDigits(m.booked_basis)
                  : "Goods receipts into the godown dated today — the receipt lags the filling, so this is production booked, not filled."}
              </p>
            </Panel>
          </div>
        </div>
      ) : (
        <Panel title="The day in rupees" asOf={<AsOf rec={live.overview} />}>
          <p className="text-sm text-zinc-500">
            This plan does not carry the day in rupees. It was built before the target and the floor were part of the
            rulebook.
          </p>
        </Panel>
      )}
    </Live>
  );
}
