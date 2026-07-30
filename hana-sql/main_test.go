package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// These exercise everything the CLI does BEFORE it needs a database: argument
// resolution, the read-only guard, the exit codes, and — the one that matters
// for the new surface — that `mcp` is recognised as a subcommand rather than
// swallowed as a positional SQL argument.
//
// HANA is not reachable from a developer laptop, so anything past the
// connection is covered by internal/hana's fake-driver tests and by the
// opt-in live suite.

func runCLI(t *testing.T, stdin string, argv ...string) (code int, stdout, stderr string) {
	t.Helper()
	var out, errb bytes.Buffer
	code = run(argv, ioStreams{in: strings.NewReader(stdin), out: &out, err: &errb})
	return code, out.String(), errb.String()
}

// A dead-end env path so nothing can accidentally dial: the guard must refuse
// before the credentials are even read, which is the point of the assertions
// on stderr below.
const noEnv = "/nonexistent/hana-sql-test/hana.env"

func TestCLIRefusesWrites(t *testing.T) {
	cases := []struct {
		name, sql, wantIn string
	}{
		{"update", `UPDATE "JIVO_OIL_HANADB"."OCRD" SET "Balance" = 0`, `got "UPDATE"`},
		{"update_inside_select", `SELECT * FROM "JIVO_OIL_HANADB"."OCRD" FOR UPDATE`, `banned keyword "UPDATE"`},
		{"delete", `DELETE FROM "JIVO_OIL_HANADB"."OINV"`, "only SELECT / WITH / EXPLAIN are allowed"},
		{"stacked", `SELECT 1 FROM DUMMY; DROP TABLE T`, "multiple statements are not allowed"},
		{"unterminated", `SELECT 'abc FROM DUMMY`, "unterminated string literal"},
		{"call", `CALL "SYS"."SOME_PROC"()`, "only SELECT / WITH / EXPLAIN are allowed"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			code, stdout, stderr := runCLI(t, "", "-env", noEnv, c.sql)
			if code != 1 {
				t.Fatalf("exit = %d, want 1; stderr: %s", code, stderr)
			}
			if stdout != "" {
				t.Fatalf("a refused query printed to stdout: %q", stdout)
			}
			if !strings.HasPrefix(stderr, "REFUSED (read-only layer ") {
				t.Fatalf("stderr = %q, want the layered REFUSED prefix", stderr)
			}
			if !strings.Contains(stderr, c.wantIn) {
				t.Fatalf("stderr = %q, want it to contain %q", stderr, c.wantIn)
			}
		})
	}
}

// The CLI keeps EXPLAIN (CLIPolicy); the MCP does not (MCPPolicy). The split is
// deliberate — EXPLAIN PLAN FOR writes SYS.EXPLAIN_PLAN_TABLE.
func TestCLIAcceptsExplainAndReachesTheCredentialStep(t *testing.T) {
	code, _, stderr := runCLI(t, "", "-env", noEnv, "EXPLAIN PLAN FOR SELECT 1 FROM DUMMY")
	if strings.Contains(stderr, "REFUSED") {
		t.Fatalf("the CLI refused EXPLAIN: %s", stderr)
	}
	if code != 1 || !strings.Contains(stderr, noEnv) {
		t.Fatalf("exit=%d stderr=%q; want the credential-file error, i.e. the guard let it through", code, stderr)
	}
}

func TestCLIInvocationForms(t *testing.T) {
	dir := t.TempDir()
	sqlFile := filepath.Join(dir, "q.sql")
	if err := os.WriteFile(sqlFile, []byte("-- a comment\nSELECT 1 FROM DUMMY\n"), 0o600); err != nil {
		t.Fatal(err)
	}

	// All four forms must get past the guard and fail only at the credentials,
	// proving the SQL was resolved from the right place.
	forms := []struct {
		name  string
		stdin string
		argv  []string
	}{
		{"argument", "", []string{"-env", noEnv, "SELECT 1 FROM DUMMY"}},
		{"file", "", []string{"-env", noEnv, "-f", sqlFile}},
		{"stdin", "SELECT 1 FROM DUMMY\n", []string{"-env", noEnv}},
		{"csv", "", []string{"-env", noEnv, "-csv", "SELECT 1 FROM DUMMY"}},
	}
	for _, f := range forms {
		t.Run(f.name, func(t *testing.T) {
			code, _, stderr := runCLI(t, f.stdin, f.argv...)
			if strings.Contains(stderr, "REFUSED") {
				t.Fatalf("form %s was refused: %s", f.name, stderr)
			}
			if code != 1 || !strings.Contains(stderr, "cannot read credentials") {
				t.Fatalf("form %s: exit=%d stderr=%q, want the credential error", f.name, code, stderr)
			}
		})
	}
}

