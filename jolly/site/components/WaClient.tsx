"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Pill } from "@/components/Card";
import type { Thread, Msg } from "@/lib/types";

const WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const dayNum = (iso: string) => Number(iso.slice(8, 10));

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
  "packaging-zero": "red",
  "oil-short": "red",
  storage: "amber",
  decision: "amber",
  "po-shift": "blue",
  labour: "green",
  weekly: "zinc",
  "day-brief": "zinc",
};

type Group = { day: string; msgs: Msg[] };

function groupByDay(msgs: Msg[]): Group[] {
  const out: Group[] = [];
  for (const m of msgs) {
    const last = out[out.length - 1];
    if (last && last.day === m.day) last.msgs.push(m);
    else out.push({ day: m.day, msgs: [m] });
  }
  return out;
}

export default function WaClient({ threads }: { threads: Thread[] }) {
  const [sel, setSel] = useState<string>(threads[0]?.whatsapp ?? "");
  const [day, setDay] = useState<number | "all">("all");
  const pane = useRef<HTMLDivElement>(null);

  // start a newly opened thread at the top, not wherever the last one was scrolled to
  useEffect(() => {
    if (pane.current) pane.current.scrollTop = 0;
  }, [sel, day]);

  // messages per calendar day, across everyone — feeds the day picker labels
  const perDay = useMemo(() => {
    const m = new Map<number, number>();
    for (const t of threads) for (const x of t.messages) m.set(dayNum(x.day), (m.get(dayNum(x.day)) ?? 0) + 1);
    return m;
  }, [threads]);

  // month the data sits in, taken from the data itself
  const month = useMemo(() => {
    const first = threads.flatMap((t) => t.messages.map((m) => m.day)).sort()[0] ?? "2026-08-01";
    return first.slice(0, 7);
  }, [threads]);

  const shown = useMemo(
    () =>
      threads.map((t) => {
        const msgs = day === "all" ? t.messages : t.messages.filter((m) => dayNum(m.day) === day);
        return {
          t,
          msgs: [...msgs].sort((a, b) => a.day.localeCompare(b.day)),
          sent: msgs.filter((m) => m.dir === "out").length,
          got: msgs.filter((m) => m.dir === "in").length,
        };
      }),
    [threads, day]
  );

  const totalShown = shown.reduce((n, s) => n + s.msgs.length, 0);
  const totalAll = threads.reduce((n, t) => n + t.messages.length, 0);
  const active = shown.find((s) => s.t.whatsapp === sel) ?? shown[0];

  function pickDay(next: number | "all") {
    setDay(next);
    if (next !== "all") {
      const cur = threads.find((t) => t.whatsapp === sel);
      const has = cur?.messages.some((m) => dayNum(m.day) === next);
      if (!has) {
        const alt = threads.find((t) => t.messages.some((m) => dayNum(m.day) === next));
        if (alt) setSel(alt.whatsapp);
      }
    }
    const u = new URL(window.location.href);
    if (next === "all") u.searchParams.delete("day");
    else u.searchParams.set("day", String(next));
    window.history.replaceState(null, "", u.toString());
  }

  // arrive from the day view as /whatsapp?day=18 and land on that day
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("day");
    const n = q ? Number(q) : NaN;
    if (!Number.isInteger(n) || n < 1 || n > 31) return;
    setDay(n);
    setSel((cur) => {
      const t = threads.find((x) => x.whatsapp === cur);
      if (t?.messages.some((m) => dayNum(m.day) === n)) return cur;
      return threads.find((x) => x.messages.some((m) => dayNum(m.day) === n))?.whatsapp ?? cur;
    });
    // mount only — the URL is read once, then the picker owns the state
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      {/* day filter */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/60 px-4 py-3">
        <label htmlFor="wa-day" className="text-xs uppercase tracking-wider text-zinc-500">
          Day
        </label>
        <select
          id="wa-day"
          value={day === "all" ? "all" : String(day)}
          onChange={(e) => pickDay(e.target.value === "all" ? "all" : Number(e.target.value))}
          className="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-sm text-zinc-100 outline-none focus:border-amber-500/70"
        >
          <option value="all">All 31 days — {totalAll} messages</option>
          {Array.from({ length: 31 }, (_, i) => i + 1).map((n) => {
            const iso = `${month}-${String(n).padStart(2, "0")}`;
            const c = perDay.get(n) ?? 0;
            return (
              <option key={n} value={n}>
                {dateLabel(iso)} — {c === 0 ? "no messages" : `${c} message${c === 1 ? "" : "s"}`}
              </option>
            );
          })}
        </select>
        <span className="text-sm text-zinc-400">
          {day === "all" ? (
            <>Showing every message the plan would have sent in August, with the replies written in.</>
          ) : (
            <>
              Showing {totalShown} of {totalAll} messages — {dateLabel(`${month}-${String(day).padStart(2, "0")}`)} only.{" "}
              <Link href={`/day/${day}`} className="text-amber-400 hover:underline">
                open day {day}
              </Link>
            </>
          )}
        </span>
        {day !== "all" && (
          <button
            onClick={() => pickDay("all")}
            className="ml-auto rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800"
          >
            Show all days
          </button>
        )}
      </div>

      <div className="mt-4 grid gap-4 md:h-[calc(100vh-26rem)] md:min-h-[500px] md:grid-cols-[20rem_1fr]">
        {/* LEFT — people */}
        <div className="max-h-[46vh] overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/40 md:max-h-none">
          <div className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-900/95 px-4 py-2.5 text-xs uppercase tracking-wider text-zinc-500 backdrop-blur">
            {threads.length} people · most messaged first
          </div>
          <ul>
            {shown.map(({ t, msgs, sent }) => {
              const on = t.whatsapp === active?.t.whatsapp;
              const empty = msgs.length === 0;
              return (
                <li key={t.whatsapp}>
                  <button
                    onClick={() => setSel(t.whatsapp)}
                    className={`flex w-full items-center gap-3 border-b border-zinc-800/70 px-3 py-3 text-left transition-colors ${
                      on ? "bg-zinc-800/80" : "hover:bg-zinc-800/40"
                    } ${empty ? "opacity-40" : ""}`}
                  >
                    <span
                      className={`grid h-10 w-10 shrink-0 place-items-center rounded-full text-sm font-semibold ${
                        on ? "bg-amber-500/20 text-amber-300" : "bg-zinc-800 text-zinc-400"
                      }`}
                    >
                      {initials(t.name)}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2">
                        <span className="truncate text-sm font-medium text-zinc-100">{t.name}</span>
                        <span
                          title="messages sent to this person"
                          className={`ml-auto shrink-0 rounded-full px-2 py-0.5 text-[11px] ${
                            empty ? "bg-zinc-800 text-zinc-500" : "bg-emerald-500/15 text-emerald-300"
                          }`}
                        >
                          {sent}
                        </span>
                      </span>
                      <span className="mt-0.5 block truncate text-[11px] text-zinc-500">{t.title}</span>
                      <span className="mt-0.5 block font-mono text-[11px] text-zinc-400">{t.display}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* RIGHT — the thread */}
        <div ref={pane} className="overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/40">
          {active && (
            <>
              <div className="sticky top-0 z-10 flex items-center gap-3 border-b border-zinc-800 bg-zinc-900/95 px-4 py-3 backdrop-blur">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-amber-500/20 text-sm font-semibold text-amber-300">
                  {initials(active.t.name)}
                </span>
                <div className="min-w-0">
                  <div className="truncate text-base font-semibold text-zinc-100">{active.t.name}</div>
                  <div className="flex flex-wrap items-center gap-x-2 text-xs text-zinc-500">
                    <span className="font-mono text-zinc-300">{active.t.display}</span>
                    <span>·</span>
                    <span className="truncate">{active.t.title}</span>
                  </div>
                </div>
                <div className="ml-auto shrink-0 text-right text-xs text-zinc-400">
                  <div>
                    <span className="text-emerald-300">{active.sent} sent</span> · {active.got} back
                  </div>
                  <div className="text-zinc-600">
                    {day === "all" ? "whole month" : dateLabel(`${month}-${String(day).padStart(2, "0")}`)}
                  </div>
                </div>
              </div>

              {active.msgs.length === 0 ? (
                <div className="px-4 py-16 text-center text-sm text-zinc-500">
                  Nothing sent to {firstName(active.t.name)} on{" "}
                  {dateLabel(`${month}-${String(day).padStart(2, "0")}`)}.
                  <div className="mt-3">
                    <button
                      onClick={() => pickDay("all")}
                      className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800"
                    >
                      Show the whole month
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 px-4 py-4">
                  {groupByDay(active.msgs).map((g) => (
                    <div key={g.day} className="space-y-2">
                      <div className="flex justify-center">
                        <Link
                          href={`/day/${dayNum(g.day)}`}
                          className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-[11px] text-zinc-400 hover:border-amber-500/40 hover:text-amber-300"
                        >
                          {dateLabel(g.day)} · day {dayNum(g.day)}
                        </Link>
                      </div>
                      {g.msgs.map((m, i) => {
                        const out = m.dir === "out";
                        return (
                          <div key={`${g.day}-${i}`} className={`flex flex-col ${out ? "items-end" : "items-start"}`}>
                            <div
                              className={`max-w-[88%] whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2.5 text-[13.5px] leading-relaxed sm:max-w-[76%] ${
                                out
                                  ? "rounded-br-sm border border-emerald-800/50 bg-emerald-900/45 text-emerald-50"
                                  : "rounded-bl-sm border border-zinc-700/60 bg-zinc-800 text-zinc-100"
                              }`}
                            >
                              {m.text}
                            </div>
                            <div className="mt-1 flex items-center gap-2">
                              {out && <span className="text-[10px] text-zinc-600">you</span>}
                              <><Pill tone={TAG_TONE[m.tag] ?? "zinc"}>{m.tag}</Pill>{!out && <Pill tone="amber">assumed reply</Pill>}</>
                              {!out && <span className="text-[10px] text-zinc-600">{firstName(active.t.name)}</span>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
