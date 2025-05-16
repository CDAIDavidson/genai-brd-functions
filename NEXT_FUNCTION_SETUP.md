# Next Function Setup: Pub/Sub Subscriber and Firestore Writer

This document explains how to set up the next function in your local Firebase emulator environment. This function will:
- Subscribe to the Pub/Sub topic published by `main.py` (e.g., `document-indexer`)
- Write a new document to Firestore
- Update an existing Firestore document

---

## 1. Prerequisites
- Firebase Emulator Suite running (see `FIREBASE_LOCAL_EMULATOR_SETUP.md`)
- Node.js or Python (depending on your function language)
- Pub/Sub and Firestore emulators must be enabled

---

## 2. Environment Variables
Ensure the following environment variables are set (in your `.env` file or via your run script):

| Variable                        | Purpose                                 | Example Value         |
|----------------------------------|-----------------------------------------|----------------------|
| `FIRESTORE_EMULATOR_HOST`        | Firestore emulator host/port            | `127.0.0.1:8090`     |
| `GOOGLE_CLOUD_PROJECT`           | Project ID                              | `genai-brd-qi`       |
| `FIRESTORE_DATABASE_ID`          | Firestore database (usually `default`)  | `default`            |
| `PUBSUB_EMULATOR_HOST`           | Pub/Sub emulator host/port              | `127.0.0.1:8085`     |
| `METADATA_COLLECTION`            | Firestore collection name               | `metadata`           |
| `DOC_INDEX_TOPIC`                | Pub/Sub topic name                      | `document-indexer`   |

---

## 3. High-Level Flow
1. **Subscribe to Pub/Sub Topic:**
   - The function listens to the topic (e.g., `document-indexer`) published by `main.py`.
2. **Process Incoming Message:**
   - The message contains at least `brd_workflow_id` and `document_id`.
3. **Write a New Firestore Document:**
   - Create a new document in the `metadata` collection (or another collection as needed).
4. **Update an Existing Firestore Document:**
   - Use the `brd_workflow_id` or `document_id` to find and update an existing document in Firestore.

---

## 4. Example (Node.js)

```js
import { PubSub } from '@google-cloud/pubsub';
import admin from 'firebase-admin';

process.env.FIRESTORE_EMULATOR_HOST = 'localhost:8090';
process.env.PUBSUB_EMULATOR_HOST = 'localhost:8085';

admin.initializeApp();
const db = admin.firestore();
const pubsub = new PubSub({ projectId: process.env.GOOGLE_CLOUD_PROJECT });

const subscriptionName = 'document-indexer-sub';
const topicName = process.env.DOC_INDEX_TOPIC || 'document-indexer';

async function listenForMessages() {
  const [subscription] = await pubsub.topic(topicName).createSubscription(subscriptionName).catch(async err => {
    if (err.code === 6) {
      // Already exists
      return [pubsub.subscription(subscriptionName)];
    }
    throw err;
  });

  subscription.on('message', async message => {
    const data = JSON.parse(message.data.toString());
    // Write a new document
    await db.collection('metadata').add({ received: true, ...data });
    // Update an existing document
    await db.collection('metadata').doc(data.brd_workflow_id).set({ processed: true }, { merge: true });
    message.ack();
    console.log('Processed message:', data);
  });
}

listenForMessages();
```

---

## 5. Example (Python)

> **Note:** The Python Pub/Sub emulator client is less mature than Node.js. You may need to use the `google-cloud-pubsub` library and set `PUBSUB_EMULATOR_HOST`.

---

## 6. Testing
- Publish a message to the topic (triggered by `main.py` or manually)
- Confirm the new and updated documents appear in Firestore Emulator UI

---

## 7. References
- [Firebase Emulator Suite Docs](https://firebase.google.com/docs/emulator-suite)
- [Google Cloud Pub/Sub Emulator](https://cloud.google.com/pubsub/docs/emulator)
- [Firestore Python Client](https://googleapis.dev/python/firestore/latest/index.html)
- [Firestore Node.js Client](https://googleapis.dev/nodejs/firestore/latest/index.html) 