// Command jwa links a WhatsApp number as a companion device, archives what
// arrives, and lets Accounts pull a vendor's bill out without scrolling a phone.
//
// It never sends. The reading commands (doctor, chats, search, bills, pull) do
// not construct a WhatsApp client at all — they open the local archive and
// nothing else, so there is no wire for them to put anything on. Only `login`
// and `run` connect. See internal/wa for the guard that enforces it.
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"text/tabwriter"
	"time"

	"github.com/mdp/qrterminal/v3"

	"jwa/internal/store"
	"jwa/internal/wa"
)

const usage = `jwa — JIVO's WhatsApp reader. Reads only; it can never send.

  jwa login                     link the number (QR, once, needs a human)
  jwa run                       stay linked and archive          (the daemon)
  jwa doctor                    linked? how much is archived?
  jwa chats  [--limit N]        conversations, most recent first
  jwa search [--chat X] [--from X] [--text X] [--since 30d] [--media] [--limit N]
  jwa bills  [--since 30d] [--chat X] [--limit N]
  jwa pull   <message-id> [--to DIR]
  jwa name   <number|jid> <label>  remember who a number is (chats/search show the label)
  jwa names  [--vcf FILE]          every label given; --vcf writes a card file to import on a phone

Everything lives under ~/.jwa — session.db (device keys), archive.db (messages),
media/YYYY-MM-DD/ (the files). Override the lot with JWA_HOME.
`

func main() {
	if len(os.Args) < 2 {
		fmt.Print(usage)
		os.Exit(2)
	}
	cmd, args := os.Args[1], os.Args[2:]

	var err error
	switch cmd {
	case "login":
		err = cmdLogin(args)
	case "run":
		err = cmdRun(args)
	case "doctor":
		err = cmdDoctor(args)
	case "chats":
		err = cmdChats(args)
	case "search":
		err = cmdSearch(args, false)
	case "bills":
		err = cmdSearch(args, true)
	case "pull":
		err = cmdPull(args)
	case "name":
		err = cmdName(args)
	case "names":
		err = cmdNames(args)
	case "help", "-h", "--help":
		fmt.Print(usage)
		return
	default:
		fmt.Fprintf(os.Stderr, "jwa: no such command %q\n\n%s", cmd, usage)
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "jwa %s: %v\n", cmd, err)
		os.Exit(1)
	}
}

// ---------------------------------------------------------------- paths

func home() string {
	if h := os.Getenv("JWA_HOME"); h != "" {
		return h
	}
	u, err := os.UserHomeDir()
	if err != nil {
		return ".jwa"
	}
	return filepath.Join(u, ".jwa")
}

func paths() (session, archive, media string) {
	h := home()
	return filepath.Join(h, "session.db"), filepath.Join(h, "archive.db"), filepath.Join(h, "media")
}

// openArchive is the whole of what a reading command is allowed to touch.
func openArchive() (*store.DB, error) {
	_, archive, _ := paths()
	if _, err := os.Stat(archive); errors.Is(err, os.ErrNotExist) {
		return nil, fmt.Errorf("no archive at %s yet — run `jwa login`, then `jwa run`", archive)
	}
	return store.Open(archive)
}

// ---------------------------------------------------------------- login / run

func cmdLogin(args []string) error {
	fs := flag.NewFlagSet("login", flag.ExitOnError)
	verbose := fs.Bool("v", false, "log whatsmeow's own chatter")
	_ = fs.Parse(args)

	session, archive, media := paths()
	c, err := wa.Open(session, archive, media, *verbose)
	if err != nil {
		return err
	}
	defer c.Close()

	if c.LoggedIn() {
		fmt.Printf("Already linked as %s.\n", c.WA.Store.ID.String())
		fmt.Println("To link a different number, delete", session, "and run this again.")
		return nil
	}

	fmt.Println("On the phone: WhatsApp → Settings → Linked devices → Link a device.")
	fmt.Println("Scan this. It refreshes every 20 seconds or so; the last one printed is the live one.")

	// Ctrl-C has to reach the QR loop, or a wrong-number scan means killing the
	// terminal window.
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	if err := c.Pair(ctx, func(code string) {
		fmt.Println()
		qrterminal.GenerateHalfBlock(code, qrterminal.L, os.Stdout)
	}); err != nil {
		return err
	}

	// Belt and braces on top of Pair's own check: never claim a link without
	// the device id that proves it.
	id := c.WA.Store.ID
	if id == nil {
		return errors.New("WhatsApp reported success but no device id was stored — nothing is linked; run `jwa login` again")
	}
	c.Note("linked", "QR scanned; the daemon has not started yet")
	fmt.Printf("\nLinked as %s.\n", id.String())
	fmt.Println("Now start the daemon so it actually archives:  systemctl --user start jwa")
	return nil
}

