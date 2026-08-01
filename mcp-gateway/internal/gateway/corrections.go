package gateway

import (
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"strings"
	"sync"
	"time"
	"unicode/utf8"
)

// The JIVO corrections digest — the team's settled truths about how this
// business's data actually works, recorded by operators who checked against
// live data (harness/corrections/C-*.md, rolled up by harness/bin/harness.py
// into harness/corrections/INDEX.md).
//
// Local CLI sessions get this injected automatically. A client talking to the
// gateway got nothing, which is not a cosmetic gap: asked for "olive oil sales
// last month" a phone answered by matching item NAMES, the exact thing
// correction C-0003 forbids, and under-reported a company by crores because
// SAP-tagged items have no "olive" in their name.
//
// It is delivered on `instructions` in the initialize result because that is
// the only initialize field clients contractually put in front of the model.
// Extra fields are ignored, and resources/tools are opt-in by the model — which
// is precisely the failure mode measured above.
//
// embeddedDigest is the checked-in snapshot: the seed before any file is read
// and the last-known-good floor if none ever is. It has to be a copy rather
// than the repo file itself because go:embed cannot cross the module boundary
// into ../../../harness; TestEmbeddedDigestSnapshotMatchesRepo is the drift
// guard that keeps the copy honest.
//
//go:embed assets/corrections.md
var embeddedDigest []byte

const (
	// correctionsByteCap bounds what the gateway will serve. It is >10x the
	// digest generator's default budget (harness.py's DIGEST_CHAR_BUDGET, 6,000
	// characters, which that generator itself refuses to exceed), so no
	// legitimate digest is ever near it, and small enough that it can never
	// bloat a handshake or the system prompt it lands in.
	//
	// Over the cap the file is REJECTED WHOLE, never truncated: a silently
	// shortened rules list still reads as authoritative while missing law, and
	// an operator would have no way to tell. Serving the last known good set
	// and shouting in gateway_status is the safe failure.
	//
	// THE ">10x" IS NOT A GUARANTEE. harness.py reads DIGEST_CHAR_BUDGET from
	// JIVO_DIGEST_BUDGET, so an operator who raises it past ~64 KB gets a digest
	// this gateway rejects whole — and because the failure is a rejection, their
	// `jivo-correct` push would appear to succeed on the CLI while every client
	// silently kept the OLDER rules, with only gateway_status's last_error to
	// say so. If that ever needs to happen, raise this cap in the same change;
	// do not raise the generator's budget alone. 64 KiB is roughly ten times
	// every correction JIVO has ever recorded, so it should not come up.
	correctionsByteCap = 64 << 10

	// correctionsRecheck is how stale a loaded digest may get before the next
	// initialize re-reads the file. Read-once was rejected: nobody restarts the
	// container after pushing a correction, so the rules would lag until the
	// next redeploy — the same gap this feature exists to close. One minute
	// puts a pushed correction on a phone by its next connection, at the cost
	// of at most one small local file read per minute on the initialize path.
	correctionsRecheck = 1 * time.Minute

	// correctionsReadBudget is how long a caller — an initialize, a
	// gateway_status — waits for the digest file before giving up and serving
	// the last known good set.
	//
	// The read used to run INLINE, under the same mutex every other caller
	// needs, with no deadline. Any path whose open or read blocks (a FIFO with
	// no writer, a stale NFS or bind mount, a device node) therefore wedged
	// initialize forever AND took gateway_status down behind the same mutex —
	// silently, with /healthz still green. That is the opposite of the trade
	// Config.CorrectionsPath documents: the startup path was made forgiving and
	// the runtime path was not. The read now runs off the mutex, on its own
	// goroutine, and this is the waiter's patience.
	correctionsReadBudget = 2 * time.Second
)

// correctionsView is one immutable snapshot of what the gateway is serving:
// the digest text plus the telemetry gateway_status reports about it.
type correctionsView struct {
	Text   string
	Count  int
	Source string // "file" once a file has ever loaded, else "embedded"
	Path   string // set only when Text came from a file
	Bytes  int
	SHA256 string // hex sha256 of the served bytes — the honest freshness signal
	// LoadedAt moves only when the CONTENT moves; CheckedAt moves on every
	// re-read. See adopt() for why the two are not the same field.
	LoadedAt  time.Time
	CheckedAt time.Time
	LastError string // non-empty: the last re-read failed, this is the last good set
}

// correctionsSource serves the digest, re-reading the configured file at most
// once per correctionsRecheck. It holds no gateway state and issues no business
// -system call — the whole feature is one local file read.
//
// The read is SINGLE-FLIGHT and happens off the mutex: reloading is held for the
// duration of one re-read, so a hundred concurrent initializes produce one file
// read and ninety-nine immediate answers from the current view. A read that
// never finishes therefore costs exactly one parked goroutine, not one per
// minute forever — which is the whole reason the flag exists rather than a
// simple "read it and hope".
type correctionsSource struct {
	mu        sync.Mutex
	path      string
	view      correctionsView
	checkedAt time.Time
	reloading bool
	now       func() time.Time // injectable so the TTL is testable without sleeping
	// read is the file reader, injectable so a test can hold a read open
	// without needing a FIFO. Production always uses readDigest.
	read func(path string) ([]byte, error)
}

