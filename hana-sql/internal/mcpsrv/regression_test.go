package mcpsrv

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"hana-sql/internal/config"
	"hana-sql/internal/hana"
)

// Regression tests for the reviewer/tester findings against internal/mcpsrv.
// Each names the defect it locks down and the live evidence for it.

// --- HTTP transport: a web page must not be able to drive production HANA ------

// FINDING (P2, CONFIRMED LIVE): the HTTP transport validated no Origin header,
// no Content-Type, and had no auth of any kind. A POST with
// `Origin: https://evil.example` and `Content-Type: text/plain` returned HTTP 200
// with a full hana_doctor report. A text/plain POST is a CORS *simple* request
// (no preflight), so any web page a JIVO machine visits could drive
// 127.0.0.1:7706/mcp blind against production HANA; DNS rebinding makes the
// responses readable. MCP.md offered loopback binding as the mitigation, but
// loopback does not stop a browser, and the MCP spec explicitly requires Origin
// validation for locally-bound HTTP servers.
func TestHTTPRefusesABrowserOrigin(t *testing.T) {
	h := testServer().HTTPHandler()
	for _, origin := range []string{
		"https://evil.example",
		"http://evil.example",
		"null",
		"http://localhost:3000", // even a friendly-looking one: not allowed by default
	} {
		req := httptest.NewRequest(http.MethodPost, "/mcp",
			strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"hana_doctor","arguments":{}}}`))
		req.Host = "127.0.0.1:7706"
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Origin", origin)
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusForbidden {
			t.Fatalf("Origin %q got HTTP %d (body %.200s), want 403 — a web page must not reach production HANA",
				origin, rec.Code, rec.Body.String())
		}
		if strings.Contains(rec.Body.String(), "read_only") || strings.Contains(rec.Body.String(), "hana_version") {
			t.Fatalf("the refusal leaked a doctor report: %s", rec.Body.String())
		}
	}
}

// The CORS simple-request path is the one a page can take with no preflight at
// all, so text/plain (and the form encodings) must be refused outright.
func TestHTTPRefusesCORSSimpleContentTypes(t *testing.T) {
	h := testServer().HTTPHandler()
	for _, ct := range []string{
		"text/plain",
		"text/plain;charset=UTF-8",
		"application/x-www-form-urlencoded",
		"multipart/form-data; boundary=x",
		"", // no Content-Type at all
	} {
		req := httptest.NewRequest(http.MethodPost, "/mcp",
			strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"hana_doctor","arguments":{}}}`))
		req.Host = "127.0.0.1:7706"
		if ct != "" {
			req.Header.Set("Content-Type", ct)
		} else {
			req.Header.Del("Content-Type")
		}
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)

		if rec.Code != http.StatusUnsupportedMediaType {
			t.Fatalf("Content-Type %q got HTTP %d, want 415 — text/plain is a CORS simple request a page can send with no preflight",
				ct, rec.Code)
		}
	}

	// application/json (with or without parameters) is the only accepted form.
	for _, ct := range []string{"application/json", "application/json; charset=utf-8", "application/vnd.x+json"} {
		req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
		req.Host = "127.0.0.1:7706"
		req.Header.Set("Content-Type", ct)
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		if rec.Code != http.StatusOK {
			t.Fatalf("Content-Type %q got HTTP %d, want 200; a legitimate MCP client must still work", ct, rec.Code)
		}
	}
}

// The anti-DNS-rebinding half: the browser sends the name it resolved, so an
// attacker name that resolves to 127.0.0.1 is visible in Host.
func TestHTTPRefusesANonLoopbackHost(t *testing.T) {
	h := testServer().HTTPHandler()
	for _, host := range []string{"evil.example", "evil.example:7706", "192.168.1.41:7706", "hana.internal"} {
		req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
		req.Host = host
		req.Header.Set("Content-Type", "application/json")
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		if rec.Code != http.StatusForbidden {
			t.Fatalf("Host %q got HTTP %d, want 403 — a request under a name that is not this loopback server is what DNS rebinding looks like", host, rec.Code)
		}
	}
	for _, host := range []string{"127.0.0.1:7706", "localhost:7706", "127.0.0.1", "localhost", "[::1]:7706"} {
		req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
		req.Host = host
		req.Header.Set("Content-Type", "application/json")
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		if rec.Code != http.StatusOK {
			t.Fatalf("Host %q got HTTP %d, want 200 — the ordinary loopback client must keep working", host, rec.Code)
		}
	}
}

