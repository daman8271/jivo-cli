package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// The four GST hosts, one cookie jar across all of them (API.md §Hosts).
// gstr2b.gst.gov.in is easy to miss: the GSTR-2B statement lives on its own host.
const (
	hostServices = "services.gst.gov.in"
	hostReturn   = "return.gst.gov.in"
	hostPayment  = "payment.gst.gov.in"
	hostGSTR2B   = "gstr2b.gst.gov.in"
)

// gstDomain is the one registrable domain this binary talks to. All four hosts
// are under it and they share a single cookie jar (API.md §Hosts), which is why
// a host-only Set-Cookie is widened to this — see client.go cookieDomainFor.
const gstDomain = "gst.gov.in"

// allHosts is the session/cookie scope and the set the guard will accept.
var allHosts = []string{hostServices, hostReturn, hostPayment, hostGSTR2B}

// Methods as plain strings, deliberately NOT net/http constants: guard.go must
// not import net/http, so that the AST test can pin "only client.go talks HTTP".
const (
	methodGET  = "GET"
	methodPOST = "POST"
)

// browserUA is the User-Agent every request carries. GST sits behind an F5
// BIG-IP/ASM WAF that bounces non-browser clients (RECON.md:18-21). This exact
// string is the one from the captured live login (fixtures/login-xhr-full.json)
// — i.e. the only UA verified to have reached the portal's captcha check.
//
// It MUST stay identical to the UserAgent inside the mFP fingerprint below: the
// portal ships both in the same login request and a mismatch is the obvious
// thing for a fingerprint check to notice.
const browserUA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/145.0.7632.6 Safari/537.36"

// acceptJSON is what the portal's own XHRs send.
const acceptJSON = "application/json, text/plain, */*"

// hostReferer is the page each host's JSON APIs are called from in the browser.
// Requesting them with no gst.gov.in Referer earns a 302 to
// /services/error/accessdenied even with a valid session (API.md §Session).
var hostReferer = map[string]string{
	hostServices: "https://services.gst.gov.in/services/auth/fowelcome",
	hostReturn:   "https://return.gst.gov.in/returns/auth/dashboard",
	hostPayment:  "https://payment.gst.gov.in/payment/auth/ledger/cashledger",
	hostGSTR2B:   "https://gstr2b.gst.gov.in/gstr2b/auth/gstr2b/summary",
}

// loginReferer is used for the pre-auth calls, which are made from the login page.
const loginReferer = "https://services.gst.gov.in/services/login"

// Endpoint is one allowlisted row. Query and Body are the ONLY keys the client
// will put on the wire: an unknown key is a guard error, not a passthrough. That
// is what stops a future "helpful" &action=submit.
type Endpoint struct {
	Name    string
	Method  string
	Host    string
	Path    string   // allowlist key; {fy}-style placeholders are filled by Params
	Params  []string // path placeholder names, in order
	Query   []string // permitted query keys
	Body    []string // permitted JSON body keys (POST rows only)
	Referer string   // overrides hostReferer when the portal calls it elsewhere
	Note    string
}

// Endpoint names — referenced by commands so a typo is a compile error.
const (
	epLoginPage      = "auth.loginpage"
	epCaptcha        = "auth.captcha"
	epAuthenticate   = "auth.authenticate"
	epUstatus        = "auth.ustatus"
	epKeepalive      = "auth.keepalive"
	epProfile        = "profile.detail"
	epFilingSnapshot = "returns.filingsnapshot"
	epDropdown       = "returns.dropdown"
	epRoleStatus     = "returns.rolestatus"
	epFormDetails    = "returns.formdetails"
	epEfiledReturns  = "returns.efiled"
	epGSTR3BSummary  = "gstr3b.summary"
	epGSTR3BAutoPop  = "gstr3b.autopop"
	epGSTR2BData     = "gstr2b.getdata"
	epGSTR2BUserDtls = "gstr2b.userdtls"
	epCashBalance    = "ledger.cashbalance"
	epCashDetails    = "ledger.cashdetls"
	epITCBalance     = "ledger.itcbalance"
	epITCDetails     = "ledger.itcdtls"
	epChallanSearch  = "ledger.challans"
	epLiability      = "ledger.liability"
	epLiabilityOther = "ledger.liability-other"
	epGSTR1Count     = "gstr1.count"
	epGSTR1Invoice   = "gstr1.invoice"
	epGSTR2ACtin     = "gstr2a.suppliers"
	epGSTR2AB2B      = "gstr2a.b2b"
	epCompareUser    = "compare.userdetail"
	epCompareData    = "compare.data"
	epMasterForms    = "masters.forms"
	epMasterFY       = "masters.fy"
	epMasterMonths   = "masters.months"
	epMasterQuarters = "masters.quarters"
	epMasterHalves   = "masters.halfyears"
	epMasterStates   = "masters.states"
)

