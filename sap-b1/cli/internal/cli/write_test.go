package cli

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"sapb1/internal/catalog"
	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// fakeSAP is an httptest stand-in for the Service Layer that records every
// non-Login request, so a test can assert both "nothing was sent" and "exactly
// this was sent".
type fakeSAP struct {
	srv      *httptest.Server
	hits     int      // requests against entity sets (i.e. real writes)
	methods  []string // "METHOD /decoded/path" of each hit
	rawPaths []string // r.URL.EscapedPath() of each hit — the bytes on the wire
	rawQuery []string // any query string that arrived (should always be empty)
	bodies   []string // request body of each hit
	status   int      // status to return for a hit (default 201)
	body     string   // response body to return for a hit
	logAtHit []string // write-log lines as they stood during the first hit
	logPath  string
}

func newFakeSAP(t *testing.T) *fakeSAP {
	t.Helper()
	f := &fakeSAP{status: http.StatusCreated, body: `{"DocEntry":4321,"DocNum":99}`}
	f.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/Login") {
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake-session"})
			_, _ = w.Write([]byte(`{"SessionId":"fake-session"}`))
			return
		}
		body, _ := io.ReadAll(r.Body)
		f.hits++
		f.methods = append(f.methods, r.Method+" "+r.URL.Path)
		f.rawPaths = append(f.rawPaths, r.URL.EscapedPath())
		f.rawQuery = append(f.rawQuery, r.URL.RawQuery)
		f.bodies = append(f.bodies, string(body))
		if f.hits == 1 {
			if data, err := os.ReadFile(f.logPath); err == nil {
				f.logAtHit = splitLines(string(data))
			}
		}
		w.WriteHeader(f.status)
		if f.body != "" {
			_, _ = w.Write([]byte(f.body))
		}
	}))
	t.Cleanup(f.srv.Close)

	// Point the CLI's config at the fake server, and keep the session cache and
	// the write log inside the test's temp dir — no real host, no real files.
	home := t.TempDir()
	u, err := url.Parse(f.srv.URL)
	if err != nil {
		t.Fatalf("parsing fake server URL: %v", err)
	}
	f.logPath = filepath.Join(home, "writes.jsonl")
	t.Setenv("HOME", home)
	t.Setenv("SAPB1_WRITE_LOG", f.logPath)
	t.Setenv("SAPB1_HOST", u.Hostname())
	t.Setenv("SAPB1_PORT", u.Port())
	t.Setenv("SAPB1_COMPANYDB", "TESTDB")
	t.Setenv("SAPB1_USER", "tester")
	t.Setenv("SAPB1_PASSWORD", "irrelevant")
	t.Setenv("SAPB1_INSECURE", "true")
	t.Setenv("SAPB1_TIMEOUT", "5")

	return f
}

// loggedPaths returns the `path` field of every write-log line, in order.
func (f *fakeSAP) loggedPaths(t *testing.T) []string {
	t.Helper()
	data, err := os.ReadFile(f.logPath)
	if err != nil {
		t.Fatalf("reading write log: %v", err)
	}
	var out []string
	for _, line := range splitLines(string(data)) {
		var e struct {
			Event string `json:"event"`
			Path  string `json:"path"`
		}
		if err := json.Unmarshal([]byte(line), &e); err != nil {
			t.Fatalf("write log line is not JSON: %v\n%s", err, line)
		}
		if e.Event == "intent" {
			out = append(out, e.Path)
		}
	}
	return out
}

// catalogServicesForTest exposes the embedded catalog to the tests that need to
// pick a real service out of it (rather than hardcoding a name that could change).
func catalogServicesForTest() []catalog.Service { return catalog.Services() }

func splitLines(s string) []string {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil
	}
	return strings.Split(s, "\n")
}

// execWrite runs the real command tree with stdin/stdout/stderr captured.
func execWrite(t *testing.T, stdin string, args ...string) (stdout, stderr string, err error) {
	t.Helper()
	root := NewRootCmd()
	var out, errBuf bytes.Buffer
	root.SetOut(&out)
	root.SetErr(&errBuf)
	root.SetIn(strings.NewReader(stdin))
	root.SetArgs(args)
	err = root.Execute()
	return out.String(), errBuf.String(), err
}

// withTTY makes the write commands believe stdin is (or isn't) a terminal, so
// both the prompt path and the refusal path are reachable in tests.
func withTTY(t *testing.T, isTTY bool) {
	t.Helper()
	prev := stdinIsTTYFunc
	stdinIsTTYFunc = func() bool { return isTTY }
	t.Cleanup(func() { stdinIsTTYFunc = prev })
}

