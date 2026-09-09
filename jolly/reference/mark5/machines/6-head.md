# MARK V machine specification: 6 Head

Date: 10 September 2026. Status: approved operating inputs; specification only,
not an engine change. Confidence: high in the adopted figures and source mapping.
The remaining limits below concern interpretation and missing fields, not approval
of these numbers.

Authority: [WORKING-RULES.md](../WORKING-RULES.md), especially M5-R01 and M5-A01;
[PDF review](../PDF-REVIEW-2026-09-10.md). Current user instructions outrank the
PDF; revised notes/tables outrank its historical summary and transcript.

## Rates and operational routes

| Pack | Approved running rate | Route qualification |
|---|---:|---|
| 3 L | 13 containers/min = 780/hour | Main larger-pack work. |
| 4 L | 12 containers/min = 720/hour | Supported; used sometimes. |
| 5 L | 10 containers/min = 600/hour | Main larger-pack work. |
| 1 L | Unrated in the adopted evidence | Emergency use when another line has a problem; not a routine capacity pool. |
| 2 L | No settled working route or rate | Keep unresolved; the old planner entry does not settle it. |

Source: revised PDF pp2,12; supporting transcript pp45–47, 31:40–33:13 and
pp48–49, 35:23–35:58. The earlier 5 L rate of 9/min is superseded.

These are physical containers while running, not sales cases or verified accepted
output over an elapsed shift. Exact SKU, container, bottle/label and tooling
compatibility must remain attached to the product route. A pack-size row does not
approve every container family. Existing specifically supported printed 5 L tin
evidence should be reconciled separately, not erased or broadened by this table.

## Changeover: inherit the 10 Head description

Source: revised PDF pp3,13–14; explicit inheritance in original transcript
pp36–37, 20:42–21:31. This is approved reported inheritance, not a separate timed
measurement of 6 Head. Inheritance covers setup descriptions, not 10 Head rates,
pack routes, or labelling restrictions.

| Change classification | Adopted duration | Meaning |
|---|---|---|
| Parts only | About 30 minutes | Mechanical component. |
| Mustard, groundnut or extra virgin change entry | 1 hour or more | Parts and flushing combined; exact from/to pairs unspecified. |
| Cold press → sunflower | About 30 minutes | Specific revised entry; its reverse is not established. |

Do not add another 30-minute parts charge to the combined one-hour-plus entry.
Preserve its open upper bound; any finite scheduling value must be an explicit
planning choice. Do not map every transition involving a named oil to that entry
without a visible classification rule. The historical 45-minute cold-press to
sunflower suggestion does not override the revised 30 minutes. Unlisted pairs,
opening setup and same-product restart conditions remain unspecified here.

Flushing still occupies the line. Under M5-A01 assume reuse; do not deduct its
whole volume as recurring fresh-oil consumption or waste. No 6 Head flushing
quantity, recovery fraction or recovery timing is supplied. Do not copy Clear
Pack's 550/1,000 L or JP's 1,500 L onto this machine, create available stock, or
report unknown loss as measured zero.

## Manual labels and capacity limits

Manual labelling is part of the operating description. Revised wording is
“4 + labour people”; original pp36–37, 20:51–21:31 describes four people applying
labels continuously through the day. This is not the total line crew, measured
labelling throughput, a separate fixed batch delay, or proof of spare labour.
Later rework-worker references must not be added without checking overlap.

Use the adopted running rates without an invented labelling penalty or automatic
80% multiplier. Equally, rate × full shift is not established good output: breaks,
ordinary stops, rejects, label/packing throughput, crew availability and net session
time remain distinct inputs. The historical approximately 10 tonnes/day statement
(p15 summary) supplies neither an efficiency factor nor a replacement rate.

No independent night entitlement, full crew, minimum batch, active-head count,
QC-release delay or shared-resource capacity is established for 6 Head here.

## Required implementation checks

- Lookup returns 780/720/600 containers/hour for supported 3/4/5 L products,
  including the new 4 L route; it never returns the old 384/hour for 3 L.
- Emergency 1 L remains visible as unrated and cannot acquire the old 1,080/hour
  silently. Unsettled 2 L cannot acquire a working route or old 720/hour silently.
- 10 Head setup inheritance leaves 6 Head pack eligibility and rates independent.
- A classified combined change incurs one combined interval, not that interval
  plus 30 minutes. Open bounds and missing pair mappings remain visible.
- Cold press → sunflower uses the revised about-30-minute entry; reversing the
  pair cannot silently reuse it.
- Label staffing is not exposed as the complete crew; no fabricated label-speed
  cap, extra batch delay or historical tonnage-derived efficiency is applied.
- Flushing consumes applicable machine time without booking the full quantity as
  waste, assuming 100% measured recovery, or importing another machine's volume.
- Container counts, saleable cases, filling time and elapsed shift output remain
  distinct; unknowns are reported as unknown rather than zero.

Current-code comparison: `site-mark4/lib/rules.ts` combines 10/6 Head eligibility,
allows 1/2/3/5 L, omits 4 L and holds the older 1/2/3 L speeds. These checks describe
the future MARK V changes; no production code or tests were changed here.
