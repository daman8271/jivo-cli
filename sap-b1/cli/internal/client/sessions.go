package client

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// SessionStore shares Service Layer sessions between the Clients of ONE
// process.
//
// Why it exists: a CLI invocation is a process that makes one request, so the
// on-disk cache is enough — the next process finds the session on disk. The MCP
// server over HTTP is the opposite: it handles tool calls CONCURRENTLY, and
// agents batch them. Every call built its own Client, every one of those found
// no session on disk (because none had finished logging in yet), and every one
// of them opened its own SAP session. Measured: 30 concurrent calls cost 29
// Logins. Each of those sessions is a licensed Service Layer slot held for its
// full ~30-minute TTL, and the MCP path never logs out.
//
// The store fixes that at the root: sessions are keyed by the same identity
// tuple as the disk cache (host, port, companyDB, user), and the per-identity
// lock means only ONE goroutine ever performs the Login while the rest wait and
// then reuse its session. Alternating between companies still keeps one session
// each, because the company is part of the key — a session is bound to the
// CompanyDB it logged into and must never be replayed against another.
//
// The zero value is not usable; call NewSessionStore.
type SessionStore struct {
	mu      sync.Mutex
	entries map[string]*sessionEntry
}

// NewSessionStore returns an empty store, ready for concurrent use.
func NewSessionStore() *SessionStore {
	return &SessionStore{entries: map[string]*sessionEntry{}}
}

// sessionEntry is one identity's shared session plus the lock that serialises
// logging in for it.
type sessionEntry struct {
	mu         sync.Mutex
	b1Session  string
	routeID    string
	loggedInAt time.Time
}

// entryFor returns the (possibly new) entry for an identity key.
func (s *SessionStore) entryFor(key string) *sessionEntry {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.entries == nil {
		s.entries = map[string]*sessionEntry{}
	}
	e, ok := s.entries[key]
	if !ok {
		e = &sessionEntry{}
		s.entries[key] = e
	}
	return e
}

// identity is the connection tuple a session is bound to. It is the same tuple
// the on-disk cache is keyed by, so the two layers can never disagree about
// which session belongs to which company.
func (c *Client) identity() string {
	return fmt.Sprintf("%s:%d:%s:%s", c.cfg.Host, c.cfg.Port, c.cfg.CompanyDB, c.cfg.User)
}

// adopt copies a shared session into this Client.
func (c *Client) adopt(e *sessionEntry) {
	c.b1Session = e.b1Session
	c.routeID = e.routeID
	c.loggedInAt = e.loggedInAt
}

// publish copies this Client's session into the shared entry.
func (c *Client) publish(e *sessionEntry) {
	e.b1Session = c.b1Session
	e.routeID = c.routeID
	e.loggedInAt = c.loggedInAt
}

// ensureSession guarantees the Client holds a session, at a cost of at most ONE
// Login per identity even when many goroutines arrive at once.
//
// Order of preference: a session already in memory on this Client, then the
// process-shared store, then the on-disk cache, then a fresh Login.
func (c *Client) ensureSession(ctx context.Context) error {
	if c.b1Session != "" {
		return nil
	}
	if c.sessions == nil {
		// No sharing (plain CLI use): disk cache, then Login.
		if c.LoadCachedSession() {
			return nil
		}
		return c.Login(ctx)
	}

	e := c.sessions.entryFor(c.identity())
	e.mu.Lock()
	defer e.mu.Unlock()

	// Another goroutine may have logged in while we waited for the lock.
	if e.b1Session != "" {
		c.adopt(e)
		return nil
	}
	if c.LoadCachedSession() {
		c.publish(e)
		return nil
	}
	if err := c.loginLocked(ctx); err != nil {
		return err
	}
	c.publish(e)
	return nil
}

// refreshSession re-establishes a session after the Service Layer rejected the
// one we used (HTTP 401). stale is the session value that was rejected: if the
// shared entry has already moved past it, another goroutine has re-logged-in
// and we simply take its session instead of opening a second one. So N
// concurrent calls hitting an expired session cost one Login, not N.
func (c *Client) refreshSession(ctx context.Context, stale string) error {
	if c.sessions == nil {
		return c.Login(ctx)
	}
	e := c.sessions.entryFor(c.identity())
	e.mu.Lock()
	defer e.mu.Unlock()

	if e.b1Session != "" && e.b1Session != stale {
		c.adopt(e)
		return nil
	}
	if err := c.loginLocked(ctx); err != nil {
		e.clear()
		return err
	}
	c.publish(e)
	return nil
}

// clear forgets a shared session.
func (e *sessionEntry) clear() {
	e.b1Session = ""
	e.routeID = ""
	e.loggedInAt = time.Time{}
}

// forget drops this identity's shared session (used by Logout).
func (c *Client) forgetShared() {
	if c.sessions == nil {
		return
	}
	e := c.sessions.entryFor(c.identity())
	e.mu.Lock()
	defer e.mu.Unlock()
	e.clear()
}
