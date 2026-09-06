"use client";

// Split the demand, always.
//
// The demand stream mixes three things and they do not mean the same thing:
//   OMS       a real order from a shop or distributor
//   ECOM-PO   a real, dated purchase order from an online platform
//   FORECAST  the month's target spread into the month — NOBODY has ordered it
//
// On a quiet day the whole "new demand" figure is forecast. The three keep
// different colours everywhere on this site so that can never be missed.

import { asHonesty, asOverview, useLive, type Rec } from "../lib/live";
import { CHANNEL, channelOf, expectedRule, forecastShareRule, maskDigits } from "../lib/labels";
import { dlabel, inr, litres, money, pct1, plural } from "../lib/fmt";
import type { OrderRow } from "../lib/types";
import { Panel, Pill } from "./Card";
import { AsOf, Live } from "./Freshness";

/** The month's demand, split three ways. */
export function DemandSplit() {
  const live = useLive(["overview", "honesty"]);
  const o = asOverview(live.overview);
  const h = asHonesty(live.honesty);
  const share = forecastShareRule(h);
  /* Mark 4 changed what "expected" MEANS. It used to be the month's target cut
     into days. It is now worked out from what the trade really bought over the
     last few months — a different claim, so the page has to say which one is
     behind the violet block rather than leave the old sentence standing. */
  const expected = expectedRule(h);
  const eo = o?.expected_orders ?? null;

  const sources = o?.demand.sources ?? {};
  const total = Object.values(sources).reduce((a, b) => a + b, 0);

  return (
    <Panel
      title="What customers want this month"
      asOf={<AsOf rec={live.overview} />}
      note={share.text ?? o?.demand.note}
    >
      <Live rec={live.overview} what="the demand book">
        {o && (
          <>
            <div className="flex h-3 overflow-hidden rounded">
              {(["oms", "ecom", "forecast"] as const).map((c) => {
                const key = c === "oms" ? "OMS" : c === "ecom" ? "ECOM-PO" : "FORECAST";
                const n = sources[key] ?? 0;
                const w = total > 0 ? (n / total) * 100 : 0;
                if (w <= 0) return null;
                return (
                  <div
                    key={c}
                    title={`${CHANNEL[c].label}: ${inr(n)} ${plural(n, "line", "lines")}`}
                    style={{ width: `${w}%` }}
                    className={CHANNEL[c].dot}
                  />
                );
              })}
            </div>

            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              {(["oms", "ecom", "forecast"] as const).map((c) => {
                const key = c === "oms" ? "OMS" : c === "ecom" ? "ECOM-PO" : "FORECAST";
                const n = sources[key] ?? 0;
                return (
                  <div key={c} className={`rounded-lg border p-3 ${CHANNEL[c].cls}`}>
                    <div className="text-[10px] font-semibold uppercase tracking-wider">{CHANNEL[c].short}</div>
                    <div className="mt-0.5 text-lg font-semibold tabular-nums">
                      {inr(n)} <span className="text-xs font-normal">{plural(n, "line", "lines")}</span>
                    </div>
                    <div className="mt-1 text-[11px] opacity-80">{CHANNEL[c].label}</div>
                    <div className="mt-1 text-[11px] opacity-70">{CHANNEL[c].why}</div>
                  </div>
                );
              })}
            </div>

            <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
                <div className="text-[10px] uppercase tracking-wider text-zinc-500">Really ordered</div>
                <div className="tabular-nums">
                  {inr(o.demand.real_pieces)} pcs · {money(o.demand.real_value_rs)}
                </div>
              </div>
              <div className="rounded-lg border border-violet-500/25 bg-violet-500/5 p-3">
                <div className="text-[10px] uppercase tracking-wider text-violet-300/80">
                  Expected — nobody has ordered it
                </div>
                <div className="tabular-nums text-violet-200">
                  {inr(o.demand.forecast_pieces)} pcs · {money(o.demand.forecast_value_rs)}
                </div>
                {eo?.used && (
                  <div className="mt-1 text-[11px] text-violet-200/70">
                    worked out from what the trade really bought
                    {eo.window?.from && eo.window?.to
                      ? `, ${dlabel(eo.window.from)} to ${dlabel(eo.window.to)}`
                      : ""}
                  </div>
                )}
                {eo && eo.used === false && eo.fallback_reason && (
                  <div className="mt-1 text-[11px] text-amber-300/80">{maskDigits(eo.fallback_reason)}</div>
                )}
              </div>
            </div>

            <p className="mt-3 text-xs text-zinc-400">
              By litres, {pct1(o.demand.forecast_share_litres_pct)} of what this month&rsquo;s demand asks for is
              expected, not ordered. By what it is worth, {pct1(o.demand.forecast_share_value_pct)}.
            </p>
            {(expected.text || eo?.source) && (
              <p className="mt-1 text-xs text-zinc-500">
                {expected.text ? maskDigits(expected.text) : ""}
                {eo?.note ? ` ${maskDigits(eo.note)}` : ""}
              </p>
            )}
            {(o.plan.sheet_skus != null || o.plan.expected_only_skus != null) && (
              <p className="mt-1 text-xs text-zinc-500">
                Of the {inr(o.plan.skus)} products in the plan,{" "}
                {o.plan.sheet_skus != null ? inr(o.plan.sheet_skus) : "—"} are on the month&rsquo;s own sheet
                {o.plan.expected_only_skus
                  ? ` and ${inr(o.plan.expected_only_skus)} are there only because the trade keeps buying them`
                  : " and none are there only because the trade keeps buying them"}
                .
              </p>
            )}
          </>
        )}
      </Live>
    </Panel>
  );
}

