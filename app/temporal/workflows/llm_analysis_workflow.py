"""LLM Analysis Workflow - Temporal sandbox compliant"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any

# Import only data classes - no activities
from app.temporal.shared import (
    LLMAnalysisWorkflowInput, WorkflowStatus,
    LLM_ACTIVITY_TIMEOUT, LLM_RETRY_ATTEMPTS
)


@workflow.defn
class LLMAnalysisWorkflow:
    """Workflow for asynchronous LLM analysis operations - sandbox compliant"""
    
    def __init__(self):
        self.status = WorkflowStatus.PENDING
        self.analysis_type: str = ""
        self.result: Dict[str, Any] = {}
    
    @workflow.run
    async def run(self, input_data: LLMAnalysisWorkflowInput) -> Dict[str, Any]:
        """Execute LLM analysis workflow"""
        
        self.status = WorkflowStatus.RUNNING
        self.analysis_type = input_data.analysis_type
        workflow.logger.info(f"Starting LLM analysis workflow: {self.analysis_type}")
        
        # Define retry policy for LLM operations
        retry_policy = RetryPolicy(
            maximum_attempts=LLM_RETRY_ATTEMPTS,
            initial_interval=timedelta(seconds=5),
            maximum_interval=timedelta(seconds=60),
            backoff_coefficient=2
        )
        
        try:
            # Route to appropriate analysis type
            if self.analysis_type == "generate_test_attributes":
                self.result = await self._generate_test_attributes(
                    input_data.parameters,
                    retry_policy
                )
            elif self.analysis_type == "analyze_document":
                self.result = await self._analyze_document(
                    input_data.parameters,
                    retry_policy
                )
            elif self.analysis_type == "recommend_tests":
                self.result = await self._recommend_tests(
                    input_data.parameters,
                    retry_policy
                )
            elif self.analysis_type == "analyze_patterns":
                self.result = await self._analyze_patterns(
                    input_data.parameters,
                    retry_policy
                )
            else:
                raise ValueError(f"Unknown analysis type: {self.analysis_type}")
            
            # Mark workflow as completed
            self.status = WorkflowStatus.COMPLETED
            
            # Notify user of completion
            await workflow.execute_activity(
                "create_in_app_notification_activity",
                {
                    "user_id": input_data.requested_by,
                    "notification_type": "LLM_ANALYSIS_COMPLETE",
                    "title": f"LLM Analysis Complete: {self.analysis_type}",
                    "message": f"Your {self.analysis_type} analysis has been completed",
                    "priority": "MEDIUM",
                    "metadata": {
                        "analysis_type": self.analysis_type,
                        "request_id": input_data.request_id
                    }
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            return {
                "status": "completed",
                "analysis_type": self.analysis_type,
                "result": self.result,
                "request_id": input_data.request_id
            }
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            workflow.logger.error(f"LLM analysis failed: {str(e)}")
            
            # Notify user of failure
            await workflow.execute_activity(
                "create_in_app_notification_activity",
                {
                    "user_id": input_data.requested_by,
                    "notification_type": "LLM_ANALYSIS_FAILED",
                    "title": f"LLM Analysis Failed: {self.analysis_type}",
                    "message": f"Analysis failed: {str(e)}",
                    "priority": "HIGH",
                    "metadata": {
                        "analysis_type": self.analysis_type,
                        "error": str(e)
                    }
                },
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy
            )
            
            raise
    
    async def _generate_test_attributes(
        self,
        parameters: Dict[str, Any],
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Generate test attributes using LLM"""
        
        return await workflow.execute_activity(
            "generate_test_attributes_activity",
            parameters,
            start_to_close_timeout=LLM_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )
    
    async def _analyze_document(
        self,
        parameters: Dict[str, Any],
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Analyze document using LLM"""
        
        return await workflow.execute_activity(
            "analyze_document_activity",
            parameters,
            start_to_close_timeout=LLM_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )
    
    async def _recommend_tests(
        self,
        parameters: Dict[str, Any],
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Get test recommendations from LLM"""
        
        return await workflow.execute_activity(
            "recommend_tests_activity",
            parameters,
            start_to_close_timeout=LLM_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )
    
    async def _analyze_patterns(
        self,
        parameters: Dict[str, Any],
        retry_policy: RetryPolicy
    ) -> Dict[str, Any]:
        """Analyze patterns using LLM"""
        
        return await workflow.execute_activity(
            "analyze_patterns_activity",
            parameters,
            start_to_close_timeout=LLM_ACTIVITY_TIMEOUT,
            retry_policy=retry_policy
        )