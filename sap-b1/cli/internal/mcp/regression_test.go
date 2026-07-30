package mcp

import (
	"fmt"
	"net/http"
	"strings"
	"sync"
	"testing"
	"time"

	"sapb1/internal/client"
)

// Regression tests for defects found by review AGAINST LIVE SAP after the
// first round of fixes landed. Each test here fails on the code as it stood
// before the fix beside it.

// ---------------------------------------------------------------------------
// The entity name must not be able to reshape the request URL
// ---------------------------------------------------------------------------

// TestEntityCannotSmuggleUrlStructure is the regression test for the worst of
// the second round: the entity was concatenated raw in front of "?" + the query
// string, so a single '#' in it turned $filter, $select, $orderby, $top and
// $inlinecount into a URI fragment that net/http never sends. Proven live
// against production Mart: {entity:"BusinessPartners#", filter:"CardType eq
// 'cCustomer'", select:"CardCode,CardType", top:3} came back isError=false with
// three FULL ~200-field records, the first of them a logistics vendor — the
// filter and the projection both silently gone.
//
// The two halves both matter: the call must FAIL (a) rather than succeed with
// unfiltered rows, and (b) rather than be quietly "cleaned up" into a different
// question than the one asked. And nothing may reach SAP.
func TestEntityCannotSmuggleUrlStructure(t *testing.T) {
	cases := []struct {
		name   string
		entity string
	}{
		{"fragment truncates the whole query string", "BusinessPartners#"},
		{"fragment in the middle", "Business#Partners"},
		{"question mark starts a query string", "Orders?$top=1"},
		{"ampersand splices a parameter", "Orders&$select=DocEntry"},
		{"percent can re-encode any of the above", "Orders%23"},
		{"a space is never part of an entity-set name", "Business Partners"},
		{"a tab likewise", "Orders\tlist"},
		{"a newline likewise", "Orders\nOrders"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 500})
			isErr, text := callTool(t, f.server(), "sapb1_query", map[string]any{
				"entity": tc.entity,
				"filter": "CardType eq 'cCustomer'",
				"select": "CardCode,CardType",
				"top":    3.0,
			})
			if !isErr {
				t.Fatalf("entity %q was ACCEPTED and answered: %s", tc.entity, text)
			}
			if !strings.Contains(text, "entity set") {
				t.Errorf("rejection should name the problem, got: %s", text)
			}
			if len(f.seen()) != 0 {
				t.Errorf("a malformed entity reached SAP anyway: %v", f.seen())
			}
		})
	}
}

// TestValidEntityStillCarriesEveryQueryOption is the positive control for the
// test above: with a clean entity, the filter, the projection, the ordering and
// the bound must all actually be on the wire. A guard that rejected the bad
// case by breaking the good one would be worse than the bug.
func TestValidEntityStillCarriesEveryQueryOption(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 500, honourPrefer: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{
		"entity":  "BusinessPartners",
		"filter":  "CardType eq 'cCustomer'",
		"select":  "CardCode,CardType",
		"orderby": "CardCode",
		"top":     3.0,
	})
	if got.RowsInPage != 3 {
		t.Errorf("rows_in_page = %d, want 3", got.RowsInPage)
	}
	gets := f.gets()
	if len(gets) == 0 {
		t.Fatal("no GET reached the fake")
	}
	q := gets[0].Query
	for param, want := range map[string]string{
		// Parenthesised by combineFilters, so a caller filter can never change
		// the precedence of a built-in one.
		"$filter":  "(CardType eq 'cCustomer')",
		"$select":  "CardCode,CardType",
		"$orderby": "CardCode",
		"$top":     "4", // top + 1, the truncation probe
	} {
		if got := q.Get(param); got != want {
			t.Errorf("%s = %q, want %q — a query option did not reach SAP", param, got, want)
		}
	}
	if gets[0].Path != "/b1s/v1/BusinessPartners" {
		t.Errorf("request path = %q, want /b1s/v1/BusinessPartners", gets[0].Path)
	}
}

