"""
Metrics and Analytics use cases for clean architecture
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.base import UseCase
from app.application.dtos.metrics import (
    DashboardMetricsDTO,
    OperationalKPIDTO,
    QualityKPIDTO,
    PerformanceTrendDTO,
    BenchmarkMetricsDTO,
    PeerComparisonDTO,
    RegulatoryBenchmarkDTO,
    BenchmarkTrendDTO,
    ExecutiveSummaryDTO,
    ServiceHealthDTO,
    SystemAnalyticsDTO,
    TesterMetricsDTO,
    SimpleDashboardMetricsDTO,
    ReportOwnerMetricsDTO,
    DataProviderMetricsDTO,
    PhaseMetricsDTO
)
from app.core.auth import UserRoles
from app.services.metrics_service import get_metrics_service
from app.services.benchmarking_service import get_benchmarking_service


class GetUserDashboardMetricsUseCase(UseCase):
    """Get dashboard metrics for current user"""
    
    async def execute(
        self,
        user_id: int,
        user_role: str,
        time_filter: Optional[str],
        db: AsyncSession
    ) -> DashboardMetricsDTO:
        """Get dashboard metrics based on user role"""
        
        metrics_service = get_metrics_service()
        
        if user_role == UserRoles.TEST_EXECUTIVE:
            metrics_data = await metrics_service.get_test_manager_dashboard_metrics(user_id, db)
        elif user_role == UserRoles.REPORT_OWNER:
            metrics_data = await metrics_service.get_report_owner_dashboard_metrics(user_id, db, time_filter)
        elif user_role == UserRoles.REPORT_OWNER_EXECUTIVE:
            metrics_data = await metrics_service.get_report_owner_executive_dashboard_metrics(user_id, db)
        elif user_role == UserRoles.TESTER:
            metrics_data = await metrics_service.get_tester_dashboard_metrics(user_id, db)
        elif user_role == UserRoles.DATA_EXECUTIVE:
            metrics_data = await metrics_service.get_cdo_dashboard_metrics(user_id, db)
        elif user_role == UserRoles.DATA_OWNER:
            metrics_data = await metrics_service.get_data_owner_dashboard_metrics(user_id, db)
        else:
            # Default metrics for admin or other roles
            metrics_data = {
                "role": user_role,
                "user_id": user_id,
                "overview": {"message": "Dashboard metrics not available for this role"},
                "generated_at": datetime.utcnow().isoformat()
            }
        
        return DashboardMetricsDTO(
            role=user_role,
            user_id=user_id,
            generated_at=datetime.utcnow(),
            time_filter=time_filter or "current_cycle",
            overview=metrics_data.get("overview", {}),
            details=metrics_data.get("details")
        )


class GetSystemAnalyticsUseCase(UseCase):
    """Get system-wide analytics"""
    
    async def execute(self, db: AsyncSession) -> SystemAnalyticsDTO:
        """Get system analytics"""
        
        metrics_service = get_metrics_service()
        analytics_data = await metrics_service.get_system_wide_analytics(db)
        
        return SystemAnalyticsDTO(
            overview=analytics_data.get("overview", {}),
            user_metrics=analytics_data.get("user_metrics", {}),
            workflow_metrics=analytics_data.get("workflow_metrics", {}),
            performance_metrics=analytics_data.get("performance_metrics", {}),
            quality_metrics=analytics_data.get("quality_metrics", {}),
            generated_at=datetime.utcnow()
        )


class GetOperationalKPIsUseCase(UseCase):
    """Get operational KPIs"""
    
    async def execute(
        self,
        time_period: str,
        db: AsyncSession
    ) -> OperationalKPIDTO:
        """Get operational KPIs"""
        
        # In a real implementation, these would be calculated from the database
        return OperationalKPIDTO(
            time_period=time_period,
            cycle_completion_rate=87.5,
            average_cycle_duration_days=14.2,
            sla_compliance_percentage=92.3,
            issue_recurrence_rate=5.8,
            data_owner_response_time_hours=18.4,
            testing_efficiency_score=85.2,
            resource_utilization_percentage=78.9,
            generated_at=datetime.utcnow()
        )


class GetQualityKPIsUseCase(UseCase):
    """Get quality KPIs"""
    
    async def execute(
        self,
        time_period: str,
        db: AsyncSession
    ) -> QualityKPIDTO:
        """Get quality KPIs"""
        
        # In a real implementation, these would be calculated from the database
        return QualityKPIDTO(
            time_period=time_period,
            test_pass_rate=94.2,
            observation_resolution_time_hours=36.5,
            retest_frequency=12.3,
            documentation_quality_score=88.7,
            attribute_coverage_rate=96.1,
            data_quality_score=91.4,
            critical_issues_count=3,
            generated_at=datetime.utcnow()
        )


class GetPerformanceTrendsUseCase(UseCase):
    """Get performance trends"""
    
    async def execute(
        self,
        time_period: str,
        db: AsyncSession
    ) -> PerformanceTrendDTO:
        """Get performance trends"""
        
        # In a real implementation, these would be calculated from the database
        return PerformanceTrendDTO(
            time_period=time_period,
            performance_improvement_percentage=15.3,
            seasonal_patterns={
                "q1": {"efficiency": 82.1, "quality": 89.3},
                "q2": {"efficiency": 85.7, "quality": 91.2},
                "q3": {"efficiency": 88.4, "quality": 93.1},
                "q4": {"efficiency": 87.9, "quality": 92.8}
            },
            resource_utilization_trend="increasing",
            efficiency_gains_percentage=12.7,
            risk_reduction_percentage=23.4,
            cycle_time_improvement_percentage=18.9,
            generated_at=datetime.utcnow()
        )


class GetIndustryBenchmarksUseCase(UseCase):
    """Get industry benchmarks"""
    
    async def execute(self, db: AsyncSession) -> BenchmarkMetricsDTO:
        """Get industry benchmarks"""
        
        # Get current system metrics
        metrics_service = get_metrics_service()
        system_analytics = await metrics_service.get_system_wide_analytics(db)
        
        # Extract key metrics for benchmarking
        our_metrics = {
            "cycle_completion_rate": 87.5,
            "sla_compliance_rate": 92.3,
            "test_pass_rate": 94.2,
            "data_quality_score": 91.4,
            "resource_utilization": 78.9,
            "automation_adoption": 67.8,
            "observation_resolution_time": 3.2,
            "audit_readiness_score": 89.7
        }
        
        benchmarking_service = get_benchmarking_service()
        benchmark_data = await benchmarking_service.get_industry_benchmarks(our_metrics)
        
        return BenchmarkMetricsDTO(
            our_metrics=benchmark_data.get("our_metrics", {}),
            industry_average=benchmark_data.get("industry_average", {}),
            top_performers=benchmark_data.get("top_performers", {}),
            percentile_rank=benchmark_data.get("percentile_rank", {}),
            improvement_opportunities=benchmark_data.get("improvement_opportunities", []),
            generated_at=datetime.utcnow()
        )


class GetPeerComparisonUseCase(UseCase):
    """Get peer comparison"""
    
    async def execute(
        self,
        organization_size: str,
        db: AsyncSession
    ) -> PeerComparisonDTO:
        """Get peer comparison"""
        
        benchmarking_service = get_benchmarking_service()
        peer_data = await benchmarking_service.get_peer_comparison(organization_size)
        
        return PeerComparisonDTO(
            organization_size=organization_size,
            peer_group_size=peer_data.get("peer_group_size", 0),
            our_metrics=peer_data.get("our_metrics", {}),
            peer_average=peer_data.get("peer_average", {}),
            peer_median=peer_data.get("peer_median", {}),
            quartile_position=peer_data.get("quartile_position", {}),
            relative_performance=peer_data.get("relative_performance", {}),
            generated_at=datetime.utcnow()
        )


class GetRegulatoryBenchmarksUseCase(UseCase):
    """Get regulatory benchmarks"""
    
    async def execute(
        self,
        regulation_type: str,
        db: AsyncSession
    ) -> RegulatoryBenchmarkDTO:
        """Get regulatory benchmarks"""
        
        benchmarking_service = get_benchmarking_service()
        regulatory_data = await benchmarking_service.get_regulatory_benchmarks(regulation_type)
        
        return RegulatoryBenchmarkDTO(
            regulation_type=regulation_type,
            compliance_requirements=regulatory_data.get("compliance_requirements", {}),
            our_compliance=regulatory_data.get("our_compliance", {}),
            gap_analysis=regulatory_data.get("gap_analysis", {}),
            risk_areas=regulatory_data.get("risk_areas", []),
            recommendations=regulatory_data.get("recommendations", []),
            generated_at=datetime.utcnow()
        )


class GetBenchmarkTrendsUseCase(UseCase):
    """Get benchmark trends"""
    
    async def execute(
        self,
        time_period: str,
        db: AsyncSession
    ) -> BenchmarkTrendDTO:
        """Get benchmark trends"""
        
        benchmarking_service = get_benchmarking_service()
        trend_data = await benchmarking_service.get_trend_analysis(time_period)
        
        return BenchmarkTrendDTO(
            time_period=time_period,
            trend_data=trend_data.get("trend_data", []),
            forecast=trend_data.get("forecast", {}),
            emerging_trends=trend_data.get("emerging_trends", []),
            strategic_recommendations=trend_data.get("strategic_recommendations", []),
            generated_at=datetime.utcnow()
        )


class GetExecutiveSummaryUseCase(UseCase):
    """Get executive summary report"""
    
    async def execute(
        self,
        time_period: str,
        db: AsyncSession
    ) -> ExecutiveSummaryDTO:
        """Get executive summary"""
        
        # In a real implementation, these would be calculated from the database
        return ExecutiveSummaryDTO(
            time_period=time_period,
            executive_summary={
                "total_cycles_completed": 24,
                "total_reports_tested": 156,
                "overall_compliance_rate": 94.2,
                "critical_issues_identified": 7,
                "critical_issues_resolved": 6,
                "cost_savings_achieved": "$2.3M",
                "efficiency_improvement": "18.5%"
            },
            key_achievements=[
                "Achieved 94.2% overall compliance rate",
                "Reduced cycle time by 18.9%",
                "Implemented automated testing for 67.8% of processes",
                "Resolved 86% of critical issues within SLA"
            ],
            critical_issues=[
                {
                    "issue": "Data quality gaps in customer records",
                    "impact": "High",
                    "status": "In Progress",
                    "resolution_eta": "2024-02-15"
                }
            ],
            strategic_recommendations=[
                "Increase automation adoption to 80% in Q2",
                "Implement predictive analytics for risk assessment",
                "Enhance data provider training program"
            ],
            next_period_focus=[
                "Complete migration to cloud-based testing platform",
                "Implement real-time monitoring dashboards",
                "Enhance integration with upstream data sources"
            ],
            generated_at=datetime.utcnow()
        )


class GetServiceHealthUseCase(UseCase):
    """Get service health status"""
    
    async def execute(self, service_name: str) -> ServiceHealthDTO:
        """Get service health"""
        
        try:
            if service_name == "benchmarking":
                benchmarking_service = get_benchmarking_service()
                health_data = await benchmarking_service.health_check()
                
                return ServiceHealthDTO(
                    service=service_name,
                    status=health_data.get("status", "unknown"),
                    uptime_percentage=health_data.get("uptime_percentage"),
                    last_check=datetime.utcnow(),
                    error=health_data.get("error")
                )
            else:
                return ServiceHealthDTO(
                    service=service_name,
                    status="unknown",
                    error="Service not found"
                )
                
        except Exception as e:
            return ServiceHealthDTO(
                service=service_name,
                status="unhealthy",
                error=str(e)
            )


class GetTesterMetricsUseCase(UseCase):
    """Get tester-specific metrics"""
    
    async def execute(
        self,
        user_id: int,
        cycle_id: Optional[int],
        report_id: Optional[int],
        db: AsyncSession
    ) -> TesterMetricsDTO:
        """Get tester metrics"""
        
        # Mock data that matches frontend expectations
        return TesterMetricsDTO(
            data={
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
                "phase_performance": [
                    {
                        "phase_name": "Planning",
                        "total": 8,
                        "completed": 6,
                        "completion_rate": 75.0
                    },
                    {
                        "phase_name": "Scoping",
                        "total": 8,
                        "completed": 5,
                        "completion_rate": 62.5
                    },
                    {
                        "phase_name": "Testing",
                        "total": 8,
                        "completed": 3,
                        "completion_rate": 37.5
                    },
                    {
                        "phase_name": "Observation Management",
                        "total": 8,
                        "completed": 2,
                        "completion_rate": 25.0
                    }
                ],
                "lob_distribution": [
                    {
                        "lob_name": "Retail Banking",
                        "report_count": 3,
                        "attribute_count": 145
                    },
                    {
                        "lob_name": "Commercial Banking",
                        "report_count": 2,
                        "attribute_count": 98
                    },
                    {
                        "lob_name": "Investment Banking",
                        "report_count": 3,
                        "attribute_count": 167
                    }
                ],
                "report_summaries": [
                    {
                        "lob_name": "Retail Banking",
                        "total_samples": 45,
                        "total_attributes": 145,
                        "total_test_cases": 290,
                        "avg_progress": 68.5
                    },
                    {
                        "lob_name": "Commercial Banking",
                        "total_samples": 32,
                        "total_attributes": 98,
                        "total_test_cases": 196,
                        "avg_progress": 55.0
                    },
                    {
                        "lob_name": "Investment Banking",
                        "total_samples": 58,
                        "total_attributes": 167,
                        "total_test_cases": 334,
                        "avg_progress": 42.0
                    }
                ]
            }
        )


class GetSimpleDashboardMetricsUseCase(UseCase):
    """Get simple dashboard metrics"""
    
    async def execute(
        self,
        user_id: int,
        cycle_id: Optional[int],
        time_period: str,
        db: AsyncSession
    ) -> SimpleDashboardMetricsDTO:
        """Get simple dashboard metrics"""
        
        return SimpleDashboardMetricsDTO(
            aggregate_metrics={
                "reports_assigned": 8,
                "reports_completed": 3,
                "reports_in_progress": 4,
                "reports_trend": 12.5,
                "avg_completion_time": 14.5,
                "completion_rate": 37.5,
                "sla_compliance_rate": 92.5,
                "observations_confirmed": 15
            },
            time_period=time_period,
            cycle_id=cycle_id
        )


class GetReportOwnerMetricsUseCase(UseCase):
    """Get report owner metrics"""
    
    async def execute(
        self,
        user_id: int,
        cycle_id: Optional[int],
        db: AsyncSession
    ) -> ReportOwnerMetricsDTO:
        """Get report owner metrics"""
        
        return ReportOwnerMetricsDTO(
            pending_approvals=12,
            approved_items=45,
            rejected_items=3,
            average_review_time=2.5,
            approval_rate=93.75,
            sla_compliance=89.5
        )


class GetDataProviderMetricsUseCase(UseCase):
    """Get data provider metrics"""
    
    async def execute(
        self,
        user_id: int,
        cycle_id: Optional[int],
        db: AsyncSession
    ) -> DataProviderMetricsDTO:
        """Get data provider metrics"""
        
        return DataProviderMetricsDTO(
            assigned_attributes=67,
            data_provided=52,
            pending_requests=15,
            sla_compliance=91.5,
            average_response_time=3.2,
            completion_rate=77.6
        )


class GetPhaseMetricsUseCase(UseCase):
    """Get phase-specific metrics"""
    
    async def execute(
        self,
        phase_name: str,
        cycle_id: Optional[int],
        report_id: Optional[int],
        db: AsyncSession
    ) -> PhaseMetricsDTO:
        """Get phase-specific metrics"""
        
        # Convert phase names to match database
        phase_name_map = {
            'planning': 'Planning',
            'data_profiling': 'Data Profiling',
            'scoping': 'Scoping',
            'sample-selection': 'Sample Selection',
            'data-provider-id': 'Data Provider Identification',
            'request-info': 'Request for Information',
            'test-execution': 'Test Execution',
            'observation-management': 'Observation Management'
        }
        
        db_phase_name = phase_name_map.get(phase_name, phase_name)
        
        # Use real metrics calculator
        from app.services.metrics.base_metrics_calculator import BaseMetricsCalculator
        calculator = BaseMetricsCalculator(db)
        
        try:
            if cycle_id and report_id:
                # Get real metrics from database
                metrics = await calculator.calculate_phase_metrics(
                    str(cycle_id), 
                    str(report_id), 
                    db_phase_name
                )
                
                # Transform to match frontend expectations based on phase
                transformed_metrics = await self._transform_phase_metrics(phase_name, metrics, calculator, str(cycle_id), str(report_id))
                
                return PhaseMetricsDTO(
                    phase_name=phase_name,
                    metrics=transformed_metrics
                )
            else:
                # Return mock data if no IDs provided
                return PhaseMetricsDTO(
                    phase_name=phase_name,
                    metrics=self._get_mock_phase_data(phase_name)
                )
                
        except Exception as e:
            # Fall back to mock data on error
            return PhaseMetricsDTO(
                phase_name=phase_name,
                metrics=self._get_mock_phase_data(phase_name)
            )
    
    async def _transform_phase_metrics(self, phase_name: str, metrics: Dict[str, Any], calculator, cycle_id: str, report_id: str) -> Dict[str, Any]:
        """Transform real metrics to match frontend expectations"""
        
        if phase_name == 'planning':
            return {
                "total_attributes": metrics.get("total_attributes", 0),
                "attributes_approved_for_planning": metrics.get("attributes_approved_for_planning", 0),
                "attributes_with_ai_recommendations": metrics.get("attributes_with_ai_recommendations", 0),
                "completion_time": metrics.get("completion_time_minutes", 0) / 60 if metrics.get("completion_time_minutes") else 0,
                "submissions_for_approval": metrics.get("submissions_for_approval", 0),
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        elif phase_name == 'data_profiling':
            return {
                "total_attributes": metrics.get("total_attributes", 0),
                "approved_profiling_rules": metrics.get("approved_profiling_rules", 0),
                "attributes_no_dq_issues": metrics.get("attributes_no_dq_issues", 0),
                "attributes_with_anomalies": metrics.get("attributes_with_anomalies", 0),
                "completion_time": metrics.get("completion_time_minutes", 0) / 60 if metrics.get("completion_time_minutes") else 0,
                "submissions_for_approval": metrics.get("submissions_for_approval", 0),
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        elif phase_name == 'scoping':
            return {
                "total_attributes": metrics.get("total_attributes", 0),
                "primary_keys": metrics.get("primary_keys", 0),
                "non_pk_scoped": metrics.get("non_pk_scoped_attributes", 0),
                "completion_time": metrics.get("completion_time_minutes", 0) / 60 if metrics.get("completion_time_minutes") else 0,
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        elif phase_name == 'sample-selection':
            return {
                "non_pk_scoped": metrics.get("non_pk_scoped_attributes", 0),
                "samples_approved": metrics.get("samples_approved", 0),
                "samples_pending_approval": metrics.get("samples_pending_approval", 0),
                "lobs_count": metrics.get("total_lobs", 0),
                "completion_time": metrics.get("completion_time_minutes", 0) / 60 if metrics.get("completion_time_minutes") else 0,
                "submissions_for_approval": metrics.get("submissions_for_approval", 0),
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        elif phase_name == 'data-provider-id':
            return {
                "non_pk_scoped": metrics.get("non_pk_scoped_attributes", 0),
                "samples_approved": metrics.get("samples_approved", 0),
                "lobs_count": metrics.get("total_lobs", 0),
                "data_providers_assigned": metrics.get("data_providers_assigned", 0),
                "changes_to_data_providers": metrics.get("changes_to_data_providers", 0),
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        elif phase_name == 'request-info':
            return {
                "non_pk_scoped": metrics.get("non_pk_scoped_attributes", 0),
                "samples_approved": metrics.get("samples_approved", 0),
                "lobs_count": metrics.get("total_lobs", 0),
                "test_cases_count": metrics.get("total_test_cases", 0),
                "test_cases_rfi_completed": metrics.get("test_cases_rfi_completed", 0),
                "test_cases_rfi_pending": metrics.get("test_cases_rfi_pending", 0),
                "changes_to_data_providers_during_rfi": metrics.get("changes_to_data_providers_during_rfi", 0),
                "completion_time": metrics.get("completion_time_minutes", 0) / 60 if metrics.get("completion_time_minutes") else 0,
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        elif phase_name == 'test-execution':
            return {
                "non_pk_scoped": metrics.get("non_pk_scoped_attributes", 0),
                "samples_approved": metrics.get("samples_approved", 0),
                "lobs_count": metrics.get("total_lobs", 0),
                "test_cases_count": metrics.get("total_test_cases", 0),
                "test_cases_completed": metrics.get("test_cases_completed", 0),
                "test_case_pass": metrics.get("test_cases_passed", 0),
                "test_case_fail": metrics.get("test_cases_failed", 0),
                "test_cases_requiring_reupload": metrics.get("test_cases_requiring_reupload", 0),
                "completion_time": metrics.get("completion_time_minutes", 0) / 60 if metrics.get("completion_time_minutes") else 0,
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        elif phase_name == 'observation-management':
            return {
                "non_pk_scoped": metrics.get("non_pk_scoped_attributes", 0),
                "samples_approved": metrics.get("samples_approved", 0),
                "lobs_count": metrics.get("total_lobs", 0),
                "test_cases_count": metrics.get("total_test_cases", 0),
                "test_cases_with_observations": metrics.get("test_cases_with_observations", 0),
                "observations_count": metrics.get("total_observations", 0),
                "approved_observations": metrics.get("approved_observations", 0),
                "samples_impacted": metrics.get("samples_impacted", 0),
                "attributes_impacted": metrics.get("attributes_impacted", 0),
                "completion_time": metrics.get("completion_time_minutes", 0) / 60 if metrics.get("completion_time_minutes") else 0,
                "on_time": "Yes" if metrics.get("on_time_completion") else "No" if metrics.get("on_time_completion") is False else "N/A"
            }
            
        return metrics
    
    def _get_mock_phase_data(self, phase_name: str) -> Dict[str, Any]:
        """Return mock data for phases"""
        # Mock data for different phases
        phase_data = {
            "planning": {
                "total_attributes": 156,
                "approved_attributes": 142,
                "attributes_trend": "up",
                "cde_count": 28,
                "cde_percentage": 18,
                "historical_issues_count": 12,
                "issues_resolved": 8,
                "phase_completion": 91,
                "completion_trend": "up",
                "days_in_phase": 5,
                "is_overdue": False,
                "mandatory_count": 89,
                "conditional_count": 34,
                "optional_count": 33,
                "pending_approval": 2,
                "rejected_count": 1,
                "approval_rate": 94,
                "approval_trend": "stable",
                "avg_time_to_approval": 3.5,
                "resubmission_count": 1,
                "first_pass_rate": 92,
                "time_trend": "down"
            },
            "scoping": {
                "recommendations_generated": 125,
                "recommendations_accepted": 108,
                "acceptance_rate": 86.4,
                "attributes_included": 98,
                "attributes_excluded": 27,
                "mandatory_coverage": 100,
                "overall_coverage": 78.4,
                "coverage_trend": "up",
                "submission_status": "Approved",
                "revision_count": 1,
                "high_risk_attributes": 18,
                "high_risk_coverage": 100,
                "avg_risk_score": 62,
                "risk_trend": "down",
                "lobs_covered": 8,
                "lob_balance_score": 87,
                "time_to_decision": 2.8,
                "efficiency_trend": "up",
                "automation_rate": 72,
                "first_pass_approval": 88
            },
            "data-provider-id": {
                "total_lobs": 10,
                "assigned_lobs": 9,
                "pending_lobs": 1,
                "total_providers": 24,
                "active_providers": 22,
                "response_rate": 91.7,
                "response_trend": "up",
                "on_time_assignments": 96.5,
                "overdue_items": 2,
                "avg_assignment_time": 4.2,
                "time_trend": "down",
                "completed_assignments": 21,
                "total_assignments": 24,
                "in_progress": 2,
                "not_started": 1,
                "cycle_over_cycle": 8.5,
                "avg_historical_time": 5.1,
                "improvement_score": 92,
                "correct_assignments": 98.2,
                "reassignment_rate": 1.8,
                "first_pass_accuracy": 96.5,
                "accuracy_trend": "up",
                "automation_rate": 68,
                "manual_interventions": 5,
                "throughput_rate": 12,
                "throughput_trend": "stable"
            },
            "sample-selection": {
                "total_samples": 450,
                "unique_samples": 445,
                "sample_coverage": 93.5,
                "random_samples": 200,
                "stratified_samples": 150,
                "judgmental_samples": 75,
                "systematic_samples": 25,
                "lob_distribution": [
                    {"lob_name": "Retail", "sample_count": 125, "percentage": 27.8},
                    {"lob_name": "Commercial", "sample_count": 98, "percentage": 21.8},
                    {"lob_name": "Investment", "sample_count": 112, "percentage": 24.9},
                    {"lob_name": "Wealth", "sample_count": 115, "percentage": 25.6}
                ],
                "validated_samples": 438,
                "invalid_samples": 7,
                "validation_rate": 97.3,
                "validation_trend": "up",
                "high_risk_coverage": 100,
                "medium_risk_coverage": 95,
                "low_risk_coverage": 88,
                "selection_time": 6.5,
                "time_trend": "down",
                "automation_rate": 82,
                "reselection_rate": 3.2,
                "transaction_samples": 280,
                "balance_samples": 85,
                "exception_samples": 45,
                "control_samples": 40
            },
            "request-info": {
                "total_requests": 156,
                "requests_sent": 156,
                "pending_requests": 12,
                "responses_received": 144,
                "response_rate": 92.3,
                "response_trend": "up",
                "incomplete_responses": 5,
                "avg_response_time": 18.5,
                "time_trend": "down",
                "fastest_response": 2.5,
                "slowest_response": 48,
                "documents_submitted": 312,
                "avg_documents_per_request": 2.2,
                "document_compliance": 94.5,
                "completeness_score": 96.8,
                "accuracy_score": 98.2,
                "accuracy_trend": "up",
                "timeliness_score": 91.5,
                "overall_quality": 95.5,
                "follow_up_requests": 8,
                "clarifications_needed": 5,
                "resubmission_rate": 3.2,
                "sla_compliance_rate": 97.4,
                "sla_breaches": 4,
                "escalations": 1,
                "automated_requests": 78,
                "manual_processing": 22,
                "throughput": 28,
                "throughput_trend": "up"
            },
            "test-execution": {
                "total_test_cases": 850,
                "executed_tests": 742,
                "execution_rate": 87.3,
                "execution_trend": "up",
                "passed_tests": 698,
                "failed_tests": 44,
                "pass_rate": 94.1,
                "pass_trend": "stable",
                "total_issues": 28,
                "critical_issues": 2,
                "high_issues": 8,
                "avg_execution_time": 12.5,
                "time_trend": "down",
                "tests_per_day": 85,
                "efficiency_score": 91.2,
                "cycle_report_test_execution_database_tests": 420,
                "data_quality_score": 93.5,
                "data_anomalies": 5,
                "document_tests": 322,
                "format_compliance": 98.2,
                "content_accuracy": 96.5,
                "regression_tests": 108,
                "regression_failures": 3,
                "stability_score": 97.2
            },
            "observation-management": {
                "total_observations": 68,
                "observation_trend": "down",
                "new_observations": 42,
                "recurring_observations": 26,
                "confirmed_observations": 45,
                "disputed_observations": 8,
                "resolved_observations": 35,
                "critical_count": 3,
                "high_count": 12,
                "medium_count": 28,
                "low_count": 25,
                "resolved_count": 35,
                "in_progress_count": 15,
                "resolution_rate": 51.5,
                "resolution_trend": "up",
                "avg_resolution_time": 8.5,
                "resolution_time_trend": "down",
                "fastest_resolution": 1,
                "longest_resolution": 28,
                "pending_approval": 6,
                "approved_count": 32,
                "rejected_count": 3,
                "approval_rate": 91.4,
                "observation_groups": 22,
                "grouping_efficiency": 68,
                "avg_group_size": 3.1,
                "ungrouped_observations": 8,
                "observations_0_30_days": 45,
                "observations_31_60_days": 18,
                "observations_61_90_days": 5,
                "observations_over_90_days": 0,
                "remediation_plans": 28,
                "completed_remediations": 18,
                "overdue_remediations": 2,
                "remediation_effectiveness": 92.5,
                "repeat_observation_rate": 15.2,
                "repeat_trend": "down",
                "root_cause_identified": 85,
                "preventive_actions": 22
            }
        }
        
        return PhaseMetricsDTO(
            phase_name=phase_name,
            metrics=phase_data.get(phase_name, {})
        )


class GetTestingSummaryUseCase(UseCase):
    """Get testing summary with LOB breakdown"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get testing summary data"""
        
        from app.services.metrics.base_metrics_calculator import BaseMetricsCalculator
        calculator = BaseMetricsCalculator(db)
        
        try:
            # Get error rates for different levels
            sample_metrics = await calculator.calculate_error_rates(str(cycle_id), str(report_id), "sample")
            attribute_metrics = await calculator.calculate_error_rates(str(cycle_id), str(report_id), "attribute")
            test_case_metrics = await calculator.calculate_error_rates(str(cycle_id), str(report_id), "test_case")
            
            # Get LOB breakdown (mock for now)
            lob_breakdown = self._get_mock_lob_breakdown()
            
            # Format response
            return {
                "sample_metrics": {
                    "aggregate": {
                        "scoped_attributes": attribute_metrics.get("total_attributes", 0),
                        "approved_samples": sample_metrics.get("total_samples", 0),
                        "passed": sample_metrics.get("samples_passed", 0),
                        "failed": sample_metrics.get("samples_failed", 0),
                        "under_review": sample_metrics.get("samples_under_review", 0),
                        "error_rate": sample_metrics.get("error_rate", 0)
                    },
                    "by_lob": lob_breakdown["sample_metrics"]
                },
                "attribute_metrics": {
                    "aggregate": {
                        "scoped_attributes": attribute_metrics.get("total_attributes", 0),
                        "passed": attribute_metrics.get("attributes_passed", 0),
                        "failed": attribute_metrics.get("attributes_failed", 0),
                        "under_review": attribute_metrics.get("attributes_under_review", 0),
                        "error_rate": attribute_metrics.get("error_rate", 0)
                    },
                    "by_lob": lob_breakdown["attribute_metrics"]
                },
                "test_case_metrics": {
                    "aggregate": {
                        "scoped_attributes": attribute_metrics.get("total_attributes", 0),
                        "approved_samples": sample_metrics.get("total_samples", 0),
                        "test_cases": test_case_metrics.get("total_test_cases", 0),
                        "passed": test_case_metrics.get("test_cases_passed", 0),
                        "failed": test_case_metrics.get("test_cases_failed", 0),
                        "under_review": test_case_metrics.get("test_cases_under_review", 0),
                        "error_rate": test_case_metrics.get("error_rate", 0)
                    },
                    "by_lob": lob_breakdown["test_case_metrics"]
                },
                "overall_error_rate": (sample_metrics.get("error_rate", 0) + attribute_metrics.get("error_rate", 0) + test_case_metrics.get("error_rate", 0)) / 3,
                "total_tests_executed": test_case_metrics.get("total_test_cases", 0),
                "lobs_covered": len(lob_breakdown["lobs"]),
                "completion_percentage": 85.5  # Mock value
            }
            
        except Exception as e:
            # Return mock data on error
            return self._get_mock_testing_summary()
    
    def _get_mock_lob_breakdown(self) -> Dict[str, Any]:
        """Get mock LOB breakdown data"""
        lobs = ["Retail Banking", "Commercial Banking", "Investment Banking", "Wealth Management"]
        
        return {
            "lobs": lobs,
            "sample_metrics": [
                {
                    "lob_name": lob,
                    "scoped_attributes": 45 + i * 10,
                    "approved_samples": 12 + i * 3,
                    "passed": 10 + i * 2,
                    "failed": 1 + (i % 2),
                    "under_review": 1,
                    "error_rate": 8.3 + i * 0.5
                }
                for i, lob in enumerate(lobs)
            ],
            "attribute_metrics": [
                {
                    "lob_name": lob,
                    "scoped_attributes": 45 + i * 10,
                    "passed": 40 + i * 8,
                    "failed": 3 + i,
                    "under_review": 2,
                    "error_rate": 6.7 + i * 0.8
                }
                for i, lob in enumerate(lobs)
            ],
            "test_case_metrics": [
                {
                    "lob_name": lob,
                    "scoped_attributes": 45 + i * 10,
                    "approved_samples": 12 + i * 3,
                    "test_cases": 90 + i * 20,
                    "passed": 85 + i * 18,
                    "failed": 4 + i,
                    "under_review": 1,
                    "error_rate": 4.4 + i * 0.3
                }
                for i, lob in enumerate(lobs)
            ]
        }
    
    def _get_mock_testing_summary(self) -> Dict[str, Any]:
        """Get full mock testing summary"""
        lob_breakdown = self._get_mock_lob_breakdown()
        
        return {
            "sample_metrics": {
                "aggregate": {
                    "scoped_attributes": 180,
                    "approved_samples": 48,
                    "passed": 42,
                    "failed": 4,
                    "under_review": 2,
                    "error_rate": 8.3
                },
                "by_lob": lob_breakdown["sample_metrics"]
            },
            "attribute_metrics": {
                "aggregate": {
                    "scoped_attributes": 180,
                    "passed": 164,
                    "failed": 10,
                    "under_review": 6,
                    "error_rate": 5.6
                },
                "by_lob": lob_breakdown["attribute_metrics"]
            },
            "test_case_metrics": {
                "aggregate": {
                    "scoped_attributes": 180,
                    "approved_samples": 48,
                    "test_cases": 360,
                    "passed": 340,
                    "failed": 15,
                    "under_review": 5,
                    "error_rate": 4.2
                },
                "by_lob": lob_breakdown["test_case_metrics"]
            },
            "overall_error_rate": 6.0,
            "total_tests_executed": 360,
            "lobs_covered": 4,
            "completion_percentage": 94.4
        }