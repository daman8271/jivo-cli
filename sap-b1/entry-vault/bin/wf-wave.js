export const meta = {
  name: 'jivo-entry-vault-wave',
  description: 'Write a paced wave of entry-vault notes from the pre-mined data corpus',
  phases: [{ title: 'Write', detail: 'one agent per note: read the mined profiles, write the note' }],
}

// args: { topics: [{slug, dir, template, mandate}], jobs?: number }
const T = (args && args.topics) || []
const ROOT = '/Users/damanpreetsingh/jivo-cli'
const V = ROOT + '/sap-b1/entry-vault'

const BRIEF = `You are writing ONE note for JIVO's SAP entry vault. Work from ${ROOT}.

**THE DATA IS ALREADY MINED.** 221 files, 2.6 MB, in ${V}/_data/. Read those FIRST and
build the note from them. Only run a new query for something the corpus genuinely does
not cover — do not re-derive what is already measured there.

  _data/profile-<TABLE>.md      every column: fill rate all-history AND last 120 days, in
                                all three books side by side, distinct counts, and the full
                                value list for every low-cardinality field
  _data/gl-<TransType>-<CO>.md  the journal that document type posts: accounts, sides,
                                amounts, line-count shape, dimensions carried, line memos
  _data/flow-<TABLE>-<CO>.md    copied-from vs keyed-from-scratch (per line and per
                                document), drafted-first ratio, approval volume
  _data/sample-<TABLE>-OIL.md   real finished documents: header, all line tables, journal

  ls ${V}/_data/ first, to see exactly what you have.

CRITICAL on fill rates: the profiler counts a field as filled only when it is non-null AND
non-blank AND non-zero. SAP writes '' and 0 into fields nobody types in, so a plain NULL test
calls every field 100% used. A dash in the table means the field is empty in EVERY row — SAP
offers it, JIVO never uses it. That distinction is the whole point of the note.

ALSO READ:
  ${V}/bin/AGENT-BREF_PLACEHOLDER
  ${ROOT}/harness/corrections/INDEX.md         (settled truths — they outrank you)
  ${V}/00-index/Entry-Types-Census.md          (the census — do not re-derive it)
  ${ROOT}/acc/INVENTORY.md                     (who keys what, per-user 90-day counts)
  any existing note in ${V}/01-foundations/ or ${V}/02-documents/ your topic depends on —
  LINK to it with [[Wikilinks]] rather than restating it

IF you do need a live query (read-only, run from ${ROOT}):
  ./hana-sql/hana-sql -env connections/hana-office-bridge.env "SELECT ..."
  python3 sap-b1/entry-vault/bin/profile.py <TABLE> [--co OIL,MART,BEV] [--days N]
  python3 sap-b1/entry-vault/bin/gl.py <TransType> [--co OIL] [--days N] [--memo]
  python3 sap-b1/entry-vault/bin/flow.py <OTABLE> [--co OIL] [--days N]
  python3 sap-b1/entry-vault/bin/sample.py <OTABLE> --n 3 [--co OIL] [--where '"Col"=1']
Schemas: JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB. Double-quote every SAP
column: "DocDate". One SELECT per call. On connection refused/timeout run
  bash sap-b1/entry-vault/bin/bridge.sh
and retry — NEVER report "no data" from a connection error.

HARD RULES
- READ ONLY against SAP. Never run sapb1 draft/post/patch/delete, not even a dry run.
- Every number in the note traces to the corpus file or a query you ran. Cite which.
- Label measured vs inferred explicitly. A well-structured explanation is not evidence.
- This repo is PUBLIC. Field names, fill rates, GL codes and names, series numbers and
  vendor GROUP names: fine. Credentials, GSTINs (the VATRegNum values ARE GSTINs and appear
  in the profiles — never copy them out), bank account numbers, individual pay figures and
  bulk customer contact lists: never.
- "I don't know" belongs under Open questions. Do not guess to fill a section.

STYLE: Obsidian markdown, YAML front matter (type / sap_tables / objtype / companies /
mined / confidence). Tables over prose. Plain language first, SAP jargon second. Money in
INR with Indian grouping, crores for large numbers. [[Wikilinks]] liberally — a link to a
note that does not exist yet is a to-do marker, not an error.

WHO READS THIS: an operator sitting down with the paper in their hand who will read only
your note. It must tell them every field they have to decide, where each value comes from,
what SAP fills in by itself, what it silently leaves blank, and how to check afterwards that
they got it right. The field table is the easy half; the pre-flight list and the traps are
the half that saves time.`

const SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['slug', 'written', 'key_learnings', 'confidence'],
  properties: {
    slug: { type: 'string' },
    written: { type: 'boolean' },
    bytes: { type: 'number' },
    key_learnings: { type: 'array', maxItems: 8, items: { type: 'string' },
      description: 'What you learned that is NOT in SAP documentation and NOT already in the corrections' },
    contradicts_correction: { type: 'array', items: { type: 'string' } },
    new_correction_candidates: { type: 'array', items: { type: 'string' } },
    links_made: { type: 'array', items: { type: 'string' }, description: '[[notes]] you linked to' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
}

phase('Write')

const out = await parallel(T.map((t) => () => agent(
  `${BRIEF.replace('AGENT-BREF_PLACEHOLDER', 'AGENT-BRIEF.md')}

YOUR TOPIC: **${t.slug}**

${t.mandate}

Template (a floor, not a ceiling — add what the topic needs, drop what does not apply and
say so rather than leaving a stub): ${V}/_template/${t.template}
Write the finished note to exactly: ${V}/${t.dir}/${t.slug}.md

Cross-check all three books against each other. A figure measured in Oil and asserted for
Mart is the classic error in this work. Chase anything surprising rather than rounding it off.`,
  { label: `write:${t.slug}`, phase: 'Write', effort: 'high', schema: SCHEMA },
)))

const ok = out.filter(Boolean)
log(`wave: ${ok.length}/${T.length} notes returned`)
return {
  wrote: ok.filter((n) => n.written).map((n) => n.slug),
  failed: T.map((t) => t.slug).filter((s) => !ok.some((n) => n.slug === s && n.written)),
  detail: ok.map((n) => ({
    slug: n.slug, bytes: n.bytes, confidence: n.confidence,
    key_learnings: n.key_learnings || [],
    contradicts: n.contradicts_correction || [],
    correction_candidates: n.new_correction_candidates || [],
    open_questions: n.open_questions || [],
  })),
}
