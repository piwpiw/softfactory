param(
  [string]$Output = '',
  [string]$LegacyOutput = ''
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir '..')

if (-not $Output) {
  $Output = Join-Path $repoRoot 'docs\CATALOG.json'
}
if (-not $LegacyOutput) {
  $LegacyOutput = Join-Path $repoRoot 'docs\doc-index.json'
}

$generator = Join-Path $scriptDir 'generate_docs_catalog.py'

python $generator --root $repoRoot --output $Output --legacy-output $LegacyOutput
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
