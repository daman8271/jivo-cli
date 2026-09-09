import type { Eligibility, Mark4Input, Product, Rate, Rule, Scenario, PlanningSpeed } from "./types.ts";

export const LINE_IDS = ["JP Machine", "Clear Pack", "10 Head", "6 Head", "Tin Head", "Pouch Machine"];
export const DEFAULT_SCENARIO: Scenario = { shiftStartHour: 8, includePackagingEstimates: true, supplyMode: "expected", nightLine: "auto", efficiency: 1, allowProposedSupply: false, allowProvisionalRecipes: false };
export const STORAGE_LIMIT = 827000;
export const DAY_TARGET = 25000000;
// Provisional planning assumptions, pending measured factory campaign/setup data.
export const PRODUCT_CHANGE_SETUP_HOURS = 1;
export const MIN_NEW_CAMPAIGN_HOURS = PRODUCT_CHANGE_SETUP_HOURS;

export function campaignEligible(productiveHours: number, continuing: boolean): boolean {
  return Number.isFinite(productiveHours) && productiveHours > 0 && (continuing || productiveHours + 1e-7 >= MIN_NEW_CAMPAIGN_HOURS);
}

export function eligibility(p: Pick<Product, "packLitres" | "container" | "category" | "name" | "bottleGrams" | "exclusionReason">, line: string): Eligibility {
  const no = (reason: string): Eligibility => ({ allowed: false, preference: 0, reason });
  const yes = (preference: number, reason: string): Eligibility => ({ allowed: true, preference, reason });
  if (p.exclusionReason) return no(p.exclusionReason);
  const text = `${p.category} ${p.name}`.toLowerCase();
  if (p.container === "unknown") return no("Primary container is not established by the recipe.");
  if (p.container === "drum") return no("Drums are deferred from Mark IV; manual filling exists outside this schedule.");
  if (p.container === "pouch") return line === "Pouch Machine" ? yes(100, "Pouch packaging uses the pouch machine.") : no("Pouches belong on the pouch machine.");
  if (line === "Pouch Machine") return no("This product is not a pouch.");
  if (p.packLitres >= 14 && p.packLitres < 20) return p.container === "tin" && line === "Tin Head" ? yes(100, "15 L / 15 kg tin family uses Tin Head only.") : no("Large 15 L / 15 kg packs require a confirmed tin recipe and Tin Head.");
  if (p.container === "tin" && p.packLitres === 3) return no("3 L tin routing and rate await confirmation; plastic 3 L is separately supported.");
  if (line === "Tin Head") return no("Tin Head's approved planning speed applies only to 15 L tins.");
  if (line === "JP Machine") {
    if (p.packLitres !== 1 || p.container !== "bottle") return no("JP is used for supported 1 L bottle families.");
    if (/yellow/.test(text)) return no("Yellow mustard is excluded from JP by the latest clarification.");
    if (/mustard|kachi|pakki/.test(text)) return yes(100, "Mustard 1 L has first preference on JP.");
    if (/groundnut|peanut/.test(text)) return yes(65, "Groundnut 1 L is allowed on JP; mustard has first preference.");
    return no("No confirmed JP route for this oil/bottle family.");
  }
  if (line === "Clear Pack") {
    if (p.container !== "bottle") return no("Clear Pack needs a supported bottle recipe.");
    if (p.packLitres === 3 || p.packLitres >= 14) return no("Clear Pack cannot fill 3 L or 15 L.");
    if (/sesame/.test(text)) return no("Sesame 1 L is explicitly excluded from Clear Pack.");
    if (p.packLitres === 1 && p.bottleGrams === 40) return yes(95, "Current 40 g 1 L bottle family is preferred on Clear Pack.");
    if (p.packLitres === 1 && p.bottleGrams === 52) return yes(70, "52 g 1 L bottles are allowed; they are not exclusive to Clear Pack.");
    if ([4, 5].includes(p.packLitres)) return yes(p.packLitres === 5 ? 65 : 80, "Supported larger plastic pack; 5 L also has a 6 Head preference.");
    return no("No confirmed Clear Pack bottle/rate match for this pack.");
  }
  if (line === "10 Head" || line === "6 Head") {
    if (![1, 2, 3, 5].includes(p.packLitres)) return no("No supported small-pack route/rate for this size.");
    if (p.container === "tin" && p.packLitres !== 5) return no("Only the confirmed 5 L tin route is enabled on this line family.");
    if (line === "6 Head") return yes(p.packLitres === 5 ? 100 : p.packLitres === 3 ? 85 : 45, p.packLitres === 5 && p.container === "tin" ? "Printed 5 L tins need no label, fitting 6 Head's broken-labeller situation." : p.packLitres === 5 ? "6 Head spacing suits 5 L packs; labelling workaround remains provisional." : "Supported fallback on 6 Head; labelling workaround remains provisional.");
    return yes([1, 2].includes(p.packLitres) ? 90 : p.packLitres === 3 ? 75 : 25, p.packLitres === 5 ? "5 L is possible but less suitable: close head spacing reduces the useful capacity." : "1 L / 2 L preferred here; supported 3 L uses the declared planning speed.");
  }
  return no("Unknown production line.");
}

