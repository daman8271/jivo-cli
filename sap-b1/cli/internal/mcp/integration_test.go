package mcp

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"sort"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"sapb1/internal/config"
)

// End-to-end tests for the MCP tool surface, driven through the real JSON-RPC
// tools/call path against a fake SAP Service Layer on httptest.
//
// These cover the things a decoder unit test cannot: which CompanyDB the Login
// payload actually carried, how many HTTP requests a "count" really costs,
// whether odata.nextLink is followed, and — the one that matters most — that
// nothing in the whole run issues anything but GET plus Login/Logout.
//
// No real SAP is contacted. The Mac this is developed on cannot reach SAP at
// all (the server IP-whitelists), which is precisely why the fake has to be
// faithful about the parts that bite: cookie-scoped sessions, $inlinecount
// encodings, Prefer: odata.maxpagesize, and the HTTP Date header.

// recordedRequest is one request the fake saw.
type recordedRequest struct {
	Method    string
	Path      string
	Query     url.Values
	Prefer    string
	CompanyDB string // Login only
	Session   string // B1SESSION cookie sent by the client, if any
}

// fakeSAP is a minimal, deliberately strict Service Layer.
type fakeSAP struct {
	t *testing.T

	// total rows the entity set holds.
	total int
	// pageSize the server returns per page unless Prefer overrides it.
	pageSize int
	// honourPrefer makes it respect Prefer: odata.maxpagesize.
	honourPrefer bool
	// countAs controls how odata.count is encoded: "number", "string", or ""
	// to omit it entirely (a server that ignores $inlinecount).
	countAs string
	// reportedCount, when > 0, is served as odata.count INSTEAD of total. It
	// models the real cases where the server's own total legitimately exceeds
	// the rows a complete sweep can return: rows deleted between the first
	// page's $inlinecount and the last page, row-level authorisation filtering,
	// or a view. $inlinecount is also skip-agnostic, so it is not a promise
	// about what is left.
	reportedCount int
	// loginDelay is how long POST /Login takes. A real Login is a network round
	// trip; without a delay, concurrent callers can accidentally serialise
	// themselves and hide a login storm.
	loginDelay time.Duration
	// ignoreTopZero models a Service Layer that does NOT honour $top=0 and
	// serves a full page anyway. The live one does honour it (verified on
	// Orders/Invoices/Items/BusinessPartners/JournalEntries across all three
	// company databases), but a count's CORRECTNESS must not rest on that — so
	// the pessimistic server is tested too.
	ignoreTopZero bool
	// fixedDate, when non-zero, is served as the HTTP Date header.
	fixedDate time.Time
	// omitDate strips the Date header entirely.
	omitDate bool

	mu       sync.Mutex
	requests []recordedRequest
	srv      *httptest.Server
	// valid is the set of session values the fake still accepts; a GET carrying
	// anything else gets a 401, exactly as an expired Service Layer session
	// does. loginGen keeps the value of a company's FIRST login stable
	// ("sess-<company>"), so the company-scoping assertions elsewhere read the
	// same as before, and only re-logins get a distinguishable suffix.
	valid    map[string]bool
	loginGen map[string]int
}

