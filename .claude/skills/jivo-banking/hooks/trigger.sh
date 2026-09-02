#!/usr/bin/env bash
# Auto-trigger for the jivo-banking skill (bank statement -> SAP B1).
#
# A skill's `description` is only a hint the model may or may not act on. This
# hook is the enforcement: it reads the operator's prompt on stdin and, when the
# prompt is about entering or reconciling a bank statement, prints a reminder to
# stdout. Claude Code injects a UserPromptSubmit hook's stdout into the turn as
# context, so the instruction arrives BEFORE any tool call is chosen.
#
# Design rules (same as every trigger in this repo):
#   - fail open. Any error, missing tool, or unreadable input exits 0 silently.
#   - print nothing on a non-match, so ordinary turns cost zero extra tokens.
#   - no interpreter dependency (Accounts runs Windows where `python3` is a
#     Store stub) — pure shell and grep.
#
# Turn it off for one session with:  export JIVO_NO_BANKING_HOOK=1

set -u
[ "${JIVO_NO_BANKING_HOOK:-}" = "1" ] && exit 0

INPUT=""
if ! IFS= read -r -d '' -t 2 INPUT 2>/dev/null; then
  : # partial or timed-out read is fine — whatever arrived is in INPUT
fi
[ -z "$INPUT" ] && exit 0

LOWER=$(printf '%s' "$INPUT" | tr '[:upper:]' '[:lower:]')

# Two-part match: a BANK signal AND a do-something-with-it signal. Requiring both
# keeps ordinary questions ("what is our bank balance") from firing it, while
# "this is a bank statement, make the entries", "put this hsbc export in sap" and
# "reconcile the bank" all match. aistmtprint is HSBC's own export filename.
BANK='bank statement|bank entry|bank entries|bank line|statement of account|passbook|aistmtprint|hsbc|reconcil|bank export|bank ledger|account statement'
CONTEXT='sap|draft|entry|entries|enter|key |keyed|punch|post|import|upload|reconcil|match|tally|xlsx|csv|statement'

printf '%s' "$LOWER" | grep -Eq "$BANK" || exit 0
printf '%s' "$LOWER" | grep -Eq "$CONTEXT" || exit 0

cat <<'EOF'
<system-reminder>
This prompt looks like BANK STATEMENT work (entering or reconciling a bank
statement in SAP B1).

Invoke the `jivo-banking` skill NOW, before any tool call, and follow it.

The one rule that matters most, because it inverts your usual caution:

  A STATEMENT RECORDS MONEY THAT HAS ALREADY MOVED. The default hypothesis is
  that the lines are ALREADY IN SAP, and the tool must prove otherwise before
  you build a single payload. On 2026-08-31 all 7 lines of an HSBC statement
  handed over for entry were already posted — 4 receipts by USER11 and 3
  payments by USER05, the same morning. The failure mode here is DUPLICATING
  REAL MONEY, not missing a record.

Match every line against ORCT and OVPM on AMOUNT + DATE + BANK GL before
drafting anything, and report the diff BOTH ways — a SAP row with no statement
line is a payment the bank never showed, and matters as much as a missing entry.

Three more things that are invisible until after the write:

  1. A narrative naming JIVO ITSELF is a TRANSFER between JIVO's own bank
     accounts, not a payment to a party — DocType 'rAccount' with a
     PaymentAccounts row carrying the DESTINATION bank GL. Resolve every
     account number in a narrative via OACT before mapping a name to a BP.
  2. U_Pymnt_Mode (NEFT/RTGS/FT) is MANDATORY on the Service Layer path and
     optional in the SAP client — 14,195 posted receipts have it NULL and yours
     will still be rejected with "(46000071) Please select Payment Mode". A
     blank field in a precedent is NOT permission to leave yours blank.
  3. An on-account draft opens with an EMPTY Contents grid and that is CORRECT.
     Count PDF2/PDF4 rows and warn the operator before they open it.

Identify drafts by DocEntry. A draft's DocNum is provisional and several
unadded drafts share the same one.

If this prompt turns out not to be about a bank statement, ignore this notice.
</system-reminder>
EOF

exit 0
