import { istDate, recent, validateBaseline, validateFactory } from "./shift-validation.ts";
import type { FactoryNow, ShiftBaseline } from "./shift-types.ts";
export type TodayReviewData = { version: 1; date: string; generatedAt: string; factory: FactoryNow | null; factoryError: string | null; baseline: ShiftBaseline | null; baselineError: string | null };
export function validReviewDate(date: string, now = Date.now()): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(date) && Number.isFinite(Date.parse(`${date}T00:00:00Z`)) && new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) === date && date >= "2026-09-01" && date <= istDate(now);
}
export function validateReviewBaseline(value: unknown, date: string, now = Date.now()): asserts value is ShiftBaseline {
  if (!validReviewDate(date, now)) throw new Error("Invalid review date.");
  validateBaseline(value, date === istDate(now) ? now : Date.parse(`${date}T23:59:59.999+05:30`));
}
export function validateTodayReview(value: unknown, date: string): asserts value is TodayReviewData {
  if (!value || typeof value !== "object") throw new Error("Review response unavailable.");
  const v = value as TodayReviewData;
  if (v.version !== 1 || v.date !== date || !recent(v.generatedAt, Date.now())) throw new Error("Review response is invalid or out of date.");
  if (v.factory !== null) {
    validateFactory(v.factory);
    if (v.factory.date !== date || v.factory.asOf && (istDate(Date.parse(v.factory.asOf)) !== date || Date.parse(v.factory.asOf) > Date.now() + 30000)) throw new Error("Factory report belongs to another date.");
  }
  if (v.baseline !== null) validateReviewBaseline(v.baseline, date);
}
