// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — the compiled-in command catalogue.
//
// This file IS the read-only guarantee. Every request the MCP surface can make
// is one of the entries below: a fixed method, a fixed path, and a closed set of
// named parameters. Callers name a command; they never supply a URL, and a
// parameter that is not declared here is refused rather than forwarded.
//
// WHAT IS DELIBERATELY NOT HERE (each exclusion is load-bearing, see Excluded):
//   - the whole `documents` group  — 4 SAP-mirror reads that undercount SAP,
//     5 endpoints that have returned HTTP 500 since 2026-07-30, the
//     GetLastBundleId counter (its mode=update variant MUTATES), and two binary
//     file streams;
//   - the whole `bpmaster` group   — SAP business-partner master, mirrored worse
//     than sap_/hana_ already answer it;
//   - the whole `bills` group      — Baru Sahib / Akal institutional supply, a
//     DIFFERENT organisation's books; answering a JIVO question from it would be
//     wrong, not merely redundant;
//   - the salary surface          — GetSalarySessionData and
//     GetEmployeesForSalaryPermission, plus key-level redaction of the salary
//     columns that ride along in the hierarchy reads;
//   - the SAP-mirror lookups in `inventory` (units/locations/warehouses/item
//     groups/sub-groups) and in `dashboards` (ledger accounts, budget heads);
//   - DocumentHub Download and Preview — Download appends a server-side
//     activity-log row (a read with a side effect) and both stream raw bytes.

package jsap

import (
	"fmt"
	"net/url"
	"sort"
	"strconv"
	"strings"
)

// ParamType is the wire type of one command parameter.
type ParamType string

const (
	TypeString ParamType = "string"
	TypeInt    ParamType = "integer"
	TypeBool   ParamType = "boolean"
)

// Param is one declared, named input of a catalogued command. The declaration
// is the allowlist: bind() refuses anything not on it.
type Param struct {
	Name     string
	Wire     string // wire name when it differs from Name ("" = same)
	Type     ParamType
	InPath   bool // substitutes into {Name} in Path
	Required bool
	Default  any  // sent when the caller omits the parameter
	FromUser bool // defaults to the configured JSAP user id
	Upper    bool // uppercased before sending (JSAP matches some names exactly)
	Help     string
}

func (p Param) wire() string {
	if p.Wire != "" {
		return p.Wire
	}
	return p.Name
}

// FixedField is a constant this command always sends. Constants are here, not
// in the caller's hands: `mode`-style switches must never be caller-supplied.
type FixedField struct {
	Name  string
	Value any
}

// Command is one catalogued read.
type Command struct {
	ID      string // "<group>.<name>", the id agents pass to jsap_execute
	Group   string
	Method  string // GET, or POST for a guarded POST-to-read
	Path    string
	Summary string
	Params  []Param
	Fixed   []FixedField
	// CompanyParam sends the session's company id under this key ("" when the
	// endpoint is company-agnostic). JSAP: 1 = JIVO OIL, 2 = JIVO BEVERAGE.
	CompanyParam string
	// Raw keeps JSAP's {success,data} envelope instead of unwrapping to data.
	Raw bool
	// HTMLUserTable marks the one endpoint that answers with a server-rendered
	// page rather than JSON; the response is parsed into rows.
	HTMLUserTable bool

	keywords []string
}

// Exclusion records one surface kept off the MCP tool set, and why. jsap_context
// serves this list so an agent that goes looking for tickets-write, bills or PO
// data is told where the real answer lives instead of guessing.
type Exclusion struct {
	Surface string
	Reason  string
}

