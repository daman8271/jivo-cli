package mcpsrv

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"time"

	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
)

// Tool names are hana_* on purpose. Behind the JIVO MCP gateway this backend is
// registered with Prefix == StripPrefix == "hana_", which makes the rename the
// identity in both directions — so the names read correctly standalone AND
// through the gateway, with no hana_hana_ stutter.
const (
	ToolQuery   = "hana_query"
	ToolTables  = "hana_tables"
	ToolColumns = "hana_columns"
	ToolDoctor  = "hana_doctor"
)

// ToolNames is the advertised order of tools/list.
var ToolNames = []string{ToolQuery, ToolTables, ToolColumns, ToolDoctor}

func strProp(desc string) map[string]any {
	return map[string]any{"type": "string", "description": desc}
}
func intProp(desc string) map[string]any {
	return map[string]any{"type": "integer", "description": desc}
}
func boolProp(desc string) map[string]any {
	return map[string]any{"type": "boolean", "description": desc}
}

// objectSchema builds a JSON Schema that forbids extra properties.
//
// additionalProperties:false is half of the fix for the benchmark's most
// dangerous defect: a tool that ACCEPTS company/companyDB/db/database, silently
// ignores it, and returns Oil's rows as though they answered a question about
// Beverages. The other half is DisallowUnknownFields at decode time, because a
// schema is advice and the decoder is enforcement.
func objectSchema(props map[string]any, required ...string) map[string]any {
	if props == nil {
		props = map[string]any{}
	}
	schema := map[string]any{
		"type":                 "object",
		"properties":           props,
		"additionalProperties": false,
	}
	if len(required) > 0 {
		schema["required"] = required
	}
	return schema
}

// ToolDefs is tools/list. The full crib sheet lives in hana_query only; the
// other three stay short because the gateway already advertises ~75 tools.
func (s *Server) ToolDefs() []map[string]any {
	lim := s.limits()
	return []map[string]any{
		{
			"name":        ToolQuery,
			"description": QueryFacts(lim.MaxRows, lim.Timeout),
			"inputSchema": objectSchema(map[string]any{
				"sql": strProp("One read-only SQL statement (SELECT or WITH). Qualify every table as \"SCHEMA\".\"TABLE\" — that is how you reach Oil, Mart or Beverages. There is no company parameter."),
				"max_rows": intProp(fmt.Sprintf(
					"Row cap for this call. May only lower the server cap of %d, never raise it.", lim.MaxRows)),
				"timeout_ms": intProp(fmt.Sprintf(
					"Statement timeout in milliseconds. May only lower the server default of %s.", lim.Timeout)),
			}, "sql"),
		},
		{
			"name":        ToolTables,
			"description": TablesFacts(),
			"inputSchema": objectSchema(map[string]any{
				"schema": strProp("One of JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB. Omit to search all three. " +
					"A schema that is not one of these (or a SYS/_SYS_* catalog schema) is an ERROR, never an empty result."),
				"like":          strProp("Case-insensitive SQL LIKE pattern on the table name, e.g. 'OIN%' or '%INV%'."),
				"include_views": boolProp("Also list views (default false)."),
				"offset": intProp(fmt.Sprintf(
					"Skip this many rows. The listing is ordered by schema then name and caps at %d rows, so an unfiltered three-company listing is only the first page — the note tells you the offset to pass next.", lim.MaxRows)),
				"no_row_counts": boolProp("Skip the live row counts (the SYS.M_TABLES join). Much faster for a broad listing; row_count comes back null."),
			}),
		},
		{
			"name":        ToolColumns,
			"description": ColumnsFacts(),
			"inputSchema": objectSchema(map[string]any{
				"schema": strProp("JIVO_OIL_HANADB, JIVO_MART_HANADB or JIVO_BEVERAGES_HANADB (required)."),
				"table":  strProp("Table or view name, e.g. OINV (required)."),
				"like":   strProp("Case-insensitive LIKE pattern to filter column names."),
			}, "schema", "table"),
		},
		{
			"name":        ToolDoctor,
			"description": DoctorFacts(),
			"inputSchema": objectSchema(nil),
		},
	}
}

