// Package mcp exposes the read-only dsr CLI as a Model Context Protocol (MCP)
// server, over stdio or streamable HTTP, so an AI agent can query JIVO's DSR
// field-sales system as a set of tools.
//
// READ-ONLY GUARANTEE. Three independent things have to hold, and each is
// checked by a test rather than asserted in a comment:
//
//  1. Every tool resolves to a literal argv into the dsr command tree, taken
//     from the hand-authored allowlist in tools.go. An action name that is not
//     in that table is an error, never a passthrough — so `dsr schema dump`,
//     the only dsr command that writes anything at all (files under --out, not
//     business data), is unreachable from here. Pinned by
//     TestRegisteredToolSetIsExactlyTheAllowlist.
//
//  2. Nothing in this package can itself write. readonly_guard_test.go parses
//     the AST of every file here and in cobratree/ and fails the build's tests
//     if any of them so much as names os.WriteFile, os.MkdirAll, os.Create,
//     ExecContext, or a non-GET HTTP verb.
//
//  3. The SQL that reaches the database is a single SELECT. dsr_query and the
//     `where` filter both run through db.GuardReadOnly, which rejects
//     comment-prefixed and multi-statement input (the child dsr process
//     applies the identical gate a second time, and runs everything inside a
//     transaction it always rolls back).
//
// Credentials are never echoed: the tools shell out to the same binary, which
// reads DSR_USER/DSR_PASSWORD from the environment, and no tool returns config.
package mcp

import (
	"context"
	"fmt"
	"strings"
	"time"

	mcplib "github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"

	"dsr/internal/db"
	"dsr/internal/mcp/cobratree"
)

// serverVersion is advertised to MCP clients during initialize.
const serverVersion = "1.0.0"

// defaultLimit bounds every row-returning tool when the caller does not say
// otherwise. DSR is big — 127k retailers, ~27M GPS breadcrumbs — and the CLI's
// own `query` is unbounded, so an un-capped tool call is a way to page a
// warehouse into a model's context.
const defaultLimit = 200

// maxResultBytes caps a tool result. Truncating JSON would hand the agent
// something that parses wrong rather than something that fails honestly, so an
// oversized result is an error that tells the caller how to make it smaller.
const maxResultBytes = 400_000

// cliTimeout bounds the child dsr process. The CLI's own per-query timeout is
// 30s; this is the outer bound for a command that makes several round trips.
const cliTimeout = 180 * time.Second

// instructions is the server-level guidance an MCP host shows the model once,
// so every tool description does not have to repeat it.
const instructions = "Read-only access to JIVO's DSR field-sales system (SQL Server database DSR_V6, plus the DSR web portal's own report endpoints). " +
	"Every tool is strictly read-only: nothing here can create, update or delete, and the one dsr command that writes files (schema dump) is not exposed. " +
	"Start with dsr_doctor to confirm the database is reachable, dsr_schema to find the right table, then the domain tools. " +
	"Most tools take an `action` that selects what to fetch — an unrecognised action is an error listing the valid ones, and unknown parameters are REJECTED rather than ignored. " +
	"DATES: `from` is inclusive, `to` is EXCLUSIVE, both YYYY-MM-DD — a full July is from=2026-07-01 to=2026-08-01. " +
	"ROWS: every row-returning tool is capped (default 200 rows) — raise `limit` deliberately and aggregate in SQL rather than pulling rows to count them; the *_count actions exist for that. " +
	"SOFT DELETES: DSR never hard-deletes, so tools exclude rows flagged deleted unless you pass include_deleted. " +
	"SALES VOCABULARY: PRIMARY sales are JIVO -> distributor (dsr_supply); SECONDARY sales are the field selling into retail outlets (dsr_sales), captured either by the sales officer or by an in-store promoter — do not add the two capture paths together without saying so. " +
	"Money is INR. This is DSR's own data: its item ids are NOT SAP ItemCodes, so a figure from here is not automatically comparable with a SAP figure — always say which system a number came from."

// Server wraps an mcp-go MCPServer preloaded with the read-only dsr tools.
type Server struct {
	mcp *server.MCPServer
	// cliPath resolves the dsr binary tool calls shell out to. Held as a
	// function so tests can point it at a stub instead of the real CLI.
	cliPath func() (string, error)
}

// NewServer builds a Server with every read-only tool registered.
func NewServer() *Server {
	s := &Server{cliPath: cobratree.SelfCLIPath}
	s.mcp = server.NewMCPServer(
		"dsr",
		serverVersion,
		server.WithToolCapabilities(false),
		server.WithRecovery(),
		// Advertise additionalProperties:false on every tool, so a
		// schema-aware client is steered away from invented parameters before
		// it sends one. The authoritative rejection still happens in
		// toolSpec.decode, which names the offending key AND lists the valid
		// ones.
		server.WithStrictInputSchemaDefault(),
		server.WithInstructions(instructions),
	)
	s.registerTools()
	return s
}

// MCPServer exposes the underlying mcp-go server, used by tests to drive
// JSON-RPC messages directly and to enumerate registered tools.
func (s *Server) MCPServer() *server.MCPServer { return s.mcp }

