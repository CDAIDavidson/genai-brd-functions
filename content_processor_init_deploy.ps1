# Deploys the content_processor function (Pub/Sub-triggered Cloud Function Gen 2)
# Handles incoming messages from BRD_ANALYSIS_TOPIC

$Project    = "genai-brd-qi"
$Region     = "australia-southeast1"
$SA         = "brd-functions-exec@$Project.iam.gserviceaccount.com"
$EnvFile    = "env.yaml"
$SourcePath = "src/content_processor"
$EntryPoint = "content_processor"

# 1. Parse required parameters from env.yaml
if (-not (Test-Path $EnvFile)) {
  Write-Error "❌ Missing env.yaml"
  exit 1
}
$TopicName = (Get-Content $EnvFile | Where-Object { $_ -match '^BRD_ANALYSIS_TOPIC:' }) -replace '^BRD_ANALYSIS_TOPIC:\s*', ''
if (-not $TopicName) {
  Write-Error "❌ Could not extract BRD_ANALYSIS_TOPIC from env.yaml"
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
  "roles/eventarc.eventReceiver",
  "roles/logging.logWriter"
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
  --role="roles/pubsub.subscriber" --quiet

gcloud projects add-iam-policy-binding $Project `
  --member="$EventarcSA" `
  --role="roles/pubsub.publisher" --quiet

# 4. Deploy the function with Pub/Sub event trigger
Write-Host "`n🚀 Deploying content_processor (triggered by $TopicName)..." -ForegroundColor Cyan

gcloud functions deploy $EntryPoint `
  --gen2 `
  --project $Project `
  --region $Region `
  --runtime python311 `
  --source $SourcePath `
  --entry-point $EntryPoint `
  --service-account $SA `
  --env-vars-file $EnvFile `
  --trigger-topic $TopicName `
  --trigger-location $Region

Write-Host "`n✅ Deployed content_processor with Pub/Sub trigger to $Region" -ForegroundColor Green 