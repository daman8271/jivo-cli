// Install on a loaded page (after EVERY full navigation): wraps XHR + fetch and records
// {m,u,h,req,st,res,t} into window.__rec. Dump with:  $B js "JSON.stringify(window.__rec)"
// Never records cookies. Strip passwords before saving anything to disk (scrub.py).
(() => {
  window.__rec = [];
  const X = XMLHttpRequest.prototype, o = X.open, s = X.send, h = X.setRequestHeader;
  X.open = function (m, u) { this.__m = m; this.__u = u; this.__h = {}; return o.apply(this, arguments); };
  X.setRequestHeader = function (k, v) { this.__h[k] = v; return h.apply(this, arguments); };
  X.send = function (b) {
    const x = this;
    x.addEventListener('load', () => { window.__rec.push({ m: x.__m, u: x.__u, h: x.__h, req: (b && String(b).slice(0, 4000)) || null, st: x.status, res: String(x.responseText).slice(0, 20000), t: Date.now() }); });
    return s.apply(this, arguments);
  };
  const f = window.fetch;
  window.fetch = async function (u, i) {
    const r = await f.apply(this, arguments);
    try { const c = r.clone(); const t = await c.text(); window.__rec.push({ m: (i && i.method) || 'GET', u: String(u), h: (i && i.headers) || {}, req: (i && i.body && String(i.body).slice(0, 4000)) || null, st: r.status, res: t.slice(0, 20000), t: Date.now() }); } catch (e) { }
    return r;
  };
  return 'recorder installed';
})();
