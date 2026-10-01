"""Zero-dependency web GUI for the antigravity pool.

Run:
    python -m antigravity.cli gui --host 127.0.0.1 --port 8390

Endpoints:
    GET  /            dashboard page
    GET  /api/status  token state per account
    GET  /api/quota   live quota snapshot (30 s cache)
    POST /api/refresh refresh all expired tokens now
    GET  /api/combos  list combos
    POST /api/combos  create combo
    DELETE /api/combos/<name> delete combo
    GET  /api/combo-resolve?name=<name> resolve combo

Binds to 127.0.0.1 by default.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from .oauth import OAuthError, refresh_account
from .quota import pool_quota
from .store import AuthAccount, load_accounts

from .combo import load_combos, add_combo, remove_combo, resolve_combo

QUOTA_CACHE_TTL = 30  # seconds


def _make_handler(auth_dirs: list[str]) -> type:
    lock = threading.Lock()
    cache = {"at": 0.0, "data": None}

    def _accounts() -> list[AuthAccount]:
        return load_accounts(auth_dirs)

    def _quota_cached() -> dict:
        with lock:
            if cache["data"] is not None and time.time() - cache["at"] < QUOTA_CACHE_TTL:
                return cache["data"]
            data = pool_quota(_accounts())
            cache["at"] = time.time()
            cache["data"] = data
            return data

    def _status() -> list[dict]:
        out = []
        for a in _accounts():
            state = "disabled" if a.disabled else ("expired" if a.is_expired() else "ok")
            out.append({"email": a.email, "state": state, "path": a.path,
                        "expired": a.expired})
        return out

    def _refresh() -> dict:
        with lock:
            refreshed, failed = [], []
            for a in _accounts():
                if a.disabled or not a.is_expired(leeway=120):
                    continue
                try:
                    refresh_account(a, leeway=0)
                    refreshed.append(a.email)
                except OAuthError as e:
                    failed.append({"email": a.email, "error": str(e)[:120]})
            cache["at"] = 0.0  # bust the quota cache
            return {"refreshed": refreshed, "failed": failed}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, data) -> None:
            self._send(code, json.dumps(data).encode(), "application/json")

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self._send(200, _PAGE.encode(), "text/html; charset=utf-8")
            elif path == "/api/status":
                try:
                    self._json(200, _status())
                except Exception as e:
                    self._json(500, {"error": str(e)})
            elif path == "/api/quota":
                try:
                    self._json(200, _quota_cached())
                except Exception as e:
                    self._json(500, {"error": str(e)})
            elif path == "/api/combos":
                try:
                    combos = load_combos()
                    self._json(200, [{"name": c.name, "kind": c.kind, "models": c.models} for c in combos])
                except Exception as e:
                    self._json(500, {"error": str(e)})
            elif path == "/api/combo-resolve":
                try:
                    qs = parse_qs(urlparse(self.path).query)
                    name = qs.get("name", [""])[0]
                    res = resolve_combo(name, _quota_cached(), threshold=0.05)
                    self._json(200, res)
                except Exception as e:
                    self._json(500, {"error": str(e)})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path == "/api/refresh":
                try:
                    self._json(200, _refresh())
                except Exception as e:
                    self._json(500, {"error": str(e)})
            elif path == "/api/combos":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    combo = add_combo(body["name"], body.get("models", []),
                                      kind=body.get("kind", "fallback"))
                    self._json(200, {"ok": True, "combo": combo.to_dict()})
                except Exception as e:
                    self._json(400, {"error": str(e)})
            else:
                self._json(404, {"error": "not found"})

        def do_DELETE(self):
            path = self.path.split("?", 1)[0]
            if path.startswith("/api/combos/"):
                name = urllib.parse.unquote(path.split("/")[-1])
                try:
                    removed = remove_combo(name)
                    self._json(200 if removed else 404, {"ok": removed})
                except Exception as e:
                    self._json(500, {"error": str(e)})
            else:
                self._json(404, {"error": "not found"})

    return Handler

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Antigravity Pool</title>
<style>
:root {
  --bg: #0b0e14; --card: #151a23; --line: #262c36; --fg: #e2e8f0; --dim: #94a3b8;
  --accent: #14b8a6; --accent-hover: #0d9488;
  --ok: #4ade80; --warn: #facc15; --bad: #f87171;
}
* { box-sizing: border-box; margin: 0; }
body { background: var(--bg); color: var(--fg); font: 14px/1.5 ui-sans-serif, system-ui, sans-serif; padding: 24px; max-width: 1200px; margin: 0 auto; }
h1 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
.sub { color: var(--dim); margin-bottom: 24px; }
button { background: var(--line); color: var(--fg); border: none; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 13px; transition: transform 0.1s, opacity 0.2s; }
button:hover { opacity: 0.8; }
button:active { transform: scale(0.96); }
button.primary { background: var(--accent); color: #000; font-weight: 500; }
button.danger { background: color-mix(in srgb, var(--bad) 20%, transparent); color: var(--bad); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
input, select { background: var(--bg); color: var(--fg); border: 1px solid var(--line); border-radius: 6px; padding: 6px 10px; font-size: 13px; outline: none; transition: border-color 0.2s; }
input:focus, select:focus { border-color: var(--accent); }
.section-title { font-size: 16px; margin: 32px 0 16px; font-weight: 600; color: var(--fg); display: flex; justify-content: space-between; align-items: center; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; }
.card-title { font-size: 14px; font-weight: 600; word-break: break-all; }
.badge { font-size: 11px; padding: 2px 6px; border-radius: 4px; background: var(--line); color: var(--dim); white-space: nowrap; }
.badge.ok { color: var(--ok); background: color-mix(in srgb, var(--ok) 15%, transparent); }
.badge.warn { color: var(--warn); background: color-mix(in srgb, var(--warn) 15%, transparent); }
.badge.bad { color: var(--bad); background: color-mix(in srgb, var(--bad) 15%, transparent); }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.row { display: flex; flex-direction: column; gap: 4px; }
.row-top { display: flex; justify-content: space-between; font-size: 12px; }
.bar { height: 6px; background: var(--bg); border-radius: 3px; overflow: hidden; }
.bar span { display: block; height: 100%; border-radius: 3px; }
.bar .hi { background: var(--ok); } .bar .mid { background: var(--warn); } .bar .lo { background: var(--bad); }
.shimmer { animation: shimmer 2s infinite linear; background: linear-gradient(90deg, var(--bg) 0%, var(--line) 50%, var(--bg) 100%); background-size: 200% 100%; border-radius: 4px; height: 16px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.empty-state { padding: 32px; text-align: center; color: var(--dim); background: var(--card); border: 1px dashed var(--line); border-radius: 8px; }
.combo-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; background: var(--card); padding: 12px; border-radius: 8px; border: 1px solid var(--line); margin-bottom: 16px; }
.combo-resolve { font-family: monospace; font-size: 11px; background: var(--bg); padding: 8px; border-radius: 6px; color: var(--dim); white-space: pre-wrap; word-break: break-all; margin-top: auto;}
.combo-resolve strong { color: var(--accent); }
.toast { position: fixed; bottom: 24px; right: 24px; background: var(--card); border: 1px solid var(--line); border-radius: 6px; padding: 12px 16px; font-size: 13px; display: none; z-index: 50; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
</style>
</head>
<body>
  <header>
    <h1>[ Antigravity Pool ]</h1>
    <div class="sub">OAuth pool manager, token state, live quota, and combos.</div>
  </header>

  <div class="chips" id="status-chips"></div>

  <div class="section-title">
    <span>Accounts & Quota</span>
    <span style="display:flex; gap:8px;">
      <button id="btn-refresh">Refresh tokens</button>
      <button id="btn-quota">Reload quota</button>
    </span>
  </div>
  <div class="grid" id="pool-grid">
    <div class="card"><div class="shimmer" style="width:50%"></div><div class="shimmer" style="width:100%"></div></div>
  </div>

  <div class="section-title">
    <span>Combos</span>
    <button id="btn-new-combo" class="primary">+ New Combo</button>
  </div>
  <div id="combo-form-container" style="display:none;">
    <form class="combo-form" id="combo-form">
      <input type="text" id="combo-name" placeholder="Name" required>
      <select id="combo-kind"><option value="fallback">Fallback</option><option value="fusion">Fusion</option></select>
      <input type="text" id="combo-models" placeholder="Models (comma separated)" style="flex:1" required>
      <button type="submit" class="primary">Save</button>
      <button type="button" id="btn-cancel-combo">Cancel</button>
    </form>
  </div>
  <div class="grid" id="combo-grid">
    <div class="card"><div class="shimmer" style="width:100%;height:60px;"></div></div>
  </div>

  <div class="toast" id="toast"></div>

<script>
const esc = s => s ? String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])) : '';
const bar = r => `<span class="${r<0.2?'lo':r<0.5?'mid':'hi'}" style="width:${Math.max(2,r*100)}%"></span>`;
const pct = r => (r*100).toFixed(0) + '%';

async function fetchJson(url, opts) {
  const r = await fetch(url, opts);
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 4000);
}

async function loadStatus() {
  try {
    const d = await fetchJson('/api/status');
    const root = document.getElementById('status-chips');
    root.innerHTML = d.map(a => `<span class="badge ${a.state === 'ok' ? 'ok' : a.state === 'expired' ? 'warn' : 'bad'}">${esc(a.email)} : ${esc(a.state)}</span>`).join('');
  } catch(e) { console.error(e); }
}

async function loadQuota() {
  const btn = document.getElementById('btn-quota'); btn.disabled = true;
  try {
    const d = await fetchJson('/api/quota');
    const root = document.getElementById('pool-grid');
    if (!d.accounts || !Object.keys(d.accounts).length) {
       root.innerHTML = '<div class="empty-state" style="grid-column:1/-1;">No accounts found.</div>';
       return;
    }
    root.innerHTML = Object.entries(d.accounts).map(([email, info]) => {
      if (info.error) return `<div class="card"><div class="card-header"><div class="card-title">${esc(email)}</div><span class="badge bad">Error</span></div><div class="badge bad" style="align-self:flex-start; white-space:normal;">${esc(info.error)}</div></div>`;
      const rows = Object.entries(info.models).sort((a,b)=>a[1].remaining-b[1].remaining)
        .map(([m, q]) => `<div class="row"><div class="row-top"><span>${esc(m)}</span><span>${pct(q.remaining)}</span></div><div class="bar">${bar(q.remaining)}</div></div>`).join('');
      return `<div class="card"><div class="card-header"><div class="card-title">${esc(email)}</div></div>${rows}</div>`;
    }).join('');
  } catch(e) {
    document.getElementById('pool-grid').innerHTML = `<div class="empty-state badge bad">${esc(e.message)}</div>`;
  } finally { btn.disabled = false; }
}

async function loadCombos() {
  try {
    const combos = await fetchJson('/api/combos');
    const root = document.getElementById('combo-grid');
    if (!combos.length) {
      root.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">Belum ada combo. Klik New Combo untuk membuat.</div>';
      return;
    }
    
    let html = '';
    for (const c of combos) {
      let resHtml = '';
      try {
        const res = await fetchJson(`/api/combo-resolve?name=${encodeURIComponent(c.name)}`);
        const picked = Array.isArray(res.picked) ? res.picked.join(', ') : res.picked;
        if (picked) {
           resHtml = `Picked: <strong style="color:var(--ok)">${esc(picked)}</strong>\nFallback: ${esc((res.fallback||[]).join(', '))}\nDrained: ${esc((res.drained||[]).join(', '))}`;
        } else {
           resHtml = `<span style="color:var(--bad)">Reason: ${esc(res.reason||'No model available')}</span>\nDrained: ${esc((res.drained||[]).join(', '))}`;
        }
      } catch(e) {
        resHtml = `<span style="color:var(--bad)">Error resolving combo</span>`;
      }
      
      html += `<div class="card">
        <div class="card-header">
          <div class="card-title" style="display:flex;align-items:center;gap:6px;">${esc(c.name)} <span class="badge">${esc(c.kind)}</span></div>
          <button class="danger" onclick="delCombo('${esc(c.name)}')">Delete</button>
        </div>
        <div class="row"><div class="row-top" style="color:var(--dim);">Models</div><div style="font-size:13px; line-height:1.4;">${esc(c.models.join(', '))}</div></div>
        <div class="combo-resolve">${resHtml}</div>
      </div>`;
    }
    root.innerHTML = html;
  } catch(e) { console.error(e); }
}

document.getElementById('btn-new-combo').onclick = () => document.getElementById('combo-form-container').style.display = 'block';
document.getElementById('btn-cancel-combo').onclick = () => document.getElementById('combo-form-container').style.display = 'none';
document.getElementById('combo-form').onsubmit = async (e) => {
  e.preventDefault();
  const name = document.getElementById('combo-name').value;
  const kind = document.getElementById('combo-kind').value;
  const models = document.getElementById('combo-models').value.split(',').map(s=>s.trim()).filter(Boolean);
  const btn = e.target.querySelector('button[type="submit"]'); btn.disabled = true;
  try {
    await fetchJson('/api/combos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, kind, models})
    });
    document.getElementById('combo-form-container').style.display = 'none';
    e.target.reset();
    toast(`Combo ${name} created`);
    await loadCombos();
  } catch(err) { alert(err.message); } finally { btn.disabled = false; }
};

window.delCombo = async (name) => {
  if (!confirm(`Delete combo ${name}?`)) return;
  try {
    await fetchJson(`/api/combos/${encodeURIComponent(name)}`, {method: 'DELETE'});
    toast(`Combo ${name} deleted`);
    await loadCombos();
  } catch(e) { alert(e.message); }
};

document.getElementById('btn-quota').onclick = async () => { await loadQuota(); await loadCombos(); };
document.getElementById('btn-refresh').onclick = async e => {
  e.target.disabled = true;
  try {
    const r = await fetchJson('/api/refresh', {method: 'POST'});
    toast(`Refreshed ${r.refreshed?.length||0}, failed ${r.failed?.length||0}`);
    await Promise.all([loadStatus(), loadQuota()]);
    await loadCombos();
  } catch(err) { alert(err.message); } finally { e.target.disabled = false; }
};

async function init() {
  await loadStatus();
  await loadQuota();
  await loadCombos();
}

init();
setInterval(() => { loadQuota().then(loadCombos); }, 60000);
setInterval(loadStatus, 120000);
</script>
</body>
</html>
"""


def serve(auth_dirs: list[str], host: str = "127.0.0.1", port: int = 8390) -> None:
    httpd = ThreadingHTTPServer((host, port), _make_handler(auth_dirs))
    print(f"antigravity-pool GUI -> http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
