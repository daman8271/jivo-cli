package gateway

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
)

// --- a v0.47.0-faithful fake backend ------------------------------------------
//
// Everything the gateway has to survive is modelled here, from the verified
// v0.47.0 contract: application/json is mandatory on POST, initialize answers
// with an Mcp-Session-Id response header, later requests must carry it, an
// unknown/terminated session is a plain-text 404 (not a JSON-RPC error), and a
// response may arrive as text/event-stream with the JSON-RPC message in a
// data: event. Stateless backends (sapb1 v0.56, postsql) are the same fake with
// stateful=false: no header issued, none expected.

type fakeOpts struct {
	name         string
	stateful     bool          // issue + require Mcp-Session-Id
	sse          bool          // answer with text/event-stream
	sseNoise     bool          // interleave an unrelated notification event first
	tools        []string      // single-page tool list
	pages        [][]string    // paginated tool list (wins over tools)
	alwaysExpire bool          // 404 every session-carrying request
	toolError    bool          // answer tools/call with a JSON-RPC error
	listDelay    time.Duration // stall tools/list (single-flight / timeout tests)
	callResult   string        // exact raw result JSON for tools/call (passthrough tests)

	// Failure modes for the round-2 regressions.
	initDelay       time.Duration // stall initialize: a backend that accepts TCP and never answers
	noSessionHeader bool          // stateful, but never returns Mcp-Session-Id (wedge)
	repeatCursor    bool          // always answer with the same nextCursor (pagination loop)
	badRequest      bool          // deterministic HTTP 400 on every non-initialize request
	decoyID         bool          // answer with a JSON-RPC id that is not the one asked
	malformedTools  []string      // raw tool definitions injected verbatim (bad ones)
}

type recordedCall struct {
	method      string
	session     string
	contentType string
	accept      string
	params      json.RawMessage
}

type fakeBackend struct {
	srv  *httptest.Server
	opts fakeOpts

	mu          sync.Mutex
	sessions    map[string]bool
	seq         int
	initializes int
	initialized int // notifications/initialized received
	calls       []recordedCall
	emptyTools  bool // serve zero tools from now on (a half-booted backend)
}

func newFakeBackend(t *testing.T, opts fakeOpts) *fakeBackend {
	t.Helper()
	if opts.name == "" {
		opts.name = "fake"
	}
	f := &fakeBackend{opts: opts, sessions: map[string]bool{}}
	f.srv = httptest.NewServer(http.HandlerFunc(f.serve))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeBackend) url() string { return f.srv.URL + "/mcp" }

func (f *fakeBackend) conf(prefix string) BackendConf {
	return BackendConf{Name: f.opts.name, Prefix: prefix, URL: f.url()}
}

// confStrip is conf plus a redundant backend-side prefix to strip.
func (f *fakeBackend) confStrip(prefix, strip string) BackendConf {
	c := f.conf(prefix)
	c.StripPrefix = strip
	return c
}

// expireAll drops every live session, exactly like v0.47.0's idle sweeper.
func (f *fakeBackend) expireAll() {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.sessions = map[string]bool{}
}

// serveEmptyTools makes tools/list answer, successfully, with no tools at all —
// what a backend that has restarted but not finished registering looks like.
func (f *fakeBackend) serveEmptyTools(empty bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.emptyTools = empty
}

func (f *fakeBackend) stats() (initializes, initialized int, calls []recordedCall) {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.initializes, f.initialized, append([]recordedCall(nil), f.calls...)
}

// callsOf returns the recorded calls for one method.
func (f *fakeBackend) callsOf(method string) []recordedCall {
	_, _, all := f.stats()
	var out []recordedCall
	for _, c := range all {
		if c.method == method {
			out = append(out, c)
		}
	}
	return out
}

