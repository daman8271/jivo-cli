package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// A GST session is a cookie jar, nothing more: AuthToken, UserName, EntityRefId,
// Lang and the two TS* cookies the F5 WAF sets. One jar per registration — the
// portal has no notion of switching GSTIN inside a session — persisted so a
// second command in the same sitting does not cost another captcha.
//
// The file is a bearer token to a portal that can FILE RETURNS. It lives outside
// the repo, in the user's config dir, mode 0600.

const (
	// stagePreLogin is the jar minted by GET /services/login + the captcha GET,
	// before any credential is sent. It has to persist because the agent-friendly
	// login is two CLI invocations: one shows the captcha, the next answers it,
	// and the captcha is bound to this jar.
	stagePreLogin = "prelogin"
	// stageAuthenticated is a jar that has been through /services/authenticate.
	stageAuthenticated = "authenticated"
)

// sessionMaxAge is how long a jar is trusted after its LAST USE — an idle
// window, not a lifetime. client.go's touchSession() moves SavedAt forward on
// every successful round trip, which is what makes that true; before it did,
// this behaved as an absolute 15 minutes from login and a `--all` sitting
// (eight hand-typed captchas) had its first registrations declared dead while
// their portal sessions were still alive.
//
// UNVERIFIED (D9): the portal's real idle timeout has not been measured. 15
// minutes is the conservative guess from the SPA's behaviour class; if D9
// measures it, put the real number here. Getting this wrong is cheap in one
// direction (a needless login) and annoying in the other (a mid-run 302).
const sessionMaxAge = 15 * time.Minute

// sessionTouchInterval throttles the idle-window refresh: a snapshot makes
// hundreds of calls and there is no reason to rewrite the jar for each one.
const sessionTouchInterval = 60 * time.Second

type sessionCookie struct {
	Name     string    `json:"name"`
	Value    string    `json:"value"`
	Domain   string    `json:"domain"`
	Path     string    `json:"path"`
	Expires  time.Time `json:"expires,omitempty"`
	Secure   bool      `json:"secure,omitempty"`
	HTTPOnly bool      `json:"http_only,omitempty"`
}

type session struct {
	GSTIN    string          `json:"gstin"`
	Username string          `json:"username"`
	Stage    string          `json:"stage"`
	SavedAt  time.Time       `json:"saved_at"`
	Cookies  []sessionCookie `json:"cookies"`

	// file overrides where save() writes. It is how a pre-login jar is staged
	// beside the real session instead of on top of it — see pendingSessionPath.
	// Not serialised: the path is not part of the jar.
	file string
}

func (s *session) authenticated() bool { return s != nil && s.Stage == stageAuthenticated }

// expired reports whether the jar has been idle longer than maxAge (SavedAt is
// bumped on every successful request; see client.go touchSession).
func (s *session) expired(maxAge time.Duration) bool {
	if s == nil || s.SavedAt.IsZero() {
		return true
	}
	return time.Since(s.SavedAt) > maxAge
}

// cookiesFor returns the cookies a request to host must carry: domain-wide
// (.gst.gov.in) plus that host's own, minus anything already past its expiry.
func (s *session) cookiesFor(host string) []sessionCookie {
	if s == nil {
		return nil
	}
	now := time.Now()
	var out []sessionCookie
	for _, c := range s.Cookies {
		if !c.Expires.IsZero() && c.Expires.Before(now) {
			continue
		}
		d := strings.TrimPrefix(c.Domain, ".")
		if d == "" || host == d || strings.HasSuffix(host, "."+d) {
			out = append(out, c)
		}
	}
	return out
}

// stateDir is where sessions (and, later, captcha samples) live: the user's
// config dir, NOT the repo — operator checkouts are sparse clones and a session
// file inside one is both clutter and a leak risk. $GST_STATE_DIR overrides it.
func stateDir() string {
	if d := os.Getenv("GST_STATE_DIR"); d != "" {
		return d
	}
	d, err := os.UserConfigDir()
	if err != nil || d == "" {
		home, _ := os.UserHomeDir()
		d = filepath.Join(home, ".config")
	}
	return d
}

// sessionPath is the per-GSTIN session file. The GSTIN is sanitised down to
// [A-Z0-9] so nothing it contains can shape a path.
func sessionPath(gstin string) string {
	return filepath.Join(stateDir(), "gst-portal", "session-"+sanitiseGSTIN(gstin)+".json")
}

