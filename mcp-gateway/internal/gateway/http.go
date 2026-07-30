package gateway

import (
	"encoding/json"
	"io"
	"net/http"
	"time"
)

// httpBodyLimit caps a single JSON-RPC request body (4 MiB), same as postsql.
const httpBodyLimit = 4 << 20

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
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", http.MethodPost)
			http.Error(w, "method not allowed: this MCP endpoint is stateless (POST one JSON-RPC message; no SSE stream, no sessions)", http.StatusMethodNotAllowed)
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
