// Day-page building blocks for the September plan site.
// Everything rendered here is fed from data/*.json (written only by scripts/gen-data.py);
// no business number is typed in this file — only layout constants and UI thresholds.
// Words follow PLAIN-LANGUAGE.md: the planner's raw names (event kinds, channel codes,
// order tags) are turned into floor words HERE, at render time. The data keys stay as they are.
import Link from "next/link";
import { fmt, dlabel } from "../lib/data";
import { materialWord } from "../lib/types";
import type { StorageDay, DayDetail, LoopChain } from "../lib/types";

const THBASE = "font-medium py-2 px-3 text-[11px] uppercase tracking-wider text-zinc-500 bg-zinc-900 sticky top-0";
export const TH = `${THBASE} text-left`;
export const THR = `${THBASE} text-right`;
export const TD = "py-2 px-3 border-t border-zinc-800/70 align-top";
export const NUM = "tabular-nums text-right whitespace-nowrap";

// ---------------------------------------------------------------- plain words

// One voice across the site: the words live in lib/types (pure, client-safe).
// The names below stay, so the day page keeps its imports.
//   eventWords  — the planner's event kinds, said the way the floor says them
//   channelWords — who an order is from; "FORECAST" is the plan wearing a date
//   plainFact   — the data's honesty notes in floor words (numbers from the page)
export { plainEvent as eventWords, plainChannel as channelWords, plainHonestyNote as plainFact, plural } from "../lib/types";
export type { HonestyFacts as FactNumbers } from "../lib/types";

/** An expected-order row's tag says which week of the plan it belongs to. */
export const weekWords = (docnum: string) => {
  const m = /^FCST-W(\d+)/.exec(docnum);
  if (!m) return "expected — not ordered yet";
  const w = Number(m[1]);
  return w === 0 ? "e-com, spread over the month (our guess)" : `week ${w} of the plan`;
};

/** What kind of material an item is — oil, bottle, cap, label… — from its SAP code and name. */
export const materialWords = (code: string, name = "") => materialWord(name, code);

/** Hours the way the floor says them: "45 min", "2 h", "2 h 10 min". */
export const hoursWords = (h: number) => {
  const total = Math.round(h * 60);
  const hrs = Math.floor(total / 60);
  const min = total % 60;
  if (hrs === 0) return `${min} min`;
  return min === 0 ? `${hrs} h` : `${hrs} h ${min} min`;
};

/** An oil change before a run, from its minutes: "oil change — about 1 hour". */
export const oilChangeWords = (min: number) => {
  const halves = Math.round(min / 30) / 2; // nearest half hour
  if (halves < 1) return `oil change — ${min} min`;
  const whole = Math.floor(halves);
  const half = halves - whole > 0;
  return `oil change — about ${whole}${half ? "½" : ""} hour${halves > 1 ? "s" : ""}`;
};

/** Names for SAP item codes, learned from the day files themselves — no name is typed here. */
export const itemNames = (days: DayDetail[], chains: LoopChain[]) => {
  const m: Record<string, string> = {};
  for (const c of chains) m[c.code] = c.name;
  for (const d of days) {
    for (const r of d.received) m[r.code] = r.name;
    for (const b of d.bought) m[b.code] = b.name;
    for (const w of d.waiting_on) m[w.code] = w.name;
    for (const u of d.unblocked) m[u.code] = u.name;
    for (const b of d.blocked) m[b.binder] = b.binder_name;
  }
  return m;
};

// ------------------------------------------------------------------- blocks

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

/** The whole month as 30 squares. Dim square = Sunday, factory closed. Red ring = godown full. */
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
            title={`${dlabel(d.date)}${d.working ? "" : " — factory closed"}${roof ? " — godown full" : ""}`}
            className={`w-8 h-8 grid place-items-center rounded-md border text-xs tabular-nums ${cls} ${roof && !on ? "ring-1 ring-red-500/70" : ""}`}
          >
            {d.n}
          </Link>
        );
      })}
    </div>
  );
}

/** A scrolling frame so a 150-row order list stays one panel tall. */
export function DayScroll({ children, max = "max-h-96", tint = "" }: { children: React.ReactNode; max?: string; tint?: string }) {
  return <div className={`overflow-auto rounded-xl border border-zinc-800 bg-zinc-900/40 ${max} ${tint}`}>{children}</div>;
}

