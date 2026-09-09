import type { Blocker, Day } from "@/lib/types";

const number = (value: number) => Math.round(value).toLocaleString("en-IN");

export default function SavedIdleReasons({ blockers, storage }: { blockers: Blocker[]; storage: Day["storage"] }) {
  const groups = new Map<string, Blocker[]>();
  for (const blocker of blockers) groups.set(blocker.reason, [...(groups.get(blocker.reason) ?? []), blocker]);
  return <div className="review-timing">
    <h4>Why no run was saved</h4>
    <p>These are the saved planner's reasons, not a report of why the factory stopped.</p>
    {!groups.size ? <p>No explanation was saved for this machine. The reason is unknown.</p> : <ul>{[...groups].map(([reason, rows]) => <li key={reason}>
      <p>{reason.startsWith("Physical godown space is full") ? "The saved plan had no room for these products after its other planned runs." : reason.startsWith("Eligible, but today's") ? "Other products were chosen first. The saved explanation does not identify the exact limiting constraint." : reason}</p>
      <details><summary>{rows.length === 1 ? rows[0].product : `${rows.length} affected products`} · saved evidence</summary>
        {rows.map(row => <p key={row.code}>{row.product}<br /><code>{row.code}</code>{row.missingQuantity != null && <small>Saved unmet material quantity: {number(row.missingQuantity)} {row.unit}</small>}</p>)}
        <p>Original explanation: {reason}</p>
      </details>
    </li>)}</ul>}
    {blockers.some(row => row.reason.startsWith("Physical godown space is full")) && <p>Saved closing storage: <strong>{number(storage.closingLitres)} L</strong> against a <strong>{number(storage.limitLitres)} L</strong> limit. This was a forecast, including {number(storage.dispatchedLitres)} L of assumed dispatch; it was not a physical stock check.</p>}
  </div>;
}
