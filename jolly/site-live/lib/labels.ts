// The label rules, applied at render.
//
// plan/honesty.json ships `label_rules` — fourteen sentences the publisher wrote
// about its own numbers ("this counter only ever goes up, it is NOT what is
// still pending"; "never headline FG0000155's realise unqualified"). Mark 2
// re-typed those sentences into JSX. Mark 3 reads them, so a rule changed in the
// engine changes the page on the next poll with no deploy.
//
// Nothing in this file contains a business number. Where a rule carries one
// (the ceiling, the forecast share) it comes out of the rule object itself.

import type { DispatchRow, HonestyData, LabelRule, OrderRow } from "./types";

/* ───────────────────────────── rule lookup ───────────────────────────── */

export type RuleId =
  | "rolling-replan" | "happened-days" | "po-open-value" | "po-open-litres" | "orders-mixed"
  | "two-oil-series" | "forecast-tags" | "ceiling-declared" | "standing-measured" | "day1-pile"
  | "observed-then-derated" | "unproducible" | "realise-outlier" | "numbers-masked" | "tank-dip"
  // Mark 4. A rule the publisher has not shipped reads null and the page says
  // nothing — it never falls back to a sentence with a number typed into it.
  | "speed-planning" | "night-line" | "dispatch-pendency" | "money-target" | "manual-fill"
  | "expected-orders-basis";

export function rule(h: HonestyData | null, id: RuleId): LabelRule | null {
  if (!h?.label_rules) return null;
  return h.label_rules.find((r) => r.id === id) ?? null;
}

/** The rule's own sentence, or null when the publisher did not ship that rule.
 *  Null means "say nothing" — never means "make something up". */
export function ruleText(h: HonestyData | null, id: RuleId): string | null {
  const r = rule(h, id);
  return r && typeof r.rule === "string" ? r.rule : null;
}

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const str = (v: unknown): string | null => (typeof v === "string" && v ? v : null);

/* ───────────────── the rules pages need as more than prose ───────────── */

/** FG0000155's realise is an inherited outlier — never a headline unqualified. */
export function realiseOutlier(h: HonestyData | null): { code: string | null; note: string | null } {
  const r = rule(h, "realise-outlier");
  const detail = (r?.detail ?? null) as Record<string, unknown> | null;
  return {
    code: str(detail?.code) ?? null,
    note: str(detail?.note) ?? ruleText(h, "realise-outlier"),
  };
}

export const isRealiseOutlier = (h: HonestyData | null, code: string | null | undefined) =>
  !!code && realiseOutlier(h).code === code;

/** The four plan SKUs no machine can fill. Shown, never hidden. */
export function unproducibleCodes(h: HonestyData | null): string[] {
  const r = rule(h, "unproducible");
  const codes = r?.codes;
  return Array.isArray(codes) ? codes.filter((c): c is string => typeof c === "string") : [];
}

/** The godown limit is Daman's own capacity sheet — a limit he declared, not a guess
 *  we made. Ruled 2026-09-04; the site says YOUR LIMIT, never OUR GUESS. */
export function ceilingRule(h: HonestyData | null) {
  const r = rule(h, "ceiling-declared");
  return { text: ruleText(h, "ceiling-declared"), working_l: num(r?.working_l), peak_l: num(r?.peak_l) };
}

/** Machines are derated once from the listed speed, twice where we measured it. */
export function derateRule(h: HonestyData | null) {
  const r = rule(h, "observed-then-derated");
  const slots = Array.isArray(r?.measured_slots)
    ? (r!.measured_slots as unknown[]).filter((s): s is string => typeof s === "string")
    : [];
  return { text: ruleText(h, "observed-then-derated"), efficiency: num(r?.efficiency), measuredSlots: slots };
}

export function forecastShareRule(h: HonestyData | null) {
  const r = rule(h, "orders-mixed");
  return { text: ruleText(h, "orders-mixed"), sharePct: num(r?.forecast_share_litres_pct) };
}

/** The days between the 1st and yesterday are RECORDS, not the plan — and the
 *  two ways of counting what was filled are never added. Counts come from the
 *  rule object, never from a number typed into a page. */
export function happenedRule(h: HonestyData | null) {
  const r = rule(h, "happened-days");
  return {
    text: ruleText(h, "happened-days"),
    through: str(r?.through),
    days: num(r?.days),
    notRead: num(r?.not_read),
    status: str(r?.status),
  };
}

