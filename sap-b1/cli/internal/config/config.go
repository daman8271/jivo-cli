// Package config loads SAP B1 Service Layer connection settings.
//
// Precedence (highest wins): CLI flag > environment variable > .env file > built-in default.
// The password is never logged, printed, or written anywhere by this package.
package config

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/joho/godotenv"

	"sapb1/internal/errs"
)

// Config holds everything needed to talk to a SAP B1 Service Layer instance.
type Config struct {
	Host      string
	Port      int
	CompanyDB string
	User      string
	Password  string
	Insecure  bool
	Timeout   int // seconds
	// TimeoutSet records whether Timeout came from the operator (--timeout or
	// SAPB1_TIMEOUT) rather than the built-in default. Writes use a longer
	// default than reads, but never override an explicit choice.
	TimeoutSet bool
	JSON       bool
	CSV        bool
}

// Defaults.
const (
	DefaultPort = 50000
	// DefaultTimeout is the read timeout. Reads are cheap to retry, so a short
	// timeout is a feature.
	DefaultTimeout = 30
	// DefaultWriteTimeout is the default for POST/PATCH. It is deliberately much
	// longer than DefaultTimeout: a write that times out client-side may still
	// commit in SAP, which leaves the operator with an unknown outcome. Waiting
	// two minutes for SAP's answer is far better than not knowing.
	DefaultWriteTimeout = 120
)

// Flags captures the values the caller pulled from CLI flags (global persistent
// flags on the root command). A flag is only applied if Changed is true, so an
// unset flag never clobbers an env var or .env value with a zero value.
type Flags struct {
	Host        string
	HostSet     bool
	Port        int
	PortSet     bool
	Company     string
	CompanySet  bool
	User        string
	UserSet     bool
	Insecure    bool
	InsecureSet bool
	Timeout     int
	TimeoutSet  bool
	JSON        bool
	CSV         bool
}

// Load builds a Config by layering: built-in defaults, then .env file (if present),
// then real process environment variables, then explicit CLI flags.
//
// It does not fail if CompanyDB, User, or Password are blank — callers that need
// those must check and produce a clear, actionable error (see Validate helpers).
func Load(f Flags) (*Config, error) {
	// Load .env from the current directory if present. godotenv.Load does NOT
	// override variables already set in the real process environment, which is
	// the precedence we want (env var > .env file).
	_ = godotenv.Load()

	cfg := &Config{
		Host:      os.Getenv("SAPB1_HOST"),
		Port:      DefaultPort,
		CompanyDB: os.Getenv("SAPB1_COMPANYDB"),
		User:      os.Getenv("SAPB1_USER"),
		Password:  os.Getenv("SAPB1_PASSWORD"),
		Insecure:  false,
		Timeout:   DefaultTimeout,
	}

	if v := os.Getenv("SAPB1_PORT"); v != "" {
		if p, err := strconv.Atoi(v); err == nil {
			cfg.Port = p
		} else {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf("invalid SAPB1_PORT %q: must be a number", v)}
		}
	}

	if v := os.Getenv("SAPB1_INSECURE"); v != "" {
		b, err := strconv.ParseBool(v)
		if err != nil {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf("invalid SAPB1_INSECURE %q: must be true/false", v)}
		}
		cfg.Insecure = b
	}

	if v := os.Getenv("SAPB1_TIMEOUT"); v != "" {
		if t, err := strconv.Atoi(v); err == nil {
			cfg.Timeout = t
			cfg.TimeoutSet = true
		} else {
			return nil, &errs.ConfigError{Msg: fmt.Sprintf("invalid SAPB1_TIMEOUT %q: must be a number of seconds", v)}
		}
	}

	// Flags win over everything else, but only if explicitly set.
	if f.HostSet {
		cfg.Host = f.Host
	}
	if f.PortSet {
		cfg.Port = f.Port
	}
	if f.CompanySet {
		cfg.CompanyDB = f.Company
	}
	if f.UserSet {
		cfg.User = f.User
	}
	if f.InsecureSet {
		cfg.Insecure = f.Insecure
	}
	if f.TimeoutSet {
		cfg.Timeout = f.Timeout
		cfg.TimeoutSet = true
	}
	cfg.JSON = f.JSON
	cfg.CSV = f.CSV

	cfg.Host = strings.TrimSpace(cfg.Host)
	cfg.CompanyDB = strings.TrimSpace(cfg.CompanyDB)
	cfg.User = strings.TrimSpace(cfg.User)

	return cfg, nil
}

