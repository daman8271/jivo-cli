// The stuck -> ordered -> arrived -> running chain, rendered so it stays visible ACROSS days:
// every step that falls on a September day links to that day's page. Chains come from
// data/loops.json (built from sim/events-sep.json); nothing here is typed by hand.
import Link from "next/link";
import type { LoopChain as Chain } from "../lib/types";
import { fmt, dlabel } from "../lib/data";
import { Pill } from "./Card";

/** date -> day number map, built from the spine. */
export const spineDateMap = (spine: { n: number; date: string }[]): Record<string, number> =>
  Object.fromEntries(spine.map((d) => [d.date, d.n]));

export const chainQtyUnit = (kind: string) => (kind === "OIL" ? "L" : "pcs");

/** The last day in the map — the month end, read from the data rather than typed. */
const lastDate = (map: Record<string, number>) => Object.keys(map).sort().slice(-1)[0];

/** A dated reference that links into the month when it can. */
export function LoopDayRef({ date, map, className = "" }: { date: string; map: Record<string, number>; className?: string }) {
  const n = map[date];
  if (!n) {
    const end = lastDate(map);
    return <span className={`text-zinc-500 ${className}`}>{dlabel(date)} — after {end ? dlabel(end) : "the month end"}</span>;
  }
  return (
    <Link href={`/days/${n}`} className={`text-amber-400 hover:underline ${className}`}>
      day {n} · {dlabel(date)}
    </Link>
  );
}

/** Which chain explains a missing item that is holding a product on `today`? */
export function chainForBinder(chains: Chain[], code: string, today: string): { chain: Chain; state: "on-order" | "ordered-later" | "landed" } | null {
  const mine = chains.filter((c) => c.code === code);
  if (mine.length === 0) return null;
  const onOrder = mine
    .filter((c) => c.ordered_day <= today && (!c.unblocked_day || c.unblocked_day > today))
    .sort((a, b) => (a.ordered_day < b.ordered_day ? 1 : -1))[0];
  if (onOrder) return { chain: onOrder, state: "on-order" };
  const later = mine.filter((c) => c.ordered_day > today).sort((a, b) => (a.ordered_day > b.ordered_day ? 1 : -1))[0];
  if (later) return { chain: later, state: "ordered-later" };
  const landed = mine
    .filter((c) => c.unblocked_day && c.unblocked_day <= today)
    .sort((a, b) => ((a.unblocked_day ?? "") < (b.unblocked_day ?? "") ? 1 : -1))[0];
  if (landed) return { chain: landed, state: "landed" };
  return null;
}

/** The planner's own note on a chain, in floor words. */
const chainNoteWords = (note: string, map: Record<string, number>) => {
  const end = lastDate(map);
  if (/not unblocked/i.test(note)) return `does not arrive by ${end ? dlabel(end) : "the month end"}`;
  return note;
};

function Step({
  title, active, done, children,
}: {
  title: string; active?: boolean; done?: boolean; children: React.ReactNode;
}) {
  return (
    <div
      className={`min-w-[10.5rem] flex-1 rounded-lg border px-3 py-2 ${
        active
          ? "border-amber-500/60 bg-amber-500/10 ring-1 ring-amber-500/40"
          : done
            ? "border-zinc-800 bg-zinc-900/60"
            : "border-zinc-800/70 bg-zinc-950/60"
      }`}
    >
      <div className={`text-[10px] font-semibold uppercase tracking-wider ${active ? "text-amber-300" : done ? "text-zinc-400" : "text-zinc-600"}`}>
        {title}
        {active ? " — today" : ""}
      </div>
      <div className="mt-1 text-sm">{children}</div>
    </div>
  );
}

const Arrow = () => <div className="hidden shrink-0 self-center text-zinc-600 sm:block">→</div>;

/**
 * One chain as four steps. `today` (ISO date) highlights the step this page's
 * day is living through; other steps link to their own days.
 */
export function LoopPipeline({ chain, today, map, roles = [] }: { chain: Chain; today: string; map: Record<string, number>; roles?: string[] }) {
  const unit = chainQtyUnit(chain.kind);
  const fr = chain.first_run_after_unblock;
  const resolved = Boolean(chain.unblocked_day);
  const held = chain.fg_codes_blocked.length;
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="font-medium text-zinc-200">{chain.name}</span>
        <span className="text-xs text-zinc-600">{chain.code}</span>
        <Pill tone={chain.kind === "OIL" ? "red" : "zinc"}>{chain.kind === "OIL" ? "oil" : "packing material"}</Pill>
        {roles.map((r) => (
          <Pill key={r} tone="amber">{r}</Pill>
        ))}
        <span className="ml-auto text-[11px] text-violet-300/70" title="This is the computer's plan. Nothing has been ordered, nothing has run.">computer&apos;s plan — nothing ordered, nothing run</span>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Step title="stuck" done>
          {held === 0 ? (
            "ran out"
          ) : (
            <>
              {held} product{held === 1 ? "" : "s"} stuck
              <span className="ml-1 text-xs text-zinc-500" title={chain.fg_codes_blocked.join(", ")}>
                ({chain.fg_codes_blocked.slice(0, 3).join(", ")}
                {held > 3 ? ", …" : ""})
              </span>
            </>
          )}
        </Step>
        <Arrow />
        <Step title="ordered" active={chain.ordered_day === today} done={chain.ordered_day < today}>
          {fmt(chain.qty)} {unit} · <LoopDayRef date={chain.ordered_day} map={map} />
          <div className="text-xs text-zinc-500">takes {chain.lead_days} day{chain.lead_days === 1 ? "" : "s"} to arrive</div>
        </Step>
        <Arrow />
        <Step
          title={resolved ? "arrived — can run again" : "arrives"}
          active={(chain.unblocked_day ?? chain.lands) === today}
          done={resolved && (chain.unblocked_day as string) < today}
        >
          <LoopDayRef date={chain.unblocked_day ?? chain.lands} map={map} />
          {typeof chain.waited_days === "number" ? <div className="text-xs text-zinc-500">waited {chain.waited_days} day{chain.waited_days === 1 ? "" : "s"}</div> : null}
          {!resolved && chain.note ? <div className="text-xs text-amber-300/80">{chainNoteWords(chain.note, map)}</div> : null}
        </Step>
        <Arrow />
        <Step title="running again" active={fr?.day === today} done={Boolean(fr && fr.day < today)}>
          {fr ? (
            <>
              <LoopDayRef date={fr.day} map={map} />
              <div className="text-xs text-zinc-400">
                {fr.sku} <span className="text-zinc-600">{fr.code}</span> · {fmt(fr.litres)} L
              </div>
            </>
          ) : resolved ? (
            <span className="text-xs text-zinc-500">nothing ran on it before the month end</span>
          ) : (
            <span className="text-xs text-zinc-600">—</span>
          )}
        </Step>
      </div>
    </div>
  );
}
