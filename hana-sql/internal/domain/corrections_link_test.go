package domain

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// --- the corrections are the source of truth, and nothing checked that ----------
//
// CLAUDE.md's contract is that a correction pushed to main reaches every
// operator. Inside this binary the corrections are FROZEN GO CONSTANTS — the card
// codes in relatedparty.go, ComboItemGroup, the variety field names — with no
// link back to harness/corrections/ and, until this file, nothing asserting they
// still say the same thing. So a correction reached the MCP only when somebody
// remembered to edit Go.
//
// That is not hypothetical. C-0002's evidence has named Mart's branch cards since
// 2026-07-30; the Go split ignored them until 2026-08-01, and the gap put
// Rs 1.53 Cr of Mart's own Delhi branch inside a figure labelled EXTERNAL.
//
// This test cannot make the corrections load at runtime (there is deliberately no
// file I/O in the serving path). What it can do is make the drift IMPOSSIBLE TO
// SHIP: change a correction record without changing the code that encodes it and
// the build fails here, with the record's own words in the failure message.

// correctionsDir walks up from the package directory to the repo root.
//
// WHEN IT FAILS vs WHEN IT SKIPS, and why the difference is not a loophole.
// `go test ./...` runs with the working directory set to the package's own
// source directory, so the checkout — and harness/corrections/ above it — is
// always reachable, and a missing directory there IS the defect: this package
// claims to encode JIVO's corrections, and being unable to read them means the
// claim cannot be checked.
//
// The live acceptance suite is different. It is cross-compiled to a binary and
// copied to the VPS (`scp domain-live.test vps:/tmp/`), where no checkout exists
// by design. The skip is therefore gated on the SOURCE FILE being absent, not on
// the corrections being absent — so it can only trigger where the check is
// meaningless, and never in the gate. A relocated binary that somehow does carry
// the source still has to pass.
func correctionsDir(t *testing.T) string {
	t.Helper()
	if _, err := os.Stat("relatedparty.go"); err != nil {
		t.Skip("not running from the package source directory (a relocated test binary), so harness/corrections/ cannot be reached; this check runs in the normal `go test ./...` gate")
	}
	dir, err := filepath.Abs(".")
	if err != nil {
		t.Fatalf("abs: %v", err)
	}
	for i := 0; i < 8; i++ {
		cand := filepath.Join(dir, "harness", "corrections")
		if fi, err := os.Stat(cand); err == nil && fi.IsDir() {
			return cand
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	t.Fatal("could not find harness/corrections/ above the package directory, but the package source IS here. This package claims to encode JIVO's corrections; if the records cannot be read, that claim cannot be checked and must not be trusted.")
	return ""
}

type correction struct {
	id     string
	status string
	body   string
}

var (
	idRe     = regexp.MustCompile(`(?m)^id:\s*(\S+)`)
	statusRe = regexp.MustCompile(`(?m)^status:\s*(\S+)`)
)

func loadCorrections(t *testing.T) map[string]correction {
	t.Helper()
	dir := correctionsDir(t)
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("read %s: %v", dir, err)
	}
	out := map[string]correction{}
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".md") || e.Name() == "INDEX.md" {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(dir, e.Name()))
		if err != nil {
			t.Fatalf("read %s: %v", e.Name(), err)
		}
		body := string(raw)
		m := idRe.FindStringSubmatch(body)
		if m == nil {
			t.Errorf("%s has no id: field", e.Name())
			continue
		}
		st := ""
		if s := statusRe.FindStringSubmatch(body); s != nil {
			st = s[1]
		}
		out[m[1]] = correction{id: m[1], status: st, body: body}
	}
	if len(out) == 0 {
		t.Fatalf("no correction records found in %s; the assertion would be vacuous", dir)
	}
	return out
}

// Every value this package hard-codes must still appear in the correction record
// that authorises it. Edit the record and this fails until the Go is edited too.
func TestEncodedValuesStillMatchTheCorrectionRecords(t *testing.T) {
	corrections := loadCorrections(t)

	cases := []struct {
		id     string
		what   string
		tokens []string
	}{
		{"C-0001", "the units rule", []string{"PCS", "cartons"}},
		{"C-0002", "the intercompany CardCode", []string{InternalCardCode}},
		{"C-0003", "the segmentation fields", []string{"U_TYPE", "U_Sub_Group"}},
		{"C-0004", "the combo item group", []string{ComboItemGroup, "U_Sub_Group"}},
	}
	for _, tc := range cases {
		c, ok := corrections[tc.id]
		if !ok {
			t.Errorf("%s is cited all over this package but has no record in harness/corrections/", tc.id)
			continue
		}
		if c.status != "active" {
			t.Errorf("%s is status %q, but this package still encodes it as settled truth", tc.id, c.status)
		}
		for _, tok := range tc.tokens {
			if !strings.Contains(c.body, tok) {
				t.Errorf("%s (%s): the Go code hard-codes %q, but %s no longer mentions it. Re-read the record and update the code — the record is the source of truth, not this binary.",
					tc.id, tc.what, tok, tc.id)
			}
		}
	}
}

// C-0002's evidence names the branch cards explicitly. The split must actually
// cover them: this is the drift that already happened, pinned so it cannot
// happen again quietly.
func TestC0002BranchCardsAreActuallyClassified(t *testing.T) {
	c, ok := loadCorrections(t)["C-0002"]
	if !ok {
		t.Fatal("C-0002 has no record")
	}
	if !strings.Contains(c.body, "branch cards") {
		t.Skip("C-0002 no longer mentions branch cards; TestEncodedValuesStillMatchTheCorrectionRecords covers the rest")
	}
	// The record says Mart's books carry branch cards AND a JIVO WELLNESS card.
	// Both must be in Mart's catalogue, or the code encodes less than the record.
	mart := RelatedPartyCards("JIVO_MART_HANADB")
	branches, wellness := 0, 0
	for _, card := range mart {
		switch {
		case strings.Contains(strings.ToUpper(card.CardName), "WELLNESS"):
			wellness++
		case strings.Contains(strings.ToUpper(card.CardName), "JIVO MART"):
			branches++
		}
	}
	if branches < 2 {
		t.Errorf("C-0002 says Mart's books carry JIVO MART branch cards (DL/PB/HR/KT/KR/RJ/UP) needing the same treatment; only %d are catalogued", branches)
	}
	if wellness < 1 {
		t.Errorf("C-0002 says Mart's books carry a JIVO WELLNESS PVT LTD card needing the same treatment; none is catalogued")
	}
}

// The digest that reaches a session must not still be describing behaviour the
// code has moved past. This catches the reverse drift: code fixed, record stale.
func TestCorrectionRulesDoNotContradictTheCode(t *testing.T) {
	c := loadCorrections(t)["C-0004"]
	// C-0004's rule offers two acceptable behaviours: split SALES BOM out, or say
	// it is counted whole. The tool does the first and says the second.
	if !strings.Contains(c.body, "SALES BOM") {
		t.Fatalf("C-0004 no longer names the item group, so ComboItemGroup = %q has no authority behind it", ComboItemGroup)
	}
	note := salesNote(emptyAggResult(), nil)
	if !strings.Contains(note, ComboItemGroup) || !strings.Contains(note, "counted whole") {
		t.Errorf("the sales note does not offer C-0004's stated remedy:\n%s", note)
	}
}
