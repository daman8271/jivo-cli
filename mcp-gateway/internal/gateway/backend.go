package gateway

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

const (
	// sessionHeader is mcp-go's session header. v0.47.0 hands it out in the
	// initialize *response* and then requires it on every later request.
	sessionHeader = "Mcp-Session-Id"

	// backendProtocolVersion is what the gateway negotiates upstream. Fixed,
	// independent of what the front-side client asks for.
	backendProtocolVersion = "2025-03-26"

	// clientName identifies the gateway to backends in initialize.
	clientName = "jivo-gateway"

	// backendBodyLimit caps one backend response (32 MiB). A tool that returns
	// more than this is a bug upstream, and buffering it would be worse.
	backendBodyLimit = 32 << 20

	// drainLimit is how much of a finished response body is drained so the
	// keep-alive connection can be reused.
	drainLimit = 4 << 10

	// maxToolPages caps tools/list cursor following (a runaway guard; all five
	// backends answer in one page).
	maxToolPages = 10

	// maxInitFailures is how many REAL initialize failures one caller absorbs
	// before giving up: the attempt plus one retry, the same allowance rpc gives
	// an expired session. Losing a leadership race is deliberately not one of
	// these — see ensureSession.
	maxInitFailures = 2
)

// errSessionExpired means the backend rejected a request because our session is
// gone, so it must be re-initialized. mcp-go v0.47.0 answers an unknown or
// terminated session with a plain-text 404 — not a JSON-RPC error — which is why
// this is a transport-level sentinel. Only 404 means this; a 400 is a real error
// (see expiredBy404 and post).
var errSessionExpired = errors.New("backend session expired")

// backend is one upstream MCP server plus its session state.
//
// Locking: mu guards the session snapshot and the initialize-in-flight
// bookkeeping. It is never held across network I/O — see ensureSession.
type backend struct {
	conf          BackendConf
	hc            *http.Client
	clientVersion string

	// requestURL is conf.URL with any userinfo removed, so no error string can
	// ever quote a password; displayURL is the same URL with the password
	// masked, for gateway_status and the startup log; authUser/authPass carry
	// whatever userinfo was there as basic auth instead.
	requestURL string
	displayURL string
	authUser   string
	authPass   string

	mu sync.Mutex // guards sessionID, inited, initDone, initErr
	// sessionID is empty for stateless backends (sapb1 v0.56 / postsql never
	// issue one); inited records that initialize has succeeded, which is what
	// makes "no session id" different from "not initialized yet".
	sessionID string
	inited    bool
	// initDone is non-nil exactly while one caller (the leader) is running an
	// initialize; initErr is that attempt's outcome, published before the
	// channel closes.
	initDone chan struct{}
	initErr  error

	nextID atomic.Int64 // backend-local JSON-RPC ids; client ids never travel
}

func newBackend(conf BackendConf, hc *http.Client, clientVersion string) *backend {
	request, display, user, pass := splitURL(conf.URL)
	return &backend{
		conf:          conf,
		hc:            hc,
		clientVersion: clientVersion,
		requestURL:    request,
		displayURL:    display,
		authUser:      user,
		authPass:      pass,
	}
}

// newHTTPClient builds the transport shared by every backend. There is no
// client-level Timeout on purpose: each request's deadline comes from its
// context, so a 120s tools/call and a 10s tools/list can share one client.
func newHTTPClient() *http.Client {
	return &http.Client{
		Transport: &http.Transport{
			Proxy:               nil, // never proxy internal service-name URLs
			MaxIdleConns:        32,
			MaxIdleConnsPerHost: 8,
			IdleConnTimeout:     90 * time.Second,
		},
		// Surface a redirect as its 3xx status instead of silently replaying
		// the POST somewhere else.
		CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse },
	}
}

// --- session management -------------------------------------------------------

// session returns a snapshot of the session state.
func (b *backend) session() (sid string, inited bool) {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.sessionID, b.inited
}

// resetSession clears the session, but only if it is still the one the caller
// saw fail (compare-and-swap). Without that check a concurrent request could
// throw away a freshly created good session.
func (b *backend) resetSession(old string) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.sessionID == old {
		b.sessionID = ""
		b.inited = false
	}
}

