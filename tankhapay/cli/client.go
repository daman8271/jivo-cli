package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
	"unicode"
)

// errUnauthorized wraps any 401/403 so commands can print uniform re-login help.
var errUnauthorized = errors.New("unauthorized")

// ------------------------------------------------------------------------
// READ-ONLY GUARDRAIL (layer 2 of 3)
//
// Layer 1: only endpoints classified READ in the vault inventory are ever wired
//          as commands (the generator excludes writes — see captures/
//          reclassified-writes.tsv, cross-checked by guardrail_coverage_test.go).
// Layer 2: forbiddenPath — this function — hard-errors before any request leaves
//          the process if the method+path looks like a write. Fails closed.
// Layer 3: no PUT/PATCH/DELETE path exists in the code at all; doRead only POSTs.
//
// The verb sets below MUST stay in sync with scripts/gen_commands.py so the Go
// guardrail and the generator agree on the exact 287-read / 35-write partition.
// ------------------------------------------------------------------------

// anyWrite: if ANY token of the last path segment is one of these, it is a write.
// These verbs never appear as a noun inside a read's name.
var anyWrite = map[string]bool{
	"create": true, "update": true, "delete": true, "insert": true, "save": true,
	"remove": true, "edit": true, "modify": true, "upsert": true, "approve": true,
	"reject": true, "disburse": true, "cancel": true, "submit": true, "upload": true,
	"generate": true, "revoke": true, "deactivate": true, "relieve": true, "onboard": true,
	"unlock": true, "settle": true, "refund": true, "destroy": true, "regularize": true,
	"otp": true, "deregister": true, "deallocate": true, "recompute": true,
	"recalculate": true, "reprocess": true,
}

// leadingWrite: if the FIRST token of the last path segment is one of these, it is
// a write. These are verbs that ALSO appear as nouns elsewhere, so they only count
// when they lead (e.g. "send_wishes_email" → write; "get_Last_sync_stataus" → read).
var leadingWrite = map[string]bool{
	"send": true, "set": true, "enable": true, "disable": true, "desable": true,
	"sync": true, "verify": true, "reset": true, "resend": true, "initiate": true,
	"toggle": true, "trigger": true, "pay": true, "mark": true, "apply": true,
	"confirm": true, "change": true, "add": true, "close": true, "clear": true,
	"import": true, "export": true, "store": true, "forward": true, "escalate": true,
	"withdraw": true, "release": true, "allocate": true, "assign": true, "publish": true,
	"logout": true, "signout": true, "invite": true, "acknowledge": true, "dispute": true,
	"lock": true, "activate": true, "refresh": true, "deduct": true, "post": true,
	"put": true, "block": true, "unblock": true, "move": true, "copy": true,
	"merge": true, "split": true, "swap": true, "link": true, "unlink": true,
	"enroll": true, "register": true, "process": true, "map": true,
}

// camelTokens splits a segment on _ and - and camelCase boundaries, lowercased.
// "getPayoutTransactionsDetails" → [get payout transactions details];
// "update_employer_mobile_email" → [update employer mobile email];
// "get_Last_sync_stataus" → [get last sync stataus].
func camelTokens(s string) []string {
	var out []string
	var cur []rune
	flush := func() {
		if len(cur) > 0 {
			out = append(out, strings.ToLower(string(cur)))
			cur = cur[:0]
		}
	}
	rs := []rune(s)
	for i, r := range rs {
		if r == '_' || r == '-' || r == '.' {
			flush()
			continue
		}
		if unicode.IsUpper(r) {
			if i > 0 && (unicode.IsLower(rs[i-1]) || unicode.IsDigit(rs[i-1])) {
				flush()
			} else if i > 0 && unicode.IsUpper(rs[i-1]) && i+1 < len(rs) && unicode.IsLower(rs[i+1]) {
				flush()
			}
		}
		cur = append(cur, r)
	}
	flush()
	return out
}

// lastSegment returns the final non-empty path segment of a URL (query stripped).
func lastSegment(rawurl string) string {
	p := rawurl
	if i := strings.IndexByte(p, '?'); i >= 0 {
		p = p[:i]
	}
	p = strings.TrimRight(p, "/")
	if i := strings.LastIndexByte(p, '/'); i >= 0 {
		p = p[i+1:]
	}
	return p
}

// forbiddenPath is the read-only backstop. Returns non-nil for anything that is
// not a plain GET/POST read.
func forbiddenPath(method, url string) error {
	m := strings.ToUpper(method)
	if m != http.MethodGet && m != http.MethodPost {
		return fmt.Errorf("read-only guardrail: HTTP %s is never allowed", m)
	}
	toks := camelTokens(lastSegment(url))
	for _, t := range toks {
		if anyWrite[t] {
			return fmt.Errorf("read-only guardrail: %q is a write (verb %q) — out of scope", url, t)
		}
	}
	if len(toks) > 0 && leadingWrite[toks[0]] {
		return fmt.Errorf("read-only guardrail: %q is a write (leading verb %q) — out of scope", url, toks[0])
	}
	return nil
}

