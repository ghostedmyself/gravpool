"""Token refresh + initial login for Antigravity OAuth accounts.

Refresh flow (verified against live accounts):

    POST https://oauth2.googleapis.com/token
      client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>
      grant_type=refresh_token&refresh_token=<rt>
    -> {access_token, expires_in, ...}

Interactive login: the pool binary (``cli-proxy-api``) ships a built-in
``--antigravity-login`` flag that runs the full OAuth device/browser flow and
writes the auth JSON; we reuse it instead of re-implementing the flow. This
module can also build the authorization URL + exchange the code directly if
you want a login path without the binary.
"""

from __future__ import annotations

import secrets
import time
import urllib.parse
import urllib.request
from typing import Optional

from . import constants
from .store import AuthAccount


class OAuthError(RuntimeError):
    pass


# ---------- refresh ----------

def refresh_access_token(refresh_token: str, *, timeout: int = 20) -> dict:
    """Exchange a refresh_token for a fresh access_token. Returns the raw
    Google token response (access_token, expires_in, scope, token_type)."""
    data = urllib.parse.urlencode({
        "client_id": constants.CLIENT_ID,
        "client_secret": constants.CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    req = urllib.request.Request(constants.TOKEN_ENDPOINT, data=data)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return dict(json_resp(resp))
    except Exception as e:  # urllib raises HTTPError with a JSON body
        body = getattr(e, "read", lambda: b"")()
        raise OAuthError(f"refresh failed: {e} {body[:200]!r}") from e


def json_resp(resp) -> dict:
    import json
    return json.loads(resp.read().decode("utf-8"))


def refresh_account(acct: AuthAccount, *, leeway: int = 120, save: bool = True) -> AuthAccount:
    """Refresh an account's access token in place if it is (nearly) expired.

    Returns the updated account. Raises OAuthError when the refresh fails
    (e.g. token revoked).
    """
    if not acct.is_expired(leeway=leeway):
        return acct
    tok = refresh_access_token(acct.refresh_token)
    acct.access_token = tok["access_token"]
    acct.expires_in = int(tok.get("expires_in", 3599))
    from datetime import datetime, timezone
    acct.expired = datetime.now(timezone.utc).isoformat(
        timespec="seconds").replace("+00:00", "Z")
    # store the expiry the way CLIProxyAPI does: expired + expires_in + ms timestamp
    acct.timestamp = int(time.time() * 1000)
    if save:
        acct.save()
    return acct


# ---------- interactive login (no binary needed) ----------

def build_auth_url(state: Optional[str] = None, *, redirect_uri: str = f"http://localhost:{constants.CALLBACK_PORT}/auth/callback") -> tuple[str, str]:
    """Build the consent-screen URL. Returns (url, state)."""
    state = state or secrets.token_urlsafe(16)
    q = urllib.parse.urlencode({
        "client_id": constants.CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(constants.SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })
    return f"{constants.AUTH_ENDPOINT}?{q}", state


def exchange_code(code: str, *, redirect_uri: str = f"http://localhost:{constants.CALLBACK_PORT}/auth/callback", timeout: int = 20) -> dict:
    """Exchange an authorization code for the initial token set."""
    data = urllib.parse.urlencode({
        "client_id": constants.CLIENT_ID,
        "client_secret": constants.CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }).encode()
    req = urllib.request.Request(constants.TOKEN_ENDPOINT, data=data)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return dict(json_resp(resp))
    except Exception as e:
        body = getattr(e, "read", lambda: b"")()
        raise OAuthError(f"code exchange failed: {e} {body[:200]!r}") from e


def fetch_userinfo(access_token: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(
        constants.USERINFO_ENDPOINT,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return dict(json_resp(resp))


def save_new_account(token_resp: dict, auth_dir: str, *, email: Optional[str] = None) -> AuthAccount:
    """Persist a fresh token response as a CLIProxyAPI-compatible auth file."""
    if email is None:
        try:
            email = fetch_userinfo(token_resp["access_token"]).get("email", "")
        except Exception:
            email = "unknown@gmail.com"
    from datetime import datetime, timezone
    acct = AuthAccount(
        path=None,  # set below
        email=email,
        access_token=token_resp["access_token"],
        refresh_token=token_resp.get("refresh_token", ""),
        expired=datetime.now(timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z"),
        expires_in=int(token_resp.get("expires_in", 3599)),
        timestamp=int(time.time() * 1000),
    )
    acct.path = f"{auth_dir}/antigravity-{email}.json"
    acct.save()
    return acct
