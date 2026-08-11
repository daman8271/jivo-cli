package mcp

import (
	"strings"
)

// The dsr MCP tool table.
//
// This is a HAND-AUTHORED ALLOWLIST, and that is the security design, not a
// stylistic choice. The reference implementation
// (exim-pp-cli/internal/mcp/cobratree) walks the Cobra tree and registers one
// tool per runnable leaf. On dsr that would be 84 tools — unusable for an
// agent, and worse, a standing policy that ANY subcommand added later appears
// on a publicly routed gateway with no review. Here the 15 tools below are
// spelled out, each action pinned to a literal argv into the dsr command tree,
// and an action name that is not in the table is an error rather than a
// passthrough.
//
// What that mechanically excludes:
//
//   - `dsr schema dump` — the ONE dsr command with side effects of any kind
//     (os.MkdirAll + os.WriteFile of ~131 sample files and a catalog under
//     --out, and minutes of runtime). It is in no action enum, so it is
//     unreachable. It also has no agent value: everything it writes to disk is
//     available live through the dsr_schema actions.
//   - every root flag a caller must not set (--db above all — the instance
//     hosts 72 databases, only one of which is DSR). See cobratree.BlockedFlags.
//
// dsr has no create/update/delete subcommands at all, and no ExecContext or
// POST call path exists anywhere in its source, so there is no write command to
// exclude — but "there is nothing to exclude today" is not a guarantee, which
// is why the allowlist, the AST guard (readonly_guard_test.go) and the tool-set
// pin (tools_test.go) all exist.

// Shared parameter definitions. Declared once so the same concept has the same
// name, type and description on every tool that offers it — an agent that
// learns `salesperson` on dsr_attendance can use it on dsr_sales unchanged.
var (
	pFrom = param{Name: "from", Flag: "from", Kind: kindString,
		Desc: "Start date, INCLUSIVE, as YYYY-MM-DD (e.g. 2026-07-01)."}
	pTo = param{Name: "to", Flag: "to", Kind: kindString,
		Desc: "End date, EXCLUSIVE, as YYYY-MM-DD (e.g. 2026-08-01) — a full July is from=2026-07-01 to=2026-08-01."}
	pSalesperson = param{Name: "salesperson", Flag: "salesperson", Kind: kindInt, Min: 1,
		Desc: "Filter to one salesperson, by tbl_salesperson.ID (see dsr_salespersons action=list)."}
	pRetailer = param{Name: "retailer", Flag: "retailer", Kind: kindInt, Min: 1,
		Desc: "Filter to one retailer/outlet, by tbl_retailers.Id (see dsr_retailers action=list)."}
	pItem = param{Name: "item", Flag: "item", Kind: kindInt, Min: 1,
		Desc: "Filter to one SKU, by tbl_item.Id (see dsr_products action=list)."}
	pStateName = param{Name: "state", Flag: "state", Kind: kindString,
		Desc: "Filter by state (id or name, whichever that column holds)."}
	pZoneName = param{Name: "zone", Flag: "zone", Kind: kindString,
		Desc: "Filter by zone (id or name, whichever that column holds)."}
	pIncludeDeleted = param{Name: "include_deleted", Flag: "include-deleted", Kind: kindBool,
		Desc: "Include soft-deleted rows. DSR never hard-deletes; the default excludes rows flagged deleted, which is almost always what you want."}
	pID = param{Name: "id", Kind: kindInt, Min: 1,
		Desc: "The numeric id the chosen action operates on (positional argument). Which id it is depends on the action — see the action list."}
	pLimit = param{Name: "limit", Flag: "limit", Kind: kindInt, Min: 1, Max: 5000,
		Desc: "Maximum rows to return. Default 200. DSR is a large database (tbl_retailers ~127k rows, tbl_geoLocation ~27M) — raise this deliberately, not by habit."}
	pStatus = param{Name: "status", Flag: "status", Kind: kindInt, Min: 0,
		Desc: "Filter by approval status (0 = pending)."}
)

