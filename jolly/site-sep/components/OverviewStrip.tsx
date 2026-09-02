"use client";

import { useState } from "react";
import Link from "next/link";

// Slim slice of the spine, mapped by the server page — the client bundle never
// touches fs or the full data files. Every field is generator-computed.
export type StripDay = {
  n: number;
  date: string;
  weekday: string;
  working: boolean;
  made_l: number;
  value_rs: number;
  shipped_l: number;
  util: number;
  storage_pct: number;
  runs: number;
  blocked: number;
  real_rows: number;
  forecast_rows: number;
};

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const dlabel = (iso: string) => `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}`;

// Indian grouping, done by hand so the server and the browser always agree.
function inr(n: number) {
  const v = Math.round(Math.abs(n));
  const s = String(v);
  const sign = n < 0 ? "-" : "";
  if (s.length <= 3) return sign + s;
  return sign + s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + s.slice(-3);
}
function money(rs: number) {
  if (rs <= 0) return "—";
  // "lakh" spelled out — "₹x.x L" would read as litres on this site.
  return rs >= 1e7 ? `₹${(rs / 1e7).toFixed(2)} Cr` : `₹${(rs / 1e5).toFixed(2)} lakh`;
}
function band(pct: number) {
  return pct >= 95 ? "red" : pct >= 80 ? "amber" : "green";
}
const FILL: Record<string, string> = {
  red: "bg-red-500",
  amber: "bg-amber-500",
  green: "bg-emerald-500",
};

function Stat({ k, v, tone = "text-zinc-100" }: { k: string; v: string; tone?: string }) {
  return (
    <div className="min-w-[86px]">
      <div className="text-[10px] uppercase tracking-wider text-zinc-500">{k}</div>
      <div className={`text-sm font-medium tabular-nums mt-0.5 ${tone}`}>{v}</div>
    </div>
  );
}

export default function OverviewStrip({ days }: { days: StripDay[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(1, ...days.map((d) => d.made_l));
  const d = hover === null ? null : days[hover];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      {/* read-out — fixed height so nothing moves when you sweep across */}
      <div className="min-h-[62px] border-b border-zinc-800 pb-3 mb-4">
        {d === null ? (
          <div className="text-sm text-zinc-500 pt-3">
            Hover a day for its planned numbers. Click to open that day. Bar height is litres the plan makes; colour is
            how full the godown gets. Nothing here has happened yet.
          </div>
        ) : (
          <div className="flex flex-wrap items-start gap-x-6 gap-y-3">
            <div className="min-w-[110px]">
              <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                {d.working ? "Working day (planned)" : `${d.weekday} — plant off`}
              </div>
              <div className="text-sm font-semibold mt-0.5">
                {d.weekday.slice(0, 3)} {dlabel(d.date)}
              </div>
            </div>
            <Stat k="Made" v={d.made_l > 0 ? `${inr(d.made_l)} L` : "nothing"} />
            <Stat k="Value" v={money(d.value_rs)} />
            <Stat k="Shipped" v={d.shipped_l > 0 ? `${inr(d.shipped_l)} L` : "nothing"} />
            <Stat
              k="Lines"
              v={`${d.util}%`}
              tone={d.util >= 80 ? "text-emerald-300" : d.util >= 30 ? "text-amber-300" : "text-zinc-100"}
            />
            <Stat
              k="Godown"
              v={`${d.storage_pct}%`}
              tone={d.storage_pct >= 95 ? "text-red-300" : d.storage_pct >= 80 ? "text-amber-300" : "text-emerald-300"}
            />
            <Stat k="Runs" v={inr(d.runs)} />
            <Stat k="Blocked runs" v={inr(d.blocked)} tone={d.blocked > 0 ? "text-red-300" : "text-zinc-100"} />
            <Stat k="Real order rows" v={inr(d.real_rows)} />
            <Stat k="Forecast rows" v={inr(d.forecast_rows)} tone="text-sky-300" />
          </div>
        )}
      </div>

      {/* bars */}
      <div className="flex items-stretch gap-[3px] h-56">
        {days.map((x, i) => {
          const b = band(x.storage_pct);
          const h = x.made_l > 0 ? Math.max(1.5, (x.made_l / max) * 100) : 0;
          return (
            <Link
              key={x.date}
              href={`/days/${x.n}`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(i)}
              onBlur={() => setHover(null)}
              aria-label={`${dlabel(x.date)} — plan makes ${inr(x.made_l)} litres, godown ${
                x.storage_pct
              } per cent full`}
              className={`flex-1 flex flex-col justify-end rounded-sm transition-colors outline-none focus-visible:ring-1 focus-visible:ring-amber-400 ${
                x.working ? "" : "opacity-40"
              } ${hover === i ? "bg-zinc-800/70" : "hover:bg-zinc-800/40"}`}
            >
              {h > 0 ? (
                <div className={`w-full rounded-t-[2px] ${FILL[b]}`} style={{ height: `${h}%` }} />
              ) : (
                <div className="w-full h-[3px] bg-zinc-700" />
              )}
            </Link>
          );
        })}
      </div>

      {/* storage ribbon — reads even on the days nothing is made */}
      <div className="flex gap-[3px] mt-1.5">
        {days.map((x) => (
          <div
            key={x.date}
            className={`flex-1 h-[6px] rounded-[1px] ${FILL[band(x.storage_pct)]} ${x.working ? "" : "opacity-40"}`}
          />
        ))}
      </div>

      {/* day numbers */}
      <div className="flex gap-[3px] mt-1.5">
        {days.map((x, i) => (
          <div
            key={x.date}
            className={`flex-1 text-center text-[9px] tabular-nums ${
              x.working ? (hover === i ? "text-zinc-200" : "text-zinc-500") : "text-zinc-700"
            }`}
          >
            {x.n}
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mt-4 text-[11px] text-zinc-500">
        <span className="text-zinc-400">Godown fill:</span>
        <span className="flex items-center gap-1.5">
          <i className="w-3 h-3 rounded-[2px] bg-emerald-500 inline-block" /> under 80%
        </span>
        <span className="flex items-center gap-1.5">
          <i className="w-3 h-3 rounded-[2px] bg-amber-500 inline-block" /> 80–95%
        </span>
        <span className="flex items-center gap-1.5">
          <i className="w-3 h-3 rounded-[2px] bg-red-500 inline-block" /> 95% and over — nearly full: production gets
          capped to what can ship
        </span>
        <span className="flex items-center gap-1.5">
          <i className="w-3 h-3 rounded-[2px] bg-zinc-700 inline-block" /> nothing made
        </span>
        <span className="opacity-60">Sundays dimmed · every bar is a plan</span>
      </div>
    </div>
  );
}
