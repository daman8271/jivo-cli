"use client";

// /days — the whole month, in two halves that are never mixed.
//
// LEFT of today: RECORDS. What the plant actually filled and what actually left
// the gate on each day between the 1st and yesterday, read off ji.jivo.in by
// live/adapters/factory_history.py. Sky bars, HAPPENED badge, their own table.
// RIGHT of today: the PLAN. Day 1 is today and it is the only day read off the
// plant live; every row after it is computed from the row before it plus what
// the planner decided, and the whole ladder is rebuilt every few minutes.
//
// Three rules this file exists to keep:
//   · a record with a null figure is NOT READ. It is drawn as an empty hatched
//     slot, never as a bar of height zero — that would be the plant idle.
//   · made_booked_l (goods receipts) and made_mes_l (the machine log) are the
//     SAME production counted two ways. They are drawn as two bars SIDE BY SIDE
//     off one baseline, both labelled, and never added. They used to be nested,
//     the machine log drawn "inside" the booked bar with the legend saying so —
//     which was false on half the days September has published so far, because
//     the goods receipt lags the filling it books by a day or so and the machine
//     log is then the taller of the two. Two bars where the inner one is bigger
//     than the outer are not a nesting; they are two marks in one slot.
//   · the plan renders whether or not the records loaded. The history record is
//     never allowed to wrap the plan panel.
//
// The strip is a CALENDAR: every slot between the 1st and today is drawn in date
// order, records and unread days in one list. Rendering the unread days as their
// own block put them all before the 1st.
//
// "Today" is checked against the calendar, never assumed from n === 1 — a plan
// the chain has stopped rebuilding keeps yesterday's day 1.

import Link from "next/link";
import { useState } from "react";
import { asHistory, asHonesty, asOverview, asSpine, istToday, useLive, useNow } from "../lib/live";
import { happenedRule, P, ruleText } from "../lib/labels";
import { dlabel, inr, litres, money, orUnknown, pct, pct1, plural, weekdayShort } from "../lib/fmt";
import { AsOf, Live, NotLive, OwnStamp } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";
import type { HistoryDay } from "../lib/types";

/** A record's date, only if it is genuinely before the plan's first day. */
const beforePlan = (date: string, firstPlanDate: string | null) =>
  firstPlanDate === null || date < firstPlanDate;

/** One slot on the calendar strip: a day already gone, with its record or
 *  without one. `row === null` is "not read" — not a day nothing happened. */
type Gone = { date: string; row: HistoryDay | null };

/** The hatch that means NOT READ, wherever it appears — a whole day or one
 *  half of a day whose other half did come back. */
const HATCH =
  "rounded-sm border border-dashed border-zinc-700 " +
  "bg-[repeating-linear-gradient(45deg,transparent,transparent_3px,rgba(113,113,122,0.25)_3px,rgba(113,113,122,0.25)_6px)]";