func requireUsageError(t *testing.T, err error, mustContain ...string) {
	t.Helper()
	if err == nil {
		t.Fatal("expected a usage error, got nil")
	}
	var usageErr *errs.UsageError
	if !errors.As(err, &usageErr) {
		t.Fatalf("expected *errs.UsageError, got %T: %v", err, err)
	}
	for _, want := range mustContain {
		if !strings.Contains(usageErr.Msg, want) {
			t.Errorf("error message should mention %q, got: %s", want, usageErr.Msg)
		}
	}
}

// ---------------------------------------------------------------------------
// post: entity sets only — no OData actions, no hand-built paths
// ---------------------------------------------------------------------------

// TestPostRejectsActionPathsAndNonEntitySets is the guardrail that makes the
// "a human adds the draft" story true. Every string below was proven to reach the
// wire before this fix; each must now be refused with zero HTTP requests.
func TestPostRejectsActionPathsAndNonEntitySets(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	cases := []struct {
		name   string
		target string
	}{
		{"cancel action", "Invoices(9)/Cancel"},
		{"post draft to document", "Drafts(4321)/SaveDraftToDocument"},
		{"close action", "Orders(1)/Close"},
		{"path traversal", "../Login"},
		{"batch", "$batch"},
		{"keyed entity", "Orders(17)"},
		{"query string", "Orders?$top=1"},
		{"absolute url", "https://evil.example/x"},
		{"dotted", "Orders.Cancel"},
		{"trailing slash", "Orders/"},
		{"unknown entity", "Orderz"},
		{"blank", "   "},
	}
	for _, tc := range cases {
		_, _, err := execWrite(t, "", "post", tc.target, "--yes", "--data", `{"CardCode":"C0001"}`)
		if err == nil {
			t.Errorf("%s: post %q must be refused", tc.name, tc.target)
			continue
		}
		var usageErr *errs.UsageError
		if !errors.As(err, &usageErr) {
			t.Errorf("%s: post %q gave %T, want *errs.UsageError", tc.name, tc.target, err)
		}
	}
	if f.hits != 0 {
		t.Fatalf("%d request(s) reached SAP; every rejected target must send nothing", f.hits)
	}
}

// TestPostActionRefusalExplainsWhy — the message has to teach, not just refuse.
func TestPostActionRefusalExplainsWhy(t *testing.T) {
	newFakeSAP(t)
	withTTY(t, false)
	_, _, err := execWrite(t, "", "post", "Invoices(9)/Cancel", "--yes", "--data", `{}`)
	requireUsageError(t, err, "entity set", "Cancel", "SAP B1 client")
}

// TestPostAcceptsCatalogEntitySetsCaseInsensitively — the flip side: real entity
// sets still work, and the catalog's canonical spelling is what goes on the wire
// (OData is case-sensitive; operators are not).
func TestPostAcceptsCatalogEntitySetsCaseInsensitively(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)
	f.body = `{"CardCode":"C90001"}`

	if _, _, err := execWrite(t, "", "post", "businesspartners", "--yes", "--data", `{"CardCode":"C90001"}`); err != nil {
		t.Fatalf("post businesspartners: %v", err)
	}
	if f.hits != 1 {
		t.Fatalf("hits = %d, want 1", f.hits)
	}
	if f.methods[0] != "POST /b1s/v1/BusinessPartners" {
		t.Errorf("request = %s, want the canonical BusinessPartners spelling", f.methods[0])
	}
}

// TestPostRejectsEntitySetsThatCannotBeCreated — an entity the catalog knows but
// which has no plain POST (read-only views) is refused before the network.
func TestPostRejectsEntitySetsThatCannotBeCreated(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	// SQLQueries-style read-only services exist in the catalog; find one with no
	// bare POST so the test tracks the real catalog rather than a hardcoded name.
	target := ""
	for _, svc := range catalogServicesForTest() {
		if !supportsEntityOperation(svc, "POST") && bareEntitySetRe.MatchString(svc.Service) {
			target = svc.Service
			break
		}
	}
	if target == "" {
		t.Skip("no non-POSTable service in the catalog to test with")
	}

	_, _, err := execWrite(t, "", "post", target, "--yes", "--data", `{"x":1}`)
	requireUsageError(t, err, "does not support POST")
	if f.hits != 0 {
		t.Errorf("hits = %d, want 0", f.hits)
	}
}

// ---------------------------------------------------------------------------
// patch: strict parsing + correct URL encoding
// ---------------------------------------------------------------------------

