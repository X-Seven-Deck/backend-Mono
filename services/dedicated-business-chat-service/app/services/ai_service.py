"""
AI Service for Dedicated Business Chat
Handles AI-powered responses with business context awareness and RAG
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from app.config import settings
from app.services.database import db_service

logger = logging.getLogger(__name__)


class AIService:
    """AI service for business-aware chat responses"""
    
    def __init__(self):
        """Initialize AI service"""
        self.client: Optional[AsyncOpenAI] = None
        self.llm: Optional[ChatOpenAI] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI clients"""
        if self._initialized:
            return
        
        try:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                api_key=settings.openai_api_key
            )
            
            self.embeddings = OpenAIEmbeddings(
                model=settings.openai_embedding_model,
                api_key=settings.openai_api_key
            )
            
            self._initialized = True
            logger.info("AI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise
    
    async def generate_response(
        self,
        session_id: str,
        user_message: str,
        business_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate AI response with business context
        
        Returns:
            Tuple of (response_text, metadata)
        """
        start_time = time.time()
        
        try:
            # Get business context
            business_context = await db_service.get_business_context(business_id)
            if not business_context:
                raise Exception(f"Business {business_id} not found")
            
            # Get conversation history
            history = await db_service.get_recent_context(
                session_id,
                max_messages=settings.max_context_messages
            )
            
            # Get relevant knowledge base content (RAG)
            knowledge_context = ""
            if settings.rag_enabled:
                knowledge_context = await self._get_rag_context(
                    business_id,
                    user_message
                )
            
            # Classify intent
            intent, entities = await self._classify_intent(user_message)
            
            # Build system prompt with business context
            system_prompt = self._build_system_prompt(
                business_context,
                knowledge_context
            )
            
            # Build conversation messages
            messages = self._build_messages(system_prompt, history, user_message)
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            
            response_text = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            # Analyze sentiment
            sentiment = await self._analyze_sentiment(user_message)
            
            # Determine actions
            actions = await self._determine_actions(intent, entities, business_context)
            
            metadata = {
                "intent": intent,
                "entities": entities,
                "sentiment": sentiment,
                "actions": actions,
                "processing_time": processing_time,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "model": settings.openai_model
            }
            
            logger.info(f"Generated response for session {session_id} in {processing_time:.2f}s")
            
            return response_text, metadata
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _build_system_prompt(
        self,
        business_context: Dict[str, Any],
        knowledge_context: str
    ) -> str:
        """Build system prompt with business context"""
        business = business_context.get("business", {})
        business_name = business.get("name", "the business")
        category = business.get("business_categories", {}).get("name", "business")
        
        prompt = f"""You are an AI assistant for {business_name}, a {category}.

Your role is to:
1. Provide helpful, accurate information about the business
2. Answer customer questions professionally and courteously
3. Assist with orders, reservations, and bookings when applicable
4. Maintain context throughout the conversation
5. Be proactive in suggesting relevant services or products

Business Information:
- Name: {business_name}
- Category: {category}
- Knowledge Base Entries: {business_context.get('knowledge_base_count', 0)}

"""
        
        if knowledge_context:
            prompt += f"\nRelevant Information:\n{knowledge_context}\n"
        
        prompt += """
Guidelines:
- Always be polite and professional
- If you don't know something, admit it and offer to connect them with a human agent
- For orders or reservations, collect all necessary information
- Provide specific details when available
- Keep responses concise but informative
- Use the business's name naturally in conversation
"""
        
        return prompt
    
    def _build_messages(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        user_message: str
    ) -> List[Dict[str, str]]:
        """Build message list for API call"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def _get_rag_context(
        self,
        business_id: UUID,
        query: str
    ) -> str:
        """Get relevant context from knowledge base using RAG"""
        try:
            # Generate embedding for query
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Search knowledge base
            results = await db_service.search_knowledge_base(
                business_id,
                query_embedding,
                top_k=settings.rag_top_k
            )
            
            if not results:
                return ""
            
            # Build context from results
            context_parts = []
            for result in results:
                title = result.get("title", "")
                content = result.get("content", "")
                context_parts.append(f"**{title}**\n{content}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            return ""
    
    async def _classify_intent(
        self,
        message: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Classify user intent and extract entities"""
        try:
            prompt = f"""Classify the intent of this message and extract key entities.

Message: "{message}"

Possible intents: general_inquiry, order, reservation, support, complaint, feedback, product_info, hours, location, pricing

Respond in JSON format:
{{
    "intent": "intent_name",
    "entities": {{
        "key": "value"
    }}
}}
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return result.get("intent", "general_inquiry"), result.get("entities", {})
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "general_inquiry", {}
    
    async def _analyze_sentiment(self, message: str) -> str:
        """Analyze sentiment of user message"""
        try:
            prompt = f"""Analyze the sentiment of this message. Respond with only one word: positive, neutral, or negative.

Message: "{message}"
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            
            if sentiment not in ["positive", "neutral", "negative"]:
                sentiment = "neutral"
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "neutral"
    
    async def _determine_actions(
        self,
        intent: str,
        entities: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine actions to take based on intent"""
        actions = []
        
        # Map intents to actions
        action_mapping = {
            "order": {"type": "create_order", "priority": "high"},
            "reservation": {"type": "create_reservation", "priority": "high"},
            "support": {"type": "escalate_to_agent", "priority": "medium"},
            "complaint": {"type": "escalate_to_agent", "priority": "high"},
            "product_info": {"type": "show_products", "priority": "low"},
            "hours": {"type": "show_hours", "priority": "low"},
            "location": {"type": "show_location", "priority": "low"}
        }
        
        if intent in action_mapping:
            action = action_mapping[intent].copy()
            action["entities"] = entities
            actions.append(action)
        
        return actions
    
    async def generate_suggestions(
        self,
        session_id: str,
        business_id: UUID
    ) -> List[str]:
        """Generate contextual suggestions for user"""
        try:
            business_context = await db_service.get_business_context(business_id)
            if not business_context:
                return []
            
            business = business_context.get("business", {})
            category = business.get("business_categories", {}).get("name", "business")
            
            # Generate category-specific suggestions
            suggestions = []
            
            if "restaurant" in category.lower():
                suggestions = [
                    "View menu",
                    "Make a reservation",
                    "Check today's specials",
                    "See business hours"
                ]
            elif "salon" in category.lower():
                suggestions = [
                    "Book an appointment",
                    "View services",
                    "See available times",
                    "Check pricing"
                ]
            else:
                suggestions = [
                    "Browse products/services",
                    "Contact information",
                    "Business hours",
                    "Get directions"
                ]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []


# Global AI service instance
ai_service = AIService()
