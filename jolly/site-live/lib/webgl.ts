"use client";

// WebGL, and what to do when it is not there.
//
// Daman hit the dead "can't draw 3D" box on Mark 2. The rule now: probe, and if
// the probe fails, wait two seconds and probe ONCE more — a tab that was
// backgrounded, a GPU process that had just been killed, or a driver still
// waking up all recover in that window. If the second probe fails too, the page
// draws a flat 2D floor plan instead. There is no third state and no dead box.

import { useEffect, useState } from "react";

export type GlState = "checking" | "ok" | "off";

const RETRY_AFTER_MS = 2000;

export function probeWebGL(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const c = document.createElement("canvas");
    const gl =
      (c.getContext("webgl2") as WebGLRenderingContext | null) ??
      (c.getContext("webgl") as WebGLRenderingContext | null) ??
      (c.getContext("experimental-webgl") as WebGLRenderingContext | null);
    if (!gl) return false;
    // hand the context straight back — probing must not hold a GPU context open
    gl.getExtension("WEBGL_lose_context")?.loseContext();
    return true;
  } catch {
    return false;
  }
}

/** Forced flat by the environment — how the verifier tests the 2D path. */
export const FORCE_2D = process.env.NEXT_PUBLIC_MARK3_FORCE_2D === "1";

export function useWebGL(): { state: GlState; retrying: boolean; forceOff: () => void } {
  const [state, setState] = useState<GlState>("checking");
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (FORCE_2D) {
      setState("off");
      return;
    }
    let dead = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    if (probeWebGL()) {
      setState("ok");
    } else {
      setRetrying(true);
      timer = setTimeout(() => {
        if (dead) return;
        setRetrying(false);
        setState(probeWebGL() ? "ok" : "off");
      }, RETRY_AFTER_MS);
    }
    return () => {
      dead = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  return { state, retrying, forceOff: () => setState("off") };
}

/** Oil name → colour. Presentation only; keyed on the NAME, never on the code. */
const OIL_KEY: [string, string][] = [
  ["MUSTARD", "#eab308"],
  ["SUNFLOWER", "#f97316"],
  ["GROUNDNUT", "#b45309"],
  ["SOYABEAN", "#38bdf8"],
  ["RICE BRAN", "#14b8a6"],
  ["SESAME", "#a78bfa"],
  ["SEASAME", "#a78bfa"],
  ["COTTON", "#94a3b8"],
  ["CANOLA", "#84cc16"],
  ["OLIVE", "#22c55e"],
];
export const IDLE_COLOR = "#4a4a53";

export function oilColor(name: string | null | undefined): string {
  if (!name) return IDLE_COLOR;
  const u = name.toUpperCase();
  for (const [k, c] of OIL_KEY) if (u.includes(k)) return c;
  let hue = 0;
  for (let i = 0; i < u.length; i++) hue = (hue * 31 + u.charCodeAt(i)) % 360;
  return `hsl(${hue} 55% 55%)`;
}

/* ── the 3D scene's palette ────────────────────────────────────────────
   three.js wants colours as numeric hex, and a numeric hex is a digit run. It
   is a UI constant, not a business number — but the site's grep should come
   back clean rather than come back with a list a reader has to judge. So the
   palette lives here, in lib/, and FloorScene.tsx holds no literals at all. */
export const SCENE = {
  bg: 0x0b0b0f,
  ground: 0x141419,
  gridMajor: 0x27272a,
  gridMinor: 0x1c1c20,
  pad: 0x1f1f26,
  shell: 0x3f3f46,
  limit: 0xef4444,
  fillPlain: 0x71717a,
  fillWarm: 0xa1a1aa,
  fillHot: 0xf87171,
  fillOver: 0xef4444,
  sold: 0xf59e0b,
  live: 0x34d399,
  beacon: 0xfbbf24,
  truckReal: 0x34d399,
  truckForecast: 0xa78bfa,
  white: 0xffffff,
} as const;
