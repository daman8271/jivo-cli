package main

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

func useTempStateDir(t *testing.T) string {
	t.Helper()
	d := t.TempDir()
	t.Setenv("GST_STATE_DIR", d)
	return d
}

// TestSessionRoundTripThreeHosts: one jar covers all four GST hosts (they share
// the .gst.gov.in cookie domain), and it survives a save/load cycle intact —
// including the TS* WAF cookies, which are the ones an F5 ASM actually keys on.
func TestSessionRoundTripThreeHosts(t *testing.T) {
	useTempStateDir(t)
	exp := time.Now().Add(30 * time.Minute).Truncate(time.Second)
	s := &session{
		GSTIN:    "06AAAAA0000A1Z0",
		Username: "jivotest729",
		Stage:    stageAuthenticated,
		Cookies: []sessionCookie{
			{Name: "AuthToken", Value: "tok", Domain: ".gst.gov.in", Path: "/", Expires: exp},
			{Name: "UserName", Value: "u", Domain: ".gst.gov.in", Path: "/"},
			{Name: "TS0134d082", Value: "f5a", Domain: ".gst.gov.in", Path: "/"},
			{Name: "TS01255980", Value: "f5b", Domain: "return.gst.gov.in", Path: "/"},
			{Name: "Lang", Value: "en", Domain: "payment.gst.gov.in", Path: "/"},
			{Name: "twobee", Value: "x", Domain: "gstr2b.gst.gov.in", Path: "/"},
		},
	}
	if err := s.save(); err != nil {
		t.Fatalf("save: %v", err)
	}
	got, err := loadSession("06AAAAA0000A1Z0")
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if got.Username != s.Username || got.Stage != stageAuthenticated || len(got.Cookies) != len(s.Cookies) {
		t.Fatalf("round trip lost data: %+v", got)
	}
	if got.SavedAt.IsZero() {
		t.Error("save() must stamp saved_at")
	}
	if !got.Cookies[0].Expires.Equal(exp) {
		t.Errorf("cookie expiry lost: %v want %v", got.Cookies[0].Expires, exp)
	}

	// every host must see the cookies that belong to it
	for _, h := range allHosts {
		cs := got.cookiesFor(h)
		if len(cs) < 3 {
			t.Errorf("host %s got %d cookies, want at least the 3 domain-wide ones", h, len(cs))
		}
		var names []string
		for _, c := range cs {
			names = append(names, c.Name)
		}
		joined := strings.Join(names, ",")
		if !strings.Contains(joined, "AuthToken") || !strings.Contains(joined, "TS0134d082") {
			t.Errorf("host %s is missing the session/WAF cookies: %v", h, names)
		}
	}
	// a host-specific cookie does not leak to another host
	for _, c := range got.cookiesFor(hostServices) {
		if c.Name == "twobee" {
			t.Error("a gstr2b-only cookie leaked to services.gst.gov.in")
		}
	}
}

// A pre-login jar (the cookies GET /services/login and the captcha GET mint) has
// to survive BETWEEN CLI invocations, or the two-step agent login cannot work:
// the captcha the operator is reading is bound to that jar.
func TestPreLoginStageSurvivesBetweenInvocations(t *testing.T) {
	useTempStateDir(t)
	pre := &session{
		GSTIN: "06AAAAA0000A1Z0",
		Stage: stagePreLogin,
		Cookies: []sessionCookie{
			{Name: "TS0134d082", Value: "preauth", Domain: ".gst.gov.in", Path: "/"},
		},
	}
	if err := pre.save(); err != nil {
		t.Fatal(err)
	}
	got, err := loadSession("06AAAAA0000A1Z0")
	if err != nil {
		t.Fatal(err)
	}
	if got.Stage != stagePreLogin {
		t.Fatalf("stage = %q want %q", got.Stage, stagePreLogin)
	}
	if got.authenticated() {
		t.Error("a pre-login jar must not count as authenticated")
	}
}

func TestSessionFileIs0600(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("unix file modes are not meaningful on windows")
	}
	dir := useTempStateDir(t)
	s := &session{GSTIN: "06AAAAA0000A1Z0", Stage: stageAuthenticated}
	if err := s.save(); err != nil {
		t.Fatal(err)
	}
	fi, err := os.Stat(sessionPath("06AAAAA0000A1Z0"))
	if err != nil {
		t.Fatal(err)
	}
	if fi.Mode().Perm() != 0o600 {
		t.Errorf("session file mode = %v want 0600 — it is a bearer token to a portal that can file returns", fi.Mode().Perm())
	}
	di, err := os.Stat(filepath.Join(dir, "gst-portal"))
	if err != nil {
		t.Fatal(err)
	}
	if di.Mode().Perm() != 0o700 {
		t.Errorf("session dir mode = %v want 0700", di.Mode().Perm())
	}
}

