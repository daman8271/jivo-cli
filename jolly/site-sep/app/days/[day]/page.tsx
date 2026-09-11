import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getDay, getAllDays, getSpine, getOverview, getStorage, getLoops, getMaterials, getLines, fmt, money, dlabel, plural, slotNames,
} from "../../../lib/data";
import { LINES } from "../../../lib/types";
import type { Blocked, DayDetail, LoopChain as Chain } from "../../../lib/types";
import { Card, Section, Pill } from "../../../components/Card";
import SimBadge from "../../../components/SimBadge";
import {
  DayStat, DayStrip, DayScroll, DayEmpty, DayWaterfall, TH, THR, TD, NUM,
  eventWords, channelWords, weekWords, materialWords, hoursWords, oilChangeWords, itemNames, plainFact,
} from "../../../components/DayBits";
import { LoopPipeline, LoopDayRef, spineDateMap, chainForBinder } from "../../../components/LoopChain";

export const dynamicParams = false;

// The full date under the heading, the way it is said: "3 September 2026", not "2026-09-03".
const fullDate = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });

export function generateStaticParams() {
  return getSpine().map((d) => ({ day: String(d.n) }));
}

export async function generateMetadata({ params }: { params: Promise<{ day: string }> }) {
  const n = Number((await params).day);
  const total = getSpine().length;
  if (!Number.isInteger(n) || n < 1 || n > total) return { title: "Day" };
  const d = getDay(n);
  return {
    title: `Day ${n} — ${d.weekday} ${dlabel(d.date)}`,
    description: `Day ${n} of ${total} of the September plan (${d.weekday} ${dlabel(d.date)}) — what the computer plans to run, bill and store. A plan, not a record: nothing here has happened.`,
  };
}

