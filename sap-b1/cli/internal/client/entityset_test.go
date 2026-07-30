package client

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// readFake is a minimal Service Layer that records what actually arrived on the
// wire — path AND raw query string — which is the only place the "the query
// options were silently dropped" defect is visible.
type readFake struct {
	mu         sync.Mutex
	paths      []string
	rawQueries []string
	logins     int
	loginDelay time.Duration
	srv        *httptest.Server
}

func newReadFake(t *testing.T) *readFake {
	t.Helper()
	f := &readFake{}
	f.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPost && strings.HasSuffix(r.URL.Path, "/Login") {
			f.mu.Lock()
			f.logins++
			f.mu.Unlock()
			if f.loginDelay > 0 {
				time.Sleep(f.loginDelay)
			}
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "sess"})
			_, _ = w.Write([]byte(`{"SessionId":"sess"}`))
			return
		}
		f.mu.Lock()
		f.paths = append(f.paths, r.URL.Path)
		f.rawQueries = append(f.rawQueries, r.URL.RawQuery)
		f.mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{"value": []map[string]any{{"DocEntry": 1}}})
	}))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *readFake) client(t *testing.T, store *SessionStore) *Client {
	t.Helper()
	u, err := url.Parse(f.srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	port, err := strconv.Atoi(u.Port())
	if err != nil {
		t.Fatal(err)
	}
	cfg := &config.Config{
		Host: u.Hostname(), Port: port,
		CompanyDB: "JIVO_OIL_HANADB", User: "tester", Password: "pw",
		Insecure: true, Timeout: 10,
	}
	return NewWithSessions(cfg, store)
}

func (f *readFake) requests() (paths, queries []string, logins int) {
	f.mu.Lock()
	defer f.mu.Unlock()
	return append([]string{}, f.paths...), append([]string{}, f.rawQueries...), f.logins
}

// ---------------------------------------------------------------------------
// The entity name must never be able to reshape the request URL
// ---------------------------------------------------------------------------

// TestQueryRejectsAnEntityThatWouldReshapeTheURL is the root-cause regression
// test. The request path was built as entitySet + "?" + queryString, so a '#'
// in the entity turned every query option into a URI fragment that net/http
// drops: the GET went out as a bare, unfiltered, unprojected read of the whole
// entity set and CAME BACK 200. Proven live against production: entity
// "Orders#" produced `GET /b1s/v1/Orders` with an empty raw query.
//
// The assertion is at the wire on purpose — a check that merely returned an
// error while still sending the request would be no fix at all.
func TestQueryRejectsAnEntityThatWouldReshapeTheURL(t *testing.T) {
	bad := []string{
		"Orders#",
		"Orders#fragment",
		"Orders?$top=1",
		"Orders&$select=DocEntry",
		"Orders%23",
		"Order s",
		"Orders\tlist",
		"Orders\nOrders",
		"   ",
		"",
	}
	for _, entity := range bad {
		t.Run(fmt.Sprintf("%q", entity), func(t *testing.T) {
			isolateHome(t)
			f := newReadFake(t)
			c := f.client(t, nil)

			opts := QueryOptions{Filter: "DocTotal gt 100", Select: "DocEntry", Top: 3}
			if _, err := c.Query(context.Background(), entity, opts); err == nil {
				t.Errorf("Query(%q) was accepted", entity)
			} else if _, ok := err.(*errs.UsageError); !ok {
				t.Errorf("Query(%q) = %T, want *errs.UsageError", entity, err)
			}
			if _, err := c.QueryAll(context.Background(), entity, opts); err == nil {
				t.Errorf("QueryAll(%q) was accepted", entity)
			}

			paths, _, logins := f.requests()
			if len(paths) != 0 {
				t.Errorf("a malformed entity still reached the server: %v", paths)
			}
			if logins != 0 {
				t.Errorf("a malformed entity still cost %d Logins", logins)
			}
		})
	}
}

// TestQueryKeepsEveryOptionOnTheWireForAValidEntity is the positive control:
// the guard must not have been bought by breaking normal reads. Surrounding
// whitespace is trimmed rather than rejected, because a stray space is a
// typing accident with an unambiguous intent — unlike a '#', which silently
// changes what is asked.
func TestQueryKeepsEveryOptionOnTheWireForAValidEntity(t *testing.T) {
	for _, entity := range []string{"Orders", "  Orders  ", "BusinessPartners", "Orders(123)", "Orders(123)/DocumentLines", "U_MyUDO"} {
		t.Run(entity, func(t *testing.T) {
			isolateHome(t)
			f := newReadFake(t)
			c := f.client(t, nil)

			if _, err := c.Query(context.Background(), entity, QueryOptions{
				Filter: "DocTotal gt 100", Select: "DocEntry", Top: 3, InlineCount: true,
			}); err != nil {
				t.Fatalf("Query(%q) = %v", entity, err)
			}

			paths, queries, _ := f.requests()
			if len(paths) != 1 {
				t.Fatalf("requests = %v, want exactly one", paths)
			}
			if want := "/b1s/v1/" + strings.TrimSpace(entity); paths[0] != want {
				t.Errorf("path = %q, want %q", paths[0], want)
			}
			q, err := url.ParseQuery(queries[0])
			if err != nil {
				t.Fatalf("raw query %q: %v", queries[0], err)
			}
			for param, want := range map[string]string{
				"$filter":      "DocTotal gt 100",
				"$select":      "DocEntry",
				"$top":         "3",
				"$inlinecount": "allpages",
			} {
				if got := q.Get(param); got != want {
					t.Errorf("%s = %q, want %q — the option never reached the server", param, got, want)
				}
			}
		})
	}
}

// TestValidateEntitySetIsUsableStandalone documents the contract callers
// (internal/mcp, internal/cli) rely on to fail early with a readable message.
func TestValidateEntitySetIsUsableStandalone(t *testing.T) {
	if err := ValidateEntitySet("Orders"); err != nil {
		t.Errorf("ValidateEntitySet(Orders) = %v", err)
	}
	err := ValidateEntitySet("Orders#")
	if err == nil {
		t.Fatal("ValidateEntitySet(Orders#) = nil")
	}
	for _, want := range []string{"Orders#", "$filter"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("message %q should mention %q so the fix is obvious", err, want)
		}
	}
}

