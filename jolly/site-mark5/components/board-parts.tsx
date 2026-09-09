"use client";

import { useEffect, useRef } from "react";
import type { DayProposal, MachineId, PlanRevision, PlannedRun, PlansResponse, PlanningBlocker, ProductChoice } from "../lib/planning-types";

export const MACHINE_IDS: MachineId[] = ["JP Machine", "Clear Pack", "10 Head", "6 Head", "Tin Head", "Hitech", "Samarpan"];
export const number = (value: number, digits = 0) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: digits }).format(value);
export const tonnes = (litres: number | null | undefined) => litres == null ? "Unknown" : `${number(litres / 1000, 1)} T`;
export function dateLabel(value: string, long = false) {
  const date = new Date(value.length === 10 ? `${value}T12:00:00+05:30` : value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", weekday: long ? "long" : "short", day: "numeric", month: "short" }).format(date);
}
export function timeLabel(value: string | null | undefined) {
  if (!value) return "Time unknown";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Time unknown" : new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hour12: false }).format(date);
}
export function clockLabel(value: string | null | undefined) { return value ? `${dateLabel(value)}, ${timeLabel(value)} IST` : "Source time unknown"; }
export const hours = (minutes: number) => minutes >= 60 ? `${number(minutes / 60, 1)} h` : `${number(minutes)} min`;
export const latestRevision = (plans: PlansResponse | undefined, status?: PlanRevision["status"]) => plans?.revisions.filter(r => !status || r.status === status).sort((a, b) => b.revision - a.revision)[0];

export function Runs({ runs, compact = false }: { runs: PlannedRun[]; compact?: boolean }) {
  if (!runs.length) return <span className="empty-cell">No run planned</span>;
  return <div className="run-list">{runs.map(run => <div className={`run ${compact ? "run-compact" : ""}`} key={run.id}>
    <div className="run-name"><span className={`shift-label ${run.shift === "night" ? "shift-night" : ""}`}>{run.shift === "night" ? "Night" : "Day"}</span><strong>{run.product}</strong></div>
    <div className="run-numbers"><span>{tonnes(run.litres)}</span><span>{run.cases !== null ? `${number(run.cases, 1)} cases` : `${number(run.pieces)} pieces`}</span><span>{timeLabel(run.startsAt)}–{timeLabel(run.endsAt)}</span></div>
    {run.changeover.minutes !== null && run.changeover.minutes > 0 && <div className="setup-note">Setup {hours(run.changeover.minutes)} from {timeLabel(run.setupStartsAt)}{run.changeover.flushingLitres !== null ? ` · ${number(run.changeover.flushingLitres)} L flushing reused` : ""}</div>}
    {run.changeover.minutes === null && <div className="setup-note">Setup duration unknown</div>}
    {run.conditional && <span className="conditional">Conditional run</span>}
    {!compact && run.reason && <p className="run-reason">{run.reason}</p>}
  </div>)}</div>;
}

export function Objective({ proposal }: { proposal: DayProposal }) {
  const progress = proposal.targetLitres > 0 ? Math.min(100, proposal.totalLitres / proposal.targetLitres * 100) : 0;
  return <section className="objective" aria-label="Production objective">
    <div className="objective-main"><span className="muted">Planned output</span><strong>{tonnes(proposal.totalLitres)}</strong><span>Day {tonnes(proposal.dayLitres)} <span className="separator">/</span> Night {tonnes(proposal.nightLitres)}</span></div>
    <div className="objective-target"><div className="target-line"><span>Minimum {tonnes(proposal.targetLitres)}</span><span>Good day {tonnes(proposal.desirableRangeLitres[0])}–{tonnes(proposal.desirableRangeLitres[1])}</span></div><div className="progress-track" role="meter" aria-label="Planned share of minimum target" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}><span style={{ width: `${progress}%` }} /></div><div className={`target-result ${proposal.shortfallLitres > 0 ? "amber-text" : "green-text"}`}>{proposal.shortfallLitres > 0 ? `${tonnes(proposal.shortfallLitres)} below minimum` : "Minimum covered"}<span>Orders cover {tonnes(proposal.confirmedLitres)}</span></div></div>
    <p className="night-reason">{proposal.nightReason}</p>
  </section>;
}

