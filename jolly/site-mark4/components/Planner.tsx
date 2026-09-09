"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Day, Mark4Model, Run, Scenario } from "@/lib/types";
import { validateScenario } from "@/lib/scenario";
import { formatDuration, formatSetupDuration } from "@/lib/duration";
import ThemeToggle from "./ThemeToggle";
import MaterialSupply from "./MaterialSupply";
import LiveShiftBoard from "./LiveShiftBoard";
import TodayReview from "./TodayReview";
import DispatchBoard from "./DispatchBoard";

type View =
  | "today"
  | "today-review"
  | "plan"
  | "machines"
  | "materials"
  | "dispatch"
  | "demand"
  | "actuals"
  | "rules";
const views: { id: View; title: string; path: string }[] = [
  { id: "today-review", title: "Today’s review", path: "M4 4h16v16H4z M8 9l2 2 5-5 M8 15h8" },
  { id: "today", title: "Shift board", path: "M3 4h18v16H3z M3 9h18 M8 9v11" },
  {
    id: "plan",
    title: "Month plan",
    path: "M4 5h16v16H4z M8 3v4 M16 3v4 M4 10h16 M8 14h2 M14 14h2 M8 18h2",
  },
  {
    id: "machines",
    title: "Machines",
    path: "M3 20V9l6 3V7l6 4V4h5v16z M7 16h1 M12 16h1 M17 16h1",
  },
  {
    id: "materials",
    title: "Materials",
    path: "M12 3l9 5v9l-9 5-9-5V8z M3 8l9 5 9-5 M12 13v9 M7 5l10 6",
  },
  {
    id: "dispatch",
    title: "Godown & dispatch",
    path: "M3 5h12v12H3z M15 10h4l3 4v3h-7 M7 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4 M18 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4",
  },
  {
    id: "demand",
    title: "Demand",
    path: "M4 20V4 M4 20h17 M8 16v-5 M13 16V7 M18 16V4",
  },
  {
    id: "actuals",
    title: "What happened",
    path: "M3 12a9 9 0 1 0 3-7 M3 3v5h5 M12 7v5l3 2",
  },
  {
    id: "rules",
    title: "Rules & questions",
    path: "M5 3h14v18H5z M9 7h6 M9 11h6 M9 15h3",
  },
];
const number = (n: number | null | undefined, digits = 0) =>
  n == null || !Number.isFinite(n)
    ? "Not read"
    : new Intl.NumberFormat("en-IN", { maximumFractionDigits: digits }).format(
        n,
      );
const litres = (n: number | null | undefined) =>
  n == null ? "Not read" : `${number(n)} L`;
const money = (n: number | null | undefined) =>
  n == null
    ? "Not valued"
    : Math.abs(n) >= 1e7
      ? `₹${number(n / 1e7, 2)} Cr`
      : Math.abs(n) >= 1e5
        ? `₹${number(n / 1e5, 2)} lakh`
        : `₹${number(n)}`;
const date = (
  s: string | null | undefined,
  options: Intl.DateTimeFormatOptions = { day: "numeric", month: "short" },
) => {
  if (!s) return "Not read";
  const parsed = new Date(s.length === 10 ? `${s}T12:00:00+05:30` : s);
  return Number.isNaN(parsed.getTime())
    ? "Not read"
    : new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        ...options,
      }).format(parsed);
};
const time = (s: string | null | undefined) =>
  date(s, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
const percent = (a: number, b: number) =>
  b > 0 ? Math.min(100, Math.max(0, (a / b) * 100)) : 0;
const shortProduct = (s: string) =>
  s
    .replace(/JIVO\s*/gi, "")
    .replace(/\s+/g, " ")
    .trim();

function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-note">{note}</div>
    </div>
  );
}
function Tag({
  children,
  tone = "",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`pill ${tone}`}>{children}</span>;
}
function Empty({ children }: { children: React.ReactNode }) {
  return <p className="empty">{children}</p>;
}
function Title({
  title,
  text,
  extra,
}: {
  title: string;
  text: string;
  extra?: React.ReactNode;
}) {
  return (
    <header className="page-title">
      <div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
      {extra}
    </header>
  );
}

export default function Planner() {
  const [view, setView] = useState<View>("today");
  const [model, setModel] = useState<Mark4Model | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [runDate, setRunDate] = useState("");
  const requestId = useRef(0);
  const scenarioRef = useRef<Scenario | undefined>(undefined);
  const inFlightRequest = useRef<number | null>(null);
  const load = useCallback(async (scenario?: Scenario) => {
    const id = ++requestId.current;
    inFlightRequest.current = id;
    setBusy(true);
    setError(null);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 60000);
    try {
      const response = await fetch(
        "/api/model",
        scenario
          ? {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(scenario),
              cache: "no-store",
              signal: controller.signal,
            }
          : { cache: "no-store", signal: controller.signal },
      );
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(
          body?.error ||
            `The planner could not refresh (${response.status}). Try again.`,
        );
      }
      const next = (await response.json()) as Mark4Model;
      if (
        !Array.isArray(next.days) ||
        !Array.isArray(next.lines) ||
        !Array.isArray(next.planningSpeeds) ||
        !next.summary ||
        !next.meta
      )
        throw new Error(
          "The planner returned an incomplete response. Try refreshing.",
        );
      if (id === requestId.current) {
        setModel(next);
        setRun(null);
        scenarioRef.current = next.scenario;
        try {
          localStorage.setItem(
            "jivo-mark4-scenario-v1",
            JSON.stringify(next.scenario),
          );
        } catch {
          /* Private browsing may disable storage. */
        }
      }
    } catch (e) {
      if (id === requestId.current)
        setError(
          e instanceof Error
            ? e.name === "AbortError"
              ? "The refresh took too long. Try again; the previous plan has been kept."
              : e.message
            : "The planner could not refresh. Try again.",
        );
    } finally {
      window.clearTimeout(timeout);
      if (id === requestId.current) {
        inFlightRequest.current = null;
        setBusy(false);
        setLoading(false);
      }
    }
  }, []);
  useEffect(() => {
    let stored: Scenario | undefined;
    try {
      const candidate = JSON.parse(
        localStorage.getItem("jivo-mark4-scenario-v1") || "null",
      );
      if (candidate && typeof candidate === "object" && !Array.isArray(candidate))
        stored = validateScenario(candidate);
    } catch {
      /* A corrupt saved scenario is ignored. */
    }
    void load(stored);
    const timer = setInterval(() => {
      // A background refresh must not supersede a scenario the user is applying.
      if (document.visibilityState === "visible" && inFlightRequest.current === null)
        void load(scenarioRef.current);
    }, 60000);
    return () => clearInterval(timer);
  }, [load]);
  useEffect(() => {
    const sync = () => {
      const candidate = location.hash.slice(1) as View;
      if (views.some((v) => v.id === candidate)) setView(candidate);
    };
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);
  const day =
    model?.days.find((d) => d.date === selectedDate) || model?.days[0];
  const openRun = (r: Run, d: string) => {
    setRun(r);
    setRunDate(d);
  };
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="side-nav">
        <div>
          <div className="brand">
            JIVO<span>MARK IV</span>
          </div>
          <p className="brand-caption">Production planning</p>
        </div>
        <nav className="nav-list" aria-label="Planner sections">
          {views.map((v) => (
            <a
              key={v.id}
              className="nav-item"
              href={`#${v.id}`}
              aria-current={view === v.id ? "page" : undefined}
              onClick={() => {
                setView(v.id);
                setRun(null);
              }}
            >
              <svg viewBox="0 0 24 24" className="nav-icon" aria-hidden="true">
                <path d={v.path} />
              </svg>
              {v.title}
            </a>
          ))}
        </nav>
        <div className="nav-footer">
          <p>
            Built around the way
            <br />
            your factory works.
          </p>
          <p>
            Machine rules from the
            <br />
            Gurvinder meeting.
          </p>
        </div>
      </aside>
      <main className="main" id="main-content">
        <div className="topline">
          <div className="topline-left">
            <span>Wellness factory</span>
            {model && (
              <span>
                <i
                  className={`dot ${model.meta.feedStatus === "live" && model.demandBook?.coverage !== "partial" ? "" : "warn"}`}
                />
                {model.meta.feedStatus === "seed"
                  ? "Saved source snapshot"
                  : model.demandBook?.coverage === "partial"
                    ? "Partial source coverage"
                    : model.meta.feedStatus === "live"
                      ? "Live source inputs"
                      : "Using last available inputs"}
              </span>
            )}
          </div>
          <div className="topline-actions">
            <ThemeToggle />
            <button
              className="subtle-button"
              disabled={busy}
              onClick={() => void load(scenarioRef.current)}
            >
              {busy ? "Refreshing…" : "Refresh data"}
            </button>
          </div>
        </div>
        {view === "today-review" ? <TodayReview /> : loading ? (
          <div className="loading-shell" role="status">
            <div className="loader" />
            <h1>Reading the factory.</h1>
            <p>Matching demand, materials and machine rules.</p>
          </div>
        ) : !model ? (
          <div className="loading-shell" role="alert">
            <h1>The plan is unavailable.</h1>
            <p>{error}</p>
            <button className="primary-button" onClick={() => void load()}>
              Try again
            </button>
          </div>
        ) : (
          <>
            {error && (
              <div className="notice error" role="alert">
                <span>{error} The previous plan is still shown.</span>
                <button
                  className="text-button"
                  onClick={() => void load(scenarioRef.current)}
                >
                  Retry
                </button>
              </div>
            )}
            {model.meta.feedStatus !== "live" && (
              <div className="notice">
                <span>
                  {model.meta.feedStatus === "seed"
                    ? "This plan uses a saved factory snapshot."
                    : "Some source records are incomplete or out of date."}{" "}
                  Inputs dated {time(model.meta.inputAsOf)} IST. Check current
                  stock before acting.
                </span>
                <a href="#rules" className="text-button">
                  Source details
                </a>
              </div>
            )}
            {Object.keys(model.scenario.arrivalDates || {}).length > 0 && (
              <div className="notice">
                <span>
                  <strong>Your arrival scenario.</strong>{" "}
                  {Object.keys(model.scenario.arrivalDates || {}).length}{" "}
                  source-event arrival dates are your assumptions. The forward
                  plan uses them; supplier dates and recorded actuals remain
                  separate.
                </span>
                <a className="text-button" href="#materials">
                  Review assumed dates
                </a>
              </div>
            )}
            {model.scenario.allowProvisionalRecipes && (
              <div className="notice">
                <span>
                  <strong>Conditional carton scenario.</strong>{" "}
                  {(model.summary.conditionalRecipeLitres ?? model.summary.conditionalLitres) > 0 ? (
                    <>
                      {litres(model.summary.conditionalRecipeLitres ?? model.summary.conditionalLitres)} of output
                      depends on unconfirmed replacement recipes.{" "}
                    </>
                  ) : (
                    <>
                      No additional carton substitution passed the bottle and
                      closure checks; the plan is unchanged for this
                      setting.{" "}
                    </>
                  )}
                  {model.summary.strictBaseline && (
                    <>
                      Strict recipe baseline:{" "}
                      {litres(model.summary.strictBaseline.plannedLitres)} /{" "}
                      {money(model.summary.strictBaseline.plannedValue)}.
                    </>
                  )}{" "}
                  This does not approve a packaging change.
                </span>
                <a className="text-button" href="#rules">
                  Review substitutions
                </a>
              </div>
            )}
            {view === "today" && (
              <Today
                model={model}
                busy={busy}
                onScenario={load}
                openRun={openRun}
              />
            )}
            {view === "plan" && (
              <MonthPlan
                model={model}
                day={day}
                selectDay={setSelectedDate}
                openRun={openRun}
              />
            )}
            {view === "machines" && <Machines model={model} />}
            {view === "materials" && (
              <Materials model={model} busy={busy} onScenario={load} />
            )}
            {view === "dispatch" && <Dispatch model={model} />}
            {view === "demand" && <Demand model={model} />}
            {view === "actuals" && <Actuals model={model} />}
            {view === "rules" && <Rules model={model} />}
            <footer className="footer">
              <span>
                Computed {time(model.meta.generatedAt)} IST. Source dates may
                differ.
              </span>
              <span>
                Future days are simulated. Factory records are shown separately.
              </span>
            </footer>
          </>
        )}
      </main>
      {run && (
        <RunDrawer
          run={run}
          dateString={runDate}
          close={() => setRun(null)}
          model={model!}
        />
      )}
    </div>
  );
}

