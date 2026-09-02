package main

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// A 1x1 PNG. Content-type detection only looks at the magic bytes, so this is
// enough to stand in for the portal's 182x50 captcha.
var tinyPNG = []byte{
	0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a,
	0x00, 0x00, 0x00, 0x0d, 'I', 'H', 'D', 'R',
	0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
	0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4, 0x89,
}

// loginPortal wires the three pre-auth routes plus ustatus. authBody is what
// POST /services/authenticate answers with.
func loginPortal(t *testing.T, authBody string) *fakePortal {
	t.Helper()
	loginPOSTs = 0
	t.Cleanup(func() { loginPOSTs = 0 })

	fp := newFakePortal(t)
	fp.handle(hostServices, "/services/login", func(w http.ResponseWriter, r *http.Request) {
		http.SetCookie(w, &http.Cookie{Name: "AuthToken", Value: "pre-auth-placeholder", Path: "/"})
		http.SetCookie(w, &http.Cookie{Name: "TS0134d082", Value: "waf-1", Path: "/"})
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte("<!DOCTYPE html><html><body>login</body></html>"))
	})
	fp.handle(hostServices, "/services/captcha", func(w http.ResponseWriter, r *http.Request) {
		http.SetCookie(w, &http.Cookie{Name: "CaptchaCookie", Value: "bound-to-this-jar", Path: "/"})
		w.Header().Set("Content-Type", "image/png")
		w.Write(tinyPNG)
	})
	fp.handle(hostServices, "/services/authenticate", func(w http.ResponseWriter, r *http.Request) {
		http.SetCookie(w, &http.Cookie{Name: "AuthToken", Value: "real-token-after-login", Path: "/"})
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(authBody))
	})
	fp.json(hostServices, "/services/api/ustatus", "ustatus.json")
	return fp
}

const loginOK = `{"url":null,"message":"auth","successCode":null}`

// runCLIWithStdin drives the tree with a canned answer waiting on stdin, which
// is what makes the interactive captcha prompt testable.
func runCLIWithStdin(t *testing.T, stdin string, args ...string) (string, string, error) {
	t.Helper()
	var out, errb strings.Builder
	app := &App{out: &out, errw: &errb, in: strings.NewReader(stdin)}
	root := newRootCmdWithApp(app)
	root.SetOut(&out)
	root.SetErr(&errb)
	root.SetArgs(args)
	err := root.Execute()
	return out.String(), errb.String(), err
}

// TestAuthCaptchaWritesPNGAndPersistsThePreLoginJar — the first half of the
// two-step login. The jar has to survive to the next process or the captcha the
// operator just read is worthless.
func TestAuthCaptchaWritesPNGAndPersistsThePreLoginJar(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	loginPortal(t, loginOK)
	png := filepath.Join(t.TempDir(), "c.png")

	out, err := runCLI(t, "auth", "captcha", "--state", "haryana", "--out", png)
	if err != nil {
		t.Fatalf("auth captcha: %v", err)
	}
	if !strings.Contains(out, png) {
		t.Errorf("auth captcha did not print the image path:\n%s", out)
	}
	b, err := os.ReadFile(png)
	if err != nil {
		t.Fatalf("captcha png: %v", err)
	}
	if string(b) != string(tinyPNG) {
		t.Error("the PNG on disk is not what the portal served")
	}

	s, err := loadPendingSession("06AAAAA0000A1Z0")
	if err != nil || s == nil {
		t.Fatalf("no pre-login jar saved: %v", err)
	}
	if s.Stage != stagePreLogin {
		t.Errorf("stage = %q want %q", s.Stage, stagePreLogin)
	}
	var names []string
	for _, c := range s.Cookies {
		names = append(names, c.Name)
	}
	for _, want := range []string{"AuthToken", "TS0134d082", "CaptchaCookie"} {
		if !contains(names, want) {
			t.Errorf("the pre-login jar is missing %s (it has %v) — the captcha is bound to that cookie", want, names)
		}
	}
	// and the image must NOT be inside the repo
	if strings.Contains(png, "portals/gst/cli") {
		t.Error("the captcha landed inside the checkout")
	}
}

