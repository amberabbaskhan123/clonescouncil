#!/usr/bin/env python3
"""
Tavily Extract Demo - Get Full Content from URLs
Shows how to extract complete content from search result URLs
"""

import os
import getpass
from langchain_tavily import TavilySearch, TavilyExtract
from dotenv import load_dotenv

load_dotenv()


def setup_tavily_api_key():
    """Set up Tavily API key from environment or user input."""
    if not os.environ.get("TAVILY_API_KEY"):
        os.environ["TAVILY_API_KEY"] = getpass.getpass("Tavily API key:\n")
    return os.environ["TAVILY_API_KEY"]


def search_and_extract():
    """Search for content and then extract full content from URLs."""
    print("🔍 Setting up Tavily Search and Extract...")
    
    # Initialize both tools
    tavily_search = TavilySearch(
        max_results=3,  # Reduced for demo
        topic="general",
        search_depth="basic"
    )
    
    tavily_extract = TavilyExtract(
        extract_depth="advanced",
        include_images=False
    )
    
    print("🚀 Searching for Elon Musk quotes...")
    
    # Search for Elon Musk quotes
    search_query = "Elon Musk quotes that were said by themself and reflects their personality and philosophy"
    search_result = tavily_search.invoke({"query": search_query})
    
    print(f"\n📊 Search Results for: '{search_query}'")
    print(f"📝 Found {len(search_result.get('results', []))} results")
    
    # Get URLs from search results
    urls = [result.get('url') for result in search_result.get('results', []) if result.get('url')]
    
    if not urls:
        print("❌ No URLs found in search results")
        return
    
    print(f"\n🔗 URLs to extract: {urls}")
    
    # Extract full content from URLs
    print("\n📄 Extracting full content from URLs...")
    extract_result = tavily_extract.invoke({"urls": urls})
    
    print(f"\n✅ Extraction completed!")
    print(f"⏱️  Response time: {extract_result.get('response_time', 'N/A')} seconds")
    print(f"📄 Successful extractions: {len(extract_result.get('results', []))}")
    print(f"❌ Failed extractions: {len(extract_result.get('failed_results', []))}")
    
    # Compare search snippets vs full content
    for i, (search_result_item, extract_result_item) in enumerate(zip(
        search_result.get('results', []), 
        extract_result.get('results', [])
    )):
        print(f"\n{'='*60}")
        print(f"📰 Result {i+1}: {search_result_item.get('title', 'N/A')}")
        print(f"🔗 URL: {search_result_item.get('url', 'N/A')}")
        
        print(f"\n📝 SEARCH SNIPPET (from Tavily Search):")
        print(f"Length: {len(search_result_item.get('content', ''))} characters")
        print(f"Content: {search_result_item.get('content', 'N/A')}")
        
        print(f"\n📄 FULL CONTENT (from Tavily Extract):")
        full_content = extract_result_item.get('raw_content', 'N/A')
        print(f"Length: {len(full_content)} characters")
        print(f"First 500 chars: {full_content[:500]}...")
        
        print(f"\n💡 DIFFERENCE:")
        print(f"Search snippet is {len(search_result_item.get('content', ''))} chars")
        print(f"Full content is {len(full_content)} chars")
        print(f"Ratio: {len(search_result_item.get('content', '')) / len(full_content) * 100:.1f}% of full content")


def main():
    """Main function to run the Tavily extract demo."""
    print("🌐 Tavily Extract Demo - Search vs Full Content")
    print("Comparing search snippets with full extracted content...")
    
    try:
        # Set up API key
        api_key = setup_tavily_api_key()
        print(f"✅ API key configured successfully")
        
        # Perform search and extract
        search_and_extract()
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("💡 Make sure you have a valid Tavily API key")
        print("🔗 Get your API key at: https://tavily.com/")


if __name__ == "__main__":
    main() 