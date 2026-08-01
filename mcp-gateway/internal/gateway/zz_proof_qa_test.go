package gateway

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

// --- Proof's independent tests. Not the author's suite. ---

func writeFile(t *testing.T, dir, name, body string) string {
	t.Helper()
	p := filepath.Join(dir, name)
	if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	return p
}

// A digest exactly ON the cap must load; one byte over must be rejected whole.
func TestProofCapBoundaryIsExact(t *testing.T) {
	dir := t.TempDir()
	at := writeFile(t, dir, "at.md", strings.Repeat("a", correctionsByteCap))
	over := writeFile(t, dir, "over.md", strings.Repeat("a", correctionsByteCap+1))

	c := newCorrectionsSource(at, time.Now)
	if v := c.current(); v.Source != "file" || v.Bytes != correctionsByteCap {
		t.Fatalf("exactly-at-cap file rejected: %+v", v)
	}
	c2 := newCorrectionsSource(over, time.Now)
	v := c2.current()
	if v.Source != "embedded" {
		t.Fatalf("over-cap file was accepted: source=%s bytes=%d", v.Source, v.Bytes)
	}
	if !strings.Contains(v.LastError, "over the") {
		t.Fatalf("over-cap error unhelpful: %q", v.LastError)
	}
	// The served text must be the WHOLE embedded snapshot, not a truncation.
	if v.Text != string(embeddedDigest) {
		t.Fatal("over-cap rejection did not fall back to the whole embedded snapshot")
	}
}

// A file that goes bad AFTER a good load must keep serving the good bytes.
func TestProofLastKnownGoodSurvivesEveryFailureMode(t *testing.T) {
	dir := t.TempDir()
	p := writeFile(t, dir, "d.md", "# good\n- **[C-0001]** rule one\n- **[C-0002]** rule two\n")

	now := time.Now()
	c := newCorrectionsSource(p, func() time.Time { return now })
	good := c.current()
	if good.Source != "file" || good.Count != 2 {
		t.Fatalf("first load wrong: %+v", good)
	}

	for _, tc := range []struct {
		name string
		mut  func()
		want string
	}{
		{"empty", func() { os.WriteFile(p, nil, 0o644) }, "empty"},
		{"invalid utf8", func() { os.WriteFile(p, []byte{0xff, 0xfe, 0x00}, 0o644) }, "UTF-8"},
		{"over cap", func() { os.WriteFile(p, []byte(strings.Repeat("z", correctionsByteCap+1)), 0o644) }, "over the"},
		{"deleted", func() { os.Remove(p) }, "no such file"},
		{"is a directory", func() { os.Mkdir(p, 0o755) }, ""},
	} {
		t.Run(tc.name, func(t *testing.T) {
			tc.mut()
			now = now.Add(2 * correctionsRecheck)
			v := c.current()
			if v.Text != good.Text {
				t.Fatalf("last-known-good was lost after %s: text=%q", tc.name, v.Text)
			}
			if v.Count != 2 || v.Source != "file" {
				t.Fatalf("telemetry lost after %s: %+v", tc.name, v)
			}
			if v.LastError == "" {
				t.Fatalf("%s produced no last_error — a silent degradation", tc.name)
			}
			if tc.want != "" && !strings.Contains(v.LastError, tc.want) {
				t.Fatalf("%s error = %q, want mention of %q", tc.name, v.LastError, tc.want)
			}
			t.Logf("%-14s last_error=%s", tc.name, v.LastError)
		})
	}
}

// Once the file recovers, a stale error must NOT stick around claiming failure.
func TestProofLastErrorClearsOnRecovery(t *testing.T) {
	dir := t.TempDir()
	p := writeFile(t, dir, "d.md", "- **[C-0001]** a\n")
	now := time.Now()
	c := newCorrectionsSource(p, func() time.Time { return now })
	c.current()
	os.Remove(p)
	now = now.Add(2 * correctionsRecheck)
	if c.current().LastError == "" {
		t.Fatal("expected an error after delete")
	}
	writeFile(t, dir, "d.md", "- **[C-0001]** a\n- **[C-0002]** b\n")
	now = now.Add(2 * correctionsRecheck)
	v := c.current()
	if v.LastError != "" {
		t.Fatalf("stale last_error survived recovery: %q", v.LastError)
	}
	if v.Count != 2 {
		t.Fatalf("recovered digest not picked up: %+v", v)
	}
}

