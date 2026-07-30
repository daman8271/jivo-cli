package cli

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
	"strings"
	"testing"
)

// readFake is a read-only stand-in for the Service Layer that records the exact
// query string each GET carried. The defects these tests cover are invisible
// anywhere else: the command "worked", it just asked SAP for a property SAP
// does not have.
type readFake struct {
	srv     *httptest.Server
	queries []url.Values
	paths   []string
}

func newReadFake(t *testing.T) *readFake {
	t.Helper()
	f := &readFake{}
	f.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/Login") {
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake-session"})
			_, _ = w.Write([]byte(`{"SessionId":"fake-session"}`))
			return
		}
		if r.Method != http.MethodGet {
			t.Errorf("read command issued %s %s — these commands are GET-only", r.Method, r.URL.Path)
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		f.paths = append(f.paths, r.URL.Path)
		f.queries = append(f.queries, r.URL.Query())
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{"value": []map[string]any{
			{"DocEntry": 1, "DocNum": 1001, "DocumentStatus": "bost_Open"},
		}})
	}))
	t.Cleanup(f.srv.Close)

	u, err := url.Parse(f.srv.URL)
	if err != nil {
		t.Fatalf("parsing fake server URL: %v", err)
	}
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)
	t.Setenv("SAPB1_HOST", u.Hostname())
	t.Setenv("SAPB1_PORT", u.Port())
	t.Setenv("SAPB1_COMPANYDB", "JIVO_OIL_HANADB")
	t.Setenv("SAPB1_USER", "tester")
	t.Setenv("SAPB1_PASSWORD", "irrelevant")
	t.Setenv("SAPB1_INSECURE", "true")
	t.Setenv("SAPB1_TIMEOUT", "5")
	return f
}

// run executes one sapb1 command line against the fake.
func run(t *testing.T, args ...string) {
	t.Helper()
	root := NewRootCmd()
	root.SetOut(&strings.Builder{})
	root.SetErr(&strings.Builder{})
	root.SetArgs(args)
	if err := root.Execute(); err != nil {
		t.Fatalf("sapb1 %s: %v", strings.Join(args, " "), err)
	}
}

// TestOrdersAndInvoicesNeverNameDocStatus is the regression test for a defect
// that made the CLI's two flagship commands fail outright against real SAP:
//
//	sapb1 orders list --top 2   -> [SAP -1000] Property 'DocStatus' of 'Document' is invalid
//	sapb1 orders list --open    -> [SAP 201]  Property 'DocStatus' is invalid
//
// DocStatus ('O'/'C') is the HANA COLUMN name. The Service Layer property is
// DocumentStatus ('bost_Open'/'bost_Close'), and naming the column fails the
// whole request — so both the default $select and the --open filter were
// broken. CLAUDE.md points the Accounts team straight at these commands.
//
// The assertion is on the wire, because that is where the difference lives.
func TestOrdersAndInvoicesNeverNameDocStatus(t *testing.T) {
	for _, tc := range []struct {
		name string
		args []string
	}{
		{"orders list", []string{"orders", "list", "--top", "2"}},
		{"orders list --open", []string{"orders", "list", "--open", "--top", "2"}},
		{"invoices list", []string{"invoices", "list", "--top", "2"}},
		{"invoices list --open", []string{"invoices", "list", "--open", "--top", "2"}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			f := newReadFake(t)
			run(t, tc.args...)

			if len(f.queries) != 1 {
				t.Fatalf("GETs = %d, want 1", len(f.queries))
			}
			q := f.queries[0]
			for _, param := range []string{"$select", "$filter"} {
				if v := q.Get(param); strings.Contains(v, "DocStatus") {
					t.Errorf("%s = %q names DocStatus — the Service Layer rejects it outright", param, v)
				}
			}
			if sel := q.Get("$select"); !strings.Contains(sel, "DocumentStatus") {
				t.Errorf("$select = %q, want the Service Layer property DocumentStatus", sel)
			}
		})
	}
}

// TestOpenFlagFiltersOnTheServiceLayerProperty pins the --open filter exactly,
// including the value spelling: 'bost_Open', not 'O'.
func TestOpenFlagFiltersOnTheServiceLayerProperty(t *testing.T) {
	for _, tc := range []struct{ entity, cmd string }{
		{"Orders", "orders"},
		{"Invoices", "invoices"},
	} {
		t.Run(tc.cmd, func(t *testing.T) {
			f := newReadFake(t)
			run(t, tc.cmd, "list", "--open", "--top", "5")

			q := f.queries[0]
			if got, want := q.Get("$filter"), "(DocumentStatus eq 'bost_Open')"; got != want {
				t.Errorf("$filter = %q, want %q", got, want)
			}
			if got, want := f.paths[0], "/b1s/v1/"+tc.entity; got != want {
				t.Errorf("path = %q, want %q", got, want)
			}
		})
	}
}