// Serve runs the MCP server over stdio (stdin/stdout JSON-RPC), blocking until
// the stream closes.
func (s *Server) Serve() error { return server.ServeStdio(s.mcp) }

// ServeStreamableHTTP runs the identical tool set over streamable HTTP at
// http://<addr>/mcp, blocking until the listener fails. HTTP adds a transport,
// never a capability: the tool set, the allowlist and the read-only gates are
// the same objects the stdio path uses.
//
// Stateless mode is deliberate — nothing about a caller is remembered between
// calls, and each tool call is an independent child process, so concurrent
// calls from an HTTP host cannot share or corrupt state.
func (s *Server) ServeStreamableHTTP(addr string) error {
	return server.NewStreamableHTTPServer(s.mcp, server.WithStateLess(true)).Start(addr)
}

// registerTools wires every tool in the allowlist onto the MCP server. Each is
// registered read-only and non-destructive: hosts like Claude Desktop treat a
// missing annotation as "could write or delete", and a wrong annotation on a
// mutating tool would let a host auto-approve it — so the annotations are
// asserted in tools_test.go, not just written here.
func (s *Server) registerTools() {
	for _, spec := range specs {
		s.mcp.AddTool(toolFor(spec), s.handlerFor(spec))
	}
}

// toolFor builds the advertised MCP tool (schema + annotations) from a spec.
func toolFor(spec *toolSpec) mcplib.Tool {
	opts := []mcplib.ToolOption{
		mcplib.WithDescription(spec.Desc + actionHelp(spec)),
		mcplib.WithTitleAnnotation(spec.Title),
		mcplib.WithReadOnlyHintAnnotation(true),
		mcplib.WithDestructiveHintAnnotation(false),
		// Every tool reaches an external system (SQL Server or the portal).
		mcplib.WithOpenWorldHintAnnotation(true),
	}
	if len(spec.Actions) > 0 {
		opts = append(opts, mcplib.WithString("action",
			mcplib.Required(),
			mcplib.Enum(spec.actionNames()...),
			mcplib.Description("Which read to perform. See the ACTIONS list in this tool's description; an unrecognised action is an error, never a default.")))
	}
	for _, p := range spec.Params {
		opts = append(opts, optionFor(spec, p))
	}
	return mcplib.NewTool(spec.Name, opts...)
}

// optionFor maps one declared parameter to its JSON-schema property.
func optionFor(spec *toolSpec, p param) mcplib.ToolOption {
	desc := p.Desc
	if p.positional() && spec.PosRequired && spec.Pos == p.Name {
		desc += " Required."
	}
	propOpts := []mcplib.PropertyOption{mcplib.Description(desc)}
	if spec.Pos == p.Name && spec.PosRequired && len(spec.Actions) == 0 {
		propOpts = append(propOpts, mcplib.Required())
	}
	switch p.Kind {
	case kindBool:
		return mcplib.WithBoolean(p.Name, propOpts...)
	case kindInt:
		numOpts := append([]mcplib.PropertyOption{}, propOpts...)
		numOpts = append(numOpts, mcplib.Min(float64(p.Min)))
		if p.Max > 0 {
			numOpts = append(numOpts, mcplib.Max(float64(p.Max)))
		}
		return mcplib.WithNumber(p.Name, numOpts...)
	default:
		if len(p.Enum) > 0 {
			propOpts = append(propOpts, mcplib.Enum(p.Enum...))
		}
		return mcplib.WithString(p.Name, propOpts...)
	}
}

// handlerFor builds the handler for one tool: decode strictly, resolve the
// action against the allowlist, assemble a literal argv, shell out.
func (s *Server) handlerFor(spec *toolSpec) server.ToolHandlerFunc {
	return func(ctx context.Context, req mcplib.CallToolRequest) (*mcplib.CallToolResult, error) {
		raw := req.GetArguments()

		vals, err := spec.decode(raw)
		if err != nil {
			return mcplib.NewToolResultError(err.Error()), nil
		}

		argv, err := buildArgv(spec, raw, vals)
		if err != nil {
			return mcplib.NewToolResultError(err.Error()), nil
		}

		bin, err := s.cliPath()
		if err != nil {
			return mcplib.NewToolResultError(fmt.Sprintf("dsr CLI binary not found: %v (tried this executable, DSR_CLI_PATH, then PATH)", err)), nil
		}

		runCtx, cancel := context.WithTimeout(ctx, cliTimeout)
		defer cancel()

		out, err := cobratree.RunCLICommand(runCtx, bin, argv)
		if err != nil {
			return mcplib.NewToolResultError(err.Error()), nil
		}
		if len(out) > maxResultBytes {
			return mcplib.NewToolResultError(fmt.Sprintf(
				"result is %d bytes, over the %d-byte cap — lower `limit`, narrow the date range, or use a *_count action instead of listing rows",
				len(out), maxResultBytes)), nil
		}
		return mcplib.NewToolResultText(out), nil
	}
}