func newFakeSAP(t *testing.T, f *fakeSAP) *fakeSAP {
	t.Helper()
	f.t = t
	if f.pageSize <= 0 {
		f.pageSize = 20
	}
	if f.countAs == "" {
		f.countAs = "number"
	}
	f.valid = map[string]bool{}
	f.loginGen = map[string]int{}
	f.srv = httptest.NewTLSServer(http.HandlerFunc(f.handle))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeSAP) handle(w http.ResponseWriter, r *http.Request) {
	rec := recordedRequest{
		Method: r.Method,
		Path:   r.URL.Path,
		Query:  r.URL.Query(),
		Prefer: r.Header.Get("Prefer"),
	}
	if ck, err := r.Cookie("B1SESSION"); err == nil {
		rec.Session = ck.Value
	}

	switch {
	case f.omitDate:
		w.Header()["Date"] = nil
	case !f.fixedDate.IsZero():
		w.Header().Set("Date", f.fixedDate.UTC().Format(http.TimeFormat))
	}

	if r.Method == http.MethodPost && strings.HasSuffix(r.URL.Path, "/Login") {
		var body struct {
			CompanyDB string `json:"CompanyDB"`
			UserName  string `json:"UserName"`
			Password  string `json:"Password"`
		}
		_ = json.NewDecoder(r.Body).Decode(&body)
		rec.CompanyDB = body.CompanyDB
		f.record(rec)
		if f.loginDelay > 0 {
			time.Sleep(f.loginDelay)
		}

		// The session cookie is SCOPED TO THE COMPANY. That is what lets a test
		// prove a read was answered by the company it asked for: a leaked
		// session would show up as a GET carrying another company's cookie.
		value := f.mintSession(body.CompanyDB)
		http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: value})
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"SessionId":%q}`, value)
		return
	}
	if r.Method == http.MethodPost && strings.HasSuffix(r.URL.Path, "/Logout") {
		f.record(rec)
		w.WriteHeader(http.StatusNoContent)
		return
	}
	f.record(rec)

	// An expired session is a 401, which is what the client's one-shot re-login
	// path exists for.
	if rec.Session != "" && !f.sessionValid(rec.Session) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusUnauthorized)
		fmt.Fprint(w, `{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session."}}}`)
		return
	}

	if r.Method != http.MethodGet {
		// RULE 0 tripwire from the server side: if the MCP surface ever learns
		// to write, the fake fails the test rather than pretending it worked.
		f.t.Errorf("fake Service Layer received a %s %s — the MCP surface must only ever GET (plus Login/Logout)", r.Method, r.URL.Path)
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	q := r.URL.Query()
	skip := atoiOr(q.Get("$skip"), 0)
	// $top is read as PRESENT-or-absent, not as >0, because $top=0 is a real
	// request with a real meaning: "tell me the total, send me no rows". The
	// live Service Layer honours it on every entity set and company database
	// JIVO runs, so the fake must too — reading it as "no top" would have let a
	// count that silently hauls a full page of documents pass as correct.
	_, topSet := q["$top"]
	top := atoiOr(q.Get("$top"), 0)
	if f.ignoreTopZero && topSet && top == 0 {
		topSet = false
	}

	page := f.pageSize
	if f.honourPrefer {
		if p := r.Header.Get("Prefer"); strings.HasPrefix(p, "odata.maxpagesize=") {
			if n, err := strconv.Atoi(strings.TrimPrefix(p, "odata.maxpagesize=")); err == nil && n > 0 {
				page = n
			}
		}
	}

	remaining := f.total - skip
	if remaining < 0 {
		remaining = 0
	}
	if topSet && top < remaining {
		remaining = top
	}
	n := remaining
	if n > page {
		n = page
	}

	rows := make([]map[string]any, 0, n)
	for i := 0; i < n; i++ {
		id := skip + i + 1
		rows = append(rows, map[string]any{"DocEntry": id, "DocNum": 1000 + id})
	}

	reported := f.total
	if f.reportedCount > 0 {
		reported = f.reportedCount
	}
	body := map[string]any{"value": rows}
	if q.Get("$inlinecount") == "allpages" {
		switch f.countAs {
		case "number":
			body["odata.count"] = reported
		case "string":
			// The Service Layer really does encode this as a string on some
			// versions; extractODataCount handles both, so both are tested.
			body["odata.count"] = strconv.Itoa(reported)
		case "omit":
			// A server that ignored $inlinecount. The tool must refuse to
			// invent a total rather than pass off a page length as one.
		}
	}
	if remaining > n {
		next := url.Values{}
		for k, vs := range q {
			next[k] = vs
		}
		next.Set("$skip", strconv.Itoa(skip+n))
		body["odata.nextLink"] = strings.TrimPrefix(r.URL.Path, "/b1s/v1/") + "?" + next.Encode()
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(body)
}

func (f *fakeSAP) record(rec recordedRequest) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.requests = append(f.requests, rec)
}

// mintSession issues a session value for a company and marks it valid. The
// first login for a company gets the bare "sess-<company>" name; re-logins get
// a suffix so a test can tell them apart.
func (f *fakeSAP) mintSession(company string) string {
	f.mu.Lock()
	defer f.mu.Unlock()
	gen := f.loginGen[company]
	f.loginGen[company] = gen + 1
	value := "sess-" + company
	if gen > 0 {
		value = fmt.Sprintf("sess-%s-r%d", company, gen)
	}
	f.valid[value] = true
	return value
}

func (f *fakeSAP) sessionValid(value string) bool {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.valid[value]
}

// expireAllSessions invalidates every session issued so far, so the next
// request carrying one gets a 401 — the real "your ~30-minute session ran out"
// event, which under concurrency is where a login storm starts.
func (f *fakeSAP) expireAllSessions() {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.valid = map[string]bool{}
}

func (f *fakeSAP) seen() []recordedRequest {
	f.mu.Lock()
	defer f.mu.Unlock()
	out := make([]recordedRequest, len(f.requests))
	copy(out, f.requests)
	return out
}

// logins returns the CompanyDB of every POST /Login, in order.
func (f *fakeSAP) logins() []string {
	var out []string
	for _, r := range f.seen() {
		if r.Method == http.MethodPost && strings.HasSuffix(r.Path, "/Login") {
			out = append(out, r.CompanyDB)
		}
	}
	return out
}

func (f *fakeSAP) gets() []recordedRequest {
	var out []recordedRequest
	for _, r := range f.seen() {
		if r.Method == http.MethodGet {
			out = append(out, r)
		}
	}
	return out
}

func atoiOr(s string, def int) int {
	if s == "" {
		return def
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return def
	}
	return n
}

// server builds an MCP Server pointed at the fake, defaulting to Oil.
func (f *fakeSAP) server() *Server {
	f.t.Helper()
	u, err := url.Parse(f.srv.URL)
	if err != nil {
		f.t.Fatal(err)
	}
	port, err := strconv.Atoi(u.Port())
	if err != nil {
		f.t.Fatal(err)
	}
	return NewServer(&config.Config{
		Host: u.Hostname(), Port: port,
		CompanyDB: "JIVO_OIL_HANADB",
		User:      "tester", Password: "pw",
		Insecure: true, Timeout: 10,
	})
}

