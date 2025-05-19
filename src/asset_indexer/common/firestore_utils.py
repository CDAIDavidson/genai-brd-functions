# """
# Firestore utilities for asset indexer functions.
# """

# import sys
# from typing import Dict, Any, Optional
# from google.cloud import firestore
# from .base import Document

# def firestore_update(
#     firestore_client: firestore.Client, 
#     collection_name: str, 
#     document_id: str, 
#     item: Document
# ) -> str:
#     """
#     Insert or update a Firestore document.
    
#     Args:
#         firestore_client: Firestore client instance
#         collection_name: Collection name to write to
#         document_id: ID of the document to write
#         item: Document instance to write
    
#     Returns:
#         The document ID
#     """
#     try:
#         doc_data = item.to_dict()
#         doc_ref = firestore_client.collection(collection_name).document(document_id)
        
#         print(f"[DEBUG] Firestore write details:")
#         print(f"[DEBUG] - Database: {firestore_client._database}")
#         print(f"[DEBUG] - Project: {firestore_client.project}")
#         print(f"[DEBUG] - Collection: {collection_name}")
#         print(f"[DEBUG] - Document path: {doc_ref.path}")
#         print(f"[DEBUG] - Document ID: {doc_ref.id}")
#         print(f"[DEBUG] - Data: {doc_data}")
        
#         doc_ref.   set(doc_data, merge=True)
#         print(f"[DEBUG] Successfully wrote to Firestore: {doc_ref.path}")
        
        
#         # Read back for confirmation
#         doc = doc_ref.get()
#         print(f"[DEBUG] Read back doc: {doc.to_dict()}")
        
#         db_id = firestore_client._database if firestore_client._database else 'default'
#         if db_id == 'default':
#             url = f"http://127.0.0.1:4000/firestore/default/data/{collection_name}/{doc_ref.id}"
#         else:
#             url = f"http://127.0.0.1:4000/firestore/data/{db_id}/{collection_name}/{doc_ref.id}"
#         print(f"[DEBUG] View this document in the Emulator UI: {url}")
        
#         return doc_ref.id
#     except Exception as e:
#         print(f"[ERROR] Failed to write to Firestore: {str(e)}", file=sys.stderr)
#         raise 





# #     method) def set(
# #     document_data: dict,
# #     merge: bool = False,
# #     retry: Retry = gapic_v1.method.DEFAULT,
# #     timeout: float = None
# # ) -> WriteResult
# # Create / replace / merge a document in the Firestore database.

# # To "upsert" a document (create if it doesn't exist, replace completely if it does), leave the merge argument at its default:
# # >>> document_data = {"a": 1, "b": {"c": "Two"}}
# # >>> document.get().to_dict() is None  # document exists
# # False
# # >>> document.set(document_data)
# # >>> document.get().to_dict() == document_data  # exists
# # True
# # To "merge" document_data with an existing document (creating if the document does not exist), pass merge as True`:
# # >>> document_data = {"a": 1, "b": {"c": "Two"}}
# # >>> document.get().to_dict() == {"d": "Three", "b": {}} # exists
# # >>> document.set(document_data, merge=True)
# # >>> document.get().to_dict() == {"a": 1, "d": "Three", "b": {"c": "Two"}}
# # True
# #   In this case, existing documents with top-level keys which are not present in document_data ("d") will preserve the values of those keys.

# # To merge only specific fields of document_data with existing documents (creating if the document does not exist), pass merge as a list of field paths:
# # >>> document_data = {"a": 1, "b": {"c": "Two"}}
# # >>> document.get().to_dict() == {"b": {"c": "One", "d": "Four" }} # exists
# # True
# # >>> document.set(document_data, merge=["b.c"])
# # >>> document.get().to_dict() == {"b": {"c": "Two", "d": "Four" }}
# # True
# #   For more information on field paths, see
# #   ~google.cloud.firestore_v1.base_client.BaseClient.field_path.

# # Args:
# #     document_data (dict): Property names and values to use for
# #         replacing a document.
# #     merge (Optional[bool] or Optional[List<fieldpath>]):
# #         If True, apply merging instead of overwriting the state of the document.
# #     retry (google.api_core.retry.Retry): Designation of what errors, if any,
# #         should be retried. Defaults to a system-specified policy.
# #     timeout (float): The timeout for this request. Defaults to a
# #         system-specified value.

# # Returns:
# #     ~google.cloud.firestore_v1.types.WriteResult: The write result corresponding to the committed document. A write result contains an update_time field.