"""
Database models for notification tracking and management

SQLAlchemy models for:
- Notification logs
- User preferences
- Template management
- Delivery tracking
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class NotificationStatus(str, enum.Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"


class NotificationChannel(str, enum.Enum):
    """Notification channels"""
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationLog(Base):
    """
    Notification delivery log
    
    Tracks all notifications sent through the system
    """
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Notification details
    channel = Column(SQLEnum(NotificationChannel), nullable=False, index=True)
    notification_type = Column(String(100), nullable=False, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    
    # Content
    subject = Column(String(500))
    content = Column(Text, nullable=False)
    template_id = Column(UUID(as_uuid=True), nullable=True)
    template_variables = Column(JSONB)
    
    # Status tracking
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, index=True)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Provider details
    provider = Column(String(50))  # twilio, sendgrid, firebase, etc.
    provider_message_id = Column(String(255), index=True)
    provider_response = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    queued_at = Column(DateTime)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    failed_at = Column(DateTime)
    
    # Error tracking
    error_code = Column(String(50))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSONB)
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_created_status', 'created_at', 'status'),
        Index('idx_notification_business_channel', 'business_id', 'channel'),
        Index('idx_notification_user_created', 'user_id', 'created_at'),
    )


class NotificationPreference(Base):
    """
    User notification preferences
    
    Manages user opt-in/opt-out settings per channel
    """
    __tablename__ = "notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    business_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=True)
    
    # Notification type preferences
    marketing_enabled = Column(Boolean, default=True)
    transactional_enabled = Column(Boolean, default=True)
    alerts_enabled = Column(Boolean, default=True)
    
    # Contact information
    email_address = Column(String(255))
    phone_number = Column(String(50))
    fcm_token = Column(String(500))
    
    # Quiet hours
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))
    timezone = Column(String(50), default='UTC')
    
    # Language preference
    language = Column(String(10), default='en')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    preferences = Column(JSONB)  # Additional custom preferences


class NotificationTemplate(Base):
    """
    Notification templates
    
    Stores reusable notification templates
    """
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Template details
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    
    # Template content
    subject_template = Column(String(500))
    body_template = Column(Text, nullable=False)
    
    # Template metadata
    language = Column(String(10), default='en')
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)
    
    # Variables
    required_variables = Column(JSONB)  # List of required variable names
    sample_variables = Column(JSONB)  # Sample data for preview
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    
    # Metadata
    metadata = Column(JSONB)
    
    __table_args__ = (
        Index('idx_template_business_active', 'business_id', 'is_active'),
        Index('idx_template_channel_language', 'channel', 'language'),
    )


class NotificationQueue(Base):
    """
    Notification queue for scheduling
    
    Manages pending and scheduled notifications
    """
    __tablename__ = "notification_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_log_id = Column(UUID(as_uuid=True), ForeignKey('notification_logs.id'), nullable=True)
    
    # Queue details
    channel = Column(SQLEnum(NotificationChannel), nullable=False, index=True)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, index=True)
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=False, index=True)
    is_recurring = Column(Boolean, default=False)
    cron_schedule = Column(String(100))  # For recurring notifications
    
    # Status
    status = Column(String(50), default='pending', index=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Task tracking
    celery_task_id = Column(String(255), index=True)
    
    # Payload
    notification_data = Column(JSONB, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationship
    notification_log = relationship("NotificationLog", backref="queue_items")
    
    __table_args__ = (
        Index('idx_queue_scheduled_status', 'scheduled_for', 'status'),
        Index('idx_queue_priority_scheduled', 'priority', 'scheduled_for'),
    )


class NotificationAnalytics(Base):
    """
    Notification analytics aggregation
    
    Stores aggregated metrics for reporting
    """
    __tablename__ = "notification_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Time bucket
    date = Column(DateTime, nullable=False, index=True)
    hour = Column(Integer)  # 0-23
    
    # Dimensions
    channel = Column(SQLEnum(NotificationChannel), index=True)
    notification_type = Column(String(100))
    
    # Metrics
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)
    
    # Engagement metrics (for email/push)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    
    # Performance metrics
    avg_delivery_time_seconds = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_analytics_business_date', 'business_id', 'date'),
        Index('idx_analytics_date_channel', 'date', 'channel'),
    )


class NotificationWebhook(Base):
    """
    Webhook configurations for notification callbacks
    
    Stores webhook endpoints for delivery status updates
    """
    __tablename__ = "notification_webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Webhook details
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255))  # For webhook signature verification
    
    # Events to subscribe to
    events = Column(JSONB)  # List of event types (sent, delivered, failed, etc.)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Retry configuration
    retry_enabled = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)
    
    # Stats
    total_calls = Column(Integer, default=0)
    last_called_at = Column(DateTime)
    last_status_code = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    metadata = Column(JSONB)
