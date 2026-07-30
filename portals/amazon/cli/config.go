package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Config holds the consumed Seller Central session. Per G9 the CLI NEVER mints
// a session — it reads the cookie jar the existing ~/ecomcliauto login already
// produced. Nothing here is a secret we own; it is a pointer to the human's jar.
type Config struct {
	Cookie   string // assembled "name=value; ..." from the jar (Seller Central)
	JarPath  string
	Merchant string // non-secret, for display
}

// scCookie is one entry of the Playwright/Chrome cookie-jar JSON.
type scCookie struct {
	Name   string `json:"name"`
	Value  string `json:"value"`
	Domain string `json:"domain"`
}

// defaultJarPath is where the ecomcliauto Seller Central login lands.
func defaultJarPath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, "ecomcliauto", "auth", "login", "out", "amazon-mp.cookies.json")
}

// loadConfig assembles the Seller Central Cookie header from the jar on disk.
// AMAZON_SC_COOKIE_JAR overrides the path. Returns a Config with an empty
// Cookie (not an error) if the jar is absent, so offline commands still work.
func loadConfig() Config {
	jp := os.Getenv("AMAZON_SC_COOKIE_JAR")
	if jp == "" {
		jp = defaultJarPath()
	}
	cfg := Config{JarPath: jp}
	b, err := os.ReadFile(jp)
	if err != nil {
		return cfg
	}
	var cookies []scCookie
	if err := json.Unmarshal(b, &cookies); err != nil {
		return cfg
	}
	var parts []string
	for _, c := range cookies {
		if !strings.Contains(c.Domain, "amazon") {
			continue
		}
		if c.Name == "" || c.Value == "" {
			continue
		}
		parts = append(parts, c.Name+"="+c.Value)
	}
	cfg.Cookie = strings.Join(parts, "; ")
	return cfg
}

// requireSession errors with actionable guidance if no jar is loaded.
func (c Config) requireSession() error {
	if c.Cookie == "" {
		return fmt.Errorf("no Seller Central session found at %s\n"+
			"  This CLI consumes the existing ~/ecomcliauto login (it never logs in itself).\n"+
			"  Set AMAZON_SC_COOKIE_JAR to a cookie-jar JSON, or run the ecomcliauto Amazon login first.", c.JarPath)
	}
	return nil
}
