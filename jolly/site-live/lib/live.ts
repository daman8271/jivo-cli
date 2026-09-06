"use client";

// The one fetcher. Mark 3 bakes NOTHING into the build: every figure on every
// page arrives here, client-side, from the publisher.
//
//   https://mark3-2ff07f84.srv1685505.hstgr.cloud/state.json      the NOW layer
//   https://mark3-2ff07f84.srv1685505.hstgr.cloud/plan/<f>.json   the FORWARD layer
//
// Both are served no-store with CORS *. A Vercel deploy is a UI change only.
//
// What this module guarantees, because the spec makes each one an acceptance
// check:
//   · one poll every 180 s, shared by every mounted component
//   · every in-flight request aborted when the last subscriber unmounts
//   · exponential backoff with jitter on failure (never a retry storm)
//   · last-good kept in memory AND localStorage (every access in try/catch —
//     private windows and blocked site data make it throw, not return null)
//   · a partial or wrong-shaped body is NEVER trusted: it is a failure, and the
//     last-good stays on screen labelled stale rather than being overwritten
//   · per-source fetched_at / server_at / ok / last_good_at, and a global
//     collected_at age, are exposed so a panel can never quietly show a stale
//     number as a fresh one

import { useEffect, useRef, useState } from "react";
import type {
  AssumptionsData, DayDetail, HistoryData, HonestyData, LinesData, LoopsData, MaterialsData, Overview, SpineDay,
  StateJson, StorageData,
} from "./types";

/* ───────────────────────────── where from ───────────────────────────── */

export const PUBLISHER = "https://mark3-2ff07f84.srv1685505.hstgr.cloud";

/** Dev/offline mode: serve the saved copies from this origin, no network. */
export const FIXTURES = process.env.NEXT_PUBLIC_MARK3_FIXTURES === "1";

/** Base URL for every fetch. Overridable so a verifier can point at a dead host. */
export const BASE: string =
  process.env.NEXT_PUBLIC_MARK3_BASE || (FIXTURES ? "/fixtures" : PUBLISHER);

/* ─────────────────────────── the source list ─────────────────────────── */

export type SourceId =
  | "state" | "overview" | "spine" | "storage" | "materials" | "loops" | "honesty" | "lines" | "history"
  | "assumptions"
  | `day:${number}`;

export const dayId = (n: number): SourceId => `day:${n}` as SourceId;

const pad2 = (n: number) => String(n).padStart(2, "0");

function pathOf(id: SourceId): string {
  if (id.startsWith("day:")) return `plan/days/day-${pad2(Number(id.slice(4)))}.json`;
  if (id === "state") return "state.json";
  return `plan/${id}.json`;
}

/* ──────────────────────── never trust a partial ───────────────────────
   Each guard asks only for the keys a page would actually read. A body that
   parses but is missing them is a half-written file or a wrong file — a
   failure, not data. */

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const hasPlanMeta = (v: unknown) =>
  isObj(v) && isObj(v.meta) && typeof (v.meta as Record<string, unknown>).collected_at === "string";

