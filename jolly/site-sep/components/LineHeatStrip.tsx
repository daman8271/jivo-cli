"use client";

// Utilisation heat strip for /lines — one row per filling line, one column per
// planned day. Colour intensity = hours the line is busy (filling + changeover)
// out of the shift. Every number shown comes from data/lines.json + spine.json
// via the server page; this component only renders what it is handed.

import Link from "next/link";
import { useState } from "react";

export type HeatCell = {
  day: number; // 1-based day index, links to /days/{day}
  label: string; // "Tue 1 Sep"
  working: boolean;
  hours: number; // on-line hours: filling + changeover minutes
  fillHours: number; // filling only
  litres: number;
  runs: number;
  flushMin: number;
};
export type HeatRow = { line: string; cells: HeatCell[] };
export type HeatHead = { day: number; wd: string; working: boolean; util: number };

type Hover = { line: string; cell: HeatCell; x: number; y: number; below: boolean };

const inr = (n: number) => Math.round(n).toLocaleString("en-IN");
const HATCH =
  "repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0 3px, rgba(255,255,255,0) 3px 7px)";
const AMBER = "245,158,11";

export default function LineHeatStrip({
  rows,
  days,
  shift,
}: {
  rows: HeatRow[];
  days: HeatHead[];
  shift: number;
}) {
  const [hover, setHover] = useState<Hover | null>(null);
  const cols = `104px repeat(${days.length}, minmax(26px, 1fr))`;
  const hoverDay = hover ? hover.cell.day : null;

  function enter(e: { currentTarget: HTMLElement }, line: string, cell: HeatCell) {
    const r = e.currentTarget.getBoundingClientRect();
    const w = typeof window === "undefined" ? 1280 : window.innerWidth;
    const x = Math.min(Math.max(r.left + r.width / 2, 168), w - 168);
    const below = r.top < 250;
    setHover({ line, cell, x, y: below ? r.bottom : r.top, below });
  }

  return (
    <div className="relative">
      <div className="overflow-x-auto pb-1">
        <div className="min-w-[880px]">
          {/* day header */}
          <div className="grid items-end gap-x-[2px]" style={{ gridTemplateColumns: cols }}>
            <div />
            {days.map((d) => (
              <div key={d.day} className="text-center leading-tight">
                <div className={`text-[9px] ${d.working ? "text-zinc-600" : "text-zinc-700"}`}>{d.wd}</div>
                <div
                  className={`text-[11px] tabular-nums ${
                    hoverDay === d.day ? "text-amber-300" : d.working ? "text-zinc-400" : "text-zinc-600"
                  }`}
                >
                  {d.day}
                </div>
              </div>
            ))}
          </div>

          {/* one heat row per line */}
          {rows.map((row) => (
            <div key={row.line} className="grid items-center gap-x-[2px] mt-[3px]" style={{ gridTemplateColumns: cols }}>
              <div className="text-[11px] text-zinc-400 pr-2 truncate">{row.line}</div>
              {row.cells.map((c) => {
                const frac = Math.max(0, Math.min(1, c.hours / shift));
                const full = frac >= 0.97;
                return (
                  <Link
                    key={c.day}
                    href={`/days/${c.day}`}
                    aria-label={`${row.line}, ${c.label}, ${c.hours.toFixed(1)} of ${shift} hours`}
                    onMouseEnter={(e) => enter(e, row.line, c)}
                    onFocus={(e) => enter(e, row.line, c)}
                    onMouseLeave={() => setHover(null)}
                    onBlur={() => setHover(null)}
                    className={`relative block h-9 rounded-[3px] border transition-colors ${
                      hoverDay === c.day ? "border-zinc-500" : full ? "border-amber-500/40" : "border-zinc-800/70"
                    } ${c.working ? "bg-zinc-900/70" : "bg-zinc-900/30"}`}
                    style={{
                      ...(c.working ? null : { backgroundImage: HATCH }),
                      ...(c.hours > 0
                        ? { backgroundColor: `rgba(${AMBER},${(0.07 + 0.8 * frac).toFixed(3)})` }
                        : null),
                    }}
                  >
                    {c.hours <= 0 && c.working && (
                      <span className="absolute inset-x-1 bottom-1 h-[2px] bg-zinc-700 rounded" />
                    )}
                  </Link>
                );
              })}
            </div>
          ))}

          {/* all-lines utilisation, from the spine */}
          <div
            className="grid items-center gap-x-[2px] mt-2 pt-2 border-t border-zinc-900"
            style={{ gridTemplateColumns: cols }}
          >
            <div className="text-[10px] uppercase tracking-wider text-zinc-600 pr-2">All lines %</div>
            {days.map((d) => (
              <div
                key={d.day}
                className={`text-center text-[10px] tabular-nums ${
                  d.util >= 100 ? "text-amber-300 font-semibold" : d.util > 0 ? "text-zinc-400" : "text-zinc-700"
                }`}
              >
                {d.util > 0 ? d.util : "·"}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* legend */}
      <div className="flex items-center gap-3 mt-3 text-[10px] text-zinc-500">
        <span>quiet</span>
        <span className="flex gap-[3px]">
          {[0.2, 0.4, 0.6, 0.8, 1].map((f) => (
            <span
              key={f}
              className="h-3 w-6 rounded-[2px] border border-zinc-800"
              style={{ backgroundColor: `rgba(${AMBER},${(0.07 + 0.8 * f).toFixed(3)})` }}
            />
          ))}
        </span>
        <span>the full {shift} h shift</span>
        <span className="ml-3 inline-block h-3 w-6 rounded-[2px] border border-zinc-800" style={{ backgroundImage: HATCH }} />
        <span>Sunday, plant off</span>
      </div>

      {hover && (
        <div
          className="fixed z-[60] pointer-events-none"
          style={{
            left: hover.x,
            top: hover.y,
            transform: hover.below ? "translate(-50%, 10px)" : "translate(-50%, calc(-100% - 10px))",
          }}
        >
          <div className="w-[320px] rounded-lg border border-zinc-700 bg-zinc-950 shadow-2xl p-3">
            <div className="flex items-baseline justify-between">
              <div className="text-sm font-semibold">{hover.line}</div>
              <div className="text-[11px] text-zinc-500">{hover.cell.label}</div>
            </div>
            {hover.cell.hours > 0 ? (
              <div className="mt-1 text-[11px] text-zinc-400 tabular-nums space-y-0.5">
                <div>
                  {hover.cell.hours.toFixed(1)} h of {shift} h on the line —{" "}
                  {Math.round((hover.cell.hours / shift) * 100)}%
                </div>
                <div>
                  {hover.cell.fillHours.toFixed(1)} h filling · {hover.cell.flushMin} min changeover ·{" "}
                  {hover.cell.runs} {hover.cell.runs === 1 ? "run" : "runs"}
                </div>
                <div>{inr(hover.cell.litres)} L planned</div>
              </div>
            ) : (
              <div className="mt-1 text-[11px] text-zinc-500">
                {hover.cell.working ? "Nothing planned on this line." : "Sunday — the plant is off."}
              </div>
            )}
            <div className="mt-2 pt-2 border-t border-zinc-800 text-[10px] text-zinc-600">
              Planned, not run — click to open the day
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
