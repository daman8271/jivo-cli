//go:build windows

package cli

// ignoreSIGPIPE does nothing on Windows: there is no SIGPIPE, and a write to a
// closed pipe already comes back as an error rather than a signal. The batch
// handles that error the same way (see streamStopped).
//
// The accounts-kit binary the office runs is a Windows build, so this file is
// what keeps it compiling.
func ignoreSIGPIPE() {}
