package main

import (
	"bytes"
	"encoding/csv"
	"os"
	"strings"
	"testing"
)

// Regression tests for the reviewer/tester findings against the CLI.

// --- delimited output ----------------------------------------------------------

// FINDING (P2, CONFIRMED LIVE against production JIVO_OIL_HANADB.OCRD):
// `-csv` emitted a bare strings.Join with no quoting or escaping, so a value
// containing a comma silently misaligned every later column —
// `VENDA001230,V TRANS, V XPRESS & V LOGIS,0.000000` is FOUR fields for a
// three-column SELECT, so the balance lands under the wrong header in Excel.
// Blast radius on Oil alone: 67/3391 OCRD."Address", 37 OINV."Comments",
// 4 OITM."ItemName" and 1 OCRD."CardName" contain a comma. Embedded newlines
// likewise split one database row across two output lines.
func TestCSVOutputIsProperlyQuoted(t *testing.T) {
	// The live row that proved the defect.
	var buf bytes.Buffer
	sink := newRowSink(&buf, true)
	if err := sink.write([]string{"CardCode", "CardName", "Balance"}); err != nil {
		t.Fatal(err)
	}
	if err := sink.write([]string{"VENDA001230", "V TRANS, V XPRESS & V LOGIS", "0.000000"}); err != nil {
		t.Fatal(err)
	}
	if err := sink.flush(); err != nil {
		t.Fatal(err)
	}

	rows, err := csv.NewReader(strings.NewReader(buf.String())).ReadAll()
	if err != nil {
		t.Fatalf("the CSV this tool emits is not parseable CSV: %v\n%s", err, buf.String())
	}
	if len(rows) != 2 {
		t.Fatalf("got %d records, want 2:\n%s", len(rows), buf.String())
	}
	for i, r := range rows {
		if len(r) != 3 {
			t.Fatalf("record %d has %d fields, want 3 — a comma inside a value shifted every later column, "+
				"so the balance lands under the wrong header:\n%s", i, len(r), buf.String())
		}
	}
	if rows[1][1] != "V TRANS, V XPRESS & V LOGIS" {
		t.Fatalf("CardName round-tripped as %q", rows[1][1])
	}
	if rows[1][2] != "0.000000" {
		t.Fatalf("Balance round-tripped as %q, want it still under the Balance header", rows[1][2])
	}
}

