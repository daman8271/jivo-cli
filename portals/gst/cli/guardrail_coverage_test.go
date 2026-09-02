package main

import (
	"os"
	"sort"
	"strings"
	"testing"
)

// TestWiredReadsMatchTheTable — the endpoint table and wired-reads.tsv must be
// the same set, 1:1. The .tsv is the human-readable truth a reviewer reads; if
// code can add an endpoint without it appearing there, the review is fiction.
func TestWiredReadsMatchTheTable(t *testing.T) {
	b, err := os.ReadFile("wired-reads.tsv")
	if err != nil {
		t.Fatalf("wired-reads.tsv: %v", err)
	}
	inFile := map[string]string{}
	for i, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		f := strings.Split(line, "\t")
		if len(f) != 4 {
			t.Fatalf("wired-reads.tsv:%d has %d tab-separated fields, want 4: %q", i+1, len(f), line)
		}
		inFile[f[0]+" "+f[1]+" "+f[2]] = f[3]
	}
	inCode := map[string]string{}
	for _, e := range endpoints {
		inCode[e.Method+" "+e.Host+" "+e.Path] = e.Name
	}
	for k := range inCode {
		if _, ok := inFile[k]; !ok {
			t.Errorf("endpoints.go has %q but wired-reads.tsv does not — every wired read must be listed for review", k)
		}
	}
	for k := range inFile {
		if _, ok := inCode[k]; !ok {
			t.Errorf("wired-reads.tsv lists %q but the table does not — stale row", k)
		}
	}
	if len(inFile) != len(inCode) {
		t.Errorf("tsv has %d rows, table has %d", len(inFile), len(inCode))
	}
}

// TestEveryTableRowPassesItsOwnGuard — no dead commands: a row that the guard
// blocks is a command that can never work. (This is the test that caught "/pay"
// blocking the entire payment host.)
func TestEveryTableRowPassesItsOwnGuard(t *testing.T) {
	names := map[string]bool{}
	for _, e := range endpoints {
		if names[e.Name] {
			t.Errorf("duplicate endpoint name %q", e.Name)
		}
		names[e.Name] = true

		params := map[string]string{}
		for _, p := range e.Params {
			params[p] = "2026-27"
		}
		resolved, err := e.resolvePath(params)
		if err != nil {
			t.Fatalf("%s: %v", e.Name, err)
		}
		if err := forbidden(e.Method, e.Host, e.Path, resolved, e.Query, e.Body); err != nil {
			t.Errorf("DEAD ROW %s: %v", e.Name, err)
		}
	}
	t.Logf("verified %d allowlisted endpoints all pass the guard", len(endpoints))
}

// TestEveryEndpointConstantIsInTheTable — the ep* constants are the only way a
// command names an endpoint; a stale constant would be a runtime guard error
// rather than a compile error, so pin them here.
func TestEveryEndpointConstantIsInTheTable(t *testing.T) {
	consts := []string{
		epLoginPage, epCaptcha, epAuthenticate, epUstatus, epKeepalive, epProfile,
		epFilingSnapshot, epDropdown, epRoleStatus, epFormDetails, epEfiledReturns,
		epGSTR3BSummary, epGSTR3BAutoPop, epGSTR2BData, epGSTR2BUserDtls,
		epCashBalance, epCashDetails, epITCBalance, epITCDetails, epChallanSearch,
		epLiability, epLiabilityOther, epGSTR1Count, epGSTR1Invoice,
		epGSTR2ACtin, epGSTR2AB2B, epCompareUser, epCompareData,
		epMasterForms, epMasterFY, epMasterMonths, epMasterQuarters, epMasterHalves,
		epMasterStates,
	}
	for _, name := range consts {
		if _, err := lookup(name); err != nil {
			t.Errorf("endpoint constant %q is not in the table", name)
		}
	}
	if len(consts) != len(endpoints) {
		var missing []string
		have := map[string]bool{}
		for _, c := range consts {
			have[c] = true
		}
		for _, e := range endpoints {
			if !have[e.Name] {
				missing = append(missing, e.Name)
			}
		}
		sort.Strings(missing)
		t.Errorf("%d constants for %d rows; rows with no constant: %v", len(consts), len(endpoints), missing)
	}
}
