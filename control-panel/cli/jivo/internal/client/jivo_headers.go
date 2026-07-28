// Hand-authored, durable across `generate --force` (novel file: the generator
// never emits internal/client/jivo_headers.go, so regeneration preserves it).
//
// This file is the single source of truth for the Django session/CSRF header
// wiring. The Jivo Control Panel authenticates with a Django session cookie
// plus cookie-to-header CSRF, and gates every AJAX endpoint behind the
// X-Requested-With header. `auth.type: none` in the spec means the generator
// emits no auth layer; instead `jivo auth login` (internal/cli/jivo_login.go)
// persists the session and stores the headers built here into the config
// file's [headers] table. The generated client then sets every entry of
// Config.Headers on each request (see do() in client.go), so Cookie +
// X-CSRFToken + X-Requested-With ride along transparently.

package client

import (
	"fmt"
	"strings"
)

// InternalHost is the internal Control Panel host. It is served over plain
// HTTP on an internal IP (no TLS), so credential/login flows must explicitly
// allow it past any https-only guard.
const InternalHost = "103.89.45.75"

// xhrHeader is the AJAX gate every Realise/Inventory endpoint requires; the
// server answers 403/HTML without it. Kept here (not only in the spec's
// required_headers) so the login-written config is self-contained.
const (
	xhrHeaderName  = "X-Requested-With"
	xhrHeaderValue = "XMLHttpRequest"
)

// SessionHeaders builds the per-request header set that carries the Django
// session and CSRF token on every authenticated call. The returned map is
// written verbatim into the config file's [headers] table by `auth login`,
// and the generated client applies it to each request. Returns:
//   - Cookie:           sessionid=<sid>; csrftoken=<csrf>
//   - X-CSRFToken:      <csrf>   (required on POST reads; harmless on GET)
//   - X-Requested-With: XMLHttpRequest
func SessionHeaders(sessionID, csrfToken string) map[string]string {
	return map[string]string{
		"Cookie":      fmt.Sprintf("sessionid=%s; csrftoken=%s", sessionID, csrfToken),
		"X-CSRFToken": csrfToken,
		xhrHeaderName: xhrHeaderValue,
	}
}

// AllowInsecureBase reports whether a plain-http base URL is permitted for the
// login credential exchange. HTTPS is always allowed; plain HTTP is allowed
// only for the internal Control Panel host and loopback (local test servers).
func AllowInsecureBase(base string) bool {
	base = strings.TrimSpace(base)
	switch {
	case strings.HasPrefix(base, "https://"):
		return true
	case strings.Contains(base, InternalHost):
		return true
	case strings.HasPrefix(base, "http://localhost"),
		strings.HasPrefix(base, "http://127.0.0.1"),
		strings.HasPrefix(base, "http://[::1]"):
		return true
	default:
		return false
	}
}
