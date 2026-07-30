// hana-sql — a strictly READ-ONLY SQL client for the JIVO SAP HANA database.
//
// It connects to HANA (the SAP Business One core database) and runs read
// queries only. Writes are refused before a statement is ever sent, by a
// layered guard (internal/guard) plus HANA's own READ ONLY transaction access
// mode (internal/hana). This mirrors the read-only guarantee of the sibling
// `postsql` tool and honours CLAUDE.md Rule 0 (never mutate SAP).
//
// Credentials come from connections/hana.env (gitignored). The file is located
// by walking up from the working directory, or via the -env flag / HANA_ENV var;
// HANA_HOST / HANA_PORT / HANA_USER / HANA_PASSWORD in the process environment
// override it, which is how the container is configured.
//
// Usage:
//
//	hana-sql "SELECT CURRENT_USER, CURRENT_SCHEMA FROM DUMMY"
//	hana-sql -f queries/turnover-oil-july.sql
//	echo "SELECT ... FROM ..." | hana-sql
//	hana-sql mcp                          # MCP server on stdio
//	hana-sql mcp --transport http --addr 127.0.0.1:7706
//
// Companies are HANA schemas: JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB.
package main

import (
	"bufio"
	"context"
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"hana-sql/internal/config"
	"hana-sql/internal/guard"
	"hana-sql/internal/hana"
	"hana-sql/internal/mcpsrv"
)

// io bundles the process streams so both subcommands are testable in-process.
type ioStreams struct {
	in       io.Reader
	out, err io.Writer
}

func stdio() ioStreams { return ioStreams{in: os.Stdin, out: os.Stdout, err: os.Stderr} }

// run is main without os.Exit, so the tests can drive it.
func run(argv []string, s ioStreams) int {
	// The `mcp` subcommand must be detected before flag.Parse: the stdlib flag
	// package stops at the first positional argument, so a subcommand needs its
	// own FlagSet over argv[1:].
	if len(argv) > 0 && argv[0] == "mcp" {
		return mcpMain(argv[1:], s)
	}
	return queryMain(argv, s)
}

func main() { os.Exit(run(os.Args[1:], stdio())) }

// --- the human CLI --------------------------------------------------------

func queryMain(argv []string, s ioStreams) int {
	fs := flag.NewFlagSet("hana-sql", flag.ContinueOnError)
	fs.SetOutput(s.err)
	envPath := fs.String("env", "", "path to hana.env (default: search up for connections/hana.env, or $HANA_ENV)")
	file := fs.String("f", "", "read SQL from this file instead of the argument/stdin")
	csvOut := fs.Bool("csv", false, "emit RFC 4180 CSV instead of tab-separated output")
	fs.Usage = func() {
		fmt.Fprint(s.err, cliUsage)
		fs.PrintDefaults()
	}
	if err := fs.Parse(argv); err != nil {
		return 2
	}

	// Resolve SQL text: -f file, else first positional arg, else stdin.
	var sqlText string
	switch {
	case *file != "":
		b, err := os.ReadFile(*file)
		if err != nil {
			fmt.Fprintln(s.err, "read sql file:", err)
			return 1
		}
		sqlText = string(b)
	case fs.NArg() > 0:
		sqlText = fs.Arg(0)
	default:
		b, _ := io.ReadAll(s.in)
		sqlText = string(b)
	}
	if strings.TrimSpace(sqlText) == "" {
		fmt.Fprintln(s.err, "no SQL provided (pass a query as an argument, -f file, or on stdin)")
		return 1
	}

	// Layers 0-3, before any credential is even read.
	if err := guard.Check(sqlText, guard.CLIPolicy); err != nil {
		fmt.Fprintln(s.err, err)
		return 1
	}

	cfg, err := config.Load(config.Find(*envPath))
	if err != nil {
		fmt.Fprintln(s.err, err)
		return 1
	}

	// The CLI is a human at a terminal: no row cap, no byte cap, no statement
	// deadline — and NO LOB cap either. A negative LobLimit is how internal/hana
	// is told "no limit"; leaving it zero meant the default 8 KiB applied, so
	// `hana-sql "SELECT DEFINITION FROM SYS.VIEWS …"` handed a person 8205 bytes
	// ending in " …[clipped]" where the old CLI printed the whole definition.
	// Layers 0-4 still apply.
	db := hana.New(cfg, hana.Options{
		MaxConcurrent: 1,
		LobLimit:      -1,
		AppName:       "hana-sql-cli",
	})
	defer db.Close()

	ctx := context.Background()

	// Dial explicitly so a connection failure keeps its own exit code (2),
	// distinct from a query error (3), exactly as before.
	if _, _, err := db.Pool(ctx); err != nil {
		fmt.Fprintln(s.err, err)
		return 2
	}

	w := bufio.NewWriter(s.out)
	defer w.Flush()
	sink := newRowSink(w, *csvOut)

	var order []string
	err = db.StreamReadOnly(ctx, guard.CLIPolicy, hana.Limits{}, sqlText, nil,
		func(cols []hana.Column) error {
			order = make([]string, len(cols))
			for i, c := range cols {
				order[i] = c.Name
			}
			return sink.write(order)
		},
		func(row map[string]any) error {
			cells := make([]string, len(order))
			for i, name := range order {
				cells[i] = hana.CellText(row[name])
			}
			return sink.write(cells)
		})
	if ferr := sink.flush(); err == nil {
		err = ferr
	}
	if err != nil {
		w.Flush()
		fmt.Fprintln(s.err, "QUERY ERROR:", err)
		return 3
	}
	return 0
}

