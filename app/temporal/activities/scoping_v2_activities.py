"""
Scoping V2 Activities for Temporal Workflows

This module contains Temporal activities for the new consolidated scoping system,
providing workflow integration for scoping decision management.
"""

from datetime import timedelta, datetime
from typing import Dict, Any, List, Optional
from temporalio import activity
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.services.scoping_service import ScopingService
from app.models.scoping_v2 import ScopingVersion, ScopingAttribute, VersionStatus, TesterDecision
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.core.exceptions import NotFoundError, BusinessLogicError

logger = logging.getLogger(__name__)


@activity.defn(name="create_scoping_version")
async def create_scoping_version_activity(
    phase_id: int,
    workflow_execution_id: str,
    workflow_run_id: str,
    user_id: int,
    activity_name: str = "create_scoping_version"
) -> Dict[str, Any]:
    """
    Create a new scoping version for a workflow phase.
    
    Args:
        phase_id: The workflow phase ID
        workflow_execution_id: Temporal workflow execution ID
        workflow_run_id: Temporal workflow run ID
        user_id: User creating the version
        activity_name: Name of the activity
        
    Returns:
        Dict containing version information
    """
    try:
        async with get_db() as db:
            service = ScopingService(db)
            
            version = await service.create_version(
                phase_id=phase_id,
                workflow_execution_id=workflow_execution_id,
                workflow_run_id=workflow_run_id,
                activity_name=activity_name,
                user_id=user_id,
                notes=f"Created by Temporal workflow {workflow_execution_id}"
            )
            
            logger.info(f"Created scoping version {version.version_id} for phase {phase_id}")
            
            return {
                "version_id": str(version.version_id),
                "phase_id": version.phase_id,
                "version_number": version.version_number,
                "status": version.version_status.value,
                "created_at": version.created_at.isoformat()
            }
    except Exception as e:
        logger.error(f"Failed to create scoping version: {str(e)}")
        raise


