// Package errs defines the typed error categories used across sapb1 to map
// failures to the CLI's documented exit codes:
//
//	0 ok
//	2 usage error
//	3 config missing
//	4 auth failed
//	5 network / unreachable
//	6 API error
package errs

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
type APIError struct {
	Code interface{}
	Msg  string
}

func (e *APIError) Error() string { return e.Msg }
