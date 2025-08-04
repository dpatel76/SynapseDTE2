"""
Clean Architecture Observation Management API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.application.dtos.observation import (
    ObservationCreateDTO,
    ObservationResponseDTO,
    ObservationUpdateDTO,
    ImpactAssessmentCreateDTO,
    ImpactAssessmentResponseDTO,
    ObservationApprovalRequestDTO,
    ObservationApprovalResponseDTO,
    ObservationBatchReviewRequestDTO,
    ResolutionCreateDTO,
    ResolutionResponseDTO,
    ObservationPhaseStartDTO,
    ObservationPhaseStatusDTO,
    ObservationPhaseCompleteDTO,
    ObservationAnalyticsDTO,
    AutoDetectionRequestDTO,
    ObservationTypeEnum,
    ObservationSeverityEnum,
    ObservationStatusEnum
)
from app.application.use_cases.observation import (
    CreateObservationUseCase,
    GetObservationUseCase,
    ListObservationsUseCase,
    UpdateObservationUseCase,
    SubmitObservationUseCase,
    ReviewObservationUseCase,
    BatchReviewObservationsUseCase,
    CreateImpactAssessmentUseCase,
    CreateResolutionUseCase,
    GetObservationPhaseStatusUseCase,
    CompleteObservationPhaseUseCase,
    GetObservationAnalyticsUseCase,
    AutoDetectObservationsUseCase
)

router = APIRouter()


# Observation Versioning Endpoints
@router.post("/{cycle_id}/reports/{report_id}/versions/create-and-submit")
@require_permission("observations", "update")
async def create_and_submit_observation_version(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new observation version and submit for approval"""
    # from app.services.observation_versioning_service import ObservationVersioningService  # Commented to avoid ObservationVersion duplicate
    from app.models.workflow import WorkflowPhase
    from sqlalchemy import select, and_
    
    try:
        # Get the observation phase
        phase_query = select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Observations"
            )
        )
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation phase not found"
            )
        
        # Temporarily disabled ObservationVersioningService due to duplicate model issue
        # This endpoint is not currently used - observation versions are handled directly in ObservationRecord
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Observation versioning endpoint is temporarily disabled. Use observation management endpoints instead."
        )
        
        return {
            "version_id": str(version.version_id),
            "version_number": version.version_number,
            "version_status": version.version_status,
            "approval_status": version.approval_status,
            "total_observations": version.total_observations
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating observation version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create observation version: {str(e)}"
        )


# Observation Group Management Endpoints
@router.post("/observation-groups/{group_id}/submit-for-approval")
@require_permission("observations", "update")
async def submit_observation_group_for_approval(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit observation group for approval"""
    # For now, return success - actual implementation would update observation statuses
    return {"message": f"Observation group {group_id} submitted for approval"}


@router.post("/observation-groups/{group_id}/approve")
@require_permission("observations", "approve")
async def approve_observation_group(
    group_id: int,
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or decline observation group"""
    import logging
    logger = logging.getLogger(__name__)
    
    approved = request_data.get("approved", False)
    comments = request_data.get("comments", "")
    
    try:
        from sqlalchemy import select, update
        from app.models.observation_management import ObservationRecord
        from datetime import datetime
        
        # First, get the observations that belong to this group
        # In the frontend, group_id is actually an observation_id from one of the grouped observations
        obs_result = await db.execute(
            select(ObservationRecord).where(
                ObservationRecord.observation_id == group_id
            )
        )
        observation = obs_result.scalar_one_or_none()
        
        if not observation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Observation {group_id} not found"
            )
        
        # Get all observations in the same group (same attribute and type)
        grouped_obs_result = await db.execute(
            select(ObservationRecord).where(
                and_(
                    ObservationRecord.cycle_id == observation.cycle_id,
                    ObservationRecord.report_id == observation.report_id,
                    ObservationRecord.source_attribute_id == observation.source_attribute_id,
                    ObservationRecord.observation_type == observation.observation_type
                )
            )
        )
        grouped_observations = grouped_obs_result.scalars().all()
        
        # Update approval fields directly in observation records
        decision = "Approved" if approved else "Rejected"
        
        for obs in grouped_observations:
            # Update tester decision fields
            obs.tester_decision = decision
            obs.tester_comments = comments
            obs.tester_decision_by_id = current_user.user_id
            obs.tester_decision_at = datetime.utcnow()
            
            # Update overall approval status
            obs.approval_status = f"{decision} by Tester"
            
            # Update audit fields
            obs.updated_at = datetime.utcnow()
            obs.updated_by_id = current_user.user_id
            
            db.add(obs)
        
        await db.commit()
        
        logger.info(f"Updated {len(grouped_observations)} observations with tester decision: {decision}")
        
        status_text = "approved" if approved else "rejected"
        return {
            "message": f"Observation group {status_text} successfully",
            "comments": comments,
            "observations_updated": len(grouped_observations),
            "approval_status": f"{decision} by Tester"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve/reject observation group: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update observation group: {str(e)}"
        )


