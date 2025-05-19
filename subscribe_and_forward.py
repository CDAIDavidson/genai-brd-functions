#!/usr/bin/env python3
"""
Pub/Sub Subscriber and Forwarder

This script:
1. Subscribes to the TOPIC_BRD_READY_TO_PARSE topic
2. Listens for messages from asset_indexer
3. Forwards them as CloudEvents to the locally running content_processor function
"""

import os
import json
import uuid
import base64
import time
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import pubsub_v1

# Load environment variables
load_dotenv()

# Configure settings
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "genai-brd-qi")
TOPIC_NAME = os.getenv("TOPIC_BRD_READY_TO_PARSE", "brd-ready-to-parse") 
SUBSCRIPTION_NAME = f"{TOPIC_NAME}-local-forwarder"
FUNCTION_URL = "http://localhost:8083"  # Local content_processor endpoint

# Set emulator host
os.environ["PUBSUB_EMULATOR_HOST"] = "localhost:8085"

print(f"Starting Pub/Sub subscriber for {PROJECT_ID}/{TOPIC_NAME}")
print(f"Will forward messages to {FUNCTION_URL}")

def setup_subscription():
    """Create a subscription to the topic if it doesn't exist."""
    try:
        subscriber = pubsub_v1.SubscriberClient()
        publisher = pubsub_v1.PublisherClient()
        
        # Make sure topic exists
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
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
                return None
        
        subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
        
        # Check if subscription exists
        try:
            subscriber.get_subscription(request={"subscription": subscription_path})
            print(f"Using existing subscription: {subscription_path}")
        except Exception:
            try:
                subscription = subscriber.create_subscription(
                    request={"name": subscription_path, "topic": topic_path}
                )
                print(f"Created subscription: {subscription.name}")
            except Exception as e:
                print(f"Error creating subscription: {e}")
                return None
        
        return subscription_path
    except Exception as e:
        print(f"Failed to set up subscription: {e}")
        return None

def create_cloud_event(message_data, message_id):
    """Create a CloudEvent from the Pub/Sub message."""
    # Handle both string and dict message data
    if isinstance(message_data, dict):
        data_json = json.dumps(message_data)
    else:
        data_json = message_data
        
    # Base64 encode the message data
    data_bytes = data_json.encode('utf-8') if isinstance(data_json, str) else data_json
    data_base64 = base64.b64encode(data_bytes).decode('utf-8')
    
    # Create the CloudEvent
    cloud_event = {
        "specversion": "1.0",
        "type": "google.cloud.pubsub.topic.v1.messagePublished",
        "source": f"pubsub:projects/{PROJECT_ID}/topics/{TOPIC_NAME}",
        "id": str(uuid.uuid4()),
        "time": datetime.utcnow().isoformat() + "Z",
        "datacontenttype": "application/json",
        "data": {
            "message": {
                "data": data_base64,
                "messageId": message_id,
                "publishTime": datetime.utcnow().isoformat() + "Z"
            },
            "subscription": f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_NAME}"
        }
    }
    
    return cloud_event

def forward_to_function(cloud_event):
    """Forward the CloudEvent to the function endpoint."""
    try:
        # First check if the function endpoint is available
        try:
            health_check = requests.get(f"{FUNCTION_URL}/health", timeout=1)
        except requests.exceptions.RequestException:
            # Health endpoint doesn't exist, just check if server is up
            health_check = requests.get(FUNCTION_URL, timeout=1)
        
        # If we get here, the server is up
        response = requests.post(
            FUNCTION_URL,
            json=cloud_event,
            headers={"Content-Type": "application/cloudevents+json"},
            timeout=30
        )
        
        print(f"Forwarded message to function. Status: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"Connection error: Could not connect to {FUNCTION_URL}")
        print("Is your content_processor function running?")
        return False
    except Exception as e:
        print(f"Error forwarding message: {e}")
        return False

def process_message(message):
    """Process a Pub/Sub message by forwarding it to the function."""
    try:
        # Print raw message for debugging
        print(f"[DEBUG] Raw message: message_id={message.message_id}")
        
        # Decode message data
        message_data_raw = message.data.decode('utf-8')
        print(f"[DEBUG] Raw message data: {message_data_raw}")
        
        try:
            message_data = json.loads(message_data_raw)
            print(f"[INFO] Parsed message: {message_data}")
        except json.JSONDecodeError:
            print(f"[WARNING] Message is not valid JSON, treating as string")
            message_data = message_data_raw
        
        # Create CloudEvent
        cloud_event = create_cloud_event(message_data, message.message_id)
        
        # Save event to file for debugging
        with open("last_event.json", "w") as f:
            json.dump(cloud_event, f, indent=2)
        
        # Forward to function
        success = forward_to_function(cloud_event)
        
        if success:
            # Acknowledge the message
            message.ack()
            print(f"✅ Message {message.message_id} successfully forwarded and acknowledged")
            
            # Check for the next topic subscription
            next_topic = os.getenv("TOPIC_TABLES_READY_TO_ASSESS")
            if next_topic:
                print(f"ℹ️ Next step: Check for messages on {next_topic}")
        else:
            print(f"⚠️ Failed to process message {message.message_id}, not acknowledging")
            print("Message will be redelivered")
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        # Don't acknowledge message on error

def main():
    """Main function to subscribe and forward messages."""
    print("\n===== PUB/SUB MESSAGE FORWARDER =====")
    print("This script will forward messages from Pub/Sub to your local function")
    
    # Set up subscription
    subscription_path = setup_subscription()
    if not subscription_path:
        print("❌ Failed to set up subscription, exiting.")
        return 1

    # Create subscriber
    subscriber = pubsub_v1.SubscriberClient()
    
    print(f"\n🎧 Listening for messages on {subscription_path}...")
    print("▶️ Run the asset_indexer function or use test_workflow_chain.py to generate test messages")
    print("⏹️ Press Ctrl+C to stop\n")
    
    # Subscribe and process messages
    try:
        streaming_pull_future = subscriber.subscribe(
            subscription_path, 
            callback=process_message
        )
        
        # Keep the main thread alive
        streaming_pull_future.result()
    except KeyboardInterrupt:
        print("\n⏹️ Stopping subscriber...")
        streaming_pull_future.cancel()
        subscriber.close()
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
if __name__ == "__main__":
    exit_code = main()
    time.sleep(1)  # Give time for logs to flush
    sys.exit(exit_code) 