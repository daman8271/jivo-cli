#!/usr/bin/env python3
"""PHASE 6 — generate the Flipkart vault skeleton from the classified inventory.

READ-ONLY. Writes only inside portals/flipkart/vault/. Idempotent.
Generates section notes, the master Endpoints index, Pages-and-Routes, and the
coverage ledger. Analytical top-level notes (Atlas, Data-Model, Data-Inventory,
_meta) are hand-written separately.
"""
import json, os, collections, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.join(HERE, '..', 'vault')
TODAY = '2026-07-30'

S = json.load(open(os.path.join(HERE, 'sections.json')))

# section key -> (group dir, Title, one-line purpose)
META = {
 'seller:report-centre': ('seller', 'Report-Centre', 'Business/analytics report catalogue — list, count, categories, download; the Seller-Insights / earn-more pipeline.'),
 'seller:orders-shipments': ('seller', 'Orders-and-Shipments', 'Order & shipment lifecycle: my-orders, consignments, self-ship, put-lists, dispatch, labels, manifests.'),
 'seller:fulfilment-fbf': ('seller', 'Fulfilment-FBF', 'Fulfilled-By-Flipkart (FBF/FAssured) & FBF-Lite inbound, stock and shipment handling.'),
 'seller:listings-catalog': ('seller', 'Listings-and-Catalog', 'Catalogue: create/edit product, variants, listing search, image enrichment, alpha listings, documents.'),
 'seller:pricing-ratecard': ('seller', 'Pricing-and-RateCard', 'Price management, price scheduling, rate cards & commission.'),
 'seller:inventory-stock': ('seller', 'Inventory-and-Stock', 'Unified inventory, inventory health, SFX stock updates, SRM.'),
 'seller:payments-finance': ('seller', 'Payments-and-Finance', 'Settlements, payments, TDS, partner-master finance data.'),
 'seller:returns-recall': ('seller', 'Returns-and-Recall', 'Customer returns, RTO, and product recall workflows.'),
 'seller:promotions': ('seller', 'Promotions', 'Flipkart promotion / offer participation surfaces.'),
 'seller:lending-capital': ('seller', 'Lending-and-Growth-Capital', 'Seller lending and Flipkart Growth Capital applications.'),
 'seller:seller-qna-ugc': ('seller', 'Seller-QnA-and-UGC', 'Product Q&A and seller-generated content answers.'),
 'seller:compliance-regulation': ('seller', 'Compliance-and-Regulation', 'Regulation approvals, audit, approval-store, product compliance.'),
 'seller:communications': ('seller', 'Communications-and-Cases', 'Seller-buyer communications (SBC), case manager, notifications.'),
 'seller:other': ('seller', 'Seller-Misc-Services', 'Assorted seller napi micro-services not owned by another section (telemetry, home widgets, OTP, tracking).'),
 'seller:ads-fed': ('ads', 'Flipkart-Ads-and-FSN', 'Flipkart Ads (PLA/PCA campaigns via fed-ads) + Consolidated FSN performance + fkpromo.'),
 'seller:graphql': ('platform', 'GraphQL-Data-Core', 'The single /napi/graphql gateway — every dashboard widget is a GraphQL operation.'),
 'seller:printing': ('platform', 'Printing', 'Label / invoice printing certificate & signature service (health-check path).'),
 'seller:onboarding': ('platform', 'Onboarding-and-SPF', 'Seller onboarding, SPF, partner services.'),
 'seller:profile-account': ('platform', 'Profile-and-Account', 'Manage profile, multi-seller select, partner permissions, myp account surfaces.'),
 'seller:growth-insights': ('platform', 'Growth-Insights-and-Assistance', 'SIR insights, guided assistance, gamification, GA content, home-page growth widgets.'),
 'seller:coe': ('platform', 'COE', 'Centre-of-excellence remote surfaces.'),
 'vendorhub:vendor-purchase-orders': ('vendorhub', 'Vendor-Purchase-Orders', 'Vendor Hub 1P purchase orders, PO workbook download, GRN.'),
 'vendorhub:vendor-analytics': ('vendorhub', 'Vendor-Analytics', 'Sales & inventory analytics: aggregated metrics, purchasing trends, operational performance, product details.'),
 'vendorhub:vendor-catalog': ('vendorhub', 'Vendor-Catalog-and-Feeds', 'Cataloging (browse-tree, FSN create, feeds) and QC-norms / BIS compliance feeds.'),
 'vendorhub:vendor-payments': ('vendorhub', 'Vendor-Payments', 'Vendor payments, debit notes, invoice-debit downloads.'),
 'vendorhub:vendor-returns': ('vendorhub', 'Vendor-Returns', 'Return orders summary and RTV for the 1P vendor lane.'),
 'vendorhub:vendor-users-access': ('vendorhub', 'Vendor-Users-and-Access', 'User management, roles & warehouses, UAM authorisation, vendor picker, aggregate entities.'),
 'vendorhub:vendor-documents': ('vendorhub', 'Vendor-Documents', 'Document service: getFile/getDocument downloads, static documents, upload templates.'),
 'vendorhub:vendor-config-support': ('vendorhub', 'Vendor-Config-and-Support', 'Sale config, ticket portal (Freshworks), support mail, recon tool, TaaS migration check.'),
 'vendorhub:other': ('vendorhub', 'Vendor-Platform-Services', 'Retail-palantir request bus, Ryuk document jobs, Triton feed processor — the plumbing under the SPA.'),
}

