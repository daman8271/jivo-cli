package config_test

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

func clearSAPB1Env(t *testing.T) {
	t.Helper()
	for _, k := range []string{
		"SAPB1_HOST", "SAPB1_PORT", "SAPB1_COMPANYDB", "SAPB1_USER",
		"SAPB1_PASSWORD", "SAPB1_INSECURE", "SAPB1_TIMEOUT",
	} {
		t.Setenv(k, "")
	}
}

func TestLoadDefaults(t *testing.T) {
	clearSAPB1Env(t)

	cfg, err := config.Load(config.Flags{})
	if err != nil {
		t.Fatalf("Load returned error: %v", err)
	}
	if cfg.Port != config.DefaultPort {
		t.Errorf("Port = %d, want default %d", cfg.Port, config.DefaultPort)
	}
	if cfg.Timeout != config.DefaultTimeout {
		t.Errorf("Timeout = %d, want default %d", cfg.Timeout, config.DefaultTimeout)
	}
	if cfg.Insecure {
		t.Errorf("Insecure = true, want default false")
	}
	if cfg.Host != "" || cfg.CompanyDB != "" || cfg.User != "" || cfg.Password != "" {
		t.Errorf("expected blank connection fields with no env set, got %+v", cfg)
	}
}

func TestLoadFromEnv(t *testing.T) {
	clearSAPB1Env(t)
	t.Setenv("SAPB1_HOST", "envhost")
	t.Setenv("SAPB1_PORT", "12345")
	t.Setenv("SAPB1_COMPANYDB", "ENVDB")
	t.Setenv("SAPB1_USER", "envuser")
	t.Setenv("SAPB1_PASSWORD", "envpass")
	t.Setenv("SAPB1_INSECURE", "true")
	t.Setenv("SAPB1_TIMEOUT", "45")

	cfg, err := config.Load(config.Flags{})
	if err != nil {
		t.Fatalf("Load returned error: %v", err)
	}
	if cfg.Host != "envhost" {
		t.Errorf("Host = %q, want envhost", cfg.Host)
	}
	if cfg.Port != 12345 {
		t.Errorf("Port = %d, want 12345", cfg.Port)
	}
	if cfg.CompanyDB != "ENVDB" {
		t.Errorf("CompanyDB = %q, want ENVDB", cfg.CompanyDB)
	}
	if cfg.User != "envuser" {
		t.Errorf("User = %q, want envuser", cfg.User)
	}
	if cfg.Password != "envpass" {
		t.Errorf("Password mismatch (not checking value on purpose in real usage, but here we're verifying plumbing)")
	}
	if !cfg.Insecure {
		t.Errorf("Insecure = false, want true")
	}
	if cfg.Timeout != 45 {
		t.Errorf("Timeout = %d, want 45", cfg.Timeout)
	}
}

func TestFlagsOverrideEnv(t *testing.T) {
	clearSAPB1Env(t)
	t.Setenv("SAPB1_HOST", "envhost")
	t.Setenv("SAPB1_PORT", "111")
	t.Setenv("SAPB1_COMPANYDB", "ENVDB")
	t.Setenv("SAPB1_USER", "envuser")
	t.Setenv("SAPB1_PASSWORD", "envpass")
	t.Setenv("SAPB1_INSECURE", "false")
	t.Setenv("SAPB1_TIMEOUT", "10")

	cfg, err := config.Load(config.Flags{
		Host:        "flaghost",
		HostSet:     true,
		Port:        9999,
		PortSet:     true,
		Company:     "FLAGDB",
		CompanySet:  true,
		User:        "flaguser",
		UserSet:     true,
		Insecure:    true,
		InsecureSet: true,
		Timeout:     5,
		TimeoutSet:  true,
		JSON:        true,
	})
	if err != nil {
		t.Fatalf("Load returned error: %v", err)
	}
	if cfg.Host != "flaghost" {
		t.Errorf("Host = %q, want flaghost (flag should win over env)", cfg.Host)
	}
	if cfg.Port != 9999 {
		t.Errorf("Port = %d, want 9999", cfg.Port)
	}
	if cfg.CompanyDB != "FLAGDB" {
		t.Errorf("CompanyDB = %q, want FLAGDB", cfg.CompanyDB)
	}
	if cfg.User != "flaguser" {
		t.Errorf("User = %q, want flaguser", cfg.User)
	}
	if !cfg.Insecure {
		t.Errorf("Insecure = false, want true (flag should win)")
	}
	if cfg.Timeout != 5 {
		t.Errorf("Timeout = %d, want 5", cfg.Timeout)
	}
	if !cfg.JSON {
		t.Errorf("JSON = false, want true")
	}
	// There is no --password flag by design; env value must survive untouched.
	if cfg.Password != "envpass" {
		t.Errorf("Password should still come from env (no flag exists for it)")
	}
}

