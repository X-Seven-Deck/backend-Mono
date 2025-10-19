"""
Models package for Chat Communication Service
"""

from .chat_models import (
    # Enums
    SessionType,
    SessionStatus,
    MessageRole,
    MessageType,
    Channel,
    Intent,
    Sentiment,
    
    # Session models
    CreateSessionRequest,
    SessionResponse,
    UpdateSessionRequest,
    
    # Message models
    SendMessageRequest,
    MessageResponse,
    ChatResponse,
    MessagesListResponse,
    
    # WhatsApp models
    WhatsAppTextMessage,
    WhatsAppTemplateMessage,
    WhatsAppMediaMessage,
    WhatsAppInteractiveMessage,
    WhatsAppWebhookPayload,
    
    # Instagram models
    InstagramTextMessage,
    InstagramMediaMessage,
    InstagramQuickReplies,
    InstagramWebhookPayload,
    
    # QR Code models
    GenerateQRCodeRequest,
    GenerateTableQRRequest,
    GenerateProductQRRequest,
    GenerateServiceQRRequest,
    QRCodeResponse,
    QRCodeAnalytics,
    
    # Analytics models
    ChatAnalyticsRequest,
    ChatAnalyticsResponse,
    SessionSummary,
    
    # Generic responses
    SuccessResponse,
    ErrorResponse,
    HealthResponse,
    WebhookVerification
)

__all__ = [
    # Enums
    "SessionType",
    "SessionStatus",
    "MessageRole",
    "MessageType",
    "Channel",
    "Intent",
    "Sentiment",
    
    # Session models
    "CreateSessionRequest",
    "SessionResponse",
    "UpdateSessionRequest",
    
    # Message models
    "SendMessageRequest",
    "MessageResponse",
    "ChatResponse",
    "MessagesListResponse",
    
    # WhatsApp models
    "WhatsAppTextMessage",
    "WhatsAppTemplateMessage",
    "WhatsAppMediaMessage",
    "WhatsAppInteractiveMessage",
    "WhatsAppWebhookPayload",
    
    # Instagram models
    "InstagramTextMessage",
    "InstagramMediaMessage",
    "InstagramQuickReplies",
    "InstagramWebhookPayload",
    
    # QR Code models
    "GenerateQRCodeRequest",
    "GenerateTableQRRequest",
    "GenerateProductQRRequest",
    "GenerateServiceQRRequest",
    "QRCodeResponse",
    "QRCodeAnalytics",
    
    # Analytics models
    "ChatAnalyticsRequest",
    "ChatAnalyticsResponse",
    "SessionSummary",
    
    # Generic responses
    "SuccessResponse",
    "ErrorResponse",
    "HealthResponse",
    "WebhookVerification"
]

