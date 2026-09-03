"use client";

// The flat floor plan — what /floor draws when the browser cannot give us 3D.
//
// This is NOT a "sorry, no 3D" box. It carries the same information the 3D view
// does: one pad per machine, height by hours, colour by oil, a live dot where a
// machine is filling now, the godown against its limit, and the trucks at the
// gate split into ordered and expected.

import { IDLE_COLOR, oilColor } from "../lib/webgl";
import type { FloorMachine } from "./FloorScene";
import { inr, litres, pct1, plural } from "../lib/fmt";

export default function Floor2D({
  machines, shiftHours, storagePct, storagePhysicalL, ceilingL, peakL, soldShare, loadsReal, loadsForecast,
  onPick,
}: {
  machines: FloorMachine[];
  shiftHours: number;
  storagePct: number;
  storagePhysicalL: number;
  ceilingL: number;
  peakL: number;
  soldShare: number;
  loadsReal: number;
  loadsForecast: number;
  onPick?: (name: string | null) => void;
}) {
  const shiftH = Math.max(1, shiftHours);
  const cap = Math.max(1, peakL);
  const fillFrac = Math.min(1.2, storagePhysicalL / cap);
  const soldFrac = fillFrac * Math.max(0, Math.min(1, soldShare));
  const freeFrac = Math.max(0, fillFrac - soldFrac);
  const ceilFrac = Math.min(1, ceilingL / cap);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
      <div className="mb-3 text-xs text-zinc-400">
        A flat plan of the same floor. Pad height is the hours the plan puts on that machine; the colour is the oil on
        it. Green dot means it is filling right now.
      </div>

      <div className="grid gap-4 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        {/* machines */}
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
          <div className="mb-2 text-[10px] uppercase tracking-wider text-zinc-500">The filling hall</div>
          <div className="flex h-56 items-end gap-3">
            {machines.map((m) => {
              const h = Math.max(4, (m.hours / shiftH) * 100);
              return (
                <button
                  key={m.name}
                  type="button"
                  onClick={() => onPick?.(m.name)}
                  title={`${m.name} — ${m.hours.toFixed(1)} h, ${litres(m.litres)}, ${m.runs} ${plural(
                    m.runs, "run", "runs",
                  )}${m.oilName ? `, on ${m.oilName}` : ""}${m.flushes ? `, ${m.flushes} oil ${plural(m.flushes, "change", "changes")}` : ""}`}
                  className="group flex flex-1 flex-col items-center justify-end gap-1 outline-none"
                >
                  {m.flushes > 0 && <span className="h-1.5 w-1.5 rounded-full bg-amber-400" title="oil change" />}
                  <div
                    className="w-full rounded-t transition-all group-hover:brightness-125"
                    style={{ height: `${h}%`, background: m.hours > 0 ? oilColor(m.oilName) : IDLE_COLOR }}
                  />
                  <div className="flex items-center gap-1 text-[10px] text-zinc-400">
                    {m.liveNow && <span className="m3-live inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />}
                    <span className="max-w-[6rem] truncate">{m.name}</span>
                  </div>
                </button>
              );
            })}
            {machines.length === 0 && <p className="text-sm text-zinc-500">No machine list yet.</p>}
          </div>
        </div>

        {/* godown + gate */}
        <div className="space-y-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
            <div className="mb-2 text-[10px] uppercase tracking-wider text-zinc-500">The godown</div>
            <div className="relative h-40 rounded border border-zinc-700 bg-zinc-950">
              <div
                className="absolute inset-x-0 border-t border-dashed border-red-500/80"
                style={{ bottom: `${ceilFrac * 100}%` }}
              >
                <span className="absolute -top-4 right-1 text-[10px] text-red-300">limit — a guess</span>
              </div>
              <div className="absolute inset-x-0 bottom-0 flex flex-col-reverse">
                <div
                  className={storagePct >= 100 ? "bg-red-500" : storagePct >= 95 ? "bg-red-400/80" : "bg-zinc-600"}
                  style={{ height: `${freeFrac * 160}px` }}
                />
                <div className="bg-amber-500/80" style={{ height: `${soldFrac * 160}px` }} />
              </div>
            </div>
            <div className="mt-2 flex flex-wrap justify-between gap-2 text-[11px]">
              <span className={storagePct >= 95 ? "text-red-300" : "text-zinc-400"}>
                {litres(storagePhysicalL)} · {pct1(storagePct)} of the limit
              </span>
              <span className="text-amber-300">amber = already sold</span>
            </div>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
            <div className="mb-2 text-[10px] uppercase tracking-wider text-zinc-500">At the gate</div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-emerald-300">
                {inr(loadsReal)} ordered {plural(loadsReal, "load", "loads")}
              </span>
              <span className="rounded bg-violet-500/10 px-2 py-0.5 text-violet-300">
                {inr(loadsForecast)} expected — nobody ordered them
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
