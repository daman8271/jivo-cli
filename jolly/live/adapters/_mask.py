#!/usr/bin/env python3
"""_mask.py — the one place that keeps personal phone numbers out of the feed.

`live/state/state.json` is published over HTTPS at a tokenised public hostname
for the Mark 3 site to fetch client-side. The site never renders a phone
number, but the JSON behind it is the thing that actually leaves the building —
so the number must not be IN it. `jolly/CLAUDE.md`: **no real phone number,
ever.**

Two rules, applied to every value on its way to disk:

  a) A dict key that NAMES a phone (``mobile``, ``phone``, ``contact_no``,
     ``whatsapp``, ``tel``) has its scalar value replaced wholesale with
     ``••••`` + the last two digits. The row stays, the key stays, the shape
     the site parses is unchanged — an operator can still tell two trucks apart
     by the tail, and nobody can dial it.

  b) Any OTHER string is scanned for an Indian-mobile-shaped run (optional
     +91 / 91 / 0, then ten digits starting 6-9, spaces and dashes tolerated
     inside) and each run is replaced with the same masked form. This is the
     one that matters in practice: today's leak is not a ``driver_mobile_no``
     field, it is ``driver_name = "Sompal 8295058874"`` — a gate clerk typing
     the number into the name box.

WHAT IS DELIBERATELY LEFT ALONE, and why it needs saying

A ten-digit number starting 6-9 is not always a phone. These systems are full
of counter-examples, and masking one of them would silently corrupt the feed:

    po_number      6500262904      an OMS purchase order — ten digits, starts 6
    grpo_no        2026086831      SAP GRPO number
    po_number      220926010       nine digits, EXIM
    order_number   ORD-20260903-0016
    entry_no       GE-2026-5640 / EVGI-20260903-0008
    vehicle_no     HR67C4904 / DL01LAN4065 / GJ39TA1566
    sap_doc_number 1726086707      ten digits, starts 1-5

So the key is consulted first. A key on the ID/plate allow-list
(``vehicle``, ``plate``, ``registration``, ``po_number``, ``order_number``,
``entry_no``, ``grpo``, ``*_code``, ``*_id``, …) keeps its scalar value
verbatim — not scanned, not masked. Everything else is scanned.

Shape-wise the run must stand alone: the lookarounds refuse a match that is
glued to another digit or sits after a decimal point, which is what keeps
timestamps (``2026-09-03T13:10:20+05:30``), litres (``9876543.21``) and long
document numbers out of it.

THE TRADE-OFF, STATED: an allow-listed key is trusted completely, and a
ten-digit PO number that appears loose inside a free-text sentence WILL be
masked. That is the safe direction — a cosmetically damaged PO number in prose
costs nothing; a driver's mobile on a public URL is the thing we cannot undo.

Idempotent: masking an already-masked value returns it unchanged, so it is
safe to run on every write (per-source file, last-good file, state.json).

Nothing here talks to any business system. Pure string work.

    from live.adapters._mask import mask_phones, mask_phones_verbose, scan_phones

    mask_phones(envelope)                 # in place, returns the same object
    obj, records = mask_phones_verbose(o) # + what was masked, and where
    scan_phones(obj)                      # [(path, value)] — what a mask missed
"""

from __future__ import annotations

import re

__all__ = ["mask_phones", "mask_phones_verbose", "scan_phones",
           "MASK", "PHONE_KEY_RE", "ID_KEY_RE", "MOBILE_RE"]

MASK = "•" * 4          # ••••

# (a) keys that NAME a phone number.
PHONE_KEY_RE = re.compile(r"(mobile|phone|contact_no|whatsapp|tel)", re.I)

# Never a phone, whatever else the name happens to contain. Checked BEFORE the
# phone-key rule so a plate field can never be masked by an unlucky substring.
PLATE_KEY_RE = re.compile(r"(vehicle|plate|registration|regn|truck_no|lorry)", re.I)

# Identifiers whose scalar values are documents, not people. Their values are
# left verbatim and are not scanned — and the leak guard skips them too, so the
# two halves of this module always agree on what is allowed to look like a
# phone number.
ID_KEY_RE = re.compile(
    r"""(
          vehicle | plate | registration | regn | truck_no | lorry
        | po_number | po_no | purchase_order | master_po | amazon_po | pos
        | order_no | order_number | order_id
        | invoice | doc_num | docnum | doc_no | doc_number | docentry
        | gate_id | gate_pass | gatepass | entry_no | entry_id
        | slip_no | slip_id | arrival_no | grpo | awb | lr_no | bilty | challan
        | ref_no | reference | batch | serial | gstin | pan_no | hsn
        | code | sku | item_no
        | (^|_)id$
    )""",
    re.I | re.X,
)

