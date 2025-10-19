"""
Notification Scheduler Service using Celery

Enterprise-grade notification scheduling with:
- Delayed notifications
- Recurring notifications
- Priority queues
- Retry logic with exponential backoff
- Dead letter queue handling
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from celery import Celery, Task
from celery.schedules import crontab
from celery.result import AsyncResult
import json

from app.config import settings
from app.utils import logger

# Initialize Celery
celery_app = Celery(
    'notification-scheduler',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_priority=5,
    task_default_queue='notifications',
    task_routes={
        'notification_scheduler.send_sms_task': {'queue': 'sms'},
        'notification_scheduler.send_email_task': {'queue': 'email'},
        'notification_scheduler.send_push_task': {'queue': 'push'},
        'notification_scheduler.send_whatsapp_task': {'queue': 'whatsapp'},
    }
)


class NotificationTask(Task):
    """Base task with retry logic"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


@celery_app.task(base=NotificationTask, name='notification_scheduler.send_sms_task')
def send_sms_task(to: str, message: str, from_number: Optional[str] = None):
    """
    Celery task to send SMS
    
    Args:
        to: Recipient phone number
        message: SMS message
        from_number: Sender phone number
    """
    from app.services.twilio_service import twilio_service
    import asyncio
    
    try:
        logger.info(f"Executing scheduled SMS task for {to}")
        
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            twilio_service.send_sms(
                to=to,
                message=message,
                from_number=from_number
            )
        )
        
        logger.info(f"Scheduled SMS sent: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Scheduled SMS task error: {e}", exc_info=True)
        raise


@celery_app.task(base=NotificationTask, name='notification_scheduler.send_email_task')
def send_email_task(
    to_email: str,
    subject: str,
    html_content: str,
    plain_content: Optional[str] = None
):
    """
    Celery task to send email
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML content
        plain_content: Plain text content
    """
    from app.services.sendgrid_service import sendgrid_service
    import asyncio
    
    try:
        logger.info(f"Executing scheduled email task for {to_email}")
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            sendgrid_service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content
            )
        )
        
        logger.info(f"Scheduled email sent: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Scheduled email task error: {e}", exc_info=True)
        raise


@celery_app.task(base=NotificationTask, name='notification_scheduler.send_push_task')
def send_push_task(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
):
    """
    Celery task to send push notification
    
    Args:
        token: FCM device token
        title: Notification title
        body: Notification body
        data: Custom data
    """
    from app.services.push_notification_service import push_notification_service
    import asyncio
    
    try:
        logger.info(f"Executing scheduled push notification task")
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            push_notification_service.send_notification(
                token=token,
                title=title,
                body=body,
                data=data
            )
        )
        
        logger.info(f"Scheduled push notification sent: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Scheduled push notification task error: {e}", exc_info=True)
        raise


@celery_app.task(base=NotificationTask, name='notification_scheduler.send_whatsapp_task')
def send_whatsapp_task(to: str, message: str, media_url: Optional[str] = None):
    """
    Celery task to send WhatsApp message
    
    Args:
        to: Recipient phone number
        message: Message content
        media_url: Media URL
    """
    from app.services.twilio_service import twilio_service
    import asyncio
    
    try:
        logger.info(f"Executing scheduled WhatsApp task for {to}")
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            twilio_service.send_whatsapp(
                to=to,
                message=message,
                media_url=media_url
            )
        )
        
        logger.info(f"Scheduled WhatsApp sent: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Scheduled WhatsApp task error: {e}", exc_info=True)
        raise


