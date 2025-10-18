"""
Pydantic schemas for Notification Integration Service
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class NotificationChannel(str, Enum):
    """Notification channel types"""
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEBHOOK = "webhook"
    PUSH = "push"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SMSNotificationRequest(BaseModel):
    """SMS notification request"""
    to: str = Field(..., description="Recipient phone number in E.164 format")
    message: str = Field(..., description="SMS message content", max_length=1600)
    from_number: Optional[str] = Field(None, description="Sender phone number")
    status_callback: Optional[str] = Field(None, description="Delivery status webhook URL")
    priority: NotificationPriority = NotificationPriority.NORMAL


class WhatsAppNotificationRequest(BaseModel):
    """WhatsApp notification request"""
    to: str = Field(..., description="Recipient phone number in E.164 format")
    message: str = Field(..., description="WhatsApp message content")
    media_url: Optional[str] = Field(None, description="Media URL (image, video, document)")
    priority: NotificationPriority = NotificationPriority.NORMAL


class EmailNotificationRequest(BaseModel):
    """Email notification request"""
    to_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    html_content: str = Field(..., description="HTML email content")
    plain_content: Optional[str] = Field(None, description="Plain text content")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    from_name: Optional[str] = Field(None, description="Sender name")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Email attachments")
    priority: NotificationPriority = NotificationPriority.NORMAL


class TemplateEmailRequest(BaseModel):
    """Template-based email request"""
    to_email: EmailStr = Field(..., description="Recipient email address")
    template_id: str = Field(..., description="SendGrid template ID")
    dynamic_data: Dict[str, Any] = Field(..., description="Template variables")
    from_email: Optional[EmailStr] = Field(None, description="Sender email")
    from_name: Optional[str] = Field(None, description="Sender name")


class WebhookNotificationRequest(BaseModel):
    """Webhook notification request"""
    webhook_url: str = Field(..., description="Webhook URL")
    data: Dict[str, Any] = Field(..., description="Webhook payload")
    retry_enabled: bool = Field(True, description="Enable retry on failure")


class BulkSMSRequest(BaseModel):
    """Bulk SMS request"""
    recipients: List[str] = Field(..., description="List of recipient phone numbers")
    message: str = Field(..., description="SMS message content", max_length=1600)
    batch_size: int = Field(100, description="Batch size for concurrent sending", ge=1, le=500)


class BulkEmailRequest(BaseModel):
    """Bulk email request"""
    recipients: List[Dict[str, str]] = Field(..., description="List of recipients with email and optional name")
    subject: str = Field(..., description="Email subject")
    html_content: str = Field(..., description="HTML email content")
    batch_size: int = Field(100, description="Batch size for concurrent sending", ge=1, le=500)


class NotificationResponse(BaseModel):
    """Generic notification response"""
    status: str = Field(..., description="Status: success or error")
    message_id: Optional[str] = Field(None, description="Message ID or SID")
    timestamp: str = Field(..., description="Timestamp of notification")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class BulkNotificationResponse(BaseModel):
    """Bulk notification response"""
    total: int = Field(..., description="Total notifications")
    success: int = Field(..., description="Successful notifications")
    failed: int = Field(..., description="Failed notifications")
    details: List[Dict[str, Any]] = Field(..., description="Detailed results")


class KafkaNotificationEvent(BaseModel):
    """Kafka notification event"""
    type: str = Field(..., description="Notification type")
    channel: NotificationChannel = Field(..., description="Notification channel")
    data: Dict[str, Any] = Field(..., description="Notification data")
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
