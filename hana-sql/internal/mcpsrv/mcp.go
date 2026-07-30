// Package mcpsrv serves hana-sql's read-only HANA connection to MCP-aware AI
// clients over two transports.
//
// The wire layer is hand-rolled JSON-RPC 2.0, structurally the same as
// postsql/internal/cli/mcp.go — same type names, same transport-neutral
// handleMessage contract, same stateless HTTP arm — so the two backends behave
// identically behind the gateway and there is one shape to reason about.
//
// Nothing in this package decides what is read-only. That is internal/guard
// (layers 0-3) and internal/hana (layers 4-5); this package only carries JSON.
package mcpsrv

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"hana-sql/internal/hana"
)

// --- JSON-RPC 2.0 wire types --------------------------------------------------

type mcpRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"` // absent => notification
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

type mcpResponse struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Result  any             `json:"result,omitempty"`
	Error   *mcpRPCError    `json:"error,omitempty"`
}

type mcpRPCError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// ServerName and ServerVersion identify this backend in initialize.
const (
	ServerName    = "hana-sql"
	ServerVersion = "0.1.0"
)

// SupportedProtocolVersions are the MCP revisions this server actually
// implements, newest first. DefaultProtocolVersion is what a client that asks
// for something else is answered with.
//
// initialize used to echo whatever string arrived — "1999-01-01-BOGUS" came back
// verbatim — which makes negotiation a no-op: the client cannot discover that
// the server does not speak its revision. Both 2024-11-05 and 2025-03-26 mandate
// JSON-RPC batching, which is why handleMessage implements it.
var SupportedProtocolVersions = []string{"2025-06-18", "2025-03-26", "2024-11-05"}

const DefaultProtocolVersion = "2024-11-05"

// Server is one MCP endpoint over one HANA connection.
//
// DB may be nil: the transport, tools/list and every argument-validation path
// work without a database, which is what makes the transport suite runnable
// with no HANA in the process at all.
type Server struct {
	DB *hana.DB

	// Now supplies as_of. Overridable for deterministic tests.
	Now func() time.Time
	// Log receives transport-level messages (stderr in production).
	Log io.Writer

	// AllowedOrigins are the browser origins the HTTP transport accepts. EMPTY
	// MEANS DENY EVERY ORIGIN, which is the right default: a request carrying an
	// Origin header came from a web page, and no web page has business driving
	// production HANA. "*" disables the check.
	AllowedOrigins []string
	// AllowedHosts extends the Host allowlist beyond loopback, for the rare
	// deployment that fronts this endpoint with a reverse proxy. "*" disables the
	// check. See checkHTTPRequest for why Host is validated at all.
	AllowedHosts []string
	// AuthToken, when non-empty, requires `Authorization: Bearer <AuthToken>` on
	// every HTTP request.
	AuthToken string
}

// New builds a Server around a lazily-connected DB.
func New(db *hana.DB) *Server {
	return &Server{DB: db, Now: time.Now, Log: os.Stderr}
}

func (s *Server) now() time.Time {
	if s.Now != nil {
		return s.Now()
	}
	return time.Now()
}

func (s *Server) logf(format string, args ...any) {
	if s.Log == nil {
		return
	}
	fmt.Fprintf(s.Log, format+"\n", args...)
}

// ServeStdio runs the newline-delimited JSON-RPC loop until stdin closes. One
// request per line in, one response per line out; logs go to stderr only, so
// they can never corrupt the protocol stream.
func (s *Server) ServeStdio(in io.Reader, out io.Writer) error {
	s.logf("hana-sql: MCP server ready on stdio")

	reader := bufio.NewReader(in)
	writer := bufio.NewWriter(out)
	defer writer.Flush()

	for {
		line, err := reader.ReadBytes('\n')
		if trimmed := strings.TrimSpace(string(line)); trimmed != "" {
			s.handleLine(writer, []byte(trimmed))
		}
		if err != nil {
			if err == io.EOF {
				return nil
			}
			s.logf("hana-sql: read error: %v", err)
			return nil
		}
	}
}

// handleLine parses one line and writes at most one payload. Parse errors are
// logged, never fatal: the loop must survive a malformed client.
func (s *Server) handleLine(w *bufio.Writer, line []byte) {
	payload, err := s.handleMessage(context.Background(), line)
	if err != nil {
		s.logf("hana-sql: parse error: %v", err)
		return
	}
	if payload != nil {
		s.write(w, payload)
	}
}

