"""
asset_indexer – single-purpose Cloud Function.

• Copies a file from DROP_BRD_BUCKET ➜ BRD_PROCESSED_BUCKET
• Logs execution metadata in Firestore
• Publishes a JSON message to DOC_INDEX_TOPIC
"""

# Standard library imports
import json
import os
import secrets
import sys
from datetime import datetime
from time import sleep

# Third-party imports
from dotenv import load_dotenv
import functions_framework
from google.cloud import firestore, pubsub_v1, storage

# Local imports - changing to relative imports
from .common.base import Document, FunctionStatus
from .common.firestore_utils import firestore_upsert

# Load dotenv for local development (ignored in prod)
load_dotenv()

# ── Environment detection functions ─────────────────────────────────────────
def running_in_gcp():
    """Check if the function is running in GCP (not in emulator)
    
    Google Cloud Functions and Cloud Run set several environment variables
    in production environments that we can use to detect where we're running.
    """
    # Check for emulator environment variables first - these take precedence
    if os.getenv("FIRESTORE_EMULATOR_HOST") or os.getenv("FIREBASE_STORAGE_EMULATOR_HOST"):
        print("[DEBUG] Running in emulator environment")
        return False
        
    # Check for GCP-specific environment variables
    gcp_indicators = [
        "K_SERVICE",              # Cloud Run/Functions service name
        "FUNCTION_NAME",          # Cloud Functions specific
        "FUNCTION_TARGET",        # Cloud Functions specific
        "FUNCTION_SIGNATURE_TYPE" # Cloud Functions specific
    ]
    
    # Debug output
    for var in gcp_indicators:
        if os.getenv(var):
            print(f"[DEBUG] Found GCP indicator: {var}={os.getenv(var)}")
    
    is_gcp = any(os.getenv(var) is not None for var in gcp_indicators)
    print(f"[DEBUG] running_in_gcp() returned: {is_gcp}")
    return is_gcp

def is_storage_emulator():
    """Check if using storage emulator"""
    return os.environ.get("FIREBASE_STORAGE_EMULATOR_HOST") is not None

# ── Config from env (all environment variables are required) ──────────────────
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
SOURCE_BUCKET = os.getenv("DROP_BRD_BUCKET")
DEST_BUCKET = os.getenv("BRD_PROCESSED_BUCKET")
COLLECTION_NAME = os.getenv("METADATA_COLLECTION")
PUBSUB_TOPIC_NAME = os.getenv("DOC_INDEX_TOPIC")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID")

# Set emulator environment variables only if not running in GCP
if not running_in_gcp():
    if os.getenv("FIRESTORE_EMULATOR_HOST") is None:
        os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8090"
    if os.getenv("FIREBASE_STORAGE_EMULATOR_HOST") is None:
        os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "127.0.0.1:9199"

# Force emulator settings for local development
# FIRESTORE_EMULATOR_HOST and FIREBASE_STORAGE_EMULATOR_HOST are strong indicators
# that we're in a local development environment
if not os.getenv("K_SERVICE"):  # Not in Cloud Run/Functions
    # Set default emulator hosts if not already set
    if "FIRESTORE_EMULATOR_HOST" not in os.environ:
        print("[DEBUG] Setting default FIRESTORE_EMULATOR_HOST")
        os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8090"
    if "FIREBASE_STORAGE_EMULATOR_HOST" not in os.environ:
        print("[DEBUG] Setting default FIREBASE_STORAGE_EMULATOR_HOST")
        os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "127.0.0.1:9199"
    
    print(f"[DEBUG] Using emulators: FIRESTORE={os.environ.get('FIRESTORE_EMULATOR_HOST')}, STORAGE={os.environ.get('FIREBASE_STORAGE_EMULATOR_HOST')}")

# ── Client initialization ──────────────────────────────────────────────────
storage_client = storage.Client()
pubsub_client = pubsub_v1.PublisherClient()
topic_path = pubsub_client.topic_path(PROJECT_ID, PUBSUB_TOPIC_NAME)
firestore_client = firestore.Client(project=PROJECT_ID)

# ── Main Cloud Function ─────────────────────────────────────────────────────
@functions_framework.cloud_event
def asset_indexer(cloud_event):
    start_time = datetime.utcnow()

    # Extract bucket & filename
    if cloud_event is None:  # local / unit-test
        src_bucket_name = SOURCE_BUCKET
        src_file_name = "mock_confluence_brd_redacted.html"
    else:
        payload = cloud_event.data
        src_bucket_name = payload["bucket"]
        src_file_name = payload["name"]

    ext = os.path.splitext(src_file_name)[1]
    brd_id = secrets.token_hex(5)
    print(f"[DEBUG] brd_id={brd_id}")
    dest_file_name = f"{brd_id}{ext}"

    src_bucket = storage_client.bucket(src_bucket_name)
    dest_bucket = storage_client.bucket(DEST_BUCKET)

    # Update in progress status
    environment = "emulator" if os.environ.get("FIRESTORE_EMULATOR_HOST") else "production"
    print(f"[DEBUG] Setting document environment to: {environment}")
    
    inprogress_document = Document.create_function_execution(
        id=brd_id,
        brd_workflow_id=brd_id,
        status=FunctionStatus.IN_PROGRESS,
        description="Processing BRD document",
        description_heading="Asset Indexer Function",
        environment=environment
    )
    firestore_upsert(firestore_client, COLLECTION_NAME, inprogress_document)
    
    sleep(10)
    
    try:
        src_blob = src_bucket.blob(src_file_name)
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
        completed_document = Document.create_function_execution(
            id=brd_id,
            brd_workflow_id=brd_id,
            status=FunctionStatus.COMPLETED,
            description="Successfully processed BRD document",
            description_heading="Asset Indexer Function",
            environment=environment
        )
        firestore_upsert(firestore_client, COLLECTION_NAME, completed_document)

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
        # Failure log
        failed_document = Document.create_function_execution(
            id=brd_id,
            brd_workflow_id=brd_id,
            status=FunctionStatus.FAILED,
            description=f"Failed to process BRD document: {str(exc)}",
            description_heading="Asset Indexer Function",
            source=src_file_name,
            dest=dest_file_name,
            environment=environment,
            error=str(exc)
        )
        firestore_upsert(firestore_client, COLLECTION_NAME, failed_document)
        print(f"[{brd_id}] ERROR: {exc}", file=sys.stderr)
        raise
