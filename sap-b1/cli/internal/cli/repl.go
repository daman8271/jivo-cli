package cli

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"os"
	"sort"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

// The REPL exists because an Accounts question is almost never one command. It
// is "that party's balance, now their open invoices, now last month's credit
// notes" — the same company, the same output format, twenty times over. Retyping
// --company JIVO_MART_HANADB on every line is where typos (and wrong-company
// answers) come from.
//
// So the session holds the flags, and every line inherits them. `:undo` steps
// that session state back — it does NOT undo anything in SAP, and cannot: a
// posted document is SAP's to reverse, and even a draft this CLI created is
// removed with `delete draft`, deliberately, with a typed confirmation.
//
// Writes are refused inside the REPL. Not on permission grounds — RULE 0
// authorises them — but because `draft`/`post`/`patch`/`delete` read a typed
// `yes` from stdin, and stdin here already belongs to the REPL's own reader. Two
// readers on one pipe is how a confirmation gets answered by the wrong line. The
// REPL prints the exact command to paste into a plain terminal instead.

// replState is everything a line inherits. Copied by value on every change,
// which is what makes undo/redo a two-line operation.
type replState struct {
	company string
	json    bool
	csv     bool
	top     int
}

// flags renders the state as the argv every dispatched line is prefixed with.
func (s replState) flags() []string {
	var out []string
	if s.company != "" {
		out = append(out, "--company", s.company)
	}
	if s.json {
		out = append(out, "--json")
	}
	if s.csv {
		out = append(out, "--csv")
	}
	return out
}

func (s replState) String() string {
	company := s.company
	if company == "" {
		company = "(default — whatever .env says)"
	}
	format := "table"
	switch {
	case s.json:
		format = "json"
	case s.csv:
		format = "csv"
	}
	top := "(command default)"
	if s.top > 0 {
		top = strconv.Itoa(s.top)
	}
	return fmt.Sprintf("company %s\nformat  %s\ntop     %s", company, format, top)
}

// companyAliases lets an operator type what they say out loud.
var companyAliases = map[string]string{
	"oil":       "JIVO_OIL_HANADB",
	"mart":      "JIVO_MART_HANADB",
	"bev":       "JIVO_BEVERAGES_HANADB",
	"beverages": "JIVO_BEVERAGES_HANADB",
	"beverage":  "JIVO_BEVERAGES_HANADB",
}

func resolveCompany(in string) string {
	if db, ok := companyAliases[strings.ToLower(strings.TrimSpace(in))]; ok {
		return db
	}
	return in
}

// writeVerbs are the commands that ask for a typed confirmation on stdin.
var writeVerbs = map[string]bool{
	"draft": true, "post": true, "patch": true, "delete": true, "add-draft": true,
}

// splitLine is a small shell-ish splitter: single and double quotes hold a token
// together, backslash escapes the next rune. An OData filter is full of spaces
// and quotes, so a naive strings.Fields would shred it.
func splitLine(line string) []string {
	var (
		out   []string
		cur   strings.Builder
		quote rune
		esc   bool
		open  bool
	)
	flush := func() {
		if open {
			out = append(out, cur.String())
			cur.Reset()
			open = false
		}
	}
	for _, r := range line {
		switch {
		case esc:
			cur.WriteRune(r)
			open = true
			esc = false
		case r == '\\':
			esc = true
			open = true
		case quote != 0:
			if r == quote {
				quote = 0
			} else {
				cur.WriteRune(r)
			}
			open = true
		case r == '\'' || r == '"':
			quote = r
			open = true
		case r == ' ' || r == '\t':
			flush()
		default:
			cur.WriteRune(r)
			open = true
		}
	}
	flush()
	return out
}

type replSession struct {
	state   replState
	undo    []replState
	redo    []replState
	history []string
	out     io.Writer
}

// apply records the current state on the undo stack, then mutates. Any change
// invalidates the redo stack — the usual editor contract.
func (s *replSession) apply(fn func(*replState)) {
	s.undo = append(s.undo, s.state)
	s.redo = nil
	fn(&s.state)
}

func (s *replSession) doUndo() error {
	if len(s.undo) == 0 {
		return fmt.Errorf("nothing to undo — the session is at its starting state")
	}
	s.redo = append(s.redo, s.state)
	s.state = s.undo[len(s.undo)-1]
	s.undo = s.undo[:len(s.undo)-1]
	return nil
}