func TestBuildKeyPath(t *testing.T) {
	cases := []struct {
		entity, key, want string
		wantErr           bool
	}{
		// Key kind comes from the entity, not the shape of the key: CardCode is a
		// string key even when it looks like a number.
		{entity: "BusinessPartners", key: "200001", want: "BusinessPartners('200001')"},
		{entity: "BusinessPartners", key: "V10000", want: "BusinessPartners('V10000')"},
		{entity: "Items", key: "A-001", want: "Items('A-001')"},
		{entity: "Orders", key: "123", want: "Orders(123)"},
		{entity: "Orders", key: "0", want: "Orders(0)"},
		{entity: "Orders", key: "V10000", wantErr: true}, // numeric key, non-numeric input
		// Percent-encoding: JIVO item codes contain "/", and #/%/? would otherwise
		// truncate or reshape the URL.
		{entity: "Items", key: "OIL/1L/MUS", want: "Items('OIL%2F1L%2FMUS')"},
		{entity: "Items", key: "A#B", want: "Items('A%23B')"},
		{entity: "Items", key: "DISC50%", want: "Items('DISC50%25')"},
		{entity: "Items", key: "x?$top=1", want: "Items('x%3F$top=1')"},
		{entity: "Items", key: "a b", want: "Items('a%20b')"},
		// OData quote-doubling survives, and stays readable in previews/logs.
		{entity: "BusinessPartners", key: "O'Brien Traders", want: "BusinessPartners('O''Brien%20Traders')"},
		// Unknown entity: fall back to the key's shape.
		{entity: "SomeUnknownThing", key: "42", want: "SomeUnknownThing(42)"},
		{entity: "SomeUnknownThing", key: "ABC", want: "SomeUnknownThing('ABC')"},
	}
	for _, tc := range cases {
		got, err := buildKeyPath(tc.entity, tc.key)
		if tc.wantErr {
			if err == nil {
				t.Errorf("buildKeyPath(%q,%q) = %q, want an error", tc.entity, tc.key, got)
			}
			continue
		}
		if err != nil {
			t.Errorf("buildKeyPath(%q,%q) errored: %v", tc.entity, tc.key, err)
			continue
		}
		if got != tc.want {
			t.Errorf("buildKeyPath(%q,%q) = %q, want %q", tc.entity, tc.key, got, tc.want)
		}
	}
}

func TestResolvePatchPath(t *testing.T) {
	ok := []struct{ target, key, want string }{
		{"Orders(123)", "", "Orders(123)"},
		{"BusinessPartners", "V10000", "BusinessPartners('V10000')"},
		{"BusinessPartners('V10000')", "", "BusinessPartners('V10000')"},
		{"businesspartners", "V10000", "BusinessPartners('V10000')"},
		// An inline key is parsed and rebuilt, so it gets encoded too.
		{"Items('OIL/1L/MUS')", "", "Items('OIL%2F1L%2FMUS')"},
		// '' inside an inline literal is one apostrophe, and round-trips.
		{"BusinessPartners('O''Brien')", "", "BusinessPartners('O''Brien')"},
	}
	for _, tc := range ok {
		got, err := resolvePatchPath(tc.target, tc.key)
		if err != nil {
			t.Errorf("resolvePatchPath(%q,%q) errored: %v", tc.target, tc.key, err)
			continue
		}
		if got != tc.want {
			t.Errorf("resolvePatchPath(%q,%q) = %q, want %q", tc.target, tc.key, got, tc.want)
		}
	}

	bad := []struct{ name, target, key string }{
		{"no key", "BusinessPartners", ""},
		{"whitespace key", "BusinessPartners", "   "},
		{"key twice", "Orders(123)", "123"},
		{"empty target", "", "V10000"},
		{"query string appended", "Items('A')?$select=ItemName", ""},
		{"action path", "Orders(1)/Cancel", ""},
		{"trailing junk", "Orders(123)x", ""},
		{"nested parens", "Orders((123))", ""},
		{"unterminated quote", "Items('A)", ""},
		{"unquoted non-numeric", "Items(ABC)", ""},
		{"empty key parens", "Orders()", ""},
		{"unknown entity", "Orderz(1)", ""},
	}
	for _, tc := range bad {
		if got, err := resolvePatchPath(tc.target, tc.key); err == nil {
			t.Errorf("%s: resolvePatchPath(%q,%q) = %q, want an error", tc.name, tc.target, tc.key, got)
		} else {
			var usageErr *errs.UsageError
			if !errors.As(err, &usageErr) {
				t.Errorf("%s: got %T, want *errs.UsageError", tc.name, err)
			}
		}
	}
}

