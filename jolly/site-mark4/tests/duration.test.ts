import test from "node:test";
import assert from "node:assert/strict";
import { formatDuration, formatSetupDuration } from "../lib/duration.ts";

test("short filling runs show seconds instead of zero hours", () => {
  assert.equal(formatDuration(45 / 4800), "34 s");
  assert.equal(formatDuration(10 / 2100), "17 s");
  assert.equal(formatDuration(0.5 / 3600), "<1 s");
});

test("durations retain minutes and normalize rounding across units", () => {
  assert.equal(formatDuration(1.214), "1 h 13 min");
  assert.equal(formatDuration(90 / 3600), "1 min 30 s");
  assert.equal(formatDuration(59.8 / 3600), "1 min");
  assert.equal(formatDuration(3599.8 / 3600), "1 h");
  assert.equal(formatDuration(1.999), "2 h");
});

test("zero is distinct from an unread or invalid duration", () => {
  assert.equal(formatDuration(0), "0 h");
  for (const hours of [null, undefined, NaN, Infinity, -1]) {
    assert.equal(formatDuration(hours), "Not read");
  }
});

test("an unknown opening setup is disclosed instead of appearing measured at zero", () => {
  assert.equal(formatSetupDuration({ setupHours: 0, reason: "first horizon campaign; opening setup is unknown and provisionally zero." }), "Unknown · 0 h assumed");
  assert.equal(formatSetupDuration({ setupHours: 0, reason: "same-product continuation; no additional setup charged." }), "0 h");
  assert.equal(formatSetupDuration({ setupHours: 1, reason: "product change" }), "1 h");
});
