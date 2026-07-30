package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

// Config holds everything needed to READ the Swiggy Instamart portal.
//
// Secrets are NEVER hardcoded and never written by this CLI. Everything is
// INHERITED from the config file JIVO's existing swiggy-instamart-cli already
// maintains, or from the environment. Per G9 this CLI consumes a session and
// never mints one: it has no login, no refresh and no sign-out command, because
// the ozone refresh token is single-use and rotating it would break the live
// session belonging to JIVO's e-com team and the production keepalive cron.
type Config struct {
	// ads / brand lane (tanuj@jivo.in in JIVO's setup)
	Token  string `json:"token"`
	UserID string `json:"user_id"`
	Email  string `json:"email"`

	// supply / vendor lane (ecom1@jivo.in in JIVO's setup). picker.swiggy.com
	// authenticates with this in an `Abacus-Token` header, NOT `authorization`.
	SupplyToken  string `json:"supply_token"`
	SupplyUserID string `json:"supply_user_id"`
	SupplyEmail  string `json:"supply_email"`

	// entity ids, keyed by label. See vault/platform/Accounts-And-Entities.md —
	// note the labels in JIVO's on-disk config are known to be mismapped.
	BrandAccounts   map[string]string `json:"brand_accounts"`
	SupplyCompanies map[string]string `json:"supply_companies"`
}

// Production hosts, read verbatim out of each remote's [PRODUCTION] env block.
const (
	hostBrandPortal = "https://brand-portal-service-http.swiggy.com"
	hostPartnerAPI  = "https://partner-api.swiggy.com"
	hostPicker      = "https://picker.swiggy.com"
	hostOzone       = "https://ozone-idp-brands-im-kba.swiggy.com" // documented, never called

	originHeader  = "https://partner.instamart.in"
	refererHeader = "https://partner.instamart.in/"
	userAgent     = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
		"(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)

// Verified account ids (vault/platform/Accounts-And-Entities.md). These are not
// secrets — G6 explicitly permits recording entity ids.
const (
	acctJivoWellness = "c9f24655-a984-4b65-a4da-2d5b6461b9ec"
	acctJivoMart     = "89bafc9c-8a56-4286-94cf-a55ab4e564d3"
	acctJivo         = "260921c1-76e7-48ef-9771-82124ebe1fcc"
)

var accountAliases = map[string]string{
	"wellness": acctJivoWellness,
	"mart":     acctJivoMart,
	"jivo":     acctJivo,
}

// errNoAuth is returned when the inherited session is absent.
var errNoAuth = errors.New("no inherited session")

func configPath() string {
	if p := os.Getenv("SWIGGY_CONFIG"); p != "" {
		return p
	}
	home, err := os.UserHomeDir()
	if err != nil {
		home = os.Getenv("HOME")
	}
	return filepath.Join(home, ".config", "swiggy-instamart-cli", "config.json")
}

func loadConfig() (Config, error) {
	var c Config
	if b, err := os.ReadFile(configPath()); err == nil {
		_ = json.Unmarshal(b, &c)
	}
	// env always wins (handy for cron and for pointing at a different box)
	if v := os.Getenv("SWIGGY_TOKEN"); v != "" {
		c.Token = v
	}
	if v := os.Getenv("SWIGGY_SUPPLY_TOKEN"); v != "" {
		c.SupplyToken = v
	}
	if v := os.Getenv("SWIGGY_EMAIL"); v != "" {
		c.Email = v
	}
	if c.BrandAccounts == nil {
		c.BrandAccounts = map[string]string{}
	}
	if c.Token == "" && c.SupplyToken == "" {
		return c, fmt.Errorf("%w: no token in %s and neither SWIGGY_TOKEN nor "+
			"SWIGGY_SUPPLY_TOKEN is set.\n"+
			"This CLI never logs in (G9: the refresh token is single-use and rotating it "+
			"breaks JIVO's live session + the keepalive cron).\n"+
			"Have a human refresh the session in the normal way, then re-run",
			errNoAuth, configPath())
	}
	return c, nil
}

// resolveAccount maps mart|wellness|jivo (or a raw uuid) to an account id.
func resolveAccount(c Config, want string) (string, error) {
	if want == "" {
		return acctJivoWellness, nil // the account with data; documented default
	}
	if id, ok := accountAliases[want]; ok {
		return id, nil
	}
	if id, ok := c.BrandAccounts[want]; ok && id != "" {
		return id, nil
	}
	if len(want) >= 30 {
		return want, nil // a raw uuid
	}
	return "", fmt.Errorf("unknown account %q (known: mart, wellness, jivo, or a raw uuid)", want)
}