// TestPatchEncodesKeyOnTheWireAndInTheLog is the end-to-end version of the
// encoding fix: what the server sees, what the log records and what the preview
// showed must all be the same bytes — and no part of the key may leak into a
// query string or an extra path segment.
func TestPatchEncodesKeyOnTheWireAndInTheLog(t *testing.T) {
	keys := []struct {
		key      string
		wantPath string
	}{
		{"OIL/1L/MUS", "Items('OIL%2F1L%2FMUS')"},
		{"A#B", "Items('A%23B')"},
		{"DISC50%", "Items('DISC50%25')"},
		{"x?$top=1", "Items('x%3F$top=1')"},
	}
	for _, tc := range keys {
		f := newFakeSAP(t)
		withTTY(t, false)
		f.status, f.body = http.StatusNoContent, ""

		_, stderr, err := execWrite(t, "", "patch", "Items", "--key", tc.key, "--yes", "--data", `{"ItemName":"x"}`)
		if err != nil {
			t.Fatalf("key %q: patch failed: %v", tc.key, err)
		}
		if f.hits != 1 {
			t.Fatalf("key %q: hits = %d, want 1", tc.key, f.hits)
		}

		wantEscaped := "/b1s/v1/" + tc.wantPath
		if f.rawPaths[0] != wantEscaped {
			t.Errorf("key %q: server saw path %q, want %q", tc.key, f.rawPaths[0], wantEscaped)
		}
		if f.rawQuery[0] != "" {
			t.Errorf("key %q: part of the key leaked into the query string: %q", tc.key, f.rawQuery[0])
		}
		if logged := f.loggedPaths(t); len(logged) != 1 || logged[0] != tc.wantPath {
			t.Errorf("key %q: write log recorded %v, want [%s] — the log must match the wire", tc.key, logged, tc.wantPath)
		}
		if !strings.Contains(stderr, tc.wantPath) {
			t.Errorf("key %q: preview should show the exact path %q, got:\n%s", tc.key, tc.wantPath, stderr)
		}
	}
}

// ---------------------------------------------------------------------------
// payload handling
// ---------------------------------------------------------------------------

func TestLoadPayloadRejectsInvalidJSONAndNonObjects(t *testing.T) {
	cmd := NewRootCmd()

	cases := []struct {
		name string
		data string
	}{
		{"not json", `{CardCode: C0001}`},
		{"truncated", `{"CardCode":`},
		{"array", `[{"CardCode":"C0001"}]`},
		{"string", `"C0001"`},
		{"number", `42`},
		{"null", `null`},
		{"empty", `   `},
		{"two objects", `{"a":1} {"b":2}`},
	}
	for _, tc := range cases {
		_, _, err := loadPayload(cmd, writeFlags{data: tc.data})
		if err == nil {
			t.Errorf("%s: loadPayload(%q) should fail", tc.name, tc.data)
			continue
		}
		var usageErr *errs.UsageError
		if !errors.As(err, &usageErr) {
			t.Errorf("%s: loadPayload = %T, want *errs.UsageError", tc.name, err)
		}
	}

	// A single object is accepted and compacted.
	payload, obj, err := loadPayload(cmd, writeFlags{data: "{\n  \"CardCode\" : \"C0001\"\n}"})
	if err != nil {
		t.Fatalf("valid object rejected: %v", err)
	}
	if string(payload) != `{"CardCode":"C0001"}` {
		t.Errorf("payload = %s, want compacted JSON", payload)
	}
	if obj["CardCode"] != "C0001" {
		t.Errorf("decoded object = %v, want CardCode C0001", obj)
	}
}

func TestLoadPayloadFromFileAndStdin(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "body.json")
	if err := os.WriteFile(path, []byte(`{"CardCode":"C0002"}`), 0o600); err != nil {
		t.Fatalf("writing temp payload: %v", err)
	}

	cmd := NewRootCmd()
	payload, _, err := loadPayload(cmd, writeFlags{dataFile: path})
	if err != nil {
		t.Fatalf("--data-file: %v", err)
	}
	if string(payload) != `{"CardCode":"C0002"}` {
		t.Errorf("payload = %s", payload)
	}

	// Every spelling of "stdin" consumes stdin, so each demands --yes.
	for _, spelling := range []string{"-", "/dev/stdin", "/dev/fd/0"} {
		if _, _, err := loadPayload(cmd, writeFlags{dataFile: spelling}); err == nil {
			t.Errorf("--data-file %s without --yes should be refused", spelling)
		}
	}

	cmd.SetIn(strings.NewReader(`{"CardCode":"C0003"}`))
	payload, _, err = loadPayload(cmd, writeFlags{dataFile: "-", yes: true})
	if err != nil {
		t.Fatalf("--data-file - --yes: %v", err)
	}
	if string(payload) != `{"CardCode":"C0003"}` {
		t.Errorf("stdin payload = %s", payload)
	}

	// --dry-run sends nothing, so it may read stdin without --yes.
	cmd.SetIn(strings.NewReader(`{"CardCode":"C0004"}`))
	if _, _, err := loadPayload(cmd, writeFlags{dataFile: "-", dryRun: true}); err != nil {
		t.Errorf("--data-file - --dry-run should be allowed: %v", err)
	}

	if _, _, err := loadPayload(cmd, writeFlags{dataFile: filepath.Join(dir, "nope.json")}); err == nil {
		t.Error("a missing --data-file should error")
	}
}

func TestDataAndDataFileMutuallyExclusive(t *testing.T) {
	_, _, err := loadPayload(NewRootCmd(), writeFlags{data: `{"a":1}`, dataFile: "body.json"})
	requireUsageError(t, err, "mutually exclusive")

	if _, _, err := loadPayload(NewRootCmd(), writeFlags{}); err == nil {
		t.Error("no payload at all should be refused")
	}
}

