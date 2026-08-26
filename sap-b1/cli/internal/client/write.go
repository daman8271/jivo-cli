package client

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptrace"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"sapb1/internal/errs"
)

// WriteResult is the outcome of a successful write. Status is the HTTP status
// the Service Layer returned (201 for a create, 204 for most PATCHes) and Body
// is the raw response body, which is the created object for a create and
// usually empty for a PATCH.
type WriteResult struct {
	Status int
	Body   []byte
}

// Create POSTs payload to entitySet (e.g. "Drafts", "BusinessPartners") and
// returns the created object. Only ever called from an operator-invoked write
// command (`sapb1 draft` / `sapb1 post`), which previews and confirms first.
//
// entitySet must be a bare entity-set name; the caller (internal/cli) validates
// that against the embedded catalog, so an OData action path such as
// "Invoices(9)/Cancel" can never reach this method.
func (c *Client) Create(ctx context.Context, entitySet string, payload []byte) (*WriteResult, error) {
	return c.write(ctx, http.MethodPost, entitySet, payload, nil)
}

// Update PATCHes payload onto a single entity addressed by key, e.g.
// `Orders(123)` or `BusinessPartners('V10000')`. Only ever called from
// `sapb1 patch`, which previews and confirms first.
//
// entityPath must arrive already percent-encoded (see cli.buildKeyPath): what is
// passed here is what goes on the wire and what lands in the audit log, byte for
// byte.
func (c *Client) Update(ctx context.Context, entityPath string, payload []byte) (*WriteResult, error) {
	return c.write(ctx, http.MethodPatch, entityPath, payload, nil)
}

// entitySetRe is what this package accepts as an entity-set name when IT builds
// the path (GetEntity, Delete): a bare OData identifier, nothing else.
var entitySetRe = regexp.MustCompile(`^[A-Za-z][A-Za-z0-9_]*$`)

// deletableSets is the ONLY thing this client will ever DELETE.
//
// A draft is SAP's undo button: nothing posts from one, no stock moves, no
// ledger entry exists until a human presses Add. That makes drafts the single
// class of object an operator may destroy from a terminal — everything else,
// posted or not, is a human's job in the SAP B1 client.
//
// This map, not the command tree, is what makes `DELETE Invoices(9)`
// inexpressible. A future caller — another command, an agent, a cleanup helper —
// cannot widen it by passing a different string; it has to edit this line, in
// this file, next to this comment.
var deletableSets = map[string]bool{
	"Drafts":        true, // ODRF — marketing-document drafts
	"PaymentDrafts": true, // OPDF — incoming/outgoing payment drafts
}

// DeleteOptions carries what the audit log must record ABOUT a delete, over and
// above the request itself: a snapshot of the object as it read immediately
// before it was destroyed (the only surviving copy), which guard overrides the
// operator used, and which write-log line vouched that this CLI created it.
//
// The snapshot is split from the rest on the way out — contents to the local
// snapshot log, hash to the shared write log — because the shared log is
// committed to a public repo. See config.SnapshotLogPath.
type DeleteOptions struct {
	Snapshot  json.RawMessage
	Overrides []string
	Origin    *WriteOrigin
}

