package cli

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// maxDeleteBatch caps one invocation. The batch tooling this exists for creates
// A/P invoice drafts fifty at a time, so fifty is the size of one mistake — and
// a cap means a fat-fingered shell glob cannot turn into a thousand deletes.
const maxDeleteBatch = 50

// maxDraftAge is how long after creation a delete still counts as cleaning up
// after a batch. Past it the operator has to name the age explicitly with
// --older-than: a draft that has survived a day has probably been looked at, or
// pre-keyed for somebody, and is no longer junk by default.
const maxDraftAge = 24 * time.Hour

// docEntryRe is the only shape a DocEntry argument may take: a positive whole
// number, no sign, no leading zero, no decimal point. Ten digits is the outer
// bound before ParseInt checks it against SAP's 32-bit column.
var docEntryRe = regexp.MustCompile(`^[1-9][0-9]{0,9}$`)

// draftKind is one deletable entity set and everything the command needs to say
// about it. Two exist, both hard-coded: there is no path by which a third
// arrives at runtime.
type draftKind struct {
	Command    string // the subcommand name: "draft" / "payment-draft"
	EntitySet  string // "Drafts" / "PaymentDrafts"
	Noun       string // "draft" / "payment draft"
	WhereInSAP string // where a human would look for it in the SAP B1 client
	// SummaryFields are shown to the operator before they confirm.
	SummaryFields []string
	// SnapshotFields and LineCollections are the STRICT allowlist recorded in
	// the write log. Everything not named here is dropped — the snapshot is what
	// SAP returned, and a server-side PaymentDrafts row carries the vendor's bank
	// account, cheque numbers and the transfer GL account. That file is designed
	// to be committed; none of that may ride along.
	SnapshotFields  []string
	LineCollections map[string][]string
	// FundingLegs are collections whose CONTENTS may never be recorded — a
	// cheque line carries the number, the bank and the account — but whose
	// AMOUNTS the operator has to see. Their totals are computed here and shown
	// as one line each.
	FundingLegs []fundingLeg
}

// fundingLeg is one way a payment draft can carry money in its lines.
type fundingLeg struct {
	Collection  string // the SAP collection, e.g. "PaymentChecks"
	AmountField string // the amount on each line, e.g. "CheckSum"
	Label       string // what the computed total is called on screen and in the snapshot
	Noun        string // what one line is, for "(1 cheque)"
}

var kindDraft = draftKind{
	Command:    "draft",
	EntitySet:  "Drafts",
	Noun:       "draft",
	WhereInSAP: "Document Drafts",
	// AuthorizationStatus is on this list and not only in the snapshot: an Oil A/P
	// invoice draft routes through approval template "USER03 AP" and sits in
	// somebody's Approval Status Report as Pending, while still reading
	// bost_Open — so no other guard sees it. A draft somebody is waiting to
	// approve must not be destroyed under a summary that says nothing about it.
	// writeDraftSummary skips absent fields, so drafts outside a workflow print
	// nothing extra.
	SummaryFields: []string{
		"DocEntry", "DocNum", "DocObjectCode", "DocType", "CardCode", "CardName",
		"DocDate", "DocTotal", "NumAtCard", "DocumentStatus", "AuthorizationStatus",
		"BPLName", "Series", "UserSign", "CreationDate", "AttachmentEntry", "Comments",
	},
	SnapshotFields: []string{
		"DocEntry", "DocNum", "DocObjectCode", "DocType", "CardCode", "CardName",
		"DocDate", "DocDueDate", "TaxDate", "DocTotal", "VatSum", "DocCurrency",
		"NumAtCard", "DocumentStatus", "Cancelled", "UserSign", "CreationDate",
		"UpdateDate", "Comments", "JournalMemo", "AttachmentEntry", "Series",
		"BPLName", "AuthorizationStatus",
	},
	LineCollections: map[string][]string{
		"DocumentLines": {
			"LineNum", "ItemCode", "ItemDescription", "Quantity", "UnitPrice",
			"LineTotal", "TaxCode", "TaxTotal", "WarehouseCode", "CostingCode",
			"WTLiable", "BaseType", "BaseEntry", "BaseLine",
		},
	},
}

var kindPaymentDraft = draftKind{
	Command:    "payment-draft",
	EntitySet:  "PaymentDrafts",
	Noun:       "payment draft",
	WhereInSAP: "Banking → Payment Drafts",
	// Field names below were read off a live PaymentDrafts row (2026-08-24), not
	// guessed: OPDF has no DocumentStatus and no header CheckSum, which is why
	// neither appears here and why the already-Added check announces itself as
	// inapplicable for this kind.
	//
	// A payment is funded by any of five legs (draftpayment.go, which creates
	// these, checks all five). Three are header amounts and are listed here; the
	// other two live in lines and come in through FundingLegs. Naming only cash
	// and transfer would show a 25-lakh cheque payment as 0.0 on every line the
	// operator sees, directly above a prompt asking them to destroy it.
	SummaryFields: []string{
		"DocEntry", "DocNum", "DocObjectCode", "DocType", "CardCode", "CardName",
		"DocDate", "CashSum", "TransferSum", "BillOfExchangeAmount", "DocCurrency",
		"BPLName", "Series", "Cancelled", "AuthorizationStatus", "AttachmentEntry",
		"Remarks",
	},
	SnapshotFields: []string{
		"DocEntry", "DocNum", "DocObjectCode", "DocType", "CardCode", "CardName",
		"DocDate", "DueDate", "TaxDate", "DocCurrency", "DocRate", "CashSum",
		"TransferSum", "BillOfExchangeAmount", "Remarks", "JournalRemarks",
		"Cancelled", "CancelStatus", "AttachmentEntry", "Series", "BPLName",
		"AuthorizationStatus",
	},
	LineCollections: map[string][]string{
		"PaymentInvoices": {"LineNum", "DocEntry", "DocNum", "SumApplied", "InvoiceType"},
		"PaymentAccounts": {"LineNum", "SumPaid"},
	},
	FundingLegs: []fundingLeg{
		{Collection: "PaymentChecks", AmountField: "CheckSum", Label: "ChequeSum", Noun: "cheque"},
		{Collection: "PaymentCreditCards", AmountField: "CreditSum", Label: "CreditCardSum", Noun: "card payment"},
	},
}

// deleteFlags backs `delete draft` / `delete payment-draft`. It is deliberately
// not writeFlags: there is no payload here, and every extra flag is an override
// of a guard rather than an input.
type deleteFlags struct {
	yes            bool
	dryRun         bool
	notCreatedHere bool
	withAttachment bool
	closed         bool
	otherOperator  bool
	inApproval     bool
	olderThan      time.Duration
}

const deleteRefusalText = `delete needs to know WHAT kind of draft, and it only knows two:

  sapb1 delete draft <DocEntry> [<DocEntry>...]           a document draft (Drafts)
  sapb1 delete payment-draft <DocEntry> [<DocEntry>...]   a payment draft (PaymentDrafts)

Drafts are the only thing this CLI will delete. A draft has posted nothing — no
stock moved, no ledger entry exists — so removing one costs whoever keyed it
their typing and nothing else. A posted or cancelled document is a human's job
in the SAP B1 client, and there is no flag here that changes that.`

func newDeleteCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete",
		Short: "Delete a DRAFT from SAP (drafts only, provenance-guarded)",
		Long: `delete removes a draft from SAP. Drafts, and nothing else.

There is no entity argument: the subcommand fixes the entity set, so
"delete Invoices(9)" and "delete Drafts(1)/Cancel" are not refusals, they are
unknown commands. Nothing posted, cancelled or live can be addressed from here.

  sapb1 delete draft <DocEntry> [<DocEntry>...]           Drafts
  sapb1 delete payment-draft <DocEntry> [<DocEntry>...]   PaymentDrafts

Each draft is read first and shown to you, the whole batch is previewed and
confirmed once, and then they are deleted one at a time, stopping at the first
failure. Every attempt is appended to the write log, and — once an operator is
registered here — to queries/<operator>/sap-writes.jsonl, which is committed and
shared with the team, whatever $SAPB1_WRITE_LOG says. What the draft HELD (the
party, their bill number, the totals, the line prices) is written to the snapshot
log on this machine only; the shared line carries its sha256, so the history says
which document was destroyed without publishing somebody's invoice.

Six guards stand in front of a delete, each with one flag that asserts past it
for a single recorded run: it is in no write log (--not-created-here), it is over
a day old (--older-than), it has a file attached (--with-attachment), it is no
longer Open (--closed), another operator created it (--other-operator), it is in
an approval workflow (--in-approval). Two more checks have no flag: a vouching
log line SAP's CreationDate contradicts, and one with no usable timestamp.

By default it refuses a draft this CLI did not create. That guard reads the
write logs in this checkout; a draft somebody keyed by hand in the SAP client
has no line there, and deleting it means they key it again from scratch.`,
		Example: exampleBlock(
			`sapb1 delete draft 54990 --dry-run          # look it up, show the DELETE, send nothing`,
			`sapb1 delete draft 54990 54991 54992        # preview all three, confirm once`,
			`sapb1 delete payment-draft 812 --yes`,
			`sapb1 delete draft 54991 --not-created-here # someone keyed it by hand; assert it, at the prompt`,
		),
		Args: cobra.NoArgs, // makes `delete Invoices(9)` an unknown command, not an argument
		RunE: func(cmd *cobra.Command, args []string) error {
			return &errs.UsageError{Msg: deleteRefusalText}
		},
	}

	cmd.AddCommand(newDeleteKindCmd(kindDraft))
	cmd.AddCommand(newDeleteKindCmd(kindPaymentDraft))
	return cmd
}

