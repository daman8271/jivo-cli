// Package client is a minimal HTTP client for the SAP Business One Service
// Layer (b1s/v1). It handles Login/Logout, session-cookie management (with
// on-disk caching + transparent one-shot re-login on 401), and generic OData
// reads. It never issues POST/PUT/PATCH/DELETE against business entity sets —
// only against Login/Logout, per the read-only contract of this tool.
package client

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"time"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// Client talks to one SAP B1 Service Layer instance described by cfg.
type Client struct {
	cfg  *config.Config
	http *http.Client

	b1Session  string
	routeID    string
	loggedInAt time.Time
}

// New builds a Client from cfg. It does not perform any I/O.
func New(cfg *config.Config) *Client {
	transport := &http.Transport{}
	if cfg.Insecure {
		transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // #nosec G402 — user opt-in for self-signed SAP certs
	}
	return &Client{
		cfg: cfg,
		http: &http.Client{
			Timeout:   time.Duration(cfg.Timeout) * time.Second,
			Transport: transport,
		},
	}
}

// HasSession reports whether this Client currently holds session cookies
// (either from a fresh Login or a loaded cache), without contacting the server.
func (c *Client) HasSession() bool {
	return c.b1Session != ""
}

// SessionAge returns how long ago the current session was (re)established,
// and whether that information is known.
func (c *Client) SessionAge() (time.Duration, bool) {
	if c.loggedInAt.IsZero() {
		return 0, false
	}
	return time.Since(c.loggedInAt), true
}

// LoadCachedSession loads ~/.sapb1-session.json if it matches this Client's
// host/port/companyDB/user. Returns true if a usable cached session was found.
func (c *Client) LoadCachedSession() bool {
	sc, ok := loadSessionCache()
	if !ok {
		return false
	}
	if sc.Host != c.cfg.Host || sc.Port != c.cfg.Port || sc.CompanyDB != c.cfg.CompanyDB || sc.User != c.cfg.User {
		return false
	}
	c.b1Session = sc.B1Session
	c.routeID = sc.RouteID
	c.loggedInAt = sc.LoggedInAt
	return true
}

// ClearCachedSession forgets any in-memory session and deletes the cache file.
func (c *Client) ClearCachedSession() {
	c.b1Session = ""
	c.routeID = ""
	c.loggedInAt = time.Time{}
	_ = clearSessionCache()
}

func (c *Client) saveSession() {
	_ = saveSessionCache(&sessionCache{
		Host:       c.cfg.Host,
		Port:       c.cfg.Port,
		CompanyDB:  c.cfg.CompanyDB,
		User:       c.cfg.User,
		B1Session:  c.b1Session,
		RouteID:    c.routeID,
		LoggedInAt: c.loggedInAt,
	})
}

func (c *Client) attachCookies(req *http.Request) {
	if c.b1Session == "" {
		return
	}
	cookie := "B1SESSION=" + c.b1Session
	if c.routeID != "" {
		cookie += "; ROUTEID=" + c.routeID
	}
	req.Header.Set("Cookie", cookie)
}

