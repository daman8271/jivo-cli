package cli

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"

	"postsql/internal/db"
)

func init() { register(newMcpCmd) }

// --- JSON-RPC 2.0 wire types --------------------------------------------------

type mcpRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"` // absent => notification
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

type mcpResponse struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Result  any             `json:"result,omitempty"`
	Error   *mcpRPCError    `json:"error,omitempty"`
}

type mcpRPCError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

func newMcpCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "mcp",
		Short: "Run a Model Context Protocol server over stdio (for AI clients)",
		Long: "Serve this read-only PostgreSQL connection to MCP-aware AI clients\n" +
			"(Claude Desktop / Claude Code) as newline-delimited JSON-RPC 2.0 over\n" +
			"stdio. Reads one request per line on stdin, writes one response per line\n" +
			"on stdout, and logs only to stderr. Exposes tools: postgres_query,\n" +
			"list_databases, list_tables, describe_table, search, schema_dump.",
		Example: "  postsql mcp   # add to a client's mcpServers config as the command",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return mcpServe(app, os.Stdin, os.Stdout)
		},
	}
}

// mcpServe runs the stdio JSON-RPC loop until stdin closes.
func mcpServe(app *App, in io.Reader, out io.Writer) error {
	fmt.Fprintln(os.Stderr, "postsql: MCP server ready on stdio")

	reader := bufio.NewReader(in)
	writer := bufio.NewWriter(out)
	defer writer.Flush()

	for {
		line, err := reader.ReadBytes('\n')
		trimmed := strings.TrimSpace(string(line))
		if trimmed != "" {
			mcpHandleLine(app, writer, []byte(trimmed))
		}
		if err != nil {
			if err == io.EOF {
				return nil
			}
			fmt.Fprintln(os.Stderr, "postsql: read error:", err)
			return nil
		}
	}
}

// mcpHandleLine parses one JSON-RPC line and dispatches it, writing at most one
// response object (plus newline). Parse errors are logged to stderr; the loop
// never crashes.
func mcpHandleLine(app *App, w *bufio.Writer, line []byte) {
	var req mcpRequest
	if err := json.Unmarshal(line, &req); err != nil {
		fmt.Fprintln(os.Stderr, "postsql: parse error:", err)
		return
	}

	// Notifications (id absent, or any notifications/* method) get no response.
	isNotification := len(req.ID) == 0 || strings.HasPrefix(req.Method, "notifications/")

	switch req.Method {
	case "initialize":
		if isNotification {
			return
		}
		mcpWrite(app, w, req.ID, mcpInitializeResult(req.Params), nil)

	case "ping":
		if isNotification {
			return
		}
		mcpWrite(app, w, req.ID, struct{}{}, nil)

	case "tools/list":
		if isNotification {
			return
		}
		mcpWrite(app, w, req.ID, map[string]any{"tools": mcpToolDefs()}, nil)

	case "tools/call":
		if isNotification {
			return
		}
		mcpWrite(app, w, req.ID, mcpCallTool(app, req.Params), nil)

	default:
		if isNotification {
			return // silently ignore notifications/* and other id-less messages
		}
		mcpWrite(app, w, req.ID, nil, &mcpRPCError{
			Code:    -32601,
			Message: "method not found: " + req.Method,
		})
	}
}

// mcpWrite marshals and emits exactly one JSON-RPC response line.
func mcpWrite(app *App, w *bufio.Writer, id json.RawMessage, result any, rpcErr *mcpRPCError) {
	resp := mcpResponse{JSONRPC: "2.0", ID: id, Result: result, Error: rpcErr}
	b, err := json.Marshal(resp)
	if err != nil {
		fmt.Fprintln(os.Stderr, "postsql: marshal error:", err)
		return
	}
	w.Write(b)
	w.WriteByte('\n')
	w.Flush()
}

// mcpInitializeResult echoes the client's protocolVersion (or a default).
func mcpInitializeResult(params json.RawMessage) map[string]any {
	protocol := "2024-11-05"
	if len(params) > 0 {
		var p struct {
			ProtocolVersion string `json:"protocolVersion"`
		}
		if json.Unmarshal(params, &p) == nil && p.ProtocolVersion != "" {
			protocol = p.ProtocolVersion
		}
	}
	return map[string]any{
		"protocolVersion": protocol,
		"capabilities":    map[string]any{"tools": map[string]any{}},
		"serverInfo":      map[string]any{"name": "postsql", "version": "0.1.0"},
	}
}