// An operator who fronts the endpoint with a proxy, or reaches it by service
// name inside Docker, has an explicit escape. Nothing is silently permissive.
func TestHTTPAllowlistsAreOptIn(t *testing.T) {
	srv := testServer()
	srv.AllowedOrigins = []string{"https://ops.jivo.internal"}
	srv.AllowedHosts = []string{"hana:7706"}
	h := srv.HTTPHandler()

	req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
	req.Host = "hana:7706"
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Origin", "https://ops.jivo.internal")
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("an explicitly allowed origin/host got HTTP %d: %s", rec.Code, rec.Body.String())
	}

	// A different origin is still refused under the same allowlist.
	req2 := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
	req2.Host = "hana:7706"
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("Origin", "https://evil.example")
	rec2 := httptest.NewRecorder()
	h.ServeHTTP(rec2, req2)
	if rec2.Code != http.StatusForbidden {
		t.Fatalf("an origin outside the allowlist got HTTP %d", rec2.Code)
	}
}

// The optional shared secret, for a deployment that needs more than
// origin/host validation.
func TestHTTPBearerTokenIsEnforcedWhenSet(t *testing.T) {
	srv := testServer()
	srv.AuthToken = "s3cret-token"
	h := srv.HTTPHandler()

	post := func(auth string) int {
		req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
		req.Host = "127.0.0.1:7706"
		req.Header.Set("Content-Type", "application/json")
		if auth != "" {
			req.Header.Set("Authorization", auth)
		}
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		return rec.Code
	}
	if got := post(""); got != http.StatusUnauthorized {
		t.Fatalf("no Authorization header got HTTP %d, want 401", got)
	}
	if got := post("Bearer wrong"); got != http.StatusUnauthorized {
		t.Fatalf("a wrong token got HTTP %d, want 401", got)
	}
	if got := post("Bearer s3cret-token"); got != http.StatusOK {
		t.Fatalf("the correct token got HTTP %d, want 200", got)
	}
	if got := post("bearer s3cret-token"); got != http.StatusOK {
		t.Fatalf("the scheme is case-insensitive per RFC 7235; got HTTP %d", got)
	}
	// And with no token configured, nothing changes for existing clients.
	if rec := postMCP(t, testServer().HTTPHandler(), `{"jsonrpc":"2.0","id":1,"method":"ping"}`); rec.Code != http.StatusOK {
		t.Fatalf("an unauthenticated server refused a plain client: HTTP %d", rec.Code)
	}
}

// --- JSON-RPC batching ---------------------------------------------------------

// FINDING (P3, CONFIRMED LIVE): a JSON-RPC batch (a top-level array) failed
// json.Unmarshal into mcpRequest, was logged to stderr as "parse error: json:
// cannot unmarshal array" and produced NO response, so a client that batched
// hung on stdio and got a hard 400 over HTTP —
// `[{"jsonrpc":"2.0","id":1,"method":"ping"}]` -> 400 -32700. Both advertised
// revisions (2024-11-05, the default, and 2025-03-26) mandate batching.
func TestJSONRPCBatchIsAnswered(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(),
		`[{"jsonrpc":"2.0","id":1,"method":"ping"},{"jsonrpc":"2.0","id":2,"method":"tools/list"}]`)
	if rec.Code != http.StatusOK {
		t.Fatalf("a JSON-RPC batch got HTTP %d: %s", rec.Code, rec.Body.String())
	}
	var out []map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &out); err != nil {
		t.Fatalf("a batch must be answered with an ARRAY of responses: %v\n%s", err, rec.Body.String())
	}
	if len(out) != 2 {
		t.Fatalf("got %d responses for a 2-message batch: %s", len(out), rec.Body.String())
	}
	ids := map[float64]bool{}
	for _, r := range out {
		if r["jsonrpc"] != "2.0" {
			t.Fatalf("batch response is not JSON-RPC 2.0: %v", r)
		}
		ids[r["id"].(float64)] = true
	}
	if !ids[1] || !ids[2] {
		t.Fatalf("batch responses do not carry both ids: %s", rec.Body.String())
	}
}

