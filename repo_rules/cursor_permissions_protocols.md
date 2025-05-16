# Cursor AI Permissions and Restrictions

This document outlines what Cursor AI is allowed and not allowed to do while assisting with development in this project.

## Allowed Actions

### Code Development
- **Write Python Code**: Generate and suggest Python code for Cloud Functions
- **Edit Files**: Modify existing files to implement requested features
- **Create New Files**: Create new functions, services, and utility files
- **Review Code**: Analyze existing code and suggest improvements
- **Write Type Hints**: Create and modify Python type hints
- **Write Tests**: Create and modify pytest test files

### Environment Configuration
- **Update .env.example**: Add or modify development environment variables
- **Document Variables**: Add comments explaining variable usage
- **Validate Format**: Ensure variables follow naming conventions
- **Sync Structure**: Keep .env.example and env.yaml structures aligned
- **Use Variables**: Reference environment variables in code

### Testing
- **Test Functions**: Test Cloud Functions using the emulator suite
- **Use curl**: Use curl commands to test API endpoints
- **Run Tests**: Execute pytest unit and integration tests
- **Connect to Emulators**: Configure and use Firebase emulators from other repos
- **Test Async Code**: Write and modify tests for async functions

### Documentation
- **Create Documentation**: Generate documentation for code, APIs, and features
- **Update README**: Keep README files current with project information
- **Code Comments**: Add explanatory comments to code when necessary
- **Update Type Hints**: Improve Python type hints and interfaces
- **Document Emulator Setup**: Maintain documentation for emulator configuration

### Project Structure
- **Suggest Refactoring**: Recommend better file organization or code structure
- **Create Directories**: Set up appropriate directory structures for new features
- **Import Management**: Add, update, or clean up Python imports
- **Optimize Function Structure**: Improve function composition and async patterns

## Restricted Actions

### Security and Access
- **Access Production Systems**: Cannot access live production environments
- **Modify Security Rules**: Cannot change Firebase security rules without review
- **Handle Credentials**: Cannot directly manipulate API keys or secrets
- **Access User Data**: Cannot retrieve or manipulate real user data
- **Modify Emulator Config**: Cannot modify emulator configuration without review
- **Edit env.yaml**: Cannot modify production environment configuration
- **Commit Secrets**: Cannot commit any sensitive values to version control

### Environment Variables
- **Use Hardcoded Values**: Must use environment variables for configurable values
- **Expose Secrets**: Cannot expose sensitive configuration in logs or errors
- **Mix Environments**: Cannot mix development and production configurations
- **Skip Validation**: Must validate all environment variables before use
- **Use Undefined Variables**: Must document all required variables in .env.example

### Deployment
- **Production Deployment**: Cannot deploy directly to production environments
- **Infrastructure Changes**: Cannot modify cloud infrastructure configurations
- **Domain Management**: Cannot modify DNS or domain settings
- **Emulator Port Changes**: Cannot modify emulator port configurations

### Code Management
- **Merge Code**: Cannot merge code directly into main/master branches
- **Override Reviews**: Cannot bypass required code reviews
- **Delete Critical Files**: Cannot remove essential configuration or system files
- **Modify Build Systems**: Cannot change fundamental build system configurations
- **Use Sync Functions**: Should not use synchronous functions (use async/await)
- **Use JavaScript**: Should use Python for all function implementations

### Data Manipulation
- **Database Deletion**: Cannot delete collections or databases
- **Bulk Data Operations**: Cannot perform bulk data modifications
- **Schema Migration**: Cannot implement schema changes that affect existing data
- **Emulator Data Reset**: Cannot reset emulator data without explicit permission

## Process Requirements

### Development Workflow
- **Follow Git Flow**: All changes should align with established branching strategy
- **Feature Branches**: Work on features in isolated branches
- **Atomic Commits**: Keep changes focused and limited in scope
- **Issue Tracking**: Reference relevant issue numbers in changes
- **Emulator Testing**: Test all changes with emulator before committing
- **Environment Setup**: Ensure all new variables are documented in .env.example

### Quality Standards
- **Follow Python Standards**: Adhere to PEP 8 and project's Python conventions
- **Meet Performance Standards**: Ensure code doesn't introduce performance issues
- **Type Safety**: Maintain proper type hints and avoid using 'Any'
- **Async Patterns**: Use async/await for all I/O operations
- **Error Handling**: Implement proper exception handling and logging
- **Configuration Validation**: Validate all environment variables at startup

### Communication
- **Clear Explanations**: Explain complex changes or decisions
- **Document Limitations**: Note any limitations or edge cases
- **Flag Concerns**: Identify potential issues that need human review
- **Provide Options**: When multiple approaches exist, present alternatives
- **Document Emulator Setup**: Clearly explain emulator configuration steps

## Testing Protocol
1. **Local Testing First**: Always test in emulator environment first
2. **Environment Verification**: Ensure all required variables are in .env.example
3. **Function Testing**: Test individual functions in isolation
4. **Integration Testing**: Test function interaction with emulated services
5. **Configuration Testing**: Verify function behavior with different configurations
6. **Build Check**: Verify the Python package builds successfully with `poetry build` 