// endpoints is the whole allowlist. Every row was observed live and is recorded
// in ../API.md; rows whose request shape is still open (GSTR-1 sections, GSTR-2A,
// comparison, liability register, downloads) are deliberately ABSENT — their
// commands print "not captured live yet" rather than guessing a contract.
//
// THREE POSTs exist in this table and they are all read-shaped:
//   - auth.authenticate — the login itself, the one sanctioned side effect;
//   - returns.efiled    — the ARN register search (the portal has no GET for it);
//   - profile.detail    — the profile read, which the portal issues as POST {}.
//
// Nothing else may ever be a POST, and there is no PUT/PATCH/DELETE anywhere in
// this binary.
var endpoints = []Endpoint{
	{
		Name: epLoginPage, Method: methodGET, Host: hostServices, Path: "/services/login",
		Referer: loginReferer,
		Note:    "login page — fetched only to mint the pre-auth cookie jar the captcha is bound to",
	},
	{
		Name: epCaptcha, Method: methodGET, Host: hostServices, Path: "/services/captcha",
		Query: []string{"rnd"}, Referer: loginReferer,
		Note: "182x50 PNG, 6 digits; a fresh GET is free and does not count as an attempt",
	},
	{
		Name: epAuthenticate, Method: methodPOST, Host: hostServices, Path: "/services/authenticate",
		Body:    []string{"username", "password", "captcha", "mFP", "deviceID", "type"},
		Referer: loginReferer,
		Note:    "THE only sanctioned side effect; always HTTP 200, success = {\"message\":\"auth\"}",
	},
	{
		Name: epUstatus, Method: methodGET, Host: hostServices, Path: "/services/api/ustatus",
		Note: "who am I: {gstin,bname,stcd,utype,regType,…} — doctor's live read",
	},
	{
		Name: epKeepalive, Method: methodGET, Host: hostPayment, Path: "/payment/auth/api/keepalive",
		Note: "the portal's own idle-timer reset (API.md §Session) — the SPA polls it; " +
			"read-shaped, returns no business data. Used by `auth keepalive` to hold a sitting open.",
	},
	{
		Name: epProfile, Method: methodPOST, Host: hostServices, Path: "/services/auth/profile/detail",
		Note: "POST with an empty body {}; contains PII (contacted{name,mobNum,email})",
	},
	{
		Name: epFilingSnapshot, Method: methodGET, Host: hostServices, Path: "/returns/auth/api/filingsnapshot",
		Note: "last-5-periods GSTR-1/3B grid; ISD registrations return a different shape. " +
			"HOST IS services, NOT return: the same path on return.gst.gov.in is an F5-ASM " +
			"\"Request Rejected\" for a plain client under every header combination (API.md, D3).",
	},
	{
		Name: epDropdown, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/dropdown",
		Note: "financial years and their MMYYYY period codes",
	},
	{
		Name: epRoleStatus, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/rolestatus",
		Query: []string{"rtn_prd"},
		Note:  "per-form tile status for one period: FIL/NF + due_dt",
	},
	{
		Name: epFormDetails, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/formdetails",
		Query: []string{"rtn_prd", "rtn_typ"},
		Note:  "ARN + fil_dt per form per period — the reconciliation key",
	},
	{
		Name: epEfiledReturns, Method: methodPOST, Host: hostReturn, Path: "/returns/auth/api/efiledReturns",
		Body: []string{"fy", "rfp", "qtr", "mth", "rtntp"},
		Note: "ARN register search; rfp is the literal word Monthly|Quarterly|Annual|Half Yearly",
	},
	{
		Name: epGSTR3BSummary, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr3b/summary",
		Query: []string{"rtn_prd"},
		Note:  "the filed 3B: sup_details, inter_sup, itc_elg, intr_ltfee, tt_val",
	},
	{
		Name: epGSTR3BAutoPop, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr3b/getr1r3bliab",
		Query: []string{"retPeriod"},
		Note:  "GSTR-1 vs 3B auto-population (note the camelCase param — it is not rtn_prd)",
	},
	{
		Name: epGSTR2BData, Method: methodGET, Host: hostGSTR2B, Path: "/gstr2b/auth/api/gstr2b/getdata",
		Query: []string{"rtnprd"},
		Note:  "document-level ITC by supplier; GTR2B-002 when 2B is not generated for that period",
	},
	{
		Name: epGSTR2BUserDtls, Method: methodGET, Host: hostGSTR2B, Path: "/gstr2b/auth/api/gstr2b/getuserdtls",
		Query: []string{"rtnprd", "fy"},
		Note:  "{gstin,lgnm,trdnm} for the 2B header",
	},
	{
		Name: epCashBalance, Method: methodGET, Host: hostPayment, Path: "/payment/auth/api/cashbalance",
		Note: "electronic cash ledger balance by head",
	},
	{
		Name: epCashDetails, Method: methodGET, Host: hostPayment, Path: "/payment/auth/api/cashdetls",
		Query: []string{"fdate", "tdate"},
		Note:  "cash ledger statement; dates are dd/mm/yyyy",
	},
	{
		Name: epITCBalance, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/itcbalance",
		Note: "electronic credit ledger balance; its `dt` field is garbage (16/02/0027) — ignore it",
	},
	{
		Name: epITCDetails, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/itcdtls",
		Query: []string{"fdate", "tdate"},
		Note:  "credit ledger statement; dates are dd/mm/yyyy",
	},
	{
		Name: epChallanSearch, Method: methodGET, Host: hostPayment, Path: "/payment/auth/api/searcharnusngdate",
		Query: []string{"fromdate", "todate"},
		Note:  "challan ARNs in a date range; LG9221 when there are none",
	},
	{
		Name: epLiability, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/retdtl",
		Query: []string{"fdate", "to_dt", "gstin"},
		Note: "liability register Part-I (return related); fdate/to_dt are MMYYYY, not dates. " +
			"The portal's own SPA sends gstin=undefined and the server resolves it from the " +
			"session — we replay that verbatim rather than invent a parameter (API.md, D5c).",
	},
	{
		Name: epLiabilityOther, Method: methodGET, Host: hostPayment, Path: "/payment/auth/api/liabdetails",
		Query: []string{"fdate", "tdate", "staystatus", "demandid"},
		Note:  "liability register Part-II (other than return); dates are ISO here, unlike cashdetls",
	},
	{
		Name: epGSTR1Count, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr1/totalsummarycount",
		Query: []string{"rtn_prd", "sec_name"},
		Note: "GSTR-1 section counts; with sec_name it breaks them down per counterparty. " +
			"sec_name=B2B returned GSTN-EXEC1003 (a portal-side Java error) on 2026-08-21.",
	},
	{
		Name: epGSTR1Invoice, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr1/invoice",
		Query: []string{"rtn_prd", "sec_name", "uploaded_by", "ctin", "inum"},
		Note: "the one list API behind every GSTR-1 section; no paging params exist, so a big " +
			"section is scoped by ctin. Empty = RETWEB_07, which is an answer, not a failure.",
	},
	{
		Name: epGSTR2ACtin, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr2a/ctin",
		Query: []string{"rtn_prd", "section_name"},
		Note:  "GSTR-2A supplier list for a section: {rc, cpty[{stin,cname,rc,cfs,filingDateGstr1}]}",
	},
	{
		Name: epGSTR2AB2B, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr2a/b2b",
		Query: []string{"rtn_prd", "ctin"},
		Note:  "GSTR-2A B2B documents for one supplier, GSTN-standard {b2b:[{inv:[…]}]}",
	},
	{
		Name: epCompareUser, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr3bvs1/getuserdetail",
		Note: "header for the comparison report: {gstin, legalName, liab_cd, fp, regtype}",
	},
	{
		Name: epCompareData, Method: methodGET, Host: hostReturn, Path: "/returns/auth/api/gstr3bvs1/getdata",
		Query: []string{"form_type", "fy"},
		Note: "the portal's own GSTR-1-vs-3B / 2A-vs-3B tables for a whole FY in one call. " +
			"fy is the FY START YEAR (2026 = FY 2026-27), not the 2026-27 label.",
	},
	{Name: epMasterForms, Method: methodGET, Host: hostReturn, Path: "/master/gstrs/A", Note: "return types + filing day"},
	{Name: epMasterFY, Method: methodGET, Host: hostReturn, Path: "/master/fy", Note: "financial years"},
	{Name: epMasterMonths, Method: methodGET, Host: hostReturn, Path: "/master/fy/{fy}", Params: []string{"fy"}, Note: "months of a financial year"},
	{Name: epMasterQuarters, Method: methodGET, Host: hostReturn, Path: "/master/qtrs/{fy}", Params: []string{"fy"}, Note: "quarters of a financial year"},
	{Name: epMasterHalves, Method: methodGET, Host: hostReturn, Path: "/master/hy/{fy}", Params: []string{"fy"}, Note: "half-years of a financial year"},
	{Name: epMasterStates, Method: methodGET, Host: hostReturn, Path: "/master/allstates", Note: "state list"},
}

