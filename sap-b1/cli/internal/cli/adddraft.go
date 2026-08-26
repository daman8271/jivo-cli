package cli

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"sort"
	"strconv"
	"strings"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// add-draft presses Add. It is the only command in this tool that creates a
// document nothing here can undo.
//
// ---------------------------------------------------------------------------
// WHY THERE ARE NO GUARD OVERRIDE FLAGS ON THIS COMMAND
// ---------------------------------------------------------------------------
// `delete` has six, and every one of them is justified: its guards read a LOCAL,
// FALLIBLE piece of evidence — an unsigned write log on this machine — and an
// operator standing in front of the SAP client genuinely knows things that file
// does not. "A person keyed this draft by hand" is a fact only they can supply.
//
// Every guard here reads a SAP-SIDE FACT instead. Is the draft still Open. Is it
// in somebody's approval queue right now. Are the GRPO lines it consumes still
// open. Has the row changed since you looked at it. A local file cannot forge
// any of those, and an operator cannot assert past one — they can only be WRONG
// about it. An override flag on a server-side fact is not the operator adding
// information; it is a button that makes the server's answer go away, and on
// this command the server's answer is the only thing standing between a typo and
// a duplicate invoice in a GST return.
//
// So: no --closed, no --in-approval, no --not-created-here, no --force. If a
// guard here refuses, the answer is to go and look in SAP, not to add a flag.
//
// ---------------------------------------------------------------------------
// WHY --yes IS STILL LEGAL WITHOUT A TERMINAL
// ---------------------------------------------------------------------------
// The honest control on this command is guard 7 — a full field diff taken
// immediately before each POST, against exactly what was previewed — not the
// presence of a human at a tty. If the draft is byte-identical to what was
// previewed, `--yes` after a `--dry-run` is exactly as safe as a typed "yes"; if
// it is not, the command refuses whether or not anybody is watching. Requiring a
// terminal would break acc/apbatch and push operators into faking a PTY, which
// is strictly worse than the thing it was meant to prevent.
//
// ---------------------------------------------------------------------------
// WHY THE GUARDS ARE ALL FRONT-LOADED
// ---------------------------------------------------------------------------
// A POST that FAILS is not free. Every request that goes out is an opportunity
// for exit 7 — sent, no answer, it may have committed — which is the worst state
// this system can produce, because the recovery is a human reading SAP. Every
// guard moved in front of the send is one fewer chance of landing there. That is
// why this command reads a great deal before it writes anything.
//
// ---------------------------------------------------------------------------
// WHAT THIS COMMAND WILL NEVER DO
// ---------------------------------------------------------------------------
// Approve on somebody else's behalf. That is PATCH ApprovalRequests /
// DraftsService_HandleApprovalRequest, it is a second person's authority, and no
// flag here may ever reach it. It is not a missing "finishing touch"; it is the
// point.

// maxAddBatch caps one invocation, and matches delete's cap: the owner does not
// want an artificial limit, and the real control is the confirmation prompt,
// which names the money going live. A cap still exists so a fat-fingered shell
// glob cannot turn into a thousand posted invoices.
const maxAddBatch = 50

// Approval states this command acts on. approvalFree ("dasWithout") lives in
// delete.go and is shared.
//
// Pressing Add at JIVO is TWO clicks, not one, and that is why this is a
// two-value gate rather than one:
//
//  1. Add on a dasWithout draft  -> submits it to approval (dasPending).
//     Nothing enters the books.
//  2. an approver approves       -> dasApproved. The draft is STILL a draft.
//  3. Add AGAIN on the approved draft -> it becomes a real posted document.
//
// Step 3 is not automatic: counted live on 2026-08-24, Oil had 78 open A/P
// drafts sitting at dasApproved totalling Rs 87.55 lakh, 71 of them from this
// month, and dasGenerated was ZERO — nothing auto-posts on approval, a human
// must press Add a second time. Automating only click 1 would leave the bigger
// half undone, and it is the half where a second person has ALREADY reviewed the
// document.
const approvalApproved = "dasApproved"

// addAction is which of the two clicks a given draft is at, decided from the row
// SAP returned and never from a flag.
//
// There is deliberately no --submit / --post switch. The DocEntry the operator
// names determines which click this is; the preview tells them which it is and
// what it will do. A flag would only ever be a way to pass the wrong one.
type addAction int

const (
	// actionSubmit is a dasWithout draft. Adding it normally creates an approval
	// REQUEST and nothing enters the ledger — but if no template matches the
	// document, SAP posts it live instead. The preview says both.
	actionSubmit addAction = iota
	// actionPost is a dasApproved draft: click 2. The approval has already been
	// given, so this Add puts the document in the books.
	actionPost
)

// goesLive reports whether this action is certain to produce a posted document.
// An actionSubmit MAY also post (no matching template), which is exactly why the
// preview never promises it will not.
func (a addAction) goesLive() bool { return a == actionPost }

func (a addAction) label() string {
	if a == actionPost {
		return "POST LIVE"
	}
	return "submit for approval"
}

// addDocType is one DRAFT DOCUMENT TYPE this command knows how to Add.
//
// A TABLE, not a string compare, and that is the whole point of it. Every
// doctype-specific fact the guards, the preview and the outcome classification
// need is read out of THIS struct: which base document to check, what to call
// it, where the posted document lands and how to recognise it, and what shape
// the snapshot takes. Adding oPurchaseOrders or oInvoices later is adding a row
// here plus its tests — the guard logic, the batch loop and the renderers do not
// change.
//
// If you find yourself writing `if t.ObjectCode == "oPurchaseInvoices"` anywhere
// below, stop: the fact you need belongs in this struct instead.
type addDocType struct {
	// ObjectCode is DocObjectCode as SAP spells it on the ODRF row.
	ObjectCode string
	// Noun is what one of these is called to an operator, e.g. "A/P invoice".
	Noun string
	// Kind is the summary + snapshot shape. Several doctypes may share one.
	Kind draftKind

	// BaseEntitySet is what guard 6b reads to prove the lines this draft
	// consumes are still open, and BaseObjectType is the numeric ObjType that
	// DocumentLines[].BaseType must carry for that read to be the right one.
	// An empty BaseEntitySet means this doctype draws on no base document and
	// guard 6b does not apply to it.
	BaseEntitySet  string
	BaseObjectType float64
	BaseNoun       string // "GRPO", for the sentence the operator reads

	// BecameEntitySet and BecameMatch are the corroborating read AFTER a post:
	// which entity set the posted document lands in, and the header fields that
	// identify it. Exactly one match is a confirmation; zero or several is
	// reported as inconclusive and never guessed at.
	BecameEntitySet string
	BecameMatch     []string
}

// kindAddDraft is the summary + snapshot shape for a document draft being Added.
//
// SEPARATE FROM kindDraft ON PURPOSE, and it must stay separate.
// delete_record_test.go pins delete's snapshot contents byte for byte, and those
// bytes are the shared write-log format for every delete on every box in the
// fleet. Widening kindDraft to get the fields guard 7 needs would change that
// format for a command that has nothing to do with this one.
//
// It is a new VALUE of the existing draftKind TYPE, which is what buys
// requireRequestedRow, snapshotOf, snapshotDigest, entityPath, draftStatus and
// sortedKeys verbatim, with zero edits to delete.go.
var kindAddDraft = draftKind{
	Command:    "add-draft",
	EntitySet:  "Drafts",
	Noun:       "draft",
	WhereInSAP: "Document Drafts",
	SummaryFields: []string{
		"DocEntry", "DocNum", "DocObjectCode", "DocType", "DocumentSubType",
		"CardCode", "CardName", "DocDate", "DocDueDate", "TaxDate",
		"DocTotal", "VatSum", "WTAmount", "DocCurrency", "NumAtCard",
		"DocumentStatus", "AuthorizationStatus", "BPLName", "Series",
		"UserSign", "CreationDate", "UpdateDate", "Comments",
	},
	// Wider than kindDraft's. Guard 7 refuses on any difference in this list, so
	// a field left out is a field a colleague can change between the preview and
	// the POST without the command noticing. WTAmount, DocumentSubType and
	// BPL_IDAssignedToInvoice are here for exactly that reason — they decide the
	// TDS, the GST document sub-type and the branch the invoice bills from.
	SnapshotFields: []string{
		"DocEntry", "DocNum", "DocObjectCode", "DocType", "DocumentSubType",
		"CardCode", "CardName", "DocDate", "DocDueDate", "TaxDate",
		"DocTotal", "VatSum", "WTAmount", "TotalDiscount", "RoundingDiffAmount",
		"DiscountPercent", "DocCurrency", "DocRate", "NumAtCard",
		"DocumentStatus", "Cancelled", "UserSign", "CreationDate", "UpdateDate",
		"Comments", "JournalMemo", "AttachmentEntry", "Series", "BPLName",
		"BPL_IDAssignedToInvoice", "AuthorizationStatus", "ControlAccount",
		"PaymentGroupCode",
	},
	LineCollections: map[string][]string{
		"DocumentLines": {
			"LineNum", "ItemCode", "ItemDescription", "Quantity", "UnitPrice",
			"GrossPrice", "DiscountPercent", "LineTotal", "TaxCode", "TaxTotal",
			"AccountCode", "WarehouseCode", "CostingCode", "CostingCode2",
			"CostingCode3", "WTLiable", "BaseType", "BaseEntry", "BaseLine",
			"LineStatus",
		},
	},
}

// addDocTypes is the whole scope of this command, keyed by DocObjectCode.
//
// oPurchaseInvoices is first because it is the live batch this was built for and
// the only doctype every guard below has been evidenced against. The others are
// coming; each is a row here, its own tests, and nothing else.
var addDocTypes = map[string]addDocType{
	"oPurchaseInvoices": {
		ObjectCode: "oPurchaseInvoices",
		Noun:       "A/P invoice",
		Kind:       kindAddDraft,
		// An A/P invoice draft at JIVO is almost always drawn from a Goods
		// Receipt PO. ObjType 20 is that document; a line claiming any other
		// base type is a draft this command cannot check, and it says so rather
		// than reading the wrong entity set by the same number.
		BaseEntitySet:   "PurchaseDeliveryNotes",
		BaseObjectType:  20,
		BaseNoun:        "GRPO",
		BecameEntitySet: "PurchaseInvoices",
		// The same identity acc/apbatch's pre-check already uses: a vendor plus
		// their bill number. Not draftKey — that column exists in HANA (OPCH)
		// and is NOT reachable over the Service Layer, so verification must not
		// rest on it.
		BecameMatch: []string{"CardCode", "NumAtCard"},
	},
}

// supportedAddDocTypes names the scope in a stable order, for the refusal.
func supportedAddDocTypes() []string {
	out := make([]string, 0, len(addDocTypes))
	for code, t := range addDocTypes {
		out = append(out, fmt.Sprintf("%s (%s)", code, t.Noun))
	}
	sort.Strings(out)
	return out
}

// addFlags backs `add-draft`. Three flags, and none of them is an override:
// --dry-run, --yes, and the inherited global --json.
type addFlags struct {
	yes    bool
	dryRun bool
}

