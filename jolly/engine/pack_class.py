#!/usr/bin/env python3
"""
JIVO Mark 4 — which PACK and which BOTTLE a finished good is, read from its RECIPE.

R15 (rulebook, 6 Sep 2026): **the pack of a product comes from its BOM container
child, never from the plan sheet's pack-type column.** Seven "15 LTR PET" rows and
SO Olive 5 L are TINS in SAP's own recipe, and a tin only fills on the Tin Head
(or, at 3 L / 5 L, on the 6 Head). Mark 3 read the sheet, believed "PET", and put
15-litre tins on Clear Pack — the mistake this module exists to make impossible.

The recipe also says HOW MANY containers make one saleable piece. Four "1 LTR +
1 LTR COMBO" rows buy two 1-litre 40 g bottles per piece: the line fills 1-litre
bottles, twice per piece, and `fills_per_piece` carries that so line time is
counted in bottles and not in sets.

One implementation, so the rule cannot drift. Callers TODAY:
  * reference/build_mark4_rulebook.py — pre-computes `rulebook.sku_pack` for the
    plan sheet's rows;
  * engine/_pack_class_test.py — the regression.
Planned (not yet wired — grep before believing this comment):
  * live/freeze_live.py — to class any SKU the rulebook did not pre-compute (A18);
  * live/gen_live.py — to re-derive it as acceptance check AC06.

What it returns:
  slot            — the Mark 4 LINE SLOT: 1L / 2L / 3L / 4L / 5L / 15L / POUCH /
                    DRUM, or None when nothing names a size. A tin's slot is its
                    size; TIN is a family, not a slot.
  family          — the BOTTLE the line has to handle: 26G / ROUND-23.8G / 40G /
                    52G / 75G / SMALL / HDPE / TIN / ANY, plus DRUM, POUCH,
                    1L-OTHER (a 1 L bottle whose grams the item name does not
                    say), "<n>G" for a gram weight outside the known five, and
                    UNKNOWN. Eligibility on JP / Clear Pack / 10 Head is
                    bottle-specific (A03), which is why the family travels.
  fills_per_piece — containers the line fills per saleable piece (1, or 2 for a
                    combo set).
  fills_basis     — the sentence that says WHY it is that many. A recipe quantity
                    is only a count of containers when the container's own printed
                    size confirms it (2 x "1 LTR" = a 2 L piece), or, when nothing
                    is printed, when the child is counted in pieces. A container
                    measured in KGS carries kilograms, not a count: 15 kg of steel
                    is one 200 L drum, never fifteen of them (B17).
  litres_per_fill — litres in ONE container = litres_per_piece / fills_per_piece,
                    or the container's own printed size when the piece has none.
                    This, not the piece, decides the slot.
  container_litres— the size printed on the container item, for cross-checking:
                    a "15 KGS" tin is filled to 16.48 L in a 15 LTR tin, so the
                    two legitimately differ by a tenth. A wider gap is published
                    as container_disagrees rather than left to be discovered.
  container_ratio — litres_per_fill / container_litres, or None.
  container_disagrees — that ratio outside 0.8-1.25.
  engine_slot     — the SAME pack in the engine's older vocabulary, where every
                    tin is one "TIN" bucket. See engine_slot() — the two
                    vocabularies are not interchangeable.

Stdlib only. No I/O, no business system: pass in the BOM and the item names.
"""
import re

# The line slots a pack can occupy — published as rulebook.pack_class.slots.
SLOTS = ["1L", "2L", "3L", "4L", "5L", "15L", "POUCH", "DRUM"]

# The vocabulary engine/august_sim.py slot() and live/gen_live.py slot_of() use, and the
# keys sim/*-inputs.json `lines` is written with. (live/freeze_live.py had a third copy;
# WS3 deleted it — the freeze takes its slots from the rulebook now. gen keeps its own
# because the -sep path still needs it.) It has TIN as a SLOT: every tin, 3 L to 15 kg, in one bucket at
# one pieces-per-hour. Mark 4 splits tins by size, so the two vocabularies differ
# and a rulebook speed must be mapped with engine_slot() before it is merged into
# `lines` — never keyed straight across.
ENGINE_SLOTS = ["1L", "2L", "3L", "4L", "5L", "15L", "TIN", "POUCH", "DRUM"]

