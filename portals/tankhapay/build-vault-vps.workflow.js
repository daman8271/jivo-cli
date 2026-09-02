export const meta = {
  name: 'tankhapay-vault-vps',
  description: 'Author the 12 remaining TankhaPay section notes from the JS corpus, then weave a master index + coverage audit',
  phases: [
    { title: 'Author', detail: 'one agent per remaining section → wikilinked Obsidian note matching the exemplar' },
    { title: 'Weave', detail: 'master endpoint index + full coverage audit (0 gaps target)' },
  ],
}

const ROOT = '/root/jivo-cli/portals/tankhapay'

// 12 sections still missing a vault note (Accounts-Taxes + Leave-Management already authored).
const SECTIONS = [
  'Dashboard', 'Employee-Management', 'Attendance', 'Payouts', 'Approvals',
  'Reports', 'Recruit-ATS', 'Masters-Config', 'Org-User-Management',
  'Broadcast-Visitor-Help', 'Contract-Labour-Inventory', 'Training-Performance',
]

const AUTHOR = (s) => `You are authoring ONE Obsidian study note for the TankhaPay Business portal reverse-engineering vault.
This is a strictly READ-ONLY study of a live HR/payroll SaaS (business.tankhapay.com) holding real data for 593 employees.
You must NEVER make any network call and NEVER write any file except your one output note. No logins, no probes.

SECTION: ${s}
OUTPUT FILE (write exactly here): ${ROOT}/vault/${s}.md
ENDPOINT LIST for your section (CLASS<TAB>URL, one per line): ${ROOT}/captures/sections/${s}.tsv

CONTEXT YOU MUST READ FIRST (do not restate them, link them):
- ${ROOT}/vault/_meta/Encryption-Scheme.md  (AES-128-ECB, PKCS7, key 0123456789abcdef; {"encrypted":..} request, commonData response)
- ${ROOT}/vault/_meta/Auth-and-Access.md     (bearer JWT; account context tp_account_id=2719, geo_location_id=37, ouIds="37,2211,38,40,31,1925")
- ${ROOT}/vault/_meta/Backends-and-Environment.md (4 backends: business=business.tankhapay.com/api/, mobapi=mobapi.tankhapay.com/api/, tpPay=mobapi.tankhapay.com/, tnd=tnd.tankhapay.com/api/)
- ${ROOT}/vault/_meta/Read-Only-Guardrails.md
- ${ROOT}/vault/Accounts-Taxes.md            <-- THE EXEMPLAR. Match its structure, depth, and tone EXACTLY.

THE CORPUS to grep for evidence (Angular production bundle, ~20MB): ${ROOT}/captures/js/*.js
  Main bundle: ${ROOT}/captures/js/main.7309d5d32824e620.js  (endpoint constants live in module 4245).
  58 chunk-*.js files hold the feature/service/call-site code.

METHOD (evidence-based — every claim must come from the corpus, never invented):
1. Read your section TSV. For EACH endpoint, take the path tail (last 1-2 path segments) and grep the corpus for:
   - the endpoint's wrapper variable + service (e.g. \`grep -rn "get_tds_report_data" captures/js\`),
   - the CALL SITE(s): the object literal passed in, to extract the exact request PAYLOAD KEYS,
   - how the RESPONSE is consumed: JSON.parse(aesDecrypt(commonData)) vs. raw commonData vs. .data nesting.
2. RE-CLASSIFY every endpoint READ vs WRITE from its call site and verb, INCLUDING every one currently marked UNKNOWN.
   A read fetches/returns data for display; a write mutates (save/update/insert/delete/approve/reject/pay/upload/send/lock/sync/refresh-materialized-view). When ambiguous, treat as WRITE (out of scope) and say why.
3. Note which account-context params each read needs (accountId=2719, geo_location_id=37, ouIds, productTypeId) and which are field-level AES-encrypted vs plaintext.

WRITE THE NOTE exactly like ${ROOT}/vault/Accounts-Taxes.md:
- YAML frontmatter: tags: [tankhapay, section, ${s.toLowerCase()}]
- A tight intro paragraph: what this section does for an HR/payroll admin, naming the key routes.
- A "> " callout naming the bundle module / services / chunks the evidence came from.
- "## Read endpoints (in-scope for the CLI)" — a markdown table: | Endpoint (path) | Backend | Request payload keys | Returns | Notes | with a row per READ endpoint. Be specific about payload keys and response fields you actually found. Flag gotchas (undecrypted commonData, .data nesting, AES field-level encryption, DD/MM/YYYY dates, composite keys).
- An "### Account context these reads need" subsection.
- "## Write endpoints (documented, OUT OF SCOPE)" — a table | Endpoint | What it does | for every WRITE (incl. reclassified ones). Note these are never wired, per [[Read-Only-Guardrails]].
- "## CLI command mapping" — a fenced code block mapping each read to a proposed \`tankhapay-portal <group> <cmd>\` command (mirror the exemplar's style; account-context params auto-filled, never asked).
- Footer line of wikilinks to [[00-TankhaPay-Atlas]], the 5 _meta notes, [[Pages-and-Routes]], and the other 13 sibling sections.

Use [[wikilinks]] liberally. Do NOT fabricate endpoints or fields — if the corpus doesn't reveal a payload, say "payload not found in bundle" rather than guessing.

Return (as your final text, this is data not a message): a one-line-per-item summary: total endpoints in section, #READ documented, #WRITE documented, list of any UNKNOWN you reclassified (with new class), and any endpoint whose payload you could not find in the corpus.`