# (b) an Indian mobile inside any other string.
#   (?<![\d.])  — not glued to a digit, not the tail of a decimal
#   prefix      — optional +91 / 91 / 0
#   ten digits starting 6-9, single space or dash tolerated between them
#   (?!\d)(?!\.\d) — not the head of a longer number, not a rupee amount
MOBILE_RE = re.compile(
    r"(?<![\d.])"
    r"(?:\+?91[\s\-]?|0)?"
    r"(?:[6-9](?:[\s\-]?\d){9})"
    r"(?!\d)(?!\.\d)"
)

_DIGITS_RE = re.compile(r"\D")


# --------------------------------------------------------------------------- #
# the masked form                                                             #
# --------------------------------------------------------------------------- #
def _masked(text: str) -> str:
    """`••••` plus the last two digits of `text` (fewer if it has fewer)."""
    digits = _DIGITS_RE.sub("", text)
    return MASK + digits[-2:]


def _mask_runs(text: str) -> str:
    """Rule (b): mask every mobile-shaped run inside a free string."""
    return MOBILE_RE.sub(lambda m: _masked(m.group(0)), text)


def _already_masked(text: str) -> bool:
    return MASK in text


# --------------------------------------------------------------------------- #
# the walk                                                                    #
# --------------------------------------------------------------------------- #
def _walk(obj, key, path, records):
    """Return the masked replacement for `obj`, which sat under `key`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = _walk(v, k, "%s.%s" % (path, k), records)
        return obj

    if isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = _walk(v, key, "%s[%d]" % (path, i), records)
        return obj

    # ---- scalars ---------------------------------------------------------
    is_str = isinstance(obj, str)
    is_num = isinstance(obj, (int, float)) and not isinstance(obj, bool)
    if not (is_str or is_num):
        return obj                                   # None, bool, anything else

    named_phone = bool(key) and bool(PHONE_KEY_RE.search(key)) \
        and not PLATE_KEY_RE.search(key)

    if named_phone:
        text = str(obj)
        if not text.strip() or _already_masked(text):
            return obj                               # empty / already done
        out = _masked(text)
        records.append({"path": path, "key": key, "reason": "key",
                        "masked": out})
        return out

    # An allow-listed identifier keeps its scalar value verbatim.
    if bool(key) and ID_KEY_RE.search(key):
        return obj

    if not is_str:
        return obj                                   # numbers are not scanned

    out = _mask_runs(obj)
    if out != obj:
        records.append({"path": path, "key": key, "reason": "value",
                        "masked": out})
        return out
    return obj


def mask_phones(obj):
    """Mask every phone number in a JSON-shaped object. Mutates and returns it."""
    return _walk(obj, None, "$", [])


def mask_phones_verbose(obj):
    """(masked_obj, records) — records say what was masked, where, and why."""
    records: list = []
    return _walk(obj, None, "$", records), records


# --------------------------------------------------------------------------- #
# the leak guard                                                              #
# --------------------------------------------------------------------------- #
def scan_phones(obj, path="$", key=None, out=None):
    """Every string still holding a mobile-shaped run, as (path, value).

    Same allow-list as the masker, so a clean run really is clean rather than a
    disagreement between two rules. Strings only — the masker never touches a
    number under a non-phone key, so warning about one would be noise.
    """
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan_phones(v, "%s.%s" % (path, k), k, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan_phones(v, "%s[%d]" % (path, i), key, out)
    elif isinstance(obj, str):
        if key and ID_KEY_RE.search(key) and not PHONE_KEY_RE.search(key):
            return out
        if MOBILE_RE.search(obj):
            out.append((path, obj))
    return out


if __name__ == "__main__":                            # tiny manual smoke test
    import json
    import sys
    doc = json.load(sys.stdin)
    doc, recs = mask_phones_verbose(doc)
    sys.stderr.write("masked %d value(s)\n" % len(recs))
    json.dump(doc, sys.stdout, ensure_ascii=False, indent=2)
