package engine

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// buildInto runs a real end-to-end build of a testdata selection into a temp
// file, so no test leaves a credential zip in distribution/dist.
func buildInto(t *testing.T, selectionFile string) (*Result, string) {
	t.Helper()
	root := testRepoRoot(t)
	sel := loadSelection(t, root, selectionFile)
	out := filepath.Join(t.TempDir(), "bundle.zip")
	res, err := Build(root, sel, Options{OutPath: out, Now: fixedTime})
	if err != nil {
		t.Fatalf("Build(%s): %v", selectionFile, err)
	}
	return res, out
}

// TestBuildEndToEnd is the seam PLAN.md §6.8 describes, checked from the
// finished artefact rather than from staging.
func TestBuildEndToEnd(t *testing.T) {
	res, out := buildInto(t, "mac-min.json")

	st, err := os.Stat(out)
	if err != nil {
		t.Fatal(err)
	}
	if res.SizeBytes != st.Size() {
		t.Errorf("reported size %d, file is %d", res.SizeBytes, st.Size())
	}
	sum, err := SHA256File(out)
	if err != nil {
		t.Fatal(err)
	}
	if res.SHA256 != sum {
		t.Errorf("reported sha256 does not match the file on disk")
	}
	if res.BundleID == "" || !strings.HasPrefix(res.DownloadURL, "/api/bundle/") {
		t.Errorf("bad result identity: %+v", res)
	}

	entries, err := ReadZipEntries(out)
	if err != nil {
		t.Fatal(err)
	}
	modes := map[string]os.FileMode{}
	for _, e := range entries {
		if strings.HasSuffix(e.Name, "/") {
			continue
		}
		modes[strings.TrimPrefix(e.Name, BundleRoot+"/")] = e.Mode.Perm()
	}

	// Exec bits, re-read from the archive.
	for _, bin := range []string{"hana-sql/hana-sql", "jsap-cli/jsap-cli"} {
		if modes[bin]&0o111 == 0 {
			t.Errorf("%s is not executable in the finished zip (mode %04o)", bin, modes[bin])
		}
	}
	// Credentials locked down.
	for _, env := range []string{".env", "connections/hana.env", "connections/hana-tunnel.env"} {
		if modes[env] != 0o600 {
			t.Errorf("%s mode in the zip = %04o, want 0600", env, modes[env])
		}
	}
	if modes["README.txt"] != 0o644 {
		t.Errorf("README.txt mode = %04o, want 0644", modes["README.txt"])
	}

	if err := AssertZipClean(out); err != nil {
		t.Error(err)
	}

	// The README must actually be in there and mention the recipient.
	readme, err := ZipFileContent(out, "README.txt")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(readme), "karanpreet") {
		t.Error("README does not name the recipient")
	}
}

// TestBuiltEnvIsScopedToTheSelection re-reads the .env out of the finished zip
// and asserts it carries only this selection's keys. Key names only — no value
// is ever read into a test.
func TestBuiltEnvIsScopedToTheSelection(t *testing.T) {
	_, out := buildInto(t, "mac-min.json")
	content, err := ZipFileContent(out, ".env")
	if err != nil {
		t.Fatal(err)
	}
	keys := envKeysOf(content)
	if len(keys) == 0 {
		t.Fatal("bundled .env has no keys")
	}
	for _, k := range keys {
		if !strings.HasPrefix(k, "JSAP_") {
			t.Errorf("a hana+jsap bundle must carry only JSAP_* keys, found %s", k)
		}
	}
	for _, forbidden := range []string{"OMS_", "SAPB1_", "EXIM_", "TPAY_", "ECOM_", "JIVO_FACTORY_"} {
		for _, k := range keys {
			if strings.HasPrefix(k, forbidden) {
				t.Errorf("bundle leaked a %s key", forbidden)
			}
		}
	}
}