export default async function DayPage({ params }: { params: Promise<{ day: string }> }) {
  const spine = getSpine();
  const n = Number((await params).day);
  if (!Number.isInteger(n) || n < 1 || n > spine.length) notFound();

  const d: DayDetail = getDay(n);
  const o = getOverview();
  const stg = getStorage();
  const loops = getLoops();
  const map = spineDateMap(spine);
  const names = itemNames(getAllDays(), loops.chains);
  const stockDate = dlabel(o.meta.frozen);
  const lagDays = stg.invoice_truck_lag_days;

  // numbers the honesty footer quotes — all from data/, none typed here
  const facts = {
    stockDate,
    products: o.plan.skus,
    leadOil: getMaterials().lead_days.oil,
    leadPack: getMaterials().lead_days.packaging,
    lagDays,
    efficiency: getLines().efficiency,
    expectedPct: o.demand.forecast_share_litres_pct,
    observedSlots: slotNames(getLines(), "observed"),
    derivedSlots: slotNames(getLines(), "derived"),
  };

  // ---- godown: start of day -> +made -> -trucks left -> end of day ------------------
  const startStock = n === 1 ? o.opening.fg_litres + o.opening.standing_l : getDay(n - 1).storage.physical_l;
  const trucked = Math.max(0, Math.round(startStock + d.made_litres - d.storage.physical_l));

  // ---- what ran ------------------------------------------------------------------
  const byLine = LINES.map((line) => ({ line, hours: d.line_hours[line] ?? 0, runs: d.runs.filter((r) => r.line === line) }));
  const linesRunning = byLine.filter((l) => l.runs.length > 0).length;
  const flushMin = d.runs.reduce((a, r) => a + r.flush_min, 0);

  // ---- what was stuck: fold repeat tries on the same missing item ----------------
  const blockedMap = new Map<string, Blocked & { times: number }>();
  for (const b of d.blocked) {
    const k = `${b.code}|${b.binder}`;
    const e = blockedMap.get(k);
    if (e) e.times += 1;
    else blockedMap.set(k, { ...b, times: 1 });
  }
  const blocked = [...blockedMap.values()].sort((a, b) => b.want - a.want);
  const blockedProducts = new Set(blocked.map((b) => b.code)).size;

  // ---- events, folded into their sections (raw kinds never reach the page) --------
  const ev = <T,>(kind: string): T[] => d.events.filter((e) => e.kind === kind) as unknown as T[];
  const bigPO = new Set(ev<{ docnum: unknown; code: unknown }>("BIG_PO").map((e) => `${e.docnum}|${e.code}`));
  const wallItems = (kind: string) => {
    const seen = new Set<string>();
    for (const e of ev<{ items?: { code: string; sku: string }[] }>(kind)) for (const it of e.items ?? []) seen.add(`${it.code}|${it.sku}`);
    return seen.size;
  };
  const oilWalls = wallItems("OIL_SHORT");
  const packWalls = wallItems("PACKAGING_ZERO");
  const idle = ev<{ util?: number; blocked?: number }>("LINES_IDLE")[0];
  const slowed = d.decisions.some((dc) => dc.kind === "STORAGE_THROTTLE") || ev("STORAGE_THROTTLE").length > 0;

  // ---- the chain: stuck -> ordered -> arrived -> running, steps that fall today ----
  const chainKey = (c: Chain) => `${c.code}|${c.ordered_day}`;
  const todays = new Map<string, { chain: Chain; roles: string[] }>();
  const addRole = (c: Chain, role: string) => {
    const e = todays.get(chainKey(c));
    if (e) e.roles.push(role);
    else todays.set(chainKey(c), { chain: c, roles: [role] });
  };
  for (const c of loops.chains) {
    if (c.ordered_day === d.date) addRole(c, "ordered today");
    if (c.unblocked_day === d.date) addRole(c, "arrives today — can run again");
    if (c.first_run_after_unblock?.day === d.date) addRole(c, "runs again today");
  }
  const todaysChains = [...todays.values()];
  const orderedTodayByCode = new Map(loops.chains.filter((c) => c.ordered_day === d.date).map((c) => [c.code, c]));
  const unblockedTodayCodes = new Set(loops.chains.filter((c) => c.unblocked_day === d.date).map((c) => c.code));
  const runClosesLoop = new Map(loops.chains.filter((c) => c.first_run_after_unblock?.day === d.date).map((c) => [c.first_run_after_unblock!.code, c]));

  // ---- sums (computed from the rows shown) ---------------------------------------
  const realPieces = d.orders_real.reduce((a, r) => a + r.pieces, 0);
  const realValue = d.orders_real.reduce((a, r) => a + r.value, 0);
  const fcstPieces = d.orders_forecast.reduce((a, r) => a + r.pieces, 0);
  const fcstValue = d.orders_forecast.reduce((a, r) => a + r.value, 0);
  const dispRealL = d.dispatched_real.reduce((a, r) => a + r.litres, 0);
  const dispFcstL = d.dispatched_forecast.reduce((a, r) => a + r.litres, 0);
  // one bill line = one product on one bill (a customer's, or an expected order's)
  const billLines = d.dispatched_real.length + d.dispatched_forecast.length;
  const lagWord = `${lagDays} ${plural(lagDays, "day", "days")}`;
  const received = [...d.received].sort((a, b) => b.qty - a.qty);
  const bought = [...d.bought].sort((a, b) => b.qty - a.qty);
  const ordersReal = [...d.orders_real].sort((a, b) => b.value - a.value);
  const ordersForecast = [...d.orders_forecast].sort((a, b) => b.value - a.value);
  const dispatchedReal = [...d.dispatched_real].sort((a, b) => b.litres - a.litres);
  const dispatchedForecast = [...d.dispatched_forecast].sort((a, b) => b.litres - a.litres);

  const s = d.storage;
  const full = s.pct >= 95;
  const roof = s.pct >= 100;

  const NavBtns = (
    <div className="flex items-center gap-2 text-sm">
      {n > 1 ? (
        <Link href={`/days/${n - 1}`} className="rounded-md border border-zinc-800 px-3 py-1.5 text-zinc-300 hover:bg-zinc-800">← Day {n - 1}</Link>
      ) : (
        <span className="rounded-md border border-zinc-900 px-3 py-1.5 text-zinc-700">← month starts</span>
      )}
      {n < spine.length ? (
        <Link href={`/days/${n + 1}`} className="rounded-md border border-zinc-800 px-3 py-1.5 text-zinc-300 hover:bg-zinc-800">Day {n + 1} →</Link>
      ) : (
        <span className="rounded-md border border-zinc-900 px-3 py-1.5 text-zinc-700">month ends →</span>
      )}
    </div>
  );

  return (
    <div>
      {/* ---------------------------------------------------------------- header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-tight">
              Day {n} <span className="text-zinc-500">—</span> {d.weekday} {dlabel(d.date)}
            </h1>
            <SimBadge kind="plan" />
            {d.working ? <Pill tone="green">working day</Pill> : <Pill>factory closed — {d.weekday}</Pill>}
            {roof ? <Pill tone="red">{slowed ? "godown full — production slowed" : "godown full"}</Pill> : full ? <Pill tone="amber">godown almost full</Pill> : null}
          </div>
          <div className="mt-1 text-sm text-zinc-500">{fullDate(d.date)}</div>
        </div>
        {NavBtns}
      </div>

      {/* --------------------------------------------------- real vs computer plan */}
      <div className="mt-4 rounded-xl border border-violet-500/25 bg-violet-500/5 px-4 py-3 text-sm text-violet-100/90">
        {n === 1 ? (
          <>
            <span className="font-semibold">Real:</span> the stock at the start of the day (from SAP).{" "}
            <span className="font-semibold">Computer plan:</span> everything below.
          </>
        ) : (
          <>
            <span className="font-semibold">Real:</span> the stock counted on {stockDate} (from SAP).{" "}
            <span className="font-semibold">Computer plan:</span> everything below — including the stock at the start of
            today, which is what the computer expected at the end of{" "}
            <Link href={`/days/${n - 1}`} className="text-amber-400 hover:underline">day {n - 1}</Link>. Nothing on this
            page has happened.{" "}
            <Link href="/days/1" className="text-violet-300 hover:underline">Start at day 1 →</Link>
          </>
        )}
      </div>

      <div className="mt-4">
        <DayStrip current={n} days={spine} />
        <div className="mt-2 text-xs text-zinc-600">All {spine.length} days of the plan. Dim squares are Sundays — factory closed. A red ring marks a day the godown is full.</div>
      </div>

      {/* ------------------------------------------------------------- six numbers */}
      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <DayStat label="Made" value={fmt(d.made_litres)} unit="L" sub={d.working ? `${d.runs.length} runs on ${linesRunning} of ${LINES.length} machines` : "factory closed"} />
        <DayStat label="Worth" value={money(d.made_value_rs)} sub="value of today's fill" />
        <DayStat label="Billed" value={fmt(d.shipped_litres)} unit="L" sub={`${fmt(billLines)} ${plural(billLines, "bill line", "bill lines")} — the trucks leave ${lagWord} after billing`} />
        <DayStat label="Machines busy" value={`${d.line_util}`} unit="%" sub={`${d.flushes} oil changes · ${hoursWords(flushMin / 60)} spent changing oil`} />
        <DayStat label="Godown full" value={`${s.pct}`} unit="%" tone={full ? "text-red-400" : ""} sub={`of the limit — ${fmt(s.ceiling_l)} L, Daman's number, not measured`} />
        <DayStat label="Space left" value={fmt(s.headroom_l)} unit="L" tone={full ? "text-red-400" : ""} sub="in the godown at the end of the day" />
      </div>

      {/* ----------------------------------------------------- the month so far */}
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <DayStat label="Still to make this month" value={fmt(d.book.plan_left_l)} unit="L" sub="of this month's target, after today's runs — product by product" />
        <DayStat label="Confirmed orders pending" value={fmt(d.open_real_l_computed)} unit="L" sub={`customers have ordered, not yet billed — counted from ${stockDate}, including the orders already pending then`} />
        <DayStat label="Expected — not ordered yet" value={fmt(d.book.forecast_open_l)} unit="L" badge={<Pill tone="blue">our guess</Pill>} sub="what the plan expects customers to still order this month" />
      </div>
      <div className="mt-2 text-[11px] leading-relaxed text-zinc-600">
        Two more counters from the planner, with a warning. Total ordered since day 1: {money(d.book.po_cumulative_value_rs)} —
        that is everything ordered this month, not what is still pending. The planner&apos;s own &quot;still to send&quot;
        counter: {fmt(d.book.po_open_l_raw)} L — it counts too much, so use the confirmed-orders figure above.
      </div>

      {/* --------------------------------------------------- what runs, per machine */}
      <Section
        title="What runs today — machine by machine, in order"
        right={<span className="text-xs text-zinc-500">{d.runs.length} runs · {fmt(d.made_litres)} L · {money(d.made_value_rs)} · {d.flushes} oil changes</span>}
      >
        {idle ? (
          <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
            {eventWords("LINES_IDLE")} today. Machines busy only {String(idle.util)}%. {String(idle.blocked)} products stuck.
            The hours were there — the material or the godown space was not.
          </div>
        ) : null}
        {!d.working ? (
          <DayEmpty>Factory closed — {d.weekday}. Nothing runs.</DayEmpty>
        ) : (
          <div className="space-y-3">
            {byLine.map((l) => {
              const changes = l.runs.filter((r) => r.flush_min > 0).length;
              return (
                <div key={l.line} className="rounded-xl border border-zinc-800 bg-zinc-900/40">
                  <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-zinc-800 px-3 py-2">
                    <div className="font-medium">{l.line}</div>
                    <div className="text-xs tabular-nums text-zinc-500">
                      {l.runs.length === 0
                        ? "no runs today"
                        : `${l.runs.length} ${plural(l.runs.length, "run", "runs")} · ${hoursWords(l.hours)} · ${fmt(l.runs.reduce((a, r) => a + r.litres, 0))} L · ${changes} oil ${plural(changes, "change", "changes")}`}
                    </div>
                  </div>
                  {l.runs.length === 0 ? (
                    <div className="px-3 py-3 text-sm text-zinc-600">nothing planned on this machine today</div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr>
                            <th className={`${TH} w-8`}>#</th>
                            <th className={TH}>Before this run</th>
                            <th className={TH}>What fills</th>
                            <th className={TH}>Oil</th>
                            <th className={THR}>Pieces</th>
                            <th className={THR}>Litres</th>
                            <th className={THR}>Time</th>
                            <th className={THR}>Earns per hour</th>
                            <th className={TH}>Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {l.runs.map((r, i) => {
                            const closes = runClosesLoop.get(r.code);
                            return (
                              <tr key={`${r.code}-${i}`} className="hover:bg-zinc-900/60">
                                <td className={`${TD} text-zinc-600 tabular-nums`}>{i + 1}</td>
                                <td className={`${TD} whitespace-nowrap`}>
                                  {r.flush_min > 0 ? (
                                    <>
                                      <span className="text-amber-300/90 text-xs">{oilChangeWords(r.flush_min)}</span>
                                      <span className="ml-1 text-[10px] text-zinc-600">({r.flush_min} min)</span>
                                    </>
                                  ) : (
                                    <span className="text-xs text-zinc-600">no oil change</span>
                                  )}
                                </td>
                                <td className={`${TD} text-zinc-200`}>{r.sku}<span className="ml-2 text-xs text-zinc-600">{r.code}</span></td>
                                <td className={`${TD} text-xs text-zinc-400 whitespace-nowrap`}>
                                  {r.oil ? (names[r.oil] ?? r.oil) : "—"}
                                  {r.oil && names[r.oil] ? <span className="ml-1 text-zinc-600">{r.oil}</span> : null}
                                </td>
                                <td className={`${TD} ${NUM}`}>{fmt(r.pieces)}</td>
                                <td className={`${TD} ${NUM}`}>{fmt(r.litres)} L</td>
                                <td className={`${TD} ${NUM} text-zinc-400`}>{hoursWords(r.hours)}</td>
                                <td className={`${TD} ${NUM} text-zinc-300`}>{money(r.rs_per_hour)}</td>
                                <td className={TD}>
                                  <span className="flex flex-wrap gap-1">
                                    {r.head === "PREMIUM" ? <Pill tone="amber">premium</Pill> : null}
                                    {r.po_backed ? <Pill tone="green">has a customer order</Pill> : null}
                                    {closes ? (
                                      <Link href={`/days/${map[closes.ordered_day] ?? 1}`}>
                                        <Pill tone="violet">running again — was stuck, ordered day {map[closes.ordered_day] ?? dlabel(closes.ordered_day)}</Pill>
                                      </Link>
                                    ) : null}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
            <div className="text-xs text-zinc-500">
              Runs are in the order the planner runs them. An oil change means washing the machine with the next oil,
              then cleaning. Machines are planned at {Math.round(facts.efficiency * 100)}% of their listed speed — that is
              what August showed, not a fault.
            </div>
          </div>
        )}
      </Section>

      {/* ------------------------------------------------------------ arrived today */}
      <Section
        title="Arrived today"
        right={<span className="text-xs text-zinc-500">{received.length} {plural(received.length, "item", "items")} — POs reaching the gate</span>}
      >
        <p className="mb-3 max-w-4xl text-xs text-zinc-500">
          Arrival dates are our guess: each item lands when its usual delivery time runs out (oil {facts.leadOil} days,
          packing material {facts.leadPack} days). Every PO that was open on {stockDate} was already late — the plan
          spreads those across the first working week.
        </p>
        {received.length === 0 ? (
          <DayEmpty>Nothing arrives today.</DayEmpty>
        ) : (
          <DayScroll max="max-h-[22rem]">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className={TH}>Item</th>
                  <th className={TH}>What it is</th>
                  <th className={THR}>Quantity</th>
                  <th className={TH}>Note</th>
                </tr>
              </thead>
              <tbody>
                {received.map((r, i) => (
                  <tr key={`${r.code}-${i}`} className="hover:bg-zinc-900/60">
                    <td className={`${TD} text-zinc-300`}>{r.name}<span className="ml-2 text-xs text-zinc-600">{r.code}</span></td>
                    <td className={TD}><Pill tone={r.kind === "OIL" ? "red" : "zinc"}>{materialWords(r.code, r.name)}</Pill></td>
                    <td className={`${TD} ${NUM}`}>{fmt(r.qty)}</td>
                    <td className={TD}>
                      {unblockedTodayCodes.has(r.code) ? <Pill tone="green">a stuck product can run again — see the chain below</Pill> : <span className="text-xs text-zinc-600">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </DayScroll>
        )}
      </Section>

      {/* --------------------------------------------------------- new orders today */}
      <Section
        title="New orders today"
        right={
          <span className="text-xs text-zinc-500">
            {d.news.real_pos_entering} confirmed · {d.news.forecast_rows} expected — not ordered yet
          </span>
        }
      >
        <p className="mb-3 max-w-4xl text-xs text-zinc-500">
          <span className="text-zinc-300">Confirmed</span> orders are real: a customer has ordered them (from SAP, on the date
          they were promised). <span className="text-sky-300">Expected</span> orders are this month&apos;s target given a
          date — nobody has ordered them yet. They are always blue.
        </p>

        {n === 1 ? (
          <div className="mb-4 rounded-xl border border-emerald-500/25 bg-emerald-500/5 p-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <Pill tone="green">real — from SAP</Pill>
              <span className="font-medium text-emerald-200">Day 1 starts with a pile of orders. The pile is real.</span>
            </div>
            <div className="mt-1.5 text-xs text-zinc-400">
              <span className="tabular-nums">{o.opening.plan_sku_backlog_docs}</span> orders for this month&apos;s{" "}
              {o.plan.skus} products were open in SAP on {stockDate}.{" "}
              <span className="tabular-nums">{o.opening.plan_sku_backlog_docs_overdue}</span> of them were already late.
              Most come in today; the rest come in on their promised dates. Together they are worth{" "}
              {money(o.opening.backlog_value_rs)} across {fmt(o.opening.backlog_pieces)} pieces.
            </div>
          </div>
        ) : null}

        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <div className="text-sm font-medium text-zinc-300">Confirmed orders <Pill tone="green">real — from SAP</Pill></div>
              <div className="text-xs text-zinc-500">{d.orders_real.length} {plural(d.orders_real.length, "order line", "order lines")} · {fmt(realPieces)} pcs · {money(realValue)}</div>
            </div>
            {ordersReal.length === 0 ? (
              <DayEmpty>{d.working ? "No confirmed orders come in today." : "Factory closed — no orders come in."}</DayEmpty>
            ) : (
              <DayScroll max="max-h-[26rem]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Customer</th>
                      <th className={TH}>Type</th>
                      <th className={TH}>Product</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Worth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordersReal.map((r, i) => (
                      <tr key={`${r.docnum}-${r.code}-${i}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-300`}>
                          {r.customer}
                          {bigPO.has(`${r.docnum}|${r.code}`) ? <span className="ml-2"><Pill tone="amber">{eventWords("BIG_PO")}</Pill></span> : null}
                        </td>
                        <td className={TD}><Pill tone={r.channel === "TRADE" ? "zinc" : "blue"}>{channelWords(r.channel)}</Pill></td>
                        <td className={`${TD} text-zinc-400`}>{r.sku ?? r.code}</td>
                        <td className={`${TD} ${NUM}`}>{fmt(r.pieces)}</td>
                        <td className={`${TD} ${NUM} text-zinc-300`}>{money(r.value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DayScroll>
            )}
          </div>

          <div>
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <div className="text-sm font-medium text-sky-200">Expected — not ordered yet <Pill tone="blue">our guess</Pill></div>
              <div className="text-xs text-sky-300/60">{d.orders_forecast.length} {plural(d.orders_forecast.length, "order line", "order lines")} · {fmt(fcstPieces)} pcs · {money(fcstValue)}</div>
            </div>
            {ordersForecast.length === 0 ? (
              <DayEmpty>{d.working ? "Nothing expected today." : "Factory closed — nothing expected today."}</DayEmpty>
            ) : (
              <DayScroll max="max-h-[26rem]" tint="border-sky-500/25 bg-sky-500/[0.04]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>For which week</th>
                      <th className={TH}>Product</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Worth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordersForecast.map((r, i) => (
                      <tr key={`${r.docnum}-${i}`} className="text-sky-100/80 hover:bg-sky-500/5">
                        <td className={`${TD}`}>
                          <span className="text-xs text-sky-300/80">{weekWords(r.docnum)}</span>
                          <div className="text-[10px] text-sky-300/50">{channelWords(r.channel)}</div>
                        </td>
                        <td className={`${TD} text-sky-100/70`}>{r.sku ?? r.code}</td>
                        <td className={`${TD} ${NUM}`}>{fmt(r.pieces)}</td>
                        <td className={`${TD} ${NUM}`}>{money(r.value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DayScroll>
            )}
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------- stuck today, and why */}
      <Section
        title="Stuck today — and why"
        right={
          <span className="text-xs text-zinc-500">
            {blockedProducts} {plural(blockedProducts, "product", "products")} stuck
            {oilWalls > 0 || packWalls > 0 ? ` · ${oilWalls} ${eventWords("OIL_SHORT")} · ${packWalls} ${eventWords("PACKAGING_ZERO")}` : ""}
          </span>
        }
      >
        {blocked.length === 0 ? (
          <DayEmpty>{d.working ? "Nothing was stuck today." : "Factory closed — nothing was planned, so nothing was stuck."}</DayEmpty>
        ) : (
          <>
            <DayScroll max="max-h-[28rem]">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className={TH}>Product the plan wanted</th>
                    <th className={THR}>Pieces wanted</th>
                    <th className={TH}>What is missing</th>
                    <th className={THR}>Tried</th>
                    <th className={TH}>Where it stands</th>
                  </tr>
                </thead>
                <tbody>
                  {blocked.map((b) => {
                    const lk = chainForBinder(loops.chains, b.binder, d.date);
                    const isOil = b.binder.startsWith("RM");
                    return (
                      <tr key={`${b.code}-${b.binder}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-200`}>{b.sku}<span className="ml-2 text-xs text-zinc-600">{b.code}</span></td>
                        <td className={`${TD} ${NUM}`}>{fmt(b.want)}</td>
                        <td className={TD}>
                          <span className="mr-2"><Pill tone={isOil ? "red" : "zinc"}>{materialWords(b.binder, b.binder_name)}</Pill></span>
                          <span className="text-zinc-300">{b.binder_name}</span>
                          <span className="ml-2 text-xs text-zinc-600">{b.binder}</span>
                        </td>
                        <td className={`${TD} ${NUM} text-zinc-500`}>{b.times}</td>
                        <td className={`${TD} text-xs`}>
                          {lk ? (
                            lk.state === "on-order" ? (
                              <span className="text-amber-300/90">
                                ordered <LoopDayRef date={lk.chain.ordered_day} map={map} /> → arrives <LoopDayRef date={lk.chain.unblocked_day ?? lk.chain.lands} map={map} />
                              </span>
                            ) : lk.state === "ordered-later" ? (
                              <span className="text-zinc-400">
                                the planner orders it <LoopDayRef date={lk.chain.ordered_day} map={map} />
                              </span>
                            ) : (
                              <span className="text-emerald-300/80">
                                arrived <LoopDayRef date={lk.chain.unblocked_day ?? lk.chain.lands} map={map} /> — finished again
                              </span>
                            )
                          ) : (
                            <span className="text-zinc-600">not ordered in this plan</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </DayScroll>
            <div className="mt-2 text-xs text-zinc-500">
              The planner tries a stuck product again and again in a day — &quot;tried&quot; counts the tries. The last
              column follows the missing item: stuck → ordered → arrived.
            </div>
          </>
        )}
      </Section>

      {/* ------------------------------------------------------------ godown today */}
      <Section
        title="Godown today"
        right={<Link href="/storage" className="text-xs text-amber-400 hover:underline">the whole month&apos;s godown →</Link>}
      >
        <p className={`mb-3 max-w-4xl text-base ${roof ? "text-red-300" : full ? "text-amber-200" : "text-zinc-200"}`}>
          {roof ? (
            <>
              Godown full{slowed ? " — production slowed" : ""}. {fmt(s.physical_l)} L inside, limit {fmt(s.ceiling_l)} L.
            </>
          ) : full ? (
            <>Godown almost full — {s.pct}%. Space left: {fmt(s.headroom_l)} L.</>
          ) : (
            <>Godown {s.pct}% full. Space left: {fmt(s.headroom_l)} L.</>
          )}{" "}
          <span className="text-sm text-zinc-400">
            Of the stock inside, {fmt(s.invoiced_not_trucked_l)} L is billed but the truck has not left yet. Free stock:{" "}
            {fmt(s.fg_in_godown_l)} L. The limit is Daman&apos;s number, not measured.
          </span>
        </p>
        <DayWaterfall
          start={startStock}
          startMeasured={n === 1}
          startCaption={
            n === 1 ? (
              <>
                The starting stock is the one real bar on this page <Pill tone="green">real — from SAP, {stockDate}</Pill>{" "}
                <span className="text-amber-300/80">
                  Stock billed on or before {stockDate} whose truck had not left is not counted — so the godown is really fuller than this.
                </span>
              </>
            ) : (
              <>
                The starting stock is what the computer expected at the end of{" "}
                <Link href={`/days/${n - 1}`} className="text-amber-400 hover:underline">day {n - 1}</Link> — computer plan, not a count.
              </>
            )
          }
          startSub={n === 1 ? `counted ${stockDate}` : `day ${n - 1}'s end, computer plan`}
          made={d.made_litres}
          trucked={trucked}
          s={s}
        />
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Card title="Oil used today" value={`${fmt(d.oil_used_l)} L`} sub="loose oil the runs used — the bulk tanks are outside the godown" />
          <div className="lg:col-span-2">
            {d.decisions.length === 0 ? (
              <DayEmpty>Godown had space today.</DayEmpty>
            ) : (
              <div className="space-y-2">
                {d.decisions.map((dc, i) => (
                  <div key={`${dc.kind}-${i}`} className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3" title={dc.text}>
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone="amber">{eventWords(dc.kind)}</Pill>
                      <span className="text-[11px] text-violet-300/70">computer plan</span>
                    </div>
                    <div className="mt-1.5 text-sm text-amber-100">
                      {dc.kind === "STORAGE_THROTTLE"
                        ? "The planner slowed production today so the godown would not overflow."
                        : dc.text}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------------ billed today */}
      <Section
        title="Billed today"
        right={<span className="text-xs text-zinc-500">{fmt(d.shipped_litres)} L — the trucks leave {lagWord} after billing</span>}
      >
        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <div className="text-sm font-medium text-zinc-300">Against confirmed orders</div>
              <div className="text-xs text-zinc-500">{dispatchedReal.length} {plural(dispatchedReal.length, "bill line", "bill lines")} · {fmt(dispRealL)} L</div>
            </div>
            {dispatchedReal.length === 0 ? (
              <DayEmpty>Nothing billed against confirmed orders today.</DayEmpty>
            ) : (
              <DayScroll max="max-h-[24rem]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Customer</th>
                      <th className={TH}>Product</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Litres</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dispatchedReal.map((x, i) => (
                      <tr key={`${x.docnum}-${x.sku}-${i}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-300`}>{x.customer}<span className="ml-2"><Pill tone={x.channel === "TRADE" ? "zinc" : "blue"}>{channelWords(x.channel)}</Pill></span></td>
                        <td className={`${TD} text-zinc-400`}>{x.sku}</td>
                        <td className={`${TD} ${NUM}`}>{fmt(x.pieces)}</td>
                        <td className={`${TD} ${NUM} text-zinc-200`}>{fmt(x.litres)} L</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DayScroll>
            )}
          </div>
          <div>
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <div className="text-sm font-medium text-sky-200">Against expected orders <Pill tone="blue">not ordered yet — our guess</Pill></div>
              <div className="text-xs text-sky-300/60">{dispatchedForecast.length} {plural(dispatchedForecast.length, "bill line", "bill lines")} · {fmt(dispFcstL)} L</div>
            </div>
            {dispatchedForecast.length === 0 ? (
              <DayEmpty>Nothing billed against expected orders today.</DayEmpty>
            ) : (
              <DayScroll max="max-h-[24rem]" tint="border-sky-500/25 bg-sky-500/[0.04]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>For which week</th>
                      <th className={TH}>Product</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Litres</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dispatchedForecast.map((x, i) => (
                      <tr key={`${x.docnum}-${x.sku}-${i}`} className="text-sky-100/80 hover:bg-sky-500/5">
                        <td className={TD}><span className="text-xs text-sky-300/80">{weekWords(x.docnum)}</span></td>
                        <td className={`${TD} text-sky-100/70`}>{x.sku}</td>
                        <td className={`${TD} ${NUM}`}>{fmt(x.pieces)}</td>
                        <td className={`${TD} ${NUM}`}>{fmt(x.litres)} L</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DayScroll>
            )}
          </div>
        </div>
      </Section>

      {/* --------------------------------------- stuck → ordered → arrived → running */}
      <Section
        title="Stuck → ordered → arrived → running"
        right={<span className="text-xs text-zinc-500">how one missing item moves through the month — each step links to its day</span>}
      >
        {todaysChains.length === 0 ? (
          <DayEmpty>
            No stuck item is ordered or arrives today. {d.waiting_on.length > 0 ? "Some are still on the way — see below." : "Nothing ordered, nothing arriving, nothing freed."}
          </DayEmpty>
        ) : (
          <div className="space-y-3">
            {todaysChains.map(({ chain, roles }) => (
              <LoopPipeline key={`${chain.code}-${chain.ordered_day}`} chain={chain} today={d.date} map={map} roles={roles} />
            ))}
          </div>
        )}

        {d.waiting_on.length > 0 ? (
          <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-900/30 p-3">
            <div className="text-xs uppercase tracking-wider text-zinc-500">Still waiting for these at the end of the day</div>
            <ul className="mt-2 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
              {d.waiting_on.map((w) => (
                <li key={`${w.code}-${w.since}`} className="flex flex-wrap items-baseline gap-x-2">
                  <span className="text-zinc-300">{w.name}</span>
                  <span className="text-xs text-zinc-600">{w.code}</span>
                  <span className="text-xs text-zinc-500">stuck since <LoopDayRef date={w.since} map={map} /></span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mt-4">
          <div className="mb-2 flex items-baseline justify-between gap-2">
            <div className="text-sm font-medium text-zinc-300">What the planner orders today</div>
            <div className="text-xs text-zinc-500">{bought.length} {plural(bought.length, "item", "items")} — orange rows free a stuck product</div>
          </div>
          {bought.length === 0 ? (
            <DayEmpty>The planner orders nothing today.</DayEmpty>
          ) : (
            <DayScroll max="max-h-[24rem]">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className={TH}>Item</th>
                    <th className={THR}>Quantity</th>
                    <th className={TH}>Arrives</th>
                    <th className={TH}>Why</th>
                  </tr>
                </thead>
                <tbody>
                  {bought.map((b, i) => {
                    const ch = orderedTodayByCode.get(b.code);
                    return (
                      <tr key={`${b.code}-${i}`} className={ch ? "bg-amber-500/[0.06] hover:bg-amber-500/10" : "hover:bg-zinc-900/60"}>
                        <td className={`${TD} text-zinc-300`}>{b.name}<span className="ml-2 text-xs text-zinc-600">{b.code}</span></td>
                        <td className={`${TD} ${NUM}`}>{fmt(b.qty)} <span className="text-zinc-500">{b.uom.toLowerCase()}</span></td>
                        <td className={`${TD} whitespace-nowrap text-xs`}><LoopDayRef date={b.lands} map={map} /></td>
                        <td className={`${TD} text-xs`}>
                          {ch ? (
                            <span className="text-amber-300/90">
                              {ch.fg_codes_blocked.length > 0
                                ? `frees ${ch.fg_codes_blocked.length} stuck ${plural(ch.fg_codes_blocked.length, "product", "products")} — see above`
                                : "ran out — ordered so it can run again, see above"}
                            </span>
                          ) : (
                            <span className="text-zinc-600">buying ahead, so stock does not run out</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </DayScroll>
          )}
        </div>
      </Section>

      {/* ------------------------------------------------------------------ honesty */}
      <div className="mt-10 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
        <div className="text-xs uppercase tracking-wider text-zinc-500">What is real on this page, and what is our guess</div>
        <div className="mt-3 grid gap-4 md:grid-cols-2">
          <div>
            <div className="mb-2 text-sm text-emerald-300">Real — counted in SAP or the factory app on {stockDate}</div>
            <div className="flex flex-wrap gap-1.5">{d.honesty.measured.map((x) => <Pill key={x} tone="green">{plainFact(x, facts)}</Pill>)}</div>
          </div>
          <div>
            <div className="mb-2 text-sm text-amber-300">Our guess — not measured</div>
            <div className="flex flex-wrap gap-1.5">{d.honesty.assumed.map((x) => <Pill key={x} tone="amber">{plainFact(x, facts)}</Pill>)}</div>
          </div>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <Link href="/days" className="rounded-md border border-zinc-800 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-800">← all {spine.length} days</Link>
        {NavBtns}
      </div>
    </div>
  );
}
