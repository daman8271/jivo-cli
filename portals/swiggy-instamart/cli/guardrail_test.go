package main

import (
	"net/http"
	"strings"
	"testing"
)

// TestGuardrailBlocksWrites is LAYER 3 of the read-only guardrail: it asserts the
// transport refuses every endpoint the study classified as a write, an export or
// UNKNOWN — including the Swiggy-specific traps that a naive verb-based rule would
// wave through.
func TestGuardrailBlocksWrites(t *testing.T) {
	blocked := []struct {
		method, url, why string
	}{
		// session endpoints — G9. Rotating the refresh token breaks the live human
		// session AND the production keepalive cron.
		{http.MethodPost, "https://ozone-idp-brands-im-kba.swiggy.com/v1/token/refresh", "token rotation"},
		{http.MethodPost, "https://ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signOut", "logout"},
		{http.MethodPost, "https://ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signInWithOTP", "login"},
		{http.MethodPost, "https://ozone-idp-brands-im-kba.swiggy.com/v1/accounts/sendVerificationCode", "mails a real OTP"},
		{http.MethodPost, "https://ozone-idp-brands-im-kba.swiggy.com/v1/accounts/createAuthURI", "login initiate"},

		// report GENERATION — G2: creates a row and burns the account's quota.
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/sales/report", "generate sales report"},
		{http.MethodPost, "https://partner-api.swiggy.com/instamart/v1/report/initiate-sales-report", "generate"},
		{http.MethodPost, "https://partner-api.swiggy.com/instamart/v1/report/initiate-bdpo-report", "generate"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/discounts/report", "generate"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/report", "generate"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/document/batch/generate", "generate"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/document/merged/generate", "generate"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/v1/generate_signed_url", "upload enabler"},

		// appointment booking — mutates a real delivery slot.
		{http.MethodPost, "https://picker.swiggy.com/api/v1/fc-appointment/batch-create", "books a delivery"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/fc-appointment/batch-cancel", "cancels a delivery"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/fc-appointment/batch-reschedule", "reschedules"},

		// indent accept/reject — accepts or rejects a real purchase indent.
		{http.MethodPost, "https://picker.swiggy.com/api/v1/external/indent/accept", "accepts an indent"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/external/indent/reject", "rejects an indent"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/external/indent/item/update", "edits an indent"},

		// campaigns spend real money.
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/campaign", "create/update campaign"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/campaign/batch", "bulk bid/budget update"},
		{http.MethodPost, "https://partner-api.swiggy.com/instamart/v1/campaign/create", "create campaign"},
		{http.MethodPost, "https://partner-api.swiggy.com/instamart/v1/campaign/deactivate", "deactivate campaign"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/campaign/resume", "resume campaign"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/release-order/approve", "approves an RO"},

		// catalogue writes against JIVO's own product data.
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/v1/create_spin_change_request", "catalogue write"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/v1/reassign_spin_change_request", "catalogue write"},

		// THE TRAPS — these look readable and are still refused.
		{http.MethodGet, "https://partner-api.swiggy.com/instamart/v1/creative/get-upload-info-v2",
			"a GET named GET_S3_UPLOAD_INFO whose only purpose is to enable an upload"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/batch/submit",
			"constant is BULK_DOWNLOAD_PO_DATA but submit enqueues a job"},
		{http.MethodPut, "https://brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/disable",
			"disable"},

		// mutating HTTP verbs are refused unconditionally, whatever the path.
		{http.MethodPut, "https://brand-portal-service-http.swiggy.com/api/v1/campaigns", "PUT"},
		{http.MethodDelete, "https://brand-portal-service-http.swiggy.com/api/v1/campaigns", "DELETE"},
		{http.MethodPatch, "https://brand-portal-service-http.swiggy.com/api/v1/campaigns", "PATCH"},

		// UNKNOWN-classified endpoints stay denied (G1).
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/ads-chat/chat",
			"UNKNOWN — posting a prompt would create a conversation row"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/v1/transition_spin_change_request", "UNKNOWN"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/discounting/v1/tnc/acceptance", "UNKNOWN"},

		// a host that is not in the study at all.
		{http.MethodGet, "https://partner-staging.swiggy.com/api/v1/campaigns", "staging — documented, never called"},
		{http.MethodGet, "https://partner.swiggy.com/food/", "the restaurant portal, not ours"},
	}

	for _, b := range blocked {
		if err := forbiddenRequest(b.method, b.url); err == nil {
			t.Errorf("expected BLOCKED (%s): %s %s — but it was allowed", b.why, b.method, b.url)
		}
	}
}

