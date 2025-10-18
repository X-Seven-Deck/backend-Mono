"""
Template Selection Service

Core business logic for template selection and configuration.
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.schemas import (
    TemplateSelectionRequest, TemplateSelectionResponse, TemplatePreviewRequest,
    TemplateCustomizationRequest, FeatureToggleRequest, TemplateAnalytics,
    BusinessContext, TemplateType, CategoryMapping, AIFeature
)
from app.services.category_mapper import get_category_mapper
from app.services.template_config import get_template_config_service
from app.services.feature_engine import get_feature_engine
import logging

logger = logging.getLogger(__name__)


class TemplateSelectionService:
    """
    Main service for template selection, configuration, and management.
    Orchestrates category mapping, feature provisioning, and customization.
    """
    
    def __init__(self):
        self.category_mapper = get_category_mapper()
        self.template_config = get_template_config_service()
        self.feature_engine = get_feature_engine()
        
        # In-memory cache (future: Redis)
        self._config_cache: Dict[str, TemplateSelectionResponse] = {}
    
    async def select_template(
        self,
        request: TemplateSelectionRequest
    ) -> TemplateSelectionResponse:
        """
        Select and configure template for a business.
        
        This is the main entry point that:
        1. Maps category to template
        2. Loads template configuration
        3. Filters features by tier
        4. Applies customizations
        5. Returns complete configuration
        """
        logger.info(
            f"Template selection requested for business {request.business_id}, "
            f"category: {request.category.value}, tier: {request.subscription_tier.value}"
        )
        
        # Check cache
        cache_key = f"{request.business_id}:{request.category.value}:{request.subscription_tier.value}"
        if cache_key in self._config_cache:
            logger.info(f"Returning cached configuration for {cache_key}")
            return self._config_cache[cache_key]
        
        # Step 1: Map category to template
        category_mapping = self.category_mapper.map_category_to_template(
            request.category,
            business_context={
                "business_size": request.business_size,
                "custom_requirements": request.custom_requirements
            }
        )
        
        # Step 2: Load template configuration
        template_config = self.template_config.get_template(category_mapping.template_type)
        
        if not template_config:
            raise ValueError(f"Template configuration not found for {category_mapping.template_type}")
        
        # Step 3: Filter features by subscription tier
        available_features, restricted_features = self.feature_engine.filter_features_by_tier(
            template_config.ai_features,
            request.subscription_tier
        )
        
        # Step 4: Apply feature toggles (if business already exists)
        available_features = self.feature_engine.apply_feature_toggles(
            request.business_id,
            available_features
        )
        
        # Step 5: Generate customization options
        customization_options = self._generate_customization_options(
            template_config,
            request
        )
        
        # Step 6: Calculate estimated setup time
        estimated_setup_time = self._calculate_setup_time(
            template_config,
            len(available_features)
        )
        
        # Create response
        response = TemplateSelectionResponse(
            business_id=request.business_id,
            selected_template=category_mapping.template_type,
            category_mapping=category_mapping,
            configuration=template_config,
            available_features=available_features,
            restricted_features=restricted_features,
            customization_options=customization_options,
            selection_timestamp=datetime.utcnow(),
            configuration_version="1.0.0",
            estimated_setup_time=estimated_setup_time
        )
        
        # Cache the response
        self._config_cache[cache_key] = response
        
        logger.info(
            f"Template selection completed for {request.business_id}: "
            f"{category_mapping.template_type.value}, "
            f"{len(available_features)} features available"
        )
        
        return response
    
    async def preview_template(
        self,
        request: TemplatePreviewRequest
    ) -> Dict:
        """
        Preview template configuration before applying.
        """
        # Map category to template
        category_mapping = self.category_mapper.map_category_to_template(request.category)
        
        # Load template configuration
        template_config = self.template_config.get_template(category_mapping.template_type)
        
        # Filter features by tier
        available_features, restricted_features = self.feature_engine.filter_features_by_tier(
            template_config.ai_features,
            request.subscription_tier
        )
        
        return {
            "template_type": category_mapping.template_type.value,
            "template_name": template_config.name,
            "description": template_config.description,
            "icon": template_config.icon,
            "color_scheme": template_config.color_scheme,
            "available_features_count": len(available_features),
            "restricted_features_count": len(restricted_features),
            "available_features": [
                {
                    "name": f.name,
                    "description": f.description,
                    "is_universal": f.is_universal
                }
                for f in available_features
            ],
            "api_endpoints_count": len(template_config.api_endpoints),
            "dashboard_widgets_count": len(template_config.dashboard_widgets),
            "confidence_score": category_mapping.confidence_score,
            "reasoning": category_mapping.reasoning
        }
    
    async def customize_template(
        self,
        request: TemplateCustomizationRequest
    ) -> Dict:
        """
        Customize template features for specific business needs.
        """
        logger.info(
            f"Template customization requested for business {request.business_id}, "
            f"template: {request.template_type.value}"
        )
        
        # Load template configuration
        template_config = self.template_config.get_template(request.template_type)
        
        # Validate feature compatibility
        is_valid, errors = self.feature_engine.validate_feature_compatibility(
            request.enabled_features,
            template_config
        )
        
        if not is_valid:
            return {
                "success": False,
                "errors": errors
            }
        
        # Apply feature toggles
        for feature_type in request.enabled_features:
            self.feature_engine.set_feature_toggle(
                request.business_id,
                feature_type,
                True,
                reason="User customization"
            )
        
        for feature_type in request.disabled_features:
            self.feature_engine.set_feature_toggle(
                request.business_id,
                feature_type,
                False,
                reason="User customization"
            )
        
        # Clear cache for this business
        self._clear_business_cache(request.business_id)
        
        return {
            "success": True,
            "business_id": request.business_id,
            "template_type": request.template_type.value,
            "enabled_features": [f.value for f in request.enabled_features],
            "disabled_features": [f.value for f in request.disabled_features],
            "message": "Template customization applied successfully"
        }
    
    async def toggle_feature(
        self,
        request: FeatureToggleRequest
    ) -> Dict:
        """
        Real-time feature toggle for a business.
        """
        self.feature_engine.set_feature_toggle(
            request.business_id,
            request.feature_type,
            request.enabled,
            reason=request.reason
        )
        
        # Clear cache
        self._clear_business_cache(request.business_id)
        
        return {
            "success": True,
            "business_id": request.business_id,
            "feature_type": request.feature_type.value,
            "enabled": request.enabled,
            "message": f"Feature {'enabled' if request.enabled else 'disabled'} successfully"
        }
    
    async def get_template_analytics(
        self,
        template_type: Optional[TemplateType] = None
    ) -> List[TemplateAnalytics]:
        """
        Get template usage analytics.
        Future: Query from analytics database.
        """
        # Placeholder: Return mock analytics
        analytics = []
        
        templates = [template_type] if template_type else list(TemplateType)
        
        for tmpl in templates:
            analytics.append(TemplateAnalytics(
                template_type=tmpl,
                total_businesses=100,  # Mock data
                active_businesses=85,
                feature_adoption_rates=self.feature_engine.calculate_feature_adoption_rate(tmpl),
                avg_satisfaction_score=4.5,
                most_used_features=["AI Copilot Chat", "AI Insight Engine"],
                least_used_features=["AI Business Coach", "What-If Simulator"]
            ))
        
        return analytics
    
    async def get_business_context(
        self,
        business_id: str
    ) -> BusinessContext:
        """
        Get business context for AI enhancement.
        Future: Query from analytics and usage databases.
        """
        # Placeholder: Return mock context
        return BusinessContext(
            business_id=business_id,
            template_type=TemplateType.FOOD_HOSPITALITY,  # Mock
            industry_insights={
                "peak_hours": [12, 13, 18, 19, 20],
                "avg_order_value": 45.50,
                "customer_retention_rate": 0.65
            },
            usage_patterns={
                "most_used_features": ["menu_management", "reservations"],
                "daily_active_users": 5,
                "api_calls_per_day": 1500
            },
            performance_metrics={
                "response_time_ms": 120,
                "error_rate": 0.01,
                "uptime_percent": 99.9
            },
            recommended_features=[
                AIFeatureType.SMART_MENU_SERVICE_OPTIMIZER,
                AIFeatureType.PREDICTIVE_INTELLIGENCE
            ]
        )
    
    def _generate_customization_options(
        self,
        template_config,
        request: TemplateSelectionRequest
    ) -> Dict:
        """Generate customization options based on template and request"""
        return {
            "can_add_custom_widgets": True,
            "can_add_custom_endpoints": request.subscription_tier.value != "basic",
            "can_customize_workflows": request.subscription_tier.value == "enterprise",
            "max_custom_features": {
                "basic": 2,
                "premium": 5,
                "enterprise": -1  # unlimited
            }[request.subscription_tier.value],
            "available_integrations": template_config.optional_integrations,
            "branding_customization": request.subscription_tier.value != "basic"
        }
    
    def _calculate_setup_time(
        self,
        template_config,
        feature_count: int
    ) -> int:
        """Calculate estimated setup time in minutes"""
        base_time = 15  # Base setup time
        feature_time = feature_count * 2  # 2 minutes per feature
        integration_time = len(template_config.required_integrations) * 5
        
        return base_time + feature_time + integration_time
    
    def _clear_business_cache(self, business_id: str):
        """Clear cache entries for a business"""
        keys_to_remove = [k for k in self._config_cache.keys() if k.startswith(f"{business_id}:")]
        for key in keys_to_remove:
            del self._config_cache[key]
        logger.info(f"Cleared {len(keys_to_remove)} cache entries for business {business_id}")


# Singleton instance
_template_service = None

def get_template_service() -> TemplateSelectionService:
    """Get singleton instance of TemplateSelectionService"""
    global _template_service
    if _template_service is None:
        _template_service = TemplateSelectionService()
    return _template_service
