import "./globals.css"; import Link from "next/link";
export const metadata = { title: "JIVO Mark 1 — August Replay" };
const nav = [["/", "Overview"], ["/day/1", "Day by day"], ["/lines", "Lines"], ["/storage", "Storage"], ["/materials", "Materials"], ["/whatsapp", "WhatsApp"], ["/floor", "Floor 3D"], ["/questions", "Questions"]];
export default function Root({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body className="bg-zinc-950 text-zinc-100 min-h-screen">
    <header className="border-b border-zinc-800 sticky top-0 bg-zinc-950/95 backdrop-blur z-50"><div className="max-w-7xl mx-auto px-5 h-14 flex items-center gap-6">
      <Link href="/" className="font-semibold tracking-tight"><span className="text-amber-400">JIVO</span> Mark 1 <span className="text-zinc-500 font-normal text-sm ml-2">August 2026 replay</span></Link>
      <nav className="flex gap-1 text-sm ml-auto">{nav.map(([h, l]) => <Link key={h} href={h} className="px-3 py-1.5 rounded-md hover:bg-zinc-800 text-zinc-300">{l}</Link>)}</nav></div></header>
    <div className="border-b border-amber-500/20 bg-amber-500/5"><div className="max-w-7xl mx-auto px-5 py-1.5 text-xs text-amber-200/90"><span className="font-semibold">Replay.</span> What the planner <em>would have done</em> in August 2026, standing on each morning with no later data. The factory did not run this way. WhatsApp replies are written in, not received.</div></div>
    <main className="max-w-7xl mx-auto px-5 py-6">{children}</main>
    <footer className="max-w-7xl mx-auto px-5 py-8 text-xs text-zinc-500 border-t border-zinc-900 mt-10 space-y-1"><div className="text-zinc-300 font-medium">This is a replay, not a record. It shows what the planner <em>would have done</em> in August 2026, standing on each morning with no later data. The factory did not run this way.</div><div>Measured: the order book, opening stock, BOMs, line speeds, realise (May–Jul), lead times, storage ceiling, and the people. Assumed: supply arrives exactly on lead time; a 2-day invoice→truck lag; rated line speed rather than the 47% observed. WhatsApp replies are written in by the simulation, not received.</div><div className="text-zinc-600">Every number traces to sim/sim-inputs.json.</div></footer>
  </body></html>);
}