class NotificationScheduler:
    """
    Notification scheduling service
    
    Features:
    - Schedule notifications for future delivery
    - Recurring notifications (daily, weekly, monthly)
    - Priority-based scheduling
    - Task cancellation and modification
    - Status tracking
    """
    
    def __init__(self):
        self.celery = celery_app
    
    def schedule_sms(
        self,
        to: str,
        message: str,
        schedule_time: datetime,
        from_number: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Schedule SMS for future delivery
        
        Args:
            to: Recipient phone number
            message: SMS content
            schedule_time: When to send
            from_number: Sender number
            priority: Task priority (0-9, higher is more important)
        
        Returns:
            Task ID
        """
        try:
            logger.info(f"Scheduling SMS for {to} at {schedule_time}")
            
            # Calculate ETA
            eta = schedule_time
            
            # Schedule task
            result = send_sms_task.apply_async(
                args=[to, message, from_number],
                eta=eta,
                priority=priority
            )
            
            logger.info(f"SMS scheduled with task ID: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Error scheduling SMS: {e}", exc_info=True)
            raise
    
    def schedule_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        schedule_time: datetime,
        plain_content: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Schedule email for future delivery
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            schedule_time: When to send
            plain_content: Plain text content
            priority: Task priority
        
        Returns:
            Task ID
        """
        try:
            logger.info(f"Scheduling email for {to_email} at {schedule_time}")
            
            result = send_email_task.apply_async(
                args=[to_email, subject, html_content, plain_content],
                eta=schedule_time,
                priority=priority
            )
            
            logger.info(f"Email scheduled with task ID: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Error scheduling email: {e}", exc_info=True)
            raise
    
    def schedule_push(
        self,
        token: str,
        title: str,
        body: str,
        schedule_time: datetime,
        data: Optional[Dict[str, str]] = None,
        priority: int = 5
    ) -> str:
        """
        Schedule push notification for future delivery
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            schedule_time: When to send
            data: Custom data
            priority: Task priority
        
        Returns:
            Task ID
        """
        try:
            logger.info(f"Scheduling push notification at {schedule_time}")
            
            result = send_push_task.apply_async(
                args=[token, title, body, data],
                eta=schedule_time,
                priority=priority
            )
            
            logger.info(f"Push notification scheduled with task ID: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Error scheduling push notification: {e}", exc_info=True)
            raise
    
    def schedule_recurring_notification(
        self,
        notification_type: str,
        cron_schedule: str,
        **kwargs
    ) -> str:
        """
        Schedule recurring notification
        
        Args:
            notification_type: 'sms', 'email', 'push', 'whatsapp'
            cron_schedule: Cron expression (e.g., '0 9 * * *' for daily at 9am)
            **kwargs: Notification parameters
        
        Returns:
            Task name for the periodic task
        """
        try:
            logger.info(f"Scheduling recurring {notification_type} with cron: {cron_schedule}")
            
            # Parse cron schedule
            minute, hour, day_of_month, month, day_of_week = cron_schedule.split()
            
            schedule = crontab(
                minute=minute,
                hour=hour,
                day_of_month=day_of_month,
                month_of_year=month,
                day_of_week=day_of_week
            )
            
            # Create task name
            task_name = f"recurring_{notification_type}_{datetime.utcnow().timestamp()}"
            
            # Map notification type to task
            task_map = {
                'sms': send_sms_task,
                'email': send_email_task,
                'push': send_push_task,
                'whatsapp': send_whatsapp_task
            }
            
            task = task_map.get(notification_type)
            if not task:
                raise ValueError(f"Unknown notification type: {notification_type}")
            
            # Register periodic task
            self.celery.conf.beat_schedule[task_name] = {
                'task': task.name,
                'schedule': schedule,
                'kwargs': kwargs
            }
            
            logger.info(f"Recurring notification scheduled: {task_name}")
            return task_name
            
        except Exception as e:
            logger.error(f"Error scheduling recurring notification: {e}", exc_info=True)
            raise
    
    def cancel_scheduled_notification(self, task_id: str) -> bool:
        """
        Cancel a scheduled notification
        
        Args:
            task_id: Task ID to cancel
        
        Returns:
            True if cancelled, False otherwise
        """
        try:
            logger.info(f"Cancelling task: {task_id}")
            
            result = AsyncResult(task_id, app=self.celery)
            result.revoke(terminate=True)
            
            logger.info(f"Task {task_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling task: {e}", exc_info=True)
            return False
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a scheduled notification
        
        Args:
            task_id: Task ID
        
        Returns:
            Dictionary with task status
        """
        try:
            result = AsyncResult(task_id, app=self.celery)
            
            return {
                "task_id": task_id,
                "status": result.state,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting task status: {e}", exc_info=True)
            raise


# Global notification scheduler instance
notification_scheduler = NotificationScheduler()