// TestDraftPayloadIsSentByteExact — the payload must reach SAP exactly as the
// operator wrote it. A map round-trip used to mangle long numbers (an 18-digit
// DocNum came back changed), alphabetize keys and collapse duplicates.
func TestDraftPayloadIsSentByteExact(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	// Key order that is NOT alphabetical, an 18-digit integer, and a
	// high-precision decimal — all of which a float round-trip would damage.
	in := `{"ZZZLast":1,"DocNum":123456789012345678,"DocTotal":1180.123456789012345,"CardCode":"C0001","AAAFirst":2}`
	if _, _, err := execWrite(t, "", "draft", "order", "--yes", "--data", in); err != nil {
		t.Fatalf("draft: %v", err)
	}
	if f.hits != 1 {
		t.Fatalf("hits = %d, want 1", f.hits)
	}

	sent := f.bodies[0]
	// Injection puts DocObjectCode first; everything after it must be the input
	// verbatim, byte for byte.
	wantPrefix := `{"DocObjectCode":"oOrders",`
	if !strings.HasPrefix(sent, wantPrefix) {
		t.Fatalf("sent body should start with the injected field, got:\n%s", sent)
	}
	if got, want := strings.TrimPrefix(sent, wantPrefix), strings.TrimPrefix(in, "{"); got != want {
		t.Errorf("payload was altered in transit\n got:  %s\n want: %s", got, want)
	}
	for _, literal := range []string{"123456789012345678", "1180.123456789012345"} {
		if !strings.Contains(sent, literal) {
			t.Errorf("numeric literal %s did not survive: %s", literal, sent)
		}
	}
}

// TestPostPayloadIsSentByteExact — post never injects anything, so the body must
// be the operator's bytes, only compacted.
func TestPostPayloadIsSentByteExact(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)
	f.body = `{"CardCode":"C90001"}`

	in := `{"CardName":"Zed","CardCode":"C90001","Big":999999999999999999}`
	if _, _, err := execWrite(t, "", "post", "BusinessPartners", "--yes", "--data", in); err != nil {
		t.Fatalf("post: %v", err)
	}
	if f.bodies[0] != in {
		t.Errorf("post altered the payload\n got:  %s\n want: %s", f.bodies[0], in)
	}
}

// ---------------------------------------------------------------------------
// confirmation + dry run
// ---------------------------------------------------------------------------

// TestNonTTYWithoutYesRefuses is the guardrail for cron jobs, pipes and agents:
// with no terminal and no --yes, the write must be refused before any HTTP
// request leaves the process.
func TestNonTTYWithoutYesRefuses(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	_, stderr, err := execWrite(t, "", "draft", "order", "--data", `{"CardCode":"C0001"}`)
	requireUsageError(t, err, "--yes", "not a terminal")
	if f.hits != 0 {
		t.Fatalf("%d request(s) reached SAP; a refused write must send nothing", f.hits)
	}
	// The operator still gets to see what would have been sent.
	if !strings.Contains(stderr, "About to WRITE to SAP") || !strings.Contains(stderr, "TESTDB") {
		t.Errorf("expected the preview on stderr, got:\n%s", stderr)
	}
}

// TestConfirmRequiresExactYes — "y", "Y", "yes please" and everything else abort.
// A single stray keystroke must not be able to commit a production write.
func TestConfirmRequiresExactYes(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, true)

	for _, answer := range []string{"y\n", "Y\n", "YES\n", "yes please\n", "no\n", "\n", "", " yes yes\n"} {
		_, stderr, err := execWrite(t, answer, "draft", "order", "--data", `{"CardCode":"C0001"}`)
		if err == nil {
			t.Fatalf("answer %q must abort the write", answer)
		}
		if !strings.Contains(err.Error(), "aborted") {
			t.Errorf("answer %q: error should say it aborted, got: %v", answer, err)
		}
		if !strings.Contains(stderr, "Type 'yes' to send this write to TESTDB") {
			t.Errorf("answer %q: expected the confirmation prompt, got:\n%s", answer, stderr)
		}
	}
	if f.hits != 0 {
		t.Fatalf("%d request(s) reached SAP after aborting; must be 0", f.hits)
	}

	// Only the exact word goes through (surrounding whitespace is forgiven).
	for _, answer := range []string{"yes\n", "  yes  \n"} {
		before := f.hits
		if _, _, err := execWrite(t, answer, "draft", "order", "--data", `{"CardCode":"C0001"}`); err != nil {
			t.Fatalf("answer %q: confirmed write failed: %v", answer, err)
		}
		if f.hits != before+1 {
			t.Fatalf("answer %q: expected exactly one request, hits went %d -> %d", answer, before, f.hits)
		}
	}
}

