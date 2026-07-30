package mcpsrv

import (
	"crypto/subtle"
	"encoding/json"
	"io"
	"mime"
	"net"
	"net/http"
	"strings"
	"time"
)

// httpBodyLimit caps a single JSON-RPC request body (4 MiB).
const httpBodyLimit = 4 << 20

// The HTTP transport is the one surface a WEB PAGE can reach.
//
// Binding to loopback is not a mitigation against a browser: every page a JIVO
// machine visits can POST to http://127.0.0.1:7706/mcp, and a `Content-Type:
// text/plain` POST is a CORS *simple* request, so it is sent with no preflight
// at all. The page cannot read the response cross-origin — but it does not need
// to in order to drive production HANA blind, and DNS rebinding (an attacker
// name that resolves to 127.0.0.1, so the browser considers the response
// same-origin) makes the answers readable too.
//
// So the transport enforces three browser-shaped checks before any JSON is
// parsed, exactly as the MCP specification requires of a locally-bound HTTP
// server, plus an optional shared secret:
//
//	Origin       must be absent (a non-browser client) or explicitly allowed
//	Host         must be loopback or explicitly allowed  (anti DNS-rebinding)
//	Content-Type must be application/json                (kills the simple-request
//	                                                      path: application/json
//	                                                      forces a preflight, and
//	                                                      no CORS response header
//	                                                      is ever emitted, so the
//	                                                      preflight fails)
//	Authorization: Bearer <AuthToken>, when AuthToken is set
//
// None of this is a substitute for the dedicated SELECT-only HANA user; it is
// the difference between "a visited web page can query the books" and "it
// cannot".

// defaultAllowedHostNames are the host names a loopback-bound server answers to
// when AllowedHosts is empty. A rebinding attack arrives with the ATTACKER's
// name in Host, which is what this list excludes.
var defaultAllowedHostNames = map[string]bool{
	"localhost": true,
	// An HTTP/1.0 request with no Host header at all. net/http already rejects an
	// HTTP/1.1 request without one, and no browser speaks 1.0, so this cannot be
	// the rebinding path.
	"": true,
}

// checkHTTPRequest applies the browser-shaped checks. It returns ("", 0) when
// the request may proceed, or a reason and the HTTP status to answer with.
func (s *Server) checkHTTPRequest(r *http.Request) (string, int) {
	// Origin: a browser always sends it on a cross-origin request. A CLI, the
	// JIVO gateway and an MCP client never do.
	if origin := r.Header.Get("Origin"); origin != "" && !s.originAllowed(origin) {
		return "forbidden: Origin " + origin + " is not allowed. This endpoint talks to JIVO's production HANA database and " +
			"validates Origin as the MCP spec requires of a locally-bound server, because loopback binding does not stop a web page. " +
			"Pass --allow-origin to permit a specific origin.", http.StatusForbidden
	}

	// Host: the anti-DNS-rebinding check. The browser sends the name it resolved,
	// so an attacker name that resolves to 127.0.0.1 is visible right here.
	if !s.hostAllowed(r.Host) {
		return "forbidden: Host " + r.Host + " is not allowed. Reach this endpoint by its loopback address " +
				"(127.0.0.1 or localhost) or pass --allow-host; a request arriving under some other name is what a DNS-rebinding attack looks like.",
			http.StatusForbidden
	}

	// Content-Type: application/json is NOT a CORS simple request, so a browser
	// must preflight it — and this server answers no preflight.
	if !jsonContentType(r.Header.Get("Content-Type")) {
		return "unsupported media type: POST a JSON-RPC message with Content-Type: application/json " +
				"(text/plain and form encodings are refused because they are CORS simple requests a web page can send with no preflight)",
			http.StatusUnsupportedMediaType
	}

	if s.AuthToken != "" && !bearerMatches(r.Header.Get("Authorization"), s.AuthToken) {
		return "unauthorized: this endpoint requires Authorization: Bearer <token>", http.StatusUnauthorized
	}
	return "", 0
}

// originAllowed reports whether an Origin header value is permitted. The
// default is DENY: a request carrying an Origin is a browser request, and no
// browser has business driving production HANA.
func (s *Server) originAllowed(origin string) bool {
	for _, a := range s.AllowedOrigins {
		if a == "*" || strings.EqualFold(strings.TrimSpace(a), origin) {
			return true
		}
	}
	return false
}

