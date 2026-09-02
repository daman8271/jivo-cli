package main

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

// fakePortal stands in for gst.gov.in in every test. It is deliberately strict:
// it records every request it receives (so a test can assert that NOTHING was
// sent), and it refuses any method other than GET/POST loudly.
type fakePortal struct {
	srv *httptest.Server

	mu   sync.Mutex
	Hits []recordedRequest

	// routes maps "HOST PATH" to a handler. Missing route = 404 + a loud body.
	routes map[string]http.HandlerFunc
}

type recordedRequest struct {
	Method  string
	Host    string
	Path    string
	Query   url.Values
	Headers http.Header
	Body    string
	Cookies []*http.Cookie
}

func newFakePortal(t *testing.T) *fakePortal {
	t.Helper()
	fp := &fakePortal{routes: map[string]http.HandlerFunc{}}
	fp.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body := ""
		if r.Body != nil {
			b := make([]byte, 1<<16)
			n, _ := r.Body.Read(b)
			body = string(b[:n])
		}
		fp.mu.Lock()
		fp.Hits = append(fp.Hits, recordedRequest{
			Method: r.Method, Host: r.Host, Path: r.URL.Path,
			Query: r.URL.Query(), Headers: r.Header.Clone(), Body: body, Cookies: r.Cookies(),
		})
		h := fp.routes[r.Host+" "+r.URL.Path]
		fp.mu.Unlock()
		if h == nil {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte(`{"fake-portal":"no route for ` + r.Host + " " + r.URL.Path + `"}`))
			return
		}
		h(w, r)
	}))
	t.Cleanup(fp.srv.Close)

	// tests must not pay the politeness delay
	old := clientMinGap
	clientMinGap = 0
	t.Cleanup(func() { clientMinGap = old })

	// route every gst.gov.in host at the fake server
	oldT := clientTransport
	clientTransport = &rewriteTransport{base: fp.srv.Listener.Addr().String()}
	t.Cleanup(func() { clientTransport = oldT })
	return fp
}

// json routes a path to a testdata file.
func (fp *fakePortal) json(host, path, testdataFile string) *fakePortal {
	b, err := os.ReadFile(filepath.Join("testdata", testdataFile))
	if err != nil {
		panic(err)
	}
	return fp.handle(host, path, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write(b)
	})
}

func (fp *fakePortal) handle(host, path string, h http.HandlerFunc) *fakePortal {
	fp.mu.Lock()
	defer fp.mu.Unlock()
	fp.routes[host+" "+path] = h
	return fp
}

// redirectTo makes a path 302 somewhere — how the WAF says "no".
func (fp *fakePortal) redirectTo(host, path, location string) *fakePortal {
	return fp.handle(host, path, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Location", location)
		w.WriteHeader(http.StatusFound)
	})
}

func (fp *fakePortal) hitCount() int {
	fp.mu.Lock()
	defer fp.mu.Unlock()
	return len(fp.Hits)
}

func (fp *fakePortal) lastHit(t *testing.T) recordedRequest {
	t.Helper()
	fp.mu.Lock()
	defer fp.mu.Unlock()
	if len(fp.Hits) == 0 {
		t.Fatal("the portal was never called")
	}
	return fp.Hits[len(fp.Hits)-1]
}

// rewriteTransport sends every https://<gst host>/… request to the test server
// while keeping the original Host header, so the client's per-host logic
// (Referer, cookie scoping) is exercised for real.
type rewriteTransport struct{ base string }

func (rt *rewriteTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	clone := r.Clone(r.Context())
	clone.URL.Scheme = "http"
	clone.URL.Host = rt.base
	return http.DefaultTransport.RoundTrip(clone)
}

// testRegistration is the Haryana-shaped registration every client test uses.
func testRegistration() Registration {
	return Registration{Idx: "01", State: "Haryana", GSTIN: "06AAAAA0000A1Z0", User: "jivotest729", Pass: testPass}
}

// seedSession writes an authenticated jar so client tests do not need a login.
func seedSession(t *testing.T, gstin string) {
	t.Helper()
	s := &session{
		GSTIN: gstin, Username: "jivotest729", Stage: stageAuthenticated,
		Cookies: []sessionCookie{
			{Name: "AuthToken", Value: "test-token", Domain: ".gst.gov.in", Path: "/"},
			{Name: "TS0134d082", Value: "waf-a", Domain: ".gst.gov.in", Path: "/"},
			{Name: "TS01255980", Value: "waf-b", Domain: ".gst.gov.in", Path: "/"},
		},
	}
	if err := s.save(); err != nil {
		t.Fatal(err)
	}
}

// runCLI drives the real cobra tree end to end and returns stdout.
func runCLI(t *testing.T, args ...string) (string, error) {
	t.Helper()
	var out, errb strings.Builder
	app := &App{out: &out, errw: &errb}
	root := newRootCmdWithApp(app)
	root.SetOut(&out)
	root.SetErr(&errb)
	root.SetArgs(args)
	err := root.Execute()
	return out.String(), err
}