const GUARDS: Record<string, (v: unknown) => boolean> = {
  state: (v) => isObj(v) && typeof v.collected_at === "string" && isObj(v.sources),
  overview: (v) => hasPlanMeta(v) && isObj((v as Record<string, unknown>).totals) &&
    isObj((v as Record<string, unknown>).opening) && isObj((v as Record<string, unknown>).demand),
  spine: (v) => Array.isArray(v) && v.length > 0 && isObj(v[0]) &&
    typeof (v[0] as Record<string, unknown>).n === "number" &&
    typeof (v[0] as Record<string, unknown>).date === "string",
  storage: (v) => hasPlanMeta(v) && isObj((v as Record<string, unknown>).ceiling) &&
    Array.isArray((v as Record<string, unknown>).series),
  materials: (v) => hasPlanMeta(v) && Array.isArray((v as Record<string, unknown>).rows),
  loops: (v) => hasPlanMeta(v) && Array.isArray((v as Record<string, unknown>).chains),
  honesty: (v) => hasPlanMeta(v) && Array.isArray((v as Record<string, unknown>).label_rules) &&
    Array.isArray((v as Record<string, unknown>).measured),
  lines: (v) => hasPlanMeta(v) && Array.isArray((v as Record<string, unknown>).lines),
  // What the plan takes as fact. The four lists are in the guard because
  // /assumptions exists to render ALL of them: a body missing one would show a
  // silently short page, and a page that quietly drops a ruling is worse than
  // one that says it could not read the file.
  assumptions: (v) => hasPlanMeta(v) && Array.isArray((v as Record<string, unknown>).settled) &&
    Array.isArray((v as Record<string, unknown>).assumed) &&
    Array.isArray((v as Record<string, unknown>).speeds) &&
    Array.isArray((v as Record<string, unknown>).open_questions),
  // The days already gone. `basis` and `meta.status` are in the guard because a
  // history file without them cannot be labelled, and an unlabelled record of
  // what the plant did is exactly what this page must never show.
  history: (v) => hasPlanMeta(v) && Array.isArray((v as Record<string, unknown>).days) &&
    Array.isArray((v as Record<string, unknown>).missing_dates) &&
    isObj((v as Record<string, unknown>).basis) &&
    typeof ((v as Record<string, unknown>).meta as Record<string, unknown>).status === "string",
  day: (v) => hasPlanMeta(v) && typeof (v as Record<string, unknown>).n === "number" &&
    Array.isArray((v as Record<string, unknown>).runs),
};

const guardFor = (id: SourceId) => GUARDS[id.startsWith("day:") ? "day" : id] ?? (() => true);

/** Is this id one of the plan files (the FORWARD layer, rebuilt by the chain)? */
export const isPlanId = (id: SourceId) => id !== "state";

/** The stamp a body carries for WHEN IT WAS MADE — the only honest age for it.
 *  state.json: collected_at (the loop's own clock). A plan file: meta.generated,
 *  the moment gen_live.py wrote it (meta.collected_at, the state it was built
 *  from, when a build did not stamp itself). The browser's fetch time says
 *  nothing about this: a plan the chain has refused to rebuild for 14 hours is
 *  fetched fresh every 3 minutes, and stamping THAT printed "as of 12:04" over
 *  yesterday evening's plan on 2026-09-05. */
export function madeStampOf(id: SourceId, data: unknown): string | null {
  if (!isObj(data)) return null;
  if (id === "state") return typeof data.collected_at === "string" ? data.collected_at : null;
  const meta = data.meta;
  if (!isObj(meta)) return null;
  if (typeof meta.generated === "string") return meta.generated;
  if (typeof meta.collected_at === "string") return meta.collected_at;
  return null;
}

/** madeStampOf for a record — null until it has a body. */
export const madeAt = (rec?: Rec): string | null => (rec ? madeStampOf(rec.id, rec.data) : null);

/** Today's date in the plant's own timezone (IST), as YYYY-MM-DD — what a plan's
 *  day 1 has to equal before the site may call it "today". */
export function istToday(now?: number): string {
  const d = now ? new Date(now) : new Date();
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit",
  }).format(d);
}

/** The publisher's own stamp for a body, when it carries one. */
function serverStampOf(id: SourceId, data: unknown): string | null {
  if (!isObj(data)) return null;
  if (id === "state") return typeof data.collected_at === "string" ? data.collected_at : null;
  const meta = data.meta;
  if (isObj(meta) && typeof meta.collected_at === "string") return meta.collected_at;
  return null;
}

/* ───────────────────────────── the record ───────────────────────────── */

