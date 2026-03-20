param(
  [switch]$Check
)

$me = Split-Path -Leaf $MyInvocation.MyCommand.Path
$repoRoot = 'D:/Project'
$registry = "$repoRoot/orchestrator/mcp-registry.md"

function Ensure-File([string]$Path) {
  if (-not (Test-Path $Path)) {
    throw "required file missing: $Path"
  }
}

try {
  Write-Output "[$me] start"
  Ensure-File $registry
  Ensure-File "$repoRoot/.mcp.json"
  Ensure-File "$repoRoot/.mcp.core.json"
  Ensure-File "$repoRoot/.mcp.optional.json"

  if ($Check) {
    Write-Output "[$me] Check mode: validating MCP docs/profile references"

    $mcpText = Get-Content $registry -Raw
    if ($mcpText -notmatch 'mcp-01|filesystem|sqlite|fetch' -and $mcpText -notmatch 'filesystem') {
      throw "Registry missing baseline MCP rows"
    }
    Write-Output "[$me] MCP registry baseline check passed"
    Write-Output "[$me] MCP docs sync check passed"
    exit 0
  }

  & "$repoRoot/scripts/sync-docs.ps1"
}
catch {
  Write-Output "[$me] ERROR: $($_.Exception.Message)"
  exit 1
}
