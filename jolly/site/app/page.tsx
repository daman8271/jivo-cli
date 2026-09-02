import { getSummary, getInputs, getAllDays, fmt, cr } from "../lib/data";
import { Card, Section, Pill } from "../components/Card";
import OvStrip from "../components/OvStrip";

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const dlabel = (iso: string) => `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}`;
const avg = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
// "4, 11 and 18 August"
const listDays = (iso: string[]) => {
  const n = iso.map((d) => String(Number(d.slice(8, 10))));
  const head = n.slice(0, -1).join(", ");
  return (head ? `${head} and ${n[n.length - 1]}` : n[0]) + " August";
};

export default function Overview() {
  const S = getSummary();
  const IN = getInputs();
  const ACT = IN.actuals_for_scoring;
  const aheadPct = ((getSummary().totals.made_l - ACT.made_l) / ACT.made_l) * 100;
  const DAYS = getAllDays();
  const D = S.days;
  const t = S.totals;

  // ---- the shape of the month, all of it read off the JSON ----------------
  const work = D.filter((d) => d.working);
  const avgUtil = Math.round(avg(work.map((d) => d.util)));
  const avgStore = Math.round(avg(D.map((d) => d.storage_pct)));
  const d0 = DAYS[0];
  const ceiling = d0.storage.ceiling_l;
  const throttled = DAYS.filter((d) => d.decisions.some((x) => x.kind === "STORAGE_THROTTLE")).length;
  const blockedDays = DAYS.filter((d) => d.working && d.blocked.length > 0).length;
  const full = D.filter((d) => d.storage_pct >= 95).length;
  const peak = D.reduce((a, b) => (b.made_l > a.made_l ? b : a));
  const idle = work.filter((d) => d.made_l === 0);
  const blocked = D.reduce((a, d) => a + d.blocked, 0);
  const planPct = Math.round((t.made_l / IN.plan_total_l) * 100);

  // the day the most litres left the godown, and who took them
  const bi = D.reduce((a, b, i) => (b.shipped_l > D[a].shipped_l ? i : a), 0);
  const bigDay = D[bi];
  const bigRaw = DAYS[bi];
  const sumBy = (k: "channel" | "customer") => {
    const m = new Map<string, number>();
    for (const x of bigRaw.dispatched) m.set(x[k], (m.get(x[k]) ?? 0) + x.litres);
    return [...m.entries()].sort((a, b) => b[1] - a[1])[0];
  };
  const topCh = sumBy("channel");
  const topCust = sumBy("customer");
  const bigShare = Math.round((bigDay.shipped_l / t.shipped_l) * 100);

  const before = D.slice(0, bi).filter((d) => d.working);
  const after = D.slice(bi + 1).filter((d) => d.working);
  const utilBefore = Math.round(avg(before.map((d) => d.util)));
  const utilAfter = Math.round(avg(after.map((d) => d.util)));
  const hundred = D.filter((d) => d.util >= 100);
  const blockedAfter = D.slice(bi + 1).reduce((a, d) => a + d.blocked, 0);

  const N = ({ children }: { children: React.ReactNode }) => (
    <span className="text-zinc-100 font-medium tabular-nums">{children}</span>
  );

  const story: React.ReactNode[] = [
    <>
      August opened with the godown at <N>{d0.storage.pct}%</N> of its <N>{fmt(ceiling)} L</N> working ceiling — only{" "}
      <N>{fmt(d0.storage.headroom_l)} L</N> of room left. The best production day of the month, {dlabel(peak.date)},
      made <N>{fmt(peak.made_l)} L</N>.
    </>,
    <>
      So on <N>{throttled}</N> of the <N>{work.length}</N> working days the planner&rsquo;s decision was the same one:
      cap production to whatever can ship. Storage stood at 95% on <N>{full}</N> of the 31 days.
    </>,
    <>
      Through the first <N>{before.length}</N> working days the lines averaged <N>{utilBefore}%</N> of capacity. On{" "}
      <N>{idle.length}</N> working days across the month — {listDays(idle.map((d) => d.date))} — nothing would have been made at
      all.
    </>,
    <>
      On {dlabel(bigDay.date)} one big load cleared the floor: <N>{fmt(bigDay.shipped_l)} L</N> went out —{" "}
      <N>{fmt(topCh[1])} L</N> of it on the {topCh[0]} channel to {topCust[0]} — which is <N>{bigShare}%</N> of
      everything shipped all month.
    </>,
    <>
      With room to put things, the lines opened up: the <N>{after.length}</N> working days after that averaged{" "}
      <N>{utilAfter}%</N> and touched 100% on {listDays(hundred.map((d) => d.date))}. Then the shortage moved from
      space to material — <N>{fmt(blocked)}</N> planned runs never started for want of an item, and{" "}
      <N>{fmt(blockedAfter)}</N> of those came after {dlabel(bigDay.date)}.
    </>,
  ];

  return (
    <div>
      {/* ---------------- headline ---------------- */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
        <div className="text-xs uppercase tracking-wider text-zinc-500">
          August 2026 · JIVO Oil · {work.length} working days, {D.length - work.length} Sundays off
        </div>
        <div className="mt-4 flex flex-wrap items-end gap-x-10 gap-y-4">
          <div>
            <div className="text-6xl sm:text-7xl font-semibold tracking-tight leading-none">
              {planPct}
              <span className="text-zinc-500 text-4xl">%</span>
            </div>
            <div className="text-sm text-zinc-400 mt-2">of the month&rsquo;s plan would have been made</div>
          </div>
          <p className="text-lg text-zinc-300 max-w-2xl leading-relaxed">
            <span className="text-zinc-100 font-medium">{fmt(t.made_l)} L</span> would have come off the lines against a plan of{" "}
            <span className="text-zinc-100 font-medium">{fmt(IN.plan_total_l)} L</span> across {IN.plan_skus} SKUs.{" "}
            <span className="text-zinc-100 font-medium">The plant actually made {fmt(IN.actuals_for_scoring.made_l)} L</span>, so the
            planner is{" "}
            <span className={aheadPct >= 0 ? "text-emerald-300 font-medium" : "text-red-300 font-medium"}>
              {aheadPct >= 0 ? "+" : ""}{aheadPct.toFixed(1)}%
            </span>{" "}
            — a modest edge, not a transformation.{" "}
            {throttled === 0
              ? "Storage never capped a day."
              : `Storage capped production on ${throttled} of the ${work.length} working days.`}{" "}
            {blockedDays > work.length / 2
              ? "What held it back was material: a component at zero stopped a planned run on most working days."
              : "Material shortages were the main brake."}
          </p>
        </div>
        <div className="mt-6">
          <div className="h-3 rounded-full bg-zinc-800 overflow-hidden">
            <div className="h-full bg-amber-500" style={{ width: `${planPct}%` }} />
          </div>
          <div className="flex justify-between text-[11px] text-zinc-500 mt-2">
            <span>{fmt(t.made_l)} L made</span>
            <span>
              plan {fmt(IN.plan_total_l)} L · {IN.plan_skus} SKUs
            </span>
          </div>
        </div>
      </div>

      {/* ---------------- six numbers ---------------- */}
      <Section title="The month in six numbers">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <Card
            title="Litres made"
            value={`${fmt(t.made_l)} L`}
            sub={`${peak.made_l > 0 ? `best day ${dlabel(peak.date)} — ${fmt(peak.made_l)} L` : ""}`}
          />
          <Card title="Value made" value={cr(t.value)} sub="priced at the May–Jul realisation per litre" />
          <Card
            title="Litres shipped"
            value={`${fmt(t.shipped_l)} L`}
            sub={`${fmt(t.made_l - t.shipped_l)} L more made than shipped`}
          />
          <Card
            title="Line utilisation"
            value={`${avgUtil}%`}
            sub={`average of the ${work.length} working days · peak ${Math.max(...D.map((d) => d.util))}%`}
            tone="text-amber-300"
          />
          <Card
            title="Godown fill"
            value={`${avgStore}%`}
            sub={`31-day average of the ${fmt(ceiling)} L ceiling`}
            tone="text-red-300"
          />
          <Card
            title="Order lines received"
            value={fmt(t.orders)}
            sub={`SAP August order book · ${fmt(D.reduce((a, d) => a + d.new_orders, 0))} of them on plan SKUs`}
          />
        </div>
      </Section>

      {/* ---------------- 31-day strip ---------------- */}
      <Section
        title="Every day of August"
        right={<span className="text-xs text-zinc-500">bar = litres made · colour = godown fill · click a day</span>}
      >
        <OvStrip days={D} />
      </Section>

      {/* ---------------- the story ---------------- */}
      <Section title="The story">
        <ol className="rounded-xl border border-zinc-800 bg-zinc-900/40 divide-y divide-zinc-800">
          {story.map((s, i) => (
            <li key={i} className="flex gap-4 p-4">
              <span className="text-amber-400/80 text-sm font-semibold tabular-nums w-4 shrink-0 pt-0.5">{i + 1}</span>
              <p className="text-zinc-400 leading-relaxed">{s}</p>
            </li>
          ))}
        </ol>
      </Section>

      {/* ---------------- honesty ---------------- */}
      <Section
        title="Measured vs assumed"
        right={<span className="text-xs text-zinc-500">the same list stands on every day of the replay</span>}
      >
        <div className="grid md:grid-cols-2 gap-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center gap-2">
              <Pill tone="green">Measured</Pill>
              <span className="text-xs text-zinc-500">read from a real system</span>
            </div>
            <ul className="mt-3 space-y-2">
              {d0.honesty.measured.map((m) => (
                <li key={m} className="text-sm text-zinc-300 flex gap-2">
                  <span className="text-emerald-400/70">·</span>
                  {m}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
            <div className="flex items-center gap-2">
              <Pill tone="amber">Assumed</Pill>
              <span className="text-xs text-zinc-500">a choice we made — treat these numbers as soft</span>
            </div>
            <ul className="mt-3 space-y-2">
              {d0.honesty.assumed.map((a) => (
                <li key={a} className="text-sm text-zinc-300 flex gap-2">
                  <span className="text-amber-400/70">·</span>
                  {a}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Section>

      {/* ---------------- provenance ---------------- */}
      <Section
        title="Where the numbers come from"
        right={
          <span className="text-xs text-zinc-500">
            frozen {IN.meta?.frozen} · standing on {IN.meta?.as_of}
          </span>
        }
      >
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-x-auto">
          <table className="w-full text-sm">
            <tbody className="divide-y divide-zinc-800">
              {Object.entries(IN.provenance).map(([k, v]) => (
                <tr key={k} className="align-top">
                  <td className="p-3 w-32 whitespace-nowrap">
                    <Pill>{k}</Pill>
                  </td>
                  <td className="p-3 text-zinc-400">{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {IN.meta?.rule && <p className="text-xs text-zinc-600 mt-3">{IN.meta.rule}</p>}
      </Section>
    </div>
  );
}
