"""
Predictive Intelligence Service
Revenue forecasting, demand prediction, churn analysis, and trend forecasting
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
from uuid import UUID
from decimal import Decimal
import numpy as np
from collections import defaultdict
import httpx

class PredictiveIntelligence:
    """AI-powered predictive analytics for business forecasting"""
    
    def __init__(self):
        self.ai_orchestration_url = os.getenv(
            "AI_ORCHESTRATION_URL",
            "http://ai-orchestration-service:8050"
        )
        self.min_data_points = 14  # Minimum data points for predictions
    
    async def forecast_revenue(
        self,
        business_id: UUID,
        business_category: str,
        historical_revenue: List[Dict[str, Any]],
        forecast_period: int = 30,
        external_factors: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Forecast future revenue using AI and statistical models
        
        Args:
            business_id: Business UUID
            business_category: Business category
            historical_revenue: Historical revenue data [{date, value}]
            forecast_period: Days to forecast
            external_factors: External factors (weather, events, etc.)
        
        Returns:
            Revenue forecast with confidence intervals
        """
        try:
            if len(historical_revenue) < self.min_data_points:
                return {
                    "error": f"Insufficient data (minimum {self.min_data_points} days required)",
                    "forecast": []
                }
            
            # Try AI-powered forecast first
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.ai_orchestration_url}/api/v1/ai-features/forecast-revenue",
                        json={
                            "business_id": str(business_id),
                            "category": business_category,
                            "historical_data": historical_revenue,
                            "forecast_days": forecast_period,
                            "external_factors": external_factors or {}
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        return response.json()
            except Exception:
                pass  # Fall through to statistical forecast
            
            # Statistical forecast using multiple methods
            forecast = self._statistical_revenue_forecast(
                historical_revenue, forecast_period
            )
            
            # Calculate accuracy metrics from historical data
            accuracy_metrics = self._calculate_forecast_accuracy(historical_revenue)
            
            return {
                "business_id": str(business_id),
                "forecast": forecast,
                "accuracy_metrics": accuracy_metrics,
                "methodology": "statistical_ensemble",
                "confidence_level": 0.80,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "forecast": []
            }
    
    async def predict_demand(
        self,
        business_id: UUID,
        business_category: str,
        item_type: str,
        historical_demand: List[Dict[str, Any]],
        forecast_period: int = 7,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict demand for products/services/menu items
        
        Args:
            business_id: Business UUID
            business_category: Business category
            item_type: Type (menu_item, product, service, appointment)
            historical_demand: Historical demand data
            forecast_period: Days to forecast
            context: Additional context (promotions, season, etc.)
        
        Returns:
            Demand forecast with recommended actions
        """
        try:
            if len(historical_demand) < 7:
                return {
                    "error": "Insufficient demand history (minimum 7 days required)",
                    "forecast": []
                }
            
            # Extract demand values
            demand_values = [float(d.get("quantity", 0)) for d in historical_demand]
            dates = [d.get("date") for d in historical_demand]
            
            # Calculate patterns
            patterns = self._detect_demand_patterns(demand_values)
            
            # Generate forecast
            forecast = []
            last_date = datetime.fromisoformat(dates[-1]) if isinstance(dates[-1], str) else dates[-1]
            
            # Use recent average with pattern adjustment
            recent_avg = np.mean(demand_values[-7:])
            
            for i in range(1, forecast_period + 1):
                forecast_date = last_date + timedelta(days=i)
                day_of_week = forecast_date.weekday()
                
                # Apply day-of-week pattern if detected
                if patterns.get("weekly_pattern"):
                    pattern_multiplier = patterns["weekly_pattern"].get(day_of_week, 1.0)
                else:
                    pattern_multiplier = 1.0
                
                predicted_demand = recent_avg * pattern_multiplier
                
                forecast.append({
                    "date": forecast_date.isoformat(),
                    "predicted_demand": round(predicted_demand, 2),
                    "lower_bound": round(predicted_demand * 0.8, 2),
                    "upper_bound": round(predicted_demand * 1.2, 2),
                    "day_of_week": forecast_date.strftime("%A"),
                    "confidence": 0.75
                })
            
            # Generate recommendations
            recommendations = self._generate_demand_recommendations(
                business_category, item_type, forecast, patterns
            )
            
            return {
                "business_id": str(business_id),
                "item_type": item_type,
                "forecast": forecast,
                "patterns": patterns,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "forecast": []
            }
    
    async def predict_customer_churn(
        self,
        business_id: UUID,
        business_category: str,
        customer_data: List[Dict[str, Any]],
        analysis_period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Predict customer churn risk and identify at-risk customers
        
        Args:
            business_id: Business UUID
            business_category: Business category
            customer_data: Customer transaction history
            analysis_period_days: Days to analyze
        
        Returns:
            Churn predictions with retention recommendations
        """
        try:
            if len(customer_data) == 0:
                return {
                    "error": "No customer data available",
                    "at_risk_customers": []
                }
            
            at_risk_customers = []
            retention_opportunities = []
            
            # Analyze each customer
            for customer in customer_data:
                churn_risk = self._calculate_churn_risk(customer, analysis_period_days)
                
                if churn_risk["risk_score"] > 0.6:  # High risk threshold
                    at_risk_customers.append({
                        "customer_id": customer.get("customer_id"),
                        "customer_name": customer.get("name", "Unknown"),
                        "risk_score": churn_risk["risk_score"],
                        "risk_level": churn_risk["risk_level"],
                        "risk_factors": churn_risk["risk_factors"],
                        "last_interaction": customer.get("last_order_date"),
                        "lifetime_value": customer.get("total_spent", 0),
                        "recommended_actions": churn_risk["recommended_actions"]
                    })
                
                if 0.4 < churn_risk["risk_score"] <= 0.6:  # Medium risk
                    retention_opportunities.append({
                        "customer_id": customer.get("customer_id"),
                        "customer_name": customer.get("name", "Unknown"),
                        "opportunity_type": "retention_campaign",
                        "estimated_value": customer.get("total_spent", 0)
                    })
            
            # Calculate overall churn metrics
            total_customers = len(customer_data)
            high_risk_count = len(at_risk_customers)
            churn_rate = (high_risk_count / total_customers * 100) if total_customers > 0 else 0
            
            return {
                "business_id": str(business_id),
                "summary": {
                    "total_customers": total_customers,
                    "at_risk_count": high_risk_count,
                    "churn_rate": round(churn_rate, 2),
                    "retention_opportunities": len(retention_opportunities)
                },
                "at_risk_customers": sorted(
                    at_risk_customers,
                    key=lambda x: x["risk_score"],
                    reverse=True
                )[:20],  # Top 20 at-risk customers
                "retention_opportunities": retention_opportunities[:10],
                "recommendations": self._generate_churn_prevention_strategies(
                    business_category, at_risk_customers
                ),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "at_risk_customers": []
            }
    
    async def analyze_trends(
        self,
        business_id: UUID,
        metric_type: str,
        time_series_data: List[Dict[str, Any]],
        comparison_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze trends in business metrics
        
        Args:
            business_id: Business UUID
            metric_type: Type of metric
            time_series_data: Time series data
            comparison_period: Period to compare against (previous_week, previous_month, etc.)
        
        Returns:
            Trend analysis with insights
        """
        try:
            if len(time_series_data) < 7:
                return {
                    "error": "Insufficient data for trend analysis",
                    "trend": "unknown"
                }
            
            values = [float(d.get("value", 0)) for d in time_series_data]
            dates = [d.get("date") for d in time_series_data]
            
            # Calculate trend direction and strength
            trend_direction = self._calculate_trend_direction(values)
            trend_strength = self._calculate_trend_strength(values)
            
            # Identify seasonality
            seasonality = self._detect_seasonality(values)
            
            # Calculate growth rate
            growth_rate = self._calculate_growth_rate(values)
            
            # Forecast next period
            next_period_forecast = self._forecast_next_period(values, dates)
            
            # Generate insights
            insights = self._generate_trend_insights(
                metric_type,
                trend_direction,
                trend_strength,
                growth_rate,
                seasonality
            )
            
            return {
                "business_id": str(business_id),
                "metric_type": metric_type,
                "trend": {
                    "direction": trend_direction,
                    "strength": trend_strength,
                    "growth_rate": growth_rate,
                    "seasonality": seasonality
                },
                "forecast": next_period_forecast,
                "insights": insights,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "trend": "unknown"
            }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _statistical_revenue_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_days: int
    ) -> List[Dict[str, Any]]:
        """Statistical ensemble forecast combining multiple methods"""
        values = [float(d.get("value", 0)) for d in historical_data]
        dates = [d.get("date") for d in historical_data]
        
        last_date = datetime.fromisoformat(dates[-1]) if isinstance(dates[-1], str) else dates[-1]
        
        # Method 1: Moving Average
        ma_window = min(7, len(values))
        ma_forecast = np.mean(values[-ma_window:])
        
        # Method 2: Exponential Smoothing
        alpha = 0.3
        es_forecast = values[-1]
        for value in values[-ma_window:]:
            es_forecast = alpha * value + (1 - alpha) * es_forecast
        
        # Method 3: Linear Trend
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        trend_slope = coefficients[0]
        trend_intercept = coefficients[1]
        
        forecast = []
        for i in range(1, forecast_days + 1):
            forecast_date = last_date + timedelta(days=i)
            
            # Ensemble prediction (weighted average)
            trend_pred = trend_slope * (len(values) + i) + trend_intercept
            ensemble_pred = (ma_forecast * 0.3 + es_forecast * 0.3 + trend_pred * 0.4)
            
            # Add day-of-week adjustment
            dow_multiplier = self._get_day_of_week_multiplier(
                forecast_date.weekday(),
                values,
                [datetime.fromisoformat(d) if isinstance(d, str) else d for d in dates]
            )
            adjusted_pred = ensemble_pred * dow_multiplier
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_revenue": round(max(0, adjusted_pred), 2),
                "lower_bound": round(max(0, adjusted_pred * 0.85), 2),
                "upper_bound": round(adjusted_pred * 1.15, 2),
                "confidence": 0.80,
                "day_of_week": forecast_date.strftime("%A")
            })
        
        return forecast
    
    def _get_day_of_week_multiplier(
        self,
        day_of_week: int,
        values: List[float],
        dates: List[datetime]
    ) -> float:
        """Calculate day-of-week multiplier based on historical patterns"""
        if len(values) < 14:
            return 1.0
        
        # Group by day of week
        dow_values = defaultdict(list)
        for date, value in zip(dates, values):
            dow_values[date.weekday()].append(value)
        
        # Calculate average for this day
        if dow_values[day_of_week]:
            dow_avg = np.mean(dow_values[day_of_week])
            overall_avg = np.mean(values)
            if overall_avg > 0:
                return dow_avg / overall_avg
        
        return 1.0
    
    def _calculate_forecast_accuracy(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate forecast accuracy metrics"""
        if len(historical_data) < 14:
            return {"mape": None, "mae": None}
        
        values = [float(d.get("value", 0)) for d in historical_data]
        
        # Calculate MAPE (Mean Absolute Percentage Error) on recent data
        actual = values[-7:]
        predicted = values[-14:-7]
        
        if len(actual) == len(predicted):
            mape = np.mean([
                abs((a - p) / a * 100) if a > 0 else 0
                for a, p in zip(actual, predicted)
            ])
            mae = np.mean([abs(a - p) for a, p in zip(actual, predicted)])
        else:
            mape = None
            mae = None
        
        return {
            "mape": round(mape, 2) if mape is not None else None,
            "mae": round(mae, 2) if mae is not None else None,
            "r_squared": self._calculate_r_squared(values)
        }
    
    def _calculate_r_squared(self, values: List[float]) -> float:
        """Calculate R-squared for trend fit"""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        predicted = np.polyval(coefficients, x)
        
        ss_res = np.sum((np.array(values) - predicted) ** 2)
        ss_tot = np.sum((np.array(values) - np.mean(values)) ** 2)
        
        if ss_tot > 0:
            r_squared = 1 - (ss_res / ss_tot)
            return round(max(0, min(1, r_squared)), 3)
        
        return 0.0
    
    def _detect_demand_patterns(self, demand_values: List[float]) -> Dict[str, Any]:
        """Detect patterns in demand data"""
        patterns = {}
        
        if len(demand_values) >= 7:
            # Weekly pattern (if we have at least 2 weeks of data)
            if len(demand_values) >= 14:
                weekly_avg = []
                for i in range(7):
                    day_values = [demand_values[j] for j in range(i, len(demand_values), 7)]
                    if day_values:
                        weekly_avg.append(np.mean(day_values))
                
                if len(weekly_avg) == 7:
                    overall_avg = np.mean(demand_values)
                    if overall_avg > 0:
                        weekly_pattern = {
                            i: avg / overall_avg
                            for i, avg in enumerate(weekly_avg)
                        }
                        patterns["weekly_pattern"] = weekly_pattern
            
            # Trend
            trend_direction = "increasing" if demand_values[-1] > demand_values[0] else "decreasing"
            patterns["trend"] = trend_direction
            
            # Volatility
            std_dev = np.std(demand_values)
            mean_val = np.mean(demand_values)
            volatility = (std_dev / mean_val * 100) if mean_val > 0 else 0
            patterns["volatility"] = round(volatility, 2)
        
        return patterns
    
    def _generate_demand_recommendations(
        self,
        business_category: str,
        item_type: str,
        forecast: List[Dict[str, Any]],
        patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on demand forecast"""
        recommendations = []
        
        # Analyze forecast for high/low demand days
        avg_demand = np.mean([f["predicted_demand"] for f in forecast])
        high_demand_days = [f for f in forecast if f["predicted_demand"] > avg_demand * 1.2]
        low_demand_days = [f for f in forecast if f["predicted_demand"] < avg_demand * 0.8]
        
        if high_demand_days:
            recommendations.append(
                f"Prepare for high demand on {', '.join([d['day_of_week'] for d in high_demand_days[:3]])}"
            )
            if business_category == "food":
                recommendations.append("Increase inventory levels for high-demand ingredients")
            elif business_category == "service":
                recommendations.append("Schedule additional staff for peak demand days")
        
        if low_demand_days:
            recommendations.append(
                f"Consider promotions on {', '.join([d['day_of_week'] for d in low_demand_days[:2]])}"
            )
        
        # Volatility-based recommendations
        if patterns.get("volatility", 0) > 30:
            recommendations.append("High demand volatility detected - implement flexible staffing")
        
        return recommendations
    
    def _calculate_churn_risk(
        self,
        customer: Dict[str, Any],
        analysis_period_days: int
    ) -> Dict[str, Any]:
        """Calculate churn risk score for a customer"""
        risk_score = 0.0
        risk_factors = []
        
        # Factor 1: Recency (days since last interaction)
        last_order_date = customer.get("last_order_date")
        if last_order_date:
            if isinstance(last_order_date, str):
                last_order_date = datetime.fromisoformat(last_order_date.replace('Z', '+00:00'))
            days_since_last_order = (datetime.now(last_order_date.tzinfo) - last_order_date).days
            
            if days_since_last_order > 90:
                risk_score += 0.4
                risk_factors.append("No activity in over 90 days")
            elif days_since_last_order > 60:
                risk_score += 0.25
                risk_factors.append("No activity in over 60 days")
            elif days_since_last_order > 30:
                risk_score += 0.1
                risk_factors.append("No activity in over 30 days")
        
        # Factor 2: Frequency decline
        total_orders = customer.get("total_orders", 0)
        recent_orders = customer.get("recent_orders", 0)
        if total_orders > 0:
            frequency_ratio = recent_orders / total_orders
            if frequency_ratio < 0.2:
                risk_score += 0.3
                risk_factors.append("Significant decline in order frequency")
        
        # Factor 3: Monetary value decline
        total_spent = customer.get("total_spent", 0)
        recent_spent = customer.get("recent_spent", 0)
        if total_spent > 0:
            spend_ratio = recent_spent / total_spent
            if spend_ratio < 0.2:
                risk_score += 0.2
                risk_factors.append("Declining spend pattern")
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate recommended actions
        recommended_actions = self._generate_retention_actions(
            risk_level, risk_factors, customer
        )
        
        return {
            "risk_score": min(1.0, risk_score),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommended_actions": recommended_actions
        }
    
    def _generate_retention_actions(
        self,
        risk_level: str,
        risk_factors: List[str],
        customer: Dict[str, Any]
    ) -> List[str]:
        """Generate retention actions based on churn risk"""
        actions = []
        
        if risk_level == "high":
            actions.append("Send personalized re-engagement email with special offer")
            actions.append("Assign account manager for personal outreach")
            actions.append(f"Offer {customer.get('total_spent', 0) * 0.1:.2f} loyalty credit")
        elif risk_level == "medium":
            actions.append("Include in next retention campaign")
            actions.append("Send product/service recommendations")
            actions.append("Invite to exclusive promotion")
        
        return actions
    
    def _generate_churn_prevention_strategies(
        self,
        business_category: str,
        at_risk_customers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate churn prevention strategies"""
        strategies = []
        
        if len(at_risk_customers) > 0:
            # Calculate potential revenue at risk
            revenue_at_risk = sum(c.get("lifetime_value", 0) for c in at_risk_customers)
            
            strategies.append({
                "strategy": "Launch Win-Back Campaign",
                "target_customers": len(at_risk_customers),
                "potential_revenue_saved": round(revenue_at_risk * 0.3, 2),
                "estimated_cost": round(revenue_at_risk * 0.05, 2),
                "roi_estimate": "6:1"
            })
            
            strategies.append({
                "strategy": "Implement Loyalty Program",
                "target_customers": "All customers",
                "expected_retention_increase": "15-25%",
                "implementation_time": "2-4 weeks"
            })
        
        return strategies
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
        
        # Linear regression
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        slope = coefficients[0]
        
        avg_value = np.mean(values)
        slope_percentage = (slope / avg_value * 100) if avg_value > 0 else 0
        
        if slope_percentage > 5:
            return "strongly_increasing"
        elif slope_percentage > 1:
            return "increasing"
        elif slope_percentage < -5:
            return "strongly_decreasing"
        elif slope_percentage < -1:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_trend_strength(self, values: List[float]) -> str:
        """Calculate trend strength using R-squared"""
        r_squared = self._calculate_r_squared(values)
        
        if r_squared > 0.8:
            return "very_strong"
        elif r_squared > 0.6:
            return "strong"
        elif r_squared > 0.4:
            return "moderate"
        else:
            return "weak"
    
    def _calculate_growth_rate(self, values: List[float]) -> Dict[str, float]:
        """Calculate various growth rates"""
        if len(values) < 2:
            return {"period_over_period": 0.0, "compound_annual": 0.0}
        
        # Period-over-period growth
        pop_growth = ((values[-1] - values[0]) / values[0] * 100) if values[0] > 0 else 0
        
        # Average period growth
        period_growths = [
            ((values[i] - values[i-1]) / values[i-1] * 100) if values[i-1] > 0 else 0
            for i in range(1, len(values))
        ]
        avg_period_growth = np.mean(period_growths) if period_growths else 0
        
        return {
            "period_over_period": round(pop_growth, 2),
            "average_period_growth": round(avg_period_growth, 2)
        }
    
    def _detect_seasonality(self, values: List[float]) -> Dict[str, Any]:
        """Detect seasonality patterns"""
        if len(values) < 14:
            return {"detected": False}
        
        # Simple seasonality detection using weekly patterns
        weekly_pattern = []
        for i in range(min(7, len(values))):
            day_values = [values[j] for j in range(i, len(values), 7)]
            if len(day_values) >= 2:
                weekly_pattern.append(np.mean(day_values))
        
        if len(weekly_pattern) >= 7:
            pattern_std = np.std(weekly_pattern)
            pattern_mean = np.mean(weekly_pattern)
            coefficient_of_variation = (pattern_std / pattern_mean) if pattern_mean > 0 else 0
            
            if coefficient_of_variation > 0.15:
                return {
                    "detected": True,
                    "pattern_type": "weekly",
                    "strength": "moderate" if coefficient_of_variation > 0.25 else "weak"
                }
        
        return {"detected": False}
    
    def _forecast_next_period(
        self,
        values: List[float],
        dates: List[str]
    ) -> Dict[str, Any]:
        """Forecast next period (7 days)"""
        if len(values) < 7:
            return {}
        
        recent_avg = np.mean(values[-7:])
        previous_avg = np.mean(values[-14:-7]) if len(values) >= 14 else recent_avg
        
        growth = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        next_period_forecast = recent_avg * (1 + growth / 100)
        
        return {
            "predicted_value": round(next_period_forecast, 2),
            "lower_bound": round(next_period_forecast * 0.9, 2),
            "upper_bound": round(next_period_forecast * 1.1, 2),
            "confidence": 0.75
        }
    
    def _generate_trend_insights(
        self,
        metric_type: str,
        direction: str,
        strength: str,
        growth_rate: Dict[str, float],
        seasonality: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from trend analysis"""
        insights = []
        
        # Direction insights
        if "increasing" in direction:
            insights.append(f"{metric_type.replace('_', ' ').title()} is trending upward")
            if growth_rate["period_over_period"] > 10:
                insights.append("Strong growth momentum detected")
        elif "decreasing" in direction:
            insights.append(f"{metric_type.replace('_', ' ').title()} is trending downward")
            insights.append("Consider investigating causes of decline")
        else:
            insights.append(f"{metric_type.replace('_', ' ').title()} is relatively stable")
        
        # Strength insights
        if strength in ["very_strong", "strong"]:
            insights.append("Trend is consistent and predictable")
        elif strength == "weak":
            insights.append("High variability - trend is less predictable")
        
        # Seasonality insights
        if seasonality.get("detected"):
            insights.append(f"{seasonality['pattern_type'].title()} seasonality pattern detected")
        
        return insights


# Singleton instance
_predictive_intelligence: Optional[PredictiveIntelligence] = None


def get_predictive_intelligence() -> PredictiveIntelligence:
    """Get predictive intelligence singleton"""
    global _predictive_intelligence
    if _predictive_intelligence is None:
        _predictive_intelligence = PredictiveIntelligence()
    return _predictive_intelligence
