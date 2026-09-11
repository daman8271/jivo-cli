import { PLAIN_KIND } from "../lib/types";

// The "is this real?" tag. Every object in data/*.json that the computer made
// up, guessed, measured or worked out carries a kind; pages put this badge next
// to it. Kind names never change (pages pass them) — only the words shown do.
const KINDS: Record<string, { cls: string; title: string }> = {
  plan: {
    cls: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    title: "This is the computer's plan for September. Nothing here has happened yet.",
  },
  simulated: {
    cls: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    title: "The computer worked this out. Nobody has done it yet.",
  },
  assumed: {
    cls: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    title: "Our guess. Nobody measured this.",
  },
  forecast: {
    cls: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    title: "This month's target, not a customer order. Nobody has ordered it yet.",
  },
  measured: {
    cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    title: "A real figure — taken from SAP or the factory app on the day the stock was counted.",
  },
  derived: {
    cls: "bg-zinc-700/40 text-zinc-300 border-zinc-600/40",
    title: "Not measured directly — worked out from other measured numbers.",
  },
};

export default function SimBadge({ kind = "simulated", note }: { kind?: string; note?: string }) {
  const k = KINDS[kind] ?? KINDS.simulated;
  const label = PLAIN_KIND[kind] ?? PLAIN_KIND.simulated;
  return (
    <span
      title={note || k.title}
      className={`inline-block align-middle text-[10px] font-semibold tracking-wider px-1.5 py-px rounded border ${k.cls}`}
    >
      {label}
    </span>
  );
}
