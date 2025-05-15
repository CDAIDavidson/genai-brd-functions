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

SOURCE_BUCKET       = os.getenv("DROP_FILE_BUCKET", "brd-genai-sink")
DEST_BUCKET         = os.getenv("PROCESSED_BUCKET", "brd-genai-doc-processor-input")

COLLECTION_NAME     = os.getenv("METADATA_COLLECTION", "metadata")
PUBSUB_TOPIC_NAME   = os.getenv("DOC_INDEX_TOPIC", "document-indexer")

# ── Clients (reuse across invocations) ─────────────────────────────────────
storage_client = storage.Client()
pubsub_client  = pubsub_v1.PublisherClient()
topic_path     = pubsub_client.topic_path(PROJECT_ID, PUBSUB_TOPIC_NAME)
firestore_client = firestore.Client(project=PROJECT_ID)
# ───────────────────────────────────────────────────────────────────────────


def _log(brd_id: str, status: str, start_time: datetime | None, **extras):
    """Insert or update a Firestore doc that tracks this invocation."""
    data = {
        "workflow_id": brd_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **extras,
    }
    firestore_client.collection(COLLECTION_NAME).document(brd_id).set(
        data, merge=True
    )


@functions_framework.cloud_event
def asset_indexer(cloud_event):
    start_time = datetime.utcnow()

    # Extract bucket & filename
    if cloud_event is None:  # local / unit-test
        src_bucket_name = SOURCE_BUCKET
        src_file_name   = "mock_confluence_brd_redacted.html"
    else:
        sleep(5)                                # GCS metadata latency
        payload        = cloud_event.data
        src_bucket_name = payload["bucket"]
        src_file_name   = payload["name"]

    ext            = os.path.splitext(src_file_name)[1]
    brd_id         = secrets.token_hex(5)
    dest_file_name = f"{brd_id}{ext}"

    src_bucket  = storage_client.bucket(src_bucket_name)
    dest_bucket = storage_client.bucket(DEST_BUCKET)

    # Initial log
    _log(brd_id, "In Progress", start_time,
         source=src_file_name, dest=dest_file_name)

    try:
        src_blob  = src_bucket.blob(src_file_name)
        dest_blob = src_bucket.copy_blob(src_blob, dest_bucket, dest_file_name)
        dest_blob.metadata = {"source_file_name": src_file_name}
        dest_blob.patch()
        src_blob.delete()

        # Success log
        _log(brd_id, "Completed", start_time,
             duration=(datetime.utcnow() - start_time).total_seconds())

        # Notify downstream
        msg = {"workflow_id": brd_id, "document_path": dest_file_name}
        pubsub_client.publish(topic_path, data=json.dumps(msg).encode()).result()

        print(f"[{brd_id}] copied {src_file_name} ➜ {dest_file_name}")

    except Exception as exc:
        _log(brd_id, "Failed", start_time)
        print(f"[{brd_id}] ERROR: {exc}", file=sys.stderr)
        raise
