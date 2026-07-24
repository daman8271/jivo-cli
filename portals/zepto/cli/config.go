package main

import (
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
)

// Config holds everything needed to authenticate against the Zepto seller
// portal. Zepto uses a raw JWT bearer token (NO "Bearer " prefix, sent in the
// `authorization` header) and the SAME token authorizes every backend host.
// Secrets are NEVER hardcoded — they come from the environment or the cached
// config file written by the existing zepto-cli `auth import` / zepto-login.sh.
type Config struct {
	Base    string `json:"base"`     // inherited: https://fcc.zepto.co.in/api/v1
	AdsBase string `json:"ads_base"` // inherited: https://fcc.zepto.co.in/ads-bff/api/v1
	JWT     string `json:"jwt"`      // raw token, no "Bearer " prefix
	BrandID string `json:"brand_id"` // ads brand_id (default: Jivo)
}

const (
	defaultBase    = "https://fcc.zepto.co.in/api/v1"
	defaultBrandID = "b3550d5d-fc71-47b0-af4f-f221f909b936" // Jivo
	defaultManufID = "946950b7-1ce2-4bdf-a7c4-37499e3f5f34" // Jivo Wellness Pvt. Ltd.
)

// Backend host roots. One JWT authorizes all of them (verified). Section
// commands build "<host><path>" using these; the path in the vault already
// carries its /api/v1, /vms/api/v1, /ads-bff/api/v1 … prefix.
const (
	hostFCC     = "https://fcc.zepto.co.in"
	hostAuth    = "https://auth-backend.zepto.co.in"
	hostFin     = "https://financenew.zepto.co.in"
	hostSCP     = "https://scpfin.zepto.co.in"
	hostOnboard = "https://brands-onboarding.zepto.co.in"
	hostAdsPlat = "https://ads-platform.zepto.co.in"
	hostPartner = "https://partner.zepto.co.in"
)

// resolveConfig builds a Config from env vars first, then falls back to the
// cached config file for any field left unset. Env always wins.
func resolveConfig() (Config, error) {
	c := loadConfigFile() // best-effort; zero value if absent

	if v := os.Getenv("ZEPTO_BASE"); v != "" {
		c.Base = v
	}
	if v := os.Getenv("ZEPTO_ADS_BASE"); v != "" {
		c.AdsBase = v
	}
	if v := os.Getenv("ZEPTO_JWT"); v != "" {
		c.JWT = v
	}
	if v := os.Getenv("ZEPTO_BRAND_ID"); v != "" {
		c.BrandID = v
	}

	if c.Base == "" {
		c.Base = defaultBase
	}
	if c.BrandID == "" {
		c.BrandID = defaultBrandID
	}

	if c.JWT == "" {
		return c, fmt.Errorf("missing credentials: [ZEPTO_JWT] — refresh the daily token with `bash ~/ecomcliauto/orchestrate/zepto-login.sh` or `zepto-portal auth import <curlfile>`")
	}
	return c, nil
}

// hostRoot returns scheme://host for a URL, falling back to def if it doesn't
// parse. Used so an inherited/overridden ZEPTO_BASE re-points the FCC host too.
func hostRoot(raw, def string) string {
	u, err := url.Parse(raw)
	if err != nil || u.Scheme == "" || u.Host == "" {
		return def
	}
	return u.Scheme + "://" + u.Host
}

// configPath resolves to the EXISTING shared zepto-cli config so this CLI
// inherits the live JWT written by zepto-login.sh. The subdir name stays
// "zepto-cli" on purpose (NOT "zepto-portal").
// On macOS: ~/Library/Application Support/zepto-cli/config.json.
func configPath() string {
	dir, err := os.UserConfigDir()
	if err != nil || dir == "" {
		dir = filepath.Join(os.Getenv("HOME"), ".config")
	}
	return filepath.Join(dir, "zepto-cli", "config.json")
}

func loadConfigFile() Config {
	var c Config
	b, err := os.ReadFile(configPath())
	if err != nil {
		return c
	}
	_ = json.Unmarshal(b, &c)
	return c
}

// save writes the config to disk with 0600 perms (it holds the JWT).
func (c Config) save() error {
	p := configPath()
	if err := os.MkdirAll(filepath.Dir(p), 0o700); err != nil {
		return err
	}
	b, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(p, b, 0o600)
}