func TestInvalidPortIsConfigError(t *testing.T) {
	clearSAPB1Env(t)
	t.Setenv("SAPB1_PORT", "not-a-number")

	_, err := config.Load(config.Flags{})
	if err == nil {
		t.Fatal("expected error for invalid SAPB1_PORT")
	}
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("expected *errs.ConfigError, got %T: %v", err, err)
	}
}

func TestValidateConnection(t *testing.T) {
	cfg := &config.Config{}
	err := cfg.ValidateConnection()
	if err == nil {
		t.Fatal("expected error for empty config")
	}
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("expected *errs.ConfigError, got %T", err)
	}

	cfg = &config.Config{Host: "h", User: "u", Password: "p"}
	if err := cfg.ValidateConnection(); err != nil {
		t.Errorf("expected no error with host/user/password set, got %v", err)
	}
}

func TestValidateCompanyDB(t *testing.T) {
	cfg := &config.Config{}
	err := cfg.ValidateCompanyDB()
	if err == nil {
		t.Fatal("expected error for empty CompanyDB")
	}
	want := "company database not set — set SAPB1_COMPANYDB in .env or pass --company. Ask your SAP admin for the CompanyDB name"
	if err.Error() != want {
		t.Errorf("error message = %q, want %q", err.Error(), want)
	}
}

func TestMaskedPasswordNeverLeaksRealValue(t *testing.T) {
	cfg := &config.Config{Password: "super-secret-value"}
	masked := cfg.MaskedPassword()
	if masked == cfg.Password {
		t.Fatal("MaskedPassword returned the real password")
	}
	if masked != "****" {
		t.Errorf("MaskedPassword() = %q, want ****", masked)
	}

	empty := &config.Config{}
	if empty.MaskedPassword() != "(not set)" {
		t.Errorf("MaskedPassword() on empty password = %q, want (not set)", empty.MaskedPassword())
	}
}

func TestBaseURLAndHostPort(t *testing.T) {
	cfg := &config.Config{Host: "10.0.0.5", Port: 50000}
	if got, want := cfg.BaseURL(), "https://10.0.0.5:50000/b1s/v1/"; got != want {
		t.Errorf("BaseURL() = %q, want %q", got, want)
	}
	if got, want := cfg.HostPort(), "10.0.0.5:50000"; got != want {
		t.Errorf("HostPort() = %q, want %q", got, want)
	}
}

