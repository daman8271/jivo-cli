package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"
)

// login.go is the ONE sanctioned side effect in this binary: POST
// /services/authenticate. Everything about it is deliberately narrow.
//
//   - ONE POST per process. maxLoginAttempts is a constant, not a flag, and the
//     counter is package-level so no loop anywhere can spend a second attempt.
//     Nobody here has measured what the portal does after N bad logins, and the
//     cost of finding out on a live statutory account is an account lockout in
//     the middle of a filing month.
//   - A CREDENTIAL rejection is never retried, by anyone, ever. It is reported
//     and the operator is told to take it to Accounts (Punjab's password has
//     been wrong since 2026-08-21 and re-trying it is how a lockout happens).
//   - A CAPTCHA rejection is a free re-roll, but only by starting again: the
//     next image needs a new jar.
//   - The password is never printed, logged, echoed or put in an error string.
//     It exists in exactly one expression in this file.
//
// Flow (API.md §Session, verified live):
//
//	GET /services/login      → mints the pre-auth jar (AuthToken placeholder, TS*)
//	GET /services/captcha    → the PNG, plus CaptchaCookie binding it to that jar
//	POST /services/authenticate {username,password,captcha,mFP}  → HTTP 200 always
//	GET /services/api/ustatus → must answer with the GSTIN we meant to be

// maxLoginAttempts is the hard cap on POST /services/authenticate per process.
const maxLoginAttempts = 1

// loginPOSTs counts the authenticate calls this process has made.
var loginPOSTs int

// otpMessage is what the operator sees if the portal ever demands an OTP. The
// CLI does not handle OTP and will not grow a handler: an OTP is a second factor
// precisely so that an unattended program cannot pass it.
const otpMessage = "portal asked for OTP for %s; this CLI never handles OTP — complete the login once in a browser, then `auth import`, or ask Accounts to disable OTP-on-login"

// mintCaptcha starts a fresh login: it opens a new pre-auth jar, fetches the
// captcha bound to it, saves both, and returns the image path.
//
// The jar is persisted (stage=prelogin) because the agent-friendly login is two
// separate CLI invocations — `auth captcha` then `auth login --captcha` — and
// the second one MUST use the jar the image was minted against.
func (a *App) mintCaptcha(reg Registration, outPath string) (string, error) {
	c := newClient(reg)
	c.startPreLoginJar()
	// Stage it: session-<GSTIN>.pending.json, NOT session-<GSTIN>.json. Only a
	// login the portal accepted may replace a working session.
	c.sess.file = pendingSessionPath(reg.GSTIN)

	// The login page is fetched only for its Set-Cookie headers. Nothing in its
	// HTML is parsed, and it is never fetched with a live session: doing that
	// replaces the AuthToken with a pre-auth placeholder and logs you straight
	// out (API.md, session-killer (a) — found the hard way, three logins burned).
	if _, _, err := c.doPreAuthRaw(epLoginPage, nil); err != nil {
		return "", err
	}
	png, ctype, err := c.doPreAuthRaw(epCaptcha, qs("rnd", cacheBuster()))
	if err != nil {
		return "", err
	}
	if !strings.HasPrefix(ctype, "image/") {
		return "", errAuth("the captcha endpoint returned %s, not an image — the portal is showing us a page, not a login", ctype)
	}
	if err := c.sess.save(); err != nil {
		return "", err
	}
	if outPath == "" {
		outPath = defaultCaptchaPath(reg.GSTIN)
	}
	return saveCaptcha(outPath, png)
}

// cacheBuster is the `rnd` parameter the portal's own login page puts on the
// captcha URL. Its only job is to defeat caching.
func cacheBuster() string { return fmt.Sprintf("0.%d", time.Now().UnixNano()) }

