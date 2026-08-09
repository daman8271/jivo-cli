package engine

import (
	"os"
	"strings"
	"testing"
	"time"

	"jivodist/internal/manifest"
)

// fixedTime keeps the golden README deterministic.
var fixedTime = time.Date(2026, 8, 10, 14, 30, 0, 0, time.FixedZone("IST", 5*3600+1800))

func readmeFor(t *testing.T, selectionFile string) ([]byte, ReadmeInput) {
	t.Helper()
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	overrides, err := manifest.LoadOverrides(root)
	if err != nil {
		t.Fatal(err)
	}
	sel := loadSelection(t, root, selectionFile)
	home, _ := os.UserHomeDir()
	files, skipped, warnings, err := ShipList(root, home, m, sel.Components, sel.Target, sel.IncludeDocs)
	if err != nil {
		t.Fatal(err)
	}
	var included []string
	for _, id := range sel.Components {
		if toolIncluded(files, id) {
			included = append(included, id)
		}
	}
	warnings = CollectWarnings(overrides, included, files, sel.Target, warnings)
	in := ReadmeInput{
		Target:      sel.Target,
		Recipient:   sel.Recipient,
		BundleID:    "20260810-1430-a1b2",
		GeneratedAt: fixedTime,
		Manifest:    m,
		Components:  included,
		Files:       files,
		Skipped:     skipped,
		Warnings:    warnings,
		Overrides:   overrides,
	}
	return RenderReadme(in), in
}

// flat collapses the README's word wrapping so an assertion about a sentence
// does not break the moment a line rewraps.
func flat(s string) string { return strings.Join(strings.Fields(s), " ") }

// section returns one titled block of the README.
func section(text, title string) string {
	i := strings.Index(text, title)
	if i < 0 {
		return ""
	}
	rest := text[i+len(title):]
	if j := strings.Index(rest, "\n\n\n"); j > 0 {
		return rest[:j]
	}
	return rest
}

// TestGoldenReadme pins the 2-component example from PLAN.md §4, and the
// Windows accounts kit — the case where a component (sap-b1) has two tools and
// only one of them ships.
func TestGoldenReadme(t *testing.T) {
	for _, sel := range []string{"mac-min.json", "win-accounts.json"} {
		t.Run(sel, func(t *testing.T) {
			got, _ := readmeFor(t, sel)
			// Goldens are stored with LF so the diff is readable; the CRLF of a
			// Windows bundle is asserted separately in TestWindowsReadmeIsCRLF.
			checkGolden(t, testRepoRoot(t),
				strings.TrimSuffix(sel, ".json")+".README.txt",
				strings.ReplaceAll(string(got), "\r\n", "\n"))
		})
	}
}

// TestOfflineCheckIsPerTool: sap-b1 has two tools and only the accounts-kit one
// ships to Windows. A component-level check printed both, telling a Windows
// recipient to run `cd sap-b1/cli && ./sapb1 --help` against a binary that is
// not in their kit.
func TestOfflineCheckIsPerTool(t *testing.T) {
	win, _ := readmeFor(t, "win-accounts.json")
	text := flat(strings.ReplaceAll(string(win), "\r\n", "\n"))
	if !strings.Contains(text, "sapb1.exe --help") {
		t.Error("the Windows kit's own offline check is missing")
	}
	if strings.Contains(text, "cd <bundle>/sap-b1/cli && ./sapb1 --help") {
		t.Error("README prints the Mac tool's offline check in a Windows kit — the guard is not per-tool")
	}

	// mac-min has no sap-b1 component, so it gets no sap-b1 section at all.
	// (The "Accounts Mac: ./sap-b1/cli/sapb1 doctor" example in the team's
	// standing instructions is quoted verbatim in every kit and is labelled as
	// an example, so it is not what this checks.)
	mac, _ := readmeFor(t, "mac-min.json")
	if strings.Contains(string(mac), "SAP B1 (SAPB1)") {
		t.Error("mac-min rendered a sap-b1 component section it does not contain")
	}
}

