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

	"jivo-ecom-pp-cli/internal/cliutil"
	"jivo-ecom-pp-cli/internal/config"

	"github.com/spf13/cobra"
)

// newAuthLoginCmd implements credential login for ecom.jivo.in.
//
// The JIVO e-com API issues a short-lived (~24h) JWT access token from
// POST /api/auth/login with an {email, password} body. The token is then sent
// as `Authorization: Bearer <token>` on every call. This command performs that
// exchange and stores the resulting token via the same config path used by
// `auth set-token`, so all subsequent commands authenticate automatically.
//
// Credentials are resolved in order: --email/--password flags, then the
// JIVO_ECOM_EMAIL / JIVO_ECOM_PASSWORD environment variables, then (for the
// password only) --password-stdin which reads the secret from standard input.
// The password is never written to disk or logged — only the returned token is
// persisted, with mode 0600.
func newAuthLoginCmd(flags *rootFlags) *cobra.Command {
	var email, password string
	var passwordStdin bool
	cmd := &cobra.Command{
		Use:   "login",
		Short: "Log in with email + password and store the JWT access token",
		Long: strings.TrimSpace(`
Log in to ecom.jivo.in with your account email and password.

This exchanges your credentials at POST /api/auth/login for a JWT access token
(valid ~24h) and saves it to the config file (mode 0600), so every other command
authenticates automatically. Your password is never stored — only the token.

Credential resolution order:
  email:    --email  ->  JIVO_ECOM_EMAIL
  password: --password  ->  JIVO_ECOM_PASSWORD  ->  --password-stdin (reads stdin)

Prefer the env var or --password-stdin over --password: a value passed as
--password is visible in 'ps' output and your shell history.`),
		Example: strings.TrimSpace(`
  # Recommended: password from env (not visible in ps/history)
  JIVO_ECOM_EMAIL=you@jivo.in JIVO_ECOM_PASSWORD=secret jivo-ecom-pp-cli auth login

  # Or pipe the password on stdin
  printf '%s' "$PW" | jivo-ecom-pp-cli auth login --email you@jivo.in --password-stdin`),
		Annotations: map[string]string{
			// Login is a network side effect; never a read-only MCP tool.
			"mcp:hidden": "true",
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			// Resolve credentials up front (flags -> env) so the help-only
			// branch below can't mask a valid env-var-driven invocation.
			if email == "" {
				email = os.Getenv("JIVO_ECOM_EMAIL")
			}
			if password == "" && !passwordStdin {
				password = os.Getenv("JIVO_ECOM_PASSWORD")
			}

			// Bare `auth login` with nothing to act on: show help, not an error.
			if email == "" && password == "" && !passwordStdin && cmd.Flags().NFlag() == 0 {
				return cmd.Help()
			}

			// Verify/dry-run: never touch the network or stdin.
			if dryRunOK(flags) || cliutil.IsVerifyEnv() {
				fmt.Fprintf(cmd.OutOrStdout(), "would log in to ecom.jivo.in as %s\n", redactLoginEmail(email))
				return nil
			}

			if passwordStdin && password == "" {
				data, err := io.ReadAll(os.Stdin)
				if err != nil {
					return usageErr(fmt.Errorf("reading password from stdin: %w", err))
				}
				password = strings.TrimRight(string(data), "\r\n")
			}
			if email == "" || password == "" {
				_ = cmd.Usage()
				return usageErr(fmt.Errorf("both an email and a password are required (use --email/--password, JIVO_ECOM_EMAIL/JIVO_ECOM_PASSWORD, or --password-stdin)"))
			}

			cfg, err := config.Load(flags.configPath)
			if err != nil {
				return configErr(err)
			}

			// Refuse to send credentials over a non-HTTPS origin (guards a
			// JIVO_ECOM_BASE_URL downgrade that would capture the password in
			// cleartext). Loopback http is allowed for local dev/test servers.
			base := strings.TrimRight(cfg.BaseURL, "/")
			if !strings.HasPrefix(base, "https://") &&
				!strings.HasPrefix(base, "http://localhost") &&
				!strings.HasPrefix(base, "http://127.0.0.1") &&
				!strings.HasPrefix(base, "http://[::1]") {
				return usageErr(fmt.Errorf("refusing to send credentials to insecure base URL %q; use an https origin", base))
			}

			ctx, cancel := boundCtx(cmd.Context(), flags)
			defer cancel()

			body, _ := json.Marshal(map[string]string{"email": email, "password": password})
			loginURL := base + "/api/auth/login"
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
				Token  string `json:"token"`
				Detail string `json:"detail"`
				User   struct {
					Email string `json:"email"`
				} `json:"user"`
			}
			_ = json.NewDecoder(resp.Body).Decode(&parsed)

			if resp.StatusCode/100 != 2 {
				msg := parsed.Detail
				if msg == "" {
					msg = http.StatusText(resp.StatusCode)
				}
				return &cliError{code: loginExitCode(resp.StatusCode), err: fmt.Errorf("login failed (HTTP %d): %s", resp.StatusCode, msg)}
			}
			if parsed.Token == "" {
				return &cliError{code: 5, err: fmt.Errorf("login succeeded (HTTP %d) but no token was returned", resp.StatusCode)}
			}

			expiry := loginJWTExpiry(parsed.Token)
			cfg.AuthHeaderVal = ""
			if err := cfg.SaveTokens("", "", parsed.Token, "", expiry); err != nil {
				return configErr(fmt.Errorf("saving token: %w", err))
			}

			who := parsed.User.Email
			if who == "" {
				who = email
			}

			// Warn if an exported JIVO_ECOM_TOKEN will shadow the token we just
			// saved (env wins over config in AuthHeader resolution).
			if os.Getenv("JIVO_ECOM_TOKEN") != "" {
				fmt.Fprintln(cmd.ErrOrStderr(), "warning: JIVO_ECOM_TOKEN is set and will override the token just saved; unset it to use the stored login")
			}

			if flags.asJSON {
				return printJSONFiltered(cmd.OutOrStdout(), map[string]any{
					"logged_in":   true,
					"email":       who,
					"config_path": cfg.Path,
					"expires_at":  loginExpiryString(expiry),
				}, flags)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Logged in as %s — token saved to %s\n", who, cfg.Path)
			if !expiry.IsZero() {
				fmt.Fprintf(cmd.OutOrStdout(), "Token expires %s (re-run 'auth login' to refresh).\n", expiry.Local().Format("2006-01-02 15:04 MST"))
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&email, "email", "", "Account email (or set JIVO_ECOM_EMAIL)")
	cmd.Flags().StringVar(&password, "password", "", "Account password (prefer JIVO_ECOM_PASSWORD or --password-stdin; --password is visible in ps/history)")
	cmd.Flags().BoolVar(&passwordStdin, "password-stdin", false, "Read the password from standard input")
	return cmd
}

// loginExitCode maps an HTTP status from the login endpoint to the CLI's typed
// exit-code palette (see helpers.go): 4=auth, 3=not-found, 7=rate-limit, 5=api.
func loginExitCode(status int) int {
	switch {
	case status == 401 || status == 403:
		return 4
	case status == 404:
		return 3
	case status == 429:
		return 7
	default:
		return 5
	}
}

// loginJWTExpiry best-effort decodes the `exp` claim from a JWT. Returns the
// zero time when the token is opaque or unparseable — callers treat zero as
// "no known expiry".
func loginJWTExpiry(token string) time.Time {
	parts := strings.Split(token, ".")
	if len(parts) < 2 {
		return time.Time{}
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		// Some encoders include padding; fall back to std URL encoding.
		payload, err = base64.URLEncoding.DecodeString(parts[1])
		if err != nil {
			return time.Time{}
		}
	}
	var claims struct {
		Exp int64 `json:"exp"`
	}
	if err := json.Unmarshal(payload, &claims); err != nil || claims.Exp == 0 {
		return time.Time{}
	}
	return time.Unix(claims.Exp, 0)
}

func loginExpiryString(t time.Time) string {
	if t.IsZero() {
		return ""
	}
	return t.UTC().Format(time.RFC3339)
}

// redactLoginEmail masks the local part of an email for verify/dry-run output
// so a real address never lands in captured logs.
func redactLoginEmail(email string) string {
	if email == "" {
		return "<unset>"
	}
	at := strings.IndexByte(email, '@')
	if at < 0 {
		return "***"
	}
	if at <= 1 {
		return "***" + email[at:]
	}
	return email[:1] + "***" + email[at:]
}
