// The measured/assumed discipline, made visible. Every simulated or assumed
// object in data/*.json carries a flag; pages render this badge next to it.
const KINDS: Record<string, { label: string; cls: string; title: string }> = {
  plan: {
    label: "PLAN",
    cls: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    title: "September has not happened — this is the simulator's forward plan, not a record.",
  },
  simulated: {
    label: "SIMULATED",
    cls: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    title: "Produced by the calibrated simulator. Nothing here has been done.",
  },
  assumed: {
    label: "ASSUMED",
    cls: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    title: "A declared assumption, not a measurement.",
  },
  forecast: {
    label: "FORECAST",
    cls: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    title: "Not yet ordered — the plan as dated demand buckets (channel=FORECAST, docnum FCST-*).",
  },
  measured: {
    label: "MEASURED",
    cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    title: "Pulled from SAP / the factory app on 31 Aug — an observed fact.",
  },
  derived: {
    label: "DERIVED",
    cls: "bg-zinc-700/40 text-zinc-300 border-zinc-600/40",
    title: "Computed from measured inputs, not directly observed.",
  },
};

export default function SimBadge({ kind = "simulated", note }: { kind?: string; note?: string }) {
  const k = KINDS[kind] ?? KINDS.simulated;
  return (
    <span
      title={note || k.title}
      className={`inline-block align-middle text-[10px] font-semibold tracking-wider px-1.5 py-px rounded border ${k.cls}`}
    >
      {k.label}
    </span>
  );
}
