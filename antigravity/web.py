"""Zero-dependency web GUI for the antigravity pool.

Run:
    python -m antigravity.cli gui --host 127.0.0.1 --port 8390

Endpoints:
    GET  /            dashboard page
    GET  /api/status  token state per account
    GET  /api/quota   live quota snapshot (30 s cache)
    POST /api/refresh refresh all expired tokens now

Binds to 127.0.0.1 by default — keep it that way unless you add your own
auth layer in front (the GUI exposes token *state*, never token values).
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .oauth import OAuthError, refresh_account
from .quota import pool_quota
from .store import AuthAccount, load_accounts

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
        def log_message(self, fmt, *args):  # quiet
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
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path.split("?", 1)[0] == "/api/refresh":
                try:
                    self._json(200, _refresh())
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
<title>antigravity-pool</title>
<style>
  :root { --bg:#0d1117; --card:#161b22; --line:#30363d; --fg:#e6edf3;
          --dim:#8b949e; --ok:#3fb950; --warn:#d29922; --bad:#f85149; }
  * { box-sizing:border-box; margin:0; }
  body { background:var(--bg); color:var(--fg);
         font:14px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif; padding:24px; }
  h1 { font-size:20px; margin-bottom:4px; }
  .sub { color:var(--dim); margin-bottom:20px; }
  button { background:#21262d; color:var(--fg); border:1px solid var(--line);
           border-radius:6px; padding:6px 14px; cursor:pointer; font-size:13px; }
  button:hover { background:#30363d; }
  button:disabled { opacity:.5; cursor:wait; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }
  .chip { background:var(--card); border:1px solid var(--line); border-radius:20px;
          padding:4px 12px; font-size:12px; }
  .chip.ok { border-color:var(--ok); } .chip.expired { border-color:var(--warn); }
  .chip.disabled, .chip.bad { border-color:var(--bad); }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px; }
  .card h2 { font-size:14px; margin-bottom:10px; word-break:break-all; }
  .row { margin-bottom:8px; }
  .row .top { display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px; }
  .row .name { color:var(--dim); }
  .bar { height:8px; background:#21262d; border-radius:4px; overflow:hidden; }
  .bar span { display:block; height:100%; border-radius:4px; }
  .bar .hi { background:var(--ok); } .bar .mid { background:var(--warn); }
  .bar .lo { background:var(--bad); }
  .err { color:var(--bad); font-size:12px; }
  footer { margin-top:20px; color:var(--dim); font-size:12px; display:flex;
           justify-content:space-between; align-items:center; }
  .toast { position:fixed; bottom:20px; right:20px; background:var(--card);
           border:1px solid var(--line); border-radius:8px; padding:10px 16px;
           display:none; font-size:13px; }
</style>
</head>
<body>
  <h1>&#128640; antigravity-pool</h1>
  <div class="sub">Google Antigravity OAuth pool &mdash; token state &amp; live quota</div>

  <div class="chips" id="chips"></div>

  <div class="grid" id="pool"></div>

  <footer>
    <span id="updated"></span>
    <span>auto-refresh 60s &middot; <button id="btn-quota">Reload quota</button>
    <button id="btn-refresh">Refresh tokens</button></span>
  </footer>
  <div class="toast" id="toast"></div>

<script>
const esc = s => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const bar = r => `<span class="${r<0.2?'lo':r<0.5?'mid':'hi'}" style="width:${Math.max(2,r*100)}%"></span>`;
const pct = r => (r*100).toFixed(0) + '%';

async function loadStatus(){
  const d = await (await fetch('/api/status')).json();
  document.getElementById('chips').innerHTML = d.map(a =>
    `<span class="chip ${esc(a.state)}">${esc(a.email)} &middot; ${esc(a.state)}</span>`).join('');
}

async function loadQuota(){
  const btn = document.getElementById('btn-quota'); btn.disabled = true;
  try {
    const d = await (await fetch('/api/quota')).json();
    const root = document.getElementById('pool');
    root.innerHTML = Object.entries(d.accounts).map(([email, info]) => {
      if (info.error) return `<div class="card"><h2>${esc(email)}</h2>
        <div class="err">${esc(info.error)}</div></div>`;
      const rows = Object.entries(info.models).sort((a,b)=>a[1].remaining-b[1].remaining)
        .map(([m, q]) => `<div class="row"><div class="top">
            <span class="name">${esc(m)}</span><span>${pct(q.remaining)}</span></div>
            <div class="bar">${bar(q.remaining)}</div></div>`).join('');
      return `<div class="card"><h2>${esc(email)}</h2>${rows}</div>`;
    }).join('');
    document.getElementById('updated').textContent =
      'updated ' + new Date(d.generated_at).toLocaleTimeString();
  } finally { btn.disabled = false; }
}

function toast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 4000);
}

document.getElementById('btn-quota').onclick = () => loadQuota();
document.getElementById('btn-refresh').onclick = async e => {
  e.target.disabled = true;
  try {
    const r = await (await fetch('/api/refresh', {method:'POST'})).json();
    toast(`refreshed ${r.refreshed.length}` +
          (r.failed.length ? `, failed ${r.failed.length}` : ''));
    await Promise.all([loadStatus(), loadQuota()]);
  } finally { e.target.disabled = false; }
};

loadStatus();
loadQuota();
setInterval(loadQuota, 60000);
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
