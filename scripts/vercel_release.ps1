param(
    [int]$LocalPort = 4173,
    [switch]$Deploy,
    [switch]$ForceDeploy
)

$ErrorActionPreference = "Stop"

function Test-Url {
    param(
        [string]$Url,
        [int]$TimeoutSec = 20
    )

    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec $TimeoutSec
        return [pscustomobject]@{ Url = $Url; Status = $resp.StatusCode; Ok = $true }
    }
    catch {
        if ($_.Exception.Response -ne $null) {
            return [pscustomobject]@{
                Url = $Url
                Status = [int]$_.Exception.Response.StatusCode
                Ok = $false
            }
        }
        return [pscustomobject]@{ Url = $Url; Status = 0; Ok = $false }
    }
}

function Assert-AllOk {
    param(
        [array]$Results,
        [string]$Phase
    )

    $failed = $Results | Where-Object { -not $_.Ok }
    if ($failed.Count -gt 0) {
        $failed | ForEach-Object { Write-Host "[$Phase][FAIL] $($_.Url) -> $($_.Status)" -ForegroundColor Red }
        throw "$Phase check failed"
    }

    $Results | ForEach-Object { Write-Host "[$Phase][OK] $($_.Url) -> $($_.Status)" -ForegroundColor Green }
}

