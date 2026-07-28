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

// runQuery is the shared read path behind sapb1_query and the convenience
// tools: validate config, GET one page, return the rows as JSON. It only ever
// issues a GET (plus Login/Logout inside the client) — never a write.
func (s *Server) runQuery(ctx context.Context, entity, sel, filter, orderby string, top int) (*mcp.CallToolResult, error) {
	entity = strings.TrimSpace(entity)
	if entity == "" {
		return toolErrf("entity is required, e.g. \"Orders\"")
	}
	if err := s.cfg.ValidateConnection(); err != nil {
		return s.toolErr(err)
	}
	if err := s.cfg.ValidateCompanyDB(); err != nil {
		return s.toolErr(err)
	}
	if top <= 0 {
		top = defaultTop
	}

	opts := client.QueryOptions{
		Select:  sel,
		Filter:  filter,
		OrderBy: orderby,
		Top:     top,
	}
	res, err := s.newClient().Query(ctx, entity, opts)
	if err != nil {
		return s.toolErr(err)
	}
	return s.jsonResult(map[string]any{
		"entity": entity,
		"count":  len(res.Value),
		"rows":   res.Value,
	})
}

// handleDoctor mirrors `sapb1 doctor`: config → TCP reachability → Login.
func (s *Server) handleDoctor(ctx context.Context, _ mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	type check struct {
		Name   string `json:"name"`
		OK     bool   `json:"ok"`
		Detail string `json:"detail"`
		Hint   string `json:"hint,omitempty"`
	}
	report := struct {
		OK     bool           `json:"ok"`
		Config map[string]any `json:"config"`
		Checks []check        `json:"checks"`
	}{
		Config: map[string]any{
			"host":      orNotSet(s.cfg.Host),
			"port":      s.cfg.Port,
			"companyDB": orNotSet(s.cfg.CompanyDB),
			"user":      orNotSet(s.cfg.User),
			"password":  s.cfg.MaskedPassword(), // never the real secret
			"insecure":  s.cfg.Insecure,
			"timeout":   s.cfg.Timeout,
		},
	}

	// 1. Configuration.
	var missing []string
	if s.cfg.Host == "" {
		missing = append(missing, "SAPB1_HOST")
	}
	if s.cfg.User == "" {
		missing = append(missing, "SAPB1_USER")
	}
	if s.cfg.Password == "" {
		missing = append(missing, "SAPB1_PASSWORD")
	}
	if s.cfg.CompanyDB == "" {
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
	if s.cfg.Host == "" {
		netCheck.Detail = "skipped — no host configured"
	} else {
		const probe = 8 * time.Second
		timeout := probe
		if t := time.Duration(s.cfg.Timeout) * time.Second; s.cfg.Timeout > 0 && t < timeout {
			timeout = t
		}
		if err := client.CheckTCPReachable(s.cfg.HostPort(), timeout); err != nil {
			netCheck.Detail = fmt.Sprintf("cannot reach %s over TCP", s.cfg.HostPort())
			netCheck.Hint = "are you on the company VPN, or is your IP whitelisted on the SAP firewall?"
		} else {
			reachable = true
			netCheck.OK = true
			netCheck.Detail = fmt.Sprintf("%s is reachable over TCP", s.cfg.HostPort())
		}
	}
	report.Checks = append(report.Checks, netCheck)

	// 3. Login.
	loginCheck := check{Name: "login"}
	switch {
	case !configOK:
		loginCheck.Detail = "skipped — fix configuration first"
	case !reachable:
		loginCheck.Detail = "skipped — host is not reachable"
	default:
		if err := s.newClient().Login(ctx); err != nil {
			loginCheck.Detail = s.safeErr(err)
			loginCheck.Hint = "check credentials and CompanyDB"
		} else {
			loginCheck.OK = true
			loginCheck.Detail = fmt.Sprintf("connected to %s as %s", s.cfg.CompanyDB, s.cfg.User)
		}
	}
	report.Checks = append(report.Checks, loginCheck)

	report.OK = configOK && reachable && loginCheck.OK
	return s.jsonResult(report)
}

// handleQuery is the core generic read tool.
func (s *Server) handleQuery(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	entity, err := req.RequireString("entity")
	if err != nil {
		return toolErrf("entity is required, e.g. \"Orders\"")
	}
	return s.runQuery(ctx,
		entity,
		req.GetString("select", ""),
		req.GetString("filter", ""),
		req.GetString("orderby", ""),
		req.GetInt("top", defaultTop),
	)
}

// handleEntities lists catalog services (offline).
func (s *Server) handleEntities(_ context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	search := strings.ToLower(strings.TrimSpace(req.GetString("search", "")))
	readOnly := req.GetBool("readOnly", false)

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
		"count":    len(out),
		"services": out,
	})
}

