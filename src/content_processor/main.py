"""
content_processor – Cloud Function to process BRD content.

• Reads analyzed document data from BRD_ANALYSIS_TOPIC
• Processes and extracts tables and key content
• Logs execution metadata in Firestore
• Publishes processed content to BRD_CONTENT_TOPIC
"""

# Standard library imports
import json
import os
import sys
from datetime import datetime
from time import sleep

# Third-party imports
from dotenv import load_dotenv
import functions_framework
from google.cloud import firestore, pubsub_v1, storage

# Local imports - changing to relative imports
from .common.base import Document, FunctionStatus, DocumentType
from .common.firestore_utils import firestore_upsert
from .common import running_in_gcp, is_storage_emulator, get_environment_name, setup_emulator_environment

# Load dotenv for local development (ignored in prod)
load_dotenv()

# ── Config from env (all environment variables are required) ──────────────────
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
SOURCE_BUCKET = os.getenv("BRD_PROCESSED_BUCKET")
COLLECTION_NAME = os.getenv("METADATA_COLLECTION")
PUBSUB_TOPIC_NAME = os.getenv("TOPIC_BRD_READY_TO_PARSE")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID")

# Set up emulator environment if needed
setup_emulator_environment()

# ── Client initialization ──────────────────────────────────────────────────
storage_client = storage.Client()
pubsub_client = pubsub_v1.PublisherClient()
topic_path = pubsub_client.topic_path(PROJECT_ID, PUBSUB_TOPIC_NAME)
firestore_client = firestore.Client(project=PROJECT_ID)

# ── Main Cloud Function ─────────────────────────────────────────────────────
@functions_framework.cloud_event
def content_processor(cloud_event):
    start_time = datetime.utcnow()

    # Extract message data from Pub/Sub
    if cloud_event is None:  # local / unit-test
        brd_workflow_id = "mock_brd_id"
        document_id = "mock_document_id"
        analysis_results = {"size_bytes": 1000, "word_count": 200, "title": "Mock Document"}
    else:
        payload = cloud_event.data
        pubsub_message = json.loads(payload["message"]["data"])
        brd_workflow_id = pubsub_message.get("brd_workflow_id")
        document_id = pubsub_message.get("document_id")
        analysis_results = pubsub_message.get("analysis_results", {})
    
    print(f"[DEBUG] Starting content_processor for brd_workflow_id={brd_workflow_id}, document_id={document_id}")
    
    # # Get bucket and file name
    # src_bucket_name = SOURCE_BUCKET
    # src_file_name = f"{document_id}.html"  # Assuming HTML format
    
    # # Get the source bucket and blob
    # src_bucket = storage_client.bucket(src_bucket_name)
    # src_blob = src_bucket.blob(src_file_name)

    # # Update in progress status
    # environment = get_environment_name()
    # print(f"[DEBUG] Setting document environment to: {environment}")
    
    # inprogress_document = Document.create_function_execution(
    #     id=document_id,
    #     brd_workflow_id=brd_workflow_id,
    #     status=FunctionStatus.IN_PROGRESS,
    #     description="Processing BRD document content",
    #     description_heading="Content Processor Function",
    #     environment=environment
    # )
    # firestore_upsert(firestore_client, COLLECTION_NAME, inprogress_document)
    
    # try:
    #     # Download the document content
    #     document_content = src_blob.download_as_text()
        
    #     # Simulate content processing (tables extraction)
    #     # In a real implementation, this would do proper content extraction
    #     simulated_tables = [
    #         {"table_id": "table1", "title": "Requirements", "rows": 5, "columns": 3},
    #         {"table_id": "table2", "title": "Timeline", "rows": 3, "columns": 2}
    #     ]
        
    #     # Create processing results
    #     processing_results = {
    #         "document_id": document_id,
    #         "brd_workflow_id": brd_workflow_id,
    #         "timestamp": datetime.utcnow().isoformat() + "Z",
    #         "tables": simulated_tables,
    #         "title": analysis_results.get("title", "Unknown Document"),
    #         "tables_count": len(simulated_tables)
    #     }
        
    #     # Log success status
    #     completed_document = Document.create_function_execution(
    #         id=document_id,
    #         brd_workflow_id=brd_workflow_id,
    #         status=FunctionStatus.COMPLETED,
    #         description="Successfully processed BRD content",
    #         description_heading="Content Processor Function",
    #         environment=environment,
    #         processing_results=processing_results
    #     )
    #     firestore_upsert(firestore_client, COLLECTION_NAME, completed_document)

    #     # Publish processing results to Pub/Sub
    #     msg = {
    #         "brd_workflow_id": brd_workflow_id, 
    #         "document_id": document_id,
    #         "processing_complete": True,
    #         "processing_results": processing_results
    #     }
        
    #     print(f"[DEBUG] About to publish to Pub/Sub: topic_path={topic_path}, msg={msg}")
    #     try:
    #         pubsub_client.publish(topic_path, data=json.dumps(msg).encode()).result()
    #         print(f"[DEBUG] Published to Pub/Sub: topic_path={topic_path}, msg={msg}")
    #     except Exception as pubsub_exc:
    #         print(f"[ERROR] Failed to publish to Pub/Sub: {str(pubsub_exc)}", file=sys.stderr)
    #         raise  # Re-raise to be caught by outer try/except

    #     print(f"[{document_id}] Successfully processed document content with {len(simulated_tables)} tables")

    # except Exception as exc:
    #     # Log failure status
    #     failed_document = Document.create_function_execution(
    #         id=document_id,
    #         brd_workflow_id=brd_workflow_id,
    #         status=FunctionStatus.FAILED,
    #         description=f"Failed to process BRD content: {str(exc)}",
    #         description_heading="Content Processor Function",
    #         environment=environment,
    #         error=str(exc)
    #     )
    #     firestore_upsert(firestore_client, COLLECTION_NAME, failed_document)
    #     print(f"[{document_id}] ERROR: {exc}", file=sys.stderr)
    #     raise 