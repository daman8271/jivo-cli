// Field names as the publisher actually emits them.
//
// TWO layers, and they are never mixed:
//   NOW      state.json          — live/collect.py, every ~3 minutes
//   FORWARD  plan/<file>.json    — live/gen_live.py, re-planned from that NOW
//
// Everything here is deliberately loose: a key that is absent means "that call
// did not come back this cycle" (factory_inbound says so in its own notes), and
// it NEVER means zero. So optional and `| null` are load-bearing — a component
// that reads one of these must decide out loud what to show when it is missing.

/* ─────────────────────────── NOW — state.json ─────────────────────────── */

export type SourceEnvelope = {
  ok: boolean;
  fetched_at: string | null;
  server_at: string | null;
  error: string | null;
  seconds?: number;
  cadence?: string;
  has_data?: boolean;
  last_good_at?: string | null;
  last_good_age_s?: number | null;
};

export type StateJson = {
  collected_at: string;
  completed_at?: string;
  cycle_seconds?: number;
  cadence?: { heavy?: boolean; hourly?: boolean; run?: number };
  sources: Record<string, SourceEnvelope>;
  warnings?: string[];
  ecom?: EcomNow;
  exim?: EximNow;
  factory_dispatch?: DispatchNow;
  factory_history?: HistoryNow;
  factory_inbound?: InboundNow;
  factory_production?: ProductionNow;
  oms?: OmsNow;
};

/** The name of an adapter inside state.json. */
export type StateSourceKey =
  | "ecom"
  | "exim"
  | "factory_dispatch"
  | "factory_history"
  | "factory_inbound"
  | "factory_production"
  | "oms";

/* ── the days already gone this month, as the adapter publishes them ──
   factory_history reads one record per elapsed day off ji.jivo.in. It is hourly
   and it caches settled days, so `read_at` is its own stamp and is usually older
   than state.json's collected_at — say so wherever it is rendered.

   EVERY figure is `| null` on purpose: a day a system did not answer for reads
   UNKNOWN, never 0, because 0 is a plant that stood still. */
export type HistoryNowDay = {
  date: string;
  day_of_month: number;
  weekday: string;
  working: boolean;
  made_mes_l: number | null;
  made_mes_cases: number | null;
  runs: number | null;
  open_segments: number | null;
  made_booked_l: number | null;
  made_booked_pcs: number | null;
  booked_receipts: number | null;
  booked_unparsed_pcs: number | null;
  booked_truncated?: boolean | null;
  /** pieces per item code — Phase 2's input; the site does not render it */
  booked_by_item?: Record<string, number> | null;
  billed_out_l: number | null;
  billed_out_pcs: number | null;
  billed_lines: number | null;
  billed_unparsed_pcs: number | null;
  dispatched_oil_l: number | null;
  dispatched_all_l: number | null;
  trucks_oil: number | null;
  trucks_all: number | null;
  rows_oil: number | null;
  bills_oil: number | null;
  /** the gate split per book — state.json only, never in history.json */
  by_company?: Record<string, { litres?: number; rows?: number; bills?: number; trucks?: number }> | null;
  settled?: boolean;
  complete?: boolean;
  read_at?: string | null;
  notes?: string[];
};

export type HistoryNow = {
  company?: string;
  month?: string;
  through?: string;
  today?: string;
  status?: "complete" | "partial" | "unavailable" | string;
  from_cache?: boolean;
  read_at?: string;
  days?: HistoryNowDay[];
  missing_dates?: string[];
  undated_dispatched_rows?: number;
  basis?: Record<string, string>;
  notes?: string[];
};

export type RunNow = {
  line: string;
  line_id?: number;
  run_id: number;
  sku_code: string;
  sku: string;
  cases: number;
  litres: number;
  litres_basis?: string;
  started?: string | null;
  live?: boolean;
  live_status?: string | null;
  running_minutes?: number | null;
  breakdown_minutes?: number | null;
  rated_speed?: number | null;
  required_qty?: number | null;
  supervisor?: string | null;
  /** present on recent_runs rows, absent on running_now */
  date?: string | null;
  status?: string | null;
};

export type LineToday = {
  line_id?: number;
  runs: number;
  cases: number;
  litres: number;
  skus?: { sku_code: string; sku: string; cases: number; litres: number }[];
  live?: boolean;
  running_minutes?: number | null;
  breakdown_minutes?: number | null;
};

export type ProductionNow = {
  company?: string;
  date?: string;
  date_yesterday?: string;
  running_now?: RunNow[];
  runs_today?: RunNow[];
  made_today_l?: number | null;
  made_yesterday_l?: number | null;
  made_today_cases?: number | null;
  made_yesterday_cases?: number | null;
  mes_coverage_note?: string;
  by_line_today?: Record<string, LineToday>;
  booked_today?: {
    receipts?: number;
    pcs?: number;
    litres?: number;
    value_inr?: number;
    note?: string;
  } | null;
  warehouse_flow_today?: {
    opening_pcs?: number;
    in_pcs?: number;
    out_pcs?: number;
    closing_pcs?: number;
    total_value_inr?: number;
    entries?: number;
  } | null;
  recent_runs?: RunNow[];
  notes?: string[];
};

