"use client";

// /floor — the plant drawn as a floor.
//
// The WebGL rule the spec makes an acceptance check: probe, retry ONCE after
// two seconds, and if it still will not draw, fall through to the flat 2D plan.
// Never the dead "can't draw 3D" box Daman hit on Mark 2.

import { useMemo, useState } from "react";
import { asDay, asHonesty, asLines, asMaterials, asSpine, asState, asStorage, dayId, useLive } from "../lib/live";
import { ceilingRule, maskDigits, P } from "../lib/labels";
import { dlabel, inr, litres, pct1, plural, weekdayShort } from "../lib/fmt";
import { FORCE_2D, oilColor, useWebGL } from "../lib/webgl";
import FloorScene, { type FloorMachine } from "./FloorScene";
import Floor2D from "./Floor2D";
import { AsOf, Live, NotLive, SourceLine } from "./Freshness";
import { Panel, Pill, Stat } from "./Card";
import SimBadge from "./SimBadge";
import type { DayDetail } from "../lib/types";

/** The DIFFERENT products that could not start that day. `blocked` is one row per
 *  ATTEMPT — a product that four machines could fill appends four of them — so its
 *  length is not a product count. gen publishes the count; a body written before it
 *  did is counted off the rows themselves rather than off their length. */
const stuckProducts = (d: DayDetail) =>
  d.blocked_products ?? new Set(d.blocked.map((b) => b.code)).size;