// Excluded is the documented, testable exclusion list.
var Excluded = []Exclusion{
	{"documents.* (Document Dispatch)", "GetPO/GetGRPO/GetApDraft/GetGR mirror SAP and undercount it (JSAP returned 3,441 POs vs SAP OPOR's 5,304) — use sap_ or hana_ instead. The dispatch half (docs/rejected/pending/history) has returned HTTP 500 since 2026-07-30. GetLastBundleId has a mode=update variant that mutates a counter."},
	{"bpmaster.* (14 commands)", "SAP business-partner master, mirrored. Ask sap_partners / hana_query."},
	{"bills.* (14 commands)", "NOT JIVO's books — Baru Sahib / Akal institutional supply (a different organisation). Its accounts, items and warehouses match nothing in SAP OCRD/OITM/OWHS."},
	{"hierarchy salary endpoints", "GetSalarySessionData and GetEmployeesForSalaryPermission expose HR compensation on a publicly-routed gateway. Salary-shaped keys are also redacted from every response this server returns."},
	{"inventory unit/location/warehouse/item-group lookups", "SAP master-data mirrors; sap_items / hana_query are the source."},
	{"dashboards ledger + budget-head lookups", "SAP chart-of-accounts mirrors."},
	{"DocumentHub Download and Preview", "Download appends a server-side activity-log row (a read with a side effect); both stream raw bytes, which is not a tool result."},
	{"every write endpoint JSAP has", "CreateTicket, AssignTicket, SaveAllAttachments, InsertBPmasterData, salary-session unlock, QC UpdateForm and the rest are not catalogued, and this server has no code path that could reach them."},
}

// ---------------------------------------------------------------------------
// declaration helpers — keep the catalogue itself readable as a table
// ---------------------------------------------------------------------------

func get(id, path, summary string, params ...Param) Command {
	return Command{ID: id, Group: groupOf(id), Method: verbGet, Path: path, Summary: summary, Params: params}
}

func post(id, path, summary string, params ...Param) Command {
	return Command{ID: id, Group: groupOf(id), Method: verbPost, Path: path, Summary: summary, Params: params}
}

func groupOf(id string) string {
	if i := strings.IndexByte(id, '.'); i > 0 {
		return id[:i]
	}
	return id
}

func (c Command) company(key string) Command { c.CompanyParam = key; return c }
func (c Command) rawEnvelope() Command       { c.Raw = true; return c }
func (c Command) htmlUsers() Command         { c.HTMLUserTable = true; return c }
func (c Command) with(n string, v any) Command {
	c.Fixed = append(c.Fixed, FixedField{Name: n, Value: v})
	return c
}

func str(name, help string) Param  { return Param{Name: name, Type: TypeString, Help: help} }
func num(name, help string) Param  { return Param{Name: name, Type: TypeInt, Help: help} }
func flag(name, help string) Param { return Param{Name: name, Type: TypeBool, Help: help} }
func req(p Param) Param            { p.Required = true; return p }
func def(p Param, v any) Param     { p.Default = v; return p }
func user(p Param) Param           { p.FromUser = true; return p }
func inPath(p Param) Param         { p.InPath = true; p.Required = true; return p }
func wire(p Param, w string) Param { p.Wire = w; return p }
func upper(p Param) Param          { p.Upper = true; return p }

// taskFilters are the shared server-side filters the five DashboardWeb task
// endpoints all accept.
func taskFilters() []Param {
	return []Param{
		str("group_by", "Grouping dimension: PROJECT|MODULE|STATUS|TASK"),
		str("assignedto", "Filter by assignee (employee id)"),
		str("project", "Filter by project name"),
		str("status", "Filter by status (In Progress|Completed Ahead|Completed|Pending)"),
		str("priority", "Filter by priority (Critical|High|Medium|Low)"),
		str("search", "Free-text search"),
		str("startDate", "Start date (YYYY-MM-DD)"),
		str("endDate", "End date (YYYY-MM-DD)"),
	}
}

func withFilters(extra ...Param) []Param {
	return append(extra, taskFilters()...)
}

// filtersRequiringGroupBy is taskFilters with group_by promoted to required:
// /api/Dashboard/stats answers 400 without it, unlike its four siblings.
func filtersRequiringGroupBy() []Param {
	out := taskFilters()
	for idx := range out {
		if out[idx].Name == "group_by" {
			out[idx].Required = true
		}
	}
	return out
}

// ---------------------------------------------------------------------------
// the catalogue
// ---------------------------------------------------------------------------

