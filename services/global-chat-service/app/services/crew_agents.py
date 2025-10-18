"""
Crew AI Agents for Global Chat Service

Production-grade multi-agent system for cross-business interactions
using Crew AI framework.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from crewai_tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.utils import logger


# Custom Tools for Agents
class BusinessSearchTool(BaseTool):
    """Tool for searching businesses"""
    name: str = "business_search"
    description: str = "Search for businesses by name, category, or location"
    
    def _run(self, query: str, category: Optional[str] = None, location: Optional[str] = None) -> str:
        """Execute business search"""
        # TODO: Implement actual Supabase query
        logger.info(f"Searching businesses: query={query}, category={category}, location={location}")
        
        # Mock response for now
        return f"Found 3 businesses matching '{query}' in category '{category or 'all'}'"


class AvailabilityCheckTool(BaseTool):
    """Tool for checking availability"""
    name: str = "availability_check"
    description: str = "Check availability for reservations or appointments"
    
    def _run(self, business_id: str, date: str, time: str) -> str:
        """Check availability"""
        # TODO: Implement actual availability check
        logger.info(f"Checking availability: business={business_id}, date={date}, time={time}")
        
        return f"Available slots: 10:00 AM, 2:00 PM, 4:00 PM on {date}"


class OrderCreationTool(BaseTool):
    """Tool for creating orders"""
    name: str = "order_creation"
    description: str = "Create orders for products or services"
    
    def _run(self, business_id: str, items: List[Dict], customer_id: str) -> str:
        """Create order"""
        # TODO: Implement actual order creation
        logger.info(f"Creating order: business={business_id}, items={len(items)}, customer={customer_id}")
        
        return f"Order created successfully with ID: ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"


class ReservationTool(BaseTool):
    """Tool for creating reservations"""
    name: str = "reservation_creation"
    description: str = "Create reservations for appointments or bookings"
    
    def _run(self, business_id: str, date: str, time: str, customer_id: str, party_size: int = 1) -> str:
        """Create reservation"""
        # TODO: Implement actual reservation creation
        logger.info(f"Creating reservation: business={business_id}, date={date}, time={time}")
        
        return f"Reservation confirmed for {date} at {time} for {party_size} people"


class RecommendationTool(BaseTool):
    """Tool for generating recommendations"""
    name: str = "recommendation_engine"
    description: str = "Generate personalized recommendations based on user preferences"
    
    def _run(self, user_id: str, category: Optional[str] = None, preferences: Optional[Dict] = None) -> str:
        """Generate recommendations"""
        # TODO: Implement actual recommendation engine
        logger.info(f"Generating recommendations: user={user_id}, category={category}")
        
        return "Top recommendations: Restaurant A (4.8★), Salon B (4.7★), Shop C (4.6★)"


class CrewAIService:
    """
    Production-grade Crew AI service for multi-agent orchestration
    
    Features:
    - Search Agent: Find businesses across platform
    - Booking Agent: Handle reservations and appointments
    - Order Agent: Process orders and purchases
    - Recommendation Agent: Provide personalized suggestions
    - Coordinator Agent: Orchestrate multi-step interactions
    """
    
    def __init__(self):
        """Initialize Crew AI service"""
        self.llm = None
        self.agents = {}
        self.tools = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize LLM and agents"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing Crew AI service")
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=settings.openai_api_key
            )
            
            # Initialize tools
            self.tools = {
                "search": BusinessSearchTool(),
                "availability": AvailabilityCheckTool(),
                "order": OrderCreationTool(),
                "reservation": ReservationTool(),
                "recommendation": RecommendationTool()
            }
            
            # Create agents
            self._create_agents()
            
            self._initialized = True
            logger.info("Crew AI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Crew AI service: {e}", exc_info=True)
            raise
    
    def _create_agents(self):
        """Create specialized agents"""
        
        # Search Agent
        self.agents["search"] = Agent(
            role="Business Search Specialist",
            goal="Find the best businesses matching user requirements",
            backstory="""You are an expert at understanding user needs and finding 
            the perfect businesses across restaurants, salons, shops, and services. 
            You excel at interpreting vague queries and providing relevant results.""",
            tools=[self.tools["search"]],
            llm=self.llm,
            verbose=True
        )
        
        # Booking Agent
        self.agents["booking"] = Agent(
            role="Reservation & Booking Specialist",
            goal="Handle all reservation and appointment bookings efficiently",
            backstory="""You are a professional booking coordinator with years of 
            experience in managing reservations. You ensure smooth booking processes 
            and handle scheduling conflicts gracefully.""",
            tools=[self.tools["availability"], self.tools["reservation"]],
            llm=self.llm,
            verbose=True
        )
        
        # Order Agent
        self.agents["order"] = Agent(
            role="Order Processing Specialist",
            goal="Process orders accurately and efficiently",
            backstory="""You are an experienced order management professional who 
            ensures every order is processed correctly, handles inventory checks, 
            and provides clear order confirmations.""",
            tools=[self.tools["order"]],
            llm=self.llm,
            verbose=True
        )
        
        # Recommendation Agent
        self.agents["recommendation"] = Agent(
            role="Personalization & Recommendation Expert",
            goal="Provide personalized recommendations based on user preferences",
            backstory="""You are a data-driven recommendation specialist who 
            understands user behavior and preferences. You provide tailored 
            suggestions that delight users.""",
            tools=[self.tools["recommendation"]],
            llm=self.llm,
            verbose=True
        )
        
        # Coordinator Agent
        self.agents["coordinator"] = Agent(
            role="Customer Service Coordinator",
            goal="Orchestrate complex multi-step user requests",
            backstory="""You are a senior customer service coordinator who 
            manages complex interactions involving multiple services. You ensure 
            seamless handoffs between specialists and maintain conversation context.""",
            tools=list(self.tools.values()),
            llm=self.llm,
            verbose=True
        )
        
        logger.info(f"Created {len(self.agents)} specialized agents")
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user query using appropriate agents
        
        Args:
            query: User question or request
            user_id: User identifier
            session_id: Session identifier
            context: Optional conversation context
            
        Returns:
            Dictionary with response and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Processing query: {query[:100]}... (user={user_id}, session={session_id})")
            
            # Determine intent and select appropriate agent(s)
            intent = self._classify_intent(query)
            
            # Create task based on intent
            task = self._create_task(query, intent, user_id, context)
            
            # Select agent(s) for the task
            selected_agents = self._select_agents(intent)
            
            # Create crew and execute
            crew = Crew(
                agents=selected_agents,
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute crew
            result = crew.kickoff()
            
            return {
                "response": str(result),
                "intent": intent,
                "agents_used": [agent.role for agent in selected_agents],
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise
    
    def _classify_intent(self, query: str) -> str:
        """Classify user intent from query"""
        query_lower = query.lower()
        
        # Simple keyword-based classification (can be enhanced with ML)
        if any(word in query_lower for word in ["find", "search", "looking for", "show me"]):
            return "search"
        elif any(word in query_lower for word in ["book", "reserve", "appointment", "schedule"]):
            return "booking"
        elif any(word in query_lower for word in ["order", "buy", "purchase", "get"]):
            return "order"
        elif any(word in query_lower for word in ["recommend", "suggest", "best", "top"]):
            return "recommendation"
        else:
            return "general"
    
    def _create_task(
        self,
        query: str,
        intent: str,
        user_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Task:
        """Create task for agents"""
        
        task_descriptions = {
            "search": f"Find businesses matching: {query}. Provide detailed results with ratings and locations.",
            "booking": f"Handle booking request: {query}. Check availability and confirm reservation.",
            "order": f"Process order: {query}. Verify items, check inventory, and create order.",
            "recommendation": f"Provide recommendations for: {query}. Consider user preferences and history.",
            "general": f"Assist with: {query}. Provide helpful and accurate information."
        }
        
        description = task_descriptions.get(intent, task_descriptions["general"])
        
        return Task(
            description=description,
            expected_output="A clear, helpful response addressing the user's request",
            agent=self.agents.get(intent, self.agents["coordinator"])
        )
    
    def _select_agents(self, intent: str) -> List[Agent]:
        """Select appropriate agents for intent"""
        
        agent_mapping = {
            "search": [self.agents["search"]],
            "booking": [self.agents["booking"]],
            "order": [self.agents["order"]],
            "recommendation": [self.agents["recommendation"]],
            "general": [self.agents["coordinator"]]
        }
        
        return agent_mapping.get(intent, [self.agents["coordinator"]])
    
    async def search_businesses(
        self,
        query: str,
        category: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for businesses"""
        if not self._initialized:
            await self.initialize()
        
        result = self.tools["search"]._run(query, category, location)
        
        return {
            "results": result,
            "query": query,
            "category": category,
            "location": location
        }
    
    async def check_availability(
        self,
        business_id: str,
        date: str,
        time: str
    ) -> Dict[str, Any]:
        """Check availability"""
        if not self._initialized:
            await self.initialize()
        
        result = self.tools["availability"]._run(business_id, date, time)
        
        return {
            "availability": result,
            "business_id": business_id,
            "date": date,
            "time": time
        }


# Global Crew AI service instance
crew_service = CrewAIService()
