#!/usr/bin/env python3
"""Diff the researched ideal assortment against ARY's live catalogue.

The demand corpus (assort/research/demand/*.json) holds, per category, the SKU lines
a store serving Baru Sahib should carry — built deliberately blind to ARY's own
catalogue. This script matches each of those lines against the live database and
writes the coverage verdict into assort/research/coverage/, which is what
`ary assort gaps` reads.

Matching is by NAME across every product group, never by ARY's category tag: the
tree is provably unreliable for this question (Loose Milk is filed under "Mini
Meals", curd under "Others", and the "Mobile" tag understated mobile accessories
by 37x). One SQL statement per category keeps it fast.

Search terms per line come from the researcher's own `examples` field — real Indian
brand names — plus the distinctive nouns in the line description. Stopwords and
generic retail words are dropped, because a term like "pack" or "fresh" matches
thousands of rows and would mark everything covered.

Verdicts, matching `ary assort gaps --state`:
    covered  a matching SKU sold at least --min-sales in the window
    dormant  a SKU exists but sold nothing, or sold under the threshold --
             listed rather than genuinely stocked
    missing  no SKU in the catalogue matches

The --min-sales floor matters. Without it, "Amul Taaza" selling Rs 308 across a
whole year marks fresh toned milk "covered" for 5,000 people. A line that turns a
few hundred rupees a year is a dead listing, not a range.

Usage
    python3 assort/bin/diff.py                 # every category in the corpus
    python3 assort/bin/diff.py dairy frozen    # only these
    python3 assort/bin/diff.py --months 24 --min-sales 10000
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ASSORT = HERE.parent.parent
ARY = ASSORT.parent / "ary"
DEMAND = ASSORT / "research" / "demand"
OUT = ASSORT / "research" / "coverage"

# Words that match too much to be evidence of anything. Kept deliberately long:
# a false "covered" is worse than a false "missing", because it hides a real gap.
STOP = {
    # grammar
    "the", "and", "or", "of", "a", "an", "in", "for", "with", "to", "as", "at", "on",
    "by", "from", "per", "its", "it", "is", "are", "be", "no", "not", "any", "all",
    # generic retail
    "pack", "packs", "packet", "sachet", "bottle", "bottles", "box", "jar", "tin",
    "tub", "pouch", "pouches", "can", "cans", "bag", "loose", "fresh", "premium",
    "regular", "standard", "value", "economy", "family", "single", "double", "large",
    "small", "medium", "mini", "big", "size", "sizes", "unit", "units", "piece",
    "pieces", "item", "items", "product", "products", "range", "assorted", "mixed",
    "mix", "variety", "type", "types", "line", "lines", "sku", "skus", "brand",
    "brands", "local", "national", "imported", "indian", "daily", "workhorse",
    "counter", "shelf", "store", "retail", "bulk", "kg", "gm", "gms", "ltr", "litre",
    "liter", "ml", "grams", "gram", "each", "count", "pcs", "nos",
    # descriptors that are true of half the catalogue
    "good", "best", "better", "new", "old", "high", "low", "light", "heavy", "long",
    "short", "hot", "cold", "warm", "cool", "dry", "wet", "raw", "whole", "half",
    "full", "plain", "sweet", "salted", "unsalted", "natural", "pure", "organic",
    "and/or", "etc", "eg", "ie", "or/and",
}


def words_of(text: str) -> list[str]:
    """Distinctive lowercase words from a phrase, order preserved."""
    text = re.sub(r"\([^)]*\)", " ", text or "")
    # drop pack sizes: "Amul Taaza 500 ml" -> "Amul Taaza"
    text = re.sub(r"\b\d+\s*(ml|l|ltr|litre|g|gm|gms|kg|mg|n|pcs|tab|tabs)\b", " ", text, flags=re.I)
    text = re.sub(r"[^A-Za-z0-9 &'-]", " ", text)
    out, seen = [], set()
    for w in text.split():
        lw = w.lower()
        if len(lw) < 3 or lw in STOP or lw in seen:
            continue
        seen.add(lw)
        out.append(lw)
    return out


def probes_for(line: dict) -> list[list[str]]:
    """AND-groups to test for one ideal SKU line, most specific first.

    A single generic word is never enough: "milk" matches 389 ARY SKUs, so it would
    mark "A2 desi-cow milk", "lactose-free milk" and "UHT tetra milk" all covered off
    one loose-milk counter. Each probe is therefore a GROUP of words that must ALL
    appear in the same product name — the line's own qualifiers, or a multi-word brand.
    """
    groups: list[list[str]] = []

    def add(g: list[str]) -> None:
        g = [w for w in g if w]
        if not g or g in groups:
            return
        groups.append(g)

    # 1. multi-word brand examples: "Mother Dairy", "Nestle Everyday"
    ex = line.get("examples") or ""
    for chunk in re.split(r"[,;/]|\band\b|\bor\b|\+", ex):
        w = words_of(chunk)
        if len(w) >= 2:
            add(w[:2])
        elif len(w) == 1:
            add([w[0]])          # a single distinctive brand token is acceptable

    # 2. the line's own qualifiers, ANDed — the specific test
    lw = words_of(line.get("line") or "")
    if len(lw) >= 3:
        add(lw[:3])
    if len(lw) >= 2:
        add(lw[:2])
        add([lw[0], lw[-1]])
    if len(lw) == 1:
        add([lw[0]])

    return groups[:12]


# Words that are real enough to survive `words_of` but far too generic to prove a
# commodity on their own. 'desi' alone matched "Loose Desi Ghee" and credited a toor
# dal line with Rs 16 lakh; 'tata' spans salt, tea, dal and pulses.
BROAD_STOP = {
    "desi", "tata", "grade", "grades", "tier", "everyday", "economy", "unpolished",
    "polished", "split", "splits", "broken", "pieces", "whole", "loose", "packet",
    "origin", "quality", "table", "cooking", "home", "ready", "instant", "classic",
    "special", "super", "extra", "fine", "coarse", "powder", "seed", "seeds",
    "grain", "grains", "oil", "juice", "drink", "food", "snack", "sweet", "salt",
    "sugar", "milk", "water", "cream", "paste", "sauce", "mix", "kit", "set",
    "adult", "baby", "kids", "child", "children", "student", "students", "family",
    "families", "staff", "elderly", "canteen", "mess", "langar", "institutional",
}


def broad_terms(line: dict) -> list[str]:
    """Single-word fallbacks, so a strict AND-group cannot fake a 'missing'.

    "Toor / arhar dal — economy grade, sold loose" ANDs to toor+arhar+dal and
    matches nothing, while ARY plainly stocks 12 arhar SKUs turning Rs 71,949.
    These broad terms catch that. A hit here proves ARY is IN the line's
    commodity, not that this exact pack or grade is on the shelf — the verdict
    records which kind of match it was.
    """
    out: list[str] = []
    for w in words_of(line.get("line") or "") + words_of(line.get("examples") or ""):
        if len(w) >= 4 and w not in out and w not in BROAD_STOP:
            out.append(w)
    return out[:10]


def sql_and(group: list[str]) -> str:
    """AND of LIKEs over ProductName for one probe group."""
    return " AND ".join(
        "p.ProductName LIKE '%" + w.replace("'", "''") + "%'" for w in group
    )


def run_probe(groups: list[list[str]], months: int) -> dict[str, dict]:
    """One SQL round-trip: for every AND-group, its SKU count and window sales."""
    if not groups:
        return {}
    cases = []
    for i, g in enumerate(groups):
        cond = sql_and(g)
        cases.append(
            f"SUM(CASE WHEN {cond} THEN 1 ELSE 0 END) AS n{i}, "
            f"SUM(CASE WHEN {cond} THEN ISNULL(s.value,0) ELSE 0 END) AS v{i}"
        )
    q = (
        "SELECT " + ", ".join(cases) + " FROM ProductMaster p LEFT JOIN ("
        "SELECT d.ProductID, SUM(d.Quantity*d.SaleRate) AS value "
        "FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber=d.SerialNumber "
        f"WHERE h.VoucherDate >= DATEADD(month,-{months},CAST(GETDATE() AS date)) "
        "GROUP BY d.ProductID) s ON s.ProductID = p.ProductID"
    )
    r = subprocess.run(
        [str(ARY), "query", q, "--json", "--timeout", "5m", "-q"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ary query failed: {r.stderr.strip()[:300]}")
    rows = json.loads(r.stdout or "[]")
    if not rows:
        return {}
    row = rows[0]
    out = {}
    for i, g in enumerate(groups):
        out[" + ".join(g)] = {
            "skus": int(float(row.get(f"n{i}") or 0)),
            "sales": float(row.get(f"v{i}") or 0),
        }
    return out


def main(argv: list[str]) -> int:
    months = 12
    min_sales = 5000.0
    if "--months" in argv:
        i = argv.index("--months")
        months = int(argv[i + 1])
        del argv[i:i + 2]
    if "--min-sales" in argv:
        i = argv.index("--min-sales")
        min_sales = float(argv[i + 1])
        del argv[i:i + 2]
    wanted = [a for a in argv if not a.startswith("-")]

    files = sorted(DEMAND.glob("*.json"))
    if wanted:
        files = [f for f in files if f.stem in wanted]
    if not files:
        print(f"no demand corpus to diff in {DEMAND}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    grand = {"covered": 0, "dormant": 0, "missing": 0}

    print(f"window {months}m  ·  covered floor Rs {min_sales:,.0f} of sales\n")
    print(f"{'category':16} {'lines':>5} {'spec':>4} {'broad':>5} {'dorm':>5} {'miss':>5} {'must-miss':>9}  line coverage")
    print("-" * 78)

    for f in files:
        d = json.load(open(f))
        cat = d.get("category") or f.stem
        lines = d.get("skuLines", [])

        # collect every AND-group AND every broad single term, probe in few trips
        per_line = [(l, probes_for(l), broad_terms(l)) for l in lines]
        all_groups: list[list[str]] = []
        for _, gs, bts in per_line:
            for g in gs:
                if g not in all_groups:
                    all_groups.append(g)
            for b in bts:
                if [b] not in all_groups:
                    all_groups.append([b])

        hits: dict[str, dict] = {}
        for i in range(0, len(all_groups), 60):
            hits.update(run_probe(all_groups[i:i + 60], months))

        out_lines = []
        tally = {"covered": 0, "dormant": 0, "missing": 0}
        must_missing = []
        for line, gs, bts in per_line:
            best_skus = 0
            best_sales = 0.0
            evidence = ""
            for g in gs:
                key = " + ".join(g)
                h = hits.get(key)
                if not h or not h["skus"]:
                    continue
                # a match that proves SALES beats one that only proves listing;
                # among selling matches prefer the most specific (fewest SKUs)
                better = (
                    (h["sales"] > 0 and best_sales == 0)
                    or (h["sales"] > 0 and best_sales > 0 and h["skus"] < best_skus)
                    or (h["sales"] == 0 and best_sales == 0 and
                        (best_skus == 0 or h["skus"] < best_skus))
                )
                if better:
                    best_skus, best_sales, evidence = h["skus"], h["sales"], key
            quality = "specific" if evidence else ""

            # fall back to broad single terms before declaring anything missing
            if best_sales < min_sales:
                for b in bts:
                    h = hits.get(b)
                    if not h or not h["skus"]:
                        continue
                    if h["sales"] > best_sales or (best_sales < min_sales and h["skus"] > best_skus):
                        best_skus, best_sales, evidence = h["skus"], h["sales"], b
                        quality = "broad"

            if best_sales >= min_sales:
                state = "covered"
            elif best_skus > 0:
                state = "dormant"
            else:
                state = "missing"
            tally[state] += 1
            ess = (line.get("essentiality") or "").lower()
            if state == "missing" and "must" in ess:
                must_missing.append(line.get("line"))
            out_lines.append({
                "line": line.get("line"),
                "state": state,
                "essentiality": line.get("essentiality"),
                "cohort": line.get("cohort"),
                "examples": line.get("examples"),
                "arySkus": best_skus,
                "arySales12m": round(best_sales, 2),
                "matchQuality": quality,
                "evidence": (
                    (f"name contains ALL of: {evidence}" if quality == "specific"
                     else f"broad commodity match on '{evidence}' — ARY is in this line, "
                          f"but this exact pack/grade is unproven")
                    if evidence else
                    "no product name matches, specific or broad: " +
                    "; ".join(list(bts)[:6])
                ),
            })

        key = [l for l in out_lines
               if "must" in (l["essentiality"] or "").lower()
               or "should" in (l["essentiality"] or "").lower()]
        # Coverage counts ONLY line-level (specific) matches. A broad commodity hit
        # proves ARY is in the commodity, not that this pack/grade is on the shelf,
        # so counting it as coverage would report 100% for every food category.
        n_spec = sum(1 for l in key
                     if l["state"] == "covered" and l.get("matchQuality") == "specific")
        n_broad = sum(1 for l in key
                      if l["state"] == "covered" and l.get("matchQuality") == "broad")
        cov_pct = round(100 * n_spec / len(key), 1) if key else 0.0
        broad_pct = round(100 * n_broad / len(key), 1) if key else 0.0

        doc = {
            "category": cat,
            "categoryName": d.get("categoryName"),
            "windowMonths": months,
            "minSalesFloorInr": min_sales,
            "method": "name-match across all product groups (ARY's category tree is unreliable "
                      "for this question); terms from the researcher's brand examples plus "
                      "distinctive nouns, generic retail words dropped; a line counts as "
                      f"covered only above Rs {min_sales:,.0f} of {months}-month sales",
            "coveragePct": cov_pct,
            "commodityOnlyPct": broad_pct,
            "lines": out_lines,
            "mustHaveMissing": must_missing,
            "surprises": [],
        }
        (OUT / f"{cat}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False))

        for k in tally:
            grand[k] += tally[k]
        bar = "#" * int(cov_pct / 4) + "-" * int(broad_pct / 4)
        print(f"{cat[:16]:16} {len(lines):>5} {n_spec:>4} {n_broad:>5} {tally['dormant']:>5} "
              f"{tally['missing']:>5} {len(must_missing):>9}  {cov_pct:>5.1f}% {bar}")

    n = sum(grand.values())
    print("-" * 78)
    print(f"{'TOTAL':16} {n:>5} {grand['covered']:>4} {grand['dormant']:>5} {grand['missing']:>5}")
    print(f"\nwritten to {OUT}\nnow run:  ary assort gaps --state missing")
    print("\nHOW TO READ THIS")
    print("  spec   the line's own qualifiers all appear in one ARY product name. Real coverage.")
    print("  broad  only the commodity word matched -- ARY is IN this line, but this pack,")
    print("         grade or brand is unproven. NOT counted in the coverage %.")
    print("  dorm   a SKU exists but sold nothing, or under the floor. Listed, not stocked.")
    print("  miss   nothing matches, specific or broad. This is the finding worth acting on.")
    print("\nBefore acting on ANY 'miss', re-check it with `ary assort probe <commodity words>`.")
    print("The first version of this script called arhar dal and almonds missing while ARY was")
    print("selling Rs 8.7 lakh of them -- see assort/data/VERIFIED-FACTS.md section 33.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
