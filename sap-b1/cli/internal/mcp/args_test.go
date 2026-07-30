package mcp

import (
	"encoding/json"
	"fmt"
	"strings"
	"testing"

	"github.com/mark3labs/mcp-go/mcp"
)

// specFor fetches a tool's argument spec, failing the test if it is missing.
func specFor(t *testing.T, tool string) toolSpec {
	t.Helper()
	spec, ok := toolSpecs[tool]
	if !ok {
		t.Fatalf("no argument spec registered for %q", tool)
	}
	return spec
}

// TestEveryRegisteredToolHasASpec is the structural link between the two halves
// of strict decoding: the schema advertised by server.go and the decoder that
// enforces it. A tool registered without a spec would panic-by-error on its
// first call, so this fails at build time instead.
func TestEveryRegisteredToolHasASpec(t *testing.T) {
	s := newTestServer()
	for name := range s.MCPServer().ListTools() {
		if _, ok := toolSpecs[name]; !ok {
			t.Errorf("tool %q is registered but has no entry in toolSpecs — every handler must decode through decodeRequest", name)
		}
	}
	for name := range toolSpecs {
		if _, ok := s.MCPServer().ListTools()[name]; !ok {
			t.Errorf("toolSpecs has an entry for %q, which is not a registered tool — dead spec", name)
		}
	}
}

// TestAdvertisedSchemaMatchesDecoder pins the schema and the decoder to the same
// parameter list. If they drift, a client is told about a parameter the decoder
// rejects (or vice versa) — the silent-discard class of defect, reintroduced
// through the back door.
func TestAdvertisedSchemaMatchesDecoder(t *testing.T) {
	s := newTestServer()
	for name, st := range s.MCPServer().ListTools() {
		spec := specFor(t, name)

		declared := map[string]bool{}
		for _, p := range spec.Params {
			declared[p.Name] = true
		}
		advertised := map[string]bool{}
		for prop := range st.Tool.InputSchema.Properties {
			advertised[prop] = true
		}

		for prop := range advertised {
			if !declared[prop] {
				t.Errorf("%s advertises parameter %q that the decoder would reject as unknown", name, prop)
			}
		}
		for prop := range declared {
			if !advertised[prop] {
				t.Errorf("%s accepts parameter %q but never advertises it — an agent cannot discover it", name, prop)
			}
		}

		// Required-ness must agree too, or a call the schema calls valid fails
		// in the decoder.
		required := map[string]bool{}
		for _, r := range st.Tool.InputSchema.Required {
			required[r] = true
		}
		for _, p := range spec.Params {
			if p.Required != required[p.Name] {
				t.Errorf("%s parameter %q: decoder required=%v, advertised required=%v", name, p.Name, p.Required, required[p.Name])
			}
		}
	}
}