// Delete removes one draft by DocEntry. It builds the path itself, so no
// caller-supplied string reaches the wire, and it refuses any entity set outside
// deletableSets.
//
// Unlike Create and Update, the intent log line is a PRECONDITION here: if the
// audit log cannot be written the delete does not happen. For a POST the object
// still exists afterwards and SAP can be queried for it; for a DELETE the log
// line is the only record that the draft ever existed.
func (c *Client) Delete(ctx context.Context, entitySet string, docEntry int64, opts DeleteOptions) (*WriteResult, error) {
	if !entitySetRe.MatchString(entitySet) || !deletableSets[entitySet] {
		return nil, &errs.UsageError{Msg: fmt.Sprintf(
			"refusing to DELETE %q: this CLI deletes drafts only (%s). Posted and live documents are cancelled or removed by a human in the SAP B1 client",
			entitySet, strings.Join(sortedDeletableSets(), ", "))}
	}
	if docEntry <= 0 {
		return nil, &errs.UsageError{Msg: fmt.Sprintf("%s key must be a positive DocEntry, got %d", entitySet, docEntry)}
	}

	path := entitySet + "(" + strconv.FormatInt(docEntry, 10) + ")"
	extra := &logExtra{
		Overrides:     opts.Overrides,
		Origin:        opts.Origin,
		RequireIntent: true,
		// Shared and Unrecordable are stated here rather than inferred from the
		// verb. They used to be: writeLogTargets asked "is this a DELETE?" and
		// attemptWrite reached for unrecordableDelete whenever an intent line was
		// required. Both were true of every caller right up until
		// SaveDraftToDocument, which is a POST and needs the identical treatment —
		// see logExtra.Shared.
		Shared:       true,
		Unrecordable: unrecordableDelete,
	}

	// Every destination for the record is proved writable before ANY of them is
	// written to. A delete's intent line goes to two files, and failing on the
	// second one after writing the first left a line in the shared, committed log
	// that says "a DELETE was sent" for a DELETE that never left this machine.
	if bad, err := checkWriteLogTargets(extra.shared()); err != nil {
		return nil, unrecordableDelete(path, bad, err)
	}

	// The contents go down first, and they go down before the request, for the
	// same reason the intent line does: if this process dies mid-DELETE, what the
	// draft held is already on disk. An unwritable snapshot log stops the delete —
	// the trail is the whole justification for allowing one from a terminal.
	if len(opts.Snapshot) > 0 {
		sha, snapPath, err := c.recordSnapshot(http.MethodDelete, path, opts.Snapshot)
		if err != nil {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf(
				"refusing to DELETE %s: the snapshot log at %s could not be written (%v). "+
					"The snapshot is the only surviving copy of what the draft held, so a delete that cannot record one is not allowed — "+
					"fix that path (or set $SAPB1_SNAPSHOT_LOG to somewhere writable) and re-run",
				path, snapPath, err)}
		}
		extra.SnapshotSHA256 = sha
	}

	return c.write(ctx, http.MethodDelete, path, nil, extra)
}

// unrecordableDelete is the refusal for a delete whose record cannot be written.
// It names the file that has to change.
//
// The advice used to end "set $SAPB1_WRITE_LOG to somewhere writable and re-run"
// whichever log had failed — and for the CHECKOUT's log that cannot work, because
// SharedWriteLogPath ignores that variable by design (a delete is always recorded
// where the team can read it). An operator who did exactly what the message said
// got the identical refusal a second time. So the variable is offered only when
// the file that failed is the one it actually chooses.
func unrecordableDelete(path, logPath string, cause error) error {
	fix := fmt.Sprintf("Make %s writable (or move whatever is sitting on that name)", logPath)
	if isConfiguredLog(logPath) {
		fix += ", or point $SAPB1_WRITE_LOG at a file you can append to"
	} else {
		fix += ". That file is inside the checkout, and a delete is always recorded there so the team can read it — no environment variable moves this one"
	}
	return &errs.ConfigError{Msg: fmt.Sprintf(
		"refusing to DELETE %s: the write log at %s could not be written (%v).\n"+
			"  A delete with no record is not allowed — that line is the only evidence the draft ever existed. %s, then re-run",
		path, logPath, cause, fix)}
}

