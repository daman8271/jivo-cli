// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — HTTP client, READ-ONLY by construction.
//
// ⛔ THE READ-ONLY LAW (ported from jsap-cli/jsap/client.py)
// This client exposes exactly two data verbs: get() and readPost(). There is no
// put/patch/delete anywhere in this file and there never will be. The ONLY
// mutating-shaped traffic is the three-request session bootstrap
// (/api/auth/Login, /websession/set, /websession/updateSelectedCompany), which
// authenticates a session and creates zero JIVO business data; those paths are
// whitelisted exactly, by string.
//
// readPost() exists because a large part of JSAP's read surface is served over
// POST with a JSON filter body (the .NET "POST-to-query" convention). It refuses
// any path whose leaf action is not a read verb, so a POST can never reach
// CreateTicket / AssignTicket / SaveAllAttachments / InsertBPmasterData.
//
// Two hazards live on the JSAP SERVER, not in this client, and are excluded one
// level up in the catalogue rather than here (see catalog.go):
//   - /api/DocumentDispatch/GetLastBundleId?mode=update MUTATES a counter. It is
//     a GET, so the leaf-verb guard would not fire. The catalogue does not carry
//     the command, and no caller can supply a URL path or a `mode` parameter.
//   - /DocumentHub/Download appends a server-side activity-log row — a read with
//     a side effect. Not catalogued.

package jsap

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	// The single permitted read verb. Everything the catalogue reads is a GET
	// unless it is an explicitly guarded POST-to-read.
	verbGet = http.MethodGet
	// The bootstrap + POST-to-read verb. Reachable only through the two guarded
	// paths below; there is no unguarded request helper in this package.
	verbPost = http.MethodPost

	sessionTTL     = time.Hour
	defaultTimeout = 45 * time.Second
)

// bootstrapPaths is the exact, closed set of non-read requests this client may
// ever issue. Matched by string equality — no prefix, no pattern.
var bootstrapPaths = map[string]bool{
	"/api/auth/Login":                   true,
	"/websession/set":                   true,
	"/websession/updateSelectedCompany": true,
}

// readLeafPrefixes are the action-name prefixes that mark a POST endpoint as a
// pure read. Same list as the Python client, which was derived from JSAP's own
// controller naming.
var readLeafPrefixes = []string{
	"get", "list", "search", "fetch", "download", "load", "view",
	"report", "fill", "all", "find", "lookup", "export", "check", "validate",
}

// Error is returned for every JSAP-side failure so callers can tell a refusal
// from a transport problem without string matching.
type Error struct{ msg string }

func (e *Error) Error() string { return e.msg }

func errf(format string, args ...any) error { return &Error{msg: fmt.Sprintf(format, args...)} }

// requestKind selects which half of the read-only guard applies.
type requestKind int

const (
	reqRead requestKind = iota
	reqReadPost
	reqBootstrap
)

// Sessions hands out one Client per company and keeps it.
//
// Why this exists: a gateway fans tool calls out in parallel, and a per-call
// client would mean a per-call Login against a single shared JSAP identity —
// the login storm that had to be fixed on the sapb1 server. One client per
// company, guarded by its own mutex, costs one Login per company per hour.
type Sessions struct {
	cfg Config

	mu        sync.Mutex
	byCompany map[int]*Client
}

// NewSessions builds the per-company client pool.
func NewSessions(cfg Config) *Sessions {
	return &Sessions{cfg: cfg, byCompany: map[int]*Client{}}
}

// Config exposes the loaded configuration (never the password — callers that
// print anything must use Redacted()).
func (s *Sessions) Config() Config { return s.cfg }

// For returns the shared client for one company id, creating it on first use.
func (s *Sessions) For(company int) *Client {
	s.mu.Lock()
	defer s.mu.Unlock()
	if c, ok := s.byCompany[company]; ok {
		return c
	}
	c := newClient(s.cfg, company)
	s.byCompany[company] = c
	return c
}

// Client is one authenticated JSAP session scoped to one company.
type Client struct {
	cfg     Config
	company int
	http    *http.Client

	mu       sync.Mutex
	authedAt time.Time
}

func newClient(cfg Config, company int) *Client {
	jar, _ := cookiejar.New(nil)
	return &Client{
		cfg:     cfg,
		company: company,
		http:    &http.Client{Jar: jar, Timeout: defaultTimeout},
	}
}

// Run executes ONE catalogued command. This is the only entry point the MCP
// surface has: it takes a Command from the compiled-in catalogue, never a
// caller-supplied URL. A path-taking execute would let an agent hand-craft
// GetLastBundleId?mode=update or any Insert*/Save* endpoint over GET and walk
// straight past the leaf-verb guard, which only fires on POST.
func (c *Client) Run(ctx context.Context, cmd Command, args map[string]any) (json.RawMessage, error) {
	path, query, body, err := cmd.bind(args, c.cfg.UserID, c.company)
	if err != nil {
		return nil, err
	}
	switch cmd.Method {
	case verbGet:
		return c.get(ctx, cmd, path, query)
	case verbPost:
		return c.readPost(ctx, cmd, path, body)
	default:
		// Unreachable: catalogue validation rejects any other verb at startup.
		return nil, errf("READ-ONLY LAW: command %s declares method %s; only GET and guarded POST-reads exist", cmd.ID, cmd.Method)
	}
}

