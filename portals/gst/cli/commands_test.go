package main

import (
	"encoding/json"
	"net/http"
	"strings"
	"testing"
)

// commands_test.go pins the wire contract of every command: which host, which
// path, which query keys and values, which body. These are the assertions that
// catch "somebody renamed a flag and the request quietly changed shape" — which
// on a portal that answers RET11403 to anything it dislikes is otherwise a
// half-hour of confused debugging.

// wired is one command's expected request.
type wired struct {
	name  string
	args  []string
	host  string
	path  string
	query map[string]string
	body  string // exact JSON body, for the POST rows
}

func TestEveryCommandSendsTheRequestItPromises(t *testing.T) {
	cases := []wired{
		{
			name: "returns calendar", args: []string{"returns", "calendar"},
			// services, NOT return: the return host is WAF-blocked for this path
			host: hostServices, path: "/returns/auth/api/filingsnapshot",
		},
		{
			name: "returns periods", args: []string{"returns", "periods"},
			host: hostReturn, path: "/returns/auth/api/dropdown",
		},
		{
			name: "returns status", args: []string{"returns", "status", "--period", "072026"},
			host: hostReturn, path: "/returns/auth/api/rolestatus",
			query: map[string]string{"rtn_prd": "072026"},
		},
		{
			name: "returns status --form", args: []string{"returns", "status", "--period", "072026", "--form", "gstr-3b"},
			host: hostReturn, path: "/returns/auth/api/formdetails",
			query: map[string]string{"rtn_prd": "072026", "rtn_typ": "GSTR3B"},
		},
		{
			name: "returns filed", args: []string{"returns", "filed", "--fy", "2026-27", "--form", "GSTR1"},
			host: hostReturn, path: "/returns/auth/api/efiledReturns",
			body: `{"fy":"2026-27","mth":null,"qtr":null,"rfp":"Monthly","rtntp":"GSTR1"}`,
		},
		{
			name: "returns filed --freq Annual", args: []string{"returns", "filed", "--fy", "2024-25", "--form", "gstr9", "--freq", "annual"},
			host: hostReturn, path: "/returns/auth/api/efiledReturns",
			body: `{"fy":"2024-25","mth":null,"qtr":null,"rfp":"Annual","rtntp":"GSTR9"}`,
		},
		{
			name: "ledger cash", args: []string{"ledger", "cash"},
			host: hostPayment, path: "/payment/auth/api/cashbalance",
		},
		{
			name: "ledger cash --from/--to", args: []string{"ledger", "cash", "--from", "2026-04-01", "--to", "2026-08-21"},
			host: hostPayment, path: "/payment/auth/api/cashdetls",
			query: map[string]string{"fdate": "01/04/2026", "tdate": "21/08/2026"},
		},
		{
			name: "ledger credit", args: []string{"ledger", "credit"},
			host: hostReturn, path: "/returns/auth/api/itcbalance",
		},
		{
			name: "ledger credit --from/--to", args: []string{"ledger", "credit", "--from", "2026-04-01", "--to", "2026-08-21"},
			host: hostReturn, path: "/returns/auth/api/itcdtls",
			query: map[string]string{"fdate": "01/04/2026", "tdate": "21/08/2026"},
		},
		{
			name: "ledger challans", args: []string{"ledger", "challans", "--from", "2026-04-01", "--to", "2026-08-21"},
			host: hostPayment, path: "/payment/auth/api/searcharnusngdate",
			query: map[string]string{"fromdate": "01/04/2026", "todate": "21/08/2026"},
		},
		{
			// Part-I takes MMYYYY, and the portal's own page sends gstin=undefined
			name: "ledger liability", args: []string{"ledger", "liability", "--from", "2026-04-01", "--to", "2026-07-31"},
			host: hostReturn, path: "/returns/auth/api/retdtl",
			query: map[string]string{"fdate": "042026", "to_dt": "072026", "gstin": "undefined"},
		},
		{
			// …and Part-II takes ISO dates. The portal is not consistent; we are.
			name: "ledger liability-other", args: []string{"ledger", "liability-other", "--from", "2026-04-01", "--to", "2026-07-31"},
			host: hostPayment, path: "/payment/auth/api/liabdetails",
			query: map[string]string{"fdate": "2026-04-01", "tdate": "2026-07-31"},
		},
		{
			name: "gstr3b summary", args: []string{"gstr3b", "summary", "--period", "072026"},
			host: hostReturn, path: "/returns/auth/api/gstr3b/summary",
			query: map[string]string{"rtn_prd": "072026"},
		},
		{
			name: "gstr3b autopop", args: []string{"gstr3b", "autopop", "--period", "072026"},
			host: hostReturn, path: "/returns/auth/api/gstr3b/getr1r3bliab",
			query: map[string]string{"retPeriod": "072026"}, // camelCase, deliberately
		},
		{
			name: "gstr3b status", args: []string{"gstr3b", "status", "--period", "072026"},
			host: hostReturn, path: "/returns/auth/api/formdetails",
			query: map[string]string{"rtn_prd": "072026", "rtn_typ": "GSTR3B"},
		},
		{
			name: "gstr1 section", args: []string{"gstr1", "section", "--period", "072026", "--section", "cdnr"},
			host: hostReturn, path: "/returns/auth/api/gstr1/totalsummarycount",
			query: map[string]string{"rtn_prd": "072026", "sec_name": "CDNR"},
		},
		{
			name: "gstr1 docs", args: []string{"gstr1", "docs", "--period", "072026", "--section", "B2B", "--ctin", "24aaaaa0000a1zp"},
			host: hostReturn, path: "/returns/auth/api/gstr1/invoice",
			query: map[string]string{"rtn_prd": "072026", "sec_name": "B2B", "uploaded_by": "SU", "ctin": "24AAAAA0000A1ZP"},
		},
		{
			name: "gstr1 docs --section B2CS", args: []string{"gstr1", "docs", "--period", "072026", "--section", "B2CS"},
			host: hostReturn, path: "/returns/auth/api/gstr1/invoice",
			query: map[string]string{"rtn_prd": "072026", "sec_name": "B2CS", "uploaded_by": "OE"},
		},
		{
			name: "gstr1 docs --section DOC", args: []string{"gstr1", "docs", "--period", "072026", "--section", "DOC"},
			host: hostReturn, path: "/returns/auth/api/gstr1/invoice",
			query: map[string]string{"rtn_prd": "072026", "sec_name": "DOC", "inum": "DOC"},
		},
		{
			name: "gstr2a status", args: []string{"gstr2a", "status", "--period", "072026"},
			host: hostReturn, path: "/returns/auth/api/formdetails",
			query: map[string]string{"rtn_prd": "072026", "rtn_typ": "GSTR2A"},
		},
		{
			name: "gstr2a suppliers", args: []string{"gstr2a", "suppliers", "--period", "072026"},
			host: hostReturn, path: "/returns/auth/api/gstr2a/ctin",
			query: map[string]string{"rtn_prd": "072026", "section_name": "B2B"},
		},
		{
			name: "gstr2a docs", args: []string{"gstr2a", "docs", "--period", "072026", "--ctin", "24AAAAA0000A1ZP"},
			host: hostReturn, path: "/returns/auth/api/gstr2a/b2b",
			query: map[string]string{"rtn_prd": "072026", "ctin": "24AAAAA0000A1ZP"},
		},
		{
			// fy is the FY START YEAR here, not the label
			name: "compare", args: []string{"compare", "--fy", "2026-27"},
			host: hostReturn, path: "/returns/auth/api/gstr3bvs1/getdata",
			query: map[string]string{"form_type": "allreports", "fy": "2026"},
		},
		{
			name: "profile", args: []string{"profile"},
			host: hostServices, path: "/services/auth/profile/detail",
			body: `{}`,
		},
		{
			name: "masters forms", args: []string{"masters", "forms"},
			host: hostReturn, path: "/master/gstrs/A",
		},
		{
			name: "auth whoami", args: []string{"auth", "whoami"},
			host: hostServices, path: "/services/api/ustatus",
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			useTempStateDir(t)
			writeTestEnv(t)
			seedSession(t, "06AAAAA0000A1Z0")
			fp := newFakePortal(t)
			fp.handle(tc.host, tc.path, func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				w.Write([]byte(`{"status":1,"gstin":"06AAAAA0000A1Z0","data":{}}`))
			})

			args := append(append([]string{}, tc.args...), "--state", "haryana")
			if _, err := runCLI(t, args...); err != nil {
				t.Fatalf("%s: %v", tc.name, err)
			}
			hits := 0
			var hit recordedRequest
			for _, h := range fp.Hits {
				if h.Path == tc.path && h.Host == tc.host {
					hits++
					hit = h
				}
			}
			if hits == 0 {
				t.Fatalf("nothing reached %s%s; the portal saw %s", tc.host, tc.path, describeHits(fp.Hits))
			}
			// exact query: no extras, no omissions
			got := map[string]string{}
			for k, v := range hit.Query {
				got[k] = v[0]
			}
			if tc.query == nil {
				tc.query = map[string]string{}
			}
			for k, want := range tc.query {
				if got[k] != want {
					t.Errorf("query %s = %q want %q (full query: %v)", k, got[k], want, got)
				}
			}
			for k := range got {
				if _, ok := tc.query[k]; !ok {
					t.Errorf("unexpected query parameter %s=%q on the wire", k, got[k])
				}
			}
			if tc.body != "" {
				if hit.Method != "POST" {
					t.Errorf("method = %s want POST", hit.Method)
				}
				if strings.TrimSpace(hit.Body) != tc.body {
					t.Errorf("body =\n  %s\nwant\n  %s", hit.Body, tc.body)
				}
			} else if hit.Method != "GET" {
				t.Errorf("method = %s want GET", hit.Method)
			}
			// every read carries the host's Referer and the pinned UA
			if ref := hit.Headers.Get("Referer"); ref != hostReferer[tc.host] {
				t.Errorf("Referer = %q want %q", ref, hostReferer[tc.host])
			}
			if ua := hit.Headers.Get("User-Agent"); ua != browserUA {
				t.Errorf("User-Agent = %q", ua)
			}
		})
	}
}

