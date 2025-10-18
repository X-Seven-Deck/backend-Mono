"""
Template Configuration Service

Defines all 4 template configurations with features, endpoints, and widgets.
"""

from typing import Dict, List
from app.models.schemas import (
    TemplateType, TemplateConfiguration, AIFeature, AIFeatureType,
    TemplateAPIEndpoint, DashboardWidget, SubscriptionTier
)


class TemplateConfigurationService:
    """Manages Template Configurations"""
    
    def __init__(self):
        self._templates: Dict[TemplateType, TemplateConfiguration] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize all template configurations"""
        self._templates[TemplateType.FOOD_HOSPITALITY] = self._create_food_hospitality_template()
        self._templates[TemplateType.SERVICE_BASED] = self._create_service_based_template()
        self._templates[TemplateType.RETAIL_ECOMMERCE] = self._create_retail_ecommerce_template()
        self._templates[TemplateType.PROFESSIONAL_SERVICES] = self._create_professional_services_template()
    
    def get_template(self, template_type: TemplateType) -> TemplateConfiguration:
        """Get template configuration"""
        return self._templates.get(template_type)
    
    def get_all_templates(self) -> Dict[TemplateType, TemplateConfiguration]:
        """Get all template configurations"""
        return self._templates
    
    # ==================== UNIVERSAL AI FEATURES ====================
    
    def _get_universal_features(self) -> List[AIFeature]:
        """Get 6 Universal AI Features"""
        return [
            AIFeature(
                feature_type=AIFeatureType.AI_INSIGHT_ENGINE,
                name="AI Insight Engine",
                description="Anomaly detection, root cause analysis, and intelligent business insights",
                is_universal=True,
                applicable_templates=[t for t in TemplateType],
                min_tier=SubscriptionTier.BASIC,
                configuration={
                    "anomaly_detection": True,
                    "root_cause_analysis": True,
                    "trend_prediction": True,
                    "alert_threshold": 0.8
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.PREDICTIVE_INTELLIGENCE,
                name="Predictive Intelligence",
                description="ML-powered forecasting for sales, demand, and business metrics",
                is_universal=True,
                applicable_templates=[t for t in TemplateType],
                min_tier=SubscriptionTier.PREMIUM,
                configuration={
                    "forecast_horizon_days": 30,
                    "confidence_interval": 0.95,
                    "auto_retrain": True
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.AI_AUTOMATION_WORKFLOWS,
                name="AI Automation Workflows",
                description="Intelligent workflow automation with LangGraph and CrewAI",
                is_universal=True,
                applicable_templates=[t for t in TemplateType],
                min_tier=SubscriptionTier.PREMIUM,
                configuration={
                    "max_concurrent_workflows": 10,
                    "auto_recovery": True,
                    "workflow_templates": []
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.AI_COPILOT_CHAT,
                name="AI Copilot Chat",
                description="Conversational AI assistant for business operations",
                is_universal=True,
                applicable_templates=[t for t in TemplateType],
                min_tier=SubscriptionTier.BASIC,
                configuration={
                    "model": "gpt-4",
                    "context_window": 8000,
                    "memory_enabled": True,
                    "multi_language": True
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.AI_GENERATED_REPORTS,
                name="AI-Generated Reports",
                description="Automated report generation with insights and visualizations",
                is_universal=True,
                applicable_templates=[t for t in TemplateType],
                min_tier=SubscriptionTier.PREMIUM,
                configuration={
                    "report_formats": ["pdf", "excel", "html"],
                    "auto_schedule": True,
                    "custom_branding": True
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.AI_BUSINESS_COACH,
                name="AI Business Coach",
                description="Personalized business coaching and strategic recommendations",
                is_universal=True,
                applicable_templates=[t for t in TemplateType],
                min_tier=SubscriptionTier.ENTERPRISE,
                configuration={
                    "coaching_frequency": "weekly",
                    "industry_benchmarking": True,
                    "goal_tracking": True
                }
            )
        ]
    
    # ==================== FOOD & HOSPITALITY TEMPLATE ====================
    
    def _create_food_hospitality_template(self) -> TemplateConfiguration:
        """Food & Hospitality Template Configuration"""
        
        # Category-specific features
        category_features = [
            AIFeature(
                feature_type=AIFeatureType.SMART_MENU_SERVICE_OPTIMIZER,
                name="Smart Menu Optimizer",
                description="AI-powered menu optimization based on sales, trends, and profitability",
                is_universal=False,
                applicable_templates=[TemplateType.FOOD_HOSPITALITY],
                min_tier=SubscriptionTier.PREMIUM,
                configuration={
                    "optimization_frequency": "weekly",
                    "consider_seasonality": True,
                    "profitability_weight": 0.6,
                    "popularity_weight": 0.4
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.CUSTOMER_RETENTION_PREDICTOR,
                name="Customer Retention Predictor",
                description="Predict customer churn and recommend retention strategies",
                is_universal=False,
                applicable_templates=[TemplateType.FOOD_HOSPITALITY],
                min_tier=SubscriptionTier.PREMIUM,
                configuration={
                    "prediction_window_days": 30,
                    "churn_threshold": 0.7,
                    "auto_campaigns": True
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.DYNAMIC_PRICING_ENGINE,
                name="Dynamic Pricing Engine",
                description="Real-time price optimization based on demand, competition, and inventory",
                is_universal=False,
                applicable_templates=[TemplateType.FOOD_HOSPITALITY],
                min_tier=SubscriptionTier.ENTERPRISE,
                configuration={
                    "pricing_strategy": "demand_based",
                    "competitor_tracking": True,
                    "min_margin_percent": 20
                }
            )
        ]
        
        # API Endpoints
        api_endpoints = [
            TemplateAPIEndpoint(method="POST", path="/api/v1/menu/categories", description="Create menu categories"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/menu/items", description="Get menu items"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/menu/items", description="Create menu item"),
            TemplateAPIEndpoint(method="PUT", path="/api/v1/menu/items/{item_id}", description="Update menu item"),
            TemplateAPIEndpoint(method="DELETE", path="/api/v1/menu/items/{item_id}", description="Delete menu item"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/menu/items/search", description="AI-powered menu search"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/menu/optimize", description="AI menu optimization"),
            
            TemplateAPIEndpoint(method="POST", path="/api/v1/reservations", description="Create reservation"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/reservations", description="Get reservations"),
            TemplateAPIEndpoint(method="PUT", path="/api/v1/reservations/{id}", description="Update reservation"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/reservations/book", description="Book table"),
            
            TemplateAPIEndpoint(method="POST", path="/api/v1/tables", description="Create/manage tables"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/tables/status", description="Real-time table status"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/analytics/table-turnover", description="Table turnover analytics"),
            
            TemplateAPIEndpoint(method="GET", path="/api/v1/kitchen/display", description="Real-time kitchen display"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/kitchen/prep-times", description="Preparation time tracking"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/inventory/alerts", description="Low inventory alerts"),
        ]
        
        # Dashboard Widgets
        widgets = [
            DashboardWidget(
                widget_id="revenue_chart",
                name="Revenue Trend",
                type="line_chart",
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                data_source="/api/v1/analytics/revenue",
                refresh_interval=300
            ),
            DashboardWidget(
                widget_id="top_menu_items",
                name="Top Menu Items",
                type="bar_chart",
                position={"x": 6, "y": 0, "width": 6, "height": 4},
                data_source="/api/v1/analytics/top-items",
                refresh_interval=600
            ),
            DashboardWidget(
                widget_id="table_status",
                name="Table Status",
                type="status_grid",
                position={"x": 0, "y": 4, "width": 4, "height": 3},
                data_source="/api/v1/tables/status",
                refresh_interval=30
            ),
            DashboardWidget(
                widget_id="reservations_today",
                name="Today's Reservations",
                type="list",
                position={"x": 4, "y": 4, "width": 4, "height": 3},
                data_source="/api/v1/reservations/today",
                refresh_interval=60
            ),
            DashboardWidget(
                widget_id="kitchen_orders",
                name="Kitchen Orders",
                type="kanban",
                position={"x": 8, "y": 4, "width": 4, "height": 3},
                data_source="/api/v1/kitchen/orders",
                refresh_interval=15
            )
        ]
        
        return TemplateConfiguration(
            template_type=TemplateType.FOOD_HOSPITALITY,
            name="Food & Hospitality",
            description="Complete solution for restaurants, cafes, bars, and food services",
            icon="🍽️",
            color_scheme={"primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#FFE66D"},
            ai_features=self._get_universal_features() + category_features,
            api_endpoints=api_endpoints,
            dashboard_widgets=widgets,
            langgraph_workflows=["order_processing", "reservation_management", "inventory_replenishment"],
            crewai_agents=["menu_optimizer_agent", "customer_service_agent", "kitchen_coordinator_agent"],
            data_models=["Menu", "MenuItem", "Category", "Order", "Reservation", "Table", "Inventory"],
            required_integrations=["payment_gateway", "pos_system"],
            optional_integrations=["delivery_platforms", "reservation_systems", "accounting_software"]
        )
    
    # ==================== SERVICE-BASED TEMPLATE ====================
    
    def _create_service_based_template(self) -> TemplateConfiguration:
        """Service-Based Template Configuration"""
        
        category_features = [
            AIFeature(
                feature_type=AIFeatureType.AI_ROUTE_OPTIMIZER,
                name="AI Route Optimizer",
                description="Optimize service routes for mobile businesses and field services",
                is_universal=False,
                applicable_templates=[TemplateType.SERVICE_BASED],
                min_tier=SubscriptionTier.PREMIUM,
                configuration={
                    "optimization_algorithm": "genetic",
                    "real_time_traffic": True,
                    "multi_vehicle": True
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.CUSTOMER_RETENTION_PREDICTOR,
                name="Customer Retention Predictor",
                description="Predict client churn and recommend retention strategies",
                is_universal=False,
                applicable_templates=[TemplateType.SERVICE_BASED],
                min_tier=SubscriptionTier.PREMIUM,
                configuration={
                    "prediction_window_days": 30,
                    "churn_threshold": 0.7
                }
            ),
            AIFeature(
                feature_type=AIFeatureType.SMART_MENU_SERVICE_OPTIMIZER,
                name="Smart Service Optimizer",
                description="Optimize service offerings based on demand and profitability",
                is_universal=False,
                applicable_templates=[TemplateType.SERVICE_BASED],
                min_tier=SubscriptionTier.PREMIUM
            )
        ]
        
        api_endpoints = [
            TemplateAPIEndpoint(method="POST", path="/api/v1/appointments", description="Book appointments"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/appointments", description="Get appointments"),
            TemplateAPIEndpoint(method="PUT", path="/api/v1/appointments/{id}", description="Update appointment"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/schedule/optimize", description="AI scheduling optimization"),
            
            TemplateAPIEndpoint(method="POST", path="/api/v1/services", description="Service catalog management"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/services", description="Get services"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/routes/optimize", description="Route optimization"),
            
            TemplateAPIEndpoint(method="GET", path="/api/v1/clients/history", description="Client interaction history"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/clients/preferences", description="Preference tracking"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/analytics/client-retention", description="Retention analytics"),
        ]
        
        widgets = [
            DashboardWidget(
                widget_id="appointments_calendar",
                name="Appointments Calendar",
                type="calendar",
                position={"x": 0, "y": 0, "width": 8, "height": 5},
                data_source="/api/v1/appointments/calendar",
                refresh_interval=60
            ),
            DashboardWidget(
                widget_id="service_performance",
                name="Service Performance",
                type="bar_chart",
                position={"x": 8, "y": 0, "width": 4, "height": 5},
                data_source="/api/v1/analytics/services",
                refresh_interval=300
            ),
            DashboardWidget(
                widget_id="route_map",
                name="Route Optimization",
                type="map",
                position={"x": 0, "y": 5, "width": 6, "height": 4},
                data_source="/api/v1/routes/current",
                refresh_interval=120
            )
        ]
        
        return TemplateConfiguration(
            template_type=TemplateType.SERVICE_BASED,
            name="Service-Based Business",
            description="Perfect for salons, spas, cleaning services, and field services",
            icon="✂️",
            color_scheme={"primary": "#9B59B6", "secondary": "#3498DB", "accent": "#1ABC9C"},
            ai_features=self._get_universal_features() + category_features,
            api_endpoints=api_endpoints,
            dashboard_widgets=widgets,
            langgraph_workflows=["appointment_scheduling", "route_optimization", "client_management"],
            crewai_agents=["scheduling_agent", "route_optimizer_agent", "client_success_agent"],
            data_models=["Appointment", "Service", "Client", "Schedule", "Route"],
            required_integrations=["calendar_sync", "payment_gateway"],
            optional_integrations=["sms_reminders", "mapping_services", "crm_systems"]
        )
    
    # ==================== RETAIL & E-COMMERCE TEMPLATE ====================
    
    def _create_retail_ecommerce_template(self) -> TemplateConfiguration:
        """Retail & E-commerce Template Configuration"""
        
        category_features = [
            AIFeature(
                feature_type=AIFeatureType.DYNAMIC_PRICING_ENGINE,
                name="Dynamic Pricing Engine",
                description="AI-powered dynamic pricing based on demand, competition, and inventory",
                is_universal=False,
                applicable_templates=[TemplateType.RETAIL_ECOMMERCE],
                min_tier=SubscriptionTier.PREMIUM
            ),
            AIFeature(
                feature_type=AIFeatureType.COMPETITOR_MARKET_WATCHDOG,
                name="Competitor & Market Watchdog",
                description="Monitor competitors and market trends in real-time",
                is_universal=False,
                applicable_templates=[TemplateType.RETAIL_ECOMMERCE],
                min_tier=SubscriptionTier.ENTERPRISE
            ),
            AIFeature(
                feature_type=AIFeatureType.CUSTOMER_RETENTION_PREDICTOR,
                name="Customer Retention Predictor",
                description="Predict customer churn and optimize retention campaigns",
                is_universal=False,
                applicable_templates=[TemplateType.RETAIL_ECOMMERCE],
                min_tier=SubscriptionTier.PREMIUM
            )
        ]
        
        api_endpoints = [
            TemplateAPIEndpoint(method="POST", path="/api/v1/inventory/bulk-update", description="Bulk inventory operations"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/inventory/forecast", description="AI inventory forecasting"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/pricing/dynamic", description="Dynamic pricing engine"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/competitors/monitor", description="Competitor price monitoring"),
            
            TemplateAPIEndpoint(method="POST", path="/api/v1/sales/process", description="Point of sale integration"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/customers/segmentation", description="Customer segmentation"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/promotions/targeted", description="AI-powered promotions"),
            
            TemplateAPIEndpoint(method="GET", path="/api/v1/products", description="Get products"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/products", description="Create product"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/analytics/sales", description="Sales analytics"),
        ]
        
        widgets = [
            DashboardWidget(
                widget_id="sales_overview",
                name="Sales Overview",
                type="metric_cards",
                position={"x": 0, "y": 0, "width": 12, "height": 2},
                data_source="/api/v1/analytics/sales-overview",
                refresh_interval=300
            ),
            DashboardWidget(
                widget_id="inventory_status",
                name="Inventory Status",
                type="table",
                position={"x": 0, "y": 2, "width": 6, "height": 4},
                data_source="/api/v1/inventory/status",
                refresh_interval=600
            ),
            DashboardWidget(
                widget_id="customer_segments",
                name="Customer Segments",
                type="pie_chart",
                position={"x": 6, "y": 2, "width": 6, "height": 4},
                data_source="/api/v1/customers/segments",
                refresh_interval=3600
            )
        ]
        
        return TemplateConfiguration(
            template_type=TemplateType.RETAIL_ECOMMERCE,
            name="Retail & E-commerce",
            description="Comprehensive solution for retail stores and online businesses",
            icon="🛍️",
            color_scheme={"primary": "#E74C3C", "secondary": "#F39C12", "accent": "#27AE60"},
            ai_features=self._get_universal_features() + category_features,
            api_endpoints=api_endpoints,
            dashboard_widgets=widgets,
            langgraph_workflows=["order_fulfillment", "inventory_management", "customer_segmentation"],
            crewai_agents=["pricing_agent", "inventory_agent", "marketing_agent"],
            data_models=["Product", "Inventory", "Sale", "Customer", "Order", "Promotion"],
            required_integrations=["payment_gateway", "shipping_providers"],
            optional_integrations=["ecommerce_platforms", "accounting_software", "marketing_tools"]
        )
    
    # ==================== PROFESSIONAL SERVICES TEMPLATE ====================
    
    def _create_professional_services_template(self) -> TemplateConfiguration:
        """Professional Services Template Configuration"""
        
        category_features = [
            AIFeature(
                feature_type=AIFeatureType.PROJECT_PROFITABILITY_ANALYZER,
                name="Project Profitability Analyzer",
                description="Real-time project profitability tracking and optimization",
                is_universal=False,
                applicable_templates=[TemplateType.PROFESSIONAL_SERVICES],
                min_tier=SubscriptionTier.PREMIUM
            ),
            AIFeature(
                feature_type=AIFeatureType.WHAT_IF_SIMULATOR,
                name="What-If Simulator",
                description="Business scenario modeling and simulation",
                is_universal=False,
                applicable_templates=[TemplateType.PROFESSIONAL_SERVICES],
                min_tier=SubscriptionTier.ENTERPRISE
            )
        ]
        
        api_endpoints = [
            TemplateAPIEndpoint(method="POST", path="/api/v1/projects", description="Project creation and management"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/projects", description="Get projects"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/projects/profitability", description="Real-time profitability tracking"),
            
            TemplateAPIEndpoint(method="POST", path="/api/v1/time/entries", description="Time tracking automation"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/time/entries", description="Get time entries"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/resources/allocation", description="Resource optimization"),
            
            TemplateAPIEndpoint(method="POST", path="/api/v1/clients/portal-access", description="Client portal management"),
            TemplateAPIEndpoint(method="GET", path="/api/v1/projects/{id}/documents", description="Document management"),
            TemplateAPIEndpoint(method="POST", path="/api/v1/invoices/generate", description="Automated invoicing"),
        ]
        
        widgets = [
            DashboardWidget(
                widget_id="project_timeline",
                name="Project Timeline",
                type="gantt_chart",
                position={"x": 0, "y": 0, "width": 8, "height": 4},
                data_source="/api/v1/projects/timeline",
                refresh_interval=600
            ),
            DashboardWidget(
                widget_id="profitability_metrics",
                name="Profitability Metrics",
                type="metric_cards",
                position={"x": 8, "y": 0, "width": 4, "height": 4},
                data_source="/api/v1/projects/profitability-metrics",
                refresh_interval=300
            ),
            DashboardWidget(
                widget_id="resource_utilization",
                name="Resource Utilization",
                type="heatmap",
                position={"x": 0, "y": 4, "width": 6, "height": 3},
                data_source="/api/v1/resources/utilization",
                refresh_interval=3600
            ),
            DashboardWidget(
                widget_id="billable_hours",
                name="Billable Hours",
                type="bar_chart",
                position={"x": 6, "y": 4, "width": 6, "height": 3},
                data_source="/api/v1/time/billable",
                refresh_interval=3600
            )
        ]
        
        return TemplateConfiguration(
            template_type=TemplateType.PROFESSIONAL_SERVICES,
            name="Professional Services",
            description="Tailored for consulting, law firms, agencies, and professional practices",
            icon="💼",
            color_scheme={"primary": "#34495E", "secondary": "#16A085", "accent": "#F39C12"},
            ai_features=self._get_universal_features() + category_features,
            api_endpoints=api_endpoints,
            dashboard_widgets=widgets,
            langgraph_workflows=["project_management", "time_tracking", "invoicing"],
            crewai_agents=["project_manager_agent", "resource_allocator_agent", "billing_agent"],
            data_models=["Project", "TimeEntry", "Client", "Invoice", "Resource", "Document"],
            required_integrations=["time_tracking", "invoicing"],
            optional_integrations=["project_management_tools", "document_management", "crm_systems"]
        )


# Singleton instance
_template_config_service = None

def get_template_config_service() -> TemplateConfigurationService:
    """Get singleton instance of TemplateConfigurationService"""
    global _template_config_service
    if _template_config_service is None:
        _template_config_service = TemplateConfigurationService()
    return _template_config_service
