package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

var errUnauthorized = errors.New("unauthorized")

// ---------------------------------------------------------------------------
// LAYER 1 of the read-only guardrail: the transport.
//
// forbiddenRequest is consulted before a socket is ever opened. It enforces:
//   a. method allowlist — only GET and POST. Swiggy serves most READS over POST
//      (list/search/metrics), so POST cannot be banned outright; PUT, PATCH and
//      DELETE have no read use on this portal and are refused unconditionally.
//   b. path allowlist — the URL must match a row classified READ/READ_FILE in
//      vault/Swiggy-Instamart-Endpoints.md. That list is generated into
//      allowlist.go from captures/endpoints-raw.tsv, so the CLI cannot reach an
//      endpoint the study did not prove is a read.
//   c. a hard denylist of the endpoints that must never fire even if a future
//      edit mistakenly allowlists them.
// ---------------------------------------------------------------------------

// hardDeny is belt-and-braces over the allowlist: these are the paths whose
// firing would be actively harmful, listed explicitly so a bad edit still fails.
var hardDeny = []string{
	"/v1/token/refresh",       // rotates a SINGLE-USE token -> breaks the live session + cron
	"/v1/accounts/signout",    // logs the human out
	"/v1/accounts/signin",     // mints a session (G9)
	"/v1/accounts/createauthuri",
	"/v1/accounts/sendverificationcode", // mails a real OTP
	"/api/v1/batch/submit",              // enqueues a bulk job despite its DOWNLOAD constant
	"/instamart/v1/creative/get-upload-info-v2", // hands back S3 upload credentials
	"/api/v1/fc-appointment/",                   // books / reschedules / cancels a real delivery
	"/api/v1/external/indent/accept",
	"/api/v1/external/indent/reject",
	"/api/v1/external/indent/item/update",
	"/api/v1/release-order/approve",
	"/api/v1/campaign/pause",
	"/api/v1/campaign/resume",
	"/instamart/v1/campaign/create",
	"/instamart/v1/campaign/update",
	"/instamart/v1/campaign/deactivate",
	"/api/v1/sales/report",                      // GENERATE (enqueue) — G2
	"/instamart/v1/report/initiate-sales-report", // GENERATE — G2
	"/instamart/v1/report/initiate-bdpo-report",  // GENERATE — G2
	"/api/v1/discounts/report",                   // GENERATE — G2
	"/api/v1/advertiser/metrics/report",          // GENERATE — G2 (note: /report/list IS a read)
	"/api/v1/document/batch/generate",
	"/api/v1/document/merged/generate",
	"/v1/generate_signed_url",
	"/v1/create_spin_change_request",
	"/v1/reassign_spin_change_request",
	"/v1/update_spin_change_workflow",
	"/api/discounting/v1/campaign/disable",
}

func forbiddenRequest(method, rawURL string) error {
	m := strings.ToUpper(method)
	if m != http.MethodGet && m != http.MethodPost {
		return fmt.Errorf("read-only guardrail: HTTP %s is never allowed by this CLI", m)
	}
	u, err := url.Parse(rawURL)
	if err != nil {
		return fmt.Errorf("read-only guardrail: unparseable URL %q", rawURL)
	}
	p := strings.ToLower(u.Path)

	for _, d := range hardDeny {
		// "/api/v1/advertiser/metrics/report" must not shadow ".../report/list"
		if p == strings.TrimSuffix(d, "/") || strings.HasPrefix(p, d) {
			if p == strings.TrimSuffix(d, "/") || strings.HasSuffix(d, "/") {
				return fmt.Errorf("read-only guardrail: %q is on the hard denylist "+
					"(write/enqueue/session endpoint) and is never called", u.Path)
			}
		}
	}
	if !isAllowedRead(u.Host, u.Path) {
		return fmt.Errorf("read-only guardrail: %s%s is not on the READ allowlist "+
			"generated from the study (see vault/Swiggy-Instamart-Endpoints.md). "+
			"Deny-by-default: only proven reads are reachable", u.Host, u.Path)
	}
	return nil
}

// ---------------------------------------------------------------------------

type Client struct {
	cfg Config
	hc  *http.Client
}

func newClient(cfg Config) *Client {
	return &Client{cfg: cfg, hc: &http.Client{Timeout: 90 * time.Second}}
}

// signingPepper is the 32-char constant embedded in Swiggy's media_loader.wasm.
// It is a SECRET and is deliberately NOT in this repo (G6). It is read at runtime
// from the environment or from JIVO's existing signer directory. Without it, calls
// to brand-portal-service-http cannot be signed and will 403.
func signingPepper() string {
	return os.Getenv("SWIGGY_SIGN_PEPPER")
}

// appVersion is server-validated and has moved over time (1.4.122 → 0.0.32/0.0.34
// observed). Overridable because a stale value returns "App version update required".
func appVersion() string {
	if v := os.Getenv("SWIGGY_APP_VERSION"); v != "" {
		return v
	}
	return "0.0.34"
}

