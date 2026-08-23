package cli

import (
	"errors"
	"testing"

	"sapb1/internal/errs"
)

func TestExitCodeFor(t *testing.T) {
	cases := []struct {
		name string
		err  error
		want int
	}{
		{"nil", nil, ExitOK},
		{"config", &errs.ConfigError{Msg: "x"}, ExitConfig},
		{"auth", &errs.AuthError{Msg: "x"}, ExitAuth},
		{"network", &errs.NetworkError{Msg: "x"}, ExitNetwork},
		{"api", &errs.APIError{Msg: "x"}, ExitAPI},
		{"usage", &errs.UsageError{Msg: "x"}, ExitUsage},
		{"write outcome unknown", &errs.WriteOutcomeUnknownError{Msg: "x"}, ExitWriteUnknown},
		{"verification failed", &errs.WriteVerifyError{Msg: "x"}, ExitVerifyFailed},
		{"a guard refused", &errs.RefusedError{Msg: "x"}, ExitRefused},
		{"unknown/cobra", errors.New("unknown flag: --bogus"), ExitUsage},
	}
	for _, tc := range cases {
		if got := ExitCodeFor(tc.err); got != tc.want {
			t.Errorf("%s: ExitCodeFor() = %d, want %d", tc.name, got, tc.want)
		}
	}
}

// TestUnknownOutcomeOutranksNetwork — an unknown write outcome usually WRAPS a
// transport error, and it must still exit 7, never 5: 5 says "nothing happened,
// try again", which is the one conclusion an operator must not draw here.
func TestUnknownOutcomeOutranksNetwork(t *testing.T) {
	wrapped := &errs.WriteOutcomeUnknownError{
		Msg: "outcome unknown",
		Err: &errs.NetworkError{Msg: "connection reset"},
	}
	if got := ExitCodeFor(wrapped); got != ExitWriteUnknown {
		t.Errorf("ExitCodeFor(unknown wrapping network) = %d, want %d", got, ExitWriteUnknown)
	}
	if ExitWriteUnknown != 7 {
		t.Errorf("ExitWriteUnknown = %d, want the documented 7", ExitWriteUnknown)
	}
}

// TestVerifyFailureOutranksNetwork — the read-back after a DELETE can fail with
// a transport error, but SAP already answered the DELETE. Exit 5 says "nothing
// was sent, safe to retry" (acc/apbatch even labels it Retryable); exit 8 says
// "it is probably gone, go look, and re-running is safe anyway".
func TestVerifyFailureOutranksNetwork(t *testing.T) {
	wrapped := &errs.WriteVerifyError{
		Msg: "could not verify",
		Err: &errs.NetworkError{Msg: "connection reset"},
	}
	if got := ExitCodeFor(wrapped); got != ExitVerifyFailed {
		t.Errorf("ExitCodeFor(verify wrapping network) = %d, want %d", got, ExitVerifyFailed)
	}
	if ExitVerifyFailed != 8 || ExitRefused != 9 {
		t.Errorf("exit codes drifted: verify=%d refused=%d, want 8 and 9", ExitVerifyFailed, ExitRefused)
	}
}