phase('Author')
const authored = await parallel(
  SECTIONS.map((s) => () =>
    agent(AUTHOR(s), { label: `author:${s}`, phase: 'Author', agentType: 'general-purpose' })
      .then((r) => ({ section: s, summary: r }))
  )
)

phase('Weave')
const weave = await agent(
  `All 14 TankhaPay section notes now exist under ${ROOT}/vault/*.md (Accounts-Taxes, Leave-Management + the 12 just written).
This is a READ-ONLY study vault. Make NO network calls. You may write ONLY ${ROOT}/vault/TankhaPay-Endpoints.md.

Do all of the following:

1) MASTER INDEX — write ${ROOT}/vault/TankhaPay-Endpoints.md:
   - A short header explaining the {"encrypted":..} request / commonData response model, linking [[Encryption-Scheme]] and [[Auth-and-Access]].
   - A table grouped by the 14 sections. For each section: link to its note ([[Section-Name]]), and its READ / WRITE / UNKNOWN counts computed from ${ROOT}/captures/sections/<Section>.tsv.
   - A grand-total row.

2) COVERAGE AUDIT — add a "## Coverage audit" section that PROVES nothing is missed (the user's hard requirement). Compute and report:
   (a) EVERY endpoint URL in ${ROOT}/captures/endpoints-raw.tsv (col 4) appears in exactly ONE ${ROOT}/captures/sections/*.tsv. List any endpoint in zero or in >1 section files.
   (b) For every READ endpoint, its path tail is documented in the matching ${ROOT}/vault/<Section>.md (grep the note). List any READ endpoint not documented in its section note.
   (c) Every route in ${ROOT}/vault/Pages-and-Routes.md maps to a section. List any unmapped route.
   Report: total endpoints, per-section READ/WRITE/UNKNOWN, total routes, and an explicit list of ANY gap — or the literal line "0 gaps" under each of (a)(b)(c) if clean.
   Use Bash/python to compute these set-difference checks; do not eyeball them.

3) THIN-NOTE PASS: list any section note that is missing, obviously thin, or contradicts the _meta crypto/auth docs. (Report only — do not rewrite other notes.)

Return (as data): the master index summary, the coverage-audit result for (a)(b)(c) with exact gap counts, and any thin notes.`,
  { label: 'weave:index+coverage-audit', phase: 'Weave', agentType: 'general-purpose' },
)

return { authored: authored.map((a) => ({ section: a.section })), weave }
