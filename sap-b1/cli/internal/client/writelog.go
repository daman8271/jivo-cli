package client

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// Write-log event kinds. Every write produces a pair: the intent line goes out
// BEFORE the request, the outcome line after it resolves. That ordering is the
// point — if the process dies mid-POST (Ctrl-C, OOM, closed laptop), the intent
// line is already on disk, so the operator knows something was sent and has to be
// checked in SAP. An intent with no matching outcome IS the "unknown outcome"
// case, in file form.
const (
	logIntent  = "intent"
	logOutcome = "outcome"
)

// writeLogEntry is one line of the append-only write audit log (JSONL).
//
// "Attempted" here means "the request was put on the wire" — hence the intent
// line. host/port/company_db are on every line so the log can answer the
// question that matters most afterwards: was that production?
//
// On secrets: the SAP login password is never part of an entry, because Login
// never goes through this path. The write PAYLOAD, though, is recorded verbatim
// by design — that's the audit trail — so if an operator writes a field that
// happens to hold a credential, it lands in the log. Hence mode 0600.
type writeLogEntry struct {
	Time           time.Time       `json:"time"`
	Event          string          `json:"event"`
	Host           string          `json:"host"`
	Port           int             `json:"port"`
	CompanyDB      string          `json:"company_db"`
	User           string          `json:"user"`
	Method         string          `json:"method"`
	Path           string          `json:"path"`
	Payload        json.RawMessage `json:"payload,omitempty"`
	PayloadOmitted bool            `json:"payload_omitted,omitempty"`
	Status         *int            `json:"status,omitempty"`
	ResultKey      string          `json:"result_key,omitempty"`
	Error          string          `json:"error,omitempty"`
	// SnapshotSHA256 identifies the object as it read immediately before a
	// DELETE. The snapshot ITSELF is not here: this file is designed to be
	// committed, into a repo that is public, and a snapshot carries the vendor's
	// name, their bill number and every line item with its price. The contents
	// go to the local snapshot log (config.SnapshotLogPath) and this hash points
	// at them — so the shared history still says a specific, verifiable thing was
	// destroyed, and an auditor with access to the machine can prove which.
	//
	// It rides the INTENT line only: the same hash on both lines would double the
	// trail for nothing.
	SnapshotSHA256 string `json:"snapshot_sha256,omitempty"`
	// Overrides names the guards the operator had to switch off by hand, e.g.
	// ["not-created-here"]. Absent means every guard passed on its own.
	Overrides []string `json:"overrides,omitempty"`
	// Origin is the write-log line that vouched this CLI created the object —
	// the exact record that authorised its deletion, kept so a planted line is
	// greppable and attributable afterwards.
	Origin *WriteOrigin `json:"origin,omitempty"`
}

// WriteOrigin points at one line of one write log: the creation record a delete
// was allowed on.
type WriteOrigin struct {
	File string    `json:"file"`
	Line int       `json:"line"`
	User string    `json:"user"`
	Time time.Time `json:"time"`
	Host string    `json:"host,omitempty"`
	Port int       `json:"port,omitempty"`
}

// logExtra is the delete-shaped additions to a log line, plus the policy
// switches that separate an irreversible write from every other one:
// RequireIntent makes the intent line a precondition instead of a courtesy, and
// Shared fans the record out to the checkout's committed log as well.
type logExtra struct {
	SnapshotSHA256 string
	Overrides      []string
	Origin         *WriteOrigin
	RequireIntent  bool
	// Shared says this record must reach the team's committed write log, not
	// only whichever file $SAPB1_WRITE_LOG names.
	//
	// It is a POLICY field and not a verb test on purpose. writeLogTargets used
	// to decide by asking "is this a DELETE?", which was true of every write
	// that needed the guarantee right up until SaveDraftToDocument — a POST that
	// posts a draft to the books and cannot be undone from this CLI. Under the
	// verb test that write would have silently dropped to one local log file,
	// losing the single property that makes an irreversible write auditable, and
	// nothing would have failed to say so.
	Shared bool
	// Unrecordable builds the refusal when RequireIntent is set and the intent
	// line could not be written. It belongs to the caller because the sentence
	// has to name what was refused ("refusing to DELETE Drafts(54990)" /
	// "refusing to ADD Drafts(55126)") and, more importantly, what the operator
	// has lost by it — for a delete that is the only copy of the row, for an Add
	// it is the only local record that we sent it.
	Unrecordable func(path, logPath string, cause error) error
}

