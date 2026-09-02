package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Config holds everything needed to talk to TankhaPay. Credentials come from the
// environment or a gitignored .env — NEVER hardcoded. One JWT authorizes all four
// backends. See ../vault/_meta/Backends-and-Environment.md.
type Config struct {
	Username string
	Password string
	BodyKey  []byte

	// Backend base URLs, keyed exactly as the endpoint generator keys them.
	Backends map[string]string
}

const (
	defBusiness = "https://business.tankhapay.com/api/"
	defMobapi   = "https://mobapi.tankhapay.com/api/"
	defTpPay    = "https://mobapi.tankhapay.com/"
	defTnd      = "https://tnd.tankhapay.com/api/"
	defBodyKey  = "0123456789abcdef"
)

// resolveConfig reads env vars first, then fills any gap from a .env file found
// near the CLI (cwd, the portal root, or the config dir). Env always wins.
func resolveConfig() (Config, error) {
	env := loadDotenvBestEffort()
	get := func(k string) string {
		if v := os.Getenv(k); v != "" {
			return v
		}
		return env[k]
	}

	key := get("TPAY_BODY_KEY")
	if key == "" {
		key = defBodyKey
	}
	c := Config{
		Username: get("TPAY_USERNAME"),
		Password: get("TPAY_PASSWORD"),
		BodyKey:  []byte(key),
		Backends: map[string]string{
			"business": orDef(get("TPAY_API"), defBusiness),
			"mobapi":   orDef(get("TPAY_EMPLOYER_API"), defMobapi),
			"tpPay":    orDef(get("TPAY_PAY_API"), defTpPay),
			"tnd":      orDef(get("TPAY_TND_API"), defTnd),
		},
	}
	if len(c.BodyKey) != 16 {
		return c, fmt.Errorf("TPAY_BODY_KEY must be 16 bytes (AES-128), got %d", len(c.BodyKey))
	}
	if c.Username == "" || c.Password == "" {
		return c, fmt.Errorf("missing credentials: set TPAY_USERNAME and TPAY_PASSWORD (env or .env)")
	}
	return c, nil
}

func orDef(v, d string) string {
	if v == "" {
		return d
	}
	return v
}

// dotenvSearchPaths returns candidate .env locations, most-specific first.
func dotenvSearchPaths() []string {
	var paths []string
	if p := os.Getenv("TANKHAPAY_ENV"); p != "" {
		paths = append(paths, p)
	}
	if wd, err := os.Getwd(); err == nil {
		paths = append(paths, filepath.Join(wd, ".env"), filepath.Join(wd, "..", ".env"))
	}
	if exe, err := os.Executable(); err == nil {
		d := filepath.Dir(exe)
		paths = append(paths, filepath.Join(d, ".env"), filepath.Join(d, "..", ".env"))
	}
	if home, err := os.UserHomeDir(); err == nil {
		paths = append(paths, filepath.Join(home, "jivo-cli", "portals", "tankhapay", ".env"))
	}
	return paths
}

// loadDotenvBestEffort parses the first .env found. Never errors: a missing file
// just yields an empty map (env vars may supply everything).
func loadDotenvBestEffort() map[string]string {
	out := map[string]string{}
	for _, p := range dotenvSearchPaths() {
		f, err := os.Open(p)
		if err != nil {
			continue
		}
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
			k := strings.TrimSpace(line[:eq])
			v := strings.TrimSpace(line[eq+1:])
			v = strings.Trim(v, `"'`)
			out[k] = v
		}
		f.Close()
		if len(out) > 0 {
			break
		}
	}
	return out
}

// ---- token cache (0600) --------------------------------------------------

type tokenCache struct {
	Token    string `json:"token"`
	CachedAt int64  `json:"cached_at"`
}

func tokenCachePath() string {
	dir, err := os.UserConfigDir()
	if err != nil || dir == "" {
		dir = filepath.Join(os.Getenv("HOME"), ".config")
	}
	return filepath.Join(dir, "tankhapay-portal", "token.json")
}

func loadCachedToken() string {
	b, err := os.ReadFile(tokenCachePath())
	if err != nil {
		return ""
	}
	var tc tokenCache
	if json.Unmarshal(b, &tc) != nil {
		return ""
	}
	return tc.Token
}

func saveCachedToken(tok string) error {
	p := tokenCachePath()
	if err := os.MkdirAll(filepath.Dir(p), 0o700); err != nil {
		return err
	}
	b, _ := json.MarshalIndent(tokenCache{Token: tok, CachedAt: time.Now().Unix()}, "", "  ")
	return os.WriteFile(p, b, 0o600)
}
