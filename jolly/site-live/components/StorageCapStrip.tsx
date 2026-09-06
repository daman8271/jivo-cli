"use client";

// B20 — THE RULE THAT MAKES THIS PLAN, on the page that exists to make the rules
// visible.
//
// The engine caps every single run to the room left in the godown. On this run that
// cap holds production back on most of the working days, decides the great majority
// of the sheet, and leaves most of the month's products unmade — and until the day
// this file was written it appeared nowhere at all: not in a settled ruling, not in an assumption, not in a
// build choice, and not in one word of copy. A reader could walk the whole site and
// come away thinking the plant was short of bottles or short of hours.
//
// Every figure below is read off `overview.storage_cap`, which gen_live.py counts off
// the days the engine just produced. Nothing here is typed.

import Link from "next/link";
import { asOverview, useLive } from "../lib/live";
import { maskDigits } from "../lib/labels";
import { dlabel, inr, litres, pct1, plural } from "../lib/fmt";
import { Panel, Pill, Stat } from "./Card";
import { AsOf, Live } from "./Freshness";
import SimBadge from "./SimBadge";

/** The one-line version, for the top of the front page. */
export function StorageCapBanner() {
  const live = useLive(["overview"]);
  const cap = asOverview(live.overview)?.storage_cap ?? null;
  if (!cap?.in_effect) return null;
  return (
    <div className="mt-3 rounded-lg border border-amber-500/40 bg-amber-500/5 px-3 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <Pill tone="amber">the rule that governs this plan</Pill>
        <span className="text-[10px] uppercase tracking-wider text-zinc-500">
          a choice the build made — {cap.rule}
        </span>
      </div>
      <p className="mt-1 text-sm text-amber-100">{maskDigits(cap.headline)}</p>
    </div>
  );
}

/** The full panel, with what the cap did and what it left unmade. */
export default function StorageCapStrip() {
  const live = useLive(["overview"]);
  const o = asOverview(live.overview);
  const cap = o?.storage_cap ?? null;
  const never = cap?.products_never_made_top ?? [];

  return (
    <Panel
      title="The godown limit — what it does to this plan"
      badge={<SimBadge kind="plan" />}
      asOf={<AsOf rec={live.overview} />}
      note={cap ? maskDigits(cap.what_it_does) : undefined}
    >
      <Live rec={live.overview} what="the plan">
        {cap && (
          <>
            <div className="flex flex-wrap gap-x-8 gap-y-3">
              <Stat
                k="Days it held production back"
                v={`${inr(cap.days_it_bit)} of ${inr(cap.working_days)}`}
                tone={cap.days_it_bit > 0 ? "text-red-300" : "text-emerald-300"}
                sub={`working days left in the month — ${inr(cap.days_throttled)} of them already opened nearly full`}
              />
              <Stat
                k="How much of the sheet gets made"
                v={cap.month_made_pct_of_sheet == null ? "—" : pct1(cap.month_made_pct_of_sheet)}
                tone="text-amber-300"
                sub={`${litres(cap.month_made_l)} of ${litres(cap.month_sheet_l)}`}
              />
              <Stat
                k="Products never made at all"
                v={`${inr(cap.products_never_made)} of ${inr(cap.products_on_the_sheet)}`}
                tone={cap.products_never_made > 0 ? "text-red-300" : "text-emerald-300"}
                sub="on the month's target, and no run anywhere in the plan"
              />
              {cap.litres_cut_off_runs_it_allowed != null && (
                <Stat
                  k="Taken off runs it did allow"
                  v={litres(cap.litres_cut_off_runs_it_allowed)}
                  sub={
                    cap.runs_cut_short != null
                      ? `${inr(cap.runs_cut_short)} ${plural(cap.runs_cut_short, "run", "runs")} cut short — the hours and the material were there`
                      : undefined
                  }
                />
              )}
              {cap.products_stopped_outright != null && (
                <Stat
                  k="Products it stopped outright"
                  v={inr(cap.products_stopped_outright)}
                  tone="text-red-300"
                  sub="tried, and there was no room for a single bottle"
                />
              )}
            </div>

            <p className="mt-3 text-xs text-zinc-400">{maskDigits(cap.why_it_is_a_build_choice)}</p>

            {never.length > 0 && (
              <div className="mt-4 border-t border-zinc-800 pt-3">
                <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">
                  Biggest of the products that never get made
                </div>
                <ul className="max-h-56 space-y-1 overflow-y-auto pr-2 text-xs">
                  {never.map((n) => (
                    <li key={n.code} className="flex flex-wrap items-baseline gap-2">
                      <span className="font-mono text-[11px] text-zinc-500">{n.code}</span>
                      <span className="text-zinc-300">{n.sku}</span>
                      <span className="ml-auto tabular-nums text-zinc-500">
                        {litres(n.month_target_litres)} on the month&rsquo;s target
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {(cap.days_it_bit_dates?.length ?? 0) > 0 && (
              <p className="mt-3 text-xs text-zinc-500">
                Days it bit:{" "}
                {cap.days_it_bit_dates!.map((d) => dlabel(d)).join(" · ")}.{" "}
                <Link href="/storage" className="underline underline-offset-2 hover:text-zinc-300">
                  the godown, day by day
                </Link>
                .
              </p>
            )}
          </>
        )}
      </Live>
    </Panel>
  );
}
