// Package httpapi serves the bundle builder: a small JSON API plus the
// frontend in distribution/web/. It binds to 127.0.0.1 by default — that is not
// an auth layer, it just keeps a credential-generating service off the LAN.
package httpapi

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"mime"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"jivodist/internal/engine"
	"jivodist/internal/manifest"
)

// DefaultAddr is the loopback address the server binds unless told otherwise.
const DefaultAddr = "127.0.0.1:7788"

// Server holds the repo it builds from. One build runs at a time: this is a
// one-operator tool, and concurrent builds would race on distribution/dist.
type Server struct {
	RepoRoot string
	HomeDir  string
	// Addr is the address the server is bound to. It defines the Host header
	// allowlist, so it must match what main actually listens on.
	Addr string

	buildMu sync.Mutex

	mu      sync.RWMutex
	bundles map[string]string // bundle id -> absolute zip path
}

// New returns a Server rooted at a jivo-cli checkout, bound to DefaultAddr.
func New(repoRoot string) *Server {
	home, _ := os.UserHomeDir()
	return &Server{RepoRoot: repoRoot, HomeDir: home, Addr: DefaultAddr, bundles: map[string]string{}}
}

// Routes wires the API and the static frontend, behind the browser hardening.
func (s *Server) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/manifest", s.handleManifest)
	mux.HandleFunc("POST /api/bundle", s.handleBuild)
	mux.HandleFunc("GET /api/bundles", s.handleList)
	mux.HandleFunc("GET /api/bundle/{id}/download", s.handleDownload)
	mux.HandleFunc("DELETE /api/bundle/{id}", s.handleDelete)
	mux.Handle("/", s.staticHandler())
	return logging(s.hardening(mux))
}

// ------------------------------------------------------- browser hardening
//
// This is NOT an authentication layer, and it adds no friction for the
// operator. It exists because a service on 127.0.0.1 is reachable by any web
// page the operator happens to have open: without these checks a hostile site
// could POST /api/bundle as a CORS "simple request" and have this machine build
// a zip full of production credentials, and DNS rebinding would let it read the
// responses. Three cheap checks close that off:
//
//  1. Host allowlist — a rebound DNS name arrives with the attacker's Host.
//  2. application/json required on state-changing methods — that makes the
//     request non-simple, so the browser must preflight, and the preflight
//     fails because (3) we never send a single CORS header.
//  3. Sec-Fetch-Site, where the browser sends it, must say the request came
//     from this origin.

func (s *Server) allowedHosts() map[string]bool {
	addr := s.Addr
	if addr == "" {
		addr = DefaultAddr
	}
	host, port, err := net.SplitHostPort(addr)
	if err != nil {
		host, port = "127.0.0.1", "7788"
	}
	allowed := map[string]bool{
		"127.0.0.1:" + port: true,
		"localhost:" + port: true,
		"[::1]:" + port:     true,
	}
	// Bound somewhere other than loopback (a VPS, later): accept that exact
	// host:port too, and nothing else.
	switch host {
	case "", "127.0.0.1", "localhost", "::1", "0.0.0.0", "::":
	default:
		allowed[net.JoinHostPort(host, port)] = true
	}
	return allowed
}

func (s *Server) hardening(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Computed per request (four map inserts) so Addr can be set after the
		// routes are wired — which is what main does once it knows its port.
		if !s.allowedHosts()[r.Host] {
			writeError(w, http.StatusForbidden,
				"refused: unexpected Host header. This server answers only on its own loopback address.")
			return
		}
		// Absent means a non-browser client (curl, the CLI); "none" means the
		// user typed the URL; "same-origin" is our own page.
		switch r.Header.Get("Sec-Fetch-Site") {
		case "", "none", "same-origin":
		default:
			writeError(w, http.StatusForbidden,
				"refused: this request came from another site. The bundle builder is only usable from its own page.")
			return
		}
		if r.Method == http.MethodPost || r.Method == http.MethodDelete {
			mt, _, err := mime.ParseMediaType(r.Header.Get("Content-Type"))
			if err != nil || mt != "application/json" {
				writeError(w, http.StatusUnsupportedMediaType,
					"refused: send Content-Type: application/json on POST and DELETE.")
				return
			}
		}
		next.ServeHTTP(w, r)
	})
}