// TestSessionCachePathForIsPerIdentity pins the property the per-identity
// cache exists for: two connections that differ in ANY of host, port,
// companyDB or user must get different files, and the same identity must
// always get the same one. Sharing a file across companies is what forces a
// re-Login on every company switch.
func TestSessionCachePathForIsPerIdentity(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)

	base := struct {
		host      string
		port      int
		companyDB string
		user      string
	}{"10.0.0.5", 50000, "JIVO_OIL_HANADB", "manager"}

	pathOf := func(host string, port int, db, user string) string {
		t.Helper()
		p, err := config.SessionCachePathFor(host, port, db, user)
		if err != nil {
			t.Fatalf("SessionCachePathFor: %v", err)
		}
		if filepath.Dir(p) != home {
			t.Errorf("cache path %q is not under HOME %q", p, home)
		}
		return p
	}

	basePath := pathOf(base.host, base.port, base.companyDB, base.user)

	// Stable for the same identity.
	if again := pathOf(base.host, base.port, base.companyDB, base.user); again != basePath {
		t.Errorf("same identity produced two paths:\n %s\n %s", basePath, again)
	}

	cases := []struct {
		name            string
		host            string
		port            int
		companyDB, user string
	}{
		{"different company", base.host, base.port, "JIVO_MART_HANADB", base.user},
		{"third company", base.host, base.port, "JIVO_BEVERAGES_HANADB", base.user},
		{"different host", "10.0.0.6", base.port, base.companyDB, base.user},
		{"different port", base.host, 47500, base.companyDB, base.user},
		{"different user", base.host, base.port, base.companyDB, "auditor"},
	}
	seen := map[string]string{basePath: "base"}
	for _, tc := range cases {
		p := pathOf(tc.host, tc.port, tc.companyDB, tc.user)
		if other, dup := seen[p]; dup {
			t.Errorf("%s collides with %s on path %s", tc.name, other, p)
		}
		seen[p] = tc.name
	}

	// The company name stays readable in the filename; the user does not.
	if !strings.Contains(filepath.Base(basePath), "jivo-oil-hanadb") {
		t.Errorf("cache filename %q should carry the company slug", filepath.Base(basePath))
	}
	if strings.Contains(filepath.Base(basePath), base.user) {
		t.Errorf("cache filename %q must not embed the username", filepath.Base(basePath))
	}
	if !strings.HasSuffix(basePath, ".json") {
		t.Errorf("cache path %q should end in .json", basePath)
	}

	// A blank company still yields a usable, non-ambiguous name.
	blank := pathOf(base.host, base.port, "", base.user)
	if blank == basePath {
		t.Error("a blank companyDB must not collide with a named one")
	}
	if strings.Contains(filepath.Base(blank), "--") {
		t.Errorf("blank company produced a malformed name: %s", filepath.Base(blank))
	}
}

// TestWriteLogPath covers both sources of the write-audit-log path: the
// SAPB1_WRITE_LOG override (used by tests and by anyone who wants the log
// somewhere shared) and the ~/.sapb1-writes.jsonl default. Paths are built with
// filepath.Join so this passes on Windows too, where the accounts-kit binary runs.
func TestWriteLogPath(t *testing.T) {
	custom := filepath.Join(t.TempDir(), "custom-writes.jsonl")
	t.Setenv("SAPB1_WRITE_LOG", custom)
	got, err := config.WriteLogPath()
	if err != nil {
		t.Fatalf("WriteLogPath: %v", err)
	}
	if got != custom {
		t.Errorf("WriteLogPath() = %q, want the SAPB1_WRITE_LOG value %q", got, custom)
	}

	home := t.TempDir()
	t.Setenv("SAPB1_WRITE_LOG", "")
	t.Setenv("HOME", home)        // unix
	t.Setenv("USERPROFILE", home) // windows
	got, err = config.WriteLogPath()
	if err != nil {
		t.Fatalf("WriteLogPath: %v", err)
	}
	if want := filepath.Join(home, ".sapb1-writes.jsonl"); got != want {
		t.Errorf("WriteLogPath() = %q, want %q", got, want)
	}
}

