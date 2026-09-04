package cli

import (
	"os"
	"strings"
	"testing"
)

// readSource reads a source file in this package, so a guard's POSITION can be
// asserted and not just its behaviour.
func readSource(t *testing.T, name string) string {
	t.Helper()
	b, err := os.ReadFile(name)
	if err != nil {
		t.Fatalf("cannot read %s: %v", name, err)
	}
	return string(b)
}

// Daman, 2026-09-04: "never post it through manager ok / this time u did but
// never ever." On that day two Oil invoices (626084323, 626084324) went live
// under the shared `manager` login, so OPCH.UserSign is 1 and the books name
// no person for either. A posted document cannot be re-attributed from this
// CLI, which is why this is a guard in the binary and not a line in a skill.
//
// If these tests are failing because someone added an override flag: don't.
// The fix is to source the operator's own env file.

func TestSharedLoginsAreRefused(t *testing.T) {
	for _, u := range []string{
		"manager", "MANAGER", "Manager", " manager ",
		"sa", "administrator", "admin", "b1admin",
	} {
		if !isSharedLogin(u) {
			t.Errorf("isSharedLogin(%q) = false, want true — a shared login must never press Add", u)
		}
	}
}

func TestRealOperatorLoginsArePermitted(t *testing.T) {
	// The five desks whose drafts are ours to post, plus the other real logins
	// that own env files beside the binary.
	for _, u := range []string{
		"USER07", "USER08", "USER09", "USER19", "USER39",
		"USER05", "USER06", "USER36", "user39",
	} {
		if isSharedLogin(u) {
			t.Errorf("isSharedLogin(%q) = true, want false — this is a real person and must be able to post", u)
		}
	}
}

func TestSharedLoginRefusalSaysHowToFixIt(t *testing.T) {
	msg := sharedLoginRefusal("manager", "JIVO_OIL_HANADB")

	// It must say nothing was sent — the operator's first question.
	if !strings.Contains(msg, "Nothing was sent") {
		t.Error("refusal does not say that nothing was sent")
	}
	// It must name the way out, not just the wall.
	if !strings.Contains(msg, ".env") {
		t.Error("refusal does not point at the per-operator env files")
	}
	// It must warn the AI off the obvious workarounds.
	for _, want := range []string{"SAPB1_USER", "no flag for this"} {
		if !strings.Contains(msg, want) {
			t.Errorf("refusal is missing the guard-rail text %q", want)
		}
	}
	// It must carry the company so a wrong-book run is obvious.
	if !strings.Contains(msg, "JIVO_OIL_HANADB") {
		t.Error("refusal does not name the company")
	}
}

// The guard has to sit AHEAD of --dry-run. A dry run prints the POST that would
// go out, and printing it invites the next step — the same reasoning as the
// drafts-only desk guard.
func TestSharedLoginGuardRunsBeforeDryRun(t *testing.T) {
	src := readSource(t, "adddraft.go")
	guard := strings.Index(src, "isSharedLogin(cfg.User)")
	if guard < 0 {
		t.Fatal("GUARD 0b is gone from runAddDrafts — a shared login can post again")
	}
	entries := strings.Index(src, "parseDocEntries(args)")
	if entries < 0 {
		t.Fatal("cannot find parseDocEntries in adddraft.go")
	}
	if guard > entries {
		t.Error("the shared-login guard runs after the DocEntries are parsed; it must be first, ahead of --dry-run")
	}
}

func TestNoOverrideFlagForSharedLogin(t *testing.T) {
	src := readSource(t, "adddraft.go")
	for _, bad := range []string{"--allow-manager", "allowManager", "--shared-login", "AllowSharedLogin"} {
		if strings.Contains(src, bad) {
			t.Errorf("found %q — there must be no way to override the shared-login guard", bad)
		}
	}
}
