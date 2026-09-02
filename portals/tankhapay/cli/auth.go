package main

import (
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// md5hex lowercases the hex MD5 — the exact password transform the portal uses.
func md5hex(s string) string {
	h := md5.Sum([]byte(s))
	return hex.EncodeToString(h[:])
}

// login is the ONLY non-read call in this CLI (the sanctioned token exchange).
// reCAPTCHA is bypassed with localhost:true and the action MUST be
// check_login_by_emailid1 (proven live 2026-07-25). See ../vault/_meta/Proven-Login-Recipe.md.
func (c *Client) login() (string, error) {
	payload := mustJSON(map[string]any{
		"email":          c.cfg.Username,
		"password":       md5hex(c.cfg.Password),
		"recaptchaToken": "",
		"localhost":      true,
		"action":         "check_login_by_emailid1",
	})
	enc, err := aesECBEncrypt(c.cfg.BodyKey, payload)
	if err != nil {
		return "", err
	}
	url := joinURL(c.cfg.Backends["business"], "login")
	raw, status, err := c.rawPost(url, mustJSON(map[string]string{"encrypted": enc}), false)
	if err != nil {
		return "", err
	}
	if status < 200 || status >= 300 {
		return "", fmt.Errorf("login → HTTP %d", status)
	}
	var r struct {
		Status  string `json:"status"`
		Token   string `json:"token"`
		Message string `json:"message"`
		Code    string `json:"code"`
	}
	if err := json.Unmarshal(raw, &r); err != nil {
		return "", fmt.Errorf("login: unparseable response")
	}
	if r.Token == "" || !strings.EqualFold(r.Status, "true") {
		return "", fmt.Errorf("login failed: status=%q code=%q message=%q", r.Status, r.Code, r.Message)
	}
	return r.Token, nil
}

// ensureAuth guarantees a live token + account context: in-memory → disk cache →
// one fresh login (capped).
func (c *Client) ensureAuth() error {
	if c.token != "" {
		if cl, err := decodeJWT(c.token); err == nil && !cl.Expired(time.Now()) {
			return nil
		}
	}
	if tok := loadCachedToken(); tok != "" {
		if cl, err := decodeJWT(tok); err == nil && !cl.Expired(time.Now()) {
			c.token = tok
			c.loadCtx()
			return nil
		}
	}
	return c.relogin()
}

// relogin forces a fresh login (ignoring cache), at most once per process.
func (c *Client) relogin() error {
	if c.attempted {
		return fmt.Errorf("login already attempted this run; not retrying (avoids account lockout)")
	}
	c.attempted = true
	tok, err := c.login()
	if err != nil {
		return err
	}
	c.token = tok
	_ = saveCachedToken(tok)
	c.loadCtx()
	return nil
}

// loadCtx decodes tp_account_id / geo_location_id / ouIds from the token's data.
func (c *Client) loadCtx() {
	if cl, err := decodeJWT(c.token); err == nil {
		if ac, err := decodeAccount(c.cfg.BodyKey, cl.Data); err == nil {
			c.ctx = ac
		}
	}
}
