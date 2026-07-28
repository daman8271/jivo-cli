// Package config loads SAP B1 Service Layer connection settings.
//
// Precedence (highest wins): CLI flag > environment variable > .env file > built-in default.
// The password is never logged, printed, or written anywhere by this package.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/joho/godotenv"

	"sapb1/internal/errs"
)

// Config holds everything needed to talk to a SAP B1 Service Layer instance.
type Config struct {
	Host      string
	Port      int
	CompanyDB string
	User      string
	Password  string
	Insecure  bool
	Timeout   int // seconds
	JSON      bool
	CSV       bool
}

// Defaults.
const (
	DefaultPort    = 50000
	DefaultTimeout = 30
)

// Flags captures the values the caller pulled from CLI flags (global persistent
// flags on the root command). A flag is only applied if Changed is true, so an
// unset flag never clobbers an env var or .env value with a zero value.
type Flags struct {
	Host        string
	HostSet     bool
	Port        int
	PortSet     bool
	Company     string
	CompanySet  bool
	User        string
	UserSet     bool
	Insecure    bool
	InsecureSet bool
	Timeout     int
	TimeoutSet  bool
	JSON        bool
	CSV         bool
}

// Load builds a Config by layering: built-in defaults, then .env file (if present),
// then real process environment variables, then explicit CLI flags.
//
// It does not fail if CompanyDB, User, or Password are blank — callers that need
// those must check and produce a clear, actionable error (see Validate helpers).
func Load(f Flags) (*Config, error) {
	// Load .env from the current directory if present. godotenv.Load does NOT
	// override variables already set in the real process environment, which is
	// the precedence we want (env var > .env file).
	_ = godotenv.Load()

	cfg := &Config{
		Host:      os.Getenv("SAPB1_HOST"),
		Port:      DefaultPort,
		CompanyDB: os.Getenv("SAPB1_COMPANYDB"),
		User:      os.Getenv("SAPB1_USER"),
		Password:  os.Getenv("SAPB1_PASSWORD"),
		Insecure:  false,
		Timeout:   DefaultTimeout,
	}

	if v := os.Getenv("SAPB1_PORT"); v != "" {
		if p, err := strconv.Atoi(v); err == nil {
			cfg.Port = p
		} else {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf("invalid SAPB1_PORT %q: must be a number", v)}
		}
	}

	if v := os.Getenv("SAPB1_INSECURE"); v != "" {
		b, err := strconv.ParseBool(v)
		if err != nil {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf("invalid SAPB1_INSECURE %q: must be true/false", v)}
		}
		cfg.Insecure = b
	}

	if v := os.Getenv("SAPB1_TIMEOUT"); v != "" {
		if t, err := strconv.Atoi(v); err == nil {
			cfg.Timeout = t
		} else {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf("invalid SAPB1_TIMEOUT %q: must be a number of seconds", v)}
		}
	}

	// Flags win over everything else, but only if explicitly set.
	if f.HostSet {
		cfg.Host = f.Host
	}
	if f.PortSet {
		cfg.Port = f.Port
	}
	if f.CompanySet {
		cfg.CompanyDB = f.Company
	}
	if f.UserSet {
		cfg.User = f.User
	}
	if f.InsecureSet {
		cfg.Insecure = f.Insecure
	}
	if f.TimeoutSet {
		cfg.Timeout = f.Timeout
	}
	cfg.JSON = f.JSON
	cfg.CSV = f.CSV

	cfg.Host = strings.TrimSpace(cfg.Host)
	cfg.CompanyDB = strings.TrimSpace(cfg.CompanyDB)
	cfg.User = strings.TrimSpace(cfg.User)

	return cfg, nil
}

// BaseURL returns the Service Layer root, e.g. https://host:50000/b1s/v1/.
func (c *Config) BaseURL() string {
	return fmt.Sprintf("https://%s:%d/b1s/v1/", c.Host, c.Port)
}

// HostPort returns "host:port" for use in network-reachability messages.
func (c *Config) HostPort() string {
	return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

// MaskedPassword returns a fixed mask if a password is set, or "(not set)".
// It never returns the real password.
func (c *Config) MaskedPassword() string {
	if c.Password == "" {
		return "(not set)"
	}
	return "****"
}

// ValidateConnection checks that the fields required to make ANY request
// (host, user, password) are present. CompanyDB is checked separately since
// some commands (like `doctor` prior to login) can still report partial status.
func (c *Config) ValidateConnection() error {
	var missing []string
	if c.Host == "" {
		missing = append(missing, "SAPB1_HOST")
	}
	if c.User == "" {
		missing = append(missing, "SAPB1_USER")
	}
	if c.Password == "" {
		missing = append(missing, "SAPB1_PASSWORD")
	}
	if len(missing) > 0 {
		return &errs.ConfigError{Msg: fmt.Sprintf("missing required config: %s — set them in .env or pass the matching flag", strings.Join(missing, ", "))}
	}
	return nil
}

// ValidateCompanyDB checks CompanyDB is set, with the exact guidance requested
// for this project.
func (c *Config) ValidateCompanyDB() error {
	if c.CompanyDB == "" {
		return &errs.ConfigError{Msg: "company database not set — set SAPB1_COMPANYDB in .env or pass --company. Ask your SAP admin for the CompanyDB name"}
	}
	return nil
}

// SessionCachePath returns ~/.sapb1-session.json.
func SessionCachePath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("cannot determine home directory: %w", err)
	}
	return filepath.Join(home, ".sapb1-session.json"), nil
}
