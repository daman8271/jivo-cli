package main

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// TestWiredPathsPassGuardrail is the coverage guard for the read-only guardrail:
// EVERY path wired into a command (via simpleGet/queryGet/getByID/postRead) must
// PASS forbiddenPath, i.e. never be a dead command. It scans the source of every
// cmd_*.go, pulls the path literal out of each builder call, and checks it. If a
// future guardrail change (or a new command) blocks a wired read, this fails and
// names the offender — so dead commands can never sneak in.
func TestWiredPathsPassGuardrail(t *testing.T) {
	files, err := filepath.Glob("cmd_*.go")
	if err != nil || len(files) == 0 {
		t.Fatalf("no cmd_*.go files found: %v", err)
	}
	builder := regexp.MustCompile(`\b(simpleGet|queryGet|getByID|postRead)\(`)
	pathLit := regexp.MustCompile(`"(/[^"]+)"`) // first "/..."-literal on the line is the path

	checked := 0
	for _, f := range files {
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatalf("read %s: %v", f, err)
		}
		for _, line := range strings.Split(string(b), "\n") {
			if !builder.MatchString(line) {
				continue
			}
			m := pathLit.FindStringSubmatch(line)
			if m == nil {
				continue
			}
			path := strings.ReplaceAll(m[1], "%s", "123") // fill the id template
			url := "https://fcc.zepto.co.in" + path
			if err := forbiddenPath("GET", url); err != nil {
				t.Errorf("DEAD COMMAND — wired read path is guardrail-blocked in %s:\n    %s\n    → %v", f, strings.TrimSpace(line), err)
			}
			checked++
		}
	}
	if checked == 0 {
		t.Fatal("extracted 0 wired paths — the scanner regex is broken")
	}
	t.Logf("verified %d wired read paths all pass the guardrail", checked)
}