export function standingRule(h: HonestyData | null) {
  const r = rule(h, "standing-measured");
  return {
    text: ruleText(h, "standing-measured"),
    litres: num(r?.billed_not_gone_l),
    pctOfCeiling: num(r?.pct_of_ceiling),
  };
}

/** The rule object a rule carries about where its figure came from. */
export function ruleSource(h: HonestyData | null, id: RuleId) {
  const s = (rule(h, id)?.source ?? null) as Record<string, unknown> | null;
  if (!s) return null;
  return {
    source: str(s.source),
    fetched_at: str(s.fetched_at),
    server_at: str(s.server_at),
    mode: str(s.mode),
    note: str(s.note),
  };
}

/* ─────────────────────────── Mark 4 rules ───────────────────────────
   Six rules the rulebook added. Each reader returns the publisher's own
   sentence plus the figures that rule carries — so a page can lay them out
   without ever typing one. */

/** How the plan picks a machine speed: a share of the listed speed, held to the
 *  best August run that lasted long enough to count. */
export function speedRule(h: HonestyData | null) {
  const r = rule(h, "speed-planning");
  return {
    text: ruleText(h, "speed-planning"),
    factor: num(r?.planning_factor),
    minRuns: num(r?.min_runs_for_cap),
    sustainedHours: num(r?.sustained_hours),
    efficiency: num(r?.efficiency),
  };
}

/** One machine, and only one, gets a second session — named, with the reason. */
export function nightRule(h: HonestyData | null) {
  const r = rule(h, "night-line");
  return {
    text: ruleText(h, "night-line"),
    line: str(r?.line),
    reason: str(r?.reason),
    nights: num(r?.nights_in_this_run),
  };
}

/** The dispatch headline is the open book and the wait — not what left today. */
export function pendencyRule(h: HonestyData | null) {
  const r = rule(h, "dispatch-pendency");
  return {
    text: ruleText(h, "dispatch-pendency"),
    pendencyDaysAll: num(r?.pendency_days_all),
    lagMedianDays: num(r?.lag_median_days),
    lagP90Days: num(r?.lag_p90_days),
    /** true = one measurement carried forward; false = re-measured every day */
    lagStatic: r?.lag_static === true,
  };
}

/** The day in rupees, against the plant's own floor and target. */
export function moneyRule(h: HonestyData | null) {
  const r = rule(h, "money-target");
  return {
    text: ruleText(h, "money-target"),
    targetRsPerDay: num(r?.target_rs_per_day),
    floorRsPerDay: num(r?.floor_rs_per_day),
    basis: str(r?.basis),
  };
}

/** The drums are filled by hand. They are never a machine that is missing. */
export function manualRule(h: HonestyData | null) {
  const r = rule(h, "manual-fill");
  const codes = Array.isArray(r?.codes)
    ? (r!.codes as unknown[]).filter((c): c is string => typeof c === "string")
    : [];
  return { text: ruleText(h, "manual-fill"), codes, display: str(r?.display) };
}

/** Orders nobody has placed yet, worked out from what the trade really bought. */
export function expectedRule(h: HonestyData | null) {
  const r = rule(h, "expected-orders-basis");
  const w = (r?.window ?? null) as Record<string, unknown> | null;
  return {
    text: ruleText(h, "expected-orders-basis"),
    present: r?.present === true,
    used: r?.used === true,
    months: num(r?.months),
    from: str(w?.from),
    to: str(w?.to),
    fallbackReason: str(r?.fallback_reason),
  };
}

/* ──────────────── the five words a planning speed can carry ────────────────
   Mark 3 had three (rated / observed / derived) and the site's map still only
   knew those, so a Mark 4 slot marked `capped`, `typical` or `carried` fell
   through to "the machine's listed speed" — which is the one thing those three
   are NOT. Each word gets its own tone and its own plain sentence; the slot's
   own `note` still wins over the fallback wherever the publisher wrote one. */