// shared reports whether this record fans out to the checkout's committed log.
// A nil extra is a plain Create/Update: one file, the configured one.
func (e *logExtra) shared() bool { return e != nil && e.Shared }

// unrecordable renders the refusal for a write whose intent line could not be
// written. Every caller that sets RequireIntent sets Unrecordable too; the
// fallback exists so a future one that forgets still refuses with something
// truthful rather than borrowing a delete's words for a POST.
func (e *logExtra) unrecordable(path, logPath string, cause error) error {
	if e != nil && e.Unrecordable != nil {
		return e.Unrecordable(path, logPath, cause)
	}
	return &errs.ConfigError{Msg: fmt.Sprintf(
		"refusing to send %s: the write log at %s could not be written (%v).\n"+
			"  This write is only allowed with a record of it. Make that file writable, then re-run",
		path, logPath, cause)}
}

// writeLogTargets lists every file one record must land in.
//
// For an ordinary write (POST/PATCH from draft/post/patch) there is exactly one,
// and $SAPB1_WRITE_LOG picks it: the object survives the write, so a diverted
// log costs an audit line, not the evidence.
//
// A SHARED record also goes to the operator's log inside the checkout, whatever
// the environment says. That is every write this CLI cannot undo — a delete,
// whose record of what was destroyed would otherwise leave with the diverted log
// because there is no SAP row left to query afterwards, and an Add, which puts a
// document in the books that only SAP can reverse. The shared history stops
// being a matter of one variable being unset. The configured log is still
// written too, so a wrapper or a script that tails it keeps working.
//
// shared is a POLICY FLAG the caller sets, never the HTTP verb. See logExtra.Shared.
func writeLogTargets(shared bool) ([]string, error) {
	configured, err := config.WriteLogPath()
	if err != nil {
		return nil, err
	}
	if !shared {
		return []string{configured}, nil
	}
	checkoutLog := config.SharedWriteLogPath()
	if checkoutLog == "" || sameLogFile(checkoutLog, configured) {
		return []string{configured}, nil
	}
	// The checkout's log first: it is the one that has to succeed.
	return []string{checkoutLog, configured}, nil
}

// checkWriteLogTargets proves every file this record must land in can be
// appended to, BEFORE the first line is written. It returns the path that could
// not be opened, or "" when they all could.
//
// It exists because the intent line FANS OUT for a shared record:
// [shared, configured]. Written one file at a time, a failure on the second left
// the first — the committed, shared log — holding an intent line with no
// outcome, and an intent with no outcome is exactly how this tool spells "sent,
// outcome unknown". So a delete that never left the machine published a phantom
// into the team's history and then refused. Opening both first turns that into a
// plain refusal with nothing written.
//
// O_APPEND|O_CREATE|O_WRONLY 0600 is what appendLine itself uses: the point is
// to fail here in exactly the cases it would fail there. The file is created if
// it does not exist, which is what the first real write would have done anyway.
func checkWriteLogTargets(shared bool) (string, error) {
	targets, err := writeLogTargets(shared)
	if err != nil {
		return "(path unresolved)", err
	}
	for _, p := range targets {
		f, err := os.OpenFile(p, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600) // #nosec G304 — resolved by config, never from an argument
		if err != nil {
			return p, err
		}
		if err := f.Close(); err != nil {
			return p, err
		}
	}
	return "", nil
}

