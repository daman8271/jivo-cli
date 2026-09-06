// The "is this real?" tag, kept from Mark 2 — but the live marks have two more
// kinds than Mark 2 did. `live` is a figure read off the plant minutes ago,
// because there is a NOW layer at all now. `happened` is a day already gone, read off the same
// systems hours or days ago — a record, not the plan and not live either.

const KINDS: Record<string, { cls: string; label: string; title: string }> = {
  live: {
    cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    label: "LIVE",
    title: "Read off the plant's own systems minutes ago. This is happening now.",
  },
  happened: {
    cls: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    label: "HAPPENED",
    title: "A record of a day already gone, read off the factory's own systems. Not the plan.",
  },
  measured: {
    cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    label: "REAL",
    title: "A real figure, taken from the plant's own systems.",
  },
  plan: {
    cls: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    label: "COMPUTER PLAN",
    title: "The computer's plan from here on. Nothing here has happened yet.",
  },
  simulated: {
    cls: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    label: "WORKED OUT",
    title: "The computer worked this out. Nobody has done it yet.",
  },
  assumed: {
    cls: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    label: "OUR GUESS",
    title: "Our guess. Nobody measured this.",
  },
  forecast: {
    cls: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    label: "EXPECTED",
    title: "This month's target, not a customer order. Nobody has ordered it yet.",
  },
  derived: {
    cls: "bg-zinc-700/40 text-zinc-300 border-zinc-600/40",
    label: "WORKED OUT",
    title: "Not measured directly — worked out from other measured numbers.",
  },
};

export default function SimBadge({ kind = "simulated", note }: { kind?: string; note?: string }) {
  const k = KINDS[kind] ?? KINDS.simulated;
  return (
    <span
      title={note || k.title}
      className={`inline-block rounded border px-1.5 py-px align-middle text-[10px] font-semibold tracking-wider ${k.cls}`}
    >
      {k.label}
    </span>
  );
}
