import type { Scenario, ScenariosData } from "../lib/types";
import { fmt, cr, money } from "../lib/data";
import { Pill } from "./Card";

// The shift patterns, simulated end-to-end. Verdicts are computed from the
// scenario numbers themselves (max output, best conversion, dominated option) —
// nothing here is hand-typed, and the row count follows the data.
export default function ScenarioBoard({ data }: { data: ScenariosData }) {
  const base = data.baseline;
  // ascending by how many extra line-hours each pattern asks for — a price ladder
  const sc = [...data.scenarios].sort(
    (a, b) => a.extra_line_hours_offered - b.extra_line_hours_offered || a.shift_hours - b.shift_hours
  );
  const best = sc.reduce((a, b) => (b.made_l > a.made_l ? b : a));
  const cheapest = sc.reduce((a, b) =>
    (b.pct_extra_hours_used ?? -1) > (a.pct_extra_hours_used ?? -1) ? b : a
  );
  const maxMade = Math.max(base.made_l, ...sc.map((s) => s.made_l));
  const wagesCaveat = sc.some((s) => /wage/i.test(s.note));

  const read = (s: Scenario): { tone: string; tag: string; text: string } => {
    if (s.id === cheapest.id)
      return {
        tone: "green",
        tag: "cheapest lever",
        text: `${s.pct_extra_hours_used}% of the extra hours actually convert — the best rate on the board. ${s.note}.`,
      };
    if (s.id === best.id)
      return {
        tone: "amber",
        tag: "max output",
        text: `The biggest gain, +${fmt(s.delta_made_l)} L — but only ${s.pct_extra_hours_used}% of the offered hours convert; ${s.note}.`,
      };
    if (s.made_l < best.made_l && s.extra_line_hours_offered > best.extra_line_hours_offered)
      return {
        tone: "red",
        tag: "not worth it",
        text: `Offers ${fmt(s.extra_line_hours_offered - best.extra_line_hours_offered)} more line-hours than the ${
          best.pattern ?? `${best.shift_hours}h`
        } pattern yet makes ${fmt(best.made_l - s.made_l)} L LESS — ${s.note}.`,
      };
    return { tone: "zinc", tag: "", text: s.note };
  };

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
              <th className="p-3 font-medium">Pattern</th>
              <th className="p-3 font-medium">Made</th>
              <th className="p-3 font-medium">vs baseline</th>
              <th className="p-3 font-medium">Output value</th>
              <th className="p-3 font-medium">Extra hours → litres</th>
              <th className="p-3 font-medium">Storage pressure</th>
              <th className="p-3 font-medium">The read</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800 align-top">
            <tr>
              <td className="p-3 whitespace-nowrap">
                <div className="font-medium text-zinc-100">
                  {base.shift_hours}h × {base.working_days}d
                </div>
                <div className="text-[11px] text-zinc-500 mt-0.5">Sundays off</div>
                <div className="mt-1.5">
                  <Pill tone="violet">baseline</Pill>
                </div>
              </td>
              <td className="p-3">
                <MadeCell made={base.made_l} />
              </td>
              <td className="p-3 text-zinc-500">—</td>
              <td className="p-3 tabular-nums text-zinc-100">{cr(base.value_rs)}</td>
              <td className="p-3 text-zinc-500">
                — <div className="text-[11px] mt-0.5">{fmt(base.line_hours_used)} line-hours used</div>
              </td>
              <td className="p-3 text-zinc-400 tabular-nums">
                {base.days_storage_ge_95} d ≥95% · {base.storage_throttle_events} throttled
              </td>
              <td className="p-3 text-zinc-400 max-w-[26ch]">
                The plan of record — every other page on this site describes this pattern.
              </td>
            </tr>
            {sc.map((s) => {
              const r = read(s);
              return (
                <tr key={s.id}>
                  <td className="p-3 whitespace-nowrap">
                    <div className="font-medium text-zinc-100">
                      {s.pattern ?? `${s.shift_hours}h × ${s.working_days}d`}
                    </div>
                    <div className="text-[11px] text-zinc-500 mt-0.5">
                      Sundays on{s.taper ? ` · tapers after day ${s.taper.boundary_day}` : ""}
                    </div>
                    {(r.tag || s.taper) && (
                      <div className="mt-1.5">
                        <Pill tone={r.tag ? r.tone : "blue"}>{r.tag || "front-load, then taper"}</Pill>
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
                      {fmt(s.extra_line_hours_used)} of {fmt(s.extra_line_hours_offered)} extra h used
                    </div>
                  </td>
                  <td className="p-3 text-zinc-400 tabular-nums whitespace-nowrap">
                    <span className={s.days_storage_ge_95 >= 10 ? "text-red-300" : ""}>
                      {s.days_storage_ge_95} d ≥95%
                    </span>{" "}
                    · {s.storage_throttle_events} throttled
                  </td>
                  <td className="p-3 text-zinc-400 max-w-[30ch]">{r.text}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {data.takeaway && (
        <div className="mt-3 rounded-lg border border-sky-500/25 bg-sky-500/[0.06] px-4 py-2.5 text-sm text-zinc-200 leading-relaxed">
          {data.takeaway}
        </div>
      )}
      <div className="mt-3 space-y-1 text-[11px] text-zinc-500">
        {wagesCaveat && (
          <div className="text-amber-300/80">
            Sunday wages are not modelled in any of these patterns — &ldquo;cheapest&rdquo; is about hours converting to
            litres, not wage cost.
          </div>
        )}
        <div>{data.method_note}.</div>
        <div>{data.artifact_note}.</div>
      </div>
    </div>
  );
}
