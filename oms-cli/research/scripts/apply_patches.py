#!/usr/bin/env python3
"""Re-apply every .printing-press-patches entry to a freshly generated tree.

Each patch fails LOUDLY if its anchor is missing. A patch script that quietly
skips its edit because "the thing already looks present" is how a required
header stayed hardcoded on the sibling factory project while the invariant gate
reported green and `--company` was a silent no-op. A skip is never an outcome
here: either the edit is applied, or it is already applied in exactly the
expected shape, or it is an error.

Run from the CLI root (oms-cli/). Idempotent on an already-patched tree.

  0001  preserve the hand-authored `auth login`
  0002  keep the generated `import` write command unregistered   (RULE 0)
  0003  keep `invoices history` unregistered (backend route absent)
  0004  HANA required params — enforced in the SPEC by emit_spec.py and
        asserted by research/verify-invariants.sh; nothing to patch in Go
  0005  fail-closed GET-only guards in BOTH MCP execution paths   (NEW)
"""
import os
import re
import sys

FAIL = []


def read(p):
    return open(p).read()


def write(p, s):
    open(p, "w").write(s)


# ---------------------------------------------------------------- patch 0001
# The hand-authored `auth login` exchanges username+password for a JWT at
# POST /api/auth/login/. It is the ONE permitted OMS write: it mutates a
# session and no business data. A clean print drops it.
p = "internal/cli/auth.go"
s = read(p)
if "newAuthOmsLoginCmd(flags)" in s:
    print("patch 0001: auth login already registered")
else:
    anchor = "\tcmd.AddCommand(newAuthSetupCmd(flags))\n"
    if anchor not in s:
        FAIL.append("0001: anchor newAuthSetupCmd not found in auth.go")
    else:
        s = s.replace(
            anchor,
            "\tcmd.AddCommand(newAuthOmsLoginCmd(flags)) "
            "// hand-authored: username+password -> JWT (oms_login.go)\n" + anchor,
            1)
        write(p, s)
        print("patch 0001: restored the auth login registration")
if not os.path.exists("internal/cli/oms_login.go"):
    FAIL.append("0001: internal/cli/oms_login.go is MISSING — restore it from the "
                "pre-reprint tree; the registration alone will not build")

# ---------------------------------------------------------------- patch 0002
# The generated `import` command POSTs records to the OMS API. RULE 0 forbids
# any write to a JIVO source system, so it must never reach the Cobra tree.
p = "internal/cli/root.go"
s = read(p)
reg = "\trootCmd.AddCommand(newImportCmd(flags))\n"
note = (
    "\t// READ-ONLY LAW (docs/READ_ONLY_LAW.md): the `import` command POSTs records\n"
    "\t// to the OMS API (base_url + /<resource>). It is intentionally NOT registered\n"
    "\t// so this CLI can never write to any JIVO source system.\n"
)
if reg in s:
    s = s.replace(reg, note, 1)
    write(p, s)
    print("patch 0002: removed the import registration")
elif "READ-ONLY LAW" in s:
    print("patch 0002: already applied")
else:
    FAIL.append("0002: neither the registration nor the marker comment found in "
                "root.go — the template changed; re-inspect before shipping")
live = [l for l in read(p).split("\n")
        if "newImportCmd" in l and not l.lstrip().startswith("//")]
if live:
    FAIL.append(f"0002: newImportCmd is still referenced by live code: {live}")

# ---------------------------------------------------------------- patch 0003
# The deployed backend has no /api/invoice/history/{id}/ route. Registering the
# command presents a permanently broken read.
p = "internal/cli/invoices.go"
s = read(p)
reg = "\tcmd.AddCommand(newInvoicesHistoryCmd(flags))\n"
note = (
    "\t// Live verification (2026-07-19, re-verified 2026-08-04): the deployed OMS\n"
    "\t// backend has no /api/invoice/history/{id}/ route, so this command always\n"
    "\t// 404s. Unregistered until the backend team confirms the route.\n"
    "\t// cmd.AddCommand(newInvoicesHistoryCmd(flags))\n"
)
if reg in s:
    s = s.replace(reg, note, 1)
    write(p, s)
    print("patch 0003: unregistered invoices history")
elif "// cmd.AddCommand(newInvoicesHistoryCmd" in s:
    print("patch 0003: already applied")
else:
    FAIL.append("0003: neither the registration nor the commented marker found in "
                "invoices.go")
live = [l for l in read(p).split("\n")
        if "newInvoicesHistoryCmd" in l and not l.lstrip().startswith("//")]