func (f *fakeBackend) serve(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", http.MethodPost)
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	// v0.47.0: a POST without application/json is a plain-text 400.
	if ct := r.Header.Get("Content-Type"); !strings.HasPrefix(ct, "application/json") {
		http.Error(w, "Content-Type must be application/json", http.StatusBadRequest)
		return
	}

	var req rpcRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	sid := r.Header.Get(sessionHeader)

	f.mu.Lock()
	f.calls = append(f.calls, recordedCall{
		method:      req.Method,
		session:     sid,
		contentType: r.Header.Get("Content-Type"),
		accept:      r.Header.Get("Accept"),
		params:      req.Params,
	})
	if req.Method == "initialize" {
		f.initializes++
		f.seq++
		if f.opts.stateful {
			sid = fmt.Sprintf("mcp-session-%s-%d", f.opts.name, f.seq)
			f.sessions[sid] = true
		}
	}
	if req.Method == "notifications/initialized" {
		f.initialized++
	}
	known := !f.opts.stateful || f.sessions[sid]
	f.mu.Unlock()

	if req.Method == "initialize" {
		// A backend that accepts the connection and then never answers.
		if f.opts.initDelay > 0 {
			select {
			case <-time.After(f.opts.initDelay):
			case <-r.Context().Done():
				return
			}
		}
		if f.opts.stateful && !f.opts.noSessionHeader {
			w.Header().Set(sessionHeader, sid)
		}
		f.reply(w, "initialize", req.ID, `{"protocolVersion":"`+backendProtocolVersion+
			`","capabilities":{"tools":{}},"serverInfo":{"name":"`+f.opts.name+`","version":"0.47.0"}}`)
		return
	}

	// Session enforcement, v0.47.0 style: plain-text 404, no JSON-RPC envelope.
	// With noSessionHeader the client cannot possibly satisfy this, which is the
	// wedge being reproduced.
	if f.opts.stateful && (f.opts.alwaysExpire || !known) {
		http.Error(w, "Invalid session ID", http.StatusNotFound)
		return
	}

	// A deterministic 400 (v0.47.0 does this for a bad Content-Type or bad
	// params): a real error, on every call, forever — never a session expiry.
	if f.opts.badRequest {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}

	if strings.HasPrefix(req.Method, "notifications/") {
		w.WriteHeader(http.StatusAccepted)
		return
	}

	switch req.Method {
	case "tools/list":
		if f.opts.listDelay > 0 {
			select {
			case <-time.After(f.opts.listDelay):
			case <-r.Context().Done():
				return
			}
		}
		f.replyToolsList(w, req)
	case "tools/call":
		if f.opts.toolError {
			f.replyError(w, req.ID, -32001, "backend says no", `{"detail":"upstream"}`)
			return
		}
		if f.opts.callResult != "" {
			f.reply(w, req.Method, req.ID, f.opts.callResult)
			return
		}
		var call struct {
			Name      string          `json:"name"`
			Arguments json.RawMessage `json:"arguments"`
		}
		json.Unmarshal(req.Params, &call)
		args := string(call.Arguments)
		if args == "" {
			args = "null"
		}
		f.reply(w, req.Method, req.ID, `{"content":[{"type":"text","text":"`+f.opts.name+`:`+call.Name+
			`"}],"isError":false,"_args":`+args+`}`)
	default:
		f.replyError(w, req.ID, -32601, "method not found: "+req.Method, "")
	}
}

func (f *fakeBackend) replyToolsList(w http.ResponseWriter, req rpcRequest) {
	var p struct {
		Cursor string `json:"cursor"`
	}
	json.Unmarshal(req.Params, &p)

	f.mu.Lock()
	empty := f.emptyTools
	f.mu.Unlock()

	pages := f.opts.pages
	if pages == nil {
		pages = [][]string{f.opts.tools}
	}
	if empty {
		pages = [][]string{nil}
	}
	idx := 0
	if p.Cursor != "" {
		fmt.Sscanf(p.Cursor, "page-%d", &idx)
	}
	if idx >= len(pages) {
		idx = len(pages) - 1
	}

	defs := make([]string, 0, len(pages[idx])+len(f.opts.malformedTools))
	for _, name := range pages[idx] {
		defs = append(defs, `{"name":"`+name+`","description":"`+f.opts.name+` tool `+name+
			`","inputSchema":{"type":"object","properties":{}},"annotations":{"readOnlyHint":true}}`)
	}
	defs = append(defs, f.opts.malformedTools...)

	result := `{"tools":[` + strings.Join(defs, ",") + `]`
	switch {
	case f.opts.repeatCursor && !empty:
		// A backend stuck on one cursor: follow it and the same page comes back
		// forever.
		result += `,"nextCursor":"page-stuck"`
	case idx+1 < len(pages):
		result += fmt.Sprintf(`,"nextCursor":"page-%d"`, idx+1)
	}
	result += `}`
	f.reply(w, "tools/list", req.ID, result)
}

// reply writes one JSON-RPC result, as JSON or as SSE depending on the fake's
// mode. With decoyID every answer after the handshake carries somebody else's
// id — the handshake itself has to work, or there is nothing left to test.
func (f *fakeBackend) reply(w http.ResponseWriter, method string, id json.RawMessage, result string) {
	if f.opts.decoyID && method != "initialize" {
		id = json.RawMessage("999999")
	}
	body := `{"jsonrpc":"2.0","id":` + string(id) + `,"result":` + result + `}`
	f.write(w, body)
}

