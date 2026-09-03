// Package client is a minimal HTTP client for the SAP Business One Service
// Layer (b1s/v1). It handles Login/Logout, session-cookie management (with
// on-disk caching + transparent one-shot re-login on 401), and generic OData
// reads.
//
// Beyond reads it exposes exactly four write operations — Create (POST), Update
// (PATCH), Delete (DELETE) and SaveDraftToDocument (POST) — and nothing else:
// there is no PUT, and SaveDraftToDocument is the only OData function this
// client will call. Two of the four are narrower than their verb suggests:
// Delete refuses every entity set outside deletableSets (Drafts,
// PaymentDrafts), so "DELETE Invoices(9)" cannot be expressed from anywhere in
// this binary, not just from the command tree; and SaveDraftToDocument builds a
// constant path, so it reaches Drafts and no other document.
//
// SaveDraftToDocument is the one write here with no way back. It presses Add on
// a draft — the document enters the books, stock moves, a ledger moves — and
// nothing in this binary reverses it. It is treated accordingly: its record is a
// precondition and it always reaches the team's shared write log (see
// logExtra.Shared).
//
// All four are reached only from the operator-invoked write commands
// (`sapb1 draft`, `sapb1 post`, `sapb1 patch`, `sapb1 delete draft`,
// `sapb1 add-draft`), each of which previews the request and asks for
// confirmation first. Every attempted write is appended to a local audit log
// (see writelog.go). Everything else in this package is a GET.
package client

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// Client talks to one SAP B1 Service Layer instance described by cfg.
type Client struct {
	cfg  *config.Config
	http *http.Client
	// writeHTTP is built on first write; it differs from http only in having the
	// longer write timeout (see config.WriteTimeout).
	writeHTTP *http.Client

	b1Session  string
	routeID    string
	loggedInAt time.Time

	// sessions, when non-nil, shares this Client's session with every other
	// Client in the process that has the same host/port/companyDB/user. It is
	// what stops a burst of concurrent MCP tool calls from opening one SAP
	// session each (see sessions.go). nil means "no sharing", which is the right
	// thing for a one-shot CLI process.
	sessions *SessionStore

	// errOut receives the one non-fatal warning this package can emit (the write
	// log being unwritable). Defaults to os.Stderr.
	errOut   io.Writer
	warnOnce sync.Once
}

// New builds a Client from cfg. It does not perform any I/O.
func New(cfg *config.Config) *Client {
	return NewWithSessions(cfg, nil)
}

// NewWithSessions builds a Client that shares sessions with every other Client
// created from the same store and the same connection identity. Long-lived,
// concurrent hosts (the MCP server) pass a store; one-shot CLI commands pass
// nil via New.
func NewWithSessions(cfg *config.Config, sessions *SessionStore) *Client {
	transport := &http.Transport{
		// Honour HTTPS_PROXY / NO_PROXY like http.DefaultTransport does. Without
		// this the Claude Code cloud sandbox (egress only via a CONNECT proxy)
		// cannot reach SAP at all; everywhere else the variables are unset and
		// nothing changes.
		Proxy: http.ProxyFromEnvironment,
	}
	if cfg.Insecure {
		transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // #nosec G402 — user opt-in for self-signed SAP certs
	}
	return &Client{
		cfg: cfg,
		http: &http.Client{
			Timeout:   time.Duration(cfg.Timeout) * time.Second,
			Transport: transport,
		},
		sessions: sessions,
	}
}

// SetErrWriter redirects the client's warning output (currently only "write log
// unavailable"). Commands point this at cmd.ErrOrStderr(); tests capture it.
func (c *Client) SetErrWriter(w io.Writer) {
	c.errOut = w
}

func (c *Client) warn(format string, args ...interface{}) {
	w := c.errOut
	if w == nil {
		w = os.Stderr
	}
	fmt.Fprintf(w, format, args...)
}

// HasSession reports whether this Client currently holds session cookies
// (either from a fresh Login or a loaded cache), without contacting the server.
func (c *Client) HasSession() bool {
	return c.b1Session != ""
}

// SessionAge returns how long ago the current session was (re)established,
// and whether that information is known.
func (c *Client) SessionAge() (time.Duration, bool) {
	if c.loggedInAt.IsZero() {
		return 0, false
	}
	return time.Since(c.loggedInAt), true
}

