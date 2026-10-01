"""Round-robin account rotation over the auth pool.

Simple pool picker: skips disabled accounts and expired tokens (after an
optional refresh), rotating deterministically across the rest.
"""

from __future__ import annotations

import itertools
import threading

from .oauth import OAuthError, refresh_account
from .store import AuthAccount


class Rotator:
    """Thread-safe round-robin over Antigravity accounts.

    auto_refresh: refresh nearly-expired tokens before handing them out.
    leeway: seconds before the stored expiry to consider a token stale.
    """

    def __init__(self, accounts: list[AuthAccount], *, auto_refresh: bool = True,
                 leeway: int = 120):
        self._accounts = accounts
        self._lock = threading.Lock()
        self._cycle = itertools.cycle(accounts) if accounts else None
        self.auto_refresh = auto_refresh
        self.leeway = leeway

    def next(self) -> AuthAccount:
        """Next usable account; raises OAuthError only if every account fails."""
        if not self._accounts:
            raise OAuthError("pool is empty")
        with self._lock:
            tried = 0
            while tried < len(self._accounts):
                acct = next(self._cycle)
                tried += 1
                if acct.disabled:
                    continue
                if self.auto_refresh and acct.is_expired(leeway=self.leeway):
                    try:
                        acct = refresh_account(acct, leeway=0)
                    except OAuthError:
                        continue  # revoked/dead — try the next one
                return acct
        raise OAuthError("no usable account in pool (all disabled or revoked)")

    def usable(self) -> list[str]:
        return [a.email for a in self._accounts if not a.disabled]
