"""
Category Mapping Engine

Maps 50+ business categories to 4 template types with ML-enhanced selection.
"""

from typing import List, Dict, Tuple
from app.models.schemas import (
    BusinessCategory, TemplateType, CategoryMapping, SubscriptionTier
)
import logging

logger = logging.getLogger(__name__)


class CategoryMappingEngine:
    """
    Intelligent category to template mapping with confidence scoring.
    Future: ML-based continuous learning from selection patterns.
    """
    
    def __init__(self):
        self._mappings: Dict[BusinessCategory, Tuple[TemplateType, float, List[TemplateType]]] = {}
        self._initialize_mappings()
    
    def _initialize_mappings(self):
        """Initialize category to template mappings with confidence scores"""
        
        # Food & Hospitality Mappings
        food_categories = [
            BusinessCategory.RESTAURANT,
            BusinessCategory.CAFE,
            BusinessCategory.BAR,
            BusinessCategory.FOOD_TRUCK,
            BusinessCategory.BAKERY,
            BusinessCategory.CATERING,
            BusinessCategory.CLOUD_KITCHEN,
            BusinessCategory.HOTEL
        ]
        for cat in food_categories:
            self._mappings[cat] = (
                TemplateType.FOOD_HOSPITALITY,
                0.95,
                [TemplateType.RETAIL_ECOMMERCE]  # Alternative for e-commerce focused
            )
        
        # Service-Based Mappings
        service_categories = [
            BusinessCategory.SALON,
            BusinessCategory.SPA,
            BusinessCategory.BARBERSHOP,
            BusinessCategory.NAIL_SALON,
            BusinessCategory.MASSAGE_THERAPY,
            BusinessCategory.FITNESS_GYM,
            BusinessCategory.YOGA_STUDIO,
            BusinessCategory.PERSONAL_TRAINING,
            BusinessCategory.CLEANING_SERVICE,
            BusinessCategory.PLUMBING,
            BusinessCategory.ELECTRICAL,
            BusinessCategory.HVAC,
            BusinessCategory.LANDSCAPING,
            BusinessCategory.PET_GROOMING,
            BusinessCategory.AUTO_REPAIR
        ]
        for cat in service_categories:
            self._mappings[cat] = (
                TemplateType.SERVICE_BASED,
                0.95,
                [TemplateType.PROFESSIONAL_SERVICES]  # Alternative for appointment-heavy
            )
        
        # Retail & E-commerce Mappings
        retail_categories = [
            BusinessCategory.RETAIL_STORE,
            BusinessCategory.BOUTIQUE,
            BusinessCategory.GROCERY_STORE,
            BusinessCategory.PHARMACY,
            BusinessCategory.ELECTRONICS_STORE,
            BusinessCategory.BOOKSTORE,
            BusinessCategory.JEWELRY_STORE,
            BusinessCategory.FURNITURE_STORE,
            BusinessCategory.ECOMMERCE
        ]
        for cat in retail_categories:
            self._mappings[cat] = (
                TemplateType.RETAIL_ECOMMERCE,
                0.95,
                [TemplateType.FOOD_HOSPITALITY]  # Alternative for food retail
            )
        
        # Professional Services Mappings
        professional_categories = [
            BusinessCategory.LAW_FIRM,
            BusinessCategory.ACCOUNTING_FIRM,
            BusinessCategory.CONSULTING,
            BusinessCategory.MARKETING_AGENCY,
            BusinessCategory.REAL_ESTATE,
            BusinessCategory.INSURANCE_AGENCY,
            BusinessCategory.FINANCIAL_ADVISORY,
            BusinessCategory.ARCHITECTURE_FIRM,
            BusinessCategory.ENGINEERING_FIRM,
            BusinessCategory.IT_SERVICES,
            BusinessCategory.MEDICAL_PRACTICE,
            BusinessCategory.DENTAL_PRACTICE,
            BusinessCategory.VETERINARY_CLINIC,
            BusinessCategory.THERAPY_PRACTICE,
            BusinessCategory.PHOTOGRAPHY,
            BusinessCategory.EVENT_PLANNING,
            BusinessCategory.TUTORING,
            BusinessCategory.DAYCARE
        ]
        for cat in professional_categories:
            self._mappings[cat] = (
                TemplateType.PROFESSIONAL_SERVICES,
                0.95,
                [TemplateType.SERVICE_BASED]  # Alternative for service-oriented
            )
    
    def map_category_to_template(
        self,
        category: BusinessCategory,
        business_context: Dict = None
    ) -> CategoryMapping:
        """
        Map business category to template type with confidence scoring.
        
        Args:
            category: Business category
            business_context: Optional context for enhanced mapping (future ML enhancement)
        
        Returns:
            CategoryMapping with template, confidence, and alternatives
        """
        if category not in self._mappings:
            logger.warning(f"Unknown category: {category}, defaulting to PROFESSIONAL_SERVICES")
            return CategoryMapping(
                category=category,
                template_type=TemplateType.PROFESSIONAL_SERVICES,
                confidence_score=0.5,
                alternative_templates=[
                    TemplateType.SERVICE_BASED,
                    TemplateType.RETAIL_ECOMMERCE
                ],
                reasoning="Category not found in mapping, using default template"
            )
        
        template_type, confidence, alternatives = self._mappings[category]
        
        # Future: ML-based confidence adjustment based on business_context
        # For now, use static confidence scores
        
        reasoning = self._generate_reasoning(category, template_type)
        
        return CategoryMapping(
            category=category,
            template_type=template_type,
            confidence_score=confidence,
            alternative_templates=alternatives,
            reasoning=reasoning
        )
    
    def _generate_reasoning(self, category: BusinessCategory, template: TemplateType) -> str:
        """Generate human-readable reasoning for the mapping"""
        reasoning_map = {
            (BusinessCategory.RESTAURANT, TemplateType.FOOD_HOSPITALITY): 
                "Restaurant businesses benefit from menu management, table reservations, and kitchen operations features.",
            (BusinessCategory.SALON, TemplateType.SERVICE_BASED):
                "Salon businesses require appointment scheduling, client management, and service optimization.",
            (BusinessCategory.RETAIL_STORE, TemplateType.RETAIL_ECOMMERCE):
                "Retail stores need inventory management, sales processing, and customer insights.",
            (BusinessCategory.LAW_FIRM, TemplateType.PROFESSIONAL_SERVICES):
                "Law firms benefit from project management, time tracking, and client portal features.",
        }
        
        # Default reasoning
        default_reasoning = f"{category.value.replace('_', ' ').title()} businesses are best served by the {template.value.replace('_', ' ').title()} template."
        
        return reasoning_map.get((category, template), default_reasoning)
    
    def get_all_categories(self) -> List[Dict]:
        """Get all available business categories with metadata"""
        categories = []
        for category in BusinessCategory:
            mapping = self.map_category_to_template(category)
            categories.append({
                "category": category.value,
                "display_name": category.value.replace('_', ' ').title(),
                "template_type": mapping.template_type.value,
                "confidence": mapping.confidence_score,
                "alternatives": [t.value for t in mapping.alternative_templates]
            })
        return categories
    
    def suggest_template_for_keywords(self, keywords: List[str]) -> List[CategoryMapping]:
        """
        Suggest templates based on business keywords.
        Future: Use NLP/embeddings for semantic matching.
        """
        suggestions = []
        keyword_lower = [k.lower() for k in keywords]
        
        # Simple keyword matching (future: use embeddings)
        for category in BusinessCategory:
            category_words = category.value.lower().split('_')
            if any(kw in category_words for kw in keyword_lower):
                mapping = self.map_category_to_template(category)
                suggestions.append(mapping)
        
        return suggestions[:5]  # Top 5 suggestions


# Singleton instance
_category_mapper = None

def get_category_mapper() -> CategoryMappingEngine:
    """Get singleton instance of CategoryMappingEngine"""
    global _category_mapper
    if _category_mapper is None:
        _category_mapper = CategoryMappingEngine()
    return _category_mapper
