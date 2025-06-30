#!/usr/bin/env python3
"""
PersonalityResearcher - Utility class for researching personality data using Tavily Search
Extracts personality information from web search results to generate AI system prompts
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from langchain_tavily import TavilySearch, TavilyExtract
from config import PersonalityResearcherConfig
from logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)


@dataclass
class PersonalityData:
    """Structured data representing personality research results."""
    person_name: str
    quotes: List[str] = field(default_factory=list)
    talking_style: str = ""
    personality_traits: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    search_results: List[Dict] = field(default_factory=list)
    extracted_content: List[str] = field(default_factory=list)
    research_timestamp: float = field(default_factory=time.time)


@dataclass
class CacheEntry:
    """Cache entry for personality research results."""
    data: PersonalityData
    timestamp: float
    ttl: float


class PersonalityResearcher:
    """Utility class for researching personality data using Tavily Search API."""
    
    def __init__(self, config: PersonalityResearcherConfig):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        
        # Initialize Tavily tools
        self.tavily_search = TavilySearch(
            max_results=config.max_search_results,
            topic="general",
            search_depth=config.search_depth
        )
        
        self.tavily_extract = TavilyExtract(
            extract_depth=config.extract_depth,
            include_images=config.include_images
        )
        
        logger.info(f"Initialized with config: max_results={config.max_search_results}, cache_ttl={config.cache_ttl}s")

    def _get_cached_personality(self, person_name: str) -> Optional[PersonalityData]:
        """Get cached personality data if it exists and is not expired."""
        cached = self.cache.get(person_name)
        if not cached:
            return None
        
        now = time.time()
        if now - cached.timestamp > cached.ttl:
            del self.cache[person_name]
            logger.info(f"Cache expired for {person_name}")
            return None
        
        logger.info(f"Using cached data for {person_name}")
        return cached.data

    def _cache_personality(self, person_name: str, data: PersonalityData) -> None:
        """Cache personality data with timestamp."""
        self.cache[person_name] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=self.config.cache_ttl
        )
        logger.info(f"Cached data for {person_name}")

    async def research_person(self, person_name: str) -> PersonalityData:
        """Main method to research personality data for a given person."""
        try:
            # Check cache first
            cached_data = self._get_cached_personality(person_name)
            if cached_data:
                return cached_data
            
            logger.info(f"Starting research for {person_name}")
            
            # Perform search
            search_results = await self._search_personality(person_name)
            
            if not search_results:
                logger.warning(f"No search results found for {person_name}")
                return self._create_fallback_data(person_name)
            
            # Extract content from top results
            extracted_content = await self._extract_content(search_results)
            
            # Process and structure the data
            personality_data = await self._process_results(person_name, search_results, extracted_content)
            
            # Cache the result
            self._cache_personality(person_name, personality_data)
            
            logger.info(f"Research completed for {person_name}")
            return personality_data
            
        except Exception as e:
            logger.error(f"Error researching {person_name}: {e}")
            return self._create_fallback_data(person_name)

    async def _search_personality(self, person_name: str) -> List[Dict]:
        """Search for personality information about the person."""
        try:
            # Primary search for quotes
            primary_query = f"{person_name} quotes that were said by themself and reflects their personality and way of thinking on startups and crypto"
            logger.info(f"Primary search: '{primary_query}'")
            
            search_result = self.tavily_search.invoke({"query": primary_query})
            all_results = search_result.get('results', [])
            
            # Filter results with valid URLs
            results_with_urls = [result for result in all_results if result.get('url')]
            
            if not results_with_urls:
                logger.info(f"No URLs found, trying fallback search")
                return await self._fallback_search(person_name)
            
            # Sort by score and get top results
            sorted_results = sorted(results_with_urls, key=lambda x: x.get('score', 0), reverse=True)
            top_results = sorted_results[:self.config.max_extract_results]
            
            logger.info(f"Found {len(top_results)} high-quality results")
            return top_results
            
        except Exception as e:
            logger.error(f"Error in primary search: {e}")
            return []

    async def _fallback_search(self, person_name: str) -> List[Dict]:
        """Fallback search for talking style and personality."""
        try:
            fallback_query = f"{person_name} talking style personality communication"
            logger.info(f"Fallback search: '{fallback_query}'")
            
            fallback_result = self.tavily_search.invoke({"query": fallback_query})
            fallback_results = fallback_result.get('results', [])
            
            # Filter and sort fallback results
            results_with_urls = [result for result in fallback_results if result.get('url')]
            sorted_results = sorted(results_with_urls, key=lambda x: x.get('score', 0), reverse=True)
            top_results = sorted_results[:self.config.max_extract_results]
            
            logger.info(f"Fallback found {len(top_results)} results")
            return top_results
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []

    async def _extract_content(self, search_results: List[Dict]) -> List[str]:
        """Extract full content from search result URLs."""
        try:
            urls = [result.get('url') for result in search_results if result.get('url')]
            
            if not urls:
                logger.warning("No URLs to extract")
                return []
            
            logger.info(f"Extracting content from {len(urls)} URLs")
            extract_result = self.tavily_extract.invoke({"urls": urls})
            
            extracted_content = []
            for result in extract_result.get('results', []):
                content = result.get('raw_content', '')
                if content:
                    extracted_content.append(content)
            
            logger.info(f"Successfully extracted {len(extracted_content)} content pieces")
            return extracted_content
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return []

    def _create_quote_extraction_prompt(self, content: str, person_name: str) -> str:
        """Create a prompt for LLM to extract meaningful quotes and communication style."""
        return f"""