func (s *Server) limits() hana.Limits {
	if s.DB == nil {
		return hana.Limits{MaxRows: hana.DefaultMaxRows, MaxBytes: hana.DefaultMaxBytes, Timeout: hana.DefaultTimeout}
	}
	return s.DB.Limits()
}

// --- tools/call ---------------------------------------------------------------

// callTool runs one tools/call. ctx is the TRANSPORT's context — an HTTP client
// that disconnects, or a gateway that times out, must be able to cancel the
// query it started; it used to be context.Background(), so nothing upstream
// could stop a call once it was queued.
func (s *Server) callTool(ctx context.Context, params json.RawMessage) map[string]any {
	var call struct {
		Name      string          `json:"name"`
		Arguments json.RawMessage `json:"arguments"`
	}
	if len(params) > 0 {
		if err := json.Unmarshal(params, &call); err != nil {
			return toolResult("invalid tool-call params: "+cleanJSONError(err), true)
		}
	}
	text, isErr := s.Dispatch(ctx, call.Name, call.Arguments)
	return toolResult(text, isErr)
}

func toolResult(text string, isErr bool) map[string]any {
	return map[string]any{
		"content": []map[string]any{{"type": "text", "text": text}},
		"isError": isErr,
	}
}

// decodeArgs unmarshals tool arguments strictly. An unrecognised argument is an
// ERROR, never a silent discard.
//
// The key check is done by hand against the struct's json tags because
// encoding/json matches field names CASE-INSENSITIVELY: {"SQL": …} and
// {"MAX_ROWS": 5} decoded happily even though the advertised inputSchema says
// additionalProperties:false and lists only sql/max_rows. That inverted the
// stated design — schema is advice, decoder is enforcement — by leaving the
// decoder looser than the schema it is supposed to enforce.
func decodeArgs(raw json.RawMessage, dst any) error {
	trimmed := bytes.TrimSpace(raw)
	if len(trimmed) == 0 || string(trimmed) == "null" {
		return nil
	}
	allowed := jsonFieldNames(dst)
	if trimmed[0] != '{' {
		return fmt.Errorf("invalid arguments: this tool takes a JSON OBJECT of named arguments%s, not %s",
			argListSuffix(allowed), jsonKind(trimmed))
	}
	var probe map[string]json.RawMessage
	if err := json.Unmarshal(trimmed, &probe); err != nil {
		return fmt.Errorf("invalid arguments: %s", cleanJSONError(err))
	}
	for k := range probe {
		if !allowed[k] {
			return argNameError(k, allowed)
		}
	}
	dec := json.NewDecoder(bytes.NewReader(trimmed))
	dec.DisallowUnknownFields()
	if err := dec.Decode(dst); err != nil {
		return argError(err, allowed)
	}
	return nil
}

// jsonFieldNames returns the exact json tag names dst accepts.
func jsonFieldNames(dst any) map[string]bool {
	out := map[string]bool{}
	t := reflect.TypeOf(dst)
	for t != nil && t.Kind() == reflect.Pointer {
		t = t.Elem()
	}
	if t == nil || t.Kind() != reflect.Struct {
		return out
	}
	for i := 0; i < t.NumField(); i++ {
		name, _, _ := strings.Cut(t.Field(i).Tag.Get("json"), ",")
		if name != "" && name != "-" {
			out[name] = true
		}
	}
	return out
}