// TestLoginPostsTheExactBodyExactlyOnce is the contract test for the one
// sanctioned side effect: the URL, the method, the headers, the body keys, and
// above all the count.
func TestLoginPostsTheExactBodyExactlyOnce(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, loginOK)

	if _, err := runCLI(t, "auth", "captcha", "--state", "haryana", "--out", filepath.Join(t.TempDir(), "c.png")); err != nil {
		t.Fatalf("auth captcha: %v", err)
	}
	out, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", "123456")
	if err != nil {
		t.Fatalf("auth login: %v", err)
	}
	if !strings.Contains(out, "logged in: 06AAAAA0000A1Z0") {
		t.Errorf("login did not confirm the registration:\n%s", out)
	}

	posts := 0
	var body, ctype, referer, ua string
	var cookieNames []string
	for _, h := range fp.Hits {
		if h.Path == "/services/authenticate" {
			posts++
			if h.Method != "POST" {
				t.Errorf("authenticate was a %s", h.Method)
			}
			body = h.Body
			ctype = h.Headers.Get("Content-Type")
			referer = h.Headers.Get("Referer")
			ua = h.Headers.Get("User-Agent")
			for _, c := range h.Cookies {
				cookieNames = append(cookieNames, c.Name)
			}
		}
	}
	if posts != 1 {
		t.Fatalf("POST /services/authenticate happened %d times, want exactly 1", posts)
	}
	for _, want := range []string{`"username":"jivotest729"`, `"captcha":"123456"`, `"deviceID":null`, `"type":"username"`, `"mFP":"`} {
		if !strings.Contains(body, want) {
			t.Errorf("login body is missing %s", want)
		}
	}
	if !strings.Contains(body, `"password":`) {
		t.Error("login body has no password field at all")
	}
	if ctype != "application/json;charset=utf-8" {
		t.Errorf("Content-Type = %q", ctype)
	}
	if referer != loginReferer {
		t.Errorf("Referer = %q want %q", referer, loginReferer)
	}
	if ua != browserUA {
		t.Errorf("User-Agent = %q", ua)
	}
	if !contains(cookieNames, "CaptchaCookie") {
		t.Errorf("the authenticate POST did not carry CaptchaCookie (%v) — it would be answering a different image", cookieNames)
	}
	// the jar was promoted and now holds the post-login token
	s, _ := loadSession("06AAAAA0000A1Z0")
	if s == nil || s.Stage != stageAuthenticated {
		t.Fatal("the session was not promoted to authenticated")
	}
	for _, c := range s.Cookies {
		if c.Name == "AuthToken" && c.Value != "real-token-after-login" {
			t.Errorf("AuthToken was not replaced with the post-login value")
		}
	}
}

// TestLoginInteractivePromptsAndAcceptsARefresh — the operator path, including
// `r` for a fresh image (free) and a malformed answer (rejected before the POST).
func TestLoginInteractivePromptsAndAcceptsARefresh(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, loginOK)

	out, errOut, err := runCLIWithStdin(t, "r\n12ab56\n654321\n",
		"auth", "login", "--state", "haryana", "--captcha-out", filepath.Join(t.TempDir(), "c.png"))
	if err != nil {
		t.Fatalf("interactive login: %v\nstderr: %s", err, errOut)
	}
	if !strings.Contains(out, "logged in: 06AAAAA0000A1Z0") {
		t.Errorf("stdout: %s", out)
	}
	captchas, posts := 0, 0
	var sent string
	for _, h := range fp.Hits {
		switch h.Path {
		case "/services/captcha":
			captchas++
		case "/services/authenticate":
			posts++
			sent = h.Body
		}
	}
	if captchas != 2 {
		t.Errorf("`r` should have fetched a second captcha; fetched %d", captchas)
	}
	if posts != 1 {
		t.Fatalf("%d authenticate POSTs, want 1 — a rejected malformed answer must not cost an attempt", posts)
	}
	if !strings.Contains(sent, `"captcha":"654321"`) {
		t.Error("the POST did not carry the last typed answer")
	}
	if !strings.Contains(errOut, "6 digits") {
		t.Errorf("the malformed answer was not explained:\n%s", errOut)
	}
}

// TestLoginCaptchaRejectionSaysFetchAnother — SWEB_9000 is a re-rollable miss.
func TestLoginCaptchaRejectionSaysFetchAnother(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	loginPortal(t, `{"url":"/","message":null,"errorCode":"SWEB_9000"}`)

	runCaptcha(t)
	_, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", "123456")
	if err == nil {
		t.Fatal("a rejected captcha must be an error")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit = %d want %d", exitCodeFor(err), exitAuth)
	}
	if !strings.Contains(err.Error(), "captcha rejected") || !strings.Contains(err.Error(), "auth captcha") {
		t.Errorf("the message does not tell the operator to fetch a fresh image: %v", err)
	}
	if strings.Contains(err.Error(), "credentials rejected") || strings.Contains(err.Error(), "do not retry") {
		t.Errorf("a captcha miss must not be reported as a credential failure: %v", err)
	}
}