// TestDryRunSendsNothing — the sanctioned agent flow: show the operator the exact
// request, contact nothing, exit 0.
func TestDryRunSendsNothing(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	for _, args := range [][]string{
		{"draft", "order", "--dry-run", "--data", `{"CardCode":"C0001"}`},
		{"post", "BusinessPartners", "--dry-run", "--data", `{"CardCode":"C90001"}`},
		{"patch", "BusinessPartners", "--key", "V10000", "--dry-run", "--data", `{"Phone1":"9"}`},
	} {
		stdout, _, err := execWrite(t, "", args...)
		if err != nil {
			t.Fatalf("%v: --dry-run must succeed, got: %v", args, err)
		}
		if !strings.Contains(stdout, "DRY RUN") || !strings.Contains(stdout, "nothing was sent") {
			t.Errorf("%v: stdout should say it sent nothing, got:\n%s", args, stdout)
		}
		if !strings.Contains(stdout, "https://") || !strings.Contains(stdout, "/b1s/v1/") {
			t.Errorf("%v: stdout should show the full URL, got:\n%s", args, stdout)
		}
		if !strings.Contains(stdout, "TESTDB") {
			t.Errorf("%v: stdout should name the company, got:\n%s", args, stdout)
		}
	}

	if f.hits != 0 {
		t.Fatalf("--dry-run sent %d request(s); must be 0", f.hits)
	}
	// Not even a Login, and nothing in the write log.
	if _, err := os.Stat(f.logPath); err == nil {
		t.Error("--dry-run must not write to the audit log")
	}
}

// TestDryRunJSONShowsExactWirePayload — an agent needs the machine-readable form
// to hand to the operator, and the payload in it must be the wire bytes.
func TestDryRunJSONShowsExactWirePayload(t *testing.T) {
	newFakeSAP(t)
	withTTY(t, false)

	stdout, _, err := execWrite(t, "", "draft", "order", "--dry-run", "--json",
		"--data", `{"CardCode":"C0001","DocNum":123456789012345678}`)
	if err != nil {
		t.Fatalf("draft --dry-run --json: %v", err)
	}

	var got struct {
		DryRun  bool            `json:"dryRun"`
		Method  string          `json:"method"`
		URL     string          `json:"url"`
		Payload json.RawMessage `json:"payload"`
	}
	if err := json.Unmarshal([]byte(stdout), &got); err != nil {
		t.Fatalf("--dry-run --json output is not JSON: %v\n%s", err, stdout)
	}
	if !got.DryRun || got.Method != "POST" || !strings.HasSuffix(got.URL, "/b1s/v1/Drafts") {
		t.Errorf("unexpected dry-run object: %+v", got)
	}
	if !strings.Contains(string(got.Payload), `"DocObjectCode":"oOrders"`) {
		t.Errorf("payload should show the injected field: %s", got.Payload)
	}
	if !strings.Contains(string(got.Payload), "123456789012345678") {
		t.Errorf("payload numbers must be exact: %s", got.Payload)
	}
}

// ---------------------------------------------------------------------------
// draft / post / patch behaviour
// ---------------------------------------------------------------------------

// TestDraftInjectsAndConflictsDocObjectCode covers the whole point of `draft`:
// the Drafts row must carry the type of document it will become.
func TestDraftInjectsAndConflictsDocObjectCode(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	// 1. Absent in the payload -> injected as the canonical enum string.
	stdout, _, err := execWrite(t, "", "draft", "order", "--yes", "--data", `{"CardCode":"C0001","DocumentLines":[{"ItemCode":"A0001","Quantity":10}]}`)
	if err != nil {
		t.Fatalf("draft order: %v", err)
	}
	if f.hits != 1 {
		t.Fatalf("hits = %d, want 1", f.hits)
	}
	if f.methods[0] != "POST /b1s/v1/Drafts" {
		t.Errorf("request = %s, want POST /b1s/v1/Drafts", f.methods[0])
	}
	if !strings.Contains(f.bodies[0], `"DocObjectCode":"oOrders"`) {
		t.Errorf("DocObjectCode was not injected: %s", f.bodies[0])
	}
	if !strings.Contains(f.bodies[0], `"CardCode":"C0001"`) {
		t.Errorf("payload fields must survive injection, got %s", f.bodies[0])
	}
	if !strings.Contains(stdout, "Draft created in TESTDB") || !strings.Contains(stdout, "DocEntry 4321") {
		t.Errorf("summary should name the company and the new key, got: %s", stdout)
	}
	if !strings.Contains(stdout, "Document Drafts") {
		t.Errorf("summary must tell the operator to review it in SAP, got: %s", stdout)
	}

	// 2. Present and agreeing (numeric form) -> accepted, and left exactly as the
	//    operator wrote it.
	if _, _, err := execWrite(t, "", "draft", "order", "--yes", "--data", `{"CardCode":"C0001","DocObjectCode":17}`); err != nil {
		t.Fatalf("agreeing DocObjectCode should be accepted: %v", err)
	}
	if f.hits != 2 {
		t.Fatalf("hits = %d, want 2", f.hits)
	}
	if f.bodies[1] != `{"CardCode":"C0001","DocObjectCode":17}` {
		t.Errorf("an agreeing payload must be sent verbatim, got %s", f.bodies[1])
	}

	// 3. Present and disagreeing -> refused, nothing sent.
	_, _, err = execWrite(t, "", "draft", "order", "--yes", "--data", `{"CardCode":"C0001","DocObjectCode":"oInvoices"}`)
	requireUsageError(t, err, "mismatch")
	if f.hits != 2 {
		t.Fatalf("hits = %d after the refused write, want it unchanged at 2", f.hits)
	}

	// 4. An unknown doc type never reaches the network either.
	if _, _, err := execWrite(t, "", "draft", "orderz", "--yes", "--data", `{"CardCode":"C0001"}`); err == nil {
		t.Fatal("unknown doc type should be refused")
	}
	if f.hits != 2 {
		t.Fatalf("hits = %d, want it unchanged at 2", f.hits)
	}
}

