// Package mcp exposes the read-only sapb1 client as a Model Context Protocol
// (MCP) server over stdio, so an AI agent (Claude Code / Claude Desktop) can
// query the SAP Business One Service Layer as a set of tools.
//
// The same server can also be served over streamable HTTP (see
// ServeStreamableHTTP). HTTP is strictly a second transport over the IDENTICAL
// GET-only tool surface — it adds no new capability, no extra tools, and no
// write path of any kind.
//
// READ-ONLY GUARANTEE: every tool in this package resolves to one of only
// four HTTP operations against the Service Layer — GET (entity reads),
// POST /Login, and POST /Logout (session establishment/teardown only). There
// is deliberately NO tool, and no code path, that issues POST/PUT/PATCH/DELETE
// against any business entity set (Orders, Invoices, Items, BusinessPartners,
// ...). The whole surface reuses internal/client, which itself only ever sends
// GET + Login/Logout. Do not add a tool here that mutates business data.
// Choosing a company changes only the CompanyDB in the Login payload; it adds
// no new kind of request.
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
const serverVersion = "1.1.0"

// defaultTop bounds how many rows a query/convenience tool returns when the
// agent doesn't specify one, keeping responses agent-friendly by default.
const defaultTop = 20

// openDocumentFilter is how the Service Layer expresses "open document". Note
// the property is DocumentStatus, NOT the HANA column name DocStatus: a
// $filter or $select on DocStatus is rejected outright with
// "Property 'DocStatus' of 'Document' is invalid".
const openDocumentFilter = "DocumentStatus eq 'bost_Open'"

// Default $select field sets for the convenience tools. These mirror the
// defaults used by the equivalent CLI commands (orders/invoices/items/
// partners `list`) so the MCP surface returns the same shape as the CLI.
const (
	ordersDefaultSelect   = "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,DocumentStatus,DocCurrency"
	invoicesDefaultSelect = "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,DocumentStatus,DocCurrency"
	itemsDefaultSelect    = "ItemCode,ItemName,ItemsGroupCode,QuantityOnStock,Valid"
	partnersDefaultSelect = "CardCode,CardName,CardType,Phone1,EmailAddress,CurrentAccountBalance"
)

// fieldNameFacts is the field-naming cheat sheet the agent needs BEFORE its
// first query. Every line here was paid for once already, in failed calls
// against live SAP: the Service Layer's property names are not the HANA column
// names, and guessing costs a round trip each time.
const fieldNameFacts = "SERVICE LAYER FIELD NAMES (they differ from the HANA column names): " +
	"DocumentStatus (values 'bost_Open'/'bost_Close'), NOT DocStatus. " +
	"Cancelled eq 'tNO' excludes cancelled documents — spelled with two l's on EVERY entity, " +
	"including IncomingPayments/VendorPayments (their HANA columns say Canceled, the Service Layer does not). " +
	"JournalEntries are dated by ReferenceDate; they have no DocDate. " +
	"CurrentAccountBalance is the ledger balance, NOT Balance — POSITIVE = DEBIT (the party owes JIVO), " +
	"NEGATIVE = CREDIT (JIVO owes them). CreditLimit, NOT CreditLine (0 means no limit set). " +
	"QuantityOnStock, NOT OnHand. MinInventory, NOT MinLevel. InventoryItem eq 'tYES' is what makes an item stock-managed. " +
	"Payment entities (IncomingPayments/VendorPayments) have NO DocTotal — the amount is " +
	"CashSum + TransferSum + BillOfExchangeAmount plus the line sums inside PaymentChecks and PaymentCreditCards. " +
	"$filter has NO toupper()/tolower(), so a name search cannot case-fold — match case-exactly or pull the rows and match yourself. " +
	"Field-to-field comparison in $filter DOES work server-side (e.g. \"CurrentAccountBalance gt CreditLimit\", " +
	"\"QuantityOnStock lt MinInventory\"), and server-side $orderby IS reliable for a global top-N — " +
	"neither needs to be done by hauling rows into your context. " +
	"Turnover/sales = (Invoices DocTotal - VatSum) minus (CreditNotes DocTotal - VatSum), by DocDate, with Cancelled eq 'tNO'."

