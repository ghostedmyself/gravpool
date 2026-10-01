"""Live quota reporting via the Antigravity (Cloud Code) internal API.

Endpoint (verified working with an Antigravity Pro account's access token):

    POST https://daily-cloudcode-pa.sandbox.googleapis.com/v1internal:fetchAvailableModels
    Authorization: Bearer <access_token>
    User-Agent: antigravity/1.11.5 windows/amd64
    {}  (empty JSON body)

Response -> {"models": {name: {displayName, quotaInfo: {remainingFraction,
resetTime}, supportsThinking, ...}}, "serverTime": ...}
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from . import constants
from .store import AuthAccount


class QuotaError(RuntimeError):
    pass


def fetch_available_models(access_token: str, *, timeout: int = 15) -> dict:
    """Raw fetchAvailableModels response for one access token."""
    req = urllib.request.Request(
        constants.QUOTA_ENDPOINT,
        data=b"{}",
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": constants.USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        body = getattr(e, "read", lambda: b"")()
        raise QuotaError(f"HTTP {e} {body[:200]!r}") from e


def parse_models(resp: dict) -> tuple[dict, dict]:
    """Split a raw response into (quota_map, catalog).

    quota_map: {model: {"remaining": float 0..1, "reset": iso|null}}
    catalog:   {model: {displayName, supportsThinking, ...}} for model pickers
    """
    models, catalog = {}, {}
    for name, info in (resp.get("models") or {}).items():
        qi = info.get("quotaInfo") or {}
        rf = qi.get("remainingFraction")
        if rf is not None:
            models[name] = {"remaining": round(float(rf), 4),
                            "reset": qi.get("resetTime")}
        catalog[name] = {
            "displayName": info.get("displayName", name),
            "supportsThinking": bool(info.get("supportsThinking", False)),
            "thinkingBudget": info.get("thinkingBudget"),
            "minThinkingBudget": info.get("minThinkingBudget"),
            "maxOutputTokens": info.get("maxOutputTokens"),
            "recommended": bool(info.get("recommended", False)),
        }
    return models, catalog


def account_quota(acct: AuthAccount, *, timeout: int = 15) -> dict:
    """Quota snapshot for one account (auto-refreshes nothing — pass a fresh
    account or run oauth.refresh_account first)."""
    try:
        resp = fetch_available_models(acct.access_token, timeout=timeout)
    except QuotaError as e:
        return {"email": acct.email, "error": str(e)}
    models, catalog = parse_models(resp)
    return {
        "email": acct.email,
        "models": models,
        "catalog": catalog,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def pool_quota(accounts: list[AuthAccount], *, timeout: int = 15) -> dict:
    """Quota for every account in the pool."""
    out: dict = {"generated_at": datetime.now(timezone.utc).isoformat(),
                 "accounts": {}}
    for acct in accounts:
        out["accounts"][acct.email] = account_quota(acct, timeout=timeout)
    return out


def write_quota_snapshot(accounts: list[AuthAccount], out_path: str, *,
                         timeout: int = 15, min_interval: int = 300) -> dict:
    """Fetch pool quota and write a JSON snapshot; skips the fetch if the
    snapshot file is younger than ``min_interval`` seconds (cache-friendly for
    dashboards)."""
    import os
    if os.path.exists(out_path):
        if time_age(out_path) < min_interval:
            with open(out_path, "r", encoding="utf-8") as f:
                return json.load(f)
    snap = pool_quota(accounts, timeout=timeout)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snap, f)
    os.replace(tmp, out_path)
    return snap


def time_age(path: str) -> float:
    import os
    import time
    return time.time() - os.path.getmtime(path)
