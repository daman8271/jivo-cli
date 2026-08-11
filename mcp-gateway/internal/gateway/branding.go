package gateway

import (
	_ "embed"
	"encoding/base64"
	"sync"
)

// JIVO branding for the initialize handshake.
//
// MCP's Implementation type (what serverInfo carries) accepts title, description,
// websiteUrl and icons; the spec requires clients to support at least image/png,
// and restricts icon sources to HTTPS URLs or data URIs.
//
// Data URIs are used rather than an HTTPS link on purpose. The gateway is served
// behind Traefik under a secret path prefix that is stripped before the request
// arrives, so the server genuinely does not know its own public URL and would
// have to be told — one more thing to configure, and one more thing to break
// silently when the path is rotated. Embedding the bytes makes the icon a
// property of the binary instead: it cannot 404, cannot leak the secret path to
// whatever renders it, and costs nothing per tool call because initialize
// happens once per connection.
//
// Two sizes are offered, smallest first, so a client picking the first entry it
// understands gets the cheap one. Both are the JIVO mark on its brand green,
// which reads correctly on light and dark chrome alike — hence no Theme hint.
//
//go:embed assets/jivo-icon-128.png
var iconPNG128 []byte

//go:embed assets/jivo-icon-256.png
var iconPNG256 []byte

// icon mirrors mcp.Icon. It is declared here rather than imported because this
// module deliberately has no dependencies — see the package doc.
type icon struct {
	Src      string   `json:"src"`
	MIMEType string   `json:"mimeType,omitempty"`
	Sizes    []string `json:"sizes,omitempty"`
}

var (
	iconsOnce sync.Once
	iconsVal  []icon
)

// serverIcons returns the branding icons as data URIs, encoded once and reused.
func serverIcons() []icon {
	iconsOnce.Do(func() {
		iconsVal = []icon{
			{
				Src:      "data:image/png;base64," + base64.StdEncoding.EncodeToString(iconPNG128),
				MIMEType: "image/png",
				Sizes:    []string{"128x128"},
			},
			{
				Src:      "data:image/png;base64," + base64.StdEncoding.EncodeToString(iconPNG256),
				MIMEType: "image/png",
				Sizes:    []string{"256x256"},
			},
		}
	})
	return iconsVal
}

const (
	// serverTitle is the human-facing name. serverInfo.name stays the stable
	// machine identifier ("jivo-gateway"); title is what a person should see.
	serverTitle = "JIVO"

	serverDescription = "Read-only access to JIVO's live business systems — " +
		"SAP B1 (all three companies), HANA SQL, Postgres, e-commerce, orders, factory, " +
		"EXIM (imports/exports) and JSAP (ops platform)."

	serverWebsiteURL = "https://jivo.in"
)