func TestSessionPathIsPerGSTIN(t *testing.T) {
	useTempStateDir(t)
	a := sessionPath("06AAAAA0000A1Z0")
	b := sessionPath("09AAAAA0000A1ZU")
	if a == b {
		t.Fatal("two registrations must not share a session file")
	}
	if !strings.Contains(filepath.Base(a), "06AAAAA0000A1Z0") {
		t.Errorf("session filename should name the GSTIN: %s", a)
	}
	// a GSTIN is the only thing that may shape the filename — no traversal
	if p := sessionPath("../../etc/passwd"); strings.Contains(p, "..") {
		t.Errorf("session path must not accept traversal: %s", p)
	}
}

func TestSessionExpiredByAge(t *testing.T) {
	useTempStateDir(t)
	s := &session{GSTIN: "06AAAAA0000A1Z0", Stage: stageAuthenticated, SavedAt: time.Now().Add(-2 * time.Hour)}
	if !s.expired(sessionMaxAge) {
		t.Error("a two-hour-old session must be treated as expired")
	}
	s.SavedAt = time.Now()
	if s.expired(sessionMaxAge) {
		t.Error("a fresh session must not be expired")
	}
	// a cookie past its own expiry is dropped on load
	s.Cookies = []sessionCookie{
		{Name: "stale", Value: "x", Domain: ".gst.gov.in", Path: "/", Expires: time.Now().Add(-time.Hour)},
		{Name: "AuthToken", Value: "y", Domain: ".gst.gov.in", Path: "/"},
	}
	if err := s.save(); err != nil {
		t.Fatal(err)
	}
	got, err := loadSession("06AAAAA0000A1Z0")
	if err != nil {
		t.Fatal(err)
	}
	for _, c := range got.cookiesFor(hostServices) {
		if c.Name == "stale" {
			t.Error("an expired cookie must not be replayed")
		}
	}
}

func TestMissingSessionIsNotAnError(t *testing.T) {
	useTempStateDir(t)
	s, err := loadSession("27AAAAA0000A2ZV")
	if err != nil {
		t.Fatalf("a missing session file is a normal state, not an error: %v", err)
	}
	if s != nil {
		t.Errorf("expected nil session, got %+v", s)
	}
	if got := sessionSummary("27AAAAA0000A2ZV"); !strings.Contains(strings.ToLower(got), "no cached session") {
		t.Errorf("sessionSummary = %q, should say there is no cached session", got)
	}
}

// `auth import` consumes what a browser exporter emits (Playwright/`$B cookies`
// style) so an operator who logged in elsewhere never has to solve a captcha here.
func TestImportPlaywrightCookies(t *testing.T) {
	raw := []byte(`[
	  {"name":"AuthToken","value":"abc","domain":".gst.gov.in","path":"/","expires":1787000000,"httpOnly":true,"secure":true},
	  {"name":"TS0134d082","value":"f5","domain":".gst.gov.in","path":"/"},
	  {"name":"irrelevant","value":"z","domain":".example.com","path":"/"}
	]`)
	cs, err := importPlaywrightCookies(raw)
	if err != nil {
		t.Fatalf("import: %v", err)
	}
	if len(cs) != 2 {
		t.Fatalf("imported %d cookies, want 2 (non-GST domains dropped)", len(cs))
	}
	if cs[0].Name != "AuthToken" || cs[0].Value != "abc" || !cs[0].Secure {
		t.Errorf("cookie fields lost: %+v", cs[0])
	}
	if cs[0].Expires.IsZero() {
		t.Error("numeric `expires` should be decoded")
	}
	if _, err := importPlaywrightCookies([]byte(`{"not":"an array"}`)); err == nil {
		t.Error("a non-array import must be a clear error")
	}
	if _, err := importPlaywrightCookies([]byte(`[{"name":"x","value":"y","domain":".example.com"}]`)); err == nil {
		t.Error("importing zero GST cookies must be an error, not a silent empty session")
	}
}