function ScenarioPanel({
  model,
  busy,
  onScenario,
}: {
  model: Mark4Model;
  busy: boolean;
  onScenario: (s: Scenario) => Promise<void>;
}) {
  const [draft, setDraft] = useState(model.scenario);
  const appliedKey = JSON.stringify(model.scenario);
  useEffect(() => setDraft(JSON.parse(appliedKey) as Scenario), [appliedKey]);
  const changed = JSON.stringify(draft) !== JSON.stringify(model.scenario);
  return (
    <form
      className="scenario"
      onSubmit={(e) => {
        e.preventDefault();
        void onScenario(draft);
      }}
    >
      <h2>Try a different shift</h2>
      <label className="field"><span>Day shift starts (IST, provisional)</span><select value={draft.shiftStartHour ?? 8} onChange={e => setDraft({ ...draft, shiftStartHour: Number(e.target.value) })}>{Array.from({ length: 24 }, (_, hour) => <option key={hour} value={hour}>{String(hour).padStart(2, "0")}:00</option>)}</select></label>
      <p className="source-text">08:00 is a temporary scenario setting, not a confirmed factory shift. Material ready during a shift can use the remaining hours; QC does not automatically add a day.</p>
      <p>Recalculate the month. These controls change the simulation only.</p>
      <label className="field">
        <span>Line to run at night</span>
        <select
          value={draft.nightLine ?? "none"}
          onChange={(e) =>
            setDraft({
              ...draft,
              nightLine: e.target.value === "none" ? null : e.target.value,
            })
          }
        >
          <option value="auto">Let the planner choose</option>
          <option value="none">No night shift</option>
          {model.lines.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </select>
      </label>
      <p className="source-text">
        Machine speeds use your approved table directly. See Machines or Rules &amp; questions for every pack.
      </p>
      {!model.materialSupply && <label className="check-field">
        <input
          type="checkbox"
          checked={draft.allowProposedSupply}
          onChange={(e) =>
            setDraft({ ...draft, allowProposedSupply: e.target.checked })
          }
        />
        <span>
          Include hypothetical new purchases
          <br />
          <small>
            Tests suggested buys at provisional lead times. Existing orders use
            their source dates or your arrival assumptions.
          </small>
        </span>
      </label>}
      <label className="check-field">
        <input
          type="checkbox"
          checked={draft.allowProvisionalRecipes}
          onChange={(e) =>
            setDraft({ ...draft, allowProvisionalRecipes: e.target.checked })
          }
        />
        <span>
          Try unconfirmed carton substitutions
          <br />
          <small>
            Use an evidenced bottle match with an unapproved replacement carton.
            Output stays conditional.
          </small>
        </span>
      </label>
      <button className="primary-button" type="submit" disabled={busy}>
        {busy
          ? "Recalculating…"
          : changed
            ? "Recalculate plan"
            : "Run this scenario"}
      </button>
      <p className="scenario-note" aria-live="polite">
        {changed
          ? "Changes are not applied yet."
          : "Applied scenario. Choices stay on this device when browser storage is available."}
      </p>
    </form>
  );
}
function ShiftBoard({
  model,
  day,
  openRun,
}: {
  model: Mark4Model;
  day?: Day;
  openRun: (r: Run, d: string) => void;
}) {
  if (!day)
    return (
      <div className="board">
        <div className="board-header">
          <h2>No future days available</h2>
        </div>
        <div className="board-foot">
          Refresh the source data to create a new planning horizon.
        </div>
      </div>
    );
  return (
    <section
      className="board"
      aria-label={`Planned production for ${date(day.date)}`}
    >
      <div className="board-header">
        <div>
          <h2>
            {`Scenario plan, ${date(day.date)}`}
          </h2>
          <p>
            {day.sunday
              ? "Full-day projection. Production closed; dispatch relief continues."
              : "Full-day projection, not time remaining tonight. Select a product to see the reasoning."}
          </p>
        </div>
        <div className="shift-legend">
          <span>
            <i className="legend-chip" />
            Day
          </span>
          <span>
            <i className="legend-chip night" />
            Night added
          </span>
        </div>
      </div>
      {model.lines.map((line) => {
        const runs = day.runs.filter((r) => r.line === line.id);
        const total = runs.reduce((n, r) => n + r.litres, 0);
        const reason = day.blockers.find((b) => b.line === line.id)?.reason;
        return (
          <div className="line-row" key={line.id}>
            <div className="line-name">
              {line.name}
              <small>
                {day.nightLine === line.id
                  ? "Day + night"
                  : day.sunday
                    ? "Closed"
                    : "Day shift"}
              </small>
            </div>
            <div className="run-track">
              {runs.length ? (
                runs.map((r, i) => (
                  <button
                    key={`${r.code}-${i}`}
                    className={`run-block ${r.nightHours > 0 ? "night" : ""}`}
                    onClick={() => openRun(r, day.date)}
                    title={`${r.product}. ${r.reason}`}
                  >
                    <strong>{shortProduct(r.product)}</strong>
                    <span>
                      {formatDuration(r.hours)} production · {number(r.pieces)} pieces
                      {r.conditionalRecipe ? " · Conditional carton" : ""}{r.conditionalSupply ? " · Estimated supply" : ""}
                    </span>
                    <span style={{ display: "block" }}>Setup: {formatSetupDuration(r)}</span>
                  </button>
                ))
              ) : (
                <div className="run-empty" title={reason}>
                  {day.sunday
                    ? "Production closed"
                    : reason || "No feasible run in this scenario"}
                </div>
              )}
            </div>
            <div className="line-qty">
              {litres(total)}
              <small>
                {runs.length
                  ? money(
                      runs.every((r) => r.value !== null)
                        ? runs.reduce((n, r) => n + (r.value ?? 0), 0)
                        : null,
                    )
                  : "Planned output"}
              </small>
            </div>
          </div>
        );
      })}
      <div className="board-foot">
        {day.sunday
          ? "A closed production day does not close the dispatch queue."
          : "Output respects machine eligibility, material availability and godown capacity."}
      </div>
    </section>
  );
}
function Today({
  model,
  busy,
  onScenario,
  openRun,
}: {
  model: Mark4Model;
  busy: boolean;
  onScenario: (s: Scenario) => Promise<void>;
  openRun: (r: Run, d: string) => void;
}) {
  const [scenarioDate, setScenarioDate] = useState("");
  const [showSunday, setShowSunday] = useState(false);
  const day = model.days.find((d) => d.date === scenarioDate) || model.days[0];
  const upcoming = model.days.find((d) => !d.sunday && (!day || d.date >= day.date));
  const boardDay = day?.sunday && !showSunday ? upcoming || day : day;
  const blockers = boardDay?.blockers || [];
  return (
    <>
      <Title
        title="A plan for every line."
        text="See what can run, what is holding it back, and how the month adds up."
        extra={
          <span className="date-pill">
            {date(model.meta.startDate)} — {date(model.meta.endDate)}
          </span>
        }
      />
      <LiveShiftBoard />
      <div className="scenario-separator"><div><h2>Try a different plan</h2><p>Your scenario changes the projection below. The original daily plan above stays fixed.</p><p>The date stays on the selected day through the night. Choose another date to view its full-day plan.</p></div><label className="scenario-date-label" htmlFor="scenario-date">Scenario date<select id="scenario-date" value={day?.date || ""} onChange={(event) => { setScenarioDate(event.target.value); setShowSunday(false); }}>{model.days.map((d) => <option key={d.date} value={d.date}>{date(d.date)}{d.sunday ? " · Sunday" : ""}</option>)}</select></label></div>
      {day?.sunday && <div className="notice info"><span>{date(day.date)} is closed for dispatch relief. {showSunday || !upcoming ? "Showing the closed lines." : `The board shows the next production day, ${date(upcoming.date)}.`}</span>{upcoming && <button className="text-button" onClick={() => setShowSunday(!showSunday)}>{showSunday ? "Show next production day" : "Show Sunday"}</button>}</div>}
      <div className="board-layout">
        <ShiftBoard model={model} day={boardDay} openRun={openRun} />
        <ScenarioPanel model={model} busy={busy} onScenario={onScenario} />
      </div>
      <div className="metrics-strip">
        <Metric
          label="Planned this month’s remainder"
          value={litres(model.summary.plannedLitres)}
          note={`${number(model.summary.productionDays)} production days in the horizon`}
        />
        <Metric
          label={
            model.summary.plannedValue === null
              ? "Valued portion of production"
              : "Production value"
          }
          value={money(
            model.summary.plannedValue ?? model.summary.knownPlannedValue,
          )}
          note={
            model.summary.unvaluedLitres > 0
              ? `${litres(model.summary.unvaluedLitres)} has no price`
              : "Estimated from product realisation rates"
          }
        />
        <Metric
          label="Still to make"
          value={litres(model.summary.unmetLitres)}
          note="Required demand left unscheduled"
        />
        <Metric
          label="Peak godown occupancy"
          value={`${number((model.summary.peakStorageLitres / model.summary.storageLimitLitres) * 100)}%`}
          note={`Against your ${litres(model.summary.storageLimitLitres)} working limit`}
        />
      </div>
      <div className="two-col section">
        <section className="panel">
          <div className="panel-head">
            <h2>
              {day?.sunday
                ? "Next production day"
                : "Production value against target"}
            </h2>
            <Tag tone="teal">Plan</Tag>
          </div>
          {upcoming ? (
            <>
              <p className="metric-value">
                {money(
                  upcoming.productionValue ?? upcoming.knownProductionValue,
                )}{" "}
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: 500,
                    letterSpacing: 0,
                    color: "var(--muted)",
                  }}
                >
                  of {money(upcoming.targetValue)}
                </span>
              </p>
              <div
                className="meter"
                role="meter"
                aria-label="Production value target coverage"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={percent(
                  upcoming.productionValue ?? upcoming.knownProductionValue,
                  upcoming.targetValue,
                )}
              >
                <span
                  style={{
                    width: `${percent(upcoming.productionValue ?? upcoming.knownProductionValue, upcoming.targetValue)}%`,
                  }}
                />
              </div>
              <p className="caption">
                {date(upcoming.date)}:{" "}
                {upcoming.targetGap == null
                  ? `${litres(upcoming.unvaluedLitres)} has no valuation. The amount above is the known subtotal; the full target gap is unknown.`
                  : upcoming.targetGap > 0
                    ? `${money(upcoming.targetGap)} below the daily production target.`
                    : "Daily production target met in this scenario."}{" "}
                The minimum is {money(model.summary.minimumDailyValue)}; the
                desired daily output is {money(model.summary.desiredDailyValue)}
                . These values describe goods made, not billing.
              </p>
            </>
          ) : (
            <Empty>No production day remains in this horizon.</Empty>
          )}
        </section>
        <section className="panel">
          <div className="panel-head">
            <h2>What needs attention</h2>
            <a className="text-button" href="#materials">
              All materials
            </a>
          </div>
          <div className="detail-list">
            {blockers.slice(0, 4).map((b, i) => (
              <div className="detail-item" key={`${b.code}-${i}`}>
                <div>
                  <strong>{shortProduct(b.product)}</strong>
                  <p>{b.reason}</p>
                </div>
                {b.missingQuantity != null && (
                  <span>
                    {number(b.missingQuantity)} {b.unit}
                  </span>
                )}
              </div>
            ))}
            {!blockers.length && (
              <Empty>
                {day?.sunday
                  ? "Production is closed today. Review the dispatch queue to release warehouse space."
                  : "No blocker is recorded for this day. Open a run to review the materials it consumes."}
              </Empty>
            )}
          </div>
        </section>
      </div>
      <section className="section">
        <div className="section-head">
          <div>
            <h2>What the factory has recorded</h2>
            <p>
              Latest line observations, separate from the proposed shift above.
            </p>
          </div>
          <a className="text-button" href="#actuals">
            View actuals
          </a>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Line</th>
                <th>Recorded product</th>
                <th>Status</th>
                <th>Source read at</th>
              </tr>
            </thead>
            <tbody>
              {model.lines.map((l) => (
                <tr key={l.id}>
                  <td>
                    <strong>{l.name}</strong>
                  </td>
                  <td>
                    {l.actual.length
                      ? l.actual.map((a, i) => (
                          <span key={i}>
                            {shortProduct(a.product)}
                            {i < l.actual.length - 1 ? "; " : ""}
                          </span>
                        ))
                      : "Not read"}
                  </td>
                  <td>
                    {l.actual.map((a) => a.status).join(", ") ||
                      "No line observation"}
                  </td>
                  <td>{time(l.actual[0]?.asOf)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function zeroDayHint(day: Day): string {
  if (!day.blockers.length) return "No remaining feasible demand";
  const reasons = new Set(
    day.blockers.map((b) =>
      b.materialCode
        ? "materials"
        : /godown space is full/i.test(b.reason)
          ? "space"
          : /available sessions/i.test(b.reason)
            ? "sessions"
            : "rules",
    ),
  );
  if (reasons.size > 1) return "Multiple constraints";
  if (reasons.has("materials")) return "Usable supply not yet supported";
  if (reasons.has("space")) return "Godown full";
  if (reasons.has("sessions")) return "Sessions unavailable";
  return "Pack or machine constraint";
}
function MonthPlan({
  model,
  day,
  selectDay,
  openRun,
}: {
  model: Mark4Model;
  day?: Day;
  selectDay: (d: string) => void;
  openRun: (r: Run, d: string) => void;
}) {
  return (
    <>
      <Title
        title="The rest of the month."
        text="Each day starts with the stock left by the previous one. Select a date to inspect its runs and constraints."
        extra={<Tag tone="blue">Forward simulation</Tag>}
      />
      {model.actuals.some((a) => a.date < model.meta.startDate) && (
        <section
          className="recorded-strip"
          aria-label="Recorded earlier this month"
        >
          <div className="section-head">
            <div>
              <h2>Recorded earlier this month</h2>
              <p>
                Two overlapping records. Estimated worth is not billing; never
                add these records together.
              </p>
            </div>
            <a className="text-button" href="#actuals">
              What happened
            </a>
          </div>
          <div className="recorded-days">
            {model.actuals
              .filter(
                (a) =>
                  a.date < model.meta.startDate &&
                  a.date.slice(0, 7) === model.meta.startDate.slice(0, 7),
              )
              .map((a) => (
                <a href="#actuals" key={a.date} className="recorded-day">
                  <strong>{date(a.date)}</strong>
                  <Tag tone={a.complete ? "blue" : "amber"}>
                    {a.complete ? "Recorded" : "Partial"}
                  </Tag>
                  <span>
                    Booked <b>{litres(a.made_booked_l)}</b>
                  </span>
                  <RecordedValue value={a.bookedValue} compact />
                  <span>
                    Machine log <b>{litres(a.made_mes_l)}</b>
                  </span>
                  <RecordedValue value={a.mesValue} compact />
                </a>
              ))}
          </div>
        </section>
      )}
      <div className="section-head">
        <h2>Forward plan</h2>
        <Tag tone="teal">Simulation</Tag>
      </div>
      <div className="calendar-grid">
        {model.days.map((d) => (
          <button
            key={d.date}
            onClick={() => selectDay(d.date)}
            className={`calendar-day ${d.sunday ? "closed" : ""} ${day?.date === d.date ? "selected" : ""}`}
            aria-pressed={day?.date === d.date}
          >
            <small>{date(d.date, { weekday: "short", month: "short" })}</small>
            <span className="day-number">
              {date(d.date, { day: "numeric" })}
            </span>
            <strong>
              {d.sunday ? "Dispatch relief" : litres(d.productionLitres)}
            </strong>
            <div className="day-value">
              {d.sunday
                ? "Production closed"
                : d.productionValue === null
                  ? `${money(d.knownProductionValue)} valued`
                  : money(d.productionValue)}
              {!d.sunday && d.productionLitres === 0 && (
                <>
                  <small className="calendar-blocker">{zeroDayHint(d)}</small>
                  <small className="calendar-action">Inspect blockers</small>
                </>
              )}
            </div>
          </button>
        ))}
      </div>
      {day && (
        <>
          <div className="section">
            <ShiftBoard model={model} day={day} openRun={openRun} />
          </div>
          <IdleReason model={model} day={day} />
          <div className="metrics-strip">
            <Metric
              label={
                day.productionValue === null
                  ? "Valued portion of production"
                  : "Production value"
              }
              value={money(day.productionValue ?? day.knownProductionValue)}
              note={
                day.productionValue === null
                  ? `${litres(day.unvaluedLitres)} unvalued; target ${money(day.targetValue)}`
                  : `Target ${money(day.targetValue)}`
              }
            />
            <Metric
              label="Closing godown"
              value={litres(day.storage.closingLitres)}
              note={
                day.storage.overLimitLitres > 0
                  ? `${litres(day.storage.overLimitLitres)} above limit`
                  : `Working limit ${litres(day.storage.limitLitres)}`
              }
            />
            <Metric
              label="Dispatch relief"
              value={litres(day.dispatchLitres)}
              note="Simulated physical departure"
            />
            <Metric
              label="Night line"
              value={
                model.lines.find((l) => l.id === day.nightLine)?.name || "None"
              }
              note="Only one line can run at night"
            />
          </div>
          <div className="two-col section">
            <section className="panel">
              <div className="panel-head">
                <h2>Arrivals assumed this day</h2>
              </div>
              {day.arrivals.length ? (
                day.arrivals.map((a, i) => (
                  <div className="detail-item" key={`${a.code}-${i}`}>
                    <div>
                      <strong>{a.name}</strong>
                      <p>
                        {a.assumed
                          ? "Estimated or assumed usable supply; timing is conditional."
                          : "Recorded expected usable date; not an actual receipt."}
                      </p>
                    </div>
                    <span>
                      {number(a.quantity)} {a.unit}
                    </span>
                  </div>
                ))
              ) : (
                <Empty>No dated usable supply is supported for this day. Undated orders may still be outstanding; this does not mean nothing will arrive.</Empty>
              )}
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Unscheduled products</h2>
                <Tag tone="amber">
                  {number(day.blockers.length)} constraints
                </Tag>
              </div>
              {day.blockers.length ? (
                day.blockers.map((b, i) => (
                  <div className="detail-item" key={`${b.code}-${i}`}>
                    <div>
                      <strong>{shortProduct(b.product)}</strong>
                      <p>{b.reason}</p>
                    </div>
                  </div>
                ))
              ) : (
                <Empty>No product constraint is recorded for this day.</Empty>
              )}
            </section>
          </div>
        </>
      )}
    </>
  );
}
function Machines({ model }: { model: Mark4Model }) {
  return (
    <>
      <Title
        title="Know the machine first."
        text="The preferred packs, eligible products and declared speeds behind every proposed run. Manual filling is not modelled."
      />
      <div className="machine-grid">
        {model.lines.map((line) => (
          <section className="machine-card" key={line.id}>
            <header>
              <div>
                <h2>{line.name}</h2>
                <p>{line.description}</p>
              </div>
              <Tag tone="teal">{number(line.utilization * 100)}% used</Tag>
            </header>
            <div className="rule-line">
              <strong>Month plan</strong>
              <span>
                {litres(line.plannedLitres)} across {formatDuration(line.hours)}{" "}
                planned line time, including setup
              </span>
            </div>
            <div className="rule-line">
              <strong>Night filling time</strong>
              <span>{formatDuration(line.nightHours)} in this scenario</span>
            </div>
            <div className="rule-line">
              <strong>Future shift</strong>
              <span>
                {line.labourPerSession == null
                  ? "Session cost not read from the factory app"
                  : `${money(line.labourPerSession)} per session`}
              </span>
            </div>
            <RecordedLabour line={line} />
            <div className="subheading">Declared planning speed</div>
            {line.rates.map((r, i) => (
              <div className="rate-row" key={`${r.pack}-${i}`}>
                <div>
                  <strong>{r.pack}</strong>
                  <p className="source-text">
                    {r.basis} · {r.source}
                    {r.asOf ? ` · ${date(r.asOf)}` : ""}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <strong>
                    {number(r.piecesPerHour)} containers/h
                  </strong>
                  <p>Used directly</p>
                </div>
              </div>
            ))}
            {model.planningSpeeds.filter(r => r.line === line.id && r.containersPerHour === null).map(r => (
              <p className="source-text" key={r.pack}>{r.pack}: {r.status}. Production remains blocked.</p>
            ))}
            {line.id === "Pouch Machine" && <p className="source-text">Hitech only. Samarpan is not separately scheduled.</p>}
            <details>
              <summary className="text-button">Product eligibility</summary>
              {model.products
                .filter((p) => !p.exclusionReason)
                .map((p) => {
                  const e = p.eligibility[line.id];
                  return e ? (
                    <div className="detail-item" key={p.code}>
                      <div>
                        <strong>{shortProduct(p.name)}</strong>
                        <p>{e.reason}</p>
                      </div>
                      <Tag tone={e.allowed ? "teal" : ""}>
                        {e.allowed ? "Allowed" : "Excluded"}
                      </Tag>
                    </div>
                  ) : null;
                })}
            </details>
          </section>
        ))}
      </div>
      <p className="caption">
        Material, stock and demand constraints can change which feasible run is
        chosen.
      </p>
    </>
  );
}
function Materials({
  model,
  busy,
  onScenario,
}: {
  model: Mark4Model;
  busy: boolean;
  onScenario: (scenario: Scenario) => Promise<void>;
}) {
  const [query, setQuery] = useState("");
  const [onlyShort, setOnlyShort] = useState(false);
  const rows = model.materials.filter(
    (m) =>
      (!onlyShort || m.shortage > 0 || (m.proposedQty === null || m.proposedQty > 0)) &&
      `${m.code} ${m.name}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <Title
        title="Give the lines what they need."
        text="Opening material, run-level blocking gaps and proposed purchases are shown separately. Arrivals follow the selected scenario."
        extra={
          <Tag tone="amber">
            {number(
              model.materials.filter((m) => m.shortage > 0 || (m.proposedQty === null || m.proposedQty > 0))
                .length,
            )}{" "}
            materials needing attention
          </Tag>
        }
      />
      <MaterialSupply model={model} busy={busy} onScenario={onScenario} />
      {!model.materialSupply && <InboundLedger model={model} busy={busy} onScenario={onScenario} />}
      <div className="incoming-head">
        <h2>Material use and proposed purchases</h2>
        <p>Proposals remain separate from source orders above.</p>
      </div>
      <div className="toolbar">
        <input
          className="search"
          aria-label="Search materials"
          placeholder="Find a material or item code"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <label className="check-field" style={{ marginTop: 0 }}>
          <input
            type="checkbox"
            checked={onlyShort}
            onChange={(e) => setOnlyShort(e.target.checked)}
          />
          Blocking or purchase needs
        </label>
        <p>{number(rows.length)} materials shown</p>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Material</th>
              <th className="numeric">Opening</th>
              <th className="numeric">Arrivals</th>
              <th className="numeric">Used in plan</th>
              <th className="numeric">Remaining</th>
              <th className="numeric">Blocking gap</th>
              <th>First blocking date</th>
              <th>Proposed purchase</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((m) => (
              <tr key={m.code}>
                <td>
                  <strong>{m.name}</strong>
                  <small>
                    {m.code} · {m.unit}
                  </small>
                  {m.note && <small>{m.note}</small>}
                </td>
                <td className="numeric">{number(m.opening)}</td>
                <td className="numeric">{number(m.arrivals)}</td>
                <td className="numeric">{number(m.consumed)}</td>
                <td className="numeric">{number(m.remaining)}</td>
                <td className="numeric">
                  {m.shortage > 0 ? (
                    <Tag tone="amber">{number(m.shortage)}</Tag>
                  ) : (
                    "—"
                  )}
                </td>
                <td>
                  {m.firstNeeded
                    ? date(m.firstNeeded)
                    : "No dated production shortfall"}
                </td>
                <td>
                  {m.proposedQty === null ? <strong>Unresolved — reconcile existing orders and loads</strong> : m.proposedQty > 0 ? (
                    <>
                      <strong>
                        {number(m.proposedQty)} {m.unit}
                      </strong>
                      {model.materialSupply ? <small>Confirm supplier timing; not included in this plan.</small> : <><small>Order by {date(m.orderBy)}</small>
                      <small>
                        Assumed arrival {date(m.projectedArrival)};{" "}
                        {number(m.leadDays)}-day provisional lead
                      </small></>}
                    </>
                  ) : (
                    "No purchase proposed"
                  )}
                </td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={8}>
                  No materials match. Clear the search or turn off “Blocking or
                  purchase needs”.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="notice info section">
        <span>
          A blocking gap is a run-level shortage, not the full purchasing need.
          Proposed purchases and arrival dates need confirmation from the
          material owner.
        </span>
        <a href="#rules" className="text-button">
          Open questions
        </a>
      </div>
    </>
  );
}
function Dispatch({ model }: { model: Mark4Model }) {
  return (
    <>
      <Title
        title="Space opens when trucks leave."
        text="Billed goods still occupy the godown. Follow the open dispatch queue and the space it releases."
      />
      <DispatchBoard />
      <div className="section-head"><div><h2>BH-BT + BH-PF space simulation</h2><p>These two Wellness warehouses are the only finished-goods storage basis. The actual dispatch board above includes Wellness and Mart.</p></div><Tag tone="blue">Simulation</Tag></div>
      <div className="metrics-strip">
        <Metric
          label="Open invoice volume"
          value={litres(model.dispatch.pendingLitres)}
          note={`Windowed, unreconciled volume; ${time(model.dispatch.asOf)}`}
        />
        <Metric
          label="Oldest open invoice in sample"
          value={
            model.dispatch.oldestDays == null
              ? "Not read"
              : `${number(model.dispatch.oldestDays)} days`
          }
          note="Windowed pending invoice-book sample"
        />
        <Metric
          label="Median age of open invoices"
          value={
            model.dispatch.medianDays == null
              ? "Not read"
              : `${number(model.dispatch.medianDays, 1)} days`
          }
          note="Pending invoice-book sample; not completed truck waits"
        />
        <Metric
          label="Working godown limit"
          value={litres(model.summary.storageLimitLitres)}
          note="Your declared finished-goods capacity"
        />
      </div>
      <div className="two-col section">
        <section className="panel">
          <div className="panel-head">
            <h2>The queue behind the estimate</h2>
            <Tag tone="amber">Read the basis</Tag>
          </div>
          <p style={{ fontSize: 13 }}>{model.dispatch.note}</p>
          <p className="caption">
            The model uses a usual wait of {number(model.dispatch.usualDays)}{" "}
            days. The recorded tail reaches {number(model.dispatch.tailDays)}{" "}
            days. A usual wait does not promise a truck date.
          </p>
        </section>
        <section className="panel">
          <div className="panel-head">
            <h2>Warehouse pressure</h2>
          </div>
          <p className="metric-value">
            {litres(model.summary.openingStorageLitres)}
          </p>
          <p className="caption">
            Opening pile used by the planner, including an estimated
            billed-waiting component. This is not a reconciled physical closing count.
          </p>
          <div className="meter">
            <span
              style={{
                width: `${percent(model.summary.openingStorageLitres, model.summary.storageLimitLitres)}%`,
              }}
            />
          </div>
          <p className="caption">
            Peak forecast: {litres(model.summary.peakStorageLitres)}. Bulk oil
            and packaging are outside this ceiling.
          </p>
        </section>
      </div>
      <section className="section">
        <div className="section-head">
          <div>
            <h2>Daily space forecast</h2>
            <p>Sunday production stops; physical dispatch can continue.</p>
          </div>
          <Tag tone="blue">Simulation</Tag>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th className="numeric">Opening pile</th>
                <th className="numeric">Made</th>
                <th className="numeric">Dispatched</th>
                <th className="numeric">Unbilled FG</th>
                <th className="numeric">Billed, waiting</th>
                <th className="numeric">Closing pile</th>
              </tr>
            </thead>
            <tbody>
              {model.days.map((d) => (
                <tr key={d.date}>
                  <td>
                    <strong>{date(d.date)}</strong>
                    {d.sunday && <small>Production closed</small>}
                  </td>
                  <td className="numeric">{litres(d.storage.openingLitres)}</td>
                  <td className="numeric">{litres(d.storage.madeLitres)}</td>
                  <td className="numeric">
                    {litres(d.storage.dispatchedLitres)}
                  </td>
                  <td className="numeric">
                    {litres(d.storage.unbilledLitres)}
                  </td>
                  <td className="numeric">
                    {litres(d.storage.billedWaitingLitres)}
                  </td>
                  <td className="numeric">
                    {litres(d.storage.closingLitres)}
                    {d.storage.overLimitLitres > 0 && (
                      <small>
                        Above limit by {litres(d.storage.overLimitLitres)}
                      </small>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
function Demand({ model }: { model: Mark4Model }) {
  const [query, setQuery] = useState("");
  const [gaps, setGaps] = useState(false);
  const rows = model.products.filter(
    (p) =>
      `${p.code} ${p.name}`.toLowerCase().includes(query.toLowerCase()) &&
      (!gaps || p.unmetPieces > 0),
  );
  return (
    <>
      <Title
        title="Prepare before the orders arrive."
        text="Confirmed orders receive priority. The forecast also prepares the factory for the late-month GT/MT rush."
      />
      <GrossDemand model={model} />
      <div className="section-head section">
        <h2>The production requirement</h2>
        <Tag tone="teal">Net planning quantities</Tag>
      </div>
      <div className="metrics-strip">
        <Metric
          label="Open-order demand to make"
          value={litres(model.summary.confirmedLitres)}
          note="Verified current-due order gap after finished-goods cover"
        />
        <Metric
          label="Forecast requirement"
          value={litres(model.summary.forecastLitres)}
          note="Expected demand beyond confirmed orders"
        />
        <Metric
          label="Required production"
          value={litres(model.summary.requiredLitres)}
          note="After the model’s stock and actuals treatment"
        />
        <Metric
          label="Excluded from scheduling"
          value={litres(model.summary.excludedLitres)}
          note="Visible, outside the current machine scope"
        />
      </div>
      {model.products.some((p) => p.allocatedOrderPieces > 0) && (
        <div className="notice section">
          <span>
            Some open e-commerce order quantities are allocated to SKUs using
            the current open-PO mix, not historical sales. Their product mapping
            and dates are inferred, not exact PO-line evidence. Each affected
            product shows the split below.
          </span>
          <a href="#rules" className="text-button">
            Order basis
          </a>
        </div>
      )}
      <div className="section">
        <div className="toolbar">
          <input
            className="search"
            aria-label="Search demand"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Find a product or item code"
          />
          <label className="check-field" style={{ marginTop: 0 }}>
            <input
              type="checkbox"
              checked={gaps}
              onChange={(e) => setGaps(e.target.checked)}
            />
            Only unscheduled demand
          </label>
          <p>
            Quantities are sales units (single packs or combos), not cartons.
          </p>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th className="numeric">Month target</th>
                <th className="numeric">Booked MTD</th>
                <th className="numeric">FG stock</th>
                <th className="numeric">Order gap</th>
                <th className="numeric">Forecast</th>
                <th className="numeric">Scheduled</th>
                <th className="numeric">Unmet</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.code}>
                  <td>
                    <strong>{shortProduct(p.name)}</strong>
                    <small>
                      {p.code} · {number(p.packLitres, 2)} L per sales unit ·{" "}
                      {p.container}
                      {p.containersPerPiece > 1 &&
                        ` · ${number(p.containersPerPiece)} × ${number(p.fillLitres, 2)} L containers`}
                      {p.cartonPieces
                        ? ` · ${number(p.cartonPieces)} per carton`
                        : ""}
                    </small>
                    {p.conditionalRecipe && (
                      <small>Conditional carton recipe; not approved</small>
                    )}
                    {p.transition && <small>{p.transition}</small>}
                    {p.exclusionReason && (
                      <small style={{ color: "var(--amber)" }}>
                        Not scheduled: {p.exclusionReason}
                      </small>
                    )}
                    {p.notes.map((n, i) => (
                      <small key={i}>{n}</small>
                    ))}
                  </td>
                  <td className="numeric">{number(p.monthlyPieces)}</td>
                  <td className="numeric">{number(p.bookedMtdPieces)}</td>
                  <td className="numeric">{number(p.fgPieces)}</td>
                  <td className="numeric">
                    {number(p.confirmedUncoveredPieces)}
                    <small>Exact orders: {number(p.exactOrderPieces)}</small>
                    {p.allocatedOrderPieces > 0 && (
                      <small>
                        Allocated: {number(p.allocatedOrderPieces)} (SKU/date
                        inferred)
                      </small>
                    )}
                  </td>
                  <td className="numeric">{number(p.forecastPieces)}</td>
                  <td className="numeric">{number(p.plannedPieces)}</td>
                  <td className="numeric">
                    {p.unmetPieces > 0 ? (
                      <Tag tone="amber">{number(p.unmetPieces)}</Tag>
                    ) : (
                      number(p.unmetPieces)
                    )}
                  </td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td colSpan={8}>
                    No products match. Try a shorter search or show all demand.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
function Actuals({ model }: { model: Mark4Model }) {
  return (
    <>
      <Title
        title="Keep the real days in view."
        text="Booked production and machine logs overlap. Their estimated product worth uses source prices; it is not billing. Never add the two records."
        extra={<Tag tone="blue">Factory observations</Tag>}
      />
      {!model.summary.historyComplete && (
        <div className="notice">
          <span>
            Month-to-date history is incomplete. Missing and partial days remain
            visible; they are not counted as zero.
          </span>
          <a className="text-button" href="#rules">
            Read the treatment
          </a>
        </div>
      )}
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th className="numeric">Booked production</th>
              <th className="numeric">Machine log</th>
              <th>Coverage</th>
              <th>What to know</th>
            </tr>
          </thead>
          <tbody>
            {model.actuals.map((d) => (
              <tr key={d.date}>
                <td>
                  <strong>
                    {date(d.date, {
                      day: "numeric",
                      month: "short",
                      weekday: "short",
                    })}
                  </strong>
                </td>
                <td className="numeric">
                  {litres(d.made_booked_l)}
                  <RecordedValue value={d.bookedValue} />
                </td>
                <td className="numeric">
                  {litres(d.made_mes_l)}
                  <RecordedValue value={d.mesValue} />
                </td>
                <td>
                  <Tag tone={d.complete ? "blue" : "amber"}>
                    {d.complete
                      ? d.settled === false
                        ? "Read, still settling"
                        : "Read"
                      : "Partial / not read"}
                  </Tag>
                </td>
                <td>
                  {d.notes?.join(" ") ||
                    (d.complete
                      ? "Source record available."
                      : "One or more source records are missing.")}
                </td>
              </tr>
            ))}
            {!model.actuals.length && (
              <tr>
                <td colSpan={5}>
                  Historical records have not been read. Refresh source data to
                  populate completed days.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <section className="section">
        <div className="section-head">
          <div>
            <h2>Latest machine observations</h2>
            <p>
              Recorded products, separate from the planner’s recommendations.
            </p>
          </div>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Machine</th>
                <th>Product</th>
                <th className="numeric">Recorded litres</th>
                <th>Status</th>
                <th>Source read at</th>
              </tr>
            </thead>
            <tbody>
              {model.lines.flatMap((l) =>
                l.actual.length
                  ? l.actual.map((a, i) => (
                      <tr key={`${l.id}-${i}`}>
                        <td>{l.name}</td>
                        <td>
                          {a.product}
                          <small>{a.note}</small>
                        </td>
                        <td className="numeric">{litres(a.litres)}</td>
                        <td>{a.status}</td>
                        <td>{time(a.asOf)}</td>
                      </tr>
                    ))
                  : [
                      <tr key={l.id}>
                        <td>{l.name}</td>
                        <td colSpan={4}>Not read for this line.</td>
                      </tr>,
                    ],
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
function Rules({ model }: { model: Mark4Model }) {
  const [query, setQuery] = useState("");
  const rows = model.rules.filter((r) =>
    `${r.title} ${r.detail} ${r.source} ${r.status}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <>
      <Title
        title="Everything this plan believes."
        text="Machine facts, provisional choices and unanswered questions are part of the plan. Review them before treating a recommendation as a commitment."
      />
      <div className="toolbar">
        <input
          className="search"
          aria-label="Search rules"
          placeholder="Find a rule, source or assumption"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <p>{number(rows.length)} rules shown</p>
        <button className="subtle-button" onClick={() => window.print()}>
          Print this page
        </button>
      </div>
      <div className="rulebook-grid">
        {rows.map((r) => (
          <article className="rule-card" key={r.id}>
            <header>
              <h3>{r.title}</h3>
              <Tag
                tone={
                  r.status === "confirmed"
                    ? "teal"
                    : r.status === "unavailable"
                      ? "red"
                      : "amber"
                }
              >
                {r.status === "confirmed"
                  ? "Confirmed"
                  : r.status === "assumption"
                    ? "Assumed"
                    : r.status === "provisional"
                      ? "Provisional"
                      : "Not available"}
              </Tag>
            </header>
            <p>{r.detail}</p>
            <p className="source-text">Source: {r.source}</p>
          </article>
        ))}
      </div>
      {!rows.length && <Empty>No rules match this search.</Empty>}
      <section className="section">
        <div className="section-head">
          <div>
            <h2>The exact speeds in use</h2>
            <p>
              Your approved final speeds, declared 6 September 2026, in physical
              containers/hour. Used directly. Combo runs divide by containers per
              sales unit. Factory readings remain separate evidence.
            </p>
          </div>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Machine / pack</th>
                <th className="numeric">Planning containers/h</th>
                <th>Status</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {model.planningSpeeds.map((r) => (
                <tr key={`${r.line}-${r.pack}`}>
                  <td><strong>{r.machine}</strong><small>{r.pack}</small></td>
                  <td className="numeric">{r.containersPerHour === null ? "—" : number(r.containersPerHour)}</td>
                  <td>{r.status}</td>
                  <td>{r.source}<small>Declared {date(r.asOf)}</small></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="section panel">
        <div className="panel-head">
          <h2>Questions for Gurvinder veerji</h2>
          <Tag tone="amber">Needs confirmation</Tag>
        </div>
        {model.questions.map((q) => (
          <article className="question-row" key={q.id}>
            <h3>{q.question}</h3>
            <p>{q.impact}</p>
          </article>
        ))}
        {!model.questions.length && (
          <Empty>No outstanding question was returned by the model.</Empty>
        )}
      </section>
      <section className="section panel">
        <div className="panel-head">
          <h2>Where the inputs came from</h2>
        </div>
        {model.sources.map((s) => (
          <div className="source-row" key={s.id}>
            <div>
              <strong>{s.label}</strong>
              <small>{s.note}</small>
            </div>
            <div>
              <Tag tone={s.ok ? "blue" : "amber"}>
                {s.ok ? "Read" : "Not current / not read"}
              </Tag>
              <small>{time(s.asOf)} IST</small>
            </div>
          </div>
        ))}
        {model.meta.assumptions.map((a, i) => (
          <p key={i} className="caption">
            {a}
          </p>
        ))}
      </section>
    </>
  );
}
function RunDrawer({
  run,
  dateString,
  close,
  model,
}: {
  run: Run;
  dateString: string;
  close: () => void;
  model: Mark4Model;
}) {
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    panel.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      if (e.key === "Tab") {
        const elements = panel.current?.querySelectorAll<HTMLElement>(
          'button,a,input,select,[tabindex="0"]',
        );
        if (!elements?.length) return;
        const first = elements[0],
          last = elements[elements.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [close]);
  return (
    <div
      className="detail-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div
        className="detail-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="run-title"
        ref={panel}
      >
        <button className="subtle-button drawer-close" onClick={close}>
          Close
        </button>
        <Tag tone="blue">Simulated · {date(dateString)}</Tag>
        <h2 id="run-title" style={{ marginTop: 17 }}>
          {shortProduct(run.product)}
        </h2>
        <p className="caption">
          {model.lines.find((l) => l.id === run.line)?.name || run.line} ·{" "}
          {run.code}
        </p>
        {run.startsAt && <p className="caption">Planned start {new Date(run.startsAt).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST{run.endsAt ? ` · end ${new Date(run.endsAt).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST` : ""}. Shift clock is provisional.</p>}
        {run.conditionalSupply && <div className="notice" style={{ marginTop: 20 }}>This run depends on estimated material availability: {run.conditionalSupplyMaterials?.join(", ")}. Check the delivery and QC window in Materials before committing the shift.</div>}
        {run.conditionalRecipe && (
          <div className="notice" style={{ marginTop: 20 }}>
            This run depends on an unconfirmed carton substitution. Confirm the
            replacement recipe before production.
          </div>
        )}
        <section className="panel">
          <div className="panel-head">
            <h3>Why this run</h3>
          </div>
          <p style={{ fontSize: 13 }}>{run.reason}</p>
          <div className="detail-item" style={{ marginTop: 17 }}>
            <strong>Production</strong>
            <span>
              {litres(run.litres)} / {number(run.pieces)} pieces
            </span>
          </div>
          <div className="detail-item">
            <strong>Value</strong>
            <span>{money(run.value)}</span>
          </div>
          <div className="detail-item">
            <strong>Working time</strong>
            <span>
              {formatDuration(run.dayHours)} day + {formatDuration(run.nightHours)} night
            </span>
          </div>
          <div className="detail-item">
            <strong>Changeover time</strong>
            <span>{formatSetupDuration(run)}</span>
          </div>
          <div className="detail-item">
            <strong>Total line time</strong>
            <span>
              {formatDuration(run.hours + run.setupHours)}
              {run.setupHours === 0 && run.reason.includes("opening setup is unknown")
                ? " + unknown opening setup"
                : " including setup"}
            </span>
          </div>
          <div className="detail-item">
            <strong>Orders / forecast</strong>
            <span>
              {number(run.confirmedPieces)} / {number(run.forecastPieces)}{" "}
              pieces
            </span>
          </div>
          <div className="detail-item">
            <strong>Order evidence in this run</strong>
            <span>
              {number(run.exactOrderPieces)} exact SKU pieces
              <br />
              {number(run.allocatedOrderPieces)} allocated pieces
              {run.allocatedOrderPieces > 0 && (
                <small>SKU / date inferred by source</small>
              )}
            </span>
          </div>
          <div className="detail-item">
            <strong>Labour cost</strong>
            <span>
              {run.labourCost == null ? "Not read" : money(run.labourCost)}
            </span>
          </div>
        </section>
        <section className="panel">
          <div className="panel-head">
            <h3>Speed basis</h3>
            <Tag tone={run.rate.basis === "derived" ? "amber" : "blue"}>
              {run.rate.basis}
            </Tag>
          </div>
          <p>
            {number(run.rate.piecesPerHour)} declared containers/h
            {(model.products.find((p) => p.code === run.code)
              ?.containersPerPiece ?? 1) > 1 && (
              <>
                {" "}
                ÷{" "}
                {number(
                  model.products.find((p) => p.code === run.code)
                    ?.containersPerPiece,
                )}{" "}
                containers per sales unit
              </>
            )}{" "}
            ={" "}
            <strong>
              {number(run.rate.effectivePiecesPerHour)} sales units/h
            </strong>
          </p>
          <p className="caption">{run.rate.source}</p>
        </section>
        <section className="panel">
          <div className="panel-head">
            <h3>Machine alternatives</h3>
          </div>
          {model.lines.map((line) => {
            const product = model.products.find((p) => p.code === run.code);
            const eligibility = product?.eligibility[line.id];
            if (!eligibility) return null;
            const other = model.days
              .find((d) => d.date === dateString)
              ?.runs.find((r) => r.line === line.id && r.code !== run.code);
            return (
              <div className="detail-item" key={line.id}>
                <div>
                  <strong>{line.name}</strong>
                  <p>{eligibility.reason}</p>
                  {other && (
                    <p>Assigned this day: {shortProduct(other.product)}.</p>
                  )}
                </div>
                <Tag
                  tone={
                    line.id === run.line
                      ? "teal"
                      : eligibility.allowed
                        ? "blue"
                        : ""
                  }
                >
                  {line.id === run.line
                    ? "Chosen"
                    : eligibility.allowed
                      ? "Eligible"
                      : "Excluded"}
                </Tag>
              </div>
            );
          })}
        </section>
        <section className="panel">
          <div className="panel-head">
            <h3>Materials this run consumes</h3>
          </div>
          {run.materials.map((m, i) => (
            <div className="detail-item" key={`${m.code}-${i}`}>
              <div>
                <strong>
                  {model.materials.find((x) => x.code === m.code)?.name ||
                    m.code}
                </strong>
                <p>{m.code}</p>
              </div>
              <span>
                {number(m.quantity, 1)} {m.unit}
              </span>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}

function RecordedValue({
  value,
  compact = false,
}: {
  value?: import("@/lib/types").ActualValue;
  compact?: boolean;
}) {
  if (
    !value ||
    value.coverage === "unavailable" ||
    (value.valuedLitres === 0 && value.unvaluedLitres > 0)
  )
    return <div className="record-value">Value not available</div>;
  return (
    <div
      className="record-value"
      title={`${value.basis}. Price source read ${time(value.asOf)} IST.`}
    >
      {money(value.value ?? value.knownValue)}{" "}
      {value.value === null ? "priced subtotal" : "estimated worth"}
      {value.unvaluedLitres > 0 && (
        <small>{litres(value.unvaluedLitres)} unpriced</small>
      )}
      {!compact && (
        <small className="record-coverage">
          {value.basis}
          <br />
          Price source {time(value.asOf)} IST
        </small>
      )}
    </div>
  );
}
function RecordedLabour({ line }: { line: import("@/lib/types").Line }) {
  const labour = line.recordedLabour;
  if (!labour)
    return (
      <div className="recorded-labour">
        <h3>Recorded labour</h3>
        <p>No run-level labour record was returned.</p>
      </div>
    );
  return (
    <section className="recorded-labour">
      <h3>Labour recorded by the factory</h3>
      <strong className="labour-amount">
        {labour.totalCost === null ? "Cost not read" : money(labour.totalCost)}
      </strong>
      <p>
        {date(labour.windowFrom)} — {date(labour.windowTo)} ·{" "}
        {number(labour.runCount)} recorded runs
      </p>
      <p>
        {labour.costPerLitre === null
          ? "Cost per litre unavailable"
          : `₹${number(labour.costPerLitre, 2)} per litre across matched cost/output runs`}
      </p>
      <p>
        {number(labour.costCoveredRunCount)} runs have cost;{" "}
        {number(labour.missingCostRunCount)} have no cost record.
      </p>
      <p className="source-text">
        {labour.basis} Source read {time(labour.asOf)} IST. This is recorded
        cost, not a future shift quotation.
      </p>
      {labour.runs.length > 0 && (
        <details>
          <summary className="text-button">See recorded runs</summary>
          <div className="table-wrap">
            <table className="data-table" style={{ minWidth: 0 }}>
              <thead>
                <tr>
                  <th>Date / product</th>
                  <th className="numeric">Output</th>
                  <th className="numeric">Labour</th>
                </tr>
              </thead>
              <tbody>
                {labour.runs.map((r, i) => (
                  <tr key={r.id || `${r.date}-${r.code}-${i}`}>
                    <td>
                      {date(r.date)}
                      <small>{r.code}</small>
                    </td>
                    <td className="numeric">{litres(r.litres)}</td>
                    <td className="numeric">
                      {r.labourCost === null ? "Not read" : money(r.labourCost)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </section>
  );
}
function GrossDemand({ model }: { model: Mark4Model }) {
  const book = model.demandBook;
  const bridge = model.planningBridge;
  const unknownTrade = book?.trade.unknownActiveOrderCount || 0;
  if (!book || !bridge)
    return (
      <div className="notice">
        The full open-order book has not been read. Net planning quantities
        below do not represent gross open POs.
      </div>
    );
  return (
    <>
      <div className="section-head">
        <div>
          <h2>The full open-order book</h2>
          <p>
            All eligible, unexpired open POs, including those created in earlier
            months. These are gross orders before FG cover.
          </p>
        </div>
        <Tag tone={book.coverage === "complete" ? "blue" : "amber"}>
          {book.coverage === "complete"
            ? "Source book read"
            : book.coverage === "partial"
              ? "Partial book"
              : "Not read"}
        </Tag>
      </div>
      <div className="book-grid">
        <section className="book-panel">
          <header>
            <h2>Online & quick commerce</h2>
            <Tag tone="blue">
              {book.online.openPoCount === null
                ? "PO count not read"
                : `${number(book.online.openPoCount)} open POs`}
            </Tag>
          </header>
          <div className="book-figures">
            <strong>{litres(book.online.grossOpenLitres)}</strong>
            <span>
              {book.online.openValueExGst === null
                ? "Order value not read"
                : `${money(book.online.openValueExGst)} excl. GST`}
            </span>
          </div>
          <div className="book-split">
            <div>
              <span>Quick commerce</span>
              <strong>{litres(book.online.quickCommerceLitres)}</strong>
            </div>
            <div>
              <span>Amazon</span>
              <strong>{litres(book.online.amazonLitres)}</strong>
            </div>
            <div>
              <span>Created before this month, still open</span>
              <strong>{litres(book.online.priorMonthOpenLitres)}</strong>
            </div>
            <div>
              <span>Expired and excluded</span>
              <strong>{litres(book.online.expiredExcludedLitres)}</strong>
            </div>
            <div>
              <span>Due this month</span>
              <strong>{litres(book.online.dueThisMonthLitres)}</strong>
            </div>
            <div>
              <span>Due later</span>
              <strong>{litres(book.online.laterDueLitres)}</strong>
            </div>
            <div>
              <span>Overdue, still eligible</span>
              <strong>{litres(book.online.overdueLitres)}</strong>
            </div>
            <div>
              <span>Due date missing</span>
              <strong>{litres(book.online.undatedLitres)}</strong>
            </div>
          </div>
          <p className="caption">
            Orders created earlier can still be due this month. Older-created
            and overdue quantities are subsets of the book, not extra orders to
            add.
          </p>
          {(book.online.outsideOilScopeLitres ?? 0) > 0 && (
            <div className="notice" style={{ marginTop: 16 }}>
              <span>
                <strong>Source book includes non-Oil items.</strong>{" "}
                {number(book.online.outsideOilScopeLitres, 2)} L is explicitly
                outside the Oil factory scope.{" "}
                {number(book.online.outsideOilScopeAcceptedLitres, 2)} L of
                accepted demand is outside scope. These stay visible in the
                source-book comparison and are excluded from the Oil planning
                requirement.
              </span>
            </div>
          )}
          <details>
            <summary className="text-button">Platform breakdown</summary>
            {book.online.byPlatform.map((p) => (
              <div className="detail-item" key={p.platform}>
                <strong>{p.platform}</strong>
                <span>
                  {litres(p.litres)}
                  <small>{number(p.poCount)} POs</small>
                </span>
              </div>
            ))}
          </details>
        </section>
        <section className="book-panel">
          <header>
            <h2>
              {unknownTrade > 0 ? "Quantified GT / MT trade" : "GT / MT trade"}
            </h2>
            <Tag tone={book.trade.scopeVerified ? "blue" : "amber"}>
              {book.trade.openOrderCount === null
                ? "Count not read"
                : `${number(book.trade.openOrderCount)} open orders`}
            </Tag>
          </header>
          <div className="book-figures">
            <strong>
              {unknownTrade > 0 && !book.trade.grossOpenLitres
                ? "Unquantified"
                : litres(book.trade.grossOpenLitres)}
            </strong>
            <span>
              {book.trade.openValueExGst === null
                ? "Order value not read"
                : `${money(book.trade.openValueExGst)} excl. GST`}
            </span>
          </div>
          {unknownTrade > 0 && (
            <div className="notice" style={{ marginTop: 19 }}>
              <span>
                <strong>Trade coverage is partial.</strong>{" "}
                {number(unknownTrade)} active OMS orders could not return
                company, items or litres. Their quantities are unknown, not
                zero; the amount above is only the quantified portion.
              </span>
            </div>
          )}
          <div className="book-split">
            <div>
              <span>Company scope</span>
              <strong>{book.trade.companyScope || "Not verified"}</strong>
            </div>
            <div>
              <span>Scope verification</span>
              <strong>
                {book.trade.scopeVerified
                  ? "Verified by source"
                  : "Still needs confirmation"}
              </strong>
            </div>
          </div>
          {(book.trade.unknownActiveOrders?.length || 0) > 0 && (
            <details>
              <summary className="text-button">
                Unquantified active OMS orders
              </summary>
              {book.trade.unknownActiveOrders!.map((order, index) => (
                <div className="detail-item" key={order.id}>
                  <div>
                    <strong title={`Source reference: ${order.id}`}>
                      Unread order {index + 1}
                    </strong>
                    <p>
                      Created {date(order.createdAt)} · {order.status}
                    </p>
                  </div>
                  <span>
                    Company unknown
                    <br />
                    Litres not available
                  </span>
                </div>
              ))}
              <p className="caption">
                Header source read {time(book.trade.headerAsOf)} IST.
              </p>
            </details>
          )}
          <div className="book-split">
            <div>
              <span>Due this month</span>
              <strong>{litres(book.trade.dueThisMonthLitres)}</strong>
            </div>
            <div>
              <span>Due later</span>
              <strong>{litres(book.trade.laterDueLitres)}</strong>
            </div>
            <div>
              <span>Overdue in quantified source</span>
              <strong>{litres(book.trade.overdueLitres)}</strong>
            </div>
            <div>
              <span>Due date missing</span>
              <strong>{litres(book.trade.undatedLitres)}</strong>
            </div>
          </div>
          <p className="caption">
            The monthly projection also prepares goods ahead of the late-month
            trade-order rush. Forecast reserve is separate from this open-order
            book.
          </p>
        </section>
      </div>
      <section className="bridge-panel">
        <div className="section-head">
          <div>
            <h2>From open orders to goods to make</h2>
            <p>
              Gross book totals and machine workload answer different questions.
            </p>
          </div>
        </div>
        <div className="bridge-steps">
          <div className="bridge-step">
            <span>
              {bridge.grossDueLitres === null
                ? "Known due quantity"
                : "Gross due in this horizon"}
            </span>
            <strong>
              {litres(bridge.grossDueLitres ?? bridge.knownGrossDueLitres)}
            </strong>
            <small>
              {bridge.grossDueLitres === null
                ? "Subtotal only; full gross due is unknown"
                : "Current due-date scope"}
            </small>
          </div>
          <div className="bridge-step">
            <span>Mapped to planner products</span>
            <strong>{litres(bridge.mappedLitres)}</strong>
            <small>{litres(bridge.unmappedLitres)} not mapped</small>
          </div>
          <div className="bridge-step">
            <span>Covered by finished goods</span>
            <strong>{litres(bridge.stockCoveredLitres)}</strong>
            <small>Stock offsets order requirement</small>
          </div>
          <div className="bridge-step">
            <span>Net order production needed</span>
            <strong>{litres(bridge.netMakeLitres)}</strong>
            <small>
              {litres(bridge.unschedulableLitres)} outside supported scheduling
            </small>
          </div>
        </div>
        {bridge.unknownActiveOrderCount > 0 && (
          <p className="caption">
            Full gross due cannot be stated:{" "}
            {number(bridge.unknownActiveOrderCount)} active OMS orders are
            unquantified. They have not been treated as zero.
          </p>
        )}
        {(bridge.outsideOilScopeLitres ?? 0) > 0 && (
          <p className="caption">
            {number(bridge.outsideOilScopeLitres, 2)} L is explicitly outside
            Oil scope and kept separate from unmapped products.
          </p>
        )}
        <p className="caption">
          Monthly forecast reserve adds {litres(bridge.projectionReserveLitres)}{" "}
          beyond the open-order requirement.
        </p>
        {bridge.explicitUnacceptedLitres !== null &&
          bridge.explicitUnacceptedLitres > 0 && (
            <p className="caption">
              Amazon requested-versus-accepted difference:{" "}
              {litres(bridge.explicitUnacceptedLitres)}. This is separate from
              unmapped SKU quantities.
            </p>
          )}
        {(bridge.quarantinedOrders?.length || 0) > 0 && (
          <div className="notice" style={{ marginTop: 18 }}>
            <span>
              <strong>Some demand needs a safe product match.</strong>{" "}
              {number(bridge.quarantinedOrders.length)} source lines are held
              because product identity, scope or units do not reconcile. They
              remain visible in the source book; the planner has not silently
              deleted the demand or made a different product.
            </span>
          </div>
        )}
        {(bridge.quarantinedOrders?.length || 0) > 0 && (
          <details>
            <summary className="text-button">Review held source lines</summary>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Source product</th>
                    <th className="numeric">Source litres</th>
                    <th>Why it is held</th>
                  </tr>
                </thead>
                <tbody>
                  {bridge.quarantinedOrders.map((order, index) => (
                    <tr key={`${order.id}-${index}`}>
                      <td>
                        <strong>
                          {order.sourceProductName ||
                            order.code ||
                            "Unidentified source product"}
                        </strong>
                        <small>{order.code || "Product code not read"}</small>
                      </td>
                      <td className="numeric">{litres(order.litres)}</td>
                      <td>{order.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="caption">
              These explain held source lines; they are not extra demand to add
              to the gross book.
            </p>
          </details>
        )}
        <details>
          <summary className="text-button">How these figures reconcile</summary>
          {bridge.notes.map((n, i) => (
            <p className="caption" key={i}>
              {n}
            </p>
          ))}
        </details>
      </section>
      <div className="caption">
        Open-book source read {time(book.asOf)} IST.
      </div>
      <details>
        <summary className="text-button">Source reconciliation details</summary>
        <p className="caption">{book.online.dateBasis}</p>
        {book.reconciliationNotes.map((n, i) => (
          <p className="caption" key={i}>
            {n}
          </p>
        ))}
      </details>
    </>
  );
}
function InboundLedger({
  model,
  busy,
  onScenario,
}: {
  model: Mark4Model;
  busy: boolean;
  onScenario: (scenario: Scenario) => Promise<void>;
}) {
  const events = model.inboundEvents || [];
  const appliedDates = JSON.stringify(model.scenario.arrivalDates || {});
  const [dateDraft, setDateDraft] = useState<Record<string, string>>(
    model.scenario.arrivalDates || {},
  );
  const [dateError, setDateError] = useState<string | null>(null);
  useEffect(() => {
    setDateDraft(JSON.parse(appliedDates));
    setDateError(null);
  }, [appliedDates]);
  const datesChanged = JSON.stringify(dateDraft) !== appliedDates;
  const setArrival = (id: string, value: string) => {
    if (value && !dateDraft[id] && Object.keys(dateDraft).length >= 20) {
      setDateError(
        "At most 20 arrival dates can be tested at once. Clear an existing date first.",
      );
      return;
    }
    const next = { ...dateDraft };
    if (value) next[id] = value;
    else delete next[id];
    setDateDraft(next);
    setDateError(null);
  };
  const sourceNames = {
    factory_po: "Factory purchase order",
    exim_transit: "EXIM transit",
    qc: "Factory QC",
    legacy: "Legacy schedule",
  };
  const dateNames = {
    supplier_due: "Supplier due date",
    transit_eta: "Transit ETA",
    observed_lead: "Estimated from observed lead",
    unverified: "Unverified date",
  };
  return (
    <form
      className="section"
      onSubmit={(event) => {
        event.preventDefault();
        if (!dateError)
          void onScenario({ ...model.scenario, arrivalDates: dateDraft });
      }}
    >
      <div className="incoming-head">
        <h2>What is actually on order or in transit</h2>
        <p>
          Source order and receipt events, separate from purchases the planner
          merely proposes. A PO does not guarantee usable stock. Enter an
          arrival assumption to test a date; this works independently of
          proposed purchases.
        </p>
      </div>
      {events.length ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Material / source</th>
                <th className="numeric">Source quantity</th>
                <th>Ordered</th>
                <th>Expected arrival</th>
                <th>Status</th>
                <th>Used by this scenario</th>
                <th>Your assumed arrival</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>
                    <strong>
                      {model.materials.find((m) => m.code === e.code)?.name ||
                        e.code}
                    </strong>
                    <small>
                      {e.code} · {sourceNames[e.source]}
                    </small>
                    <small>{e.linkedOrderId || e.id}</small>
                    <small>Source read {time(e.asOf)} IST</small>
                  </td>
                  <td className="numeric">
                    {number(e.quantity)} {e.unit}
                  </td>
                  <td>
                    {e.orderedAt
                      ? date(e.orderedAt, {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })
                      : "Not supplied"}
                  </td>
                  <td>
                    <strong>
                      {e.expectedAt
                        ? date(e.expectedAt)
                        : "No arrival date supplied"}
                    </strong>
                    <small>{dateNames[e.dateBasis]}</small>
                    <Tag tone={e.confidence === "confirmed" ? "blue" : "amber"}>
                      {e.confidence}
                    </Tag>
                  </td>
                  <td>
                    {e.status.replaceAll("_", " ")}
                    <small>
                      {e.stockIncluded === true
                        ? "Already in opening stock"
                        : e.stockIncluded === false
                          ? "Not in opening stock"
                          : "Stock inclusion not reconciled"}
                    </small>
                  </td>
                  <td>
                    <Tag
                      tone={
                        e.included ? (e.conditional ? "amber" : "teal") : ""
                      }
                    >
                      {e.included
                        ? e.conditional
                          ? "Conditional addition"
                          : "Included"
                        : "Not added"}
                    </Tag>
                    {e.appliedAt && <small>Applied {date(e.appliedAt)}</small>}
                    <small>{e.reason}</small>
                    {e.note && <small>{e.note}</small>}
                  </td>
                  <td>
                    {e.quantity > 0 &&
                    e.stockIncluded === false &&
                    ["open", "in_transit", "qc"].includes(e.status) ? (
                      <>
                        <input
                          className="arrival-input"
                          aria-label={`Assumed arrival for ${e.code} ${e.id}`}
                          type="date"
                          min={model.meta.startDate}
                          max={model.meta.endDate}
                          value={dateDraft[e.id] || ""}
                          onChange={(event) =>
                            setArrival(e.id, event.target.value)
                          }
                          disabled={
                            busy ||
                            (!dateDraft[e.id] &&
                              Object.keys(dateDraft).length >= 20)
                          }
                        />
                        {dateDraft[e.id] && (
                          <button
                            type="button"
                            className="text-button"
                            onClick={() => setArrival(e.id, "")}
                          >
                            Clear assumption
                          </button>
                        )}
                        <small>
                          {dateDraft[e.id]
                            ? "Your what-if date; not confirmed by supplier"
                            : "No date assumption entered"}
                        </small>
                      </>
                    ) : (
                      <small>
                        Not available: this event cannot add unreconciled or
                        already-received stock.
                      </small>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="notice">
          No evidenced inbound order or transit ledger has been read. Purchases
          proposed below are not placed orders.
        </div>
      )}
      {events.length > 0 && (
        <div className="arrival-actions">
          <div>
            <strong>
              {Object.keys(dateDraft).length} of 20 assumed arrival dates
            </strong>
            {Object.keys(dateDraft).length > 0 && (
              <button
                type="button"
                className="text-button"
                onClick={() => {
                  setDateDraft({});
                  setDateError(null);
                }}
              >
                Clear all assumed dates
              </button>
            )}
            <p>
              {datesChanged
                ? "Date changes are not applied yet."
                : "Showing the applied arrival assumptions."}{" "}
              These dates are your what-if inputs, not supplier promises.
              Clearing a date restores the source timing.
            </p>
          </div>
          <button
            className="primary-button"
            type="submit"
            disabled={busy || !!dateError}
          >
            {busy ? "Recalculating…" : "Apply arrival dates & recalculate"}
          </button>
        </div>
      )}
      {dateError && (
        <div className="notice error" role="alert">
          {dateError}
        </div>
      )}
    </form>
  );
}
function IdleReason({ model, day }: { model: Mark4Model; day: Day }) {
  if (day.sunday || day.productionLitres > 0) return null;
  const missing = [
    ...new Map(
      day.blockers
        .filter((b) => b.materialCode)
        .map((b) => [b.materialCode, b]),
    ).values(),
  ];
  return (
    <section className="idle-explanation">
      <h3>Why no production is scheduled on {date(day.date)}</h3>
      {missing.length ? (
        missing.slice(0, 4).map((b) => {
          const events = (model.inboundEvents || []).filter(
            (e) =>
              e.code === b.materialCode &&
              e.status !== "cancelled" &&
              e.status !== "received",
          );
          const arrivalFor = (event: (typeof events)[number]) =>
            model.scenario.arrivalDates?.[event.id] ||
            event.appliedAt ||
            event.expectedAt;
          const next = events
            .filter(
              (event) =>
                arrivalFor(event) &&
                arrivalFor(event)!.slice(0, 10) >= day.date,
            )
            .sort((a, b) => arrivalFor(a)!.localeCompare(arrivalFor(b)!))[0];
          return (
            <p key={b.materialCode}>
              <strong>{b.materialName || b.materialCode}:</strong> {b.reason}{" "}
              {next
                ? `${model.scenario.arrivalDates?.[next.id] ? "Your assumed" : next.confidence === "confirmed" ? "Source" : "Unconfirmed"} arrival dated ${date(arrivalFor(next))}. ${next.included ? "This scenario includes it when available." : next.reason}`
                : events.length
                  ? "An open source order exists, but there is no later usable arrival date in the ledger."
                  : "No open arrival event for this material was read."}
            </p>
          );
        })
      ) : (
        <p>
          {day.blockers[0]?.reason ||
            "No remaining feasible demand was returned for this day."}
        </p>
      )}
      {missing.length > 4 && (
        <p>
          Additional materials are listed under the product constraints below.
        </p>
      )}
      <p>
        Changing the proposed-supply setting can test suggested purchases. It
        does not place an order or confirm a delivery.
      </p>
      <a href="#materials">Inspect incoming materials and purchase proposals</a>
    </section>
  );
}
