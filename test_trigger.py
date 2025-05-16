"""Test script to trigger the asset_indexer function locally"""
import os
from google.cloud import storage
from src.asset_indexer.main import asset_indexer

def create_test_event():
    """Create a test cloud event"""
    class CloudEvent:
        def __init__(self, data):
            self.data = data
    
    return CloudEvent({
        "bucket": os.getenv("DROP_FILE_BUCKET", "genai-brd-qi"),
        "name": "test.html"
    })

if __name__ == "__main__":
    # Upload test file to emulator
    storage_client = storage.Client()
    bucket = storage_client.bucket(os.getenv("DROP_FILE_BUCKET", "genai-brd-qi"))
    blob = bucket.blob("test.html")
    blob.upload_from_filename("test.html")
    print(f"Uploaded test.html to {bucket.name}")

    # Trigger function
    event = create_test_event()
    asset_indexer(event)
    print("Function executed successfully") 