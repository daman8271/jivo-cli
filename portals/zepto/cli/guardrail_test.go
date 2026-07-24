package main

import (
	"net/http"
	"testing"
	"time"
)

// TestForbiddenPath asserts the read-only guardrail blocks every write and
// allows every read — including the segment-boundary cases (scheduled vs
// schedule, amendment-requests vs request).
func TestForbiddenPath(t *testing.T) {
	blocked := []struct{ method, url string }{
		{http.MethodPost, "https://fcc.zepto.co.in/api/v1/po/cancel"},
		{http.MethodPost, "https://fcc.zepto.co.in/api/v1/po/schedule"},
		{http.MethodPost, "https://fcc.zepto.co.in/api/v1/po/reschedule"},
		{http.MethodPost, "https://fcc.zepto.co.in/api/v1/po/unschedule"},
		{http.MethodPost, "https://fcc.zepto.co.in/api/v1/po/request-schedule"},
		{http.MethodPost, "https://fcc.zepto.co.in/api/v1/po/acknowledge"},
		{http.MethodPost, "https://auth-backend.zepto.co.in/api/v1/authorize/create/role"},
		{http.MethodPost, "https://auth-backend.zepto.co.in/api/v1/authorize/modify-access-for-modules-and-actions"},
		{http.MethodPost, "https://fcc.zepto.co.in/vms/api/v1/admin/non-trade-vendor/counterpart"},
		{http.MethodPost, "https://fcc.zepto.co.in/vendor/api/v1/ledger-upload/commit"},
		{http.MethodPost, "https://auth-backend.zepto.co.in/api/v1/auth/sign-out"},
		{http.MethodPut, "https://fcc.zepto.co.in/api/v1/po/123"},
		{http.MethodDelete, "https://fcc.zepto.co.in/api/v1/anything"},
		{http.MethodPatch, "https://fcc.zepto.co.in/api/v1/anything"},
	}
	for _, b := range blocked {
		if err := forbiddenPath(b.method, b.url); err == nil {
			t.Errorf("expected %s %s to be BLOCKED, but it was allowed", b.method, b.url)
		}
	}

	allowed := []struct{ method, url string }{
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/po/filter"},
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/po/listing-stat"},
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/po/scheduled"}, // NOT "schedule"
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/po/user/vendor-list"},
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/po/123/items"},
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/grn/123/asn-info"},
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/reports?offset=0&limit=1"},
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/reports/123/download"},
		{http.MethodGet, "https://fcc.zepto.co.in/api/v1/amendment-requests/list"}, // "requests" != verb
		// sanctioned generate endpoints pass the guardrail (command gates them):
		{http.MethodPost, "https://fcc.zepto.co.in/api/v1/reports/request"},
		{http.MethodPost, "https://fcc.zepto.co.in/ads-bff/api/v1/brands/analytics/reports"},
	}
	for _, a := range allowed {
		if err := forbiddenPath(a.method, a.url); err != nil {
			t.Errorf("expected %s %s to be ALLOWED, got: %v", a.method, a.url, err)
		}
	}
}

func TestDefaultSalesRange(t *testing.T) {
	now := time.Date(2026, 7, 24, 12, 0, 0, 0, istLoc)
	from, to := defaultSalesRange(now)
	if from != "2026-07-01" || to != "2026-07-23" {
		t.Errorf("defaultSalesRange = %q,%q want 2026-07-01,2026-07-23", from, to)
	}
}

func TestCurlHeader(t *testing.T) {
	curl := `curl 'https://fcc.zepto.co.in/api/v1/reports' -H 'authorization: eyJhbGc.payload.sig' -H 'accept: application/json'`
	if got := curlHeader(curl, "authorization"); got != "eyJhbGc.payload.sig" {
		t.Errorf("authorization = %q", got)
	}
}
