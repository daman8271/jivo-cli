package client

import (
	"os"
	"runtime"
	"testing"
	"time"

	"sapb1/internal/config"
)

func TestSessionCacheRoundTrip(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	if runtime.GOOS != "windows" {
		t.Setenv("USERPROFILE", tmp) // harmless on unix, keeps os.UserHomeDir happy everywhere
	}

	if _, ok := loadSessionCache(); ok {
		t.Fatal("expected no cached session in a fresh temp HOME")
	}

	sc := &sessionCache{
		Host:       "10.0.0.1",
		Port:       50000,
		CompanyDB:  "TESTDB",
		User:       "tester",
		B1Session:  "abc-123",
		RouteID:    "route-1",
		LoggedInAt: time.Now(),
	}
	if err := saveSessionCache(sc); err != nil {
		t.Fatalf("saveSessionCache: %v", err)
	}

	path, err := config.SessionCachePath()
	if err != nil {
		t.Fatalf("sessionCachePathForTest: %v", err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatalf("stat session cache file: %v", err)
	}
	if perm := info.Mode().Perm(); perm != 0o600 {
		t.Errorf("session cache file mode = %o, want 0600", perm)
	}

	loaded, ok := loadSessionCache()
	if !ok {
		t.Fatal("expected cached session to load after save")
	}
	if loaded.B1Session != "abc-123" || loaded.RouteID != "route-1" || loaded.CompanyDB != "TESTDB" {
		t.Errorf("loaded session mismatch: %+v", loaded)
	}

	if err := clearSessionCache(); err != nil {
		t.Fatalf("clearSessionCache: %v", err)
	}
	if _, ok := loadSessionCache(); ok {
		t.Fatal("expected no cached session after clear")
	}
}

func TestClearSessionCacheOnMissingFileIsNotError(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	if err := clearSessionCache(); err != nil {
		t.Errorf("clearSessionCache on a missing file should be a no-op, got: %v", err)
	}
}
