"""
Workflow Retry and Compensation Policies

This module provides retry policies and compensation strategies for
handling failures in the Temporal workflow system.
"""

from typing import Dict, Any, Optional, List, Type
from datetime import timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError, TemporalError

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Different retry strategies for workflow activities"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"


class CompensationAction(Enum):
    """Types of compensation actions"""
    ROLLBACK = "rollback"
    NOTIFY = "notify"
    SKIP = "skip"
    MANUAL_INTERVENTION = "manual_intervention"
    PARTIAL_ROLLBACK = "partial_rollback"


@dataclass
class ActivityRetryConfig:
    """Configuration for activity retries"""
    max_attempts: int = 3
    initial_interval: timedelta = timedelta(seconds=1)
    backoff_coefficient: float = 2.0
    max_interval: timedelta = timedelta(minutes=5)
    non_retryable_error_types: List[str] = None
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF


@dataclass
class CompensationConfig:
    """Configuration for compensation actions"""
    action: CompensationAction
    notify_users: List[str] = None
    rollback_phases: List[str] = None
    custom_message: Optional[str] = None
    require_approval: bool = False


class WorkflowRetryManager:
    """Manages retry policies for workflow activities"""
    
    # Default retry configurations for different activity types
    DEFAULT_CONFIGS = {
        "data_fetch": ActivityRetryConfig(
            max_attempts=5,
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            max_interval=timedelta(minutes=10),
            non_retryable_error_types=["PermissionError", "AuthenticationError"]
        ),
        "llm_request": ActivityRetryConfig(
            max_attempts=3,
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=3.0,
            max_interval=timedelta(minutes=5),
            non_retryable_error_types=["InvalidRequestError", "QuotaExceededError"]
        ),
        "database_operation": ActivityRetryConfig(
            max_attempts=3,
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            max_interval=timedelta(seconds=30),
            non_retryable_error_types=["IntegrityError", "DataError"]
        ),
        "email_notification": ActivityRetryConfig(
            max_attempts=3,
            initial_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
            max_interval=timedelta(minutes=2),
            strategy=RetryStrategy.LINEAR_BACKOFF
        ),
        "phase_transition": ActivityRetryConfig(
            max_attempts=2,
            initial_interval=timedelta(seconds=5),
            strategy=RetryStrategy.FIXED_DELAY,
            non_retryable_error_types=["WorkflowStateError", "InvalidTransitionError"]
        )
    }
    
    @classmethod
    def get_retry_policy(cls, activity_type: str, custom_config: Optional[ActivityRetryConfig] = None) -> RetryPolicy:
        """Get retry policy for an activity type"""
        config = custom_config or cls.DEFAULT_CONFIGS.get(activity_type, ActivityRetryConfig())
        
        return RetryPolicy(
            maximum_attempts=config.max_attempts,
            initial_interval=config.initial_interval,
            backoff_coefficient=config.backoff_coefficient,
            maximum_interval=config.max_interval,
            non_retryable_error_types=config.non_retryable_error_types or []
        )
    
    @classmethod
    def should_retry(cls, error: Exception, attempt: int, config: ActivityRetryConfig) -> bool:
        """Determine if an error should be retried"""
        # Check if max attempts reached
        if attempt >= config.max_attempts:
            return False
        
        # Check if error is non-retryable
        error_type = type(error).__name__
        if config.non_retryable_error_types and error_type in config.non_retryable_error_types:
            return False
        
        # Check for specific error conditions
        if isinstance(error, ApplicationError) and error.non_retryable:
            return False
        
        return True


