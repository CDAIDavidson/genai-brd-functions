<#
Deploys a single Cloud Function: asset_indexer
#>

$Project = "genai-brd-qi"
$Region  = "australia-southeast1"
$SA      = "brd-functions-exec@$Project.iam.gserviceaccount.com"

gcloud functions deploy asset_indexer `
  --gen2 `
  --project  $Project `
  --region   $Region `
  --runtime  python311 `
  --source   "src/asset_indexer" `
  --entry-point asset_indexer `
  --service-account $SA `
  --env-vars-file env.yaml `
  --trigger-resource $env:DROP_FILE_BUCKET `
  --trigger-event google.storage.object.finalize `
  --allow-unauthenticated