// Quotes, newlines and CRs must survive too, and every one must round-trip.
func TestCSVOutputRoundTripsEveryAwkwardValue(t *testing.T) {
	want := [][]string{
		{"A", "B", "C"},
		{"has,comma", `has"quote`, "1"},
		{"has\nnewline", "has\ttab", "2"},
		{"has\r\ncrlf", "plain", "3"},
		{`ends with backslash \`, "", "NULL"},
		{"V TRANS, V XPRESS & V LOGIS", `He said "hi", then left`, "1074316124.55"},
	}
	var buf bytes.Buffer
	sink := newRowSink(&buf, true)
	for _, r := range want {
		if err := sink.write(r); err != nil {
			t.Fatal(err)
		}
	}
	if err := sink.flush(); err != nil {
		t.Fatal(err)
	}

	rd := csv.NewReader(strings.NewReader(buf.String()))
	rd.FieldsPerRecord = 3
	got, err := rd.ReadAll()
	if err != nil {
		t.Fatalf("emitted CSV does not parse: %v\n%q", err, buf.String())
	}
	if len(got) != len(want) {
		t.Fatalf("got %d records, want %d:\n%q", len(got), len(want), buf.String())
	}
	for i := range want {
		for j := range want[i] {
			// encoding/csv normalises a bare \r\n inside a quoted field to \n on
			// read, which is the standard's own behaviour; compare on that basis.
			w := strings.ReplaceAll(want[i][j], "\r\n", "\n")
			if got[i][j] != w {
				t.Fatalf("record %d field %d = %q, want %q", i, j, got[i][j], w)
			}
		}
	}
}

// FINDING (same, TSV half): a value containing CHAR(9) yielded `tab\there\t2$`
// for a 2-column header, and a value containing CHAR(10) emitted TWO output lines
// for ONE database row. TSV escapes rather than quotes, because its readers are
// `cut -f` and `awk -F'\t'`, which do not understand quotes — so the invariant to
// hold is "one row is one line, and a field never contains a tab".
func TestTSVOutputKeepsOneRowOnOneLine(t *testing.T) {
	var buf bytes.Buffer
	sink := newRowSink(&buf, false)
	rows := [][]string{
		{"A", "B", "C"},
		{"tab\there", "2", "x"},
		{"line\none\nline\ntwo", "3", "y"},
		{"carriage\rreturn", "4", "z"},
		{"back\\slash", "5", "w"},
		{"V TRANS, V XPRESS & V LOGIS", "6", "v"}, // a comma is fine in TSV
	}
	for _, r := range rows {
		if err := sink.write(r); err != nil {
			t.Fatal(err)
		}
	}
	if err := sink.flush(); err != nil {
		t.Fatal(err)
	}

	lines := strings.Split(strings.TrimRight(buf.String(), "\n"), "\n")
	if len(lines) != len(rows) {
		t.Fatalf("%d database rows produced %d output lines — a value with a newline split one row across two:\n%q",
			len(rows), len(lines), buf.String())
	}
	for i, line := range lines {
		fields := strings.Split(line, "\t")
		if len(fields) != 3 {
			t.Fatalf("line %d has %d tab-separated fields, want 3 — an embedded tab shifted the columns: %q", i, len(fields), line)
		}
		if strings.ContainsAny(line, "\r") {
			t.Fatalf("line %d still carries a bare CR: %q", i, line)
		}
	}
	// The escapes are the documented PostgreSQL COPY TEXT set, and reversible.
	if got := lines[1]; got != `tab\there`+"\t2\tx" {
		t.Fatalf("tab escape = %q", got)
	}
	if got := lines[2]; got != `line\none\nline\ntwo`+"\t3\ty" {
		t.Fatalf("newline escape = %q", got)
	}
	if got := lines[3]; got != `carriage\rreturn`+"\t4\tz" {
		t.Fatalf("CR escape = %q", got)
	}
	if got := lines[4]; got != `back\\slash`+"\t5\tw" {
		t.Fatalf("backslash escape = %q — the escape character itself must be escaped or the mapping is not reversible", got)
	}
	// A comma is not special in TSV and must not be touched.
	if !strings.HasPrefix(lines[5], "V TRANS, V XPRESS & V LOGIS\t") {
		t.Fatalf("TSV needlessly mangled a comma: %q", lines[5])
	}
}

// An ordinary value must pass through byte for byte: escaping that fires when it
// does not need to is its own kind of wrong answer.
func TestTSVLeavesOrdinaryValuesAlone(t *testing.T) {
	for _, s := range []string{
		"", "ORGV000044", "1074316124.550000", "2026-07-30", "NULL",
		"V TRANS, V XPRESS & V LOGIS", `He said "hi"`, "श्री", "a b  c",
	} {
		if got := tsvEscape(s); got != s {
			t.Fatalf("tsvEscape(%q) = %q, want it untouched", s, got)
		}
	}
}

// --- CLI wiring ----------------------------------------------------------------

// FINDING (P3): the CLI opts out of the row cap, byte cap and statement deadline
// but NOT the 8 KiB LobLimit, which hana.New applies by default to a zero-value
// Options — so a 40 KB NCLOB came back as 8205 bytes ending " …[clipped]", and
// `hana-sql "SELECT DEFINITION FROM SYS.VIEWS …"` silently handed a human a
// fragment where the old CLI had no length limit.
//
// This is a source-level assertion because the behaviour needs a database; the
// value semantics are proved in internal/hana's TestNegativeLobLimitMeansNoLimit.
func TestCLIOptsOutOfTheLobCap(t *testing.T) {
	src := readSource(t, "main.go")
	i := strings.Index(src, "hana.New(cfg, hana.Options{")
	if i < 0 {
		t.Fatal("could not find the CLI's hana.New call in main.go")
	}
	block := src[i:]
	if j := strings.Index(block, "})"); j > 0 {
		block = block[:j]
	}
	if !strings.Contains(block, "LobLimit:") {
		t.Fatalf("the CLI's hana.Options sets no LobLimit, so the 8 KiB default applies and a human silently gets a clipped LOB:\n%s", block)
	}
	if !strings.Contains(block, "LobLimit:      -1") && !strings.Contains(block, "LobLimit: -1") {
		t.Fatalf("the CLI's LobLimit is not -1 (\"no limit\"):\n%s", block)
	}
}

// The three HTTP hardening controls must be reachable from the command line, or
// a deployment that needs them cannot have them.
func TestMCPSubcommandExposesTheHTTPHardeningFlags(t *testing.T) {
	_, _, stderr := runCLI(t, "", "mcp", "-h")
	for _, flag := range []string{"-allow-origin", "-allow-host", "-auth-token"} {
		if !strings.Contains(stderr, flag) {
			t.Fatalf("`hana-sql mcp -h` does not advertise %s:\n%s", flag, stderr)
		}
	}
}

// -csv must still be accepted and must now name what it emits.
func TestCSVFlagIsDocumentedAsRFC4180(t *testing.T) {
	_, _, stderr := runCLI(t, "", "-h")
	if !strings.Contains(stderr, "RFC 4180") {
		t.Fatalf("-csv is not documented as RFC 4180 CSV, so a user cannot know quoting applies:\n%s", stderr)
	}
}

func readSource(t *testing.T, name string) string {
	t.Helper()
	b, err := os.ReadFile(name)
	if err != nil {
		t.Fatalf("read %s: %v", name, err)
	}
	return string(b)
}

// --- documentation ---------------------------------------------------------------

// Several findings were doc-vs-behaviour mismatches, not code defects: MCP.md
// asserted "Timestamps with a clock -> RFC3339Nano" with no caveat, advertised
// hana_tables as "search all three companies at once", offered loopback binding
// as the mitigation for a browser, and quoted a banned-keyword count. A doc that
// confidently describes behaviour the code does not have is the same class of
// wrong answer as a bad number, so it is pinned here.
func TestDocsMatchTheShippedBehaviour(t *testing.T) {
	mcpDoc := readSource(t, "MCP.md")
	readme := readSource(t, "README.md")

	mustNot := []struct{ doc, name, text string }{
		{mcpDoc, "MCP.md", "Timestamps with a clock → **RFC3339Nano**"},
		{mcpDoc, "MCP.md", "search all three companies at once"},
		{mcpDoc, "MCP.md", "| 3 | `internal/guard/guard.go` | 32 banned keywords"},
		{readme, "README.md", "32 keywords are refused anywhere"},
	}
	for _, c := range mustNot {
		if strings.Contains(c.doc, c.text) {
			t.Errorf("%s still claims %q, which the code no longer does", c.name, c.text)
		}
	}

	must := []struct{ doc, name, text string }{
		{mcpDoc, "MCP.md", "with NO zone suffix"},
		{mcpDoc, "MCP.md", "33 banned keywords"},
		{mcpDoc, "MCP.md", "`NEXTVAL` is banned at layer 3"},
		{mcpDoc, "MCP.md", "PARTIAL CATALOG"},
		{mcpDoc, "MCP.md", "An unknown `schema` is an ERROR"},
		{mcpDoc, "MCP.md", "Loopback binding is not the mitigation"},
		{mcpDoc, "MCP.md", "--allow-origin"},
		{mcpDoc, "MCP.md", "--auth-token"},
		{mcpDoc, "MCP.md", "`null`, not `0`"},
		{mcpDoc, "MCP.md", "blocking for a gateway rollout"},
		{readme, "README.md", "33 keywords are refused anywhere"},
		{readme, "README.md", "NEXTVAL` is **a write dressed as a SELECT**"},
		{readme, "README.md", "RFC 4180"},
		{readme, "README.md", "BLOCKING for a gateway rollout"},
	}
	for _, c := range must {
		if !strings.Contains(c.doc, c.text) {
			t.Errorf("%s does not document %q", c.name, c.text)
		}
	}
}
