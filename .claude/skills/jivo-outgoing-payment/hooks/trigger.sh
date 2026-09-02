#!/usr/bin/env bash
# Auto-trigger for the jivo-outgoing-payment skill.
#
# A skill's `description` is only a hint the model may or may not act on. This
# hook is the enforcement: it reads the operator's prompt on stdin and, when the
# prompt is about paying a vendor, prints a reminder to stdout. Claude Code
# injects a UserPromptSubmit hook's stdout into the turn as context, so the
# instruction arrives BEFORE any tool call is chosen.
#
# Design rules:
#   - fail open. Any error, missing tool, or unreadable input exits 0 silently.
#     A hook must never be able to block an operator from asking a question.
#   - print nothing on a non-match, so ordinary turns cost zero extra tokens.
#   - no interpreter dependency (Accounts runs Windows where `python3` is a
#     Store stub) — pure shell and grep.
#
# Turn it off for one session with:  export JIVO_NO_PAYMENT_HOOK=1

set -u
[ "${JIVO_NO_PAYMENT_HOOK:-}" = "1" ] && exit 0

# UserPromptSubmit delivers a JSON object on stdin carrying the prompt text.
# Read it with a timeout so a hook can never hang the session waiting on stdin.
INPUT=""
if ! IFS= read -r -d '' -t 2 INPUT 2>/dev/null; then
  : # partial or timed-out read is fine — whatever arrived is in INPUT
fi
[ -z "$INPUT" ] && exit 0

# Lowercase without relying on bash 4 (macOS ships bash 3.2).
LOWER=$(printf '%s' "$INPUT" | tr '[:upper:]' '[:lower:]')

# Two-part match: a MONEY-MOVING verb/noun AND a payment context. Requiring both
# keeps ordinary SAP questions ("show me the invoice", "what is the balance")
# from firing it, while "punch this payment", "advance to AWL", "pay this
# vendor" and "outgoing payment draft" all match.
MONEY='payment|paying|pay |paid|advance|remit|rtgs|neft|outgoing|disburse'
CONTEXT='vendor|supplier|draft|sap|punch|entry|approve|bill|invoice|contract|advance|outgoing|party|beneficiar'

printf '%s' "$LOWER" | grep -Eq "$MONEY" || exit 0
printf '%s' "$LOWER" | grep -Eq "$CONTEXT" || exit 0

cat <<'EOF'
<system-reminder>
This prompt looks like outgoing-payment work (paying a vendor in SAP B1).

Invoke the `jivo-outgoing-payment` skill NOW, before any tool call, and follow
it. It is the settled JIVO procedure for this entry type and it encodes rules
that live data has already proven — skipping it has produced wrong entries.

Do not skip it because the request looks simple. The things most often got
wrong are all invisible until after the write:

  1. COMPANY comes from what the mail SAYS THE MONEY IS FOR, in words — a PO
     header "ONLY FOR BEVERAGES", "for beverage plant use", "work completion on
     beverage line". Nothing named = Oil. A LEDGER SCREENSHOT NAMES THE VENDOR,
     NOT THE COMPANY: on 2026-08-31 a screenshot of Oil's PYRUM (VENDA001678,
     -250,000) was attached to a payment released from BEVERAGES (VENDA001364,
     Rs 3,00,000). The CardCode is exact and therefore convincing — rank the
     sentence above it. Pass --company on EVERY command.
  2. LOGIN before payload. SAP passwords are PER COMPANY DB (C-0031), and
     "Fail to NONE-SSO login from SLD" means WRONG PASSWORD, not a licence
     block — ask for that company's password. Run `sapb1 doctor` first.
     UserSign is stamped at creation and cannot be patched afterwards.
  3. Decide the SHAPE — advance (on-account) vs settlement (applied). A
     SETTLEMENT also nets the vendor's unapplied advances in as NEGATIVE
     it_PaymentAdvice rows, so TransferSum is the NET, not the sum of the bills.
     A lone on-account precedent is often just an advance not yet netted off.
  4. The APPROVER's figure beats the requester's ask (request Rs 2,50,000 vs
     "Ok, approved.3lac" -> the entry was Rs 3,00,000). Approval threads live in
     accounts007@jivo.in — use mail-cli/jmail-acc7.
  5. Deduplicate on the AMOUNT, not a document number. An advance has no
     invoice reference, so the same figure going out twice is the real risk.
  6. CLONE the vendor's own most recent posted payment. Six fields
     (ControlAccount, PayToCode, ContactPersonCode, PaymentPriority, VATRegNum
     and the U_* UDFs) are per-vendor and appear on no paper. But take SERIES
     from the CURRENT month's payments in that company, not from an old
     precedent.

Also live: C-0028 (the attachment is the FULL approval mail, never the bill —
read it to the LAST page, the request is at the bottom and both named approvers
must have replied) and C-0029 (settling bills: Display = "Transactions for
Business Partner", select all).

If this prompt turns out not to be about paying a vendor, ignore this notice.
</system-reminder>
EOF

exit 0
