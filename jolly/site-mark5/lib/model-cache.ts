import { createHash } from "node:crypto";
import type { Mark4Input, Mark4Model, Scenario } from "./types.ts";

// Some source systems revise rows without advancing the enclosing snapshot clock.
// Cache the actual input content, not just meta.as_of or an advertised revision.
export function modelCacheKey(input: Mark4Input, status: Mark4Model["meta"]["feedStatus"], error: string | null, scenario: Scenario): string {
  return JSON.stringify([createHash("sha256").update(JSON.stringify(input)).digest("hex"), status, error, scenario]);
}
