import { captureBaseline } from "../lib/shift-baseline.ts";
import { readBounded } from "../lib/bounded-body.ts";
import { validateFactory } from "../lib/shift-validation.ts";
import type { FactoryNow } from "../lib/shift-types.ts";
import { validateInput } from "../lib/model.ts";
const args = process.argv.slice(2);
const arg = (name: string) => { const i = args.indexOf(name); return i < 0 ? undefined : args[i + 1]; };
const feed = arg("--feed"), directory = arg("--directory");
if (!feed || !directory) throw new Error("Usage: capture_shift_baseline.ts --feed URL --directory DIRECTORY");
const response = await fetch(feed, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(10000) });
if (!response.ok || response.headers.get("x-mark4-retained-last-good") === "true" || response.headers.get("x-mark4-source-status") === "error") throw new Error("Refusing a failed or retained input feed.");
const input: unknown = JSON.parse(await readBounded(response.body, 10000000));
validateInput(input);
let factory: FactoryNow | undefined;
try {
  const factoryResponse = await fetch(new URL("factory-now.json", feed), { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(10000) });
  if (factoryResponse.ok) { const raw: unknown = JSON.parse(await readBounded(factoryResponse.body, 2000000)); validateFactory(raw); factory = raw; }
} catch { /* The baseline stays useful; since-save progress is explicitly unavailable without counters. */ }
const result = await captureBaseline(input, directory, Date.now(), factory);
process.stdout.write(JSON.stringify({ date: result.baseline.date, id: result.baseline.id, capturedAt: result.baseline.capturedAt, created: result.created }) + "\n");
