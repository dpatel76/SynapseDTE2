"""
Data Provider Dashboard Service
Provides performance metrics and historical assignment tracking for data providers
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, text

logger = logging.getLogger(__name__)


@dataclass
class AssignmentMetrics:
    """Data provider assignment metrics"""
    total_assignments: int
    completed_assignments: int
    pending_assignments: int
    overdue_assignments: int
    average_completion_time_hours: float
    completion_rate: float


@dataclass
class PerformanceMetric:
    """Individual performance metric for data providers"""
    metric_name: str
    current_value: float
    target_value: float
    performance_category: str
    trend: str
    unit: str


class DataProviderDashboardService:
    """Service for Data Provider dashboard analytics"""
    
    def __init__(self):
        logger.info("Data Provider dashboard service initialized")
    
    async def get_data_provider_dashboard_metrics(
        self,
        data_provider_user_id: int,
        db: AsyncSession,
        time_filter: str = "last_30_days"
    ) -> Dict[str, Any]:
        """Get comprehensive data provider dashboard metrics"""
        try:
            # Calculate time range
            if time_filter == "last_7_days":
                start_date = datetime.utcnow() - timedelta(days=7)
            elif time_filter == "last_90_days":
                start_date = datetime.utcnow() - timedelta(days=90)
            else:  # last_30_days default
                start_date = datetime.utcnow() - timedelta(days=30)
            
            # Get assignment metrics
            assignment_metrics = await self._get_assignment_metrics(data_provider_user_id, start_date, db)
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics(data_provider_user_id, start_date, db)
            
            # Get historical assignments
            historical_assignments = await self._get_historical_assignments(data_provider_user_id, db)
            
            # Get workload analysis
            workload_analysis = await self._get_workload_analysis(data_provider_user_id, db)
            
            # Get quality metrics
            quality_metrics = await self._get_quality_metrics(data_provider_user_id, start_date, db)
            
            return {
                "dashboard_type": "data_provider",
                "user_id": data_provider_user_id,
                "time_period": time_filter,
                "generated_at": datetime.utcnow().isoformat(),
                "assignment_overview": {
                    "total_assignments": assignment_metrics.total_assignments,
                    "completed_assignments": assignment_metrics.completed_assignments,
                    "pending_assignments": assignment_metrics.pending_assignments,
                    "overdue_assignments": assignment_metrics.overdue_assignments,
                    "completion_rate": assignment_metrics.completion_rate,
                    "average_completion_time_hours": assignment_metrics.average_completion_time_hours
                },
                "performance_metrics": [
                    {
                        "name": metric.metric_name,
                        "current_value": metric.current_value,
                        "target_value": metric.target_value,
                        "performance_category": metric.performance_category,
                        "trend": metric.trend,
                        "unit": metric.unit,
                        "achievement_percentage": round((metric.current_value / metric.target_value) * 100, 1) if metric.target_value > 0 else 0
                    }
                    for metric in performance_metrics
                ],
                "historical_assignments": historical_assignments,
                "workload_analysis": workload_analysis,
                "quality_metrics": quality_metrics,
                "recommendations": await self._get_recommendations(data_provider_user_id, assignment_metrics, performance_metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get data provider dashboard metrics: {str(e)}")
            return {
                "error": f"Failed to generate dashboard: {str(e)}",
                "dashboard_type": "data_provider",
                "user_id": data_provider_user_id
            }
    
    async def _get_assignment_metrics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> AssignmentMetrics:
        """Get assignment metrics for data provider"""
        try:
            # Mock assignment metrics - in production, these would query actual tables
            # Based on typical data provider workload patterns
            
            total_assignments = 23
            completed_assignments = 18
            pending_assignments = 3
            overdue_assignments = 2
            average_completion_time = 14.5  # hours
            completion_rate = (completed_assignments / total_assignments) * 100 if total_assignments > 0 else 0
            
            return AssignmentMetrics(
                total_assignments=total_assignments,
                completed_assignments=completed_assignments,
                pending_assignments=pending_assignments,
                overdue_assignments=overdue_assignments,
                average_completion_time_hours=average_completion_time,
                completion_rate=completion_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to get assignment metrics: {str(e)}")
            return AssignmentMetrics(0, 0, 0, 0, 0.0, 0.0)
    
    async def _get_performance_metrics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> List[PerformanceMetric]:
        """Get performance metrics for data provider"""
        try:
            # Mock performance metrics - in production, calculated from actual data
            performance_metrics = [
                PerformanceMetric(
                    metric_name="Response Time",
                    current_value=14.5,
                    target_value=24.0,
                    performance_category="excellent",
                    trend="improving",
                    unit="hours"
                ),
                PerformanceMetric(
                    metric_name="Assignment Completion Rate",
                    current_value=78.3,
                    target_value=85.0,
                    performance_category="good",
                    trend="stable", 
                    unit="%"
                ),
                PerformanceMetric(
                    metric_name="Data Quality Score",
                    current_value=91.7,
                    target_value=90.0,
                    performance_category="excellent",
                    trend="improving",
                    unit="score"
                ),
                PerformanceMetric(
                    metric_name="Documentation Completeness",
                    current_value=87.2,
                    target_value=95.0,
                    performance_category="needs_attention",
                    trend="stable",
                    unit="%"
                ),
                PerformanceMetric(
                    metric_name="Collaboration Rating",
                    current_value=4.3,
                    target_value=4.0,
                    performance_category="excellent", 
                    trend="improving",
                    unit="rating"
                )
            ]
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return []
    
    async def _get_historical_assignments(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get historical assignment data and patterns"""
        try:
            # Mock historical data - in production, query from assignment history tables
            return {
                "assignment_history": [
                    {
                        "month": "October 2024",
                        "assignments": 28,
                        "completed": 25,
                        "avg_completion_time": 16.2,
                        "quality_score": 89.4
                    },
                    {
                        "month": "November 2024", 
                        "assignments": 31,
                        "completed": 27,
                        "avg_completion_time": 15.8,
                        "quality_score": 91.1
                    },
                    {
                        "month": "December 2024",
                        "assignments": 23,
                        "completed": 18,
                        "avg_completion_time": 14.5,
                        "quality_score": 91.7
                    }
                ],
                "assignment_patterns": {
                    "peak_assignment_day": "Tuesday",
                    "preferred_assignment_type": "Database Information",
                    "specialization_areas": ["Financial Data", "Risk Reports", "Regulatory Submissions"],
                    "collaboration_frequency": {
                        "high": ["Banking LOB", "Investment LOB"],
                        "medium": ["Insurance LOB"],
                        "low": ["Corporate LOB"]
                    }
                },
                "knowledge_areas": [
                    {
                        "area": "Financial Reporting",
                        "proficiency": 92,
                        "assignments_completed": 89,
                        "expertise_level": "Expert"
                    },
                    {
                        "area": "Risk Management Data",
                        "proficiency": 87,
                        "assignments_completed": 67,
                        "expertise_level": "Advanced"
                    },
                    {
                        "area": "Regulatory Data",
                        "proficiency": 83,
                        "assignments_completed": 45,
                        "expertise_level": "Advanced"
                    },
                    {
                        "area": "Operational Data",
                        "proficiency": 76,
                        "assignments_completed": 32,
                        "expertise_level": "Intermediate"
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get historical assignments: {str(e)}")
            return {}
    
    async def _get_workload_analysis(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get workload analysis and capacity planning"""
        try:
            # Mock workload analysis - in production, calculate from current assignments
            return {
                "current_capacity": {
                    "utilization_percentage": 73.5,
                    "available_hours_per_week": 12.5,
                    "assigned_hours_per_week": 35.0,
                    "capacity_status": "optimal"
                },
                "workload_distribution": {
                    "by_lob": {
                        "Banking": 35.2,
                        "Investment": 28.7,
                        "Insurance": 21.1,
                        "Corporate": 15.0
                    },
                    "by_assignment_type": {
                        "Source Documents": 45.3,
                        "Database Information": 32.1,
                        "Data Validation": 22.6
                    },
                    "by_complexity": {
                        "High": 18.5,
                        "Medium": 52.3,
                        "Low": 29.2
                    }
                },
                "upcoming_assignments": [
                    {
                        "cycle_name": "Q1 2025 Banking Stress Test",
                        "due_date": "2025-01-15",
                        "estimated_hours": 8.5,
                        "priority": "High",
                        "assignment_type": "Database Information"
                    },
                    {
                        "cycle_name": "Investment Portfolio Review",
                        "due_date": "2025-01-22",
                        "estimated_hours": 6.0,
                        "priority": "Medium",
                        "assignment_type": "Source Documents"
                    },
                    {
                        "cycle_name": "Insurance Regulatory Update",
                        "due_date": "2025-01-28",
                        "estimated_hours": 4.5,
                        "priority": "Medium",
                        "assignment_type": "Data Validation"
                    }
                ],
                "capacity_recommendations": [
                    "Current workload is at optimal level",
                    "Consider cross-training in Corporate LOB data",
                    "Opportunity to take on 1-2 additional assignments"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get workload analysis: {str(e)}")
            return {}
    
    async def _get_quality_metrics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get data quality metrics for data provider"""
        try:
            # Mock quality metrics - in production, calculate from actual submission data
            return {
                "overall_quality_score": 91.7,
                "quality_trends": {
                    "last_6_months": [87.2, 88.9, 89.4, 90.1, 91.1, 91.7],
                    "months": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                },
                "quality_breakdown": {
                    "data_accuracy": 93.2,
                    "completeness": 91.8,
                    "timeliness": 89.4,
                    "documentation_quality": 87.2,
                    "format_compliance": 95.1
                },
                "feedback_summary": {
                    "positive_feedback": 18,
                    "constructive_feedback": 3,
                    "total_reviews": 21,
                    "average_rating": 4.3,
                    "recent_feedback": [
                        "Excellent data quality and documentation",
                        "Very responsive to requests for clarification",
                        "Could improve documentation formatting"
                    ]
                },
                "improvement_areas": [
                    {
                        "area": "Documentation Formatting",
                        "current_score": 87.2,
                        "target_score": 95.0,
                        "improvement_suggestions": [
                            "Use standardized templates",
                            "Include data lineage information",
                            "Add validation checkpoints"
                        ]
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality metrics: {str(e)}")
            return {}
    
    async def _get_recommendations(
        self,
        user_id: int,
        assignment_metrics: AssignmentMetrics,
        performance_metrics: List[PerformanceMetric]
    ) -> List[str]:
        """Generate personalized recommendations for data provider"""
        try:
            recommendations = []
            
            # Analyze performance and generate recommendations
            if assignment_metrics.completion_rate < 80:
                recommendations.append("Focus on improving assignment completion rate through better time management")
            
            if assignment_metrics.overdue_assignments > 0:
                recommendations.append("Address overdue assignments as priority to maintain SLA compliance")
            
            if assignment_metrics.average_completion_time_hours > 20:
                recommendations.append("Consider process optimization to reduce average completion time")
            
            # Check performance metrics for specific recommendations
            for metric in performance_metrics:
                if metric.performance_category == "needs_attention":
                    if metric.metric_name == "Documentation Completeness":
                        recommendations.append("Improve documentation practices using standardized templates")
                    elif metric.metric_name == "Assignment Completion Rate":
                        recommendations.append("Review workload distribution and request support if needed")
            
            # Add positive reinforcement for good performance
            excellent_metrics = [m for m in performance_metrics if m.performance_category == "excellent"]
            if len(excellent_metrics) >= 3:
                recommendations.append("Continue excellent performance - consider mentoring other team members")
            
            # Default recommendations if performance is generally good
            if not recommendations:
                recommendations.extend([
                    "Maintain current high performance standards",
                    "Consider expanding expertise to additional LOBs",
                    "Participate in knowledge sharing sessions"
                ])
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return ["Continue current good work practices"]


# Global service instance
data_provider_dashboard_service = DataProviderDashboardService()


def get_data_provider_dashboard_service() -> DataProviderDashboardService:
    """Get the global data provider dashboard service instance"""
    return data_provider_dashboard_service 