// --- tools/list ---------------------------------------------------------------

func mcpStrProp(desc string) map[string]any {
	return map[string]any{"type": "string", "description": desc}
}

func mcpObjectSchema(props map[string]any, required ...string) map[string]any {
	if props == nil {
		props = map[string]any{}
	}
	schema := map[string]any{"type": "object", "properties": props}
	if len(required) > 0 {
		schema["required"] = required
	}
	return schema
}

func mcpToolDefs() []map[string]any {
	return []map[string]any{
		{
			"name":        "postgres_query",
			"description": "Run a read-only SQL query (SELECT/WITH/EXPLAIN/SHOW/TABLE/VALUES) and return the rows as JSON. Writes are rejected.",
			"inputSchema": mcpObjectSchema(map[string]any{
				"sql":      mcpStrProp("The read-only SQL statement to execute."),
				"database": mcpStrProp("Target database (optional; defaults to the active database)."),
			}, "sql"),
		},
		{
			"name":        "list_databases",
			"description": "List all databases in the cluster with size, owner, and encoding.",
			"inputSchema": mcpObjectSchema(nil),
		},
		{
			"name":        "list_tables",
			"description": "List tables in a database with estimated row counts and on-disk size.",
			"inputSchema": mcpObjectSchema(map[string]any{
				"database": mcpStrProp("Target database (optional; defaults to the active database)."),
				"schema":   mcpStrProp("Restrict to a single schema (optional; default: all user schemas)."),
			}),
		},
		{
			"name":        "describe_table",
			"description": "Show a table's columns with type, nullability, default, and primary-key flag. Accepts an optional schema qualifier (schema.table).",
			"inputSchema": mcpObjectSchema(map[string]any{
				"table":    mcpStrProp("Table name, optionally schema-qualified as schema.table (defaults to public)."),
				"database": mcpStrProp("Target database (optional; defaults to the active database)."),
			}, "table"),
		},
		{
			"name":        "search",
			"description": "Find schemas/tables/columns whose name matches a case-insensitive substring.",
			"inputSchema": mcpObjectSchema(map[string]any{
				"term":     mcpStrProp("Case-insensitive substring to match against catalog names."),
				"database": mcpStrProp("Target database (optional; defaults to the active database)."),
			}, "term"),
		},
		{
			"name":        "schema_dump",
			"description": "Dump every user table's columns (schema, table, column, type, position) for a database.",
			"inputSchema": mcpObjectSchema(map[string]any{
				"database": mcpStrProp("Target database (optional; defaults to the active database)."),
			}),
		},
	}
}

// --- tools/call ---------------------------------------------------------------

func mcpCallTool(app *App, params json.RawMessage) map[string]any {
	var call struct {
		Name      string          `json:"name"`
		Arguments json.RawMessage `json:"arguments"`
	}
	if len(params) > 0 {
		if err := json.Unmarshal(params, &call); err != nil {
			return mcpToolResult("invalid tool-call params: "+err.Error(), true)
		}
	}

	text, isErr := mcpDispatch(app, call.Name, call.Arguments)
	return mcpToolResult(text, isErr)
}

func mcpToolResult(text string, isErr bool) map[string]any {
	return map[string]any{
		"content": []map[string]any{{"type": "text", "text": text}},
		"isError": isErr,
	}
}

