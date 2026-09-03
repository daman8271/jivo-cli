"use client";

// Freshness is a first-class element on this site, not a footnote.
//
//  · every panel says "as of HH:MM", taken from ITS OWN source's fetched_at
//    (the publisher's own server_at is on hover)
//  · one global badge says how long ago the loop ran, from collected_at:
//    green ≤ 6 min, amber ≤ 15, red beyond — and red says in words that the
//    cron is dead
//  · a source whose last attempt failed renders its last-good body GREYED with
//    "no fresh data since <last_good_at>". Never a zero. Never blank.

import { useState } from "react";
import {
  agoWords, ageMinutes, asState, bandOf, FRESH_AMBER_MIN, FRESH_GREEN_MIN, hhmm, refreshNow, useLive, useNow,
  type Band, type Rec,
} from "../lib/live";
import type { Persist } from "../lib/labels";

/* ─────────────────────────────── as of ─────────────────────────────── */

const BAND_TEXT: Record<Band, string> = {
  green: "text-emerald-300",
  amber: "text-amber-300",
  red: "text-red-300",
  unknown: "text-zinc-500",
};
const BAND_CHIP: Record<Band, string> = {
  green: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  amber: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  red: "bg-red-500/15 text-red-300 border-red-500/40",
  unknown: "bg-zinc-800 text-zinc-400 border-zinc-700",
};

/** "as of 16:42" for one panel, from that panel's own source. */
export function AsOf({ rec, label }: { rec?: Rec; label?: string }) {
  const now = useNow();
  if (!rec) return null;
  const stamp = rec.fetched_at;
  const t = hhmm(stamp);
  const mins = ageMinutes(stamp, now);
  const band = rec.ok ? bandOf(mins) : "red";
  const title = [
    rec.server_at ? `the publisher's own stamp: ${rec.server_at}` : "the publisher gave no stamp of its own",
    rec.fetched_at ? `we read it at ${rec.fetched_at}` : null,
    rec.from === "storage" ? "carried from this browser's saved copy" : null,
    rec.error ? `last attempt failed: ${rec.error}` : null,
  ].filter(Boolean).join(" · ");

  return (
    <span className={`text-[11px] tabular-nums ${BAND_TEXT[band]}`} title={title}>
      {label ? `${label} ` : ""}
      {t ? `as of ${t}` : "not read yet"}
      {/* "not fresh" means an attempt FAILED. While the first read of the
          session is still in the air over a saved copy, nothing has failed
          yet and saying so would be crying wolf. */}
      {rec.stale && !rec.loading ? " · not fresh" : ""}
    </span>
  );
}

/* ───────────────────────── the global loop badge ───────────────────────── */

