<#
Fully deploys the asset_indexer function (GCS-triggered Cloud Function Gen 2)
- Ensures buckets exist
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

# 1. Parse DROP_FILE_BUCKET and PROCESSED_BUCKET from env.yaml
if (-not (Test-Path $EnvFile)) {
  Write-Error "❌ Missing env.yaml"
  exit 1
}
$DropBucket = (Get-Content $EnvFile | Where-Object { $_ -match '^DROP_FILE_BUCKET:' }) -replace '^DROP_FILE_BUCKET:\s*', ''
$ProcessedBucket = (Get-Content $EnvFile | Where-Object { $_ -match '^PROCESSED_BUCKET:' }) -replace '^PROCESSED_BUCKET:\s*', ''
if (-not $DropBucket) {
  Write-Error "❌ Could not extract DROP_FILE_BUCKET from env.yaml"
  exit 1
}
if (-not $ProcessedBucket) {
  Write-Error "❌ Could not extract PROCESSED_BUCKET from env.yaml"
  exit 1
}

# 2. Ensure buckets exist (optional, but good for first-time setup)
gcloud storage buckets create gs://$DropBucket --location=$Region --project=$Project --default-storage-class=STANDARD --uniform-bucket-level-access --quiet 2>$null
gcloud storage buckets create gs://$ProcessedBucket --location=$Region --project=$Project --default-storage-class=STANDARD --uniform-bucket-level-access --quiet 2>$null

Write-Host "`n🔐 Granting IAM roles..." -ForegroundColor Yellow

# 3. Add required IAM roles to the function's runtime service account
$Roles = @(
  "roles/datastore.user",
  "roles/pubsub.publisher",
  "roles/pubsub.subscriber",
  "roles/storage.objectAdmin",
  "roles/iam.serviceAccountTokenCreator",
  "roles/eventarc.eventReceiver",
  "roles/logging.logWriter"
)
foreach ($Role in $Roles) {
  gcloud projects add-iam-policy-binding $Project `
    --member="serviceAccount:$SA" `
    --role=$Role --quiet
}

# 4. Grant Eventarc service agent permissions
$ProjectNumber = gcloud projects describe $Project --format="value(projectNumber)"
$EventarcSA    = "serviceAccount:service-$ProjectNumber@gcp-sa-eventarc.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $Project `
  --member="$EventarcSA" `
  --role="roles/storage.admin" --quiet

gcloud projects add-iam-policy-binding $Project `
  --member="$EventarcSA" `
  --role="roles/pubsub.publisher" --quiet

# 5. Deploy the function with Storage event trigger
Write-Host "`n🚀 Deploying asset_indexer (triggered by gs://$DropBucket)..." -ForegroundColor Cyan

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
  --trigger-event-filters="bucket=$DropBucket" `
  --trigger-location=$Region

Write-Host "`n✅ Deployed asset_indexer with GCS trigger to $Region" -ForegroundColor Green
