import { NextResponse } from "next/server";
import { buildModel } from "../../../lib/model.ts";
import { loadInput } from "../../../lib/load-input.ts";
import { readBounded } from "../../../lib/bounded-body.ts";
import { buildShiftBoard, unavailableFactory } from "../../../lib/shift-board.ts";
import { validateFactory, validateBaseline } from "../../../lib/shift-validation.ts";
import type { FactoryNow, ShiftBaseline } from "../../../lib/shift-types.ts";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;
const FEED = "https://mark4-astha.srv1685505.hstgr.cloud";
let lastFactory: FactoryNow | null = null;
async function getJson(file: string) {
  const response = await fetch(`${FEED}/${file}`, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(7000) });
  if (!response.ok) throw new Error(`${file} unavailable (${response.status}).`);
  return JSON.parse(await readBounded(response.body, 2000000)) as unknown;
}
async function factoryNow(): Promise<FactoryNow> {
  try { const raw = await getJson("factory-now.json"); validateFactory(raw); if (raw.ok) lastFactory = raw; return raw; }
  catch { return lastFactory ? { ...lastFactory, ok: false, error: "Refresh failed. These are retained factory readings, not a new observation." } : unavailableFactory("Factory live status could not be read."); }
}
async function savedBaseline(): Promise<{ baseline: ShiftBaseline | null; error: string | null }> {
  try { const raw = await getJson("shift-baseline.json"); validateBaseline(raw); return { baseline: raw, error: null }; }
  catch { return { baseline: null, error: "Today's shared original plan has not been captured or could not be read. A browser scenario never replaces it." }; }
}
export async function GET() {
  const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
  try {
    const [loaded, factory, saved] = await Promise.all([loadInput(), factoryNow(), savedBaseline()]);
    const model = buildModel(loaded.input, undefined, loaded.status, loaded.error, false);
    return NextResponse.json(buildShiftBoard(loaded.input, model, factory, saved.baseline, saved.error), { headers });
  } catch { return NextResponse.json({ error: "The live comparison could not be built. Keeping the previous reading with its original time." }, { status: 503, headers }); }
}