export type DispatchNow = {
  as_of_date?: string;
  companies?: string[];
  invoiced_not_dispatched?: {
    bills?: number | null;
    litres?: number | null;
    value_inr?: number | null;
    basis?: string | null;
    source?: string | null;
    by_status?: Record<string, { bills?: number; litres?: number; value_inr?: number }>;
    by_company?: Record<string, { bills?: number; litres?: number; value_inr?: number }>;
    by_warehouse?: Record<string, { bills?: number; litres?: number; value_inr?: number }>;
    godown_rooms_only?: Record<string, { bills?: number; litres?: number; value_inr?: number }>;
    aged_over_7d?: Record<string, number> | { bills?: number; litres?: number };
  } | null;
  dispatched_today?: {
    trucks?: number;
    rows?: number;
    bills?: number;
    litres?: number;
    boxes?: number;
    value_inr?: number;
    /** per SAP company — NEVER summed into one headline (spec: company scoping) */
    by_company?: Record<string, { trucks?: number; bills?: number; litres?: number; value_inr?: number }>;
    source?: string;
  } | null;
  at_gate_today?: {
    rows?: number;
    by_status?: Record<string, number>;
    loaded_not_gone_litres?: number | null;
    loaded_not_gone_basis?: string | null;
    latest_event_at?: string | null;
  } | null;
  trucks_inside?: {
    vehicle_no: string;
    company?: string;
    companies?: string[];
    in_time?: string | null;
    gate_in_date?: string | null;
    bill_count?: number;
  }[];
  trucks_inside_count?: number | null;
  flow_stages?: Record<string, number>;
  /** Oil-only slice the adapter computes itself. */
  oil?: {
    company?: string;
    dispatched_today_litres?: number | null;
    dispatched_today_trucks?: number | null;
    undispatched_litres?: number | null;
    undispatched_bills?: number | null;
    trucks_inside?: number | null;
  } | null;
  lag_note?: {
    median_days?: number;
    mean_days?: number;
    p90_days?: number;
    max_days?: number;
    rows?: number;
    measured_window?: string;
    measured_on?: string;
    method?: string;
    caveat?: string;
    /** true => a one-off measurement carried forward, not re-measured each cycle */
    static?: boolean;
  } | null;
  warnings?: string[];
};

export type InboundEntry = {
  entry_no?: string;
  time?: string | null;
  time_ist?: string | null;
  date_ist?: string | null;
  phase?: string | null;
  status?: string | null;
  status_label?: string | null;
  supplier?: string | null;
  po_numbers?: string[];
  items?: { code?: string; name?: string; received_qty?: number; uom?: string }[];
};

export type InboundNow = {
  company?: string;
  as_of_ist?: string;
  today_ist?: string;
  board_counts?: Record<string, number>;
  arrived_today?: InboundEntry[];
  arrived_today_count?: number | null;
  arrived_today_usable_pcs?: number | null;
  arrived_today_usable_mt?: number | null;
  arrived_today_pending_pcs?: number | null;
  arrived_today_pending_mt?: number | null;
  in_qc?: InboundEntry[];
  in_qc_count?: number | null;
  bulk_oil_pending_mt?: number | null;
  bulk_oil_pending_lines?: number | null;
  bulk_oil_oldest_wait_hours?: number | null;
  packaging_pending_pcs?: number | null;
  /** ALL-TIME, company-wide QC scoreboard — the adapter says so in notes.qc_counts_scope */
  qc_counts?: Record<string, number>;
  trucks_open?: {
    arrival_no?: string;
    vehicle_no?: string;
    /** carries a phone number in the live feed — never render raw, see maskDigits() */
    driver_name?: string | null;
    status?: string | null;
    direction?: string | null;
    companies?: string[];
    gate_in_at?: string | null;
    age_hours?: number | null;
  }[];
  trucks_open_count?: number | null;
  notes?: Record<string, string>;
};

export type EximNow = {
  tanks?: {
    total_l?: number;
    capacity_l?: number;
    utilisation_pct?: number;
    free_headroom_l?: number;
    tank_count?: number;
    oil_count?: number;
    by_oil?: { oil: string; code: string; litres: number; capacity_l?: number; tank_count?: number }[];
    by_oil_note?: string;
    /** "manual daily dip reading … NOT a live sensor" — persistent badge */
    reading_note?: string;
    /** the newest per-tank updated_at (IST) — when a human LAST entered a dip; the block's own age */
    reading_at?: string | null;
    reading_oldest_at?: string | null;
    reading_age_hours?: number | null;
    tanks_updated_today?: number | null;
  } | null;
  inbound?: {
    on_the_way?: EximTruck[];
    under_loading?: EximTruck[];
    in_contract?: EximTruck[];
    totals_l?: Record<string, number>;
    kg_per_litre?: number;
    latest_row_created_at?: string | null;
  } | null;
  open_bulk_pos?: {
    po_number?: string;
    po_date?: string;
    rm_code?: string;
    name?: string;
    vendor?: string;
    contract_qty?: number;
    load_qty?: number;
    status?: string;
  }[];
  open_bulk_pos_note?: string;
  pos_line_count?: number | null;
  plan_version?: {
    version?: number;
    month?: string;
    title?: string;
    uploaded_at?: string;
    row_count?: number;
    grand_total?: number;
    commodity_total?: number;
    premium_total?: number;
    ecom_total?: number;
  } | null;
  freshness?: Record<string, string>;
};

export type EximTruck = {
  id?: number;
  vendor?: string;
  oil?: string;
  rm_code?: string;
  litres?: number;
  kg?: number;
  eta?: string | null;
  days_late?: number | null;
  vehicle?: string | null;
  location?: string | null;
};

