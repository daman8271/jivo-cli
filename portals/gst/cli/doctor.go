package main

import (
	"strings"

	"github.com/spf13/cobra"
)

// newDoctorCmd is the house health check: config → session → one harmless live
// read (GET /services/api/ustatus). --offline stops after the session check and
// never touches the network.
func newDoctorCmd(app *App) *cobra.Command {
	var offline bool
	c := &cobra.Command{
		Use:   "doctor",
		Short: "Check config, session and (unless --offline) one live read per registration",
		Long: `Check every configured registration: credentials present, cached session state,
and one harmless live read (GET /services/api/ustatus) unless --offline.

With no --gstin/--state it checks ALL of them — this is the first command SETUP
tells an operator to run, so it must work with no selector.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.runDoctor(offline)
		},
	}
	c.Flags().BoolVar(&offline, "offline", false, "check config and cached sessions only; open no connection")
	c.Flags().BoolVar(&app.All, "all", false, "check every configured registration (the default when no selector is given)")
	return c
}

// newAuthCmd holds the credential/session commands. `login` is the only
// sanctioned non-read in the binary and lands in the next phase.
func newAuthCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "auth",
		Short: "Registrations, cached sessions, and login",
	}
	c.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List the configured registrations (credentials masked)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.authList()
		},
	})
	c.AddCommand(newAuthStatusCmd(app))
	c.AddCommand(newAuthLoginCmd(app), newAuthCaptchaCmd(app), newAuthWhoamiCmd(app), newAuthImportCmd(app),
		newAuthKeepaliveCmd(app))
	return c
}

// newAuthLoginCmd — the only sanctioned side effect (login.go). One POST, ever.
func newAuthLoginCmd(app *App) *cobra.Command {
	var code, out string
	c := &cobra.Command{
		Use:   "login",
		Short: "Log in for the selected registration (shows a captcha; ONE attempt, never retried)",
		Long: `Log in to the GST portal for one registration.

Interactive (a person at a terminal):
  gst-portal auth login --state haryana
    fetches a captcha, opens the image, asks for the six digits, logs in once.
    Type ` + "`r`" + ` at the prompt for a fresh image — that costs nothing.

Two-step (agents, SSH, anything without a display):
  gst-portal auth captcha --state haryana --out /tmp/c.png
  gst-portal auth login   --state haryana --captcha 123456

Exactly one POST /services/authenticate happens per run. A captcha rejection
means "fetch another image"; a credential rejection is NEVER retried — take it
to Accounts, because repeated attempts are how a GST login gets locked.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			return app.authLogin(reg, code, out)
		},
	}
	c.Flags().StringVar(&code, "captcha", "", "the six digits from an image minted by `auth captcha`")
	c.Flags().StringVar(&out, "captcha-out", "", "where to write the captcha image (default: alongside the session file)")
	return c
}

// newAuthCaptchaCmd — half a login: mint the image and the jar it is bound to.
func newAuthCaptchaCmd(app *App) *cobra.Command {
	var out string
	c := &cobra.Command{
		Use:   "captcha",
		Short: "Fetch a login captcha as a PNG (then answer it with `auth login --captcha`)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			return app.authCaptcha(reg, out)
		},
	}
	c.Flags().StringVar(&out, "out", "", "where to write the PNG (default: alongside the session file)")
	return c
}

// newAuthWhoamiCmd — who does the portal think this session is?
func newAuthWhoamiCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "whoami",
		Short: "Ask the portal who the cached session belongs to (GET /services/api/ustatus)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			return app.read("auth whoami", reg, epUstatus, nil, nil, nil)
		},
	}
}

// newAuthKeepaliveCmd — hold open the sessions we already have.
//
// The portal's own SPA polls GET payment/auth/api/keepalive to reset the server
// side idle timer; this is that call and nothing more. It exists because the
// alternative to keeping a live session alive is another captcha, and a captcha
// needs eyes. Pinging is what makes an unattended box (the VPS holder) viable.
//
// It NEVER logs in. A dead session stays dead here and is reported as such — a
// lapsed jar cannot be revived by a keepalive (API.md §Session), so silently
// re-logging in would be both useless and a session-killer for whoever else is
// on that username.
func newAuthKeepaliveCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "keepalive",
		Short: "Ping the portal's idle timer so a live session does not lapse (GET payment/auth/api/keepalive)",
		Long: `Reset the portal's server-side idle timer for sessions that are ALREADY live.

This is the call the portal's own SPA makes while a tab sits open. It buys time;
it cannot resurrect a lapsed session and it never logs in. Run it on a timer
(the VPS holder does, every few minutes) to keep a sitting open without burning
another captcha.

Exit status is 0 only if every selected registration was still alive.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(app.Sel) == 0 {
				return errUsage("keepalive needs a selection: --gstin <GSTIN>, --state <name|code>, or --all")
			}
			return app.authKeepalive()
		},
	}
	c.Flags().BoolVar(&app.All, "all", false, "ping every configured registration")
	return c
}

// newAuthImportCmd — adopt a jar exported from a browser. This is the path for a
// box with no display, and the only path if the portal ever demands an OTP.
func newAuthImportCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "import <cookies.json>",
		Short: "Adopt a browser-exported cookie jar as the session for one registration",
		Long: `Adopt a cookie jar exported from a logged-in browser.