class CompensationManager:
    """Manages compensation strategies for workflow failures"""
    
    # Phase-specific compensation configurations
    PHASE_COMPENSATIONS = {
        "Planning": CompensationConfig(
            action=CompensationAction.NOTIFY,
            notify_users=["test_manager"],
            custom_message="Planning phase failed. Manual review required."
        ),
        "Scoping": CompensationConfig(
            action=CompensationAction.ROLLBACK,
            rollback_phases=["Planning"],
            notify_users=["test_manager", "report_owner"]
        ),
        "Sample Selection": CompensationConfig(
            action=CompensationAction.PARTIAL_ROLLBACK,
            custom_message="Sample selection failed. Reverting to previous selections."
        ),
        "Data Owner Identification": CompensationConfig(
            action=CompensationAction.NOTIFY,
            notify_users=["cdo", "test_manager"],
            custom_message="Failed to identify data owners. CDO intervention required."
        ),
        "Request for Information": CompensationConfig(
            action=CompensationAction.MANUAL_INTERVENTION,
            notify_users=["data_owner", "test_manager"],
            require_approval=True
        ),
        "Test Execution": CompensationConfig(
            action=CompensationAction.PARTIAL_ROLLBACK,
            custom_message="Test execution failed. Preserving successful test results."
        ),
        "Observation Management": CompensationConfig(
            action=CompensationAction.SKIP,
            custom_message="Observation phase can be retried later."
        ),
        "Finalize Test Report": CompensationConfig(
            action=CompensationAction.NOTIFY,
            notify_users=["report_owner", "test_manager"],
            custom_message="Report finalization failed. Draft report saved."
        )
    }
    
    @classmethod
    async def compensate_failure(
        cls,
        phase_name: str,
        error: Exception,
        workflow_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute compensation logic for a failed phase"""
        config = cls.PHASE_COMPENSATIONS.get(phase_name, CompensationConfig(action=CompensationAction.NOTIFY))
        
        compensation_result = {
            "phase": phase_name,
            "error": str(error),
            "action": config.action.value,
            "timestamp": workflow.now().isoformat(),
            "success": False
        }
        
        try:
            if config.action == CompensationAction.ROLLBACK:
                result = await cls._execute_rollback(phase_name, config, workflow_context)
                compensation_result.update(result)
                
            elif config.action == CompensationAction.PARTIAL_ROLLBACK:
                result = await cls._execute_partial_rollback(phase_name, config, workflow_context)
                compensation_result.update(result)
                
            elif config.action == CompensationAction.NOTIFY:
                result = await cls._send_notifications(config, workflow_context, error)
                compensation_result.update(result)
                
            elif config.action == CompensationAction.MANUAL_INTERVENTION:
                result = await cls._request_manual_intervention(config, workflow_context, error)
                compensation_result.update(result)
                
            elif config.action == CompensationAction.SKIP:
                compensation_result["success"] = True
                compensation_result["message"] = config.custom_message or f"Skipping {phase_name}"
            
            compensation_result["success"] = True
            
        except Exception as comp_error:
            logger.error(f"Compensation failed for {phase_name}: {str(comp_error)}")
            compensation_result["compensation_error"] = str(comp_error)
        
        return compensation_result
    
    @classmethod
    async def _execute_rollback(
        cls,
        phase_name: str,
        config: CompensationConfig,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute rollback compensation"""
        rollback_result = {
            "rollback_phases": config.rollback_phases or [],
            "rollback_completed": []
        }
        
        # In a real implementation, this would call rollback activities
        for phase in config.rollback_phases or []:
            # Simulate rollback
            logger.info(f"Rolling back phase: {phase}")
            rollback_result["rollback_completed"].append(phase)
        
        return rollback_result
    
    @classmethod
    async def _execute_partial_rollback(
        cls,
        phase_name: str,
        config: CompensationConfig,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute partial rollback compensation"""
        return {
            "partial_rollback": True,
            "preserved_data": context.get("completed_items", []),
            "message": config.custom_message
        }
    
    @classmethod
    async def _send_notifications(
        cls,
        config: CompensationConfig,
        context: Dict[str, Any],
        error: Exception
    ) -> Dict[str, Any]:
        """Send notification as compensation"""
        notifications_sent = []
        
        for user_role in config.notify_users or []:
            # In real implementation, this would send actual notifications
            logger.info(f"Sending notification to {user_role}: {config.custom_message}")
            notifications_sent.append(user_role)
        
        return {
            "notifications_sent": notifications_sent,
            "message": config.custom_message
        }
    
    @classmethod
    async def _request_manual_intervention(
        cls,
        config: CompensationConfig,
        context: Dict[str, Any],
        error: Exception
    ) -> Dict[str, Any]:
        """Request manual intervention"""
        intervention_request = {
            "require_approval": config.require_approval,
            "notified_users": config.notify_users or [],
            "intervention_reason": str(error),
            "workflow_paused": True
        }
        
        if config.require_approval:
            # In real implementation, this would pause workflow and wait for approval
            logger.info("Workflow paused pending manual approval")
        
        return intervention_request


# Decorator for activities with automatic retry
def with_retry(activity_type: str, custom_config: Optional[ActivityRetryConfig] = None):
    """Decorator to add retry policy to activities"""
    def decorator(func):
        retry_policy = WorkflowRetryManager.get_retry_policy(activity_type, custom_config)
        return activity.defn(name=func.__name__, retry_policy=retry_policy)(func)
    return decorator


# Compensation-aware activity result
@dataclass
class CompensableActivityResult:
    """Result of an activity that can be compensated"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    compensation_needed: bool = False
    compensation_data: Optional[Dict[str, Any]] = None


async def execute_with_compensation(
    activity_fn,
    phase_name: str,
    workflow_context: Dict[str, Any],
    *args,
    **kwargs
) -> CompensableActivityResult:
    """Execute an activity with compensation support"""
    try:
        result = await activity_fn(*args, **kwargs)
        return CompensableActivityResult(
            success=True,
            data=result,
            compensation_needed=False
        )
    except Exception as e:
        logger.error(f"Activity failed in {phase_name}: {str(e)}")
        
        # Execute compensation
        compensation_result = await CompensationManager.compensate_failure(
            phase_name,
            e,
            workflow_context
        )
        
        return CompensableActivityResult(
            success=False,
            error=str(e),
            compensation_needed=True,
            compensation_data=compensation_result
        )