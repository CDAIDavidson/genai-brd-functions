from google.cloud import firestore
import os

# Point to the Firestore emulator
os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8090"

# Use the same project and database as your function
PROJECT_ID = "genai-brd-qi"
DATABASE_ID = "default"

# Initialize Firestore client
client = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

print(f"Listing documents in 'metadata' collection (project: {PROJECT_ID}, database: {DATABASE_ID})...")
docs = client.collection("metadata").stream()
found = False
for doc in docs:
    found = True
    print(f"{doc.id}: {doc.to_dict()}")
if not found:
    print("No documents found in 'metadata' collection.") 