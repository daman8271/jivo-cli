"use client";

// /assumptions — why the plan says what it says.
//
// Mark 4's centrepiece. Three different kinds of "fact" sit on this page and
// they are never allowed to look alike:
//
//   SETTLED       the plant ruled it. Not ours to change, and it carries who
//                 said it and when.
//   TAKEN ON TOP  nobody has ruled, so the computer filled it in — and each one
//                 says whether it is actually doing anything on THIS run.
//   THIS BUILD    the rulebook was silent and this build had to pick something.
//
// Then the speeds, which machine may take which pack, where the month's sheet
// disagrees with the recipe, and the questions still waiting on an answer.
//
// Not one figure on this page is typed. Every number, every sentence and every
// id is read out of plan/assumptions.json, so the day a ruling changes, this
// page changes with it and nobody deploys anything.

import Link from "next/link";
import { asAssumptions, useLive } from "../lib/live";
import { maskDigits, prefWords, speedBasis } from "../lib/labels";
import { dlabel, inr, litres, plural } from "../lib/fmt";
import { AsOf, Live, OwnStamp, SourceLine } from "./Freshness";
import { Panel, Pill, Section, Stat } from "./Card";
import SimBadge from "./SimBadge";
import type { OpenQuestion } from "../lib/types";

/** A speed, or a dash. Absent is never zero on this page either. */
const rate = (n: number | null | undefined) =>
  typeof n === "number" && Number.isFinite(n) ? `${inr(n)}/h` : "—";

/** Group the questions the way the file already groups them. */
function bySection(qs: OpenQuestion[]): [string, OpenQuestion[]][] {
  const out: [string, OpenQuestion[]][] = [];
  for (const q of qs) {
    const last = out[out.length - 1];
    if (last && last[0] === q.section) last[1].push(q);
    else out.push([q.section, [q]]);
  }
  return out;
}

