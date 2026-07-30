package mcpsrv

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"testing"
	"time"

	"hana-sql/internal/config"
	"hana-sql/internal/hana"
)

// dispatch runs one tool with DB == nil, so nothing here can reach a database:
// every case below must be decided by argument validation alone.
func dispatch(t *testing.T, tool, args string) (string, bool) {
	t.Helper()
	return testServer().Dispatch(context.Background(), tool, json.RawMessage(args))
}

func TestToolNamesAndOrder(t *testing.T) {
	defs := testServer().ToolDefs()
	if len(defs) != len(ToolNames) {
		t.Fatalf("ToolDefs() has %d tools, ToolNames has %d", len(defs), len(ToolNames))
	}
	for i, want := range ToolNames {
		if got := defs[i]["name"]; got != want {
			t.Fatalf("tool[%d] = %v, want %q", i, got, want)
		}
	}
}

// D2 — SILENT_PARAM_DISCARD, the benchmark's highest-severity defect. A tool
// that accepts `company` and quietly ignores it can present Oil's number as
// Beverages'. Both halves of the fix are asserted: the schema forbids extra
// properties, and the decoder rejects them.
func TestUnknownArgumentsAreRefusedNotIgnored(t *testing.T) {
	for _, def := range testServer().ToolDefs() {
		schema, _ := def["inputSchema"].(map[string]any)
		if ap, ok := schema["additionalProperties"].(bool); !ok || ap {
			t.Fatalf("tool %v advertises additionalProperties = %v, want false", def["name"], schema["additionalProperties"])
		}
	}

	cases := []struct {
		tool, args, wantIn string
	}{
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","company":"JIVO_BEVERAGES_HANADB"}`, "company"},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","companyDB":"Beverages"}`, "companyDB"},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","database":"Mart"}`, "database"},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","schema":"JIVO_MART_HANADB"}`, "schema"},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","top":50}`, "top"},
		{"hana_tables", `{"company":"Mart"}`, "company"},
		{"hana_columns", `{"schema":"JIVO_OIL_HANADB","table":"OINV","db":"x"}`, "db"},
		{"hana_doctor", `{"company":"Oil"}`, "company"},
	}
	for _, c := range cases {
		t.Run(c.tool+"_"+c.wantIn, func(t *testing.T) {
			text, isErr := dispatch(t, c.tool, c.args)
			if !isErr {
				t.Fatalf("%s accepted an unrecognised argument and returned %q — that is how Oil's figure gets presented as another company's", c.tool, text)
			}
			if !strings.Contains(text, c.wantIn) {
				t.Fatalf("error text %q does not name the offending argument %q", text, c.wantIn)
			}
			if !strings.Contains(text, "refusing rather than ignoring") {
				t.Fatalf("error text %q should say plainly that the argument was refused, not ignored", text)
			}
		})
	}
}

// The company-shaped ones additionally get told how to reach another company.
func TestCompanyArgumentGetsTheQualifiedNameHint(t *testing.T) {
	for _, arg := range []string{"company", "companyDB", "database", "db", "schema"} {
		text, isErr := dispatch(t, "hana_query", fmt.Sprintf(`{"sql":"SELECT 1 FROM DUMMY","%s":"x"}`, arg))
		if !isErr {
			t.Fatalf("%s was accepted", arg)
		}
		if !strings.Contains(text, "JIVO_BEVERAGES_HANADB") {
			t.Fatalf("the %s refusal should show how to reach another company by qualifying the table name; got %q", arg, text)
		}
	}
}

func TestMissingRequiredArguments(t *testing.T) {
	cases := []struct{ tool, args, wantIn string }{
		{"hana_query", `{}`, "missing required argument: sql"},
		{"hana_query", `{"sql":"   "}`, "missing required argument: sql"},
		{"hana_columns", `{"table":"OINV"}`, "missing required argument: schema"},
		{"hana_columns", `{"schema":"JIVO_OIL_HANADB"}`, "missing required argument: table"},
		{"", `{}`, "missing tool name"},
	}
	for _, c := range cases {
		text, isErr := dispatch(t, c.tool, c.args)
		if !isErr {
			t.Fatalf("%s(%s) = %q, want an error", c.tool, c.args, text)
		}
		if !strings.Contains(text, c.wantIn) {
			t.Fatalf("%s(%s) error = %q, want it to contain %q", c.tool, c.args, text, c.wantIn)
		}
	}
	// hana_columns names the three schemas so the model does not have to guess.
	text, _ := dispatch(t, "hana_columns", `{"table":"OINV"}`)
	for _, s := range hana.Schemas {
		if !strings.Contains(text, s) {
			t.Fatalf("the missing-schema error should list %s; got %q", s, text)
		}
	}
}

func TestNegativeCapsRejected(t *testing.T) {
	for _, args := range []string{
		`{"sql":"SELECT 1 FROM DUMMY","max_rows":-1}`,
		`{"sql":"SELECT 1 FROM DUMMY","timeout_ms":-5}`,
	} {
		text, isErr := dispatch(t, "hana_query", args)
		if !isErr || !strings.Contains(text, "must not be negative") {
			t.Fatalf("hana_query(%s) = (%q, %v), want a negative-value error", args, text, isErr)
		}
	}
}

func TestRequiredListsMatchTheValidator(t *testing.T) {
	want := map[string][]string{
		"hana_query":   {"sql"},
		"hana_columns": {"schema", "table"},
	}
	for _, def := range testServer().ToolDefs() {
		name, _ := def["name"].(string)
		schema, _ := def["inputSchema"].(map[string]any)
		req, _ := schema["required"].([]string)
		exp, ok := want[name]
		if !ok {
			if len(req) != 0 {
				t.Fatalf("%s advertises required = %v, want none", name, req)
			}
			continue
		}
		if strings.Join(req, ",") != strings.Join(exp, ",") {
			t.Fatalf("%s required = %v, want %v", name, req, exp)
		}
	}
}

// The guard's refusal must survive all the way out to the tool result, naming
// the layer that refused, so the model can correct itself instead of retrying.
func TestGuardRefusalReachesTheCallerWithNoDB(t *testing.T) {
	// A write is refused by internal/guard before internal/hana is consulted,
	// which is why this works with DB == nil.
	srv := &Server{Log: nil, Now: time.Now}
	db := hana.New(&config.Config{Host: "127.0.0.1", Port: "1", User: "u", Password: "p"},
		hana.Options{Limits: hana.Limits{Timeout: time.Second}})
	srv.DB = db
	defer db.Close()

	text, isErr := srv.Dispatch(context.Background(), "hana_query",
		json.RawMessage(`{"sql":"UPDATE \"JIVO_OIL_HANADB\".\"OCRD\" SET \"Balance\" = 0"}`))
	if !isErr {
		t.Fatalf("a write was not reported as an error: %q", text)
	}
	if !strings.HasPrefix(text, "REFUSED (read-only layer ") {
		t.Fatalf("refusal text = %q, want the layered REFUSED prefix", text)
	}
	if !strings.Contains(text, "UPDATE") {
		t.Fatalf("refusal text = %q, want it to name the offending keyword", text)
	}
}

// --- the response envelope ----------------------------------------------------

func TestEnvelopeShape(t *testing.T) {
	fixed := time.Date(2026, 7, 30, 18, 22, 41, 0, time.FixedZone("IST", 5*3600+1800))
	srv := &Server{Now: func() time.Time { return fixed }}
	res := &hana.Result{
		Columns:   []hana.Column{{Name: "TURNOVER", Type: "DECIMAL"}},
		Rows:      []map[string]any{{"TURNOVER": "1368965497.2500"}},
		RowCount:  1,
		Truncated: false,
		Elapsed:   412 * time.Millisecond,
	}
	text, isErr := srv.envelope(res, nil, 1000)
	if isErr {
		t.Fatalf("envelope reported an error: %s", text)
	}
	var e map[string]any
	if err := json.Unmarshal([]byte(text), &e); err != nil {
		t.Fatalf("envelope is not JSON: %v\n%s", err, text)
	}
	for _, k := range []string{"as_of", "as_of_source", "elapsed_ms", "row_count", "max_rows", "truncated", "columns", "rows"} {
		if _, ok := e[k]; !ok {
			t.Fatalf("envelope is missing %q: %s", k, text)
		}
	}
	if e["as_of"] != "2026-07-30T18:22:41+05:30" {
		t.Fatalf("as_of = %v, want the RFC3339 host clock", e["as_of"])
	}
	if e["as_of_source"] != "mcp-host-clock" {
		t.Fatalf("as_of_source = %v", e["as_of_source"])
	}
	if e["elapsed_ms"].(float64) != 412 {
		t.Fatalf("elapsed_ms = %v, want 412", e["elapsed_ms"])
	}
	if e["max_rows"].(float64) != 1000 {
		t.Fatalf("max_rows = %v, want the cap in force", e["max_rows"])
	}
	if _, present := e["note"]; present {
		t.Fatalf("note must be omitted when there is nothing to say: %s", text)
	}
	// A DECIMAL stays an exact string, never a JSON number.
	rows := e["rows"].([]any)
	if _, ok := rows[0].(map[string]any)["TURNOVER"].(string); !ok {
		t.Fatalf("TURNOVER came back as %T; a money figure must be an exact string", rows[0].(map[string]any)["TURNOVER"])
	}
}

func TestEnvelopeCarriesTruncationNote(t *testing.T) {
	srv := &Server{Now: time.Now}
	res := &hana.Result{RowCount: 1000, Truncated: true, Note: "row cap reached (1000 rows); aggregate server-side"}
	text, _ := srv.envelope(res, nil, 1000)
	var e map[string]any
	json.Unmarshal([]byte(text), &e)
	if e["truncated"] != true {
		t.Fatalf("truncated = %v, want true", e["truncated"])
	}
	if !strings.Contains(e["note"].(string), "aggregate server-side") {
		t.Fatalf("note = %v", e["note"])
	}
}

// --- the crib sheet (golden) ---------------------------------------------------

// The facts in the tool descriptions are the model's only guardrail against the
// field-name confusion the benchmark measured (D7). This test is what stops them
// rotting silently.
func TestDescriptionsCarryFacts(t *testing.T) {
	defs := testServer().ToolDefs()
	byName := map[string]string{}
	for _, d := range defs {
		name, _ := d["name"].(string)
		desc, _ := d["description"].(string)
		if strings.TrimSpace(desc) == "" {
			t.Fatalf("tool %q has no description", name)
		}
		byName[name] = desc
	}

	// Every tool states the read-only rule.
	for name, desc := range byName {
		if !strings.Contains(desc, "READ-ONLY") {
			t.Errorf("%s does not state that the server is read-only", name)
		}
	}

	q := byName["hana_query"]
	must := []string{
		"JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB",
		`ROUND(TO_DOUBLE(SUM("DocTotal" - "VatSum")), 2)`,
		`"CANCELED" = 'N'`,
		// Verified live 2026-07-30: ORCT/OVPM spell the same flag "Canceled".
		// Benchmark defect D7 — a wrong spelling costs a whole round trip.
		`"Canceled" = 'N'`,
		// Also verified live, and the opposite of the Service Layer's rule,
		// which is exactly why it has to be said out loud.
		"ORCT / OVPM DO have",
		`"DocTotal"`, `"VatSum"`, `"DocDate"`,
		`"CreditLine"`, `"OnHand"`, `"InvntItem"`,
		"TIMESTAMP, not DATE",
		"OCRD", "OINV", "INV1", "ORIN", "RIN1", "ORDR", "RDR1", "OPOR", "POR1",
		"OITM", "OITW", "OJDT", "JDT1", "ORCT", "OVPM",
		`"RefDate"`,
		"POSITIVE = DEBIT",
		"AGGREGATE SERVER-SIDE",
		"crore",
		"1000", // the max_rows in force
		"1m0s", // the statement timeout in force
	}
	for _, m := range must {
		if !strings.Contains(q, m) {
			t.Errorf("hana_query's description is missing the load-bearing fact %q", m)
		}
	}

	// The three short descriptions must stay short: tools/list already carries
	// ~75 tools through the gateway.
	for _, name := range []string{"hana_tables", "hana_columns", "hana_doctor"} {
		if n := len(byName[name]); n > 600 {
			t.Errorf("%s's description is %d chars; keep the crib sheet in hana_query only", name, n)
		}
	}
	if len(q) < 1200 {
		t.Errorf("hana_query's description is only %d chars; the crib sheet looks truncated", len(q))
	}
}

// The description must track the caps actually in force, not a hard-coded 1000.
func TestDescriptionReflectsConfiguredCaps(t *testing.T) {
	db := hana.New(&config.Config{Host: "h", Port: "1", User: "u", Password: "p"},
		hana.Options{Limits: hana.Limits{MaxRows: 37, Timeout: 9 * time.Second}})
	defer db.Close()
	srv := &Server{DB: db}
	desc, _ := srv.ToolDefs()[0]["description"].(string)
	if !strings.Contains(desc, "37 rows") {
		t.Fatalf("description does not carry the configured row cap of 37:\n%s", desc)
	}
	if !strings.Contains(desc, "9s") {
		t.Fatalf("description does not carry the configured timeout of 9s")
	}
}

// --- credentials --------------------------------------------------------------

// A sentinel password fed through the real config must never appear in any tool
// output, including hana_doctor's report and a connection error.
func TestNoCredentialEverLeaves(t *testing.T) {
	const sentinel = "P@ssw0rd-SENTINEL-do-not-print"
	cfg := &config.Config{Host: "127.0.0.1", Port: "1", User: "ZIA", Password: sentinel, EnvFile: "/opt/jivo-mcp/env/hana/hana.env"}
	db := hana.New(cfg, hana.Options{Limits: hana.Limits{Timeout: 2 * time.Second}})
	defer db.Close()
	srv := &Server{DB: db, Now: time.Now}

	var outputs []string
	for _, c := range []struct{ tool, args string }{
		{"hana_doctor", `{}`},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY"}`},
		{"hana_tables", `{}`},
		{"hana_columns", `{"schema":"JIVO_OIL_HANADB","table":"OINV"}`},
	} {
		text, _ := srv.Dispatch(context.Background(), c.tool, json.RawMessage(c.args))
		outputs = append(outputs, c.tool+": "+text)
	}
	all := strings.Join(outputs, "\n")
	if strings.Contains(all, sentinel) {
		t.Fatalf("a credential value appeared in tool output:\n%s", all)
	}
	if !strings.Contains(outputs[0], `"password":"**** (set)"`) {
		t.Fatalf("hana_doctor should report the password as masked-but-present; got %s", outputs[0])
	}
	if !strings.Contains(outputs[0], "/opt/jivo-mcp/env/hana/hana.env") {
		t.Fatalf("hana_doctor should name the env FILE (a path is safe, a value is not); got %s", outputs[0])
	}
}

