import type { Mark4Input, Order } from "./types.ts";

const positive = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value) && value > 0;
const samePack = (a: number, b: number) => Math.abs(a - b) <= Math.max(1e-6, Math.max(a, b) * .0001);
function oilIdentity(name: string): string | null {
  const text = name.toUpperCase().replace(/[^A-Z]/g, " ").replace(/\s+/g, " ");
  if (/POMACE/.test(text)) return "pomace";
  if (/EXTRA\s*LIGHT/.test(text)) return "extra-light";
  if (/EXTRA\s*VIRGIN/.test(text)) return "extra-virgin";
  if (/GROUND\s*NUT|PEANUT/.test(text)) return "groundnut";
  if (/YELLOW.*MUSTARD|MUSTARD.*YELLOW/.test(text)) return "yellow-mustard";
  if (/MUSTARD/.test(text)) return "mustard";
  if (/SUN\s*FLOWER/.test(text)) return "sunflower";
  if (/RICE\s*BRAN/.test(text)) return "rice-bran";
  if (/SESAME|GINGELLY/.test(text)) return "sesame";
  if (/CANOLA|RAPESEED/.test(text)) return "canola";
  return null;
}

export function identityConflict(input: Mark4Input, code: string): string | null {
  const explicit = input.identityConflicts?.find(row => row.code === code);
  if (explicit) return explicit.reason;
  const factory = input.factoryIdentity?.items[code];
  const plan = input.plan.find(row => row.code === code);
  if (factory && plan && positive(factory.packLitres) && !samePack(factory.packLitres, plan.litres_per_piece)) return "Current factory sales-unit litres conflict with the inherited production plan/recipe identity.";
  if (factory) {
    const factoryOil = oilIdentity(factory.name);
    const planOil = oilIdentity(plan?.sku ?? input.items[code]?.name ?? "");
    if (factoryOil && planOil && factoryOil !== planOil) return `Current factory oil identity (${factoryOil}) conflicts with the inherited planner identity (${planOil}).`;
  }
  return null;
}

export function orderLitres(order: Order): number | null {
  if (typeof order.remainingLitres === "number" && Number.isFinite(order.remainingLitres) && order.remainingLitres >= 0) return order.remainingLitres;
  const pack = order.sourcePackLitres ?? order.packLitres;
  return positive(pack) ? order.pieces * pack : null;
}

export function orderIdentityIssue(input: Mark4Input, order: Order): string | null {
  if (!order.code) return order.mappingIssue ?? "No verified factory SKU mapping.";
  const conflict = identityConflict(input, order.code);
  if (conflict) return conflict;
  if (order.code_mapping_verified === false) return order.mappingIssue ?? "Source product identity is not verified against the current factory and production recipe.";
  if ((order.mappingStatus || input.factoryIdentity) && order.code_mapping_verified !== true) return "Source-to-factory-to-recipe identity has not been verified.";
  const transition = input.supplements?.cartonTransitions?.find(t => t.to === order.code);
  const plan = input.plan.find(row => row.code === order.code || row.code === transition?.from);
  const pack = plan?.litres_per_piece ?? input.factoryIdentity?.items[order.code]?.packLitres ?? input.valuation?.litresPerPiece[order.code];
  const sourcePack = order.sourcePackLitres ?? order.packLitres;
  if (positive(pack) && positive(sourcePack) && !samePack(pack, sourcePack)) return `Source sales unit is ${sourcePack} L but the factory production identity is ${pack} L. No rescaling or cross-product substitution is allowed.`;
  if (positive(pack) && typeof order.remainingLitres === "number" && Math.abs(order.pieces * pack - order.remainingLitres) > Math.max(.11, order.remainingLitres * .0001)) return "Source remaining litres do not reconcile with pieces and the verified factory sales unit.";
  return null;
}
