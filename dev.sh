#!/usr/bin/env bash
# Sets emulator and bucket env-vars for this shell.

export FIRESTORE_EMULATOR_HOST=127.0.0.1:8090
export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
export FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199
export STORAGE_EMULATOR_HOST=http://127.0.0.1:9199
export PUBSUB_EMULATOR_HOST=127.0.0.1:8085

export GOOGLE_CLOUD_PROJECT=genai-brd-qi
export DROP_FILE_BUCKET=brd-genai-sink
export PROCESSED_BUCKET=brd-genai-doc-processor-input
export METADATA_COLLECTION=metadata

echo -e "\n✔︎ Emulator + bucket variables set for this shell."
echo   "  (Make sure the main emulator suite is already running!)"