The file is the array a Playwright/CDP export emits: [{"name","value","domain",…}].
Only gst.gov.in cookies are kept. Note that the portal's auth cookies are
httpOnly, so a document.cookie dump will NOT contain them — the export has to be
network-level.`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			return app.authImport(reg, args[0])
		},
	}
}

// runDoctor: config → session → one harmless live read (GET /services/api/ustatus).
func (a *App) runDoctor(offline bool) error {
	type check struct {
		GSTIN   string `json:"gstin"`
		State   string `json:"state"`
		Config  string `json:"config"`
		Session string `json:"session"`
		Live    string `json:"live"`
		OK      bool   `json:"ok"`
	}
	regs := a.everySelected()
	out := make([]check, 0, len(regs))
	allOK := true
	for _, r := range regs {
		c := check{GSTIN: r.GSTIN, State: r.State, OK: true}
		c.Config = "user=" + masked(r.User) + " pass=" + maskedSecret(r.Pass)
		c.Session = sessionSummary(r.GSTIN)
		if offline {
			c.Live = "skipped (--offline)"
		} else {
			c.Live, c.OK = a.liveCheck(r)
		}
		allOK = allOK && c.OK
		out = append(out, c)
	}
	if a.JSON || a.Agent {
		if err := a.emitValue("doctor", "", "", out, len(out)); err != nil {
			return err
		}
	} else {
		for _, c := range out {
			a.printf("%s  %-20s  config:  %s", c.GSTIN, c.State, c.Config)
			a.printf("%s  %-20s  session: %s", strings.Repeat(" ", len(c.GSTIN)), "", c.Session)
			a.printf("%s  %-20s  live:    %s", strings.Repeat(" ", len(c.GSTIN)), "", c.Live)
		}
	}
	if !allOK {
		return errAuth("doctor: at least one registration could not complete its live read")
	}
	return nil
}

// authKeepalive pings the portal's idle timer for every selected registration.
//
// One ping per registration, sequential (the client's own pacing applies). A
// registration whose jar is already lapsed is reported "expired" and skipped
// rather than logged in: reviving it needs a captcha, which is a decision for
// the caller — see gstd on the VPS holder, which reads this output and decides.
func (a *App) authKeepalive() error {
	type ping struct {
		GSTIN string `json:"gstin"`
		State string `json:"state"`
		// Verdict is the machine-readable one, for gstd: "alive" | "expired" |
		// "unavailable". A keeper branches on this and nothing else.
		Verdict string `json:"verdict"`
		Result  string `json:"result"`
		OK      bool   `json:"ok"`
	}
	regs := a.everySelected()
	out := make([]ping, 0, len(regs))
	allOK := true
	anyDown := false
	for _, r := range regs {
		p := ping{GSTIN: r.GSTIN, State: r.State}
		c := newClient(r)
		// ustatus, not the portal's own keepalive, is the authoritative ping.
		// Two reasons, both learned live (2026-09-02 00:15 IST): it lives on
		// services.gst.gov.in, the one host that stays up through the portal's
		// nightly window (payment. and return. both served 503), and its answer
		// names the GSTIN, so a ping that succeeds has also PROVED the jar is
		// still ours. Any authenticated request resets the server idle timer;
		// this one reports as well.
		if _, err := c.do(epUstatus, nil, nil, nil); err != nil {
			p.Result = "FAILED — " + err.Error()
			if portalUnavailable(err) {
				p.Verdict, anyDown = "unavailable", true
			} else {
				p.Verdict = "expired"
			}
		} else {
			p.Verdict, p.Result, p.OK = "alive", "alive", true
			// Best-effort: the portal's purpose-built idle-timer reset. Its host
			// is the one that goes down overnight, so a failure here is NOT a
			// failure of the ping — ustatus already did the work.
			if _, err := c.do(epKeepalive, nil, nil, nil); err != nil {
				p.Result = "alive (services only; payment host unavailable)"
			}
		}
		allOK = allOK && p.OK
		out = append(out, p)
	}
	if a.JSON || a.Agent {
		if err := a.emitValue("auth keepalive", "", endpointURL(epUstatus), out, len(out)); err != nil {
			return err
		}
	} else {
		for _, p := range out {
			a.printf("%s  %-20s  %s", p.GSTIN, p.State, p.Result)
		}
	}
	switch {
	case allOK:
		return nil
	case anyDown:
		// Exit 6, not 4. "The portal is down" must never be reported as "your
		// session died": the caller's correct response is to wait, and a keeper
		// that logs in here achieves nothing but burnt attempts.
		return &apiError{Status: 503, Message: "the portal's authenticated API is unavailable " +
			"(it goes down overnight) — wait and retry; do NOT log in"}
	default:
		return errAuth("keepalive: at least one session is no longer alive — it needs `auth login`")
	}
}

// newAuthStatusCmd reports the cached session for each selected registration.
func newAuthStatusCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "status",
		Short: "Show the cached session age for the selected registration(s), or all of them",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.authStatus()
		},
	}
	c.Flags().BoolVar(&app.All, "all", false, "show every configured registration (the default when no selector is given)")
	return c
}
