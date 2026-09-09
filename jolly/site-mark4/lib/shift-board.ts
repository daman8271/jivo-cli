import { feasible, trial, normalizeProducts } from "./model.ts";
import { LINE_IDS, rateFor, campaignEligible, PRODUCT_CHANGE_SETUP_HOURS, MIN_NEW_CAMPAIGN_HOURS } from "./rules.ts";
import { istDate, recent } from "./shift-validation.ts";
import type { Mark4Input, Mark4Model, Product } from "./types.ts";
import type { FactoryLine, FactoryNow, ShiftBaseline, ShiftBoard, ShiftAdvice, ShiftCandidate } from "./shift-types.ts";

export function unavailableFactory(error: string, now = Date.now()): FactoryNow {
  return { version: 1, revision: "unavailable", attemptedAt: new Date(now).toISOString(), asOf: null, ok: false, complete: false, expectedRefreshSeconds: 60, date: istDate(now), error, lines: LINE_IDS.map(line => ({ line, coverage: "unreported", status: "UNKNOWN", runs: [], note: error })) };
}
export function buildShiftBoard(input: Mark4Input, model: Mark4Model, factory: FactoryNow, baseline: ShiftBaseline | null, baselineError: string | null, now = Date.now()): ShiftBoard {
  const date = istDate(now);
  if (baseline?.date !== date) baseline = null;
  const products = model.products;
  const identity = (code: string | null) => code ? products.find(p => p.code === code || p.originalCodes.includes(code)) : undefined;
  const same = (a: string | null, b: string) => !!a && (a === b || identity(a)?.originalCodes.includes(b) === true);
  const today = factory.date === date;
  const factoryFresh = today && factory.ok && recent(factory.asOf, now);
  const preparedInput = { ...input, bom: { ...input.bom, ...((input.supplements?.verifiedBom ?? {}) as Mark4Input["bom"]) }, items: { ...input.items, ...((input.supplements?.verifiedItems ?? {}) as Mark4Input["items"]) } };
  let stock = { ...(input.materialSupply?.stock.byItem ?? input.opening.stock) };
  let room = Math.max(0, model.summary.storageLimitLitres - model.summary.openingStorageLitres);
  const snapshotSources = model.sources.filter(s => /stock|dispatch|tank|oil|order|oms|ecom|material/i.test(`${s.id} ${s.label}`));
  const sourceGaps = snapshotSources.filter(s => !s.ok || !recent(s.asOf, now, /tank|oil/i.test(`${s.id} ${s.label}`) ? 86400 : 300));
  const limitations: string[] = [];
  if (model.meta.feedStatus !== "live") limitations.push(model.meta.feedError || "Some planning sources are stale or incomplete.");
  for (const source of sourceGaps) limitations.push(`${source.label}: ${source.ok ? "older source reading" : "source unavailable"}${source.asOf ? ` (${source.asOf})` : "; no source time"}.`);
  if (!input.materialSupply?.stock.asOf || !recent(input.materialSupply.stock.asOf, now, 300)) limitations.push("Material stock is not a fresh five-minute reading; confirm the available balance before changing a run.");
  if (model.demandBook.coverage !== "complete") limitations.push("The order book has incomplete coverage; an unseen urgent order can change the priority.");
  if (snapshotSources.some(s => /tank/i.test(`${s.id} ${s.label}`))) limitations.push("Tank stock uses the latest manual dip, not a continuous sensor. Confirm oil before the next batch.");
  if (!factory.complete || factory.lines.some(line => line.coverage !== "reported")) limitations.push("Factory coverage is partial; unreported lines may also be consuming these materials.");
  if (!recent(input.dispatch_aging?.asOf, now, 300)) limitations.push("Warehouse space uses the latest recorded stock/backlog. Confirm actual free space; no future truck departure is credited.");
  if (model.meta.startDate !== date || model.meta.feedStatus === "seed") limitations.push("The planning input is not today's live input; no ready-now quantity can be verified.");
  const basedOn: ShiftAdvice["basedOn"] = [{ source: "Factory live-status read", asOf: factory.asOf, status: factoryFresh ? "fresh" : "unavailable or stale" }, ...snapshotSources.map(s => ({ source: s.label, asOf: s.asOf, status: s.ok ? "source reading" : "unavailable" }))];
  // Current FG/net orders already include recorded production. MES is used only
  // against the preserved daily plan, never subtracted again from net orders.
  const observedSinceCapture = (line: string, code: string): number | null => {
    const currentLine = factory.lines.find(l => l.line === line);
    if (!today || currentLine?.coverage !== "reported") return null;
    const observed = currentLine.runs.filter(r => r.date === date && same(r.code, code));
    if (observed.some(r => r.producedPieces === null)) return null;
    if (baseline?.captureKind === "start_of_day") return observed.reduce((n, r) => n + r.producedPieces!, 0);
    const atCapture = baseline?.factoryAtCapture?.lines.find(l => l.line === line);
    if (!atCapture || !(atCapture.coverage === "reported" || (atCapture.coverage === "unreported" && atCapture.runs.length === 0 && baseline?.factoryAtCapture?.complete === true))) return null;
    const prior = atCapture.runs.filter(r => same(r.code, code));
    if (prior.some(r => r.pieces === null || !observed.some(o => o.id === r.id))) return null;
    let delta = 0;
    for (const run of observed) {
      const saved = prior.find(r => r.id === run.id)?.pieces ?? 0;
      if (run.producedPieces! < saved) return null; // Source correction/reset needs reconciliation.
      delta += run.producedPieces! - saved;
    }
    return delta;
  };
  const baselineRemaining = (line: string, p: Product): number | null => {
    const scheduled = baseline?.day.runs.filter(r => r.line === line && same(r.code, p.code));
    if (!scheduled?.length) return null;
    const made = observedSinceCapture(line, p.code);
    return made === null ? null : Math.max(0, scheduled.reduce((n, r) => n + r.pieces, 0) - made);
  };
  // Use the same eligible, canonical order rows and FG allocation as the engine.
  // Gross overdue demand is not urgent production when existing FG covers it.
  const netOrders = normalizeProducts(preparedInput).orders;
  const fg = Object.fromEntries(products.map(p => [p.code, p.fgPieces]));
  for (const order of netOrders) {
    const covered = Math.min(fg[order.code] ?? 0, order.remaining);
    fg[order.code] = (fg[order.code] ?? 0) - covered;
    order.remaining -= covered;
  }
  const exactDue = (p: Product): string | null => netOrders.filter(o => o.code === p.code && o.remaining > 0 && o.is_exact_sku_due === true && o._src !== "ECOM-PO" && o.due <= date && /^\d{4}-\d{2}-\d{2}$/.test(o.due)).map(o => o.due).sort()[0] ?? null;
  const requiredLeft = Object.fromEntries(products.map(p => [p.code, p.requiredPieces]));
  const confirmedLeft = Object.fromEntries(products.map(p => [p.code, p.confirmedUncoveredPieces]));
  const exactLeft = Object.fromEntries(products.map(p => [p.code, netOrders.filter(o => o.code === p.code && o.is_exact_sku_due === true && o._src !== "ECOM-PO" && o.due <= date).reduce((n, o) => n + o.remaining, 0)]));
  const candidates = model.days.find(d => d.date === date)?.runs ?? [];
  const active = (line: FactoryLine) => line.runs.filter(r => r.date === date && r.activeSegment?.isActive && !r.activeSegment.endedAt && r.liveStatus === "RUNNING");
  // Reserve continuing machines first, then stopped lines, so advice does not
  // promise the same bottles or godown space independently to six machines.
  const orderedLines = [...LINE_IDS].sort((a, b) => Number(factory.lines.find(l => l.line === b)?.status === "RUNNING") - Number(factory.lines.find(l => l.line === a)?.status === "RUNNING"));
  const rows = orderedLines.map(line => {
    const actual = factory.lines.find(l => l.line === line) ?? unavailableFactory("Line not reported", now).lines.find(l => l.line === line)!;
    const running = active(actual), current = running.length === 1 ? running[0] : null;
    const p = identity(current?.code ?? null);
    const validEvent = running.every(r => r.sourceUpdatedAt && Number.isFinite(Date.parse(r.sourceUpdatedAt)) && Date.parse(r.sourceUpdatedAt) <= now + 30000 && r.activeSegment?.startedAt && Number.isFinite(Date.parse(r.activeSegment.startedAt)) && Date.parse(r.activeSegment.startedAt) <= now + 30000);
    const verified = factoryFresh && actual.coverage === "reported" && actual.status !== "UNKNOWN" && validEvent && (actual.status === "RUNNING" ? running.length === 1 : running.length === 0);
    const plannedRuns = baseline?.day.runs.filter(r => r.line === line) ?? [];
    const match = !baseline || !verified || (actual.status === "RUNNING" && !current?.code) ? "unverifiable" as const : !plannedRuns.length ? "not_planned" as const : current ? plannedRuns.some(r => same(current.code, r.code)) ? "matches" as const : "different" as const : "different" as const;
    const plannedProgress = plannedRuns.map(run => {
      const madePieces = observedSinceCapture(line, run.code);
      return { code: run.code, madePieces, remainingPieces: madePieces === null ? null : Math.max(0, run.pieces - madePieces) };
    });
    const checks = [...limitations];
    let action: ShiftAdvice["action"] = "cannot_verify", title = "Cannot verify this machine", reason = !factoryFresh ? "The factory status is missing, stale or from another day. Check the line before acting." : "This line has no single reliable live status. Ask the floor operator to confirm it.";
    let candidate: ShiftCandidate | null = null;
    const choices = candidates.filter(r => r.line === line).map(r => products.find(p => p.code === r.code)).filter((p): p is Product => !!p);
    for (const product of products) if (!choices.includes(product) && product.requiredPieces > 0 && product.eligibility[line]?.allowed) choices.push(product);
    if (p && !choices.includes(p)) choices.unshift(p);
    choices.sort((a, b) => Number(b === p) - Number(a === p));
    const urgent = choices.filter(c => c !== p && exactDue(c) && (!p || !exactDue(p) || exactDue(c)! < exactDue(p)!));
    if (urgent.length) choices.unshift(...urgent.sort((a, b) => exactDue(a)!.localeCompare(exactDue(b)!)));
    const seen = new Set<string>();
    let hold: string | null = room <= 0 ? "The recorded godown has no free space. Release space through an actual dispatch before adding production." : null;
    for (const choice of choices) {
      // Unavailable/unverified machines cannot reserve a hypothetical run ahead of healthy lines.
      if (!verified || actual.status === "BREAKDOWN" || actual.status === "PAUSED" || actual.status === "UNKNOWN") break;
      if (seen.has(choice.code)) continue; seen.add(choice.code);
      if (!choice.eligibility[line]?.allowed || choice.exclusionReason || choice.conditionalRecipe) continue;
      const rate = rateFor(preparedInput, choice, line);
      if (!rate || model.meta.startDate !== date || model.meta.feedStatus === "seed") continue;
      const remaining = baselineRemaining(line, choice);
      if (remaining === 0) { if (choice === p) hold = "The recorded output has reached this product's saved daily quantity. Review remaining orders before extending it."; continue; }
      const continuing = verified && !!current && p?.code === choice.code;
      // Whole sales units can make an exact one-hour limit fractional (for example a 7-bottle combo).
      // Round a new campaign up to its first complete viable unit; display its actual duration.
      const nextBatchPieces = continuing ? rate.effectivePiecesPerHour : Math.ceil(rate.effectivePiecesPerHour * MIN_NEW_CAMPAIGN_HOURS - 1e-7);
      const max = Math.min(nextBatchPieces, requiredLeft[choice.code] ?? 0, remaining ?? Infinity, room / choice.packLitres);
      const qty = feasible(choice, max, stock, preparedInput);
      if (qty < 1) {
        const failed = trial(choice, 1, stock, preparedInput).failure;
        if (failed && !hold) hold = `Recorded stock cannot cover ${choice.name}: ${preparedInput.items[failed.code]?.name ?? failed.code} is short. Confirm a usable receipt before the next batch.`;
        continue;
      }
      const productiveHours = qty / rate.effectivePiecesPerHour;
      if (!campaignEligible(productiveHours, continuing)) {
        if (!hold) hold = `The feasible next batch for ${choice.name} is too short for a new campaign under the provisional minimum. Its demand and materials remain available; review a larger batch or continue the verified current product.`;
        continue;
      }
      const setupBasis: ShiftCandidate["setupBasis"] = continuing ? "continuation" : current && p ? "product_change" : "unknown";
      const setupHours = setupBasis === "continuation" ? 0 : setupBasis === "product_change" ? PRODUCT_CHANGE_SETUP_HOURS : null;
      const attempt = trial(choice, qty, stock, preparedInput);
      const litres = qty * choice.packLitres;
      candidate = { line, code: choice.code, product: choice.name, pieces: qty, litres, hours: productiveHours, dayHours: productiveHours, nightHours: 0, setupHours, setupBasis, value: choice.valuePerLitre === null ? null : choice.valuePerLitre * litres, confirmedPieces: Math.min(qty, confirmedLeft[choice.code] ?? 0), forecastPieces: Math.max(0, qty - (confirmedLeft[choice.code] ?? 0)), reason: `${continuing ? "Up to one production hour of the verified continuing campaign" : "Approximately one production hour in whole sales units"}, checked against recorded on-hand stock and free space, shared across the displayed lines. No expected arrival or future dispatch is credited. Confirm shift time and changeover with the operator.`, rate, labourCost: null, exactOrderPieces: Math.min(qty, exactLeft[choice.code] ?? 0), allocatedOrderPieces: 0, conditionalRecipe: false, conditionalSupply: checks.length > 0, materials: Object.entries(attempt.used).map(([code, quantity]) => ({ code, quantity, unit: input.items[code]?.uom ?? "pieces" })) };
      stock = attempt.next; room -= litres;
      requiredLeft[choice.code] = Math.max(0, requiredLeft[choice.code] - qty);
      confirmedLeft[choice.code] = Math.max(0, confirmedLeft[choice.code] - qty);
      exactLeft[choice.code] = Math.max(0, exactLeft[choice.code] - qty);
      if (verified) {
        if (current && p && choice.code === p.code) { action = "continue"; title = "Continue; check again at changeover"; reason = `${match === "matches" ? "This product is in the saved plan." : "This differs from the saved plan, but a difference alone does not make it wrong."} Its machine route is supported and recorded stock covers the suggested next batch.`; }
        else if (current && !p) { action = "investigate"; title = "Confirm the running SKU first"; reason = "The factory's current SKU is not mapped to a verified planner recipe. The suggestion below is conditional; its product name is not enough to establish a match."; }
        else if (current && p && !p.eligibility[line]?.allowed) { action = "investigate"; title = "Check this machine/product combination"; reason = `The recorded product's route needs review: ${p.eligibility[line]?.reason ?? "No verified route."} Ask the floor operator before changing anything.`; }
        else { action = "switch_next"; title = current ? "Review this for the next changeover" : "Next run to prepare"; reason = exactDue(choice) ? `Exact SKU orders are due ${exactDue(choice)}. Recorded on-hand stock and free space cover this next batch${current ? "; review it after the current batch, allowing changeover time" : "; confirm the machine is available before starting"}.` : "This product has a supported machine route and remaining demand in the current planner input. Prepare this next batch after confirming the available balance and remaining shift time."; }
      }
      let demandTaken = qty;
      for (const order of netOrders.filter(o => o.code === choice.code)) {
        const used = Math.min(order.remaining, demandTaken); order.remaining -= used; demandTaken -= used;
        if (demandTaken <= 0) break;
      }
      break;
    }
    if (verified && !candidate) {
      action = "investigate"; title = "Check before the next batch";
      reason = hold ?? (p && !p.eligibility[line]?.allowed ? p.eligibility[line]?.reason ?? "No verified route." : "No next batch is verified against the recorded stock, free space and saved daily progress. Review materials, remaining orders and the floor situation.");
    }
    if (actual.status === "BREAKDOWN" || actual.status === "PAUSED") { action = "investigate"; title = actual.status === "BREAKDOWN" ? "Resolve the breakdown first" : "Confirm why this line is paused"; reason = "The factory reports this line unavailable. Any product below is preparation only; the operator must confirm restart readiness."; }
    if (!verified) { checks.unshift(reason); action = "cannot_verify"; title = "Cannot verify this machine"; }
    if (candidate && !current) checks.push("Current campaign/changeover and remaining operator shift hours need floor confirmation.");
    if (candidate && baselineRemaining(line, identity(candidate.code)!) === null) checks.push("No reliable saved-day completion limit for this SKU; confirm today's output before extending the run.");
    return { line, actual, plannedRuns, plannedProgress, match, advice: { action, title, reason, candidate, conditional: checks.length > 0 || !verified, basedOn, limitations: [...new Set(checks)] } };
  });
  return { version: 1, date, generatedAt: new Date(now).toISOString(), refreshSeconds: 60, factory, baseline, baselineError, rows: rows.sort((a, b) => LINE_IDS.indexOf(a.line) - LINE_IDS.indexOf(b.line)) };
}
