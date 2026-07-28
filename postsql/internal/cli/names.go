package cli

import "strings"

// splitTableName parses a "[schema.]table" argument into (schema, table).
//
// It is the single shared parser used by every table-argument command so they
// all agree on the split: the FIRST dot separates schema from table (a table
// name may itself contain dots), both halves are trimmed, and an absent or
// empty schema defaults to "public".
func splitTableName(arg string) (schema, table string) {
	arg = strings.TrimSpace(arg)
	if i := strings.IndexByte(arg, '.'); i >= 0 {
		schema = strings.TrimSpace(arg[:i])
		table = strings.TrimSpace(arg[i+1:])
	} else {
		table = arg
	}
	if schema == "" {
		schema = "public"
	}
	return schema, table
}

// validateWhere guards the raw --where expression. --where is trusted,
// single-expression input concatenated into the query; it must NOT be able to
// terminate the statement and append another one. GuardReadOnly only inspects
// the leading token (the tool's own SELECT), and the READ ONLY transaction is
// the sole barrier for anything after it — so we reject a statement terminator
// here to keep --where a filter, not a statement-breakout vector.
func validateWhere(where string) error {
	if strings.ContainsRune(where, ';') {
		return Usagef("--where must be a single boolean expression; ';' (statement terminator) is not allowed")
	}
	return nil
}
