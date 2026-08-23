package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

// writeLogLines writes raw JSONL to path.
func writeLogLines(t *testing.T, path string, lines ...string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	if err := os.WriteFile(path, []byte(strings.Join(lines, "\n")+"\n"), 0o600); err != nil {
		t.Fatalf("write: %v", err)
	}
}

// creationLine renders the exact log line the guard looks for, so the near-miss
// table below can vary one field at a time from a known-good record.
func creationLine(t *testing.T, over map[string]interface{}) string {
	t.Helper()
	base := map[string]interface{}{
		"time":       time.Now().Format(time.RFC3339Nano),
		"event":      "outcome",
		"company_db": "TESTDB",
		"user":       "tester",
		"method":     "POST",
		"path":       "Drafts",
		"status":     201,
		"result_key": "DocEntry=54990",
	}
	for k, v := range over {
		base[k] = v
	}
	b, err := json.Marshal(base)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	return string(b)
}

// TestProvenanceIndexNearMisses — every one of these is a line that LOOKS like
// creation evidence and must not be treated as one. Getting any of them wrong
// means deleting a draft on somebody else's record.
func TestProvenanceIndexNearMisses(t *testing.T) {
	cases := []struct {
		name string
		over map[string]interface{}
	}{
		{"another company", map[string]interface{}{"company_db": "JIVO_MART_HANADB"}},
		{"SAP rejected it", map[string]interface{}{"status": 400}},
		{"only the intent, never an outcome", map[string]interface{}{"event": "intent"}},
		{"a PATCH, not a create", map[string]interface{}{"method": "PATCH"}},
		{"a different entity set", map[string]interface{}{"path": "PaymentDrafts"}},
		{"a keyed path, not the set", map[string]interface{}{"path": "Drafts(54990)"}},
		{"a longer DocEntry that starts the same", map[string]interface{}{"result_key": "DocEntry=549901"}},
		{"a different key entirely", map[string]interface{}{"result_key": "CardCode=V10000"}},
		{"no key at all", map[string]interface{}{"result_key": ""}},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			path := filepath.Join(dir, "sap-writes.jsonl")
			writeLogLines(t, path, creationLine(t, tc.over))

			idx, scanned, problems := buildProvenanceIndex([]string{path}, "Drafts", "TESTDB")
			if len(scanned) != 1 {
				t.Fatalf("the file should have been scanned: %v", scanned)
			}
			if len(problems) != 0 {
				t.Errorf("no problems expected: %v", problems)
			}
			if _, found := idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}]; found {
				t.Error("this line must NOT count as creation evidence")
			}
		})
	}

	t.Run("the exact line does count", func(t *testing.T) {
		dir := t.TempDir()
		path := filepath.Join(dir, "sap-writes.jsonl")
		writeLogLines(t, path,
			`not json at all`,
			creationLine(t, map[string]interface{}{"result_key": "DocEntry=1"}),
			creationLine(t, nil),
		)
		idx, _, problems := buildProvenanceIndex([]string{path}, "Drafts", "TESTDB")
		if len(problems) != 0 {
			t.Errorf("a torn line is not a problem worth reporting: %v", problems)
		}
		origin, found := idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}]
		if !found {
			t.Fatal("the exact line must count")
		}
		if origin.User != "tester" || origin.Line != 3 {
			t.Errorf("origin must point at line 3 by tester, got %+v", origin)
		}
	})

	t.Run("first match wins", func(t *testing.T) {
		dir := t.TempDir()
		path := filepath.Join(dir, "sap-writes.jsonl")
		writeLogLines(t, path,
			creationLine(t, map[string]interface{}{"user": "first"}),
			creationLine(t, map[string]interface{}{"user": "second"}),
		)
		idx, _, _ := buildProvenanceIndex([]string{path}, "Drafts", "TESTDB")
		if got := idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}].User; got != "first" {
			t.Errorf("the log is chronological: first match wins, got %q", got)
		}
	})
}

