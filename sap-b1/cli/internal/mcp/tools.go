package mcp

import (
	"context"
	"errors"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/mark3labs/mcp-go/mcp"

	"sapb1/internal/catalog"
	"sapb1/internal/client"
	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// maxSuggestions caps the "did you mean?" hints on an unknown-entity miss.
const maxSuggestions = 5

// safeErr renders an error as a string with the configured password scrubbed
// out, defensively guaranteeing the secret never reaches a tool result even if
// some future error path were to include it.
func (s *Server) safeErr(err error) string {
	msg := err.Error()
	if s.cfg.Password != "" {
		msg = strings.ReplaceAll(msg, s.cfg.Password, "****")
	}
	return msg
}

// toolErr wraps an error into an MCP tool error result (IsError=true) with the
// password scrubbed. Returning (result, nil) — not a Go error — surfaces it to
// the agent as a readable tool-level failure rather than a protocol error.
func (s *Server) toolErr(err error) (*mcp.CallToolResult, error) {
	return mcp.NewToolResultError(s.safeErr(err)), nil
}

// toolErrf builds a tool error result from a formatted message (no secrets).
func toolErrf(format string, a ...any) (*mcp.CallToolResult, error) {
	return mcp.NewToolResultError(fmt.Sprintf(format, a...)), nil
}

// jsonResult marshals payload into a JSON tool result, or a tool error if the
// value can't be encoded.
func (s *Server) jsonResult(payload any) (*mcp.CallToolResult, error) {
	res, err := mcp.NewToolResultJSON(payload)
	if err != nil {
		return toolErrf("failed to encode result as JSON: %v", err)
	}
	return res, nil
}

// combineFilters ANDs together non-empty OData filter fragments, parenthesizing
// each so a caller-supplied filter can't change the precedence of a built-in
// one. Mirrors the CLI's combineFilters.
func combineFilters(parts ...string) string {
	var nonEmpty []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			nonEmpty = append(nonEmpty, "("+p+")")
		}
	}
	return strings.Join(nonEmpty, " and ")
}

// cfgFor returns a copy of the server's config scoped to one company database.
//
// The copy is a shallow copy of the Config VALUE, which is safe because every
// field of config.Config is a scalar (no slices, maps or pointers to share).
// Overriding CompanyDB is a genuine re-scoping, not a label: the client posts
// cfg.CompanyDB in the /Login body, so the Service Layer session itself is
// opened against the requested company.
func (s *Server) cfgFor(company string) *config.Config {
	cp := *s.cfg
	cp.CompanyDB = company
	return &cp
}

// clientFor builds a fresh client for one already-resolved config. Every tool
// that touches SAP goes through here — there is deliberately no other
// constructor in this package.
//
// Fresh-per-call is kept on purpose: client.Client mutates its own session
// fields, and the HTTP transport runs tool calls concurrently, so sharing one
// Client would be a data race. What IS shared is the session itself, via the
// server's client.SessionStore: the store's per-identity lock means a burst of
// concurrent calls costs ONE Login, not one per call. Before it existed, 30
// parallel calls opened 29 SAP sessions — 29 licensed Service Layer slots held
// for their full TTL, since the MCP path never logs out.
func (s *Server) clientFor(cfg *config.Config) *client.Client {
	return client.NewWithSessions(cfg, s.sessions)
}

// company resolves the `company` argument of a decoded call. Used by every
// tool that actually reads SAP: a company is required, and a wrong one is an
// error rather than a silent fallback to the default.
func (s *Server) company(a *toolArgs) (string, error) {
	return resolveCompany(a.Str("company"), s.cfg.CompanyDB)
}

// companyEcho is the lenient form, for the tools that do not read SAP
// (sapb1_entities, sapb1_ops — the embedded catalog — and sapb1_doctor, whose
// whole job is to report on broken config). A supplied company is still
// validated; an omitted one echoes whatever is configured, which may be
// nothing. This is what keeps the catalog tools working fully offline, with no
// config at all.
func (s *Server) companyEcho(a *toolArgs) (string, error) {
	arg := strings.TrimSpace(a.Str("company"))
	if arg == "" {
		return s.cfg.CompanyDB, nil
	}
	return resolveCompany(arg, s.cfg.CompanyDB)
}

// queryRequest is one fully-resolved read. Exactly one of Count/All/plain-top
// applies; the decoder has already rejected any combination of them.
type queryRequest struct {
	Company  string
	Entity   string
	Select   string
	Filter   string
	OrderBy  string
	Top      int
	Skip     int
	PageSize int
	All      bool
	Count    bool
}

