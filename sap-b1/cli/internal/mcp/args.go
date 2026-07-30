package mcp

import (
	"fmt"
	"sort"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
)

// Strict argument decoding.
//
// The rule this file exists to enforce: NOTHING an agent passes is ever
// silently ignored. Before this, sapb1_query accepted `company`, `companyDB`,
// `db` and `database`, dropped them on the floor, and answered from the one
// configured company — so an Oil figure could be presented as a Beverages
// figure with no tell. An argument the server does not understand is not a
// harmless extra; it is a statement of intent that the answer failed to
// honour. Every such argument is therefore a hard tool error naming the
// offending key AND listing the valid ones.
//
// Every handler decodes through this file. Bounds, types, enums and mutually
// exclusive combinations are declared once, per tool, in toolSpecs (see
// server.go's registration, which mirrors the same list into the advertised
// JSON schema).

// paramKind is the JSON type a parameter must have.
type paramKind uint8

const (
	kindString paramKind = iota + 1
	kindInt
	kindBool
)

func (k paramKind) String() string {
	switch k {
	case kindString:
		return "a string"
	case kindInt:
		return "a whole number"
	case kindBool:
		return "true or false"
	}
	return "a value"
}

// paramSpec declares one accepted parameter.
type paramSpec struct {
	Name     string
	Kind     paramKind
	Required bool
	// Hint is appended to the "missing required parameter" error, e.g. `Orders`.
	Hint string
	// Min is always enforced for kindInt. Max is enforced only when > 0.
	Min int
	Max int
}

// exclusion is a pair of parameters that must not both be active in one call.
// "Active" means present, and for booleans additionally true — passing
// count=false alongside top=50 is not a conflict.
type exclusion struct {
	A, B string
	// Why explains the conflict in the error, so the agent can pick one.
	Why string
}

// toolSpec is the complete accepted argument surface of one tool. Params are
// listed in the order they appear in error messages — the order a human would
// read them in, not alphabetical.
type toolSpec struct {
	Name       string
	Params     []paramSpec
	Exclusions []exclusion
}

// Shared bounds. These are deliberately generous but finite: an unbounded top
// against a 12,861-row entity set is a request to page the whole book into a
// model's context.
const (
	// maxTop bounds an explicit top.
	maxTop = 5000
	// maxAllRows bounds how many rows all=true will return in one response.
	maxAllRows = 5000
	// defaultAllPageSize is the Prefer: odata.maxpagesize used for all=true —
	// bigger than the Service Layer's default 20, so a full sweep costs fewer
	// round trips.
	defaultAllPageSize = 100
	// maxPageSize bounds an explicit page_size.
	maxPageSize = 500
)

// paging is the pagination/counting parameter set shared by every row-returning
// tool, so all five behave identically.
func pagingParams() []paramSpec {
	return []paramSpec{
		{Name: "top", Kind: kindInt, Min: 1, Max: maxTop},
		{Name: "skip", Kind: kindInt, Min: 0},
		{Name: "page_size", Kind: kindInt, Min: 1, Max: maxPageSize},
		{Name: "all", Kind: kindBool},
		{Name: "count", Kind: kindBool},
	}
}

// pagingExclusions are the combinations that would otherwise mean one of the
// two arguments got quietly dropped.
func pagingExclusions() []exclusion {
	return []exclusion{
		{A: "count", B: "all", Why: "count returns the server-side total in one call; all pages through the rows"},
		{A: "count", B: "top", Why: "count returns the server-side total, not a page of rows"},
		{A: "count", B: "skip", Why: "count totals the whole filtered set; an offset would not change it"},
		{A: "count", B: "page_size", Why: "count needs no paging"},
		{A: "all", B: "top", Why: "all returns every matching row (up to the cap); use top on its own to bound the result"},
		// count returns no rows at all, so a projection and an ordering over
		// them cannot be honoured. Silently accepting either would be the same
		// defect this file exists to close, just with a harmless-looking effect.
		{A: "count", B: "select", Why: "count returns only a total; there are no rows to project. Drop select, or drop count to fetch rows"},
		{A: "count", B: "orderby", Why: "count returns only a total; ordering nothing changes nothing. Drop orderby, or drop count to fetch rows"},
	}
}