// ---------------------------------------------------------------------------
// Session sharing
// ---------------------------------------------------------------------------

// TestSessionStoreCollapsesConcurrentLogins is the client-level half of the
// login-storm fix. Each concurrent caller gets its own Client (they mutate
// their own session fields, so sharing the Client itself would be a data race);
// what they share is the SESSION, and the store's per-identity lock is what
// makes that one Login instead of N.
func TestSessionStoreCollapsesConcurrentLogins(t *testing.T) {
	const parallel = 30

	isolateHome(t)
	f := newReadFake(t)
	f.loginDelay = 20 * time.Millisecond
	store := NewSessionStore()

	var wg sync.WaitGroup
	start := make(chan struct{})
	errCh := make(chan error, parallel)
	for i := 0; i < parallel; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			c := f.client(t, store)
			<-start
			if _, err := c.Query(context.Background(), "Orders", QueryOptions{Top: 1}); err != nil {
				errCh <- err
			}
		}()
	}
	close(start)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		t.Fatalf("%v", err)
	}

	paths, _, logins := f.requests()
	if logins != 1 {
		t.Errorf("%d concurrent queries cost %d Logins, want 1 — every extra one is a licensed SAP session held for its full TTL", parallel, logins)
	}
	if len(paths) != parallel {
		t.Errorf("GETs = %d, want %d", len(paths), parallel)
	}
}

// TestWithoutAStoreEachClientStillWorks — a one-shot CLI process passes no
// store, and must behave exactly as before: it finds the on-disk session and
// does not log in twice.
func TestWithoutAStoreEachClientStillWorks(t *testing.T) {
	isolateHome(t)
	f := newReadFake(t)

	for i := 0; i < 3; i++ {
		c := f.client(t, nil)
		if _, err := c.Query(context.Background(), "Orders", QueryOptions{Top: 1}); err != nil {
			t.Fatalf("query %d: %v", i, err)
		}
	}
	if _, _, logins := f.requests(); logins != 1 {
		t.Errorf("three sequential clients cost %d Logins, want 1 (the on-disk cache)", logins)
	}
}

