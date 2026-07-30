package main

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// TestEveryWiredCommandPassesGuardrail is the coverage guard, the mirror of
// guardrail_test.go: that test proves writes are blocked, this one proves no READ
// was accidentally blocked. It scans the generated cmd_*.go files, pulls the path
// literal out of every readGet/readPost call, and asserts each one passes the
// transport guardrail. A dead command therefore fails the build instead of failing
// silently at runtime.
func TestEveryWiredCommandPassesGuardrail(t *testing.T) {
	files, err := filepath.Glob("cmd_*.go")
	if err != nil || len(files) == 0 {
		t.Fatalf("no cmd_*.go files found: %v", err)
	}
	builder := regexp.MustCompile(`\b(readGet|readPost)\(`)
	// the LAST quoted argument on the line is the path
	pathLit := regexp.MustCompile(`"(/[^"]*)"\s*\)`)
	hostConst := regexp.MustCompile(`\b(hostBrandPortal|hostPartnerAPI|hostPicker)\b`)
	hosts := map[string]string{
		"hostBrandPortal": hostBrandPortal,
		"hostPartnerAPI":  hostPartnerAPI,
		"hostPicker":      hostPicker,
	}

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
			pm := pathLit.FindStringSubmatch(line)
			hm := hostConst.FindString(line)
			if pm == nil || hm == "" {
				t.Errorf("could not parse a wired command in %s:\n    %s", f, strings.TrimSpace(line))
				continue
			}
			method := "GET"
			if strings.Contains(line, "readPost(") {
				method = "POST"
			}
			// substitute a concrete id for any template placeholder
			path := regexp.MustCompile(`\{[^}]*\}|\$\{[^}]*\}`).ReplaceAllString(pm[1], "123")
			url := hosts[hm] + path
			if err := forbiddenRequest(method, url); err != nil {
				t.Errorf("DEAD COMMAND — a wired read is guardrail-blocked in %s:\n    %s\n    → %v",
					f, strings.TrimSpace(line), err)
			}
			checked++
		}
	}
	if checked == 0 {
		t.Fatal("extracted 0 wired commands — the scanner regex is broken")
	}
	if checked != allowlistSize() {
		t.Errorf("wired commands (%d) != allowlist size (%d): the CLI and the allowlist "+
			"have drifted; re-run captures/build_cli.py", checked, allowlistSize())
	}
	t.Logf("verified %d wired read commands all pass the guardrail", checked)
}

// TestNoWriteCommandExists asserts no command file wires a write builder. There is
// deliberately no writeGet/writePost/post/put/delete helper in this CLI at all;
// this test fails the build if one is ever introduced and used.
func TestNoWriteCommandExists(t *testing.T) {
	files, _ := filepath.Glob("*.go")
	banned := regexp.MustCompile(`\b(writePost|writeGet|doPut|doPatch|doDelete|readPut|readDelete)\(`)
	for _, f := range files {
		if strings.HasSuffix(f, "_test.go") {
			continue
		}
		b, err := os.ReadFile(f)
		if err != nil {
			continue
		}
		if m := banned.FindString(string(b)); m != "" {
			t.Errorf("%s uses a write builder %q — this CLI must have none", f, m)
		}
	}
}

// TestHardDenyCoversTheKnownWriteFamilies is a regression net: if the endpoint
// inventory grows a new write family, the denylist should be updated too. It
// asserts the families the study found are all represented.
func TestHardDenyCoversTheKnownWriteFamilies(t *testing.T) {
	want := []string{
		"token/refresh", "signout", "sendverificationcode",
		"initiate-sales-report", "initiate-bdpo-report",
		"fc-appointment", "indent/accept", "indent/reject",
		"batch/submit", "get-upload-info-v2",
		"generate_signed_url", "create_spin_change_request",
		"document/batch/generate",
	}
	joined := strings.ToLower(strings.Join(hardDeny, " "))
	for _, w := range want {
		if !strings.Contains(joined, w) {
			t.Errorf("hardDeny is missing the %q write family", w)
		}
	}
}
