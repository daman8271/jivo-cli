package httpapi

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"jivodist/internal/engine"
	"jivodist/internal/manifest"
)

func testRepoRoot(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	root, err := manifest.FindRepoRoot(wd)
	if err != nil {
		t.Fatal(err)
	}
	return root
}

func newTestServer(t *testing.T) (*httptest.Server, *Server) {
	t.Helper()
	s := New(testRepoRoot(t))
	ts := httptest.NewServer(s.Routes())
	// The browser hardening allows only the address we are actually bound to,
	// so the test server's ephemeral port has to be what the allowlist is
	// built from.
	s.Addr = ts.Listener.Addr().String()
	t.Cleanup(ts.Close)
	return ts, s
}

// deleteJSON issues a DELETE the way the UI must: state-changing methods carry
// Content-Type: application/json so the browser is forced to preflight.
func deleteJSON(t *testing.T, url string) *http.Response {
	t.Helper()
	req, err := http.NewRequest(http.MethodDelete, url, nil)
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	return resp
}

func get(t *testing.T, ts *httptest.Server, path string, into any) *http.Response {
	t.Helper()
	resp, err := http.Get(ts.URL + path)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if into != nil {
		if err := json.Unmarshal(body, into); err != nil {
			t.Fatalf("GET %s: %v\n%s", path, err, body)
		}
	}
	return resp
}

// TestManifestEndpointIsTheOnlySourceTheUINeeds: everything the frontend
// renders — names, descriptions, auth mode, availability, size — comes from
// here, so the UI never hardcodes a tool list.
func TestManifestEndpointIsTheOnlySourceTheUINeeds(t *testing.T) {
	ts, _ := newTestServer(t)
	var view ManifestView
	resp := get(t, ts, "/api/manifest", &view)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status %d", resp.StatusCode)
	}
	if len(view.Targets) == 0 {
		t.Error("no targets")
	}
	if len(view.Components) != 12 {
		t.Errorf("got %d components, want 12", len(view.Components))
	}
	validModes := map[string]bool{
		engine.AuthBakedEnv: true, engine.AuthLogin: true,
		engine.AuthHomeConfig: true, engine.AuthExternalToken: true,
	}
	for _, c := range view.Components {
		if c.ID == "" || c.UIName == "" || c.UIDescription == "" {
			t.Errorf("component %+v is missing UI fields", c.ID)
		}
		if !validModes[c.AuthMode] {
			t.Errorf("%s: auth_mode %q is not one of the four in the contract", c.ID, c.AuthMode)
		}
		for _, target := range view.Targets {
			av, ok := c.Availability[target]
			if !ok {
				t.Errorf("%s: no availability for %s", c.ID, target)
				continue
			}
			if av.OK && av.ToolsIncluded == 0 {
				t.Errorf("%s/%s: ok with zero tools", c.ID, target)
			}
			if av.Warnings == nil {
				t.Errorf("%s/%s: warnings must be a list, not null", c.ID, target)
			}
		}
	}
}

// TestAvailabilityIsDiskTruth: the manifest's `exists` flags are irrelevant —
// availability must come from os.Stat, which is what makes this work on a box
// where portals/tankhapay/ is absent.
func TestAvailabilityIsDiskTruth(t *testing.T) {
	ts, _ := newTestServer(t)
	var view ManifestView
	get(t, ts, "/api/manifest", &view)

	byID := map[string]ComponentView{}
	for _, c := range view.Components {
		byID[c.ID] = c
	}
	// jsap ships as a Python script on both platforms (Windows runs it as
	// `python jsap-cli\jsap-cli`). The manifest used to point Windows at the
	// package directory, which made this false.
	for _, target := range []string{"mac-arm64", "windows"} {
		if !byID["jsap-cli"].Availability[target].OK {
			t.Errorf("jsap-cli should be available on %s", target)
		}
	}
	if !byID["sap-b1"].Availability["windows"].OK || !byID["sap-b1"].Availability["mac-arm64"].OK {
		t.Error("sap-b1 ships on both targets")
	}
	if byID["portals"].Availability["windows"].ToolsSkipped == 0 {
		t.Error("three portal .exe files do not exist; that must show as skipped tools")
	}
	if !byID["portals"].Sensitive {
		t.Error("portals must be flagged sensitive (TankhaPay payroll)")
	}
	if byID["hana-sql"].EstSizeBytes["mac-arm64"] == 0 {
		t.Error("estimated size should be non-zero")
	}
}

