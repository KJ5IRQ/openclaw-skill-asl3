#!/usr/bin/env python3
"""Deterministic client for the ASL Agent REST API.

Goal: provide a single, typed entrypoint that OpenClaw can invoke via exec.

Auth/env:
- ASL_PI_IP (or ASL_API_BASE) and ASL_API_KEY must be set.

New features (phase 2+):
- report: produce a clean human-readable node report (or JSON)
- favorites: save node numbers under short names
- watch: poll for connection changes and emit events

Examples:
  asl-tool.py status
  asl-tool.py nodes
  asl-tool.py report
  asl-tool.py connect 674982
  asl-tool.py connect 674982 --monitor-only
  asl-tool.py connect-fav net
  asl-tool.py favorites list
  asl-tool.py favorites set net 55553
  asl-tool.py favorites remove net
  asl-tool.py watch --interval 5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    return v


def _base_url() -> str:
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
        payload.setdefault("success", False)
        payload.setdefault("status", r.status_code)

    return payload


def _skill_dir() -> Path:
    # skill/scripts/asl-tool.py -> skill
    return Path(__file__).resolve().parents[1]


def _favorites_path() -> Path:
    # Keep local to the skill directory so it survives per-workspace.
    return _skill_dir() / "config" / "favorites.json"


def _load_favorites() -> dict[str, int]:
    p = _favorites_path()
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        favs = d.get("favorites", d)
        out: dict[str, int] = {}
        for k, v in favs.items():
            out[str(k)] = int(v)
        return out
    except Exception:
        raise SystemExit(f"Failed to read favorites: {p}")


def _save_favorites(favs: dict[str, int]) -> None:
    p = _favorites_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"favorites": favs}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cmd_status(_: argparse.Namespace) -> dict:
    return _req("GET", "/status")


def cmd_nodes(_: argparse.Namespace) -> dict:
    return _req("GET", "/nodes")


def cmd_connect(args: argparse.Namespace) -> dict:
    body = {"node": str(args.node), "monitor_only": bool(args.monitor_only)}
    return _req("POST", "/connect", json_body=body)


def cmd_connect_fav(args: argparse.Namespace) -> dict:
    favs = _load_favorites()
    if args.name not in favs:
        return {
            "success": False,
            "error": f"Favorite not found: {args.name}",
            "favorites": favs,
        }
    body = {"node": str(favs[args.name]), "monitor_only": bool(args.monitor_only)}
    out = _req("POST", "/connect", json_body=body)
    out.setdefault("favorite", args.name)
    return out


def cmd_disconnect(args: argparse.Namespace) -> dict:
    return _req("POST", "/disconnect", json_body={"node": str(args.node)})


def cmd_disconnect_all(_: argparse.Namespace) -> dict:
    return _req("POST", "/disconnect_all")


def cmd_audit(args: argparse.Namespace) -> dict:
    return _req("GET", f"/audit?lines={int(args.lines)}")


def _format_report(status: dict[str, Any], nodes: dict[str, Any]) -> str:
    node = status.get("node", "?")
    callsign = status.get("callsign", "")

    # status fields from backend are currently strings
    uptime = None
    raw = status.get("raw_output") or []
    for line in raw:
        if isinstance(line, str) and line.strip().startswith("Uptime"):
            uptime = line.split(":", 1)[-1].strip()

    connected_list = nodes.get("connected_nodes") or []
    # de-dupe while preserving order
    seen = set()
    dedup = []
    for n in connected_list:
        val = str(n.get("node", ""))
        if not val or val in seen:
            continue
        seen.add(val)
        dedup.append(n)

    count = len(dedup)
    node_ids = ", ".join([str(n.get("node")) for n in dedup][:25])
    if count > 25:
        node_ids += ", ..."

    keyups_today = status.get("keyups_today", "?")

    lines = []
    lines.append(f"ASL Node Report: {node}{(' (' + callsign + ')') if callsign else ''}")
    if uptime:
        lines.append(f"Uptime: {uptime}")
    lines.append(f"Keyups today: {keyups_today}")
    lines.append(f"Connected nodes: {count}{(' - ' + node_ids) if node_ids else ''}")

    # Asterisk stats we commonly care about
    def _find(prefix: str) -> str | None:
        for line in raw:
            if isinstance(line, str) and line.strip().startswith(prefix):
                return line.split(":", 1)[-1].strip()
        return None

    system = _find("System")
    sched = _find("Scheduler")
    sig = _find("Signal on input")
    autopatch = _find("Autopatch")
    autopatch_state = _find("Autopatch state")

    if system:
        lines.append(f"System: {system}")
    if sched:
        lines.append(f"Scheduler: {sched}")
    if sig:
        lines.append(f"Signal on input: {sig}")
    if autopatch:
        lines.append(f"Autopatch: {autopatch}{(' (state ' + autopatch_state + ')') if autopatch_state else ''}")

    return "\n".join(lines)


def cmd_report(args: argparse.Namespace) -> dict:
    status = _req("GET", "/status")
    nodes = _req("GET", "/nodes")

    report_text = _format_report(status, nodes)

    out: dict[str, Any] = {
        "success": bool(status.get("success", True)) and bool(nodes.get("success", True)),
        "node": status.get("node"),
        "callsign": status.get("callsign"),
        "report": report_text,
        "status": status,
        "nodes": nodes,
    }

    if args.format == "text":
        # Still return JSON wrapper for deterministic parsing, but put report first.
        out["output"] = report_text
    return out


def cmd_fav_list(_: argparse.Namespace) -> dict:
    return {"success": True, "favorites": _load_favorites()}


def cmd_fav_set(args: argparse.Namespace) -> dict:
    favs = _load_favorites()
    favs[args.name] = int(args.node)
    _save_favorites(favs)
    return {"success": True, "favorites": favs}


def cmd_fav_remove(args: argparse.Namespace) -> dict:
    favs = _load_favorites()
    if args.name in favs:
        favs.pop(args.name)
        _save_favorites(favs)
        return {"success": True, "favorites": favs}
    return {"success": False, "error": f"Favorite not found: {args.name}", "favorites": favs}


def _nodes_signature(nodes: dict[str, Any]) -> list[str]:
    lst = nodes.get("connected_nodes") or []
    out = []
    for n in lst:
        node = str(n.get("node", ""))
        mode = str(n.get("mode", ""))
        if node:
            out.append(f"{node}:{mode}")
    # de-dupe while preserving order
    seen = set()
    dedup = []
    for x in out:
        if x in seen:
            continue
        seen.add(x)
        dedup.append(x)
    return dedup


def cmd_watch(args: argparse.Namespace) -> dict:
    interval = float(args.interval)
    if interval < 1:
        return {"success": False, "error": "interval must be >= 1"}

    prev: list[str] | None = None
    start = time.time()

    # Stream events to stdout as JSON lines (one per change). Final return is a summary.
    changes = 0
    while True:
        nodes = _req("GET", "/nodes")
        sig = _nodes_signature(nodes)

        if prev is None:
            prev = sig
            if args.emit_initial:
                sys.stdout.write(json.dumps({"event": "initial", "nodes": sig}) + "\n")
                sys.stdout.flush()
        else:
            if sig != prev:
                prev_set = set(prev)
                sig_set = set(sig)
                joined = sorted(list(sig_set - prev_set))
                left = sorted(list(prev_set - sig_set))
                evt = {
                    "event": "change",
                    "joined": joined,
                    "left": left,
                    "nodes": sig,
                    "ts": int(time.time()),
                }
                sys.stdout.write(json.dumps(evt) + "\n")
                sys.stdout.flush()
                prev = sig
                changes += 1

        if args.max_seconds is not None and (time.time() - start) >= float(args.max_seconds):
            break
        time.sleep(interval)

    return {"success": True, "changes": changes}


def _print(out: dict) -> int:
    sys.stdout.write(json.dumps(out, indent=2, sort_keys=False) + "\n")
    return 0 if out.get("success", True) else 2


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="asl-tool.py", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("status", help="Get local node status")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("nodes", help="List connected nodes")
    sp.set_defaults(fn=cmd_nodes)

    sp = sub.add_parser("report", help="Human-friendly report (wraps /status + /nodes)")
    sp.add_argument("--format", choices=["json", "text"], default="text")
    sp.set_defaults(fn=cmd_report)

    sp = sub.add_parser("connect", help="Connect to a node")
    sp.add_argument("node", type=int, help="Target node number")
    sp.add_argument("--monitor-only", action="store_true", help="RX-only monitor mode")
    sp.set_defaults(fn=cmd_connect)

    sp = sub.add_parser("connect-fav", help="Connect using a saved favorite name")
    sp.add_argument("name", help="Favorite name")
    sp.add_argument("--monitor-only", action="store_true", help="RX-only monitor mode")
    sp.set_defaults(fn=cmd_connect_fav)

    sp = sub.add_parser("disconnect", help="Disconnect from a node")
    sp.add_argument("node", type=int, help="Target node number")
    sp.set_defaults(fn=cmd_disconnect)

    sp = sub.add_parser("disconnect-all", help="Drop all connections")
    sp.set_defaults(fn=cmd_disconnect_all)

    sp = sub.add_parser("audit", help="Read audit log")
    sp.add_argument("--lines", type=int, default=20, help="How many lines")
    sp.set_defaults(fn=cmd_audit)

    sp = sub.add_parser("favorites", help="Manage favorite node shortcuts")
    fav_sub = sp.add_subparsers(dest="fav_cmd", required=True)

    sp2 = fav_sub.add_parser("list", help="List favorites")
    sp2.set_defaults(fn=cmd_fav_list)

    sp2 = fav_sub.add_parser("set", help="Set favorite name -> node")
    sp2.add_argument("name")
    sp2.add_argument("node", type=int)
    sp2.set_defaults(fn=cmd_fav_set)

    sp2 = fav_sub.add_parser("remove", help="Remove favorite")
    sp2.add_argument("name")
    sp2.set_defaults(fn=cmd_fav_remove)

    sp = sub.add_parser("watch", help="Watch connected nodes and emit JSON-line events")
    sp.add_argument("--interval", type=float, default=5.0)
    sp.add_argument("--max-seconds", type=float, default=None)
    sp.add_argument("--emit-initial", action="store_true", help="Emit initial state event")
    sp.set_defaults(fn=cmd_watch)

    args = p.parse_args(argv)

    # Dispatch favorites subcommand
    if args.cmd == "favorites":
        out = args.fn(args)
        return _print(out)

    out = args.fn(args)
    return _print(out)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
