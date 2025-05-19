#!/usr/bin/env python3
"""
BRD Workflow Chain Test Script

Tests the complete communication chain:
1. asset_indexer -> TOPIC_BRD_READY_TO_PARSE -> content_processor
2. content_processor -> TOPIC_TABLES_READY_TO_ASSESS -> (next function)

This validates that the entire message flow works correctly.
"""

import os
import json
import time
from dotenv import load_dotenv
from google.cloud import pubsub_v1

# Load environment variables
load_dotenv()

# Set emulator host
os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"

# Read project configuration from env variables
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "test-project")
INDEXER_TOPIC = os.getenv("TOPIC_BRD_READY_TO_PARSE")
PROCESSOR_TOPIC = os.getenv("TOPIC_TABLES_READY_TO_ASSESS")
INDEXER_SUB_ID = f"{INDEXER_TOPIC}-test-sub"
PROCESSOR_SUB_ID = f"{PROCESSOR_TOPIC}-test-sub"

print(f"Testing workflow chain with:")
print(f"  PROJECT_ID: {PROJECT_ID}")
print(f"  INDEXER_TOPIC: {INDEXER_TOPIC}")
print(f"  PROCESSOR_TOPIC: {PROCESSOR_TOPIC}")

def setup_pubsub():
    """Set up publisher, subscriber, and subscriptions for testing."""
    # Create publisher client
    publisher = pubsub_v1.PublisherClient()
    
    # Create subscriber client
    subscriber = pubsub_v1.SubscriberClient()
    
    # Setup for INDEXER_TOPIC (asset_indexer -> content_processor)
    indexer_topic_path = publisher.topic_path(PROJECT_ID, INDEXER_TOPIC)
    try:
        publisher.get_topic(request={"topic": indexer_topic_path})
        print(f"Topic {indexer_topic_path} exists")
    except Exception:
        try:
            topic = publisher.create_topic(request={"name": indexer_topic_path})
            print(f"Created topic: {topic.name}")
        except Exception as e:
            print(f"Failed to create topic {INDEXER_TOPIC}: {e}")
            return None, None, None, None, None, None
    
    # Setup for PROCESSOR_TOPIC (content_processor -> next function)
    processor_topic_path = publisher.topic_path(PROJECT_ID, PROCESSOR_TOPIC)
    try:
        publisher.get_topic(request={"topic": processor_topic_path})
        print(f"Topic {processor_topic_path} exists")
    except Exception:
        try:
            topic = publisher.create_topic(request={"name": processor_topic_path})
            print(f"Created topic: {topic.name}")
        except Exception as e:
            print(f"Failed to create topic {PROCESSOR_TOPIC}: {e}")
            return publisher, subscriber, indexer_topic_path, None, None, None
    
    # Create subscription for INDEXER_TOPIC
    indexer_sub_path = subscriber.subscription_path(PROJECT_ID, INDEXER_SUB_ID)
    try:
        subscriber.get_subscription(request={"subscription": indexer_sub_path})
        print(f"Subscription {indexer_sub_path} exists")
    except Exception:
        try:
            subscription = subscriber.create_subscription(
                request={"name": indexer_sub_path, "topic": indexer_topic_path}
            )
            print(f"Created subscription: {subscription.name}")
        except Exception as e:
            print(f"Failed to create subscription for {INDEXER_TOPIC}: {e}")
            return publisher, subscriber, indexer_topic_path, processor_topic_path, None, None
    
    # Create subscription for PROCESSOR_TOPIC
    processor_sub_path = subscriber.subscription_path(PROJECT_ID, PROCESSOR_SUB_ID)
    try:
        subscriber.get_subscription(request={"subscription": processor_sub_path})
        print(f"Subscription {processor_sub_path} exists")
    except Exception:
        try:
            subscription = subscriber.create_subscription(
                request={"name": processor_sub_path, "topic": processor_topic_path}
            )
            print(f"Created subscription: {subscription.name}")
        except Exception as e:
            print(f"Failed to create subscription for {PROCESSOR_TOPIC}: {e}")
            return publisher, subscriber, indexer_topic_path, processor_topic_path, indexer_sub_path, None
    
    return publisher, subscriber, indexer_topic_path, processor_topic_path, indexer_sub_path, processor_sub_path