@activity.defn(name="generate_llm_recommendations")
async def generate_llm_recommendations_activity(
    version_id: str,
    planning_attribute_ids: List[int],
    user_id: int,
    llm_provider: str = "openai",
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Generate LLM recommendations for planning attributes.
    
    Args:
        version_id: The scoping version ID
        planning_attribute_ids: List of planning attribute IDs
        user_id: User requesting recommendations
        llm_provider: LLM provider to use
        batch_size: Number of attributes to process in each batch
        
    Returns:
        Dict containing recommendation results
    """
    try:
        async with get_db() as db:
            scoping_service = ScopingService(db)
            
            # Get the version
            version = await scoping_service.get_version(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            # Get planning attributes
            planning_attributes = []
            for attr_id in planning_attribute_ids:
                attr = await db.get(ReportAttribute, attr_id)
                if attr:
                    planning_attributes.append(attr)
            
            # Generate recommendations in batches
            recommendations = []
            total_processed = 0
            successful_recommendations = 0
            failed_recommendations = 0
            
            for i in range(0, len(planning_attributes), batch_size):
                batch = planning_attributes[i:i + batch_size]
                
                for attr in batch:
                    try:
                        # Generate basic recommendation (placeholder for actual LLM service)
                        recommendation = {
                            "recommended_action": "test" if attr.mandatory_flag == "Mandatory" else "skip",
                            "confidence_score": 0.8 if attr.mandatory_flag == "Mandatory" else 0.6,
                            "rationale": f"Recommendation for {attr.attribute_name}",
                            "provider": llm_provider,
                            "is_cde": attr.mandatory_flag == "Mandatory",
                            "is_primary_key": attr.is_primary_key or False,
                            "processing_time_ms": 500
                        }
                        
                        recommendations.append({
                            "planning_attribute_id": attr.id,
                            "recommendation": recommendation
                        })
                        
                        successful_recommendations += 1
                        total_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to generate recommendation for attribute {attr.id}: {str(e)}")
                        failed_recommendations += 1
                        total_processed += 1
                        
                        # Add default recommendation
                        recommendations.append({
                            "planning_attribute_id": attr.id,
                            "recommendation": {
                                "recommended_action": "test",
                                "confidence_score": 0.5,
                                "rationale": f"Default recommendation due to failure: {str(e)}",
                                "provider": llm_provider,
                                "error": str(e)
                            }
                        })
            
            # Add attributes to version
            if recommendations:
                attribute_ids = [r["planning_attribute_id"] for r in recommendations]
                llm_recommendations = [r["recommendation"] for r in recommendations]
                
                attributes = await scoping_service.add_attributes_to_version(
                    version_id=version_id,
                    planning_attribute_ids=attribute_ids,
                    llm_recommendations=llm_recommendations,
                    user_id=user_id
                )
                
                logger.info(f"Added {len(attributes)} attributes with LLM recommendations to version {version_id}")
            
            return {
                "version_id": version_id,
                "total_processed": total_processed,
                "successful_recommendations": successful_recommendations,
                "failed_recommendations": failed_recommendations,
                "attributes_added": len(recommendations),
                "recommendations": recommendations
            }
    except Exception as e:
        logger.error(f"Failed to generate LLM recommendations: {str(e)}")
        raise


@activity.defn(name="validate_scoping_completeness")
async def validate_scoping_completeness_activity(version_id: str) -> Dict[str, Any]:
    """
    Validate that all attributes in a version have tester decisions.
    
    Args:
        version_id: The scoping version ID
        
    Returns:
        Dict containing validation results
    """
    try:
        async with get_db() as db:
            service = ScopingService(db)
            
            version = await service.get_version_with_attributes(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            total_attributes = len(version.attributes)
            pending_decisions = len([attr for attr in version.attributes if not attr.has_tester_decision])
            completed_decisions = total_attributes - pending_decisions
            
            is_complete = pending_decisions == 0
            can_submit = version.can_be_submitted and is_complete
            
            return {
                "version_id": version_id,
                "is_complete": is_complete,
                "can_submit": can_submit,
                "total_attributes": total_attributes,
                "pending_decisions": pending_decisions,
                "completed_decisions": completed_decisions,
                "completion_percentage": (completed_decisions / total_attributes * 100) if total_attributes > 0 else 0
            }
    except Exception as e:
        logger.error(f"Failed to validate scoping completeness: {str(e)}")
        raise


@activity.defn(name="submit_scoping_version")
async def submit_scoping_version_activity(
    version_id: str,
    user_id: int,
    submission_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a scoping version for approval.
    
    Args:
        version_id: The scoping version ID
        user_id: User submitting the version
        submission_notes: Optional submission notes
        
    Returns:
        Dict containing submission results
    """
    try:
        async with get_db() as db:
            service = ScopingService(db)
            
            version = await service.submit_version_for_approval(
                version_id=version_id,
                submission_notes=submission_notes,
                user_id=user_id
            )
            
            logger.info(f"Submitted version {version_id} for approval")
            
            return {
                "version_id": str(version.version_id),
                "status": version.version_status.value,
                "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
                "submission_notes": version.submission_notes,
                "can_be_approved": version.can_be_approved
            }
    except Exception as e:
        logger.error(f"Failed to submit scoping version: {str(e)}")
        raise


@activity.defn(name="approve_scoping_version")
async def approve_scoping_version_activity(
    version_id: str,
    user_id: int,
    approval_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Approve a scoping version.
    
    Args:
        version_id: The scoping version ID
        user_id: User approving the version
        approval_notes: Optional approval notes
        
    Returns:
        Dict containing approval results
    """
    try:
        async with get_db() as db:
            service = ScopingService(db)
            
            version = await service.approve_version(
                version_id=version_id,
                approval_notes=approval_notes,
                user_id=user_id
            )
            
            logger.info(f"Approved version {version_id}")
            
            return {
                "version_id": str(version.version_id),
                "status": version.version_status.value,
                "approved_at": version.approved_at.isoformat() if version.approved_at else None,
                "approval_notes": version.approval_notes,
                "is_current": version.is_current
            }
    except Exception as e:
        logger.error(f"Failed to approve scoping version: {str(e)}")
        raise


@activity.defn(name="calculate_scoping_metrics")
async def calculate_scoping_metrics_activity(version_id: str) -> Dict[str, Any]:
    """
    Calculate comprehensive metrics for a scoping version.
    
    Args:
        version_id: The scoping version ID
        
    Returns:
        Dict containing scoping metrics
    """
    try:
        async with get_db() as db:
            service = ScopingService(db)
            
            statistics = await service.get_version_statistics(version_id)
            
            # Additional metrics calculations
            version = await service.get_version_with_attributes(version_id)
            if not version:
                raise NotFoundError(f"Version {version_id} not found")
            
            # Calculate decision distribution
            decision_distribution = {
                "accept": 0,
                "decline": 0,
                "override": 0,
                "pending": 0
            }
            
            for attr in version.attributes:
                if attr.tester_decision:
                    decision_distribution[attr.tester_decision.value] += 1
                else:
                    decision_distribution["pending"] += 1
            
            # Calculate risk distribution
            risk_distribution = {
                "cde_attributes": statistics["cde_count"],
                "override_attributes": statistics["override_count"],
                "primary_key_attributes": len([attr for attr in version.attributes if attr.is_primary_key]),
                "historical_issue_attributes": len([attr for attr in version.attributes if attr.has_historical_issues])
            }
            
            # Calculate LLM performance
            llm_performance = {
                "accuracy": statistics["llm_accuracy"],
                "total_recommendations": statistics["total_attributes"],
                "agreed_recommendations": int(statistics["llm_accuracy"] * statistics["total_attributes"]) if statistics["llm_accuracy"] else 0,
                "disagreed_recommendations": statistics["total_attributes"] - (int(statistics["llm_accuracy"] * statistics["total_attributes"]) if statistics["llm_accuracy"] else 0)
            }
            
            return {
                "version_id": version_id,
                "basic_statistics": statistics,
                "decision_distribution": decision_distribution,
                "risk_distribution": risk_distribution,
                "llm_performance": llm_performance,
                "calculated_at": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Failed to calculate scoping metrics: {str(e)}")
        raise


# Activity configuration
SCOPING_ACTIVITY_OPTIONS = {
    "start_to_close_timeout": timedelta(minutes=30),
    "retry_policy": {
        "initial_interval": timedelta(seconds=1),
        "backoff_coefficient": 2.0,
        "maximum_interval": timedelta(minutes=5),
        "maximum_attempts": 3
    }
}