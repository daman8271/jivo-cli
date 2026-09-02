package wa

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"go.mau.fi/whatsmeow/types"
)

// The daemon's own account of itself, for `jwa doctor` and the health cron —
// two plain files under ~/.jwa, so nothing outside the daemon has to open
// session.db to learn whether the link is alive.
//
//	state      what the connection last did — starting, connected,
//	           disconnected, stopped, linked — or one of the fatal states
//	heartbeat  rewritten every minute while the socket is up; its age is the
//	           liveness signal
//
// Fatal states (the daemon exits on these; systemd restarts it, and a phone or
// a rebuild is needed before it works again):
//
//	logged_out  WhatsApp removed this device — scan a new QR
//	replaced    something else connected with the same session keys
//	banned      a temporary ban; the daemon waits it out before exiting
//	outdated    WhatsApp rejects this whatsmeow build — bump go.mod, rebuild
//	unlinked    `jwa run` started with no device keys at all
const (
	StateFile      = "state"
	HeartbeatFile  = "heartbeat"
	heartbeatEvery = time.Minute
)

// Fatal is what the daemon receives when the link is gone until a human or a
// rebuild fixes it. Wait says how long to sit before exiting, so a ban or an
// outdated build is not hammered every 15 seconds by systemd's restart.
type Fatal struct {
	Err  error
	Wait time.Duration
}

// Status is what ReadStatus finds on disk.
type Status struct {
	State, Detail string
	Since, At     time.Time // Since: this state was entered; At: last write
	Heartbeat     time.Time // zero if the daemon never wrote one
}

func IsFatalState(s string) bool {
	switch s {
	case "logged_out", "replaced", "banned", "outdated", "unlinked":
		return true
	}
	return false
}

func stamp() string { return time.Now().Format("2006-01-02 15:04:05") }

// Note records a state transition: one log line and the state file. `since`
// only moves when the state name changes, so a flapping socket still shows
// how long it has been flapping.
func (c *Client) Note(state, detail string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := time.Now()
	if state != c.state {
		c.since, c.state = now, state
	}
	line := state
	if detail != "" {
		line += " — " + detail
	}
	c.Log("%s  %s", now.Format("2006-01-02 15:04:05"), line)

	body := fmt.Sprintf("state=%s\nsince=%s\nat=%s\ndetail=%s\n",
		state, c.since.Format(time.RFC3339), now.Format(time.RFC3339),
		strings.ReplaceAll(detail, "\n", " "))
	writeAtomic(filepath.Join(c.Home, StateFile), body)
}

func (c *Client) fatal(state, detail string, wait time.Duration) {
	c.Note(state, detail)
	select {
	case c.Fatal <- Fatal{Err: fmt.Errorf("%s: %s", state, detail), Wait: wait}:
	default: // one is enough; the daemon exits on the first
	}
}

// beat rewrites the heartbeat file if the socket is really up.
func (c *Client) beat() {
	if c.WA.IsConnected() {
		writeAtomic(filepath.Join(c.Home, HeartbeatFile), time.Now().Format(time.RFC3339)+"\n")
	}
}

// Heartbeat beats once a minute until ctx ends. Run it in its own goroutine.
func (c *Client) Heartbeat(ctx context.Context) {
	tick := time.NewTicker(heartbeatEvery)
	defer tick.Stop()
	c.beat()
	for {
		select {
		case <-ctx.Done():
			return
		case <-tick.C:
			c.beat()
		}
	}
}

// ReadStatus is the doctor's and the health check's view — files only, no DB.
func ReadStatus(home string) Status {
	var s Status
	if b, err := os.ReadFile(filepath.Join(home, StateFile)); err == nil {
		for _, ln := range strings.Split(string(b), "\n") {
			k, v, ok := strings.Cut(ln, "=")
			if !ok {
				continue
			}
			switch k {
			case "state":
				s.State = v
			case "detail":
				s.Detail = v
			case "since":
				s.Since, _ = time.Parse(time.RFC3339, v)
			case "at":
				s.At, _ = time.Parse(time.RFC3339, v)
			}
		}
	}
	if st, err := os.Stat(filepath.Join(home, HeartbeatFile)); err == nil {
		s.Heartbeat = st.ModTime()
	}
	return s
}

func writeAtomic(path, body string) {
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, []byte(body), 0o600); err != nil {
		return
	}
	_ = os.Rename(tmp, path)
}

// Identify turns whatever an operator typed — "+91 88990 11758", "918899011758",
// "185414426054881@lid" — into every bare user id WhatsApp uses for that person,
// via the LID↔phone map whatsmeow keeps in the session store. It reads the
// store; it does not connect. phone is "+<digits>" when the number is known.
func (c *Client) Identify(who string) (users []string, phone string, err error) {
	ctx := context.Background()
	who = strings.TrimSpace(who)
	var pn, lid types.JID
	if strings.Contains(who, "@") {
		j, perr := types.ParseJID(who)
		if perr != nil {
			return nil, "", fmt.Errorf("not a WhatsApp id: %q", who)
		}
		j.Device = 0
		if j.Server == types.HiddenUserServer {
			lid = j
		} else {
			pn = j
		}
	} else {
		digits := strings.Map(func(r rune) rune {
			if r >= '0' && r <= '9' {
				return r
			}
			return -1
		}, who)
		if len(digits) == 10 {
			digits = "91" + digits // an Indian mobile typed without the country code
		}
		if len(digits) < 8 {
			return nil, "", fmt.Errorf("not a phone number: %q", who)
		}
		pn = types.NewJID(digits, types.DefaultUserServer)
	}
	if !pn.IsEmpty() && lid.IsEmpty() {
		if l, lerr := c.WA.Store.LIDs.GetLIDForPN(ctx, pn); lerr == nil && !l.IsEmpty() {
			lid = l
		}
	}
	if !lid.IsEmpty() && pn.IsEmpty() {
		if p, perr := c.WA.Store.LIDs.GetPNForLID(ctx, lid); perr == nil && !p.IsEmpty() {
			pn = p
		}
	}
	if !pn.IsEmpty() {
		users = append(users, pn.User)
		phone = "+" + pn.User
	}
	if !lid.IsEmpty() {
		users = append(users, lid.User)
	}
	return users, phone, nil
}
