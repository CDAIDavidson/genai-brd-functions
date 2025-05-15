@echo off
REM Sets emulator and bucket env-vars for this CMD window.

set "FIRESTORE_EMULATOR_HOST=127.0.0.1:8090"
set "FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099"
set "FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199"
set "STORAGE_EMULATOR_HOST=http://127.0.0.1:9199"
set "PUBSUB_EMULATOR_HOST=127.0.0.1:8085"

set "GOOGLE_CLOUD_PROJECT=genai-brd-qi"
set "DROP_FILE_BUCKET=brd-genai-sink"
set "PROCESSED_BUCKET=brd-genai-doc-processor-input"
set "METADATA_COLLECTION=metadata"

echo.
echo [32m✔︎ Emulator + bucket variables set for this window.[0m
echo   (Make sure the main emulator suite is already running!)
echo.