// TestReadmeTellsTheTruthPerAuthMode is PLAN.md §8.3. Saying a credential is
// "ready to use" when the binary never reads the file is the exact silent
// failure this repo's lessons document.
func TestReadmeTellsTheTruthPerAuthMode(t *testing.T) {
	got, _ := readmeFor(t, "mac-all.json")
	text := flat(string(got))

	cases := []struct {
		component string
		mustSay   []string
		mustNot   []string
	}{
		{"ecom-cli", []string{"does NOT read the file", "auth login"}, nil},
		{"oms-cli", []string{"does NOT read the file"}, nil},
		{"factory-cli", []string{"does NOT read the file"}, nil},
		{"postsql", []string{"only from your home folder", "~/.postsql"}, nil},
		{"control-panel", []string{"--env-file"}, nil},
		{"portals", []string{"no long-lived credential can ship", "expire"}, nil},
		{"hana-sql", []string{"hana-tunnel.env"}, nil},
	}
	for _, tc := range cases {
		for _, want := range tc.mustSay {
			if !strings.Contains(text, want) {
				t.Errorf("%s: README should say %q", tc.component, want)
			}
		}
		for _, bad := range tc.mustNot {
			if strings.Contains(text, bad) {
				t.Errorf("%s: README must not say %q", tc.component, bad)
			}
		}
	}

	// Nothing in the kit is a repo checkout, so the harness instruction from
	// lessons.readme_must_say must be replaced, not repeated verbatim.
	if strings.Contains(text, "python3 harness/bin/setup.py") {
		t.Error("README tells the recipient to run harness/bin/setup.py, which is not in the bundle")
	}
	if !strings.Contains(text, ".sapb1-writes.jsonl") {
		t.Error("README should explain where the SAP write log actually lands outside a checkout")
	}

	// The non-negotiables from lessons.readme_must_say.
	for _, want := range []string{
		"LIVE CREDENTIALS",
		"xattr -dr com.apple.quarantine",
		"exit code 7",
		"FortiClient",
	} {
		if !strings.Contains(text, want) {
			t.Errorf("README is missing the required line about %q", want)
		}
	}
}

// TestReadmeChmodListIsTheActualStagedBinaries — a generic chmod line that
// names binaries the recipient does not have teaches them to ignore it.
func TestReadmeChmodListIsTheActualStagedBinaries(t *testing.T) {
	got, in := readmeFor(t, "mac-min.json")
	text := string(got)
	if !strings.Contains(text, "chmod +x") {
		t.Fatal("no chmod line")
	}
	for _, f := range in.Files {
		if f.Kind != KindBinary {
			continue
		}
		if !strings.Contains(text, "~/jivo-cli/"+f.ZipPath) {
			t.Errorf("chmod list is missing the staged binary %s", f.ZipPath)
		}
	}
	// And it must not name binaries that are not in this bundle.
	for _, absent := range []string{"sap-b1/cli/sapb1", "postsql/postsql", "oms-cli/oms-pp-cli"} {
		if strings.Contains(text, "~/jivo-cli/"+absent) {
			t.Errorf("chmod list names %s, which is not in this bundle", absent)
		}
	}
}

// TestWindowsReadmeIsCRLF: Notepad renders LF-only text as one long line. Only
// this generated file is translated.
func TestWindowsReadmeIsCRLF(t *testing.T) {
	win, _ := readmeFor(t, "win-accounts.json")
	if !strings.Contains(string(win), "\r\n") {
		t.Fatal("windows README has no CRLF line endings")
	}
	for i, r := range string(win) {
		if r == '\n' && (i == 0 || string(win)[i-1] != '\r') {
			t.Fatalf("bare LF at byte %d in the windows README", i)
		}
	}
	firstRun := section(strings.ReplaceAll(string(win), "\r\n", "\n"), "FIRST RUN")
	if strings.Contains(firstRun, "xattr") {
		t.Error("windows first-run steps should not include the macOS quarantine command")
	}
	if !strings.Contains(firstRun, `C:\jivo-cli`) {
		t.Error("windows first-run steps should say where to unzip")
	}

	mac, _ := readmeFor(t, "mac-min.json")
	if strings.Contains(string(mac), "\r\n") {
		t.Error("mac README must use LF only")
	}
}

// TestReadmeCarriesOverrideWarnings: the stale hana-sql.exe warning is only
// useful if it reaches the person holding the stale exe.
func TestReadmeCarriesOverrideWarnings(t *testing.T) {
	win, _ := readmeFor(t, "win-all.json")
	if !strings.Contains(string(win), "STALE") {
		t.Error("windows README should carry the stale hana-sql.exe warning")
	}
	mac, _ := readmeFor(t, "mac-min.json")
	if strings.Contains(string(mac), "hana-sql.exe is STALE") {
		t.Error("the stale-exe warning must not appear in a Mac bundle")
	}
}

// TestReadmeListsWhatWasLeftOut — a recipient should never discover a missing
// tool by trying to run it.
func TestReadmeListsWhatWasLeftOut(t *testing.T) {
	win, _ := readmeFor(t, "win-all.json")
	text := string(win)
	if !strings.Contains(text, "NOT IN THIS KIT") {
		t.Fatal("no skipped section")
	}
	for _, tool := range []string{"amazon-portal", "flipkart-portal", "jivo-factory-pp-mcp"} {
		if !strings.Contains(text, tool) {
			t.Errorf("skipped tool %s is not named in the README", tool)
		}
	}
}