export type EcomNow = {
  dated_demand?: { date: string; litres: number; platform: string }[];
  dated_demand_in_month_l?: number | null;
  dated_demand_overdue_l?: number | null;
  dated_demand_total_l?: number | null;
  open_by_platform?: Record<string, { lines?: number; litres?: number; pos?: number }>;
  open_by_platform_source?: string;
  open_qcomm_l?: number | null;
  open_amazon_sep_l?: number | null;
  open_amazon_l?: number | null;
  open_amazon_pos?: number | null;
  open_expired_l?: number | null;
  open_qcomm_expired_l?: number | null;
  open_qcomm_expired_pos?: number | null;
  open_qcomm_no_expiry_l?: number | null;
  expiry_basis?: string | null;
  open_total_l?: number | null;
  open_value_ex_gst_inr?: number | null;
  open_value_ex_gst_qcomm_inr?: number | null;
  open_value_ex_gst_total_inr?: number | null;
  open_value_basis?: string | null;
  open_backlog_amazon_l?: number | null;
  open_backlog_amazon_pos?: number | null;
  open_amazon_all_l?: number | null;
  open_amazon_all_pos?: number | null;
  open_backlog_basis?: string | null;
  mtd_by_platform?: Record<string, number>;
  mtd_delivered_l?: number | null;
  mtd_complete?: boolean;
  mtd_missing_sources?: string[];
  amazon?: Record<string, number | string>;
  /** monthly targets — `carried_from` says which month they were carried from */
  targets?: {
    carried_from?: string | null;
    carried_rows_pct?: number | null;
    commodity_l?: number | null;
    premium_l?: number | null;
    total_l?: number | null;
    drr_l_per_day?: number | null;
    require_drr_l_per_day?: number | null;
    open_pending_commodity_l?: number | null;
    open_pending_premium_l?: number | null;
  } | null;
  warnings?: string[];
  month?: number;
  year?: number;
};

export type OmsNow = {
  stale?: boolean;
  orders_recent?: {
    id: number;
    order_number: string;
    customer?: string;
    company?: string;
    created?: string;
    delivery_date?: string | null;
    status_code?: string;
    status_name?: string;
    is_terminal?: boolean;
    ltrs?: number | null;
    amount?: number | null;
  }[];
  open_by_status?: Record<
    string,
    {
      status_name?: string;
      count?: number;
      litres?: number;
      litres_by_category?: Record<string, number>;
      amount_inr?: number;
      terminal?: boolean;
    }
  >;
  open_total?: {
    count?: number;
    litres?: number;
    litres_by_category?: Record<string, number>;
    amount_inr?: number;
    amount_inr_ex_outliers?: number;
    litres_ex_outliers?: number;
    rs_per_l?: number | null;
    rs_per_l_ex_outliers?: number | null;
    headline_note?: string;
  } | null;
  company_scope?: {
    expected?: string;
    by_company?: Record<string, number>;
    clean?: boolean;
    foreign_orders?: number;
    unknown_orders?: number;
    note?: string;
  } | null;
  price_outliers?: {
    order_number?: string;
    customer?: string;
    code?: string;
    name?: string;
    inr_per_litre?: number;
    ltrs?: number;
    total_inr?: number;
  }[];
  counts?: Record<string, number>;
  note?: string;
};

/* ───────────────────────── FORWARD — plan/*.json ───────────────────────── */

export type PlanMeta = {
  collected_at: string;
  as_of?: string;
  horizon?: [string, string] | string[];
  rolling?: boolean;
  forward?: boolean;
  generated?: string;
  generated_by?: string;
  month?: string;
  frozen?: string;
  replanned_days?: number;
  working_days_left?: number;
  state_completed_at?: string;
  forward_rule?: string;
};

