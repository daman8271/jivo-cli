"use client";

// /storage — the godown.
//
// NOW: the pile as it stands, split PENDING / BOOKED / loaded-but-not-gone, by
//      company and by room where the heavy read gave them, plus the measured
//      invoice→truck lag (badged: measured once, carried).
// FORWARD: the planner's day-by-day curve against Daman's DECLARED ceiling.

import { asHonesty, asState, asStorage, useLive } from "../lib/live";
import { ceilingRule, maskDigits, P, standingRule } from "../lib/labels";
import { dlabel, inr, litres, money, orUnknown, pct, pct1, plural } from "../lib/fmt";
import { AsOf, Live, LiveSource, NotLive, SourceLine } from "./Freshness";
import { Card, Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";

export default function StorageClient() {
  const live = useLive(["storage", "state", "honesty"]);
  const S = asStorage(live.storage);
  const st = asState(live.state);
  const h = asHonesty(live.honesty);
  const ceiling = ceilingRule(h);
  const standing = standingRule(h);

  const disp = st?.factory_dispatch;
  const pile = disp?.invoiced_not_dispatched;
  const byStatus = Object.entries(pile?.by_status ?? {});
  const byCompany = Object.entries(pile?.by_company ?? {});
  const byRoom = Object.entries(pile?.godown_rooms_only ?? {});
  const lag = disp?.lag_note;

  const series = S?.series ?? [];
  const maxPhys = Math.max(1, ...series.map((s) => s.physical_l), S?.ceiling.peak_l ?? 0);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Godown</h1>
        <SimBadge kind="measured" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        Two rooms hold finished goods. Most of what is in them on a bad day is already sold — billed, waiting for a
        truck. The limit they are measured against is the one you gave us, and it is named as yours everywhere it
        appears.
      </p>

      {/* ── now ─────────────────────────────────────────────────── */}
      <div className="mt-6 flex justify-end">
        <AsOf rec={live.storage} />
      </div>
      <div className="mt-1.5 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Live rec={live.storage} what="the godown">
          {S && (
            <>
              <Card
                title="In the godown now"
                value={litres(S.at_open.physical_l)}
                badge={<SimBadge kind="measured" />}
                sub={`${pct1(S.at_open.pct)} of the limit`}
                tone={S.at_open.pct >= 95 ? "text-red-400" : S.at_open.pct >= 80 ? "text-amber-300" : ""}
              />
              <Card
                title="Of that, already sold"
                value={litres(S.at_open.billed_not_gone_l)}
                badge={<SimBadge kind="measured" />}
                sub={standing.pctOfCeiling !== null ? `${pct1(standing.pctOfCeiling)} of the whole godown, billed and waiting for a truck` : undefined}
                tone="text-amber-300"
              />
              <Card
                title="Still unsold stock"
                value={litres(S.at_open.fg_l)}
                badge={<SimBadge kind="measured" />}
                sub="finished goods with no bill against them yet"
              />
              <Card
                title="The limit"
                value={litres(S.ceiling.working_l)}
                badge={<NotLive p={P.ceiling(S.ceiling.source)} />}
                sub={`up to ${litres(S.ceiling.peak_l)} packed tight — ${
                  S.ceiling.declared_by ? `your limit, ${S.ceiling.declared_by}` : "your own limit"
                }`}
                tone="text-zinc-400"
              />
            </>
          )}
        </Live>
      </div>

      {S?.at_open.note && (
        <p className="mt-3 max-w-4xl text-xs text-zinc-400">{maskDigits(S.at_open.note)}</p>
      )}

      {/* ── the pile, split every way the plant gives us ─────────── */}
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Panel
          title="The pile, split"
          badge={<SimBadge kind="live" />}
          asOf={<SourceLine src="factory_dispatch" />}
          note={pile?.basis ? maskDigits(pile.basis) : undefined}
        >
          <LiveSource src="factory_dispatch" what="the dispatch book">
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <Stat k="All three books" v={orUnknown(pile?.litres, litres)} />
              <Stat k="Bills" v={orUnknown(pile?.bills, (v) => inr(v))} />
              <Stat k="Worth" v={orUnknown(pile?.value_inr, money)} />
              <Stat
                k="Loaded, not through the gate"
                v={orUnknown(disp?.at_gate_today?.loaded_not_gone_litres, litres)}
                tone="text-amber-300"
              />
            </div>

            <div className="mt-3">
              <div className="text-[10px] uppercase tracking-wider text-zinc-500">By stage</div>
              <div className="mt-1 flex flex-wrap gap-2">
                {byStatus.map(([k, v]) => (
                  <Pill key={k} tone={k === "PENDING" ? "amber" : "blue"}>
                    {k.toLowerCase()} {orUnknown(v.litres, litres)}
                  </Pill>
                ))}
                {byStatus.length === 0 && <span className="text-xs text-zinc-500">not split this cycle</span>}
              </div>
            </div>

            <div className="mt-3">
              <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                By company — never added together
              </div>
              {byCompany.length === 0 ? (
                <p className="mt-1 text-xs text-zinc-500">
                  The company split only comes back on the slower read. The all-books figure above is all three
                  together — it is not Oil.
                </p>
              ) : (
                <table className="mt-1 w-full text-sm">
                  <tbody>
                    {byCompany
                      .sort((a, b) => (b[1].litres ?? 0) - (a[1].litres ?? 0))
                      .map(([k, v]) => (
                        <tr key={k} className={k.includes("OIL") ? "" : "text-zinc-400"}>
                          <td className="py-0.5">{k.replace("JIVO_", "").toLowerCase()}</td>
                          <td className="py-0.5 text-right tabular-nums">{orUnknown(v.litres, litres)}</td>
                          <td className="py-0.5 text-right tabular-nums text-zinc-500">{v.bills ?? "—"} bills</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
            </div>

            {byRoom.length > 0 && (
              <div className="mt-3">
                <div className="text-[10px] uppercase tracking-wider text-zinc-500">By room</div>
                <table className="mt-1 w-full text-sm">
                  <tbody>
                    {byRoom
                      .sort((a, b) => (b[1].litres ?? 0) - (a[1].litres ?? 0))
                      .map(([k, v]) => (
                        <tr key={k}>
                          <td className="py-0.5 font-mono text-[11px]">{k}</td>
                          <td className="py-0.5 text-right tabular-nums">{orUnknown(v.litres, litres)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </LiveSource>
        </Panel>

        <Panel
          title="How long after billing does the truck leave?"
          badge={<NotLive p={P.lagStatic(lag?.caveat)} />}
          asOf={<SourceLine src="factory_dispatch" />}
          note={S?.invoice_truck_note ? maskDigits(S.invoice_truck_note) : undefined}
        >
          <LiveSource src="factory_dispatch" what="the lag">
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <Stat k="Usual" v={orUnknown(lag?.median_days, (v) => `${v} ${plural(v, "day", "days")}`)} />
              <Stat k="Average" v={orUnknown(lag?.mean_days, (v) => `${v.toFixed(1)} days`)} />
              <Stat k="Nine in ten inside" v={orUnknown(lag?.p90_days, (v) => `${v} days`)} tone="text-amber-300" />
              <Stat k="Worst" v={orUnknown(lag?.max_days, (v) => `${v} days`)} tone="text-red-300" />
              <Stat k="Rows measured" v={orUnknown(lag?.rows, (v) => inr(v))} />
            </div>
            <p className="mt-2 text-xs text-zinc-500">{maskDigits(lag?.method ?? "")}</p>
            <p className="mt-1 text-xs text-amber-300/70">{maskDigits(lag?.caveat ?? "")}</p>
          </LiveSource>
        </Panel>
      </div>

      {/* ── forward: the curve ──────────────────────────────────── */}
      <div className="mt-4">
        <Panel
          title="How full it gets from here"
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.storage} />}
          note="Grey is stock nobody has billed. Amber is billed and waiting for a truck. The red line is the limit you gave us."
        >
          <Live rec={live.storage} what="the godown curve">
            {S && (
              <>
                <div className="relative h-64">
                  {/* ceiling markers */}
                  <div
                    className="absolute inset-x-0 border-t border-dashed border-red-500/70"
                    style={{ bottom: `${(S.ceiling.working_l / maxPhys) * 100}%` }}
                  >
                    <span className="absolute -top-4 right-0 text-[10px] text-red-300">
                      limit {litres(S.ceiling.working_l)} — yours
                    </span>
                  </div>
                  <div
                    className="absolute inset-x-0 border-t border-dotted border-red-500/40"
                    style={{ bottom: `${(S.ceiling.peak_l / maxPhys) * 100}%` }}
                  >
                    <span className="absolute -top-4 right-0 text-[10px] text-red-400/60">
                      packed tight {litres(S.ceiling.peak_l)}
                    </span>
                  </div>
                  <div className="flex h-full items-end gap-[3px]">
                    {series.map((s) => {
                      const fgH = (s.fg_in_godown_l / maxPhys) * 100;
                      const invH = (s.invoiced_not_trucked_l / maxPhys) * 100;
                      return (
                        <div
                          key={s.date}
                          className={`flex flex-1 flex-col justify-end ${s.working ? "" : "opacity-40"}`}
                          title={`${dlabel(s.date)} — ${litres(s.physical_l)} in the godown, ${pct1(
                            s.pct,
                          )} of the limit. Billed and waiting: ${litres(s.invoiced_not_trucked_l)}. Room left: ${litres(
                            s.headroom_l,
                          )}.`}
                        >
                          <div className="bg-amber-500/70" style={{ height: `${invH}%` }} />
                          <div
                            className={`${s.pct >= 100 ? "bg-red-500" : s.pct >= 95 ? "bg-red-400/80" : "bg-zinc-500"}`}
                            style={{ height: `${fgH}%` }}
                          />
                          <div className="mt-1 text-center text-[9px] text-zinc-600">{Number(s.date.slice(8, 10))}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs">
                  <Stat
                    k="Days at 95% or more"
                    v={`${S.days_ge_95 ?? 0} of ${series.length}`}
                    tone={(S.days_ge_95 ?? 0) > 0 ? "text-amber-300" : ""}
                  />
                  <Stat
                    k="Days over the limit"
                    v={`${(S.days_ge_100 ?? []).length}`}
                    tone={(S.days_ge_100 ?? []).length > 0 ? "text-red-300" : "text-emerald-300"}
                    sub={(S.days_ge_100 ?? []).map(dlabel).join(", ") || undefined}
                  />
                  {S.biggest_trucked_day && (
                    <Stat
                      k="Biggest day out"
                      v={dlabel(S.biggest_trucked_day.date)}
                      sub={litres(S.biggest_trucked_day.trucked_out_l)}
                    />
                  )}
                  {S.throttles && S.throttles.length > 0 && (
                    <Stat
                      k="Days the planner had to hold back"
                      v={`${S.throttles.length}`}
                      tone="text-amber-300"
                      sub={S.throttles.map((t) => dlabel(t.day)).join(", ")}
                    />
                  )}
                </div>

                {S.biggest_fall?.note && (
                  <p className="mt-3 text-xs text-zinc-500">{maskDigits(S.biggest_fall.note)}</p>
                )}
              </>
            )}
          </Live>
        </Panel>
      </div>
    </div>
  );
}