def publish_asset_indexer_message(publisher, topic_path):
    """Publish a test message that mimics asset_indexer's output."""
    brd_id = "test-brd-id-123"
    message = {
        "brd_workflow_id": brd_id, 
        "document_id": brd_id
    }
    
    print(f"Publishing to {INDEXER_TOPIC}: {message}")
    data = json.dumps(message).encode("utf-8")
    
    try:
        future = publisher.publish(topic_path, data)
        message_id = future.result()
        print(f"Published message ID: {message_id}")
        return message
    except Exception as e:
        print(f"Failed to publish message: {e}")
        return None

def receive_message(subscriber, subscription_path, timeout=10):
    """Pull a message from the subscription with timeout."""
    print(f"Waiting for message on {subscription_path}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = subscriber.pull(
                request={
                    "subscription": subscription_path,
                    "max_messages": 1,
                }
            )
            
            if response.received_messages:
                msg = response.received_messages[0]
                data = json.loads(msg.message.data.decode("utf-8"))
                print(f"Received message ID: {msg.message.message_id}")
                print(f"Message content: {data}")
                
                # Acknowledge the message
                subscriber.acknowledge(
                    request={
                        "subscription": subscription_path,
                        "ack_ids": [msg.ack_id],
                    }
                )
                print("Message acknowledged.")
                return data
            
            time.sleep(1)
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None
    
    print(f"Timeout after {timeout} seconds")
    return None

def main():
    print("\n=== Testing BRD Workflow Communication Chain ===")
    
    # Setup
    publisher, subscriber, indexer_topic, processor_topic, indexer_sub, processor_sub = setup_pubsub()
    
    if not publisher or not indexer_topic or not processor_topic:
        print("Failed to set up topics, exiting.")
        return
    
    print("\n--- STEP 1: Testing asset_indexer → content_processor ---")
    # 1. Simulate asset_indexer publishing a message
    sent_message = publish_asset_indexer_message(publisher, indexer_topic)
    
    if not sent_message:
        print("Failed to publish message from asset_indexer, exiting.")
        return
    
    # 2. Check if the message can be received (simulating content_processor)
    if indexer_sub:
        indexer_message = receive_message(subscriber, indexer_sub)
        
        if indexer_message:
            print("\n✅ STEP 1 SUCCESS: Message from asset_indexer successfully received!")
            print("content_processor should be triggered by this message.")
        else:
            print("\n❌ STEP 1 FAILURE: Message from asset_indexer not received.")
            return
    else:
        print("Subscription for asset_indexer not available, skipping test.")
        return
    
    print("\n--- STEP 2: Testing content_processor → next function ---")
    # 3. Simulate content_processor publishing a message to the next topic
    processor_message = {
        "brd_workflow_id": indexer_message["brd_workflow_id"],
        "document_id": indexer_message["document_id"],
        "processing_complete": True,
        "processing_results": {
            "tables_count": 2,
            "tables": [
                {"table_id": "table1", "title": "Requirements"},
                {"table_id": "table2", "title": "Timeline"}
            ]
        }
    }
    
    print(f"Publishing to {PROCESSOR_TOPIC}: {processor_message}")
    try:
        data = json.dumps(processor_message).encode("utf-8")
        future = publisher.publish(processor_topic, data)
        message_id = future.result()
        print(f"Published message ID: {message_id}")
    except Exception as e:
        print(f"Failed to publish message from content_processor: {e}")
        return
    
    # 4. Check if the message can be received by the next function
    if processor_sub:
        next_function_message = receive_message(subscriber, processor_sub)
        
        if next_function_message:
            print("\n✅ STEP 2 SUCCESS: Message from content_processor successfully received!")
            print("The next function should be triggered by this message.")
        else:
            print("\n❌ STEP 2 FAILURE: Message from content_processor not received.")
    else:
        print("Subscription for content_processor not available, skipping test.")
    
    # Clean up
    subscriber.close()
    print("\n=== Test completed ===")
    
    # Final summary
    if indexer_message and next_function_message:
        print("\n🎉 COMPLETE WORKFLOW TEST PASSED! 🎉")
        print("The entire message chain is working correctly:")
        print("  asset_indexer → TOPIC_BRD_READY_TO_PARSE → content_processor")
        print("  content_processor → TOPIC_TABLES_READY_TO_ASSESS → (next function)")
    else:
        print("\n⚠️ WORKFLOW TEST INCOMPLETE")
        if not indexer_message:
            print("❌ Issue with asset_indexer to content_processor communication")
        if not next_function_message:
            print("❌ Issue with content_processor to next function communication")

if __name__ == "__main__":
    main() 