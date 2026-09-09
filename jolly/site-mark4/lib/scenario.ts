import type { Scenario } from "./types.ts";
import { DEFAULT_SCENARIO, LINE_IDS } from "./rules.ts";

const EPS = 1e-7;
// Accept valid legacy efficiency fields, but every saved/API scenario uses the final policy.
export function validateScenario(value: unknown): Scenario {
  if (value === undefined) return { ...DEFAULT_SCENARIO };
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Scenario must be an object.");
  const v = value as Record<string, unknown>;
  if (Object.keys(v).some(k => !["shiftStartHour", "includePackagingEstimates", "nightLine", "efficiency", "allowProposedSupply", "allowProvisionalRecipes", "arrivalDates", "supplyMode"].includes(k))) throw new Error("Unknown scenario setting.");
  if (v.shiftStartHour !== undefined && (typeof v.shiftStartHour !== "number" || !Number.isInteger(v.shiftStartHour) || v.shiftStartHour < 0 || v.shiftStartHour > 23)) throw new Error("Shift start must be an IST hour from 0 to 23.");
  if (v.includePackagingEstimates !== undefined && typeof v.includePackagingEstimates !== "boolean") throw new Error("Packaging estimate setting must be true or false.");
  const efficiency = v.efficiency === undefined ? 1 : v.efficiency;
  if (typeof efficiency !== "number" || !Number.isFinite(efficiency) || efficiency < .4 || efficiency > 1 || Math.abs(efficiency * 100 - Math.round(efficiency * 100)) > EPS) throw new Error("Efficiency must be between 0.4 and 1 in whole percentage points.");
  const nightLine = v.nightLine === undefined ? "auto" : v.nightLine;
  if (nightLine !== null && nightLine !== "auto" && !(typeof nightLine === "string" && LINE_IDS.includes(nightLine))) throw new Error("Choose a supported night line.");
  if (v.allowProposedSupply !== undefined && typeof v.allowProposedSupply !== "boolean") throw new Error("Supply setting must be true or false.");
  if (v.allowProvisionalRecipes !== undefined && typeof v.allowProvisionalRecipes !== "boolean") throw new Error("Recipe setting must be true or false.");
  if (v.supplyMode !== undefined && !["expected", "recorded"].includes(String(v.supplyMode))) throw new Error("Choose expected or recorded supply dates.");
  const dates = v.arrivalDates ?? {};
  if (!dates || typeof dates !== "object" || Array.isArray(dates) || Object.keys(dates).length > 20) throw new Error("Choose at most 20 incoming material dates.");
  for (const [id, date] of Object.entries(dates)) if (!id || id.length > 160 || typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(date)) || new Date(`${date}T12:00:00Z`).toISOString().slice(0,10) !== date) throw new Error("Incoming dates must be valid calendar dates.");
  const arrivalDates = Object.fromEntries(Object.entries(dates).sort(([a],[b])=>a.localeCompare(b))) as Record<string, string>;
  return { shiftStartHour: (v.shiftStartHour as number | undefined) ?? 8, includePackagingEstimates: (v.includePackagingEstimates as boolean | undefined) ?? true, supplyMode: (v.supplyMode as Scenario["supplyMode"]) ?? "expected", arrivalDates, nightLine: nightLine as string | null, efficiency: 1, allowProposedSupply: (v.allowProposedSupply as boolean | undefined) ?? false, allowProvisionalRecipes: (v.allowProvisionalRecipes as boolean | undefined) ?? false };
}

