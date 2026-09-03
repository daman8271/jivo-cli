"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ROUTES } from "../lib/routes";
import { LoopBadge } from "./Freshness";
import { FIXTURES } from "../lib/live";

// "/" matches only itself; every other tab also owns its subtree (/days/12 → "Day by day").
const isActive = (href: string, path: string) =>
  href === "/" ? path === "/" : path === href || path.startsWith(href + "/");

export default function Nav() {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-5">
        <Link href="/" className="whitespace-nowrap font-semibold tracking-tight">
          <span className="text-amber-400">JIVO</span> Mark 3
          <span className="ml-2 hidden text-sm font-normal text-zinc-500 sm:inline">the plant, right now</span>
        </Link>
        <LoopBadge />
        {FIXTURES && (
          <span
            title="This build is reading the saved copies in public/fixtures, not the publisher. Nothing here is live."
            className="rounded border border-sky-500/30 bg-sky-500/10 px-1.5 py-px text-[10px] font-semibold tracking-wider text-sky-300"
          >
            SAVED COPIES
          </span>
        )}
        <nav className="ml-auto flex gap-1 overflow-x-auto text-sm">
          {ROUTES.map(([h, l]) => {
            const on = isActive(h, path);
            return (
              <Link
                key={h}
                href={h}
                aria-current={on ? "page" : undefined}
                className={`whitespace-nowrap rounded-md px-3 py-1.5 ${
                  on ? "bg-zinc-800 font-medium text-zinc-50" : "text-zinc-300 hover:bg-zinc-800"
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
