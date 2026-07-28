#!/usr/bin/env python3
"""Generate a self-contained, searchable HTML Atlas of all SAP B1 Service Layer APIs
from the deterministic catalog (services.json + domains.json). No external deps."""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
services = json.load(open(os.path.join(HERE, "catalog/services.json")))
domains = json.load(open(os.path.join(HERE, "catalog/domains.json")))

# service -> domain title (strip the " (part N)" suffix so parts collapse)
import re
svc_domain = {}
for d in domains:
    base = re.sub(r"\s*\(part \d+\)$", "", d["title"])
    for s in d["services"]:
        svc_domain[s] = base

data = []
mcount = {"GET": 0, "POST": 0, "PATCH": 0, "PUT": 0, "DELETE": 0}
for s in services:
    methods = sorted({o["method"] for o in s["operations"]})
    for o in s["operations"]:
        mcount[o["method"]] = mcount.get(o["method"], 0) + 1
    data.append({
        "n": s["service"],
        "d": svc_domain.get(s["service"], "System & Other"),
        "r": "GET" in methods,
        "m": methods,
        "ops": [{"m": o["method"], "o": o["name"]} for o in s["operations"]],
    })

domain_titles = sorted({v for v in svc_domain.values()})
total_ops = sum(len(s["operations"]) for s in services)
readable = sum(1 for x in data if x["r"])
payload = json.dumps(data, separators=(",", ":"))
stats = {"services": len(data), "ops": total_ops, "readable": readable, "methods": mcount}

DOC = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAP B1 Service Layer — API Atlas</title>
<style>
:root{--bg:#0f1115;--card:#171a21;--line:#252a34;--fg:#e6e8ee;--dim:#9aa3b2;--acc:#4c8dff;--get:#2ecc71;--post:#f5a623;--patch:#b06bff;--del:#ff5c5c;--put:#7ad;}
@media (prefers-color-scheme: light){:root{--bg:#f6f7f9;--card:#fff;--line:#e4e7ec;--fg:#1a1d24;--dim:#5b6472;--acc:#2563eb;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:22px 20px 14px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
h1{margin:0 0 3px;font-size:20px}.sub{color:var(--dim);font-size:13px}
.stats{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:13px}
.stats b{color:var(--acc)}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;align-items:center}
input,select{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:14px}
input#q{flex:1;min-width:200px}
.chip{cursor:pointer;user-select:none;border:1px solid var(--line);border-radius:20px;padding:5px 11px;font-size:12px;background:var(--card)}
.chip.on{border-color:var(--acc);color:var(--acc)}
.wrap{padding:14px 20px 60px;max-width:1100px;margin:0 auto}
.count{color:var(--dim);font-size:13px;margin:6px 2px 12px}
.svc{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0;padding:12px 14px}
.svc summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.svc summary::-webkit-details-marker{display:none}
.name{font-weight:600;font-size:15px}
.tag{font-size:11px;color:var(--dim);border:1px solid var(--line);border-radius:6px;padding:2px 7px}
.read{color:var(--get);border-color:var(--get)}
.mm{display:inline-block;font-size:10px;font-weight:700;border-radius:5px;padding:1px 6px;margin-left:3px;color:#000}
.GET{background:var(--get)}.POST{background:var(--post)}.PATCH{background:var(--patch);color:#fff}.DELETE{background:var(--del);color:#fff}.PUT{background:var(--put)}
.ops{margin:10px 0 2px;border-top:1px solid var(--line);padding-top:8px}
.op{font:12px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--dim)}
.op b{display:inline-block;width:56px;color:var(--fg)}
.cmd{margin-top:8px;font:12px ui-monospace,Menlo,monospace;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:6px 8px;color:var(--acc);overflow-x:auto}
.spacer{flex:1}
</style></head><body>
<header>
<h1>SAP Business One — Service Layer API Atlas</h1>
<div class="sub">Every callable API on the server, grounded in SAP's own reference. Read-only focus: <b style="color:var(--get)">green = fetchable (has GET)</b>. Use with the <code>sapb1</code> CLI / MCP.</div>
<div class="stats">__STATS__</div>
<div class="controls">
<input id="q" placeholder="Search APIs… (e.g. order, invoice, stock, payment)">
<select id="dom"><option value="">All domains</option>__DOMS__</select>
<span class="chip" data-m="GET">GET</span><span class="chip" data-m="POST">POST</span>
<span class="chip" data-m="PATCH">PATCH</span><span class="chip" data-m="DELETE">DELETE</span>
<span class="chip" id="ronly">readable only</span>
</div></header>
<div class="wrap"><div class="count" id="count"></div><div id="list"></div></div>
<script>
const DATA=__PAYLOAD__;
const q=document.getElementById('q'),dom=document.getElementById('dom'),list=document.getElementById('list'),count=document.getElementById('count');
let mfil=new Set(),ronly=false;
function mm(m){return '<span class="mm '+m+'">'+m+'</span>'}
function render(){
 const t=q.value.trim().toLowerCase(),dv=dom.value;
 let rows=DATA.filter(s=>{
  if(t&&!s.n.toLowerCase().includes(t))return false;
  if(dv&&s.d!==dv)return false;
  if(ronly&&!s.r)return false;
  for(const m of mfil)if(!s.m.includes(m))return false;
  return true;});
 count.textContent=rows.length+' of '+DATA.length+' APIs';
 list.innerHTML=rows.map(s=>{
  const cmd=s.r&&!s.n.endsWith('Service')?'<div class="cmd">sapb1 query '+s.n+' --top 20</div>':'';
  const ops=s.ops.map(o=>'<div class="op"><b>'+o.m+'</b>'+o.o+'</div>').join('');
  return '<details class="svc"><summary><span class="name">'+s.n+'</span>'+
   '<span class="tag'+(s.r?' read':'')+'">'+(s.r?'readable':'action')+'</span>'+
   '<span class="tag">'+s.d+'</span><span class="spacer"></span>'+s.m.map(mm).join('')+
   '</summary>'+cmd+'<div class="ops">'+ops+'</div></details>';
 }).join('');
}
q.oninput=render;dom.onchange=render;
document.querySelectorAll('.chip[data-m]').forEach(c=>c.onclick=()=>{const m=c.dataset.m;c.classList.toggle('on');mfil.has(m)?mfil.delete(m):mfil.add(m);render()});
document.getElementById('ronly').onclick=function(){ronly=!ronly;this.classList.toggle('on');render()};
render();
</script></body></html>"""

stat_html = (
    f'<span><b>{stats["services"]}</b> APIs</span>'
    f'<span><b>{stats["ops"]}</b> operations</span>'
    f'<span><b style="color:var(--get)">{stats["readable"]}</b> readable (GET)</span>'
    + "".join(f'<span>{m} <b>{stats["methods"].get(m,0)}</b></span>' for m in ["GET","POST","PATCH","DELETE","PUT"])
)
dom_opts = "".join(f'<option value="{html.escape(d)}">{html.escape(d)}</option>' for d in domain_titles)
out = DOC.replace("__STATS__", stat_html).replace("__DOMS__", dom_opts).replace("__PAYLOAD__", payload)
open(os.path.join(HERE, "atlas.html"), "w").write(out)
print(f"wrote atlas.html — {stats['services']} APIs, {stats['ops']} ops, {stats['readable']} readable, {len(domain_titles)} domains")