func describeHits(hits []recordedRequest) string {
	if len(hits) == 0 {
		return "nothing at all"
	}
	var out []string
	for _, h := range hits {
		out = append(out, h.Method+" "+h.Host+h.Path)
	}
	return strings.Join(out, ", ")
}

// TestCompositeCommandsMakeBothCalls — gstr2b summary and gstr1 summary each
// answer a whole question, which takes two reads.
func TestCompositeCommandsMakeBothCalls(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostGSTR2B, "/gstr2b/auth/api/gstr2b/getuserdtls", "gstr2b-userdtls-072026.json")
	fp.json(hostGSTR2B, "/gstr2b/auth/api/gstr2b/getdata", "HR-gstr2b-getdata-072026.json")

	out, err := runCLI(t, "gstr2b", "summary", "--period", "072026", "--state", "hr", "--agent")
	if err != nil {
		t.Fatalf("gstr2b summary: %v", err)
	}
	var env struct {
		OK    bool `json:"ok"`
		Count int  `json:"count"`
		Data  struct {
			Period    string          `json:"period"`
			FY        string          `json:"fy"`
			Generated bool            `json:"generated"`
			UserDtls  json.RawMessage `json:"userdtls"`
			Data      json.RawMessage `json:"data"`
		} `json:"data"`
	}
	if err := json.Unmarshal([]byte(out), &env); err != nil {
		t.Fatalf("envelope: %v\n%s", err, out)
	}
	if !env.OK || !env.Data.Generated || env.Data.Period != "072026" || env.Data.FY != "2026-27" {
		t.Errorf("envelope = %+v", env.Data)
	}
	if env.Count != 2 {
		t.Errorf("count = %d want 2 (two supplier documents in the fixture)", env.Count)
	}
	if len(env.Data.UserDtls) == 0 || len(env.Data.Data) == 0 {
		t.Error("gstr2b summary must carry both the header and the statement")
	}
	// both calls, and the FY was derived not asked for
	var sawUser, sawData bool
	for _, h := range fp.Hits {
		switch h.Path {
		case "/gstr2b/auth/api/gstr2b/getuserdtls":
			sawUser = true
			if h.Query.Get("rtnprd") != "072026" || h.Query.Get("fy") != "2026-27" {
				t.Errorf("userdtls query = %v", h.Query)
			}
		case "/gstr2b/auth/api/gstr2b/getdata":
			sawData = true
			if h.Query.Get("rtnprd") != "072026" {
				t.Errorf("getdata query = %v", h.Query)
			}
		}
	}
	if !sawUser || !sawData {
		t.Error("gstr2b summary did not make both calls")
	}
}

