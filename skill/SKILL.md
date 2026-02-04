---
name: asl-control
description: Monitor and control AllStar Link amateur radio nodes via REST API
metadata: {"moltbot":{"requires":{"bins":["pwsh"],"env":[]},"emoji":"📡"}}
---

# AllStar Link Node Control

Control and monitor your AllStar Link node through the ASL Agent REST API.

## Preferred interface (deterministic tool client)

Use the Python client (preferred over ad-hoc shell glue):

```bash
# Always load secrets first
source ~/.config/secrets/api-keys.env

# Run the deterministic client
python3 {baseDir}/scripts/asl-tool.py status
python3 {baseDir}/scripts/asl-tool.py nodes
python3 {baseDir}/scripts/asl-tool.py connect 55553
python3 {baseDir}/scripts/asl-tool.py connect 55553 --monitor-only
python3 {baseDir}/scripts/asl-tool.py disconnect 55553
python3 {baseDir}/scripts/asl-tool.py disconnect-all
python3 {baseDir}/scripts/asl-tool.py audit --lines 20
```

## Legacy interfaces (still supported)

This skill also provides PowerShell functions and a Bash helper script.

### PowerShell

To use any function, first source the helper script:

```powershell
. "<PATH_TO_SKILL>/scripts/asl-api.ps1"
```

## Available Functions

### Node Status and Monitoring
- **Get-NodeStatus** - Shows node uptime, keyup count, and connected nodes
- **Get-ConnectedNodes** - Lists all currently connected nodes
- **Get-AuditLog -Lines <n>** - View recent command history

### Node Connection Management
- **Connect-Node -NodeNumber <node>** - Connect to a node in transceive mode
- **Connect-Node -NodeNumber <node> -MonitorOnly** - Connect in monitor (RX only) mode
- **Disconnect-Node -NodeNumber <node>** - Disconnect from a specific node
- **Disconnect-AllNodes** - Disconnect from all nodes

## Examples

### Check node status
```powershell
. "<PATH_TO_SKILL>/scripts/asl-api.ps1"
Get-NodeStatus
```

### List connected nodes
```powershell
. "<PATH_TO_SKILL>/scripts/asl-api.ps1"
Get-ConnectedNodes
```

### Connect to a node
```powershell
. "<PATH_TO_SKILL>/scripts/asl-api.ps1"
Connect-Node -NodeNumber 55553
```

### Disconnect from a node
```powershell
. "<PATH_TO_SKILL>/scripts/asl-api.ps1"
Disconnect-Node -NodeNumber 55553
```

### View recent commands
```powershell
. "<PATH_TO_SKILL>/scripts/asl-api.ps1"
Get-AuditLog -Lines 20
```

## Configuration

### Bash (Linux / WSL) - Preferred
Set environment variables (or source your secrets file):
- `ASL_PI_IP` - Your Pi's Tailscale or LAN IP (e.g., "100.116.156.98")
- `ASL_API_KEY` - Your API key from config.yaml on the Pi (`/opt/asl-agent/config.yaml`)

Then source the script:
```bash
source ~/.config/secrets/api-keys.env  # or wherever your env vars live
source <PATH_TO_SKILL>/scripts/asl-api.sh
```

### PowerShell (Windows)
Edit `asl-api.ps1` to set:
- `$ASL_API_BASE` - Your Pi's IP and port (e.g., "http://100.116.156.98:8073")
- `$ASL_API_KEY` - Your API key from config.yaml

## Natural Language Usage (Discord / Telegram / any OpenClaw channel)

When the user asks in natural language, translate to the appropriate bash command via exec:

**User:** "Check my node status"
**Action:** `source asl-api.sh && asl_status`

**User:** "What nodes are connected?"
**Action:** `source asl-api.sh && asl_nodes`

**User:** "Connect to node 55553"
**Action:** `source asl-api.sh && asl_connect 55553`

**User:** "Connect to node 55553 monitor only"
**Action:** `source asl-api.sh && asl_connect 55553 true`

**User:** "Disconnect from node 55553"
**Action:** `source asl-api.sh && asl_disconnect 55553`

**User:** "Disconnect everything"
**Action:** `source asl-api.sh && asl_disconnect_all`

**User:** "Show me the audit log"
**Action:** `source asl-api.sh && asl_audit 20`

## Important Notes

- Always source the secrets env file before the script (for ASL_API_KEY)
- Tailscale IP is preferred over LAN IP for the Pi (works from anywhere)
- Connection verification takes approximately 8-10 seconds
- The API requires authentication via X-API-Key header
- All commands are logged to the audit trail on the Pi at `/opt/asl-agent/audit.log`
- Known: some nodes auto-reconnect after disconnect (scheduler or remote node behavior) - this is an AllStar config issue, not an API bug