// LoadCachedSession loads this connection identity's session-cache file if it
// matches this Client's host/port/companyDB/user. Returns true if a usable
// cached session was found.
//
// The four-field match below is LOAD-BEARING and must not be removed. A
// Service Layer session is bound to the CompanyDB it logged into, so replaying
// a cached session against a different company would answer a Beverages
// question with Oil's books — the single worst failure this tool can produce.
// The per-identity filename already separates them; this check is the second,
// independent guard that does not depend on how the path was derived.
func (c *Client) LoadCachedSession() bool {
	sc, ok := loadSessionCache(c.cfg.Host, c.cfg.Port, c.cfg.CompanyDB, c.cfg.User)
	if !ok {
		return false
	}
	if sc.Host != c.cfg.Host || sc.Port != c.cfg.Port || sc.CompanyDB != c.cfg.CompanyDB || sc.User != c.cfg.User {
		return false
	}
	c.b1Session = sc.B1Session
	c.routeID = sc.RouteID
	c.loggedInAt = sc.LoggedInAt
	return true
}

// ClearCachedSession forgets any in-memory session and deletes the cache file.
func (c *Client) ClearCachedSession() {
	c.b1Session = ""
	c.routeID = ""
	c.loggedInAt = time.Time{}
	_ = clearSessionCache(c.cfg.Host, c.cfg.Port, c.cfg.CompanyDB, c.cfg.User)
}

func (c *Client) saveSession() {
	_ = saveSessionCache(&sessionCache{
		Host:       c.cfg.Host,
		Port:       c.cfg.Port,
		CompanyDB:  c.cfg.CompanyDB,
		User:       c.cfg.User,
		B1Session:  c.b1Session,
		RouteID:    c.routeID,
		LoggedInAt: c.loggedInAt,
	})
}

func (c *Client) attachCookies(req *http.Request) {
	if c.b1Session == "" {
		return
	}
	cookie := "B1SESSION=" + c.b1Session
	if c.routeID != "" {
		cookie += "; ROUTEID=" + c.routeID
	}
	req.Header.Set("Cookie", cookie)
}

// Login performs POST /Login and, on success, stores the returned session
// cookies in memory, in the on-disk cache, and — when this Client shares a
// SessionStore — in the process-shared store. It never logs or returns the
// password.
func (c *Client) Login(ctx context.Context) error {
	if err := c.loginLocked(ctx); err != nil {
		return err
	}
	if c.sessions != nil {
		e := c.sessions.entryFor(c.identity())
		e.mu.Lock()
		c.publish(e)
		e.mu.Unlock()
	}
	return nil
}

// loginLocked is Login without touching the shared store. It exists so
// ensureSession/refreshSession, which already hold the identity's lock, can log
// in without deadlocking on it.
func (c *Client) loginLocked(ctx context.Context) error {
	if err := c.cfg.ValidateConnection(); err != nil {
		return err
	}
	if err := c.cfg.ValidateCompanyDB(); err != nil {
		return err
	}

	payload, err := json.Marshal(map[string]string{
		"CompanyDB": c.cfg.CompanyDB,
		"UserName":  c.cfg.User,
		"Password":  c.cfg.Password,
	})
	if err != nil {
		return fmt.Errorf("building login request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.cfg.BaseURL()+"Login", bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("building login request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(req)
	if err != nil {
		return classifyTransportErr(err, c.cfg)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("reading login response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		msg := extractSAPError(body)
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", resp.StatusCode)
		}
		return &errs.AuthError{Msg: fmt.Sprintf("login to %q as %q failed: %s", c.cfg.CompanyDB, c.cfg.User, msg)}
	}

	var b1sess, route string
	for _, ck := range resp.Cookies() {
		switch ck.Name {
		case "B1SESSION":
			b1sess = ck.Value
		case "ROUTEID":
			route = ck.Value
		}
	}
	if b1sess == "" {
		return &errs.AuthError{Msg: "login succeeded (HTTP 200) but the server did not return a B1SESSION cookie"}
	}

	c.b1Session = b1sess
	c.routeID = route
	c.loggedInAt = time.Now()
	c.saveSession()
	return nil
}

// ClearSharedSession drops this identity's entry from the shared store (if any)
// as well as the local and on-disk copies.
func (c *Client) ClearSharedSession() {
	c.forgetShared()
	c.ClearCachedSession()
}

// Logout performs POST /Logout (best-effort) and always clears the local
// session, in memory and on disk.
func (c *Client) Logout(ctx context.Context) error {
	if c.b1Session == "" {
		c.LoadCachedSession()
	}
	if c.b1Session != "" {
		req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.cfg.BaseURL()+"Logout", nil)
		if err == nil {
			c.attachCookies(req)
			if resp, err := c.http.Do(req); err == nil {
				resp.Body.Close()
			}
			// Network/API errors on logout are not fatal — we still clear locally.
		}
	}
	c.ClearSharedSession()
	return nil
}

// getWithHeaders performs an authenticated GET against path (relative to the
// Service Layer base URL, e.g. "Orders?$top=5"). It logs in first if there is no
// session yet, and transparently re-logs-in once and retries on a 401. It
// returns the raw response body on success (2xx), plus the response headers, or
// a typed error otherwise.
//
// The response headers matter for one thing: the Service Layer's HTTP `Date`
// header, the server's own clock and therefore the honest "as of" stamp for a
// read (see serverDate). A body-only wrapper used to sit in front of this for
// callers that did not care; every caller came to care, and it was left behind
// as dead code (`golang.org/x/tools/cmd/deadcode` named it as the only
// unreachable function in the module).
func (c *Client) getWithHeaders(ctx context.Context, path string, headers map[string]string) ([]byte, http.Header, error) {
	body, status, respHeaders, err := c.getWithStatus(ctx, path, headers)
	if err != nil {
		return nil, nil, err
	}

	if status < 200 || status >= 300 {
		code, msg := extractSAPErrorDetail(body)
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", status)
		}
		if status == http.StatusUnauthorized {
			return nil, nil, &errs.AuthError{Msg: fmt.Sprintf("authentication failed: %s", msg)}
		}
		return nil, nil, &errs.APIError{Code: code, Msg: msg}
	}

	return body, respHeaders, nil
}

