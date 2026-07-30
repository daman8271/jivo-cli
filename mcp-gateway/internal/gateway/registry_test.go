package gateway

import (
	"context"
	"encoding/json"
	"strings"
	"sync"
	"testing"
	"time"
)

// testRegistry builds a registry over the given fakes with the given TTL.
func testRegistry(t *testing.T, ttl time.Duration, confs ...BackendConf) *registry {
	t.Helper()
	cfg := DefaultConfig()
	cfg.ToolsTTL = ttl
	cfg.ListTimeout = 5 * time.Second
	cfg.Backends = confs
	return newRegistry(cfg, "test")
}

// namesOf extracts the "name" of each raw tool definition.
func namesOf(t *testing.T, tools []json.RawMessage) []string {
	t.Helper()
	out := make([]string, 0, len(tools))
	for _, raw := range tools {
		var def struct {
			Name string `json:"name"`
		}
		if err := json.Unmarshal(raw, &def); err != nil {
			t.Fatalf("tool def is not JSON: %v (%s)", err, raw)
		}
		out = append(out, def.Name)
	}
	return out
}

// Merged list: every backend's tools, prefixed, in configured backend order —
// and the order is identical across refreshes.
func TestRegistryMergeOrderIsStable(t *testing.T) {
	a := newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"query", "doctor"}})
	b := newFakeBackend(t, fakeOpts{name: "postsql", stateful: true, tools: []string{"postgres_query"}})
	c := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, sse: true, tools: []string{"orders", "skus", "pos"}})

	reg := testRegistry(t, time.Hour, a.conf("sap_"), b.conf("pg_"), c.conf("ecom_"))

	want := []string{"sap_query", "sap_doctor", "pg_postgres_query", "ecom_orders", "ecom_skus", "ecom_pos"}
	for round := 0; round < 3; round++ {
		reg.refresh(t.Context())
		got := namesOf(t, reg.toolsList(t.Context()))
		if strings.Join(got, ",") != strings.Join(want, ",") {
			t.Fatalf("round %d names = %v, want %v", round, got, want)
		}
	}
}

// Renaming rewrites only the name: every other member of the definition
// survives byte-for-byte.
func TestRenameToolKeepsEverythingElse(t *testing.T) {
	src := `{"name":"query","description":"d","inputSchema":{"type":"object","properties":{"x":{"type":"string"}}},` +
		`"outputSchema":{"type":"object"},"annotations":{"readOnlyHint":true,"title":"Q"},"_extra":[1,2,3]}`
	var tool map[string]json.RawMessage
	if err := json.Unmarshal([]byte(src), &tool); err != nil {
		t.Fatal(err)
	}
	def, err := renameTool(tool, "", "sap_")
	if err != nil {
		t.Fatalf("renameTool: %v", err)
	}
	if def.name != "sap_query" {
		t.Fatalf("def.name = %q, want sap_query", def.name)
	}
	var got map[string]json.RawMessage
	if err := json.Unmarshal(def.raw, &got); err != nil {
		t.Fatal(err)
	}
	if string(got["name"]) != `"sap_query"` {
		t.Fatalf("name = %s, want \"sap_query\"", got["name"])
	}
	var want map[string]json.RawMessage
	json.Unmarshal([]byte(src), &want)
	for k, v := range want {
		if k == "name" {
			continue
		}
		if string(got[k]) != string(v) {
			t.Fatalf("member %q = %s, want %s unchanged", k, got[k], v)
		}
	}
	if len(got) != len(want) {
		t.Fatalf("members = %d, want %d (nothing added or dropped)", len(got), len(want))
	}
}

func TestRenameToolRejectsBadDefs(t *testing.T) {
	for _, src := range []string{`{}`, `{"name":123}`, `{"name":""}`} {
		var tool map[string]json.RawMessage
		json.Unmarshal([]byte(src), &tool)
		if _, err := renameTool(tool, "", "sap_"); err == nil {
			t.Fatalf("renameTool(%s) = nil error, want failure", src)
		}
	}
	// A name that is nothing but the stripped prefix would collapse to the bare
	// gateway prefix, which is not a tool name.
	var tool map[string]json.RawMessage
	json.Unmarshal([]byte(`{"name":"sapb1_"}`), &tool)
	if _, err := renameTool(tool, "sapb1_", "sap_"); err == nil {
		t.Fatal("renameTool(sapb1_ with strip sapb1_) = nil error, want failure")
	}
}

