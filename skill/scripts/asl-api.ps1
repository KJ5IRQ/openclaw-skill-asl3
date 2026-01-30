# ASL Agent API Helper Script
# Provides functions for interacting with the ASL Agent REST API

$ASL_API_BASE = "http://YOUR_PI_IP_ADDRESS:8073"
$ASL_API_KEY = "YOUR_API_KEY_HERE"

function Invoke-ASLApi {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [hashtable]$Body = $null
    )
    
    $headers = @{
        "X-API-Key" = $ASL_API_KEY
        "Content-Type" = "application/json"
    }
    
    $params = @{
        Uri = "$ASL_API_BASE$Endpoint"
        Method = $Method
        Headers = $headers
    }
    
    if ($Body) {
        $params.Body = ($Body | ConvertTo-Json)
    }
    
    try {
        $response = Invoke-RestMethod @params
        return $response
    } catch {
        Write-Error "API Error: $($_.Exception.Message)"
        return $null
    }
}

function Get-NodeStatus {
    <#
    .SYNOPSIS
        Get current node status and statistics
    .EXAMPLE
        Get-NodeStatus
    #>
    $status = Invoke-ASLApi -Endpoint "/status"
    if ($status) {
        return @"
🔘 **Node $($status.node) ($($status.callsign)) Status**

⏱️ Uptime: $($status.uptime)
🔢 Keyups Today: $($status.keyups_today)
🔗 Connected Nodes: $($status.connected_nodes)
"@
    }
    return "❌ Failed to get node status"
}

function Get-ConnectedNodes {
    <#
    .SYNOPSIS
        Get list of currently connected nodes
    .PARAMETER Raw
        Return raw API response instead of formatted output
    .EXAMPLE
        Get-ConnectedNodes
    #>
    param(
        [switch]$Raw
    )

    $result = Invoke-ASLApi -Endpoint "/nodes"
    if (-not $result) {
        return $(if ($Raw) { $null } else { "❌ Failed to get connected nodes" })
    }

    if ($Raw) { return $result }

    if ($result.count -eq 0) {
        return "📡 No nodes currently connected"
    }

    $output = "📡 **Connected Nodes ($($result.count))**`n`n"
    foreach ($node in $result.connected_nodes) {
        $info = if ($null -ne $node.info -and $node.info.ToString().Trim().Length -gt 0) { $node.info } else { "" }
        $output += "• Node $($node.node): $info`n"
    }
    return $output
}

function Get-ConnectedNodeNumbers {
    <#
    .SYNOPSIS
        Get array of currently connected node numbers
    .EXAMPLE
        $nodes = Get-ConnectedNodeNumbers
    #>
    $raw = Get-ConnectedNodes -Raw
    if (-not $raw) { return @() }
    if ($raw.count -eq 0) { return @() }

    $nodes = @()
    foreach ($n in $raw.connected_nodes) {
        if ($null -ne $n.node) { $nodes += [string]$n.node }
    }
    return $nodes
}

function Connect-Node {
    <#
    .SYNOPSIS
        Connect to another AllStar node
    .PARAMETER NodeNumber
        Node number to connect to
    .PARAMETER MonitorOnly
        Connect in monitor (receive only) mode
    .EXAMPLE
        Connect-Node -NodeNumber 55553
    .EXAMPLE
        Connect-Node -NodeNumber 55553 -MonitorOnly
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$NodeNumber,
        [switch]$MonitorOnly
    )
    
    $body = @{
        node = $NodeNumber
        monitor_only = $MonitorOnly.IsPresent
    }
    
    $result = Invoke-ASLApi -Endpoint "/connect" -Method "POST" -Body $body
    if ($result -and $result.success) {
        $mode = if ($MonitorOnly) { "monitor (RX only)" } else { "transceive (TX/RX)" }
        return "✅ Connected to node $NodeNumber in $mode mode"
    }
    return "❌ Failed to connect to node $NodeNumber"
}

function Disconnect-Node {
    <#
    .SYNOPSIS
        Disconnect from a specific node
    .PARAMETER NodeNumber
        Node number to disconnect from
    .EXAMPLE
        Disconnect-Node -NodeNumber 55553
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$NodeNumber
    )
    
    $body = @{ node = $NodeNumber }
    $result = Invoke-ASLApi -Endpoint "/disconnect" -Method "POST" -Body $body
    
    if ($result -and $result.success) {
        return "✅ Disconnected from node $NodeNumber"
    }
    return "❌ Failed to disconnect from node $NodeNumber"
}

function Disconnect-AllNodes {
    <#
    .SYNOPSIS
        Disconnect from all currently connected nodes
    .EXAMPLE
        Disconnect-AllNodes
    #>
    $result = Invoke-ASLApi -Endpoint "/disconnect-all" -Method "POST"
    if ($result -and $result.success) {
        return "✅ Disconnected from all nodes"
    }
    return "❌ Failed to disconnect from all nodes"
}

function Get-AuditLog {
    <#
    .SYNOPSIS
        Get recent command audit log entries
    .PARAMETER Lines
        Number of recent entries to retrieve (default: 20)
    .EXAMPLE
        Get-AuditLog
    .EXAMPLE
        Get-AuditLog -Lines 50
    #>
    param(
        [int]$Lines = 20
    )
    
    $result = Invoke-ASLApi -Endpoint "/audit?lines=$Lines"
    if ($result) {
        if ($result.count -eq 0) {
            return "📋 No audit log entries"
        }
        
        $output = "📋 **Recent Commands ($($result.count))**`n`n"
        foreach ($entry in $result.entries) {
            $output += "$entry`n"
        }
        return $output
    }
    return "❌ Failed to get audit log"
}
