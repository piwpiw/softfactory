param(
    [string]$BaseUrl = "http://127.0.0.1:9000",
    [string]$Port = "9000",
    [switch]$NoServer,
    [switch]$Headless,
    [switch]$KeepAlive
)

$projectRoot = "d:\\Project"
$dbPath = Join-Path $projectRoot "platform.db"

function Test-LocalServer {
    param([string]$Url)

    foreach ($path in @("/health", "/api/health")) {
        try {
            $resp = Invoke-WebRequest -Uri ($Url.TrimEnd("/") + $path) -TimeoutSec 5
            if ($resp.StatusCode -eq 200) {
                return $true
            }
        } catch {
        }
    }

    return $false
}

if (-not $NoServer) {
    if (-not (Test-LocalServer -Url $BaseUrl)) {
        Write-Output "[$(Get-Date -Format 'HH:mm:ss')] local server not running. starting start_platform.py in development mode."
        $safeDbPath = $dbPath.Replace("\", "/")
        $cmd = "cd /d $projectRoot && set `"ENVIRONMENT=development`" && set `"FLASK_ENV=development`" && set `"DATABASE_URL=sqlite:///$safeDbPath`" && start /B python start_platform.py"
        cmd /c $cmd | Out-Null

        $tries = 0
        while ($tries -lt 60) {
            Start-Sleep -Seconds 1
            if (Test-LocalServer -Url $BaseUrl) {
                Write-Output "[$(Get-Date -Format 'HH:mm:ss')] local server started."
                break
            }
            $tries++
        }

        if (-not (Test-LocalServer -Url $BaseUrl)) {
            Write-Error "Local server failed to start. Check logs before retrying."
            exit 1
        }
    } else {
        Write-Output "[$(Get-Date -Format 'HH:mm:ss')] local server already running."
    }
}

Write-Output "[$(Get-Date -Format 'HH:mm:ss')] starting UI window smoke test"
if ($Headless) {
    python scripts/ui-window-smoke-test.py --base $BaseUrl --headless true --timeout 15000 --pause 1
} else {
    python scripts/ui-window-smoke-test.py --base $BaseUrl --headless false --timeout 15000 --pause 1
}

if ($KeepAlive) {
    Write-Output "KeepAlive enabled: server will continue running."
} else {
    Write-Output "Test run finished. Server state was left unchanged."
}