// A batch of only notifications gets silence, as the spec requires.
func TestJSONRPCNotificationOnlyBatchIsSilent(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(),
		`[{"jsonrpc":"2.0","method":"notifications/initialized"},{"jsonrpc":"2.0","method":"notifications/cancelled"}]`)
	if rec.Code != http.StatusAccepted {
		t.Fatalf("an all-notification batch got HTTP %d (body %q), want 202 with no body", rec.Code, rec.Body.String())
	}
	if rec.Body.Len() != 0 {
		t.Fatalf("body = %q, want empty", rec.Body.String())
	}
}

// An empty array is a malformed batch and must be named as such, not hung on.
func TestJSONRPCEmptyBatchIsAnInvalidRequest(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(), `[]`)
	m := decodeRPC(t, rec)
	rpcErr, _ := m["error"].(map[string]any)
	if rpcErr == nil {
		t.Fatalf("an empty batch produced no error object: %s", rec.Body.String())
	}
	if code, _ := rpcErr["code"].(float64); code != -32600 {
		t.Fatalf("error.code = %v, want -32600 (invalid request)", rpcErr["code"])
	}
}

// Stdio parity: the same batch over the stdio transport gets one line back.
func TestJSONRPCBatchOverStdio(t *testing.T) {
	var out strings.Builder
	srv := &Server{Log: nil}
	if err := srv.ServeStdio(strings.NewReader(
		`[{"jsonrpc":"2.0","id":1,"method":"ping"},{"jsonrpc":"2.0","id":2,"method":"ping"}]`+"\n"), &out); err != nil {
		t.Fatalf("ServeStdio: %v", err)
	}
	line := strings.TrimSpace(out.String())
	if line == "" {
		t.Fatal("a batched client got NO response and hung — this is the defect")
	}
	var arr []map[string]any
	if err := json.Unmarshal([]byte(line), &arr); err != nil || len(arr) != 2 {
		t.Fatalf("stdio batch response = %q (err %v), want an array of 2", line, err)
	}
}

// --- protocol negotiation ------------------------------------------------------

// FINDING (P3): initialize echoed any protocolVersion string verbatim —
// "1999-01-01-BOGUS" came back as "1999-01-01-BOGUS" — so version negotiation
// was a no-op and the server advertised compliance with revisions it does not
// implement. It must answer with a version it actually speaks.
func TestInitializeAnswersWithASupportedProtocolVersion(t *testing.T) {
	ask := func(params string) string {
		body := `{"jsonrpc":"2.0","id":1,"method":"initialize"`
		if params != "" {
			body += `,"params":{"protocolVersion":"` + params + `"}`
		}
		body += `}`
		rec := postMCP(t, testServer().HTTPHandler(), body)
		m := decodeRPC(t, rec)
		result, _ := m["result"].(map[string]any)
		pv, _ := result["protocolVersion"].(string)
		return pv
	}

	supported := map[string]bool{}
	for _, v := range SupportedProtocolVersions {
		supported[v] = true
		if got := ask(v); got != v {
			t.Fatalf("initialize(%q) = %q, want the same supported revision back", v, got)
		}
	}
	for _, bogus := range []string{"1999-01-01-BOGUS", "2099-12-31", "", "not-a-date"} {
		got := ask(bogus)
		if !supported[got] {
			t.Fatalf("initialize(%q) answered %q, which this server does not implement — "+
				"the client cannot discover the mismatch, so negotiation is a no-op", bogus, got)
		}
		if got == bogus && bogus != "" {
			t.Fatalf("initialize echoed %q back verbatim", bogus)
		}
	}
	if got := ask(""); got != DefaultProtocolVersion {
		t.Fatalf("initialize with no version = %q, want the default %q", got, DefaultProtocolVersion)
	}
}