// ------------------------------------------------------------------------
// Client — AES-ECB body cipher + Bearer JWT over the four backends.
// ------------------------------------------------------------------------

type Client struct {
	cfg       Config
	hc        *http.Client
	token     string
	ctx       AccountCtx
	attempted bool // capped: at most one interactive login per process run
}

func newClient(cfg Config) *Client {
	return &Client{cfg: cfg, hc: &http.Client{Timeout: 90 * time.Second}}
}

func (c *Client) setHeaders(req *http.Request, auth bool) {
	req.Header.Set("accept", "application/json, text/plain, */*")
	req.Header.Set("content-type", "application/json")
	req.Header.Set("user-agent", "tankhapay-portal/1.0 (read-only)")
	if auth && c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
}

// rawPost sends one POST and returns (body, status). No guardrail here — callers
// (doRead / doLogin) apply the guardrail and envelope handling.
func (c *Client) rawPost(url string, body []byte, auth bool) ([]byte, int, error) {
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, 0, err
	}
	c.setHeaders(req, auth)
	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return b, resp.StatusCode, nil
}

// doRead is the one and only data path: guardrail → ensure token → AES-wrap the
// payload → POST → decrypt commonData. Auto-relogins once on 401.
func (c *Client) doRead(backendKey, relPath string, payload []byte) (json.RawMessage, error) {
	base, ok := c.cfg.Backends[backendKey]
	if !ok {
		return nil, fmt.Errorf("unknown backend %q", backendKey)
	}
	url := joinURL(base, relPath)
	if err := forbiddenPath(http.MethodPost, url); err != nil {
		return nil, err
	}
	if err := c.ensureAuth(); err != nil {
		return nil, err
	}
	enc, err := aesECBEncrypt(c.cfg.BodyKey, payload)
	if err != nil {
		return nil, err
	}
	envBody := mustJSON(map[string]string{"encrypted": enc})

	raw, status, err := c.rawPost(url, envBody, true)
	if err != nil {
		return nil, err
	}
	if status == http.StatusUnauthorized || status == http.StatusForbidden {
		if rlErr := c.relogin(); rlErr == nil {
			raw, status, err = c.rawPost(url, envBody, true)
			if err != nil {
				return nil, err
			}
		}
	}
	if status == http.StatusUnauthorized || status == http.StatusForbidden {
		return nil, fmt.Errorf("%s → HTTP %d: %w", url, status, errUnauthorized)
	}
	if status < 200 || status >= 300 {
		snip := string(raw)
		if len(snip) > 300 {
			snip = snip[:300]
		}
		return nil, fmt.Errorf("%s → HTTP %d: %s", url, status, snip)
	}
	return c.decodeEnvelope(raw)
}

// decodeEnvelope unwraps {code,statusCode,message,commonData}. commonData is
// usually an AES-ECB base64 string; a few endpoints return it already-plain
// (array/object) — both are handled. A non-envelope body is returned verbatim.
func (c *Client) decodeEnvelope(raw []byte) (json.RawMessage, error) {
	var env struct {
		Code       string          `json:"code"`
		StatusCode json.RawMessage `json:"statusCode"`
		Message    json.RawMessage `json:"message"` // may be a string OR an object
		CommonData json.RawMessage `json:"commonData"`
	}
	if err := json.Unmarshal(raw, &env); err != nil {
		return json.RawMessage(raw), nil
	}
	// 1. Usable commonData wins: decrypt an AES string, or pass through structured JSON.
	if len(env.CommonData) > 0 {
		var s string
		if json.Unmarshal(env.CommonData, &s) == nil {
			if strings.TrimSpace(s) != "" {
				plain, err := aesECBDecrypt(c.cfg.BodyKey, s)
				if err != nil {
					return nil, fmt.Errorf("decrypt commonData: %w", err)
				}
				return json.RawMessage(plain), nil
			}
		} else {
			return env.CommonData, nil // already structured
		}
	}
	// 2. No data. If the envelope signals failure, surface it as a clean error
	//    (bad params / server error) instead of a confusing raw envelope or null.
	sc := strings.Trim(string(env.StatusCode), `"`)
	if strings.EqualFold(sc, "false") || strings.HasPrefix(env.Code, "TP-4") || strings.HasPrefix(env.Code, "TP-5") {
		msg := strings.TrimSpace(string(env.Message))
		if len(msg) > 200 {
			msg = msg[:200]
		}
		return nil, fmt.Errorf("API %s: %s", env.Code, msg)
	}
	// 3. Genuine empty success (TP-200 with no rows).
	return json.RawMessage("null"), nil
}