// serverTimeMillis fetches Swiggy's clock. Signing embeds a server-synced ms
// timestamp, and a local clock that is even slightly off is rejected.
func (c *Client) serverTimeMillis() int64 {
	resp, err := c.hc.Get(hostPartnerAPI + "/time")
	if err == nil {
		defer resp.Body.Close()
		var v struct {
			Timestamp int64 `json:"timestamp"`
		}
		if json.NewDecoder(resp.Body).Decode(&v) == nil && v.Timestamp > 0 {
			return v.Timestamp
		}
	}
	return time.Now().UnixMilli()
}

// sign reproduces the portal's request signature:
//
//	x_signature = HMAC_SHA256(PEPPER ‖ requestId ‖ sessionId,
//	                          JSON.stringify(appVersion + timestamp + requestId))
//
// sessionId is the CURRENT access token's session_id claim and must be fresh.
func sign(pepper, requestID, sessionID, appVer, tsMillis string) string {
	msg, _ := json.Marshal(appVer + tsMillis + requestID)
	mac := hmac.New(sha256.New, []byte(pepper+requestID+sessionID))
	mac.Write(msg)
	return hex.EncodeToString(mac.Sum(nil))
}

// setHeaders applies the right auth scheme for the host.
//
//	picker.swiggy.com          -> Abacus-Token: <jwt>      (the vendor lane)
//	everything else            -> authorization: Bearer <jwt>
//
// and adds the signing headers for brand-portal-service-http.
func (c *Client) setHeaders(req *http.Request, host string, hasBody bool) {
	req.Header.Set("accept", "application/json, text/plain, */*")
	req.Header.Set("origin", originHeader)
	req.Header.Set("referer", refererHeader)
	req.Header.Set("user-agent", userAgent)
	if hasBody {
		req.Header.Set("content-type", "application/json")
	}

	if strings.Contains(host, "picker.swiggy.com") {
		tok := c.cfg.SupplyToken
		if tok == "" {
			tok = c.cfg.Token
		}
		req.Header.Set("Abacus-Token", tok)
		return
	}

	tok := c.cfg.Token
	if tok == "" {
		tok = c.cfg.SupplyToken
	}
	req.Header.Set("authorization", "Bearer "+tok)
	req.Header.Set("x-client-id", "IM_BRAND_PORTAL_EXTERNAL_DASHBOARD")

	if strings.Contains(host, "brand-portal-service-http") {
		rid := newRequestID()
		ts := strconv.FormatInt(c.serverTimeMillis(), 10)
		sid, _ := sessionIDFromJWT(tok)
		req.Header.Set("app_version", appVersion())
		req.Header.Set("x-client-request-id", rid)
		req.Header.Set("x-timestamp", ts)
		if p := signingPepper(); p != "" && sid != "" {
			req.Header.Set("x-signature", sign(p, rid, sid, appVersion(), ts))
		}
	}
}

// do performs one allowlisted read and returns the raw body.
func (c *Client) do(method, rawURL string, body []byte) (json.RawMessage, error) {
	if err := forbiddenRequest(method, rawURL); err != nil {
		return nil, err
	}
	var rdr io.Reader
	if body != nil {
		rdr = bytes.NewReader(body)
	}
	req, err := http.NewRequest(method, rawURL, rdr)
	if err != nil {
		return nil, err
	}
	c.setHeaders(req, req.URL.Host, body != nil)

	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)

	switch {
	case resp.StatusCode == http.StatusUnauthorized:
		return nil, fmt.Errorf("%s %s → 401: %w — the inherited session has expired. "+
			"This CLI will not re-login (G9); a human must refresh it", method, rawURL, errUnauthorized)
	case resp.StatusCode == http.StatusForbidden:
		hint := ""
		if bytes.Contains(raw, []byte("reload the browser")) {
			hint = " — this is Swiggy's session-activation wall: a hand-built request is " +
				"rejected even when correctly signed (see vault/_meta/Auth-and-Access.md §5). " +
				"Use the portal walk captures instead"
		}
		return nil, fmt.Errorf("%s %s → 403%s: %w", method, rawURL, hint, errUnauthorized)
	case resp.StatusCode < 200 || resp.StatusCode >= 300:
		snip := string(raw)
		if len(snip) > 400 {
			snip = snip[:400]
		}
		return nil, fmt.Errorf("%s %s → HTTP %d: %s", method, rawURL, resp.StatusCode, snip)
	}
	return raw, nil
}

// downloadPresigned fetches an already-completed report from its presigned S3 URL.
// The presign IS the auth, so no headers are sent. This is a READ_FILE: it consumes
// an artifact a human already generated. Generating one is a WRITE and has no
// command in this CLI.
func (c *Client) downloadPresigned(rawURL, outPath string) (int64, error) {
	u, err := url.Parse(rawURL)
	if err != nil {
		return 0, err
	}
	if !strings.HasSuffix(u.Host, ".amazonaws.com") {
		return 0, fmt.Errorf("refusing to download from %q: only presigned S3 report URLs "+
			"are allowed here", u.Host)
	}
	resp, err := c.hc.Get(rawURL)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("download → HTTP %d (a presigned URL expires; re-list to get a fresh one)",
			resp.StatusCode)
	}
	f, err := os.Create(outPath)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	return io.Copy(f, resp.Body)
}