// --- delimited output -----------------------------------------------------

// A row of live SAP data routinely contains the delimiter. Measured on Oil
// alone: 67 of 3391 OCRD."Address" values, 37 OINV."Comments" and 4
// OITM."ItemName" contain a comma, and one OCRD."CardName" does
// ("V TRANS, V XPRESS & V LOGIS"). The old output was `strings.Join(cells, sep)`
// with no quoting at all, so that single partner turned a three-column SELECT
// into a four-field line and dropped the balance under the wrong header in
// Excel — a silently wrong number, which is the one thing this tool exists not
// to produce. An embedded newline was worse: one database row became two output
// lines.
//
// So each format now escapes, by its own convention:
//
//	-csv   RFC 4180 via encoding/csv — a field containing , " CR or LF is
//	       double-quoted and its quotes doubled.
//	(TSV)  the PostgreSQL COPY TEXT convention — \\ \t \n \r. Backslash rather
//	       than quoting because TSV's readers are `cut -f` and `awk -F'\t'`,
//	       which do not understand quotes; this keeps every row exactly one line
//	       and every field free of the delimiter, so those tools stay correct.
type rowSink interface {
	write(cells []string) error
	flush() error
}

func newRowSink(w io.Writer, asCSV bool) rowSink {
	if asCSV {
		return &csvSink{w: csv.NewWriter(w)}
	}
	return &tsvSink{w: w}
}

type csvSink struct{ w *csv.Writer }

func (s *csvSink) write(cells []string) error { return s.w.Write(cells) }
func (s *csvSink) flush() error               { s.w.Flush(); return s.w.Error() }

type tsvSink struct{ w io.Writer }

func (s *tsvSink) write(cells []string) error {
	esc := make([]string, len(cells))
	for i, c := range cells {
		esc[i] = tsvEscape(c)
	}
	_, err := fmt.Fprintln(s.w, strings.Join(esc, "\t"))
	return err
}

func (s *tsvSink) flush() error { return nil }

// tsvEscape makes one cell safe to place between tabs on a single line.
func tsvEscape(s string) string {
	if !strings.ContainsAny(s, "\\\t\n\r") {
		return s
	}
	var b strings.Builder
	b.Grow(len(s) + 8)
	for _, r := range s {
		switch r {
		case '\\':
			b.WriteString(`\\`)
		case '\t':
			b.WriteString(`\t`)
		case '\n':
			b.WriteString(`\n`)
		case '\r':
			b.WriteString(`\r`)
		default:
			b.WriteRune(r)
		}
	}
	return b.String()
}

