import Link from "next/link";
import { Card, Pill, Section } from "@/components/Card";
import SimBadge from "@/components/SimBadge";
import LineHeatStrip, { type HeatHead, type HeatRow } from "@/components/LineHeatStrip";
import {
  cr, dlabel, fmt, getBuild, getHonesty, getLines, getOverview,
  getQuestions, getScenarios, getSpine, money, tonnes,
} from "@/lib/data";

export const metadata = {
  title: "Lines",
  description:
    "Each filling line's planned September — hours, litres, oil changes and slot rates, with the derates stated honestly.",
};

// hours with one decimal, Indian grouping (UI formatting only)
const h1f = (n: number) => n.toLocaleString("en-IN", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const BASIS_TONE: Record<string, string> = { rated: "zinc", observed: "amber", derived: "blue" };

export default function LinesPage() {
  const L = getLines();
  const spine = getSpine();
  const B = getBuild();
  const O = getOverview();
  const H = getHonesty();
  const q4 = getQuestions().items.find((q) => q.n === 4);
  const baseline = getScenarios().baseline;

  const shift = baseline.shift_hours;
  const eff = Math.round(L.efficiency * 100);
  const workingDays = spine.filter((d) => d.working).length;
  const sundays = spine.length - workingDays;
  const capLine = shift * workingDays;
  const capAll = capLine * L.lines.length;

  // ---- per line, per day — aggregated from the run ledger in lines.json
  const rows: HeatRow[] = L.lines.map((ln) => {
    const byDate = new Map<string, { h: number; fill: number; litres: number; runs: number; flush: number }>();
    for (const r of L.runs_by_line[ln.name] ?? []) {
      if (!r.date) continue;
      const c = byDate.get(r.date) ?? { h: 0, fill: 0, litres: 0, runs: 0, flush: 0 };
      c.fill += r.hours;
      c.h += r.hours + r.flush_min / 60;
      c.litres += r.litres;
      c.runs += 1;
      c.flush += r.flush_min;
      byDate.set(r.date, c);
    }
    return {
      line: ln.name,
      cells: spine.map((d) => {
        const c = byDate.get(d.date);
        return {
          day: d.n,
          label: `${d.weekday.slice(0, 3)} ${dlabel(d.date)}`,
          working: d.working,
          hours: c ? c.h : 0,
          fillHours: c ? c.fill : 0,
          litres: c ? c.litres : 0,
          runs: c ? c.runs : 0,
          flushMin: c ? Math.round(c.flush) : 0,
        };
      }),
    };
  });
  const heads: HeatHead[] = spine.map((d) => ({
    day: d.n,
    wd: d.weekday.slice(0, 1),
    working: d.working,
    util: d.util,
  }));

  // ---- month totals across the six lines
  const hoursOnAll = L.lines.reduce((s, l) => s + l.hours_on_line, 0);
  const changeMinAll = L.lines.reduce((s, l) => s + l.flush_minutes, 0);
  // the month total comes from lines.json total_litres (the summary's own figure) —
  // per-line litres are rounded per line, so their sum can drift a few litres from it
  const litresAll = L.total_litres;
  const valueAll = L.lines.reduce((s, l) => s + l.value_rs, 0);
  const runsAll = L.lines.reduce((s, l) => s + l.runs, 0);
  const busiest = [...L.lines].sort((a, b) => b.hours_on_line - a.hours_on_line)[0];
  const biggest = [...L.lines].sort((a, b) => b.litres - a.litres)[0];

  // ---- changeover kinds per machine, from the build list (same sim, same runs)
  const rules = B.meta.rules;
  const oilChanges = B.meta.totals.oil_changes;
  const clearancesOnly = B.meta.totals.clearances_only;
  const chg = new Map<string, { oil: number; clr: number }>();
  for (const d of B.days)
    for (const m of d.machines)
      for (const r of m.runs) {
        const c = r.changeover_before;
        if (!c) continue;
        const e = chg.get(m.machine) ?? { oil: 0, clr: 0 };
        if (c.kind === "OIL CHANGE") e.oil += 1;
        else e.clr += 1;
        chg.set(m.machine, e);
      }

  const observed = L.lines.flatMap((l) =>
    l.slots.filter((s) => s.rate_basis === "observed").map((s) => ({ line: l.name, ...s }))
  );
  const derivedSlots = L.lines.flatMap((l) =>
    l.slots.filter((s) => s.rate_basis === "derived").map((s) => ({ line: l.name, ...s }))
  );
  const speedsProv = H.measured.find((m) => m.toLowerCase().includes("line speeds")) ?? "";
  const realiseProv = H.measured.find((m) => m.toLowerCase().includes("realise")) ?? "";

  const unpro = O.unproducible;
  const unproLitres = unpro.reduce((s, u) => s + u.plan_litres, 0);
  const unproSlots = [...new Set(unpro.map((u) => u.slot_needed))].join(" or ");

  return (
    <div>
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">
            Lines <SimBadge kind="plan" />
          </h1>
          <p className="text-sm text-zinc-400 mt-1 max-w-3xl">
            {L.lines.length} filling lines, {shift} h shifts, {workingDays} working days ({sundays} Sundays off).{" "}
            {fmt(runsAll)} planned runs would fill {fmt(litresAll)} L. A line takes any oil — only the pack size ties a
            SKU to a machine. None of this has been run.
          </p>
        </div>
        <div className="text-xs text-zinc-500 text-right">
          speeds: {speedsProv} <SimBadge kind="measured" />
          <br />
          runs: {L.measured_from} <SimBadge kind="simulated" />
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mt-5">
        <Card
          title="Hours on the lines"
          value={`${h1f(hoursOnAll)} h`}
          sub={`of ${fmt(capAll)} h offered — ${Math.round((hoursOnAll / capAll) * 100)}% used`}
          tone="text-amber-300"
        />
        <Card title="Would fill" value={`${fmt(litresAll)} L`} sub={`${tonnes(litresAll)} · ${fmt(runsAll)} runs`} />
        <Card title="Value of that fill" value={cr(valueAll)} sub={`priced at ${realiseProv} (measured)`} />
        <Card
          title="Oil changes"
          value={fmt(oilChanges)}
          sub={`+ ${clearancesOnly} clearance-only · ${fmt(changeMinAll)} min of changeover`}
        />
        <Card
          title="Busiest line"
          value={busiest.name}
          sub={`${h1f(busiest.hours_on_line)} h on line · ${biggest.name} fills the most (${fmt(biggest.litres)} L)`}
        />
      </div>

      {q4 && (
        <div className="mt-4 rounded-xl border border-amber-500/25 bg-amber-500/[0.04] p-4">
          <div className="flex items-center gap-2 flex-wrap">
            <Pill tone="amber">open question Q{q4.n}</Pill>
            <Pill tone="red">{q4.priority}</Pill>
            <span className="text-xs text-zinc-500">affects every hour on this page</span>
          </div>
          <p className="text-sm text-zinc-300 mt-2 leading-relaxed max-w-4xl">
            &ldquo;{q4.one_liner}&rdquo;
          </p>
          <p className="text-xs text-zinc-500 mt-2 max-w-4xl">
            Every hour here is charged against the simulator&rsquo;s {shift}-hour working day. Until Q{q4.n} is
            answered, that clock is an assumption <SimBadge kind="assumed" /> — if the lines really run later than the
            plan&rsquo;s day, the utilisation and idle-hour figures move with the answer.
          </p>
        </div>
      )}

      <Section
        title="Utilisation, day by day"
        right={<span className="text-xs text-zinc-500">hover a cell · click to open the day</span>}
      >
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <LineHeatStrip rows={rows} days={heads} shift={shift} />
          <p className="text-xs text-zinc-500 mt-4">
            Each cell is how much of the {shift}-hour shift that line would be busy — filling plus the minutes an oil
            change or line clearance costs. A grey dash is a line standing idle on a working day; the bottom row is all{" "}
            {L.lines.length} lines together as the simulator&rsquo;s utilisation percentage. This is the plan&rsquo;s
            timetable, not a log.
          </p>
        </div>
      </Section>

      <Section title="Each line's September">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {L.lines.map((l) => {
            const pct = Math.round((l.hours_on_line / capLine) * 100);
            const c = chg.get(l.name) ?? { oil: 0, clr: 0 };
            const rate = l.hours_run > 0 ? Math.round(l.litres / l.hours_run) : 0;
            return (
              <div key={l.name} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <div className="font-semibold">{l.name}</div>
                  <div className="flex gap-1 flex-wrap justify-end">
                    {l.slots.map((s) => (
                      <Pill key={s.slot} tone={BASIS_TONE[s.rate_basis] ?? "zinc"}>
                        {s.slot}
                      </Pill>
                    ))}
                  </div>
                </div>
                <div className="flex items-baseline gap-2 mt-3">
                  <div className="text-3xl font-semibold tabular-nums">{h1f(l.hours_on_line)}</div>
                  <div className="text-sm text-zinc-500">h of {fmt(capLine)} h</div>
                </div>
                <div className="h-2 rounded-full bg-zinc-800 overflow-hidden mt-2">
                  <div className="h-full bg-amber-500/70 rounded-full" style={{ width: `${Math.min(100, pct)}%` }} />
                </div>
                <div className="text-[11px] text-zinc-500 mt-1 tabular-nums">
                  {pct}% used · {h1f(l.hours_run)} h filling + {fmt(l.flush_minutes)} min changeover
                </div>
                <dl className="grid grid-cols-2 gap-y-2 mt-4 text-sm">
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Would fill</dt>
                    <dd className="tabular-nums">{fmt(l.litres)} L</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Value</dt>
                    <dd className="tabular-nums">{money(l.value_rs)}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Runs</dt>
                    <dd className="tabular-nums">
                      {l.runs} <span className="text-zinc-500 text-xs">over {l.days_active} days</span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Oil changes</dt>
                    <dd className="tabular-nums">
                      {c.oil} <span className="text-zinc-500 text-xs">+ {c.clr} clearance-only</span>
                    </dd>
                  </div>
                </dl>
                <div className="text-xs text-zinc-500 mt-4 pt-3 border-t border-zinc-800">
                  Effective pace {fmt(rate)} L/h across the month <SimBadge kind="derived" note="litres ÷ filling hours — computed, not observed" />
                </div>
                <div className="text-[11px] text-zinc-600 mt-2 space-y-0.5">
                  {l.top_skus.slice(0, 3).map((s) => (
                    <div key={s.sku} className="truncate tabular-nums">
                      {fmt(s.litres)} L · {s.sku}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </Section>

      <Section title="What the plan fills at">
        <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.04] p-4">
          <div className="text-xs uppercase tracking-wider text-amber-300/90">
            Two slots are derated twice — say it right
          </div>
          <p className="text-sm text-zinc-300 mt-2 leading-relaxed max-w-4xl">
            Most slots carry a <em>rated</em> speed, and the sim plans them at {eff}% of it — the derate the August
            backtest calibrated (replayed on August, the engine landed {fmt(H.august_calibration.sim_made_l)} L against{" "}
            {fmt(H.august_calibration.actual_made_l)} L actually made) <SimBadge kind="assumed" />. But{" "}
            {observed.map((s, i) => (
              <span key={`${s.line}-${s.slot}`}>
                {i > 0 && " and "}
                <span className="text-zinc-100">
                  {s.line} {s.slot}
                </span>
              </span>
            ))}{" "}
            are stored at rates someone <em>watched the line do</em> — and the plan derates those by {eff}% again. So
            their planned pace is <span className="text-amber-300">the observed rate, then {eff}% efficiency</span> —
            not {eff}% of rated:
          </p>
          <div className="grid sm:grid-cols-2 gap-3 mt-3">
            {observed.map((s) => (
              <div key={`${s.line}-${s.slot}`} className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
                <div className="text-sm font-medium">
                  {s.line} <Pill tone="amber">{s.slot}</Pill>
                </div>
                <div className="text-sm tabular-nums mt-1">
                  {fmt(s.stored_rate_per_hr)} pcs/hr observed → plan runs {fmt(s.effective_rate_per_hr)} pcs/hr
                </div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-zinc-500 mt-3 italic max-w-4xl">Data register: {L.efficiency_note}</p>
        </div>

        <div className="mt-3 rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
                <th className="py-3 px-4 font-medium">Line</th>
                <th className="py-3 px-4 font-medium">Slot</th>
                <th className="py-3 px-4 font-medium text-right">Stored rate</th>
                <th className="py-3 px-4 font-medium">Basis</th>
                <th className="py-3 px-4 font-medium text-right">Plan fills at</th>
                <th className="py-3 px-4 font-medium">Note</th>
              </tr>
            </thead>
            <tbody>
              {L.lines.flatMap((l) =>
                l.slots.map((s) => (
                  <tr
                    key={`${l.name}-${s.slot}`}
                    className={`border-b border-zinc-900 last:border-0 ${
                      s.rate_basis === "observed" ? "bg-amber-500/[0.05]" : ""
                    }`}
                  >
                    <td className="py-2.5 px-4 text-zinc-300 whitespace-nowrap">{l.name}</td>
                    <td className="py-2.5 px-4">
                      <Pill tone={BASIS_TONE[s.rate_basis] ?? "zinc"}>{s.slot}</Pill>
                    </td>
                    <td className="py-2.5 px-4 text-right tabular-nums whitespace-nowrap">
                      {fmt(s.stored_rate_per_hr)} <span className="text-zinc-600 text-xs">pcs/hr</span>
                    </td>
                    <td className="py-2.5 px-4">
                      <span
                        className={`text-xs uppercase tracking-wide ${
                          s.rate_basis === "observed"
                            ? "text-amber-300"
                            : s.rate_basis === "derived"
                              ? "text-sky-300"
                              : "text-zinc-400"
                        }`}
                      >
                        {s.rate_basis}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right tabular-nums whitespace-nowrap">
                      {fmt(s.effective_rate_per_hr)} <span className="text-zinc-600 text-xs">pcs/hr</span>
                    </td>
                    <td className="py-2.5 px-4 text-xs text-zinc-500 min-w-[260px]">{s.note}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-zinc-500 mt-3 max-w-4xl">
          {derivedSlots.length > 0 && (
            <>
              The {derivedSlots.map((s) => `${s.line} ${s.slot}`).join(", ")} rates are DERIVED — no measured rate
              exists for that pack, so the sim declares the assumption instead of inventing a speed.{" "}
            </>
          )}
          A slot missing from a line means that pack size is not set up there.
        </p>
      </Section>

      <Section title="The changeover bill — time, not material">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card
            title="Changeover time"
            value={`${h1f(changeMinAll / 60)} h`}
            sub={`${fmt(changeMinAll)} min — ${Math.round((changeMinAll / 60 / hoursOnAll) * 100)}% of time on the lines`}
            tone="text-amber-300"
          />
          <Card
            title="Line-days lost to it"
            value={h1f(changeMinAll / 60 / shift)}
            sub={`full ${shift}-hour line-days of switching`}
          />
          <Card
            title="Oil changes"
            value={fmt(oilChanges)}
            sub={`+ ${clearancesOnly} pack-size-only clearances`}
          />
          <Card
            title="Flush oil cycled"
            value={`${fmt(oilChanges * rules.flush_litres)} L`}
            sub={`${fmt(rules.flush_litres)} L per change — run through and REUSED, not consumed`}
          />
        </div>
        <div className="mt-3 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <p className="text-sm text-zinc-300 leading-relaxed max-w-4xl">
            The rule the sim charges: <span className="text-zinc-100">{rules.note}</span>. So the flush is not a
            material cost — the {fmt(rules.flush_litres)} L of the next oil comes back — but every switch still pays
            its minutes, and {fmt(oilChanges)} oil changes add up to {h1f(changeMinAll / 60)} hours the lines
            aren&rsquo;t filling.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-2 mt-4">
            {L.lines.map((l) => {
              const c = chg.get(l.name) ?? { oil: 0, clr: 0 };
              const w = Math.round((l.flush_minutes / changeMinAll) * 100);
              return (
                <div key={l.name} className="text-xs">
                  <div className="flex justify-between tabular-nums text-zinc-400">
                    <span>{l.name}</span>
                    <span>
                      {c.oil} changes · {fmt(l.flush_minutes)} min
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden mt-1">
                    <div className="h-full bg-amber-500/60 rounded-full" style={{ width: `${w}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-[11px] text-zinc-600 mt-3">
            The day-by-day switching order, changeover by changeover, is written out for the floor on the{" "}
            <Link href="/build" className="text-zinc-400 hover:text-amber-300 underline underline-offset-2">
              build list
            </Link>
            .
          </p>
        </div>
      </Section>

      {unpro.length > 0 && (
        <div className="mt-8 rounded-xl border border-red-500/20 bg-red-500/[0.04] p-4">
          <p className="text-sm text-zinc-300 max-w-4xl">
            <span className="text-red-300 font-medium">What no line can do:</span> nothing here is configured for a{" "}
            {unproSlots} slot, so {unpro.length} plan SKUs — {fmt(unproLitres)} L of the month&rsquo;s plan — cannot be
            produced at all. They are not hidden in the bars above; they never reach a line.{" "}
            <Link href="/materials" className="text-red-300 hover:text-red-200 underline underline-offset-2">
              See them on Materials →
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}
