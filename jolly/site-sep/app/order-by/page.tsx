import { getMaterials, getOverview, getHonesty, getSpine, getDay, packSizesWords } from "../../lib/data";
import { Card, Section, Pill } from "../../components/Card";
import SimBadge from "../../components/SimBadge";
import OrderByHeadline from "../../components/OrderByHeadline";
import OrderByZeros from "../../components/OrderByZeros";
import OrderByTable from "../../components/OrderByTable";
import {
  obFmt, obMoney, obDate, obUnit, obLakh, obDays, obEnoughLabel, obPackDesc, obMaterial,
} from "../../components/OrderByFmt";

export const metadata = {
  title: "Order by when",
  description: "What to buy for September, and the last date to order it. Late items first.",
};

export default function OrderBy() {
  const M = getMaterials();
  const O = getOverview();
  const H = getHonesty();
  const rows = M.rows;

  const freeze = O.meta.frozen; // the day the stock was counted
  const horizon0 = O.meta.horizon[0];
  const week1End = new Date(Date.parse(horizon0) + 6 * 86400000).toISOString().slice(0, 10);

  // headline: the late row with the biggest shortfall — selected, not named
  const late = rows.filter((r) => r.late);
  const worst = [...late].sort((a, b) => b.short - a.short)[0];
  const otherLateOils = worst
    ? late
        .filter((r) => r.kind === "OIL" && r.code !== worst.code)
        .sort((a, b) => (a.order_by || "").localeCompare(b.order_by || ""))
    : [];

  // chase set: nothing in stock on day 1, but a PO already covers the need
  const chaseRows = rows.filter((r) => r.on_hand === 0 && r.on_order > 0 && r.need > 0);
  const chaseCodes = chaseRows.map((r) => r.code);
  const chaseSet = new Set(chaseCodes);
  const landing = new Map<string, { date: string; qty: number }>();
  let landFirst = "";
  let landLast = "";
  for (const s of getSpine()) {
    const d = getDay(s.n);
    for (const rec of d.received) {
      if (chaseSet.has(rec.code) && !landing.has(rec.code)) landing.set(rec.code, { date: d.date, qty: rec.qty });
      if (!landFirst || d.date < landFirst) landFirst = d.date;
      if (!landLast || d.date > landLast) landLast = d.date;
    }
  }

  // the two "nothing in stock" lists — kept apart
  const litRows = rows.filter((r) => r.zero_literal).sort((a, b) => b.value_at_risk - a.value_at_risk);
  const augRows = rows
    .filter((r) => r.zero_august_rule)
    .sort((a, b) => a.cover_pct - b.cover_pct || b.need - a.need);
  const litInsideAug = litRows.every((r) => r.zero_august_rule);

  // "enough for planned runs" that is still short of the full target — volume never booked
  const coveredShort = rows.filter((r) => r.status === "covered" && r.short > 0).sort((a, b) => b.short - a.short);
  const unschedCount = rows.filter((r) => r.order_basis === "unscheduled").length;
  const dueInsideWeek1 = M.must_order_week1 - M.already_late;

  // the honesty flags this page renders, in plain words
  const arrivalIsGuess = H.assumed.some((s) => /lead/i.test(s));
  const hasInboundNote = !!H.provenance["inbound"];

  const unprodLitres = M.unproducible.reduce((a, u) => a + u.plan_litres, 0);
  const unprodSizes = packSizesWords(M.unproducible);
  const openZero = M.opening_at_zero;

  return (
    <div>
      <h1 className="text-2xl font-bold">
        Order by when <SimBadge kind="plan" note="A plan for September, made by computer. Nothing here has happened yet." />
      </h1>
      <p className="text-base text-zinc-200 mt-2 max-w-3xl">
        What to buy, and the last date to order it.{" "}
        <span className="text-red-300 font-semibold">
          {obFmt(M.already_late)} items are already late — order them today.
        </span>{" "}
        {obFmt(M.must_order_week1)} must be ordered this week (the {obFmt(M.already_late)} late ones, plus{" "}
        {obFmt(dueInsideWeek1)} more).
      </p>
      <p className="text-sm text-amber-200/90 mt-1 max-w-3xl">
        {obFmt(M.already_late)} cheezein pehle se late hain — aaj hi order karo.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
        <Card
          title="Already late"
          value={obFmt(M.already_late)}
          sub="the last date to order has passed, or is today — order now"
          tone="text-red-400"
        />
        <Card
          title="Order this week"
          value={obFmt(M.must_order_week1)}
          sub={`by ${obDate(week1End)} — includes the ${obFmt(M.already_late)} already late`}
          tone="text-amber-300"
        />
        <Card
          title="Not enough for the whole month"
          value={`${obFmt(M.under_100_cover)} of ${obFmt(M.components_in_plan)}`}
          sub="stock + on order is less than the month's need"
        />
        <Card
          title="How long orders take"
          value={`oil ${obDays(M.lead_days.oil)} · packing ${obDays(M.lead_days.packaging)}`}
          sub="measured — real"
          tone="text-emerald-400"
        />
      </div>

      <Section
        title="The biggest late order"
        right={<span className="text-xs text-zinc-500">the late item with the biggest shortfall</span>}
      >
        {worst ? (
          <OrderByHeadline worst={worst} otherLateOils={otherLateOils} freeze={freeze} today={horizon0} />
        ) : (
          <p className="text-sm text-zinc-400">No item is late.</p>
        )}
      </Section>

      <Section
        title="Has a PO coming — chase it"
        right={<span className="text-xs text-zinc-500">already ordered — the job is the truck, not another PO</span>}
      >
        <div className="rounded-xl border border-sky-900/50 bg-sky-950/15 p-4">
          <p className="text-sm text-zinc-300 max-w-3xl">
            {chaseRows.length === 1 ? "One item has" : `${obFmt(chaseRows.length)} items have`} nothing in stock
            today, but a PO is already placed for the full need. Ordering again doubles the stock, not the speed.
            Chase the truck.
          </p>
          <div className="mt-3 grid sm:grid-cols-2 gap-3">
            {chaseRows.map((r) => {
              const l = landing.get(r.code);
              return (
                <div key={r.code} className="rounded-lg border border-sky-900/40 bg-zinc-900/40 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-zinc-100 text-sm">{r.name}</div>
                    <Pill tone="blue">CHASE THE TRUCK</Pill>
                  </div>
                  <div className="text-[11px] text-zinc-600">
                    <span className="font-mono">{r.code}</span> · {obMaterial(r.name, r.kind)}
                  </div>
                  <div className="text-sm text-zinc-400 mt-2">
                    needs {obFmt(r.need)} {obUnit(r.uom)} · in stock{" "}
                    <span className="text-red-300">nothing</span> · coming{" "}
                    <span className="text-sky-300">{obFmt(r.on_order)} {obUnit(r.uom)}</span>
                  </div>
                  <div className="text-sm mt-1">
                    {l ? (
                      <>
                        <span className="text-zinc-400">expected to arrive</span>{" "}
                        <span className="text-sky-200 font-medium">{obDate(l.date)}</span>{" "}
                        <span className="text-zinc-500">· {obFmt(l.qty)} {obUnit(r.uom)}</span>{" "}
                        <SimBadge
                          kind="assumed"
                          note={`Our guess, not a delivery date: a PO lands order date + ${obDays(r.lead_days)}. POs already late on ${obDate(horizon0)} are spread across the first working week.`}
                        />
                      </>
                    ) : (
                      <span className="text-zinc-500">no arrival inside September in this plan</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          {hasInboundNote && (
            <p className="text-[11px] text-zinc-600 mt-3 max-w-3xl">
              &ldquo;Coming&rdquo; = POs open in SAP on {obDate(freeze)}. Where a PO has no delivery date, we take order
              date + {obDays(M.lead_days.oil)} for oil, + {obDays(M.lead_days.packaging)} for packing material. POs
              already late on {obDate(horizon0)} are spread across the first working week — our guess, not measured.
              {landFirst && landLast && (
                <>
                  {" "}
                  In this plan, everything on order arrives between {obDate(landFirst)} and {obDate(landLast)}.
                </>
              )}
            </p>
          )}
        </div>
      </Section>

      <Section
        title="Nothing in stock — two lists"
        right={<span className="text-xs text-zinc-500">kept apart, never added together</span>}
      >
        <OrderByZeros z={M.zero_definitions} litRows={litRows} augRows={augRows} litInsideAug={litInsideAug} />
        <p className="text-xs text-zinc-500 mt-2">
          For the record: {obFmt(openZero.length)} items have nothing in stock on {obDate(horizon0)} — the{" "}
          {obFmt(litRows.length)} in list 1 with nothing coming, plus {obFmt(chaseRows.length)} with a PO coming
          (chase).
        </p>
      </Section>

      <Section
        title="Every item, every date"
        right={<span className="text-xs text-zinc-500">most urgent first — late at the top, then by last date</span>}
      >
        <div className="rounded-lg border border-amber-900/40 bg-amber-950/10 px-4 py-2.5 mb-3 text-sm text-zinc-300">
          <span className="text-amber-300 font-medium">This week:</span> {obFmt(M.must_order_week1)} items
          must be on a PO by {obDate(week1End)} — the {obFmt(M.already_late)} already late, plus{" "}
          {obFmt(dueInsideWeek1)} more due this week. Tap <span className="text-amber-200">This week</span> below.
        </div>
        <OrderByTable rows={rows} freeze={freeze} today={horizon0} week1End={week1End} chaseCodes={chaseCodes} />
        <ul className="mt-3 text-xs text-zinc-500 space-y-1.5 max-w-4xl list-disc pl-4">
          <li>
            <span className="text-zinc-400">In stock</span> and <span className="text-zinc-400">Coming</span> = SAP
            stock and open POs on {obDate(freeze)}. Orders the plan itself would raise are not counted.
          </li>
          <li>
            <span className="text-zinc-400">Last date to order</span> = the day it runs out − the days it takes to
            arrive (oil {obDays(M.lead_days.oil)}, packing material {obDays(M.lead_days.packaging)}).{" "}
            {arrivalIsGuess && (
              <>
                <SimBadge kind="assumed" note="Our guess — not measured." /> Our guess — not measured: every order
                arrives exactly on time. A late truck moves every date here earlier.
              </>
            )}
          </li>
          <li>
            <span className="text-zinc-400">&ldquo;Enough for&rdquo;</span> = stock plus what is on order, as a share
            of the month&rsquo;s need.
          </li>
          <li>
            <span className="text-zinc-400">&ldquo;Enough for planned runs&rdquo;</span> = the runs booked never run
            out of it. But {obFmt(coveredShort.length)} of these are still short of the full month&rsquo;s target —
            that part was never booked (next section).
          </li>
          <li>
            <span className="text-zinc-400">&ldquo;No run booked&rdquo;</span> ({obFmt(unschedCount)} items): no run
            uses this item yet, so its date comes from the first customer order that needs it.
          </li>
          {worst && (
            <li>
              <span className="text-zinc-400">Litres and value held up</span> are worked out only for items with
              nothing in stock (list 1). A late item that still has some stock — like the {worst.name.toLowerCase()} —
              shows none. That is how it is counted, not an all-clear.
            </li>
          )}
        </ul>
      </Section>

      <Section
        title="Enough for planned runs, but short of the target"
        right={
          <span className="text-xs text-zinc-500">
            {obFmt(coveredShort.length)} items — no last date, still short
          </span>
        }
      >
        <p className="text-sm text-zinc-400 max-w-3xl mb-3">
          The planner only books runs it can feed. These {obFmt(coveredShort.length)} have enough for every run it
          booked, so they never get a last date. But the plan booked less than the target. So they are still short of
          the target. Buy more only if there are machine hours to use them.
        </p>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400 text-left">
              <tr>
                <th className="px-3 py-2 font-medium">Item</th>
                <th className="px-3 py-2 font-medium text-right">Need this month</th>
                <th className="px-3 py-2 font-medium text-right">In stock</th>
                <th className="px-3 py-2 font-medium text-right">Coming (on order)</th>
                <th className="px-3 py-2 font-medium text-right">Enough for</th>
                <th className="px-3 py-2 font-medium text-right">Short of target</th>
                <th className="px-3 py-2 font-medium">What it is for</th>
              </tr>
            </thead>
            <tbody>
              {coveredShort.map((r) => {
                const products = r.skus.split(";").filter(Boolean);
                return (
                  <tr key={r.code} className="border-t border-zinc-900">
                    <td className="px-3 py-1.5">
                      <div className="text-zinc-100">{r.name}</div>
                      <div className="text-xs text-zinc-600">
                        <span className="font-mono">{r.code}</span>
                        <span className={`ml-2 ${r.kind === "OIL" ? "text-emerald-500/80" : "text-zinc-500"}`}>
                          {obMaterial(r.name, r.kind)}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums whitespace-nowrap">
                      {obFmt(r.need)} <span className="text-zinc-600">{obUnit(r.uom)}</span>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-300">
                      {r.on_hand === 0 ? "nothing" : obFmt(r.on_hand)}
                    </td>
                    <td className={`px-3 py-1.5 text-right tabular-nums ${r.on_order > 0 ? "text-sky-300" : "text-zinc-600"}`}>
                      {r.on_order > 0 ? obFmt(r.on_order) : "—"}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-amber-300 whitespace-nowrap">
                      {obEnoughLabel(r.cover_pct)}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{obFmt(r.short)}</td>
                    <td className="px-3 py-1.5 text-xs text-zinc-500 max-w-[240px]" title={products.join(" · ")}>
                      {products.slice(0, 2).join(" · ")}
                      {products.length > 2 ? ` +${products.length - 2} more` : ""}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Ordering cannot fix these" right={<span className="text-xs text-zinc-500">no machine can fill them</span>}>
        <div className="rounded-xl border border-amber-900/40 bg-amber-950/10 p-4">
          <p className="text-sm text-zinc-300 max-w-3xl">
            {obFmt(M.unproducible.length)} products — {obLakh(unprodLitres, "litres")} of the target — cannot be made
            on any machine here: {unprodSizes}. Their materials still count in
            &ldquo;Need this month&rdquo; above.
            Buying those materials will not help until there is a machine.
          </p>
          <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {M.unproducible.map((u) => (
              <div key={u.code} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
                <div className="text-sm text-zinc-100">{u.sku}</div>
                <div className="text-[11px] text-zinc-600 font-mono">{u.code}</div>
                <div className="text-xs text-zinc-400 mt-2">
                  {obFmt(u.plan_litres)} litres in the target · needs a{" "}
                  <span className="text-amber-300">{obPackDesc(u)}</span> machine
                </div>
                {typeof u.value_est_rs === "number" && (
                  <div className="text-xs text-zinc-500 mt-1">
                    ≈ {obMoney(u.value_est_rs)}{" "}
                    {u.value_est_derived && (
                      <>
                        <SimBadge kind="derived" note="An estimate — worked out from other numbers, not measured." />{" "}
                        estimate
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </Section>
    </div>
  );
}
