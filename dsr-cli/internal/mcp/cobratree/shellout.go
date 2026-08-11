package cobratree

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
	"strings"
)

// BlockedFlags are dsr root-level flags that an MCP caller must never be able
// to set, whatever the tool.
//
//   - db / d: the SQL Server instance behind DSR_V6 hosts 72 databases,
//     several of them unrelated accounting databases. The deployed .env pins
//     DSR_DATABASE; letting a tool argument override it would turn a
//     field-sales tool into a general database browser for the whole instance.
//   - profile / config: config selection is the operator's, not the caller's.
//   - csv / compact / quiet / select: output shaping is fixed by the server
//     (--json) so every tool returns one predictable, parseable shape.
//   - args: the reference implementation's raw-passthrough escape hatch. There
//     is no passthrough here at all; the name is blocked so it cannot be
//     reintroduced by accident.
//
// The primary defence is the per-action flag allowlist in ../tools.go — a
// flag that is not listed there is never emitted. This map is the second
// layer, asserted by TestNoToolEmitsABlockedFlag.
var BlockedFlags = map[string]bool{
	"args":    true,
	"compact": true,
	"config":  true,
	"csv":     true,
	"d":       true,
	"db":      true,
	"profile": true,
	"quiet":   true,
	"select":  true,
}

// RunCLICommand executes the dsr CLI and returns stdout.
//
// stdout is kept as the machine-readable channel: stderr is folded into the
// error text only, so a warning or notice printed by the CLI can never corrupt
// the JSON an agent is about to parse.
func RunCLICommand(ctx context.Context, binPath string, args []string) (string, error) {
	cmd := exec.CommandContext(ctx, binPath, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		msg := strings.TrimSpace(stderr.String())
		if msg == "" {
			msg = strings.TrimSpace(stdout.String())
		}
		if msg != "" {
			label := "stderr"
			if strings.TrimSpace(stderr.String()) == "" {
				label = "output"
			}
			return stdout.String(), fmt.Errorf("dsr %s: %w (%s: %s)", strings.Join(args, " "), err, label, msg)
		}
		return stdout.String(), fmt.Errorf("dsr %s: %w", strings.Join(args, " "), err)
	}
	return stdout.String(), nil
}
