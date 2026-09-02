export const meta = {
  name: 'tankhapay-vault',
  description: 'Author 14 TankhaPay section study notes in parallel from the JS corpus + endpoint inventory',
  phases: [
    { title: 'Author', detail: 'one agent per business section → wikilinked Obsidian note' },
    { title: 'Weave', detail: 'master endpoint index + completeness critic' },
  ],
}

const ROOT = '/Users/damanpreetsingh/jivo-cli/portals/tankhapay'
const SECTIONS = [
  'Dashboard','Employee-Management','Attendance','Leave-Management','Payouts',
  'Approvals','Accounts-Taxes','Reports','Recruit-ATS','Masters-Config',
  'Org-User-Management','Broadcast-Visitor-Help','Contract-Labour-Inventory','Training-Performance',
]

const NOTE_SCHEMA = {
  type: 'object',
  required: ['section','note_path','read_count','write_count','verified_reads'],
  properties: {
    section: { type: 'string' },
    note_path: { type: 'string' },
    read_count: { type: 'integer' },
    write_count: { type: 'integer' },
    verified_reads: { type: 'integer', description: 'reads whose payload shape was confirmed from a JS call site' },
    reclassified: { type: 'integer', description: 'endpoints whose heuristic READ/WRITE label was corrected' },
    highlights: { type: 'string', description: 'most useful read endpoints discovered' },
  },
}

function authorPrompt(sec) {
  return `You are documenting the **${sec}** section of a READ-ONLY reverse-engineering study of the
TankhaPay Business HR/payroll portal (business.tankhapay.com). Work entirely on local files under
${ROOT}. This is a real production system with live employee data — you only READ and DOCUMENT, you
never call write endpoints.

INPUTS (read these first):
- ${ROOT}/captures/sections/${sec}.tsv  — your endpoints, tab-separated: CLASS<TAB>URL (CLASS = READ|WRITE|UNKNOWN, heuristic).
- ${ROOT}/vault/_meta/Encryption-Scheme.md, Auth-and-Access.md, Backends-and-Environment.md, Read-Only-Guardrails.md — the crypto/auth model (already verified live). Read them so your note is consistent.
- ${ROOT}/captures/js/*.js — the ~20MB Angular corpus (main.7309d5d32824e620.js + chunk-*.js). This is where every endpoint's request payload and response shape live.

METHOD (per endpoint in your TSV):
1. For each READ endpoint, grep the corpus for its path's last segment (e.g. for
   .../dashboard/get_tpay_dashboard_data grep 'get_tpay_dashboard_data') to find the service method and
   its call sites. Extract the **request payload keys** (e.g. {action, accountId, geo_location_id, ouIds})
   and, where visible, what the response contains. Use commands like:
     grep -rohE '<name>\\([^)]{0,200}' ${ROOT}/captures/js/main.7309d5d32824e620.js ${ROOT}/captures/js/chunk-*.js | head
2. **Re-verify the READ/WRITE label** by reading the actual call site and the verb in the path. Correct
   any heuristic mistakes (e.g. insert_/send_/save_ are WRITES even if the regex called them READ).
   When genuinely ambiguous, mark it WRITE / out-of-scope rather than guess.
3. Note which reads need account context (accountId=2719, geo_location_id=37, ouIds="37,2211,38,40,31,1925"
   come from the decoded JWT) vs which take other params (date ranges, employee ids, etc.).

OUTPUT — write ONE Obsidian note to ${ROOT}/vault/${sec}.md with this structure:
- YAML frontmatter: tags: [tankhapay, section, ${sec.toLowerCase()}]
- H1 title + one-paragraph purpose (what this portal section does for an HR admin).
- A "Read endpoints (in-scope for the CLI)" table: | Endpoint (path) | Backend | Request payload keys | Returns | Notes |
- A "Write endpoints (documented, OUT OF SCOPE)" table: | Endpoint | What it does |
- A short "CLI command mapping" list: propose the read subcommands this section becomes
  (e.g. \`tankhapay-portal ${sec.toLowerCase().split('-')[0]} summary\`), one per useful read.
- Footer wikilinks: [[00-TankhaPay-Atlas]], [[Encryption-Scheme]], [[Auth-and-Access]], [[Read-Only-Guardrails]], and sibling sections.
Keep it precise and grounded in the corpus — no invented endpoints or fields. Do NOT make any network calls.

Return the structured summary object. note_path is the file you wrote.`
}

phase('Author')
const results = await pipeline(
  SECTIONS,
  (sec) => agent(authorPrompt(sec), {
    label: `author:${sec}`,
    phase: 'Author',
    schema: NOTE_SCHEMA,
    model: 'opus',
    agentType: 'general-purpose',
  }),
)

const done = results.filter(Boolean)
log(`Authored ${done.length}/${SECTIONS.length} section notes; ${done.reduce((a,r)=>a+(r.verified_reads||0),0)} reads verified from call sites`)

phase('Weave')
const critic = await agent(
  `All 14 TankhaPay section notes have been written under ${ROOT}/vault/*.md. Do all of the following:
1) Build the master read-only endpoint index at ${ROOT}/vault/TankhaPay-Endpoints.md from
   ${ROOT}/captures/endpoints-raw.tsv (columns CLASS<TAB>EXPORT<TAB>VAR<TAB>URL): a table grouped by the
   14 sections (use ${ROOT}/captures/sections/*.tsv to know which endpoint belongs to which section),
   with a per-section READ/WRITE count and a link to each section note. Add a short header explaining the
   {encrypted}/commonData model and linking [[Encryption-Scheme]] and [[Auth-and-Access]].
2) COVERAGE AUDIT (the user demanded nothing be missed): verify that (a) EVERY endpoint URL in
   endpoints-raw.tsv appears in exactly one section .tsv and is documented in the matching section note,
   and (b) every route in ${ROOT}/vault/Pages-and-Routes.md maps to a section. Produce a section named
   "## Coverage audit" in TankhaPay-Endpoints.md listing: total endpoints, per-section READ/WRITE counts,
   and an explicit list of ANY endpoint or route that is not covered by a section note (or state "0 gaps").
3) Completeness pass: list any section note that is missing, thin, or contradicts the _meta crypto/auth
   docs, and fix obvious gaps.
Read-only: no network calls. Return a short plain-text summary: index built, coverage-audit result
(gaps found + fixed, or 0 gaps), and any thin notes.`,
  { label: 'weave:index+coverage+critic', phase: 'Weave', model: 'opus', agentType: 'general-purpose' },
)

return {
  sections_authored: done.length,
  per_section: done.map(r => ({ section: r.section, reads: r.read_count, writes: r.write_count, verified: r.verified_reads, reclassified: r.reclassified })),
  weave: critic,
}