// hostAllowed reports whether the Host header names this server legitimately.
func (s *Server) hostAllowed(host string) bool {
	for _, a := range s.AllowedHosts {
		if a == "*" || strings.EqualFold(strings.TrimSpace(a), host) {
			return true
		}
	}
	name := host
	if h, _, err := net.SplitHostPort(host); err == nil {
		name = h
	}
	name = strings.Trim(name, "[]")
	if defaultAllowedHostNames[strings.ToLower(name)] {
		return true
	}
	if ip := net.ParseIP(name); ip != nil {
		return ip.IsLoopback()
	}
	return false
}

// jsonContentType reports whether ct is application/json (parameters allowed).
func jsonContentType(ct string) bool {
	if ct == "" {
		return false
	}
	mt, _, err := mime.ParseMediaType(ct)
	if err != nil {
		return false
	}
	mt = strings.ToLower(mt)
	return mt == "application/json" || strings.HasSuffix(mt, "+json")
}

// bearerMatches compares an Authorization header against the shared secret in
// constant time.
func bearerMatches(header, token string) bool {
	const prefix = "bearer "
	if len(header) <= len(prefix) || !strings.EqualFold(header[:len(prefix)], prefix) {
		return false
	}
	got := strings.TrimSpace(header[len(prefix):])
	return subtle.ConstantTimeCompare([]byte(got), []byte(token)) == 1
}

// HTTPHandler serves the MCP "streamable HTTP" transport, fully stateless:
// exactly one JSON-RPC message (or one batch) per POST, exactly one JSON
// response (or 202 for a notification). There are no sessions (Mcp-Session-Id is
// ignored and never emitted) and no server-initiated streams, so the GET/SSE arm
// is a 405, as the spec permits. Everything below the transport — the tools, the
// guard, the READ ONLY transaction — is shared with the stdio path.
func (s *Server) HTTPHandler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// The method check is first because it reveals nothing and reads nothing;
		// everything that follows can reach production HANA.
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", http.MethodPost)
			http.Error(w, "method not allowed: this MCP endpoint is stateless (POST one JSON-RPC message; no SSE stream, no sessions)", http.StatusMethodNotAllowed)
			return
		}
		if reason, status := s.checkHTTPRequest(r); status != 0 {
			http.Error(w, reason, status)
			return
		}

		body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, httpBodyLimit))
		if err != nil {
			httpError(w, http.StatusBadRequest, -32700, "parse error: "+err.Error())
			return
		}

		// r.Context() and not context.Background(): a client that disconnects, or
		// a gateway that times out, must be able to cancel the production query it
		// started. It used to be Background, so nothing upstream could stop a call
		// once it had been queued.
		resp, err := s.handleMessage(r.Context(), body)
		if err != nil {
			httpError(w, http.StatusBadRequest, -32700, "parse error: "+err.Error())
			return
		}
		if resp == nil { // notification (or an all-notification batch): nothing to say
			w.WriteHeader(http.StatusAccepted)
			return
		}

		b, err := json.Marshal(resp)
		if err != nil {
			httpError(w, http.StatusInternalServerError, -32603, "marshal error: "+err.Error())
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write(b)
	})
}

// httpError writes a JSON-RPC error object (id null) with the given HTTP status.
func httpError(w http.ResponseWriter, status, code int, msg string) {
	resp := mcpResponse{
		JSONRPC: "2.0",
		ID:      json.RawMessage("null"),
		Error:   &mcpRPCError{Code: code, Message: msg},
	}
	b, err := json.Marshal(resp)
	if err != nil {
		http.Error(w, msg, status)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	w.Write(b)
}

// ServeHTTP blocks serving the MCP endpoint at /mcp on addr.
func (s *Server) ServeHTTP(addr string) error {
	mux := http.NewServeMux()
	mux.Handle("/mcp", s.HTTPHandler())
	srv := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
	}
	s.logf("hana-sql: MCP server listening on http://%s/mcp", addr)
	if s.AuthToken == "" {
		s.logf("hana-sql: no --auth-token set; access control is Origin/Host/Content-Type validation only")
	}
	return srv.ListenAndServe()
}
