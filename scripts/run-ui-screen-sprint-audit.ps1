param(
    [string]$BaseUrl = "https://softfactory-platform.vercel.app",
    [string]$Passkey = "demo2026",
    [switch]$Headed,
    [int]$TimeoutMs = 20000
)

$headless = "true"
if ($Headed.IsPresent) {
    $headless = "false"
}

python scripts/ui-screen-sprint-audit.py --base $BaseUrl --passkey $Passkey --headless $headless --timeout $TimeoutMs
