package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

// App is the shared command context. Root's PersistentPreRunE resolves the
// Config, builds the Client, and stashes both here; every leaf command reads it.
type App struct {
	cfg        Config
	Client     *Client
	JSON       bool   // --json: pretty JSON output
	Agent      bool   // --agent: implies JSON + stable envelope, suppresses stderr
	Company    string // --company: friendly entity selector
	ManufID    string // manufacturer_id for the offers/brand-fund endpoints
	YesExport  bool   // --yes-export: allow the sanctioned export in --agent mode
	ExportOpt  bool   // per-command --export opt-in for sales/soh pull
	TimeoutStr string
}

// reLoginMsg is the uniform guidance printed on a 401.
const reLoginMsg = "token expired: refresh with `blinkit-partner auth import <curlfile>` or re-run orchestrate/blinkit-login.sh"

// logf writes progress to stderr unless in agent mode (which must stay clean).
func (a *App) logf(format string, args ...any) {
	if !a.Agent {
		fmt.Fprintf(os.Stderr, format+"\n", args...)
	}
}

// emit prints the result of a read. On success it renders JSON (agent envelope
// in --agent mode, pretty JSON in --json, else pretty JSON as the honest
// best-effort for unconfirmed schemas). On error it renders the failure and
// returns it so the process exits non-zero.
func (a *App) emit(command, endpoint string, raw json.RawMessage, err error) error {
	if err != nil {
		return a.emitError(command, endpoint, err)
	}
	if a.Agent {
		env := map[string]any{
			"ok":       true,
			"command":  command,
			"endpoint": endpoint,
			"count":    bestEffortCount(raw),
			"data":     json.RawMessage(raw),
		}
		b, _ := json.MarshalIndent(env, "", "  ")
		fmt.Println(string(b))
		return nil
	}
	fmt.Println(prettyJSON(raw))
	return nil
}

// emitError renders an error consistently and returns it. On a 401 it appends
// the re-login guidance.
func (a *App) emitError(command, endpoint string, err error) error {
	msg := err.Error()
	if errors.Is(err, errUnauthorized) {
		msg = msg + "\n" + reLoginMsg
	}
	if a.Agent {
		env := map[string]any{
			"ok":       false,
			"command":  command,
			"endpoint": endpoint,
			"error":    msg,
		}
		b, _ := json.MarshalIndent(env, "", "  ")
		fmt.Println(string(b))
	}
	return errors.New(msg)
}

// emitValue prints an already-decoded Go value (used for typed results such as
// the reports list) honoring the same output modes.
func (a *App) emitValue(command, endpoint string, v any, count int) error {
	b, _ := json.Marshal(v)
	if a.Agent {
		env := map[string]any{
			"ok":       true,
			"command":  command,
			"endpoint": endpoint,
			"count":    count,
			"data":     json.RawMessage(b),
		}
		out, _ := json.MarshalIndent(env, "", "  ")
		fmt.Println(string(out))
		return nil
	}
	out, _ := json.MarshalIndent(v, "", "  ")
	fmt.Println(string(out))
	return nil
}

// prettyJSON indents raw JSON; if it is not valid JSON it returns it verbatim.
func prettyJSON(raw json.RawMessage) string {
	var v any
	if err := json.Unmarshal(raw, &v); err != nil {
		return string(raw)
	}
	b, _ := json.MarshalIndent(v, "", "  ")
	return string(b)
}

// bestEffortCount tries to report a row count for the agent envelope. It counts
// a top-level array, else a common list field, else 1 for a bare object.
func bestEffortCount(raw json.RawMessage) int {
	var arr []json.RawMessage
	if err := json.Unmarshal(raw, &arr); err == nil {
		return len(arr)
	}
	var obj map[string]json.RawMessage
	if err := json.Unmarshal(raw, &obj); err == nil {
		for _, k := range []string{"reports", "data", "results", "items", "records", "rows", "purchase_orders", "appointments", "invoices", "charges"} {
			if v, ok := obj[k]; ok {
				var a []json.RawMessage
				if json.Unmarshal(v, &a) == nil {
					return len(a)
				}
			}
		}
		return 1
	}
	return 0
}