if live:
    FAIL.append(f"0003: newInvoicesHistoryCmd is still registered: {live}")

# ---------------------------------------------------------------- patch 0005
# Fail-closed GET-only guards in BOTH MCP execution paths.
#
# The MCP surface for a JIVO system is read-only forever: the CLI may write when
# an operator explicitly asks, but an agent-trusted surface has no operator in
# the loop. A fresh `cli-printing-press generate` restores the full generic
# POST/PUT/PATCH/DELETE machinery in BOTH paths, and guarding only the direct
# tool handler leaves the code-orchestration executor as a complete bypass —
# it reaches the same HTTP client.
#
# This is not currently exploitable (both paths take the method from the
# endpoint catalog, and the spec is GET-only), which is exactly why it needs a
# structural guard: the only thing standing between the machinery and a live
# write is one future spec edit that nobody reviews as a security change.
GUARD_TOOLS = (
    '\t\tdefault:\n'
    '\t\t\t// READ-ONLY LAW (docs/READ_ONLY_LAW.md): this CLI never mutates JIVO\n'
    '\t\t\t// source systems, and the MCP surface never exposes a write at all.\n'
    '\t\t\t// The spec is GET-only; refuse every write method by construction so\n'
    '\t\t\t// that a future spec edit cannot silently open a write path through\n'
    '\t\t\t// an agent-trusted surface. Re-apply after every regen. Patch 0005.\n'
    '\t\t\treturn mcplib.NewToolResultError("read-only CLI: method " + method +\n'
    '\t\t\t\t" is not permitted (GET only, per the JivoGPT READ-ONLY LAW)"), nil\n'
    '\t\t}\n'
)
p3 = "internal/mcp/tools.go"
s3 = read(p3)
if "READ-ONLY LAW" in s3:
    print("patch 0005a: tools.go guard already present")
else:
    m = re.search(r'\t\tcase "POST":\n.*?\t\tdefault:\n'
                  r'\t\t\treturn mcplib\.NewToolResultError\('
                  r'"unsupported method: " \+ method\), nil\n\t\t\}\n', s3, re.S)
    if not m:
        FAIL.append("0005a: tools.go write-method block not found in the expected shape")
    else:
        write(p3, s3[:m.start()] + GUARD_TOOLS + s3[m.end():])
        print("patch 0005a: tools.go guarded (write methods removed)")

p4 = "internal/mcp/code_orch.go"
s4 = read(p4)
if "READ-ONLY LAW" in s4:
    print("patch 0005b: code_orch.go guard already present")
else:
    m = re.search(r'\tcase "DELETE":\n.*?\tdefault:\n'
                  r'\t\treturn mcplib\.NewToolResultError\('
                  r'fmt\.Sprintf\("unsupported method %q", ep\.Method\)\), nil\n\t\}\n',
                  s4, re.S)
    if not m:
        FAIL.append("0005b: code_orch.go write-method block not found in the expected shape")
    else:
        guard = (
            '\tdefault:\n'
            '\t\t// READ-ONLY LAW (docs/READ_ONLY_LAW.md): guarding only tools.go would\n'
            '\t\t// leave THIS executor as a write bypass - it reaches the same client.\n'
            '\t\t// Both paths must be guarded, and a fresh generate restores the write\n'
            '\t\t// machinery in both. See patch 0005.\n'
            '\t\treturn mcplib.NewToolResultError(fmt.Sprintf(\n'
            '\t\t\t"read-only CLI: method %q is not permitted (GET only, per the '
            'JivoGPT READ-ONLY LAW)",\n'
            '\t\t\tep.Method)), nil\n'
            '\t}\n'
        )
        s4 = s4[:m.start()] + guard + s4[m.end():]
        # the write-body closure is now unreachable; the package-level
        # codeOrchWriteBody / codeOrchArrayBody helpers stay, because the
        # generated write-body unit test exercises them directly and that keeps
        # the body-marshaling contract pinned.
        s4 = re.sub(r'\twriteBody := func\(\) any \{\n(?:.*?\n)*?\t\}\n',
                    '\t// write-body closure removed with the write methods (patch 0005);\n'
                    '\t// codeOrchWriteBody / codeOrchArrayBody stay for their unit test.\n',
                    s4, count=1)
        write(p4, s4)
        print("patch 0005b: code_orch.go guarded (write methods removed)")

if FAIL:
    print("\nPATCH FAILURES:")
    for f in FAIL:
        print("  ", f)
    sys.exit(1)
print("all patches applied")
