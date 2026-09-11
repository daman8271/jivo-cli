"use client";

// Messages (not sent). Every message in data/whatsapp.json was written by the
// planner and never sent (assumed:true, dir:"out"); nobody replied, and this
// component never invents a reply. Phone numbers arrive already masked from
// the data and are shown exactly as they are. Words are made plain here at
// render time; the data underneath does not change.

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Pill } from "@/components/Card";
import { plainWords } from "@/lib/types";
import type { WaData, WaMsg, WaThread } from "@/lib/types";

const WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function dateLabel(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return `${WD[dt.getDay()]} ${d} ${MO[m - 1]}`;
}

function initials(name: string) {
  return name
    .replace(/\(.*?\)/g, "")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

const firstName = (name: string) => name.replace(/\(.*?\)/g, "").trim().split(/\s+/)[0];

// Plain words inside a message body come from lib's plainWords (SKU → product,
// flush → oil change, lines → machines). Whole words only — numbers are never touched.

/** WhatsApp-style *bold* segments — asterisk pairs on one line become <strong>. */
function waText(text: string) {
  const seg = text.split(/\*([^*\n]+)\*/g);
  if (seg.length === 1) return text;
  return seg.map((s, i) =>
    i % 2 ? (
      <strong key={i} className="font-semibold text-zinc-50">
        {s}
      </strong>
    ) : (
      s
    )
  );
}

type Group = { day: string; msgs: WaMsg[] };

function groupByDay(msgs: WaMsg[]): Group[] {
  const out: Group[] = [];
  for (const m of msgs) {
    const last = out[out.length - 1];
    if (last && last.day === m.day) last.msgs.push(m);
    else out.push({ day: m.day, msgs: [m] });
  }
  return out;
}

export default function WaSepClient({
  threads,
  meta,
  dayN,
  dailyName,
  tagLabels,
  tagTones,
}: {
  threads: WaThread[];
  meta: WaData["meta"];
  dayN: Record<string, number>;
  dailyName: string | null;
  tagLabels: Record<string, string>;
  tagTones: Record<string, string>;
}) {
  const [sel, setSel] = useState<string>(threads[0]?.name ?? "");
  const pane = useRef<HTMLDivElement>(null);

  const label = (tag: string) => tagLabels[tag] ?? tag.replace(/-/g, " ");

  // a freshly opened conversation starts at the top, not where the last one was left
  useEffect(() => {
    if (pane.current) pane.current.scrollTop = 0;
  }, [sel]);

  const active = threads.find((t) => t.name === sel) ?? threads[0];

  const groups = useMemo(
    () => (active ? groupByDay([...active.messages].sort((a, b) => a.day.localeCompare(b.day))) : []),
    [active]
  );

  if (!active) return null;

  const activeCount = active.messages.filter((m) => m.dir === "out").length;

  // the kinds of message everyone except the daily person gets, for the footer line
  const stuckKinds: string[] = [];
  for (const t of threads) {
    if (t.name === dailyName) continue;
    for (const m of t.messages) {
      if (m.tag === "build-list") continue;
      const l = label(m.tag);
      if (!stuckKinds.includes(l)) stuckKinds.push(l);
    }
  }

  return (
    <div className="mt-4 grid gap-4 md:h-[calc(100vh-24rem)] md:min-h-[540px] md:grid-cols-[21rem_1fr]">
      {/* LEFT — the people (name + role; phone numbers arrive masked from the data) */}
      <div className="max-h-[46vh] overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/40 md:max-h-none">
        <div className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/95 px-4 py-2.5 text-xs uppercase tracking-wider text-zinc-500 backdrop-blur">
          {threads.length} people · {meta.sent} messages · {meta.assumed_replies} replies
        </div>
        <ul>
          {threads.map((t) => {
            const on = t.name === active.name;
            const daily = t.name === dailyName;
            return (
              <li key={t.name}>
                <button
                  onClick={() => setSel(t.name)}
                  className={`flex w-full items-start gap-3 border-b border-zinc-800/70 px-3 py-3 text-left transition-colors ${
                    on ? "bg-zinc-800/80" : "hover:bg-zinc-800/40"
                  }`}
                >
                  <span
                    className={`grid h-10 w-10 shrink-0 place-items-center rounded-full text-sm font-semibold ${
                      on ? "bg-violet-500/20 text-violet-300" : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {initials(t.name)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-zinc-100">{t.name}</span>
                      <span
                        title="messages written for this person — none were sent"
                        className="ml-auto shrink-0 rounded-full bg-violet-500/15 px-2 py-0.5 text-[11px] text-violet-300"
                      >
                        {t.count}
                      </span>
                    </span>
                    <span className="mt-0.5 block truncate text-[11px] text-zinc-500">{t.title}</span>
                    <span className="mt-0.5 flex items-center gap-2">
                      <span className="font-mono text-[11px] text-zinc-400" title="phone number">
                        {t.display}
                      </span>
                      <span
                        className={`shrink-0 rounded px-1.5 py-px text-[9px] font-semibold tracking-wider ${
                          daily ? "bg-emerald-500/15 text-emerald-300" : "bg-zinc-800 text-zinc-500"
                        }`}
                      >
                        {daily ? "EVERY DAY" : "ONLY WHEN STUCK"}
                      </span>
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
        <div className="px-4 py-3 text-[11px] leading-relaxed text-zinc-500">
          {dailyName ? `${firstName(dailyName)} gets the run list every day. ` : ""}
          Everyone else only when something is stuck{stuckKinds.length ? ` — ${stuckKinds.join(", ")}` : ""}.
        </div>
      </div>

      {/* RIGHT — the conversation, one side only: nothing came back */}
      <div ref={pane} className="overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
        <div className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur">
          <div className="flex items-center gap-2 border-b border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-[11px] font-semibold tracking-wide text-violet-300">
            NOT SENT — written by the computer · nobody got these · {meta.assumed_replies} replies
          </div>
          <div className="flex items-center gap-3 px-4 py-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-violet-500/20 text-sm font-semibold text-violet-300">
              {initials(active.name)}
            </span>
            <div className="min-w-0">
              <div className="truncate text-base font-semibold text-zinc-100">{active.name}</div>
              <div className="flex flex-wrap items-center gap-x-2 text-xs text-zinc-500">
                <span className="truncate">{active.title}</span>
                <span>·</span>
                <span className="font-mono text-zinc-300" title="phone number">
                  {active.display}
                </span>
              </div>
            </div>
            <div className="ml-auto shrink-0 text-right text-xs text-zinc-400">
              <div>
                <span className="text-violet-300">{activeCount} messages</span> ·{" "}
                <span className="text-zinc-500">{meta.assumed_replies} replies</span>
              </div>
              <div className="text-zinc-600">
                {active.name === dailyName ? "gets the run list every day" : "only when something is stuck"}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4 px-4 py-4">
          {groups.map((g) => {
            const n = dayN[g.day];
            const chip = (
              <>
                {dateLabel(g.day)}
                {n ? ` · day ${n}` : ""}
              </>
            );
            return (
              <div key={g.day} className="space-y-2">
                <div className="flex justify-center">
                  {n ? (
                    <Link
                      href={`/days/${n}`}
                      className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-[11px] text-zinc-400 hover:border-violet-500/40 hover:text-violet-300"
                    >
                      {chip}
                    </Link>
                  ) : (
                    <span className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-[11px] text-zinc-400">
                      {chip}
                    </span>
                  )}
                </div>
                {g.msgs.map((m, i) => {
                  const out = m.dir === "out";
                  return (
                    <div key={`${g.day}-${i}`} className={`flex flex-col ${out ? "items-end" : "items-start"}`}>
                      <div
                        className={`max-w-[92%] whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2.5 text-[13.5px] leading-relaxed sm:max-w-[80%] ${
                          m.assumed
                            ? "rounded-br-sm border border-dashed border-violet-400/40 bg-violet-500/10 text-zinc-100"
                            : out
                              ? "rounded-br-sm border border-zinc-700/60 bg-zinc-800 text-zinc-100"
                              : "rounded-bl-sm border border-zinc-700/60 bg-zinc-800 text-zinc-100"
                        }`}
                      >
                        {waText(plainWords(m.text))}
                      </div>
                      <div className="mt-1 flex flex-wrap items-center justify-end gap-2">
                        {m.assumed && (
                          <span
                            title="The computer wrote this. It was never sent."
                            className="rounded border border-dashed border-violet-400/40 bg-violet-500/10 px-1.5 py-px text-[10px] font-semibold tracking-wider text-violet-300"
                          >
                            NOT SENT
                          </span>
                        )}
                        <Pill tone={tagTones[m.tag] ?? "zinc"}>{label(m.tag)}</Pill>
                        <span className="text-[10px] text-zinc-600">
                          {out ? `for ${firstName(active.name)}` : firstName(active.name)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}

          {/* the honest end of every conversation: no replies exist, none are invented */}
          <div className="flex items-center gap-3 pt-2">
            <span className="h-px flex-1 border-t border-dashed border-zinc-800" />
            <span className="max-w-[80%] text-center text-[11px] leading-relaxed text-zinc-500">
              End of messages. {meta.assumed_replies} replies — nothing was sent, so nothing came back. No reply is
              made up here.
            </span>
            <span className="h-px flex-1 border-t border-dashed border-zinc-800" />
          </div>
        </div>
      </div>
    </div>
  );
}