// isConfiguredLog reports whether path is the log $SAPB1_WRITE_LOG (or the
// operator default) chose — as opposed to the checkout's shared log, which a
// delete also writes to and which that variable cannot move.
func isConfiguredLog(path string) bool {
	configured, err := config.WriteLogPath()
	if err != nil || configured == "" {
		return false
	}
	return sameLogFile(configured, path)
}

// sameLogFile reports whether two log paths are the same file — by name once
// cleaned, or by inode when both already exist.
//
// One of three path-identity helpers in this CLI that must agree: this one,
// config.sameDirectory (which checkout am I in) and cli.resolvePath/withinAny
// (is this file admissible as evidence). All three answer "the same file, however
// it was spelled" — cleaned strings, then symlinks, then the inode — and a change
// to one belongs in the others.
func sameLogFile(a, b string) bool {
	if a == b {
		return true
	}
	absA, errA := filepath.Abs(a)
	absB, errB := filepath.Abs(b)
	if errA == nil && errB == nil && filepath.Clean(absA) == filepath.Clean(absB) {
		return true
	}
	fa, errA := os.Stat(a)
	fb, errB := os.Stat(b)
	return errA == nil && errB == nil && os.SameFile(fa, fb)
}

// snapshotLogEntry is one line of the LOCAL snapshot log: what a draft held at
// the moment it was destroyed, addressed by the hash the shared write log
// records. It never leaves the machine.
type snapshotLogEntry struct {
	Time      time.Time       `json:"time"`
	SHA256    string          `json:"sha256"`
	Host      string          `json:"host"`
	Port      int             `json:"port"`
	CompanyDB string          `json:"company_db"`
	User      string          `json:"user"`
	Method    string          `json:"method"`
	Path      string          `json:"path"`
	Snapshot  json.RawMessage `json:"snapshot"`
}

// recordSnapshot writes the contents of the object about to be destroyed to the
// local snapshot log and returns the hash that identifies it, plus where it
// went so the operator can be told.
func (c *Client) recordSnapshot(method, path string, snapshot json.RawMessage) (sha, logPath string, err error) {
	logPath, err = config.SnapshotLogPath()
	if err != nil {
		return "", "(path unresolved)", err
	}
	sum := sha256.Sum256(snapshot)
	sha = hex.EncodeToString(sum[:])

	line, err := json.Marshal(snapshotLogEntry{
		Time:      time.Now(),
		SHA256:    sha,
		Host:      c.cfg.Host,
		Port:      c.cfg.Port,
		CompanyDB: c.cfg.CompanyDB,
		User:      c.cfg.User,
		Method:    method,
		Path:      path,
		Snapshot:  snapshot,
	})
	if err != nil {
		return "", logPath, err
	}
	if err := appendLine(logPath, line); err != nil {
		return "", logPath, err
	}
	return sha, logPath, nil
}