@router.put("/observation-groups/{group_id}/rating")
@require_permission("observations", "update") 
async def update_observation_group_rating(
    group_id: int,
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update observation group rating"""
    rating = request_data.get("rating", "Medium")
    
    # For now, return success - actual implementation would update observations
    return {"message": f"Observation group {group_id} rating updated to {rating}"}


@router.post("/observation-groups/{group_id}/finalize")
@require_permission("observations", "approve")
async def finalize_observation_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finalize observation group"""
    # For now, return success - actual implementation would finalize observations
    return {"message": f"Observation group {group_id} finalized"}


# Add observation-groups endpoint for frontend compatibility
@router.get("/{cycle_id}/reports/{report_id}/observation-groups")
@require_permission("observations", "read")
async def get_observation_groups(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observations grouped by attribute and issue type for frontend compatibility"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from sqlalchemy import select, and_, func
        from app.models.observation_management import ObservationRecord
        from app.models.workflow import WorkflowPhase
        from app.models.report_attribute import ReportAttribute
        from collections import defaultdict
        import json
        
        # Get the observation management phase
        phase_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Observations"
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            logger.info(f"No Observations phase found for cycle {cycle_id}, report {report_id}")
            return []
        
        # Get observations for this phase with attribute info
        from sqlalchemy.orm import selectinload, joinedload
        result = await db.execute(
            select(ObservationRecord)
            .options(selectinload(ObservationRecord.phase))
            .where(
                ObservationRecord.phase_id == phase.phase_id
            )
            .order_by(ObservationRecord.created_at)
        )
        observations = result.scalars().all()
        
        logger.info(f"Found {len(observations)} observations for phase {phase.phase_id}")
        
        # Get attribute names
        attribute_ids = {obs.source_attribute_id for obs in observations if obs.source_attribute_id}
        attribute_names = {}
        if attribute_ids:
            attr_result = await db.execute(
                select(ReportAttribute.id, ReportAttribute.attribute_name)
                .where(ReportAttribute.id.in_(attribute_ids))
            )
            attribute_names = {row[0]: row[1] for row in attr_result}
        
        # Group observations by attribute_id and issue_type
        groups = defaultdict(list)
        for obs in observations:
            key = (
                obs.source_attribute_id, 
                obs.observation_type.value if obs.observation_type else "General"
            )
            groups[key].append(obs)
        
        # Convert groups to the expected format
        grouped = []
        group_id = 1
        
        for (attribute_id, issue_type), obs_list in groups.items():
            # Calculate statistics from grouped observations
            total_test_cases = 0
            for obs in obs_list:
                # Get grouped_count from supporting_data JSON field
                grouped_count = 1
                if obs.supporting_data:
                    if isinstance(obs.supporting_data, dict):
                        grouped_count = obs.supporting_data.get('grouped_count', 1)
                    elif isinstance(obs.supporting_data, str):
                        try:
                            data = json.loads(obs.supporting_data)
                            grouped_count = data.get('grouped_count', 1) if isinstance(data, dict) else 1
                        except:
                            grouped_count = 1
                total_test_cases += grouped_count
            
            # Extract unique sample IDs from supporting_data and test executions
            unique_samples = set()
            test_execution_ids = []
            
            for obs in obs_list:
                if obs.source_sample_record_id:
                    unique_samples.add(obs.source_sample_record_id)
                
                # Collect test execution IDs from the observation itself
                if obs.source_test_execution_id:
                    test_execution_ids.append(obs.source_test_execution_id)
                
                # Also check supporting_data for linked test executions
                if obs.supporting_data:
                    try:
                        data = json.loads(obs.supporting_data) if isinstance(obs.supporting_data, str) else obs.supporting_data
                        if isinstance(data, dict) and 'linked_test_executions' in data:
                            # Add linked test execution IDs
                            linked_ids = data.get('linked_test_executions', [])
                            if isinstance(linked_ids, list):
                                test_execution_ids.extend(linked_ids)
                    except:
                        pass
            
            # Query test executions to get sample IDs from analysis_results
            if test_execution_ids:
                from app.models.test_execution import TestExecution
                # Convert string IDs to integers
                int_test_execution_ids = []
                for exec_id in test_execution_ids:
                    try:
                        int_test_execution_ids.append(int(exec_id))
                    except (ValueError, TypeError):
                        continue
                
                if int_test_execution_ids:
                    # Get sample IDs from test execution analysis results
                    test_exec_result = await db.execute(
                        select(TestExecution.id, TestExecution.analysis_results)
                        .where(TestExecution.id.in_(int_test_execution_ids))
                    )
                    
                    for test_id, analysis_results in test_exec_result:
                        if analysis_results and isinstance(analysis_results, dict):
                            # Extract sample_id from analysis_results
                            sample_id = analysis_results.get('sample_id') or analysis_results.get('sample_record_id')
                            if sample_id:
                                unique_samples.add(str(sample_id))
                            
                            # Also check for sample_primary_key_values which might contain sample_id
                            if 'sample_primary_key_values' in analysis_results:
                                pk_values = analysis_results['sample_primary_key_values']
                                if isinstance(pk_values, dict) and 'sample_id' in pk_values:
                                    unique_samples.add(str(pk_values['sample_id']))
            
            # Determine overall approval status based on observation fields
            tester_decisions = [obs.tester_decision for obs in obs_list if obs.tester_decision]
            report_owner_decisions = [obs.report_owner_decision for obs in obs_list if obs.report_owner_decision]
            
            # Check tester decisions
            if len(tester_decisions) == len(obs_list):
                # All observations have tester decisions
                if all(d == "Approved" for d in tester_decisions):
                    # Check report owner decisions
                    if len(report_owner_decisions) == len(obs_list):
                        if all(d == "Approved" for d in report_owner_decisions):
                            approval_status = "Fully Approved"
                        elif any(d == "Rejected" for d in report_owner_decisions):
                            approval_status = "Rejected by Report Owner"
                        else:
                            approval_status = "Pending Report Owner Review"
                    else:
                        approval_status = "Approved by Tester"
                elif any(d == "Rejected" for d in tester_decisions):
                    approval_status = "Rejected by Tester"
                else:
                    approval_status = "Pending Review"
            elif len(tester_decisions) > 0:
                # Some observations have tester decisions
                approval_status = "Partially Reviewed"
            else:
                # No tester decisions yet
                approval_status = "Pending Review"
            
            # Get the highest severity rating
            severities = [obs.severity.value for obs in obs_list if obs.severity]
            rating = "HIGH" if "HIGH" in severities else "MEDIUM" if "MEDIUM" in severities else "LOW"
            
            # Create the group
            group = {
                "group_id": group_id,
                "attribute_id": attribute_id,
                "attribute_name": attribute_names.get(attribute_id, f"Attribute {attribute_id}") if attribute_id else "General",
                "issue_type": issue_type,
                "issue_summary": f"{len(obs_list)} observation(s) for {issue_type}",
                "total_test_cases": total_test_cases,
                "total_samples": len(unique_samples),  # Use actual unique sample count
                "rating": rating,
                "approval_status": approval_status,
                "report_owner_approved": any(obs.status and obs.status.value == "APPROVED" for obs in obs_list),
                "data_executive_approved": False,  # Would need additional logic
                "finalized": approval_status == "Finalized",
                "observations": [
                    {
                        "observation_id": obs.observation_id,
                        "test_case_id": str(obs.source_test_execution_id) if obs.source_test_execution_id else None,
                        "sample_id": obs.source_sample_record_id,
                        "description": obs.observation_description,
                        "test_execution_id": str(obs.source_test_execution_id) if obs.source_test_execution_id else None,
                        "linked_test_executions": (
                            obs.supporting_data.get('linked_test_executions', [])
                            if obs.supporting_data and isinstance(obs.supporting_data, dict)
                            else []
                        ),
                        "evidence_files": obs.evidence_documents if obs.evidence_documents else [],
                        "created_at": obs.created_at.isoformat() if obs.created_at else None
                    }
                    for obs in obs_list
                ]
            }
            
            grouped.append(group)
            group_id += 1
        
        # Sort by attribute name and issue type
        grouped.sort(key=lambda x: (x['attribute_name'], x['issue_type']))
        
        logger.info(f"Created {len(grouped)} observation groups from {len(observations)} observations")
        
        return grouped
        
    except Exception as e:
        logger.error(f"Error in get_observation_groups: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observation groups: {str(e)}"
        )


# Delete observation endpoint
@router.delete("/observations/{observation_id}")
@require_permission("observations", "delete")
async def delete_observation(
    observation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an observation"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from sqlalchemy import select, delete
        from app.models.observation_management import ObservationRecord
        
        # Check if observation exists
        obs_result = await db.execute(
            select(ObservationRecord).where(
                ObservationRecord.observation_id == observation_id
            )
        )
        observation = obs_result.scalar_one_or_none()
        
        if not observation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation not found"
            )
        
        # Check if observation is already finalized/resolved
        if observation.status and observation.status.value in ['RESOLVED', 'APPROVED']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete finalized or approved observations"
            )
        
        # Delete the observation
        await db.execute(
            delete(ObservationRecord).where(
                ObservationRecord.observation_id == observation_id
            )
        )
        
        await db.commit()
        
        logger.info(f"Observation {observation_id} deleted by user {current_user.user_id}")
        
        return {"message": f"Observation {observation_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting observation {observation_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete observation: {str(e)}"
        )


# Create observation from test result endpoint
@router.post("/{cycle_id}/reports/{report_id}/observations/from-test-result")
@require_permission("observations", "create")
async def create_observation_from_test_result(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create observation from test execution result"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Extract data from request
        test_execution_id = request_data.get("test_execution_id")
        observation_type = request_data.get("observation_type", "DATA_QUALITY")
        severity = request_data.get("severity", "MEDIUM")
        title = request_data.get("title")
        description = request_data.get("description")
        
        if not test_execution_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="test_execution_id is required"
            )
        
        # Get test execution details
        from sqlalchemy import select
        from app.models.test_execution import TestExecution
        
        result = await db.execute(
            select(TestExecution).where(
                TestExecution.id == int(test_execution_id)
            )
        )
        test_execution = result.scalar_one_or_none()
        
        if not test_execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test execution {test_execution_id} not found"
            )
            
        # Get test case details for attribute info
        from app.models.request_info import CycleReportTestCase
        tc_result = await db.execute(
            select(CycleReportTestCase).where(
                CycleReportTestCase.id == int(test_execution.test_case_id)
            )
        )
        test_case = tc_result.scalar_one_or_none()
        
        if not test_case:
            logger.warning(f"Test case {test_execution.test_case_id} not found")
            
        # Create observation using the standard endpoint logic
        observation_data = ObservationCreateDTO(
            observation_title=title or f"{observation_type} - {test_case.attribute_name if test_case else 'Unknown Attribute'}",
            observation_description=description or f"Test case failed: {test_execution.processing_notes or 'No details available'}",
            observation_type=observation_type,
            severity=severity,
            source_attribute_id=test_case.attribute_id if test_case else None,
            source_sample_id=str(test_case.sample_id) if test_case else None,
            test_execution_id=str(test_execution.id),
            evidence_urls=[],
            suggested_action=None
        )
        
        # Use the existing use case
        use_case = CreateObservationUseCase()
        observation = await use_case.execute(
            cycle_id, report_id, observation_data, current_user.user_id, db
        )
        
        # Check if this was grouped with an existing observation
        is_grouped = observation.grouped_count > 1
        if is_grouped:
            logger.info(f"Test result linked to existing observation: {observation.observation_id} (now covers {observation.grouped_count} test failures)")
            message = f"Test case linked to existing observation. This observation now covers {observation.grouped_count} test failures."
        else:
            logger.info(f"Created new observation from test result: {observation.observation_id}")
            message = "New observation created successfully from test result"
        
        return {
            "observation_id": observation.observation_id,
            "observation_number": observation.observation_number,
            "grouped_count": observation.grouped_count,
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create observation from test result: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create observation: {str(e)}"
        )


