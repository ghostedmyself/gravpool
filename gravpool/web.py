
import os
import json
import ssl
import threading
import time
import urllib.parse
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse, urlsplit

from .oauth import OAuthError, refresh_account, build_auth_url, exchange_code, save_new_account
from .quota import pool_quota
from .store import AuthAccount, load_accounts
from .combo import load_combos, add_combo, remove_combo, resolve_combo
from .constants import CALLBACK_PORT
from .login_flow import AuthServer, CallbackHandler
from . import providers as ext_providers

QUOTA_CACHE_TTL = 30  # seconds

_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

add_acc_state = {
    "pending": False,
    "url": None,
    "error": None,
    "email": None
}

def start_add_account(auth_dir: str):
    global add_acc_state
    if add_acc_state["pending"]:
        return
    add_acc_state["pending"] = True
    add_acc_state["url"] = None
    add_acc_state["error"] = None
    add_acc_state["email"] = None

    redirect_uri = f"http://127.0.0.1:{CALLBACK_PORT}/auth/callback"
    auth_url, state = build_auth_url(redirect_uri=redirect_uri)
    add_acc_state["url"] = auth_url

    def bg_task():
        global add_acc_state
        try:
            server = AuthServer(('127.0.0.1', CALLBACK_PORT), CallbackHandler)
        except OSError as e:
            add_acc_state["error"] = f"Port in use: {e}"
            add_acc_state["pending"] = False
            return
        
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        start_time = time.time()
        timeout = 300
        while server_thread.is_alive():
            server_thread.join(timeout=1.0)
            if time.time() - start_time > timeout:
                server.shutdown()
                server.server_close()
                add_acc_state["error"] = "Timeout"
                add_acc_state["pending"] = False
                return
                
        server.server_close()
        
        if server.auth_error:
            add_acc_state["error"] = f"Failed: {server.auth_error}"
        elif not server.auth_code:
            add_acc_state["error"] = "No code received"
        elif server.auth_state != state:
            add_acc_state["error"] = "State mismatch"
        else:
            try:
                token_resp = exchange_code(server.auth_code, redirect_uri=redirect_uri)
                account = save_new_account(token_resp, auth_dir)
                # --- verify: test token against quota API ---
                from .quota import account_quota
                q = account_quota(account, timeout=15)
                if q.get("error"):
                    add_acc_state["error"] = f"Token saved but verification failed: {q['error'][:120]}"
                elif q.get("models"):
                    n = len(q["models"])
                    add_acc_state["email"] = f"{account.email} (verified, {n} models)"
                else:
                    add_acc_state["error"] = "Token saved but no models returned"
            except Exception as e:
                add_acc_state["error"] = f"Exchange failed: {e}"
                
        add_acc_state["pending"] = False

    t = threading.Thread(target=bg_task)
    t.daemon = True
    t.start()