// TestLoginCredentialRejectionIsNeverRetried — the Punjab case. This message is
// the whole safety mechanism: the next human must not try again.
func TestLoginCredentialRejectionIsNeverRetried(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, `{"url":"/","message":null,"errorCode":"SWEB_8000"}`)

	runCaptcha(t)
	_, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", "123456")
	if err == nil {
		t.Fatal("rejected credentials must be an error")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit = %d want %d", exitCodeFor(err), exitAuth)
	}
	for _, want := range []string{"credentials rejected", "do not retry", "Accounts"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("message is missing %q: %v", want, err)
		}
	}
	posts := 0
	for _, h := range fp.Hits {
		if h.Path == "/services/authenticate" {
			posts++
		}
	}
	if posts != 1 {
		t.Fatalf("%d authenticate POSTs after a credential rejection, want 1", posts)
	}
}

// TestLoginStopsOnOTP — the CLI cannot pass a second factor and must not try.
func TestLoginStopsOnOTP(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	loginPortal(t, `{"url":"/otpverify","message":"Please enter the OTP sent to your registered mobile","errorCode":null}`)

	runCaptcha(t)
	_, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", "123456")
	if err == nil {
		t.Fatal("an OTP demand must stop the login")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit = %d want %d", exitCodeFor(err), exitAuth)
	}
	for _, want := range []string{"OTP", "auth import", "browser"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("the OTP message is missing %q: %v", want, err)
		}
	}
}

