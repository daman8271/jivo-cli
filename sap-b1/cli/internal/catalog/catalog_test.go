package catalog

import (
	"strings"
	"testing"
)

// TestLoadCounts is the load-and-shape guarantee: the embedded catalog must
// parse cleanly and contain exactly 498 services / 1950 operations.
func TestLoadCounts(t *testing.T) {
	svcs, err := Load()
	if err != nil {
		t.Fatalf("Load() error: %v", err)
	}
	if got, want := len(svcs), 498; got != want {
		t.Errorf("services = %d, want %d", got, want)
	}

	ops := 0
	for _, s := range svcs {
		ops += len(s.Operations)
	}
	if got, want := ops, 1950; got != want {
		t.Errorf("operations = %d, want %d", got, want)
	}
}

func TestComputeStats(t *testing.T) {
	st := ComputeStats()
	if st.Services != 498 {
		t.Errorf("Stats.Services = %d, want 498", st.Services)
	}
	if st.Operations != 1950 {
		t.Errorf("Stats.Operations = %d, want 1950", st.Operations)
	}
	// The per-method breakdown must sum back to the operation total.
	sum := 0
	for _, n := range st.ByMethod {
		sum += n
	}
	if sum != st.Operations {
		t.Errorf("ByMethod sums to %d, want %d", sum, st.Operations)
	}
	if st.ByMethod["GET"] == 0 {
		t.Errorf("expected some GET operations, got 0")
	}
	if st.Readable <= 0 || st.Readable > st.Services {
		t.Errorf("Readable = %d, want 0 < n <= %d", st.Readable, st.Services)
	}
}

func TestFind(t *testing.T) {
	// Exact match.
	if _, ok := Find("Orders"); !ok {
		t.Errorf("Find(%q) miss, want hit", "Orders")
	}
	// Case-insensitive.
	if s, ok := Find("orders"); !ok || s.Service != "Orders" {
		t.Errorf("Find(%q) = %q,%v; want Orders,true", "orders", s.Service, ok)
	}
	// Trims whitespace.
	if _, ok := Find("  OrdersService  "); !ok {
		t.Errorf("Find with surrounding whitespace should still match")
	}
	// Unknown.
	if _, ok := Find("DefinitelyNotAService"); ok {
		t.Errorf("Find(bogus) unexpectedly hit")
	}
}

func TestIsReadable(t *testing.T) {
	// Orders exposes GET -> readable.
	orders, ok := Find("Orders")
	if !ok {
		t.Fatal("Orders not in catalog")
	}
	if !orders.IsReadable() {
		t.Errorf("Orders should be readable (has GET)")
	}
	// OrdersService is POST-only actions -> not readable.
	svc, ok := Find("OrdersService")
	if !ok {
		t.Fatal("OrdersService not in catalog")
	}
	if svc.IsReadable() {
		t.Errorf("OrdersService should NOT be readable (no GET)")
	}
}

func TestMethods(t *testing.T) {
	items, ok := Find("Items")
	if !ok {
		t.Fatal("Items not in catalog")
	}
	methods := items.Methods()
	// GET must come first in canonical order.
	if len(methods) == 0 || methods[0] != "GET" {
		t.Errorf("Items.Methods() = %v, want GET first", methods)
	}
	// No duplicates.
	seen := map[string]bool{}
	for _, m := range methods {
		if seen[m] {
			t.Errorf("duplicate method %q in %v", m, methods)
		}
		seen[m] = true
	}
}

func TestSuggest(t *testing.T) {
	// A near-miss typo should surface the Orders family.
	got := Suggest("Orderz", 5)
	if len(got) == 0 {
		t.Fatal("Suggest returned nothing")
	}
	found := false
	for _, name := range got {
		if strings.Contains(name, "Orders") {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("Suggest(%q) = %v, expected an Orders* name in there", "Orderz", got)
	}

	// Respects the max cap.
	if n := len(Suggest("Service", 3)); n > 3 {
		t.Errorf("Suggest returned %d, want <= 3", n)
	}

	// Empty query yields nothing.
	if got := Suggest("", 5); got != nil {
		t.Errorf("Suggest(empty) = %v, want nil", got)
	}
}
