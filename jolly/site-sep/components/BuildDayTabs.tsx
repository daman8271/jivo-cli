"use client";

// Day picker for the run list. The day sections are server-rendered and passed
// in as children — this component only decides which one is visible on screen.
// Print behaviour: whatever is visible prints. One day selected = that day's
// sheet; "All days" = the whole month, one day per page (see the page's print CSS).

import { Children, useState, type ReactNode } from "react";

export type BuildDayMeta = {
  n: number; // 1-based day index (matches /days/{n})
  dom: number; // day of month
  wd: string; // weekday initial
  working: boolean;
  litres: number;
  label: string; // "Tuesday 1 Sep"
};

const inr = (n: number) => Math.round(n).toLocaleString("en-IN");

export default function BuildDayTabs({ days, children }: { days: BuildDayMeta[]; children: ReactNode }) {
  const kids = Children.toArray(children);
  const [sel, setSel] = useState<number>(days[0]?.n ?? 1); // 0 = all days

  function pick(n: number) {
    setSel(n);
    if (typeof document !== "undefined") {
      document.getElementById("bl-days-top")?.scrollIntoView({ block: "start" });
    }
  }

  return (
    <div>
      <div className="bl-noprint sticky top-14 z-40 -mx-5 px-5 py-2 bg-zinc-950/95 backdrop-blur border-b border-zinc-900">
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          <button
            onClick={() => pick(0)}
            className={`shrink-0 px-2.5 py-1.5 rounded-md text-xs border transition-colors ${
              sel === 0
                ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:bg-zinc-800"
            }`}
          >
            All days
          </button>
          {days.map((d) => (
            <button
              key={d.n}
              onClick={() => pick(d.n)}
              title={d.working ? `${d.label} — ${inr(d.litres)} L to make` : `${d.label} — factory closed`}
              className={`shrink-0 w-9 py-1 rounded-md text-center border transition-colors ${
                sel === d.n
                  ? "bg-amber-500/20 border-amber-500/40"
                  : "bg-zinc-900/60 border-zinc-800 hover:bg-zinc-800"
              } ${d.working ? "" : "opacity-40"}`}
            >
              <span className={`block text-[9px] leading-none ${sel === d.n ? "text-amber-300/80" : "text-zinc-600"}`}>
                {d.wd}
              </span>
              <span
                className={`block text-xs tabular-nums leading-tight ${
                  sel === d.n ? "text-amber-300 font-semibold" : "text-zinc-300"
                }`}
              >
                {d.dom}
              </span>
            </button>
          ))}
        </div>
        <div className="text-[10px] text-zinc-600 mt-1">
          To print: the day on screen prints by itself. Pick &ldquo;All days&rdquo; to print the whole month — one
          day per sheet.
        </div>
      </div>

      <div id="bl-days-top" className="scroll-mt-32">
        {days.map((d, i) => (
          <div key={d.n} className={`bl-page ${sel === 0 || sel === d.n ? "" : "hidden"}`}>
            {kids[i]}
          </div>
        ))}
      </div>
    </div>
  );
}
