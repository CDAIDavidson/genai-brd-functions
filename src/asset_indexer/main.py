"""
asset_indexer – single-purpose Cloud Function.

• Copies a file from DROP_FILE_BUCKET ➜ PROCESSED_BUCKET
• Logs execution metadata in Firestore
• Publishes a JSON message to DOC_INDEX_TOPIC
"""

from dotenv import load_dotenv

load_dotenv()                      # <- enables local .env; ignored in prod

import json
import os
import secrets
import sys
from datetime import datetime
from time import sleep

import functions_framework
from google.cloud import firestore, pubsub_v1, storage

# ── Config from env (defaults only for local smoke-tests) ──────────────────
PROJECT_ID          = os.getenv("GOOGLE_CLOUD_PROJECT", "genai-brd-qi")

# Set emulator environment variables only if not running in GCP
def running_in_gcp():
    # GCP sets this environment variable in Cloud Functions/Run
    return os.getenv("K_SERVICE") is not None

if not running_in_gcp():
    if os.getenv("FIRESTORE_EMULATOR_HOST") is None:
        os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8090"
    if os.getenv("FIREBASE_STORAGE_EMULATOR_HOST") is None:
        os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "127.0.0.1:9199"

SOURCE_BUCKET       = os.getenv("DROP_FILE_BUCKET", "genai-brd-qi").strip()
# For local development, use the same bucket
DEST_BUCKET         = os.getenv("PROCESSED_BUCKET", SOURCE_BUCKET).strip()

COLLECTION_NAME     = os.getenv("METADATA_COLLECTION", "metadata")
PUBSUB_TOPIC_NAME   = os.getenv("DOC_INDEX_TOPIC", "document-indexer")

FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "default")

# ── Clients (reuse across invocations) ─────────────────────────────────────
storage_client = storage.Client()
pubsub_client  = pubsub_v1.PublisherClient()
topic_path     = pubsub_client.topic_path(PROJECT_ID, PUBSUB_TOPIC_NAME)

print(f"[DEBUG] Initializing Firestore client:")
print(f"[DEBUG] - Project ID: {PROJECT_ID}")
print(f"[DEBUG] - Database ID: {FIRESTORE_DATABASE_ID}")
print(f"[DEBUG] - Collection: {COLLECTION_NAME}")
print(f"[DEBUG] - Emulator mode: {not running_in_gcp()}")

# Initialize Firestore with the correct database and emulator settings
if not running_in_gcp():
    print(f"[DEBUG] Using emulator at {os.environ['FIRESTORE_EMULATOR_HOST']}")
    print(f"[DEBUG] View data at: http://127.0.0.1:4000/firestore/data/{FIRESTORE_DATABASE_ID}/{COLLECTION_NAME}")
    firestore_client = firestore.Client(project=PROJECT_ID)
else:
    firestore_client = firestore.Client(project=PROJECT_ID)
# ───────────────────────────────────────────────────────────────────────────

print(f"[DEBUG] GOOGLE_CLOUD_PROJECT={os.getenv('GOOGLE_CLOUD_PROJECT')}")
print(f"[DEBUG] DROP_FILE_BUCKET={os.getenv('DROP_FILE_BUCKET')}")
print(f"[DEBUG] PROCESSED_BUCKET={os.getenv('PROCESSED_BUCKET')}")
print(f"[DEBUG] METADATA_COLLECTION={os.getenv('METADATA_COLLECTION')}")
print(f"[DEBUG] DOC_INDEX_TOPIC={os.getenv('DOC_INDEX_TOPIC')}")
print(f"[DEBUG] SOURCE_BUCKET={SOURCE_BUCKET}")
print(f"[DEBUG] DEST_BUCKET={DEST_BUCKET}")
print(f"[DEBUG] COLLECTION_NAME={COLLECTION_NAME}")
print(f"[DEBUG] PUBSUB_TOPIC_NAME={PUBSUB_TOPIC_NAME}")

