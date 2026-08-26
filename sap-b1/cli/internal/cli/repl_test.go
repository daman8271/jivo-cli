package cli

import (
	"bytes"
	"context"
	"strings"
	"testing"
)

func TestSplitLineKeepsODataFiltersIntact(t *testing.T) {
	// The whole reason for a custom splitter: an OData filter is one argument
	// full of spaces and single quotes.
	got := splitLine(`query Invoices --filter "DocDate ge '2026-08-01' and Cancelled eq 'tNO'" --top 5`)
	want := []string{"query", "Invoices", "--filter",
		"DocDate ge '2026-08-01' and Cancelled eq 'tNO'", "--top", "5"}
	if len(got) != len(want) {
		t.Fatalf("got %d tokens %q, want %d %q", len(got), got, len(want), want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("token %d = %q, want %q", i, got[i], want[i])
		}
	}
}

func TestSplitLineEscapesAndEmpty(t *testing.T) {
	if got := splitLine(""); len(got) != 0 {
		t.Errorf("empty line produced %q", got)
	}
	if got := splitLine(`a\ b c`); len(got) != 2 || got[0] != "a b" || got[1] != "c" {
		t.Errorf("escape handling: %q", got)
	}
}

func TestCompanyAliasesResolve(t *testing.T) {
	for in, want := range map[string]string{
		"oil": "JIVO_OIL_HANADB", "MART": "JIVO_MART_HANADB",
		"bev": "JIVO_BEVERAGES_HANADB", "beverages": "JIVO_BEVERAGES_HANADB",
		"JIVO_OIL_HANADB": "JIVO_OIL_HANADB", "something_else": "something_else",
	} {
		if got := resolveCompany(in); got != want {
			t.Errorf("resolveCompany(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestStateFlagsNeverEmitBothJSONAndCSV(t *testing.T) {
	// The root command rejects --json with --csv, so the session must not be
	// able to hold both. Setting one clears the other.
	s := &replSession{out: &bytes.Buffer{}}
	s.handleSet([]string{"json", "on"})
	s.handleSet([]string{"csv", "on"})
	flags := s.state.flags()
	var hasJSON, hasCSV bool
	for _, f := range flags {
		hasJSON = hasJSON || f == "--json"
		hasCSV = hasCSV || f == "--csv"
	}
	if hasJSON && hasCSV {
		t.Fatalf("session emitted both --json and --csv: %q", flags)
	}
	if !hasCSV {
		t.Errorf("last setting should win, got %q", flags)
	}
}

func TestUndoRedoWalksSessionState(t *testing.T) {
	s := &replSession{out: &bytes.Buffer{}}
	s.handleSet([]string{"company", "oil"})
	s.handleSet([]string{"company", "mart"})
	if s.state.company != "JIVO_MART_HANADB" {
		t.Fatalf("company = %q", s.state.company)
	}
	if err := s.doUndo(); err != nil {
		t.Fatalf("undo: %v", err)
	}
	if s.state.company != "JIVO_OIL_HANADB" {
		t.Errorf("after undo company = %q, want Oil", s.state.company)
	}
	if err := s.doUndo(); err != nil {
		t.Fatalf("second undo: %v", err)
	}
	if s.state.company != "" {
		t.Errorf("after two undos company = %q, want empty", s.state.company)
	}
	if err := s.doUndo(); err == nil {
		t.Error("undo past the start should report there is nothing to undo")
	}
	if err := s.doRedo(); err != nil {
		t.Fatalf("redo: %v", err)
	}
	if s.state.company != "JIVO_OIL_HANADB" {
		t.Errorf("after redo company = %q, want Oil", s.state.company)
	}
}

func TestNewChangeClearsRedoStack(t *testing.T) {
	s := &replSession{out: &bytes.Buffer{}}
	s.handleSet([]string{"company", "oil"})
	if err := s.doUndo(); err != nil {
		t.Fatal(err)
	}
	s.handleSet([]string{"company", "bev"})
	if err := s.doRedo(); err == nil {
		t.Error("a new change must invalidate redo")
	}
}

// The load-bearing safety test: no write command may execute from the REPL, and
// the refusal must hand back a runnable command rather than a lecture.
func TestWriteCommandsAreRefusedWithARunnableCommand(t *testing.T) {
	for verb := range writeVerbs {
		buf := &bytes.Buffer{}
		s := &replSession{out: buf}
		s.handleSet([]string{"company", "mart"})
		buf.Reset()
		s.dispatch(context.Background(), []string{verb, "purchase-invoice", "--data-file", "x.json"})
		got := buf.String()
		if !strings.Contains(got, "cannot run it") {
			t.Errorf("%s was not refused: %q", verb, got)
		}
		if !strings.Contains(got, "sapb1 --company JIVO_MART_HANADB "+verb) {
			t.Errorf("%s refusal did not print the paste-able command: %q", verb, got)
		}
		if !strings.Contains(got, "writes are authorised") {
			t.Errorf("%s refusal must not read as a permission refusal: %q", verb, got)
		}
	}
}

func TestTopOnlyInjectedIntoCommandsThatTakeIt(t *testing.T) {
	if acceptsTop("doctor") || acceptsTop("entities") {
		t.Error("--top must not be injected into commands that reject it")
	}
	if !acceptsTop("query") || !acceptsTop("invoices") {
		t.Error("query/invoices take --top")
	}
	if !hasFlag([]string{"query", "--top", "5"}, "--top") {
		t.Error("hasFlag missed a separated flag")
	}
	if !hasFlag([]string{"query", "--top=5"}, "--top") {
		t.Error("hasFlag missed an = flag")
	}
}

func TestREPLRunsAndExitsCleanly(t *testing.T) {
	buf := &bytes.Buffer{}
	in := strings.NewReader(":set company bev\n:state\n:exit\n")
	if err := runREPL(context.Background(), in, buf); err != nil {
		t.Fatalf("runREPL: %v", err)
	}
	out := buf.String()
	if !strings.Contains(out, "JIVO_BEVERAGES_HANADB") {
		t.Errorf(":state did not report the company: %q", out)
	}
	if !strings.Contains(out, "bye") {
		t.Errorf("REPL did not exit cleanly: %q", out)
	}
}

func TestHelpDocumentsEveryMetaCommand(t *testing.T) {
	for _, name := range replCommandNames() {
		if !strings.Contains(replHelp, name) {
			t.Errorf("%s is implemented but missing from :help", name)
		}
	}
}