export type Overview = {
  meta: PlanMeta;
  totals: {
    made_l: number;
    value_rs: number;
    shipped_l: number;
    oil_used_l: number;
    days: number;
    working_days: number;
    runs: number;
    flushes: number;
    bought_lines?: number;
    events?: number;
    util_median?: number;
    peak_day?: { date: string; made_l: number };
    oil_changes?: number | null;
  };
  plan: {
    litres: number;
    skus: number;
    made_vs_plan_pct: number;
    source?: string;
    /** how many of those SKUs are on the month's sheet … */
    sheet_skus?: number;
    /** … and how many are only there because the trade keeps buying them */
    expected_only_skus?: number;
  };
  demand: {
    rows: number;
    real_rows: number;
    forecast_rows: number;
    real_pieces: number;
    forecast_pieces: number;
    real_value_rs: number;
    forecast_value_rs: number;
    forecast_share_pieces_pct: number;
    forecast_share_value_pct: number;
    forecast_share_litres_pct: number;
    channels?: Record<string, number>;
    sources?: Record<string, number>;
    note?: string;
  };
  opening: {
    fg_litres: number;
    fg_plan_l?: number;
    fg_other_l?: number;
    oil_l: number;
    oil_l_definition?: string;
    packaging_pieces: number;
    /** present only when the publisher computes it — badge it when it is */
    packaging_in_non_moving_rooms_pcs?: number | null;
    inbound_oil_l?: number;
    standing_l: number;
    standing_assumed?: boolean;
    standing_measured?: boolean;
    standing_note?: string;
    at_zero_count?: number;
    physical_l?: number;
    physical_pct?: number;
  };
  storage: {
    ceiling_l: number;
    peak_l: number;
    /** Daman's declared limit (2026-09-04), never a guess of ours. */
    ceiling_declared: boolean;
    ceiling_declared_by?: string;
    invoice_truck_lag_days: number;
    days_ge_95: number;
    days_ge_100: string[];
    throttle_events?: number;
    pct_at_open?: number;
    /** which company's gate the invoice-to-truck wait was measured on. The plan
        runs on JIVO Oil's own; the merged three-book figure rides beside it. */
    invoice_truck_lag_book?: string | null;
  };
  /** B20 — the godown limit, and what it did to THIS run. It caps every run to the
      room left in the godown; it is the biggest single hand on the month's sheet and
      it used to be invisible. Never a claim: every field is counted off the days the
      engine just produced. */
  storage_cap?: {
    rule: string;
    in_effect: boolean;
    ceiling_l: number;
    what_it_does: string;
    /** days the cap actually stopped or shortened work — the number to quote */
    days_it_bit: number;
    days_it_bit_dates?: string[];
    /** days that OPENED with the godown nearly full. A day that opens with room and
        fills it is not in here, which is why it is the smaller of the two. */
    days_throttled: number;
    days_throttled_say?: string;
    working_days: number;
    days_throttled_dates?: string[];
    runs_cut_short?: number;
    litres_cut_off_runs_it_allowed?: number;
    products_stopped_outright?: number;
    products_stopped_codes?: string[];
    days_at_zero_headroom?: number;
    month_made_l: number;
    month_sheet_l: number;
    month_made_pct_of_sheet: number | null;
    products_on_the_sheet: number;
    products_never_made: number;
    products_never_made_top?: { code: string; sku: string; month_target_litres: number }[];
    why_it_is_a_build_choice: string;
    headline: string;
  };
  day1_blocked?: {
    attempts: number;
    products: number;
    by_binder_class?: Record<string, { attempts: number; products: number }>;
    top_binder?: { code: string; name: string; kind: string; attempts: number; products: number } | null;
    note?: string;
  };
  august?: { sim_made_l: number; actual_made_l: number; delta_pct: number; note?: string;
    measured_on?: string; reproducible?: boolean; changed_since_measured?: string[];
    source?: string };
  materials_mini?: {
    components: number;
    under_100_cover: number;
    must_order_week1: number;
    already_late: number;
    zero_literal_items?: number;
    zero_literal_value_rs?: number;
    zero_august_rule_items?: number;
    zero_august_rule_value_rs?: number;
  };
  loops_mini?: { chains: number; resolved: number; ran_after_unblock: number };
  unproducible?: Unproducible[];

  /* ───────────────────────────── Mark 4 ─────────────────────────────
     Everything below arrives only from a rulebook run. Each is optional, and
     a component that reads one must render nothing rather than a zero when it
     is absent — a Mark 3 body is still a valid body.

     `warnings` is deliberately NOT here: in rulebook mode the overview stops
     carrying them and honesty.json is the one place they live (Footer already
     reads them from there). Do not put them back. */

  rulebook?: {
    version: string;
    written?: string;
    owner?: string;
    applied?: boolean;
    hours_per_session?: number | null;
    night_sessions?: number | null;
  };
  /** which day the plan calls day 1, in its own words */
  day1?: { date: string; weekday?: string; working?: boolean };
  /** the day in rupees, against the plant's own floor and target */
  money?: {
    today_plan_rs: number;
    today_booked_rs?: number | null;
    today_booked_pieces?: number | null;
    mtd_made_rs?: number | null;
    mtd_days?: number | null;
    target_rs_per_day?: number | null;
    floor_rs_per_day?: number | null;
    on_target_today?: boolean;
    /** THE MONTH against the daily floor and the daily target. `on_target_today` is a
        statement about ONE day, and day 1 is the one day the godown limit does not
        bite — a green tick there was sitting over a month that misses the floor on
        almost every working day it has left (R16/F5). */
    month?: {
      sheet_rs_at_the_same_prices: number;
      sheet_rows_priced_by_default?: number;
      default_rs_per_l?: number | null;
      plan_pct_of_sheet_rs: number | null;
      plan_rs: number;
      working_days: number;
      days_above_floor: number;
      days_below_floor: number;
      days_on_target: number;
      target_rs_if_every_working_day_hit_it: number | null;
      pct_of_a_month_of_targets: number | null;
      worst_day: string | null;
      note: string;
    };
    above_floor_today?: boolean;
    mtd_by_basis?: Record<string, number>;
    basis?: string;
    booked_basis?: string;
    mtd_basis?: string;
  };
  /** one row per machine for TODAY — the overview is line by line in Mark 4 */
  lines_today?: {
    line: string;
    night?: boolean;
    hours_planned: number;
    hours_available: number;
    runs: number;
    pieces: number;
    litres: number;
    value_rs: number;
    product_changes?: number;
    products?: {
      code: string;
      sku: string;
      litres: number;
      pieces: number;
      hours: number;
      family?: string | null;
      pref?: number | null;
      po_backed?: boolean;
    }[];
  }[];
  night_line?: NightLine | null;
  /** the dispatch HEADLINE in Mark 4: days of pendency and how long a bill waits.
   *  `trucks` is not in this object at all — what left today is not the headline. */
  dispatch?: {
    open_l_all_books?: number | null;
    open_bills?: number | null;
    oil_pile_l?: number | null;
    pendency_days_all?: number | null;
    pendency_days_oil?: number | null;
    trailing_days?: number | null;
    basis?: string;
    basis_missing?: string | null;
    lag_median_days?: number | null;
    lag_p90_days?: number | null;
    lag_max_days?: number | null;
    lag_mean_days?: number | null;
    lag_rows?: number | null;
    lag_window?: string | null;
    lag_measured_on?: string | null;
    /** false = re-measured every day; true = one measurement carried forward */
    lag_static?: boolean;
    lag_basis?: string;
    lag_caveat?: string;
    lag_by_company?: Record<string, { median_days?: number; p90_days?: number; max_days?: number; mean_days?: number; n?: number }>;
    /** WHICH BOOK the lag above is. The gate is one gate carrying three companies and
        this plan makes Oil, so the engine is fed Oil's own wait; the merged all-books
        figure is published beside it and never instead of it. */
    lag_book?: string | null;
    lag_book_say?: string | null;
    lag_all_books_median_days?: number | null;
    lag_all_books_p90_days?: number | null;
    lag_all_books_rows?: number | null;
    headline?: string;
  };
  /** what the plan could not make, and the reason in the planner's own words */
  stuck?: {
    /** `want_*` is what the planner tried to fill TODAY. `month_target_*` is that
        product's whole line on the month's sheet. Two different counts — the data
        names them apart and `litres_note` says never to add them. */
    material?: { code: string; sku: string; want_pieces?: number; want_litres?: number;
      month_target_pieces?: number; month_target_litres?: number;
      short_of?: { code: string; name: string }[]; ordered?: boolean }[];
    /** B20 — the machine had the hours and the material was there; the godown had
        nowhere to put the output. A different reason needing a different answer:
        no purchase order fixes it. */
    storage?: { code: string; sku: string; want_pieces?: number; want_litres?: number;
      month_target_pieces?: number; month_target_litres?: number;
      ordered?: boolean; machines_with_room?: string[] }[];
    no_order?: { code: string; sku: string; month_target_pieces?: number; month_target_litres?: number;
      ordered?: boolean; expected_only?: boolean; ordered_later?: boolean }[];
    no_line_time?: { code: string; sku: string; month_target_pieces?: number; month_target_litres?: number;
      ordered?: boolean; machines_with_room?: string[] }[];
    manual?: ManualFill[];
    /** true when the godown was too full to start anything at all */
    godown_full_today?: boolean;
    definitions?: Record<string, string>;
    /** gen's own heading for each bucket — it is written from the same rows as the
        definition, so a hand-typed heading cannot contradict the sentence under it */
    headings?: Record<string, string>;
    counts?: Record<string, number>;
    /** hours each machine still had free on day 1 */
    hours_free_today?: Record<string, number>;
    litres_note?: string;
  };
  /** the drums: filled by hand, never scheduled on a machine */
  manual_fill?: ManualFill[];
  manual_fill_note?: string;
  expected_orders?: {
    present?: boolean;
    used?: boolean;
    window?: { from?: string; to?: string; months?: number };
    months?: number;
    share_of_demand_pct?: number | null;
    fallback_reason?: string | null;
    fetched_at?: string | null;
    source?: string;
    note?: string;
    age_days?: number | null;
  };
  /** the warnings live in honesty.json — this only says how many and where */
  warnings_count?: number;
  warnings_where?: string;
  sources?: Record<string, { source?: string; fetched_at?: string | null; server_at?: string | null; mode?: string; note?: string }>;
};

