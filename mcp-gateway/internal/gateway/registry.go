package gateway

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"
)

// BackendStatus is one backend's health, as reported by gateway_status and by
// the startup log.
type BackendStatus struct {
	Name        string    `json:"name"`
	Prefix      string    `json:"prefix"`
	URL         string    `json:"url"` // display form: never carries a password
	Up          bool      `json:"up"`
	ToolCount   int       `json:"tool_count"` // tools actually advertised from this backend
	LastRefresh time.Time `json:"last_refresh,omitzero"`
	LastError   string    `json:"last_error,omitempty"`
}

// registry owns the backends and the merged tool list.
//
// Three deliberate properties:
//
//   - Stale-while-down. A backend that fails a refresh keeps its last known
//     tools. A backend restart (or a 10s blip) must not churn the tool list a
//     client like claude.ai has already cached.
//   - Routing never depends on the cache. resolve() answers from the static
//     prefix table, so a stale or empty cache can never mis-route or block a
//     tools/call.
//   - A refresh is never charged to one client's request. The fan-out runs on a
//     context detached from whoever triggered it, bounded only by the
//     per-backend budget, so a client that disconnects mid-refresh cannot mark
//     every backend down for a whole TTL.
type registry struct {
	backends    []*backend
	ttl         time.Duration
	listTimeout time.Duration

	mu          sync.Mutex
	refreshDone chan struct{}        // non-nil exactly while a refresh is in flight
	tools       []json.RawMessage    // merged + prefixed + deduped, backend order
	perBackend  map[string][]toolDef // last known tools per backend
	status      map[string]BackendStatus
	lastRefresh time.Time
}

// toolDef is one advertised tool: its final (prefixed) name plus the definition
// bytes exactly as they will be handed to the client. Carrying the name avoids
// re-parsing the definition on every merge, and is what makes the duplicate
// check cheap.
type toolDef struct {
	name string
	raw  json.RawMessage
}

func newRegistry(cfg Config, version string) *registry {
	hc := newHTTPClient() // one transport, shared by all backends
	r := &registry{
		ttl:         cfg.ToolsTTL,
		listTimeout: cfg.ListTimeout,
		perBackend:  map[string][]toolDef{},
		status:      map[string]BackendStatus{},
	}
	for _, conf := range cfg.Backends {
		b := newBackend(conf, hc, version)
		r.backends = append(r.backends, b)
		r.status[conf.Name] = BackendStatus{Name: conf.Name, Prefix: conf.Prefix, URL: b.displayURL}
	}
	return r
}

// toolsList returns the merged, prefixed tool list, refreshing first if the
// cache is stale. If a refresh is already in flight the caller gets the current
// snapshot immediately rather than queueing behind five network round-trips.
//
// The one exception is a cold start: before the first refresh has ever completed
// there is no snapshot, only an empty list, and answering a client "this gateway
// has no tools" is worse than making it wait. So while the first-ever refresh is
// in flight, other callers wait for it (bounded by their own context and the list
// budget) instead of being served nothing. After that, stale-while-refresh is
// exactly the point.
func (r *registry) toolsList(ctx context.Context) []json.RawMessage {
	r.mu.Lock()
	never := r.lastRefresh.IsZero()
	stale := never || time.Since(r.lastRefresh) > r.ttl
	inFlight := r.refreshDone
	tools := r.tools
	r.mu.Unlock()

	if !stale {
		return tools
	}
	if inFlight != nil {
		if !never {
			return tools // stale-while-refresh: serve the last known list
		}
		waitForRefresh(ctx, inFlight, r.listTimeout)
		return r.cachedTools()
	}

	r.refresh(ctx)
	return r.cachedTools()
}

// cachedTools returns the merged list as it stands, without refreshing.
func (r *registry) cachedTools() []json.RawMessage {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.tools
}

// resolve maps a prefixed tool name to its backend and the name to send
// upstream. Prefix table only — never the cached list.
//
// The upstream name is the exact inverse of what refresh advertised: the
// gateway prefix comes off and the backend's own redundant prefix goes back on,
// so sap_query is forwarded to sapb1 as sapb1_query.
func (r *registry) resolve(name string) (*backend, string, bool) {
	for _, b := range r.backends {
		p := b.conf.Prefix
		if len(name) > len(p) && name[:len(p)] == p {
			return b, b.conf.StripPrefix + name[len(p):], true
		}
	}
	return nil, "", false
}

// refresh re-lists every backend and rebuilds the merged list, with the standard
// per-backend list budget.
func (r *registry) refresh(ctx context.Context) {
	r.refreshWithin(ctx, r.listTimeout)
}