// Login performs POST /Login and, on success, stores the returned session
// cookies both in memory and in the on-disk cache. It never logs or returns
// the password.
func (c *Client) Login(ctx context.Context) error {
	if err := c.cfg.ValidateConnection(); err != nil {
		return err
	}
	if err := c.cfg.ValidateCompanyDB(); err != nil {
		return err
	}

	payload, err := json.Marshal(map[string]string{
		"CompanyDB": c.cfg.CompanyDB,
		"UserName":  c.cfg.User,
		"Password":  c.cfg.Password,
	})
	if err != nil {
		return fmt.Errorf("building login request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.cfg.BaseURL()+"Login", bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("building login request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(req)
	if err != nil {
		return classifyTransportErr(err, c.cfg)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("reading login response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		msg := extractSAPError(body)
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", resp.StatusCode)
		}
		return &errs.AuthError{Msg: fmt.Sprintf("login to %q as %q failed: %s", c.cfg.CompanyDB, c.cfg.User, msg)}
	}

	var b1sess, route string
	for _, ck := range resp.Cookies() {
		switch ck.Name {
		case "B1SESSION":
			b1sess = ck.Value
		case "ROUTEID":
			route = ck.Value
		}
	}
	if b1sess == "" {
		return &errs.AuthError{Msg: "login succeeded (HTTP 200) but the server did not return a B1SESSION cookie"}
	}

	c.b1Session = b1sess
	c.routeID = route
	c.loggedInAt = time.Now()
	c.saveSession()
	return nil
}

// Logout performs POST /Logout (best-effort) and always clears the local
// session, in memory and on disk.
func (c *Client) Logout(ctx context.Context) error {
	if c.b1Session == "" {
		c.LoadCachedSession()
	}
	if c.b1Session != "" {
		req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.cfg.BaseURL()+"Logout", nil)
		if err == nil {
			c.attachCookies(req)
			if resp, err := c.http.Do(req); err == nil {
				resp.Body.Close()
			}
			// Network/API errors on logout are not fatal — we still clear locally.
		}
	}
	c.ClearCachedSession()
	return nil
}

// get performs an authenticated GET against path (relative to the Service
// Layer base URL, e.g. "Orders?$top=5"). It logs in first if there is no
// session yet, and transparently re-logs-in once and retries on a 401.
// Returns the raw response body on success (2xx), or a typed error otherwise.
func (c *Client) get(ctx context.Context, path string, headers map[string]string) ([]byte, error) {
	if c.b1Session == "" {
		if !c.LoadCachedSession() {
			if err := c.Login(ctx); err != nil {
				return nil, err
			}
		}
	}

	body, status, err := c.rawGet(ctx, path, headers)
	if err != nil {
		return nil, err
	}

	if status == http.StatusUnauthorized {
		if err := c.Login(ctx); err != nil {
			return nil, err
		}
		body, status, err = c.rawGet(ctx, path, headers)
		if err != nil {
			return nil, err
		}
	}

	if status < 200 || status >= 300 {
		msg := extractSAPError(body)
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", status)
		}
		if status == http.StatusUnauthorized {
			return nil, &errs.AuthError{Msg: fmt.Sprintf("authentication failed: %s", msg)}
		}
		return nil, &errs.APIError{Msg: msg}
	}

	return body, nil
}

func (c *Client) rawGet(ctx context.Context, path string, headers map[string]string) ([]byte, int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.cfg.BaseURL()+path, nil)
	if err != nil {
		return nil, 0, fmt.Errorf("building request: %w", err)
	}
	req.Header.Set("Accept", "application/json")
	c.attachCookies(req)
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, 0, classifyTransportErr(err, c.cfg)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, 0, fmt.Errorf("reading response body: %w", err)
	}
	return body, resp.StatusCode, nil
}

// CheckTCPReachable does a raw TCP dial to host:port (no TLS, no HTTP) to
// distinguish "network unreachable" from "reachable but SAP/TLS/auth issue".
// Used by `sapb1 doctor`.
func CheckTCPReachable(hostport string, timeout time.Duration) error {
	conn, err := net.DialTimeout("tcp", hostport, timeout)
	if err != nil {
		return &errs.NetworkError{
			Msg: fmt.Sprintf("cannot reach %s over TCP — are you on the company VPN or is your IP whitelisted? (%v)", hostport, err),
			Err: err,
		}
	}
	_ = conn.Close()
	return nil
}

// sapErrorBody mirrors the documented Service Layer error envelope:
//
//	{ "error": { "code": <int|string>, "message": { "lang": "en-us", "value": "..." } } }
type sapErrorBody struct {
	Error struct {
		Code    interface{} `json:"code"`
		Message struct {
			Lang  string `json:"lang"`
			Value string `json:"value"`
		} `json:"message"`
	} `json:"error"`
}

// extractSAPError best-effort parses the SAP error envelope out of body and
// returns the human message, or "" if body doesn't look like a SAP error.
func extractSAPError(body []byte) string {
	if len(body) == 0 {
		return ""
	}
	var eb sapErrorBody
	if err := json.Unmarshal(body, &eb); err != nil {
		return ""
	}
	return eb.Error.Message.Value
}

// classifyTransportErr turns a low-level Go net/http transport error (dial
// refused, timeout, DNS failure, TLS handshake failure, ...) into a friendly
// *errs.NetworkError. It's used for every http.Client.Do() failure, since at
// that layer there's no HTTP status code to inspect — the request never
// completed.
func classifyTransportErr(err error, cfg *config.Config) error {
	hostport := cfg.HostPort()
	msg := err.Error()

	if strings.Contains(msg, "certificate") || strings.Contains(msg, "x509") || strings.Contains(msg, "tls:") {
		return &errs.NetworkError{
			Msg: fmt.Sprintf(
				"TLS/certificate error connecting to %s — SAP boxes commonly use self-signed certificates; try --insecure or set SAPB1_INSECURE=true in .env (%v)",
				hostport, err,
			),
			Err: err,
		}
	}

	return &errs.NetworkError{
		Msg: fmt.Sprintf(
			"cannot reach SAP Service Layer at %s — are you on the company VPN or is your IP whitelisted? (%v)",
			hostport, err,
		),
		Err: err,
	}
}