// authCaptcha implements `auth captcha --out <file>`: the first half of the
// agent-friendly login. It prints where the image is and stops.
func (a *App) authCaptcha(reg Registration, outPath string) error {
	if prior, _ := loadSession(reg.GSTIN); prior != nil && prior.authenticated() {
		a.logf("note: %s already has a cached session. It is left alone — the captcha jar is staged separately "+
			"and only replaces it if the portal accepts the login. But the GST portal is one-session-per-username, "+
			"so a successful login WILL end any browser session logged in as this user.", reg.GSTIN)
	}
	path, err := a.mintCaptcha(reg, outPath)
	if err != nil {
		return a.emitError("auth captcha", reg.GSTIN, endpointURL(epCaptcha), err)
	}
	if a.JSON || a.Agent {
		return a.emitValue("auth captcha", reg.GSTIN, endpointURL(epCaptcha), map[string]any{
			"gstin":       reg.GSTIN,
			"state":       reg.State,
			"captcha_png": path,
			"next":        fmt.Sprintf("gst-portal auth login --gstin %s --captcha <%d digits>", reg.GSTIN, captchaDigits),
		}, 1)
	}
	a.printf("%s", path)
	a.logf("read the %d digits in that image, then run:\n  gst-portal auth login --gstin %s --captcha <digits>", captchaDigits, reg.GSTIN)
	return nil
}

// authLogin implements `auth login`. Two shapes, one POST either way:
//
//	--captcha 123456   answers an image minted earlier by `auth captcha`
//	(no flag)          mints one now, opens it, and prompts for the digits
func (a *App) authLogin(reg Registration, code, captchaOut string) error {
	c := newClient(reg)

	if code != "" {
		if err := validCaptcha(code); err != nil {
			return err
		}
		s, err := loadPendingSession(reg.GSTIN)
		if err != nil {
			return err
		}
		if s == nil || s.Stage != stagePreLogin {
			return errAuth("no pending captcha for %s — run `gst-portal auth captcha --gstin %s --out <file>` first; "+
				"the digits are only valid for the jar that fetched that image", reg.GSTIN, reg.GSTIN)
		}
		if s.expired(captchaMaxAge) {
			return errAuth("the captcha for %s was fetched %s ago and has almost certainly expired — fetch a fresh one",
				reg.GSTIN, time.Since(s.SavedAt).Round(time.Second))
		}
		c.useSession(s)
		return a.finishLogin(c, reg, code)
	}

	if prior, _ := loadSession(reg.GSTIN); prior != nil && prior.authenticated() {
		a.logf("note: %s already has a cached session; it is left in place unless this login succeeds. "+
			"The GST portal is one-session-per-username, so a successful login ends any browser session "+
			"logged in as this user — do not do this while somebody is mid-filing.", reg.GSTIN)
	}

	if !a.interactive() {
		return errUsage("this session has no terminal to show a captcha on. Use the two-step form:\n" +
			"  gst-portal auth captcha --gstin " + reg.GSTIN + " --out /tmp/captcha.png\n" +
			"  gst-portal auth login   --gstin " + reg.GSTIN + " --captcha <digits>")
	}

	path, err := a.mintCaptcha(reg, captchaOut)
	if err != nil {
		return err
	}
	if err := openImage(path); err != nil {
		a.logf("(could not open an image viewer: %v — open the file yourself)", err)
	}
	answer, err := promptCaptcha(a.reader(), a.errw, path, func() (string, error) {
		p, err := a.mintCaptcha(reg, captchaOut)
		if err != nil {
			return "", err
		}
		if err := openImage(p); err != nil {
			a.logf("(could not open an image viewer: %v)", err)
		}
		return p, nil
	})
	if err != nil {
		return err
	}
	// The re-rolls above replaced the staged jar on disk; reload so the POST uses
	// the jar the ANSWERED image was bound to.
	s, err := loadPendingSession(reg.GSTIN)
	if err != nil {
		return err
	}
	if s == nil {
		return errAuth("the pre-login jar for %s vanished between the captcha and the answer", reg.GSTIN)
	}
	c.useSession(s)
	return a.finishLogin(c, reg, answer)
}

// captchaMaxAge is how long a minted captcha is worth answering. The portal's
// own expiry is not published; this is a courtesy check that turns a stale
// two-step login into a clear message instead of a spent attempt.
const captchaMaxAge = 10 * time.Minute

