package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const testPass = "N0t-The-Real-Password!"

// writeTestEnv writes a .env with the 8 real-shaped registrations but synthetic
// GSTINs/creds, and points $GST_ENV at it.
func writeTestEnv(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	p := filepath.Join(dir, ".env")
	body := `# JIVO GST registrations (test)
GST_01_STATE=Haryana
GST_01_GSTIN=06AAAAA0000A1Z0
GST_01_USER=jivotest729
GST_01_PASS=` + testPass + `

export GST_02_STATE=Rajasthan
GST_02_GSTIN=08AAAAA0000A1ZW
GST_02_USER="jivotest_rj08"
GST_02_PASS='` + testPass + `'

GST_03_STATE=Punjab
GST_03_GSTIN=03AAAAA0000A1Z6
GST_03_USER=JIVOTESTPB
GST_03_PASS=` + testPass + `

GST_04_STATE=Delhi
GST_04_GSTIN=07AAAAA0000A1ZY
GST_04_USER=jivotest_dl07
GST_04_PASS=` + testPass + `

GST_05_STATE=Himachal Pradesh
GST_05_GSTIN=02AAAAA0000A1Z8
GST_05_USER=akal_test
GST_05_PASS=` + testPass + `

GST_06_STATE=Uttar Pradesh
GST_06_GSTIN=09AAAAA0000A1ZU
GST_06_USER=JIVOTESTUP09
GST_06_PASS=` + testPass + `

GST_07_STATE=Maharashtra (Mumbai)
GST_07_GSTIN=27AAAAA0000A2ZV
GST_07_USER=jivotest_mh27
GST_07_PASS=` + testPass + `

GST_08_STATE=Delhi ISD
GST_08_GSTIN=07AAAAA0000A2ZX
GST_08_USER=Jivotest_ISD
GST_08_PASS=` + testPass + `
`
	if err := os.WriteFile(p, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("GST_ENV", p)
	return p
}

func loadTestRegs(t *testing.T) []Registration {
	t.Helper()
	writeTestEnv(t)
	regs, err := loadRegistrations()
	if err != nil {
		t.Fatalf("loadRegistrations: %v", err)
	}
	return regs
}

func TestLoadRegistrationsFromTempEnv(t *testing.T) {
	regs := loadTestRegs(t)
	if len(regs) != 8 {
		t.Fatalf("loaded %d registrations, want 8", len(regs))
	}
	if regs[0].Idx != "01" || regs[0].State != "Haryana" || regs[0].GSTIN != "06AAAAA0000A1Z0" {
		t.Errorf("first registration = %+v", regs[0])
	}
	// quotes stripped, `export ` prefix tolerated
	if regs[1].User != "jivotest_rj08" || regs[1].Pass != testPass {
		t.Errorf("quoted values not unquoted: %q / %q", regs[1].User, regs[1].Pass)
	}
	// blocks come back in index order
	for i, r := range regs {
		want := []string{"01", "02", "03", "04", "05", "06", "07", "08"}[i]
		if r.Idx != want {
			t.Errorf("registration %d has Idx %q want %q", i, r.Idx, want)
		}
	}
}

// An env var always beats the .env file (house precedence: flag > env > .env).
func TestEnvVarOverridesDotenv(t *testing.T) {
	writeTestEnv(t)
	t.Setenv("GST_01_USER", "from-the-environment")
	regs, err := loadRegistrations()
	if err != nil {
		t.Fatal(err)
	}
	if regs[0].User != "from-the-environment" {
		t.Errorf("env var did not win: %q", regs[0].User)
	}
}

// A half-filled block is a config error naming the missing variables — never a
// silently-skipped registration.
func TestIncompleteBlockIsConfigError(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, ".env")
	os.WriteFile(p, []byte("GST_01_STATE=Haryana\nGST_01_GSTIN=06AAAAA0000A1Z0\nGST_01_USER=x\n"), 0o600)
	t.Setenv("GST_ENV", p)
	_, err := loadRegistrations()
	if err == nil {
		t.Fatal("expected a config error for the missing GST_01_PASS")
	}
	if exitCodeFor(err) != exitConfig {
		t.Errorf("exit code = %d want %d (config)", exitCodeFor(err), exitConfig)
	}
	if !strings.Contains(err.Error(), "GST_01_PASS") {
		t.Errorf("error should name the missing var, got: %v", err)
	}
}

func TestNoEnvFileIsConfigError(t *testing.T) {
	t.Setenv("GST_ENV", filepath.Join(t.TempDir(), "nope.env"))
	t.Setenv("HOME", t.TempDir())
	if _, err := loadRegistrations(); err == nil {
		t.Fatal("expected a config error when no registrations are configured")
	} else if exitCodeFor(err) != exitConfig {
		t.Errorf("exit code = %d want %d (config)", exitCodeFor(err), exitConfig)
	}
}