export default function DaysClient() {
  const live = useLive(["spine", "overview", "honesty", "history"]);
  const spine = asSpine(live.spine) ?? [];
  const o = asOverview(live.overview);
  const h = asHonesty(live.honesty);
  const hist = asHistory(live.history);
  const [hover, setHover] = useState<string | null>(null);
  const now = useNow(10_000);
  const today = istToday(now || undefined);
  const gone = happenedRule(h);

  // Drop any record that overlaps the plan — the plan wins for its own days.
  const firstPlanDate = spine.length ? spine[0].date : null;
  const elapsed = (hist?.days ?? []).filter((d) => beforePlan(d.date, firstPlanDate));
  const notRead = (hist?.missing_dates ?? []).filter((d) => beforePlan(d, firstPlanDate));

  // ONE list, in date order. A day with no record keeps its place in the month
  // instead of being bunched in front of the 1st.
  const goneDays: Gone[] = [
    ...elapsed.map((row) => ({ date: row.date, row })),
    ...notRead.map((date) => ({ date, row: null })),
  ].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  // The publisher's own words for the two bases, used as the legend's tooltips.
  const bookedLabel = elapsed.find((d) => d.made_booked_label)?.made_booked_label ?? null;
  const mesLabel = elapsed.find((d) => d.made_mes_label)?.made_mes_label ?? null;

  // One height scale across both halves, so a record and a plan day of the same
  // size draw the same. Records use the fuller of the two bases for the height.
  const max = Math.max(
    1,
    ...elapsed.map((d) => d.made_booked_l ?? 0),
    ...elapsed.map((d) => d.made_mes_l ?? 0),
    ...spine.map((d) => d.made_l),
  );

  const hoveredRecord = elapsed.find((d) => d.date === hover) ?? null;
  const hoveredPlan = spine.find((d) => d.date === hover) ?? null;
  const hoveredMissing = hover !== null && notRead.includes(hover) ? hover : null;

  const title = o
    ? elapsed.length
      ? `${elapsed.length} ${plural(elapsed.length, "day", "days")} gone, ${o.totals.days} left ` +
        `(${o.totals.working_days} working)`
      : `${o.totals.days} days left, ${o.totals.working_days} of them working`
    : "The month";

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Day by day</h1>
        <SimBadge kind="happened" />
        <SimBadge kind="plan" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {ruleText(h, "rolling-replan") ??
          "Today is read off the plant. The days before it are records; every later day is worked out from today."}
      </p>

      <div className="mt-6 space-y-4">
        <Panel title={title} badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live.spine} />}>
          <Live rec={live.spine} what="the month">
            {/* read-out — fixed height so nothing jumps when you sweep across */}
            <div className="mb-4 min-h-[66px] border-b border-zinc-800 pb-3">
              {hoveredRecord ? (
                <div className="flex flex-wrap items-start gap-x-6 gap-y-3">
                  <div className="min-w-[130px]">
                    <div className="text-[10px] uppercase tracking-wider text-sky-400">
                      {hoveredRecord.working ? "Happened — read off the plant" : `${hoveredRecord.weekday} — closed`}
                    </div>
                    <div className="mt-0.5 text-sm font-semibold">
                      {weekdayShort(hoveredRecord.weekday)} {dlabel(hoveredRecord.date)}
                    </div>
                  </div>
                  <Stat
                    k="Booked into godown"
                    v={orUnknown(hoveredRecord.made_booked_l, litres, "not read")}
                    sub="goods receipts"
                  />
                  <Stat
                    k="Machine log"
                    v={orUnknown(hoveredRecord.made_mes_l, litres, "not read")}
                    sub="about two-thirds of the plant"
                  />
                  <Stat k="Runs" v={orUnknown(hoveredRecord.runs, inr, "not read")} />
                  <Stat k="Billed out" v={orUnknown(hoveredRecord.billed_out_l, litres, "not read")} sub="from BH-PF" />
                  <Stat
                    k="Left the gate (Oil)"
                    v={orUnknown(hoveredRecord.dispatched_oil_l, litres, "not read")}
                    tone="text-sky-300"
                  />
                  <Stat k="Trucks (Oil)" v={orUnknown(hoveredRecord.trucks_oil, inr, "not read")} />
                  {!hoveredRecord.complete && (
                    <Pill tone="amber" title={hoveredRecord.notes.join(" · ") || "part of this day did not come back"}>
                      part-read
                    </Pill>
                  )}
                </div>
              ) : hoveredMissing ? (
                <div className="pt-3 text-sm text-zinc-400">
                  <span className="font-semibold text-zinc-300">{dlabel(hoveredMissing)}</span> — not read. The plant&rsquo;s
                  systems did not answer for this day, so nothing is known about it. It is not a day nothing happened.
                </div>
              ) : hoveredPlan ? (
                <div className="flex flex-wrap items-start gap-x-6 gap-y-3">
                  <div className="min-w-[120px]">
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                      {hoveredPlan.n === 1
                        ? hoveredPlan.date === today
                          ? "Today — read off the plant"
                          : "Day 1 when the plan was built — not today"
                        : hoveredPlan.working
                          ? "Working day — the plan"
                          : `${hoveredPlan.weekday} — closed`}
                    </div>
                    <div className="mt-0.5 text-sm font-semibold">
                      {weekdayShort(hoveredPlan.weekday)} {dlabel(hoveredPlan.date)}
                    </div>
                  </div>
                  <Stat k="Filled" v={hoveredPlan.made_l > 0 ? litres(hoveredPlan.made_l) : "nothing"} />
                  <Stat k="Worth" v={hoveredPlan.value_rs > 0 ? money(hoveredPlan.value_rs) : "—"} />
                  <Stat k="Billed" v={hoveredPlan.shipped_l > 0 ? litres(hoveredPlan.shipped_l) : "nothing"} />
                  <Stat
                    k="Machines busy"
                    v={pct(hoveredPlan.util)}
                    tone={
                      hoveredPlan.util >= 80 ? "text-emerald-300" : hoveredPlan.util >= 30 ? "text-amber-300" : "text-zinc-100"
                    }
                  />
                  <Stat
                    k="Godown full"
                    v={pct1(hoveredPlan.storage_pct)}
                    tone={
                      hoveredPlan.storage_pct >= 95
                        ? "text-red-300"
                        : hoveredPlan.storage_pct >= 80
                          ? "text-amber-300"
                          : "text-emerald-300"
                    }
                  />
                  <Stat k="Runs" v={inr(hoveredPlan.runs)} />
                  {/* PRODUCTS, not rows. `blocked` is one row per attempt and a product
                      is tried on every machine that could fill it, so the row count runs
                      to nearly double the products behind it. */}
                  <Stat
                    k="Stuck products"
                    v={orUnknown(hoveredPlan.blocked_products, inr, "—")}
                    tone={(hoveredPlan.blocked_products ?? 0) > 0 ? "text-red-300" : "text-zinc-100"}
                    sub={`${inr(hoveredPlan.blocked)} ${plural(hoveredPlan.blocked, "try", "tries")} stopped`}
                  />
                  <Stat k="Ordered lines" v={inr(hoveredPlan.orders.real_rows)} tone="text-emerald-300" />
                  <Stat k="Expected lines" v={inr(hoveredPlan.orders.forecast_rows)} tone="text-violet-300" />
                </div>
              ) : (
                <p className="pt-3 text-sm text-zinc-500">
                  Move over a day for its numbers. Bar height is litres filled; on the plan days the colour is how full
                  the godown gets. Bars before today have happened; today&rsquo;s is read live; the rest are the plan. A
                  day that has happened gets two bars, side by side: what was booked into the godown, and what the
                  machine log counted. They are the same oil counted two ways and are never added &mdash; and because a
                  booking can land the day after the filling it books, either one can be the taller.
                </p>
              )}
            </div>

            <div className="flex h-56 items-stretch gap-[3px]">
              {/* the days already gone, IN DATE ORDER — records and unread days
                  in one list, because the strip is a calendar. Records are not
                  links: there is no /days/n for a day that has happened. */}
              {goneDays.map(({ date, row: x }) =>
                x === null ? (
                  <button
                    key={date}
                    type="button"
                    onMouseEnter={() => setHover(date)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(date)}
                    onBlur={() => setHover(null)}
                    aria-label={`${dlabel(date)} — not read`}
                    title="not read"
                    className={`grid flex-1 grid-rows-[1fr_auto] gap-1 rounded-sm outline-none transition-colors focus-visible:ring-1 focus-visible:ring-sky-400 ${
                      hover === date ? "bg-zinc-800" : "hover:bg-zinc-900"
                    }`}
                  >
                    <div className={`min-h-0 ${HATCH}`} />
                    <div className="text-center text-[9px] text-zinc-600">{Number(date.slice(8, 10))}</div>
                  </button>
                ) : (
                  (() => {
                    const booked = x.made_booked_l;
                    const mes = x.made_mes_l;
                    const unread = booked === null && mes === null;
                    // Two bars off ONE baseline, half the slot each. Never
                    // nested: the goods receipt lags the filling, so on a real
                    // day the machine log is often the taller of the two.
                    const bookedH = booked === null ? 0 : Math.max(1.5, (booked / max) * 100);
                    const mesH = mes === null ? 0 : Math.max(1.5, (mes / max) * 100);
                    return (
                      <button
                        key={x.date}
                        type="button"
                        onMouseEnter={() => setHover(x.date)}
                        onMouseLeave={() => setHover(null)}
                        onFocus={() => setHover(x.date)}
                        onBlur={() => setHover(null)}
                        aria-label={
                          `${dlabel(x.date)} — happened: booked ${orUnknown(booked, inr, "not read")} litres, ` +
                          `machine log ${orUnknown(mes, inr, "not read")} litres, ` +
                          `left the gate for Oil ${orUnknown(x.dispatched_oil_l, inr, "not read")} litres`
                        }
                        className={`grid flex-1 grid-rows-[1fr_auto] gap-1 rounded-sm outline-none transition-colors focus-visible:ring-1 focus-visible:ring-sky-400 ${
                          x.working ? "" : "opacity-40"
                        } ${hover === x.date ? "bg-zinc-800" : "hover:bg-zinc-900"}`}
                      >
                        {unread ? (
                          <div className={`min-h-0 ${HATCH}`} />
                        ) : (
                          <div className="flex min-h-0 items-end gap-px">
                            {booked === null ? (
                              <div className={`h-full flex-1 ${HATCH}`} title="booked into the godown — not read" />
                            ) : (
                              <div
                                className="flex-1 rounded-sm bg-sky-500"
                                style={{ height: `${bookedH}%` }}
                                title={bookedLabel ?? "booked into the godown"}
                              />
                            )}
                            {mes === null ? (
                              <div className={`h-full flex-1 ${HATCH}`} title="the machine log — not read" />
                            ) : (
                              <div
                                className="flex-1 rounded-sm bg-sky-200/70"
                                style={{ height: `${mesH}%` }}
                                title={mesLabel ?? "the machine log"}
                              />
                            )}
                          </div>
                        )}
                        <div className="text-center text-[9px] text-sky-700">{x.day_of_month}</div>
                      </button>
                    );
                  })()
                ),
              )}
              {/* today and everything after it — the plan */}
              {spine.map((x) => {
                const tone = x.storage_pct >= 95 ? "bg-red-500" : x.storage_pct >= 80 ? "bg-amber-500" : "bg-emerald-500";
                const hgt = x.made_l > 0 ? Math.max(1.5, (x.made_l / max) * 100) : 0;
                return (
                  <Link
                    key={x.date}
                    href={`/days/${x.n}`}
                    onMouseEnter={() => setHover(x.date)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(x.date)}
                    onBlur={() => setHover(null)}
                    aria-label={`${dlabel(x.date)} — fills ${inr(x.made_l)} litres, godown ${Math.round(
                      x.storage_pct,
                    )} per cent full`}
                    className={`grid flex-1 grid-rows-[1fr_auto] gap-1 rounded-sm outline-none transition-colors focus-visible:ring-1 focus-visible:ring-amber-400 ${
                      x.working ? "" : "opacity-40"
                    } ${hover === x.date ? "bg-zinc-800" : "hover:bg-zinc-900"}`}
                  >
                    {/* the same two-row grid as a record slot, so every bar in
                        the strip stands on the same line as its neighbour */}
                    <div className="flex min-h-0 items-end">
                      <div className={`${tone} w-full rounded-sm`} style={{ height: `${hgt}%` }} />
                    </div>
                    <div className="text-center text-[9px] text-zinc-600">{Number(x.date.slice(8, 10))}</div>
                  </Link>
                );
              })}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-500">
              <span className="inline-flex items-center gap-1.5" title={bookedLabel ?? undefined}>
                <span className="h-2 w-2 rounded-sm bg-sky-500" /> happened — booked into the godown
              </span>
              <span className="inline-flex items-center gap-1.5" title={mesLabel ?? undefined}>
                <span className="h-2 w-2 rounded-sm bg-sky-200/70" /> happened — the machine log, beside it
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm bg-emerald-500" />
                <span className="h-2 w-2 rounded-sm bg-amber-500" />
                <span className="h-2 w-2 rounded-sm bg-red-500" /> the plan, by how full the godown gets
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm bg-zinc-600 opacity-40" /> Sunday
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm border border-dashed border-zinc-600" /> not read
              </span>
            </div>

            {/* the records never wrap the plan: if they are missing, one line says so */}
            {live.history.data === null && (
              <p className="mt-3 text-xs text-zinc-500">
                {live.history.loading
                  ? "Reading the days already gone…"
                  : `The days already gone could not be read${
                      live.history.error ? ` (the publisher said: ${live.history.error})` : ""
                    }. The plan below is unaffected.`}
              </p>
            )}
          </Live>
        </Panel>

        {hist && (
          <Panel
            title="Already happened this month"
            badge={<SimBadge kind="happened" />}
            asOf={
              <OwnStamp
                iso={hist.meta.records_read_at}
                what="records read"
                staleAfterHours={2}
                fallback={<AsOf rec={live.history} />}
              />
            }
            note={hist.rule}
          >
            <Live rec={live.history} what="the days already gone">
              {(hist.meta.records_from_cache || (hist.meta.records_mode && hist.meta.records_mode !== "live")) && (
                <div className="mb-3">
                  <NotLive p={P.carried(hist.meta.records_mode, hist.meta.records_from_cache)} />
                </div>
              )}
              {elapsed.length === 0 && notRead.length === 0 ? (
                <p className="text-sm text-zinc-400">
                  Nothing has gone yet this month — today is the first day.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[46rem] text-sm">
                    <thead>
                      <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                        <th className="py-1 font-normal">Day</th>
                        <th className="py-1 text-right font-normal">Booked into godown</th>
                        <th className="py-1 text-right font-normal">Machine log</th>
                        <th className="py-1 text-right font-normal">Runs</th>
                        <th className="py-1 text-right font-normal">Billed out</th>
                        <th className="py-1 text-right font-normal">Left the gate (Oil)</th>
                        <th className="py-1 text-right font-normal">Trucks (Oil)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {/* one list, in date order: an unread day sits in its own
                          calendar slot, not in a block under the read ones */}
                      {goneDays.map(({ date, row: x }) =>
                        x === null ? (
                          <tr key={date} className="border-t border-zinc-800/60 text-zinc-600">
                            <td className="py-1">{dlabel(date)}</td>
                            <td className="py-1 text-right" colSpan={6}>
                              not read — the plant&rsquo;s systems did not answer for this day
                            </td>
                          </tr>
                        ) : (
                          <tr key={x.date} className={`border-t border-zinc-800/60 ${x.working ? "" : "text-zinc-600"}`}>
                            <td className="py-1">
                              {weekdayShort(x.weekday)} {dlabel(x.date)}{" "}
                              <Pill tone="blue" title="a record of a day already gone, read off the plant">
                                happened
                              </Pill>
                              {!x.complete && (
                                <>
                                  {" "}
                                  <Pill tone="amber" title={x.notes.join(" · ") || "part of this day did not come back"}>
                                    part-read
                                  </Pill>
                                </>
                              )}
                            </td>
                            <td className="py-1 text-right tabular-nums">{orUnknown(x.made_booked_l, inr, "not read")}</td>
                            <td className="py-1 text-right tabular-nums text-zinc-400">
                              {orUnknown(x.made_mes_l, inr, "not read")}
                            </td>
                            <td className="py-1 text-right tabular-nums">{orUnknown(x.runs, inr, "not read")}</td>
                            <td className="py-1 text-right tabular-nums">{orUnknown(x.billed_out_l, inr, "not read")}</td>
                            <td className="py-1 text-right tabular-nums text-sky-300">
                              {orUnknown(x.dispatched_oil_l, inr, "not read")}
                            </td>
                            <td className="py-1 text-right tabular-nums">{orUnknown(x.trucks_oil, inr, "not read")}</td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="mt-3 text-xs text-zinc-500">
                {hist.basis.made_booked ? `${hist.basis.made_booked} ` : ""}
                {hist.basis.made_mes ?? ""}
              </p>
              <p className="mt-2 text-xs text-zinc-500">
                {gone.text ??
                  "These are records, not the plan — the two ways of counting what was filled are never added together."}
              </p>
              {hist.basis.dispatched && <p className="mt-2 text-xs text-zinc-500">{hist.basis.dispatched}</p>}
              {hist.basis.billed_out && <p className="mt-2 text-xs text-zinc-500">{hist.basis.billed_out}</p>}
            </Live>
          </Panel>
        )}

        <Panel title="Every day from here, in a table" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live.spine} />}>
          <Live rec={live.spine} what="the month">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[52rem] text-sm">
                <thead>
                  <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                    <th className="py-1 font-normal">Day</th>
                    <th className="py-1 text-right font-normal">Filled</th>
                    <th className="py-1 text-right font-normal">Worth</th>
                    <th className="py-1 text-right font-normal">Billed</th>
                    <th className="py-1 text-right font-normal">Busy</th>
                    <th className="py-1 text-right font-normal">Godown</th>
                    <th className="py-1 text-right font-normal">Runs</th>
                    <th className="py-1 text-right font-normal" title={spine[0]?.blocked_label}>
                      Stuck products
                    </th>
                    <th className="py-1 text-right font-normal">Ordered</th>
                    <th className="py-1 text-right font-normal">Expected</th>
                  </tr>
                </thead>
                <tbody>
                  {spine.map((x) => (
                    <tr key={x.date} className={`border-t border-zinc-800/60 ${x.working ? "" : "text-zinc-600"}`}>
                      <td className="py-1">
                        <Link href={`/days/${x.n}`} className="underline-offset-2 hover:underline">
                          {weekdayShort(x.weekday)} {dlabel(x.date)}
                        </Link>
                        {x.n === 1 && x.date === today && (
                          <Pill tone="green" title="the only day that is read off the plant">
                            today
                          </Pill>
                        )}
                        {x.n === 1 && x.date !== today && (
                          <Pill tone="amber" title="day 1 of a plan the chain has not rebuilt — its date is not today">
                            day 1, not today
                          </Pill>
                        )}
                      </td>
                      <td className="py-1 text-right tabular-nums">{x.made_l > 0 ? inr(x.made_l) : "—"}</td>
                      <td className="py-1 text-right tabular-nums">{x.value_rs > 0 ? money(x.value_rs) : "—"}</td>
                      <td className="py-1 text-right tabular-nums">{x.shipped_l > 0 ? inr(x.shipped_l) : "—"}</td>
                      <td className="py-1 text-right tabular-nums">{pct(x.util)}</td>
                      <td
                        className={`py-1 text-right tabular-nums ${
                          x.storage_pct >= 95 ? "text-red-300" : x.storage_pct >= 80 ? "text-amber-300" : ""
                        }`}
                      >
                        {pct1(x.storage_pct)}
                      </td>
                      <td className="py-1 text-right tabular-nums">{x.runs}</td>
                      <td
                        title={`${inr(x.blocked)} ${plural(x.blocked, "try", "tries")} stopped — ${x.blocked_label ?? ""}`}
                        className={`py-1 text-right tabular-nums ${(x.blocked_products ?? 0) > 0 ? "text-red-300" : ""}`}
                      >
                        {orUnknown(x.blocked_products, inr, "—")}
                      </td>
                      <td className="py-1 text-right tabular-nums text-emerald-300">{x.orders.real_rows}</td>
                      <td className="py-1 text-right tabular-nums text-violet-300">{x.orders.forecast_rows}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-zinc-500">
              &ldquo;Ordered&rdquo; and &ldquo;Expected&rdquo; are order LINES, not litres — on a quiet day every one of
              them is expected. &ldquo;Stuck products&rdquo; counts DIFFERENT products the planner could not start; a
              product is tried on every machine that could fill it, so the number of stopped tries behind it is larger
              &mdash; hover a figure for it. {o ? `${plural(o.totals.days, "This day is", "These days are")} re-worked every few minutes.` : ""}
            </p>
          </Live>
        </Panel>
      </div>
    </div>
  );
}
