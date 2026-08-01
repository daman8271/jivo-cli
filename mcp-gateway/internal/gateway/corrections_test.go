package gateway

import (
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// fakeClock drives correctionsSource's TTL without sleeping. It is mutex-
// guarded because the concurrency tests read it from many goroutines.
type fakeClock struct {
	mu sync.Mutex
	t  time.Time
}

func newFakeClock() *fakeClock {
	return &fakeClock{t: time.Date(2026, 8, 1, 12, 0, 0, 0, time.UTC)}
}

func (c *fakeClock) now() time.Time {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.t
}

func (c *fakeClock) advance(d time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.t = c.t.Add(d)
}

// writeDigest writes a digest file and returns its path.
func writeDigest(t *testing.T, dir, name, body string) string {
	t.Helper()
	p := filepath.Join(dir, name)
	if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
		t.Fatalf("write %s: %v", p, err)
	}
	return p
}

const markerDigest = "# JIVO corrections — active rule digest\n\n" +
	"## all\n- **[C-9001]** MARKER-ALPHA: this rule exists only in the mounted file.\n" +
	"- **[C-9002]** MARKER-BETA: and so does this one.\n"

// A mounted file wins over the embedded snapshot, and its bytes are served
// verbatim — this is the whole point of the runtime path: a correction pushed
// to main reaches a phone without rebuilding the binary.
func TestCorrectionsFileWinsOverEmbedded(t *testing.T) {
	path := writeDigest(t, t.TempDir(), "INDEX.md", markerDigest)
	c := newCorrectionsSource(path, newFakeClock().now)

	v := c.current()
	if v.Text != markerDigest {
		t.Fatalf("text = %q, want the file's bytes verbatim", v.Text)
	}
	if v.Source != "file" {
		t.Fatalf("source = %q, want file", v.Source)
	}
	if v.Path != path {
		t.Fatalf("path = %q, want %q", v.Path, path)
	}
	if v.Count != 2 {
		t.Fatalf("count = %d, want 2 (the two [C- markers in the file)", v.Count)
	}
	if v.Bytes != len(markerDigest) {
		t.Fatalf("bytes = %d, want %d", v.Bytes, len(markerDigest))
	}
	if v.LastError != "" {
		t.Fatalf("last_error = %q, want empty on a clean load", v.LastError)
	}
	// The embedded rules are gone, replaced — not merged.
	if strings.Contains(v.Text, "[C-0001]") {
		t.Fatalf("file digest still carries embedded rules: %q", v.Text)
	}
}

// No file (a mount that has not appeared, or none configured) is a degrade, not
// an outage: the embedded snapshot still carries real rules, and the failure is
// visible in last_error.
func TestCorrectionsMissingFileFallsBackToEmbedded(t *testing.T) {
	missing := filepath.Join(t.TempDir(), "nope", "INDEX.md")
	c := newCorrectionsSource(missing, newFakeClock().now)

	v := c.current()
	if v.Source != "embedded" {
		t.Fatalf("source = %q, want embedded", v.Source)
	}
	if v.Text != string(embeddedDigest) {
		t.Fatalf("text is not the embedded snapshot (%d bytes)", len(v.Text))
	}
	if !strings.Contains(v.Text, "[C-0001]") {
		t.Fatalf("embedded snapshot carries no rules: %q", v.Text)
	}
	if v.LastError == "" {
		t.Fatal("last_error is empty — a missing digest file must be visible")
	}
	// path is omitted while the embedded copy is being served: there is none.
	if _, ok := c.statusReport()["path"]; ok {
		t.Fatalf("status reports a path while serving embedded: %v", c.statusReport())
	}
}

// Over the cap the file is rejected WHOLE. A truncated rule list still sounds
// authoritative while missing law, so what must be served is the previous good
// view, untouched.
func TestCorrectionsOversizeRejectedWhole(t *testing.T) {
	dir := t.TempDir()
	path := writeDigest(t, dir, "INDEX.md", markerDigest)
	clock := newFakeClock()
	c := newCorrectionsSource(path, clock.now)
	good := c.current()
	if good.Source != "file" {
		t.Fatalf("setup: source = %q, want file", good.Source)
	}

	huge := strings.Repeat("x", correctionsByteCap+1)
	writeDigest(t, dir, "INDEX.md", huge)
	clock.advance(correctionsRecheck)

	v := c.current()
	if v.Text != markerDigest {
		t.Fatalf("text changed after an over-cap file; want the previous good view kept")
	}
	if strings.Contains(v.Text, "xxxx") || v.Bytes != len(markerDigest) {
		t.Fatalf("over-cap file was truncated into the view: bytes = %d", v.Bytes)
	}
	if !strings.Contains(v.LastError, "65536") {
		t.Fatalf("last_error = %q, want it to name the %d-byte cap", v.LastError, correctionsByteCap)
	}
	if !strings.Contains(v.LastError, path) {
		t.Fatalf("last_error = %q, want it to name the offending file", v.LastError)
	}
}

