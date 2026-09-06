"use client";

// The NOW strip — the plant as the loop last saw it, a few minutes ago.
// Every tile carries its own "as of", and every tile that is fed by something
// other than a live read carries the badge that says so.

import Link from "next/link";
import {
  asHonesty, asOverview, asState, asStorage, useLive,
} from "../lib/live";
import { ceilingRule, maskDigits, P, pendencyRule, standingRule } from "../lib/labels";
import { inr, litres, money, orUnknown, pct1, plural, tonnes } from "../lib/fmt";
import { AsOf, Live, LiveSource, NotLive, OwnStamp, SourceLine } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

/** "3 Sep 11:59" from an ISO stamp, in the reader's own clock. */
const hhmmDate = (iso: string) => {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return iso;
  const d = new Date(t);
  return `${d.getDate()} ${d.toLocaleString("en-GB", { month: "short" })} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};

export default function NowStrip() {
  const live = useLive(["state", "storage", "honesty", "overview"]);
  const st = asState(live.state);
  const storage = asStorage(live.storage);
  const h = asHonesty(live.honesty);
  const o = asOverview(live.overview);

  const prod = st?.factory_production;
  const disp = st?.factory_dispatch;
  const inb = st?.factory_inbound;
  const exim = st?.exim;
  const ecom = st?.ecom;
  const oms = st?.oms;

  const running = prod?.running_now ?? [];
  const byLine = prod?.by_line_today ?? {};
  const ceiling = ceilingRule(h);
  const standing = standingRule(h);
  const tanks = exim?.tanks;

  /* the dispatch headline, Mark 4 (AC09): how many days of work sit in the open
     book, and how long a bill waits for a truck. `overview.dispatch` carries no
     `trucks` field at all — what left the gate today is a detail, not a
     headline, and lives in a fold at the bottom of this strip. */
  const d = o?.dispatch ?? null;
  const pend = pendencyRule(h);
  const lagStatic = d ? d.lag_static === true : disp?.lag_note?.static === true;
  /* the state adapter's own lag block is the fallback for a plan built before
     the daily measurement existed */
  const lag = disp?.lag_note;
  const lagMedian = d?.lag_median_days ?? lag?.median_days ?? null;
  const lagP90 = d?.lag_p90_days ?? lag?.p90_days ?? null;
  const lagMax = d?.lag_max_days ?? lag?.max_days ?? null;
  const lagRows = d?.lag_rows ?? lag?.rows ?? null;
  const lagWindow = d?.lag_window ?? lag?.measured_window ?? null;
  const lagOn = d?.lag_measured_on ?? lag?.measured_on ?? null;
  const lagCaveat = d?.lag_caveat ?? lag?.caveat ?? null;
  const lagByCompany = Object.entries(d?.lag_by_company ?? {}).sort((a, b) => (b[1].n ?? 0) - (a[1].n ?? 0));
  /* WHICH BOOK THE PLAN'S WAIT IS. The gate is one gate carrying three companies, this
     plan makes Oil, and the engine used to be fed the MERGED median — a day shorter,
     because Beverages is more than half the rows and turns its trucks fastest. A day of
     wait is a day of room in a godown that opens full, so the merged figure was buying
     the plan storage JIVO Oil's own gate log does not give it. */
  const lagBook = d?.lag_book ?? null;
  const lagBookName = lagBook && lagBook !== "ALL_BOOKS" ? lagBook.replace("JIVO_", "").toLowerCase() : null;
  const lagAllMedian = d?.lag_all_books_median_days ?? null;
  const lagAllP90 = d?.lag_all_books_p90_days ?? null;
  const lagAllRows = d?.lag_all_books_rows ?? null;
  const days = (v: number) => `${v} ${plural(v, "day", "days")}`;

  /* dispatched today, per company — never one merged headline (spec §Company scoping) */
  const byCompany = Object.entries(disp?.dispatched_today?.by_company ?? {})
    .map(([k, v]) => ({ company: k, ...v }))
    .sort((a, b) => (b.litres ?? 0) - (a.litres ?? 0));
  const oilDispatched = disp?.oil?.dispatched_today_litres ?? null;

  /* the invoiced-but-not-trucked pile: the Oil slice is a headline, the
     all-books figure is shown beside it and labelled, never added to it */
  const pileOilL = storage?.at_open.billed_not_gone_l ?? standing.litres ?? null;
  const pileAllBooksL = disp?.invoiced_not_dispatched?.litres ?? null;
  const pileByStatus = Object.entries(disp?.invoiced_not_dispatched?.by_status ?? {});
  const pilePct = standing.pctOfCeiling ?? (pileOilL !== null && ceiling.working_l ? (pileOilL / ceiling.working_l) * 100 : null);

  return (
    <div className="space-y-4">
      {/* ── the strip ─────────────────────────────────────────────────
          No outer <Live rec={live.state}> here: each of these four panels
          carries its own <LiveSource>, which now greys for a stale body as
          well as a failed adapter. Wrapping them too would stack two banners
          and two 45% opacities on the same tiles. */}
      <div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {/* machines running */}
          <Panel
            title="Machines running now"
            badge={<SimBadge kind="live" />}
            asOf={<SourceLine src="factory_production" />}
          >
            <LiveSource src="factory_production" what="the machines">
              <div className="text-2xl font-semibold tabular-nums text-emerald-300">
                {running.length} of {Object.keys(byLine).length || running.length}
              </div>
              <ul className="mt-2 space-y-1 text-xs text-zinc-400">
                {running.length === 0 && <li>Nothing is on a machine right now.</li>}
                {running.map((r) => (
                  <li key={r.run_id} className="flex items-baseline gap-1.5">
                    <span className="m3-live inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                    <span className="font-medium text-zinc-300">{r.line}</span>
                    <span className="truncate">{r.sku}</span>
                  </li>
                ))}
              </ul>
            </LiveSource>
          </Panel>

          {/* made today */}
          <Panel
            title="Filled today"
            badge={<SimBadge kind="live" />}
            asOf={<SourceLine src="factory_production" />}
            note={prod?.mes_coverage_note ? maskDigits(prod.mes_coverage_note) : undefined}
          >
            <LiveSource src="factory_production" what="today's runs">
              <div className="text-2xl font-semibold tabular-nums">
                {orUnknown(prod?.made_today_l, litres)}
              </div>
              <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-400">
                <span>{orUnknown(prod?.made_today_cases, (v) => `${inr(v)} cases`)}</span>
                <span>
                  yesterday {orUnknown(prod?.made_yesterday_l, litres)}
                </span>
              </div>
            </LiveSource>
          </Panel>

          {/* trucks inside */}
          <Panel title="Trucks inside the gate" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_dispatch" />}>
            <LiveSource src="factory_dispatch" what="the gate">
              <div className="text-2xl font-semibold tabular-nums">
                {orUnknown(disp?.trucks_inside_count, (v) => inr(v))}
              </div>
              <ul className="mt-2 space-y-0.5 text-xs text-zinc-400">
                {(disp?.trucks_inside ?? []).slice(0, 5).map((t) => (
                  <li key={t.vehicle_no} className="flex items-baseline justify-between gap-2">
                    <span className="font-mono text-[11px] text-zinc-300">{t.vehicle_no}</span>
                    <span>
                      in {t.in_time ?? "—"} · {t.bill_count ?? 0} {plural(t.bill_count ?? 0, "bill", "bills")}
                    </span>
                  </li>
                ))}
              </ul>
              {(disp?.at_gate_today?.loaded_not_gone_litres ?? null) !== null && (
                <div className="mt-2 text-xs text-amber-300/80" title={disp?.at_gate_today?.loaded_not_gone_basis ?? ""}>
                  {litres(disp!.at_gate_today!.loaded_not_gone_litres!)} loaded but not through the gate
                </div>
              )}
            </LiveSource>
          </Panel>

          {/* bulk oil in the tanks */}
          <Panel
            title="Bulk oil in the tanks"
            badge={<NotLive p={P.tankDip(tanks?.reading_note)} />}
            asOf={<OwnStamp iso={tanks?.reading_at} what="dip read" staleAfterHours={30} fallback={<SourceLine src="exim" />} />}
          >
            <LiveSource src="exim" what="the tanks">
              <div className="text-2xl font-semibold tabular-nums">{orUnknown(tanks?.total_l, litres)}</div>
              <div className="mt-1 text-xs text-zinc-400">
                {orUnknown(tanks?.total_l, tonnes)} in {tanks?.tank_count ?? "—"} tanks ·{" "}
                {orUnknown(tanks?.utilisation_pct, pct1)} of what they hold
              </div>
              {/* the dip is a person's daily job; when it has not been done, say so —
                  a 49-hour-old level wearing "as of 12:51" is how this tile lied on 5 Sep */}
              {typeof tanks?.reading_age_hours === "number" && tanks.reading_age_hours > 30 && (
                <div className="mt-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-200">
                  No tank has been dipped since {tanks.reading_at ? hhmmDate(tanks.reading_at) : "the last reading"} —{" "}
                  {Math.round(tanks.reading_age_hours / 24)} {plural(Math.round(tanks.reading_age_hours / 24), "day", "days")} without a
                  reading. These litres are that old, whatever time this page was loaded.
                </div>
              )}
            </LiveSource>
          </Panel>
        </div>
      </div>

      {/* ── the pile, and the dispatch headline ───────────────────
          AC09: the headline is the OPEN book and the WAIT, not what left
          today. "Trucks that left today" used to sit here and it answers the
          wrong question — a good gate day with a growing book still means the
          godown fills up. What left today is in the fold at the bottom. */}
      <div className="grid gap-3 md:grid-cols-2">
        <Panel
          title="Billed but still in the godown — Oil"
          badge={<SimBadge kind="measured" />}
          asOf={<AsOf rec={live.storage} />}
          note={storage?.at_open.note ? maskDigits(storage.at_open.note) : undefined}
        >
          <Live rec={live.storage} what="the godown pile">
            <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <div className="text-2xl font-semibold tabular-nums">{orUnknown(pileOilL, litres)}</div>
              {pilePct !== null && (
                <div className="text-sm text-amber-300">
                  {pct1(pilePct)} of the godown{" "}
                  <NotLive p={P.ceiling(ceiling.text)} />
                </div>
              )}
            </div>
            <div className="mt-2 text-xs text-zinc-400">
              Whole godown right now: {orUnknown(storage?.at_open.physical_l, litres)} —{" "}
              {orUnknown(storage?.at_open.pct, pct1)} full against a limit of{" "}
              {orUnknown(ceiling.working_l, litres)} — the limit you gave us.
            </div>
            {storage?.at_open.clears_note && (
              <p className="mt-2 text-xs text-zinc-500">{maskDigits(storage.at_open.clears_note)}</p>
            )}
          </Live>
        </Panel>

        <Panel
          title="The open dispatch book — days of pendency"
          badge={<SimBadge kind="live" />}
          asOf={<AsOf rec={live.overview} />}
          note={pend.text ? maskDigits(pend.text) : undefined}
        >
          <Live rec={live.overview} what="the dispatch book">
            {d ? (
              <>
                <div className="flex flex-wrap items-baseline gap-x-8 gap-y-3">
                  <Stat
                    k="Oil — days of work in the book"
                    v={orUnknown(d.pendency_days_oil, days)}
                    tone="text-amber-300"
                    sub="at the pace the gate has been keeping"
                  />
                  <Stat k="All three books" v={orUnknown(d.pendency_days_all, days)} tone="text-zinc-400" />
                  <Stat k="Oil still in the godown" v={orUnknown(d.oil_pile_l, litres)} />
                  <Stat k="Open, all books" v={orUnknown(d.open_l_all_books, litres)} tone="text-zinc-400" />
                  <Stat k="Bills waiting" v={orUnknown(d.open_bills, (v) => inr(v))} />
                </div>
                {pileByStatus.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {pileByStatus.map(([k, v]) => (
                      <Pill key={k} tone={k === "PENDING" ? "amber" : "blue"}>
                        {k.toLowerCase()}: {orUnknown(v.litres, litres)}
                      </Pill>
                    ))}
                  </div>
                )}
                <p className="mt-2 text-xs text-zinc-500">
                  {d.basis ? maskDigits(d.basis) : ""}
                  {d.basis_missing ? ` ${maskDigits(d.basis_missing)}` : ""}
                </p>
                <p className="mt-1 text-xs text-amber-300/70">
                  The three books share one gate and are never added into one Oil headline.
                </p>
              </>
            ) : (
              <>
                <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
                  <Stat k="Litres, all books" v={orUnknown(pileAllBooksL, litres)} />
                  <Stat k="Bills" v={orUnknown(disp?.invoiced_not_dispatched?.bills, (v) => inr(v))} />
                  <Stat k="Worth" v={orUnknown(disp?.invoiced_not_dispatched?.value_inr, money)} />
                </div>
                <p className="mt-2 text-xs text-zinc-500">
                  This plan does not work out days of pendency — it was built before that was part of the rulebook.
                  What is shown is the open book straight off the gate system.
                </p>
              </>
            )}
          </Live>
        </Panel>
      </div>

      {/* ── how long a bill waits for a truck ──────────────────────── */}
      <div className="grid gap-3 md:grid-cols-2">
        <Panel
          title="Billed today, on a truck when?"
          badge={
            lagStatic ? (
              <NotLive p={P.lagStatic(lagCaveat)} />
            ) : (
              <SimBadge kind="measured" note="re-measured every day off the gate log, not carried" />
            )
          }
          asOf={<OwnStamp iso={lagOn} what="measured" staleAfterHours={lagStatic ? undefined : 30} fallback={<SourceLine src="factory_dispatch" />} />}
        >
          <Live rec={live.overview} what="the wait for a truck">
            {lagBookName && (
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Pill tone="green" title={d?.lag_book_say ?? undefined}>
                  {lagBookName} — the book this plan makes for
                </Pill>
                <span className="text-xs text-zinc-500">
                  the figures below are that book&rsquo;s own, and they are what the planner runs on
                </span>
              </div>
            )}
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <Stat k="Usual wait" v={orUnknown(lagMedian, days)} />
              <Stat k="Slowest one in ten" v={orUnknown(lagP90, days)} tone="text-amber-300" />
              <Stat k="Worst seen" v={orUnknown(lagMax, days)} tone="text-red-300" />
              <Stat k="Bills behind it" v={orUnknown(lagRows, (v) => inr(v))} />
              <Stat k="Measured over" v={lagWindow ?? "—"} />
            </div>
            {lagAllMedian != null && lagBookName && (
              <p className="mt-2 rounded border border-zinc-800 bg-zinc-900/40 px-2 py-1 text-xs text-zinc-400">
                All three books together: {days(lagAllMedian)} usually
                {lagAllP90 != null ? `, ${days(lagAllP90)} for the slowest one in ten` : ""}
                {lagAllRows != null ? ` over ${inr(lagAllRows)} bills` : ""} — shown because the
                gate is one gate, and NOT what the plan runs on. The three books are not one
                queue.
              </p>
            )}
            {d?.headline && <p className="mt-3 text-sm text-zinc-300">{maskDigits(d.headline)}</p>}
            <p className="mt-2 text-xs text-zinc-500">
              {maskDigits(lagCaveat ?? lag?.method ?? "")} The plan takes the usual wait and ignores the slow tail.
            </p>
          </Live>
        </Panel>

        <Panel
          title="The wait, book by book"
          badge={<SimBadge kind="measured" />}
          asOf={<OwnStamp iso={lagOn} what="measured" fallback={<AsOf rec={live.overview} />} />}
          note="Oil is the one that matters here. The other two are shown so a merged figure is never mistaken for it."
        >
          <Live rec={live.overview} what="the wait per book">
            {lagByCompany.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                    <th className="pb-1 font-normal">Book</th>
                    <th className="pb-1 text-right font-normal">Usual</th>
                    <th className="pb-1 text-right font-normal">One in ten</th>
                    <th className="pb-1 text-right font-normal">Worst</th>
                    <th className="pb-1 text-right font-normal">Bills</th>
                  </tr>
                </thead>
                <tbody>
                  {lagByCompany.map(([name, v]) => {
                    const isOil = name.includes("OIL");
                    return (
                      <tr key={name} className={isOil ? "text-zinc-100" : "text-zinc-400"}>
                        <td className="py-0.5">
                          <span className="mr-1.5">{name.replace("JIVO_", "").toLowerCase()}</span>
                          {isOil && <Pill tone="green" title="the planner's own company">ours</Pill>}
                        </td>
                        <td className="py-0.5 text-right tabular-nums">{orUnknown(v.median_days, days)}</td>
                        <td className="py-0.5 text-right tabular-nums">{orUnknown(v.p90_days, days)}</td>
                        <td className="py-0.5 text-right tabular-nums">{orUnknown(v.max_days, days)}</td>
                        <td className="py-0.5 text-right tabular-nums">{orUnknown(v.n, (x) => inr(x))}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-zinc-500">
                This plan does not split the wait by book. The figure on the left is every book together.
              </p>
            )}
          </Live>
        </Panel>
      </div>

      {/* ── what left the gate today: a detail, not a headline ────── */}
      <details className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
        <summary className="cursor-pointer text-sm font-semibold text-zinc-300">
          What left the gate today, by company (not a headline)
        </summary>
        <p className="mt-2 text-xs text-zinc-500">
          A good gate day does not mean the book is clearing — that is what the panel above measures. Three separate
          books share one gate and these are never added together: on a bad day the merged figure is nine-tenths
          Beverages and reads as Oil.
        </p>
        <div className="mt-3">
          <LiveSource src="factory_dispatch" what="the gate log">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                  <th className="pb-1 font-normal">Book</th>
                  <th className="pb-1 text-right font-normal">Litres</th>
                  <th className="pb-1 text-right font-normal">Trucks</th>
                  <th className="pb-1 text-right font-normal">Worth</th>
                </tr>
              </thead>
              <tbody>
                {byCompany.map((c) => {
                  const isOil = c.company.includes("OIL");
                  return (
                    <tr key={c.company} className={isOil ? "text-zinc-100" : "text-zinc-400"}>
                      <td className="py-0.5">
                        <span className="mr-1.5">{c.company.replace("JIVO_", "").toLowerCase()}</span>
                        {isOil && (
                          <Pill tone="green" title="the planner's own company">
                            ours
                          </Pill>
                        )}
                      </td>
                      <td className="py-0.5 text-right tabular-nums">{orUnknown(c.litres, litres)}</td>
                      <td className="py-0.5 text-right tabular-nums">{c.trucks ?? "—"}</td>
                      <td className="py-0.5 text-right tabular-nums">{orUnknown(c.value_inr, money)}</td>
                    </tr>
                  );
                })}
                {byCompany.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-2 text-zinc-500">
                      No truck has been through the gate on any book today.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            {oilDispatched !== null && (
              <p className="mt-2 text-xs text-zinc-500">
                Oil on its own: {litres(oilDispatched)} on {disp?.oil?.dispatched_today_trucks ?? 0}{" "}
                {plural(disp?.oil?.dispatched_today_trucks ?? 0, "truck", "trucks")}.
              </p>
            )}
          </LiveSource>
        </div>
      </details>

      {/* ── demand: what is really ordered ─────────────────────────── */}
      <div className="grid gap-3 md:grid-cols-3">
        <Panel
          title="Online platforms — open orders"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="ecom" />}
        >
          <LiveSource src="ecom" what="the online order book">
            <div className="text-2xl font-semibold tabular-nums text-sky-300">
              {orUnknown(ecom?.open_total_l, litres)}
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              {orUnknown(ecom?.open_value_ex_gst_total_inr ?? ecom?.open_value_ex_gst_inr, money)}{" "}
              before GST · every order still open and not yet expired ·
              quick-commerce {orUnknown(ecom?.open_qcomm_l, litres)}, Amazon{" "}
              {orUnknown(ecom?.open_amazon_l, litres)}
            </div>
            <ul className="mt-2 space-y-0.5 text-xs text-zinc-400">
              {Object.entries(ecom?.open_by_platform ?? {})
                .sort((a, b) => (b[1].litres ?? 0) - (a[1].litres ?? 0))
                .slice(0, 5)
                .map(([k, v]) => (
                  <li key={k} className="flex justify-between gap-2">
                    <span>
                      {k.toLowerCase()}
                      <span className="text-zinc-500">
                        {" "}
                        · {orUnknown(v.pos, (n) => `${n} ${plural(n, "PO", "POs")}`)}
                      </span>
                    </span>
                    <span className="tabular-nums">{orUnknown(v.litres, litres)}</span>
                  </li>
                ))}
            </ul>
            {/* Expiry decides whether an order counts, and its required-by date
                decides which month it lands in. Older paper is IN the figure --
                an unexpired PO is a real order whatever month it was raised in.
                What must stay visible is (a) how much of the book is older
                paper, (b) what fell out for being past expiry, and (c) how much
                is not due until after this month. */}
            <div className="mt-2 space-y-1 border-t border-zinc-800 pt-2 text-xs">
              {(ecom?.open_backlog_amazon_l ?? 0) > 0 && (
                <div className="text-zinc-400">
                  Included above: {orUnknown(ecom?.open_backlog_amazon_l, litres)} on{" "}
                  {orUnknown(ecom?.open_backlog_amazon_pos, (v) => `${v} ${plural(v, "PO", "POs")}`)}{" "}
                  raised in an earlier month — unexpired, so still a real order.
                </div>
              )}
              {(ecom?.dated_demand_total_l ?? 0) > 0 &&
                (ecom?.dated_demand_in_month_l ?? 0) > 0 &&
                (ecom?.dated_demand_total_l ?? 0) >
                  (ecom?.dated_demand_in_month_l ?? 0) && (
                  <div className="text-zinc-400">
                    Due this month: {orUnknown(ecom?.dated_demand_in_month_l, litres)}. The rest
                    is not required until next month, so the plan leaves it there.
                  </div>
                )}
              {(ecom?.open_expired_l ?? 0) > 0 && (
                <div className="text-amber-300/80">
                  Left out: {orUnknown(ecom?.open_expired_l, litres)} past its expiry date. The
                  platform still calls it open; it is not an order any more.
                </div>
              )}
            </div>
            {ecom?.targets?.carried_from && (
              <div className="mt-2 text-xs text-amber-300/80">
                Month target {orUnknown(ecom.targets.total_l, litres)}{" "}
                <NotLive p={P.targetsCarried(ecom.targets.carried_from)} />
              </div>
            )}
          </LiveSource>
        </Panel>

        <Panel
          title="Shops and distributors — open orders"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="oms" />}
          note={oms?.open_total?.headline_note ? maskDigits(oms.open_total.headline_note) : undefined}
        >
          <LiveSource src="oms" what="the order book">
            <div className="text-2xl font-semibold tabular-nums text-emerald-300">
              {orUnknown(oms?.open_total?.litres, litres)}
            </div>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-400">
              <span>{orUnknown(oms?.open_total?.count, (v) => `${inr(v)} ${plural(v, "order", "orders")}`)}</span>
              <span>{orUnknown(oms?.open_total?.amount_inr, money)}</span>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-zinc-500">Per litre, as billed</div>
                <div className="tabular-nums text-zinc-300">
                  {orUnknown(oms?.open_total?.rs_per_l, (v) => `₹${inr(v)}/L`)}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-zinc-500">Per litre, odd prices dropped</div>
                <div className="tabular-nums text-zinc-300">
                  {orUnknown(oms?.open_total?.rs_per_l_ex_outliers, (v) => `₹${inr(v)}/L`)}
                </div>
              </div>
            </div>
            {oms?.company_scope && oms.company_scope.clean === false && (
              <p className="mt-2 text-xs text-amber-300/80">
                {maskDigits(oms.company_scope.note ?? "")}
              </p>
            )}
          </LiveSource>
        </Panel>

        <Panel
          title="Arrived at the gate today"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="factory_inbound" />}
        >
          <LiveSource src="factory_inbound" what="the inward gate">
            <div className="text-2xl font-semibold tabular-nums">
              {orUnknown(inb?.arrived_today_count, (v) => `${inr(v)} ${plural(v, "load", "loads")}`)}
            </div>
            <div className="mt-2 space-y-1 text-xs text-zinc-400">
              <div>
                Waiting on quality: {orUnknown(inb?.in_qc_count, (v) => `${inr(v)} ${plural(v, "load", "loads")}`)} ·
                bulk oil {orUnknown(inb?.bulk_oil_pending_mt, (v) => `${inr(v)} T`)}
              </div>
              <div>
                Packaging waiting: {orUnknown(inb?.packaging_pending_pcs, (v) => `${inr(v)} pcs`)}
              </div>
              {inb?.bulk_oil_oldest_wait_hours != null && (
                <div className="text-amber-300/80">
                  Longest wait {Math.round(inb.bulk_oil_oldest_wait_hours)} hours. {inb.notes?.qc_speed ?? ""}
                </div>
              )}
            </div>
            {inb?.qc_counts && (
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
                <NotLive p={P.allTime(inb.notes?.qc_counts_scope)} />
                <span>
                  quality checks done {inr(inb.qc_counts.completed ?? 0)} · rejected {inr(inb.qc_counts.rejected ?? 0)}
                </span>
              </div>
            )}
          </LiveSource>
        </Panel>
      </div>

      <p className="text-xs text-zinc-500">
        Every tile above is the plant, not a plan.{" "}
        <Link href="/build" className="underline underline-offset-2 hover:text-zinc-300">
          What is on each machine right now
        </Link>{" "}
        ·{" "}
        <Link href="/storage" className="underline underline-offset-2 hover:text-zinc-300">
          how the godown fills up from here
        </Link>
        .
      </p>
    </div>
  );
}
