"""
Temporal Workflow Integration for AI Orchestration

Enterprise-grade durable workflow orchestration integrating AI operations
with long-running business processes.
"""

from typing import Dict, Any, List, Optional
from datetime import timedelta, datetime
from dataclasses import dataclass

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.common import RetryPolicy

from app.config import settings
from app.utils import logger
from app.services.langgraph_orchestrator import langgraph_orchestrator
from app.services.crew_orchestrator import crew_orchestrator
from app.services.haystack_rag import rag_service
from app.services.dspy_prompts import dspy_service


# Workflow Input/Output Data Classes
@dataclass
class AIWorkflowInput:
    """Input for AI-powered workflows"""
    workflow_type: str
    business_id: str
    user_id: Optional[str]
    input_data: Dict[str, Any]
    context: Dict[str, Any]


@dataclass
class BusinessOnboardingInput:
    """Business onboarding workflow input"""
    business_name: str
    business_type: str
    category: str
    location: str
    contact_info: Dict[str, str]
    owner_id: str


@dataclass
class CustomerEngagementInput:
    """Customer engagement workflow input"""
    customer_id: str
    business_id: str
    channel: str  # whatsapp, instagram, qr, voice, web
    message: str
    context: Dict[str, Any]


@dataclass
class OrderIntelligenceInput:
    """AI-powered order processing input"""
    order_id: str
    customer_id: str
    business_id: str
    raw_order_text: str  # Natural language order
    channel: str


# Activities - AI Operations
@activity.defn
async def execute_langgraph_workflow(
    workflow_name: str,
    message: str,
    session_id: str,
    user_id: Optional[str] = None,
    business_id: Optional[str] = None
) -> Dict[str, Any]:
    """Execute LangGraph workflow"""
    try:
        logger.info(f"Executing LangGraph workflow: {workflow_name}")
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name=workflow_name,
            initial_message=message,
            session_id=session_id,
            user_id=user_id,
            business_id=business_id
        )
        return result
    except Exception as e:
        logger.error(f"LangGraph workflow error: {e}")
        raise