var commands = buildCatalogue()

func buildCatalogue() []Command {
	out := []Command{
		// -- reports: the budget-approval trail ---------------------------
		// The highest-value unique surface: SAP draft -> JSAP approval ->
		// posted A/P invoice, resolved with stage names. Caveat for callers:
		// a JSAP budget totalAmount is NOT the SAP DocTotal (393,750 vs
		// 425,250 on the verified case). Never add the two together.
		get("reports.insight", "/api/auth/GetAllBudgetInsight",
			"Per-user Pending/Approved/Rejected budget counts for a month",
			req(str("month", "Month as MM-YYYY, e.g. 06-2026")),
		).company("company"),
		get("reports.summary", "/api/auth/GetAllBudgetSummaryAmount",
			"Full nested budget summary export dataset for a month",
			req(str("month", "Month as MM-YYYY")),
		).company("company"),
		get("reports.lookup", "/api/Reports/GetBudgetByCompany",
			"Look up budget documents by SAP DocEntry or vendor CardName",
			str("month", "Month as MM-YYYY (ignored for docEntry lookups)"),
			num("docEntry", "SAP DocEntry (numeric lookup)"),
			upper(str("cardName", "Vendor CardName (exact full-name match, uppercased)")),
		).company("company"),
		get("reports.pending", "/api/auth/getpendingbudgetwithdetails",
			"Pending budget documents for a user/month",
			req(num("userId", "User id to drill into")), req(str("month", "Month as MM-YYYY")),
		).company("company"),
		get("reports.approved", "/api/auth/getapprovedbudgetwithdetails",
			"Approved budget documents for a user/month",
			req(num("userId", "User id to drill into")), req(str("month", "Month as MM-YYYY")),
		).company("company"),
		get("reports.rejected", "/api/auth/getrejectedbudgetwithdetails",
			"Rejected budget documents for a user/month",
			req(num("userId", "User id to drill into")), req(str("month", "Month as MM-YYYY")),
		).company("company"),
		get("reports.flow", "/api/auth/GetBudgetApprovalFlow",
			"Stage-by-stage approval flow for one budget document",
			req(num("budgetId", "Budget document id")),
		),

		// -- tickets: IT helpdesk (exists nowhere in SAP/HANA/PG) ---------
		post("tickets.projects", "/api/Tickets/GetAllProjects",
			"Ticket projects with per-project ticket counts",
			flag("includeInactive", "Include inactive projects (default: active only)"),
		),
		post("tickets.mine", "/api/Tickets/GetMyTickets",
			"Tickets raised by a user",
			user(num("userId", "Requester user id (default: the configured user)")),
			str("status", "Open / Assign / InProgress / OnHold / Close"),
			num("projectId", "Filter by project id"),
			num("month", "Month 1-12"), num("year", "Year"),
		),
		post("tickets.all", "/api/Tickets/GetAllTickets",
			"Every ticket across all users (admin view)",
			str("status", "Open / Assign / InProgress / OnHold / Close"),
			num("projectId", "Filter by project id"),
			str("priority", "Low / Medium / High / Critical"),
			num("month", "Month 1-12"), num("year", "Year"),
		),
		post("tickets.assigned", "/api/Tickets/GetAssignedTickets",
			"Tickets assigned to a user",
			user(num("assigneeUserId", "Assignee user id (default: the configured user)")),
			str("status", "Assign / InProgress / OnHold / Close"),
			num("projectId", "Filter by project id"),
			num("month", "Month 1-12"), num("year", "Year"),
		),
		post("tickets.ticket", "/api/Tickets/GetTicketById",
			"One full ticket incl. requester name/email",
			req(num("ticketId", "Ticket id")),
		),
		post("tickets.timeline", "/api/Tickets/GetTicketTimeline",
			"Activity history for one ticket (action, old/new, user, time)",
			req(num("ticketId", "Ticket id")),
		),
		post("tickets.attachments", "/api/Tickets/GetAttachmentsByTicketId",
			"Attachment metadata rows for one ticket (metadata only, no bytes)",
			req(num("ticketId", "Ticket id")),
		),
		post("tickets.comments", "/api/Tickets/GetCommentsByTicketId",
			"Comment rows for one ticket",
			req(num("ticketId", "Ticket id")),
			def(flag("includeInternal", "Include internal-only notes (default true)"), true),
		),
		post("tickets.workload", "/api/Tickets/GetMyWorkloadSummary",
			"Status-count workload summary for an assignee",
			user(num("assigneeUserId", "Assignee user id (default: the configured user)")),
		).rawEnvelope(), // returns success:false with a message when empty
		get("tickets.users", "/api/Tickets/GetUsersForAssignment",
			"Assignable users with their active-ticket counts",
		),

		// -- tasks: Task Manager ------------------------------------------
		post("tasks.list", "/api/Task/GetAllTasks",
			"Task list (paged, filterable)",
			user(num("employeeId", "Task-system employee id (default: the configured user)")),
			def(num("roleTypeId", "Role type id (default 1)"), 1),
			def(str("viewMode", "OWN | TEAM | ALL (default ALL)"), "ALL"),
			str("status", "PENDING|SUBMITTED|IN_PROGRESS|COMPLETED|NOT_STARTED"),
			str("priority", "LOW|MEDIUM|HIGH|CRITICAL"),
			str("taskType", "SELF | ASSIGNED"),
			num("assignedToEmployeeId", "Filter to tasks assigned to this employee id"),
			def(num("page", "Page (default 1)"), 1),
			def(wire(num("page_size", "Rows per page (default 50)"), "limit"), 50),
		).with("sortBy", "created_on").with("sortOrder", "DESC"),
		post("tasks.dashboard", "/api/Task/GetDashboard",
			"Task stat cards: my/team totals + per-member breakdown",
			user(num("employeeId", "Task-system employee id (default: the configured user)")),
			def(num("roleTypeId", "Role type id (default 1)"), 1),
		),
		get("tasks.team", "/TaskWeb/GetTeamMembers",
			"Team member roster (id/name/code/designation/role)",
			str("scope", "Optional scope, e.g. 'allhods' for the HOD list"),
		),
		get("tasks.tree", "/TaskWeb/GetHierarchyTree",
			"HOD department -> sub-HODs -> executives task hierarchy with counts",
		),
		get("tasks.details", "/api/Task/GetTaskDetails/{taskId}",
			"Full single-task record",
			inPath(str("taskId", "Task id (string)")),
		),
		get("tasks.progress", "/api/Task/GetProgressUpdates/{taskId}",
			"Progress-update log rows for one task",
			inPath(str("taskId", "Task id (string)")),
		),

		// -- hierarchy: the 227-row employee org tree ---------------------
		// Salary columns ride along in several of these payloads; they are
		// stripped by key before anything leaves this server (see redact.go).
		get("hierarchy.tree", "/api/Hierarchy/GetHierarchyTree",
			"Full HO org tree, one nested node per HOD",
		),
		get("hierarchy.flat", "/api/Hierarchy/GetMasterFlatAdmin",
			"Flat HO hierarchy rows — the best tabular source (~202 rows)",
		),
		get("hierarchy.search", "/api/Hierarchy/SearchEmployees",
			"Search HO employees by term / role / active flag",
			str("searchTerm", "Name or employee-code search text"),
			num("roleTypeId", "Role filter: 1=HOD, 2=Sub-HOD, 3=Executive"),
			str("isActive", "Active filter: true or false"),
			num("pageSize", "Max rows to return"),
		),
		get("hierarchy.employee", "/api/Hierarchy/GetEmployee/{employeeId}",
			"Full employee record with reportsTo[] and directReports[]",
			inPath(num("employeeId", "Employee id")),
		),
		get("hierarchy.details", "/HierarchyWeb/GetEmployeeHierarchyDetails",
			"Employee record by id (Employee Hierarchy page source)",
			req(num("id", "Employee id")),
		),
		get("hierarchy.orphans", "/api/Hierarchy/GetOrphanEmployees",
			"Unassigned persons (no reporting relationship)",
		),
		get("hierarchy.hods", "/api/Hierarchy/GetActiveHODs", "Active HOD list (id, name, code)"),
		get("hierarchy.departments", "/api/Hierarchy/GetDepartments",
			"Department master, optionally with nested sub-departments",
			def(str("includeSubDepartments", "Include sub-departments (true/false)"), "true"),
		),
		get("hierarchy.subdepts", "/api/Hierarchy/GetSubDepartments/{departmentId}",
			"Sub-departments of one department",
			inPath(num("departmentId", "Department id")),
		),
		get("hierarchy.hod-depts", "/api/Hierarchy/GetDepartmentsForHOD/{hodEmployeeId}",
			"Departments owned by one HOD (with counts)",
			inPath(num("hodEmployeeId", "HOD employee id")),
		),
		get("hierarchy.subhods", "/api/Hierarchy/GetSubHODsForEdit",
			"Sub-HODs under one HOD",
			req(num("hodId", "HOD employee id")),
		),
		get("hierarchy.roles", "/api/Hierarchy/GetRoleTypes", "The 3 role types (HOD / Sub-HOD / Executive)"),
		get("hierarchy.extras", "/api/Hierarchy/GetEmployeeModalExtras",
			"Employee extras (gender/qualification/area)",
			req(num("employeeId", "Employee id")),
		),
		get("hierarchy.fields", "/api/Hierarchy/GetCustomFields", "Custom-field definitions"),
		get("hierarchy.custom-values", "/api/Hierarchy/GetEmployeeCustomValues",
			"Custom-field values (omit the id for all employees)",
			num("employeeId", "Employee id to scope to"),
		),
		get("hierarchy.logs", "/api/Hierarchy/GetAuditLogs",
			"HO hierarchy audit trail (paged)",
			def(num("pageNumber", "Page number (default 1)"), 1),
			def(num("pageSize", "Rows per page (default 30)"), 30),
			str("searchTerm", "Free-text search"),
			str("actionType", "Action filter (Create/Update/RoleChange/...)"),
		),
		get("hierarchy.sales-tree", "/HierarchyWeb/GetSalesHierarchyTree",
			"Nested sales tree (H1->H2->H3->H4->group->employees)",
		),
		get("hierarchy.sales", "/HierarchyWeb/GetSalesData",
			"Flat sales rows (H1-H4 chain codes/names per employee)",
		),
		get("hierarchy.sales-stats", "/HierarchyWeb/GetSalesStats", "Sales level/employee counts"),
		get("hierarchy.sales-lookups", "/HierarchyWeb/GetSalesLookups", "Sales lookups: states, groups, designations"),
		get("hierarchy.sales-employees", "/HierarchyWeb/GetSalesEmployeeList", "Sales employee list (id, name, code)"),
		get("hierarchy.sales-logs", "/HierarchyWeb/GetSalesAuditLogs",
			"Sales hierarchy audit trail",
			def(num("pageSize", "Rows to return (default 100)"), 100),
			def(str("search", "Search text"), "SalesHierarchy"),
		),

		// -- dochub: Document Hub metadata (no bytes) ---------------------
		get("dochub.hub", "/DocumentHub/GetHub",
			"Directory listing: folders, files, breadcrumb, stats, permissions",
			num("folderId", "Folder id to list (omit for root)"),
			str("filter", "View filter: '' (all) | recent | trash"),
			str("search", "Search text (matches file/folder names)"),
		),
		get("dochub.folders", "/DocumentHub/GetFolders", "Flat list of ALL folders (build the tree via parentFolderId)"),
		get("dochub.file", "/DocumentHub/FileAccessInfo",
			"File metadata + isConfidential/accessGranted flags",
			req(num("fileId", "File id")),
		),
		get("dochub.versions", "/DocumentHub/VersionHistory",
			"Stored version history for a file",
			req(num("fileId", "File id")),
		),
		get("dochub.activity", "/DocumentHub/ActivityLog",
			"Audit trail (view/upload/...) for a file",
			req(num("fileId", "File id")),
		),
		get("dochub.backups", "/DocumentHub/GetBackups", "Backup snapshot list (Full/Incremental)"),
		get("dochub.backup", "/DocumentHub/GetBackupContent",
			"Snapshot manifest: folders, files, versions, activities",
			req(str("backupId", "Backup id, e.g. DH-20260710110815")),
		),

		// -- inventory: physical stock-count audits -----------------------
		get("inventory.active", "/api/InventoryAudit/GetUserActiveSessions",
			"Active audit sessions assigned to a user",
			user(num("userId", "User id (default: the configured user)")),
		),
		get("inventory.inactive", "/api/InventoryAudit/GetUserInactiveSessions",
			"Inactive/deactivated sessions assigned to a user",
			user(num("userId", "User id (default: the configured user)")),
		),
		get("inventory.created-active", "/api/InventoryAudit/GetActiveSessionsByUser",
			"Active audit sessions created by a user",
			user(num("createdBy", "Creator user id (default: the configured user)")),
		),
		get("inventory.created-inactive", "/api/InventoryAudit/GetInActiveSessionsByUser",
			"Inactive audit sessions created by a user",
			user(num("createdBy", "Creator user id (default: the configured user)")),
		),
		get("inventory.report", "/api/InventoryAudit/DownloadInventoryReport",
			"Item-level audit report: system vs physical qty/value/litre per item",
			req(str("lotNumber", "Lot number, e.g. KAMALPREET19")),
			user(num("userId", "User id (default: the configured user)")),
		),
		get("inventory.users", "/api/auth/getallusers",
			"JSAP user directory (id, name, phone, email, role, status)",
		).company("company"),

		// -- meta: platform identity & permissions ------------------------
		get("meta.companies", "/api/auth/getcompanies",
			"Companies this user belongs to",
			user(num("userId", "User id (default: the configured user)")),
		),
		get("meta.departments", "/api/auth/getdepartments",
			"Department list",
		).company("company"),
		get("meta.permissions", "/api/Permission/GetUserEffectivePermissions",
			"Effective module/permission rows for a user in a company",
			user(num("UserId", "User id (default: the configured user)")),
		).company("CompanyId"),

		// -- qc: the master quality-check template ------------------------
		get("qc.form", "/api/QC/GetFormStructureV2",
			"Current QC template: header, thresholds, mandatory-document flags, parameter tree",
		),

		// -- users: JSAP's own permission model ---------------------------
		get("users.list", "/UserManagement/AllUsers",
			"All registered users (name, empId, type, department, status)",
		).htmlUsers(),
		get("users.unregistered", "/api/auth/getusernotregisterincompany",
			"Users not yet registered in the selected company",
		).company("company"),
		get("users.roles", "/api/auth/getroles", "Role catalog for the selected company").company("company"),
		get("users.states", "/api/auth/getstates", "State/zone codes for the selected company").company("company"),
		get("users.branches", "/api/auth/getbranches", "Branches for the selected company").company("company"),
		get("users.budgets", "/api/auth/getbudgets", "Budget heads for the selected company").company("company"),
		get("users.subbudgets", "/api/auth/getSubBudgets", "Sub-budgets for the selected company").company("company"),
		get("users.approvals", "/api/auth/getapprovals", "Approval types for the selected company").company("company"),
		get("users.varieties", "/api/auth/getVarieties", "Item sub-groups (varieties) for the selected company").company("company"),
		get("users.reports", "/api/auth/getreports", "Report catalog for the selected company").company("company"),

		// -- dashboards: IT standards, IT projects, MoM, budget fact table -
		get("dashboards.it-summary", "/api/Dashboard/GetSummary",
			"IT-standards priority/gap counts {p1,p2,p3,high,medium,low}",
		),
		get("dashboards.it-master", "/api/Dashboard/GetMaster",
			"Full IT-standards register rows",
			str("priority", "Optional priority filter: P1|P2|P3"),
		),
		get("dashboards.task-stats", "/api/Dashboard/stats",
			"Task KPI row by group (group_by is required by the server)",
			filtersRequiringGroupBy()...,
		),
		get("dashboards.task-status", "/api/Dashboard/status-distribution",
			"Task status distribution [{status,count}]",
			taskFilters()...,
		),
		get("dashboards.task-employees", "/api/Dashboard/employee-stats",
			"Per-assignee task totals",
			taskFilters()...,
		),
		get("dashboards.task-trend", "/api/Dashboard/trend",
			"Daily created/completed task series",
			withFilters(num("days", "Number of days back (the page uses 7)"))...,
		),
		get("dashboards.task-list", "/api/Dashboard/list",
			"Task rows for the dashboard table",
			taskFilters()...,
		),
		get("dashboards.projects", "/api/Dashboard/projects", "Project-name list (for task filters)"),
		get("dashboards.employees", "/api/Dashboard/employees", "Employee list {employeeId, employeeName}"),
		get("dashboards.task", "/api/Dashboard/details",
			"Single dashboard task detail by id",
			req(num("taskId", "Task id")),
		),
		get("dashboards.clients", "/api/Dashboard/GetDashboardMaster",
			"Per-client project/module/progress/hours summary (+TOTAL)",
		),
		get("dashboards.client-projects", "/api/Dashboard/GetDashboardByCompany",
			"Projects of one client",
			req(str("clientName", "Client name, e.g. JIVO")),
		),
		get("dashboards.project-modules", "/api/Dashboard/GetDashboardProject",
			"Modules of one project",
			req(num("projectId", "Project id")),
		),
		get("dashboards.mom", "/api/Dashboard/GetAllMoM", "All meeting-minutes (MoM) records"),
		get("dashboards.budget-data", "/api/Dashboard/getBudgetDataByBranch",
			"JSAP budget fact table by branch (heavy — filter locally)",
			str("branch", "Branch filter: OIL|BEVERAGE (omit for all)"),
		),
	}

	for idx := range out {
		out[idx].keywords = keywordsFor(out[idx])
	}
	sort.Slice(out, func(a, c int) bool { return out[a].ID < out[c].ID })
	return out
}

