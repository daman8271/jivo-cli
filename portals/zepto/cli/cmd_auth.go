package main

import (
	"fmt"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// newAuthCmd manages the inherited JWT: import it from a captured cURL, or show
// its status. No network, no secrets invented — it only reads/writes the shared
// zepto-cli config file.
func newAuthCmd(app *App) *cobra.Command {
	auth := &cobra.Command{
		Use:   "auth",
		Short: "Inspect or import the Zepto JWT (shared with zepto-cli)",
		// auth needs no resolved credentials of its own.
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error { return nil },
	}
	auth.AddCommand(newAuthStatusCmd(app), newAuthImportCmd(app))
	return auth
}

func newAuthStatusCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: "Show the current JWT's identity + expiry",
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := resolveConfig()
			if err != nil {
				return err
			}
			claims, err := decodeJWT(cfg.JWT)
			if err != nil {
				return fmt.Errorf("stored token is not a readable JWT: %w", err)
			}
			now := time.Now()
			state := "valid"
			if claims.Expired(now) {
				state = "EXPIRED — " + reLoginMsg
			}
			fmt.Printf("config:  %s\n", configPath())
			fmt.Printf("email:   %s\n", claims.EmailID)
			fmt.Printf("role:    %s\n", claims.Role)
			fmt.Printf("jwt:     (%d chars)\n", len(cfg.JWT))
			fmt.Printf("expires: %s IST (%s)\n", claims.Expiry().In(istLoc).Format("2006-01-02 15:04:05"), state)
			return nil
		},
	}
}

func newAuthImportCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "import <curlfile>",
		Short: "Import the JWT from a captured cURL command (authorization header)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			b, err := os.ReadFile(args[0])
			if err != nil {
				return err
			}
			jwt := curlHeader(string(b), "authorization")
			if jwt == "" {
				return fmt.Errorf("no `authorization:` header found in %s", args[0])
			}
			jwt = strings.TrimSpace(strings.TrimPrefix(jwt, "Bearer "))
			if _, err := decodeJWT(jwt); err != nil {
				return fmt.Errorf("extracted authorization value is not a JWT: %w", err)
			}
			cfg := loadConfigFile()
			cfg.JWT = jwt
			if cfg.Base == "" {
				cfg.Base = defaultBase
			}
			if err := cfg.save(); err != nil {
				return err
			}
			fmt.Printf("✓ imported JWT into %s\n", configPath())
			return nil
		},
	}
}

// curlHeader extracts a header value from a curl command string. It matches
// -H 'name: value' / -H "name: value" / --header forms, case-insensitively on
// the header name.
func curlHeader(curl, name string) string {
	re := regexp.MustCompile(`(?i)-H\s+['"]` + regexp.QuoteMeta(name) + `:\s*([^'"]+)['"]`)
	m := re.FindStringSubmatch(curl)
	if len(m) == 2 {
		return strings.TrimSpace(m[1])
	}
	return ""
}
