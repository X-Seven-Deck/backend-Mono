"""
Feature Availability Engine

Manages feature filtering based on subscription tier and business context.
"""

from typing import List, Dict, Tuple
from app.models.schemas import (
    AIFeature, AIFeatureType, SubscriptionTier, TemplateType, TemplateConfiguration
)
import logging

logger = logging.getLogger(__name__)


class FeatureAvailabilityEngine:
    """
    Manages feature availability based on subscription tier and business context.
    Supports real-time feature toggles and usage analytics.
    """
    
    def __init__(self):
        self._feature_toggles: Dict[str, Dict[AIFeatureType, bool]] = {}  # business_id -> feature -> enabled
        self._tier_hierarchy = {
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PREMIUM: 2,
            SubscriptionTier.ENTERPRISE: 3
        }
    
    def filter_features_by_tier(
        self,
        features: List[AIFeature],
        subscription_tier: SubscriptionTier
    ) -> Tuple[List[AIFeature], List[AIFeature]]:
        """
        Filter features based on subscription tier.
        
        Returns:
            Tuple of (available_features, restricted_features)
        """
        available = []
        restricted = []
        
        user_tier_level = self._tier_hierarchy.get(subscription_tier, 1)
        
        for feature in features:
            required_tier_level = self._tier_hierarchy.get(feature.min_tier, 1)
            
            if user_tier_level >= required_tier_level:
                available.append(feature)
            else:
                restricted.append(feature)
        
        logger.info(
            f"Filtered features for tier {subscription_tier}: "
            f"{len(available)} available, {len(restricted)} restricted"
        )
        
        return available, restricted
    
    def apply_feature_toggles(
        self,
        business_id: str,
        features: List[AIFeature]
    ) -> List[AIFeature]:
        """
        Apply real-time feature toggles for a business.
        """
        if business_id not in self._feature_toggles:
            return features
        
        toggles = self._feature_toggles[business_id]
        filtered_features = []
        
        for feature in features:
            if feature.feature_type in toggles:
                if toggles[feature.feature_type]:
                    filtered_features.append(feature)
            else:
                # Default to enabled if no toggle exists
                if feature.enabled_by_default:
                    filtered_features.append(feature)
        
        return filtered_features
    
    def set_feature_toggle(
        self,
        business_id: str,
        feature_type: AIFeatureType,
        enabled: bool,
        reason: str = None
    ):
        """
        Set feature toggle for a specific business.
        """
        if business_id not in self._feature_toggles:
            self._feature_toggles[business_id] = {}
        
        self._feature_toggles[business_id][feature_type] = enabled
        
        logger.info(
            f"Feature toggle set for business {business_id}: "
            f"{feature_type.value} = {enabled}"
            + (f" (reason: {reason})" if reason else "")
        )
    
    def get_feature_toggles(self, business_id: str) -> Dict[AIFeatureType, bool]:
        """Get all feature toggles for a business"""
        return self._feature_toggles.get(business_id, {})
    
    def enhance_features_with_context(
        self,
        features: List[AIFeature],
        business_context: Dict
    ) -> List[AIFeature]:
        """
        Enhance features based on business context.
        Future: Use ML to recommend optimal feature configurations.
        """
        # Future implementation: Analyze business context and adjust feature configurations
        # For now, return features as-is
        return features
    
    def get_feature_recommendations(
        self,
        template_type: TemplateType,
        business_context: Dict
    ) -> List[AIFeatureType]:
        """
        Recommend features based on business context and usage patterns.
        Future: ML-based recommendations.
        """
        # Basic rule-based recommendations
        recommendations = []
        
        # Universal recommendations
        recommendations.extend([
            AIFeatureType.AI_COPILOT_CHAT,
            AIFeatureType.AI_INSIGHT_ENGINE
        ])
        
        # Template-specific recommendations
        if template_type == TemplateType.FOOD_HOSPITALITY:
            recommendations.extend([
                AIFeatureType.SMART_MENU_SERVICE_OPTIMIZER,
                AIFeatureType.CUSTOMER_RETENTION_PREDICTOR
            ])
        elif template_type == TemplateType.SERVICE_BASED:
            recommendations.extend([
                AIFeatureType.AI_ROUTE_OPTIMIZER,
                AIFeatureType.CUSTOMER_RETENTION_PREDICTOR
            ])
        elif template_type == TemplateType.RETAIL_ECOMMERCE:
            recommendations.extend([
                AIFeatureType.DYNAMIC_PRICING_ENGINE,
                AIFeatureType.COMPETITOR_MARKET_WATCHDOG
            ])
        elif template_type == TemplateType.PROFESSIONAL_SERVICES:
            recommendations.extend([
                AIFeatureType.PROJECT_PROFITABILITY_ANALYZER,
                AIFeatureType.WHAT_IF_SIMULATOR
            ])
        
        return recommendations
    
    def calculate_feature_adoption_rate(
        self,
        template_type: TemplateType
    ) -> Dict[str, float]:
        """
        Calculate feature adoption rates for analytics.
        Future: Track actual usage from database.
        """
        # Placeholder: Return mock data
        # In production, query from analytics database
        return {
            "ai_copilot_chat": 0.85,
            "ai_insight_engine": 0.72,
            "predictive_intelligence": 0.45,
            "ai_automation_workflows": 0.38,
            "ai_generated_reports": 0.55,
            "ai_business_coach": 0.28
        }
    
    def validate_feature_compatibility(
        self,
        enabled_features: List[AIFeatureType],
        template_config: TemplateConfiguration
    ) -> Tuple[bool, List[str]]:
        """
        Validate that enabled features are compatible with the template.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Get all valid feature types for this template
        valid_features = {f.feature_type for f in template_config.ai_features}
        
        for feature_type in enabled_features:
            if feature_type not in valid_features:
                errors.append(
                    f"Feature {feature_type.value} is not available for template "
                    f"{template_config.template_type.value}"
                )
        
        return len(errors) == 0, errors
    
    def get_upgrade_suggestions(
        self,
        current_tier: SubscriptionTier,
        restricted_features: List[AIFeature]
    ) -> Dict:
        """
        Suggest tier upgrades based on restricted features.
        """
        if not restricted_features:
            return {
                "upgrade_needed": False,
                "message": "All features available in current tier"
            }
        
        # Find minimum tier needed for all restricted features
        required_tier = SubscriptionTier.BASIC
        for feature in restricted_features:
            if self._tier_hierarchy[feature.min_tier] > self._tier_hierarchy[required_tier]:
                required_tier = feature.min_tier
        
        return {
            "upgrade_needed": True,
            "current_tier": current_tier.value,
            "recommended_tier": required_tier.value,
            "unlocked_features": [f.name for f in restricted_features],
            "feature_count": len(restricted_features)
        }


# Singleton instance
_feature_engine = None

def get_feature_engine() -> FeatureAvailabilityEngine:
    """Get singleton instance of FeatureAvailabilityEngine"""
    global _feature_engine
    if _feature_engine is None:
        _feature_engine = FeatureAvailabilityEngine()
    return _feature_engine
