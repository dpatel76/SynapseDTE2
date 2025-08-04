"""
Metrics and Analytics DTOs for clean architecture
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class DashboardMetricsDTO(BaseModel):
    """Base DTO for dashboard metrics"""
    role: str
    user_id: int
    generated_at: datetime
    time_filter: Optional[str] = "current_cycle"
    overview: Dict[str, Any]
    details: Optional[Dict[str, Any]] = None


class KPIMetricsDTO(BaseModel):
    """DTO for KPI metrics"""
    time_period: str
    metrics: Dict[str, float]
    generated_at: datetime


class OperationalKPIDTO(BaseModel):
    """DTO for operational KPIs"""
    time_period: str
    cycle_completion_rate: float
    average_cycle_duration_days: float
    sla_compliance_percentage: float
    issue_recurrence_rate: float
    data_owner_response_time_hours: float
    testing_efficiency_score: float
    resource_utilization_percentage: float
    generated_at: datetime


class QualityKPIDTO(BaseModel):
    """DTO for quality KPIs"""
    time_period: str
    test_pass_rate: float
    observation_resolution_time_hours: float
    retest_frequency: float
    documentation_quality_score: float
    attribute_coverage_rate: float
    data_quality_score: float
    critical_issues_count: int
    generated_at: datetime


class PerformanceTrendDTO(BaseModel):
    """DTO for performance trends"""
    time_period: str
    performance_improvement_percentage: float
    seasonal_patterns: Dict[str, Dict[str, float]]
    resource_utilization_trend: str
    efficiency_gains_percentage: float
    risk_reduction_percentage: float
    cycle_time_improvement_percentage: float
    generated_at: datetime


class BenchmarkMetricsDTO(BaseModel):
    """DTO for benchmark metrics"""
    our_metrics: Dict[str, float]
    industry_average: Dict[str, float]
    top_performers: Dict[str, float]
    percentile_rank: Dict[str, int]
    improvement_opportunities: List[str]
    generated_at: datetime


class PeerComparisonDTO(BaseModel):
    """DTO for peer comparison"""
    organization_size: str
    peer_group_size: int
    our_metrics: Dict[str, float]
    peer_average: Dict[str, float]
    peer_median: Dict[str, float]
    quartile_position: Dict[str, int]
    relative_performance: Dict[str, str]
    generated_at: datetime


class RegulatoryBenchmarkDTO(BaseModel):
    """DTO for regulatory benchmarks"""
    regulation_type: str
    compliance_requirements: Dict[str, float]
    our_compliance: Dict[str, float]
    gap_analysis: Dict[str, float]
    risk_areas: List[str]
    recommendations: List[str]
    generated_at: datetime


class BenchmarkTrendDTO(BaseModel):
    """DTO for benchmark trends"""
    time_period: str
    trend_data: List[Dict[str, Any]]
    forecast: Dict[str, float]
    emerging_trends: List[str]
    strategic_recommendations: List[str]
    generated_at: datetime


class ExecutiveSummaryDTO(BaseModel):
    """DTO for executive summary report"""
    time_period: str
    executive_summary: Dict[str, Any]
    key_achievements: List[str]
    critical_issues: List[Dict[str, Any]]
    strategic_recommendations: List[str]
    next_period_focus: List[str]
    generated_at: datetime


class ServiceHealthDTO(BaseModel):
    """DTO for service health"""
    service: str
    status: str
    uptime_percentage: Optional[float] = None
    last_check: Optional[datetime] = None
    error: Optional[str] = None


class SystemAnalyticsDTO(BaseModel):
    """DTO for system-wide analytics"""
    overview: Dict[str, Any]
    user_metrics: Dict[str, Any]
    workflow_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    generated_at: datetime


class TesterMetricsDTO(BaseModel):
    """DTO for tester-specific metrics"""
    data: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "aggregate_metrics": {
                        "reports_assigned": 8,
                        "reports_completed": 3,
                        "reports_in_progress": 4,
                        "reports_trend": 12.5,
                        "avg_completion_time": 14.5,
                        "completion_rate": 37.5,
                        "sla_compliance_rate": 92.5,
                        "observations_confirmed": 15
                    },
                    "phase_performance": [],
                    "lob_distribution": [],
                    "report_summaries": []
                }
            }
        }


class SimpleDashboardMetricsDTO(BaseModel):
    """DTO for simple dashboard metrics"""
    aggregate_metrics: Dict[str, Any]
    time_period: str
    cycle_id: Optional[int] = None


class ReportOwnerMetricsDTO(BaseModel):
    """DTO for report owner metrics"""
    pending_approvals: int
    approved_items: int
    rejected_items: int
    average_review_time: float
    approval_rate: float
    sla_compliance: float


class DataProviderMetricsDTO(BaseModel):
    """DTO for data provider metrics"""
    assigned_attributes: int
    data_provided: int
    pending_requests: int
    sla_compliance: float
    average_response_time: float
    completion_rate: float


class PhaseMetricsDTO(BaseModel):
    """DTO for phase-specific metrics"""
    phase_name: str
    metrics: Dict[str, Any]