// F1. StripPrefix removes a backend's own redundant prefix before the gateway
// prefix is added, so sapb1_query is advertised as sap_query, not
// sap_sapb1_query. A name that does not carry the prefix is left alone.
func TestRenameToolStripsRedundantPrefix(t *testing.T) {
	cases := []struct{ in, strip, prefix, want string }{
		{"sapb1_query", "sapb1_", "sap_", "sap_query"},
		{"sapb1_partners", "sapb1_", "sap_", "sap_partners"},
		{"doctor", "sapb1_", "sap_", "sap_doctor"},         // no redundant prefix to strip
		{"sapb1_sapb1_x", "sapb1_", "sap_", "sap_sapb1_x"}, // strips once, not greedily
		{"postgres_query", "", "pg_", "pg_postgres_query"}, // no strip configured
		{"jivo-ecom_search", "", "ecom_", "ecom_jivo-ecom_search"},
	}
	for _, c := range cases {
		var tool map[string]json.RawMessage
		if err := json.Unmarshal([]byte(`{"name":"`+c.in+`","description":"d"}`), &tool); err != nil {
			t.Fatal(err)
		}
		def, err := renameTool(tool, c.strip, c.prefix)
		if err != nil {
			t.Fatalf("renameTool(%q, %q, %q): %v", c.in, c.strip, c.prefix, err)
		}
		if def.name != c.want {
			t.Fatalf("renameTool(%q, strip %q, prefix %q) = %q, want %q", c.in, c.strip, c.prefix, def.name, c.want)
		}
	}
}

// Routing comes from the prefix table alone: it works before any refresh, and
// it strips exactly the prefix.
func TestRegistryResolveUsesPrefixTableOnly(t *testing.T) {
	a := newFakeBackend(t, fakeOpts{name: "sapb1"})
	b := newFakeBackend(t, fakeOpts{name: "factory"})
	reg := testRegistry(t, time.Hour, a.conf("sap_"), b.conf("fct_"))

	cases := []struct {
		in       string
		backend  string
		upstream string
		ok       bool
	}{
		{"sap_query", "sapb1", "query", true},
		{"fct_production_orders", "factory", "production_orders", true},
		{"sap_pg_weird_name", "sapb1", "pg_weird_name", true},
		{"pg_query", "", "", false},
		{"sap_", "", "", false}, // prefix with no tool name behind it
		{"gateway_status", "", "", false},
		{"", "", "", false},
	}
	for _, c := range cases {
		got, upstream, ok := reg.resolve(c.in)
		if ok != c.ok {
			t.Fatalf("resolve(%q) ok = %v, want %v", c.in, ok, c.ok)
		}
		if !ok {
			continue
		}
		if got.conf.Name != c.backend || upstream != c.upstream {
			t.Fatalf("resolve(%q) = %s/%q, want %s/%q", c.in, got.conf.Name, upstream, c.backend, c.upstream)
		}
	}
	// Nothing above touched the network.
	if inits, _, _ := a.stats(); inits != 0 {
		t.Fatalf("resolve talked to a backend (%d initializes)", inits)
	}
}

// A backend that goes down keeps its last known tools (stale-while-down) and is
// reported down with the error.
func TestRegistryStaleWhileDown(t *testing.T) {
	up := newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"query"}})
	flaky := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"orders", "skus"}})

	reg := testRegistry(t, 0, up.conf("sap_"), flaky.conf("ecom_")) // ttl 0: always stale
	reg.refresh(t.Context())
	if got := namesOf(t, reg.toolsList(t.Context())); len(got) != 3 {
		t.Fatalf("tools = %v, want 3 while both are up", got)
	}

	flaky.srv.Close() // backend restart / crash
	reg.refresh(t.Context())

	got := namesOf(t, reg.toolsList(t.Context()))
	want := []string{"sap_query", "ecom_orders", "ecom_skus"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("tools = %v, want the stale list %v kept", got, want)
	}
	st := reg.snapshot()
	if len(st) != 2 {
		t.Fatalf("snapshot = %v, want 2 rows", st)
	}
	if !st[0].Up || st[0].ToolCount != 1 {
		t.Fatalf("sapb1 status = %+v, want up with 1 tool", st[0])
	}
	if st[1].Up {
		t.Fatalf("ecom status = %+v, want down", st[1])
	}
	if st[1].LastError == "" || st[1].ToolCount != 2 {
		t.Fatalf("ecom status = %+v, want an error and its 2 stale tools counted", st[1])
	}
	if st[1].LastRefresh.IsZero() {
		t.Fatalf("ecom LastRefresh is zero, want the failed attempt's time")
	}
}

