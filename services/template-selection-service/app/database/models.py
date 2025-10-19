"""
Database models and migrations for template analytics.

Tracks template selections, feature usage, and business context.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TemplateSelection(Base):
    """Track template selections for analytics"""
    __tablename__ = "template_selections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(255), nullable=False, index=True)
    business_name = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    selected_template = Column(String(100), nullable=False, index=True)
    subscription_tier = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Business context
    business_size = Column(String(50))
    custom_requirements = Column(JSON)
    
    # Template details
    features_count = Column(Integer)
    available_features = Column(JSON)
    restricted_features = Column(JSON)
    
    # Metadata
    selection_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    __table_args__ = (
        Index('idx_business_template', 'business_id', 'selected_template'),
        Index('idx_category_tier', 'category', 'subscription_tier'),
        Index('idx_timestamp', 'selection_timestamp'),
    )


class FeatureUsage(Base):
    """Track feature usage and adoption"""
    __tablename__ = "feature_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(255), nullable=False, index=True)
    template_type = Column(String(100), nullable=False, index=True)
    feature_type = Column(String(100), nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    
    # Usage metrics
    enabled = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    total_execution_time_ms = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_business_feature', 'business_id', 'feature_type'),
        Index('idx_template_feature', 'template_type', 'feature_type'),
        Index('idx_enabled', 'enabled'),
    )


class FeatureToggle(Base):
    """Track feature toggle history"""
    __tablename__ = "feature_toggles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(255), nullable=False, index=True)
    feature_type = Column(String(100), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False)
    reason = Column(Text)
    
    # Audit fields
    toggled_by = Column(String(255))  # user_id or 'system'
    toggled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_business_feature_toggle', 'business_id', 'feature_type'),
        Index('idx_toggle_timestamp', 'toggled_at'),
    )


class TemplateCustomization(Base):
    """Track template customizations"""
    __tablename__ = "template_customizations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(255), nullable=False, unique=True, index=True)
    template_type = Column(String(100), nullable=False)
    
    # Customizations
    custom_widgets = Column(JSON)
    custom_endpoints = Column(JSON)
    custom_workflows = Column(JSON)
    color_scheme_override = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_template_type', 'template_type'),
    )


class BusinessContext(Base):
    """Store business context for AI enhancement"""
    __tablename__ = "business_contexts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String(255), nullable=False, unique=True, index=True)
    template_type = Column(String(100), nullable=False)
    
    # Industry insights
    industry_insights = Column(JSON)
    usage_patterns = Column(JSON)
    performance_metrics = Column(JSON)
    
    # AI recommendations
    recommended_features = Column(JSON)
    optimization_suggestions = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_analyzed_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_last_analyzed', 'last_analyzed_at'),
    )


class TemplateAnalytics(Base):
    """Aggregated template analytics"""
    __tablename__ = "template_analytics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_type = Column(String(100), nullable=False, unique=True, index=True)
    
    # Business metrics
    total_businesses = Column(Integer, default=0)
    active_businesses = Column(Integer, default=0)
    churned_businesses = Column(Integer, default=0)
    
    # Feature metrics
    feature_adoption_rates = Column(JSON)
    avg_features_enabled = Column(Float, default=0.0)
    
    # Performance metrics
    avg_satisfaction_score = Column(Float)
    avg_response_time_ms = Column(Float)
    error_rate = Column(Float)
    
    # Popular features
    most_used_features = Column(JSON)
    least_used_features = Column(JSON)
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    calculation_period_days = Column(Integer, default=30)


class CategoryMapping(Base):
    """ML-enhanced category mappings"""
    __tablename__ = "category_mappings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, unique=True, index=True)
    template_type = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    alternative_templates = Column(JSON)
    
    # ML metrics
    selection_count = Column(Integer, default=0)
    override_count = Column(Integer, default=0)  # Times users chose alternative
    avg_user_satisfaction = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_ml_update = Column(DateTime)
    
    __table_args__ = (
        Index('idx_template_confidence', 'template_type', 'confidence_score'),
    )


# Migration Script
if __name__ == "__main__":
    from sqlalchemy import create_engine
    import os
    
    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/template_analytics"
    )
    
    # Create engine
    engine = create_engine(database_url)
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✅ All tables created successfully!")
    
    # Print table names
    print("\nCreated tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
