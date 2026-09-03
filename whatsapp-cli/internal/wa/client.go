// Package wa wraps whatsmeow for jwa.
//
// Sending is confined to ONE file, send.go, and reachable only through the
// running daemon's loopback API (api.go). Every other file — and every reading
// command — must never put anything on the wire; the guard test in
// client_guard_test.go walks the module's syntax tree and fails the build if a
// send verb appears anywhere else. No read receipts, no presence, no typing.
package wa

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"go.mau.fi/whatsmeow"
	waProto "go.mau.fi/whatsmeow/binary/proto"
	"go.mau.fi/whatsmeow/store/sqlstore"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/types/events"
	waLog "go.mau.fi/whatsmeow/util/log"

	"jwa/internal/store"
)

// Forbidden is the tripwire list. Kept next to the code it protects so a future
// edit that reaches for one of these fails loudly rather than quietly messaging
// somebody from Karanpreet's number.
var Forbidden = []string{
	"SendMessage", "SendChatPresence", "SendPresence", "MarkRead", "SendReceipt",
	"BuildRevoke", "SetStatusMessage", "SetGroupName", "JoinGroupWithLink",
	"LeaveGroup", "CreateGroup", "UpdateBlocklist", "SetDisappearingTimer",
}

type Client struct {
	WA      *whatsmeow.Client
	DB      *store.DB
	MediaTo string
	Home    string     // ~/.jwa — where state and heartbeat are written
	Fatal   chan Fatal // the daemon exits when something lands here
	Log     func(string, ...any)

	mu    sync.Mutex
	state string
	since time.Time

	lidSeen map[string]bool // LIDs already checked against the names table

	// wake is closed and replaced every time an inbound message is stored, so
	// the API's /wait can hand a message to the answering loop the instant it
	// arrives instead of the loop polling the archive.
	wakeMu sync.Mutex
	wake   chan struct{}
}

// Open builds the client but does not connect.
//
// sessionPath is whatsmeow's own device store — the linked-device keys. Losing
// it means scanning the QR again; copying it elsewhere means two things
// pretending to be the same device, which WhatsApp will notice.
func Open(sessionPath, archivePath, mediaDir string, verbose bool) (*Client, error) {
	for _, d := range []string{filepath.Dir(sessionPath), filepath.Dir(archivePath), mediaDir} {
		if err := os.MkdirAll(d, 0o700); err != nil {
			return nil, err
		}
	}

	level := "ERROR"
	if verbose {
		level = "INFO"
	}
	dbLog := waLog.Stdout("session", level, true)

	container, err := sqlstore.New(context.Background(), "sqlite",
		// WAL + a busy timeout: whatsmeow writes keys from several goroutines
		// at once and `jwa doctor` opens the same file while the daemon runs.
		// Without these the log fills with SQLITE_BUSY and a key write can be
		// lost — which is how a "random" logout starts.
		"file:"+sessionPath+"?_pragma=foreign_keys(1)&_pragma=journal_mode(WAL)&_pragma=busy_timeout(10000)", dbLog)
	if err != nil {
		return nil, fmt.Errorf("open session store: %w", err)
	}
	device, err := container.GetFirstDevice(context.Background())
	if err != nil {
		return nil, fmt.Errorf("read device: %w", err)
	}

	// The device store is as good as the account: anyone holding this file IS
	// the linked device. whatsmeow creates it 0644; the enclosing directory is
	// 0700 but on a shared box the file itself should not be world-readable.
	for _, f := range []string{sessionPath, sessionPath + "-wal", sessionPath + "-shm"} {
		if _, err := os.Stat(f); err == nil {
			_ = os.Chmod(f, 0o600)
		}
	}

	archive, err := store.Open(archivePath)
	if err != nil {
		return nil, fmt.Errorf("open archive: %w", err)
	}

	c := &Client{
		WA:      whatsmeow.NewClient(device, waLog.Stdout("client", level, true)),
		DB:      archive,
		MediaTo: mediaDir,
		Home:    filepath.Dir(sessionPath),
		Fatal:   make(chan Fatal, 1),
		Log:     func(f string, a ...any) { fmt.Printf(f+"\n", a...) },
	}
	c.WA.AddEventHandler(c.handle)
	return c, nil
}

func (c *Client) Close() {
	c.WA.Disconnect()
	c.DB.Close()
}

// LoggedIn reports whether the device store already holds a linked session.
func (c *Client) LoggedIn() bool { return c.WA.Store.ID != nil }

