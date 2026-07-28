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
		{"unknown/cobra", errors.New("unknown flag: --bogus"), ExitUsage},
	}
	for _, tc := range cases {
		if got := ExitCodeFor(tc.err); got != tc.want {
			t.Errorf("%s: ExitCodeFor() = %d, want %d", tc.name, got, tc.want)
		}
	}
}
