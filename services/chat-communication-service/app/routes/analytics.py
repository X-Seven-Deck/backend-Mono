"""
Analytics Routes for Chat Communication

Comprehensive analytics and reporting.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional

from app.models.chat_models import ChatAnalyticsRequest, ChatAnalyticsResponse
from app.services.database_service import db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/business/{business_id}/chat", response_model=ChatAnalyticsResponse)
async def get_chat_analytics(
    business_id: str,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD format"),
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch")
):
    """
    Get comprehensive chat analytics for business.
    
    Returns aggregated metrics including:
    - Session counts
    - Message volumes
    - Response times
    - Intent distribution
    - Channel distribution
    - Sentiment analysis
    """
    try:
        # Calculate date range
        if not end_date:
            end_date = datetime.utcnow().date().isoformat()
        
        if not start_date:
            start_dt = datetime.fromisoformat(end_date) - timedelta(days=days)
            start_date = start_dt.date().isoformat()
        
        # Get analytics data
        analytics_records = await db_service.get_chat_analytics(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Aggregate metrics
        total_sessions = sum(r.get("total_sessions", 0) for r in analytics_records)
        active_sessions = sum(r.get("active_sessions", 0) for r in analytics_records)
        closed_sessions = sum(r.get("closed_sessions", 0) for r in analytics_records)
        total_messages = sum(r.get("total_messages", 0) for r in analytics_records)
        user_messages = sum(r.get("user_messages", 0) for r in analytics_records)
        ai_messages = sum(r.get("ai_messages", 0) for r in analytics_records)
        
        # Calculate averages
        avg_session_duration = (
            sum(r.get("avg_session_duration", 0) for r in analytics_records) /
            len(analytics_records) if analytics_records else 0
        )
        
        avg_messages_per_session = (
            total_messages / total_sessions if total_sessions > 0 else 0
        )
        
        avg_response_time = (
            sum(r.get("avg_response_time", 0) for r in analytics_records) /
            len(analytics_records) if analytics_records else 0
        )
        
        avg_satisfaction_score = (
            sum(r.get("avg_satisfaction_score", 0) for r in analytics_records if r.get("avg_satisfaction_score")) /
            len([r for r in analytics_records if r.get("avg_satisfaction_score")]) 
            if any(r.get("avg_satisfaction_score") for r in analytics_records) else None
        )
        
        # Aggregate distributions
        intent_dist = {}
        channel_dist = {}
        
        for record in analytics_records:
            # Intent distribution
            for intent, count in record.get("intent_distribution", {}).items():
                intent_dist[intent] = intent_dist.get(intent, 0) + count
            
            # Channel distribution
            for channel, count in record.get("channel_distribution", {}).items():
                channel_dist[channel] = channel_dist.get(channel, 0) + count
        
        return ChatAnalyticsResponse(
            business_id=business_id,
            date_range={"start_date": start_date, "end_date": end_date},
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            closed_sessions=closed_sessions,
            total_messages=total_messages,
            user_messages=user_messages,
            ai_messages=ai_messages,
            avg_session_duration=avg_session_duration,
            avg_messages_per_session=avg_messages_per_session,
            avg_response_time=avg_response_time,
            avg_satisfaction_score=avg_satisfaction_score,
            intent_distribution=intent_dist,
            channel_distribution=channel_dist
        )
        
    except Exception as e:
        logger.error(f"Error getting chat analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/sessions/daily")
async def get_daily_session_counts(
    business_id: str,
    days: int = Query(30, ge=1, le=90)
):
    """Get daily session counts for visualization"""
    try:
        end_date = datetime.utcnow().date().isoformat()
        start_dt = datetime.utcnow() - timedelta(days=days)
        start_date = start_dt.date().isoformat()
        
        analytics_records = await db_service.get_chat_analytics(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Format for charting
        daily_data = [
            {
                "date": record["date"],
                "total_sessions": record.get("total_sessions", 0),
                "active_sessions": record.get("active_sessions", 0),
                "closed_sessions": record.get("closed_sessions", 0),
                "total_messages": record.get("total_messages", 0)
            }
            for record in analytics_records
        ]
        
        return {
            "business_id": business_id,
            "date_range": {"start_date": start_date, "end_date": end_date},
            "daily_data": daily_data
        }
        
    except Exception as e:
        logger.error(f"Error getting daily session counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/intents")
async def get_intent_breakdown(
    business_id: str,
    days: int = Query(30, ge=1, le=90)
):
    """Get intent classification breakdown"""
    try:
        end_date = datetime.utcnow().date().isoformat()
        start_dt = datetime.utcnow() - timedelta(days=days)
        start_date = start_dt.date().isoformat()
        
        analytics_records = await db_service.get_chat_analytics(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Aggregate intents
        intent_totals = {}
        
        for record in analytics_records:
            for intent, count in record.get("intent_distribution", {}).items():
                intent_totals[intent] = intent_totals.get(intent, 0) + count
        
        # Calculate percentages
        total = sum(intent_totals.values())
        intent_percentages = {
            intent: {
                "count": count,
                "percentage": round((count / total * 100), 2) if total > 0 else 0
            }
            for intent, count in intent_totals.items()
        }
        
        return {
            "business_id": business_id,
            "date_range": {"start_date": start_date, "end_date": end_date},
            "total_intents": total,
            "intents": intent_percentages
        }
        
    except Exception as e:
        logger.error(f"Error getting intent breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

