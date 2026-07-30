package client

import (
	"bytes"
	"encoding/json"
	"os"
	"strconv"
	"time"

	"sapb1/internal/config"
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
}

// appendWriteLog appends one record to the write log. It never fails the write
// itself: if the log can't be written the operator gets a single stderr warning
// and the write keeps its own outcome. event is logIntent or logOutcome; status
// is recorded only on outcome lines, since an intent has no outcome yet.
func (c *Client) appendWriteLog(event, method, path string, payload []byte, status int, resultKey string, writeErr error) {
	logPath, err := config.WriteLogPath()
	if err != nil {
		c.warnWriteLog("(path unresolved)", err)
		return
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
	if json.Valid(payload) {
		e.Payload = json.RawMessage(payload)
	} else {
		// Never silently drop it: say a payload existed but wasn't valid JSON.
		e.PayloadOmitted = true
	}
	if writeErr != nil {
		e.Error = writeErr.Error()
	}

	line, err := json.Marshal(e)
	if err != nil {
		c.warnWriteLog(logPath, err)
		return
	}

	if err := appendLine(logPath, line); err != nil {
		c.warnWriteLog(logPath, err)
	}
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
