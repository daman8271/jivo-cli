package cli

import (
	"errors"

	"sapb1/internal/errs"
)

// Exit codes, as documented for this tool.
const (
	ExitOK      = 0
	ExitUsage   = 2
	ExitConfig  = 3
	ExitAuth    = 4
	ExitNetwork = 5
	ExitAPI     = 6
	// ExitWriteUnknown means a write was sent but its outcome never came back.
	// It is NOT "the write failed" — see errs.WriteOutcomeUnknownError.
	ExitWriteUnknown = 7
)

// ExitCodeFor maps an error returned by a command's RunE to the process exit
// code it should produce. Unrecognized errors (including cobra's own usage
// errors, e.g. "unknown flag") default to ExitUsage.
func ExitCodeFor(err error) int {
	if err == nil {
		return ExitOK
	}

	var cfgErr *errs.ConfigError
	if errors.As(err, &cfgErr) {
		return ExitConfig
	}

	var authErr *errs.AuthError
	if errors.As(err, &authErr) {
		return ExitAuth
	}

	// Checked before NetworkError: an unknown write outcome may wrap a transport
	// error, and "you must go look in SAP" outranks "you couldn't connect".
	var unknownErr *errs.WriteOutcomeUnknownError
	if errors.As(err, &unknownErr) {
		return ExitWriteUnknown
	}

	var netErr *errs.NetworkError
	if errors.As(err, &netErr) {
		return ExitNetwork
	}

	var apiErr *errs.APIError
	if errors.As(err, &apiErr) {
		return ExitAPI
	}

	var usageErr *errs.UsageError
	if errors.As(err, &usageErr) {
		return ExitUsage
	}

	return ExitUsage
}