// noStore keeps bundle metadata and the credential zips themselves out of every
// cache between here and the operator's browser.
func noStore(w http.ResponseWriter) {
	w.Header().Set("Cache-Control", "no-store")
}

// ---------------------------------------------------------------- /api/manifest

// ComponentView is what the UI renders. The UI renders ONLY from this — it
// holds no hardcoded tool list, so adding a CLI to manifest.json is enough to
// make it selectable.
type ComponentView struct {
	ID            string                  `json:"id"`
	UIName        string                  `json:"ui_name"`
	UIDescription string                  `json:"ui_description"`
	AuthMode      string                  `json:"auth_mode"`
	AuthNote      string                  `json:"auth_note"`
	Sensitive     bool                    `json:"sensitive"`
	Availability  map[string]Availability `json:"availability"`
	EstSizeBytes  map[string]int64        `json:"est_size_bytes"`
}

// Availability is disk truth for one component on one target, computed live by
// os.Stat — never from the manifest's `exists` flags, which were recorded on
// whichever machine wrote the manifest.
type Availability struct {
	OK            bool     `json:"ok"`
	ToolsIncluded int      `json:"tools_included"`
	ToolsSkipped  int      `json:"tools_skipped"`
	Warnings      []string `json:"warnings"`
}

// ManifestView is the GET /api/manifest body.
type ManifestView struct {
	GeneratedAt string          `json:"generated_at"`
	Targets     []string        `json:"targets"`
	Components  []ComponentView `json:"components"`
	// Warnings apply to every bundle regardless of selection (overrides.json
	// `global`), so the UI shows them once rather than on each component.
	Warnings []string `json:"warnings"`
}

// BuildManifestView assembles the UI payload for a repo.
func BuildManifestView(repoRoot, homeDir string, now time.Time) (*ManifestView, error) {
	m, err := manifest.Load(repoRoot)
	if err != nil {
		return nil, err
	}
	overrides, err := manifest.LoadOverrides(repoRoot)
	if err != nil {
		return nil, err
	}

	view := &ManifestView{
		GeneratedAt: now.Format(time.RFC3339),
		Targets:     manifest.Targets,
		Components:  []ComponentView{},
		Warnings:    append([]string{}, overrides.Global...),
	}
	// Global warnings belong to the bundle, not to any one component.
	componentOverrides := &manifest.Overrides{Components: overrides.Components, Binaries: overrides.Binaries}
	for _, c := range m.Distributable() {
		cv := ComponentView{
			ID:            c.ID,
			UIName:        c.UIName,
			UIDescription: c.UIDescription,
			AuthMode:      engine.AuthMode(c.ID),
			AuthNote:      engine.AuthNote(c.ID),
			Sensitive:     engine.Sensitive(c.ID),
			Availability:  map[string]Availability{},
			EstSizeBytes:  map[string]int64{},
		}
		for _, target := range manifest.Targets {
			res := engine.ResolveComponent(repoRoot, homeDir, c, target, true)
			warnings := append([]string{}, res.Warnings...)
			if !engine.HasEnvPlan(c.ID) {
				// Show the gap instead of a false promise: the board must not
				// offer a component whose credential story nobody has written.
				warnings = append(warnings, fmt.Sprintf(
					"%s has no credential plan yet, so it cannot be bundled — add a row to envPlan in "+
						"internal/engine/envbake.go (PLAN.md §5).", c.ID))
			}
			warnings = append(warnings, engine.CollectWarnings(componentOverrides, includedIDs(res, c.ID), res.Files, target, nil)...)
			for _, sk := range res.Skipped {
				warnings = append(warnings, fmt.Sprintf("%s: %s", sk.Tool, sk.Reason))
			}
			cv.Availability[target] = Availability{
				OK:            res.ToolsIncluded > 0 && engine.HasEnvPlan(c.ID),
				ToolsIncluded: res.ToolsIncluded,
				ToolsSkipped:  res.ToolsSkipped,
				Warnings:      warnings,
			}
			cv.EstSizeBytes[target] = engine.EstimatedSize(repoRoot, res.Files)
		}
		view.Components = append(view.Components, cv)
	}
	return view, nil
}

