// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — tool result shaping.

package mcp

import (
	"encoding/json"
	"fmt"
	"time"

	"jsap-mcp/internal/jsap"

	mcplib "github.com/mark3labs/mcp-go/mcp"
)

const (
	// A JSAP read can be several megabytes (the budget fact table, the GRPO-
	// shaped lists). Hosts choke long before that, so every result is bounded
	// and says so, rather than being silently cut.
	mcpToolResultMaxBytes = 60000
	mcpToolResultMaxItems = 50
)

// result is the envelope every row-returning tool answers with. The company
// NAME is always present: in JSAP company 2 is JIVO BEVERAGE while in
// factory-cli company 2 is Mart, so a bare id is an invitation to
// cross-attribute one company's figures to another.
type result struct {
	System         string          `json:"system"`
	Command        string          `json:"command"`
	Request        string          `json:"request"`
	Company        *companyRef     `json:"company,omitempty"`
	AsOf           string          `json:"as_of"`
	RedactedFields []string        `json:"redacted_fields,omitempty"`
	Truncated      bool            `json:"truncated"`
	TotalCount     int             `json:"total_count,omitempty"`
	ReturnedCount  int             `json:"returned_count,omitempty"`
	OriginalBytes  int             `json:"original_bytes,omitempty"`
	Note           string          `json:"note,omitempty"`
	Data           json.RawMessage `json:"data"`
}

type companyRef struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

// commandResult wraps one catalogued command's payload: redact, bound, stamp.
func commandResult(cmd jsap.Command, company int, payload json.RawMessage) *mcplib.CallToolResult {
	res := result{
		System:  "jsap",
		Command: cmd.ID,
		Request: fmt.Sprintf("%s %s", cmd.Method, cmd.Path),
		AsOf:    time.Now().UTC().Format(time.RFC3339),
	}
	if cmd.CompanyParam != "" || company != 0 {
		res.Company = &companyRef{ID: company, Name: jsap.CompanyName(company)}
	}
	if cmd.CompanyParam == "" {
		res.Note = "this endpoint is not company-scoped; the company shown is the session's scope only"
	}

	cleaned, redacted, err := redactSalaries(payload)
	if err != nil {
		return mcplib.NewToolResultError(fmt.Sprintf("post-processing %s: %v", cmd.ID, err))
	}
	res.RedactedFields = redacted

	bounded, info := boundPayload(cleaned)
	res.Data = bounded
	res.Truncated = info.truncated
	res.TotalCount = info.totalCount
	res.ReturnedCount = info.returnedCount
	res.OriginalBytes = info.originalBytes

	encoded, err := json.MarshalIndent(res, "", "  ")
	if err != nil {
		return mcplib.NewToolResultError(fmt.Sprintf("encoding result for %s: %v", cmd.ID, err))
	}
	return mcplib.NewToolResultText(string(encoded))
}

// jsonResult renders any locally-computed answer (context, search) as JSON.
func jsonResult(v any) *mcplib.CallToolResult {
	encoded, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return mcplib.NewToolResultError(fmt.Sprintf("encoding result: %v", err))
	}
	return mcplib.NewToolResultText(string(encoded))
}

type boundInfo struct {
	truncated     bool
	totalCount    int
	returnedCount int
	originalBytes int
}

// boundPayload keeps a result under the host's comfortable size.
//
// Three shapes, in order: a top-level array is cut to a prefix of its items; an
// object's single largest array field is cut the same way (the surrounding
// metadata is preserved, since that is where JSAP puts totals); anything else
// falls back to a truncation notice with a preview. In every case the envelope
// records that the answer is partial — a silently short list reads exactly like
// a complete one, and that is how an agent under-reports a number.
func boundPayload(payload json.RawMessage) (json.RawMessage, boundInfo) {
	info := boundInfo{originalBytes: len(payload)}
	if len(payload) <= mcpToolResultMaxBytes {
		return payload, boundInfo{originalBytes: len(payload)}
	}

	var asArray []json.RawMessage
	if err := json.Unmarshal(payload, &asArray); err == nil {
		kept := takeItems(asArray)
		encoded, err := json.Marshal(kept)
		if err == nil {
			info.truncated = true
			info.totalCount = len(asArray)
			info.returnedCount = len(kept)
			return encoded, info
		}
	}

	var asObject map[string]json.RawMessage
	if err := json.Unmarshal(payload, &asObject); err == nil {
		biggestKey, biggest := "", []json.RawMessage(nil)
		for key, value := range asObject {
			var items []json.RawMessage
			if err := json.Unmarshal(value, &items); err != nil {
				continue
			}
			if len(items) > len(biggest) {
				biggestKey, biggest = key, items
			}
		}
		if biggestKey != "" {
			kept := takeItems(biggest)
			if encoded, err := json.Marshal(kept); err == nil {
				asObject[biggestKey] = encoded
				if rebuilt, err := json.Marshal(asObject); err == nil && len(rebuilt) <= mcpToolResultMaxBytes {
					info.truncated = true
					info.totalCount = len(biggest)
					info.returnedCount = len(kept)
					return rebuilt, info
				}
			}
		}
	}

	notice := map[string]any{
		"truncated": true,
		"preview":   preview(payload, mcpToolResultMaxBytes/2),
	}
	encoded, err := json.Marshal(notice)
	if err != nil {
		encoded = []byte(`{"truncated":true}`)
	}
	info.truncated = true
	return encoded, info
}

// takeItems returns the longest prefix that fits both caps.
func takeItems(items []json.RawMessage) []json.RawMessage {
	budget := mcpToolResultMaxBytes / 2
	kept := make([]json.RawMessage, 0, mcpToolResultMaxItems)
	used := 0
	for _, item := range items {
		if len(kept) >= mcpToolResultMaxItems || used+len(item) > budget {
			break
		}
		kept = append(kept, item)
		used += len(item)
	}
	return kept
}

func preview(b []byte, n int) string {
	if len(b) <= n {
		return string(b)
	}
	return string(b[:n]) + "…"
}
