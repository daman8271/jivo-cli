package cli

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"sapb1/internal/config"
)

// repoRootFunc is config.RepoRoot, indirected so tests can point the provenance
// scan at a temp tree. Without this, every delete test would read the
// developer's own queries/<operator>/sap-writes.jsonl — which holds real
// creation lines for real drafts — and would pass or fail depending on whose
// machine it ran on.
var repoRootFunc = config.RepoRoot

// draftOrigin is the write-log line that says this CLI created a particular
// draft: which file vouched for it, which line, which operator, and when.
type draftOrigin struct {
	File string
	Line int
	User string
	Time time.Time
	Host string
	Port int
}

// originKey identifies a created object across every log this box can read.
//
// CompanyDB is part of the key and host/port deliberately are not. The same
// company is reached down a different road depending on where the operator is
// standing — 138.252.101.222 from the office, 127.0.0.1:15000 through the home
// bridge — so host would split one draft's history into two. The company
// database is the thing that must never be confused; Oil's DocEntry 54990 and
// Mart's are different documents.
type originKey struct {
	EntitySet string
	CompanyDB string
	DocEntry  int64
}

// provenanceLogPaths lists every write log this box may treat as EVIDENCE: the
// fleet's committed logs inside this checkout (queries/*/sap-writes.jsonl), plus
// the log this run is configured to write to — but only ever when the file
// RESOLVES inside that same queries/ tree.
//
// It is the resolved location that earns the trust, never the name it was
// reached by. $SAPB1_WRITE_LOG says where this run RECORDS its writes, and a
// destination is not a witness: if the variable could name evidence outright,
// the whole guard would hang on one environment variable — point it at a
// hand-written file and a draft a person keyed by hand deletes without ever
// meeting --not-created-here, which is engineered to need a human at a prompt.
// Inside queries/ it earns nothing extra, because anyone who can write a file
// there can already have it globbed. That is the same reasoning config.RepoRoot
// applies to the trust root, and it keeps the normal fleet setup working:
// acc/_playbook/sap points the variable at queries/<operator>/sap-writes.jsonl.
//
// ~/.sapb1-writes.jsonl is admitted by exactly the same rule, which is to say
// never: os.UserHomeDir is $HOME on Unix, so trusting it was the same env-var
// lever one step to the left — `HOME=/tmp/planted sapb1 delete draft 54983
// --yes` with one forged line, no checkout, no TTY, no override. A box whose
// writes land there has no evidence corpus at all, and evidenceGapAdvice says so
// out loud with the one command that fixes it.
//
// Two shapes of file are refused, each with a note: anything that is not a
// regular file (a symlinked log says nothing about who wrote it), and anything
// that RESOLVES outside the evidence directories — os.Lstat only refuses a
// symlink in the last path component, so `queries/ghost -> /tmp/planted` would
// otherwise walk straight in and be printed back as a reassuring in-repo path.
func provenanceLogPaths() (paths []string, notes []string) {
	var candidates []string
	var allowed []string // resolved dirs/files evidence may live in

	root, note := repoRootFunc()
	if note != "" {
		notes = append(notes, note)
	}
	if root != "" {
		queries := filepath.Join(root, "queries")
		if real, ok := resolvePath(queries); ok {
			allowed = append(allowed, real)
		}
		matches, err := filepath.Glob(filepath.Join(queries, "*", "sap-writes.jsonl"))
		if err == nil {
			candidates = append(candidates, matches...)
		}
	}

	// The configured log is a candidate like any other: the withinAny check
	// below decides whether it is evidence, and it decides on where the file
	// really is.
	configured, cerr := config.WriteLogPath()
	if cerr == nil && configured != "" {
		candidates = append(candidates, configured)
	}
	configuredReal, _ := resolvePath(configured)
	configuredIsEvidence := false

	seen := make(map[string]bool, len(candidates))
	for _, p := range candidates {
		abs, err := filepath.Abs(p)
		if err != nil {
			continue
		}
		abs = filepath.Clean(abs)
		if seen[abs] {
			continue
		}
		seen[abs] = true

		fi, err := os.Lstat(abs)
		if err != nil {
			continue // simply doesn't exist — not worth a note
		}
		if !fi.Mode().IsRegular() {
			notes = append(notes, fmt.Sprintf("note: skipping %s as write-log evidence — it is not a regular file (%s)", abs, fi.Mode().Type()))
			continue
		}
		real, ok := resolvePath(abs)
		if !ok {
			continue
		}
		if !withinAny(allowed, real) {
			notes = append(notes, fmt.Sprintf(
				"note: skipping %s as write-log evidence — it really lives at %s, outside this checkout's queries/ folder. A log reached through a symlinked directory is not evidence a delete may rest on",
				abs, real))
			continue
		}
		paths = append(paths, abs)
		if configuredReal != "" && real == configuredReal {
			configuredIsEvidence = true
		}
	}

	// Say why the operator's own configured log is not in the list, but only
	// when it genuinely isn't — otherwise every delete in the fleet grows a note
	// nobody reads. Compared by resolved path, not by string: one checkout
	// reached through a symlink (/tmp -> /private/tmp on every Mac here) is one
	// checkout.
	if cerr == nil && configured != "" && !configuredIsEvidence {
		notes = append(notes, configuredLogNote(configured))
	}
	return paths, notes
}

