"""Turn a vendor bill (PDF) into candidate identifiers we can look up in SAP.

Deliberately does NOT try to parse each vendor's layout perfectly — every
vendor prints its invoice number somewhere different. Instead it harvests every
plausible reference token, GSTIN, date and money figure, and lets SAP decide
which one is real: whichever candidate SAP knows as a NumAtCard is the answer.
That is far more robust than a per-vendor template, and it degrades gracefully
on a layout nobody has seen before.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z0-9]{2}\b")
# Indian-grouped or plain money, at least 3 digits so we skip line numbers.
MONEY_RE = re.compile(r"\b\d{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?\b|\b\d{3,}\.\d{2}\b")
DATE_RES = [
    re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b"),
    re.compile(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*,?\s+(\d{4})\b", re.I),
]
# A reference token: mostly digits, may carry dashes/slashes, 5-30 chars.
REF_RE = re.compile(r"\b(?=[A-Z0-9]*\d)[A-Z0-9][A-Z0-9/\-]{4,29}\b")

# Tokens that look like refs but never are.
REF_STOPWORDS = frozenset(
    {"INVOICE", "TAXINVOICE", "GSTIN", "IGST", "CGST", "SGST", "TOTAL", "AMOUNT",
     "IFSC", "SWIFT", "HSN", "SAC", "PAN", "CIN", "TAN", "INR"}
)

TOTAL_HINTS = ("grand total", "total amount", "invoice total", "net payable",
               "amount payable", "bill amount", "total value", "total")


@dataclass
class BillFacts:
    path: str
    text: str = ""
    ocr_used: bool = False
    gstins: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    amounts: list[float] = field(default_factory=list)
    grand_total: float | None = None

    def summary(self) -> str:
        return (
            f"refs={len(self.refs)} gstin={len(self.gstins)} "
            f"dates={len(self.dates)} total={self.grand_total}"
        )


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def pdf_text(path: Path, ocr_if_empty: bool = True) -> tuple[str, bool]:
    """Return (text, ocr_used). Falls back to tesseract for scanned bills."""
    text = ""
    if have("pdftotext"):
        try:
            text = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True, text=True, timeout=120,
            ).stdout
        except Exception:
            text = ""
    if len(text.strip()) >= 40 or not ocr_if_empty:
        return text, False
    # Scanned paper: rasterise then OCR.
    if not (have("pdftoppm") and have("tesseract")):
        return text, False
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(["pdftoppm", "-r", "300", "-png", str(path), f"{td}/pg"],
                           capture_output=True, timeout=300, check=True)
            chunks = []
            for img in sorted(Path(td).glob("pg*.png")):
                res = subprocess.run(["tesseract", str(img), "-", "--psm", "6"],
                                     capture_output=True, text=True, timeout=180)
                chunks.append(res.stdout)
            return "\n".join(chunks), True
        except Exception:
            return text, False


def _to_float(tok: str) -> float | None:
    try:
        return float(tok.replace(",", ""))
    except ValueError:
        return None


def find_grand_total(text: str) -> float | None:
    """The largest money figure on a line that names a total — vendors put the
    payable last, but 'largest on a total line' beats 'last number in the file'."""
    best: float | None = None
    for line in text.splitlines():
        low = line.lower()
        if not any(h in low for h in TOTAL_HINTS):
            continue
        vals = [v for v in (_to_float(m.group()) for m in MONEY_RE.finditer(line)) if v]
        if vals:
            cand = max(vals)
            if best is None or cand > best:
                best = cand
    return best


def normalise_date(m: re.Match) -> str | None:
    months = {mn.lower(): i for i, mn in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
    g = m.groups()
    try:
        if g[1].lower()[:3] in months:                 # 12 August 2026
            return f"{int(g[2]):04d}-{months[g[1].lower()[:3]]:02d}-{int(g[0]):02d}"
        a, b, c = (int(x) for x in g)
        if a > 31:                                      # 2026-08-12
            return f"{a:04d}-{b:02d}-{c:02d}"
        return f"{c:04d}-{b:02d}-{a:02d}"                # 12-08-2026
    except Exception:
        return None


def extract(path: Path, ocr_if_empty: bool = True) -> BillFacts:
    text, ocr = pdf_text(path, ocr_if_empty=ocr_if_empty)
    facts = BillFacts(path=str(path), text=text, ocr_used=ocr)

    facts.gstins = sorted(set(GSTIN_RE.findall(text)))

    seen: set[str] = set()
    for m in REF_RE.finditer(text.upper()):
        tok = m.group()
        if tok in REF_STOPWORDS or tok in facts.gstins or tok in seen:
            continue
        if not any(ch.isdigit() for ch in tok):
            continue
        digits = sum(ch.isdigit() for ch in tok)
        if digits < 4:
            continue
        seen.add(tok)
        facts.refs.append(tok)
    # Longest, most digit-dense first — real invoice numbers beat stray codes.
    facts.refs.sort(key=lambda t: (sum(c.isdigit() for c in t), len(t)), reverse=True)

    dates: list[str] = []
    for rx in DATE_RES:
        for m in rx.finditer(text):
            d = normalise_date(m)
            if d and d not in dates:
                dates.append(d)
    facts.dates = dates

    facts.amounts = sorted({v for v in (_to_float(m.group()) for m in MONEY_RE.finditer(text)) if v}, reverse=True)
    facts.grand_total = find_grand_total(text) or (facts.amounts[0] if facts.amounts else None)
    return facts
