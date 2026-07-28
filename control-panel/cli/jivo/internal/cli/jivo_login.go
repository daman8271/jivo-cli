// Hand-authored, durable across `generate --force` (novel file: the generator
// never emits internal/cli/jivo_login.go, so regeneration preserves it). The
// `auth` command group is registered from root.go via a single AddCommand line
// that `--force`'s AST merge preserves.
//
// The Jivo Control Panel uses Django session auth (no token API). This command
// ports the verified recon login flow (recon/login.sh) to Go:
//  1. GET  /accounts/login/ with a cookie jar -> csrftoken cookie + a
//     <input name="csrfmiddlewaretoken"> value in the HTML.
//  2. POST /accounts/login/ (form-urlencoded) with that token, Referer/Origin
//     headers -> HTTP 302 + a fresh sessionid and csrftoken cookie.
//  3. Persist sessionid + csrftoken to the config file (mode 0600) and store
//     the derived request headers (Cookie / X-CSRFToken / X-Requested-With) in
//     the [headers] table so every generated read command authenticates.
//
// The password is never written to disk or logged; only the session tokens are
// persisted.

package cli

import (
	"bufio"
	"context"
	"fmt"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"jivo-pp-cli/internal/client"
	"jivo-pp-cli/internal/cliutil"
	"jivo-pp-cli/internal/config"

	"github.com/pelletier/go-toml/v2"
	"github.com/spf13/cobra"
)

const (
	loginPath       = "/accounts/login/"
	defaultEnvFile  = "software/.env" // resolved under $HOME
	defaultUsername = "preshit"
)

var csrfInputRe = regexp.MustCompile(`name="csrfmiddlewaretoken"\s+value="([^"]*)"`)

// sessionConfigFile is the on-disk shape written by `auth login`. It is a
// superset of the generated config.Config (which only reads base_url + the
// [headers] table); the extra sessionid/csrftoken scalars are ignored by the
// generated loader (go-toml skips unknown keys) and exist so `auth status`
// and re-login can read the raw tokens back.
type sessionConfigFile struct {
	BaseURL   string            `toml:"base_url"`
	SessionID string            `toml:"sessionid"`
	CSRFToken string            `toml:"csrftoken"`
	Headers   map[string]string `toml:"headers"`
}

// newAuthCmd is the hand-wired auth group for Django session login. Registered
// in root.go: rootCmd.AddCommand(newAuthCmd(flags)).
func newAuthCmd(flags *rootFlags) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "auth",
		Short: "Manage the Jivo Control Panel Django session",
		Long: strings.TrimSpace(`
Manage authentication against the Jivo Group Control Panel.

The Control Panel uses a Django session cookie (there is no token API), so
'auth login' performs the browser login flow once and stores the resulting
session in the config file. Every other command then authenticates
automatically. Re-run 'auth login' if a command reports the session expired.`),
	}
	cmd.AddCommand(newAuthLoginCmd(flags))
	cmd.AddCommand(newAuthStatusCmd(flags))
	cmd.AddCommand(newAuthLogoutCmd(flags))
	return cmd
}

