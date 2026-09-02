package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// client.go is the ONLY file in this binary that talks HTTP. readonly_ast_test.go
// enforces that (nothing else may import net/*), which is a stronger guarantee
// than scanning for method names: a mutation cannot be smuggled in from a helper
// somewhere else because no other file can open a connection at all.
//
// do() is the single request path. Its first act is always the guard.

// clientTransport is nil in production (Go's default transport). Tests point it
// at their httptest server.
var clientTransport http.RoundTripper

// clientMinGap is the politeness delay between two calls to a statutory portal.
// Set to 0 by tests.
var clientMinGap = 350 * time.Millisecond

// clientTimeout is generous: some GST reads (a full 2B) take a while.
const clientTimeout = 90 * time.Second

// maxBody caps what we will read from the portal (a big GSTR-2B is ~2 MB).
const maxBody = 32 << 20

// emptyCodes are the portal's ways of saying "there is nothing to report".
// They are ANSWERS, not failures: exit 0, data null, count 0. Treating them as
// errors would make a multi-registration run abort on the first nil filer.
var emptyCodes = map[string]bool{
	"RET13510":  true, // No Record found for the provided Inputs
	"LG9221":    true, // No data found (challan search)
	"GTR2B-002": true, // GSTR-2B not generated for that period
	"RETWEB_07": true, // "No pending invoices found!!" — a GSTR-1 section with no rows
}

// Client is the read-only GST HTTP client for ONE registration.
type Client struct {
	reg  Registration
	hc   *http.Client
	sess *session
	last time.Time
}

func newClient(reg Registration) *Client {
	c := &Client{reg: reg}
	c.hc = &http.Client{
		Timeout:   clientTimeout,
		Transport: clientTransport,
		// Never follow the WAF's "go away" bounce: surface it as an auth error
		// so the operator is told to log in instead of getting an HTML page.
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			p := req.URL.Path
			if strings.HasPrefix(p, "/services/error/accessdenied") {
				return errAuth("the portal bounced this request to %s — the session, the Referer or the WAF cookies were not accepted", p)
			}
			if strings.HasPrefix(p, "/services/login") {
				return errAuth("the portal redirected to the login page — the session for %s is not valid", c.reg.GSTIN)
			}
			if len(via) >= 5 {
				return errNetwork("too many redirects", nil)
			}
			return nil
		},
	}
	return c
}

// session returns the cached jar, loading it once.
func (c *Client) ensureSession() error {
	if c.sess != nil {
		return nil
	}
	s, err := loadSession(c.reg.GSTIN)
	if err != nil {
		return err
	}
	if s == nil {
		return errAuth("no session for %s (%s)", c.reg.GSTIN, c.reg.State)
	}
	if !s.authenticated() {
		return errAuth("the cached jar for %s is only a pre-login jar — finish `auth login`", c.reg.GSTIN)
	}
	if s.expired(sessionMaxAge) {
		return errAuth("the cached session for %s is %s old and is assumed expired", c.reg.GSTIN, time.Since(s.SavedAt).Round(time.Second))
	}
	c.sess = s
	return nil
}

// do is the single network path: guard → session → browser-shaped headers →
// request → classify. Nothing else in this binary opens a connection.
//
// name is an allowlist row; params fills its path placeholders; query and body
// carry ONLY keys that row permits (the guard rejects anything else before a
// socket is opened).
func (c *Client) do(name string, params map[string]string, query url.Values, body map[string]any) (Result, error) {
	ep, err := lookup(name)
	if err != nil {
		return Result{}, err
	}
	resolved, err := ep.resolvePath(params)
	if err != nil {
		return Result{}, err
	}
	if err := forbidden(ep.Method, ep.Host, ep.Path, resolved, keysOfValues(query), keysOfBody(body)); err != nil {
		return Result{}, err
	}
	if err := c.ensureSession(); err != nil {
		return Result{}, err
	}
	return c.send(ep, resolved, query, body)
}

