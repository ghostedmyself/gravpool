"""External API key provider store — OpenAI-compatible endpoints.

Users add providers (e.g. OpenAI, Anthropic via OpenRouter, custom endpoints)
with their API key + base URL.  Each provider exposes model IDs.  When a
/v1/chat/completions request hits the GravPool proxy, models that belong to an
external provider are routed directly to that provider's endpoint, bypassing
the CLIProxyAPI (Antigravity) child entirely.

Storage: ~/.gravpool/providers.json (chmod 0700 dir, 0600 file).
API keys are stored in plaintext locally — same threat model as the Antigravity
refresh_token JSON files.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib import request as urlreq
from urllib.error import HTTPError, URLError

# ─── storage ──────────────────────────────────────────────────────────────

_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")


def _store_dir() -> str:
    d = Path.home() / ".gravpool"
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(d), 0o700)
    except OSError:
        pass
    return str(d)


def _store_path() -> str:
    return str(Path(_store_dir()) / "providers.json")


# ─── dataclass ────────────────────────────────────────────────────────────

@dataclass
class Provider:
    """One external OpenAI-compatible API key endpoint."""
    name: str = ""
    base_url: str = ""        # e.g. https://api.openai.com/v1
    api_key: str = ""         # sk-...
    models: list[str] = field(default_factory=list)  # manual model override; auto-fetched if empty
    enabled: bool = True
    created_at: float = 0.0
    # runtime cache
    _models_cache: list[str] = field(default_factory=list, repr=False)
    _models_ts: float = 0.0

    def to_dict(self, *, include_key: bool = True) -> dict[str, Any]:
        d = {
            "name": self.name,
            "base_url": self.base_url,
            "models": list(self.models),
            "enabled": self.enabled,
            "created_at": self.created_at,
        }
        if include_key:
            d["api_key"] = self.api_key[:3] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else "***"
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Provider":
        return cls(
            name=data.get("name", ""),
            base_url=data.get("base_url", ""),
            api_key=data.get("api_key", ""),
            models=data.get("models", []),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", 0.0),
        )


# ─── CRUD ─────────────────────────────────────────────────────────────────

def _load_raw() -> list[dict]:
    p = _store_path()
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_raw(data: list[dict]) -> None:
    p = _store_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def load_providers() -> list[Provider]:
    return [Provider.from_dict(d) for d in _load_raw()]


def get_provider(name: str) -> Provider | None:
    for p in load_providers():
        if p.name == name:
            return p
    return None


def add_provider(name: str, base_url: str, api_key: str, models: list[str] | None = None) -> Provider:
    if not _NAME_RE.match(name):
        raise ValueError("name: 1-64 chars, [a-zA-Z0-9._-]")
    existing = _load_raw()
    if any(e["name"] == name for e in existing):
        raise ValueError(f"provider '{name}' already exists")
    # Auto-detect models if not provided
    if not models:
        try:
            p = Provider(name=name, base_url=base_url, api_key=api_key)
            models = fetch_provider_models(p, timeout=15)
        except Exception:
            models = []
    entry = {
        "name": name,
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "models": models or [],
        "enabled": True,
        "created_at": time.time(),
    }
    existing.append(entry)
    _save_raw(existing)
    return Provider.from_dict(entry)


def update_provider(name: str, *, base_url: str | None = None, api_key: str | None = None,
                    models: list[str] | None = None, enabled: bool | None = None) -> Provider:
    existing = _load_raw()
    found = None
    for e in existing:
        if e["name"] == name:
            found = e
            break
    if not found:
        raise ValueError(f"provider '{name}' not found")
    if base_url is not None:
        found["base_url"] = base_url.rstrip("/")
    if api_key is not None:
        found["api_key"] = api_key
    if models is not None:
        found["models"] = list(models)
    if enabled is not None:
        found["enabled"] = enabled
    _save_raw(existing)
    return Provider.from_dict(found)


def remove_provider(name: str) -> bool:
    existing = _load_raw()
    new = [e for e in existing if e["name"] != name]
    if len(new) == len(existing):
        return False
    _save_raw(new)
    return True


# ─── model discovery ─────────────────────────────────────────────────────

def _normalize_base(url: str) -> str:
    """Normalize a provider base URL. Auto-append /v1 if it looks like a bare
    API root (e.g. https://api.openai.com -> https://api.openai.com/v1)."""
    u = (url or "").rstrip("/")
    if not u:
        return u
    # If the path already looks like an API version or endpoint, leave it.
    if u.endswith("/v1") or "/v1/" in u:
        return u
    # Bare roots get /v1 appended (OpenAI-compatible convention).
    return u + "/v1"


# Some Cloudflare-fronted relays (e.g. Workers) reject requests with the
# default Python-urllib User-Agent. Send a browser-like UA so /models fetch
# isn't blocked with 403 (same pattern as the gonkarouter auth flow).
_BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/124.0.0.0 Safari/537.36")


def _models_request(url: str, api_key: str) -> urllib.request.Request:
    from urllib import request as _req
    return _req.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "User-Agent": _BROWSER_UA,
    })


def fetch_provider_models(provider: Provider, *, timeout: int = 10) -> list[str]:
    """GET <base>/models with the provider's API key. Tries the normalized
    base URL, then falls back to the raw base URL in case the provider
    already routes /models without a /v1 prefix."""
    base = _normalize_base(provider.base_url)
    tried = []
    for candidate in [base, provider.base_url.rstrip("/")]:
        if candidate in tried:
            continue
        tried.append(candidate)
        url = candidate + "/models"
        req = _models_request(url, provider.api_key)
        try:
            with urlreq.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                import gzip
                if resp.headers.get("Content-Encoding") == "gzip":
                    try:
                        raw = gzip.decompress(raw)
                    except OSError:
                        pass
                data = json.loads(raw)
            models = []
            for m in data.get("data", []):
                mid = m.get("id") if isinstance(m, dict) else str(m)
                if mid:
                    models.append(mid)
            if models:
                return sorted(models)
        except Exception:
            continue
    # All candidates failed; surface the last error for the last candidate.
    url = tried[-1] + "/models" if tried else provider.base_url + "/models"
    req = _models_request(url, provider.api_key)
    try:
        with urlreq.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        raise RuntimeError(str(e)) from e
    return [m["id"] for m in (data.get("data") or []) if isinstance(m, dict) and m.get("id")]


def resolve_provider_models(provider: Provider) -> list[str]:
    """Return models: manual override if set, else cached fetch, else live fetch."""
    if provider.models:
        return list(provider.models)
    # simple cache: fetch once, keep for session
    now = time.time()
    if provider._models_cache and (now - provider._models_ts < 300):
        return list(provider._models_cache)
    try:
        fetched = fetch_provider_models(provider)
        provider._models_cache = fetched
        provider._models_ts = now
        return fetched
    except Exception:
        return []


# ─── routing ──────────────────────────────────────────────────────────────

def find_provider_for_model(model_id: str) -> tuple[Provider | None, str]:
    """Given a model ID from /v1/chat/completions, find the matching provider.

    Returns (provider, original_model_id).  If no external provider serves
    this model, returns (None, model_id) so the caller routes to CLIProxyAPI.
    """
    for p in load_providers():
        if not p.enabled:
            continue
        pmodels = resolve_provider_models(p)
        if model_id in pmodels:
            return p, model_id
    return None, model_id


def all_provider_models() -> list[dict[str, str]]:
    """Flat list of {id, provider} for all external models."""
    out = []
    for p in load_providers():
        if not p.enabled:
            continue
        for m in resolve_provider_models(p):
            out.append({"id": m, "provider": p.name})
    return out
