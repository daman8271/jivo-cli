"use client";

// The footer says what is measured and what is a guess — and it says it in the
// publisher's OWN words, read out of plan/honesty.json every three minutes.
// Mark 2 typed this list into JSX; when the engine changed, the footer lied.

import { asHonesty, asState, useLive } from "../lib/live";
import { plainNote } from "../lib/labels";
import { AsOf, FreshnessKey } from "./Freshness";
import { Pill } from "./Card";
import { PUBLISHER, FIXTURES } from "../lib/live";

export default function Footer() {
  const live = useLive(["honesty", "state"]);
  const h = asHonesty(live.honesty);
  const st = asState(live.state);

  return (
    <footer className="mx-auto mt-10 max-w-7xl space-y-3 border-t border-zinc-900 px-5 py-8 text-xs text-zinc-500">
      <div className="font-medium text-zinc-300">
        {h?.forward_rule ?? "Only today is read from the plant. Everything after it is worked out by the computer."}
      </div>

      {h && (
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-wider text-zinc-500">
              Measured — real <AsOf rec={live.honesty} />
            </div>
            <ul className="space-y-1">
              {h.measured.map((m) => (
                <li key={m} className="flex items-start gap-2">
                  <Pill tone="green">real</Pill>
                  <span className="text-zinc-400">{plainNote(m)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">
              Our guess — not measured ({h.assumed.length})
            </div>
            <ul className="max-h-56 space-y-1 overflow-y-auto pr-2">
              {h.assumed.map((a, i) => (
                <li key={`${i}-${a.slice(0, 24)}`} className="flex items-start gap-2">
                  <Pill tone="amber">guess</Pill>
                  <span className="text-zinc-400">{plainNote(a)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {h?.warnings && h.warnings.length > 0 && (
        <details className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
          <summary className="cursor-pointer text-zinc-400">
            Things the planner wants you to know before quoting a number ({h.warnings.length})
          </summary>
          <ul className="mt-2 space-y-1.5">
            {h.warnings.map((w, i) => (
              <li key={i} className="text-zinc-400">
                {plainNote(w)}
              </li>
            ))}
          </ul>
        </details>
      )}

      {st?.warnings && st.warnings.length > 0 && (
        <div className="text-amber-300/70">This cycle: {st.warnings.map(plainNote).join(" · ")}</div>
      )}

      <FreshnessKey />

      <div className="text-zinc-600">
        Nothing on this page is typed in by hand and nothing is baked into the build. Every figure is fetched from{" "}
        <span className="text-zinc-500">{FIXTURES ? "the saved copies in public/fixtures" : PUBLISHER}</span> in your
        browser, every three minutes. {h?.august_calibration?.note ?? ""}
      </div>
    </footer>
  );
}
