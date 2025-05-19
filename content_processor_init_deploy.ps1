# Deploys the content_processor function (HTTP-triggered Cloud Function Gen 2)
# Can be called directly by asset_indexer or other functions

$Project    = "genai-brd-qi"
$Region     = "australia-southeast1"
$SA         = "brd-functions-exec@$Project.iam.gserviceaccount.com"
$EnvFile    = "env.yaml"
$SourcePath = "src/content_processor"
$EntryPoint = "content_processor"

# 1. Ensure env.yaml exists
if (-not (Test-Path $EnvFile)) {
  Write-Error "❌ Missing env.yaml"
  exit 1
}

Write-Host "`n🔐 Granting IAM roles..." -ForegroundColor Yellow

# 2. Add required IAM roles to the function's runtime service account
$Roles = @(
  "roles/datastore.user",
  "roles/pubsub.publisher",  # Still needed for publishing to output topic
  "roles/storage.objectAdmin",
  "roles/iam.serviceAccountTokenCreator",
  "roles/logging.logWriter",
  "roles/cloudfunctions.invoker"  # Added for direct function calls
)
foreach ($Role in $Roles) {
  gcloud projects add-iam-policy-binding $Project `
    --member="serviceAccount:$SA" `
    --role=$Role --quiet
}

# 3. Allow the service account to invoke itself (for direct function calls)
gcloud functions add-invoker-policy-binding $EntryPoint `
  --project $Project `
  --region $Region `
  --member="serviceAccount:$SA"

# 4. Deploy the function with HTTP trigger
Write-Host "`n🚀 Deploying content_processor (HTTP-triggered)..." -ForegroundColor Cyan

gcloud functions deploy $EntryPoint `
  --gen2 `
  --project $Project `
  --region $Region `
  --runtime python311 `
  --source $SourcePath `
  --entry-point "process_http_request" `  # Use the HTTP entry point
  --service-account $SA `
  --env-vars-file $EnvFile `
  --trigger-http `  # Change to HTTP trigger
  --allow-unauthenticated

Write-Host "`n✅ Deployed content_processor with HTTP trigger to $Region" -ForegroundColor Green 