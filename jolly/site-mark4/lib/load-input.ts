import { readBounded } from "./bounded-body.ts";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { validateInput } from "./model.ts";
import type { Mark4Input, Mark4Model } from "./types.ts";

const FEED = "https://mark4-astha.srv1685505.hstgr.cloud/inputs.json";
const MAX_INPUT_BYTES = 10000000;
type Loaded = { input: Mark4Input; status: Mark4Model["meta"]["feedStatus"]; error: string | null };
let lastGood: { input: Mark4Input; checkedAt: number; retained: boolean } | null = null;
let pending: Promise<Loaded> | null = null;

function currentStatus(input: Mark4Input): Mark4Model["meta"]["feedStatus"] {
  const stamp = input.meta.state_collected_at ?? input.meta.frozen_at ?? input.meta.as_of;
  const age = Date.now() - Date.parse(stamp);
  if (input.materialSupply && (!input.materialSupply.coverage.complete || input.materialSupply.coverage.datasets.some(dataset => !dataset.ok || !dataset.complete || !dataset.asOf || !Number.isFinite(Date.parse(dataset.asOf)) || Date.now() - Date.parse(dataset.asOf) > Math.max(dataset.expectedRefreshSeconds * 2, 300) * 1000))) return "stale";
  return Number.isFinite(age) && age >= -300000 && age < 15 * 60000 && input.sources.every(s => { if (!s.ok) return false; if (/stock|bom|machine|packaging/i.test(`${s.id} ${s.label}`)) return s.asOf !== null && Date.now() - Date.parse(s.asOf) < 2 * 3600000; return true; }) ? "live" : "stale";
}

export async function loadInput(): Promise<Loaded> {
  if (lastGood && Date.now() - lastGood.checkedAt < 15000) return { input: lastGood.input, status: lastGood.retained ? "stale" : currentStatus(lastGood.input), error: lastGood.retained ? "Upstream input refresh failed; the publisher retained its last good snapshot." : currentStatus(lastGood.input) === "stale" ? "Input sources are stale or incomplete; this is a conditional scenario." : null };
  if (pending) return pending;
  pending = (async () => {
    try {
      const response = await fetch(FEED, { signal: AbortSignal.timeout(7000), cache: "no-store", redirect: "error" });
      if (!response.ok || Number(response.headers.get("content-length") ?? 0) > MAX_INPUT_BYTES) throw new Error("Feed unavailable.");
      const raw = await readBounded(response.body, MAX_INPUT_BYTES);
      if (raw.length > MAX_INPUT_BYTES) throw new Error("Feed too large.");
      const input: unknown = JSON.parse(raw); validateInput(input);
      const retained = response.headers.get("x-mark4-retained-last-good") === "true" || response.headers.get("x-mark4-source-status") === "error";
      lastGood = { input, checkedAt: Date.now(), retained };
      return { input, status: retained ? "stale" : currentStatus(input), error: retained ? "Upstream input refresh failed; the publisher retained its last good snapshot." : currentStatus(input) === "stale" ? "Input sources are stale or incomplete; this is a conditional scenario." : null };
    } catch {
      if (lastGood) return { input: lastGood.input, status: "stale" as const, error: "Live input refresh failed. Showing the last valid input with its original source dates." };
      const seed: unknown = JSON.parse(await readFile(path.join(process.cwd(), "data", "seed.json"), "utf8"));
      validateInput(seed);
      return { input: seed, status: "seed" as const, error: "Live input is unavailable. Showing the saved dated seed; these are not fresh observations." };
    } finally { pending = null; }
  })();
  return pending;
}