// TestFieldsToolRejectsAStructuralEntity — sapb1_fields runs its own live GET,
// so it needs the same guard. Without it, `fields` on "Orders#" would report
// the fields of an unbounded read.
func TestFieldsToolRejectsAStructuralEntity(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 5})
	isErr, text := callTool(t, f.server(), "sapb1_fields", map[string]any{"entity": "Orders#"})
	if !isErr {
		t.Fatalf("sapb1_fields accepted a structural entity: %s", text)
	}
	if len(f.seen()) != 0 {
		t.Errorf("sapb1_fields reached SAP with a malformed entity: %v", f.seen())
	}
}

// ---------------------------------------------------------------------------
// Concurrency: one Login per company, not one per call
// ---------------------------------------------------------------------------

// TestConcurrentToolCallsShareOneLogin is the regression test for the login
// storm the HTTP transport introduced. Measured before the fix: 30 serial calls
// cost 1 Login, 30 CONCURRENT calls cost 29 — every parallel goroutine missed
// the on-disk cache before any of them had written it, and each opened its own
// SAP session. Those sessions each hold a licensed Service Layer slot for their
// full TTL, and the MCP path never logs out.
//
// Agents batch tool calls, and HTTP is the transport published through the
// gateway, so this is the normal case rather than an edge one.
func TestConcurrentToolCallsShareOneLogin(t *testing.T) {
	const parallel = 30

	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 50, loginDelay: 20 * time.Millisecond})
	s := f.server()

	var wg sync.WaitGroup
	start := make(chan struct{})
	errCh := make(chan error, parallel)
	for i := 0; i < parallel; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-start
			isErr, text, err := invokeTool(s, "sapb1_query", map[string]any{"entity": "Orders", "top": 5.0})
			switch {
			case err != nil:
				errCh <- err
			case isErr:
				errCh <- fmt.Errorf("call %d returned a tool error: %s", i, text)
			}
		}(i)
	}
	close(start)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		t.Fatalf("%v", err)
	}

	if logins := f.logins(); len(logins) != 1 {
		t.Errorf("%d concurrent tool calls cost %d Logins, want exactly 1 — each extra Login holds a licensed SAP session slot for its full TTL: %v",
			parallel, len(logins), logins)
	}
	if n := len(f.gets()); n != parallel {
		t.Errorf("GETs = %d, want %d (one per call)", n, parallel)
	}
	// And every read must still have used the right company's session.
	for _, g := range f.gets() {
		if g.Session != "sess-JIVO_OIL_HANADB" {
			t.Errorf("GET carried session %q — session sharing must never cross companies", g.Session)
		}
	}
}

// TestConcurrentCallsAcrossCompaniesLoginOncePerCompany — sharing must be keyed
// by identity, so three companies hit in parallel cost exactly three Logins and
// no read is ever answered by another company's session. Sharing sessions is
// only safe if it can never widen into sharing the WRONG session.
func TestConcurrentCallsAcrossCompaniesLoginOncePerCompany(t *testing.T) {
	companies := []string{"JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB"}
	const perCompany = 10

	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 50, loginDelay: 20 * time.Millisecond})
	s := f.server()

	var wg sync.WaitGroup
	start := make(chan struct{})
	errCh := make(chan error, len(companies)*perCompany)
	for _, company := range companies {
		for i := 0; i < perCompany; i++ {
			wg.Add(1)
			go func(company string) {
				defer wg.Done()
				<-start
				isErr, text, err := invokeTool(s, "sapb1_query", map[string]any{
					"entity": "Orders", "top": 5.0, "company": company,
				})
				switch {
				case err != nil:
					errCh <- err
				case isErr:
					errCh <- fmt.Errorf("%s: %s", company, text)
				}
			}(company)
		}
	}
	close(start)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		t.Fatalf("%v", err)
	}

	logins := f.logins()
	if len(logins) != len(companies) {
		t.Errorf("%d concurrent calls across %d companies cost %d Logins, want %d: %v",
			len(companies)*perCompany, len(companies), len(logins), len(companies), logins)
	}
	seen := map[string]bool{}
	for _, c := range logins {
		if seen[c] {
			t.Errorf("company %s was logged into twice: %v", c, logins)
		}
		seen[c] = true
	}
	// Every GET must carry a session minted for a real company — and each
	// company's own.
	for _, g := range f.gets() {
		if !strings.HasPrefix(g.Session, "sess-JIVO_") {
			t.Errorf("GET carried an unexpected session %q", g.Session)
		}
	}
}