func (s *replSession) doRedo() error {
	if len(s.redo) == 0 {
		return fmt.Errorf("nothing to redo")
	}
	s.undo = append(s.undo, s.state)
	s.state = s.redo[len(s.redo)-1]
	s.redo = s.redo[:len(s.redo)-1]
	return nil
}

const replHelp = `Session commands (all start with ':'). Anything else is a normal sapb1 command,
run with the session's flags already applied.

  :set company oil|mart|bev|<DB>   which company book every line reads
  :set json on|off                 raw OData JSON instead of a table
  :set csv on|off                  CSV instead of a table
  :set top <n>                     default row limit for query/list commands
  :state                           what the session is currently holding
  :undo / :redo                    step the session settings back / forward
  :history                         the lines run this session
  :help                            this
  :exit                            leave (Ctrl-D does the same)

Examples

  :set company mart
  query BusinessPartners --filter "CardCode eq 'VENDA001548'" --select "CardName,CurrentAccountBalance"
  :set json on
  query Invoices --count --filter "DocDate ge '2026-08-01' and Cancelled eq 'tNO'"

:undo moves the SESSION back, never SAP. Nothing typed here changes a document.`

// handleMeta runs a ':' command. Returns done=true when the session should end.
func (s *replSession) handleMeta(words []string) (done bool) {
	switch words[0] {
	case ":exit", ":quit", ":q":
		return true
	case ":help", ":h", ":?":
		fmt.Fprintln(s.out, replHelp)
	case ":state":
		fmt.Fprintln(s.out, s.state.String())
	case ":undo":
		if err := s.doUndo(); err != nil {
			fmt.Fprintf(s.out, "%v\n", err)
			break
		}
		fmt.Fprintf(s.out, "undone — session is now:\n%s\n", s.state.String())
	case ":redo":
		if err := s.doRedo(); err != nil {
			fmt.Fprintf(s.out, "%v\n", err)
			break
		}
		fmt.Fprintf(s.out, "redone — session is now:\n%s\n", s.state.String())
	case ":history":
		if len(s.history) == 0 {
			fmt.Fprintln(s.out, "(nothing run yet)")
			break
		}
		for i, h := range s.history {
			fmt.Fprintf(s.out, "%3d  %s\n", i+1, h)
		}
	case ":set":
		s.handleSet(words[1:])
	default:
		fmt.Fprintf(s.out, "unknown session command %q — :help lists them\n", words[0])
	}
	return false
}

func onOff(v string) (bool, error) {
	switch strings.ToLower(v) {
	case "on", "true", "yes", "1":
		return true, nil
	case "off", "false", "no", "0":
		return false, nil
	}
	return false, fmt.Errorf("expected on or off, got %q", v)
}

func (s *replSession) handleSet(args []string) {
	if len(args) < 2 {
		fmt.Fprintln(s.out, "usage: :set <company|json|csv|top> <value>")
		return
	}
	key, val := strings.ToLower(args[0]), args[1]
	switch key {
	case "company":
		db := resolveCompany(val)
		s.apply(func(st *replState) { st.company = db })
		fmt.Fprintf(s.out, "company = %s\n", db)
	case "json":
		on, err := onOff(val)
		if err != nil {
			fmt.Fprintf(s.out, "%v\n", err)
			return
		}
		s.apply(func(st *replState) {
			st.json = on
			if on {
				st.csv = false // the root command rejects both at once
			}
		})
		fmt.Fprintf(s.out, "json = %v\n", on)
	case "csv":
		on, err := onOff(val)
		if err != nil {
			fmt.Fprintf(s.out, "%v\n", err)
			return
		}
		s.apply(func(st *replState) {
			st.csv = on
			if on {
				st.json = false
			}
		})
		fmt.Fprintf(s.out, "csv = %v\n", on)
	case "top":
		n, err := strconv.Atoi(val)
		if err != nil || n < 0 {
			fmt.Fprintf(s.out, "top needs a non-negative number, got %q\n", val)
			return
		}
		s.apply(func(st *replState) { st.top = n })
		fmt.Fprintf(s.out, "top = %d\n", n)
	default:
		fmt.Fprintf(s.out, "cannot set %q. One of: company, json, csv, top\n", key)
	}
}

