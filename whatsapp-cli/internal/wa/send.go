package wa

// send.go is the ONE file in jwa allowed to put something on the wire.
//
// Until 2026-09-02 jwa never sent — it was built for a person's own number.
// That evening it was linked to a SIM bought to be JIVO's bot number ("Jivo
// AI"), and Daman asked for sending. The guard test now allows a send verb in
// this file only; anywhere else it still fails the build. Sends happen only
// through the running daemon's loopback API (see api.go), never from a
// reading command, so `jwa chats` and friends stay network-free.

import (
	"context"
	"fmt"
	"strings"
	"time"

	"go.mau.fi/whatsmeow/proto/waE2E"
	"go.mau.fi/whatsmeow/types"
	"google.golang.org/protobuf/proto"

	"jwa/internal/store"
)

// ToJID turns "+91 93193 79079", "919319379079" or a full JID into the JID to
// send to. A bare 10-digit number is taken as Indian.
func ToJID(who string) (types.JID, error) {
	who = strings.TrimSpace(who)
	if strings.Contains(who, "@") {
		j, err := types.ParseJID(who)
		if err != nil {
			return types.EmptyJID, fmt.Errorf("not a WhatsApp id: %q", who)
		}
		return j, nil
	}
	digits := strings.Map(func(r rune) rune {
		if r >= '0' && r <= '9' {
			return r
		}
		return -1
	}, who)
	if len(digits) == 10 {
		digits = "91" + digits
	}
	if len(digits) < 8 {
		return types.EmptyJID, fmt.Errorf("not a phone number: %q", who)
	}
	return types.NewJID(digits, types.DefaultUserServer), nil
}

// SendText sends one plain text message and records it in the archive, so the
// conversation reads whole from `jwa search` — WhatsApp does not echo our own
// sends back as events.
func (c *Client) SendText(ctx context.Context, to types.JID, text string) (string, error) {
	text = strings.TrimSpace(text)
	if text == "" {
		return "", fmt.Errorf("empty message")
	}
	if !c.WA.IsConnected() {
		return "", fmt.Errorf("not connected to WhatsApp right now (state file says: %s)", ReadStatus(c.Home).State)
	}
	resp, err := c.WA.SendMessage(ctx, to, &waE2E.Message{Conversation: proto.String(text)})
	if err != nil {
		return "", err
	}
	ts := resp.Timestamp
	if ts.IsZero() {
		ts = time.Now()
	}
	m := store.Message{
		ID:         resp.ID,
		ChatJID:    to.String(),
		ChatName:   c.chatName(to),
		SenderJID:  c.WA.Store.ID.String(),
		SenderName: c.WA.Store.PushName,
		FromMe:     true,
		IsGroup:    to.Server == types.GroupServer,
		Timestamp:  ts,
		Body:       text,
	}
	if err := c.DB.Put(m); err != nil {
		c.Log("! sent %s but could not archive it: %v", resp.ID, err)
	}
	c.Log("%s  sent %s to %s: %s", stamp(), resp.ID, to.String(), oneLine(text, 60))
	return resp.ID, nil
}

// Typing shows "typing…" to one chat while an answer is being written. It is
// the only presence jwa ever emits, and only when the loop is really working.
func (c *Client) Typing(ctx context.Context, to types.JID, on bool) error {
	state := types.ChatPresenceComposing
	if !on {
		state = types.ChatPresencePaused
	}
	return c.WA.SendChatPresence(ctx, to, state, types.ChatPresenceMediaText)
}

func oneLine(s string, n int) string {
	s = strings.Join(strings.Fields(s), " ")
	if len(s) > n {
		return s[:n] + "…"
	}
	return s
}
