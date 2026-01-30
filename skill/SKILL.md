---
name: asl-control
description: Monitor and control AllStar Link amateur radio nodes via REST API
metadata: {"moltbot":{"requires":{"bins":["pwsh"],"env":[]},"emoji":"📡"}}
---

# AllStar Link Node Control

Control and monitor your AllStar Link node through the ASL Agent REST API.

## How to Use This Skill

This skill provides PowerShell functions to interact with your AllStar Link node. To use any function, you must first source the helper script:

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

Edit `asl-api.ps1` to set:
- `$ASL_API_BASE` - Your Pi's IP and port (e.g., "http://192.168.1.88:8073")
- `$ASL_API_KEY` - Your API key from config.yaml

## Natural Language Usage (Telegram)

When the user asks in natural language, translate to appropriate commands:

**User:** "Check my node status"
**Action:** Run `Get-NodeStatus`

**User:** "What nodes are connected?"
**Action:** Run `Get-ConnectedNodes`

**User:** "Connect to node 55553"
**Action:** Run `Connect-Node -NodeNumber 55553`

**User:** "Disconnect from node 55553"
**Action:** Run `Disconnect-Node -NodeNumber 55553`

**User:** "Disconnect everything"
**Action:** Run `Disconnect-AllNodes`

## Important Notes

- Always source the script first before using any functions
- Connection verification takes approximately 8-10 seconds
- The API requires authentication via X-API-Key header
- All commands are logged to the audit trail