// hana_doctor never probes the read-only backstop with a write. The one
// write-attempt probe in this project is a manual, offline verification.
func TestDoctorReportsTheReadOnlyPostureWithoutWriting(t *testing.T) {
	cfg := &config.Config{Host: "127.0.0.1", Port: "1", User: "ZIA", Password: "x"}
	db := hana.New(cfg, hana.Options{Limits: hana.Limits{MaxRows: 1000, Timeout: time.Second}, MaxConcurrent: 2})
	defer db.Close()
	srv := &Server{DB: db, Now: time.Now}

	text, isErr := srv.Dispatch(context.Background(), "hana_doctor", json.RawMessage(`{}`))
	if !isErr {
		t.Fatal("doctor should report not-ok when HANA is unreachable")
	}
	var rep map[string]any
	if err := json.Unmarshal([]byte(text), &rep); err != nil {
		t.Fatalf("doctor output is not JSON: %v\n%s", err, text)
	}
	ro, _ := rep["read_only"].(map[string]any)
	if ro == nil {
		t.Fatalf("doctor has no read_only block: %s", text)
	}
	if ro["transaction"] != "READ ONLY, always rolled back" {
		t.Fatalf("read_only.transaction = %v", ro["transaction"])
	}
	if n, _ := ro["banned_tokens"].(float64); n < 25 {
		t.Fatalf("read_only.banned_tokens = %v, suspiciously low", ro["banned_tokens"])
	}
	allow, _ := ro["first_token_allowlist"].([]any)
	if len(allow) != 2 || allow[0] != "SELECT" || allow[1] != "WITH" {
		t.Fatalf("first_token_allowlist = %v, want [SELECT WITH] (EXPLAIN writes SYS.EXPLAIN_PLAN_TABLE)", allow)
	}
	// The container-vs-host address trap is the most likely deploy failure, so
	// the hint has to be right there when TCP fails.
	if !strings.Contains(text, "172.16.1.1:30015") {
		t.Fatalf("the tcp failure hint should name the in-container address; got %s", text)
	}
	// And it must not have tried to write anything.
	if strings.Contains(strings.ToUpper(text), "UPDATE ") || strings.Contains(strings.ToUpper(text), "INSERT ") {
		t.Fatalf("doctor output mentions a write statement: %s", text)
	}
}

