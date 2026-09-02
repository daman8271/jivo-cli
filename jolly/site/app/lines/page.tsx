import Link from "next/link";
import { Card, Section, Pill } from "@/components/Card";
import LnGantt, { type LnCell, type LnDayHead, type LnRow, type LnRun } from "@/components/LnGantt";
import { cr, fmt, getAllDays, getInputs, lakh } from "@/lib/data";
import { LINES, type Day } from "@/lib/types";

const PALETTE = [
  "#f59e0b", "#38bdf8", "#34d399", "#a78bfa", "#fb7185",
  "#a3e635", "#22d3ee", "#e879f9", "#fdba74", "#94a3b8",
];
const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const PACK_ORDER = ["1L", "2L", "4L", "5L", "POUCH", "TIN"];

const money = (rs: number) => (rs >= 1e7 ? cr(rs) : lakh(rs));
const dayNo = (iso: string) => Number(iso.slice(8, 10));
const dayLabel = (d: Day) => `${d.weekday.slice(0, 3)} ${dayNo(d.date)} ${MONTHS[Number(d.date.slice(5, 7))]}`;

export default function LinesPage() {
  const days = getAllDays();
  const inputs = getInputs();
  const shift: number = Number(inputs.rules.shift_hours);
  const workingDays = days.filter((d) => d.working).length;
  const capLine = shift * workingDays;
  const capAll = capLine * LINES.length;

  // ---- oils: colour by size, biggest first. The data carries RM codes, not oil names,
  //      so each code is shown with the SKU it filled most of.
  const oilStat = new Map<string, { litres: number; topSku: string; topL: number }>();
  for (const d of days) {
    for (const r of d.runs) {
      const key = r.oil ?? "—";
      const o = oilStat.get(key) ?? { litres: 0, topSku: "", topL: 0 };
      o.litres += r.litres;
      if (r.litres > o.topL) { o.topL = r.litres; o.topSku = r.sku; }
      oilStat.set(key, o);
    }
  }
  const oils = [...oilStat.entries()].sort((a, b) => b[1].litres - a[1].litres);
  const colours: Record<string, string> = {};
  oils.forEach(([code], i) => { colours[code] = PALETTE[i % PALETTE.length]; });

  // ---- per line, per day
  const rows: LnRow[] = LINES.map((line) => ({
    line,
    cells: days.map<LnCell>((d, i) => {
      const runs: LnRun[] = d.runs
        .filter((r) => r.line === line)
        .map((r) => ({ sku: r.sku, oil: r.oil, litres: r.litres, hours: r.hours, flush_min: r.flush_min }));
      const byOil = new Map<string, number>();
      for (const r of runs) byOil.set(r.oil ?? "—", (byOil.get(r.oil ?? "—") ?? 0) + r.litres);
      const dominant = [...byOil.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
      return {
        day: i + 1,
        label: dayLabel(d),
        working: d.working,
        hours: d.line_hours[line] ?? 0,
        oil: dominant,
        litres: runs.reduce((s, r) => s + r.litres, 0),
        value: d.runs.filter((r) => r.line === line).reduce((s, r) => s + r.value, 0),
        flushMin: runs.reduce((s, r) => s + r.flush_min, 0),
        runs: runs.sort((a, b) => b.litres - a.litres),
      };
    }),
  }));

  const heads: LnDayHead[] = days.map((d, i) => ({
    day: i + 1,
    label: dayLabel(d),
    wd: d.weekday.slice(0, 1),
    working: d.working,
    util: d.line_util,
  }));

  // ---- per line, the month
  const perLine = rows.map((row) => {
    const hours = row.cells.reduce((s, c) => s + c.hours, 0);
    const litres = row.cells.reduce((s, c) => s + c.litres, 0);
    const value = row.cells.reduce((s, c) => s + c.value, 0);
    const runs = row.cells.reduce((s, c) => s + c.runs.length, 0);
    const flushes = row.cells.reduce((s, c) => s + c.runs.filter((r) => r.flush_min > 0).length, 0);
    const flushMin = row.cells.reduce((s, c) => s + c.flushMin, 0);
    // busiest = most hours; several days tie at the 12 h cap, so the fuller one wins
    const best = row.cells.reduce((b, c) => (c.hours > b.hours || (c.hours === b.hours && c.litres > b.litres) ? c : b), row.cells[0]);
    return { line: row.line, hours, litres, value, runs, flushes, flushMin, best };
  });

  const hoursAll = perLine.reduce((s, l) => s + l.hours, 0);
  const litresAll = perLine.reduce((s, l) => s + l.litres, 0);
  const valueAll = perLine.reduce((s, l) => s + l.value, 0);
  const runsAll = perLine.reduce((s, l) => s + l.runs, 0);
  const flushesAll = perLine.reduce((s, l) => s + l.flushes, 0);
  const flushMinAll = perLine.reduce((s, l) => s + l.flushMin, 0);
  const busiest = perLine.reduce((b, l) => (l.hours > b.hours ? l : b), perLine[0]);

  // ---- the day utilisation first reached 100%
  const fullIdx = days.findIndex((d) => d.line_util >= 100);
  const full = fullIdx >= 0 ? days[fullIdx] : null;
  const before = fullIdx >= 0 ? days.slice(0, fullIdx) : days;
  const after = fullIdx >= 0 ? days.slice(fullIdx + 1) : [];
  const throttled = (d: Day) => d.decisions.some((x) => x.kind === "STORAGE_THROTTLE");
  const throttledBefore = before.filter((d) => d.working && throttled(d)).length;
  const workingBefore = before.filter((d) => d.working).length;
  const bestBefore = before.reduce((b, d) => (d.line_util > b.line_util ? d : b), days[0]);
  const bigShip = before.reduce((b, d) => (d.shipped_litres > b.shipped_litres ? d : b), days[0]);
  const prevWorking = [...before].reverse().find((d) => d.working) ?? null;
  const fullDays = days.filter((d) => d.line_util >= 100).length;
  const backIdx = after.findIndex((d) => d.working && throttled(d));
  const back = backIdx >= 0 ? after[backIdx] : null;
  const throttledAfter = after.filter((d) => d.working && throttled(d)).length;
  const workingAfter = after.filter((d) => d.working).length;

  // ---- what actually held production back: every blocked row names its binder
  const blocked = days.flatMap((d) => d.blocked);
  const blockedRows = blocked.length;
  const blockedByMaterial = blocked.filter((b) => /^(PM|RM)/.test(b.binder)).length;

  // ---- rated speeds
  const packs = [...new Set(Object.values(inputs.lines).flatMap((s) => Object.keys(s)))].sort(
    (a, b) => (PACK_ORDER.indexOf(a) + 1 || 99) - (PACK_ORDER.indexOf(b) + 1 || 99)
  );

  return (
    <div>
      <div className="flex items-baseline justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Lines</h1>
          <p className="text-sm text-zinc-400 mt-1">
            Six filling lines. {shift} hours a day, {workingDays} working days, Sundays off. Any oil runs on any line —
            only the bottle size decides.
          </p>
        </div>
        <div className="text-xs text-zinc-500 text-right">
          {inputs.meta.horizon[0]} to {inputs.meta.horizon[1]}
          <br />
          speeds: {inputs.provenance.lines}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mt-5">
        <Card
          title="Hours on the lines"
          value={`${hoursAll.toFixed(1)} h`}
          sub={`of ${fmt(capAll)} h possible — ${Math.round((hoursAll / capAll) * 100)}% used`}
          tone="text-amber-300"
        />
        <Card title="Filled" value={`${fmt(litresAll)} L`} sub={`in ${runsAll} runs`} />
        <Card title="Value filled" value={cr(valueAll)} sub="priced at May–Jul realisation" />
        <Card title="Oil changes" value={`${flushesAll}`} sub={`${flushMinAll} min of changeover`} />
        <Card title="Busiest line" value={busiest.line} sub={`${busiest.hours.toFixed(1)} h of ${fmt(capLine)} h`} />
      </div>

      <Section
        title="The month, line by line"
        right={<span className="text-xs text-zinc-500">hover a cell · click to open the day</span>}
      >
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <LnGantt rows={rows} days={heads} colours={colours} shift={shift} />
          <p className="text-xs text-zinc-500 mt-4">
            Each bar is how long the line was busy that day out of {shift} hours — filling plus the minutes lost to an
            oil change. Colour is the oil that filled the most litres on that line that day; a very short run still
            gets a sliver so you can see it happened. Hatched columns are Sundays, a grey baseline means the line stood
            idle on a working day. The bottom row is all six lines together, as a percentage of the{" "}
            {shift * LINES.length} line-hours a day gives you.
          </p>
        </div>

        <div className="mt-3 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
          <div className="text-xs uppercase tracking-wider text-zinc-500">The oils, biggest first</div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-2 mt-3">
            {oils.map(([code, o]) => (
              <div key={code} className="flex gap-2 items-start">
                <span className="mt-[5px] h-2.5 w-2.5 rounded-[3px] shrink-0" style={{ background: colours[code] }} />
                <div className="min-w-0">
                  <div className="text-sm tabular-nums">
                    {code} <span className="text-zinc-500">· {fmt(o.litres)} L</span>
                  </div>
                  <div className="text-[11px] text-zinc-500 truncate">mostly {o.topSku}</div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-zinc-600 mt-3">
            The replay carries the SAP raw-material code, not an oil name — the SKU under each code is the biggest thing
            that code filled in August, so you can recognise it.
          </p>
        </div>
      </Section>

      {full && prevWorking && back && (
        <Section title={`Why the bars are flat until day ${fullIdx + 1}`}>
          <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.04] p-5">
            <div className="flex items-baseline gap-3 flex-wrap">
              <div className="text-4xl font-semibold text-amber-300 tabular-nums">Day {fullIdx + 1}</div>
              <div className="text-sm text-zinc-400">{dayLabel(full)} — the first day the floor was full</div>
            </div>
            <p className="text-sm text-zinc-300 leading-relaxed mt-4 max-w-4xl">
              For the first {workingBefore} working days of August the lines barely moved. The best of them,{" "}
              {dayLabel(bestBefore)}, used {bestBefore.line_util}% of the day;{" "}
              {throttledBefore === workingBefore ? "every one of those days carries" : `${throttledBefore} of those ${workingBefore} days carry`}{" "}
              the same one-line reason in the replay —{" "}
              <span className="text-zinc-100">godown full, production capped to what can ship</span>. On{" "}
              {dayLabel(prevWorking)} the finished-goods godown stood at {prevWorking.storage.pct}% of its{" "}
              {fmt(prevWorking.storage.ceiling_l)} L ceiling, with {fmt(prevWorking.storage.headroom_l)} L of room —
              about {Math.round(prevWorking.storage.headroom_l / 1000)} thousand litres to play with when a single full
              day makes {fmt(full.made_litres)} L. There was nowhere to put the oil, so the machines waited.
            </p>
            <p className="text-sm text-zinc-300 leading-relaxed mt-3 max-w-4xl">
              Then the trucks came. {dayLabel(bigShip)} alone moved {fmt(bigShip.shipped_litres)} L out, and by the
              morning of {dayLabel(full)} the godown had fallen to {full.storage.pct}% —{" "}
              {fmt(full.storage.headroom_l)} L free, {Math.round(full.storage.headroom_l / prevWorking.storage.headroom_l)}×
              the room it had the working day before. That day carries no cap at all: all six lines ran the full {shift} hours,{" "}
              {fmt(hoursOn(full))} of {shift * LINES.length} line-hours, {full.runs.length} runs,{" "}
              {fmt(full.made_litres)} L, {money(full.made_value)}. It happened {fullDays === 2 ? "twice" : `${fullDays} times`} all
              month. The cap was back on {dayLabel(back)} and covered {throttledAfter} of the {workingAfter} working
              days that were left.
            </p>
            <p className="text-sm text-zinc-400 leading-relaxed mt-3 max-w-4xl">
              So the flat bars are not a machine problem.{" "}
              {blockedByMaterial === blockedRows
                ? `Every one of the ${fmt(blockedRows)} blocked SKU-days in the month is held by a material — packaging or oil. None is held by a line.`
                : `${fmt(blockedByMaterial)} of the ${fmt(blockedRows)} blocked SKU-days in the month are held by a material — packaging or oil.`}{" "}
              The floor gave back {Math.round(100 - (hoursAll / capAll) * 100)}% of its hours while the godown sat at
              its ceiling.
            </p>
            <div className="mt-4 flex gap-2 flex-wrap">
              <Link href="/storage" className="text-xs px-3 py-1.5 rounded-md bg-amber-500/15 text-amber-300 hover:bg-amber-500/25">
                See the storage story →
              </Link>
              <Link href={`/day/${fullIdx + 1}`} className="text-xs px-3 py-1.5 rounded-md bg-zinc-800 text-zinc-300 hover:bg-zinc-700">
                Open {dayLabel(full)} →
              </Link>
            </div>
          </div>
        </Section>
      )}

      <Section title="Each line's month">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {perLine.map((l) => {
            const pct = Math.round((l.hours / capLine) * 100);
            const sizes = Object.keys(inputs.lines[l.line] ?? {});
            return (
              <div key={l.line} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <div className="font-semibold">{l.line}</div>
                  <div className="flex gap-1">
                    {sizes.map((s) => (
                      <Pill key={s}>{s}</Pill>
                    ))}
                  </div>
                </div>
                <div className="flex items-baseline gap-2 mt-3">
                  <div className="text-3xl font-semibold tabular-nums">{l.hours.toFixed(1)}</div>
                  <div className="text-sm text-zinc-500">h of {fmt(capLine)} h</div>
                </div>
                <div className="h-2 rounded-full bg-zinc-800 overflow-hidden mt-2">
                  <div className="h-full bg-amber-500/70 rounded-full" style={{ width: `${Math.min(100, pct)}%` }} />
                </div>
                <div className="text-[11px] text-zinc-500 mt-1 tabular-nums">
                  {pct}% used · {fmt(capLine - l.hours)} h idle
                </div>
                <dl className="grid grid-cols-2 gap-y-2 mt-4 text-sm">
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Filled</dt>
                    <dd className="tabular-nums">{fmt(l.litres)} L</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Value</dt>
                    <dd className="tabular-nums">{money(l.value)}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Runs</dt>
                    <dd className="tabular-nums">{l.runs}</dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-wider text-zinc-500">Oil changes</dt>
                    <dd className="tabular-nums">
                      {l.flushes} <span className="text-zinc-500 text-xs">· {l.flushMin} min</span>
                    </dd>
                  </div>
                </dl>
                <div className="text-xs text-zinc-500 mt-4 pt-3 border-t border-zinc-800">
                  Busiest day{" "}
                  <Link href={`/day/${l.best.day}`} className="text-zinc-300 hover:text-amber-300">
                    {l.best.label}
                  </Link>{" "}
                  — {l.best.hours.toFixed(1)} h, {fmt(l.best.litres)} L
                </div>
              </div>
            );
          })}
        </div>
        <p className="text-xs text-zinc-500 mt-3">
          Hours are the line&rsquo;s clock: filling time plus the changeover minutes. Every oil change also costs{" "}
          {fmt(inputs.rules.flush_litres)} L of the next oil{inputs.rules.flush_oil_reused_monthly ? ", which is reused later in the month" : ""}.
        </p>
      </Section>

      <Section title="Rated speeds">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
                <th className="py-3 px-4 font-medium">Line</th>
                {packs.map((p) => (
                  <th key={p} className="py-3 px-4 font-medium text-right">{p}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {LINES.map((line) => (
                <tr key={line} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2.5 px-4 text-zinc-300">{line}</td>
                  {packs.map((p) => {
                    const v = inputs.lines[line]?.[p];
                    return (
                      <td key={p} className="py-2.5 px-4 text-right tabular-nums">
                        {v ? (
                          <>
                            {fmt(v)} <span className="text-zinc-600 text-xs">pcs/hr</span>
                          </>
                        ) : (
                          <span className="text-zinc-700">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="grid md:grid-cols-2 gap-3 mt-3">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="text-xs uppercase tracking-wider text-zinc-500">Corrected</div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              Clear Pack 5 L is {fmt(inputs.lines["Clear Pack"]?.["5L"] ?? 0)} pcs/hr here — corrected down from the
              3,000 the line sheet carried.
            </p>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="text-xs uppercase tracking-wider text-zinc-500">Measured, and assumed</div>
            <p className="text-sm text-zinc-300 mt-2 leading-relaxed">
              Line speeds are measured. The hours on this page are not: the replay fills at the rated speed, and says so
              — &ldquo;rated line speed, not the {Math.round(inputs.rules.efficiency_observed * 100)}% observed&rdquo;.
              At the observed rate every bar above would be longer.
            </p>
          </div>
        </div>
        <p className="text-xs text-zinc-600 mt-3">
          A dash means that bottle size is not set up on that line. Sizes are the only thing that ties a product to a
          machine — {inputs.rules.any_oil_any_line ? "any oil runs on any line." : "oil-to-line rules apply."}
        </p>
      </Section>
    </div>
  );
}

function hoursOn(d: Day) {
  return Object.values(d.line_hours).reduce((s, h) => s + h, 0);
}