// rowsResponse is THE response shape of every row-returning tool, in every
// mode. One shape means an agent never has to guess which fields it got.
//
// Field notes that matter:
//   - rows_in_page is len(rows) in THIS response. It replaces the old "count",
//     which was rows-in-page sitting next to a 20-row cap and read like a total.
//   - total_count is the server's own total ($inlinecount=allpages). It is
//     omitted rather than guessed when the server didn't give one.
//   - truncated is ALWAYS present, so "is that everything?" is answerable
//     without inference.
//   - next_skip appears exactly when truncated, and is the value to pass back
//     as skip with the SAME filter/orderby.
//   - as_of is the SAP server's clock, so a count can be quoted "as of HH:MM"
//     and live drift reads as drift rather than as an error.
type rowsResponse struct {
	Company    string           `json:"company"`
	Entity     string           `json:"entity"`
	RowsInPage int              `json:"rows_in_page"`
	TotalCount *int64           `json:"total_count,omitempty"`
	Truncated  bool             `json:"truncated"`
	NextSkip   *int             `json:"next_skip,omitempty"`
	AsOf       string           `json:"as_of"`
	AsOfSource string           `json:"as_of_source"`
	Rows       []map[string]any `json:"rows"`
}

// asOfFrom stamps a response from the SAP server's HTTP Date header, falling
// back to this machine's clock and SAYING SO when the server sent none.
func asOfFrom(res *client.QueryResult) (string, string) {
	if res != nil && res.ServerDateKnown {
		return res.ServerDate.UTC().Format(time.RFC3339), "server"
	}
	return time.Now().UTC().Format(time.RFC3339), "local"
}

// newRowsResponse assembles the one response shape.
func newRowsResponse(q queryRequest, res *client.QueryResult, rows []map[string]any, truncated bool) rowsResponse {
	if rows == nil {
		rows = []map[string]any{}
	}
	asOf, src := asOfFrom(res)
	out := rowsResponse{
		Company:    q.Company,
		Entity:     q.Entity,
		RowsInPage: len(rows),
		Truncated:  truncated,
		AsOf:       asOf,
		AsOfSource: src,
		Rows:       rows,
	}
	if res != nil && res.CountKnown {
		total := res.Count
		out.TotalCount = &total
	}
	if truncated {
		next := q.Skip + len(rows)
		out.NextSkip = &next
	}
	return out
}

// truncatedWith enforces the one invariant that makes the documented resume
// protocol ("call again with skip=next_skip") terminate: a page that returned
// NO rows can never be truncated.
//
// If it were, next_skip would equal the skip we just used, so the agent would
// re-issue the identical call, get an empty page again, and loop forever — each
// round a fresh request. A zero-row page also cannot be resumed usefully by any
// other offset we could invent, so the honest report is "that is everything we
// could read", with total_count still carried so the caller can see the server's
// own number disagreeing.
func truncatedWith(rows []map[string]any, truncated bool) bool {
	if len(rows) == 0 {
		return false
	}
	return truncated
}

// runQuery is the shared read path behind sapb1_query and the convenience
// tools. It only ever issues GETs (plus Login/Logout inside the client).
func (s *Server) runQuery(ctx context.Context, q queryRequest) (*mcp.CallToolResult, error) {
	q.Entity = strings.TrimSpace(q.Entity)
	if q.Entity == "" {
		return toolErrf("entity is required, e.g. \"Orders\"")
	}
	// The entity is concatenated in front of the query string to build the
	// request path, so a name carrying '#', '?', '&', '%' or whitespace would
	// change the SHAPE of the request rather than name an entity — a '#' in
	// particular turns $filter/$select/$orderby/$top into a URI fragment that is
	// never sent, and the call then succeeds while quietly answering a different
	// question. Rejected here so the failure is loud and local; the client
	// re-checks it independently for the CLI's sake.
	if err := client.ValidateEntitySet(q.Entity); err != nil {
		return s.toolErr(err)
	}
	cfg := s.cfgFor(q.Company)
	if err := cfg.ValidateConnection(); err != nil {
		return s.toolErr(err)
	}
	if err := cfg.ValidateCompanyDB(); err != nil {
		return s.toolErr(err)
	}
	c := s.clientFor(cfg)

	switch {
	case q.Count:
		return s.runCount(ctx, c, q)
	case q.All:
		return s.runAll(ctx, c, q)
	default:
		return s.runTop(ctx, c, q)
	}
}

