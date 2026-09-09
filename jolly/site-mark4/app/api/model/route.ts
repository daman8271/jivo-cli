import { modelCacheKey } from "../../../lib/model-cache.ts";
import { ScenarioInputError } from "../../../lib/evidence.ts";
import { readBounded } from "../../../lib/bounded-body.ts";
import { NextResponse } from "next/server";
import { buildModel, validateScenario } from "../../../lib/model.ts";
import { loadInput } from "../../../lib/load-input.ts";
import type { Mark4Model, Scenario } from "../../../lib/types.ts";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;
let buildTimes: number[] = [];
const cache = new Map<string, { model: Mark4Model; at: number }>();
const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };

async function respond(scenario: Scenario) {
  try {
    const loaded = await loadInput();
    const key = modelCacheKey(loaded.input, loaded.status, loaded.error, scenario);
    let result = cache.get(key);
    if (!result || Date.now() - result.at > 180000) {
      buildTimes = buildTimes.filter(t => Date.now() - t < 60000);
      if (buildTimes.length >= 12) return NextResponse.json({ error: "Planner is busy. Please retry in a minute." }, { status: 429, headers });
      buildTimes.push(Date.now());
      result = { model: buildModel(loaded.input, scenario, loaded.status, loaded.error), at: Date.now() };
      if (cache.size >= 8) cache.delete(cache.keys().next().value!);
      cache.set(key, result);
    }
    return NextResponse.json(result.model, { headers });
  } catch (error) {
    if (error instanceof ScenarioInputError) return NextResponse.json({ error: error.message }, { status: 400, headers });
    return NextResponse.json({ error: "The planning input could not be validated. Please retry after the next source refresh." }, { status: 503, headers });
  }
}

export async function GET() { return respond(validateScenario(undefined)); }

export async function POST(request: Request) {
  if (Number(request.headers.get("content-length") ?? 0) > 2048) return NextResponse.json({ error: "Scenario is too large." }, { status: 413, headers });
  try {
    const raw = await readBounded(request.body, 2048);
    if (raw.length > 2048) return NextResponse.json({ error: "Scenario is too large." }, { status: 413, headers });
    const scenario = validateScenario(JSON.parse(raw));
    return respond(scenario);
  } catch (error) {
    return NextResponse.json({ error: "Invalid scenario. Use a supported night line, boolean supply/recipe switches and valid arrival dates. Machine speeds are fixed by the approved table." }, { status: 400, headers });
  }
}
