import type { Overview } from "../lib/types";
import { fmt, cr } from "../lib/data";
import SimBadge from "./SimBadge";

// The demand-mix bar. Labeling rule 3: the demand stream MIXES real orders and
// forecast rows — this component exists to say that plainly, split by channel.
export default function OverviewDemand({
  demand,
  ecomRule,
}: {
  demand: Overview["demand"];
  ecomRule?: string;
}) {
  const fShareL = demand.forecast_share_litres_pct;
  const rShareL = +(100 - fShareL).toFixed(2);
  const realChannels = Object.entries(demand.channels)
    .filter(([k]) => k !== "FORECAST")
    .map(([k, v]) => `${k} ${fmt(v)}`)
    .join(" · ");
  const roughly = Math.round(fShareL);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      <p className="text-sm text-zinc-300 leading-relaxed">
        Said plainly: <span className="text-zinc-100 font-medium">roughly {roughly}% of the demand this plan serves is
        forecast, not orders.</span> Of {fmt(demand.rows)} demand rows across {fmt(demand.order_dates)} order dates,{" "}
        {fmt(demand.real_rows)} are real orders on the books and {fmt(demand.forecast_rows)} are the monthly plan
        written as dated buckets — {fShareL}% of the stream by litres. Nobody has placed the forecast rows.
      </p>

      {/* the split, by litres */}
      <div className="mt-4">
        <div className="h-5 rounded-full overflow-hidden flex border border-zinc-800">
          <div
            className="bg-emerald-500/70 h-full"
            style={{ width: `${rShareL}%` }}
            title={`real orders — ${rShareL}% of the stream by litres`}
          />
          <div
            className="bg-sky-500/50 h-full border-l border-zinc-950"
            style={{ width: `${fShareL}%` }}
            title={`forecast — ${fShareL}% of the stream by litres`}
          />
        </div>
        <div className="flex flex-wrap justify-between gap-x-6 gap-y-2 mt-2 text-xs">
          <div className="text-zinc-400">
            <span className="inline-block w-2.5 h-2.5 rounded-[2px] bg-emerald-500/70 mr-1.5 align-middle" />
            <span className="text-emerald-300 font-medium">Real orders — {rShareL}% by litres.</span>{" "}
            {fmt(demand.real_rows)} rows ({realChannels}) · {fmt(demand.real_pieces)} pcs ·{" "}
            {cr(demand.real_value_rs)}
          </div>
          <div className="text-zinc-400 text-right">
            <span className="inline-block w-2.5 h-2.5 rounded-[2px] bg-sky-500/50 mr-1.5 align-middle" />
            <span className="text-sky-300 font-medium">
              Forecast — {fShareL}% by litres <SimBadge kind="forecast" />
            </span>{" "}
            {fmt(demand.forecast_rows)} rows · {fmt(demand.forecast_pieces)} pcs · {cr(demand.forecast_value_rs)}
          </div>
        </div>
        <div className="text-[11px] text-zinc-500 mt-2 tabular-nums">
          The forecast share moves with the unit: {demand.forecast_share_litres_pct}% by litres ·{" "}
          {demand.forecast_share_pieces_pct}% by pieces · {demand.forecast_share_value_pct}% by value.
        </div>
      </div>

      <div className="mt-4 space-y-1.5 text-[11px] text-zinc-500 border-t border-zinc-800 pt-3">
        <div>
          <span className="text-sky-300/80 font-medium">Kept separable by design:</span> {demand.note}.
        </div>
        {ecomRule && (
          <div>
            <SimBadge kind="assumed" /> <span className="align-middle">{ecomRule}</span>
          </div>
        )}
      </div>
    </div>
  );
}
