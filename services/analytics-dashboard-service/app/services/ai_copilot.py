"""
AI Copilot Chat Service
Conversational assistant for business queries, reports, and insights
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import httpx


class AICopilot:
    """AI-powered conversational assistant for business intelligence"""
    
    def __init__(self):
        self.ai_orchestration_url = os.getenv(
            "AI_ORCHESTRATION_URL",
            "http://ai-orchestration-service:8050"
        )
        self.conversation_history = {}
    
    async def chat(
        self,
        business_id: UUID,
        user_id: UUID,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process chat message and generate AI response
        """
        try:
            # Get or create conversation
            if not conversation_id:
                conversation_id = f"{business_id}_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            # Initialize conversation history if needed
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            # Add user message to history
            self.conversation_history[conversation_id].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Call AI orchestration service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_orchestration_url}/api/v1/ai-features/copilot-chat",
                    json={
                        "business_id": str(business_id),
                        "user_id": str(user_id),
                        "message": message,
                        "conversation_history": self.conversation_history[conversation_id][-10:],  # Last 10 messages
                        "context": context or {}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                else:
                    result = self._fallback_response(message, context)
            
            # Add assistant response to history
            self.conversation_history[conversation_id].append({
                "role": "assistant",
                "content": result.get("response", ""),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "conversation_id": conversation_id,
                "response": result.get("response"),
                "actions": result.get("suggested_actions", []),
                "data_visualizations": result.get("visualizations", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "conversation_id": conversation_id,
                "response": "I apologize, but I'm having trouble processing your request. Please try again.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _fallback_response(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback response when AI service unavailable"""
        message_lower = message.lower()
        
        # Simple keyword-based responses
        if "revenue" in message_lower or "sales" in message_lower:
            return {
                "response": "I can help you analyze revenue and sales data. What specific time period would you like to review?",
                "suggested_actions": [
                    "Show revenue for last 7 days",
                    "Compare sales with last month",
                    "Show revenue forecast"
                ]
            }
        elif "customer" in message_lower:
            return {
                "response": "I can provide customer insights and analytics. What would you like to know about your customers?",
                "suggested_actions": [
                    "Show customer retention rate",
                    "List top customers",
                    "Analyze customer churn"
                ]
            }
        else:
            return {
                "response": "I'm here to help with your business analytics. You can ask me about revenue, customers, inventory, or any other business metrics.",
                "suggested_actions": [
                    "Show dashboard overview",
                    "Generate business report",
                    "Analyze trends"
                ]
            }


_ai_copilot: Optional[AICopilot] = None

def get_ai_copilot() -> AICopilot:
    global _ai_copilot
    if _ai_copilot is None:
        _ai_copilot = AICopilot()
    return _ai_copilot