export const SPEED_BASIS: Record<string, { tone: string; label: string; words: string }> = {
  capped: {
    tone: "green",
    label: "held to August",
    words: "a share of the listed speed, then held to the best the machine really kept for hours at a stretch",
  },
  rated: {
    tone: "zinc",
    label: "listed speed",
    words: "a share of the machine's listed speed — August had no run long enough to hold it to",
  },
  typical: {
    tone: "blue",
    label: "August typical",
    words: "the middle August run — the factory app lists no speed for this pack",
  },
  carried: {
    tone: "amber",
    label: "carried over",
    words: "carried over from the last plan and cut back — no listed speed, and no August run",
  },
  derived: {
    tone: "amber",
    label: "worked out",
    words: "taken from another pack on the same machine — nobody has timed this one on its own",
  },
  // The sixth word, and the one that must never render as a bare label: the
  // machine may take the pack and NOBODY HAS GIVEN IT A SPEED. It is a question
  // for the plant, not a slot that runs at zero.
  none: {
    tone: "red",
    label: "no rate yet",
    words: "nobody has given this machine a speed for this pack — the plan puts nothing here until somebody rules on one",
  },
};

export const speedBasis = (kind: string | null | undefined) =>
  SPEED_BASIS[(kind ?? "").toLowerCase()] ?? { tone: "zinc", label: kind || "—", words: "" };

/** 1 / 2 / 3 in floor words. The rulebook's own preference ladder. */
export const PREF_WORDS: Record<number, string> = {
  1: "first choice",
  2: "when the first choice is full",
  3: "last resort",
};
export const prefWords = (p: number | null | undefined) =>
  typeof p === "number" && PREF_WORDS[p] ? PREF_WORDS[p] : "";

/* ─────────────────────────── phone masking ───────────────────────────
   honesty rule `numbers-masked`: no real phone number anywhere on this site.
   The plan files honour it. state.json does NOT — the live gate feed carries
   driver names like "Sompal <ten digits>". Anything from the NOW layer that
   could hold free text goes through this before it reaches the DOM.

   The trap this hit on the first pass: an ISO date is also a long run of digits
   and dashes, so a naive phone regex turned "2026-09-03T16:08" into "…T16:08"
   and quietly destroyed a timestamp the reader needed. A match is only masked
   when it is NOT a date. */

// the leading guard also rejects an id: in ORD-20260903-0016 the run is
// preceded by a hyphen after letters, which a dialled number never is.
const LONG_DIGITS = /(?<![\d.\-A-Za-z/])\+?\d[\d -]{7,}\d(?![\d.\-A-Za-z])/g;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/** True when a digit run is a phone number rather than a date or an id.
 *
 *  The honest limit: a bare nine-digit PO number quoted inside a sentence is
 *  indistinguishable from a mobile, and this masks it. That is the safer way to
 *  be wrong, so it stands — but it is also why this runs over FREE TEXT ONLY
 *  (notes, warnings, vendor and driver names) and never over an identifier
 *  field like a lorry plate, an order number or a PO, which pages render raw. */
function looksLikeAPhone(run: string): boolean {
  const trimmed = run.trim();
  if (ISO_DATE.test(trimmed)) return false;
  const digits = trimmed.replace(/\D/g, "");
  // a run this long that is not a date is a number somebody could ring
  return digits.length >= 8 && digits.length <= 15;
}

export function maskDigits(text: string | null | undefined): string {
  if (!text) return "";
  return text.replace(LONG_DIGITS, (m) => (looksLikeAPhone(m) ? "…" : m));
}

/** A driver / contact name with any phone number taken out of it. */
export const safeName = (s: string | null | undefined) => maskDigits(s) || "—";

/* ───────────────────── demand: the three channels ─────────────────────
   Mark 2's triple tag, kept: channel, docnum prefix and the customer string all
   have to agree before a row is treated as a real order. */

export type Channel = "forecast" | "ecom" | "oms";

export function channelOf(row: Pick<OrderRow, "channel" | "docnum" | "customer"> | DispatchRow): Channel {
  const ch = (row.channel || "").toUpperCase();
  const doc = (row.docnum || "").toUpperCase();
  if (ch === "FORECAST" || doc.startsWith("FCST-") || (row.customer || "").includes("forecast")) return "forecast";
  if (ch === "ECOM" || ch === "ECOM-PO" || doc.startsWith("PO")) return "ecom";
  return "oms";
}

export const isForecast = (row: { assumed?: boolean; channel?: string; docnum?: string; customer?: string }) =>
  row.assumed === true || channelOf(row as OrderRow) === "forecast";

