// Hand-authored login for JIVO EXIM. NOT generated — survives `generate --force`
// on a warm dir, but a clean regen (rm + generate) drops it: after any clean
// regen, restore this file and re-add `cmd.AddCommand(newAuthLoginCmd(flags))`
// in auth.go (see .printing-press-patches/auth-login.md). Ported from the
// sibling build's jivo_login.go and adapted to the exim-pp-cli module.
//
// READ-ONLY VOW: this file contains the ONLY sanctioned non-GET request in the
// whole CLI — the auth token exchange, which hits only /account/login/ and
// creates no business data. It uses its OWN http.Client and never touches
// internal/client, which hard-blocks non-GET methods. Do not add data-mutating
// calls here.
package cli

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"exim-pp-cli/internal/config"

	"github.com/spf13/cobra"
)

func newAuthLoginCmd(flags *rootFlags) *cobra.Command {
	var email string
	var passwordStdin bool
	cmd := &cobra.Command{
		Use:   "login",
		Short: "Log in to EXIM (email + password) and store the JWT for read-only access",
		Long: strings.Trim(`
Exchange an EXIM email + password for a JWT access/refresh token and store it in
the CLI config. This is the only command that sends a non-GET request, and it
only calls /account/login/ (authentication, not a data write).

Credential sources (first found wins): --email / --password-stdin flags,
then env EXIM_EMAIL / EXIM_PASSWORD, then ~/jivogpt/.env.

  EXIM_EMAIL=you@exim.in EXIM_PASSWORD='***' exim-pp-cli auth login
  printf '%s' '***' | exim-pp-cli auth login --email you@exim.in --password-stdin
  exim-pp-cli auth login   # uses ~/jivogpt/.env if present
`, "\n"),
		Example: "  exim-pp-cli auth login",
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load(flags.configPath)
			if err != nil {
				return configErr(err)
			}
			base := strings.TrimRight(cfg.BaseURL, "/")
			if !strings.HasPrefix(base, "https://") {
				return fmt.Errorf("refusing to log in over non-HTTPS base URL %q", base)
			}
			fileEmail, filePass := credsFromEnvFile()
			if email == "" {
				email = os.Getenv("EXIM_EMAIL")
			}
			if email == "" {
				email = fileEmail
			}
			if email == "" {
				return errors.New("email required: pass --email, set EXIM_EMAIL, or add it to ~/jivogpt/.env")
			}
			var password string
			if passwordStdin {
				b, rerr := io.ReadAll(os.Stdin)
				if rerr != nil {
					return fmt.Errorf("reading password from stdin: %w", rerr)
				}
				password = strings.TrimRight(string(b), "\r\n")
			} else {
				password = os.Getenv("EXIM_PASSWORD")
				if password == "" {
					password = filePass
				}
			}
			if password == "" {
				return errors.New("password required: use --password-stdin, set EXIM_PASSWORD, or add it to ~/jivogpt/.env")
			}

			access, refresh, name, userEmail, err := eximLogin(cmd.Context(), base, email, password)
			if err != nil {
				return err
			}
			if err := cfg.SaveTokens("", "", access, refresh, jwtExpiry(access)); err != nil {
				return configErr(fmt.Errorf("saving tokens: %w", err))
			}
			if flags.asJSON {
				return printJSONFiltered(cmd.OutOrStdout(), map[string]any{
					"logged_in": true, "user": name, "email": userEmail,
					"expires": jwtExpiry(access).Format(time.RFC3339),
				}, flags)
			}
			fmt.Fprintf(cmd.OutOrStdout(), "Logged in as %s (%s). Read-only token stored.\n", name, userEmail)
			return nil
		},
	}
	cmd.Flags().StringVar(&email, "email", "", "EXIM login email (or env EXIM_EMAIL, or ~/jivogpt/.env)")
	cmd.Flags().BoolVar(&passwordStdin, "password-stdin", false, "Read password from stdin (or env EXIM_PASSWORD, or ~/jivogpt/.env)")
	return cmd
}

// credsFromEnvFile reads EXIM_EMAIL / EXIM_PASSWORD from the jivogpt root .env
// (the consolidated credentials file) as a convenience fallback. The file is
// gitignored; the password is never written anywhere by this CLI.
func credsFromEnvFile() (email, password string) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", ""
	}
	b, err := os.ReadFile(home + "/jivogpt/.env")
	if err != nil {
		return "", ""
	}
	for _, line := range strings.Split(string(b), "\n") {
		line = strings.TrimSpace(line)
		if v, ok := strings.CutPrefix(line, "EXIM_EMAIL="); ok {
			email = v
		} else if v, ok := strings.CutPrefix(line, "EXIM_PASSWORD="); ok {
			password = v
		}
	}
	return email, password
}

// eximLogin performs the token exchange. This is the sole non-GET request in the
// CLI; it deliberately uses its own http.Client and only ever calls /account/login/.
func eximLogin(ctx context.Context, base, email, password string) (access, refresh, name, userEmail string, err error) {
	body, _ := json.Marshal(map[string]string{"email": email, "password": password})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, base+"/account/login/", bytes.NewReader(body))
	if err != nil {
		return "", "", "", "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := (&http.Client{Timeout: 30 * time.Second}).Do(req)
	if err != nil {
		return "", "", "", "", fmt.Errorf("login request failed: %w", err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return "", "", "", "", fmt.Errorf("login failed (HTTP %d): check email/password", resp.StatusCode)
	}
	var lr struct {
		Access  string `json:"access"`
		Refresh string `json:"refresh"`
		Name    string `json:"name"`
		Email   string `json:"email"`
	}
	if err := json.Unmarshal(raw, &lr); err != nil {
		return "", "", "", "", fmt.Errorf("parsing login response: %w", err)
	}
	if lr.Access == "" {
		return "", "", "", "", errors.New("login response missing access token")
	}
	return lr.Access, lr.Refresh, lr.Name, lr.Email, nil
}

// jwtExpiry reads the `exp` claim from a JWT; falls back to now+23h.
func jwtExpiry(token string) time.Time {
	parts := strings.Split(token, ".")
	if len(parts) == 3 {
		if seg, err := base64.RawURLEncoding.DecodeString(parts[1]); err == nil {
			var claims struct {
				Exp int64 `json:"exp"`
			}
			if json.Unmarshal(seg, &claims) == nil && claims.Exp > 0 {
				return time.Unix(claims.Exp, 0)
			}
		}
	}
	return time.Now().Add(23 * time.Hour)
}
