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
from asset_indexer.common.base import DocumentClass, FunctionStatus, DocumentType, FunctionData
# from asset_indexer.common.firestore_utils import firestore_upsert, firestore_update
from asset_indexer.common import running_in_gcp, is_storage_emulator, get_environment_name, setup_emulator_environment

# For local testing only
try:
    # Try to import for direct local testing if possible
    if not running_in_gcp():
        from content_processor.main import content_processor as local_content_processor
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

def call_content_processor(document_id):
    """Call content_processor function either directly (local) or via HTTP (prod)"""
    if not running_in_gcp() and local_content_processor:
        # Local direct call if we have the imported function
        print(f"[DEBUG] Calling content_processor directly (local import)")
        return local_content_processor(brd_workflow_id=document_id, document_id=document_id)
    elif not running_in_gcp():
        # Local HTTP call if direct import failed
        print(f"[DEBUG] Calling content_processor via HTTP (local)")
        response = requests.post(
            "http://localhost:8083",
            json={"brd_workflow_id": document_id, "document_id": document_id}
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
            json={"brd_workflow_id": document_id, "document_id": document_id}
        )
        
        if response.status_code >= 400:
            raise Exception(f"content_processor HTTP call failed: {response.status_code} - {response.text}")
        
        return response.json().get("result")

# ── Main Cloud Function ─────────────────────────────────────────────────────
@functions_framework.cloud_event
def asset_indexer(cloud_event):
    # Extract bucket & filename

    payload = cloud_event.data
    src_bucket_name = payload["bucket"]
    src_file_name = payload["name"]

    ext = os.path.splitext(src_file_name)[1]
    brd_id = secrets.token_hex(5)
    print(f"[DEBUG] brd_id={brd_id}")
    dest_file_name = f"{brd_id}{ext}"

    src_bucket = storage_client.bucket(SOURCE_BUCKET)
    dest_bucket = storage_client.bucket(DEST_BUCKET)

    # # Update in progress status
    # environment = get_environment_name()
    # print(f"[DEBUG] Setting document environment to: {environment}")
    
    # Generate a document ID to use for both in-progress and completed states
    document_id = secrets.token_hex(8)
    
    function_item = FunctionData(
        timestamp_created=datetime.now().isoformat(),
        timestamp_updated=datetime.now().isoformat(),
        description="Assigns a unique identifier to incoming files and prepares them for further processing, ensuring each document can be tracked throughout its lifecycle.",
        description_heading="File Indexing Function",
        working_on="Assigning GUID",
        status=FunctionStatus.IN_PROGRESS,
        cloud_function_name="Asset Indexer"
    )
    function_document_data = DocumentClass(
        item_type=DocumentType.FUNCTION_EXECUTION_DATA,
        brd_workflow_id=brd_id,
        timestamp_created=datetime.now().isoformat(),
        timestamp_updated=datetime.now().isoformat(),
        description="asset_indexer",
        description_heading="asset_indexer description",
        item={"function_data":function_item.dict()}
    )

    function_document_ref = firestore_client.collection(COLLECTION_NAME).document(document_id)
    function_document_ref.set(function_document_data.to_dict())
 
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

        sleep(10)
    

        # Update document status to completed
        function_document_ref.update({
            "item.function_data.status": FunctionStatus.COMPLETED,
            "item.function_data.timestamp_updated": datetime.now().isoformat(),
            "timestamp_updated": datetime.now().isoformat()
        })
        print(f"[DEBUG] Updated document with ID: {document_id} to completed status")
        print(f"[{brd_id}] copied {src_file_name} ➜ {dest_file_name}")

    except Exception as exc:
        # Update document status to failed
        function_document_ref.update({
            "item.function_data.status": FunctionStatus.FAILED,
            "item.function_data.timestamp_updated": datetime.now().isoformat(),
            "timestamp_updated": datetime.now().isoformat()
        })
        raise
