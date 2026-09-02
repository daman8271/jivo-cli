// Types mirror site-sep/data/*.json, which is written ONLY by scripts/gen-data.py
// from the verified September artifacts. September 2026 has not happened:
// everything here is a forward PLAN — objects carry simulated/assumed flags.

export type Run = {
  line: string; code: string; sku: string; head: string; oil: string | null;
  pieces: number; litres: number; hours: number; flush_min: number;
  realise: number; rs_per_hour: number; po_backed: boolean; value: number; date?: string;
};
export type Blocked = { code: string; sku: string; want: number; binder: string; binder_name: string };
export type OrderRow = {
  docnum: string; customer: string; channel: string; code: string; sku?: string;
  pieces: number; value: number; assumed?: boolean;
};
export type DispatchRow = {
  docnum: string; customer: string; channel: string; sku: string;
  pieces: number; litres: number; assumed?: boolean;
};
export type Buy = { code: string; name: string; qty: number; uom: string; lands: string };
export type Received = { code: string; name: string; qty: number; kind: string };
export type WaitingOn = { code: string; name: string; since: string };
export type StorageDay = {
  physical_l: number; ceiling_l: number; peak_l: number; pct: number;
  fg_in_godown_l: number; invoiced_not_trucked_l: number; headroom_l: number;
};
export type Book = {
  plan_left_l: number;
  po_cumulative_value_rs: number; po_cumulative_value_label: string;
  po_open_l_raw: number; po_open_l_raw_label: string;
  forecast_open_l: number;
};
export type SimEvent = { day: string; kind: string; [k: string]: unknown };

export type SpineDay = {
  n: number; date: string; weekday: string; working: boolean;
  made_l: number; value_rs: number; shipped_l: number; util: number;
  storage_pct: number; headroom_l: number; runs: number; flushes: number;
  blocked: number; unblocked: number; bought: number; oil_used_l: number;
  orders: {
    real_rows: number; real_pieces: number; real_value_rs: number;
    forecast_rows: number; forecast_pieces: number; forecast_value_rs: number;
    forecast_assumed: boolean;
  };
  dispatched: { real_l: number; forecast_l: number };
  received_count: number; received_top: Received[];
  events: Record<string, number>;
  news: { materials_landed: number; real_pos_entering: number; forecast_rows: number };
  book: Book;
  open_real_l_computed: number; open_real_l_note: string;
};

export type DayDetail = {
  n: number; date: string; weekday: string; working: boolean;
  made_litres: number; made_value_rs: number; shipped_litres: number;
  oil_used_l: number; line_util: number; line_hours: Record<string, number>;
  flushes: number; storage: StorageDay; storage_ceiling_assumed: boolean;
  book: Book; open_real_l_computed: number;
  runs: Run[]; blocked: Blocked[]; unblocked: { code: string; name: string; waited_days?: number }[];
  waiting_on: WaitingOn[]; received: Received[];
  orders_real: OrderRow[]; orders_forecast: OrderRow[];
  dispatched_real: DispatchRow[]; dispatched_forecast: DispatchRow[];
  bought: Buy[]; decisions: { kind: string; text: string }[];
  events: SimEvent[];
  news: { materials_landed: number; unblocked: unknown[]; real_pos_entering: number; forecast_rows: number };
  honesty: { measured: string[]; assumed: string[] };
  simulated: boolean;
};

export type SlotSpec = {
  slot: string; stored_rate_per_hr: number;
  rate_basis: "observed" | "rated" | "derived";
  effective_rate_per_hr: number; note: string;
};
export type LineStat = {
  name: string; slots: SlotSpec[]; runs: number; litres: number; pieces: number;
  hours_run: number; hours_on_line: number; value_rs: number; days_active: number;
  flush_minutes: number; top_skus: { sku: string; litres: number }[];
};
export type LinesData = {
  efficiency: number; efficiency_note: string; lines: LineStat[];
  total_litres: number; total_litres_note: string;
  runs_by_line: Record<string, Run[]>; measured_from: string;
};