func (f *fakeBackend) replyError(w http.ResponseWriter, id json.RawMessage, code int, msg, data string) {
	body := fmt.Sprintf(`{"jsonrpc":"2.0","id":%s,"error":{"code":%d,"message":%q`, string(id), code, msg)
	if data != "" {
		body += `,"data":` + data
	}
	body += `}}`
	f.write(w, body)
}

func (f *fakeBackend) write(w http.ResponseWriter, body string) {
	if !f.opts.sse {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(body))
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.WriteHeader(http.StatusOK)
	if f.opts.sseNoise {
		// An unrelated interleaved notification: must be skipped, not parsed as
		// our answer.
		fmt.Fprint(w, "event: message\ndata: {\"jsonrpc\":\"2.0\",\"method\":\"notifications/progress\",\"params\":{\"progress\":1}}\n\n")
	}
	fmt.Fprint(w, "event: message\ndata: "+body+"\n\n")
}

// testBackend wires a backend to a fake.
func testBackend(f *fakeBackend) *backend {
	return newBackend(f.conf("x_"), newHTTPClient(), "test")
}

// --- tests --------------------------------------------------------------------

// Lazy init: the session is created once, on the first request, and reused.
func TestBackendLazyInitOnce(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"a"}})
	b := testBackend(f)

	if inits, _, calls := f.stats(); inits != 0 || len(calls) != 0 {
		t.Fatalf("newBackend did I/O: %d initializes, %d calls", inits, len(calls))
	}
	for i := 0; i < 3; i++ {
		if _, err := b.listTools(t.Context()); err != nil {
			t.Fatalf("listTools #%d: %v", i, err)
		}
	}
	inits, initialized, calls := f.stats()
	if inits != 1 {
		t.Fatalf("initializes = %d, want 1", inits)
	}
	if initialized != 1 {
		t.Fatalf("notifications/initialized = %d, want 1", initialized)
	}
	if got := len(f.callsOf("tools/list")); got != 3 {
		t.Fatalf("tools/list calls = %d, want 3", got)
	}
	// initialize carries no session; everything after it carries the one the
	// backend issued.
	for _, c := range calls {
		switch c.method {
		case "initialize":
			if c.session != "" {
				t.Fatalf("initialize carried session %q, want none", c.session)
			}
		default:
			if !strings.HasPrefix(c.session, "mcp-session-") {
				t.Fatalf("%s carried session %q, want the issued id", c.method, c.session)
			}
		}
		if c.contentType != "application/json" {
			t.Fatalf("%s Content-Type = %q, want application/json", c.method, c.contentType)
		}
		if !strings.Contains(c.accept, "application/json") || !strings.Contains(c.accept, "text/event-stream") {
			t.Fatalf("%s Accept = %q, want both content types", c.method, c.accept)
		}
	}
}

// Concurrent first requests must produce exactly one initialize: one leader does
// the handshake, everybody else waits on it.
func TestBackendConcurrentInitIsSingle(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "oms", stateful: true, tools: []string{"a"}})
	b := testBackend(f)

	var wg sync.WaitGroup
	errs := make([]error, 8)
	for i := range errs {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			_, errs[i] = b.listTools(t.Context())
		}(i)
	}
	wg.Wait()
	for i, err := range errs {
		if err != nil {
			t.Fatalf("listTools #%d: %v", i, err)
		}
	}
	if inits, _, _ := f.stats(); inits != 1 {
		t.Fatalf("initializes = %d, want 1 under concurrency", inits)
	}
}

// A stateless backend (postsql / sapb1 v0.56) issues no session id, so the
// gateway must never send the header.
func TestBackendStatelessNeverGetsSessionHeader(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "postsql", stateful: false, tools: []string{"postgres_query"}})
	b := testBackend(f)

	for i := 0; i < 2; i++ {
		if _, _, err := b.callTool(t.Context(), "postgres_query", json.RawMessage(`{"sql":"select 1"}`)); err != nil {
			t.Fatalf("callTool #%d: %v", i, err)
		}
	}
	inits, _, calls := f.stats()
	if inits != 1 {
		t.Fatalf("initializes = %d, want 1 (init is still once, statelessly)", inits)
	}
	for _, c := range calls {
		if c.session != "" {
			t.Fatalf("%s carried %s = %q against a stateless backend", c.method, sessionHeader, c.session)
		}
	}
}

