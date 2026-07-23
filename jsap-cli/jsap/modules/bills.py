"""Bill Verification module — maker/checker/payment/admin read desks.

READ-ONLY: GET only. Wraps every read endpoint in the Bill Verification page set
(Invoice Maker, Invoice Checker, Payment Maker, Payment Checker, Admin) — the
account-suggestion autocompletes, the per-desk bill lists, invoice line-item
drilldowns (by voucher and by item serial), the admin all-bills activity feeds,
the global summary counts and the attachment download.

No write path (SubmitBill / UpdateCheckerStatus / Reject / MarkAsPaid /
MarkVerified / RejectPayment / AttachFile / DeleteAttachment / RejectCheckerEntry)
is wrapped. Company scoping is server-side by session, so these endpoints take no
company query param. Docs: docs/jsap/BillVerification.md
"""

from __future__ import annotations

from .._reg import endpoint, group

# fromDate/toDate/accountName are optional server-side on every bill list
# (no params => 200 with the full range). Reused across the desks.
_BILL_PARAMS = [
    {
        "name": "fromDate",
        "type": str,
        "help": "Start date yyyy-MM-dd (optional; server defaults if omitted)",
    },
    {"name": "toDate", "type": str, "help": "End date yyyy-MM-dd (optional)"},
    {
        "name": "accountName",
        "type": str,
        "help": "Filter to one vendor/account (exact name; optional)",
    },
]

# Admin activity feeds — same param shape, same row shape, one per legacy tab.
_ADMIN_FEEDS = {
    "admin": (
        "/Admin/GetMakerActivity",
        "Admin all-bills feed (every voucher; maker/checker/payment status)",
    ),
    "admin-checker": (
        "/Admin/GetCheckerActivity",
        "Admin checker-activity feed (legacy tab, still live)",
    ),
    "admin-payment": (
        "/Admin/GetInvoicePaymentActivity",
        "Admin invoice-payment activity feed (legacy tab, still live)",
    ),
    "admin-paidcheck": (
        "/Admin/GetPaymentCheckerActivity",
        "Admin payment-checker activity feed (legacy tab, still live)",
    ),
}


def register(subparsers):
    g = group(
        subparsers, "bills", "Bill verification: maker/checker/payment/admin reads"
    )

    # -- Vendor/account autocomplete (two variants, same list) -------------
    endpoint(
        g,
        "accounts",
        path="/Maker/GetAccountSuggestions",
        help="Vendor/account name suggestions (omni-search; ~10 max)",
        params=[
            {
                "name": "term",
                "type": str,
                "default": "",
                "help": "Search term (optional; empty returns top matches)",
            }
        ],
    )

    endpoint(
        g,
        "checker-accounts",
        path="/Checker/GetAccountSuggestions",
        help="Vendor/account suggestions (Checker desk variant; same list)",
        params=[
            {
                "name": "term",
                "type": str,
                "default": "",
                "help": "Search term (optional; empty returns top matches)",
            }
        ],
    )

    # -- Per-desk bill lists -----------------------------------------------
    endpoint(
        g,
        "maker",
        path="/Maker/GetBillDetails",
        help="Maker view of bills (per-voucher totals: qty/value/items)",
        params=_BILL_PARAMS,
    )

    endpoint(
        g,
        "checker",
        path="/Checker/GetBillDetails",
        help="Checker view of bills (adds server-side status filter)",
        params=_BILL_PARAMS
        + [
            {
                "name": "status",
                "type": str,
                "help": "Server-side filter: Pending / Approved / Rejected (optional)",
            },
        ],
    )

    endpoint(
        g,
        "payment",
        path="/InvoicePayment/GetBillDetails",
        help="Payment-queue view (filter client-side to Approved & UnPaid)",
        params=_BILL_PARAMS,
    )

    endpoint(
        g,
        "paid",
        path="/PaymentChecker/GetPaidBillDetails",
        help="Paid invoices only (payment-checker desk)",
        params=_BILL_PARAMS,
    )

    # -- Invoice line-item drilldowns --------------------------------------
    endpoint(
        g,
        "items",
        path="/Maker/GetInvoiceItems",
        help="Invoice line items for one voucher (by MRN / vchNumber)",
        params=[
            {
                "name": "vchNumber",
                "type": str,
                "positional": True,
                "required": True,
                "help": "Voucher number / MRN, e.g. 903",
            }
        ],
    )

    endpoint(
        g,
        "checker-items",
        path="/Checker/GetInvoiceItems",
        help="Invoice line items by item serial (richer taxRate/taxAmount)",
        params=[
            {
                "name": "serialNumber",
                "type": str,
                "positional": True,
                "required": True,
                "help": "Invoice-item serial, e.g. 17039.0015",
            }
        ],
    )

    # -- Admin summary + all-bills activity feeds --------------------------
    endpoint(
        g,
        "summary",
        path="/Admin/GetSummary",
        help="Global lifetime KPI counts (totalBills/pendingMaker/approvedChecker/totalPaid)",
    )

    for name, (path, helptext) in _ADMIN_FEEDS.items():
        endpoint(g, name, path=path, help=helptext, params=_BILL_PARAMS)

    # -- Attachment download probe -----------------------------------------
    endpoint(
        g,
        "attachment",
        path="/uploads/maker",
        help="Fetch a bill attachment by its attachmentPath (metadata probe)",
        params=[
            {
                "name": "path",
                "type": str,
                "positional": True,
                "required": True,
                "help": "attachmentPath from a bill row, e.g. /uploads/maker/<guid>.pdf",
            }
        ],
        handler=_attachment,
    )


def _attachment(client, args):
    """Fetch an attachment and report metadata (the read client decodes text,
    so we surface type/size rather than dumping raw binary)."""
    path = args.path
    if not path.startswith("/"):
        path = "/uploads/maker/" + path.lstrip("/")
    blob = client.get(path)
    text = blob if isinstance(blob, str) else str(blob)
    base = path.rsplit("/", 1)[-1]
    ext = base.rsplit(".", 1)[-1].lower() if "." in base else "unknown"
    return {
        "path": path,
        "type": ext,
        "looksLikePdf": text.startswith("%PDF"),
        "approxBytes": len(text.encode("utf-8", "replace")),
    }
