import { getAllDays, fmt } from "@/lib/data";
import { Card, Section, Pill } from "@/components/Card";
import MtOilChart, { type MtOilPoint } from "@/components/MtOilChart";

export const metadata = { title: "Materials — JIVO Mark 1" };

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso: string) => { const p = iso.split("-"); return `${+p[2]} ${MON[+p[1] - 1]}`; };
const unit = (u: string) => (u === "LTR" ? "L" : u === "PCS" ? "pcs" : u.toLowerCase());
const label = (code: string, name: string) => (name && name !== code ? name : code);

type BuyAgg = { code: string; name: string; uom: string; qty: number; orders: number; firstDay: number; firstDate: string; firstLand: string };
type BindAgg = { code: string; name: string; blocks: number; days: number[]; skus: string[]; want: number };

export default function MaterialsPage() {
  const days = getAllDays();

  // ---- 1. what we ordered, by code -------------------------------------
  const buys = new Map<string, BuyAgg>();
  days.forEach((d, i) => d.bought.forEach((b) => {
    const e = buys.get(b.code);
    if (!e) buys.set(b.code, { code: b.code, name: b.name, uom: b.uom, qty: b.qty, orders: 1, firstDay: i + 1, firstDate: d.date, firstLand: b.lands });
    else { e.qty += b.qty; e.orders += 1; if (b.lands < e.firstLand) e.firstLand = b.lands; }
  }));
  const bought = [...buys.values()].sort((a, b) => b.qty - a.qty);
  const rm = bought.filter((b) => b.code.startsWith("RM"));
  const pm = bought.filter((b) => !b.code.startsWith("RM"));
  const boughtLines = days.reduce((a, d) => a + d.bought.length, 0);
  const oilOrdered = rm.reduce((a, b) => a + b.qty, 0);
  const packOrdered = pm.reduce((a, b) => a + b.qty, 0);

  // ---- 2. what stopped the line ----------------------------------------
  const binders = new Map<string, { code: string; name: string; blocks: number; days: Set<number>; skus: Map<string, string>; want: number }>();
  days.forEach((d, i) => d.blocked.forEach((b) => {
    let e = binders.get(b.binder);
    if (!e) { e = { code: b.binder, name: b.binder_name, blocks: 0, days: new Set(), skus: new Map(), want: 0 }; binders.set(b.binder, e); }
    e.blocks += 1; e.days.add(i + 1); e.skus.set(b.code, b.sku); e.want += b.want;
  }));
  const binderList: BindAgg[] = [...binders.values()]
    .map((e) => ({ code: e.code, name: e.name, blocks: e.blocks, days: [...e.days].sort((a, b) => a - b), skus: [...e.skus.values()], want: e.want }))
    .sort((a, b) => b.blocks - a.blocks || b.days.length - a.days.length);
  const top15 = binderList.slice(0, 15);
  const worst = binderList[0];
  const topBottle = binderList.find((b) => /PET BOTTLE|HDPE BOTTLE/i.test(b.name));
  const totalBlocks = days.reduce((a, d) => a + d.blocked.length, 0);
  const oilBlocks = binderList.filter((b) => b.code.startsWith("RM")).reduce((a, b) => a + b.blocks, 0);
  const blockedDays = days.filter((d) => d.blocked.length > 0).length;

  // ---- 3. what landed ---------------------------------------------------
  const landings = days.map((d, i) => {
    const oil = d.received.filter((r) => r.code.startsWith("RM")).reduce((a, b) => a + b.qty, 0);
    const pieces = d.received.filter((r) => !r.code.startsWith("RM")).reduce((a, b) => a + b.qty, 0);
    return { n: i + 1, date: d.date, dow: d.weekday.slice(0, 3), lines: d.received.length, oil, pieces, top: [...d.received].sort((a, b) => b.qty - a.qty).slice(0, 4) };
  }).filter((r) => r.lines > 0);
  const oilLanded = landings.reduce((a, r) => a + r.oil, 0);
  const packLanded = landings.reduce((a, r) => a + r.pieces, 0);
  const maxLine = Math.max(...landings.map((r) => r.lines));

  // ---- 4. oil on hand ---------------------------------------------------
  const oilPoints: MtOilPoint[] = days.map((d, i) => ({
    n: i + 1, date: d.date, dow: d.weekday.slice(0, 3), working: d.working, oil: d.oil_on_hand_l,
    landed: d.received.filter((r) => r.code.startsWith("RM")).reduce((a, b) => a + b.qty, 0),
  }));

  return (
    <div>
      <h1 className="text-2xl font-semibold">Materials</h1>
      <p className="text-zinc-400 text-sm mt-1 max-w-3xl">
        Oil is the easy part. What actually holds a line is a barcode sticker that has not come. Below: everything
        ordered in August, everything that landed, and the short list of items that stopped a machine.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
        <Card title="Purchase lines raised" value={fmt(boughtLines)} sub={`${fmt(bought.length)} different items — ${fmt(rm.length)} oils, ${fmt(pm.length)} packaging`} />
        <Card title="Oil ordered" value={`${fmt(oilOrdered)} L`} sub={`${fmt(oilLanded)} L landed inside the month`} tone="text-emerald-400" />
        <Card title="Packaging ordered" value={`${fmt(packOrdered)} pcs`} sub={`${fmt(packLanded)} pcs landed inside the month`} tone="text-sky-300" />
        <Card title="Times a part stopped a SKU" value={fmt(totalBlocks)} sub={`on ${blockedDays} of 31 days, caused by only ${binderList.length} items`} tone="text-red-400" />
      </div>

      {/* ---------------- 1. ordered ---------------- */}
      <Section title="What we ordered" right={<span className="text-xs text-zinc-500">every &quot;bought&quot; line in August, added up by item code</span>}>
        <h3 className="text-sm text-zinc-300 mb-2">Oil <span className="text-zinc-500">— {rm.length} items, {fmt(oilOrdered)} L</span></h3>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400 text-left">
              <tr>
                <th className="px-3 py-2 font-medium">Item</th>
                <th className="px-3 py-2 font-medium">Code</th>
                <th className="px-3 py-2 font-medium text-right">Ordered</th>
                <th className="px-3 py-2 font-medium text-right">Orders</th>
                <th className="px-3 py-2 font-medium">First ordered</th>
                <th className="px-3 py-2 font-medium">First landing</th>
              </tr>
            </thead>
            <tbody>
              {rm.map((b) => (
                <tr key={b.code} className="border-t border-zinc-900">
                  <td className="px-3 py-1.5 text-zinc-100">{label(b.code, b.name)}</td>
                  <td className="px-3 py-1.5 text-zinc-500 font-mono text-xs">{b.code}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-emerald-300">{fmt(b.qty)} <span className="text-zinc-500">{unit(b.uom)}</span></td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-400">{b.orders}</td>
                  <td className="px-3 py-1.5 text-zinc-400 whitespace-nowrap">Day {b.firstDay} <span className="text-zinc-600">· {shortDate(b.firstDate)}</span></td>
                  <td className="px-3 py-1.5 text-zinc-400 whitespace-nowrap">{shortDate(b.firstLand)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className="text-sm text-zinc-300 mt-6 mb-2">Packaging <span className="text-zinc-500">— {pm.length} items, {fmt(packOrdered)} pcs. Biggest first; scroll for the rest.</span></h3>
        <div className="rounded-xl border border-zinc-800 overflow-auto max-h-[540px]">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400 text-left sticky top-0 z-10">
              <tr>
                <th className="px-3 py-2 font-medium">Item</th>
                <th className="px-3 py-2 font-medium">Code</th>
                <th className="px-3 py-2 font-medium text-right">Ordered</th>
                <th className="px-3 py-2 font-medium text-right">Orders</th>
                <th className="px-3 py-2 font-medium">First ordered</th>
                <th className="px-3 py-2 font-medium">First landing</th>
              </tr>
            </thead>
            <tbody>
              {pm.map((b) => (
                <tr key={b.code} className="border-t border-zinc-900">
                  <td className="px-3 py-1.5 text-zinc-100">{label(b.code, b.name)}</td>
                  <td className="px-3 py-1.5 text-zinc-500 font-mono text-xs">{b.code}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-sky-300">{fmt(b.qty)} <span className="text-zinc-500">{unit(b.uom)}</span></td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-400">{b.orders}</td>
                  <td className="px-3 py-1.5 text-zinc-400 whitespace-nowrap">Day {b.firstDay} <span className="text-zinc-600">· {shortDate(b.firstDate)}</span></td>
                  <td className="px-3 py-1.5 text-zinc-400 whitespace-nowrap">{shortDate(b.firstLand)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* ---------------- 2. blockers ---------------- */}
      <Section title="What stopped the line" right={<span className="text-xs text-zinc-500">ranked by how many day-SKU blocks the item caused</span>}>
        <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-wider text-red-300/80">The single biggest binder in August</div>
              <div className="text-3xl font-semibold mt-1 text-zinc-50">{label(worst.code, worst.name)}</div>
              <div className="text-sm text-zinc-400 mt-1 font-mono">{worst.code}</div>
              <div className="text-sm text-zinc-300 mt-3 max-w-xl">
                It held <span className="text-zinc-100">{worst.skus.length === 1 ? worst.skus[0] : `${worst.skus.length} SKUs`}</span> on{" "}
                <span className="text-zinc-100">{worst.days.length} separate days</span>, {worst.blocks} times in all,
                for <span className="text-zinc-100">{fmt(worst.want)} pieces</span> the order book already wanted.
              </div>
            </div>
            <div className="flex gap-6">
              <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Blocks</div><div className="text-4xl font-semibold text-red-400">{worst.blocks}</div></div>
              <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Days</div><div className="text-4xl font-semibold text-zinc-100">{worst.days.length}</div></div>
              <div><div className="text-[11px] uppercase tracking-wider text-zinc-500">Pieces wanted</div><div className="text-4xl font-semibold text-zinc-100">{fmt(worst.want)}</div></div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-red-900/40 text-sm text-zinc-400">
            The worst binder is not a bottle and it is not oil — it is a barcode sticker.
            {topBottle && (
              <> The first bottle on the list is <span className="text-zinc-200">{label(topBottle.code, topBottle.name)}</span> ({topBottle.code}) at{" "}
                {topBottle.blocks} blocks over {topBottle.days.length} {topBottle.days.length === 1 ? "day" : "days"}, {fmt(topBottle.want)} pieces wanted.</>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 overflow-x-auto mt-4">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400 text-left">
              <tr>
                <th className="px-3 py-2 font-medium w-8">#</th>
                <th className="px-3 py-2 font-medium">Item that was missing</th>
                <th className="px-3 py-2 font-medium">Code</th>
                <th className="px-3 py-2 font-medium text-right">Blocks</th>
                <th className="px-3 py-2 font-medium text-right">Days</th>
                <th className="px-3 py-2 font-medium text-right">SKUs</th>
                <th className="px-3 py-2 font-medium text-right">Pieces wanted</th>
                <th className="px-3 py-2 font-medium">Which SKUs</th>
              </tr>
            </thead>
            <tbody>
              {top15.map((b, i) => (
                <tr key={b.code} className="border-t border-zinc-900">
                  <td className="px-3 py-1.5 text-zinc-600 tabular-nums">{i + 1}</td>
                  <td className="px-3 py-1.5 text-zinc-100">{label(b.code, b.name)}</td>
                  <td className="px-3 py-1.5 text-zinc-500 font-mono text-xs">{b.code}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-red-400 font-medium">{b.blocks}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{b.days.length}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{b.skus.length}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{fmt(b.want)}</td>
                  <td className="px-3 py-1.5 text-zinc-500 text-xs">{b.skus.slice(0, 2).join(" · ")}{b.skus.length > 2 ? ` +${b.skus.length - 2}` : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          A &quot;block&quot; is one SKU that could not run on one day because this item was short. {fmt(totalBlocks)} blocks in
          August came from {binderList.length} items; the 15 above are {fmt(top15.reduce((a, b) => a + b.blocks, 0))} of them.
        </p>
      </Section>

      {/* ---------------- 3. what landed ---------------- */}
      <Section title="What landed, and when" right={<span className="text-xs text-zinc-500">{landings.length} delivery days out of 31</span>}>
        <div className="rounded-xl border border-zinc-800 divide-y divide-zinc-900">
          {landings.map((r) => (
            <div key={r.n} className="flex flex-wrap items-start gap-x-5 gap-y-2 px-4 py-2.5">
              <div className="w-28 shrink-0">
                <div className="text-zinc-100 font-medium">{shortDate(r.date)}</div>
                <div className="text-xs text-zinc-600">Day {r.n} · {r.dow}</div>
              </div>
              <div className="w-32 shrink-0">
                <div className="h-2 rounded-full bg-zinc-800 overflow-hidden"><div className="h-full bg-zinc-500" style={{ width: `${(r.lines / maxLine) * 100}%` }} /></div>
                <div className="text-xs text-zinc-500 mt-1">{r.lines} {r.lines === 1 ? "line" : "lines"}</div>
              </div>
              <div className="w-40 shrink-0 text-sm">
                {r.oil > 0 && <div className="text-emerald-300 tabular-nums">{fmt(r.oil)} L oil</div>}
                {r.pieces > 0 && <div className="text-sky-300 tabular-nums">{fmt(r.pieces)} pcs</div>}
              </div>
              <div className="flex flex-wrap gap-1.5 grow">
                {r.top.map((t) => (
                  <span key={t.code} className="text-xs px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-300">
                    {label(t.code, t.name)} <span className="text-zinc-500 tabular-nums">{fmt(t.qty)}</span>
                  </span>
                ))}
                {r.lines > r.top.length && <span className="text-xs px-2 py-0.5 text-zinc-600">+{r.lines - r.top.length} more</span>}
              </div>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          <Pill tone="amber">assumed</Pill> <span className="ml-1">supply is idealised — every purchase order lands exactly on its lead time (oil 11 days, packaging 6). A late truck moves every block above to the right.</span>
        </p>
      </Section>

      {/* ---------------- 4. oil on hand ---------------- */}
      <Section title="Loose oil on hand" right={<span className="text-xs text-zinc-500">start {fmt(oilPoints[0].oil)} L → end {fmt(oilPoints[oilPoints.length - 1].oil)} L</span>}>
        <MtOilChart points={oilPoints} />
        <p className="mt-2 text-xs text-zinc-500">
          Of the {fmt(totalBlocks)} blocks in August, {fmt(oilBlocks)} came from oil being short. Everything else was packaging.
        </p>
      </Section>
    </div>
  );
}