// TestEverySapTouchingToolSharesSessions proves the sharing reaches EVERY tool
// that reads SAP, not just sapb1_query — each used to build its own
// client.New, so each was its own chance to open a session per call.
//
// sapb1_doctor is deliberately excluded: performing a real Login against the
// requested company IS its job, and a doctor that reported on a session
// somebody else opened would prove nothing. TestDoctorAlwaysPerformsItsOwnLogin
// pins that on purpose.
func TestEverySapTouchingToolSharesSessions(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 5, loginDelay: 20 * time.Millisecond})
	s := f.server()

	calls := []struct {
		tool string
		args map[string]any
	}{
		{"sapb1_fields", map[string]any{"entity": "Orders"}},
		{"sapb1_query", map[string]any{"entity": "Orders", "top": 2.0}},
		{"sapb1_orders", map[string]any{"top": 2.0}},
		{"sapb1_invoices", map[string]any{"count": true}},
		{"sapb1_items", map[string]any{"top": 2.0}},
		{"sapb1_partners", map[string]any{"top": 2.0}},
	}

	var wg sync.WaitGroup
	start := make(chan struct{})
	errCh := make(chan error, len(calls)*3)
	for round := 0; round < 3; round++ {
		for _, c := range calls {
			wg.Add(1)
			go func(tool string, args map[string]any) {
				defer wg.Done()
				<-start
				isErr, text, err := invokeTool(s, tool, args)
				switch {
				case err != nil:
					errCh <- err
				case isErr:
					errCh <- fmt.Errorf("%s: %s", tool, text)
				}
			}(c.tool, c.args)
		}
	}
	close(start)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		t.Fatalf("%v", err)
	}

	if logins := f.logins(); len(logins) != 1 {
		t.Errorf("%d concurrent calls across every SAP-touching tool cost %d Logins, want 1: %v", len(calls)*3, len(logins), logins)
	}
}

// TestDoctorAlwaysPerformsItsOwnLogin — the one tool that must NOT reuse a
// session. Doctor exists to answer "can we log in to this company right now?",
// and reporting on a session another call opened earlier would answer a
// different question.
func TestDoctorAlwaysPerformsItsOwnLogin(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 5})
	s := f.server()

	for i := 0; i < 3; i++ {
		if isErr, text := callTool(t, s, "sapb1_doctor", map[string]any{}); isErr {
			t.Fatalf("doctor: %s", text)
		}
	}
	if logins := f.logins(); len(logins) != 3 {
		t.Errorf("doctor ran 3 times and logged in %d times, want 3 — a doctor that trusts a cached session proves nothing: %v", len(logins), logins)
	}
}

// TestExpiredSessionCostsOneReLoginNotOnePerCall — the 401 path is the other
// place a storm can start: when a shared session expires, every in-flight call
// gets a 401 at once. Only the first may re-Login; the rest must adopt its
// session.
func TestExpiredSessionCostsOneReLoginNotOnePerCall(t *testing.T) {
	const parallel = 20

	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 20, loginDelay: 20 * time.Millisecond})
	s := f.server()

	// Warm a session, then make it expire for every subsequent GET exactly once.
	if isErr, text := callTool(t, s, "sapb1_query", map[string]any{"entity": "Orders", "top": 1.0}); isErr {
		t.Fatalf("warm-up call failed: %s", text)
	}
	f.expireAllSessions()

	var wg sync.WaitGroup
	start := make(chan struct{})
	errCh := make(chan error, parallel)
	for i := 0; i < parallel; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			isErr, text, err := invokeTool(s, "sapb1_query", map[string]any{"entity": "Orders", "top": 1.0})
			switch {
			case err != nil:
				errCh <- err
			case isErr:
				errCh <- fmt.Errorf("%s", text)
			}
		}()
	}
	close(start)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		t.Fatalf("%v", err)
	}

	// One warm-up Login plus exactly one re-Login for the whole expiry event.
	if logins := f.logins(); len(logins) != 2 {
		t.Errorf("an expired session under %d concurrent calls cost %d Logins, want 2 (warm-up + one refresh): %v",
			parallel, len(logins), logins)
	}
}