RW = {'READ': 'R', 'READ_FILE': 'R-file', 'WRITE': 'W', 'EXPORT': 'W-export',
      'UNKNOWN': '?', 'UNKNOWN_READLIKE': '?read'}


def title_to_file(group, title):
    return os.path.join(VAULT, group, title + '.md')


def esc(s):
    return (s or '').replace('|', '\\|')


def write_section(key, rows):
    group, title, purpose = META[key]
    reads = [r for r in rows if r['class'] in ('READ', 'READ_FILE')]
    writes = [r for r in rows if r['class'] in ('WRITE', 'EXPORT')]
    unknowns = [r for r in rows if r['class'] in ('UNKNOWN', 'UNKNOWN_READLIKE')]
    os.makedirs(os.path.join(VAULT, group), exist_ok=True)
    out = []
    out.append('---')
    out.append(f'title: {title}')
    out.append(f'created: {TODAY}')
    out.append(f'updated: {TODAY}')
    out.append('project: jivo-cli')
    out.append('type: reference')
    out.append(f'tags: [flipkart, {group}, read-only]')
    out.append('status: studied')
    out.append('---')
    out.append('')
    out.append(f'# {title}')
    out.append('')
    out.append(f'> ⚠️ READ-ONLY. {purpose}')
    out.append('')
    out.append(f'**Endpoints in this section:** {len(rows)} '
               f'— {len(reads)} read-safe (READ/READ_FILE), '
               f'{len(writes)} write/export (out of scope), '
               f'{len(unknowns)} UNKNOWN (denied per G1, documented).')
    out.append('')
    out.append('All contracts are reverse-read from the on-disk SPA JS corpus '
               '(`captures/js/*`) unless a row is marked PROVEN in the notes. '
               'Method is taken from the bundle where resolvable, else `?`. '
               'Auth per [[Auth-and-Access]].')
    out.append('')
    if reads:
        out.append('## Read-safe endpoints (allowlist)')
        out.append('')
        out.append('| R/W | METHOD | Host · Path | Const | Class |')
        out.append('|---|---|---|---|---|')
        for r in sorted(reads, key=lambda x: x['path']):
            out.append(f"| {RW[r['class']]} | {r['method']} | `{esc(r['host'])}{esc(r['path'])}` | {esc(r['const']) or '—'} | {r['class']} |")
        out.append('')
    if writes:
        out.append('## Out of scope — writes/exports (never expose in a read-only CLI)')
        out.append('')
        out.append('| METHOD | Host · Path | Const | Class |')
        out.append('|---|---|---|---|')
        for r in sorted(writes, key=lambda x: x['path']):
            out.append(f"| {r['method']} | `{esc(r['host'])}{esc(r['path'])}` | {esc(r['const']) or '—'} | {r['class']} |")
        out.append('')
    if unknowns:
        out.append('## UNKNOWN — method/posture unresolved (G1: denied, documented only)')
        out.append('')
        out.append('| METHOD | Host · Path | Const |')
        out.append('|---|---|---|')
        for r in sorted(unknowns, key=lambda x: x['path']):
            out.append(f"| {r['method']} | `{esc(r['host'])}{esc(r['path'])}` | {esc(r['const']) or '—'} |")
        out.append('')
    out.append('## Connections')
    out.append('')
    out.append('- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · '
               'Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · '
               'Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]')
    out.append('')
    open(title_to_file(group, title), 'w').write('\n'.join(out))
    return group, title, len(rows), len(reads), len(writes), len(unknowns)


