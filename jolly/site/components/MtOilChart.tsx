"use client";
import { useState } from "react";

export type MtOilPoint = { n: number; date: string; dow: string; working: boolean; oil: number; landed: number };

const nf = (n: number) => Math.round(n).toLocaleString("en-IN");
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso: string) => { const p = iso.split("-"); return `${+p[2]} ${MON[+p[1] - 1]}`; };

const W = 1000, H = 300, PL = 90, PR = 16, PT = 18, PB = 46;
const BASE = H - PB;

export default function MtOilChart({ points }: { points: MtOilPoint[] }) {
  const [hi, setHi] = useState(0);
  const max = Math.max(...points.map((p) => p.oil));
  const yMax = Math.ceil((max * 1.1) / 500000) * 500000;
  const step = (W - PL - PR) / Math.max(points.length - 1, 1);
  const x = (i: number) => PL + i * step;
  const y = (v: number) => BASE - (v / yMax) * (BASE - PT);

  const path = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.oil).toFixed(1)}`).join(" ");
  const area = `${path} L${x(points.length - 1).toFixed(1)},${BASE} L${x(0).toFixed(1)},${BASE} Z`;
  const ticks: number[] = [];
  for (let t = 0; t <= yMax; t += yMax / 4) ticks.push(t);

  const cur = points[hi];
  const lowest = points.reduce((a, b) => (b.oil < a.oil ? b : a));
  const highest = points.reduce((a, b) => (b.oil > a.oil ? b : a));

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-zinc-400 mb-2">
        <span className="flex items-center gap-2"><span className="inline-block w-4 h-0.5 bg-emerald-400" />Loose oil on hand</span>
        <span className="flex items-center gap-2 text-emerald-300">● a tanker landed that day</span>
        <span>Thinnest: <span className="text-zinc-200">{nf(lowest.oil)} L</span> on {shortDate(lowest.date)}</span>
        <span>Fullest: <span className="text-zinc-200">{nf(highest.oil)} L</span> on {shortDate(highest.date)}</span>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
        aria-label="Loose oil on hand in litres, each day of August 2026">
        <defs>
          <linearGradient id="mtOilFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#34d399" stopOpacity="0.34" />
            <stop offset="100%" stopColor="#34d399" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {points.map((p, i) => !p.working && (
          <rect key={`s${p.n}`} x={x(i) - step / 2} y={PT} width={step} height={BASE - PT} fill="#ffffff" opacity="0.035" />
        ))}

        {ticks.map((t) => (
          <g key={t}>
            <line x1={PL} y1={y(t)} x2={W - PR} y2={y(t)} stroke="#3f3f46" strokeWidth="1" opacity="0.5" />
            <text x={PL - 10} y={y(t) + 4} textAnchor="end" fontSize="12" fill="#71717a">{nf(t)}</text>
          </g>
        ))}
        <text x={PL - 10} y={PT - 4} textAnchor="end" fontSize="11" fill="#52525b">litres</text>

        <path d={area} fill="url(#mtOilFill)" />
        <path d={path} fill="none" stroke="#34d399" strokeWidth="2.4" />
        <line x1={PL} y1={BASE} x2={W - PR} y2={BASE} stroke="#52525b" strokeWidth="1" />

        {points.map((p, i) => p.landed > 0 && <circle key={`l${p.n}`} cx={x(i)} cy={y(p.oil)} r="3.4" fill="#34d399" />)}

        <line x1={x(hi)} y1={PT} x2={x(hi)} y2={BASE} stroke="#a1a1aa" strokeWidth="1" strokeDasharray="3 4" />
        <circle cx={x(hi)} cy={y(cur.oil)} r="5" fill="#fafafa" />

        {points.map((p, i) => (
          <g key={p.n}>
            <text x={x(i)} y={BASE + 18} textAnchor="middle" fontSize="10" fill={i === hi ? "#fafafa" : p.working ? "#71717a" : "#52525b"}>{p.n}</text>
            <rect x={x(i) - step / 2} y={PT} width={step} height={BASE - PT + 24} fill="transparent"
              onMouseEnter={() => setHi(i)} onClick={() => setHi(i)} style={{ cursor: "crosshair" }} />
          </g>
        ))}
      </svg>

      <div className="mt-3 border-t border-zinc-800 pt-3 flex flex-wrap gap-x-8 gap-y-2 text-sm">
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">{cur.dow} {shortDate(cur.date)}</div><div className="text-zinc-200">{cur.working ? "Working day" : "Sunday — closed"}</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Loose oil on hand</div><div className="text-emerald-300 font-semibold text-lg">{nf(cur.oil)} L</div></div>
        <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Oil that landed</div><div className="text-zinc-100 font-semibold text-lg">{cur.landed ? `${nf(cur.landed)} L` : "—"}</div></div>
      </div>
    </div>
  );
}
