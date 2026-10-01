#!/usr/bin/env bash
# GravPool quick setup — one command: check Python, login, done.
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] python3 not found. Install Python 3.9+ first, then run this again."
  exit 1
fi

python3 --version
echo
echo "Account login will open in your browser."
echo "Repeat this script for every account you want to add."
echo

python3 -m gravpool.cli add-account --auth-dir auth

echo
echo "Account added."
echo "Dashboard: python3 -m gravpool.cli gui  ->  http://127.0.0.1:8390"
