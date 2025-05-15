# Quick redeploy of asset_indexer function code changes
# Use this when you only need to update the function code

$Project    = "genai-brd-qi"
$Region     = "australia-southeast1"
$SourcePath = "src/asset_indexer"
$EntryPoint = "asset_indexer"
$EnvFile    = "env.yaml"

Write-Host "`n🚀 Redeploying asset_indexer code changes..." -ForegroundColor Cyan

gcloud functions deploy $EntryPoint `
  --gen2 `
  --project $Project `
  --region $Region `
  --runtime python311 `
  --source $SourcePath `
  --entry-point $EntryPoint `
  --env-vars-file $EnvFile

Write-Host "`n✅ Redeployed asset_indexer code to $Region" -ForegroundColor Green 