func TestGSTR1SummaryCombinesFilingAndCounts(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/formdetails", "formdetails-gstr3b-072026.json")
	fp.handle(hostReturn, "/returns/auth/api/gstr1/totalsummarycount", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(`{"status":1,"data":{"sec_count":[{"sec_name":"B2B","proc_cnt":878,"pen_cnt":0,"err_cnt":0},{"sec_name":"HSN","proc_cnt":12,"pen_cnt":0,"err_cnt":0}]}}`))
	})

	out, err := runCLI(t, "gstr1", "summary", "--period", "072026", "--state", "hr", "--agent")
	if err != nil {
		t.Fatalf("gstr1 summary: %v", err)
	}
	var env struct {
		Count int `json:"count"`
		Data  struct {
			Filing   json.RawMessage `json:"filing"`
			Sections json.RawMessage `json:"sections"`
		} `json:"data"`
	}
	if err := json.Unmarshal([]byte(out), &env); err != nil {
		t.Fatalf("envelope: %v\n%s", err, out)
	}
	if len(env.Data.Filing) == 0 || len(env.Data.Sections) == 0 {
		t.Fatal("gstr1 summary must carry both the filing status and the section counts")
	}
	if env.Count != 890 {
		t.Errorf("count = %d want 890 (878 + 12)", env.Count)
	}
	var sawForm bool
	for _, h := range fp.Hits {
		if h.Path == "/returns/auth/api/formdetails" {
			sawForm = true
			if h.Query.Get("rtn_typ") != "GSTR1" {
				t.Errorf("gstr1 summary asked formdetails for %q", h.Query.Get("rtn_typ"))
			}
		}
	}
	if !sawForm {
		t.Error("gstr1 summary never asked for the filing status")
	}
}