// pagingFacts explains the shared response shape once, so every tool
// description can stay short.
const pagingFacts = "RESULT SHAPE (identical for every row-returning tool): " +
	"{company, entity, rows_in_page, total_count (only when the server gave one), truncated (always), " +
	"next_skip (only when truncated), as_of, as_of_source, rows}. " +
	"rows_in_page is how many rows are in THIS response — it is NOT a total. " +
	"To COUNT, pass count=true: one request, server-side $inlinecount, the total in total_count, rows empty. " +
	"That is atomic; a paged tally is not. To sweep a whole set, pass all=true (follows odata.nextLink). " +
	"When truncated is true there are more rows: call again with skip=next_skip and the SAME filter/orderby. " +
	"Pagination is offset-based and the tables are live, so order by a stable key (e.g. DocEntry) when paginating, " +
	"and compare as_of stamps if two calls disagree."

// companyFacts is appended to every tool description.
const companyFacts = "COMPANY: JIVO keeps three separate SAP company databases — " +
	"JIVO_OIL_HANADB (Oil), JIVO_MART_HANADB (Mart), JIVO_BEVERAGES_HANADB (Beverages). " +
	"Pass company to choose one; omit it to use the server's configured default. " +
	"Figures from one company are NOT comparable to another's, so always state which company an answer came from — " +
	"every response echoes it back in the company field."

// Server wraps an mcp-go MCPServer preloaded with the read-only sapb1 tools.
//
// It holds the resolved config and one client.SessionStore. Each tool call
// still builds a fresh client — client.Client mutates its own session fields
// and HTTP tool calls run concurrently — but they all share SESSIONS through
// the store, so a burst of parallel calls costs one Login per company rather
// than one per call.
type Server struct {
	cfg      *config.Config
	mcp      *server.MCPServer
	sessions *client.SessionStore
}

// NewServer builds a Server with every read-only tool registered.
func NewServer(cfg *config.Config) *Server {
	s := &Server{cfg: cfg, sessions: client.NewSessionStore()}
	s.mcp = server.NewMCPServer(
		"sapb1",
		serverVersion,
		server.WithToolCapabilities(false),
		server.WithRecovery(),
		// Advertise additionalProperties:false on every tool, so a
		// schema-aware client is steered away from invented parameters before
		// it sends one. The authoritative rejection still happens in our own
		// decoder (internal/mcp/args.go), which names the offending key AND
		// lists the valid ones.
		server.WithStrictInputSchemaDefault(),
		server.WithInstructions(
			"Read-only access to the SAP Business One Service Layer (b1s/v1). "+
				"All tools are GET-only; nothing here creates, updates, or deletes "+
				"business data. Start with sapb1_doctor to confirm connectivity, use "+
				"sapb1_entities/sapb1_ops/sapb1_fields to discover what you can read "+
				"(the catalog tools work offline), then sapb1_query (or the "+
				"sapb1_orders/invoices/items/partners convenience tools) to fetch rows. "+
				"Unknown parameters are REJECTED, never ignored: if a call returns "+
				"\"unknown parameter\", read the valid list in the error and retry. "+
				"Money is INR. "+
				companyFacts+" "+pagingFacts+" "+fieldNameFacts),
	)
	s.registerTools()
	return s
}

// Serve runs the MCP server over stdio (stdin/stdout JSON-RPC), blocking until
// the stream closes or a shutdown signal arrives.
func (s *Server) Serve() error {
	return server.ServeStdio(s.mcp)
}

