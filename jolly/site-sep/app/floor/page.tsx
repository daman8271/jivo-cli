import { getAllDays, getBuild, getLines, getOverview, getStorage, fmt, cr, dlabel } from "../../lib/data";
import { LINES } from "../../lib/types";
import SimBadge from "../../components/SimBadge";
import { Card, Section, Pill } from "../../components/Card";
import FloorSepScene, { type FloorDay, type OilLegendItem } from "../../components/FloorSepScene";

export const metadata = {
  title: "Floor 3D",
  description:
    "The planned September on the factory floor in 3D — lines, oils, oil changes and dispatches, day by day.",
};

export default function FloorPage() {
  const all = getAllDays();
  const o = getOverview();
  const St = getStorage();
  const L = getLines();

  // oil RM code → oil name, read off the build list's own runs
  const oilName: Record<string, string> = {};
  for (const bd of getBuild().days)
    for (const m of bd.machines)
      for (const r of m.runs) if (r.oil && r.oil_name) oilName[r.oil] = r.oil_name;

  // the shift length, derived from the day files themselves (max planned line hours)
  let maxH = 0;
  for (const d of all) for (const ln of LINES) maxH = Math.max(maxH, d.line_hours[ln] ?? 0);
  const shiftH = Math.round(maxH * 10) / 10;

  const days: FloorDay[] = all.map((d) => ({
    n: d.n,
    date: d.date,
    weekday: d.weekday,
    working: d.working,
    hours: LINES.map((ln) => d.line_hours[ln] ?? 0),
    onLine: LINES.map((ln) => {
      const rs = d.runs.filter((r) => r.line === ln);
      if (!rs.length) return null;
      const top = rs.reduce((a, b) => (b.litres > a.litres ? b : a));
      return {
        sku: top.sku,
        head: top.head,
        oil: top.oil ? (oilName[top.oil] ?? top.oil) : null,
        pieces: Math.round(rs.reduce((n, r) => n + r.pieces, 0)),
        litres: Math.round(rs.reduce((n, r) => n + r.litres, 0)),
        runs: rs.length,
        flushes: rs.filter((r) => r.flush_min > 0).length,
      };
    }),
    util: d.line_util,
    madeL: d.made_litres,
    shippedL: d.shipped_litres,
    pct: d.storage.pct,
    physicalL: d.storage.physical_l,
    ceilingL: d.storage.ceiling_l,
    headroomL: d.storage.headroom_l,
    loadsReal: d.dispatched_real.length,
    loadsFcst: d.dispatched_forecast.length,
    runs: d.runs.length,
    oilChanges: d.runs.filter((r) => r.flush_min > 0).length,
    note: d.decisions[0]?.text ?? null,
  }));

  // which oils the plan runs, biggest first — feeds the colour key
  const oilLitres = new Map<string, number>();
  for (const d of all)
    for (const r of d.runs)
      if (r.oil) {
        const nm = oilName[r.oil] ?? r.oil;
        oilLitres.set(nm, (oilLitres.get(nm) ?? 0) + r.litres);
      }
  const oilLegend: OilLegendItem[] = [...oilLitres.entries()]
    .map(([name, litres]) => ({ name, litres }))
    .sort((a, b) => b.litres - a.litres);

  const busiest = all.reduce((a, b) => (b.line_util > a.line_util ? b : a));
  const honesty = all[0].honesty;

  return (
    <div>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">The floor, day by day</h1>
        <SimBadge kind="plan" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-400">
        {L.lines.length} filling lines, one godown, one dock — the September <em>plan</em> drawn to scale. None of this has
        happened: it is the simulator&apos;s schedule, {fmt(o.totals.runs)} runs and {o.totals.oil_changes} oil changes
        over {o.totals.working_days} planned working days. Pull the slider or press Play to watch the month the plan
        would run, one day per second; drag to walk around it. Block colour is the oil on the line; the beacons flash
        where the line changes oil that day.
      </p>

      <div className="mt-6">
        <FloorSepScene
          days={days}
          shiftH={shiftH}
          ceilingAssumed={St.ceiling.assumed}
          ceilingQ={St.ceiling.open_question}
          oilLegend={oilLegend}
        />
      </div>

      <Section title="The planned month behind the scene">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Card
            title="Planned output"
            value={`${fmt(o.totals.made_l)} L`}
            sub={`${cr(o.totals.value_rs)} across ${o.totals.working_days} working days — simulated`}
          />
          <Card
            title="Planned dispatches"
            value={`${fmt(o.totals.shipped_l)} L`}
            sub={`${o.demand.forecast_share_litres_pct}% of the demand stream is FORECAST (by litres)`}
          />
          <Card
            title="Busiest planned day"
            value={dlabel(busiest.date)}
            tone="text-amber-300"
            sub={`${busiest.line_util}% of the shift used — ${busiest.runs.length} runs`}
          />
          <Card
            title="Godown at the assumed cap"
            value={`${o.storage.days_ge_100.length} of ${o.totals.days} days`}
            tone="text-red-400"
            sub={`${o.storage.days_ge_95} days ≥95% of the ${fmt(o.storage.ceiling_l)} L ceiling — assumed (${St.ceiling.open_question})`}
          />
        </div>
      </Section>

      <Section title="What is measured, what is assumed">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="text-xs uppercase tracking-wider text-zinc-500">Measured (31 Aug opening)</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {honesty.measured.map((m) => (
              <Pill key={m} tone="green">
                {m}
              </Pill>
            ))}
          </div>
          <div className="mt-4 text-xs uppercase tracking-wider text-zinc-500">Assumed (declared)</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {honesty.assumed.map((a) => (
              <Pill key={a} tone="amber">
                {a}
              </Pill>
            ))}
          </div>
          <p className="mt-4 text-sm text-zinc-400">
            The blocks are hours of planned running, not output — a tall block on a slow line makes fewer litres than a
            short one on a fast line. Height is drawn against the full {shiftH}-hour shift, and the plan already runs
            every line at an efficiency of {Math.round(L.efficiency * 100)}%: {L.efficiency_note}.
          </p>
          <p className="mt-2 text-sm text-zinc-400">
            The godown ceiling the red ring marks ({fmt(St.ceiling.working_l)} L working, {fmt(St.ceiling.peak_l)} L
            peak) is {St.ceiling.source} — open question {St.ceiling.open_question}. Ghost trucks are FORECAST demand
            rows: volume the plan expects but nobody has ordered yet.
          </p>
        </div>
      </Section>
    </div>
  );
}
