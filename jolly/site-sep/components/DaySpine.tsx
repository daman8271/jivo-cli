// The day strip for /days: four aligned per-day panels (made / billed /
// machines busy / godown) plus the clickable day-card grid. Server components, pure SVG+divs.
// All figures come from data/spine.json via props; only layout constants live here.
import Link from "next/link";
import type { SpineDay } from "../lib/types";
import { fmt, dlabel } from "../lib/data";

const LEFT = 118; // px, panel labels
const COLW = 27; // px per day column
const BARW = 15;
const PANEL_H = 46;
const PANEL_GAP = 20;
const TOP = 14;
const XAXIS_H = 26;

function storageColor(pct: number) {
  return pct >= 100 ? "#f87171" : pct >= 95 ? "#fbbf24" : "#a78bfa";
}

/** Four panels sharing the day x-axis. Sundays are shaded off; a day the godown is
 * full carries a red marker. Each panel scales to its own biggest day. */
export function SpineChart({ spine }: { spine: SpineDay[] }) {
  const n = spine.length;
  const W = LEFT + n * COLW + 8;
  const maxMade = Math.max(...spine.map((d) => d.made_l), 1);
  const maxShip = Math.max(...spine.map((d) => d.shipped_l), 1);
  const STOR_MAX = 108; // % scale so the 100% line sits inside the panel

  const panels: {
    key: string; label: string; sub: string; color: (d: SpineDay) => string;
    val: (d: SpineDay) => number; max: number; line100?: boolean;
  }[] = [
    { key: "made", label: "MADE", sub: `biggest day ${fmt(maxMade)} L`, color: () => "#f59e0b", val: (d) => d.made_l, max: maxMade },
    { key: "ship", label: "BILLED", sub: `biggest day ${fmt(maxShip)} L`, color: () => "#38bdf8", val: (d) => d.shipped_l, max: maxShip },
    { key: "util", label: "MACHINES BUSY", sub: "% of machine hours", color: () => "#34d399", val: (d) => d.util, max: 100 },
    { key: "stor", label: "GODOWN", sub: "% full (limit is Daman's number)", color: (d) => storageColor(d.storage_pct), val: (d) => d.storage_pct, max: STOR_MAX, line100: true },
  ];
  const H = TOP + panels.length * PANEL_H + (panels.length - 1) * PANEL_GAP + XAXIS_H;
  const colX = (i: number) => LEFT + i * COLW;
  const panelY = (p: number) => TOP + p * (PANEL_H + PANEL_GAP);

  return (
    <div className="relative w-max">
      <svg width={W} height={H} role="img" aria-label="The planned days: litres made, litres billed, machines busy and how full the godown is, day by day">
        {/* Sunday bands, full height */}
        {spine.map((d, i) =>
          d.working ? null : (
            <rect key={`off-${d.n}`} x={colX(i)} y={TOP - 6} width={COLW} height={H - TOP - XAXIS_H + 12} fill="#ffffff" opacity={0.035} rx={3} />
          ),
        )}
        {panels.map((p, pi) => {
          const y0 = panelY(pi);
          return (
            <g key={p.key}>
              <text x={0} y={y0 + 12} fill="#a1a1aa" fontSize={10} fontWeight={600} letterSpacing={1}>{p.label}</text>
              <text x={0} y={y0 + 25} fill="#52525b" fontSize={9}>{p.sub}</text>
              <line x1={LEFT - 6} y1={y0 + PANEL_H} x2={LEFT + n * COLW} y2={y0 + PANEL_H} stroke="#27272a" strokeWidth={1} />
              {p.line100 ? (
                <line
                  x1={LEFT - 6} x2={LEFT + n * COLW}
                  y1={y0 + PANEL_H - (100 / p.max) * PANEL_H}
                  y2={y0 + PANEL_H - (100 / p.max) * PANEL_H}
                  stroke="#f87171" strokeOpacity={0.55} strokeWidth={1} strokeDasharray="3 3"
                />
              ) : null}
              {spine.map((d, i) => {
                const v = p.val(d);
                const h = Math.max(v > 0 ? 1.5 : 0, (v / p.max) * PANEL_H);
                return (
                  <rect
                    key={`${p.key}-${d.n}`}
                    x={colX(i) + (COLW - BARW) / 2}
                    y={y0 + PANEL_H - h}
                    width={BARW}
                    height={h}
                    rx={1.5}
                    fill={p.color(d)}
                    opacity={d.working ? 0.85 : 0.35}
                  />
                );
              })}
              {/* red marker on the day(s) the godown is full */}
              {p.line100
                ? spine
                    .filter((d) => d.storage_pct >= 100)
                    .map((d) => (
                      <circle
                        key={`roof-${d.n}`}
                        cx={colX(spine.indexOf(d)) + COLW / 2}
                        cy={y0 + PANEL_H - (d.storage_pct / p.max) * PANEL_H - 5}
                        r={3}
                        fill="#f87171"
                      />
                    ))
                : null}
            </g>
          );
        })}
        {/* x axis: day numbers, Sundays dim */}
        {spine.map((d, i) => (
          <text
            key={`x-${d.n}`}
            x={colX(i) + COLW / 2}
            y={H - 10}
            textAnchor="middle"
            fontSize={9}
            fill={d.working ? "#71717a" : "#3f3f46"}
          >
            {d.n}
          </text>
        ))}
      </svg>
      {/* invisible per-day click targets over the columns */}
      <div className="absolute top-0 bottom-0 flex" style={{ left: LEFT, width: n * COLW }}>
        {spine.map((d) => (
          <Link
            key={`lnk-${d.n}`}
            href={`/days/${d.n}`}
            className="h-full hover:bg-white/5"
            style={{ width: COLW }}
            title={
              d.working
                ? `Day ${d.n} — ${dlabel(d.date)} (${d.weekday}) · made ${fmt(d.made_l)} L · billed ${fmt(d.shipped_l)} L · machines busy ${d.util}% · godown ${d.storage_pct}% full`
                : `Day ${d.n} — ${dlabel(d.date)} (${d.weekday}) · factory closed · godown ${d.storage_pct}% full`
            }
          />
        ))}
      </div>
    </div>
  );
}

