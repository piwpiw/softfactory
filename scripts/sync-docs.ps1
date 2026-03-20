param(
  [switch]$FailOnError = $true
)

$me = Split-Path -Leaf $MyInvocation.MyCommand.Path

function Run-Step {
  param(
    [string]$name,
    [string]$scriptPath,
    [string[]]$mustContain
  )

  Write-Output "[$me] Step: $name"
  $out = & (Resolve-Path $scriptPath) 2>&1
  $joined = ($out | Out-String)
  foreach ($line in $out) {
    Write-Output $line
  }

  foreach ($token in $mustContain) {
    if ($joined -notmatch [regex]::Escape($token)) {
      throw "$name failed: missing token '$token'"
    }
  }
}

try {
  Run-Step -name 'metadata check' -scriptPath 'd:\Project\scripts\check-doc-metadata.ps1' -mustContain @('DOC_METADATA_CHECK_PASS')
  Run-Step -name 'refresh index' -scriptPath 'd:\Project\scripts\refresh-doc-index.ps1' -mustContain @('refreshed:')
  Write-Output "[$me] DONE"
}
catch {
  Write-Output "[$me] ERROR: $($_.Exception.Message)"
  if ($FailOnError) { exit 1 }
}
