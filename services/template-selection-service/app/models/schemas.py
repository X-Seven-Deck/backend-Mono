"""
Template Selection Service - Data Models

Enterprise-grade schemas for template selection, category mapping, and feature provisioning.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class BusinessCategory(str, Enum):
    """50+ Business Categories"""
    # Food & Hospitality
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAR = "bar"
    FOOD_TRUCK = "food_truck"
    BAKERY = "bakery"
    CATERING = "catering"
    CLOUD_KITCHEN = "cloud_kitchen"
    HOTEL = "hotel"
    
    # Service-Based
    SALON = "salon"
    SPA = "spa"
    BARBERSHOP = "barbershop"
    NAIL_SALON = "nail_salon"
    MASSAGE_THERAPY = "massage_therapy"
    FITNESS_GYM = "fitness_gym"
    YOGA_STUDIO = "yoga_studio"
    PERSONAL_TRAINING = "personal_training"
    CLEANING_SERVICE = "cleaning_service"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    LANDSCAPING = "landscaping"
    PET_GROOMING = "pet_grooming"
    AUTO_REPAIR = "auto_repair"
    
    # Retail & E-commerce
    RETAIL_STORE = "retail_store"
    BOUTIQUE = "boutique"
    GROCERY_STORE = "grocery_store"
    PHARMACY = "pharmacy"
    ELECTRONICS_STORE = "electronics_store"
    BOOKSTORE = "bookstore"
    JEWELRY_STORE = "jewelry_store"
    FURNITURE_STORE = "furniture_store"
    ECOMMERCE = "ecommerce"
    
    # Professional Services
    LAW_FIRM = "law_firm"
    ACCOUNTING_FIRM = "accounting_firm"
    CONSULTING = "consulting"
    MARKETING_AGENCY = "marketing_agency"
    REAL_ESTATE = "real_estate"
    INSURANCE_AGENCY = "insurance_agency"
    FINANCIAL_ADVISORY = "financial_advisory"
    ARCHITECTURE_FIRM = "architecture_firm"
    ENGINEERING_FIRM = "engineering_firm"
    IT_SERVICES = "it_services"
    MEDICAL_PRACTICE = "medical_practice"
    DENTAL_PRACTICE = "dental_practice"
    VETERINARY_CLINIC = "veterinary_clinic"
    THERAPY_PRACTICE = "therapy_practice"
    PHOTOGRAPHY = "photography"
    EVENT_PLANNING = "event_planning"
    TUTORING = "tutoring"
    DAYCARE = "daycare"


class TemplateType(str, Enum):
    """4 Core Template Types"""
    FOOD_HOSPITALITY = "food_hospitality"
    SERVICE_BASED = "service_based"
    RETAIL_ECOMMERCE = "retail_ecommerce"
    PROFESSIONAL_SERVICES = "professional_services"


class SubscriptionTier(str, Enum):
    """Subscription Tiers"""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class AIFeatureType(str, Enum):
    """AI Feature Types"""
    # Universal Features (6)
    AI_INSIGHT_ENGINE = "ai_insight_engine"
    PREDICTIVE_INTELLIGENCE = "predictive_intelligence"
    AI_AUTOMATION_WORKFLOWS = "ai_automation_workflows"
    AI_COPILOT_CHAT = "ai_copilot_chat"
    AI_GENERATED_REPORTS = "ai_generated_reports"
    AI_BUSINESS_COACH = "ai_business_coach"
    
    # Category-Specific Features (7)
    CUSTOMER_RETENTION_PREDICTOR = "customer_retention_predictor"
    SMART_MENU_SERVICE_OPTIMIZER = "smart_menu_service_optimizer"
    DYNAMIC_PRICING_ENGINE = "dynamic_pricing_engine"
    AI_ROUTE_OPTIMIZER = "ai_route_optimizer"
    PROJECT_PROFITABILITY_ANALYZER = "project_profitability_analyzer"
    WHAT_IF_SIMULATOR = "what_if_simulator"
    COMPETITOR_MARKET_WATCHDOG = "competitor_market_watchdog"


class AIFeature(BaseModel):
    """AI Feature Definition"""
    feature_type: AIFeatureType
    name: str
    description: str
    is_universal: bool
    applicable_templates: List[TemplateType]
    min_tier: SubscriptionTier
    enabled_by_default: bool = True
    configuration: Dict[str, Any] = Field(default_factory=dict)


class TemplateAPIEndpoint(BaseModel):
    """Template-Specific API Endpoint"""
    method: str  # GET, POST, PUT, DELETE
    path: str
    description: str
    requires_auth: bool = True
    rate_limit: Optional[int] = None  # requests per minute


class DashboardWidget(BaseModel):
    """Dashboard Widget Configuration"""
    widget_id: str
    name: str
    type: str  # chart, table, metric, etc.
    position: Dict[str, int]  # x, y, width, height
    data_source: str
    refresh_interval: Optional[int] = None  # seconds
    configuration: Dict[str, Any] = Field(default_factory=dict)


class TemplateConfiguration(BaseModel):
    """Complete Template Configuration"""
    template_type: TemplateType
    name: str
    description: str
    icon: str
    color_scheme: Dict[str, str]
    
    # Features
    ai_features: List[AIFeature]
    api_endpoints: List[TemplateAPIEndpoint]
    dashboard_widgets: List[DashboardWidget]
    
    # Workflows
    langgraph_workflows: List[str]
    crewai_agents: List[str]
    
    # Data Models
    data_models: List[str]
    database_schema: Optional[str] = None
    
    # Integration Points
    required_integrations: List[str] = Field(default_factory=list)
    optional_integrations: List[str] = Field(default_factory=list)


class CategoryMapping(BaseModel):
    """Business Category to Template Mapping"""
    category: BusinessCategory
    template_type: TemplateType
    confidence_score: float = Field(ge=0.0, le=1.0)
    alternative_templates: List[TemplateType] = Field(default_factory=list)
    reasoning: Optional[str] = None


class TemplateSelectionRequest(BaseModel):
    """Request for Template Selection"""
    business_id: str
    business_name: str
    category: BusinessCategory
    business_size: Optional[str] = "small"  # small, medium, large, enterprise
    subscription_tier: SubscriptionTier = SubscriptionTier.BASIC
    custom_requirements: Optional[List[str]] = Field(default_factory=list)
    
    @validator('business_name')
    def validate_business_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Business name cannot be empty")
        return v.strip()


class TemplateSelectionResponse(BaseModel):
    """Response with Complete Template Configuration"""
    business_id: str
    selected_template: TemplateType
    category_mapping: CategoryMapping
    configuration: TemplateConfiguration
    
    # Feature Availability
    available_features: List[AIFeature]
    restricted_features: List[AIFeature]
    
    # Customization Options
    customization_options: Dict[str, Any]
    
    # Metadata
    selection_timestamp: datetime
    configuration_version: str = "1.0.0"
    estimated_setup_time: int  # minutes


class TemplatePreviewRequest(BaseModel):
    """Preview Template Before Applying"""
    category: BusinessCategory
    subscription_tier: SubscriptionTier = SubscriptionTier.BASIC


class TemplateCustomizationRequest(BaseModel):
    """Customize Template Features"""
    business_id: str
    template_type: TemplateType
    enabled_features: List[AIFeatureType]
    disabled_features: List[AIFeatureType] = Field(default_factory=list)
    custom_widgets: Optional[List[DashboardWidget]] = None
    custom_endpoints: Optional[List[TemplateAPIEndpoint]] = None


class FeatureToggleRequest(BaseModel):
    """Real-time Feature Toggle"""
    business_id: str
    feature_type: AIFeatureType
    enabled: bool
    reason: Optional[str] = None


class TemplateAnalytics(BaseModel):
    """Template Usage Analytics"""
    template_type: TemplateType
    total_businesses: int
    active_businesses: int
    feature_adoption_rates: Dict[str, float]
    avg_satisfaction_score: float
    most_used_features: List[str]
    least_used_features: List[str]


class BusinessContext(BaseModel):
    """Business Context for AI Enhancement"""
    business_id: str
    template_type: TemplateType
    industry_insights: Dict[str, Any]
    usage_patterns: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommended_features: List[AIFeatureType]
