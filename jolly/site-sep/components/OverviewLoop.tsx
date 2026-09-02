import Link from "next/link";
import type { LoopChain, LoopsData } from "../lib/types";
import { fmt, dlabel } from "../lib/data";
import { Pill } from "./Card";
import SimBadge from "./SimBadge";

type ResolvedChain = LoopChain & {
  unblocked_day: string;
  first_run_after_unblock: NonNullable<LoopChain["first_run_after_unblock"]>;
};

// THE LOOP — one real blocker→order→land→run chain from the sim's own event
// stream, picked deterministically: the largest order among fully resolved chains.
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

  const unit = pick.kind === "OIL" ? "L" : "pcs";
  const kindWord = pick.kind === "OIL" ? "oil" : "packaging";
  const kindLead = pick.kind === "OIL" ? leadDays.oil : leadDays.packaging;
  const leadMin = Math.min(...loops.chains.map((c) => c.lead_days));
  const leadMax = Math.max(...loops.chains.map((c) => c.lead_days));
  const unresolvedN = loops.ordered_events - loops.resolved_chains;
  const waited = pick.waited_days ?? pick.lead_days;
  const run = pick.first_run_after_unblock;

  const steps: { tag: string; date: string; body: React.ReactNode }[] = [
    {
      tag: "Blocked",
      date: dlabel(pick.ordered_day),
      body: (
        <>
          <span className="text-zinc-100 font-medium tabular-nums">{pick.fg_codes_blocked.length} SKUs</span> want{" "}
          <span className="text-zinc-200">{pick.name}</span>{" "}
          <span className="text-zinc-500">({pick.code})</span> and the store cannot feed them.
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
          the same day. <Pill tone={pick.kind === "OIL" ? "amber" : "blue"}>{pick.kind}</Pill>
        </>
      ),
    },
    {
      tag: "The wait",
      date: `${pick.lead_days} days pass`,
      body: (
        <>
          The measured {kindWord} lead time is{" "}
          <span className="text-zinc-100 font-medium tabular-nums">{kindLead} days</span> — the sim assumes supply
          arrives exactly on it.
        </>
      ),
    },
    {
      tag: "Lands",
      date: dlabel(pick.lands),
      body: (
        <>
          The material arrives and the blocker clears on {dlabel(pick.unblocked_day)} — after{" "}
          <span className="text-zinc-100 font-medium tabular-nums">{waited} days</span> of waiting.
        </>
      ),
    },
    {
      tag: "Runs",
      date: dlabel(run.day),
      body: (
        <>
          First run out of the clear: <span className="text-zinc-200">{run.sku}</span> —{" "}
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
        Every order the plan raises follows that same loop — a shortage the plan never orders against simply stays
        short.{" "}
        <span className="text-zinc-300 tabular-nums">
          {loops.resolved_chains} of {loops.ordered_events}
        </span>{" "}
        order-chains land and unblock inside September — <span className="tabular-nums">{loops.ran_after_unblock}</span>{" "}
        of those see the freed SKU run again before month-end, <span className="tabular-nums">{loops.landed_no_run}</span>{" "}
        clear too late in the schedule to run — and <span className="tabular-nums">{unresolvedN}</span> land only after
        30 Sep. Leads run <span className="tabular-nums">{leadMin}–{leadMax} days</span> ({leadDays.packaging}{" "}
        d packaging, {leadDays.oil} d oil — measured). Watch the chains land day by day on the{" "}
        <Link href="/days" className="text-amber-300 hover:underline">
          day pages
        </Link>
        . <SimBadge kind="simulated" note={loops.note} />
      </p>
    </div>
  );
}
