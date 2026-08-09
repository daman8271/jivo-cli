package httpapi

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"jivodist/internal/engine"
)

// The bundle builder listens on loopback, which means every web page the
// operator has open can reach it. These tests pin the three checks that stop a
// hostile page from making this machine build and hand over a zip of production
// credentials. None of it is authentication — the operator sees no friction.

func serve(t *testing.T, s *Server, r *http.Request) *httptest.ResponseRecorder {
	t.Helper()
	rec := httptest.NewRecorder()
	s.Routes().ServeHTTP(rec, r)
	return rec
}

func jsonReq(method, target, body string) *http.Request {
	r := httptest.NewRequest(method, target, strings.NewReader(body))
	r.Host = "127.0.0.1:7788"
	r.Header.Set("Content-Type", "application/json")
	return r
}

// TestWrongHostIsRefused — DNS rebinding gives an attacker's page a connection
// to 127.0.0.1 while the Host header still says their domain.
func TestWrongHostIsRefused(t *testing.T) {
	s := New(testRepoRoot(t))
	for _, host := range []string{
		"evil.com",
		"evil.com:7788",
		"rebound.attacker.test:7788",
		"127.0.0.1:9999", // right host, wrong port
		"192.168.1.41:7788",
		"",
	} {
		r := httptest.NewRequest(http.MethodGet, "/api/manifest", nil)
		r.Host = host
		rec := serve(t, s, r)
		if rec.Code != http.StatusForbidden {
			t.Errorf("Host %q: status %d, want 403", host, rec.Code)
		}
	}
}

// TestLoopbackHostSpellingsAreAccepted — all the ways a browser or curl can
// address the bound port.
func TestLoopbackHostSpellingsAreAccepted(t *testing.T) {
	s := New(testRepoRoot(t))
	for _, host := range []string{"127.0.0.1:7788", "localhost:7788", "[::1]:7788"} {
		r := httptest.NewRequest(http.MethodGet, "/api/manifest", nil)
		r.Host = host
		rec := serve(t, s, r)
		if rec.Code != http.StatusOK {
			t.Errorf("Host %q: status %d, want 200", host, rec.Code)
		}
	}
}

// TestNonLoopbackBindAllowsItsOwnHost — the -addr escape hatch must keep
// working without widening the allowlist to everything.
func TestNonLoopbackBindAllowsItsOwnHost(t *testing.T) {
	s := New(testRepoRoot(t))
	s.Addr = "10.0.0.5:9000"
	allowed := s.allowedHosts()
	for _, want := range []string{"10.0.0.5:9000", "127.0.0.1:9000", "localhost:9000", "[::1]:9000"} {
		if !allowed[want] {
			t.Errorf("%s should be allowed when bound to 10.0.0.5:9000", want)
		}
	}
	for _, bad := range []string{"10.0.0.5:7788", "evil.com:9000", "10.0.0.6:9000"} {
		if allowed[bad] {
			t.Errorf("%s should not be allowed", bad)
		}
	}
}

// TestStateChangingMethodsRequireJSON — requiring application/json makes the
// request non-simple, so a cross-origin attempt must preflight, and the
// preflight dies because we send no CORS headers.
func TestStateChangingMethodsRequireJSON(t *testing.T) {
	s := New(testRepoRoot(t))
	cases := []struct {
		name, method, target, contentType string
	}{
		{"form post", http.MethodPost, "/api/bundle", "application/x-www-form-urlencoded"},
		{"text post", http.MethodPost, "/api/bundle", "text/plain"},
		{"multipart post", http.MethodPost, "/api/bundle", "multipart/form-data; boundary=x"},
		{"no content type", http.MethodPost, "/api/bundle", ""},
		{"delete without json", http.MethodDelete, "/api/bundle/whatever.zip", ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			r := httptest.NewRequest(tc.method, tc.target, strings.NewReader(`{"target":"mac-arm64"}`))
			r.Host = "127.0.0.1:7788"
			if tc.contentType != "" {
				r.Header.Set("Content-Type", tc.contentType)
			}
			rec := serve(t, s, r)
			if rec.Code != http.StatusUnsupportedMediaType {
				t.Errorf("status %d, want 415", rec.Code)
			}
		})
	}

	// application/json with a charset parameter is still json.
	r := jsonReq(http.MethodPost, "/api/bundle", `{"target":"mac-arm64","components":[]}`)
	r.Header.Set("Content-Type", "application/json; charset=utf-8")
	if rec := serve(t, s, r); rec.Code == http.StatusUnsupportedMediaType {
		t.Error("application/json; charset=utf-8 should be accepted")
	}
}

