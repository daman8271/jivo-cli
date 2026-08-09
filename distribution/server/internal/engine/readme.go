package engine

import (
	"bytes"
	"fmt"
	"sort"
	"strings"
	"time"

	"jivodist/internal/manifest"
)

// ReadmeInput is everything the per-bundle README.txt is generated from. It is
// all explicit — including the clock — so the same selection always renders the
// same file and the golden test means something.
type ReadmeInput struct {
	Target      string
	Recipient   string
	BundleID    string
	GeneratedAt time.Time
	Manifest    *manifest.Manifest
	Components  []string // included components, in selection order
	Files       []StagedFile
	Skipped     []Skip
	Warnings    []string
	Overrides   *manifest.Overrides
}

const readmeWidth = 78

// RenderReadme writes the recipient-facing README.txt. It branches on each
// component's auth_mode: telling someone a credential is "already set up" when
// their binary never reads it is the silent failure this repo's lessons are
// made of.
func RenderReadme(in ReadmeInput) []byte {
	var b strings.Builder
	line := strings.Repeat("=", readmeWidth)
	rule := strings.Repeat("-", readmeWidth)

	fmt.Fprintf(&b, "%s\n", line)
	fmt.Fprintf(&b, "JIVO KIT  —  %s\n", targetLabel(in.Target))
	if in.Recipient != "" {
		fmt.Fprintf(&b, "Built for : %s\n", in.Recipient)
	}
	fmt.Fprintf(&b, "Built on  : %s\n", in.GeneratedAt.Format("Mon 2 Jan 2006, 15:04 MST"))
	fmt.Fprintf(&b, "Bundle    : %s\n", in.BundleID)
	fmt.Fprintf(&b, "%s\n\n", line)

	// ---------------------------------------------------------------- rules
	b.WriteString("READ THIS FIRST\n\n")
	for i, l := range in.Manifest.Lessons.ReadmeMustSay {
		text := l
		if isHarnessLine(l) && !hasStagedFile(in.Files, "harness/bin/setup.py") {
			text = "This kit is a standalone bundle, NOT a git checkout of the toolkit, so " +
				"there is no harness/ folder and no setup.py to run — skip that step if a " +
				"colleague mentions it. One consequence: if you write to SAP, the audit log " +
				"lands in your home folder (~/.sapb1-writes.jsonl) instead of the shared " +
				"history. Start at the doctor command for your tool, below."
		}
		writeNumbered(&b, i+1, text)
	}
	b.WriteString("\n")

	// -------------------------------------------------------------- contents
	b.WriteString("WHAT IS IN THIS KIT\n\n")
	for _, id := range in.Components {
		c, ok := in.Manifest.Component(id)
		if !ok {
			continue
		}
		writeBullet(&b, fmt.Sprintf("%s — %s", c.UIName, firstSentence(c.UIDescription)))
	}
	b.WriteString("\n")

	// ------------------------------------------------------------- first run
	fmt.Fprintf(&b, "FIRST RUN\n\n")
	for _, step := range firstRunSteps(in) {
		writeNumbered(&b, step.n, step.text)
	}
	b.WriteString("\n")

	// --------------------------------------------------------------- network
	b.WriteString("NETWORK — WHICH TOOLS NEED WHAT\n\n")
	writeBullet(&b, "SAP B1 and HANA: office LAN, the FortiClient VPN profile 'Mieux', or the "+
		"tunnel this kit was configured with. From plain home Wi-Fi the SAP doctor WILL fail "+
		"even though the credentials are perfect — that is the network, not the kit.")
	writeBullet(&b, "Everything else (sales, factory, ecom, imports, ops portals, DSR, control "+
		"panel): any internet connection, home or office.")
	b.WriteString("\n")

	// ------------------------------------------------------------ components
	for _, id := range in.Components {
		c, ok := in.Manifest.Component(id)
		if !ok {
			continue
		}
		fmt.Fprintf(&b, "%s\n%s\n\n", rule, strings.ToUpper(c.UIName))
		writeWrapped(&b, "  ", c.UIDescription)
		b.WriteString("\n")

		b.WriteString("  HOW TO RUN IT\n")
		for _, l := range runInstructions(in, c) {
			writeWrapped(&b, "    ", l)
		}
		b.WriteString("\n")

		b.WriteString("  CREDENTIALS\n")
		writeWrapped(&b, "    ", authHeadline(AuthMode(id)))
		if note := AuthNote(id); note != "" {
			writeWrapped(&b, "    ", note)
		}
		b.WriteString("\n")

		b.WriteString("  CHECK IT WORKS (no network needed)\n")
		if in.Target == "windows" {
			// The checks below are quoted from the tool inventory verbatim and
			// are written in Mac shell style. Say the conversion once rather
			// than rewriting somebody else's prose.
			writeWrapped(&b, "    ", "(These are written Mac-style. In cmd, drop the leading ./ and "+
				"use the .exe name — e.g. `hana-sql.exe --help`.)")
		}
		for _, tool := range c.Tools {
			// Per TOOL, not per component: sap-b1 has two tools and only one of
			// them ships to any given target, so a component-level test printed
			// the check for a binary the recipient does not have.
			if !toolStaged(in.Files, tool) {
				continue
			}
			writeWrapped(&b, "    ", tool.OfflineCheck)
		}
		b.WriteString("\n")

		notes := behaviourNotes(id, in.Target)
		notes = append(notes, componentWarnings(in, id)...)
		if len(notes) > 0 {
			b.WriteString("  WORTH KNOWING\n")
			for _, n := range notes {
				writeWrapped(&b, "    - ", n)
			}
			b.WriteString("\n")
		}
	}

	// --------------------------------------------------------------- notices
	if len(in.Warnings) > 0 {
		fmt.Fprintf(&b, "%s\nWARNINGS FROM THIS BUILD\n\n", rule)
		for _, w := range in.Warnings {
			writeBullet(&b, w)
		}
		b.WriteString("\n")
	}
	if len(in.Skipped) > 0 {
		fmt.Fprintf(&b, "%s\nNOT IN THIS KIT\n\n", rule)
		for _, s := range in.Skipped {
			writeBullet(&b, fmt.Sprintf("%s / %s — %s", s.Component, s.Tool, s.Reason))
		}
		b.WriteString("\n")
	}

	fmt.Fprintf(&b, "%s\nIF SOMETHING IS WRONG\n\n", rule)
	writeBullet(&b, "A red doctor is almost always credentials or network, in that order. "+
		"Message Daman with the exact command and the exact message — do not guess and do not retry a write.")
	writeBullet(&b, "If an answer looks wrong, say so in the chat. Corrections you make reach "+
		"every other operator's copy by the next day.")
	writeBullet(&b, "Delete the zip once this folder is in place. Keep the folder; the "+
		"credentials inside it are live.")
	b.WriteString("\n")

	out := b.String()
	if in.Target == "windows" {
		// Windows Notepad shows LF-only text as one long line. Only this
		// generated file is translated — every copied file, and in particular
		// the hash-pinned product-identity JSON, ships byte-identical.
		out = strings.ReplaceAll(out, "\n", "\r\n")
	}
	return []byte(out)
}

