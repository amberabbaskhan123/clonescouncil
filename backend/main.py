#!/usr/bin/env python3
"""
FastAPI server for the ChatService
Provides REST API endpoints for frontend integration
"""

import os
import asyncio
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging

from chat_service import ChatService, ChatServiceConfig, InitializationResult, ConversationInfo

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Chat Service API",
    description="REST API for AI chat service with personality initialization",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for chat service instances
chat_services: Dict[str, ChatService] = {}

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to send")
    person_name: str = Field(..., description="Name of the AI personality")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    person_name: str = Field(..., description="Name of the AI personality")
    message_count: int = Field(..., description="Number of messages in conversation")
    estimated_tokens: int = Field(..., description="Estimated tokens used")

class InitializeRequest(BaseModel):
    person_name: str = Field(..., description="Name of the AI personality")

class InitializeResponse(BaseModel):
    success: bool = Field(..., description="Whether initialization was successful")
    personality_context: str = Field(..., description="Generated personality context")
    errors: list = Field(..., description="List of errors if any")
    data_quality: dict = Field(..., description="Data quality information")

class ConversationInfoResponse(BaseModel):
    message_count: int = Field(..., description="Number of messages in conversation")
    estimated_tokens: int = Field(..., description="Estimated tokens used")
    person_name: str = Field(..., description="Name of the AI personality")
    personality_context: str = Field(..., description="Current personality context")

def get_openai_api_key() -> str:
    """Get OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
    return api_key

def get_or_create_chat_service(person_name: str) -> ChatService:
    """Get existing chat service or create a new one for the person."""
    if person_name not in chat_services:
        api_key = get_openai_api_key()
        config = ChatServiceConfig(
            person_name=person_name,
            openai_api_key=api_key,
            model_name="gpt-4",
            enable_personality_research=True
        )
        chat_services[person_name] = ChatService(config)
        logger.info(f"Created new chat service for {person_name}")
    
    return chat_services[person_name]

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Chat Service API",
        "version": "1.0.0",
        "endpoints": {
            "POST /initialize": "Initialize AI personality",
            "POST /chat": "Send a message and get response",
            "GET /conversation/{person_name}": "Get conversation info",
            "DELETE /conversation/{person_name}": "Clear conversation",
            "POST /reinitialize/{person_name}": "Reinitialize personality"
        }
    }

@app.post("/initialize", response_model=InitializeResponse)
async def initialize_personality(request: InitializeRequest):
    """Initialize the AI personality for a given person."""
    try:
        chat_service = get_or_create_chat_service(request.person_name)
        result: InitializationResult = await chat_service.initialize()
        
        return InitializeResponse(
            success=len(result.errors) == 0,
            personality_context=result.personality_context,
            errors=result.errors,
            data_quality={
                "has_sufficient_data": result.data_quality.has_sufficient_data,
                "has_recent_data": result.data_quality.has_recent_data,
                "total_pieces": result.data_quality.total_pieces
            }
        )
    except Exception as e:
        logger.error(f"Error initializing personality for {request.person_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get an AI response."""
    try:
        chat_service = get_or_create_chat_service(request.person_name)
        
        # Send message and get response
        response = await chat_service.chat(request.message)
        
        # Get conversation info
        info: ConversationInfo = await chat_service.get_conversation_info()
        
        return ChatResponse(
            response=response,
            person_name=request.person_name,
            message_count=info.message_count,
            estimated_tokens=info.estimated_tokens
        )
    except Exception as e:
        logger.error(f"Error in chat for {request.person_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{person_name}", response_model=ConversationInfoResponse)
async def get_conversation_info(person_name: str):
    """Get information about the current conversation."""
    try:
        chat_service = get_or_create_chat_service(person_name)
        info: ConversationInfo = await chat_service.get_conversation_info()
        
        return ConversationInfoResponse(
            message_count=info.message_count,
            estimated_tokens=info.estimated_tokens,
            person_name=info.person_name,
            personality_context=info.personality_context
        )
    except Exception as e:
        logger.error(f"Error getting conversation info for {person_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversation/{person_name}")
async def clear_conversation(person_name: str):
    """Clear the conversation history for a person."""
    try:
        chat_service = get_or_create_chat_service(person_name)
        await chat_service.clear_conversation()
        
        return {"message": f"Conversation cleared for {person_name}"}
    except Exception as e:
        logger.error(f"Error clearing conversation for {person_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reinitialize/{person_name}", response_model=InitializeResponse)
async def reinitialize_personality(person_name: str):
    """Force re-initialization of the AI personality."""
    try:
        chat_service = get_or_create_chat_service(person_name)
        result: InitializationResult = await chat_service.reinitialize()
        
        return InitializeResponse(
            success=len(result.errors) == 0,
            personality_context=result.personality_context,
            errors=result.errors,
            data_quality={
                "has_sufficient_data": result.data_quality.has_sufficient_data,
                "has_recent_data": result.data_quality.has_recent_data,
                "total_pieces": result.data_quality.total_pieces
            }
        )
    except Exception as e:
        logger.error(f"Error reinitializing personality for {person_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 