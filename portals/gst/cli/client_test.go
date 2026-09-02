package main

import (
	"net/http"
	"net/url"
	"strings"
	"testing"
)

// TestDoReadHeaders: every request must look like the portal's own XHR — full
// cookie jar (including the TS* WAF cookies), a browser User-Agent, the host's
// Referer, and Accept: application/json. Missing any of these earns a 302 to
// /services/error/accessdenied from the F5 in front of GST (API.md §Session).
func TestDoReadHeaders(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/itcbalance", "HR-itcbalance.json")

	c := newClient(testRegistration())
	if _, err := c.do(epITCBalance, nil, nil, nil); err != nil {
		t.Fatalf("do: %v", err)
	}
	hit := fp.lastHit(t)
	if hit.Method != http.MethodGet {
		t.Errorf("method = %s want GET", hit.Method)
	}
	if hit.Host != hostReturn {
		t.Errorf("Host header = %s want %s", hit.Host, hostReturn)
	}
	if got := hit.Headers.Get("User-Agent"); got != browserUA {
		t.Errorf("User-Agent = %q want the pinned browser UA", got)
	}
	if got := hit.Headers.Get("Accept"); got != acceptJSON {
		t.Errorf("Accept = %q want %q", got, acceptJSON)
	}
	if got := hit.Headers.Get("Referer"); got != hostReferer[hostReturn] {
		t.Errorf("Referer = %q want %q", got, hostReferer[hostReturn])
	}
	names := map[string]bool{}
	for _, ck := range hit.Cookies {
		names[ck.Name] = true
	}
	for _, want := range []string{"AuthToken", "TS0134d082", "TS01255980"} {
		if !names[want] {
			t.Errorf("cookie %s was not sent — the WAF keys on the TS* pair", want)
		}
	}
}

// The GSTR-2B host is a fourth host that is easy to forget; it must get its own
// Referer, and the shared jar.
func TestFourthHostIsWired(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostGSTR2B, "/gstr2b/auth/api/gstr2b/getdata", "HR-gstr2b-getdata-072026.json")

	c := newClient(testRegistration())
	res, err := c.do(epGSTR2BData, nil, url.Values{"rtnprd": {"072026"}}, nil)
	if err != nil {
		t.Fatalf("do: %v", err)
	}
	if res.Empty {
		t.Fatal("a real 2B body must not be classified as empty")
	}
	hit := fp.lastHit(t)
	if hit.Host != hostGSTR2B {
		t.Errorf("Host = %s want %s", hit.Host, hostGSTR2B)
	}
	if got := hit.Headers.Get("Referer"); got != hostReferer[hostGSTR2B] {
		t.Errorf("Referer = %q want the gstr2b page", got)
	}
	if got := hit.Query.Get("rtnprd"); got != "072026" {
		t.Errorf("rtnprd = %q", got)
	}
}

// A 302 to /services/error/accessdenied is the WAF refusing us. It must surface
// as an auth error (exit 4) — never as a mysterious HTML body.
func TestAccessDeniedRedirectIsAuthError(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.redirectTo(hostReturn, "/returns/auth/api/itcbalance", "https://services.gst.gov.in/services/error/accessdenied")

	c := newClient(testRegistration())
	_, err := c.do(epITCBalance, nil, nil, nil)
	if err == nil {
		t.Fatal("a redirect to accessdenied must be an error")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit code = %d want %d (auth); err = %v", exitCodeFor(err), exitAuth, err)
	}
}

// The same for a bounce back to the login page.
func TestLoginRedirectIsAuthError(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.redirectTo(hostReturn, "/returns/auth/api/itcbalance", "https://services.gst.gov.in/services/login")

	c := newClient(testRegistration())
	if _, err := c.do(epITCBalance, nil, nil, nil); exitCodeFor(err) != exitAuth {
		t.Errorf("exit code = %d want %d (auth); err = %v", exitCodeFor(err), exitAuth, err)
	}
}

