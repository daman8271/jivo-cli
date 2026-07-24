package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

// App is the shared command context. Root's PersistentPreRunE resolves the
// Config, builds the Client, and stashes both here; every leaf command reads it.
// The host-root fields let a section command pick the right backend per endpoint
// (Zepto spreads its API over 7 hosts, all sharing one JWT).
type App struct {
	cfg     Config
	Client  *Client
	JSON    bool   // --json: pretty JSON output
	Agent   bool   // --agent: implies JSON + stable envelope, suppresses stderr
	BrandID string // ads brand_id
	ManufID string // manufacturer_id (Jivo Wellness)
}

// Backend host roots are the package-level host* constants (config.go). Section
// commands pass the right one to the leaf builders at construction time; do NOT
// stash them on App (App fields are zero until PersistentPreRunE, which runs
// AFTER the command tree is built).

// reLoginMsg is the uniform guidance printed on a 401. Zepto's JWT is daily.
const reLoginMsg = "token expired (Zepto JWT expires 23:59:59 IST daily): refresh with `bash ~/ecomcliauto/orchestrate/zepto-login.sh` or `zepto-portal auth import <curlfile>`"

// logf writes progress to stderr unless in agent mode (which must stay clean).
func (a *App) logf(format string, args ...any) {
	if !a.Agent {
		fmt.Fprintf(os.Stderr, format+"\n", args...)
	}
}

// get does an authenticated GET against host+path and emits the raw result.
func (a *App) get(command, host, path string) error {
	url := joinURL(host, path)
	raw, err := a.Client.doRaw("GET", url, nil)
	return a.emit(command, url, raw, err)
}

// post does an authenticated POST-to-read against host+path and emits the raw
// result. body may be nil.
func (a *App) post(command, host, path string, body []byte) error {
	url := joinURL(host, path)
	raw, err := a.Client.doRaw("POST", url, body)
	return a.emit(command, url, raw, err)
}

// deferred prints a uniform "endpoint to confirm" notice for endpoints whose
// exact request shape needs one live capture before wiring — kept in the tree
// so it is discoverable, never invented.
func (a *App) deferred(command, note string) error {
	return a.emitError(command, note, fmt.Errorf("endpoint to confirm — capture live first: %s", note))
}

// emit renders the result of a read: agent envelope in --agent, else pretty JSON.
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

// emitValue prints an already-decoded Go value honoring the same output modes.
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

func prettyJSON(raw json.RawMessage) string {
	var v any
	if err := json.Unmarshal(raw, &v); err != nil {
		return string(raw)
	}
	b, _ := json.MarshalIndent(v, "", "  ")
	return string(b)
}

// bestEffortCount reports a row count for the agent envelope: a top-level array,
// else a common list field, else 1 for a bare object.
func bestEffortCount(raw json.RawMessage) int {
	var arr []json.RawMessage
	if err := json.Unmarshal(raw, &arr); err == nil {
		return len(arr)
	}
	var obj map[string]json.RawMessage
	if err := json.Unmarshal(raw, &obj); err == nil {
		// Zepto commonly wraps rows under "data"; unwrap one level then count.
		if d, ok := obj["data"]; ok {
			var a []json.RawMessage
			if json.Unmarshal(d, &a) == nil {
				return len(a)
			}
			var inner map[string]json.RawMessage
			if json.Unmarshal(d, &inner) == nil {
				obj = inner
			}
		}
		for _, k := range []string{"reports", "results", "items", "records", "rows", "content", "orders", "campaigns", "invoices", "list", "entries", "purchaseOrders", "data"} {
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

// joinURL joins a host root and a path with exactly one slash.
func joinURL(host, path string) string {
	if path == "" {
		return host
	}
	if path[0] != '/' {
		path = "/" + path
	}
	for len(host) > 0 && host[len(host)-1] == '/' {
		host = host[:len(host)-1]
	}
	return host + path
}
