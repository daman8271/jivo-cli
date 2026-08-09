package engine

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jivodist/internal/manifest"
)

// ---------------------------------------------------------------- M2: atomic

// TestZipIsWrittenAtomically: a half-written credential zip must never appear
// under its final name, where it would be listed and sent.
func TestZipIsWrittenAtomically(t *testing.T) {
	stage := t.TempDir()
	if err := os.WriteFile(filepath.Join(stage, "f.txt"), []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	dst := filepath.Join(t.TempDir(), "bundle.zip")
	if err := WriteZip(stage, dst); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(dst); err != nil {
		t.Fatalf("final zip missing: %v", err)
	}
	if _, err := os.Stat(dst + TmpSuffix); !os.IsNotExist(err) {
		t.Error("the .tmp file survived a successful write")
	}
}

// TestFailedZipLeavesNothingBehind — a symlink in the staging tree is refused
// mid-write, which is exactly when a partial file would be left.
func TestFailedZipLeavesNothingBehind(t *testing.T) {
	stage := t.TempDir()
	real := filepath.Join(stage, "real.txt")
	if err := os.WriteFile(real, []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(real, filepath.Join(stage, "link.txt")); err != nil {
		t.Skipf("symlinks unavailable: %v", err)
	}
	dst := filepath.Join(t.TempDir(), "bundle.zip")
	if err := WriteZip(stage, dst); err == nil {
		t.Fatal("expected the write to fail")
	}
	for _, p := range []string{dst, dst + TmpSuffix} {
		if _, err := os.Stat(p); !os.IsNotExist(err) {
			t.Errorf("%s was left behind after a failed write", filepath.Base(p))
		}
	}
}

func TestIsPartial(t *testing.T) {
	if !IsPartial("jivo-kit-mac-arm64-20260810-1430-a1b2-x.zip.tmp") {
		t.Error(".zip.tmp should be partial")
	}
	if IsPartial("jivo-kit-mac-arm64-20260810-1430-a1b2-x.zip") {
		t.Error(".zip should not be partial")
	}
}

// ------------------------------------------------------------- M4: empty kit

// TestEmptySelectionForTargetFails: a zip containing only a README is not a
// bundle, and handing one to an operator to send is worse than an error.
func TestEmptySelectionForTargetFails(t *testing.T) {
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()

	// oms-cli's MCP server has only a mac binary, and that binary is not built
	// on this machine — so on its own it ships nothing to either target.
	fake := &manifest.Manifest{
		Components: []manifest.Component{{
			ID: "postsql", Distributable: true, UIName: "x", UIDescription: "x",
			Tools: []manifest.Tool{{
				Name:         "postsql",
				Binaries:     []manifest.Binary{{OS: "linux", Path: "postsql/postsql-linux"}},
				OfflineCheck: "x",
			}},
		}},
		Lessons: m.Lessons,
	}
	_, _, _, err = ShipList(root, home, fake, []string{"postsql"}, "windows", true)
	if err == nil {
		t.Fatal("a selection with nothing for the target should fail")
	}
	if !strings.Contains(err.Error(), "selection contains nothing for target") {
		t.Errorf("error should say the selection is empty for the target, got: %v", err)
	}
}

// ------------------------------------------------------ M6: no silent default

// TestUnknownComponentHasNoAuthDefault — defaulting to baked-env would print
// "Ready to use" for a component whose credentials nobody has thought about.
func TestUnknownComponentHasNoAuthDefault(t *testing.T) {
	if HasEnvPlan("brand-new-cli") {
		t.Fatal("test assumes this component does not exist")
	}
	if got := AuthMode("brand-new-cli"); got != AuthUnconfigured {
		t.Errorf("AuthMode of an unplanned component = %q, want %q", got, AuthUnconfigured)
	}
	if got := AuthMode("brand-new-cli"); got == AuthBakedEnv {
		t.Error("an unplanned component must never claim baked-env")
	}
	if note := AuthNote("brand-new-cli"); !strings.Contains(note, "envbake.go") {
		t.Errorf("the note should say where to add the plan, got %q", note)
	}
	if strings.Contains(authHeadline(AuthUnconfigured), "Ready to use") {
		t.Error("the unconfigured headline must not promise readiness")
	}
}

// TestBuildRefusesComponentWithoutEnvPlan — loud, not silent.
func TestBuildRefusesComponentWithoutEnvPlan(t *testing.T) {
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	fake := &manifest.Manifest{
		Components: []manifest.Component{{
			ID: "brand-new-cli", Distributable: true, UIName: "x", UIDescription: "x",
			Tools: []manifest.Tool{{
				Name:         "brand-new-cli",
				Binaries:     []manifest.Binary{{OS: "mac-arm64", Path: "hana-sql/hana-sql", Exists: true}},
				OfflineCheck: "x",
			}},
		}},
		Lessons: m.Lessons,
	}
	_, _, _, err = ShipList(root, home, fake, []string{"brand-new-cli"}, "mac-arm64", true)
	if err == nil {
		t.Fatal("a component with no env plan must not build")
	}
	if !strings.Contains(err.Error(), "no env plan") || !strings.Contains(err.Error(), "envbake.go") {
		t.Errorf("error should name the gap and where to fix it, got: %v", err)
	}
}

// TestEveryDistributableComponentHasAnEnvPlan is the regression that keeps the
// loud failure above from ever firing in production.
func TestEveryDistributableComponentHasAnEnvPlan(t *testing.T) {
	m, err := manifest.Load(testRepoRoot(t))
	if err != nil {
		t.Fatal(err)
	}
	for _, c := range m.Distributable() {
		if !HasEnvPlan(c.ID) {
			t.Errorf("%s is offered in the UI but has no row in envPlan (PLAN.md §5)", c.ID)
		}
	}
}

// ------------------------------------------------------- m1: containment

func TestValidZipPathRefusesEscapes(t *testing.T) {
	bad := []string{
		"../outside.txt",
		"sap-b1/../../etc/passwd",
		"/etc/passwd",
		"",
		"a/../../b",
	}
	for _, p := range bad {
		if err := ValidZipPath(p); err == nil {
			t.Errorf("ValidZipPath(%q) should have failed", p)
		}
	}
	good := []string{".env", "sap-b1/cli/.env", "product-identity/v1/sources/jid-registry.json", "README.txt"}
	for _, p := range good {
		if err := ValidZipPath(p); err != nil {
			t.Errorf("ValidZipPath(%q) = %v", p, err)
		}
	}
}

// TestStagingRefusesEscapingPath: the check is repeated at the join itself, so
// a future manifest edit cannot write outside the staging tree.
func TestStagingRefusesEscapingPath(t *testing.T) {
	stage := t.TempDir()
	err := stageFiles(testRepoRoot(t), stage, []StagedFile{
		{ZipPath: "../escaped.txt", Mode: 0o644, Content: []byte("x")},
	})
	if err == nil {
		t.Fatal("staging accepted a path outside the bundle root")
	}
	if _, statErr := os.Stat(filepath.Join(filepath.Dir(stage), "escaped.txt")); statErr == nil {
		t.Error("a file was written outside the staging tree")
	}
}

// ------------------------------------------------- m2: deny-list case folding

// TestDenyListIsCaseInsensitive — APFS is case-insensitive, so Token.json is
// the same file as token.json and must not slip past the gate.
func TestDenyListIsCaseInsensitive(t *testing.T) {
	for _, p := range []string{
		"exim/.secrets/Token.json",
		"exim/.secrets/TOKEN.JSON",
		"sap-b1/cli/Lovepreet-Veerji.env",
		"ecom-cli/.ds_store",
		"ecom-cli/.DS_Store",
		"jsap-cli/jsap/__PYCACHE__/cli.pyc",
		"jsap-cli/jsap/cli.PYC",
		"Env-Vault/all-env.txt",
		"control-panel/RECON/cookies.txt",
		"connections/Fleet-Access.env",
	} {
		if _, denied := Denied(p); !denied {
			t.Errorf("%s slipped past the deny list", p)
		}
	}
	// Still not over-matching.
	for _, p := range []string{"sap-b1/cli/.env", "hana-sql/README.md", "postsql/config.toml.INSTALL"} {
		if pattern, denied := Denied(p); denied {
			t.Errorf("%s wrongly denied by %s", p, pattern)
		}
	}
}

// ------------------------------------------------------------- F1: estimates

// TestEstimatedSizeDeduplicates: product-identity is nominated by two
// components and ecom-cli nominates its own binary twice, which over-reported
// the full kit by about a fifth before every click.
func TestEstimatedSizeDeduplicates(t *testing.T) {
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

	// ShipList already dedupes, so the estimate over its output must equal the
	// sum of the distinct staged files.
	var want int64
	for _, f := range Dedupe(files) {
		if f.Content != nil {
			want += int64(len(f.Content))
			continue
		}
		p := f.Src
		if !filepath.IsAbs(p) {
			p = filepath.Join(root, f.Src)
		}
		if st, statErr := os.Stat(p); statErr == nil {
			want += st.Size()
		}
	}
	if got := EstimatedSize(root, files); got != want {
		t.Errorf("EstimatedSize = %d, want %d", got, want)
	}

	// And a list with duplicates must not double-count.
	dup := append(append([]StagedFile{}, files...), files...)
	if got := EstimatedSize(root, dup); got != want {
		t.Errorf("EstimatedSize double-counted duplicates: %d, want %d", got, want)
	}
}

// TestComponentEstimateMatchesWhatIsStaged compares the number shown in the UI
// against the bytes actually written for one component.
func TestComponentEstimateMatchesWhatIsStaged(t *testing.T) {
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	c, ok := m.Component("jivo-scraping-cli")
	if !ok {
		t.Fatal("component missing")
	}
	res := ResolveComponent(root, home, c, "mac-arm64", true)
	estimate := EstimatedSize(root, res.Files)

	stage := t.TempDir()
	if err := stageFiles(root, stage, Dedupe(res.Files)); err != nil {
		t.Fatal(err)
	}
	var staged int64
	err = filepath.Walk(stage, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			staged += info.Size()
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if estimate != staged {
		t.Errorf("estimate %d bytes vs %d actually staged (%.0f%% off)",
			estimate, staged, 100*float64(estimate-staged)/float64(staged))
	}
}

// ------------------------------------------------------------- F2 / F5 / M3

// TestJsapShipsToWindows — the corrected manifest entry must actually put jsap
// in a Windows kit, package and all.
func TestJsapShipsToWindows(t *testing.T) {
	root := testRepoRoot(t)
	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	files, skipped, _, err := ShipList(root, home, m, []string{"jsap-cli"}, "windows", true)
	if err != nil {
		t.Fatalf("jsap should now build for windows: %v", err)
	}
	for _, s := range skipped {
		t.Errorf("nothing should be skipped: %+v", s)
	}
	want := []string{
		"jsap-cli/jsap-cli",
		"jsap-cli/jsap/cli.py",
		"jsap-cli/jsap/__main__.py",
		"jsap-cli/jsap/modules/bills.py",
		"jsap-cli/README.md",
		".env",
	}
	got := map[string]StagedFile{}
	for _, f := range files {
		got[f.ZipPath] = f
	}
	for _, w := range want {
		if _, ok := got[w]; !ok {
			t.Errorf("windows jsap kit is missing %s", w)
		}
	}
	if got["jsap-cli/jsap-cli"].Kind != KindBinary {
		t.Error("the launcher should be staged as a binary (0755)")
	}
}

// TestWindowsRunInstructionsUseWindowsPaths — mixing separators in the same
// instruction is how a recipient ends up typing a path that does not exist.
func TestWindowsRunInstructionsUseWindowsPaths(t *testing.T) {
	if got := bundlePath("windows", "sap-b1/accounts-kit"); got != `C:\jivo-cli\sap-b1\accounts-kit` {
		t.Errorf("windows bundle path = %q", got)
	}
	if got := bundlePath("mac-arm64", "sap-b1/cli"); got != "~/jivo-cli/sap-b1/cli" {
		t.Errorf("mac bundle path = %q", got)
	}
	if got := bundlePath("windows", ""); got != `C:\jivo-cli` {
		t.Errorf("windows root = %q", got)
	}
}

// TestSapRunDirIsPerTarget: the Windows exe and its .env live in
// accounts-kit/, not cli/ — sending a Windows recipient to cli/ points them at
// a folder with no credentials and no binary in it.
func TestSapRunDirIsPerTarget(t *testing.T) {
	if got := RunDir("sap-b1", "windows"); got != "sap-b1/accounts-kit" {
		t.Errorf("windows sap-b1 run dir = %q, want sap-b1/accounts-kit", got)
	}
	if got := RunDir("sap-b1", "mac-arm64"); got != "sap-b1/cli" {
		t.Errorf("mac sap-b1 run dir = %q, want sap-b1/cli", got)
	}
	if got := RunDir("jsap-cli", "windows"); got != "jsap-cli" {
		t.Errorf("jsap run dir = %q", got)
	}
	if got := RunDir("hana-sql", "mac-arm64"); got != "" {
		t.Errorf("hana-sql needs no run dir, got %q", got)
	}
}

// TestWindowsReadmeSendsPeopleToFoldersThatExist walks every cd instruction in
// a real Windows bundle's README and checks the folder is actually in the zip.
func TestWindowsReadmeSendsPeopleToFoldersThatExist(t *testing.T) {
	root := testRepoRoot(t)
	sel := loadSelection(t, root, "win-all.json")
	out := filepath.Join(t.TempDir(), "win.zip")
	if _, err := Build(root, sel, Options{OutPath: out, Now: fixedTime}); err != nil {
		t.Fatal(err)
	}
	entries, err := ReadZipEntries(out)
	if err != nil {
		t.Fatal(err)
	}
	dirs := map[string]bool{}
	for _, e := range entries {
		rel := strings.TrimPrefix(e.Name, BundleRoot+"/")
		for {
			i := strings.LastIndex(rel, "/")
			if i < 0 {
				break
			}
			rel = rel[:i]
			dirs[rel] = true
		}
	}

	m, err := manifest.Load(root)
	if err != nil {
		t.Fatal(err)
	}
	for _, c := range m.Distributable() {
		dir := RunDir(c.ID, "windows")
		if dir == "" {
			continue
		}
		if !dirs[dir] {
			continue // component not in this kit
		}
		var hasEnv, hasBinary bool
		for _, e := range entries {
			rel := strings.TrimPrefix(e.Name, BundleRoot+"/")
			if filepath.ToSlash(filepath.Dir(rel)) != dir {
				continue
			}
			base := filepath.Base(rel)
			if strings.HasSuffix(base, ".env") {
				hasEnv = true
			}
			if e.Mode.Perm()&0o111 != 0 && !strings.HasSuffix(e.Name, "/") {
				hasBinary = true
			}
		}
		if !hasEnv && !hasBinary {
			t.Errorf("%s: the README says `cd %s`, but that folder holds neither credentials nor a binary", c.ID, dir)
		}
	}
}