// Daman's 6 September screenshot is the final planning policy. Source feeds remain
// evidence about the factory; they cannot change these approved capacities.
const SPEED_SOURCE = "Daman's approved Mark IV speed table, 6 September 2026; final containers/hour, used directly.";
const speed = (line: string, pack: string, containersPerHour: number | null, status: PlanningSpeed["status"] = "declared", machine = line): PlanningSpeed =>
  ({ line, machine, pack, containersPerHour, status, source: SPEED_SOURCE, asOf: "2026-09-06" });
export const PLANNING_SPEEDS: readonly PlanningSpeed[] = Object.freeze([
  speed("JP Machine", "1L", 5400),
  speed("Clear Pack", "1L", 4800), speed("Clear Pack", "4L", 800), speed("Clear Pack", "5L", 3000),
  speed("10 Head", "1L", 2100), speed("10 Head", "2L", 1260), speed("10 Head", "3L", 720), speed("10 Head", "5L", 900),
  speed("6 Head", "1L", 1080), speed("6 Head", "2L", 720), speed("6 Head", "3L", 384), speed("6 Head", "5L", 600),
  { ...speed("Tin Head", "15L", 600), source: "Daman's Tin Head 15 L speed instruction, 6 September 2026; final tins/hour, used directly." },
  speed("Pouch Machine", "POUCH", 1800, "declared", "Pouch — Hitech"),
  speed("Pouch Samarpan", "POUCH", null, "not separately scheduled", "Pouch — Samarpan"),
  speed("Manual", "—", null, "not modelled"),
].map(row => Object.freeze(row)));

export function ratesForLine(line: string): Rate[] {
  return PLANNING_SPEEDS.filter(row => row.line === line && row.containersPerHour !== null).map(row => ({
    line, pack: row.pack, piecesPerHour: row.containersPerHour!, effectivePiecesPerHour: row.containersPerHour!,
    basis: "declared", source: row.source, asOf: row.asOf,
  }));
}

export function rateFor(_input: Mark4Input, p: Pick<Product, "packLitres" | "container"> & Partial<Pick<Product, "fillLitres" | "containersPerPiece">>, line: string, _legacyEfficiency?: number): Rate | null {
  if (line === "Tin Head" && p.container !== "tin") return null;
  const key = p.container === "pouch" ? "POUCH" : `${p.fillLitres ?? p.packLitres}L`;
  const units = p.containersPerPiece ?? 1;
  if (!Number.isFinite(units) || units <= 0) return null;
  const declared = ratesForLine(line).find(row => row.pack === key);
  if (!declared) return null;
  return units === 1 ? declared : { ...declared, effectivePiecesPerHour: declared.piecesPerHour / units, source: `${declared.source} Divide by ${units} containers per sales unit to calculate sales units/hour.` };
}

