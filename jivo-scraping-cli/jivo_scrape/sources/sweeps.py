"""Platform sweep loader + defensive display fields + exact listing identity.

Every platform's ``result.json`` carries an ``allRows`` list, but the exact
field names inside each row VARY per platform (amazon vs blinkit vs flipkart
disagree on where the name/price/availability live). Nothing here ever assumes
a key exists — missing fields degrade to ``None`` instead of raising.

READ-ONLY: this module only ever opens data files for reading.

Date axis (per SOURCES.md):
- ``today``   -> live ``result.json``; if ``partial: true`` fall back to
                ``result.last-good.json`` and flag it.
- ``yesterday`` / ``YYYY-MM-DD`` -> per-platform sweeps retain ONLY the live
                ``result.json`` + ``result.last-good.json`` (the today.prev/
                snapshots are markdown reports, not structured rows, and dated
                exports are xlsx). So we serve the current live/last-good
                snapshot and say so plainly in ``info['date_note']`` rather than
                pretend we have historical rows.
"""

import os

from jivo_scrape import identity, util


# Evidence-backed source contracts observed in the live result.json files.
# Do not add convenient aliases here: an operational join is valid only when
# the platform's authoritative listing-ID field is present.
LISTING_ID_FIELDS = {
    "amazon": ("asin", "asin"),
    "amazon-fresh": ("asin", "asin"),
    "amazon-now": ("asin", "asin"),
    "flipkart": ("fsn", "fsn"),
    "flipkart-minutes": ("fk_pid", "fk_pid"),
    "zepto": ("variant_id", "variant_id"),
    "blinkit": ("prid", "prid"),
    "bigbasket": ("sku_id", "sku_id"),
    "swiggy-instamart": ("listing_id", "listing_id"),
}

# --- Field-name candidates (priority order) for values that vary per platform ---
# sku_raw is the most consistently human-readable name; canonical is last because
# on some platforms (e.g. flipkart) it is an opaque code, not a real name.
NAME_FIELDS = (
    "product_name",
    "fk_name",
    "sku_raw",
    "title",
    "product",
    "name",
    "item",
    "canonical",
)
PRICE_FIELDS = (
    "sale",
    "offer_sale",
    "base_sale",
    "selling_price",
    "sp",
    "price",
    "base_price",
)
MRP_FIELDS = ("mrp", "mrp_price", "list_price")
PINCODE_FIELDS = ("pincode", "pin", "pin_code")
INSTOCK_FIELDS = ("in_stock", "inStock", "is_in_stock", "oos")
AVAIL_TEXT_FIELDS = (
    "availability_text",
    "avail_status",
    "availability",
    "listing_status",
    "avail_button",
)


def _first(row, fields):
    """First present, non-empty value among candidate field names, else None."""
    if not isinstance(row, dict):
        return None
    for f in fields:
        if f in row:
            v = row[f]
            if v is not None and v != "":
                return v
    return None


def _num(v):
    """Coerce a price-ish value to int/float, else None (never raises)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        s = str(v).replace(",", "").replace("₹", "").replace("Rs", "").strip()
        if s in ("", "-", "na", "n/a", "none", "null"):
            return None
        return float(s) if ("." in s or "e" in s.lower()) else int(s)
    except (ValueError, TypeError):
        return None


def product_name(row):
    """Best human-readable product name for display, or None."""
    return _first(row, NAME_FIELDS)


def price(row):
    """Selling price as a number, or None."""
    return _num(_first(row, PRICE_FIELDS))


def mrp(row):
    """MRP as a number, or None."""
    return _num(_first(row, MRP_FIELDS))


def pincode(row):
    """Pincode string, or None. National listings carry '-' -> None."""
    v = _first(row, PINCODE_FIELDS)
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-"):
        return None
    return s


def _to_bool(v):
    """True / False / None from the many availability encodings seen in the wild."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        low = v.strip().lower()
        if low in (
            "1",
            "true",
            "yes",
            "y",
            "in_stock",
            "instock",
            "available",
            "listed_in_stock",
        ):
            return True
        if low in ("0", "false", "no", "n", "oos", "out_of_stock", "unavailable", ""):
            return False
        if "outofstock" in low or "out of stock" in low or "unavailable" in low:
            return False
        if "instock" in low or "in stock" in low or "listed_in_stock" in low:
            return True
    return None