// get performs an authenticated GET and unwraps the {success,data} envelope.
func (c *Client) get(ctx context.Context, cmd Command, path string, query url.Values) (json.RawMessage, error) {
	raw, err := c.do(ctx, verbGet, path, query, nil, reqRead)
	if err != nil {
		return nil, err
	}
	if cmd.HTMLUserTable {
		return scrapeUserTable(raw)
	}
	return unwrap(raw, !cmd.Raw)
}

// readPost performs a POST-to-read. The leaf action must be a read verb.
func (c *Client) readPost(ctx context.Context, cmd Command, path string, body map[string]any) (json.RawMessage, error) {
	raw, err := c.do(ctx, verbPost, path, nil, body, reqReadPost)
	if err != nil {
		return nil, err
	}
	return unwrap(raw, !cmd.Raw)
}

// do is the single request core, and the place the read-only law is enforced.
func (c *Client) do(ctx context.Context, method, path string, query url.Values, body map[string]any, kind requestKind) ([]byte, error) {
	switch kind {
	case reqBootstrap:
		if !bootstrapPaths[path] {
			return nil, errf("READ-ONLY LAW: %s is not one of the three bootstrap paths", path)
		}
	case reqReadPost:
		if method != verbPost || !hasReadLeaf(path) {
			return nil, errf("READ-ONLY LAW: refusing %s %s — its action is not a read verb, so it may mutate", method, path)
		}
	case reqRead:
		if method != verbGet {
			return nil, errf("READ-ONLY LAW: refusing %s %s — reads are GET only", method, path)
		}
	default:
		return nil, errf("READ-ONLY LAW: refusing %s %s — unclassified request", method, path)
	}

	if kind != reqBootstrap {
		if err := c.ensureSession(ctx); err != nil {
			return nil, err
		}
	}

	target := c.cfg.BaseURL + path
	if len(query) > 0 {
		target += "?" + query.Encode()
	}

	var reader io.Reader
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			return nil, errf("encoding request body for %s: %v", path, err)
		}
		reader = bytes.NewReader(encoded)
	}

	req, err := http.NewRequestWithContext(ctx, method, target, reader)
	if err != nil {
		return nil, errf("building request for %s: %v", path, err)
	}
	req.Header.Set("Accept", "application/json")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.http.Do(req)
	if err != nil {
		// The URL carries no credentials (they only ever travel in a bootstrap
		// body), so it is safe to name the host in the error.
		return nil, errf("cannot reach JSAP at %s: %v", target, err)
	}
	defer resp.Body.Close()

	// JSAP answers errors with a JSON envelope and a non-2xx status on the same
	// body; read it either way so the operator sees the server's own message.
	payload, err := io.ReadAll(io.LimitReader(resp.Body, 32<<20))
	if err != nil {
		return nil, errf("reading response from %s: %v", path, err)
	}
	if resp.StatusCode >= 400 && !json.Valid(payload) {
		return nil, errf("HTTP %d on %s %s: %s", resp.StatusCode, method, path, preview(payload, 200))
	}
	return payload, nil
}

// ensureSession logs in when there is no live session. Serialised on the
// client's mutex so a burst of concurrent tool calls costs one Login, not one
// per call.
func (c *Client) ensureSession(ctx context.Context) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if !c.authedAt.IsZero() && time.Since(c.authedAt) < sessionTTL {
		return nil
	}
	if err := c.cfg.RequireCreds(); err != nil {
		return err
	}

	loginBody, err := c.do(ctx, verbPost, "/api/auth/Login", nil, map[string]any{
		"loginUser": c.cfg.Username,
		"password":  c.cfg.Password,
	}, reqBootstrap)
	if err != nil {
		return err
	}
	var login struct {
		Success bool   `json:"success"`
		Message string `json:"message"`
		User    struct {
			UserID   int    `json:"userId"`
			UserName string `json:"userName"`
		} `json:"user"`
	}
	if err := json.Unmarshal(loginBody, &login); err != nil {
		return errf("login response was not JSON: %s", preview(loginBody, 200))
	}
	if !login.Success {
		// login.Message is JSAP's own text ("Invalid credentials"), never a secret.
		return errf("JSAP login failed: %s", login.Message)
	}

	userID := login.User.UserID
	if userID == 0 {
		userID = c.cfg.UserID
	}
	userName := login.User.UserName
	if userName == "" {
		userName = c.cfg.Username
	}
	companies := make([]map[string]any, 0, len(Companies))
	for id, name := range Companies {
		companies = append(companies, map[string]any{"id": id, "company": name})
	}
	if _, err := c.do(ctx, verbPost, "/websession/set", nil, map[string]any{
		"userId":    userID,
		"userName":  userName,
		"companies": companies,
	}, reqBootstrap); err != nil {
		return err
	}
	// Company scoping. Not fatal: every company-scoped catalogue command also
	// sends its own explicit company parameter.
	_, _ = c.do(ctx, verbPost, "/websession/updateSelectedCompany", nil,
		map[string]any{"companyId": c.company}, reqBootstrap)

	c.authedAt = time.Now()
	return nil
}

