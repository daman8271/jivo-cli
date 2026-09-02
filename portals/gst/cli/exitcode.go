package main

import (
	"errors"
	"fmt"
)

// Exit codes — the house table (sap-b1/cli/internal/cli/exitcode.go:10-20, dsr
// uses the same numbering). There is deliberately no exit 7 ("write outcome
// unknown"): this CLI never writes, so that outcome cannot happen.
const (
	exitOK      = 0
	exitGeneric = 1
	exitUsage   = 2
	exitConfig  = 3
	exitAuth    = 4
	exitNetwork = 5 // network failure OR read-only guard refusal — nothing was sent
	exitAPI     = 6 // the portal answered, and its answer was an error
)

// usageError — the operator asked for something the CLI cannot parse.
type usageError struct{ msg string }

func (e *usageError) Error() string { return e.msg }
func errUsage(format string, a ...any) error {
	return &usageError{msg: fmt.Sprintf(format, a...)}
}

// configError — credentials or .env are missing/invalid. Never contains a secret.
type configError struct{ msg string }

func (e *configError) Error() string { return e.msg }
func errConfig(format string, a ...any) error {
	return &configError{msg: fmt.Sprintf(format, a...)}
}

// authError — no session, expired session, WAF bounce to accessdenied/login,
// GSTIN mismatch, or the portal demanding OTP.
type authError struct{ msg string }

func (e *authError) Error() string { return e.msg }
func errAuth(format string, a ...any) error {
	return &authError{msg: fmt.Sprintf(format, a...)}
}

// guardError — the read-only guard refused the call. NOTHING WAS SENT. This is
// the error the operator should see if a command ever tries to leave the
// allowlist; it shares exit 5 with network failures because both mean "the
// portal never heard from us".
type guardError struct{ msg string }

func (e *guardError) Error() string { return "read-only guard: " + e.msg }
func errGuard(format string, a ...any) error {
	return &guardError{msg: fmt.Sprintf(format, a...)}
}

// networkError — transport failure; the request may or may not have been read,
// but for a read-only CLI that is harmless.
type networkError struct {
	msg string
	err error
}

func (e *networkError) Error() string {
	if e.err == nil {
		return e.msg
	}
	return e.msg + ": " + e.err.Error()
}
func (e *networkError) Unwrap() error { return e.err }
func errNetwork(msg string, err error) error {
	return &networkError{msg: msg, err: err}
}

// apiError — the portal returned an error envelope ({"status":0,"error":{…}} or
// {"status_cd":"0","error":{…}}) or an HTTP status we cannot use. Empty-result
// codes (RET13510, LG9221, GTR2B-002) are NOT errors — see emptyCodes.
type apiError struct {
	Code    string
	Message string
	Status  int
}

func (e *apiError) Error() string {
	switch {
	case e.Code != "" && e.Message != "":
		return fmt.Sprintf("portal error %s: %s", e.Code, e.Message)
	case e.Code != "":
		return "portal error " + e.Code
	case e.Status != 0:
		return fmt.Sprintf("portal returned HTTP %d", e.Status)
	default:
		return "portal error"
	}
}

// errPlain is an untyped error, used where no category applies.
func errPlain(format string, a ...any) error { return fmt.Errorf(format, a...) }

// exitCodeFor maps a command error to the process exit code. Unrecognised
// errors (including cobra's own "unknown flag") default to exitUsage, as sapb1.
func exitCodeFor(err error) int {
	if err == nil {
		return exitOK
	}
	var cfgErr *configError
	if errors.As(err, &cfgErr) {
		return exitConfig
	}
	var aErr *authError
	if errors.As(err, &aErr) {
		return exitAuth
	}
	// Guard before network: "nothing was sent because we refused" outranks a
	// transport message it might be wrapped in.
	var gErr *guardError
	if errors.As(err, &gErr) {
		return exitNetwork
	}
	var nErr *networkError
	if errors.As(err, &nErr) {
		return exitNetwork
	}
	var apiErr *apiError
	if errors.As(err, &apiErr) {
		return exitAPI
	}
	var uErr *usageError
	if errors.As(err, &uErr) {
		return exitUsage
	}
	return exitUsage
}

// portalUnavailable reports whether err is the PORTAL being down, as opposed to
// anything at all about our session.
//
// This distinction is load-bearing for any unattended keeper. The GST portal
// takes its authenticated API offline overnight — observed 2026-09-02 00:15 IST,
// where services/api/ustatus, return. and payment. all served 503 while a plain
// GET of the public login page still answered (that 200 is the F5 interstitial,
// not the page). A keeper that reads 503 as "session died" will try to log in,
// find the login flow is 503 too, and spend the whole maintenance window burning
// attempts that cannot succeed. 503 means WAIT; only exit 4 means LOG IN.
func portalUnavailable(err error) bool {
	var apiErr *apiError
	if errors.As(err, &apiErr) {
		return apiErr.Status >= 500 && apiErr.Status <= 599
	}
	return false
}

// asAuthError is errors.As specialised for *authError; kept here so output.go
// does not need to import errors.
func asAuthError(err error, target **authError) bool {
	return errors.As(err, target)
}

// asCredentialError is the same for *credentialError (login.go), so a refused
// username/password can be written down without matching on message text.
func asCredentialError(err error, target **credentialError) bool {
	return errors.As(err, target)
}
