$ErrorActionPreference = 'Stop'

# Load the official ASL Control skill API helpers
. 'C:\Users\kj5ir\AppData\Roaming\npm\node_modules\clawdbot\skills\asl-control\scripts\asl-api.ps1'

# Load our alias resolver
. (Join-Path $PSScriptRoot 'asl-alias.ps1')

# Default alias map lives in the clawd workspace root
$ASL_ALIAS_PATH = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'asl-node-aliases.json')

function Connect-ASL {
  param(
    [Parameter(Mandatory=$true)][string]$NodeOrAlias,
    [switch]$MonitorOnly
  )

  $node = Resolve-ASLNode -NodeOrAlias $NodeOrAlias -AliasPath $ASL_ALIAS_PATH
  return Safe-Connect-Node -NodeNumber $node -MonitorOnly:$MonitorOnly
}

function Disconnect-ASL {
  param([Parameter(Mandatory=$true)][string]$NodeOrAlias)

  $node = Resolve-ASLNode -NodeOrAlias $NodeOrAlias -AliasPath $ASL_ALIAS_PATH
  return Safe-Disconnect-Node -NodeNumber $node
}

function Emergency-DisconnectAllASL {
  # Disconnect-all + verify (gives ASL a moment to update its node list)
  Disconnect-AllNodes | Out-Null
  Start-Sleep -Seconds 3
  $list = Get-ConnectedNodes
  return $list
}

function Show-ASLAliases {
  Get-ASLAliasList -AliasPath $ASL_ALIAS_PATH | Format-Table -AutoSize
}
