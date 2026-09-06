// The dense dark-zinc idiom, carried over from Mark 2 unchanged, plus one
// addition every live mark needs everywhere: a panel header slot for the
// "as of" stamp.

export function Card({
  title, value, sub, tone = "", badge,
}: {
  title: string;
  value: string;
  sub?: React.ReactNode;
  tone?: string;
  badge?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="text-xs uppercase tracking-wider text-zinc-500">{title}</div>
        {badge}
      </div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${tone}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-zinc-400">{sub}</div>}
    </div>
  );
}

export function Section({
  title, children, right, note,
}: {
  title: string;
  children: React.ReactNode;
  right?: React.ReactNode;
  note?: React.ReactNode;
}) {
  return (
    <section className="mt-8">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        {right}
      </div>
      {note && <p className="mb-3 max-w-3xl text-sm text-zinc-400">{note}</p>}
      {children}
    </section>
  );
}

/** A panel with its own freshness line in the header. Every panel on this site
 *  has one — the spec makes it an acceptance check. */
export function Panel({
  title, asOf, badge, children, note,
}: {
  title: string;
  asOf?: React.ReactNode;
  badge?: React.ReactNode;
  children: React.ReactNode;
  note?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 border-b border-zinc-800 pb-2">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold text-zinc-200">{title}</h3>
          {badge}
        </div>
        {asOf}
      </div>
      {note && <p className="mb-3 text-xs text-zinc-400">{note}</p>}
      {children}
    </div>
  );
}

export function Pill({ children, tone = "zinc", title }: { children: React.ReactNode; tone?: string; title?: string }) {
  const t: Record<string, string> = {
    zinc: "bg-zinc-800 text-zinc-300",
    amber: "bg-amber-500/15 text-amber-300",
    red: "bg-red-500/15 text-red-300",
    green: "bg-emerald-500/15 text-emerald-300",
    blue: "bg-sky-500/15 text-sky-300",
    violet: "bg-violet-500/15 text-violet-300",
  };
  return (
    <span title={title} className={`inline-block rounded-full px-2 py-0.5 text-[11px] ${t[tone] || t.zinc}`}>
      {children}
    </span>
  );
}

/** One key/value in a dense row of them. */
export function Stat({ k, v, tone = "text-zinc-100", sub }: { k: string; v: string; tone?: string; sub?: string }) {
  return (
    <div className="min-w-[96px]">
      <div className="text-[10px] uppercase tracking-wider text-zinc-500">{k}</div>
      <div className={`mt-0.5 text-sm font-medium tabular-nums ${tone}`}>{v}</div>
      {sub && <div className="text-[10px] text-zinc-500">{sub}</div>}
    </div>
  );
}
