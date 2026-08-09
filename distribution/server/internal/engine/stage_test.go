package engine

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jivodist/internal/manifest"
)

var update = flag.Bool("update", false, "rewrite the golden ship lists in distribution/testdata/golden")

func loadSelection(t *testing.T, root, name string) Selection {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join(root, "distribution", "testdata", name))
	if err != nil {
		t.Fatal(err)
	}
	var s Selection
	if err := json.Unmarshal(raw, &s); err != nil {
		t.Fatal(err)
	}
	return s
}

func goldenPath(root, name string) string {
	return filepath.Join(root, "distribution", "testdata", "golden", name)
}

// checkGolden compares got against the stored golden, or rewrites it under
// -update. Ship lists are paths only — never contents — so a golden can be read
// by anyone without leaking a credential.
func checkGolden(t *testing.T, root, name, got string) {
	t.Helper()
	p := goldenPath(root, name)
	if *update {
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte(got), 0o644); err != nil {
			t.Fatal(err)
		}
		t.Logf("wrote golden %s", p)
		return
	}
	want, err := os.ReadFile(p)
	if err != nil {
		t.Fatalf("golden %s missing (run: go test ./internal/engine -update): %v", name, err)
	}
	if string(want) == got {
		return
	}
	t.Errorf("ship list for %s changed", name)
	for _, line := range diffLines(strings.Split(string(want), "\n"), strings.Split(got, "\n")) {
		t.Error("  " + line)
	}
}

func diffLines(want, got []string) []string {
	inGot := map[string]bool{}
	for _, g := range got {
		inGot[g] = true
	}
	inWant := map[string]bool{}
	for _, w := range want {
		inWant[w] = true
	}
	var out []string
	for _, w := range want {
		if !inGot[w] {
			out = append(out, "- "+w)
		}
	}
	for _, g := range got {
		if !inWant[g] {
			out = append(out, "+ "+g)
		}
	}
	if len(out) > 40 {
		out = append(out[:40], fmt.Sprintf("... and %d more", len(out)-40))
	}
	return out
}

func shipListReport(t *testing.T, root string, sel Selection) string {
	t.Helper()
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	files, skipped, _, err := ShipList(root, home, m, sel.Components, sel.Target, sel.IncludeDocs)
	if err != nil {
		t.Fatalf("ShipList: %v", err)
	}
	var b strings.Builder
	for _, f := range files {
		fmt.Fprintf(&b, "%-4s %04o %s\n", f.Kind, f.Mode.Perm(), f.ZipPath)
	}
	b.WriteString("--- skipped ---\n")
	for _, s := range skipped {
		fmt.Fprintf(&b, "%s / %s: %s\n", s.Component, s.Tool, s.Reason)
	}
	return b.String()
}

// TestGoldenShipLists is the allowlist's proof. If anyone replaces the resolver
// with a directory copy, these lists explode with hundreds of extra paths.
func TestGoldenShipLists(t *testing.T) {
	root := testRepoRoot(t)
	for _, name := range []string{"mac-all.json", "win-all.json", "mac-min.json", "win-accounts.json"} {
		t.Run(name, func(t *testing.T) {
			sel := loadSelection(t, root, name)
			checkGolden(t, root, strings.TrimSuffix(name, ".json")+".shiplist.txt", shipListReport(t, root, sel))
		})
	}
}

// TestMacMinMatchesPlanLayout pins PLAN.md §4's worked example file-for-file.
func TestMacMinMatchesPlanLayout(t *testing.T) {
	root := testRepoRoot(t)
	sel := loadSelection(t, root, "mac-min.json")
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	files, _, _, err := ShipList(root, home, m, sel.Components, sel.Target, sel.IncludeDocs)
	if err != nil {
		t.Fatal(err)
	}
	got := map[string]StagedFile{}
	for _, f := range files {
		got[f.ZipPath] = f
	}
	for _, want := range []string{
		".env",
		"connections/hana.env",
		"connections/hana-tunnel.env",
		"hana-sql/hana-sql",
		"hana-sql/README.md",
		"hana-sql/MCP.md",
		"hana-sql/queries/turnover-oil-july.sql",
		"jsap-cli/jsap-cli",
		"jsap-cli/README.md",
		"jsap-cli/tests/test_readonly.py",
		"jsap-cli/jsap/cli.py",
		"jsap-cli/jsap/modules/bills.py",
	} {
		if _, ok := got[want]; !ok {
			t.Errorf("PLAN §4 example is missing %s", want)
		}
	}
	for p, wantMode := range map[string]os.FileMode{
		"hana-sql/hana-sql":           0o755,
		"jsap-cli/jsap-cli":           0o755,
		"connections/hana.env":        0o600,
		"connections/hana-tunnel.env": 0o600,
		".env":                        0o600,
	} {
		if got[p].Mode.Perm() != wantMode {
			t.Errorf("%s mode = %04o, want %04o", p, got[p].Mode.Perm(), wantMode)
		}
	}
	// No credential belonging to another component may travel.
	for p := range got {
		for _, forbidden := range []string{"sap-b1/", "oms-cli/", "control-panel/", "portals/"} {
			if strings.HasPrefix(p, forbidden) {
				t.Errorf("hana+jsap bundle carries %s, which belongs to another component", p)
			}
		}
	}
}

