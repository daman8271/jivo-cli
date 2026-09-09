# Independent Mark 4 release

Vercel app: jivo-mark4-astha (site-mark4 only). Input service: mark4-astha-inputs, loopback8794, separate HTTPS route. Existing Mark3 service/collector/cron untouched. Source files are read only, sanitized through an allowlist; no factory credentials copied to Vercel or exposed.

Deployment performed only after sanitizer security audit. Install service file under /etc/systemd/system and route under /docker/traefik/dynamic with unique names. Removal/rollback: stop and disable mark4-astha-inputs, remove only mark4-astha.traefik.yml. This does not change Mark3.

Build/test/browser work runs in isolated /root/mark4-astha on VPS. Local worktree is source of truth.

Revision 2 adds owned `mark4-astha-factory.service` and `mark4-astha-demand.timer`/`.service`. Factory reads every three minutes, caches the complete supplier PO catalog for 30 minutes, and refreshes the complete factory SKU catalog every 12 hours. Demand refreshes original e-commerce rows and all OMS creator header lists every three minutes; unreadable active orders remain quantified as unknown. A daily numeric-ID backstop supplements discovery. Dedicated OMS/e-commerce credentials remain under the private `demand-audit` directory. No credentials go into the app.

The input service reads `--supplement-root /root/mark4-astha/state`. Partial or failed supplements retain their original timestamps. Public output uses scalar allowlists. Individual EXIM shipments supplement factory PO/QC events; undated POs do not become dated receipts. Mapping requires agreement between source, factory identity and planner identity; conflicting quantities remain visible and cannot produce another SKU.

Release checks: `verify_http.py <base>` and `verify_revision_http.py <base>`. Build and browser verification run in `/root/mark4-astha/app` on VPS. To remove this independent installation, also stop/disable `mark4-astha-factory.service` and `mark4-astha-demand.timer`; leave all Mark 3 services alone.

Revision 3 adds independent `mark4-astha-material-orders.service` and `mark4-astha-materials.service` (180-second target cycles), plus `mark4-astha-material-history.service` (hourly historical-coverage check). They use private cache `/root/mark4-astha/private/material-supply`; the reconciled `material-supply.json` replaces inherited material stock and legacy incoming credits. Supplier catalogs refresh each full scan. Older gate history is warmed separately and unresolved relevant records stay on the fast refresh. EXIM authentication uses its existing client's private token cache; that narrow path is writable in the materials unit so automatic login refresh remains possible.

Use `verify_material_http.py` for revision-3 acceptance; the older revision-2 incoming-event assumptions are no longer the release contract. It checks source/model revision agreement, lot bounds, usable-date ordering, owned stock and recorded-only behavior. Two live production cycles were verified on 6 September 2026. The full plan, decisions, tests, independent review, release record and rollback are in `reference/mark4/revision3/`. To roll back this addition, stop only the three new material services and restore the owned feed/scripts per that runbook.
