package engine

import (
	"bufio"
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Auth modes. These tell the recipient the truth about what a baked credential
// actually does, and the README branches on them. Baking a .env that a binary
// never reads and calling it "works out of the box" is the silent failure this
// repo's lessons document.
const (
	// AuthBakedEnv — credentials are in place and the tool reads them.
	AuthBakedEnv = "baked-env"
	// AuthLogin — credentials ship for reference; the recipient runs `auth login`.
	AuthLogin = "auth-login"
	// AuthHomeConfig — a config file must be copied into the home directory.
	AuthHomeConfig = "home-config-install"
	// AuthExternalToken — no useful credential can ship at all.
	AuthExternalToken = "external-token"
	// AuthUnconfigured — this component has no row in envPlan, so nobody has
	// decided what its credentials do. It is never a valid bundle input: the
	// build fails loud rather than guessing, and the UI shows it as unknown.
	// Defaulting to baked-env here would promise "ready on arrival" for a
	// component whose credential story has never been written down.
	AuthUnconfigured = "unconfigured"
)

// envCopy is a live credential file copied verbatim into the bundle.
type envCopy struct {
	src      string      // repo-relative, or ~/-prefixed for out-of-repo files
	dst      string      // path inside the bundle
	mode     os.FileMode //
	targets  []string    // empty means every target
	optional bool        // missing source is a warning, not an error
	note     string      // extra context for the warning when it is missing
}

// extraFile is a non-credential file a component needs that the manifest does
// not list under its own tools (product-identity, the hana-sql example query).
type extraFile struct {
	src string
	dst string
}

// envSpec is one row of PLAN.md §5 — how a component gets its credentials.
type envSpec struct {
	authMode  string
	authNote  string   // the honest one-liner shown in the README under the mode
	sensitive bool     // shown in the API so the operator knows to be careful
	prefixes  []string // keys lifted out of the repo-root .env
	copies    []envCopy
	extras    []extraFile
	runDir    string // where the recipient must cd before running, "" = bundle root
	// runDirByTarget overrides runDir per target. sap-b1 needs it: the Mac
	// binary and its .env live in sap-b1/cli, the Windows exe and its .env in
	// sap-b1/accounts-kit, and the tool reads .env from the current directory —
	// so a single path sends one of the two recipients to an empty folder.
	runDirByTarget map[string]string
}

// productIdentityFiles is the hash-pinned identity bundle. It must be copied
// byte-for-byte: release-attestation.json's digest is checked at runtime, and a
// single re-encoded or CRLF-translated byte makes every `product` command fail
// closed with exit 6.
var productIdentityFiles = []string{
	"product-identity/v1/product-identity-map.json",
	"product-identity/v1/release-attestation.json",
	"product-identity/v1/review-decisions.json",
	"product-identity/v1/sources/ecom-master-products.json",
	"product-identity/v1/sources/factory-catalogs.json",
	"product-identity/v1/sources/jid-registry.json",
	"product-identity/v1/sources/pricematch-master-v2.json",
	"product-identity/v1/sources/pricematch-sku-map.json",
	"product-identity/v1/sources/source-manifest.json",
}

func productIdentityExtras() []extraFile {
	out := make([]extraFile, 0, len(productIdentityFiles))
	for _, p := range productIdentityFiles {
		out = append(out, extraFile{src: p, dst: p})
	}
	return out
}

// envPlan is PLAN.md §5, in code. Every component that ships a credential
// appears here; anything not listed ships no credential at all.
var envPlan = map[string]envSpec{
	"sap-b1": {
		authMode: AuthBakedEnv,
		authNote: "The SAP login is already in the .env next to the tool. Run it from that folder — the CLI only reads .env from the current directory.",
		runDir:   "sap-b1/cli",
		runDirByTarget: map[string]string{
			"windows": "sap-b1/accounts-kit",
		},
		copies: []envCopy{
			{src: "sap-b1/cli/.env", dst: "sap-b1/cli/.env", mode: 0o600, targets: []string{"mac-arm64"}},
			{src: "sap-b1/accounts-kit/.env", dst: "sap-b1/accounts-kit/.env", mode: 0o600, targets: []string{"windows"}},
		},
	},
	"hana-sql": {
		authMode: AuthBakedEnv,
		authNote: "Both connection variants ship: connections/hana.env (direct, office network) and connections/hana-tunnel.env (from home, through the tunnel). hana-sql walks UP from wherever you run it to find connections/hana.env — so keep the folder layout, and to use the tunnel variant copy it over connections/hana.env.",
		copies: []envCopy{
			{src: "connections/hana.env", dst: "connections/hana.env", mode: 0o600},
			{src: "connections/hana-tunnel.env", dst: "connections/hana-tunnel.env", mode: 0o600},
		},
		extras: []extraFile{
			{src: "hana-sql/queries/turnover-oil-july.sql", dst: "hana-sql/queries/turnover-oil-july.sql"},
		},
	},
	"ecom-cli": {
		authMode: AuthLogin,
		authNote: "The binary does NOT read the bundled .env. The credentials are there for reference — run `auth login` once with them and the session is cached in your home directory.",
		prefixes: []string{"ECOM_", "JIVO_ECOM_"},
	},
	"exim": {
		authMode: AuthBakedEnv,
		authNote: "exim's Python layer walks up from exim/ and finds the bundle's root .env — nothing to configure.",
		prefixes: []string{"EXIM_", "EXIM_API", "EXIM_WEB"},
	},
	"factory-cli": {
		authMode: AuthLogin,
		authNote: "The binary does NOT read the bundled .env. Run `auth login` once with the credentials in the root .env.",
		prefixes: []string{"JIVO_FACTORY_"},
		extras:   productIdentityExtras(),
	},
	"oms-cli": {
		authMode: AuthLogin,
		authNote: "The binary does NOT read the bundled .env. Run `auth login` once with the credentials in the root .env.",
		prefixes: []string{"OMS_"},
	},
	"jsap-cli": {
		authMode: AuthBakedEnv,
		authNote: "jsap walks up from jsap-cli/jsap/ and finds the bundle's root .env — nothing to configure.",
		runDir:   "jsap-cli",
		prefixes: []string{"JSAP_"},
	},
	"postsql": {
		authMode: AuthHomeConfig,
		authNote: "postsql reads ONLY ~/.postsql/config.toml (or PG* environment variables) — the bundled copy is inert until you install it.",
		copies: []envCopy{
			{src: "~/.postsql/config.toml", dst: "postsql/config.toml.INSTALL", mode: 0o600, optional: true,
				note: "postsql will have no credentials until one is placed at ~/.postsql/config.toml"},
		},
	},
	"dsr-cli": {
		authMode: AuthBakedEnv,
		authNote: "dsr reads .env from the folder holding the binary.",
		runDir:   "dsr-cli",
	},
	"portals": {
		authMode:  AuthExternalToken,
		sensitive: true,
		authNote:  "Blinkit / Zepto / Amazon / Flipkart / Swiggy carry no usable credential: their sessions are minted by the token automation on Daman's Mac and expire on their own. This bundle gives read access only until the current session expires, and it cannot refresh itself. TankhaPay is the exception — its live login IS baked at portals/tankhapay/.env, and it is payroll data.",
		copies: []envCopy{
			{src: "portals/tankhapay/.env", dst: "portals/tankhapay/.env", mode: 0o600, optional: true,
				note: "portals/tankhapay/ is gitignored and exists only on Daman's Mac"},
		},
	},
	"control-panel": {
		authMode: AuthLogin,
		authNote: "The binary's compiled-in credential path is ~/software/.env, which this bundle does not create. Point it at the bundled file instead: `jivo auth login --env-file <unzip>/control-panel/.env`.",
		copies: []envCopy{
			{src: "control-panel/.env", dst: "control-panel/.env", mode: 0o600},
		},
	},
	"jivo-scraping-cli": {
		authMode: AuthBakedEnv,
		authNote: "No credentials are needed or shipped: the `product` commands are fully offline against the bundled product-identity files. The data commands need JIVO_SCRAPE_ROOT pointing at an ecom-intel checkout, which is not part of this bundle.",
		extras:   productIdentityExtras(),
	},
}

// HasEnvPlan reports whether PLAN.md §5 has a row for this component. A new
// component in manifest.json without one is a gap, not a default.
func HasEnvPlan(component string) bool {
	_, ok := envPlan[component]
	return ok
}

// AuthMode returns the auth story for a component, or AuthUnconfigured when
// nobody has written one down. It never guesses baked-env: that would tell a
// recipient their credentials are ready when no one has checked.
func AuthMode(component string) string {
	if s, ok := envPlan[component]; ok {
		return s.authMode
	}
	return AuthUnconfigured
}

// Sensitive reports whether a component carries data that needs an extra
// thought before sending (payroll).
func Sensitive(component string) bool {
	return envPlan[component].sensitive
}

// AuthNote is the plain-language explanation shown under the auth mode.
func AuthNote(component string) string {
	if s, ok := envPlan[component]; ok {
		return s.authNote
	}
	return "No credential plan has been written for this component yet — it cannot be bundled. " +
		"Add a row to envPlan in internal/engine/envbake.go (see PLAN.md §5)."
}

// RunDir is the directory the recipient must cd into first, if any. It is
// per-target because a component's binary and its credentials do not
// necessarily live in the same folder on both platforms.
func RunDir(component, target string) string {
	spec := envPlan[component]
	if dir, ok := spec.runDirByTarget[target]; ok {
		return dir
	}
	return spec.runDir
}

// resolveSrc turns an envPlan source into an absolute path. `~/` sources live
// outside the repo (postsql's config.toml) and use the caller-supplied home
// directory so tests can point it at a fixture.
func resolveSrc(repoRoot, homeDir, src string) string {
	if strings.HasPrefix(src, "~/") {
		return filepath.Join(homeDir, strings.TrimPrefix(src, "~/"))
	}
	return filepath.Join(repoRoot, src)
}

func appliesToTarget(targets []string, target string) bool {
	if len(targets) == 0 {
		return true
	}
	for _, t := range targets {
		if t == target {
			return true
		}
	}
	return false
}

// ---------------------------------------------------------------- root .env

// envLine is one KEY=VALUE line lifted out of a source .env. Values are never
// logged; they exist only to be written into the bundle.
type envLine struct {
	key string
	raw string
}

// parseEnvKeys reads KEY=VALUE lines from a .env file. Comments and blanks are
// dropped: the bundle's root .env is regenerated with its own header, and a
// stray comment from the source could carry a credential for a component the
// recipient did not ask for.
func parseEnvKeys(path string) ([]envLine, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var out []envLine
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
	for sc.Scan() {
		line := strings.TrimRight(sc.Text(), "\r")
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}
		trimmed = strings.TrimPrefix(trimmed, "export ")
		eq := strings.Index(trimmed, "=")
		if eq <= 0 {
			continue
		}
		key := strings.TrimSpace(trimmed[:eq])
		if key == "" {
			continue
		}
		out = append(out, envLine{key: key, raw: trimmed})
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

// prefixesFor collects the root-.env key prefixes the selected components need.
// A jsap-only bundle must not carry OMS or SAP credentials, so this is an
// allowlist and nothing else is copied.
func prefixesFor(components []string) []string {
	seen := map[string]bool{}
	var out []string
	for _, c := range components {
		for _, p := range envPlan[c].prefixes {
			if !seen[p] {
				seen[p] = true
				out = append(out, p)
			}
		}
	}
	sort.Strings(out)
	return out
}

// BakeRootEnv builds the bundle's root .env from the repo-root .env, keeping
// only keys whose prefix belongs to a selected component. Returns nil content
// when no selected component needs it.
func BakeRootEnv(repoRoot string, components []string, target string) (content []byte, warnings []string, err error) {
	prefixes := prefixesFor(components)
	if len(prefixes) == 0 {
		return nil, nil, nil
	}

	srcPath := filepath.Join(repoRoot, ".env")
	lines, err := parseEnvKeys(srcPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, []string{"repo-root .env not found — no shared credentials were baked into the bundle's .env"}, nil
		}
		return nil, nil, fmt.Errorf("root .env: %w", err)
	}

	var kept []envLine
	keptKeys := map[string]bool{}
	for _, l := range lines {
		for _, p := range prefixes {
			if strings.HasPrefix(l.key, p) {
				kept = append(kept, l)
				keptKeys[l.key] = true
				break
			}
		}
	}

	var buf bytes.Buffer
	buf.WriteString("# JIVO kit — credentials for the tools in this bundle.\n")
	buf.WriteString("# Generated by the bundle builder; only the keys the included tools need are here.\n")
	buf.WriteString("# LIVE CREDENTIALS. Do not forward this file, copy it elsewhere, or commit it.\n")
	for _, c := range sortedStrings(components) {
		if len(envPlan[c].prefixes) == 0 {
			continue
		}
		fmt.Fprintf(&buf, "# %s: %s\n", c, strings.Join(envPlan[c].prefixes, " "))
	}
	buf.WriteString("\n")
	for _, l := range kept {
		buf.WriteString(l.raw)
		buf.WriteString("\n")
	}

	// Hard requirements the lessons call out by name.
	for _, c := range components {
		if c != "exim" {
			continue
		}
		for _, need := range []string{"EXIM_API", "EXIM_WEB"} {
			if !keptKeys[need] {
				warnings = append(warnings, fmt.Sprintf(
					"exim: %s is missing from the repo-root .env — eximapi.py raises a KeyError on it at import time, so exim will not run in this bundle", need))
			}
		}
	}
	if len(kept) == 0 {
		warnings = append(warnings, "no matching keys were found in the repo-root .env — the bundle's .env is empty")
	}
	return buf.Bytes(), warnings, nil
}

// ------------------------------------------------------------------- dsr

// dsrKeys are the variables dsr-cli/internal/config expects.
var dsrKeys = []string{
	"DSR_HOST", "DSR_PORT", "DSR_DATABASE", "DSR_ENCRYPT",
	"DSR_USER", "DSR_PASSWORD", "DSR_PORTAL_URL",
}

// BakeDSREnv generates dsr-cli/.env from distribution/secrets.local.env, which
// is gitignored and operator-maintained because no DSR credential exists
// anywhere in the repo or the env vault. With no source, it degrades to a blank
// template plus a loud warning — it never invents values.
func BakeDSREnv(repoRoot string) (content []byte, warnings []string) {
	secrets := filepath.Join(repoRoot, "distribution", "secrets.local.env")
	values := map[string]string{}
	if lines, err := parseEnvKeys(secrets); err == nil {
		for _, l := range lines {
			if strings.HasPrefix(l.key, "DSR_") {
				values[l.key] = l.raw
			}
		}
	}

	var buf bytes.Buffer
	buf.WriteString("# JIVO kit — DSR field-sales portal credentials.\n")
	if len(values) == 0 {
		buf.WriteString("# TEMPLATE ONLY — no DSR credentials were available when this bundle was built.\n")
		buf.WriteString("# Fill these in (ask Daman) before running dsr, and keep this file chmod 600.\n")
		warnings = append(warnings, "dsr-cli: DSR_* keys not found in distribution/secrets.local.env — shipped a blank template, dsr will not connect until it is filled in")
	} else {
		buf.WriteString("# LIVE CREDENTIALS. Do not forward this file or copy it elsewhere.\n")
	}
	buf.WriteString("\n")
	for _, k := range dsrKeys {
		if raw, ok := values[k]; ok {
			buf.WriteString(raw)
		} else {
			buf.WriteString(k + "=")
		}
		buf.WriteString("\n")
	}
	// Anything else DSR_* the operator recorded travels too.
	var extra []string
	for k := range values {
		if !containsString(dsrKeys, k) {
			extra = append(extra, k)
		}
	}
	sort.Strings(extra)
	for _, k := range extra {
		buf.WriteString(values[k])
		buf.WriteString("\n")
	}
	return buf.Bytes(), warnings
}

// eximSecretsPlaceholder keeps exim/.secrets/ alive in the zip. Empty
// directories vanish from an archive and eximapi.py never creates the folder,
// so its first token write would fail.
const eximSecretsPlaceholder = `This folder must exist before exim runs.

exim caches its login token here as token.json. The bundle deliberately does
NOT ship a token: tokens are short-lived and tied to the machine that minted
them. On first use exim logs in with the credentials in the bundle's root .env
and writes token.json next to this file.

Do not copy a token.json from another machine into this folder.
`

func containsString(xs []string, s string) bool {
	for _, x := range xs {
		if x == s {
			return true
		}
	}
	return false
}

func sortedStrings(xs []string) []string {
	out := append([]string(nil), xs...)
	sort.Strings(out)
	return out
}
