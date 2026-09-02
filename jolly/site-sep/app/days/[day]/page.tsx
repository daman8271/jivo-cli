import Link from "next/link";
import { notFound } from "next/navigation";
import { getDay, getSpine, getOverview, getStorage, getLoops, getHonesty, fmt, money, dlabel } from "../../../lib/data";
import { LINES } from "../../../lib/types";
import type { Blocked, DayDetail, LoopChain as Chain } from "../../../lib/types";
import { Card, Section, Pill } from "../../../components/Card";
import SimBadge from "../../../components/SimBadge";
import { DayStat, DayStrip, DayScroll, DayEmpty, DayWaterfall, TH, THR, TD, NUM } from "../../../components/DayBits";
import { LoopPipeline, LoopDayRef, spineDateMap, chainForBinder } from "../../../components/LoopChain";

export const dynamicParams = false;

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
    description: `Planned day ${n} of ${total} (${d.weekday} ${dlabel(d.date)}) — what the simulator would run, ship and store. A forward plan, not a record.`,
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

  // ---- storage waterfall: opening -> +made -> -gated-out -> closing --------------
  const opening = n === 1 ? o.opening.fg_litres + o.opening.standing_l : getDay(n - 1).storage.physical_l;
  const gated = Math.max(0, Math.round(opening + d.made_litres - d.storage.physical_l));

  // ---- what ran ------------------------------------------------------------------
  const byLine = LINES.map((line) => ({ line, hours: d.line_hours[line] ?? 0, runs: d.runs.filter((r) => r.line === line) }));
  const linesRunning = byLine.filter((l) => l.runs.length > 0).length;
  const flushMin = d.runs.reduce((a, r) => a + r.flush_min, 0);

  // ---- what didn't: fold repeat hits on the same wall ----------------------------
  const blockedMap = new Map<string, Blocked & { times: number }>();
  for (const b of d.blocked) {
    const k = `${b.code}|${b.binder}`;
    const e = blockedMap.get(k);
    if (e) e.times += 1;
    else blockedMap.set(k, { ...b, times: 1 });
  }
  const blocked = [...blockedMap.values()].sort((a, b) => b.want - a.want);
  const blockedProducts = new Set(blocked.map((b) => b.code)).size;

  // ---- events, folded into their sections ----------------------------------------
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

  // ---- the loop: chains this day is living through -------------------------------
  const chainKey = (c: Chain) => `${c.code}|${c.ordered_day}`;
  const todays = new Map<string, { chain: Chain; roles: string[] }>();
  const addRole = (c: Chain, role: string) => {
    const e = todays.get(chainKey(c));
    if (e) e.roles.push(role);
    else todays.set(chainKey(c), { chain: c, roles: [role] });
  };
  for (const c of loops.chains) {
    if (c.ordered_day === d.date) addRole(c, "ordered today");
    if (c.unblocked_day === d.date) addRole(c, "lands & unblocks today");
    if (c.first_run_after_unblock?.day === d.date) addRole(c, "loop closes today");
  }
  const todaysChains = [...todays.values()];
  const orderedTodayByCode = new Map(loops.chains.filter((c) => c.ordered_day === d.date).map((c) => [c.code, c]));
  const unblockedTodayCodes = new Set(loops.chains.filter((c) => c.unblocked_day === d.date).map((c) => c.code));
  const runClosesLoop = new Map(loops.chains.filter((c) => c.first_run_after_unblock?.day === d.date).map((c) => [c.first_run_after_unblock!.code, c]));

  // ---- news sums (computed from the rows shown) ----------------------------------
  const realPieces = d.orders_real.reduce((a, r) => a + r.pieces, 0);
  const realValue = d.orders_real.reduce((a, r) => a + r.value, 0);
  const fcstPieces = d.orders_forecast.reduce((a, r) => a + r.pieces, 0);
  const fcstValue = d.orders_forecast.reduce((a, r) => a + r.value, 0);
  const dispRealL = d.dispatched_real.reduce((a, r) => a + r.litres, 0);
  const dispFcstL = d.dispatched_forecast.reduce((a, r) => a + r.litres, 0);
  const received = [...d.received].sort((a, b) => b.qty - a.qty);
  const bought = [...d.bought].sort((a, b) => b.qty - a.qty);
  const ordersReal = [...d.orders_real].sort((a, b) => b.value - a.value);
  const ordersForecast = [...d.orders_forecast].sort((a, b) => b.value - a.value);
  const dispatchedReal = [...d.dispatched_real].sort((a, b) => b.litres - a.litres);
  const dispatchedForecast = [...d.dispatched_forecast].sort((a, b) => b.litres - a.litres);

  // ---- day-1 pile: the measured backlog, quoted from provenance ------------------
  const pile = n === 1 ? getHonesty().label_rules.find((r) => r.id === "day1-pile") : undefined;
  const pileQuote = pile ? String((pile as Record<string, unknown>)["provenance_quote"] ?? "") : "";

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
            {d.working ? <Pill tone="green">working day</Pill> : <Pill>plant off — {d.weekday}</Pill>}
            {roof ? <Pill tone="red">godown at the assumed roof</Pill> : full ? <Pill tone="amber">godown near full</Pill> : null}
          </div>
          <div className="mt-1 text-sm text-zinc-500">{d.date}</div>
        </div>
        {NavBtns}
      </div>

      {/* ---------------------------------------------------------------- the rule */}
      <div className="mt-4 rounded-xl border border-violet-500/25 bg-violet-500/5 px-4 py-3 text-sm text-violet-100/90">
        <span className="mr-2 align-middle"><SimBadge kind="simulated" /></span>
        {n === 1 ? (
          <>
            <span className="font-semibold">The rule:</span> only this day&apos;s <em>opening</em> is observed — the 31-Aug
            SAP close. Everything that then &quot;happens&quot; below — runs, arrivals, invoices — is the calibrated
            simulator playing the plan forward. <span className="text-violet-200/70">{o.meta.forward_rule}</span>
          </>
        ) : (
          <>
            <span className="font-semibold">The rule:</span> only day 1&apos;s opening is observed. This page is{" "}
            <span className="tabular-nums font-semibold">{n - 1}</span> computed {n - 1 === 1 ? "day" : "days"} deep — its
            opening state is <Link href={`/days/${n - 1}`} className="text-amber-400 hover:underline">day {n - 1}</Link>
            &apos;s computed close, and today&apos;s runs, arrivals and invoices are the algorithm applied to that state.
            Nothing on this page has happened.{" "}
            <Link href="/days/1" className="text-violet-300 hover:underline">The chain starts at day 1 →</Link>
          </>
        )}
      </div>

      <div className="mt-4">
        <DayStrip current={n} days={spine} />
        <div className="mt-2 text-xs text-zinc-600">All of planned September. Dim squares are Sundays — plant off. A red ring marks the day the godown touches the assumed roof.</div>
      </div>

      {/* ------------------------------------------------------------- six numbers */}
      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <DayStat label="Filled" value={fmt(d.made_litres)} unit="L" sub={d.working ? `${d.runs.length} runs on ${linesRunning} of ${LINES.length} lines` : "plant off"} />
        <DayStat label="Worth" value={money(d.made_value_rs)} sub="value of what the plan fills today" />
        <DayStat label="Invoiced" value={fmt(d.shipped_litres)} unit="L" sub={`${d.dispatched_real.length + d.dispatched_forecast.length} dispatch lines — trucks out later (declared lag)`} />
        <DayStat label="Line use" value={`${d.line_util}`} unit="%" sub={`${d.flushes} flushes · ${fmt(flushMin)} min changing over`} />
        <DayStat label="Godown" value={`${s.pct}`} unit="%" tone={full ? "text-red-400" : ""} sub={<>of the <em>assumed</em> roof — {fmt(s.ceiling_l)} L <SimBadge kind="assumed" /></>} />
        <DayStat label="Room left" value={fmt(s.headroom_l)} unit="L" tone={full ? "text-red-400" : ""} sub="under the assumed roof, end of day" />
      </div>

      {/* -------------------------------------------------------------- the book */}
      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <DayStat label="Plan left to make" value={fmt(d.book.plan_left_l)} unit="L" sub="of the September plan at this day's close — opening plan-SKU stock and runs to date netted off, SKU by SKU" />
        <DayStat label="Real orders open" value={fmt(d.open_real_l_computed)} unit="L" sub={spine[n - 1].open_real_l_note} />
        <DayStat label="Forecast volume open" value={fmt(d.book.forecast_open_l)} unit="L" badge={<SimBadge kind="forecast" />} sub="demand not yet ordered — the plan's assumed buckets" />
      </div>
      <div className="mt-2 text-[11px] leading-relaxed text-zinc-600">
        Raw sim counters, shown only with their health warnings: {fmt(d.book.po_open_l_raw)} L — {d.book.po_open_l_raw_label}.{" "}
        {money(d.book.po_cumulative_value_rs)} — {d.book.po_cumulative_value_label}.
      </div>

      {/* ---------------------------------------------------------- news of the day */}
      <Section
        title="News of the day"
        right={
          <span className="text-xs text-zinc-500">
            {d.news.materials_landed} PO landings · {d.news.real_pos_entering} real order rows · {d.news.forecast_rows} forecast rows
          </span>
        }
      >
        <p className="mb-3 max-w-4xl text-xs text-zinc-500">
          Purchase orders landing at the gate are the plan&apos;s only external arrivals — each lands when its assumed
          lead time runs out, and on some days nothing lands. Orders are split hard:{" "}
          <span className="text-zinc-300">real</span> rows are the measured SAP backlog entering by promise date;{" "}
          <span className="text-sky-300">forecast</span> rows are the plan wearing a date — nobody has ordered them.
        </p>

        {n === 1 && pile ? (
          <div className="mb-4 rounded-xl border border-emerald-500/25 bg-emerald-500/5 p-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <SimBadge kind="measured" />
              <span className="font-medium text-emerald-200">Day 1 is a pile, and the pile is real.</span>
            </div>
            <div className="mt-1.5 text-zinc-300">{pile.rule}</div>
            <div className="mt-1.5 text-xs text-zinc-400">
              Within the sim&apos;s world — the {o.plan.skus} plan SKUs — the frozen opening carries{" "}
              <span className="tabular-nums">{o.opening.plan_sku_backlog_docs}</span> open order documents,{" "}
              <span className="tabular-nums">{o.opening.plan_sku_backlog_docs_overdue}</span> of them already overdue on
              31 Aug. Most of that slice enters as the pile below — the rest enters on later days, by promise date; the
              whole slice is worth {money(o.opening.backlog_value_rs)} across {fmt(o.opening.backlog_pieces)} pieces.
              The SAP-wide count is a different, wider fact — quoted in full provenance:
            </div>
            {pileQuote ? (
              <details className="mt-2 text-xs text-zinc-500">
                <summary className="cursor-pointer text-emerald-300/80 hover:text-emerald-200">the demand stream&apos;s full provenance, verbatim</summary>
                <div className="mt-2 whitespace-pre-line border-l-2 border-emerald-500/30 pl-3">{pileQuote}</div>
              </details>
            ) : null}
          </div>
        ) : null}

        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <div className="text-sm font-medium text-zinc-300">Real orders entering <SimBadge kind="measured" note="Measured SAP backlog rows, dated by promise. The orders exist; only their timing into the sim follows the promise dates." /></div>
              <div className="text-xs text-zinc-500">{d.orders_real.length} rows · {fmt(realPieces)} pcs · {money(realValue)}</div>
            </div>
            {ordersReal.length === 0 ? (
              <DayEmpty>{d.working ? "No real order rows enter on this date." : "Plant off — no order rows enter."}</DayEmpty>
            ) : (
              <DayScroll max="max-h-[26rem]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Customer</th>
                      <th className={TH}>Channel</th>
                      <th className={TH}>What</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Worth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordersReal.map((r, i) => (
                      <tr key={`${r.docnum}-${r.code}-${i}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-300`}>
                          {r.customer}
                          {bigPO.has(`${r.docnum}|${r.code}`) ? <span className="ml-2"><Pill tone="amber">big PO</Pill></span> : null}
                        </td>
                        <td className={TD}><Pill tone={r.channel === "TRADE" ? "zinc" : "blue"}>{r.channel}</Pill></td>
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
              <div className="text-sm font-medium text-sky-200">Forecast rows entering <SimBadge kind="forecast" /></div>
              <div className="text-xs text-sky-300/60">{d.orders_forecast.length} rows · {fmt(fcstPieces)} pcs · {money(fcstValue)}</div>
            </div>
            {ordersForecast.length === 0 ? (
              <DayEmpty>{d.working ? "No forecast buckets dated today." : "Plant off — no forecast buckets dated today."}</DayEmpty>
            ) : (
              <DayScroll max="max-h-[26rem]" tint="border-sky-500/25 bg-sky-500/[0.04]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Bucket</th>
                      <th className={TH}>What</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Worth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordersForecast.map((r, i) => (
                      <tr key={`${r.docnum}-${i}`} className="text-sky-100/80 hover:bg-sky-500/5">
                        <td className={`${TD}`}>
                          <span className="font-mono text-xs text-sky-300/80">{r.docnum}</span>
                          <div className="text-[10px] text-sky-300/50">{r.customer}</div>
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

        <div className="mt-4">
          <div className="mb-2 flex items-baseline justify-between gap-2">
            <div className="text-sm font-medium text-zinc-300">Purchase orders landing at the gate</div>
            <div className="text-xs text-zinc-500">{received.length} items — arrival dates ride the lead-time assumption</div>
          </div>
          {received.length === 0 ? (
            <DayEmpty>Nothing lands on this date.</DayEmpty>
          ) : (
            <DayScroll max="max-h-[22rem]">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className={TH}>Item</th>
                    <th className={TH}>Kind</th>
                    <th className={THR}>Quantity</th>
                    <th className={TH}>Loop</th>
                  </tr>
                </thead>
                <tbody>
                  {received.map((r, i) => (
                    <tr key={`${r.code}-${i}`} className="hover:bg-zinc-900/60">
                      <td className={`${TD} text-zinc-300`}>{r.name}<span className="ml-2 text-xs text-zinc-600">{r.code}</span></td>
                      <td className={TD}><Pill tone={r.kind === "OIL" ? "red" : "zinc"}>{r.kind.toLowerCase()}</Pill></td>
                      <td className={`${TD} ${NUM}`}>{fmt(r.qty)}</td>
                      <td className={TD}>
                        {unblockedTodayCodes.has(r.code) ? <Pill tone="green">unblocks product — see the loop below</Pill> : <span className="text-xs text-zinc-600">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </DayScroll>
          )}
        </div>
      </Section>

      {/* ------------------------------------------------------------------ what ran */}
      <Section
        title="What ran — line by line, in sequence"
        right={<span className="text-xs text-zinc-500">{d.runs.length} runs · {fmt(d.made_litres)} L · {money(d.made_value_rs)} · {fmt(flushMin)} min of changeovers</span>}
      >
        {idle ? (
          <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
            The lines ran well under capacity today — line use {String(idle.util)}%, {String(idle.blocked)} wants
            blocked. The plan had the hours; it did not have the materials or the room.
          </div>
        ) : null}
        {!d.working ? (
          <DayEmpty>Plant off — {d.weekday}. No runs are planned.</DayEmpty>
        ) : (
          <div className="space-y-3">
            {byLine.map((l) => (
              <div key={l.line} className="rounded-xl border border-zinc-800 bg-zinc-900/40">
                <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-zinc-800 px-3 py-2">
                  <div className="font-medium">{l.line}</div>
                  <div className="text-xs tabular-nums text-zinc-500">
                    {l.runs.length === 0
                      ? "idle"
                      : `${l.runs.length} run${l.runs.length > 1 ? "s" : ""} · ${l.hours} h · ${fmt(l.runs.reduce((a, r) => a + r.litres, 0))} L · ${
                          l.runs.filter((r) => r.flush_min > 0).length
                        } changeover${l.runs.filter((r) => r.flush_min > 0).length === 1 ? "" : "s"}`}
                  </div>
                </div>
                {l.runs.length === 0 ? (
                  <div className="px-3 py-3 text-sm text-zinc-600">idle — nothing planned on this line today</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr>
                          <th className={`${TH} w-8`}>#</th>
                          <th className={TH}>Changeover</th>
                          <th className={TH}>What fills</th>
                          <th className={TH}>Oil</th>
                          <th className={THR}>Pieces</th>
                          <th className={THR}>Litres</th>
                          <th className={THR}>Hours</th>
                          <th className={THR}>Per hour</th>
                          <th className={TH}>Tags</th>
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
                                  <span className="text-amber-300/90 text-xs">{r.flush_min} min flush before</span>
                                ) : (
                                  <span className="text-xs text-zinc-600">straight on</span>
                                )}
                              </td>
                              <td className={`${TD} text-zinc-200`}>{r.sku}<span className="ml-2 text-xs text-zinc-600">{r.code}</span></td>
                              <td className={`${TD} text-xs text-zinc-500 whitespace-nowrap`}>{r.oil ?? "—"}</td>
                              <td className={`${TD} ${NUM}`}>{fmt(r.pieces)}</td>
                              <td className={`${TD} ${NUM}`}>{fmt(r.litres)} L</td>
                              <td className={`${TD} ${NUM} text-zinc-400`}>{r.hours.toFixed(2)}</td>
                              <td className={`${TD} ${NUM} text-zinc-300`}>{money(r.rs_per_hour)}</td>
                              <td className={TD}>
                                <span className="flex flex-wrap gap-1">
                                  {r.head === "PREMIUM" ? <Pill tone="amber">PREMIUM</Pill> : null}
                                  {r.po_backed ? <Pill tone="green">PO backed</Pill> : null}
                                  {closes ? (
                                    <Link href={`/days/${map[closes.ordered_day] ?? 1}`}>
                                      <Pill tone="violet">loop closes — ordered day {map[closes.ordered_day] ?? dlabel(closes.ordered_day)}</Pill>
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
            ))}
          </div>
        )}
      </Section>

      {/* --------------------------------------------------------------- what didn't */}
      <Section
        title="What could not run"
        right={
          <span className="text-xs text-zinc-500">
            {blockedProducts} products held{oilWalls > 0 || packWalls > 0 ? ` · walls hit: ${oilWalls} oil-short, ${packWalls} packaging-zero` : ""}
          </span>
        }
      >
        {blocked.length === 0 ? (
          <DayEmpty>{d.working ? "No product was held back today." : "Plant off — nothing was scheduled, so nothing was blocked."}</DayEmpty>
        ) : (
          <>
            <DayScroll max="max-h-[28rem]">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className={TH}>Product the plan wanted</th>
                    <th className={THR}>Pieces wanted</th>
                    <th className={TH}>The binder — one item short holds the product</th>
                    <th className={THR}>Hits</th>
                    <th className={TH}>Where its loop stands</th>
                  </tr>
                </thead>
                <tbody>
                  {blocked.map((b) => {
                    const lk = chainForBinder(loops.chains, b.binder, d.date);
                    return (
                      <tr key={`${b.code}-${b.binder}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-200`}>{b.sku}<span className="ml-2 text-xs text-zinc-600">{b.code}</span></td>
                        <td className={`${TD} ${NUM}`}>{fmt(b.want)}</td>
                        <td className={TD}>
                          <span className="text-zinc-300">{b.binder_name}</span>
                          <span className="ml-2 text-xs text-zinc-600">{b.binder}</span>
                          <span className="ml-2"><Pill tone={b.binder.startsWith("RM") ? "red" : "zinc"}>{b.binder.startsWith("RM") ? "oil" : "packaging"}</Pill></span>
                        </td>
                        <td className={`${TD} ${NUM} text-zinc-500`}>{b.times}</td>
                        <td className={`${TD} text-xs`}>
                          {lk ? (
                            lk.state === "on-order" ? (
                              <span className="text-amber-300/90">
                                ordered <LoopDayRef date={lk.chain.ordered_day} map={map} /> → lands <LoopDayRef date={lk.chain.unblocked_day ?? lk.chain.lands} map={map} />
                              </span>
                            ) : lk.state === "ordered-later" ? (
                              <span className="text-zinc-400">
                                the sim orders it <LoopDayRef date={lk.chain.ordered_day} map={map} />
                              </span>
                            ) : (
                              <span className="text-emerald-300/80">
                                landed <LoopDayRef date={lk.chain.unblocked_day ?? lk.chain.lands} map={map} /> — ran out again
                              </span>
                            )
                          ) : (
                            <span className="text-zinc-600">no order in the sim&apos;s book</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </DayScroll>
            <div className="mt-2 text-xs text-zinc-500">
              Folded: the plan re-tries a wall, so the same block can be hit many times in a day — &quot;hits&quot; counts
              the attempts. The last column is the block → order → land loop for that binder.
            </div>
          </>
        )}
      </Section>

      {/* ------------------------------------------------------------------ the loop */}
      <Section
        title="The loop — blocked → ordered → lands → runs"
        right={<span className="text-xs text-zinc-500">{loops.note}</span>}
      >
        {todaysChains.length === 0 ? (
          <DayEmpty>
            No loop steps fall on this date. {d.waiting_on.length > 0 ? "Materials are still in transit — see below." : "Nothing ordered, nothing landing, nothing freed."}
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
            <div className="text-xs uppercase tracking-wider text-zinc-500">Still waiting at day&apos;s end</div>
            <ul className="mt-2 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
              {d.waiting_on.map((w) => (
                <li key={`${w.code}-${w.since}`} className="flex flex-wrap items-baseline gap-x-2">
                  <span className="text-zinc-300">{w.name}</span>
                  <span className="text-xs text-zinc-600">{w.code}</span>
                  <span className="text-xs text-zinc-500">blocked since <LoopDayRef date={w.since} map={map} /></span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mt-4">
          <div className="mb-2 flex items-baseline justify-between gap-2">
            <div className="text-sm font-medium text-zinc-300">Every purchase the plan places today</div>
            <div className="text-xs text-zinc-500">{bought.length} items — amber rows are orders that free a blocked product</div>
          </div>
          {bought.length === 0 ? (
            <DayEmpty>The plan places no purchase orders on this date.</DayEmpty>
          ) : (
            <DayScroll max="max-h-[24rem]">
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className={TH}>Item</th>
                    <th className={THR}>Quantity</th>
                    <th className={TH}>Lands</th>
                    <th className={TH}>Unblocks</th>
                  </tr>
                </thead>
                <tbody>
                  {bought.map((b, i) => {
                    const ch = orderedTodayByCode.get(b.code);
                    return (
                      <tr key={`${b.code}-${i}`} className={ch ? "bg-amber-500/[0.06] hover:bg-amber-500/10" : "hover:bg-zinc-900/60"}>
                        <td className={`${TD} text-zinc-300`}>{b.name}<span className="ml-2 text-xs text-zinc-600">{b.code}</span></td>
                        <td className={`${TD} ${NUM}`}>{fmt(b.qty)} <span className="text-zinc-500">{b.uom}</span></td>
                        <td className={`${TD} whitespace-nowrap text-xs`}><LoopDayRef date={b.lands} map={map} /></td>
                        <td className={`${TD} text-xs`}>
                          {ch ? (
                            <span className="text-amber-300/90">{ch.fg_codes_blocked.length} blocked product{ch.fg_codes_blocked.length === 1 ? "" : "s"} — pipeline above</span>
                          ) : (
                            <span className="text-zinc-600">cover buy</span>
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

      {/* ------------------------------------------------------------------ storage */}
      <Section
        title="Storage"
        right={<Link href="/storage" className="text-xs text-amber-400 hover:underline">the whole month&apos;s storage →</Link>}
      >
        <DayWaterfall
          opening={opening}
          openingMeasured={n === 1}
          openingCaption={
            n === 1 ? (
              <>
                Opening is the one measured bar on this page <SimBadge kind="measured" /> — the 31-Aug SAP close.{" "}
                <span className="text-amber-300/80">{stg.standing_at_open.note}</span> <SimBadge kind="assumed" />
              </>
            ) : (
              <>
                Opening is <Link href={`/days/${n - 1}`} className="text-amber-400 hover:underline">day {n - 1}</Link>&apos;s computed
                close — simulated, like everything downstream of day 1. <SimBadge kind="simulated" />
              </>
            )
          }
          openingSub={n === 1 ? "measured 31-Aug close" : `day ${n - 1}'s computed close`}
          made={d.made_litres}
          gated={gated}
          s={s}
        />
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Card title="Oil drawn today" value={`${fmt(d.oil_used_l)} L`} sub="loose oil the runs consume — bulk tanks sit outside the godown roof" />
          <div className="lg:col-span-2">
            {d.decisions.length === 0 ? (
              <DayEmpty>No storage call today — the plan fit under the assumed roof.</DayEmpty>
            ) : (
              <div className="space-y-2">
                {d.decisions.map((dc, i) => (
                  <div key={`${dc.kind}-${i}`} className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone="amber">{dc.kind.replace(/_/g, " ").toLowerCase()}</Pill>
                      <SimBadge kind="simulated" />
                    </div>
                    <div className="mt-1.5 text-sm text-amber-100">{dc.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* ----------------------------------------------------------- what went out */}
      <Section
        title="What the plan invoices today"
        right={<span className="text-xs text-zinc-500">{fmt(d.shipped_litres)} L — it leaves the gate later, on the declared invoice-to-truck lag</span>}
      >
        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <div className="mb-2 flex items-baseline justify-between gap-2">
              <div className="text-sm font-medium text-zinc-300">Against real orders</div>
              <div className="text-xs text-zinc-500">{dispatchedReal.length} lines · {fmt(dispRealL)} L</div>
            </div>
            {dispatchedReal.length === 0 ? (
              <DayEmpty>Nothing invoiced against real orders on this date.</DayEmpty>
            ) : (
              <DayScroll max="max-h-[24rem]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Customer</th>
                      <th className={TH}>What</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Litres</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dispatchedReal.map((x, i) => (
                      <tr key={`${x.docnum}-${x.sku}-${i}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-300`}>{x.customer}<span className="ml-2"><Pill tone={x.channel === "TRADE" ? "zinc" : "blue"}>{x.channel}</Pill></span></td>
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
              <div className="text-sm font-medium text-sky-200">Against forecast buckets <SimBadge kind="forecast" /></div>
              <div className="text-xs text-sky-300/60">{dispatchedForecast.length} lines · {fmt(dispFcstL)} L</div>
            </div>
            {dispatchedForecast.length === 0 ? (
              <DayEmpty>No forecast volume is served on this date.</DayEmpty>
            ) : (
              <DayScroll max="max-h-[24rem]" tint="border-sky-500/25 bg-sky-500/[0.04]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Bucket</th>
                      <th className={TH}>What</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Litres</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dispatchedForecast.map((x, i) => (
                      <tr key={`${x.docnum}-${x.sku}-${i}`} className="text-sky-100/80 hover:bg-sky-500/5">
                        <td className={TD}><span className="font-mono text-xs text-sky-300/80">{x.docnum}</span></td>
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

      {/* ------------------------------------------------------------------ honesty */}
      <div className="mt-10 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
        <div className="text-xs uppercase tracking-wider text-zinc-500">What is real on this page, and what is not</div>
        <div className="mt-3 grid gap-4 md:grid-cols-2">
          <div>
            <div className="mb-2 text-sm text-emerald-300">Measured — pulled from the real systems on 31 Aug</div>
            <div className="flex flex-wrap gap-1.5">{d.honesty.measured.map((x) => <Pill key={x} tone="green">{x}</Pill>)}</div>
          </div>
          <div>
            <div className="mb-2 text-sm text-amber-300">Assumed — declared choices of the model, not measurements</div>
            <div className="flex flex-wrap gap-1.5">{d.honesty.assumed.map((x) => <Pill key={x} tone="amber">{x}</Pill>)}</div>
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