// BaseURL returns the Service Layer root, e.g. https://host:50000/b1s/v1/.
func (c *Config) BaseURL() string {
	return fmt.Sprintf("https://%s:%d/b1s/v1/", c.Host, c.Port)
}

// WriteTimeout returns the timeout (seconds) to use for POST/PATCH. An explicit
// --timeout/SAPB1_TIMEOUT always wins; otherwise writes get
// DefaultWriteTimeout instead of the shorter read default.
func (c *Config) WriteTimeout() int {
	if c.TimeoutSet {
		return c.Timeout
	}
	if c.Timeout > DefaultWriteTimeout {
		return c.Timeout
	}
	return DefaultWriteTimeout
}

// HostPort returns "host:port" for use in network-reachability messages.
func (c *Config) HostPort() string {
	return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

// MaskedPassword returns a fixed mask if a password is set, or "(not set)".
// It never returns the real password.
func (c *Config) MaskedPassword() string {
	if c.Password == "" {
		return "(not set)"
	}
	return "****"
}

// ValidateConnection checks that the fields required to make ANY request
// (host, user, password) are present. CompanyDB is checked separately since
// some commands (like `doctor` prior to login) can still report partial status.
func (c *Config) ValidateConnection() error {
	var missing []string
	if c.Host == "" {
		missing = append(missing, "SAPB1_HOST")
	}
	if c.User == "" {
		missing = append(missing, "SAPB1_USER")
	}
	if c.Password == "" {
		missing = append(missing, "SAPB1_PASSWORD")
	}
	if len(missing) > 0 {
		return &errs.ConfigError{Msg: fmt.Sprintf("missing required config: %s — set them in .env or pass the matching flag", strings.Join(missing, ", "))}
	}
	return nil
}

// ValidateCompanyDB checks CompanyDB is set, with the exact guidance requested
// for this project.
func (c *Config) ValidateCompanyDB() error {
	if c.CompanyDB == "" {
		return &errs.ConfigError{Msg: "company database not set — set SAPB1_COMPANYDB in .env or pass --company. Ask your SAP admin for the CompanyDB name"}
	}
	return nil
}

// SessionCachePathFor returns the session-cache file for ONE connection
// identity: ~/.sapb1-session-<companydb-slug>-<hash of host:port:user>.json.
//
// Why per identity rather than one shared file: a Service Layer session is
// scoped to the CompanyDB it logged into, so Oil, Mart and Beverages need
// three different sessions. With a single file they overwrite each other, and
// alternating companies (exactly what a "compare Mart vs Beverages" workflow
// does) forces a fresh POST /Login on every switch — SAP B1 sessions are a
// finite, ~30-minute-lived resource, so that is a login storm.
//
// The CompanyDB is kept readable in the filename (it is not a secret and makes
// the files self-explaining); host, port and user are folded into a short hash
// so the name stays bounded and no username lands in a filename.
func SessionCachePathFor(host string, port int, companyDB, user string) (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("cannot determine home directory: %w", err)
	}
	id := fmt.Sprintf("%s:%d:%s", host, port, user)
	sum := sha256.Sum256([]byte(id))
	name := fmt.Sprintf(".sapb1-session-%s-%s.json", slugify(companyDB), hex.EncodeToString(sum[:4]))
	return filepath.Join(home, name), nil
}

