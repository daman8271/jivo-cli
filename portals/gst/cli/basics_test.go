package main

import (
	"strings"
	"testing"
)

// TestInr pins the house money format (dsr-cli/internal/cli/domain.go:147-183):
// Indian digit grouping, ₹ prefix, crore/lakh suffix for big sums.
func TestInr(t *testing.T) {
	cases := []struct {
		in   float64
		want string
	}{
		{73216548, "₹7,32,16,548.00 (7.32 Cr)"},
		{57314, "₹57,314.00"},
		{143296.5, "₹1,43,296.50 (1.43 L)"},
		{-500, "-₹500.00"},
		{0, "₹0.00"},
	}
	for _, c := range cases {
		if got := inr(c.in); got != c.want {
			t.Errorf("inr(%v) = %q want %q", c.in, got, c.want)
		}
	}
}

// TestExitCodeFor pins the house exit-code table (sap-b1/cli/internal/cli/exitcode.go:10-20).
// There is no exit 7 here: this CLI never writes.
func TestExitCodeFor(t *testing.T) {
	cases := []struct {
		err  error
		want int
	}{
		{nil, exitOK},
		{errUsage("bad flag"), exitUsage},
		{errConfig("no .env"), exitConfig},
		{errAuth("session expired"), exitAuth},
		{errGuard("blocked"), exitNetwork},
		{errNetwork("dial", nil), exitNetwork},
		{&apiError{Code: "RET11403", Message: "Invalid API Request"}, exitAPI},
		{errPlain("something else"), exitUsage},
	}
	for _, c := range cases {
		if got := exitCodeFor(c.err); got != c.want {
			t.Errorf("exitCodeFor(%v) = %d want %d", c.err, got, c.want)
		}
	}
}

// TestPeriodParse pins the GST period vocabulary: MMYYYY codes, a financial year
// expanding to its 12 months (April→March), and the portal's two date spellings.
func TestPeriodParse(t *testing.T) {
	if _, err := parsePeriod("072026"); err != nil {
		t.Fatalf("parsePeriod(072026): %v", err)
	}
	if _, err := parsePeriod("132026"); err == nil {
		t.Error("month 13 should not parse")
	}
	if _, err := parsePeriod("72026"); err == nil {
		t.Error("5-digit period should not parse")
	}

	ps, err := fyPeriods("2026-27")
	if err != nil {
		t.Fatalf("fyPeriods: %v", err)
	}
	if len(ps) != 12 {
		t.Fatalf("fyPeriods(2026-27) = %d periods want 12", len(ps))
	}
	if ps[0] != "042026" || ps[11] != "032027" {
		t.Errorf("fyPeriods bounds = %q..%q want 042026..032027", ps[0], ps[11])
	}
	if _, err := fyPeriods("2026-28"); err == nil {
		t.Error("2026-28 is not a financial year")
	}

	// The portal spells dates both ways: itcdtls uses dd/mm/yyyy, formdetails dd-mm-yyyy.
	for _, s := range []string{"11/08/2026", "11-08-2026"} {
		d, err := parsePortalDate(s)
		if err != nil {
			t.Fatalf("parsePortalDate(%q): %v", s, err)
		}
		if got := isoDate(d); got != "2026-08-11" {
			t.Errorf("parsePortalDate(%q) → %q want 2026-08-11", s, got)
		}
	}
	// and back out to the portal's query format
	d, _ := parseISODate("2026-04-01")
	if got := portalDate(d); got != "01/04/2026" {
		t.Errorf("portalDate = %q want 01/04/2026", got)
	}
	// fy that a period belongs to
	if got := fyOfPeriod("032027"); got != "2026-27" {
		t.Errorf("fyOfPeriod(032027) = %q want 2026-27", got)
	}
	if got := fyOfPeriod("042026"); got != "2026-27" {
		t.Errorf("fyOfPeriod(042026) = %q want 2026-27", got)
	}
}

// TestBestEffortCount pins the agent envelope's count for the shapes GST returns:
// a bare array (efiledReturns), a {data:{…}} wrapper, a bare object.
func TestBestEffortCount(t *testing.T) {
	if got := bestEffortCount([]byte(`[{"a":1},{"a":2}]`)); got != 2 {
		t.Errorf("array count = %d want 2", got)
	}
	if got := bestEffortCount([]byte(`{"data":{"tr":[1,2,3]}}`)); got != 3 {
		t.Errorf("data.tr count = %d want 3", got)
	}
	if got := bestEffortCount([]byte(`{"op_tot":1}`)); got != 1 {
		t.Errorf("object count = %d want 1", got)
	}
}

// TestMaskedNeverEchoesPassword covers both the listing path AND the error path:
// no code that renders a credential may ever print it whole (CRITIQUE §4).
func TestMaskedNeverEchoesPassword(t *testing.T) {
	const secret = "SuperSecret123!"
	if m := masked(secret); strings.Contains(m, secret) {
		t.Fatalf("masked(%q) leaked the secret: %q", secret, m)
	}
	if m := masked(secret); !strings.HasPrefix(m, "Supe") || !strings.HasSuffix(m, "123!") {
		t.Errorf("masked = %q want first4…last4", m)
	}
	if masked("") != "MISSING" {
		t.Error("empty credential should render as MISSING")
	}
	if masked("short") != "present" {
		t.Error("short credential should render as present, not a prefix/suffix")
	}

	// A PASSWORD gets no prefix/suffix at all: across 8 registrations the house
	// first4…last4 masking would have shown that they share a prefix.
	if got := maskedSecret(secret); got != "present" {
		t.Errorf("maskedSecret = %q want %q", got, "present")
	}
	if maskedSecret("") != "MISSING" {
		t.Error("an unset password must read MISSING")
	}
}