// An expired session is re-initialized and the request retried exactly once.
func TestBackendReInitOnExpiryRetriesOnce(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"a"}})
	b := testBackend(f)

	if _, err := b.listTools(t.Context()); err != nil {
		t.Fatalf("first listTools: %v", err)
	}
	f.expireAll()

	tools, err := b.listTools(t.Context())
	if err != nil {
		t.Fatalf("listTools after expiry: %v", err)
	}
	if len(tools) != 1 {
		t.Fatalf("tools = %v, want 1 after recovery", tools)
	}
	inits, initialized, _ := f.stats()
	if inits != 2 {
		t.Fatalf("initializes = %d, want 2 (one re-init)", inits)
	}
	if initialized != 2 {
		t.Fatalf("notifications/initialized = %d, want 2", initialized)
	}
	// The expired attempt plus the retry, and nothing more.
	if got := len(f.callsOf("tools/list")); got != 3 {
		t.Fatalf("tools/list attempts = %d, want 3 (ok, expired, retry)", got)
	}
	// The retry used the new session, not the dead one.
	attempts := f.callsOf("tools/list")
	if attempts[1].session == attempts[2].session {
		t.Fatalf("retry reused the expired session %q", attempts[2].session)
	}
}

// A second expiry in a row is a hard failure: one retry, never a loop.
func TestBackendDoubleExpiryFails(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, alwaysExpire: true, tools: []string{"a"}})
	b := testBackend(f)

	_, err := b.listTools(t.Context())
	if err == nil {
		t.Fatal("listTools = nil error, want failure")
	}
	if !errors.Is(err, errSessionExpired) {
		t.Fatalf("err = %v, want errSessionExpired", err)
	}
	if inits, _, _ := f.stats(); inits != 2 {
		t.Fatalf("initializes = %d, want exactly 2 (initial + one re-init)", inits)
	}
	if got := len(f.callsOf("tools/list")); got != 2 {
		t.Fatalf("tools/list attempts = %d, want 2", got)
	}
}

// A backend that answers with text/event-stream is parsed the same way, even
// with an unrelated notification interleaved before the answer.
func TestBackendSSEResponse(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "factory", stateful: true, sse: true, sseNoise: true, tools: []string{"orders"}})
	b := testBackend(f)

	tools, err := b.listTools(t.Context())
	if err != nil {
		t.Fatalf("listTools over SSE: %v", err)
	}
	if len(tools) != 1 || string(tools[0]["name"]) != `"orders"` {
		t.Fatalf("tools = %v, want one tool named orders", tools)
	}
	res, rerr, err := b.callTool(t.Context(), "orders", json.RawMessage(`{"limit":5}`))
	if err != nil || rerr != nil {
		t.Fatalf("callTool over SSE: err=%v rpcErr=%v", err, rerr)
	}
	if !strings.Contains(string(res), `"factory:orders"`) {
		t.Fatalf("result = %s, want the fake's text", res)
	}
}

// tools/list pagination: every page is followed and the cursor is echoed back.
func TestBackendToolsListFollowsCursor(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "sapb1", stateful: false, pages: [][]string{
		{"a", "b"}, {"c"}, {"d", "e"},
	}})
	b := testBackend(f)

	tools, err := b.listTools(t.Context())
	if err != nil {
		t.Fatalf("listTools: %v", err)
	}
	var names []string
	for _, tl := range tools {
		names = append(names, strings.Trim(string(tl["name"]), `"`))
	}
	want := []string{"a", "b", "c", "d", "e"}
	if strings.Join(names, ",") != strings.Join(want, ",") {
		t.Fatalf("names = %v, want %v (in page order)", names, want)
	}
	calls := f.callsOf("tools/list")
	if len(calls) != 3 {
		t.Fatalf("tools/list requests = %d, want 3 pages", len(calls))
	}
	if strings.Contains(string(calls[0].params), "cursor") {
		t.Fatalf("first page sent a cursor: %s", calls[0].params)
	}
	for i, c := range calls[1:] {
		if !strings.Contains(string(c.params), fmt.Sprintf(`"cursor":"page-%d"`, i+1)) {
			t.Fatalf("page %d params = %s, want cursor page-%d", i+2, c.params, i+1)
		}
	}
}

// A backend JSON-RPC error is data, not a transport failure: code, message and
// data all survive.
func TestBackendToolErrorIsReturnedNotWrapped(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "oms", stateful: true, toolError: true})
	b := testBackend(f)

	res, rerr, err := b.callTool(t.Context(), "whatever", nil)
	if err != nil {
		t.Fatalf("err = %v, want nil (the backend answered)", err)
	}
	if res != nil {
		t.Fatalf("result = %s, want nil", res)
	}
	if rerr == nil || rerr.Code != -32001 || rerr.Message != "backend says no" {
		t.Fatalf("rpcErr = %+v, want code -32001 message \"backend says no\"", rerr)
	}
	if string(rerr.Data) != `{"detail":"upstream"}` {
		t.Fatalf("rpcErr.Data = %s, want the backend's data verbatim", rerr.Data)
	}
}