// specs is the complete, ordered tool set. Order here is the order tools are
// registered, and tools_test.go pins the exact names.
var specs = []*toolSpec{
	//
	// 1. dsr_doctor ------------------------------------------------------
	//
	{
		Name:  "dsr_doctor",
		Title: "DSR connection doctor",
		Desc: "Check the DSR system end to end: is the SQL Server instance reachable, which login and database are in use, " +
			"how many tables the database has, and is the web portal answering. Returns a JSON status report; the password is never included. " +
			"Call this first when another tool fails, to tell a network/VPN problem apart from a credentials or query problem.",
		Fixed: []string{"doctor"},
	},

	//
	// 2. dsr_query -------------------------------------------------------
	//
	{
		Name:  "dsr_query",
		Title: "Read-only T-SQL query",
		Desc: "Run ONE read-only T-SQL statement against the DSR_V6 database and return the rows as JSON. " +
			"Use this only when no domain tool answers the question — the domain tools already encode DSR's joins and soft-delete rules, " +
			"and getting those wrong is the usual way a DSR number comes out wrong. " +
			"Only a single SELECT (or WITH ... SELECT) is accepted: multi-statement batches, EXEC, DDL and DML are rejected before they reach the server. " +
			"Results are always capped — the query is wrapped as SELECT TOP <limit> — so aggregate in SQL rather than pulling rows to count them.",
		Fixed:       []string{"query"},
		Pos:         "sql",
		PosRequired: true,
		Params: []param{
			{Name: "sql", Kind: kindString, Desc: "The T-SQL SELECT (or WITH ... SELECT) to run. Passed to the CLI verbatim as one argument, so quotes and comments survive intact."},
			pLimit,
		},
	},

	//
	// 3. dsr_schema ------------------------------------------------------
	//
	{
		Name:  "dsr_schema",
		Title: "DSR database catalog",
		Desc: "Explore the DSR_V6 catalog and sample any table: list tables with row counts, list a table's columns, list primary/foreign keys, " +
			"list views, peek at the first rows of a table, or count a table's rows. " +
			"Start here when you do not know which table holds something — DSR has 209 tables and the names are inconsistent (tbl_retailers, tbl_SalesReport, TAReprotSave).",
		Params: []param{
			{Name: "table", Kind: kindString, Desc: "Table name (case-insensitive). Required for peek and count; optional for columns (omit it to get every column of every table)."},
			{Name: "min_rows", Flag: "min-rows", Kind: kindInt, Min: 0, Desc: "For action=tables: only tables with at least this many rows. Use 1 to hide the empty ones."},
			{Name: "rows", Flag: "rows", Kind: kindInt, Min: 1, Max: 5000, Desc: "For action=peek: how many rows to show (default 10)."},
			{Name: "where", Flag: "where", Kind: kindString, Desc: "For action=count: a T-SQL WHERE clause WITHOUT the WHERE keyword (e.g. \"attDate >= '2026-07-01'\"). Read-only: a payload carrying a second statement is rejected."},
			pLimit,
		},
		Actions: []action{
			{Name: "tables", Argv: []string{"schema", "tables"}, Flags: []string{"min_rows", "limit"},
				Desc: "every table with its row count"},
			{Name: "columns", Argv: []string{"schema", "columns"}, Pos: "table", Flags: []string{"limit"},
				Desc: "columns and types, for one table or all of them"},
			{Name: "keys", Argv: []string{"schema", "keys"}, Flags: []string{"limit"},
				Desc: "primary and foreign keys — the join map"},
			{Name: "views", Argv: []string{"schema", "views"}, Flags: []string{"limit"},
				Desc: "views defined in the database"},
			{Name: "peek", Argv: []string{"peek"}, Pos: "table", PosRequired: true, Flags: []string{"rows", "limit"},
				Desc: "first N rows of a table"},
			{Name: "count", Argv: []string{"count"}, Pos: "table", PosRequired: true, Flags: []string{"where"},
				Desc: "row count, optionally filtered by where"},
		},
	},

	//
	// 4. dsr_retailers ---------------------------------------------------
	//
	{
		Name:  "dsr_retailers",
		Title: "Retailers, outlets and distributors",
		Desc: "The outlet master: ~127,000 retailers with their type, territory and owning distributor. " +
			"Distributors live in the SAME table (tbl_retailers with type='Distributor'), which is why they are actions here rather than a separate tool — " +
			"use action=distributors for the distributor list, and distributor_shops/distributor_mappings to see the outlets under one of them.",
		Params: []param{
			pID, pStateName, pZoneName, pIncludeDeleted, pLimit,
			{Name: "type", Flag: "type", Kind: kindString, Desc: "Outlet type, e.g. Shop, Distributor, Modern Store."},
		},
		Actions: []action{
			{Name: "list", Argv: []string{"retailers", "list"}, Flags: []string{"state", "zone", "type", "include_deleted", "limit"},
				Desc: "retailers, filtered by state/zone/type"},
			{Name: "get", Argv: []string{"retailers", "get"}, Pos: "id", PosRequired: true,
				Desc: "one retailer in full, by tbl_retailers.Id"},
			{Name: "count", Argv: []string{"retailers", "count"}, Flags: []string{"state", "zone", "type", "include_deleted"},
				Desc: "how many retailers match"},
			{Name: "distributors", Argv: []string{"distributors", "list"}, Flags: []string{"state", "zone", "include_deleted", "limit"},
				Desc: "distributors only"},
			{Name: "distributors_count", Argv: []string{"distributors", "count"}, Flags: []string{"state", "zone", "include_deleted"},
				Desc: "how many distributors match"},
			{Name: "distributor_shops", Argv: []string{"distributors", "shops"}, Pos: "id", PosRequired: true, Flags: []string{"include_deleted", "limit"},
				Desc: "outlets served by one distributor (id = distributor's tbl_retailers.Id)"},
			{Name: "distributor_mappings", Argv: []string{"distributors", "mappings"}, Pos: "id", PosRequired: true, Flags: []string{"limit"},
				Desc: "salesperson/beat mappings for one distributor"},
		},
	},

	//
	// 5. dsr_salespersons ------------------------------------------------
	//
	{
		Name:  "dsr_salespersons",
		Title: "Field workforce",
		Desc: "The field team (192 people): SOs, ASMs, RSMs, promoters and their reporting lines. " +
			"Use action=subordinates to walk the hierarchy downward from a manager.",
		Params: []param{
			pID, pStateName, pIncludeDeleted, pLimit,
			{Name: "type", Flag: "type", Kind: kindString, Desc: "PERSONTYPE label, e.g. SO, ASM, RSM, PROMOTER(MT)."},
		},
		Actions: []action{
			{Name: "list", Argv: []string{"salespersons", "list"}, Flags: []string{"state", "type", "include_deleted", "limit"},
				Desc: "the field workforce, filtered by state/type"},
			{Name: "get", Argv: []string{"salespersons", "get"}, Pos: "id", PosRequired: true,
				Desc: "one salesperson in full, by tbl_salesperson.ID"},
			{Name: "count", Argv: []string{"salespersons", "count"}, Flags: []string{"state", "type", "include_deleted"},
				Desc: "how many salespersons match"},
			{Name: "subordinates", Argv: []string{"salespersons", "subordinates"}, Pos: "id", PosRequired: true, Flags: []string{"include_deleted", "limit"},
				Desc: "everyone reporting to one manager (id = manager's tbl_salesperson.ID)"},
		},
	},

	//
	// 6. dsr_territory ---------------------------------------------------
	//
	{
		Name:  "dsr_territory",
		Title: "Territory hierarchy and beats",
		Desc: "How DSR divides the country and the working day: the state -> zone -> area -> sub-area hierarchy, and the BEATS (daily routes) laid over it. " +
			"A beat is the list of outlets a salesperson is meant to visit on a given day, so beats are the link between the territory map and the visit data in dsr_sales.",
		Params: []param{
			pID, pSalesperson, pStateName, pZoneName, pIncludeDeleted, pFrom, pTo, pLimit,
			{Name: "state_id", Flag: "state", Kind: kindInt, Min: 1, Desc: "For action=zones: parent state id (tbl_states.stateId)."},
			{Name: "zone_id", Flag: "zone", Kind: kindInt, Min: 1, Desc: "For action=areas: parent zone id (tbl_zones.zoneId)."},
			{Name: "area_id", Flag: "area", Kind: kindInt, Min: 1, Desc: "For action=subareas: parent area id (tbl_areas.areaId)."},
		},
		Actions: []action{
			{Name: "states", Argv: []string{"geography", "states"}, Flags: []string{"limit"}, Desc: "states"},
			{Name: "zones", Argv: []string{"geography", "zones"}, Flags: []string{"state_id", "limit"}, Desc: "zones, optionally within one state"},
			{Name: "areas", Argv: []string{"geography", "areas"}, Flags: []string{"zone_id", "limit"}, Desc: "areas, optionally within one zone"},
			{Name: "subareas", Argv: []string{"geography", "subareas"}, Flags: []string{"area_id", "limit"}, Desc: "sub-areas, optionally within one area"},
			{Name: "beats", Argv: []string{"beats", "list"}, Flags: []string{"salesperson", "include_deleted", "limit"}, Desc: "beats/routes, optionally for one salesperson"},
			{Name: "beat_shops", Argv: []string{"beats", "shops"}, Pos: "id", PosRequired: true, Flags: []string{"state", "zone", "include_deleted", "limit"},
				Desc: "outlets on one beat (id = tbl_beats.beatId)"},
			{Name: "beat_assignments", Argv: []string{"beats", "assignments"}, Flags: []string{"salesperson", "from", "to", "include_deleted", "limit"},
				Desc: "which beat was assigned to whom, by date"},
			{Name: "beats_count", Argv: []string{"beats", "count"}, Flags: []string{"salesperson", "include_deleted"}, Desc: "how many beats match"},
		},
	},

	//
	// 7. dsr_products ----------------------------------------------------
	//
	{
		Name:  "dsr_products",
		Title: "Product master",
		Desc: "DSR's own SKU catalogue (tbl_item). Note this is DSR's item master, NOT SAP's — item ids here do not match SAP ItemCodes, " +
			"so resolve a product through this tool before using an item filter on any other dsr tool.",
		Params: []param{
			pID, pIncludeDeleted, pLimit,
			{Name: "type", Flag: "type", Kind: kindInt, Min: 1, Desc: "Item type id (tbl_itemType.Id, e.g. 4 = MUSTARD)."},
		},
		Actions: []action{
			{Name: "list", Argv: []string{"products", "list"}, Flags: []string{"type", "include_deleted", "limit"}, Desc: "SKUs, optionally by item type"},
			{Name: "get", Argv: []string{"products", "get"}, Pos: "id", PosRequired: true, Desc: "one SKU in full, by tbl_item.Id"},
			{Name: "count", Argv: []string{"products", "count"}, Flags: []string{"type", "include_deleted"}, Desc: "how many SKUs match"},
		},
	},

	//
	// 8. dsr_attendance --------------------------------------------------
	//
	{
		Name:  "dsr_attendance",
		Title: "Attendance and GPS trail",
		Desc: "Where the field team actually was: GPS punch-in/punch-out attendance, a per-person summary, a register view, " +
			"and the raw location breadcrumb trail. " +
			"The breadcrumb table is ~27 MILLION rows — always bound geo_track with from/to and a person, and prefer geo_count to find out how much data a window holds before pulling it.",
		Params: []param{
			pID, pSalesperson, pFrom, pTo, pLimit,
		},
		Actions: []action{
			{Name: "list", Argv: []string{"attendance", "list"}, Flags: []string{"salesperson", "from", "to", "limit"}, Desc: "attendance punches"},
			{Name: "summary", Argv: []string{"attendance", "summary"}, Flags: []string{"salesperson", "from", "to", "limit"}, Desc: "days present per person"},
			{Name: "count", Argv: []string{"attendance", "count"}, Flags: []string{"salesperson", "from", "to"}, Desc: "how many punches match"},
			{Name: "register", Argv: []string{"attendance", "register"}, Flags: []string{"salesperson", "from", "to", "limit"}, Desc: "register-style attendance grid"},
			{Name: "geo_track", Argv: []string{"geo", "track"}, Pos: "id", PosRequired: true, Flags: []string{"from", "to", "limit"},
				Desc: "GPS breadcrumb trail for one person (id = tbl_salesperson.ID) — bound it with from/to"},
			{Name: "geo_last", Argv: []string{"geo", "last"}, Pos: "id", PosRequired: true, Desc: "that person's most recent GPS fix"},
			{Name: "geo_count", Argv: []string{"geo", "count"}, Pos: "id", PosRequired: true, Flags: []string{"from", "to"},
				Desc: "how many breadcrumbs exist for a person and window"},
		},
	},

	//
	// 9. dsr_sales -------------------------------------------------------
	//
	{
		Name:  "dsr_sales",
		Title: "Secondary sales (SO and promoter)",
		Desc: "SECONDARY sales — what the field sold INTO retail outlets, captured visit by visit. " +
			"Two capture paths share this tool because they are the same business event recorded by different people: " +
			"the sales officer's own visits (visits/lines/summary/count, tbl_SalesReport) and in-store promoters (promoter_*, tbl_SalesReportPromoter). " +
			"Do not add them together without saying so. For sales JIVO made TO distributors, use dsr_supply (primary sales) instead.",
		Params: []param{
			pID, pSalesperson, pRetailer, pStateName, pZoneName, pFrom, pTo, pIncludeDeleted, pLimit,
			{Name: "by", Flag: "by", Kind: kindString, Enum: []string{"day", "person"}, Desc: "For action=summary: group by day or by person (default day)."},
		},
		Actions: []action{
			{Name: "visits", Argv: []string{"sales", "visits"}, Flags: []string{"salesperson", "retailer", "from", "to", "include_deleted", "limit"},
				Desc: "SO visit headers — one row per outlet visit"},
			{Name: "lines", Argv: []string{"sales", "lines"}, Pos: "id", PosRequired: true, Flags: []string{"include_deleted", "limit"},
				Desc: "the SKU lines of one visit (id = salesId from action=visits)"},
			{Name: "summary", Argv: []string{"sales", "summary"}, Flags: []string{"salesperson", "retailer", "from", "to", "include_deleted", "by", "limit"},
				Desc: "totals rolled up by day or by person"},
			{Name: "count", Argv: []string{"sales", "count"}, Flags: []string{"salesperson", "retailer", "from", "to", "include_deleted"},
				Desc: "how many SO visits match"},
			{Name: "promoter_visits", Argv: []string{"promoters", "visits"}, Flags: []string{"salesperson", "retailer", "state", "zone", "from", "to", "include_deleted", "limit"},
				Desc: "promoter in-store visit headers"},
			{Name: "promoter_lines", Argv: []string{"promoters", "lines"}, Pos: "id", PosRequired: true, Flags: []string{"include_deleted", "limit"},
				Desc: "the SKU lines of one promoter visit"},
			{Name: "promoter_count", Argv: []string{"promoters", "count"}, Flags: []string{"salesperson", "retailer", "state", "zone", "from", "to", "include_deleted"},
				Desc: "how many promoter visits match"},
		},
	},

	//
	// 10. dsr_supply -----------------------------------------------------
	//
	{
		Name:  "dsr_supply",
		Title: "Primary sales and stock declarations",
		Desc: "The distributor side of the pipe: PRIMARY sales (JIVO -> distributor lines and orders) and the STOCK DECLARATIONS " +
			"that say what is sitting in the trade — at a retailer, at a distributor, line by line, and the monthly closing position. " +
			"Primary minus secondary is how DSR sees channel inventory building up. Stock declarations are self-reported by the field, " +
			"so treat them as claims, not as a measured warehouse balance.",
		Params: []param{
			pID, pSalesperson, pRetailer, pItem, pFrom, pTo, pIncludeDeleted, pLimit,
			{Name: "pending", Flag: "pending", Kind: kindBool, Desc: "For primary_stock: only entries still awaiting approval (approved = 0)."},
			{Name: "unresolved", Flag: "unresolved", Kind: kindBool, Desc: "For primary_orders: only order lines whose itemid never resolved to a SKU (NULL) — the data-quality view."},
			{Name: "distributor", Flag: "distributor", Kind: kindInt, Min: 1, Desc: "For stock_* actions: distributor id (tbl_distributorStock.distId / tbl_monthlystock.distid)."},
			{Name: "distributor_id", Flag: "distributor", Kind: kindString, Desc: "For primary_orders: distributor id as recorded on the order (tbl_distorders.distid, a string column)."},
		},
		Actions: []action{
			{Name: "primary_list", Argv: []string{"primary", "list"}, Flags: []string{"retailer", "item", "from", "to", "include_deleted", "limit"},
				Desc: "primary sales lines (JIVO -> distributor)"},
			{Name: "primary_count", Argv: []string{"primary", "count"}, Flags: []string{"retailer", "item", "from", "to", "include_deleted"},
				Desc: "how many primary lines match"},
			{Name: "primary_stock", Argv: []string{"primary", "stock"}, Flags: []string{"salesperson", "from", "to", "pending", "include_deleted", "limit"},
				Desc: "primary stock entries, with an approval filter"},
			{Name: "primary_orders", Argv: []string{"primary", "orders"}, Flags: []string{"distributor_id", "from", "to", "unresolved", "limit"},
				Desc: "distributor order lines"},
			{Name: "stock_retailer", Argv: []string{"stock", "retailer"}, Pos: "id", PosRequired: true, Flags: []string{"item", "limit"},
				Desc: "stock declared at a retailer during one visit (id = salesId)"},
			{Name: "stock_distributor", Argv: []string{"stock", "distributor"}, Pos: "id", PosRequired: true, Flags: []string{"salesperson", "from", "to", "include_deleted", "limit"},
				Desc: "stock declarations for one distributor (id = distributor id)"},
			{Name: "stock_lines", Argv: []string{"stock", "lines"}, Pos: "id", PosRequired: true, Flags: []string{"item", "include_deleted", "limit"},
				Desc: "the SKU lines of one distributor stock declaration (id = distStockId)"},
			{Name: "stock_monthly", Argv: []string{"stock", "monthly"}, Flags: []string{"distributor", "item", "from", "to", "limit"},
				Desc: "monthly closing stock positions"},
			{Name: "stock_count", Argv: []string{"stock", "count"}, Flags: []string{"distributor", "salesperson", "from", "to", "include_deleted"},
				Desc: "how many stock declarations match"},
		},
	},

	//
	// 11. dsr_incentives -------------------------------------------------
	//
	{
		Name:  "dsr_incentives",
		Title: "Targets, schemes and gifts",
		Desc: "What the field was asked to do and what it was given to do it with: monthly TARGETS versus actuals (per person, per category, per retailer) " +
			"and the TRADE SCHEMES and gifts issued at the outlet. " +
			"Targets are the only place DSR states an intended number, so they are the right denominator for any achievement question.",
		Params: []param{
			pID, pSalesperson, pRetailer, pItem, pFrom, pTo, pIncludeDeleted, pLimit,
			{Name: "include_inactive", Flag: "include-inactive", Kind: kindBool, Desc: "For action=gifts: include gifts whose giftAllow is not 1 (withdrawn from the catalogue)."},
		},
		Actions: []action{
			{Name: "target_person", Argv: []string{"targets", "person"}, Pos: "id", PosRequired: true, Flags: []string{"from", "to", "limit"},
				Desc: "one person's targets vs actuals (id = user id)"},
			{Name: "target_category", Argv: []string{"targets", "category"}, Pos: "id", PosRequired: true, Flags: []string{"from", "to", "limit"},
				Desc: "one person's targets broken down by category (id = tbl_salesperson.ID)"},
			{Name: "target_retailer", Argv: []string{"targets", "retailer"}, Pos: "id", PosRequired: true, Flags: []string{"from", "to", "limit"},
				Desc: "targets set against one retailer"},
			{Name: "target_count", Argv: []string{"targets", "count"}, Flags: []string{"salesperson", "from", "to"},
				Desc: "how many target rows match"},
			{Name: "schemes_sold", Argv: []string{"schemes", "list-sold"}, Flags: []string{"item", "from", "to", "include_deleted", "limit"},
				Desc: "scheme lines actually sold"},
			{Name: "schemes_count", Argv: []string{"schemes", "count"}, Flags: []string{"item", "from", "to", "include_deleted"},
				Desc: "how many scheme lines match"},
			{Name: "gifts", Argv: []string{"schemes", "gifts"}, Flags: []string{"include_inactive", "limit"},
				Desc: "the gift catalogue"},
			{Name: "gift", Argv: []string{"schemes", "get"}, Pos: "id", PosRequired: true,
				Desc: "one gift in full (id = giftId)"},
			{Name: "gifts_issued", Argv: []string{"schemes", "issued"}, Flags: []string{"salesperson", "retailer", "from", "to", "include_deleted", "limit"},
				Desc: "gifts actually issued at outlets"},
		},
	},

	//
	// 12. dsr_travel -----------------------------------------------------
	//
	{
		Name:  "dsr_travel",
		Title: "Travel allowance",
		Desc: "Travel allowance (TA): the per-person rate card, the place-to-place km matrix, claimed km, and the TA reports with their approval status. " +
			"Use status=0 to find claims still pending approval.",
		Params: []param{
			pSalesperson, pRetailer, pFrom, pTo, pIncludeDeleted, pStatus, pLimit,
			{Name: "from_area", Flag: "from-area", Kind: kindInt, Min: 1, Desc: "For action=place: origin area id (FromAreaId)."},
			{Name: "to_area", Flag: "to-area", Kind: kindInt, Min: 1, Desc: "For action=place: destination area id (ToAreaId)."},
		},
		Actions: []action{
			{Name: "rates", Argv: []string{"travel", "rates"}, Flags: []string{"salesperson", "include_deleted", "limit"}, Desc: "per-person TA rate card"},
			{Name: "km", Argv: []string{"travel", "km"}, Flags: []string{"salesperson", "retailer", "include_deleted", "limit"}, Desc: "claimed kilometres"},
			{Name: "place", Argv: []string{"travel", "place"}, Flags: []string{"from_area", "to_area", "include_deleted", "limit"}, Desc: "place-to-place distance matrix"},
			{Name: "reports", Argv: []string{"travel", "reports"}, Flags: []string{"salesperson", "status", "from", "to", "limit"}, Desc: "TA reports with approval status"},
			{Name: "count", Argv: []string{"travel", "count"}, Flags: []string{"salesperson", "status", "from", "to"}, Desc: "how many TA reports match"},
		},
	},

	//
	// 13. dsr_ecom -------------------------------------------------------
	//
	{
		Name:  "dsr_ecom",
		Title: "Marketplace sales, returns and settlements",
		Desc: "The marketplace channel as DSR records it (Amazon/Flipkart): order-level sales, returns with their condition, and settlement lines. " +
			"This is DSR's copy of the data — where the ecom CLI and this tool disagree, say which source a number came from rather than merging them.",
		Params: []param{
			pFrom, pTo, pStateName, pLimit,
			{Name: "sku", Flag: "sku", Kind: kindString, Desc: "Exact marketplace SKU (sales) or return SKU (returns)."},
			{Name: "condition", Flag: "condition", Kind: kindString, Desc: "For action=returns: item condition as the marketplace reported it, e.g. OK."},
			{Name: "table", Flag: "table", Kind: kindString, Enum: []string{"sales", "returns", "settlements"},
				Desc: "For action=count: which of the three tables to count (default sales)."},
		},
		Actions: []action{
			{Name: "sales", Argv: []string{"ecom", "sales"}, Flags: []string{"sku", "state", "from", "to", "limit"}, Desc: "marketplace sales lines"},
			{Name: "returns", Argv: []string{"ecom", "returns"}, Flags: []string{"sku", "condition", "from", "to", "limit"}, Desc: "marketplace returns"},
			{Name: "settlements", Argv: []string{"ecom", "settlements"}, Flags: []string{"from", "to", "limit"}, Desc: "marketplace settlement lines"},
			{Name: "count", Argv: []string{"ecom", "count"}, Flags: []string{"table", "from", "to"}, Desc: "row count for sales, returns or settlements"},
		},
	},

	//
	// 14. dsr_admin ------------------------------------------------------
	//
	{
		Name:  "dsr_admin",
		Title: "Back-office users and platform logs",
		Desc: "Who can use the DSR portal (users, roles, per-user permissions) and how the platform is behaving (API exception log, report-SQL log). " +
			"The logs are the fastest way to tell 'the data is wrong' apart from 'the app has been failing since Tuesday' — " +
			"pass errors=true on logs_count to drop the routine GetShopsData breadcrumbs and see genuine failures only.",
		Params: []param{
			pID, pSalesperson, pFrom, pTo, pIncludeDeleted, pLimit,
			{Name: "role", Flag: "role", Kind: kindInt, Min: 1, Desc: "Role id (tbl_roles.Id: 1=ADMIN, 2=USER, 3=VIEWER, 4=SUPER ADMIN, 5=CALLER)."},
			{Name: "errors", Flag: "errors", Kind: kindBool, Desc: "For action=logs_count: count only genuine errors."},
		},
		Actions: []action{
			{Name: "users", Argv: []string{"users", "list"}, Flags: []string{"role", "include_deleted", "limit"}, Desc: "portal users"},
			{Name: "roles", Argv: []string{"users", "roles"}, Flags: []string{"limit"}, Desc: "the role catalogue"},
			{Name: "permissions", Argv: []string{"users", "permissions"}, Pos: "id", PosRequired: true, Flags: []string{"limit"},
				Desc: "one user's permissions (id = user id)"},
			{Name: "users_count", Argv: []string{"users", "count"}, Flags: []string{"role", "include_deleted"}, Desc: "how many users match"},
			{Name: "logs_recent", Argv: []string{"logs", "recent"}, Flags: []string{"salesperson", "from", "to", "limit"}, Desc: "recent API log entries"},
			{Name: "logs_errors", Argv: []string{"logs", "errors"}, Flags: []string{"salesperson", "from", "to", "limit"}, Desc: "API exceptions only"},
			{Name: "logs_count", Argv: []string{"logs", "count"}, Flags: []string{"salesperson", "from", "to", "errors"}, Desc: "how many log rows match"},
			{Name: "logs_reports", Argv: []string{"logs", "reports"}, Flags: []string{"limit"}, Desc: "the report-SQL log"},
		},
	},

	//
	// 15. dsr_portal -----------------------------------------------------
	//
	{
		Name:  "dsr_portal",
		Title: "DSR web portal reports",
		Desc: "GET-only calls to the DSR web portal's OWN report endpoints, so a figure computed by direct SQL can be checked against the figure the portal itself shows a user. " +
			"Needs the portal login (DSR_PORTAL_USER / DSR_PORTAL_PASSWORD); without it these actions fail cleanly and every SQL-backed tool keeps working. " +
			"Use it to arbitrate a disagreement, not as the primary source — the SQL path is faster and filterable.",
		Params: []param{
			pFrom, pTo,
			{Name: "month", Flag: "month", Kind: kindString, Desc: "For action=item_sale: the month, in the portal's own format, e.g. \"July,2026\"."},
		},
		Actions: []action{
			{Name: "check", Argv: []string{"portal", "check"}, Desc: "log in and confirm the portal session works"},
			{Name: "monthly_sale", Argv: []string{"portal", "monthly-sale"}, Flags: []string{"from", "to"}, Desc: "the portal's monthly sale totals (/Home/MonthlySale)"},
			{Name: "item_sale", Argv: []string{"portal", "item-sale"}, Flags: []string{"month"}, Required: []string{"month"}, Desc: "the portal's item-wise sale report for one month"},
			{Name: "unapproved_count", Argv: []string{"portal", "unapproved-count"}, Desc: "the portal's count of unapproved entries"},
		},
	},
}

// actionHelp renders a tool's action list into its description, so the enum an
// agent sees is never just bare identifiers.
func actionHelp(t *toolSpec) string {
	if len(t.Actions) == 0 {
		return ""
	}
	var b strings.Builder
	b.WriteString(" ACTIONS: ")
	for i, a := range t.Actions {
		if i > 0 {
			b.WriteString("; ")
		}
		b.WriteString(a.Name)
		if a.Desc != "" {
			b.WriteString(" = ")
			b.WriteString(a.Desc)
		}
	}
	b.WriteString(".")
	return b.String()
}