// An empty (or whitespace-only) file is a bad mount or a read that landed mid
// -rewrite — never "no rules today", because a real digest always carries the
// generator's header prose.
func TestCorrectionsEmptyFileFallsBack(t *testing.T) {
	for _, body := range []string{"", "   \n\t\n  "} {
		dir := t.TempDir()
		path := writeDigest(t, dir, "INDEX.md", body)
		c := newCorrectionsSource(path, newFakeClock().now)

		v := c.current()
		if v.Source != "embedded" || v.Text != string(embeddedDigest) {
			t.Fatalf("empty file %q served: source = %q", body, v.Source)
		}
		if !strings.Contains(v.LastError, "empty") {
			t.Fatalf("last_error = %q, want it to say the digest was empty", v.LastError)
		}
	}
}

// Binary junk (a half-written file, a wrong mount) is rejected too.
func TestCorrectionsInvalidUTF8Rejected(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "INDEX.md")
	if err := os.WriteFile(path, []byte{0x23, 0x20, 0xff, 0xfe, 0xfd, 0x0a}, 0o644); err != nil {
		t.Fatal(err)
	}
	c := newCorrectionsSource(path, newFakeClock().now)

	v := c.current()
	if v.Source != "embedded" || v.Text != string(embeddedDigest) {
		t.Fatalf("invalid UTF-8 was served: source = %q", v.Source)
	}
	if !strings.Contains(v.LastError, "UTF-8") {
		t.Fatalf("last_error = %q, want it to say invalid UTF-8", v.LastError)
	}
}

// A correction pushed to main reaches clients within correctionsRecheck — no
// container restart. Before the TTL the old set is still served (one file read
// per minute, not one per initialize).
func TestCorrectionsReloadOnTTL(t *testing.T) {
	dir := t.TempDir()
	path := writeDigest(t, dir, "INDEX.md", markerDigest)
	clock := newFakeClock()
	c := newCorrectionsSource(path, clock.now)

	if v := c.current(); !strings.Contains(v.Text, "MARKER-ALPHA") {
		t.Fatalf("first load = %q, want file A", v.Text)
	}

	const digestB = "# JIVO corrections — active rule digest\n\n## all\n- **[C-9003]** MARKER-GAMMA: pushed after the gateway booted.\n"
	writeDigest(t, dir, "INDEX.md", digestB)

	clock.advance(correctionsRecheck - time.Nanosecond)
	if v := c.current(); !strings.Contains(v.Text, "MARKER-ALPHA") {
		t.Fatalf("re-read before the TTL: text = %q", v.Text)
	}

	clock.advance(time.Nanosecond)
	v := c.current()
	if v.Text != digestB {
		t.Fatalf("text = %q, want file B after the TTL", v.Text)
	}
	if v.Count != 1 {
		t.Fatalf("count = %d, want 1 after reload", v.Count)
	}
}

// Last known good is per-source: once a file has loaded, a later breakage keeps
// the FILE's rules, not the (older) embedded snapshot.
func TestCorrectionsLastGoodFileSurvivesBreakage(t *testing.T) {
	dir := t.TempDir()
	path := writeDigest(t, dir, "INDEX.md", markerDigest)
	clock := newFakeClock()
	c := newCorrectionsSource(path, clock.now)
	if v := c.current(); v.Source != "file" {
		t.Fatalf("setup: source = %q, want file", v.Source)
	}

	if err := os.Remove(path); err != nil {
		t.Fatal(err)
	}
	clock.advance(correctionsRecheck)

	v := c.current()
	if v.Text != markerDigest {
		t.Fatalf("text = %q, want the last good FILE content", v.Text)
	}
	if v.Source != "file" || v.Path != path {
		t.Fatalf("source/path = %q/%q, want the file provenance kept", v.Source, v.Path)
	}
	if v.LastError == "" {
		t.Fatal("last_error is empty — the deleted file must be visible")
	}
	if v.Text == string(embeddedDigest) {
		t.Fatal("fell back to the embedded snapshot, losing newer file rules")
	}
}

