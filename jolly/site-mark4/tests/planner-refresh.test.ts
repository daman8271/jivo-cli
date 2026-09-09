import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";

test("background tick cannot overwrite an in-flight user scenario, and older response cannot unlock a newer request", async () => {
  // Execute the actual callbacks with deferred HTTP responses, without mounting React.
  const source = fs.readFileSync(new URL("../components/Planner.tsx", import.meta.url), "utf8");
  const start = source.indexOf("  const load = useCallback");
  const loadCode = source.slice(start, source.indexOf("  useEffect(() => {", start));
  const timerCode = source.slice(source.indexOf("    const timer = setInterval"), source.indexOf("    return () => clearInterval(timer)"));
  const requestId = { current: 0 }, inFlightRequest: { current: number | null } = { current: null };
  const scenarioRef = { current: { includePackagingEstimates: true } };
  type Scenario = { includePackagingEstimates: boolean };
  type Response = { ok: boolean; json: () => Promise<unknown> };
  const requests: { options: { body: string }; resolve: (value: Response) => void }[] = [];
  const saved: Scenario[] = [];
  let interval = () => {};
  const load = new Function("useCallback", "requestId", "inFlightRequest", "scenarioRef", "setBusy", "setError", "setModel", "setRun", "setLoading", "window", "fetch", "localStorage", ts.transpile(loadCode, { target: ts.ScriptTarget.ES2022 }) + "; return load;")(
    (callback: unknown) => callback, requestId, inFlightRequest, scenarioRef,
    () => {}, () => {}, () => {}, () => {}, () => {},
    { setTimeout: () => 1, clearTimeout: () => {} },
    (_url: string, options: { body: string }) => new Promise<Response>(resolve => requests.push({ options, resolve })),
    { setItem: (_key: string, value: string) => saved.push(JSON.parse(value)) },
  ) as (scenario: Scenario) => Promise<void>;
  new Function("setInterval", "document", "inFlightRequest", "scenarioRef", "load", timerCode)(
    (callback: () => void) => { interval = callback; }, { visibilityState: "visible" }, inFlightRequest, scenarioRef, load,
  );
  const success = (scenario: Scenario): Response => ({ ok: true, json: async () => ({ scenario, days: [], lines: [], planningSpeeds: [], summary: {}, meta: {} }) });
  const manual = load({ includePackagingEstimates: false });
  interval();
  assert.equal(requests.length, 1, "background refresh must wait for the user's choice");
  requests[0].resolve(success({ includePackagingEstimates: false })); await manual;
  assert.equal(saved.at(-1)?.includePackagingEstimates, false);
  assert.equal(inFlightRequest.current, null);
  interval();
  assert.equal(requests.length, 2);
  assert.equal(JSON.parse(requests[1].options.body).includePackagingEstimates, false);
  const newer = load({ includePackagingEstimates: true });
  requests[1].resolve(success({ includePackagingEstimates: false }));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(inFlightRequest.current, 3, "older response must leave newer request locked");
  requests[2].resolve(success({ includePackagingEstimates: true })); await newer;
  assert.equal(saved.at(-1)?.includePackagingEstimates, true);
  assert.equal(inFlightRequest.current, null);
});