/** A product that is filled by hand off a machine — the drums (R14). */
export type ManualFill = {
  code: string;
  sku: string;
  litres_per_piece?: number;
  plan_pieces?: number;
  plan_litres?: number;
  display?: string;
};

export type Unproducible = {
  code: string;
  sku: string;
  pack_type: string;
  litres_per_piece: number;
  plan_pieces: number;
  plan_litres: number;
  slot_needed: string;
  reason: string;
  value_est_rs?: number;
  value_est_derived?: boolean;
};

export type SpineDay = {
  n: number;
  date: string;
  weekday: string;
  working: boolean;
  made_l: number;
  value_rs: number;
  shipped_l: number;
  util: number;
  storage_pct: number;
  headroom_l: number;
  runs: number;
  flushes: number;
  /** ATTEMPTS stopped that day — one product tried on four machines is four rows.
      Never render this as a count of products; see `blocked_products`. */
  blocked: number;
  /** how many DIFFERENT products could not start that day — the one to show */
  blocked_products?: number;
  /** gen's own words for which of the two is which */
  blocked_label?: string;
  unblocked: number;
  bought: number;
  oil_used_l: number;
  orders: {
    real_rows: number;
    real_pieces: number;
    real_value_rs: number;
    forecast_rows: number;
    forecast_pieces: number;
    forecast_value_rs: number;
    forecast_assumed?: boolean;
  };
  dispatched: { real_l: number; forecast_l: number };
  received_count?: number;
  /** Mark 4: the line given the second session that day, by name */
  night_line?: string | null;
  events?: Record<string, number>;
  book?: PlanBook;
  open_real_l_computed?: number;
  open_real_l_note?: string;
  collected_at?: string;
};

export type PlanBook = {
  plan_left_l: number;
  po_cumulative_value_rs: number;
  po_cumulative_value_label?: string;
  po_open_l_raw: number;
  po_open_l_raw_label?: string;
  forecast_open_l: number;
};

export type PlanRun = {
  line: string;
  code: string;
  sku: string;
  head?: string;
  oil?: string | null;
  pieces: number;
  litres: number;
  hours: number;
  flush_min: number;
  realise?: number;
  value?: number;
  po_backed?: boolean;
  /* Mark 4. The rulebook decides WHICH machine a run may open on, so a run now
     carries the pack slot, the bottle family and which choice of line this was.
     All optional: an older plan file has none of them and must still render. */
  slot?: string;
  family?: string | null;
  /** 1 = its first-choice line, 2 = only because the first choice was full, 3 = last resort */
  pref?: number | null;
  /** true when this run is on the one machine allowed a second session that day */
  night?: boolean;
  fills?: number;
  containers?: number;
};

export type OrderRow = {
  docnum: string;
  customer: string;
  channel: string;
  code: string;
  sku: string;
  pieces: number;
  value: number;
  assumed?: boolean;
};

export type DispatchRow = {
  docnum: string;
  customer: string;
  channel: string;
  sku: string;
  pieces: number;
  litres: number;
  assumed?: boolean;
};

