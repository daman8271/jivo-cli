package mcp

import (
	"context"
	"encoding/json"
	"fmt"
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

// invokeTool drives one tools/call through the real JSON-RPC path, exactly as a
// stdio client would, WITHOUT touching *testing.T — so it is safe to call from
// a goroutine (t.Fatalf outside the test goroutine is a runtime error, and the
// concurrency tests need many callers at once).
func invokeTool(s *Server, name string, args map[string]any) (isError bool, text string, err error) {
	payload, err := json.Marshal(map[string]any{
		"jsonrpc": "2.0", "id": 99, "method": "tools/call",
		"params": map[string]any{"name": name, "arguments": args},
	})
	if err != nil {
		return false, "", fmt.Errorf("building tools/call: %w", err)
	}
	resp := s.MCPServer().HandleMessage(context.Background(), payload)
	if resp == nil {
		return false, "", fmt.Errorf("tools/call %s returned nil response", name)
	}
	raw, err := json.Marshal(resp)
	if err != nil {
		return false, "", fmt.Errorf("marshaling tools/call response: %w", err)
	}
	return parseToolCallResponse(raw)
}

// parseToolCallResponse decodes a tools/call JSON-RPC response into
// (isError, text).
func parseToolCallResponse(raw []byte) (isError bool, text string, err error) {
	var parsed struct {
		Result struct {
			IsError bool `json:"isError"`
			Content []struct {
				Text string `json:"text"`
			} `json:"content"`
		} `json:"result"`
		Error *struct {
			Message string `json:"message"`
		} `json:"error"`
	}
	if err := json.Unmarshal(raw, &parsed); err != nil {
		return false, "", fmt.Errorf("parsing tools/call response %s: %w", raw, err)
	}
	if parsed.Error != nil {
		// A protocol-level error is also a rejection; surface its message.
		return true, parsed.Error.Message, nil
	}
	var sb strings.Builder
	for _, c := range parsed.Result.Content {
		sb.WriteString(c.Text)
	}
	return parsed.Result.IsError, sb.String(), nil
}

// callTool is invokeTool for the test goroutine, failing the test on any
// transport-level problem.
func callTool(t *testing.T, s *Server, name string, args map[string]any) (isError bool, text string) {
	t.Helper()
	isErr, out, err := invokeTool(s, name, args)
	if err != nil {
		t.Fatalf("%v", err)
	}
	return isErr, out
}

// requiredArgsFor is the smallest valid argument set for each tool, so a test
// can isolate the effect of adding ONE bad argument.
var requiredArgsFor = map[string]map[string]any{
	"sapb1_doctor":   {},
	"sapb1_entities": {},
	"sapb1_fields":   {"entity": "Orders"},
	"sapb1_invoices": {},
	"sapb1_items":    {},
	"sapb1_ops":      {"service": "Orders"},
	"sapb1_orders":   {},
	"sapb1_partners": {},
	"sapb1_query":    {"entity": "Orders"},
}

// TestEveryToolRejectsUnknownArgumentsOverJSONRPC is the D2 tripwire, and it
// plays the same role for silent-parameter-discard that
// TestRegisteredToolsAreReadOnly plays for RULE 0.
//
// The defect it guards against is not a crash — it is a SUCCESSFUL-LOOKING
// answer. `sapb1_query` used to accept company/companyDB/db/database, ignore
// them, and return the default company's rows. An agent asking for Beverages
// got Oil, formatted exactly like a correct answer, with nothing anywhere in
// the response to say so. A measured 31.5x error with no tell.
//
// Every tool, offline ones included, must therefore reject unknown arguments
// through the real transport — not merely in a unit test of the decoder, which
// a handler could bypass.
func TestEveryToolRejectsUnknownArgumentsOverJSONRPC(t *testing.T) {
	s := newTestServer()

	for _, name := range wantTools {
		t.Run(name, func(t *testing.T) {
			base, ok := requiredArgsFor[name]
			if !ok {
				t.Fatalf("no required-args entry for registered tool %q — add one", name)
			}
			args := map[string]any{}
			for k, v := range base {
				args[k] = v
			}
			// The historical offender plus an obviously invented key.
			args["companyDB"] = "JIVO_MART_HANADB"
			args["bogus_xyz"] = 1

			isErr, text := callTool(t, s, name, args)
			if !isErr {
				t.Fatalf("%s ACCEPTED unknown arguments and answered anyway: %s", name, text)
			}
			for _, want := range []string{"companyDB", "bogus_xyz", "valid parameters:", "company"} {
				if !strings.Contains(text, want) {
					t.Errorf("%s rejection message must mention %q, got: %s", name, want, text)
				}
			}
		})
	}
}

// TestUnknownCompanyIsRejectedOverJSONRPC — the other half of D1. A company
// value that isn't a real company must fail loudly; falling back to the default
// is exactly how one company's books get reported as another's.
func TestUnknownCompanyIsRejectedOverJSONRPC(t *testing.T) {
	s := newTestServer()
	for _, name := range wantTools {
		t.Run(name, func(t *testing.T) {
			args := map[string]any{"company": "JIVO_MART"} // plausible typo
			for k, v := range requiredArgsFor[name] {
				args[k] = v
			}
			isErr, text := callTool(t, s, name, args)
			if !isErr {
				t.Fatalf("%s accepted an unknown company and answered anyway: %s", name, text)
			}
			if !strings.Contains(text, "unknown company") {
				t.Errorf("%s must say the company is unknown, got: %s", name, text)
			}
			for _, db := range companyEnum {
				if !strings.Contains(text, db) {
					t.Errorf("%s rejection must list %s so the agent can retry, got: %s", name, db, text)
				}
			}
		})
	}
}

// TestAdvertisedSchemasForbidAdditionalProperties guards
// server.WithStrictInputSchemaDefault() against a silent regression: a
// schema-aware client should be steered away from inventing a parameter before
// it ever sends one. (Our decoder is still the authoritative rejection — this
// is the earlier, cheaper layer.)
func TestAdvertisedSchemasForbidAdditionalProperties(t *testing.T) {
	s := newTestServer()
	ctx := context.Background()

	initReq := `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}`
	if resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(initReq)); resp == nil {
		t.Fatal("initialize returned nil response")
	}
	resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(`{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}`))
	raw, err := json.Marshal(resp)
	if err != nil {
		t.Fatalf("marshaling tools/list: %v", err)
	}

	var parsed struct {
		Result struct {
			Tools []struct {
				Name        string `json:"name"`
				InputSchema struct {
					AdditionalProperties *bool               `json:"additionalProperties"`
					Properties           map[string]struct { // presence check only
						Type any `json:"type"`
					} `json:"properties"`
				} `json:"inputSchema"`
			} `json:"tools"`
		} `json:"result"`
	}
	if err := json.Unmarshal(raw, &parsed); err != nil {
		t.Fatalf("parsing tools/list %s: %v", raw, err)
	}
	if len(parsed.Result.Tools) != len(wantTools) {
		t.Fatalf("advertised %d tools, want %d", len(parsed.Result.Tools), len(wantTools))
	}
	for _, tl := range parsed.Result.Tools {
		if tl.InputSchema.AdditionalProperties == nil {
			t.Errorf("tool %q advertises no additionalProperties — WithStrictInputSchemaDefault regressed", tl.Name)
			continue
		}
		if *tl.InputSchema.AdditionalProperties {
			t.Errorf("tool %q advertises additionalProperties:true — invented parameters would look legal", tl.Name)
		}
		// Every tool must advertise `company`, or an agent cannot discover that
		// the other two companies are reachable at all (the D1 refusals).
		if _, ok := tl.InputSchema.Properties["company"]; !ok {
			t.Errorf("tool %q does not advertise a company parameter", tl.Name)
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
