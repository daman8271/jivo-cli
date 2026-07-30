// Package config locates and loads the HANA credentials for hana-sql.
//
// Precedence, highest first:
//
//  1. process environment (HANA_HOST / HANA_PORT / HANA_USER / HANA_PASSWORD)
//  2. the env file (-env flag, else $HANA_ENV, else the nearest
//     connections/hana.env walking up from the working directory)
//  3. built-in default for the port only (30015)
//
// The process environment wins so a container can be configured with plain env
// vars and no file. Nothing in this package ever prints the password: use
// MaskedPassword for display and Scrub before emitting any string that might
// have picked it up (a driver error, an audit line).
package config

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// DefaultPort is HANA's SQL port for the SAP B1 instance (tenant NDB).
const DefaultPort = "30015"

// Config is one resolved HANA login.
type Config struct {
	Host     string
	Port     string
	User     string
	Password string

	// EnvFile is the file the values came from ("" when the process
	// environment supplied everything).
	EnvFile string
}

// Find returns the env-file path to read: the explicit flag if given, else
// $HANA_ENV, else the nearest connections/hana.env walking up from the working
// directory. The last-resort relative path matches the historical behaviour so
// the error message stays recognisable.
func Find(explicit string) string {
	if explicit != "" {
		return explicit
	}
	if v := os.Getenv("HANA_ENV"); v != "" {
		return v
	}
	dir, _ := os.Getwd()
	for {
		cand := filepath.Join(dir, "connections", "hana.env")
		if _, err := os.Stat(cand); err == nil {
			return cand
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "connections/hana.env"
		}
		dir = parent
	}
}

// ParseEnvFile reads a KEY=VALUE file, ignoring blanks and # comments.
func ParseEnvFile(path string) (map[string]string, error) {
	m := map[string]string{}
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if kv := strings.SplitN(line, "=", 2); len(kv) == 2 {
			m[strings.TrimSpace(kv[0])] = strings.TrimSpace(kv[1])
		}
	}
	return m, sc.Err()
}

// Load resolves a Config from the env file at path plus the process
// environment. A missing or unreadable file is only an error when the process
// environment does not already supply host, user and password.
func Load(path string) (*Config, error) {
	vals, fileErr := ParseEnvFile(path)
	if fileErr != nil {
		vals = map[string]string{}
	}

	get := func(key string) string {
		if v := strings.TrimSpace(os.Getenv(key)); v != "" {
			return v
		}
		return strings.TrimSpace(vals[key])
	}

	c := &Config{
		Host:     get("HANA_HOST"),
		Port:     get("HANA_PORT"),
		User:     get("HANA_USER"),
		Password: get("HANA_PASSWORD"),
	}
	if fileErr == nil {
		c.EnvFile = path
	}
	if c.Port == "" {
		c.Port = DefaultPort
	}

	if fileErr != nil && (c.Host == "" || c.User == "" || c.Password == "") {
		return nil, fmt.Errorf("cannot read credentials at %s: %w", path, fileErr)
	}
	if err := c.Validate(); err != nil {
		return nil, err
	}
	return c, nil
}

// Validate reports the first missing field, by name only.
func (c *Config) Validate() error {
	switch {
	case c.Host == "":
		return fmt.Errorf("HANA_HOST is not set (env file or process environment)")
	case c.User == "":
		return fmt.Errorf("HANA_USER is not set (env file or process environment)")
	case c.Password == "":
		return fmt.Errorf("HANA_PASSWORD is not set (env file or process environment)")
	}
	return nil
}

// Addr is the host:port the driver dials.
func (c *Config) Addr() string { return c.Host + ":" + c.Port }

// MaskedPassword is what may be shown to a user or an AI client.
func (c *Config) MaskedPassword() string {
	if c.Password == "" {
		return "(not set)"
	}
	return "**** (set)"
}

// Scrub removes the password value from s. Every string that leaves the process
// — an error from the driver, an audit line, a doctor field — goes through it,
// so a credential can never be echoed back even if some layer below embeds it.
func (c *Config) Scrub(s string) string {
	if c == nil || len(c.Password) < 3 {
		return s
	}
	return strings.ReplaceAll(s, c.Password, "****")
}

// ScrubErr is Scrub for an error value; it returns "" for a nil error.
func (c *Config) ScrubErr(err error) string {
	if err == nil {
		return ""
	}
	return c.Scrub(err.Error())
}