// F5 ASM's "Request Rejected" page comes back with HTTP 200 and an HTML body.
func TestRequestRejectedHTMLIsAuthError(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/itcbalance", "request-rejected.html")

	c := newClient(testRegistration())
	_, err := c.do(epITCBalance, nil, nil, nil)
	if err == nil {
		t.Fatal("an HTML body where JSON was expected must be an error")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit code = %d want %d (auth); err = %v", exitCodeFor(err), exitAuth, err)
	}
	if !strings.Contains(err.Error(), "Request Rejected") && !strings.Contains(err.Error(), "HTML") {
		t.Errorf("the error should say what came back, got: %v", err)
	}
}

// A real portal error envelope is exit 6 — the portal answered, and said no.
func TestPortalErrorEnvelopeToExit6(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/efiledReturns", "err-RET11403.json")

	c := newClient(testRegistration())
	_, err := c.do(epEfiledReturns, nil, nil, map[string]any{"fy": "2025-26", "rfp": "M", "rtntp": "GSTR9"})
	if err == nil {
		t.Fatal("RET11403 must be an error")
	}
	if exitCodeFor(err) != exitAPI {
		t.Errorf("exit code = %d want %d (API)", exitCodeFor(err), exitAPI)
	}
	if !strings.Contains(err.Error(), "RET11403") || !strings.Contains(err.Error(), "Invalid API Request") {
		t.Errorf("the error should carry the portal's own code and message, got: %v", err)
	}
}

// RET13510 / LG9221 / GTR2B-002 are ANSWERS ("nothing to report"), not failures.
// A nil-filer registration must not abort a multi-GSTIN run.
func TestEmptyCodesAreOkCountZero(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/efiledReturns", "err-RET13510.json")
	fp.json(hostPayment, "/payment/auth/api/searcharnusngdate", "err-LG9221.json")
	fp.json(hostGSTR2B, "/gstr2b/auth/api/gstr2b/getdata", "err-GTR2B-002.json")

	c := newClient(testRegistration())
	cases := []struct {
		ep    string
		query url.Values
		body  map[string]any
		code  string
	}{
		{epEfiledReturns, nil, map[string]any{"fy": "2026-27"}, "RET13510"},
		{epChallanSearch, url.Values{"fromdate": {"01/04/2026"}, "todate": {"21/08/2026"}}, nil, "LG9221"},
		{epGSTR2BData, url.Values{"rtnprd": {"072026"}}, nil, "GTR2B-002"},
	}
	for _, tc := range cases {
		res, err := c.do(tc.ep, nil, tc.query, tc.body)
		if err != nil {
			t.Errorf("%s: %s must be an empty answer, not an error: %v", tc.ep, tc.code, err)
			continue
		}
		if !res.Empty {
			t.Errorf("%s: expected Empty=true for %s", tc.ep, tc.code)
		}
		if res.Note == "" || !strings.Contains(res.Note, tc.code) {
			t.Errorf("%s: note should carry the portal's message and code, got %q", tc.ep, res.Note)
		}
	}

	// and the agent envelope renders it as ok/count 0/data null
	var app App
	var sb strings.Builder
	app.out, app.errw, app.Agent, app.JSON = &sb, &strings.Builder{}, true, true
	res, _ := c.do(epGSTR2BData, nil, url.Values{"rtnprd": {"072026"}}, nil)
	if err := app.emit("gstr2b summary", "06AAAAA0000A1Z0", endpointURL(epGSTR2BData), res, nil); err != nil {
		t.Fatal(err)
	}
	out := sb.String()
	for _, want := range []string{`"ok": true`, `"count": 0`, `"data": null`, `"note"`} {
		if !strings.Contains(out, want) {
			t.Errorf("agent envelope for an empty answer is missing %s:\n%s", want, out)
		}
	}
}