// ServeStreamableHTTP runs the MCP server over streamable HTTP, bound to addr
// (host:port or :port), blocking until the listener fails. The endpoint path
// is mcp-go's default, /mcp. It serves the exact same read-only tool set as
// the stdio transport.
//
// The server runs stateless in the MCP sense (no Mcp-Session-Id required):
// nothing about a caller is remembered between calls. Note that unlike stdio
// (one serial client), HTTP allows CONCURRENT tool calls, which is why SAP
// sessions are shared through the Server's client.SessionStore — its
// per-identity lock makes N parallel calls cost one Login instead of N, so a
// batch of tool calls cannot burn through the licensed Service Layer session
// slots. The on-disk cache write in internal/client is not temp+rename atomic,
// but a corrupt/partial cache file is treated as "no session", and the store
// then serialises the single re-Login that follows.
func (s *Server) ServeStreamableHTTP(addr string) error {
	return s.newStreamableServer().Start(addr)
}

// newStreamableServer wraps the MCP server in mcp-go's streamable HTTP
// transport (stateless mode). Unexported so tests can mount it on an
// httptest.Server.
func (s *Server) newStreamableServer() *server.StreamableHTTPServer {
	return server.NewStreamableHTTPServer(s.mcp, server.WithStateLess(true))
}

// MCPServer exposes the underlying mcp-go server, used by tests to drive
// JSON-RPC messages directly and to enumerate registered tools.
func (s *Server) MCPServer() *server.MCPServer {
	return s.mcp
}

// companyOption is the `company` parameter every tool carries.
func companyOption() mcp.ToolOption {
	return mcp.WithString("company",
		mcp.Enum(companyEnum...),
		mcp.Description("Which SAP company database to read: JIVO_OIL_HANADB (Oil), JIVO_MART_HANADB (Mart), or JIVO_BEVERAGES_HANADB (Beverages). Omit to use the server's configured default. An unrecognised value is an error — it never silently falls back."))
}

// pagingOptions are the shared paging/counting parameters of every
// row-returning tool. Keeping them in one place is what makes the five tools
// behave identically.
func pagingOptions() []mcp.ToolOption {
	return []mcp.ToolOption{
		mcp.WithNumber("top",
			mcp.Min(1), mcp.Max(maxTop),
			mcp.Description("Max rows to return. Default 20, max 5000. Values larger than the Service Layer's page size are honoured — the server follows odata.nextLink for you. Mutually exclusive with all and count.")),
		mcp.WithNumber("skip",
			mcp.Min(0),
			mcp.Description("Rows to skip ($skip) — pass the next_skip from a truncated response, with the SAME filter/orderby, to continue where you left off.")),
		mcp.WithNumber("page_size",
			mcp.Min(1), mcp.Max(maxPageSize),
			mcp.Description("Rows per underlying request while paginating (Prefer: odata.maxpagesize), 1-500. Only affects how many round trips a sweep costs, never the result.")),
		mcp.WithBoolean("all",
			mcp.Description("Return EVERY matching row by following odata.nextLink, up to 5000. Beyond that, truncated=true and next_skip tells you where to resume. Mutually exclusive with top and count.")),
		mcp.WithBoolean("count",
			mcp.Description("Return ONLY the server-side total ($inlinecount=allpages) in total_count, with rows empty. One request, so the number is atomic. Use this for \"how many …\" questions instead of paging. Mutually exclusive with top, skip, page_size and all.")),
	}
}

// tool assembles a tool from a name, description and options, always adding
// the read-only annotations and the company parameter.
func tool(name, title, description string, openWorld bool, opts ...mcp.ToolOption) mcp.Tool {
	base := []mcp.ToolOption{
		mcp.WithDescription(description),
		mcp.WithReadOnlyHintAnnotation(true),
		mcp.WithDestructiveHintAnnotation(false),
		mcp.WithOpenWorldHintAnnotation(openWorld),
		mcp.WithTitleAnnotation(title),
		companyOption(),
	}
	return mcp.NewTool(name, append(base, opts...)...)
}

// rowTool assembles a row-returning tool: company + its own options + the
// shared paging set.
func rowTool(name, title, description string, opts ...mcp.ToolOption) mcp.Tool {
	return tool(name, title, description, true, append(opts, pagingOptions()...)...)
}

