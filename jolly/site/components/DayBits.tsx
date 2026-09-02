import Link from "next/link";
import { fmt, cr, lakh } from "@/lib/data";
import type { Storage } from "@/lib/types";

/** Money the way the floor reads it: crores over a crore, lakhs over a lakh, plain rupees below. */
export const rs = (v: number) => (v >= 1e7 ? cr(v) : v >= 1e5 ? lakh(v) : `₹${fmt(v)}`);

const THBASE = "font-medium py-2 px-3 text-[11px] uppercase tracking-wider text-zinc-500 bg-zinc-900 sticky top-0";
export const TH = `${THBASE} text-left`;
export const THR = `${THBASE} text-right`;
export const TD = "py-2 px-3 border-t border-zinc-800/70 align-top";
export const NUM = "tabular-nums text-right whitespace-nowrap";

/** One big number. Same skin as Card, twice the type — these are the ones read across a room. */
export function DayStat({ label, value, unit, sub, tone = "" }: { label: string; value: string; unit?: string; sub?: string; tone?: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="text-xs uppercase tracking-wider text-zinc-500">{label}</div>
      <div className={`mt-1.5 text-3xl md:text-4xl xl:text-3xl font-semibold tabular-nums leading-none tracking-tight ${tone}`}>
        {value}
        {unit ? <span className="ml-1 text-base font-normal text-zinc-500">{unit}</span> : null}
      </div>
      {sub ? <div className="mt-2 text-xs text-zinc-400">{sub}</div> : null}
    </div>
  );
}

/** The whole month as 31 squares. Dim square = Sunday, plant closed. */
export function DayStrip({ current, days }: { current: number; days: { date: string; working: boolean }[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {days.map((d, i) => {
        const n = i + 1;
        const on = n === current;
        const cls = on
          ? "bg-amber-500 text-zinc-950 border-amber-400 font-semibold"
          : d.working
            ? "border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
            : "border-zinc-900 bg-zinc-950 text-zinc-600 hover:bg-zinc-900";
        return (
          <Link key={d.date} href={`/day/${n}`} className={`w-8 h-8 grid place-items-center rounded-md border text-xs tabular-nums ${cls}`}>
            {n}
          </Link>
        );
      })}
    </div>
  );
}

/** A scrolling frame so a 115-row order book stays one panel tall. */
export function DayScroll({ children, max = "max-h-96" }: { children: React.ReactNode; max?: string }) {
  return <div className={`overflow-auto rounded-xl border border-zinc-800 bg-zinc-900/40 ${max}`}>{children}</div>;
}

export function DayEmpty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/20 px-4 py-6 text-sm text-zinc-500">{children}</div>;
}

/** Finished goods in the godown, against the roof. Two blocks stacked, then the room that is left. */
export function DayBar({ s }: { s: Storage }) {
  const pctOf = (v: number) => Math.max(0, Math.min(100, (v / s.ceiling_l) * 100));
  const fg = pctOf(s.fg_in_godown_l);
  const inv = Math.min(pctOf(s.invoiced_not_trucked_l), Math.max(0, 100 - fg));
  const full = s.pct >= 95;
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-baseline justify-between">
        <div className="text-xs uppercase tracking-wider text-zinc-500">Godown, end of day</div>
        <div className={`text-2xl font-semibold tabular-nums ${full ? "text-red-400" : "text-zinc-100"}`}>{s.pct}%</div>
      </div>
      <div className="relative mt-3 h-10 w-full overflow-hidden rounded-lg bg-zinc-950 ring-1 ring-inset ring-zinc-800">
        <div className="absolute inset-y-0 left-0 bg-amber-500/70" style={{ width: `${fg}%` }} />
        <div className="absolute inset-y-0 bg-sky-500/60" style={{ left: `${fg}%`, width: `${inv}%` }} />
        <div className="absolute inset-y-0 w-px bg-zinc-100/50" style={{ left: "95%" }} />
        <div className="absolute right-1.5 top-1 text-[10px] text-zinc-500">95% cap</div>
      </div>
      <div className="mt-3 grid gap-3 text-sm sm:grid-cols-4">
        <div>
          <div className="flex items-center gap-1.5 text-xs text-zinc-400"><span className="h-2 w-2 rounded-sm bg-amber-500/70" />In the godown</div>
          <div className="tabular-nums">{fmt(s.fg_in_godown_l)} L</div>
        </div>
        <div>
          <div className="flex items-center gap-1.5 text-xs text-zinc-400"><span className="h-2 w-2 rounded-sm bg-sky-500/60" />Invoiced, not on a truck yet</div>
          <div className="tabular-nums">{fmt(s.invoiced_not_trucked_l)} L</div>
        </div>
        <div>
          <div className="text-xs text-zinc-400">Room left</div>
          <div className={`tabular-nums ${full ? "text-red-400" : ""}`}>{fmt(s.headroom_l)} L</div>
        </div>
        <div>
          <div className="text-xs text-zinc-400">Roof</div>
          <div className="tabular-nums text-zinc-400">{fmt(s.ceiling_l)} L</div>
        </div>
      </div>
    </div>
  );
}
