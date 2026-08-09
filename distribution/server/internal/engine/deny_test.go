package engine

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestDenyListCatchesTheRealOffenders names, one by one, the files that have
// actually leaked or nearly leaked out of this repo.
func TestDenyListCatchesTheRealOffenders(t *testing.T) {
	denied := []string{
		"env-vault/all-env.txt",
		"env-vault",
		"exim/.secrets/token.json",
		"portals/blinkit/token.json",
		"sap-b1/cli/lovepreet-veerji.env",
		"control-panel/recon/cookies.txt",
		"portals/amazon/captures/page-01.har",
		"deep/nested/captures/x.json",
		".git/config",
		"sap-b1/.git/HEAD",
		"jsap-cli/jsap/__pycache__/cli.cpython-313.pyc",
		"jsap-cli/jsap/cli.pyc",
		".DS_Store",
		"ecom-cli/.DS_Store",
		"connections/fleet-access.env",
	}
	for _, p := range denied {
		if pattern, bad := Denied(p); !bad {
			t.Errorf("%s should be denied", p)
		} else if pattern == "" {
			t.Errorf("%s denied by an empty pattern", p)
		}
	}

	allowed := []string{
		"sap-b1/cli/.env",
		"sap-b1/cli/sapb1",
		"connections/hana.env",
		"connections/hana-tunnel.env",
		"exim/.secrets/README.txt",
		"jsap-cli/jsap/cli.py",
		"product-identity/v1/product-identity-map.json",
		"README.txt",
		".env",
		"portals/tankhapay/.env",
		"control-panel/.env",
		"postsql/config.toml.INSTALL",
	}
	for _, p := range allowed {
		if pattern, bad := Denied(p); bad {
			t.Errorf("%s must be allowed, was denied by %s", p, pattern)
		}
	}
}

// TestAssertCleanFailsOnASeededStagingTree proves the final gate is real: even
// if the allowlist were bypassed entirely, this stops the zip.
func TestAssertCleanFailsOnASeededStagingTree(t *testing.T) {
	stage := t.TempDir()
	write := func(rel string) {
		p := filepath.Join(stage, filepath.FromSlash(rel))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte("x"), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	write("sap-b1/cli/sapb1")
	write("sap-b1/cli/.env")
	if err := AssertClean(stage); err != nil {
		t.Fatalf("clean tree rejected: %v", err)
	}

	write("sap-b1/cli/lovepreet-veerji.env")
	write("exim/.secrets/token.json")
	err := AssertClean(stage)
	if err == nil {
		t.Fatal("gate did not fire on a poisoned staging tree")
	}
	for _, want := range []string{"lovepreet-veerji.env", "token.json"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("error should name %s; got %v", want, err)
		}
	}
}

func TestScanStagingSkipsDeniedDirectoriesWhole(t *testing.T) {
	stage := t.TempDir()
	p := filepath.Join(stage, "control-panel", "recon", "deep", "cookies.json")
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte("x"), 0o600); err != nil {
		t.Fatal(err)
	}
	found, err := ScanStaging(stage)
	if err != nil {
		t.Fatal(err)
	}
	if len(found) != 1 || found[0].Path != "control-panel/recon" {
		t.Errorf("expected the recon directory reported once, got %+v", found)
	}
}
