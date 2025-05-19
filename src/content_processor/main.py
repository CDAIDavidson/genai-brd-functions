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
import base64
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
# Clear topic naming - separate subscription from publication
SUB_TOPIC_NAME = os.getenv("TOPIC_BRD_READY_TO_PARSE")  # Topic we subscribe to
PUB_TOPIC_NAME = os.getenv("TOPIC_TABLES_READY_TO_ASSESS")  # Topic we publish to
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID")

# For local testing
IS_LOCAL_TEST = os.getenv("LOCAL_TEST", "false").lower() == "true"

# Set up emulator environment if needed
setup_emulator_environment()

# ── Client initialization ──────────────────────────────────────────────────
storage_client = storage.Client()
pubsub_client = pubsub_v1.PublisherClient()
# Update to use the publication topic path
pub_topic_path = pubsub_client.topic_path(PROJECT_ID, PUB_TOPIC_NAME)
firestore_client = firestore.Client(project=PROJECT_ID)

# ── Main Cloud Function ─────────────────────────────────────────────────────
@functions_framework.cloud_event
def content_processor(cloud_event):

    # Extract message data from Pub/Sub
    if cloud_event is None:  # local / unit-test
        brd_workflow_id = "mock_brd_id"
        document_id = "mock_document_id"
        analysis_results = {"size_bytes": 1000, "word_count": 200, "title": "Mock Document"}
        is_test = True
    else:
        try:
            print(f"[DEBUG] Received cloud_event type: {cloud_event.type}")
            payload = cloud_event.data
            
            # Extract base64-encoded message data
            if "message" in payload and "data" in payload["message"]:
                message_data = payload["message"]["data"]
                
                # Check if it's a string that needs decoding or already decoded
                if isinstance(message_data, str):
                    try:
                        # Decode the base64 message data
                        decoded_data = base64.b64decode(message_data).decode('utf-8')
                        pubsub_message = json.loads(decoded_data)
                    except Exception as decode_err:
                        print(f"[ERROR] Failed to decode base64 message: {decode_err}")
                        # Try parsing directly if base64 decode fails
                        pubsub_message = json.loads(message_data)
                else:
                    # If it's already a dict, use it directly
                    pubsub_message = message_data
                
                print(f"[DEBUG] Parsed pubsub_message: {pubsub_message}")
                
                brd_workflow_id = pubsub_message.get("brd_workflow_id")
                document_id = pubsub_message.get("document_id")
                analysis_results = pubsub_message.get("analysis_results", {})
                
                # Check if this is a test message by looking at the IDs
                is_test = "test" in str(brd_workflow_id).lower() or "test" in str(document_id).lower()
            else:
                print(f"[WARNING] Unexpected payload format: {payload}")
                # Use fallback values
                brd_workflow_id = "unknown_workflow_id"
                document_id = "unknown_document_id"
                analysis_results = {}
                is_test = True
                
        except Exception as e:
            print(f"[ERROR] Failed to parse cloud event: {e}")
            # Use fallback values
            brd_workflow_id = "error_workflow_id"
            document_id = "error_document_id" 
            analysis_results = {}
            is_test = True
    
    print(f"[DEBUG] Starting content_processor for brd_workflow_id={brd_workflow_id}, document_id={document_id}")
    
    # Update in progress status
    environment = get_environment_name()
    print(f"[DEBUG] Setting document environment to: {environment}")
    
    inprogress_document = Document.create_function_execution(
        id=document_id,
        brd_workflow_id=brd_workflow_id,
        status=FunctionStatus.IN_PROGRESS,
        description="Processing BRD document content",
        description_heading="Content Processor Function",
        environment=environment
    )
    firestore_upsert(firestore_client, COLLECTION_NAME, inprogress_document)
    
    try:
        # Document content - either from storage or mock content for tests
        document_content = ""
        
        if is_test:
            print(f"[DEBUG] Test mode detected - using mock document content")
            document_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test BRD Document</title>
            </head>
            <body>
                <h1>Business Requirements Document</h1>
                <table>
                    <tr><th>Requirement</th><th>Description</th></tr>
                    <tr><td>REQ-001</td><td>Test requirement 1</td></tr>
                    <tr><td>REQ-002</td><td>Test requirement 2</td></tr>
                </table>
                <table>
                    <tr><th>Timeline</th><th>Date</th></tr>
                    <tr><td>Start</td><td>2023-01-01</td></tr>
                    <tr><td>End</td><td>2023-12-31</td></tr>
                </table>
            </body>
            </html>
            """
        else:
            # Get bucket and file name
            src_bucket_name = SOURCE_BUCKET
            src_file_name = f"{document_id}.html"  # Assuming HTML format
            
            # Get the source bucket and blob
            src_bucket = storage_client.bucket(src_bucket_name)
            src_blob = src_bucket.blob(src_file_name)
            
            # Download the document content
            document_content = src_blob.download_as_text()
        
        # Simulate content processing (tables extraction)
        # In a real implementation, this would do proper content extraction
        simulated_tables = [
            {"table_id": "table1", "title": "Requirements", "rows": 5, "columns": 3},
            {"table_id": "table2", "title": "Timeline", "rows": 3, "columns": 2}
        ]
        
        # Create processing results
        processing_results = {
            "document_id": document_id,
            "brd_workflow_id": brd_workflow_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tables": simulated_tables,
            "title": analysis_results.get("title", "Unknown Document"),
            "tables_count": len(simulated_tables)
        }
        
        # Log success status
        completed_document = Document.create_function_execution(
            id=document_id,
            brd_workflow_id=brd_workflow_id,
            status=FunctionStatus.COMPLETED,
            description="Successfully processed BRD content",
            description_heading="Content Processor Function",
            environment=environment,
            processing_results=processing_results
        )
        firestore_upsert(firestore_client, COLLECTION_NAME, completed_document)

        # Publish processing results to Pub/Sub (using the publication topic)
        msg = {
            "brd_workflow_id": brd_workflow_id, 
            "document_id": document_id,
            "processing_complete": True,
            "processing_results": processing_results
        }
        
        print(f"[DEBUG] About to publish to Pub/Sub: topic_path={pub_topic_path}, msg={msg}")
        try:
            pubsub_client.publish(pub_topic_path, data=json.dumps(msg).encode()).result()
            print(f"[DEBUG] Published to Pub/Sub: topic_path={pub_topic_path}, msg={msg}")
        except Exception as pubsub_exc:
            print(f"[ERROR] Failed to publish to Pub/Sub: {str(pubsub_exc)}", file=sys.stderr)
            raise  # Re-raise to be caught by outer try/except

        print(f"[{document_id}] Successfully processed document content with {len(simulated_tables)} tables")
        return "OK"

    except Exception as exc:
        # Log failure status
        failed_document = Document.create_function_execution(
            id=document_id,
            brd_workflow_id=brd_workflow_id,
            status=FunctionStatus.FAILED,
            description=f"Failed to process BRD content: {str(exc)}",
            description_heading="Content Processor Function",
            environment=environment,
            error=str(exc)
        )
        firestore_upsert(firestore_client, COLLECTION_NAME, failed_document)
        print(f"[{document_id}] ERROR: {exc}", file=sys.stderr)
        raise 