// isolateHome points the session cache at a throwaway HOME, so these tests
// never read or write the developer's real ~/.sapb1-session-*.json.
func isolateHome(t *testing.T) {
	t.Helper()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
}

// callRows drives a tools/call and decodes the row response, failing on a tool
// error. It returns both the typed shape and the raw map, because some
// assertions are about which keys exist at all.
func callRows(t *testing.T, s *Server, tool string, args map[string]any) (rowsResponse, map[string]any) {
	t.Helper()
	isErr, text := callTool(t, s, tool, args)
	if isErr {
		t.Fatalf("%s returned a tool error: %s", tool, text)
	}
	var typed rowsResponse
	if err := json.Unmarshal([]byte(text), &typed); err != nil {
		t.Fatalf("%s result is not a rows response (%v): %s", tool, err, text)
	}
	var raw map[string]any
	if err := json.Unmarshal([]byte(text), &raw); err != nil {
		t.Fatalf("%s result is not a JSON object (%v): %s", tool, err, text)
	}
	return typed, raw
}

// ---------------------------------------------------------------------------
// D1 — the company actually queried
// ---------------------------------------------------------------------------

// TestCompanyArgumentReachesTheLoginPayload is the regression test for the
// worst failure this tool can produce: answering a Beverages question with
// Oil's books. The assertion is deliberately made at the wire, on the /Login
// body, not on anything the server merely echoes back — an echo can be right
// while the read was wrong.
func TestCompanyArgumentReachesTheLoginPayload(t *testing.T) {
	cases := []struct {
		name string
		arg  map[string]any
		want string
	}{
		{"mart", map[string]any{"company": "JIVO_MART_HANADB"}, "JIVO_MART_HANADB"},
		{"beverages", map[string]any{"company": "JIVO_BEVERAGES_HANADB"}, "JIVO_BEVERAGES_HANADB"},
		{"oil explicitly", map[string]any{"company": "JIVO_OIL_HANADB"}, "JIVO_OIL_HANADB"},
		{"omitted uses the configured default", map[string]any{}, "JIVO_OIL_HANADB"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 5})
			s := f.server()

			args := map[string]any{"entity": "Invoices", "top": 5.0}
			for k, v := range tc.arg {
				args[k] = v
			}
			got, _ := callRows(t, s, "sapb1_query", args)

			logins := f.logins()
			if len(logins) != 1 {
				t.Fatalf("logins = %v, want exactly one", logins)
			}
			if logins[0] != tc.want {
				t.Errorf("POST /Login carried CompanyDB=%q, want %q — the read went to the WRONG COMPANY", logins[0], tc.want)
			}
			if got.Company != tc.want {
				t.Errorf("response company = %q, want %q", got.Company, tc.want)
			}
			// Every GET must carry the session minted for that company.
			for _, g := range f.gets() {
				if g.Session != "sess-"+tc.want {
					t.Errorf("GET %s carried session %q, want %q — a session from another company leaked into the read", g.Path, g.Session, "sess-"+tc.want)
				}
			}
		})
	}
}

// TestAlternatingCompaniesNeverReplayASession covers both halves of the session
// story at once:
//
//	CORRECTNESS — switching company must never reuse the previous company's
//	session (that would be the wrong-company leak, silently).
//	COST — coming BACK to a company already logged into must not re-Login.
//	With one shared cache file each switch overwrote the other's session, so a
//	"compare Mart against Beverages" loop became a login storm against a finite,
//	~30-minute-lived SAP resource.
func TestAlternatingCompaniesNeverReplayASession(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 5})
	s := f.server()

	order := []string{"JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB", "JIVO_OIL_HANADB"}
	for _, company := range order {
		got, _ := callRows(t, s, "sapb1_query", map[string]any{
			"entity": "Invoices", "top": 5.0, "company": company,
		})
		if got.Company != company {
			t.Fatalf("response company = %q, want %q", got.Company, company)
		}
	}

	// Three distinct companies were read, so exactly three logins — not five.
	wantLogins := []string{"JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB", "JIVO_OIL_HANADB"}
	if got := f.logins(); len(got) != len(wantLogins) {
		t.Errorf("logins = %v, want one per distinct company %v — per-identity session cache regressed into login churn", got, wantLogins)
	} else {
		for i := range wantLogins {
			if got[i] != wantLogins[i] {
				t.Errorf("login %d = %q, want %q", i, got[i], wantLogins[i])
			}
		}
	}

	// And the reads themselves: five GETs, each carrying its own company's
	// session, in the order the calls were made.
	gets := f.gets()
	if len(gets) != len(order) {
		t.Fatalf("GET count = %d, want %d", len(gets), len(order))
	}
	for i, g := range gets {
		if want := "sess-" + order[i]; g.Session != want {
			t.Errorf("read %d used session %q, want %q — WRONG-COMPANY SESSION LEAK", i, g.Session, want)
		}
	}
}