// TestProvenanceIndexReadsPastAHugeLine — a delete's own log line carries a
// snapshot and can be far over bufio.Scanner's 64KB cap. Scanner would stop the
// file there, hiding every later line, and a real creation record would silently
// become "no record that this CLI created it".
func TestProvenanceIndexReadsPastAHugeLine(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "sap-writes.jsonl")
	huge := creationLine(t, map[string]interface{}{
		"result_key": "DocEntry=1",
		"user":       strings.Repeat("x", 200_000),
	})
	writeLogLines(t, path, huge, creationLine(t, nil))

	idx, _, problems := buildProvenanceIndex([]string{path}, "Drafts", "TESTDB")
	if len(problems) != 0 {
		t.Errorf("a long line is not a read problem: %v", problems)
	}
	if _, found := idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}]; !found {
		t.Error("the line AFTER a 200KB line must still be indexed")
	}
}

// TestProvenanceIndexReportsUnreadableFiles — "I could not finish reading the
// evidence" must never look like "there is no evidence".
func TestProvenanceIndexReportsUnreadableFiles(t *testing.T) {
	if os.Geteuid() == 0 {
		t.Skip("running as root: an unreadable file is still readable")
	}
	dir := t.TempDir()
	path := filepath.Join(dir, "sap-writes.jsonl")
	writeLogLines(t, path, creationLine(t, nil))
	if err := os.Chmod(path, 0o000); err != nil {
		t.Fatalf("chmod: %v", err)
	}
	t.Cleanup(func() { _ = os.Chmod(path, 0o600) })

	idx, scanned, problems := buildProvenanceIndex([]string{path}, "Drafts", "TESTDB")
	if len(scanned) != 0 {
		t.Errorf("an unopenable file was not scanned: %v", scanned)
	}
	if len(problems) != 1 || !strings.Contains(problems[0], "provenance may be incomplete") {
		t.Errorf("want an incomplete-provenance problem, got %v", problems)
	}
	if len(idx) != 0 {
		t.Errorf("nothing should have been indexed: %v", idx)
	}
}

// TestProvenanceLogPathsRefusesPlantedEvidence — the guard only reads logs that
// really live in this checkout's queries/ folder.
//
// os.Lstat alone is not enough: it refuses a symlinked FILE, but every
// directory above it is resolved normally, so a symlinked operator directory
// used to walk straight through the glob — and then be rendered back to the
// operator as the reassuring in-repo path "queries/ghost/sap-writes.jsonl".
func TestProvenanceLogPathsRefusesPlantedEvidence(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("symlinks need a privilege on Windows")
	}
	root := t.TempDir()
	for _, d := range []string{"harness", ".git"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
	}

	// (a) a symlinked LOG FILE, pointing at a file elsewhere in the checkout.
	real := filepath.Join(root, "elsewhere.jsonl")
	writeLogLines(t, real, creationLine(t, nil))
	linkedFile := filepath.Join(root, "queries", "USER01", "sap-writes.jsonl")
	if err := os.MkdirAll(filepath.Dir(linkedFile), 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	if err := os.Symlink(real, linkedFile); err != nil {
		t.Fatalf("symlink: %v", err)
	}

	// (b) a symlinked OPERATOR DIRECTORY, pointing outside the checkout
	// entirely — the last component is an honest regular file.
	outside := t.TempDir()
	writeLogLines(t, filepath.Join(outside, "sap-writes.jsonl"), creationLine(t, nil))
	if err := os.Symlink(outside, filepath.Join(root, "queries", "ghost")); err != nil {
		t.Fatalf("symlink: %v", err)
	}

	// (c) the honest one.
	honest := filepath.Join(root, "queries", "USER06", "sap-writes.jsonl")
	writeLogLines(t, honest, creationLine(t, nil))

	setProvenanceRoot(t, root)
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(t.TempDir(), "unused.jsonl"))
	t.Setenv("HOME", t.TempDir())

	paths, notes := provenanceLogPaths()
	if len(paths) != 1 || paths[0] != honest {
		t.Errorf("want only the real log, got %v", paths)
	}
	all := strings.Join(notes, "\n")
	for _, want := range []string{"not a regular file", "outside this checkout"} {
		if !strings.Contains(all, want) {
			t.Errorf("skipping evidence must be said out loud (%q), got:\n%s", want, all)
		}
	}
}

