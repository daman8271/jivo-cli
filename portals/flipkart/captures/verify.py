#!/usr/bin/env python3
"""PHASE 7 — adversarial self-verification of the Flipkart vault. READ-ONLY."""
import os, re, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.join(HERE, '..', 'vault')

def strip_code(s):
    s = re.sub(r'```.*?```', '', s, flags=re.S)
    s = re.sub(r'`[^`]*`', '', s)
    return s

# ---- 1. file presence ----
notes = {os.path.splitext(os.path.basename(p))[0]: p
         for p in glob.glob(os.path.join(VAULT, '**', '*.md'), recursive=True)}
expected_top = ['00-Flipkart-Atlas', 'Flipkart-Endpoints', 'Flipkart-Pages-and-Routes',
                'Flipkart-Data-Model', 'Flipkart-Data-Inventory',
                'Auth-and-Access', 'Read-Only-Guardrails', 'Study-Verification']
missing = [n for n in expected_top if n not in notes]
print(f'[1] file presence: {len(notes)} notes on disk; missing expected top-level: {missing or "none"}')

# ---- 2. broken wikilinks ----
targets = set(notes.keys())
broken = collections.Counter()
linkre = re.compile(r'\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]')
for n, p in notes.items():
    body = strip_code(open(p, encoding='utf-8').read())
    for m in linkre.finditer(body):
        t = m.group(1).strip()
        if t not in targets:
            broken[t] += 1
print(f'[2] broken wikilinks: {sum(broken.values())} occurrences, {len(broken)} distinct')
for t, c in broken.most_common():
    print(f'      BROKEN [[{t}]] x{c}')

# ---- 3. endpoint coverage ----
raw = []
with open(os.path.join(HERE, 'endpoints-raw.tsv')) as fh:
    next(fh)
    for line in fh:
        parts = line.rstrip('\n').split('\t')
        if len(parts) >= 4:
            raw.append(parts[3])  # path
raw = sorted(set(raw))
endpoints_md = open(os.path.join(VAULT, 'Flipkart-Endpoints.md'), encoding='utf-8').read()
missing_paths = [p for p in raw if p not in endpoints_md]
print(f'[3] endpoint coverage: {len(raw)-len(missing_paths)}/{len(raw)} distinct paths indexed '
      f'({100*(len(raw)-len(missing_paths))//max(len(raw),1)}%); missing {len(missing_paths)}')
for p in missing_paths[:20]:
    print('      MISSING', p)

# ---- 4. guardrail audit: no WRITE/EXPORT/UNKNOWN path in any allowlist table ----
# read classification
cls = {}
with open(os.path.join(HERE, 'endpoints-raw.tsv')) as fh:
    next(fh)
    for line in fh:
        parts = line.rstrip('\n').split('\t')
        if len(parts) >= 5:
            cls[parts[3]] = parts[4]
violations = []
for n, p in notes.items():
    body = open(p, encoding='utf-8').read()
    # find the allowlist section only
    m = re.search(r'## Read-safe endpoints \(allowlist\)(.*?)(?:\n## |\Z)', body, re.S)
    if not m:
        continue
    seg = m.group(1)
    for path, c in cls.items():
        if c in ('WRITE', 'EXPORT', 'UNKNOWN', 'UNKNOWN_READLIKE') and f'`{path}`' in seg.replace('\\|','|') or (c in ('WRITE','EXPORT') and re.search(r'`[^`]*'+re.escape(path)+r'`', seg)):
            # confirm the path token appears as an endpoint cell in allowlist
            if re.search(r'\|\s*`[^`]*'+re.escape(path)+r'`\s*\|', seg):
                violations.append((n, path, c))
print(f'[4] guardrail audit: {len(violations)} write/export/unknown paths wrongly in a read allowlist')
for v in violations[:20]:
    print('      VIOLATION', v)

ok = (not missing) and (sum(broken.values()) == 0) and (not missing_paths) and (not violations)
print('\nVERDICT:', 'PASS' if ok else 'FAIL')