// runCount asks the server for the total and returns ONLY that. It is one
// request, so the number is atomic — unlike a paged tally, which can straddle
// live postings and land between two truths.
//
// It costs no rows at all: CountOnly sends $top=0, so the Service Layer answers
// with the total in ~120 bytes. The earlier $top=1 hauled one complete SAP
// document (14,460 bytes on BusinessPartners) purely to read a header, and a
// tool's default $select only softened that for the four convenience tools —
// sapb1_query, which has no default field set and cannot invent one for an
// arbitrary entity, still paid the whole document. $top=0 fixes it everywhere
// at once, and needs no per-entity knowledge.
func (s *Server) runCount(ctx context.Context, c *client.Client, q queryRequest) (*mcp.CallToolResult, error) {
	res, err := c.Query(ctx, q.Entity, client.QueryOptions{
		Filter:    q.Filter,
		CountOnly: true,
	})
	if err != nil {
		return s.toolErr(err)
	}
	if !res.CountKnown {
		// Never substitute rows-in-page for a total. A wrong total that looks
		// right is worse than a failed call — and since the request asked for
		// $top=0, the substitute would be 0: every entity set reported empty.
		return toolErrf("the Service Layer did not return a server-side total (odata.count) for %s in %s — "+
			"refusing to answer with anything else. "+
			"Re-run with all=true and read total_count/rows_in_page instead.", q.Entity, q.Company)
	}
	return s.jsonResult(newRowsResponse(q, res, nil, false))
}

// runAll sweeps every matching row via odata.nextLink, up to maxAllRows.
//
// Truncation is decided ONLY by the two things that actually stopped the sweep
// early: the row cap (detected exactly, by asking for one row more than the cap
// and seeing whether it arrives) and the page cap (client.MaxPages). If neither
// fired, the sweep ended because odata.nextLink ran out — the set IS exhausted.
//
// It deliberately does NOT infer truncation from odata.count > rows held.
// $inlinecount is skip-agnostic and computed on the first page, so it
// legitimately exceeds the rows a complete sweep returns whenever rows are
// deleted mid-sweep, or row-level authorisation/a view filters what comes back.
// Treating that as "more rows exist" made a COMPLETE sweep report truncated,
// and — when the final page was empty — produced a fixed point (rows 0,
// truncated true, next_skip unchanged) that loops an agent forever. The
// server's own total is still reported as total_count, so a caller can see the
// disagreement instead of being told a story about it.
func (s *Server) runAll(ctx context.Context, c *client.Client, q queryRequest) (*mcp.CallToolResult, error) {
	pageSize := q.PageSize
	if pageSize <= 0 {
		pageSize = defaultAllPageSize
	}
	res, err := c.QueryAll(ctx, q.Entity, client.QueryOptions{
		Select:      q.Select,
		Filter:      q.Filter,
		OrderBy:     q.OrderBy,
		Skip:        q.Skip,
		PageSize:    pageSize,
		InlineCount: true,
		Top:         maxAllRows + 1, // N+1 probe
	})
	if err != nil {
		return s.toolErr(err)
	}

	rows := res.Value
	truncated := res.Capped || len(rows) > maxAllRows
	if len(rows) > maxAllRows {
		rows = rows[:maxAllRows]
	}
	return s.jsonResult(newRowsResponse(q, res, rows, truncatedWith(rows, truncated)))
}

// runTop returns at most `top` rows, following odata.nextLink as needed — so a
// top larger than the Service Layer's page size finally works — and says
// whether more rows exist by asking for one extra and checking if it came.
//
// It asks for $inlinecount too. This is the mode agents use by default, and
// without it a truncated answer said "there is more" with no sense of how much
// more: 20 rows out of 46 and 20 out of 46,000 looked identical. The total
// rides along on a request we were making anyway.
//
// The default page size is the size of the answer (top+1), not the Service
// Layer's 20: at the old default, top=20 cost two round trips and pulled 40
// rows to return 20.
func (s *Server) runTop(ctx context.Context, c *client.Client, q queryRequest) (*mcp.CallToolResult, error) {
	top := q.Top
	if top <= 0 {
		top = defaultTop
	}
	pageSize := q.PageSize
	if pageSize <= 0 {
		pageSize = top + 1
		if pageSize > maxPageSize {
			pageSize = maxPageSize
		}
	}
	res, err := c.QueryAll(ctx, q.Entity, client.QueryOptions{
		Select:      q.Select,
		Filter:      q.Filter,
		OrderBy:     q.OrderBy,
		Skip:        q.Skip,
		PageSize:    pageSize,
		InlineCount: true,
		Top:         top + 1, // N+1 probe
	})
	if err != nil {
		return s.toolErr(err)
	}

	rows := res.Value
	truncated := len(rows) > top || res.Capped
	if len(rows) > top {
		rows = rows[:top]
	}
	return s.jsonResult(newRowsResponse(q, res, rows, truncatedWith(rows, truncated)))
}