// doPreAuth is the same path for the three pre-login rows (login page, captcha,
// authenticate), which by definition have no authenticated session yet. It is
// separate ONLY so that ensureSession is not bypassable by accident from a read
// command; the guard still runs, so it cannot reach anything but the table.
func (c *Client) doPreAuth(name string, query url.Values, body map[string]any) (Result, error) {
	ep, err := lookup(name)
	if err != nil {
		return Result{}, err
	}
	switch name {
	case epLoginPage, epCaptcha, epAuthenticate:
	default:
		return Result{}, errGuard("%s is not a pre-authentication endpoint", name)
	}
	if err := forbidden(ep.Method, ep.Host, ep.Path, ep.Path, keysOfValues(query), keysOfBody(body)); err != nil {
		return Result{}, err
	}
	return c.send(ep, ep.Path, query, body)
}

// doPreAuthRaw fetches a pre-login artefact whose body is NOT JSON: the login
// page (HTML, minted only for its cookies) and the captcha (a 182x50 PNG). It
// takes the same guarded path as everything else — the only difference is that
// classify() would reject these bodies, so the caller gets the bytes.
func (c *Client) doPreAuthRaw(name string, query url.Values) ([]byte, string, error) {
	ep, err := lookup(name)
	if err != nil {
		return nil, "", err
	}
	if name != epLoginPage && name != epCaptcha {
		return nil, "", errGuard("%s is not one of the two raw pre-login reads", name)
	}
	if err := forbidden(ep.Method, ep.Host, ep.Path, ep.Path, keysOfValues(query), nil); err != nil {
		return nil, "", err
	}
	status, _, raw, err := c.roundTrip(ep, ep.Path, query, nil)
	if err != nil {
		return nil, "", err
	}
	if status != http.StatusOK {
		return nil, "", errAuth("%s returned HTTP %d — the portal would not serve the login prerequisites", ep.Name, status)
	}
	return raw, http.DetectContentType(raw), nil
}

// startPreLoginJar arms the client with an empty jar so the login page and the
// captcha can mint one. The captcha is bound server-side to THIS jar
// (CaptchaCookie), which is why it has to be persisted between the two
// invocations of the agent-friendly login.
func (c *Client) startPreLoginJar() {
	c.sess = &session{GSTIN: c.reg.GSTIN, Username: c.reg.User, Stage: stagePreLogin}
}

// useSession arms the client with an already-loaded jar (login continues on the
// pre-login jar it just saved; snapshot reuses one jar for a whole registration).
func (c *Client) useSession(s *session) { c.sess = s }

// urlValues lets other files pass a query around without naming net/url. Only
// client.go may import net/* (readonly_ast_test.go), so the alias is how a
// command file holds one.
type urlValues = url.Values

// qs builds a query string from key/value pairs, dropping empty values so an
// optional filter needs no branch at the call site. It lives here because
// client.go is the only file allowed to name net/url (readonly_ast_test.go).
func qs(kv ...string) url.Values {
	v := url.Values{}
	for i := 0; i+1 < len(kv); i += 2 {
		if kv[i+1] == "" {
			continue
		}
		v.Set(kv[i], kv[i+1])
	}
	return v
}

func (c *Client) send(ep Endpoint, resolved string, query url.Values, body map[string]any) (Result, error) {
	status, retryAfter, raw, err := c.roundTrip(ep, resolved, query, body)
	if err != nil {
		return Result{}, err
	}
	return classify(ep, status, retryAfter, raw)
}

