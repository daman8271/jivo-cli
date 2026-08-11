package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"testing"

	mcplib "github.com/mark3labs/mcp-go/mcp"

	"dsr/internal/mcp/cobratree"
)

// wantTools is the exact set of tools the server must advertise. dsr's command
// tree has 84 runnable leaves; a blanket walker would emit 84 tools. These 15
// are the reviewed surface, and this list is the review — adding a tool means
// changing this test on purpose.
var wantTools = []string{
	"dsr_admin",
	"dsr_attendance",
	"dsr_doctor",
	"dsr_ecom",
	"dsr_incentives",
	"dsr_portal",
	"dsr_products",
	"dsr_query",
	"dsr_retailers",
	"dsr_salespersons",
	"dsr_schema",
	"dsr_sales",
	"dsr_supply",
	"dsr_territory",
	"dsr_travel",
}

func TestRegisteredToolSetIsExactlyTheAllowlist(t *testing.T) {
	s := NewServer()
	tools := s.MCPServer().ListTools()

	var got []string
	for name, st := range tools {
		got = append(got, name)

		ro := st.Tool.Annotations.ReadOnlyHint
		if ro == nil || !*ro {
			t.Errorf("tool %q is not marked read-only (ReadOnlyHint must be true) — an MCP host treats a missing hint as 'could write'", name)
		}
		if d := st.Tool.Annotations.DestructiveHint; d != nil && *d {
			t.Errorf("tool %q is marked destructive — the MCP surface is read-only forever", name)
		}
		if st.Tool.Description == "" {
			t.Errorf("tool %q has no description — every tool must guide the agent", name)
		}
	}
	sort.Strings(got)

	want := append([]string{}, wantTools...)
	sort.Strings(want)

	if len(got) != len(want) {
		t.Fatalf("tool count = %d, want %d\n got:  %v\n want: %v", len(got), len(want), got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("tool set mismatch\n got:  %v\n want: %v", got, want)
		}
	}
}

// TestToolTableIsInternallyConsistent catches the table bugs that would
// otherwise only show up as a confusing runtime error: an action referencing a
// parameter the tool does not declare, a positional that is not positional, a
// duplicate name.
func TestToolTableIsInternallyConsistent(t *testing.T) {
	seenTool := map[string]bool{}
	for _, spec := range specs {
		if seenTool[spec.Name] {
			t.Errorf("duplicate tool name %q", spec.Name)
		}
		seenTool[spec.Name] = true

		if !strings.HasPrefix(spec.Name, "dsr_") {
			t.Errorf("tool %q must carry the dsr_ prefix the gateway routes on", spec.Name)
		}
		if (len(spec.Actions) == 0) == (len(spec.Fixed) == 0) {
			t.Errorf("tool %q must declare either Actions or a Fixed argv, not both/neither", spec.Name)
		}

		seenParam := map[string]bool{}
		positionals := 0
		for _, p := range spec.Params {
			if seenParam[p.Name] {
				t.Errorf("%s: duplicate parameter %q", spec.Name, p.Name)
			}
			seenParam[p.Name] = true
			if p.Desc == "" {
				t.Errorf("%s: parameter %q has no description", spec.Name, p.Name)
			}
			if p.Kind == 0 {
				t.Errorf("%s: parameter %q has no declared type", spec.Name, p.Name)
			}
			if p.positional() {
				positionals++
			}
		}
		if positionals > 1 {
			t.Errorf("%s: %d positional parameters declared, at most 1 is supported", spec.Name, positionals)
		}

		seenAction := map[string]bool{}
		for _, a := range spec.Actions {
			if seenAction[a.Name] {
				t.Errorf("%s: duplicate action %q", spec.Name, a.Name)
			}
			seenAction[a.Name] = true
			if len(a.Argv) == 0 {
				t.Errorf("%s: action %q has an empty argv", spec.Name, a.Name)
			}
			if a.Desc == "" {
				t.Errorf("%s: action %q has no description", spec.Name, a.Name)
			}
			if a.Pos != "" {
				p, ok := spec.param(a.Pos)
				if !ok {
					t.Errorf("%s: action %q names positional %q, which the tool does not declare", spec.Name, a.Name, a.Pos)
				} else if !p.positional() {
					t.Errorf("%s: action %q uses %q as a positional, but it maps to flag --%s", spec.Name, a.Name, a.Pos, p.Flag)
				}
			}
			for _, f := range append(append([]string{}, a.Flags...), a.Required...) {
				p, ok := spec.param(f)
				if !ok {
					t.Errorf("%s: action %q allows parameter %q, which the tool does not declare", spec.Name, a.Name, f)
					continue
				}
				if p.positional() {
					t.Errorf("%s: action %q lists positional %q as a flag", spec.Name, a.Name, f)
				}
			}
		}
	}
}

