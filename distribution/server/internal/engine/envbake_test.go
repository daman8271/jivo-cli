package engine

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// fixtureRepo builds a throwaway repo tree with fake credentials, so no test
// ever reads, asserts on, or prints a real production value.
func fixtureRepo(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	write := func(rel, body string) {
		p := filepath.Join(root, filepath.FromSlash(rel))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(body), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	write(".env", strings.Join([]string{
		"# JSAP credentials",
		"JSAP_URL=https://example.invalid/jsap",
		"JSAP_USERNAME=fixture-user",
		"JSAP_PASSWORD=fixture-pass",
		"",
		"# OMS credentials",
		"OMS_URL=https://example.invalid/oms",
		"OMS_USERNAME=fixture-user",
		"OMS_PASSWORD=fixture-pass",
		"",
		"EXIM_EMAIL=fixture@example.invalid",
		"EXIM_PASSWORD=fixture-pass",
		"EXIM_API=https://example.invalid/exim-api",
		"EXIM_WEB=https://example.invalid/exim",
		"",
		"JIVO_FACTORY_WEB=https://example.invalid/factory",
		"JIVO_FACTORY_API=https://example.invalid/factory-api",
		"JIVO_FACTORY_EMAIL=fixture@example.invalid",
		"JIVO_FACTORY_PASSWORD=fixture-pass",
		"",
		"ECOM_URL=https://example.invalid/ecom",
		"ECOM_EMAIL=fixture@example.invalid",
		"ECOM_PASSWORD=fixture-pass",
		"JIVO_ECOM_TOKEN=fixture-token",
		"",
		"TPAY_USERNAME=fixture-user",
		"TPAY_PASSWORD=fixture-pass",
		"",
	}, "\n"))
	write("sap-b1/cli/.env", strings.Join([]string{
		"# SAP Business One Service Layer",
		"SAPB1_HOST=203.0.113.10",
		"SAPB1_PORT=50000",
		"SAPB1_COMPANYDB=JIVO_OIL_HANADB",
		"SAPB1_USER=fixture",
		"SAPB1_PASSWORD=fixture-pass",
		"SAPB1_INSECURE=true",
		"",
	}, "\n"))
	return root
}

// TestRootEnvIsAnAllowlist: a jsap-only bundle must not carry OMS, EXIM,
// factory, ecom or SAP credentials. This is the whole point of D5.
func TestRootEnvIsAnAllowlist(t *testing.T) {
	root := fixtureRepo(t)
	content, warnings, err := BakeRootEnv(root, []string{"jsap-cli"}, "mac-arm64")
	if err != nil {
		t.Fatal(err)
	}
	if len(warnings) != 0 {
		t.Errorf("unexpected warnings: %v", warnings)
	}
	keys := envKeysOf(content)
	wantExactly(t, keys, []string{"JSAP_URL", "JSAP_USERNAME", "JSAP_PASSWORD"})
	for _, forbidden := range []string{"OMS_", "EXIM_", "JIVO_FACTORY_", "ECOM_", "SAPB1_", "TPAY_"} {
		for _, k := range keys {
			if strings.HasPrefix(k, forbidden) {
				t.Errorf("jsap-only bundle leaked a %s key", forbidden)
			}
		}
	}
}

// TestRootEnvEximHasHardRequiredKeys: eximapi.py raises a KeyError at import
// time without EXIM_API and EXIM_WEB, so their absence must be loud.
func TestRootEnvEximHasHardRequiredKeys(t *testing.T) {
	root := fixtureRepo(t)
	content, warnings, err := BakeRootEnv(root, []string{"exim"}, "mac-arm64")
	if err != nil {
		t.Fatal(err)
	}
	keys := envKeysOf(content)
	for _, need := range []string{"EXIM_API", "EXIM_WEB", "EXIM_EMAIL", "EXIM_PASSWORD"} {
		if !containsString(keys, need) {
			t.Errorf("exim bundle is missing %s", need)
		}
	}
	if len(warnings) != 0 {
		t.Errorf("unexpected warnings: %v", warnings)
	}

	// Now remove them and prove the warning fires.
	stripped := filepath.Join(root, ".env")
	body, err := os.ReadFile(stripped)
	if err != nil {
		t.Fatal(err)
	}
	var kept []string
	for _, l := range strings.Split(string(body), "\n") {
		if strings.HasPrefix(l, "EXIM_API") || strings.HasPrefix(l, "EXIM_WEB") {
			continue
		}
		kept = append(kept, l)
	}
	if err := os.WriteFile(stripped, []byte(strings.Join(kept, "\n")), 0o600); err != nil {
		t.Fatal(err)
	}
	_, warnings, err = BakeRootEnv(root, []string{"exim"}, "mac-arm64")
	if err != nil {
		t.Fatal(err)
	}
	joined := strings.Join(warnings, " ")
	for _, need := range []string{"EXIM_API", "EXIM_WEB"} {
		if !strings.Contains(joined, need) {
			t.Errorf("missing %s should have produced a warning; got %v", need, warnings)
		}
	}
}

// TestRootEnvMultiComponentUnion: picking several components unions their
// prefixes and nothing more.
func TestRootEnvMultiComponentUnion(t *testing.T) {
	root := fixtureRepo(t)
	content, _, err := BakeRootEnv(root, []string{"jsap-cli", "oms-cli", "ecom-cli"}, "mac-arm64")
	if err != nil {
		t.Fatal(err)
	}
	keys := envKeysOf(content)
	wantExactly(t, keys, []string{
		"JSAP_URL", "JSAP_USERNAME", "JSAP_PASSWORD",
		"OMS_URL", "OMS_USERNAME", "OMS_PASSWORD",
		"ECOM_URL", "ECOM_EMAIL", "ECOM_PASSWORD", "JIVO_ECOM_TOKEN",
	})
}

// TestRootEnvSkippedForCredentiallessSelection: hana-sql keeps its credentials
// in connections/, so a hana-only bundle gets no root .env at all.
func TestRootEnvSkippedForCredentiallessSelection(t *testing.T) {
	root := fixtureRepo(t)
	content, _, err := BakeRootEnv(root, []string{"hana-sql", "postsql"}, "mac-arm64")
	if err != nil {
		t.Fatal(err)
	}
	if content != nil {
		t.Errorf("expected no root .env, got:\n%s", envKeysOf(content))
	}
}

// TestSapEnvKeepsInsecureFlag: without SAPB1_INSECURE=true the doctor dies with
// an x509 error against SAP's self-signed certificate.
func TestSapEnvKeepsInsecureFlag(t *testing.T) {
	root := fixtureRepo(t)
	lines, err := parseEnvKeys(filepath.Join(root, "sap-b1", "cli", ".env"))
	if err != nil {
		t.Fatal(err)
	}
	var found bool
	for _, l := range lines {
		if l.key == "SAPB1_INSECURE" {
			found = true
			if !strings.HasSuffix(strings.TrimSpace(l.raw), "=true") {
				t.Error("SAPB1_INSECURE must be true")
			}
		}
	}
	if !found {
		t.Error("SAPB1_INSECURE missing from the SAP env")
	}

	// The SAP env is copied whole, so it must never be filtered through the
	// root-.env prefix mechanism.
	if len(envPlan["sap-b1"].prefixes) != 0 {
		t.Error("sap-b1 must not draw keys from the repo-root .env")
	}
}

// TestSapEnvNeverStagesNamedOperatorFile: lovepreet-veerji.env is a real SAP
// login for a named user and must never leave this machine.
func TestSapEnvNeverStagesNamedOperatorFile(t *testing.T) {
	for _, cp := range envPlan["sap-b1"].copies {
		if strings.Contains(cp.src, "lovepreet") {
			t.Fatalf("sap-b1 stages %s", cp.src)
		}
	}
	if _, denied := Denied("sap-b1/cli/lovepreet-veerji.env"); !denied {
		t.Error("lovepreet-veerji.env is not on the deny list")
	}
}

// TestDSRDegradesToTemplate: no DSR credential exists anywhere in the repo or
// the env vault, so with no secrets.local.env the builder ships a blank
// template and says so — it never invents a value.
func TestDSRDegradesToTemplate(t *testing.T) {
	root := t.TempDir()
	content, warnings := BakeDSREnv(root)
	if len(warnings) == 0 {
		t.Error("expected a loud warning when DSR keys are absent")
	}
	if !strings.Contains(strings.Join(warnings, " "), "secrets.local.env") {
		t.Errorf("the warning should name the file to fill in; got %v", warnings)
	}
	body := string(content)
	if !strings.Contains(body, "TEMPLATE ONLY") {
		t.Error("template should say it is a template")
	}
	for _, k := range dsrKeys {
		if !strings.Contains(body, k+"=\n") {
			t.Errorf("%s should be present and blank", k)
		}
	}

	// With an overlay present, the values travel and the warning goes away.
	if err := os.MkdirAll(filepath.Join(root, "distribution"), 0o755); err != nil {
		t.Fatal(err)
	}
	overlay := "DSR_HOST=198.51.100.7\nDSR_USER=fixture\nDSR_PASSWORD=fixture-pass\nDSR_EXTRA=1\n"
	if err := os.WriteFile(filepath.Join(root, "distribution", "secrets.local.env"), []byte(overlay), 0o600); err != nil {
		t.Fatal(err)
	}
	content, warnings = BakeDSREnv(root)
	if len(warnings) != 0 {
		t.Errorf("unexpected warnings with an overlay present: %v", warnings)
	}
	keys := envKeysOf(content)
	for _, k := range []string{"DSR_HOST", "DSR_USER", "DSR_PASSWORD", "DSR_EXTRA", "DSR_PORT"} {
		if !containsString(keys, k) {
			t.Errorf("%s missing from the generated dsr-cli/.env", k)
		}
	}
	if strings.Contains(string(content), "TEMPLATE ONLY") {
		t.Error("a populated file should not claim to be a template")
	}
}

// TestPostsqlIsHomeConfigInstall pins the mode that stops the README from
// claiming postsql works out of the box.
func TestPostsqlIsHomeConfigInstall(t *testing.T) {
	if AuthMode("postsql") != AuthHomeConfig {
		t.Errorf("postsql auth mode = %s, want %s", AuthMode("postsql"), AuthHomeConfig)
	}
	var dst string
	for _, cp := range envPlan["postsql"].copies {
		dst = cp.dst
		if !strings.HasPrefix(cp.src, "~/") {
			t.Errorf("postsql source should be the out-of-repo home config, got %s", cp.src)
		}
	}
	if dst != "postsql/config.toml.INSTALL" {
		t.Errorf("postsql destination = %q, want postsql/config.toml.INSTALL — it must not look installed", dst)
	}
}

// TestAuthModesAreTheDeclaredFour: the UI renders a badge per mode, so an
// unknown value would render blank.
func TestAuthModesAreTheDeclaredFour(t *testing.T) {
	valid := map[string]bool{AuthBakedEnv: true, AuthLogin: true, AuthHomeConfig: true, AuthExternalToken: true}
	for id, spec := range envPlan {
		if !valid[spec.authMode] {
			t.Errorf("%s: auth mode %q is not one of the four the API contract declares", id, spec.authMode)
		}
		if spec.authNote == "" {
			t.Errorf("%s: no auth note — the README would state the mode with no explanation", id)
		}
	}
	// The tools that do not read a bundled .env must never claim baked-env.
	for _, id := range []string{"ecom-cli", "oms-cli", "factory-cli", "control-panel"} {
		if AuthMode(id) != AuthLogin {
			t.Errorf("%s should be %s: its binary does not read the bundled .env", id, AuthLogin)
		}
	}
	if AuthMode("portals") != AuthExternalToken {
		t.Errorf("portals should be %s", AuthExternalToken)
	}
	if !Sensitive("portals") {
		t.Error("portals carries TankhaPay payroll credentials and must be flagged sensitive")
	}
}

func TestResolveSrcHandlesHomePaths(t *testing.T) {
	got := resolveSrc("/repo", "/home/x", "~/.postsql/config.toml")
	if got != filepath.Join("/home/x", ".postsql", "config.toml") {
		t.Errorf("home path resolution = %s", got)
	}
	if got := resolveSrc("/repo", "/home/x", "control-panel/.env"); got != filepath.Join("/repo", "control-panel/.env") {
		t.Errorf("repo path resolution = %s", got)
	}
}

func TestParseEnvKeysIgnoresCommentsAndBlanks(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, ".env")
	body := "# a comment with a secret-looking token\n\nexport A_KEY=1\nB_KEY=2\nnot a kv line\n"
	if err := os.WriteFile(p, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	lines, err := parseEnvKeys(p)
	if err != nil {
		t.Fatal(err)
	}
	if len(lines) != 2 || lines[0].key != "A_KEY" || lines[1].key != "B_KEY" {
		t.Errorf("parsed %+v", lines)
	}
	if lines[0].raw != "A_KEY=1" {
		t.Errorf("the `export ` prefix should be dropped, got %q", lines[0].raw)
	}
}

// ------------------------------------------------------------------ helpers

// envKeysOf returns only the KEY names from generated env content. Tests assert
// on key names, never values.
func envKeysOf(content []byte) []string {
	var out []string
	for _, l := range strings.Split(string(content), "\n") {
		l = strings.TrimSpace(l)
		if l == "" || strings.HasPrefix(l, "#") {
			continue
		}
		if i := strings.Index(l, "="); i > 0 {
			out = append(out, l[:i])
		}
	}
	return out
}

func wantExactly(t *testing.T, got, want []string) {
	t.Helper()
	if len(got) != len(want) {
		t.Errorf("got %d keys %v, want %d %v", len(got), got, len(want), want)
		return
	}
	for _, w := range want {
		if !containsString(got, w) {
			t.Errorf("missing key %s (got %v)", w, got)
		}
	}
}