export type DayDetail = {
  meta: PlanMeta & { n: number; date: string };
  n: number;
  date: string;
  weekday: string;
  working: boolean;
  made_litres: number;
  made_value_rs: number;
  shipped_litres: number;
  oil_used_l: number;
  /** BOM-relevant oils only — NOT the same series as overview.opening.oil_l */
  oil_on_hand_l: number;
  line_util: number;
  line_hours: Record<string, number>;
  /** Mark 4: the hours each line was ALLOWED that day — 10, or 20 for the night line */
  line_hours_max?: Record<string, number>;
  /** Mark 4: the one machine given a second session, and why it was picked */
  night_line?: NightLine | null;
  /** Mark 4: how many times each line changed product that day */
  product_changes?: Record<string, number>;
  flushes: number;
  storage: {
    physical_l: number;
    ceiling_l: number;
    peak_l: number;
    pct: number;
    fg_in_godown_l: number;
    invoiced_not_trucked_l: number;
    headroom_l: number;
  };
  storage_ceiling_declared?: boolean;
  book?: PlanBook;
  open_real_l_computed?: number;
  runs: PlanRun[];
  /** one row per ATTEMPT — the same product appears once per machine it was tried on */
  /** one row per ATTEMPT: the planner tries a product on every machine that could
      fill it, on every pass of the day, so the SAME (product, binder) pair appears
      several times. Render them de-duplicated — see `blocked_label`. `reason` is
      "material" (a bottle ran out) or "storage" (B20: the godown had no room). */
  blocked: { code: string; sku: string; want: number; binder: string; binder_name: string;
    reason?: string }[];
  /** how many DIFFERENT products those rows are */
  blocked_products?: number;
  blocked_label?: string;
  unblocked: { code: string; name?: string }[];
  waiting_on: { code: string; name: string; since: string }[];
  received: { code: string; name: string; qty: number; kind: string }[];
  orders_real: OrderRow[];
  orders_forecast: OrderRow[];
  dispatched_real: DispatchRow[];
  dispatched_forecast: DispatchRow[];
  bought: { code: string; name: string; qty: number; uom: string; lands: string }[];
  events: { day: string; kind: string; code?: string; name?: string; qty?: number; lands?: string; lead?: number }[];
  honesty?: { measured: string[]; assumed: string[] };
};

export type StorageData = {
  meta: PlanMeta;
  /** `declared` — Daman's own capacity sheet, ruled a fact on 2026-09-04. Not `assumed`. */
  ceiling: {
    working_l: number;
    peak_l: number;
    declared: boolean;
    declared_by?: string;
    source?: string;
    basis?: string;
  };
  standing_at_open: { litres: number; assumed?: boolean; optimistic?: boolean; note?: string };
  at_open: {
    physical_l: number;
    fg_l: number;
    billed_not_gone_l: number;
    pct: number;
    over_ceiling?: boolean;
    measured?: boolean;
    assumed?: boolean;
    clears_on_day_n?: number | null;
    clears_note?: string;
    note?: string;
  };
  invoice_truck_lag_days: number;
  invoice_truck_note?: string;
  series: {
    n: number;
    date: string;
    working: boolean;
    physical_l: number;
    pct: number;
    fg_in_godown_l: number;
    invoiced_not_trucked_l: number;
    headroom_l: number;
    invoiced_l: number;
    trucked_out_l: number;
  }[];
  days_ge_95?: number;
  days_ge_100?: string[];
  throttles?: { day: string; pct_start_of_day: number; headroom_l: number }[];
  biggest_fall?: { n: number; date: string; fall_l: number; trucked_out_l: number; made_l: number; note?: string } | null;
  biggest_invoicing_day?: { n: number; date: string; invoiced_l: number; trucked_out_that_day_l: number } | null;
  biggest_trucked_day?: { n: number; date: string; trucked_out_l: number } | null;
};

export type MaterialRow = {
  code: string;
  name: string;
  kind: string;
  uom: string;
  need: number;
  on_hand: number;
  on_order: number;
  cover_pct: number;
  short: number;
  at_zero: string;
  skus_blocked: number;
  litres_at_risk: number;
  value_at_risk: number;
  lead_days: number;
  first_short_day: string | null;
  order_by: string | null;
  order_basis?: string;
  status: string;
  skus?: string;
  late?: boolean;
  zero_literal?: boolean;
  zero_august_rule?: boolean;
};

export type MaterialsData = {
  meta: PlanMeta;
  basis?: string;
  components_in_plan: number;
  under_100_cover: number;
  must_order_week1: number;
  already_late: number;
  lead_days: { oil: number; packaging: number };
  zero_definitions?: Record<string, unknown>;
  rows: MaterialRow[];
  opening_at_zero?: { code: string; name: string; kind: string; on_order: number }[];
  unproducible?: Unproducible[];
  unproducible_note?: string;
};

export type LoopChain = {
  code: string;
  name: string;
  kind: string;
  ordered_day: string;
  qty: number;
  lands: string;
  lead_days: number;
  fg_codes_blocked?: string[];
  unblocked_day?: string | null;
  waited_days?: number | null;
  first_run_after_unblock?: { day: string; code: string; sku: string } | null;
};

export type LoopsData = {
  meta: PlanMeta;
  note?: string;
  chains: LoopChain[];
  ordered_events?: number;
  unblocked_events?: number;
  resolved_chains?: number;
  ran_after_unblock?: number;
  landed_no_run?: number;
  resolved_note?: string;
};

/** How the rulebook arrived at the speed the plan uses for one line + pack.
 *  Mark 3 had three words; Mark 4 has five, and they are not interchangeable:
 *    capped   80% of the listed speed, then held to the best August sustained run
 *    rated    80% of the listed speed — August had no run long enough to hold it to
 *    typical  the middle August run — the app has no listed speed for this pack
 *    carried  a speed carried from the last plan, cut to 80% — nothing else exists
 *    derived  taken from another pack on the same machine — never timed on its own
 */
export type SpeedBasis = "capped" | "rated" | "typical" | "carried" | "derived" | string;