// ---------------------------------------------------------------------------
// Truncation must never become a fixed point
// ---------------------------------------------------------------------------

// TestSweepDoesNotLivelockWhenTheServerTotalExceedsTheRows reproduces the
// livelock: the server serves 30 rows and reports odata.count = 500 (which
// happens for real when rows are deleted mid-sweep, when row-level
// authorisation filters the result, or over a view — $inlinecount is computed
// on the first page and is skip-agnostic, so it is not a promise about what is
// left). Truncation used to be inferred from count > skip+rows, so round 0
// returned 30 rows with next_skip 30, and round 1 returned ZERO rows still
// marked truncated with next_skip 30 — a fixed point. An agent following the
// documented resume protocol loops on it forever, each round a fresh Login.
//
// The test drives the documented protocol itself rather than asserting on one
// response, because "it terminates" is the property that actually matters.
func TestSweepDoesNotLivelockWhenTheServerTotalExceedsTheRows(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 30, pageSize: 100, honourPrefer: true, reportedCount: 500})
	s := f.server()

	const maxRounds = 5
	skip := 0.0
	rounds := 0
	seenSkips := map[float64]bool{}
	for {
		rounds++
		if rounds > maxRounds {
			t.Fatalf("the documented resume protocol did not terminate in %d rounds — truncated is a fixed point", maxRounds)
		}
		args := map[string]any{"entity": "BusinessPartners", "all": true}
		if skip > 0 {
			args["skip"] = skip
		}
		got, _ := callRows(t, s, "sapb1_query", args)

		if got.Truncated && got.RowsInPage == 0 {
			t.Fatalf("truncated=true with rows_in_page=0 — next_skip cannot advance, so the agent repeats this exact call forever")
		}
		if !got.Truncated {
			break
		}
		if got.NextSkip == nil {
			t.Fatal("truncated response carries no next_skip")
		}
		next := float64(*got.NextSkip)
		if seenSkips[next] {
			t.Fatalf("next_skip %v was already visited — the resume protocol is cycling", next)
		}
		seenSkips[next] = true
		skip = next
	}

	if rounds != 1 {
		t.Errorf("a complete sweep took %d rounds, want 1 — a stale odata.count must not be read as \"there is more\"", rounds)
	}
}

// TestCompleteSweepIsNotReportedTruncated is the single-response form of the
// same defect: 30 of a claimed 500 rows, fetched to exhaustion, is complete.
// total_count still carries the server's own number so the disagreement is
// visible rather than papered over.
func TestCompleteSweepIsNotReportedTruncated(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 30, pageSize: 100, honourPrefer: true, reportedCount: 500})
	got, raw := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders", "all": true})

	if got.Truncated {
		t.Errorf("truncated = true although odata.nextLink ran out and neither cap fired")
	}
	if _, present := raw["next_skip"]; present {
		t.Errorf("a complete sweep advertises next_skip = %v", raw["next_skip"])
	}
	if got.TotalCount == nil || *got.TotalCount != 500 {
		t.Errorf("total_count = %v, want the server's own 500 — the caller must be able to see the disagreement", got.TotalCount)
	}
	if got.RowsInPage != 30 {
		t.Errorf("rows_in_page = %d, want 30", got.RowsInPage)
	}
}