// TestProvenanceLogPathsIgnoreTheConfiguredLog — $SAPB1_WRITE_LOG says where
// this run RECORDS its writes. Reading it back as evidence would let one
// environment variable authorise a delete that --not-created-here deliberately
// makes un-automatable, and would put the evidence and the audit record of
// having used it in the same caller-chosen file.
func TestProvenanceLogPathsIgnoreTheConfiguredLog(t *testing.T) {
	root := t.TempDir()
	for _, d := range []string{"harness", ".git", "queries"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
	}
	planted := filepath.Join(t.TempDir(), "anything.jsonl")
	writeLogLines(t, planted, creationLine(t, nil))

	setProvenanceRoot(t, root)
	t.Setenv("SAPB1_WRITE_LOG", planted)
	t.Setenv("HOME", t.TempDir())

	paths, notes := provenanceLogPaths()
	for _, p := range paths {
		if p == planted {
			t.Errorf("the configured write log must not be read as evidence: %v", paths)
		}
	}
	if !strings.Contains(strings.Join(notes, "\n"), "RECORDS writes, not evidence") {
		t.Errorf("the operator must be told why their configured log did not count, got %v", notes)
	}
}

// TestProvenanceLogPathsIgnoreTheHomeLog — ~/.sapb1-writes.jsonl was the same
// env-var lever the list above refuses, one step to the left: os.UserHomeDir is
// $HOME on Unix, and the allowed-roots check whitelisted that exact file, so a
// planted home directory passed every filter.
//
// Outside a registered checkout there is no shared history, so the honest answer
// is an empty evidence list.
func TestProvenanceLogPathsIgnoreTheHomeLog(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	planted := filepath.Join(home, ".sapb1-writes.jsonl")
	writeLogLines(t, planted, creationLine(t, nil))

	setProvenanceRoot(t, "") // no checkout at all
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(t.TempDir(), "elsewhere.jsonl"))

	paths, _ := provenanceLogPaths()
	if len(paths) != 0 {
		t.Errorf("nothing outside a checkout may vouch for a delete, got %v", paths)
	}

	// And with a checkout present, the home file still does not join the list.
	root := t.TempDir()
	for _, d := range []string{"harness", ".git", "queries"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
	}
	setProvenanceRoot(t, root)
	paths, _ = provenanceLogPaths()
	for _, p := range paths {
		if p == planted {
			t.Errorf("$HOME/.sapb1-writes.jsonl must not be evidence: %v", paths)
		}
	}
}

// TestProvenanceLogPathsDedupes — in the normal fleet setup $SAPB1_WRITE_LOG IS
// one of the repo's operator logs. It must still be scanned (through the glob,
// on its own merits) and scanned exactly once: twice would double every line
// number in the evidence it reports.
func TestProvenanceLogPathsDedupes(t *testing.T) {
	root := t.TempDir()
	for _, d := range []string{"harness", ".git"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
	}
	log := filepath.Join(root, "queries", "tester", "sap-writes.jsonl")
	writeLogLines(t, log, creationLine(t, nil))

	setProvenanceRoot(t, root)
	t.Setenv("SAPB1_WRITE_LOG", log)
	t.Setenv("HOME", t.TempDir())

	paths, notes := provenanceLogPaths()
	seen := map[string]int{}
	for _, p := range paths {
		seen[p]++
	}
	if seen[log] != 1 {
		t.Errorf("the operator's own log inside the checkout must be scanned exactly once, got %v", paths)
	}
	if strings.Contains(strings.Join(notes, "\n"), "RECORDS writes, not evidence") {
		t.Errorf("no note is due when the configured log IS one of the scanned ones: %v", notes)
	}
}

// TestConfiguredLogInsideQueriesIsEvidence — the rule is about WHERE a file
// resolves, not what it is called or which variable named it. A log the operator
// configured that lands inside the checkout's queries/ tree is exactly as
// trustworthy as one the glob found there: anybody who can write that file could
// have written it under the globbed name instead, so refusing it buys nothing
// and costs the operator their own creation records.
func TestConfiguredLogInsideQueriesIsEvidence(t *testing.T) {
	root := t.TempDir()
	for _, d := range []string{"harness", ".git"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
	}
	// Deliberately NOT the globbed name: this is the configured path being read
	// on its own merits.
	configured := filepath.Join(root, "queries", "tester", "sap-writes-2026-08.jsonl")
	writeLogLines(t, configured, creationLine(t, nil))

	setProvenanceRoot(t, root)
	t.Setenv("SAPB1_WRITE_LOG", configured)
	t.Setenv("HOME", t.TempDir())

	paths, notes := provenanceLogPaths()
	found := false
	for _, p := range paths {
		if p == configured {
			found = true
		}
	}
	if !found {
		t.Fatalf("a configured log inside queries/ must be read as evidence, got %v", paths)
	}
	if strings.Contains(strings.Join(notes, "\n"), "RECORDS writes, not evidence") {
		t.Errorf("no note is due when the configured log IS evidence: %v", notes)
	}

	idx, _, _ := buildProvenanceIndex(paths, "Drafts", "TESTDB")
	if _, ok := idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}]; !ok {
		t.Error("the creation line in it must be indexed")
	}
}

