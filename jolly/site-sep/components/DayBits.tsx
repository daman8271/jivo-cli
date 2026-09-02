// Day-page building blocks for the September FORWARD PLAN site.
// Everything rendered here is fed from data/*.json (written only by scripts/gen-data.py);
// no business number is typed in this file — only layout constants and UI thresholds.
import Link from "next/link";
import { fmt } from "../lib/data";
import type { StorageDay } from "../lib/types";
import SimBadge from "./SimBadge";

const THBASE = "font-medium py-2 px-3 text-[11px] uppercase tracking-wider text-zinc-500 bg-zinc-900 sticky top-0";
export const TH = `${THBASE} text-left`;
export const THR = `${THBASE} text-right`;
export const TD = "py-2 px-3 border-t border-zinc-800/70 align-top";
export const NUM = "tabular-nums text-right whitespace-nowrap";

/** One big number, read across a room. */
export function DayStat({
  label, value, unit, sub, tone = "", badge,
}: {
  label: string; value: string; unit?: string; sub?: React.ReactNode; tone?: string; badge?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-zinc-500">
        {label}
        {badge}
      </div>
      <div className={`mt-1.5 text-3xl md:text-4xl xl:text-3xl font-semibold tabular-nums leading-none tracking-tight ${tone}`}>
        {value}
        {unit ? <span className="ml-1 text-base font-normal text-zinc-500">{unit}</span> : null}
      </div>
      {sub ? <div className="mt-2 text-xs text-zinc-400">{sub}</div> : null}
    </div>
  );
}

/** The whole month as 30 squares. Dim square = Sunday, plant off. Red ring = godown at the assumed roof. */
export function DayStrip({
  current, days,
}: {
  current: number;
  days: { n: number; date: string; working: boolean; storage_pct: number }[];
}) {
  return (
    <div className="flex flex-wrap gap-1">
      {days.map((d) => {
        const on = d.n === current;
        const roof = d.storage_pct >= 100;
        const cls = on
          ? "bg-amber-500 text-zinc-950 border-amber-400 font-semibold"
          : d.working
            ? "border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
            : "border-zinc-900 bg-zinc-950 text-zinc-600 hover:bg-zinc-900";
        return (
          <Link
            key={d.date}
            href={`/days/${d.n}`}
            title={`${d.date}${d.working ? "" : " — plant off"}${roof ? " — godown at 100% of the assumed roof" : ""}`}
            className={`w-8 h-8 grid place-items-center rounded-md border text-xs tabular-nums ${cls} ${roof && !on ? "ring-1 ring-red-500/70" : ""}`}
          >
            {d.n}
          </Link>
        );
      })}
    </div>
  );
}

/** A scrolling frame so a 150-row order book stays one panel tall. */
export function DayScroll({ children, max = "max-h-96", tint = "" }: { children: React.ReactNode; max?: string; tint?: string }) {
  return <div className={`overflow-auto rounded-xl border border-zinc-800 bg-zinc-900/40 ${max} ${tint}`}>{children}</div>;
}

export function DayEmpty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/20 px-4 py-6 text-sm text-zinc-500">{children}</div>;
}

/**
 * The day's storage waterfall: opening physical -> + filled -> - left the gate -> closing physical,
 * against the ASSUMED roof (open question Q2). `gated` is computed by the caller as
 * opening + made - closing, i.e. stock that physically trucked out today (invoiced on an
 * earlier day — the declared invoice-to-truck lag).
 */