// configuredLogNote explains why this run's own write log did not count as
// evidence, naming the thing that actually chose the path. Blaming
// $SAPB1_WRITE_LOG when nobody set it sends the operator looking for a variable
// that does not exist.
//
// One line, and no advice: what to DO about it is said once, where it lands —
// in the refusal if a guard stops the delete, and in the preview's record lines
// if it goes ahead.
func configuredLogNote(configured string) string {
	head := fmt.Sprintf("note: this run RECORDS its writes to %s, which is not evidence", configured)
	if strings.TrimSpace(os.Getenv("SAPB1_WRITE_LOG")) != "" {
		head = fmt.Sprintf("note: $SAPB1_WRITE_LOG (%s) is where this run RECORDS writes, not evidence", configured)
	}
	return head + " — provenance is read only from queries/*/sap-writes.jsonl in this checkout"
}

// evidenceGapAdvice names the one thing to do about a box whose own writes are
// recorded where the guard cannot read them, or "" when they already are.
//
// This is the gap that makes bulk cleanup impossible on a fresh box: RepoRoot
// needs only harness/ + .git/, while config.WriteLogPath needs harness/.operator
// to put the log inside queries/. So an unregistered checkout CREATES drafts
// into ~/.sapb1-writes.jsonl and READS evidence from queries/* — and its own
// drafts, made thirty seconds ago, refuse to delete. Pointing at
// --not-created-here there is a dead end: it takes one DocEntry and a human at a
// prompt, which is fifty prompts for the fifty-draft batch this command exists
// for. The remedy is one command, and the operator has to be told it.
func evidenceGapAdvice() string {
	configured, err := config.WriteLogPath()
	if err != nil || configured == "" {
		return ""
	}
	root, _ := repoRootFunc()
	if root != "" && withinQueries(root, configured) {
		return ""
	}
	switch {
	case root == "":
		return fmt.Sprintf("This sapb1 is not inside a JIVO checkout (one has both harness/ and .git/), so there is no shared history here at all — your writes are recorded in %s.", configured)
	case config.SharedWriteLogPath() == "":
		return fmt.Sprintf("This checkout has no registered operator, so your writes are recorded in %s — outside queries/, which is where `sapb1 delete` looks for proof a draft was made here. Run `python3 harness/bin/setup.py` once and every write after it lands in queries/<you>/sap-writes.jsonl, where this guard and the team can both read it.", configured)
	default:
		return fmt.Sprintf("$SAPB1_WRITE_LOG sends this run's records to %s, outside queries/ — a draft created with that in force cannot later be shown to be this CLI's. Unset it, or point it at your queries/<you>/sap-writes.jsonl.", configured)
	}
}

// withinQueries reports whether p resolves inside root/queries — the one place
// evidence may live.
func withinQueries(root, p string) bool {
	return resolvesUnder(filepath.Join(root, "queries"), p)
}

// withinCheckout reports whether p resolves anywhere inside the checkout. It
// answers a different question from withinQueries: where the file IS, which is
// what an operator reading "OUTSIDE any checkout" above a destroy prompt is
// being told.
func withinCheckout(root, p string) bool {
	return resolvesUnder(root, p)
}