// sortedDeletableSets renders the allowlist for an error message, in a stable
// order (map iteration is not one).
func sortedDeletableSets() []string {
	out := make([]string, 0, len(deletableSets))
	for k := range deletableSets {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// write performs an authenticated POST/PATCH against path (relative to the
// Service Layer base URL). It mirrors get(): log in first if there is no
// session, and on a 401 re-login exactly once and retry.
//
// The retry is deliberately limited to a 401 that SAP itself answered with.
// Anything that leaves the result in doubt — a timeout, a connection reset after
// the request went out, a bare gateway 502/504 — becomes
// *errs.WriteOutcomeUnknownError and is never replayed, because the write may
// already have committed.
//
// Every attempt is bracketed in the local write log: an "intent" line before the
// request goes out and an "outcome" line after it resolves, so even a killed
// process leaves a record of what was sent.
func (c *Client) write(ctx context.Context, method, path string, payload []byte, extra *logExtra) (*WriteResult, error) {
	if c.b1Session == "" {
		if !c.LoadCachedSession() {
			if err := c.Login(ctx); err != nil {
				// Nothing was sent, but record the abandoned attempt anyway.
				c.appendWriteLog(logOutcome, method, path, payload, 0, "", err, extra)
				return nil, err
			}
		}
	}

	body, status, err := c.attemptWrite(ctx, method, path, payload, extra)
	if err != nil {
		return nil, err
	}

	if status == http.StatusUnauthorized {
		// Exactly one re-login, and only for a 401 SAP itself answered with. A
		// 401 is the Service Layer rejecting the session cookie BEFORE it
		// dispatches, so nothing has been committed and the retry cannot double
		// anything.
		//
		// This is load-bearing for add-draft, not merely convenient. An Add is
		// irreversible from this CLI, and a batch of them runs for minutes over
		// the bridge; without the retry a session expiring mid-batch would kill
		// the run at the one write in this tool where the operator then has to
		// reason about which documents went and which did not. Removing it makes
		// add-draft strictly MORE dangerous, not less.
		//
		// Close out this attempt in the log before trying again, so the pair
		// count always matches the number of requests actually sent.
		c.appendWriteLog(logOutcome, method, path, payload, status, "", errSessionExpiredRetry, extra)
		if err := c.Login(ctx); err != nil {
			c.appendWriteLog(logOutcome, method, path, payload, status, "", err, extra)
			return nil, err
		}
		body, status, err = c.attemptWrite(ctx, method, path, payload, extra)
		if err != nil {
			return nil, err
		}
	}

	if status < 200 || status >= 300 {
		code, msg := extractSAPErrorDetail(body)
		var werr error
		switch {
		case status == http.StatusUnauthorized:
			if msg == "" {
				msg = fmt.Sprintf("HTTP %d", status)
			}
			werr = &errs.AuthError{Msg: fmt.Sprintf("authentication failed: %s", msg)}
		case msg == "" && isGatewayStatus(status):
			// A gateway/proxy answered, not SAP. The request may well have reached
			// SAP and committed — we just never got SAP's answer.
			werr = c.outcomeUnknownError(method, path, fmt.Sprintf("HTTP %d from a gateway/proxy, with no SAP error body", status), nil)
		default:
			if msg == "" {
				msg = fmt.Sprintf("HTTP %d", status)
			}
			werr = &errs.APIError{Code: code, Msg: msg}
		}
		c.appendWriteLog(logOutcome, method, path, payload, status, "", werr, extra)
		return nil, werr
	}

	c.appendWriteLog(logOutcome, method, path, payload, status, resultKeyFromBody(body), nil, extra)
	return &WriteResult{Status: status, Body: body}, nil
}

// errSessionExpiredRetry is what the log records for the 401 that triggers the
// one allowed re-login — it is not an error the caller ever sees.
var errSessionExpiredRetry = errors.New("HTTP 401 (session expired) — re-logging in and retrying this write once")

// attemptWrite logs the intent, fires exactly one request, and classifies a
// transport failure as either "never left the building" (*errs.NetworkError,
// safe to re-run) or "may have been committed"
// (*errs.WriteOutcomeUnknownError, do not re-run). Either way the outcome is
// logged before returning.
func (c *Client) attemptWrite(ctx context.Context, method, path string, payload []byte, extra *logExtra) ([]byte, int, error) {
	logPath, logErr := c.appendWriteLog(logIntent, method, path, payload, 0, "", nil, extra)
	if logErr != nil && extra != nil && extra.RequireIntent {
		// Deliberately different from the Create/Update path, which warns and
		// carries on. A delete that goes unrecorded destroys the only evidence
		// the object existed, so an unwritable log stops it.
		//
		// Delete pre-flights every target (checkWriteLogTargets), so reaching here
		// means something took the file away between that check and this line. Same
		// refusal either way. add-draft pre-flights them too, from the command.
		//
		// The refusal SENTENCE comes from the caller (logExtra.Unrecordable): a
		// delete and an Add lose different things when the record cannot be
		// written, and this is the one place an operator finds out which.
		return nil, 0, extra.unrecordable(path, logPath, logErr)
	}

	body, status, sent, err := c.rawWrite(ctx, method, path, payload)
	if err != nil {
		if sent {
			err = c.outcomeUnknownError(method, path, "the response never arrived", err)
		}
		c.appendWriteLog(logOutcome, method, path, payload, 0, "", err, extra)
		return nil, 0, err
	}
	return body, status, nil
}

// outcomeUnknownError builds the one error in this tool whose whole job is to
// change what the reader does next: don't re-run it, go look in SAP.
func (c *Client) outcomeUnknownError(method, path, why string, cause error) error {
	advice := "Check SAP (query the entity / Document Drafts) before re-running this command: a blind retry can create a duplicate"
	if method == http.MethodDelete {
		// The opposite failure mode: a DELETE cannot double-delete, so the
		// duplicate warning would be wrong. What the operator still must not do
		// is assume — the draft may or may not be gone.
		advice = fmt.Sprintf(
			"Check SAP before re-running: `sapb1 query %s` — if it returns nothing, the delete went through. "+
				"(Unlike a POST, re-sending a DELETE cannot create a duplicate, but look first)",
			queryHintFor(path))
	}
	msg := fmt.Sprintf(
		"%s %s on %s: the write request was sent but its outcome is unknown — it MAY have been committed in SAP (%s). %s",
		method, path, c.cfg.CompanyDB, why, advice,
	)
	if cause != nil {
		msg += fmt.Sprintf(" [%v]", cause)
	}
	return &errs.WriteOutcomeUnknownError{Msg: msg, Err: cause}
}

// deletePathRe splits "Drafts(54990)" back into set + key, purely so the
// unknown-outcome message can hand the operator a query they can paste.
var deletePathRe = regexp.MustCompile(`^([A-Za-z][A-Za-z0-9_]*)\((\d+)\)$`)

// queryHintFor renders the `sapb1 query` arguments that answer "is it still
// there?" for a keyed path, falling back to the path itself if it isn't one.
func queryHintFor(path string) string {
	m := deletePathRe.FindStringSubmatch(path)
	if m == nil {
		return path
	}
	return fmt.Sprintf("%s --filter \"DocEntry eq %s\"", m[1], m[2])
}

// rawWrite sends one write request. The returned `sent` flag reports whether the
// request bytes made it onto the network before the failure — that is the line
// between "safe to re-run" and "outcome unknown", so it comes from
// httptrace.WroteRequest rather than from pattern-matching an error string.
//
// NOTE: never add an Idempotency-Key (or similar) header here. Go's net/http
// treats a request carrying one as replayable and will silently retry it after a
// connection error — exactly the double-post everything else in this file works
// to prevent. The absence of that header is load-bearing.
func (c *Client) rawWrite(ctx context.Context, method, path string, payload []byte) ([]byte, int, bool, error) {
	var wrote atomic.Bool
	trace := &httptrace.ClientTrace{
		WroteRequest: func(info httptrace.WroteRequestInfo) {
			if info.Err == nil {
				wrote.Store(true)
			}
		},
	}

	req, err := http.NewRequestWithContext(httptrace.WithClientTrace(ctx, trace), method, c.cfg.BaseURL()+path, bytes.NewReader(payload))
	if err != nil {
		return nil, 0, false, fmt.Errorf("building request: %w", err)
	}
	if len(payload) > 0 {
		// A DELETE carries no body; sending Content-Type for zero bytes just
		// invites a fussy proxy to have an opinion about it.
		req.Header.Set("Content-Type", "application/json")
	}
	req.Header.Set("Accept", "application/json")
	c.attachCookies(req)

	resp, err := c.writeClient().Do(req)
	if err != nil {
		// A timeout counts as "sent" even if WroteRequest never fired: the
		// deadline may have struck while the response was in flight.
		if wrote.Load() || isTimeout(err) || errors.Is(err, context.DeadlineExceeded) {
			return nil, 0, true, err
		}
		return nil, 0, false, classifyTransportErr(err, c.cfg)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		// Headers arrived but the body was cut off: SAP has already acted, we
		// just can't read what it said.
		return nil, 0, true, err
	}
	return body, resp.StatusCode, true, nil
}

// writeClient returns the HTTP client used for writes. It exists separately from
// the read client purely for its longer timeout (see config.WriteTimeout).
func (c *Client) writeClient() *http.Client {
	if c.writeHTTP != nil {
		return c.writeHTTP
	}
	transport := &http.Transport{}
	if c.cfg.Insecure {
		transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // #nosec G402 — user opt-in for self-signed SAP certs
	}
	c.writeHTTP = &http.Client{
		Timeout:   time.Duration(c.cfg.WriteTimeout()) * time.Second,
		Transport: transport,
	}
	return c.writeHTTP
}

// isGatewayStatus reports whether status is the kind a proxy or load balancer in
// front of SAP returns when IT, not SAP, gave up.
func isGatewayStatus(status int) bool {
	switch status {
	case http.StatusBadGateway, http.StatusServiceUnavailable, http.StatusGatewayTimeout:
		return true
	}
	return false
}

// isTimeout reports whether err is a timeout, including the
// "Client.Timeout exceeded while awaiting headers" wrapper net/http produces.
func isTimeout(err error) bool {
	var te interface{ Timeout() bool }
	if errors.As(err, &te) && te.Timeout() {
		return true
	}
	return strings.Contains(err.Error(), "Client.Timeout")
}
