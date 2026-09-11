import type { Scenario, ScenariosData } from "../lib/types";
import { fmt, cr, money } from "../lib/data";
import { Pill } from "./Card";

// The shift options, each run through the same computer plan for the whole
// month. The advice is computed from each option's own numbers (most litres,
// best use of the extra hours, a longer shift that makes less) — nothing here
// is hand-typed, and the row count follows the data. Words: PLAIN-LANGUAGE.md.
export default function ScenarioBoard({ data }: { data: ScenariosData }) {
  const base = data.baseline;
  // cheapest first — sorted by how many extra machine hours each option asks for
  const sc = [...data.scenarios].sort(
    (a, b) => a.extra_line_hours_offered - b.extra_line_hours_offered || a.shift_hours - b.shift_hours
  );
  const best = sc.reduce((a, b) => (b.made_l > a.made_l ? b : a));
  const bestValue = sc.reduce((a, b) =>
    (b.pct_extra_hours_used ?? -1) > (a.pct_extra_hours_used ?? -1) ? b : a
  );
  // the option just below the biggest one — what the last few hours actually buy
  const runnerUp = sc
    .filter((s) => s.extra_line_hours_offered < best.extra_line_hours_offered)
    .reduce<Scenario | null>((a, b) => (a === null || b.made_l > a.made_l ? b : a), null);
  const maxMade = Math.max(base.made_l, ...sc.map((s) => s.made_l));
  const wagesCaveat = sc.some((s) => /wage/i.test(s.note));

  // plain names, built from the option's own hours and days
  const sundays = (workingDays: number) => (workingDays > base.working_days ? "Sundays on" : "Sundays off");
  const name = (s: Scenario) =>
    s.taper
      ? `${s.taper.front_hours} hours up to day ${s.taper.boundary_day}, then ${s.taper.tail_hours} hours`
      : `${s.shift_hours} hours a day`;
  const shortName = (s: Scenario) => (s.taper ? name(s) : `${s.shift_hours} hours`);
  const flatFor = (s: Scenario) =>
    s.taper
      ? sc.find((x) => !x.taper && x.shift_hours === s.taper!.front_hours && x.working_days === s.working_days)
      : undefined;
  const slowed = (n: number) => (n === 0 ? "never slowed" : `slowed ${n} ${n === 1 ? "time" : "times"}`);
  const fullDays = (n: number) => `nearly full on ${n} ${n === 1 ? "day" : "days"}`;

  const advice = (s: Scenario): { tone: string; tag: string; text: string } => {
    const pct = s.pct_extra_hours_used ?? 0;
    if (s.taper) {
      const flat = flatFor(s);
      const share = s.share_of_flat_front_gain_pct;
      if (flat && typeof share === "number") {
        const hoursShare = Math.round((s.extra_line_hours_offered / flat.extra_line_hours_offered) * 100);
        if (share >= hoursShare)
          return {
            tone: "blue",
            tag: "middle path",
            text: `Keeps ${share}% of the ${flat.shift_hours}-hour gain, using ${hoursShare}% of its extra hours. A fair middle path.`,
          };
        return {
          tone: "red",
          tag: "not worth it",
          text: `Keeps only ${share}% of the ${flat.shift_hours}-hour gain. Dropping to ${s.taper.tail_hours} hours loses most of it.`,
        };
      }
    }
    if (s.id === bestValue.id)
      return {
        tone: "green",
        tag: "best value",
        text: `${pct}% of the extra hours actually ran — the best on this table. Start here.${
          /wage/i.test(s.note) ? " Sunday wages are not counted." : ""
        }`,
      };
    if (s.id === best.id) {
      const cmp =
        runnerUp && runnerUp.id !== s.id
          ? ` ${fmt(s.extra_line_hours_offered - runnerUp.extra_line_hours_offered)} more machine hours than ${shortName(
              runnerUp
            )}, for only ${fmt(s.made_l - runnerUp.made_l)} L more.`
          : "";
      return {
        tone: "amber",
        tag: "most litres",
        text: `Makes the most. But only ${pct}% of the extra hours ran, and the godown is ${fullDays(s.days_storage_ge_95)}.${cmp}`,
      };
    }
    if (s.made_l < best.made_l && s.extra_line_hours_offered > best.extra_line_hours_offered)
      return {
        tone: "red",
        tag: "not worth it",
        text: `More hours than ${shortName(best)}, yet makes ${fmt(best.made_l - s.made_l)} L less.`,
      };
    if (s.days_storage_ge_95 >= 10)
      return {
        tone: "amber",
        tag: "godown fills up",
        text: `The godown is ${fullDays(s.days_storage_ge_95)} and production is ${slowed(
          s.storage_throttle_events
        )} for space. Only ${pct}% of the extra hours ran.`,
      };
    return { tone: "zinc", tag: "", text: `${pct}% of the extra hours ran.` };
  };

  // the one-line takeaway, from the same numbers
  const tapers = sc
    .filter((s) => s.taper && typeof s.share_of_flat_front_gain_pct === "number" && flatFor(s))
    .sort((a, b) => b.taper!.tail_hours - a.taper!.tail_hours);
  const taperLine =
    tapers.length > 0
      ? `Start long and slow down after day ${tapers[0].taper!.boundary_day}: ` +
        tapers
          .map(
            (s, i) =>
              `drop to ${s.taper!.tail_hours} hours and you keep ${i === 0 ? "" : "only "}${
                s.share_of_flat_front_gain_pct
              }% of the ${flatFor(s)!.shift_hours}-hour gain`
          )
          .join("; ") +
        "."
      : "";

  const MadeCell = ({ made }: { made: number }) => (
    <div className="min-w-[140px]">
      <div className="tabular-nums text-zinc-100 font-medium">{fmt(made)} L</div>
      <div className="h-1.5 rounded-full bg-zinc-800 mt-1.5 overflow-hidden">
        <div className="h-full bg-amber-500/80" style={{ width: `${(made / maxMade) * 100}%` }} />
      </div>
    </div>
  );

  return (
    <div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
              <th className="p-3 font-medium">Shift</th>
              <th className="p-3 font-medium">Litres made</th>
              <th className="p-3 font-medium">Extra</th>
              <th className="p-3 font-medium">Worth</th>
              <th className="p-3 font-medium">Of the extra hours, how many ran</th>
              <th className="p-3 font-medium">Godown</th>
              <th className="p-3 font-medium">What to do</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800 align-top">
            <tr>
              <td className="p-3 whitespace-nowrap">
                <div className="font-medium text-zinc-100">{base.shift_hours} hours a day</div>
                <div className="text-[11px] text-zinc-500 mt-0.5">
                  {sundays(base.working_days)} · {base.working_days} working days
                </div>
                <div className="mt-1.5">
                  <Pill tone="violet">today&rsquo;s shift</Pill>
                </div>
              </td>
              <td className="p-3">
                <MadeCell made={base.made_l} />
              </td>
              <td className="p-3 text-zinc-500">—</td>
              <td className="p-3 tabular-nums text-zinc-100">{cr(base.value_rs)}</td>
              <td className="p-3 text-zinc-500">
                — <div className="text-[11px] mt-0.5">{fmt(base.line_hours_used)} machine hours used</div>
              </td>
              <td className="p-3 text-zinc-400 tabular-nums">
                {fullDays(base.days_storage_ge_95)} · {slowed(base.storage_throttle_events)}
              </td>
              <td className="p-3 text-zinc-400 max-w-[26ch]">
                This is how we run today. Every other page on this site describes this option.
              </td>
            </tr>
            {sc.map((s) => {
              const r = advice(s);
              return (
                <tr key={s.id}>
                  <td className="p-3 whitespace-nowrap">
                    <div className="font-medium text-zinc-100">{name(s)}</div>
                    <div className="text-[11px] text-zinc-500 mt-0.5">
                      {sundays(s.working_days)} · {s.working_days} working days
                    </div>
                    {r.tag && (
                      <div className="mt-1.5">
                        <Pill tone={r.tone}>{r.tag}</Pill>
                      </div>
                    )}
                  </td>
                  <td className="p-3">
                    <MadeCell made={s.made_l} />
                  </td>
                  <td className="p-3 tabular-nums">
                    <span className="text-emerald-300">+{fmt(s.delta_made_l)} L</span>
                    <div className="text-[11px] text-zinc-500 mt-0.5">+{money(s.value_rs - base.value_rs)}</div>
                  </td>
                  <td className="p-3 tabular-nums text-zinc-100">{cr(s.value_rs)}</td>
                  <td className="p-3">
                    <span
                      className={`tabular-nums font-medium ${
                        (s.pct_extra_hours_used ?? 0) >= 70
                          ? "text-emerald-300"
                          : (s.pct_extra_hours_used ?? 0) >= 40
                          ? "text-amber-300"
                          : "text-red-300"
                      }`}
                    >
                      {s.pct_extra_hours_used ?? "—"}%
                    </span>
                    <div className="text-[11px] text-zinc-500 mt-0.5 tabular-nums">
                      {fmt(s.extra_line_hours_used)} of {fmt(s.extra_line_hours_offered)} extra hours ran
                    </div>
                  </td>
                  <td className="p-3 text-zinc-400 tabular-nums whitespace-nowrap">
                    <span className={s.days_storage_ge_95 >= 10 ? "text-red-300" : ""}>
                      {fullDays(s.days_storage_ge_95)}
                    </span>{" "}
                    · {slowed(s.storage_throttle_events)}
                  </td>
                  <td className="p-3 text-zinc-400 max-w-[30ch]">{r.text}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-3 rounded-lg border border-sky-500/25 bg-sky-500/[0.06] px-4 py-2.5 text-sm text-zinc-200 leading-relaxed">
        In short: <span className="font-medium">{name(bestValue)}, {sundays(bestValue.working_days)}</span> is the
        best value — {bestValue.pct_extra_hours_used}% of its extra hours ran.{" "}
        <span className="font-medium">{name(best)}</span> makes the most,{" "}
        <span className="tabular-nums">{fmt(best.made_l)} L</span>, but the godown is {fullDays(best.days_storage_ge_95)}.
        {taperLine ? ` ${taperLine}` : ""}
      </div>
      <div className="mt-3 space-y-1 text-[11px] text-zinc-500">
        {wagesCaveat && (
          <div className="text-amber-300/80">
            Sunday wages are not counted in any option. &ldquo;Best value&rdquo; means hours that turned into litres,
            not money spent.
          </div>
        )}
        <div>
          Every option was run through the same computer plan for the full month. &ldquo;Of the extra hours, how many
          ran&rdquo; = extra machine hours the machines actually used ÷ extra machine hours the shift offered.
        </div>
      </div>
    </div>
  );
}