// Arguments reach the backend byte-for-byte.
func TestBackendForwardsArgumentsVerbatim(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true})
	b := testBackend(f)

	args := json.RawMessage(`{"z":1,"a":{"nested":[1,2,{"k":"v"}]},"s":"até"}`)
	if _, _, err := b.callTool(t.Context(), "some_tool", args); err != nil {
		t.Fatalf("callTool: %v", err)
	}
	calls := f.callsOf("tools/call")
	if len(calls) != 1 {
		t.Fatalf("tools/call calls = %d, want 1", len(calls))
	}
	var p struct {
		Name      string          `json:"name"`
		Arguments json.RawMessage `json:"arguments"`
	}
	if err := json.Unmarshal(calls[0].params, &p); err != nil {
		t.Fatalf("params: %v", err)
	}
	if p.Name != "some_tool" {
		t.Fatalf("name = %q, want the stripped tool name", p.Name)
	}
	if string(p.Arguments) != string(args) {
		t.Fatalf("arguments = %s, want %s byte-for-byte", p.Arguments, args)
	}
}

// B1. A backend that accepts the connection and then never answers initialize
// must cost each caller only that caller's own deadline. Before the fix the
// initialize POST happened while the session mutex was held (there is no such
// lock any more), so every other caller was parked in an uncancellable Lock for
// up to the full CallTimeout — and because registry.refresh waits on its
// fan-out, one such backend stalled the gateway.
func TestBackendHungInitializeRespectsEachCallersDeadline(t *testing.T) {
	const hang = 600 * time.Millisecond
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, initDelay: hang, tools: []string{"orders"}})
	b := testBackend(f)

	// Caller 1 is patient and becomes the leader of the initialize.
	leaderDone := make(chan error, 1)
	go func() {
		_, err := b.listTools(t.Context())
		leaderDone <- err
	}()

	// Give the leader time to claim the initialize, then arrive with a small
	// budget of our own.
	time.Sleep(50 * time.Millisecond)
	ctx, cancel := context.WithTimeout(t.Context(), 150*time.Millisecond)
	defer cancel()

	began := time.Now()
	_, err := b.listTools(ctx)
	elapsed := time.Since(began)

	if err == nil {
		t.Fatal("second caller succeeded, want its own deadline to expire")
	}
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("second caller err = %v, want a deadline error", err)
	}
	if elapsed > 400*time.Millisecond {
		t.Fatalf("second caller waited %v, want ~150ms (its own budget, not the leader's)", elapsed)
	}

	// The patient caller still gets its answer, and there was only ever one
	// initialize in flight.
	if err := <-leaderDone; err != nil {
		t.Fatalf("leader listTools: %v", err)
	}
	if inits, _, _ := f.stats(); inits != 1 {
		t.Fatalf("initializes = %d, want 1", inits)
	}
}

// B1, other half: a caller whose own context is already dead must not start an
// initialize and hang on it.
func TestBackendEnsureSessionHonoursDeadCallerContext(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, initDelay: 5 * time.Second, tools: []string{"a"}})
	b := testBackend(f)

	ctx, cancel := context.WithCancel(t.Context())
	cancel()
	began := time.Now()
	if _, err := b.listTools(ctx); err == nil {
		t.Fatal("listTools with a cancelled context succeeded, want failure")
	}
	if elapsed := time.Since(began); elapsed > time.Second {
		t.Fatalf("took %v, want an immediate failure", elapsed)
	}
}