func newAddDraftCmd() *cobra.Command {
	var af addFlags

	cmd := &cobra.Command{
		Use:   "add-draft <DocEntry> [<DocEntry>...]",
		Short: "ADD a draft — press Add on it in SAP (irreversible from this CLI)",
		Long: `add-draft does what a human does in SAP B1 → Document Drafts → Add.

This is the one command in this tool whose result cannot be undone from here.
Adding a draft can put a real document in the books: stock moves, the vendor's
ledger moves, and it lands in a GST return. Only SAP can reverse that, and only
a person in the SAP B1 client.

Pressing Add at JIVO is TWO clicks, and which one you get depends on the draft:

  AuthorizationStatus dasWithout   Add SUBMITS it for approval. Nothing enters
                                   the ledger — unless no approval template
                                   matches the document, in which case SAP posts
                                   it live. The preview says which.
  AuthorizationStatus dasApproved  the approval has already been given, so Add
                                   POSTS IT LIVE. This is click two.

Anything else is refused: dasPending is in somebody's queue right now,
dasRejected is a person's decision this command will not override, and a draft
that is no longer Open has already been Added once.

There are NO override flags. Every guard here reads a fact from SAP — is it
open, is it in an approval queue, are its GRPO lines still open, has it changed
since you looked — and a flag on a server-side fact is not you adding
information, it is a button that makes SAP's answer go away. If a guard refuses,
go and look in SAP.

Each draft is read first and shown to you in full, the whole batch is previewed
and confirmed ONCE — naming the money going live separately from the money going
for approval — and then they are posted one at a time, stopping at the first
problem. Immediately before each POST the row is re-read and compared field by
field with what you were shown; any difference stops the batch with nothing sent
for that DocEntry.

--yes is accepted without a terminal. The control on this command is that field
diff, not a tty: a draft identical to the one you previewed is as safe to add
with --yes as with a typed "yes", and one that is not is refused either way.

This command NEVER approves on anybody's behalf. Approving is a second person's
authority in the SAP B1 client, and no flag here reaches it.`,
		Example: exampleBlock(
			`sapb1 add-draft 55126 --dry-run              # read it, run every guard, show the POST, send nothing`,
			`sapb1 add-draft 55126 55130 55131            # preview all three, confirm once`,
			`sapb1 add-draft 55126 --yes --json           # for acc/apbatch: one JSON record per draft`,
		),
		Args: func(cmd *cobra.Command, args []string) error {
			if len(args) == 0 {
				return &errs.UsageError{Msg: "which draft? Pass one or more DocEntry numbers, e.g. `sapb1 add-draft 55126`"}
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			return runAddDrafts(cmd, args, af)
		},
	}

	cmd.Flags().BoolVar(&af.yes, "yes", false, "skip the confirmation prompt (legal without a terminal — the field diff before each POST is the real control)")
	cmd.Flags().BoolVar(&af.dryRun, "dry-run", false, "read the drafts, run every guard, print the POSTs that WOULD be sent; sends none (this one DOES read SAP)")

	return cmd
}

// addPreflight is one DocEntry after the read-only lookup: the row, what it is,
// which click it is at, what it draws on, and anything standing in the way.
type addPreflight struct {
	DocEntry int64
	Type     addDocType
	Obj      map[string]interface{}
	// Snapshot is the row as it read at PREFLIGHT — the bytes the operator is
	// shown and confirms. Guard 7 compares the row as it reads immediately
	// before the POST against THIS, and refuses on any difference.
	Snapshot json.RawMessage
	// Status and Approval are DocumentStatus and AuthorizationStatus as they read
	// at preflight. Both are re-checked on the fresh row before the send.
	Status   string
	Approval string
	Action   addAction
	Total    float64
	Origin   *draftOrigin
	// OriginDoubt is set when a write-log line vouches for this draft but
	// disagrees with SAP about it. On delete that is a refusal; here provenance
	// is informational, so it becomes a sentence in the summary instead of a
	// reassuring "yes".
	OriginDoubt string
	Bases       []addBaseRef
	TDS         addTDSNote
	Problems    []draftProblem
}

// addBaseRef is one base document this draft consumes, and the verdict on it.
type addBaseRef struct {
	EntitySet string
	DocEntry  int64
	Lines     []int64 // the BaseLines this draft consumes
	DocNum    string
	OK        bool
	Note      string
}

// addTDSNote is what the summary says about withholding tax. It never refuses —
// see the ruling in writeAddSummary.
type addTDSNote struct {
	HeaderAmount   float64
	LiableLines    int
	TotalLines     int
	VendorCardCode string
	VendorLiable   string // SubjectToWithholdingTax as SAP spelled it, or ""
	VendorCodes    []string
	Contradiction  bool // every line tYES but SAP computed nothing (the C-0018 shape)
}

func runAddDrafts(cmd *cobra.Command, args []string, af addFlags) error {
	// A closed stdout must come back as an error this command can report on, not
	// as a signal that kills it between two POSTs.
	ignoreSIGPIPE()

	cfg, err := writeConfigMsg(cmd, "--csv is not supported for add-draft; use --json for machine-readable output (one JSON object per draft)")
	if err != nil {
		return err
	}

	entries, dupes, err := parseDocEntries(args)
	if err != nil {
		return err
	}

	errOut := cmd.ErrOrStderr()
	for _, d := range dupes {
		fmt.Fprintf(errOut, "note: DocEntry %d given twice — it will be added once.\n", d)
	}
	if len(entries) > maxAddBatch {
		return &errs.UsageError{Msg: fmt.Sprintf(
			"%d DocEntries in one command — the cap is %d. Split the list; every one of these can become a live document",
			len(entries), maxAddBatch)}
	}

	// Prove the audit trail can be written BEFORE the first document is live.
	// SaveDraftToDocument checks this again on every call — that is the check
	// that actually guards the write — but finding a read-only checkout after
	// three of nine invoices have posted is a far worse afternoon.
	if bad, logErr := client.CheckAddDraftLogTargets(); logErr != nil {
		return &errs.ConfigError{Msg: fmt.Sprintf(
			"refusing to start: the write log at %s cannot be written (%v).\n"+
				"  An Add cannot be undone from here, so it is not allowed without a record. Fix that path, then re-run",
			bad, logErr)}
	}

	// One pass over the fleet's write logs for the whole batch. Here provenance
	// is INFORMATIONAL — see writeAddSummary — so nothing below can refuse on it.
	logPaths, notes := provenanceLogPaths()
	for _, n := range notes {
		fmt.Fprintln(errOut, n)
	}
	idx, _, problems := buildProvenanceIndex(logPaths, kindAddDraft.EntitySet, cfg.CompanyDB)
	for _, p := range problems {
		fmt.Fprintf(errOut, "warning: %s\n", p)
	}

	c := client.New(cfg)
	c.SetErrWriter(errOut)

	pfs, err := preflightAddDrafts(cmd, c, cfg, entries, idx)
	if err != nil {
		return err
	}

	// Summaries go to stderr so stdout stays machine-readable in --json mode; in
	// plain dry-run mode stdout is the report, so they go there.
	summaryOut := errOut
	if af.dryRun && !cfg.JSON {
		summaryOut = cmd.OutOrStdout()
	}
	var refusals []string
	for _, pf := range pfs {
		writeAddSummary(summaryOut, cfg, pf)
		for _, p := range pf.Problems {
			refusals = append(refusals, p.Msg)
		}
	}

	// BATCH-LEVEL FAIL-CLOSED. If any draft in the list has a problem, the WHOLE
	// batch refuses having sent nothing — not "skip that one and carry on".
	// The operator is approving a TOTAL at the prompt; a partial batch they did
	// not agree to is not what they asked for, and on this command the
	// difference is live documents.
	if len(refusals) > 0 {
		if cfg.JSON {
			if err := renderAddRefusedBatch(cmd.OutOrStdout(), cfg, pfs, af.dryRun); err != nil {
				return err
			}
		}
		return &errs.RefusedError{Msg: strings.Join(refusals, "\n\n")}
	}

	if af.dryRun {
		return renderAddDryRun(cmd, cfg, pfs)
	}

	previewAdd(errOut, cfg, pfs)
	if err := confirmPrompt(cmd, addPrompt(cfg, pfs), af.yes, stdinIsTTYFunc()); err != nil {
		return err
	}

	return addSequentially(cmd, c, cfg, pfs)
}

// preflightAddDrafts reads every DocEntry and runs the read-only guards. It
// sends no POST and stops at the first read error — a batch that cannot be read
// cannot be judged.
func preflightAddDrafts(cmd *cobra.Command, c *client.Client, cfg *config.Config, entries []int64, idx map[originKey]draftOrigin) ([]addPreflight, error) {
	out := make([]addPreflight, 0, len(entries))
	// Caches for the whole batch: a nine-draft run from one vendor against one
	// GRPO should read each of them once.
	bases := map[int64]map[string]interface{}{}
	vendors := map[string]map[string]interface{}{}

	for _, docEntry := range entries {
		pf := addPreflight{DocEntry: docEntry, Type: addDocType{Kind: kindAddDraft}}

		res, err := c.GetEntity(cmd.Context(), kindAddDraft.EntitySet, docEntry)
		if err != nil {
			return nil, err
		}

		// GUARD 1 — IT MUST EXIST. This INVERTS delete's behaviour, deliberately.
		//
		// delete.go treats a 404 as "already deleted — skip it and carry on",
		// which is what makes re-running a partially-failed delete batch work.
		// Here the opposite is true: SaveDraftToDocument does NOT remove the ODRF
		// row, it CLOSES it, so a draft that has been Added still reads back. A
		// MISSING draft therefore means one of three things — somebody deleted
		// it, the DocEntry is wrong, or we are pointed at the wrong company — and
		// all three mean stop and look, not carry on into the rest of the list.
		if !res.Found {
			pf.Problems = append(pf.Problems, draftProblem{
				Guard: "missing",
				Msg: fmt.Sprintf(
					"refusing to add %s(%d): it does not exist in %s.\n"+
						"  Adding a draft does not delete it — SAP closes the row and leaves it in place — so a draft that is not there was never here, was deleted, or belongs to another company (check --company).\n"+
						"  Nothing in this batch was attempted.",
					kindAddDraft.EntitySet, docEntry, cfg.CompanyDB),
			})
			out = append(out, pf)
			continue
		}

		// GUARD 2 — and it must be THAT row. A 2xx carrying an HTML error page or
		// a Service Layer error envelope would otherwise make every guard below
		// pass vacuously, on the command where that ends in a live document.
		pf.Obj = decodeWriteObject(res.Body)
		if err := requireRequestedRow(cfg, kindAddDraft, docEntry, res.Status, res.Body, pf.Obj); err != nil {
			return nil, err
		}

		// GUARD 3 — SCOPE. Exit 2, not exit 9: "this command does not do that
		// doctype yet" is the command being wrong for the job, not SAP saying no.
		objectCode := formatCell(pf.Obj["DocObjectCode"])
		docType, known := addDocTypes[objectCode]
		if !known {
			return nil, &errs.UsageError{Msg: fmt.Sprintf(
				"%s(%d) in %s is a %s draft, which add-draft cannot add yet.\n"+
					"  Supported today: %s.\n"+
					"  The others are coming — each is one row in the doctype table plus its guards' evidence, not a rewrite. Add this one in the SAP B1 client for now.",
				kindAddDraft.EntitySet, docEntry, cfg.CompanyDB, blankAs(objectCode, "(no DocObjectCode)"),
				strings.Join(supportedAddDocTypes(), ", "))}
		}
		pf.Type = docType
		pf.Snapshot = snapshotOf(pf.Obj, docType.Kind)
		pf.Status = draftStatus(pf.Obj)
		pf.Approval = formatCell(pf.Obj["AuthorizationStatus"])
		pf.Total, _ = numberValue(pf.Obj["DocTotal"])

		checkAddOpen(&pf, cfg)
		checkAddApproval(&pf, cfg)
		checkAddLineIntegrity(&pf, cfg)
		if err := checkAddBaseLines(cmd, c, cfg, &pf, bases); err != nil {
			return nil, err
		}
		if err := describeAddTDS(cmd, c, &pf, vendors); err != nil {
			return nil, err
		}
		noteAddProvenance(cfg, &pf, idx)

		out = append(out, pf)
	}
	return out, nil
}

// blankAs renders an empty string as a placeholder, so a refusal never reads
// "is a  draft".
func blankAs(s, placeholder string) string {
	if strings.TrimSpace(s) == "" {
		return placeholder
	}
	return s
}

// addPrompt is the sentence above the confirmation, and it names the money.
//
// SPLIT, not one total. A batch can mix a draft that will merely go for approval
// with one that will post live, and the consequences are nothing alike. A person
// approving a mixed batch must not read one figure and think all nine are
// harmless.
func addPrompt(cfg *config.Config, pfs []addPreflight) string {
	live, liveSum, pending, pendingSum := addTotals(pfs)
	switch {
	case live > 0 && pending > 0:
		return fmt.Sprintf(
			"Type 'yes' to ADD %d draft(s) to %s — Rs %s going LIVE (%d) and Rs %s for approval (%d), irreversible from this CLI: ",
			len(pfs), cfg.CompanyDB, formatRupees(liveSum), live, formatRupees(pendingSum), pending)
	case live > 0:
		return fmt.Sprintf(
			"Type 'yes' to POST %d approved draft(s) LIVE to %s — Rs %s, irreversible from this CLI: ",
			live, cfg.CompanyDB, formatRupees(liveSum))
	default:
		return fmt.Sprintf(
			"Type 'yes' to ADD %d draft(s) to %s — Rs %s, submitted for approval unless no template matches, irreversible from this CLI: ",
			pending, cfg.CompanyDB, formatRupees(pendingSum))
	}
}

// addTotals splits the batch by what will actually happen to each draft.
func addTotals(pfs []addPreflight) (live int, liveSum float64, pending int, pendingSum float64) {
	for _, pf := range pfs {
		if pf.Action.goesLive() {
			live++
			liveSum += pf.Total
			continue
		}
		pending++
		pendingSum += pf.Total
	}
	return live, liveSum, pending, pendingSum
}

// previewAdd prints the exact requests and the two money columns, then leaves
// the prompt to confirmPrompt.
func previewAdd(w io.Writer, cfg *config.Config, pfs []addPreflight) {
	live, liveSum, pending, pendingSum := addTotals(pfs)
	fmt.Fprintln(w, "About to ADD to SAP:")
	fmt.Fprintf(w, "  company : %s\n", cfg.CompanyDB)
	fmt.Fprintf(w, "  user    : %s\n", cfg.User)
	fmt.Fprintf(w, "  drafts  : %d\n", len(pfs))
	if live > 0 {
		fmt.Fprintf(w, "  LIVE    : %d draft(s), Rs %s — approved already; this posts them to the books. Stock and ledgers move. Only SAP can reverse it.\n", live, formatRupees(liveSum))
	}
	if pending > 0 {
		fmt.Fprintf(w, "  approval: %d draft(s), Rs %s — submitted for approval; nothing enters the ledger unless no template matches, in which case SAP posts it live.\n", pending, formatRupees(pendingSum))
	}
	for _, pf := range pfs {
		fmt.Fprintf(w, "  request : POST %s%s   %s   [%s(%d) — %s]\n",
			cfg.BaseURL(), client.SaveDraftToDocumentPath(), client.AddDraftPayloadFor(pf.DocEntry),
			pf.Type.Kind.EntitySet, pf.DocEntry, pf.Action.label())
	}
	writeAddRecordLines(w)
}

// writeAddRecordLines says where this Add will be written down and who can read
// it. Same split as a delete: the record is shared, the contents are not.
func writeAddRecordLines(w io.Writer) {
	shared := config.SharedWriteLogPath()
	configured, cerr := config.WriteLogPath()
	root, _ := repoRootFunc()

	switch {
	case shared != "":
		fmt.Fprintf(w, "  record  : each Add is appended to %s and shared with the team.\n", shortPath(shared))
		if cerr == nil && configured != "" && configured != shared {
			fmt.Fprintf(w, "            (also to %s, which is where $SAPB1_WRITE_LOG points.)\n", shortPath(configured))
		}
	case cerr == nil && configured != "" && root != "" && withinCheckout(root, configured):
		fmt.Fprintf(w, "  record  : each Add is appended to %s, which is inside this checkout —\n", shortPath(configured))
		fmt.Fprintln(w, "            but no operator is registered here, so nothing files it under a name or")
		fmt.Fprintln(w, "            syncs it. Run `python3 harness/bin/setup.py` once if it should reach the team.")
	case cerr == nil && configured != "":
		fmt.Fprintf(w, "  record  : each Add is appended to %s, which is OUTSIDE any checkout —\n", shortPath(configured))
		fmt.Fprintln(w, "            the team will not see it. Run `python3 harness/bin/setup.py` in the JIVO")
		fmt.Fprintln(w, "            checkout (and leave $SAPB1_WRITE_LOG unset) if it should reach them.")
	}
	if p, err := config.SnapshotLogPath(); err == nil && p != "" {
		fmt.Fprintln(w, "  contents: exactly what was posted (party, bill number, totals, line prices) is kept in")
		fmt.Fprintf(w, "            %s on THIS machine only; the shared line carries just its sha256.\n", shortPath(p))
	}
}

// formatRupees renders an amount with Indian digit grouping — 12,45,310.00, not
// 1,245,310.00. Two decimals always: this figure sits directly above a prompt
// that commits money, and "Rs 425250" reads like a different number than
// "Rs 4,25,250.00".
func formatRupees(v float64) string {
	neg := v < 0
	if neg {
		v = -v
	}
	whole := int64(v)
	frac := int64((v-float64(whole))*100 + 0.5)
	if frac >= 100 { // rounding carried
		whole++
		frac -= 100
	}

	digits := strconv.FormatInt(whole, 10)
	var grouped string
	switch {
	case len(digits) <= 3:
		grouped = digits
	default:
		// Last three digits, then pairs, which is how Indian grouping works.
		grouped = digits[len(digits)-3:]
		rest := digits[:len(digits)-3]
		for len(rest) > 2 {
			grouped = rest[len(rest)-2:] + "," + grouped
			rest = rest[:len(rest)-2]
		}
		if rest != "" {
			grouped = rest + "," + grouped
		}
	}
	out := fmt.Sprintf("%s.%02d", grouped, frac)
	if neg {
		out = "-" + out
	}
	return out
}

// ---------------------------------------------------------------------------
// GUARDS. In execution order. None of them has an override flag.
// ---------------------------------------------------------------------------

// checkAddOpen is GUARD 4, and it is the single most important line in this
// command.
//
// A draft that is no longer Open has, in the ordinary case, ALREADY BEEN ADDED —
// the closed draft row is the trail behind a real document. Adding it a second
// time is a duplicate A/P invoice on the vendor's ledger and in the GST return.
//
// `delete` has a --closed flag for the same condition, and copying it here would
// be a catastrophe wearing a familiar name. On a delete, --closed says "a person
// closed this off as junk and I still want it gone", which costs somebody their
// typing. On an Add the identical flag means "post this draft a SECOND time".
// There is no flag, there is no override, and draftProblem.Flag is left EMPTY on
// purpose so the --json stream's suggestedFlags comes out empty and no agent can
// synthesise one from the record.
//
// It also INVERTS delete's absent-field convention. delete.go treats a missing
// DocumentStatus as "this check does not apply" — correct there, because OPDF
// genuinely has none. Drafts/ODRF ALWAYS carries one. If it is missing here,
// something answered that is not an ODRF row, and we are one step from an
// irreversible post. ABSENT REFUSES.
func checkAddOpen(pf *addPreflight, cfg *config.Config) {
	raw, present := pf.Obj["DocumentStatus"]
	if !present || raw == nil {
		pf.Problems = append(pf.Problems, draftProblem{
			Guard: "open",
			Msg: fmt.Sprintf(
				"refusing to add %s(%d) in %s: the row carries no DocumentStatus.\n"+
					"  Every document draft (ODRF) has one, so whatever answered is not a draft row. Unlike `delete`, a missing field here is not \"the check does not apply\" — it is the one check that stops this command adding an already-added draft a second time, and it could not run.\n"+
					"  Check what is answering for SAP on %s:%d (a bridge, a tunnel or a proxy in front of the Service Layer), then re-run.",
				kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, cfg.Host, cfg.Port),
		})
		return
	}
	if pf.Status == "bost_Open" {
		return
	}
	pf.Problems = append(pf.Problems, draftProblem{
		Guard: "open",
		// NO FLAG. Deliberately empty — see this function's doc comment.
		Msg: fmt.Sprintf(
			"refusing to add %s(%d) in %s: DocumentStatus is %s, not bost_Open.\n"+
				"  A closed draft has almost always been Added already — the draft row is the trail behind a real document. Adding it again would create a SECOND %s on the vendor's ledger and in the GST return.\n"+
				"  There is no flag for this, by design. Open %s in the SAP B1 client and find out what this draft became before doing anything else.",
			kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, describeStatus(pf.Status),
			pf.Type.Noun, kindAddDraft.WhereInSAP),
	})
}

// checkAddApproval is GUARD 5, a TWO-VALUE gate.
//
// dasWithout PROCEEDS: a draft no template has touched is what click one acts
// on, and a freshly API-made draft reads exactly that (approval starts only at
// Add).
//
// dasApproved ALSO PROCEEDS, and this is the part somebody will eventually try
// to "fix" in the wrong direction. An approved draft is still a draft: the
// approver said yes, and a human then has to press Add a SECOND time to put it
// in the books. Counted live 2026-08-24, Oil was holding 78 such drafts worth Rs
// 87.55 lakh with dasGenerated at zero — nothing posts itself on approval. If you
// remove this branch, you delete the larger half of the job, and the half where
// a second person has already reviewed the document.
//
// Everything else refuses, with no override:
//   - dasPending is in somebody's queue RIGHT NOW. Re-submitting takes the
//     request out from under them.
//   - dasRejected is a person's decision. Adding it overrides them silently.
//   - dasGenerated means SAP already produced the document.
//   - ABSENT refuses, for the same reason guard 4's absent field does: ODRF
//     carries this field, so a row without one is not a draft row.
func checkAddApproval(pf *addPreflight, cfg *config.Config) {
	raw, present := pf.Obj["AuthorizationStatus"]
	if !present || raw == nil {
		pf.Problems = append(pf.Problems, draftProblem{
			Guard: "approval",
			Msg: fmt.Sprintf(
				"refusing to add %s(%d) in %s: the row carries no AuthorizationStatus.\n"+
					"  Without it there is no way to tell whether Adding this submits it for approval or posts it straight into the books — two completely different consequences. A document draft always carries one, so whatever answered is not a draft row.\n"+
					"  Check what is answering for SAP on %s:%d, then re-run.",
				kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, cfg.Host, cfg.Port),
		})
		return
	}

	switch pf.Approval {
	case approvalFree:
		pf.Action = actionSubmit
		return
	case approvalApproved:
		pf.Action = actionPost
		return
	}

	pf.Problems = append(pf.Problems, draftProblem{
		Guard: "approval",
		// NO FLAG, same reasoning as guard 4: an approval status is a fact about
		// what a second person is doing, and an operator cannot assert past it.
		Msg: fmt.Sprintf(
			"refusing to add %s(%d) in %s: AuthorizationStatus is %s.\n"+
				"  %s\n"+
				"  add-draft acts on two states and no others: dasWithout (submits it for approval) and dasApproved (posts it, because the approval has already been given). There is no flag for the rest, by design.",
			kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, pf.Approval, approvalRefusalReason(pf.Approval)),
	})
}

// approvalRefusalReason says what the state MEANS, in the words that make an
// operator go and talk to the right person instead of looking for a flag.
func approvalRefusalReason(status string) string {
	switch status {
	case "dasPending":
		return "Somebody has this in their Approval Status Report right now. Adding it again raises a SECOND request and takes the first out from under them — ask them to approve it, then run add-draft again and it will post."
	case "dasRejected":
		return "Somebody looked at this and said no. Adding it would override a person's decision without telling them. If it should go through after all, that is a conversation and then a fresh draft."
	case "dasGenerated":
		return "SAP has already generated the document from this draft — there is nothing left to add."
	default:
		return "That is not a state this command knows how to act on. Look at the draft in the SAP B1 client and see who is holding it."
	}
}

// checkAddLineIntegrity is GUARD 6a: the draft's lines must be consistently
// based, or consistently not.
//
// A draft with SOME lines drawn from a base document and some keyed free-hand is
// not a shape this command can check: guard 6b can only speak for the lines that
// name a base, and the ones that do not would ride along unexamined into a live
// document. It is also, in practice, a draft somebody edited by hand halfway
// through — worth a person's eyes either way.
func checkAddLineIntegrity(pf *addPreflight, cfg *config.Config) {
	rows, _ := pf.Obj["DocumentLines"].([]interface{})
	if len(rows) == 0 {
		pf.Problems = append(pf.Problems, draftProblem{
			Guard: "lines",
			Msg: fmt.Sprintf(
				"refusing to add %s(%d) in %s: it has no DocumentLines.\n"+
					"  A %s with no lines is not a document; adding it would post an empty invoice against %s. Open it in %s and look.",
				kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, pf.Type.Noun,
				blankAs(formatCell(pf.Obj["CardCode"]), "the vendor"), kindAddDraft.WhereInSAP),
		})
		return
	}

	based, free := 0, 0
	for _, r := range rows {
		row, ok := r.(map[string]interface{})
		if !ok {
			continue
		}
		if n, ok := numberValue(row["BaseEntry"]); ok && n > 0 {
			based++
			continue
		}
		free++
	}
	if based > 0 && free > 0 {
		pf.Problems = append(pf.Problems, draftProblem{
			Guard: "lines",
			Msg: fmt.Sprintf(
				"refusing to add %s(%d) in %s: %d of its %d lines are drawn from a base document and %d are not.\n"+
					"  This command checks that the base document's lines are still open before it posts (a colleague invoicing them first is what makes Add fail), and it can only do that for lines that name a base. A mixed draft would carry the unchecked ones into a live document.\n"+
					"  A half-based draft is usually one somebody edited by hand. Open it in %s and look.",
				kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, based, len(rows), free, kindAddDraft.WhereInSAP),
		})
	}
}

// checkAddBaseLines is GUARD 6b, and it is the highest-value guard nobody asked
// for.
//
// Between a draft being made and being Added, somebody else can invoice the
// GRPO lines it draws on. When that happens SAP refuses the Add — which is the
// good case — but it refuses it AFTER the request has gone out, which is one
// more opportunity for exit 7 on the one command where exit 7 costs a person an
// afternoon in the SAP client. acc/apbatch's readback already knows this shape;
// turning a would-fail POST into a pre-flight refusal is worth more here than
// anywhere else in this codebase.
//
// Base documents are cached across the batch: nine drafts off one GRPO read it
// once.
func checkAddBaseLines(cmd *cobra.Command, c *client.Client, cfg *config.Config, pf *addPreflight, cache map[int64]map[string]interface{}) error {
	if pf.Type.BaseEntitySet == "" {
		return nil // this doctype draws on nothing; the guard does not apply
	}
	rows, _ := pf.Obj["DocumentLines"].([]interface{})

	// BaseEntry -> the BaseLines this draft consumes, in order.
	order := []int64{}
	consumed := map[int64][]int64{}
	for _, r := range rows {
		row, ok := r.(map[string]interface{})
		if !ok {
			continue
		}
		baseEntry, ok := numberValue(row["BaseEntry"])
		if !ok || baseEntry <= 0 {
			continue
		}
		// The base TYPE must be the one this doctype's table names. Without this
		// a draft drawn from a purchase ORDER would be checked against the
		// PurchaseDeliveryNote that happens to share its DocEntry — a different
		// document, read with total confidence.
		if bt, ok := numberValue(row["BaseType"]); !ok || bt != pf.Type.BaseObjectType {
			pf.Problems = append(pf.Problems, draftProblem{
				Guard: "base-lines",
				Msg: fmt.Sprintf(
					"refusing to add %s(%d) in %s: line %s is drawn from base type %s, and this command only knows how to check %s (ObjType %s) for a %s.\n"+
						"  It will not read a different document by the same DocEntry and call that a check. Add this one in the SAP B1 client, or add its base type to the doctype table with its own evidence.",
					kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, formatCell(row["LineNum"]),
					blankAs(formatCell(row["BaseType"]), "(none)"), pf.Type.BaseNoun,
					formatCell(pf.Type.BaseObjectType), pf.Type.Noun),
			})
			return nil
		}
		key := int64(baseEntry)
		if _, seen := consumed[key]; !seen {
			order = append(order, key)
		}
		baseLine, _ := numberValue(row["BaseLine"])
		consumed[key] = append(consumed[key], int64(baseLine))
	}

	for _, baseEntry := range order {
		base, ok := cache[baseEntry]
		if !ok {
			res, err := c.GetEntity(cmd.Context(), pf.Type.BaseEntitySet, baseEntry)
			if err != nil {
				return err
			}
			if !res.Found {
				pf.Problems = append(pf.Problems, draftProblem{
					Guard: "base-lines",
					Msg: fmt.Sprintf(
						"refusing to add %s(%d) in %s: the %s it is based on, %s(%d), does not exist.\n"+
							"  Nothing here can tell whether its lines are still open, and adding a draft whose base document has gone is how a duplicate gets in. Look at it in the SAP B1 client.",
						kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, pf.Type.BaseNoun,
						pf.Type.BaseEntitySet, baseEntry),
				})
				return nil
			}
			base = decodeWriteObject(res.Body)
			baseKind := draftKind{EntitySet: pf.Type.BaseEntitySet, Noun: pf.Type.BaseNoun, WhereInSAP: "the SAP B1 client"}
			if err := requireRequestedRow(cfg, baseKind, baseEntry, res.Status, res.Body, base); err != nil {
				return err
			}
			cache[baseEntry] = base
		}

		ref := addBaseRef{
			EntitySet: pf.Type.BaseEntitySet,
			DocEntry:  baseEntry,
			Lines:     consumed[baseEntry],
			DocNum:    formatCell(base["DocNum"]),
			OK:        true,
		}
		baseRows, _ := base["DocumentLines"].([]interface{})
		byLineNum := map[int64]map[string]interface{}{}
		for _, r := range baseRows {
			row, ok := r.(map[string]interface{})
			if !ok {
				continue
			}
			if n, ok := numberValue(row["LineNum"]); ok {
				byLineNum[int64(n)] = row
			}
		}

		var closed []string
		for _, lineNum := range consumed[baseEntry] {
			row, found := byLineNum[lineNum]
			if !found {
				closed = append(closed, fmt.Sprintf("line %d is not on that %s at all", lineNum, pf.Type.BaseNoun))
				continue
			}
			if status := formatCell(row["LineStatus"]); status != "bost_Open" {
				closed = append(closed, fmt.Sprintf("line %d is %s", lineNum, describeStatus(status)))
			}
		}
		if len(closed) > 0 {
			ref.OK = false
			ref.Note = strings.Join(closed, "; ")
			pf.Problems = append(pf.Problems, draftProblem{
				Guard: "base-lines",
				Msg: fmt.Sprintf(
					"refusing to add %s(%d) in %s: the %s it draws on (%s(%d), DocNum %s) no longer has all those lines open — %s.\n"+
						"  Somebody has invoiced them since this draft was made. SAP would refuse the Add anyway; refusing here means the request never goes out, so there is no \"did it post?\" to resolve afterwards.\n"+
						"  Check who invoiced that %s, and whether this draft is now a duplicate.",
					kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB, pf.Type.BaseNoun,
					pf.Type.BaseEntitySet, baseEntry, blankAs(ref.DocNum, "?"), ref.Note, pf.Type.BaseNoun),
			})
		}
		pf.Bases = append(pf.Bases, ref)
	}
	return nil
}

// describeAddTDS reads what the operator would tick in the SAP client and puts
// it directly above the prompt. IT NEVER REFUSES, AND IT NEVER PATCHES.
//
// RULING, and it is settled — do not turn any of this into a guard:
//
//   - "vendor is liable but WTAmount is 0" is the NORMAL, CORRECT outcome for a
//     large class of JIVO's vendors. TPAC is boYES with 194Q code 1031, and all
//     three of its last posted invoices carry WTAmount 0: Accounts does not
//     withhold from it. Precedent beats the master flag, and a refusal here would
//     fire on most of a legitimate batch.
//   - "every line says tYES but SAP computed nothing" is confusing, and JIVO
//     posts it anyway: VENDA000636 has three POSTED invoices in exactly that
//     shape. It gets a non-blocking line (the C-0018 shape), not a refusal.
//   - patch-then-post is refused for three separate reasons, any one sufficient:
//     it would re-decide a business question the operator already answered
//     upstream in the sheet; it would put two writes with a window between them
//     on an irreversible path; and it would break the field diff by
//     construction, because the bytes posted would no longer be the bytes
//     previewed.
//
// So: display always, refuse never, patch never. What replaces the TDS guard the
// brief was reaching for is guard 6b, which is mechanically decidable.
func describeAddTDS(cmd *cobra.Command, c *client.Client, pf *addPreflight, cache map[string]map[string]interface{}) error {
	note := addTDSNote{VendorCardCode: formatCell(pf.Obj["CardCode"])}
	note.HeaderAmount, _ = numberValue(pf.Obj["WTAmount"])

	rows, _ := pf.Obj["DocumentLines"].([]interface{})
	for _, r := range rows {
		row, ok := r.(map[string]interface{})
		if !ok {
			continue
		}
		note.TotalLines++
		if formatCell(row["WTLiable"]) == "tYES" {
			note.LiableLines++
		}
	}
	note.Contradiction = note.TotalLines > 0 && note.LiableLines == note.TotalLines && note.HeaderAmount == 0

	if note.VendorCardCode != "" {
		vendor, ok := cache[note.VendorCardCode]
		if !ok {
			// One row per distinct vendor per batch. No $select: the withholding
			// codes live in a nested collection, and asking for a projection that
			// may not include it would mean guessing at a field list. A read that
			// happens once per vendor can afford the whole row.
			res, err := c.Query(cmd.Context(), "BusinessPartners", client.QueryOptions{
				Filter: fmt.Sprintf("CardCode eq '%s'", odataQuote(note.VendorCardCode)),
				Top:    2,
			})
			if err != nil {
				return err
			}
			if len(res.Value) == 1 {
				vendor = res.Value[0]
			}
			cache[note.VendorCardCode] = vendor
		}
		if vendor != nil {
			note.VendorLiable = formatCell(vendor["SubjectToWithholdingTax"])
			note.VendorCodes = withholdingCodes(vendor)
		}
	}

	pf.TDS = note
	return nil
}

// withholdingCodes reads the vendor's withholding-tax codes off the row SAP
// actually returned. Nothing is requested by name: if the collection is not
// there, no codes are printed, rather than a guessed field appearing blank next
// to a confident label.
func withholdingCodes(vendor map[string]interface{}) []string {
	rows, ok := vendor["BPWithholdingTax"].([]interface{})
	if !ok {
		return nil
	}
	var out []string
	for _, r := range rows {
		row, ok := r.(map[string]interface{})
		if !ok {
			continue
		}
		if code := formatCell(row["WTCode"]); code != "" {
			out = append(out, code)
		}
	}
	return out
}

// odataQuote escapes a string literal for an OData $filter, where a single quote
// is written by doubling it. The value here is a CardCode read back off SAP's
// own row, but escaping it is not optional: this string is concatenated into a
// filter, and "escape it where you build it" is the only version of that rule
// that survives the next person copying this line.
func odataQuote(s string) string {
	return strings.ReplaceAll(s, "'", "''")
}

// noteAddProvenance records what the write logs say about where this draft came
// from. RENDER-ONLY — it can never refuse.
//
// `delete` refuses by default on this, and copying that here would be fatal:
// Neetu pre-keys A/P drafts in the SAP client, so a HAND-KEYED draft is the
// NORMAL INPUT to this command. Every one of them would refuse, the operator
// would reach for the override reflexively, and on delete that same override
// also silently disables the clock-skew and CreationDate anti-tamper checks. Net
// reduction in safety, so there is no such flag here at all.
//
// The one addition, precisely because there is no override to disable them: when
// the vouching log line disagrees with SAP, the summary says "cannot be
// confirmed" rather than a reassuring "yes".
func noteAddProvenance(cfg *config.Config, pf *addPreflight, idx map[originKey]draftOrigin) {
	origin, found := idx[originKey{EntitySet: kindAddDraft.EntitySet, CompanyDB: cfg.CompanyDB, DocEntry: pf.DocEntry}]
	if !found {
		return
	}
	if bad, why := untrustworthyOriginTime(origin); bad {
		pf.OriginDoubt = fmt.Sprintf("cannot be confirmed — the write-log line vouching for it %s (%s:%d)",
			why, shortPath(origin.File), origin.Line)
		return
	}
	if sapDate, claimed, contradicts := creationDateContradicts(pf.Obj, origin); contradicts {
		pf.OriginDoubt = fmt.Sprintf("cannot be confirmed — the write log says %s, SAP says the row was created %s (%s:%d)",
			claimed, sapDate, shortPath(origin.File), origin.Line)
		return
	}
	pf.Origin = &origin
}

// ---------------------------------------------------------------------------
// WHAT THE OPERATOR READS
// ---------------------------------------------------------------------------

// writeAddSummary prints what is about to be added.
//
// Not writeDraftSummary. That one ends in "created here: NO — no write log shows
// this CLI creating it", which is a refusal-flavoured sentence about something
// that is NOT a guard here — and it has no idea about the action, the base
// document or the TDS, which are the three things an operator actually checks
// before pressing Add.
func writeAddSummary(w io.Writer, cfg *config.Config, pf addPreflight) {
	fmt.Fprintf(w, "%s(%d) in %s\n", kindAddDraft.EntitySet, pf.DocEntry, cfg.CompanyDB)
	if pf.Obj == nil {
		fmt.Fprintf(w, "  %-20s: %s\n", "status", "not found")
		return
	}
	for _, f := range pf.Type.Kind.SummaryFields {
		raw, ok := pf.Obj[f]
		if !ok || raw == nil {
			continue
		}
		fmt.Fprintf(w, "  %-20s: %s\n", f, trimSAPDate(formatCell(raw)))
	}

	// The action line, and it is the most important line in the summary: two
	// drafts that look identical above it can have completely different
	// consequences below it.
	if len(pf.Problems) == 0 {
		for _, line := range addActionLines(pf) {
			fmt.Fprintf(w, "  %-20s: %s\n", "WILL", line)
		}
	}

	for _, b := range pf.Bases {
		fmt.Fprintf(w, "  %-20s: %s(%d) DocNum %s — %s\n", "based on", b.EntitySet, b.DocEntry,
			blankAs(b.DocNum, "?"), b.describe())
	}

	for _, line := range addTDSLines(pf.TDS) {
		fmt.Fprintf(w, "  %-20s: %s\n", "TDS", line)
	}

	fmt.Fprintf(w, "  %-20s: %s\n", "attachment", addAttachmentLine(pf))
	fmt.Fprintf(w, "  %-20s: %s\n", "created here", addCreatedHereLine(cfg, pf))
}

// addActionLines says which of the two clicks this is and what it does. The
// dasApproved case names the approval if the row carries one, and says plainly
// that it does not when it does not — a blank next to a confident label is worse
// than the admission.
func addActionLines(pf addPreflight) []string {
	if pf.Action.goesLive() {
		lines := []string{
			fmt.Sprintf("POST LIVE — Rs %s enters the books. Stock and %s's ledger move. Only SAP can reverse it.",
				formatRupees(pf.Total), blankAs(formatCell(pf.Obj["CardCode"]), "the vendor")),
		}
		if detail := approvalDetail(pf.Obj); detail != "" {
			lines = append(lines, "already approved — "+detail)
		} else {
			lines = append(lines, "already approved (the approver is not shown on this row; the Approval Status Report has it)")
		}
		return lines
	}
	return []string{
		"be SUBMITTED FOR APPROVAL — it goes to somebody's Approval Status Report and nothing enters the ledger.",
		"post LIVE instead if no approval template matches this document. add-draft reads the row back and tells you which happened.",
	}
}

// approvalDetail reports what the row ITSELF says about the approval, and
// nothing more.
//
// Deliberately data-driven rather than a list of field names somebody thinks
// ought to exist: it walks the keys SAP actually returned. A guessed $select
// would either fail or print an empty value next to a confident label, and on
// this command an operator reading "approved by:" with nothing after it is worse
// than reading that we cannot see who.
func approvalDetail(obj map[string]interface{}) string {
	var keys []string
	for k := range obj {
		if k == "AuthorizationStatus" || !strings.Contains(k, "Approv") {
			continue
		}
		keys = append(keys, k)
	}
	sort.Strings(keys)

	var parts []string
	for _, k := range keys {
		v := obj[k]
		if v == nil {
			continue
		}
		s := trimSAPDate(formatCell(v))
		if s == "" || s == "0" || s == "null" || s == "[]" || s == "{}" {
			continue
		}
		if len(s) > 60 {
			continue // a whole nested collection is not a summary line
		}
		parts = append(parts, k+" "+s)
		if len(parts) == 3 {
			break
		}
	}
	return strings.Join(parts, ", ")
}

func (b addBaseRef) describe() string {
	what := fmt.Sprintf("%d line(s) consumed", len(b.Lines))
	if b.OK {
		return what + ", all still open"
	}
	return what + "; " + b.Note
}

// addTDSLines renders the withholding-tax picture. Always printed, never a
// refusal — see describeAddTDS for the ruling.
func addTDSLines(n addTDSNote) []string {
	if n.TotalLines == 0 {
		return nil
	}
	first := fmt.Sprintf("Rs %s — %d of %d lines WTLiable tYES", formatRupees(n.HeaderAmount), n.LiableLines, n.TotalLines)
	if n.Contradiction {
		first = fmt.Sprintf("Rs %s — but %d of %d lines are WTLiable tYES. SAP computed nothing on them (the C-0018 shape). Check before adding.",
			formatRupees(n.HeaderAmount), n.LiableLines, n.TotalLines)
	}
	lines := []string{first}
	if n.VendorLiable != "" {
		vendor := fmt.Sprintf("vendor %s is SubjectToWithholdingTax %s", n.VendorCardCode, n.VendorLiable)
		if len(n.VendorCodes) > 0 {
			vendor += fmt.Sprintf(" (codes %s)", strings.Join(n.VendorCodes, ", "))
		}
		lines = append(lines, vendor)
	}
	return lines
}

// addAttachmentLine inverts delete's reading of the same field, and says so.
//
// On a delete an attachment is the signal that a person did work on the row, so
// its PRESENCE is the anomaly. For an A/P invoice the attachment IS the vendor's
// bill, so its ABSENCE is. It is not a guard either way: service invoices (fuel,
// courier) routinely have none, and refusing them would refuse a normal batch.
func addAttachmentLine(pf addPreflight) string {
	raw, ok := pf.Obj["AttachmentEntry"]
	if !ok || raw == nil || formatCell(raw) == "0" {
		return "none — the vendor's bill is not attached to this draft"
	}
	return fmt.Sprintf("AttachmentEntry %s", formatCell(raw))
}

// addCreatedHereLine renders provenance. Informational: the words are chosen so
// nobody reads them as a verdict on whether the Add may proceed.
func addCreatedHereLine(cfg *config.Config, pf addPreflight) string {
	switch {
	case pf.OriginDoubt != "":
		return pf.OriginDoubt
	case pf.Origin == nil:
		return "no write log shows this CLI creating it — normal for a draft keyed in the SAP client, and not a problem here"
	case !strings.EqualFold(pf.Origin.User, cfg.User):
		return fmt.Sprintf("yes — created by %s, not you, at %s (%s:%d)",
			pf.Origin.User, pf.Origin.Time.Local().Format("2006-01-02 15:04"), shortPath(pf.Origin.File), pf.Origin.Line)
	default:
		return fmt.Sprintf("yes — POST %s by %s at %s (%s:%d)", kindAddDraft.EntitySet, pf.Origin.User,
			pf.Origin.Time.Local().Format("2006-01-02 15:04"), shortPath(pf.Origin.File), pf.Origin.Line)
	}
}

// ---------------------------------------------------------------------------
// THE JSON STREAM
// ---------------------------------------------------------------------------

// addOutcome is one draft's result, in a shape both renderers read.
//
// NOT deleteOutcome. That struct has no field for what a draft BECAME, and
// adding one would change the JSON shape of every delete record — which
// acc/apbatch reads. Two commands, two record shapes, no coupling.
type addOutcome struct {
	DryRun        bool
	DocEntry      int64
	EntitySet     string
	DocObjectCode string
	CompanyDB     string
	Host          string
	Port          int
	Method        string
	URL           string
	Payload       json.RawMessage
	Action        string
	Status        int
	// Outcome is the classification from the read-back, never from the response
	// body: "approval-requested", "posted", "no-change", "unverified".
	Outcome             string
	Verified            bool
	VerifyNote          string
	DocumentStatus      string
	AuthorizationStatus string
	// Became* names the document the draft turned into, and is set only when
	// exactly one candidate was found. Zero or several is reported in
	// VerifyNote and never guessed at.
	BecameEntitySet string
	BecameDocEntry  int64
	BecameDocNum    string
	BecameTotal     float64
	CreatedHere     bool
	Origin          *draftOrigin
	Snapshot        json.RawMessage
	Error           string
	Skipped         string
	// Refused and Reason make an exit 9 machine-readable. SuggestedFlags is
	// always empty on this command and is emitted anyway — see writeAddJSONLine.
	Refused []string
	Reason  string
}

// writeAddJSONLine emits one compact JSON object per draft (JSONL).
//
// Two deliberate differences from delete's record:
//
//   - "suggestedFlags" is ALWAYS present and ALWAYS empty. add-draft has no
//     override flags, and an empty array says that positively to a caller that
//     is looking for one. Omitting the key would let a machine conclude the
//     field simply was not populated and go looking for a flag to pass; an empty
//     array tells it there is none to find. Nothing may ever put a value here —
//     on guard 4 a suggested flag would be a double-post button.
//   - the snapshot CONTENTS are never emitted, only the hash. A delete publishes
//     them on the one record of a draft it destroyed, because that is the only
//     copy left. Here the draft still exists in SAP after the Add (it closes, it
//     does not vanish), so there is nothing to preserve and every reason not to
//     print a vendor's bill into a log or a CI transcript.
func writeAddJSONLine(out io.Writer, o addOutcome) error {
	rec := struct {
		DryRun              bool            `json:"dryRun,omitempty"`
		DocEntry            int64           `json:"docEntry"`
		EntitySet           string          `json:"entitySet"`
		DocObjectCode       string          `json:"docObjectCode,omitempty"`
		CompanyDB           string          `json:"companyDb"`
		Host                string          `json:"host,omitempty"`
		Port                int             `json:"port,omitempty"`
		Method              string          `json:"method,omitempty"`
		URL                 string          `json:"url,omitempty"`
		Payload             json.RawMessage `json:"payload,omitempty"`
		Action              string          `json:"action,omitempty"`
		Status              int             `json:"status,omitempty"`
		Outcome             string          `json:"outcome,omitempty"`
		Verified            bool            `json:"verified"`
		VerifyNote          string          `json:"verifyNote,omitempty"`
		DocumentStatus      string          `json:"documentStatus,omitempty"`
		AuthorizationStatus string          `json:"authorizationStatus,omitempty"`
		BecameEntitySet     string          `json:"becameEntitySet,omitempty"`
		BecameDocEntry      int64           `json:"becameDocEntry,omitempty"`
		BecameDocNum        string          `json:"becameDocNum,omitempty"`
		BecameTotal         float64         `json:"becameTotal,omitempty"`
		CreatedHere         bool            `json:"createdHere"`
		Origin              *originJSON     `json:"origin,omitempty"`
		Skipped             string          `json:"skipped,omitempty"`
		Error               string          `json:"error,omitempty"`
		Refused             []string        `json:"refused,omitempty"`
		Reason              string          `json:"reason,omitempty"`
		SuggestedFlags      []string        `json:"suggestedFlags"`
		SnapshotSHA256      string          `json:"snapshotSha256,omitempty"`
	}{
		DryRun:              o.DryRun,
		DocEntry:            o.DocEntry,
		EntitySet:           o.EntitySet,
		DocObjectCode:       o.DocObjectCode,
		CompanyDB:           o.CompanyDB,
		Host:                o.Host,
		Port:                o.Port,
		Method:              o.Method,
		URL:                 o.URL,
		Payload:             o.Payload,
		Action:              o.Action,
		Status:              o.Status,
		Outcome:             o.Outcome,
		Verified:            o.Verified,
		VerifyNote:          o.VerifyNote,
		DocumentStatus:      o.DocumentStatus,
		AuthorizationStatus: o.AuthorizationStatus,
		BecameEntitySet:     o.BecameEntitySet,
		BecameDocEntry:      o.BecameDocEntry,
		BecameDocNum:        o.BecameDocNum,
		BecameTotal:         o.BecameTotal,
		CreatedHere:         o.CreatedHere,
		Origin:              toOriginJSON(o.Origin),
		Skipped:             o.Skipped,
		Error:               o.Error,
		Refused:             o.Refused,
		Reason:              o.Reason,
		SuggestedFlags:      []string{},
		SnapshotSHA256:      snapshotDigest(o.Snapshot),
	}
	b, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	_, err = fmt.Fprintln(out, string(b))
	return err
}

// baseAddOutcome fills the fields every record carries, whatever happened.
func baseAddOutcome(cfg *config.Config, pf addPreflight) addOutcome {
	return addOutcome{
		DocEntry:            pf.DocEntry,
		EntitySet:           kindAddDraft.EntitySet,
		DocObjectCode:       pf.Type.ObjectCode,
		CompanyDB:           cfg.CompanyDB,
		Host:                cfg.Host,
		Port:                cfg.Port,
		Method:              "POST",
		URL:                 cfg.BaseURL() + client.SaveDraftToDocumentPath(),
		Payload:             json.RawMessage(client.AddDraftPayloadFor(pf.DocEntry)),
		Action:              pf.Action.label(),
		DocumentStatus:      pf.Status,
		AuthorizationStatus: pf.Approval,
		CreatedHere:         pf.Origin != nil,
		Origin:              pf.Origin,
		Snapshot:            pf.Snapshot,
	}
}

// renderAddRefusedBatch writes one JSON record per DocEntry for a batch a guard
// stopped — the refused ones with their guards, the rest marked not attempted,
// so a caller can journal the whole list and see which one stopped it.
func renderAddRefusedBatch(out io.Writer, cfg *config.Config, pfs []addPreflight, dryRun bool) error {
	stopper := ""
	for _, pf := range pfs {
		if len(pf.Problems) > 0 {
			stopper = fmt.Sprintf("%s(%d)", kindAddDraft.EntitySet, pf.DocEntry)
			break
		}
	}
	for _, pf := range pfs {
		o := baseAddOutcome(cfg, pf)
		o.DryRun = dryRun
		if len(pf.Problems) > 0 {
			reasons := make([]string, 0, len(pf.Problems))
			for _, p := range pf.Problems {
				o.Refused = append(o.Refused, p.Guard)
				reasons = append(reasons, p.Msg)
			}
			o.Reason = strings.Join(reasons, "\n\n")
		} else {
			o.Skipped = fmt.Sprintf("not attempted — %s was refused", stopper)
		}
		if err := writeAddJSONLine(out, o); err != nil {
			return err
		}
	}
	return nil
}

// renderAddDryRun prints the POSTs that would go, and says clearly that this dry
// run — unlike draft/post/patch --dry-run — did read SAP.
//
// Not renderDeleteDryRun: different verb, different consequences, and a closing
// sentence that has to name what re-running without --dry-run would actually do
// to the books.
func renderAddDryRun(cmd *cobra.Command, cfg *config.Config, pfs []addPreflight) error {
	out := cmd.OutOrStdout()
	if cfg.JSON {
		for _, pf := range pfs {
			o := baseAddOutcome(cfg, pf)
			o.DryRun = true
			if err := writeAddJSONLine(out, o); err != nil {
				return err
			}
		}
		return nil
	}

	live, liveSum, pending, pendingSum := addTotals(pfs)
	fmt.Fprintf(out, "DRY RUN — read %d draft(s), ran every guard; no POST was sent.\n", len(pfs))
	fmt.Fprintf(out, "  company : %s\n", cfg.CompanyDB)
	for _, pf := range pfs {
		fmt.Fprintf(out, "  request : POST %s%s   %s   [%s(%d) — %s]\n",
			cfg.BaseURL(), client.SaveDraftToDocumentPath(), client.AddDraftPayloadFor(pf.DocEntry),
			kindAddDraft.EntitySet, pf.DocEntry, pf.Action.label())
	}
	if live > 0 {
		fmt.Fprintf(out, "  LIVE    : %d draft(s), Rs %s would be posted to the books.\n", live, formatRupees(liveSum))
	}
	if pending > 0 {
		fmt.Fprintf(out, "  approval: %d draft(s), Rs %s would be submitted for approval.\n", pending, formatRupees(pendingSum))
	}
	fmt.Fprintln(out, "Unlike draft/post/patch --dry-run, this one did contact SAP (to read the drafts and their base documents).")
	fmt.Fprintln(out, "Re-run the same command without --dry-run to send it. What is posted cannot be undone from this CLI.")
	return nil
}

// ---------------------------------------------------------------------------
// The send path.
//
// Everything above this line reads. Everything below it can make a document
// real, and the whole file is ordered that way on purpose: a reader who stops
// halfway has read the half that cannot hurt anybody.
//
// The governing difference from delete.go, which this borrows heavily from:
// a DELETE that is re-sent cannot destroy the draft twice, so delete's
// ergonomics are built to make re-running SAFE and easy. An Add that is
// re-sent CAN create a second live A/P invoice on a vendor's ledger and in a
// GST return. So every place delete says "just run it again", this must say
// the opposite, and say it in the operator's face rather than in a doc comment.
// ---------------------------------------------------------------------------

// addSequentially sends the batch one document at a time, stopping at the first
// trouble.
//
// FAIL-FAST IS NOT AN OPTIMISATION HERE. Once one Add has gone wrong, the
// operator's next job is to find out what happened to THAT document before any
// more become real — and if they are looking at an exit 7, they must do it
// before a second document can muddy the answer. So the remaining DocEntries
// are reported as "not attempted" rather than tried.
func addSequentially(cmd *cobra.Command, c *client.Client, cfg *config.Config, pfs []addPreflight) error {
	out := cmd.OutOrStdout()
	var posted, submitted, unverified, failed, notAttempted []int64
	var firstErr error
	stopper := ""

	for _, pf := range pfs {
		if firstErr != nil {
			notAttempted = append(notAttempted, pf.DocEntry)
			if cfg.JSON {
				o := baseAddOutcome(cfg, pf)
				o.Skipped = "not attempted — stopped after " + stopper
				// Best-effort: the batch is already stopping, and if stdout is the
				// thing that broke, failing again here would swap the report of what
				// happened for the write error.
				_ = writeAddJSONLine(out, o)
			}
			continue
		}

		outcome, err := addOne(cmd, c, cfg, pf)

		// Classified BEFORE it is rendered, so the tally is right even when the
		// record cannot be printed.
		switch {
		case err != nil && outcome.Status != 0:
			// SAP answered, and only the verification fell over. "failed" would be
			// a lie that costs money: an operator who reads it re-runs the Add and
			// duplicates a live invoice. This column exists to stop exactly that.
			unverified = append(unverified, pf.DocEntry)
			stopper = fmt.Sprintf("Drafts(%d) could not be verified", pf.DocEntry)
		case err != nil:
			failed = append(failed, pf.DocEntry)
			stopper = fmt.Sprintf("Drafts(%d) failed", pf.DocEntry)
		case outcome.Outcome == outcomePosted:
			posted = append(posted, pf.DocEntry)
		default:
			submitted = append(submitted, pf.DocEntry)
		}

		renderErr := renderAddOutcome(out, cfg.JSON, outcome)
		switch {
		case err != nil:
			firstErr = err
		case renderErr != nil:
			firstErr = addStreamStopped(pf.DocEntry, outcome, renderErr)
			stopper = fmt.Sprintf("Drafts(%d) could not be reported", pf.DocEntry)
		}
	}

	if firstErr == nil {
		return nil
	}
	if len(pfs) == 1 {
		return firstErr
	}
	return &addBatchError{
		Err: firstErr, Posted: posted, Submitted: submitted,
		Unverified: unverified, Failed: failed, NotAttempted: notAttempted,
	}
}

// The four values addOutcome.Outcome can take. Named constants because the tally,
// the renderer and the JSON stream all branch on them and a typo in any one of
// them would silently miscount a live document.
const (
	outcomeApprovalRequested = "approval-requested"
	outcomePosted            = "posted"
	outcomeNoChange          = "no-change"
	outcomeUnverified        = "unverified"
)

// addOne re-reads the draft, refuses if anything about it moved since the
// operator looked, sends the Add, and then works out from SAP what actually
// happened.
func addOne(cmd *cobra.Command, c *client.Client, cfg *config.Config, pf addPreflight) (addOutcome, error) {
	o := baseAddOutcome(cfg, pf)

	// --- GUARD 7, and the reason this command is safe to use --------------
	//
	// The operator read a summary and typed yes. Between those two moments a
	// colleague in the SAP client can edit this draft: change a line total,
	// swap the vendor's bill number, move the posting date into another GST
	// period. delete.go:1204 hits the same window and deliberately TOLERATES
	// it — it re-snapshots, because for a delete the freshest copy is the one
	// worth recording and the row dies either way.
	//
	// Here the opposite is required. What the operator approved was a
	// document, not a DocEntry. If the document changed, their yes was about
	// something that no longer exists.
	fresh, err := c.GetEntity(cmd.Context(), kindAddDraft.EntitySet, pf.DocEntry)
	if err != nil {
		return o, err
	}
	if !fresh.Found {
		// It was there at preflight and it is gone now. On delete this is a
		// skip; here it means somebody deleted or Added it in the last few
		// seconds, and either way this Add must not go out.
		return o, &errs.RefusedError{Msg: fmt.Sprintf(
			"Drafts(%d) was there when you looked and is not there now — somebody removed or Added it "+
				"in the SAP client while you were confirming. Nothing was sent. Look in %s before running this again.",
			pf.DocEntry, kindAddDraft.WhereInSAP)}
	}
	freshObj := decodeWriteObject(fresh.Body)
	if err := requireRequestedRow(cfg, kindAddDraft, pf.DocEntry, fresh.Status, fresh.Body, freshObj); err != nil {
		return o, err
	}

	// The DECISION is the digest: one comparison over an allowlist that is
	// already ordered, already deterministic and already tested. The MESSAGE
	// below is a second, separate walk that names what moved. If that walk
	// misses a field the digest still refuses — the human text may be
	// incomplete, the gate cannot be.
	freshSnap := snapshotOf(freshObj, kindAddDraft)
	if snapshotDigest(freshSnap) != snapshotDigest(pf.Snapshot) {
		return o, &errs.RefusedError{Msg: fmt.Sprintf(
			"Drafts(%d) has CHANGED since it was shown to you. Nothing was sent.\n\n%s\n\n"+
				"  What you approved at the prompt is not what is in SAP now. Run add-draft %d --dry-run,\n"+
				"  read it again, and confirm the new version if it is still right.",
			pf.DocEntry, indentLines(describeSnapshotDiff(pf.Snapshot, freshSnap), "  "), pf.DocEntry)}
	}

	// Belt and braces over the digest, purely so the operator gets the precise
	// sentence rather than a field list, in the two cases that matter most.
	if s := draftStatus(freshObj); s != "" && s != statusOpen {
		return o, &errs.RefusedError{Msg: fmt.Sprintf(
			"Drafts(%d) is %s now — somebody Added it in the SAP client while you were confirming. "+
				"Nothing was sent, and it must not be Added twice.", pf.DocEntry, describeStatus(s))}
	}
	if a := formatCell(freshObj["AuthorizationStatus"]); a != "" && a != pf.Approval {
		return o, &errs.RefusedError{Msg: fmt.Sprintf(
			"Drafts(%d) was %s when you looked and is %s now — its approval moved while you were confirming. "+
				"Nothing was sent.", pf.DocEntry, pf.Approval, a)}
	}
	o.Snapshot = freshSnap

	// --- the irreversible line -------------------------------------------
	res, err := c.SaveDraftToDocument(cmd.Context(), pf.DocEntry, client.AddDraftOptions{
		Snapshot: freshSnap,
		Origin:   toWriteOrigin(pf.Origin),
	})
	if res != nil {
		o.Status = res.Status
	}
	if err != nil {
		// Exit 7 is the worst state this command has, and it is the one place
		// where the generic advice is actively dangerous. Replace it with the
		// three-state lookup that settles it, because on THIS command the draft
		// row survives the Add and carries the answer itself.
		var unknown *errs.WriteOutcomeUnknownError
		if errors.As(err, &unknown) {
			o.Outcome = outcomeUnverified
			o.Error = unknown.Msg
			return o, &errs.WriteOutcomeUnknownError{
				Msg: unknownOutcomeRecovery(cfg, pf),
				Err: unknown,
			}
		}
		o.Error = err.Error()
		return o, addAPIHint(err)
	}

	// --- what actually happened, read from SAP, never from the reply ------
	return classifyAdd(cmd, c, cfg, pf, o, res)
}

// classifyAdd decides between the two outcomes by re-reading the draft.
//
// The response body is a BONUS and never a precondition: nobody has ever made
// this call succeed from this repo, so its shape is unknown and nothing here
// may depend on it. If SAP happens to name the document it created, that name
// is recorded; if it does not, the corroborating read below finds it, and if
// that is inconclusive the command says so instead of guessing.
func classifyAdd(cmd *cobra.Command, c *client.Client, cfg *config.Config, pf addPreflight, o addOutcome, res *client.WriteResult) (addOutcome, error) {
	if body := decodeWriteObject(res.Body); body != nil {
		if n, ok := int64Value(body["DocEntry"]); ok && n > 0 {
			o.BecameDocEntry = n
			o.BecameEntitySet = pf.Type.BecameEntitySet
		}
		if s := formatCell(body["DocNum"]); s != "" {
			o.BecameDocNum = s
		}
	}

	after, err := c.GetEntity(cmd.Context(), kindAddDraft.EntitySet, pf.DocEntry)
	if err != nil {
		// SAP took the Add — the POST returned 2xx — and only the verifying read
		// fell over. Exit 8. The cause is put in the MESSAGE and deliberately not
		// wrapped, so errors.As cannot reach a NetworkError through it and
		// conclude "nothing was sent". Same reasoning as delete.go:1240.
		o.Outcome = outcomeUnverified
		o.VerifyNote = "the read-back after the Add could not be made: " + err.Error()
		return o, &errs.WriteVerifyError{Msg: fmt.Sprintf(
			"Drafts(%d): SAP accepted the Add (HTTP %d) and the read-back afterwards failed: %v\n\n"+
				"  It went through. Do NOT run add-draft for %d again — go and look:\n"+
				"    %s\n",
			pf.DocEntry, o.Status, err, pf.DocEntry, draftLookupCmd(cfg, pf.DocEntry))}
	}

	if !after.Found {
		// The row did not survive. Unusual for this endpoint (an Added draft
		// normally closes rather than vanishing) but it unambiguously means the
		// Add took effect.
		o.Outcome = outcomePosted
		o.Verified = true
		o.VerifyNote = "the draft row no longer exists — the Add took effect"
		return corroborateAdd(cmd, c, cfg, pf, o)
	}

	afterObj := decodeWriteObject(after.Body)
	o.DocumentStatus = draftStatus(afterObj)
	o.AuthorizationStatus = formatCell(afterObj["AuthorizationStatus"])

	switch {
	// Only a TRANSITION counts. Comparing against the value captured immediately
	// before the send is what stops a draft somebody had already closed by hand
	// from reading as "we posted it" — DocumentStatus 'C' has more than one
	// cause, and this window is two seconds wide.
	case o.DocumentStatus != "" && o.DocumentStatus != pf.Status:
		o.Outcome = outcomePosted
		o.Verified = true
		return corroborateAdd(cmd, c, cfg, pf, o)

	case o.AuthorizationStatus != "" && o.AuthorizationStatus != pf.Approval:
		// The expected path for an Oil A/P draft: an approval template matched
		// and this is now a request in somebody's queue, not a ledger entry.
		o.Outcome = outcomeApprovalRequested
		o.Verified = true
		return o, nil

	default:
		// 2xx with nothing visibly different is NOT success. Say so.
		o.Outcome = outcomeNoChange
		o.VerifyNote = "SAP accepted the Add but the draft reads exactly as before"
		return o, &errs.WriteVerifyError{Msg: fmt.Sprintf(
			"Drafts(%d): SAP accepted the Add (HTTP %d) but the draft still reads %s / %s — nothing visibly changed.\n\n"+
				"  Do NOT run add-draft for %d again until you know why. Look in %s and in the Approval Status Report.",
			pf.DocEntry, o.Status, blankAs(o.DocumentStatus, "?"), blankAs(o.AuthorizationStatus, "?"),
			pf.DocEntry, kindAddDraft.WhereInSAP)}
	}
}

// corroborateAdd names the document the draft became.
//
// It matches on the doctype's own identity fields — for an A/P invoice a vendor
// plus their bill number, the same identity acc/apbatch's pre-check uses.
// Deliberately NOT draftKey: that column exists in HANA (OPCH.draftKey) and is
// not reachable over the Service Layer, so a verifier resting on it could not
// be built here at all.
//
// Exactly one match is a confirmation. Zero or several is reported as
// inconclusive — a "posted" verdict with no document named is still a true
// statement, and a guessed DocEntry is not.
func corroborateAdd(cmd *cobra.Command, c *client.Client, cfg *config.Config, pf addPreflight, o addOutcome) (addOutcome, error) {
	if pf.Type.BecameEntitySet == "" || len(pf.Type.BecameMatch) == 0 || o.BecameDocEntry != 0 {
		return o, nil
	}
	clauses := make([]string, 0, len(pf.Type.BecameMatch))
	for _, f := range pf.Type.BecameMatch {
		v := formatCell(pf.Obj[f])
		if v == "" {
			// One of the identifying fields is blank on the draft, so the filter
			// cannot identify anything. Better to say we did not look than to run
			// a query that matches half the ledger.
			o.VerifyNote = fmt.Sprintf("posted, but %s is blank on the draft so the document could not be looked up by name", f)
			return o, nil
		}
		clauses = append(clauses, fmt.Sprintf("%s eq '%s'", f, odataQuote(v)))
	}
	res, err := c.Query(cmd.Context(), pf.Type.BecameEntitySet, client.QueryOptions{
		Filter: strings.Join(clauses, " and "),
		Select: "DocEntry,DocNum,DocDate,DocTotal",
		Top:    5,
	})
	if err != nil {
		o.VerifyNote = "posted, but the document could not be looked up: " + err.Error()
		return o, nil
	}
	switch len(res.Value) {
	case 1:
		row := res.Value[0]
		o.BecameEntitySet = pf.Type.BecameEntitySet
		if n, ok := int64Value(row["DocEntry"]); ok {
			o.BecameDocEntry = n
		}
		o.BecameDocNum = formatCell(row["DocNum"])
		if f, ok := row["DocTotal"].(json.Number); ok {
			o.BecameTotal, _ = f.Float64()
		}
	case 0:
		o.VerifyNote = "posted, but no matching " + pf.Type.BecameEntitySet + " was found to name it"
	default:
		o.VerifyNote = fmt.Sprintf("posted, but %d %s rows match this vendor and bill number — not naming one of them",
			len(res.Value), pf.Type.BecameEntitySet)
	}
	return o, nil
}

// unknownOutcomeRecovery is the exit-7 message, and it is the most important
// text this command produces.
//
// The request went out and the answer never came back. The Add may or may not
// have happened, and the ONE reaction that must not follow is running the
// command again — on a DELETE that is harmless, here it duplicates a live A/P
// invoice on a vendor's ledger and in a GST return.
//
// What makes this recoverable rather than merely frightening is that the draft
// row survives the Add and carries the answer in two fields. So this does not
// say "go and look" in the abstract; it hands over the exact query and what
// each of the three possible replies means.
func unknownOutcomeRecovery(cfg *config.Config, pf addPreflight) string {
	var b strings.Builder
	fmt.Fprintf(&b, "Drafts(%d): the Add was SENT to %s and SAP's answer never arrived. It MAY have gone through.\n\n",
		pf.DocEntry, cfg.CompanyDB)
	fmt.Fprintf(&b, "  DO NOT re-run add-draft for %d. A second Add can create a duplicate %s\n",
		pf.DocEntry, pf.Type.Noun)
	if cc := formatCell(pf.Obj["CardCode"]); cc != "" {
		fmt.Fprintf(&b, "  on %s's ledger and in the GST return, and nothing here can undo one.\n\n", cc)
	} else {
		b.WriteString("  on the vendor's ledger and in the GST return, and nothing here can undo one.\n\n")
	}
	b.WriteString("  The draft itself settles it. Run:\n")
	fmt.Fprintf(&b, "    %s\n\n", draftLookupCmd(cfg, pf.DocEntry))
	b.WriteString("  and read the two fields:\n")
	fmt.Fprintf(&b, "    DocumentStatus %s and AuthorizationStatus %s  -> nothing happened. Safe to run add-draft %d again.\n",
		statusOpen, pf.Approval, pf.DocEntry)
	b.WriteString("    AuthorizationStatus dasPending                       -> it went through and is awaiting approval. Done. Do not re-run.\n")
	fmt.Fprintf(&b, "    DocumentStatus %s                              -> it went through and posted. Done. Do not re-run.\n", statusClosed)
	if pf.Type.BecameEntitySet != "" {
		fmt.Fprintf(&b, "\n  To name the posted document if it posted:\n    %s\n", becameLookupCmd(cfg, pf))
	}
	fmt.Fprintf(&b, "\n  Still unclear: SAP B1 client -> %s, and the Approval Status Report.\n", kindAddDraft.WhereInSAP)
	return b.String()
}

// draftLookupCmd is the runnable query that answers "what happened to it".
func draftLookupCmd(cfg *config.Config, docEntry int64) string {
	return fmt.Sprintf(
		"sapb1 query Drafts --filter \"DocEntry eq %d\" --select \"DocEntry,DocumentStatus,AuthorizationStatus\"%s",
		docEntry, companyFlag(cfg))
}

// becameLookupCmd is the runnable query that names the posted document.
func becameLookupCmd(cfg *config.Config, pf addPreflight) string {
	clauses := make([]string, 0, len(pf.Type.BecameMatch))
	for _, f := range pf.Type.BecameMatch {
		clauses = append(clauses, fmt.Sprintf("%s eq '%s'", f, odataQuote(formatCell(pf.Obj[f]))))
	}
	return fmt.Sprintf("sapb1 query %s --filter \"%s\" --select \"DocEntry,DocNum,DocTotal,DocDate\"%s",
		pf.Type.BecameEntitySet, strings.Join(clauses, " and "), companyFlag(cfg))
}

// companyFlag repeats --company only when it is not the configured default, so
// a paste-able command stays paste-able without teaching a habit of naming the
// wrong database.
func companyFlag(cfg *config.Config) string {
	if cfg.CompanyDB == "" {
		return ""
	}
	return " --company " + cfg.CompanyDB
}

// addAPIHint annotates the SAP errors whose raw text sends an operator in the
// wrong direction.
//
// -5002 [131-102] is the one most likely to greet the first live run: the
// approval-intercept path needs an attachments folder the Linux Service Layer
// must be able to see, and it has already killed the adjacent POST
// /PurchaseInvoices route once (jivo-ap-draft/reference/series-and-errors.md:47).
// It reads like a problem with the draft. It is not one, and NOTHING was posted.
func addAPIHint(err error) error {
	var apiErr *errs.APIError
	if !errors.As(err, &apiErr) {
		return err
	}
	if strings.Contains(apiErr.Msg, "Attachments folder") || strings.Contains(apiErr.Msg, "131-102") {
		apiErr.Msg += "\n\n  That is the attachments folder on the SAP server, not anything about your draft.\n" +
			"  NOTHING was posted. Do not retry — the CIFS mount for this company needs checking\n" +
			"  (see connections/ and the SAP box's fstab)."
	}
	return apiErr
}

// addBatchError is the tally for a batch that stopped partway.
//
// Its columns differ from delete's for a reason that is not cosmetic. A partial
// delete leaves an operator with drafts that still exist — they can look and
// re-run. A partial Add leaves LIVE DOCUMENTS, and the only question that
// matters is which ones. So "posted" and "submitted" are separate columns
// rather than one "done", because one of them moved money and the other did
// not, and "unverified" is its own column so that a document SAP accepted is
// never filed under "failed" — an operator who reads "failed" re-runs it.
type addBatchError struct {
	Err                                                 error
	Posted, Submitted, Unverified, Failed, NotAttempted []int64
}

func (b *addBatchError) Unwrap() error { return b.Err }

func (b *addBatchError) Error() string {
	var parts []string
	if len(b.Posted) > 0 {
		parts = append(parts, fmt.Sprintf("POSTED LIVE (%d): %s", len(b.Posted), joinEntries(b.Posted)))
	}
	if len(b.Submitted) > 0 {
		parts = append(parts, fmt.Sprintf("submitted for approval (%d): %s", len(b.Submitted), joinEntries(b.Submitted)))
	}
	if len(b.Unverified) > 0 {
		parts = append(parts, fmt.Sprintf("SENT, OUTCOME NOT CONFIRMED (%d): %s", len(b.Unverified), joinEntries(b.Unverified)))
	}
	if len(b.Failed) > 0 {
		parts = append(parts, fmt.Sprintf("failed (%d): %s", len(b.Failed), joinEntries(b.Failed)))
	}
	if len(b.NotAttempted) > 0 {
		parts = append(parts, fmt.Sprintf("not attempted (%d): %s", len(b.NotAttempted), joinEntries(b.NotAttempted)))
	}
	msg := b.Err.Error()
	if len(parts) > 0 {
		msg += "\n\n  " + strings.Join(parts, "\n  ")
	}
	if len(b.Posted) > 0 || len(b.Unverified) > 0 {
		msg += "\n\n  Documents above marked POSTED LIVE or SENT are real or may be real. Do not re-run\n" +
			"  add-draft for any of them — check each one before doing anything else."
	}
	return msg
}

// addStreamStopped is what a batch does when its own output cannot be written
// (`--json | head -1`, a closed pipe).
//
// Same exit code as delete's twin and the OPPOSITE advice: delete's says
// re-sending cannot double-delete. Re-sending this can double-post, so a
// command that has just made a document real and then could not hand over the
// receipt stops and says what it did.
func addStreamStopped(docEntry int64, o addOutcome, cause error) error {
	what := "was Added"
	if o.Outcome == outcomeApprovalRequested {
		what = "was submitted for approval"
	}
	return &errs.WriteVerifyError{Msg: fmt.Sprintf(
		"Drafts(%d) %s and the record of it could not be written: %v\n\n"+
			"  The Add HAPPENED. Do NOT re-run add-draft for it. Nothing after it was attempted.",
		docEntry, what, cause)}
}

// renderAddOutcome prints one result, as JSON or as the sentence an operator
// reads. The two outcomes are worded to be impossible to confuse: one of them
// moved money and the other explicitly did not.
func renderAddOutcome(out io.Writer, asJSON bool, o addOutcome) error {
	if asJSON {
		return writeAddJSONLine(out, o)
	}
	var b strings.Builder
	switch o.Outcome {
	case outcomeApprovalRequested:
		fmt.Fprintf(&b, "Drafts(%d) -> submitted for approval in %s.\n", o.DocEntry, o.CompanyDB)
		fmt.Fprintf(&b, "  AuthorizationStatus is now %s. It is in the Approval Status Report, not in the ledger.\n",
			blankAs(o.AuthorizationStatus, "?"))
		b.WriteString("  NOTHING was added to stock or to the vendor's account. It posts when the approver approves it.\n")
	case outcomePosted:
		fmt.Fprintf(&b, "Drafts(%d) -> ADDED in %s.\n", o.DocEntry, o.CompanyDB)
		switch {
		case o.BecameDocEntry != 0:
			fmt.Fprintf(&b, "  It is now %s DocEntry %d", blankAs(o.BecameEntitySet, "the posted document"), o.BecameDocEntry)
			if o.BecameDocNum != "" {
				fmt.Fprintf(&b, ", DocNum %s", o.BecameDocNum)
			}
			if o.BecameTotal != 0 {
				fmt.Fprintf(&b, ", %s", formatRupees(o.BecameTotal))
			}
			b.WriteString(".\n")
		case o.VerifyNote != "":
			fmt.Fprintf(&b, "  %s.\n", o.VerifyNote)
		}
		b.WriteString("  This is LIVE: stock and the vendor's ledger have moved. Only SAP can reverse it.\n")
	default:
		fmt.Fprintf(&b, "Drafts(%d) -> %s in %s.\n", o.DocEntry, blankAs(o.Outcome, "outcome unknown"), o.CompanyDB)
		if o.VerifyNote != "" {
			fmt.Fprintf(&b, "  %s.\n", o.VerifyNote)
		}
	}
	_, err := io.WriteString(out, b.String())
	return err
}

// statusOpen and statusClosed are DocumentStatus as SAP spells it. Named
// because this command branches on them in five places and a mistyped literal
// in any one of them would either refuse a good draft or, far worse, let an
// already-Added one through.
const (
	statusOpen   = "bost_Open"
	statusClosed = "bost_Close"
)

// int64Value pulls a whole number out of whatever SAP put in a field. Bodies are
// decoded with UseNumber, so a DocEntry arrives as json.Number, but a float or a
// string is accepted too rather than silently reading as zero.
func int64Value(v interface{}) (int64, bool) {
	switch n := v.(type) {
	case json.Number:
		i, err := n.Int64()
		return i, err == nil
	case float64:
		return int64(n), n == float64(int64(n))
	case string:
		i, err := strconv.ParseInt(strings.TrimSpace(n), 10, 64)
		return i, err == nil
	}
	return 0, false
}

// indentLines prefixes every line of s, so a multi-line diff sits under its
// heading instead of against the left margin.
func indentLines(s, prefix string) string {
	lines := strings.Split(strings.TrimRight(s, "\n"), "\n")
	for i, l := range lines {
		if l != "" {
			lines[i] = prefix + l
		}
	}
	return strings.Join(lines, "\n")
}

// describeSnapshotDiff names what moved between two snapshots of the same draft.
//
// THIS IS THE MESSAGE, NOT THE GATE. The refusal has already been decided by
// comparing digests over the whole allowlist; this walk exists only so the
// operator reads "DocTotal 1,20,000.00 -> 12,00,000.00" instead of "something
// changed". If it misses a field, the digest still refused — which is the right
// way round for a text-formatting function to fail.
func describeSnapshotDiff(before, after json.RawMessage) string {
	a, b := decodeSnapshot(before), decodeSnapshot(after)
	if a == nil || b == nil {
		return "The draft's contents differ from what you were shown."
	}
	var lines []string
	seen := map[string]bool{}
	for _, k := range sortedMapKeys(a) {
		seen[k] = true
		if av, bv := formatCell(a[k]), formatCell(b[k]); av != bv {
			lines = append(lines, fmt.Sprintf("%-24s %s  ->  %s", k, blankAs(av, "(blank)"), blankAs(bv, "(blank)")))
		}
	}
	for _, k := range sortedMapKeys(b) {
		if !seen[k] {
			lines = append(lines, fmt.Sprintf("%-24s %s  ->  %s", k, "(absent)", blankAs(formatCell(b[k]), "(blank)")))
		}
	}
	if len(lines) == 0 {
		// The digests differed but no top-level field did, so the change is inside
		// a line collection. Say that rather than printing nothing and looking
		// like a false alarm.
		return "A line on the draft changed. The header fields read the same, so compare the lines in " +
			kindAddDraft.WhereInSAP + "."
	}
	return strings.Join(lines, "\n")
}

// decodeSnapshot re-reads a snapshot into a map for diffing. A snapshot this
// process produced a moment ago always parses; a nil return simply degrades the
// message, never the refusal.
func decodeSnapshot(raw json.RawMessage) map[string]interface{} {
	if len(raw) == 0 {
		return nil
	}
	var m map[string]interface{}
	dec := json.NewDecoder(strings.NewReader(string(raw)))
	dec.UseNumber()
	if err := dec.Decode(&m); err != nil {
		return nil
	}
	return m
}

// sortedMapKeys orders an arbitrary decoded object's keys, so a diff reads the
// same way twice. delete.go's sortedKeys is typed to the line-collection map and
// cannot take this one.
func sortedMapKeys(m map[string]interface{}) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