func targetLabel(target string) string {
	switch target {
	case "mac-arm64":
		return "Mac (Apple Silicon)"
	case "windows":
		return "Windows (64-bit)"
	default:
		return target
	}
}

func authHeadline(mode string) string {
	switch mode {
	case AuthBakedEnv:
		return "Ready to use — the credentials are in this kit and the tool reads them itself."
	case AuthLogin:
		return "One login needed — the credentials are in this kit for reference, but the tool " +
			"does NOT read the file. Run its `auth login` once, and it caches the session."
	case AuthHomeConfig:
		return "One file to install — the tool reads its config only from your home folder, so " +
			"the bundled copy does nothing until you put it there."
	case AuthExternalToken:
		return "Limited — no long-lived credential can ship for this. See below."
	default:
		return mode
	}
}

type runStep struct {
	n    int
	text string
}

func firstRunSteps(in ReadmeInput) []runStep {
	var steps []runStep
	n := 0
	next := func(text string) {
		n++
		steps = append(steps, runStep{n: n, text: text})
	}

	if in.Target == "windows" {
		next(`Unzip to a short path with no spaces: C:\jivo-cli. You should end up with C:\jivo-cli\ containing this README.txt.`)
		next("Open Command Prompt there: press Win+R, type cmd, then `cd C:\\jivo-cli`.")
		next("Windows quirks that bite: use `python`, not `python3`. The imports tool (exim) " +
			"only runs under Git Bash. For write payloads use --data-file instead of escaping quotes in cmd.")
	} else {
		next("Unzip into your HOME folder so you end up with ~/jivo-cli — not Documents, Desktop or " +
			"Downloads. macOS blocks remote support from those three folders.")
		next("Open Terminal and run: cd ~/jivo-cli")
		next("Clear the download quarantine, once, or macOS blocks every tool as an " +
			"'unidentified developer':\n    xattr -dr com.apple.quarantine ~/jivo-cli")
		if bins := stagedBinaries(in.Files); len(bins) > 0 {
			var sb strings.Builder
			sb.WriteString("If a command says 'permission denied', restore the execute bit:\n    chmod +x \\\n")
			for i, p := range bins {
				sep := " \\"
				if i == len(bins)-1 {
					sep = ""
				}
				fmt.Fprintf(&sb, "      ~/jivo-cli/%s%s\n", p, sep)
			}
			next(strings.TrimRight(sb.String(), "\n"))
		}
	}
	next("Lock the credential files down: on Mac `chmod 600 $(find ~/jivo-cli -name '*.env')`; " +
		"on Windows leave them where they are and do not copy them anywhere.")
	next("Run the offline check for your tool from its section below. That proves the tool runs. " +
		"Then run its doctor, which also proves the network and the credentials.")
	return steps
}

