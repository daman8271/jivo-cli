package main

import (
	"fmt"
	"os"
	"regexp"
	"strings"

	"github.com/spf13/cobra"
)

func newAuthCmd(app *App) *cobra.Command {
	auth := &cobra.Command{
		Use:   "auth",
		Short: "Credential management (local, no network)",
	}

	imp := &cobra.Command{
		Use:   "import <curlfile>",
		Short: "Extract creds from a captured cURL into the shared blinkit-cli config",
		Args:  cobra.ExactArgs(1),
		// No auth needed to import creds, so skip the root PreRunE.
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error { return nil },
		RunE: func(cmd *cobra.Command, args []string) error {
			return runAuthImport(args[0])
		},
	}
	auth.AddCommand(imp)

	// login (email-OTP) is intentionally DEFERRED: the request-OTP path is not
	// verified, and we do not invent auth. Use orchestrate/blinkit-login.sh.
	auth.AddCommand(&cobra.Command{
		Use:               "login",
		Short:             "[DEFERRED] email-OTP login — use orchestrate/blinkit-login.sh for now",
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error { return nil },
		RunE: func(cmd *cobra.Command, args []string) error {
			return fmt.Errorf("auth login is not wired (request-OTP path unconfirmed) — refresh the token with orchestrate/blinkit-login.sh, then `auth import`")
		},
	})
	return auth
}

func runAuthImport(path string) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read %s: %w", path, err)
	}
	s := string(raw)
	cfg := loadConfigFile()
	if cfg.Base == "" {
		cfg.Base = defaultBase
	}
	if v := curlHeader(s, "x-api-key"); v != "" {
		cfg.APIKey = v
	}
	if v := curlHeader(s, "token"); v != "" {
		cfg.Token = v
	}
	if v := curlHeader(s, "x-entity-id"); v != "" {
		cfg.EntityID = v
	}
	if v := curlHeader(s, "x-entity-type"); v != "" {
		cfg.EntityType = v
	}
	if cfg.EntityType == "" {
		cfg.EntityType = "manufacturer"
	}
	if cfg.APIKey == "" || cfg.Token == "" || cfg.EntityID == "" {
		return fmt.Errorf("could not extract all creds (api-key=%v token=%v entity-id=%v) from %s",
			cfg.APIKey != "", cfg.Token != "", cfg.EntityID != "", path)
	}
	if err := cfg.save(); err != nil {
		return fmt.Errorf("save config: %w", err)
	}
	fmt.Printf("✓ imported creds to %s (entity=%s)\n", configPath(), cfg.EntityID)
	return nil
}

// curlHeader extracts the value of a `-H 'name: value'` cURL header
// (case-insensitive name). Matches `token:` specifically, not `access_token:`.
func curlHeader(curl, name string) string {
	re := regexp.MustCompile(`(?i)-H\s+'` + regexp.QuoteMeta(name) + `:\s*([^']*)'`)
	m := re.FindStringSubmatch(curl)
	if len(m) == 2 {
		return strings.TrimSpace(m[1])
	}
	return ""
}
