package cli

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"sort"
	"strings"
	"text/tabwriter"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

// renderResult prints a query result either as pretty JSON (the raw "value"
// array — good for jq / feeding an AI agent) or as an aligned text table.
//
// columns, if non-empty, fixes the table's column order (used when the
// caller applied a --select, or when a subcommand has sensible defaults).
// If empty, the table falls back to the union of all keys present in the
// rows, sorted alphabetically, so `sapb1 query <AnyEntitySet>` always
// produces something readable.
func renderResult(w io.Writer, res *client.QueryResult, asJSON bool, columns []string) error {
	if asJSON {
		return renderJSON(w, res.Value)
	}
	renderTable(w, res.Value, columns)
	if res.Capped {
		fmt.Fprintf(w, "\n(note: stopped after %d pages — more results may exist; narrow your --filter or raise the page cap logic if you truly need all of it)\n", client.MaxPages)
	}
	return nil
}

func renderJSON(w io.Writer, rows []map[string]interface{}) error {
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	if rows == nil {
		rows = []map[string]interface{}{}
	}
	return enc.Encode(rows)
}

func renderTable(w io.Writer, rows []map[string]interface{}, columns []string) {
	if len(rows) == 0 {
		fmt.Fprintln(w, "(no rows)")
		return
	}

	cols := columns
	if len(cols) == 0 {
		cols = unionKeys(rows)
	}

	tw := tabwriter.NewWriter(w, 0, 2, 2, ' ', 0)
	fmt.Fprintln(tw, strings.Join(cols, "\t"))
	for _, row := range rows {
		vals := make([]string, len(cols))
		for i, c := range cols {
			vals[i] = formatCell(row[c])
		}
		fmt.Fprintln(tw, strings.Join(vals, "\t"))
	}
	tw.Flush()
}

// renderCSV writes rows as CSV with a header row. columns, if non-empty, fixes
// the column set and order (used when the caller applied a --select); otherwise
// the union of keys across the rows is used, sorted alphabetically. Object/array
// cell values are JSON-encoded (via formatCell), and encoding/csv quotes any
// cell that needs it.
func renderCSV(w io.Writer, rows []map[string]interface{}, columns []string) error {
	cols := columns
	if len(cols) == 0 {
		cols = unionKeys(rows)
	}

	cw := csv.NewWriter(w)
	if err := cw.Write(cols); err != nil {
		return err
	}
	for _, row := range rows {
		rec := make([]string, len(cols))
		for i, c := range cols {
			rec[i] = formatCell(row[c])
		}
		if err := cw.Write(rec); err != nil {
			return err
		}
	}
	cw.Flush()
	return cw.Error()
}

// renderCount prints the authoritative server-side total for a --count request.
//
// It has no rows-returned fallback any more, and must not grow one back. A
// count-only request carries $top=0, so len(res.Value) is 0 by construction —
// the old fallback would have printed "0" under a note nobody reads and called
// it the total. runList refuses outright when the server withholds odata.count,
// which is why this function can require it.
func renderCount(w io.Writer, res *client.QueryResult, asJSON bool) error {
	if !res.CountKnown {
		return &errs.APIError{Msg: "no server-side total to print (odata.count absent)"}
	}
	if asJSON {
		return renderJSONValue(w, map[string]interface{}{
			"count":      res.Count,
			"serverSide": true,
		})
	}
	fmt.Fprintln(w, res.Count)
	return nil
}

// renderJSONValue writes a single value as indented JSON.
func renderJSONValue(w io.Writer, v interface{}) error {
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}

func unionKeys(rows []map[string]interface{}) []string {
	seen := map[string]bool{}
	var keys []string
	for _, row := range rows {
		for k := range row {
			if !seen[k] {
				seen[k] = true
				keys = append(keys, k)
			}
		}
	}
	sort.Strings(keys)
	return keys
}

func formatCell(v interface{}) string {
	if v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	case bool:
		if t {
			return "true"
		}
		return "false"
	case float64:
		// SAP OData numbers decode as float64; print integral values without
		// a trailing ".0" since most SAP numeric fields (DocEntry, DocNum,
		// QuantityOnStock counts, etc.) read better that way.
		if t == float64(int64(t)) {
			return fmt.Sprintf("%d", int64(t))
		}
		return fmt.Sprintf("%v", t)
	default:
		b, err := json.Marshal(t)
		if err != nil {
			return fmt.Sprintf("%v", t)
		}
		return string(b)
	}
}

// parseFieldList splits a comma-separated $select-style field list (as used
// for both the OData query and the table's column order) into a slice.
// An empty/blank input returns nil, which tells renderTable to fall back to
// the union-of-all-keys behavior.
func parseFieldList(s string) []string {
	if strings.TrimSpace(s) == "" {
		return nil
	}
	parts := strings.Split(s, ",")
	cols := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			cols = append(cols, p)
		}
	}
	return cols
}