// Pair connects and, if this device is not linked yet, prints the QR codes for
// the operator to scan from WhatsApp on the phone:
// Settings -> Linked devices -> Link a device.
func (c *Client) Pair(ctx context.Context, showQR func(string)) error {
	if c.LoggedIn() {
		return c.WA.Connect()
	}
	ch, err := c.WA.GetQRChannel(ctx)
	if err != nil {
		return err
	}
	if err := c.WA.Connect(); err != nil {
		return err
	}
	for evt := range ch {
		switch evt.Event {
		case "code":
			showQR(evt.Code)
		case "success":
			return nil
		case "timeout":
			return fmt.Errorf("QR expired before it was scanned — run `jwa login` again")
		default:
			// whatsmeow reports every other outcome as err-*: an outdated
			// client, a scan from a phone that is not on multi-device, a lost
			// socket. None of them linked anything.
			if strings.HasPrefix(evt.Event, "err") {
				return fmt.Errorf("pairing failed: %s", evt.Event)
			}
		}
	}

	// The channel closed without ever saying "success" — the process was
	// killed, the socket dropped, or the context was cancelled. Nothing is
	// linked, and saying nothing here would let the caller print a cheerful
	// "Linked." over a number that is not.
	if !c.LoggedIn() {
		return fmt.Errorf("pairing ended without linking — the QR window closed before a phone scanned it; run `jwa login` again")
	}
	return nil
}

// handle is the only place an inbound event turns into a stored row.
func (c *Client) handle(raw any) {
	switch evt := raw.(type) {
	case *events.Message:
		c.record(evt)
	case *events.HistorySync:
		// WhatsApp pushes a slice of recent history right after linking. It is
		// whatever the phone chose to send — never the full archive.
		for _, conv := range evt.Data.GetConversations() {
			for _, h := range conv.GetMessages() {
				if m := h.GetMessage(); m != nil {
					c.recordHistory(conv.GetID(), m)
				}
			}
		}
	case *events.OfflineSyncCompleted:
		c.Log("%s  offline sync done, %d messages caught up", stamp(), evt.Count)

	// Connection state. Everything below is what "it just logged out" looks
	// like from the inside; each case leaves a verdict in ~/.jwa/state.
	case *events.Connected:
		c.Note("connected", "")
		c.beat()
	case *events.KeepAliveRestored:
		c.Note("connected", "keepalive restored")
		c.beat()
	case *events.Disconnected:
		// whatsmeow reconnects on its own (EnableAutoReconnect is on by
		// default); this only marks the gap so doctor and the health cron see it.
		c.Note("disconnected", "socket closed; whatsmeow is reconnecting")
	case *events.KeepAliveTimeout:
		c.Note("disconnected", fmt.Sprintf("keepalive timed out %d× (last ok %s)",
			evt.ErrorCount, evt.LastSuccess.Format("15:04:05")))
	case *events.StreamError:
		c.Note("disconnected", "stream error "+evt.Code)
	case *events.ConnectFailure:
		c.Note("disconnected", fmt.Sprintf("connect failure %s: %s", evt.Reason, evt.Message))

	// Fatal: the daemon exits on these. whatsmeow has already given up
	// reconnecting, and only a phone or a rebuild gets the link back.
	case *events.LoggedOut:
		c.fatal("logged_out", fmt.Sprintf("WhatsApp removed this device (%s) — a phone must scan a new QR: jwa login", evt.Reason), 0)
	case *events.StreamReplaced:
		c.fatal("replaced", "another client connected with this session — a second `jwa run`, or a copied session.db?", time.Minute)
	case *events.TemporaryBan:
		wait := evt.Expire
		if wait <= 0 {
			wait = time.Hour
		}
		if wait > 24*time.Hour {
			wait = 24 * time.Hour
		}
		c.fatal("banned", evt.String(), wait)
	case *events.ClientOutdated:
		c.fatal("outdated", "WhatsApp rejects this whatsmeow build as too old — bump go.mod, rebuild, restart", time.Hour)
	}
}

func (c *Client) record(evt *events.Message) {
	m := store.Message{
		ID:         evt.Info.ID,
		ChatJID:    evt.Info.Chat.String(),
		ChatName:   c.chatName(evt.Info.Chat),
		SenderJID:  evt.Info.Sender.String(),
		SenderName: evt.Info.PushName,
		FromMe:     evt.Info.IsFromMe,
		IsGroup:    evt.Info.IsGroup,
		Timestamp:  evt.Info.Timestamp,
		Body:       bodyOf(evt.Message),
	}
	c.attachMedia(&m, evt.Message)
	if err := c.DB.Put(m); err != nil {
		c.Log("! could not store %s: %v", m.ID, err)
	}
	c.learnLID(evt.Info.Chat)
	c.learnLID(evt.Info.Sender)
	if !evt.Info.IsFromMe {
		c.wakeAll()
	}
}

func (c *Client) wakeAll() {
	c.wakeMu.Lock()
	if c.wake != nil {
		close(c.wake)
	}
	c.wake = make(chan struct{})
	c.wakeMu.Unlock()
}

