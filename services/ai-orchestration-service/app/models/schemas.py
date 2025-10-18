"""
Pydantic models for AI Orchestration Service

Defines request/response schemas for API endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowType(str, Enum):
    """Available workflow types"""
    BUSINESS_ONBOARDING = "business_onboarding"
    CUSTOMER_SUPPORT = "customer_support"
    ORDER_PROCESSING = "order_processing"


class LLMProviderEnum(str, Enum):
    """LLM provider options"""
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"


class Message(BaseModel):
    """Chat message schema"""
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "role": "user",
            "content": "I want to create a new business",
            "timestamp": "2025-10-04T14:50:00Z"
        }
    })


class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_name: WorkflowType = Field(..., description="Workflow to execute")
    message: str = Field(..., description="User message to process")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User ID")
    business_id: Optional[str] = Field(default=None, description="Business ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "workflow_name": "business_onboarding",
            "message": "I want to register my restaurant",
            "session_id": "session_123",
            "user_id": "user_456",
            "metadata": {"source": "web"}
        }
    })


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution"""
    status: str = Field(..., description="Execution status")
    messages: List[Message] = Field(..., description="Conversation messages")
    context: Dict[str, Any] = Field(..., description="Workflow context")
    current_step: str = Field(..., description="Current workflow step")
    session_id: str = Field(..., description="Session identifier")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "success",
            "messages": [
                {"role": "user", "content": "I want to register my restaurant"},
                {"role": "assistant", "content": "Welcome! Let's get started."}
            ],
            "context": {"business_info": {}},
            "current_step": "welcome",
            "session_id": "session_123"
        }
    })


class GenerateRequest(BaseModel):
    """Request for text generation"""
    prompt: str = Field(..., description="User prompt")
    provider: Optional[LLMProviderEnum] = Field(default=LLMProviderEnum.OPENAI, description="LLM provider")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=4000, description="Maximum tokens")
    system_message: Optional[str] = Field(default=None, description="System message")
    stream: Optional[bool] = Field(default=False, description="Enable streaming")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "prompt": "Explain the benefits of AI for restaurants",
            "provider": "openai",
            "temperature": 0.7,
            "max_tokens": 500
        }
    })


class GenerateResponse(BaseModel):
    """Response from text generation"""
    content: str = Field(..., description="Generated text")
    provider: str = Field(..., description="Provider used")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "content": "AI can help restaurants with...",
            "provider": "openai",
            "tokens_used": 150
        }
    })


class RAGQueryRequest(BaseModel):
    """Request for RAG query"""
    query: str = Field(..., description="Search query")
    business_id: Optional[str] = Field(default=None, description="Business ID for filtering")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of results")
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "What are the restaurant hours?",
            "business_id": "biz_123",
            "top_k": 5
        }
    })


class RAGQueryResponse(BaseModel):
    """Response from RAG query"""
    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents")
    confidence: float = Field(..., description="Confidence score")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "answer": "The restaurant is open from 9 AM to 9 PM daily.",
            "sources": [
                {"content": "Business hours: 9 AM - 9 PM", "score": 0.95}
            ],
            "confidence": 0.95
        }
    })


class SentimentAnalysisRequest(BaseModel):
    """Request for sentiment analysis"""
    text: str = Field(..., description="Text to analyze")
    aspects: Optional[List[str]] = Field(default=None, description="Specific aspects to analyze")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "text": "The food was great but service was slow",
            "aspects": ["food", "service"]
        }
    })


class SentimentAnalysisResponse(BaseModel):
    """Response from sentiment analysis"""
    overall_sentiment: str = Field(..., description="Overall sentiment")
    overall_score: float = Field(..., description="Overall sentiment score")
    aspect_sentiments: Dict[str, Dict[str, Any]] = Field(..., description="Per-aspect sentiments")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "overall_sentiment": "mixed",
            "overall_score": 0.3,
            "aspect_sentiments": {
                "food": {"sentiment": "positive", "score": 0.9},
                "service": {"sentiment": "negative", "score": -0.6}
            }
        }
    })


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(..., description="Dependency statuses")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "timestamp": "2025-10-04T14:50:00Z",
            "version": "0.1.0",
            "dependencies": {
                "redis": "connected",
                "openai": "available"
            }
        }
    })