// TestEmptyPortalAnswersAreNotFailures — the RET13510 / LG9221 / GTR2B-002 /
// RETWEB_07 family. A nil filer must exit 0, or `snapshot --all` dies on the
// first quiet registration.
func TestEmptyPortalAnswersAreNotFailures(t *testing.T) {
	cases := []struct {
		name, fixture, host, path string
		args                      []string
	}{
		{"filed returns, none", "err-RET13510.json", hostReturn, "/returns/auth/api/efiledReturns",
			[]string{"returns", "filed", "--fy", "2026-27", "--form", "GSTR1"}},
		{"no challans", "err-LG9221.json", hostPayment, "/payment/auth/api/searcharnusngdate",
			[]string{"ledger", "challans", "--from", "2026-04-01", "--to", "2026-08-21"}},
		{"2B not generated", "err-GTR2B-002.json", hostGSTR2B, "/gstr2b/auth/api/gstr2b/getdata",
			[]string{"gstr2b", "summary", "--period", "082026"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			useTempStateDir(t)
			writeTestEnv(t)
			seedSession(t, "06AAAAA0000A1Z0")
			fp := newFakePortal(t)
			fp.json(tc.host, tc.path, tc.fixture)
			fp.json(hostGSTR2B, "/gstr2b/auth/api/gstr2b/getuserdtls", "gstr2b-userdtls-072026.json")

			out, err := runCLI(t, append(tc.args, "--state", "hr", "--agent")...)
			if err != nil {
				t.Fatalf("an empty answer must exit 0: %v", err)
			}
			var env struct {
				OK    bool `json:"ok"`
				Count int  `json:"count"`
			}
			if err := json.Unmarshal([]byte(out), &env); err != nil {
				t.Fatalf("envelope: %v\n%s", err, out)
			}
			if !env.OK || env.Count != 0 {
				t.Errorf("want ok=true count=0, got ok=%v count=%d\n%s", env.OK, env.Count, out)
			}
		})
	}
}

// TestBadArgumentsNeverReachThePortal — validation is local, so a typo costs
// nothing on a live statutory system.
func TestBadArgumentsNeverReachThePortal(t *testing.T) {
	bad := [][]string{
		{"returns", "status", "--period", "2026-07"},
		{"returns", "status", "--period", "132026"},
		{"returns", "filed", "--fy", "2026-27", "--form", "GSTR-42"},
		{"returns", "filed", "--fy", "2026-27", "--freq", "M"},
		{"gstr3b", "summary", "--period", "july"},
		{"gstr1", "docs", "--period", "072026", "--section", "B2X"},
		{"gstr2a", "docs", "--period", "072026"}, // no --ctin
		{"ledger", "challans"},                   // a required range with neither end
		{"ledger", "cash", "--to", "2026-08-01"}, // --to without --from
		{"ledger", "cash", "--from", "2026-08-01", "--to", "2026-07-01"},
		{"compare", "--fy", "2026-28"},
		{"snapshot", "--fy", "2026-27"}, // no --out
	}
	for _, args := range bad {
		t.Run(strings.Join(args, " "), func(t *testing.T) {
			useTempStateDir(t)
			writeTestEnv(t)
			seedSession(t, "06AAAAA0000A1Z0")
			fp := newFakePortal(t)
			if _, err := runCLI(t, append(args, "--state", "hr")...); err == nil {
				t.Error("this must be refused")
			}
			if fp.hitCount() != 0 {
				t.Errorf("it reached the portal anyway: %s", describeHits(fp.Hits))
			}
		})
	}
}

