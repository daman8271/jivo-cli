// Package portal is a READ-ONLY HTTP client for the JIVO DSR web portal.
//
// It authenticates once (GET /Login/CheckLogin) and issues GET requests to the
// portal's report/read endpoints only. It deliberately exposes no POST/write
// method — the DSR portal is strictly read-only for this tool (RULE 0).
package portal

import (
	"fmt"
	"io"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strings"
	"time"
)

// Client is a logged-in, read-only portal session.
type Client struct {
	base string
	http *http.Client
}

// New builds a client with a cookie jar for the portal base URL.
func New(base string, timeout time.Duration) (*Client, error) {
	jar, err := cookiejar.New(nil)
	if err != nil {
		return nil, err
	}
	if timeout <= 0 {
		timeout = 30 * time.Second
	}
	return &Client{
		base: strings.TrimRight(base, "/"),
		http: &http.Client{Jar: jar, Timeout: timeout},
	}, nil
}

// Login authenticates via GET /Login/CheckLogin. The app returns its literal
// client-side redirect on success; anything else (e.g. "Wrong Credentials") is
// treated as a failed login.
func (c *Client) Login(user, pass string) error {
	q := url.Values{}
	q.Set("user", user)
	q.Set("password", pass)
	body, err := c.Get("/Login/CheckLogin", q)
	if err != nil {
		return err
	}
	s := strings.TrimSpace(string(body))
	if !strings.Contains(s, "window.location") {
		return fmt.Errorf("portal login failed: %s", strings.Trim(s, "'\" "))
	}
	return nil
}

// Get issues a read-only GET and returns the raw response body (capped at 8 MB).
func (c *Client) Get(path string, params url.Values) ([]byte, error) {
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}
	u := c.base + path
	if len(params) > 0 {
		u += "?" + params.Encode()
	}
	resp, err := c.http.Get(u)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("GET %s -> HTTP %d", path, resp.StatusCode)
	}
	return body, nil
}
