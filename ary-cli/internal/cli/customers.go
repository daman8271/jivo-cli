package cli

// Customers — CustomerMaster (the retail/CRM party master, distinct from
// AccountMaster which is the ledger).
//
// Notes (verified live 2026-08-27):
//   - CustomerID is nvarchar; SaleHeader.CustomerID is blank on walk-in bills.
//   - AccountID links a customer to their ledger account when they buy on credit.
//   - Limit / Spent / Deposit and the loyalty point columns are the CRM side;
//     the money that matters lives in the ledger (`ary accounts outstanding`).

import (
	"fmt"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() { register(newCustomersCmd) }

func newCustomersCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "customers",
		Short:   "Customer master — list, get, count, credit customers, dormant",
		Aliases: []string{"customer"},
	}
	c.AddCommand(customersListCmd(app), customersGetCmd(app), customersCountCmd(app),
		customersCreditCmd(app), customersDormantCmd(app))
	return c
}

const customersJoins = " FROM CustomerMaster c " +
	"LEFT JOIN CustomerTypeMaster ct ON ct.CustomerTypeID = c.CustomerTypeID " +
	"LEFT JOIN AccountMaster a ON a.AccountID = c.AccountID " +
	"LEFT JOIN StateMaster st ON st.StateID = c.StateID " +
	"LEFT JOIN CityMaster ci ON ci.CityID = c.CityID"

func customersListCmd(app *App) *cobra.Command {
	var f domFilters
	var typ int
	c := &cobra.Command{
		Use:     "list",
		Short:   "List customers with type, city, GSTIN, credit flag and ledger link",
		Example: "  ary customers list --search \"singh\" -n 40",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d c.CustomerID AS id, "+
				"COALESCE(NULLIF(c.CustomerName,''), NULLIF(c.CompanyName,''), "+
				"LTRIM(RTRIM(ISNULL(c.FirstName,'') + ' ' + ISNULL(c.LastName,'')))) AS customer, "+
				"ct.CustomerTypeName AS customer_type, ci.CityName AS city, st.StateName AS state, "+
				"c.GSTINNo AS gstin, c.Mobile AS mobile, c.AllowCreditSale AS credit_allowed, "+
				"CAST(c.Limit AS decimal(18,2)) AS crm_limit, CAST(c.Spent AS decimal(18,2)) AS crm_spent, "+
				"a.AccountName AS ledger_account, c.VisitCount AS visits, c.IsActive AS active%s%s "+
				"ORDER BY c.VisitCount DESC", topN(app, 40), customersJoins,
				fWhere(customersSearch(f.Search), fEqInt("c.CustomerTypeID", typ), fActive("c.", f.ActiveOnly)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search", "active")
	c.Flags().IntVar(&typ, "type", 0, "filter by CustomerTypeID (see `ary masters customer-types`)")
	return c
}

// customersSearch matches the search term across every name column plus mobile.
func customersSearch(s string) string {
	if s == "" {
		return ""
	}
	l := db.Lit("%" + s + "%")
	return "(c.CustomerName LIKE " + l + " OR c.CompanyName LIKE " + l + " OR c.FirstName LIKE " + l +
		" OR c.LastName LIKE " + l + " OR c.Mobile LIKE " + l + " OR c.GSTINNo LIKE " + l + ")"
}

func customersCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "count",
		Short: "Count customers, with the credit-enabled and active splits",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS customers, " +
				"SUM(CASE WHEN ISNULL(c.IsActive,0)=1 THEN 1 ELSE 0 END) AS active, " +
				"SUM(CASE WHEN ISNULL(c.AllowCreditSale,0)=1 THEN 1 ELSE 0 END) AS credit_allowed, " +
				"SUM(CASE WHEN c.AccountID IS NOT NULL AND c.AccountID <> 0 THEN 1 ELSE 0 END) AS with_ledger_account, " +
				"SUM(CASE WHEN c.GSTINNo IS NOT NULL AND LTRIM(RTRIM(c.GSTINNo)) <> '' THEN 1 ELSE 0 END) AS with_gstin " +
				"FROM CustomerMaster c" + fWhere(customersSearch(f.Search))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search")
	return c
}

func customersGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <CustomerID>",
		Short:   "One customer: master row plus their recent bills",
		Example: "  ary customers get 000001",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := db.Lit(args[0])
			return runSections(app, []section{
				{"master", "SELECT c.CustomerID AS id, " +
					"COALESCE(NULLIF(c.CustomerName,''), NULLIF(c.CompanyName,''), " +
					"LTRIM(RTRIM(ISNULL(c.FirstName,'') + ' ' + ISNULL(c.LastName,'')))) AS customer, " +
					"ct.CustomerTypeName AS customer_type, c.Address1 AS address, ci.CityName AS city, " +
					"st.StateName AS state, c.Pincode AS pincode, c.Mobile AS mobile, c.Email AS email, " +
					"c.GSTINNo AS gstin, c.AllowCreditSale AS credit_allowed, CAST(c.Limit AS decimal(18,2)) AS crm_limit, " +
					"a.AccountName AS ledger_account, c.VisitCount AS visits, " +
					"CAST(c.BalancePoint AS decimal(18,2)) AS loyalty_points, c.IsActive AS active" +
					customersJoins + " WHERE c.CustomerID = " + id},
				{"recent bills", "SELECT TOP 25 h.SerialNumber AS serial, CONVERT(varchar(16), h.VoucherDate, 120) AS date, " +
					"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS bill_no, l.LocationName AS location, " +
					"CAST(h.QtyTotal AS decimal(18,2)) AS qty, CAST(h.BillAmount AS decimal(18,2)) AS bill_amount " +
					"FROM SaleHeader h LEFT JOIN LocationMaster l ON l.LocationID = h.LocationID " +
					"WHERE h.CustomerID = " + id + " ORDER BY h.VoucherDate DESC, h.SerialNumber DESC"},
			})
		},
	}
}

func customersCreditCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "credit",
		Short: "Credit-sale customers and what their ledger account actually owes",
		Long: "Joins the CRM credit flag to the real bill-wise balance from RefMaster, so a customer\n" +
			"allowed credit but sitting on an old balance is visible in one place. Positive = owes ARY.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d c.CustomerID AS id, "+
				"COALESCE(NULLIF(c.CustomerName,''), NULLIF(c.CompanyName,'')) AS customer, "+
				"CAST(c.Limit AS decimal(18,2)) AS crm_limit, a.AccountName AS ledger_account, "+
				"a.CreditDays AS credit_days, CAST(a.CreditLimit AS decimal(18,2)) AS ledger_credit_limit, "+
				"CAST(ISNULL(r.balance,0) AS decimal(18,2)) AS outstanding "+
				"FROM CustomerMaster c "+
				"LEFT JOIN AccountMaster a ON a.AccountID = c.AccountID "+
				"LEFT JOIN (SELECT AccountID, SUM(DebitAmount - CreditAmount) AS balance FROM RefMaster "+
				"WHERE ISNULL(IsDeleted,0) = 0 GROUP BY AccountID) r ON r.AccountID = c.AccountID "+
				"WHERE ISNULL(c.AllowCreditSale,0) = 1 ORDER BY outstanding DESC", topN(app, 40))
			return runSelect(app, q)
		},
	}
	return c
}

func customersDormantCmd(app *App) *cobra.Command {
	var days int
	c := &cobra.Command{
		Use:   "dormant",
		Short: "Customers who used to buy and have not billed in N days",
		Long: "Ranked by what they used to be worth, so the list is a call-back sheet rather than a\n" +
			"dump of every inactive card.",
		Example: "  ary customers dormant --days 120 -n 40",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d s.CustomerID AS id, "+
				"COALESCE(NULLIF(c.CustomerName,''), NULLIF(c.CompanyName,'')) AS customer, c.Mobile AS mobile, "+
				"s.bills, CAST(s.value AS decimal(18,2)) AS lifetime_value, "+
				"CONVERT(varchar(10), s.last_bill, 120) AS last_bill, "+
				"DATEDIFF(day, s.last_bill, GETDATE()) AS days_since "+
				"FROM (SELECT CustomerID, COUNT(*) AS bills, SUM(BillAmount) AS value, MAX(VoucherDate) AS last_bill "+
				"FROM SaleHeader WHERE CustomerID IS NOT NULL AND LTRIM(RTRIM(CustomerID)) <> '' "+
				"GROUP BY CustomerID) s "+
				"LEFT JOIN CustomerMaster c ON c.CustomerID = s.CustomerID "+
				"WHERE s.last_bill < DATEADD(day, -%d, GETDATE()) ORDER BY s.value DESC", topN(app, 40), days)
			return runSelect(app, q)
		},
	}
	c.Flags().IntVar(&days, "days", 90, "dormant if no bill in this many days")
	return c
}
