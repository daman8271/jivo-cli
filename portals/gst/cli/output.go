package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
)

// App is the shared command context. Root's PersistentPreRunE loads the
// registrations and resolves the --gstin/--state/--all selection into Sel;
// every leaf command reads it.
//
// out/errw are injectable so the whole CLI can be driven in tests without
// capturing the process's stdout.
type App struct {
	out  io.Writer
	errw io.Writer
	in   io.Reader // the captcha prompt's input; nil means os.Stdin

	JSON  bool // --json: pretty JSON output
	Agent bool // --agent: implies JSON + stable envelope, suppresses stderr
	GSTIN string
	State string
	All   bool

	Regs []Registration // everything configured
	Sel  []Registration // what this invocation runs against

	// wroteEnvelope records that an --agent envelope already went to stdout, so
	// main.go's catch-all does not print a second one.
	wroteEnvelope bool
}

// Result is what one allowlisted read returns. Empty marks the portal's
// "no record for that filter" answers (RET13510 / LG9221 / GTR2B-002), which
// are answers rather than failures — see client.go emptyCodes.
type Result struct {
	Raw   json.RawMessage
	Empty bool
	Note  string
}

// reLoginMsg is the uniform guidance printed whenever the portal stops
// recognising us. GST sessions are short and single-use per username.
const reLoginMsg = "session expired or not established — run `gst-portal auth login --gstin <GSTIN>` (a captcha will be shown) or `gst-portal auth import <cookies.json>`"

// resolve loads the registrations and applies the selector flags.
//
// No selector at all is NOT an error here: `auth list` exists precisely to show
// what there is to select, and `doctor` is the first thing SETUP tells an
// operator to run. Both used to die in PersistentPreRunE with exit 2 before
// their RunE was ever reached. A selector that is present but WRONG
// (--gstin 99…) still fails here, loudly. Commands that need exactly one
// registration raise the usage error themselves, at the leaf, via a.one().
func (a *App) resolve() error {
	regs, err := loadRegistrations()
	if err != nil {
		return err
	}
	a.Regs = regs
	if !a.All && strings.TrimSpace(a.GSTIN) == "" && strings.TrimSpace(a.State) == "" &&
		strings.TrimSpace(os.Getenv("GST_DEFAULT")) == "" {
		a.Sel = nil
		return nil
	}
	sel, err := selectRegistrations(regs, a.GSTIN, a.State, os.Getenv("GST_DEFAULT"), a.All)
	if err != nil {
		return err
	}
	a.Sel = sel
	return nil
}

// everySelected is what the estate-wide commands (doctor, auth status) run over:
// the explicit selection when there is one, otherwise every configured
// registration. These three are the only commands where "all of them" is a safe
// default — they are cheap, read-only and diagnostic.
func (a *App) everySelected() []Registration {
	if len(a.Sel) > 0 {
		return a.Sel
	}
	return a.Regs
}

// one returns the single selected registration, or a usage error if the command
// does not support --all.
func (a *App) one() (Registration, error) {
	switch len(a.Sel) {
	case 1:
		return a.Sel[0], nil
	case 0:
		return Registration{}, errUsage("no registration selected — use --gstin or --state")
	default:
		return Registration{}, errUsage("this command takes one registration at a time; drop --all and use --gstin or --state")
	}
}

// logf writes progress to stderr unless in agent mode (which must stay clean).
func (a *App) logf(format string, args ...any) {
	if !a.Agent {
		fmt.Fprintf(a.errw, format+"\n", args...)
	}
}

// printf writes to the command's stdout.
func (a *App) printf(format string, args ...any) {
	fmt.Fprintf(a.out, format+"\n", args...)
}

// emit renders the result of a read: the agent envelope under --agent, else the
// pretty portal body. `res.Empty` is a portal "no record" answer — an answer,
// not a failure: ok=true, data=null, count=0, and the portal's own message in
// `note` (PLAN.md §1, empty-result codes).
func (a *App) emit(command, gstin, endpoint string, res Result, err error) error {
	if err != nil {
		return a.emitError(command, gstin, endpoint, err)
	}
	if a.Agent {
		env := map[string]any{
			"ok":       true,
			"command":  command,
			"endpoint": endpoint,
			"gstin":    gstin,
			"count":    0,
			"data":     nil,
		}
		if res.Empty {
			env["note"] = res.Note
		} else {
			env["count"] = bestEffortCount(res.Raw)
			env["data"] = json.RawMessage(res.Raw)
		}
		b, _ := json.MarshalIndent(env, "", "  ")
		fmt.Fprintln(a.out, string(b))
		a.wroteEnvelope = true
		return nil
	}
	if res.Empty {
		fmt.Fprintln(a.out, prettyJSON(json.RawMessage(`null`)))
		a.logf("%s: %s", gstin, res.Note)
		return nil
	}
	fmt.Fprintln(a.out, prettyJSON(res.Raw))
	return nil
}

// emitError renders an error consistently and returns it (so the exit code is
// derived from the typed error, not from the rendering).
//
// The re-login guidance goes on the RETURNED error, not just into the --agent
// envelope: main.go prints the returned error, so building the message and then
// returning the bare one was exactly backwards — the agent got the hint and the
// human, who is the one who has to run `auth login`, got nothing
// (docs/conventions.md:45, "every command appends one uniform reLoginMsg").
func (a *App) emitError(command, gstin, endpoint string, err error) error {
	msg := err.Error()
	var aerr *authError
	if asAuthError(err, &aerr) {
		msg = msg + "\n" + reLoginMsg
		err = errAuth("%s", msg) // same type, same exit code, with the guidance
	}
	if a.Agent {
		env := map[string]any{
			"ok":       false,
			"command":  command,
			"endpoint": endpoint,
			"gstin":    gstin,
			"error":    msg,
		}
		b, _ := json.MarshalIndent(env, "", "  ")
		fmt.Fprintln(a.out, string(b))
		a.wroteEnvelope = true
	}
	return err
}

// emitValue prints an already-decoded Go value honouring the same output modes.
func (a *App) emitValue(command, gstin, endpoint string, v any, count int) error {
	b, _ := json.Marshal(v)
	if a.Agent {
		env := map[string]any{
			"ok":       true,
			"command":  command,
			"endpoint": endpoint,
			"gstin":    gstin,
			"count":    count,
			"data":     json.RawMessage(b),
		}
		out, _ := json.MarshalIndent(env, "", "  ")
		fmt.Fprintln(a.out, string(out))
		a.wroteEnvelope = true
		return nil
	}
	out, _ := json.MarshalIndent(v, "", "  ")
	fmt.Fprintln(a.out, string(out))
	return nil
}

// deferred is the uniform notice for an endpoint that exists in the portal but
// whose request shape has not been captured live yet. It is kept in the tree so
// it is discoverable, and it NEVER opens a socket (blinkit/zepto precedent).
func (a *App) deferred(command, note string) error {
	return a.emitError(command, "", "", errUsage("not captured live yet — %s", note))
}
