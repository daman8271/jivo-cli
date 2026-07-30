package main

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

const userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " +
	"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

var errUnauthorized = errors.New("unauthorized (401/403) — the Flipkart session is dead; " +
	"re-run the production login on HO-IT-PC10, this CLI never mints a session")

// LAYER 1 — TRANSPORT GUARD.
// The only method this client will ever put on the wire is GET. Any other verb
// throws before a socket opens. There is no login path here: this CLI consumes an
// existing session cookie jar (G9) and only reads.
func guardMethod(method string) error {
	if method != http.MethodGet {
		return fmt.Errorf("read-only CLI: method %q is refused by the transport guard "+
			"(only GET is ever sent)", method)
	}
	return nil
}

// writeVerbs are path segments that denote a mutation. LAYER-2 backstop: even a GET
// is refused if its path looks like a write, so an accidental future miswiring of a
// write path as a GET command still cannot fire.
var writeVerbs = map[string]bool{
	"create": true, "update": true, "delete": true, "remove": true, "edit": true,
	"modify": true, "upsert": true, "insert": true, "save": true, "submit": true,
	"upload": true, "import": true, "cancel": true, "approve": true, "reject": true,
	"acknowledge": true, "confirm": true, "accept": true, "decline": true,
	"schedule": true, "reschedule": true, "unschedule": true, "assign": true,
	"revoke": true, "dispute": true, "adjust": true, "pay": true, "payout": true,
	"settle": true, "refund": true, "activate": true, "deactivate": true,
	"enable": true, "disable": true, "pause": true, "resume": true, "publish": true,
	"logout": true, "signout": true, "generate": true, "toggle": true, "trigger": true,
	"invite": true, "reinvite": true, "sync": true, "send": true, "book": true,
	"register": true, "suspend": true, "createfsn": true, "createvariant": true,
	"add": true,
}

// camelCaseWriteVerbs are matched as a SUBSTRING of a segment, to catch minified
// camelCase mutations like "generateReport" or "submitSurvey" that carry no
// hyphen/slash boundary. Kept to strong verbs verified (2026-07-30) not to occur
// inside any wired READ path, so they cannot false-positive a real read.
// NOTE: "suspend"/"activate"/"deactivate" are deliberately NOT here — they are
// exact-segment verbs in writeVerbs (matching "user-activation/suspend"), and as
// substrings they would wrongly flag the READ path "users/suspended".
var camelCaseWriteVerbs = []string{
	"generate", "create", "update", "delete", "upload", "submit", "approve",
	"reject", "cancel", "remove", "publish",
}

func segmentIsWrite(seg string) bool {
	seg = strings.ToLower(seg)
	if writeVerbs[seg] {
		return true
	}
	for _, part := range strings.Split(seg, "-") {
		if writeVerbs[part] {
			return true
		}
	}
	for _, v := range camelCaseWriteVerbs {
		if strings.Contains(seg, v) {
			return true
		}
	}
	return false
}

// forbiddenPath — LAYER 2. Refuses a path whose segments contain a write verb.
func forbiddenPath(method, rawurl string) error {
	if err := guardMethod(method); err != nil {
		return err
	}
	u, err := url.Parse(rawurl)
	if err != nil {
		return fmt.Errorf("unparseable url %q: %w", rawurl, err)
	}
	for _, seg := range strings.Split(u.Path, "/") {
		if seg == "" || strings.HasPrefix(seg, "{") {
			continue
		}
		if segmentIsWrite(seg) {
			return fmt.Errorf("read-only guardrail: path segment %q in %s looks like a write; refused",
				seg, u.Path)
		}
	}
	return nil
}

type Client struct{ hc *http.Client }

func newClient() *Client { return &Client{hc: &http.Client{Timeout: 60 * time.Second}} }

// cookieForHost returns the session cookie jar for a host from the environment.
// Values never appear in code or output; they live only in the process env.
func cookieForHost(host string) (cookie, csrf string) {
	if strings.Contains(host, "vendorhub") {
		return os.Getenv("FLIPKART_VENDOR_COOKIE"), os.Getenv("FLIPKART_VENDOR_CSRF")
	}
	return os.Getenv("FLIPKART_SELLER_COOKIE"), os.Getenv("FLIPKART_SELLER_CSRF")
}

// GET performs the one and only kind of request this CLI makes.
func (c *Client) GET(host, path string, params map[string]string) ([]byte, int, error) {
	scheme := "https://"
	q := url.Values{}
	for k, v := range params {
		q.Set(k, v)
	}
	full := scheme + host + path
	if len(q) > 0 {
		sep := "?"
		if strings.Contains(path, "?") {
			sep = "&"
		}
		full += sep + q.Encode()
	}
	if err := forbiddenPath(http.MethodGet, full); err != nil {
		return nil, 0, err
	}
	req, err := http.NewRequest(http.MethodGet, full, nil)
	if err != nil {
		return nil, 0, err
	}
	cookie, csrf := cookieForHost(host)
	if cookie != "" {
		req.Header.Set("Cookie", cookie)
	}
	if csrf != "" {
		req.Header.Set("x-csrf-token", csrf)
	}
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "application/json, text/plain, */*")
	req.Header.Set("Referer", scheme+host+"/")
	req.Header.Set("X-Requested-With", "XMLHttpRequest")
	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	body, rerr := io.ReadAll(resp.Body)
	if rerr != nil {
		return nil, resp.StatusCode, rerr
	}
	if resp.StatusCode == 401 || resp.StatusCode == 403 {
		return body, resp.StatusCode, errUnauthorized
	}
	return body, resp.StatusCode, nil
}
