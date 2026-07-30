// Package errs defines the typed error categories used across sapb1 to map
// failures to the CLI's documented exit codes:
//
//	0 ok
//	2 usage error
//	3 config missing
//	4 auth failed
//	5 network / unreachable (nothing was sent)
//	6 API error (server reached, request definitively rejected)
//	7 write outcome unknown (request was sent, result never came back)
package errs

import "fmt"

// ConfigError means required configuration (host/user/password/companyDB/etc.)
// is missing or invalid. Maps to exit code 3.
type ConfigError struct {
	Msg string
}

func (e *ConfigError) Error() string { return e.Msg }

// UsageError means the command itself was invoked incorrectly (bad flag
// combination, bad argument). Maps to exit code 2.
type UsageError struct {
	Msg string
}

func (e *UsageError) Error() string { return e.Msg }

// AuthError means the Service Layer rejected credentials, or a session could
// not be (re)established. Maps to exit code 4.
type AuthError struct {
	Msg string
}

func (e *AuthError) Error() string { return e.Msg }

// NetworkError means the Service Layer host could not be reached at all
// (dial/timeout/DNS/TLS handshake failure). Maps to exit code 5.
type NetworkError struct {
	Msg string
	Err error
}

func (e *NetworkError) Error() string { return e.Msg }
func (e *NetworkError) Unwrap() error { return e.Err }

// APIError means the Service Layer was reached, a session exists, but the
// request itself failed (bad $filter, unknown entity set, server-side
// error, etc.). Maps to exit code 6.
//
// For a write, an APIError is a DEFINITIVE rejection: SAP answered with its own
// error envelope, so nothing was committed. Contrast WriteOutcomeUnknownError.
type APIError struct {
	Code interface{}
	Msg  string
}

// Error includes SAP's own error code when the envelope carried one — those
// codes (-5002, -2028, 301, …) are what an SAP admin searches for.
func (e *APIError) Error() string {
	if e.Code == nil || e.Code == "" {
		return e.Msg
	}
	return fmt.Sprintf("[SAP %v] %s", e.Code, e.Msg)
}

// WriteOutcomeUnknownError means a write request was (or may have been) put on
// the wire, but no definitive answer came back: the client timed out waiting for
// the response, the connection was reset after the request was sent, or a
// gateway returned 502/504 with no SAP error envelope — i.e. the failure came
// from something between us and SAP, not from SAP itself.
//
// This is deliberately its own category (exit code 7) because the safe reaction
// is the opposite of a NetworkError's: do NOT re-run the command. The write may
// already be committed, and a blind retry double-posts.
type WriteOutcomeUnknownError struct {
	Msg string
	Err error
}

func (e *WriteOutcomeUnknownError) Error() string { return e.Msg }
func (e *WriteOutcomeUnknownError) Unwrap() error { return e.Err }
