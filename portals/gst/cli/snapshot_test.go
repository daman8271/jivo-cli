package main

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// snapshotPortal serves a plausible Haryana for one FY.
func snapshotPortal(t *testing.T) *fakePortal {
	t.Helper()
	fp := newFakePortal(t)
	fp.json(hostServices, "/services/api/ustatus", "ustatus.json")
	fp.json(hostServices, "/returns/auth/api/filingsnapshot", "master-gstrs-A.json")
	fp.json(hostPayment, "/payment/auth/api/cashbalance", "HR-cashbalance.json")
	fp.json(hostPayment, "/payment/auth/api/cashdetls", "HR-cashdetls-fy2627.json")
	fp.json(hostReturn, "/returns/auth/api/itcbalance", "HR-itcbalance.json")
	fp.json(hostReturn, "/returns/auth/api/itcdtls", "HR-itcdtls-fy2627.json")
	fp.json(hostReturn, "/returns/auth/api/efiledReturns", "HR-filed-GSTR1-2026-27.json")
	fp.json(hostReturn, "/returns/auth/api/formdetails", "formdetails-gstr3b-072026.json")
	fp.json(hostReturn, "/returns/auth/api/gstr3b/summary", "HR-gstr3b-summary-072026.json")
	fp.json(hostGSTR2B, "/gstr2b/auth/api/gstr2b/getdata", "HR-gstr2b-getdata-072026.json")
	return fp
}

