"use client";

// The FORWARD layer: what the planner does with today's count, from today to
// the end of the month. Nothing here has happened.

import Link from "next/link";
import { asHonesty, asOverview, asSpine, useLive } from "../lib/live";
import { ceilingRule, maskDigits, P } from "../lib/labels";
import { cr, dlabel, inr, litres, money, orUnknown, pct, pct1, plural } from "../lib/fmt";
import { Card, Panel, Pill } from "./Card";
import { AsOf, Live, NotLive } from "./Freshness";
import SimBadge from "./SimBadge";

export default function ForwardStrip() {
  const live = useLive(["overview", "spine", "honesty"]);
  const o = asOverview(live.overview);
  const spine = asSpine(live.spine);
  const h = asHonesty(live.honesty);
  const ceiling = ceilingRule(h);
  const today = spine?.[0] ?? null;
  const book = today?.book ?? null;

  return (
    <div className="space-y-4">
      <Live rec={live.overview} what="the plan">
        {o && (
          <>
            {/* one freshness stamp for the four tiles below — they all come
                from the same source, so four identical stamps would be noise */}
            <div className="mb-1.5 flex justify-end">
              <AsOf rec={live.overview} />
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card
              title="Still to make this month"
              value={orUnknown(book?.plan_left_l, litres)}
              badge={<SimBadge kind="plan" />}
              sub={book?.plan_left_l ? "against this month's target, from today onward" : undefined}
            />
            <Card
              title="The computer expects to make"
              value={litres(o.totals.made_l)}
              tone="text-violet-300"
              badge={<SimBadge kind="plan" />}
              sub={`${cr(o.totals.value_rs)} over ${o.totals.working_days} working ${plural(
                o.totals.working_days, "day", "days",
              )} — ${pct1(o.plan.made_vs_plan_pct)} of the target`}
            />
            <Card
              title="Billed out over the month"
              value={litres(o.totals.shipped_l)}
              badge={<SimBadge kind="plan" />}
              sub={`${pct1(o.demand.forecast_share_litres_pct)} of the demand behind it is expected, not ordered`}
            />
            <Card
              title="Days the godown is over the limit"
              value={`${o.storage.days_ge_100.length} of ${o.totals.days}`}
              tone={o.storage.days_ge_100.length > 0 ? "text-red-400" : "text-emerald-300"}
              badge={<NotLive p={P.ceiling(ceiling.text)} />}
              sub={
                <>
                  {o.storage.days_ge_95} {plural(o.storage.days_ge_95, "day", "days")} at 95% or more of{" "}
                  {litres(o.storage.ceiling_l)} — the limit you gave us
                </>
              }
            />
            </div>
          </>
        )}
      </Live>

      <div className="grid gap-3 md:grid-cols-2">
        <Panel
          title="Today, as the planner sees it"
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.spine} />}
        >
          <Live rec={live.spine} what="today's plan">
            {today && (
              <>
                <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Fill today</div>
                    <div className="text-xl font-semibold tabular-nums">{litres(today.made_l)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Machines busy</div>
                    <div className="text-xl font-semibold tabular-nums">{pct(today.util)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Godown</div>
                    <div
                      className={`text-xl font-semibold tabular-nums ${
                        today.storage_pct >= 95 ? "text-red-300" : today.storage_pct >= 80 ? "text-amber-300" : "text-emerald-300"
                      }`}
                    >
                      {pct1(today.storage_pct)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Runs / stuck</div>
                    <div className="text-xl font-semibold tabular-nums">
                      {today.runs} <span className="text-red-300">/ {today.blocked}</span>
                    </div>
                  </div>
                </div>
                {today.open_real_l_computed != null && (
                  <p className="mt-3 text-xs text-zinc-400">
                    Still to send on confirmed orders: {litres(today.open_real_l_computed)}.{" "}
                    {today.open_real_l_note ? maskDigits(today.open_real_l_note) : ""}
                  </p>
                )}
                {book && (
                  <div className="mt-3 space-y-1 text-xs text-zinc-500">
                    <div title={book.po_cumulative_value_label}>
                      {money(book.po_cumulative_value_rs)} — {book.po_cumulative_value_label}
                    </div>
                    <div title={book.po_open_l_raw_label}>
                      {litres(book.po_open_l_raw)} — {book.po_open_l_raw_label}
                    </div>
                  </div>
                )}
              </>
            )}
          </Live>
        </Panel>

        <Panel
          title="Why these numbers get to have an opinion"
          badge={<SimBadge kind="measured" />}
          asOf={<AsOf rec={live.overview} />}
        >
          <Live rec={live.overview} what="the calibration">
            {o?.august && (
              <>
                <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">The computer said</div>
                    <div className="text-xl font-semibold tabular-nums">{litres(o.august.sim_made_l)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">The plant really made</div>
                    <div className="text-xl font-semibold tabular-nums">{litres(o.august.actual_made_l)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Out by</div>
                    <div className="text-xl font-semibold tabular-nums text-emerald-300">{pct1(o.august.delta_pct)}</div>
                  </div>
                </div>
                <p className="mt-2 text-xs text-zinc-400">{maskDigits(o.august.note ?? "")}</p>
              </>
            )}
            {o?.day1_blocked && (
              <div className="mt-4 border-t border-zinc-800 pt-3">
                <div className="text-[10px] uppercase tracking-wider text-zinc-500">Stuck today</div>
                <div className="mt-1 flex flex-wrap items-baseline gap-2 text-sm">
                  <span className="text-lg font-semibold tabular-nums text-red-300">{o.day1_blocked.products}</span>
                  <span className="text-zinc-400">
                    {plural(o.day1_blocked.products, "product", "products")} the planner could not start
                  </span>
                  {o.day1_blocked.top_binder && (
                    <Pill tone="amber" title={`${o.day1_blocked.top_binder.attempts} attempts stopped by this one`}>
                      worst: {o.day1_blocked.top_binder.name}
                    </Pill>
                  )}
                </div>
                <p className="mt-1 text-xs text-zinc-500">{maskDigits(o.day1_blocked.note ?? "")}</p>
              </div>
            )}
          </Live>
        </Panel>
      </div>

      {o?.unproducible && o.unproducible.length > 0 && (
        <Panel
          title="In the target, but no machine can fill it"
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.overview} />}
          note="Shown, never hidden. There is no 3-litre line and no drum line, so these litres cannot be made at all this month."
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                <th className="pb-1 font-normal">Product</th>
                <th className="pb-1 font-normal">Needs</th>
                <th className="pb-1 text-right font-normal">In the target</th>
                <th className="pb-1 text-right font-normal">Worth, roughly</th>
              </tr>
            </thead>
            <tbody>
              {o.unproducible.map((u) => (
                <tr key={u.code} className="border-t border-zinc-800/60">
                  <td className="py-1">
                    <span className="mr-2 font-mono text-[11px] text-zinc-500">{u.code}</span>
                    {u.sku}
                  </td>
                  <td className="py-1 text-zinc-400">{u.reason}</td>
                  <td className="py-1 text-right tabular-nums">{litres(u.plan_litres)}</td>
                  <td className="py-1 text-right tabular-nums text-amber-300">
                    {u.value_est_rs ? money(u.value_est_rs) : "—"}
                    {u.value_est_derived && <span className="ml-1 text-[10px] text-zinc-500">worked out</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}

      {o?.totals.peak_day && (
        <p className="text-xs text-zinc-500">
          Busiest day the planner picks: {dlabel(o.totals.peak_day.date)} at {litres(o.totals.peak_day.made_l)}.{" "}
          <Link href="/days" className="underline underline-offset-2 hover:text-zinc-300">
            walk the month day by day
          </Link>
          .
        </p>
      )}
    </div>
  );
}
