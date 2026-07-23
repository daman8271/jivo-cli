#!/usr/bin/env python3
"""
Phase C — render the lossless linked Obsidian vault from raw/ capture.

One note per record (YAML frontmatter + lossless body + [[wikilinks]] for every
foreign key), a MOC hub per entity type (chunked for big sets), domain MOCs, and
a Home MOC. Mirrors the jivo-intel formula. Output: vault/  (becomes jivo-data-bank/factory/).
Deterministic, lossless: every captured field is written into a note.
"""

import json
import os
import re
import glob
import shutil
import math

ROOT = "/root/jivo-factory-intel"
RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "vault")
COMPANY = "JIVO_MART"

# Curated entities that are wikilink TARGETS — fixed short prefix so foreign
# keys resolve. (slug -> (prefix, title, keyfield))
TARGETS = {
    "vehicle-management__vehicles": ("veh", "Vehicle", "id"),
    "vehicle-management__vehicle-types": ("vty", "Vehicle Type", "id"),
    "vehicle-management__transporters": ("trn", "Transporter", "id"),
    "driver-management__drivers": ("drv", "Driver", "id"),
    "gate-core__arrivals": ("arr", "Gate Arrival", "id"),
    "barcode__pallets": ("pal", "Pallet", "id"),
    "barcode__boxes": ("box", "Barcode Box", "id"),
    "barcode__items__oitm": ("oitm", "SAP Item (OITM)", "item_code"),
    "po__vendors": ("ven", "Vendor", "vendor_code"),
    "po__warehouses": ("wh", "Warehouse", "warehouse_code"),
    "company__companies": ("comp", "Company", "id"),
    "person-gatein__person-types": ("ptype", "Person Type", "id"),
    "person-gatein__visitors": ("vis", "Visitor", "id"),
    "person-gatein__gates": ("pgate", "Gate", "id"),
}
# foreign-key field name -> target prefix
FK = {
    "vehicle": "veh",
    "vehicle_id": "veh",
    "vehicle_type": "vty",
    "vehicle_type_id": "vty",
    "transporter": "trn",
    "transporter_id": "trn",
    "driver": "drv",
    "driver_id": "drv",
    "arrival": "arr",
    "arrival_id": "arr",
    "pallet": "pal",
    "pallet_id": "pal",
    "source_pallet_id": "pal",
    "box": "box",
    "box_id": "box",
    "vendor": "ven",
    "vendor_code": "ven",
    "warehouse": "wh",
    "warehouse_code": "wh",
    "company": "comp",
    "company_id": "comp",
    "person_type": "ptype",
    "visitor": "vis",
    "gate": "pgate",
    "gate_in": "pgate",
    "gate_out": "pgate",
}
# SAP item-code fields -> bridge to product nodes (and link to the oitm note)
SAP_FIELDS = {
    "item_code",
    "material_code",
    "sku_code",
    "component_code",
    "po_item_code",
}


# derived/view endpoints to skip (dupes or status-filters of a base entity)
def is_derived(slug):
    if slug.endswith("__names"):
        return True
    if "__inspections__" in slug:  # status views of quality-control__inspections
        return True
    if (
        slug.endswith("__pending")
        and "inspections" not in slug
        and slug not in ("dispatch__bilty-grpo__pending", "grpo__service__pending")
    ):
        return True
    if slug.endswith("__low-stock") or slug.endswith("__actionable"):
        return True
    return False


def scalar(v):
    return v is None or isinstance(v, (str, int, float, bool))


def fk_value(v):
    """Return the id for a FK field whose value may be a scalar or a nested {id:..} dict."""
    if scalar(v):
        return v
    if isinstance(v, dict):
        for k in ("id", "pk", "code", "value"):
            if k in v and scalar(v[k]):
                return v[k]
    return None


def slugify(s):
    return re.sub(r"[^a-zA-Z0-9_-]", "-", str(s)).strip("-")[:80] or "x"


def title_of(rec, default):
    for k in (
        "name",
        "title",
        "item_name",
        "vehicle_number",
        "vehicle_no",
        "arrival_no",
        "entry_no",
        "full_name",
        "vendor_name",
        "warehouse_name",
        "barcode",
        "code",
        "number",
    ):
        if isinstance(rec.get(k), str) and rec[k].strip():
            return rec[k].strip()
    return default


