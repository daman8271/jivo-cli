package mcp

import (
	"context"
	"encoding/json"
	"sort"
	"strings"
	"testing"

	"sapb1/internal/config"
)

// newTestServer builds a Server over a minimal config. No network is touched:
// these tests only exercise registration and the JSON-RPC tools/list path.
func newTestServer() *Server {
	return NewServer(&config.Config{Port: config.DefaultPort, Timeout: config.DefaultTimeout})
}

// wantTools is the exact set of tools the server must advertise.
var wantTools = []string{
	"sapb1_doctor",
	"sapb1_entities",
	"sapb1_fields",
	"sapb1_invoices",
	"sapb1_items",
	"sapb1_ops",
	"sapb1_orders",
	"sapb1_partners",
	"sapb1_query",
}

func TestRegisteredToolsAreReadOnly(t *testing.T) {
	s := newTestServer()
	tools := s.MCPServer().ListTools()

	var got []string
	for name, st := range tools {
		got = append(got, name)
		ro := st.Tool.Annotations.ReadOnlyHint
		if ro == nil || !*ro {
			t.Errorf("tool %q is not marked read-only (ReadOnlyHint must be true)", name)
		}
		// Nothing should ever be flagged destructive.
		if d := st.Tool.Annotations.DestructiveHint; d != nil && *d {
			t.Errorf("tool %q is marked destructive — MCP surface must be read-only", name)
		}
		if st.Tool.Description == "" {
			t.Errorf("tool %q has no description — every tool must guide the agent", name)
		}
	}
	sort.Strings(got)

	if len(got) != len(wantTools) {
		t.Fatalf("tool count = %d, want %d\n got:  %v\n want: %v", len(got), len(wantTools), got, wantTools)
	}
	for i := range wantTools {
		if got[i] != wantTools[i] {
			t.Fatalf("tool set mismatch\n got:  %v\n want: %v", got, wantTools)
		}
	}
}

// TestToolsListOverJSONRPC drives the real JSON-RPC path (initialize +
// tools/list) through HandleMessage, exactly like a stdio client would, and
// verifies the advertised tool names.
func TestToolsListOverJSONRPC(t *testing.T) {
	s := newTestServer()
	ctx := context.Background()

	initReq := `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}`
	if resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(initReq)); resp == nil {
		t.Fatal("initialize returned nil response")
	}

	listReq := `{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}`
	resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(listReq))
	if resp == nil {
		t.Fatal("tools/list returned nil response")
	}

	raw, err := json.Marshal(resp)
	if err != nil {
		t.Fatalf("marshaling tools/list response: %v", err)
	}

	var parsed struct {
		Result struct {
			Tools []struct {
				Name        string `json:"name"`
				Description string `json:"description"`
				Annotations struct {
					ReadOnlyHint *bool `json:"readOnlyHint"`
				} `json:"annotations"`
			} `json:"tools"`
		} `json:"result"`
	}
	if err := json.Unmarshal(raw, &parsed); err != nil {
		t.Fatalf("parsing tools/list response %s: %v", raw, err)
	}

	var got []string
	for _, tl := range parsed.Result.Tools {
		got = append(got, tl.Name)
		if tl.Description == "" {
			t.Errorf("tool %q advertised without a description", tl.Name)
		}
		if tl.Annotations.ReadOnlyHint == nil || !*tl.Annotations.ReadOnlyHint {
			t.Errorf("tool %q not advertised as read-only", tl.Name)
		}
	}
	sort.Strings(got)

	if len(got) != len(wantTools) {
		t.Fatalf("advertised %d tools, want %d: %v", len(got), len(wantTools), got)
	}
	for i := range wantTools {
		if got[i] != wantTools[i] {
			t.Fatalf("advertised tool set mismatch\n got:  %v\n want: %v", got, wantTools)
		}
	}
}

// TestOfflineEntitiesToolNeedsNoNetwork drives sapb1_entities through the real
// tools/call JSON-RPC path with no config and no network, proving the catalog
// tools work fully offline.
func TestOfflineEntitiesToolNeedsNoNetwork(t *testing.T) {
	s := newTestServer()
	ctx := context.Background()

	initReq := `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}`
	if resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(initReq)); resp == nil {
		t.Fatal("initialize returned nil response")
	}

	callReq := `{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sapb1_entities","arguments":{"search":"order"}}}`
	resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(callReq))
	if resp == nil {
		t.Fatal("tools/call returned nil response")
	}

	raw, err := json.Marshal(resp)
	if err != nil {
		t.Fatalf("marshaling tools/call response: %v", err)
	}

	var parsed struct {
		Result struct {
			IsError bool `json:"isError"`
			Content []struct {
				Type string `json:"type"`
				Text string `json:"text"`
			} `json:"content"`
		} `json:"result"`
	}
	if err := json.Unmarshal(raw, &parsed); err != nil {
		t.Fatalf("parsing tools/call response %s: %v", raw, err)
	}
	if parsed.Result.IsError {
		t.Fatalf("offline entities call returned an error result: %s", raw)
	}
	if len(parsed.Result.Content) == 0 {
		t.Fatalf("offline entities call returned no content: %s", raw)
	}
	// The JSON text content should mention a matching service.
	body := parsed.Result.Content[0].Text
	if !json.Valid([]byte(body)) {
		t.Fatalf("entities content is not valid JSON: %q", body)
	}
	if !strings.Contains(body, "Orders") {
		t.Fatalf("expected an Orders service in the offline result, got: %s", body)
	}
}