// TestConvenienceToolsAlsoScopeTheCompany — D1 was a defect of the whole
// surface, not of sapb1_query alone.
func TestConvenienceToolsAlsoScopeTheCompany(t *testing.T) {
	for _, tool := range []string{"sapb1_orders", "sapb1_invoices", "sapb1_items", "sapb1_partners"} {
		t.Run(tool, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 3})
			got, _ := callRows(t, f.server(), tool, map[string]any{
				"company": "JIVO_BEVERAGES_HANADB", "top": 3.0,
			})
			if logins := f.logins(); len(logins) != 1 || logins[0] != "JIVO_BEVERAGES_HANADB" {
				t.Errorf("%s logged in as %v, want [JIVO_BEVERAGES_HANADB]", tool, logins)
			}
			if got.Company != "JIVO_BEVERAGES_HANADB" {
				t.Errorf("%s echoed company %q", tool, got.Company)
			}
		})
	}
}

// TestDoctorTestsTheRequestedCompany — doctor's whole job is proving a
// connection; pinned to one company it cannot prove Mart or Beverages is
// reachable.
func TestDoctorTestsTheRequestedCompany(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 1})
	isErr, text := callTool(t, f.server(), "sapb1_doctor", map[string]any{"company": "JIVO_BEVERAGES_HANADB"})
	if isErr {
		t.Fatalf("doctor returned an error: %s", text)
	}
	var report struct {
		OK      bool   `json:"ok"`
		Company string `json:"company"`
		Config  struct {
			Password string `json:"password"`
		} `json:"config"`
		Checks []struct {
			Name   string `json:"name"`
			OK     bool   `json:"ok"`
			Detail string `json:"detail"`
		} `json:"checks"`
	}
	if err := json.Unmarshal([]byte(text), &report); err != nil {
		t.Fatalf("doctor result is not JSON (%v): %s", err, text)
	}
	if !report.OK {
		t.Errorf("doctor.ok = false against a healthy fake: %s", text)
	}
	if report.Company != "JIVO_BEVERAGES_HANADB" {
		t.Errorf("doctor company = %q, want JIVO_BEVERAGES_HANADB", report.Company)
	}
	if logins := f.logins(); len(logins) != 1 || logins[0] != "JIVO_BEVERAGES_HANADB" {
		t.Errorf("doctor logged in as %v, want [JIVO_BEVERAGES_HANADB] — it must test the company it was asked about", logins)
	}
	// The password must never appear, in any field, ever.
	if strings.Contains(text, "pw") && !strings.Contains(report.Config.Password, "*") {
		t.Errorf("doctor report may be leaking the password: %s", text)
	}
	if strings.Contains(report.Config.Password, "pw") {
		t.Errorf("doctor reported the real password: %q", report.Config.Password)
	}
}

// ---------------------------------------------------------------------------
// D4/D5 — pagination past the page cap, and honest truncation
// ---------------------------------------------------------------------------

// TestTopBeyondOnePageFollowsNextLink pins the N+1 truncation probe on BOTH
// sides of the boundary. An off-by-one here either hands back one row too many
// or claims a complete result is truncated, and both are invisible without an
// exact-boundary test.
func TestTopBeyondOnePageFollowsNextLink(t *testing.T) {
	cases := []struct {
		name          string
		total         int
		top           int
		wantRows      int
		wantTruncated bool
		wantNextSkip  int // only checked when wantTruncated
	}{
		{"fewer rows than asked for", 44, 45, 44, false, 0},
		{"exactly as many rows as asked for", 45, 45, 45, false, 0},
		{"one row more than asked for", 46, 45, 45, true, 45},
		{"far more rows than asked for", 500, 45, 45, true, 45},
		{"single page", 100, 5, 5, true, 5},
		{"exact page multiple", 40, 40, 40, false, 0},
		{"one over a page multiple", 41, 40, 40, true, 40},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: tc.total, pageSize: 20})
			got, raw := callRows(t, f.server(), "sapb1_query", map[string]any{
				"entity": "Orders", "top": float64(tc.top),
			})

			if got.RowsInPage != tc.wantRows || len(got.Rows) != tc.wantRows {
				t.Errorf("rows_in_page = %d, len(rows) = %d, want %d", got.RowsInPage, len(got.Rows), tc.wantRows)
			}
			if got.Truncated != tc.wantTruncated {
				t.Errorf("truncated = %v, want %v (total=%d, top=%d)", got.Truncated, tc.wantTruncated, tc.total, tc.top)
			}
			if tc.wantTruncated {
				if got.NextSkip == nil {
					t.Fatalf("truncated result carries no next_skip — the agent cannot continue")
				}
				if *got.NextSkip != tc.wantNextSkip {
					t.Errorf("next_skip = %d, want %d", *got.NextSkip, tc.wantNextSkip)
				}
			} else if _, present := raw["next_skip"]; present {
				t.Errorf("next_skip present on a complete result: %v", raw["next_skip"])
			}

			// The rows must be the FIRST n, in order — a probe row must never
			// leak into the result.
			for i, row := range got.Rows {
				if de, ok := row["DocEntry"].(float64); !ok || int(de) != i+1 {
					t.Fatalf("row %d = %v, want DocEntry %d", i, row, i+1)
				}
			}
		})
	}
}

