# Revision 2 review and fix record

## Pass 1: source contracts and functional behavior

- Fully paginated factory supplier catalog and current original e-commerce/OMS reads. Five active OMS headers have broken detail responses; their company/volume is explicitly unknown.
- Fixed empty-success envelopes, stale-clock laundering, omitted quantity/scope fields and credential/redirect boundary issues.
- Added separate historical booked/MES values, actual recorded labour, existing PO/QC ledger and user date assumptions.
- Corrected EXIM integration so adding structured factory events does not suppress individual oil shipments. Overdue ETAs remain held.

## Pass 2: integrated source, model and UI

- Detected source product-code collisions that inflated a 1-litre order into 200-litre planning units. Added source/factory/planner identity guards, explicit held-line accounting, forecast/FG/value quarantine and a conservation bound.
- Accepted current Oil source demand reconciles exactly to mapped plus held/unmapped litres. Six current factory/planner conflicts have zero scheduled production and no inherited prices.
- Removed an inherited rice kg-to-oil-litre conversion; preserved unknown historical quantity/price coverage.
- 52 TypeScript tests and typecheck pass on VPS. Independent factory audit: 15 acceptance checks pass. Python source/feed/collector suite: 42 tests pass.
- Browser checked month history worth, machine labour, gross-demand bridge, incoming ledger, date assumption application, persistence after reload, mobile width, and favicon metadata. Corrected stale source-status copy, proposed-purchase wording, tiny-run hour rounding and missing years on old POs.
- Candidate HTTP release checks pass, including scenario date application and invalid IDs. Public release checks are recorded separately after deployment.

Remaining source limits are visible, not zero: five unreadable active OMS details; unclassified unknown-unit lines; unverified SKU mappings; missing historical SKU prices; supplier PO records without promised arrival dates. These are not claims of full source coverage.

## Public release verification

Released to https://jivo-mark4-astha.vercel.app on 6 September 2026, deployment `dpl_69AQHvz2a9t9SLCzsQeAxhGTBt9H`. Logged-out root response HTTP200. Both HTTP release scripts passed on the public URL, including malformed/oversized scenario rejection, all shift variants, actual worth/labour, demand conservation, date override and favicon. Public mobile browser: 390px viewport/document width, correct worth and partial-coverage badges, custom icon metadata, no console errors.

Owned recurring factory and demand collectors verified running/refreshed at 06:44–06:45 IST; the factory unit includes the durable identity-output option. Partial demand coverage is an explicit source result, not a collector crash. Temporary preview and browser automation stopped after verification.

## Light and dark mode — 6 September 2026

Added a persistent light/dark switch beside Refresh data. A first visit follows the device colour preference; the saved choice is applied before the page paints. All eight views, forms, notices, run blocks and drawers use the selected palette; print retains the light palette. Changes are confined to app/globals.css, app/layout.tsx, components/Planner.tsx and the new components/ThemeToggle.tsx.

VPS production build and TypeScript validation passed. Browser verification covered both toggle directions and reload persistence, all eight views at 390px with no page overflow or unthemed white cards, desktop/mobile visual review, and an empty browser console. Deployed as dpl_7LkcHPCjEiv4wpM74jPEVHHDpHpd to the same public Astha URL. Logged-out HTTP 200 and public mobile dark-mode persistence were verified. Scheduling and source-data logic were not changed.
