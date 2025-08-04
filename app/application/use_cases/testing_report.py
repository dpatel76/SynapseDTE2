"""Testing Report phase use cases"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.application.interfaces.repositories import (
    TestCycleRepository,
    ReportRepository,
    WorkflowRepository,
    UserRepository
)
from app.application.interfaces.services import (
    LLMService,
    NotificationService,
    EmailService,
    AuditService,
    DocumentStorageService
)
from .base import UseCase, UseCaseResult


class GenerateTestingReportUseCase(UseCase[Dict[str, Any], Dict[str, Any]]):
    """Use case for generating the testing report"""
    
    def __init__(
        self,
        cycle_repository: TestCycleRepository,
        workflow_repository: WorkflowRepository,
        llm_service: LLMService,
        document_storage_service: DocumentStorageService,
        audit_service: AuditService
    ):
        self.cycle_repository = cycle_repository
        self.workflow_repository = workflow_repository
        self.llm_service = llm_service
        self.document_storage_service = document_storage_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[Dict[str, Any]]:
        """Generate comprehensive testing report"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Testing Report"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Testing Report phase is not active")
            
            # Gather data from all phases
            cycle = await self.cycle_repository.get(cycle_id)
            if not cycle:
                return self._failure("Test cycle not found")
            
            # Collect data from each phase
            phase_data = await self._collect_phase_data(cycle_id, report_id)
            
            # Generate report sections
            report_sections = {
                "executive_summary": await self._generate_executive_summary(phase_data),
                "testing_methodology": await self._generate_methodology_section(phase_data),
                "sample_selection": await self._generate_sample_section(phase_data),
                "test_results": await self._generate_results_section(phase_data),
                "observations": await self._generate_observations_section(phase_data),
                "recommendations": await self._generate_recommendations_section(phase_data),
                "appendices": await self._generate_appendices(phase_data)
            }
            
            # Compile full report
            full_report = self._compile_report(report_sections, cycle, phase_data)
            
            # Store report document
            report_content = json.dumps(full_report, indent=2).encode('utf-8')
            document_id = await self.document_storage_service.store_document(
                file_content=report_content,
                filename=f"testing_report_{cycle_id}_{report_id}_{datetime.utcnow().strftime('%Y%m%d')}.json",
                content_type="application/json",
                metadata={
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "phase": "Testing Report",
                    "generated_by": user_id,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
            # Update phase metadata
            metadata = phase_status.get('metadata', {})
            metadata['report_generated'] = True
            metadata['document_id'] = document_id
            metadata['generated_at'] = datetime.utcnow().isoformat()
            metadata['generated_by'] = user_id
            metadata['sections_completed'] = list(report_sections.keys())
            metadata['report_status'] = 'draft'
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Testing Report",
                status={
                    "status": "in_progress",
                    "metadata": metadata
                }
            )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="GENERATE_TESTING_REPORT",
                resource_type="testing_report",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "document_id": document_id,
                    "sections": list(report_sections.keys())
                }
            )
            
            return self._success({
                "document_id": document_id,
                "report_status": "draft",
                "sections": list(report_sections.keys()),
                "preview": report_sections.get("executive_summary", "")
            })
            
        except Exception as e:
            return self._failure(f"Failed to generate testing report: {str(e)}")
    
    async def _collect_phase_data(self, cycle_id: int, report_id: int) -> Dict[str, Any]:
        """Collect data from all workflow phases"""
        phases = [
            "Planning", "Scoping", "Sample Selection", "Data Owner Identification",
            "Request for Information", "Test Execution", "Observation Management"
        ]
        
        phase_data = {}
        for phase_name in phases:
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, phase_name
            )
            if phase_status:
                phase_data[phase_name] = phase_status
        
        return phase_data
    
    async def _generate_executive_summary(self, phase_data: Dict[str, Any]) -> str:
        """Generate executive summary using LLM"""
        # Extract key metrics
        testing_data = phase_data.get("Test Execution", {}).get("metadata", {})
        observation_data = phase_data.get("Observation Management", {}).get("metadata", {})
        
        summary_context = {
            "total_tests": testing_data.get("total_tests", 0),
            "tests_passed": testing_data.get("tests_passed", 0),
            "tests_failed": testing_data.get("tests_failed", 0),
            "pass_rate": testing_data.get("pass_rate", 0),
            "total_observations": observation_data.get("total_observations", 0),
            "critical_observations": observation_data.get("critical_observations", 0),
            "high_observations": observation_data.get("high_observations", 0)
        }
        
        result = await self.llm_service.generate_report_summary(
            test_results=[],  # Simplified for this example
            observations=[],
            cycle_context=summary_context
        )
        
        return result
    
    async def _generate_methodology_section(self, phase_data: Dict[str, Any]) -> str:
        """Generate testing methodology section"""
        scoping_data = phase_data.get("Scoping", {}).get("metadata", {})
        sample_data = phase_data.get("Sample Selection", {}).get("metadata", {})
        
        return f"""
## Testing Methodology

### Approach
The testing was conducted following a risk-based approach with {scoping_data.get('total_attributes', 0)} attributes identified for testing.

### Sample Selection
- Methodology: {sample_data.get('methodology', 'Statistical sampling')}
- Sample Size: {sample_data.get('sample_size', 0)}
- Coverage: {sample_data.get('coverage_percentage', 0)}%

### Test Types
- Document verification
- Database validation
- Manual inspection
"""
    
    async def _generate_sample_section(self, phase_data: Dict[str, Any]) -> str:
        """Generate sample selection section"""
        sample_data = phase_data.get("Sample Selection", {}).get("metadata", {})
        
        return f"""
## Sample Selection

### Selection Criteria
{sample_data.get('approach', 'Risk-based selection focusing on high-value transactions')}

### Sample Distribution
- Total Samples: {sample_data.get('sample_size', 0)}
- Selection Method: {sample_data.get('methodology', 'Statistical random sampling')}
"""
    
    async def _generate_results_section(self, phase_data: Dict[str, Any]) -> str:
        """Generate test results section"""
        testing_data = phase_data.get("Test Execution", {}).get("metadata", {})
        
        return f"""
## Test Results

### Overall Performance
- Total Tests Executed: {testing_data.get('total_tests', 0)}
- Tests Passed: {testing_data.get('tests_passed', 0)}
- Tests Failed: {testing_data.get('tests_failed', 0)}
- Pass Rate: {testing_data.get('pass_rate', 0):.1f}%

### Test Coverage
All identified attributes were tested using appropriate testing methods.
"""
    
    async def _generate_observations_section(self, phase_data: Dict[str, Any]) -> str:
        """Generate observations section"""
        observation_data = phase_data.get("Observation Management", {}).get("metadata", {})
        observations = observation_data.get("observations", [])
        
        section = "## Observations\n\n"
        
        # Group by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_obs = [o for o in observations if o.get('severity') == severity]
            if severity_obs:
                section += f"### {severity.title()} Severity\n"
                for obs in severity_obs:
                    section += f"- **{obs['title']}**: {obs.get('description', '')[:100]}...\n"
                section += "\n"
        
        return section
    
    async def _generate_recommendations_section(self, phase_data: Dict[str, Any]) -> str:
        """Generate recommendations section"""
        observation_data = phase_data.get("Observation Management", {}).get("metadata", {})
        
        # Use LLM to generate recommendations based on observations
        if observation_data.get("observation_groups"):
            return """
## Recommendations

Based on the testing results and observations identified, we recommend:

1. **Immediate Actions**: Address all critical observations within 30 days
2. **Process Improvements**: Implement enhanced controls for areas with repeated failures
3. **Monitoring**: Establish continuous monitoring for high-risk attributes
4. **Training**: Provide additional training for data owners on compliance requirements
"""
        else:
            return "## Recommendations\n\nNo significant recommendations at this time."
    
    async def _generate_appendices(self, phase_data: Dict[str, Any]) -> str:
        """Generate appendices section"""
        return """
## Appendices

- Appendix A: Detailed Test Results
- Appendix B: Supporting Documentation
- Appendix C: Data Owner Responses
- Appendix D: Testing Evidence
"""
    
    def _compile_report(self, sections: Dict[str, str], cycle: Any, phase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all sections into final report"""
        return {
            "report_metadata": {
                "cycle_id": cycle.id,
                "cycle_name": cycle.cycle_name,
                "report_date": datetime.utcnow().isoformat(),
                "reporting_period": {
                    "start": cycle.start_date.isoformat(),
                    "end": cycle.end_date.isoformat()
                }
            },
            "sections": sections,
            "generated_at": datetime.utcnow().isoformat()
        }


class ReviewTestingReportUseCase(UseCase[Dict[str, Any], Dict[str, Any]]):
    """Use case for reviewing and approving testing report"""
    
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        email_service: EmailService,
        audit_service: AuditService
    ):
        self.workflow_repository = workflow_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.email_service = email_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[Dict[str, Any]]:
        """Review and approve testing report"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            reviewer_id = request['reviewer_id']
            action = request['action']  # 'approve', 'reject', 'request_changes'
            comments = request.get('comments', '')
            
            # Validate reviewer permissions
            reviewer_permissions = await self.user_repository.get_user_permissions(reviewer_id)
            if "report.approve" not in reviewer_permissions:
                return self._failure("User does not have permission to review reports")
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Testing Report"
            )
            if not phase_status:
                return self._failure("Testing Report phase not found")
            
            metadata = phase_status.get('metadata', {})
            
            # Update report status based on action
            old_status = metadata.get('report_status', 'draft')
            
            if action == 'approve':
                new_status = 'approved'
                metadata['approved_by'] = reviewer_id
                metadata['approved_at'] = datetime.utcnow().isoformat()
            elif action == 'reject':
                new_status = 'rejected'
                metadata['rejected_by'] = reviewer_id
                metadata['rejected_at'] = datetime.utcnow().isoformat()
            elif action == 'request_changes':
                new_status = 'pending_changes'
                metadata['changes_requested_by'] = reviewer_id
                metadata['changes_requested_at'] = datetime.utcnow().isoformat()
            else:
                return self._failure(f"Invalid action: {action}")
            
            # Add review comments
            reviews = metadata.get('reviews', [])
            reviews.append({
                "reviewer_id": reviewer_id,
                "action": action,
                "comments": comments,
                "reviewed_at": datetime.utcnow().isoformat()
            })
            metadata['reviews'] = reviews
            metadata['report_status'] = new_status
            
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Testing Report",
                status={
                    "status": phase_status.get('status'),
                    "metadata": metadata
                }
            )
            
            # Get report owner for notifications
            reviewer = await self.user_repository.get(reviewer_id)
            
            # Send notifications
            notification_title = f"Testing Report {action.replace('_', ' ').title()}"
            notification_message = f"Testing report has been {action.replace('_', ' ')} by {reviewer.get('full_name', 'Reviewer')}"
            
            await self.notification_service.send_notification(
                user_id=metadata.get('generated_by', reviewer_id),
                title=notification_title,
                message=notification_message,
                notification_type=f"report_{action}",
                priority="high",
                metadata={"review_action": action}
            )
            
            # Send email for important actions
            if action in ['approve', 'reject']:
                # Get report owner executives
                executives = await self.user_repository.find_by_role("Report Owner Executive")
                for exec in executives:
                    await self.email_service.send_template_email(
                        to_email=exec.get('email'),
                        template_name=f"report_{action}",
                        context={
                            "executive_name": exec.get('full_name'),
                            "cycle_id": cycle_id,
                            "report_id": report_id,
                            "reviewer_name": reviewer.get('full_name'),
                            "comments": comments
                        }
                    )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=reviewer_id,
                action=f"REVIEW_TESTING_REPORT_{action.upper()}",
                resource_type="testing_report",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "comments": comments
                }
            )
            
            return self._success({
                "report_status": new_status,
                "action": action,
                "reviewed_by": reviewer_id,
                "reviewed_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return self._failure(f"Failed to review testing report: {str(e)}")


class FinalizeTestingReportUseCase(UseCase[Dict[str, Any], Dict[str, Any]]):
    """Use case for finalizing testing report and completing workflow"""
    
    def __init__(
        self,
        cycle_repository: TestCycleRepository,
        workflow_repository: WorkflowRepository,
        document_storage_service: DocumentStorageService,
        notification_service: NotificationService,
        email_service: EmailService,
        audit_service: AuditService
    ):
        self.cycle_repository = cycle_repository
        self.workflow_repository = workflow_repository
        self.document_storage_service = document_storage_service
        self.notification_service = notification_service
        self.email_service = email_service
        self.audit_service = audit_service
    
    async def execute(self, request: Dict[str, Any]) -> UseCaseResult[Dict[str, Any]]:
        """Finalize testing report and complete entire workflow"""
        try:
            cycle_id = request['cycle_id']
            report_id = request['report_id']
            user_id = request['user_id']
            
            # Check workflow phase
            phase_status = await self.workflow_repository.get_phase_status(
                cycle_id, report_id, "Testing Report"
            )
            if not phase_status or phase_status.get('status') != 'in_progress':
                return self._failure("Testing Report phase is not active")
            
            metadata = phase_status.get('metadata', {})
            
            # Verify report is approved
            if metadata.get('report_status') != 'approved':
                return self._failure("Report must be approved before finalization")
            
            # Generate final report document (PDF or other format)
            # This is simplified - in real implementation would generate actual document
            final_document_id = metadata.get('document_id')
            
            # Complete Testing Report phase
            await self.workflow_repository.save_phase_status(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Testing Report",
                status={
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        **metadata,
                        "finalized_by": user_id,
                        "finalized_at": datetime.utcnow().isoformat(),
                        "final_document_id": final_document_id
                    }
                }
            )
            
            # Update cycle status to completed if all reports are done
            cycle = await self.cycle_repository.get(cycle_id)
            if cycle:
                # Check if all reports in cycle are completed
                all_completed = True
                for report_assignment in cycle.reports:
                    report_phase = await self.workflow_repository.get_phase_status(
                        cycle_id, report_assignment.report_id, "Testing Report"
                    )
                    if not report_phase or report_phase.get('status') != 'completed':
                        all_completed = False
                        break
                
                if all_completed:
                    cycle.complete()
                    await self.cycle_repository.save(cycle)
            
            # Send notifications to all stakeholders
            stakeholder_roles = ["Test Executive", "Report Owner", "Report Owner Executive"]
            for role in stakeholder_roles:
                stakeholders = await self.user_repository.find_by_role(role)
                await self.notification_service.send_bulk_notifications(
                    user_ids=[s['user_id'] for s in stakeholders],
                    title="Testing Report Finalized",
                    message=f"Testing report for cycle {cycle.cycle_name} has been finalized",
                    notification_type="report_finalized",
                    priority="high"
                )
            
            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action="FINALIZE_TESTING_REPORT",
                resource_type="testing_report",
                resource_id=report_id,
                details={
                    "cycle_id": cycle_id,
                    "final_document_id": final_document_id,
                    "workflow_completed": True
                }
            )
            
            return self._success({
                "status": "finalized",
                "final_document_id": final_document_id,
                "workflow_completed": True,
                "finalized_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return self._failure(f"Failed to finalize testing report: {str(e)}")