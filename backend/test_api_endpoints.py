#!/usr/bin/env python3
"""
Integration tests for the Chat Service API endpoints
These tests send actual HTTP requests to the running API server
"""

import pytest
import pytest_asyncio
import httpx
import os
import time
from typing import AsyncGenerator

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_PERSON_NAME = "TestAssistant"


@pytest.fixture
def api_base_url():
    """Get the API base URL from environment or use default."""
    return os.getenv("API_BASE_URL", API_BASE_URL)


@pytest_asyncio.fixture
async def api_client(api_base_url) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async HTTP client for API testing."""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint(api_client):
    """Test the health check endpoint."""
    response = await api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Chat Service API is running" in data["message"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_root_endpoint(api_client):
    """Test the root endpoint with API information."""
    response = await api_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Chat Service API"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_initialize_personality(api_client):
    """Test personality initialization endpoint."""
    response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "personality_context" in data
    assert len(data["personality_context"]) > 0
    assert "errors" in data
    assert "data_quality" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_chat_endpoint(api_client):
    """Test the chat endpoint."""
    # First initialize the personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Send a chat message
    chat_response = await api_client.post("/chat", json={
        "message": "Hello! What's your name?",
        "person_name": TEST_PERSON_NAME
    })
    
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert "response" in data
    assert "person_name" in data
    assert "message_count" in data
    assert "estimated_tokens" in data
    assert data["person_name"] == TEST_PERSON_NAME
    assert len(data["response"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_conversation_clearing(api_client):
    """Test that conversation clearing works and starts fresh."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Send initial message with specific information
    initial_response = await api_client.post("/chat", json={
        "message": "My name is Alice and I love pizza. What's your name?",
        "person_name": TEST_PERSON_NAME
    })
    assert initial_response.status_code == 200
    
    # Get initial conversation info
    initial_info_response = await api_client.get(f"/conversation/{TEST_PERSON_NAME}")
    assert initial_info_response.status_code == 200
    initial_info = initial_info_response.json()
    assert initial_info["message_count"] > 0

    # Clear conversation
    clear_response = await api_client.delete(f"/conversation/{TEST_PERSON_NAME}")
    assert clear_response.status_code == 200
    clear_data = clear_response.json()
    assert f"Conversation cleared for {TEST_PERSON_NAME}" in clear_data["message"]
    
    # Send message after clearing asking about the previous information
    second_response = await api_client.post("/chat", json={
        "message": "What's my name and what do I love?",
        "person_name": TEST_PERSON_NAME
    })
    assert second_response.status_code == 200
    second_data = second_response.json()
    
    # The AI should not remember the previous conversation
    response_lower = second_data["response"].lower()
    
    # Check that the AI doesn't mention the specific information from the previous conversation
    should_not_contain = ["alice", "pizza"]
    contains_previous_info = any(info in response_lower for info in should_not_contain)
    
    # The AI should indicate it doesn't have this information
    no_memory_indicators = [
        "don't have", "no memory", "i am stateless", "i don't remember", 
        "i do not have memory", "i don't recall", "i do not recall",
        "i do not have access to previous", "don't have the ability to recall",
        "cannot recall", "unable to recall", "no access to previous",
        "first question", "first time", "this session", "new session",
        "isn't a previous", "no previous", "haven't asked", "haven't discussed",
        "don't know", "i don't know", "i do not know", "not provided", "haven't told me"
    ]
    
    has_no_memory = any(indicator in response_lower for indicator in no_memory_indicators)
    
    # Either the AI should indicate it doesn't remember, OR it shouldn't contain the specific info
    assert has_no_memory or not contains_previous_info, f"AI should not remember previous conversation. Response: {second_data['response']}"
    
    # Get conversation info after clearing
    info_after_clear_response = await api_client.get(f"/conversation/{TEST_PERSON_NAME}")
    assert info_after_clear_response.status_code == 200
    info_after_clear = info_after_clear_response.json()
    assert info_after_clear["message_count"] > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_coherent_responses(api_client):
    """Test that the AI returns coherent and contextual responses."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Send a mathematical question
    response = await api_client.post("/chat", json={
        "message": "What is 2 + 2?",
        "person_name": TEST_PERSON_NAME
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Basic response validation
    assert data["response"] is not None
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 10  # Should be more than just "4"
    
    # Should not be error messages
    response_lower = data["response"].lower()
    assert 'error' not in response_lower
    assert 'failed' not in response_lower
    assert 'undefined' not in response_lower
    assert 'null' not in response_lower
    
    # Should contain mathematical content
    assert any(term in response_lower for term in ['four', '4', 'answer', 'result', 'equals'])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_empty_message_handling(api_client):
    """Test that the AI handles empty messages gracefully."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Send empty message
    response = await api_client.post("/chat", json={
        "message": "",
        "person_name": TEST_PERSON_NAME
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["response"] is not None
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0
    assert 'error' not in data["response"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_long_message_handling(api_client):
    """Test that the AI handles very long messages."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Send long message
    long_message = "This is a very long message. " * 100
    response = await api_client.post("/chat", json={
        "message": long_message,
        "person_name": TEST_PERSON_NAME
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["response"] is not None
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0
    assert 'error' not in data["response"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_conversation_info_endpoint(api_client):
    """Test the conversation info endpoint."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Send a message
    chat_response = await api_client.post("/chat", json={
        "message": "Hello!",
        "person_name": TEST_PERSON_NAME
    })
    assert chat_response.status_code == 200
    
    # Get conversation info
    info_response = await api_client.get(f"/conversation/{TEST_PERSON_NAME}")
    assert info_response.status_code == 200
    data = info_response.json()
    
    assert "message_count" in data
    assert "estimated_tokens" in data
    assert "person_name" in data
    assert "personality_context" in data
    assert data["person_name"] == TEST_PERSON_NAME
    assert data["message_count"] > 0
    assert len(data["personality_context"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_conversation_exchanges(api_client):
    """Test multiple conversation exchanges to ensure memory works."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Clear any existing conversation to start fresh
    clear_response = await api_client.delete(f"/conversation/{TEST_PERSON_NAME}")
    assert clear_response.status_code == 200
    
    messages = [
        "My name is John. What's your name?",
        "What's my name?",
        "How many messages have we exchanged so far?",
        "What was the first thing I told you?"
    ]
    
    responses = []
    for i, message in enumerate(messages):
        response = await api_client.post("/chat", json={
            "message": message,
            "person_name": TEST_PERSON_NAME
        })
        assert response.status_code == 200
        data = response.json()
        responses.append(data["response"])
        
        # Basic validation
        assert data["response"] is not None
        assert len(data["response"]) > 0
        assert 'error' not in data["response"].lower()
    
    # Verify that the AI remembers information from earlier in the conversation
    # The AI should remember the user's name "John"
    assert any('john' in response.lower() for response in responses[1:])
    
    # Check conversation info
    info_response = await api_client.get(f"/conversation/{TEST_PERSON_NAME}")
    assert info_response.status_code == 200
    info_data = info_response.json()
    
    # The message_count represents the number of exchanges (user + AI pairs)
    # Each chat call adds 2 messages to the conversation history (user + AI)
    # So for 4 user messages, we expect 4 message_count
    assert info_data["message_count"] == len(messages)
    
    # Verify the conversation has the expected number of exchanges
    # Each exchange creates 2 messages (user + AI), so 4 exchanges = 8 total messages
    # But message_count only counts exchanges, so it should be 4
    assert info_data["message_count"] == 4


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reinitialize_personality(api_client):
    """Test the reinitialize personality endpoint."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    initial_context = init_response.json()["personality_context"]
    
    # Reinitialize personality
    reinit_response = await api_client.post(f"/reinitialize/{TEST_PERSON_NAME}")
    assert reinit_response.status_code == 200
    reinit_data = reinit_response.json()
    
    assert reinit_data["success"] is True
    assert "personality_context" in reinit_data
    assert len(reinit_data["personality_context"]) > 0
    assert "errors" in reinit_data
    assert "data_quality" in reinit_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_handling_invalid_person_name(api_client):
    """Test error handling for invalid person names."""
    # Try to get conversation info for non-existent person
    response = await api_client.get("/conversation/NonExistentPerson")
    # This should still work as it creates a new service instance
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_handling_missing_api_key(api_client):
    """Test error handling when OpenAI API key is missing."""
    # This test would require temporarily unsetting the API key
    # For now, we'll test that the API returns proper error responses
    # when the service is not properly configured
    
    # Test with malformed request
    response = await api_client.post("/chat", json={
        "message": "Hello",
        # Missing person_name
    })
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_requests(api_client):
    """Test handling of concurrent requests to the same person."""
    # Initialize personality
    init_response = await api_client.post("/initialize", json={
        "person_name": TEST_PERSON_NAME
    })
    assert init_response.status_code == 200
    
    # Send multiple concurrent requests
    import asyncio
    
    async def send_message(message):
        return await api_client.post("/chat", json={
            "message": message,
            "person_name": TEST_PERSON_NAME
        })
    
    # Send 3 concurrent messages
    tasks = [
        send_message(f"Message {i}") for i in range(1, 4)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    # All responses should be successful
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data["response"] is not None
        assert len(data["response"]) > 0


if __name__ == "__main__":
    # For manual testing
    import asyncio
    
    async def run_tests():
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
            # Test health endpoint
            response = await client.get("/health")
            print(f"Health check: {response.status_code} - {response.json()}")
    
    asyncio.run(run_tests()) 