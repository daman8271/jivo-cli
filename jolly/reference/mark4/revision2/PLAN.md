# Revision 2 implementation plan

Atlas recommended tracing original sources before changing the model or headlines. Implemented in the isolated Codex worktree only.

1. Read the complete factory supplier catalog and original e-commerce/OMS details. Preserve source errors, dates, units and unquantified active orders.
2. Add independent private collectors and a scalar-only public merger. Keep the existing Mark 3 collector unchanged.
3. Value historical booked and MES production separately at the same SKU realisation basis as the forward plan. Display recorded machine labour with period and run coverage.
4. Separate gross requested open demand, accepted scheduling quantities, current-horizon make demand, excluded scope and unmapped quantities.
5. Model individual EXIM shipments, outstanding factory POs and QC separately. Undated POs stay visible; user date assumptions are bounded, reversible scenarios.
6. Add responsive disclosures and a custom J4 favicon.
7. Review/fix twice: functional/source and security contracts first; then fresh integrated source, full regression suite, browser interactions and public HTTP behavior.

Important limits: five active OMS headers have failing detail endpoints; their litres and company remain unknown. Factory open PO creation dates are not supplier delivery promises. Historical worth uses inherited selling realisation, not actual revenue or booked manufacturing cost.