// hasReadLeaf reports whether the last path segment names a read action.
func hasReadLeaf(path string) bool {
	leaf := path
	if i := strings.IndexByte(leaf, '?'); i >= 0 {
		leaf = leaf[:i]
	}
	leaf = strings.TrimRight(leaf, "/")
	if i := strings.LastIndexByte(leaf, '/'); i >= 0 {
		leaf = leaf[i+1:]
	}
	leaf = strings.ToLower(leaf)
	for _, prefix := range readLeafPrefixes {
		if strings.HasPrefix(leaf, prefix) {
			return true
		}
	}
	return false
}

// unwrap returns the `data` payload of JSAP's standard {success,data} envelope.
// A success:false envelope is returned whole — the server's message is the
// answer in that case (e.g. the Tickets workload endpoint's DBNull bug), and
// silently handing back an empty data field would read as "no rows".
func unwrap(raw []byte, want bool) (json.RawMessage, error) {
	trimmed := bytes.TrimSpace(raw)
	if len(trimmed) == 0 {
		return json.RawMessage("null"), nil
	}
	if !json.Valid(trimmed) {
		// Some endpoints answer with HTML or plain text; hand it back as a JSON
		// string so the tool result stays valid JSON.
		encoded, err := json.Marshal(string(trimmed))
		if err != nil {
			return nil, errf("encoding non-JSON response: %v", err)
		}
		return encoded, nil
	}
	if !want {
		return json.RawMessage(trimmed), nil
	}
	var envelope map[string]json.RawMessage
	if err := json.Unmarshal(trimmed, &envelope); err != nil {
		return json.RawMessage(trimmed), nil // a bare array or scalar
	}
	data, hasData := envelope["data"]
	successRaw, hasSuccess := envelope["success"]
	if !hasData || !hasSuccess {
		return json.RawMessage(trimmed), nil
	}
	var success bool
	if err := json.Unmarshal(successRaw, &success); err != nil || !success {
		return json.RawMessage(trimmed), nil
	}
	return data, nil
}

var (
	userRowRe   = regexp.MustCompile(`(?s)<tr class="user-row">(.*?)</tr>`)
	userIDRe    = regexp.MustCompile(`data-userid="(\d+)"`)
	typeDeptRe  = regexp.MustCompile(`(?s)user-empid">.*?</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>`)
	htmlTagRe   = regexp.MustCompile(`<[^>]+>`)
	cellPattern = `(?s)<td class="%s">(.*?)</td>`
)

// scrapeUserTable parses the server-rendered User Management page into rows.
// JSAP publishes no JSON list for it, so the page IS the endpoint; this is a
// pure read of a page the browser fetches identically. Ported from
// jsap-cli/jsap/modules/users.py:_all_users.
func scrapeUserTable(raw []byte) (json.RawMessage, error) {
	page := string(raw)
	type userRow struct {
		UserID     *int   `json:"userId"`
		Name       string `json:"name"`
		EmpID      string `json:"empId"`
		UserType   string `json:"userType"`
		Department string `json:"department"`
		Status     string `json:"status"`
	}
	rows := []userRow{}
	for _, match := range userRowRe.FindAllStringSubmatch(page, -1) {
		block := match[1]
		row := userRow{
			Name:   cell(block, "user-name"),
			EmpID:  cell(block, "user-empid"),
			Status: "locked",
		}
		if id := userIDRe.FindStringSubmatch(block); id != nil {
			if n, err := strconv.Atoi(id[1]); err == nil {
				row.UserID = &n
			}
		}
		if td := typeDeptRe.FindStringSubmatch(block); td != nil {
			row.UserType = clean(td[1])
			row.Department = clean(td[2])
		}
		if strings.Contains(block, "slider round green") {
			row.Status = "active"
		}
		rows = append(rows, row)
	}
	encoded, err := json.Marshal(rows)
	if err != nil {
		return nil, errf("encoding scraped user rows: %v", err)
	}
	return encoded, nil
}

func cell(block, class string) string {
	re := regexp.MustCompile(fmt.Sprintf(cellPattern, regexp.QuoteMeta(class)))
	if m := re.FindStringSubmatch(block); m != nil {
		return clean(m[1])
	}
	return ""
}

func clean(s string) string {
	return strings.TrimSpace(html.UnescapeString(htmlTagRe.ReplaceAllString(s, "")))
}

func preview(b []byte, n int) string {
	s := strings.TrimSpace(string(b))
	if len(s) <= n {
		return s
	}
	return s[:n] + "…"
}