// buildArgv assembles the child process arguments.
//
// The argv prefix is a literal from the allowlist; only parameters the chosen
// action declares can follow it. That double check — the tool's own parameter
// list, then the action's — is what stops `where` (a raw SQL fragment, only
// meaningful on `count`) from being smuggled onto a domain command, and what
// makes the set of flags this server can emit finite and reviewable.
func buildArgv(spec *toolSpec, raw map[string]any, vals map[string]string) ([]string, error) {
	var (
		argv        []string
		posName     string
		posRequired bool
		allowed     map[string]bool
		required    []string
	)

	if len(spec.Actions) > 0 {
		name, _ := raw["action"].(string)
		name = strings.TrimSpace(name)
		if name == "" {
			return nil, fmt.Errorf("missing required parameter \"action\" for tool %s. Valid actions: %s",
				spec.Name, strings.Join(spec.actionNames(), ", "))
		}
		act, ok := spec.action(name)
		if !ok {
			return nil, fmt.Errorf("unknown action %q for tool %s. Valid actions: %s",
				name, spec.Name, strings.Join(spec.actionNames(), ", "))
		}
		argv = append(argv, act.Argv...)
		posName, posRequired, required = act.Pos, act.PosRequired, act.Required
		allowed = map[string]bool{}
		for _, f := range act.Flags {
			allowed[f] = true
		}
	} else {
		argv = append(argv, spec.Fixed...)
		posName, posRequired = spec.Pos, spec.PosRequired
		allowed = map[string]bool{}
		for _, p := range spec.Params {
			if !p.positional() {
				allowed[p.Name] = true
			}
		}
	}

	// The positional, if this action takes one.
	if posName != "" {
		if v, ok := vals[posName]; ok {
			argv = append(argv, v)
		} else if posRequired {
			return nil, fmt.Errorf("missing required parameter %q for %s%s", posName, spec.Name, actionSuffix(raw))
		}
	} else if _, ok := vals[spec.posCandidate()]; ok && spec.posCandidate() != "" {
		return nil, fmt.Errorf("parameter %q does not apply to %s%s", spec.posCandidate(), spec.Name, actionSuffix(raw))
	}

	// Flags, in the order the spec declares them, so the argv is stable and
	// diffable in the write-free audit trail an operator reads.
	for _, p := range spec.Params {
		if p.positional() || p.Name == posName {
			continue
		}
		v, ok := vals[p.Name]
		if !ok {
			continue
		}
		if !allowed[p.Name] {
			return nil, fmt.Errorf("parameter %q does not apply to %s%s", p.Name, spec.Name, actionSuffix(raw))
		}
		if cobratree.BlockedFlags[p.Flag] {
			return nil, fmt.Errorf("parameter %q maps to a blocked root flag --%s", p.Name, p.Flag)
		}
		if err := guardSQLFragment(p.Name, v); err != nil {
			return nil, err
		}
		if p.Kind == kindBool {
			argv = append(argv, "--"+p.Flag)
			continue
		}
		argv = append(argv, "--"+p.Flag, v)
	}

	for _, r := range required {
		if _, ok := vals[r]; !ok {
			return nil, fmt.Errorf("missing required parameter %q for %s%s", r, spec.Name, actionSuffix(raw))
		}
	}

	// The positional of dsr_query is SQL and gets the same gate the database
	// layer applies, one process earlier — so a rejected statement never even
	// starts a child.
	if posName == "sql" {
		if v, ok := vals["sql"]; ok {
			if err := db.GuardReadOnly(v); err != nil {
				return nil, fmt.Errorf("refused: %v", err)
			}
		}
	}

	// Bound every row-returning call. The CLI's `query` is unbounded by
	// default and its domain lists default to 100-500; injecting the cap here
	// makes the ceiling one number an agent can see and reason about.
	if allowed["limit"] {
		if _, ok := vals["limit"]; !ok {
			argv = append(argv, "--limit", itoa(defaultLimit))
		}
	}

	// One output shape for every tool.
	argv = append(argv, "--json")
	return argv, nil
}

// posCandidate names the parameter this tool uses as a positional, if any, so
// passing it to an action that takes no positional is a named error instead of
// a silently dropped argument.
func (t *toolSpec) posCandidate() string {
	for _, p := range t.Params {
		if p.positional() {
			return p.Name
		}
	}
	return ""
}

// guardSQLFragment applies the database layer's read-only gate to the one
// parameter that carries raw SQL (`where`, appended into a WHERE clause by
// `dsr count`). Wrapping it in a trivial SELECT lets the real guard — the same
// code the CLI and the driver path use — judge it, instead of a second,
// weaker copy of the rule living here.
func guardSQLFragment(name, value string) error {
	if name != "where" {
		return nil
	}
	if err := db.GuardReadOnly("SELECT 1 WHERE " + value); err != nil {
		return fmt.Errorf("refused `where` filter: %v", err)
	}
	return nil
}

func actionSuffix(raw map[string]any) string {
	if a, ok := raw["action"].(string); ok && a != "" {
		return " action=" + a
	}
	return ""
}

func itoa(n int) string { return fmt.Sprintf("%d", n) }
