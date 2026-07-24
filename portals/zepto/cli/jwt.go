package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// JWTClaims is the subset of Zepto's session JWT we care about. No signature
// verification is performed (we hold no HS256 secret and none is needed — we
// only read the token we were handed). This is a client-side expiry check to
// fail fast with a clear message instead of a confusing 401.
type JWTClaims struct {
	Exp     int64  `json:"exp"`
	Iat     int64  `json:"iat"`
	EmailID string `json:"emailId"`
	Role    string `json:"roleName"`
}

func (c JWTClaims) Expiry() time.Time          { return time.Unix(c.Exp, 0).UTC() }
func (c JWTClaims) Expired(now time.Time) bool { return !now.Before(c.Expiry()) }
func (c JWTClaims) Remaining(now time.Time) time.Duration {
	return c.Expiry().Sub(now)
}

// decodeJWT extracts claims from a JWT payload without verifying its signature.
// token must be the raw "header.payload.signature" string (no "Bearer " prefix).
func decodeJWT(token string) (JWTClaims, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return JWTClaims{}, fmt.Errorf("not a JWT: expected 3 dot-separated parts, got %d", len(parts))
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		payload, err = base64.RawURLEncoding.DecodeString(strings.TrimRight(parts[1], "="))
		if err != nil {
			return JWTClaims{}, fmt.Errorf("decode JWT payload: %w", err)
		}
	}
	var claims JWTClaims
	if err := json.Unmarshal(payload, &claims); err != nil {
		return JWTClaims{}, fmt.Errorf("parse JWT claims: %w", err)
	}
	return claims, nil
}