// TestHumanSummaryGoesToStderrNotStdout — stdout stays parseable JSON.
func TestHumanSummaryGoesToStderrNotStdout(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.json(hostReturn, "/returns/auth/api/itcbalance", "HR-itcbalance.json")
	_ = fp

	var out, errb strings.Builder
	app := &App{out: &out, errw: &errb}
	root := newRootCmdWithApp(app)
	root.SetOut(&out)
	root.SetErr(&errb)
	root.SetArgs([]string{"ledger", "credit", "--state", "hr"})
	if err := root.Execute(); err != nil {
		t.Fatalf("ledger credit: %v", err)
	}
	if !strings.Contains(errb.String(), "4,33,72,582") || !strings.Contains(errb.String(), "4.34 Cr") {
		t.Errorf("the human INR line is missing from stderr:\n%s", errb.String())
	}
	var body map[string]any
	if err := json.Unmarshal([]byte(out.String()), &body); err != nil {
		t.Errorf("stdout is not clean JSON: %v\n%s", err, out.String())
	}
	if strings.Contains(out.String(), "Cr)") {
		t.Error("the human summary leaked into stdout")
	}
}

// TestKeepaliveTellsPortalDownFromSessionDead is the regression guard for the
// one mistake that would make an unattended keeper thrash.
//
// The GST portal takes its authenticated API offline overnight (observed live
// 2026-09-02 00:15 IST: services/api/ustatus, return. and payment. all 503). If
// keepalive reports that as "session expired", gstd on the VPS holder will try
// to log in — and the login flow is 503 too, so it burns attempts all night for
// nothing. 503 must mean WAIT (exit 6, verdict "unavailable"); only a real
// session failure may mean LOG IN (exit 4, verdict "expired").
func TestKeepaliveTellsPortalDownFromSessionDead(t *testing.T) {
	for _, tc := range []struct {
		name        string
		status      int
		wantVerdict string
		wantExit    int
	}{
		{"maintenance window", http.StatusServiceUnavailable, "unavailable", exitAPI},
		{"bad gateway", http.StatusBadGateway, "unavailable", exitAPI},
		{"session actually gone", http.StatusForbidden, "expired", exitAuth},
	} {
		t.Run(tc.name, func(t *testing.T) {
			useTempStateDir(t)
			writeTestEnv(t)
			seedSession(t, "06AAAAA0000A1Z0")
			fp := newFakePortal(t)
			fp.handle(hostServices, "/services/api/ustatus", func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tc.status)
			})

			out, err := runCLI(t, "auth", "keepalive", "--state", "hr", "--agent")
			if err == nil {
				t.Fatalf("keepalive should have failed on HTTP %d", tc.status)
			}
			if got := exitCodeFor(err); got != tc.wantExit {
				t.Errorf("exit code = %d, want %d (err: %v)", got, tc.wantExit, err)
			}
			var env struct {
				Data []struct {
					Verdict string `json:"verdict"`
					OK      bool   `json:"ok"`
				} `json:"data"`
			}
			if err := json.Unmarshal([]byte(out), &env); err != nil {
				t.Fatalf("envelope: %v\n%s", err, out)
			}
			if len(env.Data) != 1 {
				t.Fatalf("want 1 row, got %d", len(env.Data))
			}
			if env.Data[0].Verdict != tc.wantVerdict {
				t.Errorf("verdict = %q, want %q", env.Data[0].Verdict, tc.wantVerdict)
			}
			if env.Data[0].OK {
				t.Error("row should not be ok")
			}
		})
	}
}

// TestKeepaliveNeverLogsIn — keepalive must never touch the login flow, however
// dead the session looks. Reviving a jar needs a captcha, and a silent re-login
// would also kill whatever human is on that username.
func TestKeepaliveNeverLogsIn(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	seedSession(t, "06AAAAA0000A1Z0")
	fp := newFakePortal(t)
	fp.handle(hostServices, "/services/api/ustatus", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusForbidden)
	})

	_, _ = runCLI(t, "auth", "keepalive", "--state", "hr", "--agent")

	for _, h := range fp.Hits {
		if h.Path == "/services/authenticate" || h.Path == "/services/captcha" || h.Path == "/services/login" {
			t.Fatalf("keepalive reached the login flow: %s %s", h.Method, h.Path)
		}
	}
}
