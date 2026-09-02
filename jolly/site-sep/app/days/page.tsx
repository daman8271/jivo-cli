import { getSpine, getOverview, getLoops, getStorage, fmt, cr, dlabel } from "../../lib/data";
import SimBadge from "../../components/SimBadge";
import { Card } from "../../components/Card";
import { SpineChart, SpineCards, SpineLegend } from "../../components/DaySpine";

export const metadata = {
  title: "Day by day",
  description:
    "The 30-day spine of the September plan — planned fill, invoicing, line use and godown occupancy for every day.",
};

export default function Days() {
  const S = getSpine();
  const o = getOverview();
  const loops = getLoops();
  const st = getStorage();
  const roofDays = S.filter((d) => d.storage_pct >= 100);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Day by day — the 30-day spine</h1>
        <SimBadge kind="plan" />
      </div>
      <p className="mt-2 max-w-4xl text-sm text-zinc-400">
        {o.meta.forward_rule} Day 1 opens from the measured 31-Aug close; every later day is computed from the day
        before plus the planner&apos;s algorithm. Each column links to that day&apos;s full page — runs and changeovers,
        news of the day, blockers, the order loop, the storage waterfall.
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Card title="Planned fill" value={`${fmt(o.totals.made_l)} L`} sub={`${cr(o.totals.value_rs)} across ${o.totals.working_days} working days`} />
        <Card title="Planned invoicing" value={`${fmt(o.totals.shipped_l)} L`} sub="orders + forecast served" />
        <Card title="Runs" value={fmt(o.totals.runs)} sub={`${fmt(o.totals.oil_changes)} oil changes on the lines`} />
        <Card title="Line use, median" value={`${o.totals.util_median}%`} sub={`peak day ${dlabel(o.totals.peak_day.date)} — ${fmt(o.totals.peak_day.made_l)} L`} />
        <Card
          title="Godown at the roof"
          value={roofDays.length === 1 ? "1 day" : `${roofDays.length} days`}
          sub={
            roofDays.length > 0
              ? `${roofDays.map((d) => dlabel(d.date)).join(", ")} — roof is assumed (${st.ceiling.open_question})`
              : `roof is assumed (${st.ceiling.open_question})`
          }
          tone={roofDays.length > 0 ? "text-red-400" : ""}
        />
        <Card
          title="Loops landed in-month"
          value={`${loops.resolved_chains} of ${loops.chains.length}`}
          sub={`blocker → order → land chains that unblock by 30 Sep — ${loops.ran_after_unblock} run the freed SKU again in-month`}
        />
      </div>

      <div className="mt-3 rounded-lg border border-sky-500/20 bg-sky-500/5 px-3 py-2 text-xs text-sky-200/90">
        <SimBadge kind="forecast" />{" "}
        <span className="tabular-nums font-semibold">{o.demand.forecast_share_litres_pct}%</span> of the demand stream by
        litres is FORECAST, not orders — {o.demand.note}
      </div>

      <section className="mt-7">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">The spine, four signals per day</h2>
          <span className="text-xs text-zinc-500">every panel scales to its own peak — click a column to open the day</span>
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
            {S.filter((d) => d.working).length} working · {S.filter((d) => !d.working).length} Sundays off
          </span>
        </div>
        <div className="mt-3">
          <SpineCards spine={S} />
        </div>
      </section>
    </div>
  );
}