// roundTrip is the wire itself: build, send, read. It does not interpret the
// body — send() classifies JSON, and the pre-login callers take the bytes raw
// (the login page is HTML and the captcha is a PNG).
func (c *Client) roundTrip(ep Endpoint, resolved string, query url.Values, body map[string]any) (status int, retryAfter string, raw []byte, err error) {
	u := url.URL{Scheme: "https", Host: ep.Host, Path: resolved}
	if len(query) > 0 {
		u.RawQuery = query.Encode()
	}

	var payload io.Reader
	if ep.Method == methodPOST {
		// A POST row always sends a JSON body, even when it is {} (profile/detail).
		if body == nil {
			body = map[string]any{}
		}
		b, err := json.Marshal(body)
		if err != nil {
			return 0, "", nil, errPlain("cannot encode the request body: %v", err)
		}
		payload = bytes.NewReader(b)
	}

	req, err := http.NewRequest(ep.Method, u.String(), payload)
	if err != nil {
		return 0, "", nil, errNetwork("cannot build the request", err)
	}
	// Look like the portal's own XHR. Any of these missing and the F5 in front
	// of GST answers with a redirect to accessdenied instead of data.
	//
	// TODO(D3): the discovery agent is measuring which of these a plain Go
	// client actually needs (API.md "Plain-client rules"). Until that lands this
	// is the conservative set: whole jar incl. TS*, browser UA, per-host Referer,
	// Accept. Do not trim it on a hunch.
	req.Header.Set("User-Agent", browserUA)
	req.Header.Set("Accept", acceptJSON)
	req.Header.Set("Accept-Language", "en-GB,en-US;q=0.9,en;q=0.8")
	req.Header.Set("Referer", ep.referer())
	if ep.Method == methodPOST {
		req.Header.Set("Content-Type", "application/json;charset=utf-8")
	}
	for _, ck := range c.sess.cookiesFor(ep.Host) {
		req.AddCookie(&http.Cookie{Name: ck.Name, Value: ck.Value})
	}

	c.pause()
	resp, err := c.hc.Do(req)
	if err != nil {
		// CheckRedirect's typed errors arrive wrapped in *url.Error; keep the
		// type. NOTE: the error text names the method and the URL only — never
		// the body, which on the login row holds the password.
		var aerr *authError
		if asAuthError(err, &aerr) {
			return 0, "", nil, aerr
		}
		return 0, "", nil, errNetwork(fmt.Sprintf("%s %s failed", ep.Method, u.Host+u.Path), err)
	}
	defer resp.Body.Close()
	raw, _ = io.ReadAll(io.LimitReader(resp.Body, maxBody))
	c.rememberCookies(ep.Host, resp)
	// sessionMaxAge is an IDLE window, so use of the session has to reset it.
	// Without this, SavedAt only moves when a cookie VALUE changes — and API.md
	// records that the TS* cookies do not rotate on a JSON API call. The jar
	// would then expire 15 minutes after LOGIN however busy it was, which is
	// exactly the shape of a `--all` sitting: eight captchas take longer than
	// that, and the first registrations get skipped while their portal sessions
	// are still alive.
	c.touchSession()
	return resp.StatusCode, resp.Header.Get("Retry-After"), raw, nil
}

// touchSession refreshes the jar's saved_at after a successful round trip, at
// most once a minute so a snapshot does not rewrite the file 400 times.
func (c *Client) touchSession() {
	if c.sess == nil || c.sess.Stage != stageAuthenticated {
		return
	}
	if time.Since(c.sess.SavedAt) < sessionTouchInterval {
		return
	}
	_ = c.sess.save()
}

// pause keeps a fixed gap between calls. GST is a statutory portal shared with
// every other filer in the country; there is no reason to hammer it.
func (c *Client) pause() {
	if clientMinGap <= 0 {
		return
	}
	if d := clientMinGap - time.Since(c.last); d > 0 {
		time.Sleep(d)
	}
	c.last = time.Now()
}

