// Package config loads postsql connection profiles from
// ~/.postsql/config.toml, with environment-variable overrides.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	"github.com/BurntSushi/toml"
)

// Profile is a single named PostgreSQL connection target.
type Profile struct {
	Host     string `toml:"host"`
	Port     int    `toml:"port"`
	User     string `toml:"user"`
	Password string `toml:"password"`
	Database string `toml:"database"`
}

// Config is the on-disk configuration: a set of named profiles plus a default.
type Config struct {
	Default  string             `toml:"default"`
	Profiles map[string]Profile `toml:"profiles"`
}

// Path returns the config file location (~/.postsql/config.toml).
func Path() string {
	if p := os.Getenv("POSTSQL_CONFIG"); p != "" {
		return p
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".postsql", "config.toml")
}

// Load reads the config file if present. A missing file is not an error:
// profiles can also come entirely from environment variables.
func Load() (*Config, error) {
	c := &Config{Profiles: map[string]Profile{}}
	b, err := os.ReadFile(Path())
	if err != nil {
		if os.IsNotExist(err) {
			return c, nil
		}
		return nil, err
	}
	if err := toml.Unmarshal(b, c); err != nil {
		return nil, fmt.Errorf("parsing %s: %w", Path(), err)
	}
	if c.Profiles == nil {
		c.Profiles = map[string]Profile{}
	}
	return c, nil
}

// Resolve selects a profile by name (falling back to POSTSQL_PROFILE, then the
// configured default), then applies environment overrides and sane defaults.
func (c *Config) Resolve(name string) (Profile, error) {
	if name == "" {
		name = os.Getenv("POSTSQL_PROFILE")
	}
	if name == "" {
		name = c.Default
	}

	var p Profile
	if name != "" {
		pp, ok := c.Profiles[name]
		if !ok && len(c.Profiles) > 0 {
			return Profile{}, fmt.Errorf("profile %q not found in %s", name, Path())
		}
		p = pp
	}

	// Environment overrides (POSTSQL_* wins, then libpq-style PG* as fallback).
	p.Host = firstNonEmpty(os.Getenv("POSTSQL_HOST"), os.Getenv("PGHOST"), p.Host)
	p.User = firstNonEmpty(os.Getenv("POSTSQL_USER"), os.Getenv("PGUSER"), p.User)
	p.Password = firstNonEmpty(os.Getenv("POSTSQL_PASSWORD"), os.Getenv("PGPASSWORD"), p.Password)
	p.Database = firstNonEmpty(os.Getenv("POSTSQL_DATABASE"), os.Getenv("PGDATABASE"), p.Database)
	if v := firstNonEmpty(os.Getenv("POSTSQL_PORT"), os.Getenv("PGPORT")); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			p.Port = n
		}
	}

	// Defaults for benign fields.
	if p.Host == "" {
		p.Host = "127.0.0.1"
	}
	if p.Port == 0 {
		p.Port = 5432
	}
	if p.Database == "" {
		p.Database = "postgres"
	}

	// Fail closed on the connecting role: do NOT silently default to the
	// "postgres" superuser. A superuser connection has an unrestricted read
	// blast radius (server-side file reads, RLS bypass, all databases) that the
	// READ ONLY transaction cannot constrain. Require an explicit, ideally
	// least-privilege (NOSUPERUSER, NOBYPASSRLS, SELECT-only) login.
	if p.User == "" {
		return Profile{}, fmt.Errorf(
			"no database user configured: set it in a profile in %s, or via POSTSQL_USER / PGUSER "+
				"(use a dedicated read-only, non-superuser role — not 'postgres')", Path())
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
