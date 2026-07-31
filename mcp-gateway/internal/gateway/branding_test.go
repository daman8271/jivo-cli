package gateway

import (
	"encoding/base64"
	"encoding/json"
	"strings"
	"testing"
)

// TestServerInfoCarriesBranding pins what a client sees on initialize. The
// failure this guards against is silent: a broken embed or a dropped field
// costs nothing at build time and simply shows the connector as an anonymous
// entry with no icon, which nobody notices until they look at the app.
func TestServerInfoCarriesBranding(t *testing.T) {
	g := New(DefaultConfig(), "test")
	res := g.initializeResult(json.RawMessage(`{"protocolVersion":"2025-06-18"}`))

	info, ok := res["serverInfo"].(map[string]any)
	if !ok {
		t.Fatalf("serverInfo missing or wrong type: %T", res["serverInfo"])
	}
	// name stays the machine identifier; title is the human-facing one.
	if info["name"] != "jivo-gateway" {
		t.Errorf("serverInfo.name = %v, want jivo-gateway (the stable machine id)", info["name"])
	}
	if info["title"] != serverTitle {
		t.Errorf("serverInfo.title = %v, want %q", info["title"], serverTitle)
	}
	for _, k := range []string{"description", "websiteUrl"} {
		if s, _ := info[k].(string); s == "" {
			t.Errorf("serverInfo.%s is empty", k)
		}
	}

	icons, ok := info["icons"].([]icon)
	if !ok || len(icons) == 0 {
		t.Fatalf("serverInfo.icons missing or empty: %#v", info["icons"])
	}
	for _, ic := range icons {
		if ic.MIMEType != "image/png" {
			t.Errorf("icon mimeType = %q, want image/png (the one type the spec requires clients to support)", ic.MIMEType)
		}
		// Spec restricts icon sources to HTTPS URLs or data URIs.
		const prefix = "data:image/png;base64,"
		if !strings.HasPrefix(ic.Src, prefix) {
			t.Fatalf("icon src does not start with %q", prefix)
		}
		raw, err := base64.StdEncoding.DecodeString(strings.TrimPrefix(ic.Src, prefix))
		if err != nil {
			t.Fatalf("icon src is not valid base64: %v", err)
		}
		// A failed go:embed yields an empty slice, which would still encode to
		// a syntactically valid data URI — so check the bytes are a real PNG.
		if len(raw) < 1000 {
			t.Errorf("icon decodes to only %d bytes — embed likely empty", len(raw))
		}
		if got := string(raw[1:4]); got != "PNG" {
			t.Errorf("icon is not a PNG (magic bytes %q)", got)
		}
	}
}

// TestBrandingSurvivesJSONRoundTrip proves the wire form is what a client
// actually receives — initializeResult builds a map[string]any, so a type that
// does not marshal would only fail at request time, not in the test above.
func TestBrandingSurvivesJSONRoundTrip(t *testing.T) {
	g := New(DefaultConfig(), "test")
	b, err := json.Marshal(g.initializeResult(json.RawMessage(`{}`)))
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	var out struct {
		ServerInfo struct {
			Name        string `json:"name"`
			Title       string `json:"title"`
			Description string `json:"description"`
			WebsiteURL  string `json:"websiteUrl"`
			Icons       []struct {
				Src      string   `json:"src"`
				MIMEType string   `json:"mimeType"`
				Sizes    []string `json:"sizes"`
			} `json:"icons"`
		} `json:"serverInfo"`
	}
	if err := json.Unmarshal(b, &out); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if out.ServerInfo.Title != serverTitle || len(out.ServerInfo.Icons) == 0 {
		t.Fatalf("branding lost on the wire: %+v", out.ServerInfo)
	}
	if len(out.ServerInfo.Icons[0].Sizes) == 0 {
		t.Error("icon sizes missing — a client cannot choose between the two variants")
	}
}
