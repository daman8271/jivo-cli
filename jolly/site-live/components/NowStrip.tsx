"use client";

// The NOW strip — the plant as the loop last saw it, a few minutes ago.
// Every tile carries its own "as of", and every tile that is fed by something
// other than a live read carries the badge that says so.

import Link from "next/link";
import {
  asHonesty, asState, asStorage, useLive,
} from "../lib/live";
import { ceilingRule, maskDigits, P, standingRule } from "../lib/labels";
import { inr, litres, money, orUnknown, pct, pct1, plural, tonnes } from "../lib/fmt";
import { AsOf, Live, LiveSource, NotLive, SourceLine } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

export default function NowStrip() {
  const live = useLive(["state", "storage", "honesty"]);
  const st = asState(live.state);
  const storage = asStorage(live.storage);
  const h = asHonesty(live.honesty);

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
  const lag = disp?.lag_note;

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
            asOf={<SourceLine src="exim" />}
          >
            <LiveSource src="exim" what="the tanks">
              <div className="text-2xl font-semibold tabular-nums">{orUnknown(tanks?.total_l, litres)}</div>
              <div className="mt-1 text-xs text-zinc-400">
                {orUnknown(tanks?.total_l, tonnes)} in {tanks?.tank_count ?? "—"} tanks ·{" "}
                {orUnknown(tanks?.utilisation_pct, pct1)} of what they hold
              </div>
            </LiveSource>
          </Panel>
        </div>
      </div>

      {/* ── the pile, split by company ─────────────────────────────── */}
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
          title="Trucks that left today — by company"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="factory_dispatch" />}
          note="Three separate books share one gate. These are never added together — on a bad day the merged figure is nine-tenths Beverages and reads as Oil."
        >
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
        </Panel>
      </div>

      {/* ── the all-books backlog, and the lag ─────────────────────── */}
      <div className="grid gap-3 md:grid-cols-2">
        <Panel
          title="The open dispatch book — all three companies"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="factory_dispatch" />}
          note={disp?.invoiced_not_dispatched?.basis ? maskDigits(disp.invoiced_not_dispatched.basis) : undefined}
        >
          <LiveSource src="factory_dispatch" what="the dispatch book">
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <Stat k="Litres, all books" v={orUnknown(pileAllBooksL, litres)} />
              <Stat k="Bills" v={orUnknown(disp?.invoiced_not_dispatched?.bills, (v) => inr(v))} />
              <Stat k="Worth" v={orUnknown(disp?.invoiced_not_dispatched?.value_inr, money)} />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {pileByStatus.map(([k, v]) => (
                <Pill key={k} tone={k === "PENDING" ? "amber" : "blue"}>
                  {k.toLowerCase()}: {orUnknown(v.litres, litres)}
                </Pill>
              ))}
            </div>
            <p className="mt-2 text-xs text-amber-300/70">
              This is all three books together and it is not dated — it is the whole open backlog. The Oil-only slice is
              the tile on the left.
            </p>
          </LiveSource>
        </Panel>

        <Panel
          title="Billed today, on a truck when?"
          badge={<NotLive p={P.lagStatic(lag?.caveat)} />}
          asOf={<SourceLine src="factory_dispatch" />}
        >
          <LiveSource src="factory_dispatch" what="the lag">
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <Stat k="Usual wait" v={orUnknown(lag?.median_days, (v) => `${v} ${plural(v, "day", "days")}`)} />
              <Stat k="Slowest nine in ten" v={orUnknown(lag?.p90_days, (v) => `${v} days`)} tone="text-amber-300" />
              <Stat k="Worst seen" v={orUnknown(lag?.max_days, (v) => `${v} days`)} tone="text-red-300" />
              <Stat k="Measured over" v={lag?.measured_window ?? "—"} />
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              {maskDigits(lag?.method ?? "")} The plan takes the usual wait and ignores the slow tail.
            </p>
          </LiveSource>
        </Panel>
      </div>

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
              before GST · quick-commerce {orUnknown(ecom?.open_qcomm_l, litres)}, Amazon this
              month {orUnknown(ecom?.open_amazon_sep_l, litres)}
            </div>
            <ul className="mt-2 space-y-0.5 text-xs text-zinc-400">
              {Object.entries(ecom?.open_by_platform ?? {})
                .sort((a, b) => (b[1].litres ?? 0) - (a[1].litres ?? 0))
                .slice(0, 5)
                .map(([k, v]) => (
                  <li key={k} className="flex justify-between gap-2">
                    <span>
                      {k.toLowerCase()}
                      {k === "AMAZON" && (
                        <span className="text-zinc-500"> · this month only</span>
                      )}
                    </span>
                    <span className="tabular-nums">{orUnknown(v.litres, litres)}</span>
                  </li>
                ))}
            </ul>
            {/* The Amazon litres deliberately kept OUT of the headline. They are
                real open POs; they are just dated before this month, so they must
                not drive this month's plan. Showing the total without this line
                let the page read as if Amazon's whole book were the month slice. */}
            {(ecom?.open_backlog_amazon_l ?? 0) > 0 && (
              <div className="mt-2 border-t border-zinc-800 pt-2 text-xs text-amber-300/80">
                Not in the figure above: {orUnknown(ecom?.open_backlog_amazon_l, litres)} of
                Amazon orders still open on{" "}
                {orUnknown(ecom?.open_backlog_amazon_pos, (v) => `${v} ${plural(v, "PO", "POs")}`)}{" "}
                dated before this month. Amazon&rsquo;s whole open book is{" "}
                {orUnknown(ecom?.open_amazon_all_l, litres)} on{" "}
                {orUnknown(ecom?.open_amazon_all_pos, (v) => `${v} ${plural(v, "PO", "POs")}`)}.
                Old orders are left out of the plan on purpose.
              </div>
            )}
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