func companyParam() paramSpec {
	return paramSpec{Name: "company", Kind: kindString}
}

// rowToolSpec builds the spec for a row-returning tool: company, the tool's own
// parameters, then the shared paging set.
func rowToolSpec(name string, own ...paramSpec) toolSpec {
	params := append([]paramSpec{companyParam()}, own...)
	params = append(params, pagingParams()...)
	return toolSpec{Name: name, Params: params, Exclusions: pagingExclusions()}
}

// toolSpecs is the single source of truth for what each tool accepts.
var toolSpecs = map[string]toolSpec{
	"sapb1_query": rowToolSpec("sapb1_query",
		paramSpec{Name: "entity", Kind: kindString, Required: true, Hint: `"Orders"`},
		paramSpec{Name: "select", Kind: kindString},
		paramSpec{Name: "filter", Kind: kindString},
		paramSpec{Name: "orderby", Kind: kindString},
	),
	"sapb1_orders": rowToolSpec("sapb1_orders",
		paramSpec{Name: "filter", Kind: kindString},
		paramSpec{Name: "open", Kind: kindBool},
	),
	"sapb1_invoices": rowToolSpec("sapb1_invoices",
		paramSpec{Name: "filter", Kind: kindString},
		paramSpec{Name: "open", Kind: kindBool},
	),
	"sapb1_items": rowToolSpec("sapb1_items",
		paramSpec{Name: "filter", Kind: kindString},
		paramSpec{Name: "lowStock", Kind: kindInt, Min: 0},
	),
	"sapb1_partners": func() toolSpec {
		s := rowToolSpec("sapb1_partners",
			paramSpec{Name: "filter", Kind: kindString},
			paramSpec{Name: "customers", Kind: kindBool},
			paramSpec{Name: "suppliers", Kind: kindBool},
		)
		s.Exclusions = append(s.Exclusions, exclusion{
			A: "customers", B: "suppliers",
			Why: "a partner is filtered to one CardType or the other; omit both to list all",
		})
		return s
	}(),
	"sapb1_doctor": {Name: "sapb1_doctor", Params: []paramSpec{companyParam()}},
	"sapb1_fields": {Name: "sapb1_fields", Params: []paramSpec{
		companyParam(),
		{Name: "entity", Kind: kindString, Required: true, Hint: `"Orders"`},
	}},
	"sapb1_entities": {Name: "sapb1_entities", Params: []paramSpec{
		companyParam(),
		{Name: "search", Kind: kindString},
		{Name: "readOnly", Kind: kindBool},
	}},
	"sapb1_ops": {Name: "sapb1_ops", Params: []paramSpec{
		companyParam(),
		{Name: "service", Kind: kindString, Required: true, Hint: `"Orders"`},
	}},
}

// toolArgs is a decoded, fully validated argument set. Every accessor is
// total: if decoding succeeded, reading a parameter cannot fail.
type toolArgs struct {
	tool    string
	strs    map[string]string
	ints    map[string]int
	bools   map[string]bool
	present map[string]bool
}

// Str returns a string parameter, or "" if it was not passed.
func (a *toolArgs) Str(name string) string { return a.strs[name] }

// Int returns an int parameter, or def if it was not passed.
func (a *toolArgs) Int(name string, def int) int {
	if v, ok := a.ints[name]; ok {
		return v
	}
	return def
}

// Bool returns a bool parameter, or false if it was not passed.
func (a *toolArgs) Bool(name string) bool { return a.bools[name] }

// Has reports whether the caller passed the parameter at all — the difference
// between "top defaulted to 20" and "the caller asked for 20".
func (a *toolArgs) Has(name string) bool { return a.present[name] }

