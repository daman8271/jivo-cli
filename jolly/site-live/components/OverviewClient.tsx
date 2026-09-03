"use client";

import NowStrip from "./NowStrip";
import ForwardStrip from "./ForwardStrip";
import LoopChain from "./LoopChain";
import { DemandSplit } from "./DemandSplit";
import { Section } from "./Card";
import { asHonesty, useLive } from "../lib/live";
import { ruleText } from "../lib/labels";
import SimBadge from "./SimBadge";

export default function OverviewClient() {
  const live = useLive(["honesty"]);
  const h = asHonesty(live.honesty);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">The plant, right now</h1>
        <SimBadge kind="live" />
      </div>
      <p className="mt-1 max-w-3xl text-sm text-zinc-300">
        {ruleText(h, "rolling-replan") ??
          "The top half is read off the plant. The bottom half is what the computer would do about it."}
      </p>

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
