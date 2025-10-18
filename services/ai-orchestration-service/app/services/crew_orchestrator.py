"""
Crew AI Multi-Agent Orchestrator

Enterprise-grade multi-agent system for complex business workflows.
Implements specialized agents for different business domains with collaborative task execution.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.config import settings
from app.utils import logger


class CrewAIOrchestrator:
    """
    Production-grade Crew AI orchestrator for multi-agent workflows
    
    Features:
    - Specialized agents for different business domains
    - Collaborative task execution
    - Sequential and parallel processing
    - Memory and context sharing between agents
    - Integration with business logic and data sources
    """
    
    def __init__(self):
        self.llm = None
        self.agents: Dict[str, Agent] = {}
        self.crews: Dict[str, Crew] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize Crew AI with agents and crews"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing Crew AI orchestrator")
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.openai_api_key,
                temperature=0.7
            )
            
            # Create specialized agents
            self._create_agents()
            
            # Create crew workflows
            self._create_crews()
            
            self._initialized = True
            logger.info("Crew AI orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Crew AI: {e}", exc_info=True)
            raise
    
    def _create_agents(self):
        """Create specialized AI agents"""
        
        # Business Analyst Agent
        self.agents["business_analyst"] = Agent(
            role="Business Analyst",
            goal="Analyze business requirements and provide strategic insights",
            backstory="""You are an experienced business analyst with expertise in 
            restaurant, salon, and retail operations. You excel at understanding 
            business needs and translating them into actionable requirements.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )
        
        # Customer Service Agent
        self.agents["customer_service"] = Agent(
            role="Customer Service Specialist",
            goal="Provide exceptional customer support and resolve queries efficiently",
            backstory="""You are a friendly and knowledgeable customer service expert 
            who specializes in handling customer inquiries, complaints, and requests 
            for various business types including restaurants, salons, and retail stores.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Order Management Agent
        self.agents["order_manager"] = Agent(
            role="Order Management Specialist",
            goal="Process orders accurately and ensure smooth fulfillment",
            backstory="""You are an expert in order processing and fulfillment with 
            deep knowledge of inventory management, pricing, and delivery logistics. 
            You ensure every order is processed correctly and efficiently.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )
        
        # Reservation Coordinator Agent
        self.agents["reservation_coordinator"] = Agent(
            role="Reservation Coordinator",
            goal="Manage reservations and appointments efficiently",
            backstory="""You are a skilled reservation coordinator who manages 
            bookings for restaurants, salons, and service businesses. You optimize 
            scheduling to maximize capacity while ensuring customer satisfaction.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Marketing Strategist Agent
        self.agents["marketing_strategist"] = Agent(
            role="Marketing Strategist",
            goal="Develop and execute effective marketing campaigns",
            backstory="""You are a creative marketing strategist with expertise in 
            digital marketing, customer engagement, and brand building for local 
            businesses. You create compelling campaigns that drive customer acquisition.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )
        
        # Data Analyst Agent
        self.agents["data_analyst"] = Agent(
            role="Data Analyst",
            goal="Analyze business data and provide actionable insights",
            backstory="""You are a data analyst specializing in business intelligence 
            and analytics. You transform raw data into meaningful insights that help 
            businesses make informed decisions.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Quality Assurance Agent
        self.agents["qa_specialist"] = Agent(
            role="Quality Assurance Specialist",
            goal="Ensure high quality standards and customer satisfaction",
            backstory="""You are a quality assurance expert who monitors service 
            quality, reviews customer feedback, and ensures businesses maintain 
            high standards across all operations.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )
        
        logger.info(f"Created {len(self.agents)} specialized agents")
    
    def _create_crews(self):
        """Create crew workflows for different scenarios"""
        
        # Customer Support Crew
        self.crews["customer_support"] = Crew(
            agents=[
                self.agents["customer_service"],
                self.agents["order_manager"],
                self.agents["reservation_coordinator"]
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Business Onboarding Crew
        self.crews["business_onboarding"] = Crew(
            agents=[
                self.agents["business_analyst"],
                self.agents["marketing_strategist"],
                self.agents["data_analyst"]
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Order Processing Crew
        self.crews["order_processing"] = Crew(
            agents=[
                self.agents["order_manager"],
                self.agents["customer_service"],
                self.agents["qa_specialist"]
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Analytics & Insights Crew
        self.crews["analytics"] = Crew(
            agents=[
                self.agents["data_analyst"],
                self.agents["business_analyst"],
                self.agents["marketing_strategist"]
            ],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info(f"Created {len(self.crews)} crew workflows")
    
    async def execute_customer_support(
        self,
        customer_query: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute customer support workflow
        
        Args:
            customer_query: Customer's question or issue
            business_context: Business information and context
        
        Returns:
            Dictionary with support response and actions
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Executing customer support crew workflow")
            
            # Create tasks
            analyze_task = Task(
                description=f"""Analyze this customer query and determine the type of support needed:
                Query: {customer_query}
                Business: {business_context.get('business_name', 'Unknown')}
                Business Type: {business_context.get('business_type', 'general')}
                
                Categorize the query and identify required actions.""",
                agent=self.agents["customer_service"],
                expected_output="Query analysis with category and required actions"
            )
            
            resolve_task = Task(
                description=f"""Based on the query analysis, provide a comprehensive solution:
                - If it's an order issue, check order status and provide updates
                - If it's a reservation, check availability and confirm booking
                - Provide clear, helpful response to the customer
                
                Business context: {business_context}""",
                agent=self.agents["order_manager"],
                expected_output="Detailed solution and customer response"
            )
            
            quality_task = Task(
                description="""Review the proposed solution for quality and customer satisfaction:
                - Ensure response is clear and helpful
                - Verify all customer concerns are addressed
                - Suggest improvements if needed""",
                agent=self.agents["qa_specialist"],
                expected_output="Quality review and final customer response"
            )
            
            # Execute crew
            crew = Crew(
                agents=[
                    self.agents["customer_service"],
                    self.agents["order_manager"],
                    self.agents["qa_specialist"]
                ],
                tasks=[analyze_task, resolve_task, quality_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "success",
                "response": str(result),
                "workflow": "customer_support",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Customer support crew error: {e}", exc_info=True)
            raise
    
    async def execute_business_onboarding(
        self,
        business_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute business onboarding workflow
        
        Args:
            business_info: New business information
        
        Returns:
            Dictionary with onboarding plan and recommendations
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Executing business onboarding crew workflow")
            
            # Create tasks
            analysis_task = Task(
                description=f"""Analyze this new business and create an onboarding strategy:
                Business Name: {business_info.get('name')}
                Business Type: {business_info.get('business_type')}
                Category: {business_info.get('category')}
                Location: {business_info.get('location')}
                
                Provide strategic recommendations for successful platform adoption.""",
                agent=self.agents["business_analyst"],
                expected_output="Business analysis and onboarding strategy"
            )
            
            marketing_task = Task(
                description="""Based on the business analysis, create a marketing plan:
                - Identify target audience
                - Suggest promotional strategies
                - Recommend engagement tactics
                - Outline customer acquisition approach""",
                agent=self.agents["marketing_strategist"],
                expected_output="Comprehensive marketing plan"
            )
            
            analytics_task = Task(
                description="""Set up analytics framework for the business:
                - Define key performance indicators (KPIs)
                - Establish tracking metrics
                - Create reporting dashboard structure
                - Set success benchmarks""",
                agent=self.agents["data_analyst"],
                expected_output="Analytics framework and KPI definitions"
            )
            
            # Execute crew
            crew = Crew(
                agents=[
                    self.agents["business_analyst"],
                    self.agents["marketing_strategist"],
                    self.agents["data_analyst"]
                ],
                tasks=[analysis_task, marketing_task, analytics_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "success",
                "onboarding_plan": str(result),
                "workflow": "business_onboarding",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Business onboarding crew error: {e}", exc_info=True)
            raise
    
    async def execute_order_processing(
        self,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute order processing workflow
        
        Args:
            order_data: Order information
        
        Returns:
            Dictionary with order processing result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Executing order processing crew workflow")
            
            # Create tasks
            process_task = Task(
                description=f"""Process this order and verify all details:
                Order Items: {order_data.get('items')}
                Customer: {order_data.get('customer_id')}
                Business: {order_data.get('business_id')}
                
                Validate inventory, calculate pricing, and prepare order confirmation.""",
                agent=self.agents["order_manager"],
                expected_output="Order validation and confirmation details"
            )
            
            customer_comm_task = Task(
                description="""Create customer communication for the order:
                - Generate order confirmation message
                - Provide estimated delivery/pickup time
                - Include any special instructions
                - Add contact information for support""",
                agent=self.agents["customer_service"],
                expected_output="Customer communication message"
            )
            
            quality_check_task = Task(
                description="""Perform quality check on the order:
                - Verify order accuracy
                - Check for any issues or concerns
                - Ensure customer satisfaction measures are in place
                - Approve for fulfillment""",
                agent=self.agents["qa_specialist"],
                expected_output="Quality check report and approval"
            )
            
            # Execute crew
            crew = Crew(
                agents=[
                    self.agents["order_manager"],
                    self.agents["customer_service"],
                    self.agents["qa_specialist"]
                ],
                tasks=[process_task, customer_comm_task, quality_check_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "success",
                "order_result": str(result),
                "workflow": "order_processing",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Order processing crew error: {e}", exc_info=True)
            raise
    
    async def execute_analytics_insights(
        self,
        business_id: str,
        analytics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute analytics and insights workflow
        
        Args:
            business_id: Business identifier
            analytics_data: Analytics data to process
        
        Returns:
            Dictionary with insights and recommendations
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Executing analytics insights crew workflow")
            
            # Create tasks
            data_analysis_task = Task(
                description=f"""Analyze business performance data:
                Business ID: {business_id}
                Metrics: {analytics_data.get('metrics', {})}
                Time Period: {analytics_data.get('period', 'last_30_days')}
                
                Identify trends, patterns, and key insights.""",
                agent=self.agents["data_analyst"],
                expected_output="Data analysis with trends and patterns"
            )
            
            business_insights_task = Task(
                description="""Based on the data analysis, provide strategic business insights:
                - Identify growth opportunities
                - Highlight areas of concern
                - Suggest operational improvements
                - Provide competitive analysis""",
                agent=self.agents["business_analyst"],
                expected_output="Strategic business insights and recommendations"
            )
            
            marketing_recommendations_task = Task(
                description="""Create marketing recommendations based on insights:
                - Suggest targeted campaigns
                - Identify customer segments to focus on
                - Recommend promotional strategies
                - Outline engagement tactics""",
                agent=self.agents["marketing_strategist"],
                expected_output="Marketing action plan"
            )
            
            # Execute crew
            crew = Crew(
                agents=[
                    self.agents["data_analyst"],
                    self.agents["business_analyst"],
                    self.agents["marketing_strategist"]
                ],
                tasks=[data_analysis_task, business_insights_task, marketing_recommendations_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "status": "success",
                "insights": str(result),
                "workflow": "analytics_insights",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analytics insights crew error: {e}", exc_info=True)
            raise


# Global Crew AI orchestrator instance
crew_orchestrator = CrewAIOrchestrator()
