import "./globals.css";
import type { Metadata } from "next";
import Nav from "../components/Nav";
import Footer from "../components/Footer";
import { LoopBanner } from "../components/Freshness";

// No data at build time — by design. The shell is static; every figure inside
// it arrives client-side from the publisher. So this file, unlike Mark 2's,
// cannot and does not read a single number.
export const metadata: Metadata = {
  title: {
    default: "JIVO Mark 4 — the plant, right now",
    template: "%s · JIVO Mark 4",
  },
  description:
    "JIVO Oil's plant as it stands right now, re-planned to the end of the month every few minutes. Only today is " +
    "read off the plant; every later day is worked out from it — and every rule and guess behind it is written down.",
};

export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">
        <Nav />
        <LoopBanner />
        <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
