"""
content_processor – Cloud Function to process BRD content.

• Can be called directly by other Cloud Functions
• Processes and extracts tables and key content
• Logs execution metadata in Firestore
"""

# Standard library imports
import json
import os
import sys
import base64
import secrets
from datetime import datetime
from time import sleep

# Third-party imports
from dotenv import load_dotenv
import functions_framework
from google.cloud import firestore, storage

# Local imports
from .common.base import Document, FunctionStatus, DocumentType, PubSubMessage
from .common.firestore_utils import firestore_upsert
from .common import running_in_gcp, is_storage_emulator, get_environment_name, setup_emulator_environment

# Load dotenv for local development (ignored in prod)
load_dotenv()

# ── Config from env (all environment variables are required) ──────────────────
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
SOURCE_BUCKET = os.getenv("BRD_PROCESSED_BUCKET")
COLLECTION_NAME = os.getenv("METADATA_COLLECTION")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID")

# Set up emulator environment if needed
setup_emulator_environment()

# ── Client initialization ──────────────────────────────────────────────────
storage_client = storage.Client()
firestore_client = firestore.Client(project=PROJECT_ID)

def download_document_content(document_id):
    """
    Download document content from Storage bucket.
    
    Args:
        document_id: The ID of the document to download
        
    Returns:
        The document content as text
    """
    try:
        # Get bucket
        src_bucket_name = SOURCE_BUCKET
        src_bucket = storage_client.bucket(src_bucket_name)
        
        # List blobs with document_id prefix to find the actual filename with extension
        blobs = list(src_bucket.list_blobs(prefix=document_id))
        
        if not blobs:
            # Try the old .html assumption as fallback
            src_file_name = f"{document_id}.html"
            src_blob = src_bucket.blob(src_file_name)
        else:
            # Use the first matching blob
            src_blob = blobs[0]
        
        print(f"[DEBUG] Downloading document: {src_blob.name}")
        
        # Download the document content
        return src_blob.download_as_text()
    except Exception as e:
        print(f"[ERROR] Failed to download document content: {e}")
        raise

def extract_tables_from_content(document_content):
    """
    Extract tables from document content.
    
    Args:
        document_content: The document content as text
        
    Returns:
        List of extracted tables
    """
    # In a real implementation, this would do proper HTML parsing and tables extraction
    # For now, it's a simulated extraction
    simulated_tables = [
        {"table_id": "table1", "title": "Requirements", "rows": 5, "columns": 3},
        {"table_id": "table2", "title": "Timeline", "rows": 3, "columns": 2}
    ]
    
    return simulated_tables

# ── Main Function ─────────────────────────────────────────────────────
def content_processor(document_id=None, brd_workflow_id=None):
    """
    Process BRD document content.
    
    Can be triggered directly by other functions via HTTP.
    
    Args:
        document_id: Document ID (also used as brd_workflow_id if not specified)
        brd_workflow_id: Optional BRD workflow ID (defaults to document_id)
        
    Returns:
        Processing results dictionary if successful
    """
    print(f"[Function Started] content_processor")
    
    try:
        # If brd_workflow_id not provided, use document_id for both
        if brd_workflow_id is None:
            brd_workflow_id = document_id
            
        # Validate required parameters
        if document_id:
            # Direct function call with provided ID
            print(f"[DEBUG] Direct function call with document_id={document_id}")
        else:
            # Missing required parameter
            error_message = "Missing required parameter: document_id must be provided"
            print(f"[ERROR] {error_message}")
            raise ValueError(error_message)
    
        print(f"[DEBUG] Starting content_processor for document_id={document_id}")
        
        # Update in progress status
        environment = get_environment_name()
        print(f"[DEBUG] Setting document environment to: {environment}")
        
        # Create in-progress document record
        # Generate a document ID to use for both in-progress and completed states
        document_id = secrets.token_hex(8)
        
        inprogress_document = Document.create_document(
            brd_workflow_id=brd_workflow_id,
            status=FunctionStatus.IN_PROGRESS,
            description="Processing BRD document content",
            description_heading="Content Processor Function",
            environment=environment
        )
        firestore_upsert(firestore_client, COLLECTION_NAME, inprogress_document, document_id=document_id)
        
        print(f"[DEBUG] Created in-progress document with ID: {document_id}")
        
        # Download document content from storage
        document_content = download_document_content(document_id)
        
        # Extract tables from document content
        extracted_tables = extract_tables_from_content(document_content)
        
        # Create processing results object
        processing_results = {
            "document_id": document_id,
            "brd_workflow_id": brd_workflow_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tables": extracted_tables,
            "title": f"BRD Document {document_id}",
            "tables_count": len(extracted_tables)
        }
        # Log success status in Firestore
        completed_document = Document.update_document(
            brd_workflow_id=brd_workflow_id,
            status=FunctionStatus.COMPLETED,
            description="Successfully processed BRD content",
            description_heading="Content Processor Function",
            environment=environment,
            processing_results=processing_results
        )
        # Use the same document ID as the in-progress document
        firestore_upsert(firestore_client, COLLECTION_NAME, completed_document, document_id=document_id)
        print(f"[DEBUG] Updated document with ID: {document_id} to completed status")

        print(f"[{document_id}] Successfully processed document content with {len(extracted_tables)} tables")
        return processing_results

    except Exception as exc:
        # Log failure status in Firestore
        if document_id:
            failed_document = Document.create_document(
                brd_workflow_id=brd_workflow_id,
                status=FunctionStatus.FAILED,
                description=f"Failed to process BRD content: {str(exc)}",
                description_heading="Content Processor Function",
                environment=get_environment_name(),
                error=str(exc)
            )
            # Use the same document ID as the in-progress document
            firestore_upsert(firestore_client, COLLECTION_NAME, failed_document, document_id=document_id)
            print(f"[DEBUG] Updated document with ID: {document_id} to failed status")
        
        print(f"[{document_id or 'unknown'}] ERROR: {exc}", file=sys.stderr)
        raise

# For direct HTTP requests
@functions_framework.http
def process_http_request(request):
    """HTTP request handler that delegates to the main content_processor function.
    
    Expects JSON payload with document_id.
    """
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return {"error": "Missing JSON payload"}, 400
        
        # Extract parameters from request
        document_id = request_json.get("document_id")
        brd_workflow_id = request_json.get("brd_workflow_id")  # Optional
        
        if not document_id:
            return {"error": "Missing required parameter: document_id"}, 400
        
        # Call the main function
        result = content_processor(
            document_id=document_id,
            brd_workflow_id=brd_workflow_id
        )
        
        return {"status": "success", "result": result}, 200
    
    except Exception as e:
        print(f"[ERROR] HTTP request processing failed: {e}")
        return {"error": str(e)}, 500

# For Pub/Sub backward compatibility (deprecated)
@functions_framework.cloud_event
def process_pub_sub_event(cloud_event):
    """Pub/Sub event handler - no longer supported, use HTTP endpoint instead."""
    try:
        return {"error": "Pub/Sub triggers are no longer supported. Use the HTTP endpoint."}, 400
    except Exception as e:
        print(f"[ERROR] Failed to process Pub/Sub event: {e}")
        return {"error": str(e)}, 400 