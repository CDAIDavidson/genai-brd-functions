<#
.SYNOPSIS
  Upload a local file into the Firebase Storage emulator so it shows up in the UI.
#>

# ───────── Configuration ──────────────────────────────────────
# Path to your mock file:
$filePath = "C:\Users\chris\OneDrive\Desktop\mock_confluence_brd_redacted.html"

# The emulator’s project ID and bucket name:
$projectId = "genai-brd-qi"
$bucket    = "brd-genai-sink"

# ───────────────────────────────────────────────────────────────

Write-Host "`n⏳ Waiting for Firebase Storage emulator to be up on localhost:9199…" -ForegroundColor Cyan
# (Adjust the sleep if your emulator takes longer)
Start-Sleep -Seconds 3

Write-Host "`n📤 Uploading $filePath into emulator bucket $bucket …" -ForegroundColor Green

# Use the new storage:upload command in Firebase CLI
firebase storage:upload `
  $filePath `
  --project $projectId `
  --bucket $bucket `
  --emulator

if ($LASTEXITCODE -eq 0) {
  Write-Host "`n✅ File successfully uploaded to Firebase Storage emulator!" -ForegroundColor Green
  Write-Host "🔍 Open http://127.0.0.1:4000/storage/$bucket to view it." -ForegroundColor Yellow
} else {
  Write-Error "`n❌ Upload failed. Make sure the Storage emulator is running (`firebase emulators:start`)."
}
