"use client";
import { useState } from "react";

export type StPoint = {
  n: number; date: string; dow: string; working: boolean;
  fg: number; inv: number; physical: number; ceiling: number;
  pct: number; headroom: number; made: number; shipped: number; throttle: boolean;
};

const nf = (n: number) => Math.round(n).toLocaleString("en-IN");
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso: string) => { const p = iso.split("-"); return `${+p[2]} ${MON[+p[1] - 1]}`; };

const W = 1000, H = 380, PL = 84, PR = 16, PT = 18, PB = 52;
const BASE = H - PB;

export default function StStorageChart({ points }: { points: StPoint[] }) {
  const [hi, setHi] = useState(0);
  const ceiling = points[0]?.ceiling ?? 0;
  const safety = ceiling * 0.95;
  const yMax = Math.ceil((ceiling * 1.08) / 50000) * 50000;

  const step = (W - PL - PR) / Math.max(points.length - 1, 1);
  const x = (i: number) => PL + i * step;
  const y = (v: number) => BASE - (v / yMax) * (BASE - PT);

  const line = (get: (p: StPoint) => number) =>
    points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(get(p)).toFixed(1)}`).join(" ");

  const fgArea = `${line((p) => p.fg)} L${x(points.length - 1).toFixed(1)},${BASE} L${x(0).toFixed(1)},${BASE} Z`;
  const invArea =
    `${line((p) => p.physical)} ` +
    points.slice().reverse().map((p, k) => `L${x(points.length - 1 - k).toFixed(1)},${y(p.fg).toFixed(1)}`).join(" ") +
    " Z";

  const ticks = [0, 200000, 400000, 600000, 800000].filter((t) => t <= yMax);
  const cur = points[hi];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-zinc-400 mb-2">
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-2.5 rounded-sm" style={{ background: "rgba(56,189,248,.38)", boxShadow: "inset 0 0 0 1px #38bdf8" }} />Finished goods in the godown</span>
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-2.5 rounded-sm" style={{ background: "repeating-linear-gradient(45deg,#f59e0b,#f59e0b 2px,transparent 2px,transparent 5px)", boxShadow: "inset 0 0 0 1px rgba(245,158,11,.7)" }} />Invoiced, still on the floor</span>
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-0.5" style={{ background: "#ef4444" }} />Ceiling {nf(ceiling)} L</span>
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-0.5" style={{ background: "#fbbf24", opacity: .9 }} />95% safety line</span>
        <span className="flex items-center gap-2 text-amber-300"><span>▲</span>Production throttled</span>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
        aria-label="Litres on the godown floor each day of August 2026 against the 827,000 litre ceiling">
        <defs>
          <pattern id="stHatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
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
        <path d={invArea} fill="url(#stHatch)" />
        <path d={line((p) => p.fg)} fill="none" stroke="#38bdf8" strokeWidth="1.5" opacity="0.85" />
        <path d={line((p) => p.physical)} fill="none" stroke="#fafafa" strokeWidth="2.4" />

        <line x1={PL} y1={y(safety)} x2={W - PR} y2={y(safety)} stroke="#fbbf24" strokeWidth="1.4" strokeDasharray="6 5" opacity="0.9" />
        <line x1={PL} y1={y(ceiling)} x2={W - PR} y2={y(ceiling)} stroke="#ef4444" strokeWidth="2" />
        <text x={W - PR} y={y(ceiling) - 7} textAnchor="end" fontSize="12" fill="#f87171">CEILING {nf(ceiling)} L</text>
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
          <div className="text-zinc-200 font-medium">{cur.working ? "Working day" : "Sunday — closed"}</div>
        </div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">On the floor</div><div className="text-zinc-100 font-semibold">{nf(cur.physical)} L <span className="text-zinc-500 font-normal">({cur.pct}%)</span></div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Of that, invoiced</div><div className="text-amber-300 font-semibold">{nf(cur.inv)} L</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Room left</div><div className="text-zinc-100 font-semibold">{nf(cur.headroom)} L</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Made</div><div className="text-zinc-100 font-semibold">{nf(cur.made)} L</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Shipped</div><div className="text-zinc-100 font-semibold">{nf(cur.shipped)} L</div></div>
      </div>
      <div className="mt-2 text-[11px] text-zinc-600">Hover or tap any day to move the readout.{cur.throttle ? " ▲ On this day production was capped to what could ship." : ""}</div>
    </div>
  );
}