// TestBuildDownloadDelete walks the operator's whole workflow.
func TestBuildDownloadDelete(t *testing.T) {
	ts, _ := newTestServer(t)

	body, _ := json.Marshal(engine.Selection{
		Target: "mac-arm64", Components: []string{"hana-sql", "jsap-cli"},
		Recipient: "apitest", IncludeDocs: true,
	})
	resp, err := http.Post(ts.URL+"/api/bundle", "application/json", bytes.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	raw, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("build failed: %d %s", resp.StatusCode, raw)
	}
	var res engine.Result
	if err := json.Unmarshal(raw, &res); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { os.Remove(res.ZipPath) })

	// The sha256 in the response must match the file on disk.
	onDisk, err := engine.SHA256File(res.ZipPath)
	if err != nil {
		t.Fatal(err)
	}
	if onDisk != res.SHA256 {
		t.Errorf("sha256 mismatch: response %s, disk %s", res.SHA256, onDisk)
	}
	if !strings.HasPrefix(res.Filename, "jivo-kit-mac-arm64-") || !strings.HasSuffix(res.Filename, "-apitest.zip") {
		t.Errorf("unexpected filename %s", res.Filename)
	}

	// It is listed.
	var list []BundleInfo
	get(t, ts, "/api/bundles", &list)
	var found bool
	for _, b := range list {
		if b.ID == res.BundleID {
			found = true
			if b.SizeBytes != res.SizeBytes {
				t.Errorf("listed size %d, built %d", b.SizeBytes, res.SizeBytes)
			}
		}
	}
	if !found {
		t.Errorf("bundle %s not in /api/bundles", res.BundleID)
	}

	// It downloads, with the right headers and the right bytes.
	dl, err := http.Get(ts.URL + res.DownloadURL)
	if err != nil {
		t.Fatal(err)
	}
	got, _ := io.ReadAll(dl.Body)
	dl.Body.Close()
	if dl.StatusCode != http.StatusOK {
		t.Fatalf("download status %d", dl.StatusCode)
	}
	if ct := dl.Header.Get("Content-Type"); ct != "application/zip" {
		t.Errorf("content-type %q", ct)
	}
	if cd := dl.Header.Get("Content-Disposition"); !strings.Contains(cd, "attachment") {
		t.Errorf("content-disposition %q", cd)
	}
	if int64(len(got)) != res.SizeBytes {
		t.Errorf("downloaded %d bytes, expected %d", len(got), res.SizeBytes)
	}

	// And it deletes — the zips hold live credentials, so removing them after
	// sending is part of the job.
	del := deleteJSON(t, ts.URL+"/api/bundle/"+res.BundleID)
	del.Body.Close()
	if del.StatusCode != http.StatusOK {
		t.Fatalf("delete status %d", del.StatusCode)
	}
	if _, err := os.Stat(res.ZipPath); !os.IsNotExist(err) {
		t.Error("zip still on disk after DELETE")
	}
}

// TestBadRequestsAre400 pins the error contract.
func TestBadRequestsAre400(t *testing.T) {
	ts, _ := newTestServer(t)
	cases := []struct {
		name string
		body string
		want int
	}{
		{"unknown component", `{"target":"mac-arm64","components":["nope"]}`, http.StatusBadRequest},
		{"empty selection", `{"target":"mac-arm64","components":[]}`, http.StatusBadRequest},
		{"bad target", `{"target":"beos","components":["hana-sql"]}`, http.StatusBadRequest},
		{"malformed json", `{`, http.StatusBadRequest},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			resp, err := http.Post(ts.URL+"/api/bundle", "application/json", strings.NewReader(tc.body))
			if err != nil {
				t.Fatal(err)
			}
			raw, _ := io.ReadAll(resp.Body)
			resp.Body.Close()
			if resp.StatusCode != tc.want {
				t.Errorf("status %d, want %d (%s)", resp.StatusCode, tc.want, raw)
			}
			var e APIError
			if err := json.Unmarshal(raw, &e); err != nil || e.Error == "" {
				t.Errorf("error body should explain what to fix, got %s", raw)
			}
		})
	}
}

// TestDownloadRejectsPathTraversal — the download handler resolves ids, and an
// id is attacker-controlled text.
func TestDownloadRejectsPathTraversal(t *testing.T) {
	ts, _ := newTestServer(t)
	for _, id := range []string{
		"..%2f..%2f.env",
		"nope",
		"..",
		"not-a-zip",
	} {
		resp, err := http.Get(ts.URL + "/api/bundle/" + id + "/download")
		if err != nil {
			t.Fatal(err)
		}
		resp.Body.Close()
		if resp.StatusCode != http.StatusNotFound {
			t.Errorf("%s: status %d, want 404", id, resp.StatusCode)
		}
	}
}

func TestResolveBundleRefusesEscapes(t *testing.T) {
	s := New(testRepoRoot(t))
	for _, id := range []string{"../.env", "a/b.zip", `a\b.zip`, "..%2fx.zip", "", "plain"} {
		if _, err := s.resolveBundle(id); err == nil {
			t.Errorf("resolveBundle(%q) should have failed", id)
		}
	}
}

// TestStaticHandlerSaysWhatIsMissing — the frontend is built separately, so an
// absent web/ directory must produce an explanation, not a blank 404.
func TestStaticHandlerSaysWhatIsMissing(t *testing.T) {
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, "distribution"), 0o755); err != nil {
		t.Fatal(err)
	}
	s := New(root)
	rec := httptest.NewRecorder()
	s.staticHandler().ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))
	if rec.Code != http.StatusNotFound {
		t.Errorf("status %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), "/api/manifest") {
		t.Errorf("the message should point at the working API, got %q", rec.Body.String())
	}
}

func TestBuildManifestViewIsDeterministic(t *testing.T) {
	root := testRepoRoot(t)
	home, _ := os.UserHomeDir()
	now := time.Date(2026, 8, 10, 14, 30, 0, 0, time.UTC)
	a, err := BuildManifestView(root, home, now)
	if err != nil {
		t.Fatal(err)
	}
	b, err := BuildManifestView(root, home, now)
	if err != nil {
		t.Fatal(err)
	}
	ja, _ := json.Marshal(a)
	jb, _ := json.Marshal(b)
	if string(ja) != string(jb) {
		t.Error("two identical calls produced different payloads")
	}
}
