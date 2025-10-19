"""
Pydantic Models for Chat Communication Service

Enterprise-grade request/response models with validation.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class SessionType(str, Enum):
    """Chat session types"""
    DEDICATED = "dedicated"  # Business-specific chat
    DASHBOARD = "dashboard"  # Business AI assistant
    GLOBAL = "global"  # Cross-business chat


class SessionStatus(str, Enum):
    """Session status"""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    TRANSFERRED = "transferred"


class MessageRole(str, Enum):
    """Message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"
    BOT = "bot"


class MessageType(str, Enum):
    """Message types"""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    FILE = "file"
    ACTION = "action"
    SUGGESTION = "suggestion"


class Channel(str, Enum):
    """Communication channels"""
    WEB = "web"
    MOBILE = "mobile"
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    SMS = "sms"
    QR_CODE = "qr_code"


class Intent(str, Enum):
    """User intents"""
    SEARCH = "search"
    ORDER = "order"
    RESERVATION = "reservation"
    SUPPORT = "support"
    ANALYTICS = "analytics"
    GENERAL = "general"
    MENU_INQUIRY = "menu_inquiry"
    PRICING = "pricing"
    HOURS = "hours"
    LOCATION = "location"


class Sentiment(str, Enum):
    """Sentiment values"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


# ============================================================================
# SESSION MODELS
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create chat session"""
    session_type: SessionType
    business_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: Channel = Channel.WEB
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    qr_code_id: Optional[str] = None  # For QR code initiated chats
    
    @validator('business_id')
    def validate_business_id(cls, v, values):
        """Business ID required for dedicated and dashboard sessions"""
        if values.get('session_type') in [SessionType.DEDICATED, SessionType.DASHBOARD]:
            if not v:
                raise ValueError('business_id required for dedicated/dashboard sessions')
        return v


class SessionResponse(BaseModel):
    """Chat session response"""
    id: str
    session_id: str
    session_type: SessionType
    business_id: Optional[str]
    user_id: Optional[str]
    status: SessionStatus
    channel: Channel
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    message_count: int = 0
    created_at: str
    last_message_at: Optional[str]
    
    class Config:
        use_enum_values = True


class UpdateSessionRequest(BaseModel):
    """Request to update session"""
    status: Optional[SessionStatus] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    assigned_agent_id: Optional[str] = None
    intent: Optional[Intent] = None
    sentiment: Optional[Sentiment] = None


