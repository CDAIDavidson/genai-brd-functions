<#
.SYNOPSIS
    Run all BRD processing Cloud Functions locally with Google Functions Framework.
    • Loads environment variables from .env
    • Runs each function on a different port
    • Optional VS Code debugging when DEBUG=1

.DESCRIPTION
    1. Reads each KEY=VALUE line in .env and exports it.
    2. If $Env:DEBUG is set, starts debugpy so VS Code can attach.
    3. Launches Functions Framework for each function on a different port.
    No virtual-env or Cloud Code extension required.
#>

#───────────────── 1. Load environment variables ─────────────────
Write-Host "`n🔧 Loading variables from .env …" -ForegroundColor Cyan

# Set emulator environment variables
$env:FIRESTORE_EMULATOR_HOST = "127.0.0.1:8090"
$env:FIREBASE_STORAGE_EMULATOR_HOST = "127.0.0.1:9199"
$env:FUNCTIONS_EMULATOR = "true"

$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "❓ .env not found, creating from env.yaml..." -ForegroundColor Yellow
    # Create .env from env.yaml if it doesn't exist
    $yamlContent = Get-Content "env.yaml" -ErrorAction SilentlyContinue
    if ($yamlContent) {
        $yamlContent | ForEach-Object {
            if ($_ -match '([A-Z_][A-Z0-9_]+):\s*(.+?)$') {
                "$($matches[1])=$($matches[2])" | Out-File -FilePath $envFile -Append
            }
        }
        Write-Host "✅ Created .env from env.yaml" -ForegroundColor Green
        # Add emulator settings to .env
        "FIRESTORE_EMULATOR_HOST=127.0.0.1:8090" | Out-File -FilePath $envFile -Append
        "FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199" | Out-File -FilePath $envFile -Append
        "FUNCTIONS_EMULATOR=true" | Out-File -FilePath $envFile -Append
    } else {
        Write-Error "❌ Neither .env nor env.yaml found in $(Get-Location)"
        exit 1
    }
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]+)\s*=\s*(.+?)\s*$') {
        $varName = $matches[1]
        $varValue = $matches[2].Trim()
        Set-Item -Path "env:$varName" -Value $varValue
    }
}

#───────────────── 2. Function configuration ─────────────────────
$functions = @(
    @{
        Name = "asset_indexer"
        Port = 8081
        Path = "src/asset_indexer/main.py"
        DebugPort = 5678
    },
    @{
        Name = "document_analyzer"
        Port = 8082
        Path = "src/document_analyzer/main.py"
        DebugPort = 5679
    },
    @{
        Name = "content_processor"
        Port = 8083
        Path = "src/content_processor/main.py"
        DebugPort = 5680
    },
    @{
        Name = "requirement_extractor"
        Port = 8084
        Path = "src/requirement_extractor/main.py"
        DebugPort = 5681
    },
    @{
        Name = "summary_generator"
        Port = 8085
        Path = "src/summary_generator/main.py"
        DebugPort = 5682
    }
)

#───────────────── 3. Start all functions in background jobs ─────
$jobs = @()

foreach ($function in $functions) {
    $functionName = $function.Name
    $port = $function.Port
    $sourcePath = $function.Path
    $debugPort = $function.DebugPort
    
    Write-Host "`n🌐 Starting $functionName on http://localhost:$port …" -ForegroundColor Green
    
    # Choose launcher (with/without debugpy)
    if ($Env:DEBUG) {
        Write-Host "🐞 Debug port for ${functionName}: localhost:${debugPort} …" -ForegroundColor Yellow
        $launcher = "python -m debugpy --listen $debugPort --wait-for-client -m"
    } else {
        $launcher = "python -m"
    }
    
    # Build the command
    $cmd = "$launcher functions_framework --target $functionName --source $sourcePath --signature-type cloudevent --port $port"
    
    # Start function in a new window
    $escaped = $cmd -replace '"', '\"'
    $windowTitle = "BRD Function: $functionName"
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host `"$windowTitle on port $port`" -ForegroundColor Cyan; $escaped"
    
    Write-Host "✅ Started $functionName on port $port" -ForegroundColor Green
}

Write-Host "`n🚀 All functions are now running locally:" -ForegroundColor Cyan
foreach ($function in $functions) {
    Write-Host "   • $($function.Name): http://localhost:$($function.Port)" -ForegroundColor White
}

Write-Host "`n📋 Testing workflow:" -ForegroundColor Yellow
Write-Host "1. Upload a file to trigger asset_indexer" -ForegroundColor White
Write-Host "2. asset_indexer will publish to document-indexer topic" -ForegroundColor White
Write-Host "3. document_analyzer will process and publish to brd-analysis topic" -ForegroundColor White
Write-Host "4. content_processor will process and publish to brd-content topic" -ForegroundColor White
Write-Host "5. requirement_extractor will process and publish to brd-requirements topic" -ForegroundColor White
Write-Host "6. summary_generator will process and publish to brd-summary topic" -ForegroundColor White

Write-Host "`n⚠️ Press Ctrl+C in each window to stop the functions when done" -ForegroundColor Yellow 