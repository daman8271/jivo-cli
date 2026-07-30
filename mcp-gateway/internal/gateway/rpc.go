package gateway

import "encoding/json"

// --- JSON-RPC 2.0 wire types --------------------------------------------------
//
// Shapes and names mirror postsql/internal/cli/mcp.go so the two servers read
// the same. The one difference: Result is a json.RawMessage, because most of
// what this gateway returns is a backend's own result bytes forwarded verbatim.

type rpcRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"` // absent => notification
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

type rpcResponse struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Result  json.RawMessage `json:"result,omitempty"`
	Error   *rpcError       `json:"error,omitempty"`
}

type rpcError struct {
	Code    int             `json:"code"`
	Message string          `json:"message"`
	Data    json.RawMessage `json:"data,omitempty"`
}

// jsonResult marshals a natively-produced result. Native results are built from
// plain maps, strings, numbers and json.RawMessage, so this cannot fail in
// practice; if it somehow does the caller returns an internal error instead of
// panicking. The (result, error) pair is shaped for direct assignment:
//
//	resp.Result, resp.Error = jsonResult(v)
func jsonResult(v any) (json.RawMessage, *rpcError) {
	b, err := json.Marshal(v)
	if err != nil {
		return nil, &rpcError{Code: -32603, Message: "internal error: " + err.Error()}
	}
	return b, nil
}

// toolResult builds an MCP tool result (postsql's mcpToolResult shape).
func toolResult(text string, isErr bool) map[string]any {
	return map[string]any{
		"content": []map[string]any{{"type": "text", "text": text}},
		"isError": isErr,
	}
}
