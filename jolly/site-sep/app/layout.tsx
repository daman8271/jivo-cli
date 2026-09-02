import "./globals.css";
import Nav from "../components/Nav";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    default: "JIVO Mark 2 — September 2026 plan",
    template: "%s · JIVO Mark 2 — September 2026 plan",
  },
  description:
    "Forward production plan for JIVO Oil, September 2026 — a simulator's day-by-day plan (August backtest within a fraction of a percent), not a record. September has not happened.",
};

export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 min-h-screen">
        <Nav />
        <div className="border-b border-violet-500/20 bg-violet-500/5">
          <div className="max-w-7xl mx-auto px-5 py-1.5 text-xs text-violet-200/90">
            <span className="font-semibold">Plan, not record.</span> September 2026 has not happened. This is what the
            planner <em>would do</em>, day by day, produced by the simulator that backtested August to within a fraction
            of a percent. Forecast demand is marked FORECAST; every declared assumption is flagged in the data.
            WhatsApp messages are simulated drafts — nothing was sent, nobody replied.
          </div>
        </div>
        <main className="max-w-7xl mx-auto px-5 py-6">{children}</main>
        <footer className="max-w-7xl mx-auto px-5 py-8 text-xs text-zinc-500 border-t border-zinc-900 mt-10 space-y-1">
          <div className="text-zinc-300 font-medium">
            This is a forward plan, not a record. September 2026 has not happened; only the 1-September opening is
            observed. The factory has not run this way.
          </div>
          <div>
            Measured: the 31-Aug stock and open POs, the open order backlog, BOMs, line speeds and clearance, realise,
            lead times. Assumed (declared, flagged in the data): forecast demand buckets for volume not yet ordered, the
            even ecom spread, supply exactly on lead time, the invoice→truck lag, the observed line-efficiency derate,
            the storage ceiling (open question Q2), standing stock uncounted at open. Phone numbers are masked —
            September has no approval to show them.
          </div>
          <div className="text-zinc-600">Every number traces to sim/sep-inputs.json via scripts/gen-data.py.</div>
        </footer>
      </body>
    </html>
  );
}