def _log(brd_id: str, status: str, start_time: datetime | None, **extras):
    """Insert or update a Firestore doc that tracks this invocation."""
    data = {
        "workflow_id": brd_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": "emulator" if not running_in_gcp() else "production",
        **extras,
    }
    try:
        doc_ref = firestore_client.collection(COLLECTION_NAME).document(brd_id)
        print(f"[DEBUG] Firestore write details:")
        print(f"[DEBUG] - Database: {firestore_client._database}")
        print(f"[DEBUG] - Project: {firestore_client.project}")
        print(f"[DEBUG] - Collection: {COLLECTION_NAME}")
        print(f"[DEBUG] - Document path: {doc_ref.path}")
        print(f"[DEBUG] - Data: {data}")
        doc_ref.set(data, merge=True)
        print(f"[DEBUG] Successfully wrote to Firestore: {doc_ref.path}")
        # Read back for confirmation
        doc = doc_ref.get()
        print(f"[DEBUG] Read back doc: {doc.to_dict()}")
        db_id = firestore_client._database if firestore_client._database else 'default'
        if db_id == 'default':
            url = f"http://127.0.0.1:4000/firestore/default/data/{COLLECTION_NAME}/{brd_id}"
        else:
            url = f"http://127.0.0.1:4000/firestore/data/{db_id}/{COLLECTION_NAME}/{brd_id}"
        print(f"[DEBUG] View this document in the Emulator UI: {url}")
    except Exception as e:
        print(f"[ERROR] Failed to write to Firestore: {str(e)}", file=sys.stderr)
        raise

def is_storage_emulator():
    return os.getenv("FIREBASE_STORAGE_EMULATOR_HOST") is not None

@functions_framework.cloud_event
def asset_indexer(cloud_event):
    start_time = datetime.utcnow()

    # Extract bucket & filename
    if cloud_event is None:  # local / unit-test
        src_bucket_name = SOURCE_BUCKET
        src_file_name   = "mock_confluence_brd_redacted.html"
    else:
        sleep(1)                                # GCS metadata latency
        payload        = cloud_event.data
        src_bucket_name = payload["bucket"]
        src_file_name   = payload["name"]

    ext            = os.path.splitext(src_file_name)[1]
    brd_id         = secrets.token_hex(5)
    print(f"[DEBUG] brd_id={brd_id}")
    dest_file_name = f"{brd_id}{ext}"

    src_bucket  = storage_client.bucket(src_bucket_name)
    dest_bucket = storage_client.bucket(DEST_BUCKET)

    # Initial log
    _log(brd_id, "In Progress", start_time,
         source=src_file_name, dest=dest_file_name)

    try:
        src_blob  = src_bucket.blob(src_file_name)
        # Use workaround only if running in the emulator
        if is_storage_emulator():
            content = src_blob.download_as_bytes()
            dest_blob = dest_bucket.blob(dest_file_name)
            dest_blob.upload_from_string(content)
        else:
            dest_blob = src_bucket.copy_blob(src_blob, dest_bucket, dest_file_name)
        dest_blob.metadata = {"source_file_name": src_file_name}
        if not is_storage_emulator():
            dest_blob.patch()
        src_blob.delete()

        # Success log
        _log(brd_id, "Completed", start_time,
             duration=(datetime.utcnow() - start_time).total_seconds())

        # Notify downstream
        msg = {"brd_workflow_id": brd_id, "document_id": brd_id}
        print(f"[DEBUG] About to publish to Pub/Sub: topic_path={topic_path}, msg={msg}")
        try:
            pubsub_client.publish(topic_path, data=json.dumps(msg).encode()).result()
            print(f"[DEBUG] Published to Pub/Sub: topic_path={topic_path}, msg={msg}")
        except Exception as pubsub_exc:
            print(f"[ERROR] Failed to publish to Pub/Sub: {str(pubsub_exc)}", file=sys.stderr)
            raise  # Re-raise to be caught by outer try/except

        print(f"[{brd_id}] copied {src_file_name} ➜ {dest_file_name}")

    except Exception as exc:
        _log(brd_id, "Failed", start_time)
        print(f"[{brd_id}] ERROR: {exc}", file=sys.stderr)
        raise
