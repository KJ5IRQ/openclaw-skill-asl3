#!/usr/bin/env python3
"""Deterministic client for the ASL Agent REST API.

Why this exists:
- Avoids ad-hoc shell glue and quoting issues.
- Provides a single, typed entrypoint that can be invoked from OpenClaw via exec.

Auth/env:
- ASL_PI_IP (or ASL_API_BASE) and ASL_API_KEY must be set.

Examples:
  asl-tool.py status
  asl-tool.py nodes
  asl-tool.py connect 674982
  asl-tool.py connect 674982 --monitor-only
  asl-tool.py disconnect 674982
  asl-tool.py disconnect-all
  asl-tool.py audit --lines 50
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import urljoin

import requests


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    return v


def _base_url() -> str:
    # Prefer explicit base URL, else build from ASL_PI_IP
    base = _env("ASL_API_BASE")
    if base:
        return base.rstrip("/") + "/"

    ip = _env("ASL_PI_IP")
    if not ip:
        raise SystemExit("Missing ASL_API_BASE or ASL_PI_IP in environment")
    return f"http://{ip}:8073/"


def _api_key() -> str:
    key = _env("ASL_API_KEY")
    if not key:
        raise SystemExit("Missing ASL_API_KEY in environment")
    return key


def _req(method: str, path: str, *, json_body: dict | None = None) -> dict:
    url = urljoin(_base_url(), path.lstrip("/"))
    headers = {"X-API-Key": _api_key()}

    r = requests.request(method, url, headers=headers, json=json_body, timeout=30)
    try:
        payload = r.json()
    except Exception:
        payload = {"success": False, "status": r.status_code, "text": r.text}

    if not r.ok:
        # Keep deterministic output for the agent
        payload.setdefault("success", False)
        payload.setdefault("status", r.status_code)

    return payload


def cmd_status(_: argparse.Namespace) -> dict:
    return _req("GET", "/status")


def cmd_nodes(_: argparse.Namespace) -> dict:
    return _req("GET", "/nodes")


def cmd_connect(args: argparse.Namespace) -> dict:
    body = {
        "node": str(args.node),
        "monitor_only": bool(args.monitor_only),
    }
    return _req("POST", "/connect", json_body=body)


def cmd_disconnect(args: argparse.Namespace) -> dict:
    return _req("POST", "/disconnect", json_body={"node": str(args.node)})


def cmd_disconnect_all(_: argparse.Namespace) -> dict:
    return _req("POST", "/disconnect_all")


def cmd_audit(args: argparse.Namespace) -> dict:
    return _req("GET", f"/audit?lines={int(args.lines)}")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="asl-tool.py", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("status", help="Get local node status")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("nodes", help="List connected nodes")
    sp.set_defaults(fn=cmd_nodes)

    sp = sub.add_parser("connect", help="Connect to a node")
    sp.add_argument("node", type=int, help="Target node number")
    sp.add_argument("--monitor-only", action="store_true", help="RX-only monitor mode")
    sp.set_defaults(fn=cmd_connect)

    sp = sub.add_parser("disconnect", help="Disconnect from a node")
    sp.add_argument("node", type=int, help="Target node number")
    sp.set_defaults(fn=cmd_disconnect)

    sp = sub.add_parser("disconnect-all", help="Drop all connections")
    sp.set_defaults(fn=cmd_disconnect_all)

    sp = sub.add_parser("audit", help="Read audit log")
    sp.add_argument("--lines", type=int, default=20, help="How many lines")
    sp.set_defaults(fn=cmd_audit)

    args = p.parse_args(argv)
    out = args.fn(args)
    sys.stdout.write(json.dumps(out, indent=2, sort_keys=False) + "\n")
    return 0 if out.get("success", True) else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
