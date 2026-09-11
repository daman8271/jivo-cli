import Link from "next/link";
import {
  getMaterials, getOverview, getAllDays, fmt, money, tonnes, dlabel,
  litresProse, lakhCrore, plural, packWords, packSizesWords,
} from "../../lib/data";
import { Card, Section, Pill } from "../../components/Card";
import SimBadge from "../../components/SimBadge";

export const metadata = {
  title: "Stock",
  description:
    "Oil and packing material for the September plan — what we had at the start, what the month needs, what is coming, and the products no machine can fill.",
};

// Sentence numbers in Indian style ("8.06 lakh litres", "1.22 crore pieces") and the
// pack words ("3-litre bottles and 200-litre drums") come from lib, so every page
// says them the same way. Exact figures stay in the tables; every value still
// arrives from data/*.json.

export default function MaterialsPage() {
  const M = getMaterials();
  const O = getOverview();
  const days = getAllDays();
  const z = M.zero_definitions;
  const start = dlabel(O.meta.frozen); // the day the stock was counted — the one real day
  const monthEnd = dlabel(O.meta.horizon[1]);

  // ---- oil vs packing split (the full item-by-item table lives on /order-by) ----
  const oilRows = M.rows.filter((r) => r.kind === "OIL").sort((a, b) => b.need - a.need);
  const packRows = M.rows.filter((r) => r.kind === "PACK");
  const packUnder = packRows.filter((r) => r.cover_pct < 100).length;
  const packLate = packRows.filter((r) => r.late).length;

  // ---- oil arriving and used during the month, oil by oil, from the plan's day files ----
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

  // Oil the plan orders in September that only arrives after the month ends.
  const octDates: string[] = [];
  let octL = 0;
  let octLines = 0;
  days.forEach((d) => {
    d.bought.forEach((b) => {
      if (b.code.startsWith("RM") && b.lands > O.meta.horizon[1]) {
        octL += b.qty; octLines += 1; octDates.push(b.lands);
      }
    });
  });
  octDates.sort();

  const oilCodes = new Set(oilRows.map((r) => r.code));
  const extras = [...new Set([...recv.keys(), ...used.keys()])]
    .filter((c) => !oilCodes.has(c))
    .sort((a, b) => (recv.get(b) ?? 0) - (recv.get(a) ?? 0));
  const blendExtras = extras.filter((c) => (used.get(c) ?? 0) > 0);

  const openingOil13 = oilRows.reduce((a, r) => a + r.on_hand, 0);
  const recvAll = [...recv.values()].reduce((a, b) => a + b, 0);
  const usedRuns = [...used.values()].reduce((a, b) => a + b, 0);
  const oilUsedTotal = O.totals.oil_used_l; // includes the oil used to wash machines at oil changes
  const flushDelta = oilUsedTotal - usedRuns;
  const closingOil = openingOil13 + recvAll - oilUsedTotal;

  const unprodLitres = M.unproducible.reduce((a, u) => a + u.plan_litres, 0);
  const unprodValue = M.unproducible.reduce((a, u) => a + (u.value_est_rs ?? 0), 0);
  const unprodPct = (unprodLitres / O.plan.litres) * 100;
  const sizesWords = packSizesWords(M.unproducible);

  const closing = (r: { code: string; on_hand: number }) => r.on_hand + (recv.get(r.code) ?? 0) - (used.get(r.code) ?? 0);
  const topCarry = [...oilRows].sort((a, b) => closing(b) - closing(a))[0];

  return (
    <div>
      <h1 className="text-2xl font-bold">
        Stock <SimBadge kind="plan" note="The computer's plan for September. Nothing here has happened yet." />
      </h1>
      <p className="text-lg text-zinc-100 mt-2 max-w-3xl">
        On {start} evening we had {litresProse(O.opening.oil_l)} of loose oil and {lakhCrore(O.opening.packaging_pieces)} pieces of
        packing material.
      </p>
      <p className="text-sm text-zinc-300 mt-1 max-w-3xl">
        Packing is counted in pieces — a cap, a label and a carton each count as one. So that number shows size, not
        whether it is enough.
      </p>
      <p className="text-sm text-zinc-400 mt-2 max-w-3xl">
        {M.components_in_plan} materials go into this month&apos;s {O.plan.skus} products. {M.under_100_cover} of them will
        not last the month, even counting what is on order. {M.must_order_week1} must be ordered this week.{" "}
        <span className="text-red-300">{M.already_late} are already late — order today.</span> The full list with the last
        date to order each one is on{" "}
        <Link href="/order-by" className="text-sky-300 underline decoration-sky-800 underline-offset-2">Order by when</Link>.
      </p>

      {/* ---------------- stock at the start ---------------- */}
      <Section title={`Stock at the start — counted on ${start} evening`} right={<Pill tone="green">counted — real</Pill>}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card title="Loose oil" value={`${fmt(O.opening.oil_l)} L`}
            sub="every oil in stock — a wider count than the oil table below" tone="text-emerald-400" />
          <Card title="Packing material" value={`${fmt(O.opening.packaging_pieces)} pcs`}
            sub="bottles, caps, labels, cartons — all counted as pieces" tone="text-sky-300" />
          <Card title="Already on order" value={`${fmt(O.opening.inbound_oil_l)} L oil`}
            sub={`plus ${fmt(O.opening.inbound_packaging)} pcs of packing — open POs on ${start}`} />
          <Card title="Nothing in stock" value={`${M.opening_at_zero.length}`}
            sub={`items on day 1 — ${z.opening_zero_reconciliation.literal_items} with nothing on order, ${z.opening_zero_reconciliation.chase_items} already on order (chase it)`} tone="text-red-400" />
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          The oil figure counts <em>every</em> oil in stock. The table below counts only the {oilRows.length} oils that go
          into September&apos;s products. They are two different counts — do not compare them.
        </p>
        {M.opening_at_zero.length > 0 && (
          <div className="mt-3 rounded-xl border border-red-900/50 bg-red-950/15 p-3">
            <div className="text-[11px] uppercase tracking-wider text-red-300/80 mb-2">Nothing in stock on day 1 · counted — real</div>
            <div className="flex flex-wrap gap-1.5">
              {M.opening_at_zero.map((it) => (
                <span key={it.code} className="text-xs px-2 py-0.5 rounded-full bg-zinc-900 border border-red-900/40 text-zinc-300">
                  {it.name} <span className="text-zinc-600 font-mono">{it.code}</span>{" "}
                  <span className="text-zinc-500">· {it.kind === "PACKAGING" ? "packing" : it.kind.toLowerCase()}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* ---------------- oil, family by family ---------------- */}
      <Section title="Oil, family by family — what the month needs, what we have, what is coming"
        right={<span className="text-xs text-zinc-500">{oilRows.length} oils go into September&apos;s products</span>}>
        <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
          <span><Pill tone="green">counted — real</Pill> <span className="ml-1">in stock and on order on {start}</span></span>
          <span><Pill tone="zinc">worked out</Pill> <span className="ml-1">month need = this month&apos;s target × what goes into each bottle</span></span>
          <span><Pill tone="violet">the computer&apos;s plan</Pill> <span className="ml-1">arrives, used, left — has not happened</span></span>
        </div>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400 text-left">
              <tr>
                <th className="px-3 py-2 font-medium">Oil</th>
                <th className="px-3 py-2 font-medium text-right">In stock {start}</th>
                <th className="px-3 py-2 font-medium text-right">Month needs</th>
                <th className="px-3 py-2 font-medium text-right">On order now</th>
                <th className="px-3 py-2 font-medium w-40">Enough?</th>
                <th className="px-3 py-2 font-medium text-right">Arrives in Sept (plan)</th>
                <th className="px-3 py-2 font-medium text-right">Used in Sept (plan)</th>
                <th className="px-3 py-2 font-medium text-right">Left on {monthEnd} (plan)</th>
              </tr>
            </thead>
            <tbody>
              {oilRows.map((r) => {
                const landed = recv.get(r.code) ?? 0;
                const usedL = used.get(r.code) ?? 0;
                const wOpen = Math.min(100, (r.on_hand / r.need) * 100);
                const wLand = Math.min(100 - wOpen, (landed / r.need) * 100);
                const enough = r.on_hand + landed >= r.need;
                return (
                  <tr key={r.code} className="border-t border-zinc-900">
                    <td className="px-3 py-1.5">
                      <div className="text-zinc-100">{r.name}</div>
                      <div className="text-xs text-zinc-600 font-mono">
                        {r.code}
                        {r.late && <span className="ml-2 font-sans text-red-400">already late — order today</span>}
                        {r.zero_august_rule && !r.late && <span className="ml-2 font-sans text-amber-400">almost nothing in stock</span>}
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{fmt(r.on_hand)} L</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{fmt(r.need)} L</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-400">{r.on_order ? `${fmt(r.on_order)} L` : <span className="text-zinc-700">—</span>}</td>
                    <td className="px-3 py-1.5">
                      <div className="flex items-center gap-2">
                        <div className="h-2 grow rounded-full bg-zinc-800 overflow-hidden flex" title="green = in stock now · blue = arrives during September (plan) · full bar = the month's need">
                          <div className="bg-emerald-500/70" style={{ width: `${wOpen}%` }} />
                          <div className="bg-sky-500/70" style={{ width: `${wLand}%` }} />
                        </div>
                        <span className={`text-xs tabular-nums w-9 text-right ${enough ? "text-emerald-300" : "text-red-400"}`}>
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
                    Bought in September under their own names — not in the list above:
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
                        <span className="ml-2 font-sans text-violet-300">{usedL > 0 ? "ready-mixed oil — filled as itself" : "arrives, but no September product uses it"}</span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-600" title={`Ready-mixed oil in stock on ${start} is not seen by the planner — see the note below`}>—</td>
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
          &ldquo;Arrives&rdquo; = oil already on order <em>plus</em> what the planner orders during the month. Do not add it
          on top of &ldquo;On order now&rdquo;. Oil takes {M.lead_days.oil} days to arrive (measured — real), and the plan
          takes every order to arrive exactly on time — our guess. &ldquo;Used&rdquo; = oil that went into bottles. The
          month&apos;s total oil use is {fmt(oilUsedTotal)} L. That includes {fmt(flushDelta)} L used to wash the machines at
          oil changes, which is not counted under any one oil. Oils that go by two names are counted as one oil.
        </p>
      </Section>

      {/* ---------------- ready-mixed oils ---------------- */}
      <Section title="Ready-mixed oils — the one thing the planner cannot see">
        <div className="rounded-xl border border-violet-800/40 bg-violet-950/15 p-5">
          <div className="text-xs uppercase tracking-wider text-violet-300/80 mb-1">A limit of the computer, not a fact about the godown</div>
          <p className="text-sm text-zinc-300 max-w-3xl leading-relaxed">
            Some products are filled with a ready-mixed oil ({blendExtras.map((c) => names.get(c) ?? c).join(", ") || "see the table"}).
            The planner works out how much of each base oil goes into the mix — that is what the table above counts. When
            it needs the mix in the middle of the month, it buys and fills it under its own name. What it cannot see is{" "}
            <span className="text-zinc-100">ready-mixed oil already in stock on {start}</span>. So it may order base oil we do
            not really need, and the &ldquo;left on {monthEnd}&rdquo; figure below is a little low.
          </p>
        </div>
      </Section>

      {/* ---------------- products no machine can fill ---------------- */}
      <Section title={`${M.unproducible.length} products no machine can fill`}
        right={<span className="text-xs text-zinc-500">also marked on <Link href="/order-by" className="underline decoration-zinc-700 underline-offset-2">Order by when</Link></span>}>
        <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5">
          <p className="text-sm text-zinc-300 max-w-3xl">
            This month&apos;s target has {M.unproducible.length} products that <span className="text-zinc-100">no machine
            here can fill</span>: {sizesWords}. Together that is {fmt(unprodLitres)} L — {unprodPct.toFixed(1)}% of the{" "}
            {fmt(O.plan.litres)} L target. They will not run, whatever the stock. Either a machine is set up for{" "}
            {sizesWords}, or these litres come out of the target.
          </p>
          <div className="rounded-lg border border-red-900/40 overflow-x-auto mt-4">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900/70 text-zinc-400 text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">Product</th>
                  <th className="px-3 py-2 font-medium">Needs</th>
                  <th className="px-3 py-2 font-medium text-right">Target pieces</th>
                  <th className="px-3 py-2 font-medium text-right">Target litres</th>
                  <th className="px-3 py-2 font-medium text-right">Worth (rough)</th>
                </tr>
              </thead>
              <tbody>
                {M.unproducible.map((u) => (
                  <tr key={u.code} className="border-t border-zinc-900">
                    <td className="px-3 py-1.5">
                      <div className="text-zinc-100">{u.sku}</div>
                      <div className="text-xs text-zinc-600 font-mono">{u.code} · {fmt(u.litres_per_piece)} L each</div>
                    </td>
                    <td className="px-3 py-1.5"><span className="text-red-400">{packWords(u)}</span> <span className="text-zinc-500 text-xs">— no machine here fills these</span></td>
                    <td className="px-3 py-1.5 text-right tabular-nums">{fmt(u.plan_pieces)}</td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{fmt(u.plan_litres)} L</td>
                    <td className="px-3 py-1.5 text-right tabular-nums">
                      {u.value_est_rs != null ? money(u.value_est_rs) : "—"}
                      {u.value_est_derived && <span className="ml-1 text-xs text-zinc-500" title="A rough figure — selling price per litre × litres, not from any order">rough</span>}
                    </td>
                  </tr>
                ))}
                <tr className="border-t border-zinc-800 bg-zinc-900/50">
                  <td className="px-3 py-1.5 text-zinc-400" colSpan={2}>All {M.unproducible.length} together</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-300">{fmt(M.unproducible.reduce((a, u) => a + u.plan_pieces, 0))}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{fmt(unprodLitres)} L</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-300">{money(unprodValue)} <span className="ml-1 text-xs text-zinc-500">rough</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Section>

      {/* ---------------- oil left at the end ---------------- */}
      <Section title={`Oil left on ${monthEnd} — what carries into October`}>
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/15 p-5">
            <div className="text-xs uppercase tracking-wider text-emerald-300/80">Loose oil left on {monthEnd} · the computer&apos;s plan</div>
            <div className="text-3xl font-semibold mt-1 text-emerald-300">{fmt(closingOil)} L</div>
            <div className="text-sm text-zinc-400 mt-1">≈ {tonnes(closingOil)} of oil — counting the {oilRows.length} oils the products use</div>
            <div className="mt-3 pt-3 border-t border-emerald-900/40 text-xs text-zinc-400 space-y-1 tabular-nums">
              <div className="flex justify-between"><span>In stock on {start}</span><span>{fmt(openingOil13)} L</span></div>
              <div className="flex justify-between"><span>+ arrives in Sept (plan)</span><span>{fmt(recvAll)} L</span></div>
              <div className="flex justify-between"><span>− used in Sept, incl. machine washing (plan)</span><span>{fmt(oilUsedTotal)} L</span></div>
              <div className="flex justify-between text-emerald-300 border-t border-emerald-900/40 pt-1"><span>= left on {monthEnd}</span><span>{fmt(closingOil)} L</span></div>
            </div>
          </div>
          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 text-sm text-zinc-400 space-y-2.5">
            <div className="text-xs uppercase tracking-wider text-zinc-500">Read this number with care</div>
            <div><Pill tone="violet">the computer&apos;s plan</Pill> <span className="ml-1">It only comes true if September runs exactly as planned. A late tanker moves it down. A lost day moves it up.</span></div>
            {octL > 0 && (
              <div><Pill tone="amber">arrives in October</Pill> <span className="ml-1">{litresProse(octL)} of oil ordered in September arrives only in October ({octLines} {plural(octLines, "order", "orders")}, {dlabel(octDates[0])}–{dlabel(octDates[octDates.length - 1])}). It is <span className="text-zinc-200">not</span> in this figure.</span></div>
            )}
            <div><Pill tone="amber">a different count</Pill> <span className="ml-1">This counts the {oilRows.length} oils the products use. The {start} count of all oil ({fmt(O.opening.oil_l)} L) is a wider count — do not compare the two.</span></div>
            <div><Pill tone="amber">ready-mixed</Pill> <span className="ml-1">Ready-mixed oil in stock on {start} is not counted (note above), so the real figure is a little higher.</span></div>
            <div><Pill tone="zinc">carry</Pill> <span className="ml-1">Treat it as October&apos;s <em>planned</em> starting stock, not what SAP will show. The biggest carry is{" "}
              <span className="text-zinc-200">{topCarry.name.toLowerCase()} at {fmt(closing(topCarry))} L</span>.</span></div>
          </div>
        </div>
      </Section>

      {/* ---------------- packing material + the two ways of saying "nothing" ---------------- */}
      <Section title="Packing material — and two ways of saying “nothing in stock”"
        right={<span className="text-xs text-zinc-500">item-by-item list on <Link href="/order-by" className="underline decoration-zinc-700 underline-offset-2">Order by when</Link></span>}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card title="Packing items" value={`${packRows.length}`} sub={`of ${M.components_in_plan} materials in this month's target`} />
          <Card title="Not enough for the month" value={`${packUnder}`} sub={`even counting what is on order — ${packLate} already late, order today`} tone="text-amber-300" />
          <Card title="Nothing in stock, nothing on order" value={`${z.literal.items}`} sub={`stops ${money(z.literal.blocked_value_rs)} of products (${z.literal.skus_blocked} ${plural(z.literal.skus_blocked, "product", "products")})`} tone="text-red-400" />
          <Card title="Almost nothing in stock" value={`${z.august_rule.items}`} sub={`so little it counts as nothing — August's rule. Stops ${money(z.august_rule.blocked_value_rs)} of products (${z.august_rule.skus_blocked} ${plural(z.august_rule.skus_blocked, "product", "products")})`} tone="text-red-400" />
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Two different counts, both true. &ldquo;Nothing in stock, nothing on order&rdquo; = {z.literal.zero_pack ?? 0} packing{" "}
          {plural(z.literal.zero_pack ?? 0, "item", "items")} and {z.literal.zero_oil ?? 0} {plural(z.literal.zero_oil ?? 0, "oil", "oils")} (a product
          stopped by two missing items is counted once). It is smaller than the {z.opening_zero_reconciliation.opening_items}{" "}
          &ldquo;nothing in stock&rdquo; items above because {z.opening_zero_reconciliation.chase_items} of those{" "}
          {plural(z.opening_zero_reconciliation.chase_items, "is", "are")} already on order — chase it. Packing stays counted in
          pieces throughout — a cap and a carton each count as one.
        </p>
      </Section>

      <p className="mt-8 text-[11px] text-zinc-600 max-w-3xl">
        Where these numbers come from: the stock counted in SAP on {start} evening. Month need = this month&apos;s target ×
        what goes into each bottle. Arrivals and use are the computer&apos;s plan — oil takes {M.lead_days.oil} days to arrive,
        packing {M.lead_days.packaging} days (measured — real), and the plan takes every order to arrive exactly on time (our
        guess). Products the planner counts: {O.plan.skus}. Materials: {M.components_in_plan}. Products with no machine:{" "}
        {M.unproducible.length}.
      </p>
    </div>
  );
}