// TestCrossSiteFetchIsRefused — the browser tells us where the request came
// from; anything but our own page is refused.
func TestCrossSiteFetchIsRefused(t *testing.T) {
	s := New(testRepoRoot(t))
	for _, site := range []string{"cross-site", "same-site"} {
		r := jsonReq(http.MethodPost, "/api/bundle", `{"target":"mac-arm64","components":["hana-sql"]}`)
		r.Header.Set("Sec-Fetch-Site", site)
		rec := serve(t, s, r)
		if rec.Code != http.StatusForbidden {
			t.Errorf("Sec-Fetch-Site: %s → status %d, want 403", site, rec.Code)
		}
	}
	// A GET from a hostile page is just as unwelcome.
	r := httptest.NewRequest(http.MethodGet, "/api/manifest", nil)
	r.Host = "127.0.0.1:7788"
	r.Header.Set("Sec-Fetch-Site", "cross-site")
	if rec := serve(t, s, r); rec.Code != http.StatusForbidden {
		t.Errorf("cross-site GET status %d, want 403", rec.Code)
	}
}

// TestSameOriginAndDirectClientsPass — no friction for the real UI, for curl,
// or for someone typing the URL.
func TestSameOriginAndDirectClientsPass(t *testing.T) {
	s := New(testRepoRoot(t))
	for _, site := range []string{"same-origin", "none", ""} {
		r := httptest.NewRequest(http.MethodGet, "/api/manifest", nil)
		r.Host = "127.0.0.1:7788"
		if site != "" {
			r.Header.Set("Sec-Fetch-Site", site)
		}
		rec := serve(t, s, r)
		if rec.Code != http.StatusOK {
			t.Errorf("Sec-Fetch-Site %q: status %d, want 200", site, rec.Code)
		}
	}
}

// TestNoCORSHeadersEverEmitted — one Access-Control-Allow-Origin would undo the
// whole preflight defence.
func TestNoCORSHeadersEverEmitted(t *testing.T) {
	s := New(testRepoRoot(t))
	requests := []*http.Request{
		httptest.NewRequest(http.MethodGet, "/api/manifest", nil),
		httptest.NewRequest(http.MethodGet, "/api/bundles", nil),
		httptest.NewRequest(http.MethodOptions, "/api/bundle", nil),
		httptest.NewRequest(http.MethodGet, "/", nil),
		jsonReq(http.MethodPost, "/api/bundle", `{"target":"mac-arm64","components":[]}`),
	}
	for _, r := range requests {
		if r.Host == "" || !strings.Contains(r.Host, "127.0.0.1") {
			r.Host = "127.0.0.1:7788"
		}
		r.Header.Set("Origin", "https://evil.com")
		rec := serve(t, s, r)
		for name := range rec.Header() {
			if strings.HasPrefix(strings.ToLower(name), "access-control-") {
				t.Errorf("%s %s emitted a CORS header: %s", r.Method, r.URL.Path, name)
			}
		}
	}
}

// TestHardeningCoversTheStaticRoot — the frontend page is served from the same
// origin, so it is behind the same checks.
func TestHardeningCoversTheStaticRoot(t *testing.T) {
	s := New(testRepoRoot(t))
	r := httptest.NewRequest(http.MethodGet, "/", nil)
	r.Host = "evil.com"
	if rec := serve(t, s, r); rec.Code != http.StatusForbidden {
		t.Errorf("static root with a bad Host: status %d, want 403", rec.Code)
	}
}

// TestNoStoreOnCredentialResponses — bundle metadata and the zips themselves
// must not sit in any cache.
func TestNoStoreOnCredentialResponses(t *testing.T) {
	s := New(testRepoRoot(t))
	for _, path := range []string{"/api/manifest", "/api/bundles"} {
		r := httptest.NewRequest(http.MethodGet, path, nil)
		r.Host = "127.0.0.1:7788"
		rec := serve(t, s, r)
		if got := rec.Header().Get("Cache-Control"); got != "no-store" {
			t.Errorf("%s Cache-Control = %q, want no-store", path, got)
		}
	}

	// And on the download itself.
	res := buildViaAPI(t, s)
	t.Cleanup(func() { os.Remove(res.ZipPath) })
	r := httptest.NewRequest(http.MethodGet, res.DownloadURL, nil)
	r.Host = "127.0.0.1:7788"
	rec := serve(t, s, r)
	if rec.Code != http.StatusOK {
		t.Fatalf("download status %d", rec.Code)
	}
	if got := rec.Header().Get("Cache-Control"); got != "no-store" {
		t.Errorf("download Cache-Control = %q, want no-store", got)
	}
}

func buildViaAPI(t *testing.T, s *Server) engine.Result {
	t.Helper()
	r := jsonReq(http.MethodPost, "/api/bundle",
		`{"target":"mac-arm64","components":["hana-sql"],"recipient":"hardening","include_docs":false}`)
	rec := serve(t, s, r)
	if rec.Code != http.StatusOK {
		t.Fatalf("build status %d: %s", rec.Code, rec.Body.String())
	}
	var res engine.Result
	if err := json.Unmarshal(rec.Body.Bytes(), &res); err != nil {
		t.Fatal(err)
	}
	return res
}

// ---------------------------------------------------------- M1 / M2 / m5 / M6