func cmdRun(args []string) error {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	verbose := fs.Bool("v", false, "log whatsmeow's own chatter")
	_ = fs.Parse(args)

	session, archive, media := paths()
	c, err := wa.Open(session, archive, media, *verbose)
	if err != nil {
		return err
	}
	defer c.Close()

	if !c.LoggedIn() {
		// Keep a logged_out / banned verdict on disk rather than blurring it
		// into "unlinked" on every 15-second restart.
		if s := wa.ReadStatus(home()); !wa.IsFatalState(s.State) {
			c.Note("unlinked", "no device keys in session.db — a phone must scan a QR: jwa login")
		}
		return fmt.Errorf("this box is not linked to a number yet — run `jwa login` with a phone in hand")
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	c.Note("starting", "")
	if err := c.Pair(ctx, func(string) {}); err != nil {
		c.Note("disconnected", "connect: "+err.Error())
		return err
	}
	fmt.Printf("%s  linked as %s, archiving to %s\n",
		time.Now().Format("2006-01-02 15:04:05"), c.WA.Store.ID.String(), archive)
	go c.Heartbeat(ctx)

	select {
	case <-ctx.Done():
		c.Note("stopped", "asked to stop")
		return nil
	case f := <-c.Fatal:
		// ~/.jwa/state already says why. Exit non-zero so systemd restarts
		// us (15 s) and the health cron sees a daemon that is not connected —
		// but only after a ban or an outdated build has had its wait, so the
		// restart loop does not hammer WhatsApp.
		if f.Wait > 0 {
			fmt.Printf("%s  waiting %s before exiting\n",
				time.Now().Format("2006-01-02 15:04:05"), f.Wait.Round(time.Second))
			select {
			case <-ctx.Done():
			case <-time.After(f.Wait):
			}
		}
		return f.Err
	}
}

// ---------------------------------------------------------------- doctor

func cmdDoctor(args []string) error {
	fs := flag.NewFlagSet("doctor", flag.ExitOnError)
	_ = fs.Parse(args)

	session, archive, media := paths()
	w := tabwriter.NewWriter(os.Stdout, 0, 8, 2, ' ', 0)
	defer w.Flush()

	fmt.Fprintf(w, "home\t%s\n", home())

	// Linked or not, read straight off the device store. This opens the file;
	// it does not connect.
	c, err := wa.Open(session, archive, media, false)
	if err != nil {
		fmt.Fprintf(w, "session\tCANNOT READ — %v\n", err)
		return nil
	}
	defer c.Close()

	if c.LoggedIn() {
		fmt.Fprintf(w, "linked\tyes, as %s\n", c.WA.Store.ID.String())
	} else {
		fmt.Fprintf(w, "linked\tNO — run `jwa login`\n")
	}
	if st, err := os.Stat(session); err == nil {
		fmt.Fprintf(w, "session.db\t%s  (mode %s)\n", human(st.Size()), st.Mode().Perm())
	}

	// The daemon's own verdict — the files it writes, not a guess from the DB.
	if s := wa.ReadStatus(home()); s.State == "" {
		fmt.Fprintf(w, "daemon\tno state yet — `jwa run` has not started since this build\n")
	} else {
		line := s.State
		if wa.IsFatalState(s.State) {
			line = strings.ToUpper(s.State)
		}
		if !s.Since.IsZero() {
			line += " since " + s.Since.Format("2006-01-02 15:04")
		}
		if !s.Heartbeat.IsZero() {
			line += fmt.Sprintf(" (heartbeat %s ago)", ago(s.Heartbeat))
		}
		if s.Detail != "" {
			line += " — " + s.Detail
		}
		fmt.Fprintf(w, "daemon\t%s\n", line)
	}

	msgs, mediaN, chats, oldest, newest, err := c.DB.Counts()
	if err != nil {
		return err
	}
	fmt.Fprintf(w, "messages\t%d in %d chats, %d carrying a file\n", msgs, chats, mediaN)
	if msgs > 0 {
		fmt.Fprintf(w, "covers\t%s → %s\n",
			oldest.Format("2006-01-02 15:04"), newest.Format("2006-01-02 15:04"))
		fmt.Fprintf(w, "last seen\t%s ago\n", ago(newest))
	} else {
		fmt.Fprintf(w, "covers\tnothing yet — the archive fills only while `jwa run` is up\n")
	}

	files, bytes := dirSize(media)
	fmt.Fprintf(w, "media\t%d files, %s under %s\n", files, human(bytes), media)
	return nil
}

// ---------------------------------------------------------------- chats

func cmdChats(args []string) error {
	fs := flag.NewFlagSet("chats", flag.ExitOnError)
	limit := fs.Int("limit", 30, "how many conversations")
	_ = fs.Parse(args)

	db, err := openArchive()
	if err != nil {
		return err
	}
	defer db.Close()

	chats, err := db.Chats(*limit)
	if err != nil {
		return err
	}
	if len(chats) == 0 {
		fmt.Println("Nothing archived yet. The archive fills only while `jwa run` is up.")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 8, 2, ' ', 0)
	fmt.Fprintln(w, "LAST\tKIND\tMSGS\tFILES\tCHAT")
	for _, c := range chats {
		kind := "dm"
		if c.IsGroup {
			kind = "group"
		}
		fmt.Fprintf(w, "%s\t%s\t%d\t%d\t%s\n",
			c.LastSeen.Format("2006-01-02 15:04"), kind, c.Messages, c.Media, c.Name)
	}
	return w.Flush()
}

// ---------------------------------------------------------------- search / bills

// cmdSearch backs both `search` and `bills`. `bills` is the same query narrowed
// to the two things a vendor's bill ever arrives as — an image or a PDF — which
// is the only reason this tool exists.
func cmdSearch(args []string, billsOnly bool) error {
	name := "search"
	if billsOnly {
		name = "bills"
	}
	fs := flag.NewFlagSet(name, flag.ExitOnError)
	chat := fs.String("chat", "", "substring of the chat name or JID")
	from := fs.String("from", "", "substring of the sender name or JID")
	text := fs.String("text", "", "substring of the message body")
	since := fs.String("since", "", "30d, 12h, 2w, or 2026-08-01")
	onlyMedia := fs.Bool("media", false, "only messages carrying a file")
	limit := fs.Int("limit", 50, "how many messages")
	_ = fs.Parse(args)

	q := store.Query{Chat: *chat, Sender: *from, Text: *text, Limit: *limit}
	if billsOnly {
		q.OnlyMedia = true
		q.Kinds = []string{"image", "document"}
		if *since == "" {
			*since = "30d" // a bill older than a month is not what anyone means by "bills"
		}
	} else {
		q.OnlyMedia = *onlyMedia
	}
	if *since != "" {
		t, err := parseSince(*since)
		if err != nil {
			return err
		}
		q.Since = t
	}

	db, err := openArchive()
	if err != nil {
		return err
	}
	defer db.Close()

	msgs, err := db.Search(q)
	if err != nil {
		return err
	}
	if len(msgs) == 0 {
		fmt.Println("Nothing matched.")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 8, 2, ' ', 0)
	fmt.Fprintln(w, "WHEN\tCHAT\tFROM\tWHAT\tMESSAGE-ID")
	for _, m := range msgs {
		what := oneLine(m.Body)
		if m.MediaType != "" {
			label := m.MediaName
			if label == "" {
				label = m.MediaType
			}
			what = fmt.Sprintf("[%s %s]", m.MediaType, label)
			if m.Body != "" {
				what += " " + oneLine(m.Body)
			}
		}
		sender := m.SenderName
		if m.FromMe {
			sender = "(us)"
		} else if sender == "" {
			sender = shortJID(m.SenderJID)
		}
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\n",
			m.Timestamp.Format("2006-01-02 15:04"), trim(m.ChatName, 22),
			trim(sender, 18), trim(what, 60), m.ID)
	}
	if err := w.Flush(); err != nil {
		return err
	}
	fmt.Printf("\n%d message(s). Pull a file with:  jwa pull <message-id> --to .\n", len(msgs))
	return nil
}