// TestNoToolEmitsABlockedFlag is the second layer under the per-action
// allowlist: --db above all must never be settable by a caller, because the
// SQL Server instance behind DSR_V6 hosts 72 databases and only one of them is
// DSR's.
func TestNoToolEmitsABlockedFlag(t *testing.T) {
	for _, spec := range specs {
		for _, p := range spec.Params {
			if p.positional() {
				continue
			}
			if cobratree.BlockedFlags[p.Flag] {
				t.Errorf("%s: parameter %q maps to blocked root flag --%s", spec.Name, p.Name, p.Flag)
			}
		}
	}
}

// TestAdvertisedSchemaMatchesTheTable proves a client is told exactly what the
// server accepts: the JSON schema properties are the declared parameters plus
// `action`, no more and no less.
func TestAdvertisedSchemaMatchesTheTable(t *testing.T) {
	s := NewServer()
	tools := s.MCPServer().ListTools()

	for _, spec := range specs {
		st, ok := tools[spec.Name]
		if !ok {
			t.Fatalf("tool %s is not registered", spec.Name)
		}
		props := st.Tool.InputSchema.Properties

		want := map[string]bool{}
		if len(spec.Actions) > 0 {
			want["action"] = true
		}
		for _, p := range spec.Params {
			want[p.Name] = true
		}
		for name := range props {
			if !want[name] {
				t.Errorf("%s advertises property %q that the table does not declare", spec.Name, name)
			}
		}
		for name := range want {
			if _, ok := props[name]; !ok {
				t.Errorf("%s declares parameter %q but does not advertise it", spec.Name, name)
			}
		}
	}
}

// --- argv construction -------------------------------------------------

func mustArgv(t *testing.T, tool string, args map[string]any) []string {
	t.Helper()
	spec := specByName(t, tool)
	vals, err := spec.decode(args)
	if err != nil {
		t.Fatalf("%s decode(%v): %v", tool, args, err)
	}
	argv, err := buildArgv(spec, args, vals)
	if err != nil {
		t.Fatalf("%s buildArgv(%v): %v", tool, args, err)
	}
	return argv
}

func wantErr(t *testing.T, tool string, args map[string]any, mustContain string) {
	t.Helper()
	spec := specByName(t, tool)
	vals, err := spec.decode(args)
	if err == nil {
		_, err = buildArgv(spec, args, vals)
	}
	if err == nil {
		t.Fatalf("%s(%v) was accepted; expected an error mentioning %q", tool, args, mustContain)
	}
	if !strings.Contains(err.Error(), mustContain) {
		t.Fatalf("%s(%v) error = %q, want it to mention %q", tool, args, err, mustContain)
	}
}

func specByName(t *testing.T, name string) *toolSpec {
	t.Helper()
	for _, s := range specs {
		if s.Name == name {
			return s
		}
	}
	t.Fatalf("no tool named %q", name)
	return nil
}