// TestUnknownParameterIsRejected is the D2 unit-level guard: the exact defect
// that let an Oil figure be presented as a Beverages figure was `company`,
// `companyDB`, `db` and `database` being accepted and dropped. Every one of
// them must now be a hard error that both names the key and lists the valid
// alternatives — the error has to be actionable in one round trip.
func TestUnknownParameterIsRejected(t *testing.T) {
	cases := []struct {
		name    string
		tool    string
		args    map[string]any
		wantAll []string
	}{
		{
			name:    "the historical silent-discard key",
			tool:    "sapb1_query",
			args:    map[string]any{"entity": "Invoices", "companyDB": "JIVO_MART_HANADB"},
			wantAll: []string{`"companyDB"`, "sapb1_query", "company", "entity", "select", "filter", "orderby", "top", "skip", "page_size", "all", "count"},
		},
		{
			name:    "db",
			tool:    "sapb1_query",
			args:    map[string]any{"entity": "Invoices", "db": "JIVO_MART_HANADB"},
			wantAll: []string{`"db"`, "valid parameters"},
		},
		{
			name:    "database",
			tool:    "sapb1_partners",
			args:    map[string]any{"database": "JIVO_MART_HANADB"},
			wantAll: []string{`"database"`, "valid parameters", "company"},
		},
		{
			name:    "several unknown keys are reported together and sorted",
			tool:    "sapb1_items",
			args:    map[string]any{"zulu": 1, "alpha": 2},
			wantAll: []string{"unknown parameters", `"alpha", "zulu"`},
		},
		{
			name:    "a near-miss on a real parameter is not silently coerced",
			tool:    "sapb1_query",
			args:    map[string]any{"entity": "Orders", "orderBy": "DocDate desc"},
			wantAll: []string{`"orderBy"`, "orderby"},
		},
		{
			name:    "smuggled paging arguments",
			tool:    "sapb1_query",
			args:    map[string]any{"entity": "Orders", "$skip": 40},
			wantAll: []string{`"$skip"`, "skip"},
		},
		{
			name:    "offline tools are just as strict",
			tool:    "sapb1_entities",
			args:    map[string]any{"searchTerm": "invoice"},
			wantAll: []string{`"searchTerm"`, "search", "readOnly"},
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := decodeArgs(specFor(t, tc.tool), tc.args)
			if err == nil {
				t.Fatalf("decodeArgs accepted unknown arguments %v — that is the silent-discard defect", tc.args)
			}
			for _, want := range tc.wantAll {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}
}

// TestEveryToolRejectsUnknownParameters makes the guarantee exhaustive rather
// than sampled: no tool, present or future, may quietly swallow an argument.
func TestEveryToolRejectsUnknownParameters(t *testing.T) {
	for name, spec := range toolSpecs {
		t.Run(name, func(t *testing.T) {
			args := minimalArgs(spec)
			args["definitely_not_a_parameter"] = "x"
			_, err := decodeArgs(spec, args)
			if err == nil {
				t.Fatalf("%s accepted an unknown parameter", name)
			}
			if !strings.Contains(err.Error(), "definitely_not_a_parameter") {
				t.Errorf("%s: error must name the offending key, got: %v", name, err)
			}
			if !strings.Contains(err.Error(), "valid parameters:") {
				t.Errorf("%s: error must list the valid parameters, got: %v", name, err)
			}
			// Naming the tool is what makes a multi-tool transcript debuggable.
			if !strings.Contains(err.Error(), name) {
				t.Errorf("%s: error must name the tool, got: %v", name, err)
			}
		})
	}
}

// minimalArgs builds the smallest argument set a spec accepts.
func minimalArgs(spec toolSpec) map[string]any {
	args := map[string]any{}
	for _, p := range spec.Params {
		if !p.Required {
			continue
		}
		switch p.Kind {
		case kindString:
			args[p.Name] = "Orders"
		case kindInt:
			args[p.Name] = 1
		case kindBool:
			args[p.Name] = true
		}
	}
	return args
}

func TestTypeErrorsAreNamed(t *testing.T) {
	spec := specFor(t, "sapb1_query")
	cases := []struct {
		name string
		args map[string]any
		want []string
	}{
		{"top as a string", map[string]any{"entity": "Orders", "top": "50"}, []string{`"top"`, "whole number", `the string "50"`}},
		{"top fractional", map[string]any{"entity": "Orders", "top": 12.5}, []string{`"top"`, "whole number", "12.5"}},
		{"all as a string", map[string]any{"entity": "Orders", "all": "true"}, []string{`"all"`, "true or false"}},
		{"count as a number", map[string]any{"entity": "Orders", "count": 1.0}, []string{`"count"`, "true or false"}},
		{"filter as an object", map[string]any{"entity": "Orders", "filter": map[string]any{"a": 1}}, []string{`"filter"`, "a string", "an object"}},
		{"entity as a number", map[string]any{"entity": 7.0}, []string{`"entity"`, "a string"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := decodeArgs(spec, tc.args)
			if err == nil {
				t.Fatalf("decodeArgs accepted %v", tc.args)
			}
			for _, want := range tc.want {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}
}

// TestBoundsAreEnforced pins every numeric edge. The in-range cases matter as
// much as the rejections: a bound that is one off silently truncates a legal
// request.
func TestBoundsAreEnforced(t *testing.T) {
	spec := specFor(t, "sapb1_query")
	cases := []struct {
		name    string
		args    map[string]any
		wantErr bool
		errBits []string
	}{
		{"top 0", map[string]any{"entity": "Orders", "top": 0.0}, true, []string{`"top"`, "between 1 and 5000", "got 0"}},
		{"top negative", map[string]any{"entity": "Orders", "top": -1.0}, true, []string{"between 1 and 5000"}},
		{"top 1", map[string]any{"entity": "Orders", "top": 1.0}, false, nil},
		{"top at max", map[string]any{"entity": "Orders", "top": float64(maxTop)}, false, nil},
		{"top over max", map[string]any{"entity": "Orders", "top": float64(maxTop + 1)}, true, []string{"between 1 and 5000", "5001"}},
		{"skip 0", map[string]any{"entity": "Orders", "skip": 0.0}, false, nil},
		{"skip negative", map[string]any{"entity": "Orders", "skip": -5.0}, true, []string{`"skip"`, "0 or greater"}},
		{"page_size 1", map[string]any{"entity": "Orders", "page_size": 1.0}, false, nil},
		{"page_size at max", map[string]any{"entity": "Orders", "page_size": float64(maxPageSize)}, false, nil},
		{"page_size over max", map[string]any{"entity": "Orders", "page_size": float64(maxPageSize + 1)}, true, []string{`"page_size"`, "between 1 and 500"}},
		{"page_size 0", map[string]any{"entity": "Orders", "page_size": 0.0}, true, []string{"between 1 and 500"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := decodeArgs(spec, tc.args)
			if tc.wantErr && err == nil {
				t.Fatalf("decodeArgs accepted out-of-range %v", tc.args)
			}
			if !tc.wantErr && err != nil {
				t.Fatalf("decodeArgs rejected in-range %v: %v", tc.args, err)
			}
			for _, want := range tc.errBits {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}
}

// TestMutuallyExclusiveParametersAreNamedErrors: the CLI's "--top is ignored
// with --all" behaviour is deliberately NOT carried over. Ignoring an argument
// is how a caller's intent gets lost, which is the whole defect class this
// decoder exists to close.
func TestMutuallyExclusiveParametersAreNamedErrors(t *testing.T) {
	spec := specFor(t, "sapb1_query")
	cases := []struct {
		name string
		args map[string]any
		want []string
	}{
		{"count with all", map[string]any{"entity": "Orders", "count": true, "all": true}, []string{`"count"`, `"all"`, "mutually exclusive"}},
		{"count with top", map[string]any{"entity": "Orders", "count": true, "top": 50.0}, []string{`"count"`, `"top"`, "mutually exclusive"}},
		{"count with skip", map[string]any{"entity": "Orders", "count": true, "skip": 20.0}, []string{`"count"`, `"skip"`}},
		{"count with page_size", map[string]any{"entity": "Orders", "count": true, "page_size": 100.0}, []string{`"count"`, `"page_size"`}},
		{"all with top", map[string]any{"entity": "Orders", "all": true, "top": 50.0}, []string{`"all"`, `"top"`, "mutually exclusive"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := decodeArgs(spec, tc.args)
			if err == nil {
				t.Fatalf("decodeArgs accepted the conflicting pair %v — one of them would have been silently dropped", tc.args)
			}
			for _, want := range tc.want {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}
}

// TestFalseBooleanIsNotAConflict — count=false alongside top=50 states no
// intent to count, so it must not be treated as a conflict. Rejecting it would
// make the strictness user-hostile rather than protective.
func TestFalseBooleanIsNotAConflict(t *testing.T) {
	spec := specFor(t, "sapb1_query")
	for _, args := range []map[string]any{
		{"entity": "Orders", "count": false, "top": 50.0},
		{"entity": "Orders", "all": false, "top": 50.0},
		{"entity": "Orders", "count": false, "all": false, "top": 50.0},
	} {
		if _, err := decodeArgs(spec, args); err != nil {
			t.Errorf("decodeArgs(%v) = %v, want accepted — an explicit false is not a request", args, err)
		}
	}
}

// TestPartnersCustomersAndSuppliersConflict — a partner is one CardType or the
// other; asking for both would have silently taken whichever branch came first.
func TestPartnersCustomersAndSuppliersConflict(t *testing.T) {
	spec := specFor(t, "sapb1_partners")
	_, err := decodeArgs(spec, map[string]any{"customers": true, "suppliers": true})
	if err == nil {
		t.Fatal("decodeArgs accepted customers=true with suppliers=true")
	}
	if !strings.Contains(err.Error(), "mutually exclusive") {
		t.Errorf("error should explain the conflict, got: %v", err)
	}
	// Either one alone is fine.
	for _, k := range []string{"customers", "suppliers"} {
		if _, err := decodeArgs(spec, map[string]any{k: true}); err != nil {
			t.Errorf("decodeArgs(%s=true) = %v, want accepted", k, err)
		}
	}
}

func TestRequiredParameters(t *testing.T) {
	cases := []struct {
		tool string
		args map[string]any
		want []string
	}{
		{"sapb1_query", map[string]any{"top": 5.0}, []string{"missing required parameter", `"entity"`, "sapb1_query", `"Orders"`}},
		{"sapb1_query", map[string]any{"entity": ""}, []string{"missing required parameter", `"entity"`}},
		{"sapb1_query", map[string]any{"entity": "   "}, []string{"missing required parameter", `"entity"`}},
		{"sapb1_query", map[string]any{"entity": nil}, []string{"missing required parameter", `"entity"`}},
		{"sapb1_fields", map[string]any{}, []string{"missing required parameter", `"entity"`}},
		{"sapb1_ops", map[string]any{}, []string{"missing required parameter", `"service"`}},
	}
	for _, tc := range cases {
		t.Run(tc.tool, func(t *testing.T) {
			_, err := decodeArgs(specFor(t, tc.tool), tc.args)
			if err == nil {
				t.Fatalf("decodeArgs(%v) accepted a call with no required parameter", tc.args)
			}
			for _, want := range tc.want {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}
}

func TestDecodedValuesAndDefaults(t *testing.T) {
	a, err := decodeArgs(specFor(t, "sapb1_query"), map[string]any{
		"entity": "  Invoices  ",
		"filter": " DocumentStatus eq 'bost_Open' ",
		"top":    45.0,
		"skip":   20.0,
	})
	if err != nil {
		t.Fatalf("decodeArgs: %v", err)
	}
	if got := a.Str("entity"); got != "Invoices" {
		t.Errorf("entity = %q, want trimmed %q", got, "Invoices")
	}
	if got := a.Str("filter"); got != "DocumentStatus eq 'bost_Open'" {
		t.Errorf("filter = %q, want trimmed", got)
	}
	if got := a.Int("top", 20); got != 45 {
		t.Errorf("top = %d, want 45", got)
	}
	if got := a.Int("page_size", 0); got != 0 {
		t.Errorf("page_size = %d, want the 0 default when omitted", got)
	}
	if a.Bool("count") || a.Bool("all") {
		t.Error("omitted booleans must decode as false")
	}
	if !a.Has("skip") {
		t.Error("Has(skip) = false although skip was passed")
	}
	if a.Has("orderby") {
		t.Error("Has(orderby) = true although orderby was omitted")
	}
	// Has must distinguish an explicitly-passed zero from an absent value.
	b, err := decodeArgs(specFor(t, "sapb1_query"), map[string]any{"entity": "Orders", "skip": 0.0})
	if err != nil {
		t.Fatalf("decodeArgs: %v", err)
	}
	if !b.Has("skip") {
		t.Error("Has(skip) = false for an explicit skip=0")
	}
}

// TestIntEncodings — an int can legitimately arrive as a JSON number (float64
// after unmarshalling) or as a Go int from an in-process caller. Both are
// whole numbers and both must work; a fraction must not be rounded into one.
func TestIntEncodings(t *testing.T) {
	spec := specFor(t, "sapb1_query")
	for _, v := range []any{45, int32(45), int64(45), float64(45), float32(45)} {
		a, err := decodeArgs(spec, map[string]any{"entity": "Orders", "top": v})
		if err != nil {
			t.Fatalf("decodeArgs(top=%T(%v)) = %v, want accepted", v, v, err)
		}
		if got := a.Int("top", 0); got != 45 {
			t.Errorf("top from %T = %d, want 45", v, got)
		}
	}
	for _, v := range []any{45.5, "45", true, nil} {
		if v == nil {
			continue // nil means absent, tested elsewhere
		}
		if _, err := decodeArgs(spec, map[string]any{"entity": "Orders", "top": v}); err == nil {
			t.Errorf("decodeArgs(top=%T(%v)) was accepted, want rejected", v, v)
		}
	}
}

// TestResolveCompany is the D1 core: which company a call actually reads.
func TestResolveCompany(t *testing.T) {
	cases := []struct {
		name       string
		arg        string
		configured string
		want       string
		wantErr    []string
	}{
		{name: "omitted falls back to the configured default", arg: "", configured: "JIVO_OIL_HANADB", want: "JIVO_OIL_HANADB"},
		{name: "whitespace counts as omitted", arg: "   ", configured: "JIVO_OIL_HANADB", want: "JIVO_OIL_HANADB"},
		{name: "mart", arg: "JIVO_MART_HANADB", configured: "JIVO_OIL_HANADB", want: "JIVO_MART_HANADB"},
		{name: "beverages", arg: "JIVO_BEVERAGES_HANADB", configured: "JIVO_OIL_HANADB", want: "JIVO_BEVERAGES_HANADB"},
		{name: "oil explicitly", arg: "JIVO_OIL_HANADB", configured: "JIVO_OIL_HANADB", want: "JIVO_OIL_HANADB"},
		{name: "trimmed", arg: " JIVO_MART_HANADB ", configured: "JIVO_OIL_HANADB", want: "JIVO_MART_HANADB"},
		{
			name: "a typo is an error, NEVER a silent fallback to the default",
			arg:  "JIVO_MART", configured: "JIVO_OIL_HANADB",
			wantErr: []string{"unknown company", `"JIVO_MART"`, "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB", "default when omitted: JIVO_OIL_HANADB"},
		},
		{
			name: "case matters — HANA company names are not case-folded",
			arg:  "jivo_mart_hanadb", configured: "JIVO_OIL_HANADB",
			wantErr: []string{"unknown company"},
		},
		{
			name: "a deployment-specific company that is configured is allowed",
			arg:  "SOME_OTHER_DB", configured: "SOME_OTHER_DB", want: "SOME_OTHER_DB",
		},
		{
			name: "omitted with nothing configured is an actionable error",
			arg:  "", configured: "",
			wantErr: []string{"no company selected and no default configured", "SAPB1_COMPANYDB"},
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := resolveCompany(tc.arg, tc.configured)
			if len(tc.wantErr) > 0 {
				if err == nil {
					t.Fatalf("resolveCompany(%q, %q) = %q, want an error", tc.arg, tc.configured, got)
				}
				for _, want := range tc.wantErr {
					if !strings.Contains(err.Error(), want) {
						t.Errorf("error %q does not mention %q", err, want)
					}
				}
				return
			}
			if err != nil {
				t.Fatalf("resolveCompany(%q, %q) = %v", tc.arg, tc.configured, err)
			}
			if got != tc.want {
				t.Errorf("resolveCompany(%q, %q) = %q, want %q", tc.arg, tc.configured, got, tc.want)
			}
		})
	}
}

// TestDecodeRequestUsesRawArguments proves the decoder reads the request's raw
// argument map — the only place an unknown key still exists. Any typed
// unmarshal into a struct would have dropped it before we could complain.
func TestDecodeRequestUsesRawArguments(t *testing.T) {
	var req mcp.CallToolRequest
	req.Params.Name = "sapb1_query"
	req.Params.Arguments = map[string]any{"entity": "Orders", "companyDB": "JIVO_MART_HANADB"}

	if _, err := decodeRequest("sapb1_query", req); err == nil {
		t.Fatal("decodeRequest accepted an unknown key from a real CallToolRequest")
	} else if !strings.Contains(err.Error(), "companyDB") {
		t.Errorf("error must name the key, got: %v", err)
	}

	req.Params.Arguments = map[string]any{"entity": "Orders", "top": 5.0}
	a, err := decodeRequest("sapb1_query", req)
	if err != nil {
		t.Fatalf("decodeRequest on a valid call: %v", err)
	}
	if a.Str("entity") != "Orders" || a.Int("top", 0) != 5 {
		t.Errorf("decoded %+v, want entity=Orders top=5", a)
	}
}

// TestAdvertisedBoundsAndEnumMatchTheDecoder extends
// TestAdvertisedSchemaMatchesDecoder, which pinned parameter NAMES and
// required-ness only. Names agreeing while ranges drift is its own
// silent-failure: a client told "1-5000" that gets rejected at 4000, or worse,
// a client told "minimum 1" for a parameter whose 0 the decoder accepts and the
// handler then ignores. That last one is exactly how lowStock:0 became a silent
// no-op, so the schema and the decoder are pinned to each other numerically.
func TestAdvertisedBoundsAndEnumMatchTheDecoder(t *testing.T) {
	wantType := map[paramKind]string{
		kindString: "string",
		kindInt:    "number",
		kindBool:   "boolean",
	}

	s := newTestServer()
	checked := 0
	for name, st := range s.MCPServer().ListTools() {
		spec := specFor(t, name)
		for _, p := range spec.Params {
			raw, ok := st.Tool.InputSchema.Properties[p.Name]
			if !ok {
				t.Errorf("%s: parameter %q is not advertised at all", name, p.Name)
				continue
			}
			prop, ok := raw.(map[string]any)
			if !ok {
				t.Errorf("%s: advertised schema for %q is %T, not an object", name, p.Name, raw)
				continue
			}
			checked++

			if got := prop["type"]; got != wantType[p.Kind] {
				t.Errorf("%s.%s: advertised type %v, decoder enforces %v", name, p.Name, got, wantType[p.Kind])
			}

			if p.Kind == kindInt {
				min, present := numberField(prop, "minimum")
				if !present {
					t.Errorf("%s.%s: no advertised minimum, decoder enforces >= %d", name, p.Name, p.Min)
				} else if min != p.Min {
					t.Errorf("%s.%s: advertised minimum %d, decoder enforces %d", name, p.Name, min, p.Min)
				}
				max, present := numberField(prop, "maximum")
				switch {
				case p.Max > 0 && !present:
					t.Errorf("%s.%s: no advertised maximum, decoder enforces <= %d", name, p.Name, p.Max)
				case p.Max > 0 && max != p.Max:
					t.Errorf("%s.%s: advertised maximum %d, decoder enforces %d", name, p.Name, max, p.Max)
				case p.Max == 0 && present:
					t.Errorf("%s.%s: advertises a maximum of %d that the decoder does not enforce", name, p.Name, max)
				}
			} else if _, present := numberField(prop, "minimum"); present {
				t.Errorf("%s.%s: a non-numeric parameter advertises a minimum", name, p.Name)
			}

			// The company enum is the D1 guard rail: a client that cannot see
			// the three valid values cannot discover the other two companies,
			// and resolveCompany rejects anything not on this list.
			if p.Name == "company" {
				var advertised []string
				for _, v := range asSlice(prop["enum"]) {
					advertised = append(advertised, fmt.Sprint(v))
				}
				if strings.Join(advertised, ",") != strings.Join(companyEnum, ",") {
					t.Errorf("%s.company: advertised enum %v, resolveCompany enforces %v", name, advertised, companyEnum)
				}
			}
		}
	}
	if checked == 0 {
		t.Fatal("no advertised parameters were compared — the guard would pass vacuously")
	}
}

// numberField reads a JSON-schema numeric keyword, which may arrive as any of
// Go's numeric types depending on how the schema was built.
func numberField(prop map[string]any, key string) (int, bool) {
	v, ok := prop[key]
	if !ok {
		return 0, false
	}
	switch n := v.(type) {
	case int:
		return n, true
	case int64:
		return int(n), true
	case float64:
		return int(n), true
	case json.Number:
		i, err := n.Int64()
		return int(i), err == nil
	}
	return 0, false
}

// asSlice normalises a JSON-schema list keyword, which the schema builder may
// hold as []string or as a decoded []any.
func asSlice(v any) []any {
	switch s := v.(type) {
	case []any:
		return s
	case []string:
		out := make([]any, 0, len(s))
		for _, e := range s {
			out = append(out, e)
		}
		return out
	}
	return nil
}

// TestExplicitNullIsNotSilentlyTreatedAsAbsent. `company: null` is what an
// agent sends when its company variable evaluated to nothing — and treating it
// as "omitted" hands back the DEFAULT company's numbers with nothing anywhere
// in the answer to say so. That is a miniature of the exact defect this decoder
// exists to close, so a null is a named error. (No advertised property is
// nullable, so a schema-aware client never sends one by accident.)
func TestExplicitNullIsNotSilentlyTreatedAsAbsent(t *testing.T) {
	cases := []struct {
		name string
		tool string
		args map[string]any
		want []string
	}{
		{"company", "sapb1_query", map[string]any{"entity": "Orders", "company": nil}, []string{`"company"`, "null", "omit"}},
		{"top", "sapb1_query", map[string]any{"entity": "Orders", "top": nil}, []string{`"top"`, "null"}},
		{"filter", "sapb1_partners", map[string]any{"filter": nil}, []string{`"filter"`, "null"}},
		{"all", "sapb1_orders", map[string]any{"all": nil}, []string{`"all"`, "null"}},
		{"lowStock", "sapb1_items", map[string]any{"lowStock": nil}, []string{`"lowStock"`, "null"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := decodeArgs(specFor(t, tc.tool), tc.args)
			if err == nil {
				t.Fatalf("decodeArgs accepted %v — a null quietly became \"not specified\"", tc.args)
			}
			for _, want := range tc.want {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}

	// A REQUIRED parameter passed as null keeps its own, clearer message.
	if _, err := decodeArgs(specFor(t, "sapb1_query"), map[string]any{"entity": nil}); err == nil {
		t.Fatal("decodeArgs accepted entity: null")
	} else if !strings.Contains(err.Error(), "missing required parameter") {
		t.Errorf("entity: null should read as a missing required parameter, got: %v", err)
	}

	// And omitting the key entirely is still perfectly legal.
	if _, err := decodeArgs(specFor(t, "sapb1_query"), map[string]any{"entity": "Orders"}); err != nil {
		t.Errorf("omitting optional parameters must stay legal, got: %v", err)
	}
}

// TestCountRejectsSelectAndOrderBy — count returns a total and no rows, so a
// projection or an ordering over those rows cannot be honoured. Accepting them
// and doing nothing is the silent-discard behaviour this file's own doc comment
// calls intolerable; the fact that the effect is harmless is not the point,
// because the caller cannot tell the difference from the outside.
func TestCountRejectsSelectAndOrderBy(t *testing.T) {
	spec := specFor(t, "sapb1_query")
	for _, tc := range []struct {
		name string
		args map[string]any
		want []string
	}{
		{"count with select", map[string]any{"entity": "Orders", "count": true, "select": "DocEntry"}, []string{`"count"`, `"select"`, "mutually exclusive"}},
		{"count with orderby", map[string]any{"entity": "Orders", "count": true, "orderby": "DocDate desc"}, []string{`"count"`, `"orderby"`, "mutually exclusive"}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			_, err := decodeArgs(spec, tc.args)
			if err == nil {
				t.Fatalf("decodeArgs accepted %v — one of the two was going to be dropped in silence", tc.args)
			}
			for _, want := range tc.want {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}

	// count=false is a statement of intent NOT to count, so it conflicts with
	// nothing.
	if _, err := decodeArgs(spec, map[string]any{"entity": "Orders", "count": false, "select": "DocEntry"}); err != nil {
		t.Errorf("count=false with select must stay legal, got: %v", err)
	}
	// And select/orderby on their own are the normal case.
	if _, err := decodeArgs(spec, map[string]any{"entity": "Orders", "select": "DocEntry", "orderby": "DocDate desc"}); err != nil {
		t.Errorf("select+orderby without count must stay legal, got: %v", err)
	}
}