// endpointIndex is the by-name lookup, built once.
var endpointIndex = func() map[string]Endpoint {
	m := make(map[string]Endpoint, len(endpoints))
	for _, e := range endpoints {
		m[e.Name] = e
	}
	return m
}()

// lookup returns the allowlisted endpoint with this name.
func lookup(name string) (Endpoint, error) {
	e, ok := endpointIndex[name]
	if !ok {
		return Endpoint{}, errGuard("no endpoint named %q is in the allowlist", name)
	}
	return e, nil
}

// referer is the Referer header this endpoint must carry.
func (e Endpoint) referer() string {
	if e.Referer != "" {
		return e.Referer
	}
	return hostReferer[e.Host]
}

// resolvePath fills the {name} placeholders in the path template. A missing or
// unsafe value is a guard error — a path segment may never contain / or ...
func (e Endpoint) resolvePath(params map[string]string) (string, error) {
	p := e.Path
	for _, name := range e.Params {
		v, ok := params[name]
		if !ok || v == "" {
			return "", errGuard("endpoint %s needs the path parameter %q", e.Name, name)
		}
		if strings.ContainsAny(v, "/?#%") || strings.Contains(v, "..") {
			return "", errGuard("path parameter %s=%q is not a plain segment", name, v)
		}
		p = strings.ReplaceAll(p, "{"+name+"}", v)
	}
	if strings.Contains(p, "{") {
		return "", errGuard("endpoint %s has unfilled path parameters: %s", e.Name, p)
	}
	return p, nil
}

