#!/usr/bin/env python3
"""gravpool CLI.

Usage:
  python -m gravpool.cli status  [--auth-dirs DIR ...]        # pool overview
  python -m gravpool.cli quota   [--auth-dirs DIR ...] [--out FILE]
  python -m gravpool.cli refresh [--auth-dirs DIR ...]        # refresh all
  python -m gravpool.cli gui     [--host H] [--port P]     # web dashboard
  python -m gravpool.cli login-binary [--binary PATH] [--config PATH]
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
from .proxy import ProxySupervisor
from .web import serve

DEFAULT_AUTH_DIRS = [
    "/root/.cli-proxy-api",
    "/root/.cli-proxy-api-2",
    "/root/.cli-proxy-api-3",
    "/root/.cli-proxy-api-writer",
]


def dirs_from(args) -> list[str]:
    if args.auth_dirs:
        return args.auth_dirs
    existing = [d for d in DEFAULT_AUTH_DIRS if os.path.isdir(d)]
    return existing or ["auth"]


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


def cmd_add_account(args) -> int:
    """One-command interactive login: browser consent -> callback -> save."""
    from .login_flow import add_account_cmd

    auth_dirs = dirs_from(args)
    auth_dir = args.auth_dir or (auth_dirs[0] if auth_dirs else "auth")
    try:
        acct = add_account_cmd(auth_dir, browser_open=not args.no_browser,
                               timeout=args.timeout)
    except (RuntimeError, OAuthError) as e:
        print(f"login failed: {e}", file=sys.stderr)
        return 1
    print(f"saved {acct.path}")
    return 0


def cmd_combo(args) -> int:
    from . import combo as combo_mod

    if args.combo_cmd == "list":
        combos = combo_mod.load_combos()
        if not combos:
            print("no combos yet — add one with 'combo add'")
            return 0
        for c in combos:
            print(f"{c.name:24} {c.kind:9} {', '.join(c.models)}")
        return 0

    if args.combo_cmd == "add":
        try:
            c = combo_mod.add_combo(args.name, args.models or [],
                                    kind=args.kind)
        except ValueError as e:
            print(f"add failed: {e}", file=sys.stderr)
            return 1
        print(f"combo {c.name} saved ({c.kind}, {len(c.models)} models)")
        return 0

    if args.combo_cmd == "rm":
        ok = combo_mod.remove_combo(args.name)
        print(f"removed {args.name}" if ok else f"combo {args.name} not found")
        return 0 if ok else 1

    if args.combo_cmd == "resolve":
        c = combo_mod.get_combo(args.name)
        if not c:
            print(f"combo {args.name} not found", file=sys.stderr)
            return 1
        accounts = load_accounts(dirs_from(args))
        snap = pool_quota(accounts)
        res = combo_mod.resolve_combo(args.name, snap,
                                      strategy=args.strategy or None,
                                      threshold=args.threshold)
        print(f"combo {res['combo']} [{res['strategy']}]")
        print(f"  picked : {res['picked']}")
        if res["fallback"]:
            print(f"  fallback: {', '.join(res['fallback'])}")
        if res["drained"]:
            print(f"  drained: {', '.join(res['drained'])}")
        print(f"  reason : {res['reason']}")
        return 0

    raise SystemExit("unknown combo subcommand")


def cmd_login_binary(args) -> int:
    """Run the pool binary's built-in `--antigravity-login` flow."""
    binary = args.binary or proxy_binary()
    cmd = [binary]
    if args.config:
        cmd += ["--config", args.config]
    cmd.append("--antigravity-login")
    print("running:", " ".join(cmd))
    os.execvp(cmd[0], cmd)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def proxy_binary() -> str:
    """Path to the bundled cli-proxy-api binary (repo-local, not a hardcoded path)."""
    bin_dir = os.path.join(REPO_ROOT, "bin")
    names = ["cli-proxy-api.exe", "cli-proxy-api"] if os.name == "nt" else ["cli-proxy-api"]
    for n in names:
        p = os.path.join(bin_dir, n)
        if os.path.isfile(p):
            return p
    return os.path.join(bin_dir, names[0])


def cmd_gui(args) -> int:
    """Serve the web dashboard."""
    proxy = None
    if not args.no_proxy:
        proxy = ProxySupervisor(proxy_binary(), dirs_from(args),
                                port=args.proxy_port if args.proxy_port else None)

    try:
        serve(dirs_from(args), host=args.host, port=args.port, proxy=proxy)
    finally:
        if proxy:
            proxy.stop()
    return 0

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="gravpool",
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
    sp.add_argument("--with-proxy", dest="no_proxy", action="store_false", default=False)
    sp.add_argument("--no-proxy", action="store_true", default=False)
    sp.add_argument("--proxy-port", type=int, default=0)
    sp.set_defaults(fn=cmd_gui)

    sp = sub.add_parser("login-binary", help="run cli-proxy-api --antigravity-login")
    sp.add_argument("--binary", default=None)
    sp.add_argument("--config", default=None)
    sp.set_defaults(fn=cmd_login_binary)

    sp = sub.add_parser("add-account", help="one-command browser login for a new account")
    add_dirs(sp)
    sp.add_argument("--auth-dir", default=None,
                    help="auth dir to write the new auth file into (default: first auth dir)")
    sp.add_argument("--no-browser", action="store_true",
                    help="print the consent URL instead of opening a browser")
    sp.add_argument("--timeout", type=int, default=300,
                    help="seconds to wait for the browser callback")
    sp.set_defaults(fn=cmd_add_account)

    sp = sub.add_parser("combo", help="manage virtual model combos (fallback/fusion)")
    add_dirs(sp)
    csub = sp.add_subparsers(dest="combo_cmd", required=True)
    csp = csub.add_parser("list", help="list combos")
    csp.set_defaults(fn=cmd_combo)
    csp = csub.add_parser("add", help="add/update a combo")
    csp.add_argument("name")
    csp.add_argument("models", nargs="*", help="ordered model names (space or comma separated)")
    csp.add_argument("--kind", choices=["fallback", "fusion"], default="fallback")
    csp.set_defaults(fn=cmd_combo)
    csp = csub.add_parser("rm", help="remove a combo")
    csp.add_argument("name")
    csp.set_defaults(fn=cmd_combo)
    csp = csub.add_parser("resolve", help="resolve a combo against live quota")
    csp.add_argument("name")
    csp.add_argument("--strategy", choices=["fallback", "fusion"], default=None)
    csp.add_argument("--threshold", type=float, default=0.05)
    csp.set_defaults(fn=cmd_combo)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
