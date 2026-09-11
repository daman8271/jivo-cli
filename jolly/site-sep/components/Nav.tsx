"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ROUTES } from "../lib/routes";

// "/" matches only itself; every other tab also owns its subtree (/days/12 → "Day by day").
const isActive = (href: string, path: string) =>
  href === "/" ? path === "/" : path === href || path.startsWith(href + "/");

export default function Nav() {
  const path = usePathname();
  return (
    <header className="border-b border-zinc-800 sticky top-0 bg-zinc-950/95 backdrop-blur z-50">
      <div className="max-w-7xl mx-auto px-5 h-14 flex items-center gap-4">
        <Link href="/" className="font-semibold tracking-tight whitespace-nowrap">
          <span className="text-amber-400">JIVO</span> Mark 2{" "}
          <span className="text-zinc-500 font-normal text-sm ml-2">September 2026 plan</span>
        </Link>
        <span
          className="text-[10px] font-semibold tracking-wider px-1.5 py-px rounded border bg-violet-500/15 text-violet-300 border-violet-500/30"
          title="Nothing here has happened yet. This is the computer's plan for September."
        >
          COMPUTER PLAN
        </span>
        <nav className="flex gap-1 text-sm ml-auto overflow-x-auto">
          {ROUTES.map(([h, l]) => {
            const on = isActive(h, path);
            return (
              <Link
                key={h}
                href={h}
                aria-current={on ? "page" : undefined}
                className={`px-3 py-1.5 rounded-md whitespace-nowrap ${
                  on ? "bg-zinc-800 text-zinc-50 font-medium" : "text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                {l}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