// rowRequest turns a decoded argument set into a queryRequest, resolving the
// company and applying the tool's default select/orderby.
func (s *Server) rowRequest(a *toolArgs, entity, extraFilter, defSelect, defOrderBy string) (queryRequest, error) {
	company, err := s.company(a)
	if err != nil {
		return queryRequest{}, err
	}
	sel := a.Str("select")
	if sel == "" {
		sel = defSelect
	}
	ob := a.Str("orderby")
	if ob == "" {
		ob = defOrderBy
	}
	return queryRequest{
		Company:  company,
		Entity:   entity,
		Select:   sel,
		Filter:   combineFilters(extraFilter, a.Str("filter")),
		OrderBy:  ob,
		Top:      a.Int("top", 0),
		Skip:     a.Int("skip", 0),
		PageSize: a.Int("page_size", 0),
		All:      a.Bool("all"),
		Count:    a.Bool("count"),
	}, nil
}

// handleDoctor mirrors `sapb1 doctor`: config → TCP reachability → Login,
// against the requested company (so it can prove Mart or Beverages is
// reachable, not just the default).
func (s *Server) handleDoctor(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_doctor", req)
	if err != nil {
		return s.toolErr(err)
	}
	// Doctor is the tool you reach for when config is broken, so an unset
	// default company must still produce a report rather than an error.
	company, err := s.companyEcho(a)
	if err != nil {
		return s.toolErr(err)
	}
	cfg := s.cfgFor(company)

	type check struct {
		Name   string `json:"name"`
		OK     bool   `json:"ok"`
		Detail string `json:"detail"`
		Hint   string `json:"hint,omitempty"`
	}
	report := struct {
		OK      bool           `json:"ok"`
		Company string         `json:"company"`
		Config  map[string]any `json:"config"`
		Checks  []check        `json:"checks"`
	}{
		Company: orNotSet(company),
		Config: map[string]any{
			"host":      orNotSet(cfg.Host),
			"port":      cfg.Port,
			"companyDB": orNotSet(cfg.CompanyDB),
			"user":      orNotSet(cfg.User),
			"password":  cfg.MaskedPassword(), // never the real secret
			"insecure":  cfg.Insecure,
			"timeout":   cfg.Timeout,
		},
	}

	// 1. Configuration.
	var missing []string
	if cfg.Host == "" {
		missing = append(missing, "SAPB1_HOST")
	}
	if cfg.User == "" {
		missing = append(missing, "SAPB1_USER")
	}
	if cfg.Password == "" {
		missing = append(missing, "SAPB1_PASSWORD")
	}
	if cfg.CompanyDB == "" {
		missing = append(missing, "SAPB1_COMPANYDB")
	}
	configOK := len(missing) == 0
	cfgCheck := check{Name: "configuration", OK: configOK}
	if configOK {
		cfgCheck.Detail = "host, user, password, and companyDB are all set"
	} else {
		cfgCheck.Detail = "missing: " + strings.Join(missing, ", ")
		cfgCheck.Hint = "set them in ~/sapb1-cli/.env or via SAPB1_* environment variables in the MCP server config"
	}
	report.Checks = append(report.Checks, cfgCheck)

	// 2. TCP reachability.
	reachable := false
	netCheck := check{Name: "network"}
	if cfg.Host == "" {
		netCheck.Detail = "skipped — no host configured"
	} else {
		const probe = 8 * time.Second
		timeout := probe
		if t := time.Duration(cfg.Timeout) * time.Second; cfg.Timeout > 0 && t < timeout {
			timeout = t
		}
		if err := client.CheckTCPReachable(cfg.HostPort(), timeout); err != nil {
			netCheck.Detail = fmt.Sprintf("cannot reach %s over TCP", cfg.HostPort())
			netCheck.Hint = "are you on the company VPN, or is your IP whitelisted on the SAP firewall?"
		} else {
			reachable = true
			netCheck.OK = true
			netCheck.Detail = fmt.Sprintf("%s is reachable over TCP", cfg.HostPort())
		}
	}
	report.Checks = append(report.Checks, netCheck)

	// 3. Login — against the requested company.
	loginCheck := check{Name: "login"}
	switch {
	case !configOK:
		loginCheck.Detail = "skipped — fix configuration first"
	case !reachable:
		loginCheck.Detail = "skipped — host is not reachable"
	default:
		if err := s.clientFor(cfg).Login(ctx); err != nil {
			loginCheck.Detail = s.safeErr(err)
			loginCheck.Hint = "check credentials and CompanyDB"
		} else {
			loginCheck.OK = true
			loginCheck.Detail = fmt.Sprintf("connected to %s as %s", cfg.CompanyDB, cfg.User)
		}
	}
	report.Checks = append(report.Checks, loginCheck)

	report.OK = configOK && reachable && loginCheck.OK
	return s.jsonResult(report)
}

