package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Registration is one GST registration of JIVO Wellness Pvt Ltd: one state, one
// GSTIN, one portal login. There are 8 (LOGIN-STATUS.md). Every command runs
// against one at a time — the portal has no cross-registration view.
type Registration struct {
	Idx   string // the .env block number, "01".."08"
	State string
	GSTIN string
	User  string
	Pass  string
}

// StateCode is the first two digits of the GSTIN (06 = Haryana, 09 = UP, …).
func (r Registration) StateCode() string {
	if len(r.GSTIN) >= 2 {
		return r.GSTIN[:2]
	}
	return ""
}

// summary is the `auth list` line. Credentials are ALWAYS masked here; nothing
// in this binary prints a password whole.
func (r Registration) summary() string {
	return fmt.Sprintf("%s  %-20s %s  user=%s  pass=%s",
		r.Idx, r.State, r.GSTIN, masked(r.User), maskedSecret(r.Pass))
}

// envSuffixes are the four keys every GST_NN_ block must carry.
var envSuffixes = []string{"STATE", "GSTIN", "USER", "PASS"}

// loadRegistrations builds the registration list from the environment and the
// .env file. Precedence is the house rule — env var beats .env (there is
// deliberately no --password flag anywhere in this CLI).
func loadRegistrations() ([]Registration, error) {
	// An explicit $GST_ENV is an instruction, not a hint: if it names a file we
	// cannot read, say so instead of quietly falling back to some other .env.
	if p := os.Getenv("GST_ENV"); p != "" {
		if _, err := os.Stat(p); err != nil {
			return nil, errConfig("$GST_ENV points at %s, which cannot be read: %v", p, err)
		}
	}
	file := loadDotenvBestEffort()
	get := func(k string) string {
		if v := os.Getenv(k); v != "" {
			return v
		}
		return file[k]
	}

	// Which block numbers exist at all? A block "exists" if any of its four keys
	// is set, so a half-filled block is reported rather than silently dropped.
	seen := map[string]bool{}
	for _, src := range []map[string]string{file, envKeys()} {
		for k := range src {
			if idx, ok := blockIndex(k); ok {
				seen[idx] = true
			}
		}
	}
	idxs := make([]string, 0, len(seen))
	for i := range seen {
		idxs = append(idxs, i)
	}
	sort.Strings(idxs)

	var regs []Registration
	var missing []string
	for _, idx := range idxs {
		vals := map[string]string{}
		for _, s := range envSuffixes {
			key := "GST_" + idx + "_" + s
			v := strings.TrimSpace(get(key))
			if v == "" {
				missing = append(missing, key)
			}
			vals[s] = v
		}
		regs = append(regs, Registration{
			Idx:   idx,
			State: vals["STATE"],
			GSTIN: strings.ToUpper(vals["GSTIN"]),
			User:  vals["USER"],
			Pass:  vals["PASS"],
		})
	}
	if len(missing) > 0 {
		return nil, errConfig("incomplete GST registration block(s) — set: %s (in %s or the environment)",
			strings.Join(missing, ", "), dotenvFoundAt())
	}
	if len(regs) == 0 {
		return nil, errConfig("no GST registrations configured: expected GST_01_STATE/GSTIN/USER/PASS … in a .env (searched: %s). Copy portals/gst/.env.example and fill it from env-vault.",
			strings.Join(dotenvSearchPaths(), ", "))
	}
	return regs, nil
}

// blockIndex reports the NN of a GST_NN_<SUFFIX> key.
func blockIndex(k string) (string, bool) {
	if !strings.HasPrefix(k, "GST_") {
		return "", false
	}
	rest := strings.TrimPrefix(k, "GST_")
	i := strings.IndexByte(rest, '_')
	if i <= 0 {
		return "", false
	}
	idx, suffix := rest[:i], rest[i+1:]
	for _, c := range idx {
		if c < '0' || c > '9' {
			return "", false
		}
	}
	for _, s := range envSuffixes {
		if suffix == s {
			return idx, true
		}
	}
	return "", false
}

// envKeys snapshots the GST_* environment variables as a map.
func envKeys() map[string]string {
	out := map[string]string{}
	for _, kv := range os.Environ() {
		if i := strings.IndexByte(kv, '='); i > 0 && strings.HasPrefix(kv, "GST_") {
			out[kv[:i]] = kv[i+1:]
		}
	}
	return out
}

// ---- selection ------------------------------------------------------------

// selectRegistrations resolves --gstin / --state / --all (and the GST_DEFAULT
// fallback) to the registrations a command should run against. It never guesses:
// no selector, or an ambiguous one, is a usage error that lists the options.
func selectRegistrations(regs []Registration, gstin, state, deflt string, all bool) ([]Registration, error) {
	if all {
		return regs, nil
	}
	if g := strings.ToUpper(strings.TrimSpace(gstin)); g != "" {
		for _, r := range regs {
			if r.GSTIN == g {
				return []Registration{r}, nil
			}
		}
		return nil, errUsage("no registration with GSTIN %s is configured.\n%s", g, listOf(regs))
	}
	if s := strings.TrimSpace(state); s != "" {
		return matchState(regs, s)
	}
	if d := strings.TrimSpace(deflt); d != "" {
		if hit, err := matchState(regs, d); err == nil {
			return hit, nil
		}
		for _, r := range regs {
			if r.GSTIN == strings.ToUpper(d) {
				return []Registration{r}, nil
			}
		}
		return nil, errUsage("GST_DEFAULT=%q does not name a configured registration.\n%s", d, listOf(regs))
	}
	return nil, errUsage("pick a registration: --gstin <GSTIN>, --state <name|code>, or --all.\n%s", listOf(regs))
}