// TestFullBundleCarriesNoSecretItShouldNot is PLAN.md §7.5, run against the
// widest possible selection.
func TestFullBundleCarriesNoSecretItShouldNot(t *testing.T) {
	if testing.Short() {
		t.Skip("full bundle build is slow")
	}
	_, out := buildInto(t, "mac-all.json")

	entries, err := ReadZipEntries(out)
	if err != nil {
		t.Fatal(err)
	}
	forbidden := []string{
		"lovepreet-veerji.env", "token.json", "all-env.txt", "env-vault",
		"recon/", "captures/", ".git/", "fleet-access.env", "__pycache__", ".pyc", ".DS_Store",
	}
	for _, e := range entries {
		for _, f := range forbidden {
			if strings.Contains(e.Name, f) {
				t.Errorf("full bundle contains %s (matched %q)", e.Name, f)
			}
		}
	}
	// The hash-pinned identity files must be byte-identical to the repo copies.
	root := testRepoRoot(t)
	for _, rel := range []string{
		"product-identity/v1/release-attestation.json",
		"product-identity/v1/product-identity-map.json",
	} {
		want, err := os.ReadFile(filepath.Join(root, rel))
		if err != nil {
			t.Fatal(err)
		}
		got, err := ZipFileContent(out, rel)
		if err != nil {
			t.Fatal(err)
		}
		if len(got) != len(want) || string(got) != string(want) {
			t.Errorf("%s was not copied byte-for-byte — every `product` command would fail closed", rel)
		}
	}
}

// TestBuildLeavesGitClean: a bundle is a pile of production credentials, and
// nothing it writes may ever become committable.
func TestBuildLeavesGitClean(t *testing.T) {
	root := testRepoRoot(t)
	before := gitStatus(t, root)

	sel := loadSelection(t, root, "mac-min.json")
	res, err := Build(root, sel, Options{Now: time.Now(), KeepStaging: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		os.Remove(res.ZipPath)
		os.RemoveAll(filepath.Join(root, StagingDir, res.BundleID))
	})

	if !strings.HasPrefix(res.ZipPath, filepath.Join(root, DistDir)) {
		t.Errorf("default output landed outside %s: %s", DistDir, res.ZipPath)
	}
	after := gitStatus(t, root)
	if before != after {
		t.Errorf("a build changed what git sees.\nbefore:\n%s\nafter:\n%s", before, after)
	}

	// The staged tree really was kept, and is itself ignored.
	staged := filepath.Join(root, StagingDir, res.BundleID, "README.txt")
	if _, err := os.Stat(staged); err != nil {
		t.Errorf("-keep-staging did not keep the tree: %v", err)
	}
	if err := exec.Command("git", "-C", root, "check-ignore", "-q", "--",
		filepath.Join(StagingDir, res.BundleID, "README.txt")).Run(); err != nil {
		t.Error("the kept staging tree is not gitignored")
	}
}

// TestBuildStagesOutsideTheRepoByDefault — secrets cannot be committed from a
// directory git has never heard of.
func TestBuildStagesOutsideTheRepoByDefault(t *testing.T) {
	root := testRepoRoot(t)
	stage, cleanup, err := makeStaging(root, "test-id", false)
	if err != nil {
		t.Fatal(err)
	}
	defer cleanup()
	if strings.HasPrefix(stage, root) {
		t.Errorf("default staging %s is inside the repo", stage)
	}
	if filepath.Base(stage) != BundleRoot {
		t.Errorf("staging root should be named %s, got %s", BundleRoot, filepath.Base(stage))
	}
	cleanup()
	if _, err := os.Stat(stage); !os.IsNotExist(err) {
		t.Error("temporary staging was not removed")
	}
}

func TestBuildRejectsBadSelections(t *testing.T) {
	root := testRepoRoot(t)
	out := filepath.Join(t.TempDir(), "x.zip")
	for _, sel := range []Selection{
		{Target: "mac-arm64", Components: []string{"does-not-exist"}},
		{Target: "mac-arm64"},
		{Target: "amiga", Components: []string{"hana-sql"}},
	} {
		if _, err := Build(root, sel, Options{OutPath: out, Now: fixedTime}); err == nil {
			t.Errorf("expected an error for %+v", sel)
		}
	}
}

func TestBundleFilename(t *testing.T) {
	const id = "20260810-1430-a1b2"
	got := bundleFilename(Selection{Target: "mac-arm64", Recipient: "Karanpreet Singh"}, id)
	if got != "jivo-kit-mac-arm64-20260810-1430-a1b2-karanpreet-singh.zip" {
		t.Errorf("filename = %s", got)
	}
	if got := bundleFilename(Selection{Target: "windows", Recipient: "../../etc"}, id); strings.Contains(got, "/") {
		t.Errorf("a path-traversal recipient leaked into the filename: %s", got)
	}
	if got := bundleFilename(Selection{Target: "windows"}, id); got != "jivo-kit-windows-20260810-1430-a1b2-kit.zip" {
		t.Errorf("filename without a recipient = %s", got)
	}
}