function Wait-AllOk {
    param(
        [string[]]$Urls,
        [string]$Phase,
        [int]$Attempts = 18,
        [int]$DelaySeconds = 10,
        [int]$TimeoutSec = 20
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        $results = $Urls | ForEach-Object { Test-Url -Url $_ -TimeoutSec $TimeoutSec }
        $failed = $results | Where-Object { -not $_.Ok }
        if ($failed.Count -eq 0) {
            Assert-AllOk -Results $results -Phase $Phase
            return
        }

        $failedSummary = ($failed | ForEach-Object { "$($_.Status):$($_.Url)" }) -join ", "
        Write-Host "[$Phase][WAIT] attempt $attempt/$Attempts -> $failedSummary" -ForegroundColor Yellow
        if ($attempt -lt $Attempts) {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    $finalResults = $Urls | ForEach-Object { Test-Url -Url $_ -TimeoutSec $TimeoutSec }
    Assert-AllOk -Results $finalResults -Phase $Phase
}

function Get-RelativePathCompat {
    param(
        [string]$BasePath,
        [string]$TargetPath
    )

    $base = (Resolve-Path $BasePath).Path.TrimEnd('\', '/')
    $target = (Resolve-Path $TargetPath).Path
    if ($target.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $target.Substring($base.Length).TrimStart('\', '/')
    }

    return $target
}

function Get-FrontendFingerprint {
    param(
        [string]$ProjectRoot,
        [string]$WebDir
    )

    $metaLines = New-Object System.Collections.Generic.List[string]

    if (Test-Path $WebDir) {
        Get-ChildItem $WebDir -Recurse -File |
            Sort-Object FullName |
            ForEach-Object {
                $rel = Get-RelativePathCompat -BasePath $ProjectRoot -TargetPath $_.FullName
                $metaLines.Add("$rel|$($_.Length)|$($_.LastWriteTimeUtc.Ticks)")
            }
    }

    $backendDir = Join-Path $ProjectRoot "backend"
    if (Test-Path $backendDir) {
        Get-ChildItem $backendDir -Recurse -File |
            Sort-Object FullName |
            ForEach-Object {
                $rel = Get-RelativePathCompat -BasePath $ProjectRoot -TargetPath $_.FullName
                $metaLines.Add("$rel|$($_.Length)|$($_.LastWriteTimeUtc.Ticks)")
            }
    }

    $trackedFiles = @(
        "vercel.json",
        "api\proxy.js",
        "api\_health.js",
        "api\runtime.py",
        "api\ping.py",
        "requirements.txt",
        "pyproject.toml"
    )
    foreach ($relativePath in $trackedFiles) {
        $absolutePath = Join-Path $ProjectRoot $relativePath
        if (Test-Path $absolutePath) {
            $file = Get-Item $absolutePath
            $rel = Get-RelativePathCompat -BasePath $ProjectRoot -TargetPath $file.FullName
            $metaLines.Add("$rel|$($file.Length)|$($file.LastWriteTimeUtc.Ticks)")
        }
    }

    $raw = [string]::Join("`n", $metaLines.ToArray())
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha.ComputeHash($bytes)
    return ([BitConverter]::ToString($hashBytes)).Replace("-", "").ToLowerInvariant()
}

function Test-VercelAuth {
    $whoamiOutput = (& npx vercel whoami 2>&1) | Out-String
    if ($LASTEXITCODE -ne 0) {
        $trimmed = $whoamiOutput.Trim()
        if ($trimmed -match "token is not valid|No existing credentials found|Please login|not logged in") {
            throw "Vercel authentication is invalid. Run 'npx vercel login' or set a valid VERCEL_TOKEN before production deploy."
        }
        throw "Vercel auth preflight failed: $trimmed"
    }

    Write-Host "[VERCEL] authenticated as $($whoamiOutput.Trim())" -ForegroundColor Green
}

function Assert-VercelApiUpstreamHealthy {
    param(
        [string]$ProjectRoot
    )

    $vercelConfig = Join-Path $ProjectRoot "vercel.json"
    $runtimeEntrypoint = Join-Path $ProjectRoot "api\runtime.py"
    if ((Test-Path $vercelConfig) -and (Test-Path $runtimeEntrypoint)) {
        $configText = Get-Content $vercelConfig -Raw
        if ($configText -match '/api/runtime\?path=:path\*') {
            Write-Host "[UPSTREAM] skipped: Vercel runtime API mode is active." -ForegroundColor Yellow
            return
        }
    }

    $tmpEnv = Join-Path $ProjectRoot ".workspace\tmp.vercel.production.env"
    if (Test-Path $tmpEnv) {
        Remove-Item $tmpEnv -Force
    }

    & npx vercel env pull $tmpEnv --environment=production | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tmpEnv)) {
        throw "Unable to pull Vercel production environment variables."
    }

    $upstreamLine = Get-Content $tmpEnv | Where-Object { $_ -match '^API_UPSTREAM_URL=' -or $_ -match '^VERCEL_API_UPSTREAM_URL=' } | Select-Object -First 1
    if (-not $upstreamLine) {
        throw "API_UPSTREAM_URL or VERCEL_API_UPSTREAM_URL is not configured in Vercel production."
    }

    $upstreamUrl = ($upstreamLine -split '=', 2)[1].Trim().Trim('"')
    $upstreamUrl = $upstreamUrl -replace '\\r\\n', ''
    $upstreamUrl = $upstreamUrl.Trim()
    if (-not $upstreamUrl) {
        throw "Production API upstream is empty."
    }

    if ($upstreamUrl -match 'localhost|127\.0\.0\.1|loca\.lt|localtunnel') {
        throw "Production API upstream is invalid for public use: $upstreamUrl"
    }

    $healthCandidates = @(
        ($upstreamUrl.TrimEnd('/') + '/health'),
        ($upstreamUrl.TrimEnd('/') + '/api/health')
    )

    $healthy = $false
    foreach ($candidate in $healthCandidates) {
        $result = Test-Url -Url $candidate -TimeoutSec 20
        if ($result.Ok) {
            Write-Host "[UPSTREAM][OK] $candidate -> $($result.Status)" -ForegroundColor Green
            $healthy = $true
            break
        }
        Write-Host "[UPSTREAM][WAIT] $candidate -> $($result.Status)" -ForegroundColor Yellow
    }

    if (-not $healthy) {
        throw "Production API upstream is configured but not healthy: $upstreamUrl"
    }
}

function New-VercelStage {
    param(
        [string]$ProjectRoot,
        [string]$StageDir
    )

    if (Test-Path $StageDir) {
        Remove-Item $StageDir -Recurse -Force
    }

    New-Item -Path $StageDir -ItemType Directory | Out-Null
    New-Item -Path (Join-Path $StageDir "api") -ItemType Directory | Out-Null
    New-Item -Path (Join-Path $StageDir "backend") -ItemType Directory | Out-Null
    New-Item -Path (Join-Path $StageDir "web") -ItemType Directory | Out-Null
    New-Item -Path (Join-Path $StageDir ".vercel") -ItemType Directory | Out-Null

    Copy-Item (Join-Path $ProjectRoot "vercel.json") (Join-Path $StageDir "vercel.json") -Force
    Copy-Item (Join-Path $ProjectRoot "api\proxy.js") (Join-Path $StageDir "api\proxy.js") -Force
    Copy-Item (Join-Path $ProjectRoot "api\_health.js") (Join-Path $StageDir "api\_health.js") -Force
    Copy-Item (Join-Path $ProjectRoot "api\runtime.py") (Join-Path $StageDir "api\runtime.py") -Force
    Copy-Item (Join-Path $ProjectRoot "api\ping.py") (Join-Path $StageDir "api\ping.py") -Force
    Copy-Item (Join-Path $ProjectRoot "requirements.txt") (Join-Path $StageDir "requirements.txt") -Force
    Copy-Item (Join-Path $ProjectRoot "pyproject.toml") (Join-Path $StageDir "pyproject.toml") -Force
    Copy-Item (Join-Path $ProjectRoot ".vercel\project.json") (Join-Path $StageDir ".vercel\project.json") -Force
    Copy-Item (Join-Path $ProjectRoot "backend\*") (Join-Path $StageDir "backend") -Recurse -Force
    Copy-Item (Join-Path $ProjectRoot "web\*") (Join-Path $StageDir "web") -Recurse -Force
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$webDir = Join-Path $projectRoot "web"
$stateDir = Join-Path $projectRoot ".deploy"
$fingerprintFile = Join-Path $stateDir "vercel_frontend.sha256"
$vercelStageDir = Join-Path $stateDir "vercel-stage"

$requiredPaths = @(
    ".vercel\project.json",
    "vercel.json",
    "api\proxy.js",
    "api\_health.js",
    "api\runtime.py",
    "api\ping.py",
    "backend",
    "requirements.txt",
    "pyproject.toml",
    "web"
)

foreach ($relativePath in $requiredPaths) {
    $absolutePath = Join-Path $projectRoot $relativePath
    if (-not (Test-Path $absolutePath)) {
        throw "$relativePath not found."
    }
}

$listening = Get-NetTCPConnection -LocalPort $LocalPort -State Listen -ErrorAction SilentlyContinue
if ($listening) {
    throw "Local port $LocalPort is already in use. Use -LocalPort with a free port."
}

$httpProc = $null
try {
    Write-Host "[LOCAL] start static server on port $LocalPort" -ForegroundColor Cyan
    $httpProc = Start-Process python -ArgumentList "-m","http.server","$LocalPort","--directory",$webDir -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2

    $localUrls = @(
        "http://127.0.0.1:$LocalPort/index.html",
        "http://127.0.0.1:$LocalPort/bohemian-marketing/index.html",
        "http://127.0.0.1:$LocalPort/platform/index.html",
        "http://127.0.0.1:$LocalPort/analytics/dashboard.html"
    )
    $localResults = $localUrls | ForEach-Object { Test-Url -Url $_ -TimeoutSec 12 }
    Assert-AllOk -Results $localResults -Phase "LOCAL"
}
finally {
    if ($httpProc -and -not $httpProc.HasExited) {
        Stop-Process -Id $httpProc.Id -Force -ErrorAction SilentlyContinue
    }
}

if (-not $Deploy) {
    Write-Host "[DEPLOY] skipped (default mode). Use -Deploy to run production deploy." -ForegroundColor Yellow
    exit 0
}

Test-VercelAuth
Assert-VercelApiUpstreamHealthy -ProjectRoot $projectRoot

$currentFingerprint = Get-FrontendFingerprint -ProjectRoot $projectRoot -WebDir $webDir

if (-not $ForceDeploy -and (Test-Path $fingerprintFile)) {
    $previousFingerprint = (Get-Content $fingerprintFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if ($previousFingerprint -and $previousFingerprint -eq $currentFingerprint) {
        Write-Host "[DEPLOY] skipped (no frontend/api/vercel.json changes since last successful deploy)." -ForegroundColor Yellow
        Write-Host "[DEPLOY] use -ForceDeploy to override." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "[DEPLOY] prepare minimal Vercel stage" -ForegroundColor Cyan
New-VercelStage -ProjectRoot $projectRoot -StageDir $vercelStageDir

if (-not $env:API_UPSTREAM_URL -and -not $env:VERCEL_API_UPSTREAM_URL) {
    Write-Host "[DEPLOY][WARN] API_UPSTREAM_URL / VERCEL_API_UPSTREAM_URL not set in local shell. Ensure the Vercel project has one of them configured." -ForegroundColor Yellow
}

Write-Host "[DEPLOY] run vercel production deployment" -ForegroundColor Cyan
$deployOutput = $null
Push-Location $vercelStageDir
try {
    $deployOutputRaw = cmd /c "npx vercel --prod --yes --archive=tgz --logs 2>&1"
    if ($deployOutputRaw -is [string]) {
        $deployOutput = $deployOutputRaw -split "`r?`n"
    } elseif ($deployOutputRaw -is [System.Array]) {
        $deployOutput = $deployOutputRaw
    } else {
        $deployOutput = @($deployOutputRaw)
    }
}
finally {
    Pop-Location
}

$deployOutput = @($deployOutput | ForEach-Object { ($_ -replace "`r", "").Trim() } | Where-Object { $_ })

$deployOutput | ForEach-Object { Write-Host $_ }

$prodUrl = $null
$prodUrl = ($deployOutput | ForEach-Object {
    if ($_ -match 'Production:\s*(https://[^\s\[]+)') {
        $matches[1]
    }
} | Select-Object -Last 1)

if (-not $prodUrl) {
    throw "Could not parse production URL from Vercel output."
}

$deployUrl = $prodUrl.Trim()
Write-Host "[DEPLOY] production url: $deployUrl" -ForegroundColor Green

$remoteUrls = @(
    "https://softfactory-platform.vercel.app/",
    "https://softfactory-platform.vercel.app/bohemian-marketing/index.html",
    "https://softfactory-platform.vercel.app/platform/index.html",
    "https://softfactory-platform.vercel.app/analytics/dashboard.html",
    "$deployUrl/",
    "$deployUrl/bohemian-marketing/index.html"
)
Wait-AllOk -Urls $remoteUrls -Phase "REMOTE"

if (-not (Test-Path $stateDir)) {
    New-Item -Path $stateDir -ItemType Directory | Out-Null
}
$currentFingerprint | Set-Content -Encoding ascii $fingerprintFile

Write-Host "[DONE] local check + production deploy + external verify complete" -ForegroundColor Green