func newDeleteKindCmd(kind draftKind) *cobra.Command {
	var df deleteFlags

	cmd := &cobra.Command{
		Use:   kind.Command + " <DocEntry> [<DocEntry>...]",
		Short: fmt.Sprintf("Delete one or more %ss by DocEntry (%s)", kind.Noun, kind.EntitySet),
		Long: fmt.Sprintf(`delete %s removes %s rows by DocEntry.

Each DocEntry is read first (a plain GET), shown to you with who created it and
when, and checked against six guards. Each guard has one flag that switches it
off for one run, and using one is recorded in the write log:

  it is in no write log            --not-created-here  (one DocEntry, at the prompt)
  it is older than %s             --older-than <dur>
  it has a file attached           --with-attachment
  it is no longer Open             --closed
  another operator created it      --other-operator
  it is in an approval workflow    --in-approval

Two more checks have no flag of their own, and both end at --not-created-here:
when SAP's own CreationDate on the row disagrees with the write-log line vouching
for it, that line is not about this draft (DocEntry numbers come round again
after a company restore); and when that line carries no timestamp at all, or one
in the future, nothing here can say how old the draft is — every age check rests
on it.

--dry-run does the lookups and prints the exact DELETE requests without sending
any of them. Note that this differs from draft/post/patch --dry-run, which
contact SAP not at all: to show you what you are deleting, this one has to read
it.

Two things about the write log everything above rests on. It is a plain text
file on this machine — unsigned, and appendable by anything running here — so
treat it as a record and a check against mistakes, not as a lock: it will stop
you deleting somebody's hand-keyed draft by accident, it cannot stop someone who
means to. And the record splits in two. The DELETE itself goes to
queries/<operator>/sap-writes.jsonl, which is committed and shared with the team,
whatever $SAPB1_WRITE_LOG says — a delete nobody else can see is not a record.
That holds once an operator is REGISTERED in this checkout (one run of
"python3 harness/bin/setup.py"); until then there is no name to file it under,
the DELETE is recorded only in this machine's own log, and the preview above the
prompt says so before you type yes. The SNAPSHOT of what the %s held (the party,
their bill number, the totals and the line items with their prices) stays on this
machine, in the snapshot log, and the shared line carries only its sha256: that
repo is public, and a vendor's invoice does not belong in it.`, kind.Command, kind.EntitySet, shortDuration(maxDraftAge), kind.Noun),
		Args: func(cmd *cobra.Command, args []string) error {
			if len(args) == 0 {
				return &errs.UsageError{Msg: fmt.Sprintf(
					"which %s? Pass one or more DocEntry numbers, e.g. `sapb1 delete %s 54990`",
					kind.Noun, kind.Command)}
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			return runDeleteDrafts(cmd, kind, args, df)
		},
	}

	cmd.Flags().BoolVar(&df.yes, "yes", false, "skip the confirmation prompt — required when stdin is not a terminal")
	cmd.Flags().BoolVar(&df.dryRun, "dry-run", false, "look the drafts up and print the DELETEs that WOULD be sent; sends none (this one DOES read SAP)")
	cmd.Flags().BoolVar(&df.notCreatedHere, "not-created-here", false, "delete even though no write log shows this CLI created it (one DocEntry, prompt required, recorded)")
	cmd.Flags().DurationVar(&df.olderThan, "older-than", 0, "permit deleting a draft this old or younger, e.g. 48h (recorded)")
	cmd.Flags().BoolVar(&df.withAttachment, "with-attachment", false, "permit deleting a draft that has a file attached (recorded)")
	cmd.Flags().BoolVar(&df.closed, "closed", false, "permit deleting a draft that is no longer Open (recorded)")
	cmd.Flags().BoolVar(&df.otherOperator, "other-operator", false, "permit deleting a draft another operator created (recorded)")
	cmd.Flags().BoolVar(&df.inApproval, "in-approval", false, "permit deleting a draft that is in an approval workflow (recorded)")

	return cmd
}

// parseDocEntries turns the operator's arguments into DocEntry numbers, keeping
// their order and reporting repeats rather than silently deleting twice.
func parseDocEntries(args []string) (entries []int64, dupes []int64, err error) {
	seen := make(map[int64]bool, len(args))
	for _, arg := range args {
		if !docEntryRe.MatchString(arg) {
			return nil, nil, &errs.UsageError{Msg: fmt.Sprintf(
				"%q is not a DocEntry. This command takes plain positive numbers — the DocEntry of a draft, e.g. 54990. "+
					"It does not take an entity set, a key path or a filter", arg)}
		}
		// ODRF.DocEntry is a 32-bit column: a bigger number is a typo, and it is
		// worth saying so here rather than letting SAP answer "not found".
		n, perr := strconv.ParseInt(arg, 10, 32)
		if perr != nil {
			return nil, nil, &errs.UsageError{Msg: fmt.Sprintf(
				"DocEntry %s is larger than SAP can hold (max 2147483647) — check the number", arg)}
		}
		if seen[n] {
			dupes = append(dupes, n)
			continue
		}
		seen[n] = true
		entries = append(entries, n)
	}
	return entries, dupes, nil
}

// validate checks the flag combinations that are wrong regardless of what the
// drafts turn out to be.
func (df deleteFlags) validate(count int, stdinIsTTY bool) error {
	if count > maxDeleteBatch {
		return &errs.UsageError{Msg: fmt.Sprintf(
			"%d DocEntries in one command — the cap is %d. Split the list; a delete list this long is worth reading twice anyway",
			count, maxDeleteBatch)}
	}
	if !df.notCreatedHere {
		return nil
	}
	if count != 1 {
		return &errs.UsageError{Msg: "--not-created-here takes exactly one DocEntry; run them one at a time — you are asserting something about THAT draft"}
	}
	if df.yes || (!df.dryRun && !stdinIsTTY) {
		return &errs.UsageError{Msg: "--not-created-here asserts a person keyed this draft; that assertion needs a person at the prompt. It cannot be combined with --yes or a non-interactive stdin"}
	}
	return nil
}

// draftPreflight is one DocEntry after the read-only lookup: what it holds, what
// vouches for it, and what (if anything) stands in the way of deleting it.
type draftPreflight struct {
	DocEntry int64
	Obj      map[string]interface{}
	// Snapshot is the row as it read at PREFLIGHT — what the operator was shown,
	// and what a --dry-run or a refusal reports. It is not what gets recorded: a
	// delete rebuilds the snapshot from the read taken immediately before the
	// DELETE goes out (see deleteOne), because the log has to hold a copy of the
	// row that was actually destroyed.
	Snapshot json.RawMessage
	// Status is DocumentStatus as it read at preflight (empty when the entity
	// has none). The just-before-send re-check compares against THIS, not
	// against bost_Open: what must stop a delete is the status CHANGING under
	// the operator, and that is true whatever it started as.
	Status    string
	Origin    *draftOrigin
	Overrides []string
	Problems  []draftProblem
	Skip      string
}

// draftProblem is one guard refusing one draft: which guard, the flag that
// asserts past it, and the sentence the operator reads.
//
// The first two exist so the --json stream can carry a refusal a machine can act
// on. acc/apbatch runs fifty drafts at a time; "attachment" and
// "--with-attachment" are what let it journal which draft stopped the batch and
// build the follow-up command, instead of scraping prose out of stderr.
type draftProblem struct {
	Guard string // "provenance", "creation-date", "log-timestamp", "older-than", "attachment", "closed", "other-operator", "in-approval"
	Flag  string // the flag that asserts past it, e.g. "--older-than 96h"
	Msg   string // what the operator reads
}

func runDeleteDrafts(cmd *cobra.Command, kind draftKind, args []string, df deleteFlags) error {
	// A closed stdout must come back as an error this command can report on, not
	// as a signal that kills it between two DELETEs.
	ignoreSIGPIPE()

	cfg, err := writeConfigMsg(cmd, "--csv is not supported for delete; use --json for machine-readable output (one JSON object per draft)")
	if err != nil {
		return err
	}

	entries, dupes, err := parseDocEntries(args)
	if err != nil {
		return err
	}

	errOut := cmd.ErrOrStderr()
	for _, d := range dupes {
		fmt.Fprintf(errOut, "note: DocEntry %d given twice — it will be deleted once.\n", d)
	}
	if err := df.validate(len(entries), stdinIsTTYFunc()); err != nil {
		return err
	}

	// One pass over the fleet's write logs for the whole batch.
	logPaths, notes := provenanceLogPaths()
	for _, n := range notes {
		fmt.Fprintln(errOut, n)
	}
	idx, scanned, problems := buildProvenanceIndex(logPaths, kind.EntitySet, cfg.CompanyDB)
	for _, p := range problems {
		fmt.Fprintf(errOut, "warning: %s\n", p)
	}

	c := client.New(cfg)
	c.SetErrWriter(errOut)

	pfs, err := preflightDrafts(cmd, c, cfg, kind, entries, df, idx, scanned, problems)
	if err != nil {
		return err
	}

	// Summaries go to stderr so stdout stays machine-readable in --json mode; in
	// plain dry-run mode stdout is the report, so they go there.
	summaryOut := errOut
	if df.dryRun && !cfg.JSON {
		summaryOut = cmd.OutOrStdout()
	}
	var refusals []string
	for _, pf := range pfs {
		writeDraftSummary(summaryOut, cfg, kind, pf)
		for _, p := range pf.Problems {
			refusals = append(refusals, p.Msg)
		}
	}
	if len(refusals) > 0 {
		// The JSON stream carries the refusal too. Without this, --json produced
		// ZERO bytes here: exit 9 and a page of prose on stderr. The batch tooling
		// this command exists for runs fifty drafts at a time, and when one of the
		// fifty trips a guard the caller got an empty stdout — no DocEntry, no
		// reason, nothing to journal or to build the follow-up command from.
		if cfg.JSON {
			if err := renderRefusedBatch(cmd.OutOrStdout(), cfg, kind, pfs, df.dryRun); err != nil {
				return err
			}
		}
		return &errs.RefusedError{Msg: strings.Join(refusals, "\n\n")}
	}

	live := make([]draftPreflight, 0, len(pfs))
	for _, pf := range pfs {
		if pf.Skip == "" {
			live = append(live, pf)
		}
	}

	if df.dryRun {
		return renderDeleteDryRun(cmd, cfg, kind, pfs)
	}

	// Nothing left to confirm: every DocEntry was already gone. Say so and let
	// the loop render the skips (the JSON stream still gets a record each).
	if len(live) == 0 {
		fmt.Fprintf(errOut, "Every %s in this list is already gone — nothing to confirm.\n", kind.Noun)
		return deleteSequentially(cmd, c, cfg, kind, pfs, df)
	}

	previewDelete(errOut, cfg, kind, live)
	prompt := fmt.Sprintf("Type 'yes' to DELETE %d %s(s) from %s (this cannot be undone): ", len(live), kind.Noun, cfg.CompanyDB)
	if err := confirmPrompt(cmd, prompt, df.yes, stdinIsTTYFunc()); err != nil {
		return err
	}

	return deleteSequentially(cmd, c, cfg, kind, pfs, df)
}

// preflightDrafts reads every DocEntry and runs the guards. It sends no DELETE
// and stops at the first read error — a batch that cannot be read cannot be
// judged.
func preflightDrafts(cmd *cobra.Command, c *client.Client, cfg *config.Config, kind draftKind, entries []int64, df deleteFlags, idx map[originKey]draftOrigin, scanned, scanProblems []string) ([]draftPreflight, error) {
	out := make([]draftPreflight, 0, len(entries))
	statusNoted, creationDateNoted := false, false

	for _, docEntry := range entries {
		res, err := c.GetEntity(cmd.Context(), kind.EntitySet, docEntry)
		if err != nil {
			return nil, err
		}

		pf := draftPreflight{DocEntry: docEntry}
		if !res.Found {
			if len(entries) == 1 {
				return nil, &errs.UsageError{Msg: fmt.Sprintf(
					"%s(%d) does not exist in %s — nothing to delete. It may already be gone, or the DocEntry may belong to another company (check --company)",
					kind.EntitySet, docEntry, cfg.CompanyDB)}
			}
			// In a batch this is the normal state of a re-run after a partial
			// failure: the first few already went. Skipping is what makes
			// "just run it again" work.
			pf.Skip = "not found — already deleted"
			out = append(out, pf)
			continue
		}

		pf.Obj = decodeWriteObject(res.Body)
		if err := requireRequestedRow(cfg, kind, docEntry, res.Status, res.Body, pf.Obj); err != nil {
			return nil, err
		}
		pf.Snapshot = snapshotOf(pf.Obj, kind)
		pf.Status = draftStatus(pf.Obj)

		statusNoted = checkDraftStatus(cmd.ErrOrStderr(), kind, df, &pf, statusNoted)
		checkProvenance(cfg, kind, df, &pf, idx, scanned, scanProblems)
		creationDateNoted = noteMissingCreationDate(cmd.ErrOrStderr(), kind, &pf, creationDateNoted)
		checkAttachment(kind, df, &pf)
		checkApprovalStatus(kind, df, &pf)

		out = append(out, pf)
	}
	return out, nil
}

// requireRequestedRow refuses a 2xx whose body is not the row that was asked
// for.
//
// client.GetEntity treats any 2xx as "found" and hands the body back; nothing
// else here checks that the body IS a draft, or that it is THIS draft. Every
// guard below reads its signal off that object and treats an absent field as
// "does not apply", so a 200 carrying an HTML error page or a Service Layer
// {"error":…} envelope made the closed check, the attachment check and the
// CreationDate cross-check all pass vacuously, printed a summary listing no
// fields at all, and recorded an empty snapshot — above a prompt that had just
// promised the operator a record of what the draft held.
//
// It is not a hypothetical shape: SAP sits behind Traefik and an ssh bridge
// here, and a mis-routed proxy answering 200 for a keyed path is exactly how
// this arrives.
func requireRequestedRow(cfg *config.Config, kind draftKind, docEntry int64, status int, body []byte, obj map[string]interface{}) error {
	if obj != nil {
		if raw, ok := obj["DocEntry"]; ok && raw != nil {
			if n, ok := numberValue(raw); ok && int64(n) == docEntry {
				return nil
			}
		}
	}
	return &errs.APIError{Msg: fmt.Sprintf(
		"SAP answered %d for GET %s(%d) in %s, but the body is not that %s row — it is %s. Nothing was deleted.\n"+
			"  Something between this command and SAP answered for it: check what is listening on %s:%d (a bridge, a tunnel or a proxy in front of the Service Layer), then re-run.",
		status, kind.EntitySet, docEntry, cfg.CompanyDB, kind.Noun, describeUnexpectedBody(obj, body),
		cfg.Host, cfg.Port)}
}

// describeUnexpectedBody names what came back instead of the row, in the terms
// the operator needs to work out which box lied to them.
func describeUnexpectedBody(obj map[string]interface{}, body []byte) string {
	if obj == nil {
		s := strings.TrimSpace(string(body))
		if s == "" {
			return "empty"
		}
		if len(s) > 60 {
			s = s[:60] + "…"
		}
		return fmt.Sprintf("not a JSON object (it starts %q)", s)
	}
	if _, isErr := obj["error"]; isErr {
		return "a Service Layer error envelope"
	}
	if raw, ok := obj["DocEntry"]; ok && raw != nil {
		return fmt.Sprintf("an object whose DocEntry is %s", formatCell(raw))
	}
	return "a JSON object with no DocEntry"
}

// checkDraftStatus refuses a draft that is no longer Open. bost_Close on a draft
// usually means it was Added — the draft is the trail behind a real document —
// but a person can also close one off as junk, so the override exists. Returns
// the updated "already said this" flag for the missing-field note.
func checkDraftStatus(errOut io.Writer, kind draftKind, df deleteFlags, pf *draftPreflight, noted bool) bool {
	status := pf.Status
	if status == "" {
		if !noted {
			fmt.Fprintf(errOut, "note: %s carries no DocumentStatus — the already-Added check does not apply to this kind.\n", kind.EntitySet)
		}
		return true
	}
	if status == "bost_Open" {
		return noted
	}
	if df.closed {
		pf.Overrides = append(pf.Overrides, "closed")
		return noted
	}
	pf.Problems = append(pf.Problems, draftProblem{
		Guard: "closed",
		Flag:  "--closed",
		Msg: fmt.Sprintf(
			"refusing to delete %s(%d): DocumentStatus is %s, not bost_Open.\n"+
				"  A closed draft is usually one that was already Added — the draft row is the trail behind a real document, and deleting it destroys that trail.\n"+
				"  If a person closed it as junk instead, re-run with --closed (recorded in the write log).",
			kind.EntitySet, pf.DocEntry, status),
	})
	return noted
}

// checkProvenance is the guard that is on by default: was this draft made by
// this CLI, and by this operator, and recently enough to be batch cleanup?
func checkProvenance(cfg *config.Config, kind draftKind, df deleteFlags, pf *draftPreflight, idx map[originKey]draftOrigin, scanned, scanProblems []string) {
	origin, found := idx[originKey{EntitySet: kind.EntitySet, CompanyDB: cfg.CompanyDB, DocEntry: pf.DocEntry}]
	if !found {
		if df.notCreatedHere {
			pf.Overrides = append(pf.Overrides, "not-created-here")
			return
		}
		pf.Problems = append(pf.Problems, draftProblem{
			Guard: "provenance",
			Flag:  "--not-created-here",
			Msg:   provenanceRefusal(cfg, kind, pf.DocEntry, scanned, scanProblems),
		})
		return
	}

	// A line the clock disagrees with is not evidence about a row that already
	// exists. Both halves matter, and both were holes:
	//
	//   - no timestamp at all (a torn append, a hand-edit, a merge of two
	//     operators' logs) used to fall through to the age guard, which read the
	//     zero time as 292 years old and handed back an unusable --older-than;
	//   - a timestamp in the FUTURE disabled the age guard outright, because
	//     time.Since is then negative and can never exceed maxDraftAge. On
	//     Drafts the CreationDate cross-check below still caught it; on
	//     PaymentDrafts, which SAP returns with no CreationDate, nothing did —
	//     so one future-dated line deleted a hand-keyed payment draft
	//     non-interactively, printing "created here : yes" as reassurance.
	//
	// A forward-skewed clock on the box that wrote the line is enough to produce
	// this without anybody meaning to, and the guard the skew disables is the
	// one asking "has somebody looked at this since". So the line is refused on
	// its own account, whatever entity it is on, and --not-created-here (one
	// DocEntry, a person at the prompt) is what applies.
	if bad, why := untrustworthyOriginTime(origin); bad {
		if df.notCreatedHere {
			pf.Overrides = append(pf.Overrides, "not-created-here")
			return
		}
		pf.Problems = append(pf.Problems, draftProblem{
			Guard: "log-timestamp",
			Flag:  "--not-created-here",
			Msg: fmt.Sprintf(
				"refusing to delete %s(%d): the write-log line vouching for it %s, so nothing here can say how old this %s is.\n"+
					"  Evidence: %s:%d. Every age check rests on that timestamp, so without a trustworthy one the line is not evidence about this row at all. A line like this comes from a torn write, a hand-edit, or a box whose clock is wrong — worth checking the clock on the machine that made the %s.\n"+
					"  Look at it in %s first. If it really should go, re-run with --not-created-here (one DocEntry at a time, and a person must answer the prompt).",
				kind.EntitySet, pf.DocEntry, why, kind.Noun,
				shortPath(origin.File), origin.Line, kind.Noun, kind.WhereInSAP),
		})
		return
	}

	// SAP's own answer beats the local file. The write log is unsigned text on
	// this box; the row's CreationDate came off the server. When they disagree
	// the log line is not about this draft — a stale log after a company
	// restore reuses DocEntry numbers, and a planted line claims whatever its
	// author typed — so it does not get to vouch.
	if sapDate, claimed, contradicts := creationDateContradicts(pf.Obj, origin); contradicts {
		if df.notCreatedHere {
			// Origin stays nil on purpose: that line does not describe this row,
			// and recording it as the authority for the delete would be a lie in
			// the shared history.
			pf.Overrides = append(pf.Overrides, "not-created-here")
			return
		}
		pf.Problems = append(pf.Problems, draftProblem{
			Guard: "creation-date",
			Flag:  "--not-created-here",
			Msg: fmt.Sprintf(
				"refusing to delete %s(%d): the write log says this CLI created it on %s, but SAP says the row was created on %s.\n"+
					"  Evidence: %s:%d. One of the two is not about this draft — DocEntry numbers come back round after a company restore, and a write log is an unsigned text file on this machine.\n"+
					"  Look at it in %s first. If it really should go, re-run with --not-created-here (one DocEntry at a time, and a person must answer the prompt).",
				kind.EntitySet, pf.DocEntry, claimed, sapDate,
				shortPath(origin.File), origin.Line, kind.WhereInSAP),
		})
		return
	}
	pf.Origin = &origin

	if age := time.Since(origin.Time); age > maxDraftAge {
		switch {
		case df.olderThan >= age:
			pf.Overrides = append(pf.Overrides, "older-than="+shortDuration(df.olderThan))
		default:
			suggested := shortDuration(suggestOlderThan(age))
			pf.Problems = append(pf.Problems, draftProblem{
				Guard: "older-than",
				Flag:  "--older-than " + suggested,
				Msg: fmt.Sprintf(
					"refusing to delete %s(%d): this CLI created it %s ago (%s).\n"+
						"  A delete this long after creation is not batch cleanup — somebody has probably looked at it since.\n"+
						"  If you mean it, re-run with --older-than %s (recorded in the write log).",
					kind.EntitySet, pf.DocEntry, humanAge(age), origin.Time.Local().Format("2006-01-02 15:04"),
					suggested),
			})
		}
	}

	if !strings.EqualFold(origin.User, cfg.User) {
		if df.otherOperator {
			pf.Overrides = append(pf.Overrides, "other-operator")
		} else {
			pf.Problems = append(pf.Problems, draftProblem{
				Guard: "other-operator",
				Flag:  "--other-operator",
				Msg: fmt.Sprintf(
					"refusing to delete %s(%d): this CLI created it, but as %s — you are %s.\n"+
						"  A draft is owned by the login that made it, so it is not even in YOUR Document Drafts list; %s may be waiting on it.\n"+
						"  Evidence: %s:%d. If you have spoken to them, re-run with --other-operator (recorded in the write log).",
					kind.EntitySet, pf.DocEntry, origin.User, cfg.User, origin.User,
					shortPath(origin.File), origin.Line),
			})
		}
	}
}

// maxClockSkew is how far ahead of this box a write-log line may be stamped
// before it stops counting as evidence. The line is written by whichever machine
// created the draft, and the fleet's Windows boxes are not all on NTP, so a few
// minutes of honest disagreement must not refuse every delete. Hours are not
// honest disagreement.
const maxClockSkew = 5 * time.Minute

// untrustworthyOriginTime judges the timestamp the age guard rests on, and says
// in the operator's own words what is wrong with it.
func untrustworthyOriginTime(origin draftOrigin) (bool, string) {
	switch {
	case origin.Time.IsZero():
		return true, "carries no timestamp"
	case time.Until(origin.Time) > maxClockSkew:
		return true, fmt.Sprintf("is dated %s, which is in the future",
			origin.Time.Local().Format("2006-01-02 15:04"))
	}
	return false, ""
}

// noteMissingCreationDate says out loud when the one server-side corroboration
// of the log line could not run. checkDraftStatus already announces its own
// missing field; this check used to skip in silence while the summary printed
// "created here : yes" two lines later, which reads as though SAP had confirmed
// it. PaymentDrafts (OPDF) returns no CreationDate at all, so on that kind the
// vouching line is checked against nothing.
func noteMissingCreationDate(errOut io.Writer, kind draftKind, pf *draftPreflight, noted bool) bool {
	if noted || pf.Origin == nil {
		return noted
	}
	if raw, ok := pf.Obj["CreationDate"]; ok && raw != nil {
		return noted
	}
	fmt.Fprintf(errOut,
		"note: %s carries no CreationDate here — the write-log line vouching for this %s cannot be checked against SAP, so \"created here: yes\" rests on this machine's log alone.\n",
		kind.EntitySet, kind.Noun)
	return true
}

// creationDateContradicts compares the vouching log line against the one piece
// of evidence a local file cannot forge: the row's own CreationDate, as SAP
// returned it a second ago.
//
// A whole day of slack, deliberately. CreationDate is a plain date in the
// company's timezone and the log line is a UTC instant, so a draft keyed late
// in the evening straddles two dates honestly. What this catches is the real
// disagreement — a row SAP says was created in 2020 with a log line claiming
// this afternoon. Entities that do not return CreationDate (OPDF) are simply
// not checked; a check that cannot run must not become a refusal.
func creationDateContradicts(obj map[string]interface{}, origin draftOrigin) (sapDate, claimedDate string, contradicts bool) {
	raw, ok := obj["CreationDate"]
	if !ok || raw == nil {
		return "", "", false
	}
	s := formatCell(raw)
	if len(s) < 10 {
		return "", "", false
	}
	sap, err := time.Parse("2006-01-02", s[:10])
	if err != nil {
		return "", "", false
	}
	if origin.Time.IsZero() {
		// A line with no timestamp cannot be compared — and never reaches here:
		// untrustworthyOriginTime refuses it first, on its own account.
		return "", "", false
	}
	local := origin.Time.Local()
	claimed := time.Date(local.Year(), local.Month(), local.Day(), 0, 0, 0, 0, time.UTC)
	diff := claimed.Sub(sap)
	if diff < 0 {
		diff = -diff
	}
	if diff <= 24*time.Hour {
		return "", "", false
	}
	return sap.Format("2006-01-02"), claimed.Format("2006-01-02"), true
}

// checkAttachment refuses a draft with a file attached. An attachment is the one
// signal in the data that a person did work on this row: batch junk has none.
func checkAttachment(kind draftKind, df deleteFlags, pf *draftPreflight) {
	raw, ok := pf.Obj["AttachmentEntry"]
	if !ok || raw == nil || formatCell(raw) == "0" {
		return
	}
	if df.withAttachment {
		pf.Overrides = append(pf.Overrides, "with-attachment")
		return
	}
	pf.Problems = append(pf.Problems, draftProblem{
		Guard: "attachment",
		Flag:  "--with-attachment",
		Msg: fmt.Sprintf(
			"refusing to delete %s(%d): it has a file attached (AttachmentEntry %s) — someone did work on this draft.\n"+
				"  If you mean it, re-run with --with-attachment (recorded in the write log).",
			kind.EntitySet, pf.DocEntry, formatCell(raw)),
	})
}

// approvalFree lists every AuthorizationStatus meaning "no approval workflow has
// touched this draft". Anything else — dasPending, dasApproved, dasGenerated,
// dasRejected, and their pas* twins — means a template matched and the document
// entered somebody's Approval Status Report.
//
// SAP spells the enum per object family: marketing-document drafts (ODRF) return
// the das* prefix, payments (OPDF) return pas*. They are the same state under two
// names, so both belong here. Live proof this matters: Beverages PaymentDrafts
// DocEntry 292 came back "pasWithout" — untouched by any workflow — and a
// das*-only test refused it, which made EVERY payment draft undeletable and
// pushed the operator toward asserting --in-approval about a draft nobody was
// approving. A guard that cries wolf on all of its inputs teaches people to
// override it.
const approvalFree = "dasWithout"

// approvalUntouched is the same state across both object families. add-draft
// works on ODRF alone and keeps using approvalFree above; delete reaches
// PaymentDrafts too, so it must know both spellings.
var approvalUntouched = map[string]bool{
	approvalFree: true, // ODRF — marketing-document drafts
	"pasWithout": true, // OPDF — incoming/outgoing payment drafts
}

// checkApprovalStatus refuses a draft that is in an approval workflow.
//
// It was shown in the summary and recorded in the snapshot, and stopped nothing:
// an Oil A/P invoice draft routes through approval template "USER03 AP" and sits
// in somebody's Approval Status Report as Pending while still reading bost_Open,
// so no other guard here sees it. With --yes nobody reads the summary either. A
// draft somebody has been asked to approve — or has already approved, or has
// rejected and expects to discuss — is in use by a second person, and the whole
// batch-cleanup case for this command is junk nobody has touched.
//
// Absent field means the check does not apply, and a check that cannot run must
// not become a refusal. (PaymentDrafts were once assumed to carry no such field.
// They do — see approvalFree.)
func checkApprovalStatus(kind draftKind, df deleteFlags, pf *draftPreflight) {
	raw, ok := pf.Obj["AuthorizationStatus"]
	if !ok || raw == nil {
		return
	}
	status := formatCell(raw)
	if status == "" || approvalUntouched[status] {
		return
	}
	if df.inApproval {
		pf.Overrides = append(pf.Overrides, "in-approval")
		return
	}
	pf.Problems = append(pf.Problems, draftProblem{
		Guard: "in-approval",
		Flag:  "--in-approval",
		Msg: fmt.Sprintf(
			"refusing to delete %s(%d): this draft is in an approval workflow (AuthorizationStatus %s) — someone is acting on it.\n"+
				"  It is in their Approval Status Report, not only in your Document Drafts, and deleting it takes the request out from under them with no notice.\n"+
				"  Ask them first. If it really should go, re-run with --in-approval (recorded in the write log).",
			kind.EntitySet, pf.DocEntry, status),
	})
}

// provenanceRefusal is the default refusal, and the most important text in this
// command: it has to make an operator stop and ask a person rather than reach
// for the override.
func provenanceRefusal(cfg *config.Config, kind draftKind, docEntry int64, scanned, scanProblems []string) string {
	var b strings.Builder
	fmt.Fprintf(&b, "refusing to delete %s(%d) in %s: no record that this CLI created it.\n", kind.EntitySet, docEntry, cfg.CompanyDB)
	if len(scanned) == 0 {
		b.WriteString("  No write log was found on this machine at all, so nothing can vouch for any draft here.\n")
	} else {
		fmt.Fprintf(&b, "  Scanned %d write log(s): %s — none has a successful POST %s that returned DocEntry=%d for %s.\n",
			len(scanned), strings.Join(shortPaths(scanned), ", "), kind.EntitySet, docEntry, cfg.CompanyDB)
	}
	// If this box's own writes are being recorded somewhere the guard cannot
	// read, that — not a hand-keyed draft — is the likeliest reason a draft made
	// here refuses to delete, and it has a one-command fix. Saying only
	// "--not-created-here" would send an operator into fifty interactive prompts
	// for a fifty-draft batch this CLI made itself.
	if advice := evidenceGapAdvice(); advice != "" {
		fmt.Fprintf(&b, "  %s\n", advice)
	}
	for _, p := range scanProblems {
		fmt.Fprintf(&b, "  %s\n", p)
	}
	b.WriteString("  That usually means a person keyed this draft in the SAP B1 client, and deleting it means they re-key it from scratch.\n")
	b.WriteString("  A colleague's sapb1 log only reaches this box if they committed queries/<them>/sap-writes.jsonl — ask them, or check `git log -- queries/`.\n")
	b.WriteString("  If it really should go, re-run with --not-created-here (one DocEntry at a time, and a person must answer the prompt); the override is recorded in the write log.")
	return b.String()
}

// writeDraftSummary prints what the operator is about to destroy.
func writeDraftSummary(w io.Writer, cfg *config.Config, kind draftKind, pf draftPreflight) {
	fmt.Fprintf(w, "%s(%d) in %s\n", kind.EntitySet, pf.DocEntry, cfg.CompanyDB)
	if pf.Skip != "" {
		fmt.Fprintf(w, "  %-20s: %s\n", "status", pf.Skip)
		return
	}
	for _, f := range kind.SummaryFields {
		raw, ok := pf.Obj[f]
		if !ok || raw == nil {
			continue
		}
		fmt.Fprintf(w, "  %-20s: %s\n", f, trimSAPDate(formatCell(raw)))
	}
	for _, t := range fundingTotals(pf.Obj, kind) {
		fmt.Fprintf(w, "  %-20s: %s\n", t.Leg.Label, t.describe())
	}
	fmt.Fprintf(w, "  %-20s: %s\n", "created here", createdHereLine(cfg, kind, pf))
	if len(pf.Overrides) > 0 {
		fmt.Fprintf(w, "  %-20s: %s\n", "overrides", strings.Join(pf.Overrides, ", "))
	}
}

// createdHereLine renders the provenance verdict with its evidence, so the human
// at the prompt can see WHICH file is vouching before they type yes.
func createdHereLine(cfg *config.Config, kind draftKind, pf draftPreflight) string {
	if pf.Origin == nil {
		if hasOverride(pf.Overrides, "not-created-here") {
			return "NO — deleting on --not-created-here (recorded in the write log)"
		}
		return "NO — no write log shows this CLI creating it"
	}
	where := fmt.Sprintf("(%s:%d)", shortPath(pf.Origin.File), pf.Origin.Line)
	when := pf.Origin.Time.Local().Format("2006-01-02 15:04")
	if !strings.EqualFold(pf.Origin.User, cfg.User) {
		return fmt.Sprintf("yes — but by %s, not you, at %s %s", pf.Origin.User, when, where)
	}
	return fmt.Sprintf("yes — POST %s by %s at %s %s", kind.EntitySet, pf.Origin.User, when, where)
}

// previewDelete prints the exact requests, each with the log line that
// authorised it, then leaves the prompt to confirmPrompt.
func previewDelete(w io.Writer, cfg *config.Config, kind draftKind, pfs []draftPreflight) {
	fmt.Fprintln(w, "About to DELETE from SAP:")
	fmt.Fprintf(w, "  company : %s\n", cfg.CompanyDB)
	fmt.Fprintf(w, "  user    : %s\n", cfg.User)
	fmt.Fprintf(w, "  %-8s: %d\n", pluralNoun(kind), len(pfs))
	for _, pf := range pfs {
		fmt.Fprintf(w, "  request : DELETE %s%s   [%s]\n", cfg.BaseURL(), entityPath(kind, pf.DocEntry), originTag(pf))
	}
	writeRecordLines(w, kind)
	fmt.Fprintf(w, "A deleted %s is gone from %s. Nothing posted is touched, and SAP cannot bring a %s back.\n",
		kind.Noun, kind.WhereInSAP, kind.Noun)
}

// writeRecordLines says where this delete will be written down, and — the part
// that has to be exactly true above a destroy prompt — who will be able to read
// it. The record and the contents go to two different files: one committed and
// shared, one local. Saying "shared with the team" over a path in /tmp, which is
// what this printed before, is worse than saying nothing.
//
// "Outside a checkout" is decided from where the file RESOLVES, never from
// whether an operator happens to be registered. The two are different questions,
// and running them together printed the flatly self-contradictory
// "queries/USER36/sap-writes.jsonl, which is OUTSIDE any checkout" — a relative
// in-repo path, described as being nowhere near the repo, to an operator already
// standing in it, above a prompt asking them to destroy something. What is true
// in that case is narrower and has a fix: nobody is registered here, so nothing
// syncs it.
func writeRecordLines(w io.Writer, kind draftKind) {
	shared := config.SharedWriteLogPath()
	configured, cerr := config.WriteLogPath()
	root, _ := repoRootFunc()

	switch {
	case shared != "":
		fmt.Fprintf(w, "  record  : each DELETE is appended to %s and shared with the team.\n", shortPath(shared))
		if cerr == nil && configured != "" && configured != shared {
			fmt.Fprintf(w, "            (also to %s, which is where $SAPB1_WRITE_LOG points.)\n", shortPath(configured))
		}
	case cerr == nil && configured != "" && root != "" && withinCheckout(root, configured):
		fmt.Fprintf(w, "  record  : each DELETE is appended to %s, which is inside this checkout —\n", shortPath(configured))
		fmt.Fprintln(w, "            but no operator is registered here, so nothing files it under a name or")
		fmt.Fprintln(w, "            syncs it. Run `python3 harness/bin/setup.py` once if it should reach the team.")
	case cerr == nil && configured != "":
		fmt.Fprintf(w, "  record  : each DELETE is appended to %s, which is OUTSIDE any checkout —\n", shortPath(configured))
		fmt.Fprintln(w, "            the team will not see it. Run `python3 harness/bin/setup.py` in the JIVO")
		fmt.Fprintln(w, "            checkout (and leave $SAPB1_WRITE_LOG unset) if it should reach them.")
	}
	if p, err := config.SnapshotLogPath(); err == nil && p != "" {
		fmt.Fprintf(w, "  contents: what the %s held (party, bill number, totals, line prices) is kept in\n", kind.Noun)
		fmt.Fprintf(w, "            %s on THIS machine only; the shared line carries just its sha256.\n", shortPath(p))
	}
}

func originTag(pf draftPreflight) string {
	if pf.Origin == nil {
		return "NOT created by this CLI — --not-created-here"
	}
	return fmt.Sprintf("created by %s, %s:%d", pf.Origin.User, shortPath(pf.Origin.File), pf.Origin.Line)
}

// deleteOutcome is one draft's result, in a shape both the text and the JSON
// renderer can read.
type deleteOutcome struct {
	DryRun       bool
	DocEntry     int64
	EntitySet    string
	CompanyDB    string
	Host         string
	Port         int
	Method       string
	URL          string
	Status       int
	Verified     bool
	VerifyNote   string
	StillPresent bool
	CreatedHere  bool
	Origin       *draftOrigin
	Overrides    []string
	Snapshot     json.RawMessage
	Error        string
	Skipped      string
	// Refused, Reason and SuggestedFlags are set when a guard stopped this
	// DocEntry. They are what makes an exit-9 machine-readable: which guard,
	// what it said, and the exact flags that would assert past it.
	Refused        []string
	Reason         string
	SuggestedFlags []string
}

// renderRefusedBatch writes one JSON record per DocEntry for a batch a guard
// stopped — the refused ones with their guards and suggested flags, the rest
// marked not attempted, so a caller can journal all fifty and see which one
// stopped it.
func renderRefusedBatch(out io.Writer, cfg *config.Config, kind draftKind, pfs []draftPreflight, dryRun bool) error {
	stopper := ""
	for _, pf := range pfs {
		if len(pf.Problems) > 0 {
			stopper = fmt.Sprintf("%s(%d)", kind.EntitySet, pf.DocEntry)
			break
		}
	}

	for _, pf := range pfs {
		o := deleteOutcome{
			DryRun:      dryRun,
			DocEntry:    pf.DocEntry,
			EntitySet:   kind.EntitySet,
			CompanyDB:   cfg.CompanyDB,
			CreatedHere: pf.Origin != nil,
			Origin:      pf.Origin,
			Overrides:   pf.Overrides,
			Snapshot:    pf.Snapshot,
		}
		switch {
		case pf.Skip != "":
			o.Skipped = pf.Skip
		case len(pf.Problems) > 0:
			// The request that WOULD have gone, so the caller can rebuild the
			// command rather than reconstruct the URL.
			o.Host, o.Port = cfg.Host, cfg.Port
			o.Method, o.URL = "DELETE", cfg.BaseURL()+entityPath(kind, pf.DocEntry)
			reasons := make([]string, 0, len(pf.Problems))
			for _, p := range pf.Problems {
				o.Refused = append(o.Refused, p.Guard)
				if p.Flag != "" {
					o.SuggestedFlags = append(o.SuggestedFlags, p.Flag)
				}
				reasons = append(reasons, p.Msg)
			}
			o.Reason = strings.Join(reasons, "\n\n")
		default:
			o.Skipped = fmt.Sprintf("not attempted — %s was refused", stopper)
		}
		if err := writeJSONLine(out, o); err != nil {
			return err
		}
	}
	return nil
}

// deleteSequentially sends the DELETEs one at a time and stops at the first
// failure. Sequential on purpose: a partial batch the operator can read top to
// bottom beats a fast one they have to reconstruct.
func deleteSequentially(cmd *cobra.Command, c *client.Client, cfg *config.Config, kind draftKind, pfs []draftPreflight, df deleteFlags) error {
	out := cmd.OutOrStdout()
	var deleted, failed, unverified, skipped, notAttempted []int64
	var firstErr error
	stopper := "" // what stopped the batch, in the words the tally uses

	for _, pf := range pfs {
		if firstErr != nil {
			notAttempted = append(notAttempted, pf.DocEntry)
			if cfg.JSON {
				// Best-effort: the batch is already stopping and the tally goes to
				// stderr. If stdout is the thing that broke, failing again here would
				// swap a report of what happened for the write error.
				_ = renderSkipped(out, kind, cfg, pf.DocEntry, "not attempted — stopped after "+stopper, false)
			}
			continue
		}
		if pf.Skip != "" {
			skipped = append(skipped, pf.DocEntry)
			if err := renderSkip(out, cfg, kind, pf.DocEntry, pf.Skip); err != nil {
				firstErr = streamStopped(kind, pf.DocEntry, err)
				stopper = fmt.Sprintf("%s(%d) could not be reported", kind.EntitySet, pf.DocEntry)
			}
			continue
		}

		outcome, err := deleteOne(cmd, c, cfg, kind, pf, df)

		// Classified BEFORE it is rendered: the tally has to be right even when
		// the record cannot be printed.
		switch {
		case err != nil && sentButUnverified(outcome, err):
			// "failed" is not what happened when SAP answered the DELETE and only
			// the read-back fell over: the draft is almost certainly gone, and the
			// line printed a moment earlier says so. An operator who reads
			// "failed" in the tally re-keys a document that does not need
			// re-keying — the tally has to agree with the headline above it.
			unverified = append(unverified, pf.DocEntry)
			stopper = fmt.Sprintf("%s(%d) could not be verified", kind.EntitySet, pf.DocEntry)
		case err != nil:
			failed = append(failed, pf.DocEntry)
			stopper = fmt.Sprintf("%s(%d) failed", kind.EntitySet, pf.DocEntry)
		case outcome.Skipped != "":
			// It vanished between the preview and the DELETE. No request was sent
			// and no log line exists for it, so counting it under "deleted" would
			// put a DocEntry nobody touched into the operator's list of destroyed
			// documents — and the write log, the only thing that could settle it,
			// has nothing to say about that number.
			skipped = append(skipped, pf.DocEntry)
		default:
			deleted = append(deleted, pf.DocEntry)
		}

		renderErr := renderDeleteOutcome(out, cfg.JSON, outcome)
		switch {
		case err != nil:
			firstErr = err
		case renderErr != nil:
			firstErr = streamStopped(kind, pf.DocEntry, renderErr)
			stopper = fmt.Sprintf("%s(%d) could not be reported", kind.EntitySet, pf.DocEntry)
		}
	}

	if firstErr == nil {
		return nil
	}
	if len(pfs) == 1 {
		return firstErr
	}
	return &batchError{Err: firstErr, Deleted: deleted, Failed: failed, Unverified: unverified, Skipped: skipped, NotAttempted: notAttempted}
}

// streamStopped is what a batch does when its own output cannot be written.
//
// `sapb1 delete draft … --json | head -1` and `… | grep -q` are ordinary shell,
// and both close the pipe after the first record. The run then destroyed more
// than it printed and died of SIGPIPE (exit 141) on the write AFTER the next
// DELETE had already gone. The audit trail survived that, but the caller's stdout
// is its receipt, and a destructive command that cannot hand over the receipt
// stops instead of carrying on into the rest of the list.
//
// Exit 8, the same code as a delete whose read-back failed, and for the same
// reason: SAP answered, the operator's evidence of it did not arrive, going and
// looking is the next step, and re-running is safe because a DELETE cannot
// double-delete. At most one DocEntry is destroyed past the last record the
// caller managed to read — the outcome cannot be printed before it is known.
func streamStopped(kind draftKind, docEntry int64, cause error) error {
	return &errs.WriteVerifyError{Msg: fmt.Sprintf(
		"stopping: the record for %s(%d) could not be written to stdout (%v). Nothing after it was attempted.\n"+
			"  That %s's own DELETE is in the write log, but a receipt you cannot read is not one. If this was piped into something that closes early (head, grep -q), re-run into a file instead — re-sending a DELETE cannot double-delete.",
		kind.EntitySet, docEntry, cause, kind.Noun)}
}

// sentButUnverified separates "SAP never took this delete" from "SAP took it and
// the read-back could not run". Both come back as *errs.WriteVerifyError (exit
// 8), but only the second one is a draft that is almost certainly gone: a draft
// that still READS BACK may genuinely still be there, so it stays in the failed
// column where an operator will go and look at it.
func sentButUnverified(o deleteOutcome, err error) bool {
	var verify *errs.WriteVerifyError
	return errors.As(err, &verify) && o.Status != 0 && !o.StillPresent
}

// deleteOne re-reads the draft, deletes it, and reads it back.
//
// The re-read is not paranoia about our own preview: a fifty-draft batch runs
// for minutes over the bridge, and Accounts is Adding drafts in the SAP client
// the whole time. Between the preview and this moment a draft can become a
// posted document.
func deleteOne(cmd *cobra.Command, c *client.Client, cfg *config.Config, kind draftKind, pf draftPreflight, df deleteFlags) (deleteOutcome, error) {
	o := deleteOutcome{
		DocEntry:    pf.DocEntry,
		EntitySet:   kind.EntitySet,
		CompanyDB:   cfg.CompanyDB,
		Host:        cfg.Host,
		Port:        cfg.Port,
		Method:      "DELETE",
		URL:         cfg.BaseURL() + entityPath(kind, pf.DocEntry),
		CreatedHere: pf.Origin != nil,
		Origin:      pf.Origin,
		Overrides:   pf.Overrides,
		Snapshot:    pf.Snapshot,
	}

	fresh, err := c.GetEntity(cmd.Context(), kind.EntitySet, pf.DocEntry)
	if err != nil {
		o.Error = err.Error()
		return o, err
	}
	if !fresh.Found {
		o.Skipped = "already gone — deleted between the preview and now"
		return o, nil
	}
	freshObj := decodeWriteObject(fresh.Body)
	if err := requireRequestedRow(cfg, kind, pf.DocEntry, fresh.Status, fresh.Body, freshObj); err != nil {
		o.Error = err.Error()
		return o, err
	}
	// The snapshot that goes in the log is rebuilt from the row as it reads NOW.
	//
	// The preflight copy is what the OPERATOR was shown, and it can be minutes
	// old: an edit that leaves DocumentStatus alone — a line added, a total
	// corrected, the vendor's bill number fixed — passes the status re-check below
	// and used to be recorded as the pre-edit version. The snapshot is the only
	// surviving copy of what was destroyed, so it has to be a copy of what was
	// destroyed.
	o.Snapshot = snapshotOf(freshObj, kind)
	// What stops the batch is the status CHANGING since the operator looked at
	// it — not the status itself, and not whether --closed was passed. --closed
	// asserts "this draft was already closed when I previewed it and I still
	// mean it"; it says nothing about what a colleague does to it in the four
	// minutes a fifty-draft batch takes.
	if now := draftStatus(freshObj); now != pf.Status {
		refusal := &errs.RefusedError{Msg: fmt.Sprintf(
			"stopping: %s(%d) was %s a moment ago and is now %s — somebody is working through this very list in the SAP client. Nothing was deleted for this DocEntry.\n"+
				"  Re-run the command to see it as it stands now; --closed does not cover a change that happened after you looked",
			kind.EntitySet, pf.DocEntry, describeStatus(pf.Status), describeStatus(now))}
		o.Error = refusal.Error()
		return o, refusal
	}

	res, err := c.Delete(cmd.Context(), kind.EntitySet, pf.DocEntry, client.DeleteOptions{
		Snapshot:  o.Snapshot,
		Overrides: pf.Overrides,
		Origin:    toWriteOrigin(pf.Origin),
	})
	if err != nil {
		o.Error = err.Error()
		return o, err
	}
	o.Status = res.Status

	check, verr := c.GetEntity(cmd.Context(), kind.EntitySet, pf.DocEntry)
	switch {
	case verr != nil:
		// SAP answered the DELETE. Whatever went wrong belongs to the read that
		// followed, and reporting it as a network failure would be a lie about a
		// delete that has already happened.
		//
		// The cause is put in the MESSAGE and deliberately NOT wrapped: exit 5 is
		// documented fleet-wide (and in acc/apbatch) as "nothing was sent, safe to
		// retry", and errors.As must not be able to reach a NetworkError through
		// this and reach that conclusion.
		o.VerifyNote = verr.Error()
		return o, &errs.WriteVerifyError{Msg: fmt.Sprintf(
			"Deleted %s(%d) from %s (HTTP %d) — could not verify: %v. The %s is almost certainly gone; check %s if it matters",
			kind.EntitySet, pf.DocEntry, cfg.CompanyDB, res.Status, verr, kind.Noun, kind.WhereInSAP)}
	case check.Found:
		// "Found" is any 2xx, so it has to be shown to be THIS row before it counts
		// as "the draft is still there". A gateway answering 200 for a keyed path —
		// the shape this tool already refuses on the two reads before the DELETE —
		// would otherwise send the operator to Document Drafts to look for a draft
		// SAP has already removed, and park it in the failed column as if the DELETE
		// had not taken.
		if rowErr := requireRequestedRow(cfg, kind, pf.DocEntry, check.Status, check.Body, decodeWriteObject(check.Body)); rowErr != nil {
			o.VerifyNote = rowErr.Error()
			return o, &errs.WriteVerifyError{Msg: fmt.Sprintf(
				"Deleted %s(%d) from %s (HTTP %d) — could not verify: the read-back was answered by something that is not that row. %v",
				kind.EntitySet, pf.DocEntry, cfg.CompanyDB, res.Status, rowErr)}
		}
		o.StillPresent = true
		msg := fmt.Sprintf(
			"SAP answered %d for DELETE %s(%d) but the %s still reads back. The delete may not have taken effect — check %s in the SAP B1 client. "+
				"Re-running this command is safe (a DELETE cannot double-delete)",
			res.Status, kind.EntitySet, pf.DocEntry, kind.Noun, kind.WhereInSAP)
		o.Error = msg
		return o, &errs.WriteVerifyError{Msg: msg}
	}

	o.Verified = true
	return o, nil
}

func renderDeleteOutcome(out io.Writer, asJSON bool, o deleteOutcome) error {
	if asJSON {
		return writeJSONLine(out, o)
	}
	switch {
	case o.Skipped != "":
		fmt.Fprintf(out, "%s(%d): %s — skipping.\n", o.EntitySet, o.DocEntry, o.Skipped)
	case o.StillPresent, o.Status == 0:
		// The error itself carries the whole story; saying "Deleted" here would
		// contradict it.
	case o.VerifyNote != "":
		fmt.Fprintf(out, "Deleted %s(%d) from %s (HTTP %d) — could not verify: %s\n", o.EntitySet, o.DocEntry, o.CompanyDB, o.Status, o.VerifyNote)
	default:
		fmt.Fprintf(out, "Deleted %s(%d) from %s (HTTP %d) — verified gone: it no longer reads back.\n", o.EntitySet, o.DocEntry, o.CompanyDB, o.Status)
	}
	return nil
}

func renderSkip(out io.Writer, cfg *config.Config, kind draftKind, docEntry int64, why string) error {
	if cfg.JSON {
		return renderSkipped(out, kind, cfg, docEntry, why, false)
	}
	fmt.Fprintf(out, "%s(%d): %s — skipping.\n", kind.EntitySet, docEntry, why)
	return nil
}

// renderSkipped emits the JSON record for a DocEntry that was not deleted.
//
// Through writeJSONLine like every other record, and carrying dryRun: a skip
// written in its own little shape used to come out of a --dry-run stream
// byte-identical to the same skip from a real run, so a machine reading the
// JSONL could not tell a preview from a delete that had already happened.
func renderSkipped(out io.Writer, kind draftKind, cfg *config.Config, docEntry int64, why string, dryRun bool) error {
	return writeJSONLine(out, deleteOutcome{
		DryRun:    dryRun,
		DocEntry:  docEntry,
		EntitySet: kind.EntitySet,
		CompanyDB: cfg.CompanyDB,
		Skipped:   why,
	})
}

// renderDeleteDryRun prints the DELETEs that would go, and says clearly that
// this dry run — unlike every other one in this tool — did read SAP.
func renderDeleteDryRun(cmd *cobra.Command, cfg *config.Config, kind draftKind, pfs []draftPreflight) error {
	out := cmd.OutOrStdout()
	if cfg.JSON {
		for _, pf := range pfs {
			if pf.Skip != "" {
				if err := renderSkipped(out, kind, cfg, pf.DocEntry, pf.Skip, true); err != nil {
					return err
				}
				continue
			}
			o := deleteOutcome{
				DryRun:      true,
				DocEntry:    pf.DocEntry,
				EntitySet:   kind.EntitySet,
				CompanyDB:   cfg.CompanyDB,
				Host:        cfg.Host,
				Port:        cfg.Port,
				Method:      "DELETE",
				URL:         cfg.BaseURL() + entityPath(kind, pf.DocEntry),
				CreatedHere: pf.Origin != nil,
				Origin:      pf.Origin,
				Overrides:   pf.Overrides,
				Snapshot:    pf.Snapshot,
			}
			if err := writeJSONLine(out, o); err != nil {
				return err
			}
		}
		return nil
	}

	live := 0
	for _, pf := range pfs {
		if pf.Skip == "" {
			live++
		}
	}
	fmt.Fprintf(out, "DRY RUN — looked up %d %s(s); no DELETE was sent.\n", len(pfs), kind.Noun)
	fmt.Fprintf(out, "  company : %s\n", cfg.CompanyDB)
	for _, pf := range pfs {
		if pf.Skip != "" {
			fmt.Fprintf(out, "  skipped : %s(%d) — %s\n", kind.EntitySet, pf.DocEntry, pf.Skip)
			continue
		}
		fmt.Fprintf(out, "  request : DELETE %s%s   [%s]\n", cfg.BaseURL(), entityPath(kind, pf.DocEntry), originTag(pf))
	}
	fmt.Fprintf(out, "Unlike draft/post/patch --dry-run, this one did contact SAP (to read the %ss it would delete).\n", kind.Noun)
	fmt.Fprintf(out, "Re-run the same command without --dry-run to delete %d %s(s).\n", live, kind.Noun)
	return nil
}

// writeJSONLine emits one compact JSON object per draft (JSONL). Deliberately
// not the single-object shape draft/post/patch return: a batch has one record
// per draft, and a stream a caller can read line by line is worth more than a
// pretty array it has to buffer.
func writeJSONLine(out io.Writer, o deleteOutcome) error {
	overrides := o.Overrides
	if overrides == nil {
		overrides = []string{}
	}
	// The snapshot CONTENTS ride exactly one kind of record: the one for a draft
	// SAP has actually destroyed. That record is the operator's receipt of what is
	// gone, and it is the only copy left. A refused, skipped or dry-run record
	// carries the sha256 and nothing else — the draft is still there to be read,
	// so putting the vendor, their bill number and every line price on stdout
	// (into a log, a journal, a CI transcript) buys nothing. The hash still ties
	// the record to the local snapshot log for anything that has to match them up.
	snapshot := o.Snapshot
	if o.DryRun || o.Status == 0 || o.StillPresent {
		snapshot = nil
	}
	rec := struct {
		DryRun    bool   `json:"dryRun,omitempty"`
		DocEntry  int64  `json:"docEntry"`
		EntitySet string `json:"entitySet"`
		CompanyDB string `json:"companyDb"`
		Host      string `json:"host,omitempty"`
		Port      int    `json:"port,omitempty"`
		Method    string `json:"method,omitempty"`
		URL       string `json:"url,omitempty"`
		Status    int    `json:"status,omitempty"`
		Verified  bool   `json:"verified"`
		// CreatedHere is stated outright rather than left to be inferred from
		// whether "origin" happens to be present — a caller reading a stream of
		// fifty records should not have to know that rule.
		CreatedHere    bool        `json:"createdHere"`
		VerifyNote     string      `json:"verifyNote,omitempty"`
		Skipped        string      `json:"skipped,omitempty"`
		Error          string      `json:"error,omitempty"`
		Refused        []string    `json:"refused,omitempty"`
		Reason         string      `json:"reason,omitempty"`
		SuggestedFlags []string    `json:"suggestedFlags,omitempty"`
		Origin         *originJSON `json:"origin,omitempty"`
		Overrides      []string    `json:"overrides"`
		// SnapshotSHA256 is on every record that read a row at all: it names the
		// row this record is about, contents or no contents. On the record of a
		// draft that was actually deleted it is the same hash the write log's
		// intent line carries, and the key into the local snapshot log.
		SnapshotSHA256 string          `json:"snapshotSha256,omitempty"`
		Snapshot       json.RawMessage `json:"snapshot,omitempty"`
	}{
		DryRun:         o.DryRun,
		DocEntry:       o.DocEntry,
		EntitySet:      o.EntitySet,
		CompanyDB:      o.CompanyDB,
		Host:           o.Host,
		Port:           o.Port,
		Method:         o.Method,
		URL:            o.URL,
		Status:         o.Status,
		Verified:       o.Verified,
		CreatedHere:    o.CreatedHere,
		VerifyNote:     o.VerifyNote,
		Skipped:        o.Skipped,
		Error:          o.Error,
		Refused:        o.Refused,
		Reason:         o.Reason,
		SuggestedFlags: o.SuggestedFlags,
		Origin:         toOriginJSON(o.Origin),
		Overrides:      overrides,
		SnapshotSHA256: snapshotDigest(o.Snapshot),
		Snapshot:       snapshot,
	}
	b, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	_, err = fmt.Fprintln(out, string(b))
	return err
}

// snapshotDigest is the sha256 the write log records for a snapshot, computed
// over the same bytes client.recordSnapshot hashes — so a JSON record and the
// shared log line name the same thing, and a caller can find the contents in the
// local snapshot log without them being printed here.
func snapshotDigest(snapshot json.RawMessage) string {
	if len(snapshot) == 0 {
		return ""
	}
	sum := sha256.Sum256(snapshot)
	return hex.EncodeToString(sum[:])
}

type originJSON struct {
	User string    `json:"user"`
	Time time.Time `json:"time"`
	File string    `json:"file"`
	Line int       `json:"line"`
}

func toOriginJSON(o *draftOrigin) *originJSON {
	if o == nil {
		return nil
	}
	return &originJSON{User: o.User, Time: o.Time, File: shortPath(o.File), Line: o.Line}
}

func toWriteOrigin(o *draftOrigin) *client.WriteOrigin {
	if o == nil {
		return nil
	}
	return &client.WriteOrigin{File: shortPath(o.File), Line: o.Line, User: o.User, Time: o.Time, Host: o.Host, Port: o.Port}
}

// batchError reports what a partial batch actually did. The underlying error is
// preserved for errors.As (and therefore for the exit code): the tally is
// context, not a new failure category.
type batchError struct {
	Err     error
	Deleted []int64
	Failed  []int64
	// Unverified is its own column on purpose: SAP answered these DELETEs and
	// only the read-back after them failed. Counting them as failed contradicts
	// the "Deleted … could not verify" line printed one line above, and sends an
	// operator to re-key a draft that is almost certainly already gone.
	Unverified   []int64
	Skipped      []int64
	NotAttempted []int64
}

func (e *batchError) Unwrap() error { return e.Err }

func (e *batchError) Error() string {
	var b strings.Builder
	b.WriteString(e.Err.Error())
	fmt.Fprintf(&b, "\n  deleted (%d)       : %s", len(e.Deleted), joinEntries(e.Deleted))
	if len(e.Unverified) > 0 {
		fmt.Fprintf(&b, "\n  unverified (%d)    : %s — SAP answered the DELETE, the read-back did not. Almost certainly gone; re-running is safe",
			len(e.Unverified), joinEntries(e.Unverified))
	}
	fmt.Fprintf(&b, "\n  failed (%d)        : %s", len(e.Failed), joinEntries(e.Failed))
	if len(e.Skipped) > 0 {
		fmt.Fprintf(&b, "\n  skipped (%d)       : %s", len(e.Skipped), joinEntries(e.Skipped))
	}
	fmt.Fprintf(&b, "\n  not attempted (%d) : %s", len(e.NotAttempted), joinEntries(e.NotAttempted))
	return b.String()
}

func joinEntries(entries []int64) string {
	if len(entries) == 0 {
		return "-"
	}
	parts := make([]string, 0, len(entries))
	for _, e := range entries {
		parts = append(parts, strconv.FormatInt(e, 10))
	}
	return strings.Join(parts, ", ")
}

// snapshotOf builds the write log's record of what is about to be destroyed.
//
// A STRICT allowlist, applied to nested lines as well as the header. Not a
// blocklist: a blocklist is only as good as the last time somebody read SAP's
// field list, and OPDF alone carries BankAccount, CheckAccount, PayToBankAccountNo
// and TransferAccount. Numbers stay as json.Number, so an 18-digit DocNum is
// recorded as SAP sent it.
func snapshotOf(obj map[string]interface{}, kind draftKind) json.RawMessage {
	if obj == nil {
		return nil
	}
	var b bytes.Buffer
	b.WriteByte('{')
	first := true

	writeField := func(name string, v interface{}) {
		raw, err := json.Marshal(v)
		if err != nil {
			return
		}
		if !first {
			b.WriteByte(',')
		}
		first = false
		key, _ := json.Marshal(name)
		b.Write(key)
		b.WriteByte(':')
		b.Write(raw)
	}

	for _, f := range kind.SnapshotFields {
		if v, ok := obj[f]; ok && v != nil {
			writeField(f, v)
		}
	}
	// The funding legs, as totals only. The amount is not the sensitive part of
	// a cheque line — the CheckNumber, BankCode and AccountNo are, and they stay
	// out. Without this the trail for a cheque-funded payment records every
	// figure it has as zero. These keys are computed by this CLI; SAP has no
	// such field on OPDF.
	for _, t := range fundingTotals(obj, kind) {
		if !t.AmountOK {
			continue
		}
		writeField(t.Leg.Label, json.Number(strconv.FormatFloat(t.Sum, 'f', -1, 64)))
	}
	for _, name := range sortedKeys(kind.LineCollections) {
		rows, ok := obj[name].([]interface{})
		if !ok || len(rows) == 0 {
			continue
		}
		allowed := kind.LineCollections[name]
		filtered := make([]map[string]interface{}, 0, len(rows))
		for _, r := range rows {
			row, ok := r.(map[string]interface{})
			if !ok {
				continue
			}
			keep := make(map[string]interface{}, len(allowed))
			for _, f := range allowed {
				if v, ok := row[f]; ok && v != nil {
					keep[f] = v
				}
			}
			if len(keep) > 0 {
				filtered = append(filtered, keep)
			}
		}
		if len(filtered) > 0 {
			writeField(name, filtered)
		}
	}

	b.WriteByte('}')
	return json.RawMessage(b.Bytes())
}

// legTotal is one funding leg added up: how many lines, how much, and whether
// the amount could be read at all.
type legTotal struct {
	Leg      fundingLeg
	Count    int
	Sum      float64
	AmountOK bool
}

// describe renders the leg for the summary block. When the amount field cannot
// be read it says so rather than printing a confident zero — "there is a cheque
// here and I cannot tell you for how much" is the truth, and it sends the
// operator to SAP instead of to the prompt.
func (t legTotal) describe() string {
	if !t.AmountOK {
		return fmt.Sprintf("%s — amount not readable here; open the %s in SAP before deleting it",
			countNoun(t.Count, t.Leg.Noun), t.Leg.Noun)
	}
	return fmt.Sprintf("%s (%s)", formatCell(t.Sum), countNoun(t.Count, t.Leg.Noun))
}

func countNoun(n int, noun string) string {
	if n == 1 {
		return "1 " + noun
	}
	return fmt.Sprintf("%d %ss", n, noun)
}

// fundingTotals adds up each funding leg present on the row.
func fundingTotals(obj map[string]interface{}, kind draftKind) []legTotal {
	var out []legTotal
	for _, leg := range kind.FundingLegs {
		rows, ok := obj[leg.Collection].([]interface{})
		if !ok || len(rows) == 0 {
			continue
		}
		t := legTotal{Leg: leg, Count: len(rows)}
		for _, r := range rows {
			row, ok := r.(map[string]interface{})
			if !ok {
				continue
			}
			if n, ok := numberValue(row[leg.AmountField]); ok {
				t.Sum += n
				t.AmountOK = true
			}
		}
		out = append(out, t)
	}
	return out
}

// numberValue reads a JSON number whichever way it was decoded — the write path
// keeps json.Number, other callers hand over float64.
func numberValue(v interface{}) (float64, bool) {
	switch t := v.(type) {
	case json.Number:
		f, err := t.Float64()
		return f, err == nil
	case float64:
		return t, true
	case int:
		return float64(t), true
	case int64:
		return float64(t), true
	}
	return 0, false
}

// sortedKeys names the line collections in a fixed order, so two snapshots of
// the same draft are byte-identical and the log line stays diffable (map
// iteration is not an order).
func sortedKeys(m map[string][]string) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	slices.Sort(out)
	return out
}

