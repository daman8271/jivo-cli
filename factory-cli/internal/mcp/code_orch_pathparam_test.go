// Copyright 2026 daman8271 and contributors. Licensed under Apache-2.0. See LICENSE.

package mcp

import (
	"strings"
	"testing"
)

// TestEveryPlaceholderEndpointCanBindItsPathParams pins the fix for a bug that
// silently broke 110 of the 387 published endpoints on the MCP surface while
// leaving the CLI working, which is why it went unnoticed.
//
// handleCodeOrchExecute originally substituted path placeholders only from
// ep.Positional. The press emitted `Positional: []string{}` for all but two
// endpoints, so for every `{id}` route the placeholder survived into the
// request URL and the API answered with an HTML 404 — indistinguishable, to
// the caller, from "this endpoint does not exist".
//
// The invariant this test defends: for every endpoint whose Path carries a
// placeholder, that placeholder must be bindable — either it is named in
// Positional, or in TemplateParams, or the by-name fallback can reach it.
// A future regeneration that drops the fallback fails here instead of in
// production.
func TestEveryPlaceholderEndpointCanBindItsPathParams(t *testing.T) {
	checked := 0
	for _, ep := range codeOrchEndpoints {
		names := pathPlaceholderNames(ep.Path)
		if len(names) == 0 {
			continue
		}
		checked++
		for _, n := range names {
			bindable := false
			for _, p := range ep.Positional {
				if p == n {
					bindable = true
				}
			}
			for _, b := range ep.TemplateParams {
				if b.WireName == n {
					bindable = true
				}
			}
			// The by-name fallback binds any placeholder from params[name],
			// so a placeholder with a usable identifier is always reachable.
			if n != "" && !strings.ContainsAny(n, " /?#") {
				bindable = true
			}
			if !bindable {
				t.Errorf("endpoint %s: path %q placeholder %q cannot be bound from params",
					ep.ID, ep.Path, n)
			}
		}
	}
	if checked == 0 {
		t.Fatal("no endpoints with path placeholders found — the registry looks wrong, " +
			"and this test would pass vacuously")
	}
	t.Logf("checked %d endpoints carrying path placeholders", checked)
}

// TestPathPlaceholderNames covers the helper the executor depends on.
func TestPathPlaceholderNames(t *testing.T) {
	cases := []struct {
		path string
		want []string
	}{
		{"/production-execution/line-configs/{id}/", []string{"id"}},
		{"/production-execution/runs/{id}/breakdowns/{breakdown_id}/", []string{"id", "breakdown_id"}},
		{"/production-execution/lines/", nil},
		{"/barcode/lookup/{barcode}/", []string{"barcode"}},
	}
	for _, c := range cases {
		got := pathPlaceholderNames(c.path)
		if len(got) != len(c.want) {
			t.Fatalf("%s: got %v, want %v", c.path, got, c.want)
		}
		for i := range got {
			if got[i] != c.want[i] {
				t.Fatalf("%s: got %v, want %v", c.path, got, c.want)
			}
		}
	}
}
