#!/usr/bin/env python3
"""antigravity-pool CLI.

Usage:
  python -m antigravity.cli status  [--auth-dirs DIR ...]        # pool overview
  python -m antigravity.cli quota   [--auth-dirs DIR ...] [--out FILE]
  python -m antigravity.cli refresh [--auth-dirs DIR ...]        # refresh all
  python -m antigravity.cli gui     [--host H] [--port P]     # web dashboard
  python -m antigravity.cli login-binary [--binary PATH] [--config PATH]
                                                        # run --antigravity-login
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from .oauth import OAuthError, refresh_account
from .quota import pool_quota
from .store import load_accounts
from .web import serve

DEFAULT_AUTH_DIRS = [
    "/root/.cli-proxy-api",
    "/root/.cli-proxy-api-2",
    "/root/.cli-proxy-api-3",
    "/root/.cli-proxy-api-writer",
]


def dirs_from(args) -> list[str]:
    return args.auth_dirs or DEFAULT_AUTH_DIRS


def cmd_status(args) -> int:
    accounts = load_accounts(dirs_from(args))
    if not accounts:
        print("no antigravity-*.json auth files found", file=sys.stderr)
        return 1
    for a in accounts:
        state = "DISABLED" if a.disabled else ("EXPIRED" if a.is_expired() else "ok")
        print(f"{a.email:40} {state:9} {a.path}")
    return 0


def cmd_quota(args) -> int:
    accounts = load_accounts(dirs_from(args))
    snap = pool_quota(accounts)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(snap, f, indent=1)
        print(f"wrote {args.out}")
    else:
        for email, info in snap["accounts"].items():
            if "error" in info:
                print(f"{email:40} ERROR {info['error'][:60]}")
                continue
            worst = min(info["models"].items(), key=lambda kv: kv[1]["remaining"])
            print(f"{email:40} worst model: {worst[0]} = {worst[1]['remaining']*100:.0f}%")
    return 0


def cmd_refresh(args) -> int:
    accounts = load_accounts(dirs_from(args))
    ok = fail = 0
    for a in accounts:
        if a.disabled or not a.is_expired():
            continue
        try:
            refresh_account(a, leeway=0)
            ok += 1
            print(f"refreshed {a.email}")
        except OAuthError as e:
            fail += 1
            print(f"FAILED {a.email}: {e}", file=sys.stderr)
    print(f"\n{ok} refreshed, {fail} failed")
    return 1 if fail and not ok else 0


def cmd_login_binary(args) -> int:
    """Run the pool binary's built-in `--antigravity-login` flow."""
    binary = args.binary or "/opt/cli-proxy-api"
    cmd = [binary]
    if args.config:
        cmd += ["--config", args.config]
    cmd.append("--antigravity-login")
    print("running:", " ".join(cmd))
    os.execvp(cmd[0], cmd)


def cmd_gui(args) -> int:
    """Serve the web dashboard."""
    serve(dirs_from(args), host=args.host, port=args.port)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="antigravity-pool",
                                description="Manage a pool of Google Antigravity OAuth accounts")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_dirs(sp):
        sp.add_argument("--auth-dirs", nargs="*", default=None,
                        help="auth dirs containing antigravity-*.json")

    sp = sub.add_parser("status", help="list accounts + token state")
    add_dirs(sp)
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("quota", help="fetch live quota for every account")
    add_dirs(sp)
    sp.add_argument("--out", help="write full JSON snapshot to file")
    sp.set_defaults(fn=cmd_quota)

    sp = sub.add_parser("refresh", help="refresh expired access tokens")
    add_dirs(sp)
    sp.set_defaults(fn=cmd_refresh)

    sp = sub.add_parser("gui", help="serve the web dashboard")
    add_dirs(sp)
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8390)
    sp.set_defaults(fn=cmd_gui)

    sp = sub.add_parser("login-binary", help="run cli-proxy-api --antigravity-login")
    sp.add_argument("--binary", default="/opt/cli-proxy-api")
    sp.add_argument("--config", default=None)
    sp.set_defaults(fn=cmd_login_binary)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
