package client

import (
	"encoding/json"
	"os"
	"time"

	"sapb1/internal/config"
)

// sessionCache is what gets persisted to ~/.sapb1-session.json. It is scoped
// to a specific host+port+companyDB+user tuple so a cached session is never
// reused against a different SAP connection.
type sessionCache struct {
	Host       string    `json:"host"`
	Port       int       `json:"port"`
	CompanyDB  string    `json:"company_db"`
	User       string    `json:"user"`
	B1Session  string    `json:"b1session"`
	RouteID    string    `json:"route_id"`
	LoggedInAt time.Time `json:"logged_in_at"`
}

// loadSessionCache reads the cache file, if any. It never errors on a
// missing/unreadable/corrupt file — callers just treat that as "no session".
func loadSessionCache() (*sessionCache, bool) {
	path, err := config.SessionCachePath()
	if err != nil {
		return nil, false
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, false
	}
	var sc sessionCache
	if err := json.Unmarshal(data, &sc); err != nil {
		return nil, false
	}
	if sc.B1Session == "" {
		return nil, false
	}
	return &sc, true
}

// saveSessionCache writes the cache file with 0600 permissions, creating or
// truncating it as needed.
func saveSessionCache(sc *sessionCache) error {
	path, err := config.SessionCachePath()
	if err != nil {
		return err
	}
	data, err := json.MarshalIndent(sc, "", "  ")
	if err != nil {
		return err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := f.Write(data); err != nil {
		return err
	}
	return f.Chmod(0o600)
}

// clearSessionCache removes the cache file. Missing file is not an error.
func clearSessionCache() error {
	path, err := config.SessionCachePath()
	if err != nil {
		return err
	}
	err = os.Remove(path)
	if err != nil && !os.IsNotExist(err) {
		return err
	}
	return nil
}
