package cli

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"oms-pp-cli/internal/cliutil"
	"oms-pp-cli/internal/config"

	"github.com/spf13/cobra"
)

// newAuthOmsLoginCmd implements credential login for oms.jivo.in.
//
// OMS issues a short-lived JWT access token from POST /api/auth/login/ with a
// {username, password} body, returning {data:{tokens:{access, refresh}}}. The
// access token is then sent as `Authorization: Bearer <token>` on every call.
// This command performs that exchange (login is the ONE permitted write per the
// read-only law — it mutates nothing but a session) and stores the token via the
// same config path used by `auth set-token`, so all other commands authenticate
// automatically. The password is never written to disk or logged.
//
// Credential resolution order:
//
//	username: --username -> OMS_USERNAME
//	password: --password -> OMS_PASSWORD -> --password-stdin (reads stdin)
func newAuthOmsLoginCmd(flags *rootFlags) *cobra.Command {
	var username, password string
	var passwordStdin bool
	cmd := &cobra.Command{
		Use:   "login",
		Short: "Log in with username + password and store the JWT access token",
		Long: strings.TrimSpace(`
Log in to oms.jivo.in with your account username and password.

This exchanges your credentials at POST /api/auth/login/ for a JWT access token
and saves it to the config file (mode 0600), so every other command authenticates
automatically. Your password is never stored — only the token.

Login is the only write this read-only CLI performs: it creates a session token
and mutates no JIVO data.

Credential resolution order:
  username: --username  ->  OMS_USERNAME
  password: --password  ->  OMS_PASSWORD  ->  --password-stdin (reads stdin)

Prefer the env var or --password-stdin over --password: a value passed as
--password is visible in 'ps' output and your shell history.`),
		Example: strings.TrimSpace(`
  # Recommended: password from env (not visible in ps/history)
  OMS_USERNAME=paramjot OMS_PASSWORD=secret oms-pp-cli auth login

  # Or pipe the password on stdin
  printf '%s' "$PW" | oms-pp-cli auth login --username paramjot --password-stdin`),
		Annotations: map[string]string{
			// Login is a network side effect; never a read-only MCP tool.
			"mcp:hidden": "true",
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			if username == "" {
				username = os.Getenv("OMS_USERNAME")
			}
			if password == "" && !passwordStdin {
				password = os.Getenv("OMS_PASSWORD")
			}

			// Bare `auth login` with nothing to act on: show help, not an error.
			if username == "" && password == "" && !passwordStdin && cmd.Flags().NFlag() == 0 {
				return cmd.Help()
			}

			// Verify/dry-run: never touch the network or stdin.
			if dryRunOK(flags) || cliutil.IsVerifyEnv() {
				fmt.Fprintf(cmd.OutOrStdout(), "would log in to oms.jivo.in as %s\n", redactUsername(username))
				return nil
			}

			if passwordStdin && password == "" {
				data, err := io.ReadAll(os.Stdin)
				if err != nil {
					return usageErr(fmt.Errorf("reading password from stdin: %w", err))
				}
				password = strings.TrimRight(string(data), "\r\n")
			}
			if username == "" || password == "" {
				_ = cmd.Usage()
				return usageErr(fmt.Errorf("both a username and a password are required (use --username/--password, OMS_USERNAME/OMS_PASSWORD, or --password-stdin)"))
			}

			cfg, err := config.Load(flags.configPath)
			if err != nil {
				return configErr(err)
			}

			// Refuse to send credentials over a non-HTTPS origin (guards a
			// base-url downgrade that would capture the password in cleartext).
			base := strings.TrimRight(cfg.BaseURL, "/")
			if !strings.HasPrefix(base, "https://") &&
				!strings.HasPrefix(base, "http://localhost") &&
				!strings.HasPrefix(base, "http://127.0.0.1") &&
				!strings.HasPrefix(base, "http://[::1]") {
				return usageErr(fmt.Errorf("refusing to send credentials to insecure base URL %q; use an https origin", base))
			}

			ctx, cancel := boundCtx(cmd.Context(), flags)
			defer cancel()

			body, _ := json.Marshal(map[string]string{"username": username, "password": password})
			loginURL := base + "/api/auth/login/"
			req, err := http.NewRequestWithContext(ctx, http.MethodPost, loginURL, bytes.NewReader(body))
			if err != nil {
				return &cliError{code: 5, err: fmt.Errorf("building login request: %w", err)}
			}
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Accept", "application/json")

			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				return &cliError{code: 5, err: fmt.Errorf("contacting %s: %w", loginURL, err)}
			}
			defer resp.Body.Close()

			var parsed struct {
				Success bool   `json:"success"`
				Message string `json:"message"`
				Detail  string `json:"detail"`
				Data    struct {
					Tokens struct {
						Access  string `json:"access"`
						Refresh string `json:"refresh"`
					} `json:"tokens"`
					User struct {
						Username string `json:"username"`
						Role     string `json:"role"`
					} `json:"user"`
				} `json:"data"`
			}
			_ = json.NewDecoder(resp.Body).Decode(&parsed)

			if resp.StatusCode/100 != 2 || parsed.Data.Tokens.Access == "" {
				msg := parsed.Detail
				if msg == "" {
					msg = parsed.Message
				}
				if msg == "" {
					msg = fmt.Sprintf("login failed (HTTP %d)", resp.StatusCode)
				}
				return &cliError{code: 4, err: fmt.Errorf("%s", msg)}
			}

			access := parsed.Data.Tokens.Access
			refresh := parsed.Data.Tokens.Refresh
			if err := cfg.SaveTokens("", "", access, refresh, jwtExpiry(access)); err != nil {
				return configErr(fmt.Errorf("saving token: %w", err))
			}

			who := parsed.Data.User.Username
			if who == "" {
				who = username
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Logged in to oms.jivo.in as %s", who)
			if parsed.Data.User.Role != "" {
				fmt.Fprintf(cmd.OutOrStdout(), " (%s)", parsed.Data.User.Role)
			}
			fmt.Fprintf(cmd.OutOrStdout(), ". Token saved to %s\n", cfg.Path)
			return nil
		},
	}
	cmd.Flags().StringVar(&username, "username", "", "OMS username (or set OMS_USERNAME)")
	cmd.Flags().StringVar(&password, "password", "", "OMS password (prefer OMS_PASSWORD or --password-stdin)")
	cmd.Flags().BoolVar(&passwordStdin, "password-stdin", false, "Read the password from standard input")
	return cmd
}

// jwtExpiry decodes the `exp` claim from a JWT access token, returning that time.
// On any decode failure it returns the zero time (unknown expiry).
func jwtExpiry(token string) time.Time {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return time.Time{}
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return time.Time{}
	}
	var claims struct {
		Exp int64 `json:"exp"`
	}
	if err := json.Unmarshal(payload, &claims); err != nil || claims.Exp == 0 {
		return time.Time{}
	}
	return time.Unix(claims.Exp, 0)
}

// redactUsername masks the middle of a username for dry-run display.
func redactUsername(u string) string {
	if len(u) <= 2 {
		return u
	}
	return u[:1] + strings.Repeat("*", len(u)-2) + u[len(u)-1:]
}