// TestTruncatedNeverAccompaniesAnEmptyPage pins the invariant itself across
// every row-returning tool and both row modes: whatever the server says, a
// response with no rows can never claim to be truncated, because next_skip
// would repeat the call that just came back empty.
func TestTruncatedNeverAccompaniesAnEmptyPage(t *testing.T) {
	for _, tool := range []string{"sapb1_query", "sapb1_orders", "sapb1_invoices", "sapb1_items", "sapb1_partners"} {
		for _, mode := range []map[string]any{{"all": true}, {"top": 20.0}} {
			name := tool + "/top"
			if mode["all"] == true {
				name = tool + "/all"
			}
			t.Run(name, func(t *testing.T) {
				isolateHome(t)
				// Past the end of the set: no rows come back, but the server's
				// skip-agnostic total still says 500.
				f := newFakeSAP(t, &fakeSAP{total: 30, pageSize: 100, honourPrefer: true, reportedCount: 500})
				args := map[string]any{"skip": 30.0}
				for k, v := range mode {
					args[k] = v
				}
				if tool == "sapb1_query" {
					args["entity"] = "Orders"
				}
				got, raw := callRows(t, f.server(), tool, args)
				if got.RowsInPage != 0 {
					t.Fatalf("expected an empty page, got %d rows", got.RowsInPage)
				}
				if got.Truncated {
					t.Errorf("truncated = true on an empty page — the agent would resume at the same skip forever")
				}
				if _, present := raw["next_skip"]; present {
					t.Errorf("next_skip present on an empty page: %v", raw["next_skip"])
				}
			})
		}
	}
}

// ---------------------------------------------------------------------------
// lowStock: 0
// ---------------------------------------------------------------------------

// TestLowStockZeroIsHonoured — the schema advertises Min 0 and 0 is the most
// useful value there is ("what is out of stock?"). The handler tested `> 0`, so
// lowStock:0 produced NO filter and returned EVERY item, formatted exactly like
// a correct answer. Wire capture is the assertion: what matters is the $filter
// SAP received.
func TestLowStockZeroIsHonoured(t *testing.T) {
	cases := []struct {
		name       string
		args       map[string]any
		wantFilter string
	}{
		{"lowStock 0 means out of stock", map[string]any{"lowStock": 0.0}, "(QuantityOnStock le 0)"},
		{"lowStock 1", map[string]any{"lowStock": 1.0}, "(QuantityOnStock le 1)"},
		{"lowStock 10", map[string]any{"lowStock": 10.0}, "(QuantityOnStock le 10)"},
		{"omitted means no stock filter", map[string]any{}, ""},
		{"lowStock 0 ANDs with a caller filter", map[string]any{
			"lowStock": 0.0, "filter": "InventoryItem eq 'tYES'",
		}, "(QuantityOnStock le 0) and (InventoryItem eq 'tYES')"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 5})
			args := map[string]any{"top": 5.0}
			for k, v := range tc.args {
				args[k] = v
			}
			callRows(t, f.server(), "sapb1_items", args)

			gets := f.gets()
			if len(gets) == 0 {
				t.Fatal("no GET reached the fake")
			}
			if got := gets[0].Query.Get("$filter"); got != tc.wantFilter {
				t.Errorf("$filter = %q, want %q", got, tc.wantFilter)
			}
		})
	}
}

// ---------------------------------------------------------------------------
// total_count in the default (top) mode
// ---------------------------------------------------------------------------

// TestTopModeReturnsTheServerTotal — top is the mode agents use by default, and
// it never asked for $inlinecount. So the default answer said "truncated: true"
// with no sense of scale: 20 rows out of 46 and 20 out of 46,000 were
// indistinguishable, and MCP.md documented a response shape no call could
// produce.
func TestTopModeReturnsTheServerTotal(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 2184, pageSize: 100, honourPrefer: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{
		"entity": "BusinessPartners", "top": 3.0,
	})

	if got.RowsInPage != 3 {
		t.Errorf("rows_in_page = %d, want 3", got.RowsInPage)
	}
	if !got.Truncated {
		t.Error("truncated = false with 2184 rows behind a top of 3")
	}
	if got.TotalCount == nil || *got.TotalCount != 2184 {
		t.Fatalf("total_count = %v, want 2184 — the default mode must say how much it is not showing", got.TotalCount)
	}
	if q := f.gets()[0].Query.Get("$inlinecount"); q != "allpages" {
		t.Errorf("$inlinecount = %q, want allpages (it is free on a request we were making anyway)", q)
	}
}

