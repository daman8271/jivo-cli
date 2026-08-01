package gateway

import (
	"encoding/json"
	"io"
	"mime"
	"net"
	"net/http"
	"strings"
	"time"
)

// httpBodyLimit caps a single JSON-RPC request body (4 MiB), same as postsql.
const httpBodyLimit = 4 << 20

// The front side is the one surface a WEB PAGE can reach, and this gateway is
// reachable through a public reverse proxy, so it is the surface that matters
// most. hana-sql's transport already enforces these checks and explains the
// reasoning; this one enforced none of them, which meant a POST carrying
// `Origin: http://evil.example` or `Content-Type: text/plain` was answered 200.
//
//	Origin        must be absent (a CLI, an MCP client, the Claude connector —
//	              none of them send one) or explicitly allowed. A browser always
//	              sends it cross-origin, and no browser has business driving
//	              JIVO's production books.
//	Content-Type  must be application/json. text/plain and the form encodings
//	              are CORS *simple* requests, sent with no preflight at all;
//	              application/json forces a preflight, and this server answers
//	              no preflight and emits no CORS header, so the preflight fails.
//	              The MCP streamable-HTTP transport requires this header anyway.
//	Host          checked only when AllowedHosts is configured. Unlike
//	              hana-sql, this gateway is DELIBERATELY reached by a public
//	              name through a proxy, so a loopback-only default would 403 the
//	              real deployment. --allow-host is there for a loopback-bound
//	              gateway that wants the anti-DNS-rebinding check.
//
// None of this is authentication. It is the difference between "a page a JIVO
// machine visits can drive the gateway" and "it cannot".

// checkHTTPRequest applies the browser-shaped checks. It returns ("", 0) when
// the request may proceed, or a reason and the HTTP status to answer with.
func (g *Gateway) checkHTTPRequest(r *http.Request) (string, int) {
	if origin := r.Header.Get("Origin"); origin != "" && !allowedBy(g.cfg.AllowedOrigins, origin) {
		return "forbidden: Origin " + origin + " is not allowed. This endpoint fronts JIVO's production systems and validates Origin, " +
			"because a client that legitimately speaks MCP does not send one at all. Pass --allow-origin to permit a specific origin.", http.StatusForbidden
	}
	if len(g.cfg.AllowedHosts) > 0 && !g.hostAllowed(r.Host) {
		return "forbidden: Host " + r.Host + " is not allowed. Reach this endpoint under one of the names passed to --allow-host; " +
			"a request arriving under some other name is what a DNS-rebinding attack looks like.", http.StatusForbidden
	}
	if !jsonContentType(r.Header.Get("Content-Type")) {
		return "unsupported media type: POST a JSON-RPC message with Content-Type: application/json " +
			"(text/plain and the form encodings are refused because they are CORS simple requests a web page can send with no preflight)", http.StatusUnsupportedMediaType
	}
	return "", 0
}

// allowedBy reports whether value appears in an allowlist ("*" allows all).
func allowedBy(list []string, value string) bool {
	for _, a := range list {
		if a == "*" || strings.EqualFold(strings.TrimSpace(a), value) {
			return true
		}
	}
	return false
}

// hostAllowed reports whether the Host header names this gateway legitimately.
// Only reached when AllowedHosts is non-empty. Loopback is always accepted
// alongside the configured names, so --allow-host never locks an operator out
// of their own 127.0.0.1 probe.
func (g *Gateway) hostAllowed(host string) bool {
	if allowedBy(g.cfg.AllowedHosts, host) {
		return true
	}
	name := host
	if h, _, err := net.SplitHostPort(host); err == nil {
		name = h
	}
	name = strings.Trim(name, "[]")
	if allowedBy(g.cfg.AllowedHosts, name) || strings.EqualFold(name, "localhost") {
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

// mcpHTTPHandler serves the MCP "streamable HTTP" transport on the front side,
// fully stateless: exactly one JSON-RPC message per POST, exactly one JSON
// response (or 202 for notifications). There are no front-side sessions
// (Mcp-Session-Id is ignored and never emitted) and no server-initiated
// streams, so the GET/SSE arm is a 405, as the spec permits. Per-backend
// sessions live entirely inside backend.go and never leak out here.
//
// Ported from postsql/internal/cli/mcp_http.go so the two endpoints behave
// identically byte-for-byte on transport errors.
func (g *Gateway) mcpHTTPHandler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// The method check is first because it reveals nothing and reads nothing;
		// everything after it can reach JIVO's production backends.
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", http.MethodPost)
			http.Error(w, "method not allowed: this MCP endpoint is stateless (POST one JSON-RPC message; no SSE stream, no sessions)", http.StatusMethodNotAllowed)
			return
		}
		if reason, status := g.checkHTTPRequest(r); status != 0 {
			http.Error(w, reason, status)
			return
		}

		body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, httpBodyLimit))
		if err != nil {
			mcpHTTPError(w, http.StatusBadRequest, -32700, "parse error: "+err.Error())
			return
		}

		resp, err := g.handleMessage(r.Context(), body)
		if err != nil {
			mcpHTTPError(w, http.StatusBadRequest, -32700, "parse error: "+err.Error())
			return
		}
		if resp == nil { // notification: accepted, nothing to say
			w.WriteHeader(http.StatusAccepted)
			return
		}

		b, err := json.Marshal(resp)
		if err != nil {
			mcpHTTPError(w, http.StatusInternalServerError, -32603, "marshal error: "+err.Error())
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write(b)
	})
}

// mcpHTTPError writes a JSON-RPC error object (id null) with the given HTTP
// status.
func mcpHTTPError(w http.ResponseWriter, status, code int, msg string) {
	resp := rpcResponse{
		JSONRPC: "2.0",
		ID:      json.RawMessage("null"),
		Error:   &rpcError{Code: code, Message: msg},
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

// Handler returns the gateway's HTTP surface: the MCP endpoint at /mcp plus a
// trivial /healthz for container health checks.
//
// /mcp/ is registered as well as /mcp. Behind a reverse proxy the endpoint's
// exact path is whatever the proxy leaves behind — Traefik's stripPrefix in
// particular can hand us "/mcp/" — and a 404 there is a silent, confusing
// outage. "{$}" keeps it to that one extra path instead of a whole subtree.
func (g *Gateway) Handler() http.Handler {
	mux := http.NewServeMux()
	mcp := g.mcpHTTPHandler()
	mux.Handle("/mcp", mcp)
	mux.Handle("/mcp/{$}", mcp)
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		w.Write([]byte("ok"))
	})
	return mux
}

// ListenAndServe blocks serving Handler() on cfg.Addr.
//
// The timeouts are the front door's only protection: this endpoint is reachable
// through a public reverse proxy, and a connection that opens and then dribbles
// (or opens and says nothing) must not be able to accumulate. There is
// deliberately no WriteTimeout — a forwarded SAP query is allowed to take the
// full --call-timeout before there is anything to write.
func (g *Gateway) ListenAndServe() error {
	return g.server().ListenAndServe()
}

// server builds the front-side http.Server. Split out from ListenAndServe so the
// timeouts are assertable without binding a port.
func (g *Gateway) server() *http.Server {
	return &http.Server{
		Addr:              g.cfg.Addr,
		Handler:           g.Handler(),
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       60 * time.Second,
		IdleTimeout:       120 * time.Second,
	}
}
