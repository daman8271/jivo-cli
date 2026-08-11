// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — the tool surface.
//
// Ten tools, not 146. The gateway already advertises 84 tools across six
// backends; one tool per CLI leaf command would add 174% more names and wreck
// routing, and most of those leaves answer questions sap_/hana_ answer better.
// So: seven curated tools over the surfaces that exist NOWHERE else in JIVO's
// stack (budget approvals, helpdesk tickets, tasks, the employee hierarchy,
// Document Hub, inventory audits), plus jsap_search + jsap_execute over the
// full compiled-in catalogue for everything else.
//
// EVERY tool here is a read. There is no write tool, and there is no code path
// from this package to one: handlers dispatch a catalogued command id to
// jsap.Client.Run, which accepts nothing but a Command from the compiled-in
// catalogue. See readonly_guard_test.go, which fails the build if this package
// so much as names a mutating HTTP verb.

package mcp

import (
	"context"
	"fmt"
	"sort"
	"strings"

	"jsap-mcp/internal/jsap"

	mcplib "github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// defaultCompany is JIVO OIL. JSAP knows exactly two companies and has no Mart.
const defaultCompany = 1

// instructions ride along on initialize, so a host that never calls
// jsap_context still learns the one fact that stops wrong answers: JSAP is not
// a view of SAP.
const instructions = `JSAP is JIVO's internal ops/governance platform (helpdesk tickets, tasks, the ` +
	`employee hierarchy, Document Hub, physical inventory audits, budget approvals) — NOT a view of SAP. ` +
	`Ledger, invoice, purchase-order and stock questions belong to sap_ / hana_ tools; JSAP's copies of ` +
	`those are filtered subsets that undercount. Every tool is read-only. Company ids: 1 = JIVO OIL, ` +
	`2 = JIVO BEVERAGE (note: in factory-cli company 2 means Mart — never carry an id across systems). ` +
	`Call jsap_context first.`

// Server owns the MCP server and the per-company JSAP session pool.
type Server struct {
	sessions *jsap.Sessions
	mcp      *server.MCPServer
}

// New builds the server and registers every tool.
func New(cfg jsap.Config, version string) *Server {
	s := &Server{sessions: jsap.NewSessions(cfg)}
	s.mcp = server.NewMCPServer(
		"JIVO JSAP",
		version,
		server.WithToolCapabilities(false),
		server.WithInstructions(instructions),
	)
	s.registerTools()
	return s
}

// MCPServer exposes the underlying server (transport wiring and tests).
func (s *Server) MCPServer() *server.MCPServer { return s.mcp }

// curated is one hand-shaped tool over a named set of catalogued commands. Its
// input schema is DERIVED from the catalogue, so a tool can never advertise a
// parameter the command does not declare, or miss one it requires.
type curated struct {
	Name        string
	Description string
	// Actions maps the tool's action value to a catalogued command id, in the
	// order they should be presented.
	Actions [][2]string
}

func (c curated) commandFor(action string) (string, bool) {
	for _, pair := range c.Actions {
		if pair[0] == action {
			return pair[1], true
		}
	}
	return "", false
}

func (c curated) actionNames() []string {
	out := make([]string, 0, len(c.Actions))
	for _, pair := range c.Actions {
		out = append(out, pair[0])
	}
	return out
}

// curatedTools is the whole hand-shaped surface. Anything not here is still
// reachable through jsap_search + jsap_execute.
var curatedTools = []curated{
	{
		Name: "jsap_budget_approvals",
		Description: "JSAP's budget-approval trail — the highest-value surface here: SAP draft -> JSAP approval stages -> posted A/P invoice, with stage names resolved. " +
			"actions: insight (per-user pending/approved/rejected counts for a month), summary (full month export), pending|approved|rejected (documents for one user+month), " +
			"lookup (find budget docs by SAP DocEntry or vendor CardName), flow (stage-by-stage flow for one budgetId). " +
			"CAUTION: a JSAP budget totalAmount is NOT the SAP DocTotal (393,750 vs 425,250 on a verified case) — never add or compare the two. Months are MM-YYYY.",
		Actions: [][2]string{
			{"insight", "reports.insight"},
			{"summary", "reports.summary"},
			{"pending", "reports.pending"},
			{"approved", "reports.approved"},
			{"rejected", "reports.rejected"},
			{"lookup", "reports.lookup"},
			{"flow", "reports.flow"},
		},
	},
	{
		Name: "jsap_tickets",
		Description: "IT helpdesk / support tickets. This data exists in no other JIVO system — not in SAP, HANA, Postgres, ecom, oms or factory. " +
			"actions: projects, mine, all, assigned, ticket, timeline, comments, attachments (metadata only), workload, users. " +
			"Ticket data is global across both companies. Attachment BYTES are deliberately not exposed.",
		Actions: [][2]string{
			{"projects", "tickets.projects"},
			{"mine", "tickets.mine"},
			{"all", "tickets.all"},
			{"assigned", "tickets.assigned"},
			{"ticket", "tickets.ticket"},
			{"timeline", "tickets.timeline"},
			{"comments", "tickets.comments"},
			{"attachments", "tickets.attachments"},
			{"workload", "tickets.workload"},
			{"users", "tickets.users"},
		},
	},
	{
		Name: "jsap_tasks",
		Description: "Task Manager (daily tasks): the task list, stat cards, team roster, the task hierarchy tree, one task's record and its progress-update log. " +
			"actions: list, dashboard, team, tree, details, progress. Scoping follows the employee hierarchy, not the company.",
		Actions: [][2]string{
			{"list", "tasks.list"},
			{"dashboard", "tasks.dashboard"},
			{"team", "tasks.team"},
			{"tree", "tasks.tree"},
			{"details", "tasks.details"},
			{"progress", "tasks.progress"},
		},
	},
	{
		Name: "jsap_hierarchy",
		Description: "The employee org tree — JIVO's only structured 'who reports to whom': HO hierarchy (HOD -> sub-HOD -> executive), department masters, employee records, " +
			"the audit trail, and the field Sales H1-H4 chain. actions: tree, flat (best tabular source), search, employee, details, orphans, hods, departments, subdepts, " +
			"hod-depts, subhods, roles, extras, fields, custom-values, logs, sales-tree, sales, sales-stats, sales-lookups, sales-employees, sales-logs. " +
			"SALARY IS REDACTED: compensation-shaped fields are stripped from every response and the salary-only endpoints are not exposed at all.",
		Actions: [][2]string{
			{"tree", "hierarchy.tree"},
			{"flat", "hierarchy.flat"},
			{"search", "hierarchy.search"},
			{"employee", "hierarchy.employee"},
			{"details", "hierarchy.details"},
			{"orphans", "hierarchy.orphans"},
			{"hods", "hierarchy.hods"},
			{"departments", "hierarchy.departments"},
			{"subdepts", "hierarchy.subdepts"},
			{"hod-depts", "hierarchy.hod-depts"},
			{"subhods", "hierarchy.subhods"},
			{"roles", "hierarchy.roles"},
			{"extras", "hierarchy.extras"},
			{"fields", "hierarchy.fields"},
			{"custom-values", "hierarchy.custom-values"},
			{"logs", "hierarchy.logs"},
			{"sales-tree", "hierarchy.sales-tree"},
			{"sales", "hierarchy.sales"},
			{"sales-stats", "hierarchy.sales-stats"},
			{"sales-lookups", "hierarchy.sales-lookups"},
			{"sales-employees", "hierarchy.sales-employees"},
			{"sales-logs", "hierarchy.sales-logs"},
		},
	},
	{
		Name: "jsap_dochub",
		Description: "Document Hub METADATA: folder/file listings, file access flags, version history, per-file activity trail and backup manifests. " +
			"actions: hub, folders, file, versions, activity, backups, backup. " +
			"File CONTENT is not exposed: Download appends a server-side activity-log row (a read with a side effect) and Preview streams raw bytes.",
		Actions: [][2]string{
			{"hub", "dochub.hub"},
			{"folders", "dochub.folders"},
			{"file", "dochub.file"},
			{"versions", "dochub.versions"},
			{"activity", "dochub.activity"},
			{"backups", "dochub.backups"},
			{"backup", "dochub.backup"},
		},
	},
	{
		Name: "jsap_inventory_audit",
		Description: "Physical stock-count audit sessions and the item-level audit report (system vs physically counted qty/value/litre per item) — the counted side of stock, " +
			"which SAP does not hold. actions: active, inactive, created-active, created-inactive, report (needs lotNumber), users. " +
			"For book stock use sap_items / hana_query instead; the unit/location/warehouse/item-group lookups here are SAP mirrors and are not exposed.",
		Actions: [][2]string{
			{"active", "inventory.active"},
			{"inactive", "inventory.inactive"},
			{"created-active", "inventory.created-active"},
			{"created-inactive", "inventory.created-inactive"},
			{"report", "inventory.report"},
			{"users", "inventory.users"},
		},
	},
	{
		Name: "jsap_admin",
		Description: "JSAP's own platform model: users, roles, states, branches, budget heads, approval types, report catalog, departments, companies, effective permissions, " +
			"and the master quality-check template. actions: users, unregistered, roles, states, branches, budgets, subbudgets, approvals, varieties, reports, departments, " +
			"companies, permissions, qc-form. These describe JSAP itself — who may see what — not JIVO's books.",
		Actions: [][2]string{
			{"users", "users.list"},
			{"unregistered", "users.unregistered"},
			{"roles", "users.roles"},
			{"states", "users.states"},
			{"branches", "users.branches"},
			{"budgets", "users.budgets"},
			{"subbudgets", "users.subbudgets"},
			{"approvals", "users.approvals"},
			{"varieties", "users.varieties"},
			{"reports", "users.reports"},
			{"departments", "meta.departments"},
			{"companies", "meta.companies"},
			{"permissions", "meta.permissions"},
			{"qc-form", "qc.form"},
		},
	},
}

// registerTools registers jsap_context, jsap_search, jsap_execute and the
// curated tools. Every name starts with "jsap_" so the gateway can declare
// Prefix and StripPrefix as the same string and the rename is the identity —
// the tools read as jsap_tickets standalone and behind the gateway alike, with
// no jsap_jsap_ stutter (the same arrangement hana uses).
func (s *Server) registerTools() {
	s.mcp.AddTool(
		mcplib.NewTool("jsap_context",
			mcplib.WithDescription("What JSAP is, what it is NOT, which questions it answers better than SAP, which surfaces are deliberately excluded and why. Call this first — it costs no network round trip."),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
		),
		s.handleContext,
	)

	s.mcp.AddTool(
		mcplib.NewTool("jsap_search",
			mcplib.WithDescription("Search the JSAP command catalogue by natural language. Returns ranked {command, method, path, summary, params} entries; pass a command id to jsap_execute. Use this for anything the curated tools do not cover (IT-standards register, MoM minutes, client/project dashboards, the budget fact table)."),
			mcplib.WithString("query", mcplib.Required(), mcplib.Description("What you are trying to find, in plain words.")),
			mcplib.WithNumber("limit", mcplib.Description("Max commands to return (default 10).")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
		),
		s.handleSearch,
	)

	s.mcp.AddTool(
		mcplib.NewTool("jsap_execute",
			mcplib.WithDescription("Run ONE catalogued JSAP read by its command id (from jsap_search). Only catalogued command ids are accepted — this tool takes no URL and no path, by design. Parameters are validated against the command's declaration; an undeclared parameter is rejected, never ignored."),
			mcplib.WithString("command", mcplib.Required(), mcplib.Description("Command id returned by jsap_search, e.g. \"dashboards.mom\".")),
			mcplib.WithObject("params", mcplib.Description("Parameters for the command, as declared in jsap_search output.")),
			mcplib.WithNumber("company", mcplib.Description("JSAP company id: 1 = JIVO OIL (default), 2 = JIVO BEVERAGE.")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
		),
		s.handleExecute,
	)

	for _, tool := range curatedTools {
		s.mcp.AddTool(buildCuratedTool(tool), s.handleCurated(tool))
	}
}

// buildCuratedTool derives one curated tool's input schema from the catalogue:
// an action enum plus the union of the declared parameters of the commands it
// covers, each documented with the actions that accept it.
func buildCuratedTool(t curated) mcplib.Tool {
	opts := []mcplib.ToolOption{
		mcplib.WithDescription(t.Description),
		mcplib.WithString("action",
			mcplib.Required(),
			mcplib.Enum(t.actionNames()...),
			mcplib.Description("Which read to perform: "+strings.Join(t.actionNames(), ", ")),
		),
		mcplib.WithNumber("company",
			mcplib.Description("JSAP company id: 1 = JIVO OIL (default), 2 = JIVO BEVERAGE. Responses always echo the company NAME back."),
		),
	}
	for _, p := range unionParams(t) {
		desc := p.Help
		if len(p.actions) > 0 {
			desc = fmt.Sprintf("%s (actions: %s)", desc, strings.Join(p.actions, ", "))
		}
		switch p.Type {
		case jsap.TypeInt:
			opts = append(opts, mcplib.WithNumber(p.Name, mcplib.Description(desc)))
		case jsap.TypeBool:
			opts = append(opts, mcplib.WithBoolean(p.Name, mcplib.Description(desc)))
		default:
			opts = append(opts, mcplib.WithString(p.Name, mcplib.Description(desc)))
		}
	}
	opts = append(opts,
		mcplib.WithReadOnlyHintAnnotation(true),
		mcplib.WithDestructiveHintAnnotation(false),
	)
	return mcplib.NewTool(t.Name, opts...)
}

// unionParam is one parameter of a curated tool, plus the actions that take it.
type unionParam struct {
	jsap.Param
	actions []string
}

// unionParams merges the parameter declarations of a curated tool's commands.
// A name that appears under two actions with two different types would be an
// ambiguous schema; TestCuratedToolSchemasAreConsistent pins that it does not
// happen, and here the first declaration wins so the schema stays deterministic.
func unionParams(t curated) []unionParam {
	byName := map[string]*unionParam{}
	var order []string
	for _, pair := range t.Actions {
		cmd, ok := jsap.Lookup(pair[1])
		if !ok {
			continue
		}
		for _, p := range cmd.Params {
			existing, seen := byName[p.Name]
			if !seen {
				byName[p.Name] = &unionParam{Param: p, actions: []string{pair[0]}}
				order = append(order, p.Name)
				continue
			}
			existing.actions = append(existing.actions, pair[0])
		}
	}
	out := make([]unionParam, 0, len(order))
	for _, name := range order {
		out = append(out, *byName[name])
	}
	return out
}

// ---------------------------------------------------------------------------
// handlers
// ---------------------------------------------------------------------------

func (s *Server) handleContext(ctx context.Context, req mcplib.CallToolRequest) (*mcplib.CallToolResult, error) {
	groups := map[string]int{}
	for _, c := range jsap.Commands() {
		groups[c.Group]++
	}
	groupNames := make([]string, 0, len(groups))
	for name := range groups {
		groupNames = append(groupNames, name)
	}
	sort.Strings(groupNames)
	groupRows := make([]map[string]any, 0, len(groupNames))
	for _, name := range groupNames {
		groupRows = append(groupRows, map[string]any{"group": name, "commands": groups[name]})
	}

	exclusions := make([]map[string]string, 0, len(jsap.Excluded))
	for _, e := range jsap.Excluded {
		exclusions = append(exclusions, map[string]string{"surface": e.Surface, "why": e.Reason})
	}

	companies := make([]map[string]any, 0, len(jsap.Companies))
	for id, name := range jsap.Companies {
		companies = append(companies, map[string]any{"id": id, "name": name})
	}
	sort.Slice(companies, func(a, b int) bool {
		return companies[a]["id"].(int) < companies[b]["id"].(int)
	})

	return jsonResult(map[string]any{
		"system":   "JSAP — JIVO's internal ops/governance platform (ASP.NET Core, same host as the DSR portal)",
		"base_url": s.sessions.Config().BaseURL,
		"what_it_is": "Helpdesk tickets, daily tasks, the employee org tree, Document Hub, physical inventory audits, " +
			"budget approvals, IT-standards and MoM dashboards, and JSAP's own permission model. None of that exists in SAP, HANA, Postgres, ecom, oms or factory.",
		"what_it_is_not": "It is NOT a view of SAP, despite the name. Its copies of purchase orders, GRPOs, AP drafts and business partners " +
			"are filtered subsets (3,441 POs against SAP OPOR's 5,304) and are not exposed here. Ledger, invoice, turnover, PO and book-stock questions go to sap_ / hana_.",
		"read_only": "Every tool is a read. jsap_execute dispatches by catalogued command id only — it accepts no URL and no path — so JSAP's " +
			"write endpoints and its two side-effecting reads are unreachable from here.",
		"companies":            companies,
		"default_company":      defaultCompany,
		"company_id_collision": "A company id is only meaningful inside one system: JSAP 2 = JIVO BEVERAGE, but factory-cli 2 = Mart. Every response echoes the company NAME; quote that, never the id.",
		"tools": []string{
			"jsap_context", "jsap_search", "jsap_execute",
			"jsap_budget_approvals", "jsap_tickets", "jsap_tasks",
			"jsap_hierarchy", "jsap_dochub", "jsap_inventory_audit", "jsap_admin",
		},
		"catalogue_size":   len(jsap.Commands()),
		"catalogue_groups": groupRows,
		"gotchas": []string{
			"A JSAP budget totalAmount is not the SAP DocTotal (393,750 vs 425,250 on a verified case). Never mix the two.",
			"The raw budget-approval rows also live in the SAP HANA schemas (JS_SYNC_BUDGET_APPROVAL_WORKFLOW, tbl_Draft_Approvals); jsap adds the resolved, stage-named view, not new facts.",
			"Every gateway caller authenticates as the same single JSAP identity and inherits its permissions.",
			"Salary fields are stripped from every response; the salary-only endpoints are not exposed.",
			"Amounts are INR.",
		},
		"excluded": exclusions,
	}), nil
}

func (s *Server) handleSearch(ctx context.Context, req mcplib.CallToolRequest) (*mcplib.CallToolResult, error) {
	args := req.GetArguments()
	query, _ := args["query"].(string)
	if strings.TrimSpace(query) == "" {
		return mcplib.NewToolResultError("query is required"), nil
	}
	limit := 10
	if raw, ok := args["limit"].(float64); ok && raw > 0 {
		limit = int(raw)
	}

	hits := jsap.Search(query, limit)
	rows := make([]map[string]any, 0, len(hits))
	for _, cmd := range hits {
		params := make([]map[string]any, 0, len(cmd.Params))
		for _, p := range cmd.Params {
			params = append(params, map[string]any{
				"name":     p.Name,
				"type":     string(p.Type),
				"required": p.Required,
				"help":     p.Help,
			})
		}
		rows = append(rows, map[string]any{
			"command":        cmd.ID,
			"group":          cmd.Group,
			"method":         cmd.Method,
			"path":           cmd.Path,
			"summary":        cmd.Summary,
			"company_scoped": cmd.CompanyParam != "",
			"params":         params,
		})
	}
	return jsonResult(map[string]any{
		"query":    query,
		"matches":  len(rows),
		"commands": rows,
		"next":     "Run one with jsap_execute {command, params}.",
	}), nil
}

func (s *Server) handleExecute(ctx context.Context, req mcplib.CallToolRequest) (*mcplib.CallToolResult, error) {
	args := req.GetArguments()
	id, _ := args["command"].(string)
	if strings.TrimSpace(id) == "" {
		return mcplib.NewToolResultError("command is required — find one with jsap_search"), nil
	}
	params := map[string]any{}
	if raw, ok := args["params"].(map[string]any); ok {
		params = raw
	}
	company, err := companyFrom(args)
	if err != nil {
		return mcplib.NewToolResultError(err.Error()), nil
	}
	return s.run(ctx, id, params, company), nil
}

func (s *Server) handleCurated(t curated) server.ToolHandlerFunc {
	return func(ctx context.Context, req mcplib.CallToolRequest) (*mcplib.CallToolResult, error) {
		args := req.GetArguments()
		action, _ := args["action"].(string)
		id, ok := t.commandFor(strings.TrimSpace(action))
		if !ok {
			return mcplib.NewToolResultError(fmt.Sprintf("unknown action %q for %s — valid actions: %s",
				action, t.Name, strings.Join(t.actionNames(), ", "))), nil
		}
		company, err := companyFrom(args)
		if err != nil {
			return mcplib.NewToolResultError(err.Error()), nil
		}
		params := map[string]any{}
		for name, value := range args {
			if name == "action" || name == "company" || value == nil {
				continue
			}
			params[name] = value
		}
		return s.run(ctx, id, params, company), nil
	}
}

// run is the single execution path shared by every tool: look the command up in
// the compiled-in catalogue, hand it to the company's session, shape the result.
func (s *Server) run(ctx context.Context, id string, params map[string]any, company int) *mcplib.CallToolResult {
	cmd, ok := jsap.Lookup(id)
	if !ok {
		return mcplib.NewToolResultError(fmt.Sprintf("unknown command %q — it is not in the JSAP catalogue. "+
			"Search for one with jsap_search; excluded surfaces (SAP mirrors, the bills group, salary, document dispatch) are excluded on purpose, see jsap_context.", id))
	}
	payload, err := s.sessions.For(company).Run(ctx, cmd, params)
	if err != nil {
		return mcplib.NewToolResultError(err.Error())
	}
	return commandResult(cmd, company, payload)
}

// companyFrom reads and validates the company id. An unknown id is refused
// rather than defaulted: silently answering for JIVO OIL when the caller asked
// for something else is the cross-attribution this server exists to prevent.
func companyFrom(args map[string]any) (int, error) {
	raw, ok := args["company"]
	if !ok || raw == nil {
		return defaultCompany, nil
	}
	var id int
	switch v := raw.(type) {
	case float64:
		id = int(v)
	case int:
		id = v
	case string:
		trimmed := strings.TrimSpace(v)
		for candidate, name := range jsap.Companies {
			if strings.EqualFold(trimmed, name) {
				return candidate, nil
			}
		}
		return 0, fmt.Errorf("company %q is not a JSAP company — valid: %s", v, companyList())
	default:
		return 0, fmt.Errorf("company must be a number (1 or 2)")
	}
	if _, known := jsap.Companies[id]; !known {
		return 0, fmt.Errorf("company id %d is not a JSAP company — valid: %s", id, companyList())
	}
	return id, nil
}

func companyList() string {
	ids := make([]int, 0, len(jsap.Companies))
	for id := range jsap.Companies {
		ids = append(ids, id)
	}
	sort.Ints(ids)
	parts := make([]string, 0, len(ids))
	for _, id := range ids {
		parts = append(parts, fmt.Sprintf("%d = %s", id, jsap.Companies[id]))
	}
	return strings.Join(parts, ", ")
}