// FINDING (P3, cosmetic but stated): the `jsonrpc` version field was not
// validated — {"id":1,"method":"ping"} and {"jsonrpc":"1.0",…} both returned a
// normal 2.0 result.
func TestJSONRPCVersionFieldIsValidated(t *testing.T) {
	// A wrong version is refused, with the id echoed so the client can match it.
	rec := postMCP(t, testServer().HTTPHandler(), `{"jsonrpc":"1.0","id":1,"method":"ping"}`)
	m := decodeRPC(t, rec)
	rpcErr, _ := m["error"].(map[string]any)
	if rpcErr == nil {
		t.Fatalf(`jsonrpc:"1.0" was answered as if it were 2.0: %s`, rec.Body.String())
	}
	if code, _ := rpcErr["code"].(float64); code != -32600 {
		t.Fatalf("error.code = %v, want -32600", rpcErr["code"])
	}
	if !strings.Contains(rpcErr["message"].(string), "2.0") {
		t.Fatalf("message = %v, want it to name the version required", rpcErr["message"])
	}
	// An ABSENT field stays lenient — harmless, and refusing it would break
	// clients that already work.
	rec = postMCP(t, testServer().HTTPHandler(), `{"id":1,"method":"ping"}`)
	m = decodeRPC(t, rec)
	if _, ok := m["result"]; !ok {
		t.Fatalf("an absent jsonrpc field was refused; that is stricter than it needs to be: %s", rec.Body.String())
	}
}

// --- argument handling ---------------------------------------------------------

// FINDING (P3): encoding/json matches keys CASE-INSENSITIVELY, so {"SQL": …} and
// {"MAX_ROWS": 5} were accepted even though the advertised inputSchema says
// additionalProperties:false and lists only sql/max_rows. That inverted the
// stated design at tools.go — "a schema is advice and the decoder is
// enforcement" — by leaving the decoder looser than the schema.
func TestArgumentNamesAreCaseSensitive(t *testing.T) {
	cases := []struct{ tool, args, want string }{
		{"hana_query", `{"SQL":"SELECT 1 FROM DUMMY"}`, "SQL"},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","MAX_ROWS":5}`, "MAX_ROWS"},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","Timeout_MS":5}`, "Timeout_MS"},
		{"hana_tables", `{"SCHEMA":"JIVO_OIL_HANADB"}`, "SCHEMA"},
		{"hana_tables", `{"Like":"O%"}`, "Like"},
		{"hana_columns", `{"schema":"JIVO_OIL_HANADB","TABLE":"OINV"}`, "TABLE"},
	}
	for _, c := range cases {
		t.Run(c.want, func(t *testing.T) {
			text, isErr := dispatch(t, c.tool, c.args)
			if !isErr {
				t.Fatalf("%s accepted %q — the decoder must not be looser than the schema it enforces; got %q", c.tool, c.want, text)
			}
			if !strings.Contains(text, c.want) {
				t.Fatalf("the refusal does not name %q: %s", c.want, text)
			}
			if !strings.Contains(text, "case-sensitive") {
				t.Fatalf("the refusal should say the names are case-sensitive and offer the right one: %s", text)
			}
		})
	}
	// The correctly-spelled names still work (they get as far as the missing DB).
	for _, c := range []struct{ tool, args string }{
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","max_rows":5,"timeout_ms":100}`},
		{"hana_tables", `{"schema":"JIVO_OIL_HANADB","like":"O%","include_views":true,"offset":0,"no_row_counts":true}`},
		{"hana_columns", `{"schema":"JIVO_OIL_HANADB","table":"OINV","like":"Doc%"}`},
	} {
		text, isErr := dispatch(t, c.tool, c.args)
		if isErr && !strings.Contains(text, "no HANA connection") {
			t.Fatalf("%s(%s) was refused on its own arguments: %s", c.tool, c.args, text)
		}
	}
}