// newAuthLoginCmd performs the Django session login and persists the session.
func newAuthLoginCmd(flags *rootFlags) *cobra.Command {
	var username, password, envFile string
	cmd := &cobra.Command{
		Use:   "login",
		Short: "Log in with username + password and store the Django session (read-only)",
		Long: strings.TrimSpace(`
Log in to the Jivo Control Panel and store the Django session cookie.

Credential resolution order:
  username: --username  ->  JIVO_USER  ->  <env-file> JIVO_USER
  password: --password  ->  JIVO_PASS  ->  <env-file> JIVO_PASS

The env file defaults to ~/software/.env (KEY=VALUE lines). The password is
never written to disk or logged; only the session tokens are persisted, with
mode 0600.`),
		Example: strings.TrimSpace(`
  # Use the shared ~/software/.env credentials
  jivo auth login

  # Or pass them explicitly (env var preferred; --password shows in ps/history)
  JIVO_USER=preshit JIVO_PASS=secret jivo auth login`),
		Annotations: map[string]string{
			// Login is a network side effect, never an MCP read tool.
			"mcp:hidden": "true",
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load(flags.configPath)
			if err != nil {
				return configErr(err)
			}
			base := strings.TrimRight(cfg.BaseURL, "/")

			// Resolve credentials: flags -> env -> env file.
			envFilePath := envFile
			if envFilePath == "" {
				home, _ := os.UserHomeDir()
				envFilePath = filepath.Join(home, defaultEnvFile)
			}
			fileVars := loadEnvFile(envFilePath)
			if username == "" {
				username = firstNonEmpty(os.Getenv("JIVO_USER"), fileVars["JIVO_USER"], defaultUsername)
			}
			if password == "" {
				password = firstNonEmpty(os.Getenv("JIVO_PASS"), fileVars["JIVO_PASS"])
			}
			// Honor an env-file base URL override if the config still holds the default.
			if v := firstNonEmpty(os.Getenv("JIVO_BASE"), fileVars["JIVO_BASE"]); v != "" {
				base = strings.TrimRight(v, "/")
			}

			// Verify/dry-run: never touch the network or the live production system.
			if dryRunOK(flags) || cliutil.IsVerifyEnv() {
				fmt.Fprintf(cmd.OutOrStdout(), "would log in to %s as %s\n", base, redactUser(username))
				return nil
			}

			if password == "" {
				return usageErr(fmt.Errorf("a password is required (use --password, JIVO_PASS, or %s)", envFilePath))
			}
			if !client.AllowInsecureBase(base) {
				return usageErr(fmt.Errorf("refusing to send credentials to %q over plain HTTP; only https, the internal host %s, or loopback are allowed", base, client.InternalHost))
			}

			ctx, cancel := boundCtx(cmd.Context(), flags)
			defer cancel()

			sessionID, csrfToken, err := djangoLogin(ctx, flags.timeout, base, username, password)
			if err != nil {
				return authErr(err)
			}

			if err := writeSessionConfig(cfg.Path, base, sessionID, csrfToken); err != nil {
				return configErr(fmt.Errorf("saving session: %w", err))
			}

			if flags.asJSON {
				return printJSONFiltered(cmd.OutOrStdout(), map[string]any{
					"logged_in":   true,
					"username":    username,
					"base_url":    base,
					"config_path": cfg.Path,
				}, flags)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Logged in as %s — session saved to %s\n", username, cfg.Path)
			return nil
		},
	}
	cmd.Flags().StringVar(&username, "username", "", "Control Panel username (or set JIVO_USER)")
	cmd.Flags().StringVar(&password, "password", "", "Control Panel password (prefer JIVO_PASS or the env file; --password is visible in ps/history)")
	cmd.Flags().StringVar(&envFile, "env-file", "", "Path to a KEY=VALUE credentials file (default ~/software/.env)")
	return cmd
}

// newAuthStatusCmd reports whether a session is stored, without hitting the network.
func newAuthStatusCmd(flags *rootFlags) *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: "Show whether a Django session is stored",
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load(flags.configPath)
			if err != nil {
				return configErr(err)
			}
			hasSession := cfg.Headers["Cookie"] != ""
			w := cmd.OutOrStdout()
			if flags.asJSON {
				out := map[string]any{
					"authenticated": hasSession,
					"base_url":      cfg.BaseURL,
					"config":        cfg.Path,
				}
				if err := printJSONFiltered(w, out, flags); err != nil {
					return err
				}
				if !hasSession {
					return authErr(fmt.Errorf("no session stored"))
				}
				return nil
			}
			if !hasSession {
				fmt.Fprintln(w, "Not authenticated")
				fmt.Fprintln(w, "  Run: jivo auth login")
				return authErr(fmt.Errorf("no session stored"))
			}
			fmt.Fprintln(w, "Session stored (not verified)")
			fmt.Fprintf(w, "  Base:   %s\n", cfg.BaseURL)
			fmt.Fprintf(w, "  Config: %s\n", cfg.Path)
			return nil
		},
	}
}

// newAuthLogoutCmd removes the stored session.
func newAuthLogoutCmd(flags *rootFlags) *cobra.Command {
	return &cobra.Command{
		Use:   "logout",
		Short: "Remove the stored Django session",
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load(flags.configPath)
			if err != nil {
				return configErr(err)
			}
			if err := os.Remove(cfg.Path); err != nil && !os.IsNotExist(err) {
				return configErr(fmt.Errorf("removing %s: %w", cfg.Path, err))
			}
			if flags.asJSON {
				return printJSONFiltered(cmd.OutOrStdout(), map[string]any{"cleared": true}, flags)
			}
			fmt.Fprintln(cmd.OutOrStdout(), "Session cleared.")
			return nil
		},
	}
}

