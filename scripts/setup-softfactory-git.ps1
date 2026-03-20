param(
    [string]$Name = "In Wung, Park",
    [string]$Email = "piwpiw@naver.com",
    [string]$GitHubUsername = "piwpiw99"
)

Write-Host "[softfactory] Setting local git identity"
git config user.name $Name
git config user.email $Email

Write-Host "[softfactory] Enforcing deploy-safe local hooks"
New-Item -ItemType Directory -Path .githooks -Force | Out-Null
git config core.hooksPath .githooks

Write-Host "[softfactory] Forcing GitHub username for credential helper"
git config credential.https://github.com.username $GitHubUsername
git config --global credential.https://github.com.username $GitHubUsername
git config user.useConfigOnly true

Write-Host "[softfactory] Current git identity:"
git config user.name
git config user.email
git config credential.https://github.com.username