// TestSessionStoreNeverCrossesCompanies — sharing is only safe if it cannot
// widen. A session is bound to the CompanyDB it logged into, so replaying one
// against another company would answer a Beverages question with Oil's books.
func TestSessionStoreNeverCrossesCompanies(t *testing.T) {
	isolateHome(t)

	var mu sync.Mutex
	loginsFor := map[string]int{}
	sessionsSeen := map[string]string{} // cookie value -> company it was minted for
	getsFor := map[string]int{}

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPost && strings.HasSuffix(r.URL.Path, "/Login") {
			var body struct{ CompanyDB string }
			_ = json.NewDecoder(r.Body).Decode(&body)
			value := "sess-" + body.CompanyDB
			mu.Lock()
			loginsFor[body.CompanyDB]++
			sessionsSeen[value] = body.CompanyDB
			mu.Unlock()
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: value})
			_, _ = w.Write([]byte(`{"SessionId":"x"}`))
			return
		}
		ck, err := r.Cookie("B1SESSION")
		if err != nil {
			t.Errorf("GET arrived with no session cookie")
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		mu.Lock()
		getsFor[sessionsSeen[ck.Value]]++
		mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{"value": []map[string]any{}})
	}))
	defer srv.Close()

	u, _ := url.Parse(srv.URL)
	port, _ := strconv.Atoi(u.Port())
	store := NewSessionStore()
	companies := []string{"JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB"}

	// Two passes, so the second one proves the store REUSES rather than
	// re-logs-in, without ever handing a company another company's session.
	for pass := 0; pass < 2; pass++ {
		for _, company := range companies {
			cfg := &config.Config{
				Host: u.Hostname(), Port: port, CompanyDB: company,
				User: "tester", Password: "pw", Insecure: true, Timeout: 10,
			}
			c := NewWithSessions(cfg, store)
			if _, err := c.Query(context.Background(), "Orders", QueryOptions{Top: 1}); err != nil {
				t.Fatalf("%s: %v", company, err)
			}
		}
	}

	mu.Lock()
	defer mu.Unlock()
	for _, company := range companies {
		if loginsFor[company] != 1 {
			t.Errorf("%s logged in %d times, want 1", company, loginsFor[company])
		}
		if getsFor[company] != 2 {
			t.Errorf("%s answered %d reads with its own session, want 2 — a session crossed companies", company, getsFor[company])
		}
	}
}

// TestExpiredSharedSessionCostsOneReLogin — when a shared session expires,
// every concurrent caller gets a 401 at the same moment. Only the first may
// re-Login; the rest must adopt its new session rather than each opening one.
func TestExpiredSharedSessionCostsOneReLogin(t *testing.T) {
	const parallel = 20

	isolateHome(t)

	var mu sync.Mutex
	logins := 0
	valid := map[string]bool{}
	gets := 0

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodPost && strings.HasSuffix(r.URL.Path, "/Login") {
			mu.Lock()
			logins++
			value := fmt.Sprintf("sess-%d", logins)
			valid[value] = true
			mu.Unlock()
			time.Sleep(20 * time.Millisecond)
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: value})
			_, _ = w.Write([]byte(`{"SessionId":"x"}`))
			return
		}
		ck, _ := r.Cookie("B1SESSION")
		mu.Lock()
		ok := ck != nil && valid[ck.Value]
		if ok {
			gets++
		}
		mu.Unlock()
		if !ok {
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session."}}}`))
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{"value": []map[string]any{}})
	}))
	defer srv.Close()

	u, _ := url.Parse(srv.URL)
	port, _ := strconv.Atoi(u.Port())
	cfgFor := func() *config.Config {
		return &config.Config{
			Host: u.Hostname(), Port: port, CompanyDB: "JIVO_OIL_HANADB",
			User: "tester", Password: "pw", Insecure: true, Timeout: 10,
		}
	}
	store := NewSessionStore()

	// Warm one session, then expire it.
	if _, err := NewWithSessions(cfgFor(), store).Query(context.Background(), "Orders", QueryOptions{Top: 1}); err != nil {
		t.Fatalf("warm-up: %v", err)
	}
	mu.Lock()
	valid = map[string]bool{}
	mu.Unlock()

	var wg sync.WaitGroup
	start := make(chan struct{})
	errCh := make(chan error, parallel)
	for i := 0; i < parallel; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			c := NewWithSessions(cfgFor(), store)
			<-start
			if _, err := c.Query(context.Background(), "Orders", QueryOptions{Top: 1}); err != nil {
				errCh <- err
			}
		}()
	}
	close(start)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		t.Fatalf("%v", err)
	}

	mu.Lock()
	defer mu.Unlock()
	if logins != 2 {
		t.Errorf("an expired session under %d concurrent calls cost %d Logins, want 2 (warm-up + one refresh)", parallel, logins)
	}
	if gets != 1+parallel {
		t.Errorf("successful GETs = %d, want %d", gets, 1+parallel)
	}
}