func TestArgvIsALiteralCommandPlusAllowedFlags(t *testing.T) {
	cases := []struct {
		tool string
		args map[string]any
		want []string
	}{
		{"dsr_doctor", map[string]any{}, []string{"doctor", "--json"}},
		{"dsr_query", map[string]any{"sql": "SELECT TOP 3 * FROM tbl_roles"},
			[]string{"query", "SELECT TOP 3 * FROM tbl_roles", "--limit", "200", "--json"}},
		{"dsr_query", map[string]any{"sql": "SELECT 1", "limit": float64(5)},
			[]string{"query", "SELECT 1", "--limit", "5", "--json"}},
		{"dsr_schema", map[string]any{"action": "tables", "min_rows": float64(1)},
			[]string{"schema", "tables", "--min-rows", "1", "--limit", "200", "--json"}},
		{"dsr_schema", map[string]any{"action": "count", "table": "tbl_roles", "where": "1=0"},
			[]string{"count", "tbl_roles", "--where", "1=0", "--json"}},
		{"dsr_retailers", map[string]any{"action": "get", "id": float64(4210)},
			[]string{"retailers", "get", "4210", "--json"}},
		{"dsr_retailers", map[string]any{"action": "list", "state": "Punjab", "include_deleted": true},
			[]string{"retailers", "list", "--state", "Punjab", "--include-deleted", "--limit", "200", "--json"}},
		{"dsr_territory", map[string]any{"action": "zones", "state_id": float64(3)},
			[]string{"geography", "zones", "--state", "3", "--limit", "200", "--json"}},
		{"dsr_attendance", map[string]any{"action": "geo_track", "id": float64(77), "from": "2026-07-01", "to": "2026-08-01"},
			[]string{"geo", "track", "77", "--from", "2026-07-01", "--to", "2026-08-01", "--limit", "200", "--json"}},
		{"dsr_sales", map[string]any{"action": "summary", "by": "person", "from": "2026-07-01"},
			[]string{"sales", "summary", "--from", "2026-07-01", "--by", "person", "--limit", "200", "--json"}},
		{"dsr_supply", map[string]any{"action": "primary_orders", "distributor_id": "37"},
			[]string{"primary", "orders", "--distributor", "37", "--limit", "200", "--json"}},
		{"dsr_portal", map[string]any{"action": "item_sale", "month": "July,2026"},
			[]string{"portal", "item-sale", "--month", "July,2026", "--json"}},
	}
	for _, c := range cases {
		got := mustArgv(t, c.tool, c.args)
		if strings.Join(got, "\x00") != strings.Join(c.want, "\x00") {
			t.Errorf("%s(%v)\n got:  %v\n want: %v", c.tool, c.args, got, c.want)
		}
	}
}

// TestFlagsAreScopedToTheirAction is the reason the allowlist is per-action and
// not per-tool: `where` is a raw SQL fragment that only `count` interpolates,
// and it must not be reachable from a domain command that would silently
// ignore it (or worse, accept it).
func TestFlagsAreScopedToTheirAction(t *testing.T) {
	wantErr(t, "dsr_schema", map[string]any{"action": "tables", "where": "1=1"}, "does not apply")
	wantErr(t, "dsr_schema", map[string]any{"action": "peek", "table": "tbl_roles", "where": "1=1"}, "does not apply")
	wantErr(t, "dsr_retailers", map[string]any{"action": "list", "id": float64(1)}, "does not apply")
	wantErr(t, "dsr_sales", map[string]any{"action": "count", "by": "day"}, "does not apply")
	wantErr(t, "dsr_supply", map[string]any{"action": "primary_list", "pending": true}, "does not apply")
}

func TestUnknownAndMistypedParametersAreNamedErrors(t *testing.T) {
	wantErr(t, "dsr_retailers", map[string]any{"action": "list", "stat": "Punjab"}, "unknown parameter")
	wantErr(t, "dsr_retailers", map[string]any{"action": "list", "database": "master"}, "unknown parameter")
	wantErr(t, "dsr_retailers", map[string]any{"action": "list", "db": "master"}, "unknown parameter")
	wantErr(t, "dsr_sales", map[string]any{"action": "visits", "salesperson": "twelve"}, "whole number")
	wantErr(t, "dsr_sales", map[string]any{"action": "summary", "by": "week"}, "must be one of")
	wantErr(t, "dsr_query", map[string]any{"sql": "SELECT 1", "limit": float64(999999)}, "must be <=")
	wantErr(t, "dsr_retailers", map[string]any{"action": "get"}, "missing required parameter")
	wantErr(t, "dsr_portal", map[string]any{"action": "item_sale"}, "missing required parameter")
}