// resolvesUnder reports whether p sits under dir once every symlink on both
// sides is followed.
//
// A file that does not exist yet is judged by where it WOULD be: the log named
// by $SAPB1_WRITE_LOG is created by the first write, and on a fresh box neither
// it nor its queries/<operator>/ directory exists at the moment these messages
// are printed. So climb to the nearest ancestor that does exist and answer for
// that. (Evidence admission never uses this — it resolves each candidate file
// itself and skips the ones that are not there.)
func resolvesUnder(dir, p string) bool {
	real, ok := resolvePath(dir)
	if !ok {
		return false
	}
	for target := p; ; {
		if r, ok := resolvePath(target); ok {
			return withinAny([]string{real}, r)
		}
		parent := filepath.Dir(target)
		if parent == target {
			return false
		}
		target = parent
	}
}

// resolvePath follows every symlink in p. A path that cannot be resolved does
// not exist as far as the guard is concerned.
//
// One of three path-identity helpers that must agree about when two spellings
// name the same thing: this pair (resolvePath/withinAny/resolvesUnder) decides
// whether a file is admissible as evidence, config.sameDirectory decides which
// checkout this binary belongs to, and client.sameLogFile decides whether the
// shared and configured write logs are one file. They are deliberately not one
// function — each answers a different question and two of them must work on
// paths that do not exist yet — but they share the rule: compare the
// symlink-resolved paths, never the strings the operator typed. Change one and
// read the other two.
func resolvePath(p string) (string, bool) {
	real, err := filepath.EvalSymlinks(p)
	if err != nil {
		return "", false
	}
	return filepath.Clean(real), true
}

// withinAny reports whether p is one of the allowed files or sits under one of
// the allowed directories. Both sides are already symlink-resolved.
func withinAny(allowed []string, p string) bool {
	for _, a := range allowed {
		rel, err := filepath.Rel(a, p)
		if err != nil {
			continue
		}
		if rel == "." || (rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator))) {
			return true
		}
	}
	return false
}

// logLine is the subset of a write-log entry the provenance scan reads.
type logLine struct {
	Time      time.Time `json:"time"`
	Event     string    `json:"event"`
	Host      string    `json:"host"`
	Port      int       `json:"port"`
	CompanyDB string    `json:"company_db"`
	User      string    `json:"user"`
	Method    string    `json:"method"`
	Path      string    `json:"path"`
	Status    *int      `json:"status"`
	ResultKey string    `json:"result_key"`
}

// buildProvenanceIndex reads every log ONCE and returns the creation evidence it
// found, keyed by entity set + company + DocEntry.
//
// One pass, not one pass per draft: a 50-draft batch against a fleet-wide
// history would otherwise re-read every log fifty times.
//
// A line is creation evidence only if it is the OUTCOME of a POST to this entity
// set, in this company, that SAP answered 2xx with this DocEntry. The EARLIEST
// such line wins, whichever file it came from — see indexLogLine. Unparseable
// lines are skipped in silence — the log is append-only from several processes
// and a torn line proves nothing — but a file that cannot be read to the end is
// reported in problems, because "I couldn't finish reading the evidence" must
// never be mistaken for "there is no evidence".
func buildProvenanceIndex(paths []string, entitySet, companyDB string) (idx map[originKey]draftOrigin, scanned []string, problems []string) {
	idx = make(map[originKey]draftOrigin)

	for _, path := range paths {
		f, err := os.Open(path) // #nosec G304 — paths come from provenanceLogPaths, not from an argument
		if err != nil {
			problems = append(problems, fmt.Sprintf("could not read %s (%v) — provenance may be incomplete", path, err))
			continue
		}
		scanned = append(scanned, path)

		// bufio.Reader, not bufio.Scanner: a line carrying a draft snapshot can
		// exceed Scanner's 64KB cap, and Scanner would stop the file there —
		// silently hiding every later line and turning a real creation record
		// into "no record that this CLI created it".
		r := bufio.NewReader(f)
		lineNo := 0
		for {
			raw, err := r.ReadString('\n')
			if len(raw) > 0 {
				lineNo++
				indexLogLine(idx, path, lineNo, raw, entitySet, companyDB)
			}
			if err != nil {
				if err != io.EOF {
					problems = append(problems, fmt.Sprintf("could not read all of %s (%v) — provenance may be incomplete", path, err))
				}
				break
			}
		}
		f.Close()
	}
	return idx, scanned, problems
}