func includedIDs(res engine.Resolution, id string) []string {
	if res.ToolsIncluded > 0 {
		return []string{id}
	}
	return nil
}

func (s *Server) handleManifest(w http.ResponseWriter, r *http.Request) {
	view, err := BuildManifestView(s.RepoRoot, s.HomeDir, time.Now())
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	noStore(w)
	writeJSON(w, http.StatusOK, view)
}

// ------------------------------------------------------------------ /api/bundle

func (s *Server) handleBuild(w http.ResponseWriter, r *http.Request) {
	var sel engine.Selection
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20)).Decode(&sel); err != nil {
		writeError(w, http.StatusBadRequest, "could not read the request: "+err.Error())
		return
	}

	res, err := s.build(sel)
	if err != nil {
		switch {
		case errors.Is(err, engine.ErrNotIgnored):
			writeError(w, http.StatusConflict, err.Error())
		case isSelectionError(err):
			writeError(w, http.StatusBadRequest, err.Error())
		default:
			writeError(w, http.StatusInternalServerError, err.Error())
		}
		return
	}

	s.mu.Lock()
	s.bundles[res.BundleID] = res.ZipPath
	s.mu.Unlock()

	// JSON first, download second: the warnings are meant to be read before the
	// zip is sent to anybody.
	writeJSON(w, http.StatusOK, res)
}

// build serialises bundle creation. The unlock is deferred so a panic inside
// the engine cannot wedge the server for every later request.
func (s *Server) build(sel engine.Selection) (*engine.Result, error) {
	s.buildMu.Lock()
	defer s.buildMu.Unlock()
	return engine.Build(s.RepoRoot, sel, engine.Options{HomeDir: s.HomeDir})
}

func isSelectionError(err error) bool {
	msg := err.Error()
	for _, s := range []string{
		"unknown component", "empty selection", "unknown target",
		"not distributable", "illegal on NTFS", "selection contains nothing for target",
	} {
		if strings.Contains(msg, s) {
			return true
		}
	}
	return false
}

// BundleInfo is one zip sitting in distribution/dist.
type BundleInfo struct {
	ID        string `json:"id"`
	Filename  string `json:"filename"`
	SizeBytes int64  `json:"size_bytes"`
	AgeSecs   int64  `json:"age_seconds"`
	Modified  string `json:"modified"`
}

func (s *Server) handleList(w http.ResponseWriter, r *http.Request) {
	dir := filepath.Join(s.RepoRoot, engine.DistDir)
	entries, err := os.ReadDir(dir)
	if err != nil && !os.IsNotExist(err) {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	out := []BundleInfo{}
	now := time.Now()
	for _, e := range entries {
		// *.zip.tmp is a bundle still being written — never list a half-written
		// credential zip as if it were ready to send.
		if e.IsDir() || engine.IsPartial(e.Name()) || !strings.HasSuffix(e.Name(), ".zip") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		// The id is embedded in the filename, so it is recovered the same way
		// whether or not this server built the file.
		id := engine.BundleIDFromFilename(e.Name())
		if id == "" {
			id = e.Name()
		}
		out = append(out, BundleInfo{
			ID:        id,
			Filename:  e.Name(),
			SizeBytes: info.Size(),
			AgeSecs:   int64(now.Sub(info.ModTime()).Seconds()),
			Modified:  info.ModTime().Format(time.RFC3339),
		})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].AgeSecs < out[j].AgeSecs })
	noStore(w)
	writeJSON(w, http.StatusOK, out)
}