// registerTools wires every read-only tool onto the MCP server. Each tool is
// marked with the read-only annotation hint; the network-backed tools are also
// marked open-world (they reach an external system) while the catalog tools
// (entities/ops) are closed-world and work fully offline.
func (s *Server) registerTools() {
	// sapb1_doctor — connectivity self-check.
	s.mcp.AddTool(tool("sapb1_doctor", "SAP B1 connection doctor",
		"Diagnose the SAP B1 connection end-to-end: is config present, is the "+
			"host reachable over TCP, and does Login succeed. Pass company to test "+
			"THAT company database specifically (the login is performed against it), "+
			"which is how you prove Mart or Beverages is reachable and not just the "+
			"default. Returns a JSON status report (password is masked). Call this "+
			"first when a query fails, to tell apart a missing-config, off-VPN, or "+
			"bad-credentials problem.",
		true,
	), s.handleDoctor)

	// sapb1_query — the core generic read.
	s.mcp.AddTool(rowTool("sapb1_query", "Query a SAP B1 entity set",
		"Run a read-only OData GET against ANY SAP B1 Service Layer entity set "+
			"and return the matching rows as JSON. This is the core tool. Use "+
			"sapb1_entities to discover entity-set names and sapb1_fields to "+
			"discover selectable field names. "+
			"Key entity sets: Invoices (A/R), CreditNotes (sales returns), Orders, "+
			"PurchaseInvoices, PurchaseOrders, IncomingPayments, VendorPayments, "+
			"BusinessPartners, Items, JournalEntries. "+
			pagingFacts+" "+fieldNameFacts+" "+companyFacts,
		mcp.WithString("entity", mcp.Required(),
			mcp.Description("OData entity set to read, e.g. \"Orders\", \"Invoices\", \"Items\", \"BusinessPartners\", \"PurchaseOrders\".")),
		mcp.WithString("select",
			mcp.Description("Comma-separated fields to return ($select), e.g. \"DocEntry,DocNum,CardName,DocTotal\". Omit to return all fields.")),
		mcp.WithString("filter",
			mcp.Description("Raw OData $filter, e.g. \"DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO'\", \"DocDate ge '2026-04-01' and DocDate lt '2026-07-25'\", or a field-to-field comparison like \"QuantityOnStock lt MinInventory\". Do NOT append $skip/$top here — use the skip/top parameters.")),
		mcp.WithString("orderby",
			mcp.Description("Raw OData $orderby, e.g. \"DocDate desc\" or \"CurrentAccountBalance desc\". Server-side ordering is reliable, so a global top-N needs no client-side sorting.")),
	), s.handleQuery)

	// sapb1_entities — offline discovery of entity sets.
	s.mcp.AddTool(tool("sapb1_entities", "List SAP B1 entities (offline)",
		"List Service Layer services/entities from the embedded catalog. Works "+
			"OFFLINE (no network/login needed). Use it to discover what you can "+
			"query. Each entry has the service name, operation count, HTTP methods "+
			"present, and whether it is readable (has a GET). The catalog is "+
			"company-independent — company is accepted and echoed back for "+
			"consistency with the other tools, but does not change the result.",
		false,
		mcp.WithString("search",
			mcp.Description("Case-insensitive substring filter on the service/entity name, e.g. \"invoice\".")),
		mcp.WithBoolean("readOnly",
			mcp.Description("If true, only list services that are readable (expose a GET).")),
	), s.handleEntities)

	// sapb1_ops — offline discovery of one service's operations.
	s.mcp.AddTool(tool("sapb1_ops", "List operations for a SAP B1 service (offline)",
		"Show every catalogued operation (HTTP method + name) for ONE service or "+
			"entity, from the embedded catalog. Works OFFLINE. Write operations are "+
			"listed for reference only; sapb1 never executes them. The catalog is "+
			"company-independent — company is accepted and echoed back for "+
			"consistency with the other tools, but does not change the result.",
		false,
		mcp.WithString("service", mcp.Required(),
			mcp.Description("Service or entity name, e.g. \"Orders\", \"OrdersService\", \"BusinessPartners\".")),
	), s.handleOps)

	// sapb1_fields — live field discovery with offline fallback.
	s.mcp.AddTool(tool("sapb1_fields", "Discover a SAP B1 entity's fields",
		"Discover the real field names of an entity so you know what to pass to "+
			"sapb1_query's select and filter. Live, it does GET <entity>?$top=1 and "+
			"returns the sorted JSON keys of the first record. If SAP is unreachable "+
			"or not configured, it falls back to the entity's catalogued operations. "+
			"Use this before guessing a field name — Service Layer property names "+
			"differ from HANA column names. "+companyFacts,
		true,
		mcp.WithString("entity", mcp.Required(),
			mcp.Description("Entity set to inspect, e.g. \"Orders\", \"BusinessPartners\", \"IncomingPayments\".")),
	), s.handleFields)

	// Convenience read tools — thin wrappers over sapb1_query.
	s.mcp.AddTool(rowTool("sapb1_orders", "List SAP B1 sales orders",
		"List sales orders (Orders) with a sensible default field set, newest "+
			"first. open=true restricts to open orders (DocumentStatus eq "+
			"'bost_Open'). Read-only. "+pagingFacts+" "+companyFacts,
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter. Add \"Cancelled eq 'tNO'\" to exclude cancelled orders.")),
		mcp.WithBoolean("open", mcp.Description("If true, only open orders (DocumentStatus eq 'bost_Open').")),
	), s.handleOrders)

	s.mcp.AddTool(rowTool("sapb1_invoices", "List SAP B1 A/R invoices",
		"List A/R invoices (Invoices) with a sensible default field set, newest "+
			"first. open=true restricts to open invoices (DocumentStatus eq "+
			"'bost_Open'). Read-only. Note DocTotal is GST-INCLUSIVE; net of GST is "+
			"DocTotal - VatSum, and turnover subtracts CreditNotes on the same basis. "+
			pagingFacts+" "+companyFacts,
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter. Add \"Cancelled eq 'tNO'\" to exclude cancelled invoices.")),
		mcp.WithBoolean("open", mcp.Description("If true, only open invoices (DocumentStatus eq 'bost_Open').")),
	), s.handleInvoices)

	s.mcp.AddTool(rowTool("sapb1_items", "List SAP B1 items",
		"List items/products (Items) with a sensible default field set. "+
			"lowStock=N restricts to items with QuantityOnStock <= N, and "+
			"lowStock=0 is the out-of-stock list (it is honoured, not treated as "+
			"unset). For items "+
			"below their OWN minimum, filter \"MinInventory gt 0 and QuantityOnStock "+
			"lt MinInventory and InventoryItem eq 'tYES'\" — field-to-field "+
			"comparison works server-side. Read-only. "+pagingFacts+" "+companyFacts,
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter. \"InventoryItem eq 'tYES'\" restricts to stock-managed items.")),
		mcp.WithNumber("lowStock", mcp.Min(0), mcp.Description("Only items with QuantityOnStock <= this value. 0 is honoured and means \"out of stock\"; omit the parameter entirely for no stock filter.")),
	), s.handleItems)

	s.mcp.AddTool(rowTool("sapb1_partners", "List SAP B1 business partners",
		"List business partners (BusinessPartners) — customers and suppliers — "+
			"with a sensible default field set. customers=true or suppliers=true "+
			"restricts by CardType. CurrentAccountBalance is the ledger balance: "+
			"POSITIVE = DEBIT (they owe JIVO), NEGATIVE = CREDIT (JIVO owes them). "+
			"One party may hold several accounts (e.g. an employee IMPREST vendor "+
			"card plus a customer card) — check them all. Read-only. "+
			pagingFacts+" "+companyFacts,
		mcp.WithString("filter", mcp.Description("Additional raw OData $filter, ANDed with any built-in filter. $filter has no toupper()/tolower(), so name matching is case-exact.")),
		mcp.WithBoolean("customers", mcp.Description("If true, only customers (CardType eq 'cCustomer').")),
		mcp.WithBoolean("suppliers", mcp.Description("If true, only suppliers (CardType eq 'cSupplier').")),
	), s.handlePartners)
}
