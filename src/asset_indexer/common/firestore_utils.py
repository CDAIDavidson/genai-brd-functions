"""
Firestore utilities for asset indexer functions.
"""

import sys
from typing import Dict, Any, Optional
from google.cloud import firestore
from .base import Document

def firestore_update(
    firestore_client: firestore.Client, 
    collection_name: str, 
    document_id: str, 
    item: Document
) -> str:
    """
    Insert or update a Firestore document.
    
    Args:
        firestore_client: Firestore client instance
        collection_name: Collection name to write to
        document_id: ID of the document to write
        item: Document instance to write
    
    Returns:
        The document ID
    """
    try:
        doc_data = item.to_dict()
        doc_ref = firestore_client.collection(collection_name).document(document_id)
        
        print(f"[DEBUG] Firestore write details:")
        print(f"[DEBUG] - Database: {firestore_client._database}")
        print(f"[DEBUG] - Project: {firestore_client.project}")
        print(f"[DEBUG] - Collection: {collection_name}")
        print(f"[DEBUG] - Document path: {doc_ref.path}")
        print(f"[DEBUG] - Document ID: {doc_ref.id}")
        print(f"[DEBUG] - Data: {doc_data}")
        
        doc_ref.set(doc_data, merge=True)
        print(f"[DEBUG] Successfully wrote to Firestore: {doc_ref.path}")
        
        # Read back for confirmation
        doc = doc_ref.get()
        print(f"[DEBUG] Read back doc: {doc.to_dict()}")
        
        db_id = firestore_client._database if firestore_client._database else 'default'
        if db_id == 'default':
            url = f"http://127.0.0.1:4000/firestore/default/data/{collection_name}/{doc_ref.id}"
        else:
            url = f"http://127.0.0.1:4000/firestore/data/{db_id}/{collection_name}/{doc_ref.id}"
        print(f"[DEBUG] View this document in the Emulator UI: {url}")
        
        return doc_ref.id
    except Exception as e:
        print(f"[ERROR] Failed to write to Firestore: {str(e)}", file=sys.stderr)
        raise 