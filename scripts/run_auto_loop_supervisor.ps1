$ErrorActionPreference = 'Stop'

$root = 'D:\Project'
$hours = [int]$env:SOFTFACTORY_LOOP_HOURS
if (-not $hours -or $hours -le 0) { $hours = 5 }
$interval = if ($env:SOFTFACTORY_LOOP_INTERVAL_SECONDS) { [int]$env:SOFTFACTORY_LOOP_INTERVAL_SECONDS } else { 300 }
$workers = if ($env:SOFTFACTORY_LOOP_MAX_WORKERS) { [int]$env:SOFTFACTORY_LOOP_MAX_WORKERS } else { 12 }

$start = Get-Date
$end = $start.AddHours($hours)
$log = Join-Path $root 'tmp_logs/loop_supervisor.log'
$scriptPath = Join-Path $root 'scripts/agent_3h_loop.py'
$pythonCmd = (Get-Command python).Source

function Write-SuperLog {
    param([string]$Message)
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Add-Content -Path $log -Value "[$ts] $Message"
}

New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

Write-SuperLog "SUPERVISOR_START hours=$hours interval=$interval workers=$workers"

while ((Get-Date) -lt $end) {
    $alive = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like "*scripts/agent_3h_loop.py*" }

    if (-not $alive) {
        Write-SuperLog "AUTORESTART_TRIGGER no-loop-process -> starting"
        $env:SOFTFACTORY_LOOP_HOURS = [string]$hours
        $env:SOFTFACTORY_LOOP_INTERVAL_SECONDS = [string]$interval
        $env:SOFTFACTORY_LOOP_MAX_WORKERS = [string]$workers

        Start-Process -FilePath $pythonCmd `
            -ArgumentList $scriptPath `
            -WorkingDirectory $root `
            -RedirectStandardOutput (Join-Path $root 'tmp_logs/agent_5h_loop_stdout.log') `
            -RedirectStandardError (Join-Path $root 'tmp_logs/agent_5h_loop_stderr.log') `
            -WindowStyle Hidden | Out-Null

        Start-Sleep -Seconds 3
        $started = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -like "*scripts/agent_3h_loop.py*" }
        Write-SuperLog ("AUTORESTART: started=$($started.ProcessId -ne $null)")
    }

    Start-Sleep -Seconds 20
}

Write-SuperLog 'SUPERVISOR_END'
