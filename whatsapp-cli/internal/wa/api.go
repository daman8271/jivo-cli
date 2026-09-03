package wa

// The daemon's loopback API. Only `jwa run` listens, only on 127.0.0.1, and
// this is the only door through which a message leaves this box — the reading
// commands never connect to WhatsApp at all.
//
//	GET  /health          {"linked":…, "connected":…, "state":…}
//	GET  /wait            blocks until an inbound message lands (≤25 s), then {"woke":true|false}
//	POST /send            {"to":"+91…"|"jid","text":"…"}  → {"id":"…"}
//	POST /typing          {"to":"…","on":true|false}

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"net/http"
	"time"

	"go.mau.fi/whatsmeow/types"
)

type sendReq struct {
	To   string `json:"to"`
	Text string `json:"text"`
}

// Serve runs the API until ctx ends. addr is host:port on loopback.
func (c *Client) Serve(ctx context.Context, addr string) error {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		s := ReadStatus(c.Home)
		writeJSON(w, 200, map[string]any{
			"linked":    c.LoggedIn(),
			"connected": c.WA.IsConnected(),
			"state":     s.State,
			"since":     s.Since,
			"me":        c.WA.Store.ID.String(),
		})
	})
	mux.HandleFunc("GET /wait", func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-c.Wake():
			writeJSON(w, 200, map[string]any{"woke": true})
		case <-time.After(25 * time.Second):
			writeJSON(w, 200, map[string]any{"woke": false})
		case <-r.Context().Done():
		}
	})
	mux.HandleFunc("POST /typing", func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			To string `json:"to"`
			On bool   `json:"on"`
		}
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 4<<10)).Decode(&req); err != nil {
			writeJSON(w, 400, map[string]any{"error": "bad json: " + err.Error()})
			return
		}
		to, err := c.deliverable(r.Context(), req.To)
		if err != nil {
			writeJSON(w, 400, map[string]any{"error": err.Error()})
			return
		}
		if err := c.Typing(r.Context(), to, req.On); err != nil {
			writeJSON(w, 502, map[string]any{"error": err.Error()})
			return
		}
		writeJSON(w, 200, map[string]any{"ok": true})
	})
	mux.HandleFunc("POST /send", func(w http.ResponseWriter, r *http.Request) {
		var req sendReq
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 64<<10)).Decode(&req); err != nil {
			writeJSON(w, 400, map[string]any{"error": "bad json: " + err.Error()})
			return
		}
		to, err := c.deliverable(r.Context(), req.To)
		if err != nil {
			writeJSON(w, 400, map[string]any{"error": err.Error()})
			return
		}
		sctx, cancel := context.WithTimeout(r.Context(), 60*time.Second)
		defer cancel()
		id, err := c.SendText(sctx, to, req.Text)
		if err != nil {
			writeJSON(w, 502, map[string]any{"error": err.Error()})
			return
		}
		writeJSON(w, 200, map[string]any{"id": id, "to": to.String()})
	})

	host, _, err := net.SplitHostPort(addr)
	if err != nil {
		return err
	}
	if ip := net.ParseIP(host); ip == nil || !ip.IsLoopback() {
		return errors.New("the API only listens on a loopback address")
	}
	srv := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	go func() {
		<-ctx.Done()
		shut, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		_ = srv.Shutdown(shut)
	}()
	c.Log("%s  api listening on http://%s", stamp(), addr)
	if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return nil
}

// deliverable parses a target and, for a chat keyed by a privacy LID, swaps in
// the phone behind it when the session store knows the mapping.
func (c *Client) deliverable(ctx context.Context, who string) (types.JID, error) {
	to, err := ToJID(who)
	if err != nil {
		return to, err
	}
	if to.Server == types.HiddenUserServer {
		if pn, perr := c.WA.Store.LIDs.GetPNForLID(ctx, to.ToNonAD()); perr == nil && !pn.IsEmpty() {
			to = pn
		}
	}
	return to, nil
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
