"""
Template Selection API Routes

Enterprise-grade REST API for template selection and configuration.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List
from app.models.schemas import (
    TemplateSelectionRequest, TemplateSelectionResponse, TemplatePreviewRequest,
    TemplateCustomizationRequest, FeatureToggleRequest, TemplateType,
    BusinessCategory, SubscriptionTier
)
from app.services.template_service import get_template_service
from app.services.category_mapper import get_category_mapper
from app.services.template_config import get_template_config_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/template-selection", tags=["Template Selection"])


@router.post("/select", response_model=TemplateSelectionResponse, status_code=status.HTTP_200_OK)
async def select_template(request: TemplateSelectionRequest):
    """
    Select and configure template for a business.
    
    **Main Entry Point** - Returns complete template configuration with:
    - Selected template type
    - Available and restricted features
    - API endpoints
    - Dashboard widgets
    - LangGraph workflows
    - CrewAI agents
    - Customization options
    
    **Response Time:** <100ms (with caching)
    """
    try:
        service = get_template_service()
        response = await service.select_template(request)
        return response
    except ValueError as e:
        logger.error(f"Template selection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in template selection: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during template selection"
        )


@router.get("/categories", status_code=status.HTTP_200_OK)
async def get_all_categories():
    """
    Get all 50+ available business categories with metadata.
    
    Returns:
    - Category name and display name
    - Mapped template type
    - Confidence score
    - Alternative templates
    """
    try:
        mapper = get_category_mapper()
        categories = mapper.get_all_categories()
        return {
            "total_categories": len(categories),
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching categories"
        )


@router.get("/templates", status_code=status.HTTP_200_OK)
async def get_all_templates():
    """
    Get all 4 template configurations with their feature sets.
    
    Returns complete metadata for:
    - Food & Hospitality
    - Service-Based
    - Retail & E-commerce
    - Professional Services
    """
    try:
        config_service = get_template_config_service()
        templates = config_service.get_all_templates()
        
        return {
            "total_templates": len(templates),
            "templates": [
                {
                    "template_type": tmpl.template_type.value,
                    "name": tmpl.name,
                    "description": tmpl.description,
                    "icon": tmpl.icon,
                    "color_scheme": tmpl.color_scheme,
                    "features_count": len(tmpl.ai_features),
                    "api_endpoints_count": len(tmpl.api_endpoints),
                    "dashboard_widgets_count": len(tmpl.dashboard_widgets),
                    "workflows": tmpl.langgraph_workflows,
                    "agents": tmpl.crewai_agents,
                    "required_integrations": tmpl.required_integrations,
                    "optional_integrations": tmpl.optional_integrations
                }
                for tmpl in templates.values()
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching templates"
        )


@router.get("/templates/{template_type}", status_code=status.HTTP_200_OK)
async def get_template_details(template_type: TemplateType):
    """
    Get detailed configuration for a specific template.
    
    Includes:
    - All AI features (universal + category-specific)
    - API endpoints with methods and descriptions
    - Dashboard widgets with configurations
    - Workflow and agent definitions
    - Integration requirements
    """
    try:
        config_service = get_template_config_service()
        template = config_service.get_template(template_type)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_type.value} not found"
            )
        
        return {
            "template_type": template.template_type.value,
            "name": template.name,
            "description": template.description,
            "icon": template.icon,
            "color_scheme": template.color_scheme,
            "ai_features": [
                {
                    "feature_type": f.feature_type.value,
                    "name": f.name,
                    "description": f.description,
                    "is_universal": f.is_universal,
                    "min_tier": f.min_tier.value,
                    "configuration": f.configuration
                }
                for f in template.ai_features
            ],
            "api_endpoints": [
                {
                    "method": e.method,
                    "path": e.path,
                    "description": e.description,
                    "requires_auth": e.requires_auth,
                    "rate_limit": e.rate_limit
                }
                for e in template.api_endpoints
            ],
            "dashboard_widgets": [
                {
                    "widget_id": w.widget_id,
                    "name": w.name,
                    "type": w.type,
                    "position": w.position,
                    "data_source": w.data_source,
                    "refresh_interval": w.refresh_interval
                }
                for w in template.dashboard_widgets
            ],
            "langgraph_workflows": template.langgraph_workflows,
            "crewai_agents": template.crewai_agents,
            "data_models": template.data_models,
            "required_integrations": template.required_integrations,
            "optional_integrations": template.optional_integrations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching template details"
        )


@router.post("/preview", status_code=status.HTTP_200_OK)
async def preview_template(request: TemplatePreviewRequest):
    """
    Preview template configuration before applying.
    
    Shows:
    - Template metadata
    - Available vs restricted features based on tier
    - Feature counts and descriptions
    - Confidence score and reasoning
    """
    try:
        service = get_template_service()
        preview = await service.preview_template(request)
        return preview
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error previewing template"
        )


@router.post("/customize", status_code=status.HTTP_200_OK)
async def customize_template(request: TemplateCustomizationRequest):
    """
    Customize template features for specific business needs.
    
    Allows:
    - Enabling/disabling specific features
    - Adding custom widgets
    - Adding custom API endpoints
    - Feature validation against template
    """
    try:
        service = get_template_service()
        result = await service.customize_template(request)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("errors", ["Customization failed"])
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error customizing template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error customizing template"
        )


@router.post("/features/toggle", status_code=status.HTTP_200_OK)
async def toggle_feature(request: FeatureToggleRequest):
    """
    Real-time feature toggle for a business.
    
    Enables dynamic feature management without redeployment.
    Useful for:
    - A/B testing
    - Gradual rollouts
    - Emergency feature disabling
    - Tier-based access control
    """
    try:
        service = get_template_service()
        result = await service.toggle_feature(request)
        return result
    except Exception as e:
        logger.error(f"Error toggling feature: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error toggling feature"
        )


@router.get("/analytics", status_code=status.HTTP_200_OK)
async def get_template_analytics(
    template_type: Optional[TemplateType] = Query(None, description="Filter by template type")
):
    """
    Get template usage analytics.
    
    Provides:
    - Total and active business counts
    - Feature adoption rates
    - Satisfaction scores
    - Most/least used features
    """
    try:
        service = get_template_service()
        analytics = await service.get_template_analytics(template_type)
        
        return {
            "analytics": [
                {
                    "template_type": a.template_type.value,
                    "total_businesses": a.total_businesses,
                    "active_businesses": a.active_businesses,
                    "feature_adoption_rates": a.feature_adoption_rates,
                    "avg_satisfaction_score": a.avg_satisfaction_score,
                    "most_used_features": a.most_used_features,
                    "least_used_features": a.least_used_features
                }
                for a in analytics
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching analytics"
        )


@router.get("/business/{business_id}/context", status_code=status.HTTP_200_OK)
async def get_business_context(business_id: str):
    """
    Get business context for AI enhancement.
    
    Returns:
    - Industry insights
    - Usage patterns
    - Performance metrics
    - Recommended features
    """
    try:
        service = get_template_service()
        context = await service.get_business_context(business_id)
        
        return {
            "business_id": context.business_id,
            "template_type": context.template_type.value,
            "industry_insights": context.industry_insights,
            "usage_patterns": context.usage_patterns,
            "performance_metrics": context.performance_metrics,
            "recommended_features": [f.value for f in context.recommended_features]
        }
    except Exception as e:
        logger.error(f"Error fetching business context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching business context"
        )


@router.get("/categories/search", status_code=status.HTTP_200_OK)
async def search_categories_by_keywords(
    keywords: List[str] = Query(..., description="Keywords to search for")
):
    """
    Search categories by keywords.
    
    Future: Use NLP/embeddings for semantic matching.
    """
    try:
        mapper = get_category_mapper()
        suggestions = mapper.suggest_template_for_keywords(keywords)
        
        return {
            "keywords": keywords,
            "suggestions": [
                {
                    "category": s.category.value,
                    "template_type": s.template_type.value,
                    "confidence_score": s.confidence_score,
                    "reasoning": s.reasoning
                }
                for s in suggestions
            ]
        }
    except Exception as e:
        logger.error(f"Error searching categories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching categories"
        )
