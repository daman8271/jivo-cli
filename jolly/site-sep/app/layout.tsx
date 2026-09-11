import "./globals.css";
import Nav from "../components/Nav";
import { getLines, getOverview, getStorage } from "../lib/data";

import type { Metadata } from "next";

// The stock-count date is read from the plan's own data (site rule: never type a date or a
// number). '2026-09-02' -> '2 Sep' — the same floor words the generator uses.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function dayMonth(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[(m || 1) - 1]}`;
}
const FROZEN = dayMonth(getOverview().meta.frozen);


export const metadata: Metadata = {
  title: {
    default: "JIVO Mark 2 — September 2026 plan",
    template: "%s · JIVO Mark 2 — September 2026 plan",
  },
  description:
    "JIVO Oil's production plan for September 2026, made by computer. Nothing here has happened yet. Stock was counted on " + FROZEN + " evening.",
};

export default function Root({ children }: { children: React.ReactNode }) {
  // The footer names three of our guesses by their size — read from data, never typed (site rule).
  const lagDays = getStorage().invoice_truck_lag_days;
  const speedPct = Math.round(getLines().efficiency * 100);
  const expectedPct = Math.round(getOverview().demand.forecast_share_litres_pct);
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 min-h-screen">
        <Nav />
        <div className="border-b border-violet-500/20 bg-violet-500/5">
          <div className="max-w-7xl mx-auto px-5 py-1.5 text-xs text-violet-200/90">
            <span className="font-semibold">This is a PLAN for September, made by computer. Nothing here has happened yet.</span>{" "}
            Stock was counted on {FROZEN} evening. Messages on this site were never sent.
          </div>
        </div>
        <main className="max-w-7xl mx-auto px-5 py-6">{children}</main>
        <footer className="max-w-7xl mx-auto px-5 py-8 text-xs text-zinc-500 border-t border-zinc-900 mt-10 space-y-1">
          <div className="text-zinc-300 font-medium">
            Nothing on this site has happened. Only the stock counted on {FROZEN} is real. Every later day is the
            computer&rsquo;s plan.
          </div>
          <div>
            Measured — real: stock and open POs on {FROZEN}, pending customer orders, recipes, machine speeds and
            oil-change time, selling prices, how many days material takes to arrive. Our guess — not measured: about{" "}
            {expectedPct}% of what customers want this month is expected, not ordered yet. E-com orders are spread
            evenly over the month. Material arrives exactly on time. The truck leaves {lagDays} days after billing.
            Machines run at {speedPct}% of listed speed — the pace we measured in August, not a fault. The godown limit
            is Daman&rsquo;s number, not measured (open question Q2). Stock billed but not yet trucked on day 1 is not
            counted, so the godown is really fuller. Phone numbers are hidden.
          </div>
          <div className="text-zinc-600">
            Every number comes from the {FROZEN} stock count and the computer plan (sim/sep-inputs.json →
            scripts/gen-data.py). Nothing is typed in by hand.
          </div>
        </footer>
      </body>
    </html>
  );
}
