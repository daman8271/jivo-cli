package cli

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"sapb1/internal/client"
)

func TestParseFieldList(t *testing.T) {
	cases := map[string][]string{
		"":                     nil,
		"  ":                   nil,
		"DocEntry":             {"DocEntry"},
		"DocEntry,DocNum":      {"DocEntry", "DocNum"},
		"DocEntry, DocNum , X": {"DocEntry", "DocNum", "X"},
	}
	for in, want := range cases {
		got := parseFieldList(in)
		if len(got) != len(want) {
			t.Errorf("parseFieldList(%q) = %v, want %v", in, got, want)
			continue
		}
		for i := range want {
			if got[i] != want[i] {
				t.Errorf("parseFieldList(%q) = %v, want %v", in, got, want)
				break
			}
		}
	}
}

func TestCombineFilters(t *testing.T) {
	if got := combineFilters("", ""); got != "" {
		t.Errorf("combineFilters(empty) = %q, want empty", got)
	}
	if got, want := combineFilters("DocStatus eq 'O'", ""), "(DocStatus eq 'O')"; got != want {
		t.Errorf("combineFilters = %q, want %q", got, want)
	}
	got := combineFilters("DocStatus eq 'O'", "DocTotal gt 100")
	want := "(DocStatus eq 'O') and (DocTotal gt 100)"
	if got != want {
		t.Errorf("combineFilters = %q, want %q", got, want)
	}
}

func TestRenderJSONNeverPanicsOnEmpty(t *testing.T) {
	var buf bytes.Buffer
	if err := renderJSON(&buf, nil); err != nil {
		t.Fatalf("renderJSON(nil): %v", err)
	}
	var out []map[string]interface{}
	if err := json.Unmarshal(buf.Bytes(), &out); err != nil {
		t.Fatalf("output isn't valid JSON: %v\n%s", err, buf.String())
	}
	if out == nil {
		t.Errorf("expected an empty array, not null, for piping into jq")
	}
}

func TestRenderTableColumnsAndOrder(t *testing.T) {
	rows := []map[string]interface{}{
		{"DocEntry": float64(5), "CardName": "Acme Corp", "DocTotal": float64(1234.5)},
	}
	var buf bytes.Buffer
	renderTable(&buf, rows, []string{"DocEntry", "CardName", "DocTotal"})
	out := buf.String()

	if !strings.Contains(out, "DocEntry") || !strings.Contains(out, "CardName") || !strings.Contains(out, "DocTotal") {
		t.Fatalf("table missing expected headers:\n%s", out)
	}
	if !strings.Contains(out, "Acme Corp") {
		t.Fatalf("table missing row data:\n%s", out)
	}
	if strings.Contains(out, "5.0") {
		t.Errorf("integral float64 should render without trailing .0, got:\n%s", out)
	}
	if !strings.Contains(out, "1234.5") {
		t.Errorf("non-integral float should keep its decimal, got:\n%s", out)
	}
}

func TestRenderTableEmptyRows(t *testing.T) {
	var buf bytes.Buffer
	renderTable(&buf, nil, []string{"A", "B"})
	if got := strings.TrimSpace(buf.String()); got != "(no rows)" {
		t.Errorf("renderTable(empty) = %q, want (no rows)", got)
	}
}

func TestRenderCSVFixedColumns(t *testing.T) {
	rows := []map[string]interface{}{
		{"DocEntry": float64(5), "CardName": "Acme, Inc.", "Lines": []interface{}{map[string]interface{}{"ItemCode": "A1"}}},
		{"DocEntry": float64(6), "CardName": "Beta", "Lines": nil},
	}
	var buf bytes.Buffer
	if err := renderCSV(&buf, rows, []string{"DocEntry", "CardName", "Lines"}); err != nil {
		t.Fatalf("renderCSV: %v", err)
	}
	out := buf.String()

	// Header row in the requested order.
	if !strings.HasPrefix(out, "DocEntry,CardName,Lines\n") {
		t.Errorf("CSV header wrong:\n%s", out)
	}
	// Integral float renders without .0; a comma-bearing value gets quoted.
	if !strings.Contains(out, "5,\"Acme, Inc.\",") {
		t.Errorf("expected quoted CardName + integral DocEntry, got:\n%s", out)
	}
	// Array cell is JSON-encoded (and quoted because it contains commas/braces).
	if !strings.Contains(out, `"[{""ItemCode"":""A1""}]"`) {
		t.Errorf("expected JSON-encoded array cell, got:\n%s", out)
	}
}

func TestRenderCSVUnionColumns(t *testing.T) {
	rows := []map[string]interface{}{
		{"B": "2", "A": "1"},
	}
	var buf bytes.Buffer
	if err := renderCSV(&buf, rows, nil); err != nil {
		t.Fatalf("renderCSV: %v", err)
	}
	// With no explicit columns, keys are the sorted union: A before B.
	if !strings.HasPrefix(buf.String(), "A,B\n") {
		t.Errorf("expected sorted union header A,B, got:\n%s", buf.String())
	}
}

func TestRenderCountServerSide(t *testing.T) {
	var buf bytes.Buffer
	res := &client.QueryResult{Count: 42, CountKnown: true}
	if err := renderCount(&buf, res, false); err != nil {
		t.Fatalf("renderCount: %v", err)
	}
	if got := strings.TrimSpace(buf.String()); got != "42" {
		t.Errorf("renderCount server-side = %q, want 42", got)
	}
}

func TestRenderCountFallback(t *testing.T) {
	var buf bytes.Buffer
	res := &client.QueryResult{
		Value:      []map[string]interface{}{{"A": 1}, {"A": 2}},
		CountKnown: false,
	}
	if err := renderCount(&buf, res, false); err != nil {
		t.Fatalf("renderCount: %v", err)
	}
	out := buf.String()
	if !strings.Contains(out, "2") {
		t.Errorf("fallback count should print returned-row count 2, got:\n%s", out)
	}
	if !strings.Contains(out, "note:") {
		t.Errorf("fallback count should carry a note, got:\n%s", out)
	}
}

func TestRenderResultCappedNote(t *testing.T) {
	var buf bytes.Buffer
	res := &client.QueryResult{
		Value:  []map[string]interface{}{{"A": "x"}},
		Capped: true,
	}
	if err := renderResult(&buf, res, false, []string{"A"}); err != nil {
		t.Fatalf("renderResult: %v", err)
	}
	if !strings.Contains(buf.String(), "stopped after") {
		t.Errorf("expected a capped-pagination note in output, got:\n%s", buf.String())
	}
}
