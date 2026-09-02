package wa

// The daemon's loopback API. Only `jwa run` listens, only on 127.0.0.1, and
// this is the only door through which a message leaves this box — the reading
// commands never connect to WhatsApp at all.
//
//	GET  /health          {"linked":…, "connected":…, "state":…}
//	POST /send            {"to":"+91…"|"jid","text":"…"}  → {"id":"…"}

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
	mux.HandleFunc("POST /send", func(w http.ResponseWriter, r *http.Request) {
		var req sendReq
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 64<<10)).Decode(&req); err != nil {
			writeJSON(w, 400, map[string]any{"error": "bad json: " + err.Error()})
			return
		}
		to, err := ToJID(req.To)
		if err != nil {
			writeJSON(w, 400, map[string]any{"error": err.Error()})
			return
		}
		// A chat keyed by a privacy LID is delivered to the phone behind it
		// when the session store knows the mapping; otherwise send to the LID.
		if to.Server == types.HiddenUserServer {
			if pn, perr := c.WA.Store.LIDs.GetPNForLID(r.Context(), to.ToNonAD()); perr == nil && !pn.IsEmpty() {
				to = pn
			}
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

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