// rememberCookies folds any Set-Cookie back into the session file. The F5
// rotates the TS* cookies, and replaying a stale pair is how a working session
// starts getting bounced mid-run. It also carries the pre-login jar: the
// CaptchaCookie the portal binds an image to arrives this way.
//
// host is the GST host we ADDRESSED, not resp.Request.URL.Host: a host-only
// cookie must be scoped to the name we will send it back to, and the response's
// URL can differ (a redirect, or a test transport that rewrites the address).
// Getting this wrong silently drops the cookie on the next request.
func (c *Client) rememberCookies(host string, resp *http.Response) {
	fresh := resp.Cookies()
	if len(fresh) == 0 || c.sess == nil {
		return
	}
	changed := false
	for _, n := range fresh {
		sc := sessionCookie{
			Name: n.Name, Value: n.Value, Domain: n.Domain, Path: n.Path,
			Secure: n.Secure, HTTPOnly: n.HttpOnly,
		}
		if sc.Domain == "" {
			// A Set-Cookie with no Domain attribute is host-only by RFC 6265, and
			// scoping it to `host` is what a browser does. GST is the one place
			// that would silently break us: GET /services/login mints AuthToken
			// on services.gst.gov.in, and if the portal does not re-issue it with
			// Domain=.gst.gov.in on /authenticate, a host-only jar sends ZERO
			// cookies to return./payment./gstr2b. — three of the four hosts —
			// while `auth import` (a browser export, which carries .gst.gov.in)
			// keeps working. That failure reads as "login is broken but import
			// works" and costs a day.
			//
			// This client only ever talks to gst.gov.in (guard.go pins the four
			// hosts), the auth cookie IS domain-wide there (API.md:102), and
			// over-sending the F5's TS* cookies is documented as harmless. So
			// widen to the registrable domain instead of the exact host.
			sc.Domain = cookieDomainFor(host)
		}
		if sc.Path == "" {
			sc.Path = "/"
		}
		if !n.Expires.IsZero() {
			sc.Expires = n.Expires
		}
		replaced := false
		for i := range c.sess.Cookies {
			if c.sess.Cookies[i].Name == sc.Name {
				if c.sess.Cookies[i].Value != sc.Value {
					c.sess.Cookies[i] = sc
					changed = true
				}
				replaced = true
				break
			}
		}
		if !replaced {
			c.sess.Cookies = append(c.sess.Cookies, sc)
			changed = true
		}
	}
	if changed {
		// Best effort: a failure to persist costs a re-login, never data.
		_ = c.sess.save()
	}
}

// cookieDomainFor widens a host-only cookie to the GST registrable domain. Any
// other host (a test server) keeps its exact name.
func cookieDomainFor(host string) string {
	if host == gstDomain || strings.HasSuffix(host, "."+gstDomain) {
		return gstDomain
	}
	return host
}

// portalEnvelope covers both error shapes GST uses: the returns/payment hosts
// send {"status":0,"error":{"errorCode","message"}}, the 2B host sends
// {"status_cd":"0","error":{"error_cd","message"}}.
type portalEnvelope struct {
	Status   json.RawMessage `json:"status"`
	StatusCd json.RawMessage `json:"status_cd"`
	Error    *struct {
		ErrorCode string `json:"errorCode"`
		ErrorCd   string `json:"error_cd"`
		Message   string `json:"message"`
	} `json:"error"`
}

func (p portalEnvelope) code() string {
	if p.Error == nil {
		return ""
	}
	if p.Error.ErrorCode != "" {
		return p.Error.ErrorCode
	}
	return p.Error.ErrorCd
}