// TestLoginRejectsAndDiscardsAWrongRegistration: if ustatus comes back as a
// different GSTIN the jar is worse than useless — every later command would
// answer confidently about the wrong company.
func TestLoginRejectsAndDiscardsAWrongRegistration(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, loginOK)
	fp.handle(hostServices, "/services/api/ustatus", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"gstin":"09AAAAA0000A1ZU","bname":"SOMEONE ELSE","stcd":"09"}`))
	})

	runCaptcha(t)
	_, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", "123456")
	if err == nil {
		t.Fatal("a login that lands on another GSTIN must fail")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit = %d want %d", exitCodeFor(err), exitAuth)
	}
	if s, _ := loadSession("06AAAAA0000A1Z0"); s != nil {
		t.Error("the mismatched session was kept — it must be discarded")
	}
}

// TestLoginNeverPrintsThePassword covers BOTH paths, success and rejection.
// CRITIQUE §4 asked for the error path specifically.
func TestLoginNeverPrintsThePassword(t *testing.T) {
	for _, tc := range []struct{ name, body string }{
		{"success", loginOK},
		{"captcha rejected", `{"url":"/","message":null,"errorCode":"SWEB_9000"}`},
		{"credentials rejected", `{"url":"/","message":null,"errorCode":"SWEB_8000"}`},
	} {
		t.Run(tc.name, func(t *testing.T) {
			useTempStateDir(t)
			writeTestEnv(t)
			loginPortal(t, tc.body)
			runCaptcha(t)

			var out, errb strings.Builder
			app := &App{out: &out, errw: &errb, in: strings.NewReader("")}
			root := newRootCmdWithApp(app)
			root.SetOut(&out)
			root.SetErr(&errb)
			root.SetArgs([]string{"auth", "login", "--state", "haryana", "--captcha", "123456"})
			err := root.Execute()

			for what, s := range map[string]string{"stdout": out.String(), "stderr": errb.String()} {
				if strings.Contains(s, testPass) {
					t.Errorf("%s leaked the password", what)
				}
			}
			if err != nil && strings.Contains(err.Error(), testPass) {
				t.Error("the error message leaked the password")
			}
			// and nothing on disk either
			if s, _ := loadSession("06AAAAA0000A1Z0"); s != nil {
				b, _ := os.ReadFile(sessionPath("06AAAAA0000A1Z0"))
				if strings.Contains(string(b), testPass) {
					t.Error("the session file contains the password")
				}
			}
		})
	}
}

// TestLoginWithoutAPendingCaptchaSendsNothing — --captcha with no minted jar is
// answering an image that does not exist. It must not cost an attempt.
func TestLoginWithoutAPendingCaptchaSendsNothing(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, loginOK)

	_, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", "123456")
	if err == nil {
		t.Fatal("answering a captcha that was never fetched must fail")
	}
	if exitCodeFor(err) != exitAuth {
		t.Errorf("exit = %d want %d", exitCodeFor(err), exitAuth)
	}
	if fp.hitCount() != 0 {
		t.Errorf("%d request(s) were sent; want 0", fp.hitCount())
	}
}

// TestMalformedCaptchaNeverReachesThePortal — validated locally, before the wire.
func TestMalformedCaptchaNeverReachesThePortal(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, loginOK)
	runCaptcha(t)
	before := fp.hitCount()

	for _, bad := range []string{"12345", "1234567", "12a456", "      "} {
		if _, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", bad); err == nil {
			t.Errorf("%q was accepted as a captcha", bad)
		}
	}
	if fp.hitCount() != before {
		t.Errorf("a malformed captcha reached the portal (%d new requests)", fp.hitCount()-before)
	}
	if loginPOSTs != 0 {
		t.Errorf("a malformed captcha spent %d login attempt(s)", loginPOSTs)
	}
}

// TestLoginCapIsOnePerProcess — the constant is the protection; pin it.
func TestLoginCapIsOnePerProcess(t *testing.T) {
	if maxLoginAttempts != 1 {
		t.Fatalf("maxLoginAttempts = %d; it must stay 1 until somebody has measured the portal's lockout behaviour", maxLoginAttempts)
	}
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, loginOK)
	runCaptcha(t)

	loginPOSTs = maxLoginAttempts // simulate an attempt already spent
	_, err := runCLI(t, "auth", "login", "--state", "haryana", "--captcha", "123456")
	if err == nil {
		t.Fatal("a second login attempt in one process must be refused")
	}
	posts := 0
	for _, h := range fp.Hits {
		if h.Path == "/services/authenticate" {
			posts++
		}
	}
	if posts != 0 {
		t.Errorf("the cap did not hold: %d POSTs", posts)
	}
}

// TestAuthLoginIsNonInteractiveSafe — under --agent there is no terminal, so the
// CLI must explain the two-step form rather than block on stdin forever.
func TestAuthLoginIsNonInteractiveSafe(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := loginPortal(t, loginOK)

	var out, errb strings.Builder
	app := &App{out: &out, errw: &errb, in: nil} // nil ⇒ os.Stdin, and --agent forces non-interactive
	root := newRootCmdWithApp(app)
	root.SetOut(&out)
	root.SetErr(&errb)
	root.SetArgs([]string{"auth", "login", "--state", "haryana", "--agent"})
	err := root.Execute()
	if err == nil {
		t.Fatal("agent-mode login without --captcha must refuse")
	}
	if !strings.Contains(err.Error(), "auth captcha") {
		t.Errorf("it must point at the two-step form: %v", err)
	}
	if fp.hitCount() != 0 {
		t.Errorf("it opened %d connection(s) anyway", fp.hitCount())
	}
}

// TestAuthWhoamiAndImport — the two remaining auth verbs.
func TestAuthWhoamiAndImport(t *testing.T) {
	useTempStateDir(t)
	writeTestEnv(t)
	fp := newFakePortal(t)
	fp.json(hostServices, "/services/api/ustatus", "ustatus.json")

	cookies := filepath.Join(t.TempDir(), "cookies.json")
	os.WriteFile(cookies, []byte(`[
	  {"name":"AuthToken","value":"from-browser","domain":".gst.gov.in","path":"/","httpOnly":true,"secure":true},
	  {"name":"unrelated","value":"x","domain":".example.com","path":"/"}
	]`), 0o600)

	if _, err := runCLI(t, "auth", "import", cookies, "--state", "haryana"); err != nil {
		t.Fatalf("auth import: %v", err)
	}
	s, _ := loadSession("06AAAAA0000A1Z0")
	if s == nil || len(s.Cookies) != 1 || s.Cookies[0].Name != "AuthToken" {
		t.Fatalf("import kept the wrong cookies: %+v", s)
	}
	if s.Stage != stageAuthenticated {
		t.Errorf("an imported jar should be usable immediately, stage = %q", s.Stage)
	}

	out, err := runCLI(t, "auth", "whoami", "--state", "haryana")
	if err != nil {
		t.Fatalf("auth whoami: %v", err)
	}
	if !strings.Contains(out, "06AAAAA0000A1Z0") {
		t.Errorf("whoami: %s", out)
	}
	if got := fp.lastHit(t); got.Path != "/services/api/ustatus" {
		t.Errorf("whoami hit %s", got.Path)
	}
}

// runCaptcha mints a pre-login jar so a --captcha login has something to answer.
func runCaptcha(t *testing.T) {
	t.Helper()
	if _, err := runCLI(t, "auth", "captcha", "--state", "haryana", "--out", filepath.Join(t.TempDir(), "c.png")); err != nil {
		t.Fatalf("auth captcha: %v", err)
	}
}

func contains(ss []string, want string) bool {
	for _, s := range ss {
		if s == want {
			return true
		}
	}
	return false
}
