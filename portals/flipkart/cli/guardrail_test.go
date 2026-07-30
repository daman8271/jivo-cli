package main

import (
	"net/http"
	"testing"
)

// LAYER-1/2 test: the transport refuses every non-GET verb, and the path guard
// refuses any GET whose path looks like a write.
func TestGuardMethodRefusesNonGET(t *testing.T) {
	for _, m := range []string{http.MethodPost, http.MethodPut, http.MethodPatch, http.MethodDelete, http.MethodHead} {
		if err := guardMethod(m); err == nil {
			t.Errorf("method %s must be refused by the transport guard", m)
		}
	}
	if err := guardMethod(http.MethodGet); err != nil {
		t.Errorf("GET must be allowed, got %v", err)
	}
}

func TestForbiddenPathBlocksWrites(t *testing.T) {
	blocked := []string{
		"https://vendorhub.flipkart.com/vendor/user-management/user-activation/activate",
		"https://vendorhub.flipkart.com/vendor/user-management/user-activation/suspend",
		"https://vendorhub.flipkart.com/vendor/cataloging/create-fsn",
		"https://vendorhub.flipkart.com/vendor/feeds/upload-feed-file",
		"https://seller.flipkart.com/napi/createProductV2/create-variants",
		"https://seller.flipkart.com/napi/metrics/bizReport/report/generateReport",
		"https://seller.flipkart.com/napi/sfx/address/add",
		"https://vendorhub.flipkart.com/logout",
	}
	for _, u := range blocked {
		if err := forbiddenPath(http.MethodGet, u); err == nil {
			t.Errorf("expected BLOCKED: %s", u)
		}
	}
	// even GET is refused if wrongly asked with a non-GET verb
	if err := forbiddenPath(http.MethodPost, "https://seller.flipkart.com/napi/printing/certificate"); err == nil {
		t.Error("POST must be blocked even for a read path")
	}
}

func TestForbiddenPathAllowsReads(t *testing.T) {
	allowed := []string{
		"https://seller.flipkart.com/napi/metrics/bizReport/reportCategories",
		"https://seller.flipkart.com/napi/printing/certificate",
		"https://vendorhub.flipkart.com/vendor/user-management/vendor-list",
		"https://vendorhub.flipkart.com/vendor/purchase-orders",
		"https://vendorhub.flipkart.com/vendor/user-management/users/active",
		"https://vendorhub.flipkart.com/vendor/config/sale-config",
	}
	for _, u := range allowed {
		if err := forbiddenPath(http.MethodGet, u); err != nil {
			t.Errorf("expected ALLOWED: %s got %v", u, err)
		}
	}
}