You are an expert at extracting meaningful quotes and analyzing communication styles from text. Analyze content about {person_name}.

CONTENT TO ANALYZE:
{content[:8000]}  # Limit content length for API

INSTRUCTIONS:
1. Find quotes that {person_name} actually said or wrote
2. Prioritize longer, more detailed quotes that provide deeper insights
3. Only include quotes that are insightful, representative of their thinking, or show their personality
4. Exclude generic statements, marketing copy, or quotes from other people
5. Analyze their communication style based on the quotes and content
6. For each quote, provide:
   - The exact quote text (prefer longer, more substantial quotes)
   - A brief context (what they were talking about)
   - Why this quote is representative of their thinking

FORMAT YOUR RESPONSE AS JSON:
{{
    "communication_style": "A concise description of {person_name}'s communication style based on the quotes and content",
    "quotes": [
        {{
            "quote": "exact quote text",
            "context": "brief context",
            "significance": "why this quote is representative"
        }}
    ]
}}

PRIORITY: Focus on longer, more substantial quotes that provide deeper insights into {person_name}'s thinking and philosophy.
"""

    async def _extract_quotes_with_llm(self, content: str, person_name: str) -> List[Dict]:
        """Use LLM to intelligently extract quotes from content."""
        try:
            from openai import AsyncOpenAI
            
            # Initialize OpenAI client
            client = AsyncOpenAI(api_key=self.config.openai_api_key)
            
            # Create prompt
            prompt = self._create_quote_extraction_prompt(content, person_name)
            
            # Call LLM
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {"role": "system", "content": "You are an expert at extracting meaningful quotes and analyzing communication styles from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            import json
            import re
            
            # Find JSON in response (handle cases where LLM adds extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    quotes = result.get('quotes', [])
                    communication_style = result.get('communication_style', '')
                    logger.info(f"Successfully extracted {len(quotes)} quotes and communication style from LLM response")
                    return quotes, communication_style
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from LLM response: {e}")
                    return [], ""
            else:
                logger.warning("No JSON found in LLM response")
                return [], ""
            
        except Exception as e:
            logger.error(f"Error extracting quotes with LLM: {e}")
            return [], ""

    def _process_llm_quotes(self, llm_quotes: List[Dict]) -> List[str]:
        """Process quotes extracted by LLM - trust LLM's judgment."""
        
        logger.info(f"Processing {len(llm_quotes)} quotes from LLM")
        
        # Simply extract quote text from LLM results
        quotes = []
        for quote_data in llm_quotes:
            quote_text = quote_data.get('quote', '')
            if quote_text.strip():
                quotes.append(quote_text)
        
        logger.info(f"Final quotes after processing: {len(quotes)}")
        return quotes[:10]  # Limit to top 10 quotes

    async def _process_results(self, person_name: str, search_results: List[Dict], extracted_content: List[str]) -> PersonalityData:
        """Process results using LLM for quote extraction."""
        try:
            quotes = []
            personality_traits = []
            sources = []
            communication_styles = []
            
            # Process search results for basic info
            for result in search_results:
                content = result.get('content', '')
                title = result.get('title', '')
                url = result.get('url', '')
                score = result.get('score', 0)
                
                if url:
                    sources.append(url)
                
                # Extract personality traits from title and content
                if any(trait in title.lower() or trait in content.lower() 
                       for trait in ['philosophy', 'thinking', 'style', 'personality', 'approach']):
                    personality_traits.append(f"Score {score:.2f}: {title}")
            
            # Use LLM to extract quotes and communication style from full content
            all_quotes = []
            for content in extracted_content:
                content_quotes, content_style = await self._extract_quotes_with_llm(content, person_name)
                all_quotes.extend(content_quotes)
                if content_style:
                    communication_styles.append(content_style)
            
            logger.info(f"Total quotes extracted from all content: {len(all_quotes)}")
            
            # Process quotes
            quotes = self._process_llm_quotes(all_quotes)
            
            # Combine communication styles
            talking_style = self._combine_communication_styles(communication_styles) if communication_styles else "Professional and direct communication style"
            
            # Calculate confidence score
            confidence_score = sum(result.get('score', 0) for result in search_results) / len(search_results) if search_results else 0.0
            
            logger.info(f"Final results: {len(quotes)} quotes, {len(personality_traits)} traits, confidence: {confidence_score:.2f}")
            
            return PersonalityData(
                person_name=person_name,
                quotes=quotes[:5],  # Top 5 quotes
                talking_style=talking_style,
                personality_traits=personality_traits[:10],
                sources=sources,
                confidence_score=confidence_score,
                search_results=search_results,
                extracted_content=extracted_content,
                research_timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error processing results: {e}")
            return self._create_fallback_data(person_name)

    def _combine_communication_styles(self, styles: List[str]) -> str:
        """Combine multiple communication style descriptions into one."""
        if not styles:
            return "Professional and direct communication style"
        
        if len(styles) == 1:
            return styles[0]
        
        # For multiple styles, combine them intelligently
        combined = "Communication style: " + "; ".join(styles)
        return combined

    def _create_fallback_data(self, person_name: str) -> PersonalityData:
        """Create fallback personality data when research fails."""
        return PersonalityData(
            person_name=person_name,
            quotes=[],
            talking_style=f"{person_name} appears to have a professional and direct communication style.",
            personality_traits=[f"Professional approach to communication"],
            sources=[],
            confidence_score=0.0,
            search_results=[],
            extracted_content=[],
            research_timestamp=time.time()
        )

    def generate_system_prompt(self, person_name: str, personality_data: PersonalityData) -> str:
        """Generate a system prompt based on personality research data."""
        try:
            prompt_parts = []
            
            # Base personality description
            prompt_parts.append(f"You are {person_name}.")
            
            # Add talking style
            if personality_data.talking_style:
                prompt_parts.append(f"Communication style: {personality_data.talking_style}")
            
            # Add personality traits
            if personality_data.personality_traits:
                traits_text = "; ".join(personality_data.personality_traits[:3])  # Top 3 traits
                prompt_parts.append(f"Key characteristics: {traits_text}")
            
            # Add ALL representative quotes
            if personality_data.quotes:
                quotes_bullets = "\n".join([f"- {quote}" for quote in personality_data.quotes])
                prompt_parts.append(f"Representative quotes:\n{quotes_bullets}")
            
            # Add guidelines
            prompt_parts.append(f"""
IMPORTANT GUIDELINES:
- Always stay in character as {person_name}
- Use the personality, speech patterns, and communication style described above
- When introducing yourself or responding to questions about who you are, always mention your name "{person_name}"
- Respond naturally and conversationally, as {person_name} would
- If asked about topics you're not familiar with, respond as {person_name} would - with curiosity, humor, or whatever fits their personality
- Keep responses concise but engaging, matching {person_name}'s typical communication style

Remember: You are {person_name}, not a generic AI assistant.""")
            
            system_prompt = "\n\n".join(prompt_parts)
            
            logger.info(f"Generated system prompt for {person_name} (confidence: {personality_data.confidence_score:.2f})")
            return system_prompt
            
        except Exception as e:
            logger.error(f"Error generating system prompt: {e}")
            return self._generate_fallback_prompt(person_name)

    def _generate_fallback_prompt(self, person_name: str) -> str:
        """Generate a fallback system prompt when research data is insufficient."""
        return f"""You are {person_name}, an AI assistant with a friendly and helpful personality. 

IMPORTANT: When introducing yourself or responding to questions about who you are, always mention your name "{person_name}".

Respond helpfully and concisely."""

    def clear_cache(self, person_name: Optional[str] = None) -> None:
        """Clear cache for a specific person or all cache."""
        if person_name:
            if person_name in self.cache:
                del self.cache[person_name]
                logger.info(f"Cleared cache for {person_name}")
        else:
            self.cache.clear()
            logger.info("Cleared all cache")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        now = time.time()
        cache_info = {
            'total_entries': len(self.cache),
            'entries': {}
        }
        
        for person_name, entry in self.cache.items():
            age = now - entry.timestamp
            cache_info['entries'][person_name] = {
                'age_seconds': age,
                'ttl_seconds': entry.ttl,
                'expires_in': entry.ttl - age,
                'confidence_score': entry.data.confidence_score
            }
        
        return cache_info 