export default function FloorClient() {
  const [n, setN] = useState(1);
  const [picked, setPicked] = useState<string | null>(null);
  const id = dayId(n);
  const live = useLive([id, "spine", "storage", "lines", "materials", "state", "honesty"]);

  const day = asDay(live[id]);
  const spine = asSpine(live.spine) ?? [];
  const S = asStorage(live.storage);
  const L = asLines(live.lines);
  const M = asMaterials(live.materials);
  const st = asState(live.state);
  const h = asHonesty(live.honesty);
  const ceiling = ceilingRule(h);
  const gl = useWebGL();

  // RM code → oil name, off the materials list. Never guessed.
  const oilName = useMemo(() => {
    const map = new Map<string, string>();
    for (const r of M?.rows ?? []) if (r.kind === "OIL") map.set(r.code, r.name);
    return map;
  }, [M]);

  const runningNow = useMemo(
    () => new Set((st?.factory_production?.running_now ?? []).map((r) => r.line)),
    [st],
  );

  const machines: FloorMachine[] = useMemo(() => {
    const names = L?.lines.map((l) => l.name) ?? Object.keys(day?.line_hours ?? {});
    return names.map((name) => {
      const runs = (day?.runs ?? []).filter((r) => r.line === name);
      const top = runs.length ? runs.reduce((a, b) => (b.litres > a.litres ? b : a)) : null;
      return {
        name,
        hours: day?.line_hours?.[name] ?? 0,
        oilName: top?.oil ? (oilName.get(top.oil) ?? top.oil) : null,
        litres: runs.reduce((a, r) => a + r.litres, 0),
        runs: runs.length,
        flushes: runs.filter((r) => r.flush_min > 0).length,
        // "running right now" is only true of today — a later day cannot be live
        liveNow: n === 1 && runningNow.has(name),
      };
    });
  }, [L, day, oilName, runningNow, n]);

  const shiftHours = Math.max(1, ...machines.map((m) => m.hours));
  const soldShare =
    day && day.storage.physical_l > 0 ? day.storage.invoiced_not_trucked_l / day.storage.physical_l : 0;
  const pick = machines.find((m) => m.name === picked) ?? null;
  const last = spine.length ? spine[spine.length - 1].n : 1;
  const row = spine.find((s) => s.n === n) ?? null;

  const floorProps = {
    machines,
    shiftHours,
    storagePct: day?.storage.pct ?? S?.at_open.pct ?? 0,
    storagePhysicalL: day?.storage.physical_l ?? S?.at_open.physical_l ?? 0,
    ceilingL: day?.storage.ceiling_l ?? S?.ceiling.working_l ?? 1,
    peakL: day?.storage.peak_l ?? S?.ceiling.peak_l ?? 1,
    soldShare,
    loadsReal: day?.dispatched_real.length ?? 0,
    loadsForecast: day?.dispatched_forecast.length ?? 0,
    onPick: setPicked,
  };

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Floor map</h1>
        <SimBadge kind={n === 1 ? "live" : "plan"} />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {machines.length} {plural(machines.length, "machine", "machines")}, one godown, one truck gate. Drag to walk
        around; click a machine for its day. Block height is hours, not litres — a slow machine makes fewer litres in
        the same hours.
      </p>

      {/* day scrubber */}
      <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
        <button
          type="button"
          onClick={() => setN((v) => Math.max(1, v - 1))}
          className="rounded-md px-2 py-1 text-sm text-zinc-300 hover:bg-zinc-800 disabled:opacity-40"
          disabled={n <= 1}
        >
          ←
        </button>
        <input
          type="range"
          min={1}
          max={last}
          value={n}
          onChange={(e) => setN(Number(e.target.value))}
          className="h-1 flex-1 min-w-[12rem] accent-amber-400"
          aria-label="pick a day"
        />
        <button
          type="button"
          onClick={() => setN((v) => Math.min(last, v + 1))}
          className="rounded-md px-2 py-1 text-sm text-zinc-300 hover:bg-zinc-800 disabled:opacity-40"
          disabled={n >= last}
        >
          →
        </button>
        <div className="min-w-[9rem] text-sm">
          <span className="font-semibold">
            {row ? `${weekdayShort(row.weekday)} ${dlabel(row.date)}` : `Day ${n}`}
          </span>
          {n === 1 && <Pill tone="green">today, live</Pill>}
        </div>
        <AsOf rec={live[id]} />
      </div>

      {/* the floor */}
      <div className="mt-4">
        <Live rec={live[id]} what={`day ${n}`}>
          {gl.state === "checking" ? (
            <div className="flex h-[26rem] items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950 text-sm text-zinc-500 md:h-[32rem]">
              {gl.retrying ? "The 3D view did not start. Trying once more…" : "Starting the 3D view…"}
            </div>
          ) : gl.state === "ok" ? (
            <FloorScene {...floorProps} />
          ) : (
            <>
              <div className="mb-2 rounded-md border border-zinc-700 bg-zinc-900/60 px-3 py-1.5 text-xs text-zinc-300">
                This browser will not draw 3D{FORCE_2D ? " (turned off for this build)" : " — we tried twice"}. Here is
                the same floor, flat.
              </div>
              <Floor2D {...floorProps} />
            </>
          )}
        </Live>
      </div>

      {/* what is on the floor that day */}
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <Panel title="That day, in four numbers" badge={<SimBadge kind={n === 1 ? "live" : "plan"} />} asOf={<AsOf rec={live[id]} />}>
          <div className="flex flex-wrap gap-x-6 gap-y-2">
            <Stat k="Filled" v={day ? litres(day.made_litres) : "—"} />
            <Stat k="Machines busy" v={day ? `${day.line_util}%` : "—"} />
            <Stat
              k="Godown"
              v={day ? pct1(day.storage.pct) : "—"}
              tone={day && day.storage.pct >= 95 ? "text-red-300" : ""}
            />
            {/* the DIFFERENT products that could not start. day.blocked is one row per
                attempt — a product tried on four machines is four of them. */}
            <Stat
              k="Stuck products"
              v={day ? String(stuckProducts(day)) : "—"}
              tone={day && stuckProducts(day) ? "text-red-300" : ""}
              sub={day ? `${day.blocked.length} ${day.blocked.length === 1 ? "try" : "tries"} stopped` : undefined}
            />
          </div>
          <div className="mt-3">
            <NotLive p={P.ceiling(ceiling.text)} />
            <span className="ml-2 text-xs text-zinc-500">
              the limit these percentages are measured against is the one you gave us
            </span>
          </div>
        </Panel>

        <Panel title={pick ? pick.name : "Pick a machine"} badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live[id]} />}>
          {pick ? (
            <div className="space-y-2">
              <div className="flex flex-wrap gap-x-6 gap-y-2">
                <Stat k="Hours" v={pick.hours.toFixed(1)} />
                <Stat k="Litres" v={litres(pick.litres)} />
                <Stat k="Runs" v={String(pick.runs)} />
                <Stat k="Oil changes" v={String(pick.flushes)} tone={pick.flushes ? "text-amber-300" : ""} />
              </div>
              {pick.oilName && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="inline-block h-3 w-3 rounded" style={{ background: oilColor(pick.oilName) }} />
                  <span className="text-zinc-300">{pick.oilName}</span>
                </div>
              )}
              {pick.liveNow && <Pill tone="green">filling right now</Pill>}
              <button
                type="button"
                onClick={() => setPicked(null)}
                className="text-xs text-zinc-500 underline underline-offset-2 hover:text-zinc-300"
              >
                clear
              </button>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">Click a machine on the floor to see what it does that day.</p>
          )}
        </Panel>

        <Panel title="Oil on the machines that day" badge={<SimBadge kind="plan" />} asOf={<AsOf rec={live.materials} />}>
          <ul className="space-y-1 text-sm">
            {machines
              .filter((m) => m.oilName)
              .map((m) => (
                <li key={m.name} className="flex items-center gap-2">
                  <span className="inline-block h-3 w-3 shrink-0 rounded" style={{ background: oilColor(m.oilName) }} />
                  <span className="text-zinc-400">{m.name}</span>
                  <span className="ml-auto truncate text-zinc-300">{m.oilName}</span>
                </li>
              ))}
            {machines.every((m) => !m.oilName) && <li className="text-zinc-500">No machine is on oil that day.</li>}
          </ul>
          {S?.at_open.note && <p className="mt-2 text-xs text-zinc-500">{maskDigits(S.at_open.note)}</p>}
        </Panel>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-zinc-500">
        <span>Live machine state comes from the factory app:</span>
        <SourceLine src="factory_production" />
        <span>·</span>
        <span>
          {inr(runningNow.size)} {plural(runningNow.size, "machine", "machines")} filling at this moment
        </span>
      </div>
    </div>
  );
}