// C1. The retry budget must count real backend failures only. A patient caller
// with a multi-second budget, arriving into a storm of impatient callers that
// keep claiming the initialize and then dying on their own short deadlines, must
// still get an initialize of its own and a result.
//
// Before the fix the cap counted *turns* of the wait/takeover loop, so two dead
// leaders exhausted it and the third caller — however much budget it had left —
// was handed a synthetic "session initialization keeps failing" error after zero
// initialize attempts of its own. That error is not a context error, so the
// registry read it as a backend verdict and parked a healthy backend at up=false
// for a full TTL (see TestRegistryRefreshNotPoisonedByOtherCallersCancellations).
//
// The other half of the guarantee: an impatient caller may only ever fail on its
// own deadline. Any non-context error here would mean the gateway invented a
// backend fault out of a cancellation.
func TestBackendPatientCallerSurvivesImpatientStorm(t *testing.T) {
	const (
		initTime   = 300 * time.Millisecond // one initialize takes this long
		impatience = 80 * time.Millisecond  // ... which no impatient caller waits for
		waves      = 8                      // arriving in bursts, so a burst of waiters
		perWave    = 6                      // wakes together and leadership changes hands fast
		waveGap    = 30 * time.Millisecond
	)
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, initDelay: initTime, tools: []string{"orders"}})
	b := testBackend(f)

	list := func(budget time.Duration) ([]map[string]json.RawMessage, error) {
		ctx, cancel := context.WithTimeout(context.Background(), budget)
		defer cancel()
		return b.listTools(ctx)
	}

	// The first wave claims leadership, so the patient caller arrives as a waiter —
	// the shape that used to burn the cap.
	var wg sync.WaitGroup
	impatient := make([]error, waves*perWave)
	for w := 0; w < waves; w++ {
		for i := 0; i < perWave; i++ {
			wg.Add(1)
			go func(n int, w int) {
				defer wg.Done()
				time.Sleep(time.Duration(w) * waveGap)
				_, impatient[n] = list(impatience)
			}(w*perWave+i, w)
		}
	}

	time.Sleep(waveGap / 4) // let the first wave take the lead
	patient := make(chan error, 1)
	go func() {
		tools, err := list(10 * time.Second)
		if err == nil && len(tools) != 1 {
			err = fmt.Errorf("patient caller got %d tools, want 1", len(tools))
		}
		patient <- err
	}()

	if err := <-patient; err != nil {
		t.Fatalf("patient caller: %v, want a session and a result (its budget was never the problem)", err)
	}
	wg.Wait()

	for i, err := range impatient {
		if err == nil {
			continue // arrived after the session existed: fine
		}
		if !errors.Is(err, context.DeadlineExceeded) {
			t.Fatalf("impatient caller %d: err = %v, want only its own deadline", i, err)
		}
	}
	inits, _, calls := f.stats()
	if inits == 0 {
		t.Fatal("initializes = 0: the patient caller never even attempted a handshake")
	}
	// The reworked wait/takeover loop may not invent a method while it is at it:
	// the read-only whitelist holds through the storm as well.
	allowed := map[string]bool{
		"initialize": true, "notifications/initialized": true,
		"tools/list": true, "tools/call": true,
	}
	for _, c := range calls {
		if !allowed[c.method] {
			t.Fatalf("the storm put %q downstream, outside the read-only whitelist", c.method)
		}
	}
}

// S5. A stateful backend that answers initialize without an Mcp-Session-Id then
// 404s everything: the gateway believed it was initialized and never re-inited,
// because it only treated a 404 as expiry when it had sent a header. It must now
// re-init and retry exactly once, then fail loudly instead of staying wedged.
func TestBackendMissingSessionHeaderStillReInitsOnce(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, noSessionHeader: true, tools: []string{"orders"}})
	b := testBackend(f)

	_, err := b.listTools(t.Context())
	if err == nil {
		t.Fatal("listTools = nil error, want failure against a wedged backend")
	}
	if !errors.Is(err, errSessionExpired) {
		t.Fatalf("err = %v, want errSessionExpired", err)
	}
	inits, _, _ := f.stats()
	if inits != 2 {
		t.Fatalf("initializes = %d, want 2 (initial + exactly one re-init)", inits)
	}
	if got := len(f.callsOf("tools/list")); got != 2 {
		t.Fatalf("tools/list attempts = %d, want 2 (first + one retry)", got)
	}
	// Every attempt went out with no session header, because none was ever
	// issued — the gateway must not invent one.
	for _, c := range f.callsOf("tools/list") {
		if c.session != "" {
			t.Fatalf("tools/list carried session %q, want none", c.session)
		}
	}
	// And the error still names what actually happened.
	if !strings.Contains(err.Error(), "404") {
		t.Fatalf("err = %v, want the HTTP status kept for diagnosis", err)
	}
}

// S8. Only 404 is a session expiry (v0.47.0 ground truth). A deterministic 400
// is a real error: treating it as expiry threw away the shared session and
// re-initialized on every single call, forever.
func TestBackendBadRequestIsNotSessionExpiry(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, badRequest: true, tools: []string{"a"}})
	b := testBackend(f)

	for i := 0; i < 3; i++ {
		_, err := b.listTools(t.Context())
		if err == nil {
			t.Fatalf("listTools #%d = nil error, want the backend's 400", i)
		}
		if errors.Is(err, errSessionExpired) {
			t.Fatalf("listTools #%d treated a 400 as a session expiry: %v", i, err)
		}
		if !strings.Contains(err.Error(), "400") {
			t.Fatalf("listTools #%d err = %v, want the 400 reported", i, err)
		}
	}
	if inits, _, _ := f.stats(); inits != 1 {
		t.Fatalf("initializes = %d across 3 failing calls, want exactly 1", inits)
	}
	if got := len(f.callsOf("tools/list")); got != 3 {
		t.Fatalf("tools/list attempts = %d, want 3 (one per call, no retries)", got)
	}
}