// TestBundleIsAddressableByIDAfterRestart — the id lives in the filename, so a
// fresh server can still find and serve a zip it did not build.
func TestBundleIsAddressableByIDAfterRestart(t *testing.T) {
	s := New(testRepoRoot(t))
	res := buildViaAPI(t, s)
	t.Cleanup(func() { os.Remove(res.ZipPath) })

	fresh := New(testRepoRoot(t)) // empty in-memory map
	r := httptest.NewRequest(http.MethodGet, "/api/bundle/"+res.BundleID+"/download", nil)
	r.Host = "127.0.0.1:7788"
	rec := serve(t, fresh, r)
	if rec.Code != http.StatusOK {
		t.Errorf("a restarted server could not serve %s: status %d", res.BundleID, rec.Code)
	}
	if int64(rec.Body.Len()) != res.SizeBytes {
		t.Errorf("served %d bytes, built %d", rec.Body.Len(), res.SizeBytes)
	}
}

// TestListIgnoresPartialBundles — a *.zip.tmp is a build in flight, not
// something to offer the operator.
func TestListIgnoresPartialBundles(t *testing.T) {
	root := testRepoRoot(t)
	s := New(root)
	partial := filepath.Join(root, engine.DistDir, "jivo-kit-mac-arm64-20260810-1430-dead-partial.zip.tmp")
	if err := os.MkdirAll(filepath.Dir(partial), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(partial, []byte("half a zip"), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { os.Remove(partial) })

	r := httptest.NewRequest(http.MethodGet, "/api/bundles", nil)
	r.Host = "127.0.0.1:7788"
	rec := serve(t, s, r)
	var list []BundleInfo
	if err := json.Unmarshal(rec.Body.Bytes(), &list); err != nil {
		t.Fatal(err)
	}
	for _, b := range list {
		if strings.Contains(b.Filename, ".tmp") {
			t.Errorf("a half-written bundle was listed: %s", b.Filename)
		}
	}
	// And it cannot be downloaded either.
	dl := httptest.NewRequest(http.MethodGet, "/api/bundle/"+filepath.Base(partial)+"/download", nil)
	dl.Host = "127.0.0.1:7788"
	if rec := serve(t, s, dl); rec.Code != http.StatusNotFound {
		t.Errorf("partial bundle download status %d, want 404", rec.Code)
	}
}

// TestDeleteByFilenamePurgesTheIDEntry — otherwise the id keeps returning 200
// for a file that is gone.
func TestDeleteByFilenamePurgesTheIDEntry(t *testing.T) {
	s := New(testRepoRoot(t))
	res := buildViaAPI(t, s)
	t.Cleanup(func() { os.Remove(res.ZipPath) })

	del := jsonReq(http.MethodDelete, "/api/bundle/"+res.Filename, "")
	if rec := serve(t, s, del); rec.Code != http.StatusOK {
		t.Fatalf("delete by filename status %d: %s", rec.Code, rec.Body.String())
	}
	s.mu.RLock()
	left := len(s.bundles)
	s.mu.RUnlock()
	if left != 0 {
		t.Errorf("%d stale entries left in the bundle map after delete", left)
	}
	dl := httptest.NewRequest(http.MethodGet, "/api/bundle/"+res.BundleID+"/download", nil)
	dl.Host = "127.0.0.1:7788"
	if rec := serve(t, s, dl); rec.Code != http.StatusNotFound {
		t.Errorf("the id still resolves after the file was deleted: status %d", rec.Code)
	}
}

// TestEmptyForTargetMapsTo400 — M4 surfaced through the API. Every component
// happens to be available for both targets on this machine, so the engine test
// drives the condition with a synthetic manifest and this pins the mapping:
// an empty-for-target selection is the operator's mistake (400), not a crash.
func TestEmptyForTargetMapsTo400(t *testing.T) {
	err := errors.New("selection contains nothing for target windows: none of oms-cli has a binary for it on this machine")
	if !isSelectionError(err) {
		t.Error("an empty-for-target selection must be reported as a 400, not a 500")
	}
	if isSelectionError(errors.New("no env plan for component \"x\" — add it to envPlan")) {
		t.Error("a missing env plan is a server-side gap (500), not the operator's fault")
	}
	for _, msg := range []string{
		"unknown component \"nope\"", "empty selection: pick at least one component",
		"unknown target \"beos\"", "windows bundle: \"a:b\" contains \":\", which is illegal on NTFS",
	} {
		if !isSelectionError(errors.New(msg)) {
			t.Errorf("%q should map to 400", msg)
		}
	}
}

// TestUnconfiguredComponentIsHonestInTheAPI — M6 seen from the board.
func TestUnconfiguredComponentIsHonestInTheAPI(t *testing.T) {
	s := New(testRepoRoot(t))
	r := httptest.NewRequest(http.MethodGet, "/api/manifest", nil)
	r.Host = "127.0.0.1:7788"
	rec := serve(t, s, r)
	body, _ := io.ReadAll(rec.Body)
	var view ManifestView
	if err := json.Unmarshal(body, &view); err != nil {
		t.Fatal(err)
	}
	for _, c := range view.Components {
		if c.AuthMode == engine.AuthUnconfigured {
			av := c.Availability["mac-arm64"]
			if av.OK {
				t.Errorf("%s has no credential plan but is offered as available", c.ID)
			}
			if len(av.Warnings) == 0 {
				t.Errorf("%s is unconfigured with no warning explaining why", c.ID)
			}
		}
	}
}