export type LineSlot = {
  slot: string;
  stored_rate_per_hr: number;
  /** capped | rated | typical | carried | derived — the honest basis for the speed */
  rate_basis: SpeedBasis;
  rate_basis_raw?: string;
  effective_rate_per_hr: number;
  note?: string;
  /* ── Mark 4 ── every one of these can be absent, and absent is never zero. */
  /** which bottle/pack families may open here, and at which preference (1/2/3) */
  families?: Record<string, number>;
  /** the speed the factory app lists for this machine and pack */
  rated?: number | null;
  rated_basis?: string | null;
  /** the middle August run, and the best one that lasted long enough to count */
  aug_median?: number | null;
  aug_best?: number | null;
  aug_runs?: number;
  aug_runs_sustained?: number;
  /** the speed the plan actually uses */
  planning?: number | null;
  planning_basis?: string | null;
  planning_rule?: {
    kind?: SpeedBasis;
    factor?: number | null;
    rated?: number | null;
    best?: number | null;
    median?: number | null;
    median_sustained?: number | null;
    runs?: number;
    runs_sustained?: number;
    sustained_min_minutes?: number;
    min_runs?: number;
    carried_from?: number | null;
    derived_from?: string[] | null;
  } | null;
  /** the pouch machine runs two sets at once — its own rate, said separately */
  set_of_two_rate_per_hr?: number | null;
  set_of_two_basis?: string | null;
};

/** A pack a line CAN take but has no speed for — a ruling is needed, and the
 *  plan puts nothing there in the meantime. Shown, never dropped. */
export type NoSpeedSlot = {
  slot: string;
  families?: Record<string, number>;
  why: string;
};

export type LineStat = {
  name: string;
  slots: LineSlot[];
  runs: number;
  litres: number;
  pieces: number;
  hours_run: number;
  hours_on_line: number;
  value_rs: number;
  days_active: number;
  flush_minutes: number;
  top_skus?: { sku: string; litres: number }[];
  /* ── Mark 4 ── */
  /** the dates this line is given the second session */
  night_days?: string[];
  /** the hours it is allowed TODAY — 10, or 20 if it has tonight's second session */
  hours_max_today?: number | null;
  no_speed_slots?: NoSpeedSlot[];
};

/** The one machine given a second session, and why it was picked. */
export type NightLine = {
  line: string | null;
  reason?: string;
  po_backed_l_unmade?: number | null;
  hours?: number | null;
  candidates?: { line: string; po_backed_l?: number; other_l?: number }[];
};

export type LinesData = {
  meta: PlanMeta;
  efficiency: number;
  efficiency_note?: string;
  lines: LineStat[];
  total_litres: number;
  total_litres_note?: string;
  measured_slots?: string[];
  measured_from?: string;
  /* ── Mark 4 ── */
  planning_factor?: number | null;
  planning_factor_basis?: string;
  sustained_hours?: number | null;
  night_line_today?: NightLine | null;
  hours_per_session?: number | null;
  rulebook_version?: string;
  rate_basis_words?: string[];
  runs_by_line?: Record<string, number>;
};

export type LabelRule = {
  id: string;
  rule: string;
  [k: string]: unknown;
};

export type HonestyData = {
  meta: PlanMeta;
  forward_rule?: string;
  measured: string[];
  assumed: string[];
  provenance?: Record<
    string,
    { source?: string; fetched_at?: string | null; server_at?: string | null; mode?: string; note?: string }
  >;
  warnings?: string[];
  label_rules: LabelRule[];
  august_calibration?: { sim_made_l: number; actual_made_l: number; delta_pct: number; note?: string;
    measured_on?: string; reproducible?: boolean; changed_since_measured?: string[];
    source?: string };
  not_here?: Record<string, string>;
};

/* ───────────────────── FORWARD — plan/history.json ─────────────────────
   The one file on this site that looks BACKWARDS: what the plant actually did
   on each day between the 1st and yesterday. It is not the plan and it is never
   drawn as part of it.

   Two things a component reading this must respect:
     · a null figure means NOT READ. Draw it as "not read", never as zero.
     · made_mes_l and made_booked_l are the SAME production counted two ways
       (the machine log sees about two-thirds of the plant; the goods receipt is
       the fuller figure). They carry their own labels and are never added. */

export type HistoryDay = {
  date: string;
  day_of_month: number;
  weekday: string;
  working: boolean;
  /** always true — this row is a record, not a plan day */
  happened: true;
  made_mes_l: number | null;
  made_mes_cases: number | null;
  runs: number | null;
  open_segments: number | null;
  made_booked_l: number | null;
  made_booked_pcs: number | null;
  booked_receipts: number | null;
  booked_unparsed_pcs: number | null;
  booked_truncated: boolean;
  billed_out_l: number | null;
  billed_out_pcs: number | null;
  billed_lines: number | null;
  billed_unparsed_pcs: number | null;
  dispatched_oil_l: number | null;
  dispatched_all_l: number | null;
  trucks_oil: number | null;
  trucks_all: number | null;
  rows_oil: number | null;
  bills_oil: number | null;
  /** false = a read behind this day came back short; its figures are a floor */
  complete: boolean;
  /** true = this day is final and will not be read again */
  settled: boolean;
  read_at: string | null;
  notes: string[];
  made_mes_label: string;
  made_booked_label: string;
};

export type HistoryTotals = {
  made_mes_l: number | null;
  made_booked_l: number | null;
  billed_out_l: number | null;
  dispatched_oil_l: number | null;
  dispatched_all_l: number | null;
  runs: number | null;
  days_with_records: number;
  days_not_read: number;
  working_days: number;
  /** how many days went into each sum above — a sum over 3 of 4 days says so */
  covers: Record<string, number>;
};

export type HistoryMeta = PlanMeta & {
  month?: string;
  first?: string;
  /** the last day already gone, or "—" on the 1st of the month */
  through?: string;
  status?: "complete" | "partial" | "unavailable" | string;
  /** how the records reached this file: live, live-partial, last-good …, missing */
  records_mode?: string;
  /** the records' OWN reading time — older than meta.collected_at by design */
  records_read_at?: string | null;
  records_through?: string | null;
  records_from_cache?: boolean;
  source?: { source?: string; fetched_at?: string | null; server_at?: string | null; mode?: string; note?: string } | null;
};

