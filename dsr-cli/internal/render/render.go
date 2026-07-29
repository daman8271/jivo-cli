// Package render turns a db.Result into human tables, JSON, or CSV.
package render

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"text/tabwriter"
	"time"

	"dsr/internal/db"
)

// Options controls output formatting, driven by global CLI flags.
type Options struct {
	JSON    bool
	CSV     bool
	Compact bool
	Quiet   bool
	Select  string // comma-separated column allowlist
}

// Render writes res to w in the format selected by opts.
func Render(w io.Writer, res *db.Result, opts Options) error {
	cols, rows, err := project(res, opts.Select)
	if err != nil {
		return err
	}
	switch {
	case opts.JSON || opts.Compact:
		return renderJSON(w, cols, rows, opts.Compact)
	case opts.CSV:
		return renderCSV(w, cols, rows)
	default:
		return renderTable(w, cols, rows, opts.Quiet)
	}
}

// Maps converts a result into a slice of column->value maps (JSON-friendly).
func Maps(res *db.Result) []map[string]any {
	out := make([]map[string]any, 0, len(res.Rows))
	for _, r := range res.Rows {
		m := make(map[string]any, len(res.Columns))
		for i, c := range res.Columns {
			if i < len(r) {
				m[c] = norm(r[i])
			}
		}
		out = append(out, m)
	}
	return out
}

func renderJSON(w io.Writer, cols []string, rows [][]any, compact bool) error {
	out := make([]map[string]any, 0, len(rows))
	for _, r := range rows {
		m := make(map[string]any, len(cols))
		for i, c := range cols {
			if i < len(r) {
				m[c] = norm(r[i])
			}
		}
		out = append(out, m)
	}
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	if !compact {
		enc.SetIndent("", "  ")
	}
	return enc.Encode(out)
}

func renderCSV(w io.Writer, cols []string, rows [][]any) error {
	cw := csv.NewWriter(w)
	if err := cw.Write(cols); err != nil {
		return err
	}
	for _, r := range rows {
		rec := make([]string, len(cols))
		for i := range cols {
			if i < len(r) {
				rec[i] = str(r[i])
			}
		}
		if err := cw.Write(rec); err != nil {
			return err
		}
	}
	cw.Flush()
	return cw.Error()
}

func renderTable(w io.Writer, cols []string, rows [][]any, quiet bool) error {
	if len(cols) == 0 {
		if !quiet {
			fmt.Fprintln(w, "(no columns)")
		}
		return nil
	}
	tw := tabwriter.NewWriter(w, 0, 2, 2, ' ', 0)
	fmt.Fprintln(tw, strings.Join(cols, "\t"))
	seps := make([]string, len(cols))
	for i, c := range cols {
		seps[i] = strings.Repeat("-", len(c))
	}
	fmt.Fprintln(tw, strings.Join(seps, "\t"))
	for _, r := range rows {
		cells := make([]string, len(cols))
		for i := range cols {
			if i < len(r) {
				cells[i] = str(r[i])
			}
		}
		fmt.Fprintln(tw, strings.Join(cells, "\t"))
	}
	if err := tw.Flush(); err != nil {
		return err
	}
	if !quiet {
		fmt.Fprintf(w, "(%d row%s)\n", len(rows), plural(len(rows)))
	}
	return nil
}

// project narrows a result to the --select columns. Empty selector = all columns.
// A selector naming an absent column is an error (never silently dump more).
func project(res *db.Result, sel string) ([]string, [][]any, error) {
	if strings.TrimSpace(sel) == "" {
		return res.Columns, res.Rows, nil
	}
	var idx []int
	var cols []string
	var unknown []string
	for _, want := range strings.Split(sel, ",") {
		want = strings.TrimSpace(want)
		if want == "" {
			continue
		}
		found := false
		for i, c := range res.Columns {
			if c == want {
				idx = append(idx, i)
				cols = append(cols, c)
				found = true
				break
			}
		}
		if !found {
			unknown = append(unknown, want)
		}
	}
	if len(unknown) > 0 {
		return nil, nil, fmt.Errorf("--select: no such column%s %s (available: %s)",
			plural(len(unknown)), strings.Join(unknown, ", "), strings.Join(res.Columns, ", "))
	}
	if len(idx) == 0 {
		return res.Columns, res.Rows, nil
	}
	rows := make([][]any, len(res.Rows))
	for ri, r := range res.Rows {
		nr := make([]any, len(idx))
		for j, ci := range idx {
			if ci < len(r) {
				nr[j] = r[ci]
			}
		}
		rows[ri] = nr
	}
	return cols, rows, nil
}

// norm converts a driver value to a JSON-friendly representation.
func norm(v any) any {
	switch t := v.(type) {
	case nil:
		return nil
	case []byte:
		return string(t)
	case time.Time:
		return t.Format(time.RFC3339)
	default:
		return v
	}
}

// str converts a value to its display string.
func str(v any) string {
	switch t := norm(v).(type) {
	case nil:
		return ""
	case string:
		return t
	default:
		return fmt.Sprintf("%v", t)
	}
}

func plural(n int) string {
	if n == 1 {
		return ""
	}
	return "s"
}
