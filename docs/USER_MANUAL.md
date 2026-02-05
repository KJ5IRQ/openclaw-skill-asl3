# ASL Control — `asl-tool.py` User Manual (Verified)

This is a **verified, command-line user manual** for the `asl-control` skill’s deterministic client:

- Script: `skill/scripts/asl-tool.py`
- Purpose: a single, predictable CLI entrypoint to the **ASL Agent REST API**
- Typical target: your AllStarLink node **637050 (KJ5IRQ)** via the Pi’s agent (`:8073`)

Everything in the **Examples** sections below was run against the live API first.

---

## Prerequisites

### Required environment variables

You must have:

- `ASL_API_KEY`
- Either:
  - `ASL_API_BASE` (full base URL, e.g. `http://host:8073/`), **or**
  - `ASL_PI_IP` (IP/host for the Pi; base becomes `http://<ASL_PI_IP>:8073/`)

Optional:

- `ASL_STATE_DIR`
  - If not set, state is stored at:
    - `~/.openclaw/state/asl-control/`

### Where the env vars live on this system

On this OpenClaw host, they’re typically loaded from:

```bash
source /home/kj5irq/.config/secrets/api-keys.env
```

---

## Quick Start (3 lines)

```bash
cd /home/kj5irq/.openclaw/workspace/openclaw-skill-asl3/skill/scripts
source /home/kj5irq/.config/secrets/api-keys.env
./asl-tool.py report --out text
```

Verified output (example):

```text
ASL Node Report: 637050 (KJ5IRQ)
Uptime: 36:29:28
Keyups today: 204
Connected nodes: 0
System: ENABLED
Scheduler: ENABLED
Signal on input: NO
Autopatch: ENABLED (state DOWN)
```

---

## Output modes (`--out`)

Most commands support:

- `--out json` (default)
  - Pretty-printed JSON; exit code is **0 on success**, **2 on failure**.
- `--out text`
  - Prints `output` (or `report`) if present; otherwise falls back to `OK`/error text.

Note: Some commands (notably `connect-fav`) may print `OK` in text mode when the API response doesn’t include an `output` field.

---

## Command Reference

### Status & reporting

#### `status`

- What it does:
  - Calls `GET /status` on the ASL Agent.

Syntax:

```bash
./asl-tool.py status [--out json|text]
```

Example (verified):

```bash
./asl-tool.py status --out json
```

Output:

```json
{
  "raw_output": [
    "************************ NODE 637050 STATISTICS *************************",
    "",
    "Selected system state............................: 0",
    "Signal on input..................................: NO",
    "System...........................................: ENABLED",
    "Parrot Mode......................................: DISABLED",
    "Scheduler........................................: ENABLED",
    "Tail Time........................................: STANDARD",
    "Time out timer...................................: ENABLED",
    "Incoming connections.............................: ENABLED",
    "Time out timer state.............................: RESET",
    "Time outs since system initialization............: 0",
    "Identifier state.................................: CLEAN",
    "Kerchunks today..................................: 0",
    "Kerchunks since system initialization............: 1",
    "Keyups today.....................................: 204",
    "Keyups since system initialization...............: 214",
    "DTMF commands today..............................: 0",
    "DTMF commands since system initialization........: 0",
    "Last DTMF command executed.......................: N/A",
    "TX time today....................................: 01:50:58:281",
    "TX time since system initialization..............: 01:53:43:52",
    "Uptime...........................................: 36:29:25",
    "Nodes currently connected to us..................: <NONE>",
    "Autopatch........................................: ENABLED",
    "Autopatch state..................................: DOWN",
    "Autopatch called number..........................: N/A",
    "Reverse patch/IAXRPT connected...................: DOWN",
    "User linking commands............................: ENABLED",
    "User functions...................................: ENABLED"
  ],
  "node": "637050",
  "callsign": "KJ5IRQ",
  "keyups_today": "204",
  "uptime": "25",
  "connected_nodes": "None"
}
```

Example (verified):

```bash
./asl-tool.py status --out text
```

Output:

```text
OK
```

(For `status`, `--out text` currently falls back to `OK` because the backend payload does not include an `output` field.)

---

#### `nodes`

- What it does:
  - Calls `GET /nodes` and returns connected-node list.

Syntax:

```bash
./asl-tool.py nodes [--out json|text]
```

Example (verified):

```bash
./asl-tool.py nodes --out json
```

Output:

```json
{
  "connected_nodes": [],
  "count": 0
}
```

Example (verified):

```bash
./asl-tool.py nodes --out text
```

Output:

```text
OK
```

(Like `status`, `nodes --out text` falls back to `OK` because there is no `output` field.)

---

#### `report`

- What it does:
  - Calls `/status` + `/nodes`, then produces a **human-friendly** roll-up.

Syntax:

