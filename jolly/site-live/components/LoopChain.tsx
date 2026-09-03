"use client";

// The loop that makes this planner worth having:
//   a product is STUCK for want of a material  →  the planner ORDERS it
//   →  it LANDS  →  the product is FREED  →  it RUNS
// One chain per missing item, straight out of plan/loops.json.

import { asLoops, useLive } from "../lib/live";
import { dlabel, inr, plural } from "../lib/fmt";
import { Panel, Pill } from "./Card";
import { AsOf, Live } from "./Freshness";
import SimBadge from "./SimBadge";

export default function LoopChain({ limit }: { limit?: number }) {
  const live = useLive(["loops"]);
  const L = asLoops(live.loops);
  const chains = (L?.chains ?? []).slice(0, limit ?? undefined);

  return (
    <Panel
      title="Stuck → ordered → arrived → running"
      badge={<SimBadge kind="plan" />}
      asOf={<AsOf rec={live.loops} />}
      note={L?.note}
    >
      <Live rec={live.loops} what="the chains">
        {L && (
          <>
            <div className="mb-3 flex flex-wrap gap-2 text-xs">
              <Pill tone="amber">{inr(L.ordered_events ?? L.chains.length)} ordered</Pill>
              <Pill tone="blue">{inr(L.resolved_chains ?? 0)} arrive inside this plan</Pill>
              <Pill tone="green">{inr(L.ran_after_unblock ?? 0)} actually run again</Pill>
              {(L.landed_no_run ?? 0) > 0 && <Pill tone="zinc">{inr(L.landed_no_run!)} arrive but never run</Pill>}
            </div>
            {L.resolved_note && <p className="mb-3 text-xs text-zinc-500">{L.resolved_note as string}</p>}
            <ul className="space-y-2">
              {chains.map((c) => (
                <li key={`${c.code}-${c.ordered_day}`} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-2.5">
                  <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
                    <span className="font-mono text-[11px] text-zinc-500">{c.code}</span>
                    <span className="font-medium">{c.name}</span>
                    <Pill tone={c.kind === "OIL" ? "amber" : "zinc"}>{c.kind.toLowerCase()}</Pill>
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-zinc-400">
                    <span className="text-red-300">
                      stuck: {c.fg_codes_blocked?.length ?? 0}{" "}
                      {plural(c.fg_codes_blocked?.length ?? 0, "product", "products")}
                    </span>
                    <span className="text-zinc-600">→</span>
                    <span>
                      order {inr(c.qty)} on {dlabel(c.ordered_day)}
                    </span>
                    <span className="text-zinc-600">→</span>
                    <span>
                      lands {dlabel(c.lands)} ({c.lead_days} {plural(c.lead_days, "day", "days")})
                    </span>
                    <span className="text-zinc-600">→</span>
                    {c.unblocked_day ? (
                      <span className="text-emerald-300">freed {dlabel(c.unblocked_day)}</span>
                    ) : (
                      <span className="text-amber-300">still stuck at the end of the month</span>
                    )}
                    {c.first_run_after_unblock && (
                      <>
                        <span className="text-zinc-600">→</span>
                        <span className="text-emerald-300">
                          runs {dlabel(c.first_run_after_unblock.day)}: {c.first_run_after_unblock.sku}
                        </span>
                      </>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </Live>
    </Panel>
  );
}