// TestOpenFlagCombinesWithAUserFilter — the built-in filter must stay
// parenthesised so a --filter can never change its precedence.
func TestOpenFlagCombinesWithAUserFilter(t *testing.T) {
	f := newReadFake(t)
	run(t, "orders", "list", "--open", "--filter", "DocTotal gt 100 or DocTotal lt 10", "--top", "5")

	got := f.queries[0].Get("$filter")
	want := "(DocumentStatus eq 'bost_Open') and (DocTotal gt 100 or DocTotal lt 10)"
	if got != want {
		t.Errorf("$filter = %q, want %q", got, want)
	}
}

// TestQueryCommandRejectsAnEntityThatWouldReshapeTheURL — the CLI's generic
// `query` takes the entity straight from the command line, so it inherits the
// same hazard the MCP surface had: "Orders#" would drop --filter/--select/--top
// into a URI fragment and print a full, unfiltered page as if it were the
// answer.
func TestQueryCommandRejectsAnEntityThatWouldReshapeTheURL(t *testing.T) {
	f := newReadFake(t)
	root := NewRootCmd()
	root.SetOut(&strings.Builder{})
	root.SetErr(&strings.Builder{})
	root.SetArgs([]string{"query", "Orders#", "--filter", "DocTotal gt 100", "--top", "3"})
	err := root.Execute()
	if err == nil {
		t.Fatal("sapb1 query 'Orders#' was accepted")
	}
	if !strings.Contains(err.Error(), "entity set") {
		t.Errorf("error should explain the entity set is invalid, got: %v", err)
	}
	if len(f.queries) != 0 {
		t.Errorf("the malformed entity still reached SAP: %v", f.paths)
	}
}

// countFake is readFake with control over odata.count and over how many rows a
// GET comes back with, so the --count request shape can be asserted at the wire.
type countFake struct {
	*readFake
	omitCount bool
	rowsSent  int
}

func newCountFake(t *testing.T, total int) *countFake {
	t.Helper()
	cf := &countFake{readFake: &readFake{}}
	cf.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/Login") {
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake-session"})
			_, _ = w.Write([]byte(`{"SessionId":"fake-session"}`))
			return
		}
		if r.Method != http.MethodGet {
			t.Errorf("count command issued %s %s — it must be GET-only", r.Method, r.URL.Path)
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		cf.paths = append(cf.paths, r.URL.Path)
		cf.queries = append(cf.queries, r.URL.Query())

		// Honour $top the way the live Service Layer does, INCLUDING $top=0.
		n := 20
		if v, ok := r.URL.Query()["$top"]; ok {
			if parsed, err := strconv.Atoi(v[0]); err == nil && parsed < n {
				n = parsed
			}
		}
		cf.rowsSent += n
		rows := make([]map[string]any, 0, n)
		for i := 0; i < n; i++ {
			rows = append(rows, map[string]any{"CardCode": fmt.Sprintf("C%04d", i), "CardName": "a name"})
		}
		body := map[string]any{"value": rows}
		if !cf.omitCount && r.URL.Query().Get("$inlinecount") == "allpages" {
			body["odata.count"] = total
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(body)
	}))
	t.Cleanup(cf.srv.Close)

	u, err := url.Parse(cf.srv.URL)
	if err != nil {
		t.Fatalf("parsing fake server URL: %v", err)
	}
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)
	t.Setenv("SAPB1_HOST", u.Hostname())
	t.Setenv("SAPB1_PORT", u.Port())
	t.Setenv("SAPB1_COMPANYDB", "JIVO_OIL_HANADB")
	t.Setenv("SAPB1_USER", "tester")
	t.Setenv("SAPB1_PASSWORD", "irrelevant")
	t.Setenv("SAPB1_INSECURE", "true")
	t.Setenv("SAPB1_TIMEOUT", "5")
	return cf
}

