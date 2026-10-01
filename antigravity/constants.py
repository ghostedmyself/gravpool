"""OAuth client credentials and API endpoints for the Antigravity provider.

Client ID/secret are the public, embedded credentials used by the Antigravity
IDE itself — they identify the app, not the account. At runtime they load from
(1) environment variables, or (2) a gitignored ``antigravity/_local_creds.py``.
See ``antigravity/_local_creds.py.example`` and run
``cp antigravity/_local_creds.py.example antigravity/_local_creds.py`` to set
them up; the values match the open-source upstream CLIProxyAPI
``internal/auth/antigravity/constants.go``.
"""

import os

# --- OAuth client (public embedded app credentials) ---
CLIENT_ID = os.environ.get("ANTIGRAVITY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ANTIGRAVITY_CLIENT_SECRET", "")

if not CLIENT_ID or not CLIENT_SECRET:
    try:
        from . import _local_creds  # type: ignore
    except ImportError:
        _local_creds = None  # type: ignore
    if _local_creds:
        CLIENT_ID = _local_creds.CLIENT_ID
        CLIENT_SECRET = _local_creds.CLIENT_SECRET

CALLBACK_PORT = 51121

SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
]

# --- Google OAuth2 endpoints ---
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo?alt=json"

# --- Antigravity (Cloud Code) API ---
# The sandbox host is what the Antigravity IDE hits and is what we verified
# working; the non-sandbox host exists as fallback.
API_ENDPOINT = "https://daily-cloudcode-pa.sandbox.googleapis.com"
QUOTA_ENDPOINT = f"{API_ENDPOINT}/v1internal:fetchAvailableModels"
USER_AGENT = "antigravity/1.11.5 windows/amd64"

# --- auth file layout (CLIProxyAPI compatible) ---
AUTH_FILE_GLOB = "antigravity-*.json"