export type Rec<T = unknown> = {
  id: SourceId;
  /** did the LAST attempt succeed */
  ok: boolean;
  /** the newest body we trust — last-good when ok is false. null = never had one */
  data: T | null;
  /** our clock, when the body on screen was fetched */
  fetched_at: string | null;
  /** the publisher's own stamp inside that body (collected_at) */
  server_at: string | null;
  /** when that body was last confirmed fresh */
  last_good_at: string | null;
  /** true when `data` is last-good and the last attempt failed */
  stale: boolean;
  /** verbatim failure text — never swallowed */
  error: string | null;
  /** true until the first attempt for this source has finished */
  loading: boolean;
  /** how the body reached the page: network this session, or localStorage */
  from: "network" | "storage" | null;
  failures: number;
};

const blank = (id: SourceId): Rec => ({
  id, ok: false, data: null, fetched_at: null, server_at: null, last_good_at: null,
  stale: false, error: null, loading: true, from: null, failures: 0,
});

/* ───────────────────────────── the timings ───────────────────────────── */

const INTERVAL_MS = 180_000;      // the loop publishes every ~3 min; match it
const FIRST_RETRY_MS = 30_000;    // recover fast from one blip …
const MAX_BACKOFF_MS = 1_800_000; // … then back off hard: 30s 60s 2m 4m 8m 16m 30m
const TICK_MS = 5_000;            // the scheduler's own heartbeat
const REQUEST_TIMEOUT_MS = 20_000;
const STORE_KEY = (id: SourceId) => `mark3:live:v1:${id}`;
const STORE_MAX_BYTES = 2_000_000; // do not try to persist a body larger than this

/** Freshness bands for the global badge, in minutes (UI constants). */
export const FRESH_GREEN_MIN = 6;
export const FRESH_AMBER_MIN = 15;

/* ─────────────────────────────── storage ─────────────────────────────── */
// Every single access is wrapped: localStorage THROWS in a private window, with
// site data blocked, and inside a thumbnailer. It is a convenience, never a
// dependency — the site is correct with it entirely absent.

type Saved = { data: unknown; last_good_at: string; server_at: string | null };

function loadSaved(id: SourceId): Saved | null {
  try {
    const raw = window.localStorage.getItem(STORE_KEY(id));
    if (!raw) return null;
    const p = JSON.parse(raw) as Saved;
    if (!p || typeof p.last_good_at !== "string") return null;
    if (!guardFor(id)(p.data)) return null; // a stored body must still pass the guard
    return p;
  } catch {
    return null;
  }
}

function saveGood(id: SourceId, data: unknown, at: string, serverAt: string | null) {
  try {
    const body = JSON.stringify({ data, last_good_at: at, server_at: serverAt } satisfies Saved);
    if (body.length > STORE_MAX_BYTES) return;
    window.localStorage.setItem(STORE_KEY(id), body);
  } catch {
    // quota, or storage disabled. Drop the oldest of our own keys and let the
    // next cycle try again; never let this break a render.
    try {
      for (let i = 0; i < window.localStorage.length; i++) {
        const k = window.localStorage.key(i);
        if (k && k.startsWith("mark3:live:v1:") && k !== STORE_KEY(id)) {
          window.localStorage.removeItem(k);
          break;
        }
      }
    } catch { /* nothing more to try */ }
  }
}

/* ──────────────────────────────── store ──────────────────────────────── */

type Entry = {
  rec: Rec;
  subs: number;
  nextAt: number;      // epoch ms of the next attempt
  inflight: AbortController | null;
  hydrated: boolean;   // has localStorage been consulted for this id
};

const entries = new Map<SourceId, Entry>();
const listeners = new Set<() => void>();
let ticker: ReturnType<typeof setInterval> | null = null;
let snapshotVersion = 0;

const notify = () => { snapshotVersion++; listeners.forEach((l) => l()); };

function entryOf(id: SourceId): Entry {
  let e = entries.get(id);
  if (!e) {
    e = { rec: blank(id), subs: 0, nextAt: 0, inflight: null, hydrated: false };
    entries.set(id, e);
  }
  return e;
}

/** Pull last-good out of localStorage once, the first time anyone wants this id.
 *  Called from subscribe (an effect), never during render — so the first client
 *  render still matches the server HTML and hydration stays clean. */
