"""
Notification scheduling endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.notification_scheduler import notification_scheduler
from app.utils import logger

router = APIRouter()


class ScheduleSMSRequest(BaseModel):
    """Schedule SMS request"""
    to: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="SMS message")
    schedule_time: datetime = Field(..., description="When to send (ISO 8601)")
    from_number: Optional[str] = Field(None, description="Sender number")
    priority: int = Field(5, description="Priority (0-9, higher is more important)", ge=0, le=9)


class ScheduleEmailRequest(BaseModel):
    """Schedule email request"""
    to_email: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    html_content: str = Field(..., description="HTML content")
    schedule_time: datetime = Field(..., description="When to send (ISO 8601)")
    plain_content: Optional[str] = Field(None, description="Plain text content")
    priority: int = Field(5, description="Priority", ge=0, le=9)


class SchedulePushRequest(BaseModel):
    """Schedule push notification request"""
    token: str = Field(..., description="FCM device token")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    schedule_time: datetime = Field(..., description="When to send (ISO 8601)")
    data: Optional[Dict[str, str]] = Field(None, description="Custom data")
    priority: int = Field(5, description="Priority", ge=0, le=9)


class RecurringNotificationRequest(BaseModel):
    """Recurring notification request"""
    notification_type: str = Field(..., description="Type: sms, email, push, whatsapp")
    cron_schedule: str = Field(..., description="Cron expression (e.g., '0 9 * * *')")
    notification_data: Dict[str, Any] = Field(..., description="Notification parameters")


@router.post("/sms")
async def schedule_sms(request: ScheduleSMSRequest):
    """
    Schedule SMS for future delivery
    
    Schedules SMS to be sent at specified time
    """
    try:
        logger.info(f"Scheduling SMS for {request.to} at {request.schedule_time}")
        
        task_id = notification_scheduler.schedule_sms(
            to=request.to,
            message=request.message,
            schedule_time=request.schedule_time,
            from_number=request.from_number,
            priority=request.priority
        )
        
        return {
            "status": "scheduled",
            "task_id": task_id,
            "scheduled_for": request.schedule_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error scheduling SMS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email")
async def schedule_email(request: ScheduleEmailRequest):
    """
    Schedule email for future delivery
    
    Schedules email to be sent at specified time
    """
    try:
        logger.info(f"Scheduling email for {request.to_email} at {request.schedule_time}")
        
        task_id = notification_scheduler.schedule_email(
            to_email=request.to_email,
            subject=request.subject,
            html_content=request.html_content,
            schedule_time=request.schedule_time,
            plain_content=request.plain_content,
            priority=request.priority
        )
        
        return {
            "status": "scheduled",
            "task_id": task_id,
            "scheduled_for": request.schedule_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error scheduling email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/push")
async def schedule_push(request: SchedulePushRequest):
    """
    Schedule push notification for future delivery
    
    Schedules push notification to be sent at specified time
    """
    try:
        logger.info(f"Scheduling push notification at {request.schedule_time}")
        
        task_id = notification_scheduler.schedule_push(
            token=request.token,
            title=request.title,
            body=request.body,
            schedule_time=request.schedule_time,
            data=request.data,
            priority=request.priority
        )
        
        return {
            "status": "scheduled",
            "task_id": task_id,
            "scheduled_for": request.schedule_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error scheduling push: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recurring")
async def create_recurring_notification(request: RecurringNotificationRequest):
    """
    Create recurring notification
    
    Sets up cron-based recurring notifications
    
    Cron format: minute hour day_of_month month day_of_week
    Example: '0 9 * * *' = Every day at 9:00 AM
    """
    try:
        logger.info(f"Creating recurring {request.notification_type} with schedule: {request.cron_schedule}")
        
        task_name = notification_scheduler.schedule_recurring_notification(
            notification_type=request.notification_type,
            cron_schedule=request.cron_schedule,
            **request.notification_data
        )
        
        return {
            "status": "created",
            "task_name": task_name,
            "cron_schedule": request.cron_schedule
        }
    
    except Exception as e:
        logger.error(f"Error creating recurring notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def cancel_scheduled_notification(task_id: str):
    """
    Cancel scheduled notification
    
    Cancels a pending scheduled notification
    """
    try:
        logger.info(f"Cancelling scheduled task: {task_id}")
        
        success = notification_scheduler.cancel_scheduled_notification(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or already executed")
        
        return {
            "status": "cancelled",
            "task_id": task_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Get status of scheduled notification
    
    Returns current status and result of scheduled task
    """
    try:
        status = notification_scheduler.get_task_status(task_id)
        return status
    
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
