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
        max_results=5,  # Get more results to have better selection
        topic="general",
        search_depth="basic"
    )
    
    tavily_extract = TavilyExtract(
        extract_depth="advanced",
        include_images=False
    )
    
    print("🚀 Searching for Greg Isenberg quotes...")
    
    # Search for Greg Isenberg quotes
    search_query = "Greg Isenberg quotes that were said by themself and reflects their personality and philosophy"
    search_result = tavily_search.invoke({"query": search_query})
    
    print(f"\n📊 Search Results for: '{search_query}'")
    print(f"📝 Found {len(search_result.get('results', []))} results")
    
    # Sort results by score (highest first) and get top 3 with valid URLs
    all_results = search_result.get('results', [])
    
    # Filter results that have valid URLs first
    results_with_urls = [result for result in all_results if result.get('url')]
    
    if not results_with_urls:
        print("🔄 Trying fallback search for talking style and personality...")
        
        fallback_query = f"{search_query.split()[0]} {search_query.split()[1]} talking style personality communication"
        print(f"🔍 Fallback search: '{fallback_query}'")
        
        fallback_result = tavily_search.invoke({"query": fallback_query})
        fallback_all_results = fallback_result.get('results', [])
        fallback_results_with_urls = [result for result in fallback_all_results if result.get('url')]
        
        if not fallback_results_with_urls:
            print("❌ Still no results with valid URLs found in fallback search")
            print("📋 Showing all search results without extraction:")
            for i, result in enumerate(all_results, 1):
                print(f"  {i}. Score: {result.get('score', 'N/A')} - {result.get('title', 'N/A')}")
                print(f"     Content: {result.get('content', 'N/A')[:200]}...")
            return
        
        # Use fallback results
        sorted_results = sorted(fallback_results_with_urls, key=lambda x: x.get('score', 0), reverse=True)
        top_3_results = sorted_results[:2]
        search_result = fallback_result  # Update to use fallback results
        print(f"✅ Found {len(fallback_results_with_urls)} results with URLs in fallback search")
    else:
        # Sort by score (highest first) and get top 3
        sorted_results = sorted(results_with_urls, key=lambda x: x.get('score', 0), reverse=True)
        top_3_results = sorted_results[:2]
    
    print(f"\n🏆 Top 2 highest-scoring results with valid URLs:")
    for i, result in enumerate(top_3_results, 1):
        print(f"  {i}. Score: {result.get('score', 'N/A')} - {result.get('title', 'N/A')}")
        print(f"     URL: {result.get('url', 'N/A')}")
    
    # Get URLs from top 3 results
    urls = [result.get('url') for result in top_3_results]
    
    print(f"\n🔗 URLs to extract (top 2 by score): {urls}")
    
    # Extract full content from top 3 URLs only
    print("\n📄 Extracting full content from top 2 URLs...")
    extract_result = tavily_extract.invoke({"urls": urls})
    
    print(f"\n✅ Extraction completed!")
    print(f"⏱️  Response time: {extract_result.get('response_time', 'N/A')} seconds")
    print(f"📄 Successful extractions: {len(extract_result.get('results', []))}")
    print(f"❌ Failed extractions: {len(extract_result.get('failed_results', []))}")
    
    # Compare search snippets vs full content for top 3 only
    for i, (search_result_item, extract_result_item) in enumerate(zip(
        top_3_results, 
        extract_result.get('results', [])
    )):
        print(f"\n{'='*60}")
        print(f"🏆 TOP {i+1} RESULT (Score: {search_result_item.get('score', 'N/A')})")
        print(f"📰 Title: {search_result_item.get('title', 'N/A')}")
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
    
    # Show other results that weren't extracted
    other_results = sorted_results[2:]
    if other_results:
        print(f"\n📋 Other results with URLs (not extracted due to lower scores):")
        for i, result in enumerate(other_results, 3):
            print(f"  {i}. Score: {result.get('score', 'N/A')} - {result.get('title', 'N/A')}")
    
    # Show results without URLs (if any)
    results_without_urls = [result for result in search_result.get('results', []) if not result.get('url')]
    if results_without_urls:
        print(f"\n⚠️  Results without URLs (excluded from extraction):")
        for i, result in enumerate(results_without_urls, 1):
            print(f"  {i}. Score: {result.get('score', 'N/A')} - {result.get('title', 'N/A')}")


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