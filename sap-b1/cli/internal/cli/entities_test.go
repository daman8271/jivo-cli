package cli

import (
	"bytes"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	"sapb1/internal/catalog"
	"sapb1/internal/errs"
)

// execRoot runs the full command tree with args and captures stdout, mirroring
// a real `sapb1 ...` invocation (offline commands only, so no network).
func execRoot(t *testing.T, args ...string) (string, error) {
	t.Helper()
	root := NewRootCmd()
	var buf bytes.Buffer
	root.SetOut(&buf)
	root.SetErr(&buf)
	root.SetArgs(args)
	err := root.Execute()
	return buf.String(), err
}

func TestEntitiesSearch(t *testing.T) {
	out, err := execRoot(t, "entities", "--search", "invoice")
	if err != nil {
		t.Fatalf("entities --search invoice: %v", err)
	}
	if !strings.Contains(out, "Invoices") {
		t.Errorf("expected Invoices in output:\n%s", out)
	}
	// The filter is a name substring: every listed service name must contain it.
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "SERVICE") || strings.HasSuffix(line, "service(s).") {
			continue
		}
		name := strings.Fields(line)[0]
		if !strings.Contains(strings.ToLower(name), "invoice") {
			t.Errorf("row %q does not match search 'invoice'", name)
		}
	}
}

func TestEntitiesReadOnlyJSON(t *testing.T) {
	out, err := execRoot(t, "entities", "--read-only", "--json")
	if err != nil {
		t.Fatalf("entities --read-only --json: %v", err)
	}
	var rows []map[string]interface{}
	if err := json.Unmarshal([]byte(out), &rows); err != nil {
		t.Fatalf("output not valid JSON: %v\n%s", err, out)
	}
	if len(rows) == 0 {
		t.Fatal("expected some readable services")
	}
	for _, r := range rows {
		if r["readable"] != true {
			t.Errorf("--read-only returned a non-readable service: %v", r["service"])
		}
	}
}

func TestFilterServices(t *testing.T) {
	all := catalog.Services()
	// read-only filter keeps only readable services.
	ro := filterServices(all, "", true)
	for _, s := range ro {
		if !s.IsReadable() {
			t.Errorf("filterServices(read-only) let through non-readable %q", s.Service)
		}
	}
	if len(ro) >= len(all) {
		t.Errorf("read-only filter should shrink the set (%d vs %d)", len(ro), len(all))
	}
	// search is case-insensitive.
	lower := filterServices(all, "orders", false)
	upper := filterServices(all, "ORDERS", false)
	if len(lower) == 0 || len(lower) != len(upper) {
		t.Errorf("search should be case-insensitive: %d vs %d", len(lower), len(upper))
	}
}

func TestOpsLookup(t *testing.T) {
	out, err := execRoot(t, "ops", "Orders")
	if err != nil {
		t.Fatalf("ops Orders: %v", err)
	}
	if !strings.Contains(out, "GET") || !strings.Contains(out, "Orders") {
		t.Errorf("ops Orders missing expected content:\n%s", out)
	}
	// Case-insensitive exact match works too.
	if _, err := execRoot(t, "ops", "orders"); err != nil {
		t.Errorf("ops orders (lowercase) should match: %v", err)
	}
}

func TestOpsUnknownSuggests(t *testing.T) {
	out, err := execRoot(t, "ops", "Orderz")
	if err == nil {
		t.Fatal("expected an error for an unknown service")
	}
	var usageErr *errs.UsageError
	if !errors.As(err, &usageErr) {
		t.Fatalf("expected *errs.UsageError (exit 2), got %T: %v", err, err)
	}
	if !strings.Contains(usageErr.Msg, "did you mean") {
		t.Errorf("expected a suggestion in the error, got: %s", usageErr.Msg)
	}
	if !strings.Contains(usageErr.Msg, "Orders") {
		t.Errorf("expected Orders among suggestions, got: %s", usageErr.Msg)
	}
	_ = out
}

func TestCatalogStats(t *testing.T) {
	out, err := execRoot(t, "catalog", "stats")
	if err != nil {
		t.Fatalf("catalog stats: %v", err)
	}
	if !strings.Contains(out, "498") {
		t.Errorf("expected 498 services in stats output:\n%s", out)
	}
	if !strings.Contains(out, "1950") {
		t.Errorf("expected 1950 operations in stats output:\n%s", out)
	}
}