// runOut executes one command line and returns its stdout.
func runOut(t *testing.T, args ...string) string {
	t.Helper()
	var out strings.Builder
	root := NewRootCmd()
	root.SetOut(&out)
	root.SetErr(&strings.Builder{})
	root.SetArgs(args)
	if err := root.Execute(); err != nil {
		t.Fatalf("sapb1 %s: %v", strings.Join(args, " "), err)
	}
	return out.String()
}

// TestCountIsOneRequestThatFetchesNoRows is the CLI half of the count defect.
//
// `sapb1 query BusinessPartners --count` — the command CLAUDE.md hands the
// Accounts team, and the one used to verify this tool against production — went
// down the ordinary row path: $top=20 plus the command's full $select, twenty
// complete SAP documents dragged across the wire to print a single number. With
// --all it walked up to 200 pages of them for the same number, because the total
// always came from the first page's odata.count regardless.
//
// A count is a question about the SET: one GET, $top=0, no rows.
func TestCountIsOneRequestThatFetchesNoRows(t *testing.T) {
	for _, tc := range []struct {
		name string
		args []string
	}{
		{"query", []string{"query", "BusinessPartners", "--count"}},
		{"partners list", []string{"partners", "list", "--count"}},
		{"orders list", []string{"orders", "list", "--count"}},
		{"invoices list", []string{"invoices", "list", "--count"}},
		{"items list", []string{"items", "list", "--count"}},
		// --all must not turn a count into a 200-page sweep for the same number.
		{"query --count --all", []string{"query", "BusinessPartners", "--count", "--all"}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			f := newCountFake(t, 3391)
			got := strings.TrimSpace(runOut(t, tc.args...))

			if got != "3391" {
				t.Errorf("printed %q, want the server-side total 3391", got)
			}
			if len(f.queries) != 1 {
				t.Fatalf("count cost %d GETs, want exactly 1: %v", len(f.queries), f.queries)
			}
			q := f.queries[0]
			if top := q.Get("$top"); top != "0" {
				t.Errorf("$top = %q, want %q — anything higher hauls whole SAP documents to print one number", top, "0")
			}
			if q.Get("$inlinecount") != "allpages" {
				t.Errorf("$inlinecount = %q, want allpages", q.Get("$inlinecount"))
			}
			if sel := q.Get("$select"); sel != "" {
				t.Errorf("$select = %q rode along on a count — there are no rows to project", sel)
			}
			if f.rowsSent != 0 {
				t.Errorf("the server sent %d rows for a count, want 0", f.rowsSent)
			}
		})
	}
}

// TestCountStillCarriesTheFilterItIsCounting — the one option a count MUST keep
// is the filter, because it is what defines the set being counted. Dropping it
// would turn "how many open orders?" into "how many orders?" and answer with a
// perfectly formatted wrong number.
func TestCountStillCarriesTheFilterItIsCounting(t *testing.T) {
	f := newCountFake(t, 7)
	runOut(t, "orders", "list", "--count", "--open", "--filter", "DocTotal gt 100")

	got := f.queries[0].Get("$filter")
	want := "(DocumentStatus eq 'bost_Open') and (DocTotal gt 100)"
	if got != want {
		t.Errorf("$filter = %q, want %q", got, want)
	}
}

// TestCountRefusesWhenTheServerWithholdsTheTotal — the old code fell back to
// printing len(rows) with a note. Under $top=0 that fallback prints "0", which
// reads as "this entity set is empty" for a set of any size. Refusing is the
// only honest answer, and it must be an APIError so the process exits 6 rather
// than looking like success.
func TestCountRefusesWhenTheServerWithholdsTheTotal(t *testing.T) {
	f := newCountFake(t, 3391)
	f.omitCount = true

	var out strings.Builder
	root := NewRootCmd()
	root.SetOut(&out)
	root.SetErr(&strings.Builder{})
	root.SetArgs([]string{"query", "BusinessPartners", "--count"})
	err := root.Execute()

	if err == nil {
		t.Fatalf("--count printed %q instead of refusing, with no odata.count from the server", out.String())
	}
	if strings.ContainsAny(out.String(), "0123456789") {
		t.Errorf("a number was printed despite the server giving no total: %q", out.String())
	}
	if !strings.Contains(err.Error(), "odata.count") {
		t.Errorf("the refusal should name what was missing, got: %v", err)
	}
	if code := ExitCodeFor(err); code != ExitAPI {
		t.Errorf("exit code = %d, want %d (ExitAPI) so a script cannot mistake it for success", code, ExitAPI)
	}
}