// Requirement 5 as an executable contract: the digest is opaque passthrough. A
// format change in harness.py degrades the count to 0 and nothing else. Do not
// "fix" this by parsing.
func TestCorrectionsFormatChangeStillDelivers(t *testing.T) {
	const newFormat = "# JIVO corrections\n\nRULE 1 :: quantity is in pieces.\nRULE 2 :: segment on U_Sub_Group.\n"
	path := writeDigest(t, t.TempDir(), "INDEX.md", newFormat)
	c := newCorrectionsSource(path, newFakeClock().now)

	v := c.current()
	if v.Text != newFormat {
		t.Fatalf("text = %q, want the unfamiliar format delivered verbatim", v.Text)
	}
	if v.Count != 0 {
		t.Fatalf("count = %d, want 0 (best-effort telemetry only)", v.Count)
	}
	if v.LastError != "" {
		t.Fatalf("last_error = %q, want empty: an unknown format is not an error", v.LastError)
	}
}

// The embedded snapshot must not drift from the repo digest, or the fallback
// silently teaches yesterday's rules.
//
// The skip is gated on a MARKER, not on the digest's own readability. Skipping
// whenever the file could not be read made the drift guard opt-in on build
// location: a CI job or container build that copies only mcp-gateway/ got a
// green suite with a silently stale rule set, which is the exact failure this
// test exists to catch. So the rule is now: if harness/bin/harness.py is there,
// we are in the jivo-cli checkout and the digest MUST be readable and identical;
// only a genuinely standalone module skips.
func TestEmbeddedDigestSnapshotMatchesRepo(t *testing.T) {
	const (
		repoDigest = "../../../harness/corrections/INDEX.md"
		repoMarker = "../../../harness/bin/harness.py"
	)
	if _, err := os.Stat(repoMarker); err != nil {
		t.Skipf("no jivo-cli checkout around this module (%s absent): %v", repoMarker, err)
	}
	want, err := os.ReadFile(repoDigest)
	if err != nil {
		t.Fatalf("in a jivo-cli checkout (%s exists) but the repo digest at %s is unreadable: %v\n"+
			"the embedded snapshot cannot be checked for drift, which is the one thing this test is for",
			repoMarker, repoDigest, err)
	}
	if string(want) != string(embeddedDigest) {
		t.Fatalf("assets/corrections.md has drifted from %s — re-copy it:\n"+
			"  cp harness/corrections/INDEX.md mcp-gateway/internal/gateway/assets/corrections.md\n"+
			"embedded (%d bytes):\n%s\nrepo (%d bytes):\n%s",
			repoDigest, len(embeddedDigest), embeddedDigest, len(want), want)
	}
}

// validateDigest's boundary: exactly at the cap is fine, one byte over is not.
func TestValidateDigestCapBoundary(t *testing.T) {
	atCap := []byte(strings.Repeat("y", correctionsByteCap))
	if _, err := validateDigest(atCap); err != nil {
		t.Fatalf("exactly at the cap was rejected: %v", err)
	}
	if _, err := validateDigest(append(atCap, 'y')); err == nil {
		t.Fatal("one byte over the cap was accepted")
	}
}

// countCorrections is deliberately dumb: markers, not parsing.
func TestCountCorrections(t *testing.T) {
	cases := []struct {
		text string
		want int
	}{
		{"", 0},
		{"no markers here", 0},
		{"- **[C-0001]** a\n- **[C-0002]** b\n", 2},
		{string(embeddedDigest), strings.Count(string(embeddedDigest), "[C-")},
	}
	for _, c := range cases {
		if got := countCorrections(c.text); got != c.want {
			t.Errorf("countCorrections(%.30q) = %d, want %d", c.text, got, c.want)
		}
	}
	if countCorrections(string(embeddedDigest)) < 3 {
		t.Fatalf("embedded snapshot has %d rules, want the real digest's several",
			countCorrections(string(embeddedDigest)))
	}
}

