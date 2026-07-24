package main

import "github.com/spf13/cobra"

func init() { registerSection(newUsersCmd) }

// newUsersCmd — Users & Access management. Read the vendor-portal user list,
// roles, per-application module/action maps, and pending user-approval details.
// Creating/activating users, assigning/creating roles, and approve/reject are
// WRITES → out of scope (guardrail-blocked).
func newUsersCmd(app *App) *cobra.Command {
	users := &cobra.Command{Use: "users", Short: "Users & access — roles, user list, module/action access maps (read-only)"}
	users.AddCommand(
		// auth-backend access-management reads
		simpleGet(app, "users", "roles", "Roles list (GET_ROLES_LIST)", hostAuth, "/api/v1/access-management/roles"),
		simpleGet(app, "users", "users", "Users list (GET_USERS_LIST)", hostAuth, "/api/v1/access-management/users"),
		simpleGet(app, "users", "vendors", "Managed vendors list (GET_MANAGE_VENDORS_LIST)", hostAuth, "/api/v1/access-management/vendors"),
		// fcc authorize reads
		simpleGet(app, "users", "modules-for-role", "Modules for an application + role (v1)", hostFCC, "/api/v1/authorize/fetch-all-modules-for-an-application-and-role"),
		simpleGet(app, "users", "authorize-roles", "Authorize roles list (v1)", hostFCC, "/api/v1/authorize/get-roles"),
		simpleGet(app, "users", "child-roles", "Child roles for current user (GET_USER_ROLES)", hostFCC, "/api/v1/users/child-roles"),
		simpleGet(app, "users", "modules", "Modules for an application (v2)", hostFCC, "/api/v2/authorize/fetch-all-modules-for-an-application"),
		getByID(app, "users", "approval-details", "User-approval details by id (v2)", hostFCC, "/api/v2/user-approvals/%s/details", "user_id"),
		simpleGet(app, "users", "entity-data", "Access-management entity data (GET_ENTITY_DATA)", hostFCC, "/brand-analytics-web/api/v1/access-management/user"),
		// vendor authorize reads
		simpleGet(app, "users", "vendor-modules-for-role", "Vendor: modules for an application + role (GET_ALL_MODULES_BASED_ON_ROLE)", hostFCC, "/vendor/api/v1/authorize/fetch-all-modules-for-an-application-and-role"),
		simpleGet(app, "users", "vendor-roles", "Vendor: all roles (GET_ALL_ROLES)", hostFCC, "/vendor/api/v1/authorize/get-roles"),
		simpleGet(app, "users", "vendor-modules", "Vendor: modules for an application (GET_ROLE_CONFIG, v2)", hostFCC, "/vendor/api/v2/authorize/fetch-all-modules-for-an-application"),
	)
	return users
}
