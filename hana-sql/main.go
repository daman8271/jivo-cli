// hana-sql — a strictly READ-ONLY SQL client for the JIVO SAP HANA database.
//
// It connects to HANA (the SAP Business One core database) and runs SELECT
// queries only. Writes are refused before a statement is ever sent: a first-token
// allowlist (SELECT / WITH / EXPLAIN) plus a single-statement guard. This mirrors
// the read-only guarantee of the sibling `postsql` tool and honours CLAUDE.md
// Rule 0 (never mutate SAP).
//
// Credentials come from connections/hana.env (gitignored). The file is located by
// walking up from the working directory, or via the -env flag / HANA_ENV var.
//
// Usage:
//
//	hana-sql "SELECT CURRENT_USER, CURRENT_SCHEMA FROM DUMMY"
//	hana-sql -f queries/turnover-oil-july.sql
//	echo "SELECT ... FROM ..." | hana-sql
//
// Companies are HANA schemas: JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB.
package main

import (
	"bufio"
	"crypto/tls"
	"database/sql"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/SAP/go-hdb/driver"
)

func loadEnv(path string) (map[string]string, error) {
	m := map[string]string{}
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		kv := strings.SplitN(line, "=", 2)
		if len(kv) == 2 {
			m[strings.TrimSpace(kv[0])] = strings.TrimSpace(kv[1])
		}
	}
	return m, sc.Err()
}

// findEnv walks up from the current directory looking for connections/hana.env.
func findEnv() string {
	if v := os.Getenv("HANA_ENV"); v != "" {
		return v
	}
	dir, _ := os.Getwd()
	for {
		cand := filepath.Join(dir, "connections", "hana.env")
		if _, err := os.Stat(cand); err == nil {
			return cand
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "connections/hana.env" // last-resort relative
		}
		dir = parent
	}
}

var (
	lineComment  = regexp.MustCompile(`--[^\n]*`)
	blockComment = regexp.MustCompile(`(?s)/\*.*?\*/`)
)

// assertReadOnly refuses anything that is not a single SELECT / WITH / EXPLAIN.
func assertReadOnly(sqlText string) error {
	s := blockComment.ReplaceAllString(sqlText, " ")
	s = lineComment.ReplaceAllString(s, " ")
	s = strings.TrimSpace(s)
	s = strings.TrimRight(s, ";")
	if strings.Contains(s, ";") {
		return fmt.Errorf("multiple statements are not allowed (found ';') — run one SELECT at a time")
	}
	fields := strings.Fields(s)
	if len(fields) == 0 {
		return fmt.Errorf("empty query")
	}
	switch strings.ToUpper(fields[0]) {
	case "SELECT", "WITH", "EXPLAIN":
		return nil
	default:
		return fmt.Errorf("only SELECT / WITH / EXPLAIN are allowed (read-only); got %q", fields[0])
	}
}

func connect(env map[string]string) (*sql.DB, string, error) {
	host := env["HANA_HOST"] + ":" + env["HANA_PORT"]
	for _, useTLS := range []bool{false, true} {
		c := driver.NewBasicAuthConnector(host, env["HANA_USER"], env["HANA_PASSWORD"])
		c.SetTimeout(90 * time.Second)
		if useTLS {
			c.SetTLSConfig(&tls.Config{InsecureSkipVerify: true})
		}
		db := sql.OpenDB(c)
		var one int
		if err := db.QueryRow("SELECT 1 FROM DUMMY").Scan(&one); err == nil {
			mode := "plaintext"
			if useTLS {
				mode = "TLS"
			}
			return db, mode, nil
		}
		db.Close()
	}
	return nil, "", fmt.Errorf("could not connect to HANA at %s (tried plaintext and TLS)", host)
}

func cell(v interface{}) string {
	if v == nil {
		return "NULL"
	}
	if b, ok := v.([]byte); ok {
		return string(b)
	}
	return fmt.Sprintf("%v", v)
}

func main() {
	envPath := flag.String("env", "", "path to hana.env (default: search up for connections/hana.env, or $HANA_ENV)")
	file := flag.String("f", "", "read SQL from this file instead of the argument/stdin")
	csv := flag.Bool("csv", false, "emit comma-separated output instead of tab-separated")
	flag.Parse()

	// Resolve SQL text: -f file, else first positional arg, else stdin.
	var sqlText string
	switch {
	case *file != "":
		b, err := os.ReadFile(*file)
		if err != nil {
			fmt.Fprintln(os.Stderr, "read sql file:", err)
			os.Exit(1)
		}
		sqlText = string(b)
	case flag.NArg() > 0:
		sqlText = flag.Arg(0)
	default:
		b, _ := io.ReadAll(os.Stdin)
		sqlText = string(b)
	}
	if strings.TrimSpace(sqlText) == "" {
		fmt.Fprintln(os.Stderr, "no SQL provided (pass a query as an argument, -f file, or on stdin)")
		os.Exit(1)
	}

	if err := assertReadOnly(sqlText); err != nil {
		fmt.Fprintln(os.Stderr, "REFUSED:", err)
		os.Exit(1)
	}

	ep := *envPath
	if ep == "" {
		ep = findEnv()
	}
	env, err := loadEnv(ep)
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot read credentials at %s: %v\n", ep, err)
		os.Exit(1)
	}

	db, _, err := connect(env)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	defer db.Close()

	rows, err := db.Query(sqlText)
	if err != nil {
		fmt.Fprintln(os.Stderr, "QUERY ERROR:", err)
		os.Exit(3)
	}
	defer rows.Close()

	cols, _ := rows.Columns()
	sep := "\t"
	if *csv {
		sep = ","
	}
	fmt.Println(strings.Join(cols, sep))

	vals := make([]interface{}, len(cols))
	ptrs := make([]interface{}, len(cols))
	for i := range vals {
		ptrs[i] = &vals[i]
	}
	for rows.Next() {
		if err := rows.Scan(ptrs...); err != nil {
			fmt.Fprintln(os.Stderr, "scan:", err)
			os.Exit(3)
		}
		out := make([]string, len(cols))
		for i := range vals {
			out[i] = cell(vals[i])
		}
		fmt.Println(strings.Join(out, sep))
	}
	if err := rows.Err(); err != nil {
		fmt.Fprintln(os.Stderr, "rows err:", err)
		os.Exit(3)
	}
}
