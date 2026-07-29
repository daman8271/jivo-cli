package cli

// Domain commands for portal back-office users — the DSR web-portal identity
// layer (NOT the field-app salespersons). See domain.go for the shared helpers
// and study/vault/portal-users-and-permissions.md for the data model.
//
// Tables: tbl_loginUser (accounts), tbl_roles (5 coarse labels),
// tbl_pageMaster (portal screens), tbl_pagePermission (the real per-user ACL).
//
// SECURITY: never select password/otp/refreshToken columns — list/get here
// deliberately omit tbl_loginUser.password.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newUsersCmd) }

func newUsersCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "users",
		Short:   "Portal back-office users — list, roles, permissions, count",
		Aliases: []string{"user", "logins"},
	}
	c.AddCommand(usersListCmd(app), usersRolesCmd(app), usersPermissionsCmd(app), usersCountCmd(app))
	return c
}

// usersWhere builds the live/role filter for tbl_loginUser (aliased "u").
func usersWhere(f *domFilters, role int) string {
	return fWhere(
		fEqInt("u.role", role),
		fLive("u.", f.IncludeDeleted),
	)
}

func usersListCmd(app *App) *cobra.Command {
	var f domFilters
	var role int
	c := &cobra.Command{
		Use:     "list",
		Short:   "List portal accounts with role name (never shows password)",
		Example: "  dsr users list\n  dsr users list --role 1 -n 20 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d u.UserID, u.name, u.userName, u.email, "+
				"u.role AS roleId, r.role AS roleName, u.backDaysAllowed, u.approvedStatus, "+
				"u.CreatedOn, u.deleted "+
				"FROM tbl_loginUser u LEFT JOIN tbl_roles r ON r.Id = u.role%s "+
				"ORDER BY u.UserID DESC",
				topN(app, 100), usersWhere(&f, role))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	c.Flags().IntVar(&role, "role", 0, "filter by role id (tbl_roles.Id: 1=ADMIN,2=USER,3=VIEWER,4=SUPER ADMIN,5=CALLER)")
	return c
}

func usersRolesCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "roles",
		Short:   "List the coarse role labels (tbl_roles)",
		Args:    cobra.NoArgs,
		Example: "  dsr users roles --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runSelect(app, "SELECT Id, role FROM tbl_roles ORDER BY Id")
		},
	}
}

func usersPermissionsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "permissions <userId>",
		Short:   "Show the page permission matrix (CRUD bits) for one user",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr users permissions 42\n  dsr users permissions 42 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("userId must be an integer, got %q", args[0])
			}
			// One row per portal screen; NULL read bit => page hidden for this user.
			q := fmt.Sprintf("SELECT p.id AS pageId, LTRIM(RTRIM(p.pageName)) AS pageName, "+
				"LTRIM(RTRIM(p.pageUrl)) AS pageUrl, "+
				"pp.readPermission, pp.createPermission, pp.updatePermission, pp.deletePermission, "+
				"pp.createdBy AS grantedBy, pp.createdOn "+
				"FROM tbl_pageMaster p "+
				"LEFT JOIN tbl_pagePermission pp ON pp.pageId = p.id AND pp.userId = %d "+
				"WHERE p.DeletedOn IS NULL ORDER BY p.id", id)
			return runSelect(app, q)
		},
	}
	return c
}

func usersCountCmd(app *App) *cobra.Command {
	var f domFilters
	var role int
	c := &cobra.Command{
		Use:   "count",
		Short: "Count portal accounts matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS users FROM tbl_loginUser u" + usersWhere(&f, role)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	c.Flags().IntVar(&role, "role", 0, "filter by role id (tbl_roles.Id)")
	return c
}
