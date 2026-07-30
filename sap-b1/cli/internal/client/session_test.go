package client

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"
	"time"

	"sapb1/internal/config"
)

// testIdentity is the connection identity used by the session-cache tests.
const (
	tHost      = "10.0.0.1"
	tPort      = 50000
	tCompanyDB = "TESTDB"
	tUser      = "tester"
)

func TestSessionCacheRoundTrip(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	if runtime.GOOS != "windows" {
		t.Setenv("USERPROFILE", tmp) // harmless on unix, keeps os.UserHomeDir happy everywhere
	}

	if _, ok := loadSessionCache(tHost, tPort, tCompanyDB, tUser); ok {
		t.Fatal("expected no cached session in a fresh temp HOME")
	}

	sc := &sessionCache{
		Host:       tHost,
		Port:       tPort,
		CompanyDB:  tCompanyDB,
		User:       tUser,
		B1Session:  "abc-123",
		RouteID:    "route-1",
		LoggedInAt: time.Now(),
	}
	if err := saveSessionCache(sc); err != nil {
		t.Fatalf("saveSessionCache: %v", err)
	}

	path, err := config.SessionCachePathFor(tHost, tPort, tCompanyDB, tUser)
	if err != nil {
		t.Fatalf("SessionCachePathFor: %v", err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatalf("stat session cache file: %v", err)
	}
	if perm := info.Mode().Perm(); perm != 0o600 {
		t.Errorf("session cache file mode = %o, want 0600", perm)
	}

	loaded, ok := loadSessionCache(tHost, tPort, tCompanyDB, tUser)
	if !ok {
		t.Fatal("expected cached session to load after save")
	}
	if loaded.B1Session != "abc-123" || loaded.RouteID != "route-1" || loaded.CompanyDB != tCompanyDB {
		t.Errorf("loaded session mismatch: %+v", loaded)
	}

	if err := clearSessionCache(tHost, tPort, tCompanyDB, tUser); err != nil {
		t.Fatalf("clearSessionCache: %v", err)
	}
	if _, ok := loadSessionCache(tHost, tPort, tCompanyDB, tUser); ok {
		t.Fatal("expected no cached session after clear")
	}
}

func TestClearSessionCacheOnMissingFileIsNotError(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	if err := clearSessionCache(tHost, tPort, tCompanyDB, tUser); err != nil {
		t.Errorf("clearSessionCache on a missing file should be a no-op, got: %v", err)
	}
}

// TestSessionCacheIsPerCompany is the session-slot half of the wrong-company
// story: three companies on the same host/user must land in three different
// files, so alternating between them does not overwrite (and therefore does
// not force a fresh Login on) the others. Saving Mart must leave Oil's cached
// session exactly as it was.
func TestSessionCacheIsPerCompany(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	if runtime.GOOS != "windows" {
		t.Setenv("USERPROFILE", tmp)
	}

	companies := []string{"JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB"}
	for i, db := range companies {
		sc := &sessionCache{
			Host: tHost, Port: tPort, CompanyDB: db, User: tUser,
			B1Session:  "session-" + db,
			LoggedInAt: time.Now(),
		}
		if err := saveSessionCache(sc); err != nil {
			t.Fatalf("saveSessionCache(%s): %v", db, err)
		}
		// Every company saved so far must still be readable and unchanged.
		for _, prev := range companies[:i+1] {
			got, ok := loadSessionCache(tHost, tPort, prev, tUser)
			if !ok {
				t.Fatalf("after saving %s, %s's cached session disappeared — the cache is not per-company", db, prev)
			}
			if want := "session-" + prev; got.B1Session != want {
				t.Fatalf("after saving %s, %s's session = %q, want %q", db, prev, got.B1Session, want)
			}
		}
	}

	// And the paths really are distinct files.
	seen := map[string]string{}
	for _, db := range companies {
		p, err := config.SessionCachePathFor(tHost, tPort, db, tUser)
		if err != nil {
			t.Fatal(err)
		}
		if other, dup := seen[p]; dup {
			t.Fatalf("companies %s and %s share the cache file %s", other, db, p)
		}
		seen[p] = db
	}

	// Clearing one company must not clear the others.
	if err := clearSessionCache(tHost, tPort, "JIVO_MART_HANADB", tUser); err != nil {
		t.Fatalf("clearSessionCache: %v", err)
	}
	if _, ok := loadSessionCache(tHost, tPort, "JIVO_MART_HANADB", tUser); ok {
		t.Error("Mart session survived its own clear")
	}
	if _, ok := loadSessionCache(tHost, tPort, "JIVO_OIL_HANADB", tUser); !ok {
		t.Error("clearing Mart also cleared Oil — cache files are not independent")
	}
}

// TestLoadCachedSessionRejectsOtherCompany pins the load-bearing guard in
// Client.LoadCachedSession: even if a cache file for a DIFFERENT company is
// handed to a client (here by writing Oil's identity into Mart's file), the
// session must be refused rather than replayed. This is the check that stops
// an Oil session from answering a Beverages question.
func TestLoadCachedSessionRejectsOtherCompany(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	if runtime.GOOS != "windows" {
		t.Setenv("USERPROFILE", tmp)
	}

	// A well-formed session cache belonging to Oil...
	oil := &sessionCache{
		Host: tHost, Port: tPort, CompanyDB: "JIVO_OIL_HANADB", User: tUser,
		B1Session: "oil-session", LoggedInAt: time.Now(),
	}
	if err := saveSessionCache(oil); err != nil {
		t.Fatal(err)
	}

	// ...an Oil client happily uses it.
	oilClient := New(&config.Config{Host: tHost, Port: tPort, CompanyDB: "JIVO_OIL_HANADB", User: tUser, Password: "x", Timeout: 5})
	if !oilClient.LoadCachedSession() {
		t.Fatal("Oil client should load Oil's cached session")
	}

	// ...but a Mart client must not, even when the file it would read has been
	// planted with Oil's payload.
	martPath, err := config.SessionCachePathFor(tHost, tPort, "JIVO_MART_HANADB", tUser)
	if err != nil {
		t.Fatal(err)
	}
	oilPath, err := config.SessionCachePathFor(tHost, tPort, "JIVO_OIL_HANADB", tUser)
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(oilPath)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(martPath, raw, 0o600); err != nil {
		t.Fatal(err)
	}

	martClient := New(&config.Config{Host: tHost, Port: tPort, CompanyDB: "JIVO_MART_HANADB", User: tUser, Password: "x", Timeout: 5})
	if martClient.LoadCachedSession() {
		t.Fatal("a Mart client replayed an Oil session — the four-field guard in LoadCachedSession is broken")
	}
	if martClient.HasSession() {
		t.Fatal("Mart client holds a session it must not have")
	}
}

// TestLegacySessionFileIsIgnored — the old shared ~/.sapb1-session.json is
// simply not read any more. Worst case that costs one extra Login; it must
// never be mistaken for a valid session.
func TestLegacySessionFileIsIgnored(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	if runtime.GOOS != "windows" {
		t.Setenv("USERPROFILE", tmp)
	}
	legacy := filepath.Join(tmp, ".sapb1-session.json")
	body := `{"host":"10.0.0.1","port":50000,"company_db":"TESTDB","user":"tester","b1session":"legacy"}`
	if err := os.WriteFile(legacy, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, ok := loadSessionCache(tHost, tPort, tCompanyDB, tUser); ok {
		t.Error("legacy shared session file was loaded; it must be ignored")
	}
}