// FINDING (P3): a malformed-arguments error leaked the internal Go struct
// definition to the MCP client:
//
//	invalid arguments: json: cannot unmarshal string into Go value of type
//	struct { SQL string "json:\"sql\""; MaxRows int "json:\"max_rows\""; … }
//
// No secret, but it is this program's private shape handed to a model instead of
// an answer about its own request — unlike every other error in this codebase.
func TestArgumentErrorsDoNotLeakGoInternals(t *testing.T) {
	cases := []struct{ tool, args string }{
		{"hana_query", `"not-an-object"`},
		{"hana_query", `[1,2,3]`},
		{"hana_query", `42`},
		{"hana_query", `true`},
		{"hana_query", `{"sql":123}`},
		{"hana_query", `{"sql":"SELECT 1 FROM DUMMY","max_rows":"lots"}`},
		{"hana_tables", `"nope"`},
	}
	for _, c := range cases {
		t.Run(c.args, func(t *testing.T) {
			text, isErr := dispatch(t, c.tool, c.args)
			if !isErr {
				t.Fatalf("%s(%s) was accepted", c.tool, c.args)
			}
			for _, leak := range []string{"Go value of type", "Go struct field", "struct {", `json:\"`, "MaxRows", "TimeoutMS", "IncludeViews"} {
				if strings.Contains(text, leak) {
					t.Fatalf("the error hands the client this program's internals (%q):\n%s", leak, text)
				}
			}
			if !strings.Contains(strings.ToLower(text), "argument") {
				t.Fatalf("the error should be about the caller's arguments: %s", text)
			}
		})
	}
	// The object-shaped refusal names what the caller actually sent and what the
	// tool takes.
	text, _ := dispatch(t, "hana_query", `"not-an-object"`)
	if !strings.Contains(text, "a string") || !strings.Contains(text, "sql") {
		t.Fatalf("text = %q, want it to name the kind sent and the arguments accepted", text)
	}
}

// --- envelope ------------------------------------------------------------------

// FINDING (minor, CONFIRMED LIVE): `--max-rows 0` means unlimited (1200 rows came
// back uncapped) but the envelope reported "max_rows": 0, which an agent reads as
// "zero rows permitted" — the opposite of the truth.
func TestUnlimitedRowCapIsNullNotZero(t *testing.T) {
	srv := &Server{Now: time.Now}
	text, isErr := srv.envelope(&hana.Result{RowCount: 1200, Rows: []map[string]any{}}, nil, 0)
	if isErr {
		t.Fatalf("envelope error: %s", text)
	}
	var e map[string]any
	if err := json.Unmarshal([]byte(text), &e); err != nil {
		t.Fatalf("not JSON: %v", err)
	}
	raw, present := e["max_rows"]
	if !present {
		t.Fatalf("max_rows must still be present (as null), so the field is never just missing: %s", text)
	}
	if raw != nil {
		t.Fatalf(`max_rows = %v, want null; "max_rows": 0 reads as "zero rows permitted"`, raw)
	}
	if !strings.Contains(e["note"].(string), "no row cap") {
		t.Fatalf("note = %v, want it to say plainly that no cap is in force", e["note"])
	}
	// And a real cap still reports the number.
	text, _ = srv.envelope(&hana.Result{RowCount: 5}, nil, 1000)
	json.Unmarshal([]byte(text), &e)
	if e["max_rows"].(float64) != 1000 {
		t.Fatalf("max_rows = %v, want 1000", e["max_rows"])
	}
}

// --- hana_doctor ---------------------------------------------------------------