// TestTopModeOmitsTotalCountWhenTheServerGivesNone — asking is not the same as
// getting. A server that ignores $inlinecount must produce a response with NO
// total_count, never a guessed one.
func TestTopModeOmitsTotalCountWhenTheServerGivesNone(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 100, countAs: "omit"})
	got, raw := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders", "top": 5.0})
	if _, present := raw["total_count"]; present {
		t.Errorf("total_count present although the server sent no odata.count: %v", raw["total_count"])
	}
	if got.RowsInPage != 5 || !got.Truncated {
		t.Errorf("rows_in_page = %d truncated = %v, want 5/true", got.RowsInPage, got.Truncated)
	}
}

// TestTopModeFetchesExactlyOnePage — top=20 used to cost two round trips and
// pull 40 rows to return 20, because the paging preference was left at the
// Service Layer's default of 20 while the request asked for top+1.
func TestTopModeFetchesExactlyOnePage(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 1000, pageSize: 20, honourPrefer: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders"})

	if got.RowsInPage != defaultTop {
		t.Errorf("rows_in_page = %d, want %d", got.RowsInPage, defaultTop)
	}
	if n := len(f.gets()); n != 1 {
		t.Errorf("a default top cost %d GETs, want 1", n)
	}
	if p := f.gets()[0].Prefer; p != fmt.Sprintf("odata.maxpagesize=%d", defaultTop+1) {
		t.Errorf("Prefer = %q, want odata.maxpagesize=%d (the size of the answer, not the server default)", p, defaultTop+1)
	}
	// An explicit page_size is still the caller's to choose.
	isolateHome(t)
	f2 := newFakeSAP(t, &fakeSAP{total: 1000, pageSize: 20, honourPrefer: true})
	callRows(t, f2.server(), "sapb1_query", map[string]any{"entity": "Orders", "top": 50.0, "page_size": 25.0})
	if p := f2.gets()[0].Prefer; p != "odata.maxpagesize=25" {
		t.Errorf("Prefer = %q, want the caller's odata.maxpagesize=25", p)
	}
}

// TestCountModeHaulsNoRowsAtAll supersedes the earlier
// TestCountModeSendsTheToolsDefaultSelect, which pinned a HALF fix: a count was
// $top=1 plus the tool's own default $select, so the four convenience tools got
// a slim row while sapb1_query — the core tool, with no default field set and no
// way to invent one for an arbitrary entity — still pulled a complete ~200-field
// SAP document to read a number out of a header. Measured live on production
// BusinessPartners: 14,460 bytes at $top=1 versus 121 bytes at $top=0, same
// odata.count.
//
// So the property is now the stronger one, and it holds for EVERY row-returning
// tool including the generic one: a count asks for zero rows and receives zero
// rows.
func TestCountModeHaulsNoRowsAtAll(t *testing.T) {
	for _, tc := range []struct {
		tool string
		args map[string]any
	}{
		// The tool the earlier fix missed entirely.
		{"sapb1_query", map[string]any{"entity": "BusinessPartners", "count": true}},
		{"sapb1_partners", map[string]any{"count": true}},
		{"sapb1_orders", map[string]any{"count": true}},
		{"sapb1_invoices", map[string]any{"count": true}},
		{"sapb1_items", map[string]any{"count": true}},
	} {
		t.Run(tc.tool, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 3390, pageSize: 20})
			got, _ := callRows(t, f.server(), tc.tool, tc.args)

			if got.TotalCount == nil || *got.TotalCount != 3390 {
				t.Fatalf("total_count = %v, want 3390", got.TotalCount)
			}
			if got.RowsInPage != 0 {
				t.Errorf("rows_in_page = %d, want 0 — a count returns a number, not rows", got.RowsInPage)
			}
			gets := f.gets()
			if len(gets) != 1 {
				t.Fatalf("count cost %d GETs, want 1 — the number must be atomic", len(gets))
			}
			if top := gets[0].Query.Get("$top"); top != "0" {
				t.Errorf("$top = %q, want %q — any higher and SAP ships whole documents to answer \"how many?\"", top, "0")
			}
			if gets[0].Query.Get("$inlinecount") != "allpages" {
				t.Errorf("count request did not ask for $inlinecount: %v", gets[0].Query)
			}
			for _, dropped := range []string{"$select", "$orderby", "$skip"} {
				if v, present := gets[0].Query[dropped]; present {
					t.Errorf("%s = %v rode along on a count; there are no rows for it to apply to", dropped, v)
				}
			}
		})
	}
}