@activity.defn
async def execute_crew_ai_analysis(
    analysis_type: str,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute Crew AI multi-agent analysis"""
    try:
        logger.info(f"Executing Crew AI analysis: {analysis_type}")
        
        if analysis_type == "business_onboarding":
            return await crew_orchestrator.execute_business_onboarding(input_data)
        elif analysis_type == "customer_support":
            return await crew_orchestrator.execute_customer_support(
                customer_query=input_data.get("query", ""),
                business_context=input_data.get("business_context", {})
            )
        elif analysis_type == "order_processing":
            return await crew_orchestrator.execute_order_processing(input_data)
        elif analysis_type == "analytics":
            return await crew_orchestrator.execute_analytics_insights(
                business_id=input_data.get("business_id", ""),
                analytics_data=input_data.get("analytics_data", {})
            )
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
            
    except Exception as e:
        logger.error(f"Crew AI analysis error: {e}")
        raise


@activity.defn
async def perform_rag_query(
    query: str,
    business_id: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """Perform RAG query against knowledge base"""
    try:
        logger.info(f"Performing RAG query: {query[:100]}...")
        result = await rag_service.query(
            query=query,
            top_k=top_k,
            filters={"business_id": business_id} if business_id else None
        )
        return result
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise


@activity.defn
async def extract_order_from_natural_language(
    order_text: str,
    business_id: str
) -> Dict[str, Any]:
    """Extract structured order from natural language using DSPy"""
    try:
        logger.info("Extracting order from natural language")
        
        # Get business context via RAG
        business_info = await rag_service.query(
            query=f"Get menu and product information for business {business_id}",
            top_k=10
        )
        
        # Use DSPy to process order
        result = await dspy_service.process_order(
            order_details={"raw_text": order_text},
            business_info={"business_id": business_id, "context": business_info}
        )
        
        return result
    except Exception as e:
        logger.error(f"Order extraction error: {e}")
        raise


@activity.defn
async def analyze_customer_sentiment(
    text: str
) -> Dict[str, Any]:
    """Analyze customer sentiment using DSPy"""
    try:
        result = await dspy_service.analyze_sentiment(text)
        return result
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise


@activity.defn
async def generate_ai_response(
    query: str,
    context: Dict[str, Any]
) -> str:
    """Generate AI response with context"""
    try:
        logger.info("Generating AI response")
        result = await dspy_service.process_business_query(
            query=query,
            context=str(context)
        )
        return result.get("answer", "")
    except Exception as e:
        logger.error(f"AI response generation error: {e}")
        raise


# Temporal Workflows
@workflow.defn
class AIBusinessOnboardingWorkflow:
    """
    Complete AI-powered business onboarding workflow
    
    Steps:
    1. Collect business information via AI chat (LangGraph)
    2. Analyze business needs (Crew AI)
    3. Generate onboarding plan
    4. Set up knowledge base (Haystack RAG)
    5. Configure AI features
    6. Create welcome materials
    """
    
    @workflow.run
    async def run(self, input_data: BusinessOnboardingInput) -> Dict[str, Any]:
        """Execute AI business onboarding"""
        
        workflow.logger.info(f"Starting AI onboarding for {input_data.business_name}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3
        )
        
        try:
            # Step 1: Execute LangGraph onboarding conversation
            langgraph_result = await workflow.execute_activity(
                execute_langgraph_workflow,
                args=["business_onboarding", input_data.business_name, f"session_{input_data.owner_id}"],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy
            )
            
            # Step 2: Crew AI analysis for strategic planning
            crew_input = {
                "name": input_data.business_name,
                "business_type": input_data.business_type,
                "category": input_data.category,
                "location": input_data.location
            }
            
            crew_result = await workflow.execute_activity(
                execute_crew_ai_analysis,
                args=["business_onboarding", crew_input],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy
            )
            
            workflow.logger.info(f"Onboarding complete for {input_data.business_name}")
            
            return {
                "success": True,
                "business_name": input_data.business_name,
                "conversation_result": langgraph_result,
                "strategic_plan": crew_result,
                "status": "onboarded"
            }
            
        except Exception as e:
            workflow.logger.error(f"Onboarding failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "business_name": input_data.business_name
            }


@workflow.defn
class CustomerEngagementWorkflow:
    """
    Multi-channel customer engagement workflow
    
    Handles customer interactions across all channels (WhatsApp, Instagram, QR, Voice, Web)
    with AI-powered responses and sentiment analysis.
    """
    
    @workflow.run
    async def run(self, input_data: CustomerEngagementInput) -> Dict[str, Any]:
        """Execute customer engagement workflow"""
        
        workflow.logger.info(f"Customer engagement via {input_data.channel}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3
        )
        
        try:
            # Step 1: Analyze sentiment
            sentiment_result = await workflow.execute_activity(
                analyze_customer_sentiment,
                args=[input_data.message],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            # Step 2: Get relevant context via RAG
            rag_result = await workflow.execute_activity(
                perform_rag_query,
                args=[input_data.message, input_data.business_id, 5],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            # Step 3: Generate AI response
            context = {
                "sentiment": sentiment_result,
                "knowledge": rag_result,
                "channel": input_data.channel,
                **input_data.context
            }
            
            ai_response = await workflow.execute_activity(
                generate_ai_response,
                args=[input_data.message, context],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy
            )
            
            return {
                "success": True,
                "response": ai_response,
                "sentiment": sentiment_result,
                "channel": input_data.channel,
                "customer_id": input_data.customer_id
            }
            
        except Exception as e:
            workflow.logger.error(f"Customer engagement failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "We're experiencing technical difficulties. A team member will assist you shortly."
            }


@workflow.defn
class OrderIntelligenceWorkflow:
    """
    AI-powered order processing workflow
    
    Extracts order from natural language, validates, and processes with AI assistance.
    """
    
    @workflow.run
    async def run(self, input_data: OrderIntelligenceInput) -> Dict[str, Any]:
        """Execute AI order processing"""
        
        workflow.logger.info(f"Processing AI order: {input_data.order_id}")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3
        )
        
        try:
            # Step 1: Extract structured order from natural language
            order_extraction = await workflow.execute_activity(
                extract_order_from_natural_language,
                args=[input_data.raw_order_text, input_data.business_id],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy
            )
            
            # Step 2: Validate and process with Crew AI
            crew_input = {
                "order_id": input_data.order_id,
                "items": order_extraction.get("items", []),
                "customer_id": input_data.customer_id,
                "business_id": input_data.business_id,
                "total_amount": order_extraction.get("total", 0.0)
            }
            
            processing_result = await workflow.execute_activity(
                execute_crew_ai_analysis,
                args=["order_processing", crew_input],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy
            )
            
            return {
                "success": True,
                "order_id": input_data.order_id,
                "extracted_order": order_extraction,
                "processing_result": processing_result,
                "channel": input_data.channel
            }
            
        except Exception as e:
            workflow.logger.error(f"Order intelligence failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "order_id": input_data.order_id
            }


class TemporalOrchestrator:
    """
    Temporal workflow manager for AI orchestration service
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.worker: Optional[Worker] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Temporal client and worker"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing Temporal orchestrator")
            
            # Connect to Temporal server
            self.client = await Client.connect(
                f"{settings.temporal_host}:{settings.temporal_port}",
                namespace=settings.temporal_namespace
            )
            
            logger.info("Temporal client connected")
            
            # Create worker for AI workflows
            self.worker = Worker(
                self.client,
                task_queue="ai-orchestration-queue",
                workflows=[
                    AIBusinessOnboardingWorkflow,
                    CustomerEngagementWorkflow,
                    OrderIntelligenceWorkflow
                ],
                activities=[
                    execute_langgraph_workflow,
                    execute_crew_ai_analysis,
                    perform_rag_query,
                    extract_order_from_natural_language,
                    analyze_customer_sentiment,
                    generate_ai_response
                ]
            )
            
            self._initialized = True
            logger.info("Temporal orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Temporal orchestrator: {e}")
            raise
    
    async def start_worker(self):
        """Start Temporal worker"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting Temporal worker...")
        await self.worker.run()
    
    async def execute_business_onboarding(
        self,
        input_data: BusinessOnboardingInput
    ) -> str:
        """Start business onboarding workflow"""
        if not self._initialized:
            await self.initialize()
        
        workflow_id = f"onboarding_{input_data.business_name}_{datetime.utcnow().timestamp()}"
        
        handle = await self.client.start_workflow(
            AIBusinessOnboardingWorkflow.run,
            input_data,
            id=workflow_id,
            task_queue="ai-orchestration-queue"
        )
        
        logger.info(f"Started onboarding workflow: {workflow_id}")
        return workflow_id
    
    async def execute_customer_engagement(
        self,
        input_data: CustomerEngagementInput
    ) -> str:
        """Start customer engagement workflow"""
        if not self._initialized:
            await self.initialize()
        
        workflow_id = f"engagement_{input_data.customer_id}_{datetime.utcnow().timestamp()}"
        
        handle = await self.client.start_workflow(
            CustomerEngagementWorkflow.run,
            input_data,
            id=workflow_id,
            task_queue="ai-orchestration-queue"
        )
        
        logger.info(f"Started engagement workflow: {workflow_id}")
        return workflow_id
    
    async def execute_order_intelligence(
        self,
        input_data: OrderIntelligenceInput
    ) -> str:
        """Start AI order processing workflow"""
        if not self._initialized:
            await self.initialize()
        
        workflow_id = f"order_ai_{input_data.order_id}"
        
        handle = await self.client.start_workflow(
            OrderIntelligenceWorkflow.run,
            input_data,
            id=workflow_id,
            task_queue="ai-orchestration-queue"
        )
        
        logger.info(f"Started order intelligence workflow: {workflow_id}")
        return workflow_id
    
    async def get_workflow_result(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Get workflow result"""
        if not self._initialized:
            await self.initialize()
        
        handle = self.client.get_workflow_handle(workflow_id)
        result = await handle.result()
        return result


# Global Temporal orchestrator instance
temporal_orchestrator = TemporalOrchestrator()
