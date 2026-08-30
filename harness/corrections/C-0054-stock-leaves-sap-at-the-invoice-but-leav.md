---
id: C-0054
date: 2026-08-30
author: Daman
area: all
severity: high
status: active
supersedes: 
tags: [storage]
---

# Stock leaves SAP at the invoice, but leaves the godown when the truck goes

## Wrong
Read SAP OITW.OnHand as the physical contents of a warehouse, and computed free storage space from it.

## Right
JIVO raises the invoice FIRST and the truck often leaves the NEXT DAY. SAP decrements stock at the invoice, but the goods are still physically occupying the godown until the vehicle is actually dispatched. Operationally JIVO does not consider goods out of the warehouse until the truck carrying them has gone. So SAP OnHand UNDERSTATES physical occupancy, and any free-space figure derived from it is too optimistic by the volume that is invoiced-but-not-yet-trucked. The real physical occupancy = SAP OnHand + invoiced-not-dispatched. The dispatch/gate-out event in the factory app (ji.jivo.in), not the invoice date, is the moment space is actually released.

## Evidence
Stated by Daman 2026-08-30: 'sometimes for dispatch we put the invoice first, and that shows the storage is pretty low because the dispatch has been done. Unless the truck hasn't been dispatched we do not consider that stuff out of the warehouse.' Magnitude to be measured from the invoice-date vs gate-out timestamp gap in the factory app's dispatch module; Aug-2026 Oil outbound was 1,847,240 L over the month, so one day of lag is on the order of 71,000 L against 162,659 L of apparent free space.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
SAP OITW.OnHand is post-invoice, NOT physical. Goods invoiced but not yet trucked still occupy the godown. For storage space use OnHand + invoiced-not-dispatched (gate-out event in ji.jivo.in), never OnHand alone.
