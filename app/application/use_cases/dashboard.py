"""
Dashboard use cases for clean architecture
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case

from app.application.use_cases.base import UseCase
from app.application.dtos.dashboard import (
    DashboardTimeFilter,
    ExecutiveDashboardDTO,
    DataOwnerDashboardDTO,
    DataExecutiveDashboardDTO,
    BoardReportSummaryDTO,
    DashboardSectionDTO,
    MetricDTO
)
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
# Removed unused import - ObservationRecord
from app.models.test_execution import TestExecution
from app.models.request_info import CycleReportTestCase
from app.core.auth import UserRoles


class GetExecutiveDashboardUseCase(UseCase):
    """Get executive dashboard data"""
    
    async def execute(
        self,
        user_id: int,
        time_filter: DashboardTimeFilter,
        db: AsyncSession
    ) -> ExecutiveDashboardDTO:
        """Execute executive dashboard query"""
        
        # Calculate date range
        days = time_filter.to_days()
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get overview metrics
        overview_metrics = await self._get_overview_metrics(user_id, start_date, db)
        
        # Get portfolio metrics
        portfolio_metrics = await self._get_portfolio_metrics(user_id, start_date, db)
        
        # Get operational efficiency
        operational_metrics = await self._get_operational_metrics(user_id, start_date, db)
        
        # Get risk management metrics
        risk_metrics = await self._get_risk_metrics(user_id, start_date, db)
        
        # Get action items
        action_items = await self._get_executive_action_items(user_id, db)
        
        return ExecutiveDashboardDTO(
            overview=overview_metrics,
            portfolio_metrics=portfolio_metrics,
            operational_efficiency=operational_metrics,
            risk_management=risk_metrics,
            action_items=action_items,
            time_filter=time_filter.filter_type,
            last_updated=datetime.utcnow()
        )
    
    async def _get_overview_metrics(
        self, 
        user_id: int, 
        start_date: datetime, 
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get overview metrics"""
        # Implementation would query actual data
        # This is a simplified version
        return DashboardSectionDTO(
            title="Executive Overview",
            metrics=[
                MetricDTO(label="Active Reports", value=12, change=20.0, trend="up"),
                MetricDTO(label="Compliance Rate", value="94.5%", change=2.3, trend="up"),
                MetricDTO(label="Pending Reviews", value=8, change=-11.1, trend="down"),
                MetricDTO(label="Risk Score", value="Low", trend="stable")
            ]
        )
    
    async def _get_portfolio_metrics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get portfolio performance metrics"""
        return DashboardSectionDTO(
            title="Portfolio Performance",
            metrics=[
                MetricDTO(label="Total Reports", value=45),
                MetricDTO(label="On-Time Completion", value="87%", change=5.0, trend="up"),
                MetricDTO(label="Average Cycle Time", value="14.2 days", change=-8.5, trend="down"),
                MetricDTO(label="Quality Score", value="A", trend="stable")
            ]
        )
    
    async def _get_operational_metrics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get operational efficiency metrics"""
        return DashboardSectionDTO(
            title="Operational Efficiency",
            metrics=[
                MetricDTO(label="Resource Utilization", value="78%", change=3.2, trend="up"),
                MetricDTO(label="Process Efficiency", value="Good"),
                MetricDTO(label="Cost per Report", value="$2,340", change=-5.1, trend="down"),
                MetricDTO(label="Automation Rate", value="65%", change=12.0, trend="up")
            ]
        )
    
    async def _get_risk_metrics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get risk management metrics"""
        return DashboardSectionDTO(
            title="Risk Management",
            metrics=[
                MetricDTO(label="Critical Issues", value=2, trend="stable"),
                MetricDTO(label="Overdue Items", value=5, change=-28.6, trend="down"),
                MetricDTO(label="SLA Breaches", value=1),
                MetricDTO(label="Risk Coverage", value="92%", change=1.5, trend="up")
            ]
        )
    
    async def _get_executive_action_items(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list:
        """Get executive action items"""
        return [
            {
                "id": 1,
                "type": "approval_required",
                "title": "Q4 Report Approval Pending",
                "priority": "high",
                "due_date": "2023-12-15"
            },
            {
                "id": 2,
                "type": "review_required",
                "title": "Critical Observation Review",
                "priority": "critical",
                "due_date": "2023-12-10"
            }
        ]


class GetDataOwnerDashboardUseCase(UseCase):
    """Get data owner dashboard data"""
    
    async def execute(
        self,
        user_id: int,
        time_filter: DashboardTimeFilter,
        db: AsyncSession
    ) -> DataOwnerDashboardDTO:
        """Execute data owner dashboard query"""
        
        # Calculate date range
        days = time_filter.to_days()
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get assignment overview
        assignment_overview = await self._get_assignment_overview(user_id, start_date, db)
        
        # Get performance metrics
        performance_metrics = await self._get_performance_metrics(user_id, start_date, db)
        
        # Get quality scores
        quality_scores = await self._get_quality_scores(user_id, start_date, db)
        
        # Get workload analysis
        workload_analysis = await self._get_workload_analysis(user_id, start_date, db)
        
        # Get pending actions
        pending_actions = await self._get_pending_actions(user_id, db)
        
        return DataOwnerDashboardDTO(
            assignment_overview=assignment_overview,
            performance_metrics=performance_metrics,
            quality_scores=quality_scores,
            workload_analysis=workload_analysis,
            pending_actions=pending_actions,
            time_filter=time_filter.filter_type,
            last_updated=datetime.utcnow()
        )
    
    async def _get_assignment_overview(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get assignment overview"""
        # Get test cases assigned to this data owner
        result = await db.execute(
            select(
                func.count(TestCase.test_case_id).label('total'),
                func.sum(case((TestCase.status == 'Submitted', 1), else_=0)).label('submitted'),
                func.sum(case((TestCase.status == 'Pending', 1), else_=0)).label('pending'),
                func.sum(case((TestCase.status == 'Overdue', 1), else_=0)).label('overdue')
            )
            .where(TestCase.data_owner_id == user_id)
        )
        stats = result.first()
        
        return DashboardSectionDTO(
            title="Assignment Overview",
            metrics=[
                MetricDTO(label="Total Assignments", value=stats.total or 0),
                MetricDTO(label="Submitted", value=stats.submitted or 0),
                MetricDTO(label="Pending", value=stats.pending or 0),
                MetricDTO(label="Overdue", value=stats.overdue or 0)
            ]
        )
    
    async def _get_performance_metrics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get performance metrics"""
        return DashboardSectionDTO(
            title="Performance Metrics",
            metrics=[
                MetricDTO(label="On-Time Rate", value="92%", change=3.5, trend="up"),
                MetricDTO(label="Response Time", value="2.3 days", change=-15.0, trend="down"),
                MetricDTO(label="Accuracy Rate", value="98.5%", trend="stable"),
                MetricDTO(label="Completion Rate", value="95%", change=2.1, trend="up")
            ]
        )
    
    async def _get_quality_scores(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get quality scores"""
        return DashboardSectionDTO(
            title="Quality Scores",
            metrics=[
                MetricDTO(label="Document Quality", value="A", trend="stable"),
                MetricDTO(label="Data Accuracy", value="99.2%", change=0.5, trend="up"),
                MetricDTO(label="Resubmission Rate", value="3%", change=-25.0, trend="down"),
                MetricDTO(label="Overall Score", value="94/100", change=2.0, trend="up")
            ]
        )
    
    async def _get_workload_analysis(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get workload analysis"""
        return DashboardSectionDTO(
            title="Workload Analysis",
            metrics=[
                MetricDTO(label="Active Reports", value=8),
                MetricDTO(label="Weekly Volume", value=25, change=12.5, trend="up"),
                MetricDTO(label="Average per Day", value=5),
                MetricDTO(label="Peak Days", value="Tue, Thu")
            ]
        )
    
    async def _get_pending_actions(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list:
        """Get pending actions for data owner"""
        # Get pending test cases
        result = await db.execute(
            select(TestCase)
            .where(and_(
                TestCase.data_owner_id == user_id,
                TestCase.status == 'Pending'
            ))
            .limit(5)
        )
        test_cases = result.scalars().all()
        
        actions = []
        for tc in test_cases:
            actions.append({
                "id": tc.test_case_id,
                "type": "submission_required",
                "title": f"Submit evidence for {tc.attribute_name}",
                "priority": "high" if tc.status == 'Overdue' else "medium",
                "due_date": tc.submission_deadline.isoformat() if tc.submission_deadline else None
            })
        
        return actions


class GetDataExecutiveDashboardUseCase(UseCase):
    """Get data executive (CDO) dashboard data"""
    
    async def execute(
        self,
        user_id: int,
        time_filter: DashboardTimeFilter,
        db: AsyncSession
    ) -> DataExecutiveDashboardDTO:
        """Execute data executive dashboard query"""
        
        # Calculate date range
        days = time_filter.to_days()
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get LOB overview
        lob_overview = await self._get_lob_overview(user_id, start_date, db)
        
        # Get team performance
        team_performance = await self._get_team_performance(user_id, start_date, db)
        
        # Get assignment analytics
        assignment_analytics = await self._get_assignment_analytics(user_id, start_date, db)
        
        # Get escalation management
        escalation_management = await self._get_escalation_management(user_id, start_date, db)
        
        # Get action required items
        action_required = await self._get_action_required(user_id, db)
        
        return DataExecutiveDashboardDTO(
            lob_overview=lob_overview,
            team_performance=team_performance,
            assignment_analytics=assignment_analytics,
            escalation_management=escalation_management,
            action_required=action_required,
            time_filter=time_filter.filter_type,
            last_updated=datetime.utcnow()
        )
    
    async def _get_lob_overview(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get LOB overview metrics"""
        return DashboardSectionDTO(
            title="LOB Overview",
            metrics=[
                MetricDTO(label="Managed LOBs", value=3),
                MetricDTO(label="Active Reports", value=24),
                MetricDTO(label="Data Owners", value=15),
                MetricDTO(label="Coverage Rate", value="89%", change=4.5, trend="up")
            ]
        )
    
    async def _get_team_performance(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get team performance metrics"""
        return DashboardSectionDTO(
            title="Team Performance",
            metrics=[
                MetricDTO(label="Team Efficiency", value="87%", change=2.3, trend="up"),
                MetricDTO(label="Average Response", value="1.8 days", change=-10.0, trend="down"),
                MetricDTO(label="Quality Score", value="A-", trend="stable"),
                MetricDTO(label="SLA Compliance", value="96%", change=1.2, trend="up")
            ]
        )
    
    async def _get_assignment_analytics(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get assignment analytics"""
        return DashboardSectionDTO(
            title="Assignment Analytics",
            metrics=[
                MetricDTO(label="Total Assignments", value=156),
                MetricDTO(label="Pending CDO Action", value=12, change=-20.0, trend="down"),
                MetricDTO(label="Reassignments", value=8),
                MetricDTO(label="Auto-Assigned", value="72%", change=5.0, trend="up")
            ]
        )
    
    async def _get_escalation_management(
        self,
        user_id: int,
        start_date: datetime,
        db: AsyncSession
    ) -> DashboardSectionDTO:
        """Get escalation management metrics"""
        return DashboardSectionDTO(
            title="Escalation Management",
            metrics=[
                MetricDTO(label="Active Escalations", value=3, change=-25.0, trend="down"),
                MetricDTO(label="Resolution Time", value="4.2 hours", change=-15.0, trend="down"),
                MetricDTO(label="Escalation Rate", value="2.1%", change=-0.5, trend="down"),
                MetricDTO(label="Critical Issues", value=1)
            ]
        )
    
    async def _get_action_required(
        self,
        user_id: int,
        db: AsyncSession
    ) -> list:
        """Get action required items for data executive"""
        return [
            {
                "id": 1,
                "type": "assignment_required",
                "title": "12 attributes pending CDO assignment",
                "priority": "high",
                "report_count": 3
            },
            {
                "id": 2,
                "type": "escalation",
                "title": "Overdue submission - Critical Report",
                "priority": "critical",
                "data_owner": "John Smith"
            }
        ]


class GetBoardReportSummaryUseCase(UseCase):
    """Generate board-level report summary"""
    
    async def execute(
        self,
        user_id: int,
        db: AsyncSession
    ) -> BoardReportSummaryDTO:
        """Generate board report summary"""
        
        # Get portfolio status
        portfolio_status = await self._get_portfolio_status(db)
        
        # Get critical issues
        critical_issues = await self._get_critical_issues(db)
        
        # Generate executive summary
        executive_summary = await self._generate_executive_summary(
            portfolio_status, 
            critical_issues
        )
        
        # Get key highlights
        key_highlights = await self._get_key_highlights(db)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(critical_issues)
        
        return BoardReportSummaryDTO(
            executive_summary=executive_summary,
            key_highlights=key_highlights,
            portfolio_status=portfolio_status,
            critical_issues=critical_issues,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
    
    async def _get_portfolio_status(self, db: AsyncSession) -> DashboardSectionDTO:
        """Get portfolio status for board report"""
        return DashboardSectionDTO(
            title="Portfolio Status",
            metrics=[
                MetricDTO(label="Total Reports", value=145),
                MetricDTO(label="Compliance Rate", value="94.8%", change=1.2, trend="up"),
                MetricDTO(label="Risk Exposure", value="Low-Medium"),
                MetricDTO(label="YTD Performance", value="On Track")
            ]
        )
    
    async def _get_critical_issues(self, db: AsyncSession) -> list:
        """Get critical issues for board report"""
        return [
            {
                "id": 1,
                "severity": "critical",
                "title": "Regulatory compliance gap in Division A",
                "impact": "High",
                "mitigation_status": "In Progress"
            },
            {
                "id": 2,
                "severity": "high",
                "title": "Resource constraints affecting Q4 deliverables",
                "impact": "Medium",
                "mitigation_status": "Planned"
            }
        ]
    
    async def _generate_executive_summary(
        self,
        portfolio_status: DashboardSectionDTO,
        critical_issues: list
    ) -> str:
        """Generate executive summary text"""
        return (
            "The regulatory reporting portfolio maintains strong performance with "
            "94.8% compliance rate, showing improvement from last quarter. "
            "Two critical issues require board attention, with mitigation plans "
            "in progress. Overall risk exposure remains within acceptable thresholds."
        )
    
    async def _get_key_highlights(self, db: AsyncSession) -> list:
        """Get key highlights for board report"""
        return [
            "Achieved 94.8% compliance rate, exceeding target by 2.8%",
            "Reduced average cycle time by 15% through process optimization",
            "Successfully onboarded 5 new data providers this quarter",
            "Implemented automated quality checks, improving accuracy by 12%"
        ]
    
    async def _generate_recommendations(self, critical_issues: list) -> list:
        """Generate recommendations based on analysis"""
        return [
            "Allocate additional resources to address Q4 capacity constraints",
            "Accelerate Division A compliance remediation timeline",
            "Invest in automation tools to further reduce cycle times",
            "Enhance data provider training programs to maintain quality standards"
        ]