// indexLogLine records one line as creation evidence if it qualifies, keeping
// the EARLIEST timestamp per key.
//
// Not "first line seen": the files arrive in filepath.Glob order, which is
// alphabetical by operator slug, so first-seen made queries/avtar/ outrank
// queries/tester/ for no reason but the letter it starts with. The line that
// wins is not merely the one recorded — it decides the age guard, the
// other-operator guard, and the file:line written into the shared audit trail as
// the authority for the delete. This fleet has the precondition on file: DocEntry
// numbers come round again after a company restore, and PaymentDrafts has no
// CreationDate for the cross-check to catch a stale line with.
//
// EARLIEST rather than latest, deliberately. A line appended to a queries/ file
// can be stamped "now" by anyone who can write there, so "the newest line wins"
// hands the key to whoever wrote last. Backdating one instead has to get past
// the two checks that already exist: SAP's own CreationDate on the row, and the
// age guard. The cost is the safe direction — a stale earlier line makes the
// guards refuse a delete that would have been fine, and the operator reads why.
//
// Ties keep the first seen: two lines stamped the same instant are the same
// write recorded twice (the shared log and the configured log are both scanned),
// and picking between them is meaningless.
func indexLogLine(idx map[originKey]draftOrigin, path string, lineNo int, raw, entitySet, companyDB string) {
	var e logLine
	if err := json.Unmarshal([]byte(strings.TrimSpace(raw)), &e); err != nil {
		return
	}
	if e.Event != "outcome" || !strings.EqualFold(e.Method, "POST") {
		return
	}
	if e.Path != entitySet || e.CompanyDB != companyDB {
		return
	}
	if e.Status == nil || *e.Status < 200 || *e.Status >= 300 {
		return
	}
	docEntry, ok := docEntryFromResultKey(e.ResultKey)
	if !ok {
		return
	}
	key := originKey{EntitySet: entitySet, CompanyDB: companyDB, DocEntry: docEntry}
	if seen, ok := idx[key]; ok && !earlierOrigin(e.Time, seen.Time) {
		return
	}
	idx[key] = draftOrigin{
		File: path,
		Line: lineNo,
		User: e.User,
		Time: e.Time,
		Host: e.Host,
		Port: e.Port,
	}
}

// earlierOrigin reports whether a candidate line should displace the one already
// indexed for a key.
//
// A zero time is not "the earliest" — it is no time at all (a torn append, a
// hand-edit, a box whose clock never started), and it must not be able to push a
// real creation line out of the index. It still gets in when nothing else has,
// so the log-timestamp guard can refuse on it by name rather than the delete
// falling through to "no record that this CLI created it".
func earlierOrigin(candidate, held time.Time) bool {
	switch {
	case candidate.IsZero():
		return false
	case held.IsZero():
		return true
	default:
		return candidate.Before(held) // equal timestamps keep the first seen
	}
}

// docEntryFromResultKey parses the log's greppable key ("DocEntry=54990"). It
// insists on the exact prefix and a whole number, so "DocEntry=549901" never
// matches 54990 and "CardCode=DocEntry" never matches anything.
func docEntryFromResultKey(resultKey string) (int64, bool) {
	const prefix = "DocEntry="
	if !strings.HasPrefix(resultKey, prefix) {
		return 0, false
	}
	n, err := strconv.ParseInt(resultKey[len(prefix):], 10, 64)
	if err != nil || n <= 0 {
		return 0, false
	}
	return n, true
}

// shortPaths renders a list of log paths for an operator-facing message,
// relative to the checkout when they live inside it — "queries/USER36/…" reads
// far better than 90 characters of absolute path.
func shortPaths(paths []string) []string {
	root, _ := repoRootFunc()
	out := make([]string, 0, len(paths))
	for _, p := range paths {
		if root != "" {
			if rel, err := filepath.Rel(root, p); err == nil && !strings.HasPrefix(rel, "..") {
				out = append(out, rel)
				continue
			}
		}
		out = append(out, p)
	}
	return out
}
