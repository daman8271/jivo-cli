import { NextResponse } from "next/server";
import { readBounded } from "../../../lib/bounded-body.ts";
import { istDate, validateFactory } from "../../../lib/shift-validation.ts";
import { validReviewDate, validateReviewBaseline } from "../../../lib/today-review-validation.ts";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;
const FEED = "https://mark4-astha.srv1685505.hstgr.cloud";
const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
export async function GET(request: Request) {
  const now = Date.now(), date = new URL(request.url).searchParams.get("date") || istDate(now);
  if (!validReviewDate(date, now)) return NextResponse.json({ error: "Choose a recorded date through today." }, { status: 400, headers });
  const prefix = date === istDate(now) ? "" : `review/${date}/`;
  async function read(file: string) {
    const response = await fetch(`${FEED}/${prefix}${file}`, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(7000) });
    if (!response.ok) throw new Error("Source unavailable");
    return JSON.parse(await readBounded(response.body, 2000000)) as unknown;
  }
  const [factory, baseline] = await Promise.allSettled([
    read("factory-now.json").then(value => { validateFactory(value); if (value.date !== date) throw new Error("Factory date mismatch"); return value; }),
    read("shift-baseline.json").then(value => { validateReviewBaseline(value, date, now); return value; }),
  ]);
  return NextResponse.json({ version: 1, date, generatedAt: new Date().toISOString(),
    factory: factory.status === "fulfilled" ? factory.value : null,
    factoryError: factory.status === "fulfilled" ? null : "The dated factory report could not be read. No output is assumed.",
    baseline: baseline.status === "fulfilled" ? baseline.value : null,
    baselineError: baseline.status === "fulfilled" ? null : "No readable saved plan exists for this date. Current plans and browser scenarios cannot replace it.",
  }, { headers });
}