// S9. A JSON (non-SSE) response answering a different id must be rejected, the
// same way the SSE path has always rejected one. Otherwise a mismatched answer
// is handed to the client as the answer to a question it never asked.
func TestBackendJSONDecoyIDIsRejected(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "sapb1", decoyID: true, tools: []string{"query"}})
	b := testBackend(f)

	_, err := b.listTools(t.Context())
	if err == nil {
		t.Fatal("listTools accepted a response with the wrong id")
	}
	if !strings.Contains(err.Error(), "does not match request id") {
		t.Fatalf("err = %v, want an id-mismatch error", err)
	}
}

// S4. A backend that keeps handing back the same nextCursor used to be followed
// ten times — duplicating its tools tenfold — and then reported healthy. It must
// now be an error, so the registry keeps the last complete list instead.
func TestBackendRepeatedCursorIsAnError(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "factory", stateful: true, repeatCursor: true, tools: []string{"a", "b"}})
	b := testBackend(f)

	tools, err := b.listTools(t.Context())
	if err == nil {
		t.Fatalf("listTools = %d tools, nil error; want a pagination error", len(tools))
	}
	if tools != nil {
		t.Fatalf("tools = %v, want nothing on a pagination failure", tools)
	}
	if !strings.Contains(err.Error(), "repeated") {
		t.Fatalf("err = %v, want it to name the repeated cursor", err)
	}
	// It stopped the moment it saw the cursor twice, not after ten pages.
	if got := len(f.callsOf("tools/list")); got != 2 {
		t.Fatalf("tools/list requests = %d, want 2 (page, then the repeat)", got)
	}
}

// S4, page cap: pagination that advances but never ends is also an error, not a
// truncated list served as if it were complete.
func TestBackendPageCapIsAnError(t *testing.T) {
	pages := make([][]string, maxToolPages+3)
	for i := range pages {
		pages[i] = []string{fmt.Sprintf("tool%d", i)}
	}
	f := newFakeBackend(t, fakeOpts{name: "factory", pages: pages})
	b := testBackend(f)

	if _, err := b.listTools(t.Context()); err == nil {
		t.Fatal("listTools followed the cap and returned a truncated list, want an error")
	} else if !strings.Contains(err.Error(), "pages") {
		t.Fatalf("err = %v, want it to name the page cap", err)
	}
	if got := len(f.callsOf("tools/list")); got != maxToolPages {
		t.Fatalf("tools/list requests = %d, want the %d-page cap", got, maxToolPages)
	}
}

// A dead backend is a transport error, distinguishable from a JSON-RPC error.
func TestBackendDownIsTransportError(t *testing.T) {
	f := newFakeBackend(t, fakeOpts{name: "dead"})
	url := f.url()
	f.srv.Close()

	b := newBackend(BackendConf{Name: "dead", Prefix: "x_", URL: url}, newHTTPClient(), "test")
	if _, err := b.listTools(t.Context()); err == nil {
		t.Fatal("listTools against a closed server = nil error, want failure")
	}
}

// --- parseSSEBody unit tests --------------------------------------------------

func TestParseSSEBodyPicksOurID(t *testing.T) {
	stream := "event: message\n" +
		"data: {\"jsonrpc\":\"2.0\",\"method\":\"notifications/message\",\"params\":{}}\n\n" +
		"event: message\n" +
		"data: {\"jsonrpc\":\"2.0\",\"id\":41,\"result\":{\"not\":\"ours\"}}\n\n" +
		"id: 7\n" +
		"data: {\"jsonrpc\":\"2.0\",\"id\":42,\"result\":{\"ours\":true}}\n\n"
	res, rerr, err := parseSSEBody(strings.NewReader(stream), 42)
	if err != nil || rerr != nil {
		t.Fatalf("err=%v rpcErr=%v", err, rerr)
	}
	if string(res) != `{"ours":true}` {
		t.Fatalf("result = %s, want the id-42 result", res)
	}
}