// ---------------------------------------------------------------------------
// A count must cost no rows
// ---------------------------------------------------------------------------

// TestCountOnlyAsksForZeroRows pins the request shape of a count.
//
// The defect it closes: a count was expressed as $top=1 (or, in the CLI, as the
// command's ordinary $top with its full $select), so asking "how many business
// partners are there?" hauled complete ~200-field SAP documents across the wire
// to read a number out of a response header. Measured live against production:
// BusinessPartners?$top=1&$inlinecount=allpages returned 14,460 bytes; the same
// request with $top=0 returned 121 bytes and the identical odata.count. The
// Service Layer honours $top=0 on every entity set and company database JIVO
// runs (Orders/Invoices/Items/BusinessPartners/JournalEntries x Oil/Mart/
// Beverages, all HTTP 200 with the correct total and zero rows).
func TestCountOnlyAsksForZeroRows(t *testing.T) {
	f := newReadFake(t)
	c := f.client(t, nil)

	if _, err := c.Query(context.Background(), "BusinessPartners", QueryOptions{
		Filter:    "CardType eq 'cCustomer'",
		CountOnly: true,
	}); err != nil {
		t.Fatalf("count-only query: %v", err)
	}

	paths, queries, _ := f.requests()
	if len(queries) != 1 {
		t.Fatalf("GETs = %d, want exactly 1 — a count is one atomic request", len(queries))
	}
	if got, want := paths[0], "/b1s/v1/BusinessPartners"; got != want {
		t.Errorf("path = %q, want %q", got, want)
	}
	q, err := url.ParseQuery(queries[0])
	if err != nil {
		t.Fatalf("parsing %q: %v", queries[0], err)
	}
	if got := q.Get("$top"); got != "0" {
		t.Errorf("$top = %q, want %q — anything above 0 pulls whole SAP documents to read a header", got, "0")
	}
	if got := q.Get("$inlinecount"); got != "allpages" {
		t.Errorf("$inlinecount = %q, want allpages — without it there is no server-side total at all", got)
	}
	// The filter is the ONLY thing that may ride along: it is what is being
	// counted.
	if got, want := q.Get("$filter"), "CardType eq 'cCustomer'"; got != want {
		t.Errorf("$filter = %q, want %q — the filter defines which rows are counted", got, want)
	}
	for _, dropped := range []string{"$select", "$orderby", "$skip"} {
		if v, present := q[dropped]; present {
			t.Errorf("%s = %v was sent on a count-only request; it has no rows to apply to", dropped, v)
		}
	}
}

// TestCountOnlyRefusesOptionsItCannotHonour — CountOnly returns no rows, so a
// $select/$orderby/$skip/$top/PageSize alongside it cannot be honoured. Quietly
// ignoring them is the same silent-discard defect ValidateEntitySet exists to
// stop, one layer up, so each is a named error and NOTHING reaches SAP.
func TestCountOnlyRefusesOptionsItCannotHonour(t *testing.T) {
	for _, tc := range []struct {
		name string
		opts QueryOptions
	}{
		{"Select", QueryOptions{CountOnly: true, Select: "CardCode"}},
		{"OrderBy", QueryOptions{CountOnly: true, OrderBy: "CardCode"}},
		{"Skip", QueryOptions{CountOnly: true, Skip: 10}},
		{"Top", QueryOptions{CountOnly: true, Top: 5}},
		{"PageSize", QueryOptions{CountOnly: true, PageSize: 50}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			f := newReadFake(t)
			c := f.client(t, nil)

			_, err := c.Query(context.Background(), "BusinessPartners", tc.opts)
			if err == nil {
				t.Fatalf("CountOnly with %s was accepted — the option was going to be dropped in silence", tc.name)
			}
			var useErr *errs.UsageError
			if !errors.As(err, &useErr) {
				t.Errorf("error is %T, want *errs.UsageError so the CLI exits 2: %v", err, err)
			}
			if !strings.Contains(err.Error(), tc.name) {
				t.Errorf("error %q does not name the offending option %q", err, tc.name)
			}
			if _, queries, _ := f.requests(); len(queries) != 0 {
				t.Errorf("a refused combination still reached SAP: %v", queries)
			}
		})
	}

	// And the plain form stays legal.
	f := newReadFake(t)
	if _, err := f.client(t, nil).Query(context.Background(), "Orders", QueryOptions{CountOnly: true}); err != nil {
		t.Errorf("a bare count-only request must stay legal, got: %v", err)
	}
}