// TestNoPycacheOrJunkAnywhere: the Python packages ship whole, so the deny list
// is what keeps __pycache__ and .DS_Store out.
func TestNoPycacheOrJunkAnywhere(t *testing.T) {
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	sel := loadSelection(t, root, "mac-all.json")
	files, _, _, err := ShipList(root, home, m, sel.Components, sel.Target, sel.IncludeDocs)
	if err != nil {
		t.Fatal(err)
	}
	if len(files) == 0 {
		t.Fatal("empty ship list")
	}
	for _, f := range files {
		if pattern, bad := Denied(f.ZipPath); bad {
			t.Errorf("%s reached the ship list (matches %s)", f.ZipPath, pattern)
		}
	}
	// The Python package really did expand, or the check above proves nothing.
	var pkg int
	for _, f := range files {
		if strings.HasPrefix(f.ZipPath, "jivo-scraping-cli/jivo_scrape/") {
			pkg++
		}
	}
	if pkg < 10 {
		t.Errorf("jivo_scrape package expanded to %d files, expected the whole package", pkg)
	}
}

// TestWindowsRejectsNTFSIllegalNames asserts rather than silently dropping.
func TestWindowsRejectsNTFSIllegalNames(t *testing.T) {
	err := AssertWindowsSafe([]StagedFile{
		{ZipPath: "sap-b1/README.md"},
		{ZipPath: "sap-b1/vault/services/Entities:.md"},
	})
	if err == nil {
		t.Fatal("expected the colon in Entities:.md to be rejected")
	}
	if !strings.Contains(err.Error(), "Entities:.md") {
		t.Errorf("error should name the file, got: %v", err)
	}
	if err := AssertWindowsSafe([]StagedFile{{ZipPath: "sap-b1/README.md"}}); err != nil {
		t.Errorf("clean list should pass: %v", err)
	}
}

// TestWindowsFullSelectionIsExtractable is the live version of the check: the
// real Windows ship list must contain nothing NTFS refuses.
func TestWindowsFullSelectionIsExtractable(t *testing.T) {
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	sel := loadSelection(t, root, "win-all.json")
	files, skipped, _, err := ShipList(root, home, m, sel.Components, sel.Target, sel.IncludeDocs)
	if err != nil {
		t.Fatalf("windows ship list: %v", err)
	}
	if err := AssertWindowsSafe(files); err != nil {
		t.Error(err)
	}
	// The known Windows gaps must be reported, not silently absent.
	want := []string{"jivo-ecom-pp-mcp", "jivo-factory-pp-mcp", "amazon-portal", "flipkart-portal", "swiggy-instamart-portal"}
	var joined string
	for _, s := range skipped {
		joined += s.Tool + "|"
	}
	for _, w := range want {
		if !strings.Contains(joined, w) {
			t.Errorf("expected %s in the skipped list for windows; got %q", w, joined)
		}
	}
	// dsr's generated .env must sit next to dsr.exe.
	var haveDSREnv, haveDSRExe bool
	for _, f := range files {
		switch f.ZipPath {
		case "dsr-cli/.env":
			haveDSREnv = true
		case "dsr-cli/dsr.exe":
			haveDSRExe = true
		}
	}
	if !haveDSREnv || !haveDSRExe {
		t.Errorf("windows dsr bundle incomplete: .env=%v exe=%v", haveDSREnv, haveDSRExe)
	}
}

// TestSelectionErrors covers the 400 cases.
func TestSelectionErrors(t *testing.T) {
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	cases := []struct {
		name       string
		components []string
		target     string
		wantSubstr string
	}{
		{"unknown component", []string{"nope"}, "mac-arm64", "unknown component"},
		{"empty selection", nil, "mac-arm64", "empty selection"},
		{"bad target", []string{"hana-sql"}, "solaris", "unknown target"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, _, _, err := ShipList(root, home, m, tc.components, tc.target, true)
			if err == nil || !strings.Contains(err.Error(), tc.wantSubstr) {
				t.Errorf("want error containing %q, got %v", tc.wantSubstr, err)
			}
		})
	}
}

// TestDedupeKeepsExecBit: ecom-cli's MCP tool lists the CLI binary as a
// companion file. If the companion entry won, the binary would ship 0644.
func TestDedupeKeepsExecBit(t *testing.T) {
	out := Dedupe([]StagedFile{
		{ZipPath: "ecom-cli/jivo-ecom-pp-cli", Mode: 0o644, Kind: KindData},
		{ZipPath: "ecom-cli/jivo-ecom-pp-cli", Mode: 0o755, Kind: KindBinary},
	})
	if len(out) != 1 {
		t.Fatalf("want 1 entry, got %d", len(out))
	}
	if out[0].Mode.Perm() != 0o755 {
		t.Errorf("mode = %04o, want 0755", out[0].Mode.Perm())
	}
}

func TestExpandCompanionStripsAnnotation(t *testing.T) {
	root := testRepoRoot(t)
	got := expandCompanion(root, "product-identity/v1/release-attestation.json (digest pinned in identity.py; must ship byte-identical)")
	if len(got) != 1 || got[0].ZipPath != "product-identity/v1/release-attestation.json" {
		t.Errorf("annotation not stripped: %+v", got)
	}
}