// --- stdio transport ------------------------------------------------------------

func TestServeStdioRoundTrip(t *testing.T) {
	in := strings.NewReader(strings.Join([]string{
		`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}`,
		`{"jsonrpc":"2.0","method":"notifications/initialized"}`,
		``,           // a blank line must be skipped, not fatal
		`{not json}`, // a malformed line must not kill the loop
		`{"jsonrpc":"2.0","id":2,"method":"tools/list"}`,
	}, "\n") + "\n")

	var out bytes.Buffer
	srv := &Server{Log: nil}
	if err := srv.ServeStdio(in, &out); err != nil {
		t.Fatalf("ServeStdio: %v", err)
	}

	lines := strings.Split(strings.TrimSpace(out.String()), "\n")
	if len(lines) != 2 {
		t.Fatalf("got %d response lines, want 2 (initialize + tools/list); output:\n%s", len(lines), out.String())
	}
	var initResp map[string]any
	json.Unmarshal([]byte(lines[0]), &initResp)
	if initResp["id"].(float64) != 1 {
		t.Fatalf("first response id = %v, want 1", initResp["id"])
	}
	var listResp map[string]any
	json.Unmarshal([]byte(lines[1]), &listResp)
	result := listResp["result"].(map[string]any)
	if len(result["tools"].([]any)) != 4 {
		t.Fatalf("tools/list over stdio returned %d tools, want 4", len(result["tools"].([]any)))
	}
}
