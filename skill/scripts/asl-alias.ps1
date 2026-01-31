$ErrorActionPreference = 'Stop'

function Normalize-ASLAliasKey {
  param([Parameter(Mandatory=$true)][string]$Text)

  # speech-friendly normalization:
  # - lowercase
  # - remove punctuation (keep letters/digits/spaces)
  # - collapse whitespace
  $t = $Text.ToLowerInvariant()
  $t = [regex]::Replace($t, '[^a-z0-9\s]+', ' ')
  $t = [regex]::Replace($t, '\s+', ' ').Trim()
  return $t
}

function Get-ASLAliasMap {
  param(
    [string]$Path = (Join-Path $PWD 'asl-node-aliases.json')
  )

  if (-not (Test-Path $Path)) {
    throw "Alias file not found: $Path"
  }

  $raw = Get-Content -Raw -Path $Path | ConvertFrom-Json
  $map = @{}

  foreach ($p in $raw.PSObject.Properties) {
    $k = Normalize-ASLAliasKey $p.Name
    $v = [string]$p.Value
    if ([string]::IsNullOrWhiteSpace($k)) { continue }

    if ($map.ContainsKey($k) -and $map[$k] -ne $v) {
      throw "Alias conflict: '$k' maps to both '$($map[$k])' and '$v'"
    }

    $map[$k] = $v

    # Also support a no-space variant automatically (drop in -> dropin)
    $k2 = $k -replace ' ', ''
    if (-not [string]::IsNullOrWhiteSpace($k2)) {
      if ($map.ContainsKey($k2) -and $map[$k2] -ne $v) {
        throw "Alias conflict: '$k2' maps to both '$($map[$k2])' and '$v'"
      }
      $map[$k2] = $v
    }
  }

  return $map
}

function Resolve-ASLNode {
  <#
    Resolves either a raw node number (e.g. 55553) OR a speech-friendly alias (e.g. "parrot node").
    Returns a string node number.

    NOTE: Callsigns like "KF8DRJ" contain digits. So we ALWAYS try alias lookup first,
    and only fall back to number-extraction when the text explicitly looks like a node reference.
  #>
  param(
    [Parameter(Mandatory=$true)][string]$NodeOrAlias,
    [string]$AliasPath = (Join-Path $PWD 'asl-node-aliases.json')
  )

  $input = $NodeOrAlias.Trim()

  # If it's already just digits, treat as node
  if ($input -match '^\d+$') { return $input }

  $map = Get-ASLAliasMap -Path $AliasPath

  $key = Normalize-ASLAliasKey $input
  if ($map.ContainsKey($key)) { return $map[$key] }

  $key2 = $key -replace ' ', ''
  if ($map.ContainsKey($key2)) { return $map[$key2] }

  # Fallback: extract digits only when it *looks like* the user meant a node number.
  # Examples: "node 55553", "asl 55553", "allstar 55553"
  if ($key -match '(^|\b)(node|asl|allstar|all\s*star)\b') {
    $m = [regex]::Matches($input, '\d+')
    if ($m.Count -gt 0) {
      return $m[$m.Count - 1].Value
    }
  }

  throw "Unknown ASL node alias: '$NodeOrAlias' (normalized: '$key'). Add it to $AliasPath"
}

function Get-ASLAliasList {
  param([string]$AliasPath = (Join-Path $PWD 'asl-node-aliases.json'))

  $map = Get-ASLAliasMap -Path $AliasPath
  $map.GetEnumerator() | Sort-Object Name | ForEach-Object {
    [PSCustomObject]@{ alias = $_.Key; node = $_.Value }
  }
}
