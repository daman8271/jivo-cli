// Package config loads dsr connection profiles from ~/.dsr/config.toml (optional)
// with environment-variable overrides, and a small .env loader so the tool works
// with a gitignored .env next to the binary — matching the other JIVO CLIs.
//
// Two targets live in one profile: the SQL Server database (the primary,
// direct-read path over DSR_V6) and the portal (the secondary HTTP path).
package config

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// Profile is a single named target: SQL Server creds + portal creds.
type Profile struct {
	// SQL Server (primary path)
	Host     string
	Port     int
	User     string
	Password string
	Database string
	Encrypt  string // "disable" (default), "true", "false"

	// Portal (secondary HTTP path)
	PortalURL      string
	PortalUser     string
	PortalPassword string
}

// Defaults for the known JIVO DSR server. Credentials are never defaulted —
// they must come from env / .env / config so nothing secret lives in the binary.
const (
	defaultHost      = "103.89.45.75"
	defaultPort      = 1433
	defaultDatabase  = "DSR_V6"
	defaultEncrypt   = "disable"
	defaultPortalURL = "http://103.89.45.75:90"
)

// LoadDotEnv sets environment variables from the first .env file found, without
// overriding anything already present in the real environment. Search order:
// $DSR_ENV_FILE, ./.env, <exe dir>/.env, ~/.dsr/.env.
func LoadDotEnv() {
	var paths []string
	if p := os.Getenv("DSR_ENV_FILE"); p != "" {
		paths = append(paths, p)
	}
	paths = append(paths, ".env")
	if exe, err := os.Executable(); err == nil {
		paths = append(paths, filepath.Join(filepath.Dir(exe), ".env"))
	}
	if home, err := os.UserHomeDir(); err == nil {
		paths = append(paths, filepath.Join(home, ".dsr", ".env"))
	}
	for _, p := range paths {
		loadDotEnvFile(p)
	}
}

func loadDotEnvFile(path string) {
	f, err := os.Open(path)
	if err != nil {
		return
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		line = strings.TrimPrefix(line, "export ")
		eq := strings.IndexByte(line, '=')
		if eq < 0 {
			continue
		}
		key := strings.TrimSpace(line[:eq])
		val := strings.TrimSpace(line[eq+1:])
		val = strings.Trim(val, `"'`)
		if key == "" {
			continue
		}
		if _, ok := os.LookupEnv(key); !ok {
			os.Setenv(key, val)
		}
	}
}

// Config is unused-but-reserved for future named profiles; today the profile is
// assembled entirely from environment variables (populated by LoadDotEnv).
type Config struct{}

// Load is a no-op placeholder kept for parity with the other CLIs' shape.
func Load() (*Config, error) { return &Config{}, nil }

// Path reports where a config file would live (for messages).
func Path() string {
	if p := os.Getenv("DSR_ENV_FILE"); p != "" {
		return p
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".dsr", ".env")
}

// Resolve builds the effective profile from environment variables plus defaults.
// It fails closed on the database user: no silent default login.
func (c *Config) Resolve(name string) (Profile, error) {
	var p Profile
	p.Host = firstNonEmpty(os.Getenv("DSR_HOST"), defaultHost)
	p.User = os.Getenv("DSR_USER")
	p.Password = os.Getenv("DSR_PASSWORD")
	p.Database = firstNonEmpty(os.Getenv("DSR_DATABASE"), defaultDatabase)
	p.Encrypt = firstNonEmpty(os.Getenv("DSR_ENCRYPT"), defaultEncrypt)
	p.Port = defaultPort
	if v := os.Getenv("DSR_PORT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			p.Port = n
		}
	}

	p.PortalURL = firstNonEmpty(os.Getenv("DSR_PORTAL_URL"), defaultPortalURL)
	p.PortalUser = os.Getenv("DSR_PORTAL_USER")
	p.PortalPassword = os.Getenv("DSR_PORTAL_PASSWORD")

	if p.User == "" {
		return Profile{}, fmt.Errorf(
			"no database user configured: set DSR_USER (and DSR_PASSWORD) in the environment or a .env file " +
				"next to the binary. Use a dedicated read-only login where possible")
	}
	return p, nil
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}
