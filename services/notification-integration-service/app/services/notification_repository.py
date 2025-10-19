"""
Database Repository for Notification Service

Handles all database operations for notifications
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import uuid

from app.config import settings
from app.utils import logger
from app.models.database import (
    Base,
    NotificationLog,
    NotificationPreference,
    NotificationTemplate,
    NotificationQueue,
    NotificationAnalytics,
    NotificationWebhook,
    NotificationStatus,
    NotificationChannel,
    NotificationPriority
)


class NotificationRepository:
    """
    Database repository for notification operations
    
    Features:
    - CRUD operations for all notification entities
    - Transaction management
    - Query optimization
    - Analytics aggregation
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
        
        try:
            # Create engine
            self.engine = create_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_pre_ping=True,
                echo=settings.environment == "development"
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Database repository initialized")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    @contextmanager
    def get_db(self) -> Session:
        """Get database session"""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")
        
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    # ===== Notification Log Operations =====
    
    async def create_notification_log(
        self,
        business_id: Optional[uuid.UUID],
        user_id: Optional[uuid.UUID],
        channel: NotificationChannel,
        notification_type: str,
        recipient: str,
        content: str,
        **kwargs
    ) -> NotificationLog:
        """Create notification log entry"""
        try:
            with self.get_db() as db:
                log = NotificationLog(
                    business_id=business_id,
                    user_id=user_id,
                    channel=channel,
                    notification_type=notification_type,
                    recipient=recipient,
                    content=content,
                    **kwargs
                )
                db.add(log)
                db.flush()
                db.refresh(log)
                return log
        except SQLAlchemyError as e:
            logger.error(f"Error creating notification log: {e}", exc_info=True)
            raise
    
    async def update_notification_status(
        self,
        notification_id: uuid.UUID,
        status: NotificationStatus,
        provider_message_id: Optional[str] = None,
        provider_response: Optional[Dict] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update notification status"""
        try:
            with self.get_db() as db:
                log = db.query(NotificationLog).filter(
                    NotificationLog.id == notification_id
                ).first()
                
                if not log:
                    return False
                
                log.status = status
                
                if provider_message_id:
                    log.provider_message_id = provider_message_id
                if provider_response:
                    log.provider_response = provider_response
                if error_code:
                    log.error_code = error_code
                if error_message:
                    log.error_message = error_message
                
                # Update timestamps
                if status == NotificationStatus.QUEUED:
                    log.queued_at = datetime.utcnow()
                elif status == NotificationStatus.SENT:
                    log.sent_at = datetime.utcnow()
                elif status == NotificationStatus.DELIVERED:
                    log.delivered_at = datetime.utcnow()
                elif status == NotificationStatus.FAILED:
                    log.failed_at = datetime.utcnow()
                    log.retry_count += 1
                
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating notification status: {e}", exc_info=True)
            return False
    
    async def get_notification_logs(
        self,
        business_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        channel: Optional[NotificationChannel] = None,
        status: Optional[NotificationStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationLog]:
        """Get notification logs with filters"""
        try:
            with self.get_db() as db:
                query = db.query(NotificationLog)
                
                if business_id:
                    query = query.filter(NotificationLog.business_id == business_id)
                if user_id:
                    query = query.filter(NotificationLog.user_id == user_id)
                if channel:
                    query = query.filter(NotificationLog.channel == channel)
                if status:
                    query = query.filter(NotificationLog.status == status)
                if start_date:
                    query = query.filter(NotificationLog.created_at >= start_date)
                if end_date:
                    query = query.filter(NotificationLog.created_at <= end_date)
                
                return query.order_by(desc(NotificationLog.created_at)).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting notification logs: {e}", exc_info=True)
            return []
    
    # ===== Notification Preferences =====
    
    async def get_user_preferences(
        self,
        user_id: uuid.UUID
    ) -> Optional[NotificationPreference]:
        """Get user notification preferences"""
        try:
            with self.get_db() as db:
                return db.query(NotificationPreference).filter(
                    NotificationPreference.user_id == user_id
                ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user preferences: {e}", exc_info=True)
            return None
    
    async def update_user_preferences(
        self,
        user_id: uuid.UUID,
        **preferences
    ) -> bool:
        """Update user notification preferences"""
        try:
            with self.get_db() as db:
                pref = db.query(NotificationPreference).filter(
                    NotificationPreference.user_id == user_id
                ).first()
                
                if not pref:
                    pref = NotificationPreference(user_id=user_id)
                    db.add(pref)
                
                for key, value in preferences.items():
                    if hasattr(pref, key):
                        setattr(pref, key, value)
                
                pref.updated_at = datetime.utcnow()
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating user preferences: {e}", exc_info=True)
            return False
    
    # ===== Templates =====
    
    async def create_template(
        self,
        name: str,
        channel: NotificationChannel,
        body_template: str,
        **kwargs
    ) -> Optional[NotificationTemplate]:
        """Create notification template"""
        try:
            with self.get_db() as db:
                template = NotificationTemplate(
                    name=name,
                    channel=channel,
                    body_template=body_template,
                    **kwargs
                )
                db.add(template)
                db.flush()
                db.refresh(template)
                return template
        except SQLAlchemyError as e:
            logger.error(f"Error creating template: {e}", exc_info=True)
            return None
    
    async def get_template(
        self,
        template_id: uuid.UUID
    ) -> Optional[NotificationTemplate]:
        """Get template by ID"""
        try:
            with self.get_db() as db:
                return db.query(NotificationTemplate).filter(
                    NotificationTemplate.id == template_id
                ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting template: {e}", exc_info=True)
            return None
    
    async def get_templates(
        self,
        business_id: Optional[uuid.UUID] = None,
        channel: Optional[NotificationChannel] = None,
        is_active: bool = True
    ) -> List[NotificationTemplate]:
        """Get templates with filters"""
        try:
            with self.get_db() as db:
                query = db.query(NotificationTemplate)
                
                if business_id:
                    query = query.filter(NotificationTemplate.business_id == business_id)
                if channel:
                    query = query.filter(NotificationTemplate.channel == channel)
                if is_active is not None:
                    query = query.filter(NotificationTemplate.is_active == is_active)
                
                return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting templates: {e}", exc_info=True)
            return []
    
    # ===== Analytics =====
    
    async def get_notification_stats(
        self,
        business_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            with self.get_db() as db:
                query = db.query(NotificationLog)
                
                if business_id:
                    query = query.filter(NotificationLog.business_id == business_id)
                if start_date:
                    query = query.filter(NotificationLog.created_at >= start_date)
                if end_date:
                    query = query.filter(NotificationLog.created_at <= end_date)
                
                total = query.count()
                sent = query.filter(NotificationLog.status == NotificationStatus.SENT).count()
                delivered = query.filter(NotificationLog.status == NotificationStatus.DELIVERED).count()
                failed = query.filter(NotificationLog.status == NotificationStatus.FAILED).count()
                
                return {
                    "total": total,
                    "sent": sent,
                    "delivered": delivered,
                    "failed": failed,
                    "success_rate": (delivered / total * 100) if total > 0 else 0
                }
        except SQLAlchemyError as e:
            logger.error(f"Error getting notification stats: {e}", exc_info=True)
            return {}
    
    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Delete notification logs older than specified days"""
        try:
            with self.get_db() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                deleted = db.query(NotificationLog).filter(
                    NotificationLog.created_at < cutoff_date
                ).delete()
                return deleted
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old logs: {e}", exc_info=True)
            return 0


# Global repository instance
notification_repository = NotificationRepository()