// refreshWithin re-lists every backend in parallel, giving each one budget, and
// rebuilds the merged list. Failures are recorded, never fatal, and never drop a
// backend's last known tools.
//
// ctx is used for its values only: the fan-out runs on a context detached from
// it, because a refresh mutates state shared by every client. When the caller
// that triggered the refresh walks away, the work must still finish correctly —
// otherwise one client disconnecting after 50ms would mark all five backends
// down (ctx.Canceled) for a full TTL, for everybody.
//
// Single-flight: a caller that finds a refresh already in flight waits for that
// one instead of starting a second, bounded by budget and by its own context.
// Only the *waiter* honours ctx; the leader stays detached, because the work it
// is doing belongs to everybody.
func (r *registry) refreshWithin(ctx context.Context, budget time.Duration) {
	done, leader := r.beginRefresh()
	if !leader {
		waitForRefresh(ctx, done, budget)
		return
	}
	defer r.endRefresh(done)

	parent := context.WithoutCancel(ctx)
	outcomes := make([]outcome, len(r.backends))

	var wg sync.WaitGroup
	for i, b := range r.backends {
		wg.Add(1)
		go func(i int, b *backend) {
			defer wg.Done()
			bctx, cancel := context.WithTimeout(parent, budget)
			defer cancel()

			out := outcome{name: b.conf.Name}
			raw, err := b.listTools(bctx)
			if err != nil {
				out.err = err
				outcomes[i] = out
				return
			}
			// One malformed definition is not a broken backend: skip it, keep
			// the other seventy-three, and say so in the status.
			var bad []string
			for j, tool := range raw {
				def, err := renameTool(tool, b.conf.StripPrefix, b.conf.Prefix)
				if err != nil {
					bad = append(bad, fmt.Sprintf("#%d (%v)", j, err))
					continue
				}
				out.tools = append(out.tools, def)
			}
			if len(bad) > 0 {
				out.notes = append(out.notes, fmt.Sprintf("skipped %d malformed tool definition(s): %s",
					len(bad), strings.Join(bad, ", ")))
			}
			outcomes[i] = out
		}(i, b)
	}
	wg.Wait()

	// Logging happens outside the critical section: stderr is not something to
	// block the whole registry on.
	for _, note := range r.apply(outcomes) {
		logf("%s", note)
	}
}

// outcome is one backend's refresh result.
type outcome struct {
	name  string
	tools []toolDef
	notes []string // non-fatal anomalies, surfaced in LastError
	err   error
}

// apply folds a completed fan-out into the registry: per-backend health, the
// per-backend tool lists and the merged list. It returns the anomalies worth
// logging.
func (r *registry) apply(outcomes []outcome) []string {
	now := time.Now()
	r.mu.Lock()
	defer r.mu.Unlock()

	var loggable []string
	notes := map[string]string{} // per backend, this refresh's non-duplicate notes
	for _, out := range outcomes {
		st := r.status[out.name]

		switch {
		case out.err != nil && errors.Is(out.err, context.Canceled) && !errors.Is(out.err, context.DeadlineExceeded):
			// Not reachable from a detached parent, and that is the point: only
			// a real backend failure may mark a backend down. A bare
			// cancellation can only come from outside the backend, so it is not
			// allowed to change anybody's health.
			continue
		case out.err != nil:
			st.Up = false
			notes[out.name] = out.err.Error()
		case len(out.tools) == 0 && len(r.perBackend[out.name]) > 0:
			// The backend answered, healthily, with nothing. That is far more
			// likely to be a half-booted backend than a real un-registration,
			// so keep the last known list rather than making every one of its
			// tools vanish from the client's list.
			st.Up = true
			notes[out.name] = joinNotes(append(out.notes,
				"backend returned empty tool list; serving last-known")...)
		default:
			st.Up = true
			notes[out.name] = joinNotes(out.notes...)
			r.perBackend[out.name] = out.tools // only a real answer replaces tools
		}
		st.LastRefresh = now
		st.LastError = notes[out.name]
		r.status[out.name] = st
		for _, n := range out.notes {
			loggable = append(loggable, "backend "+out.name+": "+n)
		}
	}
	// The merge is what decides how many tools each backend really contributes,
	// so tool counts and duplicate notes are written from there.
	for name, dup := range r.rebuildLocked() {
		loggable = append(loggable, "backend "+name+": "+dup)
		note, stamped := notes[name]
		if !stamped {
			continue // this backend's status was left alone; leave its error too
		}
		st := r.status[name]
		st.LastError = joinNotes(note, dup)
		r.status[name] = st
	}
	r.lastRefresh = now
	return loggable
}

// beginRefresh claims the single-flight slot. The second return reports whether
// the caller is the one that must do the work; either way the channel closes
// when the in-flight refresh finishes.
func (r *registry) beginRefresh() (chan struct{}, bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.refreshDone != nil {
		return r.refreshDone, false
	}
	r.refreshDone = make(chan struct{})
	return r.refreshDone, true
}

