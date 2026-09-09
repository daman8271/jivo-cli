// Shared MARK V contract. Engine owner coordinates changes with service and UI.
export type MachineId = "JP Machine" | "Clear Pack" | "10 Head" | "6 Head" | "Tin Head" | "Hitech" | "Samarpan";
export type SourceHealth = { id: string; label: string; asOf: string | null; status: "fresh" | "stale" | "missing" | "conflict"; note: string };
export type PlanningAssumption = { id: string; label: string; detail: string };
export type ValidationResult = { valid: boolean; errors: string[]; warnings: string[] };
export type Changeover = {
  minutes: number | null; sourceRange: { min: number; max: number | null } | null;
  basis: "continuation" | "approved" | "planning_assumption" | "unknown";
  ruleId: string; includedActivities: string[]; flushingLitres: number | null;
  flushingPolicy: "reused"; requiresConfirmation: boolean;
};
export type PlannedRun = {
  id: string; machineId: MachineId; code: string; product: string; date: string;
  shift: "day" | "night"; setupStartsAt: string; startsAt: string; endsAt: string;
  pieces: number; containers: number; cases: number | null; litres: number;
  piecesPerCase: number | null; containersPerPiece: number; packLitres: number;
  speedPerHour: number; speedRange: { min: number; max: number };
  changeover: Changeover; fillingMinutes: number;
  demandBasis: "orders" | "forecast" | "mixed"; confirmedLitres: number;
  conditional: boolean; constraints: string[]; reason: string;
};
export type PlanningBlocker = { machineId: MachineId | null; code: string | null; reason: string; kind: "material" | "storage" | "route" | "setup" | "demand" | "source" };
export type DayProposal = {
  storage?: { openingLitres: number; limitLitres: number; closingLitres: number; standingLitres: number; standingBasis: string; spaceNeededForMinimumLitres: number; conditional: boolean };
  date: string; runs: PlannedRun[]; blockers: PlanningBlocker[];
  dayLitres: number; nightLitres: number; totalLitres: number;
  confirmedLitres: number; targetLitres: number; desirableRangeLitres: [number, number];
  shortfallLitres: number; nightReason: string; assumptions: PlanningAssumption[];
  validation: ValidationResult;
};
export type MachineNow = {
  machineId: MachineId; status: "running" | "stopped" | "completed" | "not_started" | "unknown";
  code: string | null; product: string | null; recordedLitres: number | null;
  targetLitres: number | null; asOf: string | null; note: string;
};
export type TodayBoard = { date: string; recordedLitres: number | null; recordedBasis: string; machines: MachineNow[]; aggregatePouchNote: string | null; proposal?: DayProposal };
export type MachineRuleView = { machineId: MachineId; packs: string; speed: string; changeover: string; note: string; sourcePages: string };
export type ProductChoice = { code: string; name: string; packLitres: number; piecesPerCase: number | null; machines: MachineId[] };
export type PlanningChange =
  | { type: "prioritize_sku"; code: string }
  | { type: "set_line_enabled"; machineId: MachineId; enabled: boolean }
  | { type: "set_night_line"; machineId: MachineId | "auto" | null }
  | { type: "set_run"; machineId: MachineId; code: string; pieces: number; shift: "day" | "night" };
export type PlanCommand = { expectedRevision: number | null; idempotencyKey: string; date: string; changes: PlanningChange[] };
export type PlanRevision = {
  id: string; date: string; revision: number; parentRevision: number | null;
  status: "draft" | "approved" | "superseded"; createdAt: string;
  createdBy: "operator" | "ai" | "system"; sourceRevision: string; rulesVersion: string;
  proposal: DayProposal; changes: PlanningChange[];
};
export type PlanSummary = { id: string; date: string; revision: number; status: PlanRevision["status"]; createdAt: string; totalLitres: number; sourceRevision: string };
export type ActivityEvent = { id: string; at: string; kind: string; title: string; detail: string; status: "info" | "succeeded" | "failed" | "running"; jobId: string | null };
export type JobSummary = {
  id: string; kind: "refresh" | "replan" | "ai_review";
  status: "queued" | "running" | "succeeded" | "failed" | "superseded";
  inputRevision: string; resultRevision: string | null; createdAt: string;
  finishedAt: string | null; error: string | null;
};
export type PlanningSnapshot = {
  schemaVersion: 1; revision: string; generatedAt: string; sourceRevision: string;
  sourceAsOf: string; freshness: SourceHealth[]; today: TodayBoard;
  tomorrow: DayProposal; ahead: DayProposal[]; savedPlans: PlanSummary[];
  activity: ActivityEvent[]; jobs: JobSummary[]; machineRulesVersion: string;
  machineRules: MachineRuleView[]; products: ProductChoice[];
};
export type EngineRequest = {
  input: unknown; factoryNow: unknown; now: string;
  sourceRevision: string; sourceStatus?: string;
  command?: PlanCommand; savedPlans?: PlanRevision[];
};
export type EngineResult = { snapshot: PlanningSnapshot; proposal: DayProposal | null; validation: ValidationResult };
export type PlansResponse = { date: string; proposal: DayProposal | null; revisions: PlanRevision[] };
export type JobAccepted = { job: JobSummary };