// draftStatus reads DocumentStatus off a row, or "" when the entity carries
// none (OPDF does not).
func draftStatus(obj map[string]interface{}) string {
	raw, ok := obj["DocumentStatus"]
	if !ok || raw == nil {
		return ""
	}
	return formatCell(raw)
}

// describeStatus puts a SAP status code into the sentence an operator reads.
func describeStatus(status string) string {
	switch status {
	case "":
		return "without a DocumentStatus"
	case "bost_Open":
		return "Open"
	case "bost_Close":
		return "Closed (bost_Close)"
	default:
		return status
	}
}

func entityPath(kind draftKind, docEntry int64) string {
	return kind.EntitySet + "(" + strconv.FormatInt(docEntry, 10) + ")"
}

func hasOverride(overrides []string, name string) bool {
	for _, o := range overrides {
		if o == name || strings.HasPrefix(o, name+"=") {
			return true
		}
	}
	return false
}

// pluralNoun labels the count line in the preview ("drafts  :" / "payments:").
func pluralNoun(kind draftKind) string {
	if kind.EntitySet == "PaymentDrafts" {
		return "payments"
	}
	return "drafts"
}

// humanAge renders a duration the way an operator thinks about it.
func humanAge(d time.Duration) string {
	if d < 48*time.Hour {
		return fmt.Sprintf("%d hours", int(d.Hours()))
	}
	return fmt.Sprintf("%d days", int(d.Hours()/24))
}