// TestDefaultTopWhenOmitted — the default must stay 20 and must still say so
// when there is more.
func TestDefaultTopWhenOmitted(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 100, pageSize: 20})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders"})
	if got.RowsInPage != defaultTop {
		t.Errorf("rows_in_page = %d, want the default %d", got.RowsInPage, defaultTop)
	}
	if !got.Truncated {
		t.Error("truncated = false although 100 rows match a default-capped request")
	}
	if got.NextSkip == nil || *got.NextSkip != defaultTop {
		t.Errorf("next_skip = %v, want %d", got.NextSkip, defaultTop)
	}
}

// TestSkipContinuesWhereTheLastCallStopped — the documented way to continue,
// replacing the benchmark's "&$skip=N smuggled inside the filter string" hack.
func TestSkipContinuesWhereTheLastCallStopped(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 100, pageSize: 20})
	s := f.server()

	first, _ := callRows(t, s, "sapb1_query", map[string]any{"entity": "Orders", "top": 45.0})
	if first.NextSkip == nil {
		t.Fatal("first page not marked truncated")
	}
	second, _ := callRows(t, s, "sapb1_query", map[string]any{
		"entity": "Orders", "top": 45.0, "skip": float64(*first.NextSkip),
	})

	if second.RowsInPage != 45 {
		t.Errorf("second page rows = %d, want 45", second.RowsInPage)
	}
	if de, ok := second.Rows[0]["DocEntry"].(float64); !ok || int(de) != 46 {
		t.Errorf("second page starts at %v, want DocEntry 46 — skip did not continue the window", second.Rows[0]["DocEntry"])
	}
	if second.NextSkip == nil || *second.NextSkip != 90 {
		t.Errorf("second next_skip = %v, want 90 (skip 45 + 45 rows)", second.NextSkip)
	}

	// Third call drains the set: 10 rows left, so not truncated.
	third, raw := callRows(t, s, "sapb1_query", map[string]any{
		"entity": "Orders", "top": 45.0, "skip": float64(*second.NextSkip),
	})
	if third.RowsInPage != 10 || third.Truncated {
		t.Errorf("final page rows = %d truncated = %v, want 10/false", third.RowsInPage, third.Truncated)
	}
	if _, present := raw["next_skip"]; present {
		t.Error("final page still advertises next_skip")
	}
}

// ---------------------------------------------------------------------------
// D3 — the server-side count
// ---------------------------------------------------------------------------

// TestCountModeIsOneRequestAndAServerTotal. The benchmark's q06 failed only
// because an 18-call paged tally straddled live postings — the number was never
// true at any single instant. count=true has to be ONE request, or it has the
// same problem in a smaller way.
func TestCountModeIsOneRequestAndAServerTotal(t *testing.T) {
	for _, encoding := range []string{"number", "string"} {
		t.Run("odata.count as a "+encoding, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 12861, pageSize: 20, countAs: encoding})
			got, raw := callRows(t, f.server(), "sapb1_query", map[string]any{
				"entity": "Invoices",
				"filter": "DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'",
				"count":  true,
			})

			if got.TotalCount == nil {
				t.Fatalf("count mode returned no total_count: %v", raw)
			}
			if *got.TotalCount != 12861 {
				t.Errorf("total_count = %d, want 12861", *got.TotalCount)
			}
			if got.RowsInPage != 0 || len(got.Rows) != 0 {
				t.Errorf("count mode returned %d rows, want none", got.RowsInPage)
			}
			if rows, ok := raw["rows"].([]any); !ok || rows == nil {
				t.Errorf("rows must be an empty ARRAY in count mode, got %#v", raw["rows"])
			}
			if got.Truncated {
				t.Error("count mode must not be truncated — the total is the whole answer")
			}

			gets := f.gets()
			if len(gets) != 1 {
				t.Fatalf("count cost %d GETs, want exactly 1 (a paged tally is not atomic)", len(gets))
			}
			if gets[0].Query.Get("$inlinecount") != "allpages" {
				t.Errorf("count request did not ask for $inlinecount=allpages: %v", gets[0].Query)
			}
			if gets[0].Query.Get("$filter") == "" {
				t.Error("count request dropped the $filter — it would have counted the whole entity set")
			}
		})
	}
}

// TestCountModeRefusesToInventATotal — the honesty requirement. If the server
// ignored $inlinecount there is no total, and rows-in-page is NOT a substitute:
// reporting 20 as the number of open invoices is worse than failing, because it
// looks like an answer.
func TestCountModeRefusesToInventATotal(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 12861, pageSize: 20, countAs: "omit"})
	isErr, text := callTool(t, f.server(), "sapb1_query", map[string]any{
		"entity": "Invoices", "count": true,
	})
	if !isErr {
		t.Fatalf("count mode returned a result although the server gave no total: %s", text)
	}
	for _, want := range []string{"odata.count", "Invoices", "JIVO_OIL_HANADB"} {
		if !strings.Contains(text, want) {
			t.Errorf("refusal should mention %q, got: %s", want, text)
		}
	}
	// The refusal may NAME total_count as guidance, but it must not be a
	// result carrying one — and above all it must not hand back the page
	// length (20) as if it were the 12,861 the caller asked for.
	var raw map[string]any
	if err := json.Unmarshal([]byte(text), &raw); err == nil {
		if _, present := raw["total_count"]; present {
			t.Errorf("refusal decoded to a result carrying total_count: %s", text)
		}
	}
	for _, forbidden := range []string{`"total_count":`, `"rows_in_page":`} {
		if strings.Contains(text, forbidden) {
			t.Errorf("refusal must not be dressed up as a result (%s): %s", forbidden, text)
		}
	}
}

