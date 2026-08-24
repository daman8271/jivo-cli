"""readback — a draft as SAP actually holds it, and what is missing from it.

Report the flags as gaps, never as success. An API-made A/P draft reliably comes
out with TDS at zero even when the vendor card says otherwise (C-0018) and with
AttachmentEntry null, and the only way anyone finds out is by reading it back.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from . import rules
from .sap import SapCli


def read_draft(sap: SapCli, docentry: int) -> dict | None:
    rows = sap.query("Drafts", filter=f"DocEntry eq {int(docentry)}")
    return rows[0] if rows else None


def draft_owner(sap: SapCli, draft: Mapping[str, Any]) -> str:
    rows = sap.query("Users", filter=f"InternalKey eq {draft['UserSign']}",
                     select="UserCode,UserName")
    if rows:
        return f"{rows[0]['UserCode']} ({rows[0]['UserName']})"
    return f"user {draft['UserSign']}"


def readback_flags(draft: Mapping[str, Any], expect: Mapping[str, Any] | None = None,
                   tds_choice: str | None = None, attachment_entry: Any = None,
                   bp: Mapping[str, Any] | None = None, origin: str = "expected") -> list[str]:
    """Everything wrong with this draft, in the words the operator needs.

    `tds_choice` is the decision that was actually made for this bill ("yes" or
    "no"). When it is "no", TDS of zero is the intended outcome and flagging it
    would be a false positive — that is exactly what happened on TPAC once the
    operator overruled the master flag.
    """
    flags: list[str] = []
    lines = draft.get("DocumentLines") or []

    for l in lines:
        if not l.get("BaseEntry"):
            flags.append(f"line {l['LineNum']} is not drawn from a GRPO — adding it would "
                         "receive stock a second time")

    wt_amount = float(draft.get("WTAmount") or 0)
    if tds_choice == "yes":
        if not wt_amount:
            flags.append("TDS was asked for but the draft came out 0 — tick WTax Liable on every "
                         "row in the SAP client before Add (C-0018)")
    elif tds_choice is None and bp and bp.get("SubjectToWithholdingTax") == "boYES" and not wt_amount:
        codes = [w.get("WTCode") for w in (bp.get("BPWithholdingTaxCollection") or [])]
        flags.append(f"TDS is 0 but the vendor is TDS-liable (codes {codes}) — tick WTax Liable "
                     "on every row in the SAP client before Add")

    if expect:
        qty = sum(float(l.get("Quantity") or 0) for l in lines)
        if expect.get("open_qty") is not None and abs(qty - float(expect["open_qty"])) > 0.001:
            flags.append(f"quantity {qty:g} ≠ {origin} {float(expect['open_qty']):g}")
        if expect.get("gross") is not None:
            gross = float(draft.get("DocTotal") or 0) + wt_amount
            if abs(round(gross) - round(float(expect["gross"]))) > 1:
                flags.append(f"gross {rules.inr(gross)} (total + TDS) ≠ {origin} "
                             f"{rules.inr(float(expect['gross']))}")

    if attachment_entry and not draft.get("AttachmentEntry"):
        flags.append(f"attachment pointer not set — the GRPO's bill is Attachments2 "
                     f"{attachment_entry}; attach it in the client or patch the draft")

    return flags


def base_line_flags(draft: Mapping[str, Any], grpo: Mapping[str, Any]) -> list[str]:
    """Are the GRPO lines this draft sits on still open?

    If somebody else invoiced them between the draft being made and being added,
    Add fails — better to say so now than to let the operator find out in the
    client.
    """
    used = {l["BaseLine"] for l in (draft.get("DocumentLines") or [])
            if l.get("BaseEntry") == grpo.get("DocEntry")}
    closed = [gl["LineNum"] for gl in (grpo.get("DocumentLines") or [])
              if gl["LineNum"] in used and gl.get("LineStatus") != "bost_Open"]
    if closed:
        return [f"GRPO {grpo['DocNum']} lines {closed} were invoiced by someone else — "
                "this draft will fail on Add"]
    return []


def base_entries(draft: Mapping[str, Any]) -> list[int]:
    return sorted({l["BaseEntry"] for l in (draft.get("DocumentLines") or [])
                   if l.get("BaseType") == 20 and l.get("BaseEntry")})