// The guard runs BEFORE the socket. If a caller invents a query key, the portal
// must never hear about it.
func TestUnknownQueryKeyNeverOpensSocket(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/itcdtls", "HR-itcdtls-fy2627.json")

	c := newClient(testRegistration())
	_, err := c.do(epITCDetails, nil, url.Values{"fdate": {"01/04/2026"}, "action": {"submit"}}, nil)
	if err == nil {
		t.Fatal("an unknown query key must be refused")
	}
	if exitCodeFor(err) != exitNetwork {
		t.Errorf("guard refusals exit 5 (nothing was sent), got %d", exitCodeFor(err))
	}
	if fp.hitCount() != 0 {
		t.Fatalf("THE GUARD LEAKED: %d request(s) reached the portal", fp.hitCount())
	}

	// same for an unknown endpoint name and an unknown body key
	if _, err := c.do("returns.invented", nil, nil, nil); err == nil {
		t.Error("an endpoint that is not in the table must be refused")
	}
	if _, err := c.do(epEfiledReturns, nil, nil, map[string]any{"fy": "2026-27", "action": "file"}); err == nil {
		t.Error("an unknown body key must be refused")
	}
	if fp.hitCount() != 0 {
		t.Fatalf("THE GUARD LEAKED: %d request(s) reached the portal", fp.hitCount())
	}
}

// 429 is a stop sign, not a retry prompt (CRITIQUE: never loop on a statutory portal).
func TestRateLimitIsApiErrorAndNotRetried(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.handle(hostReturn, "/returns/auth/api/itcbalance", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Retry-After", "120")
		w.WriteHeader(http.StatusTooManyRequests)
		w.Write([]byte(`{"status":0,"error":{"errorCode":"TOOMANY","message":"rate limited"}}`))
	})
	c := newClient(testRegistration())
	_, err := c.do(epITCBalance, nil, nil, nil)
	if exitCodeFor(err) != exitAPI {
		t.Errorf("exit code = %d want %d (API)", exitCodeFor(err), exitAPI)
	}
	if fp.hitCount() != 1 {
		t.Errorf("a 429 must be sent exactly once, saw %d attempts", fp.hitCount())
	}
	if !strings.Contains(err.Error(), "120") {
		t.Errorf("the error should surface Retry-After, got: %v", err)
	}
}

// Without a session there is nothing to send; say so in the operator's language
// rather than firing an unauthenticated request at a statutory portal.
func TestNoSessionIsAuthErrorBeforeAnyRequest(t *testing.T) {
	useTempStateDir(t)
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/itcbalance", "HR-itcbalance.json")

	c := newClient(testRegistration())
	_, err := c.do(epITCBalance, nil, nil, nil)
	if exitCodeFor(err) != exitAuth {
		t.Fatalf("exit code = %d want %d (auth); err = %v", exitCodeFor(err), exitAuth, err)
	}
	if fp.hitCount() != 0 {
		t.Errorf("no session ⇒ no request; %d were sent", fp.hitCount())
	}
}

// Path parameters are filled from the table, and the request lands on the
// resolved path.
func TestPathParameterEndpoint(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/master/fy/2026-27", "master-gstrs-A.json")

	c := newClient(testRegistration())
	if _, err := c.do(epMasterMonths, map[string]string{"fy": "2026-27"}, nil, nil); err != nil {
		t.Fatalf("do: %v", err)
	}
	if got := fp.lastHit(t).Path; got != "/master/fy/2026-27" {
		t.Errorf("path = %s want /master/fy/2026-27", got)
	}
}

// Fresh Set-Cookie values (the F5 rotates TS*) are written back to the session
// file, so the next command in the sitting is not bounced.
func TestSetCookieIsPersisted(t *testing.T) {
	useTempStateDir(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.handle(hostReturn, "/returns/auth/api/itcbalance", func(w http.ResponseWriter, r *http.Request) {
		http.SetCookie(w, &http.Cookie{Name: "TS0134d082", Value: "rotated", Path: "/", Domain: ".gst.gov.in"})
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"op_tot":1}`))
	})
	c := newClient(testRegistration())
	if _, err := c.do(epITCBalance, nil, nil, nil); err != nil {
		t.Fatal(err)
	}
	s, err := loadSession("06AAAAA0000A1Z0")
	if err != nil || s == nil {
		t.Fatalf("session gone: %v", err)
	}
	for _, ck := range s.Cookies {
		if ck.Name == "TS0134d082" && ck.Value == "rotated" {
			return
		}
	}
	t.Error("the rotated WAF cookie was not written back to the session file")
}
