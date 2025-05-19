"""
Utility functions for environment detection in cloud functions.
"""

import os

def running_in_gcp():
    """Check if the function is running in GCP (not in emulator)
    
    Google Cloud Functions and Cloud Run set several environment variables
    in production environments that we can use to detect where we're running.
    """
    # Check for emulator environment variables first - these take precedence
    if os.getenv("FIRESTORE_EMULATOR_HOST") or os.getenv("FIREBASE_STORAGE_EMULATOR_HOST"):
        print("[DEBUG] Running in emulator environment")
        return False
        
    # Check for GCP-specific environment variables
    gcp_indicators = [
        "K_SERVICE",              # Cloud Run/Functions service name
        "FUNCTION_NAME",          # Cloud Functions specific
        "FUNCTION_TARGET",        # Cloud Functions specific
        "FUNCTION_SIGNATURE_TYPE" # Cloud Functions specific
    ]
    
    # Debug output
    for var in gcp_indicators:
        if os.getenv(var):
            print(f"[DEBUG] Found GCP indicator: {var}={os.getenv(var)}")
    
    is_gcp = any(os.getenv(var) is not None for var in gcp_indicators)
    print(f"[DEBUG] running_in_gcp() returned: {is_gcp}")
    return is_gcp

def is_storage_emulator():
    """Check if using storage emulator"""
    return os.environ.get("FIREBASE_STORAGE_EMULATOR_HOST") is not None

def get_environment_name():
    """Returns 'emulator' or 'production' based on current environment"""
    return "emulator" if os.environ.get("FIRESTORE_EMULATOR_HOST") else "production"
    
def setup_emulator_environment():
    """Set up emulator environment variables if not already set"""
    if not os.getenv("K_SERVICE"):  # Not in Cloud Run/Functions
        # Set default emulator hosts if not already set
        if "FIRESTORE_EMULATOR_HOST" not in os.environ:
            print("[DEBUG] Setting default FIRESTORE_EMULATOR_HOST")
            os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8090"
        if "FIREBASE_STORAGE_EMULATOR_HOST" not in os.environ:
            print("[DEBUG] Setting default FIREBASE_STORAGE_EMULATOR_HOST")
            os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "127.0.0.1:9199"
        
        print(f"[DEBUG] Using emulators: FIRESTORE={os.environ.get('FIRESTORE_EMULATOR_HOST')}, STORAGE={os.environ.get('FIREBASE_STORAGE_EMULATOR_HOST')}") 