// TestEvidenceGapAdviceNamesTheOneCommandThatFixesIt — RepoRoot needs only
// harness/ + .git/, while config.WriteLogPath needs harness/.operator to put the
// log inside queries/. So a valid but UNREGISTERED checkout creates drafts into
// ~/.sapb1-writes.jsonl and reads evidence from queries/* — and its own drafts,
// made a minute ago, refuse to delete.
//
// That is the state of a freshly cloned box, and the fleet's whole reason for
// this command is bulk cleanup, which --not-created-here cannot serve (one
// DocEntry, one human, one prompt at a time). So the gap has to be named where
// it is felt, with the command that closes it.
func TestEvidenceGapAdviceNamesTheOneCommandThatFixesIt(t *testing.T) {
	t.Run("a checkout with no registered operator", func(t *testing.T) {
		root := t.TempDir()
		for _, d := range []string{"harness", ".git", "queries"} {
			if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
				t.Fatalf("mkdir: %v", err)
			}
		}
		setProvenanceRoot(t, root)
		t.Setenv("SAPB1_WRITE_LOG", "")
		t.Setenv("HOME", t.TempDir())
		t.Chdir(t.TempDir()) // nothing above cwd registers an operator

		advice := evidenceGapAdvice()
		for _, want := range []string{"no registered operator", "harness/bin/setup.py", ".sapb1-writes.jsonl"} {
			if !strings.Contains(advice, want) {
				t.Errorf("advice must contain %q, got:\n%s", want, advice)
			}
		}
	})

	t.Run("the configured log already is evidence", func(t *testing.T) {
		root := t.TempDir()
		for _, d := range []string{"harness", ".git"} {
			if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
				t.Fatalf("mkdir: %v", err)
			}
		}
		log := filepath.Join(root, "queries", "tester", "sap-writes.jsonl")
		writeLogLines(t, log, creationLine(t, nil))
		setProvenanceRoot(t, root)
		t.Setenv("SAPB1_WRITE_LOG", log)
		t.Setenv("HOME", t.TempDir())

		if advice := evidenceGapAdvice(); advice != "" {
			t.Errorf("the normal setup must produce no advice at all, got:\n%s", advice)
		}
	})
}

// TestDocEntryFromResultKey pins the parse that decides whether a line is about
// the draft in front of us.
func TestDocEntryFromResultKey(t *testing.T) {
	ok := map[string]int64{"DocEntry=1": 1, "DocEntry=54990": 54990}
	for in, want := range ok {
		got, found := docEntryFromResultKey(in)
		if !found || got != want {
			t.Errorf("docEntryFromResultKey(%q) = %d,%v; want %d,true", in, got, found, want)
		}
	}
	bad := []string{"", "DocEntry=", "DocEntry=0", "DocEntry=-1", "DocEntry=1.0", "docentry=1", "CardCode=DocEntry=1", "DocEntry=1x"}
	for _, in := range bad {
		if _, found := docEntryFromResultKey(in); found {
			t.Errorf("docEntryFromResultKey(%q) should not have matched", in)
		}
	}
}

// TestShortPathsRelativeToTheCheckout keeps refusal messages readable.
func TestShortPathsRelativeToTheCheckout(t *testing.T) {
	root := t.TempDir()
	setProvenanceRoot(t, root)

	inside := filepath.Join(root, "queries", "USER36", "sap-writes.jsonl")
	outside := filepath.Join(t.TempDir(), "somewhere.jsonl")
	got := shortPaths([]string{inside, outside})

	want := filepath.Join("queries", "USER36", "sap-writes.jsonl")
	if got[0] != want {
		t.Errorf("a log inside the checkout should render as %q, got %q", want, got[0])
	}
	if got[1] != outside {
		t.Errorf("a log outside it keeps its full path, got %q", got[1])
	}
	_ = fmt.Sprint(got)
}
