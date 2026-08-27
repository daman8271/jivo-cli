// Package store is jwa's own archive of what arrived on WhatsApp.
//
// whatsmeow keeps its *session* in a separate database of its own. This one is
// ours: every message the daemon sees is appended here, and every CLI read goes
// through here rather than back to WhatsApp. That split is deliberate — the
// reading commands can never touch the network, so they can never send.
package store

import (
	"database/sql"
	"fmt"
	"time"

	_ "modernc.org/sqlite"
)

const schema = `
CREATE TABLE IF NOT EXISTS messages (
    id           TEXT PRIMARY KEY,
    chat_jid     TEXT NOT NULL,
    chat_name    TEXT NOT NULL DEFAULT '',
    sender_jid   TEXT NOT NULL DEFAULT '',
    sender_name  TEXT NOT NULL DEFAULT '',
    from_me      INTEGER NOT NULL DEFAULT 0,
    is_group     INTEGER NOT NULL DEFAULT 0,
    ts           INTEGER NOT NULL,
    body         TEXT NOT NULL DEFAULT '',
    media_type   TEXT NOT NULL DEFAULT '',
    media_name   TEXT NOT NULL DEFAULT '',
    media_path   TEXT NOT NULL DEFAULT '',
    media_size   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_jid, ts DESC);
CREATE INDEX IF NOT EXISTS idx_messages_ts   ON messages(ts DESC);
CREATE INDEX IF NOT EXISTS idx_messages_med  ON messages(media_type) WHERE media_type <> '';
`

// Message is one WhatsApp message as jwa keeps it.
type Message struct {
	ID         string
	ChatJID    string
	ChatName   string
	SenderJID  string
	SenderName string
	FromMe     bool
	IsGroup    bool
	Timestamp  time.Time
	Body       string
	MediaType  string
	MediaName  string
	MediaPath  string
	MediaSize  int64
}

// Chat is one conversation, summarised from the messages we hold.
type Chat struct {
	JID      string
	Name     string
	IsGroup  bool
	Messages int
	Media    int
	LastSeen time.Time
}

type DB struct{ sql *sql.DB }

func Open(path string) (*DB, error) {
	h, err := sql.Open("sqlite", "file:"+path+"?_pragma=journal_mode(WAL)&_pragma=busy_timeout(5000)")
	if err != nil {
		return nil, err
	}
	if _, err := h.Exec(schema); err != nil {
		h.Close()
		return nil, fmt.Errorf("create schema: %w", err)
	}
	return &DB{sql: h}, nil
}

func (d *DB) Close() error { return d.sql.Close() }

// Put is an upsert — WhatsApp re-delivers on reconnect, and a duplicate arriving
// twice must not become two rows.
func (d *DB) Put(m Message) error {
	_, err := d.sql.Exec(`
        INSERT INTO messages
            (id, chat_jid, chat_name, sender_jid, sender_name, from_me, is_group,
             ts, body, media_type, media_name, media_path, media_size)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            chat_name  = excluded.chat_name,
            media_path = CASE WHEN excluded.media_path <> '' THEN excluded.media_path
                              ELSE messages.media_path END`,
		m.ID, m.ChatJID, m.ChatName, m.SenderJID, m.SenderName, b2i(m.FromMe),
		b2i(m.IsGroup), m.Timestamp.Unix(), m.Body, m.MediaType, m.MediaName,
		m.MediaPath, m.MediaSize)
	return err
}

func (d *DB) Counts() (messages, media, chats int, oldest, newest time.Time, err error) {
	var o, n sql.NullInt64
	err = d.sql.QueryRow(`
        SELECT COUNT(*),
               COALESCE(SUM(media_type <> ''), 0),
               COUNT(DISTINCT chat_jid),
               MIN(ts), MAX(ts)
        FROM messages`).Scan(&messages, &media, &chats, &o, &n)
	if o.Valid {
		oldest = time.Unix(o.Int64, 0)
	}
	if n.Valid {
		newest = time.Unix(n.Int64, 0)
	}
	return
}

func (d *DB) Chats(limit int) ([]Chat, error) {
	rows, err := d.sql.Query(`
        SELECT chat_jid,
               COALESCE(NULLIF(MAX(chat_name), ''), chat_jid),
               MAX(is_group), COUNT(*),
               COALESCE(SUM(media_type <> ''), 0), MAX(ts)
        FROM messages
        GROUP BY chat_jid
        ORDER BY MAX(ts) DESC
        LIMIT ?`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Chat
	for rows.Next() {
		var c Chat
		var grp int
		var ts int64
		if err := rows.Scan(&c.JID, &c.Name, &grp, &c.Messages, &c.Media, &ts); err != nil {
			return nil, err
		}
		c.IsGroup, c.LastSeen = grp == 1, time.Unix(ts, 0)
		out = append(out, c)
	}
	return out, rows.Err()
}

// Query is the one filter type the reading commands share.
type Query struct {
	Chat      string // substring of chat name or JID
	Sender    string // substring of sender name or JID
	Text      string // substring of the message body
	Since     time.Time
	OnlyMedia bool
	Limit     int
}

func (d *DB) Search(q Query) ([]Message, error) {
	sqlStr := `SELECT id, chat_jid, chat_name, sender_jid, sender_name, from_me,
                      is_group, ts, body, media_type, media_name, media_path, media_size
               FROM messages WHERE 1=1`
	var args []any
	if q.Chat != "" {
		sqlStr += ` AND (LOWER(chat_name) LIKE ? OR LOWER(chat_jid) LIKE ?)`
		args = append(args, like(q.Chat), like(q.Chat))
	}
	if q.Sender != "" {
		sqlStr += ` AND (LOWER(sender_name) LIKE ? OR LOWER(sender_jid) LIKE ?)`
		args = append(args, like(q.Sender), like(q.Sender))
	}
	if q.Text != "" {
		sqlStr += ` AND LOWER(body) LIKE ?`
		args = append(args, like(q.Text))
	}
	if !q.Since.IsZero() {
		sqlStr += ` AND ts >= ?`
		args = append(args, q.Since.Unix())
	}
	if q.OnlyMedia {
		sqlStr += ` AND media_type <> ''`
	}
	sqlStr += ` ORDER BY ts DESC LIMIT ?`
	if q.Limit <= 0 {
		q.Limit = 50
	}
	args = append(args, q.Limit)

	rows, err := d.sql.Query(sqlStr, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Message
	for rows.Next() {
		var m Message
		var fromMe, grp int
		var ts int64
		if err := rows.Scan(&m.ID, &m.ChatJID, &m.ChatName, &m.SenderJID, &m.SenderName,
			&fromMe, &grp, &ts, &m.Body, &m.MediaType, &m.MediaName, &m.MediaPath,
			&m.MediaSize); err != nil {
			return nil, err
		}
		m.FromMe, m.IsGroup, m.Timestamp = fromMe == 1, grp == 1, time.Unix(ts, 0)
		out = append(out, m)
	}
	return out, rows.Err()
}

func like(s string) string { return "%" + lower(s) + "%" }

func lower(s string) string {
	b := []byte(s)
	for i, c := range b {
		if c >= 'A' && c <= 'Z' {
			b[i] = c + 32
		}
	}
	return string(b)
}

func b2i(b bool) int {
	if b {
		return 1
	}
	return 0
}
