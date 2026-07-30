#!/usr/bin/env python3
"""Build vault/Flipkart-Live-Walk.md — a gallery referencing EVERY on-disk walk
screenshot (so none is an orphan), with a caption pulled from the page text +
manifest. Also emits a machine list the ledger builder consumes."""
import os, glob, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.join(HERE, '..', 'vault')
TODAY = '2026-07-30'

GROUPS = [
    ('vendorhub-walk', 'Vendor Hub', 'https://vendorhub.flipkart.com'),
    ('seller-walk', 'Seller Hub', 'https://seller.flipkart.com'),
]

def caption_from_txt(txt_path):
    if not os.path.exists(txt_path):
        return ''
    t = re.sub(r'\s+', ' ', open(txt_path, encoding='utf-8', errors='replace').read()).strip()
    return t[:240]

L = ['---', 'title: Flipkart Live Walk', f'created: {TODAY}', f'updated: {TODAY}',
     'project: jivo-cli', 'type: reference', 'tags: [flipkart, live-walk, screenshots, read-only]', '---', '',
     '# Flipkart — Live Read-Only Walk (screenshots + on-screen evidence)',
     '',
     'Per-section screenshots + page text captured by a read-only browser walk on 2026-07-30 '
     '(headless Chrome on `HO-IT-PC10`, session consumed not minted — G9; navigation only, no '
     'clicks; write-verb/auth requests aborted before the socket). Each image is a **distinct, '
     'non-trivial** page (byte-identical AND same-content duplicates were dropped at ingest). '
     'Raw per-page network capture (`sec-*.json`) is kept local (gitignored) as it carries '
     'response bodies; the screenshot + page text are the committed evidence.',
     '',
     'Amendment-04 audit of application-fired non-GET requests: `captures/nonget-allowed.tsv` '
     '(+ `nonget-flagged.tsv`). All were reads/telemetry — no mutation (no clicks were made).',
     '']
walked = []   # (group, route, screenshot, finalUrl) for the coverage ledger
for gdir, glabel, origin in GROUPS:
    d = os.path.join(HERE, gdir)
    if not os.path.isdir(d):
        continue
    mani = {}
    mf = os.path.join(d, '_manifest.json')
    if os.path.exists(mf):
        for m in json.load(open(mf)):
            mani[m['name']] = m
    pngs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(d, '*.png')))
    L.append(f'## {glabel} ({len(pngs)} sections)')
    L.append('')
    for png in pngs:
        name = png[:-4]
        m = mani.get(name, {})
        route = m.get('route', '')
        final = m.get('finalUrl', '')
        cap = caption_from_txt(os.path.join(d, name + '.txt'))
        L.append(f'### {name}')
        L.append('')
        L.append(f'`{origin}{route}` {("→ " + final) if final and final != origin+route else ""}'.strip())
        L.append('')
        L.append(f'![{name}](../captures/{gdir}/{png})')
        L.append('')
        if cap:
            L.append(f'> {cap}')
            L.append('')
        walked.append((glabel, route, f'{gdir}/{png}', final))

open(os.path.join(VAULT, 'Flipkart-Live-Walk.md'), 'w').write('\n'.join(L))
json.dump(walked, open(os.path.join(HERE, 'walked.json'), 'w'), indent=1)
print(f'gallery: {len(walked)} screenshots referenced across {len(GROUPS)} groups')