// ---------------------------------------------------------------- pull

func cmdPull(args []string) error {
	// The README documents `jwa pull <message-id> --to DIR`, and that is the
	// order a person types. Go's flag package stops parsing at the first
	// positional, so lift the id out first and let flag see only the flags.
	id, rest := splitPositional(args)
	fs := flag.NewFlagSet("pull", flag.ExitOnError)
	to := fs.String("to", ".", "directory to copy the file into")
	_ = fs.Parse(rest)
	if id == "" || fs.NArg() > 0 {
		return errors.New("give exactly one message-id (the last column of `jwa search`)")
	}

	db, err := openArchive()
	if err != nil {
		return err
	}
	defer db.Close()

	m, err := db.Get(id)
	if err != nil {
		return err
	}
	if m.MediaPath == "" {
		return fmt.Errorf("message %s carries no file (it is %s)", id, describe(m))
	}
	src, err := os.Open(m.MediaPath)
	if err != nil {
		return fmt.Errorf("the archive says the file is at %s but it is not readable: %w", m.MediaPath, err)
	}
	defer src.Close()

	if err := os.MkdirAll(*to, 0o755); err != nil {
		return err
	}
	base := m.MediaName
	if base == "" {
		base = filepath.Base(m.MediaPath)
	}
	dst := filepath.Join(*to, filepath.Base(base))
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	n, err := io.Copy(out, src)
	if cerr := out.Close(); err == nil {
		err = cerr
	}
	if err != nil {
		return err
	}
	fmt.Printf("%s  (%s)\n", dst, human(n))
	fmt.Printf("from %s in %s, %s\n", nameOr(m.SenderName, shortJID(m.SenderJID)),
		m.ChatName, m.Timestamp.Format("2006-01-02 15:04"))
	return nil
}