// ensureSession initializes the backend once, lazily, and never holds a lock
// across network I/O.
//
// The first caller that finds no session becomes the leader: it publishes an
// in-flight channel, drops the lock and does the initialize POST on its own
// context. Every other caller waits on {that channel, its own ctx.Done()}, so a
// backend that accepts TCP and then never answers initialize costs each caller
// only its own deadline. It can no longer park every caller in an uncancellable
// mutex Lock for a full CallTimeout — which, through the registry's refresh
// fan-out, used to stall the whole gateway.
//
// A failed attempt clears the in-flight marker, so the next caller retries.
//
// Two rules keep the wait/takeover loop both terminating and fair:
//
//   - Only a REAL backend failure is charged to maxInitFailures. Losing a
//     leadership race — the leader gave up on the leader's own deadline — is
//     nobody's fault and costs nothing, so a caller is never billed for other
//     callers' impatience. This used to be counted, and two dead leaders were
//     enough to hand a third caller with seconds of budget left a synthetic
//     failure after zero initialize attempts of its own.
//   - Every error whose only cause is cancellation wraps a context error. The
//     registry can then tell "this backend is broken" from "somebody hung up",
//     and no starved caller can mark a healthy backend down for a whole TTL.
//
// Termination: each turn either ends the call (a session, a real failure, or our
// own context) or requires *another* leader to have burned its own deadline in
// the meantime; our context is checked before every turn, so the loop can never
// outlive the caller's budget.
func (b *backend) ensureSession(ctx context.Context) error {
	realFailures := 0 // only actual backend faults count toward the cap
	for {
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("initialize %s: %w", b.conf.Name, err)
		}

		b.mu.Lock()
		if b.inited {
			b.mu.Unlock()
			return nil
		}
		if b.initDone == nil { // nobody is initializing: we lead
			done := make(chan struct{})
			b.initDone = done
			b.mu.Unlock()

			err := b.leadInitialize(ctx, done) // network I/O, no lock held
			switch {
			case err == nil:
				return nil
			case isContextErr(err):
				return err // our own budget ran out; already wraps the ctx error
			case ctx.Err() != nil:
				// A backend error and our deadline in the same breath: report
				// both, with the context error wrapped, so a caller that walked
				// away cannot be read as a verdict on the backend.
				return fmt.Errorf("initialize %s: %w (after %v)", b.conf.Name, ctx.Err(), err)
			}
			realFailures++
			if realFailures >= maxInitFailures {
				return err
			}
			continue // one retry of a real failure, as leader again
		}
		done := b.initDone
		b.mu.Unlock()

		select {
		case <-done: // the leader finished, one way or the other
		case <-ctx.Done():
			return fmt.Errorf("initialize %s: waiting for session: %w", b.conf.Name, ctx.Err())
		}

		b.mu.Lock()
		inited, initErr := b.inited, b.initErr
		b.mu.Unlock()
		if inited {
			return nil
		}
		if initErr != nil && !isContextErr(initErr) {
			// A real backend fault: ours too. Charge it and allow the same one
			// retry we would have had as the leader.
			realFailures++
			if realFailures >= maxInitFailures {
				return initErr
			}
		}
		// Otherwise the leader ran out of *its* budget (or the session was reset
		// again) while ours is still intact: take another turn, leading if we can.
	}
}

// leadInitialize runs one initialize as the leader and publishes its outcome to
// the waiters.
//
// The bookkeeping is deferred on purpose: if initialize ever panics (or a test's
// runtime.Goexit unwinds through it), clearing initDone inline would be skipped
// and this backend would stay claimed forever — every later caller waiting on a
// channel nobody closes, for the life of the process.
func (b *backend) leadInitialize(ctx context.Context, done chan struct{}) (err error) {
	defer func() {
		b.mu.Lock()
		b.initErr = err
		b.initDone = nil // cleared on failure too, so the next caller retries
		b.mu.Unlock()
		close(done)
	}()
	return b.initialize(ctx)
}

// isContextErr reports whether err came from a deadline or a cancellation
// rather than from the backend.
func isContextErr(err error) bool {
	return errors.Is(err, context.DeadlineExceeded) || errors.Is(err, context.Canceled)
}