// mcpDispatch runs the named tool and returns (text, isError). It never panics;
// query errors are returned as isError text so the JSON-RPC loop keeps running.
func mcpDispatch(app *App, name string, rawArgs json.RawMessage) (string, bool) {
	var args struct {
		SQL      string `json:"sql"`
		Database string `json:"database"`
		Schema   string `json:"schema"`
		Table    string `json:"table"`
		Term     string `json:"term"`
	}
	if len(rawArgs) > 0 {
		if err := json.Unmarshal(rawArgs, &args); err != nil {
			return "invalid arguments: " + err.Error(), true
		}
	}

	dbName := app.DBName()
	if strings.TrimSpace(args.Database) != "" {
		dbName = args.Database
	}

	ctx, cancel := app.Ctx()
	defer cancel()

	switch name {
	case "postgres_query":
		if strings.TrimSpace(args.SQL) == "" {
			return "missing required argument: sql", true
		}
		return mcpRun(app, ctx, dbName, args.SQL)

	case "list_databases":
		const sql = `
			SELECT datname AS database,
			       pg_size_pretty(pg_database_size(datname)) AS size,
			       pg_catalog.pg_get_userbyid(datdba) AS owner,
			       pg_catalog.pg_encoding_to_char(encoding) AS encoding
			FROM pg_database
			WHERE NOT datistemplate
			ORDER BY pg_database_size(datname) DESC`
		return mcpRun(app, ctx, dbName, sql)

	case "list_tables":
		const sql = `
			SELECT n.nspname AS schema,
			       c.relname AS "table",
			       CASE WHEN c.reltuples < 0 THEN 'unknown'
			            ELSE to_char(c.reltuples, 'FM999,999,999,990')
			       END AS est_rows,
			       pg_size_pretty(pg_total_relation_size(c.oid)) AS size
			FROM pg_class c
			JOIN pg_namespace n ON n.oid = c.relnamespace
			WHERE c.relkind IN ('r', 'p')
			  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
			  AND n.nspname !~ '^pg_toast'
			  AND ($1 = '' OR n.nspname = $1)
			ORDER BY pg_total_relation_size(c.oid) DESC, n.nspname, c.relname`
		return mcpRun(app, ctx, dbName, sql, args.Schema)

	case "describe_table":
		if strings.TrimSpace(args.Table) == "" {
			return "missing required argument: table", true
		}
		schema, table := splitTableName(args.Table)
		if table == "" {
			return "empty table name", true
		}
		// Shared with the `describe` command: true Postgres types via
		// format_type on pg_attribute (not the information_schema flattening).
		return mcpRun(app, ctx, dbName, describeColumnsSQL, schema, table)

	case "search":
		if strings.TrimSpace(args.Term) == "" {
			return "missing required argument: term", true
		}
		const sql = `
			SELECT c.table_schema AS schema,
			       c.table_name   AS table,
			       c.column_name  AS column,
			       c.data_type    AS type
			FROM information_schema.columns c
			JOIN information_schema.tables t
			  ON t.table_schema = c.table_schema
			 AND t.table_name   = c.table_name
			WHERE t.table_type = 'BASE TABLE'
			  AND c.table_schema NOT IN ('pg_catalog', 'information_schema')
			  AND (c.table_schema ILIKE $1
			    OR c.table_name   ILIKE $1
			    OR c.column_name  ILIKE $1)
			ORDER BY c.table_schema, c.table_name, c.column_name`
		return mcpRun(app, ctx, dbName, sql, "%"+args.Term+"%")

	case "schema_dump":
		const sql = `
			SELECT c.table_schema   AS schema,
			       c.table_name     AS table,
			       c.column_name    AS column,
			       c.data_type      AS type,
			       c.ordinal_position AS position
			FROM information_schema.columns c
			JOIN information_schema.tables t
			  ON t.table_schema = c.table_schema
			 AND t.table_name   = c.table_name
			WHERE t.table_type = 'BASE TABLE'
			  AND c.table_schema NOT IN ('pg_catalog', 'information_schema')
			ORDER BY c.table_schema, c.table_name, c.ordinal_position`
		return mcpRun(app, ctx, dbName, sql)

	case "":
		return "missing tool name", true

	default:
		return "unknown tool: " + name, true
	}
}

// mcpRun executes a read-only query and returns its rows as a compact
// array-of-objects JSON string. On error it returns the error text and isError.
func mcpRun(app *App, ctx context.Context, dbName, sql string, qargs ...any) (string, bool) {
	res, err := app.DB.Query(ctx, dbName, sql, qargs...)
	if err != nil {
		return err.Error(), true
	}
	text, err := mcpResultJSON(res)
	if err != nil {
		return err.Error(), true
	}
	return text, false
}

// mcpResultJSON marshals a db.Result as a compact JSON array-of-objects.
func mcpResultJSON(res *db.Result) (string, error) {
	out := make([]map[string]any, 0, len(res.Rows))
	for _, row := range res.Rows {
		m := make(map[string]any, len(res.Columns))
		for i, col := range res.Columns {
			if i < len(row) {
				m[col] = mcpNorm(row[i])
			}
		}
		out = append(out, m)
	}
	b, err := json.Marshal(out)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

// mcpNorm converts a driver value to a JSON-friendly representation, mirroring
// the render package's normalization (text protocol => strings/[]byte).
func mcpNorm(v any) any {
	switch t := v.(type) {
	case nil:
		return nil
	case []byte:
		return string(t)
	case time.Time:
		return t.Format(time.RFC3339)
	default:
		return v
	}
}
