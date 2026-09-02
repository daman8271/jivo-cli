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
	"strings"
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
CREATE TABLE IF NOT EXISTS names (
    jid_user TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    phone    TEXT NOT NULL DEFAULT '',
    set_at   INTEGER NOT NULL
);
`

// Name is a label an operator gave a number — jwa's own address book. The
// phone's contacts do not reach a companion device reliably, and WhatsApp hides
// most senders behind a LID (185414426054881@lid) rather than a phone JID, so
// one label is stored against every user id that means the same person.
type Name struct {
	User  string // bare JID user: 918899011758, or a LID like 185414426054881
	Name  string
	Phone string // +918899011758 when known
	SetAt time.Time
}

// userOf is the SQL for the bare user of a JID column: device suffix and server
// stripped, so 185414426054881:9@lid and 185414426054881@lid name the same person.
func userOf(col string) string {
	return `CASE WHEN instr(` + col + `, ':') > 0 THEN substr(` + col + `, 1, instr(` + col + `, ':') - 1)
	             ELSE substr(` + col + `, 1, instr(` + col + `, '@') - 1) END`
}

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
        SELECT m.chat_jid,
               COALESCE(n.name, NULLIF(MAX(m.chat_name), ''), m.chat_jid),
               MAX(m.is_group), COUNT(*),
               COALESCE(SUM(m.media_type <> ''), 0), MAX(m.ts)
        FROM messages m
        LEFT JOIN names n ON n.jid_user = `+userOf("m.chat_jid")+`
        GROUP BY m.chat_jid
        ORDER BY MAX(m.ts) DESC
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

// Get returns one message by its WhatsApp id — what `jwa pull` is handed.
func (d *DB) Get(id string) (Message, error) {
	var m Message
	var fromMe, grp int
	var ts int64
	err := d.sql.QueryRow(selectMessage+` WHERE m.id = ?`, id).
		Scan(&m.ID, &m.ChatJID, &m.ChatName, &m.SenderJID, &m.SenderName,
			&fromMe, &grp, &ts, &m.Body, &m.MediaType, &m.MediaName, &m.MediaPath,
			&m.MediaSize)
	if err == sql.ErrNoRows {
		return m, fmt.Errorf("no message %q in the archive", id)
	}
	if err != nil {
		return m, err
	}
	m.FromMe, m.IsGroup, m.Timestamp = fromMe == 1, grp == 1, time.Unix(ts, 0)
	return m, nil
}

// Query is the one filter type the reading commands share.
type Query struct {
	Chat      string // substring of chat name or JID
	Sender    string // substring of sender name or JID
	Text      string // substring of the message body
	Since     time.Time
	OnlyMedia bool
	Kinds     []string // media_type whitelist, e.g. image+document for a bill
	Limit     int
}

func (d *DB) Search(q Query) ([]Message, error) {
	sqlStr := selectMessage + ` WHERE 1=1`
	var args []any
	if q.Chat != "" {
		sqlStr += ` AND (LOWER(COALESCE(nc.name, '')) LIKE ? OR LOWER(m.chat_name) LIKE ? OR LOWER(m.chat_jid) LIKE ?)`
		args = append(args, like(q.Chat), like(q.Chat), like(q.Chat))
	}
	if q.Sender != "" {
		sqlStr += ` AND (LOWER(COALESCE(ns.name, '')) LIKE ? OR LOWER(m.sender_name) LIKE ? OR LOWER(m.sender_jid) LIKE ?)`
		args = append(args, like(q.Sender), like(q.Sender), like(q.Sender))
	}
	if q.Text != "" {
		sqlStr += ` AND LOWER(body) LIKE ?`
		args = append(args, like(q.Text))
	}
	if !q.Since.IsZero() {
		sqlStr += ` AND m.ts >= ?`
		args = append(args, q.Since.Unix())
	}
	if q.OnlyMedia {
		sqlStr += ` AND m.media_type <> ''`
	}
	if len(q.Kinds) > 0 {
		sqlStr += ` AND m.media_type IN (` + placeholders(len(q.Kinds)) + `)`
		for _, k := range q.Kinds {
			args = append(args, k)
		}
	}
	sqlStr += ` ORDER BY m.ts DESC LIMIT ?`
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

// selectMessage is the one SELECT every read uses: chat and sender names come
// back with any operator-given label already applied.
var selectMessage = `
        SELECT m.id, m.chat_jid, COALESCE(nc.name, m.chat_name),
               m.sender_jid, COALESCE(ns.name, m.sender_name), m.from_me,
               m.is_group, m.ts, m.body, m.media_type, m.media_name, m.media_path, m.media_size
        FROM messages m
        LEFT JOIN names nc ON nc.jid_user = ` + userOf("m.chat_jid") + `
        LEFT JOIN names ns ON ns.jid_user = ` + userOf("m.sender_jid")

// SetName labels every user id in users with the same name.
func (d *DB) SetName(users []string, name, phone string) error {
	tx, err := d.sql.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	now := time.Now().Unix()
	for _, u := range users {
		if u == "" {
			continue
		}
		if _, err := tx.Exec(`
            INSERT INTO names (jid_user, name, phone, set_at) VALUES (?, ?, ?, ?)
            ON CONFLICT(jid_user) DO UPDATE SET name = excluded.name,
                phone = CASE WHEN excluded.phone <> '' THEN excluded.phone ELSE names.phone END,
                set_at = excluded.set_at`, u, name, phone, now); err != nil {
			return err
		}
	}
	return tx.Commit()
}

// Names lists every label given, newest first.
func (d *DB) Names() ([]Name, error) {
	rows, err := d.sql.Query(`SELECT jid_user, name, phone, set_at FROM names ORDER BY set_at DESC, name`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Name
	for rows.Next() {
		var n Name
		var ts int64
		if err := rows.Scan(&n.User, &n.Name, &n.Phone, &ts); err != nil {
			return nil, err
		}
		n.SetAt = time.Unix(ts, 0)
		out = append(out, n)
	}
	return out, rows.Err()
}

func placeholders(n int) string {
	if n <= 0 {
		return "NULL"
	}
	return "?" + strings.Repeat(",?", n-1)
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
