package main

import "os"

// authList prints every configured registration with masked credentials. It is
// the one command that ignores the selector flags: its whole job is to show what
// there is to select.
func (a *App) authList() error {
	type row struct {
		Idx       string `json:"idx"`
		State     string `json:"state"`
		GSTIN     string `json:"gstin"`
		StateCode string `json:"state_code"`
		User      string `json:"user_masked"`
		Pass      string `json:"pass_masked"`
	}
	rows := make([]row, 0, len(a.Regs))
	for _, r := range a.Regs {
		rows = append(rows, row{r.Idx, r.State, r.GSTIN, r.StateCode(), masked(r.User), maskedSecret(r.Pass)})
	}
	if a.JSON || a.Agent {
		return a.emitValue("auth list", "", "", rows, len(rows))
	}
	a.printf("%d GST registrations configured (credentials masked):", len(rows))
	for _, r := range a.Regs {
		a.printf("  %s", r.summary())
	}
	return nil
}

// authImport adopts a browser-exported cookie jar as the session for one
// registration. It is the documented way in for a box with no display, and the
// only way in if the portal ever starts demanding an OTP.
//
// It cannot verify the jar offline, so it does the next best thing: it saves it
// and tells the operator to run `doctor`, whose live read fails loudly if the
// jar belongs to a different GSTIN.
func (a *App) authImport(reg Registration, path string) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return errConfig("cannot read %s: %v", path, err)
	}
	cookies, err := importPlaywrightCookies(raw)
	if err != nil {
		return err
	}
	s := &session{
		GSTIN:    reg.GSTIN,
		Username: reg.User,
		Stage:    stageAuthenticated,
		Cookies:  cookies,
	}
	if err := s.save(); err != nil {
		return err
	}
	if a.JSON || a.Agent {
		return a.emitValue("auth import", reg.GSTIN, "", map[string]any{
			"gstin":        reg.GSTIN,
			"cookies":      len(cookies),
			"session_file": sessionPath(reg.GSTIN),
		}, len(cookies))
	}
	a.printf("imported %d gst.gov.in cookies for %s", len(cookies), reg.GSTIN)
	a.logf("verify it with: gst-portal doctor --gstin %s", reg.GSTIN)
	return nil
}
