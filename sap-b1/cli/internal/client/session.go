package client

import (
	"encoding/json"
	"os"
	"time"

	"sapb1/internal/config"
)

// sessionCache is what gets persisted to the per-identity cache file
// ~/.sapb1-session-<companydb>-<hash>.json. It is scoped to a specific
// host+port+companyDB+user tuple so a cached session is never reused against a
// different SAP connection: the tuple is both what picks the file AND what is
// re-checked on load (see Client.LoadCachedSession).
type sessionCache struct {
	Host       string    `json:"host"`
	Port       int       `json:"port"`
	CompanyDB  string    `json:"company_db"`
	User       string    `json:"user"`
	B1Session  string    `json:"b1session"`
	RouteID    string    `json:"route_id"`
	LoggedInAt time.Time `json:"logged_in_at"`
}

// loadSessionCache reads the cache file for one connection identity, if any.
// It never errors on a missing/unreadable/corrupt file — callers just treat
// that as "no session" and log in again.
func loadSessionCache(host string, port int, companyDB, user string) (*sessionCache, bool) {
	path, err := config.SessionCachePathFor(host, port, companyDB, user)
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

// saveSessionCache writes the cache file for the identity carried by sc, with
// 0600 permissions, creating or truncating it as needed.
func saveSessionCache(sc *sessionCache) error {
	path, err := config.SessionCachePathFor(sc.Host, sc.Port, sc.CompanyDB, sc.User)
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

// clearSessionCache removes one identity's cache file. Missing file is not an
// error.
func clearSessionCache(host string, port int, companyDB, user string) error {
	path, err := config.SessionCachePathFor(host, port, companyDB, user)
	if err != nil {
		return err
	}
	err = os.Remove(path)
	if err != nil && !os.IsNotExist(err) {
		return err
	}
	return nil
}