// initialize performs the MCP handshake: initialize (with no session header,
// because we do not have one yet), remember any Mcp-Session-Id the backend
// hands back, then notifications/initialized fire-and-forget.
func (b *backend) initialize(ctx context.Context) error {
	params := map[string]any{
		"protocolVersion": backendProtocolVersion,
		"capabilities":    map[string]any{},
		"clientInfo":      map[string]any{"name": clientName, "version": b.clientVersion},
	}
	out, err := b.post(ctx, "initialize", params, "")
	if err != nil {
		return fmt.Errorf("initialize %s: %w", b.conf.Name, err)
	}
	if out.rpcErr != nil {
		return fmt.Errorf("initialize %s: %s (code %d)", b.conf.Name, out.rpcErr.Message, out.rpcErr.Code)
	}

	b.mu.Lock()
	b.sessionID = out.sessionID
	b.inited = true
	b.mu.Unlock()

	// v0.47.0 does not enforce this notification and stateless backends ignore
	// it; send it for spec correctness and never fail the handshake over it.
	_, _ = b.post(ctx, "notifications/initialized", nil, out.sessionID)
	return nil
}

// --- request path -------------------------------------------------------------

// postResult is one backend response: its JSON-RPC payload plus the session id
// the backend advertised (only initialize cares about the latter).
type postResult struct {
	result    json.RawMessage
	rpcErr    *rpcError
	sessionID string
}

// rpc round-trips one JSON-RPC method to the backend, initializing first if
// needed and re-initializing exactly once if the session turned out to be
// expired. Every method the gateway sends is a read, so replaying one is safe.
//
// The three returns are (result, backend JSON-RPC error, transport error):
// a JSON-RPC error is the backend answering, and is forwarded to the client
// verbatim; a transport error means we could not get an answer at all.
func (b *backend) rpc(ctx context.Context, method string, params any) (json.RawMessage, *rpcError, error) {
	if err := b.ensureSession(ctx); err != nil {
		return nil, nil, err
	}
	sid, _ := b.session()

	out, err := b.post(ctx, method, params, sid)
	if errors.Is(err, errSessionExpired) {
		b.resetSession(sid)
		if err := b.ensureSession(ctx); err != nil {
			return nil, nil, err
		}
		retrySID, _ := b.session()
		out, err = b.post(ctx, method, params, retrySID)
		if err != nil {
			return nil, nil, fmt.Errorf("%s %s: %w", b.conf.Name, method, err)
		}
	}
	if err != nil {
		return nil, nil, fmt.Errorf("%s %s: %w", b.conf.Name, method, err)
	}
	return out.result, out.rpcErr, nil
}

