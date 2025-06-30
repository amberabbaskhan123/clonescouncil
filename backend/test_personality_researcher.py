#!/usr/bin/env python3
"""
Test script for PersonalityResearcher class
Demonstrates how to use the personality research utility
"""

import asyncio

from personality_researcher import PersonalityResearcher
from config import get_config


async def test_personality_research():
    """Test the PersonalityResearcher functionality."""
    
    try:
        # Get configuration from centralized config
        config = get_config()
        personality_config = config.get_personality_researcher_config()
        
        print(f"🔍 Testing PersonalityResearcher with centralized config")
        print("=" * 60)
        
        # Initialize PersonalityResearcher
        researcher = PersonalityResearcher(personality_config)
        
        # Test person to research
        test_person = "Greg Isenberg"
        
        # Research the person
        print("📚 Researching personality data...")
        personality_data = await researcher.research_person(test_person)
        
        # Display results
        print(f"\n✅ Research completed!")
        print(f"📊 Confidence score: {personality_data.confidence_score:.2f}")
        print(f"🔗 Sources found: {len(personality_data.sources)}")
        print(f"💬 Quotes found: {len(personality_data.quotes)}")
        print(f"🎭 Personality traits: {len(personality_data.personality_traits)}")
        
        # Show quotes
        if personality_data.quotes:
            print(f"\n💬 Representative quotes:")
            for i, quote in enumerate(personality_data.quotes, 1):
                print(f"  {i}. {quote}")
        
        # Show personality traits
        if personality_data.personality_traits:
            print(f"\n🎭 Personality traits:")
            for i, trait in enumerate(personality_data.personality_traits, 1):
                print(f"  {i}. {trait}")
        
        # Show talking style
        print(f"\n🗣️  Talking style: {personality_data.talking_style}")
        
        # Generate system prompt
        print(f"\n🤖 Generating system prompt...")
        system_prompt = researcher.generate_system_prompt(test_person, personality_data)
        
        print(f"\n📝 Generated System Prompt:")
        print("-" * 40)
        print(system_prompt)
        print("-" * 40)
        
        # Test caching
        print(f"\n🔄 Testing cache functionality...")
        cached_data = await researcher.research_person(test_person)
        print(f"✅ Cache test completed (should be instant)")
        
        # Show cache info
        cache_info = researcher.get_cache_info()
        print(f"\n📋 Cache information:")
        print(f"  Total entries: {cache_info['total_entries']}")
        for person, info in cache_info['entries'].items():
            print(f"  {person}: age={info['age_seconds']:.1f}s, expires_in={info['expires_in']:.1f}s")
        
        # Show config info
        print(f"\n⚙️  Configuration info:")
        print(f"  Max search results: {personality_config.max_search_results}")
        print(f"  Max extract results: {personality_config.max_extract_results}")
        print(f"  Cache TTL: {personality_config.cache_ttl}s")
        print(f"  Search depth: {personality_config.search_depth}")
        print(f"  Extract depth: {personality_config.extract_depth}")
        
        print(f"\n🎉 Test completed successfully!")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Make sure you have the required environment variables set:")
        print("   - TAVILY_API_KEY")
        print("   - OPENAI_API_KEY")
    except Exception as e:
        print(f"❌ Error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_personality_research()) 