// One dead backend must not stop the others being listed.
func TestRegistryDownBackendDoesNotBlockOthers(t *testing.T) {
	dead := newFakeBackend(t, fakeOpts{name: "oms"})
	dead.srv.Close()
	alive := newFakeBackend(t, fakeOpts{name: "postsql", tools: []string{"postgres_query"}})

	reg := testRegistry(t, time.Hour, dead.conf("oms_"), alive.conf("pg_"))
	got := namesOf(t, reg.toolsList(t.Context()))
	if strings.Join(got, ",") != "pg_postgres_query" {
		t.Fatalf("tools = %v, want just pg_postgres_query", got)
	}
	st := reg.snapshot()
	if st[0].Up || !st[1].Up {
		t.Fatalf("status = %+v, want oms down and postsql up", st)
	}
}

// TTL: inside it the cache is served without touching a backend; ttl 0 refreshes
// on every call.
func TestRegistryTTLLaziness(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"orders"}})
	reg := testRegistry(t, time.Hour, f.conf("ecom_"))

	for i := 0; i < 4; i++ {
		if got := namesOf(t, reg.toolsList(t.Context())); len(got) != 1 {
			t.Fatalf("call %d tools = %v, want 1", i, got)
		}
	}
	if n := len(f.callsOf("tools/list")); n != 1 {
		t.Fatalf("tools/list requests = %d, want 1 inside the TTL", n)
	}

	eager := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"orders"}})
	regEager := testRegistry(t, 0, eager.conf("ecom_"))
	for i := 0; i < 3; i++ {
		regEager.toolsList(t.Context())
	}
	if n := len(eager.callsOf("tools/list")); n != 3 {
		t.Fatalf("tools/list requests = %d, want 3 with ttl 0", n)
	}
}

// Single-flight: while one refresh is in flight, other callers are served the
// current snapshot instead of piling on more backend requests.
func TestRegistrySingleFlightRefresh(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"orders"}, listDelay: 300 * time.Millisecond})
	reg := testRegistry(t, 0, f.conf("ecom_")) // always stale

	var wg sync.WaitGroup
	start := make(chan struct{})
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			reg.toolsList(t.Context())
		}()
	}
	close(start)
	wg.Wait()

	if n := len(f.callsOf("tools/list")); n != 1 {
		t.Fatalf("tools/list requests = %d, want 1 (single-flight)", n)
	}
	if got := namesOf(t, reg.toolsList(t.Context())); len(got) != 1 {
		t.Fatalf("after the refresh, tools = %v, want 1", got)
	}
}

// A backend slower than the list timeout is marked down without hanging the
// refresh.
func TestRegistryListTimeoutMarksDown(t *testing.T) {
	slow := newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"query"}, listDelay: 2 * time.Second})
	fast := newFakeBackend(t, fakeOpts{name: "oms", tools: []string{"orders"}})

	cfg := DefaultConfig()
	cfg.ToolsTTL = time.Hour
	cfg.ListTimeout = 100 * time.Millisecond
	cfg.Backends = []BackendConf{slow.conf("sap_"), fast.conf("oms_")}
	reg := newRegistry(cfg, "test")

	began := time.Now()
	reg.refresh(t.Context())
	if elapsed := time.Since(began); elapsed > time.Second {
		t.Fatalf("refresh took %v, want it bounded by the 100ms per-backend timeout", elapsed)
	}
	st := reg.snapshot()
	if st[0].Up || st[0].LastError == "" {
		t.Fatalf("slow backend status = %+v, want down with an error", st[0])
	}
	if !st[1].Up {
		t.Fatalf("fast backend status = %+v, want up", st[1])
	}
}

