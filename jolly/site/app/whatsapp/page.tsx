import { getThreads } from "@/lib/data";
import { Card, Pill } from "@/components/Card";
import WaClient from "@/components/WaClient";
import type { Thread } from "@/lib/types";

export const metadata = { title: "WhatsApp — JIVO Mark 1" };

const TAG_TONE: Record<string, string> = {
  "packaging-zero": "red",
  "oil-short": "red",
  storage: "amber",
  decision: "amber",
  "po-shift": "blue",
  labour: "green",
  weekly: "zinc",
  "day-brief": "zinc",
};

export default function WhatsAppPage() {
  const threads: Thread[] = [...getThreads()].sort(
    (a, b) => b.count - a.count || b.messages.length - a.messages.length
  );

  const all = threads.flatMap((t) => t.messages);
  const sent = all.filter((m) => m.dir === "out").length;
  const back = all.filter((m) => m.dir === "in").length;
  const days = new Set(all.map((m) => m.day)).size;

  const tags = new Map<string, number>();
  for (const m of all) tags.set(m.tag, (tags.get(m.tag) ?? 0) + 1);
  const tagList = [...tags.entries()].sort((a, b) => b[1] - a[1]);

  const top = threads[0];
  const topSent = (top?.messages ?? []).filter((m) => m.dir === "out").length;
  const topTags = new Map<string, number>();
  for (const m of top?.messages ?? []) topTags.set(m.tag, (topTags.get(m.tag) ?? 0) + 1);
  const topTag = [...topTags.entries()].sort((a, b) => b[1] - a[1])[0];

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">WhatsApp</h1>
      <p className="mt-1 max-w-3xl text-sm text-zinc-400">
        Every message the plan would have sent in August, to whom, on which day — and the reply the simulation wrote in. Click a person on the
        left to read their thread. Pick a day at the top to see only that day.
      </p>
      <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-sm text-amber-100">The outgoing messages are what the planner would have sent. <span className="font-medium">The replies are written in by the simulation, not received</span> — nobody in this list was actually messaged in August 2026. Names and numbers are real; the conversations are not.</div>

      <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Card title="People messaged" value={String(threads.length)} sub="everyone the plan wrote to" />
        <Card
          title="Messages sent"
          value={String(sent)}
          sub={top ? `${topSent} of them to ${top.name}` : undefined}
          tone="text-emerald-300"
        />
        <Card title="Replies written in" value={String(back)} sub="assumed by the simulation, not received" tone="text-amber-300" />
        <Card title="Days with messages" value={`${days} of 31`} sub={`nothing sent on the other ${31 - days} days`} />
      </div>

      {top && topTag && (
        <p className="mt-3 text-sm text-zinc-400">
          Most chased: <span className="text-zinc-200">{top.name}</span> — {topSent} of the {sent} messages sent. In that
          thread {topTag[1]} of {top.messages.length} messages are tagged{" "}
          <span className="text-zinc-200">{topTag[0]}</span>.
        </p>
      )}

      <div className="mt-5">
        <WaClient threads={threads} />
      </div>

      <div className="mt-5 rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-3">
        <div className="text-xs uppercase tracking-wider text-zinc-500">What the messages were about</div>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
          {tagList.map(([tag, n]) => (
            <span key={tag} className="flex items-center gap-1.5">
              <Pill tone={TAG_TONE[tag] ?? "zinc"}>{tag}</Pill>
              <span className="text-xs text-zinc-400">{n}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
