"""Auth file store — CLIProxyAPI-compatible JSON files.

Auth file shape (verified against a live pool):

    {
      "access_token": "ya29....",
      "disabled": false,
      "email": "user@gmail.com",
      "expired": "2026-10-01T13:01:06Z",
      "expires_in": 3599,
      "project_id": "aicode-consumers",
      "refresh_token": "1//0g...",
      "timestamp": 1790856067175,
      "type": "antigravity"
    }
"""

from __future__ import annotations

import glob
import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from .constants import AUTH_FILE_GLOB


@dataclass
class AuthAccount:
    """One Antigravity OAuth account loaded from (or destined for) a JSON file."""

    path: str
    email: str = ""
    access_token: str = ""
    refresh_token: str = ""
    project_id: str = "aicode-consumers"
    expired: str = ""  # ISO8601 UTC string as stored by CLIProxyAPI
    expires_in: int = 3599
    timestamp: int = 0
    disabled: bool = False
    extra: dict = field(default_factory=dict)

    # ---------- parsing ----------

    @classmethod
    def from_file(cls, path: str) -> "AuthAccount":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        known = {
            "access_token", "email", "refresh_token", "project_id",
            "expired", "expires_in", "timestamp", "disabled",
        }
        return cls(
            path=path,
            email=d.get("email", os.path.basename(path)),
            access_token=d.get("access_token", ""),
            refresh_token=d.get("refresh_token", ""),
            project_id=d.get("project_id", "aicode-consumers"),
            expired=d.get("expired", ""),
            expires_in=int(d.get("expires_in", 3599)),
            timestamp=int(d.get("timestamp", 0)),
            disabled=bool(d.get("disabled", False)),
            extra={k: v for k, v in d.items() if k not in known},
        )

    def to_dict(self) -> dict:
        d = {
            "access_token": self.access_token,
            "disabled": self.disabled,
            "email": self.email,
            "expired": self.expired,
            "expires_in": self.expires_in,
            "project_id": self.project_id,
            "refresh_token": self.refresh_token,
            "timestamp": self.timestamp or int(time.time() * 1000),
            "type": "antigravity",
        }
        d.update(self.extra)
        return d

    def save(self, path: Optional[str] = None) -> None:
        path = path or self.path
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=1)
        os.replace(tmp, path)

    # ---------- expiry ----------

    def expired_epoch(self) -> Optional[float]:
        """Parse the ISO8601 ``expired`` field into a unix timestamp."""
        if not self.expired:
            return None
        try:
            from datetime import datetime, timezone
            return datetime.fromisoformat(self.expired.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None

    def is_expired(self, leeway: int = 120) -> bool:
        ep = self.expired_epoch()
        if ep is None:
            return True
        return time.time() >= (ep - leeway)

    def filename(self) -> str:
        return os.path.basename(self.path)


# ---------- directory scanning ----------

def load_accounts(auth_dirs: list[str]) -> list[AuthAccount]:
    """Load every ``antigravity-*.json`` in the given auth dirs."""
    out: list[AuthAccount] = []
    for d in auth_dirs:
        for fp in sorted(glob.glob(os.path.join(d, AUTH_FILE_GLOB))):
            try:
                out.append(AuthAccount.from_file(fp))
            except (OSError, json.JSONDecodeError):
                continue
    return out
