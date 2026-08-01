//go:build unix

package gateway

import (
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"
)

// The reported probe, reproduced: mkfifo INDEX.md, point --corrections at it,
// call initialize. os.ReadFile blocks in open(2) until a writer appears, and it
// used to do that inline while holding the corrections mutex — so initialize
// never returned and gateway_status wedged behind the same lock, with nothing
// logged and /healthz still passing.
//
// Without the fix this test does not pass slowly; it never finishes the two
// selects and fails on their deadlines.
func TestCorrectionsFIFOPathDoesNotWedgeTheGateway(t *testing.T) {
	fifo := filepath.Join(t.TempDir(), "INDEX.md")
	if err := syscall.Mkfifo(fifo, 0o600); err != nil {
		t.Skipf("cannot create a FIFO here: %v", err)
	}

	cfg := DefaultConfig()
	cfg.CorrectionsPath = fifo
	g := New(cfg, "test")

	initDone := make(chan string, 1)
	go func() {
		res := g.initializeResult(nil)
		s, _ := res["instructions"].(string)
		initDone <- s
	}()
	statusDone := make(chan map[string]any, 1)
	go func() { statusDone <- g.CorrectionsStatus() }()

	var instr string
	select {
	case instr = <-initDone:
	case <-time.After(30 * time.Second):
		t.Fatal("initialize never returned with a FIFO at --corrections: the digest read is blocking on the caller's path again")
	}
	select {
	case st := <-statusDone:
		if st["source"] != "embedded" {
			t.Fatalf("source = %v, want the embedded snapshot while the FIFO never answers", st["source"])
		}
	case <-time.After(30 * time.Second):
		t.Fatal("gateway_status never returned: it is queued behind the blocked FIFO read on the corrections mutex")
	}

	// Degraded, never dead: the client still gets a real rule set.
	if !strings.Contains(instr, "[C-0001]") {
		t.Fatalf("a blocking --corrections path cost the client its rules:\n%s", instr)
	}
	// The parked read stays parked in the kernel for the life of the process.
	// That is the deliberate cost: exactly one goroutine, not one per minute.
}
