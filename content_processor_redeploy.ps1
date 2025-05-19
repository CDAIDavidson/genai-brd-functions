# Quick redeploy of content_processor function code changes
# Use this when you only need to update the function code

$Project    = "genai-brd-qi"
$Region     = "australia-southeast1"
$SourcePath = "src/content_processor"
$EntryPoint = "content_processor"
$EnvFile    = "env.yaml"

Write-Host "`n🚀 Redeploying content_processor code changes..." -ForegroundColor Cyan

gcloud functions deploy $EntryPoint `
  --gen2 `
  --project $Project `
  --region $Region `
  --runtime python311 `
  --source $SourcePath `
  --entry-point $EntryPoint `
  --env-vars-file $EnvFile

Write-Host "`n✅ Redeployed content_processor code to $Region" -ForegroundColor Green 