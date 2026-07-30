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