func TestSnapshotWritesRawRecordsAndManifest(t *testing.T) {
	pinClock(t)
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	snapshotPortal(t)
	out := t.TempDir()

	if _, err := runCLI(t, "snapshot", "--fy", "2026-27", "--out", out, "--state", "haryana"); err != nil {
		t.Fatalf("snapshot: %v", err)
	}

	var m manifest
	b, err := os.ReadFile(filepath.Join(out, "manifest.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(b, &m); err != nil {
		t.Fatalf("manifest: %v", err)
	}
	if m.FY != "2026-27" || len(m.Registrations) != 1 {
		t.Fatalf("manifest = %+v", m)
	}
	rep := m.Registrations[0]
	if rep.Status != "ok" {
		t.Errorf("status = %q, note = %q", rep.Status, rep.Note)
	}
	if rep.Records == 0 || m.TotalRecords != rep.Records {
		t.Errorf("records = %d, total = %d", rep.Records, m.TotalRecords)
	}
	// the FY is frozen at 2026-08-21, so periods stop at August: Apr–Aug = 5
	if len(m.Periods) != 5 || m.Periods[0] != "042026" || m.Periods[4] != "082026" {
		t.Errorf("periods = %v — future months must not be requested", m.Periods)
	}

	dir := filepath.Join(out, "06AAAAA0000A1Z0")
	for _, want := range []string{
		"raw/ustatus.json", "raw/ledger-cash-balance.json", "raw/ledger-credit-statement.json",
		"raw/filed-GSTR1.json", "raw/gstr3b-072026.json", "raw/gstr2b-072026.json", "records.jsonl",
	} {
		if _, err := os.Stat(filepath.Join(dir, want)); err != nil {
			t.Errorf("missing %s: %v", want, err)
		}
	}

	// every emitted line is a full envelope
	lines := readJSONL(t, filepath.Join(dir, "records.jsonl"))
	if len(lines) != rep.Records {
		t.Errorf("records.jsonl has %d lines, the manifest claims %d", len(lines), rep.Records)
	}
	forms := map[string]int{}
	for i, r := range lines {
		for _, k := range []string{"src", "gstin", "form", "record_kind", "pulled_at", "portal_ref"} {
			if _, ok := r[k]; !ok {
				t.Fatalf("record %d has no %q", i, k)
			}
		}
		if r["gstin"] != "06AAAAA0000A1Z0" {
			t.Fatalf("record %d belongs to %v", i, r["gstin"])
		}
		forms[r["form"].(string)]++
	}
	for _, want := range []string{"FILING", "LEDGER_CASH", "LEDGER_CREDIT", "GSTR3B", "GSTR2B"} {
		if forms[want] == 0 {
			t.Errorf("no %s records were produced (got %v)", want, forms)
		}
	}
	// the portal_ref must name the endpoint the record came from, not a stale one
	for _, r := range lines {
		ref := r["portal_ref"].(map[string]any)
		if !strings.HasPrefix(ref["endpoint"].(string), "https://") {
			t.Fatalf("portal_ref.endpoint = %v", ref["endpoint"])
		}
	}
}

// TestSnapshotNeverPromptsAndRecordsNeedsLogin — the headline behaviour. A
// registration with no session must be a manifest line, never a captcha.
func TestSnapshotNeverPromptsAndRecordsNeedsLogin(t *testing.T) {
	pinClock(t)
	useTempStateDir(t)
	writeTestEnv(t)
	fp := snapshotPortal(t)
	out := t.TempDir()

	// stdin is deliberately empty: if snapshot ever prompted, it would fail here
	// rather than hang, and either way the test would not pass.
	_, _, err := runCLIWithStdin(t, "", "snapshot", "--fy", "2026-27", "--out", out, "--state", "haryana")
	if err != nil {
		t.Fatalf("snapshot with no session must still succeed: %v", err)
	}
	var m manifest
	b, _ := os.ReadFile(filepath.Join(out, "manifest.json"))
	if err := json.Unmarshal(b, &m); err != nil {
		t.Fatal(err)
	}
	rep := m.Registrations[0]
	if rep.Status != "needs login" {
		t.Errorf("status = %q want \"needs login\"", rep.Status)
	}
	if !strings.Contains(rep.Note, "auth login") {
		t.Errorf("the note must say how to fix it: %q", rep.Note)
	}
	if fp.hitCount() != 0 {
		t.Errorf("it opened %d connection(s) without a session", fp.hitCount())
	}
	// no login endpoint was touched either
	for _, h := range fp.Hits {
		if strings.Contains(h.Path, "captcha") || strings.Contains(h.Path, "authenticate") {
			t.Fatal("snapshot tried to log in")
		}
	}
}

// TestSnapshotContinuesPastAuthFailure — Punjab must not take the run down.
func TestSnapshotContinuesPastAuthFailure(t *testing.T) {
	pinClock(t)
	useTempStateDir(t)
	writeTestEnv(t)
	// Haryana works; Rajasthan's jar turns out to belong to Haryana; the other
	// six have no session at all.
	seedSession(t, "06AAAAA0000A1Z0")
	seedSession(t, "08AAAAA0000A1ZW")
	fp := snapshotPortal(t)
	// The portal answers "you are Haryana" to every session, so Rajasthan's jar
	// comes back as the wrong registration — which is exactly the case worth
	// testing, since a copied or mis-imported jar looks like this.
	fp.handle(hostServices, "/services/api/ustatus", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"gstin":"06AAAAA0000A1Z0","bname":"TEST NAME","stcd":"06","utype":"Normal"}`))
	})
	out := t.TempDir()

	if _, err := runCLI(t, "snapshot", "--fy", "2026-27", "--out", out, "--all"); err != nil {
		t.Fatalf("snapshot --all: %v", err)
	}
	var m manifest
	b, _ := os.ReadFile(filepath.Join(out, "manifest.json"))
	if err := json.Unmarshal(b, &m); err != nil {
		t.Fatal(err)
	}
	if len(m.Registrations) != 8 {
		t.Fatalf("the run covered %d of 8 registrations", len(m.Registrations))
	}
	byGSTIN := map[string]regReport{}
	for _, r := range m.Registrations {
		byGSTIN[r.GSTIN] = r
	}
	if byGSTIN["06AAAAA0000A1Z0"].Records == 0 {
		t.Error("Haryana produced nothing")
	}
	// Rajasthan's session answers as Haryana's GSTIN — a wrong-registration
	// session must be recorded, not silently accepted.
	rj := byGSTIN["08AAAAA0000A1ZW"]
	if rj.Status != "wrong registration" || rj.Records != 0 {
		t.Errorf("a session belonging to another GSTIN was accepted: status=%q records=%d", rj.Status, rj.Records)
	}
	if !strings.Contains(rj.Note, "06AAAAA0000A1Z0") {
		t.Errorf("the note must name the GSTIN the session actually belongs to: %q", rj.Note)
	}
	if _, err := os.Stat(filepath.Join(out, "08AAAAA0000A1ZW", "records.jsonl")); err == nil {
		t.Error("records were written for a registration whose session belonged to someone else")
	}
	needsLogin := 0
	for _, r := range m.Registrations {
		if r.Status == "needs login" {
			needsLogin++
		}
	}
	if needsLogin != 6 {
		t.Errorf("%d registrations recorded as needing login, want 6", needsLogin)
	}
}

// TestSnapshotWritesOnlyUnderOut — nothing outside --out is touched, in
// particular nothing inside the repo.
func TestSnapshotWritesOnlyUnderOut(t *testing.T) {
	pinClock(t)
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	snapshotPortal(t)

	root := t.TempDir()
	out := filepath.Join(root, "snap")
	sentinel := filepath.Join(root, "untouched.txt")
	if err := os.WriteFile(sentinel, []byte("original"), 0o600); err != nil {
		t.Fatal(err)
	}
	before := treeOf(t, ".")

	if _, err := runCLI(t, "snapshot", "--fy", "2026-27", "--out", out, "--state", "haryana"); err != nil {
		t.Fatal(err)
	}
	for _, p := range treeOf(t, root) {
		if !strings.HasPrefix(p, out) && p != sentinel {
			t.Errorf("snapshot wrote outside --out: %s", p)
		}
	}
	if b, _ := os.ReadFile(sentinel); string(b) != "original" {
		t.Error("snapshot modified a file outside --out")
	}
	if after := treeOf(t, "."); len(after) != len(before) {
		t.Errorf("snapshot changed the working directory: %d files before, %d after", len(before), len(after))
	}
}

// TestSnapshotSkipsGSTR1And3BForAnISD — an ISD registration files GSTR-6; asking
// for 1/3B/2B produces portal errors that look like breakage.
func TestSnapshotSkipsGSTR1And3BForAnISD(t *testing.T) {
	pinClock(t)
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "07AAAAA0000A2ZX")
	fp := snapshotPortal(t)
	fp.handle(hostServices, "/services/api/ustatus", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"gstin":"07AAAAA0000A2ZX","bname":"TEST NAME","stcd":"07","utype":"ISD","regType":"ISD"}`))
	})
	out := t.TempDir()

	if _, err := runCLI(t, "snapshot", "--fy", "2026-27", "--out", out, "--gstin", "07AAAAA0000A2ZX"); err != nil {
		t.Fatalf("snapshot: %v", err)
	}
	for _, h := range fp.Hits {
		if strings.Contains(h.Path, "gstr3b") || strings.Contains(h.Path, "gstr2b") || h.Path == "/returns/auth/api/efiledReturns" {
			t.Errorf("an ISD snapshot called %s", h.Path)
		}
	}
	var m manifest
	b, _ := os.ReadFile(filepath.Join(out, "manifest.json"))
	json.Unmarshal(b, &m)
	if !strings.Contains(m.Registrations[0].Note, "ISD") {
		t.Errorf("the manifest does not explain the ISD skip: %q", m.Registrations[0].Note)
	}
	// the ledgers, which an ISD does have, were still pulled
	if m.Registrations[0].Records == 0 {
		t.Error("an ISD registration should still yield ledger records")
	}
}

