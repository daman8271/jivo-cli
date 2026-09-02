import Link from "next/link";
import {
  getOverview,
  getSpine,
  getScenarios,
  getLoops,
  getMaterials,
  getStorage,
  getHonesty,
  fmt,
  cr,
  money,
  dlabel,
  countWord,
} from "../lib/data";
import { Card, Section, Pill } from "../components/Card";
import SimBadge from "../components/SimBadge";
import OverviewStrip, { type StripDay } from "../components/OverviewStrip";
import OverviewDemand from "../components/OverviewDemand";
import ScenarioBoard from "../components/ScenarioBoard";
import OverviewLoop from "../components/OverviewLoop";

// Every figure on this page is read from data/*.json (written only by
// scripts/gen-data.py from the verified artifacts). Nothing is hand-typed.
export default function Overview() {
  const O = getOverview();
  const t = O.totals;
  const SC = getScenarios();
  const L = getLoops();
  const M = getMaterials();
  const ST = getStorage();
  const H = getHonesty();
  const spine = getSpine();

  const strip: StripDay[] = spine.map((d) => ({
    n: d.n,
    date: d.date,
    weekday: d.weekday,
    working: d.working,
    made_l: d.made_l,
    value_rs: d.value_rs,
    shipped_l: d.shipped_l,
    util: d.util,
    storage_pct: d.storage_pct,
    runs: d.runs,
    blocked: d.blocked,
    real_rows: d.orders.real_rows,
    forecast_rows: d.orders.forecast_rows,
  }));

  const vsAug = ((t.made_l - O.august.actual_made_l) / O.august.actual_made_l) * 100;
  const offDays = t.days - t.working_days;
  const shipDelta = t.shipped_l - t.made_l;
  const planGap = O.plan.litres - t.made_l;
  const unprodL = O.unproducible.reduce((a, u) => a + u.plan_litres, 0);
  const unprodSlots = [...new Set(O.unproducible.map((u) => u.slot_needed))].join(" or ");
  const day1 = spine[0];
  const rule = (id: string) => H.label_rules.find((r) => r.id === id)?.rule;
  const mm = O.materials_mini;
  const zd = M.zero_definitions;
  const zrec = zd.opening_zero_reconciliation;
  const db = O.day1_blocked;
  const hundredDates = O.storage.days_ge_100.map(dlabel).join(", ");
  const hundredWord = O.storage.days_ge_100.length === 1 ? "exactly once" : `${O.storage.days_ge_100.length} times`;
  const zeroAllPackaging = M.opening_at_zero.every((z) => z.kind === "PACKAGING");
  const throttleDates = ST.throttles.map((x) => dlabel(x.day)).join(", ");
  const taperCount = SC.scenarios.filter((s) => s.taper).length;
  const taperCountWord = countWord(taperCount).replace(/^./, (c) => c.toUpperCase());

  const N = ({ children }: { children: React.ReactNode }) => (
    <span className="text-zinc-100 font-medium tabular-nums">{children}</span>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold">
        {O.meta.month} — the forward plan <SimBadge kind="plan" />
      </h1>
      <p className="text-sm text-zinc-400 mt-1">
        Frozen {dlabel(O.meta.frozen)}. {O.meta.forward_rule}
      </p>

      {/* ---------------- headline ---------------- */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 mt-5">
        <div className="text-xs uppercase tracking-wider text-zinc-500">
          JIVO Oil · {SC.baseline.shift_hours}h shifts × {t.working_days} working days · {offDays} Sundays off
        </div>
        <div className="mt-4 flex flex-wrap items-end gap-x-10 gap-y-4">
          <div>
            <div className="text-6xl sm:text-7xl font-semibold tracking-tight leading-none">
              {O.plan.made_vs_plan_pct}
              <span className="text-zinc-500 text-4xl">%</span>
            </div>
            <div className="text-sm text-zinc-400 mt-2">of the September plan gets made under the baseline pattern</div>
          </div>
          <p className="text-lg text-zinc-300 max-w-2xl leading-relaxed">
            Run the floor as it runs today and September makes <N>{fmt(t.made_l)} L</N> — <N>{cr(t.value_rs)}</N> of
            output — and ships <N>{fmt(t.shipped_l)} L</N>, against a plan of <N>{fmt(O.plan.litres)} L</N> across{" "}
            {O.plan.skus} SKUs. That is{" "}
            <span className={vsAug >= 0 ? "text-emerald-300 font-medium" : "text-red-300 font-medium"}>
              {vsAug >= 0 ? "+" : ""}
              {vsAug.toFixed(1)}%
            </span>{" "}
            on the <N>{fmt(O.august.actual_made_l)} L</N> the plant actually made in August. The missing{" "}
            <N>{fmt(planGap)} L</N> is not idle will — it is storage, materials and the clock, plus{" "}
            <N>{fmt(unprodL)} L</N> that no configured line can make at all.
          </p>
        </div>
        <div className="mt-6">
          <div className="h-3 rounded-full bg-zinc-800 overflow-hidden">
            <div className="h-full bg-amber-500" style={{ width: `${O.plan.made_vs_plan_pct}%` }} />
          </div>
          <div className="flex justify-between text-[11px] text-zinc-500 mt-2">
            <span>{fmt(t.made_l)} L planned to be made</span>
            <span>
              plan {fmt(O.plan.litres)} L · {O.plan.skus} SKUs
            </span>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-zinc-800 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-zinc-500">
          <Pill tone="green">calibration</Pill>
          <span>
            Why believe a simulator: replayed on August it landed <span className="tabular-nums">{fmt(O.august.sim_made_l)} L</span>{" "}
            against <span className="tabular-nums">{fmt(O.august.actual_made_l)} L</span> actually made — within{" "}
            <span className="text-emerald-300 tabular-nums">{O.august.delta_pct}%</span>.
          </span>
        </div>
        <p className="text-[11px] text-zinc-600 mt-3">Plan source: {O.plan.source}</p>
      </div>

      {/* ---------------- six numbers ---------------- */}
      <Section title="The month in six numbers">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Card
            title="Litres made (planned)"
            value={`${fmt(t.made_l)} L`}
            sub={`best day ${dlabel(t.peak_day.date)} — ${fmt(t.peak_day.made_l)} L`}
          />
          <Card title="Output value" value={cr(t.value_rs)} sub="priced at the measured May–Jul realise per litre" />
          <Card
            title="Litres shipped"
            value={`${fmt(t.shipped_l)} L`}
            sub={
              shipDelta >= 0
                ? `${fmt(shipDelta)} L more shipped than made — drawn from opening stock`
                : `${fmt(-shipDelta)} L more made than shipped`
            }
          />
          <Card
            title="Line utilisation"
            value={`${t.util_median}%`}
            sub={`median working day, inside the ${SC.baseline.shift_hours}h window`}
            tone="text-amber-300"
          />
          <Card
            title="Runs on the board"
            value={fmt(t.runs)}
            sub={`${fmt(t.oil_changes)} oil changes · ${fmt(t.flushes)} flushes`}
          />
          <Card
            title="Godown pressure"
            value={`${O.storage.days_ge_95} days ≥95%`}
            sub={`hits 100% ${hundredWord} — ${hundredDates}`}
            tone="text-red-300"
          />
        </div>
      </Section>

      {/* ---------------- 30-day strip ---------------- */}
      <Section
        title="Every planned day of September"
        right={<span className="text-xs text-zinc-500">bar = litres made · colour = godown fill · click a day</span>}
      >
        <OverviewStrip days={strip} />
        <p className="text-xs text-zinc-500 mt-2 leading-relaxed">
          <span className="text-zinc-300 font-medium">Day 1 opens on a pile by design:</span> {rule("day1-pile")}{" "}
          The plan-SKU slice of that book at freeze: <span className="tabular-nums">{O.opening.plan_sku_backlog_docs}</span>{" "}
          open documents, <span className="tabular-nums">{O.opening.plan_sku_backlog_docs_overdue}</span> already
          overdue — so the plan invoices <span className="tabular-nums">{fmt(day1.dispatched.real_l)} L</span> against
          the pile on day 1 (<span className="tabular-nums">{fmt(day1.shipped_l)} L</span> in all — the rest serves{" "}
          <span className="text-sky-300">forecast</span> buckets nobody has ordered); the trucks leave on the declared{" "}
          {O.storage.invoice_truck_lag_days}-day invoice-to-truck lag.
        </p>
      </Section>

      {/* ---------------- demand mix ---------------- */}
      <Section
        title="What the demand stream really is"
        right={<span className="text-xs text-zinc-500">real vs forecast — split by channel, never mixed</span>}
      >
        <OverviewDemand demand={O.demand} ecomRule={rule("ecom-spread")} />
      </Section>

      {/* ---------------- binders ---------------- */}
      <Section
        title="What binds the month"
        right={<span className="text-xs text-zinc-500">three walls, in the order the plan hits them</span>}
      >
        {/* day-one alert — two separate facts, kept apart on purpose: day-1 blocking
            is an OIL story; the zero-stock packaging openers are a smaller, month-long
            chase. Merging them once misdirected the day-1 priority — never re-merge. */}
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 mb-3">
          <div className="flex flex-wrap items-center gap-2">
            <Pill tone="red">day-one alert</Pill>
            <span className="text-sm font-medium text-red-200">
              {fmt(db.products)} products sit blocked on day 1 ({fmt(db.attempts)} blocked scheduling attempts) — and
              the day-one wall is oil, not packaging
            </span>
          </div>
          <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
            <N>{db.by_binder_class.oil.products}</N> of the <N>{db.products}</N> blocked products wait on short oil —{" "}
            <N>{db.by_binder_class.oil.attempts}</N> of the <N>{db.attempts}</N> attempts,{" "}
            <N>{db.top_binder.attempts}</N> of those on{" "}
            <span className="text-zinc-100">{db.top_binder.name.toLowerCase()}</span>{" "}
            <span className="font-mono text-zinc-500">{db.top_binder.code}</span> alone. Only{" "}
            <N>{db.by_binder_class.zero_stock_packaging.products}</N>{" "}
            {db.by_binder_class.zero_stock_packaging.products === 1 ? "traces" : "trace"} to a zero-stock packaging
            item; <N>{db.by_binder_class.other_packaging.products}</N> wait on other packaging
            {db.products_in_multiple_classes > 0 && (
              <>
                {" "}
                ({db.products_in_multiple_classes} of the {db.products}{" "}
                {db.products_in_multiple_classes === 1 ? "is" : "are"} short in two classes at once)
              </>
            )}
            .{" "}
            <a href="#loop" className="text-amber-300 hover:underline">
              ↓ the loop
            </a>{" "}
            ·{" "}
            <Link href="/order-by" className="text-amber-300 hover:underline">
              → the order-by list
            </Link>
          </p>
          <p className="text-xs text-zinc-400 mt-3 leading-relaxed">
            Separately: {M.opening_at_zero.length} {zeroAllPackaging ? "packaging items" : "items"} open September at
            literal zero stock. The <span className="tabular-nums">{zd.literal.items}</span> with nothing on order hold{" "}
            <span className="tabular-nums">{money(zd.literal.blocked_value_rs)}</span> of plan across{" "}
            <span className="tabular-nums">{zd.literal.skus_blocked}</span> SKUs; the other{" "}
            <span className="tabular-nums">{zrec.chase_items}</span> already have a live PO to chase. Across the whole
            month these openers block <span className="tabular-nums">{db.zero_openers_products_blocked_month}</span>{" "}
            products — a chase, not the day-one wall.
          </p>
          <div className="flex flex-wrap gap-1.5 mt-3">
            {M.opening_at_zero.map((z) => (
              <span
                key={z.code}
                className="text-[11px] bg-zinc-950/60 border border-red-500/20 text-zinc-300 rounded px-1.5 py-0.5"
              >
                {z.name} <span className="text-zinc-600">{z.code}</span>
              </span>
            ))}
          </div>
          <p className="text-xs text-zinc-400 mt-3">
            <Link href="/order-by" className="text-amber-300 hover:underline">
              What to order, and by when → the order-by list
            </Link>
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-3">
          {/* storage */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-wider text-zinc-500">1 · Storage</div>
              <Pill tone="red">first wall</Pill>
            </div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              The godown hits <span className="text-red-300 font-medium">100% {hundredWord}</span> — {hundredDates} —
              and stands at 95% or more on <span className="tabular-nums">{O.storage.days_ge_95}</span> days. Production
            is capped to shipping headroom on {throttleDates}.
            </p>
            <p className="text-xs text-zinc-400 mt-2 tabular-nums">
              Ceiling: {fmt(ST.ceiling.working_l)} L working · {fmt(ST.ceiling.peak_l)} L peak{" "}
              <SimBadge kind="assumed" />
            </p>
            <p className="text-[11px] text-zinc-500 mt-1">
              {ST.ceiling.source} — open question {ST.ceiling.open_question}.
            </p>
            <Link href="/storage" className="text-amber-300 text-xs hover:underline mt-2 inline-block">
              → Storage
            </Link>
          </div>

          {/* materials */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-wider text-zinc-500">2 · Materials</div>
              <Pill tone="amber">the long wall</Pill>
            </div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              <span className="tabular-nums">{mm.under_100_cover}</span> of{" "}
              <span className="tabular-nums">{mm.components}</span> components are under 100% month cover;{" "}
              <span className="tabular-nums">{mm.must_order_week1}</span> must be ordered in week 1 and{" "}
              <span className="text-red-300 tabular-nums">{mm.already_late} are already late</span>.
            </p>
            <div className="text-xs text-zinc-400 mt-2 space-y-1">
              <div>
                At zero, {zd.literal.definition}: <span className="tabular-nums">{zd.literal.items}</span> items —{" "}
                <span className="tabular-nums">{money(zd.literal.blocked_value_rs)}</span> across{" "}
                <span className="tabular-nums">{zd.literal.skus_blocked}</span> SKUs blocked.
              </div>
              <div>
                At zero, {zd.august_rule.definition}: <span className="tabular-nums">{zd.august_rule.items}</span> items
                — <span className="tabular-nums">{money(zd.august_rule.blocked_value_rs)}</span> across{" "}
                <span className="tabular-nums">{zd.august_rule.skus_blocked}</span> SKUs.
              </div>
              <div className="text-[11px] text-zinc-500">
                {zd.note}. {zrec.note}.
              </div>
              <div>
                <span className="text-red-300 tabular-nums">{O.unproducible.length}</span> plan SKUs can never run — no{" "}
                {unprodSlots} line exists — <span className="tabular-nums">{fmt(unprodL)} L</span> of the plan.
              </div>
            </div>
            <div className="flex gap-3 mt-2">
              <Link href="/materials" className="text-amber-300 text-xs hover:underline">
                → Materials
              </Link>
              <Link href="/order-by" className="text-amber-300 text-xs hover:underline">
                → Order-by
              </Link>
            </div>
          </div>

          {/* hours */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-wider text-zinc-500">3 · Hours</div>
              <Pill tone="blue">the lever</Pill>
            </div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              Inside the {SC.baseline.shift_hours}h window the lines already run at a median{" "}
              <span className="text-amber-300 font-medium tabular-nums">{t.util_median}%</span> —{" "}
              <span className="tabular-nums">{fmt(SC.baseline.line_hours_used)}</span> line-hours over{" "}
              <span className="tabular-nums">{t.working_days}</span> working days, {offDays} Sundays off.
            </p>
            <p className="text-xs text-zinc-400 mt-2 tabular-nums">
              {fmt(t.runs)} runs · {fmt(t.oil_changes)} oil changes · {fmt(t.flushes)} flushes
            </p>
            <p className="text-xs text-zinc-400 mt-2">
              The only capacity not yet offered to the plan is evenings and Sundays — the shift board below prices
              exactly that.
            </p>
            <a href="#scenarios" className="text-amber-300 text-xs hover:underline mt-2 inline-block">
              ↓ Shift scenarios
            </a>
          </div>
        </div>
      </Section>

      {/* ---------------- scenarios ---------------- */}
      <div id="scenarios">
        <Section
          title={`If the plant ran longer — ${countWord(SC.scenarios.length + 1)} shift patterns`}
          right={
            <span className="text-xs text-zinc-500">
              simulated end-to-end with the same engine <SimBadge kind="simulated" />
            </span>
          }
        >
          <p className="text-sm text-zinc-400 mb-3 max-w-3xl">
            Extra hours turn into litres only until storage and materials push back — which is why the biggest pattern
            is not the best one. &ldquo;Extra hours → litres&rdquo; is the share of the additional line-hours each
            pattern actually converts.
            {taperCount > 0 && (
              <>
                {" "}
                {taperCountWord} of the patterns front-load — long shifts early, a shorter tail after the switch day —
                to test whether the early gain survives a cheaper back half.
              </>
            )}
          </p>
          <ScenarioBoard data={SC} />
        </Section>
      </div>

      {/* ---------------- the loop ---------------- */}
      <div id="loop">
      <Section
        title="The loop — how a shortage becomes a run"
        right={<span className="text-xs text-zinc-500">one chain from the plan&rsquo;s event stream</span>}
      >
        <p className="text-sm text-zinc-400 mb-3 max-w-3xl">
          The plan&rsquo;s whole supply story is one loop, run{" "}
          <span className="tabular-nums text-zinc-300">{L.ordered_events}</span> times: a blocker surfaces, the planner
          orders — usually the same day, sometimes days after the wall first bites — the measured lead time passes, the
          material lands, and the freed SKU runs where the calendar still allows. Not every chain gets all the way
          round (the tally below); the largest that closes end-to-end:
        </p>
        <OverviewLoop loops={L} leadDays={M.lead_days} />
      </Section>
      </div>
    </div>
  );
}
