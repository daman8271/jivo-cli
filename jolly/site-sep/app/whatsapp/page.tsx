import { getSpine, getWhatsapp } from "../../lib/data";
import SimBadge from "../../components/SimBadge";
import { Card, Pill } from "../../components/Card";
import WaSepClient from "../../components/WaSepClient";

export const metadata = {
  title: "Messages (not sent)",
  description: "Messages the computer wrote for the September plan. Not sent. Nobody replied.",
};

// Message kinds, as the floor would say them. The raw tags stay in
// data/whatsapp.json; only the label changes here, at render time.
const TAG_LABEL: Record<string, string> = {
  "build-list": "run list",
  unblocked: "material arrived",
  "packaging-zero": "packing material finished",
  ordered: "ordered",
  "oil-short": "oil short",
  weekly: "week's summary",
  storage: "godown full",
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
const tagLabel = (tag: string) => TAG_LABEL[tag] ?? tag.replace(/-/g, " ");
const firstName = (name: string) => name.replace(/\(.*?\)/g, "").trim().split(/\s+/)[0];
// a role the data marked as inferred is our guess — say so plainly
const plainTitle = (title: string) => title.replace(/\(inferred\)/gi, "(our guess)");

export default function Whatsapp() {
  const W = getWhatsapp();
  const spine = getSpine();

  // date → site day number, for the /days/N chips inside a conversation
  const dayN: Record<string, number> = Object.fromEntries(spine.map((d) => [d.date, d.n]));
  const workingDays = spine.filter((d) => d.working).length;

  // Who gets what, read off the data: the person who receives run lists hears
  // every day; everyone else only hears when something is stuck.
  const named = W.threads.map((t) => ({ ...t, title: plainTitle(t.title) }));
  const daily = named.find((t) => t.messages.some((m) => m.tag === "build-list")) ?? null;
  const dailyBuild = daily ? daily.messages.filter((m) => m.tag === "build-list").length : 0;
  const dailyExtra = daily ? daily.count - dailyBuild : 0;
  const threads = daily ? [daily, ...named.filter((t) => t !== daily)] : named;
  const who = daily ? firstName(daily.name) : null;

  // what everyone else's messages are about, counted from the data
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
      {/* the one thing every view must say — sticks under the nav while the page scrolls */}
      <div className="sticky top-14 z-40 mb-4 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-violet-500/40 bg-violet-950/85 px-4 py-2 text-sm text-violet-100 backdrop-blur">
        <span className="font-semibold tracking-wide">NOT SENT.</span>
        <span>These messages were written by the computer. They were NOT sent. Nobody replied.</span>
        <span className="text-violet-300/80">
          {W.meta.sent} messages · {W.meta.assumed_replies} replies
        </span>
      </div>

      <h1 className="text-2xl font-bold">
        Messages (not sent){" "}
        <SimBadge kind="simulated" note="The computer wrote these for the September plan. Not one was sent." />
      </h1>
      <p className="mt-1 text-sm text-zinc-300">
        Yeh messages computer ne likhe hain. Bheje nahi gaye. Kisi ne jawab nahi diya.
      </p>
      <p className="mt-1 max-w-4xl text-sm text-zinc-400">
        {W.meta.assumed_sends} messages for {W.threads.length} people. Names and roles are shown.{" "}
        {W.meta.numbers_masked ? "Phone numbers are hidden." : "Phone numbers are shown."}
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card title="Messages written" value={String(W.meta.sent)} tone="text-violet-300" sub="not one was sent" />
        <Card title="Replies" value={String(W.meta.assumed_replies)} sub="nobody replied — none made up here" />
        <Card title="People" value={String(W.threads.length)} sub={W.meta.numbers_masked ? "name and role shown, phone number hidden" : "name, role and phone number shown"} />
        <Card
          title="Daily run lists"
          value={String(dailyBuild)}
          tone="text-emerald-300"
          sub={daily ? `for ${who}${dailyBuild === workingDays ? " — one for every working day" : ""}` : "nobody gets a daily list"}
        />
      </div>

      <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-400">
        <div className="text-xs uppercase tracking-wider text-zinc-500">Who gets what</div>
        <p className="mt-2 text-base text-zinc-200">
          {daily ? (
            <>{who} gets the run list every day. Everyone else only when something is stuck.</>
          ) : (
            <>Everyone gets a message only when something is stuck.</>
          )}
        </p>
        {daily && (
          <p className="mt-2 max-w-4xl leading-relaxed">
            {daily.name} ({daily.title}): {dailyBuild} run lists
            {dailyExtra > 0 ? (
              <>
                , plus {dailyExtra} &ldquo;material arrived&rdquo; note{dailyExtra === 1 ? "" : "s"}
              </>
            ) : null}
            . Messages for everyone else, by kind:
          </p>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {exTagList.map(([tag, n]) => (
            <Pill key={tag} tone={TAG_TONE[tag] ?? "zinc"}>
              {tagLabel(tag)} × {n}
            </Pill>
          ))}
        </div>
      </div>

      <WaSepClient
        threads={threads}
        meta={W.meta}
        dayN={dayN}
        dailyName={daily?.name ?? null}
        tagLabels={TAG_LABEL}
        tagTones={TAG_TONE}
      />

      <p className="mt-4 text-xs text-zinc-500">
        Where these come from: the planner writes one message for each thing it decides in the day-by-day plan. The
        people are real. The messages went to nobody.
      </p>
    </div>
  );
}
