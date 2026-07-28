// Package catalog embeds the full offline map of SAP B1 Service Layer
// services and their operations (services.json, generated from the Service
// Layer metadata) so the discovery commands — `entities`, `ops`,
// `catalog stats`, and the offline fallback of `fields` — work with zero
// network access.
//
// The catalog is descriptive only. It lists write operations
// (POST/PUT/PATCH/DELETE) for reference, but nothing in this package or the
// CLI ever executes them; sapb1 stays strictly read-only.
package catalog

import (
	_ "embed"
	"encoding/json"
	"sort"
	"strings"
	"sync"
)

//go:embed services.json
var servicesJSON []byte

// Operation is one Service Layer operation: an HTTP method and the OperationId
// (for service actions) or entity operation name it maps to.
type Operation struct {
	Method string `json:"method"`
	Name   string `json:"name"`
}

// Service is one Service Layer service/entity and all of its catalogued
// operations.
type Service struct {
	Service    string      `json:"service"`
	Operations []Operation `json:"operations"`
}

// canonicalMethodOrder is the display order for HTTP methods; anything not
// listed is appended afterwards in alphabetical order.
var canonicalMethodOrder = []string{"GET", "POST", "PATCH", "PUT", "DELETE"}

var (
	loadOnce sync.Once
	services []Service
	loadErr  error
)

func load() {
	loadErr = json.Unmarshal(servicesJSON, &services)
}

// Load parses and returns the embedded catalog. It is memoized: the JSON is
// unmarshaled once and the same slice is returned on subsequent calls. An
// error here means the embedded services.json is malformed, which is a
// build/test-time condition, never a runtime one.
func Load() ([]Service, error) {
	loadOnce.Do(load)
	return services, loadErr
}

// Services returns the full embedded catalog. It panics if the embedded JSON
// is invalid — a guaranteed-at-build-time condition surfaced by the package's
// own tests.
func Services() []Service {
	svcs, err := Load()
	if err != nil {
		panic("catalog: embedded services.json is invalid: " + err.Error())
	}
	return svcs
}

// IsReadable reports whether the service exposes at least one GET operation,
// i.e. it can be read from without a write.
func (s Service) IsReadable() bool {
	for _, op := range s.Operations {
		if strings.EqualFold(op.Method, "GET") {
			return true
		}
	}
	return false
}

// Methods returns the distinct HTTP methods present on the service, in a
// stable canonical order (GET, POST, PATCH, PUT, DELETE, then any others
// alphabetically).
func (s Service) Methods() []string {
	seen := map[string]bool{}
	for _, op := range s.Operations {
		seen[strings.ToUpper(op.Method)] = true
	}

	var out []string
	for _, m := range canonicalMethodOrder {
		if seen[m] {
			out = append(out, m)
			delete(seen, m)
		}
	}
	var rest []string
	for m := range seen {
		rest = append(rest, m)
	}
	sort.Strings(rest)
	return append(out, rest...)
}

// Find returns the service whose name matches name case-insensitively, or
// false if there is no exact match.
func Find(name string) (Service, bool) {
	name = strings.TrimSpace(name)
	for _, s := range Services() {
		if strings.EqualFold(s.Service, name) {
			return s, true
		}
	}
	return Service{}, false
}

// Suggest returns up to max service names ranked by similarity to name, for
// "did you mean?" hints when Find misses. Case-insensitive substring matches
// rank first (closest length wins), then closest edit distance.
func Suggest(name string, max int) []string {
	q := strings.ToLower(strings.TrimSpace(name))
	if q == "" || max <= 0 {
		return nil
	}

	type cand struct {
		name  string
		score int
	}
	var cands []cand
	for _, s := range Services() {
		ln := strings.ToLower(s.Service)
		var score int
		if strings.Contains(ln, q) {
			// Substring match: the closer the lengths, the better.
			score = 1000 - (len(ln) - len(q))
		} else {
			score = 500 - levenshtein(q, ln)
		}
		cands = append(cands, cand{s.Service, score})
	}

	sort.SliceStable(cands, func(i, j int) bool {
		if cands[i].score != cands[j].score {
			return cands[i].score > cands[j].score
		}
		return cands[i].name < cands[j].name
	})

	if len(cands) > max {
		cands = cands[:max]
	}
	out := make([]string, len(cands))
	for i, c := range cands {
		out[i] = c.name
	}
	return out
}

// Stats is the aggregate summary printed by `catalog stats`.
type Stats struct {
	Services   int            `json:"services"`
	Operations int            `json:"operations"`
	ByMethod   map[string]int `json:"by_method"`
	Readable   int            `json:"readable"`
}

// ComputeStats walks the catalog and returns totals: number of services, total
// operations, per-method breakdown, and how many services are readable (have a
// GET).
func ComputeStats() Stats {
	st := Stats{ByMethod: map[string]int{}}
	for _, s := range Services() {
		st.Services++
		if s.IsReadable() {
			st.Readable++
		}
		for _, op := range s.Operations {
			st.Operations++
			st.ByMethod[strings.ToUpper(op.Method)]++
		}
	}
	return st
}

// MethodOrder returns the canonical HTTP-method display order, so callers can
// print a per-method breakdown deterministically.
func MethodOrder() []string {
	return append([]string(nil), canonicalMethodOrder...)
}

// levenshtein is the classic edit distance between two strings, used only to
// rank fuzzy suggestions.
func levenshtein(a, b string) int {
	ra, rb := []rune(a), []rune(b)
	la, lb := len(ra), len(rb)
	if la == 0 {
		return lb
	}
	if lb == 0 {
		return la
	}

	prev := make([]int, lb+1)
	curr := make([]int, lb+1)
	for j := 0; j <= lb; j++ {
		prev[j] = j
	}
	for i := 1; i <= la; i++ {
		curr[0] = i
		for j := 1; j <= lb; j++ {
			cost := 1
			if ra[i-1] == rb[j-1] {
				cost = 0
			}
			curr[j] = min3(curr[j-1]+1, prev[j]+1, prev[j-1]+cost)
		}
		prev, curr = curr, prev
	}
	return prev[lb]
}

func min3(a, b, c int) int {
	m := a
	if b < m {
		m = b
	}
	if c < m {
		m = c
	}
	return m
}