// suggestOlderThan rounds up to the next whole day, so the value printed in the
// refusal is one the operator can paste and have work — a suggestion that is
// exactly the current age would be stale by the time they typed it.
//
// Clamped, because "have work" is the whole contract: rounding an age past ~292
// years up to the next day overflows int64 nanoseconds and comes back NEGATIVE.
// cobra accepts a negative duration happily, and `olderThan >= age` can then
// never be true — so the refusal ended with a flag value that reproduces the
// identical refusal. A dead end printed as advice is worse than no advice.
func suggestOlderThan(age time.Duration) time.Duration {
	const day = 24 * time.Hour
	days := age / day
	if days >= time.Duration(math.MaxInt64)/day {
		return time.Duration(math.MaxInt64)
	}
	return (days + 1) * day
}

// shortDuration renders a whole-hour duration the way the operator typed it
// ("96h", not Go's "96h0m0s") — the recorded override should read back as the
// flag value, so the log line and the command line match.
//
// Formatted from the components, never by trimming Go's rendering: trimming
// "0s" then "0m" off "25h30m0s" yields "25h3", and that string is what would
// land in the shared write log as the override the operator asserted. Anything
// not a whole number of hours keeps Go's spelling — ugly, but it reparses.
func shortDuration(d time.Duration) string {
	if d > 0 && d%time.Hour == 0 {
		return strconv.FormatInt(int64(d/time.Hour), 10) + "h"
	}
	return d.String()
}

// trimSAPDate drops the time half of a SAP date-only field, which is always
// midnight-Z and always noise in a summary.
func trimSAPDate(s string) string {
	return strings.TrimSuffix(s, "T00:00:00Z")
}

// shortPath renders one log path relative to the checkout, for readability.
func shortPath(p string) string {
	if short := shortPaths([]string{p}); len(short) == 1 {
		return short[0]
	}
	return p
}