// finishLogin performs the single POST and everything that follows it.
func (a *App) finishLogin(c *Client, reg Registration, code string) error {
	if reg.User == "" || reg.Pass == "" {
		return errConfig("no username/password configured for %s (%s) — check the GST_%s_* block in the .env", reg.GSTIN, reg.State, reg.Idx)
	}
	if loginPOSTs >= maxLoginAttempts {
		return errAuth("this process has already spent its one login attempt for the GST portal; "+
			"run the command again rather than looping (attempt cap: %d)", maxLoginAttempts)
	}
	// maxLoginAttempts only binds THIS process. The cap that binds a retry loop,
	// a cron or an agent is on disk: once the portal has refused these
	// credentials, no further attempt is made for this GSTIN until a human
	// clears the record. That is how "never retry a credential rejection"
	// stops being advice.
	if rej := credentialRejectionFor(reg.GSTIN); rej != nil {
		return errAuth("the portal already rejected the credentials for %s (%s) on %s%s — refusing to try again.\n"+
			"Get a corrected password from Accounts, then delete %s to re-enable login for this registration.\n"+
			"Repeated attempts on a wrong password are how a GST account gets locked, and only the department can unlock it.",
			reg.GSTIN, reg.State, rej.RejectedAt.Format("2006-01-02 15:04"), portalCodeSuffix(rej.PortalCode), rejectionPath(reg.GSTIN))
	}
	loginPOSTs++

	a.logf("logging in as %s (%s) — one attempt, no retry", reg.GSTIN, reg.State)
	res, err := c.doPreAuth(epAuthenticate, nil, map[string]any{
		"username": reg.User,
		"password": reg.Pass,
		"captcha":  code,
		"mFP":      mfpBlob(),
		"deviceID": nil,
		"type":     "username",
	})
	if err != nil {
		return a.emitError("auth login", reg.GSTIN, endpointURL(epAuthenticate), err)
	}
	if err := interpretLogin(reg, res.Raw); err != nil {
		var cerr *credentialError
		if asCredentialError(err, &cerr) {
			recordCredentialRejection(reg.GSTIN, cerr.PortalCode)
		}
		return a.emitError("auth login", reg.GSTIN, endpointURL(epAuthenticate), err)
	}

	// The portal accepted us. Promote the staged jar over the real session file
	// (this is the ONLY thing that may replace a working session), verify who it
	// thinks we are, and clear any stale rejection record.
	c.sess.Stage = stageAuthenticated
	c.sess.Username = reg.User
	c.sess.file = sessionPath(reg.GSTIN)
	if err := c.sess.save(); err != nil {
		return err
	}
	discardPendingSession(reg.GSTIN)
	clearCredentialRejection(reg.GSTIN)
	who, err := c.do(epUstatus, nil, nil, nil)
	if err != nil {
		discardSession(reg.GSTIN)
		return a.emitError("auth login", reg.GSTIN, endpointURL(epUstatus),
			errAuth("logged in, but the portal would not confirm who we are (%v) — the session was discarded", err))
	}
	var u struct {
		GSTIN string `json:"gstin"`
		BName string `json:"bname"`
		Stcd  string `json:"stcd"`
	}
	if err := json.Unmarshal(who.Raw, &u); err != nil || u.GSTIN == "" {
		discardSession(reg.GSTIN)
		return a.emitError("auth login", reg.GSTIN, endpointURL(epUstatus),
			errAuth("logged in, but ustatus did not name a GSTIN — the session was discarded"))
	}
	if !strings.EqualFold(u.GSTIN, reg.GSTIN) {
		discardSession(reg.GSTIN)
		return a.emitError("auth login", reg.GSTIN, endpointURL(epUstatus),
			errAuth("that login belongs to %s, not %s — the session was discarded; check the GST_%s_* block in the .env",
				u.GSTIN, reg.GSTIN, reg.Idx))
	}

	if a.JSON || a.Agent {
		return a.emitValue("auth login", reg.GSTIN, endpointURL(epAuthenticate), map[string]any{
			"gstin":        u.GSTIN,
			"state":        reg.State,
			"state_code":   u.Stcd,
			"session_file": sessionPath(reg.GSTIN),
			"logged_in":    true,
		}, 1)
	}
	a.printf("logged in: %s (state %s)", u.GSTIN, u.Stcd)
	a.logf("session cached at %s — GST sessions are short; re-run `auth login` when a command says the session expired.", sessionPath(reg.GSTIN))
	return nil
}