// B2. A client that abandons tools/list must not poison the shared cache. The
// refresh runs on a context detached from the caller's, so a disconnect after
// 50ms cannot mark every backend down (ctx.Canceled) for a whole TTL — which is
// what happened when the fan-out ran on the request context.
func TestRegistryAbandonedCallerDoesNotPoisonStatus(t *testing.T) {
	slow := newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"query"}, listDelay: 250 * time.Millisecond})
	fast := newFakeBackend(t, fakeOpts{name: "oms", stateful: true, tools: []string{"orders"}})

	cfg := DefaultConfig()
	cfg.ToolsTTL = time.Hour
	cfg.ListTimeout = 5 * time.Second
	cfg.Backends = []BackendConf{slow.conf("sap_"), fast.conf("oms_")}
	reg := newRegistry(cfg, "test")

	// The client hangs up 50ms in, long before the slow backend answers.
	ctx, cancel := context.WithTimeout(t.Context(), 50*time.Millisecond)
	defer cancel()
	reg.toolsList(ctx)

	// Nothing was poisoned: both backends are up, with their real tools.
	for _, st := range reg.snapshot() {
		if !st.Up {
			t.Fatalf("%s = %+v, want up (the caller's cancellation is not a backend failure)", st.Name, st)
		}
		if st.LastError != "" {
			t.Fatalf("%s last_error = %q, want empty", st.Name, st.LastError)
		}
		if st.ToolCount != 1 {
			t.Fatalf("%s tool_count = %d, want 1", st.Name, st.ToolCount)
		}
	}
	// And the next client is served the full list from the fresh cache.
	got := namesOf(t, reg.toolsList(t.Context()))
	if strings.Join(got, ",") != "sap_query,oms_orders" {
		t.Fatalf("tools = %v, want both backends", got)
	}
	if n := len(slow.callsOf("tools/list")); n != 1 {
		t.Fatalf("slow backend tools/list requests = %d, want 1 (the cache is fresh)", n)
	}
}

// B1 at registry level: one backend that accepts TCP and never answers
// initialize must not stall the fan-out beyond the per-backend budget, and must
// not stop the others from being listed. Before the fix the initialize happened
// under a mutex and wg.Wait() waited on it uninterruptibly.
func TestRegistryHungInitializeDoesNotStallRefresh(t *testing.T) {
	hung := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, initDelay: 5 * time.Second, tools: []string{"orders"}})
	fast := newFakeBackend(t, fakeOpts{name: "postsql", tools: []string{"postgres_query"}})

	cfg := DefaultConfig()
	cfg.ToolsTTL = time.Hour
	cfg.ListTimeout = 150 * time.Millisecond
	cfg.Backends = []BackendConf{hung.conf("ecom_"), fast.conf("pg_")}
	reg := newRegistry(cfg, "test")

	began := time.Now()
	got := namesOf(t, reg.toolsList(t.Context()))
	elapsed := time.Since(began)

	if elapsed > 2*time.Second {
		t.Fatalf("refresh took %v, want it bounded by the 150ms per-backend budget", elapsed)
	}
	if strings.Join(got, ",") != "pg_postgres_query" {
		t.Fatalf("tools = %v, want the healthy backend's tools", got)
	}
	st := reg.snapshot()
	if st[0].Up || st[0].LastError == "" {
		t.Fatalf("hung backend = %+v, want down with an error", st[0])
	}
	if !st[1].Up {
		t.Fatalf("healthy backend = %+v, want up", st[1])
	}
}

// C1 at registry level. A refresh that only lost leadership races to callers who
// then cancelled must not mark the backend down: its failure cause was other
// people's deadlines, not this backend.
//
// Before the fix the wait/takeover loop handed the refresh a synthetic
// "session initialization keeps failing" error, which — being a plain error and
// not a context one — slipped straight past apply's cancellation guard and left a
// healthy backend at up=false, with an empty tool list, for a whole TTL. That is
// the B2 symptom through a new door.
func TestRegistryRefreshNotPoisonedByOtherCallersCancellations(t *testing.T) {
	const (
		waves    = 6
		perWave  = 5
		waveGap  = 30 * time.Millisecond
		hangUpAt = 80 * time.Millisecond
	)
	f := newFakeBackend(t, fakeOpts{
		name: "ecom", stateful: true, initDelay: 300 * time.Millisecond,
		tools: []string{"orders", "skus"},
	})

	cfg := DefaultConfig()
	cfg.ToolsTTL = time.Hour
	cfg.ListTimeout = 10 * time.Second // the refresh is the patient caller here
	cfg.Backends = []BackendConf{f.conf("ecom_")}
	reg := newRegistry(cfg, "test")
	b := reg.backends[0]

	// Waves of tools/call clients on the same backend, each hanging up after
	// 80ms — long enough to claim the initialize, never long enough to finish it.
	var wg sync.WaitGroup
	for w := 0; w < waves; w++ {
		for i := 0; i < perWave; i++ {
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				time.Sleep(time.Duration(w) * waveGap)
				ctx, cancel := context.WithTimeout(context.Background(), hangUpAt)
				defer cancel()
				b.callTool(ctx, "orders", nil)
			}(w)
		}
	}

	time.Sleep(waveGap / 4) // let the first wave take the lead
	reg.refresh(t.Context())
	wg.Wait()

	st := reg.snapshot()[0]
	if !st.Up {
		t.Fatalf("backend = %+v, want up: the only failures were other callers' cancellations", st)
	}
	if st.LastError != "" {
		t.Fatalf("last_error = %q, want empty", st.LastError)
	}
	if got := namesOf(t, reg.cachedTools()); strings.Join(got, ",") != "ecom_orders,ecom_skus" {
		t.Fatalf("tools = %v, want both tools listed", got)
	}
}

