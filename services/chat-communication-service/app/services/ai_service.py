"""
AI Integration Service for Chat Communication

Integrates with AI Orchestration Service for intelligent chat responses.
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AIService:
    """
    AI Integration Service
    
    Features:
    - Intent classification
    - Entity extraction
    - Sentiment analysis
    - Response generation
    - RAG (Retrieval-Augmented Generation)
    - Context management
    - Multi-turn conversations
    """
    
    def __init__(self):
        self._initialized = False
        self.ai_orchestration_url = os.getenv(
            "AI_ORCHESTRATION_URL",
            "http://ai-orchestration-service:8030"
        )
        self._client = httpx.AsyncClient(
            base_url=self.ai_orchestration_url,
            timeout=60.0
        )
    
    async def initialize(self):
        """Initialize AI service"""
        try:
            # Test connection to AI orchestration service
            response = await self._client.get("/health")
            if response.status_code == 200:
                self._initialized = True
                logger.info("AI service initialized successfully")
            else:
                logger.warning("AI service health check failed")
        except Exception as e:
            logger.warning(f"Failed to initialize AI service: {e}")
            # Don't fail - service can work without AI
    
    async def classify_intent(
        self,
        message: str,
        business_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Classify user intent from message.
        
        Returns:
            Intent classification with confidence score
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/classify-intent",
                json={
                    "message": message,
                    "context": business_context or {}
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "intent": data.get("intent", "general"),
                    "confidence": data.get("confidence", 0.0),
                    "subcategory": data.get("subcategory"),
                    "entities": data.get("entities", {})
                }
            else:
                logger.warning(f"Intent classification failed: {response.status_code}")
                return {"intent": "general", "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return {"intent": "general", "confidence": 0.0}
    
    async def extract_entities(
        self,
        message: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, List[Any]]:
        """
        Extract entities from message.
        
        Args:
            message: User message
            entity_types: Optional list of entity types to extract
        
        Returns:
            Dictionary of extracted entities by type
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/extract-entities",
                json={
                    "message": message,
                    "entity_types": entity_types or [
                        "date", "time", "location", "person", "product", "service", "number"
                    ]
                }
            )
            
            if response.status_code == 200:
                return response.json().get("entities", {})
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
    
    async def analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """
        Analyze sentiment of message.
        
        Returns:
            Sentiment analysis results
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/analyze-sentiment",
                json={"message": message}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "sentiment": data.get("sentiment", "neutral"),  # positive, negative, neutral
                    "score": data.get("score", 0.0),  # -1 to 1
                    "confidence": data.get("confidence", 0.0)
                }
            else:
                return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
    
    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        business_context: Dict[str, Any],
        session_context: Optional[Dict] = None,
        use_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI response using LangGraph workflow.
        
        Args:
            message: User message
            conversation_history: Previous messages
            business_context: Business information
            session_context: Session-specific context
            use_rag: Whether to use RAG for knowledge retrieval
        
        Returns:
            Generated response with metadata
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/generate-response",
                json={
                    "message": message,
                    "conversation_history": conversation_history,
                    "business_context": business_context,
                    "session_context": session_context or {},
                    "use_rag": use_rag,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", ""),
                    "model": data.get("model", "gpt-4o-mini"),
                    "tokens_used": data.get("tokens_used", 0),
                    "rag_sources": data.get("rag_sources", []),
                    "suggested_actions": data.get("suggested_actions", []),
                    "confidence": data.get("confidence", 0.0)
                }
            else:
                logger.error(f"Response generation failed: {response.status_code}")
                return {
                    "response": "I apologize, but I'm having trouble processing your request. Could you please rephrase?",
                    "model": "fallback",
                    "tokens_used": 0
                }
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I'm experiencing technical difficulties. Please try again in a moment.",
                "model": "error",
                "tokens_used": 0
            }
    
    async def process_message_with_ai(
        self,
        message: str,
        business_id: str,
        conversation_history: List[Dict],
        session_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Complete AI processing pipeline for a message.
        
        This combines all AI operations:
        - Intent classification
        - Entity extraction
        - Sentiment analysis
        - Response generation
        
        Returns:
            Complete AI processing results
        """
        try:
            # Get business context (would be from database)
            business_context = await self._get_business_context(business_id)
            
            # Run AI operations in parallel
            import asyncio
            
            intent_task = self.classify_intent(message, business_context)
            entities_task = self.extract_entities(message)
            sentiment_task = self.analyze_sentiment(message)
            
            intent_result, entities, sentiment = await asyncio.gather(
                intent_task,
                entities_task,
                sentiment_task
            )
            
            # Generate response based on intent
            response_result = await self.generate_response(
                message=message,
                conversation_history=conversation_history,
                business_context=business_context,
                session_context={
                    **(session_context or {}),
                    "intent": intent_result["intent"],
                    "entities": entities,
                    "sentiment": sentiment["sentiment"]
                }
            )
            
            return {
                "intent": intent_result,
                "entities": entities,
                "sentiment": sentiment,
                "response": response_result["response"],
                "ai_metadata": {
                    "model": response_result["model"],
                    "tokens_used": response_result["tokens_used"],
                    "rag_sources": response_result.get("rag_sources", []),
                    "suggested_actions": response_result.get("suggested_actions", []),
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in AI processing pipeline: {e}")
            return {
                "intent": {"intent": "general", "confidence": 0.0},
                "entities": {},
                "sentiment": {"sentiment": "neutral", "score": 0.0},
                "response": "I'm having trouble processing your message. Please try again.",
                "ai_metadata": {"error": str(e)}
            }
    
    async def generate_quick_replies(
        self,
        context: Dict[str, Any],
        max_replies: int = 3
    ) -> List[str]:
        """
        Generate contextual quick reply suggestions.
        
        Args:
            context: Current conversation context
            max_replies: Maximum number of quick replies
        
        Returns:
            List of suggested quick replies
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/generate-quick-replies",
                json={
                    "context": context,
                    "max_replies": max_replies
                }
            )
            
            if response.status_code == 200:
                return response.json().get("quick_replies", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating quick replies: {e}")
            return []
    
    async def detect_language(self, message: str) -> str:
        """
        Detect language of message.
        
        Returns:
            ISO language code (e.g., 'en', 'es', 'fr')
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/detect-language",
                json={"message": message}
            )
            
            if response.status_code == 200:
                return response.json().get("language", "en")
            else:
                return "en"
                
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return "en"
    
    async def translate_message(
        self,
        message: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate message to target language.
        
        Args:
            message: Message to translate
            target_language: Target language code
            source_language: Optional source language code
        
        Returns:
            Translated message
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/translate",
                json={
                    "message": message,
                    "target_language": target_language,
                    "source_language": source_language
                }
            )
            
            if response.status_code == 200:
                return response.json().get("translated_text", message)
            else:
                return message
                
        except Exception as e:
            logger.error(f"Error translating message: {e}")
            return message
    
    async def summarize_conversation(
        self,
        messages: List[Dict[str, str]],
        max_length: int = 200
    ) -> str:
        """
        Generate conversation summary.
        
        Args:
            messages: List of conversation messages
            max_length: Maximum summary length
        
        Returns:
            Conversation summary
        """
        try:
            response = await self._client.post(
                "/api/v1/orchestration/summarize",
                json={
                    "messages": messages,
                    "max_length": max_length
                }
            )
            
            if response.status_code == 200:
                return response.json().get("summary", "")
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return ""
    
    async def _get_business_context(self, business_id: str) -> Dict[str, Any]:
        """
        Get business context from database/cache.
        
        In production, this would fetch from database or cache.
        For now, returns basic structure.
        """
        # This would be fetched from database in production
        return {
            "business_id": business_id,
            "business_name": "",  # Fetched from DB
            "business_category": "",  # Fetched from DB
            "template_type": "",  # Fetched from DB
            "features_enabled": [],  # Fetched from DB
            "operating_hours": {},  # Fetched from DB
            "contact_info": {}  # Fetched from DB
        }
    
    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()


# Singleton instance
ai_service = AIService()

