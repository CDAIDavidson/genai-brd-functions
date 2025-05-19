"""
asset_indexer – single-purpose Cloud Function.

• Copies a file from DROP_BRD_BUCKET ➜ BRD_PROCESSED_BUCKET
• Logs execution metadata in Firestore
• Directly triggers content_processor function with brd_workflow_id
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
from google.cloud import firestore, storage
import requests
import google.auth.transport.requests
import google.oauth2.id_token

# Local imports
from .common.base import Document, FunctionStatus, PubSubMessage
from .common.firestore_utils import firestore_upsert
from .common import running_in_gcp, is_storage_emulator, get_environment_name, setup_emulator_environment

# For local testing only
try:
    # Try to import for direct local testing if possible
    if not running_in_gcp():
        from ..content_processor.main import content_processor as local_content_processor
except ImportError:
    local_content_processor = None
    print("[DEBUG] Could not import content_processor for direct local calling")

# Load dotenv for local development (ignored in prod)
load_dotenv()

# ── Config from env (all environment variables are required) ──────────────────
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
SOURCE_BUCKET = os.getenv("DROP_BRD_BUCKET")
DEST_BUCKET = os.getenv("BRD_PROCESSED_BUCKET")
COLLECTION_NAME = os.getenv("METADATA_COLLECTION")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID")
REGION = os.getenv("REGION", "australia-southeast1")  # Default region

# Set up emulator environment if needed
setup_emulator_environment()

# ── Client initialization ──────────────────────────────────────────────────
storage_client = storage.Client()
firestore_client = firestore.Client(project=PROJECT_ID)

def call_content_processor(brd_workflow_id, document_id):
    """Call content_processor function either directly (local) or via HTTP (prod)"""
    if not running_in_gcp() and local_content_processor:
        # Local direct call if we have the imported function
        print(f"[DEBUG] Calling content_processor directly (local import)")
        return local_content_processor(brd_workflow_id=brd_workflow_id, document_id=document_id)
    elif not running_in_gcp():
        # Local HTTP call if direct import failed
        print(f"[DEBUG] Calling content_processor via HTTP (local)")
        response = requests.post(
            "http://localhost:8083",
            json={"brd_workflow_id": brd_workflow_id, "document_id": document_id}
        )
        if response.status_code >= 400:
            raise Exception(f"content_processor HTTP call failed: {response.text}")
        return response.json().get("result")
    else:
        # Production HTTP call with auth
        print(f"[DEBUG] Calling content_processor via HTTP (production)")
        function_url = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net/content_processor"
        
        # Get auth token
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, function_url)
        
        # Call the function with auth token
        response = requests.post(
            function_url,
            headers={"Authorization": f"Bearer {id_token}"},
            json={"brd_workflow_id": brd_workflow_id, "document_id": document_id}
        )
        
        if response.status_code >= 400:
            raise Exception(f"content_processor HTTP call failed: {response.status_code} - {response.text}")
        
        return response.json().get("result")

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
    environment = get_environment_name()
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

        # Call content_processor using the appropriate method
        print(f"[DEBUG] Calling content_processor with brd_workflow_id={brd_id}")
        additional_data = {
            "title": os.path.splitext(os.path.basename(src_file_name))[0],
            "source_file": src_file_name
        }
        
        try:
            result = call_content_processor(brd_id, brd_id)
            print(f"[DEBUG] Successfully called content_processor for brd_workflow_id={brd_id}. Result: {result}")
        except Exception as func_exc:
            print(f"[ERROR] Failed to call content_processor: {str(func_exc)}", file=sys.stderr)
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
