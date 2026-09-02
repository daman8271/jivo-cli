import { Card } from "@/components/Card";
import SimBadge from "@/components/SimBadge";
import BuildDayTabs, { type BuildDayMeta } from "@/components/BuildDayTabs";
import BuildDaySection from "@/components/BuildDaySection";
import { dlabel, fmt, getBuild, getOverview, tonnes } from "@/lib/data";

export const metadata = {
  title: "Build list",
  description:
    "Gautam's day-by-day build lists for the September plan — runs in sequence with oil changes and clearances called out.",
};

// Print: the selected day prints alone; "All days" prints the month one day per
// sheet. Dark chrome flips to plain black-on-white so the sheet survives a
// factory printer. header/footer/picker are hidden; the plan-not-record banner
// deliberately stays — it should be on the paper too.
const PRINT_CSS = `
@media print {
  header, footer, .bl-noprint { display: none !important; }
  body { background: #fff !important; }
  body * {
    background: transparent !important;
    color: #000 !important;
    border-color: #d4d4d8 !important;
    box-shadow: none !important;
    text-shadow: none !important;
  }
  main { max-width: 100% !important; padding: 0 !important; }
  .bl-page + .bl-page { break-before: page; page-break-before: always; }
  .bl-day { border: none !important; padding: 8px 0 !important; margin-top: 0 !important; }
  a { text-decoration: none !important; }
}
`;

export default function BuildPage() {
  const B = getBuild();
  const O = getOverview();
  const t = B.meta.totals;
  const r = B.meta.recipient;
  const rules = B.meta.rules;
  const fcShare = Math.round(O.demand.forecast_share_litres_pct);
  const peak = O.totals.peak_day;

  const metas: BuildDayMeta[] = B.days.map((d, i) => ({
    n: i + 1,
    dom: Number(d.date.slice(8, 10)),
    wd: d.weekday.slice(0, 1),
    working: d.working,
    litres: d.made_litres,
    label: `${d.weekday} ${dlabel(d.date)}`,
  }));

  return (
    <div className="bl-root">
      <style>{PRINT_CSS}</style>

      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">
            Build list <SimBadge kind="plan" />
          </h1>
          <p className="text-sm text-zinc-400 mt-1 max-w-3xl">
            Gautam&rsquo;s page — {B.meta.month}, machine by machine, run by run, changeover by changeover. Written for{" "}
            <span className="text-zinc-200">{r.name}</span> ({r.title}
            {r.number_masked ? (
              <>
                , <span className="tabular-nums">{r.display}</span> — number masked, September has no approval to show
                it
              </>
            ) : (
              <>, {r.display}</>
            )}
            ).
          </p>
        </div>
        <div className="text-xs text-zinc-500 text-right max-w-xs">source: {B.meta.source}</div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5">
        <Card title="Working days" value={`${t.working_days}`} sub={`of ${t.days} days — Sundays off`} />
        <Card
          title="Runs to make"
          value={fmt(t.runs)}
          sub={`${fmt(t.oil_changes)} oil changes + ${t.clearances_only} clearance-only switches`}
        />
        <Card title="To fill" value={`${fmt(t.litres)} L`} sub={`${tonnes(t.litres)} across the month`} tone="text-amber-300" />
        <Card title="Biggest day" value={dlabel(peak.date)} sub={`${fmt(peak.made_l)} L planned`} />
      </div>

      {/* how to read the list */}
      <div className="mt-4 grid md:grid-cols-3 gap-3 text-xs">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
          <div className="uppercase tracking-wider text-zinc-500 text-[10px]">The changeover rule</div>
          <p className="text-zinc-300 mt-1.5 leading-relaxed">{rules.note}. The flush oil comes back — the minutes don&rsquo;t.</p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
          <div className="uppercase tracking-wider text-zinc-500 text-[10px]">
            The{" "}
            <span className="normal-case tracking-normal text-[10px] px-1 py-px rounded border border-emerald-500/40 text-emerald-300 bg-emerald-500/10">
              PO-backed
            </span>{" "}
            tag
          </div>
          <p className="text-zinc-300 mt-1.5 leading-relaxed">
            When that run was scheduled, the SKU still had open pieces on a <em>real</em> customer order. Untagged runs
            build to the monthly plan&rsquo;s FORECAST demand <SimBadge kind="forecast" /> — about {fcShare}% of
            September&rsquo;s demand stream by litres is forecast, not orders.
          </p>
        </div>
        <div className="rounded-xl border border-violet-500/25 bg-violet-500/[0.05] p-3">
          <div className="uppercase tracking-wider text-violet-300 text-[10px]">This is a plan</div>
          <p className="text-zinc-300 mt-1.5 leading-relaxed">
            Nothing below has been run. Only the 1-September opening is observed; every later day is computed, and the
            sequence re-plans as POs land — those days carry a &ldquo;plan changed&rdquo; note.
          </p>
        </div>
      </div>

      <div className="mt-6">
        <BuildDayTabs days={metas}>
          {B.days.map((d, i) => (
            <BuildDaySection key={d.date} n={i + 1} day={d} />
          ))}
        </BuildDayTabs>
      </div>
    </div>
  );
}