// TestCountModeStaysCorrectIfTheServerIgnoresTopZero — $top=0 is an
// optimisation, and the correctness of the answer must not depend on it. A
// Service Layer that served a full page anyway must still yield the server's own
// total and an empty rows array, never a page length dressed up as a count.
func TestCountModeStaysCorrectIfTheServerIgnoresTopZero(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 3390, pageSize: 20, ignoreTopZero: true})
	got, raw := callRows(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders", "count": true})

	if got.TotalCount == nil || *got.TotalCount != 3390 {
		t.Fatalf("total_count = %v, want the server's 3390", got.TotalCount)
	}
	if got.RowsInPage != 0 {
		t.Errorf("rows_in_page = %d, want 0 — rows the caller did not ask for must not leak into a count", got.RowsInPage)
	}
	if rows, ok := raw["rows"].([]any); !ok || len(rows) != 0 {
		t.Errorf("rows = %v, want an empty array", raw["rows"])
	}
	if got.Truncated {
		t.Error("a count is never truncated — it is the whole set's total")
	}
}

// TestCountModeStillRefusesToInventATotalWithTopZero — the "refuse rather than
// guess" guarantee must survive the switch to $top=0. It matters MORE now: with
// zero rows in hand, a rows-in-page fallback would report every entity set as
// empty.
func TestCountModeStillRefusesToInventATotal(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 3390, countAs: "omit"})
	isErr, text := callTool(t, f.server(), "sapb1_query", map[string]any{"entity": "Orders", "count": true})
	if !isErr {
		t.Fatalf("count answered without a server-side total: %s", text)
	}
	if !strings.Contains(text, "odata.count") {
		t.Errorf("the refusal should name what was missing, got: %s", text)
	}
	// The refusal must be prose, not a rows payload with a fabricated total.
	if strings.Contains(text, `"total_count"`) || strings.Contains(text, `"rows"`) {
		t.Errorf("the refusal returned a result payload instead of refusing: %s", text)
	}
}

// ---------------------------------------------------------------------------
// The convenience CLI-facing constant, from the MCP side
// ---------------------------------------------------------------------------

// TestOpenFilterUsesTheServiceLayerPropertyName — SAP rejects DocStatus
// outright ("Property 'DocStatus' of 'Document' is invalid"), so an open-document
// filter naming it fails the whole request. Asserted on the wire for both tools.
func TestOpenFilterUsesTheServiceLayerPropertyName(t *testing.T) {
	for _, tool := range []string{"sapb1_orders", "sapb1_invoices"} {
		t.Run(tool, func(t *testing.T) {
			isolateHome(t)
			f := newFakeSAP(t, &fakeSAP{total: 5})
			callRows(t, f.server(), tool, map[string]any{"open": true, "top": 5.0})
			g := f.gets()[0]
			if filter := g.Query.Get("$filter"); !strings.Contains(filter, "DocumentStatus eq 'bost_Open'") {
				t.Errorf("$filter = %q, want DocumentStatus eq 'bost_Open'", filter)
			}
			for _, param := range []string{"$filter", "$select"} {
				if v := g.Query.Get(param); strings.Contains(v, "DocStatus") {
					t.Errorf("%s = %q names DocStatus, which the Service Layer rejects outright", param, v)
				}
			}
		})
	}
}

// ---------------------------------------------------------------------------
// RULE 0, again — every new path is still a read
// ---------------------------------------------------------------------------