// ---- login fingerprint ----------------------------------------------------

// deviceFingerprint mirrors the mFP blob the portal's own login page builds and
// posts alongside the credentials (API.md §Session). We send a fixed, realistic
// one rather than inventing a shape: the UserAgent inside it is the SAME
// constant the transport sends, which is the whole point of pinning it here.
type deviceFingerprint struct {
	VERSION string `json:"VERSION"`
	MFP     struct {
		Browser struct {
			UserAgent     string `json:"UserAgent"`
			Vendor        string `json:"Vendor"`
			VendorSubID   string `json:"VendorSubID"`
			BuildID       string `json:"BuildID"`
			CookieEnabled bool   `json:"CookieEnabled"`
		} `json:"Browser"`
		Screen struct {
			FullHeight int `json:"FullHeight"`
			AvlHeight  int `json:"AvlHeight"`
			FullWidth  int `json:"FullWidth"`
			AvlWidth   int `json:"AvlWidth"`
			ColorDepth int `json:"ColorDepth"`
			PixelDepth int `json:"PixelDepth"`
		} `json:"Screen"`
		System struct {
			Platform       string `json:"Platform"`
			SystemLanguage string `json:"systemLanguage"`
			Timezone       int    `json:"Timezone"`
		} `json:"System"`
	} `json:"MFP"`
	ExternalIP string `json:"ExternalIP"`
	MESC       struct {
		Mesc string `json:"mesc"`
	} `json:"MESC"`
}

// mfpBlob is the stringified fingerprint sent as the login body's mFP field.
func mfpBlob() string {
	var f deviceFingerprint
	f.VERSION = "2.1"
	f.MFP.Browser.UserAgent = browserUA
	f.MFP.Browser.Vendor = "Google Inc."
	f.MFP.Browser.VendorSubID = ""
	f.MFP.Browser.BuildID = "20030107"
	f.MFP.Browser.CookieEnabled = true
	f.MFP.Screen.FullHeight = 720
	f.MFP.Screen.AvlHeight = 720
	f.MFP.Screen.FullWidth = 1280
	f.MFP.Screen.AvlWidth = 1280
	f.MFP.Screen.ColorDepth = 24
	f.MFP.Screen.PixelDepth = 24
	f.MFP.System.Platform = "MacIntel"
	f.MFP.System.SystemLanguage = "en-US"
	f.MFP.System.Timezone = -330 // IST, as JavaScript's getTimezoneOffset reports it
	f.ExternalIP = ""
	f.MESC.Mesc = "mi=2;cd=150;id=30;mesc=3482565;mesc=3743007"
	b, err := json.Marshal(f)
	if err != nil {
		return ""
	}
	return string(b)
}

// endpointURL renders an endpoint's canonical URL, for display in errors and in
// the agent envelope's `endpoint` field.
func endpointURL(name string) string {
	e, err := lookup(name)
	if err != nil {
		return name
	}
	return fmt.Sprintf("https://%s%s", e.Host, e.Path)
}