// classify turns an HTTP response into a Result or a typed error.
func classify(ep Endpoint, status int, retryAfter string, raw []byte) (Result, error) {
	trimmed := strings.TrimSpace(string(raw))
	lower := strings.ToLower(trimmed)

	// An HTML body means we are talking to the WAF or a login shell, not the API.
	if strings.HasPrefix(lower, "<!doctype") || strings.HasPrefix(lower, "<html") {
		what := "an HTML page"
		if strings.Contains(trimmed, "Request Rejected") {
			what = "the WAF's \"Request Rejected\" page"
		}
		return Result{}, errAuth("%s returned %s instead of JSON — the session or the request shape was not accepted", ep.Name, what)
	}

	switch {
	case status == http.StatusUnauthorized, status == http.StatusForbidden:
		return Result{}, errAuth("%s returned HTTP %d for %s", ep.Name, status, ep.Host)
	case status == http.StatusTooManyRequests:
		msg := "the portal is rate-limiting us"
		if retryAfter != "" {
			// RFC 9110 allows delay-seconds OR an HTTP-date; appending "s" to a
			// date renders "Wed, 21 Aug 2026 12:00:00 GMTs".
			if _, err := strconv.Atoi(strings.TrimSpace(retryAfter)); err == nil {
				msg += "; Retry-After: " + retryAfter + "s"
			} else {
				msg += "; Retry-After: " + retryAfter
			}
		}
		// Deliberately NOT retried: on a statutory portal, backing off is the
		// operator's decision, not a loop's.
		return Result{}, &apiError{Status: status, Code: "429", Message: msg}
	case status >= 400:
		return Result{}, &apiError{Status: status, Message: firstLine(trimmed)}
	}

	if len(trimmed) == 0 {
		return Result{}, &apiError{Status: status, Message: "the portal returned an empty body"}
	}

	var env portalEnvelope
	if err := json.Unmarshal(raw, &env); err == nil && env.Error != nil {
		code := env.code()
		if emptyCodes[code] {
			return Result{Empty: true, Note: fmt.Sprintf("%s: %s", code, env.Error.Message)}, nil
		}
		return Result{}, &apiError{Code: code, Message: env.Error.Message, Status: status}
	}
	if !json.Valid(raw) {
		return Result{}, &apiError{Status: status, Message: "the portal returned a body that is not JSON: " + firstLine(trimmed)}
	}
	// API.md:115, error → action map: `services /ustatus` answering `{}` (2 bytes,
	// HTTP 200) IS the expired-session signal. Without this it decodes cleanly as
	// a happy Result with an empty gstin, and doctor then reports "WRONG
	// REGISTRATION — the session belongs to , not 06…", sending the operator
	// hunting a credential mix-up that does not exist.
	if ep.Name == epUstatus && !namesAGSTIN(raw) {
		return Result{}, errAuth("%s answered with no GSTIN — the session for %s is expired or absent", ep.Name, ep.Host)
	}
	return Result{Raw: json.RawMessage(raw)}, nil
}

// namesAGSTIN reports whether a ustatus body actually identifies a registration.
func namesAGSTIN(raw []byte) bool {
	var u struct {
		GSTIN string `json:"gstin"`
	}
	return json.Unmarshal(raw, &u) == nil && strings.TrimSpace(u.GSTIN) != ""
}

func firstLine(s string) string {
	if i := strings.IndexByte(s, '\n'); i >= 0 {
		s = s[:i]
	}
	if len(s) > 200 {
		s = s[:200] + "…"
	}
	return s
}

func keysOfValues(v url.Values) []string {
	if len(v) == 0 {
		return nil
	}
	out := make([]string, 0, len(v))
	for k := range v {
		out = append(out, k)
	}
	return out
}

func keysOfBody(b map[string]any) []string {
	if len(b) == 0 {
		return nil
	}
	out := make([]string, 0, len(b))
	for k := range b {
		out = append(out, k)
	}
	return out
}

// ---- App-level helpers ----------------------------------------------------

// read runs one allowlisted read for one registration and emits it.
func (a *App) read(command string, reg Registration, name string, params map[string]string, query url.Values, body map[string]any) error {
	c := newClient(reg)
	res, err := c.do(name, params, query, body)
	return a.emit(command, reg.GSTIN, endpointURL(name), res, err)
}

// liveCheck is doctor's one harmless live read: GET /services/api/ustatus, whose
// answer must be the GSTIN we think we are.
func (a *App) liveCheck(reg Registration) (string, bool) {
	c := newClient(reg)
	res, err := c.do(epUstatus, nil, nil, nil)
	if err != nil {
		return "FAILED — " + err.Error(), false
	}
	var u struct {
		GSTIN string `json:"gstin"`
		BName string `json:"bname"`
		Stcd  string `json:"stcd"`
	}
	if err := json.Unmarshal(res.Raw, &u); err != nil {
		return "FAILED — ustatus was not the expected shape", false
	}
	if !strings.EqualFold(u.GSTIN, reg.GSTIN) {
		return fmt.Sprintf("WRONG REGISTRATION — the session belongs to %s, not %s", u.GSTIN, reg.GSTIN), false
	}
	return fmt.Sprintf("ok — ustatus says %s (state %s)", u.GSTIN, u.Stcd), true
}