// R2. A caller that arrives during the FIRST-EVER refresh has no snapshot to be
// served: stale-while-refresh has nothing stale yet, and it used to be handed an
// empty list — "this gateway has no tools" — which a client like claude.ai then
// caches. Cold-start callers now wait for that first refresh (bounded by their own
// context and the list budget) instead.
func TestRegistryColdStartCallersWaitForFirstRefresh(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{
		name: "ecom", stateful: true, tools: []string{"orders", "skus"},
		listDelay: 300 * time.Millisecond,
	})
	reg := testRegistry(t, time.Hour, f.conf("ecom_"))

	var wg sync.WaitGroup
	counts := make([]int, 8)
	for i := range counts {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			counts[i] = len(reg.toolsList(t.Context()))
		}(i)
	}
	wg.Wait()

	for i, n := range counts {
		if n != 2 {
			t.Fatalf("cold-start caller %d got %d tools, want 2 (nobody may be served an empty list)", i, n)
		}
	}
	if n := len(f.callsOf("tools/list")); n != 1 {
		t.Fatalf("tools/list requests = %d, want 1 (single-flight still holds)", n)
	}
}

// R2, other half: once a first refresh has completed there IS a last known list,
// so a caller arriving during a later refresh is served it immediately. Waiting
// there would put five network round-trips in front of a client for nothing.
func TestRegistryStaleWhileRefreshStillDoesNotWait(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{
		name: "ecom", stateful: true, tools: []string{"orders"},
		listDelay: 400 * time.Millisecond,
	})
	reg := testRegistry(t, 0, f.conf("ecom_")) // ttl 0: always stale
	reg.refresh(t.Context())                   // ... and now one refresh has landed

	refreshing := make(chan struct{})
	go func() {
		close(refreshing)
		reg.refresh(context.Background())
	}()
	<-refreshing
	time.Sleep(50 * time.Millisecond) // let it claim the single-flight slot

	began := time.Now()
	got := namesOf(t, reg.toolsList(t.Context()))
	if elapsed := time.Since(began); elapsed > 200*time.Millisecond {
		t.Fatalf("caller waited %v during a later refresh, want the last known list at once", elapsed)
	}
	if strings.Join(got, ",") != "ecom_orders" {
		t.Fatalf("tools = %v, want the last known list", got)
	}
}

// R1. A single-flight waiter honours its own context. The leader stays detached,
// because the refresh it is running belongs to every client, but a waiter whose
// request has been abandoned must not stay parked for the whole list budget.
func TestRegistryRefreshWaiterHonoursCallerContext(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{
		name: "ecom", stateful: true, tools: []string{"orders"},
		listDelay: 700 * time.Millisecond,
	})
	cfg := DefaultConfig()
	cfg.ToolsTTL = 0
	cfg.ListTimeout = 5 * time.Second
	cfg.Backends = []BackendConf{f.conf("ecom_")}
	reg := newRegistry(cfg, "test")

	// A leader takes the slot and will be busy for 700ms.
	leaderDone := make(chan struct{})
	go func() {
		defer close(leaderDone)
		reg.refresh(context.Background())
	}()
	time.Sleep(50 * time.Millisecond)

	ctx, cancel := context.WithTimeout(t.Context(), 100*time.Millisecond)
	defer cancel()
	began := time.Now()
	reg.refreshWithin(ctx, 5*time.Second)
	if elapsed := time.Since(began); elapsed > 400*time.Millisecond {
		t.Fatalf("waiter parked %v after its caller gave up, want ~100ms", elapsed)
	}

	// The leader was not disturbed: the shared refresh still completed.
	<-leaderDone
	if n := len(f.callsOf("tools/list")); n != 1 {
		t.Fatalf("tools/list requests = %d, want 1", n)
	}
	if st := reg.snapshot()[0]; !st.Up || st.ToolCount != 1 {
		t.Fatalf("status = %+v, want up with 1 tool", st)
	}
}

