package main

import (
	"net/http"
	"strings"
	"testing"
)

// TestTransportRefusesNonGET asserts the binary cannot issue any mutating method.
func TestTransportRefusesNonGET(t *testing.T) {
	// use a real allowlisted path so ONLY the method is what's under test
	host, path := "sellercentral.amazon.in", readEndpoints[0].Path
	for _, m := range []string{http.MethodPost, http.MethodPut, http.MethodPatch, http.MethodDelete, "TRACE"} {
		if err := forbidden(m, host, path); err == nil {
			t.Errorf("expected HTTP %s to be REFUSED by the transport guard, but it passed", m)
		}
	}
	if err := forbidden(http.MethodGet, readEndpoints[0].Host, readEndpoints[0].Path); err != nil {
		t.Errorf("expected a GET to an allowlisted path to pass, got: %v", err)
	}
}

// TestNoWritePathIsReachable asserts every known write / POST-read / session
// endpoint is refused by the guardrail — they must never be reachable even by GET.
func TestNoWritePathIsReachable(t *testing.T) {
	blocked := []struct{ host, path string }{
		{"sellercentral.amazon.in", "/coupons/api/couponPromotion"},          // create coupon
		{"sellercentral.amazon.in", "/coupons/api/editCouponPromotion"},      // edit
		{"sellercentral.amazon.in", "/coupons/api/cancelCouponPromotion"},    // cancel
		{"sellercentral.amazon.in", "/abis/ajax/create-listing"},             // create listing
		{"sellercentral.amazon.in", "/abis/ajax/write-offer"},                // write offer
		{"sellercentral.amazon.in", "/myinventory/gql"},                      // READ_POST — not wired
		{"sellercentral.amazon.in", "/business-reports/api"},                 // READ_POST — not wired
		{"sellercentral.amazon.in", "/orders-api/countOrders"},              // READ_POST — not wired
		{"sellercentral.amazon.in", "/ap/signout"},                           // logout
		{"www.vendorcentral.in", "/api/retail-analytics/v1/request-report-download"}, // enqueue = write
		{"www.vendorcentral.in", "/po-api/vendor/members/po-mgmt/search/generateVendorSearchFile-v3"},
	}
	for _, b := range blocked {
		if err := forbidden(http.MethodGet, b.host, b.path); err == nil {
			t.Errorf("expected %s %s to be BLOCKED, but the guardrail allowed it", b.host, b.path)
		}
	}
}

// TestAllowlistedReadsPass asserts a sample of genuine reads are allowed.
func TestAllowlistedReadsPass(t *testing.T) {
	n := 0
	for _, e := range readEndpoints {
		if err := forbidden(http.MethodGet, e.Host, e.Path); err != nil {
			// a wired READ endpoint must never be refused by the guardrail
			t.Errorf("wired READ endpoint refused: %s %s → %v", e.Host, e.Path, err)
		}
		n++
	}
	if n == 0 {
		t.Fatal("no read endpoints wired — allowlist is empty")
	}
}

// TestNoWriteVerbInAllowlist asserts the generated allowlist itself contains no
// write-verb path segment (belt-and-braces over the classifier).
func TestNoWriteVerbInAllowlist(t *testing.T) {
	for _, e := range readEndpoints {
		if e.Class != "READ" && e.Class != "READ_FILE" {
			t.Errorf("non-read class %q wired: %s", e.Class, e.Path)
		}
		lp := strings.ToLower(e.Path)
		if i := strings.IndexByte(lp, '?'); i >= 0 {
			lp = lp[:i]
		}
		for _, seg := range strings.Split(lp, "/") {
			for _, part := range strings.Split(seg, "-") {
				if writeVerbs[part] {
					t.Errorf("write verb %q found in wired allowlist path %s", part, e.Path)
				}
			}
		}
	}
}
