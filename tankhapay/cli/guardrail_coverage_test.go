package main

import (
	"bufio"
	"os"
	"strings"
	"testing"
)

// loadTSVCol0 returns the first tab-separated column of every non-empty line.
func loadTSVCol0(t *testing.T, path string) []string {
	f, err := os.Open(path)
	if err != nil {
		t.Fatalf("open %s: %v", path, err)
	}
	defer f.Close()
	var out []string
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1024*1024), 1024*1024)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		out = append(out, strings.Split(line, "\t")[0])
	}
	return out
}

// TestManifestCoversAllWiredReads is the coverage mandate: the generated
// wiredManifest must equal EXACTLY the extractor's wired-reads.tsv — every true
// read is wired as a command, and nothing extra is wired.
func TestManifestCoversAllWiredReads(t *testing.T) {
	want := map[string]bool{}
	for _, u := range loadTSVCol0(t, "../captures/wired-reads.tsv") {
		want[u] = true
	}
	got := map[string]bool{}
	for _, e := range wiredManifest {
		got[e.URL] = true
	}
	for u := range want {
		if !got[u] {
			t.Errorf("UNWIRED read (in wired-reads.tsv, missing from CLI): %s", u)
		}
	}
	for u := range got {
		if !want[u] {
			t.Errorf("EXTRA endpoint wired (not a known read): %s", u)
		}
	}
	if len(want) != len(got) {
		t.Errorf("count mismatch: wired-reads.tsv=%d, manifest=%d", len(want), len(got))
	} else {
		t.Logf("coverage OK: %d read endpoints wired, 1:1 with the inventory", len(got))
	}
}

// TestEveryWiredReadPassesGuardrail: no dead commands — every wired path must
// pass forbiddenPath (else it could never actually run).
func TestEveryWiredReadPassesGuardrail(t *testing.T) {
	for _, e := range wiredManifest {
		if err := forbiddenPath("POST", e.URL); err != nil {
			t.Errorf("DEAD COMMAND %s/%s — wired but guardrail-blocked: %v", e.Group, e.Cmd, err)
		}
	}
}

// TestReclassifiedWritesAllBlocked: the 35 mis-tagged reads (extractor said READ,
// call sites say WRITE) must ALL be refused by the guardrail — proving they are
// correctly held out of scope.
func TestReclassifiedWritesAllBlocked(t *testing.T) {
	writes := loadTSVCol0(t, "../captures/reclassified-writes.tsv")
	if len(writes) == 0 {
		t.Fatal("reclassified-writes.tsv is empty — the partition manifest is missing")
	}
	for _, u := range writes {
		if err := forbiddenPath("POST", u); err == nil {
			t.Errorf("reclassified WRITE not blocked by guardrail: %s", u)
		}
	}
}
