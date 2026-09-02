import Link from "next/link";
import { getMaterials, getOverview, getAllDays, getHonesty, fmt, money, tonnes, dlabel, countWord } from "../../lib/data";
import { Card, Section, Pill } from "../../components/Card";
import SimBadge from "../../components/SimBadge";

export const metadata = {
  title: "Materials",
  description:
    "Oil and packaging position for the September plan — opening stock, consumption vs supply, zeros and the unproducible SKUs.",
};

export default function MaterialsPage() {
  const M = getMaterials();
  const O = getOverview();
  const H = getHonesty();
  const days = getAllDays();
  const z = M.zero_definitions;

  // ---- component split (the 209-row cover table itself lives on /order-by) ----
  const oilRows = M.rows.filter((r) => r.kind === "OIL").sort((a, b) => b.need - a.need);
  const packRows = M.rows.filter((r) => r.kind === "PACK");
  const packUnder = packRows.filter((r) => r.cover_pct < 100).length;
  const packLate = packRows.filter((r) => r.late).length;

  // ---- in-month oil flows, code by code, from the simulated day files ---------
  const recv = new Map<string, number>();
  const used = new Map<string, number>();
  const names = new Map<string, string>();
  days.forEach((d) => {
    d.received.forEach((r) => {
      if (r.code.startsWith("RM")) {
        recv.set(r.code, (recv.get(r.code) ?? 0) + r.qty);
        if (!names.has(r.code)) names.set(r.code, r.name);
      }
    });
    d.runs.forEach((run) => { if (run.oil) used.set(run.oil, (used.get(run.oil) ?? 0) + run.litres); });
  });

  const oilCodes = new Set(oilRows.map((r) => r.code));
  const extras = [...new Set([...recv.keys(), ...used.keys()])]
    .filter((c) => !oilCodes.has(c))
    .sort((a, b) => (recv.get(b) ?? 0) - (recv.get(a) ?? 0));
  const blendExtras = extras.filter((c) => (used.get(c) ?? 0) > 0);

  const openingOil13 = oilRows.reduce((a, r) => a + r.on_hand, 0);
  const recvAll = [...recv.values()].reduce((a, b) => a + b, 0);
  const usedRuns = [...used.values()].reduce((a, b) => a + b, 0);
  const oilUsedTotal = O.totals.oil_used_l; // includes flush oil
  const flushDelta = oilUsedTotal - usedRuns;
  const closingOil = openingOil13 + recvAll - oilUsedTotal;

  const unprodLitres = M.unproducible.reduce((a, u) => a + u.plan_litres, 0);
  const unprodValue = M.unproducible.reduce((a, u) => a + (u.value_est_rs ?? 0), 0);
  const unprodPct = (unprodLitres / O.plan.litres) * 100;

  const leadAssumption = H.assumed.find((a) => a.includes("lead time")) ?? "supply arrives exactly on its lead time";

  const closing = (r: { code: string; on_hand: number }) => r.on_hand + (recv.get(r.code) ?? 0) - (used.get(r.code) ?? 0);

  return (
    <div>
      <h1 className="text-2xl font-bold">
        Materials <SimBadge kind="plan" />
      </h1>
      <p className="text-zinc-400 text-sm mt-1 max-w-3xl">
        What the plan starts with, what it eats, and what is left. {M.components_in_plan} components sit under the
        month&apos;s {O.plan.skus}-SKU plan; {M.under_100_cover} of them have less than 100% month cover at the freeze,{" "}
        {M.must_order_week1} must be ordered in week 1 and {M.already_late} are already late — the full cover table with
        order-by dates lives on <Link href="/order-by" className="text-sky-300 underline decoration-sky-800 underline-offset-2">Order-by</Link>.
        Oil synonyms are already {M.synonyms}. Measured lead times: oil {M.lead_days.oil} d, packaging {M.lead_days.packaging} d.
      </p>

      {/* ---------------- opening position ---------------- */}
      <Section title={`Opening position — ${dlabel(O.meta.frozen)} freeze`} right={<SimBadge kind="measured" note={H.provenance.opening ?? "the 31-Aug freeze — the one observed day in this whole plan"} />}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card title="Loose oil on hand" value={`${fmt(O.opening.oil_l)} L`}
            sub="all RM oils — a broader set than the component table below; the two are different definitions" tone="text-emerald-400" />
          <Card title="Packaging on hand" value={`${fmt(O.opening.packaging_pieces)} pcs`}
            sub="one count across mixed units — bottles, caps, labels, cartons all as “pieces”; scale, not cover" tone="text-sky-300" />
          <Card title="Already on order" value={`${fmt(O.opening.inbound_oil_l)} L oil`}
            sub={`plus ${fmt(O.opening.inbound_packaging)} pcs packaging — open POs at the freeze`} />
          <Card title="Components at zero on the shelf" value={`${M.opening_at_zero.length}`}
            sub={`on day 1 — ${z.opening_zero_reconciliation.literal_items} with nothing on order + ${z.opening_zero_reconciliation.chase_items} a live PO already covers`} tone="text-red-400" />
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          The oil figure above counts <em>every</em> RM oil in stock; the family table below counts only the{" "}
          {oilRows.length} oils the plan&apos;s BOMs actually pull. Different definitions — never chart or reconcile them as
          one series.
        </p>
        {M.opening_at_zero.length > 0 && (
          <div className="mt-3 rounded-xl border border-red-900/50 bg-red-950/15 p-3">
            <div className="text-[11px] uppercase tracking-wider text-red-300/80 mb-2">At zero on the shelf, day 1 <SimBadge kind="measured" /></div>
            <div className="flex flex-wrap gap-1.5">
              {M.opening_at_zero.map((it) => (
                <span key={it.code} className="text-xs px-2 py-0.5 rounded-full bg-zinc-900 border border-red-900/40 text-zinc-300">
                  {it.name} <span className="text-zinc-600 font-mono">{it.code}</span> <span className="text-zinc-500">· {it.kind.toLowerCase()}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* ---------------- oil, family by family ---------------- */}
      <Section title="Oil, family by family — consumption vs supply"
        right={<span className="text-xs text-zinc-500">{oilRows.length} base oils the plan&apos;s BOMs pull · synonyms merged upstream</span>}>
        <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
          <span><Pill tone="green">measured</Pill> <span className="ml-1">opening, on PO at freeze; need is derived from the frozen plan × BOMs</span></span>
          <span><Pill tone="violet">simulated</Pill> <span className="ml-1">landed, used, closing — the sim&apos;s month, with &ldquo;{leadAssumption}&rdquo; assumed</span></span>
        </div>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400 text-left">
              <tr>
                <th className="px-3 py-2 font-medium">Oil family</th>
                <th className="px-3 py-2 font-medium text-right">Opening</th>
                <th className="px-3 py-2 font-medium text-right">Month need</th>
                <th className="px-3 py-2 font-medium text-right">On PO at freeze</th>
                <th className="px-3 py-2 font-medium w-40">Supply vs need</th>
                <th className="px-3 py-2 font-medium text-right">Landed (sim)</th>
                <th className="px-3 py-2 font-medium text-right">Used (sim)</th>
                <th className="px-3 py-2 font-medium text-right">Closing (sim)</th>
              </tr>
            </thead>
            <tbody>
              {oilRows.map((r) => {
                const landed = recv.get(r.code) ?? 0;
                const usedL = used.get(r.code) ?? 0;
                const wOpen = Math.min(100, (r.on_hand / r.need) * 100);
                const wLand = Math.min(100 - wOpen, (landed / r.need) * 100);
                const covered = r.on_hand + landed >= r.need;
                return (
                  <tr key={r.code} className="border-t border-zinc-900">
                    <td className="px-3 py-1.5">
                      <div className="text-zinc-100">{r.name}</div>
                      <div className="text-xs text-zinc-600 font-mono">
                        {r.code}
                        {r.late && <span className="ml-2 font-sans text-red-400">already late to order</span>}
                        {r.zero_august_rule && !r.late && <span className="ml-2 font-sans text-amber-400">cover &lt; 1% at freeze</span>}
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{fmt(r.on_hand)} L</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{fmt(r.need)} L</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-400">{r.on_order ? `${fmt(r.on_order)} L` : <span className="text-zinc-700">—</span>}</td>
                    <td className="px-3 py-1.5">
                      <div className="flex items-center gap-2">
                        <div className="h-2 grow rounded-full bg-zinc-800 overflow-hidden flex" title="green = opening stock, blue = lands in-month (sim), track = month need">
                          <div className="bg-emerald-500/70" style={{ width: `${wOpen}%` }} />
                          <div className="bg-sky-500/70" style={{ width: `${wLand}%` }} />
                        </div>
                        <span className={`text-xs tabular-nums w-9 text-right ${covered ? "text-emerald-300" : "text-red-400"}`}>
                          {Math.round(Math.min(999, ((r.on_hand + landed) / r.need) * 100))}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-sky-300">{landed ? `${fmt(landed)} L` : <span className="text-zinc-700">—</span>}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{usedL ? `${fmt(usedL)} L` : <span className="text-zinc-700">—</span>}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-emerald-300">{fmt(closing(r))} L</td>
                  </tr>
                );
              })}
              {extras.length > 0 && (
                <tr className="border-t border-zinc-800 bg-zinc-900/40">
                  <td colSpan={8} className="px-3 py-1.5 text-xs text-zinc-500">
                    Bought under their own code in-month, outside the component table above — blends run as themselves,
                    plus landings no plan BOM consumes:
                  </td>
                </tr>
              )}
              {extras.map((c) => {
                const landed = recv.get(c) ?? 0;
                const usedL = used.get(c) ?? 0;
                return (
                  <tr key={c} className="border-t border-zinc-900 bg-zinc-900/40">
                    <td className="px-3 py-1.5">
                      <div className="text-zinc-300">{names.get(c) ?? c}</div>
                      <div className="text-xs text-zinc-600 font-mono">
                        {c}
                        <span className="ml-2 font-sans text-violet-300">{usedL > 0 ? "blend — run on the lines as itself" : "lands in-month; no plan BOM consumes it"}</span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-600" title="Opening blend stock is invisible to the engine — see the blend note below">—</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-600">—</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-600">—</td>
                    <td className="px-3 py-1.5"></td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-sky-300">{landed ? `${fmt(landed)} L` : <span className="text-zinc-700">—</span>}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{usedL ? `${fmt(usedL)} L` : <span className="text-zinc-700">—</span>}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-emerald-300">{fmt(landed - usedL)} L</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          &ldquo;Landed&rdquo; includes the freeze&apos;s open POs arriving <em>and</em> the orders the sim raises during the month —
          it is not additive with the &ldquo;On PO&rdquo; column. Every landing assumes &ldquo;{leadAssumption}&rdquo;{" "}
          <SimBadge kind="assumed" />. &ldquo;Used&rdquo; is oil consumed by scheduled runs; the month&apos;s total oil draw of{" "}
          {fmt(oilUsedTotal)} L also includes {fmt(flushDelta)} L of flush oil not attributed to a single family.
          Needs are per base oil — {M.synonyms}.
        </p>
      </Section>

      {/* ---------------- blend note ---------------- */}
      <Section title="The blend simplification — declared, not hidden">
        <div className="rounded-xl border border-violet-800/40 bg-violet-950/15 p-5">
          <div className="text-xs uppercase tracking-wider text-violet-300/80 mb-1">Engine simplification <SimBadge kind="assumed" /></div>
          <p className="text-sm text-zinc-300 max-w-3xl leading-relaxed">
            Some SKUs fill a <em>blended</em> oil. The engine plans blends by their recipes: their demand is decomposed
            into the base oils in the table above, and when the sim needs blend oil mid-month it buys and runs it under
            the blend&apos;s own code ({blendExtras.map((c) => names.get(c) ?? c).join(", ") || "see table"}). What it cannot
            see is <span className="text-zinc-100">blend stock already standing at the freeze</span> — ready blend on the
            floor on day 1 is invisible to production, so the plan orders base oil it may not strictly need and the
            closing figure below understates real oil by whatever ready blend existed on 31 Aug. That is a simplification
            of the engine, not a fact about the godown.
          </p>
        </div>
      </Section>

      {/* ---------------- unproducible ---------------- */}
      <Section title={`The ${countWord(M.unproducible.length)} plan SKUs no line can make`}
        right={<span className="text-xs text-zinc-500">also flagged on <Link href="/order-by" className="underline decoration-zinc-700 underline-offset-2">Order-by</Link></span>}>
        <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5">
          <p className="text-sm text-zinc-300 max-w-3xl">
            The plan asks for {M.unproducible.length} SKUs that <span className="text-zinc-100">no configured line can
            fill</span> — {M.unproducible_note}. Together they are {fmt(unprodLitres)} L ({unprodPct.toFixed(1)}% of the{" "}
            {fmt(O.plan.litres)} L plan) that will not run as configured, whatever the materials position. Either a line
            gets a {[...new Set(M.unproducible.map((u) => u.slot_needed))].join(" and a ")} slot, or these litres come out
            of the plan.
          </p>
          <div className="rounded-lg border border-red-900/40 overflow-x-auto mt-4">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/70 text-zinc-400 text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">SKU</th>
                  <th className="px-3 py-2 font-medium">Missing slot</th>
                  <th className="px-3 py-2 font-medium text-right">Plan pieces</th>
                  <th className="px-3 py-2 font-medium text-right">Plan litres</th>
                  <th className="px-3 py-2 font-medium text-right">Value est.</th>
                </tr>
              </thead>
              <tbody>
                {M.unproducible.map((u) => (
                  <tr key={u.code} className="border-t border-zinc-900">
                    <td className="px-3 py-1.5">
                      <div className="text-zinc-100">{u.sku}</div>
                      <div className="text-xs text-zinc-600 font-mono">{u.code} · {u.pack_type} · {fmt(u.litres_per_piece)} L/pc</div>
                    </td>
                    <td className="px-3 py-1.5"><span className="text-red-400">{u.slot_needed}</span> <span className="text-zinc-500 text-xs">— {u.reason}</span></td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{fmt(u.plan_pieces)}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{fmt(u.plan_litres)} L</td>
                    <td className="px-3 py-1.5 text-right tabular-nums">
                      {u.value_est_rs != null ? money(u.value_est_rs) : "—"}{" "}
                      {u.value_est_derived && <SimBadge kind="derived" note="estimated from realise × litres, not an order-book value" />}
                    </td>
                  </tr>
                ))}
                <tr className="border-t border-zinc-800 bg-zinc-900/50">
                  <td className="px-3 py-1.5 text-zinc-400" colSpan={2}>All {M.unproducible.length} together</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-300">{fmt(M.unproducible.reduce((a, u) => a + u.plan_pieces, 0))}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{fmt(unprodLitres)} L</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-300">{money(unprodValue)} <SimBadge kind="derived" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Section>

      {/* ---------------- closing oil ---------------- */}
      <Section title="Closing oil — what carries into October">
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/15 p-5">
            <div className="text-xs uppercase tracking-wider text-emerald-300/80">Loose oil at close of {dlabel(O.meta.horizon[1])} <SimBadge kind="simulated" /></div>
            <div className="text-3xl font-semibold mt-1 text-emerald-300">{fmt(closingOil)} L</div>
            <div className="text-sm text-zinc-400 mt-1">≈ {tonnes(closingOil)} of oil, on the component (BOM-relevant) definition</div>
            <div className="mt-3 pt-3 border-t border-emerald-900/40 text-xs text-zinc-400 space-y-1 tabular-nums">
              <div className="flex justify-between"><span>Component opening</span><span>{fmt(openingOil13)} L</span></div>
              <div className="flex justify-between"><span>+ lands in-month (sim)</span><span>{fmt(recvAll)} L</span></div>
              <div className="flex justify-between"><span>− oil used, incl. flush (sim)</span><span>{fmt(oilUsedTotal)} L</span></div>
              <div className="flex justify-between text-emerald-300 border-t border-emerald-900/40 pt-1"><span>= closing</span><span>{fmt(closingOil)} L</span></div>
            </div>
          </div>
          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 text-sm text-zinc-400 space-y-2.5">
            <div className="text-xs uppercase tracking-wider text-zinc-500">Read this number with its caveats</div>
            <div><Pill tone="violet">simulated</Pill> <span className="ml-1">It exists only if September runs exactly as planned — every landing assumes &ldquo;{leadAssumption}&rdquo;. A late tanker moves it down; an unrun day moves it up.</span></div>
            <div><Pill tone="amber">definition</Pill> <span className="ml-1">This is the {oilRows.length}-component BOM-relevant set. The freeze&apos;s all-RM count ({fmt(O.opening.oil_l)} L at open) is a different, broader definition — never reconcile the two directly.</span></div>
            <div><Pill tone="amber">blends</Pill> <span className="ml-1">Ready blend standing at the freeze is invisible to the engine (note above), so real closing oil would be slightly higher than shown.</span></div>
            <div><Pill tone="zinc">carry</Pill> <span className="ml-1">Treat it as October&apos;s <em>planned</em> opening position, not a forecast of the SAP book — the biggest single carry is{" "}
              {(() => { const top = [...oilRows].sort((a, b) => closing(b) - closing(a))[0]; return <span className="text-zinc-200">{top.name.toLowerCase()} at {fmt(closing(top))} L</span>; })()}.</span></div>
          </div>
        </div>
      </Section>

      {/* ---------------- packaging + the two zero definitions ---------------- */}
      <Section title="Packaging — and the two “zero” definitions, labeled"
        right={<span className="text-xs text-zinc-500">full item-level table on <Link href="/order-by" className="underline decoration-zinc-700 underline-offset-2">Order-by</Link></span>}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card title="Packaging components" value={`${packRows.length}`} sub={`of ${M.components_in_plan} components under the plan`} />
          <Card title="Under 100% month cover" value={`${packUnder}`} sub={`packaging items; ${packLate} already late to order`} tone="text-amber-300" />
          <Card title="Literal zeros" value={`${z.literal.items}`} sub={`${z.literal.definition} — blocking ${money(z.literal.blocked_value_rs)} across ${z.literal.skus_blocked} SKUs`} tone="text-red-400" />
          <Card title="August-rule zeros" value={`${z.august_rule.items}`} sub={`${z.august_rule.definition} — blocking ${money(z.august_rule.blocked_value_rs)} across ${z.august_rule.skus_blocked} SKUs`} tone="text-red-400" />
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Two different definitions, both real, both in the order-by data — {z.note}. The literal-zero count here is{" "}
          {z.literal.zero_pack ?? 0} packaging and {z.literal.zero_oil ?? 0} oil items{z.literal.blocked_value_note ? <> ({z.literal.blocked_value_note})</> : null}.
          It is smaller than the {z.opening_zero_reconciliation.opening_items}-item zero-shelf card above by design:{" "}
          {z.opening_zero_reconciliation.note}. Packaging &ldquo;pieces&rdquo; remain mixed units throughout — a cap and
          a carton each count as one.
        </p>
      </Section>
    </div>
  );
}
