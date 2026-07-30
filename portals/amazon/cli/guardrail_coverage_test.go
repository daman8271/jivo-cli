package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestEveryWiredCommandMapsToAReadRow asserts every endpoint the CLI exposes is
// present in the vault's wired-reads.tsv (classified READ/READ_FILE). This is the
// coverage guarantee: the CLI never drifts ahead of the study's read allowlist.
func TestEveryWiredCommandMapsToAReadRow(t *testing.T) {
	tsv := filepath.Join("..", "captures", "wired-reads.tsv")
	b, err := os.ReadFile(tsv)
	if err != nil {
		t.Skipf("wired-reads.tsv not readable (%v) — skipping coverage cross-check", err)
	}
	// build the set of allowlisted (host,path) from the TSV
	read := map[string]bool{}
	for _, line := range strings.Split(string(b), "\n") {
		cols := strings.Split(line, "\t")
		if len(cols) < 6 {
			continue
		}
		host, path, class := cols[2], cols[3], cols[5]
		if class == "READ" || class == "READ_FILE" {
			read[host+"|"+path] = true
		}
	}
	if len(read) == 0 {
		t.Fatal("no READ rows parsed from wired-reads.tsv")
	}
	missing := 0
	for _, e := range readEndpoints {
		if !read[e.Host+"|"+e.Path] {
			t.Errorf("wired command %q (%s %s) is NOT a READ row in wired-reads.tsv", e.Name, e.Host, e.Path)
			missing++
		}
	}
	if missing == 0 {
		t.Logf("all %d wired commands map to a READ row", len(readEndpoints))
	}
}

// TestNoDuplicateCommandNamesWithinSection guards the generator against name clashes.
func TestNoDuplicateCommandNamesWithinSection(t *testing.T) {
	seen := map[string]bool{}
	for _, e := range readEndpoints {
		key := e.Section + "/" + e.Name
		if seen[key] {
			t.Errorf("duplicate command name within section: %s", key)
		}
		seen[key] = true
	}
}