// FINDING (minor, CONFIRMED LIVE): hana_doctor measured clock skew
// (clock_skew_ms = -48943, HANA ~49s ahead) and then threw it away — there was no
// `clock` entry in checks[] and skew never affected `ok`. Every envelope's as_of
// comes from the host clock (as_of_source: mcp-host-clock), so a drifting host
// silently mis-stamps every answer it gives.
func TestDoctorChecksTheClockItMeasures(t *testing.T) {
	srv := &Server{Now: time.Now}

	within := srv.clockCheck(true, -49*time.Second)
	if within.Name != "clock" {
		t.Fatalf("checks[] has no clock entry: %+v", within)
	}
	if !within.OK {
		t.Fatalf("49s of skew should be reported but tolerated, not failed: %+v", within)
	}
	if !strings.Contains(within.Detail, "as_of") {
		t.Fatalf("the clock detail should say what the skew affects: %q", within.Detail)
	}

	bad := srv.clockCheck(true, 10*time.Minute)
	if bad.OK {
		t.Fatalf("10 minutes of skew was reported OK; every as_of stamp is wrong by that much: %+v", bad)
	}
	if bad.Hint == "" {
		t.Fatalf("a failing clock check must say what to do about it: %+v", bad)
	}
	// Unknown skew is honest, not a failure.
	if unknown := srv.clockCheck(false, 0); !unknown.OK || !strings.Contains(unknown.Detail, "unknown") {
		t.Fatalf("unparseable server time = %+v, want an OK check that says the skew is unknown", unknown)
	}
}

// FINDING (cosmetic, CONFIRMED LIVE): doctor's config check read "credentials
// resolved from (none — credentials came from the process environment)" when
// EnvFile was empty — the placeholder was interpolated into a sentence it does
// not fit.
func TestDoctorConfigDetailReadsAsASentence(t *testing.T) {
	run := func(envFile string) map[string]any {
		cfg := &config.Config{Host: "127.0.0.1", Port: "1", User: "u", Password: "p", EnvFile: envFile}
		db := hana.New(cfg, hana.Options{Limits: hana.Limits{Timeout: 500 * time.Millisecond}})
		defer db.Close()
		srv := &Server{DB: db, Now: time.Now}
		text, _ := srv.Dispatch(context.Background(), "hana_doctor", json.RawMessage(`{}`))
		var rep map[string]any
		if err := json.Unmarshal([]byte(text), &rep); err != nil {
			t.Fatalf("doctor output is not JSON: %v\n%s", err, text)
		}
		return rep
	}

	detailFor := func(rep map[string]any, name string) string {
		for _, c := range rep["checks"].([]any) {
			cm := c.(map[string]any)
			if cm["name"] == name {
				d, _ := cm["detail"].(string)
				return d
			}
		}
		t.Fatalf("no %q check in %v", name, rep["checks"])
		return ""
	}

	noFile := run("")
	d := detailFor(noFile, "config")
	if strings.Contains(d, "resolved from (none") {
		t.Fatalf("config detail = %q — the env-file placeholder was interpolated into a sentence it does not fit", d)
	}
	if !strings.Contains(d, "process environment") {
		t.Fatalf("config detail = %q, want it to say where the credentials came from", d)
	}
	// The env_file field itself still explains the absence.
	if ef, _ := noFile["env_file"].(string); !strings.Contains(ef, "none") {
		t.Fatalf("env_file = %q, want it to say plainly that no file was used", ef)
	}

	withFile := run("/opt/jivo-mcp/env/hana/hana.env")
	d = detailFor(withFile, "config")
	if !strings.Contains(d, "the env file /opt/jivo-mcp/env/hana/hana.env") {
		t.Fatalf("config detail = %q, want it to name the file it read", d)
	}
}

// FINDING (P3): layer 4 remains UNPROVEN — on HANA 2.00.059.13.1713941539
// SYS.M_TRANSACTIONS exposes no ACCESS_MODE column and reports
// TRANSACTION_TYPE='USER TRANSACTION' for a read-only transaction, so there is no
// read-only way to confirm `set transaction read only` took effect. That must be
// stated where a reader of the tool output can see it, not only in the README,
// and it must never quietly become a claim of proof.
func TestDoctorStatesThatLayer4IsUnproven(t *testing.T) {
	cfg := &config.Config{Host: "127.0.0.1", Port: "1", User: "u", Password: "p"}
	db := hana.New(cfg, hana.Options{Limits: hana.Limits{Timeout: 500 * time.Millisecond}})
	defer db.Close()
	srv := &Server{DB: db, Now: time.Now}

	text, _ := srv.Dispatch(context.Background(), "hana_doctor", json.RawMessage(`{}`))
	var rep map[string]any
	if err := json.Unmarshal([]byte(text), &rep); err != nil {
		t.Fatalf("doctor output is not JSON: %v", err)
	}
	ro, _ := rep["read_only"].(map[string]any)
	proof, _ := ro["transaction_proof"].(string)
	if proof == "" {
		t.Fatal("read_only has no transaction_proof field: a reader is entitled to know the layer-4 ask has never been observed to reject anything")
	}
	if !strings.HasPrefix(proof, "UNPROVEN") {
		t.Fatalf("transaction_proof = %q, want it to lead with UNPROVEN", proof)
	}
	for _, must := range []string{"M_TRANSACTIONS", "Layers 0-3", "SELECT-only"} {
		if !strings.Contains(proof, must) {
			t.Fatalf("transaction_proof does not mention %q: %s", must, proof)
		}
	}
	// The banned-token count reported here is what MCP.md quotes.
	if n, _ := ro["banned_tokens"].(float64); n != 33 {
		t.Fatalf("banned_tokens = %v, want 33 (32 originally + NEXTVAL)", ro["banned_tokens"])
	}
}