// S3. A backend that comes back up but answers with zero tools (half-booted,
// registration not finished) must not wipe its tools out of the merged list. It
// stays up, keeps its last known tools, and says so.
func TestRegistryEmptyToolListKeepsLastKnown(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"orders", "skus"}})
	reg := testRegistry(t, 0, f.conf("ecom_")) // ttl 0: every call refreshes

	if got := namesOf(t, reg.toolsList(t.Context())); len(got) != 2 {
		t.Fatalf("tools = %v, want 2 while the backend is healthy", got)
	}

	f.serveEmptyTools(true)
	got := namesOf(t, reg.toolsList(t.Context()))
	if strings.Join(got, ",") != "ecom_orders,ecom_skus" {
		t.Fatalf("tools = %v, want the last known list kept", got)
	}
	st := reg.snapshot()[0]
	if !st.Up {
		t.Fatalf("status = %+v, want up (the backend answered)", st)
	}
	if !strings.Contains(st.LastError, "empty tool list") {
		t.Fatalf("last_error = %q, want it to mention the empty tool list", st.LastError)
	}
	if st.ToolCount != 2 {
		t.Fatalf("tool_count = %d, want the 2 tools still advertised", st.ToolCount)
	}

	// And a real recovery replaces them again, cleanly.
	f.serveEmptyTools(false)
	if got := namesOf(t, reg.toolsList(t.Context())); len(got) != 2 {
		t.Fatalf("tools after recovery = %v, want 2", got)
	}
	if st := reg.snapshot()[0]; st.LastError != "" {
		t.Fatalf("last_error after recovery = %q, want empty", st.LastError)
	}
}

// S4. A backend looping on one nextCursor is a failed refresh: it must be marked
// down and its last complete list kept, not replaced by a tenfold-duplicated one
// while being reported healthy.
func TestRegistryRepeatedCursorMarksDownAndKeepsList(t *testing.T) {
	good := newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"query"}})
	loop := newFakeBackend(t, fakeOpts{name: "factory", tools: []string{"production", "stock"}})

	reg := testRegistry(t, 0, good.conf("sap_"), loop.conf("fct_"))
	if got := namesOf(t, reg.toolsList(t.Context())); len(got) != 3 {
		t.Fatalf("tools = %v, want 3 while both are healthy", got)
	}

	// The same backend, now looping. (A second fake on the same prefix, because
	// the mode is fixed at construction.)
	broken := newFakeBackend(t, fakeOpts{name: "factory", repeatCursor: true, tools: []string{"production", "stock"}})
	reg.backends[1] = newBackend(broken.conf("fct_"), newHTTPClient(), "test")
	reg.refresh(t.Context())

	got := namesOf(t, reg.toolsList(t.Context()))
	if strings.Join(got, ",") != "sap_query,fct_production,fct_stock" {
		t.Fatalf("tools = %v, want the last complete list (no duplicates)", got)
	}
	st := reg.snapshot()[1]
	if st.Up {
		t.Fatalf("looping backend = %+v, want down", st)
	}
	if !strings.Contains(st.LastError, "repeated") {
		t.Fatalf("last_error = %q, want it to name the repeated cursor", st.LastError)
	}
	if st.ToolCount != 2 {
		t.Fatalf("tool_count = %d, want its 2 stale tools still counted", st.ToolCount)
	}
}

