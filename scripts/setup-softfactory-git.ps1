param(
    [string]$Name = "In Wung, Park",
    [string]$Email = "piwpiw@naver.com"
)

Write-Host "[softfactory] Setting local git identity"
git config user.name $Name
git config user.email $Email

Write-Host "[softfactory] Enforcing deploy-safe local hooks"
New-Item -ItemType Directory -Path .githooks -Force | Out-Null
git config core.hooksPath .githooks

Write-Host "[softfactory] Current git identity:"
git config user.name
git config user.email
