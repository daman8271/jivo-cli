"use client";

// The front page, in the order a planner actually asks the questions:
//
//   1. Are we making the number today?          money, against your own target
//   2. What is each machine doing about it?     line by line
//   3. What does the plant look like right now?  the live strip
//   4. What happens between now and month end?   the computer's plan
//
// The mark before this one opened with a single number for the whole plant.
// Mark 4 opens with rupees and then goes machine by machine, because that is
// the shape of the job.

import Link from "next/link";
import NowStrip from "./NowStrip";
import ForwardStrip from "./ForwardStrip";
import LinesStrip from "./LinesStrip";
import MoneyStrip from "./MoneyStrip";
import LoopChain from "./LoopChain";
import StorageCapStrip, { StorageCapBanner } from "./StorageCapStrip";
import { DemandSplit } from "./DemandSplit";
import { Pill, Section } from "./Card";
import { asHonesty, asOverview, useLive } from "../lib/live";
import { maskDigits, ruleText } from "../lib/labels";
import { dlabel, plural, inr } from "../lib/fmt";
import SimBadge from "./SimBadge";

export default function OverviewClient() {
  const live = useLive(["honesty", "overview"]);
  const h = asHonesty(live.honesty);
  const o = asOverview(live.overview);
  const rb = o?.rulebook ?? null;
  const day1 = o?.day1 ?? null;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">The plant, right now</h1>
        <SimBadge kind="live" />
        {rb?.applied && (
          <Pill
            tone="violet"
            title={
              rb.owner
                ? `whose rules: ${rb.owner}${rb.written ? ` · written ${rb.written}` : ""}`
                : undefined
            }
          >
            rulebook {rb.version}
          </Pill>
        )}
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {ruleText(h, "rolling-replan") ??
          "The top half is read off the plant. The bottom half is what the computer would do about it."}
      </p>
      <p className="mt-1 max-w-3xl text-xs text-zinc-500">
        {day1 ? `The plan calls ${dlabel(day1.date)} day one${day1.weekday ? ` — a ${day1.weekday}` : ""}. ` : ""}
        Everything the plan does rests on rules and guesses that are written down:{" "}
        <Link href="/assumptions" className="underline underline-offset-2 hover:text-zinc-300">
          what this plan takes as fact
        </Link>
        {o?.warnings_count
          ? ` · ${inr(o.warnings_count)} ${plural(o.warnings_count, "thing", "things")} the planner wants you to know before quoting a number${
              o.warnings_where ? ` — ${maskDigits(o.warnings_where)}` : ""
            }`
          : ""}
        .
      </p>

      {/* B20 — the cap that decides most of this month, at the top where it cannot be
          missed. The page exists to make the rules visible and this was the one rule
          it did not carry. */}
      <StorageCapBanner />

      <Section title="Money — today against the target">
        <MoneyStrip />
      </Section>

      <Section title="The one limit that governs the whole plan">
        <StorageCapStrip />
      </Section>

      <Section title="Line by line — today">
        <LinesStrip />
      </Section>

      <Section title="Now — read off the plant">
        <NowStrip />
      </Section>

      <Section title="From here to the end of the month — the computer's plan">
        <ForwardStrip />
      </Section>

      <Section title="The demand behind it">
        <DemandSplit />
      </Section>

      <Section title="How a stuck product gets unstuck">
        <LoopChain limit={8} />
      </Section>
    </div>
  );
}
