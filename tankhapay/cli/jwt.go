package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// Claims is the outer TankhaPay session JWT (HS256, 24h). We never verify the
// signature — we only read the token we were handed, to fail fast on expiry with
// a clear message instead of a confusing 401. The interesting account context is
// AES-ECB encrypted inside the `data` field (same body key). See
// ../vault/_meta/Auth-and-Access.md.
type Claims struct {
	Exp  int64  `json:"exp"`
	Iat  int64  `json:"iat"`
	Data string `json:"data"`
	// aud/iss are intentionally omitted: TankhaPay serializes `aud` as an ARRAY,
	// which would break json.Unmarshal into a string field — and we never use them.
}

func (c Claims) Expiry() time.Time          { return time.Unix(c.Exp, 0).UTC() }
func (c Claims) Expired(now time.Time) bool { return c.Exp == 0 || !now.Before(c.Expiry()) }
func (c Claims) Remaining(now time.Time) time.Duration {
	return c.Expiry().Sub(now)
}

// decodeJWT parses the payload of a "header.payload.signature" token, no verify.
func decodeJWT(token string) (Claims, error) {
	parts := strings.Split(strings.TrimSpace(token), ".")
	if len(parts) != 3 {
		return Claims{}, fmt.Errorf("not a JWT: expected 3 parts, got %d", len(parts))
	}
	payload, err := base64.RawURLEncoding.DecodeString(strings.TrimRight(parts[1], "="))
	if err != nil {
		return Claims{}, fmt.Errorf("decode JWT payload: %w", err)
	}
	var c Claims
	if err := json.Unmarshal(payload, &c); err != nil {
		return Claims{}, fmt.Errorf("parse JWT claims: %w", err)
	}
	return c, nil
}

// AccountCtx is the per-account context every read needs. All values are strings
// so the CLI can splice them into JSON payloads verbatim (the API accepts both
// "2719" and 2719 for accountId).
type AccountCtx struct {
	AccountID     string `json:"tp_account_id"`
	GeoLocationID string `json:"geo_location_id"`
	OuIds         string `json:"ouIds"`
	ProductType   string `json:"product_type"`
	UserID        string `json:"userid"`
	Name          string `json:"name"`
	Role          string `json:"rolename"`
}

// decodeAccount decrypts the JWT `data` blob (AES-ECB, body key) into AccountCtx.
func decodeAccount(bodyKey []byte, dataField string) (AccountCtx, error) {
	var ac AccountCtx
	if dataField == "" {
		return ac, fmt.Errorf("JWT has no data field")
	}
	plain, err := aesECBDecrypt(bodyKey, dataField)
	if err != nil {
		return ac, fmt.Errorf("decrypt JWT data: %w", err)
	}
	var m map[string]any
	if err := json.Unmarshal(plain, &m); err != nil {
		return ac, fmt.Errorf("parse JWT data: %w", err)
	}
	str := func(k string) string {
		switch v := m[k].(type) {
		case nil:
			return ""
		case string:
			return v
		case float64:
			// integers arrive as float64; render without a trailing ".0"
			return fmt.Sprintf("%.0f", v)
		default:
			return fmt.Sprintf("%v", v)
		}
	}
	ac = AccountCtx{
		AccountID:     str("tp_account_id"),
		GeoLocationID: str("geo_location_id"),
		OuIds:         str("ouIds"),
		ProductType:   str("product_type"),
		UserID:        str("userid"),
		Name:          str("name"),
		Role:          str("rolename"),
	}
	return ac, nil
}