// pendingSessionPath is where a PRE-LOGIN jar lives while a captcha is
// outstanding. It is deliberately a different file from sessionPath: minting a
// captcha used to overwrite the working session with a pre-auth placeholder, so
// abandoning the prompt (Ctrl-C, an unreadable image, a blank line) destroyed a
// live session that had cost a captcha to get. Nothing replaces the real file
// until the portal has actually accepted the login.
func pendingSessionPath(gstin string) string {
	return filepath.Join(stateDir(), "gst-portal", "session-"+sanitiseGSTIN(gstin)+".pending.json")
}

// loadPendingSession reads the staged pre-login jar, if there is one.
func loadPendingSession(gstin string) (*session, error) {
	return loadSessionFrom(pendingSessionPath(gstin), gstin)
}

// discardPendingSession removes a staged pre-login jar (spent, or abandoned).
func discardPendingSession(gstin string) { _ = os.Remove(pendingSessionPath(gstin)) }

// sanitiseGSTIN reduces a GSTIN to [A-Z0-9] so nothing it contains can shape a
// file path. Shared by the session file and the captcha image.
func sanitiseGSTIN(gstin string) string {
	var b strings.Builder
	for _, c := range strings.ToUpper(gstin) {
		if (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') {
			b.WriteRune(c)
		}
	}
	if b.Len() == 0 {
		return "UNKNOWN"
	}
	return b.String()
}

// loadSession reads the cached jar. A missing file is a normal state, not an
// error: it just means "log in first".
func loadSession(gstin string) (*session, error) {
	return loadSessionFrom(sessionPath(gstin), gstin)
}

// loadSessionFrom reads a jar from an explicit path (the live session, or the
// staged pre-login one).
func loadSessionFrom(path, gstin string) (*session, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, errConfig("cannot read the session file for %s: %v", gstin, err)
	}
	var s session
	if err := json.Unmarshal(b, &s); err != nil {
		return nil, errConfig("session file for %s is corrupt (%v) — delete %s and log in again", gstin, err, path)
	}
	s.file = path
	// drop cookies that have already expired rather than replaying them
	now := time.Now()
	kept := s.Cookies[:0]
	for _, c := range s.Cookies {
		if !c.Expires.IsZero() && c.Expires.Before(now) {
			continue
		}
		kept = append(kept, c)
	}
	s.Cookies = kept
	return &s, nil
}

// save writes the jar 0600 inside a 0700 directory, stamping saved_at.
func (s *session) save() error {
	s.SavedAt = time.Now()
	p := s.file
	if p == "" {
		p = sessionPath(s.GSTIN)
	}
	if err := os.MkdirAll(filepath.Dir(p), 0o700); err != nil {
		return errConfig("cannot create %s: %v", filepath.Dir(p), err)
	}
	b, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(p, b, 0o600); err != nil {
		return errConfig("cannot write %s: %v", p, err)
	}
	return nil
}

// discardSession deletes a jar. Used when a login lands on the WRONG
// registration: a jar that authenticates as somebody else is worse than none,
// because every later command would quietly answer about the wrong GSTIN.
func discardSession(gstin string) {
	_ = os.Remove(sessionPath(gstin))
}

// sessionSummary is the one-line session state used by `doctor` and
// `auth status`. It never prints a cookie value.
func sessionSummary(gstin string) string {
	s, err := loadSession(gstin)
	if err != nil {
		return "unreadable: " + err.Error()
	}
	if s == nil {
		return "no cached session (run `auth login`)"
	}
	age := time.Since(s.SavedAt).Round(time.Second)
	state := s.Stage
	if s.expired(sessionMaxAge) {
		state += ", assumed expired"
	}
	return fmt.Sprintf("%s, %d cookies, %s old", state, len(s.Cookies), age)
}