```bash
./asl-tool.py report [--format text|json] [--out json|text]
```

Notes:

- `--format` controls the report format inside the JSON wrapper.
- In practice:
  - `./asl-tool.py report --out text` prints the report.
  - `./asl-tool.py report --out json` returns JSON with `report`, plus the raw `status` and `nodes` payloads.

Example (verified):

```bash
./asl-tool.py report --out text
```

Output:

```text
ASL Node Report: 637050 (KJ5IRQ)
Uptime: 36:29:28
Keyups today: 204
Connected nodes: 0
System: ENABLED
Scheduler: ENABLED
Signal on input: NO
Autopatch: ENABLED (state DOWN)
```

Example (verified):

```bash
./asl-tool.py report --out json
```

Output (trimmed here only by JSON formatting, not content):

```json
{
  "success": true,
  "node": "637050",
  "callsign": "KJ5IRQ",
  "report": "ASL Node Report: 637050 (KJ5IRQ)\nUptime: 36:29:28\nKeyups today: 204\nConnected nodes: 0\nSystem: ENABLED\nScheduler: ENABLED\nSignal on input: NO\nAutopatch: ENABLED (state DOWN)",
  "status": {
    "raw_output": [
      "************************ NODE 637050 STATISTICS *************************",
      "",
      "Selected system state............................: 0",
      "Signal on input..................................: NO",
      "System...........................................: ENABLED",
      "Parrot Mode......................................: DISABLED",
      "Scheduler........................................: ENABLED",
      "Tail Time........................................: STANDARD",
      "Time out timer...................................: ENABLED",
      "Incoming connections.............................: ENABLED",
      "Time out timer state.............................: RESET",
      "Time outs since system initialization............: 0",
      "Identifier state.................................: CLEAN",
      "Kerchunks today..................................: 0",
      "Kerchunks since system initialization............: 1",
      "Keyups today.....................................: 204",
      "Keyups since system initialization...............: 214",
      "DTMF commands today..............................: 0",
      "DTMF commands since system initialization........: 0",
      "Last DTMF command executed.......................: N/A",
      "TX time today....................................: 01:50:58:281",
      "TX time since system initialization..............: 01:53:43:52",
      "Uptime...........................................: 36:29:28",
      "Nodes currently connected to us..................: <NONE>",
      "Autopatch........................................: ENABLED",
      "Autopatch state..................................: DOWN",
      "Autopatch called number..........................: N/A",
      "Reverse patch/IAXRPT connected...................: DOWN",
      "User linking commands............................: ENABLED",
      "User functions...................................: ENABLED"
    ],
    "node": "637050",
    "callsign": "KJ5IRQ",
    "keyups_today": "204",
    "uptime": "28",
    "connected_nodes": "None"
  },
  "nodes": {
    "connected_nodes": [],
    "count": 0
  },
  "output": "ASL Node Report: 637050 (KJ5IRQ)\nUptime: 36:29:28\nKeyups today: 204\nConnected nodes: 0\nSystem: ENABLED\nScheduler: ENABLED\nSignal on input: NO\nAutopatch: ENABLED (state DOWN)"
}
```

---

### Linking (connect/disconnect)

#### `connect`

- What it does:
  - Calls `POST /connect` with `{ node, monitor_only }`.

Syntax:

```bash
./asl-tool.py connect <node> [--monitor-only] [--out json|text]
```

Example (verified; node **55553**):

```bash
./asl-tool.py connect 55553 --out text
```

Output:

```text
Connected to node 55553 (transceive)
```

Example (verified; monitor-only):

```bash
./asl-tool.py connect 55553 --monitor-only --out json
```

Output:

```json
{
  "success": true,
  "message": "Connected to node 55553 in monitor mode",
  "node": "55553",
  "mode": "monitor",
  "output": "Connected to node 55553 (monitor)"
}
```

Behavior note (verified):

- If you run `connect` again while already connected, the API accepted it and effectively **switched mode**:

```bash
./asl-tool.py connect 55553 --monitor-only --out text
```

Output:

```text
Connected to node 55553 (monitor)
```

---

#### `disconnect`

- What it does:
  - Calls `POST /disconnect` with `{ node }`.

Syntax:

```bash
./asl-tool.py disconnect <node> [--out json|text]
```

Example (verified; node **55553**):

```bash
./asl-tool.py disconnect 55553 --out text
```

Output:

```text
Disconnected from node 55553
```

---

#### `disconnect-all`

- What it does:
  - Intended to call `POST /disconnect_all`.

Syntax:

```bash
./asl-tool.py disconnect-all [--out json|text]
```

Verified result on this system (IMPORTANT):

- The ASL Agent returned **404 Not Found** for `/disconnect_all`.
- `asl-tool.py` exits with code **2** (failure).

Example (verified):

```bash
./asl-tool.py disconnect-all --out json
```

