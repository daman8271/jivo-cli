#!/usr/bin/env python3
"""Repeatable regeneration that preserves hand-written enrichment blocks.

1. extract each section note's enrichment (a heading starting with '## PROVEN'
   through to just before '## Connections') BEFORE regeneration
2. run classify + build_vault (which overwrite section notes + Endpoints.md)
3. re-insert the enrichment blocks before '## Connections'
"""
import os, re, glob, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.join(HERE, '..', 'vault')

ENRICH_RE = re.compile(r'(\n## PROVEN.*?)(?=\n## Connections)', re.S)

# 1. stash enrichments
stash = {}
for p in glob.glob(os.path.join(VAULT, '**', '*.md'), recursive=True):
    s = open(p, encoding='utf-8').read()
    m = ENRICH_RE.search(s)
    if m:
        stash[os.path.abspath(p)] = m.group(1)
print(f'stashed {len(stash)} enrichment blocks')

# 2. regenerate
for script in ('classify.py', 'build_vault.py', 'build_routes_ledger.py'):
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True)
    print(f'--- {script} ---')
    print((r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr).strip() else '(ok)')
    if r.returncode:
        print(r.stderr); sys.exit(1)

# 3. re-insert enrichments (match by title, since path is stable)
reinserted = 0
for absp, block in stash.items():
    if not os.path.exists(absp):
        print('WARN enrichment target vanished:', absp); continue
    s = open(absp, encoding='utf-8').read()
    if '## PROVEN' in s:
        continue  # already present (shouldn't be after regen)
    if '## Connections' in s:
        s = s.replace('\n## Connections', block + '\n## Connections', 1)
        open(absp, 'w').write(s)
        reinserted += 1
print(f're-inserted {reinserted} enrichment blocks')
