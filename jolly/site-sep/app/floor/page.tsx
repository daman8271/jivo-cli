import {
  getAllDays, getBuild, getLines, getMaterials, getOverview, getStorage, fmt, cr, dlabel, plainHonestyNote, slotNames, plural,
} from "../../lib/data";
import type { HonestyFacts } from "../../lib/data";
import { LINES } from "../../lib/types";
import SimBadge from "../../components/SimBadge";
import { Card, Section, Pill } from "../../components/Card";
import FloorSepScene, { type FloorDay, type OilLegendItem } from "../../components/FloorSepScene";

export const metadata = {
  title: "Floor map",
  description: "The September plan drawn on the factory floor — machines, oils, oil changes and trucks, one day at a time.",
};

export default function FloorPage() {
  const all = getAllDays();
  const o = getOverview();
  const St = getStorage();
  const L = getLines();
  const lead = getMaterials().lead_days;

  const countedOn = dlabel(o.meta.frozen); // the day the stock was counted

  // oil RM code → oil name, read off the run list's own runs
  const oilName: Record<string, string> = {};
  for (const bd of getBuild().days)
    for (const m of bd.machines)
      for (const r of m.runs) if (r.oil && r.oil_name) oilName[r.oil] = r.oil_name;

  // the shift length, worked out from the day files themselves (max planned machine hours)
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
    blocked: d.blocked.length,
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

  // The measured / guess notes in the data are one-liners written for engineers.
  // lib's plainHonestyNote says each one in floor words — the same words the day
  // pages use. Every figure inside a line is read from the data, here.
  const facts: HonestyFacts = {
    stockDate: countedOn,
    products: o.plan.skus,
    leadOil: lead.oil,
    leadPack: lead.packaging,
    lagDays: St.invoice_truck_lag_days,
    efficiency: L.efficiency,
    expectedPct: o.demand.forecast_share_litres_pct,
    observedSlots: slotNames(L, "observed"),
    derivedSlots: slotNames(L, "derived"),
  };

  return (
    <div>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">Floor map</h1>
        <SimBadge kind="plan" note="The computer's plan for September. Nothing here has happened yet." />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {L.lines.length} machines, one godown, one truck gate. Press Play to watch September run, one day per second.
      </p>
      <p className="mt-1 max-w-3xl text-sm text-zinc-400">
        None of this has happened. It is the computer&apos;s plan: {fmt(o.totals.runs)} runs and {o.totals.oil_changes}{" "}
        oil changes over {o.totals.working_days} working days. Block colour is the oil on the machine. The yellow light
        blinks where a machine changes oil that day. Drag to walk around.
      </p>

      <div className="mt-6">
        <FloorSepScene days={days} shiftH={shiftH} ceilingAssumed={St.ceiling.assumed} oilLegend={oilLegend} />
      </div>

      <Section title="The month in four numbers">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Card
            title="Made in September"
            value={`${fmt(o.totals.made_l)} L`}
            sub={`${cr(o.totals.value_rs)} in ${o.totals.working_days} working days — the plan, not done yet`}
          />
          <Card
            title="Billed"
            value={`${fmt(o.totals.shipped_l)} L`}
            sub={`about ${Math.round(o.demand.forecast_share_litres_pct)}% of what customers want is expected — not ordered yet`}
          />
          <Card
            title="Busiest day"
            value={dlabel(busiest.date)}
            tone="text-amber-300"
            sub={`machines busy ${busiest.line_util}% — ${busiest.runs.length} runs`}
          />
          <Card
            title="Days the godown is full"
            value={`${o.storage.days_ge_100.length} of ${o.totals.days}`}
            tone="text-red-400"
            sub={`${o.storage.days_ge_95} ${plural(o.storage.days_ge_95, "day", "days")} at 95% or more of ${fmt(o.storage.ceiling_l)} L${
              St.ceiling.assumed ? " — Daman's number, not measured" : ""
            }`}
          />
        </div>
      </Section>

      <Section title="What is measured — real, and what is our guess">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="text-xs uppercase tracking-wider text-zinc-500">Measured — real</div>
          <ul className="mt-2 space-y-1.5 text-sm text-zinc-300">
            {honesty.measured.map((m) => (
              <li key={m} className="flex items-start gap-2">
                <Pill tone="green">real</Pill>
                <span>{plainHonestyNote(m, facts)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 text-xs uppercase tracking-wider text-zinc-500">Our guess — not measured</div>
          <ul className="mt-2 space-y-1.5 text-sm text-zinc-300">
            {honesty.assumed.map((a) => (
              <li key={a} className="flex items-start gap-2">
                <Pill tone="amber">guess</Pill>
                <span>{plainHonestyNote(a, facts)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-sm text-zinc-400">
            A tall block means more hours, not more litres. A slow machine makes fewer litres in the same hours. Blocks
            are drawn against a {shiftH}-hour shift.
          </p>
          <p className="mt-2 text-sm text-zinc-400">
            The red line is the godown limit: {fmt(St.ceiling.working_l)} L normally, up to {fmt(St.ceiling.peak_l)} L
            packed tight.{St.ceiling.assumed ? " That is Daman's number — not measured." : ""} See-through trucks are
            expected orders — nobody has ordered them yet.
          </p>
        </div>
      </Section>

      <p className="mt-4 text-xs text-zinc-500">
        Where this comes from: the day-by-day plan files, the machine list and the godown file that the planner writes.
        Every number on this page is read from them.
      </p>
    </div>
  );
}