// newCorrectionsSource seeds the source with the embedded snapshot, so a
// gateway with no --corrections configured (or one whose mount has not appeared
// yet) still serves a real rule set from its first initialize on.
func newCorrectionsSource(path string, now func() time.Time) *correctionsSource {
	if now == nil {
		now = time.Now
	}
	text := string(embeddedDigest)
	sum := sha256.Sum256(embeddedDigest)
	return &correctionsSource{
		path: strings.TrimSpace(path),
		now:  now,
		read: func(p string) ([]byte, error) { return readDigest(p, correctionsByteCap) },
		view: correctionsView{
			Text:      text,
			Count:     countCorrections(text),
			Source:    "embedded",
			Bytes:     len(embeddedDigest),
			SHA256:    hex.EncodeToString(sum[:]),
			LoadedAt:  now(),
			CheckedAt: now(),
		},
	}
}

// current returns the digest to serve, re-reading the file first if the last
// check is older than correctionsRecheck.
//
// The re-read is bounded: past correctionsReadBudget this stops waiting and
// answers from the last known good view. It never blocks on I/O while holding
// the mutex, so one bad mount cannot wedge every other caller.
func (c *correctionsSource) current() correctionsView {
	done := c.beginReload()
	if done == nil {
		return c.snapshot()
	}
	timer := time.NewTimer(correctionsReadBudget)
	defer timer.Stop()
	select {
	case <-done:
	case <-timer.C:
		c.noteSlowRead()
	}
	return c.snapshot()
}

// snapshot returns the current view under the lock. It performs no I/O, so it
// cannot be made slow by anything on disk.
func (c *correctionsSource) snapshot() correctionsView {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.view
}

// beginReload claims the right to re-read the file and starts the read, or
// returns nil when there is nothing to do (no path configured, the TTL has not
// elapsed, or a read is already in flight).
func (c *correctionsSource) beginReload() <-chan struct{} {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.path == "" || c.reloading || c.now().Sub(c.checkedAt) < correctionsRecheck {
		return nil
	}
	c.reloading = true
	c.checkedAt = c.now()
	done := make(chan struct{})
	go c.reload(done)
	return done
}

// reload re-reads the configured file, off the mutex, and commits the result.
//
// Any failure — missing file, over cap, empty, invalid UTF-8, a read that never
// returns — keeps the existing view and records why. The last known good set
// keeps serving: embedded until a file has ever loaded, then the last good file
// bytes. A gateway that suddenly stops telling clients the rules is the one
// outcome worse than telling them slightly stale ones.
func (c *correctionsSource) reload(done chan<- struct{}) {
	b, err := c.read(c.path)
	// commit before close: the waiter must observe the committed view, and a
	// test driving an injected clock must not race the commit's now() call.
	c.commit(b, err)
	close(done)
}

// commit installs the outcome of one re-read. It is the only place reloading is
// cleared, so a read that is still parked in the kernel keeps the single-flight
// claim and no second goroutine is ever spawned onto the same bad path.
func (c *correctionsSource) commit(b []byte, err error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.reloading = false
	if err == nil {
		var text string
		if text, err = validateDigest(b); err == nil {
			c.adopt(text, b)
			return
		}
		err = fmt.Errorf("%s: %w", c.path, err)
	}
	c.view.CheckedAt = c.now()
	c.view.LastError = err.Error()
}

// adopt installs a freshly-read digest. Caller holds c.mu.
//
// LoadedAt moves only when the CONTENT moves. It used to be stamped on every
// successful re-read, so corrections.loaded_at was always less than a minute
// old no matter how many weeks stale the checkout behind the file was — and the
// README pointed operators at exactly that field to confirm a deploy had landed,
// a signal that could not detect the risk it was named for. SHA256 is the honest
// one: compare it with `shasum -a 256 harness/corrections/INDEX.md`. CheckedAt
// keeps the "is the poller alive" reading that loaded_at used to double as.
func (c *correctionsSource) adopt(text string, raw []byte) {
	sum := sha256.Sum256(raw)
	digest := hex.EncodeToString(sum[:])
	loadedAt := c.view.LoadedAt
	if c.view.Source != "file" || c.view.Path != c.path || c.view.SHA256 != digest {
		loadedAt = c.now()
	}
	c.view = correctionsView{
		Text:      text,
		Count:     countCorrections(text),
		Source:    "file",
		Path:      c.path,
		Bytes:     len(raw),
		SHA256:    digest,
		LoadedAt:  loadedAt,
		CheckedAt: c.now(),
	}
}

