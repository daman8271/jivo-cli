import { getAllDays, getSummary, fmt } from "@/lib/data";
import { LINES } from "@/lib/types";
import { Card, Section, Pill } from "@/components/Card";
import FloorScene, { type FloorDay } from "@/components/FloorScene";

export const metadata = { title: "Floor 3D — JIVO Mark 1" };

export default function FloorPage() {
  const all = getAllDays();
  const summary = getSummary();

  const days: FloorDay[] = all.map((d, i) => ({
    n: i + 1,
    date: d.date,
    weekday: d.weekday,
    working: d.working,
    hours: LINES.map((l) => d.line_hours[l] ?? 0),
    onLine: LINES.map((l) => {
      const rs = d.runs.filter((r) => r.line === l);
      if (!rs.length) return null;
      const top = rs.reduce((a, b) => (b.litres > a.litres ? b : a));
      return {
        sku: top.sku,
        oil: top.oil ?? "",
        head: top.head,
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
    loads: d.dispatched.length,
    runs: d.runs.length,
    note: d.decisions[0]?.text ?? null,
  }));

  const ceiling = all[0].storage.ceiling_l;
  const capped = all.filter((d) => d.storage.pct >= 95).length;
  const busiest = all.reduce((a, b) => (b.line_util > a.line_util ? b : a));
  const busiestDay = Number(busiest.date.split("-")[2]);
  const honesty = all[0].honesty;

  return (
    <div>
      <h1 className="text-2xl font-semibold">The floor, day by day</h1>
      <p className="mt-1 max-w-3xl text-sm text-zinc-400">
        Six filling lines, one godown, one dock — the same August the rest of this site counts, drawn to scale.
        Pull the slider, or press Play to watch the month run at one day per second. Drag to walk around it.
      </p>

      <div className="mt-6">
        <FloorScene days={days} />
      </div>

      <Section title="The month behind the scene">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Card title="Made in August" value={`${fmt(summary.totals.made_l)} L`} sub={`across ${summary.days.filter((d) => d.working).length} working days`} />
          <Card title="Shipped out" value={`${fmt(summary.totals.shipped_l)} L`} sub="invoiced and trucked" />
          <Card title="Busiest line day" value={`${busiestDay} Aug`} tone="text-amber-300" sub={`${busiest.line_util}% of the shift used — ${busiest.runs.length} runs`} />
          <Card title="Godown at its cap" value={`${capped} of 31 days`} tone="text-red-400" sub={`95% of the ${fmt(ceiling)} L ceiling`} />
        </div>
      </Section>

      <Section title="What is measured, what is assumed">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="text-xs uppercase tracking-wider text-zinc-500">Measured</div>
          <div className="mt-2 flex flex-wrap gap-2">{honesty.measured.map((m) => <Pill key={m} tone="green">{m}</Pill>)}</div>
          <div className="mt-4 text-xs uppercase tracking-wider text-zinc-500">Assumed</div>
          <div className="mt-2 flex flex-wrap gap-2">{honesty.assumed.map((a) => <Pill key={a} tone="amber">{a}</Pill>)}</div>
          <p className="mt-4 text-sm text-zinc-400">
            The blocks are hours of running, not output — a tall block on a slow line makes fewer litres than a short one
            on a fast line. Height is drawn against the full 12-hour shift, and the shift is run at rated line speed, not
            the 47% actually observed.
          </p>
        </div>
      </Section>
    </div>
  );
}
