package cli

import (
	"errors"

	"sapb1/internal/errs"
)

// Exit codes, as documented for this tool.
//
//	0  it worked
//	2  usage — the command was spelled wrong; nothing was sent
//	3  config — something this run needs is missing or unwritable; nothing was sent
//	4  auth — SAP would not log this user in
//	5  network — the request never left; safe to re-run
//	6  API — SAP answered, and the answer was no
//	7  unknown outcome — sent, no answer; it MAY have committed. Do not re-run, go look
//	8  sent, but unverified — SAP answered and the evidence did not arrive. Go look; a delete is safe to re-run
//	9  refused — a guard said no. The command was right; the answer was still no
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
	// ExitVerifyFailed means SAP answered the write and the operator's evidence of
	// it did not arrive: the read-back after it failed, disagreed, or was answered
	// by something that is not that row — or, in a batch delete, the record could
	// not be written to stdout at all (a pipe closed early: `--json | head -1`;
	// see cli.streamStopped, which stops the batch there rather than deleting on
	// into a list it can no longer report). All of them mean the same two things
	// to an operator: it probably happened, and go and look. Re-running a delete
	// is safe — a DELETE cannot double-delete. See errs.WriteVerifyError.
	ExitVerifyFailed = 8
	// ExitRefused means a guard said no. The command was spelled correctly; the
	// answer was still no. See errs.RefusedError.
	ExitRefused = 9
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

	// Checked before NetworkError for the same reason as above: the verifying GET
	// after a successful DELETE can fail with a transport error, and "SAP already
	// answered, go look" outranks "you couldn't connect".
	var verifyErr *errs.WriteVerifyError
	if errors.As(err, &verifyErr) {
		return ExitVerifyFailed
	}

	var netErr *errs.NetworkError
	if errors.As(err, &netErr) {
		return ExitNetwork
	}

	var refusedErr *errs.RefusedError
	if errors.As(err, &refusedErr) {
		return ExitRefused
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