// TestNewPathsStillIssueOnlyReads re-runs the wire-level RULE 0 check over the
// paths this round of fixes touched (session sharing, the 401 refresh, count
// with a select, an empty resumed page).
func TestNewPathsStillIssueOnlyReads(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 40, pageSize: 20, honourPrefer: true, reportedCount: 500})
	s := f.server()

	calls := []struct {
		tool string
		args map[string]any
	}{
		{"sapb1_query", map[string]any{"entity": "Orders", "top": 5.0}},
		{"sapb1_query", map[string]any{"entity": "Orders", "all": true, "skip": 40.0}},
		{"sapb1_items", map[string]any{"lowStock": 0.0}},
		{"sapb1_partners", map[string]any{"count": true}},
	}
	for _, c := range calls {
		if isErr, text := callTool(t, s, c.tool, c.args); isErr {
			t.Fatalf("%s%v: %s", c.tool, c.args, text)
		}
	}
	f.expireAllSessions()
	if isErr, text := callTool(t, s, "sapb1_query", map[string]any{"entity": "Orders", "top": 5.0}); isErr {
		t.Fatalf("post-expiry call: %s", text)
	}

	for _, r := range f.seen() {
		switch {
		case r.Method == http.MethodGet:
		case r.Method == http.MethodPost && (strings.HasSuffix(r.Path, "/Login") || strings.HasSuffix(r.Path, "/Logout")):
		default:
			t.Errorf("RULE 0 VIOLATION: %s %s", r.Method, r.Path)
		}
	}
}

// ---------------------------------------------------------------------------
// Behaviours reviewed and deliberately KEPT — pinned so the decision is
// visible in code rather than re-argued from the symptom
// ---------------------------------------------------------------------------

// TestExplicitPageSizeIsHonouredEvenWhenExpensive. page_size=1 with all=true is
// legal and costs one round trip per row until client.MaxPages stops it. That
// is a footgun, but the alternative — quietly substituting a page size the
// caller did not ask for — is the silent-discard defect this surface exists to
// abolish. So the request is honoured exactly, the cost is BOUNDED by MaxPages,
// and the response says so via truncated + next_skip instead of pretending the
// sweep was complete.
func TestExplicitPageSizeIsHonouredEvenWhenExpensive(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 1000, pageSize: 100, honourPrefer: true})
	got, _ := callRows(t, f.server(), "sapb1_query", map[string]any{
		"entity": "Orders", "all": true, "page_size": 1.0,
	})

	if p := f.gets()[0].Prefer; p != "odata.maxpagesize=1" {
		t.Errorf("Prefer = %q, want the caller's odata.maxpagesize=1 — an unrequested page size is a silently changed request", p)
	}
	if n := len(f.gets()); n != client.MaxPages {
		t.Errorf("sweep cost %d GETs, want the MaxPages bound of %d", n, client.MaxPages)
	}
	if got.RowsInPage != client.MaxPages {
		t.Errorf("rows_in_page = %d, want %d", got.RowsInPage, client.MaxPages)
	}
	if !got.Truncated {
		t.Error("a sweep stopped by the page cap must report truncated — otherwise 200 of 1000 rows reads as the whole set")
	}
	if got.NextSkip == nil || *got.NextSkip != client.MaxPages {
		t.Errorf("next_skip = %v, want %d so the caller can resume", got.NextSkip, client.MaxPages)
	}
}

// TestTotalCountIsTheWholeSetNotWhatIsLeft pins SAP's own semantics, which read
// like a contradiction until they are stated: $inlinecount is computed over the
// whole filtered set and is $skip-agnostic. So `all=true, skip=2180` against
// 2184 rows legitimately answers "4 rows in this page, 2184 in the set, nothing
// truncated" — the sweep from that offset really is complete. Pinned because
// the temptation to "fix" the apparent inconsistency is exactly what produced
// the false-truncation defect.
func TestTotalCountIsTheWholeSetNotWhatIsLeft(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 2184, pageSize: 100, honourPrefer: true})
	got, raw := callRows(t, f.server(), "sapb1_partners", map[string]any{
		"company": "JIVO_MART_HANADB", "all": true, "skip": 2180.0,
	})

	if got.RowsInPage != 4 {
		t.Errorf("rows_in_page = %d, want the remaining 4", got.RowsInPage)
	}
	if got.TotalCount == nil || *got.TotalCount != 2184 {
		t.Errorf("total_count = %v, want the whole set's 2184", got.TotalCount)
	}
	if got.Truncated {
		t.Error("truncated = true although the sweep from skip=2180 drained the set")
	}
	if _, present := raw["next_skip"]; present {
		t.Errorf("next_skip present on a complete resume: %v", raw["next_skip"])
	}
}
