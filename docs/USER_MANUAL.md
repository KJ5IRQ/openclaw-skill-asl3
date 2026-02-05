# asl-control User Manual

**Node:** KJ5IRQ / 637050
**Backend:** FastAPI on Raspberry Pi, reachable via Tailscale
**Tool:** `skill/scripts/asl-tool.py` -- the single entry point for everything below

All examples were tested against the live node. Output shown is real.

---

## Prerequisites

Two environment variables. Both live in `~/.config/secrets/api-keys.env`:

- `ASL_PI_IP` -- Tailscale IP of the Pi running the ASL3 agent
- `ASL_API_KEY` -- Bearer token for the FastAPI backend

If you need to point at a different base URL (non-default port, etc.), set `ASL_API_BASE` to override the full `http://host:port` prefix.

**Before any command:**

```bash
source ~/.config/secrets/api-keys.env
```

---

## Quick Start

Three commands. That's the loop.

```bash
source ~/.config/secrets/api-keys.env
python3 skill/scripts/asl-tool.py report --out text
python3 skill/scripts/asl-tool.py connect 55553 --out text
```

Done. You're on the node.

---

## Output Modes

Every command supports `--out json` or `--out text`.

- `--out json` (default) -- machine-readable. Full payload. Use this for scripting.
- `--out text` -- human-readable one-liner. Use this for eyeballing in Discord or terminal.

All commands produce useful text in `--out text` mode. `report` is the most detailed; `status` and `nodes` are compact one-liners.

---

## Command Reference

### Monitoring

#### `report`

The daily driver for "what's happening on my node." Wraps `status` + `nodes` into one clean output.

```bash
# Human-readable (use this one)
python3 asl-tool.py report --out text

# Output:
# ASL Node Report: 637050 (KJ5IRQ)
# Uptime: 36:35:07
# Keyups today: 208
# Connected nodes: 8 - 1999, 2000, 466494, 55553, 56931, 584390, 598100, 62972
# System: ENABLED
# Scheduler: ENABLED
# Signal on input: NO
# Autopatch: ENABLED (state DOWN)
```

```bash
# Full JSON (for scripting -- includes raw ASL3 stats output)
python3 asl-tool.py report --out json
```

#### `status`

Raw node statistics from the ASL3 agent. Text mode gives you a compact one-liner; JSON gives you the full stats block.

```bash
python3 asl-tool.py status --out text
# Node 637050 (KJ5IRQ) | Up 37:39:41 | 298 keyups | System ENABLED | Sched ENABLED | Signal NO
```

```bash
python3 asl-tool.py status --out json
# Full raw_output array with every ASL3 stat, plus parsed node/callsign/keyups_today fields
```

#### `nodes`

Just the connected node list. Nothing else.

```bash
python3 asl-tool.py nodes --out text
# 15 nodes: 1883, 1995, 1998, 1999, 3452873, 578250, 578990, 623121, 623122, ...

# When empty:
# 0 nodes connected
```

```bash
python3 asl-tool.py nodes --out json
# { "connected_nodes": [...], "count": 15 }
```

#### `audit`

Recent activity log from the Pi backend. Timestamped.

```bash
python3 asl-tool.py audit --lines 5 --out json

# Output:
# {
#   "entries": [
#     "2026-02-05T00:42:59 | api | nodes | 0 nodes connected",
#     "2026-02-05T00:44:14 | api | status | Status retrieved",
#     ...
#   ],
#   "count": 5
# }
```

`--lines` controls how many entries. Default: 20.

---

### Connecting & Disconnecting

#### `connect`

Connect to a node. Two modes: transceive (default) or monitor-only.

```bash
# Transceive (full duplex)
python3 asl-tool.py connect 55553 --out text
# Connected to node 55553 (transceive)

# Monitor only (RX listen, no TX)
python3 asl-tool.py connect 55553 --monitor-only --out text
# Connected to node 55553 (monitor)
```

Connecting to a node you're already on works -- the backend accepts it. If you're in transceive and reconnect with `--monitor-only`, it switches you to monitor. Verified.

#### `disconnect`

Drop one specific node.

```bash
python3 asl-tool.py disconnect 55553 --out text
# Disconnected from node 55553
```

---

### Favorites

Named shortcuts to nodes. Saves you from typing node numbers.

#### Define a favorite

```bash
python3 asl-tool.py favorites set tac 55553 --out json
# {
#   "success": true,
#   "favorites": {
#     "tac": 55553
#   }
# }
```

#### List favorites

```bash
python3 asl-tool.py favorites list --out json
# {
#   "success": true,
#   "favorites": {
#     "tac": 55553
#   }
# }
```

#### Connect via favorite

```bash
python3 asl-tool.py connect-fav tac --out text
# Connected to tac (node 55553, transceive)

# Monitor-only:
python3 asl-tool.py connect-fav tac --monitor-only --out text
# Connected to tac (node 55553, monitor)
```

#### Remove a favorite

```bash
python3 asl-tool.py favorites remove tac --out json
# {
#   "success": true,
#   "favorites": {}
# }
```

Favorites are stored locally in `~/.openclaw/state/asl-control/favorites.json`. They don't touch the Pi.

