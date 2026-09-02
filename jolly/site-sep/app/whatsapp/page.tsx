import { getSpine, getWhatsapp } from "../../lib/data";
import SimBadge from "../../components/SimBadge";
import { Card, Pill } from "../../components/Card";
import WaSepClient from "../../components/WaSepClient";

export const metadata = {
  title: "WhatsApp drafts",
  description:
    "Simulated WhatsApp drafts the planner would send — nothing was sent, nobody replied.",
};

const TAG_TONE: Record<string, string> = {
  "build-list": "zinc",
  unblocked: "green",
  "packaging-zero": "red",
  ordered: "blue",
  "oil-short": "red",
  weekly: "violet",
  storage: "amber",
};

export default function Whatsapp() {
  const W = getWhatsapp();
  const spine = getSpine();

  // date → site day number, for the /days/N chips inside threads
  const dayN: Record<string, number> = Object.fromEntries(spine.map((d) => [d.date, d.n]));
  const workingDays = spine.filter((d) => d.working).length;

  // The routing rule, derived from the data: the thread carrying build-list
  // drafts is the daily one; every other thread only hears on exception.
  const daily = W.threads.find((t) => t.messages.some((m) => m.tag === "build-list")) ?? null;
  const dailyBuild = daily ? daily.messages.filter((m) => m.tag === "build-list").length : 0;
  const dailyExtra = daily ? daily.count - dailyBuild : 0;
  const threads = daily ? [daily, ...W.threads.filter((t) => t !== daily)] : W.threads;

  // what the exception traffic to everyone else is about, counted from the data
  // (the daily thread's own unblocked notes are narrated in the sentence above the pills)
  const exTags = new Map<string, number>();
  for (const t of threads) {
    if (t === daily) continue;
    for (const m of t.messages) {
      if (m.tag === "build-list") continue;
      exTags.set(m.tag, (exTags.get(m.tag) ?? 0) + 1);
    }
  }
  const exTagList = [...exTags.entries()].sort((a, b) => b[1] - a[1]);

  return (
    <div>
      {/* persistent banner — sticks under the nav while the page scrolls */}
      <div className="sticky top-14 z-40 mb-4 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-violet-500/40 bg-violet-950/85 px-4 py-2 text-sm text-violet-100 backdrop-blur">
        <span className="font-semibold tracking-wide">SIMULATED — drafts, not sent.</span>
        <span className="text-violet-200/90">
          September has not happened: these {W.meta.sent} messages are what the planner <em>would</em> send. Nothing was
          delivered, and {W.meta.assumed_replies} replies exist — every bubble is flagged <code>assumed</code> in the
          data.
        </span>
      </div>

      <h1 className="text-2xl font-bold">
        WhatsApp <SimBadge kind="simulated" note={W.meta.note} />
      </h1>
      <p className="mt-1 max-w-4xl text-sm text-zinc-400">
        {W.meta.assumed_sends} simulated drafts across {W.threads.length} threads, one per recipient. Recipients are
        shown by name and role; {W.meta.masking_note}.
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card
          title="Drafts written"
          value={String(W.meta.sent)}
          tone="text-violet-300"
          sub="every one flagged assumed:true — none sent"
        />
        <Card
          title="Replies"
          value={String(W.meta.assumed_replies)}
          sub="none exist, and none are invented here"
        />
        <Card title="Threads" value={String(W.threads.length)} sub="name + role shown; numbers masked in the data" />
        <Card
          title="Daily build lists"
          value={String(dailyBuild)}
          tone="text-emerald-300"
          sub={
            daily
              ? `to ${daily.name}${dailyBuild === workingDays ? " — one per planned working day" : ""}`
              : "no daily thread in the data"
          }
        />
      </div>

      <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-400">
        <div className="text-xs uppercase tracking-wider text-zinc-500">The routing rule</div>
        <p className="mt-2 max-w-4xl leading-relaxed">
          {daily ? (
            <>
              <span className="text-zinc-200">{daily.name}</span> ({daily.title}) gets the day&apos;s build list every
              working day the plan runs — {dailyBuild} of them
              {dailyExtra > 0 ? (
                <>
                  , plus {dailyExtra} material-unblocked note{dailyExtra === 1 ? "" : "s"} for his own lines
                </>
              ) : null}
              . Everyone else is <span className="text-zinc-200">exception-only</span>: they hear nothing unless the
              plan hits something on their desk —
            </>
          ) : (
            <>Every thread is exception-only —</>
          )}
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {exTagList.map(([tag, n]) => (
            <Pill key={tag} tone={TAG_TONE[tag] ?? "zinc"}>
              {tag} × {n}
            </Pill>
          ))}
        </div>
      </div>

      <WaSepClient threads={threads} meta={W.meta} dayN={dayN} dailyName={daily?.name ?? null} />
    </div>
  );
}
