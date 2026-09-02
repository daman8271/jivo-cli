#!/usr/bin/env python3
"""Fetch every lazy chunk of the ji.jivo.in bundle and extract API path literals.
Read-only: static asset GETs, no auth, no business system touched."""
import json,re,urllib.request,collections
from concurrent.futures import ThreadPoolExecutor
BASE="https://ji.jivo.in"
idx=urllib.request.urlopen(BASE+"/",timeout=30).read().decode("utf8","replace")
main=re.search(r'/assets/index-[A-Za-z0-9_-]+\.js',idx).group(0)
js=urllib.request.urlopen(BASE+main,timeout=60).read().decode("utf8","replace")
chunks=sorted(set(re.findall(r'["\'](?:\./)?(?:assets/)?([A-Za-z0-9_.-]+-[A-Za-z0-9_-]{8}\.js)["\']',js)))
print("main:",main,"chunks:",len(chunks),flush=True)
def get(c):
    try:
        return c,urllib.request.urlopen(f"{BASE}/assets/{c}",timeout=45).read().decode("utf8","replace")
    except Exception as e:
        return c,""
texts={main:js}
ok=0
with ThreadPoolExecutor(max_workers=12) as ex:
    for c,t in ex.map(get,chunks):
        texts[c]=t
        if t: ok+=1
print("chunks fetched ok:",ok,"/",len(chunks),flush=True)
api=collections.defaultdict(set)
RE=re.compile(r'["\`\']((/[a-z0-9][a-z0-9-]*(?:/[A-Za-z0-9${}._:-]+)*/))["\`\']')
for c,t in texts.items():
    for m in RE.finditer(t):
        p=m.group(1)
        if p.count('/')<2 or ':' in p: continue
        api[p.split('/')[1]].add(p)
tot=sum(len(v) for v in api.values())
print("distinct API-shaped literals:",tot,"across",len(api),"prefixes",flush=True)
out={k:sorted(v) for k,v in sorted(api.items(),key=lambda kv:-len(kv[1]))}
json.dump(out,open("/root/ji_api_by_prefix.json","w"),indent=1)
for k,v in list(out.items()): print(f"  {k:26s} {len(v)}")
