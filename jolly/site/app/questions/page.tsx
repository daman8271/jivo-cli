import { Card, Section, Pill } from "@/components/Card";
import fs from "fs";
import path from "path";

export const metadata = { title: "Questions — JIVO Mark 1" };

type Q = {
  n: number; priority: string; question: string; why: string; blocks: string;
  guess: string; status: string; owner: string; note: string; moved: string;
};
type Doc = { asked: string; total: number; top3: number[]; note: string; questions: Q[] };

const TONE: Record<string, { pill: string; dot: string; label: string }> = {
  blocking: { pill: "red", dot: "bg-red-500", label: "Blocking — changes the model" },
  high: { pill: "amber", dot: "bg-amber-500", label: "High" },
  medium: { pill: "blue", dot: "bg-sky-500", label: "Medium" },
  low: { pill: "zinc", dot: "bg-zinc-600", label: "Low" },
};
const ORDER = ["blocking", "high", "medium", "low"];

export default function QuestionsPage() {
  const doc: Doc = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), "public", "data", "questions.json"), "utf8"),
  );
  const byPri = ORDER.map((p) => [p, doc.questions.filter((q) => q.priority === p)] as const)
    .filter(([, qs]) => qs.length > 0);

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Questions for Daman</h1>
      <p className="mt-1 max-w-3xl text-sm text-zinc-400">
        Everything the study could not settle from data, in one place — asked {doc.asked}. Each one carries my best
        guess, so a one-word confirm or correction is enough. Anything I could have looked up myself was dropped
        rather than asked.
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Card title="Open questions" value={String(doc.total)} sub="down from 34 — 12 answered from data" />
        <Card title="Blocking" value={String(doc.questions.filter((q) => q.priority === "blocking").length)}
              sub="these change the model" tone="text-red-300" />
        <Card title="With a guess attached" value={String(doc.questions.filter((q) => q.guess).length)}
              sub="confirm or correct in a word" tone="text-emerald-300" />
        <Card title="Assigned out" value={String(doc.questions.filter((q) => q.owner).length)}
              sub="needs someone other than you" />
      </div>

      <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
        <span className="font-medium">If you only answer three, make it {doc.top3.join(", ")}</span> — the ceiling,
        the shift length, and whether the planner may schedule short. Those three move the model; the rest sharpen it.
        <div className="mt-1 text-amber-200/80">{doc.note}</div>
      </div>

      {byPri.map(([pri, qs]) => (
        <Section key={pri} title={TONE[pri].label}
                 right={<span className="text-xs text-zinc-500">{qs.length} question{qs.length === 1 ? "" : "s"}</span>}>
          <div className="space-y-3">
            {qs.map((q) => (
              <div key={q.n} className="rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden">
                <div className="flex gap-3 p-4">
                  <div className="flex flex-col items-center gap-1.5 pt-0.5">
                    <span className={`h-2 w-2 rounded-full ${TONE[q.priority].dot}`} />
                    <span className="text-xs tabular-nums text-zinc-500">{q.n}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[15px] leading-relaxed text-zinc-100">{q.question}</p>

                    {q.guess && (
                      <div className="mt-2.5 rounded-lg border-l-2 border-emerald-500/50 bg-emerald-500/5 px-3 py-2">
                        <div className="text-[11px] uppercase tracking-wider text-emerald-400/80">My guess</div>
                        <div className="mt-0.5 text-sm text-zinc-300">{q.guess}</div>
                      </div>
                    )}

                    {q.moved && (
                      <div className="mt-2 rounded-lg border-l-2 border-amber-500/60 bg-amber-500/5 px-3 py-2">
                        <div className="text-[11px] uppercase tracking-wider text-amber-400/80">Changed since the rebuild</div>
                        <div className="mt-0.5 text-sm text-amber-100/90">{q.moved}</div>
                      </div>
                    )}

                    <div className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1 text-xs text-zinc-500">
                      {q.blocks && <span><span className="text-zinc-600">blocks:</span> {q.blocks}</span>}
                      {q.owner && <Pill tone="blue">{q.owner}</Pill>}
                      {q.status && <Pill tone="amber">{q.status}</Pill>}
                    </div>

                    {q.note && <div className="mt-2 text-xs italic text-zinc-500">{q.note}</div>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>
      ))}

      <p className="mt-8 text-xs text-zinc-600">
        Source: <span className="font-mono">jolly/out/QUESTIONS-FOR-DAMAN.csv</span>. Twelve further questions arose
        during the study and were answered from the data rather than asked.
      </p>
    </div>
  );
}
