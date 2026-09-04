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
  factory_inbound?: InboundNow;
  factory_production?: ProductionNow;
  oms?: OmsNow;
};

/** The name of an adapter inside state.json. */
export type StateSourceKey =
  | "ecom"
  | "exim"
  | "factory_dispatch"
  | "factory_inbound"
  | "factory_production"
  | "oms";

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
  plan: { litres: number; skus: number; made_vs_plan_pct: number; source?: string };
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
  };
  day1_blocked?: {
    attempts: number;
    products: number;
    by_binder_class?: Record<string, { attempts: number; products: number }>;
    top_binder?: { code: string; name: string; kind: string; attempts: number; products: number } | null;
    note?: string;
  };
  august?: { sim_made_l: number; actual_made_l: number; delta_pct: number; note?: string };
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
  blocked: number;
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
  blocked: { code: string; sku: string; want: number; binder: string; binder_name: string }[];
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

export type LineSlot = {
  slot: string;
  stored_rate_per_hr: number;
  /** rated | observed | derived — the honest basis for the speed */
  rate_basis: string;
  rate_basis_raw?: string;
  effective_rate_per_hr: number;
  note?: string;
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
  august_calibration?: { sim_made_l: number; actual_made_l: number; delta_pct: number; note?: string };
  not_here?: Record<string, string>;
};