// The source is read from every initialize, on every connection, while the
// mounted file is being rewritten under it. Run under -race, this is the test
// that the shared view is never observed half-updated.
func TestCorrectionsConcurrentReloadRace(t *testing.T) {
	dir := t.TempDir()
	path := writeDigest(t, dir, "INDEX.md", markerDigest)

	// A clock that jumps a minute per call, so every single current() re-reads:
	// the reload path runs hot instead of once.
	base := time.Date(2026, 8, 1, 12, 0, 0, 0, time.UTC)
	var ticks int64
	c := newCorrectionsSource(path, func() time.Time {
		return base.Add(time.Duration(atomic.AddInt64(&ticks, 1)) * time.Minute)
	})

	stop := make(chan struct{})
	var writer sync.WaitGroup
	writer.Add(1)
	go func() {
		defer writer.Done()
		// os.WriteFile directly, not the helper: t.Fatalf may only be called
		// from the test goroutine. This also reproduces harness.py's
		// non-atomic in-place rewrite, torn reads and all.
		for i := 0; ; i++ {
			select {
			case <-stop:
				return
			default:
			}
			body := markerDigest + "- **[C-99" + string(rune('0'+i%10)) + "]** churn\n"
			if err := os.WriteFile(filepath.Join(dir, "INDEX.md"), []byte(body), 0o644); err != nil {
				t.Errorf("rewrite: %v", err)
				return
			}
		}
	}()

	var readers sync.WaitGroup
	for i := 0; i < 32; i++ {
		readers.Add(1)
		go func() {
			defer readers.Done()
			for j := 0; j < 40; j++ {
				v := c.current()
				if strings.TrimSpace(v.Text) == "" {
					t.Errorf("served an empty digest (source %q, err %q)", v.Source, v.LastError)
					return
				}
			}
		}()
	}
	readers.Wait()
	close(stop)
	writer.Wait()
}

// The same, one level up: N clients calling initialize concurrently while the
// digest file churns. Nothing may race, and every client must get real rules.
func TestCorrectionsConcurrentInitialize(t *testing.T) {
	dir := t.TempDir()
	path := writeDigest(t, dir, "INDEX.md", markerDigest)

	cfg := DefaultConfig()
	cfg.CorrectionsPath = path
	g := New(cfg, "test")

	stop := make(chan struct{})
	var writer sync.WaitGroup
	writer.Add(1)
	go func() {
		defer writer.Done()
		for {
			select {
			case <-stop:
				return
			default:
			}
			if err := os.WriteFile(filepath.Join(dir, "INDEX.md"), []byte(markerDigest), 0o644); err != nil {
				t.Errorf("rewrite: %v", err)
				return
			}
		}
	}()

	var clients sync.WaitGroup
	for i := 0; i < 24; i++ {
		clients.Add(1)
		go func() {
			defer clients.Done()
			for j := 0; j < 20; j++ {
				res := g.initializeResult(nil)
				instr, _ := res["instructions"].(string)
				if !strings.Contains(instr, "gateway_status") {
					t.Errorf("instructions lost the gateway guidance: %q", instr)
					return
				}
				if !strings.Contains(instr, "[C-") {
					t.Errorf("instructions carry no corrections: %q", instr)
					return
				}
				_ = g.CorrectionsStatus()
			}
		}()
	}
	clients.Wait()
	close(stop)
	writer.Wait()
}

// An unconfigured gateway (the compiled default) reports a clean embedded
// source, not a phantom failure — CorrectionsPath is deliberately not in
// Validate(), so this is the shape an operator sees when nothing is mounted.
func TestCorrectionsUnconfiguredIsCleanEmbedded(t *testing.T) {
	if DefaultConfig().CorrectionsPath != "" {
		t.Fatalf("DefaultConfig().CorrectionsPath = %q, want empty", DefaultConfig().CorrectionsPath)
	}
	if err := DefaultConfig().Validate(); err != nil {
		t.Fatalf("an unconfigured digest must not block startup: %v", err)
	}
	st := New(DefaultConfig(), "test").CorrectionsStatus()
	if st["source"] != "embedded" {
		t.Fatalf("source = %v, want embedded", st["source"])
	}
	if st["last_error"] != "" {
		t.Fatalf("last_error = %v, want empty when no path is configured", st["last_error"])
	}
	if n, _ := st["count"].(int); n < 3 {
		t.Fatalf("count = %v, want the embedded snapshot's rules", st["count"])
	}
	if _, err := time.Parse(time.RFC3339, st["loaded_at"].(string)); err != nil {
		t.Fatalf("loaded_at = %v, not RFC3339: %v", st["loaded_at"], err)
	}
}

// The env var and the Config field are wired, with the flag left to win in
// main.go (same precedence as every other setting).
func TestConfigFromEnvReadsCorrectionsPath(t *testing.T) {
	env := map[string]string{"JIVO_GW_CORRECTIONS": "  /etc/jivo/corrections/INDEX.md  "}
	cfg := ConfigFromEnv(func(k string) string { return env[k] })
	if cfg.CorrectionsPath != "/etc/jivo/corrections/INDEX.md" {
		t.Fatalf("CorrectionsPath = %q, want the trimmed env value", cfg.CorrectionsPath)
	}
	if empty := ConfigFromEnv(func(string) string { return "" }); empty.CorrectionsPath != "" {
		t.Fatalf("CorrectionsPath = %q with no env, want empty", empty.CorrectionsPath)
	}
}