// The TTL must actually hold: no re-read before correctionsRecheck elapses.
func TestProofTTLHoldsAndThenReleases(t *testing.T) {
	dir := t.TempDir()
	p := writeFile(t, dir, "d.md", "- **[C-0001]** a\n")
	now := time.Now()
	c := newCorrectionsSource(p, func() time.Time { return now })
	c.current()
	writeFile(t, dir, "d.md", "- **[C-0001]** a\n- **[C-0002]** b\n")

	now = now.Add(correctionsRecheck - time.Nanosecond)
	if got := c.current().Count; got != 1 {
		t.Fatalf("re-read happened before the TTL elapsed: count=%d", got)
	}
	now = now.Add(time.Nanosecond)
	if got := c.current().Count; got != 2 {
		t.Fatalf("no re-read after the TTL elapsed: count=%d", got)
	}
}

// Concurrent initialize + gateway_status must not race or tear the text.
func TestProofConcurrentInitializeAndStatus(t *testing.T) {
	dir := t.TempDir()
	p := writeFile(t, dir, "d.md", "- **[C-0001]** a\n")
	g := New(Config{CorrectionsPath: p, Backends: nil}, "test")

	// A writer keeps rewriting the file underneath the readers.
	stop := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for i := 0; ; i++ {
			select {
			case <-stop:
				return
			default:
			}
			os.WriteFile(p, []byte(strings.Repeat("- **[C-0001]** a\n", 1+i%5)), 0o644)
		}
	}()
	for i := 0; i < 40; i++ {
		wg.Add(2)
		go func() { defer wg.Done(); _ = g.initializeResult(nil) }()
		go func() { defer wg.Done(); _ = g.CorrectionsStatus() }()
	}
	close(stop)
	wg.Wait()

	res := g.initializeResult(nil)
	if !strings.Contains(res["instructions"].(string), "[C-0001]") {
		t.Fatal("instructions lost the digest under concurrency")
	}
}

// What a client actually receives must be JSON-safe and carry the digest verbatim.
func TestProofInitializeCarriesDigestVerbatimOverJSON(t *testing.T) {
	dir := t.TempDir()
	// Deliberately nasty: quotes, backslashes, a control-ish char and non-ASCII.
	body := "# JIVO \"corrections\"\n- **[C-0001]** ₹2.5 Cr \\ path — em-dash & \"quoted\"\n\ttabbed\n"
	p := writeFile(t, dir, "d.md", body)
	g := New(Config{CorrectionsPath: p}, "test")

	b, err := json.Marshal(g.initializeResult(nil))
	if err != nil {
		t.Fatal(err)
	}
	var back map[string]any
	if err := json.Unmarshal(b, &back); err != nil {
		t.Fatal(err)
	}
	ins := back["instructions"].(string)
	// Verbatim, byte for byte, after a full JSON round trip — but fenced, and
	// with the read-only trailer after it rather than the file having the last
	// word.
	if !strings.Contains(ins, body) {
		t.Fatalf("digest not delivered verbatim after a JSON round trip.\ngot: %q", ins)
	}
	if !strings.HasSuffix(ins, correctionsTrailer) {
		t.Fatalf("the digest is the last thing the client reads; the trailer must be.\ngot tail: %q", ins[max(0, len(ins)-200):])
	}
}

// An empty --corrections path must never read the process's working directory
// or anything else; it stays on the embedded snapshot forever.
func TestProofEmptyPathNeverReadsAnything(t *testing.T) {
	c := newCorrectionsSource("   ", time.Now)
	for i := 0; i < 3; i++ {
		v := c.current()
		if v.Source != "embedded" || v.Path != "" {
			t.Fatalf("empty path produced a file read: %+v", v)
		}
	}
	if _, ok := c.statusReport()["path"]; ok {
		t.Fatal("statusReport advertises a path while serving the embedded snapshot")
	}
}
