package main

import (
	"encoding/json"
	"fmt"
	"os"
)

// App carries the shared state every command needs.
type App struct {
	cfg     Config
	Client  *Client
	JSON    bool
	Agent   bool
	Account string
}

// envelope is the stable agent-mode shape: predictable keys so a script or an
// agent can consume any command without knowing which one it ran.
type envelope struct {
	OK       bool            `json:"ok"`
	Command  string          `json:"command"`
	Endpoint string          `json:"endpoint"`
	Account  string          `json:"account,omitempty"`
	Error    string          `json:"error,omitempty"`
	Data     json.RawMessage `json:"data,omitempty"`
}

func (a *App) emit(cmd, endpoint string, raw json.RawMessage, err error) error {
	if a.Agent {
		e := envelope{OK: err == nil, Command: cmd, Endpoint: endpoint, Account: a.Account}
		if err != nil {
			e.Error = err.Error()
		} else {
			e.Data = raw
		}
		b, _ := json.MarshalIndent(e, "", "  ")
		fmt.Println(string(b))
		if err != nil {
			os.Exit(1)
		}
		return nil
	}
	if err != nil {
		return err
	}
	var v any
	if json.Unmarshal(raw, &v) == nil {
		b, _ := json.MarshalIndent(v, "", "  ")
		fmt.Println(string(b))
	} else {
		fmt.Println(string(raw))
	}
	return nil
}

// get performs an allowlisted GET.
func (a *App) get(cmd, host, path string) error {
	url := host + path
	raw, err := a.Client.do("GET", url, nil)
	return a.emit(cmd, "GET "+url, raw, err)
}

// postRead performs an allowlisted POST-to-read. Most Swiggy reads are POSTs
// (list / search / metrics), which is why the transport permits POST at all.
func (a *App) postRead(cmd, host, path string, body []byte) error {
	url := host + path
	if body == nil {
		body = []byte("{}")
	}
	raw, err := a.Client.do("POST", url, body)
	return a.emit(cmd, "POST "+url, raw, err)
}
