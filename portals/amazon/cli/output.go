package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
)

// App is the shared command context.
type App struct {
	Client *Client
	cfg    Config
	pretty bool
}

// emit prints a JSON response, pretty by default.
func (a *App) emit(raw json.RawMessage) error {
	if !a.pretty {
		fmt.Println(string(raw))
		return nil
	}
	var buf bytes.Buffer
	if err := json.Indent(&buf, raw, "", "  "); err != nil {
		fmt.Println(string(raw)) // not JSON — print as-is
		return nil
	}
	fmt.Println(buf.String())
	return nil
}

// run resolves an endpoint's path params from args, guards, GETs, and prints.
func (a *App) run(e Endpoint, args []string) error {
	if err := a.cfg.requireSession(); err != nil {
		return err
	}
	resolved := e.Path
	if e.Params != "" {
		names := splitPipe(e.Params)
		if len(args) < len(names) {
			return fmt.Errorf("%s needs %d argument(s): %s", e.Name, len(names), e.Params)
		}
		for i, n := range names {
			resolved = replaceOnce(resolved, "{"+n+"}", args[i])
		}
	}
	raw, _, err := a.Client.get(e.Host, e.Path, resolved)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return err
	}
	return a.emit(raw)
}

func splitPipe(s string) []string {
	if s == "" {
		return nil
	}
	var out []string
	cur := ""
	for _, r := range s {
		if r == '|' {
			out = append(out, cur)
			cur = ""
		} else {
			cur += string(r)
		}
	}
	return append(out, cur)
}

func replaceOnce(s, old, new string) string {
	i := indexOf(s, old)
	if i < 0 {
		return s
	}
	return s[:i] + new + s[i+len(old):]
}

func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}