// TestGuardrailAllowsProvenReads asserts the guardrail does not block the reads
// the study proved — a dead command is a bug too.
func TestGuardrailAllowsProvenReads(t *testing.T) {
	allowed := []struct{ method, url string }{
		// proven live during the walk
		{http.MethodGet, "https://partner-api.swiggy.com/time"},
		{http.MethodGet, "https://partner-api.swiggy.com/instamart/v1/configs"},
		{http.MethodGet, "https://partner-api.swiggy.com/instamart/v1/account/list"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/account/permissions"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/sales/metric"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/sales/filters"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/campaigns"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/v1/list_spins"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/searchPurchaseOrder"},
		{http.MethodPost, "https://picker.swiggy.com/api/v1/listAllFCs"},
		{http.MethodGet, "https://picker.swiggy.com/api/v1/category/list"},
		{http.MethodGet, "https://picker.swiggy.com/api/v1/vendorPortal/accessInfo"},

		// the report LIST endpoints are reads even though the sibling generate is not.
		// This is the pair most easily got wrong, so it is asserted explicitly.
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/sales/reports"},
		{http.MethodPost, "https://brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/report/list"},
		{http.MethodPost, "https://partner-api.swiggy.com/instamart/v1/report/list-sales"},

		// a query string must not defeat the allowlist lookup
		{http.MethodGet, "https://partner-api.swiggy.com/instamart/v1/configs?x=1&y=2"},
	}
	for _, a := range allowed {
		if err := forbiddenRequest(a.method, a.url); err != nil {
			t.Errorf("expected ALLOWED: %s %s — got %v", a.method, a.url, err)
		}
	}
}

// TestTemplateMatchingIsSegmentExact guards the one place the allowlist could
// accidentally widen: an id placeholder must consume exactly one segment.
func TestTemplateMatchingIsSegmentExact(t *testing.T) {
	// the inventory contains .../conversations/{conversation_id}/messages/list
	if !isAllowedRead("brand-portal-service-http.swiggy.com",
		"/api/v1/ads-chat/conversations/abc123/messages/list") {
		t.Error("a concrete id should match the templated read path")
	}
	// ...but the template must not become a prefix wildcard
	if isAllowedRead("brand-portal-service-http.swiggy.com",
		"/api/v1/ads-chat/conversations/abc123/messages/list/extra") {
		t.Error("template matching leaked into a prefix match (extra segment accepted)")
	}
	if isAllowedRead("brand-portal-service-http.swiggy.com",
		"/api/v1/ads-chat/conversations/abc123") {
		t.Error("the DELETE-only conversation path must not be readable")
	}
}

// TestNoWriteVerbInAllowlist re-derives the guardrail claim from the allowlist
// itself: no allowlisted path may contain a mutating segment.
func TestNoWriteVerbInAllowlist(t *testing.T) {
	bad := []string{
		"create", "update", "delete", "remove", "submit", "approve", "reject",
		"acknowledge", "cancel", "pause", "resume", "activate", "deactivate",
		"pay", "settle", "upload", "generate", "initiate", "signout", "signin",
		"schedule", "book", "disable", "reassign", "transition",
	}
	for host, paths := range allowedReads {
		for p := range paths {
			for _, seg := range strings.Split(strings.ToLower(p), "/") {
				for _, part := range strings.FieldsFunc(seg, func(r rune) bool {
					return r == '-' || r == '_'
				}) {
					for _, b := range bad {
						if part == b {
							t.Errorf("allowlist contains a mutating segment %q: %s%s", b, host, p)
						}
					}
				}
			}
		}
	}
}

func TestAllowlistIsNotEmpty(t *testing.T) {
	if n := allowlistSize(); n < 50 {
		t.Fatalf("allowlist has only %d entries — the generator probably failed", n)
	}
}
