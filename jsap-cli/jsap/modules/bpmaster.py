"""BP Master module — Business Partner master-data reads.

READ-ONLY: every endpoint here is a GET lookup that feeds the BP Creation form's
dropdowns / uniqueness checks (docs/jsap/BPMaster.md). The module itself is
creation-only in the app; the CLI wraps only its read surface. The single write
(`InsertBPmasterData`) and the legacy upload/delete routes are deliberately
excluded.
"""

from __future__ import annotations

from .._reg import endpoint, group


def register(subparsers):
    g = group(subparsers, "bpmaster", "Business Partner master reads")

    # Full BP card list. BPType/isStaff are required by the API (400 otherwise)
    # but do not actually filter — pass sane defaults so the command just works.
    endpoint(
        g,
        "cards",
        path="/api/BPmaster/BPGetCardInfo",
        help="Full BP card list (code, name, address, state, GSTIN)",
        params=[
            {
                "name": "BPType",
                "type": str,
                "required": False,
                "default": "custa",
                "help": "custa|venda|orgc|orgv (API-required; does not filter)",
            },
            {
                "name": "isStaff",
                "type": str,
                "required": False,
                "default": "N",
                "help": "Y|N (API-required; does not filter)",
            },
        ],
        company_param="company",
    )

    endpoint(
        g,
        "groups",
        path="/api/BPmaster/GetGroupNameByBPType",
        help="BP groups (groupCode/groupName) for a type",
        params=[
            {
                "name": "bpType",
                "type": str,
                "required": False,
                "default": "custa",
                "help": "custa|venda|orgc|orgv",
            },
            {
                "name": "isStaff",
                "type": str,
                "required": False,
                "default": "N",
                "help": "Y|N",
            },
        ],
        company_param="company",
    )

    endpoint(
        g,
        "maingroups",
        path="/api/BPmaster/GetMaingroup",
        help="Main groups (u_Main_Group) for a type",
        params=[
            {
                "name": "bpType",
                "type": str,
                "required": False,
                "default": "custa",
                "help": "custa|venda|orgc|orgv",
            },
            {
                "name": "IsStaff",
                "type": str,
                "required": False,
                "default": "N",
                "help": "Y|N",
            },
        ],
        company_param="company",
    )

    endpoint(
        g,
        "chains",
        path="/api/BPmaster/GetChain",
        help="Sales chains (u_Chain); customer-only in the form",
        params=[
            {
                "name": "bpType",
                "type": str,
                "required": False,
                "default": "custa",
                "help": "custa|venda|orgc|orgv",
            },
            {
                "name": "IsStaff",
                "type": str,
                "required": False,
                "default": "N",
                "help": "Y|N",
            },
        ],
        company_param="company",
    )

    endpoint(
        g,
        "msmetypes",
        path="/api/BPmaster/GetMSMEtype",
        help="MSME business types (Manufacturing/Service/Trading/Others)",
        company_param="company",
    )

    endpoint(
        g,
        "pans",
        path="/api/BPmaster/GetUniquePANs",
        help="Registered PANs (currently returns an empty list)",
        company_param="company",
    )

    endpoint(
        g,
        "countries",
        path="/api/BPmaster/GetCountry",
        help="Country list (code/name); company is mandatory (500 without)",
        company_param="company",
    )

    endpoint(
        g,
        "states",
        path="/api/BPmaster/GetDistinctStates",
        help="States (code/name) for a country",
        params=[
            {
                "name": "CountryCode",
                "type": str,
                "required": False,
                "default": "IN",
                "help": "ISO-2 country code, e.g. IN, US",
            },
        ],
        company_param="company",
    )

    endpoint(
        g,
        "gst",
        path="/api/BPmaster/GetGSTMismatchByState",
        help="GST state-code lookup for a state (state code required)",
        params=[
            {
                "name": "stateCode",
                "type": str,
                "required": True,
                "positional": True,
                "help": "State code, e.g. PB, MH, DL",
            },
        ],
        company_param="company",
    )

    endpoint(
        g,
        "payterms",
        path="/api/BPmaster/GetDistinctPaymentGroups",
        help="Payment-term groups (groupNum/pymntGroup)",
        company_param="company",
    )

    endpoint(
        g,
        "pricelists",
        path="/api/BPmaster/GetPricelist",
        help="Price lists (listNum/code/name/listName)",
        company_param="company",
    )

    endpoint(
        g,
        "banks",
        path="/api/BPmaster/GetDistinctBankName",
        help="Bank names (bankCode/bankName/swiftNo/countryCode)",
        company_param="company",
    )

    # Uniqueness-check routes: documented reads, but they 404 on this
    # deployment (frontend falls back to in-session checks). Wrapped for
    # completeness — expect an empty/None response ("not found/unavailable").
    endpoint(
        g,
        "contactuid",
        path="/api/BPmaster/CheckContactUid",
        help="Contact-UID uniqueness check (404/empty on this deployment)",
        params=[
            {
                "name": "contactUid",
                "type": str,
                "required": True,
                "positional": True,
                "help": "Contact UID to check",
            },
        ],
    )

    endpoint(
        g,
        "addressuid",
        path="/api/BPmaster/CheckAddressUid",
        help="Address-UID uniqueness check (404/empty on this deployment)",
        params=[
            {
                "name": "addressUid",
                "type": str,
                "required": True,
                "positional": True,
                "help": "Address UID to check",
            },
        ],
    )
