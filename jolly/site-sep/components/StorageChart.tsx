"use client";
import { useState } from "react";

// How full the godown is, day by day — the computer's PLAN for September (nothing
// here has happened). Adapted from the August site's StStorageChart; September adds
// the squeezed-limit line and plan wording. Every number arrives via props from
// data/*.json — nothing is typed here.
export type StoragePoint = {
  n: number; date: string; dow: string; working: boolean;
  fg: number; inv: number; physical: number; pct: number; headroom: number;
  made: number; shipped: number; throttle: boolean;
};

const nf = (n: number) => Math.round(n).toLocaleString("en-IN");
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso: string) => { const p = iso.split("-"); return `${+p[2]} ${MON[+p[1] - 1]}`; };

const W = 1000, H = 380, PL = 84, PR = 16, PT = 18, PB = 52;
const BASE = H - PB;

export default function StorageChart({ points, workingL, peakL }: { points: StoragePoint[]; workingL: number; peakL: number }) {
  const [hi, setHi] = useState(0);
  const ceiling = workingL;
  const safety = ceiling * 0.95;
  const yMax = Math.ceil((Math.max(ceiling, peakL) * 1.05) / 50000) * 50000;

  const step = (W - PL - PR) / Math.max(points.length - 1, 1);
  const x = (i: number) => PL + i * step;
  const y = (v: number) => BASE - (v / yMax) * (BASE - PT);

  const line = (get: (p: StoragePoint) => number) =>
    points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(get(p)).toFixed(1)}`).join(" ");

  const fgArea = `${line((p) => p.fg)} L${x(points.length - 1).toFixed(1)},${BASE} L${x(0).toFixed(1)},${BASE} Z`;
  const invArea =
    `${line((p) => p.physical)} ` +
    points.slice().reverse().map((p, k) => `L${x(points.length - 1 - k).toFixed(1)},${y(p.fg).toFixed(1)}`).join(" ") +
    " Z";

  const ticks: number[] = [];
  for (let t = 0; t <= yMax; t += 200000) ticks.push(t);
  const cur = points[hi];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-zinc-400 mb-2">
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-2.5 rounded-sm" style={{ background: "rgba(56,189,248,.38)", boxShadow: "inset 0 0 0 1px #38bdf8" }} />Stock in the godown, not yet billed</span>
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-2.5 rounded-sm" style={{ background: "repeating-linear-gradient(45deg,#f59e0b,#f59e0b 2px,transparent 2px,transparent 5px)", boxShadow: "inset 0 0 0 1px rgba(245,158,11,.7)" }} />Billed, truck not left yet</span>
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-0.5" style={{ background: "#ef4444" }} />Godown full — {nf(ceiling)} L (Daman&apos;s number, not measured)</span>
        {peakL > ceiling && (
          <span className="flex items-center gap-2"><span className="inline-block w-4 h-0.5" style={{ background: "#f87171", opacity: .8, backgroundImage: "repeating-linear-gradient(90deg,#f87171,#f87171 3px,transparent 3px,transparent 6px)" }} />Squeezed hard — {nf(peakL)} L (not measured)</span>
        )}
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-0.5" style={{ background: "#fbbf24", opacity: .9 }} />95% — nearly full</span>
        <span className="flex items-center gap-2 text-amber-300"><span>▲</span>Godown full, the plan made less</span>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
        aria-label={`Litres in the godown on each day of September 2026, against the ${nf(ceiling)} litre limit we take as full — Daman's number, not measured`}>
        <defs>
          <pattern id="sepStHatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="7" height="7" fill="#f59e0b" opacity="0.10" />
            <line x1="0" y1="0" x2="0" y2="7" stroke="#f59e0b" strokeWidth="2.4" opacity="0.6" />
          </pattern>
        </defs>

        {points.map((p, i) => !p.working && (
          <rect key={`sun${p.n}`} x={x(i) - step / 2} y={PT} width={step} height={BASE - PT} fill="#ffffff" opacity="0.035" />
        ))}

        {ticks.map((t) => (
          <g key={t}>
            <line x1={PL} y1={y(t)} x2={W - PR} y2={y(t)} stroke="#3f3f46" strokeWidth="1" opacity="0.5" />
            <text x={PL - 10} y={y(t) + 4} textAnchor="end" fontSize="12" fill="#71717a">{nf(t)}</text>
          </g>
        ))}
        <text x={PL - 10} y={PT - 4} textAnchor="end" fontSize="11" fill="#52525b">litres</text>

        <path d={fgArea} fill="rgba(56,189,248,0.28)" />
        <path d={invArea} fill="url(#sepStHatch)" />
        <path d={line((p) => p.fg)} fill="none" stroke="#38bdf8" strokeWidth="1.5" opacity="0.85" />
        <path d={line((p) => p.physical)} fill="none" stroke="#fafafa" strokeWidth="2.4" />

        <line x1={PL} y1={y(safety)} x2={W - PR} y2={y(safety)} stroke="#fbbf24" strokeWidth="1.4" strokeDasharray="6 5" opacity="0.9" />
        <line x1={PL} y1={y(ceiling)} x2={W - PR} y2={y(ceiling)} stroke="#ef4444" strokeWidth="2" />
        {peakL > ceiling && (
          <>
            <line x1={PL} y1={y(peakL)} x2={W - PR} y2={y(peakL)} stroke="#f87171" strokeWidth="1.4" strokeDasharray="3 5" opacity="0.8" />
            <text x={PL + 6} y={y(peakL) - 5} fontSize="11" fill="#f87171" opacity="0.85">squeezed hard {nf(peakL)} L — not measured</text>
          </>
        )}
        <text x={W - PR} y={y(ceiling) - 7} textAnchor="end" fontSize="12" fill="#f87171">GODOWN FULL {nf(ceiling)} L · DAMAN&apos;S NUMBER, NOT MEASURED</text>
        <text x={PL + 6} y={y(safety) - 6} fontSize="11" fill="#fbbf24" opacity="0.9">95% — {nf(safety)} L</text>

        <line x1={PL} y1={BASE} x2={W - PR} y2={BASE} stroke="#52525b" strokeWidth="1" />

        <line x1={x(hi)} y1={PT} x2={x(hi)} y2={BASE} stroke="#a1a1aa" strokeWidth="1" strokeDasharray="3 4" />
        <circle cx={x(hi)} cy={y(cur.physical)} r="4.5" fill="#fafafa" />

        {points.map((p, i) => (
          <g key={p.n}>
            {p.throttle && <text x={x(i)} y={BASE + 34} textAnchor="middle" fontSize="10" fill="#f59e0b">▲</text>}
            <text x={x(i)} y={BASE + 18} textAnchor="middle" fontSize="10"
              fill={i === hi ? "#fafafa" : p.working ? "#71717a" : "#52525b"}>{p.n}</text>
            <rect x={x(i) - step / 2} y={PT} width={step} height={BASE - PT + 36} fill="transparent"
              onMouseEnter={() => setHi(i)} onClick={() => setHi(i)} style={{ cursor: "crosshair" }} />
          </g>
        ))}
      </svg>

      <div className="mt-3 border-t border-zinc-800 pt-3 grid grid-cols-2 md:grid-cols-6 gap-3 text-sm">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-zinc-500">{cur.dow} {shortDate(cur.date)}</div>
          <div className="text-zinc-200 font-medium">{cur.working ? "Working day" : "Sunday — factory closed"}</div>
        </div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">In the godown (plan)</div><div className="text-zinc-100 font-semibold">{nf(cur.physical)} L <span className="text-zinc-500 font-normal">({cur.pct}% full)</span></div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Of that, billed — truck not left</div><div className="text-amber-300 font-semibold">{nf(cur.inv)} L</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Space left</div><div className="text-zinc-100 font-semibold">{nf(cur.headroom)} L</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Made (plan)</div><div className="text-zinc-100 font-semibold">{cur.made ? `${nf(cur.made)} L` : "—"}</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Billed (plan)</div><div className="text-zinc-100 font-semibold">{cur.shipped ? `${nf(cur.shipped)} L` : "—"}</div></div>
      </div>
      <div className="mt-2 text-[11px] text-zinc-600">
        Tap or hover on any day to see its numbers. All of this is the computer&apos;s plan — none of it has happened yet.
        {cur.throttle ? " ▲ On this day the godown was full, so the plan made less." : ""}
      </div>
    </div>
  );
}
