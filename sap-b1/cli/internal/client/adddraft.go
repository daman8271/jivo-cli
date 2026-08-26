package client

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"strconv"

	"sapb1/internal/errs"
)

// This file holds the one operation in this package that cannot be undone from
// this CLI: pressing Add on a draft.
//
// Create, Update and Delete all leave a way back. A created draft can be
// deleted; a patched field can be patched again; a deleted draft was inert by
// definition and cost its author their typing. SaveDraftToDocument turns a draft
// into a real document — stock moves, the vendor's ledger moves, and it lands in
// a GST return. Nothing in this binary reverses that, and there is no flag that
// could: only SAP can, and only a human in the SAP B1 client.
//
// It lives in its own file rather than in write.go for the same reason Delete
// does: write.go is generic machinery, this is a policy-carrying hard-coded
// path, and keeping it separate is what makes both the AST guard's job and the
// diff legible.

// saveDraftToDocumentPath is the whole path, and it is a constant.
//
// Nothing caller-supplied ever becomes a path segment: only docEntry crosses the
// boundary, and it crosses as an int64 that this file formats itself. So
// "DraftsService_SaveDraftToDocument?$filter=…", "../Login" and
// "PaymentDrafts(812)/SaveDraftToDocument" are not refusals here — they are
// unspellable.
//
// The flat function import is the ONLY route to this operation. The keyed form
// `Drafts(4321)/SaveDraftToDocument` that appears in this repo's refusal
// messages is not a real Service Layer endpoint; it is an illustrative string,
// and `sapb1 post` still refuses it along with every other OData action.
const saveDraftToDocumentPath = "DraftsService_SaveDraftToDocument"

// AddDraftOptions carries what the audit log must record ABOUT an Add, over and
// above the request itself: a snapshot of the draft exactly as it read
// immediately before it was posted (the bytes the operator approved), which
// guard overrides were used, and which write-log line says where the draft came
// from.
//
// The snapshot is split from the rest on the way out — contents to the local
// snapshot log, hash to the shared write log — because the shared log is
// committed to a public repo. See config.SnapshotLogPath.
type AddDraftOptions struct {
	Snapshot json.RawMessage
	// Overrides is always empty today: add-draft has no guard override flags,
	// deliberately (every guard it runs reads a SAP-side fact an operator cannot
	// assert past, only be wrong about). The field exists so this write's log
	// lines have the same shape as every other write's, and so adding an
	// override later is a decision about the COMMAND rather than a change to the
	// log format the fleet already parses.
	Overrides []string
	Origin    *WriteOrigin
}

// saveDraftRequest is the documented body of DraftsService_SaveDraftToDocument.
//
// DocEntry is a STRING, not a number. That is the vendor's own example
// (api-reference/raw/service-layer-api-reference.html:7531-7538) and what the
// live probe against this fleet's Service Layer accepted; it is not a typo to be
// tidied into an int.
type saveDraftRequest struct {
	Document saveDraftDocument `json:"Document"`
}

type saveDraftDocument struct {
	DocEntry string `json:"DocEntry"`
}

