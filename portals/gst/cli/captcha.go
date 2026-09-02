package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// The captcha is the whole reason logging in is a human act. The portal serves a
// 182x50 PNG of six digits bound to the cookie jar that fetched it, and there is
// no API to answer it. So the CLI does the only honest thing: it saves the image
// where the operator can see it, opens it, and waits for them to type the digits.
//
// No OCR. The measured accuracy of the study pipeline was ~50% per attempt
// (docs/captcha-ocr.md) and a wrong answer costs a login attempt on a statutory
// portal whose lockout behaviour nobody here has measured. A typed answer is
// slower and correct.
//
// This is also the only file allowed to run a subprocess (`open` / `cmd /c
// start`) and, with session.go and snapshot.go, one of the three allowed to
// write to disk — readonly_ast_test.go pins both.

// captchaDigits is how many digits the portal's captcha always has.
const captchaDigits = 6

// defaultCaptchaPath is where the interactive login drops the image: alongside
// the session files, outside the repo. Operator checkouts are sparse clones and
// a stray PNG in one is clutter at best.
func defaultCaptchaPath(gstin string) string {
	name := "captcha-" + sanitiseGSTIN(gstin) + ".png"
	return filepath.Join(stateDir(), "gst-portal", name)
}

// safeImagePath reports whether an operator-supplied output path is one we are
// willing to write to and hand to a viewer. Two reasons it is narrow:
//
//   - the file is CLOBBERED with PNG bytes, so a typo pointed at something that
//     matters would destroy it. Requiring .png makes that a typo you notice;
//   - on Windows the path is handed to an image viewer as a process argument.
//     Keeping it to [A-Za-z0-9 _.:\/-] means no shell metacharacter can ever
//     reach a command line, whatever the launcher underneath turns out to do.
func safeImagePath(path string) error {
	if !strings.EqualFold(filepath.Ext(path), ".png") {
		return errUsage("the captcha image path must end in .png (got %q) — it is overwritten with PNG bytes", path)
	}
	for _, r := range path {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9':
		case r == '/', r == '\\', r == '.', r == '-', r == '_', r == ':', r == ' ', r == '~':
		default:
			return errUsage("the captcha image path may not contain %q — use a plain path like /tmp/captcha.png", string(r))
		}
	}
	return nil
}

// saveCaptcha writes the PNG 0600 inside a 0700 directory and returns the path.
func saveCaptcha(path string, png []byte) (string, error) {
	if len(png) == 0 {
		return "", errAuth("the portal returned an empty captcha image")
	}
	if err := safeImagePath(path); err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return "", errConfig("cannot create %s: %v", filepath.Dir(path), err)
	}
	if err := os.WriteFile(path, png, 0o600); err != nil {
		return "", errConfig("cannot write the captcha image to %s: %v", path, err)
	}
	return path, nil
}

// openImage shows the captcha to the operator. On a headless box (SSH, an agent,
// a cron) there is nothing to show it with — that is not an error, the caller
// prints the path instead. openImage never blocks on the viewer.
func openImage(path string) error {
	if err := safeImagePath(path); err != nil {
		return err
	}
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", path)
	case "windows":
		// Deliberately NOT `cmd /c start "" <path>`. Go escapes argv for the C
		// runtime, but cmd.exe re-parses the joined command line and acts on
		// & | ^ > BEFORE dequoting — so a --captcha-out containing & would run a
		// command on the Accounts laptops. rundll32 takes plain argv and does the
		// same job (open the file with its registered handler).
		//
		// UNVERIFIED ON WINDOWS: nothing on a Mac can exercise this branch, and
		// per the fleet rule Windows behaviour has to be checked on a live box.
		// safeImagePath above is the layer that does not depend on which
		// launcher wins.
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", path)
	default:
		if _, err := exec.LookPath("xdg-open"); err != nil {
			return errPlain("no image viewer on this box")
		}
		cmd = exec.Command("xdg-open", path)
	}
	return cmd.Start()
}

// captchaSource fetches a fresh captcha image and reports where it was saved.
// The refresh path exists because a fresh GET costs nothing and does NOT count
// as a login attempt — re-rolling an unreadable image is always cheaper than
// guessing at it.
type captchaSource func() (path string, err error)

// promptCaptcha asks the operator for the digits, offering a free re-roll.
// It returns the digits; it never echoes anything but them.
func promptCaptcha(in io.Reader, errw io.Writer, first string, next captchaSource) (string, error) {
	path := first
	r := bufio.NewReader(in)
	for {
		fmt.Fprintf(errw, "captcha image: %s\n", path)
		fmt.Fprintf(errw, "captcha (%d digits, or `r` for a fresh image, or blank to abort): ", captchaDigits)
		line, err := r.ReadString('\n')
		if err != nil && strings.TrimSpace(line) == "" {
			return "", errAuth("could not read the captcha from the terminal: %v", err)
		}
		answer := strings.TrimSpace(line)
		switch {
		case answer == "":
			return "", errAuth("login aborted at the captcha prompt — nothing was sent")
		case strings.EqualFold(answer, "r"):
			p, err := next()
			if err != nil {
				return "", err
			}
			path = p
			continue
		}
		if err := validCaptcha(answer); err != nil {
			fmt.Fprintf(errw, "  %v\n", err)
			continue
		}
		return answer, nil
	}
}

// validCaptcha checks the shape before a login attempt is spent on it.
func validCaptcha(s string) error {
	if len(s) != captchaDigits {
		return errUsage("the captcha is %d digits; %q is %d characters", captchaDigits, s, len(s))
	}
	for _, r := range s {
		if r < '0' || r > '9' {
			return errUsage("the captcha is %d digits; %q is not all digits", captchaDigits, s)
		}
	}
	return nil
}