func keywordsFor(c Command) []string {
	text := strings.ToLower(strings.Join([]string{c.ID, c.Group, c.Summary, c.Path}, " "))
	text = strings.Map(func(r rune) rune {
		switch {
		case r >= 'a' && r <= 'z', r >= '0' && r <= '9':
			return r
		default:
			return ' '
		}
	}, text)
	return strings.Fields(text)
}

// Commands returns the whole catalogue, sorted by id.
func Commands() []Command { return commands }

// Lookup finds one command by its exact id.
func Lookup(id string) (Command, bool) {
	for _, c := range commands {
		if c.ID == id {
			return c, true
		}
	}
	return Command{}, false
}

// Search ranks catalogued commands against a natural-language query by naive
// token overlap. Anything cleverer belongs on the agent side.
func Search(query string, limit int) []Command {
	if limit <= 0 {
		limit = 10
	}
	terms := strings.Fields(strings.ToLower(query))
	type scored struct {
		cmd   Command
		score int
	}
	var hits []scored
	for _, c := range commands {
		score := 0
		for _, term := range terms {
			for _, kw := range c.keywords {
				if kw == term {
					score += 3
				} else if strings.Contains(kw, term) || strings.Contains(term, kw) {
					score++
				}
			}
		}
		if score > 0 {
			hits = append(hits, scored{c, score})
		}
	}
	sort.SliceStable(hits, func(a, b int) bool {
		if hits[a].score != hits[b].score {
			return hits[a].score > hits[b].score
		}
		return hits[a].cmd.ID < hits[b].cmd.ID
	})
	if len(hits) > limit {
		hits = hits[:limit]
	}
	out := make([]Command, 0, len(hits))
	for _, h := range hits {
		out = append(out, h.cmd)
	}
	return out
}