function hydrate(e: Entry) {
  if (e.hydrated) return;
  e.hydrated = true;
  if (typeof window === "undefined") return;
  const saved = loadSaved(e.rec.id);
  if (!saved || e.rec.data !== null) return;
  e.rec = {
    ...e.rec,
    data: saved.data,
    last_good_at: saved.last_good_at,
    fetched_at: saved.last_good_at,
    server_at: saved.server_at,
    stale: true,
    from: "storage",
  };
}

function backoffMs(failures: number) {
  const base = Math.min(FIRST_RETRY_MS * 2 ** Math.max(0, failures - 1), MAX_BACKOFF_MS);
  return base * (0.85 + Math.random() * 0.3); // jitter, so sources never sync up
}

async function pull(id: SourceId) {
  const e = entryOf(id);
  if (e.inflight) return;

  const ac = new AbortController();
  e.inflight = ac;
  const killer = setTimeout(() => ac.abort(new Error("timed out")), REQUEST_TIMEOUT_MS);
  const url = `${BASE}/${pathOf(id)}`;
  const now = () => new Date().toISOString();

  try {
    const res = await fetch(url, { cache: "no-store", signal: ac.signal, credentials: "omit" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    // .json() throws on a truncated body — that is the first line of defence
    // against a half-written file, and the guard below is the second.
    const body: unknown = await res.json();
    if (!guardFor(id)(body)) throw new Error("body did not match the shape this page reads");

    const at = now();
    e.rec = {
      id, ok: true, data: body, fetched_at: at, server_at: serverStampOf(id, body),
      last_good_at: at, stale: false, error: null, loading: false, from: "network", failures: 0,
    };
    e.nextAt = Date.now() + INTERVAL_MS;
    if (typeof window !== "undefined") saveGood(id, body, at, e.rec.server_at);
  } catch (err) {
    if (ac.signal.aborted && (err as Error)?.name === "AbortError") {
      e.inflight = null;
      clearTimeout(killer);
      return; // unmounted or superseded: leave the record exactly as it was
    }
    const failures = e.rec.failures + 1;
    e.rec = {
      ...e.rec,
      ok: false,
      // data / last_good_at / server_at are deliberately left as they were:
      // a failure never overwrites the last body we trusted, and never zeroes it
      stale: e.rec.data !== null,
      error: (err as Error)?.message || String(err),
      loading: false,
      failures,
    };
    e.nextAt = Date.now() + backoffMs(failures);
  } finally {
    clearTimeout(killer);
    e.inflight = null;
    notify();
  }
}

function sweep() {
  const t = Date.now();
  for (const [id, e] of entries) if (e.subs > 0 && !e.inflight && t >= e.nextAt) void pull(id);
}

function startTicker() {
  if (ticker !== null || typeof window === "undefined") return;
  ticker = setInterval(sweep, TICK_MS);
}

function stopTickerIfIdle() {
  let live = 0;
  for (const e of entries.values()) live += e.subs;
  if (live > 0) return;
  if (ticker !== null) { clearInterval(ticker); ticker = null; }
  // abort every request still in the air — the spec's "abort on unmount"
  for (const e of entries.values()) {
    if (e.inflight) { e.inflight.abort(); e.inflight = null; }
  }
}

function subscribe(ids: SourceId[], cb: () => void): () => void {
  listeners.add(cb);
  for (const id of ids) {
    const e = entryOf(id);
    e.subs++;
    hydrate(e);
  }
  startTicker();
  sweep(); // first pull immediately, do not wait a tick
  notify();
  return () => {
    listeners.delete(cb);
    for (const id of ids) {
      const e = entries.get(id);
      if (e) e.subs = Math.max(0, e.subs - 1);
    }
    stopTickerIfIdle();
  };
}

/** Force a pull now (the "check again" button). Clears the backoff. */
export function refreshNow(ids?: SourceId[]) {
  const list = ids ?? [...entries.keys()];
  for (const id of list) {
    const e = entryOf(id);
    e.rec = { ...e.rec, failures: 0 };
    e.nextAt = 0;
  }
  sweep();
  notify();
}

/* ───────────────────────────── the hooks ───────────────────────────── */

export type LiveMap = Record<string, Rec>;

/** Subscribe to a fixed set of sources. Returns one record per id, always
 *  defined, so a page never has to guard for undefined — only for `data:null`. */
export function useLive(ids: SourceId[]): LiveMap {
  const key = ids.join("|");
  const [, force] = useState(0);
  const idsRef = useRef(ids);
  idsRef.current = ids;

  useEffect(() => {
    const list = key ? (key.split("|") as SourceId[]) : [];
    return subscribe(list, () => force((v) => v + 1));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const out: LiveMap = {};
  for (const id of ids) out[id] = entries.get(id)?.rec ?? blank(id);
  return out;
}

/** Typed convenience readers — they only narrow, they never invent a default. */
export const asState = (r?: Rec) => (r?.data as StateJson | null) ?? null;
export const asOverview = (r?: Rec) => (r?.data as Overview | null) ?? null;
export const asSpine = (r?: Rec) => (r?.data as SpineDay[] | null) ?? null;
export const asStorage = (r?: Rec) => (r?.data as StorageData | null) ?? null;
export const asMaterials = (r?: Rec) => (r?.data as MaterialsData | null) ?? null;
export const asLoops = (r?: Rec) => (r?.data as LoopsData | null) ?? null;
export const asHonesty = (r?: Rec) => (r?.data as HonestyData | null) ?? null;
export const asLines = (r?: Rec) => (r?.data as LinesData | null) ?? null;
export const asHistory = (r?: Rec) => (r?.data as HistoryData | null) ?? null;
export const asAssumptions = (r?: Rec) => (r?.data as AssumptionsData | null) ?? null;
export const asDay = (r?: Rec) => (r?.data as DayDetail | null) ?? null;

/** A ticking clock, so an age on screen counts up between polls. */
export function useNow(everyMs = 15_000): number {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now()); // first value after hydration — SSR and first render agree on null
    const t = setInterval(() => setNow(Date.now()), everyMs);
    return () => clearInterval(t);
  }, [everyMs]);
  return now ?? 0;
}

/* ─────────────────────────── freshness maths ─────────────────────────── */

export type Band = "green" | "amber" | "red" | "unknown";

export const parseAt = (iso: string | null | undefined): number | null => {
  if (!iso) return null;
  const t = Date.parse(iso);
  return Number.isFinite(t) ? t : null;
};

/** Minutes between a stamp and now. null when either is unknown. */
export function ageMinutes(iso: string | null | undefined, now: number): number | null {
  const t = parseAt(iso);
  if (t === null || !now) return null;
  return Math.max(0, (now - t) / 60000);
}

export function bandOf(mins: number | null): Band {
  if (mins === null) return "unknown";
  if (mins <= FRESH_GREEN_MIN) return "green";
  if (mins <= FRESH_AMBER_MIN) return "amber";
  return "red";
}

/** "HH:MM" in the reader's own timezone, from an ISO stamp. */
export function hhmm(iso: string | null | undefined): string | null {
  const t = parseAt(iso);
  if (t === null) return null;
  const d = new Date(t);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** "4 minutes ago" / "2 hours 10 minutes ago" — words, never a bare number. */
export function agoWords(mins: number | null): string {
  if (mins === null) return "at a time we do not know";
  const m = Math.floor(mins);
  if (m < 1) return "less than a minute ago";
  if (m === 1) return "a minute ago";
  if (m < 60) return `${m} minutes ago`;
  const h = Math.floor(m / 60);
  const r = m % 60;
  const hw = h === 1 ? "an hour" : `${h} hours`;
  return r === 0 ? `${hw} ago` : `${hw} ${r} ${r === 1 ? "minute" : "minutes"} ago`;
}
