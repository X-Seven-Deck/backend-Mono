"""
AI Insight Engine Service
Anomaly detection, root cause analysis, and actionable recommendations
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
from decimal import Decimal
import numpy as np
from collections import defaultdict
import httpx

class AIInsightEngine:
    """AI-powered insight engine for business analytics"""
    
    def __init__(self):
        self.ai_orchestration_url = os.getenv(
            "AI_ORCHESTRATION_URL", 
            "http://ai-orchestration-service:8050"
        )
        self.anomaly_threshold = 2.5  # Standard deviations for anomaly detection
    
    async def detect_anomalies(
        self,
        business_id: UUID,
        metric_type: str,
        time_series_data: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies in time series data using statistical methods and AI
        
        Args:
            business_id: Business UUID
            metric_type: Type of metric (revenue, orders, inventory, etc.)
            time_series_data: List of {date, value} dictionaries
            context: Additional context for AI analysis
        
        Returns:
            Dictionary with anomalies, severity, and insights
        """
        try:
            if len(time_series_data) < 7:
                return {
                    "anomalies": [],
                    "message": "Insufficient data for anomaly detection (minimum 7 data points required)"
                }
            
            # Extract values and dates
            values = [float(d.get("value", 0)) for d in time_series_data]
            dates = [d.get("date") for d in time_series_data]
            
            # Calculate statistical measures
            mean = np.mean(values)
            std = np.std(values)
            
            # Detect anomalies using Z-score
            anomalies = []
            for i, (value, date_val) in enumerate(zip(values, dates)):
                if std > 0:
                    z_score = abs((value - mean) / std)
                    if z_score > self.anomaly_threshold:
                        severity = "high" if z_score > 3 else "medium"
                        anomalies.append({
                            "date": date_val,
                            "value": value,
                            "expected_value": mean,
                            "deviation": value - mean,
                            "z_score": z_score,
                            "severity": severity,
                            "type": "spike" if value > mean else "drop"
                        })
            
            # If anomalies detected, get AI analysis
            if anomalies:
                ai_analysis = await self._get_ai_analysis(
                    business_id=business_id,
                    metric_type=metric_type,
                    anomalies=anomalies,
                    context=context or {}
                )
            else:
                ai_analysis = {
                    "root_causes": [],
                    "recommendations": ["No anomalies detected. Performance is within normal range."],
                    "impact_assessment": "low"
                }
            
            return {
                "anomalies": anomalies,
                "statistics": {
                    "mean": mean,
                    "std": std,
                    "min": min(values),
                    "max": max(values),
                    "trend": self._calculate_trend(values)
                },
                "ai_analysis": ai_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "anomalies": [],
                "message": "Error detecting anomalies"
            }
    
    async def analyze_root_causes(
        self,
        business_id: UUID,
        issue_description: str,
        metrics_data: Dict[str, Any],
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform root cause analysis using AI
        
        Args:
            business_id: Business UUID
            issue_description: Description of the issue
            metrics_data: Relevant metrics data
            business_context: Business context (category, location, etc.)
        
        Returns:
            Root causes, contributing factors, and recommendations
        """
        try:
            # Call AI orchestration service for deep analysis
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_orchestration_url}/api/v1/ai-features/root-cause-analysis",
                    json={
                        "business_id": str(business_id),
                        "issue_description": issue_description,
                        "metrics_data": metrics_data,
                        "business_context": business_context
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return self._fallback_root_cause_analysis(
                        issue_description, metrics_data
                    )
        except Exception as e:
            return self._fallback_root_cause_analysis(
                issue_description, metrics_data
            )
    
    async def generate_actionable_recommendations(
        self,
        business_id: UUID,
        business_category: str,
        current_metrics: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        goals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered actionable recommendations
        
        Args:
            business_id: Business UUID
            business_category: Business category (food, service, retail, professional)
            current_metrics: Current business metrics
            historical_data: Historical performance data
            goals: Business goals and targets
        
        Returns:
            Prioritized recommendations with implementation steps
        """
        try:
            # Analyze performance gaps
            performance_gaps = self._identify_performance_gaps(
                current_metrics, goals or {}
            )
            
            # Get AI-powered recommendations
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_orchestration_url}/api/v1/ai-features/generate-recommendations",
                    json={
                        "business_id": str(business_id),
                        "category": business_category,
                        "current_metrics": current_metrics,
                        "historical_data": historical_data[:30],  # Last 30 data points
                        "performance_gaps": performance_gaps,
                        "goals": goals or {}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return self._fallback_recommendations(
                        business_category, performance_gaps
                    )
        except Exception as e:
            return self._fallback_recommendations(
                business_category, {}
            )
    
    async def predict_future_trends(
        self,
        business_id: UUID,
        metric_type: str,
        historical_data: List[Dict[str, Any]],
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Predict future trends using statistical forecasting and AI
        
        Args:
            business_id: Business UUID
            metric_type: Type of metric to forecast
            historical_data: Historical time series data
            forecast_days: Number of days to forecast
        
        Returns:
            Forecast with confidence intervals
        """
        try:
            if len(historical_data) < 14:
                return {
                    "error": "Insufficient data for forecasting (minimum 14 data points required)",
                    "forecast": []
                }
            
            # Simple moving average forecast (can be enhanced with ARIMA, Prophet, etc.)
            values = [float(d.get("value", 0)) for d in historical_data]
            
            # Calculate trend
            trend = self._calculate_trend(values)
            
            # Simple forecast using trend and recent average
            recent_avg = np.mean(values[-7:])  # Last week average
            forecast = []
            
            last_date = datetime.fromisoformat(historical_data[-1]["date"]) if isinstance(historical_data[-1]["date"], str) else historical_data[-1]["date"]
            
            for i in range(1, forecast_days + 1):
                forecast_date = last_date + timedelta(days=i)
                forecast_value = recent_avg * (1 + (trend * i / 100))
                
                # Add confidence interval (±10% for simplicity)
                forecast.append({
                    "date": forecast_date.isoformat(),
                    "predicted_value": forecast_value,
                    "lower_bound": forecast_value * 0.9,
                    "upper_bound": forecast_value * 1.1,
                    "confidence": 0.80
                })
            
            return {
                "metric_type": metric_type,
                "forecast": forecast,
                "trend": trend,
                "methodology": "moving_average_with_trend",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "forecast": []
            }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend as percentage change"""
        if len(values) < 2:
            return 0.0
        
        # Linear regression for trend
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        slope = coefficients[0]
        
        # Convert to percentage
        avg_value = np.mean(values)
        if avg_value > 0:
            trend_percentage = (slope / avg_value) * 100
        else:
            trend_percentage = 0.0
        
        return round(trend_percentage, 2)
    
    async def _get_ai_analysis(
        self,
        business_id: UUID,
        metric_type: str,
        anomalies: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI analysis of anomalies"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_orchestration_url}/api/v1/ai-features/analyze-anomaly",
                    json={
                        "business_id": str(business_id),
                        "metric_type": metric_type,
                        "anomalies": anomalies,
                        "context": context
                    },
                    timeout=20.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return self._fallback_ai_analysis(metric_type, anomalies)
        except Exception:
            return self._fallback_ai_analysis(metric_type, anomalies)
    
    def _fallback_ai_analysis(
        self,
        metric_type: str,
        anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback analysis when AI service is unavailable"""
        root_causes = []
        recommendations = []
        
        # Analyze anomaly patterns
        spikes = [a for a in anomalies if a["type"] == "spike"]
        drops = [a for a in anomalies if a["type"] == "drop"]
        
        if spikes:
            root_causes.append(f"Unusual spike in {metric_type} detected")
            recommendations.append(f"Investigate causes of increased {metric_type}")
        
        if drops:
            root_causes.append(f"Significant drop in {metric_type} observed")
            recommendations.append(f"Review factors contributing to decreased {metric_type}")
        
        # Impact assessment
        high_severity = [a for a in anomalies if a["severity"] == "high"]
        impact = "high" if high_severity else "medium"
        
        return {
            "root_causes": root_causes,
            "recommendations": recommendations,
            "impact_assessment": impact,
            "confidence": 0.7
        }
    
    def _fallback_root_cause_analysis(
        self,
        issue_description: str,
        metrics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback root cause analysis"""
        return {
            "root_causes": [
                "Statistical analysis indicates potential operational inefficiencies",
                "External factors may be impacting performance"
            ],
            "contributing_factors": [
                "Historical data patterns",
                "Industry benchmarks"
            ],
            "recommendations": [
                "Review operational processes",
                "Analyze market conditions",
                "Consult with industry experts"
            ],
            "confidence": 0.6,
            "methodology": "rule_based_analysis"
        }
    
    def _identify_performance_gaps(
        self,
        current_metrics: Dict[str, Any],
        goals: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify gaps between current performance and goals"""
        gaps = []
        
        for metric_name, target_value in goals.items():
            current_value = current_metrics.get(metric_name)
            if current_value is not None:
                gap_percentage = ((target_value - current_value) / target_value * 100) if target_value > 0 else 0
                
                if abs(gap_percentage) > 5:  # 5% threshold
                    gaps.append({
                        "metric": metric_name,
                        "current": current_value,
                        "target": target_value,
                        "gap": target_value - current_value,
                        "gap_percentage": gap_percentage
                    })
        
        return gaps
    
    def _fallback_recommendations(
        self,
        business_category: str,
        performance_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback recommendations when AI service unavailable"""
        # Category-specific recommendations
        category_recommendations = {
            "food": [
                "Optimize menu mix based on popularity and profitability",
                "Implement dynamic pricing during peak hours",
                "Reduce food waste through better inventory management"
            ],
            "service": [
                "Improve appointment scheduling efficiency",
                "Implement client retention programs",
                "Optimize service pricing and packages"
            ],
            "retail": [
                "Optimize inventory levels to reduce stockouts",
                "Implement personalized marketing campaigns",
                "Improve product placement and merchandising"
            ],
            "professional": [
                "Increase billable hours through better time tracking",
                "Improve project scoping and estimation",
                "Implement value-based pricing strategies"
            ]
        }
        
        recommendations = category_recommendations.get(business_category, [
            "Review and optimize operational processes",
            "Analyze customer behavior and preferences",
            "Implement data-driven decision making"
        ])
        
        return {
            "recommendations": [
                {
                    "title": rec,
                    "priority": "high" if i < 2 else "medium",
                    "category": "operational_efficiency",
                    "estimated_impact": "high" if i == 0 else "medium",
                    "implementation_steps": [
                        "Analyze current state",
                        "Develop action plan",
                        "Implement changes",
                        "Monitor results"
                    ]
                }
                for i, rec in enumerate(recommendations)
            ],
            "performance_gaps": performance_gaps,
            "confidence": 0.7,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_ai_insight_engine: Optional[AIInsightEngine] = None


def get_ai_insight_engine() -> AIInsightEngine:
    """Get AI insight engine singleton"""
    global _ai_insight_engine
    if _ai_insight_engine is None:
        _ai_insight_engine = AIInsightEngine()
    return _ai_insight_engine