def main():
    summary = []
    for key, rows in sorted(S.items()):
        if key not in META:
            print('WARN no META for', key, len(rows)); continue
        summary.append((key,) + write_section(key, rows))

    # ---- master Endpoints index ----
    total = sum(len(v) for v in S.values())
    allrows = [r for v in S.values() for r in v]
    reads = [r for r in allrows if r['class'] in ('READ', 'READ_FILE')]
    writes = [r for r in allrows if r['class'] in ('WRITE', 'EXPORT')]
    unknown = [r for r in allrows if r['class'] in ('UNKNOWN', 'UNKNOWN_READLIKE')]
    L = []
    L.append('---')
    L.append('title: Flipkart Endpoints (read-only master index)')
    L.append(f'created: {TODAY}')
    L.append(f'updated: {TODAY}')
    L.append('project: jivo-cli')
    L.append('type: reference')
    L.append('tags: [flipkart, endpoints, master-index, read-only]')
    L.append('---')
    L.append('')
    L.append('# Flipkart — Read-Only Master Endpoint Inventory')
    L.append('')
    L.append(f'Every distinct API path found across the Seller Hub + Vendor Hub JS corpus '
             f'(`captures/js/*`), classified. **{total} distinct endpoints.** '
             f'`READ`/`READ_FILE` rows are safe to expose in a read-only CLI; '
             f'`WRITE`/`EXPORT` mutate or side-effect and are held out of scope; '
             f'`UNKNOWN` rows have a binding but the method/posture is unresolved from the '
             f'minified source — per **G1 they are denied by default** (documented, never wired).')
    L.append('')
    L.append('Atlas: [[00-Flipkart-Atlas]] · Routes: [[Flipkart-Pages-and-Routes]] · '
             'Data model: [[Flipkart-Data-Model]] · Data inventory: [[Flipkart-Data-Inventory]] · '
             'Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]]')
    L.append('')
    L.append('## Roll-up')
    L.append('')
    L.append('| Class | Count | Exposed in CLI? |')
    L.append('|---|---|---|')
    L.append(f'| READ (JSON) | {sum(1 for r in reads if r["class"]=="READ")} | yes |')
    L.append(f'| READ_FILE (download existing) | {sum(1 for r in reads if r["class"]=="READ_FILE")} | yes (download-only) |')
    L.append(f'| WRITE | {sum(1 for r in writes if r["class"]=="WRITE")} | **never** |')
    L.append(f'| EXPORT (enqueue/generate) | {sum(1 for r in writes if r["class"]=="EXPORT")} | **never** (G2) |')
    L.append(f'| UNKNOWN / UNKNOWN_READLIKE | {len(unknown)} | **never** (G1 denied) |')
    L.append(f'| **TOTAL** | **{total}** | |')
    L.append('')
    L.append('Legend: `READ` pure JSON query · `READ_FILE` downloads an already-generated '
             'binary · `WRITE` mutates data/state · `EXPORT` creates a report-request row '
             '(a WRITE per G2) · `UNKNOWN`/`?` method or read-vs-write not proven from the '
             'bundle → to-confirm, never exposed blind · `?read` = read-like verb but POST/unknown.')
    L.append('')
    # per section, in group order
    order = ['seller', 'ads', 'vendorhub', 'platform']
    by_group = collections.defaultdict(list)
    for key in S:
        if key in META:
            by_group[META[key][0]].append(key)
    for g in order:
        L.append(f'# {g.upper()} lane')
        L.append('')
        for key in sorted(by_group[g], key=lambda k: META[k][1]):
            rows = S[key]
            group, title, purpose = META[key]
            rd = sum(1 for r in rows if r['class'] in ('READ', 'READ_FILE'))
            wr = sum(1 for r in rows if r['class'] in ('WRITE', 'EXPORT'))
            un = sum(1 for r in rows if r['class'] in ('UNKNOWN', 'UNKNOWN_READLIKE'))
            L.append(f'## [[{title}]]')
            L.append('')
            L.append(f'{purpose}  \n**{len(rows)} endpoints** — {rd} read-safe · {wr} write/export · {un} unknown.')
            L.append('')
            L.append('| R/W | METHOD | Host · Path | Class |')
            L.append('|---|---|---|---|')
            for r in sorted(rows, key=lambda x: (x['class'], x['path'])):
                L.append(f"| {RW[r['class']]} | {r['method']} | `{esc(r['host'])}{esc(r['path'])}` | {r['class']} |")
            L.append('')
    open(os.path.join(VAULT, 'Flipkart-Endpoints.md'), 'w').write('\n'.join(L))

    print('sections written:', len(summary))
    print('endpoints indexed:', total, '(reads', len(reads), 'writes', len(writes), 'unknown', len(unknown), ')')


if __name__ == '__main__':
    main()