// interpretLogin reads the authenticate response. It is always HTTP 200, so the
// body is the only signal (API.md §Session):
//
//	success  {"url":null,"message":"auth","successCode":null}
//	captcha  {"url":"/","message":null,"errorCode":"SWEB_9000"}
//	creds    any other errorCode ("Invalid Username or Password")
func interpretLogin(reg Registration, raw json.RawMessage) error {
	// OTP is checked first and against the whole body: whatever shape the portal
	// wraps it in, the word is the signal and the answer is always "stop".
	if mentionsOTP(string(raw)) {
		return errAuth(otpMessage, reg.GSTIN)
	}
	var body struct {
		URL         *string `json:"url"`
		Message     *string `json:"message"`
		ErrorCode   string  `json:"errorCode"`
		ErrorMsg    string  `json:"errorMsg"`
		SuccessCode *string `json:"successCode"`
	}
	if err := json.Unmarshal(raw, &body); err != nil {
		return errAuth("the portal's answer to the login was not the expected JSON shape")
	}
	switch {
	case body.ErrorCode == "SWEB_9000":
		return errAuth("captcha rejected — run `gst-portal auth captcha --gstin %s` again for a fresh image "+
			"(a wrong captcha is not a credential failure; a fresh image costs nothing)", reg.GSTIN)
	case body.ErrorCode != "":
		return &credentialError{PortalCode: body.ErrorCode, authError: authError{msg: fmt.Sprintf(
			"credentials rejected for %s (%s), portal code %s — do not retry, tell Accounts. "+
				"Repeated attempts on a wrong password are how a GST account gets locked",
			reg.GSTIN, reg.State, body.ErrorCode)}}
	case body.Message != nil && *body.Message == "auth":
		return nil
	}
	return errAuth("the portal neither accepted nor refused the login in a way this CLI recognises — "+
		"nothing was retried; check %s in a browser", reg.GSTIN)
}

// credentialError is a login the portal refused on the USERNAME/PASSWORD (as
// opposed to the captcha). It is an authError, so it keeps exit 4; the separate
// type exists so finishLogin can write the rejection down without string
// matching on a message.
type credentialError struct {
	authError
	PortalCode string
}

// Unwrap keeps errors.As(*authError) working — without it a refused credential
// would fall through to exit 2 (usage) instead of exit 4 (auth).
func (e *credentialError) Unwrap() error { return &e.authError }

func portalCodeSuffix(code string) string {
	if code == "" {
		return ""
	}
	return " (portal code " + code + ")"
}

// mentionsOTP looks for the portal asking for a second factor.
func mentionsOTP(s string) bool {
	l := strings.ToLower(s)
	for _, needle := range []string{"otp", "one time password", "one-time password", "two factor", "2fa"} {
		if strings.Contains(l, needle) {
			return true
		}
	}
	return false
}

// ---- terminal plumbing -----------------------------------------------------

// reader is where a prompt reads from: the injected reader in tests, stdin
// otherwise.
func (a *App) reader() io.Reader {
	if a.in != nil {
		return a.in
	}
	return os.Stdin
}

// interactive reports whether there is a human at a terminal to show a captcha
// to. Agent mode is never interactive, and neither is a pipe or an `ssh box
// gst-portal auth login`: prompting there would hang forever, so the CLI says so
// and points at the two-step form instead.
func (a *App) interactive() bool {
	if a.Agent {
		return false
	}
	f, ok := a.reader().(*os.File)
	if !ok {
		return true // an injected reader (tests) always has an answer waiting
	}
	fi, err := f.Stat()
	if err != nil {
		return false
	}
	return fi.Mode()&os.ModeCharDevice != 0
}
