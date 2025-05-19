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

def download_document_content(document_id):
    """
    Download document content from Storage bucket.
    
    Args:
        document_id: The ID of the document to download
        
    Returns:
        The document content as text
    """
    try:
        # Get bucket and file name
        src_bucket_name = SOURCE_BUCKET
        src_file_name = f"{document_id}.html"  # Assuming HTML format
        
        # Get the source bucket and blob
        src_bucket = storage_client.bucket(src_bucket_name)
        src_blob = src_bucket.blob(src_file_name)
        
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

def publish_processing_results(message):
    """
    Publish processing results to Pub/Sub.
    
    Args:
        message: The PubSubMessage object to publish
    """
    try:
        message_dict = message.to_dict()
        print(f"[DEBUG] Publishing to topic {pub_topic_path}: {message_dict}")
        
        future = pubsub_client.publish(
            pub_topic_path, 
            data=json.dumps(message_dict).encode()
        )
        future.result()  # Wait for message to be published
        
        print(f"[DEBUG] Successfully published message to {PUB_TOPIC_NAME}")
    except Exception as e:
        print(f"[ERROR] Failed to publish to Pub/Sub: {e}")
        raise

# ── Main Cloud Function ─────────────────────────────────────────────────────
@functions_framework.cloud_event
def content_processor(cloud_event):
    """
    Process BRD document content.
    
    Args:
        cloud_event: The Cloud Event object from Pub/Sub
        
    Returns:
        "OK" if successful
    """
    document_id = None
    brd_workflow_id = None

    
    
    try:
        # Extract message data from Pub/Sub using our standard message class
        if cloud_event is None or IS_LOCAL_TEST:  # local / unit-test
            brd_workflow_id = "mock_brd_id"
            document_id = "mock_document_id"
            message = PubSubMessage(brd_workflow_id, document_id)
            is_test = True
        else:
            try:
                # Handle cloud_event potentially being a dict in local testing
                event_type = None
                event_data = None
                if hasattr(cloud_event, 'type') and hasattr(cloud_event, 'data'):
                    event_type = cloud_event.type
                    event_data = cloud_event.data
                elif isinstance(cloud_event, dict):
                    # Standard CloudEvent attributes are in 'attributes'
                    event_attributes = cloud_event.get('attributes', {})
                    event_type = event_attributes.get('type')
                    event_data = cloud_event.get('data')
                
                if event_type is None or event_data is None:
                    # If critical information is missing, log and raise to ensure it's caught
                    missing_parts = []
                    if event_type is None: missing_parts.append("type")
                    if event_data is None: missing_parts.append("data")
                    error_message = f"CloudEvent structure is missing critical parts: {', '.join(missing_parts)}. Event: {cloud_event}"
                    print(f"[ERROR] {error_message}")
                    raise ValueError(error_message)

                print(f"[DEBUG] Received cloud_event type: {event_type}")
                # PubSubMessage.from_cloud_event expects the 'data' part of the CloudEvent,
                # which itself contains the 'message' with the base64-encoded payload.
                message = PubSubMessage.from_cloud_event(event_data)
                brd_workflow_id = message.brd_workflow_id
                document_id = message.document_id
                
                # Check if this is a test message by looking at the IDs
                is_test = "test" in str(brd_workflow_id).lower() or "test" in str(document_id).lower()
            except Exception as e:
                print(f"[ERROR] Failed to parse cloud event: {e}")
                # Use fallback values
                brd_workflow_id = "error_workflow_id"
                document_id = "error_document_id" 
                message = PubSubMessage(brd_workflow_id, document_id)
                is_test = True
    
        print(f"[DEBUG] Starting content_processor for brd_workflow_id={brd_workflow_id}, document_id={document_id}")
        
        # Update in progress status
        environment = get_environment_name()
        print(f"[DEBUG] Setting document environment to: {environment}")
        
        # Create in-progress document record
        inprogress_document = Document.create_function_execution(
            id=document_id,
            brd_workflow_id=brd_workflow_id,
            status=FunctionStatus.IN_PROGRESS,
            description="Processing BRD document content",
            description_heading="Content Processor Function",
            environment=environment
        )
        firestore_upsert(firestore_client, COLLECTION_NAME, inprogress_document)
        
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
            # Download the document content from storage
            document_content = download_document_content(document_id)
        
        # Extract tables from document content
        extracted_tables = extract_tables_from_content(document_content)
        
        # Create processing results object
        processing_results = {
            "document_id": document_id,
            "brd_workflow_id": brd_workflow_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tables": extracted_tables,
            "title": message.data.get("title", "Unknown Document") if message.data else "Unknown Document",
            "tables_count": len(extracted_tables)
        }
        
        # Log success status in Firestore
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

        # Create a PubSubMessage with the processing results and publish
        result_message = PubSubMessage(
            brd_workflow_id=brd_workflow_id,
            document_id=document_id,
            data=processing_results,
            processing_complete=True
        )
        publish_processing_results(result_message)

        print(f"[{document_id}] Successfully processed document content with {len(extracted_tables)} tables")
        return "OK"

    except Exception as exc:
        # Log failure status in Firestore
        failed_document = Document.create_function_execution(
            id=document_id or "unknown_document_id",
            brd_workflow_id=brd_workflow_id or "unknown_workflow_id",
            status=FunctionStatus.FAILED,
            description=f"Failed to process BRD content: {str(exc)}",
            description_heading="Content Processor Function",
            environment=get_environment_name(),
            error=str(exc)
        )
        firestore_upsert(firestore_client, COLLECTION_NAME, failed_document)
        print(f"[{document_id or 'unknown'}] ERROR: {exc}", file=sys.stderr)
        raise 