#!/usr/bin/env bash
#
# GravPool — one-command installer (public release)
#
#   curl -LsSf https://raw.githubusercontent.com/ghostedmyself/gravpool/main/install.sh | bash
#
# Installs GravPool into ~/.gravpool, fetches the CLIProxyAPI proxy binary,
# puts a `gravpool` launcher on PATH, and starts the dashboard + /v1 gateway.
# Safe to re-run (idempotent): updates the repo, never touches your auth/keys.
#
set -euo pipefail

REPO_URL="https://github.com/ghostedmyself/gravpool.git"
# Code lives in a share dir; ~/.gravpool is reserved for runtime data
# (providers.json / combos.json) so it never bleeds into the install.
INSTALL_DIR="${GRAVPOOL_HOME:-$HOME/.local/share/gravpool}"
BIN_LINK="$HOME/.local/bin/gravpool"   # also covered if PATH fallback

echo "== GravPool installer =="
echo "  target: $INSTALL_DIR"

# 1. Python check
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then
    # require >= 3.9
    if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' 2>/dev/null; then
      PY="$c"
      break
    fi
  fi
done
if [ -z "$PY" ]; then
  echo "[ERROR] Python 3.9+ not found. Install Python then re-run." >&2
  exit 1
fi
echo "  python: $PY $(command "$PY" --version 2>&1)"

# 2. Clone / update the repo
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "  updating existing install..."
  ( cd "$INSTALL_DIR" && git pull --ff-only -q ) || echo "  (update skipped/failed — continuing with existing)"
else
  mkdir -p "$INSTALL_DIR"
  echo "  cloning..."
  git clone -q "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# 3. Fetch the CLIProxyAPI proxy binary (idempotent; skips if already present)
if [ ! -x "bin/cli-proxy-api" ] && [ ! -f "bin/cli-proxy-api.exe" ]; then
  echo "  fetching proxy binary..."
  "$PY" bundle.py --no-login || echo "  (proxy fetch failed — GravPool still works for external providers)"
else
  echo "  proxy binary present"
fi

# 4. Wire up a launcher on PATH
mkdir -p "$HOME/.local/bin"
cat > "$BIN_LINK" <<LAUNCH
#!/usr/bin/env bash
cd "$INSTALL_DIR"
exec "$PY" -m gravpool.cli "\$@"
LAUNCH
chmod +x "$BIN_LINK"

# 5. Ensure PATH hint (non-fatal)
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "  NOTE: add ~/.local/bin to your PATH to use \`gravpool\` directly, or use:" ;;
esac

echo ""
echo "=============================================================="
echo " GravPool installed at $INSTALL_DIR"
echo ""
echo " Start the gateway + dashboard:"
echo "   gravpool gui --port 8390"
echo "   # or: $PY -m gravpool.cli gui --port 8390"
echo ""
echo " Dashboard : http://127.0.0.1:8390"
echo " API       : http://127.0.0.1:8390/v1   (key: sk-local)"
echo ""
echo " Add accounts / providers from the dashboard (Add Account / Add Provider)."
echo "=============================================================="
echo ""