// Wake returns a channel closed on the next inbound message.
func (c *Client) Wake() <-chan struct{} {
	c.wakeMu.Lock()
	defer c.wakeMu.Unlock()
	if c.wake == nil {
		c.wake = make(chan struct{})
	}
	return c.wake
}

// learnLID completes a label that was given by phone number only. WhatsApp
// addresses people by LID, and the LID for a phone is unknown until the first
// message from it arrives — this is that moment, so the label is copied across.
func (c *Client) learnLID(j types.JID) {
	if j.Server != types.HiddenUserServer {
		return
	}
	c.mu.Lock()
	seen := c.lidSeen[j.User]
	if !seen {
		if c.lidSeen == nil {
			c.lidSeen = map[string]bool{}
		}
		c.lidSeen[j.User] = true
	}
	c.mu.Unlock()
	if seen {
		return
	}
	pn, err := c.WA.Store.LIDs.GetPNForLID(context.Background(), j.ToNonAD())
	if err != nil || pn.IsEmpty() {
		return
	}
	if err := c.DB.CopyName(pn.User, j.User); err != nil {
		c.Log("! could not carry the name of %s to %s: %v", pn.User, j.User, err)
	}
}

func (c *Client) recordHistory(chatJID string, msg *waProto.WebMessageInfo) {
	ts := time.Unix(int64(msg.GetMessageTimestamp()), 0)
	m := store.Message{
		ID:        msg.GetKey().GetID(),
		ChatJID:   chatJID,
		FromMe:    msg.GetKey().GetFromMe(),
		IsGroup:   strings.Contains(chatJID, "@g.us"),
		Timestamp: ts,
		Body:      bodyOf(msg.GetMessage()),
	}
	if m.ID == "" {
		return
	}
	_ = c.DB.Put(m)
}

// attachMedia downloads images, documents and audio to disk. A vendor's bill
// arrives as an image or a PDF document, which is the whole reason this exists.
func (c *Client) attachMedia(m *store.Message, msg *waProto.Message) {
	var (
		dl   whatsmeow.DownloadableMessage
		kind string
		name string
	)
	switch {
	case msg.GetImageMessage() != nil:
		im := msg.GetImageMessage()
		dl, kind, name = im, "image", m.ID+".jpg"
	case msg.GetDocumentMessage() != nil:
		doc := msg.GetDocumentMessage()
		dl, kind = doc, "document"
		name = doc.GetFileName()
		if name == "" {
			name = m.ID + ".bin"
		}
	case msg.GetAudioMessage() != nil:
		dl, kind, name = msg.GetAudioMessage(), "audio", m.ID+".ogg"
	case msg.GetVideoMessage() != nil:
		dl, kind, name = msg.GetVideoMessage(), "video", m.ID+".mp4"
	default:
		return
	}

	m.MediaType, m.MediaName = kind, name
	data, err := c.WA.Download(context.Background(), dl)
	if err != nil {
		c.Log("! %s from %s did not download: %v", kind, m.ChatName, err)
		return
	}
	day := m.Timestamp.Format("2006-01-02")
	dir := filepath.Join(c.MediaTo, day)
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return
	}
	path := filepath.Join(dir, safeName(m.ID+"_"+name))
	if err := os.WriteFile(path, data, 0o600); err != nil {
		c.Log("! could not save %s: %v", path, err)
		return
	}
	m.MediaPath, m.MediaSize = path, int64(len(data))
}

func (c *Client) chatName(jid types.JID) string {
	if contact, err := c.WA.Store.Contacts.GetContact(context.Background(), jid); err == nil {
		if contact.FullName != "" {
			return contact.FullName
		}
		if contact.PushName != "" {
			return contact.PushName
		}
	}
	if info, err := c.WA.GetGroupInfo(context.Background(), jid); err == nil && info.Name != "" {
		return info.Name
	}
	return jid.User
}

// bodyOf pulls the readable text out of whichever envelope WhatsApp used.
func bodyOf(msg *waProto.Message) string {
	if msg == nil {
		return ""
	}
	if t := msg.GetConversation(); t != "" {
		return t
	}
	if e := msg.GetExtendedTextMessage(); e != nil {
		return e.GetText()
	}
	if im := msg.GetImageMessage(); im != nil {
		return im.GetCaption()
	}
	if doc := msg.GetDocumentMessage(); doc != nil {
		if cap := doc.GetCaption(); cap != "" {
			return cap
		}
		return doc.GetFileName()
	}
	if v := msg.GetVideoMessage(); v != nil {
		return v.GetCaption()
	}
	return ""
}

func safeName(s string) string {
	var b strings.Builder
	for _, r := range s {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9',
			r == '.', r == '-', r == '_':
			b.WriteRune(r)
		default:
			b.WriteRune('_')
		}
	}
	out := b.String()
	if len(out) > 120 {
		out = out[:120]
	}
	return out
}
