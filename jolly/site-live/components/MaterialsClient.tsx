"use client";

// /materials — what is in QC, what is on the way, what is on order, and the
// components the plan runs out of. The order-by dates live on /order-by; this
// page is the stock position behind them.

import Link from "next/link";
import { asHonesty, asMaterials, asOverview, asState, useLive } from "../lib/live";
import { manualRule, maskDigits, P, unproducibleCodes } from "../lib/labels";
import { dlabel, inr, litres, money, orUnknown, pct1, plural, tonnes } from "../lib/fmt";
import { AsOf, Live, LiveSource, NotLive, OwnStamp, SourceLine } from "./Freshness";
import { Card, Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

export default function MaterialsClient() {
  const live = useLive(["materials", "state", "overview", "honesty"]);
  const M = asMaterials(live.materials);
  const st = asState(live.state);
  const o = asOverview(live.overview);
  const h = asHonesty(live.honesty);

  const inb = st?.factory_inbound;
  const exim = st?.exim;
  const tanks = exim?.tanks;
  const otw = exim?.inbound?.on_the_way ?? [];
  const loading = exim?.inbound?.under_loading ?? [];
  const contract = exim?.inbound?.in_contract ?? [];
  const bulkPos = exim?.open_bulk_pos ?? [];
  const cannotMake = unproducibleCodes(h);
  const manual = manualRule(h);
  /* the drums (R14): filled by hand, on no machine. They sit UNDER the
     "no machine can fill it" panel and are pointedly not in it — a drum is not
     a gap in the plant, it is a job somebody does with a hose. */
  const byHand = o?.manual_fill ?? [];
  const nonMovingPcs = o?.opening.packaging_in_non_moving_rooms_pcs ?? null;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Stock</h1>
        <SimBadge kind="live" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        Oil sits in quality control for days; packaging clears in about an hour. A tanker at the gate is not oil you can
        fill with.
      </p>

      {/* ── in QC right now ─────────────────────────────────────── */}
      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Panel title="Bulk oil waiting on quality" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_inbound" />}>
          <LiveSource src="factory_inbound" what="quality control">
            <div className="text-2xl font-semibold tabular-nums text-amber-300">
              {orUnknown(inb?.bulk_oil_pending_mt, (v) => `${inr(v)} T`)}
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              {orUnknown(inb?.bulk_oil_pending_lines, (v) => `${inr(v)} ${plural(v, "line", "lines")}`)}
              {inb?.bulk_oil_oldest_wait_hours != null && ` · longest ${Math.round(inb.bulk_oil_oldest_wait_hours)} h`}
            </div>
          </LiveSource>
        </Panel>
        <Panel title="Packaging waiting on quality" badge={<SimBadge kind="live" />} asOf={<SourceLine src="factory_inbound" />}>
          <LiveSource src="factory_inbound" what="quality control">
            <div className="text-2xl font-semibold tabular-nums">
              {orUnknown(inb?.packaging_pending_pcs, (v) => `${inr(v)} pcs`)}
            </div>
            <div className="mt-1 text-xs text-zinc-400">{inb?.notes?.qc_speed ? maskDigits(inb.notes.qc_speed) : ""}</div>
          </LiveSource>
        </Panel>
        <Panel title="Bulk oil in the tanks" badge={<NotLive p={P.tankDip(tanks?.reading_note)} />} asOf={<OwnStamp iso={tanks?.reading_at} what="dip read" staleAfterHours={30} fallback={<SourceLine src="exim" />} />}>
          <LiveSource src="exim" what="the tanks">
            <div className="text-2xl font-semibold tabular-nums">{orUnknown(tanks?.total_l, litres)}</div>
            <div className="mt-1 text-xs text-zinc-400">
              {orUnknown(tanks?.total_l, tonnes)} · room for {orUnknown(tanks?.free_headroom_l, litres)} more
            </div>
          </LiveSource>
        </Panel>
        <Panel title="Packaging counted" badge={nonMovingPcs !== null ? <NotLive p={P.nonMoving()} /> : <SimBadge kind="measured" />} asOf={<AsOf rec={live.overview} />}>
          <Live rec={live.overview} what="the packaging count">
            {o && (
              <>
                <div className="text-2xl font-semibold tabular-nums">{inr(o.opening.packaging_pieces)} pcs</div>
                {nonMovingPcs !== null && (
                  <div className="mt-1 text-xs text-amber-300/80">
                    {inr(nonMovingPcs)} pcs of that is counted in rooms that have not moved — it may not all be usable.
                  </div>
                )}
              </>
            )}
          </Live>
        </Panel>
      </div>

      {/* ── on the way ──────────────────────────────────────────── */}
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Panel
          title="Oil on its way in"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="exim" />}
          note="Only trucks already rolling are counted as arriving. Oil still under loading, or only under contract, is not."
        >
          <LiveSource src="exim" what="the inbound board">
            <div className="mb-3 flex flex-wrap gap-x-6 gap-y-2">
              <Stat k="On the way" v={`${otw.length} ${plural(otw.length, "truck", "trucks")}`} tone="text-emerald-300" />
              <Stat k="Under loading" v={`${loading.length}`} tone="text-amber-300" />
              <Stat k="Only in contract" v={`${contract.length}`} tone="text-zinc-400" />
            </div>
            <div className="max-h-72 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                    <th className="py-1 font-normal">Oil</th>
                    <th className="py-1 font-normal">Vendor</th>
                    <th className="py-1 text-right font-normal">Litres</th>
                    <th className="py-1 text-right font-normal">Due</th>
                  </tr>
                </thead>
                <tbody>
                  {[...otw, ...loading].map((t, i) => (
                    <tr key={`${t.id}-${i}`} className="border-t border-zinc-800/60">
                      <td className="py-1">{t.oil}</td>
                      <td className="py-1 max-w-[16rem] truncate text-zinc-400">{maskDigits(t.vendor)}</td>
                      <td className="py-1 text-right tabular-nums">{orUnknown(t.litres, litres)}</td>
                      <td className={`py-1 text-right ${t.days_late ? "text-red-300" : "text-zinc-400"}`}>
                        {dlabel(t.eta)}
                        {t.days_late ? ` · ${t.days_late} ${plural(t.days_late, "day", "days")} late` : ""}
                      </td>
                    </tr>
                  ))}
                  {otw.length + loading.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-2 text-zinc-500">
                        Nothing on the road.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </LiveSource>
        </Panel>

        <Panel
          title="Open bulk purchase orders"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="exim" />}
          note={exim?.open_bulk_pos_note ? maskDigits(exim.open_bulk_pos_note) : undefined}
        >
          <LiveSource src="exim" what="the purchase book">
            <div className="mb-2 text-sm text-zinc-400">
              {bulkPos.length} open {plural(bulkPos.length, "line", "lines")} shown of{" "}
              {orUnknown(exim?.pos_line_count, (v) => inr(v))} in the book.
            </div>
            <div className="max-h-72 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                    <th className="py-1 font-normal">PO</th>
                    <th className="py-1 font-normal">Material</th>
                    <th className="py-1 text-right font-normal">Drawn</th>
                  </tr>
                </thead>
                <tbody>
                  {bulkPos.slice(0, 40).map((p, i) => (
                    <tr key={`${p.po_number}-${i}`} className="border-t border-zinc-800/60">
                      <td className="py-1 font-mono text-[11px] text-zinc-400">{p.po_number}</td>
                      <td className="py-1 max-w-[16rem] truncate">{p.name}</td>
                      <td className="py-1 text-right tabular-nums">{orUnknown(p.load_qty, (v) => inr(v))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </LiveSource>
        </Panel>
      </div>

      {/* ── the shortfall the plan runs into ────────────────────── */}
      <div className="mt-4">
        <Live rec={live.materials} what="the materials list">
          {M && (
            <>
            <div className="mb-1.5 flex justify-end">
              <AsOf rec={live.materials} />
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <Card
                title="Materials the plan needs"
                value={inr(M.components_in_plan)}
                badge={<SimBadge kind="plan" />}
                sub={`${M.lead_days.oil}-day wait for oil, ${M.lead_days.packaging} for packaging`}
              />
              <Card
                title="Not enough for the whole plan"
                value={inr(M.under_100_cover)}
                tone="text-amber-300"
                badge={<SimBadge kind="plan" />}
              />
              <Card
                title="Must be ordered this week"
                value={inr(M.must_order_week1)}
                tone="text-amber-300"
                badge={<SimBadge kind="plan" />}
              />
              <Card
                title="Already too late to order"
                value={inr(M.already_late)}
                tone="text-red-400"
                badge={<SimBadge kind="plan" />}
                sub="the run slips whatever happens now"
              />
            </div>
            </>
          )}
        </Live>
      </div>

      {M?.opening_at_zero && M.opening_at_zero.length > 0 && (
        <div className="mt-4">
          <Panel
            title="At zero right now"
            badge={<SimBadge kind="measured" />}
            asOf={<AsOf rec={live.materials} />}
            note="None of these are in the godown at all. Nothing that needs them can be filled until they land."
          >
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                  <th className="py-1 font-normal">Material</th>
                  <th className="py-1 font-normal">Kind</th>
                  <th className="py-1 text-right font-normal">On order</th>
                </tr>
              </thead>
              <tbody>
                {M.opening_at_zero.map((z) => (
                  <tr key={z.code} className="border-t border-zinc-800/60">
                    <td className="py-1">
                      <span className="mr-2 font-mono text-[11px] text-zinc-500">{z.code}</span>
                      {z.name}
                    </td>
                    <td className="py-1 text-zinc-400">{z.kind.toLowerCase()}</td>
                    <td className={`py-1 text-right tabular-nums ${z.on_order > 0 ? "text-emerald-300" : "text-red-300"}`}>
                      {z.on_order > 0 ? inr(z.on_order) : "nothing on order"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>
      )}

      {M?.unproducible && M.unproducible.length > 0 && (
        <div className="mt-4">
          <Panel
            title="In the target, but no machine can fill it"
            badge={<SimBadge kind="plan" />}
            asOf={<AsOf rec={live.materials} />}
            note={M.unproducible_note}
          >
            <ul className="space-y-1 text-sm">
              {M.unproducible.map((u) => (
                <li key={u.code} className="flex flex-wrap items-baseline gap-2 border-t border-zinc-800/60 py-1 first:border-0">
                  <span className="font-mono text-[11px] text-zinc-500">{u.code}</span>
                  <span>{u.sku}</span>
                  <Pill tone="red">{u.reason}</Pill>
                  <span className="ml-auto tabular-nums text-zinc-400">{litres(u.plan_litres)}</span>
                  {u.value_est_rs && <span className="tabular-nums text-amber-300">{money(u.value_est_rs)}</span>}
                </li>
              ))}
            </ul>
            {cannotMake.length > 0 && (
              <p className="mt-2 text-xs text-zinc-500">
                Codes: {cannotMake.join(", ")}. Shown, never hidden.
              </p>
            )}
          </Panel>
        </div>
      )}

      {byHand.length > 0 && (
        <div className="mt-4">
          <Panel
            title="Filled by hand — not scheduled here"
            badge={<SimBadge kind="plan" />}
            asOf={<AsOf rec={live.overview} />}
            note={maskDigits(o?.manual_fill_note ?? manual.text ?? "")}
          >
            <ul className="space-y-1 text-sm">
              {byHand.map((m) => (
                <li key={m.code} className="flex flex-wrap items-baseline gap-2 border-t border-zinc-800/60 py-1 first:border-0">
                  <span className="font-mono text-[11px] text-zinc-500">{m.code}</span>
                  <span>{m.sku}</span>
                  <Pill tone="zinc">{maskDigits(m.display ?? manual.display ?? "")}</Pill>
                  <span className="ml-auto tabular-nums text-zinc-400">
                    {m.plan_litres != null ? litres(m.plan_litres) : "—"}
                  </span>
                  {m.plan_pieces != null && (
                    <span className="tabular-nums text-zinc-500">
                      {inr(m.plan_pieces)} {plural(m.plan_pieces, "drum", "drums")}
                    </span>
                  )}
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-zinc-500">
              These are in the month&rsquo;s target and they will be filled. No machine is missing for them.
            </p>
          </Panel>
        </div>
      )}

      <p className="mt-4 text-xs text-zinc-500">
        When each of these has to be ordered is on{" "}
        <Link href="/order-by" className="underline underline-offset-2 hover:text-zinc-300">
          Order by when
        </Link>
        .{M?.basis ? ` ${maskDigits(M.basis)}` : ""}
      </p>
    </div>
  );
}