// handleQuery is the core generic read tool.
func (s *Server) handleQuery(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_query", req)
	if err != nil {
		return s.toolErr(err)
	}
	q, err := s.rowRequest(a, a.Str("entity"), "", "", "")
	if err != nil {
		return s.toolErr(err)
	}
	return s.runQuery(ctx, q)
}

// handleEntities lists catalog services (offline).
func (s *Server) handleEntities(_ context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_entities", req)
	if err != nil {
		return s.toolErr(err)
	}
	company, err := s.companyEcho(a)
	if err != nil {
		return s.toolErr(err)
	}
	search := strings.ToLower(a.Str("search"))
	readOnly := a.Bool("readOnly")

	out := make([]map[string]any, 0)
	for _, svc := range catalog.Services() {
		if readOnly && !svc.IsReadable() {
			continue
		}
		if search != "" && !strings.Contains(strings.ToLower(svc.Service), search) {
			continue
		}
		out = append(out, map[string]any{
			"service":  svc.Service,
			"ops":      len(svc.Operations),
			"methods":  svc.Methods(),
			"readable": svc.IsReadable(),
		})
	}
	return s.jsonResult(map[string]any{
		"company":        orNotSet(company),
		"services_count": len(out),
		"services":       out,
		"note":           "the entity catalog is embedded and identical for every company; company is echoed only for consistency with the other tools",
	})
}

// handleOps lists one service's catalogued operations (offline).
func (s *Server) handleOps(_ context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_ops", req)
	if err != nil {
		return s.toolErr(err)
	}
	company, err := s.companyEcho(a)
	if err != nil {
		return s.toolErr(err)
	}
	name := a.Str("service")
	svc, ok := catalog.Find(name)
	if !ok {
		return toolErrf("%s", unknownEntityMsg(name))
	}
	ops := make([]map[string]string, 0, len(svc.Operations))
	for _, op := range svc.Operations {
		ops = append(ops, map[string]string{"method": op.Method, "name": op.Name})
	}
	return s.jsonResult(map[string]any{
		"company":          orNotSet(company),
		"service":          svc.Service,
		"readable":         svc.IsReadable(),
		"operations":       ops,
		"operations_count": len(ops),
		"note":             "the operation catalog is embedded and identical for every company; company is echoed only for consistency with the other tools",
	})
}

// handleFields mirrors `sapb1 fields`: live GET ?$top=1 keys, offline fallback
// to the entity's catalogued operations.
func (s *Server) handleFields(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_fields", req)
	if err != nil {
		return s.toolErr(err)
	}
	// companyEcho, not company: sapb1_fields promises a catalog fallback when
	// SAP is "unreachable OR not configured", and it is the tool an agent
	// reaches for before it has any connection working. Requiring a default
	// company would break that promise on a bare install. An explicitly WRONG
	// company is still a hard error — companyEcho validates anything supplied —
	// so D1/D2 is untouched; only the empty case is allowed through, and the
	// live path below re-checks ValidateCompanyDB before touching the network.
	company, err := s.companyEcho(a)
	if err != nil {
		return s.toolErr(err)
	}
	entity := a.Str("entity")
	if err := client.ValidateEntitySet(entity); err != nil {
		return s.toolErr(err)
	}
	cfg := s.cfgFor(company)

	// Live path only if we have enough config to attempt a request.
	if cfg.ValidateConnection() == nil && cfg.ValidateCompanyDB() == nil {
		res, qErr := s.clientFor(cfg).Query(ctx, entity, client.QueryOptions{Top: 1})
		if qErr == nil {
			return s.jsonResult(fieldsPayload(company, entity, res))
		}
		// Only network/unreachability failures fall back to the catalog; auth
		// and API errors are surfaced so the agent can fix them.
		var netErr *errs.NetworkError
		if !errors.As(qErr, &netErr) {
			return s.toolErr(qErr)
		}
	}

	// Offline fallback: catalogued operations.
	svc, ok := catalog.Find(entity)
	if !ok {
		return toolErrf("%s", unknownEntityMsg(entity))
	}
	ops := make([]map[string]string, 0, len(svc.Operations))
	for _, op := range svc.Operations {
		ops = append(ops, map[string]string{"method": op.Method, "name": op.Name})
	}
	return s.jsonResult(map[string]any{
		"company":    orNotSet(company),
		"entity":     entity,
		"source":     "catalog",
		"operations": ops,
	})
}