/** How long ago the ingest loop ran. Red says the cron is dead, in words. */
export function LoopBadge() {
  const live = useLive(["state"]);
  const now = useNow(10_000);
  const rec = live.state;
  const st = asState(rec);
  const collected = st?.collected_at ?? null;
  const mins = ageMinutes(collected, now);
  // "the loop last ran a minute ago" is TRUE and useless while this browser
  // cannot reach the publisher at all — the panels below say "no fresh data"
  // and the badge would sit there green contradicting them. An unreachable
  // publisher is red, whatever stamp the last body happens to carry.
  const unreachable = !rec.ok && !rec.loading;
  const band: Band = unreachable ? "red" : collected === null ? "unknown" : bandOf(mins);

  const words = unreachable
    ? collected
      ? `this browser cannot reach the publisher — what is on screen was read at ${hhmm(collected)}, ${agoWords(mins)}`
      : "this browser cannot reach the publisher, and has never read it"
    : band === "unknown"
      ? rec.loading
        ? "reading the plant…"
        : "the plant has not answered this browser yet"
      : band === "red"
        ? `the loop has not run since ${hhmm(collected)} — ${agoWords(mins)}. It runs every few minutes, so it is not running.`
        : `the loop last ran ${agoWords(mins)}`;

  return (
    <button
      type="button"
      onClick={() => refreshNow()}
      title={`${words}${rec.error ? ` · last attempt: ${rec.error}` : ""} — click to read again now`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${BAND_CHIP[band]}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          band === "green" ? "bg-emerald-400" : band === "amber" ? "bg-amber-400" : band === "red" ? "bg-red-400" : "bg-zinc-500"
        }`}
      />
      {words}
    </button>
  );
}

/** The one-line strip under the nav — what this site is, and how old it is. */
export function LoopBanner() {
  const live = useLive(["state"]);
  const now = useNow(10_000);
  const rec = live.state;
  const st = asState(rec);
  const mins = ageMinutes(st?.collected_at ?? null, now);
  const band: Band = st?.collected_at ? bandOf(mins) : "unknown";
  const failed = Object.entries(st?.sources ?? {}).filter(([, s]) => !s.ok);
  const unreachable = !rec.ok && !rec.loading;

  if (band === "red" || unreachable || failed.length > 0) {
    return (
      <div className="border-b border-red-500/25 bg-red-500/10">
        <div className="mx-auto max-w-7xl px-5 py-1.5 text-xs text-red-200">
          {unreachable && (
            <span className="font-semibold">
              This browser cannot reach the publisher{rec.error ? ` (${rec.error})` : ""}. Everything below is the last
              reading it got{st?.collected_at ? `, taken at ${hhmm(st.collected_at)}` : ""}.{" "}
            </span>
          )}
          {band === "red" && !unreachable && (
            <span className="font-semibold">
              The loop has not run since {hhmm(st?.collected_at)} ({agoWords(mins)}). Everything below is the last thing
              it saw, not the plant right now.{" "}
            </span>
          )}
          {failed.length > 0 && (
            <span>
              Not answering this cycle: {failed.map(([k]) => k.replace(/_/g, " ")).join(", ")}. Those panels show the
              last good read, greyed.
            </span>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className="border-b border-emerald-500/15 bg-emerald-500/5">
      <div className="mx-auto max-w-7xl px-5 py-1.5 text-xs text-emerald-200/90">
        <span className="font-semibold">Only today is real.</span> Every later day is worked out by the computer from
        today&rsquo;s count — and the whole thing is re-worked every few minutes.
      </div>
    </div>
  );
}

/* ──────────────────── the stale wrapper (never a zero) ──────────────────── */

/**
 * Wrap a panel's body. Three states, and only three:
 *   · never read      → says so, shows nothing
 *   · fresh           → the body, plain
 *   · last attempt failed but we have a body → the body GREYED, with
 *     "no fresh data since <last_good_at>" above it
 */
export function Live({
  rec, children, what,
}: {
  rec?: Rec;
  children: React.ReactNode;
  /** what this panel is about, for the empty line: "the tanks", "today's runs" */
  what?: string;
}) {
  const now = useNow();
  if (!rec) return <>{children}</>;

  if (rec.data === null) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-700 bg-zinc-900/30 p-4 text-sm text-zinc-400">
        {rec.loading ? (
          <>Reading {what ?? "this"} from the plant…</>
        ) : (
          <>
            <span className="text-zinc-300">No reading for {what ?? "this"} yet.</span>{" "}
            {rec.error ? <span className="text-zinc-500">The publisher said: {rec.error}.</span> : null}{" "}
            <button type="button" className="underline underline-offset-2 hover:text-zinc-200" onClick={() => refreshNow([rec.id])}>
              try again
            </button>
          </>
        )}
      </div>
    );
  }

  if (!rec.stale) return <>{children}</>;

  const mins = ageMinutes(rec.last_good_at, now);

  // A saved copy on screen while the FIRST read of this session is still in
  // the air is not a failure — nothing has gone wrong yet. Saying "no fresh
  // data" here flashed a false alarm on every page load that had a saved copy.
  if (rec.loading) {
    return (
      <div>
        <div className="mb-2 flex flex-wrap items-center gap-2 rounded-md border border-zinc-700 bg-zinc-900/50 px-2.5 py-1.5 text-[11px] text-zinc-400">
          <span>
            This browser&rsquo;s saved copy from {hhmm(rec.last_good_at) ?? "an unknown time"} — reading the plant now…
          </span>
        </div>
        <div className="opacity-70">{children}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-1.5 text-[11px] text-amber-200">
        <span className="font-semibold">No fresh data since {hhmm(rec.last_good_at) ?? "an unknown time"}</span>
        <span className="text-amber-200/70">({agoWords(mins)})</span>
        {rec.error && <span className="text-amber-200/60">— {rec.error}</span>}
        <button type="button" className="ml-auto underline underline-offset-2" onClick={() => refreshNow([rec.id])}>
          try again
        </button>
      </div>
      <div className="opacity-45 grayscale" aria-describedby="stale">
        {children}
      </div>
    </div>
  );
}

/* ─────────────────── source-level freshness, per adapter ─────────────────── */

/** state.json's per-adapter envelope, for a panel fed by one adapter.
 *
 *  TWO different things can make this panel stale, and both have to show:
 *   · that one adapter did not answer the loop this cycle (`env.ok === false`)
 *   · this browser could not refresh state.json AT ALL (`rec.stale`) — in which
 *     case every adapter inside the body still says it answered, because it did,
 *     minutes ago, in a body nobody can replace. Trusting `env.ok` alone printed
 *     a plain "as of 16:36" over numbers the publisher had stopped serving. */
export function SourceLine({ src, rec }: { src: string; rec?: Rec }) {
  const live = useLive(["state"]);
  const st = asState(live.state);
  const env = st?.sources?.[src];
  if (!env) return <AsOf rec={rec} />;
  // a saved copy while the first read is still in flight is not a failure
  const unread = live.state.stale && !live.state.loading;
  const fresh = env.ok && !unread;
  const t = hhmm(env.fetched_at);
  // when the adapter answered but the body is old, the honest stamp is when
  // THAT adapter's figures were actually read
  const since = env.ok ? env.fetched_at : env.last_good_at;
  const tone = fresh ? "text-zinc-500" : "text-amber-300";
  return (
    <span
      className={`text-[11px] tabular-nums ${tone}`}
      title={[
        `${src}: ${env.ok ? "answered" : "did not answer"} the loop when this body was written`,
        env.server_at ? `its own stamp: ${env.server_at}` : "it gave no stamp of its own",
        env.error ? `error: ${env.error}` : null,
        env.last_good_at ? `last good: ${env.last_good_at}` : null,
        unread ? `this browser could not read the publisher: ${live.state.error ?? "no reason given"}` : null,
      ].filter(Boolean).join(" · ")}
    >
      {fresh ? `as of ${t ?? "—"}` : `no fresh data since ${hhmm(since) ?? "an unknown time"}`}
    </span>
  );
}

/** A whole panel fed by one adapter inside state.json. It greys out for either
 *  reason a panel can be out of date: that one adapter failed the loop, or this
 *  browser could not fetch state.json at all. The second case is the one that
 *  used to slip through — `env.ok` is still true inside a body that is minutes
 *  old and cannot be replaced, so the panel rendered plain and "LIVE". */
export function LiveSource({
  src, children, what,
}: {
  src: string;
  children: React.ReactNode;
  what?: string;
}) {
  const live = useLive(["state"]);
  const now = useNow();
  const rec = live.state;
  const st = asState(rec);
  const env = st?.sources?.[src];

  if (!st) return <Live rec={rec} what={what}>{children}</Live>;
  if (!env) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-700 bg-zinc-900/30 p-4 text-sm text-zinc-400">
        The loop is not reading {what ?? src.replace(/_/g, " ")} at all this cycle.
      </div>
    );
  }
  const bodyStale = rec.stale && !rec.loading; // a failure, not a first read
  if (env.ok && !bodyStale) return <>{children}</>;

  // which stamp is honest depends on which of the two failed
  const since = env.ok ? env.fetched_at : (env.last_good_at ?? null);
  const why = env.ok ? rec.error : env.error;
  const mins = ageMinutes(since, now);
  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-1.5 text-[11px] text-amber-200">
        <span className="font-semibold">
          No fresh data since {hhmm(since) ?? "an unknown time"}
        </span>
        <span className="text-amber-200/70">({agoWords(mins)})</span>
        {why && <span className="text-amber-200/60">— {why}</span>}
        {env.ok && (
          <button type="button" className="ml-auto underline underline-offset-2" onClick={() => refreshNow([rec.id])}>
            try again
          </button>
        )}
      </div>
      <div className="opacity-45 grayscale">{children}</div>
    </div>
  );
}

/* ───────────────────────── persistent (non-live) badge ───────────────────── */

/** The badge that follows a non-live input everywhere it appears. */
export function NotLive({ p, className = "" }: { p: Persist; className?: string }) {
  const [open, setOpen] = useState(false);
  return (
    <button
      type="button"
      onClick={() => setOpen((v) => !v)}
      title={p.note}
      className={`inline-flex items-center gap-1 rounded border border-amber-500/30 bg-amber-500/10 px-1.5 py-px align-middle text-[10px] font-semibold tracking-wider text-amber-300 ${className}`}
    >
      {p.label}
      {open && <span className="ml-1 font-normal tracking-normal text-amber-200/80">— {p.note}</span>}
    </button>
  );
}

/** The freshness legend, so the colours mean something without being told. */
export function FreshnessKey() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-500">
      <span className="inline-flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> read in the last {FRESH_GREEN_MIN} minutes
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> up to {FRESH_AMBER_MIN} minutes old
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" /> older — the loop is not running
      </span>
    </div>
  );
}