// S4 / N13. Two backends whose tools collide after prefixing: the first in
// configured order wins, the duplicate is dropped rather than advertised twice,
// and the losing backend's status says what it lost.
func TestRegistryDropsDuplicateToolNames(t *testing.T) {
	// Same prefix on both, so their tool names collide by construction.
	a := newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"query", "doctor"}})
	b := newFakeBackend(t, fakeOpts{name: "twin", tools: []string{"query", "extra"}})

	reg := testRegistry(t, time.Hour, a.conf("sap_"), b.conf("sap_"))
	reg.refresh(t.Context())

	got := namesOf(t, reg.toolsList(t.Context()))
	want := []string{"sap_query", "sap_doctor", "sap_extra"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("tools = %v, want %v (one sap_query only)", got, want)
	}
	st := reg.snapshot()
	if st[0].ToolCount != 2 || st[0].LastError != "" {
		t.Fatalf("first backend = %+v, want 2 tools and no error", st[0])
	}
	if st[1].ToolCount != 1 {
		t.Fatalf("second backend tool_count = %d, want 1 (the dropped one does not count)", st[1].ToolCount)
	}
	if !strings.Contains(st[1].LastError, "duplicate") || !strings.Contains(st[1].LastError, "sap_query") {
		t.Fatalf("second backend last_error = %q, want the dropped name named", st[1].LastError)
	}
	if !st[1].Up {
		t.Fatalf("second backend = %+v, want still up (a collision is not an outage)", st[1])
	}

	// Refreshing again must not accumulate the same note twice.
	reg.refresh(t.Context())
	if n := strings.Count(reg.snapshot()[1].LastError, "duplicate"); n != 1 {
		t.Fatalf("last_error = %q, want the note recorded exactly once", reg.snapshot()[1].LastError)
	}
}

// N14. One malformed tool definition must not fail the whole backend: the rest
// are kept, the backend stays up, and the skip is reported.
func TestRegistrySkipsMalformedToolDefs(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{
		name:  "ecom",
		tools: []string{"orders", "skus"},
		malformedTools: []string{
			`{"description":"no name at all"}`,
			`{"name":42,"description":"name is not a string"}`,
			`{"name":"","description":"empty name"}`,
		},
	})
	reg := testRegistry(t, time.Hour, f.conf("ecom_"))
	reg.refresh(t.Context())

	got := namesOf(t, reg.toolsList(t.Context()))
	if strings.Join(got, ",") != "ecom_orders,ecom_skus" {
		t.Fatalf("tools = %v, want the two good ones kept", got)
	}
	st := reg.snapshot()[0]
	if !st.Up {
		t.Fatalf("status = %+v, want up (a bad definition is not an outage)", st)
	}
	if !strings.Contains(st.LastError, "skipped 3 malformed") {
		t.Fatalf("last_error = %q, want the 3 skips reported", st.LastError)
	}
	if st.ToolCount != 2 {
		t.Fatalf("tool_count = %d, want 2", st.ToolCount)
	}
}

// F1. resolve is the exact inverse of what refresh advertised: the gateway
// prefix comes off and the backend's own redundant prefix goes back on.
func TestRegistryResolveReAddsStripPrefix(t *testing.T) {
	sap := newFakeBackend(t, fakeOpts{name: "sapb1"})
	pg := newFakeBackend(t, fakeOpts{name: "postsql"})
	reg := testRegistry(t, time.Hour, sap.confStrip("sap_", "sapb1_"), pg.conf("pg_"))

	cases := []struct{ in, backend, upstream string }{
		{"sap_query", "sapb1", "sapb1_query"},
		{"sap_partners", "sapb1", "sapb1_partners"},
		{"pg_postgres_query", "postsql", "postgres_query"},
	}
	for _, c := range cases {
		b, upstream, ok := reg.resolve(c.in)
		if !ok {
			t.Fatalf("resolve(%q) not found", c.in)
		}
		if b.conf.Name != c.backend || upstream != c.upstream {
			t.Fatalf("resolve(%q) = %s/%q, want %s/%q", c.in, b.conf.Name, upstream, c.backend, c.upstream)
		}
	}
}

func TestRegistrySnapshotBeforeAnyRefresh(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom"})
	reg := testRegistry(t, time.Hour, f.conf("ecom_"))
	st := reg.snapshot()
	if len(st) != 1 || st[0].Name != "ecom" || st[0].Prefix != "ecom_" || st[0].Up || st[0].ToolCount != 0 {
		t.Fatalf("snapshot = %+v, want one down/zero row for ecom", st)
	}
	if !st[0].LastRefresh.IsZero() || !reg.lastRefreshedAt().IsZero() {
		t.Fatalf("timestamps = %v/%v, want zero before any refresh", st[0].LastRefresh, reg.lastRefreshedAt())
	}
}
