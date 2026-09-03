package config

import (
	"encoding/json"
	"os"
	"os/user"
	"path/filepath"
	"strings"

	"github.com/joho/godotenv"
)

// ---------------------------------------------------------------------------
// DRAFTS-ONLY DESKS
// ---------------------------------------------------------------------------
//
// Some desks build documents and hand them to a person; they never press Add.
// Mahak's GRPO desk is the first: she keys the freight bills, and SHE decides
// when a draft is submitted for approval or posted — from the SAP B1 client,
// with the paper in front of her. An AI that "finishes the job" by running
// add-draft on her behalf puts documents in Bhawani's approval queue that
// nobody asked to send, and there is no un-send.
//
// The instruction to stop at the draft already exists in CLAUDE.md and in the
// skill router, but both are words a model can talk itself past. This is the
// part that cannot be talked past: a check in the binary, ahead of every read
// and every send, that refuses the command outright.
//
// WHY THE DESK LIVES IN harness/desks.json AND NOT IN A LOCAL FILE
//
// desks.json is committed, reviewed and shared. A marker file on one machine is
// invisible to everyone else and disappears the next time the kit is
// re-unzipped; a policy nobody can see is a policy nobody maintains. The same
// file already decides which skills a desk carries, matched by the same
// identity rules, so a desk is described in exactly one place.
//
// WHY $SAPB1_DRAFTS_ONLY CAN ONLY TURN IT *ON*
//
// An override that switches the guard off is a button that makes the policy go
// away, which is the one thing it must not be — same reasoning as add-draft's
// missing --force. The env var exists so a desk can be locked down before the
// commit lands (and so the tests can drive it); it is never consulted to lift
// the lock.

// DraftsOnly is the answer to "may this checkout press Add?".
type DraftsOnly struct {
	On   bool   // true: add-draft must refuse
	Who  string // the identity token that matched, for the refusal message
	Note string // the desks.json note — who set it and when
	From string // where the answer came from
}

// DraftsOnlyDesk reports whether this checkout is a drafts-only desk.
//
// Best-effort and silent by design: it is called before a write, and every
// failure mode — no checkout, unreadable JSON, no home directory — resolves to
// "not a drafts-only desk", which is the behaviour every other box has today.
// A parse error here must never break add-draft on the 20 desks that are
// allowed to use it.
func DraftsOnlyDesk() DraftsOnly {
	// The .env beside the kit is the belt for the one case desks.json cannot
	// reach: a kit unzipped WITHOUT .git, where RepoRoot correctly answers ""
	// and the shared policy file is therefore invisible. godotenv never
	// overwrites a variable the shell already set, and Load runs again inside
	// config.Load a moment later, so this is safe to call twice.
	_ = godotenv.Load()
	if envTruthy(os.Getenv("SAPB1_DRAFTS_ONLY")) {
		return DraftsOnly{On: true, Who: "SAPB1_DRAFTS_ONLY", From: "environment", Note: "set in this shell"}
	}
	root, _ := RepoRoot()
	if root == "" {
		return DraftsOnly{}
	}
	raw, err := os.ReadFile(filepath.Join(root, "harness", "desks.json")) // #nosec G304 — inside the resolved checkout
	if err != nil {
		return DraftsOnly{}
	}
	var cfg struct {
		DraftsOnly []struct {
			Who  []string `json:"who"`
			Note string   `json:"note"`
		} `json:"drafts_only"`
	}
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return DraftsOnly{}
	}
	ids := deskIdentity(root)
	for _, rule := range cfg.DraftsOnly {
		for _, tok := range rule.Who {
			tok = strings.ToLower(strings.TrimSpace(tok))
			if tok == "" {
				continue
			}
			for _, id := range ids {
				if strings.Contains(id, tok) {
					return DraftsOnly{On: true, Who: tok, Note: rule.Note, From: "harness/desks.json"}
				}
			}
		}
	}
	return DraftsOnly{}
}

// deskIdentity is harness/bin/desk.py's _identity(), in Go and lower-cased:
// hostname, %COMPUTERNAME%, the local username, and the slug/name in
// harness/.operator. The two implementations must agree, or a desk would carry
// the skill it is not allowed to have while the binary let it write, or the
// reverse.
func deskIdentity(root string) []string {
	var ids []string
	add := func(s string) {
		s = strings.ToLower(strings.TrimSpace(s))
		if s != "" {
			ids = append(ids, s)
		}
	}
	if forced := os.Getenv("JIVO_DESK_AS"); strings.TrimSpace(forced) != "" {
		add(forced)
		return ids
	}
	if h, err := os.Hostname(); err == nil {
		add(h)
	}
	add(os.Getenv("COMPUTERNAME"))
	if u, err := user.Current(); err == nil {
		add(u.Username)
		// Windows hands back DOMAIN\user; the bare name is what desks.json names.
		if i := strings.LastIndexAny(u.Username, `\/`); i >= 0 {
			add(u.Username[i+1:])
		}
	}
	if raw, err := os.ReadFile(filepath.Join(root, "harness", ".operator")); err == nil { // #nosec G304
		var reg struct {
			Slug string `json:"slug"`
			Name string `json:"name"`
		}
		if json.Unmarshal(raw, &reg) == nil {
			add(reg.Slug)
			add(reg.Name)
		}
	}
	return ids
}

func envTruthy(v string) bool {
	switch strings.ToLower(strings.TrimSpace(v)) {
	case "1", "true", "yes", "on":
		return true
	}
	return false
}