// TestWriteTimeout — writes get a longer default than reads, but never override
// an explicit --timeout/SAPB1_TIMEOUT, however short.
func TestWriteTimeout(t *testing.T) {
	cases := []struct {
		name string
		cfg  config.Config
		want int
	}{
		{"default read timeout -> long write default", config.Config{Timeout: config.DefaultTimeout}, config.DefaultWriteTimeout},
		{"explicit short timeout wins", config.Config{Timeout: 7, TimeoutSet: true}, 7},
		{"explicit long timeout wins", config.Config{Timeout: 600, TimeoutSet: true}, 600},
		{"unset but generous default", config.Config{Timeout: 300}, 300},
	}
	for _, tc := range cases {
		if got := tc.cfg.WriteTimeout(); got != tc.want {
			t.Errorf("%s: WriteTimeout() = %d, want %d", tc.name, got, tc.want)
		}
	}
	if config.DefaultWriteTimeout <= config.DefaultTimeout {
		t.Error("the write default must be longer than the read default")
	}
}

// TestTimeoutSetTracksProvenance — WriteTimeout's behaviour depends on knowing
// whether the operator chose the timeout, so Load must record that.
func TestTimeoutSetTracksProvenance(t *testing.T) {
	t.Setenv("SAPB1_TIMEOUT", "")
	cfg, err := config.Load(config.Flags{})
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.TimeoutSet {
		t.Error("TimeoutSet should be false when nothing set it")
	}

	t.Setenv("SAPB1_TIMEOUT", "45")
	cfg, err = config.Load(config.Flags{})
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if !cfg.TimeoutSet || cfg.Timeout != 45 {
		t.Errorf("env timeout: got %d/%v, want 45/true", cfg.Timeout, cfg.TimeoutSet)
	}

	t.Setenv("SAPB1_TIMEOUT", "")
	cfg, err = config.Load(config.Flags{Timeout: 9, TimeoutSet: true})
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if !cfg.TimeoutSet || cfg.Timeout != 9 {
		t.Errorf("flag timeout: got %d/%v, want 9/true", cfg.Timeout, cfg.TimeoutSet)
	}
}

// TestWriteLogPathPrefersOperatorFolder pins the precedence that makes the
// write audit trail actually auditable: an explicit SAPB1_WRITE_LOG wins, then
// the registered operator's folder inside the checkout, and only then the home
// fallback. The middle case is the one that matters — a log that lands in the
// writer's home directory is readable by exactly the person it is meant to hold
// accountable.
func TestWriteLogPathPrefersOperatorFolder(t *testing.T) {
	repo := t.TempDir()
	if err := os.MkdirAll(filepath.Join(repo, "harness"), 0o755); err != nil {
		t.Fatal(err)
	}
	operator := filepath.Join(repo, "harness", ".operator")
	if err := os.WriteFile(operator, []byte(`{"name":"Param Singh","slug":"param-singh"}`), 0o600); err != nil {
		t.Fatal(err)
	}

	// Run from a subdirectory to prove the upward walk finds the checkout.
	sub := filepath.Join(repo, "sap-b1", "cli")
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	prev, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(prev)
	if err := os.Chdir(sub); err != nil {
		t.Fatal(err)
	}

	t.Setenv("SAPB1_WRITE_LOG", "")
	got, err := config.WriteLogPath()
	if err != nil {
		t.Fatalf("WriteLogPath: %v", err)
	}
	want := filepath.Join(repo, "queries", "param-singh", "sap-writes.jsonl")
	if gotResolved, err := filepath.EvalSymlinks(filepath.Dir(got)); err == nil {
		if wantResolved, err := filepath.EvalSymlinks(filepath.Dir(want)); err == nil {
			if gotResolved != wantResolved {
				t.Errorf("write log dir:\n got %s\nwant %s", gotResolved, wantResolved)
			}
		}
	}
	if filepath.Base(got) != "sap-writes.jsonl" {
		t.Errorf("write log basename = %q, want sap-writes.jsonl", filepath.Base(got))
	}

	// An explicit override must still win outright.
	t.Setenv("SAPB1_WRITE_LOG", "/tmp/explicit.jsonl")
	if got, _ := config.WriteLogPath(); got != "/tmp/explicit.jsonl" {
		t.Errorf("explicit override lost: got %s", got)
	}
}
