package gateway

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// The gateway is the internet-facing surface, reachable through a public reverse
// proxy, and it performed no Origin, Host or Content-Type validation at all: a
// POST carrying `Origin: http://evil.example` was answered 200, and so was one
// carrying `Content-Type: text/plain`. hana-sql's own MCP transport enforces all
// three and documents the DNS-rebinding / CSRF reasoning behind them.
//
// post sends one JSON-RPC ping with the headers a caller chooses.
func post(t *testing.T, g *Gateway, headers map[string]string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
	for k, v := range headers {
		// Host never lands in Header: net/http lifts it into Request.Host, and a
		// handler reads it there.
		if k == "Host" {
			req.Host = v
			continue
		}
		if v == "" {
			req.Header.Del(k)
			continue
		}
		req.Header.Set(k, v)
	}
	rec := httptest.NewRecorder()
	g.Handler().ServeHTTP(rec, req)
	return rec
}

// A browser origin is refused. No legitimate MCP client sends one.
func TestHTTPRefusesABrowserOrigin(t *testing.T) {
	rec := post(t, testGateway(t), map[string]string{
		"Content-Type": "application/json",
		"Origin":       "http://evil.example",
	})
	if rec.Code != http.StatusForbidden {
		t.Fatalf("status = %d, want 403 for a cross-origin browser POST; body: %s", rec.Code, rec.Body.String())
	}
	if !strings.Contains(rec.Body.String(), "Origin") {
		t.Fatalf("refusal does not name the reason: %s", rec.Body.String())
	}
}

// An operator can allow one explicitly, and only that one.
func TestHTTPAllowsAConfiguredOrigin(t *testing.T) {
	cfg := DefaultConfig()
	cfg.Backends = nil
	cfg.AllowedOrigins = []string{"https://jivo.example"}
	g := New(cfg, "test")

	if rec := post(t, g, map[string]string{"Content-Type": "application/json", "Origin": "https://jivo.example"}); rec.Code != http.StatusOK {
		t.Fatalf("status = %d for an allowed origin, want 200; body: %s", rec.Code, rec.Body.String())
	}
	if rec := post(t, g, map[string]string{"Content-Type": "application/json", "Origin": "https://other.example"}); rec.Code != http.StatusForbidden {
		t.Fatalf("status = %d for an origin outside the allowlist, want 403", rec.Code)
	}
}

// The CORS *simple* request content types are what a web page can POST with no
// preflight at all. application/json forces a preflight, and this server answers
// none, so refusing everything else is what closes the no-preflight path.
func TestHTTPRefusesSimpleRequestContentTypes(t *testing.T) {
	g := testGateway(t)
	for _, ct := range []string{
		"text/plain",
		"text/plain;charset=UTF-8",
		"application/x-www-form-urlencoded",
		"multipart/form-data; boundary=x",
		"", // no Content-Type at all is a simple request too
	} {
		rec := post(t, g, map[string]string{"Content-Type": ct})
		if rec.Code != http.StatusUnsupportedMediaType {
			t.Fatalf("Content-Type %q got status %d, want 415; body: %s", ct, rec.Code, rec.Body.String())
		}
	}
}

// The real client's headers keep working: application/json, no Origin.
func TestHTTPAcceptsARealMCPClient(t *testing.T) {
	g := testGateway(t)
	for _, ct := range []string{"application/json", "application/json; charset=utf-8", "application/vnd.foo+json"} {
		rec := post(t, g, map[string]string{"Content-Type": ct})
		if rec.Code != http.StatusOK {
			t.Fatalf("Content-Type %q got status %d, want 200; body: %s", ct, rec.Code, rec.Body.String())
		}
	}
}

// Host is NOT checked by default: this gateway is deliberately reached by a
// public name through a proxy, so a loopback-only default would 403 the whole
// deployment. Configuring --allow-host turns the anti-rebinding check on.
func TestHTTPHostIsCheckedOnlyWhenConfigured(t *testing.T) {
	open := post(t, testGateway(t), map[string]string{"Content-Type": "application/json", "Host": "mcp.jivo.example"})
	if open.Code != http.StatusOK {
		t.Fatalf("status = %d with no --allow-host, want 200: a proxied gateway must not 403 its own public name", open.Code)
	}

	cfg := DefaultConfig()
	cfg.Backends = nil
	cfg.AllowedHosts = []string{"mcp.jivo.example"}
	g := New(cfg, "test")

	if rec := post(t, g, map[string]string{"Content-Type": "application/json", "Host": "mcp.jivo.example"}); rec.Code != http.StatusOK {
		t.Fatalf("status = %d for the allowed host, want 200", rec.Code)
	}
	if rec := post(t, g, map[string]string{"Content-Type": "application/json", "Host": "rebind.attacker.example"}); rec.Code != http.StatusForbidden {
		t.Fatalf("status = %d for an unlisted host, want 403 — this is what a DNS-rebinding request looks like", rec.Code)
	}
	// Loopback always survives, so --allow-host cannot lock an operator out of
	// their own probe.
	if rec := post(t, g, map[string]string{"Content-Type": "application/json", "Host": "127.0.0.1:7700"}); rec.Code != http.StatusOK {
		t.Fatalf("status = %d for loopback with --allow-host set, want 200", rec.Code)
	}
}

// /healthz is a container probe: it reads nothing and reaches nothing, so it
// stays open to a bare GET with no headers.
func TestHealthzIsNotGatedByTheFrontDoorChecks(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	req.Header.Set("Origin", "http://evil.example")
	rec := httptest.NewRecorder()
	testGateway(t).Handler().ServeHTTP(rec, req)
	if rec.Code != http.StatusOK || rec.Body.String() != "ok" {
		t.Fatalf("healthz = %d %q, want 200 ok", rec.Code, rec.Body.String())
	}
}

// The env vars are wired, and an empty value never becomes an allowlist of "".
func TestConfigFromEnvReadsTheAllowlists(t *testing.T) {
	env := map[string]string{
		"JIVO_GW_ALLOW_ORIGIN": " https://a.example , https://b.example ",
		"JIVO_GW_ALLOW_HOST":   "mcp.jivo.example",
	}
	cfg := ConfigFromEnv(func(k string) string { return env[k] })
	if len(cfg.AllowedOrigins) != 2 || cfg.AllowedOrigins[0] != "https://a.example" || cfg.AllowedOrigins[1] != "https://b.example" {
		t.Fatalf("AllowedOrigins = %q, want the two trimmed entries", cfg.AllowedOrigins)
	}
	if len(cfg.AllowedHosts) != 1 || cfg.AllowedHosts[0] != "mcp.jivo.example" {
		t.Fatalf("AllowedHosts = %q", cfg.AllowedHosts)
	}

	blank := ConfigFromEnv(func(k string) string {
		if k == "JIVO_GW_ALLOW_ORIGIN" {
			return " , , "
		}
		return ""
	})
	if len(blank.AllowedOrigins) != 0 {
		t.Fatalf("AllowedOrigins = %q, want nil for an all-separator value", blank.AllowedOrigins)
	}
	if len(DefaultConfig().AllowedOrigins) != 0 {
		t.Fatal("the compiled default must allow no browser origin at all")
	}
}
