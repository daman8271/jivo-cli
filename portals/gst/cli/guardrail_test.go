package main

import (
	"strings"
	"testing"
)

// TestForbiddenBlocksWrites is the read-only guard's core table. Every entry is
// a thing RULE 0 forbids on a live statutory portal, plus the false-friends that
// must NOT be caught by the same rules (efiledReturns contains "file",
// filingsnapshot contains "fil", searcharnusngdate contains "arn").
func TestForbiddenBlocksWrites(t *testing.T) {
	blocked := []struct {
		what               string
		method, host, path string
	}{
		{"PUT anywhere", "PUT", hostReturn, "/returns/auth/api/itcbalance"},
		{"PATCH anywhere", "PATCH", hostReturn, "/returns/auth/api/itcbalance"},
		{"DELETE anywhere", "DELETE", hostReturn, "/returns/auth/api/itcbalance"},
		{"logout kills the operator's session", methodGET, hostServices, "/services/logout"},
		{"3B save", methodPOST, hostReturn, "/returns/auth/api/gstr3b/save"},
		{"3B submit", methodPOST, hostReturn, "/returns/auth/api/gstr3b/submit"},
		{"3B file/return filing", methodPOST, hostReturn, "/returns/auth/api/gstr3b/file"},
		{"offset liability", methodPOST, hostReturn, "/returns/auth/api/gstr3b/setoff"},
		{"create a challan", methodPOST, hostPayment, "/payment/auth/api/challan/create"},
		{"GSTR-1 generate summary", methodGET, hostReturn, "/returns/auth/api/gstr1/generatesummary"},
		{"2B generate-then-download", methodGET, hostGSTR2B, "/gstr2b/auth/api/gstr2b/gendwnldjson"},
		{"any download", methodGET, hostReturn, "/returns/auth/api/gstr1/download"},
		{"reset a form", methodPOST, hostReturn, "/returns/auth/api/gstr3b/reset"},
		{"amend", methodPOST, hostReturn, "/returns/auth/api/gstr1/amend"},
		{"an unknown but harmless-looking read", methodGET, hostReturn, "/returns/auth/api/somethingnew"},
		{"a foreign host", methodGET, "evil.example.com", "/returns/auth/api/itcbalance"},
		{"a relative path", methodGET, hostReturn, "returns/auth/api/itcbalance"},
		{"path traversal", methodGET, hostReturn, "/returns/auth/../../services/logout"},
		{"POST to a GET-only row", methodPOST, hostReturn, "/returns/auth/api/itcbalance"},
	}
	for _, b := range blocked {
		if err := forbidden(b.method, b.host, b.path, b.path, nil, nil); err == nil {
			t.Errorf("BLOCK EXPECTED (%s): %s %s%s was allowed", b.what, b.method, b.host, b.path)
		} else if exitCodeFor(err) != exitNetwork {
			t.Errorf("%s %s: guard errors must exit 5 (nothing was sent), got %d", b.method, b.path, exitCodeFor(err))
		}
	}
}

// TestForbiddenAllowsEveryTableRow — no dead rows: everything in the allowlist
// must pass its own guard, including the three sanctioned POSTs.
func TestForbiddenAllowsEveryTableRow(t *testing.T) {
	for _, e := range endpoints {
		params := map[string]string{}
		for _, p := range e.Params {
			params[p] = "2026-27"
		}
		resolved, err := e.resolvePath(params)
		if err != nil {
			t.Fatalf("%s: resolvePath: %v", e.Name, err)
		}
		if err := forbidden(e.Method, e.Host, e.Path, resolved, e.Query, e.Body); err != nil {
			t.Errorf("DEAD ROW — allowlisted %s is blocked by the guard: %v", e.Name, err)
		}
	}
}

