package main

import (
	"net/http"
	"testing"
	"time"
)

// TestForbiddenPath asserts the read-only guardrail rejects every out-of-scope
// write/export and accepts the read paths. Table is drawn straight from the
// endpoint spec's "Out of scope (writes)" section.
func TestForbiddenPath(t *testing.T) {
	blocked := []struct{ method, url string }{
		{http.MethodPost, "https://www.partnersbiz.com/v1/po-amendment/process/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/client-po-details/asn-details/upsert/"},
		{http.MethodPost, "https://www.partnersbiz.com/vendor_appointment/api/v2/appointments/create/"},
		{http.MethodPost, "https://www.partnersbiz.com/vendor_appointment/api/v2/appointments/cancel/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/reports/bulk-invoice-excel/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/reports/vendor-charges-excel/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/reports/bulk-dn-download/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/reports/bulk-prn-download/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/reports/bulk-po-excel/"},
		{http.MethodPost, "https://www.partnersbiz.com/api/attributes/v1/brands-sheets/"},
		{http.MethodPost, "https://www.partnersbiz.com/api/bundlesandcombos/v1/bundles_and_combos_bf/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/client-requests/"},
		{http.MethodGet, "https://www.partnersbiz.com/v1/vis/generate-url/?aggregator=zoho"},
		{http.MethodPost, "https://www.partnersbiz.com/vendor_appointment/api/v1/courier-partner/validate/"},
		{http.MethodPost, "https://www.partnersbiz.com/vendor_appointment/api/v1/invoice/upload-s3-resource/"},
		{http.MethodPost, "https://www.partnersbiz.com/vendor_appointment/api/v1/bulk-upload-request/"},
		{http.MethodPut, "https://www.partnersbiz.com/vendor_appointment/api/v2/appointments/"},
		{http.MethodDelete, "https://www.partnersbiz.com/v1/anything/"},
	}
	for _, b := range blocked {
		if err := forbiddenPath(b.method, b.url); err == nil {
			t.Errorf("expected %s %s to be BLOCKED, but it was allowed", b.method, b.url)
		}
	}

	allowed := []struct{ method, url string }{
		{http.MethodPost, "https://www.partnersbiz.com/v1/report-requests/"},
		{http.MethodGet, "https://www.partnersbiz.com/v1/report-requests/download//123/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/get-sales-details/?offset=0&limit=50"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/client-po-details/"},
		{http.MethodGet, "https://www.partnersbiz.com/v1/get-po-details/?po_number=42"},
		{http.MethodGet, "https://www.partnersbiz.com/v1/get-entity-tabs/"},
		{http.MethodPost, "https://www.partnersbiz.com/v2/invoice/"},
		{http.MethodGet, "https://www.partnersbiz.com/api/attributes/v1/brands-sheets/?offset=0"}, // GET read is fine
		{http.MethodPost, "https://www.partnersbiz.com/v1/po-amendment/list/"},
		// the two sanctioned exports:
		{http.MethodPost, "https://www.partnersbiz.com/v1/reports/sales-details-excel/"},
		{http.MethodPost, "https://www.partnersbiz.com/v1/reports/soh-details-excel/"},
	}
	for _, a := range allowed {
		if err := forbiddenPath(a.method, a.url); err != nil {
			t.Errorf("expected %s %s to be ALLOWED, got: %v", a.method, a.url, err)
		}
	}
}

func TestCurlHeader(t *testing.T) {
	curl := `curl 'https://www.partnersbiz.com/v1/report-requests/' -H 'x-api-key: fe25a1da-abc' -H 'token: v2::deadbeef' -H 'access_token: v2::deadbeef' -H 'x-entity-id: 1117' -H 'x-entity-type: manufacturer'`
	if got := curlHeader(curl, "x-api-key"); got != "fe25a1da-abc" {
		t.Errorf("x-api-key = %q", got)
	}
	// token must match `token:` not `access_token:`
	if got := curlHeader(curl, "token"); got != "v2::deadbeef" {
		t.Errorf("token = %q", got)
	}
	if got := curlHeader(curl, "x-entity-id"); got != "1117" {
		t.Errorf("x-entity-id = %q", got)
	}
}

func TestDefaultSalesRange(t *testing.T) {
	// 2026-07-24 IST → from = 2026-07-01, to = 2026-07-23
	now := time.Date(2026, 7, 24, 12, 0, 0, 0, istLoc)
	from, to := defaultSalesRange(now)
	if from != "2026-07-01" || to != "2026-07-23" {
		t.Errorf("defaultSalesRange = %q,%q want 2026-07-01,2026-07-23", from, to)
	}
}