func TestSelectByStateAliases(t *testing.T) {
	regs := loadTestRegs(t)
	cases := []struct{ sel, want string }{
		{"haryana", "06AAAAA0000A1Z0"},
		{"HARYANA", "06AAAAA0000A1Z0"},
		{"hr", "06AAAAA0000A1Z0"},
		{"06", "06AAAAA0000A1Z0"},
		{"Delhi", "07AAAAA0000A1ZY"},
		{"Delhi ISD", "07AAAAA0000A2ZX"},
		{"delhi-isd", "07AAAAA0000A2ZX"},
		{"maharashtra", "27AAAAA0000A2ZV"},
		{"mh", "27AAAAA0000A2ZV"},
		{"Himachal Pradesh", "02AAAAA0000A1Z8"},
	}
	for _, c := range cases {
		got, err := selectRegistrations(regs, "", c.sel, "", false)
		if err != nil {
			t.Errorf("--state %q: %v", c.sel, err)
			continue
		}
		if len(got) != 1 || got[0].GSTIN != c.want {
			t.Errorf("--state %q selected %v want %s", c.sel, gstins(got), c.want)
		}
	}

	// an unknown state is a usage error that lists what IS configured
	_, err := selectRegistrations(regs, "", "kerala", "", false)
	if err == nil || exitCodeFor(err) != exitUsage {
		t.Fatalf("--state kerala should be a usage error, got %v", err)
	}
	if !strings.Contains(err.Error(), "Haryana") {
		t.Errorf("unknown-state error should list the configured states, got: %v", err)
	}

	// "07" matches Delhi AND Delhi ISD — ambiguity must be reported, not guessed
	_, err = selectRegistrations(regs, "", "07", "", false)
	if err == nil || exitCodeFor(err) != exitUsage {
		t.Fatalf("--state 07 is ambiguous and must be a usage error, got %v", err)
	}
	if !strings.Contains(err.Error(), "07AAAAA0000A1ZY") || !strings.Contains(err.Error(), "07AAAAA0000A2ZX") {
		t.Errorf("ambiguity error should name both candidates, got: %v", err)
	}
}

func TestSelectByGSTINAndAll(t *testing.T) {
	regs := loadTestRegs(t)
	got, err := selectRegistrations(regs, "09AAAAA0000A1ZU", "", "", false)
	if err != nil || len(got) != 1 || got[0].State != "Uttar Pradesh" {
		t.Fatalf("--gstin selection = %v, %v", gstins(got), err)
	}
	// case-insensitive, whitespace-tolerant
	got, err = selectRegistrations(regs, " 09aaaaa0000a1zu ", "", "", false)
	if err != nil || len(got) != 1 {
		t.Fatalf("--gstin should be case/space tolerant: %v", err)
	}
	if _, err := selectRegistrations(regs, "99AAAAA0000A1Z9", "", "", false); err == nil {
		t.Error("an unconfigured GSTIN must be a usage error")
	}
	all, err := selectRegistrations(regs, "", "", "", true)
	if err != nil || len(all) != 8 {
		t.Fatalf("--all selected %d want 8 (%v)", len(all), err)
	}
}

func TestNoSelectorIsUsageError(t *testing.T) {
	regs := loadTestRegs(t)
	_, err := selectRegistrations(regs, "", "", "", false)
	if err == nil {
		t.Fatal("no selector must be an error — never guess a registration")
	}
	if exitCodeFor(err) != exitUsage {
		t.Errorf("exit code = %d want %d (usage)", exitCodeFor(err), exitUsage)
	}
	for _, want := range []string{"--gstin", "--state", "--all", "06AAAAA0000A1Z0"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("the no-selector error should mention %q; got: %v", want, err)
		}
	}
	// GST_DEFAULT fills in when the operator has one
	got, err := selectRegistrations(regs, "", "", "rajasthan", false)
	if err != nil || len(got) != 1 || got[0].State != "Rajasthan" {
		t.Fatalf("GST_DEFAULT=rajasthan selection = %v, %v", gstins(got), err)
	}
}

// No error message, anywhere in config handling, may contain a password.
func TestNoCredentialInConfigErrors(t *testing.T) {
	regs := loadTestRegs(t)
	var msgs []string
	for _, sel := range []string{"kerala", "07", ""} {
		if _, err := selectRegistrations(regs, "", sel, "", false); err != nil {
			msgs = append(msgs, err.Error())
		}
	}
	if _, err := selectRegistrations(regs, "99AAAAA0000A1Z9", "", "", false); err != nil {
		msgs = append(msgs, err.Error())
	}
	for _, m := range msgs {
		if strings.Contains(m, testPass) {
			t.Fatalf("a config error leaked the password: %q", m)
		}
	}
	// and the human summary line used by `auth list`
	for _, r := range regs {
		line := r.summary()
		if strings.Contains(line, testPass) {
			t.Fatalf("registration summary leaked the password: %q", line)
		}
		if !strings.Contains(line, "…") && !strings.Contains(line, "present") {
			t.Errorf("registration summary should show a masked credential: %q", line)
		}
	}
}

func gstins(rs []Registration) []string {
	out := make([]string, 0, len(rs))
	for _, r := range rs {
		out = append(out, r.GSTIN)
	}
	return out
}