Output (as captured by the OpenClaw exec tool):

```text
{
  "detail": "Not Found",
  "success": false,
  "status": 404,
  "output": "Failed to disconnect all nodes"
}

Command exited with code 2
```

Workaround:

- Use `nodes` to enumerate connected nodes, then call `disconnect <node>` for each.

---

### Favorites

Favorites are local shortcuts stored in a JSON file (see **State files**).

#### `favorites list`

Syntax:

```bash
./asl-tool.py favorites list [--out json|text]
```

Example (verified):

```bash
./asl-tool.py favorites list --out json
```

Output:

```json
{
  "success": true,
  "favorites": {}
}
```

---

#### `favorites set`

Syntax:

```bash
./asl-tool.py favorites set <name> <node> [--out json|text]
```

Example (verified; sets `testfav -> 55553`):

```bash
./asl-tool.py favorites set testfav 55553 --out json
```

Output:

```json
{
  "success": true,
  "favorites": {
    "testfav": 55553
  }
}
```

---

#### `favorites remove`

Syntax:

```bash
./asl-tool.py favorites remove <name> [--out json|text]
```

Example (verified):

```bash
./asl-tool.py favorites remove testfav --out json
```

Output:

```json
{
  "success": true,
  "favorites": {}
}
```

---

#### `connect-fav`

- What it does:
  - Loads favorites locally, then calls `POST /connect` for the saved node.

Syntax:

```bash
./asl-tool.py connect-fav <name> [--monitor-only] [--out json|text]
```

Example (verified):

```bash
./asl-tool.py connect-fav testfav --out text
```

Output:

```text
OK
```

Why it printed `OK`:

- The API response in this case didn’t include an `output` field, so text mode fell back to `OK`.

Example (verified; JSON shows the real payload):

```bash
./asl-tool.py connect-fav testfav --out json
```

Output:

```json
{
  "success": true,
  "message": "Connected to node 55553 in transceive mode",
  "node": "55553",
  "mode": "transceive",
  "favorite": "testfav"
}
```

---

### Net Profiles & timed net sessions

This is the “big feature”: create named profiles and run a **timed session** with auto-disconnect enforcement.

Concepts:

- **Profile**: a saved config `{ node, monitor_only, duration_minutes }`.
- **Session**: a currently-running net session, saved to disk with an `end_ts`.
- **Auto-disconnect**: enforced by running `net tick` (cron-friendly).

#### `net list`

Syntax:

```bash
./asl-tool.py net list [--out json|text]
```

Example (verified):

```bash
./asl-tool.py net list --out json
```

Output (note: an existing `ares` profile was already present):

```json
{
  "success": true,
  "profiles": {
    "ares": {
      "duration_minutes": 1,
      "monitor_only": false,
      "node": 55553
    }
  }
}
```

---

#### `net set`

Syntax:

```bash
./asl-tool.py net set <name> <node> [--monitor-only] [--duration-minutes N] [--out json|text]
```

Example (verified; creates `testn`):

```bash
./asl-tool.py net set testn 55553 --duration-minutes 2 --out json
```

Output:

```json
{
  "success": true,
  "profiles": {
    "ares": {
      "duration_minutes": 1,
      "monitor_only": false,
      "node": 55553
    },
    "testn": {
      "node": 55553,
      "monitor_only": false,
      "duration_minutes": 2
    }
  }
}
```

---

#### `net start`

- What it does:
  - Connects immediately to the profile’s node.
  - Writes a `net-session.json` with an end timestamp.

Syntax:

```bash
./asl-tool.py net start <name> [--duration-minutes N] [--out json|text]
```

Example (verified):

```bash
./asl-tool.py net start testn --out text
```

Output:

```text
NET STARTED: testn -> node 55553 (transceive) for 2m (auto-disconnect)
```

---

#### `net status`

Syntax:

```bash
./asl-tool.py net status [--out json|text]
```

Example (verified):

```bash
./asl-tool.py net status --out text
```

Output:

```text
NET ACTIVE: testn -> node 55553 (remaining 1m58s)
```

---

#### `net tick`

- What it does:
  - If the session is still active: prints remaining time.
  - If expired: disconnects and clears the session file.

Syntax:

```bash
./asl-tool.py net tick [--out json|text]
```

Example (verified; session active):

```bash
./asl-tool.py net tick --out text
```

Output:

```text
NET OK: testn remaining 1m56s
```

Example (verified; no active session):

```bash
./asl-tool.py net tick --out text
```

Output:

```text
No active net session
```

---

#### `net stop`

- What it does:
  - Disconnects the session node immediately and clears the session file.

Syntax:

```bash
./asl-tool.py net stop [--out json|text]
```

Example (verified):

```bash
./asl-tool.py net stop --out text
```

Output:

```text
NET STOPPED: disconnected node 55553
```

