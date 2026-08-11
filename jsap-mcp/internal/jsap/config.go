// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — configuration.

package jsap

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// defaultBaseURL is JSAP's documented base URL — the same default the Python
// CLI carries in jsap/config.py:31. It is not a secret; the credentials are.
const defaultBaseURL = "http://103.89.45.75:5001"

// defaultUserID is the account every gateway caller authenticates as. Single
// shared identity, exactly like the other JIVO backends: every tool call
// inherits this user's JSAP permissions.
const defaultUserID = 68

// Companies maps JSAP's company ids to their names.
//
// READ THIS BEFORE TRUSTING A COMPANY ID: in JSAP company 2 is JIVO BEVERAGE
// and there is no Mart, while in factory-cli company 2 is Mart. An id alone is
// therefore ambiguous across JIVO systems, so every tool response echoes the
// company NAME back and never the bare id.
var Companies = map[int]string{
	1: "JIVO OIL",
	2: "JIVO BEVERAGE",
}

// CompanyName resolves an id to its JSAP company name, or a clearly-marked
// unknown so a wrong id can never be silently attributed to a real company.
func CompanyName(id int) string {
	if name, ok := Companies[id]; ok {
		return name
	}
	return fmt.Sprintf("UNKNOWN COMPANY ID %d", id)
}

// Config is everything the client needs. Credentials are read from the
// environment (or a .env beside the binary) and are never logged or returned
// in a tool result.
type Config struct {
	BaseURL  string
	Username string
	Password string
	UserID   int
}

// LoadConfig reads JSAP_URL / JSAP_USERNAME / JSAP_PASSWORD / JSAP_USER_ID from
// the process environment, falling back to a .env file in the working directory
// and next to the binary. That is the same shape the deployed sapb1 container
// uses (working_dir /srv, ./env/<name>/.env bind-mounted to /srv/.env:ro), so a
// jsap service can be wired identically without extra plumbing.
func LoadConfig() Config {
	fileEnv := loadDotenv()
	pick := func(key string) string {
		if v := strings.TrimSpace(os.Getenv(key)); v != "" {
			return v
		}
		return strings.TrimSpace(fileEnv[key])
	}

	cfg := Config{
		BaseURL:  strings.TrimRight(pick("JSAP_URL"), "/"),
		Username: pick("JSAP_USERNAME"),
		Password: pick("JSAP_PASSWORD"),
		UserID:   defaultUserID,
	}
	if cfg.BaseURL == "" {
		cfg.BaseURL = defaultBaseURL
	}
	if v := pick("JSAP_USER_ID"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			cfg.UserID = n
		}
	}
	return cfg
}

// RequireCreds reports a missing-credential error naming only the variables and
// the file they belong in — never a value. RULE 3: credentials are referred to
// by name and path, never printed.
func (c Config) RequireCreds() error {
	var missing []string
	if c.Username == "" {
		missing = append(missing, "JSAP_USERNAME")
	}
	if c.Password == "" {
		missing = append(missing, "JSAP_PASSWORD")
	}
	if len(missing) == 0 {
		return nil
	}
	return fmt.Errorf("missing %s — set them in the environment or in the .env mounted beside this binary",
		strings.Join(missing, ", "))
}

// loadDotenv parses ./.env and <dir of binary>/.env, first hit wins per key.
// A tiny KEY=VALUE parser on purpose: no dependency, and it accepts exactly the
// file shape the Python CLI already writes.
func loadDotenv() map[string]string {
	out := map[string]string{}
	var candidates []string
	if wd, err := os.Getwd(); err == nil {
		candidates = append(candidates, filepath.Join(wd, ".env"))
	}
	if exe, err := os.Executable(); err == nil {
		candidates = append(candidates, filepath.Join(filepath.Dir(exe), ".env"))
	}
	for _, path := range candidates {
		f, err := os.Open(path)
		if err != nil {
			continue
		}
		scanner := bufio.NewScanner(f)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" || strings.HasPrefix(line, "#") || !strings.Contains(line, "=") {
				continue
			}
			key, value, _ := strings.Cut(line, "=")
			key = strings.TrimSpace(key)
			value = strings.Trim(strings.TrimSpace(value), `"'`)
			if _, seen := out[key]; !seen {
				out[key] = value
			}
		}
		f.Close()
	}
	return out
}
