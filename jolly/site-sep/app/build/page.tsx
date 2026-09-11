import { Card } from "@/components/Card";
import SimBadge from "@/components/SimBadge";
import BuildDayTabs, { type BuildDayMeta } from "@/components/BuildDayTabs";
import BuildDaySection from "@/components/BuildDaySection";
import { dlabel, fmt, getBuild, getOverview, tonnes } from "@/lib/data";

export const metadata = {
  title: "Run list",
  description:
    "Gautam's day-by-day run list for September — every machine, every run in order, every oil change called out.",
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
  const firstDay = B.days[0]?.date ?? O.meta.as_of;

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
            Run list <SimBadge kind="plan" />
          </h1>
          <p className="text-sm text-zinc-300 mt-1 max-w-3xl">
            Gautam&rsquo;s run list for {B.meta.month}. Machine by machine, run by run, oil change by oil change.
          </p>
          <p className="text-xs text-zinc-500 mt-1 max-w-3xl">
            Written for <span className="text-zinc-200">{r.name}</span> ({r.title}
            {r.number_masked ? (
              <>
                , <span className="tabular-nums">{r.display}</span> — number withheld, nobody has approved showing it
              </>
            ) : (
              <>, {r.display}</>
            )}
            ).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5">
        <Card title="Working days" value={`${t.working_days}`} sub={`of ${t.days} days — Sundays off`} />
        <Card
          title="Runs"
          value={fmt(t.runs)}
          sub={`${fmt(t.oil_changes)} oil changes + ${t.clearances_only} bottle-size changes`}
        />
        <Card title="To make" value={`${fmt(t.litres)} L`} sub={`${tonnes(t.litres)} this month`} tone="text-amber-300" />
        <Card title="Biggest day" value={dlabel(peak.date)} sub={`${fmt(peak.made_l)} L`} />
      </div>

      {/* how to read the list */}
      <div className="mt-4 grid md:grid-cols-3 gap-3 text-xs">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
          <div className="uppercase tracking-wider text-zinc-500 text-[10px]">An oil change</div>
          <p className="text-zinc-300 mt-1.5 leading-relaxed">
            Costs time, not oil. Wash the machine with {fmt(rules.flush_litres)} L of the next oil, then clean for
            about {Math.round(rules.line_clearance_min)} min. The wash oil comes back. A bottle-size change on the
            same oil is cleaning only.
          </p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
          <div className="uppercase tracking-wider text-zinc-500 text-[10px]">The green tag on a run</div>
          <p className="text-zinc-300 mt-1.5 leading-relaxed">
            <span className="px-1 py-px rounded border border-emerald-500/40 text-emerald-300 bg-emerald-500/10">
              has a customer order
            </span>{" "}
            — a customer has really ordered this run. No tag — the run is for orders we expect but nobody has placed
            yet. Those are shown in blue as{" "}
            <span className="px-1 py-px rounded border border-sky-500/40 text-sky-300 bg-sky-500/10">
              expected — not ordered yet
            </span>
            . About {fcShare}% of what customers want this month is expected, not ordered.
          </p>
        </div>
        <div className="rounded-xl border border-violet-500/25 bg-violet-500/[0.05] p-3">
          <div className="uppercase tracking-wider text-violet-300 text-[10px]">This is a plan</div>
          <p className="text-zinc-300 mt-1.5 leading-relaxed">
            Nothing below has been run. Only the stock at the start of {dlabel(firstDay)} is real. Every later day is
            worked out from the day before. When material arrives, the list changes — those days say &ldquo;plan
            changed&rdquo;.
          </p>
        </div>
      </div>

      <div className="mt-6">
        <BuildDayTabs days={metas}>
          {B.days.map((d, i) => (
            <BuildDaySection key={d.date} n={i + 1} day={d} rules={rules} />
          ))}
        </BuildDayTabs>
      </div>

      <p className="bl-noprint text-[11px] text-zinc-600 mt-8 max-w-4xl">
        Where this comes from: the computer&rsquo;s day-by-day plan for {B.meta.month}. Stock was counted on{" "}
        {dlabel(O.meta.frozen)} evening. Everything after that is worked out, not recorded.
      </p>
    </div>
  );
}
