import { getSpine, getOverview, getLoops, fmt, cr, dlabel } from "../../lib/data";
import SimBadge from "../../components/SimBadge";
import { Card } from "../../components/Card";
import { SpineChart, SpineCards, SpineLegend } from "../../components/DaySpine";

export const metadata = {
  title: "Day by day",
  description:
    "The September plan, one day at a time — litres made, litres billed, machines busy and how full the godown is. A plan made by computer; nothing here has happened.",
};

export default function Days() {
  const S = getSpine();
  const o = getOverview();
  const loops = getLoops();
  const roofDays = S.filter((d) => d.storage_pct >= 100);
  const workingDays = S.filter((d) => d.working).length;
  const offDays = S.length - workingDays;
  const stockDate = dlabel(o.meta.frozen);
  const lastDay = dlabel(S[S.length - 1].date);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Day by day — all {S.length} days</h1>
        <SimBadge kind="plan" />
      </div>
      <p className="mt-2 max-w-4xl text-sm text-zinc-400">
        Only the stock counted on {stockDate} is real. Every day below is the computer&apos;s plan, built on the day
        before it. Nothing has happened yet. Click a day to see what runs on each machine, what arrives, what is
        stuck, and how full the godown is.
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Card title="Made this month" value={`${fmt(o.totals.made_l)} L`} sub={`${cr(o.totals.value_rs)} · ${o.totals.working_days} working days`} />
        <Card title="Billed this month" value={`${fmt(o.totals.shipped_l)} L`} sub="confirmed orders + expected orders" />
        <Card title="Runs" value={fmt(o.totals.runs)} sub={`${fmt(o.totals.oil_changes)} oil changes`} />
        <Card title="Machines busy, typical day" value={`${o.totals.util_median}%`} sub={`biggest day ${dlabel(o.totals.peak_day.date)} — ${fmt(o.totals.peak_day.made_l)} L`} />
        <Card
          title="Godown full"
          value={roofDays.length === 1 ? "1 day" : `${roofDays.length} days`}
          sub={
            roofDays.length > 0
              ? `${roofDays.map((d) => dlabel(d.date)).join(", ")} — the limit is Daman's number, not measured`
              : "never full this month — but the limit is Daman's number, not measured"
          }
          tone={roofDays.length > 0 ? "text-red-400" : ""}
        />
        <Card
          title="Stuck items that arrive this month"
          value={`${loops.resolved_chains} of ${loops.chains.length}`}
          sub={`ordered → arrived by ${lastDay}, so the product can run again — the plan runs ${loops.ran_after_unblock} of them again before the month ends`}
        />
      </div>

      <div className="mt-3 rounded-lg border border-sky-500/20 bg-sky-500/5 px-3 py-2 text-xs text-sky-200/90">
        <span className="tabular-nums font-semibold">{o.demand.forecast_share_litres_pct}%</span> of what customers want this
        month is <span className="font-semibold">expected — not ordered yet</span>. Those orders are blue on every day
        page, so they never mix with confirmed orders.
      </div>

      <section className="mt-7">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">Four things, every day</h2>
          <span className="text-xs text-zinc-500">each row scales to its own biggest day — click a column to open the day</span>
        </div>
        <div className="mt-3 overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <SpineChart spine={S} />
        </div>
        <SpineLegend spine={S} />
      </section>

      <section className="mt-8">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">All {S.length} days</h2>
          <span className="text-xs text-zinc-500">
            {workingDays} working · {offDays} Sundays off
          </span>
        </div>
        <div className="mt-3">
          <SpineCards spine={S} />
        </div>
      </section>

      <p className="mt-8 text-[11px] text-zinc-600">
        Where these numbers come from: stock and open orders from SAP on {stockDate}; every later day is the computer
        plan, built on the day before. Tested on August — the computer said {fmt(o.august.sim_made_l)} L, the factory
        made {fmt(o.august.actual_made_l)} L.
      </p>
    </div>
  );
}