/** Clickable card per day: the four bars in miniature plus the day's headline counts. */
export function SpineCards({ spine }: { spine: SpineDay[] }) {
  const maxMade = Math.max(...spine.map((d) => d.made_l), 1);
  const maxShip = Math.max(...spine.map((d) => d.shipped_l), 1);
  const Bar = ({ v, max, cls }: { v: number; max: number; cls: string }) => (
    <div className="h-1 w-full overflow-hidden rounded bg-zinc-800/80">
      <div className={`h-full rounded ${cls}`} style={{ width: `${Math.min(100, (v / max) * 100)}%` }} />
    </div>
  );
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5 xl:grid-cols-6">
      {spine.map((d) => {
        const roof = d.storage_pct >= 100;
        return (
          <Link
            key={d.n}
            href={`/days/${d.n}`}
            className={`rounded-lg border p-2.5 text-sm transition-colors hover:bg-zinc-800/80 ${
              d.working ? "border-zinc-800 bg-zinc-900/60" : "border-zinc-900 bg-zinc-950 text-zinc-500"
            } ${roof ? "ring-1 ring-red-500/60" : ""}`}
          >
            <div className="flex items-baseline justify-between">
              <div className="font-medium">
                {dlabel(d.date)} <span className="text-[10px] text-zinc-500">{d.weekday.slice(0, 3)}</span>
              </div>
              <div className="text-[10px] tabular-nums text-zinc-600">day {d.n}</div>
            </div>
            <div className="mt-1 text-xs tabular-nums text-zinc-400">
              {d.working ? (
                <>
                  {fmt(d.made_l)} L · {d.runs} runs
                </>
              ) : (
                `factory closed — ${d.weekday}`
              )}
            </div>
            <div className="mt-2 space-y-1">
              <Bar v={d.made_l} max={maxMade} cls="bg-amber-500/80" />
              <Bar v={d.shipped_l} max={maxShip} cls="bg-sky-400/80" />
              <Bar v={d.util} max={100} cls="bg-emerald-400/80" />
              <Bar v={Math.min(d.storage_pct, 108)} max={108} cls={roof ? "bg-red-400" : d.storage_pct >= 95 ? "bg-amber-400" : "bg-violet-400/80"} />
            </div>
            <div className="mt-2 flex flex-wrap gap-1 text-[10px] leading-none">
              {roof ? <span className="rounded bg-red-500/15 px-1 py-0.5 text-red-300">godown full — {d.storage_pct}%</span> : null}
              {!roof && d.storage_pct >= 95 ? <span className="rounded bg-amber-500/15 px-1 py-0.5 text-amber-300">godown almost full — {d.storage_pct}%</span> : null}
              {d.unblocked > 0 ? <span className="rounded bg-emerald-500/15 px-1 py-0.5 text-emerald-300">{d.unblocked} arrived, can run again</span> : null}
              {d.working && d.blocked > 0 ? <span className="rounded bg-zinc-800 px-1 py-0.5 text-zinc-400">{d.blocked} stuck</span> : null}
            </div>
          </Link>
        );
      })}
    </div>
  );
}

/** Chart legend + the godown-full note, computed from the spine itself. */
export function SpineLegend({ spine }: { spine: SpineDay[] }) {
  const roofDays = spine.filter((d) => d.storage_pct >= 100);
  const offDays = spine.filter((d) => !d.working);
  return (
    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-500">
      <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-amber-500/80" />made, litres</span>
      <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-sky-400/80" />billed, litres</span>
      <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-emerald-400/80" />machines busy %</span>
      <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-violet-400/80" />godown % full</span>
      <span className="text-zinc-600">
        shaded columns = {offDays.length} Sundays, factory closed
      </span>
      {roofDays.length > 0 ? (
        <span className="flex items-center gap-1.5 text-red-300/90">
          <span className="h-2 w-2 rounded-full bg-red-400" />
          godown full {roofDays.length === 1 ? "once" : `${roofDays.length} times`} (the limit is Daman&apos;s number, not measured):{" "}
          {roofDays.map((d) => `${dlabel(d.date)} (day ${d.n})`).join(", ")}
        </span>
      ) : null}
    </div>
  );
}
