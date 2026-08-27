module jwa

go 1.24

// Versions are deliberately left for `go mod tidy` to pin on the build box —
// whatsmeow moves fast and pinning a stale commit here would be a lie by the
// time anyone runs it. deploy/install-vps.sh runs tidy before it builds.
require (
	github.com/mdp/qrterminal/v3 v3.2.0
	go.mau.fi/whatsmeow v0.0.0-20250101000000-000000000000
	modernc.org/sqlite v1.34.5
)
