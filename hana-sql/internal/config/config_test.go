package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeEnv(t *testing.T, body string) string {
	t.Helper()
	dir := t.TempDir()
	p := filepath.Join(dir, "hana.env")
	if err := os.WriteFile(p, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	return p
}

func TestLoadFromFile(t *testing.T) {
	p := writeEnv(t, `# JIVO HANA
HANA_HOST = 127.0.0.1
HANA_PORT=47301
HANA_USER=ZIA
HANA_PASSWORD=hunter2

`)
	c, err := Load(p)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if c.Addr() != "127.0.0.1:47301" {
		t.Fatalf("Addr = %q", c.Addr())
	}
	if c.User != "ZIA" || c.Password != "hunter2" {
		t.Fatalf("got user=%q", c.User)
	}
	if c.EnvFile != p {
		t.Fatalf("EnvFile = %q, want %q", c.EnvFile, p)
	}
}

// The container is configured with plain env vars, so the process environment
// must win over whatever file happens to be lying around.
func TestProcessEnvironmentOverridesTheFile(t *testing.T) {
	p := writeEnv(t, "HANA_HOST=file-host\nHANA_PORT=1\nHANA_USER=file-user\nHANA_PASSWORD=file-pw\n")
	t.Setenv("HANA_HOST", "172.16.1.1")
	t.Setenv("HANA_PORT", "30015")

	c, err := Load(p)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if c.Addr() != "172.16.1.1:30015" {
		t.Fatalf("Addr = %q, want the process environment to win", c.Addr())
	}
	if c.User != "file-user" {
		t.Fatalf("User = %q, want the file value for keys the environment did not set", c.User)
	}
}

func TestPortDefaultsTo30015(t *testing.T) {
	p := writeEnv(t, "HANA_HOST=h\nHANA_USER=u\nHANA_PASSWORD=p\n")
	c, err := Load(p)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if DefaultPort != "30015" {
		t.Fatalf("DefaultPort = %q, want the SAP B1 tenant port 30015", DefaultPort)
	}
	if c.Port != DefaultPort {
		t.Fatalf("Port = %q, want the %s default when the file omits it", c.Port, DefaultPort)
	}
}

// A missing file is fine when the environment supplies everything (the
// container case), and an error when it does not.
func TestMissingFile(t *testing.T) {
	missing := filepath.Join(t.TempDir(), "nope.env")

	if _, err := Load(missing); err == nil {
		t.Fatal("Load on a missing file with an empty environment should fail")
	} else if !strings.Contains(err.Error(), missing) {
		t.Fatalf("error should name the path it tried: %v", err)
	}

	t.Setenv("HANA_HOST", "172.16.1.1")
	t.Setenv("HANA_USER", "ZIA")
	t.Setenv("HANA_PASSWORD", "pw")
	c, err := Load(missing)
	if err != nil {
		t.Fatalf("Load with a full environment and no file: %v", err)
	}
	if c.EnvFile != "" {
		t.Fatalf("EnvFile = %q, want empty when nothing was read from a file", c.EnvFile)
	}
}

func TestValidateNamesTheMissingKeyOnly(t *testing.T) {
	cases := []struct {
		c    Config
		want string
	}{
		{Config{User: "u", Password: "p"}, "HANA_HOST"},
		{Config{Host: "h", Password: "p"}, "HANA_USER"},
		{Config{Host: "h", User: "u"}, "HANA_PASSWORD"},
	}
	for _, tc := range cases {
		err := tc.c.Validate()
		if err == nil || !strings.Contains(err.Error(), tc.want) {
			t.Fatalf("Validate(%+v) = %v, want it to name %s", tc.c, err, tc.want)
		}
		// and never the value
		if err != nil && strings.Contains(err.Error(), "p") && strings.Contains(err.Error(), "secret") {
			t.Fatalf("Validate leaked a value: %v", err)
		}
	}
}

func TestMaskedPassword(t *testing.T) {
	c := &Config{Password: "hunter2"}
	if got := c.MaskedPassword(); got != "**** (set)" {
		t.Fatalf("MaskedPassword = %q", got)
	}
	if strings.Contains(c.MaskedPassword(), "hunter2") {
		t.Fatal("MaskedPassword leaked the value")
	}
	if got := (&Config{}).MaskedPassword(); got != "(not set)" {
		t.Fatalf("MaskedPassword with no password = %q", got)
	}
}

func TestScrub(t *testing.T) {
	c := &Config{Password: "S3cr3t!"}
	in := `hdb: authentication failed for user ZIA (password S3cr3t! rejected)`
	out := c.Scrub(in)
	if strings.Contains(out, "S3cr3t!") {
		t.Fatalf("Scrub left the password in: %q", out)
	}
	if !strings.Contains(out, "****") {
		t.Fatalf("Scrub = %q, want the value replaced by ****", out)
	}

	// A pathologically short password must not turn every message into stars.
	short := &Config{Password: "a"}
	if got := short.Scrub("banana"); got != "banana" {
		t.Fatalf("Scrub with a 1-char password mangled the text: %q", got)
	}

	if got := c.ScrubErr(nil); got != "" {
		t.Fatalf("ScrubErr(nil) = %q, want empty", got)
	}
}

func TestFindPrecedence(t *testing.T) {
	if got := Find("/explicit/path.env"); got != "/explicit/path.env" {
		t.Fatalf("Find(explicit) = %q", got)
	}
	t.Setenv("HANA_ENV", "/from/env.env")
	if got := Find(""); got != "/from/env.env" {
		t.Fatalf("Find() = %q, want $HANA_ENV", got)
	}
	// The explicit flag still beats the environment variable.
	if got := Find("/explicit/path.env"); got != "/explicit/path.env" {
		t.Fatalf("Find(explicit) = %q, want the flag to win over $HANA_ENV", got)
	}
}

// Walking up for connections/hana.env is the historical behaviour the whole
// repo relies on; it must keep working.
func TestFindWalksUp(t *testing.T) {
	t.Setenv("HANA_ENV", "")
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, "connections"), 0o755); err != nil {
		t.Fatal(err)
	}
	want := filepath.Join(root, "connections", "hana.env")
	if err := os.WriteFile(want, []byte("HANA_HOST=h\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	deep := filepath.Join(root, "a", "b", "c")
	if err := os.MkdirAll(deep, 0o755); err != nil {
		t.Fatal(err)
	}
	old, _ := os.Getwd()
	t.Cleanup(func() { os.Chdir(old) })
	if err := os.Chdir(deep); err != nil {
		t.Fatal(err)
	}
	got := Find("")
	// macOS temp dirs are symlinked through /private, so compare resolved paths.
	gotR, _ := filepath.EvalSymlinks(got)
	wantR, _ := filepath.EvalSymlinks(want)
	if gotR != wantR {
		t.Fatalf("Find() = %q, want %q", got, want)
	}
}

func TestParseEnvFileIgnoresCommentsAndBlanks(t *testing.T) {
	p := writeEnv(t, "# comment\n\n  \nA=1\nB = two \n#C=3\nD=has=equals\n")
	m, err := ParseEnvFile(p)
	if err != nil {
		t.Fatal(err)
	}
	want := map[string]string{"A": "1", "B": "two", "D": "has=equals"}
	if len(m) != len(want) {
		t.Fatalf("parsed %v, want %v", m, want)
	}
	for k, v := range want {
		if m[k] != v {
			t.Fatalf("%s = %q, want %q", k, m[k], v)
		}
	}
}
