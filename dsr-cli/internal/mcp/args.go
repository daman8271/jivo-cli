package mcp

import (
	"encoding/json"
	"fmt"
	"math"
	"sort"
	"strconv"
	"strings"
)

// Strict argument decoding.
//
// The rule: NOTHING an agent passes is ever silently ignored. An argument the
// server does not understand is not a harmless extra — it is a statement of
// intent that the answer failed to honour, and on a data tool that produces a
// confidently wrong number with no tell. Every unknown key is therefore a hard
// tool error that names the offending key AND lists the valid ones, so the
// agent can fix the call in one retry instead of guessing.
//
// The same table drives the advertised JSON schema (see tools.go), so what a
// client is told it may send and what the server actually accepts cannot drift
// apart.

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

// param declares one accepted tool parameter and the dsr CLI flag it becomes.
//
// Flag is the CLI flag name WITHOUT the leading dashes; an empty Flag marks a
// positional argument (the CLI takes it as a bare token, e.g.
// `dsr retailers get 4210`). Two params may map to the same Flag when the same
// flag is typed differently on different subcommands — `dsr geography zones
// --state <id>` versus `dsr beats shops --state <name>` — which is why the
// mapping is explicit rather than derived from the name.
type param struct {
	Name string
	Flag string
	Kind paramKind
	Desc string
	Enum []string
	// Min/Max bound kindInt values. Max is enforced only when > 0.
	Min, Max int
}

func (p param) positional() bool { return p.Flag == "" }

// action is one entry of a tool's hand-authored allowlist: a fixed argv prefix
// into the dsr command tree plus the exact parameters that may accompany it.
//
// Argv is a literal, not a template — nothing a caller sends can change which
// subcommand runs. An action name that is not in the tool's table is an error,
// never a passthrough, which is what keeps `schema dump` (the one dsr command
// with filesystem side effects) off the MCP surface for good.
type action struct {
	Name string
	Argv []string
	// Pos names the parameter supplying the command's positional argument.
	Pos string
	// PosRequired fails the call when Pos is missing.
	PosRequired bool
	// Flags are the parameter names this action accepts, beyond Pos.
	Flags []string
	// Required lists parameters (flags) the underlying command demands.
	Required []string
	Desc     string
}

// toolSpec is the complete accepted surface of one MCP tool.
type toolSpec struct {
	Name  string
	Title string
	Desc  string
	// Fixed is the argv for tools that have no action selector (doctor, query).
	Fixed []string
	// Pos/PosRequired apply to Fixed-argv tools.
	Pos         string
	PosRequired bool
	Params      []param
	Actions     []action
}

func (t *toolSpec) param(name string) (param, bool) {
	for _, p := range t.Params {
		if p.Name == name {
			return p, true
		}
	}
	return param{}, false
}

func (t *toolSpec) action(name string) (action, bool) {
	for _, a := range t.Actions {
		if a.Name == name {
			return a, true
		}
	}
	return action{}, false
}

func (t *toolSpec) actionNames() []string {
	out := make([]string, 0, len(t.Actions))
	for _, a := range t.Actions {
		out = append(out, a.Name)
	}
	return out
}

// paramNames lists every accepted key, "action" included, sorted for stable
// error text.
func (t *toolSpec) paramNames() []string {
	out := make([]string, 0, len(t.Params)+1)
	if len(t.Actions) > 0 {
		out = append(out, "action")
	}
	for _, p := range t.Params {
		out = append(out, p.Name)
	}
	sort.Strings(out)
	return out
}

// decode validates raw tool arguments against the spec and returns them typed.
// Values come back as strings already formatted the way the CLI wants them;
// booleans come back as "" (absent/false) or "true".
func (t *toolSpec) decode(raw map[string]any) (map[string]string, error) {
	allowed := map[string]bool{}
	for _, n := range t.paramNames() {
		allowed[n] = true
	}
	for k := range raw {
		if !allowed[k] {
			return nil, fmt.Errorf("unknown parameter %q for tool %s. Valid parameters: %s",
				k, t.Name, strings.Join(t.paramNames(), ", "))
		}
	}

	out := make(map[string]string, len(raw))
	for _, p := range t.Params {
		v, ok := raw[p.Name]
		if !ok || v == nil {
			continue
		}
		s, err := coerce(p, v)
		if err != nil {
			return nil, err
		}
		if s == "" {
			continue
		}
		out[p.Name] = s
	}
	return out, nil
}

// coerce type-checks one value and renders it as the CLI argument text.
func coerce(p param, v any) (string, error) {
	switch p.Kind {
	case kindString:
		s, ok := v.(string)
		if !ok {
			return "", fmt.Errorf("parameter %q must be %s, got %T", p.Name, p.Kind, v)
		}
		s = strings.TrimSpace(s)
		if s == "" {
			return "", nil
		}
		if len(p.Enum) > 0 && !contains(p.Enum, s) {
			return "", fmt.Errorf("parameter %q must be one of: %s (got %q)", p.Name, strings.Join(p.Enum, ", "), s)
		}
		return s, nil

	case kindInt:
		f, ok := toFloat(v)
		if !ok {
			return "", fmt.Errorf("parameter %q must be %s, got %T", p.Name, p.Kind, v)
		}
		if math.Trunc(f) != f {
			return "", fmt.Errorf("parameter %q must be %s, got %v", p.Name, p.Kind, v)
		}
		n := int(f)
		if n < p.Min {
			return "", fmt.Errorf("parameter %q must be >= %d (got %d)", p.Name, p.Min, n)
		}
		if p.Max > 0 && n > p.Max {
			return "", fmt.Errorf("parameter %q must be <= %d (got %d)", p.Name, p.Max, n)
		}
		return strconv.Itoa(n), nil

	case kindBool:
		b, ok := v.(bool)
		if !ok {
			return "", fmt.Errorf("parameter %q must be %s, got %T", p.Name, p.Kind, v)
		}
		if !b {
			// A false boolean is the CLI default; emitting nothing is what
			// "false" means for a Cobra bool flag.
			return "", nil
		}
		return "true", nil
	}
	return "", fmt.Errorf("parameter %q has no declared type", p.Name)
}

func toFloat(v any) (float64, bool) {
	switch n := v.(type) {
	case float64:
		return n, true
	case float32:
		return float64(n), true
	case int:
		return float64(n), true
	case int64:
		return float64(n), true
	case json.Number:
		f, err := n.Float64()
		if err != nil {
			return 0, false
		}
		return f, true
	}
	return 0, false
}

func contains(list []string, s string) bool {
	for _, v := range list {
		if v == s {
			return true
		}
	}
	return false
}
