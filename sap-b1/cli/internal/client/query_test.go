package client

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
	"strings"
	"testing"
	"time"

	"sapb1/internal/config"
)

// TestExtractODataCount covers both encodings the Service Layer uses for
// odata.count (a quoted string per OData v3, or a bare number) plus the
// absent/garbage cases.
func TestExtractODataCount(t *testing.T) {
	cases := []struct {
		name   string
		body   string
		wantN  int64
		wantOK bool
	}{
		{"quoted string", `{"odata.count":"42","value":[]}`, 42, true},
		{"bare number", `{"odata.count":7,"value":[]}`, 7, true},
		{"absent", `{"value":[{"DocEntry":1}]}`, 0, false},
		{"garbage", `not json`, 0, false},
		{"non-numeric", `{"odata.count":"lots"}`, 0, false},
	}
	for _, tc := range cases {
		n, ok := extractODataCount([]byte(tc.body))
		if ok != tc.wantOK || n != tc.wantN {
			t.Errorf("%s: extractODataCount = (%d,%v), want (%d,%v)", tc.name, n, ok, tc.wantN, tc.wantOK)
		}
	}
}

// TestParseQueryResultCount verifies a mock inlinecount response threads the
// server-side total through onto the QueryResult.
func TestParseQueryResultCount(t *testing.T) {
	body := []byte(`{"odata.count":"1234","value":[{"DocEntry":1},{"DocEntry":2}]}`)
	qr, err := parseQueryResult(body, "Orders")
	if err != nil {
		t.Fatalf("parseQueryResult: %v", err)
	}
	if !qr.CountKnown {
		t.Fatal("expected CountKnown=true when odata.count is present")
	}
	if qr.Count != 1234 {
		t.Errorf("Count = %d, want 1234", qr.Count)
	}
	if len(qr.Value) != 2 {
		t.Errorf("rows = %d, want 2", len(qr.Value))
	}
}

func TestParseQueryResultNoCount(t *testing.T) {
	body := []byte(`{"value":[{"DocEntry":1}]}`)
	qr, err := parseQueryResult(body, "Orders")
	if err != nil {
		t.Fatalf("parseQueryResult: %v", err)
	}
	if qr.CountKnown {
		t.Error("expected CountKnown=false when odata.count absent")
	}
}

// TestInlineCountQueryString confirms --count maps onto $inlinecount=allpages.
func TestInlineCountQueryString(t *testing.T) {
	qs := QueryOptions{InlineCount: true}.queryString()
	if qs != "%24inlinecount=allpages" && qs != "$inlinecount=allpages" {
		t.Errorf("queryString = %q, want it to set $inlinecount=allpages", qs)
	}
}

// fakeSL is a stand-in Service Layer over httptest: it accepts POST /Login,
// serves paged OData responses for one entity set, and records what it was
// asked for. It never touches a real SAP box.
type fakeSL struct {
	t *testing.T
	// total rows the entity set contains
	total int
	// pageSize the server chooses to return (may ignore Prefer)
	pageSize int
	// honourPrefer makes the server respect Prefer: odata.maxpagesize
	honourPrefer bool
	// omitDate strips the HTTP Date header
	omitDate bool
	// inlineCount total to report, when $inlinecount=allpages is asked for
	reportCount bool

	srv      *httptest.Server
	Requests []*http.Request
	Prefers  []string
}

