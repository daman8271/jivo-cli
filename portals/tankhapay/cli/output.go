package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
)

// App is the shared command context; root's PersistentPreRunE fills cfg + Client.
type App struct {
	cfg    Config
	Client *Client
	JSON   bool
	Agent  bool
}

const reLoginMsg = "auth failed: the CLI auto-logs-in from .env — check TPAY_USERNAME/TPAY_PASSWORD, or run `tankhapay-portal auth login`"

func (a *App) logf(format string, args ...any) {
	if !a.Agent {
		fmt.Fprintf(os.Stderr, format+"\n", args...)
	}
}

// runRead executes one read and emits it in the selected output mode.
func (a *App) runRead(command, backend, relPath string, payload []byte) error {
	raw, err := a.Client.doRead(backend, relPath, payload)
	return a.emit(command, backend+":/"+relPath, raw, err)
}

func (a *App) emit(command, endpoint string, raw json.RawMessage, err error) error {
	if err != nil {
		return a.emitError(command, endpoint, err)
	}
	if a.Agent {
		env := map[string]any{"ok": true, "command": command, "endpoint": endpoint, "count": bestEffortCount(raw), "data": raw}
		b, _ := json.MarshalIndent(env, "", "  ")
		fmt.Println(string(b))
		return nil
	}
	fmt.Println(prettyJSON(raw))
	return nil
}

func (a *App) emitError(command, endpoint string, err error) error {
	msg := err.Error()
	if errors.Is(err, errUnauthorized) {
		msg += "\n" + reLoginMsg
	}
	if a.Agent {
		env := map[string]any{"ok": false, "command": command, "endpoint": endpoint, "error": msg}
		b, _ := json.MarshalIndent(env, "", "  ")
		fmt.Println(string(b))
	}
	return errors.New(msg)
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
	if json.Unmarshal(raw, &arr) == nil {
		return len(arr)
	}
	var obj map[string]json.RawMessage
	if json.Unmarshal(raw, &obj) == nil {
		for _, k := range []string{"data", "result", "results", "list", "rows", "records", "items", "employees", "reports", "content"} {
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

func mustJSON(v any) []byte {
	b, _ := json.Marshal(v)
	return b
}

// joinURL joins a backend base and a relative path with exactly one slash.
func joinURL(base, rel string) string {
	for len(base) > 0 && base[len(base)-1] == '/' {
		base = base[:len(base)-1]
	}
	rel = strings.TrimLeft(rel, "/")
	if rel == "" {
		return base
	}
	return base + "/" + rel
}