// stateAbbrev maps the two-letter shorthand Accounts actually types.
var stateAbbrev = map[string]string{
	"hr": "haryana", "rj": "rajasthan", "pb": "punjab", "dl": "delhi",
	"hp": "himachalpradesh", "up": "uttarpradesh", "mh": "maharashtra",
	"gj": "gujarat", "ka": "karnataka", "tn": "tamilnadu", "wb": "westbengal",
}

// matchState resolves a --state value in a fixed order: exact state name, then
// two-letter abbreviation, then GSTIN state code, then a unique name prefix.
// Two hits at the same level is an error naming both (07 = Delhi AND Delhi ISD).
func matchState(regs []Registration, sel string) ([]Registration, error) {
	n := normaliseState(sel)
	if full, ok := stateAbbrev[n]; ok {
		n = full
	}

	var exact, code, prefix []Registration
	for _, r := range regs {
		rn := normaliseState(r.State)
		switch {
		case rn == n:
			exact = append(exact, r)
		case r.StateCode() == n:
			code = append(code, r)
		case strings.HasPrefix(rn, n):
			prefix = append(prefix, r)
		}
	}
	for _, tier := range [][]Registration{exact, code, prefix} {
		switch len(tier) {
		case 0:
			continue
		case 1:
			return tier, nil
		default:
			return nil, errUsage("--state %q is ambiguous — it matches %s. Use --gstin to pick one.",
				sel, strings.Join(gstinList(tier), " and "))
		}
	}
	return nil, errUsage("no registration matches --state %q.\n%s", sel, listOf(regs))
}

// normaliseState lowercases and drops everything that is not a letter or digit,
// so "Delhi ISD", "delhi-isd" and "DelhiISD" are the same selector.
func normaliseState(s string) string {
	var b strings.Builder
	for _, c := range strings.ToLower(s) {
		if (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') {
			b.WriteRune(c)
		}
	}
	return b.String()
}

func gstinList(rs []Registration) []string {
	out := make([]string, 0, len(rs))
	for _, r := range rs {
		out = append(out, r.GSTIN)
	}
	return out
}

// listOf renders the configured registrations for an error message. Credentials
// are not part of it.
func listOf(regs []Registration) string {
	var b strings.Builder
	b.WriteString("configured registrations:")
	for _, r := range regs {
		fmt.Fprintf(&b, "\n  %s  %-20s %s", r.Idx, r.State, r.GSTIN)
	}
	return b.String()
}

// ---- .env loading ---------------------------------------------------------

// dotenvSearchPaths returns candidate .env locations, most specific first
// (house order: $GST_ENV → ./ → ../ → exe dir → exe dir/.. → ~/jivo-cli/...).
func dotenvSearchPaths() []string {
	var paths []string
	if p := os.Getenv("GST_ENV"); p != "" {
		paths = append(paths, p)
	}
	if wd, err := os.Getwd(); err == nil {
		paths = append(paths, filepath.Join(wd, ".env"), filepath.Join(wd, "..", ".env"))
	}
	if exe, err := os.Executable(); err == nil {
		d := filepath.Dir(exe)
		paths = append(paths, filepath.Join(d, ".env"), filepath.Join(d, "..", ".env"))
	}
	if home, err := os.UserHomeDir(); err == nil {
		paths = append(paths, filepath.Join(home, "jivo-cli", "portals", "gst", ".env"))
	}
	return paths
}

// dotenvFoundAt names the file the values came from, for error messages.
func dotenvFoundAt() string {
	for _, p := range dotenvSearchPaths() {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return "the .env"
}

// loadDotenvBestEffort parses the first .env found. Never errors: a missing file
// just yields an empty map (environment variables may supply everything).
func loadDotenvBestEffort() map[string]string {
	out := map[string]string{}
	for _, p := range dotenvSearchPaths() {
		f, err := os.Open(p)
		if err != nil {
			continue
		}
		sc := bufio.NewScanner(f)
		for sc.Scan() {
			line := strings.TrimSpace(sc.Text())
			if line == "" || strings.HasPrefix(line, "#") {
				continue
			}
			line = strings.TrimPrefix(line, "export ")
			eq := strings.IndexByte(line, '=')
			if eq < 0 {
				continue
			}
			k := strings.TrimSpace(line[:eq])
			v := strings.TrimSpace(line[eq+1:])
			v = strings.Trim(v, `"'`)
			out[k] = v
		}
		f.Close()
		if len(out) > 0 {
			break
		}
	}
	return out
}
