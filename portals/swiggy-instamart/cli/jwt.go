package main

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"
)

// Claims is the subset of the ozone JWT this CLI reads. It NEVER prints the token
// itself (G6) — only these non-secret facts, so `doctor` can tell a human whether
// the inherited session is alive without exposing it.
type Claims struct {
	Email     string `json:"email"`
	Sub       string `json:"sub"`
	UserPool  string `json:"user_pool"`
	SessionID string `json:"session_id"`
	Exp       int64  `json:"exp"`
	Iat       int64  `json:"iat"`
	Jti       string `json:"jti"`
	Iss       string `json:"iss"`
}

func decodeJWT(tok string) (Claims, error) {
	var c Claims
	parts := strings.Split(tok, ".")
	if len(parts) != 3 {
		return c, errors.New("not a JWT")
	}
	b, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return c, err
	}
	if err := json.Unmarshal(b, &c); err != nil {
		return c, err
	}
	return c, nil
}

// sessionIDFromJWT pulls the session_id claim, which is what the request signature
// is keyed on. A STALE session_id is what produces Swiggy's 403
// "Request Forbidden: Please reload the browser".
func sessionIDFromJWT(tok string) (string, error) {
	c, err := decodeJWT(tok)
	if err != nil {
		return "", err
	}
	return c.SessionID, nil
}

func (c Claims) expiry() time.Time { return time.Unix(c.Exp, 0) }
func (c Claims) valid() bool       { return c.Exp > time.Now().Unix() }

func (c Claims) describe() string {
	if c.Exp == 0 {
		return "no token"
	}
	state := "EXPIRED"
	if c.valid() {
		state = fmt.Sprintf("valid, %s left", time.Until(c.expiry()).Round(time.Minute))
	}
	return fmt.Sprintf("%s (sub %s, pool %s) — %s, expires %s",
		c.Email, c.Sub, c.UserPool, state, c.expiry().UTC().Format(time.RFC3339))
}
