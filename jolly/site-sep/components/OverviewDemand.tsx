import type { Overview } from "../lib/types";
import { fmt, cr, plainChannel } from "../lib/data";
import SimBadge from "./SimBadge";

// Confirmed orders vs expected orders. The month's order book MIXES the two —
// this component exists to say that plainly and keep them apart. Raw channel
// names from the data are said with lib's plainChannel (a real channel keeps
// its own name — nothing is read into "MART" that the data does not say).

export default function OverviewDemand({
  demand,
  ecomRule,
}: {
  demand: Overview["demand"];
  // present when the honesty file carries the e-com rule — the page shows its
  // own plain words for it, never the rule text
  ecomRule?: string;
}) {
  const fShareL = demand.forecast_share_litres_pct;
  const rShareL = +(100 - fShareL).toFixed(2);
  const realChannels = Object.entries(demand.channels)
    .filter(([k]) => k !== "FORECAST")
    .map(([k, v]) => `${plainChannel(k)} ${fmt(v)}`)
    .join(" · ");
  const roughly = Math.round(fShareL);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      <p className="text-sm text-zinc-300 leading-relaxed">
        <span className="text-zinc-100 font-medium">
          Roughly {roughly}% of what customers want this month is expected — not ordered yet.
        </span>{" "}
        {fmt(demand.real_rows)} entries are confirmed orders on the books. {fmt(demand.forecast_rows)} entries are the
        monthly plan written as weekly amounts — expected, not ordered. By litres that is {fShareL}% of the month.
        Nobody has placed those orders yet.
      </p>

      {/* the split, by litres */}
      <div className="mt-4">
        <div className="h-5 rounded-full overflow-hidden flex border border-zinc-800">
          <div
            className="bg-emerald-500/70 h-full"
            style={{ width: `${rShareL}%` }}
            title={`confirmed orders — ${rShareL}% of the month by litres`}
          />
          <div
            className="bg-sky-500/50 h-full border-l border-zinc-950"
            style={{ width: `${fShareL}%` }}
            title={`expected, not ordered yet — ${fShareL}% of the month by litres`}
          />
        </div>
        <div className="flex flex-wrap justify-between gap-x-6 gap-y-2 mt-2 text-xs">
          <div className="text-zinc-400">
            <span className="inline-block w-2.5 h-2.5 rounded-[2px] bg-emerald-500/70 mr-1.5 align-middle" />
            <span className="text-emerald-300 font-medium">Confirmed orders — {rShareL}% by litres.</span>{" "}
            {fmt(demand.real_rows)} entries ({realChannels}) · {fmt(demand.real_pieces)} pcs ·{" "}
            {cr(demand.real_value_rs)}
          </div>
          <div className="text-zinc-400 text-right">
            <span className="inline-block w-2.5 h-2.5 rounded-[2px] bg-sky-500/50 mr-1.5 align-middle" />
            <span className="text-sky-300 font-medium">
              Expected — not ordered yet — {fShareL}% by litres <SimBadge kind="forecast" />
            </span>{" "}
            {fmt(demand.forecast_rows)} entries · {fmt(demand.forecast_pieces)} pcs · {cr(demand.forecast_value_rs)}
          </div>
        </div>
        <div className="text-[11px] text-zinc-500 mt-2 tabular-nums">
          The share changes with the unit: {demand.forecast_share_litres_pct}% by litres ·{" "}
          {demand.forecast_share_pieces_pct}% by pieces · {demand.forecast_share_value_pct}% by value.
        </div>
      </div>

      <div className="mt-4 space-y-1.5 text-[11px] text-zinc-500 border-t border-zinc-800 pt-3">
        <div>
          <span className="text-sky-300/80 font-medium">Kept apart on every page:</span> confirmed orders and expected
          orders are never added into one number. Expected is always shown in blue.
        </div>
        {ecomRule && (
          <div>
            <SimBadge kind="assumed" />{" "}
            <span className="align-middle">
              E-com orders are spread evenly over the month. That is our guess — not measured. The monthly plan gives
              e-com no weekly dates.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
