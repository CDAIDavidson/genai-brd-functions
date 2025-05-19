# start_local_workflow.ps1
#
# This script starts all the components needed for local development and testing
# of the complete BRD processing workflow:
#
# 1. Start a listener that connects Pub/Sub to the content_processor function
# 2. Provide instructions for testing the workflow end-to-end

Write-Host "🚀 Starting complete BRD workflow test environment..."
Write-Host ""

# Check if Python is available
try {
    python --version | Out-Null
} catch {
    Write-Host "❌ Error: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python and make sure it's in your PATH"
    exit 1
}

# Check if dotenv file exists
if (!(Test-Path .\.env)) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "Please create a .env file with the required environment variables"
    exit 1
}

# Display current configuration
Write-Host "📋 Current workflow configuration:"
$topic_sub = (Get-Content .\.env | Where-Object { $_ -match "TOPIC_BRD_READY_TO_PARSE" -and $_ -notmatch "^#" }) -replace "TOPIC_BRD_READY_TO_PARSE=", ""
$topic_pub = (Get-Content .\.env | Where-Object { $_ -match "TOPIC_TABLES_READY_TO_ASSESS" -and $_ -notmatch "^#" }) -replace "TOPIC_TABLES_READY_TO_ASSESS=", ""

if (!$topic_sub -or !$topic_pub) {
    Write-Host "❌ Error: Pub/Sub topics not configured in .env file" -ForegroundColor Red
    Write-Host "Please check your .env file has the following variables:"
    Write-Host "TOPIC_BRD_READY_TO_PARSE=brd-ready-to-parse"
    Write-Host "TOPIC_TABLES_READY_TO_ASSESS=tables-ready-to-assess"
    exit 1
}

Write-Host " - ↘️ asset_indexer publishes to: $topic_sub"
Write-Host " - ↙️ content_processor subscribes to: $topic_sub"
Write-Host " - ↘️ content_processor publishes to: $topic_pub"
Write-Host ""

# Start the Pub/Sub bridge in a new PowerShell window
$psCommand = @"
cd "$pwd"
Write-Host `"Starting Pub/Sub forwarding bridge...`"
python subscribe_and_forward.py
"@

$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($psCommand))
Start-Process powershell -ArgumentList "-NoExit", "-EncodedCommand", $encodedCommand -WindowStyle Normal

# Wait a bit for the bridge to start
Start-Sleep -Seconds 2

Write-Host "📝 TESTING INSTRUCTIONS:" -ForegroundColor Green
Write-Host ""
Write-Host "1️⃣ START THE FUNCTIONS (in separate terminals):"
Write-Host "   - Run ./asset_indexer_run_local.ps1"
Write-Host "   - Run ./content_processor_run_local.ps1"
Write-Host ""
Write-Host "2️⃣ TRIGGER THE WORKFLOW:"
Write-Host "   - Run ./asset_indexer_send_local_test_event.ps1"
Write-Host ""
Write-Host "3️⃣ VERIFY THE RESULT:"
Write-Host "   - Check the logs in both function terminals"
Write-Host "   - Check that content_processor received the message and processed it"
Write-Host "   - Check that content_processor published to the next topic"
Write-Host ""
Write-Host "🔄 To verify Pub/Sub communication directly, run:"
Write-Host "   python test_workflow_chain.py"
Write-Host ""
Write-Host "🏁 The Pub/Sub forwarding bridge is running in another window"
Write-Host "   (don't close that window while testing)" 