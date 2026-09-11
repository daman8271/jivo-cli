"use client";

import { useEffect, useState } from "react";
import type { JobSummary, MachineId, PlanCommand, PlanningChange, ProductChoice } from "../lib/planning-types";
import { revisionKey } from "../lib/use-dashboard";
import { MACHINE_IDS, number } from "./board-parts";

export default function PlanEditor({ date, revision, products, busy, jobs, onSave }: {
  date: string; revision: number | null; products: ProductChoice[]; busy: boolean; jobs: JobSummary[];
  onSave: (command: PlanCommand) => Promise<JobSummary | null>;
}) {
  const [machine, setMachine] = useState<MachineId>("JP Machine");
  const [code, setCode] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState<"cases" | "pieces">("pieces");
  const [shift, setShift] = useState<"day" | "night">("day");
  const [changes, setChanges] = useState<PlanningChange[]>([]);
  const [baseRevision, setBaseRevision] = useState<number | null>(revision);
  const [formError, setFormError] = useState<string | null>(null);
  const [pendingJob, setPendingJob] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const choices = products.filter(p => p.machines.includes(machine));
  const product = choices.find(p => p.code === code);
  const caseFactor = product?.piecesPerCase;
  const canCases = typeof caseFactor === "number" && Number.isFinite(caseFactor) && caseFactor > 0;
  const waitingJob = jobs.find(job => job.id === pendingJob);
  const saving = pendingJob !== null && (!waitingJob || ["queued", "running"].includes(waitingJob.status));
  const stale = changes.length > 0 && baseRevision !== revision;
  const nightChange = [...changes].reverse().find(change => change.type === "set_night_line");

  useEffect(() => {
    if (waitingJob?.status === "succeeded") { setChanges([]); setPendingJob(null); setSavedMessage("Draft saved. Review its output and then approve the exact revision."); }
    if (waitingJob && ["failed", "superseded"].includes(waitingJob.status)) { setPendingJob(null); setFormError(waitingJob.error || "This job was replaced. Your edits are kept here; review the current revision before saving again."); }
  }, [waitingJob]);
  useEffect(() => { if (!changes.length) setBaseRevision(revision); }, [revision, changes.length]);

  function add(change: PlanningChange) {
    if (!changes.length) setBaseRevision(revision);
    setSavedMessage(null); setFormError(null);
    setChanges(previous => {
      if (change.type === "set_run") return [...previous.filter(c => !(c.type === "set_run" && c.machineId === change.machineId && c.shift === change.shift)), change];
      if (change.type === "set_line_enabled") return [...previous.filter(c => !(c.type === "set_line_enabled" && c.machineId === change.machineId)), change];
      if (change.type === "set_night_line") return [...previous.filter(c => c.type !== "set_night_line"), change];
      return [...previous.filter(c => !(c.type === "prioritize_sku" && c.code === change.code)), change];
    });
  }
  function addRun() {
    const entered = Number(quantity);
    if (!product) { setFormError("Choose a product approved for this machine."); return; }
    if (!Number.isFinite(entered) || entered <= 0 || !Number.isInteger(entered)) { setFormError("Enter a positive whole number of cases or pieces."); return; }
    if (unit === "cases" && !canCases) { setFormError("The case factor is not verified. Use pieces."); return; }
    const pieces = entered * (unit === "cases" ? caseFactor! : 1);
    if (!Number.isSafeInteger(pieces)) { setFormError("This quantity cannot be represented as whole pieces."); return; }
    add({ type: "set_run", machineId: machine, code: product.code, pieces, shift });
  }
  function changeLabel(change: PlanningChange) {
    if (change.type === "set_run") return `${change.machineId} · ${change.shift} · ${products.find(p => p.code === change.code)?.name ?? change.code} · ${number(change.pieces)} pieces`;
    if (change.type === "prioritize_sku") return `Prioritize ${products.find(p => p.code === change.code)?.name ?? change.code}`;
    if (change.type === "set_line_enabled") return `${change.enabled ? "Enable" : "Disable"} ${change.machineId}`;
    return `Night: ${change.machineId ?? "off"}`;
  }
  return <aside className="plan-editor" aria-labelledby="edit-heading">
    <div className="editor-heading"><div><h2 id="edit-heading">Revise tomorrow</h2><p>Choose the work. Review what fits.</p></div><span className="revision-label">{revision === null ? "New draft" : `From r${revision}`}</span></div>
    <fieldset disabled={busy || saving} className="editor-fields">
      <label>Machine<select value={machine} onChange={event => { setMachine(event.target.value as MachineId); setCode(""); setUnit("pieces"); }}>{MACHINE_IDS.map(id => <option key={id}>{id}</option>)}</select></label>
      <label>Product<select value={code} onChange={event => { setCode(event.target.value); setUnit("pieces"); }}><option value="">Choose a compatible product</option>{choices.map(p => <option key={p.code} value={p.code}>{p.name} ({p.code})</option>)}</select></label>
      {!choices.length && <p className="field-help">No verified product routes are available for this machine.</p>}
      <div className="field-pair"><label>Quantity<input inputMode="numeric" type="number" min="1" step="1" value={quantity} onChange={event => setQuantity(event.target.value)} placeholder="Enter quantity" /></label><label>Unit<select value={unit} onChange={event => setUnit(event.target.value as "cases" | "pieces")}><option value="pieces">Pieces</option>{canCases && <option value="cases">Cases</option>}</select></label></div>
      {product && <p className="field-help">{canCases ? `Verified case: ${number(caseFactor!)} pieces.` : "Case factor unverified. Enter pieces."} {product.packLitres > 0 ? `${number(product.packLitres, 3)} L per sales piece.` : ""}</p>}
      <label>Session<select value={shift} onChange={event => setShift(event.target.value as "day" | "night")}><option value="day">Day</option><option value="night">Night</option></select></label>
      <button className="button secondary full-width" onClick={addRun}>Add run to revision</button>
      <div className="editor-secondary"><button className="text-button" disabled={!product} onClick={() => product && add({ type: "prioritize_sku", code: product.code })}>Prioritize this product</button><label className="small-label">Machine availability<select value="" onChange={event => { if (event.target.value) add({ type: "set_line_enabled", machineId: machine, enabled: event.target.value === "on" }); }}><option value="">Change availability…</option><option value="on">Enable {machine}</option><option value="off">Disable {machine}</option></select></label></div>
      <label>Night allocation<select value={nightChange?.type === "set_night_line" ? nightChange.machineId ?? "off" : ""} onChange={event => { if (event.target.value) add({ type: "set_night_line", machineId: event.target.value === "off" ? null : event.target.value as MachineId | "auto" }); }}><option value="">Keep current allocation</option><option value="auto">Choose automatically</option><option value="off">No night session</option>{MACHINE_IDS.map(id => <option key={id}>{id}</option>)}</select></label>
    </fieldset>
    {formError && <p className="inline-error" role="alert">{formError}</p>}
    {changes.length > 0 && <div className="pending-changes"><h3>{changes.length} unsaved {changes.length === 1 ? "change" : "changes"}</h3><ul>{changes.map((change, index) => <li key={index}><span>{changeLabel(change)}</span><button className="icon-button" aria-label={`Remove change ${index + 1}`} disabled={saving} onClick={() => setChanges(previous => previous.filter((_, i) => i !== index))}>×</button></li>)}</ul></div>}
    {stale && <div className="inline-error" role="alert">A newer revision is available. Review it before applying these changes.<button className="text-button" disabled={saving} onClick={() => setBaseRevision(revision)}>Use these changes on r{revision}</button></div>}
    <button className="button primary full-width" disabled={!changes.length || busy || saving || stale} onClick={async () => {
      const job = await onSave({ date, expectedRevision: baseRevision, idempotencyKey: revisionKey(), changes });
      if (job) { setPendingJob(job.id); setSavedMessage(null); }
    }}>{saving ? "Calculating draft…" : "Save revision draft"}</button>
    <p className="field-help">Saving recalculates a proposal. The agreed plan changes only after approval.</p>
    {savedMessage && <p className="green-text" role="status">{savedMessage}</p>}
  </aside>;
}
