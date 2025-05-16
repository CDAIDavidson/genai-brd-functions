import admin from 'firebase-admin';

// Set the Firestore emulator host
process.env.FIRESTORE_EMULATOR_HOST = 'localhost:8090';

// Initialize Firebase Admin SDK
admin.initializeApp();

// Get Firestore instance
const db = admin.firestore();

// Add a dummy document to the root 'metadata' collection
async function addDummyDoc() {
  const docRef = db.collection('metadata').doc('dummy-root-id');
  await docRef.set({
    brd_workflow_id: '2860bea37e',
    id: 'dummy-root-id',
    status: 'test',
    created_at: new Date().toISOString(),
    note: 'This is a dummy document at the root of the metadata collection.'
  });
  console.log('Dummy document written to Firestore emulator!');
}

addDummyDoc().catch(console.error); 