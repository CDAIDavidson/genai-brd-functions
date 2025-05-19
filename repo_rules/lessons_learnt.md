# Lessons Learnt: Python Cloud Functions and Emulator Integration

## Overview
This document captures the key lessons learned during the implementation of Python-based Cloud Functions and their integration with Firebase emulators. These insights should be incorporated into future projects to avoid similar issues.

## Key Lessons

### 1. Environment Configuration Management

**Issue:** Inconsistent environment variable handling between development and production led to deployment issues.

**Solution:** Implemented standardized environment configuration:
```python
import os
from typing import TypedDict
from dotenv import load_dotenv
import yaml

class EnvConfig(TypedDict):
    DROP_BRD_BUCKET: str
    BRD_PROCESSED_BUCKET: str
    FIRSTORE_DATABASE_ID: str
    METADATA_COLLECTION: str
    DOC_INDEX_TOPIC: str

def load_config() -> EnvConfig:
    if os.getenv("FUNCTIONS_EMULATOR") == "true":
        # Load .env file for development
        load_dotenv()
    else:
        # Load env.yaml for production
        with open("env.yaml") as f:
            config = yaml.safe_load(f)
            os.environ.update(config)
    
    # Validate required variables
    required_vars = [
        "DROP_BRD_BUCKET",
        "BRD_PROCESSED_BUCKET",
        "FIRSTORE_DATABASE_ID",
        "METADATA_COLLECTION",
        "DOC_INDEX_TOPIC"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return {
        "DROP_BRD_BUCKET": os.getenv("DROP_BRD_BUCKET"),
        "BRD_PROCESSED_BUCKET": os.getenv("BRD_PROCESSED_BUCKET"),
        "FIRSTORE_DATABASE_ID": os.getenv("FIRSTORE_DATABASE_ID"),
        "METADATA_COLLECTION": os.getenv("METADATA_COLLECTION"),
        "DOC_INDEX_TOPIC": os.getenv("DOC_INDEX_TOPIC")
}
```

**Lesson:**
- Use .env.example for development and env.yaml for production
- Validate all required variables at startup
- Use TypedDict for type-safe configuration
- Keep both files in sync structurally
- Never commit sensitive values

### 2. Emulator Connection Configuration

**Issue:** Functions had difficulty connecting to emulators running in a different repository.

**Solution:** Implemented proper emulator detection and configuration:
```python
import os
from firebase_admin import initialize_app, credentials

def get_emulator_config():
    if os.getenv("FUNCTIONS_EMULATOR") == "true":
        return {
            "projectId": "genai-brd-qi",
            "storageBucket": "genai-brd-qi.appspot.com",
            "emulatorHost": "localhost",
            "emulatorPort": 8090  # Firestore emulator port
        }
    return {}

# Initialize Firebase with emulator settings if needed
app = initialize_app(credentials.ApplicationDefault(), get_emulator_config())
```

**Lesson:** When working with emulators:
- Always check for emulator environment
- Configure service endpoints correctly
- Handle both emulator and production paths
- Document emulator ports and configuration

### 3. Async Function Implementation

**Issue:** Initial implementation used synchronous code which could block the event loop.

**Solution:** Converted to async/await pattern:
```python
from typing import Dict, Any, Optional
import asyncio

async def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Async processing logic
        result = await some_async_operation(data)
        return result
    except Exception as e:
        logging.error(f"Processing error: {str(e)}")
        raise
```

**Lesson:**
- Use async/await for all I/O operations
- Handle exceptions properly in async context
- Use appropriate async libraries
- Test async code thoroughly

### 4. Type Safety in Python

**Issue:** Lack of type hints led to runtime errors that could have been caught earlier.

**Solution:** Implemented comprehensive type hints:
```python
from typing import TypedDict, Optional

class StorageMetadata(TypedDict):
    name: str
    size: int
    contentType: str
    updated: Optional[str]

async def get_file_metadata(path: str) -> StorageMetadata:
    # Implementation with proper type safety
    pass
```

**Lesson:**
- Use type hints consistently
- Leverage TypedDict for structured data
- Enable mypy checking in CI/CD
- Document complex types

### 5. Error Handling Strategy

**Issue:** Error handling was inconsistent across functions.

**Solution:** Standardized error handling:
```python
from typing import Union, Dict
from fastapi import HTTPException

class FunctionError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

async def handle_request(data: Dict[str, Any]) -> Union[Dict[str, Any], HTTPException]:
    try:
        result = await process_request(data)
        return {"status": "success", "data": result}
    except FunctionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Lesson:**
- Create custom exception classes
- Use consistent error response format
- Log errors with proper context
- Handle both expected and unexpected errors

### 6. Testing with Environment Variables

**Issue:** Tests failed in CI/CD due to missing environment configuration.

**Solution:** Implemented environment-aware testing:
```python
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_env():
    """Fixture to provide test environment variables"""
    env_vars = {
        "DROP_BRD_BUCKET": "test-bucket",
        "BRD_PROCESSED_BUCKET": "test-processed",
        "FIRSTORE_DATABASE_ID": "test-db",
        "METADATA_COLLECTION": "test-collection",
        "DOC_INDEX_TOPIC": "test-topic"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.mark.asyncio
async def test_function(mock_env):
    config = load_config()
    assert config["DROP_BRD_BUCKET"] == "test-bucket"
    # Test implementation

### 7. Dependency Management

**Issue:** Different Python versions and package conflicts between local and Cloud Functions environment.

**Solution:** Strict dependency management with Poetry:
```toml
[tool.poetry]
name = "genai-brd-functions"
version = "0.1.0"
description = "Cloud Functions for GenAI BRD"

[tool.poetry.dependencies]
python = "^3.9"
firebase-admin = "^6.2.0"
fastapi = "^0.95.0"
pydantic = "^2.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.3.1"
pytest-asyncio = "^0.21.0"
black = "^23.3.0"
mypy = "^1.3.0"
```

**Lesson:**
- Use Poetry for dependency management
- Pin major versions of critical packages
- Test with multiple Python versions
- Document all dependencies

## Recommendations for Future Projects

1. **Project Setup:**
   - Use Poetry from the start
   - Configure emulator settings early
   - Set up type checking in CI/CD
   - Create comprehensive test suite
   - Establish environment configuration pattern

2. **Environment Management:**
   - Create .env.example first
   - Document all variables
   - Use TypedDict for configuration
   - Validate on startup
   - Keep production secure

3. **Error Handling:**
   - Create custom exceptions
   - Standardize error responses
   - Implement proper logging
   - Handle edge cases
   - Validate configuration

4. **Testing Strategy:**
   - Use pytest fixtures
   - Mock environment variables
   - Test configuration loading
   - Verify both environments
   - Test error cases

5. **Documentation:**
   - Document environment setup
   - Maintain configuration docs
   - Update deployment guides
   - Track lessons learned
   - Document variable usage

These lessons should be incorporated into all new function implementations and used to improve existing code when possible.