def in_stock(row):
    """Tri-state availability: True (in stock) / False (OOS) / None (unknown).

    Discovered defensively across the platform-specific encodings:
    numeric in_stock, schema.org availability URLs, bigbasket avail_status
    codes, blinkit listing_status, amazon availability_text prose.
    """
    if not isinstance(row, dict):
        return None
    for f in INSTOCK_FIELDS:
        if f in row and row[f] is not None:
            b = _to_bool(row[f])
            # 'oos' field carries inverted semantics if it ever appears
            if f == "oos" and isinstance(b, bool):
                return not b
            if b is not None:
                return b
    av = row.get("availability")
    if isinstance(av, str):
        b = _to_bool(av)
        if b is not None:
            return b
    avs = row.get("avail_status")
    if avs is not None:
        s = str(avs).strip()
        if s:
            # bigbasket: '001' family = orderable; all-zero / empty = not
            return s.strip("0") != ""
    ls = row.get("listing_status")
    if isinstance(ls, str) and ls:
        return _to_bool(ls)
    at = row.get("availability_text")
    if isinstance(at, str) and at:
        return _to_bool(at)
    return None


def avail_text(row):
    """Raw availability descriptor for display, or None."""
    return _first(row, AVAIL_TEXT_FIELDS)


def listing_identity(row, platform):
    """Return the exact source listing ID, kind, and qualified observed key.

    Unknown platforms and absent/empty authoritative fields deliberately yield
    no ID. Product names and alternate identifier-looking fields are ignored.
    """
    normalized_platform = (
        platform.strip().lower() if isinstance(platform, str) else None
    )
    contract = LISTING_ID_FIELDS.get(normalized_platform)
    if contract is None:
        return {"listing_id": None, "listing_id_kind": None, "listing_key": None}
    field, kind = contract
    raw_id = row.get(field) if isinstance(row, dict) else None
    listing_id = None
    if raw_id is not None and not isinstance(raw_id, bool):
        candidate = str(raw_id).strip()
        listing_id = candidate or None
    return {
        "listing_id": listing_id,
        "listing_id_kind": kind,
        "listing_key": identity.listing_key_for(normalized_platform, listing_id),
    }


def normalize(row, platform, identity_store=None):
    """Uniform output row with exact listing identity and optional enrichment."""
    observed = listing_identity(row, platform)
    normalized = {
        "platform": platform,
        "product": product_name(row),
        "price": price(row),
        "mrp": mrp(row),
        "pincode": pincode(row),
        "in_stock": in_stock(row),
        "availability": avail_text(row),
    }
    normalized.update(observed)
    if identity_store is not None:
        normalized.update(
            identity_store.enrich_listing(platform, observed["listing_id"])
        )
    return normalized


def _pin_match(row, want):
    p = pincode(row)
    return p is not None and str(want).strip() == p


def select_platforms(platform_arg):
    """(list_of_platforms, error_or_None). None/empty arg => all platforms."""
    if not platform_arg:
        return list(util.PLATFORMS), None
    p = str(platform_arg).strip().lower()
    if p in util.PLATFORMS:
        return [p], None
    return [], (
        "unknown platform %r; choose one of: %s"
        % (platform_arg, ", ".join(util.PLATFORMS))
    )