export function rulebook(scenario: Scenario, input?: Mark4Input): Rule[] {
  const orderBasis = input?.orders.some(o => o._src === "ECOM-EXACT") ? "Exact e-commerce source lines now drive accepted/residual planning quantities. Requested residual stays visible in the gross open book; unaccepted quantities are a separate difference." : "Legacy ECOM per-SKU/date allocations are inferred from platform mix, although source aggregate orders are real.";
  return [
    { id: "material-clock", title: "QC uses elapsed hours; shift clock is provisional", detail: `Day starts at ${scenario.shiftStartHour ?? 8}:00 IST for 10 effective hours; selected night adds 10 hours. The clock is editable and awaits factory confirmation. A complete batch reserves its materials at its start, after source release or estimated QA. No automatic extra day; sessions stop at Sunday midnight and the monthly horizon boundary. Sunday remains closed.`, status: "provisional", source: "Daman 9 September: hour-level QC; source shift clocks not provided" },
    { id: "temporary-packaging", title: "Temporary packaging dates await confirmation", detail: `Matching supplier/material/unit receipt history may estimate an existing outstanding packaging delivery, capped at the order balance. ${scenario.includePackagingEstimates === false ? "Disabled" : "Enabled"} in this scenario, excluded in recorded mode, and expires after 10 September 2026. A missed historical anchor is never advanced automatically.`, status: "provisional", source: "Daman 9 September: use estimated dates until owner confirmation" },
    { id: "sessions", title: "10 effective hours per session", detail: "One day session on each enabled line; at most one line gets an extra 10-hour night session. Automatic selection compares up to two feasible campaigns at 10 and 20 hours on each line, including shared materials, storage, setup and the minimum campaign guard. A night needs additional productive filling, not setup alone. This bounded priority-based preview is not a proof of the best possible factory-wide schedule. Sunday has no production.", status: "confirmed", source: "5 Sep meeting 11:11–11:30, 13:14–13:24, 14:21–14:38" },
    { id: "speeds", title: "Use the approved machine speeds directly", detail: "The complete speed table below is the final planning capacity in physical containers/hour. No further efficiency multiplier applies. Combo packs divide by containers per sales unit. Tin Head has an approved speed for 15 L tins only, Hitech alone supplies pouch capacity, Samarpan is not separately scheduled and manual filling is not modelled. Factory readings do not override this policy.", status: "confirmed", source: SPEED_SOURCE },
    { id: "campaign", title: "Keep a product running; permit a justified second campaign", detail: "Prefer one SKU per line/day. If that run finishes or is blocked, a second SKU can use the remaining session after a provisional 1-hour setup. Product changes across different dates also cost 1 hour; same-product continuation does not. The first horizon setup is unknown and provisionally zero. At most two campaigns per line/day. This avoids treating a preference as a physical ban.", status: "provisional", source: "Meeting 09:28–09:59; 1-hour setup is a planner assumption pending measured setup data" },
    { id: "campaign-minimum", title: "Defer new campaigns shorter than 1 productive hour", detail: `A new product campaign must have at least ${MIN_NEW_CAMPAIGN_HOURS} hour of feasible filling time after demand, materials, storage and session limits. This provisional planning guard uses the existing setup allowance as its minimum; it is not a measured factory minimum batch. It also applies to the first horizon campaign, even though its opening setup is unknown and provisionally zero. A same-product continuation on that line can finish a smaller remainder. Deferred quantities stay unmet and can run when later supply or space makes a sufficient campaign possible.`, status: "provisional", source: "Planner correction, 8 September 2026; pending factory confirmation of practical batch sizes" },
    { id: "jp", title: "JP: mustard first, groundnut allowed", detail: "Supported 1 L mustard bottles have first preference. Groundnut is allowed. Yellow mustard is excluded from JP and considered on supported 10/6 Head routes.", status: "confirmed", source: "Daman clarifications [8], [9], [13]" },
    { id: "clear", title: "Clear Pack follows the bottle", detail: "1 L 40 g preferred, 52 g allowed; supported 4/5 L plastic packs allowed. No 3 L, no 15 L, no sesame. Unidentified 1 L bottle families are held.", status: "confirmed", source: "Meeting 03:03, 06:43, 11:42; Daman [8]/[9]" },
    { id: "heads", title: "10 Head small bottles; 6 Head larger packs", detail: "10 Head prefers 1/2 L, 6 Head prefers 5 L, especially printed tins. Plastic 3 L uses the declared pack rates on 10 Head and 6 Head. 5 L on 10 Head is less suitable, not impossible. 6 Head's separate labelling workaround is unconfirmed.", status: "provisional", source: "Meeting 07:07–08:44" },
    { id: "tins", title: "15 L tins on Tin Head only", detail: "Container comes from the recipe's primary bottle/tin/pouch, not the plan-sheet pack column. The declared speed applies only to 15 L tins. Other tin fill sizes, including 15 kg packs with a different litre fill, have no approved Tin Head speed. Production still requires materials, demand and warehouse space.", status: "confirmed", source: "Daman's Tin Head 15 L speed instruction, 6 September 2026" },
    { id: "cartons", title: "20-piece transition is agreed; legacy FG handling is provisional", detail: "Old/new SKU identity is merged only with a verified transition. Pieces stay pieces; each replacement carton consumes 1/20 per piece. The separate provisional-recipe switch can test the narrow PM0000121 bottle/identical-closure family with PM0000914 at 1/20, retaining other coefficients and old identity; affected output is conditional and shown separately against a strict baseline. Without this explicit scenario, a missing verified replacement blocks new production of that old 16-piece family, while existing old FG provisionally covers its family demand by bottle count. This does not prove it is ready to ship in 20-piece cases; recartoning material/labour is not yet known.", status: "provisional", source: "Meeting 04:26, 15:51–16:02; Daman [13]; legacy FG shipping/repacking treatment is unresolved" },
    { id: "demand", title: "Production projection remains; real POs take priority", detail: `Remaining make target = monthly production target minus booked month-to-date pieces. Required make = max(remaining target, open PO pieces minus available FG). POs are part of that total, not added twice. Reserve stays visible for late-month GT/MT demand. ${orderBasis} No new historical GT/MT average is claimed.`, status: "assumption", source: "Daman [13]; interpreting the sheet as goods made is provisional and needs owner confirmation" },
    { id: "history", title: "Booked production and MES are overlapping views", detail: "Only booked-by-item is used for provisional month-to-date netting. Missing days leave MTD unknown; known booked quantities are a lower bound. MES is never added. Current FG is not subtracted again from the production target.", status: "provisional", source: "Factory history data contract; monthly-target meaning is still an open question" },
    { id: "storage", title: "Billing does not release warehouse space", detail: "BH-BT/BH-PF physical pressure includes unbilled FG and billed waiting stock. Working limit is the declared 827,000 L. Current standing stock is an Oil-share estimate; future shipments are assumptions. Existing billed backlog drains over two days; newly fulfilled real POs leave two days after their due/ready date. Forecast reserve stays until an order exists. The 14-day tail is disclosed, not modelled.", status: "assumption", source: "Declared capacity 29 Aug/4 Sep; meeting 00:37–01:08, 14:47–15:04" },
    { id: "supply", title: "Shared recipes, blends and dated arrivals", detail: `All lines draw from one material ledger. Ready blend stock is used before its component oils. Existing issued POs and transit events remain separate source commitments. Supported future dates are credited as expected, not received. Missing/overdue dates stay held for reconfirmation; they are never automatically moved to today. Your arrival-date overrides are explicit conditional availability scenarios. Hypothetical NEW purchasing is ${scenario.allowProposedSupply ? "included" : "excluded"}; already-issued comparable quantities reduce new purchase proposals without becoming production stock. Suggested procurement lead times are provisional: 7 days for packaging, 14 for oils, with immediate ordering when already late; these are not supplier commitments. Packaging in BH-NM and GP-NM was explicitly allowed by the owner on 29 August. Opening oil uses EXIM only; factory oil balances are excluded. Source arrival dates plus elapsed receiving-to-QA hours govern conditional readiness. Only the separately labelled, expiring temporary packaging scenario can use matching receipt cadence; old unlabelled historical arrival promises are disabled.`, status: "assumption", source: "Factory/EXIM input provenance; owner warehouse ruling, 29 August" },
    { id: "value", title: "₹2.5 crore is desired daily production value", detail: "₹2 crore is the discussed minimum. Daily gaps are shown for production days only; Sunday is closed. The original input realisation table is an estimate, not billing or guaranteed sale; its own valuation date was not supplied, so the input collection timestamp is not a price-validation date. Missing valuations stay unknown; abnormal inherited rates are disclosed on products.", status: "provisional", source: "Daman [8]/[9]/[13]; calendar-day versus production-day target remains unresolved" },
    { id: "labour", title: "Labour cost needs a verified session basis", detail: "A recorded-run cost is not automatically a 10-hour session cost. Missing session cost displays as unavailable. If a verified session cost is supplied, each started 10-hour session is charged once, without assuming short runs reduce the crew cost. Pouch work without a PO remains a low-priority reserve campaign; labour availability is not independently measured.", status: "unavailable", source: "Meeting 12:23–13:03; JA means ji.jivo.in, Daman [9]" },
    { id: "deferred", title: "Drums, employee messaging and August backtest are deferred", detail: "No manual drum schedule, no WhatsApp sends, no autonomous rule edits. Mark IV is a deterministic planning scenario and has not been calibrated against August. No Mark 3 future schedule is reused.", status: "confirmed", source: "Daman final clarification [13]" },
  ];
}
