// Copyright 2026 daman8271 and contributors. Licensed under Apache-2.0. See LICENSE.
// Hand-authored: credential login for ji.jivo.in (factory.jivo.in API).

package cli

import (
	"bufio"
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"jivo-factory-pp-cli/internal/cliutil"
	"jivo-factory-pp-cli/internal/config"

	"github.com/spf13/cobra"
)

// newAuthFactoryLoginCmd implements credential login for the JIVO factory API.
//
// The API issues a SimpleJWT pair from POST /accounts/login/ with an
// {email, password} body, returning {access, refresh, token:{...}, user:{...}}.
// The access token (~25h) is then sent as `Authorization: Bearer <token>` on
// every call. Login is the ONE permitted write per the read-only law — it
// mutates nothing but a session. The password is never written to disk.
//
// Credential resolution order:
//
//	email:    --email    -> JIVO_FACTORY_EMAIL    -> ~/jivogpt/.env
//	password: --password -> JIVO_FACTORY_PASSWORD -> ~/jivogpt/.env -> --password-stdin
func newAuthFactoryLoginCmd(flags *rootFlags) *cobra.Command {
	var email, password string
	var passwordStdin bool
	cmd := &cobra.Command{
		Use:   "login",
		Short: "Log in with email + password and store the JWT access token",
		Long: strings.TrimSpace(`
Log in to ji.jivo.in (factory.jivo.in API) with your account email and password.

This exchanges your credentials at POST /accounts/login/ for a SimpleJWT access
token (~25h) and saves it to the config file (mode 0600), so every other command
authenticates automatically. Your password is never stored — only the token.

The test account has Employee access to all three companies; after login use
--company (or JIVO_FACTORY_COMPANY) to switch between JIVO_MART, JIVO_OIL and
JIVO_BEVERAGES.

Login is the only write this read-only CLI performs: it creates a session token
and mutates no JIVO data.

Credential resolution order:
  email:    --email     ->  JIVO_FACTORY_EMAIL    ->  ~/jivogpt/.env
  password: --password  ->  JIVO_FACTORY_PASSWORD ->  ~/jivogpt/.env  ->  --password-stdin`),
		Example: strings.Trim(`
  # Zero-setup: reads JIVO_FACTORY_EMAIL/PASSWORD from env or ~/jivogpt/.env
  jivo-factory-pp-cli auth login

  # Or pipe the password on stdin
  printf '%s' "$PW" | jivo-factory-pp-cli auth login --email test@jivo.in --password-stdin`, "\n"),
		Annotations: map[string]string{
			// Login is a network side effect; never a read-only MCP tool.
			"mcp:hidden": "true",
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			if email == "" {
				email = os.Getenv("JIVO_FACTORY_EMAIL")
			}
			if password == "" && !passwordStdin {
				password = os.Getenv("JIVO_FACTORY_PASSWORD")
			}
			// Fallback: the jivogpt project keeps all JIVO credentials in one
			// gitignored root .env; read it so `auth login` works zero-setup.
			if email == "" || password == "" {
				envEmail, envPassword := jivogptDotEnvCreds()
				if email == "" {
					email = envEmail
				}
				if password == "" && !passwordStdin {
					password = envPassword
				}
			}

			// Verify/dry-run: never touch the network or stdin.
			if dryRunOK(flags) || cliutil.IsVerifyEnv() {
				fmt.Fprintf(cmd.OutOrStdout(), "would log in to factory.jivo.in as %s\n", redactEmail(email))
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
				return usageErr(fmt.Errorf("both an email and a password are required (use --email/--password, JIVO_FACTORY_EMAIL/JIVO_FACTORY_PASSWORD, ~/jivogpt/.env, or --password-stdin)"))
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

			body, _ := json.Marshal(map[string]string{"email": email, "password": password})
			loginURL := base + "/accounts/login/"
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
				Access  string `json:"access"`
				Refresh string `json:"refresh"`
				Detail  string `json:"detail"`
				Message string `json:"message"`
				User    struct {
					Email     string `json:"email"`
					FullName  string `json:"full_name"`
					Companies []struct {
						CompanyCode string `json:"company_code"`
						Role        string `json:"role"`
					} `json:"companies"`
				} `json:"user"`
			}
			_ = json.NewDecoder(resp.Body).Decode(&parsed)

			if resp.StatusCode/100 != 2 || parsed.Access == "" {
				msg := parsed.Detail
				if msg == "" {
					msg = parsed.Message
				}
				if msg == "" {
					msg = fmt.Sprintf("login failed (HTTP %d)", resp.StatusCode)
				}
				return &cliError{code: 4, err: fmt.Errorf("%s", msg)}
			}

			if err := cfg.SaveTokens("", "", parsed.Access, parsed.Refresh, factoryJWTExpiry(parsed.Access)); err != nil {
				return configErr(fmt.Errorf("saving token: %w", err))
			}

			who := parsed.User.Email
			if who == "" {
				who = email
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Logged in to factory.jivo.in as %s", who)
			if n := len(parsed.User.Companies); n > 0 {
				codes := make([]string, 0, n)
				for _, c := range parsed.User.Companies {
					codes = append(codes, c.CompanyCode)
				}
				fmt.Fprintf(cmd.OutOrStdout(), " (companies: %s)", strings.Join(codes, ", "))
			}
			fmt.Fprintf(cmd.OutOrStdout(), ". Token saved to %s\n", cfg.Path)
			return nil
		},
	}
	cmd.Flags().StringVar(&email, "email", "", "Account email (or set JIVO_FACTORY_EMAIL)")
	cmd.Flags().StringVar(&password, "password", "", "Account password (prefer JIVO_FACTORY_PASSWORD or --password-stdin)")
	cmd.Flags().BoolVar(&passwordStdin, "password-stdin", false, "Read the password from standard input")
	return cmd
}

// jivogptDotEnvCreds reads JIVO_FACTORY_EMAIL / JIVO_FACTORY_PASSWORD from the
// jivogpt project's root .env (~/jivogpt/.env), the single consolidated
// credential file for all JIVO CLIs. Returns empty strings when unavailable.
func jivogptDotEnvCreds() (email, password string) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", ""
	}
	f, err := os.Open(filepath.Join(home, "jivogpt", ".env"))
	if err != nil {
		return "", ""
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		k, v, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		v = strings.Trim(strings.TrimSpace(v), `"'`)
		switch strings.TrimSpace(k) {
		case "JIVO_FACTORY_EMAIL":
			email = v
		case "JIVO_FACTORY_PASSWORD":
			password = v
		}
	}
	return email, password
}

// factoryJWTExpiry decodes the `exp` claim from a JWT access token, returning
// that time. On any decode failure it returns the zero time (unknown expiry).
func factoryJWTExpiry(token string) time.Time {
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

// redactEmail masks the local part of an email for dry-run display.
func redactEmail(e string) string {
	local, domain, ok := strings.Cut(e, "@")
	if !ok || len(local) <= 2 {
		return e
	}
	return local[:1] + strings.Repeat("*", len(local)-2) + local[len(local)-1:] + "@" + domain
}