def load_platform(platform, date_label):
    """Load one platform's rows + source info.

    Returns {'rows': [...raw rows...], 'info': {...}} where info carries
    path, freshness, partial_fallback, missing and (for non-today dates) a
    date_note explaining the live/last-good limitation.
    """
    pdir = os.path.join(util.PLATFORMS_DIR, platform)
    live = os.path.join(pdir, "result.json")
    lastgood = os.path.join(pdir, "result.last-good.json")
    info = {
        "platform": platform,
        "path": None,
        "freshness": None,
        "partial_fallback": False,
        "date_note": None,
        "missing": False,
    }

    data = None
    if os.path.exists(live):
        try:
            data = util.load_json(live)
        except (ValueError, OSError):
            data = None
    if not isinstance(data, dict):
        info["missing"] = True
        return {"rows": [], "info": info}

    src = live
    if data.get("partial") and os.path.exists(lastgood):
        try:
            good = util.load_json(lastgood)
            if isinstance(good, dict):
                data = good
                src = lastgood
                info["partial_fallback"] = True
        except (ValueError, OSError):
            pass  # keep the partial live data if last-good is unreadable

    rows = data.get("allRows")
    if not isinstance(rows, list):
        rows = []

    info["path"] = src
    info["freshness"] = util.freshness(src)
    if date_label != "today":
        info["date_note"] = (
            "per-platform sweeps retain only live result.json + last-good; no "
            "structured rows are kept for '%s' — showing current live/last-good "
            "snapshot" % date_label
        )
    return {"rows": rows, "info": info}


def gather(platforms, date_label, listing_targets=None, pincode_filter=None):
    """Load + filter rows for each platform.

    Returns a list of {'platform', 'rows' (raw), 'info'} preserving platform
    order. ``listing_targets`` is an exact set of ``(platform, listing_id)``
    tuples; ``None`` retains the whole catalogue. Pincode is exact.
    """
    out = []
    for p in platforms:
        res = load_platform(p, date_label)
        rows = res["rows"]
        if listing_targets is not None:
            rows = [
                row
                for row in rows
                if (p.lower(), listing_identity(row, p)["listing_id"])
                in listing_targets
            ]
        if pincode_filter:
            rows = [r for r in rows if _pin_match(r, pincode_filter)]
        out.append({"platform": p, "rows": rows, "info": res["info"]})
    return out


def sources_meta(gathered):
    """Build the freshness/fallback/notes portion of meta from gathered results."""
    freshness = {}
    fallbacks = []
    missing = []
    notes = []
    for g in gathered:
        info = g["info"]
        freshness[g["platform"]] = info["freshness"]
        if info.get("partial_fallback"):
            fallbacks.append(g["platform"])
        if info.get("missing"):
            missing.append(g["platform"])
        note = info.get("date_note")
        if note and note not in notes:
            notes.append(note)
    return {
        "freshness": freshness,
        "partial_fallback": bool(fallbacks),
        "partial_fallback_platforms": fallbacks,
        "missing_sources": missing,
        "notes": notes,
    }


def mode(values):
    """Most-common value (first-seen wins ties), or None. Pure-stdlib, no import."""
    counts = {}
    order = []
    for v in values:
        if v is None:
            continue
        if v not in counts:
            counts[v] = 0
            order.append(v)
        counts[v] += 1
    if not order:
        return None
    best = order[0]
    for v in order:
        if counts[v] > counts[best]:
            best = v
    return best


# --- tiny plain-text table renderer (shared by the three commands) ---
def table(headers, rows):
    """Left-aligned, space-padded columns. None/empty cells render blank."""
    heads = [str(h) for h in headers]
    srows = [["" if c is None else str(c) for c in r] for r in rows]
    widths = [len(h) for h in heads]
    for r in srows:
        for i, c in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(c))

    def fmt(cells):
        return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells))

    lines = [fmt(heads), "  ".join("-" * w for w in widths)]
    lines += [fmt(r) for r in srows]
    return "\n".join(lines)


def fmt_price(v):
    if v is None:
        return "-"
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return "₹%s" % v


def fmt_stock(v):
    if v is True:
        return "in"
    if v is False:
        return "OOS"
    return "?"
