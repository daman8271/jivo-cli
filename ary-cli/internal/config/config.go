// Package config resolves ary's SQL Server connection from environment
// variables, with a small .env loader so the tool works with a gitignored .env
// next to the binary — matching the other JIVO CLIs (dsr, hana-sql, postsql).
//
// The repo is PUBLIC: no credential is ever defaulted or compiled in. The user
// must come from the environment or a .env file, and the tool fails closed.
//
// It accepts ARY_* first and falls back to DSR_* so the existing
// connections/ary.env (written for the dsr binary) works unchanged.
package config

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// Profile is one SQL Server target.
type Profile struct {
	Host     string
	Port     int
	User     string
	Password string
	Database string
	Encrypt  string // "disable" (default), "true", "false"
}

// Defaults for the known ARY server (JOY SERVICES range, same vendor as the
// SAP HANA box .222). Reachable from home — no tunnel needed.
const (
	defaultHost     = "138.252.101.118"
	defaultPort     = 1433
	defaultDatabase = "FR8HODBNEW"
	defaultEncrypt  = "disable"
)

// LoadDotEnv sets environment variables from the first .env files found, never
// overriding the real environment. Search order: $ARY_ENV_FILE, ./.env,
// ./connections/ary.env, <exe dir>/.env, <exe dir>/ary.env, ~/.ary/.env.
func LoadDotEnv() {
	var paths []string
	if p := os.Getenv("ARY_ENV_FILE"); p != "" {
		paths = append(paths, p)
	}
	paths = append(paths, ".env", "ary.env", filepath.Join("connections", "ary.env"))
	if exe, err := os.Executable(); err == nil {
		d := filepath.Dir(exe)
		paths = append(paths, filepath.Join(d, ".env"), filepath.Join(d, "ary.env"),
			filepath.Join(d, "..", "connections", "ary.env"))
	}
	if home, err := os.UserHomeDir(); err == nil {
		paths = append(paths, filepath.Join(home, ".ary", ".env"))
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
		val := strings.Trim(strings.TrimSpace(line[eq+1:]), `"'`)
		if key == "" {
			continue
		}
		if _, ok := os.LookupEnv(key); !ok {
			os.Setenv(key, val)
		}
	}
}

// Config is reserved for future named profiles; today the profile comes from
// the environment (populated by LoadDotEnv).
type Config struct{}

// Load is a placeholder kept for parity with the other JIVO CLIs' shape.
func Load() (*Config, error) { return &Config{}, nil }

// Path reports where a config file would live (for messages).
func Path() string {
	if p := os.Getenv("ARY_ENV_FILE"); p != "" {
		return p
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".ary", ".env")
}

// Resolve builds the effective profile. ARY_* wins, DSR_* is the fallback so an
// existing connections/ary.env keeps working. Fails closed on the login.
func (c *Config) Resolve(name string) (Profile, error) {
	var p Profile
	p.Host = firstNonEmpty(os.Getenv("ARY_HOST"), os.Getenv("DSR_HOST"), defaultHost)
	p.User = firstNonEmpty(os.Getenv("ARY_USER"), os.Getenv("DSR_USER"))
	p.Password = firstNonEmpty(os.Getenv("ARY_PASSWORD"), os.Getenv("DSR_PASSWORD"))
	p.Database = firstNonEmpty(os.Getenv("ARY_DATABASE"), defaultDatabase)
	p.Encrypt = firstNonEmpty(os.Getenv("ARY_ENCRYPT"), os.Getenv("DSR_ENCRYPT"), defaultEncrypt)
	p.Port = defaultPort
	for _, k := range []string{"ARY_PORT", "DSR_PORT"} {
		if v := os.Getenv(k); v != "" {
			if n, err := strconv.Atoi(v); err == nil {
				p.Port = n
				break
			}
		}
	}
	if p.User == "" {
		return Profile{}, fmt.Errorf(
			"no database user configured: set ARY_USER and ARY_PASSWORD (or DSR_USER/DSR_PASSWORD) " +
				"in the environment or a .env file next to the binary — e.g. `set -a; . connections/ary.env; set +a`. " +
				"Use a dedicated read-only login where possible")
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