func TestParseSSEBodyMultilineData(t *testing.T) {
	stream := "data: {\"jsonrpc\":\"2.0\",\n" +
		"data: \"id\":5,\"result\":{\"a\":1}}\n\n"
	res, _, err := parseSSEBody(strings.NewReader(stream), 5)
	if err != nil {
		t.Fatalf("err = %v", err)
	}
	if string(res) != `{"a":1}` {
		t.Fatalf("result = %s, want {\"a\":1}", res)
	}
}

func TestParseSSEBodyUnterminatedEvent(t *testing.T) {
	res, _, err := parseSSEBody(strings.NewReader(`data: {"jsonrpc":"2.0","id":1,"result":{}}`), 1)
	if err != nil {
		t.Fatalf("err = %v", err)
	}
	if string(res) != `{}` {
		t.Fatalf("result = %s, want {}", res)
	}
}

func TestParseSSEBodyError(t *testing.T) {
	stream := "data: {\"jsonrpc\":\"2.0\",\"id\":3,\"error\":{\"code\":-32000,\"message\":\"nope\"}}\n\n"
	res, rerr, err := parseSSEBody(strings.NewReader(stream), 3)
	if err != nil || res != nil {
		t.Fatalf("err=%v res=%s, want the JSON-RPC error only", err, res)
	}
	if rerr == nil || rerr.Code != -32000 {
		t.Fatalf("rpcErr = %+v, want code -32000", rerr)
	}
}

func TestParseSSEBodyMissingResponse(t *testing.T) {
	stream := "data: {\"jsonrpc\":\"2.0\",\"id\":99,\"result\":{}}\n\n"
	if _, _, err := parseSSEBody(strings.NewReader(stream), 1); err == nil {
		t.Fatal("err = nil, want 'no JSON-RPC response for id 1'")
	}
}

// --- parseJSONBody unit tests -------------------------------------------------

func TestParseJSONBodyChecksID(t *testing.T) {
	cases := []struct {
		name string
		body string
		ok   bool
	}{
		{"ours", `{"jsonrpc":"2.0","id":7,"result":{"a":1}}`, true},
		{"decoy", `{"jsonrpc":"2.0","id":8,"result":{"a":1}}`, false},
		{"string id", `{"jsonrpc":"2.0","id":"7","result":{"a":1}}`, false},
		{"null id", `{"jsonrpc":"2.0","id":null,"result":{"a":1}}`, false},
		{"absent id", `{"jsonrpc":"2.0","result":{"a":1}}`, false},
	}
	for _, c := range cases {
		res, rerr, err := parseJSONBody(strings.NewReader(c.body), 7)
		if c.ok {
			if err != nil || rerr != nil || string(res) != `{"a":1}` {
				t.Fatalf("%s: res=%s rpcErr=%v err=%v, want the result", c.name, res, rerr, err)
			}
			continue
		}
		if err == nil {
			t.Fatalf("%s: err = nil, want an id-mismatch error (res=%s)", c.name, res)
		}
		if !strings.Contains(err.Error(), "does not match request id") {
			t.Fatalf("%s: err = %v, want an id-mismatch error", c.name, err)
		}
	}
}

// An id-matched JSON-RPC error still comes back as an error object, not a
// transport failure.
func TestParseJSONBodyErrorWithMatchingID(t *testing.T) {
	res, rerr, err := parseJSONBody(
		strings.NewReader(`{"jsonrpc":"2.0","id":3,"error":{"code":-32002,"message":"nope"}}`), 3)
	if err != nil || res != nil {
		t.Fatalf("err=%v res=%s, want the JSON-RPC error only", err, res)
	}
	if rerr == nil || rerr.Code != -32002 {
		t.Fatalf("rpcErr = %+v, want code -32002", rerr)
	}
}

func TestIDEquals(t *testing.T) {
	cases := []struct {
		raw  string
		want bool
	}{
		{"42", true}, {" 42 ", true}, {`"42"`, false}, {"41", false}, {"null", false}, {"", false},
	}
	for _, c := range cases {
		if got := idEquals(json.RawMessage(c.raw), 42); got != c.want {
			t.Fatalf("idEquals(%q, 42) = %v, want %v", c.raw, got, c.want)
		}
	}
}

func TestIsEventStream(t *testing.T) {
	for _, ct := range []string{"text/event-stream", "text/event-stream; charset=utf-8", "TEXT/EVENT-STREAM"} {
		if !isEventStream(ct) {
			t.Fatalf("isEventStream(%q) = false, want true", ct)
		}
	}
	for _, ct := range []string{"application/json", "", "text/plain"} {
		if isEventStream(ct) {
			t.Fatalf("isEventStream(%q) = true, want false", ct)
		}
	}
}
