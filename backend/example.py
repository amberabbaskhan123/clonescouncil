#!/usr/bin/env python3
"""
Example usage of the Python ChatService
"""

import asyncio
import os
from chat_service import ChatService, ChatServiceConfig

async def main():
    # Get OpenAI API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Create configuration
    config = ChatServiceConfig(
        person_name="Alice",
        openai_api_key=api_key,
        model_name="gpt-4"
    )

    # Initialize chat service
    chat_service = ChatService(config)

    # Initialize personality (optional - will auto-initialize if not done)
    print("Initializing personality...")
    init_result = await chat_service.initialize()
    print(f"Initialization result: {init_result}")

    # Start chatting
    print("\n=== Chat Session ===")
    
    messages = [
        "Hello! What's your name?",
        "Tell me about yourself",
        "What's your favorite color?",
        "How are you feeling today?"
    ]

    for message in messages:
        print(f"\nUser: {message}")
        try:
            response = await chat_service.chat(message)
            print(f"Alice: {response}")
        except Exception as e:
            print(f"Error: {e}")

    # Get conversation info
    print("\n=== Conversation Info ===")
    info = await chat_service.get_conversation_info()
    print(f"Message count: {info.message_count}")
    print(f"Estimated tokens: {info.estimated_tokens}")
    print(f"Person name: {info.person_name}")

    # Clear conversation
    print("\n=== Clearing Conversation ===")
    await chat_service.clear_conversation()
    print("Conversation cleared!")

    # Start a new conversation
    print("\n=== New Chat Session ===")
    response = await chat_service.chat("Hello again!")
    print(f"User: Hello again!")
    print(f"Alice: {response}")

if __name__ == "__main__":
    asyncio.run(main()) 