// SaveDraftToDocument posts one draft to the books — the API equivalent of
// opening SAP B1 → Document Drafts and pressing Add.
//
// What comes out the other side is one of TWO things, and this method does not
// pretend to know which: if an approval template matches the document it becomes
// an approval REQUEST (nothing enters the ledger), and if none matches — or the
// approval has already been given — it becomes a posted document. Classifying
// that is the caller's job, done by reading the row back, never by guessing from
// the response body.
//
// It builds the path and the payload itself, so no caller-supplied string
// reaches the wire.
//
// DELIBERATELY NO FIELD OVERRIDES. The vendor's example shows a DocDueDate
// riding along in the Document object, and it would be four lines to support.
// It is refused because this command's entire contract is POST EXACTLY THE DRAFT
// THE OPERATOR PREVIEWED: a field override at post time means the bytes posted
// are not the bytes previewed, which defeats the full-field diff the caller runs
// immediately before calling this. If a draft is wrong, `sapb1 patch` it and
// preview it again.
//
// Like Delete, the intent log line is a PRECONDITION: if the audit log cannot be
// written, the Add does not happen. Arguably stronger than for a delete — after
// an irreversible post the intent line is the only local record that we sent it
// at all.
func (c *Client) SaveDraftToDocument(ctx context.Context, docEntry int64, opts AddDraftOptions) (*WriteResult, error) {
	// The CLI layer already enforces both of these (parseDocEntries). They are
	// enforced AGAIN here because this is the last gate before the wire, exactly
	// as Delete does — a future caller inside this binary does not get to skip
	// them by not being the command.
	if docEntry <= 0 {
		return nil, &errs.UsageError{Msg: fmt.Sprintf("Drafts key must be a positive DocEntry, got %d", docEntry)}
	}
	if docEntry > math.MaxInt32 {
		return nil, &errs.UsageError{Msg: fmt.Sprintf(
			"DocEntry %d is larger than SAP can hold (max %d) — check the number", docEntry, math.MaxInt32)}
	}

	payload, err := addDraftPayload(docEntry)
	if err != nil {
		return nil, fmt.Errorf("building the Add request: %w", err)
	}

	// draftPath names the DRAFT, not the request. It is what the snapshot log
	// files this row under and what the refusals say, because
	// "DraftsService_SaveDraftToDocument" identifies an operation and no
	// document. The write log's `path` field still carries the real wire path.
	draftPath := "Drafts(" + strconv.FormatInt(docEntry, 10) + ")"

	extra := &logExtra{
		Overrides:     opts.Overrides,
		Origin:        opts.Origin,
		RequireIntent: true,
		Shared:        true,
		Unrecordable:  unrecordableAdd,
	}

	// Every destination for the record is proved writable before ANY of them is
	// written to, and before the request goes out. The command pre-flights this
	// too, once for the whole batch; doing it again here costs one open() and
	// means a filesystem problem cannot surface between two live documents.
	if bad, err := checkWriteLogTargets(extra.shared()); err != nil {
		return nil, unrecordableAdd(draftPath, bad, err)
	}

	// The snapshot goes down BEFORE the request, like a delete's does, and for a
	// related reason: if this process dies mid-POST, what the operator approved
	// is already on disk, and the operator reconciling an unknown outcome has the
	// vendor, the bill number and the total to search SAP with.
	//
	// Contents to the LOCAL snapshot log; only the sha256 rides the shared write
	// log. queries/ is committed into a public repo and a snapshot carries the
	// vendor's name, their bill number and every line price.
	if len(opts.Snapshot) > 0 {
		sha, snapPath, err := c.recordSnapshot(http.MethodPost, draftPath, opts.Snapshot)
		if err != nil {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf(
				"refusing to ADD %s: the snapshot log at %s could not be written (%v). "+
					"The snapshot is the record of exactly what was posted, and this write cannot be undone from here, so an Add that cannot record one is not allowed — "+
					"fix that path (or set $SAPB1_SNAPSHOT_LOG to somewhere writable) and re-run",
				draftPath, snapPath, err)}
		}
		extra.SnapshotSHA256 = sha
	}

	// The wire path is the flat function import. Note for whoever reads the write
	// log afterwards: the outcome line's `path` is
	// "DraftsService_SaveDraftToDocument", which is NOT an entity-set name, so
	// this line can never be mistaken by the provenance scan for the POST that
	// CREATED a draft (cli.indexLogLine requires path == the entity set).
	return c.write(ctx, http.MethodPost, saveDraftToDocumentPath, payload, extra)
}

// unrecordableAdd is the refusal for an Add whose record cannot be written.
//
// A near-duplicate of unrecordableDelete on purpose. Its sibling's exact words
// are pinned by tests across two packages, and generalising them inside the
// change that introduces an irreversible write is not a trade worth making — ten
// duplicated lines, zero risk. The SENTENCES differ where it matters: a delete
// loses the only copy of what it destroyed, an Add loses the only local evidence
// that a live document was created from this machine.
func unrecordableAdd(path, logPath string, cause error) error {
	fix := fmt.Sprintf("Make %s writable (or move whatever is sitting on that name)", logPath)
	if isConfiguredLog(logPath) {
		fix += ", or point $SAPB1_WRITE_LOG at a file you can append to"
	} else {
		fix += ". That file is inside the checkout, and an Add is always recorded there so the team can read it — no environment variable moves this one"
	}
	return &errs.ConfigError{Msg: fmt.Sprintf(
		"refusing to ADD %s: the write log at %s could not be written (%v).\n"+
			"  An Add with no record is not allowed — this CLI cannot undo one, so that line is the only local evidence that a live document was created from this machine. %s, then re-run",
		path, logPath, cause, fix)}
}

// CheckAddDraftLogTargets proves every file an Add's record must land in can be
// appended to, and sends nothing.
//
// It is exported so the COMMAND can run it once for the whole batch, before the
// first document is live. SaveDraftToDocument checks the same thing again on
// every call — that check is the one that actually guards the write — but
// discovering a full disk or a read-only checkout after three of nine invoices
// have already posted is a much worse afternoon than discovering it before any
// of them have.
func CheckAddDraftLogTargets() (string, error) {
	return checkWriteLogTargets(true)
}

// addDraftPayload builds the request body. ONE builder, used by the method that
// sends it and by the preview that shows it to the operator — so the bytes on
// screen and the bytes on the wire cannot drift apart. A second copy in the
// command would be a second model of the request, which is the whole class of
// bug this command is built to avoid.
func addDraftPayload(docEntry int64) ([]byte, error) {
	return json.Marshal(saveDraftRequest{
		Document: saveDraftDocument{DocEntry: strconv.FormatInt(docEntry, 10)},
	})
}

// SaveDraftToDocumentPath is the path an Add goes to, for the preview to print.
// Exported as a function rather than a constant so there is exactly one
// definition and the preview cannot fall behind it.
func SaveDraftToDocumentPath() string { return saveDraftToDocumentPath }

// AddDraftPayloadFor renders the exact bytes SaveDraftToDocument will send for
// this DocEntry, for the preview and the --dry-run report. It returns a string
// because it is display; the method marshals its own copy for the wire from the
// same builder.
func AddDraftPayloadFor(docEntry int64) string {
	b, err := addDraftPayload(docEntry)
	if err != nil {
		return ""
	}
	return string(b)
}
