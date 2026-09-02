"use client";

// WhatsApp — September FORWARD PLAN. Every message in data/whatsapp.json is a
// simulated DRAFT (assumed:true, dir:"out"): nothing was sent, nobody replied,
// and this component may never invent a reply. Numbers arrive already masked
// at the data layer and are rendered verbatim — never unmasked.

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Pill } from "@/components/Card";
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

const TAG_TONE: Record<string, string> = {
  "build-list": "zinc",
  unblocked: "green",
  "packaging-zero": "red",
  ordered: "blue",
  "oil-short": "red",
  weekly: "violet",
  storage: "amber",
};

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
}: {
  threads: WaThread[];
  meta: WaData["meta"];
  dayN: Record<string, number>;
  dailyName: string | null;
}) {
  const [sel, setSel] = useState<string>(threads[0]?.name ?? "");
  const pane = useRef<HTMLDivElement>(null);

  // a freshly opened thread starts at the top, not where the last one was left
  useEffect(() => {
    if (pane.current) pane.current.scrollTop = 0;
  }, [sel]);

  const active = threads.find((t) => t.name === sel) ?? threads[0];

  const groups = useMemo(
    () => (active ? groupByDay([...active.messages].sort((a, b) => a.day.localeCompare(b.day))) : []),
    [active]
  );

  if (!active) return null;

  const activeDraftCount = active.messages.filter((m) => m.dir === "out").length;

  return (
    <div className="mt-4 grid gap-4 md:h-[calc(100vh-24rem)] md:min-h-[540px] md:grid-cols-[21rem_1fr]">
      {/* LEFT — recipients (name + role, numbers masked at the data layer) */}
      <div className="max-h-[46vh] overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/40 md:max-h-none">
        <div className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/95 px-4 py-2.5 text-xs uppercase tracking-wider text-zinc-500 backdrop-blur">
          {threads.length} recipients · {meta.sent} drafts · {meta.assumed_replies} replies
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
                        title="simulated drafts addressed to this person — none were sent"
                        className="ml-auto shrink-0 rounded-full bg-violet-500/15 px-2 py-0.5 text-[11px] text-violet-300"
                      >
                        {t.count}
                      </span>
                    </span>
                    <span className="mt-0.5 block truncate text-[11px] text-zinc-500">{t.title}</span>
                    <span className="mt-0.5 flex items-center gap-2">
                      <span className="font-mono text-[11px] text-zinc-400" title={meta.masking_note}>
                        {t.display}
                      </span>
                      <span
                        className={`shrink-0 rounded px-1.5 py-px text-[9px] font-semibold tracking-wider ${
                          daily ? "bg-emerald-500/15 text-emerald-300" : "bg-zinc-800 text-zinc-500"
                        }`}
                      >
                        {daily ? "DAILY" : "EXCEPTION-ONLY"}
                      </span>
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
        <div className="px-4 py-3 text-[11px] leading-relaxed text-zinc-500">
          Routing: the production incharge gets the build list every planned working day; everyone else is messaged only
          when something breaks their way — packaging at zero, an order going out, oil short, the weekly readout, a
          storage push.
        </div>
      </div>

      {/* RIGHT — the thread of drafts */}
      <div ref={pane} className="overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
        <div className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/95 backdrop-blur">
          <div className="flex items-center gap-2 border-b border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-[11px] font-semibold tracking-wide text-violet-300">
            SIMULATED — drafts, not sent · nothing was delivered · {meta.assumed_replies} replies
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
                <span className="font-mono text-zinc-300" title={meta.masking_note}>
                  {active.display}
                </span>
              </div>
            </div>
            <div className="ml-auto shrink-0 text-right text-xs text-zinc-400">
              <div>
                <span className="text-violet-300">{activeDraftCount} drafts</span> ·{" "}
                <span className="text-zinc-500">{meta.assumed_replies} replies</span>
              </div>
              <div className="text-zinc-600">{active.name === dailyName ? "daily build list" : "exception-only"}</div>
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
                        {waText(m.text)}
                      </div>
                      <div className="mt-1 flex flex-wrap items-center justify-end gap-2">
                        {m.assumed && (
                          <span
                            title="assumed:true in the data — the planner would send this; it was never sent"
                            className="rounded border border-dashed border-violet-400/40 bg-violet-500/10 px-1.5 py-px text-[10px] font-semibold tracking-wider text-violet-300"
                          >
                            ✎ DRAFT — NOT SENT
                          </span>
                        )}
                        <Pill tone={TAG_TONE[m.tag] ?? "zinc"}>{m.tag}</Pill>
                        <span className="text-[10px] text-zinc-600">
                          {out ? `would go to ${firstName(active.name)}` : firstName(active.name)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}

          {/* the honest end of every thread: no replies exist, none are invented */}
          <div className="flex items-center gap-3 pt-2">
            <span className="h-px flex-1 border-t border-dashed border-zinc-800" />
            <span className="max-w-[80%] text-center text-[11px] leading-relaxed text-zinc-500">
              End of drafts. {meta.assumed_replies} replies exist — nothing was actually sent, so nothing came back, and
              no reply has been invented here.
            </span>
            <span className="h-px flex-1 border-t border-dashed border-zinc-800" />
          </div>
        </div>
      </div>
    </div>
  );
}
