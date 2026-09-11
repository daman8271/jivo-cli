export function formatDuration(hours: number | null | undefined): string {
  if (hours == null || !Number.isFinite(hours) || hours < 0) return "Not read";
  if (hours === 0) return "0 h";
  const seconds = hours * 3600;
  if (seconds < 1) return "<1 s";
  const roundedSeconds = Math.round(seconds);
  if (roundedSeconds < 60) return `${roundedSeconds} s`;
  if (roundedSeconds < 3600) {
    const minutes = Math.floor(roundedSeconds / 60);
    const remainder = roundedSeconds % 60;
    return `${minutes} min${remainder ? ` ${remainder} s` : ""}`;
  }
  const roundedMinutes = Math.round(seconds / 60);
  const wholeHours = Math.floor(roundedMinutes / 60);
  const minutes = roundedMinutes % 60;
  return `${wholeHours} h${minutes ? ` ${minutes} min` : ""}`;
}

export function formatSetupDuration(run: {
  setupHours: number | null | undefined;
  reason: string;
}): string {
  return run.setupHours === 0 && run.reason.includes("opening setup is unknown")
    ? "Unknown · 0 h assumed"
    : formatDuration(run.setupHours);
}