// decodeRequest validates a tool call's arguments against the tool's spec.
func decodeRequest(tool string, req mcp.CallToolRequest) (*toolArgs, error) {
	spec, ok := toolSpecs[tool]
	if !ok {
		// Unreachable in practice: every registered tool has a spec, and
		// TestEveryRegisteredToolHasASpec proves it.
		return nil, fmt.Errorf("internal error: no argument spec registered for %s", tool)
	}
	return decodeArgs(spec, req.GetArguments())
}

// decodeArgs is the whole decoder. It rejects, in order: unknown keys, wrong
// types, out-of-range values, missing required parameters, and mutually
// exclusive combinations.
func decodeArgs(spec toolSpec, raw map[string]any) (*toolArgs, error) {
	byName := make(map[string]paramSpec, len(spec.Params))
	for _, p := range spec.Params {
		byName[p.Name] = p
	}

	// 1. Unknown keys — the defect this decoder exists for. Reported together
	// and sorted, so the message is deterministic and one round trip fixes all
	// of them.
	var unknown []string
	for k := range raw {
		if _, ok := byName[k]; !ok {
			unknown = append(unknown, k)
		}
	}
	if len(unknown) > 0 {
		sort.Strings(unknown)
		quoted := make([]string, 0, len(unknown))
		for _, k := range unknown {
			quoted = append(quoted, fmt.Sprintf("%q", k))
		}
		noun := "parameter"
		if len(unknown) > 1 {
			noun = "parameters"
		}
		return nil, fmt.Errorf("unknown %s %s for %s — valid parameters: %s",
			noun, strings.Join(quoted, ", "), spec.Name, strings.Join(paramNames(spec), ", "))
	}

	args := &toolArgs{
		tool:    spec.Name,
		strs:    map[string]string{},
		ints:    map[string]int{},
		bools:   map[string]bool{},
		present: map[string]bool{},
	}

	// 2. Types and bounds, in declaration order so errors are deterministic.
	for _, p := range spec.Params {
		v, ok := raw[p.Name]
		if !ok {
			if p.Required {
				return nil, missingRequired(spec, p)
			}
			continue
		}
		// An explicit null is NOT the same as omitting the parameter. Treating
		// it as "absent" is how `company: null` — an agent whose company
		// variable evaluated to nothing — quietly becomes "the default
		// company", which is the one substitution this surface must never make.
		// It is also invalid against the advertised schema (no property is
		// nullable), so a schema-aware client never sends it by accident.
		if v == nil {
			if p.Required {
				return nil, missingRequired(spec, p)
			}
			return nil, nullErr(spec, p)
		}
		args.present[p.Name] = true

		switch p.Kind {
		case kindString:
			s, ok := v.(string)
			if !ok {
				return nil, typeErr(spec, p, v)
			}
			s = strings.TrimSpace(s)
			if s == "" && p.Required {
				return nil, missingRequired(spec, p)
			}
			args.strs[p.Name] = s
		case kindInt:
			n, err := asInt(v)
			if err != nil {
				return nil, typeErr(spec, p, v)
			}
			if n < p.Min || (p.Max > 0 && n > p.Max) {
				return nil, boundsErr(spec, p, n)
			}
			args.ints[p.Name] = n
		case kindBool:
			b, ok := v.(bool)
			if !ok {
				return nil, typeErr(spec, p, v)
			}
			args.bools[p.Name] = b
		}
	}

	// 3. Mutually exclusive combinations — each a named error, never a silent
	// "the other one wins".
	for _, ex := range spec.Exclusions {
		if args.active(ex.A) && args.active(ex.B) {
			return nil, fmt.Errorf("parameters %q and %q are mutually exclusive for %s — %s",
				ex.A, ex.B, spec.Name, ex.Why)
		}
	}

	return args, nil
}

// active reports whether a parameter should count towards a mutual-exclusion
// conflict: present, and — for a boolean — actually switched on.
func (a *toolArgs) active(name string) bool {
	if !a.present[name] {
		return false
	}
	if b, isBool := a.bools[name]; isBool {
		return b
	}
	return true
}

func paramNames(spec toolSpec) []string {
	out := make([]string, 0, len(spec.Params))
	for _, p := range spec.Params {
		out = append(out, p.Name)
	}
	return out
}