// authStatus prints the cached session state for the selected registrations.
func (a *App) authStatus() error {
	type row struct {
		GSTIN   string `json:"gstin"`
		State   string `json:"state"`
		Stage   string `json:"stage"`
		Session string `json:"session"`
		Path    string `json:"path"`
	}
	regs := a.everySelected()
	rows := make([]row, 0, len(regs))
	for _, r := range regs {
		s, _ := loadSession(r.GSTIN)
		stage := "none"
		if s != nil {
			stage = s.Stage
		}
		rows = append(rows, row{r.GSTIN, r.State, stage, sessionSummary(r.GSTIN), sessionPath(r.GSTIN)})
	}
	if a.JSON || a.Agent {
		return a.emitValue("auth status", "", "", rows, len(rows))
	}
	for _, r := range rows {
		a.printf("%s  %-20s %s", r.GSTIN, r.State, r.Session)
	}
	return nil
}

// ---- credential-rejection record ------------------------------------------

// The login cap (maxLoginAttempts) is package-level, so it resets on every exec:
// a wrapper, a cron, an agent retry or `for i in 1 2 3; do gst-portal auth login`
// spends one REAL attempt per invocation against a live statutory account.
// Punjab/03 is the standing proof that this happens. So a credential rejection
// is written down, and the next login for that GSTIN is refused from disk until
// a human clears it — which is what "never retry a credential rejection"
// actually means.

type credentialRejection struct {
	GSTIN      string    `json:"gstin"`
	RejectedAt time.Time `json:"rejected_at"`
	PortalCode string    `json:"portal_code"`
}

func rejectionPath(gstin string) string {
	return filepath.Join(stateDir(), "gst-portal", "rejected-"+sanitiseGSTIN(gstin)+".json")
}

// recordCredentialRejection remembers that the portal refused this GSTIN's
// username/password. Best effort: failing to write it must not mask the
// rejection itself.
func recordCredentialRejection(gstin, portalCode string) {
	b, err := json.MarshalIndent(credentialRejection{
		GSTIN: gstin, RejectedAt: time.Now(), PortalCode: portalCode,
	}, "", "  ")
	if err != nil {
		return
	}
	p := rejectionPath(gstin)
	if err := os.MkdirAll(filepath.Dir(p), 0o700); err != nil {
		return
	}
	_ = os.WriteFile(p, b, 0o600)
}

// credentialRejectionFor returns the recorded rejection for a GSTIN, if any.
func credentialRejectionFor(gstin string) *credentialRejection {
	b, err := os.ReadFile(rejectionPath(gstin))
	if err != nil {
		return nil
	}
	var r credentialRejection
	if err := json.Unmarshal(b, &r); err != nil {
		return nil
	}
	return &r
}

// clearCredentialRejection is called after a login the portal accepted.
func clearCredentialRejection(gstin string) { _ = os.Remove(rejectionPath(gstin)) }

// ---- importing a browser-minted jar ---------------------------------------

// playwrightCookie is the shape browser exporters emit (Playwright, and gstack
// `browse cookies`): expires is seconds since epoch, -1 for a session cookie.
type playwrightCookie struct {
	Name     string   `json:"name"`
	Value    string   `json:"value"`
	Domain   string   `json:"domain"`
	Path     string   `json:"path"`
	Expires  *float64 `json:"expires"`
	Secure   bool     `json:"secure"`
	HTTPOnly bool     `json:"httpOnly"`
}

// importPlaywrightCookies converts an exported browser jar, keeping only
// gst.gov.in cookies. Anything else is somebody's unrelated browsing.
func importPlaywrightCookies(raw []byte) ([]sessionCookie, error) {
	var in []playwrightCookie
	if err := json.Unmarshal(raw, &in); err != nil {
		return nil, errUsage("cookie file is not a JSON array of {name,value,domain,…}: %v", err)
	}
	var out []sessionCookie
	for _, c := range in {
		d := strings.TrimPrefix(c.Domain, ".")
		if d != "gst.gov.in" && !strings.HasSuffix(d, ".gst.gov.in") {
			continue
		}
		sc := sessionCookie{
			Name: c.Name, Value: c.Value, Domain: c.Domain, Path: c.Path,
			Secure: c.Secure, HTTPOnly: c.HTTPOnly,
		}
		if sc.Path == "" {
			sc.Path = "/"
		}
		if c.Expires != nil && *c.Expires > 0 {
			sc.Expires = time.Unix(int64(*c.Expires), 0)
		}
		out = append(out, sc)
	}
	if len(out) == 0 {
		return nil, errUsage("no gst.gov.in cookies in that file — export the jar while logged in to the GST portal")
	}
	return out, nil
}
