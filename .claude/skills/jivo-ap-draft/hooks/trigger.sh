#!/usr/bin/env bash
# Auto-trigger for A/P bill entry (jivo-add-and-new -> the right builder skill).
#
# Written for operators who will NOT prompt well. The common shape at the
# Accounts desk is a folder of scans and either no instruction at all or three
# words ("yeh karo", "enter this", "do these"). A skill `description` is only a
# hint the model may or may not act on; this hook is the enforcement.
#
# Two ways to match, because a bill arrives with or without words:
#   1. bill/invoice language, or
#   2. an attached document (pdf/jpg/scan/folder) plus an entry-ish verb.
#
# Fail open, always exit 0. Print nothing on a non-match.
# Turn it off for one session with:  export JIVO_NO_AP_HOOK=1

set -u
[ "${JIVO_NO_AP_HOOK:-}" = "1" ] && exit 0

INPUT=""
if ! IFS= read -r -d '' -t 2 INPUT 2>/dev/null; then
  :
fi
[ -z "$INPUT" ] && exit 0

LOWER=$(printf '%s' "$INPUT" | tr '[:upper:]' '[:lower:]')

# A payment is a different entry type with its own hook — let that one own it.
printf '%s' "$LOWER" | grep -Eq 'payment|advance|rtgs|neft|remit' && exit 0

BILL='bill|invoice|grpo|goods receipt|bilty|lr no|freight|transporter|purchase invoice|a/p|ap invoice|vendor|credit note'
DOC='\.pdf|\.jpg|\.jpeg|\.png|\.tif|scan|photo|attach|folder|these files'
VERB='enter|entry|make|draft|create|punch|key|do these|do this|yeh karo|karo|process|add'

MATCH=0
printf '%s' "$LOWER" | grep -Eq "$BILL" && MATCH=1
if [ "$MATCH" -eq 0 ]; then
  printf '%s' "$LOWER" | grep -Eq "$DOC" \
    && printf '%s' "$LOWER" | grep -Eq "$VERB" && MATCH=1
fi
[ "$MATCH" -eq 0 ] && exit 0

cat <<'EOF'
<system-reminder>
This looks like a vendor bill arriving at the Accounts desk.

Invoke the `jivo-add-and-new` skill NOW, before any tool call, and follow it to
the END. Entering the bill is not the job — the job ends when the approver has
it. A draft nobody submits is invisible to her (ODRF.WddStatus='-').

Pick the builder skill that matches the paper in hand:
  - ordinary vendor tax invoice ............ jivo-ap-draft
  - service bill (no GRPO behind it) ....... jivo-ap-service-draft
  - credit note / return ................... jivo-ap-credit-memo
  - transporter freight bill ............... jivo-oil-freight-grpo (Oil),
                                             jivo-bev-freight-grpo (Beverages),
                                             jivo-mart-freight-grpo (Mart)
Read the BILL-TO and the sale invoice numbers to choose the book. Do not
hand-roll the payload — the pre-check finds the GRPO, branch, series and any
existing draft before anything is sent.

Never `sapb1 post` a document to "just get it in" — that bypasses the approver
and lands unapproved in the ledger (C-0034).

If this prompt is not about a vendor bill, ignore this notice.
EOF

exit 0