# ============================================================================
# MESSAGE MODELS
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request to send message"""
    session_id: str
    content: str = Field(..., min_length=1, max_length=10000)
    role: MessageRole = MessageRole.USER
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # For AI processing
    process_with_ai: bool = True
    use_rag: bool = True


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    session_id: str
    role: MessageRole
    content: str
    sender_id: Optional[str]
    sender_name: Optional[str]
    message_type: MessageType
    ai_generated: bool = False
    ai_model: Optional[str]
    intent: Optional[Intent]
    entities: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    
    class Config:
        use_enum_values = True


class ChatResponse(BaseModel):
    """Chat response with user message and AI response"""
    user_message: MessageResponse
    ai_response: Optional[MessageResponse] = None
    processing_time_ms: float
    intent: Optional[Intent] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    sentiment: Optional[Sentiment] = None
    suggested_actions: List[str] = Field(default_factory=list)


class MessagesListResponse(BaseModel):
    """List of messages"""
    messages: List[MessageResponse]
    total: int
    session_id: str
    has_more: bool = False


# ============================================================================
# WHATSAPP MODELS
# ============================================================================

class WhatsAppTextMessage(BaseModel):
    """WhatsApp text message"""
    to: str = Field(..., description="Recipient phone number with country code")
    message: str = Field(..., min_length=1, max_length=4096)
    business_id: str
    context_message_id: Optional[str] = None


class WhatsAppTemplateMessage(BaseModel):
    """WhatsApp template message"""
    to: str
    template_name: str
    business_id: str
    language_code: str = "en"
    parameters: Optional[List[str]] = Field(default_factory=list)


class WhatsAppMediaMessage(BaseModel):
    """WhatsApp media message"""
    to: str
    media_type: str = Field(..., description="image, document, video, audio")
    media_url: str
    business_id: str
    caption: Optional[str] = None


class WhatsAppInteractiveMessage(BaseModel):
    """WhatsApp interactive message with buttons"""
    to: str
    body_text: str
    business_id: str
    buttons: List[Dict[str, str]] = Field(..., max_items=3)


class WhatsAppWebhookPayload(BaseModel):
    """WhatsApp webhook payload"""
    entry: List[Dict[str, Any]]
    object: str = "whatsapp_business_account"


# ============================================================================
# INSTAGRAM MODELS
# ============================================================================

class InstagramTextMessage(BaseModel):
    """Instagram text message"""
    recipient_id: str = Field(..., description="Instagram user ID (IGSID)")
    message_text: str = Field(..., min_length=1, max_length=1000)
    business_id: str
    message_type: str = "RESPONSE"


class InstagramMediaMessage(BaseModel):
    """Instagram media message"""
    recipient_id: str
    media_url: str
    business_id: str
    media_type: str = "image"  # image or video


class InstagramQuickReplies(BaseModel):
    """Instagram message with quick replies"""
    recipient_id: str
    message_text: str
    business_id: str
    quick_replies: List[Dict[str, str]] = Field(..., max_items=13)


class InstagramWebhookPayload(BaseModel):
    """Instagram webhook payload"""
    entry: List[Dict[str, Any]]
    object: str = "instagram"


# ============================================================================
# QR CODE MODELS
# ============================================================================

class GenerateQRCodeRequest(BaseModel):
    """Request to generate QR code"""
    business_id: str
    context_type: str = Field(..., description="table, product, service, general")
    context_data: Dict[str, Any]
    expires_in_hours: Optional[int] = None


class GenerateTableQRRequest(BaseModel):
    """Request to generate table QR code"""
    business_id: str
    table_number: str
    table_name: Optional[str] = None
    section: Optional[str] = None


class GenerateProductQRRequest(BaseModel):
    """Request to generate product QR code"""
    business_id: str
    product_id: str
    product_name: str
    product_image: Optional[str] = None


class GenerateServiceQRRequest(BaseModel):
    """Request to generate service QR code"""
    business_id: str
    service_id: str
    service_name: str
    service_type: Optional[str] = None


class QRCodeResponse(BaseModel):
    """QR code generation response"""
    qr_id: str
    qr_image_base64: str
    chat_url: str
    shareable_link: str
    context_type: str
    expires_at: Optional[str]
    metadata: Dict[str, Any]


class QRCodeAnalytics(BaseModel):
    """QR code analytics"""
    qr_id: str
    business_id: str
    context_type: str
    scan_count: int
    created_at: str
    last_scanned_at: Optional[str]
    expires_at: Optional[str]
    active: bool
    scan_history: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class ChatAnalyticsRequest(BaseModel):
    """Request for chat analytics"""
    business_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metrics: Optional[List[str]] = None


class ChatAnalyticsResponse(BaseModel):
    """Chat analytics response"""
    business_id: str
    date_range: Dict[str, str]
    total_sessions: int = 0
    active_sessions: int = 0
    closed_sessions: int = 0
    total_messages: int = 0
    user_messages: int = 0
    ai_messages: int = 0
    avg_session_duration: float = 0.0
    avg_messages_per_session: float = 0.0
    avg_response_time: float = 0.0
    avg_satisfaction_score: Optional[float] = None
    intent_distribution: Dict[str, int] = Field(default_factory=dict)
    channel_distribution: Dict[str, int] = Field(default_factory=dict)
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)


class SessionSummary(BaseModel):
    """Session summary"""
    session_id: str
    session_type: SessionType
    status: SessionStatus
    message_count: int
    created_at: str
    last_message_at: Optional[str]
    intent: Optional[Intent]
    sentiment: Optional[Sentiment]
    recent_messages: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


# ============================================================================
# GENERIC RESPONSES
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str
    services: Dict[str, bool]
    active_rooms: Optional[int] = None


# ============================================================================
# WEBHOOK VERIFICATION
# ============================================================================

class WebhookVerification(BaseModel):
    """Webhook verification for Facebook/Instagram"""
    mode: str = Field(..., alias="hub.mode")
    challenge: str = Field(..., alias="hub.challenge")
    verify_token: str = Field(..., alias="hub.verify_token")
    
    class Config:
        populate_by_name = True

