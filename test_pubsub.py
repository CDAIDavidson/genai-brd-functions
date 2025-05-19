#!/usr/bin/env python3
"""
PubSub Emulator Test Script

This script tests the local Pub/Sub emulator by:
1. Creating a topic (if it doesn't exist)
2. Creating a subscription (if it doesn't exist)
3. Publishing a test message
4. Pulling the message to verify it was received
"""

import os
import json
import time
from google.cloud import pubsub_v1

# Set environment variables for emulator
os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"

# Project ID doesn't matter in emulator mode
PROJECT_ID = "test-project"
TOPIC_ID = "test-topic"
SUBSCRIPTION_ID = "test-subscription"

def setup_pubsub():
    """Create topic and subscription if they don't exist."""
    # Create publisher client
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    
    # Create topic if it doesn't exist
    try:
        publisher.get_topic(request={"topic": topic_path})
        print(f"Topic {topic_path} already exists")
    except Exception:
        topic = publisher.create_topic(request={"name": topic_path})
        print(f"Created topic: {topic.name}")
    
    # Create subscriber client
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    # Create subscription if it doesn't exist
    try:
        subscriber.get_subscription(request={"subscription": subscription_path})
        print(f"Subscription {subscription_path} already exists")
    except Exception:
        subscription = subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path}
        )
        print(f"Created subscription: {subscription.name}")
    
    return publisher, subscriber, topic_path, subscription_path

def publish_message(publisher, topic_path):
    """Publish a test message to the topic."""
    message = {
        "brd_workflow_id": "test-workflow-id",
        "document_id": "test-document-id",
        "timestamp": time.time()
    }
    data = json.dumps(message).encode("utf-8")
    future = publisher.publish(topic_path, data)
    message_id = future.result()
    print(f"Published message ID: {message_id}")
    print(f"Message content: {message}")
    return message

def pull_message(subscriber, subscription_path):
    """Pull messages from the subscription."""
    print("Pulling messages...")
    response = subscriber.pull(
        request={
            "subscription": subscription_path,
            "max_messages": 1,
        }
    )
    
    if not response.received_messages:
        print("No messages received.")
        return None
    
    for msg in response.received_messages:
        print(f"Received message ID: {msg.message.message_id}")
        data = json.loads(msg.message.data.decode("utf-8"))
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
    
    return None

def main():
    print("Testing Pub/Sub emulator...")
    
    # Setup
    publisher, subscriber, topic_path, subscription_path = setup_pubsub()
    
    # Publish a message
    sent_message = publish_message(publisher, topic_path)
    
    # Give some time for the message to be processed
    print("Waiting for message to be processed...")
    time.sleep(2)
    
    # Pull the message
    received_message = pull_message(subscriber, subscription_path)
    
    # Verify the test
    if received_message:
        if received_message["brd_workflow_id"] == sent_message["brd_workflow_id"]:
            print("✅ TEST PASSED: Message was successfully published and received!")
        else:
            print("❌ TEST FAILED: Received message doesn't match the sent message.")
    else:
        print("❌ TEST FAILED: No message was received.")
    
    # Clean up
    subscriber.close()

if __name__ == "__main__":
    main() 