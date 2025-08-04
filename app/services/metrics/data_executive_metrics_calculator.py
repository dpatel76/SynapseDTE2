"""Data Executive (CDO) specific metrics calculator."""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.metrics.base_metrics_calculator import BaseMetricsCalculator
from app.models.lob_assignment import LOBAssignment
from app.models.test_scoping import ScopedReportAttribute
from app.models.sample_selection import SampleSet, CycleReportSampleSelectionSamples
from app.models.test_execution import TestExecution
from app.models.test_planning import TestPlan
from app.models.request_for_information import RFIRequest, RFIResponse
from app.models.observations import Observation
from app.models.workflow_tracking import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.core.enums import WorkflowPhaseState, ScheduleStatus


class DataExecutiveMetricsCalculator(BaseMetricsCalculator):
    """Calculate metrics specific to the Data Executive (CDO) role."""
    
    async def get_data_executive_dashboard_metrics(
        self,
        executive_id: str,
        lob_name: str,
        cycle_id: Optional[str] = None,
        time_period: str = "current_cycle"
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for a data executive."""
        metrics = {
            "lob_summary": {},
            "provider_performance": [],
            "sla_compliance": {},
            "quality_metrics": {},
            "assignment_metrics": {},
            "trend_analysis": {}
        }
        
        # LOB summary
        metrics["lob_summary"] = await self._calculate_lob_summary(
            lob_name,
            cycle_id
        )
        
        # Data provider performance
        metrics["provider_performance"] = await self._calculate_provider_performance(
            lob_name,
            cycle_id
        )
        
        # SLA compliance
        metrics["sla_compliance"] = await self._calculate_lob_sla_compliance(
            lob_name,
            cycle_id
        )
        
        # Quality metrics
        metrics["quality_metrics"] = await self._calculate_lob_quality_metrics(
            lob_name,
            cycle_id
        )
        
        # Assignment metrics
        metrics["assignment_metrics"] = await self._calculate_assignment_distribution(
            lob_name,
            cycle_id
        )
        
        # Trend analysis
        metrics["trend_analysis"] = await self._calculate_lob_trends(
            lob_name,
            time_period
        )
        
        return metrics
    
    async def get_provider_comparison_metrics(
        self,
        lob_name: str,
        cycle_id: str
    ) -> Dict[str, Any]:
        """Compare performance across data providers in the LOB."""
        providers = await self._get_lob_providers(lob_name, cycle_id)
        
        comparison = {
            "providers": [],
            "performance_ranking": [],
            "quality_ranking": [],
            "efficiency_ranking": []
        }
        
        for provider_id in providers:
            provider_metrics = await self._calculate_individual_provider_metrics(
                provider_id,
                lob_name,
                cycle_id
            )
            comparison["providers"].append(provider_metrics)
        
        # Sort by different criteria
        comparison["performance_ranking"] = sorted(
            comparison["providers"],
            key=lambda x: x["on_time_delivery_rate"],
            reverse=True
        )
        
        comparison["quality_ranking"] = sorted(
            comparison["providers"],
            key=lambda x: x["quality_score"],
            reverse=True
        )
        
        comparison["efficiency_ranking"] = sorted(
            comparison["providers"],
            key=lambda x: x["avg_completion_time"],
            reverse=False  # Lower is better
        )
        
        return comparison
    
    async def get_lob_report_breakdown(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed breakdown by report for the LOB."""
        breakdown = {
            "reports": [],
            "summary": {
                "total_reports": 0,
                "total_attributes": 0,
                "total_samples": 0,
                "overall_completion_rate": 0
            }
        }
        
        # Get all reports with LOB assignments
        report_query = select(
            LOBAssignment.report_id,
            LOBAssignment.cycle_id
        ).where(
            LOBAssignment.lob_name == lob_name
        ).distinct()
        
        if cycle_id:
            report_query = report_query.where(LOBAssignment.cycle_id == cycle_id)
        
        report_result = await self.db.execute(report_query)
        
        for row in report_result:
            report_metrics = await self._calculate_lob_report_metrics(
                lob_name,
                row.cycle_id,
                row.report_id
            )
            breakdown["reports"].append(report_metrics)
            
            # Update summary
            breakdown["summary"]["total_attributes"] += report_metrics["attributes_count"]
            breakdown["summary"]["total_samples"] += report_metrics["samples_count"]
        
        breakdown["summary"]["total_reports"] = len(breakdown["reports"])
        
        if breakdown["reports"]:
            breakdown["summary"]["overall_completion_rate"] = sum(
                r["completion_rate"] for r in breakdown["reports"]
            ) / len(breakdown["reports"])
        
        return breakdown
    
    async def _calculate_lob_summary(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate summary metrics for the LOB."""
        summary = {
            "lob_name": lob_name,
            "total_assignments": 0,
            "active_providers": 0,
            "reports_covered": 0,
            "attributes_assigned": 0,
            "samples_assigned": 0,
            "completion_rate": 0,
            "sla_breaches": 0,
            "quality_score": 0
        }
        
        # Get assignment count
        assignment_query = select(
            func.count(LOBAssignment.assignment_id).label("total"),
            func.count(func.distinct(LOBAssignment.assigned_user_id)).label("providers"),
            func.count(func.distinct(LOBAssignment.report_id)).label("reports")
        ).where(
            LOBAssignment.lob_name == lob_name
        )
        
        if cycle_id:
            assignment_query = assignment_query.where(LOBAssignment.cycle_id == cycle_id)
        
        assignment_result = await self.db.execute(assignment_query)
        assignment_data = assignment_result.one()
        
        summary["total_assignments"] = assignment_data.total or 0
        summary["active_providers"] = assignment_data.providers or 0
        summary["reports_covered"] = assignment_data.reports or 0
        
        # Get attribute count
        attr_query = select(
            func.count(ScopedReportAttribute.scoped_attribute_id)
        ).where(
            ScopedReportAttribute.lob_name == lob_name
        )
        
        if cycle_id:
            attr_query = attr_query.where(ScopedReportAttribute.cycle_id == cycle_id)
        
        attr_result = await self.db.execute(attr_query)
        summary["attributes_assigned"] = attr_result.scalar() or 0
        
        # Get sample count
        sample_query = select(func.count(CycleReportSampleSelectionSamples.sample_id)).join(
            SampleSet
        ).where(
            and_(
                SampleSet.lob_name == lob_name,
                SampleSet.is_latest_version == True
            )
        )
        
        if cycle_id:
            sample_query = sample_query.where(SampleSet.cycle_id == cycle_id)
        
        sample_result = await self.db.execute(sample_query)
        summary["samples_assigned"] = sample_result.scalar() or 0
        
        # Calculate completion rate
        if cycle_id:
            completion_data = await self._calculate_lob_completion_rate(lob_name, cycle_id)
            summary["completion_rate"] = completion_data["overall_rate"]
            summary["sla_breaches"] = completion_data["sla_breaches"]
        
        # Calculate quality score
        quality_data = await self._calculate_lob_quality_score(lob_name, cycle_id)
        summary["quality_score"] = quality_data["overall_score"]
        
        return summary
    
    async def _calculate_provider_performance(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculate performance metrics for each data provider in the LOB."""
        providers = await self._get_lob_providers(lob_name, cycle_id)
        
        performance_metrics = []
        
        for provider_id in providers:
            metrics = await self._calculate_individual_provider_metrics(
                provider_id,
                lob_name,
                cycle_id
            )
            performance_metrics.append(metrics)
        
        # Sort by performance score
        performance_metrics.sort(
            key=lambda x: x["performance_score"],
            reverse=True
        )
        
        return performance_metrics
    
    async def _calculate_lob_sla_compliance(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate SLA compliance metrics for the LOB."""
        sla_metrics = {
            "overall_compliance_rate": 0,
            "breaches_by_provider": {},
            "breaches_by_phase": {},
            "critical_breaches": [],
            "at_risk_items": []
        }
        
        # Get all LOB assignments
        assignment_query = select(LOBAssignment).where(
            LOBAssignment.lob_name == lob_name
        )
        
        if cycle_id:
            assignment_query = assignment_query.where(LOBAssignment.cycle_id == cycle_id)
        
        assignment_result = await self.db.execute(assignment_query)
        assignments = assignment_result.scalars().all()
        
        total_deliverables = 0
        on_time_deliverables = 0
        
        for assignment in assignments:
            provider_id = assignment.assigned_user_id
            
            if provider_id not in sla_metrics["breaches_by_provider"]:
                sla_metrics["breaches_by_provider"][provider_id] = {
                    "total": 0,
                    "breaches": 0,
                    "breach_rate": 0
                }
            
            # Check RFI compliance
            rfi_query = select(RFIRequest).where(
                and_(
                    RFIRequest.assigned_to == provider_id,
                    RFIRequest.cycle_id == assignment.cycle_id,
                    RFIRequest.report_id == assignment.report_id
                )
            )
            
            rfi_result = await self.db.execute(rfi_query)
            rfis = rfi_result.scalars().all()
            
            for rfi in rfis:
                total_deliverables += 1
                sla_metrics["breaches_by_provider"][provider_id]["total"] += 1
                
                # Check if responded on time
                response_query = select(RFIResponse).where(
                    RFIResponse.request_id == rfi.request_id
                ).order_by(RFIResponse.created_at.desc())
                
                response_result = await self.db.execute(response_query)
                response = response_result.scalars().first()
                
                if response and rfi.due_date:
                    if response.created_at <= rfi.due_date:
                        on_time_deliverables += 1
                    else:
                        sla_metrics["breaches_by_provider"][provider_id]["breaches"] += 1
                        
                        # Track critical breaches
                        delay_days = (response.created_at - rfi.due_date).days
                        if delay_days > 3:
                            sla_metrics["critical_breaches"].append({
                                "type": "RFI Response",
                                "provider_id": provider_id,
                                "delay_days": delay_days,
                                "subject": rfi.subject
                            })
                elif rfi.status == "pending" and rfi.due_date:
                    # Check if at risk
                    days_until_due = (rfi.due_date - datetime.utcnow()).days
                    if days_until_due <= 1:
                        sla_metrics["at_risk_items"].append({
                            "type": "RFI Response",
                            "provider_id": provider_id,
                            "due_date": rfi.due_date,
                            "subject": rfi.subject
                        })
            
            # Check test execution compliance
            test_query = select(TestPlan).where(
                and_(
                    TestPlan.assigned_to == provider_id,
                    TestPlan.cycle_id == assignment.cycle_id,
                    TestPlan.report_id == assignment.report_id
                )
            )
            
            test_result = await self.db.execute(test_query)
            test_plans = test_result.scalars().all()
            
            for test_plan in test_plans:
                total_deliverables += 1
                sla_metrics["breaches_by_provider"][provider_id]["total"] += 1
                
                # Check if completed on time (assuming 48 hour SLA)
                if test_plan.status == "completed":
                    exec_query = select(TestExecution).where(
                        TestExecution.test_plan_id == test_plan.test_plan_id
                    ).order_by(TestExecution.run_number.desc())
                    
                    exec_result = await self.db.execute(exec_query)
                    execution = exec_result.scalars().first()
                    
                    if execution and execution.completed_at and test_plan.created_at:
                        completion_hours = (
                            execution.completed_at - test_plan.created_at
                        ).total_seconds() / 3600
                        
                        if completion_hours <= 48:
                            on_time_deliverables += 1
                        else:
                            sla_metrics["breaches_by_provider"][provider_id]["breaches"] += 1
        
        # Calculate provider breach rates
        for provider_id, data in sla_metrics["breaches_by_provider"].items():
            if data["total"] > 0:
                data["breach_rate"] = (data["breaches"] / data["total"]) * 100
        
        # Calculate overall compliance
        if total_deliverables > 0:
            sla_metrics["overall_compliance_rate"] = (
                on_time_deliverables / total_deliverables * 100
            )
        
        # Calculate breaches by phase
        for phase_name in ["Request for Information", "Test Execution"]:
            phase_query = select(
                func.count(WorkflowPhase.phase_id).label("total"),
                func.sum(
                    func.cast(
                        WorkflowPhase.schedule_status == ScheduleStatus.PAST_DUE,
                        func.Integer
                    )
                ).label("breaches")
            ).where(
                and_(
                    WorkflowPhase.phase_name == phase_name,
                    WorkflowPhase.phase_data.contains({"lob_name": lob_name})
                )
            )
            
            if cycle_id:
                phase_query = phase_query.where(WorkflowPhase.cycle_id == cycle_id)
            
            phase_result = await self.db.execute(phase_query)
            phase_data = phase_result.one()
            
            if phase_data.total:
                sla_metrics["breaches_by_phase"][phase_name] = {
                    "total": phase_data.total,
                    "breaches": phase_data.breaches or 0,
                    "breach_rate": (
                        (phase_data.breaches or 0) / phase_data.total * 100
                    )
                }
        
        return sla_metrics
    
    async def _calculate_lob_quality_metrics(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate quality metrics for the LOB."""
        quality_metrics = {
            "overall_error_rate": 0,
            "resubmission_rate": 0,
            "first_time_pass_rate": 0,
            "observation_rate": 0,
            "by_provider": {},
            "by_report_type": {},
            "common_issues": []
        }
        
        # Get all test executions for the LOB
        test_query = select(TestExecution, TestPlan, LOBAssignment).join(
            TestPlan,
            TestExecution.test_plan_id == TestPlan.test_plan_id
        ).join(
            LOBAssignment,
            and_(
                LOBAssignment.assigned_user_id == TestPlan.assigned_to,
                LOBAssignment.cycle_id == TestPlan.cycle_id,
                LOBAssignment.report_id == TestPlan.report_id
            )
        ).where(
            LOBAssignment.lob_name == lob_name
        )
        
        if cycle_id:
            test_query = test_query.where(TestPlan.cycle_id == cycle_id)
        
        test_result = await self.db.execute(test_query)
        
        total_tests = 0
        failed_tests = 0
        first_time_passes = 0
        resubmissions = 0
        provider_stats = {}
        
        for execution, test_plan, assignment in test_result:
            if execution.status == "completed":
                total_tests += 1
                provider_id = test_plan.assigned_to
                
                if provider_id not in provider_stats:
                    provider_stats[provider_id] = {
                        "total": 0,
                        "failed": 0,
                        "resubmissions": 0
                    }
                
                provider_stats[provider_id]["total"] += 1
                
                if execution.overall_result == "fail":
                    failed_tests += 1
                    provider_stats[provider_id]["failed"] += 1
                elif execution.run_number == 1 and execution.overall_result == "pass":
                    first_time_passes += 1
                
                if execution.requires_resubmission:
                    resubmissions += 1
                    provider_stats[provider_id]["resubmissions"] += 1
        
        # Calculate overall rates
        if total_tests > 0:
            quality_metrics["overall_error_rate"] = (failed_tests / total_tests) * 100
            quality_metrics["first_time_pass_rate"] = (first_time_passes / total_tests) * 100
            quality_metrics["resubmission_rate"] = (resubmissions / total_tests) * 100
        
        # Calculate by provider
        for provider_id, stats in provider_stats.items():
            if stats["total"] > 0:
                quality_metrics["by_provider"][provider_id] = {
                    "error_rate": (stats["failed"] / stats["total"]) * 100,
                    "resubmission_rate": (stats["resubmissions"] / stats["total"]) * 100,
                    "total_tests": stats["total"]
                }
        
        # Get observation rate
        obs_query = select(
            func.count(Observation.observation_id)
        ).where(
            Observation.metadata.contains({"lob_name": lob_name})
        )
        
        if cycle_id:
            obs_query = obs_query.where(Observation.cycle_id == cycle_id)
        
        obs_result = await self.db.execute(obs_query)
        observation_count = obs_result.scalar() or 0
        
        if total_tests > 0:
            quality_metrics["observation_rate"] = observation_count / total_tests
        
        # Identify common issues
        issue_query = select(
            TestExecution.metadata,
            func.count(TestExecution.execution_id).label("count")
        ).where(
            and_(
                TestExecution.overall_result == "fail",
                TestExecution.metadata != None
            )
        ).group_by(
            TestExecution.metadata
        ).order_by(
            func.count(TestExecution.execution_id).desc()
        ).limit(5)
        
        issue_result = await self.db.execute(issue_query)
        
        for row in issue_result:
            if row.metadata and "failure_reason" in row.metadata:
                quality_metrics["common_issues"].append({
                    "issue": row.metadata["failure_reason"],
                    "frequency": row.count
                })
        
        return quality_metrics
    
    async def _calculate_assignment_distribution(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate assignment distribution metrics for the LOB."""
        distribution = {
            "by_provider": {},
            "by_report": {},
            "workload_balance": {},
            "reassignment_stats": {}
        }
        
        # Get assignments
        assignment_query = select(LOBAssignment).where(
            LOBAssignment.lob_name == lob_name
        )
        
        if cycle_id:
            assignment_query = assignment_query.where(LOBAssignment.cycle_id == cycle_id)
        
        assignment_result = await self.db.execute(assignment_query)
        assignments = assignment_result.scalars().all()
        
        provider_workload = {}
        report_coverage = {}
        total_reassignments = 0
        
        for assignment in assignments:
            provider_id = assignment.assigned_user_id
            report_id = assignment.report_id
            
            # Track by provider
            if provider_id not in provider_workload:
                provider_workload[provider_id] = {
                    "reports": set(),
                    "attributes": 0,
                    "cycle_report_sample_selection_samples": 0,
                    "reassignments": 0
                }
            
            provider_workload[provider_id]["reports"].add(report_id)
            provider_workload[provider_id]["reassignments"] += assignment.reassignment_count
            total_reassignments += assignment.reassignment_count
            
            # Track by report
            if report_id not in report_coverage:
                report_coverage[report_id] = {
                    "providers": set(),
                    "coverage_complete": False
                }
            
            report_coverage[report_id]["providers"].add(provider_id)
            
            # Get attribute and sample counts
            attr_query = select(
                func.count(ScopedReportAttribute.scoped_attribute_id)
            ).where(
                and_(
                    ScopedReportAttribute.cycle_id == assignment.cycle_id,
                    ScopedReportAttribute.report_id == assignment.report_id,
                    ScopedReportAttribute.lob_name == lob_name
                )
            )
            
            attr_result = await self.db.execute(attr_query)
            attr_count = attr_result.scalar() or 0
            provider_workload[provider_id]["attributes"] += attr_count
            
            sample_query = select(func.count(CycleReportSampleSelectionSamples.sample_id)).join(
                SampleSet
            ).where(
                and_(
                    SampleSet.cycle_id == assignment.cycle_id,
                    SampleSet.report_id == assignment.report_id,
                    SampleSet.lob_name == lob_name,
                    SampleSet.is_latest_version == True
                )
            )
            
            sample_result = await self.db.execute(sample_query)
            sample_count = sample_result.scalar() or 0
            provider_workload[provider_id]["cycle_report_sample_selection_samples"] += sample_count
        
        # Convert to distribution metrics
        for provider_id, workload in provider_workload.items():
            distribution["by_provider"][provider_id] = {
                "report_count": len(workload["reports"]),
                "attribute_count": workload["attributes"],
                "sample_count": workload["cycle_report_sample_selection_samples"],
                "reassignment_count": workload["reassignments"]
            }
        
        for report_id, coverage in report_coverage.items():
            from app.models.report import Report
            report_query = select(Report.report_name).where(
                Report.report_id == report_id
            )
            report_result = await self.db.execute(report_query)
            report_name = report_result.scalar()
            
            distribution["by_report"][report_name] = {
                "provider_count": len(coverage["providers"]),
                "coverage_complete": coverage["coverage_complete"]
            }
        
        # Calculate workload balance
        if provider_workload:
            workloads = [w["attributes"] for w in provider_workload.values()]
            avg_workload = sum(workloads) / len(workloads)
            max_workload = max(workloads)
            min_workload = min(workloads)
            
            distribution["workload_balance"] = {
                "average_attributes_per_provider": avg_workload,
                "max_attributes": max_workload,
                "min_attributes": min_workload,
                "balance_score": 100 - ((max_workload - min_workload) / avg_workload * 100)
                if avg_workload > 0 else 100
            }
        
        # Reassignment statistics
        distribution["reassignment_stats"] = {
            "total_reassignments": total_reassignments,
            "reassignment_rate": (
                total_reassignments / len(assignments) * 100
                if assignments else 0
            )
        }
        
        return distribution
    
    async def _calculate_lob_trends(
        self,
        lob_name: str,
        time_period: str
    ) -> Dict[str, Any]:
        """Calculate trend analysis for the LOB."""
        trends = {
            "performance_trend": [],
            "quality_trend": [],
            "sla_trend": [],
            "workload_trend": []
        }
        
        # Get historical cycles
        cycle_query = select(TestCycle).order_by(
            TestCycle.start_date.desc()
        ).limit(6)  # Last 6 cycles
        
        cycle_result = await self.db.execute(cycle_query)
        cycles = cycle_result.scalars().all()
        
        for cycle in cycles:
            # Performance trend
            completion_data = await self._calculate_lob_completion_rate(
                lob_name,
                cycle.cycle_id
            )
            
            trends["performance_trend"].append({
                "cycle_name": cycle.cycle_name,
                "completion_rate": completion_data["overall_rate"],
                "date": cycle.start_date
            })
            
            # Quality trend
            quality_data = await self._calculate_lob_quality_score(
                lob_name,
                cycle.cycle_id
            )
            
            trends["quality_trend"].append({
                "cycle_name": cycle.cycle_name,
                "quality_score": quality_data["overall_score"],
                "error_rate": quality_data.get("error_rate", 0)
            })
            
            # SLA trend
            sla_data = await self._calculate_lob_sla_compliance(
                lob_name,
                cycle.cycle_id
            )
            
            trends["sla_trend"].append({
                "cycle_name": cycle.cycle_name,
                "compliance_rate": sla_data["overall_compliance_rate"],
                "breach_count": sum(
                    d["breaches"] for d in sla_data["breaches_by_provider"].values()
                )
            })
        
        return trends
    
    async def _get_lob_providers(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> List[str]:
        """Get all data providers assigned to the LOB."""
        query = select(
            LOBAssignment.assigned_user_id
        ).where(
            and_(
                LOBAssignment.lob_name == lob_name,
                LOBAssignment.assigned_user_id != None
            )
        ).distinct()
        
        if cycle_id:
            query = query.where(LOBAssignment.cycle_id == cycle_id)
        
        result = await self.db.execute(query)
        return [row[0] for row in result]
    
    async def _calculate_individual_provider_metrics(
        self,
        provider_id: str,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate metrics for an individual provider in the LOB."""
        from app.models.user import User
        
        # Get provider name
        user_query = select(User.full_name).where(User.user_id == provider_id)
        user_result = await self.db.execute(user_query)
        provider_name = user_result.scalar() or "Unknown"
        
        metrics = {
            "provider_id": provider_id,
            "provider_name": provider_name,
            "workload": 0,
            "completion_rate": 0,
            "on_time_delivery_rate": 0,
            "error_rate": 0,
            "resubmission_rate": 0,
            "avg_completion_time": 0,
            "quality_score": 0,
            "performance_score": 0
        }
        
        # Get workload
        assignment_query = select(
            func.count(LOBAssignment.assignment_id)
        ).where(
            and_(
                LOBAssignment.assigned_user_id == provider_id,
                LOBAssignment.lob_name == lob_name
            )
        )
        
        if cycle_id:
            assignment_query = assignment_query.where(LOBAssignment.cycle_id == cycle_id)
        
        assignment_result = await self.db.execute(assignment_query)
        metrics["workload"] = assignment_result.scalar() or 0
        
        # Get test metrics
        test_query = select(TestExecution, TestPlan).join(
            TestPlan
        ).join(
            LOBAssignment,
            and_(
                LOBAssignment.assigned_user_id == TestPlan.assigned_to,
                LOBAssignment.cycle_id == TestPlan.cycle_id,
                LOBAssignment.report_id == TestPlan.report_id,
                LOBAssignment.lob_name == lob_name
            )
        ).where(
            TestPlan.assigned_to == provider_id
        )
        
        if cycle_id:
            test_query = test_query.where(TestPlan.cycle_id == cycle_id)
        
        test_result = await self.db.execute(test_query)
        
        total_tests = 0
        completed_tests = 0
        failed_tests = 0
        resubmissions = 0
        completion_times = []
        on_time_count = 0
        
        for execution, test_plan in test_result:
            total_tests += 1
            
            if execution.status == "completed":
                completed_tests += 1
                
                if execution.overall_result == "fail":
                    failed_tests += 1
                
                if execution.requires_resubmission:
                    resubmissions += 1
                
                # Calculate completion time
                if test_plan.created_at and execution.completed_at:
                    completion_time = (
                        execution.completed_at - test_plan.created_at
                    ).total_seconds() / 3600
                    completion_times.append(completion_time)
                    
                    # Check if on time (48 hour SLA)
                    if completion_time <= 48:
                        on_time_count += 1
        
        # Calculate metrics
        if total_tests > 0:
            metrics["completion_rate"] = (completed_tests / total_tests) * 100
            metrics["error_rate"] = (failed_tests / total_tests) * 100
            metrics["resubmission_rate"] = (resubmissions / total_tests) * 100
        
        if completed_tests > 0:
            metrics["on_time_delivery_rate"] = (on_time_count / completed_tests) * 100
        
        if completion_times:
            metrics["avg_completion_time"] = sum(completion_times) / len(completion_times)
        
        # Calculate scores
        metrics["quality_score"] = max(0, 100 - metrics["error_rate"])
        metrics["performance_score"] = (
            metrics["on_time_delivery_rate"] * 0.5 +
            metrics["completion_rate"] * 0.3 +
            metrics["quality_score"] * 0.2
        )
        
        return metrics
    
    async def _calculate_lob_completion_rate(
        self,
        lob_name: str,
        cycle_id: str
    ) -> Dict[str, Any]:
        """Calculate completion rate for LOB assignments."""
        # Get all test plans for LOB
        test_query = select(
            func.count(TestPlan.test_plan_id).label("total"),
            func.sum(
                func.cast(TestPlan.status == "completed", func.Integer)
            ).label("completed")
        ).join(
            LOBAssignment,
            and_(
                LOBAssignment.assigned_user_id == TestPlan.assigned_to,
                LOBAssignment.cycle_id == TestPlan.cycle_id,
                LOBAssignment.report_id == TestPlan.report_id
            )
        ).where(
            and_(
                LOBAssignment.lob_name == lob_name,
                TestPlan.cycle_id == cycle_id
            )
        )
        
        test_result = await self.db.execute(test_query)
        test_data = test_result.one()
        
        overall_rate = 0
        if test_data.total:
            overall_rate = ((test_data.completed or 0) / test_data.total) * 100
        
        # Count SLA breaches
        breach_count = 0  # Would calculate based on actual SLA data
        
        return {
            "overall_rate": overall_rate,
            "sla_breaches": breach_count
        }
    
    async def _calculate_lob_quality_score(
        self,
        lob_name: str,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate quality score for the LOB."""
        # Get error rate from quality metrics
        quality_data = await self._calculate_lob_quality_metrics(lob_name, cycle_id)
        
        error_rate = quality_data["overall_error_rate"]
        resubmission_rate = quality_data["resubmission_rate"]
        
        # Simple quality score calculation
        quality_score = max(0, 100 - error_rate - (resubmission_rate * 0.5))
        
        return {
            "overall_score": quality_score,
            "error_rate": error_rate,
            "resubmission_rate": resubmission_rate
        }
    
    async def _calculate_lob_report_metrics(
        self,
        lob_name: str,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Calculate metrics for a specific report in the LOB."""
        from app.models.report import Report
        
        # Get report name
        report_query = select(Report.report_name).where(
            Report.report_id == report_id
        )
        report_result = await self.db.execute(report_query)
        report_name = report_result.scalar()
        
        # Get counts
        attr_query = select(
            func.count(ScopedReportAttribute.scoped_attribute_id)
        ).where(
            and_(
                ScopedReportAttribute.cycle_id == cycle_id,
                ScopedReportAttribute.report_id == report_id,
                ScopedReportAttribute.lob_name == lob_name
            )
        )
        
        attr_result = await self.db.execute(attr_query)
        attr_count = attr_result.scalar() or 0
        
        sample_query = select(func.count(CycleReportSampleSelectionSamples.sample_id)).join(
            SampleSet
        ).where(
            and_(
                SampleSet.cycle_id == cycle_id,
                SampleSet.report_id == report_id,
                SampleSet.lob_name == lob_name,
                SampleSet.is_latest_version == True
            )
        )
        
        sample_result = await self.db.execute(sample_query)
        sample_count = sample_result.scalar() or 0
        
        # Get completion rate
        test_query = select(
            func.count(TestPlan.test_plan_id).label("total"),
            func.sum(
                func.cast(TestPlan.status == "completed", func.Integer)
            ).label("completed")
        ).join(
            LOBAssignment,
            and_(
                LOBAssignment.assigned_user_id == TestPlan.assigned_to,
                LOBAssignment.cycle_id == TestPlan.cycle_id,
                LOBAssignment.report_id == TestPlan.report_id
            )
        ).where(
            and_(
                LOBAssignment.lob_name == lob_name,
                TestPlan.cycle_id == cycle_id,
                TestPlan.report_id == report_id
            )
        )
        
        test_result = await self.db.execute(test_query)
        test_data = test_result.one()
        
        completion_rate = 0
        if test_data.total:
            completion_rate = ((test_data.completed or 0) / test_data.total) * 100
        
        return {
            "report_id": report_id,
            "report_name": report_name,
            "cycle_id": cycle_id,
            "attributes_count": attr_count,
            "samples_count": sample_count,
            "test_cases_total": test_data.total or 0,
            "test_cases_completed": test_data.completed or 0,
            "completion_rate": completion_rate
        }