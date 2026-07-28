// Package mcp exposes the read-only sapb1 client as a Model Context Protocol
// (MCP) server over stdio, so an AI agent (Claude Code / Claude Desktop) can
// query the SAP Business One Service Layer as a set of tools.
//
// READ-ONLY GUARANTEE: every tool in this package resolves to one of only
// four HTTP operations against the Service Layer — GET (entity reads),
// POST /Login, and POST /Logout (session establishment/teardown only). There
// is deliberately NO tool, and no code path, that issues POST/PUT/PATCH/DELETE
// against any business entity set (Orders, Invoices, Items, BusinessPartners,
// ...). The whole surface reuses internal/client, which itself only ever sends
// GET + Login/Logout. Do not add a tool here that mutates business data.
//
// The password is never returned in a tool result, logged, or embedded in any
// error message: every error surfaced to the agent is scrubbed via
// (*Server).safeErr, and config summaries use Config.MaskedPassword.
package mcp

import (
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"

	"sapb1/internal/client"
	"sapb1/internal/config"
)

// serverVersion is advertised to MCP clients during initialize.
const serverVersion = "1.0.0"

// defaultTop bounds how many rows a query/convenience tool returns when the
// agent doesn't specify one, keeping responses agent-friendly by default.
const defaultTop = 20

// Default $select field sets for the convenience tools. These mirror the
// defaults used by the equivalent CLI commands (orders/invoices/items/
// partners `list`) so the MCP surface returns the same shape as the CLI.
const (
	ordersDefaultSelect   = "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,DocStatus,DocCurrency"
	invoicesDefaultSelect = "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,DocStatus,DocCurrency"
	itemsDefaultSelect    = "ItemCode,ItemName,ItemsGroupCode,QuantityOnStock,Valid"
	partnersDefaultSelect = "CardCode,CardName,CardType,Phone1,EmailAddress,CurrentAccountBalance"
)

// Server wraps an mcp-go MCPServer preloaded with the read-only sapb1 tools.
// It holds the resolved config; each tool call builds a fresh client (which
// transparently reuses the on-disk session cache), mirroring how each CLI
// command runs — this keeps the client's mutable session state free of
// cross-request contention.
type Server struct {
	cfg *config.Config
	mcp *server.MCPServer
}

// NewServer builds a Server with every read-only tool registered.
func NewServer(cfg *config.Config) *Server {
	s := &Server{cfg: cfg}
	s.mcp = server.NewMCPServer(
		"sapb1",
		serverVersion,
		server.WithToolCapabilities(false),
		server.WithRecovery(),
		server.WithInstructions(
			"Read-only access to the SAP Business One Service Layer (b1s/v1). "+
				"All tools are GET-only; nothing here creates, updates, or deletes "+
				"business data. Start with sapb1_doctor to confirm connectivity, use "+
				"sapb1_entities/sapb1_ops/sapb1_fields to discover what you can read "+
				"(the catalog tools work offline), then sapb1_query (or the "+
				"sapb1_orders/invoices/items/partners convenience tools) to fetch rows.",
		),
	)
	s.registerTools()
	return s
}

// Serve runs the MCP server over stdio (stdin/stdout JSON-RPC), blocking until
// the stream closes or a shutdown signal arrives.
func (s *Server) Serve() error {
	return server.ServeStdio(s.mcp)
}

// MCPServer exposes the underlying mcp-go server, used by tests to drive
// JSON-RPC messages directly and to enumerate registered tools.
func (s *Server) MCPServer() *server.MCPServer {
	return s.mcp
}

// newClient builds a fresh client for a single tool call. Each call reuses the
// on-disk session cache, so this does not re-login on every request.
func (s *Server) newClient() *client.Client {
	return client.New(s.cfg)
}