// TestCountModeOnConvenienceTools — counting is the fix for the "nine money
// questions needed hundreds of calls" class, so it must work everywhere.
func TestCountModeOnConvenienceTools(t *testing.T) {
	for _, tool := range []string{"sapb1_orders", "sapb1_invoices", "sapb1_items", "sapb1_partners"} {
		t.Run(tool, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 3390, pageSize: 20})
			got, _ := callRows(t, f.server(), tool, map[string]any{"count": true})
			if got.TotalCount == nil || *got.TotalCount != 3390 {
				t.Errorf("%s total_count = %v, want 3390", tool, got.TotalCount)
			}
			if len(f.gets()) != 1 {
				t.Errorf("%s count cost %d GETs, want 1", tool, len(f.gets()))
			}
		})
	}
}

// TestCountModeAppliesTheToolsBuiltInFilter — a count of "open orders" must
// count open orders, not all orders.
func TestCountModeAppliesTheToolsBuiltInFilter(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 42})
	callRows(t, f.server(), "sapb1_orders", map[string]any{"count": true, "open": true})

	gets := f.gets()
	if len(gets) != 1 {
		t.Fatalf("GETs = %d, want 1", len(gets))
	}
	if filter := gets[0].Query.Get("$filter"); !strings.Contains(filter, "DocumentStatus eq 'bost_Open'") {
		t.Errorf("$filter = %q, want the open-document filter", filter)
	}
}

// ---------------------------------------------------------------------------
// all=true — sweeping a whole set
// ---------------------------------------------------------------------------

func TestAllModeSweepsTheWholeSet(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 137, pageSize: 20, honourPrefer: true})
	got, raw := callRows(t, f.server(), "sapb1_items", map[string]any{
		"company": "JIVO_BEVERAGES_HANADB",
		"filter":  "MinInventory gt 0 and QuantityOnStock lt MinInventory and InventoryItem eq 'tYES'",
		"all":     true,
	})

	if got.RowsInPage != 137 {
		t.Errorf("rows_in_page = %d, want the whole set (137)", got.RowsInPage)
	}
	if got.Truncated {
		t.Error("truncated = true on a complete sweep")
	}
	if _, present := raw["next_skip"]; present {
		t.Error("complete sweep advertises next_skip")
	}
	if got.TotalCount == nil || *got.TotalCount != 137 {
		t.Errorf("total_count = %v, want 137 (all mode asks for $inlinecount)", got.TotalCount)
	}

	// The requested page size must actually travel, or a sweep costs 7x the
	// round trips it needs to.
	prefer := ""
	for _, g := range f.gets() {
		if g.Prefer != "" {
			prefer = g.Prefer
			break
		}
	}
	if prefer != fmt.Sprintf("odata.maxpagesize=%d", defaultAllPageSize) {
		t.Errorf("Prefer header = %q, want odata.maxpagesize=%d", prefer, defaultAllPageSize)
	}
	if n := len(f.gets()); n != 2 { // 137 rows at 100/page
		t.Errorf("sweep cost %d GETs, want 2 at a page size of %d", n, defaultAllPageSize)
	}
}

func TestAllModeRespectsAnExplicitPageSize(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 250, pageSize: 20, honourPrefer: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{
		"entity": "Orders", "all": true, "page_size": 500.0,
	})
	if got.RowsInPage != 250 {
		t.Errorf("rows_in_page = %d, want 250", got.RowsInPage)
	}
	if n := len(f.gets()); n != 1 {
		t.Errorf("sweep cost %d GETs, want 1 at page_size=500", n)
	}
	if p := f.gets()[0].Prefer; p != "odata.maxpagesize=500" {
		t.Errorf("Prefer = %q, want odata.maxpagesize=500", p)
	}
}

// TestAllModeReportsTruncationAtTheCap — all=true is bounded, and when the
// bound bites it must say so and say where to resume. Silence here is how a
// partial sweep gets reported as a complete one.
func TestAllModeReportsTruncationAtTheCap(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: maxAllRows + 37, pageSize: 500, honourPrefer: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{
		"entity": "Invoices", "all": true, "page_size": 500.0,
	})

	if got.RowsInPage != maxAllRows {
		t.Errorf("rows_in_page = %d, want the cap %d", got.RowsInPage, maxAllRows)
	}
	if !got.Truncated {
		t.Fatalf("truncated = false although %d rows match a %d cap", maxAllRows+37, maxAllRows)
	}
	if got.NextSkip == nil || *got.NextSkip != maxAllRows {
		t.Errorf("next_skip = %v, want %d", got.NextSkip, maxAllRows)
	}
	if got.TotalCount == nil || *got.TotalCount != int64(maxAllRows+37) {
		t.Errorf("total_count = %v, want %d — the agent must be able to see how much it is missing", got.TotalCount, maxAllRows+37)
	}
}

