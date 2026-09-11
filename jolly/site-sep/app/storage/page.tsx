import { getStorage, getSpine, getOverview, getQuestions, fmt, dlabel, countWord, litresProse, plural, plainWords } from "../../lib/data";
import { Card, Section, Pill } from "../../components/Card";
import SimBadge from "../../components/SimBadge";
import StorageChart, { type StoragePoint } from "../../components/StorageChart";

export const metadata = {
  title: "Godown",
  description:
    "How full the godown is on every day of the September plan — stock not yet billed, stock billed but not yet trucked, and the limit we take as full.",
};

// Sentence numbers in Indian style ("5.60 lakh litres") come from lib — litresProse — so every page says them the same way.
const dayWord = (n: number) => plural(n, "day", "days");
// The open question is written for the office ("BH-BT", "pallet positions"). Say it
// in godown words — the SAP warehouse code goes, the numbers in it are untouched.
const floorQuestion = (s: string) =>
  plainWords(s).replace(/\s*\((?:BH|GP)-[A-Z]+\)/g, "").replace(/pallet positions/gi, "pallet places");

export default function StoragePage() {
  const S = getStorage();
  const spine = getSpine();
  const O = getOverview();
  const q2 = getQuestions().items.find((q) => q.n === 2);
  const countedOn = dlabel(O.meta.frozen); // the one real day — the stock count on the eve of the month

  // Join the godown series with the day spine (made/billed) — same 1-based day n.
  const byN = new Map(spine.map((d) => [d.n, d]));
  const points: StoragePoint[] = S.series.map((s) => {
    const sp = byN.get(s.n);
    return {
      n: s.n, date: s.date, dow: (sp?.weekday ?? "").slice(0, 3), working: s.working,
      fg: s.fg_in_godown_l, inv: s.invoiced_not_trucked_l, physical: s.physical_l,
      pct: s.pct, headroom: s.headroom_l, made: sp?.made_l ?? 0, shipped: sp?.shipped_l ?? 0,
      throttle: S.throttles.some((t) => t.day === s.date),
    };
  });

  const ceiling = S.ceiling.working_l;
  const safety = ceiling * 0.95;
  const open = points[0];
  const peak = points.reduce((a, b) => (b.physical > a.physical ? b : a));
  const at95 = points.filter((p) => p.physical >= safety - 1).length;

  // Billed is not the same as trucked: the generator computes both per day. The biggest
  // drop, biggest billing day and biggest truck day come pre-computed from data.
  const lagDays = S.invoice_truck_lag_days;
  const fall = S.biggest_fall;
  const bigInv = S.biggest_invoicing_day;
  const bigTrk = S.biggest_trucked_day;

  // The day(s) the plan made less because the godown was full — what the plan did, from data.
  const slowDays = S.throttles.map((t) => {
    const row = S.series.find((x) => x.date === t.day)!;
    return {
      ...t, n: row.n, point: points[row.n - 1],
      next: points[row.n] ?? null, // the following day, if any
    };
  });

  const standingL = S.standing_at_open.litres;
  const shipDays = points.filter((p) => p.shipped > 0).length;
  const avgInv = points.reduce((a, p) => a + p.inv, 0) / points.length;

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="max-w-3xl">
          <h1 className="text-2xl font-bold">
            Godown <SimBadge kind="plan" note="The computer's plan for September. Nothing here has happened yet." />
          </h1>
          <p className="text-lg text-zinc-100 mt-2">
            End of day 1 ({dlabel(open.date)}): the godown is{" "}
            <span className="font-semibold text-amber-300">{open.pct}% full</span> — {litresProse(open.physical)} in{" "}
            {litresProse(ceiling)}.
          </p>
          <p className="text-sm text-zinc-300 mt-1">
            Of that, {litresProse(open.inv)} is billed, but the truck has not left yet. Fullest day of the plan:{" "}
            {dlabel(peak.date)}, {peak.pct}% full.
          </p>
          <p className="text-sm text-zinc-400 mt-2">
            We take the godown as full at <span className="text-zinc-200">{litresProse(ceiling)}</span> — Daman&apos;s number,
            not measured. Squeezed hard, {litresProse(S.ceiling.peak_l)}. Every percentage on this page leans on that number.
          </p>
        </div>
        <div className="text-right text-xs text-zinc-500 max-w-sm">
          The limit is <span className="text-amber-300">Daman&apos;s number</span>, not measured.
          {q2 && <><br />Still to check: {floorQuestion(q2.one_liner)}</>}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 mt-5">
        <Card title={`End of day 1 — ${dlabel(open.date)}`} value={`${open.pct}% full`}
          sub={`${fmt(open.physical)} L of ${fmt(ceiling)} L — ${fmt(open.inv)} L of it billed, truck not left`} tone="text-amber-300" />
        <Card title="Fullest day" value={`${peak.pct}% full`}
          sub={`${fmt(peak.physical)} L on ${dlabel(peak.date)} — ${fmt(ceiling - peak.physical)} L of space left`} tone="text-red-400" />
        <Card title="Days at 95% or more" value={`${at95} of ${points.length}`}
          sub={S.days_ge_100.length ? `100% full on ${S.days_ge_100.map(dlabel).join(", ")}` : "never reaches 100%"} tone="text-red-400" />
        <Card title="Days production was slowed" value={`${S.throttles.length}`}
          sub={S.throttles.length ? "godown full — the plan made less so it would fit" : "the plan never had to make less for want of space"} tone="text-amber-300" />
        <Card title="Biggest one-day drop" value={`−${fmt(fall.fall_l)} L`}
          sub={`${dlabel(fall.date)} — ${fall.source_date ? `${dlabel(fall.source_date)}'s billed stock leaves by truck` : `trucks leave ${lagDays} ${dayWord(lagDays)} after billing`}: ${fmt(fall.trucked_out_l)} L out, ${fmt(fall.made_l)} L made`} tone="text-emerald-400" />
      </div>

      <Section title="Every day of September — how full"
        right={<span className="text-xs text-zinc-500">white line = litres in the godown · the computer&apos;s plan</span>}>
        <StorageChart points={points} workingL={ceiling} peakL={S.ceiling.peak_l} />
      </Section>

      {slowDays.map((t) => (
        <Section key={t.day} title={`${dlabel(t.day)} — godown full, so the plan made less`}>
          <div className="rounded-xl border border-amber-800/50 bg-amber-950/15 p-5">
            <div className="grid lg:grid-cols-3 gap-5">
              <div className="lg:col-span-2">
                <div className="text-xs uppercase tracking-wider text-amber-300/80">Godown full — production slowed · the computer&apos;s plan</div>
                <div className="text-xl font-semibold mt-1 text-zinc-50">{t.point.pct}% full by the end of the day</div>
                <p className="text-sm text-zinc-300 mt-3 max-w-2xl">
                  The day started {t.pct_start_of_day}% full, with only {fmt(t.headroom_l)} L of space left. So the plan did
                  not run the machines flat out.{" "}
                  {t.point.made === t.headroom_l
                    ? <>It made only what would fit — {fmt(t.point.made)} L — and billed {fmt(t.point.shipped)} L.</>
                    : <>It made {fmt(t.point.made)} L and billed {fmt(t.point.shipped)} L.</>}{" "}
                  The day ended {t.point.pct}% full, with {fmt(t.point.headroom)} L of space left.
                  {t.next && (
                    <> The trucks left the next day: by the end of {dlabel(t.next.date)} the godown was back to{" "}
                    {t.next.pct}% ({fmt(t.point.physical - t.next.physical)} L gone).</>
                  )}
                </p>
              </div>
              <div className="flex lg:flex-col gap-6 lg:gap-3">
                <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Start of day</div><div className="text-3xl font-semibold text-amber-300">{t.pct_start_of_day}%</div></div>
                <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">End of day</div><div className="text-3xl font-semibold text-red-400">{t.point.pct}%</div></div>
                <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Made / billed</div><div className="text-lg font-semibold text-zinc-100">{fmt(t.point.made)} / {fmt(t.point.shipped)} L</div></div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-amber-900/40 text-xs text-zinc-400">
              This is not a mistake. The plan slows production on purpose when the godown is full. It happens{" "}
              {S.throttles.length === 1 ? "once" : `${countWord(S.throttles.length)} times`} in the month. A real September
              works the same way: if the godown starts this full, something must leave before the machines can run free.
            </div>
          </div>
        </Section>
      ))}

      <Section title={`Why billed stock still takes space — the ${countWord(lagDays)}-day truck wait`}>
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <ol className="space-y-2.5 text-[15px] leading-relaxed text-zinc-200 list-none">
              <li><span className="text-zinc-600 mr-2">1.</span>When a bill is made, SAP removes the stock from the books. On paper, it is gone.</li>
              <li><span className="text-zinc-600 mr-2">2.</span>But the cartons stay in the godown until the truck leaves — about {lagDays} {dayWord(lagDays)} later. The plan takes that {lagDays} {dayWord(lagDays)} as fixed. Checked against the factory gate log, it is the usual wait for our trucks — but some take much longer, and the plan ignores those.</li>
              <li><span className="text-zinc-600 mr-2">3.</span>So how full the godown really is = stock not yet billed <span className="text-sky-300">(blue)</span> + billed, but the truck has not left <span className="text-amber-300">(orange)</span>. Both take the same space.</li>
              <li><span className="text-zinc-600 mr-2">4.</span>On an average day of the plan, <span className="text-zinc-100">{fmt(avgInv)} L</span> is sitting billed with the truck not left — space the books say is empty.</li>
              <li><span className="text-zinc-600 mr-2">5.</span>If trucks take longer than {lagDays} {dayWord(lagDays)}, every bar on this page gets taller. Plan by the godown, not by the books.</li>
            </ol>
            <div className="mt-4 pt-3 border-t border-zinc-800 text-sm text-zinc-400">
              Biggest billing day: {dlabel(bigInv.date)} — {fmt(bigInv.invoiced_l)} L billed (the trucks leave {lagDays}{" "}
              {dayWord(lagDays)} later). Biggest truck day: {dlabel(bigTrk.date)} — {fmt(bigTrk.trucked_out_l)} L out of the
              gate. Bills go out on {shipDays} of {points.length} days.
            </div>
          </div>
          <div className="space-y-3">
            <div className="rounded-xl border border-amber-800/50 bg-amber-950/15 p-4">
              <div className="text-xs uppercase tracking-wider text-amber-300/90 mb-1">
                Day 1: billed, truck not left = {fmt(standingL)} L · our guess
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                The plan starts the month with {fmt(standingL)} L of stock that is billed but still waiting for a truck.
                That is our guess, not a count.
              </p>
              <p className="text-xs text-amber-300/80 mt-2">
                Stock billed but not trucked on day 1 is not counted. So the godown is really fuller than every chart
                here shows.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-xs text-zinc-400">
              <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5">What is real, what is a guess</div>
              <div><Pill tone="green">counted — real</Pill> <span className="ml-1">the stock in the godown on {countedOn} evening, and the customer orders waiting to go.</span></div>
              <div className="mt-1.5"><Pill tone="amber">our guess — not measured</Pill> <span className="ml-1">the {fmt(ceiling)} L limit ({fmt(S.ceiling.peak_l)} L squeezed) — Daman&apos;s number, still to be checked; the {lagDays}-day truck wait; and {fmt(standingL)} L billed-but-not-trucked on day 1.</span></div>
              <div className="mt-1.5"><Pill tone="violet">the computer&apos;s plan</Pill> <span className="ml-1">every daily figure. September has not happened.</span></div>
            </div>
          </div>
        </div>
      </Section>

      <Section title="Day by day" right={<span className="text-xs text-zinc-500">Sundays dim · ▲ = godown full, the plan made less that day</span>}>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400">
              <tr className="text-left">
                <th className="px-3 py-2 font-medium">Day</th>
                <th className="px-3 py-2 font-medium text-right">In the godown</th>
                <th className="px-3 py-2 font-medium w-48">How full</th>
                <th className="px-3 py-2 font-medium text-right">Space left</th>
                <th className="px-3 py-2 font-medium text-right">Made</th>
                <th className="px-3 py-2 font-medium text-right">Billed</th>
                <th className="px-3 py-2 font-medium"> </th>
              </tr>
            </thead>
            <tbody>
              {points.map((p) => (
                <tr key={p.n} className={`border-t border-zinc-900 ${p.working ? "" : "opacity-40"}`}>
                  <td className="px-3 py-1.5 whitespace-nowrap"><span className="text-zinc-500 tabular-nums mr-2">{String(p.n).padStart(2, "0")}</span>{dlabel(p.date)} <span className="text-zinc-600">{p.dow}</span></td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{fmt(p.physical)} L</td>
                  <td className="px-3 py-1.5">
                    <div className="flex items-center gap-2">
                      <div className="h-2 grow rounded-full bg-zinc-800 overflow-hidden flex" title="blue = not yet billed · orange = billed, truck not left">
                        <div className="bg-sky-500/70" style={{ width: `${(p.fg / ceiling) * 100}%` }} />
                        <div className="bg-amber-500/70" style={{ width: `${(p.inv / ceiling) * 100}%` }} />
                      </div>
                      <span className={`tabular-nums w-12 text-right ${p.physical >= safety - 1 ? "text-red-400" : "text-zinc-300"}`}>{p.pct}%</span>
                    </div>
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-400">{fmt(p.headroom)} L</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{p.made ? `${fmt(p.made)} L` : <span className="text-zinc-700">—</span>}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{p.shipped ? `${fmt(p.shipped)} L` : <span className="text-zinc-700">—</span>}</td>
                  <td className="px-3 py-1.5">{p.throttle && <span className="text-amber-400" title="Godown full — the plan made less this day">▲</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Blue = stock not yet billed. Orange = billed, but the truck has not left (about {lagDays} {dayWord(lagDays)}). Both
          take space. Every row is the computer&apos;s plan, against Daman&apos;s limit — <span className="text-amber-300">not measured</span>.
        </p>
      </Section>

      <p className="mt-8 text-[11px] text-zinc-600 max-w-3xl">
        Where these numbers come from: the stock counted in SAP on {countedOn} evening. The godown limit is Daman&apos;s
        capacity sheet — not measured, still to be checked. The {lagDays}-day truck wait is our guess.
        Everything day by day is the computer&apos;s plan — September has not happened.
      </p>
    </div>
  );
}