// dispatch runs one non-meta line as a normal sapb1 invocation.
func (s *replSession) dispatch(ctx context.Context, words []string) {
	if writeVerbs[words[0]] {
		full := append([]string{"sapb1"}, s.state.flags()...)
		full = append(full, words...)
		fmt.Fprintf(s.out, `%s is a write, and the REPL cannot run it.

Not a permission limit — writes are authorised. It is that the confirmation
prompt reads a typed "yes" from stdin, and stdin here belongs to the REPL. Run
it in a plain terminal so the prompt is unambiguous:

  %s

`, words[0], strings.Join(full, " "))
		return
	}

	args := append(s.state.flags(), words...)
	if s.state.top > 0 && !hasFlag(words, "--top") && acceptsTop(words[0]) {
		args = append(args, "--top", strconv.Itoa(s.state.top))
	}

	root := NewRootCmd()
	root.SetArgs(args)
	root.SetOut(s.out)
	root.SetErr(s.out)
	root.SilenceUsage = true
	root.SilenceErrors = true
	if err := root.ExecuteContext(ctx); err != nil {
		fmt.Fprintf(s.out, "Error: %v\n", err)
	}
}

func hasFlag(words []string, flag string) bool {
	for _, w := range words {
		if w == flag || strings.HasPrefix(w, flag+"=") {
			return true
		}
	}
	return false
}

// acceptsTop lists the read commands that take --top, so `:set top` does not
// inject a flag into a command that would reject it.
func acceptsTop(verb string) bool {
	switch verb {
	case "query", "orders", "invoices", "items", "partners":
		return true
	}
	return false
}

func newREPLCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "repl",
		Short: "Interactive session — set the company once, then just ask",
		Long: `repl opens an interactive sapb1 session.

The session remembers the flags, so you set the company (and the output format)
once and every following line inherits them. That is the whole point: an Accounts
question is rarely one command, and --company retyped twenty times is how a Mart
figure ends up presented as an Oil one.

  sapb1 repl
  sapb1> :set company mart
  sapb1> partners --filter "CardCode eq 'VENDA001235'"
  sapb1> :set json on
  sapb1> query Invoices --count --filter "Cancelled eq 'tNO'"
  sapb1> :undo          # back to table output
  sapb1> :exit

:undo and :redo move the SESSION's settings, not SAP. Nothing typed in the REPL
can change a document: the write commands (draft, post, patch, delete, add-draft)
are refused here because their typed-"yes" confirmation would have to share stdin
with the REPL's own reader. The REPL prints the command to run in a plain
terminal instead.`,
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			return runREPL(cmd.Context(), os.Stdin, cmd.OutOrStdout())
		},
	}
	return cmd
}

func runREPL(ctx context.Context, in io.Reader, out io.Writer) error {
	sess := &replSession{out: out}

	// Inherit the company the operator already passed on the command line, so
	// `sapb1 --company JIVO_MART_HANADB repl` starts where they expect.
	if flagCompany != "" {
		sess.state.company = flagCompany
	}
	if flagJSON {
		sess.state.json = true
	}
	if flagCSV {
		sess.state.csv = true
	}

	fmt.Fprintln(out, "sapb1 interactive session. :help for session commands, :exit to leave.")
	fmt.Fprintln(out, "Reads only — write commands are refused here and printed for a plain terminal.")
	fmt.Fprintln(out, sess.state.String())
	fmt.Fprintln(out)

	sc := bufio.NewScanner(in)
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024) // OData filters get long
	for {
		fmt.Fprint(out, "sapb1> ")
		if !sc.Scan() {
			break
		}
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		words := splitLine(line)
		if len(words) == 0 {
			continue
		}
		sess.history = append(sess.history, line)
		if strings.HasPrefix(words[0], ":") {
			if sess.handleMeta(words) {
				break
			}
			continue
		}
		sess.dispatch(ctx, words)
	}
	if err := sc.Err(); err != nil {
		return err
	}
	fmt.Fprintln(out, "bye")
	return nil
}

// replCommandNames is used by the help text and by tests to keep the meta-command
// list and the documentation from drifting apart.
func replCommandNames() []string {
	names := []string{":set", ":state", ":undo", ":redo", ":history", ":help", ":exit"}
	sort.Strings(names)
	return names
}