// noteSlowRead records that the caller gave up waiting. It is a no-op if the
// read landed in the meantime, so a read that finishes on the deadline is not
// retroactively stamped as a failure.
func (c *correctionsSource) noteSlowRead() {
	c.mu.Lock()
	defer c.mu.Unlock()
	if !c.reloading {
		return
	}
	c.view.LastError = fmt.Sprintf("%s: the read did not finish within %s and is still outstanding; serving the last known good set. A path whose open or read blocks (a FIFO with no writer, a stale NFS or bind mount, a device node) is the usual cause.",
		c.path, correctionsReadBudget)
}

// readDigest reads the digest file with the cap applied BEFORE the bytes are
// allocated.
//
// os.ReadFile sizes its buffer from the file and pulls the whole thing into
// memory, so the 64 KiB cap only ever stopped bad bytes reaching the CLIENT: a
// wrong mount (a 256 MiB tarball at --corrections) was a 256 MiB allocation on
// the initialize path, repeated every correctionsRecheck, and only then
// rejected. Two guards now stand in front of that. A regular file over the cap
// is refused on its stat, unread. And the read itself is bounded by an
// io.LimitReader, so a growing file, a pipe or a /proc entry — none of which
// stat honestly — cannot get past cap+1 bytes either. The +1 is what keeps
// "exactly at the cap" loadable while still detecting one byte more.
func readDigest(path string, limit int) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	if st, serr := f.Stat(); serr == nil && st.Mode().IsRegular() && st.Size() > int64(limit) {
		return nil, fmt.Errorf("%s: corrections digest is %d bytes, over the %d-byte cap; rejected whole without reading it into memory (never truncated)", path, st.Size(), limit)
	}
	b, err := io.ReadAll(io.LimitReader(f, int64(limit)+1))
	if err != nil {
		return nil, fmt.Errorf("%s: %w", path, err)
	}
	return b, nil
}

// validateDigest accepts or rejects a candidate digest whole, and returns it
// verbatim — the gateway never parses, trims or rewrites the text.
func validateDigest(b []byte) (string, error) {
	// readDigest already refuses an over-cap REGULAR file on its stat, unread.
	// This is the second line: a pipe, a /proc entry or a file growing under the
	// read stats as 0 (or as something smaller than it delivers), and comes back
	// from the LimitReader as exactly cap+1 bytes.
	if len(b) > correctionsByteCap {
		return "", fmt.Errorf("corrections digest delivered more than the %d-byte cap (stopped at %d bytes); rejected whole (never truncated)", correctionsByteCap, len(b))
	}
	if !utf8.Valid(b) {
		return "", fmt.Errorf("corrections digest is not valid UTF-8 (%d bytes)", len(b))
	}
	// A digest with no corrections in it still carries the generator's header
	// prose, so empty never means "no rules today" — it means a bad mount or a
	// read that landed mid-rewrite (harness.py rebuilds INDEX.md with a plain
	// write_text, in place and not atomically, so a torn read is possible).
	// Either way the last known good set is the better answer.
	if strings.TrimSpace(string(b)) == "" {
		return "", fmt.Errorf("corrections digest is empty (%d bytes) — bad mount or a torn write", len(b))
	}
	return string(b), nil
}

// countCorrections is best-effort telemetry for gateway_status, nothing more.
// If harness.py ever changes the "[C-0001]" marker the count degrades to 0,
// visibly, while delivery is unaffected — the text is opaque passthrough. Do
// not "fix" this by parsing the digest: that would couple the gateway to a
// format another tool owns, and the coupling would break delivery, not a count.
func countCorrections(text string) int {
	return strings.Count(text, "[C-")
}

// statusReport is the corrections block of gateway_status: enough for an
// operator to see at a glance whether clients are getting rules, from where,
// and how fresh they are. path is omitted while the embedded snapshot is being
// served, because there is none. A non-empty last_error means the most recent
// re-read failed and this is the last known good set.
//
// Three fields answer three different questions, and conflating them is what
// made the old report misleading:
//
//	checked_at  when the file was last re-read. Always recent — that is the
//	            point: it says the poller is alive, nothing more.
//	loaded_at   when the CONTENT last changed. Old is not a fault; old plus a
//	            sha256 that does not match main is a checkout nobody pulled.
//	sha256      of the exact bytes being served. This is the field to compare
//	            against `shasum -a 256 harness/corrections/INDEX.md`; it is the
//	            only one that can tell a fresh deploy from a stale mount.
func (c *correctionsSource) statusReport() map[string]any {
	v := c.current()
	out := map[string]any{
		"count":      v.Count,
		"source":     v.Source,
		"bytes":      v.Bytes,
		"sha256":     v.SHA256,
		"loaded_at":  v.LoadedAt.Format(time.RFC3339),
		"checked_at": v.CheckedAt.Format(time.RFC3339),
		"last_error": v.LastError,
	}
	if v.Path != "" {
		out["path"] = v.Path
	}
	return out
}