// appendWriteLog appends one record to the write log and returns the path it
// wrote to plus whatever went wrong.
//
// For POST/PATCH it still never fails the write itself: the caller ignores the
// error, the operator gets a single stderr warning, and the write keeps its own
// outcome. The return value exists for the one caller that cannot be so
// forgiving — Delete, whose intent line is the only surviving copy of what it is
// about to destroy (see logExtra.RequireIntent).
//
// event is logIntent or logOutcome; status is recorded only on outcome lines,
// since an intent has no outcome yet.
func (c *Client) appendWriteLog(event, method, path string, payload []byte, status int, resultKey string, writeErr error, extra *logExtra) (string, error) {
	targets, err := writeLogTargets(extra.shared())
	if err != nil {
		c.warnWriteLog("(path unresolved)", err)
		return "(path unresolved)", err
	}

	e := writeLogEntry{
		Time:      time.Now(),
		Event:     event,
		Host:      c.cfg.Host,
		Port:      c.cfg.Port,
		CompanyDB: c.cfg.CompanyDB,
		User:      c.cfg.User,
		Method:    method,
		Path:      path,
		ResultKey: resultKey,
	}
	if event == logOutcome {
		st := status
		e.Status = &st
	}
	switch {
	case len(payload) == 0:
		// No body at all (a DELETE): there is nothing to record and nothing was
		// omitted, so say neither.
	case json.Valid(payload):
		e.Payload = json.RawMessage(payload)
	default:
		// Never silently drop it: say a payload existed but wasn't valid JSON.
		e.PayloadOmitted = true
	}
	if extra != nil {
		e.Overrides = extra.Overrides
		e.Origin = extra.Origin
		if event == logIntent {
			e.SnapshotSHA256 = extra.SnapshotSHA256
		}
	}
	if writeErr != nil {
		e.Error = writeErr.Error()
	}

	line, err := json.Marshal(e)
	if err != nil {
		c.warnWriteLog(targets[0], err)
		return targets[0], err
	}

	// Every target gets the line. A failure on any of them is reported — for a
	// DELETE the caller turns that into a refusal, since a delete nobody can read
	// about afterwards is worse than a delete that didn't happen.
	for _, p := range targets {
		if err := appendLine(p, line); err != nil {
			c.warnWriteLog(p, err)
			return p, err
		}
	}
	return targets[0], nil
}

// appendLine appends one line to path, creating it 0600 and tightening a
// pre-existing file that was created too openly — the same belt-and-braces
// Chmod the session cache does.
func appendLine(path string, line []byte) error {
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	defer f.Close()
	if err := f.Chmod(0o600); err != nil {
		return err
	}
	if _, err := f.Write(append(line, '\n')); err != nil {
		return err
	}
	return nil
}

// warnWriteLog tells the operator once, on stderr, that the audit trail is not
// being written. Once per client: at two lines per write, repeating it would just
// be noise.
func (c *Client) warnWriteLog(path string, err error) {
	c.warnOnce.Do(func() {
		c.warn("warning: write log unavailable at %s: %v — the write itself is unaffected, but it is NOT being recorded\n", path, err)
	})
}

// resultKeyFromBody pulls a short human key out of a created/updated object so
// the log line is greppable ("DocEntry=4321", "CardCode=V10000"). Returns ""
// when the body is empty (e.g. HTTP 204) or carries none of the known keys.
func resultKeyFromBody(body []byte) string {
	if len(body) == 0 {
		return ""
	}
	obj, err := decodeObjectExact(body)
	if err != nil {
		return ""
	}
	for _, k := range []string{"DocEntry", "AbsoluteEntry", "CardCode", "ItemCode", "Code"} {
		if v, ok := obj[k]; ok && v != nil {
			return k + "=" + scalarString(v)
		}
	}
	return ""
}

// scalarString renders a JSON scalar the way SAP keys read best: DocEntry
// arrives as a json.Number and should print as 4321 — not 4321.000000, and not
// with digits lost to a float round-trip.
func scalarString(v interface{}) string {
	switch t := v.(type) {
	case string:
		return t
	case json.Number:
		return t.String()
	case float64:
		if t == float64(int64(t)) {
			return strconv.FormatInt(int64(t), 10)
		}
	}
	b, err := json.Marshal(v)
	if err != nil {
		return ""
	}
	return string(b)
}

// decodeObjectExact decodes a JSON object without turning its numbers into
// float64s (json.Number keeps the literal digits), so an 18-digit DocNum or a
// high-precision DocTotal survives inspection unchanged.
func decodeObjectExact(body []byte) (map[string]interface{}, error) {
	dec := json.NewDecoder(bytes.NewReader(body))
	dec.UseNumber()
	var obj map[string]interface{}
	if err := dec.Decode(&obj); err != nil {
		return nil, err
	}
	return obj, nil
}