// TestRebuildDoesNotOverwriteTheEarlierBundle: two kits for the same person in
// the same minute used to land on the same filename, so the second silently
// destroyed the first — which the operator may already have sent. The random
// suffix alone only makes that unlikely; Build re-mints until the name is free.
func TestRebuildDoesNotOverwriteTheEarlierBundle(t *testing.T) {
	root := testRepoRoot(t)
	sel := loadSelection(t, root, "mac-min.json")

	first, err := Build(root, sel, Options{Now: fixedTime})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { os.Remove(first.ZipPath) })

	second, err := Build(root, sel, Options{Now: fixedTime})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { os.Remove(second.ZipPath) })

	if first.ZipPath == second.ZipPath {
		t.Fatalf("both builds wrote to %s", first.ZipPath)
	}
	if first.BundleID == second.BundleID {
		t.Errorf("both builds share bundle id %s", first.BundleID)
	}
	for _, res := range []*Result{first, second} {
		if _, err := os.Stat(res.ZipPath); err != nil {
			t.Errorf("%s is gone: %v", filepath.Base(res.ZipPath), err)
		}
		if BundleIDFromFilename(filepath.Base(res.ZipPath)) != res.BundleID {
			t.Errorf("id %s is not recoverable from %s", res.BundleID, filepath.Base(res.ZipPath))
		}
	}
}

// TestBundleIDIsRecoverableFromEveryFilename covers the recipient shapes that
// could otherwise break the embedded id.
func TestBundleIDIsRecoverableFromEveryFilename(t *testing.T) {
	const id = "20260810-1430-a1b2"
	for _, recipient := range []string{"karanpreet", "Karanpreet Singh", "", "a-b_c", "../../etc", "JIVO201"} {
		name := bundleFilename(Selection{Target: "mac-arm64", Recipient: recipient}, id)
		if got := BundleIDFromFilename(name); got != id {
			t.Errorf("recipient %q -> %s -> id %q, want %q", recipient, name, got, id)
		}
	}
}

func TestBundleIDFromFilename(t *testing.T) {
	cases := map[string]string{
		"jivo-kit-mac-arm64-20260810-1430-a1b2-karanpreet.zip": "20260810-1430-a1b2",
		"jivo-kit-windows-20260810-1430-00ff-kit.zip":          "20260810-1430-00ff",
		"handmade.zip": "",
		"test.zip":     "",
	}
	for name, want := range cases {
		if got := BundleIDFromFilename(name); got != want {
			t.Errorf("%s -> %q, want %q", name, got, want)
		}
	}
}

func TestScopeWarnings(t *testing.T) {
	in := []string{"applies everywhere", "[windows] windows only", "[mac-arm64] mac only", "[unclosed bracket"}
	got := scopeWarnings(in, "windows")
	if len(got) != 3 || got[1] != "windows only" {
		t.Errorf("windows scope = %q", got)
	}
	got = scopeWarnings(in, "mac-arm64")
	if len(got) != 3 || got[1] != "mac only" {
		t.Errorf("mac scope = %q", got)
	}
}

// TestDSRWarningReachesTheOperator: the whole point of the degrade path is that
// nobody discovers the blank template by running dsr.
func TestDSRWarningReachesTheOperator(t *testing.T) {
	root := testRepoRoot(t)
	if _, err := os.Stat(filepath.Join(root, "distribution", "secrets.local.env")); err == nil {
		t.Skip("secrets.local.env exists on this machine, so DSR credentials are available")
	}
	out := filepath.Join(t.TempDir(), "dsr.zip")
	res, err := Build(root, Selection{
		Target: "mac-arm64", Components: []string{"dsr-cli"}, Recipient: "test", IncludeDocs: true,
	}, Options{OutPath: out, Now: fixedTime})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(strings.Join(res.Warnings, " "), "blank template") {
		t.Errorf("no blank-template warning in the result: %v", res.Warnings)
	}
	env, err := ZipFileContent(out, "dsr-cli/.env")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(env), "TEMPLATE ONLY") {
		t.Error("the shipped dsr-cli/.env does not announce that it is a template")
	}
	readme, err := ZipFileContent(out, "README.txt")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(flat(string(readme)), "blank template") {
		t.Error("the README does not repeat the blank-template warning to the recipient")
	}
}