export function DayEmpty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/20 px-4 py-6 text-sm text-zinc-500">{children}</div>;
}

/**
 * The day's godown picture: stock at the start -> + made -> - trucks left -> stock at the end,
 * against the godown limit (Daman's number, not measured). `trucked` is computed by the caller
 * as start + made - end, i.e. stock that left on a truck today (billed on an earlier day).
 */
export function DayWaterfall({
  start, startCaption, startSub, made, trucked, s, startMeasured = false,
}: {
  start: number;
  /** where the starting figure comes from — shown under the panel title */
  startCaption?: React.ReactNode;
  /** short note under the starting row label */
  startSub?: React.ReactNode;
  made: number;
  trucked: number;
  s: StorageDay;
  startMeasured?: boolean;
}) {
  const closing = s.physical_l;
  const scale = Math.max(start + made, s.peak_l, closing) * 1.03;
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
        <div className="text-xs uppercase tracking-wider text-zinc-500">Finished goods in the godown — start of day to end of day</div>
        <div className={`text-2xl font-semibold tabular-nums ${full ? "text-red-400" : "text-zinc-100"}`}>{s.pct}%</div>
      </div>
      {startCaption ? <div className="mt-1 text-xs text-zinc-500">{startCaption}</div> : null}

      <div className="relative mt-4">
        {/* the two limit lines span every row — both Daman's numbers, not measured */}
        <div className="pointer-events-none absolute -top-5 bottom-0 z-10 border-l border-dashed border-red-400/70" style={{ left: `calc(10rem + 0.75rem + (100% - 10rem - 0.75rem - 8rem - 0.75rem) * ${s.ceiling_l / scale})` }} />
        <div className="pointer-events-none absolute -top-5 bottom-0 z-10 border-l border-dashed border-red-400/30" style={{ left: `calc(10rem + 0.75rem + (100% - 10rem - 0.75rem - 8rem - 0.75rem) * ${s.peak_l / scale})` }} />
        <div className="mb-1 flex items-center gap-3 text-[10px] text-zinc-500">
          <div className="w-40 shrink-0" />
          <div className="relative h-4 flex-1">
            <span className="absolute -translate-x-1/2 whitespace-nowrap text-red-300/80" style={{ left: pw(s.ceiling_l) }}>
              full at {fmt(s.ceiling_l)} L
            </span>
            <span className="absolute -translate-x-1/2 whitespace-nowrap text-red-300/40" style={{ left: pw(s.peak_l) }}>
              squeeze limit {fmt(s.peak_l)} L
            </span>
          </div>
          <div className="w-32 shrink-0" />
        </div>

        <Row
          label="stock at start of day"
          sub={startSub}
          left={0}
          width={start}
          color={startMeasured ? "bg-emerald-500/50" : "bg-zinc-500/50"}
          value={`${fmt(start)} L`}
        />
        <Row
          label="+ made today"
          sub="the day's runs"
          left={start}
          width={made}
          color="bg-amber-500/70"
          value={made > 0 ? `+${fmt(made)} L` : "—"}
          valueTone="text-amber-300"
        />
        <Row
          label="− trucks left today"
          sub="billed on an earlier day"
          left={closing}
          width={trucked}
          color="bg-rose-500/45"
          value={trucked > 0 ? `−${fmt(trucked)} L` : "—"}
          valueTone="text-rose-300"
        />
        <Row label="stock at end of day" left={0} width={closing} color="" value={`${fmt(closing)} L`} valueTone={full ? "text-red-300" : "text-zinc-100"}>
          <>
            <div className="absolute inset-y-0 rounded-l-sm bg-amber-600/50" style={{ left: 0, width: fgW }} />
            <div className="absolute inset-y-0 bg-sky-500/50" style={{ left: fgW, width: invW }} />
          </>
        </Row>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-500">
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-amber-600/50" />free stock in the godown: {fmt(s.fg_in_godown_l)} L</span>
        <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-sky-500/50" />billed, truck not left yet: {fmt(s.invoiced_not_trucked_l)} L</span>
        <span className={full ? "text-red-300" : ""}>space left: {fmt(s.headroom_l)} L</span>
        <span>
          godown full at {fmt(s.ceiling_l)} L, squeeze limit {fmt(s.peak_l)} L — Daman&apos;s numbers, not measured
        </span>
      </div>
    </div>
  );
}
