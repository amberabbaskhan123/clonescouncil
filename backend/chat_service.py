import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel

# Import PersonalityResearcher
from personality_researcher import PersonalityResearcher
from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DataQuality:
    has_sufficient_data: bool
    has_recent_data: bool
    total_pieces: int


@dataclass
class InitializationResult:
    personality_context: str
    errors: List[str]
    data_quality: DataQuality


@dataclass
class ConversationInfo:
    message_count: int
    estimated_tokens: int
    person_name: str
    personality_context: str


@dataclass
class ChatServiceConfig:
    person_name: str
    personality_context: Optional[str] = None
    max_tokens: Optional[int] = None
    model_name: str = "gpt-4"
    openai_api_key: Optional[str] = None
    enable_personality_research: bool = True


@dataclass
class PersonalityCacheEntry:
    personality_context: str
    timestamp: float
    ttl: float  # Time to live in seconds


@dataclass
class ChatState:
    current_query: str
    response: str
    person_name: str
    personality_context: str
    message_count: int
    estimated_tokens: int
    messages: List[BaseMessage] = field(default_factory=list)


class ChatService:
    def __init__(self, config: ChatServiceConfig):
        self.person_name = config.person_name
        self.personality_context = config.personality_context or ""
        self.thread_id = f"thread_{int(time.time() * 1000)}"
        self.is_initialized = bool(self.personality_context)
        self.personality_cache: Dict[str, PersonalityCacheEntry] = {}
        self.CACHE_TTL = 24 * 60 * 60  # 24 hours in seconds
        self.enable_personality_research = config.enable_personality_research
        
        # Initialize OpenAI client
        if config.openai_api_key:
            self.client = AsyncOpenAI(api_key=config.openai_api_key)
            self.model = ChatOpenAI(
                model_name=config.model_name,
                openai_api_key=config.openai_api_key,
                temperature=0.7
            )
        else:
            raise ValueError("OpenAI API key is required")
        
        # Initialize PersonalityResearcher if enabled
        self.personality_researcher: Optional[PersonalityResearcher] = None
        if self.enable_personality_research:
            try:
                backend_config = get_config()
                personality_config = backend_config.get_personality_researcher_config()
                self.personality_researcher = PersonalityResearcher(personality_config)
                logger.info(f"[ChatService] Initialized PersonalityResearcher for {self.person_name}")
            except Exception as e:
                logger.warning(f"[ChatService] Failed to initialize PersonalityResearcher: {e}")
                self.personality_researcher = None
        
        # Conversation history
        self.conversation_history: List[BaseMessage] = []
        
        logger.info(f"[ChatService] Initialized for {self.person_name}")

    def _get_cached_personality(self) -> Optional[PersonalityCacheEntry]:
        """Get cached personality if it exists and is not expired."""
        cached = self.personality_cache.get(self.person_name)
        if not cached:
            return None
        
        now = time.time()
        if now - cached.timestamp > cached.ttl:
            del self.personality_cache[self.person_name]
            return None
        
        return cached

    def _cache_personality(self, personality_context: str) -> None:
        """Cache personality context with timestamp."""
        self.personality_cache[self.person_name] = PersonalityCacheEntry(
            personality_context=personality_context,
            timestamp=time.time(),
            ttl=self.CACHE_TTL
        )

    async def _research_personality_directly(self) -> Optional[str]:
        """Research personality directly using PersonalityResearcher."""
        if not self.personality_researcher:
            logger.warning(f"[ChatService] PersonalityResearcher not available for {self.person_name}")
            return None
        
        try:
            logger.info(f"[ChatService] Researching personality for {self.person_name}")
            
            # Research the person
            personality_data = await self.personality_researcher.research_person(self.person_name)
            
            # Generate system prompt
            system_prompt = self.personality_researcher.generate_system_prompt(self.person_name, personality_data)
            
            logger.info(f"[ChatService] Successfully researched personality for {self.person_name}")
            logger.info(f"[ChatService] Confidence score: {personality_data.confidence_score:.2f}")
            logger.info(f"[ChatService] Quotes found: {len(personality_data.quotes)}")
            
            return system_prompt
            
        except Exception as e:
            logger.error(f"[ChatService] Error researching personality for {self.person_name}: {e}")
            return None

    async def initialize(self) -> InitializationResult:
        """Initialize the personality context for the person."""
        try:
            # Check cache first
            cached = self._get_cached_personality()
            if cached:
                self.personality_context = cached.personality_context
                self.is_initialized = True
                logger.info(f"[ChatService] Using cached personality for {self.person_name}")
                return InitializationResult(
                    personality_context=cached.personality_context,
                    errors=[],
                    data_quality=DataQuality(
                        has_sufficient_data=True,
                        has_recent_data=True,
                        total_pieces=0
                    )
                )

            logger.info(f"[ChatService] Starting initialization for {self.person_name}")
            
            # Try to research personality if enabled
            if self.enable_personality_research and self.personality_researcher:
                logger.info(f"[ChatService] Attempting personality research for {self.person_name}")
                researched_personality = await self._research_personality_directly()
                
                if researched_personality:
                    personality_context = researched_personality
                    logger.info(f"[ChatService] Using researched personality for {self.person_name}")
                else:
                    # Fallback to basic personality context
                    personality_context = f"""You are {self.person_name}, an AI assistant with a friendly and helpful personality. 
                    You have expertise in various topics and enjoy engaging in meaningful conversations. 
                    You're known for being approachable, knowledgeable, and having a good sense of humor when appropriate."""
                    logger.info(f"[ChatService] Using fallback personality for {self.person_name}")
            else:
                # Use basic personality context
                personality_context = f"""You are {self.person_name}, an AI assistant with a friendly and helpful personality. 
                You have expertise in various topics and enjoy engaging in meaningful conversations. 
                You're known for being approachable, knowledgeable, and having a good sense of humor when appropriate."""
                logger.info(f"[ChatService] Using basic personality for {self.person_name}")
            
            # Update service state
            self.personality_context = personality_context
            self.is_initialized = True
            
            # Cache the result
            self._cache_personality(personality_context)
            
            logger.info(f"[ChatService] Initialization completed for {self.person_name}")
            
            return InitializationResult(
                personality_context=personality_context,
                errors=[],
                data_quality=DataQuality(
                    has_sufficient_data=True,
                    has_recent_data=True,
                    total_pieces=1
                )
            )
            
        except Exception as err:
            logger.error(f"[ChatService] Error in initialization: {err}")
            # Set a basic personality context as fallback
            self.personality_context = f"You are {self.person_name}. I'll respond in a helpful and engaging manner."
            self.is_initialized = True
            
            return InitializationResult(
                personality_context=self.personality_context,
                errors=[f"Initialization failed: {err}"],
                data_quality=DataQuality(
                    has_sufficient_data=False,
                    has_recent_data=False,
                    total_pieces=0
                )
            )

    async def chat(self, message: str) -> str:
        """Send a message and get a response."""
        try:
            # Ensure initialization is complete
            if not self.is_initialized:
                logger.info(f"[ChatService] Auto-initializing for {self.person_name}")
                await self.initialize()

            # Build messages for the chat
            messages = []
            
            # Add system message with personality context
            if self.personality_context:
                messages.append(SystemMessage(content=self.personality_context))
            
            # Add conversation history
            messages.extend(self.conversation_history)
            
            # Add current user message
            messages.append(HumanMessage(content=message))
            
            # Get response from model
            response = await self.model.ainvoke(messages)
            response_content = response.content
            
            # Update conversation history
            self.conversation_history.append(HumanMessage(content=message))
            self.conversation_history.append(AIMessage(content=response_content))
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 20:  # Keep last 10 exchanges
                self.conversation_history = self.conversation_history[-20:]
            
            logger.info(f"[ChatService] Response generated for {self.person_name}")
            return response_content
            
        except Exception as e:
            logger.error(f"[ChatService] Error in chat: {e}")
            raise Exception(f"Failed to generate response: {e}")

    async def clear_conversation(self) -> None:
        """Clear the conversation history."""
        try:
            # Create a new thread ID to effectively clear the conversation
            self.thread_id = f"thread_{int(time.time() * 1000)}"
            self.conversation_history.clear()
            logger.info(f"[ChatService] Conversation cleared. New thread ID: {self.thread_id}")
        except Exception as err:
            logger.error(f"[ChatService] Error clearing conversation: {err}")
            raise Exception("Failed to clear conversation.")

    async def get_conversation_info(self) -> ConversationInfo:
        """Get information about the current conversation."""
        try:
            message_count = len(self.conversation_history) // 2  # Each exchange has 2 messages
            
            # Estimate tokens based on conversation history
            estimated_tokens = len(json.dumps([msg.dict() for msg in self.conversation_history])) // 4
            
            return ConversationInfo(
                message_count=message_count,
                estimated_tokens=estimated_tokens,
                person_name=self.person_name,
                personality_context=self.personality_context
            )
        except Exception as err:
            logger.error(f"[ChatService] Error getting conversation info: {err}")
            # Return default values if there's an error
            return ConversationInfo(
                message_count=0,
                estimated_tokens=0,
                person_name=self.person_name,
                personality_context=self.personality_context
            )

    # Getter methods for external access
    def get_person_name(self) -> str:
        return self.person_name

    def get_personality_context(self) -> str:
        return self.personality_context

    def is_personality_initialized(self) -> bool:
        return self.is_initialized

    async def reinitialize(self) -> InitializationResult:
        """Force re-initialization of personality."""
        self.is_initialized = False
        if self.person_name in self.personality_cache:
            del self.personality_cache[self.person_name]
        return await self.initialize() 