// getWithStatus is getWithHeaders without the "any non-2xx is an error" verdict:
// it establishes a session, sends the GET, re-logs-in once on a 401 and retries,
// and hands the raw status back to the caller.
//
// It exists because one caller does NOT want a missing entity turned into an
// error: GetEntity has to be able to say "404 — it isn't there" as a normal,
// expected answer (that is how a delete verifies itself, and how it notices a
// draft somebody else already removed).
func (c *Client) getWithStatus(ctx context.Context, path string, headers map[string]string) ([]byte, int, http.Header, error) {
	if err := c.ensureSession(ctx); err != nil {
		return nil, 0, nil, err
	}

	used := c.b1Session
	body, status, respHeaders, err := c.rawGet(ctx, path, headers)
	if err != nil {
		return nil, 0, nil, err
	}

	if status == http.StatusUnauthorized {
		if err := c.refreshSession(ctx, used); err != nil {
			return nil, 0, nil, err
		}
		body, status, respHeaders, err = c.rawGet(ctx, path, headers)
		if err != nil {
			return nil, 0, nil, err
		}
	}

	return body, status, respHeaders, nil
}

// EntityResult is the outcome of a single-entity read. Found is false — with a
// nil error — when the Service Layer answered 404, i.e. the object genuinely
// isn't there.
type EntityResult struct {
	Found  bool
	Status int
	Body   []byte
}

// GetEntity reads exactly one numerically-keyed entity, e.g. Drafts(54990).
//
// It builds the path itself from entitySet + docEntry, so no caller-supplied
// string ever becomes a path segment: `Drafts(1)/Cancel`, `Drafts?$filter=…` and
// `../Login` are not spellable through this method, they are compile-time
// impossible. entitySet must be a bare OData identifier and docEntry must be
// positive.
//
// A 404 is not an error here — it is the answer (Found=false). Anything else
// non-2xx is, as everywhere else, an AuthError or an APIError.
func (c *Client) GetEntity(ctx context.Context, entitySet string, docEntry int64) (*EntityResult, error) {
	if !entitySetRe.MatchString(entitySet) {
		return nil, &errs.UsageError{Msg: fmt.Sprintf("%q is not a bare entity-set name — GetEntity addresses one entity set by a numeric key and nothing else", entitySet)}
	}
	if docEntry <= 0 {
		return nil, &errs.UsageError{Msg: fmt.Sprintf("%s key must be a positive number, got %d", entitySet, docEntry)}
	}

	path := entitySet + "(" + strconv.FormatInt(docEntry, 10) + ")"
	body, status, _, err := c.getWithStatus(ctx, path, nil)
	if err != nil {
		return nil, err
	}

	switch {
	case status == http.StatusNotFound:
		return &EntityResult{Found: false, Status: status}, nil
	case status == http.StatusUnauthorized:
		_, msg := extractSAPErrorDetail(body)
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", status)
		}
		return nil, &errs.AuthError{Msg: fmt.Sprintf("authentication failed: %s", msg)}
	case status < 200 || status >= 300:
		code, msg := extractSAPErrorDetail(body)
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", status)
		}
		return nil, &errs.APIError{Code: code, Msg: msg}
	}

	return &EntityResult{Found: true, Status: status, Body: body}, nil
}

