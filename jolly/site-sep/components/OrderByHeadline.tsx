// The headline case: the late component with the biggest shortfall (selected
// from data, not named in code). At the 31-Aug freeze this is the refined
// olive tank — day-1 short, a sliver of cover, nothing on order.

import type { MaterialRow } from "../lib/types";
import { obFmt, obDate, obUnit, obDaysBetween, obCoverLabel } from "./OrderByFmt";

export default function OrderByHeadline({
  worst,
  otherLateOils,
  freeze,
}: {
  worst: MaterialRow;
  otherLateOils: MaterialRow[];
  freeze: string;
}) {
  const past = worst.order_by ? obDaysBetween(worst.order_by, freeze) : 0;
  const skus = worst.skus.split(";").filter(Boolean);
  return (
    <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-xl">
          <div className="text-xs uppercase tracking-wider text-red-300/80">
            The biggest late order on the board
          </div>
          <div className="text-3xl font-semibold mt-1 text-zinc-50">{worst.name}</div>
          <div className="text-sm text-zinc-400 mt-1 font-mono">
            {worst.code} · {worst.kind === "OIL" ? "loose oil" : "packaging"} · lead {worst.lead_days} days
          </div>
          <div className="text-sm text-zinc-300 mt-3">
            The plan needs <span className="text-zinc-100">{obFmt(worst.need)} {obUnit(worst.uom)}</span> of it.
            On hand: <span className="text-zinc-100">{obFmt(worst.on_hand)} {obUnit(worst.uom)}</span> —{" "}
            <span className="text-red-300">{obCoverLabel(worst.cover_pct)} cover</span> — and{" "}
            <span className={worst.on_order === 0 ? "text-red-300" : "text-zinc-100"}>
              {worst.on_order === 0 ? "zero on order" : `${obFmt(worst.on_order)} ${obUnit(worst.uom)} on order`}
            </span>
            . The first scheduled run outruns supply on{" "}
            <span className="text-zinc-100">{obDate(worst.first_short_day)}</span>; with a {worst.lead_days}-day lead
            the last safe order date was <span className="text-red-300">{obDate(worst.order_by)}</span> —{" "}
            {past > 0 ? `already ${past} days past` : "reached"} at the {obDate(freeze)} freeze. Every day without a
            PO slips a run.
          </div>
          {skus.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {skus.map((s) => (
                <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-300">
                  {s.trim()}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex gap-6">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Short</div>
            <div className="text-4xl font-semibold text-red-400 tabular-nums">{obFmt(worst.short)}</div>
            <div className="text-xs text-zinc-500">{obUnit(worst.uom)}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Cover</div>
            <div className="text-4xl font-semibold text-zinc-100 tabular-nums">{obCoverLabel(worst.cover_pct)}</div>
            <div className="text-xs text-zinc-500">on hand + on order</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Days past order-by</div>
            <div className="text-4xl font-semibold text-zinc-100 tabular-nums">{past}</div>
            <div className="text-xs text-zinc-500">at the freeze</div>
          </div>
        </div>
      </div>
      {otherLateOils.length > 0 && (
        <div className="mt-4 pt-3 border-t border-red-900/40 text-sm text-zinc-400">
          <span className="text-zinc-300">{otherLateOils.length} more loose oils are late too:</span>{" "}
          {otherLateOils.map((r, i) => (
            <span key={r.code}>
              {i > 0 && " · "}
              <span className="text-zinc-200">{r.name}</span>{" "}
              <span className="text-zinc-500">
                ({obFmt(r.need)} L needed, {obCoverLabel(r.cover_pct)} cover, order-by {obDate(r.order_by)})
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