---

### Net Profiles

The power feature. Define a named net with a node and a duration. Start it. It auto-disconnects when time runs out.

#### How it works

1. Define a profile (name, node, duration)
2. `net start <name>` -- connects and starts a countdown timer
3. `net tick` (run via cron) checks the timer. If expired, disconnects automatically.
4. Or call `net stop` to end early.

Auto-disconnect is the default. There is no "no-auto-disconnect" mode.

#### Define a net profile

```bash
python3 asl-tool.py net set tac 55553 --duration-minutes 2 --out json
# {
#   "success": true,
#   "profiles": {
#     "tac": {
#       "node": 55553,
#       "monitor_only": false,
#       "duration_minutes": 2
#     }
#   }
# }

# Monitor-only net:
python3 asl-tool.py net set scanner 55553 --duration-minutes 60 --monitor-only --out json
```

#### List net profiles

```bash
python3 asl-tool.py net list --out json
# {
#   "success": true,
#   "profiles": {
#     "tac": { "node": 55553, "monitor_only": false, "duration_minutes": 2 },
#     "ares": { "node": 55553, "monitor_only": false, "duration_minutes": 90 }
#   }
# }
```

#### Start a net session

```bash
python3 asl-tool.py net start tac --out text
# NET STARTED: tac -> node 55553 (transceive) for 2m (auto-disconnect)
```

Override the duration at start time if you want:

```bash
python3 asl-tool.py net start tac --duration-minutes 30 --out text
# NET STARTED: tac -> node 55553 (transceive) for 30m (auto-disconnect)
```

Only one net session can be active at a time.

#### Check status

```bash
python3 asl-tool.py net status --out text
# NET ACTIVE: tac -> node 55553 (remaining 1m59s)

# When nothing is running:
# No active net session
```

#### Tick (cron enforcement)

This is what enforces the auto-disconnect. Run it from cron every minute.

```bash
python3 asl-tool.py net tick --out text

# While time remains:
# NET OK: tac remaining 1m59s

# When the timer has expired (tick fires, disconnects, clears session):
# NET AUTO-DISCONNECT: node 55553

# When no session is active:
# No active net session
```

#### Stop early

```bash
python3 asl-tool.py net stop --out text
# NET STOPPED: disconnected node 55553
```

Clears the session immediately. `net tick` after this returns "No active net session."

#### Remove a profile

```bash
python3 asl-tool.py net remove tac --out json
# {
#   "success": true,
#   "profiles": {
#     "ares": { ... }   <-- only remaining profiles shown
#   }
# }
```

---

### Watch

Continuous monitor. Emits a JSON line every time the connected-nodes list changes. Designed to feed into alerting (cron + Discord, etc.).

```bash
python3 asl-tool.py watch --interval 2 --max-seconds 4 --emit-initial --out json

# First line (if --emit-initial):
# {"event": "initial", "nodes": []}

# On exit (no changes detected in the window):
# {"success": true, "changes": 0}
```

Flags:
- `--interval <seconds>` -- poll interval. Default: 5
- `--max-seconds <seconds>` -- total run time, then exit. Omit for infinite.
- `--emit-initial` -- print the current node list immediately on start, before watching for changes.

When a change happens, it emits a `{"event": "change", ...}` line. Use this to trigger alerts.

---

## Cron Recipe: Net Tick

To get auto-disconnect working, run `net tick` every minute:

```bash
* * * * * /bin/bash -c 'source ~/.config/secrets/api-keys.env && python3 /path/to/asl-tool.py net tick --out text >> ~/.openclaw/state/asl-control/tick.log 2>&1'
```

Or wire it into an OpenClaw cron job for Discord delivery.

---

## State Files

All local state lives here. Nothing in the git repo.

```
~/.openclaw/state/asl-control/
├── favorites.json       -- saved favorite name -> node mappings
├── net-profiles.json    -- named net profile definitions
└── net-session.json     -- active net session (cleared on stop/auto-disconnect)
```

Override the directory with `ASL_STATE_DIR` if needed.

---

## Known Issues

- **One active net session at a time.** Starting a second `net start` without stopping the first will overwrite the session file.
- **Nodes may auto-reconnect after disconnect.** If your node's scheduler is configured to maintain certain connections, they'll come right back. Disable the scheduler first if you need them to stay dropped.

---

## Troubleshooting

**"Connection refused" or timeout on any command:**
The Pi is unreachable. Check Tailscale: `tailscale status` and confirm `ASL_PI_IP` is correct.

**401 Unauthorized:**
`ASL_API_KEY` is wrong or not set. Check: `echo $ASL_API_KEY`

**"Not Found" (404):**
The endpoint doesn't exist on the backend. Known for `disconnect_all`. Check `audit` to see what the Pi actually logged.

**Net tick doesn't disconnect:**
Tick only fires when you run it. If you're not running it via cron, nothing happens automatically. The timer is checked, not enforced by a daemon.

**Favorites disappear after reinstall:**
They're in `~/.openclaw/state/asl-control/`, not the skill repo. They survive updates. If they're gone, someone deleted that directory.