// TestSnapshotSkipDocuments — the fast path for "just the ledgers".
func TestSnapshotSkipDocuments(t *testing.T) {
	pinClock(t)
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := snapshotPortal(t)
	out := t.TempDir()

	if _, err := runCLI(t, "snapshot", "--fy", "2026-27", "--out", out, "--state", "hr", "--skip-documents"); err != nil {
		t.Fatal(err)
	}
	for _, h := range fp.Hits {
		if strings.Contains(h.Path, "gstr3b/summary") || strings.Contains(h.Path, "gstr2b/getdata") {
			t.Errorf("--skip-documents still called %s", h.Path)
		}
	}
}

func readJSONL(t *testing.T, path string) []map[string]any {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var out []map[string]any
	for _, line := range strings.Split(strings.TrimSpace(string(b)), "\n") {
		if line == "" {
			continue
		}
		var m map[string]any
		if err := json.Unmarshal([]byte(line), &m); err != nil {
			t.Fatalf("%s: not JSON: %v", path, err)
		}
		out = append(out, m)
	}
	return out
}

func treeOf(t *testing.T, root string) []string {
	t.Helper()
	var out []string
	err := filepath.Walk(root, func(p string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		out = append(out, p)
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return out
}

// TestPeriodsUpToNow — a snapshot must not ask about months that have not
// happened. An "unfiled" future return is a calendar, not a finding.
func TestPeriodsUpToNow(t *testing.T) {
	old := nowIST
	nowIST = func() time.Time { return time.Date(2026, 8, 21, 0, 0, 0, 0, istLoc) }
	defer func() { nowIST = old }()

	all, err := fyPeriods("2026-27")
	if err != nil {
		t.Fatal(err)
	}
	got := periodsUpToNow(all)
	want := []string{"042026", "052026", "062026", "072026", "082026"}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Errorf("periods = %v want %v", got, want)
	}
}
