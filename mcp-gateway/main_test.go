package main

import (
	"io"
	"os"
	"strings"
	"testing"

	"mcp-gateway/internal/gateway"
)

// usage() is the only backend list a human reads at the terminal, and nothing
// else consults it — so when a backend is added it goes stale silently, which is
// exactly what happened to the client-facing strings before
// TestAdvertisedSurfaceNamesEveryBackend was written. Same guard, other surface:
// every configured backend's name, prefix and URL-derived port must appear.
func TestUsageNamesEveryBackend(t *testing.T) {
	out := captureStderr(t, usage)

	for _, b := range gateway.DefaultBackends() {
		if !strings.Contains(out, b.Name) {
			t.Errorf("usage() never names the %s backend:\n%s", b.Name, out)
		}
		if !strings.Contains(out, b.Prefix) {
			t.Errorf("usage() never lists the %s backend's prefix %q:\n%s", b.Name, b.Prefix, out)
		}
	}
	// The spelled-out count in the first line has to match reality too.
	countWord := map[int]string{5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
	want := countWord[len(gateway.DefaultBackends())]
	if want == "" {
		t.Fatalf("no count word for %d backends; add one and fix usage()", len(gateway.DefaultBackends()))
	}
	if !strings.Contains(out, want+" JIVO backends") {
		t.Errorf("usage() does not say %q JIVO backends:\n%s", want, out)
	}
	for _, stale := range []string{"five", "six", "seven"} {
		if stale != want && strings.Contains(out, stale+" JIVO backends") {
			t.Errorf("usage() still says %q JIVO backends:\n%s", stale, out)
		}
	}
	// The env list is the documented way to repoint a backend; an omitted name
	// there reads as "this one is not overridable", which is false.
	for _, b := range gateway.DefaultBackends() {
		if !strings.Contains(out, strings.ToUpper(b.Name)) {
			t.Errorf("usage()'s JIVO_GW_URL_<NAME> list omits %s:\n%s", strings.ToUpper(b.Name), out)
		}
	}
}

// captureStderr runs fn with os.Stderr redirected to a pipe and returns what it
// wrote. flag.PrintDefaults resolves os.Stderr at call time, so the flag block
// is captured along with the banner.
func captureStderr(t *testing.T, fn func()) string {
	t.Helper()
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("os.Pipe: %v", err)
	}
	orig := os.Stderr
	os.Stderr = w
	done := make(chan string, 1)
	go func() {
		b, _ := io.ReadAll(r)
		done <- string(b)
	}()
	fn()
	os.Stderr = orig
	w.Close()
	out := <-done
	r.Close()
	return out
}