export type StorageData = {
  ceiling: { working_l: number; peak_l: number; assumed: boolean; source: string; open_question: string };
  standing_at_open: { litres: number; assumed: boolean; optimistic: boolean; note: string };
  invoice_truck_lag_days: number;
  invoice_truck_note: string;
  series: {
    n: number; date: string; working: boolean; physical_l: number; pct: number;
    fg_in_godown_l: number; invoiced_not_trucked_l: number; headroom_l: number;
    invoiced_l: number; trucked_out_l: number;
  }[];
  biggest_fall: {
    n: number; date: string; fall_l: number; trucked_out_l: number; made_l: number;
    invoiced_that_day_l: number; source_day_n: number | null; source_date: string | null; note: string;
  };
  biggest_invoicing_day: { n: number; date: string; invoiced_l: number; trucked_out_that_day_l: number };
  biggest_trucked_day: { n: number; date: string; trucked_out_l: number };
  days_ge_95: number; days_ge_100: string[];
  throttles: { day: string; pct_start_of_day: number; headroom_l: number }[];
  simulated: boolean;
};

export type MaterialRow = {
  code: string; name: string; kind: string; uom: string;
  need: number; on_hand: number; on_order: number; cover_pct: number; short: number;
  at_zero: string; skus_blocked: number; litres_at_risk: number; value_at_risk: number;
  lead_days: number; first_short_day: string; order_by: string; order_basis: string;
  status: string; skus: string; late: boolean; zero_literal: boolean; zero_august_rule: boolean;
};
export type ZeroDef = {
  definition: string; items: number; skus_blocked: number; blocked_value_rs: number;
  zero_pack?: number; zero_oil?: number; blocked_value_note?: string; codes?: string[];
};
export type Unproducible = {
  code: string; sku: string; pack_type: string; litres_per_piece: number;
  plan_pieces: number; plan_litres: number; slot_needed: string; reason: string;
  value_est_rs?: number; value_est_derived?: boolean;
};
export type MaterialsData = {
  generated: string; basis: string; components_in_plan: number; under_100_cover: number;
  must_order_week1: number; already_late: number; lead_days: { oil: number; packaging: number };
  zero_definitions: {
    literal: ZeroDef; august_rule: ZeroDef;
    opening_zero_reconciliation: {
      opening_items: number; literal_items: number; chase_items: number;
      chase_codes: string[]; note: string;
    };
    note: string;
  };
  rows: MaterialRow[];
  opening_at_zero: { code: string; name: string; kind: string }[];
  unproducible: Unproducible[]; unproducible_note: string; synonyms: string;
};

export type BuildRun = {
  seq: number; code: string; sku: string; oil: string | null; oil_name: string | null;
  pieces: number; litres: number; hours: number;
  changeover_before: { minutes: number; kind: string; note: string } | null;
  po_backed: boolean;
};
export type BuildMachine = { machine: string; hours_used: number; runs: BuildRun[] };
export type BuildDay = {
  date: string; weekday: string; working: boolean; made_litres: number;
  made_value: number; line_util: number; machines: BuildMachine[];
  news: { materials_landed: number; unblocked: unknown[]; real_pos_entering: number; forecast_rows: number };
  note?: string;
};
export type BuildData = {
  meta: {
    month: string; generated: string; source: string; simulated: boolean;
    rules: { flush_litres: number; line_clearance_min: number; note: string };
    recipient: { name: string; display: string; title: string; number_masked: boolean };
    totals: { days: number; working_days: number; runs: number; oil_changes: number; clearances_only: number; litres: number };
    sample_day1: string[];
  };
  days: BuildDay[];
};

export type WaMsg = { day: string; dir: "in" | "out"; text: string; tag: string; assumed: boolean };
export type WaThread = {
  name: string; title: string; display: string; number_masked: boolean;
  count: number; simulated: boolean; messages: WaMsg[];
};
export type WaData = {
  meta: {
    note: string; forward: boolean; sent: number; assumed_sends: number; assumed_replies: number;
    simulated: boolean; numbers_masked: boolean; masking_note: string;
  };
  threads: WaThread[];
};

export type Scenario = {
  id: string; label: string; shift_hours: number; working_days: number;
  // tapered patterns only — phase ceilings derived by the generator from the day files
  pattern?: string;
  taper?: {
    front_hours: number; front_days: number; tail_hours: number; tail_days: number;
    boundary_day: number; derived_note: string;
  };
  share_of_flat_front_gain_pct?: number;
  made_l: number; value_rs: number; shipped_l: number; delta_made_l: number;
  line_hours_used: number; extra_line_hours_offered: number; extra_line_hours_used: number;
  pct_extra_hours_used: number | null; days_storage_ge_95: number;
  storage_throttle_events: number; note: string; simulated: boolean;
};
export type ScenariosData = {
  baseline: {
    id: string; label: string; shift_hours: number; working_days: number;
    made_l: number; value_rs: number; shipped_l: number; line_hours_used: number;
    days_storage_ge_95: number; storage_throttle_events: number; baseline: boolean;
  };
  scenarios: Scenario[]; takeaway: string; method_note: string; artifact_note: string;
  simulated: boolean;
};