export type HistoryData = {
  meta: HistoryMeta;
  rule: string;
  days: HistoryDay[];
  /** elapsed dates with no record at all — "not read", never a zero day */
  missing_dates: string[];
  /** records dated today or later, dropped rather than refused (midnight straddle) */
  trimmed_dates: string[];
  totals: HistoryTotals;
  basis: Record<string, string>;
  notes: string[];
  unavailable_reason: string | null;
};

/* ─────────────────── FORWARD — plan/assumptions.json ───────────────────
   Mark 4's centrepiece, and the reason the project exists: the plan's own
   answer to "why does it say that". Three separate things, never blended:

     settled        what the plant has RULED. Not ours to change.
     assumed        what the computer filled in for itself because nobody has
                    ruled yet — each one says whether it is in effect THIS run.
     build_choices  where the rulebook was silent and this build had to pick.

   Plus the speeds, the eligibility matrix, where the sheet disagrees with the
   recipe, and the questions still waiting for an answer. Everything is a plain
   list, so /assumptions can render all of it without knowing any of it. */

export type SettledRule = {
  id: string;
  rule: string;
  source?: string;
  /** did THIS run really honour it. The freeze computes a verdict for the rulings it
      can (the money floor, the daily-measured lag) exactly as it does for the
      assumptions, and the page used to throw them away — a settled ruling never said
      whether the run in front of you kept it. null = nothing this cycle exercised it. */
  in_effect?: boolean | null;
  in_effect_note?: string;
};

export type AssumedRule = {
  id: string;
  assumption: string;
  why?: string;
  /** what would replace this assumption with a ruling */
  changes_it?: string;
  /** is this assumption actually doing anything on THIS run */
  in_effect?: boolean;
  in_effect_note?: string;
};

export type BuildChoice = {
  id: string;
  choice: string;
  why?: string;
  changes_it?: string;
};

export type SpeedRow = {
  line: string;
  slot: string;
  set_of_two?: boolean;
  rated?: number | null;
  aug_median?: number | null;
  aug_best?: number | null;
  aug_runs?: number | null;
  planning?: number | null;
  basis?: string;
  basis_kind?: SpeedBasis;
  used_by_the_plan?: boolean;
};

export type EligibilityRow = {
  line: string;
  slot: string;
  /** family → preference: 1 first choice, 2 when the first choice is full, 3 last resort */
  families: Record<string, number>;
  has_a_speed?: boolean;
};

/** A plan-sheet row whose pack type disagrees with the recipe's own container. */
export type SheetDisagreement = {
  code: string;
  sku: string;
  sheet_pack_type?: string;
  container_name?: string;
  slot?: string;
  family?: string;
};

export type OpenQuestion = {
  number: number;
  section: string;
  title: string;
  question: string;
  status: string;
  answer?: string | null;
};

export type AcceptanceCheck = {
  id: string;
  text: string;
  /** the WHOLE line is this file's to pass */
  checked_here?: boolean;
  /** some clauses are and some are not — see `clauses` */
  checked_here_in_part?: boolean;
  /** a verdict on the whole line, or null when the whole line is not this file's */
  passed?: boolean | null;
  /** the verdict on the clauses this file DID check */
  passed_here?: boolean | null;
  checks?: number;
  /** an acceptance line is several checks in one sentence; each says who owns it */
  clauses?: { clause: string; checked_here: boolean; checked_here_in_part?: boolean;
    verdict_by: string }[];
  verdict_by?: string;
};

export type AssumptionsData = {
  meta: PlanMeta & {
    rulebook_version?: string;
    rulebook_written?: string;
    rulebook_owner?: string;
    rulebook_sources?: Record<string, string>;
    note?: string;
  };
  settled: SettledRule[];
  assumed: AssumedRule[];
  build_choices: BuildChoice[];
  speeds: SpeedRow[];
  eligibility: EligibilityRow[];
  excluded_lines?: Record<string, string>;
  sheet_disagrees: SheetDisagreement[];
  open_questions: OpenQuestion[];
  /** A16 in full — the note beside it shows only the first few */
  a16_products?: {
    named_in_the_rule: string[];
    classed_the_same_way_and_not_named: string[];
    named_but_not_classed_that_way: string[];
  };
  open_questions_source?: string;
  open_questions_convention?: string;
  /** what this particular run had to guess, and what it wants you to know */
  this_run?: {
    assumed?: string[];
    warnings?: string[];
    prefs_used?: Record<string, number>;
    product_changes?: number | null;
    product_changes_by_line?: Record<string, number>;
    second_change_allowed?: number | null;
    second_change_allowed_more_than_once?: number | null;
    /** SESSIONS OPENED. Not hours, and not crews that did anything — see below. */
    night_sessions?: number | null;
    night_sessions_worked?: number | null;
    night_hours_used?: number | null;
    night_hours_rostered?: number | null;
    night_litres?: number | null;
    filled_by_hand?: string[];
    storage_cap?: Overview["storage_cap"];
  };
  /** where a figure came from when the first choice was not available */
  fallbacks?: {
    expected_orders?: { used?: boolean; reason?: string | null; instead?: string };
    lag?: { measured_daily?: boolean; source?: string; measured_on?: string | null; instead?: string };
    night_line?: NightLine & { instead?: string };
  };
  freshness?: {
    rulebook_written?: string;
    questions_file?: string;
    questions_file_read_at?: string | null;
    state_collected_at?: string | null;
    expected_orders_file?: {
      present?: boolean;
      fetched_at?: string | null;
      window?: { from?: string; to?: string; months?: number };
      mode?: string;
      age_days?: number | null;
    };
    lag_file?: { measured_on?: string | null; measured_once?: boolean; window?: string; rows?: number };
    history_through?: string | null;
  };
  preference_semantics?: string;
  drums?: { scheduled?: boolean; skus?: string[]; display?: string; source?: string };
  acceptance: AcceptanceCheck[];
  acceptance_note?: string;
};
