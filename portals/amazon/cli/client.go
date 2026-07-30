package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// Client is the Amazon portal read-only HTTP client. It is deliberately
// minimal and GET-only. There is no code path in this binary that can issue a
// POST, PUT, PATCH, or DELETE — see doRaw / forbidden.
type Client struct {
	cfg Config
	hc  *http.Client
}

func newClient(cfg Config) *Client {
	return &Client{cfg: cfg, hc: &http.Client{
		Timeout: 60 * time.Second,
		// never follow a redirect to a login page automatically; surface it
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if strings.Contains(req.URL.String(), "/ap/signin") {
				return fmt.Errorf("redirected to sign-in — session expired (run `amazon-portal doctor`)")
			}
			return nil
		},
	}}
}

// allowlistIndex is the set of exact allowlisted paths (placeholders normalised)
// built once from readEndpoints. Layer-2 guardrail: a GET is refused unless its
// path template is a READ/READ_FILE row.
var allowlistIndex = func() map[string]bool {
	m := make(map[string]bool, len(readEndpoints))
	for _, e := range readEndpoints {
		m[e.Host+"|"+e.Path] = true
	}
	return m
}()

// forbidden is the three-part read-only guardrail, deny-by-default. It runs
// BEFORE any socket opens.
//
//  1. Method allowlist — only GET is ever legal in this binary.
//  2. Never a sign-out or token-rotation path (self-preservation).
//  3. Path must resolve to a READ/READ_FILE allowlist template.
func forbidden(method, host, pathTemplate string) error {
	if strings.ToUpper(method) != http.MethodGet {
		return fmt.Errorf("read-only guardrail: HTTP %s is never allowed (this CLI is GET-only)", method)
	}
	lp := strings.ToLower(pathTemplate)
	for _, bad := range []string{"signout", "sign-out", "logout", "token/refresh", "refresh-token", "rotate"} {
		if strings.Contains(lp, bad) {
			return fmt.Errorf("read-only guardrail: %q is a session-mutating path and is refused", pathTemplate)
		}
	}
	// segment-boundary write-verb scan (defence in depth even though only reads are wired)
	clean := lp
	if i := strings.IndexByte(clean, '?'); i >= 0 {
		clean = clean[:i]
	}
	for _, seg := range strings.Split(clean, "/") {
		for _, part := range strings.Split(seg, "-") {
			if writeVerbs[part] {
				return fmt.Errorf("read-only guardrail: path segment %q denotes a write; %q is out of scope", part, pathTemplate)
			}
		}
	}
	if !allowlistIndex[host+"|"+pathTemplate] {
		return fmt.Errorf("read-only guardrail: %s %s is not in the READ allowlist (deny-by-default)", host, pathTemplate)
	}
	return nil
}

// writeVerbs — path segments that unambiguously denote a mutation. Used as a
// backstop; the real guarantee is that only READ rows are ever wired.
var writeVerbs = map[string]bool{
	"create": true, "update": true, "delete": true, "remove": true, "edit": true,
	"modify": true, "save": true, "submit": true, "upload": true, "cancel": true,
	"approve": true, "reject": true, "acknowledge": true, "confirm": true,
	"schedule": true, "activate": true, "deactivate": true, "pause": true,
	"resume": true, "pay": true, "settle": true, "dispute": true, "generate": true,
	"invite": true, "sync": true, "import": true, "publish": true, "logout": true,
	"signout": true, "signin": true, "write": true, "clone": true, "relist": true,
}

// get performs an allowlisted, guarded GET against host+resolvedPath. resolvedPath
// is the concrete path (placeholders already substituted); pathTemplate is the
// allowlist key it came from (with placeholders) used for the guardrail check.
func (c *Client) get(host, pathTemplate, resolvedPath string) (json.RawMessage, int, error) {
	if err := forbidden(http.MethodGet, host, pathTemplate); err != nil {
		return nil, 0, err
	}
	url := "https://" + host + resolvedPath
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, 0, err
	}
	c.setHeaders(req)
	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if resp.StatusCode == 401 || resp.StatusCode == 403 {
		return nil, resp.StatusCode, fmt.Errorf("HTTP %d — session expired or insufficient rights (run `amazon-portal doctor`)", resp.StatusCode)
	}
	if resp.StatusCode >= 400 {
		return nil, resp.StatusCode, fmt.Errorf("HTTP %d for %s", resp.StatusCode, pathTemplate)
	}
	// content-sniff: Amazon returns an HTML sign-in shell with 200 on expiry
	trimmed := strings.TrimSpace(string(body))
	if strings.HasPrefix(strings.ToLower(trimmed), "<!doctype") || strings.HasPrefix(trimmed, "<html") {
		return nil, resp.StatusCode, fmt.Errorf("got an HTML page, not JSON — session likely expired (run `amazon-portal doctor`)")
	}
	return json.RawMessage(body), resp.StatusCode, nil
}

// setHeaders applies the consumed (never minted) Seller Central cookie session.
func (c *Client) setHeaders(req *http.Request) {
	req.Header.Set("accept", "application/json, text/plain, */*")
	req.Header.Set("accept-language", "en-GB,en-US;q=0.9,en;q=0.8")
	req.Header.Set("user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36")
	if c.cfg.Cookie != "" {
		req.Header.Set("cookie", c.cfg.Cookie)
	}
}
