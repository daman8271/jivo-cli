// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — HR compensation redaction.

package mcp

import (
	"encoding/json"
	"regexp"
	"sort"
)

// salaryKey matches the compensation-shaped field names JSAP's hierarchy
// payloads carry alongside names, employee codes, designations and dates of
// joining: hodSalary, subHodSalary, execSalary and friends.
//
// Why redact rather than trust the exclusion list: the two salary-only
// endpoints (GetSalarySessionData, GetEmployeesForSalaryPermission) are simply
// not catalogued, but the salary COLUMNS ride along inside ordinary org-tree
// reads like hierarchy.flat. This gateway is published on a public hostname
// behind a secret path prefix, not an authenticated ACL, so the org chart may
// travel and the pay must not. Keys are matched, values never are — a ledger
// account literally named "SALARY & WAGES" stays intact because it is a value.
var salaryKey = regexp.MustCompile(`(?i)salary|ctc|payscale|remuneration|grosspay|gross_pay|netpay|net_pay`)

// redactSalaries strips compensation-shaped keys from a decoded JSON payload
// and reports which key names were removed, so the answer says what is missing
// instead of quietly under-reporting a record.
func redactSalaries(payload json.RawMessage) (json.RawMessage, []string, error) {
	var decoded any
	if err := json.Unmarshal(payload, &decoded); err != nil {
		// Not JSON (already-encoded string, scalar, or empty): nothing to walk.
		return payload, nil, nil
	}
	removed := map[string]bool{}
	cleaned := walkRedact(decoded, removed)
	if len(removed) == 0 {
		return payload, nil, nil
	}
	encoded, err := json.Marshal(cleaned)
	if err != nil {
		return nil, nil, err
	}
	names := make([]string, 0, len(removed))
	for name := range removed {
		names = append(names, name)
	}
	sort.Strings(names)
	return encoded, names, nil
}

func walkRedact(node any, removed map[string]bool) any {
	switch v := node.(type) {
	case map[string]any:
		out := make(map[string]any, len(v))
		for key, value := range v {
			if salaryKey.MatchString(key) {
				removed[key] = true
				continue
			}
			out[key] = walkRedact(value, removed)
		}
		return out
	case []any:
		out := make([]any, 0, len(v))
		for _, item := range v {
			out = append(out, walkRedact(item, removed))
		}
		return out
	default:
		return node
	}
}
