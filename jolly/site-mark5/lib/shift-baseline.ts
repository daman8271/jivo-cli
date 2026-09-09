import { createHash, randomUUID } from "node:crypto";
import { mkdir, writeFile, link, unlink, readFile } from "node:fs/promises";
import path from "node:path";
import { buildModel, validateInput } from "./model.ts";
import { istDate, recent, validateBaseline } from "./shift-validation.ts";
import type { ShiftBaseline, FactoryNow } from "./shift-types.ts";
import type { Mark4Input } from "./types.ts";
export async function captureBaseline(input: Mark4Input, directory: string, now = Date.now(), factory?: FactoryNow): Promise<{ baseline: ShiftBaseline; created: boolean }> {
  const date = istDate(now), destination = path.join(directory, `${date}.json`);
  try { const saved: unknown = JSON.parse(await readFile(destination, "utf8")); validateBaseline(saved, now); return { baseline: saved, created: false }; }
  catch (e) { if ((e as NodeJS.ErrnoException).code !== "ENOENT") throw e; }
  validateInput(input);
  const stamp = input.meta.state_collected_at ?? input.meta.frozen_at;
  if (input.meta.as_of.slice(0, 10) !== date || !recent(stamp, now, 900)) throw new Error("Refusing to save a daily plan from an old, missing or future input timestamp.");
  const status = input.sources.every(s => s.ok) ? "live" : "stale";
  const model = buildModel(input, undefined, status, status === "stale" ? "Some sources were unavailable when this daily plan was captured." : null, false);
  const day = model.days.find(d => d.date === date);
  if (!day) throw new Error("Today's day is missing from the model.");
  const inputRevision = createHash("sha256").update(JSON.stringify(input)).digest("hex");
  const baseline: ShiftBaseline = { version: 1, id: `${date}:${inputRevision}`, date, timeZone: "Asia/Kolkata", capturedAt: new Date(now).toISOString(), inputAsOf: input.meta.as_of, inputRevision, engineVersion: model.meta.engine, captureKind: "first_capture", scenario: model.scenario, day, sources: model.sources, feedStatus: model.meta.feedStatus };
  if (factory?.ok && factory.date === date && factory.asOf && recent(factory.asOf, now)) {
    baseline.factoryAtCapture = { asOf: factory.asOf, complete: factory.complete, lines: factory.lines.map(line => ({ line: line.line, coverage: line.coverage, runs: line.runs.filter(run => run.date === date).map(run => ({ id: run.id, code: run.code, pieces: run.producedPieces })) })) };
  }
  validateBaseline(baseline, now);
  await mkdir(directory, { recursive: true });
  const temporary = path.join(directory, `.${date}-${randomUUID()}.tmp`);
  await writeFile(temporary, JSON.stringify(baseline), { flag: "wx", mode: 0o644 });
  try {
    // An atomic hard-link publishes complete bytes and fails if another worker
    // already saved today. Never truncate or replace the agreed daily record.
    await link(temporary, destination);
    return { baseline, created: true };
  } catch (e) {
    if ((e as NodeJS.ErrnoException).code !== "EEXIST") throw e;
    const saved: unknown = JSON.parse(await readFile(destination, "utf8")); validateBaseline(saved, now);
    return { baseline: saved, created: false };
  } finally { await unlink(temporary); }
}
