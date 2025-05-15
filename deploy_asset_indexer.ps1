<#
Fully deploys the asset_indexer function (GCS-triggered Cloud Function Gen 2)

What it does:
- Parses DROP_FILE_BUCKET from env.yaml
- Grants required IAM roles to:
    • runtime service account
    • Eventarc service agent
- Deploys using --trigger-event-filters (GCS finalize)
#>

$Project    = "genai-brd-qi"
$Region     = "australia-southeast1"
$SA         = "brd-functions-exec@$Project.iam.gserviceaccount.com"
$EnvFile    = "env.yaml"
$SourcePath = "src/asset_indexer"
$EntryPoint = "asset_indexer"

# 1. Parse DROP_FILE_BUCKET from env.yaml
if (-not (Test-Path $EnvFile)) {
  Write-Error "❌ Missing env.yaml"
  exit 1
}
$Bucket = (Get-Content $EnvFile | Where-Object { $_ -match '^DROP_FILE_BUCKET:' }) -replace '^DROP_FILE_BUCKET:\s*', ''
if (-not $Bucket) {
  Write-Error "❌ Could not extract DROP_FILE_BUCKET from env.yaml"
  exit 1
}

Write-Host "`n🔐 Granting IAM roles..." -ForegroundColor Yellow

# 2. Add required IAM roles to the function's runtime service account
$Roles = @(
  "roles/datastore.user",
  "roles/pubsub.publisher",
  "roles/pubsub.subscriber",
  "roles/storage.objectAdmin",
  "roles/iam.serviceAccountTokenCreator",
  "roles/eventarc.eventReceiver"
)
foreach ($Role in $Roles) {
  gcloud projects add-iam-policy-binding $Project `
    --member="serviceAccount:$SA" `
    --role=$Role --quiet
}

# 3. Grant Eventarc service agent permissions
$ProjectNumber = gcloud projects describe $Project --format="value(projectNumber)"
$EventarcSA    = "serviceAccount:service-$ProjectNumber@gcp-sa-eventarc.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $Project `
  --member="$EventarcSA" `
  --role="roles/storage.admin" --quiet

gcloud projects add-iam-policy-binding $Project `
  --member="$EventarcSA" `
  --role="roles/pubsub.publisher" --quiet

# 4. Deploy the function with Storage event trigger
Write-Host "`n🚀 Deploying asset_indexer (triggered by gs://$Bucket)..." -ForegroundColor Cyan

gcloud functions deploy $EntryPoint `
  --gen2 `
  --project $Project `
  --region $Region `
  --runtime python311 `
  --source $SourcePath `
  --entry-point $EntryPoint `
  --service-account $SA `
  --env-vars-file $EnvFile `
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" `
  --trigger-event-filters="bucket=$Bucket" `
  --trigger-location=$Region

Write-Host "`n✅ Deployed asset_indexer with GCS trigger to $Region" -ForegroundColor Green