func newFakeSL(t *testing.T, f *fakeSL) *fakeSL {
	t.Helper()
	f.t = t
	if f.pageSize <= 0 {
		f.pageSize = 20
	}
	f.srv = httptest.NewTLSServer(http.HandlerFunc(f.handle))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeSL) handle(w http.ResponseWriter, r *http.Request) {
	f.Requests = append(f.Requests, r)
	if f.omitDate {
		// Go's http server always sets Date unless told otherwise.
		w.Header()["Date"] = nil
	}
	if r.Method == http.MethodPost && strings.HasSuffix(r.URL.Path, "/Login") {
		http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake-session"})
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"SessionId":"fake-session"}`)
		return
	}

	q := r.URL.Query()
	f.Prefers = append(f.Prefers, r.Header.Get("Prefer"))

	skip := 0
	if v := q.Get("$skip"); v != "" {
		skip, _ = strconv.Atoi(v)
	}
	top := 0
	if v := q.Get("$top"); v != "" {
		top, _ = strconv.Atoi(v)
	}

	page := f.pageSize
	if f.honourPrefer {
		if p := r.Header.Get("Prefer"); strings.HasPrefix(p, "odata.maxpagesize=") {
			if n, err := strconv.Atoi(strings.TrimPrefix(p, "odata.maxpagesize=")); err == nil && n > 0 {
				page = n
			}
		}
	}

	// Rows this request may still draw: everything from $skip to the end of
	// the set, capped by $top. Note the fake deliberately re-applies $top to
	// each request's own $skip — a sloppier reading than the Service Layer's,
	// which keeps the original window. That is the pessimistic case, and it is
	// exactly what proves QueryAll's client-side stop is what bounds the walk.
	remaining := f.total - skip
	if remaining < 0 {
		remaining = 0
	}
	if top > 0 && top < remaining {
		remaining = top
	}
	n := remaining
	if n > page {
		n = page
	}

	rows := make([]map[string]any, 0, n)
	for i := 0; i < n; i++ {
		rows = append(rows, map[string]any{"DocEntry": skip + i + 1})
	}

	body := map[string]any{"value": rows}
	if f.reportCount && q.Get("$inlinecount") == "allpages" {
		body["odata.count"] = strconv.Itoa(f.total)
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

func (f *fakeSL) client() *Client {
	f.t.Helper()
	u, err := url.Parse(f.srv.URL)
	if err != nil {
		f.t.Fatal(err)
	}
	port, err := strconv.Atoi(u.Port())
	if err != nil {
		f.t.Fatal(err)
	}
	return New(&config.Config{
		Host: u.Hostname(), Port: port,
		CompanyDB: "FAKEDB", User: "tester", Password: "pw",
		Insecure: true, Timeout: 10,
	})
}

// isolateHome points the session cache at a throwaway HOME so tests never read
// or write the developer's real ~/.sapb1-session-*.json.
func isolateHome(t *testing.T) {
	t.Helper()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
}

// TestQueryCapturesServerDate — the as-of stamp comes from the SAP server's
// own clock (HTTP Date), not ours.
func TestQueryCapturesServerDate(t *testing.T) {
	isolateHome(t)
	f := newFakeSL(t, &fakeSL{total: 3})
	res, err := f.client().Query(context.Background(), "Orders", QueryOptions{Top: 3})
	if err != nil {
		t.Fatalf("Query: %v", err)
	}
	if !res.ServerDateKnown {
		t.Fatal("ServerDateKnown = false, want the HTTP Date header to be captured")
	}
	if time.Since(res.ServerDate) > time.Minute || time.Since(res.ServerDate) < -time.Minute {
		t.Errorf("ServerDate %v is not close to now — header parsed wrong?", res.ServerDate)
	}
}

// TestQueryWithoutDateHeader — a server that sends no Date must leave
// ServerDateKnown false rather than silently substituting local time.
func TestQueryWithoutDateHeader(t *testing.T) {
	isolateHome(t)
	f := newFakeSL(t, &fakeSL{total: 3, omitDate: true})
	res, err := f.client().Query(context.Background(), "Orders", QueryOptions{Top: 3})
	if err != nil {
		t.Fatalf("Query: %v", err)
	}
	if res.ServerDateKnown {
		t.Error("ServerDateKnown = true although the server sent no Date header")
	}
	if !res.ServerDate.IsZero() {
		t.Errorf("ServerDate = %v, want the zero time when unknown", res.ServerDate)
	}
}

// TestQueryAllFollowsNextLink — the baseline pagination behaviour, unchanged.
func TestQueryAllFollowsNextLink(t *testing.T) {
	isolateHome(t)
	f := newFakeSL(t, &fakeSL{total: 45, pageSize: 20})
	res, err := f.client().QueryAll(context.Background(), "Orders", QueryOptions{})
	if err != nil {
		t.Fatalf("QueryAll: %v", err)
	}
	if len(res.Value) != 45 {
		t.Fatalf("rows = %d, want 45 (nextLink not followed to exhaustion)", len(res.Value))
	}
	if res.Capped {
		t.Error("Capped = true on a 3-page walk")
	}
	if !res.ServerDateKnown {
		t.Error("QueryAll lost the server Date stamp")
	}
}

// TestQueryAllStopsAtTop — a bounded request must stay bounded, and must trim
// to exactly Top, no matter how many rows the server would keep offering.
func TestQueryAllStopsAtTop(t *testing.T) {
	isolateHome(t)
	cases := []struct {
		name      string
		total     int
		top       int
		wantRows  int
		wantPages int // GETs, excluding the one Login
	}{
		{"top smaller than one page", 500, 5, 5, 1},
		{"top spans exactly two pages", 500, 40, 40, 2},
		{"top spans three pages", 500, 45, 45, 3},
		{"top larger than the set", 12, 45, 12, 1},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSL(t, &fakeSL{total: tc.total, pageSize: 20})
			res, err := f.client().QueryAll(context.Background(), "Orders", QueryOptions{Top: tc.top})
			if err != nil {
				t.Fatalf("QueryAll: %v", err)
			}
			if len(res.Value) != tc.wantRows {
				t.Errorf("rows = %d, want %d", len(res.Value), tc.wantRows)
			}
			gets := 0
			for _, r := range f.Requests {
				if r.Method == http.MethodGet {
					gets++
				}
			}
			if gets != tc.wantPages {
				t.Errorf("GET pages = %d, want %d (a bounded top must not walk the whole set)", gets, tc.wantPages)
			}
		})
	}
}

// TestQueryAllKeepsInlineCountAndPageSize — the server-side total is taken
// from the first page, and the requested page size travels as a Prefer header.
func TestQueryAllKeepsInlineCountAndPageSize(t *testing.T) {
	isolateHome(t)
	f := newFakeSL(t, &fakeSL{total: 250, pageSize: 20, honourPrefer: true, reportCount: true})
	res, err := f.client().QueryAll(context.Background(), "Orders", QueryOptions{
		InlineCount: true, PageSize: 100, Top: 150,
	})
	if err != nil {
		t.Fatalf("QueryAll: %v", err)
	}
	if !res.CountKnown || res.Count != 250 {
		t.Errorf("Count = %d (known=%v), want 250/true", res.Count, res.CountKnown)
	}
	if len(res.Value) != 150 {
		t.Errorf("rows = %d, want 150", len(res.Value))
	}
	if len(f.Prefers) == 0 || f.Prefers[0] != "odata.maxpagesize=100" {
		t.Errorf("Prefer headers = %v, want the first to be odata.maxpagesize=100", f.Prefers)
	}
}