// registerTools wires every read-only tool onto the MCP server. Each tool is
// marked with the read-only annotation hint; the network-backed tools are also
// marked open-world (they reach an external system) while the catalog tools
// (entities/ops) are closed-world and work fully offline.
func (s *Server) registerTools() {
	// sapb1_doctor — connectivity self-check.
	s.mcp.AddTool(mcp.NewTool("sapb1_doctor",
		mcp.WithDescription(
			"Diagnose the SAP B1 connection end-to-end: is config present, is the "+
				"host reachable over TCP, and does Login succeed. Takes no arguments. "+
				"Returns a JSON status report (password is masked). Call this first "+
				"when a query fails, to tell apart a missing-config, off-VPN, or "+
				"bad-credentials problem."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(true),
		mcp.WithTitleAnnotation("SAP B1 connection doctor"),
	), s.handleDoctor)

	// sapb1_query — the core generic read.
	s.mcp.AddTool(mcp.NewTool("sapb1_query",
		mcp.WithDescription(
			"Run a read-only OData GET against ANY SAP B1 Service Layer entity set "+
				"and return the matching rows as JSON. This is the core tool. Use "+
				"sapb1_entities to discover entity-set names and sapb1_fields to "+
				"discover selectable field names."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(true),
		mcp.WithTitleAnnotation("Query a SAP B1 entity set"),
		mcp.WithString("entity", mcp.Required(),
			mcp.Description("OData entity set to read, e.g. \"Orders\", \"Invoices\", \"Items\", \"BusinessPartners\", \"PurchaseOrders\".")),
		mcp.WithString("select",
			mcp.Description("Comma-separated fields to return ($select), e.g. \"DocEntry,DocNum,CardName,DocTotal\". Omit to return all fields.")),
		mcp.WithString("filter",
			mcp.Description("Raw OData $filter expression, e.g. \"DocStatus eq 'O'\" or \"DocTotal gt 10000\".")),
		mcp.WithNumber("top",
			mcp.Description("Max rows to return ($top). Default 20.")),
		mcp.WithString("orderby",
			mcp.Description("Raw OData $orderby expression, e.g. \"DocDate desc\".")),
	), s.handleQuery)

	// sapb1_entities — offline discovery of entity sets.
	s.mcp.AddTool(mcp.NewTool("sapb1_entities",
		mcp.WithDescription(
			"List Service Layer services/entities from the embedded catalog. Works "+
				"OFFLINE (no network/login needed). Use it to discover what you can "+
				"query. Each entry has the service name, operation count, HTTP methods "+
				"present, and whether it is readable (has a GET)."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(false),
		mcp.WithTitleAnnotation("List SAP B1 entities (offline)"),
		mcp.WithString("search",
			mcp.Description("Case-insensitive substring filter on the service/entity name, e.g. \"invoice\".")),
		mcp.WithBoolean("readOnly",
			mcp.Description("If true, only list services that are readable (expose a GET).")),
	), s.handleEntities)

	// sapb1_ops — offline discovery of one service's operations.
	s.mcp.AddTool(mcp.NewTool("sapb1_ops",
		mcp.WithDescription(
			"Show every catalogued operation (HTTP method + name) for ONE service or "+
				"entity, from the embedded catalog. Works OFFLINE. Write operations are "+
				"listed for reference only; sapb1 never executes them."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(false),
		mcp.WithTitleAnnotation("List operations for a SAP B1 service (offline)"),
		mcp.WithString("service", mcp.Required(),
			mcp.Description("Service or entity name, e.g. \"Orders\", \"OrdersService\", \"BusinessPartners\".")),
	), s.handleOps)

	// sapb1_fields — live field discovery with offline fallback.
	s.mcp.AddTool(mcp.NewTool("sapb1_fields",
		mcp.WithDescription(
			"Discover the real field names of an entity so you know what to pass to "+
				"sapb1_query's select. Live, it does GET <entity>?$top=1 and returns the "+
				"sorted JSON keys of the first record. If SAP is unreachable or not "+
				"configured, it falls back to the entity's catalogued operations."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(true),
		mcp.WithTitleAnnotation("Discover a SAP B1 entity's fields"),
		mcp.WithString("entity", mcp.Required(),
			mcp.Description("Entity set to inspect, e.g. \"Orders\", \"BusinessPartners\".")),
	), s.handleFields)

	// Convenience read tools — thin wrappers over sapb1_query.
	s.mcp.AddTool(mcp.NewTool("sapb1_orders",
		mcp.WithDescription(
			"List sales orders (Orders) with a sensible default field set, newest "+
				"first. Optional filter/top, plus open=true to restrict to open orders "+
				"(DocStatus eq 'O'). Read-only."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(true),
		mcp.WithTitleAnnotation("List SAP B1 sales orders"),
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter.")),
		mcp.WithNumber("top", mcp.Description("Max rows to return. Default 20.")),
		mcp.WithBoolean("open", mcp.Description("If true, only open orders (DocStatus eq 'O').")),
	), s.handleOrders)

	s.mcp.AddTool(mcp.NewTool("sapb1_invoices",
		mcp.WithDescription(
			"List A/R invoices (Invoices) with a sensible default field set, newest "+
				"first. Optional filter/top, plus open=true to restrict to open invoices "+
				"(DocStatus eq 'O'). Read-only."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(true),
		mcp.WithTitleAnnotation("List SAP B1 A/R invoices"),
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter.")),
		mcp.WithNumber("top", mcp.Description("Max rows to return. Default 20.")),
		mcp.WithBoolean("open", mcp.Description("If true, only open invoices (DocStatus eq 'O').")),
	), s.handleInvoices)

	s.mcp.AddTool(mcp.NewTool("sapb1_items",
		mcp.WithDescription(
			"List items/products (Items) with a sensible default field set. Optional "+
				"filter/top, plus lowStock=N to restrict to items with QuantityOnStock "+
				"<= N. Read-only."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(true),
		mcp.WithTitleAnnotation("List SAP B1 items"),
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter.")),
		mcp.WithNumber("top", mcp.Description("Max rows to return. Default 20.")),
		mcp.WithNumber("lowStock", mcp.Description("If > 0, only items with QuantityOnStock <= this value.")),
	), s.handleItems)

	s.mcp.AddTool(mcp.NewTool("sapb1_partners",
		mcp.WithDescription(
			"List business partners (BusinessPartners) — customers and suppliers — "+
				"with a sensible default field set. Optional filter/top, plus "+
				"customers=true or suppliers=true to restrict by CardType. Read-only."),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(true),
		mcp.WithTitleAnnotation("List SAP B1 business partners"),
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter.")),
		mcp.WithNumber("top", mcp.Description("Max rows to return. Default 20.")),
		mcp.WithBoolean("customers", mcp.Description("If true, only customers (CardType eq 'cCustomer').")),
		mcp.WithBoolean("suppliers", mcp.Description("If true, only suppliers (CardType eq 'cSupplier').")),
	), s.handlePartners)
}