// resolveBundle maps an id (or a bare filename) to a finished zip inside
// dist/. It refuses anything that escapes that directory and anything still
// being written.
func (s *Server) resolveBundle(id string) (string, error) {
	s.mu.RLock()
	p, ok := s.bundles[id]
	s.mu.RUnlock()
	if ok {
		return p, nil
	}
	if id == "" || strings.ContainsAny(id, `/\`) || strings.Contains(id, "..") || engine.IsPartial(id) {
		return "", fmt.Errorf("no such bundle")
	}
	dir := filepath.Join(s.RepoRoot, engine.DistDir)

	// A build id: the filename carries it, so a zip built before this server
	// started is still reachable by its id.
	if engine.BundleIDFromFilename(id) == id {
		entries, err := os.ReadDir(dir)
		if err != nil {
			return "", fmt.Errorf("no such bundle")
		}
		for _, e := range entries {
			name := e.Name()
			if e.IsDir() || engine.IsPartial(name) || !strings.HasSuffix(name, ".zip") {
				continue
			}
			if engine.BundleIDFromFilename(name) == id {
				return filepath.Join(dir, name), nil
			}
		}
		return "", fmt.Errorf("no such bundle")
	}

	if !strings.HasSuffix(id, ".zip") {
		return "", fmt.Errorf("no such bundle")
	}
	abs := filepath.Join(dir, id)
	if st, err := os.Stat(abs); err != nil || st.IsDir() {
		return "", fmt.Errorf("no such bundle")
	}
	return abs, nil
}

func (s *Server) handleDownload(w http.ResponseWriter, r *http.Request) {
	path, err := s.resolveBundle(r.PathValue("id"))
	if err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}
	f, err := os.Open(path)
	if err != nil {
		writeError(w, http.StatusNotFound, "bundle file is gone")
		return
	}
	defer f.Close()
	st, err := f.Stat()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	noStore(w)
	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%q", filepath.Base(path)))
	http.ServeContent(w, r, filepath.Base(path), st.ModTime(), f)
}

func (s *Server) handleDelete(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	path, err := s.resolveBundle(id)
	if err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}
	if err := os.Remove(path); err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	// Purge by path, not just by the key that was asked for: the same zip can be
	// addressed by its build id or its filename, and a stale entry would keep
	// serving 200s for a file that is gone.
	s.mu.Lock()
	delete(s.bundles, id)
	for k, v := range s.bundles {
		if v == path {
			delete(s.bundles, k)
		}
	}
	s.mu.Unlock()
	writeJSON(w, http.StatusOK, map[string]string{"deleted": filepath.Base(path)})
}

// ---------------------------------------------------------------------- static

// staticHandler serves distribution/web/. The directory is built in a separate
// session; if it is not there yet, say so plainly instead of 404ing blankly.
func (s *Server) staticHandler() http.Handler {
	dir := filepath.Join(s.RepoRoot, "distribution", "web")
	fs := http.FileServer(http.Dir(dir))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// no-store on the frontend too: a stale cached board.js after a server
		// upgrade runs old logic against a new API (observed live: cached
		// deletes 415ing after the hardening landed).
		w.Header().Set("Cache-Control", "no-store")
		if st, err := os.Stat(dir); err != nil || !st.IsDir() {
			w.Header().Set("Content-Type", "text/plain; charset=utf-8")
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintf(w, "The frontend is not installed: %s does not exist.\n"+
				"The API is up — try GET /api/manifest.\n", dir)
			return
		}
		fs.ServeHTTP(w, r)
	})
}

// ---------------------------------------------------------------------- helpers

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	if err := enc.Encode(v); err != nil {
		log.Printf("write json: %v", err)
	}
}

// APIError is the body of every non-2xx response.
type APIError struct {
	Error string `json:"error"`
}

func writeError(w http.ResponseWriter, code int, msg string) {
	writeJSON(w, code, APIError{Error: msg})
}

func logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.URL.Path, time.Since(start).Round(time.Millisecond))
	})
}
