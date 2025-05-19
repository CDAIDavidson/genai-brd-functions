#!/usr/bin/env python3
"""
Project-specific PubSub Emulator Test Script

Tests the communication between asset_indexer and content_processor
by publishing a message to TOPIC_BRD_READY_TO_PARSE and setting up 
a subscription to receive and verify the message.
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
TOPIC_NAME = os.getenv("TOPIC_BRD_READY_TO_PARSE")
SUBSCRIPTION_ID = f"{TOPIC_NAME}-test-sub"

print(f"Testing with: PROJECT_ID={PROJECT_ID}, TOPIC={TOPIC_NAME}")

def setup_pubsub():
    """Set up publisher, subscriber, and subscription for testing."""
    # Create publisher client
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
    
    # Check if topic exists (should have been created by the emulator or previous runs)
    try:
        publisher.get_topic(request={"topic": topic_path})
        print(f"Topic {topic_path} exists")
    except Exception as e:
        print(f"Error checking topic: {e}")
        try:
            topic = publisher.create_topic(request={"name": topic_path})
            print(f"Created topic: {topic.name}")
        except Exception as e:
            print(f"Failed to create topic: {e}")
            return None, None, None, None
    
    # Create subscriber client
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    # Create subscription if it doesn't exist
    try:
        subscriber.get_subscription(request={"subscription": subscription_path})
        print(f"Subscription {subscription_path} exists")
    except Exception:
        try:
            subscription = subscriber.create_subscription(
                request={"name": subscription_path, "topic": topic_path}
            )
            print(f"Created subscription: {subscription.name}")
        except Exception as e:
            print(f"Failed to create subscription: {e}")
            return publisher, None, topic_path, None
    
    return publisher, subscriber, topic_path, subscription_path

def publish_test_message(publisher, topic_path):
    """Publish a test message that mimics the asset_indexer's message."""
    brd_id = "test-brd-id-123"
    message = {
        "brd_workflow_id": brd_id, 
        "document_id": brd_id
    }
    
    print(f"Preparing to publish message: {message}")
    data = json.dumps(message).encode("utf-8")
    
    try:
        future = publisher.publish(topic_path, data)
        message_id = future.result()
        print(f"Published message ID: {message_id}")
        return message
    except Exception as e:
        print(f"Failed to publish message: {e}")
        return None

def receive_messages(subscriber, subscription_path, timeout=10):
    """Receive messages from the subscription with a timeout."""
    if not subscriber or not subscription_path:
        print("Subscriber or subscription path is None, cannot receive messages")
        return None
    
    print(f"Pulling messages from {subscription_path}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = subscriber.pull(
                request={
                    "subscription": subscription_path,
                    "max_messages": 5,
                }
            )
            
            if response.received_messages:
                for msg in response.received_messages:
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
            
            print("No messages received yet, waiting...")
            time.sleep(2)
            
        except Exception as e:
            print(f"Error pulling messages: {e}")
            return None
    
    print(f"Timeout after {timeout} seconds, no messages received.")
    return None

def main():
    print("\n=== Testing Pub/Sub communication for BRD workflow ===")
    
    # Setup publisher and subscriber
    publisher, subscriber, topic_path, subscription_path = setup_pubsub()
    
    if not publisher or not topic_path:
        print("Failed to set up publisher or topic, exiting.")
        return
    
    # Publish a test message mimicking asset_indexer
    sent_message = publish_test_message(publisher, topic_path)
    
    if not sent_message:
        print("Failed to publish message, exiting.")
        return
    
    # Try to receive the message
    if subscriber and subscription_path:
        print("\nWaiting for message to be received...")
        received_message = receive_messages(subscriber, subscription_path)
        
        # Test verification
        if received_message:
            if received_message["brd_workflow_id"] == sent_message["brd_workflow_id"]:
                print("\n✅ SUCCESS: Message successfully published and received!")
                print("This confirms that Pub/Sub emulator is working correctly.")
                print("The connection between asset_indexer and content_processor should work.")
            else:
                print("\n❌ FAILURE: Received message doesn't match the sent message.")
        else:
            print("\n❌ FAILURE: No message was received.")
            print("Possible issues:")
            print("1. Pub/Sub emulator may not be working correctly")
            print("2. The topic might not be configured properly")
            print("3. Network or permission issues")
    else:
        print("\nSkipping message reception due to setup issues.")
    
    # Clean up
    if subscriber:
        subscriber.close()
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main() 