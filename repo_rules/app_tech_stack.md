# Approved Technology Stack for Functions

This document outlines the approved technology stack for the Functions application. All development must adhere to these technologies to maintain consistency and prevent fragmentation of the codebase.

## Core Technologies

### Backend Framework
- **Python 3.9+**: The application is built with Python for Cloud Functions
- **FastAPI**: For API development and routing (if needed)
- **asyncio**: For asynchronous operations
- **TypeScript**: For type definitions and interfaces

### Environment Configuration
- **.env.example**: Template for development environment variables
- **env.yaml**: Production environment configuration
- **python-dotenv**: For loading development environment variables
- **pyyaml**: For loading production environment configuration

Variables that must be configured in both files:
- Project IDs
- Storage bucket names
- Pub/Sub topic names
- Firestore database IDs
- Collection names
- Region settings
- Service endpoints

### Build & Development
- **Poetry**: For Python dependency management
- **pytest**: For testing Python functions
- **black**: For Python code formatting
- **isort**: For import sorting
- **mypy**: For static type checking

### Firebase Emulator Integration
- **Firebase Emulator Suite**: For local development and testing
- **Firebase Admin SDK**: For Firebase service interactions
- **Google Cloud Storage**: For file storage and retrieval
- **Firestore**: For database operations

### Testing
- **pytest**: For unit and integration testing
- **pytest-asyncio**: For testing async functions
- **pytest-cov**: For code coverage reporting

### Tooling
- **pylint**: For Python code linting
- **black**: For code formatting
- **Git**: For version control
- **mypy**: For static type checking

## Prohibited Technologies

The following technologies should **not** be introduced to the codebase:

- **Django/Flask**: The application uses FastAPI when needed
- **Synchronous Functions**: Use async/await pattern
- **JavaScript Functions**: Use Python for all functions
- **Raw SQL**: Use Firestore operations instead
- **Local File Storage**: Use Google Cloud Storage

## Approved Libraries

The following additional libraries may be used:

- **python-dateutil**: For date manipulation
- **pydantic**: For data validation
- **google-cloud-storage**: For GCS operations
- **firebase-admin**: For Firebase operations
- **aiohttp**: For async HTTP requests
- **python-jose**: For JWT handling
- **python-dotenv**: For development environment configuration
- **pyyaml**: For production environment configuration

## Architecture Patterns

All code should follow these architectural patterns:

- **Async First**: Use async/await for all I/O operations
- **Dependency Injection**: Use FastAPI's dependency injection
- **Service Layer**: Separate business logic from handlers
- **Repository Pattern**: Abstract data access
- **Type Hints**: Use Python type hints throughout
- **Error Handling**: Consistent error response format
- **Environment Configuration**: Use environment variables for all configurable values

## File Structure

- **/src/**: Source code root
- **/src/functions/**: Individual Cloud Functions
- **/src/common/**: Shared utilities and base classes
- **/src/models/**: Data models and schemas
- **/src/services/**: Business logic services
- **/src/repositories/**: Data access layer
- **/tests/**: Test files
- **/config/**: Configuration files
- **.env.example**: Development environment template
- **env.yaml**: Production environment configuration

## Environment Configuration Standards

### Development (.env.example)
- Must contain all required configuration variables
- Values should be development-safe defaults
- Should never contain production credentials
- Must be kept in sync with env.yaml structure
- Example values should demonstrate the expected format

### Production (env.yaml)
- Contains all production configuration
- No default values allowed
- Must be properly secured
- Values deployed through CI/CD
- Structure must match .env.example

### Configuration Loading
```python
def load_config():
    if os.getenv("FUNCTIONS_EMULATOR") == "true":
        # Load .env file for development
        from dotenv import load_dotenv
        load_dotenv()
    else:
        # Load env.yaml for production
        import yaml
        with open("env.yaml") as f:
            config = yaml.safe_load(f)
            os.environ.update(config)
```

## Adding New Dependencies

Before adding any new dependency:
1. Check if the functionality exists in standard library
2. Ensure it's compatible with Cloud Functions
3. Verify it doesn't introduce unnecessary complexity
4. Confirm it's actively maintained and secure
5. Get approval from the tech lead
6. Add to poetry.lock and pyproject.toml

## Version Requirements

- **Python**: 3.9 or higher
- **Firebase CLI**: v12 or higher
- **Poetry**: v1.4 or higher
- **FastAPI**: v0.95 or higher
- **firebase-admin**: v6.2 or higher

## Emulator Integration

The functions in this repository are designed to work with Firebase emulators served from another repository. Key considerations:

- All functions must support both emulator and production environments
- Environment detection must be implemented in all functions
- Emulator connection settings must be configurable
- Local testing must use emulator suite
- Production deployments must be tested in emulator first
