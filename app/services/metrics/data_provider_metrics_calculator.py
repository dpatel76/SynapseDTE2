"""Data Provider-specific metrics calculator."""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.metrics.base_metrics_calculator import BaseMetricsCalculator
from app.models.lob_assignment import LOBAssignment
from app.models.test_scoping import ScopedReportAttribute
from app.models.sample_selection import SampleSet, CycleReportSampleSelectionSamples
from app.models.test_planning import TestPlan
from app.models.test_execution import TestExecution
from app.models.request_for_information import RFIRequest, RFIResponse
from app.models.workflow_tracking import WorkflowPhase
from app.core.enums import WorkflowPhaseState


class DataProviderMetricsCalculator(BaseMetricsCalculator):
    """Calculate metrics specific to the Data Provider role."""
    
    async def get_data_provider_dashboard_metrics(
        self,
        provider_id: str,
        cycle_id: Optional[str] = None,
        time_period: str = "current_cycle"
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for a data provider."""
        metrics = {
            "summary": {},
            "assignment_metrics": [],
            "rfi_metrics": {},
            "test_execution_metrics": {},
            "quality_metrics": {},
            "timeline_metrics": {}
        }
        
        # Get assignments for this data provider
        assignments = await self._get_provider_assignments(provider_id, cycle_id)
        
        # Summary metrics
        metrics["summary"] = await self._calculate_provider_summary(
            provider_id,
            assignments
        )
        
        # Detailed assignment metrics
        for assignment in assignments:
            assignment_metric = await self._calculate_assignment_metrics(
                provider_id,
                assignment
            )
            metrics["assignment_metrics"].append(assignment_metric)
        
        # RFI metrics
        metrics["rfi_metrics"] = await self._calculate_rfi_metrics_for_provider(
            provider_id,
            assignments
        )
        
        # Test execution metrics
        metrics["test_execution_metrics"] = await self._calculate_test_metrics_for_provider(
            provider_id,
            assignments
        )
        
        # Quality metrics
        metrics["quality_metrics"] = await self._calculate_quality_metrics_for_provider(
            provider_id,
            assignments
        )
        
        # Timeline metrics
        metrics["timeline_metrics"] = await self._calculate_timeline_metrics_for_provider(
            provider_id,
            assignments
        )
        
        return metrics
    
    async def get_provider_test_case_details(
        self,
        provider_id: str,
        cycle_id: str,
        report_id: str
    ) -> Dict[str, Any]:
        """Get detailed test case information for a provider's assignments."""
        details = {
            "assigned_attributes": [],
            "assigned_samples": [],
            "test_cases": [],
            "summary": {}
        }
        
        # Get assigned attributes
        attr_query = select(ScopedReportAttribute).join(
            LOBAssignment,
            and_(
                LOBAssignment.lob_name == ScopedReportAttribute.lob_name,
                LOBAssignment.cycle_id == ScopedReportAttribute.cycle_id,
                LOBAssignment.report_id == ScopedReportAttribute.report_id
            )
        ).where(
            and_(
                LOBAssignment.assigned_user_id == provider_id,
                LOBAssignment.cycle_id == cycle_id,
                LOBAssignment.report_id == report_id
            )
        )
        
        attr_result = await self.db.execute(attr_query)
        attributes = attr_result.scalars().all()
        
        for attr in attributes:
            details["assigned_attributes"].append({
                "attribute_id": attr.attribute_id,
                "attribute_name": attr.attribute_name,
                "lob_name": attr.lob_name,
                "is_primary_key": attr.is_primary_key
            })
        
        # Get assigned samples
        sample_query = select(CycleReportSampleSelectionSamples).join(
            SampleSet
        ).join(
            LOBAssignment,
            and_(
                LOBAssignment.lob_name == SampleSet.lob_name,
                LOBAssignment.cycle_id == SampleSet.cycle_id,
                LOBAssignment.report_id == SampleSet.report_id
            )
        ).where(
            and_(
                LOBAssignment.assigned_user_id == provider_id,
                LOBAssignment.cycle_id == cycle_id,
                LOBAssignment.report_id == report_id,
                SampleSet.is_latest_version == True
            )
        )
        
        sample_result = await self.db.execute(sample_query)
        samples = sample_result.scalars().all()
        
        for sample in samples:
            details["assigned_samples"].append({
                "sample_id": sample.sample_id,
                "sample_type": sample.sample_type,
                "validation_status": sample.validation_status
            })
        
        # Get test cases
        test_query = select(TestPlan).where(
            and_(
                TestPlan.cycle_id == cycle_id,
                TestPlan.report_id == report_id,
                TestPlan.assigned_to == provider_id
            )
        )
        
        test_result = await self.db.execute(test_query)
        test_plans = test_result.scalars().all()
        
        for test_plan in test_plans:
            # Get execution status
            exec_query = select(TestExecution).where(
                TestExecution.test_plan_id == test_plan.test_plan_id
            ).order_by(TestExecution.run_number.desc())
            
            exec_result = await self.db.execute(exec_query)
            latest_execution = exec_result.scalars().first()
            
            details["test_cases"].append({
                "test_plan_id": test_plan.test_plan_id,
                "attribute_id": test_plan.attribute_id,
                "sample_id": test_plan.sample_id,
                "status": test_plan.status,
                "execution_status": latest_execution.status if latest_execution else "not_started",
                "result": latest_execution.overall_result if latest_execution else None
            })
        
        # Summary
        details["summary"] = {
            "total_attributes": len(details["assigned_attributes"]),
            "total_samples": len(details["assigned_samples"]),
            "total_test_cases": len(details["test_cases"]),
            "completed_test_cases": sum(
                1 for tc in details["test_cases"]
                if tc["execution_status"] == "completed"
            ),
            "passed_test_cases": sum(
                1 for tc in details["test_cases"]
                if tc["result"] == "pass"
            ),
            "failed_test_cases": sum(
                1 for tc in details["test_cases"]
                if tc["result"] == "fail"
            )
        }
        
        return details
    
    async def _get_provider_assignments(
        self,
        provider_id: str,
        cycle_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all LOB assignments for a data provider."""
        query = select(
            LOBAssignment.assignment_id,
            LOBAssignment.cycle_id,
            LOBAssignment.report_id,
            LOBAssignment.lob_name,
            LOBAssignment.assignment_date,
            LOBAssignment.reassignment_count
        ).where(
            LOBAssignment.assigned_user_id == provider_id
        )
        
        if cycle_id:
            query = query.where(LOBAssignment.cycle_id == cycle_id)
        
        result = await self.db.execute(query)
        
        assignments = []
        for row in result:
            assignments.append({
                "assignment_id": row.assignment_id,
                "cycle_id": row.cycle_id,
                "report_id": row.report_id,
                "lob_name": row.lob_name,
                "assignment_date": row.assignment_date,
                "reassignment_count": row.reassignment_count
            })
        
        return assignments
    
    async def _calculate_provider_summary(
        self,
        provider_id: str,
        assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate summary metrics for a data provider."""
        summary = {
            "total_assignments": len(assignments),
            "active_cycles": len(set(a["cycle_id"] for a in assignments)),
            "unique_reports": len(set(a["report_id"] for a in assignments)),
            "unique_lobs": len(set(a["lob_name"] for a in assignments)),
            "pending_rfis": 0,
            "completed_tests": 0,
            "failed_tests": 0,
            "resubmission_required": 0
        }
        
        # Get RFI and test statistics
        for assignment in assignments:
            # RFI count
            rfi_query = select(func.count(RFIRequest.request_id)).where(
                and_(
                    RFIRequest.assigned_to == provider_id,
                    RFIRequest.cycle_id == assignment["cycle_id"],
                    RFIRequest.report_id == assignment["report_id"],
                    RFIRequest.status == "pending"
                )
            )
            
            rfi_result = await self.db.execute(rfi_query)
            summary["pending_rfis"] += rfi_result.scalar() or 0
            
            # Test execution count
            test_query = select(TestExecution).join(
                TestPlan
            ).where(
                and_(
                    TestPlan.assigned_to == provider_id,
                    TestPlan.cycle_id == assignment["cycle_id"],
                    TestPlan.report_id == assignment["report_id"]
                )
            )
            
            test_result = await self.db.execute(test_query)
            test_executions = test_result.scalars().all()
            
            for test_exec in test_executions:
                if test_exec.status == "completed":
                    summary["completed_tests"] += 1
                    if test_exec.overall_result == "fail":
                        summary["failed_tests"] += 1
                
                if test_exec.requires_resubmission:
                    summary["resubmission_required"] += 1
        
        return summary
    
    async def _calculate_assignment_metrics(
        self,
        provider_id: str,
        assignment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate metrics for a specific assignment."""
        metrics = {
            "assignment_id": assignment["assignment_id"],
            "cycle_id": assignment["cycle_id"],
            "report_id": assignment["report_id"],
            "lob_name": assignment["lob_name"],
            "assignment_date": assignment["assignment_date"],
            "reassignment_count": assignment["reassignment_count"],
            "attributes_assigned": 0,
            "samples_assigned": 0,
            "test_cases": 0,
            "completion_status": {}
        }
        
        # Count assigned attributes
        attr_query = select(func.count(ScopedReportAttribute.scoped_attribute_id)).where(
            and_(
                ScopedReportAttribute.cycle_id == assignment["cycle_id"],
                ScopedReportAttribute.report_id == assignment["report_id"],
                ScopedReportAttribute.lob_name == assignment["lob_name"]
            )
        )
        
        attr_result = await self.db.execute(attr_query)
        metrics["attributes_assigned"] = attr_result.scalar() or 0
        
        # Count assigned samples
        sample_query = select(func.count(CycleReportSampleSelectionSamples.sample_id)).join(
            SampleSet
        ).where(
            and_(
                SampleSet.cycle_id == assignment["cycle_id"],
                SampleSet.report_id == assignment["report_id"],
                SampleSet.lob_name == assignment["lob_name"],
                SampleSet.is_latest_version == True
            )
        )
        
        sample_result = await self.db.execute(sample_query)
        metrics["samples_assigned"] = sample_result.scalar() or 0
        
        # Count test cases
        test_query = select(
            func.count(TestPlan.test_plan_id).label("total"),
            func.sum(
                func.cast(TestPlan.status == "completed", func.Integer)
            ).label("completed"),
            func.sum(
                func.cast(TestPlan.status == "rfi_sent", func.Integer)
            ).label("rfi_sent"),
            func.sum(
                func.cast(TestPlan.status == "in_progress", func.Integer)
            ).label("in_progress")
        ).where(
            and_(
                TestPlan.assigned_to == provider_id,
                TestPlan.cycle_id == assignment["cycle_id"],
                TestPlan.report_id == assignment["report_id"]
            )
        )
        
        test_result = await self.db.execute(test_query)
        test_data = test_result.one()
        
        metrics["test_cases"] = test_data.total or 0
        metrics["completion_status"] = {
            "completed": test_data.completed or 0,
            "rfi_sent": test_data.rfi_sent or 0,
            "in_progress": test_data.in_progress or 0,
            "not_started": (test_data.total or 0) - (
                (test_data.completed or 0) +
                (test_data.rfi_sent or 0) +
                (test_data.in_progress or 0)
            )
        }
        
        # Get report name for display
        from app.models.report import Report
        report_query = select(Report.report_name).where(
            Report.report_id == assignment["report_id"]
        )
        report_result = await self.db.execute(report_query)
        metrics["report_name"] = report_result.scalar()
        
        return metrics
    
    async def _calculate_rfi_metrics_for_provider(
        self,
        provider_id: str,
        assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate RFI-related metrics for a data provider."""
        rfi_metrics = {
            "total_rfis_received": 0,
            "rfis_responded": 0,
            "rfis_pending": 0,
            "avg_response_time_hours": 0,
            "by_status": {},
            "recent_rfis": []
        }
        
        response_times = []
        
        # Get all RFIs for this provider
        rfi_query = select(RFIRequest).where(
            RFIRequest.assigned_to == provider_id
        ).order_by(RFIRequest.created_at.desc())
        
        rfi_result = await self.db.execute(rfi_query)
        rfis = rfi_result.scalars().all()
        
        rfi_metrics["total_rfis_received"] = len(rfis)
        
        for rfi in rfis[:5]:  # Get 5 most recent
            rfi_data = {
                "request_id": rfi.request_id,
                "subject": rfi.subject,
                "status": rfi.status,
                "created_at": rfi.created_at,
                "due_date": rfi.due_date
            }
            
            # Check for response
            response_query = select(RFIResponse).where(
                RFIResponse.request_id == rfi.request_id
            ).order_by(RFIResponse.created_at.desc())
            
            response_result = await self.db.execute(response_query)
            response = response_result.scalars().first()
            
            if response:
                rfi_data["responded_at"] = response.created_at
                response_time = (response.created_at - rfi.created_at).total_seconds() / 3600
                response_times.append(response_time)
            
            rfi_metrics["recent_rfis"].append(rfi_data)
        
        # Calculate status breakdown
        for rfi in rfis:
            if rfi.status not in rfi_metrics["by_status"]:
                rfi_metrics["by_status"][rfi.status] = 0
            rfi_metrics["by_status"][rfi.status] += 1
            
            if rfi.status == "responded":
                rfi_metrics["rfis_responded"] += 1
            elif rfi.status == "pending":
                rfi_metrics["rfis_pending"] += 1
        
        # Calculate average response time
        if response_times:
            rfi_metrics["avg_response_time_hours"] = sum(response_times) / len(response_times)
        
        return rfi_metrics
    
    async def _calculate_test_metrics_for_provider(
        self,
        provider_id: str,
        assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate test execution metrics for a data provider."""
        test_metrics = {
            "total_test_cases": 0,
            "completed_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "resubmissions_required": 0,
            "avg_execution_time_hours": 0,
            "by_phase": {},
            "failure_reasons": {}
        }
        
        execution_times = []
        
        # Get all test plans assigned to provider
        test_query = select(TestPlan).where(
            TestPlan.assigned_to == provider_id
        )
        
        test_result = await self.db.execute(test_query)
        test_plans = test_result.scalars().all()
        
        test_metrics["total_test_cases"] = len(test_plans)
        
        for test_plan in test_plans:
            # Get latest execution
            exec_query = select(TestExecution).where(
                TestExecution.test_plan_id == test_plan.test_plan_id
            ).order_by(TestExecution.run_number.desc())
            
            exec_result = await self.db.execute(exec_query)
            latest_execution = exec_result.scalars().first()
            
            if latest_execution:
                if latest_execution.status == "completed":
                    test_metrics["completed_tests"] += 1
                    
                    if latest_execution.overall_result == "pass":
                        test_metrics["passed_tests"] += 1
                    elif latest_execution.overall_result == "fail":
                        test_metrics["failed_tests"] += 1
                        
                        # Track failure reasons
                        if latest_execution.metadata:
                            failure_reason = latest_execution.metadata.get("failure_reason", "unknown")
                            if failure_reason not in test_metrics["failure_reasons"]:
                                test_metrics["failure_reasons"][failure_reason] = 0
                            test_metrics["failure_reasons"][failure_reason] += 1
                
                if latest_execution.requires_resubmission:
                    test_metrics["resubmissions_required"] += 1
                
                # Calculate execution time
                if latest_execution.started_at and latest_execution.completed_at:
                    exec_time = (
                        latest_execution.completed_at - latest_execution.started_at
                    ).total_seconds() / 3600
                    execution_times.append(exec_time)
        
        # Calculate average execution time
        if execution_times:
            test_metrics["avg_execution_time_hours"] = sum(execution_times) / len(execution_times)
        
        # Calculate metrics by phase
        for phase in ["Document Upload", "Data Validation", "Test Execution"]:
            phase_count = sum(
                1 for tp in test_plans
                if tp.metadata and tp.metadata.get("current_phase") == phase
            )
            test_metrics["by_phase"][phase] = phase_count
        
        return test_metrics
    
    async def _calculate_quality_metrics_for_provider(
        self,
        provider_id: str,
        assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for a data provider."""
        quality_metrics = {
            "error_rate": 0,
            "first_time_pass_rate": 0,
            "resubmission_rate": 0,
            "data_completeness_score": 0,
            "by_report": {}
        }
        
        total_tests = 0
        failed_tests = 0
        first_time_passes = 0
        resubmissions = 0
        
        for assignment in assignments:
            # Get test executions for this assignment
            test_query = select(TestExecution).join(
                TestPlan
            ).where(
                and_(
                    TestPlan.assigned_to == provider_id,
                    TestPlan.cycle_id == assignment["cycle_id"],
                    TestPlan.report_id == assignment["report_id"]
                )
            )
            
            test_result = await self.db.execute(test_query)
            executions = test_result.scalars().all()
            
            report_tests = 0
            report_failures = 0
            
            for execution in executions:
                if execution.status == "completed":
                    total_tests += 1
                    report_tests += 1
                    
                    if execution.overall_result == "fail":
                        failed_tests += 1
                        report_failures += 1
                    elif execution.run_number == 1 and execution.overall_result == "pass":
                        first_time_passes += 1
                    
                    if execution.requires_resubmission:
                        resubmissions += 1
            
            # Store by report
            if report_tests > 0:
                from app.models.report import Report
                report_query = select(Report.report_name).where(
                    Report.report_id == assignment["report_id"]
                )
                report_result = await self.db.execute(report_query)
                report_name = report_result.scalar()
                
                quality_metrics["by_report"][report_name] = {
                    "total_tests": report_tests,
                    "failed_tests": report_failures,
                    "error_rate": (report_failures / report_tests * 100) if report_tests > 0 else 0
                }
        
        # Calculate overall metrics
        if total_tests > 0:
            quality_metrics["error_rate"] = (failed_tests / total_tests) * 100
            quality_metrics["first_time_pass_rate"] = (first_time_passes / total_tests) * 100
            quality_metrics["resubmission_rate"] = (resubmissions / total_tests) * 100
            
            # Simple data completeness score (inverse of error rate)
            quality_metrics["data_completeness_score"] = max(0, 100 - quality_metrics["error_rate"])
        
        return quality_metrics
    
    async def _calculate_timeline_metrics_for_provider(
        self,
        provider_id: str,
        assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate timeline and SLA metrics for a data provider."""
        timeline_metrics = {
            "avg_rfi_response_time": 0,
            "avg_test_completion_time": 0,
            "on_time_delivery_rate": 0,
            "sla_breaches": 0,
            "upcoming_deadlines": []
        }
        
        rfi_response_times = []
        test_completion_times = []
        on_time_deliveries = 0
        total_deliveries = 0
        
        # RFI response times
        rfi_query = select(RFIRequest, RFIResponse).join(
            RFIResponse,
            RFIResponse.request_id == RFIRequest.request_id
        ).where(
            RFIRequest.assigned_to == provider_id
        )
        
        rfi_result = await self.db.execute(rfi_query)
        
        for rfi, response in rfi_result:
            response_time = (response.created_at - rfi.created_at).total_seconds() / 3600
            rfi_response_times.append(response_time)
            
            # Check if on time
            if rfi.due_date and response.created_at <= rfi.due_date:
                on_time_deliveries += 1
            total_deliveries += 1
        
        # Test completion times
        test_query = select(TestPlan, TestExecution).join(
            TestExecution,
            TestExecution.test_plan_id == TestPlan.test_plan_id
        ).where(
            and_(
                TestPlan.assigned_to == provider_id,
                TestExecution.status == "completed"
            )
        )
        
        test_result = await self.db.execute(test_query)
        
        for test_plan, execution in test_result:
            if test_plan.created_at and execution.completed_at:
                completion_time = (
                    execution.completed_at - test_plan.created_at
                ).total_seconds() / 3600
                test_completion_times.append(completion_time)
                
                # Check if on time (assuming 48 hour SLA)
                if completion_time <= 48:
                    on_time_deliveries += 1
                else:
                    timeline_metrics["sla_breaches"] += 1
                total_deliveries += 1
        
        # Calculate averages
        if rfi_response_times:
            timeline_metrics["avg_rfi_response_time"] = (
                sum(rfi_response_times) / len(rfi_response_times)
            )
        
        if test_completion_times:
            timeline_metrics["avg_test_completion_time"] = (
                sum(test_completion_times) / len(test_completion_times)
            )
        
        if total_deliveries > 0:
            timeline_metrics["on_time_delivery_rate"] = (
                on_time_deliveries / total_deliveries * 100
            )
        
        # Get upcoming deadlines
        upcoming_query = select(RFIRequest).where(
            and_(
                RFIRequest.assigned_to == provider_id,
                RFIRequest.status == "pending",
                RFIRequest.due_date != None
            )
        ).order_by(RFIRequest.due_date)
        
        upcoming_result = await self.db.execute(upcoming_query)
        upcoming_rfis = upcoming_result.scalars().all()
        
        for rfi in upcoming_rfis[:5]:  # Get next 5 deadlines
            days_until_due = (rfi.due_date - datetime.utcnow()).days
            
            timeline_metrics["upcoming_deadlines"].append({
                "type": "RFI Response",
                "subject": rfi.subject,
                "due_date": rfi.due_date,
                "days_until_due": days_until_due,
                "urgency": "high" if days_until_due <= 1 else "medium" if days_until_due <= 3 else "low"
            })
        
        return timeline_metrics