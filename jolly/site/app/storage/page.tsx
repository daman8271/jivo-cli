import { getAllDays, getInputs, fmt } from "@/lib/data";
import { Card, Section, Pill } from "@/components/Card";
import StStorageChart, { type StPoint } from "@/components/StStorageChart";

export const metadata = { title: "Storage — JIVO Mark 1" };

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso: string) => { const p = iso.split("-"); return `${+p[2]} ${MON[+p[1] - 1]}`; };

export default function StoragePage() {
  const days = getAllDays();
  const inputs = getInputs();

  const points: StPoint[] = days.map((d, i) => ({
    n: i + 1, date: d.date, dow: d.weekday.slice(0, 3), working: d.working,
    fg: d.storage.fg_in_godown_l, inv: d.storage.invoiced_not_trucked_l,
    physical: d.storage.physical_l, ceiling: d.storage.ceiling_l,
    pct: d.storage.pct, headroom: d.storage.headroom_l,
    made: d.made_litres, shipped: d.shipped_litres,
    throttle: d.decisions.some((x) => x.kind === "STORAGE_THROTTLE"),
  }));

  const ceiling = points[0].ceiling;
  const safety = ceiling * 0.95;
  const open = points[0];
  const peak = points.reduce((a, b) => (b.physical > a.physical ? b : a));
  const at95 = points.filter((p) => p.physical >= safety - 1).length;
  const throttled = points.filter((p) => p.throttle).length;

  let fallIdx = 1, fallDrop = 0;
  for (let i = 1; i < points.length; i++) {
    const drop = points[i - 1].physical - points[i].physical;
    if (drop > fallDrop) { fallDrop = drop; fallIdx = i; }
  }
  const fall = points[fallIdx];

  // channel split of everything that left the floor in August
  let mart = 0, dock = 0;
  const martByDay = days.map((d) => d.dispatched.filter((x) => x.channel === "MART").reduce((a, b) => a + b.litres, 0));
  days.forEach((d) => d.dispatched.forEach((x) => { if (x.channel === "MART") mart += x.litres; else dock += x.litres; }));
  const bigShip = points.reduce((a, b) => (b.shipped > a.shipped ? b : a));
  const bigShipMart = martByDay[bigShip.n - 1];
  const fallMart = martByDay[fall.n - 1];

  const sheetOpen = Number(inputs.opening?.fg_litres ?? 0);   // the BOOK figure: SAP OnHand at 1 Aug, all FG
  const sheetOpenPct = (sheetOpen / ceiling) * 100;
  const prov = String(inputs.provenance?.storage ?? "");
  const assumed = days[0].honesty.assumed.filter((a) => /truck|invoice|lag/i.test(a));

  const totalMade = points.reduce((a, b) => a + b.made, 0);
  const totalShipped = points.reduce((a, b) => a + b.shipped, 0);

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Storage</h1>
          <p className="text-zinc-400 text-sm mt-1 max-w-2xl">
            You cannot just make things and not think about where they go. The godown holds{" "}
            <span className="text-zinc-200">{fmt(ceiling)} L</span> when it is working properly. On {at95} of the 31 days
            in August it stood at the 95% line.
          </p>
        </div>
        <div className="text-right text-xs text-zinc-500 max-w-sm">Ceiling: BH-BT + BH-PF working capacity.<br />{prov}</div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 mt-5">
        <Card title="1 August, on the floor" value={`${open.pct}%`} sub={`${fmt(open.physical)} L of ${fmt(ceiling)} L`} tone="text-amber-300" />
        <Card title="Peak" value={`${peak.pct}%`} sub={`${fmt(peak.physical)} L — only ${fmt(ceiling - peak.physical)} L spare`} tone="text-red-400" />
        <Card title="Days at 95% or over" value={`${at95} of 31`} sub={`${throttled} days production was capped to what could ship`} tone="text-red-400" />
        <Card title="Biggest one-day fall" value={`−${fmt(fallDrop)} L`} sub={`${shortDate(fall.date)} — trucks finally left: ${fmt(fall.shipped)} L shipped, ${fmt(fallMart)} L of it to JIVO Mart`} tone="text-emerald-400" />
        <Card title="Biggest single day out" value={`${fmt(bigShip.shipped)} L`} sub={`${shortDate(bigShip.date)} — ${fmt(bigShipMart)} L of it billed to JIVO Mart in one go`} tone="text-sky-300" />
      </div>

      <Section title="Every day of August, against the ceiling"
        right={<span className="text-xs text-zinc-500">white line = what is actually standing in the godown</span>}>
        <StStorageChart points={points} />
      </Section>

      <Section title={`Why the sheet says ${sheetOpenPct.toFixed(0)}% and the floor says ${Math.round(open.pct)}%`}>
        <div className="grid lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <ol className="space-y-2.5 text-[15px] leading-relaxed text-zinc-200 list-none">
              <li><span className="text-zinc-600 mr-2">1.</span>SAP takes stock off the books the moment the invoice is cut.</li>
              <li><span className="text-zinc-600 mr-2">2.</span>The truck leaves a day or two later. Until it does, those cartons are still standing on our floor.</li>
              <li><span className="text-zinc-600 mr-2">3.</span>So the sheet reads {sheetOpenPct.toFixed(0)}% full while the floor is at {Math.round(open.pct)}%, and the space you were promised is not there.</li>
              <li><span className="text-zinc-600 mr-2">4.</span>Stock leaves by two doors, not one — the customer&apos;s truck at the dock, and the transfer to Mart. Count both.</li>
              <li><span className="text-zinc-600 mr-2">5.</span>Plan production against the floor number, never the book number.</li>
            </ol>
            <div className="mt-4 pt-3 border-t border-zinc-800 text-sm text-zinc-400">On 1 August the book showed <span className="text-zinc-200">{fmt(sheetOpen)} L</span> on hand ({sheetOpenPct.toFixed(1)}%). By the end of that day the floor held <span className="text-zinc-200">{fmt(open.physical)} L</span> ({open.pct.toFixed(1)}%). The {fmt(open.physical - sheetOpen)} L gap is two things: <span className="text-zinc-200">{fmt(open.inv)} L</span> billed but not yet trucked, plus <span className="text-zinc-200">{fmt(Math.max(0, open.made - open.shipped))} L</span> made that day net of what shipped. The invoice lag is most of the gap, not all of it.</div>
          </div>
          <div className="space-y-3">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="text-xs uppercase tracking-wider text-zinc-500">The two exit doors, all August</div>
              <div className="mt-2 flex items-baseline justify-between"><span className="text-zinc-300">Transfer to JIVO Mart</span><span className="text-xl font-semibold">{fmt(mart)} L</span></div>
              <div className="mt-1 flex items-baseline justify-between"><span className="text-zinc-300">Customer dock (GT + MT)</span><span className="text-xl font-semibold">{fmt(dock)} L</span></div>
              <div className="mt-2 h-2 rounded-full overflow-hidden bg-zinc-800 flex">
                <div className="bg-sky-500/70" style={{ width: `${(mart / (mart + dock)) * 100}%` }} />
                <div className="bg-amber-500/70 grow" />
              </div>
              <div className="mt-2 text-xs text-zinc-500">{fmt(totalShipped)} L left the floor. {fmt(totalMade)} L was made.</div>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-xs text-zinc-400">
              <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1.5">Honest about this panel</div>
              <div><Pill tone="green">measured</Pill> <span className="ml-1">the {fmt(ceiling)} L ceiling, opening stock, and every invoice and transfer.</span></div>
              <div className="mt-1.5"><Pill tone="amber">assumed</Pill> <span className="ml-1">{assumed.length ? assumed.join("; ") : "invoice→truck lag 2 d (median)"} — a slower truck makes every bar above taller.</span></div>
            </div>
          </div>
        </div>
      </Section>

      <Section title="Day by day" right={<span className="text-xs text-zinc-500">Sundays dim · ▲ = production capped that day</span>}>
        <div className="rounded-xl border border-zinc-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-900 text-zinc-400">
              <tr className="text-left">
                <th className="px-3 py-2 font-medium">Day</th>
                <th className="px-3 py-2 font-medium text-right">On the floor</th>
                <th className="px-3 py-2 font-medium w-48">Full</th>
                <th className="px-3 py-2 font-medium text-right">Room left</th>
                <th className="px-3 py-2 font-medium text-right">Made</th>
                <th className="px-3 py-2 font-medium text-right">Shipped</th>
                <th className="px-3 py-2 font-medium"> </th>
              </tr>
            </thead>
            <tbody>
              {points.map((p) => (
                <tr key={p.n} className={`border-t border-zinc-900 ${p.working ? "" : "opacity-40"}`}>
                  <td className="px-3 py-1.5 whitespace-nowrap"><span className="text-zinc-500 tabular-nums mr-2">{String(p.n).padStart(2, "0")}</span>{shortDate(p.date)} <span className="text-zinc-600">{p.dow}</span></td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{fmt(p.physical)} L</td>
                  <td className="px-3 py-1.5">
                    <div className="flex items-center gap-2">
                      <div className="h-2 grow rounded-full bg-zinc-800 overflow-hidden flex">
                        <div className="bg-sky-500/70" style={{ width: `${(p.fg / p.ceiling) * 100}%` }} />
                        <div className="bg-amber-500/70" style={{ width: `${(p.inv / p.ceiling) * 100}%` }} />
                      </div>
                      <span className={`tabular-nums w-12 text-right ${p.physical >= safety - 1 ? "text-red-400" : "text-zinc-300"}`}>{p.pct}%</span>
                    </div>
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-zinc-400">{fmt(p.headroom)} L</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{p.made ? `${fmt(p.made)} L` : <span className="text-zinc-700">—</span>}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">{p.shipped ? `${fmt(p.shipped)} L` : <span className="text-zinc-700">—</span>}</td>
                  <td className="px-3 py-1.5">{p.throttle && <span className="text-amber-400" title="Production capped to what could ship">▲</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          Blue = finished goods in the godown. Amber = invoiced but still standing here. Both take up the same space.
        </p>
      </Section>
    </div>
  );
}