/** Wording and colour per channel — kept in one place so every page agrees. */
export const CHANNEL: Record<Channel, { label: string; short: string; cls: string; dot: string; why: string }> = {
  oms: {
    label: "Ordered — shops and distributors",
    short: "OMS",
    cls: "bg-emerald-500/10 text-emerald-200 border-emerald-500/25",
    dot: "bg-emerald-400",
    why: "A real order on the live order book (OMS).",
  },
  ecom: {
    label: "Ordered — online platforms",
    short: "ECOM-PO",
    cls: "bg-sky-500/10 text-sky-200 border-sky-500/25",
    dot: "bg-sky-400",
    why: "A real, dated purchase order from an online platform.",
  },
  forecast: {
    label: "Expected — nobody has ordered it",
    short: "FORECAST",
    cls: "bg-violet-500/10 text-violet-200 border-violet-500/25",
    dot: "bg-violet-400",
    why: "This month's target spread into the month. No customer has ordered it.",
  },
};

/* ───────────────────── the persistent (non-live) badges ─────────────────
   Five inputs on this site are not live, and each carries its badge wherever it
   appears. Every sentence is read from the data, never typed here. */

export type Persist = { label: string; note: string };

export const P = {
  /** Tank litres — a person walks the yard with a dipstick, once a day. */
  tankDip: (readingNote?: string | null, ruleNote?: string | null): Persist => ({
    label: "HAND-READ DAILY",
    note: readingNote || ruleNote || "read by hand, not by a meter",
  }),
  /** Ecom targets — carried from an earlier month, not this month's. */
  targetsCarried: (carriedFrom?: string | null): Persist => ({
    label: "CARRIED FORWARD",
    note: carriedFrom
      ? `this month's target sheet has not been loaded — these are the ${carriedFrom} numbers, carried forward`
      : "carried forward from an earlier month, not this month's sheet",
  }),
  /** The invoice→truck lag — measured once, not re-measured each cycle. */
  lagStatic: (caveat?: string | null): Persist => ({
    label: "MEASURED ONCE",
    note: caveat || "measured once off the gate log and carried — not re-measured every cycle",
  }),
  /** The godown limit — Daman's own capacity sheet of 29 Aug 2026. He ruled on
   *  2026-09-04 that it IS the limit ("this is correct, no guess now"), so it is the
   *  one persistent input on this site that is a declared fact rather than an
   *  estimate: it is badged YOUR LIMIT, and it is never called a guess anywhere.
   *  The litres come from the data, as everything on this site does. */
  ceiling: (source?: string | null): Persist => ({
    label: "YOUR LIMIT",
    note: source || "Daman's capacity sheet, 29 Aug 2026. A declared limit, not a measurement estimate.",
  }),
  /** A counter that has been adding up since the system went in. */
  allTime: (scopeNote?: string | null): Persist => ({
    label: "ALL-TIME",
    note: scopeNote || "counted since the system went in — not today's, and not this month's",
  }),
  /** Packaging counted out of rooms that have not moved this cycle. */
  nonMoving: (note?: string | null): Persist => ({
    label: "NOT MOVING",
    note: note || "counted in rooms that have not moved — it may not all be usable stock",
  }),
  /** A body read on an earlier cycle and carried into this one.
   *
   *  `mode` is the PUBLISHER's word for where the body came from — "live",
   *  "live-partial", "last-good <stamp>", "missing". It was being used as the
   *  note itself, so on the ordinary path (a cached record republished by a
   *  live source) the badge expanded to the single word "live", and on the
   *  others to publisher jargon and a raw timestamp. It picks the sentence
   *  now; it is never shown. */
  carried: (mode?: string | null, fromCache?: boolean): Persist => {
    const m = (mode ?? "").trim();
    if (m.startsWith("last-good"))
      return {
        label: "EARLIER READ",
        note: "the plant's systems did not answer this cycle, so the last reading that did come back is shown",
      };
    if (m === "live-partial")
      return {
        label: "PART-READ",
        note: "part of this reading did not come back this cycle; what did is shown, and anything missing says so",
      };
    if (m === "missing")
      return {
        label: "NOT READ",
        note: "nothing came back for this and there is no earlier reading to fall back on",
      };
    return {
      label: "EARLIER READ",
      note: fromCache
        ? "these are read once an hour, not every few minutes — this one was read on an earlier cycle and carried into this one"
        : "read on an earlier cycle and carried into this one",
    };
  },
} as const;

/* ───────────────────── honesty notes, as the publisher wrote them ─────────
   An earlier version of this function swapped the publisher's field names for
   friendlier words. It changed the MEANING: a warning that named two different
   opening fields came out as "the opening count and the opening count", which
   reads as a contradiction the publisher never wrote. The publisher's sentences
   ship verbatim now; the only thing taken out of them is a phone number. */

export const plainNote = (s: string): string => maskDigits(s);
