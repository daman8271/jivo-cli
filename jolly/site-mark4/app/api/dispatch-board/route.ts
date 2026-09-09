import { NextResponse } from "next/server";
import { readBounded } from "../../../lib/bounded-body.ts";
import { validateDispatchFeed, validateStorageEvidence } from "../../../lib/dispatch-validation.ts";
import { dispatchStatus } from "../../../lib/dispatch-board.ts";
import type { DispatchFeed } from "../../../lib/dispatch-types.ts";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;
const origin = "https://mark4-astha.srv1685505.hstgr.cloud";
const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
let lastGood: DispatchFeed | null = null;
async function read(name: string, limit: number) {
  const response = await fetch(`${origin}/${name}`, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(10000) });
  if (!response.ok || Number(response.headers.get("content-length") ?? 0) > limit) throw new Error("Source unavailable");
  return { value: JSON.parse(await readBounded(response.body, limit)) as unknown, retained: response.headers.get("x-mark4-retained-last-good") === "true" || response.headers.get("x-mark4-source-status") === "error" };
}
export async function GET() {
  const [dispatch, storage] = await Promise.allSettled([read("dispatch-now.json", 15000000), read("storage-evidence.json", 2000000)]);
  const storageValue = storage.status === "fulfilled" ? validateStorageEvidence(storage.value.value) : null;
  try {
    if (dispatch.status === "rejected") throw dispatch.reason;
    const data = validateDispatchFeed(dispatch.value.value);
    if (data.ok) lastGood = data;
    const status = dispatch.value.retained ? "stale" : dispatchStatus(data);
    return NextResponse.json({ data, status, error: status === "fresh" ? null : "Source is stale or incomplete. These are the records read at the original source time, not a confirmed complete daily total.", storage: storageValue }, { headers });
  } catch {
    return NextResponse.json({ data: lastGood, status: lastGood ? "stale" : "unavailable", error: lastGood ? "Dispatch refresh failed. Last valid records retain their original timestamp." : "Actual dispatch could not be read. No zero or estimated total has been substituted.", storage: storageValue }, { headers });
  }
}