# The bottle families, with the PM codes that define them where they are a fixed
# list — published verbatim as rulebook.pack_class.families. Insertion order is
# the published order; keep it.
FAMILIES = {
    "26G": ["PM0000851", "PM0000584"],
    "ROUND-23.8G": ["PM0000054"],
    "40G": ["PM0000194"],
    "52G": ["PM0000055", "PM0000195", "PM0000121"],
    "75G": ["PM0000517", "PM0000792"],
    "SMALL": "any pack < 0.95 L (bottle known or not)",
    "HDPE": "HDPE/PET 3 L and 5 L bottles",
    "TIN": "any TIN item",
    "ANY": "no family rule",
}

# Every family label pack_class() can return. The five gram families above are
# matched by weight, not by PM code, so a sixth weight yields a "<n>G" label that
# no line names — it is eligible nowhere until someone rules on it.
ALL_FAMILIES = list(FAMILIES) + ["DRUM", "POUCH", "1L-OTHER", "UNKNOWN"]

# A BOM child whose name matches this is the container...
CONTAINER_RE = re.compile(r"BOTTLE|JAR|\bTIN\b|TIN \d|DRUM|POUCH|CAN\b|CONTAINER|BARREL|JERRY")
# ...unless it is one of the things that only MENTIONS the container: "CARTON TIN
# TOP", "LABEL 2 LTR ... HANDLE BOTTLE", "CAPS 250 MLS GLASS BOTTLE", "TIN STRIP".
# 22 of the 84 plan recipes list one of these beside the real container; today the
# real one happens to come first in every case, which is luck, not a rule.
NOT_CONTAINER_RE = re.compile(r"CARTON|LABEL|\bCAPS?\b|SHRINK|\bTAPE\b|TIKKI|STICKER|STRIP|SLEEVE|\bBOX\b|SEAL|WAD|\bBAG\b")
TIN_RE = re.compile(r"\bTIN\b|TIN \d")
GRAMS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*G(?:M|MS|RM|R)?\b")
# The size printed on a container item, for the cross-check only. Millilitres and
# kilograms before litres; the grams in "PET BOTTLE 1 LTR 40 GMS" are the BOTTLE's
# own weight, never its fill, so this deliberately does not read them.
SIZE_ML_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:MLS|ML)\b")
SIZE_KG_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:KGS|KG)\b")
SIZE_L_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:LTRS|LTR|LITRES|LITRE|LITER|L)\b")

SMALL_MAX_L = 0.95          # below this the pack is a small bottle (200/250/500 ml)
GRAM_TOL = 1.0              # a bottle within 1 g of 26/40/52/75 is that family
MULTIPACK_MIN = 1.5         # this many containers per piece and up = a combo set
DENSITY_G_PER_L = 910.0     # C-0050 / plan_units.py — a KGS tin is filled to weight
FILLS_TOL = 0.05            # piece / container size must land within 5% of the quantity
CONTAINER_TOL = (0.8, 1.25)  # a fill outside this share of the printed size is flagged

# A BOM quantity is a COUNT of containers only when the child is counted. Units
# that measure weight, length or volume carry an AMOUNT of the child, so "15 KGS
# of MS COATED DRUM 200 LTR" is 15 kg of steel — one drum, not fifteen. The plan's
# three pouch films are the live case (0.0083 KGS of roll per piece).
MEASURE_UOMS = frozenset("""KGS KG GMS GM GRM GRMS LTR LTRS LTS L ML MLS MTR MTRS
    MTS M CM MM TON TONS MT SQM SQF ROLL ROLLS SET BDL""".split())
# ...and these count discrete objects. Blank / NULL / missing is treated as a count,
# because SAP simply not filling the field is not evidence of a measure.
COUNT_UOMS = frozenset(["PCS", "PC", "NOS", "NO", "EA", "EACH", "UNIT", "UNITS",
                        "DRM", "PKT", "", "NULL", "NONE"])


