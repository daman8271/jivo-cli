// The biggest late order: the late material with the biggest shortfall
// (selected from data, not named in code). At the 31-Aug stock count this is
// the refined olive tank — short from day 1, a sliver in stock, nothing on order.

import type { MaterialRow } from "../lib/types";
import {
  obFmt, obDate, obUnit, obUnitWord, obLakh, obDaysBetween, obEnoughLabel, obCoverLabel, obMaterial, obDays,
} from "./OrderByFmt";

export default function OrderByHeadline({
  worst,
  otherLateOils,
  freeze,
  today,
}: {
  worst: MaterialRow;
  otherLateOils: MaterialRow[];
  freeze: string; // the day the stock was counted (31 Aug)
  today: string; // day 1 — LATE means the last date to order is today or has passed
}) {
  const past = worst.order_by ? obDaysBetween(worst.order_by, today) : 0;
  const products = worst.skus.split(";").filter(Boolean);
  const unitWord = obUnitWord(worst.uom);
  return (
    <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-xl">
          <div className="text-xs uppercase tracking-wider text-red-300/80">The biggest late order</div>
          <div className="text-3xl font-semibold mt-1 text-zinc-50">{worst.name}</div>
          <div className="text-sm text-zinc-400 mt-1">
            <span className="font-mono">{worst.code}</span> · {obMaterial(worst.name, worst.kind)} · takes{" "}
            {obDays(worst.lead_days)} to arrive
          </div>
          <div className="text-sm text-zinc-300 mt-3">
            This month needs <span className="text-zinc-100">{obLakh(worst.need, unitWord)}</span>. In stock (counted{" "}
            {obDate(freeze)}): <span className="text-zinc-100">{obLakh(worst.on_hand, unitWord)}</span> —{" "}
            <span className="text-red-300">enough for {obCoverLabel(worst.cover_pct)} of the month</span>. On order:{" "}
            <span className={worst.on_order === 0 ? "text-red-300" : "text-zinc-100"}>
              {worst.on_order === 0 ? "nothing" : obLakh(worst.on_order, unitWord)}
            </span>
            .{" "}
            {worst.first_short_day && (
              <>
                The first run that needs it is on <span className="text-zinc-100">{obDate(worst.first_short_day)}</span>.
              </>
            )}{" "}
            It takes {obDays(worst.lead_days)} to arrive, so the last date to order was{" "}
            <span className="text-red-300">{obDate(worst.order_by)}</span>
            {past > 0 ? ` — already ${obDays(past)} ago on ${obDate(today)}` : ` — that is today, ${obDate(today)}`}.
            Every day without a PO, another run slips.
          </div>
          {products.length > 0 && (
            <div className="mt-3">
              <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1">Products waiting on it</div>
              <div className="flex flex-wrap gap-1.5">
                {products.map((s) => (
                  <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-300">
                    {s.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-6">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Short by</div>
            <div className="text-4xl font-semibold text-red-400 tabular-nums">{obFmt(worst.short)}</div>
            <div className="text-xs text-zinc-500">{obUnit(worst.uom)}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Enough for</div>
            <div className="text-4xl font-semibold text-zinc-100 tabular-nums">{obEnoughLabel(worst.cover_pct)}</div>
            <div className="text-xs text-zinc-500">in stock + coming</div>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Days late</div>
            <div className="text-4xl font-semibold text-zinc-100 tabular-nums">{Math.max(0, past)}</div>
            <div className="text-xs text-zinc-500">
              {past > 0 ? `on ${obDate(today)}` : `last date is today, ${obDate(today)}`}
            </div>
          </div>
        </div>
      </div>
      {otherLateOils.length > 0 && (
        <div className="mt-4 pt-3 border-t border-red-900/40 text-sm text-zinc-400">
          <span className="text-zinc-300">
            {obFmt(otherLateOils.length)} more {otherLateOils.length === 1 ? "oil is" : "oils are"} late too:
          </span>{" "}
          {otherLateOils.map((r, i) => (
            <span key={r.code}>
              {i > 0 && " · "}
              <span className="text-zinc-200">{r.name}</span>{" "}
              <span className="text-zinc-500">
                (needs {obLakh(r.need, obUnitWord(r.uom))}, has {obCoverLabel(r.cover_pct)} of that in stock + coming,
                last date to order {obDate(r.order_by)})
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
