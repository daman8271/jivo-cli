// Two zero definitions, two labelled blocks — NEVER blended. Both live in the
// verified order-by artifact; each block names its own definition and its own
// block-level value. Server component: everything arrives from data/materials.json.

import type { MaterialRow, MaterialsData } from "../lib/types";
import { obFmt, obMoney, obDate, obUnit } from "./OrderByFmt";

type Props = {
  z: MaterialsData["zero_definitions"];
  litRows: MaterialRow[]; // zero_literal
  augRows: MaterialRow[]; // zero_august_rule
  litInsideAug: boolean; // computed: every literal zero also passes the August rule
};

export default function OrderByZeros({ z, litRows, augRows, litInsideAug }: Props) {
  return (
    <div>
      <div className="grid md:grid-cols-2 gap-4">
        {/* ---- definition 1: literally at zero, nothing coming ---- */}
        <div className="rounded-xl border border-red-900/50 bg-red-950/15 p-4">
          <div className="text-xs uppercase tracking-wider text-red-300/80">
            Definition 1 — literally at zero
          </div>
          <div className="text-sm text-zinc-400 mt-0.5">
            {z.literal.definition} (the {z.opening_zero_reconciliation.chase_items} zero-shelf items a live PO already
            covers sit under &ldquo;chase&rdquo; instead)
          </div>
          <div className="flex items-baseline gap-3 mt-3">
            <div className="text-3xl font-semibold text-red-400">{z.literal.items} items</div>
            <div className="text-sm text-zinc-300">
              holding <span className="text-zinc-100">{obMoney(z.literal.blocked_value_rs)}</span> of plan across{" "}
              {z.literal.skus_blocked} SKUs
            </div>
          </div>
          <table className="w-full text-sm mt-3">
            <thead className="text-zinc-500 text-left text-xs">
              <tr>
                <th className="py-1 font-medium">Item</th>
                <th className="py-1 font-medium text-right">Need</th>
                <th className="py-1 font-medium text-right">Litres held</th>
                <th className="py-1 font-medium text-right">Value held</th>
                <th className="py-1 font-medium text-right">Order by</th>
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
              Per-item values overlap where one SKU waits on several zeros — the block total is {z.literal.blocked_value_note}.
            </p>
          )}
        </div>

        {/* ---- definition 2: August's cover<1% rule ---- */}
        <div className="rounded-xl border border-amber-900/50 bg-amber-950/10 p-4">
          <div className="text-xs uppercase tracking-wider text-amber-300/80">
            Definition 2 — August&rsquo;s rule
          </div>
          <div className="text-sm text-zinc-400 mt-0.5">{z.august_rule.definition}</div>
          <div className="flex items-baseline gap-3 mt-3">
            <div className="text-3xl font-semibold text-amber-300">{z.august_rule.items} items</div>
            <div className="text-sm text-zinc-300">
              blocking <span className="text-zinc-100">{obMoney(z.august_rule.blocked_value_rs)}</span> across{" "}
              {z.august_rule.skus_blocked} SKUs
            </div>
          </div>
          <table className="w-full text-sm mt-3">
            <thead className="text-zinc-500 text-left text-xs">
              <tr>
                <th className="py-1 font-medium">Item</th>
                <th className="py-1 font-medium text-right">On hand</th>
                <th className="py-1 font-medium text-right">Need</th>
                <th className="py-1 font-medium text-right">Cover</th>
                <th className="py-1 font-medium text-right">Order by</th>
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
                    {obFmt(r.on_hand)}
                  </td>
                  <td className="py-1.5 text-right tabular-nums text-zinc-300 whitespace-nowrap">
                    {obFmt(r.need)} <span className="text-zinc-600">{obUnit(r.uom)}</span>
                  </td>
                  <td className="py-1.5 text-right tabular-nums text-amber-300">
                    {r.cover_pct % 1 === 0 ? r.cover_pct.toFixed(0) : r.cover_pct.toFixed(1)}%
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
            Block value is computed across the {z.august_rule.skus_blocked} blocked SKUs, not per item — a sliver of
            stock has no per-item &ldquo;value held&rdquo; figure, so none is shown here.
          </p>
        </div>
      </div>
      <p className="text-xs text-zinc-500 mt-2">
        Two different zero definitions live in the artifact — each block above is labelled with its own; they are never
        added together.
        {litInsideAug && (
          <> All {litRows.length} literal zeros also pass the August rule, so definition 2 contains definition 1.</>
        )}
      </p>
    </div>
  );
}
