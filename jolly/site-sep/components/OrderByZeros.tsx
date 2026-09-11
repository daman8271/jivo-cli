// Two "nothing in stock" lists, two labelled blocks — NEVER blended. Both live
// in the verified order-by artifact; each block names its own rule and its own
// block-level value. Server component: everything arrives from data/materials.json.
// The August rule's threshold is read out of the artifact's own definition
// string at render time — never typed here.

import type { MaterialRow, MaterialsData } from "../lib/types";
import { obFmt, obMoney, obDate, obUnit, obEnoughLabel, obPctFromText } from "./OrderByFmt";

type Props = {
  z: MaterialsData["zero_definitions"];
  litRows: MaterialRow[]; // zero_literal
  augRows: MaterialRow[]; // zero_august_rule
  litInsideAug: boolean; // computed: every "nothing in stock" item also passes the August rule
};

export default function OrderByZeros({ z, litRows, augRows, litInsideAug }: Props) {
  const chaseN = z.opening_zero_reconciliation.chase_items;
  const augPct = obPctFromText(z.august_rule.definition);
  return (
    <div>
      <div className="grid md:grid-cols-2 gap-4">
        {/* ---- list 1: nothing in stock, nothing coming ---- */}
        <div className="rounded-xl border border-red-900/50 bg-red-950/15 p-4">
          <div className="text-xs uppercase tracking-wider text-red-300/80">List 1 — nothing in stock</div>
          <div className="text-sm text-zinc-400 mt-0.5">
            Nothing in stock, and nothing on order.{" "}
            {chaseN > 0 && (
              <>
                (The {chaseN === 1 ? "one item" : `${obFmt(chaseN)} items`} with nothing in stock but a PO coming{" "}
                {chaseN === 1 ? "is" : "are"} under &ldquo;PO coming — chase it&rdquo; above.)
              </>
            )}
          </div>
          <div className="flex items-baseline gap-3 mt-3">
            <div className="text-3xl font-semibold text-red-400">{obFmt(z.literal.items)} items</div>
            <div className="text-sm text-zinc-300">
              holding up <span className="text-zinc-100">{obMoney(z.literal.blocked_value_rs)}</span> of production ·{" "}
              {obFmt(z.literal.skus_blocked)} products
            </div>
          </div>
          <table className="w-full text-sm mt-3">
            <thead className="text-zinc-500 text-left text-xs">
              <tr>
                <th className="py-1 font-medium">Item</th>
                <th className="py-1 font-medium text-right">Need</th>
                <th className="py-1 font-medium text-right">Litres held up</th>
                <th className="py-1 font-medium text-right">Value held up</th>
                <th className="py-1 font-medium text-right">Last date to order</th>
              </tr>
            </thead>
            <tbody>
              {litRows.map((r) => (
                <tr key={r.code} className="border-t border-red-900/30">
                  <td className="py-1.5 pr-2">
                    <div className="text-zinc-200 text-[13px] leading-tight">{r.name}</div>
                    <div className="text-[11px] text-zinc-600 font-mono">{r.code}</div>
                  </td>
                  <td className="py-1.5 text-right tabular-nums text-zinc-300 whitespace-nowrap">
                    {obFmt(r.need)} <span className="text-zinc-600">{obUnit(r.uom)}</span>
                  </td>
                  <td className="py-1.5 text-right tabular-nums text-zinc-300">{obFmt(r.litres_at_risk)} L</td>
                  <td className="py-1.5 text-right tabular-nums text-red-300">{obMoney(r.value_at_risk)}</td>
                  <td className="py-1.5 text-right whitespace-nowrap">
                    <span className={r.late ? "text-red-300" : "text-zinc-300"}>{obDate(r.order_by)}</span>
                    {r.late && <span className="text-[10px] text-red-400/80 ml-1">LATE</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {z.literal.blocked_value_note && (
            <p className="text-[11px] text-zinc-600 mt-2">
              One product can wait on two or three missing items. The total counts each product once, so the item
              values add up to more than the total.
            </p>
          )}
        </div>

        {/* ---- list 2: almost nothing in stock — the August rule ---- */}
        <div className="rounded-xl border border-amber-900/50 bg-amber-950/10 p-4">
          <div className="text-xs uppercase tracking-wider text-amber-300/80">
            List 2 — almost nothing in stock (the August rule)
          </div>
          <div className="text-sm text-zinc-400 mt-0.5">
            {augPct
              ? `Stock plus what is on order is under ${augPct}% of the month's need.`
              : "Stock plus what is on order is a tiny part of the month's need."}{" "}
            A few pieces may be lying around, but not enough to run. Same rule we used in August.
          </div>
          <div className="flex items-baseline gap-3 mt-3">
            <div className="text-3xl font-semibold text-amber-300">{obFmt(z.august_rule.items)} items</div>
            <div className="text-sm text-zinc-300">
              holding up <span className="text-zinc-100">{obMoney(z.august_rule.blocked_value_rs)}</span> of production
              · {obFmt(z.august_rule.skus_blocked)} products
            </div>
          </div>
          <table className="w-full text-sm mt-3">
            <thead className="text-zinc-500 text-left text-xs">
              <tr>
                <th className="py-1 font-medium">Item</th>
                <th className="py-1 font-medium text-right">In stock</th>
                <th className="py-1 font-medium text-right">Need</th>
                <th className="py-1 font-medium text-right">Enough for</th>
                <th className="py-1 font-medium text-right">Last date to order</th>
              </tr>
            </thead>
            <tbody>
              {augRows.map((r) => (
                <tr key={r.code} className="border-t border-amber-900/25">
                  <td className="py-1.5 pr-2">
                    <div className="text-zinc-200 text-[13px] leading-tight">{r.name}</div>
                    <div className="text-[11px] text-zinc-600 font-mono">{r.code}</div>
                  </td>
                  <td className={`py-1.5 text-right tabular-nums ${r.on_hand === 0 ? "text-red-400" : "text-amber-200"}`}>
                    {r.on_hand === 0 ? "nothing" : obFmt(r.on_hand)}
                  </td>
                  <td className="py-1.5 text-right tabular-nums text-zinc-300 whitespace-nowrap">
                    {obFmt(r.need)} <span className="text-zinc-600">{obUnit(r.uom)}</span>
                  </td>
                  <td className="py-1.5 text-right tabular-nums text-amber-300 whitespace-nowrap">
                    {obEnoughLabel(r.cover_pct)}
                  </td>
                  <td className="py-1.5 text-right whitespace-nowrap">
                    <span className={r.late ? "text-red-300" : "text-zinc-300"}>{obDate(r.order_by)}</span>
                    {r.late && <span className="text-[10px] text-red-400/80 ml-1">LATE</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-[11px] text-zinc-600 mt-2">
            The value is worked out for the {obFmt(z.august_rule.skus_blocked)} products together, not item by item.
            So no per-item value is shown here.
          </p>
        </div>
      </div>
      <p className="text-xs text-zinc-500 mt-2">
        Two lists, two rules. They are never added together.
        {litInsideAug && (
          <>
            {" "}
            All {obFmt(litRows.length)} items in list 1 are also in list 2 — so list 2 includes list 1.
          </>
        )}
      </p>
    </div>
  );
}