export function DayWaterfall({
  opening, openingCaption, openingSub, made, gated, s, openingMeasured = false,
}: {
  opening: number;
  /** where the opening figure comes from (badge included) — shown under the panel title */
  openingCaption?: React.ReactNode;
  /** short note under the opening row label */
  openingSub?: React.ReactNode;
  made: number;
  gated: number;
  s: StorageDay;
  openingMeasured?: boolean;
}) {
  const closing = s.physical_l;
  const scale = Math.max(opening + made, s.peak_l, closing) * 1.03;
  const pw = (v: number) => `${Math.max(0, (v / scale) * 100)}%`;
  const full = s.pct >= 95;
  const fgW = pw(s.fg_in_godown_l);
  const invW = pw(s.invoiced_not_trucked_l);

  const Row = ({
    label, sub, left, width, color, value, valueTone = "",
    children,
  }: {
    label: string; sub?: React.ReactNode; left: number; width: number; color: string;
    value: string; valueTone?: string; children?: React.ReactNode;
  }) => (
    <div className="flex items-center gap-3 py-1">
      <div className="w-40 shrink-0 text-right">
        <div className="text-xs text-zinc-300">{label}</div>
        {sub ? <div className="text-[10px] leading-tight text-zinc-600">{sub}</div> : null}
      </div>
      <div className="relative h-7 flex-1 rounded bg-zinc-950/60 ring-1 ring-inset ring-zinc-800/60">
        {children ?? (
          <div className={`absolute inset-y-0 rounded-sm ${color}`} style={{ left: pw(left), width: pw(width) }} />
        )}
      </div>
      <div className={`w-32 shrink-0 text-sm tabular-nums ${valueTone || "text-zinc-200"}`}>{value}</div>
    </div>
  );

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-xs uppercase tracking-wider text-zinc-500">The day&apos;s storage waterfall — finished goods on the floor</div>
        <div className={`text-2xl font-semibold tabular-nums ${full ? "text-red-400" : "text-zinc-100"}`}>{s.pct}%</div>
      </div>
      {openingCaption ? <div className="mt-1 text-xs text-zinc-500">{openingCaption}</div> : null}

      <div className="relative mt-4">
        {/* the two roof lines span every row — both ASSUMED, not measured (open question Q2) */}
        <div className="pointer-events-none absolute -top-5 bottom-0 z-10 border-l border-dashed border-red-400/70" style={{ left: `calc(10rem + 0.75rem + (100% - 10rem - 0.75rem - 8rem - 0.75rem) * ${s.ceiling_l / scale})` }} />
        <div className="pointer-events-none absolute -top-5 bottom-0 z-10 border-l border-dashed border-red-400/30" style={{ left: `calc(10rem + 0.75rem + (100% - 10rem - 0.75rem - 8rem - 0.75rem) * ${s.peak_l / scale})` }} />
        <div className="mb-1 flex items-center gap-3 text-[10px] text-zinc-500">
          <div className="w-40 shrink-0" />
          <div className="relative h-4 flex-1">
            <span className="absolute -translate-x-1/2 whitespace-nowrap text-red-300/80" style={{ left: pw(s.ceiling_l) }}>
              roof {fmt(s.ceiling_l)} L
            </span>
            <span className="absolute -translate-x-1/2 whitespace-nowrap text-red-300/40" style={{ left: pw(s.peak_l) }}>
              peak {fmt(s.peak_l)} L
            </span>
          </div>
          <div className="w-32 shrink-0" />
        </div>

        <Row
          label="opening physical"
          sub={openingSub}
          left={0}
          width={opening}
          color={openingMeasured ? "bg-emerald-500/50" : "bg-zinc-500/50"}
          value={`${fmt(opening)} L`}
        />
        <Row
          label="+ filled today"
          sub="the plan's runs"
          left={opening}
          width={made}
          color="bg-amber-500/70"
          value={made > 0 ? `+${fmt(made)} L` : "—"}
          valueTone="text-amber-300"
        />
        <Row
          label="− left the gate"
          sub="invoiced on an earlier day, trucked today"
          left={closing}
          width={gated}
          color="bg-rose-500/45"
          value={gated > 0 ? `−${fmt(gated)} L` : "—"}
          valueTone="text-rose-300"
        />
        <Row label="closing physical" left={0} width={closing} color="" value={`${fmt(closing)} L`} valueTone={full ? "text-red-300" : "text-zinc-100"}>
          <>
            <div className="absolute inset-y-0 rounded-l-sm bg-amber-600/50" style={{ left: 0, width: fgW }} />
            <div className="absolute inset-y-0 bg-sky-500/50" style={{ left: fgW, width: invW }} />
          </>
        </Row>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-500">
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-amber-600/50" />in the godown: {fmt(s.fg_in_godown_l)} L</span>
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-sky-500/50" />invoiced, not on a truck yet: {fmt(s.invoiced_not_trucked_l)} L</span>
        <span className={full ? "text-red-300" : ""}>room left: {fmt(s.headroom_l)} L</span>
        <span className="flex items-center gap-1.5">
          roof: {fmt(s.ceiling_l)} L working / {fmt(s.peak_l)} L peak
          <SimBadge kind="assumed" note="The roof is Daman's spreadsheet figure, NOT a measured capacity — open question Q2." />
        </span>
      </div>
    </div>
  );
}