// slugify reduces an arbitrary CompanyDB name to a safe, lower-case filename
// fragment. Any run of non-alphanumeric characters collapses to a single "-";
// an empty or fully-stripped name becomes "none" so the path is never
// ambiguous.
func slugify(s string) string {
	var b strings.Builder
	lastDash := false
	for _, r := range strings.ToLower(strings.TrimSpace(s)) {
		switch {
		case (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9'):
			b.WriteRune(r)
			lastDash = false
		default:
			if !lastDash && b.Len() > 0 {
				b.WriteByte('-')
				lastDash = true
			}
		}
	}
	out := strings.Trim(b.String(), "-")
	if out == "" {
		return "none"
	}
	return out
}

// WriteLogPath returns the append-only audit log every write command records to.
//
// Precedence: $SAPB1_WRITE_LOG > this operator's folder inside the JIVO repo >
// ~/.sapb1-writes.jsonl.
//
// The repo default is the important one. A write log that only ever lands in
// the operator's home directory is an audit trail nobody audits: the person who
// made the write is the only person who can read it. Inside the repo it sits in
// `queries/<operator>/sap-writes.jsonl`, which is committed and pushed with the
// rest of their session log — so every write attempt, by every operator, on
// every machine, converges into one shared history. Home is kept only as the
// fallback for a binary running outside a registered checkout.
func WriteLogPath() (string, error) {
	if p := strings.TrimSpace(os.Getenv("SAPB1_WRITE_LOG")); p != "" {
		return p, nil
	}
	if p := operatorWriteLog(); p != "" {
		return p, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("cannot determine home directory: %w", err)
	}
	return filepath.Join(home, ".sapb1-writes.jsonl"), nil
}

// SharedWriteLogPath returns this operator's log INSIDE the checkout — the file
// the fleet commits and everybody else reads — or "" when this binary is not
// running in a registered checkout.
//
// Unlike WriteLogPath it ignores $SAPB1_WRITE_LOG on purpose. That variable is
// how a wrapper script or a test redirects its own writes, and for a POST that
// is harmless: the object still exists in SAP and can be queried for. A DELETE
// has no such fallback — divert its record and the only trace that fifty drafts
// were destroyed sits in /tmp on one machine. So the delete path writes here as
// well, and "one shared history" stops depending on an environment variable
// being unset.
func SharedWriteLogPath() string {
	return operatorWriteLog()
}

// SnapshotLogPath returns the file a delete's SNAPSHOT — the contents of the
// draft it is about to destroy — is written to.
//
// Deliberately NOT the write log, and deliberately NOT inside the checkout. The
// write log is designed to be committed (see WriteLogPath) and this repo is
// public; a snapshot carries the vendor's name, their bill number, the totals
// and every line item with its price. The committed line keeps the sha256 of
// the snapshot, so the trail is still verifiable and still points at a record
// that exists — it just doesn't publish the contents of somebody's invoice.
//
// $SAPB1_SNAPSHOT_LOG redirects it (tests, or an operator who keeps this
// somewhere backed up).
func SnapshotLogPath() (string, error) {
	if p := strings.TrimSpace(os.Getenv("SAPB1_SNAPSHOT_LOG")); p != "" {
		return p, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("cannot determine home directory: %w", err)
	}
	return filepath.Join(home, ".sapb1-delete-snapshots.jsonl"), nil
}

// RepoRoot returns the root of the JIVO checkout this binary belongs to, or ""
// when there isn't one. It also returns a note the caller should show the
// operator: non-empty only when something about the answer deserves saying out
// loud.
//
// A root must contain BOTH `harness/` and `.git/`. That pair is the difference
// between a real checkout and a scratch directory somebody unzipped — and a
// month-old Drive zip (which has no `.git/`) correctly fails the test, so its
// operator is told "no write log found" and has to use the recorded override
// rather than silently deleting on a stale, incomplete history.
//
// The EXE's directory is tried before the working directory, and $SAPB1_WRITE_LOG
// is deliberately not a seed. This function chooses which evidence corpus a
// delete may be authorised against; letting one environment variable point it at
// a directory of the caller's choosing would let a planted tree skip the
// override marker entirely. (The env var names one more candidate LOG file, but
// it is read as evidence only when the file RESOLVES inside this root's
// queries/ tree — it never gets to pick the root itself.)
//
// When exe-root and cwd-root both resolve and disagree, the exe's wins and the
// note names both: that divergence is the stale-kit smell this fleet keeps
// hitting, and it is worth one line on stderr.
//
// "Disagree" means a different DIRECTORY, not a different string — see
// sameDirectory. The exe path is symlink-resolved and os.Getwd is not (it
// honours $PWD, the logical path the shell was given), so one checkout reached
// through a symlink used to look like two: on macOS, standing in /tmp/kit while
// the binary resolves to /private/tmp/kit fired the stale-copy warning every
// single run. An alarm that cries wolf is an alarm nobody reads, and this one
// exists to catch an operator running a month-old Drive zip.
func RepoRoot() (root string, note string) {
	exeRoot := ""
	if exe, err := executablePath(); err == nil {
		if resolved, err := filepath.EvalSymlinks(exe); err == nil {
			exe = resolved
		}
		exeRoot = walkUpToRepoRoot(filepath.Dir(exe))
	}
	cwdRoot := ""
	if cwd, err := os.Getwd(); err == nil {
		cwdRoot = walkUpToRepoRoot(cwd)
	}

	switch {
	case exeRoot != "" && cwdRoot != "" && !sameDirectory(exeRoot, cwdRoot):
		return exeRoot, fmt.Sprintf(
			"note: this sapb1 lives in the checkout at %s but you are standing in %s — using the binary's checkout for write-log evidence. One of the two is probably a stale copy",
			exeRoot, cwdRoot)
	case exeRoot != "":
		return exeRoot, ""
	default:
		return cwdRoot, ""
	}
}

// executablePath is os.Executable, indirected so the divergence case (the
// binary in one checkout, the operator standing in another) is testable — it is
// exactly the stale-kit failure this fleet keeps hitting, so it needs a test.
var executablePath = os.Executable

// walkUpToRepoRoot climbs from start looking for a directory holding both
// `harness/` and `.git/`, bounded the same way operatorWriteLog is.
func walkUpToRepoRoot(start string) string {
	dir := start
	for i := 0; i < 12; i++ { // bounded: never walk to / on a deep tree
		if isDir(filepath.Join(dir, "harness")) && isDir(filepath.Join(dir, ".git")) {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return ""
		}
		dir = parent
	}
	return ""
}

func isDir(path string) bool {
	fi, err := os.Stat(path)
	return err == nil && fi.IsDir()
}

// sameDirectory reports whether two paths name the same directory, however they
// were spelled. Three tries, cheapest first: the strings, the symlink-resolved
// strings, and finally the inode — os.SameFile is the only one of the three that
// also sees through a Windows junction or a bind mount, which is the shape the
// operator boxes hit (a synced Documents folder).
//
// One of three path-identity helpers that must agree: this one, client.sameLogFile
// (are these two write logs one file) and cli.resolvePath/withinAny (is this file
// admissible as evidence). Same rule in all three — compare what the paths
// RESOLVE to, never the strings — so a change here belongs in the others.
func sameDirectory(a, b string) bool {
	if a == b {
		return true
	}
	ra, errA := filepath.EvalSymlinks(a)
	rb, errB := filepath.EvalSymlinks(b)
	if errA == nil && errB == nil && ra == rb {
		return true
	}
	fa, errA := os.Stat(a)
	fb, errB := os.Stat(b)
	return errA == nil && errB == nil && os.SameFile(fa, fb)
}

// operatorWriteLog finds `queries/<slug>/sap-writes.jsonl` for the operator
// registered in this checkout, or "" if there isn't one.
//
// The checkout is RepoRoot's answer, never a second walk of its own. It used to
// do the walk again with the opposite preference — cwd before exe, where RepoRoot
// prefers the exe — so the two could name different checkouts on the box this
// fleet keeps hitting: an operator standing in one copy running a binary from
// another. The delete guard then read its evidence out of one checkout while the
// write log it vouches for was written into the other, and every message about
// "this checkout" meant whichever function had printed it. One question, one
// answer.
//
// A consequence worth stating: RepoRoot needs BOTH harness/ and .git/, so a
// month-old Drive zip (no .git) no longer gets an in-repo log. Its writes go to
// ~/.sapb1-writes.jsonl, which is the truth — nothing in an un-versioned folder
// reaches the team — and evidenceGapAdvice says so with the command that fixes it.
//
// Best-effort by design: it is called on a path where failing to resolve must
// never block a write that the operator has already confirmed. Any problem —
// no repo, no registration, unreadable JSON — simply falls through to the home
// default rather than returning an error.
func operatorWriteLog() string {
	root, _ := RepoRoot() // the note is for the operator; callers here just need the path
	if root == "" {
		return ""
	}
	raw, err := os.ReadFile(filepath.Join(root, "harness", ".operator")) // #nosec G304 — inside the resolved checkout
	if err != nil {
		return "" // a checkout, but nobody registered in it
	}
	var reg struct {
		Slug string `json:"slug"`
	}
	if err := json.Unmarshal(raw, &reg); err != nil {
		return ""
	}
	slug := strings.TrimSpace(reg.Slug)
	if slug == "" {
		return ""
	}
	logDir := filepath.Join(root, "queries", slug)
	if err := os.MkdirAll(logDir, 0o755); err != nil {
		return ""
	}
	return filepath.Join(logDir, "sap-writes.jsonl")
}