// TestDraftJSONKeepsTheReviewInstruction — with --json, stdout is SAP's object,
// so the "a human must Add this" instruction has to survive on stderr.
func TestDraftJSONKeepsTheReviewInstruction(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)
	f.body = `{"DocEntry":4321,"DocNum":123456789012345678,"DocObjectCode":"oOrders"}`

	stdout, stderr, err := execWrite(t, "", "draft", "order", "--yes", "--json", "--data", `{"CardCode":"C0001"}`)
	if err != nil {
		t.Fatalf("draft --json: %v", err)
	}
	if !strings.Contains(stderr, "Document Drafts") || !strings.Contains(stderr, "review") {
		t.Errorf("the review instruction must survive --json on stderr, got:\n%s", stderr)
	}
	// stdout stays machine-readable, and SAP's numbers pass through untouched.
	var obj map[string]interface{}
	if err := json.Unmarshal([]byte(stdout), &obj); err != nil {
		t.Fatalf("stdout is not clean JSON: %v\n%s", err, stdout)
	}
	if !strings.Contains(stdout, "123456789012345678") {
		t.Errorf("SAP's number was reshaped on the way out: %s", stdout)
	}
}

// TestWriteJSONPassesNonObjectBodyThrough — SAP occasionally answers with
// something that isn't an object; --json must not replace it with {"status":201}.
func TestWriteJSONPassesNonObjectBodyThrough(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)
	f.body = `"CREATED-BUT-NOT-AN-OBJECT"`

	stdout, _, err := execWrite(t, "", "post", "BusinessPartners", "--yes", "--json", "--data", `{"CardCode":"C90001"}`)
	if err != nil {
		t.Fatalf("post --json: %v", err)
	}
	if !strings.Contains(stdout, "CREATED-BUT-NOT-AN-OBJECT") {
		t.Errorf("a non-object body must be passed through verbatim, got: %s", stdout)
	}
	if strings.Contains(stdout, `"status"`) {
		t.Errorf("the real body must not be replaced by a status stub: %s", stdout)
	}
}

// TestPostAndPatchHitTheRightEndpoints checks the two escape hatches address what
// they say they address, and that patch tolerates a 204 with no body.
func TestPostAndPatchHitTheRightEndpoints(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	f.status, f.body = http.StatusCreated, `{"CardCode":"C90001","CardName":"Test Customer"}`
	stdout, _, err := execWrite(t, "", "post", "BusinessPartners", "--yes", "--data", `{"CardCode":"C90001","CardName":"Test Customer"}`)
	if err != nil {
		t.Fatalf("post BusinessPartners: %v", err)
	}
	if f.methods[0] != "POST /b1s/v1/BusinessPartners" {
		t.Errorf("request = %s", f.methods[0])
	}
	if !strings.Contains(stdout, "Created BusinessPartners in TESTDB") || !strings.Contains(stdout, "CardCode C90001") {
		t.Errorf("post summary = %s", stdout)
	}

	f.status, f.body = http.StatusNoContent, ""
	stdout, _, err = execWrite(t, "", "patch", "BusinessPartners", "--key", "V10000", "--yes", "--data", `{"Phone1":"9876543210"}`)
	if err != nil {
		t.Fatalf("patch: %v", err)
	}
	if f.methods[1] != "PATCH /b1s/v1/BusinessPartners('V10000')" {
		t.Errorf("request = %s, want the quoted key path", f.methods[1])
	}
	if !strings.Contains(stdout, "Updated BusinessPartners('V10000') in TESTDB (HTTP 204).") {
		t.Errorf("patch summary = %s", stdout)
	}

	// --json on a 204 reports the status rather than inventing an object.
	stdout, _, err = execWrite(t, "", "patch", "Orders(123)", "--yes", "--json", "--data", `{"Comments":"ok"}`)
	if err != nil {
		t.Fatalf("patch --json: %v", err)
	}
	if !strings.Contains(stdout, `"status": 204`) {
		t.Errorf("patch --json output = %s", stdout)
	}
	if f.methods[2] != "PATCH /b1s/v1/Orders(123)" {
		t.Errorf("request = %s, want the bare numeric key path", f.methods[2])
	}
}