// ParamNames lists a command's declared parameter names, for error messages.
func (c Command) ParamNames() []string {
	names := make([]string, 0, len(c.Params))
	for _, p := range c.Params {
		names = append(names, p.Name)
	}
	sort.Strings(names)
	return names
}

// bind validates caller arguments against the declared parameters and returns
// the concrete path, query and body. Unknown arguments are REJECTED, never
// ignored: silently dropping one would let a caller believe a filter applied.
func (c Command) bind(args map[string]any, configuredUser, company int) (string, url.Values, map[string]any, error) {
	declared := map[string]Param{}
	for _, p := range c.Params {
		declared[p.Name] = p
	}
	for name := range args {
		if _, ok := declared[name]; !ok {
			return "", nil, nil, errf("unknown parameter %q for command %s — valid parameters: %s",
				name, c.ID, strings.Join(c.ParamNames(), ", "))
		}
	}

	path := c.Path
	query := url.Values{}
	body := map[string]any{}

	for _, p := range c.Params {
		raw, supplied := args[p.Name]
		if !supplied || raw == nil {
			switch {
			case p.FromUser:
				raw = configuredUser
			case p.Default != nil:
				raw = p.Default
			case p.Required:
				return "", nil, nil, errf("command %s requires parameter %q (%s)", c.ID, p.Name, p.Help)
			default:
				continue
			}
		}
		value, err := coerce(p, raw)
		if err != nil {
			return "", nil, nil, err
		}
		if p.InPath {
			path = strings.ReplaceAll(path, "{"+p.Name+"}", url.PathEscape(fmt.Sprint(value)))
			continue
		}
		if c.Method == verbPost {
			body[p.wire()] = value
		} else {
			query.Set(p.wire(), fmt.Sprint(value))
		}
	}

	for _, f := range c.Fixed {
		if c.Method == verbPost {
			body[f.Name] = f.Value
		} else {
			query.Set(f.Name, fmt.Sprint(f.Value))
		}
	}

	if c.CompanyParam != "" {
		if c.Method == verbPost {
			body[c.CompanyParam] = company
		} else {
			query.Set(c.CompanyParam, strconv.Itoa(company))
		}
	}

	if strings.Contains(path, "{") {
		return "", nil, nil, errf("command %s left an unfilled path placeholder in %q", c.ID, path)
	}
	if c.Method != verbPost {
		body = nil
	}
	return path, query, body, nil
}

