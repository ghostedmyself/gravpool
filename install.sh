#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[Gravpool] Checking Python installation..."
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "[ERROR] Python 3 not found."
    echo "Please install Python 3.9+ for your system."
    exit 1
fi

echo "[Gravpool] Running setup bundle..."
if ! "$PY" bundle.py; then
    echo "[ERROR] Setup bundle failed."
    exit 1
fi

echo ""
echo "========================================================"
echo "[SUCCESS] Gravpool setup completed!"
echo ""
echo "Next steps:"
echo "1. Start Dashboard:  $PY -m gravpool.cli gui --auth-dirs auth"
echo "   (Visit http://127.0.0.1:8390)"
echo "2. Start Proxy API:  bin/cli-proxy-api --config config.yaml"
echo "   (API at http://127.0.0.1:8317/v1)"
echo "========================================================"
echo ""