---

#### `net remove`

Syntax:

```bash
./asl-tool.py net remove <name> [--out json|text]
```

Example (verified):

```bash
./asl-tool.py net remove testn --out json
```

Output:

```json
{
  "success": true,
  "profiles": {
    "ares": {
      "duration_minutes": 1,
      "monitor_only": false,
      "node": 55553
    }
  }
}
```

---

### Monitoring

#### `audit`

- What it does:
  - Calls `GET /audit?lines=N`.

Syntax:

```bash
./asl-tool.py audit [--lines N] [--out json|text]
```

Example (verified):

```bash
./asl-tool.py audit --lines 10 --out json
```

Output:

```json
{
  "entries": [
    "2026-02-05T00:41:04.942259 | api | nodes | 0 nodes connected",
    "2026-02-05T00:41:20.319025 | api | connect | Node 55553 (transceive)",
    "2026-02-05T00:41:31.616551 | api | connect | Node 55553 (transceive)",
    "2026-02-05T00:41:40.126731 | api | disconnect | Node 55553",
    "2026-02-05T00:41:51.747318 | api | connect | Node 55553 (transceive)",
    "2026-02-05T00:42:02.378244 | api | connect | Node 55553 (monitor)",
    "2026-02-05T00:42:12.956477 | api | connect | Node 55553 (monitor)",
    "2026-02-05T00:42:19.999567 | api | disconnect | Node 55553",
    "2026-02-05T00:42:36.400188 | api | connect | Node 55553 (transceive)",
    "2026-02-05T00:42:47.532080 | api | disconnect | Node 55553"
  ],
  "count": 10
}
```

---

#### `watch`

- What it does:
  - Polls `GET /nodes` and emits **JSON Lines** events to stdout.
  - Emits an `initial` event if `--emit-initial` is set.
  - Emits `change` events when connected nodes differ.

Syntax:

```bash
./asl-tool.py watch [--interval SECONDS] [--max-seconds SECONDS] [--emit-initial] [--out json|text]
```

Example (verified; bounded):

```bash
./asl-tool.py watch --interval 2 --max-seconds 4 --emit-initial --out json
```

Output:

```json
{"event": "initial", "nodes": []}
{
  "success": true,
  "changes": 0
}
```

Notes:

- The first line is an **event line** (JSONL).
- The last block is the command’s final JSON summary.

---

## Favorites (workflow)

Typical flow:

- Save a node number under a short name
- Connect by name
- Remove when you’re done

Verified example sequence (using node **55553**):

```bash
./asl-tool.py favorites set testfav 55553 --out json
./asl-tool.py connect-fav testfav --out json
./asl-tool.py disconnect 55553 --out text
./asl-tool.py favorites remove testfav --out json
```

---

## Net Profiles (workflow)

A clean “net night” flow:

- Define a profile with a duration
- Start it
- Periodically enforce with `net tick` (cron)
- Stop early if needed

Verified example sequence:

```bash
./asl-tool.py net set testn 55553 --duration-minutes 2 --out json
./asl-tool.py net start testn --out text
./asl-tool.py net status --out text
./asl-tool.py net tick --out text
./asl-tool.py net stop --out text
./asl-tool.py net remove testn --out json
```

Cron-friendly enforcement idea:

- Run `net tick` every minute (or every 30s) from cron/systemd timer.
- When the session expires, `net tick` will disconnect and clear state.

---

## Troubleshooting

### “Missing ASL_API_BASE or ASL_PI_IP in environment”

- Set one of:
  - `ASL_API_BASE=http://<host>:8073/`
  - `ASL_PI_IP=<host>`

### “Missing ASL_API_KEY in environment”

- Load your secrets:

```bash
source /home/kj5irq/.config/secrets/api-keys.env
```

### `disconnect-all` fails

Verified on this system:

- `/disconnect_all` returned **404 Not Found**.
- This is an API/backend mismatch (CLI expects the endpoint).

Workaround:

- Use `nodes --out json` and disconnect individually.

### Text mode only prints `OK`

- This happens when the response doesn’t include `output` (or `report`).
- Use `--out json` when you need details.

---

## State files (where things live)

Default state directory:

- `~/.openclaw/state/asl-control/`

Files:

- `favorites.json`
  - Stores `{"favorites": {"name": nodeNumber}}`
- `net-profiles.json`
  - Stores profiles by name
- `net-session.json`
  - Created by `net start`
  - Cleared by `net stop` or an expired `net tick`

You can override the directory with:

- `ASL_STATE_DIR=/some/path`

---

## Safety / operational notes (ham-friendly)

- **Be deliberate with transceive vs monitor-only.**
  - `--monitor-only` is a safe “listen only” link.
- Keep your linking clean:
  - Prefer timed nets + `net tick` so you don’t leave links up overnight.
