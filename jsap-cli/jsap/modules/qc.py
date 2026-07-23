"""Quality Check module — the master QC parameter template (read-only).

Wraps the QC form-definition reads from /QcWeb/QualityCheck. READ-ONLY: GET only.
The page's Update flow (UpdateForm/CreateParameter/CreateSubParameter) is a WRITE
surface and is deliberately NOT wrapped — see docs/READ_ONLY_LAW.md.

Docs: docs/jsap/QualityCheck.md

Note: the shared-shell read GetUserEffectivePermissions (the page's QC_web gate)
is a cross-cutting concern already exposed globally as `meta permissions`; it is
not re-wrapped here, matching the reports.py/meta.py convention.
"""

from __future__ import annotations

from .._reg import endpoint, group


def register(subparsers):
    g = group(subparsers, "qc", "Parameter quality-check reads")

    endpoint(
        g,
        "form",
        path="/api/QC/GetFormStructureV2",
        help="Full current QC template: form header, quality settings/"
        "thresholds, 7 mandatory-document flags, and the parameter -> "
        "sub-parameter tree (flat join rows keyed by parameterId)",
    )

    endpoint(
        g,
        "legacy",
        path="/api/QC/GetFormStructure",
        help="Legacy v1 form structure (debug alias; currently returns a "
        "null form + empty arrays — GetFormStructureV2 is the live one)",
    )