// TestForbiddenRejectsUnknownKeys: only the keys the portal itself sends may go
// on the wire. This is the rule that stops a future "&action=submit".
func TestForbiddenRejectsUnknownKeys(t *testing.T) {
	e, _ := lookup(epITCDetails)
	if err := forbidden(e.Method, e.Host, e.Path, e.Path, []string{"fdate", "tdate"}, nil); err != nil {
		t.Fatalf("the endpoint's own query keys must pass: %v", err)
	}
	err := forbidden(e.Method, e.Host, e.Path, e.Path, []string{"fdate", "action"}, nil)
	if err == nil {
		t.Fatal("an unknown query key must be refused")
	}
	if !strings.Contains(err.Error(), "action") {
		t.Errorf("the error should name the offending key, got: %v", err)
	}

	f, _ := lookup(epEfiledReturns)
	if err := forbidden(f.Method, f.Host, f.Path, f.Path, nil, []string{"fy", "rfp", "rtntp"}); err != nil {
		t.Fatalf("a subset of the allowed body keys must pass: %v", err)
	}
	if err := forbidden(f.Method, f.Host, f.Path, f.Path, nil, []string{"fy", "flag"}); err == nil {
		t.Fatal("an unknown body key must be refused")
	}

	// profile/detail takes an EMPTY body — any key at all is refused.
	p, _ := lookup(epProfile)
	if err := forbidden(p.Method, p.Host, p.Path, p.Path, nil, []string{"gstin"}); err == nil {
		t.Fatal("profile/detail accepts no body keys; one must be refused")
	}
}

// TestOnlyThreePOSTsExist pins the sanctioned-write surface. If a fourth POST
// ever appears in the table, this test makes someone justify it in review.
func TestOnlyThreePOSTsExist(t *testing.T) {
	var posts []string
	for _, e := range endpoints {
		if e.Method == methodPOST {
			posts = append(posts, e.Name)
		}
	}
	want := map[string]bool{epAuthenticate: true, epEfiledReturns: true, epProfile: true}
	if len(posts) != len(want) {
		t.Fatalf("POST rows = %v; exactly three read-shaped POSTs are sanctioned", posts)
	}
	for _, p := range posts {
		if !want[p] {
			t.Errorf("unsanctioned POST row %q — RULE 0 allows only login, efiledReturns and profile/detail", p)
		}
	}
}

// TestPathParamsCannotEscapeTheirSegment: a financial year is a segment, not a
// place to smuggle another path.
func TestPathParamsCannotEscapeTheirSegment(t *testing.T) {
	e, _ := lookup(epMasterMonths)
	if _, err := e.resolvePath(map[string]string{"fy": "2026-27"}); err != nil {
		t.Fatalf("a normal fy must resolve: %v", err)
	}
	for _, bad := range []string{"../../services/logout", "2026-27?x=1", "a/b", ""} {
		if _, err := e.resolvePath(map[string]string{"fy": bad}); err == nil {
			t.Errorf("path parameter %q should have been refused", bad)
		}
	}
}

// TestFingerprintCarriesTheSameUA — CRITIQUE: the request User-Agent and the UA
// inside the mFP fingerprint are shipped together at login; if they disagree the
// portal's fingerprint check has an obvious tell.
func TestFingerprintCarriesTheSameUA(t *testing.T) {
	blob := mfpBlob()
	if !strings.Contains(blob, browserUA) {
		t.Fatalf("mFP does not carry browserUA")
	}
	for _, want := range []string{`"VERSION":"2.1"`, `"MFP"`, `"Screen"`, `"System"`, `"MESC"`} {
		if !strings.Contains(blob, want) {
			t.Errorf("mFP is missing %s — the portal expects the whole shape", want)
		}
	}
}

// TestRefererIsSetForEveryHost — a JSON call with no gst.gov.in Referer is
// bounced to /services/error/accessdenied even with a valid session (API.md).
func TestRefererIsSetForEveryHost(t *testing.T) {
	for _, e := range endpoints {
		if r := e.referer(); !strings.HasPrefix(r, "https://") || !strings.Contains(r, "gst.gov.in") {
			t.Errorf("%s has no usable Referer: %q", e.Name, r)
		}
	}
	for _, h := range allHosts {
		if hostReferer[h] == "" {
			t.Errorf("host %s has no default Referer", h)
		}
	}
}