// handleMessage parses and dispatches one JSON-RPC message OR one batch (a
// top-level array), transport-neutrally.
//
// It returns (nil, err) when the bytes are not valid JSON-RPC, (nil, nil) when
// there is nothing to answer (a notification, or a batch of only
// notifications), and otherwise the payload to marshal: one response object, or
// an array of them for a batch.
//
// Batching is here because a top-level array used to fail json.Unmarshal into
// mcpRequest, get logged to stderr and produce NO response at all — a client
// that batched simply hung on stdio and got a hard 400 over HTTP, while
// initialize happily advertised protocol revisions that require batching.
func (s *Server) handleMessage(ctx context.Context, raw []byte) (any, error) {
	trimmed := bytes.TrimSpace(raw)
	if len(trimmed) == 0 {
		return nil, errors.New("empty message")
	}
	if trimmed[0] != '[' {
		resp, err := s.handleOne(ctx, trimmed)
		if err != nil || resp == nil {
			return nil, err
		}
		return resp, nil
	}

	var msgs []json.RawMessage
	if err := json.Unmarshal(trimmed, &msgs); err != nil {
		return nil, err
	}
	if len(msgs) == 0 {
		return &mcpResponse{JSONRPC: "2.0", ID: json.RawMessage("null"),
			Error: &mcpRPCError{Code: -32600, Message: "invalid request: an empty array is not a valid JSON-RPC batch"}}, nil
	}
	out := make([]*mcpResponse, 0, len(msgs))
	for _, m := range msgs {
		resp, err := s.handleOne(ctx, m)
		if err != nil {
			out = append(out, &mcpResponse{JSONRPC: "2.0", ID: json.RawMessage("null"),
				Error: &mcpRPCError{Code: -32700, Message: "parse error: " + err.Error()}})
			continue
		}
		if resp != nil {
			out = append(out, resp)
		}
	}
	if len(out) == 0 { // an all-notification batch is answered with silence
		return nil, nil
	}
	return out, nil
}

// handleOne dispatches exactly one JSON-RPC message.
func (s *Server) handleOne(ctx context.Context, raw []byte) (*mcpResponse, error) {
	var req mcpRequest
	if err := json.Unmarshal(raw, &req); err != nil {
		return nil, err
	}
	// The version field is accepted when absent (lenient, and harmless) but a
	// WRONG value is refused rather than answered as if it were 2.0.
	if req.JSONRPC != "" && req.JSONRPC != "2.0" {
		if len(req.ID) == 0 {
			return nil, nil
		}
		return &mcpResponse{JSONRPC: "2.0", ID: req.ID, Error: &mcpRPCError{Code: -32600,
			Message: fmt.Sprintf("invalid request: jsonrpc must be \"2.0\", got %q", req.JSONRPC)}}, nil
	}
	if len(req.ID) == 0 || strings.HasPrefix(req.Method, "notifications/") {
		return nil, nil
	}

	resp := &mcpResponse{JSONRPC: "2.0", ID: req.ID}
	switch req.Method {
	case "initialize":
		resp.Result = initializeResult(req.Params)
	case "ping":
		resp.Result = struct{}{}
	case "tools/list":
		resp.Result = map[string]any{"tools": s.ToolDefs()}
	case "tools/call":
		resp.Result = s.callTool(ctx, req.Params)
	default:
		resp.Error = &mcpRPCError{Code: -32601, Message: "method not found: " + req.Method}
	}
	return resp, nil
}

func (s *Server) write(w *bufio.Writer, payload any) {
	b, err := json.Marshal(payload)
	if err != nil {
		s.logf("hana-sql: marshal error: %v", err)
		return
	}
	w.Write(b)
	w.WriteByte('\n')
	w.Flush()
}

// initializeResult answers with a protocol version this server actually speaks.
//
// A client asking for a supported revision gets it back; anything else gets the
// default, which is the whole point of negotiation — the client can compare what
// it asked for with what it got and decide.
func initializeResult(params json.RawMessage) map[string]any {
	protocol := DefaultProtocolVersion
	if len(params) > 0 {
		var p struct {
			ProtocolVersion string `json:"protocolVersion"`
		}
		if json.Unmarshal(params, &p) == nil && p.ProtocolVersion != "" {
			for _, v := range SupportedProtocolVersions {
				if v == p.ProtocolVersion {
					protocol = v
					break
				}
			}
		}
	}
	return map[string]any{
		"protocolVersion": protocol,
		"capabilities":    map[string]any{"tools": map[string]any{}},
		"serverInfo":      map[string]any{"name": ServerName, "version": ServerVersion},
	}
}