// handleOps lists one service's catalogued operations (offline).
func (s *Server) handleOps(_ context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	name, err := req.RequireString("service")
	if err != nil {
		return toolErrf("service is required, e.g. \"Orders\"")
	}
	name = strings.TrimSpace(name)
	svc, ok := catalog.Find(name)
	if !ok {
		return toolErrf("%s", unknownEntityMsg(name))
	}
	ops := make([]map[string]string, 0, len(svc.Operations))
	for _, op := range svc.Operations {
		ops = append(ops, map[string]string{"method": op.Method, "name": op.Name})
	}
	return s.jsonResult(map[string]any{
		"service":    svc.Service,
		"readable":   svc.IsReadable(),
		"operations": ops,
	})
}

// handleFields mirrors `sapb1 fields`: live GET ?$top=1 keys, offline fallback
// to the entity's catalogued operations.
func (s *Server) handleFields(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	entity, err := req.RequireString("entity")
	if err != nil {
		return toolErrf("entity is required, e.g. \"Orders\"")
	}
	entity = strings.TrimSpace(entity)
	if entity == "" {
		return toolErrf("entity is required, e.g. \"Orders\"")
	}

	// Live path only if we have enough config to attempt a request.
	if s.cfg.ValidateConnection() == nil && s.cfg.ValidateCompanyDB() == nil {
		res, qErr := s.newClient().Query(ctx, entity, client.QueryOptions{Top: 1})
		if qErr == nil {
			return s.jsonResult(fieldsPayload(entity, res))
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
		"entity":     entity,
		"source":     "catalog",
		"operations": ops,
	})
}

// fieldsPayload builds the live-fields JSON from the first returned record.
func fieldsPayload(entity string, res *client.QueryResult) map[string]any {
	if len(res.Value) == 0 {
		return map[string]any{
			"entity": entity,
			"source": "live",
			"fields": []string{},
			"note":   "entity returned no rows — cannot infer fields (it may be empty)",
		}
	}
	keys := make([]string, 0, len(res.Value[0]))
	for k := range res.Value[0] {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return map[string]any{
		"entity": entity,
		"source": "live",
		"fields": keys,
	}
}

// handleOrders — convenience wrapper over Orders.
func (s *Server) handleOrders(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	extra := ""
	if req.GetBool("open", false) {
		extra = "DocStatus eq 'O'"
	}
	filter := combineFilters(extra, req.GetString("filter", ""))
	return s.runQuery(ctx, "Orders", ordersDefaultSelect, filter, "DocDate desc", req.GetInt("top", defaultTop))
}

// handleInvoices — convenience wrapper over Invoices.
func (s *Server) handleInvoices(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	extra := ""
	if req.GetBool("open", false) {
		extra = "DocStatus eq 'O'"
	}
	filter := combineFilters(extra, req.GetString("filter", ""))
	return s.runQuery(ctx, "Invoices", invoicesDefaultSelect, filter, "DocDate desc", req.GetInt("top", defaultTop))
}

// handleItems — convenience wrapper over Items.
func (s *Server) handleItems(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	extra := ""
	if low := req.GetInt("lowStock", 0); low > 0 {
		extra = fmt.Sprintf("QuantityOnStock le %d", low)
	}
	filter := combineFilters(extra, req.GetString("filter", ""))
	return s.runQuery(ctx, "Items", itemsDefaultSelect, filter, "ItemCode", req.GetInt("top", defaultTop))
}

// handlePartners — convenience wrapper over BusinessPartners.
func (s *Server) handlePartners(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	customers := req.GetBool("customers", false)
	suppliers := req.GetBool("suppliers", false)
	if customers && suppliers {
		return toolErrf("customers and suppliers are mutually exclusive")
	}
	extra := ""
	switch {
	case customers:
		extra = "CardType eq 'cCustomer'"
	case suppliers:
		extra = "CardType eq 'cSupplier'"
	}
	filter := combineFilters(extra, req.GetString("filter", ""))
	return s.runQuery(ctx, "BusinessPartners", partnersDefaultSelect, filter, "CardCode", req.GetInt("top", defaultTop))
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
