"""
Pydantic models for Dedicated Business Chat Service
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4
from enum import Enum


class MessageRole(str, Enum):
    """Message role types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"
    BOT = "bot"


class MessageType(str, Enum):
    """Message content types"""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    FILE = "file"
    ACTION = "action"
    SUGGESTION = "suggestion"


class SessionStatus(str, Enum):
    """Chat session status"""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    TRANSFERRED = "transferred"


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message"""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ChatMessageResponse(BaseModel):
    """Response model for chat message"""
    id: UUID4
    session_id: str
    role: MessageRole
    content: str
    message_type: MessageType
    ai_generated: bool
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Request model for creating a chat session"""
    business_id: UUID4 = Field(..., description="Business identifier")
    user_id: Optional[UUID4] = Field(default=None, description="User identifier")
    channel: str = Field(default="web", description="Communication channel")
    initial_message: Optional[str] = Field(default=None, description="Initial message to start conversation")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Initial context")


class ChatSessionResponse(BaseModel):
    """Response model for chat session"""
    id: UUID4
    session_id: str
    session_type: str
    business_id: UUID4
    user_id: Optional[UUID4] = None
    status: SessionStatus
    channel: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    message_count: int
    created_at: datetime
    last_message_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]
    total_messages: int
    has_more: bool


class BusinessContextResponse(BaseModel):
    """Business context information"""
    business_id: UUID4
    business_name: str
    business_type: str
    category: str
    features: List[str]
    knowledge_base_count: int
    active_templates: int


class IntentClassification(BaseModel):
    """Intent classification result"""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    suggested_actions: List[str]


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    sentiment: str  # positive, neutral, negative
    score: float
    confidence: float


class ChatAnalytics(BaseModel):
    """Chat analytics for a session"""
    session_id: str
    total_messages: int
    user_messages: int
    ai_messages: int
    avg_response_time: float
    satisfaction_score: Optional[float] = None
    intents_detected: List[str]
    actions_taken: List[Dict[str, Any]]


class HandoverRequest(BaseModel):
    """Request to handover chat to human agent"""
    session_id: str
    reason: str
    agent_id: Optional[UUID4] = None
    notes: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Request to submit feedback for a message"""
    message_id: UUID4
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(default=None, max_length=1000, description="Feedback comment")


class KnowledgeBaseQuery(BaseModel):
    """Query for knowledge base search"""
    query: str = Field(..., min_length=1, max_length=500)
    business_id: UUID4
    top_k: int = Field(default=5, ge=1, le=20)
    content_types: Optional[List[str]] = None


class KnowledgeBaseResult(BaseModel):
    """Knowledge base search result"""
    id: UUID4
    title: str
    content: str
    content_type: str
    similarity: float
    tags: List[str]


class QuickReply(BaseModel):
    """Quick reply suggestion"""
    text: str
    action: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatSuggestions(BaseModel):
    """Chat suggestions for user"""
    quick_replies: List[QuickReply]
    suggested_actions: List[str]
    context_hints: List[str]