// djangoLogin runs the two-step Django login and returns the sessionid +
// csrftoken cookies from the authenticated jar. Success is HTTP 302 with a
// sessionid cookie set.
func djangoLogin(ctx context.Context, timeout time.Duration, base, username, password string) (string, string, error) {
	jar, err := cookiejar.New(nil)
	if err != nil {
		return "", "", fmt.Errorf("creating cookie jar: %w", err)
	}
	httpClient := &http.Client{
		Timeout: timeout,
		Jar:     jar,
		// Stop at the 302 so we can read its Set-Cookie; the jar is still
		// updated from the redirect response before this fires.
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}
	loginURL := base + loginPath

	// Step 1: GET the login page for the csrfmiddlewaretoken + csrftoken cookie.
	getReq, err := http.NewRequestWithContext(ctx, http.MethodGet, loginURL, nil)
	if err != nil {
		return "", "", fmt.Errorf("building GET %s: %w", loginURL, err)
	}
	getResp, err := httpClient.Do(getReq)
	if err != nil {
		return "", "", fmt.Errorf("GET %s: %w", loginURL, err)
	}
	defer getResp.Body.Close()
	pageBytes := make([]byte, 0, 64*1024)
	buf := make([]byte, 32*1024)
	for {
		n, rerr := getResp.Body.Read(buf)
		if n > 0 {
			pageBytes = append(pageBytes, buf[:n]...)
		}
		if rerr != nil {
			break
		}
		if len(pageBytes) > 4*1024*1024 {
			break
		}
	}
	m := csrfInputRe.FindSubmatch(pageBytes)
	if len(m) < 2 {
		return "", "", fmt.Errorf("could not find csrfmiddlewaretoken on %s (HTTP %d) — is the base URL correct?", loginURL, getResp.StatusCode)
	}
	formToken := string(m[1])

	// Step 2: POST the credentials form-urlencoded.
	form := url.Values{}
	form.Set("csrfmiddlewaretoken", formToken)
	form.Set("next", "")
	form.Set("username", username)
	form.Set("password", password)
	postReq, err := http.NewRequestWithContext(ctx, http.MethodPost, loginURL, strings.NewReader(form.Encode()))
	if err != nil {
		return "", "", fmt.Errorf("building POST %s: %w", loginURL, err)
	}
	postReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	postReq.Header.Set("Referer", loginURL)
	postReq.Header.Set("Origin", base)
	postResp, err := httpClient.Do(postReq)
	if err != nil {
		return "", "", fmt.Errorf("POST %s: %w", loginURL, err)
	}
	defer postResp.Body.Close()

	sessionID, csrfToken := cookiesFromJar(jar, base)
	if postResp.StatusCode != http.StatusFound || sessionID == "" {
		return "", "", fmt.Errorf("login failed (HTTP %d) — check username/password", postResp.StatusCode)
	}
	if csrfToken == "" {
		// Fall back to the pre-login token if the server did not rotate it.
		csrfToken = formToken
	}
	return sessionID, csrfToken, nil
}

// cookiesFromJar extracts the sessionid + csrftoken cookies for base.
func cookiesFromJar(jar *cookiejar.Jar, base string) (sessionID, csrfToken string) {
	u, err := url.Parse(base)
	if err != nil {
		return "", ""
	}
	for _, c := range jar.Cookies(u) {
		switch c.Name {
		case "sessionid":
			sessionID = c.Value
		case "csrftoken":
			csrfToken = c.Value
		}
	}
	return sessionID, csrfToken
}

// writeSessionConfig persists the session + derived headers to the config file
// (mode 0600, dir 0700). The [headers] table is what the generated client
// applies to every request.
func writeSessionConfig(path, base, sessionID, csrfToken string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return fmt.Errorf("creating config dir: %w", err)
	}
	out := sessionConfigFile{
		BaseURL:   base,
		SessionID: sessionID,
		CSRFToken: csrfToken,
		Headers:   client.SessionHeaders(sessionID, csrfToken),
	}
	data, err := toml.Marshal(out)
	if err != nil {
		return fmt.Errorf("marshaling config: %w", err)
	}
	return os.WriteFile(path, data, 0o600)
}

// loadEnvFile parses a KEY=VALUE file (comments with #, optional surrounding
// quotes). Returns an empty map when the file is missing.
func loadEnvFile(path string) map[string]string {
	out := map[string]string{}
	f, err := os.Open(path)
	if err != nil {
		return out
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		line = strings.TrimPrefix(line, "export ")
		k, v, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		k = strings.TrimSpace(k)
		v = strings.TrimSpace(v)
		v = strings.Trim(v, `"'`)
		if k != "" {
			out[k] = v
		}
	}
	return out
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if strings.TrimSpace(v) != "" {
			return v
		}
	}
	return ""
}

// redactUser masks a username for verify/dry-run output.
func redactUser(u string) string {
	if u == "" {
		return "<unset>"
	}
	if len(u) <= 2 {
		return "***"
	}
	return u[:1] + "***"
}