// --- tool surface --------------------------------------------------------------

// The hana_tables description and schema must stop advertising a whole-catalog
// search it cannot deliver, and must show the way out of a truncated page.
func TestTablesToolAdvertisesPagingAndTheSchemaRule(t *testing.T) {
	var def map[string]any
	for _, d := range testServer().ToolDefs() {
		if d["name"] == ToolTables {
			def = d
		}
	}
	if def == nil {
		t.Fatal("no hana_tables tool")
	}
	props := def["inputSchema"].(map[string]any)["properties"].(map[string]any)
	for _, arg := range []string{"schema", "like", "include_views", "offset", "no_row_counts"} {
		if _, ok := props[arg]; !ok {
			t.Fatalf("hana_tables does not advertise %q; without it a truncated catalog page cannot be recovered from", arg)
		}
	}
	schemaDesc := props["schema"].(map[string]any)["description"].(string)
	if !strings.Contains(schemaDesc, "ERROR, never an empty result") {
		t.Fatalf("the schema argument does not warn that an unknown value is refused: %q", schemaDesc)
	}
	offsetDesc := props["offset"].(map[string]any)["description"].(string)
	if !strings.Contains(offsetDesc, "first page") {
		t.Fatalf("the offset argument does not explain that an unfiltered listing is only a page: %q", offsetDesc)
	}
}

// The catalog truncation note must never carry the aggregate advice, which is
// meaningless for a table listing.
func TestCatalogAdviceIsNotTheAggregateAdvice(t *testing.T) {
	advice := hana.CatalogTruncationAdvice()
	if strings.Contains(advice, "SUM/COUNT/GROUP BY") {
		t.Fatalf("the catalog advice still tells the caller to aggregate: %q", advice)
	}
	for _, must := range []string{"like", "schema", "offset"} {
		if !strings.Contains(advice, must) {
			t.Fatalf("the catalog advice does not offer %q as a way forward: %q", must, advice)
		}
	}
	// ... while a business query still gets the advice that is right for it.
	if !strings.Contains(hana.QueryTruncationAdvice(), "SUM/COUNT/GROUP BY") {
		t.Fatalf("the query advice lost the aggregate steer: %q", hana.QueryTruncationAdvice())
	}
}

// The description itself carried the false promise: "Omit `schema` to search all
// three companies at once", while an unfiltered call returned 1000 Beverages
// tables and nothing from Oil or Mart.
func TestTablesDescriptionDoesNotPromiseAWholeCatalogSearch(t *testing.T) {
	desc := TablesFacts()
	if strings.Contains(desc, "all three companies at once") {
		t.Fatalf("hana_tables still promises a whole-catalog search it cannot deliver:\n%s", desc)
	}
	for _, must := range []string{"ONE PAGE", "offset", "like", "error, never an empty result"} {
		if !strings.Contains(desc, must) {
			t.Fatalf("hana_tables' description is missing %q:\n%s", must, desc)
		}
	}
	if len(desc) > 600 {
		t.Fatalf("hana_tables' description grew to %d chars; the crib sheet belongs in hana_query", len(desc))
	}
}
