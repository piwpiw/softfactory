param(
  [string[]]$RequiredFiles = @(
    'README.md',
    'docs/INDEX.md',
    'web/bohemian-marketing/parallel-implementation-plan.md'
  )
)
$errors = @()
foreach ($f in $RequiredFiles) {
  if (-not (Test-Path $f)) { $errors += "missing:$f"; continue }
  $c = Get-Content $f -Raw
  if ($c -notmatch 'doc-metadata|documentation-maintenance-template|Keywords:') { $errors += "missing-metadata:$f" }
  if ($c -notmatch '변경|수정|요청|rollback|rollback_plan|근거|verification|검증') { $errors += "missing-maintenance-fields:$f" }
}
if ($errors.Count -gt 0) {
  Write-Output 'DOC_METADATA_CHECK_FAIL'
  $errors | ForEach-Object { Write-Output $_ }
  exit 1
}
Write-Output 'DOC_METADATA_CHECK_PASS'
