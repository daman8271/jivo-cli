package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// mcpHTTPBodyLimit caps a single JSON-RPC request body (4 MiB).
const mcpHTTPBodyLimit = 4 << 20

// mcpHTTPHandler serves the MCP "streamable HTTP" transport, fully stateless:
// exactly one JSON-RPC message per POST, exactly one JSON response (or 202 for
// notifications). There are no sessions (Mcp-Session-Id is ignored and never
// emitted) and no server-initiated streams, so the GET/SSE arm is a 405, as
// the spec permits. Everything below the transport — tool definitions, SQL,
// the READ ONLY transaction guarantee — is shared with the stdio path.
func mcpHTTPHandler(app *App) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", http.MethodPost)
			http.Error(w, "method not allowed: this MCP endpoint is stateless (POST one JSON-RPC message; no SSE stream, no sessions)", http.StatusMethodNotAllowed)
			return
		}

		body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, mcpHTTPBodyLimit))
		if err != nil {
			mcpHTTPError(w, http.StatusBadRequest, -32700, "parse error: "+err.Error())
			return
		}

		resp, err := mcpHandleMessage(app, body)
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

// mcpServeHTTP blocks serving the MCP endpoint at /mcp on addr.
func mcpServeHTTP(app *App, addr string) error {
	mux := http.NewServeMux()
	mux.Handle("/mcp", mcpHTTPHandler(app))
	srv := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
	}
	fmt.Fprintf(os.Stderr, "postsql: MCP server listening on http://%s/mcp\n", addr)
	return srv.ListenAndServe()
}
