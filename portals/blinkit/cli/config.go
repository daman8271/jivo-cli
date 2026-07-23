package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Config holds everything needed to authenticate against PartnersBiz.
// Secrets are NEVER hardcoded — they come from the environment or the cached
// config file written by the existing blinkit-cli `auth import`.
type Config struct {
	Base       string `json:"base"`
	APIKey     string `json:"api_key"`     // x-api-key (app-level)
	Token      string `json:"token"`       // session token, v2::<uuid>; sent as token + access_token
	EntityID   string `json:"entity_id"`   // x-entity-id (1117 = Jivo Wellness)
	EntityType string `json:"entity_type"` // x-entity-type (manufacturer)
}

const defaultBase = "https://www.partnersbiz.com"

// resolveConfig builds a Config from env vars first, then falls back to the
// cached config file for any field left unset. Env always wins.
func resolveConfig() (Config, error) {
	c := loadConfigFile() // best-effort; zero value if absent

	if v := os.Getenv("BLINKIT_BASE"); v != "" {
		c.Base = v
	}
	if v := os.Getenv("BLINKIT_API_KEY"); v != "" {
		c.APIKey = v
	}
	if v := os.Getenv("BLINKIT_TOKEN"); v != "" {
		c.Token = v
	}
	if v := os.Getenv("BLINKIT_ENTITY_ID"); v != "" {
		c.EntityID = v
	}
	if v := os.Getenv("BLINKIT_ENTITY_TYPE"); v != "" {
		c.EntityType = v
	}

	if c.Base == "" {
		c.Base = defaultBase
	}
	if c.EntityType == "" {
		c.EntityType = "manufacturer"
	}

	var missing []string
	if c.APIKey == "" {
		missing = append(missing, "BLINKIT_API_KEY")
	}
	if c.Token == "" {
		missing = append(missing, "BLINKIT_TOKEN")
	}
	if c.EntityID == "" {
		missing = append(missing, "BLINKIT_ENTITY_ID")
	}
	if len(missing) > 0 {
		return c, fmt.Errorf("missing credentials: %v — set the env vars, run `blinkit-partner auth import <curlfile>`, or refresh with orchestrate/blinkit-login.sh", missing)
	}
	return c, nil
}

// configPath resolves to the EXISTING shared blinkit-cli config so this CLI
// inherits the live token/api-key/entity. The subdir name stays "blinkit-cli"
// on purpose (NOT "blinkit-partner"). On macOS this is
// ~/Library/Application Support/blinkit-cli/config.json.
func configPath() string {
	dir, err := os.UserConfigDir()
	if err != nil || dir == "" {
		dir = filepath.Join(os.Getenv("HOME"), ".config")
	}
	return filepath.Join(dir, "blinkit-cli", "config.json")
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

// save writes the config to disk with 0600 perms (it holds a session token).
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