# Phase Management Endpoints
@router.post("/{cycle_id}/reports/{report_id}/start", response_model=ObservationPhaseStatusDTO)
@require_permission("observations", "create")
async def start_observation_phase(
    cycle_id: int,
    report_id: int,
    start_data: ObservationPhaseStartDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start observation management phase"""
    try:
        # Get current status (this will create phase if it doesn't exist)
        use_case = GetObservationPhaseStatusUseCase()
        status = await use_case.execute(cycle_id, report_id, db)
        
        if status.phase_status != "Not Started":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Observation phase has already been started"
            )
        
        # Phase is automatically created when first observation is added
        # Return current status
        return status
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start observation phase: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/status", response_model=ObservationPhaseStatusDTO)
@require_permission("observations", "read")
async def get_observation_phase_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observation management phase status"""
    try:
        use_case = GetObservationPhaseStatusUseCase()
        return await use_case.execute(cycle_id, report_id, db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get phase status: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/complete")
@require_permission("observations", "execute")
async def complete_observation_phase(
    cycle_id: int,
    report_id: int,
    completion_data: ObservationPhaseCompleteDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete observation management phase"""
    try:
        use_case = CompleteObservationPhaseUseCase()
        result = await use_case.execute(
            cycle_id, report_id, completion_data, current_user.user_id, db
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete phase: {str(e)}"
        )


# Observation CRUD Endpoints
@router.post("/{cycle_id}/reports/{report_id}/observations", response_model=ObservationResponseDTO)
@require_permission("observations", "create")
async def create_observation(
    cycle_id: int,
    report_id: int,
    observation_data: ObservationCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new observation with intelligent grouping"""
    try:
        use_case = CreateObservationUseCase()
        observation = await use_case.execute(
            cycle_id, report_id, observation_data, current_user.user_id, db
        )
        # Log the type of observation being returned
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Observation type: {type(observation)}, Value: {observation}")
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create observation: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/observations", response_model=List[ObservationResponseDTO])
@require_permission("observations", "read")
async def list_observations(
    cycle_id: int,
    report_id: int,
    status: Optional[ObservationStatusEnum] = None,
    severity: Optional[ObservationSeverityEnum] = None,
    observation_type: Optional[ObservationTypeEnum] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List observations with optional filters"""
    try:
        use_case = ListObservationsUseCase()
        observations = await use_case.execute(
            cycle_id, report_id, status, severity, observation_type, db
        )
        return observations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list observations: {str(e)}"
        )


@router.get("/observations/{observation_id}", response_model=ObservationResponseDTO)
@require_permission("observations", "read")
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observation details"""
    try:
        use_case = GetObservationUseCase()
        observation = await use_case.execute(observation_id, db)
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get observation: {str(e)}"
        )


@router.put("/observations/{observation_id}", response_model=ObservationResponseDTO)
@require_permission("observations", "update")
async def update_observation(
    observation_id: str,
    update_data: ObservationUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update observation details"""
    try:
        use_case = UpdateObservationUseCase()
        observation = await use_case.execute(
            observation_id, update_data, current_user.user_id, db
        )
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update observation: {str(e)}"
        )


@router.post("/observations/{observation_id}/submit", response_model=ObservationResponseDTO)
@require_permission("observations", "update")
async def submit_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit observation for review"""
    try:
        use_case = SubmitObservationUseCase()
        observation = await use_case.execute(
            observation_id, current_user.user_id, db
        )
        return observation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit observation: {str(e)}"
        )


# Review and Approval Endpoints
@router.post("/observations/{observation_id}/review", response_model=ObservationApprovalResponseDTO)
@require_permission("observations", "approve")
async def review_observation(
    observation_id: str,
    review_data: ObservationApprovalRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review and approve/reject observation"""
    try:
        use_case = ReviewObservationUseCase()
        approval = await use_case.execute(
            observation_id, review_data, current_user.user_id, db
        )
        return approval
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review observation: {str(e)}"
        )


@router.post("/{cycle_id}/reports/{report_id}/observations/batch-review", response_model=Dict[str, Any])
@require_permission("observations", "approve")
async def batch_review_observations(
    cycle_id: int,
    report_id: int,
    batch_request: ObservationBatchReviewRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Batch approve or reject multiple observations"""
    try:
        use_case = BatchReviewObservationsUseCase()
        result = await use_case.execute(
            cycle_id, report_id, batch_request, current_user.user_id, db
        )
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch review observations: {str(e)}"
        )


# Impact Assessment Endpoints
@router.post("/observations/{observation_id}/impact-assessment", response_model=ImpactAssessmentResponseDTO)
@require_permission("observations", "update")
async def create_impact_assessment(
    observation_id: str,
    assessment_data: ImpactAssessmentCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create impact assessment for observation"""
    try:
        use_case = CreateImpactAssessmentUseCase()
        assessment = await use_case.execute(
            observation_id, assessment_data, current_user.user_id, db
        )
        return assessment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create impact assessment: {str(e)}"
        )


# Resolution Endpoints
@router.post("/observations/{observation_id}/resolution", response_model=ResolutionResponseDTO)
@require_permission("observations", "update")
async def create_resolution(
    observation_id: str,
    resolution_data: ResolutionCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create resolution for observation"""
    try:
        use_case = CreateResolutionUseCase()
        resolution = await use_case.execute(
            observation_id, resolution_data, current_user.user_id, db
        )
        return resolution
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resolution: {str(e)}"
        )


# Analytics Endpoints
@router.get("/{cycle_id}/reports/{report_id}/analytics", response_model=ObservationAnalyticsDTO)
@require_permission("observations", "read")
async def get_observation_analytics(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observation analytics and insights"""
    try:
        use_case = GetObservationAnalyticsUseCase()
        analytics = await use_case.execute(cycle_id, report_id, db)
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


# Auto-Detection Endpoints
@router.post("/{cycle_id}/reports/{report_id}/auto-detect", response_model=Dict[str, Any])
@require_permission("observations", "create")
async def auto_detect_observations(
    cycle_id: int,
    report_id: int,
    request_data: AutoDetectionRequestDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-detect and create observations from test failures"""
    try:
        # Get phase ID
        from sqlalchemy import and_, select
        phase_query = select(WorkflowPhase.phase_id).where(and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Observation Management"
        ))
        phase_result = await db.execute(phase_query)
        phase_id = phase_result.scalar_one_or_none()
        
        if not phase_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation Management phase not found"
            )
        
        # Use background job for detection
        from app.tasks.observation_detection_tasks import check_and_create_observations_batch
        
        job_id = await check_and_create_observations_batch(
            phase_id=phase_id,
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=current_user.user_id,
            auto_create=request_data.auto_create if hasattr(request_data, 'auto_create') else True,
            batch_size=request_data.batch_size if hasattr(request_data, 'batch_size') else 100
        )
        
        return {
            "job_id": job_id,
            "message": "Observation detection started in background",
            "status_url": f"/api/v1/jobs/{job_id}/status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start observation detection: {str(e)}"
        )


# Tester-specific endpoints
@router.get("/my-observations", response_model=List[ObservationResponseDTO])
@require_permission("observations", "read")
async def get_my_observations(
    status: Optional[ObservationStatusEnum] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observations created by current user"""
    try:
        from sqlalchemy import select, and_
        from app.models import ObservationRecord
        
        query = select(ObservationRecord).where(
            ObservationRecord.created_by == current_user.user_id
        )
        
        if status:
            query = query.where(ObservationRecord.status == status)
        
        query = query.order_by(ObservationRecord.created_at.desc())
        
        result = await db.execute(query)
        observations = result.scalars().all()
        
        return [
            ObservationResponseDTO(
                observation_id=obs.observation_id,
                phase_id=obs.phase_id,
                cycle_id=obs.cycle_id,
                report_id=obs.report_id,
                observation_number=obs.observation_number,
                observation_title=obs.observation_title,
                observation_description=obs.observation_description,
                observation_type=obs.observation_type,
                severity=obs.severity,
                status=obs.status,
                source_attribute_id=obs.source_attribute_id,
                source_sample_id=obs.source_sample_record_id,
                test_execution_id=str(obs.source_test_execution_id) if obs.source_test_execution_id else None,
                grouped_count=getattr(obs, 'grouped_count', 1),
                created_by=obs.created_by,
                created_at=obs.created_at,
                updated_at=obs.updated_at,
                submitted_at=obs.submitted_at,
                reviewed_by=obs.reviewed_by,
                reviewed_at=obs.reviewed_at,
                resolution_status=obs.resolution.resolution_status if obs.resolution else None
            )
            for obs in observations
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user observations: {str(e)}"
        )


# Report Owner/Executive endpoints
@router.get("/pending-review", response_model=List[ObservationResponseDTO])
@require_permission("observations", "approve")
async def get_pending_review_observations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get observations pending review for current user's reports"""
    try:
        from sqlalchemy import select, and_, or_
        from app.models import ObservationRecord, Report, ReportOwner
        
        # Get reports owned by current user
        if current_user.role in ['Report Owner', 'Report Owner Executive']:
            # Get observations for owned reports
            query = select(ObservationRecord).join(
                Report, ObservationRecord.report_id == Report.report_id
            ).join(
                ReportOwner, Report.report_id == ReportOwner.report_id
            ).where(and_(
                ReportOwner.owner_id == current_user.user_id,
                ObservationRecord.status.in_([
                    ObservationStatusEnum.SUBMITTED,
                    ObservationStatusEnum.UNDER_REVIEW
                ])
            ))
        else:
            # Admin can see all pending
            query = select(ObservationRecord).where(
                ObservationRecord.status.in_([
                    ObservationStatusEnum.SUBMITTED,
                    ObservationStatusEnum.UNDER_REVIEW
                ])
            )
        
        query = query.order_by(
            ObservationRecord.severity.desc(),
            ObservationRecord.submitted_at
        )
        
        result = await db.execute(query)
        observations = result.scalars().all()
        
        return [
            ObservationResponseDTO(
                observation_id=obs.observation_id,
                phase_id=obs.phase_id,
                cycle_id=obs.cycle_id,
                report_id=obs.report_id,
                observation_number=obs.observation_number,
                observation_title=obs.observation_title,
                observation_description=obs.observation_description,
                observation_type=obs.observation_type,
                severity=obs.severity,
                status=obs.status,
                source_attribute_id=obs.source_attribute_id,
                source_sample_id=obs.source_sample_record_id,
                test_execution_id=str(obs.source_test_execution_id) if obs.source_test_execution_id else None,
                grouped_count=getattr(obs, 'grouped_count', 1),
                created_by=obs.created_by,
                created_at=obs.created_at,
                updated_at=obs.updated_at,
                submitted_at=obs.submitted_at,
                reviewed_by=obs.reviewed_by,
                reviewed_at=obs.reviewed_at,
                resolution_status=obs.resolution.resolution_status if obs.resolution else None
            )
            for obs in observations
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending review observations: {str(e)}"
        )