// post performs exactly one POST, with no retry. sid is echoed as the session
// header when non-empty. Methods starting with notifications/ are sent without
// an id and expect 202.
func (b *backend) post(ctx context.Context, method string, params any, sid string) (postResult, error) {
	notification := strings.HasPrefix(method, "notifications/")

	msg := map[string]any{"jsonrpc": "2.0", "method": method}
	var wantID int64
	if !notification {
		wantID = b.nextID.Add(1)
		msg["id"] = wantID
	}
	if params != nil {
		msg["params"] = params
	}
	body, err := json.Marshal(msg)
	if err != nil {
		return postResult{}, fmt.Errorf("marshal %s: %w", method, err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, b.requestURL, bytes.NewReader(body))
	if err != nil {
		return postResult{}, err
	}
	// v0.47.0 hard-rejects a POST without application/json, and may answer
	// either JSON or SSE — so ask for both.
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	if sid != "" {
		req.Header.Set(sessionHeader, sid)
	}
	// Userinfo from the configured URL travels as a header, never in the URL,
	// so it cannot end up in an *url.Error.
	if b.authUser != "" || b.authPass != "" {
		req.SetBasicAuth(b.authUser, b.authPass)
	}

	resp, err := b.hc.Do(req)
	if err != nil {
		return postResult{}, err
	}
	defer func() {
		io.Copy(io.Discard, io.LimitReader(resp.Body, drainLimit))
		resp.Body.Close()
	}()

	out := postResult{sessionID: resp.Header.Get(sessionHeader)}

	switch {
	case resp.StatusCode == http.StatusAccepted:
		return out, nil // notification accepted; there is no message to read
	case resp.StatusCode == http.StatusNotFound && b.expiredBy404(method, sid):
		// v0.47.0 answers an unknown or terminated session with a plain-text
		// 404. Keep the status text: after the one retry this is what the
		// operator sees, and "HTTP 404: 404 page not found" versus "Invalid
		// session ID" is the difference between a wrong URL and a dead session.
		return out, fmt.Errorf("HTTP %s: %s: %w", resp.Status, firstLine(resp.Body), errSessionExpired)
	case resp.StatusCode < 200 || resp.StatusCode > 299:
		// Everything else, 400 included, is a real error. A deterministic 400
		// (bad Content-Type, malformed params) treated as an expiry would throw
		// away the shared session on every single call and re-initialize
		// forever without ever succeeding.
		return out, fmt.Errorf("HTTP %s: %s", resp.Status, firstLine(resp.Body))
	}

	if notification {
		return out, nil // 200 for a notification: nothing to parse
	}

	if isEventStream(resp.Header.Get("Content-Type")) {
		out.result, out.rpcErr, err = parseSSEBody(resp.Body, wantID)
	} else {
		out.result, out.rpcErr, err = parseJSONBody(resp.Body, wantID)
	}
	if err != nil {
		return out, err
	}
	return out, nil
}

// expiredBy404 reports whether a 404 means "your session is gone" rather than
// "no such endpoint".
//
// The obvious case is a request that carried a session header. The other one is
// a request that carried none on a backend we believe is initialized: a stateful
// backend that answered initialize without an Mcp-Session-Id (proxy stripped
// it, restart mid-handshake) then 404s every following request, and without this
// the backend would stay wedged in that state until the process restarted.
// initialize itself is never an expiry — that would be a re-init loop.
func (b *backend) expiredBy404(method, sid string) bool {
	if method == "initialize" {
		return false
	}
	if sid != "" {
		return true
	}
	_, inited := b.session()
	return inited
}

// listTools reads the backend's whole tool list, following nextCursor. Tools
// stay as raw member maps so annotations / outputSchema / anything else the
// backend sends survives untouched.
// A backend that never terminates its pagination is a failed refresh, not a
// partial one: returning what we managed to read would advertise a tool list
// that is a multiple of the truth, and would report the backend healthy while
// doing it. Failing lets the registry keep the last complete list instead.
func (b *backend) listTools(ctx context.Context) ([]map[string]json.RawMessage, error) {
	var (
		out    []map[string]json.RawMessage
		cursor string
		seen   = map[string]bool{} // cursors already followed
	)
	for page := 0; page < maxToolPages; page++ {
		params := map[string]any{}
		if cursor != "" {
			params["cursor"] = cursor
		}
		res, rerr, err := b.rpc(ctx, "tools/list", params)
		if err != nil {
			return nil, err
		}
		if rerr != nil {
			return nil, fmt.Errorf("%s tools/list: %s (code %d)", b.conf.Name, rerr.Message, rerr.Code)
		}
		var payload struct {
			Tools      []map[string]json.RawMessage `json:"tools"`
			NextCursor string                       `json:"nextCursor"`
		}
		if err := json.Unmarshal(res, &payload); err != nil {
			return nil, fmt.Errorf("%s tools/list: bad result: %w", b.conf.Name, err)
		}
		out = append(out, payload.Tools...)
		if payload.NextCursor == "" {
			return out, nil
		}
		if seen[payload.NextCursor] {
			return nil, fmt.Errorf("%s tools/list: pagination cursor %q repeated (backend is looping)",
				b.conf.Name, payload.NextCursor)
		}
		seen[payload.NextCursor] = true
		cursor = payload.NextCursor
	}
	return nil, fmt.Errorf("%s tools/list: more than %d pages of tools (pagination does not terminate)",
		b.conf.Name, maxToolPages)
}

// callTool forwards one tools/call. args travel byte-for-byte as the client
// sent them.
func (b *backend) callTool(ctx context.Context, name string, args json.RawMessage) (json.RawMessage, *rpcError, error) {
	params := map[string]any{"name": name}
	if len(args) > 0 {
		params["arguments"] = args
	}
	return b.rpc(ctx, "tools/call", params)
}

// --- response parsing ---------------------------------------------------------

// isEventStream reports whether a Content-Type is SSE.
func isEventStream(ct string) bool {
	return strings.Contains(strings.ToLower(ct), "text/event-stream")
}

// parseJSONBody reads a single JSON-RPC response object and checks that it
// answers request wantID. The id check is not pedantry: without it a backend
// (or something in between) answering the wrong request would have its result
// handed to the client as the answer to a question it never asked. The SSE path
// has always matched on the id; this is the same rule for the JSON path.
func parseJSONBody(r io.Reader, wantID int64) (json.RawMessage, *rpcError, error) {
	body, err := readCapped(r)
	if err != nil {
		return nil, nil, err
	}
	var msg rpcResponse
	if err := json.Unmarshal(body, &msg); err != nil {
		return nil, nil, fmt.Errorf("bad JSON-RPC response: %w", err)
	}
	if !idEquals(msg.ID, wantID) {
		return nil, nil, fmt.Errorf("JSON-RPC response id %s does not match request id %d",
			idText(msg.ID), wantID)
	}
	if msg.Error != nil {
		return nil, msg.Error, nil
	}
	if msg.Result == nil {
		return nil, nil, errors.New("JSON-RPC response has neither result nor error")
	}
	return msg.Result, nil, nil
}

// parseSSEBody scans an SSE body for the JSON-RPC response with id wantID.
// mcp-go may upgrade a POST response to text/event-stream and interleave
// notifications (progress, logging) with the actual answer, so anything that is
// not our id is skipped. Pure and directly unit-tested.
func parseSSEBody(r io.Reader, wantID int64) (json.RawMessage, *rpcError, error) {
	limited := &io.LimitedReader{R: r, N: backendBodyLimit + 1}
	sc := bufio.NewScanner(limited)
	sc.Buffer(make([]byte, 0, 64<<10), backendBodyLimit)

	var data []string
	for sc.Scan() {
		line := sc.Text()
		switch {
		case strings.HasPrefix(line, "data:"):
			data = append(data, strings.TrimPrefix(strings.TrimPrefix(line, "data:"), " "))
		case strings.TrimSpace(line) == "": // end of event
			res, rerr, matched, err := matchSSEEvent(data, wantID)
			if matched || err != nil {
				return res, rerr, err
			}
			data = data[:0]
		default:
			// event:, id:, retry:, comments — irrelevant here.
		}
	}
	if err := sc.Err(); err != nil {
		return nil, nil, fmt.Errorf("reading SSE response: %w", err)
	}
	// A stream may end without a trailing blank line.
	if res, rerr, matched, err := matchSSEEvent(data, wantID); matched || err != nil {
		return res, rerr, err
	}
	if limited.N <= 0 {
		return nil, nil, fmt.Errorf("SSE response exceeds %d bytes", backendBodyLimit)
	}
	return nil, nil, fmt.Errorf("no JSON-RPC response for id %d in SSE stream", wantID)
}

// matchSSEEvent decodes one event's data lines and reports whether it is the
// response we are waiting for. Unparseable or unrelated events are not errors:
// they are simply not ours.
func matchSSEEvent(data []string, wantID int64) (json.RawMessage, *rpcError, bool, error) {
	if len(data) == 0 {
		return nil, nil, false, nil
	}
	var msg rpcResponse
	if err := json.Unmarshal([]byte(strings.Join(data, "\n")), &msg); err != nil {
		return nil, nil, false, nil
	}
	if !idEquals(msg.ID, wantID) {
		return nil, nil, false, nil
	}
	if msg.Error != nil {
		return nil, msg.Error, true, nil
	}
	if msg.Result == nil {
		return nil, nil, true, errors.New("JSON-RPC response has neither result nor error")
	}
	return msg.Result, nil, true, nil
}

// idEquals reports whether a raw JSON-RPC id is the integer want. The gateway
// only ever sends integer ids, so a non-numeric id is never ours.
func idEquals(raw json.RawMessage, want int64) bool {
	s := strings.TrimSpace(string(raw))
	if s == "" {
		return false
	}
	got, err := strconv.ParseInt(s, 10, 64)
	return err == nil && got == want
}

// idText renders a raw id for an error message, without letting a huge or
// binary "id" into the log line.
func idText(raw json.RawMessage) string {
	s := strings.TrimSpace(string(raw))
	if s == "" {
		return "(absent)"
	}
	if len(s) > 32 {
		return s[:32] + "…"
	}
	return s
}

// readCapped reads at most backendBodyLimit bytes, erroring if there is more.
func readCapped(r io.Reader) ([]byte, error) {
	body, err := io.ReadAll(io.LimitReader(r, backendBodyLimit+1))
	if err != nil {
		return nil, err
	}
	if len(body) > backendBodyLimit {
		return nil, fmt.Errorf("response exceeds %d bytes", backendBodyLimit)
	}
	return body, nil
}

// firstLine is the first line of an error body (mcp-go answers plain text),
// trimmed for a one-line error message.
func firstLine(r io.Reader) string {
	body, err := io.ReadAll(io.LimitReader(r, 512))
	if err != nil || len(body) == 0 {
		return "no body"
	}
	line := strings.TrimSpace(string(body))
	if i := strings.IndexAny(line, "\r\n"); i >= 0 {
		line = line[:i]
	}
	return line
}