const blockerLabels: Record<PlanningBlocker["kind"], string> = { material: "Materials", storage: "Warehouse space", route: "Machine suitability", setup: "Changeovers", demand: "Demand", source: "Source information" };

export function BlockerGroups({ blockers, products }: { blockers: PlanningBlocker[]; products: ProductChoice[] }) {
  const kinds = [...new Set(blockers.map(blocker => blocker.kind))];
  if (!blockers.length) return <p className="muted">No blockers were reported.</p>;
  return <div className="blocker-groups">{kinds.map(kind => {
    const rows = blockers.filter(blocker => blocker.kind === kind);
    const reasons = [...new Set(rows.map(row => row.reason))];
    const affected = new Set(rows.map(row => row.code).filter(Boolean));
    return <section key={kind} className="blocker-group"><header><h3>{blockerLabels[kind]}</h3><span>{affected.size ? `${affected.size} affected products` : `${rows.length} ${rows.length === 1 ? "hold" : "holds"}`}</span></header>{reasons.map(reason => {
      const matching = rows.filter(row => row.reason === reason);
      const codes = [...new Set(matching.map(row => row.code).filter((code): code is string => code !== null))];
      const machines = [...new Set(matching.map(row => row.machineId).filter(Boolean))];
      return <div className="grouped-reason" key={reason}><p>{reason}</p>{codes.length > 0 && <details><summary>{codes.length === 1 ? "Affected product" : `${codes.length} affected products`}{machines.length > 0 ? ` on ${machines.join(", ")}` : ""}</summary><ul>{codes.map(code => <li key={code}>{products.find(product => product.code === code)?.name ?? "Product name unavailable"}<small>{code}</small></li>)}</ul></details>}{!codes.length && machines.length > 0 && <small>{machines.join(", ")}</small>}</div>;
    })}</section>;
  })}</div>;
}

export function WarehouseAction({ proposal, onDetails }: { proposal: DayProposal; onDetails: () => void }) {
  const storage = proposal.storage;
  const binding = proposal.blockers.some(blocker => blocker.kind === "storage");
  if (!storage || !binding) return null;
  const headroom = Math.max(0, storage.limitLitres - storage.openingLitres);
  return <section className="warehouse-action" aria-label="Warehouse release needed">
    <div className="warehouse-heading"><h2>Warehouse release needed</h2><span>Conditional estimate</span></div>
    <p className="warehouse-lead">{storage.spaceNeededForMinimumLitres > 0 ? <>The model needs about <strong>{tonnes(storage.spaceNeededForMinimumLitres)}</strong> of space released to fit the minimum target.</> : "Warehouse space limits the additional work in this proposal."} Verify physical stock and planned dispatch before deciding the shifts.</p>
    <dl className="warehouse-figures"><div><dt>Modelled opening occupancy</dt><dd>{number(storage.openingLitres)} L</dd></div><div><dt>Space currently in the model</dt><dd>{number(headroom)} L</dd></div><div><dt>Estimated billed stock included</dt><dd>{number(storage.standingLitres)} L</dd></div></dl>
    <p className="warehouse-basis">Billed-stock basis: {storage.standingBasis.replace(/[.\s]+$/, "")}. This is an estimate of occupancy, not a physical warehouse count or a confirmed factory stop.</p>
    <button className="text-button" onClick={onDetails}>Review the space assumption and affected products</button>
  </section>;
}

export function Drawer({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    const trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialog?.showModal();
    return () => {
      if (dialog?.open) dialog.close();
      queueMicrotask(() => { if (trigger?.isConnected) trigger.focus({ preventScroll: true }); });
    };
  }, []);
  return <dialog ref={ref} className="drawer" aria-label={title} onCancel={onClose} onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
    <div className="drawer-content"><header className="drawer-header"><h2>{title}</h2><button className="icon-button" aria-label="Close details" onClick={onClose}>×</button></header>{children}</div>
  </dialog>;
}