// TestWriteCommandsRejectCSV — there is no table to CSV-ify for a write.
func TestWriteCommandsRejectCSV(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	_, _, err := execWrite(t, "", "draft", "order", "--yes", "--csv", "--data", `{"CardCode":"C0001"}`)
	requireUsageError(t, err, "--csv")
	if f.hits != 0 {
		t.Errorf("hits = %d, want 0", f.hits)
	}
}

// TestWriteLogRecordsCLIWrites ties the CLI layer to the audit log, including the
// host/port fields that answer "was that production?".
func TestWriteLogRecordsCLIWrites(t *testing.T) {
	f := newFakeSAP(t)
	withTTY(t, false)

	if _, _, err := execWrite(t, "", "draft", "order", "--yes", "--data", `{"CardCode":"C0001"}`); err != nil {
		t.Fatalf("draft: %v", err)
	}

	data, err := os.ReadFile(f.logPath)
	if err != nil {
		t.Fatalf("write log was not created: %v", err)
	}
	lines := splitLines(string(data))
	if len(lines) != 2 {
		t.Fatalf("write log has %d lines, want 2 (intent + outcome)", len(lines))
	}
	// The intent line was already on disk while the request was in flight — that
	// is what makes a Ctrl-C mid-POST traceable.
	if len(f.logAtHit) != 1 || !strings.Contains(f.logAtHit[0], `"event":"intent"`) {
		t.Errorf("during the request the log should hold exactly the intent line, had: %v", f.logAtHit)
	}
	for i, line := range lines {
		var e map[string]interface{}
		if err := json.Unmarshal([]byte(line), &e); err != nil {
			t.Fatalf("log line %d is not JSON: %v", i, err)
		}
		if e["method"] != "POST" || e["path"] != "Drafts" || e["company_db"] != "TESTDB" {
			t.Errorf("log entry %d = %v", i, e)
		}
		if e["host"] == "" || e["host"] == nil || e["port"] == nil {
			t.Errorf("log entry %d has no host/port: %v", i, e)
		}
	}
}

// TestConfirmWritePreviewGoesToStderr keeps stdout parseable: the preview must
// never contaminate the machine-readable result.
func TestConfirmWritePreviewGoesToStderr(t *testing.T) {
	cmd := NewRootCmd()
	var out, errBuf bytes.Buffer
	cmd.SetOut(&out)
	cmd.SetErr(&errBuf)

	cfg := &config.Config{Host: "sap.example", Port: 50000, CompanyDB: "TESTDB", User: "tester"}
	if err := confirmWrite(cmd, cfg, "POST", "Drafts", []byte(`{"CardCode":"C0001"}`), true, false); err != nil {
		t.Fatalf("confirmWrite with --yes: %v", err)
	}
	if out.Len() != 0 {
		t.Errorf("preview leaked to stdout: %s", out.String())
	}
	for _, want := range []string{"About to WRITE to SAP", "TESTDB", "POST", "Drafts", "C0001"} {
		if !strings.Contains(errBuf.String(), want) {
			t.Errorf("preview missing %q:\n%s", want, errBuf.String())
		}
	}
}

// TestSpliceJSONField is the byte-preserving injection primitive.
func TestSpliceJSONField(t *testing.T) {
	cases := []struct{ in, want string }{
		{`{}`, `{"DocObjectCode":"oOrders"}`},
		{`{"a":1}`, `{"DocObjectCode":"oOrders","a":1}`},
		{`{"a":1,"b":[1,2,{"c":3}]}`, `{"DocObjectCode":"oOrders","a":1,"b":[1,2,{"c":3}]}`},
		{`{"n":123456789012345678}`, `{"DocObjectCode":"oOrders","n":123456789012345678}`},
	}
	for _, tc := range cases {
		got, err := spliceJSONField([]byte(tc.in), "DocObjectCode", "oOrders")
		if err != nil {
			t.Errorf("spliceJSONField(%s) errored: %v", tc.in, err)
			continue
		}
		if string(got) != tc.want {
			t.Errorf("spliceJSONField(%s) = %s, want %s", tc.in, got, tc.want)
		}
		if !json.Valid(got) {
			t.Errorf("spliceJSONField(%s) produced invalid JSON: %s", tc.in, got)
		}
	}
}
