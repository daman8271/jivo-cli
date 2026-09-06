"use client";

// The FORWARD layer: what the planner does with today's count, from today to
// the end of the month. Nothing here has happened.

import Link from "next/link";
import { asHonesty, asOverview, asSpine, useLive } from "../lib/live";
import { ceilingRule, manualRule, maskDigits, P } from "../lib/labels";
import { cr, dlabel, inr, litres, money, orUnknown, pct, pct1, plural } from "../lib/fmt";
import { Card, Panel, Pill, Stat } from "./Card";
import { AsOf, Live, NotLive } from "./Freshness";
import SimBadge from "./SimBadge";

export default function ForwardStrip() {
  const live = useLive(["overview", "spine", "honesty"]);
  const o = asOverview(live.overview);
  const spine = asSpine(live.spine);
  const h = asHonesty(live.honesty);
  const ceiling = ceilingRule(h);
  const today = spine?.[0] ?? null;
  const book = today?.book ?? null;
  const manual = manualRule(h);
  /* the drums. R14: they are filled by hand and go on no machine, so they are
     never a "no machine can fill it" row — that panel is for a real gap. */
  const byHand = o?.manual_fill ?? [];
  const stuck = o?.stuck ?? null;
  const def = stuck?.definitions ?? {};
  /* The HEADINGS come from gen too. "The machine had no hours left" was typed here
     while the sentence under it said most of those products had a machine with hours
     to spare — a hand-typed heading cannot be kept true by hand. The fallbacks below
     are true of the bucket whatever the day looks like. */
  const head = stuck?.headings ?? {};
  /* Machines that still had hours on day 1, in gen's own numbers. */
  const freeHours = Object.entries(stuck?.hours_free_today ?? {}).filter(([, v]) => v > 0);

  return (
    <div className="space-y-4">
      <Live rec={live.overview} what="the plan">
        {o && (
          <>
            {/* one freshness stamp for the four tiles below — they all come
                from the same source, so four identical stamps would be noise */}
            <div className="mb-1.5 flex justify-end">
              <AsOf rec={live.overview} />
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card
              title="Still to make this month"
              value={orUnknown(book?.plan_left_l, litres)}
              badge={<SimBadge kind="plan" />}
              sub={book?.plan_left_l ? "against this month's target, from today onward" : undefined}
            />
            <Card
              title="The computer expects to make"
              value={litres(o.totals.made_l)}
              tone="text-violet-300"
              badge={<SimBadge kind="plan" />}
              sub={`${cr(o.totals.value_rs)} over ${o.totals.working_days} working ${plural(
                o.totals.working_days, "day", "days",
              )} — ${pct1(o.plan.made_vs_plan_pct)} of the target`}
            />
            <Card
              title="Billed out over the month"
              value={litres(o.totals.shipped_l)}
              badge={<SimBadge kind="plan" />}
              sub={`${pct1(o.demand.forecast_share_litres_pct)} of the demand behind it is expected, not ordered`}
            />
            <Card
              title="Days the godown is over the limit"
              value={`${o.storage.days_ge_100.length} of ${o.totals.days}`}
              tone={o.storage.days_ge_100.length > 0 ? "text-red-400" : "text-emerald-300"}
              badge={<NotLive p={P.ceiling(ceiling.text)} />}
              sub={
                <>
                  {o.storage.days_ge_95} {plural(o.storage.days_ge_95, "day", "days")} at 95% or more of{" "}
                  {litres(o.storage.ceiling_l)} — the limit you gave us
                </>
              }
            />
            </div>
          </>
        )}
      </Live>

      <div className="grid gap-3 md:grid-cols-2">
        <Panel
          title="Today, as the planner sees it"
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.spine} />}
        >
          <Live rec={live.spine} what="today's plan">
            {today && (
              <>
                <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Fill today</div>
                    <div className="text-xl font-semibold tabular-nums">{litres(today.made_l)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Machines busy</div>
                    <div className="text-xl font-semibold tabular-nums">{pct(today.util)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Godown</div>
                    <div
                      className={`text-xl font-semibold tabular-nums ${
                        today.storage_pct >= 95 ? "text-red-300" : today.storage_pct >= 80 ? "text-amber-300" : "text-emerald-300"
                      }`}
                    >
                      {pct1(today.storage_pct)}
                    </div>
                  </div>
                  {/* stuck = DIFFERENT products that could not start. `blocked` counts
                      tries, and a product is tried on every machine that could fill it. */}
                  <div title={today.blocked_label}>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">
                      Runs / stuck products
                    </div>
                    <div className="text-xl font-semibold tabular-nums">
                      {today.runs}{" "}
                      <span className="text-red-300">/ {orUnknown(today.blocked_products, inr, "—")}</span>
                    </div>
                    <div className="text-[10px] text-zinc-500">
                      {inr(today.blocked)} {plural(today.blocked, "try", "tries")} stopped
                    </div>
                  </div>
                </div>
                {today.open_real_l_computed != null && (
                  <p className="mt-3 text-xs text-zinc-400">
                    Still to send on confirmed orders: {litres(today.open_real_l_computed)}.{" "}
                    {today.open_real_l_note ? maskDigits(today.open_real_l_note) : ""}
                  </p>
                )}
                {book && (
                  <div className="mt-3 space-y-1 text-xs text-zinc-500">
                    <div title={book.po_cumulative_value_label}>
                      {money(book.po_cumulative_value_rs)} — {book.po_cumulative_value_label}
                    </div>
                    <div title={book.po_open_l_raw_label}>
                      {litres(book.po_open_l_raw)} — {book.po_open_l_raw_label}
                    </div>
                  </div>
                )}
              </>
            )}
          </Live>
        </Panel>

        <Panel
          title="Why these numbers get to have an opinion"
          badge={<SimBadge kind="measured" />}
          asOf={<AsOf rec={live.overview} />}
        >
          <Live rec={live.overview} what="the calibration">
            {o?.august && (
              <>
                <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">The computer said</div>
                    <div className="text-xl font-semibold tabular-nums">{litres(o.august.sim_made_l)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">The plant really made</div>
                    <div className="text-xl font-semibold tabular-nums">{litres(o.august.actual_made_l)}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-zinc-500">Out by</div>
                    <div className="text-xl font-semibold tabular-nums text-emerald-300">{pct1(o.august.delta_pct)}</div>
                  </div>
                </div>
                <p className="mt-2 text-xs text-zinc-400">{maskDigits(o.august.note ?? "")}</p>
              </>
            )}
            {o?.day1_blocked && (
              <div className="mt-4 border-t border-zinc-800 pt-3">
                <div className="text-[10px] uppercase tracking-wider text-zinc-500">Stuck today</div>
                <div className="mt-1 flex flex-wrap items-baseline gap-2 text-sm">
                  <span className="text-lg font-semibold tabular-nums text-red-300">{o.day1_blocked.products}</span>
                  <span className="text-zinc-400">
                    {plural(o.day1_blocked.products, "product", "products")} the planner could not start
                  </span>
                  {o.day1_blocked.top_binder && (
                    <Pill tone="amber" title={`${o.day1_blocked.top_binder.attempts} attempts stopped by this one`}>
                      worst: {o.day1_blocked.top_binder.name}
                    </Pill>
                  )}
                </div>
                <p className="mt-1 text-xs text-zinc-500">{maskDigits(o.day1_blocked.note ?? "")}</p>
              </div>
            )}
          </Live>
        </Panel>
      </div>

      {/* ── why a product is not in today's plan ──────────────────
          FOUR different reasons, and they need four different actions: buy
          something · get a truck to the gate · nobody wants it · the plan did not
          get to it. The headings AND the planner's own words for each are in the
          data — the third reason is not always the clock, and gen is the only thing
          that knows which it was today.
          The godown one (B20) used to have no row at all: the engine dropped the run
          without saying so, and eleven of this run's held-back days published
          "nothing is stuck" with machines standing idle. */}
      {stuck && (
        <Panel
          title="What is not being made today, and why"
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.overview} />}
          note={
            stuck.godown_full_today
              ? "The godown ran out of room today. Everything in the second column had the machine hours and the material — there was nowhere to put what it would fill."
              : undefined
          }
        >
          <div className="flex flex-wrap gap-x-8 gap-y-3">
            <Stat
              k={head.material ?? "Short of something it is made from"}
              v={orUnknown(stuck.counts?.material, (v) => `${inr(v)} ${plural(v, "product", "products")}`)}
              tone="text-red-300"
              sub={def.material}
            />
            <Stat
              k={head.storage ?? "The godown was too full to put it anywhere"}
              v={orUnknown(stuck.counts?.storage, (v) => `${inr(v)} ${plural(v, "product", "products")}`)}
              tone="text-amber-300"
              sub={def.storage}
            />
            <Stat
              k={head.no_order ?? "Nobody has asked for it"}
              v={orUnknown(stuck.counts?.no_order, (v) => `${inr(v)} ${plural(v, "product", "products")}`)}
              tone="text-violet-300"
              sub={def.no_order}
            />
            <Stat
              k={head.no_line_time ?? "Ordered, and the plan did not get to it"}
              v={orUnknown(stuck.counts?.no_line_time, (v) => `${inr(v)} ${plural(v, "product", "products")}`)}
              tone="text-amber-300"
              sub={def.no_line_time}
            />
            <Stat
              k={head.manual ?? "Filled by hand"}
              v={orUnknown(stuck.counts?.manual, (v) => `${inr(v)} ${plural(v, "product", "products")}`)}
              sub={def.manual}
            />
          </div>
          {freeHours.length > 0 && (
            <p className="mt-2 text-xs text-zinc-500">
              Hours still free on the machines today:{" "}
              {freeHours.map(([line, hours]) => `${line} ${hours} h`).join(" · ")} &mdash; a product in that third
              column whose machine is named here was left out by the running order, not by the clock.
            </p>
          )}

          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">
                {head.material ?? "Short of something it is made from"}
              </div>
              <ul className="max-h-56 space-y-1 overflow-y-auto pr-2 text-xs">
                {(stuck.material ?? []).map((m) => (
                  <li key={m.code}>
                    <span className="text-zinc-300">{m.sku}</span>
                    <span className="text-zinc-500">
                      {" "}— short of {(m.short_of ?? []).map((x) => x.name).join(", ") || "something"}
                    </span>
                    {/* what it tried to fill TODAY — not the month's line */}
                    {m.want_litres != null && (
                      <span className="ml-1 tabular-nums text-zinc-600">{litres(m.want_litres)} wanted today</span>
                    )}
                  </li>
                ))}
                {(stuck.material ?? []).length === 0 && <li className="text-zinc-500">Nothing.</li>}
              </ul>
            </div>
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">
                {head.storage ?? "The godown was too full to put it anywhere"}
              </div>
              <ul className="max-h-56 space-y-1 overflow-y-auto pr-2 text-xs">
                {(stuck.storage ?? []).map((m) => (
                  <li key={m.code}>
                    <span className="text-zinc-300">{m.sku}</span>
                    <span className="text-zinc-500"> — nowhere to put it</span>
                    {m.ordered && (
                      <Pill tone="amber" title="somebody has really ordered this one">
                        somebody wants it
                      </Pill>
                    )}
                    {(m.machines_with_room?.length ?? 0) > 0 && (
                      <Pill tone="blue" title="this machine had hours to spare and the material was there — the godown is what stopped it">
                        {m.machines_with_room!.join(", ")} had hours
                      </Pill>
                    )}
                    {m.want_litres != null && (
                      <span className="ml-1 tabular-nums text-zinc-600">{litres(m.want_litres)} wanted today</span>
                    )}
                  </li>
                ))}
                {(stuck.storage ?? []).length === 0 && <li className="text-zinc-500">Nothing.</li>}
              </ul>
            </div>
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">
                {head.no_order ?? "Nobody has asked for it"}
              </div>
              <ul className="max-h-56 space-y-1 overflow-y-auto pr-2 text-xs">
                {(stuck.no_order ?? []).map((m) => (
                  <li key={m.code}>
                    <span className="text-zinc-300">{m.sku}</span>
                    {/* the WHOLE MONTH off the plan sheet, never today's want */}
                    {m.month_target_litres != null && (
                      <span className="ml-1 tabular-nums text-zinc-600">
                        {litres(m.month_target_litres)} — the month&rsquo;s target
                      </span>
                    )}
                  </li>
                ))}
                {(stuck.no_order ?? []).length === 0 && <li className="text-zinc-500">Nothing.</li>}
              </ul>
            </div>
            <div>
              <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-500">
                {head.no_line_time ?? "Ordered, and the plan did not get to it"}
              </div>
              <ul className="max-h-56 space-y-1 overflow-y-auto pr-2 text-xs">
                {(stuck.no_line_time ?? []).map((m) => (
                  <li key={m.code}>
                    <span className="text-zinc-300">{m.sku}</span>
                    {m.ordered && (
                      <Pill tone="amber" title="somebody has really ordered this one">
                        somebody wants it
                      </Pill>
                    )}
                    {(m.machines_with_room?.length ?? 0) > 0 && (
                      <Pill tone="blue" title="this machine still had hours today, so it was the running order that left it out — not the clock">
                        {m.machines_with_room!.join(", ")} had hours
                      </Pill>
                    )}
                    {m.month_target_litres != null && (
                      <span className="ml-1 tabular-nums text-zinc-600">
                        {litres(m.month_target_litres)} — the month&rsquo;s target
                      </span>
                    )}
                  </li>
                ))}
                {(stuck.no_line_time ?? []).length === 0 && <li className="text-zinc-500">Nothing.</li>}
              </ul>
            </div>
          </div>
          {stuck.litres_note && <p className="mt-3 text-xs text-zinc-500">{maskDigits(stuck.litres_note)}</p>}
        </Panel>
      )}

      {/* ── the drums ─────────────────────────────────────────────── */}
      {byHand.length > 0 && (
        <Panel
          title="Filled by hand — not scheduled here"
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.overview} />}
          note={maskDigits(o?.manual_fill_note ?? manual.text ?? "")}
        >
          <ul className="space-y-1 text-sm">
            {byHand.map((m) => (
              <li key={m.code} className="flex flex-wrap items-baseline gap-2 border-t border-zinc-800/60 py-1 first:border-0">
                <span className="font-mono text-[11px] text-zinc-500">{m.code}</span>
                <span>{m.sku}</span>
                <Pill tone="zinc">{maskDigits(m.display ?? manual.display ?? "")}</Pill>
                <span className="ml-auto tabular-nums text-zinc-400">
                  {m.plan_litres != null ? litres(m.plan_litres) : "—"}
                </span>
                {m.plan_pieces != null && (
                  <span className="tabular-nums text-zinc-500">
                    {inr(m.plan_pieces)} {plural(m.plan_pieces, "drum", "drums")}
                  </span>
                )}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-zinc-500">
            These are in the month&rsquo;s target and they will be filled. They are simply not put on a machine, so no
            machine is missing.
          </p>
        </Panel>
      )}

      {o?.unproducible && o.unproducible.length > 0 && (
        <Panel
          title="In the target, but no machine can fill it"
          badge={<SimBadge kind="plan" />}
          asOf={<AsOf rec={live.overview} />}
          note="Shown, never hidden. There is no 3-litre line and no drum line, so these litres cannot be made at all this month."
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-wider text-zinc-500">
                <th className="pb-1 font-normal">Product</th>
                <th className="pb-1 font-normal">Needs</th>
                <th className="pb-1 text-right font-normal">In the target</th>
                <th className="pb-1 text-right font-normal">Worth, roughly</th>
              </tr>
            </thead>
            <tbody>
              {o.unproducible.map((u) => (
                <tr key={u.code} className="border-t border-zinc-800/60">
                  <td className="py-1">
                    <span className="mr-2 font-mono text-[11px] text-zinc-500">{u.code}</span>
                    {u.sku}
                  </td>
                  <td className="py-1 text-zinc-400">{u.reason}</td>
                  <td className="py-1 text-right tabular-nums">{litres(u.plan_litres)}</td>
                  <td className="py-1 text-right tabular-nums text-amber-300">
                    {u.value_est_rs ? money(u.value_est_rs) : "—"}
                    {u.value_est_derived && <span className="ml-1 text-[10px] text-zinc-500">worked out</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}

      {o?.totals.peak_day && (
        <p className="text-xs text-zinc-500">
          Busiest day the planner picks: {dlabel(o.totals.peak_day.date)} at {litres(o.totals.peak_day.made_l)}.{" "}
          <Link href="/days" className="underline underline-offset-2 hover:text-zinc-300">
            walk the month day by day
          </Link>
          .
        </p>
      )}
    </div>
  );
}
