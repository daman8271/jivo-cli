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
  litresProse,
  rupeesProse,
  packSizesWords,
  plural,
  speedPhrase,
} from "../lib/data";
import { Card, Section, Pill } from "../components/Card";
import SimBadge from "../components/SimBadge";
import OverviewStrip, { type StripDay } from "../components/OverviewStrip";
import OverviewDemand from "../components/OverviewDemand";
import ScenarioBoard from "../components/ScenarioBoard";
import OverviewLoop from "../components/OverviewLoop";

// The root segment gets no title template from its own layout, so the tab name is written in full here.
export const metadata = {
  title: "Summary · JIVO Mark 2 — September 2026 plan",
  description:
    "September 2026 on one page — what gets made, what is missing and why, and what a longer shift is worth. A plan made by computer; nothing here has happened.",
};

// Every figure on this page is read from data/*.json (written only by
// scripts/gen-data.py from the verified artifacts). Nothing is hand-typed.
// Words follow PLAIN-LANGUAGE.md: short sentences, factory words, the truth kept.
// Spoken Indian units (litresProse, rupeesProse) and the pack words come from
// lib, so every page says them the same way.

export default function Summary() {
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
  const gapPct = (100 - O.plan.made_vs_plan_pct).toFixed(0);
  const unprodL = O.unproducible.reduce((a, u) => a + u.plan_litres, 0);
  const unprodPacks = packSizesWords(O.unproducible);
  const day1 = spine[0];
  const mm = O.materials_mini;
  const zd = M.zero_definitions;
  const zrec = zd.opening_zero_reconciliation;
  const db = O.day1_blocked;
  const zeroAllPackaging = M.opening_at_zero.every((z) => z.kind === "PACKAGING");
  const zeroWord = zeroAllPackaging ? "packing items" : "items";
  const fullDates = O.storage.days_ge_100.map(dlabel).join(", ");
  const slowDates = ST.throttles.map((x) => dlabel(x.day)).join(", ");
  const longest = SC.scenarios.reduce((a, b) => (b.made_l > a.made_l ? b : a));
  const taperDays = [...new Set(SC.scenarios.filter((s) => s.taper).map((s) => s.taper!.boundary_day))].join(" and ");
  const taperCount = SC.scenarios.filter((s) => s.taper).length;
  const taperCountWord = countWord(taperCount).replace(/^./, (c) => c.toUpperCase());
  // machine speed: the plan runs every machine below its normal speed — say it, in words
  const effRule = H.label_rules.find((r) => r.id === "observed-then-derated");
  const eff = typeof effRule?.efficiency === "number" ? (effRule.efficiency as number) : null;
  const speedWord = eff === null ? null : speedPhrase(Math.round(eff * 100));
  const wa = O.whatsapp_mini;

  const N = ({ children }: { children: React.ReactNode }) => (
    <span className="text-zinc-100 font-medium tabular-nums">{children}</span>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold">
        {O.meta.month} — the plan <SimBadge kind="plan" />
      </h1>
      <p className="text-sm text-zinc-400 mt-1">
        Only the stock counted on {dlabel(O.meta.frozen)} is real. Everything else is what the computer expects.
      </p>

      {/* ---------------- the one line ---------------- */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 mt-5">
        <div className="text-xs uppercase tracking-wider text-zinc-500">
          JIVO Oil · {SC.baseline.shift_hours}-hour shift · {t.working_days} working days · {offDays} Sundays off
        </div>
        <div className="mt-4 flex flex-wrap items-end gap-x-10 gap-y-4">
          <div>
            <div className="text-6xl sm:text-7xl font-semibold tracking-tight leading-none">
              {O.plan.made_vs_plan_pct}
              <span className="text-zinc-500 text-4xl">%</span>
            </div>
            <div className="text-sm text-zinc-400 mt-2">of the target gets made</div>
          </div>
          <p className="text-lg text-zinc-300 max-w-2xl leading-relaxed">
            Running as we do today — {SC.baseline.shift_hours} hours, Sundays off — September makes{" "}
            <N>{litresProse(t.made_l)}</N>, worth <N>{rupeesProse(t.value_rs)}</N>. The target is <N>{litresProse(O.plan.litres)}</N>.
            That is <N>{O.plan.made_vs_plan_pct}%</N>. The rest is lost to three things: godown space, materials
            arriving late, and hours. And <N>{fmt(unprodL)} litres</N> are products no machine can fill.
          </p>
        </div>
        <div className="mt-6">
          <div className="h-3 rounded-full bg-zinc-800 overflow-hidden">
            <div className="h-full bg-amber-500" style={{ width: `${O.plan.made_vs_plan_pct}%` }} />
          </div>
          <div className="flex justify-between text-[11px] text-zinc-500 mt-2">
            <span>{fmt(t.made_l)} L the plan makes</span>
            <span>
              target {fmt(O.plan.litres)} L · {O.plan.skus} products
            </span>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-zinc-800 flex flex-wrap items-baseline gap-x-3 gap-y-1 text-xs text-zinc-400">
          <span>
            August made <span className="tabular-nums text-zinc-200">{litresProse(O.august.actual_made_l)}</span>. This plan is{" "}
            <span className={`tabular-nums font-medium ${vsAug >= 0 ? "text-emerald-300" : "text-red-300"}`}>
              {Math.abs(vsAug).toFixed(1)}% {vsAug >= 0 ? "more" : "less"}
            </span>
            .
          </span>
          <span className="flex flex-wrap items-baseline gap-x-2">
            <Pill tone="green">tested</Pill>
            <span>
              Tested on August: the computer said{" "}
              <span className="tabular-nums text-zinc-200">{litresProse(O.august.sim_made_l, 1)}</span>, the factory made{" "}
              <span className="tabular-nums text-zinc-200">{litresProse(O.august.actual_made_l, 1)}</span>. Almost the same
              — that is why these numbers can be trusted.
            </span>
          </span>
        </div>
      </div>

      {/* ---------------- six numbers ---------------- */}
      <Section title="The month in six numbers">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Card
            title="Litres made"
            value={`${fmt(t.made_l)} L`}
            sub={`best day ${dlabel(t.peak_day.date)} — ${fmt(t.peak_day.made_l)} L`}
          />
          <Card title="Worth" value={cr(t.value_rs)} sub="at the selling price per litre we measured in May–Jul" />
          <Card
            title="Litres billed"
            value={`${fmt(t.shipped_l)} L`}
            sub={
              shipDelta >= 0
                ? `${fmt(shipDelta)} L more billed than made — from stock already in the godown`
                : `${fmt(-shipDelta)} L more made than billed`
            }
          />
          <Card
            title="Machines busy"
            value={`${t.util_median}%`}
            sub={`on a normal working day, inside the ${SC.baseline.shift_hours}-hour shift`}
            tone="text-amber-300"
          />
          <Card title="Runs" value={fmt(t.runs)} sub={`${fmt(t.oil_changes)} oil changes`} />
          <Card
            title="Godown nearly full"
            value={`${O.storage.days_ge_95} ${plural(O.storage.days_ge_95, "day", "days")}`}
            sub={fullDates ? `completely full on ${fullDates}` : "never completely full"}
            tone={O.storage.days_ge_95 >= 10 ? "text-red-300" : "text-amber-300"}
          />
        </div>
      </Section>

      {/* ---------------- three reasons ---------------- */}
      <Section
        title={`Why ${gapPct}% of the target is missing — three reasons`}
        right={<span className="text-xs text-zinc-500">godown space · materials · hours</span>}
      >
        <div className="grid md:grid-cols-3 gap-3">
          {/* godown */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-wider text-zinc-500">1 · Godown space</div>
              <Pill tone="red">fills up first</Pill>
            </div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              Today&rsquo;s shift: the godown is nearly full on{" "}
              <span className="text-red-300 font-medium tabular-nums">
                {O.storage.days_ge_95} {plural(O.storage.days_ge_95, "day", "days")}
              </span>
              . {fullDates ? `Completely full on ${fullDates}.` : "Never completely full."}{" "}
              {slowDates ? `Production slowed for space on ${slowDates}.` : "Production never slowed for space."}
            </p>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              Run <span className="tabular-nums">{longest.shift_hours}</span> hours a day and it is nearly full on{" "}
              <span className="text-red-300 font-medium tabular-nums">{longest.days_storage_ge_95} days</span>. That is
              what stops the longer shifts.
            </p>
            <p className="text-xs text-zinc-400 mt-2">
              Godown full at <span className="tabular-nums">{litresProse(ST.ceiling.working_l)}</span> (
              <span className="tabular-nums">{litresProse(ST.ceiling.peak_l)}</span> if squeezed). This is Daman&rsquo;s
              number — not measured. <SimBadge kind="assumed" />
            </p>
            {ST.standing_at_open.assumed && (
              <p className="text-xs text-zinc-400 mt-1">
                Stock billed before {dlabel(O.meta.frozen)} but not yet trucked is not counted. The godown is really
                fuller on day 1.
              </p>
            )}
            <Link href="/storage" className="text-amber-300 text-xs hover:underline mt-2 inline-block">
              → Godown
            </Link>
          </div>

          {/* materials */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-wider text-zinc-500">2 · Materials arrive late</div>
              <Pill tone="amber">all month</Pill>
            </div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              <span className="tabular-nums">{mm.under_100_cover}</span> of{" "}
              <span className="tabular-nums">{mm.components}</span> materials are not enough for the whole month.{" "}
              <span className="text-red-300 font-medium tabular-nums">{mm.already_late} are already late — order today.</span>{" "}
              <span className="tabular-nums">{mm.must_order_week1}</span> must be ordered this week.
            </p>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              No machine can fill <span className="text-red-300 font-medium tabular-nums">{O.unproducible.length} products</span>{" "}
              ({unprodPacks}). That is <span className="tabular-nums">{fmt(unprodL)} L</span> of the target.
            </p>
            <p className="text-xs text-zinc-400 mt-2">
              The open purchase orders are already late. The plan guesses they all arrive in the first week.
            </p>
            <div className="flex gap-3 mt-2">
              <Link href="/materials" className="text-amber-300 text-xs hover:underline">
                → Stock
              </Link>
              <Link href="/order-by" className="text-amber-300 text-xs hover:underline">
                → Order by when
              </Link>
            </div>
          </div>

          {/* hours */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center justify-between">
              <div className="text-xs uppercase tracking-wider text-zinc-500">3 · Hours</div>
              <Pill tone="blue">the one thing we can change</Pill>
            </div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              Machines are already busy{" "}
              <span className="text-amber-300 font-medium tabular-nums">{t.util_median}%</span> of the{" "}
              {SC.baseline.shift_hours}-hour shift on a normal day.{" "}
              <span className="tabular-nums">{fmt(SC.baseline.line_hours_used)}</span> machine hours over{" "}
              <span className="tabular-nums">{t.working_days}</span> working days. {offDays} Sundays off.
            </p>
            <p className="text-xs text-zinc-400 mt-2 tabular-nums">
              {fmt(t.runs)} runs · {fmt(t.oil_changes)} oil changes
            </p>
            <p className="text-xs text-zinc-400 mt-2">
              The only hours not used yet are evenings and Sundays. The options below show what they are worth.
            </p>
            {speedWord && (
              <p className="text-xs text-zinc-400 mt-1">
                In this plan machines run at {speedWord}. That is what we measured in August — not a fault.
              </p>
            )}
            <a href="#scenarios" className="text-amber-300 text-xs hover:underline mt-2 inline-block">
              ↓ Shift options
            </a>
          </div>
        </div>

        {/* day one — two separate facts, kept apart on purpose: day-1 stuck products
            are an OIL story; the nothing-in-stock packing items are a smaller,
            month-long chase. Merging them once misdirected the day-1 priority. */}
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 mt-3">
          <div className="flex flex-wrap items-center gap-2">
            <Pill tone="red">day 1</Pill>
            <span className="text-sm font-medium text-red-200">
              {fmt(db.products)} products cannot run on day 1 — because of oil, not packing material
            </span>
          </div>
          <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
            <N>{db.by_binder_class.oil.products}</N> of the <N>{db.products}</N> wait for oil —{" "}
            <N>{db.top_binder.products}</N> of them for{" "}
            <span className="text-zinc-100">{db.top_binder.name.toLowerCase()}</span> alone.{" "}
            <N>{db.by_binder_class.other_packaging.products}</N> wait for packing material.{" "}
            {db.by_binder_class.zero_stock_packaging.products > 0 ? (
              <>
                <N>{db.by_binder_class.zero_stock_packaging.products}</N> wait for a packing item with nothing in stock.
              </>
            ) : (
              <>None is stuck on an item with nothing in stock.</>
            )}
            {db.products_in_multiple_classes > 0 && (
              <>
                {" "}
                ({db.products_in_multiple_classes} of the {db.products}{" "}
                {db.products_in_multiple_classes === 1 ? "is" : "are"} short of both.)
              </>
            )}{" "}
            <a href="#loop" className="text-amber-300 hover:underline">
              ↓ what happens next
            </a>
          </p>
          <p className="text-xs text-zinc-400 mt-3 leading-relaxed">
            Separately: <span className="tabular-nums">{M.opening_at_zero.length}</span> {zeroWord} have nothing in
            stock on day 1. <span className="tabular-nums">{zd.literal.items}</span> of them have nothing on order — they
            block <span className="tabular-nums">{money(zd.literal.blocked_value_rs)}</span> of the target (
            <span className="tabular-nums">{zd.literal.skus_blocked}</span> products).{" "}
            <span className="tabular-nums">{zrec.chase_items}</span> {plural(zrec.chase_items, "is", "are")} already
            ordered — chase it. Over the whole month these stop{" "}
            <span className="tabular-nums">{db.zero_openers_products_blocked_month}</span>{" "}
            {plural(db.zero_openers_products_blocked_month, "product", "products")} — a chase, not the day-1 problem.
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
            Also: <span className="tabular-nums">{zd.august_rule.items}</span> items have almost nothing in stock. They
            block <span className="tabular-nums">{money(zd.august_rule.blocked_value_rs)}</span> of the target (
            <span className="tabular-nums">{zd.august_rule.skus_blocked}</span> products).{" "}
            <Link href="/order-by" className="text-amber-300 hover:underline">
              What to order, and by when →
            </Link>
          </p>
        </div>
      </Section>

      {/* ---------------- shift options ---------------- */}
      <div id="scenarios">
        <Section
          title={`If the factory ran longer — ${countWord(SC.scenarios.length + 1)} shift options`}
          right={<span className="text-xs text-zinc-500">each one run through the same computer plan, all month</span>}
        >
          <p className="text-sm text-zinc-400 mb-3 max-w-3xl">
            Extra hours make extra litres only until the godown fills up or materials run out. So the longest shift
            is not the best one.
            {taperCount > 0 && (
              <>
                {" "}
                {taperCountWord} of the options start with long shifts and slow down after day {taperDays} — to see how
                much of the early gain stays.
              </>
            )}
          </p>
          <ScenarioBoard data={SC} />
        </Section>
      </div>

      {/* ---------------- stuck → ordered → arrived → running ---------------- */}
      <div id="loop">
        <Section
          title="Stuck → ordered → arrived → running"
          right={<span className="text-xs text-zinc-500">one example from the plan, step by step</span>}
        >
          <p className="text-sm text-zinc-400 mb-3 max-w-3xl">
            When a product cannot run, the planner orders the missing material — usually the same day, sometimes a few
            days later. The material takes its usual days to arrive. Then the product runs. This happened{" "}
            <span className="tabular-nums text-zinc-300">{L.ordered_events}</span> times in the plan. The biggest one:
          </p>
          <OverviewLoop loops={L} leadDays={M.lead_days} />
        </Section>
      </div>

      {/* ---------------- 30-day strip ---------------- */}
      <Section
        title="The month, day by day"
        right={<span className="text-xs text-zinc-500">bar = litres made · colour = how full the godown is · click a day</span>}
      >
        <OverviewStrip days={strip} />
        <p className="text-xs text-zinc-500 mt-2 leading-relaxed">
          <span className="text-zinc-300 font-medium">Day 1 starts with a pile of orders. That is real, not a mistake.</span>{" "}
          <span className="tabular-nums">{O.opening.plan_sku_backlog_docs}</span> customer orders were pending on{" "}
          {dlabel(O.meta.frozen)}, <span className="tabular-nums">{O.opening.plan_sku_backlog_docs_overdue}</span> of
          them already late. So on day 1 the plan bills <span className="tabular-nums">{fmt(day1.dispatched.real_l)} L</span>{" "}
          against those orders — <span className="tabular-nums">{fmt(day1.shipped_l)} L</span> in all, the rest for{" "}
          <span className="text-sky-300">expected orders nobody has placed yet</span>. After billing, the truck leaves{" "}
          {O.storage.invoice_truck_lag_days} days later.
        </p>
      </Section>

      {/* ---------------- what customers want ---------------- */}
      <Section
        title="What customers want this month"
        right={<span className="text-xs text-zinc-500">confirmed orders and expected orders — kept apart</span>}
      >
        <OverviewDemand demand={O.demand} ecomRule={rule(H, "ecom-spread")} />
      </Section>

      {/* ---------------- where the numbers come from ---------------- */}
      <p className="text-[11px] text-zinc-600 mt-8 leading-relaxed">
        Where these numbers come from: the target is this month&rsquo;s plan ({O.plan.skus} products). Stock is SAP,
        counted on {dlabel(O.meta.frozen)} evening. Everything after that is the computer plan, tested on August.{" "}
        {wa.messages} messages the computer wrote for {wa.threads} people were{" "}
        <span className="text-zinc-400">NOT sent</span> — {wa.replies} replies.{" "}
        <Link href="/whatsapp" className="hover:underline">
          Messages (not sent) →
        </Link>
      </p>
    </div>
  );
}

// A named rule from the honesty file — the page renders its own plain words, never the rule text.
function rule(H: ReturnType<typeof getHonesty>, id: string) {
  return H.label_rules.find((r) => r.id === id)?.rule;
}