def _f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _size(v):
    """A positive size, or None. A missing, blank, zero or negative litres figure
    is NOT a small pack — it is an unknown pack, and says so."""
    x = _f(v, 0.0)
    return x if x > 0 else None


def slot_by_litres(litres, pack_type=""):
    """The line slot for ONE container of `litres`. `pack_type` only says DRUM /
    POUCH / TIN — a tin over 12 L is the 15 L slot whatever its net weight
    (12/13/15 KGS tins all fill in the same tin, plan_units.py). None when no
    size is known and the pack type does not settle it on its own."""
    l = _size(litres)
    pt = str(pack_type or "").upper()
    if "DRUM" in pt: return "DRUM"
    if "POUCH" in pt: return "POUCH"
    if l is None: return None
    if pt == "TIN":
        if l >= 12: return "15L"
        if l <= 3.05: return "3L"
        return "5L"
    if l <= 1.05: return "1L"
    if l <= 2.05: return "2L"
    if l <= 3.05: return "3L"
    if l <= 4.05: return "4L"
    if l <= 5.05: return "5L"
    return "15L"


def container_litres(container_name):
    """The size printed on a container item ("TIN 15 LTR" -> 15.0, "GLASS BOTTLE
    500 MLS" -> 0.5), or None. Cross-check only — see the module docstring."""
    n = str(container_name or "").upper()
    m = SIZE_ML_RE.search(n)
    if m: return float(m.group(1)) / 1000.0
    m = SIZE_KG_RE.search(n)
    if m: return float(m.group(1)) * 1000.0 / DENSITY_G_PER_L
    m = SIZE_L_RE.search(n)
    if m: return float(m.group(1))
    return None


def container_of(code, bom, items):
    """The container child of `code`'s recipe: (item code, UPPERCASED name, qty
    per piece). (None, None, 0.0) when the BOM names no container (the three
    small packs of A16)."""
    for c, per in bom.get(code, []):
        n = (items.get(c, {}) or {}).get("name") or ""
        n = str(n).upper()
        if CONTAINER_RE.search(n) and not NOT_CONTAINER_RE.search(n):
            return c, n, _f(per)
    return None, None, 0.0


def fills_per_piece(qty, uom, piece_litres, printed_litres):
    """(how many containers make one saleable piece, why) — B17.

    A recipe quantity of 2 is only two containers when something says so. In order:
    a unit that measures rather than counts settles it at one; then the container's
    own printed size, which is arithmetic (a 2 L piece made of "1 LTR" bottles);
    then the unit, when the container prints no size. An unrecognised unit with
    nothing to confirm it stays at one and says which unit it was.
    """
    per = _f(qty)
    u = str(uom or "").strip().upper()
    if per < MULTIPACK_MIN:
        return 1, "one container per piece"
    n = int(per) if abs(per - round(per)) < 1e-6 else per
    if u in MEASURE_UOMS:
        return 1, f"recipe quantity {per:g} is {u}, an amount of the child and not a count of containers"
    if printed_litres and piece_litres:
        got = piece_litres / printed_litres
        if abs(got - per) <= max(FILLS_TOL * per, FILLS_TOL):
            return n, f"recipe quantity {per:g}, confirmed by the container's own printed size"
        return 1, (f"recipe quantity {per:g} is not a container count: the piece divided by the "
                   f"container's printed size is {got:.3g}")
    if u in COUNT_UOMS:
        return n, f"recipe quantity {per:g}, counted in {u or 'PCS'}"
    return 1, f"recipe quantity {per:g} in {u}, with no printed container size to confirm it"


def bottle_family(container_name, litres):
    """The 1-litre bottle family from the container's own name."""
    n = str(container_name or "").upper()
    l = _size(litres)
    g = GRAMS_RE.search(n)
    if g:
        gv = float(g.group(1))
        if "ROUND" in n: fam = "ROUND-23.8G"
        elif abs(gv - 26) < GRAM_TOL: fam = "26G"
        elif abs(gv - 40) < GRAM_TOL: fam = "40G"
        elif abs(gv - 52) < GRAM_TOL: fam = "52G"
        elif abs(gv - 75) < GRAM_TOL: fam = "75G"
        else: fam = f"{gv:g}G"
    else:
        fam = "1L-OTHER"
    if l is not None and l < SMALL_MAX_L: fam = "SMALL"
    return fam


