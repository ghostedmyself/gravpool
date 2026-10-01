# antigravity-pool

Turn **Google Antigravity Pro** accounts into a refreshable OAuth credential
pool with live quota reporting — OpenAI/Claude/Gemini-compatible quota for
free-ish Gemini 3 / Claude Sonnet access through the Antigravity (Cloud Code)
backend.

Verified working against live accounts (Oct 2026).

## How it works

```
Google OAuth (project aicode-consumers)
        │  refresh_token → access_token (ya29…)          oauth.py
        ▼
daily-cloudcode-pa.sandbox.googleapis.com
        │  v1internal:fetchAvailableModels               quota.py
        ▼
per-account quota: {model: {remaining 0..1, resetTime}}
```

- **Auth files** are CLIProxyAPI-compatible `antigravity-<email>.json`
  (drop-in: point `auth-dir` at the same directory).
- **Refresh** is a plain `oauth2.googleapis.com/token` call with the public
  embedded client credentials (same values the Antigravity IDE ships with).
- **Interactive login** reuses the pool binary's built-in
  `--antigravity-login` flag (see below), so you don't re-implement the OAuth
  dance.
- **Quota** comes from `fetchAvailableModels` — the same endpoint the IDE uses
  to render its model quota bars.

## Install

```bash
pip install -e .
# or just: python -m antigravity.cli … (stdlib only, no deps)
```

Set up the OAuth client credentials (public app credentials, see Notes):

```bash
cp antigravity/_local_creds.py.example antigravity/_local_creds.py
# edit it with the real ClientID/ClientSecret, or export
# ANTIGRAVITY_CLIENT_ID / ANTIGRAVITY_CLIENT_SECRET instead
```

## Usage

```bash
# pool overview (token state per account)
python -m antigravity.cli status

# live quota for every account (worst model summary, or full JSON via --out)
python -m antigravity.cli quota --out /var/www/ag_quota.json

# refresh every expired access token in place
python -m antigravity.cli refresh

# web dashboard (live quota bars + token state + one-click refresh)
python -m antigravity.cli gui --host 127.0.0.1 --port 8390
#   then open http://127.0.0.1:8390

# add a new account (opens the Google consent flow via cli-proxy-api)
python -m antigravity.cli login-binary --binary /opt/cli-proxy-api \
    --config /opt/cliproxy-config.yaml
```

Auth dirs default to `/root/.cli-proxy-api*`; override with
`--auth-dirs dir1 dir2`.

### Library use

```python
from antigravity.store import load_accounts
from antigravity.oauth import refresh_account
from antigravity.quota import pool_quota
from antigravity.rotate import Rotator

accounts = load_accounts(["/root/.cli-proxy-api"])
rot = Rotator(accounts)              # auto-refreshes + skips dead accounts
acct = rot.next()                    # round-robin, thread-safe
print(pool_quota([acct]))
```

### Cron example

```cron
# refresh tokens every 30 min, quota snapshot every 5 min
*/30 * * * * python -m antigravity.cli refresh >> /var/log/ag-pool.log 2>&1
*/5  * * * * python -m antigravity.cli quota --out /var/www/ag_quota.json >> /var/log/ag-pool.log 2>&1
```

## Web GUI

`python -m antigravity.cli gui` serves a zero-dependency dashboard:

- **token chips** per account (ok / expired / disabled)
- **live quota bars** per model, sorted worst-first (green >50%, amber >20%, red ≤20%)
- **one-click token refresh** (POST /api/refresh)
- 30 s quota cache, 60 s auto-poll — bind stays on 127.0.0.1 by default

Endpoints: `/` (page), `/api/status`, `/api/quota`, `/api/refresh`. The GUI
exposes token *state* only — never token values — so it's safe to run
locally; add your own auth if you ever bind it beyond localhost.

## Auth file shape

```json
{
  "access_token": "ya29.…",
  "disabled": false,
  "email": "user@gmail.com",
  "expired": "2026-10-01T13:01:06Z",
  "expires_in": 3599,
  "project_id": "aicode-consumers",
  "refresh_token": "1//0g…",
  "timestamp": 1790856067175,
  "type": "antigravity"
}
```

## Pairing with CLIProxyAPI

`cli-proxy-api` (router-for-me/CLIProxyAPI) consumes these auth files
directly and exposes an OpenAI-compatible endpoint in front of Antigravity:

```yaml
# /opt/cliproxy-config.yaml
host: 127.0.0.1
port: 8317
auth-dir: /root/.cli-proxy-api
api-keys: ["sk-…"]
```

This repo adds what the binary doesn't give you: standalone refresh, live
quota snapshots, and rotation logic you can embed in your own tooling.

## Files

| path | purpose |
|---|---|
| `antigravity/constants.py` | OAuth client + endpoints (from upstream CLIProxyAPI, public embedded creds) |
| `antigravity/store.py` | auth-file model, scanning, expiry logic |
| `antigravity/oauth.py` | refresh / code-exchange / userinfo / save-new-account |
| `antigravity/quota.py` | `fetchAvailableModels` client + snapshot writer |
| `antigravity/rotate.py` | thread-safe round-robin with auto-refresh |
| `antigravity/web.py` | zero-dependency web dashboard (status + quota + refresh) |
| `antigravity/cli.py` | `status` / `quota` / `refresh` / `gui` / `login-binary` |

## Notes

- The client ID/secret are **public embedded app credentials** (they identify
  the Antigravity app, not your account) — the same constants are shipped in
  the open-source upstream. Your `refresh_token`s are the real secret; keep
  auth dirs at `0700`.
- `remainingFraction` is Antigravity's own quota metric (0..1 per model);
  resets are rolling windows reported by `resetTime`.

## License

MIT