func (c *Client) rawGet(ctx context.Context, path string, headers map[string]string) ([]byte, int, http.Header, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.cfg.BaseURL()+path, nil)
	if err != nil {
		return nil, 0, nil, fmt.Errorf("building request: %w", err)
	}
	req.Header.Set("Accept", "application/json")
	c.attachCookies(req)
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, 0, nil, classifyTransportErr(err, c.cfg)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, 0, nil, fmt.Errorf("reading response body: %w", err)
	}
	return body, resp.StatusCode, resp.Header, nil
}

// serverDate reads the HTTP `Date` response header — the SAP server's own
// clock at the moment it answered. It is the difference between "12,861 open
// invoices as of 13:09 on the SAP box" and an unqualified number that may
// already have moved. ok=false when the header is absent or unparseable, in
// which case callers fall back to local time and must say so.
func serverDate(h http.Header) (time.Time, bool) {
	if h == nil {
		return time.Time{}, false
	}
	v := h.Get("Date")
	if v == "" {
		return time.Time{}, false
	}
	t, err := http.ParseTime(v)
	if err != nil {
		return time.Time{}, false
	}
	return t, true
}

// CheckTCPReachable does a raw TCP dial to host:port (no TLS, no HTTP) to
// distinguish "network unreachable" from "reachable but SAP/TLS/auth issue".
// Used by `sapb1 doctor`.
func CheckTCPReachable(hostport string, timeout time.Duration) error {
	conn, err := net.DialTimeout("tcp", hostport, timeout)
	if err != nil {
		return &errs.NetworkError{
			Msg: fmt.Sprintf("cannot reach %s over TCP — are you on the company VPN or is your IP whitelisted? (%v)", hostport, err),
			Err: err,
		}
	}
	_ = conn.Close()
	return nil
}

// sapErrorBody mirrors the documented Service Layer error envelope:
//
//	{ "error": { "code": <int|string>, "message": { "lang": "en-us", "value": "..." } } }
type sapErrorBody struct {
	Error struct {
		Code    interface{} `json:"code"`
		Message struct {
			Lang  string `json:"lang"`
			Value string `json:"value"`
		} `json:"message"`
	} `json:"error"`
}

// extractSAPError best-effort parses the SAP error envelope out of body and
// returns the human message, or "" if body doesn't look like a SAP error.
func extractSAPError(body []byte) string {
	_, msg := extractSAPErrorDetail(body)
	return msg
}

// extractSAPErrorDetail parses the SAP error envelope and returns both SAP's own
// error code (-5002, 301, …, nil when absent) and the human message. An empty
// message means the body isn't a SAP error envelope at all — which, for a write,
// is the difference between "SAP rejected this" and "something in between
// answered for it".
func extractSAPErrorDetail(body []byte) (interface{}, string) {
	if len(body) == 0 {
		return nil, ""
	}
	var eb sapErrorBody
	if err := json.Unmarshal(body, &eb); err != nil {
		return nil, ""
	}
	if eb.Error.Message.Value == "" {
		return nil, ""
	}
	return eb.Error.Code, eb.Error.Message.Value
}

// classifyTransportErr turns a low-level Go net/http transport error (dial
// refused, timeout, DNS failure, TLS handshake failure, ...) into a friendly
// *errs.NetworkError. It's used for every http.Client.Do() failure, since at
// that layer there's no HTTP status code to inspect — the request never
// completed.
func classifyTransportErr(err error, cfg *config.Config) error {
	hostport := cfg.HostPort()
	msg := err.Error()

	if strings.Contains(msg, "certificate") || strings.Contains(msg, "x509") || strings.Contains(msg, "tls:") {
		return &errs.NetworkError{
			Msg: fmt.Sprintf(
				"TLS/certificate error connecting to %s — SAP boxes commonly use self-signed certificates; try --insecure or set SAPB1_INSECURE=true in .env (%v)",
				hostport, err,
			),
			Err: err,
		}
	}

	return &errs.NetworkError{
		Msg: fmt.Sprintf(
			"cannot reach SAP Service Layer at %s — are you on the company VPN or is your IP whitelisted? (%v)",
			hostport, err,
		),
		Err: err,
	}
}
