package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
)

// WiredEndpoint is one wired READ. The generated wired_manifest.go supplies the
// full slice; the generated cmd_<section>.go files build their groups from it.
type WiredEndpoint struct {
	Group   string // studied section, e.g. "Dashboard"
	Cmd     string // leaf command name, e.g. "tpay-dashboard-data"
	Backend string // business | mobapi | tpPay | tnd
	Path    string // path relative to the backend base
	URL     string // full URL (used by the coverage test + guardrail)
	Short   string // one-line help
}

// buildSection assembles a section command group from every wiredManifest entry
// in that group. One read command per endpoint — read-only by construction.
func buildSection(app *App, group, use, short string) *cobra.Command {
	g := &cobra.Command{Use: use, Short: short}
	for i := range wiredManifest {
		if wiredManifest[i].Group == group {
			g.AddCommand(readCmd(app, wiredManifest[i]))
		}
	}
	return g
}

// readCmd is the universal read leaf: POST an AES-wrapped payload built from
// account context + --set/--body. It can only ever call app.runRead (a read).
func readCmd(app *App, e WiredEndpoint) *cobra.Command {
	var body string
	var sets []string
	var noCtx bool
	c := &cobra.Command{
		Use:   e.Cmd,
		Short: e.Short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			payload, err := buildPayload(app, body, sets, !noCtx)
			if err != nil {
				return err
			}
			return app.runRead(e.Group+" "+e.Cmd, e.Backend, e.Path, payload)
		},
	}
	c.Flags().StringVar(&body, "body", "", "raw JSON request body (overrides --set and auto-context)")
	c.Flags().StringArrayVar(&sets, "set", nil, "payload field k=v (repeatable); value may be @accountId @geo @ouIds @productType @userid")
	c.Flags().BoolVar(&noCtx, "no-ctx", false, "do not auto-inject account context (accountId, customerAccountId, geo_location_id, ouIds)")
	return c
}

// buildPayload assembles the request JSON: optional --body base, auto account
// context (unless disabled), then --set overrides (with @token expansion).
func buildPayload(app *App, body string, sets []string, ctx bool) ([]byte, error) {
	m := map[string]any{}
	if strings.TrimSpace(body) != "" {
		if err := json.Unmarshal([]byte(body), &m); err != nil {
			return nil, fmt.Errorf("--body must be valid JSON: %w", err)
		}
	}
	ac := app.Client.ctx
	if ctx {
		// Only the proven-safe triple is auto-injected. NOT customerAccountId:
		// some endpoints (e.g. dashboard/get_tpay_dashboard_data) switch behaviour
		// and return empty when it is present. Add it per-endpoint with
		// `--set customerAccountId=@accountId` (the vault documents which need it).
		setIfAbsent(m, "accountId", ac.AccountID)
		setIfAbsent(m, "geo_location_id", ac.GeoLocationID)
		setIfAbsent(m, "ouIds", ac.OuIds)
	}
	for _, kv := range sets {
		i := strings.IndexByte(kv, '=')
		if i < 0 {
			return nil, fmt.Errorf("--set expects k=v, got %q", kv)
		}
		m[kv[:i]] = resolveToken(kv[i+1:], ac)
	}
	b, err := json.Marshal(m)
	if os.Getenv("TP_DEBUG") != "" {
		fmt.Fprintln(os.Stderr, "DEBUG payload:", string(b))
	}
	return b, err
}

func setIfAbsent(m map[string]any, k, v string) {
	if v == "" {
		return
	}
	if _, ok := m[k]; !ok {
		m[k] = v
	}
}

func resolveToken(v string, ac AccountCtx) string {
	switch v {
	case "@accountId":
		return ac.AccountID
	case "@geo":
		return ac.GeoLocationID
	case "@ouIds":
		return ac.OuIds
	case "@productType":
		return ac.ProductType
	case "@userid":
		return ac.UserID
	}
	return v
}
