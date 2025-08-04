"""
Dashboard DTOs for clean architecture
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class DashboardTimeFilter(BaseModel):
    """Time filter for dashboard queries"""
    filter_type: str = "last_30_days"  # current_quarter, current_year, last_30_days, last_7_days, last_90_days

    def to_days(self) -> int:
        """Convert filter to number of days"""
        filters = {
            "last_7_days": 7,
            "last_30_days": 30,
            "last_90_days": 90,
            "current_quarter": 90,
            "current_year": 365
        }
        return filters.get(self.filter_type, 30)


class MetricDTO(BaseModel):
    """Individual metric data"""
    label: str
    value: Any
    change: Optional[float] = None
    trend: Optional[str] = None  # up, down, stable


class ChartDataDTO(BaseModel):
    """Chart data for visualizations"""
    labels: List[str]
    datasets: List[Dict[str, Any]]


class DashboardSectionDTO(BaseModel):
    """Dashboard section with metrics"""
    title: str
    metrics: List[MetricDTO]
    charts: Optional[List[ChartDataDTO]] = None


class ExecutiveDashboardDTO(BaseModel):
    """Executive dashboard response"""
    overview: DashboardSectionDTO
    portfolio_metrics: DashboardSectionDTO
    operational_efficiency: DashboardSectionDTO
    risk_management: DashboardSectionDTO
    action_items: List[Dict[str, Any]]
    time_filter: str
    last_updated: datetime


class DataOwnerDashboardDTO(BaseModel):
    """Data Owner dashboard response"""
    assignment_overview: DashboardSectionDTO
    performance_metrics: DashboardSectionDTO
    quality_scores: DashboardSectionDTO
    workload_analysis: DashboardSectionDTO
    pending_actions: List[Dict[str, Any]]
    time_filter: str
    last_updated: datetime


class DataExecutiveDashboardDTO(BaseModel):
    """Data Executive (CDO) dashboard response"""
    lob_overview: DashboardSectionDTO
    team_performance: DashboardSectionDTO
    assignment_analytics: DashboardSectionDTO
    escalation_management: DashboardSectionDTO
    action_required: List[Dict[str, Any]]
    time_filter: str
    last_updated: datetime


class BoardReportSummaryDTO(BaseModel):
    """Board-level report summary"""
    executive_summary: str
    key_highlights: List[str]
    portfolio_status: DashboardSectionDTO
    critical_issues: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime


class DashboardHealthDTO(BaseModel):
    """Dashboard service health status"""
    dashboard_services_status: str
    services: Dict[str, Dict[str, Any]]
    capabilities: Dict[str, Any]


class DashboardSummaryDTO(BaseModel):
    """Summary of available dashboards"""
    user_role: str
    available_dashboards: List[Dict[str, Any]]
    total_available: int
    dashboard_capabilities: Dict[str, bool]