package main

import (
	"encoding/json"
	"strings"
	"testing"
)

// TestHelpWorksWithoutConfig: --help must never need a .env, a session or a
// network. It is the first thing an operator on a fresh Windows box runs.
func TestHelpWorksWithoutConfig(t *testing.T) {
	useTempStateDir(t)
	t.Setenv("GST_ENV", "")
	out, err := runCLI(t, "--help")
	if err != nil {
		t.Fatalf("--help: %v", err)
	}
	for _, want := range []string{"gst-portal", "doctor", "auth", "masters", "--gstin", "--agent"} {
		if !strings.Contains(out, want) {
			t.Errorf("--help output is missing %q:\n%s", want, out)
		}
	}
	if !strings.Contains(out, "READ") && !strings.Contains(out, "read-only") {
		t.Error("--help must state that this CLI is read-only")
	}
}

func TestAuthListMasksCredentials(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	out, err := runCLI(t, "auth", "list")
	if err != nil {
		t.Fatalf("auth list: %v", err)
	}
	if strings.Contains(out, testPass) {
		t.Fatal("auth list printed a password")
	}
	for _, want := range []string{"06AAAAA0000A1Z0", "Haryana", "Delhi ISD", "…"} {
		if !strings.Contains(out, want) {
			t.Errorf("auth list is missing %q:\n%s", want, out)
		}
	}
	if n := strings.Count(out, "AAAAA0000A"); n != 8 {
		t.Errorf("auth list showed %d registrations, want 8", n)
	}
}

func TestDoctorOfflineOpensNoSocket(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := newFakePortal(t) // routes nothing: any request at all would 404 and be counted

	out, err := runCLI(t, "doctor", "--offline", "--state", "haryana")
	if err != nil {
		t.Fatalf("doctor --offline: %v", err)
	}
	if fp.hitCount() != 0 {
		t.Errorf("--offline opened %d connection(s)", fp.hitCount())
	}
	for _, want := range []string{"06AAAAA0000A1Z0", "no cached session", "skipped (--offline)"} {
		if !strings.Contains(out, want) {
			t.Errorf("doctor --offline is missing %q:\n%s", want, out)
		}
	}
	if strings.Contains(out, testPass) {
		t.Fatal("doctor printed a password")
	}
}

func TestDoctorLiveReadChecksTheGSTIN(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostServices, "/services/api/ustatus", "ustatus.json")

	out, err := runCLI(t, "doctor", "--state", "haryana")
	if err != nil {
		t.Fatalf("doctor: %v", err)
	}
	if !strings.Contains(out, "ok — ustatus says 06AAAAA0000A1Z0") {
		t.Errorf("doctor did not confirm the registration:\n%s", out)
	}

	// and if the session belongs to a DIFFERENT registration, doctor must say so
	seedSession(t, "09AAAAA0000A1ZU")
	_, err = runCLI(t, "doctor", "--gstin", "09AAAAA0000A1ZU")
	if err == nil {
		t.Fatal("a session for another GSTIN must fail the doctor")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit code = %d want %d (auth)", exitCodeFor(err), exitAuth)
	}
}

func TestMastersFormsAgainstFakePortal(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/master/gstrs/A", "master-gstrs-A.json")

	out, err := runCLI(t, "masters", "forms", "--state", "hr", "--agent")
	if err != nil {
		t.Fatalf("masters forms: %v", err)
	}
	var env struct {
		OK       bool            `json:"ok"`
		Command  string          `json:"command"`
		Endpoint string          `json:"endpoint"`
		GSTIN    string          `json:"gstin"`
		Count    int             `json:"count"`
		Data     json.RawMessage `json:"data"`
	}
	if err := json.Unmarshal([]byte(out), &env); err != nil {
		t.Fatalf("--agent output is not the envelope: %v\n%s", err, out)
	}
	if !env.OK || env.Command != "masters forms" || env.GSTIN != "06AAAAA0000A1Z0" {
		t.Errorf("envelope = %+v", env)
	}
	if env.Count != 3 {
		t.Errorf("count = %d want 3", env.Count)
	}
	if !strings.Contains(env.Endpoint, "/master/gstrs/A") {
		t.Errorf("endpoint = %q", env.Endpoint)
	}
	hit := fp.lastHit(t)
	if hit.Path != "/master/gstrs/A" || hit.Host != hostReturn {
		t.Errorf("request went to %s%s", hit.Host, hit.Path)
	}
}

func TestMastersMonthsPassesTheFY(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/master/fy/2026-27", "master-gstrs-A.json")

	if _, err := runCLI(t, "masters", "months", "--fy", "2026-27", "--state", "hr"); err != nil {
		t.Fatalf("masters months: %v", err)
	}
	if got := fp.lastHit(t).Path; got != "/master/fy/2026-27" {
		t.Errorf("path = %s", got)
	}
	// a malformed FY is caught before any request
	before := fp.hitCount()
	if _, err := runCLI(t, "masters", "months", "--fy", "2026-28", "--state", "hr"); err == nil {
		t.Error("2026-28 is not a financial year and must be refused")
	}
	if fp.hitCount() != before {
		t.Error("a bad --fy still reached the portal")
	}
}

// A command with no registration selector must refuse rather than pick one.
func TestCommandWithoutSelectorIsUsageError(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := newFakePortal(t)
	_, err := runCLI(t, "masters", "forms")
	if err == nil {
		t.Fatal("no selector must be an error")
	}
	if exitCodeFor(err) != exitUsage {
		t.Errorf("exit code = %d want %d (usage)", exitCodeFor(err), exitUsage)
	}
	if fp.hitCount() != 0 {
		t.Error("a usage error must not open a connection")
	}
}

// Deferred leaves are discoverable but inert: they never touch the network.
func TestDeferredLeavesNeverHitNetwork(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)

	if _, err := runCLI(t, "gstr2a", "amendments", "--period", "072026", "--state", "hr"); err == nil {
		t.Error("gstr2a amendments is not captured live yet and must say so")
	}
	if fp.hitCount() != 0 {
		t.Errorf("a deferred leaf opened %d connection(s)", fp.hitCount())
	}
}