def _make_handler(auth_dirs: list[str], proxy=None, host: str = "127.0.0.1", port: int = 8390) -> type:
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
            state = "disabled" if getattr(a, 'disabled', False) else ("expired" if a.is_expired() else "ok")
            out.append({"email": a.email, "state": state, "path": a.path,
                        "expired": a.expired})
        return out

    def _refresh() -> dict:
        with lock:
            refreshed, failed = [], []
            for a in _accounts():
                if getattr(a, 'disabled', False) or not a.is_expired(leeway=120):
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

        def _serve_static(self, filename: str, content_type: str):
            path = os.path.join(_STATIC_DIR, filename)
            if not os.path.exists(path):
                self._json(404, {"error": "not found"})
                return
            with open(path, "rb") as f:
                body = f.read()
            self._send(200, body, content_type)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/v1" or path.startswith("/v1/"):
                self.proxy_request()
                return

            if path == "/":
                self._serve_static("index.html", "text/html; charset=utf-8")
            elif path == "/style.css":
                self._serve_static("style.css", "text/css")
            elif path == "/app.js":
                self._serve_static("app.js", "application/javascript")
            elif path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
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
            elif path == "/api/proxy":
                if proxy:
                    self._json(200, {
                        "running": proxy.running,
                        "port": proxy.port,
                        "url": f"http://127.0.0.1:{proxy.port}",
                        "endpoint": f"http://{host}:{port}/v1",
                        "api_key": "sk-local",
                        "healthy": proxy.healthy() if proxy.running else False,
                        "version": None,
                        "error": proxy.error
                    })
                else:
                    self._json(200, {
                        "running": False, "port": 0, "url": "", "endpoint": "",
                        "api_key": "", "healthy": False, "version": "", "error": "No proxy configured"
                    })
            elif path == "/api/models":
                if proxy and proxy.running:
                    self._json(200, proxy.models())
                else:
                    self._json(200, {"data": [], "error": "proxy not running"})
            elif path == "/api/add-account":
                self._json(200, add_acc_state)
            elif path == "/api/providers":
                try:
                    plist = ext_providers.load_providers()
                    self._json(200, [p.to_dict(include_key=False) for p in plist])
                except Exception as e:
                    self._json(500, {"error": str(e)})
            elif path == "/api/providers/models":
                try:
                    self._json(200, {"data": ext_providers.all_provider_models()})
                except Exception as e:
                    self._json(500, {"error": str(e)})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path == "/v1" or path.startswith("/v1/"):
                self.proxy_request()
                return
                
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
            elif path == "/api/accounts/toggle":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    email = body.get("email")
                    disabled = bool(body.get("disabled"))
                    accs = _accounts()
                    found = None
                    for a in accs:
                        if a.email == email:
                            found = a
                            break
                    if not found:
                        self._json(404, {"error": "not found"})
                        return
                    found.disabled = disabled
                    found.save()
                    self._json(200, {"ok": True, "email": email, "disabled": disabled})
                except Exception as e:
                    self._json(400, {"error": str(e)})
            elif path == "/api/add-account":
                if add_acc_state["pending"]:
                    self._json(400, {"error": "already pending"})
                    return
                auth_dir = auth_dirs[0] if auth_dirs else "auth"
                start_add_account(auth_dir)
                self._json(200, {"ok": True, "url": add_acc_state["url"]})
            elif path == "/api/providers":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    p = ext_providers.add_provider(
                        body["name"], body["base_url"], body["api_key"],
                        models=body.get("models") or None,
                    )
                    self._json(200, {"ok": True, "provider": p.to_dict(include_key=False)})
                except Exception as e:
                    self._json(400, {"error": str(e)})
            elif path == "/api/providers/test":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    name = body.get("name", "")
                    p = ext_providers.get_provider(name)
                    if not p:
                        self._json(404, {"error": f"provider '{name}' not found"})
                        return
                    models = ext_providers.fetch_provider_models(p)
                    self._json(200, {"ok": True, "provider": name, "models": models})
                except Exception as e:
                    self._json(502, {"error": str(e)})
            elif path == "/api/providers/update":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    p = ext_providers.update_provider(
                        body["name"],
                        base_url=body.get("base_url"),
                        api_key=body.get("api_key"),
                        models=body.get("models"),
                        enabled=body.get("enabled"),
                    )
                    self._json(200, {"ok": True, "provider": p.to_dict(include_key=False)})
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
            elif path.startswith("/api/providers/"):
                name = urllib.parse.unquote(path.split("/")[-1])
                try:
                    removed = ext_providers.remove_provider(name)
                    self._json(200 if removed else 404, {"ok": removed})
                except Exception as e:
                    self._json(500, {"error": str(e)})
            else:
                self._json(404, {"error": "not found"})
                
        def do_OPTIONS(self):
            path = self.path.split("?", 1)[0]
            if path == "/v1" or path.startswith("/v1/"):
                self.proxy_request()
                return
            self._json(404, {"error": "not found"})

        def proxy_request(self):
            if not proxy or not proxy.running:
                self._json(502, {"error": "proxy not running"})
                return

            try:
                self.close_connection = True

                length = self.headers.get("Content-Length")
                body = None
                if length:
                    body = self.rfile.read(int(length))

                # --- external provider routing ---
                # If this is a /v1/chat/completions (or /v1/completions) request,
                # check if the requested model belongs to an external provider.
                routed_external = False
                if body and self.path.startswith("/v1/"):
                    try:
                        payload = json.loads(body)
                        model_id = payload.get("model", "")
                        if model_id:
                            provider, orig_model = ext_providers.find_provider_for_model(model_id)
                            if provider:
                                self._forward_to_provider(provider, body)
                                return
                    except (json.JSONDecodeError, KeyError):
                        pass

                # --- default: route to CLIProxyAPI (Antigravity) ---
                headers = {}
                for k, v in self.headers.items():
                    if k.lower() not in ("host", "connection"):
                        headers[k] = v

                conn = http.client.HTTPConnection("127.0.0.1", proxy.port)
                conn.request(self.command, self.path, body, headers)
                resp = conn.getresponse()

                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.send_header("Connection", "close")
                self.end_headers()

                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()

                conn.close()
            except Exception as e:
                self.log_error(f"Proxy error: {e}")
                if not getattr(self, '_headers_buffer', None):
                    self._json(502, {"error": str(e)})

        def _forward_to_provider(self, provider, body: bytes) -> None:
            """Forward a request body to an external OpenAI-compatible endpoint."""
            try:
                parsed = urlsplit(provider.base_url)
                is_https = parsed.scheme == "https"
                host = parsed.hostname or ""
                port = parsed.port or (443 if is_https else 80)
                path_prefix = parsed.path.rstrip("/")

                # Build the target path: provider base + incoming path
                target_path = path_prefix + self.path
                # Rewrite Authorization header
                headers = {}
                for k, v in self.headers.items():
                    kl = k.lower()
                    if kl in ("host", "connection", "authorization", "content-length", "transfer-encoding"):
                        continue
                    headers[k] = v
                headers["Authorization"] = f"Bearer {provider.api_key}"
                headers["Content-Length"] = str(len(body))
                headers["Host"] = host
                headers["Connection"] = "close"

                if is_https:
                    ctx = ssl.create_default_context()
                    conn = http.client.HTTPSConnection(host, port, context=ctx, timeout=120)
                else:
                    conn = http.client.HTTPConnection(host, port, timeout=120)

                conn.request(self.command, target_path, body, headers)
                resp = conn.getresponse()

                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.send_header("Connection", "close")
                self.end_headers()

                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
                conn.close()
            except Exception as e:
                if not getattr(self, '_headers_buffer', None):
                    self._json(502, {"error": f"Provider {provider.name} error: {e}"})

    return Handler


def serve(auth_dirs: list[str], host: str = "127.0.0.1", port: int = 8390, proxy=None) -> None:
    httpd = ThreadingHTTPServer((host, port), _make_handler(auth_dirs, proxy, host, port))
    print(f"GravPool -> http://{host}:{port}")
    if proxy and proxy.running:
        print(f"Proxy endpoint -> http://{host}:{port}/v1")
        print("API Key: sk-local")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