def engine_slot(pack):
    """The same pack in the engine's older vocabulary (ENGINE_SLOTS), where every
    tin is one "TIN" bucket at one pieces-per-hour. Use this — never the Mark 4
    slot — when reading or writing sim/*-inputs.json `lines`, and never merge a
    rulebook speed into that table without it. None when the slot is unknown."""
    fam, slot = pack.get("family"), pack.get("slot")
    if slot in ("DRUM", "POUCH"): return slot
    if fam == "TIN": return "TIN"
    return slot


def sheet_slot(sku, pack_type, litres_per_piece):
    """The LEGACY, sheet-based slot: engine/august_sim.py slot(), reproduced once
    here so the copies in the engine, the freeze and gen can be replaced by an
    import and so the rulebook can publish where Mark 4 disagrees with it. It
    believes the plan sheet's pack-type column, which is the bug R15 fixes — do
    not call it to decide anything."""
    pt = str(pack_type or "").upper()
    s = str(sku or "").upper()
    l = _f(litres_per_piece)
    if "DRUM" in pt: return "DRUM"
    if "TIN" in pt or "KGS" in s: return "TIN"
    if "POUCH" in pt or "POUCH" in s: return "POUCH"
    for cap, name in ((1.05, "1L"), (2.05, "2L"), (3.05, "3L"), (4.05, "4L"), (5.05, "5L")):
        if l <= cap: return name
    return "15L"


def pack_class(code, bom, items, litres_per_piece, pack_type=""):
    """R15 for one FG: which container, how many per piece, which slot, which
    bottle. See the module docstring for every key returned.

    `pack_type` is the plan sheet's column — used ONLY when the recipe names no
    container, and to flag `sheet_disagrees` (the sheet says PET, the recipe uses
    a tin). Everything else comes from the BOM.
    """
    piece_l = _size(litres_per_piece)
    c, n, per = container_of(code, bom, items)
    cl = container_litres(n)
    uom = (items.get(c, {}) or {}).get("uom") if c else ""
    fills, why = fills_per_piece(per, uom, piece_l, cl)
    # The piece divided by the containers in it. With no size on the sheet the
    # container's OWN printed size is already ONE container — dividing it again
    # would halve an unsized combo and hand a 1 L bottle to a 500 ml machine.
    fill_l = (piece_l / fills) if piece_l is not None else cl
    out = lambda slot, family: _out(slot, family, c, n, pack_type, fills, why, fill_l, cl)
    if c is None:
        slot = slot_by_litres(fill_l, pack_type)
        return out(slot, "SMALL" if (slot == "1L" and fill_l < SMALL_MAX_L) else "UNKNOWN")
    if "DRUM" in n:
        return out("DRUM", "DRUM")
    if "POUCH" in n:
        return out("POUCH", "POUCH")
    if TIN_RE.search(n):
        return out(slot_by_litres(fill_l, "TIN"), "TIN")
    slot = slot_by_litres(fill_l, "PET")
    if slot is None:
        return out(None, "UNKNOWN")
    if slot == "1L":
        return out(slot, bottle_family(n, fill_l))
    if slot in ("3L", "5L"):
        return out(slot, "HDPE")
    return out(slot, "ANY")


def _out(slot, family, container, container_name, pack_type, fills, fills_why, fill_l, cl):
    ratio = round(fill_l / cl, 4) if (fill_l is not None and cl) else None
    p = dict(slot=slot, family=family, container=container, container_name=container_name,
             sheet_disagrees=(str(pack_type or "").upper() == "PET" and family == "TIN"),
             fills_per_piece=fills, fills_basis=fills_why,
             litres_per_fill=round(fill_l, 4) if fill_l is not None else None,
             container_litres=round(cl, 4) if cl is not None else None,
             container_ratio=ratio,
             container_disagrees=bool(ratio is not None and not CONTAINER_TOL[0] <= ratio <= CONTAINER_TOL[1]))
    p["engine_slot"] = engine_slot(p)
    return p
