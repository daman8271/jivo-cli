#!/usr/bin/env python3
"""Re-apply every .printing-press-patches entry to a freshly generated tree.

Each patch fails LOUDLY if its anchor is missing. A patch script that quietly
skips its edit because "the thing already looks present" is how a required
header stayed hardcoded on the sibling factory project while the invariant gate
reported green and --company was a silent no-op.

Run from the CLI root. Idempotent: re-running on an already-patched tree is a
no-op, but a MISSING anchor is an error, never a skip.
"""
import re
import sys

FAIL = []


def read(p):
    return open(p).read()


def write(p, s):
    open(p, "w").write(s)


# ---------------------------------------------------------------- patch 0001
# Remove the generic `import` write command's registration. It POSTs to
# ecom.jivo.in with a Super-Admin JWT and is the only write path to a JIVO
# source system in this CLI. RULE 0 forbids it.
p = "internal/cli/root.go"
s = read(p)
reg = "\trootCmd.AddCommand(newImportCmd(flags))\n"
note = (
    "\t// JivoGPT RULE 0 (READ_ONLY_LAW): the generic `import` command POSTs records to\n"
    "\t// ecom.jivo.in (internal/cli/import.go -> c.Post \"/<resource>\"). It is the only write\n"
    "\t// path to a JIVO source system in this CLI, so it is deliberately NOT registered.\n"
    "\t// Re-apply this removal after any `cli-printing-press generate`. See patch 0001.\n"
    "\t// Do not re-add newImportCmd.\n"
)
if reg in s:
    s = s.replace(reg, note, 1)
    print("patch 0001: removed the import registration")
elif note.splitlines()[0] in s:
    print("patch 0001: already applied")
else:
    FAIL.append("0001: neither the registration nor the marker comment found in root.go — "
                "the template changed; re-inspect before shipping")
live = [l for l in s.split("\n")
        if "newImportCmd" in l and not l.lstrip().startswith("//")]
if live:
    FAIL.append(f"0001: newImportCmd is still referenced by live code: {live}")

# ---------------------------------------------------------------- patch 0003
# Restore the hand-authored `api` discovery command's registration.
if "newAPICmd(flags)" in s:
    print("patch 0003: already registered")
else:
    anchor = "\trootCmd.AddCommand(newVersionCmd())\n"
    if anchor not in s:
        FAIL.append("0003: anchor newVersionCmd not found in root.go")
    else:
        s = s.replace(anchor, "\trootCmd.AddCommand(newAPICmd(flags)) // hand-authored: "
                              "raw endpoint browser, no HTTP (api_discovery.go)\n" + anchor, 1)
        print("patch 0003: registered newAPICmd")
write(p, s)

# ---------------------------------------------------------------- patch 0002
# Restore the hand-authored `auth login` command's registration.
p2 = "internal/cli/auth.go"
s2 = read(p2)
if "newAuthLoginCmd(flags)" in s2:
    print("patch 0002: already registered")
else:
    m = re.search(r"(\tcmd\.AddCommand\(newAuthSetupCmd\(flags\)\)\n)", s2)
    if not m:
        FAIL.append("0002: anchor newAuthSetupCmd not found in auth.go")
    else:
        s2 = s2[:m.start()] + ("\tcmd.AddCommand(newAuthLoginCmd(flags)) // hand-authored: "
                               "email+password -> JWT (jivo_login.go)\n") + s2[m.start():]
        write(p2, s2)
        print("patch 0002: registered newAuthLoginCmd")

# ---------------------------------------------------------------- patch 0004
# Fail-closed GET-only guards in BOTH MCP execution paths. A fresh generate
# restores the generic POST/PUT/PATCH/DELETE machinery in both; guarding only
# the direct tool handler leaves the code-orchestration executor as a bypass.
GUARD_TOOLS = (
    '\t\tdefault:\n'
    '\t\t\t// READ-ONLY LAW (jivogpt): this CLI never mutates JIVO source\n'
    '\t\t\t// systems, and the MCP surface never exposes a write at all. The\n'
    '\t\t\t// spec is GET-only; refuse every write method by construction so\n'
    '\t\t\t// that a future spec edit cannot silently open a write path\n'
    '\t\t\t// through an agent-trusted surface. Re-apply after every regen.\n'
    '\t\t\treturn mcplib.NewToolResultError("read-only CLI: method " + method +\n'
    '\t\t\t\t" is not permitted (GET only, per the JivoGPT READ-ONLY LAW)"), nil\n'
    '\t\t}\n'
)
p3 = "internal/mcp/tools.go"
s3 = read(p3)
if "READ-ONLY LAW" in s3:
    print("patch 0004a: tools.go guard already present")
else:
    m = re.search(r'\t\tcase "POST":\n.*?\t\tdefault:\n\t\t\treturn mcplib\.NewToolResultError\('
                  r'"unsupported method: " \+ method\), nil\n\t\t\}\n', s3, re.S)
    if not m:
        FAIL.append("0004a: tools.go write-method block not found in the expected shape")
    else:
        s3 = s3[:m.start()] + GUARD_TOOLS + s3[m.end():]
        write(p3, s3)
        print("patch 0004a: tools.go guarded (write methods removed)")

p4 = "internal/mcp/code_orch.go"
s4 = read(p4)
if "READ-ONLY LAW" in s4:
    print("patch 0004b: code_orch.go guard already present")
else:
    m = re.search(r'\tcase "DELETE":\n.*?\tdefault:\n\t\treturn mcplib\.NewToolResultError\('
                  r'fmt\.Sprintf\("unsupported method %q", ep\.Method\)\), nil\n\t\}\n', s4, re.S)
    if not m:
        FAIL.append("0004b: code_orch.go write-method block not found in the expected shape")
    else:
        guard = (
            '\tdefault:\n'
            '\t\t// READ-ONLY LAW (jivogpt): guarding only tools.go would leave THIS\n'
            '\t\t// executor as a write bypass - it reaches the same client. Both\n'
            '\t\t// paths must be guarded, and a fresh generate restores the write\n'
            '\t\t// machinery in both. See patch 0004.\n'
            '\t\treturn mcplib.NewToolResultError(fmt.Sprintf(\n'
            '\t\t\t"read-only CLI: method %q is not permitted (GET only, per the '
            'JivoGPT READ-ONLY LAW)",\n'
            '\t\t\tep.Method)), nil\n'
            '\t}\n'
        )
        s4 = s4[:m.start()] + guard + s4[m.end():]
        s4 = re.sub(r'\twriteBody := func\(\) any \{\n(?:.*?\n)*?\t\}\n',
                    '\t// write-body closure removed with the write methods (patch 0004);\n'
                    '\t// codeOrchWriteBody / codeOrchArrayBody stay for their unit test.\n',
                    s4, count=1)
        write(p4, s4)
        print("patch 0004b: code_orch.go guarded (write methods removed)")

if FAIL:
    print("\nPATCH FAILURES:")
    for f in FAIL:
        print("  ", f)
    sys.exit(1)
print("all patches applied")
