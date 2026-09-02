import Link from "next/link";
import { notFound } from "next/navigation";
import { getDay, getSummary, getThreads, fmt } from "@/lib/data";
import { LINES } from "@/lib/types";
import type { Day, Blocked, Run } from "@/lib/types";
import { Card, Section, Pill } from "@/components/Card";
import { DayStat, DayStrip, DayScroll, DayEmpty, DayBar, rs, TH, THR, TD, NUM } from "@/components/DayBits";

export const dynamicParams = false;
export function generateStaticParams() {
  return Array.from({ length: 31 }, (_, i) => ({ n: String(i + 1) }));
}

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
function dateLabel(iso: string) {
  const [, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[m - 1]}`;
}

export async function generateMetadata({ params }: { params: Promise<{ n: string }> }) {
  const n = Number((await params).n);
  if (!Number.isInteger(n) || n < 1 || n > 31) return { title: "Day" };
  const d = getDay(n);
  return { title: `Day ${n} — ${d.weekday} ${dateLabel(d.date)} · JIVO Mark 1` };
}

type MovedUp = { code: string; sku: string; head: string; lines: string[]; po: boolean; litres: number; value: number };

export default async function DayPage({ params }: { params: Promise<{ n: string }> }) {
  const n = Number((await params).n);
  if (!Number.isInteger(n) || n < 1 || n > 31) notFound();

  const day: Day = getDay(n);
  const prev: Day | null = n > 1 ? getDay(n - 1) : null;

  // The lines only move on working days, so compare against the last day they actually ran.
  let ref: Day | null = null;
  let refN = 0;
  for (let i = n - 1; i >= 1; i--) {
    const d = getDay(i);
    if (d.working) { ref = d; refN = i; break; }
  }

  const summary = getSummary();
  const threads = getThreads();

  // --- what changed on the lines -------------------------------------------------
  const todayByCode = new Map<string, MovedUp>();
  for (const r of day.runs) {
    const e = todayByCode.get(r.code);
    if (e) { if (!e.lines.includes(r.line)) e.lines.push(r.line); e.po = e.po || r.po_backed; e.litres += r.litres; e.value += r.value; }
    else todayByCode.set(r.code, { code: r.code, sku: r.sku, head: r.head, lines: [r.line], po: r.po_backed, litres: r.litres, value: r.value });
  }
  const refCodes = new Set((ref?.runs ?? []).map((r) => r.code));
  const movedUp = [...todayByCode.values()].filter((e) => !refCodes.has(e.code)).sort((a, b) => b.litres - a.litres);
  const droppedMap = new Map<string, Run>();
  for (const r of ref?.runs ?? []) if (!todayByCode.has(r.code) && !droppedMap.has(r.code)) droppedMap.set(r.code, r);
  const dropped = [...droppedMap.values()];

  const orderPieces = day.new_orders.reduce((a, o) => a + o.pieces, 0);
  const orderValue = day.new_orders.reduce((a, o) => a + o.value, 0);

  // --- what ran ------------------------------------------------------------------
  const byLine = LINES.map((line) => ({ line, hours: day.line_hours[line] ?? 0, runs: day.runs.filter((r) => r.line === line) }));
  const linesRunning = byLine.filter((l) => l.runs.length > 0).length;
  const flushMin = day.runs.reduce((a, r) => a + r.flush_min, 0);

  // --- what didn't: the same block is reported once per attempt, so fold it -------
  const blockedMap = new Map<string, Blocked & { times: number }>();
  for (const b of day.blocked) {
    const k = `${b.code}|${b.binder}`;
    const e = blockedMap.get(k);
    if (e) e.times += 1; else blockedMap.set(k, { ...b, times: 1 });
  }
  const blocked = [...blockedMap.values()].sort((a, b) => b.want - a.want);
  const wantByCode = new Map<string, number>();
  for (const b of blocked) wantByCode.set(b.code, Math.max(wantByCode.get(b.code) ?? 0, b.want));
  const blockedProducts = wantByCode.size;
  const blockedPieces = [...wantByCode.values()].reduce((a, v) => a + v, 0);

  const dispatched = [...day.dispatched].sort((a, b) => b.litres - a.litres);
  const bought = [...day.bought].sort((a, b) => b.qty - a.qty);
  const received = [...day.received].sort((a, b) => b.qty - a.qty);

  const talks = threads
    .map((t) => ({ t, msgs: t.messages.filter((m) => m.day === day.date) }))
    .filter((x) => x.msgs.length > 0);
  const msgCount = talks.reduce((a, x) => a + x.msgs.length, 0);

  const s = day.storage;
  const full = s.pct >= 95;
  const cap = day.decisions.find((d) => typeof d.headroom_l === "number")?.headroom_l;

  return (
    <div>
      {/* ---------------------------------------------------------------- header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-tight">
              Day {n} <span className="text-zinc-500">—</span> {day.weekday} {dateLabel(day.date)}
            </h1>
            {day.working ? <Pill tone="green">Working day</Pill> : <Pill>{day.weekday} — plant closed</Pill>}
            {full ? <Pill tone="red">Godown full</Pill> : null}
            {day.working && day.made_litres === 0 ? <Pill tone="red">Nothing made</Pill> : null}
          </div>
          <div className="mt-1 text-sm text-zinc-500">{day.date}</div>
        </div>
        <div className="flex items-center gap-2 text-sm">
          {n > 1 ? (
            <Link href={`/day/${n - 1}`} className="rounded-md border border-zinc-800 px-3 py-1.5 text-zinc-300 hover:bg-zinc-800">← Day {n - 1}</Link>
          ) : (
            <span className="rounded-md border border-zinc-900 px-3 py-1.5 text-zinc-700">← month starts</span>
          )}
          {n < 31 ? (
            <Link href={`/day/${n + 1}`} className="rounded-md border border-zinc-800 px-3 py-1.5 text-zinc-300 hover:bg-zinc-800">Day {n + 1} →</Link>
          ) : (
            <span className="rounded-md border border-zinc-900 px-3 py-1.5 text-zinc-700">month ends →</span>
          )}
        </div>
      </div>

      <div className="mt-4">
        <DayStrip current={n} days={summary.days} />
        <div className="mt-2 text-xs text-zinc-600">Every day of August. The dim squares are Sundays — the plant is closed.</div>
      </div>

      {/* ------------------------------------------------------------- six numbers */}
      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <DayStat label="Made" value={fmt(day.made_litres)} unit="L" sub={day.working ? `${day.runs.length} runs on ${linesRunning} of 6 lines` : "plant closed"} />
        <DayStat label="Worth" value={rs(day.made_value)} sub="value of what was filled" />
        <DayStat label="Shipped" value={fmt(day.shipped_litres)} unit="L" sub={`${day.dispatched.length} dispatch lines`} />
        <DayStat label="Line use" value={`${day.line_util}`} unit="%" sub={`${day.flushes} flushes · ${flushMin} min`} />
        <DayStat label="Storage" value={`${s.pct}`} unit="%" tone={full ? "text-red-400" : ""} sub={`${fmt(s.physical_l)} of ${fmt(s.ceiling_l)} L`} />
        <DayStat label="Room left" value={fmt(s.headroom_l)} unit="L" tone={full ? "text-red-400" : ""} sub="before the godown is full" />
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Card title="Plan still to make" value={`${fmt(day.book.plan_left_l)} L`} sub="left in the August plan, this morning" />
        <Card title="Purchase orders open" value={`${fmt(day.book.po_open_l)} L`} sub="on order, not landed yet" />
        <Card title="Money in those POs" value={rs(day.book.po_open_value)} sub="committed to suppliers" />
      </div>

      {/* -------------------------------------------------- what changed since yesterday */}
      <Section
        title="What changed since yesterday"
        right={
          <span className="text-xs text-zinc-500">
            {ref ? `lines compared with day ${refN} — ${ref.weekday} ${dateLabel(ref.date)}` : "first day of the month, nothing before it"}
          </span>
        }
      >
        {prev && ref && refN !== n - 1 ? (
          <div className="mb-3 text-xs text-zinc-500">
            {prev.weekday} {dateLabel(prev.date)} was a closed day, so the comparison jumps back to the last day the lines ran.
          </div>
        ) : null}

        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <div className="mb-2 flex items-baseline justify-between">
              <div className="text-sm font-medium text-zinc-300">Orders that landed today</div>
              <div className="text-xs text-zinc-500">{day.new_orders.length} lines · {fmt(orderPieces)} pcs · {rs(orderValue)}</div>
            </div>
            {day.new_orders.length === 0 ? (
              <DayEmpty>No new orders on this date.</DayEmpty>
            ) : (
              <DayScroll max="max-h-[26rem]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Customer</th>
                      <th className={TH}>Where</th>
                      <th className={TH}>What</th>
                      <th className={THR}>Pieces</th>
                      <th className={THR}>Worth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {day.new_orders.map((o, i) => (
                      <tr key={`${o.docnum}-${o.code}-${i}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-300`}>{o.customer}</td>
                        <td className={TD}><Pill tone={o.channel === "MART" ? "blue" : "zinc"}>{o.channel}</Pill></td>
                        <td className={`${TD} text-zinc-400`}>{o.sku}</td>
                        <td className={`${TD} ${NUM}`}>{fmt(o.pieces)}</td>
                        <td className={`${TD} ${NUM} text-zinc-300`}>{rs(o.value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DayScroll>
            )}
          </div>

          <div>
            <div className="mb-2 text-sm font-medium text-zinc-300">What the plan moved on the lines</div>
            {!day.working ? (
              <DayEmpty>Plant closed — the lines did not move today.</DayEmpty>
            ) : movedUp.length === 0 && dropped.length === 0 ? (
              <DayEmpty>Same products as the last working day.</DayEmpty>
            ) : (
              <div className="space-y-3">
                {movedUp.length > 0 ? (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
                    <div className="mb-2 text-xs uppercase tracking-wider text-zinc-500">{ref ? "New on the lines today" : "On the lines today"}</div>
                    <ul className="space-y-1.5">
                      {movedUp.map((e) => (
                        <li key={e.code} className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
                          <span className="text-zinc-200">{e.sku}</span>
                          <span className="text-xs text-zinc-500">{e.lines.join(", ")}</span>
                          <span className="text-xs tabular-nums text-zinc-500">{fmt(e.litres)} L · {rs(e.value)}</span>
                          {e.po ? <Pill tone="amber">↑ moved up — PO backed</Pill> : null}
                          {e.head === "PREMIUM" ? <Pill tone="amber">PREMIUM</Pill> : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {dropped.length > 0 ? (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/20 p-3">
                    <div className="mb-2 text-xs uppercase tracking-wider text-zinc-500">Ran on day {refN}, not today</div>
                    <ul className="space-y-1 text-sm text-zinc-500">
                      {dropped.map((r) => <li key={r.code}>{r.sku}</li>)}
                    </ul>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------------------ what ran */}
      <Section
        title="What ran"
        right={<span className="text-xs text-zinc-500">{day.runs.length} runs · {fmt(day.made_litres)} L · {rs(day.made_value)} · {flushMin} min of flushing</span>}
      >
        {day.working && day.runs.length === 0 ? (
          <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
            Nothing was filled today.{typeof cap === "number" ? ` The day was capped at ${fmt(cap)} L of new stock — see the storage call below.` : ""}
          </div>
        ) : null}
        <div className="space-y-3">
          {byLine.map((l) => (
            <div key={l.line} className="rounded-xl border border-zinc-800 bg-zinc-900/40">
              <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-zinc-800 px-3 py-2">
                <div className="font-medium">{l.line}</div>
                <div className="text-xs tabular-nums text-zinc-500">
                  {l.runs.length === 0 ? "idle" : `${l.runs.length} run${l.runs.length > 1 ? "s" : ""} · ${l.hours} h · ${fmt(l.runs.reduce((a, r) => a + r.litres, 0))} L`}
                </div>
              </div>
              {l.runs.length === 0 ? (
                <div className="px-3 py-3 text-sm text-zinc-600">idle — nothing was filled on this line today</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr>
                        <th className={`${TH} w-8`}>#</th>
                        <th className={TH}>What was filled</th>
                        <th className={THR}>Pieces</th>
                        <th className={THR}>Litres</th>
                        <th className={THR}>Hours</th>
                        <th className={THR}>Flush</th>
                        <th className={THR}>Per hour</th>
                        <th className={TH}>Tags</th>
                      </tr>
                    </thead>
                    <tbody>
                      {l.runs.map((r, i) => (
                        <tr key={`${r.code}-${i}`} className="hover:bg-zinc-900/60">
                          <td className={`${TD} text-zinc-600 tabular-nums`}>{i + 1}</td>
                          <td className={`${TD} text-zinc-200`}>{r.sku}<span className="ml-2 text-xs text-zinc-600">{r.code}</span></td>
                          <td className={`${TD} ${NUM}`}>{fmt(r.pieces)}</td>
                          <td className={`${TD} ${NUM}`}>{fmt(r.litres)} L</td>
                          <td className={`${TD} ${NUM} text-zinc-400`}>{r.hours.toFixed(2)}</td>
                          <td className={`${TD} ${NUM} text-zinc-400`}>{r.flush_min > 0 ? `${r.flush_min} min` : "—"}</td>
                          <td className={`${TD} ${NUM} text-zinc-300`}>{rs(r.rs_per_hour)}</td>
                          <td className={TD}>
                            <span className="flex flex-wrap gap-1">
                              {r.head === "PREMIUM" ? <Pill tone="amber">PREMIUM</Pill> : <Pill>COMMODITY</Pill>}
                              {r.po_backed ? <Pill tone="green">PO backed</Pill> : null}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* --------------------------------------------------------------- what didn't */}
      <Section
        title="What did not run"
        right={<span className="text-xs text-zinc-500">{blockedProducts} products held · {fmt(blockedPieces)} pcs wanted</span>}
      >
        {blocked.length === 0 ? (
          <DayEmpty>{day.working ? "No product was recorded as held back today." : "Plant closed — nothing was scheduled."}</DayEmpty>
        ) : (
          <DayScroll max="max-h-[28rem]">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className={TH}>Product we could not fill</th>
                  <th className={THR}>Pieces wanted</th>
                  <th className={TH}>Held up by</th>
                  <th className={THR}>Times blocked</th>
                </tr>
              </thead>
              <tbody>
                {blocked.map((b) => (
                  <tr key={`${b.code}-${b.binder}`} className="hover:bg-zinc-900/60">
                    <td className={`${TD} text-zinc-200`}>{b.sku}<span className="ml-2 text-xs text-zinc-600">{b.code}</span></td>
                    <td className={`${TD} ${NUM}`}>{fmt(b.want)}</td>
                    <td className={TD}>
                      <span className="text-zinc-300">{b.binder_name}</span>
                      <span className="ml-2 text-xs text-zinc-600">{b.binder}</span>
                      <span className="ml-2"><Pill tone={b.binder.startsWith("RM") ? "red" : "zinc"}>{b.binder.startsWith("RM") ? "oil" : "packaging"}</Pill></span>
                    </td>
                    <td className={`${TD} ${NUM} text-zinc-500`}>{b.times}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </DayScroll>
        )}
        {blocked.length > 0 ? (
          <div className="mt-2 text-xs text-zinc-500">One item short holds the whole product. Each row names the item that held it back, and how many times the plan hit that wall today.</div>
        ) : null}
      </Section>

      {/* -------------------------------------------------------------- dispatched */}
      <Section
        title="What went out"
        right={<span className="text-xs text-zinc-500">{dispatched.length} lines · {fmt(day.shipped_litres)} L</span>}
      >
        {dispatched.length === 0 ? (
          <DayEmpty>Nothing was dispatched on this date.</DayEmpty>
        ) : (
          <DayScroll max="max-h-[26rem]">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className={TH}>Customer</th>
                  <th className={TH}>Where</th>
                  <th className={TH}>What</th>
                  <th className={THR}>Pieces</th>
                  <th className={THR}>Litres</th>
                </tr>
              </thead>
              <tbody>
                {dispatched.map((d, i) => (
                  <tr key={`${d.docnum}-${d.sku}-${i}`} className="hover:bg-zinc-900/60">
                    <td className={`${TD} text-zinc-300`}>{d.customer}</td>
                    <td className={TD}><Pill tone={d.channel === "MART" ? "blue" : "zinc"}>{d.channel}</Pill></td>
                    <td className={`${TD} text-zinc-400`}>{d.sku}</td>
                    <td className={`${TD} ${NUM}`}>{fmt(d.pieces)}</td>
                    <td className={`${TD} ${NUM} text-zinc-200`}>{fmt(d.litres)} L</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </DayScroll>
        )}
      </Section>

      {/* ------------------------------------------------------------------ storage */}
      <Section title="Storage" right={<span className="text-xs text-zinc-500">roof is {fmt(s.ceiling_l)} L of finished goods</span>}>
        <DayBar s={s} />
        <div className="mt-3 grid gap-3 lg:grid-cols-3">
          <Card title="Loose oil on hand" value={`${fmt(day.oil_on_hand_l)} L`} sub="bulk oil, not counted against the godown roof above" />
          <div className="lg:col-span-2">
            {day.decisions.length === 0 ? (
              <DayEmpty>No storage call recorded on this date.</DayEmpty>
            ) : (
              <div className="space-y-2">
                {day.decisions.map((d, i) => (
                  <div key={`${d.kind}-${i}`} className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone="amber">{d.kind.replace(/_/g, " ").toLowerCase()}</Pill>
                      {typeof d.headroom_l === "number" ? (
                        <span className="text-xs text-amber-200/70">room left when the call was made: {fmt(d.headroom_l)} L</span>
                      ) : null}
                    </div>
                    <div className="mt-1.5 text-sm text-amber-100">{d.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* ------------------------------------------------------- ordered and arrived */}
      <Section title="Materials" right={<span className="text-xs text-zinc-500">{bought.length} items ordered · {received.length} arrived</span>}>
        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <div className="mb-2 text-sm font-medium text-zinc-300">Ordered today</div>
            {bought.length === 0 ? (
              <DayEmpty>Nothing was ordered on this date.</DayEmpty>
            ) : (
              <DayScroll max="max-h-[24rem]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Item</th>
                      <th className={THR}>Quantity</th>
                      <th className={TH}>Lands on</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bought.map((b, i) => (
                      <tr key={`${b.code}-${i}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-300`}>{b.name}<span className="ml-2 text-xs text-zinc-600">{b.code}</span></td>
                        <td className={`${TD} ${NUM}`}>{fmt(b.qty)} <span className="text-zinc-500">{b.uom}</span></td>
                        <td className={`${TD} text-zinc-400 whitespace-nowrap`}>{dateLabel(b.lands)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DayScroll>
            )}
          </div>
          <div>
            <div className="mb-2 text-sm font-medium text-zinc-300">Arrived at the gate today</div>
            {received.length === 0 ? (
              <DayEmpty>Nothing came in on this date.</DayEmpty>
            ) : (
              <DayScroll max="max-h-[24rem]">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className={TH}>Item</th>
                      <th className={THR}>Quantity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {received.map((r, i) => (
                      <tr key={`${r.code}-${i}`} className="hover:bg-zinc-900/60">
                        <td className={`${TD} text-zinc-300`}>
                          {r.name === r.code ? <span className="text-zinc-500">{r.code}</span> : <>{r.name}<span className="ml-2 text-xs text-zinc-600">{r.code}</span></>}
                        </td>
                        <td className={`${TD} ${NUM}`}>{fmt(r.qty)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DayScroll>
            )}
          </div>
        </div>
      </Section>

      {/* ----------------------------------------------------------------- messages */}
      <Section
        title="Messages today"
        right={<Link href="/whatsapp" className="text-xs text-amber-400 hover:underline">all of August on WhatsApp →</Link>}
      >
        {talks.length === 0 ? (
          <DayEmpty>No messages went out or came in on this date.</DayEmpty>
        ) : (
          <>
            <div className="mb-2 text-xs text-zinc-500">{msgCount} messages with {talks.length} {talks.length === 1 ? "person" : "people"}</div>
            <div className="space-y-3">
              {talks.map(({ t, msgs }) => (
                <div key={t.whatsapp} className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-zinc-800 pb-2">
                    <span className="font-medium">{t.name}</span>
                    <span className="text-xs text-zinc-500">{t.title}</span>
                    <span className="ml-auto text-xs tabular-nums text-zinc-500">{t.display}</span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {msgs.map((m, i) => (
                      <div key={i} className={`rounded-lg border-l-2 px-3 py-2 text-sm ${m.dir === "out" ? "border-amber-500/60 bg-amber-500/5" : "border-zinc-700 bg-zinc-800/40"}`}>
                        <div className="mb-1 flex items-center gap-2">
                          <span className="text-[11px] uppercase tracking-wider text-zinc-500">{m.dir === "out" ? "we would have sent" : `assumed reply from ${t.name.split(" ")[0]}`}</span>
                          <Pill>{m.tag}</Pill>
                        </div>
                        <div className="whitespace-pre-line text-zinc-200">{m.text}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </Section>

      {/* ------------------------------------------------------------------ honesty */}
      <div className="mt-10 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
        <div className="text-xs uppercase tracking-wider text-zinc-500">What is real on this page, and what is not</div>
        <div className="mt-3 grid gap-4 md:grid-cols-2">
          <div>
            <div className="mb-2 text-sm text-emerald-300">Measured — pulled from the real systems</div>
            <div className="flex flex-wrap gap-1.5">{day.honesty.measured.map((x) => <Pill key={x} tone="green">{x}</Pill>)}</div>
          </div>
          <div>
            <div className="mb-2 text-sm text-amber-300">Assumed — the model chose this, it was not measured</div>
            <div className="flex flex-wrap gap-1.5">{day.honesty.assumed.map((x) => <Pill key={x} tone="amber">{x}</Pill>)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
