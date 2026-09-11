import Link from "next/link";
import type { LoopChain, LoopsData } from "../lib/types";
import { fmt, dlabel } from "../lib/data";
import { Pill } from "./Card";

type ResolvedChain = LoopChain & {
  unblocked_day: string;
  first_run_after_unblock: NonNullable<LoopChain["first_run_after_unblock"]>;
};

// STUCK → ORDERED → ARRIVED → RUNNING — one example chain from the plan's own
// events (simulated, nothing happened), picked deterministically: the largest
// order among chains that got all the way to a run. On this site "real" means
// counted in SAP, so never call the example "real". Words: PLAIN-LANGUAGE.md.
export default function OverviewLoop({
  loops,
  leadDays,
}: {
  loops: LoopsData;
  leadDays: { oil: number; packaging: number };
}) {
  const resolved = loops.chains.filter(
    (c): c is ResolvedChain => Boolean(c.unblocked_day && c.first_run_after_unblock)
  );
  if (resolved.length === 0) return null;
  const pick = resolved.reduce((a, b) => (b.qty > a.qty ? b : a));

  const isOil = pick.kind === "OIL";
  const unit = isOil ? "L" : "pcs";
  const kindWord = isOil ? "Oil" : "Packing material";
  const kindLead = isOil ? leadDays.oil : leadDays.packaging;
  const leadMin = Math.min(...loops.chains.map((c) => c.lead_days));
  const leadMax = Math.max(...loops.chains.map((c) => c.lead_days));
  const afterMonth = loops.ordered_events - loops.resolved_chains;
  const waited = pick.waited_days ?? pick.lead_days;
  const run = pick.first_run_after_unblock;
  const nProducts = pick.fg_codes_blocked.length;

  const steps: { tag: string; date: string; body: React.ReactNode }[] = [
    {
      tag: "Stuck",
      date: dlabel(pick.ordered_day),
      body: (
        <>
          <span className="text-zinc-100 font-medium tabular-nums">
            {nProducts} {nProducts === 1 ? "product" : "products"}
          </span>{" "}
          need <span className="text-zinc-200">{pick.name.toLowerCase()}</span>{" "}
          <span className="text-zinc-500">({pick.code})</span>. There is not enough in stock.
        </>
      ),
    },
    {
      tag: "Ordered",
      date: dlabel(pick.ordered_day),
      body: (
        <>
          The planner orders{" "}
          <span className="text-zinc-100 font-medium tabular-nums">
            {fmt(pick.qty)} {unit}
          </span>{" "}
          the same day. <Pill tone={isOil ? "amber" : "blue"}>{isOil ? "oil" : "packing material"}</Pill>
        </>
      ),
    },
    {
      tag: "Waiting",
      date: `${pick.lead_days} days`,
      body: (
        <>
          {kindWord} takes <span className="text-zinc-100 font-medium tabular-nums">{kindLead} days</span> to arrive
          — measured, real. The plan guesses it arrives exactly on time.
        </>
      ),
    },
    {
      tag: "Arrived",
      date: dlabel(pick.lands),
      body: (
        <>
          The material arrives. The products are free to run from {dlabel(pick.unblocked_day)} — after{" "}
          <span className="text-zinc-100 font-medium tabular-nums">{waited} days</span> of waiting.
        </>
      ),
    },
    {
      tag: "Running",
      date: dlabel(run.day),
      body: (
        <>
          First run after that: <span className="text-zinc-200">{run.sku}</span> —{" "}
          <span className="text-zinc-100 font-medium tabular-nums">{fmt(run.litres)} L</span>.
        </>
      ),
    },
  ];

  return (
    <div>
      <ol className="grid md:grid-cols-5 gap-2">
        {steps.map((s, i) => (
          <li key={s.tag} className="relative rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 text-[11px] font-semibold flex items-center justify-center tabular-nums">
                {i + 1}
              </span>
              <span className="text-[10px] uppercase tracking-wider text-zinc-500">{s.tag}</span>
            </div>
            <div className="text-sm font-semibold mt-2 tabular-nums">{s.date}</div>
            <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">{s.body}</p>
            {i < steps.length - 1 && (
              <span className="hidden md:block absolute top-1/2 -right-[7px] text-zinc-600 text-xs z-10">→</span>
            )}
          </li>
        ))}
      </ol>
      <p className="text-xs text-zinc-500 mt-3 leading-relaxed">
        Every order in the plan goes the same way. If the planner does not order, the shortage stays.{" "}
        <span className="text-zinc-300 tabular-nums">
          {loops.resolved_chains} of {loops.ordered_events}
        </span>{" "}
        orders arrive within September. <span className="tabular-nums">{loops.ran_after_unblock}</span> of those
        products run again before month end. <span className="tabular-nums">{loops.landed_no_run}</span> arrive too late
        in the month to run. <span className="tabular-nums">{afterMonth}</span> arrive only after September.
        Arrival takes <span className="tabular-nums">{leadMin}–{leadMax} days</span> ({leadDays.packaging} days for
        packing material, {leadDays.oil} days for oil — measured, real). See each one arrive on the{" "}
        <Link href="/days" className="text-amber-300 hover:underline">
          day pages
        </Link>
        . All of this is the computer plan — none of it has happened.
      </p>
    </div>
  );
}
