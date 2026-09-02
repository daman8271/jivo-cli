import { getMaterials, getOverview, getHonesty, getSpine, getDay } from "../../lib/data";
import { Card, Section, Pill } from "../../components/Card";
import SimBadge from "../../components/SimBadge";
import OrderByHeadline from "../../components/OrderByHeadline";
import OrderByZeros from "../../components/OrderByZeros";
import OrderByTable from "../../components/OrderByTable";
import { obFmt, obMoney, obDate, obUnit } from "../../components/OrderByFmt";

export const metadata = {
  title: "Order-by",
  description:
    "What to order and by when for the September plan — late items first, measured lead times, both zero definitions kept apart.",
};

export default function OrderBy() {
  const M = getMaterials();
  const O = getOverview();
  const H = getHonesty();
  const rows = M.rows;

  const freeze = O.meta.frozen;
  const horizon0 = O.meta.horizon[0];
  const week1End = new Date(Date.parse(horizon0) + 6 * 86400000).toISOString().slice(0, 10);

  // headline: the late row with the biggest shortfall — selected, not named
  const late = rows.filter((r) => r.late);
  const worst = [...late].sort((a, b) => b.short - a.short)[0];
  const otherLateOils = late
    .filter((r) => r.kind === "OIL" && r.code !== worst.code)
    .sort((a, b) => (a.order_by || "").localeCompare(b.order_by || ""));

  // chase set: physically zero at open, but a live PO already covers the need
  const chaseRows = rows.filter((r) => r.on_hand === 0 && r.on_order > 0 && r.need > 0);
  const chaseCodes = chaseRows.map((r) => r.code);
  const chaseSet = new Set(chaseCodes);
  const landing = new Map<string, { date: string; qty: number }>();
  for (const s of getSpine()) {
    const d = getDay(s.n);
    for (const rec of d.received) {
      if (chaseSet.has(rec.code) && !landing.has(rec.code)) landing.set(rec.code, { date: d.date, qty: rec.qty });
    }
  }

  // the two zero definitions — kept apart
  const litRows = rows.filter((r) => r.zero_literal).sort((a, b) => b.value_at_risk - a.value_at_risk);
  const augRows = rows
    .filter((r) => r.zero_august_rule)
    .sort((a, b) => a.cover_pct - b.cover_pct || b.need - a.need);
  const litInsideAug = litRows.every((r) => r.zero_august_rule);

  // "covered" that is still short of the full plan — volume the schedule never ran
  const coveredShort = rows.filter((r) => r.status === "covered" && r.short > 0).sort((a, b) => b.short - a.short);
  const unschedCount = rows.filter((r) => r.order_basis === "unscheduled").length;
  const dueInsideWeek1 = M.must_order_week1 - M.already_late;

  const leadAssumption = H.assumed.find((s) => /lead time/i.test(s));
  const inboundProv = H.provenance["inbound"];

  const unprodLitres = M.unproducible.reduce((a, u) => a + u.plan_litres, 0);
  const openZero = M.opening_at_zero;

  return (
    <div>
      <h1 className="text-2xl font-bold">
        Order-by dates <SimBadge kind="plan" />
      </h1>
      <p className="text-sm text-zinc-400 mt-1 max-w-3xl">
        Everything the September plan has to buy, with the last day each item can go on a PO before a run slips. At
        the {obDate(freeze)} freeze, <span className="text-red-300">{M.already_late} of {M.components_in_plan}</span>{" "}
        components were already past that day; {M.must_order_week1} must be ordered inside week&nbsp;1. This page is
        where the plan is won or lost — the build list only holds if these dates do.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
        <Card
          title="Already late at the freeze"
          value={obFmt(M.already_late)}
          sub="order today and the run still slips"
          tone="text-red-400"
        />
        <Card
          title="Must order in week 1"
          value={obFmt(M.must_order_week1)}
          sub={`by ${obDate(week1End)} — includes the ${obFmt(M.already_late)} already late`}
          tone="text-amber-300"
        />
        <Card
          title="Under 100% month cover"
          value={`${obFmt(M.under_100_cover)} of ${obFmt(M.components_in_plan)}`}
          sub="(on hand + on order) ÷ full-plan need"
        />
        <Card
          title="Lead times, measured"
          value={`oil ${M.lead_days.oil} d · pack ${M.lead_days.packaging} d`}
          sub="order-by = first short day − lead"
          tone="text-emerald-400"
        />
      </div>

      <Section title="The headline case" right={<span className="text-xs text-zinc-500">largest shortfall among the late items</span>}>
        <OrderByHeadline worst={worst} otherLateOils={otherLateOils} freeze={freeze} />
      </Section>

      <Section
        title="Chase, don't order"
        right={<span className="text-xs text-zinc-500">already on a PO — the job is the truck, not the order pad</span>}
      >
        <div className="rounded-xl border border-sky-900/50 bg-sky-950/15 p-4">
          <p className="text-sm text-zinc-300 max-w-3xl">
            {chaseRows.length === 1 ? "One item opens" : `${chaseRows.length} items open`} the month at physical zero
            with a live PO already covering the need. Raising another order doubles the stock, not the speed — these
            are <span className="text-sky-300 font-medium">chase</span> calls.
          </p>
          <div className="mt-3 grid sm:grid-cols-2 gap-3">
            {chaseRows.map((r) => {
              const l = landing.get(r.code);
              return (
                <div key={r.code} className="rounded-lg border border-sky-900/40 bg-zinc-900/40 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-zinc-100 text-sm">{r.name}</div>
                    <Pill tone="blue">CHASE</Pill>
                  </div>
                  <div className="text-[11px] text-zinc-600 font-mono">{r.code}</div>
                  <div className="text-sm text-zinc-400 mt-2">
                    needs {obFmt(r.need)} {obUnit(r.uom)} · on hand{" "}
                    <span className="text-red-300">{obFmt(r.on_hand)}</span> · on order{" "}
                    <span className="text-sky-300">{obFmt(r.on_order)} {obUnit(r.uom)}</span>
                  </div>
                  <div className="text-sm mt-1">
                    {l ? (
                      <>
                        <span className="text-zinc-400">first landing</span>{" "}
                        <span className="text-sky-200 font-medium">{obDate(l.date)}</span>{" "}
                        <span className="text-zinc-500">· {obFmt(l.qty)} {obUnit(r.uom)}</span>{" "}
                        <SimBadge kind="assumed" note="Landing date from the freeze's inbound schedule — POs land on their measured lead, and lines already overdue at 1 Sep are spread across the first working week by assumption." />
                      </>
                    ) : (
                      <span className="text-zinc-500">no landing inside September&rsquo;s inbound schedule</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          {inboundProv && <p className="text-[11px] text-zinc-600 mt-3 max-w-3xl">Inbound basis: {inboundProv}</p>}
        </div>
      </Section>

      <Section
        title="At zero — two definitions, two blocks"
        right={<span className="text-xs text-zinc-500">never added together</span>}
      >
        <OrderByZeros
          z={M.zero_definitions}
          litRows={litRows}
          augRows={augRows}
          litInsideAug={litInsideAug}
        />
        <p className="text-xs text-zinc-500 mt-2">
          For the record: {openZero.length} items open the month at physical zero — the {litRows.length} above with
          nothing coming, plus {chaseRows.length} already covered by a live PO (the chase{" "}
          {chaseRows.length === 1 ? "item" : chaseRows.length === 2 ? "pair" : "items"}).
        </p>
      </Section>

      <Section
        title="Every component, every date"
        right={<span className="text-xs text-zinc-500">sorted by urgency — late first, then soonest order-by</span>}
      >
        <div className="rounded-lg border border-amber-900/40 bg-amber-950/10 px-4 py-2.5 mb-3 text-sm text-zinc-300">
          <span className="text-amber-300 font-medium">The week-1 wall:</span> {obFmt(M.must_order_week1)} components
          must be on a PO by {obDate(week1End)} — the {obFmt(M.already_late)} already late plus {obFmt(dueInsideWeek1)}{" "}
          falling due inside the week. Use the <span className="text-amber-200">Week 1</span> chip below.
        </div>
        <OrderByTable rows={rows} freeze={freeze} week1End={week1End} chaseCodes={chaseCodes} />
        <ul className="mt-3 text-xs text-zinc-500 space-y-1.5 max-w-4xl list-disc pl-4">
          <li>
            <span className="text-zinc-400">Cover</span> counts on-hand plus POs live at the {obDate(freeze)} freeze
            only — the plan&rsquo;s own paper orders are excluded. Basis: {M.basis}.
          </li>
          <li>
            <span className="text-zinc-400">Order-by</span> = first short day − measured lead (oil {M.lead_days.oil} d,
            packaging {M.lead_days.packaging} d). <SimBadge kind="assumed" />{" "}
            {leadAssumption ? `${leadAssumption} — a late truck moves every date here left.` : "Supply is assumed to land exactly on lead."}
          </li>
          <li>
            <span className="text-zinc-400">&ldquo;covered&rdquo;</span> means the scheduled runs never outrun supply —
            but {obFmt(coveredShort.length)} covered items are still short against the full month plan; that volume
            simply never got scheduled (next section).
          </li>
          <li>
            <span className="text-zinc-400">&ldquo;unscheduled&rdquo;</span> under a date ({obFmt(unschedCount)} rows):
            the item&rsquo;s SKUs never reached a line, so its date anchors to the first demand for those SKUs instead
            of a run.
          </li>
          <li>
            <span className="text-zinc-400">Litres / value held</span> are computed only for at-zero items
            (definition&nbsp;1). A late item that still has stock — the {worst.name.toLowerCase()} included — shows
            none; that is a definition, not an all-clear.
          </li>
        </ul>
      </Section>

      <Section
        title="Covered for the schedule, short of the plan"
        right={<span className="text-xs text-zinc-500">{obFmt(coveredShort.length)} items with no order-by date but a real gap</span>}
      >
        <p className="text-sm text-zinc-400 max-w-3xl mb-3">
          The scheduler only books runs it can feed, so these {obFmt(coveredShort.length)} never trip an order-by date —
          the shortfall lands on plan volume that never reached a line. Topping them up is how the plan grows beyond
          what is scheduled (line hours permitting).
        </p>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400 text-left">
              <tr>
                <th className="px-3 py-2 font-medium">Component</th>
                <th className="px-3 py-2 font-medium text-right">Month need</th>
                <th className="px-3 py-2 font-medium text-right">On hand</th>
                <th className="px-3 py-2 font-medium text-right">On order</th>
                <th className="px-3 py-2 font-medium text-right">Cover</th>
                <th className="px-3 py-2 font-medium text-right">Short vs plan</th>
                <th className="px-3 py-2 font-medium">Feeds</th>
              </tr>
            </thead>
            <tbody>
              {coveredShort.map((r) => {
                const skus = r.skus.split(";").filter(Boolean);
                return (
                  <tr key={r.code} className="border-t border-zinc-900">
                    <td className="px-3 py-1.5">
                      <div className="text-zinc-100">{r.name}</div>
                      <div className="text-xs text-zinc-600 font-mono">
                        {r.code}
                        <span className={`ml-2 ${r.kind === "OIL" ? "text-emerald-500/80" : "text-zinc-600"}`}>{r.kind}</span>
                      </div>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums whitespace-nowrap">
                      {obFmt(r.need)} <span className="text-zinc-600">{obUnit(r.uom)}</span>
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-300">{obFmt(r.on_hand)}</td>
                    <td className={`px-3 py-1.5 text-right tabular-nums ${r.on_order > 0 ? "text-sky-300" : "text-zinc-600"}`}>
                      {obFmt(r.on_order)}
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-amber-300">
                      {r.cover_pct % 1 === 0 ? r.cover_pct.toFixed(0) : r.cover_pct.toFixed(1)}%
                    </td>
                    <td className="px-3 py-1.5 text-right tabular-nums text-zinc-100">{obFmt(r.short)}</td>
                    <td className="px-3 py-1.5 text-xs text-zinc-500 max-w-[240px]" title={skus.join(" · ")}>
                      {skus.slice(0, 2).join(" · ")}
                      {skus.length > 2 ? ` +${skus.length - 2}` : ""}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Ordering can't fix these" right={<span className="text-xs text-zinc-500">no line exists for them</span>}>
        <div className="rounded-xl border border-amber-900/40 bg-amber-950/10 p-4">
          <p className="text-sm text-zinc-300 max-w-3xl">
            {M.unproducible.length} plan SKUs — {obFmt(unprodLitres)} L of plan — cannot run on any configured line:{" "}
            {M.unproducible_note}. Their BOM components still count in the month need above, so ordering those parts
            cannot unlock a run until a line slot exists.
          </p>
          <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {M.unproducible.map((u) => (
              <div key={u.code} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
                <div className="text-sm text-zinc-100">{u.sku}</div>
                <div className="text-[11px] text-zinc-600 font-mono">{u.code}</div>
                <div className="text-xs text-zinc-400 mt-2">
                  {obFmt(u.plan_litres)} L planned · needs a <span className="text-amber-300">{u.slot_needed}</span> slot
                </div>
                {typeof u.value_est_rs === "number" && (
                  <div className="text-xs text-zinc-500 mt-1">
                    ≈ {obMoney(u.value_est_rs)} {u.value_est_derived && <SimBadge kind="derived" />}
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