// coerce turns an MCP argument (JSON: string, float64 or bool) into the wire
// type the parameter declares, refusing anything that does not fit.
func coerce(p Param, raw any) (any, error) {
	switch p.Type {
	case TypeInt:
		switch v := raw.(type) {
		case int:
			return v, nil
		case int64:
			return int(v), nil
		case float64:
			if v != float64(int(v)) {
				return nil, errf("parameter %q must be a whole number, got %v", p.Name, v)
			}
			return int(v), nil
		case string:
			n, err := strconv.Atoi(strings.TrimSpace(v))
			if err != nil {
				return nil, errf("parameter %q must be an integer, got %q", p.Name, v)
			}
			return n, nil
		default:
			return nil, errf("parameter %q must be an integer, got %T", p.Name, raw)
		}
	case TypeBool:
		switch v := raw.(type) {
		case bool:
			return v, nil
		case string:
			parsed, err := strconv.ParseBool(strings.TrimSpace(v))
			if err != nil {
				return nil, errf("parameter %q must be true or false, got %q", p.Name, v)
			}
			return parsed, nil
		default:
			return nil, errf("parameter %q must be a boolean, got %T", p.Name, raw)
		}
	default:
		var out string
		switch v := raw.(type) {
		case string:
			out = v
		case float64:
			if v == float64(int(v)) {
				out = strconv.Itoa(int(v))
			} else {
				out = strconv.FormatFloat(v, 'f', -1, 64)
			}
		case bool:
			out = strconv.FormatBool(v)
		case int:
			out = strconv.Itoa(v)
		default:
			return nil, errf("parameter %q must be a string, got %T", p.Name, raw)
		}
		if p.Upper {
			out = strings.ToUpper(out)
		}
		return out, nil
	}
}
