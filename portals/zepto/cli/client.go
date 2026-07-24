package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// errUnauthorized is returned (wrapped) whenever the API answers 401/403 so any
// command can print uniform re-login guidance. Zepto's JWT is daily.
var errUnauthorized = errors.New("unauthorized")

// Client talks to any Zepto backend host with the single-JWT bearer scheme.
type Client struct {
	cfg Config
	hc  *http.Client
}

func newClient(cfg Config) *Client {
	return &Client{cfg: cfg, hc: &http.Client{Timeout: 90 * time.Second}}
}

// writeVerbs are path SEGMENTS (or hyphen-bounded parts of a segment) that
// unambiguously denote a mutation. Matching is segment-boundary aware so a read
// like ".../po/scheduled" is NOT confused with the write ".../po/schedule".
var writeVerbs = map[string]bool{
	"create": true, "update": true, "delete": true, "remove": true, "edit": true,
	"modify": true, "upsert": true, "insert": true, "save": true, "submit": true,
	"upload": true, "cancel": true, "approve": true, "reject": true, "acknowledge": true,
	"schedule": true, "reschedule": true, "unschedule": true, "assign": true,
	"revoke": true, "dispute": true, "pay": true, "payout": true, "settle": true,
	"refund": true, "activate": true, "deactivate": true, "enable": true,
	"disable": true, "publish": true, "logout": true, "signout": true, "sign-out": true,
	"counterpart": true,
	// added after adversarial review — mutating verbs that appear in the
	// portal's out-of-scope write table but lacked a matching segment before:
	"initiate": true, "send": true, "sign-in": true, "signin": true, "reset": true,
	"resend": true, "reinvite": true, "invite": true, "sync": true, "feedback": true,
	"impersonation": true, "impersonate": true, "subscribe": true, "draft": true,
	"generate": true, "toggle": true, "trigger": true,
}

// segmentIsWrite reports whether a path segment denotes a write. It matches the
// whole segment, or any HYPHEN-delimited part of it, against the verb set — so
// "ledger-upload" (→upload), "request-schedule" (→schedule), "modify-access-…"
// (→modify) and "failure-upload-csv" (→upload) are all caught. It deliberately
// does NOT split on underscore: Zepto uses hyphens for path verbs but underscores
// for descriptive config keys, so "quick_edit_form_metadata" and
// "create_campaign_modal_subtype_image_map" (both /layout/config/* READS) must
// pass. "scheduled", "vendor-list", "external-view-status" pass too.
func segmentIsWrite(seg string) bool {
	if writeVerbs[seg] {
		return true
	}
	for _, part := range strings.Split(seg, "-") {
		if writeVerbs[part] {
			return true
		}
	}
	return false
}

// forbiddenPath is the read-only guardrail: a best-effort backstop that
// hard-errors BEFORE any request leaves the process when the method+URL looks
// like a write. It is NOT an exhaustive proof — a mutating endpoint whose path
// contains no write-verb segment (e.g. ".../wallet/payment/initiate") would pass
// it. The REAL guarantee is upstream: only READ-classified endpoints from the
// vault inventory are ever wired as commands (see each cmd_*.go). This layer
// exists to catch an accidental future miswiring, not to sanction one.
//
// Report GENERATION (POST .../reports/request, .../brands/analytics/reports) has
// no write-verb segment, so it passes here — it is instead gated behind an
// explicit --export flag at the command layer (it only creates a queue row).
func forbiddenPath(method, url string) error {
	m := strings.ToUpper(method)
	// 1. HTTP method allowlist: only GET and POST are ever legitimate.
	if m != http.MethodGet && m != http.MethodPost {
		return fmt.Errorf("read-only guardrail: HTTP %s is never allowed", m)
	}
	// 2. Segment-boundary write-verb scan over the path only (query stripped).
	path := strings.ToLower(url)
	if i := strings.IndexByte(path, '?'); i >= 0 {
		path = path[:i]
	}
	if i := strings.Index(path, "://"); i >= 0 {
		if j := strings.IndexByte(path[i+3:], '/'); j >= 0 {
			path = path[i+3+j:]
		} else {
			path = ""
		}
	}
	for _, seg := range strings.Split(path, "/") {
		if seg == "" {
			continue
		}
		if segmentIsWrite(seg) {
			return fmt.Errorf("read-only guardrail: write endpoint %q (segment %q) is out of scope", url, seg)
		}
	}
	return nil
}

// setHeaders applies the minimal working Zepto auth: one JWT in `authorization`
// (no Bearer prefix). WAF headers are not enforced. UA + accept mirror a browser.
func (c *Client) setHeaders(req *http.Request, hasBody bool) {
	req.Header.Set("accept", "application/json, text/plain, */*")
	req.Header.Set("authorization", c.cfg.JWT)
	req.Header.Set("user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36")
	if hasBody {
		req.Header.Set("content-type", "application/json")
	}
}

// doRaw performs an authenticated request, checks the HTTP status, and returns
// the raw body with NO envelope assumption (Zepto response shapes vary by host).
func (c *Client) doRaw(method, url string, body []byte) (json.RawMessage, error) {
	if err := forbiddenPath(method, url); err != nil {
		return nil, err
	}
	var rdr io.Reader
	if body != nil {
		rdr = bytes.NewReader(body)
	}
	req, err := http.NewRequest(method, url, rdr)
	if err != nil {
		return nil, err
	}
	c.setHeaders(req, body != nil)

	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)

	if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden {
		return nil, fmt.Errorf("%s %s → HTTP %d: %w", method, url, resp.StatusCode, errUnauthorized)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		snippet := string(raw)
		if len(snippet) > 300 {
			snippet = snippet[:300]
		}
		return nil, fmt.Errorf("%s %s → HTTP %d: %s", method, url, resp.StatusCode, snippet)
	}
	return raw, nil
}

// download fetches an authenticated binary and writes it to outPath.
func (c *Client) download(method, url string, body []byte, outPath string) (int64, error) {
	if err := forbiddenPath(method, url); err != nil {
		return 0, err
	}
	var rdr io.Reader
	if body != nil {
		rdr = bytes.NewReader(body)
	}
	req, err := http.NewRequest(method, url, rdr)
	if err != nil {
		return 0, err
	}
	c.setHeaders(req, body != nil)
	resp, err := c.hc.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden {
		return 0, fmt.Errorf("%s %s → HTTP %d: %w", method, url, resp.StatusCode, errUnauthorized)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return 0, fmt.Errorf("%s %s → HTTP %d", method, url, resp.StatusCode)
	}
	f, err := os.Create(outPath)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	return io.Copy(f, resp.Body)
}

// downloadURL fetches a presigned S3 URL (no auth headers) to outPath.
func (c *Client) downloadURL(url, outPath string) (int64, error) {
	resp, err := c.hc.Get(url)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("download → HTTP %d", resp.StatusCode)
	}
	f, err := os.Create(outPath)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	return io.Copy(f, resp.Body)
}