/** One day's order lines, split and kept visually distinct. */
export function OrderLines({
  real, forecast, rec, title,
}: {
  real: OrderRow[];
  forecast: OrderRow[];
  rec?: Rec;
  title: string;
}) {
  const rows = [...real, ...forecast];
  const totals = { oms: 0, ecom: 0, forecast: 0 } as Record<string, number>;
  for (const r of rows) totals[channelOf(r)] += r.pieces;

  return (
    <Panel
      title={title}
      asOf={<AsOf rec={rec} />}
      note="Confirmed orders and this month's expected demand are both here, and they never share a colour."
    >
      <div className="mb-3 flex flex-wrap gap-2">
        {(["oms", "ecom", "forecast"] as const).map((c) => (
          <Pill key={c} tone={c === "forecast" ? "violet" : c === "ecom" ? "blue" : "green"}>
            {CHANNEL[c].short} {inr(totals[c])} pcs
          </Pill>
        ))}
      </div>
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-zinc-900">
            <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
              <th className="py-1 font-normal">Order</th>
              <th className="py-1 font-normal">Customer</th>
              <th className="py-1 font-normal">Product</th>
              <th className="py-1 text-right font-normal">Pieces</th>
              <th className="py-1 text-right font-normal">Worth</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const c = channelOf(r);
              return (
                <tr
                  key={`${r.docnum}-${r.code}-${i}`}
                  className={`border-t border-zinc-800/60 ${c === "forecast" ? "bg-violet-500/5 text-violet-200/80" : ""}`}
                >
                  <td className="py-1">
                    <span className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full align-middle ${CHANNEL[c].dot}`} />
                    <span className="font-mono text-[11px]">{r.docnum}</span>
                  </td>
                  <td className="py-1 max-w-[16rem] truncate">{r.customer}</td>
                  <td className="py-1 max-w-[18rem] truncate text-zinc-400">{r.sku}</td>
                  <td className="py-1 text-right tabular-nums">{inr(r.pieces)}</td>
                  <td className="py-1 text-right tabular-nums">{r.value > 0 ? money(r.value) : "—"}</td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="py-3 text-zinc-500">
                  Nothing new on the book for this day.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

/** Litres shipped that day, split real vs expected. */
export function DispatchSplit({ realL, forecastL }: { realL: number; forecastL: number }) {
  const t = realL + forecastL;
  return (
    <div>
      <div className="flex h-2 overflow-hidden rounded">
        <div style={{ width: `${t ? (realL / t) * 100 : 0}%` }} className="bg-emerald-400" />
        <div style={{ width: `${t ? (forecastL / t) * 100 : 0}%` }} className="bg-violet-400" />
      </div>
      <div className="mt-1 flex justify-between text-[11px]">
        <span className="text-emerald-300">{litres(realL)} ordered</span>
        <span className="text-violet-300">{litres(forecastL)} expected</span>
      </div>
    </div>
  );
}
