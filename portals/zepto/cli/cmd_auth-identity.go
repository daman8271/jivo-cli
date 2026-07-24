package main

import "github.com/spf13/cobra"

func init() { registerSection(newIdentityCmd) }

// newIdentityCmd — Auth & Identity. Session/user-identity reads only: resolve
// the current user from an auth token, look a user up by invite code.
// Sign-in / sign-out / MFA / reset-password / invite / disable-user are all
// WRITES → out of scope (guardrail-blocked).
// Source: sections.json slug "auth-identity".
func newIdentityCmd(app *App) *cobra.Command {
	id := &cobra.Command{Use: "identity", Short: "Auth & identity reads (who-am-I / user lookup)"}
	id.AddCommand(
		// user profile from the current auth token (GET_USER_PROFILE)
		simpleGet(app, "identity", "user-profile", "Current user profile from auth token (vendor)", hostFCC, "/vendor/api/v1/auth/get-user-by-token"),
		queryGet(app, "identity", "user-by-token", "Resolve user by auth token (--query for token)", hostFCC, "/api/v1/auth/get-user-by-token"),
		// user lookup by invite code (auth-backend)
		queryGet(app, "identity", "user-by-code", "Resolve user by invite code (--query for code)", hostAuth, "/api/v1/auth/get-user-by-code"),
	)
	return id
}