func sortedNames(allowed map[string]bool) []string {
	out := make([]string, 0, len(allowed))
	for k := range allowed {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

func argListSuffix(allowed map[string]bool) string {
	if len(allowed) == 0 {
		return " (this tool takes none)"
	}
	return " (" + strings.Join(sortedNames(allowed), ", ") + ")"
}

// jsonKind names what the caller sent, without quoting a payload back at them.
func jsonKind(b []byte) string {
	switch b[0] {
	case '[':
		return "an array"
	case '"':
		return "a string"
	case 't', 'f':
		return "a boolean"
	case 'n':
		return "null"
	}
	return "a number"
}

// argError turns json's terse "unknown field" into an answer to the question
// the caller was actually asking.
func argError(err error, allowed map[string]bool) error {
	msg := err.Error()
	if !strings.Contains(msg, "unknown field") {
		return fmt.Errorf("invalid arguments: %s", cleanJSONError(err))
	}
	name := ""
	if i := strings.Index(msg, `"`); i >= 0 {
		if j := strings.Index(msg[i+1:], `"`); j >= 0 {
			name = msg[i+1 : i+1+j]
		}
	}
	return argNameError(name, allowed)
}

// argNameError is the refusal for an argument this tool does not have.
func argNameError(name string, allowed map[string]bool) error {
	hint := ""
	switch strings.ToLower(name) {
	case "company", "companydb", "company_db", "db", "database", "schema":
		hint = " There is no company/database parameter on this tool, and it will NOT be applied silently: " +
			"choose the company by qualifying the table name instead, e.g. \"JIVO_BEVERAGES_HANADB\".\"OINV\"."
	}
	for want := range allowed {
		if strings.EqualFold(want, name) && want != name {
			hint += fmt.Sprintf(" Argument names are case-sensitive — did you mean %q?", want)
			break
		}
	}
	return fmt.Errorf("unrecognised argument %q — refusing rather than ignoring it, because a silently discarded "+
		"parameter returns the wrong company's numbers with no tell. Valid arguments%s.%s",
		name, argListSuffix(allowed), hint)
}

// cleanJSONError keeps encoding/json's diagnosis but drops the Go internals it
// carries. Feeding a model `json: cannot unmarshal string into Go value of type
// struct { SQL string "json:\"sql\"" ; … }` hands it this program's private
// shape instead of an answer about its own request.
func cleanJSONError(err error) string {
	msg := err.Error()
	if i := strings.Index(msg, " into Go struct field "); i >= 0 {
		rest := msg[i+len(" into Go struct field "):]
		field := rest
		if j := strings.Index(rest, " of type "); j >= 0 {
			field = rest[:j]
		}
		if _, after, ok := strings.Cut(field, "."); ok {
			field = after
		}
		return msg[:i] + " for argument " + strconv.Quote(field)
	}
	if i := strings.Index(msg, " into Go value of type "); i >= 0 {
		return msg[:i]
	}
	return msg
}

// Dispatch runs one tool and returns (text, isError). It never panics; every
// failure comes back as isError text so the JSON-RPC loop keeps running.
//
// Argument validation always happens BEFORE the database is touched.
func (s *Server) Dispatch(ctx context.Context, name string, rawArgs json.RawMessage) (string, bool) {
	switch name {
	case ToolQuery:
		var a struct {
			SQL       string `json:"sql"`
			MaxRows   int    `json:"max_rows"`
			TimeoutMS int    `json:"timeout_ms"`
		}
		if err := decodeArgs(rawArgs, &a); err != nil {
			return err.Error(), true
		}
		if strings.TrimSpace(a.SQL) == "" {
			return "missing required argument: sql", true
		}
		if a.MaxRows < 0 || a.TimeoutMS < 0 {
			return "max_rows and timeout_ms must not be negative", true
		}
		db, err := s.db()
		if err != nil {
			return err.Error(), true
		}
		lim := hana.Limits{MaxRows: a.MaxRows, Timeout: time.Duration(a.TimeoutMS) * time.Millisecond}
		res, qerr := db.QueryReadOnly(ctx, guard.MCPPolicy, lim, a.SQL)
		return s.envelope(res, qerr, db.Limits().MaxRows)

	case ToolTables:
		var a struct {
			Schema       string `json:"schema"`
			Like         string `json:"like"`
			IncludeViews bool   `json:"include_views"`
			Offset       int    `json:"offset"`
			NoRowCounts  bool   `json:"no_row_counts"`
		}
		if err := decodeArgs(rawArgs, &a); err != nil {
			return err.Error(), true
		}
		if a.Offset < 0 {
			return "offset must not be negative", true
		}
		db, err := s.db()
		if err != nil {
			return err.Error(), true
		}
		res, qerr := db.Tables(ctx, hana.TableQuery{
			Schema:       a.Schema,
			Like:         a.Like,
			IncludeViews: a.IncludeViews,
			Offset:       a.Offset,
			NoRowCounts:  a.NoRowCounts,
		})
		return s.envelope(res, qerr, db.Limits().MaxRows)

	case ToolColumns:
		var a struct {
			Schema string `json:"schema"`
			Table  string `json:"table"`
			Like   string `json:"like"`
		}
		if err := decodeArgs(rawArgs, &a); err != nil {
			return err.Error(), true
		}
		if strings.TrimSpace(a.Schema) == "" {
			return "missing required argument: schema (one of " + strings.Join(hana.Schemas, ", ") + ")", true
		}
		if strings.TrimSpace(a.Table) == "" {
			return "missing required argument: table", true
		}
		db, err := s.db()
		if err != nil {
			return err.Error(), true
		}
		res, qerr := db.Columns(ctx, a.Schema, a.Table, a.Like)
		return s.envelope(res, qerr, db.Limits().MaxRows)

	case ToolDoctor:
		var a struct{}
		if err := decodeArgs(rawArgs, &a); err != nil {
			return err.Error(), true
		}
		return s.doctor(ctx)

	case "":
		return "missing tool name", true

	default:
		return "unknown tool: " + name, true
	}
}

func (s *Server) db() (*hana.DB, error) {
	if s.DB == nil {
		return nil, fmt.Errorf("no HANA connection configured on this server")
	}
	return s.DB, nil
}

// --- response envelope --------------------------------------------------------

type envelope struct {
	AsOf       string `json:"as_of"`
	AsOfSource string `json:"as_of_source"`
	ElapsedMS  int64  `json:"elapsed_ms"`
	RowCount   int    `json:"row_count"`
	// MaxRows is a pointer so "no row cap" is null, not 0. `--max-rows 0` means
	// unlimited, and reporting "max_rows": 0 reads as "zero rows permitted" —
	// the opposite of the truth.
	MaxRows   *int             `json:"max_rows"`
	Truncated bool             `json:"truncated"`
	Columns   []hana.Column    `json:"columns"`
	Rows      []map[string]any `json:"rows"`
	Note      string           `json:"note,omitempty"`
}

// envelope marshals one result (or one error) into the tool's text payload.
func (s *Server) envelope(res *hana.Result, err error, maxRows int) (string, bool) {
	if err != nil {
		return s.scrub(err.Error()), true
	}
	e := envelope{
		AsOf:       s.now().Format(time.RFC3339),
		AsOfSource: "mcp-host-clock",
		ElapsedMS:  res.Elapsed.Milliseconds(),
		RowCount:   res.RowCount,
		Truncated:  res.Truncated,
		Columns:    res.Columns,
		Rows:       res.Rows,
		Note:       res.Note,
	}
	if maxRows > 0 {
		e.MaxRows = &maxRows
	} else {
		e.Note = joinNote(e.Note, "max_rows is null: no row cap is in force on this server, so this answer is complete")
	}
	b, merr := json.Marshal(e)
	if merr != nil {
		return "could not encode result: " + merr.Error(), true
	}
	return string(b), false
}

// scrub keeps a credential out of any error text that leaves the process.
func (s *Server) scrub(msg string) string {
	if s.DB == nil || s.DB.Config() == nil {
		return msg
	}
	return s.DB.Config().Scrub(msg)
}

// --- hana_doctor --------------------------------------------------------------

type check struct {
	Name   string `json:"name"`
	OK     bool   `json:"ok"`
	Detail string `json:"detail,omitempty"`
	Hint   string `json:"hint,omitempty"`
}

type readOnlyInfo struct {
	FirstTokenAllowlist []string `json:"first_token_allowlist"`
	SingleStatement     bool     `json:"single_statement"`
	BannedTokens        int      `json:"banned_tokens"`
	Transaction         string   `json:"transaction"`
	// TransactionProof states how well layer 4 is actually established. It is
	// here because "READ ONLY, always rolled back" describes what this client
	// ASKS for, and a reader is entitled to know that the ask has never been
	// observed to reject anything.
	TransactionProof string `json:"transaction_proof"`
	MaxRows          int    `json:"max_rows"`
	Timeout          string `json:"timeout"`
	MaxConcurrent    int    `json:"max_concurrent"`
}

// transactionProof is the honest state of the layer-4 evidence.
const transactionProof = "UNPROVEN: HANA accepts `set transaction read only` (BeginTx succeeds) but resolves object names before applying the access mode, so a probe against a non-existent table returns the same error with or without it. On HANA 2.00.059 SYS.M_TRANSACTIONS exposes no ACCESS_MODE column, so there is no read-only way to confirm the mode took effect, and proving it any other way would mean sending a real write at a real table. Layers 0-3 are load-bearing on their own; the dedicated SELECT-only HANA user is the only thing that turns this into a database-enforced guarantee."

// maxClockSkew is how far apart the host and HANA clocks may be before the
// doctor calls it a fault. Every envelope's as_of comes from the host clock, so
// a drifting host silently mis-stamps every answer it gives.
const maxClockSkew = 2 * time.Minute

type doctorReport struct {
	OK          bool              `json:"ok"`
	AsOf        string            `json:"as_of"`
	ServerTime  string            `json:"server_time,omitempty"`
	ClockSkewMS int64             `json:"clock_skew_ms,omitempty"`
	EnvFile     string            `json:"env_file"`
	Host        string            `json:"host"`
	User        string            `json:"user"`
	Password    string            `json:"password"`
	TLS         string            `json:"tls"`
	HanaVersion string            `json:"hana_version,omitempty"`
	Schemas     []hana.SchemaInfo `json:"schemas,omitempty"`
	ReadOnly    readOnlyInfo      `json:"read_only"`
	Checks      []check           `json:"checks"`
}

// doctor never attempts a write to "self-test" the read-only backstop, and
// never returns a credential value.
func (s *Server) doctor(ctx context.Context) (string, bool) {
	db, err := s.db()
	if err != nil {
		return err.Error(), true
	}
	cfg := db.Config()
	lim := db.Limits()

	rep := doctorReport{
		OK:      true,
		AsOf:    s.now().Format(time.RFC3339),
		EnvFile: cfg.EnvFile,
		Host:    cfg.Addr(),
		User:    cfg.User,
		ReadOnly: readOnlyInfo{
			FirstTokenAllowlist: guard.MCPPolicy.AllowFirst,
			SingleStatement:     true,
			BannedTokens:        len(guard.BannedTokens()),
			Transaction:         "READ ONLY, always rolled back",
			TransactionProof:    transactionProof,
			MaxRows:             lim.MaxRows,
			Timeout:             lim.Timeout.String(),
			MaxConcurrent:       db.MaxConcurrent(),
		},
	}
	rep.Password = cfg.MaskedPassword()
	// Where the credentials came from, as a sentence that reads correctly in
	// both cases rather than interpolating a parenthetical into "resolved from".
	credSource := "the process environment (no env file was used)"
	if rep.EnvFile == "" {
		rep.EnvFile = "(none — credentials came from the process environment)"
	} else {
		credSource = "the env file " + rep.EnvFile
	}

	// config
	if cerr := cfg.Validate(); cerr != nil {
		rep.OK = false
		rep.Checks = append(rep.Checks, check{Name: "config", OK: false, Detail: cerr.Error(),
			Hint: "set HANA_HOST / HANA_USER / HANA_PASSWORD in the env file or the process environment"})
		out, _ := json.Marshal(rep)
		return string(out), true
	}
	rep.Checks = append(rep.Checks, check{Name: "config", OK: true, Detail: "credentials resolved from " + credSource})

	// tcp
	conn, terr := net.DialTimeout("tcp", cfg.Addr(), 5*time.Second)
	if terr != nil {
		rep.OK = false
		rep.Checks = append(rep.Checks, check{Name: "tcp", OK: false, Detail: s.scrub(terr.Error()),
			Hint: "inside a container HANA is reached at 172.16.1.1:30015 via the hana-bridge, NOT the host's 127.0.0.1:47301"})
	} else {
		conn.Close()
		rep.Checks = append(rep.Checks, check{Name: "tcp", OK: true, Detail: "reachable at " + cfg.Addr()})
	}

	// connect + identity + schemas
	id, ierr := db.Identify(ctx)
	if ierr != nil {
		rep.OK = false
		rep.Checks = append(rep.Checks, check{Name: "connect", OK: false, Detail: s.scrub(ierr.Error()),
			Hint: "the office reverse tunnel may be down; retry, then check the tunnel"})
		out, _ := json.Marshal(rep)
		return string(out), true
	}
	rep.TLS = db.Mode()
	rep.HanaVersion = id.Version
	rep.ServerTime = id.ServerUTC
	if id.SkewKnown {
		rep.ClockSkewMS = id.ClockSkew.Milliseconds()
	}
	rep.Schemas = id.SchemaRows
	rep.Checks = append(rep.Checks,
		check{Name: "connect", OK: true, Detail: "connected (" + rep.TLS + ")"},
		check{Name: "identity", OK: true, Detail: "logged in as " + id.User + ", default schema " + id.Schema})

	readable := 0
	for _, sc := range id.SchemaRows {
		if sc.Readable {
			readable++
		}
	}
	schemaOK := readable == len(hana.Schemas)
	if !schemaOK {
		rep.OK = false
	}
	rep.Checks = append(rep.Checks, check{
		Name:   "schemas",
		OK:     schemaOK,
		Detail: fmt.Sprintf("%d of %d company schemas readable", readable, len(hana.Schemas)),
		Hint:   hintIf(!schemaOK, "the login may lack SELECT on one company schema"),
	})

	// clock — the skew was already measured and then thrown away. as_of on every
	// answer comes from THIS host's clock, so drift here mis-stamps every reply.
	rep.Checks = append(rep.Checks, s.clockCheck(id.SkewKnown, id.ClockSkew))
	if !last(rep.Checks).OK {
		rep.OK = false
	}

	out, merr := json.Marshal(rep)
	if merr != nil {
		return "could not encode doctor report: " + merr.Error(), true
	}
	return string(out), !rep.OK
}

// clockCheck turns the measured skew into a verdict.
func (s *Server) clockCheck(known bool, skew time.Duration) check {
	if !known {
		return check{Name: "clock", OK: true,
			Detail: "server time could not be parsed, so clock skew is unknown; as_of comes from this host's clock"}
	}
	ahead := "ahead of"
	if skew < 0 {
		ahead = "behind"
	}
	detail := fmt.Sprintf("this host is %s %s HANA (skew %s); as_of on every answer comes from this host's clock",
		absDuration(skew).Round(time.Millisecond), ahead, skew.Round(time.Millisecond))
	if absDuration(skew) <= maxClockSkew {
		return check{Name: "clock", OK: true, Detail: detail}
	}
	return check{Name: "clock", OK: false, Detail: detail,
		Hint: fmt.Sprintf("skew exceeds %s — fix NTP on this host; until then treat every as_of stamp as wrong by about that much", maxClockSkew)}
}

func absDuration(d time.Duration) time.Duration {
	if d < 0 {
		return -d
	}
	return d
}

func last(cs []check) check { return cs[len(cs)-1] }

func joinNote(existing, add string) string {
	if existing == "" {
		return add
	}
	return existing + "; " + add
}

func hintIf(cond bool, hint string) string {
	if cond {
		return hint
	}
	return ""
}