const cliUsage = `hana-sql — read-only SQL against JIVO's SAP HANA database.

  hana-sql "SELECT CURRENT_USER FROM DUMMY"
  hana-sql -f queries/turnover-oil-july.sql
  echo "SELECT ..." | hana-sql
  hana-sql mcp [--transport stdio|http] [--addr 127.0.0.1:7706]

Flags:
`

// --- the MCP subcommand ---------------------------------------------------

func mcpMain(argv []string, s ioStreams) int {
	fs := flag.NewFlagSet("hana-sql mcp", flag.ContinueOnError)
	fs.SetOutput(s.err)
	envPath := fs.String("env", "", "path to hana.env (default: search up for connections/hana.env, or $HANA_ENV)")
	transport := fs.String("transport", "stdio", "stdio | http")
	addr := fs.String("addr", "127.0.0.1:7706", "listen address for --transport http")
	maxRows := fs.Int("max-rows", hana.DefaultMaxRows, "hard row cap per query")
	maxBytes := fs.Int("max-bytes", hana.DefaultMaxBytes, "approximate response payload cap, in bytes")
	timeout := fs.Duration("timeout", hana.DefaultTimeout, "per-statement deadline (a real server-side cancel)")
	maxConc := fs.Int("max-concurrent", hana.DefaultMaxConcurrent, "in-flight query cap, so a model cannot stampede production")
	quiet := fs.Bool("quiet", false, "suppress the per-query audit line on stderr")
	allowOrigin := fs.String("allow-origin", "", "comma-separated browser origins the HTTP transport accepts (default: none — any request carrying an Origin header is refused)")
	allowHost := fs.String("allow-host", "", "comma-separated extra Host header values the HTTP transport accepts (default: loopback only, which is the DNS-rebinding defence)")
	authToken := fs.String("auth-token", "", "require `Authorization: Bearer <token>` on the HTTP transport (or set HANA_MCP_TOKEN)")
	fs.Usage = func() {
		fmt.Fprint(s.err, "hana-sql mcp — serve read-only HANA to MCP clients.\n\nFlags:\n")
		fs.PrintDefaults()
	}
	if err := fs.Parse(argv); err != nil {
		return 2
	}

	cfg, err := config.Load(config.Find(*envPath))
	if err != nil {
		// Do not die: a container whose tunnel is down must still start and
		// report the problem through hana_doctor rather than crash-loop.
		fmt.Fprintln(s.err, "hana-sql: WARNING:", err)
		cfg = &config.Config{Port: config.DefaultPort}
	}

	var auditLog io.Writer = s.err
	if *quiet {
		auditLog = io.Discard
	}
	db := hana.New(cfg, hana.Options{
		Limits: hana.Limits{
			MaxRows:  *maxRows,
			MaxBytes: *maxBytes,
			Timeout:  *timeout,
		},
		MaxConcurrent: *maxConc,
		AppName:       "jivo-hana-mcp",
		Log:           auditLog,
	})
	defer db.Close()

	srv := mcpsrv.New(db)
	srv.Log = s.err // transport logs must never touch stdout: that is the protocol stream
	srv.AllowedOrigins = splitList(*allowOrigin)
	srv.AllowedHosts = splitList(*allowHost)
	srv.AuthToken = *authToken
	if srv.AuthToken == "" {
		srv.AuthToken = os.Getenv("HANA_MCP_TOKEN")
	}

	switch *transport {
	case "stdio":
		if err := srv.ServeStdio(s.in, s.out); err != nil {
			fmt.Fprintln(s.err, "hana-sql mcp:", err)
			return 1
		}
		return 0
	case "http":
		go func() {
			sig := make(chan os.Signal, 1)
			signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
			<-sig
			db.Close()
			os.Exit(0)
		}()
		if err := srv.ServeHTTP(*addr); err != nil {
			fmt.Fprintln(s.err, "hana-sql mcp:", err)
			return 1
		}
		return 0
	default:
		fmt.Fprintf(s.err, "unknown --transport %q (want stdio or http)\n", *transport)
		return 1
	}
}

// splitList parses a comma-separated flag value into a trimmed, non-empty list.
func splitList(v string) []string {
	var out []string
	for _, part := range strings.Split(v, ",") {
		if p := strings.TrimSpace(part); p != "" {
			out = append(out, p)
		}
	}
	return out
}