def load(slug):
    f = os.path.join(RAW, slug + ".json")
    return json.load(open(f))


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    # Scan raw/*.json directly (robust to gap re-captures not yet in _manifest.json).
    list_slugs = []
    empty_slugs = []
    object_slugs = []
    for f in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        if os.path.basename(f) == "_manifest.json":
            continue
        d = json.load(open(f))
        ep, kind, cnt = d["endpoint"], d["kind"], d["count"]
        slug = os.path.basename(f)[:-5]
        if kind in ("list", "paginated_list"):
            if cnt == 0:
                empty_slugs.append((slug, ep))
            elif not is_derived(slug):
                list_slugs.append((slug, ep, cnt))
        elif kind == "object":
            object_slugs.append((slug, ep))

    # assign prefix+title+keyfield per rendered entity
    cfg = {}
    for slug, ep, cnt in list_slugs:
        d = load(slug)["data"]
        rec0 = d[0] if isinstance(d, list) and d else {}
        if slug in TARGETS:
            prefix, title, keyf = TARGETS[slug]
        else:
            keyf = "id" if "id" in rec0 else (next(iter(rec0), "id"))
            prefix = slug
            title = slug.split("__")[-1].replace("-", " ").title()
        cfg[slug] = {
            "prefix": prefix,
            "title": title,
            "keyf": keyf,
            "ep": ep,
            "count": cnt,
        }

    # PASS 1 — registry of existing note ids (prefix -> set(keys))
    registry = {}
    for slug, c in cfg.items():
        d = load(slug)["data"]
        keys = set()
        for rec in d if isinstance(d, list) else []:
            kv = rec.get(c["keyf"])
            if kv is not None:
                keys.add(str(kv))
        registry[c["prefix"]] = keys

    # PASS 2 — render notes
    note_index = {}  # slug -> list of (noteid, title)
    bridge_links = {}  # FG item_code -> set of note ids that reference it (for Phase D product bridge)
    total_notes = 0
    for slug, c in cfg.items():
        d = load(slug)["data"]
        folder = os.path.join(OUT, slug)
        os.makedirs(folder, exist_ok=True)
        idx = []
        used = set()  # guarantee unique note-ids (lossless)
        for rec in d if isinstance(d, list) else []:
            if not isinstance(rec, dict):
                continue
            kv = rec.get(c["keyf"])
            noteid = f"{c['prefix']}-{slugify(kv)}"
            if noteid in used:  # non-unique key field -> append index
                n = 2
                while f"{noteid}-{n}" in used:
                    n += 1
                noteid = f"{noteid}-{n}"
            used.add(noteid)
            title = title_of(rec, f"{c['title']} {kv}")
            tags = [
                f"type/factory-{c['prefix']}",
                "source/factory",
                f"company/{COMPANY}",
            ]
            related = []
            sap_codes = []
            # foreign-key wikilinks
            for field, val in rec.items():
                if field in FK:
                    tgt = FK[field]
                    fv = fk_value(val)
                    if fv is not None and str(fv) in registry.get(tgt, ()):
                        related.append(f"- {field} -> [[{tgt}-{slugify(fv)}]]")
                if field in SAP_FIELDS:
                    fv = fk_value(val)
                    if fv:
                        sap_codes.append(str(fv))
            # SAP bridge: link to oitm note + record the product-bridge code
            for code in sap_codes:
                if str(code) in registry.get("oitm", ()):
                    related.append(f"- item -> [[oitm-{slugify(code)}]]")
                if re.match(r"^FG\d+$", str(code)):
                    tags.append(f"bridge/{code}")
                    bridge_links.setdefault(code, set()).add(f"{slug}/{noteid}")
            # body — lossless dump of every field
            body = []
            for field, val in rec.items():
                if scalar(val):
                    body.append(f"- **{field}:** {val}")
                else:
                    body.append(
                        f"- **{field}:**\n  ```json\n  {json.dumps(val, ensure_ascii=False)}\n  ```"
                    )
            fm = (
                [
                    "---",
                    f"type: factory-{c['prefix']}",
                    f"id: {kv}",
                    f'title: "{title.replace(chr(34), chr(39))}"',
                    f"entity: {c['title']}",
                    f"source_endpoint: {c['ep']}",
                    f"company: {COMPANY}",
                    "tags:",
                ]
                + [f"  - {t}" for t in tags]
                + ["---", ""]
            )
            note = "\n".join(fm)
            note += f"# {title}\n\n> {c['title']} from `{c['ep']}` (Jivo Mart / {COMPANY}).\n\n## Fields\n"
            note += "\n".join(body) + "\n"
            if related:
                note += "\n## Related\n" + "\n".join(sorted(set(related))) + "\n"
            with open(os.path.join(folder, noteid + ".md"), "w") as f:
                f.write(note)
            idx.append((noteid, title))
            total_notes += 1
        note_index[slug] = idx

    # PASS 3 — MOC hubs (chunked at 1000 links)
    def write_moc(slug, idx, c):
        folder = os.path.join(OUT, slug)
        n = len(idx)
        pages = math.ceil(n / 1000) or 1
        moc_links = []
        for p in range(pages):
            chunk = idx[p * 1000 : (p + 1) * 1000]
            name = f"_moc-{slug}" + ("" if pages == 1 else f"-{p + 1:03d}")
            lines = [
                f"---\ntype: moc\ntitle: {c['title']} ({n})\ntags:\n  - moc\n  - source/factory\n---\n",
                f"# {c['title']} — {n} records"
                + ("" if pages == 1 else f" (page {p + 1}/{pages})"),
                f"\nFrom `{c['ep']}`. Up: [[_HOME]]\n",
            ]
            for noteid, title in chunk:
                lines.append(f"- [[{noteid}]] — {title}")
            with open(os.path.join(folder, name + ".md"), "w") as f:
                f.write("\n".join(lines) + "\n")
            moc_links.append(name)
        return moc_links, n

    domain_mocs = {}  # domain -> list of (moc_name, title, count)
    for slug, c in cfg.items():
        mocs, n = write_moc(slug, note_index[slug], c)
        domain = c["ep"].strip("/").split("/")[0]
        for mn in mocs:
            domain_mocs.setdefault(domain, []).append((mn, c["title"], n))

    # PASS 4 — Home MOC + data-presence + empty modules + bridge
    home = [
        "---\ntype: moc\ntitle: JIVO Factory (Jivo Mart) — Home\ntags:\n  - moc\n  - source/factory\n---\n",
        "# JIVO Factory — Jivo Mart (JIVO_MART)\n",
        f"Lossless capture of the ji.jivo.in factory app for **{COMPANY}** — one note per record, "
        f"linked by foreign keys. Bridges to product nodes via SAP item code (FG####).\n",
        f"\n- **Notes:** {total_notes}  ·  **Entity types:** {len(cfg)}  ·  "
        f"**SAP-bridged item codes:** {len(bridge_links)}\n",
        "\n## Entity hubs by domain\n",
    ]
    for domain in sorted(domain_mocs):
        home.append(f"\n### {domain}")
        seen = set()
        for mn, title, n in domain_mocs[domain]:
            if (title, n) in seen:
                continue
            seen.add((title, n))
            home.append(f"- [[{mn}|{title}]] ({n})")
    if empty_slugs:
        home.append("\n## Empty for Jivo Mart (not configured on the retail arm)\n")
        home.append(
            "These modules exist in the app but have no JIVO_MART data (live on Jivo Oil / Beverages):\n"
        )
        for slug, ep in sorted(empty_slugs):
            home.append(f"- `{ep}`")
    home.append("\n## SAP product bridge\n")
    home.append(
        f"{len(bridge_links)} distinct SAP item codes (FG####) are referenced by factory records and "
        f"link to jivo-data-bank product nodes. See `_bridge.json`.\n"
    )
    with open(os.path.join(OUT, "_HOME.md"), "w") as f:
        f.write("\n".join(home) + "\n")

    json.dump(
        {k: sorted(v) for k, v in bridge_links.items()},
        open(os.path.join(OUT, "_bridge.json"), "w"),
        indent=2,
    )

    # proof
    proof = {
        "total_notes": total_notes,
        "entity_types": len(cfg),
        "empty_modules": len(empty_slugs),
        "sap_bridge_codes": len(bridge_links),
        "per_entity": {s: len(note_index[s]) for s in cfg},
    }
    json.dump(proof, open(os.path.join(ROOT, "render-proof.json"), "w"), indent=2)
    print(f"rendered {total_notes} notes across {len(cfg)} entity types")
    print(
        f"SAP-bridge item codes: {len(bridge_links)} | empty modules: {len(empty_slugs)}"
    )
    print("output:", OUT)


if __name__ == "__main__":
    main()
