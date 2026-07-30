package config_test

import (
	"errors"
	"path/filepath"
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
