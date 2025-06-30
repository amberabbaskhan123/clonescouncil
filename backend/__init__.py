"""
Python ChatService Backend Package

This package contains a Python implementation of the ChatService,
converted from the original TypeScript version.
"""

from .chat_service import (
    ChatService,
    ChatServiceConfig,
    InitializationResult,
    ConversationInfo,
    DataQuality,
    PersonalityCacheEntry,
    ChatState
)

__version__ = "1.0.0"
__author__ = "ClonesCouncil Team"

__all__ = [
    "ChatService",
    "ChatServiceConfig", 
    "InitializationResult",
    "ConversationInfo",
    "DataQuality",
    "PersonalityCacheEntry",
    "ChatState"
] 