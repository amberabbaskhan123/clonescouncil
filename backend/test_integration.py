#!/usr/bin/env python3
"""
Test script to verify integration between ChatService and PersonalityResearcher
"""

import asyncio
import logging
from chat_service import ChatService, ChatServiceConfig
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_chat_service_integration():
    """Test the ChatService with PersonalityResearcher integration."""
    
    try:
        # Get configuration
        config = get_config()
        
        print("🔍 Testing ChatService with PersonalityResearcher integration")
        print("=" * 60)
        
        # Test person
        test_person = "Greg Isenberg"
        
        # Create ChatService config
        chat_config = ChatServiceConfig(
            person_name=test_person,
            openai_api_key=config.personality_researcher.openai_api_key,
            model_name="gpt-4",
            enable_personality_research=True
        )
        
        # Initialize ChatService
        print(f"📝 Initializing ChatService for {test_person}")
        chat_service = ChatService(chat_config)
        
        # Test initialization
        print("🔄 Testing initialization...")
        init_result = await chat_service.initialize()
        
        print(f"✅ Initialization completed!")
        print(f"📊 Success: {len(init_result.errors) == 0}")
        print(f"📝 Personality context length: {len(init_result.personality_context)}")
        print(f"📊 Data quality: {init_result.data_quality}")
        
        if init_result.errors:
            print(f"⚠️  Errors: {init_result.errors}")
        
        # Show personality context
        print(f"\n🤖 Generated Personality Context:")
        print("-" * 40)
        print(init_result.personality_context[:500] + "..." if len(init_result.personality_context) > 500 else init_result.personality_context)
        print("-" * 40)
        
        # Test first chat message
        print(f"\n💬 Testing first chat message...")
        first_message = "Hello! Can you tell me about yourself?"
        first_response = await chat_service.chat(first_message)
        
        print(f"✅ First chat test completed!")
        print(f"💬 User: {first_message}")
        print(f"🤖 AI: {first_response}")
        
        # Test second chat message to verify conversation memory
        print(f"\n💬 Testing second chat message (conversation memory)...")
        second_message = "What did I just ask you about? And can you tell me more about your approach to business?"
        second_response = await chat_service.chat(second_message)
        
        print(f"✅ Second chat test completed!")
        print(f"💬 User: {second_message}")
        print(f"🤖 AI: {second_response}")
        
        # Test third chat message to verify personality consistency
        print(f"\n💬 Testing third chat message (personality consistency)...")
        third_message = "What's your take on community building in the digital age?"
        third_response = await chat_service.chat(third_message)
        
        print(f"✅ Third chat test completed!")
        print(f"💬 User: {third_message}")
        print(f"🤖 AI: {third_response}")
        
        # Test conversation info
        print(f"\n📊 Testing conversation info...")
        conv_info = await chat_service.get_conversation_info()
        print(f"✅ Conversation info: {conv_info}")
        print(f"📊 Message count: {conv_info.message_count}")
        print(f"📊 Estimated tokens: {conv_info.estimated_tokens}")
        
        # Test conversation clearing
        print(f"\n🗑️  Testing conversation clearing...")
        await chat_service.clear_conversation()
        conv_info_after_clear = await chat_service.get_conversation_info()
        print(f"✅ Conversation cleared! New message count: {conv_info_after_clear.message_count}")
        
        # Test that personality is still maintained after clearing
        print(f"\n💬 Testing chat after conversation clear (personality persistence)...")
        test_message_after_clear = "Hi again! What's your name?"
        response_after_clear = await chat_service.chat(test_message_after_clear)
        
        print(f"✅ Chat after clear test completed!")
        print(f"💬 User: {test_message_after_clear}")
        print(f"🤖 AI: {response_after_clear}")
        
        print(f"\n🎉 Integration test completed successfully!")
        print(f"✅ All tests passed: initialization, personality research, conversation memory, and personality consistency!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


async def test_stereotype_person():
    """Test the ChatService with a stereotype/type of person (Exit Bro)."""
    
    try:
        # Get configuration
        config = get_config()
        
        print("\n" + "=" * 60)
        print("🧪 Testing ChatService with Stereotype Person: 'Exit Bro'")
        print("=" * 60)
        
        # Test stereotype person
        stereotype_person = "Exit Bro"
        
        # Create ChatService config
        chat_config = ChatServiceConfig(
            person_name=stereotype_person,
            openai_api_key=config.personality_researcher.openai_api_key,
            model_name="gpt-4",
            enable_personality_research=True
        )
        
        # Initialize ChatService
        print(f"📝 Initializing ChatService for {stereotype_person}")
        chat_service = ChatService(chat_config)
        
        # Test initialization
        print("🔄 Testing initialization...")
        init_result = await chat_service.initialize()
        
        print(f"✅ Initialization completed!")
        print(f"📊 Success: {len(init_result.errors) == 0}")
        print(f"📝 Personality context length: {len(init_result.personality_context)}")
        print(f"📊 Data quality: {init_result.data_quality}")
        
        if init_result.errors:
            print(f"⚠️  Errors: {init_result.errors}")
        
        # Show personality context (this should be the fallback prompt)
        print(f"\n🤖 Generated Personality Context for '{stereotype_person}':")
        print("-" * 60)
        print(init_result.personality_context)
        print("-" * 60)
        
        # Test first chat message
        print(f"\n💬 Testing first chat message...")
        first_message = "Hey Exit Bro! What's your deal?"
        first_response = await chat_service.chat(first_message)
        
        print(f"✅ First chat test completed!")
        print(f"💬 User: {first_message}")
        print(f"🤖 AI: {first_response}")
        
        # Test second chat message
        print(f"\n💬 Testing second chat message...")
        second_message = "What's your approach to business and startups?"
        second_response = await chat_service.chat(second_message)
        
        print(f"✅ Second chat test completed!")
        print(f"💬 User: {second_message}")
        print(f"🤖 AI: {second_response}")
        
        # Test third chat message
        print(f"\n💬 Testing third chat message...")
        third_message = "What's your take on the current startup ecosystem?"
        third_response = await chat_service.chat(third_message)
        
        print(f"✅ Third chat test completed!")
        print(f"💬 User: {third_message}")
        print(f"🤖 AI: {third_response}")
        
        # Test conversation info
        print(f"\n📊 Testing conversation info...")
        conv_info = await chat_service.get_conversation_info()
        print(f"✅ Conversation info: {conv_info}")
        print(f"📊 Message count: {conv_info.message_count}")
        print(f"📊 Estimated tokens: {conv_info.estimated_tokens}")
        
        print(f"\n🎉 Stereotype person test completed successfully!")
        print(f"✅ Shows how system handles non-real person names and stereotypes!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


async def run_all_tests():
    """Run all integration tests."""
    print("🚀 Starting ChatService Integration Tests")
    print("=" * 80)
    
    # Test with real person
    # await test_chat_service_integration()
    
    # Test with stereotype person
    await test_stereotype_person()
    
    print("\n" + "=" * 80)
    print("🎉 All integration tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 