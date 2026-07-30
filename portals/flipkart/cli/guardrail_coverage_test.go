package main

import (
	"net/http"
	"strings"
	"testing"
)

// LAYER-3 coverage test: every wired command must be a READ/READ_FILE endpoint,
// declared GET, and must itself pass the read-only path guard. If a future
// regeneration ever admits a WRITE/EXPORT/UNKNOWN row, this fails the build.
func TestEveryWiredEndpointIsRead(t *testing.T) {
	if len(registry) == 0 {
		t.Fatal("registry is empty")
	}
	for _, e := range registry {
		if e.Method != http.MethodGet {
			t.Errorf("%s/%s wired with method %q — only GET may be wired", e.Group, e.Name, e.Method)
		}
		if e.Class != "READ" && e.Class != "READ_FILE" {
			t.Errorf("%s/%s has class %q — only READ/READ_FILE may be wired", e.Group, e.Name, e.Class)
		}
		u := "https://" + e.Host + e.Path
		if err := forbiddenPath(http.MethodGet, u); err != nil {
			t.Errorf("%s/%s (%s) fails the read-only guard: %v", e.Group, e.Name, u, err)
		}
	}
}

// No wired path may contain a mutating verb segment.
func TestNoWriteVerbInAnyWiredPath(t *testing.T) {
	for _, e := range registry {
		for _, seg := range strings.Split(e.Path, "/") {
			if seg == "" || strings.HasPrefix(seg, "{") {
				continue
			}
			if segmentIsWrite(seg) {
				t.Errorf("wired path %s contains write segment %q", e.Path, seg)
			}
		}
	}
}
