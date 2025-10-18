"""
LangGraph Orchestrator

Implements graph-based AI workflows for complex decision-making and multi-step processes.
Integrates with Redis for state management and memory persistence.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
from app.core.redis_client import redis_client
from app.core.llm_provider import llm_manager
from app.config import settings
from app.utils import logger
import json
from datetime import datetime


class GraphState(TypedDict):
    """State schema for LangGraph workflows"""
    messages: Annotated[List[Dict[str, Any]], operator.add]
    context: Dict[str, Any]
    current_step: str
    user_id: Optional[str]
    business_id: Optional[str]
    session_id: str
    metadata: Dict[str, Any]


class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator for AI workflows
    
    Manages complex multi-step AI processes with branching logic,
    state persistence, and memory management via Redis.
    """
    
    def __init__(self):
        self.graphs: Dict[str, StateGraph] = {}
        self.memory_saver = MemorySaver()
        self._initialize_workflows()
    
    def _initialize_workflows(self) -> None:
        """Initialize predefined workflows"""
        self.graphs["business_onboarding"] = self._create_onboarding_workflow()
        self.graphs["customer_support"] = self._create_support_workflow()
        self.graphs["order_processing"] = self._create_order_workflow()
        logger.info("LangGraph workflows initialized")
    
    def _create_onboarding_workflow(self) -> StateGraph:
        """
        Create business onboarding workflow
        
        Flow: Welcome -> Collect Info -> Validate -> Setup -> Complete
        """
        workflow = StateGraph(GraphState)
        
        # Define nodes
        workflow.add_node("welcome", self._welcome_node)
        workflow.add_node("collect_info", self._collect_business_info)
        workflow.add_node("validate", self._validate_business_info)
        workflow.add_node("setup", self._setup_business)
        workflow.add_node("complete", self._complete_onboarding)
        
        # Define edges
        workflow.set_entry_point("welcome")
        workflow.add_edge("welcome", "collect_info")
        workflow.add_conditional_edges(
            "collect_info",
            self._should_validate,
            {
                "validate": "validate",
                "collect_more": "collect_info"
            }
        )
        workflow.add_conditional_edges(
            "validate",
            self._is_valid,
            {
                "setup": "setup",
                "retry": "collect_info"
            }
        )
        workflow.add_edge("setup", "complete")
        workflow.add_edge("complete", END)
        
        return workflow.compile(checkpointer=self.memory_saver)
    
    def _create_support_workflow(self) -> StateGraph:
        """
        Create customer support workflow
        
        Flow: Analyze Query -> Retrieve Context -> Generate Response -> Validate
        """
        workflow = StateGraph(GraphState)
        
        workflow.add_node("analyze", self._analyze_query)
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("generate", self._generate_response)
        workflow.add_node("validate", self._validate_response)
        
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._is_response_valid,
            {
                "end": END,
                "regenerate": "generate"
            }
        )
        
        return workflow.compile(checkpointer=self.memory_saver)
    
    def _create_order_workflow(self) -> StateGraph:
        """
        Create order processing workflow
        
        Flow: Parse Order -> Check Inventory -> Calculate Price -> Confirm
        """
        workflow = StateGraph(GraphState)
        
        workflow.add_node("parse", self._parse_order)
        workflow.add_node("check_inventory", self._check_inventory)
        workflow.add_node("calculate", self._calculate_price)
        workflow.add_node("confirm", self._confirm_order)
        
        workflow.set_entry_point("parse")
        workflow.add_edge("parse", "check_inventory")
        workflow.add_conditional_edges(
            "check_inventory",
            self._has_inventory,
            {
                "calculate": "calculate",
                "out_of_stock": END
            }
        )
        workflow.add_edge("calculate", "confirm")
        workflow.add_edge("confirm", END)
        
        return workflow.compile(checkpointer=self.memory_saver)
    
    # Node implementations
    async def _welcome_node(self, state: GraphState) -> GraphState:
        """Welcome message for onboarding"""
        welcome_msg = await llm_manager.generate(
            prompt="Generate a warm welcome message for a new business owner starting their onboarding process.",
            system_message="You are a friendly AI assistant helping businesses get started.",
            temperature=0.8
        )
        
        state["messages"].append({
            "role": "assistant",
            "content": welcome_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        state["current_step"] = "welcome"
        
        # Cache in Redis
        await self._save_state_to_redis(state)
        
        return state
    
    async def _collect_business_info(self, state: GraphState) -> GraphState:
        """Collect business information"""
        last_message = state["messages"][-1]["content"] if state["messages"] else ""
        
        prompt = f"""
        Based on the conversation so far, extract business information.
        Last user message: {last_message}
        
        Extract: business_name, category, location, contact_info
        Return as JSON.
        """
        
        response = await llm_manager.generate(
            prompt=prompt,
            system_message="You are an information extraction assistant.",
            temperature=0.3
        )
        
        try:
            extracted_info = json.loads(response)
            state["context"]["business_info"] = extracted_info
        except json.JSONDecodeError:
            logger.warning("Failed to parse business info")
        
        state["current_step"] = "collect_info"
        await self._save_state_to_redis(state)
        
        return state
    
    async def _validate_business_info(self, state: GraphState) -> GraphState:
        """Validate collected business information"""
        business_info = state["context"].get("business_info", {})
        
        required_fields = ["business_name", "category", "location"]
        is_valid = all(field in business_info for field in required_fields)
        
        state["context"]["validation_passed"] = is_valid
        state["current_step"] = "validate"
        
        await self._save_state_to_redis(state)
        return state
    
    async def _setup_business(self, state: GraphState) -> GraphState:
        """Setup business in system"""
        business_info = state["context"].get("business_info", {})
        
        # Here you would integrate with Supabase to create business record
        # For now, simulate setup
        state["context"]["business_id"] = f"biz_{datetime.utcnow().timestamp()}"
        state["current_step"] = "setup"
        
        setup_msg = f"Great! Your business '{business_info.get('business_name')}' has been set up successfully."
        state["messages"].append({
            "role": "assistant",
            "content": setup_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await self._save_state_to_redis(state)
        return state
    
    async def _complete_onboarding(self, state: GraphState) -> GraphState:
        """Complete onboarding process"""
        state["current_step"] = "complete"
        state["context"]["onboarding_completed"] = True
        
        completion_msg = "Onboarding complete! You're all set to start using the platform."
        state["messages"].append({
            "role": "assistant",
            "content": completion_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await self._save_state_to_redis(state)
        return state
    
    async def _analyze_query(self, state: GraphState) -> GraphState:
        """Analyze customer query"""
        last_message = state["messages"][-1]["content"] if state["messages"] else ""
        
        analysis = await llm_manager.generate(
            prompt=f"Analyze this customer query and categorize it: {last_message}",
            system_message="You are a query analysis assistant. Categorize as: order, reservation, inquiry, complaint, or other.",
            temperature=0.3
        )
        
        state["context"]["query_analysis"] = analysis
        state["current_step"] = "analyze"
        
        await self._save_state_to_redis(state)
        return state
    
    async def _retrieve_context(self, state: GraphState) -> GraphState:
        """Retrieve relevant context from knowledge base"""
        # This would integrate with Haystack RAG
        # For now, simulate context retrieval
        state["context"]["retrieved_docs"] = [
            {"content": "Business hours: 9 AM - 9 PM", "score": 0.9},
            {"content": "Menu items available", "score": 0.85}
        ]
        state["current_step"] = "retrieve"
        
        await self._save_state_to_redis(state)
        return state
    
    async def _generate_response(self, state: GraphState) -> GraphState:
        """Generate AI response"""
        query = state["messages"][-1]["content"] if state["messages"] else ""
        context = state["context"].get("retrieved_docs", [])
        
        context_str = "\n".join([doc["content"] for doc in context])
        
        response = await llm_manager.generate(
            prompt=f"Query: {query}\n\nContext: {context_str}\n\nProvide a helpful response.",
            system_message="You are a helpful customer support assistant.",
            temperature=0.7
        )
        
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        state["current_step"] = "generate"
        
        await self._save_state_to_redis(state)
        return state
    
    async def _validate_response(self, state: GraphState) -> GraphState:
        """Validate generated response quality"""
        # Simple validation - in production, use LangChain evaluators
        last_response = state["messages"][-1]["content"]
        is_valid = len(last_response) > 20  # Basic check
        
        state["context"]["response_valid"] = is_valid
        state["current_step"] = "validate"
        
        await self._save_state_to_redis(state)
        return state
    
    async def _parse_order(self, state: GraphState) -> GraphState:
        """Parse order from message"""
        last_message = state["messages"][-1]["content"] if state["messages"] else ""
        
        parsed = await llm_manager.generate(
            prompt=f"Extract order items and quantities from: {last_message}. Return as JSON.",
            system_message="You are an order parsing assistant.",
            temperature=0.2
        )
        
        try:
            order_data = json.loads(parsed)
            state["context"]["order"] = order_data
        except json.JSONDecodeError:
            state["context"]["order"] = {}
        
        state["current_step"] = "parse"
        await self._save_state_to_redis(state)
        return state
    
    async def _check_inventory(self, state: GraphState) -> GraphState:
        """Check inventory availability"""
        # Simulate inventory check
        state["context"]["inventory_available"] = True
        state["current_step"] = "check_inventory"
        
        await self._save_state_to_redis(state)
        return state
    
    async def _calculate_price(self, state: GraphState) -> GraphState:
        """Calculate order price"""
        # Simulate price calculation
        state["context"]["total_price"] = 25.99
        state["current_step"] = "calculate"
        
        await self._save_state_to_redis(state)
        return state
    
    async def _confirm_order(self, state: GraphState) -> GraphState:
        """Confirm order"""
        total = state["context"].get("total_price", 0)
        
        confirmation = f"Order confirmed! Total: ${total:.2f}"
        state["messages"].append({
            "role": "assistant",
            "content": confirmation,
            "timestamp": datetime.utcnow().isoformat()
        })
        state["current_step"] = "confirm"
        
        await self._save_state_to_redis(state)
        return state
    
    # Conditional edge functions
    def _should_validate(self, state: GraphState) -> str:
        """Check if enough info collected"""
        business_info = state["context"].get("business_info", {})
        if len(business_info) >= 3:
            return "validate"
        return "collect_more"
    
    def _is_valid(self, state: GraphState) -> str:
        """Check if validation passed"""
        if state["context"].get("validation_passed", False):
            return "setup"
        return "retry"
    
    def _is_response_valid(self, state: GraphState) -> str:
        """Check if response is valid"""
        if state["context"].get("response_valid", False):
            return "end"
        return "regenerate"
    
    def _has_inventory(self, state: GraphState) -> str:
        """Check inventory availability"""
        if state["context"].get("inventory_available", False):
            return "calculate"
        return "out_of_stock"
    
    # State management
    async def _save_state_to_redis(self, state: GraphState) -> None:
        """Save workflow state to Redis"""
        session_id = state.get("session_id", "default")
        key = f"langgraph:state:{session_id}"
        
        # Serialize state
        state_json = {
            "messages": state["messages"],
            "context": state["context"],
            "current_step": state["current_step"],
            "metadata": state.get("metadata", {})
        }
        
        await redis_client.set_json(key, state_json, ttl=settings.redis_ttl)
    
    async def load_state_from_redis(self, session_id: str) -> Optional[GraphState]:
        """Load workflow state from Redis"""
        key = f"langgraph:state:{session_id}"
        state_json = await redis_client.get_json(key)
        
        if state_json:
            return GraphState(
                messages=state_json.get("messages", []),
                context=state_json.get("context", {}),
                current_step=state_json.get("current_step", ""),
                session_id=session_id,
                metadata=state_json.get("metadata", {})
            )
        return None
    
    async def execute_workflow(
        self,
        workflow_name: str,
        initial_message: str,
        session_id: str,
        user_id: Optional[str] = None,
        business_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            workflow_name: Name of workflow to execute
            initial_message: Initial user message
            session_id: Session identifier
            user_id: Optional user ID
            business_id: Optional business ID
        
        Returns:
            Workflow result with messages and context
        """
        if workflow_name not in self.graphs:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        # Load or create state
        state = await self.load_state_from_redis(session_id)
        
        if not state:
            state = GraphState(
                messages=[{
                    "role": "user",
                    "content": initial_message,
                    "timestamp": datetime.utcnow().isoformat()
                }],
                context={},
                current_step="start",
                user_id=user_id,
                business_id=business_id,
                session_id=session_id,
                metadata={}
            )
        else:
            # Add new message to existing state
            state["messages"].append({
                "role": "user",
                "content": initial_message,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Execute workflow
        graph = self.graphs[workflow_name]
        
        try:
            result = await graph.ainvoke(
                state,
                config={"configurable": {"thread_id": session_id}}
            )
            
            return {
                "status": "success",
                "messages": result["messages"],
                "context": result["context"],
                "current_step": result["current_step"]
            }
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "messages": state["messages"]
            }


# Global orchestrator instance
langgraph_orchestrator = LangGraphOrchestrator()