// TestAllModeWithSkipResumes — the resume path a truncated sweep advertises.
func TestAllModeWithSkipResumes(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 137, pageSize: 100, honourPrefer: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{
		"entity": "Orders", "all": true, "skip": 100.0,
	})
	if got.RowsInPage != 37 {
		t.Errorf("rows_in_page = %d, want the remaining 37", got.RowsInPage)
	}
	if got.Truncated {
		t.Error("truncated = true although the resume drained the set")
	}
	if de, ok := got.Rows[0]["DocEntry"].(float64); !ok || int(de) != 101 {
		t.Errorf("resume started at %v, want DocEntry 101", got.Rows[0]["DocEntry"])
	}
}

// ---------------------------------------------------------------------------
// D8 — as_of
// ---------------------------------------------------------------------------

// TestAsOfComesFromTheSAPServerClock. A count is only quotable if it is
// quotable "as of" something, and the only clock that matters is SAP's.
func TestAsOfComesFromTheSAPServerClock(t *testing.T) {
	isolateHome(t)
	stamp := time.Date(2026, 7, 30, 9, 33, 11, 0, time.UTC)
	f := newFakeSAP(t, &fakeSAP{total: 5, fixedDate: stamp})

	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders", "top": 5.0})
	if got.AsOfSource != "server" {
		t.Errorf("as_of_source = %q, want %q", got.AsOfSource, "server")
	}
	if want := stamp.Format(time.RFC3339); got.AsOf != want {
		t.Errorf("as_of = %q, want the server's Date header %q", got.AsOf, want)
	}
}

// TestAsOfFallsBackToLocalAndSaysSo — when the server sends no Date we must not
// pass our own clock off as SAP's.
func TestAsOfFallsBackToLocalAndSaysSo(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 5, omitDate: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders", "top": 5.0})

	if got.AsOfSource != "local" {
		t.Errorf("as_of_source = %q, want %q when the server sent no Date", got.AsOfSource, "local")
	}
	when, err := time.Parse(time.RFC3339, got.AsOf)
	if err != nil {
		t.Fatalf("as_of %q is not RFC3339: %v", got.AsOf, err)
	}
	if d := time.Since(when); d > time.Minute || d < -time.Minute {
		t.Errorf("local as_of %v is not close to now", when)
	}
}

// TestAsOfOnAMultiPageSweepIsTheFinalPage — the honest stamp for a sweep is
// when the LAST row was read, not the first.
func TestAsOfOnAMultiPageSweepIsTheFinalPage(t *testing.T) {
	isolateHome(t)
	stamp := time.Date(2026, 7, 30, 11, 0, 0, 0, time.UTC)
	f := newFakeSAP(t, &fakeSAP{total: 250, pageSize: 100, honourPrefer: true, fixedDate: stamp})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders", "all": true})
	if len(f.gets()) < 2 {
		t.Fatalf("expected a multi-page sweep, got %d GETs", len(f.gets()))
	}
	if got.AsOfSource != "server" || got.AsOf != stamp.Format(time.RFC3339) {
		t.Errorf("as_of = %q/%q, want the server stamp %q", got.AsOf, got.AsOfSource, stamp.Format(time.RFC3339))
	}
}

// ---------------------------------------------------------------------------
// D5 — one response shape, and no field named "count"
// ---------------------------------------------------------------------------