// waitForRefresh waits for an in-flight refresh, for at most budget, and gives up
// the moment the caller's context does. A request that has been abandoned must
// not keep a goroutine parked for the full budget on behalf of nobody.
func waitForRefresh(ctx context.Context, done chan struct{}, budget time.Duration) {
	timer := time.NewTimer(budget)
	defer timer.Stop()
	select {
	case <-done:
	case <-timer.C:
	case <-ctx.Done():
	}
}

// endRefresh releases the single-flight slot and wakes the waiters.
func (r *registry) endRefresh(done chan struct{}) {
	r.mu.Lock()
	r.refreshDone = nil
	r.mu.Unlock()
	close(done)
}

// rebuildLocked recomputes the merged list in configured backend order, so the
// tool order a client sees is stable across refreshes. It always allocates a
// fresh slice, which is what makes handing r.tools out without copying safe.
//
// It is also where duplicate names are resolved. Two tools with the same
// advertised name is a protocol violation that makes a client's tool list
// ambiguous, and a gateway that merges five independent backends is exactly
// where it can happen (a backend paginating badly, or two tools colliding after
// a StripPrefix). First one in configured order wins; the rest are dropped,
// logged, and reported in that backend's last_error.
//
// It returns, per backend that lost tools, the note describing what it lost.
// ToolCount is written here too, because the merge is the only place that knows
// how many of a backend's tools are actually advertised.
func (r *registry) rebuildLocked() map[string]string {
	total := 0
	for _, b := range r.backends {
		total += len(r.perBackend[b.conf.Name])
	}
	merged := make([]json.RawMessage, 0, total)
	seen := make(map[string]string, total) // tool name -> backend that owns it
	dupNotes := map[string]string{}

	for _, b := range r.backends {
		name := b.conf.Name
		var dropped []string
		kept := 0
		for _, def := range r.perBackend[name] {
			if owner, dup := seen[def.name]; dup {
				dropped = append(dropped, fmt.Sprintf("%s (already from %s)", def.name, owner))
				continue
			}
			seen[def.name] = name
			merged = append(merged, def.raw)
			kept++
		}
		st := r.status[name]
		st.ToolCount = kept
		r.status[name] = st
		if len(dropped) > 0 {
			dupNotes[name] = fmt.Sprintf("dropped %d duplicate tool name(s): %s",
				len(dropped), strings.Join(dropped, ", "))
		}
	}
	r.tools = merged
	return dupNotes
}

// snapshot returns per-backend status in configured order.
func (r *registry) snapshot() []BackendStatus {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]BackendStatus, 0, len(r.backends))
	for _, b := range r.backends {
		out = append(out, r.status[b.conf.Name])
	}
	return out
}

// lastRefreshedAt is when the merged list was last rebuilt (zero if never).
func (r *registry) lastRefreshedAt() time.Time {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.lastRefresh
}

// renameTool rewrites a tool definition's name to prefix + name-without-strip
// and re-marshals it. Only "name" is touched: description, inputSchema,
// outputSchema, annotations and anything else the backend invented survive
// verbatim.
func renameTool(tool map[string]json.RawMessage, strip, prefix string) (toolDef, error) {
	rawName, ok := tool["name"]
	if !ok {
		return toolDef{}, errors.New("tool definition has no name")
	}
	var name string
	if err := json.Unmarshal(rawName, &name); err != nil {
		return toolDef{}, fmt.Errorf("tool name is not a string: %w", err)
	}
	if name == "" {
		return toolDef{}, errors.New("tool definition has an empty name")
	}
	final := prefix + strings.TrimPrefix(name, strip)
	if final == prefix {
		return toolDef{}, fmt.Errorf("tool name %q is nothing but the stripped prefix %q", name, strip)
	}
	renamed, err := json.Marshal(final)
	if err != nil {
		return toolDef{}, err
	}
	// tool was freshly decoded for this refresh, so mutating it is local.
	tool["name"] = renamed
	raw, err := json.Marshal(tool)
	if err != nil {
		return toolDef{}, err
	}
	return toolDef{name: final, raw: raw}, nil
}

// joinNotes joins the non-empty notes that make up a LastError.
func joinNotes(notes ...string) string {
	out := make([]string, 0, len(notes))
	for _, n := range notes {
		if n != "" {
			out = append(out, n)
		}
	}
	return strings.Join(out, "; ")
}

// logf reports a non-fatal anomaly on stderr, in the same shape as main.go's
// startup lines. Used only for refresh anomalies that are also visible in
// gateway_status, so nothing here is on a hot path.
func logf(format string, a ...any) {
	fmt.Fprintf(os.Stderr, "jivo-gateway: "+format+"\n", a...)
}
