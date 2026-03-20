param()

$me = Split-Path -Leaf $MyInvocation.MyCommand.Path
$repoRoot = 'D:/Project'

function Read-McpProfile {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    throw "MCP profile missing: $Path"
  }

  try {
    $raw = Get-Content $Path -Raw
    $cfg = $raw | ConvertFrom-Json -ErrorAction Stop
  }
  catch {
    throw "MCP profile parse failed: $Path"
  }

  if (-not $cfg.PSObject.Properties.Name -contains 'mcpServers') {
    throw "Invalid MCP profile (missing mcpServers): $Path"
  }

  return $cfg.mcpServers.PSObject.Properties.Name
}

try {
  Write-Output "[$me] start"

  $coreProfile = Read-McpProfile "$repoRoot/.mcp.json"
  $coreMinimalProfile = Read-McpProfile "$repoRoot/.mcp.core.json"
  $optionalProfile = Read-McpProfile "$repoRoot/.mcp.optional.json"

  $coreRequired = @('filesystem', 'sqlite', 'fetch')
  foreach ($name in $coreRequired) {
    if ($coreProfile -notcontains $name) {
      throw "Core profile missing required server: $name"
    }
    if ($coreMinimalProfile -notcontains $name) {
      throw "Core minimal profile missing required server: $name"
    }
  }

  if ($coreProfile.Count -lt 1 -or $coreMinimalProfile.Count -lt 1 -or $optionalProfile.Count -lt 1) {
    throw "MCP profiles must define at least one server"
  }

  $allServers = @{}
  foreach ($item in $coreProfile) { $allServers[$item] = $true }
  foreach ($item in $coreMinimalProfile) { $allServers[$item] = $true }
  foreach ($item in $optionalProfile) { $allServers[$item] = $true }

  Write-Output "[$me] OK: .mcp.json servers: $($coreProfile -join ', ')"
  Write-Output "[$me] OK: .mcp.core.json servers: $($coreMinimalProfile -join ', ')"
  Write-Output "[$me] OK: .mcp.optional.json servers: $($optionalProfile -join ', ')"
  Write-Output "[$me] MCP servers in union: $($allServers.Keys -join ', ')"
  Write-Output "[$me] MCP consistency check passed"
}
catch {
  Write-Output "[$me] ERROR: $($_.Exception.Message)"
  exit 1
}