// ---------------------------------------------------------------- small helpers

// splitPositional pulls the first bare argument out of a command line, leaving
// the flags — in any order — for flag.Parse. --to is the only flag here that
// takes a separate value, so it is the only one whose value must be skipped.
func splitPositional(args []string) (positional string, flags []string) {
	for i := 0; i < len(args); i++ {
		a := args[i]
		if strings.HasPrefix(a, "-") {
			flags = append(flags, a)
			// "--to DIR" — the next token belongs to this flag, not to us.
			// "--to=DIR" carries its own value and needs no lookahead.
			if !strings.Contains(a, "=") && isValueFlag(a) && i+1 < len(args) {
				i++
				flags = append(flags, args[i])
			}
			continue
		}
		if positional == "" {
			positional = a
			continue
		}
		flags = append(flags, a) // a second bare arg: let the caller reject it
	}
	return
}

func isValueFlag(a string) bool {
	switch strings.TrimLeft(a, "-") {
	case "to":
		return true
	}
	return false
}

// parseSince takes what a person would actually type.
func parseSince(s string) (time.Time, error) {
	s = strings.TrimSpace(strings.ToLower(s))
	if s == "" {
		return time.Time{}, nil
	}
	if t, err := time.ParseInLocation("2006-01-02", s, time.Local); err == nil {
		return t, nil
	}
	unit := s[len(s)-1]
	n, err := strconv.Atoi(s[:len(s)-1])
	if err != nil || n < 0 {
		return time.Time{}, fmt.Errorf("--since %q: use 30d, 12h, 2w, or 2026-08-01", s)
	}
	switch unit {
	case 'h':
		return time.Now().Add(-time.Duration(n) * time.Hour), nil
	case 'd':
		return time.Now().AddDate(0, 0, -n), nil
	case 'w':
		return time.Now().AddDate(0, 0, -7*n), nil
	case 'm':
		return time.Now().AddDate(0, -n, 0), nil
	}
	return time.Time{}, fmt.Errorf("--since %q: use 30d, 12h, 2w, or 2026-08-01", s)
}

func oneLine(s string) string {
	s = strings.ReplaceAll(s, "\n", " ")
	s = strings.ReplaceAll(s, "\t", " ")
	return strings.TrimSpace(s)
}

func trim(s string, n int) string {
	if len([]rune(s)) <= n {
		return s
	}
	return string([]rune(s)[:n-1]) + "…"
}

func shortJID(j string) string {
	if i := strings.IndexByte(j, '@'); i > 0 {
		return j[:i]
	}
	return j
}

