import Link from "next/link";
import { ROUTES } from "../lib/routes";

// Keeps the site chrome (nav + plan banner come from the layout) instead of
// Next's bare default, and points back at real routes. No business numbers here.
export default function NotFound() {
  return (
    <div className="py-16 max-w-xl">
      <div className="text-xs uppercase tracking-wider text-zinc-500">404</div>
      <h1 className="text-2xl font-semibold mt-1">No such page in the September plan</h1>
      <p className="text-sm text-zinc-400 mt-3">
        The plan has 30 days (<Link href="/days/1" className="text-amber-400 hover:underline">/days/1</Link> to{" "}
        <Link href="/days/30" className="text-amber-400 hover:underline">/days/30</Link>) and the sections below —
        nothing else.
      </p>
      <ul className="mt-5 flex flex-wrap gap-2 text-sm">
        {ROUTES.map(([h, l]) => (
          <li key={h}>
            <Link href={h} className="inline-block rounded-md border border-zinc-800 px-3 py-1.5 text-zinc-300 hover:bg-zinc-800">
              {l}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
