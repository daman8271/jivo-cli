// Package cobratree holds the mechanics for exposing a Cobra command tree as
// MCP tools: resolving the CLI binary to shell out to, refusing root flags a
// tool caller must not be able to set, and running the child process.
//
// It is deliberately a SUBSET of the reference implementation in
// exim-pp-cli/internal/mcp/cobratree. Two pieces of that package are
// intentionally absent here:
//
//   - the blanket walker (RegisterAll). On dsr it would emit one tool per
//     runnable leaf — 84 of them — which is both unusable for an agent and
//     unsafe as a policy: any subcommand added later would auto-appear as a
//     tool with no review. dsr's tool table is hand-authored instead (see
//     ../tools.go), so a new leaf reaches the MCP surface only when a human
//     adds it to the allowlist.
//
//   - SplitShellArgs. It strips quotes and rejects any token starting with
//     "-", which would mangle exactly the input dsr_query has to carry
//     verbatim (`WHERE name = 'A B'`, or any SQL containing a `--` comment).
//     Positionals here are passed as single argv elements, untouched.
package cobratree

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

// SelfCLIPath resolves the dsr CLI binary the MCP tools shell out to.
//
// Unlike the reference implementation, which looks for a SEPARATE companion
// binary next to itself, the dsr MCP server lives INSIDE the dsr binary
// (`dsr mcp`). The shell-out target is therefore this same executable, which
// is why the container needs only one mount and the tool surface can never
// drift from the CLI it claims to mirror. The env var and PATH lookups remain
// as escape hatches for odd deployments (e.g. a symlinked/renamed exe).
func SelfCLIPath() (string, error) {
	if exe, err := os.Executable(); err == nil {
		if resolved, err := filepath.EvalSymlinks(exe); err == nil {
			exe = resolved
		}
		if _, err := os.Stat(exe); err == nil {
			return exe, nil
		}
	}
	if v := os.Getenv("DSR_CLI_PATH"); v != "" {
		return v, nil
	}
	return exec.LookPath(cliExecutableName(runtime.GOOS))
}

func cliExecutableName(goos string) string {
	name := "dsr"
	if goos == "windows" {
		return name + ".exe"
	}
	return name
}
