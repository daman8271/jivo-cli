#!/usr/bin/env python3
"""Ingest a live-walk output dir into portals/flipkart/captures/<group>/.

Verifies each screenshot is DISTINCT (sha256) and NON-TRIVIAL (>=8KB and page had
text), copies sec-*.png/.json/.txt into captures/<group>/, appends app-fired
non-GET requests to captures/nonget-allowed.tsv (+ flags state-change paths into
nonget-flagged.tsv), and prints a section->screenshot map for wiring into the vault.

Usage: ingest_walk.py <local_walk_dir> <group> <origin>
"""
import os, sys, json, hashlib, shutil, re

SRC = sys.argv[1]
GROUP = sys.argv[2]
ORIGIN = sys.argv[3] if len(sys.argv) > 3 else ''
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, GROUP)
os.makedirs(DST, exist_ok=True)

MIN_BYTES = 8000
FLAG_RE = re.compile(r'(create|update|delete|submit|approve|acknowledge|mark-read|pause|activate|pay|upload|generate|schedule|select-vendor|cancel|reject)', re.I)

manifest = []
mf = os.path.join(SRC, '_manifest.json')
if os.path.exists(mf):
    manifest = json.load(open(mf))

def norm_text(name):
    """whitespace-normalised first 1200 chars of the page text — catches SEMANTIC
    duplicates (routes that fell back to the same dashboard but differ by a few
    dynamic bytes so their PNG sha differs)."""
    tp = os.path.join(SRC, name + '.txt')
    if not os.path.exists(tp):
        return None
    t = re.sub(r'\s+', ' ', open(tp, encoding='utf-8', errors='replace').read()).strip()[:1200]
    return hashlib.sha256(t.encode()).hexdigest()[:16] if t else None

shas = {}
texts = {}
rows = []
copied = 0
for m in manifest:
    name = m['name']
    png = os.path.join(SRC, name + '.png')
    if not os.path.exists(png):
        rows.append((name, m.get('route'), 'NO-PNG', m.get('error') or ''))
        continue
    b = open(png, 'rb').read()
    sha = hashlib.sha256(b).hexdigest()[:16]
    trivial = len(b) < MIN_BYTES or (m.get('text_len', 0) < 40)
    dup = shas.get(sha)
    if dup:
        rows.append((name, m.get('route'), f'DUP-png-of-{dup}', ''))
        continue
    th = norm_text(name)
    tdup = texts.get(th) if th else None
    if tdup:
        rows.append((name, m.get('route'), f'DUP-content-of-{tdup}', 'same page rendered (fallback)'))
        continue
    if trivial:
        rows.append((name, m.get('route'), f'TRIVIAL({len(b)}b,txt{m.get("text_len",0)})', m.get('error') or ''))
        continue
    shas[sha] = name
    if th:
        texts[th] = name
    for ext in ('.png', '.json', '.txt'):
        s = os.path.join(SRC, name + ext)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(DST, name + ext))
    copied += 1
    rows.append((name, m.get('route'), f'OK {len(b)}b sha={sha}', m.get('finalUrl', '')))

# copy the manifests
for aux in ('_manifest.json', '_blocked.json', '_nonget.json'):
    s = os.path.join(SRC, aux)
    if os.path.exists(s):
        shutil.copy2(s, os.path.join(DST, aux))

# append app-fired non-GETs to the Amendment-04 audit trails
ng = os.path.join(SRC, '_nonget.json')
allowed_path = os.path.join(HERE, 'nonget-allowed.tsv')
flagged_path = os.path.join(HERE, 'nonget-flagged.tsv')
n_allowed = n_flagged = 0
if os.path.exists(ng):
    ngs = json.load(open(ng))
    if ngs:
        # (re)write with a real header + rows
        with open(allowed_path, 'a') as fa:
            for r in ngs:
                body_shape = re.sub(r'"[^"]*"', '"<redacted>"', (r.get('body') or ''))[:200]
                fa.write(f"{GROUP}\t{r.get('method')}\t{r.get('url')}\t{ORIGIN}\t{body_shape}\tapp-fired-during-walk\n")
                n_allowed += 1
                if FLAG_RE.search(r.get('url', '')):
                    with open(flagged_path, 'a') as ff:
                        ff.write(f"{GROUP}\t{r.get('method')}\t{r.get('url')}\t{ORIGIN}\t{body_shape}\tpath-suggests-state-change\n")
                    n_flagged += 1

print(f"=== ingest {GROUP} from {SRC} ===")
for name, route, status, extra in rows:
    print(f"  {status:22} {name:44} {route}")
print(f"\ncopied {copied} distinct non-trivial screenshots to captures/{GROUP}/")
print(f"app-fired non-GET logged: {n_allowed} (flagged state-change: {n_flagged})")
print(f"distinct shas: {len(shas)}")