// fieldsPayload builds the live-fields JSON from the first returned record.
func fieldsPayload(company, entity string, res *client.QueryResult) map[string]any {
	asOf, src := asOfFrom(res)
	if len(res.Value) == 0 {
		return map[string]any{
			"company":      company,
			"entity":       entity,
			"source":       "live",
			"fields":       []string{},
			"as_of":        asOf,
			"as_of_source": src,
			"note":         "entity returned no rows — cannot infer fields (it may be empty)",
		}
	}
	keys := make([]string, 0, len(res.Value[0]))
	for k := range res.Value[0] {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return map[string]any{
		"company":      company,
		"entity":       entity,
		"source":       "live",
		"fields":       keys,
		"as_of":        asOf,
		"as_of_source": src,
	}
}

// handleOrders — convenience wrapper over Orders.
func (s *Server) handleOrders(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_orders", req)
	if err != nil {
		return s.toolErr(err)
	}
	extra := ""
	if a.Bool("open") {
		extra = openDocumentFilter
	}
	q, err := s.rowRequest(a, "Orders", extra, ordersDefaultSelect, "DocDate desc")
	if err != nil {
		return s.toolErr(err)
	}
	return s.runQuery(ctx, q)
}

// handleInvoices — convenience wrapper over Invoices.
func (s *Server) handleInvoices(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_invoices", req)
	if err != nil {
		return s.toolErr(err)
	}
	extra := ""
	if a.Bool("open") {
		extra = openDocumentFilter
	}
	q, err := s.rowRequest(a, "Invoices", extra, invoicesDefaultSelect, "DocDate desc")
	if err != nil {
		return s.toolErr(err)
	}
	return s.runQuery(ctx, q)
}

// handleItems — convenience wrapper over Items.
func (s *Server) handleItems(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_items", req)
	if err != nil {
		return s.toolErr(err)
	}
	// Has, not > 0. The schema advertises Min 0 and 0 is the most valuable
	// value there is — "what is out of stock?" — so treating it as "unset" and
	// returning EVERY item, formatted exactly like a correct answer, is the
	// silent-discard defect this whole surface exists to abolish.
	extra := ""
	if a.Has("lowStock") {
		extra = fmt.Sprintf("QuantityOnStock le %d", a.Int("lowStock", 0))
	}
	q, err := s.rowRequest(a, "Items", extra, itemsDefaultSelect, "ItemCode")
	if err != nil {
		return s.toolErr(err)
	}
	return s.runQuery(ctx, q)
}

// handlePartners — convenience wrapper over BusinessPartners.
func (s *Server) handlePartners(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	a, err := decodeRequest("sapb1_partners", req)
	if err != nil {
		return s.toolErr(err)
	}
	extra := ""
	switch {
	case a.Bool("customers"):
		extra = "CardType eq 'cCustomer'"
	case a.Bool("suppliers"):
		extra = "CardType eq 'cSupplier'"
	}
	q, err := s.rowRequest(a, "BusinessPartners", extra, partnersDefaultSelect, "CardCode")
	if err != nil {
		return s.toolErr(err)
	}
	return s.runQuery(ctx, q)
}

// unknownEntityMsg builds the "no such entity, did you mean?" message.
func unknownEntityMsg(name string) string {
	msg := fmt.Sprintf("no service or entity named %q in the catalog", name)
	if sugg := catalog.Suggest(name, maxSuggestions); len(sugg) > 0 {
		msg += " — did you mean: " + strings.Join(sugg, ", ") + "?"
	}
	return msg
}

// orNotSet renders empty config values as "(not set)".
func orNotSet(v string) string {
	if v == "" {
		return "(not set)"
	}
	return v
}