export default function AssumptionsClient() {
  const live = useLive(["assumptions"]);
  const A = asAssumptions(live.assumptions);
  const rec = live.assumptions;

  const answered = (A?.open_questions ?? []).filter((q) => q.status !== "open").length;
  const inEffect = (A?.assumed ?? []).filter((a) => a.in_effect).length;
  const fresh = A?.freshness;
  const run = A?.this_run;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">What this plan takes as fact</h1>
        <SimBadge kind="plan" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {A?.meta?.note
          ? maskDigits(A.meta.note)
          : "What the plant has settled, what the computer filled in for itself, and what is still a question."}
      </p>

      <div className="mt-6">
        <Live rec={rec} what="the rulebook">
          {A && (
            <div className="space-y-2">
              {/* ── what this page is ─────────────────────────────── */}
              <Panel title="The rulebook this plan was built from" asOf={<AsOf rec={rec} />}>
                <div className="flex flex-wrap gap-x-8 gap-y-3">
                  <Stat k="Rulebook" v={A.meta?.rulebook_version ?? "—"} sub="the version the plan was built from" />
                  <Stat k="Written" v={A.meta?.rulebook_written ? dlabel(A.meta.rulebook_written) : "—"} />
                  <Stat k="Whose rules" v={A.meta?.rulebook_owner ?? "—"} />
                  <Stat
                    k="Settled"
                    v={`${A.settled.length} ${plural(A.settled.length, "ruling", "rulings")}`}
                    tone="text-emerald-300"
                  />
                  <Stat
                    k="Taken on top"
                    v={`${A.assumed.length}, ${inEffect} in effect`}
                    tone="text-amber-300"
                    sub="not ruled — the computer filled these in"
                  />
                  <Stat
                    k="Waiting on you"
                    v={`${A.open_questions.length - answered} of ${A.open_questions.length}`}
                    tone={A.open_questions.length - answered > 0 ? "text-violet-300" : "text-emerald-300"}
                    sub="questions still unanswered"
                  />
                </div>
                {A.meta?.rulebook_sources && (
                  <ul className="mt-3 space-y-0.5 border-t border-zinc-800 pt-2 text-xs text-zinc-500">
                    {Object.entries(A.meta.rulebook_sources).map(([k, v]) => (
                      <li key={k}>
                        <span className="text-zinc-400">{k.replace(/_/g, " ")}</span> — {maskDigits(v)}
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>

              {/* ── settled ───────────────────────────────────────── */}
              <Section
                title="Settled — the plant has ruled on these"
                right={<AsOf rec={rec} />}
                note="These are not ours to change. Each one says who said it."
              >
                <ul className="space-y-1.5">
                  {A.settled.map((r) => (
                    <li key={r.id} className="rounded-lg border border-emerald-500/15 bg-emerald-500/[0.03] p-3">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <Pill tone="green">{r.id}</Pill>
                        {/* the freeze computes a verdict on the rulings it can, exactly
                            as it does for the guesses below. It was being thrown away:
                            no settled ruling on this page ever said whether the run in
                            front of you kept it. */}
                        {r.in_effect === true && (
                          <Pill tone="green" title={r.in_effect_note ?? undefined}>
                            this run keeps it
                          </Pill>
                        )}
                        {r.in_effect === false && (
                          <Pill tone="red" title={r.in_effect_note ?? undefined}>
                            this run does NOT keep it
                          </Pill>
                        )}
                        <span className="text-sm text-zinc-200">{maskDigits(r.rule)}</span>
                      </div>
                      {r.in_effect != null && r.in_effect_note && (
                        <div className="mt-1 text-xs text-zinc-400">
                          <span className="text-zinc-500">On this run: </span>
                          {maskDigits(r.in_effect_note)}
                        </div>
                      )}
                      {r.source && <div className="mt-1 text-xs text-zinc-500">{maskDigits(r.source)}</div>}
                    </li>
                  ))}
                </ul>
              </Section>

              {/* ── assumed ───────────────────────────────────────── */}
              <Section
                title="Taken on top — nobody has ruled, so the computer filled it in"
                right={<AsOf rec={rec} />}
                note="Every one of these says what would replace it: one answer from you turns a guess into a ruling."
              >
                <ul className="space-y-1.5">
                  {A.assumed.map((a) => (
                    <li key={a.id} className="rounded-lg border border-amber-500/20 bg-amber-500/[0.03] p-3">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <Pill tone="amber">{a.id}</Pill>
                        {a.in_effect ? (
                          <Pill tone="green" title={a.in_effect_note ?? undefined}>
                            in effect
                          </Pill>
                        ) : (
                          <Pill tone="zinc" title={a.in_effect_note ?? undefined}>
                            not in effect this run
                          </Pill>
                        )}
                        <span className="text-sm text-zinc-200">{maskDigits(a.assumption)}</span>
                      </div>
                      {a.in_effect_note && (
                        <div className="mt-1 text-xs text-zinc-400">
                          <span className="text-zinc-500">{a.in_effect ? "How it shows up: " : "Why not: "}</span>
                          {maskDigits(a.in_effect_note)}
                        </div>
                      )}
                      {a.why && (
                        <div className="mt-1 text-xs text-zinc-400">
                          <span className="text-zinc-500">Why we think so: </span>
                          {maskDigits(a.why)}
                        </div>
                      )}
                      {a.changes_it && (
                        <div className="mt-1 text-xs text-violet-300/80">
                          <span className="text-zinc-500">What would change it: </span>
                          {maskDigits(a.changes_it)}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </Section>

              {/* ── build choices ─────────────────────────────────── */}
              <Section
                title="Choices this build made"
                right={<AsOf rec={rec} />}
                note="The rulebook did not say, so the code had to pick. Tell us to pick differently and it changes."
              >
                <ul className="space-y-1.5">
                  {A.build_choices.map((b) => (
                    <li key={b.id} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <Pill tone="blue">{b.id}</Pill>
                        <span className="text-sm text-zinc-200">{maskDigits(b.choice)}</span>
                      </div>
                      {b.why && <div className="mt-1 text-xs text-zinc-400">{maskDigits(b.why)}</div>}
                      {b.changes_it && (
                        <div className="mt-1 text-xs text-violet-300/80">
                          <span className="text-zinc-500">What would change it: </span>
                          {maskDigits(b.changes_it)}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </Section>

              {/* ── speeds ────────────────────────────────────────── */}
              <Section
                title="The speed the plan uses for every machine and pack"
                right={<AsOf rec={rec} />}
                note="Bottles an hour. A dash means nobody has that figure — it is not a zero."
              >
                <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
                  <table className="w-full min-w-[52rem] text-sm">
                    <thead>
                      <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                        <th className="p-2 font-normal">Machine</th>
                        <th className="p-2 font-normal">Pack</th>
                        <th className="p-2 text-right font-normal">Listed</th>
                        <th className="p-2 text-right font-normal">August typical</th>
                        <th className="p-2 text-right font-normal">August best</th>
                        <th className="p-2 text-right font-normal">Runs</th>
                        <th className="p-2 text-right font-normal">The plan uses</th>
                        <th className="p-2 font-normal">Where that comes from</th>
                      </tr>
                    </thead>
                    <tbody>
                      {A.speeds.map((s, i) => {
                        const b = speedBasis(s.basis_kind);
                        // a pack with NO rate is the row that most needs reading —
                        // it is a question for the plant, so it is never greyed
                        const needsRuling = (s.basis_kind ?? "") === "none";
                        return (
                          <tr
                            key={`${s.line}-${s.slot}-${i}`}
                            className={`border-t border-zinc-800/60 ${
                              needsRuling ? "bg-red-500/[0.04]" : s.used_by_the_plan ? "" : "text-zinc-500"
                            }`}
                          >
                            <td className="p-2">{s.line}</td>
                            <td className="p-2">
                              {s.slot}
                              {s.set_of_two && (
                                <Pill tone="zinc" title="this machine fills two at once">
                                  two at a time
                                </Pill>
                              )}
                            </td>
                            <td className="p-2 text-right tabular-nums">{rate(s.rated)}</td>
                            <td className="p-2 text-right tabular-nums">{rate(s.aug_median)}</td>
                            <td className="p-2 text-right tabular-nums">{rate(s.aug_best)}</td>
                            <td className="p-2 text-right tabular-nums">{s.aug_runs ?? "—"}</td>
                            <td className="p-2 text-right font-medium tabular-nums text-zinc-100">{rate(s.planning)}</td>
                            <td className="p-2">
                              <Pill tone={b.tone} title={s.basis ?? b.words}>
                                {b.label}
                              </Pill>
                              <span className="ml-2 text-xs text-zinc-500">{maskDigits(s.basis ?? b.words)}</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Section>

              {/* ── eligibility ───────────────────────────────────── */}
              <Section
                title="Which pack and which bottle may go on which machine"
                right={<AsOf rec={rec} />}
                note={A.preference_semantics ? maskDigits(A.preference_semantics) : undefined}
              >
                <div className="grid gap-2 md:grid-cols-2">
                  {A.eligibility.map((e, i) => (
                    <div key={`${e.line}-${e.slot}-${i}`} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className="text-sm font-medium text-zinc-200">{e.line}</span>
                        <span className="text-sm text-zinc-400">{e.slot}</span>
                        {e.has_a_speed === false && (
                          <Pill tone="red" title="this machine may take the pack, but nobody has given it a speed — the plan puts nothing here">
                            no speed yet
                          </Pill>
                        )}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {Object.entries(e.families)
                          .sort((a, b) => a[1] - b[1])
                          .map(([fam, pref]) => (
                            <Pill
                              key={fam}
                              tone={pref === 1 ? "green" : pref === 2 ? "amber" : "zinc"}
                              title={prefWords(pref)}
                            >
                              {fam} · {prefWords(pref)}
                            </Pill>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
                {A.excluded_lines && Object.keys(A.excluded_lines).length > 0 && (
                  <ul className="mt-3 space-y-0.5 text-xs text-zinc-500">
                    {Object.entries(A.excluded_lines).map(([k, v]) => (
                      <li key={k}>
                        <span className="text-zinc-400">{k} is left out of the plan</span> — {maskDigits(v)}
                      </li>
                    ))}
                  </ul>
                )}
              </Section>

              {/* ── the sheet vs the recipe ───────────────────────── */}
              {A.sheet_disagrees.length > 0 && (
                <Section
                  title="Where the month's sheet disagrees with the recipe"
                  right={<AsOf rec={rec} />}
                  note="The sheet calls these plastic; the recipe in the system says the container is a tin. The recipe wins, so they go on the tin machine — question 10 is asking you to confirm that."
                >
                  <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
                    <table className="w-full min-w-[36rem] text-sm">
                      <thead>
                        <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                          <th className="p-2 font-normal">Product</th>
                          <th className="p-2 font-normal">The sheet says</th>
                          <th className="p-2 font-normal">The recipe says</th>
                          <th className="p-2 font-normal">So the plan treats it as</th>
                        </tr>
                      </thead>
                      <tbody>
                        {A.sheet_disagrees.map((d) => (
                          <tr key={d.code} className="border-t border-zinc-800/60">
                            <td className="p-2">
                              <span className="mr-2 font-mono text-[11px] text-zinc-500">{d.code}</span>
                              {d.sku}
                            </td>
                            <td className="p-2 text-zinc-400">{d.sheet_pack_type ?? "—"}</td>
                            <td className="p-2 text-zinc-300">{d.container_name ?? "—"}</td>
                            <td className="p-2">
                              <Pill tone="amber">
                                {d.family ?? "—"} {d.slot ?? ""}
                              </Pill>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Section>
              )}

              {/* ── the questions ─────────────────────────────────── */}
              <Section
                title="Questions waiting for you"
                right={<AsOf rec={rec} />}
                note={
                  A.open_questions_convention
                    ? maskDigits(A.open_questions_convention)
                    : "Each answer turns a guess above into a ruling."
                }
              >
                <div className="space-y-4">
                  {bySection(A.open_questions).map(([section, qs]) => (
                    <div key={section}>
                      <h3 className="mb-1.5 text-xs uppercase tracking-wider text-zinc-500">{maskDigits(section)}</h3>
                      <ul className="space-y-1.5">
                        {qs.map((q) => {
                          const open = q.status === "open";
                          return (
                            <li
                              key={q.number}
                              className={`rounded-lg border p-3 ${
                                open ? "border-violet-500/20 bg-violet-500/[0.03]" : "border-emerald-500/20 bg-emerald-500/[0.03]"
                              }`}
                            >
                              <div className="flex flex-wrap items-baseline gap-2">
                                <span className="font-mono text-xs text-zinc-500">{q.number}</span>
                                <span className="text-sm font-medium text-zinc-200">{maskDigits(q.title)}</span>
                                <Pill tone={open ? "violet" : "green"}>{maskDigits(q.status)}</Pill>
                              </div>
                              {q.question && (
                                <details className="mt-2">
                                  <summary className="cursor-pointer text-xs text-zinc-500">
                                    what we asked
                                  </summary>
                                  <pre className="mt-1.5 overflow-x-auto whitespace-pre-wrap break-words font-sans text-xs leading-relaxed text-zinc-400">
                                    {maskDigits(q.question)}
                                  </pre>
                                </details>
                              )}
                              {q.answer && (
                                <div className="mt-1.5 text-xs text-emerald-300/90">
                                  <span className="text-zinc-500">Your answer: </span>
                                  {maskDigits(q.answer)}
                                </div>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))}
                </div>
                {A.open_questions_source && (
                  <p className="mt-3 text-xs text-zinc-500">Read from {maskDigits(A.open_questions_source)}.</p>
                )}
              </Section>

              {/* ── what THIS run had to guess ────────────────────── */}
              {run && (
                <Section title="What this particular run had to guess" right={<AsOf rec={rec} />}>
                  <div className="grid gap-2 md:grid-cols-2">
                    <Panel title="The guesses behind today's plan" asOf={<AsOf rec={rec} />}>
                      {run.assumed && run.assumed.length > 0 ? (
                        <ul className="max-h-72 space-y-1.5 overflow-y-auto pr-2 text-xs">
                          {run.assumed.map((a, i) => (
                            <li key={`${i}-${a.slice(0, 24)}`} className="flex items-start gap-2">
                              <Pill tone="amber">guess</Pill>
                              <span className="text-zinc-400">{maskDigits(a)}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-zinc-500">Nothing had to be guessed on this run.</p>
                      )}
                    </Panel>
                    <Panel title="What the rulebook actually did today" asOf={<AsOf rec={rec} />}>
                      <div className="flex flex-wrap gap-x-8 gap-y-3">
                        {run.prefs_used && (
                          <Stat
                            k="Runs on a first-choice machine"
                            v={`${run.prefs_used["1"] ?? 0} of ${Object.values(run.prefs_used).reduce((a, b) => a + b, 0)}`}
                            sub="the rest moved because the first choice was full"
                          />
                        )}
                        {run.product_changes != null && (
                          <Stat k="Product changes" v={inr(run.product_changes)} sub="across all machines, all month" />
                        )}
                        {run.second_change_allowed != null && (
                          <Stat k="A second change in one day" v={inr(run.second_change_allowed)} />
                        )}
                        {/* A SESSION OPENED IS NOT A NIGHT'S WORK. This tile used to
                            read "Second sessions: 22", which a plant manager reads as
                            22 crews to roster — against ten and a half hours of actual
                            night work in the whole month. Hours lead now; the roster
                            count sits under them. */}
                        {run.night_hours_used != null && (
                          <Stat
                            k="Night work in the rest of the month"
                            v={`${run.night_hours_used} h`}
                            tone={run.night_hours_used > 0 ? undefined : "text-zinc-400"}
                            sub={
                              run.night_sessions_worked != null
                                ? `on ${inr(run.night_sessions_worked)} ${plural(run.night_sessions_worked, "night", "nights")}${
                                    run.night_sessions != null
                                      ? ` — ${inr(run.night_sessions)} second ${plural(run.night_sessions, "session", "sessions")} opened in all`
                                      : ""
                                  }`
                                : "one machine a day, at most"
                            }
                          />
                        )}
                        {run.night_litres != null && run.night_litres > 0 && (
                          <Stat k="Filled at night" v={litres(run.night_litres)} sub="everything the second sessions made" />
                        )}
                      </div>
                      {run.product_changes_by_line && (
                        <ul className="mt-3 space-y-0.5 border-t border-zinc-800 pt-2 text-xs text-zinc-400">
                          {Object.entries(run.product_changes_by_line).map(([line, n]) => (
                            <li key={line} className="flex justify-between gap-3">
                              <span>{line}</span>
                              <span className="tabular-nums text-zinc-500">
                                {inr(n)} {plural(n, "change", "changes")}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                      {run.filled_by_hand && run.filled_by_hand.length > 0 && (
                        <p className="mt-3 text-xs text-zinc-500">
                          {A.drums?.display ? `${maskDigits(A.drums.display)}: ` : ""}
                          {run.filled_by_hand.join(", ")}.
                        </p>
                      )}
                    </Panel>
                  </div>
                  {run.warnings && run.warnings.length > 0 && (
                    <details className="mt-2 rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
                      <summary className="cursor-pointer text-sm text-zinc-400">
                        Things to know before quoting a number from this run ({run.warnings.length})
                      </summary>
                      <ul className="mt-2 space-y-1.5 text-xs text-zinc-400">
                        {run.warnings.map((w, i) => (
                          <li key={i}>{maskDigits(w)}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                </Section>
              )}

              {/* ── where a figure came from when the first choice failed ── */}
              {A.fallbacks && (
                <Section title="When the first source was missing" right={<AsOf rec={rec} />}>
                  <div className="grid gap-2 md:grid-cols-3">
                    <Panel title="Orders nobody has placed yet" asOf={<AsOf rec={rec} />}>
                      <div className="text-sm text-zinc-300">
                        {A.fallbacks.expected_orders?.used
                          ? "Worked out from what the trade really bought."
                          : "Not used on this run."}
                      </div>
                      {A.fallbacks.expected_orders?.reason && (
                        <p className="mt-1 text-xs text-amber-300/80">{maskDigits(A.fallbacks.expected_orders.reason)}</p>
                      )}
                      {A.fallbacks.expected_orders?.instead && (
                        <p className="mt-1 text-xs text-zinc-500">
                          Otherwise: {maskDigits(A.fallbacks.expected_orders.instead)}
                        </p>
                      )}
                    </Panel>
                    <Panel
                      title="How long a bill waits for a truck"
                      asOf={
                        <OwnStamp
                          iso={A.fallbacks.lag?.measured_on}
                          what="measured"
                          fallback={<AsOf rec={rec} />}
                        />
                      }
                    >
                      <div className="text-sm text-zinc-300">
                        {A.fallbacks.lag?.measured_daily ? "Measured again every day." : "One measurement, carried."}
                      </div>
                      {A.fallbacks.lag?.source && (
                        <p className="mt-1 text-xs text-zinc-500">{maskDigits(A.fallbacks.lag.source)}</p>
                      )}
                    </Panel>
                    <Panel title="Which machine gets tonight" asOf={<AsOf rec={rec} />}>
                      <div className="text-sm text-zinc-300">{A.fallbacks.night_line?.line ?? "none picked"}</div>
                      {A.fallbacks.night_line?.reason && (
                        <p className="mt-1 text-xs text-zinc-400">{maskDigits(A.fallbacks.night_line.reason)}</p>
                      )}
                      {A.fallbacks.night_line?.instead && (
                        <p className="mt-1 text-xs text-zinc-500">
                          Otherwise: {maskDigits(A.fallbacks.night_line.instead)}
                        </p>
                      )}
                    </Panel>
                  </div>
                </Section>
              )}

              {/* ── how old each input is ─────────────────────────── */}
              {fresh && (
                <Section
                  title="How old each of these is"
                  right={<AsOf rec={rec} />}
                  note="Nothing on this page is live. Each line says when it was last read, so a stale input is never quoted as a fresh one."
                >
                  <div className="grid gap-2 md:grid-cols-2">
                    <Panel title="The rulebook and your questions" asOf={<AsOf rec={rec} />}>
                      <div className="space-y-1.5 text-xs text-zinc-400">
                        <div className="flex flex-wrap items-baseline justify-between gap-2">
                          <span>Rulebook written</span>
                          <OwnStamp iso={fresh.rulebook_written} what="written" />
                        </div>
                        <div className="flex flex-wrap items-baseline justify-between gap-2">
                          <span>Your answers file, last read</span>
                          <OwnStamp iso={fresh.questions_file_read_at} what="read" staleAfterHours={30} />
                        </div>
                        {fresh.questions_file && (
                          <div className="text-zinc-500">{maskDigits(fresh.questions_file)}</div>
                        )}
                        <div className="flex flex-wrap items-baseline justify-between gap-2">
                          <span>The plant, as the loop last saw it</span>
                          <SourceLine src="factory_production" />
                        </div>
                        {fresh.history_through && (
                          <div className="flex flex-wrap items-baseline justify-between gap-2">
                            <span>Days already gone, counted through</span>
                            <OwnStamp iso={fresh.history_through} what="through" />
                          </div>
                        )}
                      </div>
                    </Panel>
                    <Panel title="The two files read once a day" asOf={<AsOf rec={rec} />}>
                      <div className="space-y-2 text-xs text-zinc-400">
                        <div>
                          <div className="flex flex-wrap items-baseline justify-between gap-2">
                            <span className="text-zinc-300">What the trade really bought</span>
                            <OwnStamp
                              iso={fresh.expected_orders_file?.fetched_at}
                              what="read"
                              staleAfterHours={30}
                              fallback={<span className="text-amber-300 text-[11px]">never read</span>}
                            />
                          </div>
                          {fresh.expected_orders_file?.window && (
                            <div className="text-zinc-500">
                              Over {dlabel(fresh.expected_orders_file.window.from)} to{" "}
                              {dlabel(fresh.expected_orders_file.window.to)}
                              {fresh.expected_orders_file.window.months
                                ? ` — ${inr(fresh.expected_orders_file.window.months)} ${plural(
                                    fresh.expected_orders_file.window.months, "month", "months",
                                  )}`
                                : ""}
                            </div>
                          )}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-baseline justify-between gap-2">
                            <span className="text-zinc-300">How long a bill waits for a truck</span>
                            <OwnStamp
                              iso={fresh.lag_file?.measured_on}
                              what="measured"
                              staleAfterHours={fresh.lag_file?.measured_once ? undefined : 30}
                            />
                          </div>
                          <div className="text-zinc-500">
                            {fresh.lag_file?.measured_once
                              ? "Measured once and carried — not re-measured."
                              : "Measured again every day off the gate log."}
                            {fresh.lag_file?.window ? ` Over ${maskDigits(fresh.lag_file.window)}.` : ""}
                            {fresh.lag_file?.rows != null
                              ? ` ${inr(fresh.lag_file.rows)} ${plural(fresh.lag_file.rows, "bill", "bills")} behind it.`
                              : ""}
                          </div>
                        </div>
                      </div>
                    </Panel>
                  </div>
                </Section>
              )}

              {/* ── the checks this run had to pass ───────────────── */}
              <Section
                title="The checks this plan had to pass before you saw it"
                right={<AsOf rec={rec} />}
                note={A.acceptance_note ? maskDigits(A.acceptance_note) : undefined}
              >
                <ul className="space-y-1">
                  {A.acceptance.map((c) => (
                    <li
                      key={c.id}
                      className="flex flex-wrap items-baseline gap-2 rounded-lg border border-zinc-800 bg-zinc-900/40 p-2.5 text-sm"
                    >
                      {c.passed === true ? (
                        <Pill tone="green">passed</Pill>
                      ) : c.passed === false ? (
                        <Pill tone="red">failed</Pill>
                      ) : c.checked_here_in_part ? (
                        <Pill tone="amber" title={c.verdict_by}>
                          {c.passed_here ? "the part checked here passed" : "part checked here"}
                        </Pill>
                      ) : (
                        <Pill tone="zinc" title="checked outside this file — by the site's own build, or by running the whole chain">
                          checked elsewhere
                        </Pill>
                      )}
                      <span className="text-zinc-300">{maskDigits(c.text)}</span>
                      {c.checks ? (
                        <span className="ml-auto text-xs tabular-nums text-zinc-500">
                          {inr(c.checks)} {plural(c.checks, "check", "checks")}
                        </span>
                      ) : null}
                      {/* one acceptance line is several checks in one sentence, and they
                          do not all belong to the same thing. AC10 was publishing one
                          green tick over four clauses, two of which this file never
                          sees. Each clause says who really checks it. */}
                      {c.checked_here_in_part && c.clauses && (
                        <ul className="mt-1 w-full space-y-0.5 border-t border-zinc-800 pt-1 text-xs">
                          {c.clauses.map((q, qi) => (
                            <li key={qi} className="flex flex-wrap items-baseline gap-2">
                              <span className={q.checked_here ? "text-emerald-300" : "text-zinc-400"}>
                                {maskDigits(q.clause)}
                              </span>
                              <span className="ml-auto text-zinc-500">{maskDigits(q.verdict_by)}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ul>
              </Section>

              <p className="mt-6 text-xs text-zinc-500">
                Every id, sentence and figure on this page is read out of the plan itself, every few minutes. Change a
                ruling and this page changes with it.{" "}
                <Link href="/lines" className="underline underline-offset-2 hover:text-zinc-300">
                  the speeds on the machines page
                </Link>{" "}
                ·{" "}
                <Link href="/" className="underline underline-offset-2 hover:text-zinc-300">
                  back to the plant
                </Link>
                .
              </p>
            </div>
          )}
        </Live>
      </div>
    </div>
  );
}
