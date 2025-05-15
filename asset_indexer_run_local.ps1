<#
.SYNOPSIS
    Run the asset_indexer Cloud Function locally with Google Functions Framework.
    • Loads environment variables from .env.example
    • Listens on http://localhost:8081
    • Optional VS Code debugging on port 5678 when DEBUG=1

.DESCRIPTION
    1. Reads each KEY=VALUE line in .env.example and exports it.
    2. If $Env:DEBUG is set, starts debugpy so VS Code can attach.
    3. Launches Functions Framework, pointing at src/asset_indexer.
    No virtual-env or Cloud Code extension required.
#>

#───────────────── 1  Load environment variables ─────────────────
Write-Host "`n🔧 Loading variables from .env.example …" -ForegroundColor Cyan

# Set emulator environment variables
$env:FIRESTORE_EMULATOR_HOST = "127.0.0.1:8090"
$env:FIREBASE_STORAGE_EMULATOR_HOST = "127.0.0.1:9199"
$env:FUNCTIONS_EMULATOR = "true"

$envFile = ".env.example"
if (-not (Test-Path $envFile)) {
    Write-Error "❌  $envFile not found in $(Get-Location)"
    exit 1
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]+)\s*=\s*(.+?)\s*$') {
        $varName = $matches[1]
        $varValue = $matches[2].Trim()
        Set-Item -Path "env:$varName" -Value $varValue
    }
}

#───────────────── 2  Choose launcher (with / without debugpy) ─────
$port      = 8081          # HTTP port for Functions Framework
$debugPort = 5678          # VS Code attach port

if ($Env:DEBUG) {
    Write-Host "🐞 Waiting for VS Code debugger on localhost:$debugPort …" `
               -ForegroundColor Yellow
    $launcher = "python -m debugpy --listen $debugPort --wait-for-client -m"
} else {
    $launcher = "python -m"
}

#───────────────── 3  Run Functions Framework ─────────────────────
Write-Host "🌐 Starting asset_indexer on http://localhost:$port …`n" `
           -ForegroundColor Green

$cmd = "$launcher functions_framework --target asset_indexer --source src/asset_indexer/main.py --signature-type cloudevent --port $port"

Invoke-Expression $cmd
