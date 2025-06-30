#!/usr/bin/env python3
"""
Backend Service Configuration
Centralized configuration management for all backend services
"""

import os
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class PersonalityResearcherConfig:
    """Configuration for PersonalityResearcher."""
    tavily_api_key: str
    openai_api_key: str
    max_search_results: int = 20
    max_extract_results: int = 5
    search_depth: str = "basic"
    extract_depth: str = "advanced"
    cache_ttl: int = 24 * 60 * 60  # 24 hours in seconds
    min_score_threshold: float = 0.5
    include_images: bool = False


@dataclass
class ChatServiceConfig:
    """Configuration for ChatService."""
    openai_api_key: str
    model_name: str = "gpt-4"
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    max_conversation_history: int = 50
    enable_personality_research: bool = True


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enable_cache: bool = True
    default_ttl: int = 3600  # 1 hour
    max_cache_size: int = 1000
    cache_type: str = "memory"  # memory, redis, etc.


@dataclass
class BackendConfig:
    """Main configuration class for the entire backend service."""
    
    # Service configurations
    personality_researcher: PersonalityResearcherConfig
    chat_service: ChatServiceConfig
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    @classmethod
    def from_environment(cls) -> "BackendConfig":
        """Create configuration from environment variables."""
        
        # Required API keys
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Personality Researcher Config
        personality_researcher = PersonalityResearcherConfig(
            tavily_api_key=tavily_api_key,
            openai_api_key=openai_api_key,
            max_search_results=int(os.getenv("TAVILY_MAX_SEARCH_RESULTS", "5")),
            max_extract_results=int(os.getenv("TAVILY_MAX_EXTRACT_RESULTS", "2")),
            search_depth=os.getenv("TAVILY_SEARCH_DEPTH", "basic"),
            extract_depth=os.getenv("TAVILY_EXTRACT_DEPTH", "advanced"),
            cache_ttl=int(os.getenv("TAVILY_CACHE_TTL", str(24 * 60 * 60))),
            min_score_threshold=float(os.getenv("TAVILY_MIN_SCORE", "0.5")),
            include_images=os.getenv("TAVILY_INCLUDE_IMAGES", "false").lower() == "true"
        )
        
        # Chat Service Config
        chat_service = ChatServiceConfig(
            openai_api_key=openai_api_key,
            model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "0")) or None,
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_conversation_history=int(os.getenv("CHAT_MAX_HISTORY", "50")),
            enable_personality_research=os.getenv("ENABLE_PERSONALITY_RESEARCH", "true").lower() == "true"
        )
        
        # Cache Config
        cache_config = CacheConfig(
            enable_cache=os.getenv("CACHE_ENABLE", "true").lower() == "true",
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
            max_cache_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            cache_type=os.getenv("CACHE_TYPE", "memory")
        )
        
        # Environment
        environment = os.getenv("ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        return cls(
            personality_researcher=personality_researcher,
            chat_service=chat_service,
            cache=cache_config,
            environment=environment,
            debug=debug
        )
    
    def validate(self) -> None:
        """Validate the configuration."""
        errors = []
        
        # Validate required fields
        if not self.personality_researcher.tavily_api_key:
            errors.append("TAVILY_API_KEY is required")
        
        if not self.personality_researcher.openai_api_key:
            errors.append("OPENAI_API_KEY is required for personality researcher")
        
        if not self.chat_service.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Validate ranges
        if not (0 <= self.chat_service.temperature <= 2):
            errors.append("Temperature must be between 0 and 2")
        
        if self.personality_researcher.max_search_results <= 0:
            errors.append("max_search_results must be positive")
        
        if self.personality_researcher.max_extract_results <= 0:
            errors.append("max_extract_results must be positive")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_personality_researcher_config(self) -> PersonalityResearcherConfig:
        """Get PersonalityResearcher configuration."""
        return self.personality_researcher
    
    def get_chat_service_config(self) -> ChatServiceConfig:
        """Get ChatService configuration."""
        return self.chat_service
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.cache
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"


# Global configuration instance
_config: Optional[BackendConfig] = None


def get_config() -> BackendConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = BackendConfig.from_environment()
        _config.validate()
    return _config


def set_config(config: BackendConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
    _config.validate()


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None 