export type LoopChain = {
  code: string; name: string; kind: string; ordered_day: string; qty: number;
  lands: string; lead_days: number; fg_codes_blocked: string[]; simulated: boolean;
  unblocked_day: string | null; waited_days?: number;
  first_run_after_unblock?: { day: string; code: string; sku: string; litres: number };
  note?: string;
};
export type LoopsData = {
  note: string; chains: LoopChain[]; ordered_events: number; unblocked_events: number;
  resolved_chains: number; ran_after_unblock: number; landed_no_run: number;
  resolved_note: string; simulated: boolean;
};

export type LabelRule = { id: string; rule: string; [k: string]: unknown };
export type HonestyData = {
  forward_rule: string; measured: string[]; assumed: string[];
  provenance: Record<string, string>; label_rules: LabelRule[];
  august_calibration: { sim_made_l: number; actual_made_l: number; delta_pct: number; note: string };
};

export type QuestionItem = { n: number; priority: string; one_liner: string; status: string };
export type QuestionsData = { asked: string; note: string; items: QuestionItem[] };

export type Overview = {
  meta: {
    month: string; frozen: string; as_of: string; horizon: string[];
    forward: boolean; forward_rule: string; generated: string;
  };
  totals: {
    made_l: number; value_rs: number; shipped_l: number; oil_used_l: number;
    days: number; working_days: number; runs: number; oil_changes: number;
    clearances_only: number; flushes: number; bought_lines: number; events: number;
    util_median: number; peak_day: { date: string; made_l: number };
  };
  plan: { litres: number; skus: number; made_vs_plan_pct: number; source: string };
  demand: {
    rows: number; real_rows: number; forecast_rows: number;
    real_pieces: number; forecast_pieces: number; real_value_rs: number; forecast_value_rs: number;
    forecast_share_pieces_pct: number; forecast_share_value_pct: number; forecast_share_litres_pct: number;
    order_dates: number; channels: Record<string, number>; note: string;
  };
  opening: {
    fg_litres: number; fg_plan_l: number; fg_other_l: number;
    oil_l: number; oil_l_definition: string; packaging_pieces: number;
    inbound_oil_l: number; inbound_packaging: number;
    standing_l: number; standing_assumed: boolean;
    backlog_pieces: number; backlog_value_rs: number;
    plan_sku_backlog_docs: number; plan_sku_backlog_docs_overdue: number;
    at_zero_count: number;
  };
  storage: {
    ceiling_l: number; peak_l: number; ceiling_assumed: boolean;
    invoice_truck_lag_days: number;
    days_ge_95: number; days_ge_100: string[]; throttle_events: number;
  };
  day1_blocked: {
    attempts: number; products: number; product_binder_pairs: number;
    by_binder_class: Record<"oil" | "zero_stock_packaging" | "other_packaging", { attempts: number; products: number }>;
    top_binder: { code: string; name: string; kind: string; attempts: number; products: number };
    products_in_multiple_classes: number;
    zero_openers_products_blocked_month: number;
    note: string;
  };
  august: { sim_made_l: number; actual_made_l: number; delta_pct: number; note: string };
  scenarios_mini: { id: string; label: string; made_l: number; delta_made_l: number; pct_extra_hours_used: number | null }[];
  materials_mini: {
    components: number; under_100_cover: number; must_order_week1: number; already_late: number;
    zero_literal_items: number; zero_literal_value_rs: number;
    zero_august_rule_items: number; zero_august_rule_value_rs: number;
  };
  whatsapp_mini: { threads: number; messages: number; replies: number; simulated: boolean };
  unproducible: Unproducible[];
  questions_top: QuestionItem[];
  simulated: boolean;
};

export const LINES = ["JP Machine", "Clear Pack", "10 Head", "6 Head", "Pouch Machine", "Tin Head"];