func nameOr(a, b string) string {
	if a != "" {
		return a
	}
	return b
}

func describe(m store.Message) string {
	if m.Body != "" {
		return "text: " + trim(oneLine(m.Body), 60)
	}
	return "empty"
}

func human(n int64) string {
	switch {
	case n >= 1<<30:
		return fmt.Sprintf("%.1f GB", float64(n)/(1<<30))
	case n >= 1<<20:
		return fmt.Sprintf("%.1f MB", float64(n)/(1<<20))
	case n >= 1<<10:
		return fmt.Sprintf("%.1f KB", float64(n)/(1<<10))
	}
	return fmt.Sprintf("%d B", n)
}

func ago(t time.Time) string {
	d := time.Since(t)
	switch {
	case d < time.Minute:
		return "under a minute"
	case d < time.Hour:
		return fmt.Sprintf("%d min", int(d.Minutes()))
	case d < 48*time.Hour:
		return fmt.Sprintf("%d h", int(d.Hours()))
	}
	return fmt.Sprintf("%d days", int(d.Hours()/24))
}

func dirSize(dir string) (files int, bytes int64) {
	_ = filepath.Walk(dir, func(_ string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		files++
		bytes += info.Size()
		return nil
	})
	return
}

// jwa name <number|jid> <label…>
func cmdName(args []string) error {
	if len(args) < 2 {
		return errors.New("usage: jwa name <number|jid> <label>   e.g. jwa name +919876543210 \"Ramesh, Delhi Punjab\"")
	}
	who, label := args[0], strings.TrimSpace(strings.Join(args[1:], " "))
	if label == "" {
		return errors.New("the label is empty")
	}

	session, archive, media := paths()
	c, err := wa.Open(session, archive, media, false)
	if err != nil {
		return err
	}
	defer c.Close()

	users, phone, err := c.Identify(who)
	if err != nil {
		return err
	}
	if err := c.DB.SetName(users, label, phone); err != nil {
		return err
	}
	fmt.Printf("%s = %s", label, nameOr(phone, who))
	if len(users) > 1 {
		fmt.Printf("  (also LID %s)", users[len(users)-1])
	} else if phone != "" {
		fmt.Printf("  (no LID for it yet — that arrives with the first message)")
	}
	fmt.Println()
	return nil
}

// jwa names [--vcf FILE]
func cmdNames(args []string) error {
	fs := flag.NewFlagSet("names", flag.ExitOnError)
	vcf := fs.String("vcf", "", "write a vCard file of these names, to import on a phone")
	_ = fs.Parse(args)

	db, err := openArchive()
	if err != nil {
		return err
	}
	defer db.Close()
	names, err := db.Names()
	if err != nil {
		return err
	}
	if len(names) == 0 {
		fmt.Println("No names given yet:  jwa name <number> <label>")
		return nil
	}

	// One person, several ids: fold them by label.
	type person struct {
		name, phone string
		ids         []string
		at          time.Time
	}
	var people []*person
	byName := map[string]*person{}
	for _, n := range names {
		p := byName[n.Name]
		if p == nil {
			p = &person{name: n.Name, at: n.SetAt}
			byName[n.Name] = p
			people = append(people, p)
		}
		if n.Phone != "" {
			p.phone = n.Phone
		}
		p.ids = append(p.ids, n.User)
	}

	if *vcf != "" {
		var b strings.Builder
		for _, p := range people {
			if p.phone == "" {
				continue
			}
			fmt.Fprintf(&b, "BEGIN:VCARD\r\nVERSION:3.0\r\nFN:%s\r\nN:%s;;;;\r\nTEL;TYPE=CELL:%s\r\nEND:VCARD\r\n",
				p.name, p.name, p.phone)
		}
		if err := os.WriteFile(*vcf, []byte(b.String()), 0o644); err != nil {
			return err
		}
		fmt.Printf("wrote %s — open it on the phone and tap Add to save them all\n", *vcf)
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 8, 2, ' ', 0)
	fmt.Fprintln(w, "NAME\tPHONE\tIDS\tGIVEN")
	for _, p := range people {
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\n", p.name, nameOr(p.phone, "?"), strings.Join(p.ids, " "), p.at.Format("2006-01-02"))
	}
	return w.Flush()
}
