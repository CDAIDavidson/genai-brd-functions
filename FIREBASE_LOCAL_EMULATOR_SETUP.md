# Firebase Local Emulator Setup

This document explains how local Firebase emulation is set up for this project, including environment variables, emulator startup, and how both Python and Node.js scripts connect to the emulator.

---

## 1. Prerequisites
- [Node.js](https://nodejs.org/)
- [Firebase CLI](https://firebase.google.com/docs/cli) (`npm install -g firebase-tools`)
- Python 3.x (for Python functions)

---

## 2. Environment Variables

The following environment variables are required for the code to connect to the local emulators:

| Variable                        | Purpose                                 | Example Value         |
|----------------------------------|-----------------------------------------|----------------------|
| `FIRESTORE_EMULATOR_HOST`        | Firestore emulator host/port            | `127.0.0.1:8090`     |
| `FIREBASE_STORAGE_EMULATOR_HOST` | Storage emulator host/port              | `127.0.0.1:9199`     |
| `FUNCTIONS_EMULATOR`             | Indicates functions are running locally | `true`               |
| `GOOGLE_CLOUD_PROJECT`           | Project ID                              | `genai-brd-qi`       |
| `FIRESTORE_DATABASE_ID`          | Firestore database ID                   | `default`            |
| `METADATA_COLLECTION`            | Firestore collection name               | `metadata`           |
| `DROP_BRD_BUCKET`                | Source bucket name                      | `genai-brd-qi`       |
| `BRD_PROCESSED_BUCKET`           | Destination bucket name                 | `genai-brd-qi`       |
| `DOC_INDEX_TOPIC`                | Pub/Sub topic name                      | `document-indexer`   |

- All variables are required with no default values.
- These must be set in your `.env` file or via scripts (e.g., `asset_indexer_run_local.ps1`).

---

## 3. Starting the Emulator Suite

From the root of your Firebase project (where `firebase.json` is located), run:

```sh
firebase emulators:start --project genai-brd-qi
```

Or use your provided batch script (if available):

```sh
./Z_install_dev_deploy/development/start-emulators.bat
```

This will start the following emulators:
- Firestore (port 8090)
- Storage (port 9199)
- Functions (port 5001)
- Pub/Sub (port 8085)
- Authentication (port 9099)
- Emulator UI (port 4000)

Access the Emulator UI at: [http://127.0.0.1:4000](http://127.0.0.1:4000)

---

## 4. Python Function Setup

- The Python function (`src/asset_indexer/main.py`) loads environment variables from `.env` (or `.env.example` for reference).
- It connects to the Firestore emulator using the `FIRESTORE_EMULATOR_HOST` variable.
- The Firestore client is initialized as:
  ```python
  firestore_client = firestore.Client(project=PROJECT_ID)
  ```
- The collection name is set by:
  ```python
  COLLECTION_NAME = os.getenv("METADATA_COLLECTION")
  ```
- All environment variables are required with no default values.

---

## 5. Node.js Script Setup

- The Node.js script (`create_firestore_dummy_doc.js`) sets the emulator host:
  ```js
  process.env.FIRESTORE_EMULATOR_HOST = 'localhost:8090';
  ```
- It uses the Firebase Admin SDK, which automatically connects to the emulator if the env var is set.
- Documents are written to the `metadata` collection in the `default` database.

---

## 6. Troubleshooting
- If you do not see documents in the Emulator UI, ensure:
  - The correct database is selected (`default` by default).
  - The collection name matches (`metadata`).
  - The emulator is running and ports are not blocked.
  - Environment variables are loaded (check `.env` vs `.env.example`).
- For Python, ensure `.env` (not just `.env.example`) exists and is loaded.

---

## 7. References
- [Firebase Emulator Suite Docs](https://firebase.google.com/docs/emulator-suite)
- [Google Cloud Firestore Emulator](https://cloud.google.com/sdk/gcloud/reference/beta/emulators/firestore/) 