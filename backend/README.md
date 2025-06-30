# Backend Python Chat Service

A Python implementation of the ChatService using OpenAI's API with async support and comprehensive testing.

## Features

- 🤖 **OpenAI Integration**: Powered by OpenAI's GPT-4 model
- 🔄 **Async Support**: Full async/await support for better performance
- 🧪 **Comprehensive Testing**: Integration tests with real API calls
- 📊 **Conversation Management**: Track message counts and token usage
- 🎭 **Personality Context**: Customizable AI personality and behavior

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -e .
```

### 2. Environment Variables

Create a `.env` file in the project root (one level up from `backend/`):

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run only integration tests (requires API key)
pytest -m integration

# Run tests with verbose output
pytest -v

# Run specific test file
pytest test_chat_service.py -v
```

## Testing Best Practices

### Environment Variable Handling

✅ **Good Practices:**
- Use `conftest.py` to centralize environment setup
- Load `.env` file from project root
- Provide clear error messages when API keys are missing
- Skip tests gracefully when dependencies aren't available
- Mark integration tests appropriately

✅ **What We Do:**
- Load environment variables in `conftest.py` (not individual test files)
- Use fixtures to provide API keys to tests
- Mark tests as `@pytest.mark.integration` for API-dependent tests
- Provide helpful error messages for missing configuration

### Test Structure

```python
# ✅ Good: Use fixtures for setup
@pytest_asyncio.fixture
async def chat_service_async(openai_api_key):
    """Create an async ChatService instance for testing."""
    config = ChatServiceConfig(
        person_name="TestAssistant",
        personality_context="You are a helpful and friendly AI assistant for testing purposes.",
        openai_api_key=openai_api_key,
        model_name="gpt-4"
    )
    service = ChatService(config)
    yield service
    # Cleanup after each test
    await service.clear_conversation()
```

### Running Tests

```bash
# Run all tests (unit + integration)
pytest

# Run only unit tests (no API calls)
pytest -m "not integration"

# Run only integration tests (requires API key)
pytest -m integration

# Run with coverage
pytest --cov=chat_service

# Run specific test
pytest test_chat_service.py::test_conversation_flow_with_memory -v
```

## API Usage

```python
import asyncio
from chat_service import ChatService, ChatServiceConfig

async def main():
    config = ChatServiceConfig(
        person_name="Alice",
        personality_context="You are a helpful assistant.",
        openai_api_key="your-api-key",
        model_name="gpt-4"
    )
    
    service = ChatService(config)
    
    # Chat with the AI
    response = await service.chat("Hello!")
    print(response)
    
    # Get conversation info
    info = await service.get_conversation_info()
    print(f"Messages: {info.message_count}, Tokens: {info.estimated_tokens}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Structure

```
backend/
├── chat_service.py          # Main ChatService implementation
├── test_chat_service.py     # Integration tests
├── conftest.py             # Pytest configuration and shared fixtures
├── example.py              # Usage example
├── pyproject.toml          # Project dependencies
└── README.md              # This file
```

## Dependencies

- `openai>=1.93.0` - OpenAI API client
- `langchain-openai>=0.3.27` - LangChain OpenAI integration
- `pytest>=8.4.1` - Testing framework
- `pytest-asyncio>=1.0.0` - Async test support
- `python-dotenv>=1.1.1` - Environment variable loading 

## Running the Service

### Using uvicorn CLI (Recommended)

Start the server directly with uvicorn:

```bash
# Basic start
uvicorn api_server:app --reload

# With custom host and port
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

# With environment variables
HOST=0.0.0.0 PORT=8000 uvicorn api_server:app --reload
```

### Using Python directly

```bash
python api_server.py
```

## API Endpoints

Once the server is running, you can access:

- **API Documentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### Available Endpoints

- `POST /initialize` - Initialize AI personality
- `POST /chat` - Send a message and get response
- `GET /conversation/{person_name}` - Get conversation info
- `DELETE /conversation/{person_name}` - Clear conversation
- `POST /reinitialize/{person_name}` - Reinitialize personality

## Frontend Integration

The API supports CORS and can be used with any frontend framework. Example usage:

```javascript
// Initialize personality
const initResponse = await fetch('http://localhost:8000/initialize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ person_name: 'Alice' })
});

// Send message
const chatResponse = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello!',
    person_name: 'Alice'
  })
});
```

## Development

- The server runs with auto-reload enabled for development
- Logs are displayed in the console
- API documentation is automatically generated from the code

## Testing

Run the tests:
```bash
pytest
```

### Unit Tests (ChatService)
Run the original unit tests:
```bash
pytest test_chat_service.py
```

### API Integration Tests
Run comprehensive API endpoint tests (requires server to be running):

1. **Start the server in one terminal:**
   ```bash
   uvicorn api_server:app --reload
   ```

2. **Run API tests in another terminal:**
   ```bash
   pytest test_api_endpoints.py -v
   ```

   Or run with custom API URL:
   ```bash
   API_BASE_URL=http://localhost:8000 pytest test_api_endpoints.py -v
   ```

### Test Coverage
The API tests cover:
- ✅ Health and root endpoints
- ✅ Personality initialization
- ✅ Chat functionality
- ✅ Conversation management (info, clearing)
- ✅ Error handling
- ✅ Concurrent requests
- ✅ Memory and conversation state
- ✅ Reinitialization 