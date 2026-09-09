"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { JobAccepted, JobSummary, PlanCommand, PlanRevision, PlansResponse, PlanningSnapshot } from "./planning-types";

export async function api<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(path, {
      method, cache: "no-store", credentials: "same-origin", signal: controller.signal,
      ...(body === undefined ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = typeof data?.error === "string" ? data.error : typeof data?.message === "string" ? data.message : `Request failed (${response.status}).`;
      throw new Error(response.status === 409 ? `The plan changed. Reload and review the latest revision before saving. ${detail}` : detail);
    }
    return data as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw new Error("The request took too long. Your last loaded plan is still shown. Try again.");
    throw error;
  } finally { clearTimeout(timeout); }
}

export function revisionKey() {
  return globalThis.crypto?.randomUUID?.() ?? `operator-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function useDashboard() {
  const [snapshot, setSnapshot] = useState<PlanningSnapshot | null>(null);
  const [plans, setPlans] = useState<Record<string, PlansResponse>>({});
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const watchedJobs = useRef(new Set<string>());
  const refreshInFlight = useRef(false);

  const reload = useCallback(async () => {
    if (refreshInFlight.current) return;
    refreshInFlight.current = true;
    try {
      const next = await api<PlanningSnapshot>("/api/dashboard");
      setSnapshot(next);
      setJobs(current => {
        const merged = new Map(current.map(job => [job.id, job]));
        for (const job of next.jobs ?? []) merged.set(job.id, job);
        return [...merged.values()].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
      });
      for (const job of next.jobs ?? []) if (["queued", "running"].includes(job.status)) watchedJobs.current.add(job.id);
      const dates = [...new Set([next.today.date, next.tomorrow.date])];
      const results = await Promise.allSettled(dates.map(date => api<PlansResponse>(`/api/plans/${date}`)));
      setPlans(current => {
        const updated = { ...current };
        results.forEach((result, index) => { if (result.status === "fulfilled") updated[dates[index]] = result.value; });
        return updated;
      });
      const failed = results.find(result => result.status === "rejected");
      setError(failed?.status === "rejected" ? `Saved plans could not be refreshed. ${String(failed.reason instanceof Error ? failed.reason.message : failed.reason)}` : null);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not load the factory board."); }
    finally { setLoading(false); refreshInFlight.current = false; }
  }, []);

  useEffect(() => {
    void reload();
    void api<{ authenticated: boolean }>("/api/session").then(s => setAuthenticated(s.authenticated)).catch(() => setAuthenticated(false));
    const interval = setInterval(() => { if (document.visibilityState === "visible") void reload(); }, 45000);
    return () => clearInterval(interval);
  }, [reload]);

  useEffect(() => {
    let stopped = false;
    let polling = false;
    const interval = setInterval(async () => {
      if (polling || !watchedJobs.current.size) return;
      polling = true;
      try {
        const ids = [...watchedJobs.current];
        const results = await Promise.allSettled(ids.map(id => api<JobSummary>(`/api/jobs/${encodeURIComponent(id)}`)));
        if (stopped) return;
        let completed = false;
        let jobError: string | null = results.some(result => result.status === "rejected") ? "Job status could not be refreshed. The last reported status is shown; checking continues automatically." : null;
        for (const result of results) {
          if (result.status !== "fulfilled") continue;
          const job = result.value;
          setJobs(current => [job, ...current.filter(j => j.id !== job.id)].sort((a, b) => b.createdAt.localeCompare(a.createdAt)));
          if (!["queued", "running"].includes(job.status)) {
            watchedJobs.current.delete(job.id);
            completed = true;
            if (job.status === "failed") jobError = job.error || "The job failed. Your saved agreement has not changed.";
            else if (job.status === "superseded") setNotice("A newer source or plan replaced this job. Review the latest proposal.");
            else setNotice(job.kind === "ai_review" ? "AI review finished. Review its proposal and activity before approving." : job.kind === "replan" ? "Draft saved. Review the resulting plan before approving." : "Factory refresh finished.");
          }
        }
        if (completed) await reload();
        if (jobError) setError(jobError);
      } finally { polling = false; }
    }, 2500);
    return () => { stopped = true; clearInterval(interval); };
  }, [reload]);

  const act = useCallback(async <T,>(action: () => Promise<T>): Promise<T | null> => {
    setBusy(true); setError(null); setNotice(null);
    try { return await action(); }
    catch (e) { setError(e instanceof Error ? e.message : "This action could not be completed."); return null; }
    finally { setBusy(false); }
  }, []);

  const startJob = useCallback(async (path: string, body: unknown) => act(async () => {
    const accepted = await api<JobAccepted>(path, "POST", body);
    watchedJobs.current.add(accepted.job.id);
    setJobs(current => [accepted.job, ...current.filter(j => j.id !== accepted.job.id)]);
    setNotice("Job started. You can keep reviewing the current board while it runs.");
    return accepted.job;
  }), [act]);

  const unlock = useCallback(async (passcode: string) => act(async () => {
    const result = await api<{ authenticated: boolean }>("/api/session", "POST", { passcode });
    setAuthenticated(result.authenticated);
    return result.authenticated;
  }), [act]);

  const lock = useCallback(async () => act(async () => {
    await api("/api/session", "DELETE"); setAuthenticated(false); return true;
  }), [act]);

  const approve = useCallback(async (revision: PlanRevision) => act(async () => {
    const result = await api<PlanRevision>(`/api/plans/${revision.date}/approve`, "POST", { expectedRevision: revision.revision, idempotencyKey: revisionKey() });
    setNotice(`Revision ${revision.revision} is now the agreed plan.`);
    await reload();
    return result;
  }), [act, reload]);

  return {
    snapshot, plans, jobs, authenticated, loading, busy, error, notice, reload, unlock, lock, approve,
    dismissNotice: () => setNotice(null),
    refresh: () => startJob("/api/refresh", {}),
    review: (date: string) => startJob("/api/ai/review", { date, idempotencyKey: revisionKey() }),
    revise: (command: PlanCommand) => startJob(`/api/plans/${command.date}/revise`, command),
  };
}
