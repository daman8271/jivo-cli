//go:build !windows

package cli

import (
	"os/signal"
	"syscall"
)

// ignoreSIGPIPE makes a write to a closed stdout return EPIPE instead of killing
// the process.
//
// Go's default is to die of SIGPIPE on fd 1 and 2, which for `delete … --json |
// head -1` means the run stops at an arbitrary point with exit 141 and no tally:
// the signal lands on the write AFTER the next DELETE has gone. signal.Ignore
// sets the disposition to SIG_IGN, so the write returns an error the batch can
// act on — see streamStopped, which turns it into "stop here, and say what was
// and was not deleted".
//
// Called from the delete path only. It is deliberately not process-wide startup
// behaviour: every other command in this tool is a read, and dying on a closed
// pipe is the right thing for those.
func ignoreSIGPIPE() {
	signal.Ignore(syscall.SIGPIPE)
}
