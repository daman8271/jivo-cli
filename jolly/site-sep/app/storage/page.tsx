import { getStorage, getSpine, getDay, getHonesty, getQuestions, fmt, dlabel, countWord } from "../../lib/data";
import { Card, Section, Pill } from "../../components/Card";
import SimBadge from "../../components/SimBadge";
import StorageChart, { type StoragePoint } from "../../components/StorageChart";

export const metadata = {
  title: "Storage",
  description:
    "Planned godown occupancy across September against the assumed working ceiling — the invoice-to-truck lag, the capped days, and the floor number the plan steers by.",
};

export default function StoragePage() {
  const S = getStorage();
  const spine = getSpine();
  const H = getHonesty();
  const q2 = getQuestions().items.find((q) => q.n === 2);

  // Join the storage series with the day spine (made/shipped) — same 1-based day n.
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

  // Invoiced ≠ trucked: the generator computes both per day. The biggest fall,
  // biggest invoicing day and biggest gate-out day come pre-computed from data.
  const lagDays = S.invoice_truck_lag_days;
  const fall = S.biggest_fall;
  const bigInv = S.biggest_invoicing_day;
  const bigTrk = S.biggest_trucked_day;

  // The throttle day(s): what the sim actually did, quoted from the day file.
  const throttles = S.throttles.map((t) => {
    const row = S.series.find((x) => x.date === t.day)!;
    const dd = getDay(row.n);
    const decision = dd.decisions.find((x) => x.kind === "STORAGE_THROTTLE");
    return {
      ...t, n: row.n, point: points[row.n - 1],
      text: decision?.text ?? "", made: dd.made_litres, shipped: dd.shipped_litres,
      next: points[row.n] ?? null, // the following day, if any
    };
  });

  // Declared-assumption strings, quoted from the data rather than retyped.
  const lagAssumption = H.assumed.find((a) => a.includes("invoice-to-truck")) ?? "invoice→truck lag (assumed)";
  const standingProv = H.provenance.standing ?? S.standing_at_open.note;

  const shipDays = points.filter((p) => p.shipped > 0).length;
  const avgInv = points.reduce((a, p) => a + p.inv, 0) / points.length;

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">
            Storage <SimBadge kind="plan" />
          </h1>
          <p className="text-zinc-400 text-sm mt-1 max-w-2xl">
            Where the plan puts every carton before a truck takes it. The godown is taken to hold{" "}
            <span className="text-zinc-200">{fmt(ceiling)} L</span> working / {fmt(S.ceiling.peak_l)} L peak{" "}
            <SimBadge kind="assumed" note={S.ceiling.source} /> — {S.ceiling.source}. Until that is settled
            (open question {S.ceiling.open_question}), every percentage on this page leans on it.
          </p>
        </div>
        <div className="text-right text-xs text-zinc-500 max-w-sm">
          Ceiling is <span className="text-amber-300">assumed</span>, not measured.
          {q2 && <><br />Q{q2.n}: {q2.one_liner}</>}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 mt-5">
        <Card title={`${dlabel(open.date)}, day 1 floor`} value={`${open.pct}%`}
          sub={`${fmt(open.physical)} L of ${fmt(ceiling)} L — ${fmt(open.inv)} L of it already invoiced`} tone="text-amber-300" />
        <Card title="Planned peak" value={`${peak.pct}%`}
          sub={`${fmt(peak.physical)} L on ${dlabel(peak.date)} — ${fmt(ceiling - peak.physical)} L spare`} tone="text-red-400" />
        <Card title="Days at 95% or over" value={`${at95} of ${points.length}`}
          sub={`hits 100% on ${S.days_ge_100.length} day${S.days_ge_100.length === 1 ? "" : "s"} (${S.days_ge_100.map(dlabel).join(", ")})`} tone="text-red-400" />
        <Card title="Times production was capped" value={`${S.throttles.length}`}
          sub="the sim cut the build to what could ship, rather than overfill the godown" tone="text-amber-300" />
        <Card title="Biggest one-day fall" value={`−${fmt(fall.fall_l)} L`}
          sub={`${dlabel(fall.date)} — ${fall.source_date ? `${dlabel(fall.source_date)}'s invoices truck out on the ${lagDays}-day lag` : `trucks leave on the ${lagDays}-day lag`}: ${fmt(fall.trucked_out_l)} L gate out, ${fmt(fall.made_l)} L filled`} tone="text-emerald-400" />
      </div>

      <Section title="Every day of September, against the ceiling"
        right={<span className="text-xs text-zinc-500">white line = planned litres standing on the floor · <SimBadge kind="simulated" /></span>}>
        <StorageChart points={points} workingL={ceiling} peakL={S.ceiling.peak_l} />
      </Section>

      {throttles.map((t) => (
        <Section key={t.day} title={`The ${t.point.pct}% day — ${dlabel(t.day)}, and what the sim did about it`}>
          <div className="rounded-xl border border-amber-800/50 bg-amber-950/15 p-5">
            <div className="grid lg:grid-cols-3 gap-5">
              <div className="lg:col-span-2">
                <div className="text-xs uppercase tracking-wider text-amber-300/80">STORAGE_THROTTLE <SimBadge kind="simulated" /></div>
                <div className="text-xl font-semibold mt-1 text-zinc-50">&ldquo;{t.text}&rdquo;</div>
                <p className="text-sm text-zinc-300 mt-3 max-w-2xl">
                  The day opened at {t.pct_start_of_day}% with only {fmt(t.headroom_l)} L of headroom, so instead of
                  running the lines flat out the planner capped the build.{" "}
                  {t.made === t.headroom_l
                    ? <>It made exactly the space it had — {fmt(t.made)} L, litre for litre the morning&apos;s headroom — and invoiced {fmt(t.shipped)} L,</>
                    : <>It made {fmt(t.made)} L and invoiced {fmt(t.shipped)} L,</>}{" "}
                  and the floor ended the day at {t.point.pct}% — full to the assumed ceiling, with{" "}
                  {fmt(t.point.headroom)} L of room.
                  {t.next && (
                    <> The release comes the next day: by end of {dlabel(t.next.date)} the floor is back to{" "}
                    {t.next.pct}% ({fmt(t.point.physical - t.next.physical)} L cleared).</>
                  )}
                </p>
              </div>
              <div className="flex lg:flex-col gap-6 lg:gap-3">
                <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Start of day</div><div className="text-3xl font-semibold text-amber-300">{t.pct_start_of_day}%</div></div>
                <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">End of day</div><div className="text-3xl font-semibold text-red-400">{t.point.pct}%</div></div>
                <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Made / invoiced</div><div className="text-lg font-semibold text-zinc-100">{fmt(t.made)} / {fmt(t.shipped)} L</div></div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-amber-900/40 text-xs text-zinc-400">
              This is the plan handling its own constraint, not an accident: the cap is a scheduled decision in the day
              file, and it fires exactly {S.throttles.length === 1 ? "once" : `${S.throttles.length} times`} in the month.
              A real September inherits the same physics — if the floor opens this full, something must ship before the
              lines can run free.
            </div>
          </div>
        </Section>
      ))}

      <Section title={`Why “invoiced” still takes floor space — the ${countWord(lagDays)}-day lag, plainly`}>
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <ol className="space-y-2.5 text-[15px] leading-relaxed text-zinc-200 list-none">
              <li><span className="text-zinc-600 mr-2">1.</span>The moment an invoice is cut, SAP takes the stock off the books. On paper, it is gone.</li>
              <li><span className="text-zinc-600 mr-2">2.</span>The truck leaves later — the sim models &ldquo;{lagAssumption}&rdquo; <SimBadge kind="assumed" />. Until it leaves, those cartons stand on our floor.</li>
              <li><span className="text-zinc-600 mr-2">3.</span>So the floor number = finished goods in the godown <span className="text-sky-300">(blue)</span> + invoiced-but-not-yet-trucked <span className="text-amber-300">(amber)</span>. Both take up the same space.</li>
              <li><span className="text-zinc-600 mr-2">4.</span>Across the month the plan keeps an average of <span className="text-zinc-100">{fmt(avgInv)} L</span> standing in that amber state — space the book says is already empty.</li>
              <li><span className="text-zinc-600 mr-2">5.</span>A slower truck than the assumed lag makes every bar on this page taller. Plan against the floor number, never the book number.</li>
            </ol>
            <div className="mt-4 pt-3 border-t border-zinc-800 text-sm text-zinc-400">
              The single biggest planned invoicing day is {dlabel(bigInv.date)} — {fmt(bigInv.invoiced_l)} L invoiced
              (the trucks leave on the {lagDays}-day lag); the biggest gate-out day is {dlabel(bigTrk.date)} —{" "}
              {fmt(bigTrk.trucked_out_l)} L actually rolling out. The plan invoices on {shipDays} of {points.length}{" "}
              days.
            </div>
          </div>
          <div className="space-y-3">
            <div className="rounded-xl border border-amber-800/50 bg-amber-950/15 p-4">
              <div className="text-xs uppercase tracking-wider text-amber-300/90 mb-1">
                Standing stock at open: {fmt(S.standing_at_open.litres)} L <SimBadge kind="assumed" />
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                The model starts the month with {fmt(S.standing_at_open.litres)} L already standing invoiced on the
                floor — {S.standing_at_open.note}.
              </p>
              <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                From the freeze record: &ldquo;{standingProv}&rdquo;
              </p>
              <p className="text-xs text-amber-300/80 mt-2">
                If invoiced-but-not-yet-trucked stock was really standing on 31 Aug, day 1 has less room than every
                chart above shows.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-xs text-zinc-400">
              <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5">Honest about this page</div>
              <div><Pill tone="green">measured</Pill> <span className="ml-1">the 31-Aug opening stock and the order backlog the dispatches answer.</span></div>
              <div className="mt-1.5"><Pill tone="amber">assumed</Pill> <span className="ml-1">the {fmt(ceiling)} L / {fmt(S.ceiling.peak_l)} L ceiling ({S.ceiling.open_question}), the &ldquo;{lagAssumption}&rdquo;, and standing stock {fmt(S.standing_at_open.litres)} at open.</span></div>
              <div className="mt-1.5"><Pill tone="violet">simulated</Pill> <span className="ml-1">every daily litre — September has not happened.</span></div>
            </div>
          </div>
        </div>
      </Section>

      <Section title="Day by day" right={<span className="text-xs text-zinc-500">Sundays dim · ▲ = the sim capped production that day</span>}>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400">
              <tr className="text-left">
                <th className="px-3 py-2 font-medium">Day</th>
                <th className="px-3 py-2 font-medium text-right">On the floor</th>
                <th className="px-3 py-2 font-medium w-48">Full</th>
                <th className="px-3 py-2 font-medium text-right">Room left</th>
                <th className="px-3 py-2 font-medium text-right">Made</th>
                <th className="px-3 py-2 font-medium text-right">Invoiced</th>
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
                      <div className="h-2 grow rounded-full bg-zinc-800 overflow-hidden flex">
                        <div className="bg-sky-500/70" style={{ width: `${(p.fg / ceiling) * 100}%` }} />
                        <div className="bg-amber-500/70" style={{ width: `${(p.inv / ceiling) * 100}%` }} />
                      </div>
                      <span className={`tabular-nums w-12 text-right ${p.physical >= safety - 1 ? "text-red-400" : "text-zinc-300"}`}>{p.pct}%</span>
                    </div>
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-400">{fmt(p.headroom)} L</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{p.made ? `${fmt(p.made)} L` : <span className="text-zinc-700">—</span>}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{p.shipped ? `${fmt(p.shipped)} L` : <span className="text-zinc-700">—</span>}</td>
                  <td className="px-3 py-1.5">{p.throttle && <span className="text-amber-400" title="The sim capped production to what could ship">▲</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Blue = finished goods in the godown. Amber = invoiced but still standing here (the assumed lag). Both take up
          the same space, and every row is the simulator&apos;s plan against the <span className="text-amber-300">assumed</span> ceiling.
        </p>
      </Section>
    </div>
  );
}