func TestCLIEmptyAndMissingInputs(t *testing.T) {
	code, _, stderr := runCLI(t, "", "-env", noEnv)
	if code != 1 || !strings.Contains(stderr, "no SQL provided") {
		t.Fatalf("empty stdin: exit=%d stderr=%q", code, stderr)
	}

	code, _, stderr = runCLI(t, "", "-env", noEnv, "-f", filepath.Join(t.TempDir(), "missing.sql"))
	if code != 1 || !strings.Contains(stderr, "read sql file") {
		t.Fatalf("missing -f file: exit=%d stderr=%q", code, stderr)
	}
}

// --- the mcp subcommand ---------------------------------------------------

// argv[1] == "mcp" must be seen BEFORE flag parsing. If it were not, `hana-sql
// mcp` would be treated as a SQL string and refused by the guard.
func TestMCPSubcommandIsDetectedBeforeFlagParsing(t *testing.T) {
	code, stdout, stderr := runCLI(t, "", "mcp", "--transport", "nonsense")
	if strings.Contains(stderr, "REFUSED") {
		t.Fatalf("`mcp` was parsed as SQL: %s", stderr)
	}
	if code != 1 || !strings.Contains(stderr, `unknown --transport "nonsense"`) {
		t.Fatalf("exit=%d stdout=%q stderr=%q, want the transport error", code, stdout, stderr)
	}
}

// The MCP server must start and answer even when HANA is unreachable: a dead
// reverse tunnel has to degrade the backend, not crash-loop the container.
func TestMCPStdioServesWithNoDatabase(t *testing.T) {
	in := strings.Join([]string{
		`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}`,
		`{"jsonrpc":"2.0","id":2,"method":"tools/list"}`,
		`{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hana_query","arguments":{"sql":"SELECT 1 FROM DUMMY","company":"Mart"}}}`,
	}, "\n") + "\n"

	var out, errb bytes.Buffer
	code := run([]string{"mcp", "-env", noEnv, "-quiet"},
		ioStreams{in: strings.NewReader(in), out: &out, err: &errb})
	if code != 0 {
		t.Fatalf("exit = %d; stderr: %s", code, errb.String())
	}
	if !strings.Contains(errb.String(), "WARNING") {
		t.Fatalf("a missing credential file should be warned about on stderr, not fatal; stderr: %q", errb.String())
	}

	lines := strings.Split(strings.TrimSpace(out.String()), "\n")
	if len(lines) != 3 {
		t.Fatalf("got %d responses, want 3:\n%s", len(lines), out.String())
	}

	var list map[string]any
	if err := json.Unmarshal([]byte(lines[1]), &list); err != nil {
		t.Fatalf("tools/list is not JSON: %v", err)
	}
	tools := list["result"].(map[string]any)["tools"].([]any)
	var names []string
	for _, tl := range tools {
		names = append(names, tl.(map[string]any)["name"].(string))
	}
	want := "hana_query,hana_tables,hana_columns,hana_doctor"
	if strings.Join(names, ",") != want {
		t.Fatalf("tools = %v, want %s", names, want)
	}

	// The unknown `company` argument must be refused, not silently discarded —
	// and refused before any connection is attempted.
	var call map[string]any
	json.Unmarshal([]byte(lines[2]), &call)
	res := call["result"].(map[string]any)
	if isErr, _ := res["isError"].(bool); !isErr {
		t.Fatalf("an unrecognised `company` argument was accepted: %s", lines[2])
	}
	text := res["content"].([]any)[0].(map[string]any)["text"].(string)
	if !strings.Contains(text, "company") || !strings.Contains(text, "refusing rather than ignoring") {
		t.Fatalf("text = %q", text)
	}
}

// Stdout must carry protocol only. A log line on stdout corrupts the stream.
func TestMCPStdioKeepsLogsOffStdout(t *testing.T) {
	var out, errb bytes.Buffer
	run([]string{"mcp", "-env", noEnv},
		ioStreams{in: strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}` + "\n"), out: &out, err: &errb})
	for _, line := range strings.Split(strings.TrimSpace(out.String()), "\n") {
		if line == "" {
			continue
		}
		var m map[string]any
		if err := json.Unmarshal([]byte(line), &m); err != nil {
			t.Fatalf("non-JSON line on stdout (%q): %v", line, err)
		}
	}
	if !strings.Contains(errb.String(), "ready on stdio") {
		t.Fatalf("the readiness log should be on stderr; stderr = %q", errb.String())
	}
}