// nativePath renders a bundle-relative path the way the recipient's shell
// writes it. Zip entries themselves always use forward slashes (zip spec) —
// this is only for the instructions a person reads and types.
func nativePath(target, p string) string {
	if target == "windows" {
		return strings.ReplaceAll(p, "/", `\`)
	}
	return p
}

// bundlePath is a path inside the unzipped kit, spelled for the target.
func bundlePath(target, rel string) string {
	if target == "windows" {
		if rel == "" {
			return `C:\jivo-cli`
		}
		return `C:\jivo-cli\` + nativePath(target, rel)
	}
	if rel == "" {
		return "~/jivo-cli"
	}
	return "~/jivo-cli/" + rel
}

func runInstructions(in ReadmeInput, c *manifest.Component) []string {
	var out []string
	if dir := RunDir(c.ID, in.Target); dir != "" {
		out = append(out, fmt.Sprintf(
			"cd %s   — this tool reads its credentials from the folder you are standing in, so run it from there.",
			bundlePath(in.Target, dir)))
	} else {
		out = append(out, fmt.Sprintf(
			"Run it from anywhere inside %s — it finds its own settings by looking upward through the folders.",
			bundlePath(in.Target, "")))
	}
	if bins := binaryPathsFor(in.Files, c.ID); len(bins) > 0 {
		var names []string
		for _, p := range bins {
			if in.Target == "windows" {
				names = append(names, nativePath(in.Target, p))
			} else {
				names = append(names, "./"+p)
			}
		}
		out = append(out, "Included here: "+strings.Join(names, "  "))
	}
	return out
}

// behaviourNotes are the things that differ inside a bundle from inside the
// repo — the surprises a recipient would otherwise discover by being wrong.
func behaviourNotes(component, target string) []string {
	var out []string
	switch component {
	case "sap-b1":
		out = append(out,
			"Reading is safe and changes nothing. SAP is the only system in this kit you can write to, "+
				"and only by typing draft/post/patch yourself — every write previews first and needs the full word 'yes'.",
			"If a write ever says the outcome is unknown (exit code 7): STOP. Do not run it again. "+
				"Check SAP for what actually exists, and tell Daman.",
			"Because this is a standalone kit and not a repo checkout, your SAP write log goes to your "+
				"home folder (~/.sapb1-writes.jsonl on Mac, C:\\Users\\<you>\\.sapb1-writes.jsonl on Windows) "+
				"instead of the shared team history.")
		if target == "windows" {
			out = append(out,
				"claude_desktop_config.json in this kit points at C:\\jivo-sap\\sapb1.exe. Either copy the "+
					"sap-b1\\accounts-kit folder to C:\\jivo-sap, or edit that path in the file before pasting it "+
					"into %APPDATA%\\Claude\\claude_desktop_config.json. Fill in the password by hand and keep that file private.",
				"If the SAP box is reached through the tunnel, SAPB1_HOST must be exactly 'localhost' — "+
					"any other name or IP gets a 403 from SAP's web server.")
		}
	case "hana-sql":
		out = append(out,
			"To switch between office and home routes, copy connections/hana-tunnel.env over "+
				"connections/hana.env (keep a copy of the original first).",
			"--help exits with code 2. That is normal for this tool — if you see the usage text, it works.")
	case "postsql":
		out = append(out,
			"Install the config before first use — Mac: `mkdir -p ~/.postsql && cp postsql/config.toml.INSTALL ~/.postsql/config.toml && chmod 600 ~/.postsql/config.toml`. "+
				"Windows: create %USERPROFILE%\\.postsql\\config.toml with the same contents.")
	case "control-panel":
		out = append(out,
			"The tool looks for credentials at ~/software/.env, which this kit does not create. "+
				"Log in explicitly instead: `jivo auth login --env-file <this folder>/control-panel/.env`.")
	case "exim":
		if target == "windows" {
			out = append(out, "exim runs through a bash wrapper, so Windows needs Git Bash installed. "+
				"The exim-pp-cli.exe in this kit can also be run directly from cmd.")
		}
		out = append(out, "exim/.secrets/ is empty on purpose: the login token is minted on first use and "+
			"belongs to this machine. Never copy a token.json in from another machine.")
	case "jsap-cli":
		if target == "windows" {
			out = append(out, "Run it as `python jsap-cli\\jsap` — on Windows the interpreter is `python`, not `python3`.")
		}
	case "dsr-cli":
		out = append(out, "If you run dsr from outside this folder it also looks for a copy of its .env at "+
			"~/.dsr/.env (Windows: %USERPROFILE%\\.dsr\\.env) — copy it there if you want to run it from anywhere.")
	case "factory-cli", "jivo-scraping-cli":
		out = append(out, "The product-identity files at the top of this kit are checksum-pinned. Do not edit, "+
			"reformat or re-save them, or every `product` command will refuse to run.")
	}
	return out
}

func componentWarnings(in ReadmeInput, id string) []string {
	if in.Overrides == nil {
		return nil
	}
	out := append([]string(nil), scopeWarnings(in.Overrides.Components[id], in.Target)...)
	for _, f := range in.Files {
		if f.Component != id || f.Kind != KindBinary {
			continue
		}
		out = append(out, scopeWarnings(in.Overrides.Binaries[f.Src], in.Target)...)
	}
	return out
}

// ------------------------------------------------------------------ helpers

func isHarnessLine(l string) bool {
	return strings.Contains(l, "harness/bin/setup.py")
}

func hasStagedFile(files []StagedFile, zipPath string) bool {
	for _, f := range files {
		if f.ZipPath == zipPath {
			return true
		}
	}
	return false
}

func toolIncluded(files []StagedFile, component string) bool {
	for _, f := range files {
		if f.Component == component && f.Kind == KindBinary {
			return true
		}
	}
	return false
}

// toolStaged reports whether this specific tool's binary made it into the
// bundle, matched by the binary paths the manifest gives the tool.
func toolStaged(files []StagedFile, tool manifest.Tool) bool {
	for _, f := range files {
		if f.Kind != KindBinary {
			continue
		}
		for _, b := range tool.Binaries {
			if f.Src == b.Path {
				return true
			}
		}
	}
	return false
}

func stagedBinaries(files []StagedFile) []string {
	var out []string
	for _, f := range files {
		if f.Kind == KindBinary {
			out = append(out, f.ZipPath)
		}
	}
	sort.Strings(out)
	return out
}

func binaryPathsFor(files []StagedFile, component string) []string {
	var out []string
	for _, f := range files {
		if f.Kind == KindBinary && f.Component == component {
			out = append(out, f.ZipPath)
		}
	}
	sort.Strings(out)
	return out
}

func firstSentence(s string) string {
	if i := strings.Index(s, " — "); i > 0 {
		return strings.TrimSpace(s[:i])
	}
	if i := strings.Index(s, ". "); i > 0 {
		return strings.TrimSpace(s[:i+1])
	}
	return s
}

func writeNumbered(b *strings.Builder, n int, text string) {
	head := fmt.Sprintf("  %2d. ", n)
	writeWrapped(b, head, text)
}

func writeBullet(b *strings.Builder, text string) {
	writeWrapped(b, "  - ", text)
}

// writeWrapped renders text under a hanging indent. Pre-formatted blocks (lines
// the caller already broke, such as the chmod list) are passed through.
func writeWrapped(b *strings.Builder, head, text string) {
	indent := strings.Repeat(" ", len(head))
	first := true
	for _, para := range strings.Split(text, "\n") {
		h := indent
		if first {
			h = head
			first = false
		}
		if strings.HasPrefix(para, "    ") || strings.HasPrefix(para, "      ") {
			// already laid out by the caller
			b.WriteString(indent + strings.TrimRight(para, " ") + "\n")
			continue
		}
		for _, l := range wrap(para, readmeWidth-len(indent)) {
			b.WriteString(h + l + "\n")
			h = indent
		}
	}
}

func wrap(s string, width int) []string {
	words := strings.Fields(s)
	if len(words) == 0 {
		return []string{""}
	}
	var lines []string
	var cur bytes.Buffer
	for _, w := range words {
		if cur.Len() > 0 && cur.Len()+1+len(w) > width {
			lines = append(lines, cur.String())
			cur.Reset()
		}
		if cur.Len() > 0 {
			cur.WriteByte(' ')
		}
		cur.WriteString(w)
	}
	if cur.Len() > 0 {
		lines = append(lines, cur.String())
	}
	return lines
}