// TestResponseShapeIsIdenticalAcrossToolsAndModes. The old response called
// rows-in-a-page "count", sitting next to a 20-row cap — it read like a total
// and was routinely used as one. The name is gone, and every row-returning tool
// in every mode now emits exactly one shape, so an agent never has to guess
// which fields it got.
func TestResponseShapeIsIdenticalAcrossToolsAndModes(t *testing.T) {
	baseKeys := []string{"as_of", "as_of_source", "company", "entity", "rows", "rows_in_page", "truncated"}

	modes := []struct {
		name     string
		args     map[string]any
		total    int
		extra    []string // keys that must ALSO be present
		mustLack []string
	}{
		// total_count is present in EVERY mode against a server that honours
		// $inlinecount — including top, which is the mode agents use by default.
		// It used to be reachable only via all/count, so the default answer said
		// "truncated: true" with no sense of scale: 20 of 46 and 20 of 46,000
		// looked the same.
		{"top", map[string]any{"top": 5.0}, 5, []string{"total_count"}, []string{"next_skip"}},
		{"top truncated", map[string]any{"top": 5.0}, 50, []string{"next_skip", "total_count"}, nil},
		{"all", map[string]any{"all": true}, 30, []string{"total_count"}, []string{"next_skip"}},
		{"count", map[string]any{"count": true}, 30, []string{"total_count"}, []string{"next_skip"}},
	}
	tools := map[string]map[string]any{
		"sapb1_query":    {"entity": "Orders"},
		"sapb1_orders":   {},
		"sapb1_invoices": {},
		"sapb1_items":    {},
		"sapb1_partners": {},
	}

	for tool, toolArgs := range tools {
		for _, mode := range modes {
			t.Run(tool+"/"+mode.name, func(t *testing.T) {
				isolateHome(t)
				f := newFakeSAP(t, &fakeSAP{total: mode.total, pageSize: 20, honourPrefer: true})
				args := map[string]any{}
				for k, v := range toolArgs {
					args[k] = v
				}
				for k, v := range mode.args {
					args[k] = v
				}
				_, raw := callRows(t, f.server(), tool, args)

				want := append([]string{}, baseKeys...)
				want = append(want, mode.extra...)
				sort.Strings(want)

				var got []string
				for k := range raw {
					got = append(got, k)
				}
				sort.Strings(got)

				if strings.Join(got, ",") != strings.Join(want, ",") {
					t.Errorf("response keys\n got:  %v\n want: %v", got, want)
				}
				for _, k := range mode.mustLack {
					if _, present := raw[k]; present {
						t.Errorf("key %q must be omitted in %s mode, got %v", k, mode.name, raw[k])
					}
				}
				// The misleading name must be gone everywhere, forever.
				if _, present := raw["count"]; present {
					t.Errorf(`response carries a bare "count" key — it was renamed to rows_in_page precisely because it read as a total`)
				}
				if _, ok := raw["rows"].([]any); !ok {
					t.Errorf("rows must always be an array, got %#v", raw["rows"])
				}
			})
		}
	}
}

// TestOfflineToolsCarryNoBareCountKey — the rename had to reach the catalog
// tools too, or "count" still means two different things on one surface.
func TestOfflineToolsCarryNoBareCountKey(t *testing.T) {
	s := newTestServer()
	for tool, args := range map[string]map[string]any{
		"sapb1_entities": {"search": "order"},
		"sapb1_ops":      {"service": "Orders"},
	} {
		isErr, text := callTool(t, s, tool, args)
		if isErr {
			t.Fatalf("%s errored: %s", tool, text)
		}
		var raw map[string]any
		if err := json.Unmarshal([]byte(text), &raw); err != nil {
			t.Fatalf("%s result is not JSON: %v", tool, err)
		}
		if _, present := raw["count"]; present {
			t.Errorf("%s still returns a bare \"count\" key", tool)
		}
		if _, present := raw["company"]; !present {
			t.Errorf("%s does not echo company", tool)
		}
	}
}

// ---------------------------------------------------------------------------
// RULE 0 — at the wire
// ---------------------------------------------------------------------------

// TestWholeSurfaceIssuesOnlyReadsAndLogins is RULE 0 observed from the SAP
// side. TestRegisteredToolsAreReadOnly checks the advertised annotation and
// TestMCPPackageCannotReachWriteAPI checks the AST; this one drives every tool
// for real and inspects what actually arrived on the wire. Three independent
// layers, because a read-only guarantee asserted only in metadata is a promise,
// not a property.
func TestWholeSurfaceIssuesOnlyReadsAndLogins(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 60, pageSize: 20, honourPrefer: true})
	s := f.server()

	calls := []struct {
		tool string
		args map[string]any
	}{
		{"sapb1_doctor", map[string]any{}},
		{"sapb1_doctor", map[string]any{"company": "JIVO_MART_HANADB"}},
		{"sapb1_query", map[string]any{"entity": "Orders", "top": 45.0}},
		{"sapb1_query", map[string]any{"entity": "Invoices", "count": true}},
		{"sapb1_query", map[string]any{"entity": "Invoices", "all": true}},
		{"sapb1_fields", map[string]any{"entity": "BusinessPartners"}},
		{"sapb1_orders", map[string]any{"open": true, "top": 5.0}},
		{"sapb1_invoices", map[string]any{"open": true, "count": true}},
		{"sapb1_items", map[string]any{"lowStock": 10.0}},
		{"sapb1_partners", map[string]any{"customers": true, "company": "JIVO_BEVERAGES_HANADB"}},
		{"sapb1_entities", map[string]any{}},
		{"sapb1_ops", map[string]any{"service": "Orders"}},
	}
	for _, c := range calls {
		if isErr, text := callTool(t, s, c.tool, c.args); isErr {
			t.Fatalf("%s%v returned an error: %s", c.tool, c.args, text)
		}
	}

	seen := f.seen()
	if len(seen) == 0 {
		t.Fatal("the fake saw no requests at all — the test proves nothing")
	}
	for _, r := range seen {
		switch {
		case r.Method == http.MethodGet:
			// Reads are the point.
		case r.Method == http.MethodPost && (strings.HasSuffix(r.Path, "/Login") || strings.HasSuffix(r.Path, "/Logout")):
			// Session establishment/teardown only.
		default:
			t.Errorf("RULE 0 VIOLATION: the MCP surface issued %s %s", r.Method, r.Path)
		}
	}
	t.Logf("read-only wire check: %d requests, %d GETs, logins to %v", len(seen), len(f.gets()), f.logins())
}