// TestQueryToolRefusesNonReadSQL is the gate that matters most: dsr_query is
// published through a gateway and the connecting SQL login is a sysadmin, so
// the batching bypass (a first-token check accepting "SELECT 1; EXEC ...")
// has to be closed HERE as well as in the database layer.
func TestQueryToolRefusesNonReadSQL(t *testing.T) {
	bad := []string{
		"SELECT 1 AS a; DECLARE @x int = 1",
		"SELECT 1; EXEC xp_cmdshell 'whoami'",
		"UPDATE tbl_roles SET name = 'x'",
		"/* SELECT */ EXEC sp_configure",
		"DROP TABLE tbl_roles",
	}
	for _, q := range bad {
		wantErr(t, "dsr_query", map[string]any{"sql": q}, "refused")
	}
	// The legitimate shapes must still pass, quotes and all.
	for _, q := range []string{
		"SELECT TOP 5 * FROM tbl_retailers WHERE shopName = 'A B'",
		"WITH x AS (SELECT 1 AS n) SELECT * FROM x",
	} {
		mustArgv(t, "dsr_query", map[string]any{"sql": q})
	}
}

// TestWhereFilterRefusesASecondStatement covers the other raw-SQL entry point:
// `dsr count <table> --where` appends its value straight into a WHERE clause.
func TestWhereFilterRefusesASecondStatement(t *testing.T) {
	wantErr(t, "dsr_schema",
		map[string]any{"action": "count", "table": "tbl_roles", "where": "1=0; DECLARE @y int = 1"},
		"refused")
	// A semicolon inside a literal is not a second statement.
	mustArgv(t, "dsr_schema", map[string]any{"action": "count", "table": "tbl_roles", "where": "shopName = 'a;b'"})
}

// --- end-to-end through a stub CLI -------------------------------------

// TestHandlerShellsOutWithTheExactArgv drives a real tool handler against a
// stub binary that echoes its own arguments, proving the argv the table
// describes is the argv the child process actually receives — including the
// SQL positional surviving as ONE argument with its quotes and spaces intact,
// which is exactly what the reference implementation's SplitShellArgs would
// have destroyed.
func TestHandlerShellsOutWithTheExactArgv(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("stub CLI is a POSIX shell script")
	}
	dir := t.TempDir()
	stub := filepath.Join(dir, "stub-dsr")
	script := "#!/bin/sh\n" +
		"printf '['\n" +
		"sep=''\n" +
		"for a in \"$@\"; do printf '%s\"%s\"' \"$sep\" \"$a\"; sep=','; done\n" +
		"printf ']\\n'\n"
	if err := os.WriteFile(stub, []byte(script), 0o755); err != nil {
		t.Fatalf("write stub: %v", err)
	}

	s := NewServer()
	s.cliPath = func() (string, error) { return stub, nil }

	call := func(tool string, args map[string]any) []string {
		t.Helper()
		spec := specByName(t, tool)
		res, err := s.handlerFor(spec)(context.Background(), mcplib.CallToolRequest{
			Params: mcplib.CallToolParams{Name: tool, Arguments: args},
		})
		if err != nil {
			t.Fatalf("%s handler error: %v", tool, err)
		}
		if res.IsError {
			t.Fatalf("%s returned a tool error: %v", tool, res.Content)
		}
		text, ok := res.Content[0].(mcplib.TextContent)
		if !ok {
			t.Fatalf("%s returned %T, want TextContent", tool, res.Content[0])
		}
		var got []string
		if err := json.Unmarshal([]byte(strings.TrimSpace(text.Text)), &got); err != nil {
			t.Fatalf("%s stub output %q: %v", tool, text.Text, err)
		}
		return got
	}

	sql := "SELECT TOP 2 shopName FROM tbl_retailers WHERE shopName = 'A B' -- note"
	got := call("dsr_query", map[string]any{"sql": sql})
	want := []string{"query", sql, "--limit", "200", "--json"}
	if fmt.Sprint(got) != fmt.Sprint(want) {
		t.Errorf("dsr_query argv\n got:  %q\n want: %q", got, want)
	}

	got = call("dsr_salespersons", map[string]any{"action": "subordinates", "id": float64(12)})
	want = []string{"salespersons", "subordinates", "12", "--limit", "200", "--json"}
	if fmt.Sprint(got) != fmt.Sprint(want) {
		t.Errorf("dsr_salespersons argv\n got:  %q\n want: %q", got, want)
	}
}