func missingRequired(spec toolSpec, p paramSpec) error {
	msg := fmt.Sprintf("missing required parameter %q for %s", p.Name, spec.Name)
	if p.Hint != "" {
		msg += ", e.g. " + p.Hint
	}
	return fmt.Errorf("%s", msg)
}

// nullErr rejects an explicitly-null optional parameter, and says what to do
// instead — the fix is either a real value or leaving the key out entirely.
func nullErr(spec toolSpec, p paramSpec) error {
	return fmt.Errorf("parameter %q of %s was passed as null — pass %s, or omit the parameter entirely to use the default; "+
		"a null is not treated as \"not specified\", because that is how a call meaning one thing silently answers another",
		p.Name, spec.Name, p.Kind)
}

func typeErr(spec toolSpec, p paramSpec, v any) error {
	return fmt.Errorf("parameter %q of %s must be %s, got %s",
		p.Name, spec.Name, p.Kind, describe(v))
}

func boundsErr(spec toolSpec, p paramSpec, n int) error {
	if p.Max > 0 {
		return fmt.Errorf("parameter %q of %s must be between %d and %d, got %d",
			p.Name, spec.Name, p.Min, p.Max, n)
	}
	return fmt.Errorf("parameter %q of %s must be %d or greater, got %d",
		p.Name, spec.Name, p.Min, n)
}

// asInt accepts the JSON encodings an integer can legitimately arrive as — a
// JSON number that happens to be whole, or a Go int from an in-process caller
// — and rejects everything else, including a fractional number. 12.5 rows is
// not a rounding opportunity, it is a mistake worth surfacing.
func asInt(v any) (int, error) {
	switch n := v.(type) {
	case int:
		return n, nil
	case int32:
		return int(n), nil
	case int64:
		return int(n), nil
	case float64:
		if n != float64(int64(n)) {
			return 0, fmt.Errorf("not a whole number")
		}
		return int(n), nil
	case float32:
		if float64(n) != float64(int64(n)) {
			return 0, fmt.Errorf("not a whole number")
		}
		return int(n), nil
	}
	return 0, fmt.Errorf("not a number")
}

// describe renders the value an agent actually sent, for the error message.
func describe(v any) string {
	switch t := v.(type) {
	case string:
		return fmt.Sprintf("the string %q", t)
	case bool:
		return fmt.Sprintf("the boolean %v", t)
	case float64:
		if t == float64(int64(t)) {
			return fmt.Sprintf("the number %d", int64(t))
		}
		return fmt.Sprintf("the number %v", t)
	case []any:
		return "an array"
	case map[string]any:
		return "an object"
	case nil:
		return "null"
	}
	return fmt.Sprintf("%v", v)
}

// companyEnum is the set of SAP company databases this deployment serves. It
// is advertised in every tool's schema and enforced by resolveCompany.
var companyEnum = []string{
	"JIVO_OIL_HANADB",
	"JIVO_MART_HANADB",
	"JIVO_BEVERAGES_HANADB",
}

// resolveCompany turns the `company` argument into the CompanyDB to log into.
// Empty means "the configured default". Anything else must name a real company
// — a typo must never fall back to the default, because a silently-defaulted
// company is exactly how one company's numbers get reported as another's.
func resolveCompany(arg, configured string) (string, error) {
	arg = strings.TrimSpace(arg)
	if arg == "" {
		if strings.TrimSpace(configured) == "" {
			return "", fmt.Errorf("no company selected and no default configured — pass company (one of: %s) or set SAPB1_COMPANYDB",
				strings.Join(companyEnum, ", "))
		}
		return configured, nil
	}
	for _, c := range companyEnum {
		if arg == c {
			return arg, nil
		}
	}
	if configured != "" && arg == configured {
		return arg, nil
	}
	msg := fmt.Sprintf("unknown company %q — valid values: %s", arg, strings.Join(companyEnum, ", "))
	if configured != "" {
		msg += fmt.Sprintf(" (default when omitted: %s)", configured)
	}
	return "", fmt.Errorf("%s", msg)
}
