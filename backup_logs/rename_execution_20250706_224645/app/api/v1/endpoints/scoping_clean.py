"""
Scoping phase endpoints using clean architecture
Simplified version focusing on core functionality
"""

from typing import List, Dict, Any
from datetime import datetime
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, exists

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth import UserRoles, RoleChecker
from app.core.logging import get_logger
from app.core.exceptions import ValidationException, NotFoundException, BusinessLogicException
from app.core.background_jobs import job_manager, JobProgress
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.services.llm_service import get_llm_service
from app.services.workflow_orchestrator import get_workflow_orchestrator

logger = get_logger(__name__)
router = APIRouter()

# Role-based access control
tester_roles = [UserRoles.TESTER]
report_owner_roles = [UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE]
management_roles = [UserRoles.TEST_EXECUTIVE, UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.ADMIN]


@router.post("/cycles/{cycle_id}/reports/{report_id}/start")
async def start_scoping_phase(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Start scoping phase for a report"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Verify planning phase is complete
    planning_phase = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
    )
    planning = planning_phase.scalar_one_or_none()
    
    if not planning or planning.status != "Complete":
        raise BusinessLogicException("Planning phase must be completed before starting scoping")
    
    # Check if scoping phase already exists
    scoping_phase = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Scoping"
            )
        )
    )
    existing_scoping = scoping_phase.scalar_one_or_none()
    
    if existing_scoping:
        if existing_scoping.status == "Complete":
            raise BusinessLogicException("Scoping phase already completed")
        elif existing_scoping.status == "In Progress":
            return {"message": "Scoping phase already in progress"}
        else:
            # Update the existing phase from "Not Started" to "In Progress"
            existing_scoping.status = "In Progress"
            existing_scoping.state = "In Progress"
            existing_scoping.actual_start_date = datetime.utcnow()
            existing_scoping.started_by = current_user.user_id
            await db.commit()
            return {
                "message": "Scoping phase started successfully",
                "phase": "Scoping",
                "status": "In Progress"
            }
    
    # Create scoping phase if it doesn't exist
    new_phase = WorkflowPhase(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name="Scoping",
        status="In Progress",
        state="In Progress",
        actual_start_date=datetime.utcnow(),
        started_by=current_user.user_id
    )
    db.add(new_phase)
    await db.commit()
    
    return {
        "message": "Scoping phase started successfully",
        "phase": "Scoping",
        "status": "In Progress"
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/status")
async def get_scoping_status(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get scoping phase status"""
    # Get workflow phase
    workflow_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        )
    )
    
    workflow_phase_result = await db.execute(workflow_phase_query)
    workflow_phase = workflow_phase_result.scalar_one_or_none()
    
    if not workflow_phase:
        # Return a default "Not Started" status instead of throwing an error
        return {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "phase_status": "Not Started",
            "total_attributes": 0,
            "attributes_with_recommendations": 0,
            "attributes_with_decisions": 0,
            "attributes_scoped_for_testing": 0,
            "submission_status": None,
            "approval_status": None,
            "can_generate_recommendations": False,
            "started_at": None,
            "completed_at": None,
            "selected_attributes_count": 0,
            "total_approved_attributes_count": 0,
            "pk_attributes_count": 0,
            "cde_attributes_count": 0,
            "historical_issues_count": 0,
            "attributes_with_anomalies": 0,
            "can_complete": False,
            "completion_requirements": ["Phase not started"],
            "can_submit_for_approval": False
        }
    
    # Get all attributes
    attr_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.is_active == True
        )
    )
    attr_result = await db.execute(attr_query)
    attributes = attr_result.scalars().all()
    
    total_attributes = len(attributes)
    # Count attributes that have LLM recommendations (any of the LLM fields populated)
    attributes_with_recommendations = sum(1 for a in attributes if 
        a.llm_rationale is not None or 
        a.llm_risk_rationale is not None or 
        a.typical_source_documents is not None or
        a.keywords_to_look_for is not None or
        a.testing_approach is not None)
    attributes_with_decisions = sum(1 for a in attributes if a.is_scoped is not None)
    attributes_scoped_for_testing = sum(1 for a in attributes if a.is_scoped == True)
    pk_attributes_count = sum(1 for a in attributes if a.is_primary_key == True)
    cde_attributes_count = sum(1 for a in attributes if a.cde_flag == True)
    historical_issues_count = sum(1 for a in attributes if a.historical_issues_flag == True)
    # Count attributes with actual anomalies from data profiling results
    attributes_with_anomalies = 0
    try:
        # Get data profiling phase to check for actual anomalies
        from app.models.data_profiling import DataProfilingPhase, ProfilingResult
        
        profiling_phase_query = select(DataProfilingPhase).where(
            and_(
                DataProfilingPhase.cycle_id == cycle_id,
                DataProfilingPhase.report_id == report_id
            )
        )
        profiling_phase_result = await db.execute(profiling_phase_query)
        profiling_phase = profiling_phase_result.scalar_one_or_none()
        
        if profiling_phase:
            # Count attributes that have anomalies detected in profiling results
            anomaly_query = select(func.count(func.distinct(ProfilingResult.attribute_id))).where(
                and_(
                    ProfilingResult.phase_id == profiling_phase.phase_id,
                    ProfilingResult.has_anomaly == True
                )
            )
            anomaly_result = await db.execute(anomaly_query)
            attributes_with_anomalies = anomaly_result.scalar() or 0
        else:
            # No data profiling phase yet, so no anomalies detected
            attributes_with_anomalies = 0
            
    except Exception as e:
        logger.warning(f"Error counting anomalies: {str(e)}")
        # Fallback to 0 if there's an error
        attributes_with_anomalies = 0
    
    # Get latest scoping submission
    from app.models.scoping import ScopingSubmission, ReportOwnerScopingReview
    
    submission_query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.version.desc())
    submission_result = await db.execute(submission_query)
    latest_submission = submission_result.scalars().first()
    
    # Get review if submission exists
    review = None
    if latest_submission:
        review_query = select(ReportOwnerScopingReview).where(
            ReportOwnerScopingReview.submission_id == latest_submission.submission_id
        ).order_by(ReportOwnerScopingReview.created_at.desc())
        review_result = await db.execute(review_query)
        review = review_result.scalars().first()
    
    # Determine actual status based on real data
    submission_status = "Submitted" if latest_submission else None
    approval_status = None
    needs_revision = False
    
    if review:
        if review.approval_status == "Approved":
            approval_status = "Approved"
        elif review.approval_status == "Declined":
            approval_status = "Declined"
        elif review.approval_status == "Needs Revision":
            approval_status = "Needs Revision"
            needs_revision = True
    
    # Check if can generate recommendations
    can_generate_recommendations = workflow_phase.status == "In Progress" and total_attributes > 0
    
    # Can complete phase
    can_complete = attributes_scoped_for_testing > 0 and workflow_phase.status == "In Progress"
    completion_requirements = []
    if attributes_scoped_for_testing == 0:
        completion_requirements.append("At least one attribute must be scoped for testing")
    
    return {
        "cycle_id": cycle_id,
        "report_id": report_id,
        "phase_status": workflow_phase.status,
        "total_attributes": total_attributes,
        "attributes_with_recommendations": attributes_with_recommendations,
        "attributes_with_decisions": attributes_with_decisions,
        "attributes_scoped_for_testing": attributes_scoped_for_testing,
        "submission_status": submission_status,
        "approval_status": approval_status,
        "can_generate_recommendations": can_generate_recommendations,
        "started_at": workflow_phase.actual_start_date,
        "completed_at": workflow_phase.actual_end_date,
        "selected_attributes_count": attributes_scoped_for_testing,
        "total_approved_attributes_count": total_attributes,
        "pk_attributes_count": pk_attributes_count,
        "cde_attributes_count": cde_attributes_count,
        "historical_issues_count": historical_issues_count,
        "attributes_with_anomalies": attributes_with_anomalies,
        "can_complete": can_complete,
        "completion_requirements": completion_requirements,
        "can_submit_for_approval": attributes_with_decisions > 0,
        # New fields for proper state management
        "has_submission": latest_submission is not None,
        "has_review": review is not None,
        "current_version": latest_submission.version if latest_submission else 0,
        "review_decision": review.approval_status if review else None,
        "needs_revision": needs_revision,
        "review_comments": review.review_comments if review else None
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/generate-attributes")
async def generate_test_attributes(
    cycle_id: int,
    report_id: int,
    sample_size: int = 25,
    preferred_provider: str = "claude",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Generate test attributes using LLM"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    # Get attributes from planning phase
    attributes_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.is_active == True
        )
    )
    
    attributes_result = await db.execute(attributes_query)
    attributes = attributes_result.scalars().all()
    
    if not attributes:
        raise BusinessLogicException("No attributes found. Complete planning phase first.")
    
    # Get report info
    report_query = select(Report).join(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id
        )
    )
    
    report_result = await db.execute(report_query)
    report = report_result.scalar_one_or_none()
    
    if not report:
        raise NotFoundException("Report not found")
    
    # Get LLM service
    llm_service = get_llm_service()
    
    # Generate recommendations for each attribute
    recommendations = []
    
    for attribute in attributes:
        try:
            # Call LLM to get recommendations
            llm_result = await llm_service.generate_scoping_recommendations(
                attribute_name=attribute.attribute_name,
                attribute_description=attribute.description,
                data_type=attribute.data_type,
                report_type=report.report_type,
                regulatory_context=report.regulation_name,
                is_key=attribute.is_primary_key,
                preferred_provider=preferred_provider
            )
            
            recommendations.append({
                "attribute_id": attribute.attribute_id,
                "attribute_name": attribute.attribute_name,
                "include": llm_result.get("include", True),
                "risk_score": llm_result.get("risk_score", 0.5),
                "criticality": llm_result.get("criticality", "Medium"),
                "test_approach": llm_result.get("test_approach", "Standard validation"),
                "sample_size": llm_result.get("sample_size", sample_size),
                "rationale": llm_result.get("rationale", "")
            })
            
        except Exception as e:
            logger.error(f"Failed to generate recommendation for attribute {attribute.attribute_name}: {e}")
            # Continue with other attributes
    
    return {
        "message": f"Generated {len(recommendations)} recommendations",
        "total_attributes": len(attributes),
        "recommendations": recommendations
    }


@router.put("/cycles/{cycle_id}/reports/{report_id}/review-attributes")
async def review_attributes(
    cycle_id: int,
    report_id: int,
    attribute_updates: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Review and update test attributes"""
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
    updated_count = 0
    
    for update in attribute_updates:
        attr_id = update.get("attribute_id")
        if not attr_id:
            continue
            
        # Get attribute
        attr_query = select(ReportAttribute).where(
            and_(
                ReportAttribute.attribute_id == attr_id,
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        )
        
        attr_result = await db.execute(attr_query)
        attribute = attr_result.scalar_one_or_none()
        
        if attribute:
            # Update scoping-related fields
            if "include_in_testing" in update:
                attribute.is_scoped = update["include_in_testing"]
            if "test_approach" in update:
                attribute.testing_approach = update["test_approach"]
            if "sample_size" in update:
                # sample_size field doesn't exist, store in tester_notes for now
                if attribute.tester_notes:
                    attribute.tester_notes = f"{attribute.tester_notes}\nSample size: {update['sample_size']}"
                else:
                    attribute.tester_notes = f"Sample size: {update['sample_size']}"
            if "risk_score" in update:
                attribute.risk_score = update["risk_score"]
            
            attribute.updated_at = datetime.utcnow()
            updated_count += 1
    
    await db.commit()
    
    return {
        "message": f"Updated {updated_count} attributes",
        "updated_count": updated_count
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/approve-attributes")
async def approve_attributes(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Approve attributes and complete scoping phase"""
    # Check permissions - report owner or management
    RoleChecker(report_owner_roles + management_roles)(current_user)
    
    # Get workflow orchestrator
    orchestrator = await get_workflow_orchestrator(db)
    
    # Update phase state to Complete
    phase = await orchestrator.update_phase_state(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name="Scoping",
        new_state="Complete",
        notes=f"Attributes approved by {current_user.email}",
        user_id=current_user.user_id
    )
    
    # Also update the status field to Complete
    from sqlalchemy import update
    from app.models.workflow import WorkflowPhase
    
    await db.execute(
        update(WorkflowPhase)
        .where(WorkflowPhase.phase_id == phase.phase_id)
        .values(status="Complete")
    )
    await db.commit()
    
    return {
        "message": "Attributes approved. Scoping phase completed.",
        "next_phases": ["Sample Selection", "Data Owner Identification"]
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/complete")
async def complete_scoping_phase(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Complete scoping phase"""
    # Check permissions
    RoleChecker(tester_roles + management_roles)(current_user)
    
    # Get workflow orchestrator
    orchestrator = await get_workflow_orchestrator(db)
    
    # Update phase state to Complete
    phase = await orchestrator.update_phase_state(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name="Scoping",
        new_state="Complete",
        notes="Scoping phase completed",
        user_id=current_user.user_id
    )
    
    # Also update the status field to Complete
    from sqlalchemy import update
    from app.models.workflow import WorkflowPhase
    
    await db.execute(
        update(WorkflowPhase)
        .where(WorkflowPhase.phase_id == phase.phase_id)
        .values(status="Complete")
    )
    await db.commit()
    
    return {
        "message": "Scoping phase completed",
        "next_phases": ["Sample Selection", "Data Provider ID"]
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/attributes")
async def get_scoped_attributes(
    cycle_id: int,
    report_id: int,
    include_excluded: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """Get all attributes with scoping decisions and composite DQ scores"""
    # Build query
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.is_active == True
        )
    )
    
    if not include_excluded:
        query = query.where(ReportAttribute.is_scoped == True)
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    # Debug logging
    if attributes:
        logger.info(f"First attribute data: id={attributes[0].attribute_id}, "
                   f"name={attributes[0].attribute_name}, "
                   f"approval_status={attributes[0].approval_status}, "
                   f"is_scoped={attributes[0].is_scoped}")
    
    # Calculate composite DQ scores for all attributes
    from app.services.data_quality_service import DataQualityService
    
    attribute_ids = [attr.attribute_id for attr in attributes]
    logger.info(f"Calculating DQ scores for {len(attribute_ids)} attributes")
    
    try:
        dq_scores = await DataQualityService.calculate_dq_scores_for_all_attributes(
            db, cycle_id, report_id, attribute_ids
        )
        logger.info(f"Successfully calculated DQ scores for {len(dq_scores)} attributes")
    except Exception as e:
        logger.error(f"Error calculating DQ scores: {str(e)}")
        # Fallback to empty scores if calculation fails
        dq_scores = {attr_id: {
            "overall_quality_score": 0.0,
            "total_rules_executed": 0,
            "rules_passed": 0,
            "rules_failed": 0,
            "has_profiling_data": False
        } for attr_id in attribute_ids}
    
    return [
        {
            "attribute_id": attr.attribute_id,
            "attribute_name": attr.attribute_name,
            "data_type": attr.data_type,
            "is_key": attr.is_primary_key,
            "is_primary_key": attr.is_primary_key,
            "description": attr.description,
            "include_in_testing": attr.is_scoped,
            "is_scoped": attr.is_scoped,  # Add this field
            "approval_status": attr.approval_status,  # Add this field
            "test_approach": attr.testing_approach,
            "sample_size": None,  # This field doesn't exist in the model
            "risk_score": attr.risk_score,
            "llm_risk_score": attr.risk_score,  # Frontend expects this field name
            "llm_rationale": attr.llm_rationale,
            "llm_risk_rationale": attr.llm_risk_rationale,
            "llm_generated": attr.llm_generated,
            "cde_flag": attr.cde_flag,
            "historical_issues_flag": attr.historical_issues_flag,
            "mandatory_flag": attr.mandatory_flag,
            "line_item_number": attr.line_item_number,
            "mdrm": attr.mdrm,
            "typical_source_documents": attr.typical_source_documents,
            "keywords_to_look_for": attr.keywords_to_look_for,
            "tester_notes": attr.tester_notes,
            # Add composite DQ score fields
            "composite_dq_score": dq_scores.get(attr.attribute_id, {}).get("overall_quality_score", 0.0),
            "dq_rules_count": dq_scores.get(attr.attribute_id, {}).get("total_rules_executed", 0),
            "dq_rules_passed": dq_scores.get(attr.attribute_id, {}).get("rules_passed", 0),
            "dq_rules_failed": dq_scores.get(attr.attribute_id, {}).get("rules_failed", 0),
            "has_profiling_data": dq_scores.get(attr.attribute_id, {}).get("has_profiling_data", False)
        }
        for attr in attributes
    ]


@router.get("/cycles/{cycle_id}/reports/{report_id}/decisions")
async def get_scoping_decisions(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list:
    """Get scoping decisions for attributes - only for the latest submission version"""
    from sqlalchemy import text
    
    # First, get the latest submission version
    version_query = text("""
        SELECT MAX(version) as latest_version
        FROM cycle_report_scoping_submissions
        WHERE cycle_id = :cycle_id AND report_id = :report_id
    """)
    
    version_result = await db.execute(version_query, {
        "cycle_id": cycle_id,
        "report_id": report_id
    })
    
    latest_version = version_result.scalar()
    if not latest_version:
        return []  # No submissions yet
    
    # Get tester scoping decisions only for the latest version
    # Use a window function to get the most recent decision for each attribute
    query = text("""
        WITH ranked_decisions AS (
            SELECT 
                tsd.attribute_id,
                ra.attribute_name,
                tsd.decision,
                tsd.final_scoping,
                tsd.tester_rationale,
                tsd.override_reason,
                ra.is_primary_key,
                tsd.created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY tsd.attribute_id 
                    ORDER BY tsd.created_at DESC
                ) as rn
            FROM cycle_report_scoping_tester_decisions tsd
            JOIN report_attributes ra ON 
                ra.attribute_id = tsd.attribute_id 
                AND ra.cycle_id = tsd.cycle_id 
                AND ra.report_id = tsd.report_id
            WHERE tsd.cycle_id = :cycle_id 
              AND tsd.report_id = :report_id
        )
        SELECT 
            attribute_id,
            attribute_name,
            decision,
            final_scoping,
            tester_rationale,
            override_reason,
            is_primary_key
        FROM ranked_decisions
        WHERE rn = 1
        ORDER BY attribute_name
    """)
    
    result = await db.execute(query, {
        "cycle_id": cycle_id,
        "report_id": report_id
    })
    
    rows = result.fetchall()
    
    # Build decisions response
    decisions = []
    for row in rows:
        decisions.append({
            "attribute_id": row[0],
            "attribute_name": row[1],
            "decision": row[2],
            "final_scoping": row[3],
            "tester_rationale": row[4],
            "override_reason": row[5],
            "is_primary_key": row[6]
        })
    
    return decisions


@router.get("/cycles/{cycle_id}/reports/{report_id}/feedback")
async def get_scoping_feedback(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get report owner feedback on scoping decisions"""
    from sqlalchemy import text
    
    # Get the latest submission and its review
    query = text("""
        WITH latest_submission AS (
            SELECT submission_id, version
            FROM cycle_report_scoping_submissions
            WHERE cycle_id = :cycle_id AND report_id = :report_id
            ORDER BY version DESC
            LIMIT 1
        )
        SELECT 
            rosr.review_id,
            rosr.approval_status,
            rosr.review_comments,
            rosr.requested_changes,
            rosr.reviewed_by,
            rosr.created_at,
            CONCAT(u.first_name, ' ', u.last_name) as reviewer_name,
            ls.version as submission_version
        FROM latest_submission ls
        LEFT JOIN cycle_report_scoping_report_owner_reviews rosr ON rosr.submission_id = ls.submission_id
        LEFT JOIN users u ON u.user_id = rosr.reviewed_by
    """)
    
    result = await db.execute(query, {
        "cycle_id": cycle_id,
        "report_id": report_id
    })
    
    row = result.first()
    if not row or not row[0]:  # No review found
        return {
            "feedback_id": None,
            "needs_revision": False,
            "feedback_text": None,
            "provided_by": None,
            "provided_at": None,
            "is_outdated_feedback": False,
            "can_resubmit": False,
            "submission_version": row[7] if row else None
        }
    
    # Determine if revision is needed
    needs_revision = row[1] == "Needs Revision"
    
    return {
        "feedback_id": row[0],
        "needs_revision": needs_revision,
        "feedback_text": row[2],
        "requested_changes": row[3],
        "provided_by": row[6],
        "provided_at": row[5].isoformat() if row[5] else None,
        "is_outdated_feedback": False,
        "can_resubmit": needs_revision,
        "submission_version": row[7],
        "review_decision": row[1]
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/versions")
async def get_scoping_versions(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get version history of scoping decisions"""
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            ss.submission_id,
            ss.version,
            ss.created_at as submitted_at,
            CONCAT(u.first_name, ' ', u.last_name) as submitted_by,
            ss.submission_notes,
            ss.scoped_attributes,
            ss.total_attributes,
            rosr.approval_status as review_status,
            rosr.review_comments,
            CONCAT(ru.first_name, ' ', ru.last_name) as reviewed_by
        FROM cycle_report_scoping_submissions ss
        LEFT JOIN users u ON u.user_id = ss.submitted_by
        LEFT JOIN cycle_report_scoping_report_owner_reviews rosr ON rosr.submission_id = ss.submission_id
        LEFT JOIN users ru ON ru.user_id = rosr.reviewed_by
        WHERE ss.cycle_id = :cycle_id AND ss.report_id = :report_id
        ORDER BY ss.version DESC
    """)
    
    result = await db.execute(query, {
        "cycle_id": cycle_id,
        "report_id": report_id
    })
    
    rows = result.fetchall()
    versions = []
    current_version = 0
    
    for row in rows:
        version_data = {
            "submission_id": row[0],
            "version": row[1],
            "submitted_at": row[2].isoformat() if row[2] else None,
            "submitted_by": row[3],
            "submission_notes": row[4],
            "scoped_attributes": row[5],
            "total_attributes": row[6],
            "review_status": row[7],
            "review_comments": row[8],
            "reviewed_by": row[9]
        }
        versions.append(version_data)
        if row[1] > current_version:
            current_version = row[1]
    
    return {
        "versions": versions,
        "current_version": current_version,
        "total_versions": len(versions)
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/recommendations")
async def get_scoping_recommendations(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get LLM recommendations for scoping"""
    # Get all attributes with recommendations
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.is_active == True
        )
    ).order_by(ReportAttribute.attribute_name)
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    # Build recommendations response
    recommendations = []
    for attr in attributes:
        if attr.llm_rationale:  # Has LLM recommendation
            recommendations.append({
                "attribute_id": attr.attribute_id,
                "attribute_name": attr.attribute_name,
                "recommendation": attr.llm_rationale,
                "confidence_score": getattr(attr, 'llm_confidence_score', 85),  # Default confidence
                "rationale": attr.llm_risk_rationale,
                "risk_score": attr.risk_score,
                "is_primary_key": attr.is_primary_key
            })
    
    return {
        "recommendations": recommendations,
        "total_attributes": len(attributes),
        "recommended_count": len(recommendations)
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/recommendations")
async def generate_recommendations(
    cycle_id: int,
    report_id: int,
    background_tasks: BackgroundTasks,
    request_data: dict = {},
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Generate LLM recommendations for attributes as a background job"""
    # Get all attributes to validate
    query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id,
            ReportAttribute.is_active == True
        )
    )
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    if not attributes:
        raise BusinessLogicException("No attributes found to generate recommendations for")
    
    # Get report info for context
    report_query = select(Report).join(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id
        )
    )
    
    report_result = await db.execute(report_query)
    report = report_result.scalar_one_or_none()
    
    if not report:
        raise NotFoundException("Report not found")
    
    # Create a job ID and progress tracking
    import uuid
    job_id = str(uuid.uuid4())
    
    # Initialize job progress
    job_progress = JobProgress(job_id)
    job_progress.metadata = {
        "task_type": "scoping_recommendations",
        "cycle_id": cycle_id,
        "report_id": report_id,
        "user_id": current_user.user_id,
        "attribute_count": len(attributes)
    }
    job_manager.jobs[job_id] = job_progress
    
    # Run the job asynchronously in background
    background_tasks.add_task(
        job_manager.run_job,
        job_id,
        _generate_recommendations_task,
        cycle_id, report_id, report.report_name, report.regulation or "General",
        report.regulation or "General", len(attributes),
        preferred_provider=request_data.get("preferred_provider", "claude")
    )
    
    logger.info(f"Created background job {job_id} for generating recommendations")
    
    return {
        "job_id": job_id,
        "message": "LLM recommendation generation started",
        "attributes_to_process": len(attributes)
    }


async def _generate_recommendations_task(
    job_id: str,
    cycle_id: int,
    report_id: int,
    report_name: str,
    report_regulation: str,
    regulation_name: str,
    total_attributes: int,
    preferred_provider: str = "claude"
) -> dict:
    """Background task to generate LLM recommendations"""
    from app.core.database import AsyncSessionLocal
    
    logger.info(f"Starting _generate_recommendations_task for job {job_id}")
    
    try:
        # Update job status
        logger.info(f"Updating job progress for {job_id}")
        job_manager.update_job_progress(
            job_id, 
            progress=0, 
            message="Starting LLM recommendation generation",
            current_step="Initializing"
        )
        logger.info(f"Job progress updated for {job_id}")
        
        async with AsyncSessionLocal() as db:
            # Get all attributes
            query = select(ReportAttribute).where(
                and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_active == True
                )
            )
            
            result = await db.execute(query)
            attributes = result.scalars().all()
            
            job_manager.update_job_progress(
                job_id, 
                progress=10, 
                message=f"Processing {len(attributes)} attributes",
                current_step="Loading attributes"
            )
            
            # Get LLM service
            llm_service = get_llm_service()
            
            # Process in batches
            batch_size = 10
            processed = 0
            recommendations_generated = 0
            
            for i in range(0, len(attributes), batch_size):
                batch = attributes[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(attributes) + batch_size - 1) // batch_size
                
                # Calculate proper progress percentage
                progress_pct = int(10 + (80 * batch_num / total_batches))
                job_manager.update_job_progress(
                    job_id,
                    progress=progress_pct,
                    message=f"Processing batch {batch_num} of {total_batches}",
                    current_step=f"Generating recommendations for attributes {i+1}-{min(i+batch_size, len(attributes))}",
                    metadata={
                        "completed_steps": batch_num - 1,
                        "total_steps": total_batches
                    }
                )
                
                # Prepare context for batch
                context_attributes = [
                    {
                        "name": attr.attribute_name,
                        "description": attr.description,
                        "is_primary_key": attr.is_primary_key,
                        "is_cde": attr.cde_flag,
                        "has_historical_issues": attr.historical_issues_flag,
                        "mandatory": attr.mandatory_flag,
                        "data_type": attr.data_type
                    }
                    for attr in batch
                ]
                
                try:
                    # Generate recommendations for entire batch in one LLM call
                    logger.info(f"Processing batch {batch_num} with {len(batch)} attributes")
                    
                    # Prepare batch data for LLM
                    batch_attributes = []
                    for attr in batch:
                        historical_issues = []
                        if attr.historical_issues_flag:
                            historical_issues.append(f"Historical issues reported")
                        
                        batch_attributes.append({
                            "attribute_id": attr.attribute_id,
                            "attribute_name": attr.attribute_name,
                            "data_type": attr.data_type or "String",
                            "is_primary_key": attr.is_primary_key,
                            "is_cde": attr.cde_flag,
                            "is_mandatory": attr.mandatory_flag == "Mandatory",
                            "has_historical_issues": bool(attr.historical_issues_flag),
                            "historical_issues": historical_issues
                        })
                    
                    # Call LLM with batch
                    rec_result = await llm_service.recommend_tests_batch(
                        attributes=batch_attributes,
                        regulatory_context=regulation_name,
                        report_name=report_name,
                        report_type="Credit Card",  # TODO: Get from report object
                        batch_num=batch_num,
                        total_batches=total_batches
                    )
                    
                    if rec_result.get("success") and rec_result.get("recommendations"):
                        batch_recommendations = rec_result["recommendations"]
                        logger.info(f"Received recommendations for {len(batch_recommendations)} attributes")
                        # Log first recommendation to see structure
                        if batch_recommendations:
                            logger.debug(f"Sample recommendation structure: {json.dumps(batch_recommendations[0], indent=2)}")
                        
                        # Process each attribute's recommendations
                        for attr in batch:
                            # Find recommendations for this attribute
                            attr_recs = None
                            for rec in batch_recommendations:
                                if rec.get("attribute_id") == attr.attribute_id or rec.get("attribute_name") == attr.attribute_name:
                                    attr_recs = rec
                                    break
                            
                            if attr_recs:
                                # Handle enhanced rationale structure with better formatting
                                if attr_recs.get("enhanced_rationale"):
                                    enhanced = attr_recs["enhanced_rationale"]
                                    rationale_parts = []
                                    if enhanced.get("regulatory_usage"):
                                        rationale_parts.append(f"**Regulatory Usage:** {enhanced['regulatory_usage']}")
                                    if enhanced.get("interconnections"):
                                        rationale_parts.append(f"**Interconnections:** {enhanced['interconnections']}")
                                    if enhanced.get("business_impact"):
                                        rationale_parts.append(f"**Business Impact:** {enhanced['business_impact']}")
                                    if enhanced.get("historical_issues"):
                                        rationale_parts.append(f"**Historical Issues:** {enhanced['historical_issues']}")
                                    attr.llm_rationale = "\n\n".join(rationale_parts) if rationale_parts else attr_recs.get("rationale", "Recommended for testing based on regulatory requirements")
                                else:
                                    # Fallback to simple rationale
                                    attr.llm_rationale = attr_recs.get("rationale", "Recommended for testing based on regulatory requirements")
                                
                                # Store LLM description (always update if LLM provides one)
                                if attr_recs.get("description"):
                                    attr.description = attr_recs.get("description")
                                    logger.info(f"Setting description for {attr.attribute_name}: {attr.description[:50]}...")
                                else:
                                    logger.warning(f"No description in LLM response for {attr.attribute_name}")
                                
                                # Mark as LLM generated
                                attr.llm_generated = True
                                
                                # Store MDRM code if provided
                                if attr_recs.get("mdrm_code"):
                                    attr.mdrm = attr_recs.get("mdrm_code")
                                
                                # Store data type if provided
                                if attr_recs.get("data_type"):
                                    data_type_map = {
                                        "Integer": "Integer",
                                        "Decimal": "Decimal", 
                                        "Varchar": "String",
                                        "Date": "Date",
                                        "Boolean": "Boolean",
                                        "Numeric": "Decimal"  # Handle both Numeric and Decimal
                                    }
                                    llm_data_type = attr_recs.get("data_type")
                                    if llm_data_type in data_type_map:
                                        attr.data_type = data_type_map[llm_data_type]
                                        logger.info(f"Setting data_type for {attr.attribute_name}: {attr.data_type}")
                                    else:
                                        logger.warning(f"Unknown data type from LLM for {attr.attribute_name}: {llm_data_type}")
                                else:
                                    logger.warning(f"No data_type in LLM response for {attr.attribute_name}")
                                
                                # Store additional info in tester_notes
                                notes_parts = []
                                
                                # Store risk score details if present
                                if attr_recs.get("risk_score_details"):
                                    details = attr_recs["risk_score_details"]
                                    breakdown_parts = []
                                    breakdown_parts.append(f"Regulatory: {details.get('regulatory_impact', 'N/A')}")
                                    breakdown_parts.append(f"Complexity: {details.get('data_complexity', 'N/A')}")
                                    breakdown_parts.append(f"Errors: {details.get('common_errors', 'N/A')}")
                                    breakdown_parts.append(f"Dependencies: {details.get('downstream_dependencies', 'N/A')}")
                                    breakdown_parts.append(f"CDE: {details.get('cde_criticality', 'N/A')}")
                                    breakdown_parts.append(f"Historical: {details.get('historical_issues', 'N/A')}")
                                    notes_parts.append(f"Risk Breakdown - {', '.join(breakdown_parts)}")
                                
                                # Store historical issues from enhanced rationale
                                hist_issues_text = attr_recs.get("enhanced_rationale", {}).get("historical_issues", "")
                                if hist_issues_text:
                                    notes_parts.append(f"Historical Issues: {hist_issues_text}")
                                    # Only set flag to True if historical issues were actually identified
                                    # The LLM returns "No historical issues identified" when there are none
                                    if "have been identified" in hist_issues_text and "No historical issues" not in hist_issues_text:
                                        attr.historical_issues_flag = True
                                
                                if notes_parts:
                                    combined_notes = "\n".join(notes_parts)
                                    if attr.tester_notes:
                                        attr.tester_notes = f"{combined_notes}\n{attr.tester_notes}"
                                    else:
                                        attr.tester_notes = combined_notes
                                
                                # Risk score based on attribute properties and recommendations
                                risk_score = int(attr_recs.get("risk_score", 50))
                                if attr.is_primary_key:
                                    risk_score = max(risk_score, 100)
                                elif attr.cde_flag:
                                    risk_score = max(risk_score, 95)
                                elif attr.mandatory_flag == "Mandatory":
                                    risk_score = max(risk_score, 85)
                                
                                attr.risk_score = risk_score
                                
                                # Enhanced risk rationale from risk_score_details with better formatting
                                if attr_recs.get("risk_score_details"):
                                    details = attr_recs["risk_score_details"]
                                    risk_parts = []
                                    # Order the factors for consistent display
                                    factor_map = {
                                        'regulatory_impact': 'Regulatory Impact',
                                        'data_complexity': 'Data Complexity', 
                                        'common_errors': 'Common Errors',
                                        'downstream_dependencies': 'Downstream Dependencies',
                                        'cde_criticality': 'CDE Criticality',
                                        'historical_issues': 'Historical Issues'
                                    }
                                    for key, display_name in factor_map.items():
                                        value = details.get(key)
                                        if value and "N/A" not in str(value):
                                            risk_parts.append(f"**{display_name}:** {value}")
                                    attr.llm_risk_rationale = "\n".join(risk_parts) if risk_parts else f"Risk score {risk_score} based on regulatory importance"
                                else:
                                    attr.llm_risk_rationale = attr_recs.get("rationale", f"Risk score {risk_score} based on regulatory importance")
                                
                                # Set testing approach from validation rules
                                if attr_recs.get("validation_rules"):
                                    attr.testing_approach = attr_recs.get("validation_rules")
                                else:
                                    attr.testing_approach = "Standard validation"
                                
                                # Set source documents
                                if attr_recs.get("typical_source_documents"):
                                    attr.typical_source_documents = attr_recs.get("typical_source_documents")
                                
                                # Set keywords
                                if attr_recs.get("keywords_to_look_for"):
                                    attr.keywords_to_look_for = attr_recs.get("keywords_to_look_for")
                                
                                recommendations_generated += 1
                            else:
                                # Fallback if no recommendations found for this attribute
                                logger.warning(f"No recommendations found for attribute {attr.attribute_name}")
                                if attr.is_primary_key:
                                    attr.llm_rationale = "Primary key - Always include in testing"
                                    attr.risk_score = 100
                                elif attr.cde_flag:
                                    attr.llm_rationale = "Critical data element - Strongly recommend testing"
                                    attr.risk_score = 95
                                else:
                                    attr.llm_rationale = "Standard attribute - Evaluate based on risk"
                                    attr.risk_score = 50
                    else:
                        # LLM call failed for entire batch
                        logger.error(f"Failed to get recommendations for batch {batch_num}")
                        for attr in batch:
                            if attr.is_primary_key:
                                attr.llm_rationale = "Primary key - Always include in testing"
                                attr.risk_score = 100
                            else:
                                attr.llm_rationale = "Standard attribute - Evaluate based on risk"
                                attr.risk_score = 50
                    
                    processed += len(batch)
                    
                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {str(e)}")
                    # Use fallback for this batch
                    for attr in batch:
                        if attr.is_primary_key:
                            attr.llm_rationale = "Primary key - Always include in testing"
                            attr.risk_score = 100
                        elif attr.cde_flag:
                            attr.llm_rationale = "Critical data element - Strongly recommend testing"
                            attr.risk_score = 95
                        else:
                            attr.llm_rationale = "Standard attribute - Evaluate based on risk"
                            attr.risk_score = 50
                    processed += len(batch)
                
                # Save after each batch
                await db.commit()
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
            
            # Final update
            job_manager.update_job_progress(
                job_id,
                progress=100,
                message="Recommendations generated successfully",
                current_step="Complete",
                result={
                    "attributes_processed": processed,
                    "recommendations_generated": recommendations_generated,
                    "test_recommendations": recommendations_generated
                }
            )
            
            return {
                "success": True,
                "attributes_processed": processed,
                "recommendations_generated": recommendations_generated
            }
            
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        job_manager.complete_job(job_id, error=str(e))
        raise


@router.post("/cycles/{cycle_id}/reports/{report_id}/decisions")
async def submit_scoping_decisions(
    cycle_id: int,
    report_id: int,
    submission_payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Submit scoping decisions for attributes"""
    from app.models.scoping import ScopingSubmission, TesterScopingDecision
    
    # Extract decision data
    decisions = submission_payload.get("decisions", [])
    submission_notes = submission_payload.get("submission_notes", "")
    confirm_submission = submission_payload.get("confirm_submission", False)
    
    # Update attributes with scoping decisions
    for decision in decisions:
        attr_id = decision["attribute_id"]
        
        # Get the attribute
        attr_query = select(ReportAttribute).where(
            and_(
                ReportAttribute.attribute_id == attr_id,
                ReportAttribute.cycle_id == cycle_id,
                ReportAttribute.report_id == report_id
            )
        )
        result = await db.execute(attr_query)
        attr = result.scalar_one_or_none()
        
        if attr:
            # Update scoping decision
            attr.is_scoped = decision.get("final_scoping", False)
            # Store rationale
            if decision.get("tester_rationale"):
                attr.tester_notes = decision["tester_rationale"]
    
    # If confirming submission, create a ScopingSubmission record
    if confirm_submission:
        # Get report info for assignment
        report_query = select(Report).where(Report.report_id == report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        
        if not report:
            raise NotFoundException("Report not found")
        
        # Get previous submission if exists
        prev_query = select(ScopingSubmission).where(
            and_(
                ScopingSubmission.cycle_id == cycle_id,
                ScopingSubmission.report_id == report_id
            )
        ).order_by(ScopingSubmission.version.desc())
        prev_result = await db.execute(prev_query)
        previous = prev_result.scalars().first()
        
        # Count included/excluded
        included_count = sum(1 for d in decisions if d.get("final_scoping", False))
        excluded_count = len(decisions) - included_count
        
        # Create new submission
        new_submission = ScopingSubmission(
            cycle_id=cycle_id,
            report_id=report_id,
            submitted_by=current_user.user_id,
            version=previous.version + 1 if previous else 1,
            previous_version_id=previous.submission_id if previous else None,
            total_attributes=len(decisions),
            scoped_attributes=included_count,
            skipped_attributes=excluded_count,
            submission_notes=submission_notes
        )
        
        db.add(new_submission)
        await db.flush()  # Get submission_id
        
        # Create individual decision records
        for decision in decisions:
            tester_decision = TesterScopingDecision(
                cycle_id=cycle_id,
                report_id=report_id,
                attribute_id=decision["attribute_id"],
                decision=decision.get("decision", "Accept" if decision["final_scoping"] else "Decline"),
                final_scoping=decision.get("final_scoping", False),
                tester_rationale=decision.get("tester_rationale", ""),
                decided_by=current_user.user_id
            )
            db.add(tester_decision)
        
        # Create UniversalAssignment for Report Owner approval
        from app.services.universal_assignment_service import UniversalAssignmentService
        
        assignment_service = UniversalAssignmentService(db)
        
        assignment = await assignment_service.create_assignment(
            assignment_type="Scoping Approval",
            from_role="Tester",
            to_role="Report Owner", 
            from_user_id=current_user.user_id,
            to_user_id=report.report_owner_id,
            title=f"Scoping Approval Required - {report.report_name}",
            description=f"Tester {current_user.first_name} {current_user.last_name} has submitted scoping decisions for {report.report_name}. Please review and approve/reject the selected attributes.",
            task_instructions=f"Review the {included_count} attributes selected for testing out of {len(decisions)} total attributes. Provide feedback if changes are needed.",
            context_type="Report",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "submission_id": new_submission.submission_id,
                "version": new_submission.version,
                "included_count": included_count,
                "total_attributes": len(decisions),
                "phase": "Scoping",
                "submission_url": f"/cycles/{cycle_id}/reports/{report_id}/scoping-review"
            },
            priority="High",
            due_date=datetime.utcnow() + timedelta(days=3),
            requires_approval=True,
            approval_role="Report Owner",
            assignment_metadata={
                "submission_version": new_submission.version,
                "tester_notes": submission_notes,
                "auto_created": True,
                "workflow_step": "scoping_approval"
            }
        )
        
        logger.info(f"Created UniversalAssignment {assignment.assignment_id} for Report Owner approval of scoping submission {new_submission.submission_id}")
    
    await db.commit()
    
    if confirm_submission:
        return {
            "message": "Scoping decisions submitted successfully",
            "decisions_submitted": len(decisions),
            "submission_notes": submission_notes,
            "version": new_submission.version,
            "is_revision": previous is not None
        }
    else:
        return {
            "message": "Scoping decisions saved successfully",
            "decisions_saved": len(decisions),
            "submission_notes": submission_notes
        }


@router.get("/pending-reviews")
async def get_pending_scoping_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """Get pending scoping reviews for Report Owner"""
    from sqlalchemy import text
    
    # Check if user is a Report Owner
    if current_user.role not in ["Report Owner", "Report Owner Executive"]:
        return []
    
    try:
        # Use raw SQL to avoid model relationship issues
        query = text("""
            WITH latest_versions AS (
                SELECT cycle_id, report_id, MAX(version) as max_version
                FROM cycle_report_scoping_submissions
                WHERE report_id IN (
                    SELECT report_id FROM reports WHERE report_owner_id = :owner_id
                )
                GROUP BY cycle_id, report_id
            )
            SELECT 
                ss.submission_id,
                ss.cycle_id,
                ss.report_id,
                r.report_name,
                l.lob_name,
                CONCAT(u.first_name, ' ', u.last_name) as submitted_by,
                ss.created_at,
                ss.scoped_attributes,
                ss.total_attributes,
                ss.version
            FROM cycle_report_scoping_submissions ss
            JOIN latest_versions lv ON 
                ss.cycle_id = lv.cycle_id AND 
                ss.report_id = lv.report_id AND 
                ss.version = lv.max_version
            JOIN reports r ON r.report_id = ss.report_id
            LEFT JOIN lobs l ON l.lob_id = r.lob_id
            LEFT JOIN users u ON u.user_id = ss.submitted_by
            WHERE r.report_owner_id = :owner_id
              AND NOT EXISTS (
                  SELECT 1 FROM cycle_report_scoping_report_owner_reviews rosr
                  WHERE rosr.submission_id = ss.submission_id
              )
            ORDER BY ss.created_at DESC
        """)
        
        result = await db.execute(query, {"owner_id": current_user.user_id})
        rows = result.fetchall()
        
        # Build response
        pending_reviews = []
        for row in rows:
            pending_reviews.append({
                "submission_id": row[0],
                "cycle_id": row[1],
                "report_id": row[2],
                "report_name": row[3],
                "lob": row[4] or "Unknown",
                "submitted_by": row[5] or "Unknown",
                "submitted_date": row[6].isoformat() if row[6] else datetime.utcnow().isoformat(),
                "attributes_selected": row[7] or 0,
                "total_attributes": row[8] or 0,
                "priority": "High" if (row[8] or 0) > 100 else "Medium",
                "version": row[9]
            })
        
        return pending_reviews
        
    except Exception as e:
        logger.error(f"Error getting pending scoping reviews: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving pending reviews: {str(e)}"
        )


@router.get("/cycles/{cycle_id}/reports/{report_id}/submission")
async def get_scoping_submission(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the latest scoping submission for a report"""
    from sqlalchemy import text
    
    # Get the latest submission
    query = text("""
        WITH latest_version AS (
            SELECT MAX(version) as max_version
            FROM cycle_report_scoping_submissions
            WHERE cycle_id = :cycle_id AND report_id = :report_id
        )
        SELECT 
            ss.submission_id,
            ss.cycle_id,
            ss.report_id,
            ss.submission_notes,
            ss.total_attributes,
            ss.scoped_attributes,
            ss.skipped_attributes,
            ss.created_at as submitted_at,
            CONCAT(u.first_name, ' ', u.last_name) as submitted_by_name,
            ss.version,
            ss.changes_from_previous
        FROM cycle_report_scoping_submissions ss
        JOIN latest_version lv ON ss.version = lv.max_version
        LEFT JOIN users u ON u.user_id = ss.submitted_by
        WHERE ss.cycle_id = :cycle_id AND ss.report_id = :report_id
    """)
    
    result = await db.execute(query, {
        "cycle_id": cycle_id,
        "report_id": report_id
    })
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scoping submission found"
        )
    
    return {
        "submission_id": row[0],
        "cycle_id": row[1],
        "report_id": row[2],
        "submission_notes": row[3],
        "total_attributes": row[4],
        "scoped_attributes": row[5],
        "skipped_attributes": row[6] or 0,
        "submitted_at": row[7].isoformat() if row[7] else None,
        "submitted_by_name": row[8],
        "version": row[9],
        "changes_from_previous": row[10]
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/review")
async def submit_scoping_review(
    cycle_id: int,
    report_id: int,
    review_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit report owner review for scoping submission"""
    from sqlalchemy import text
    from datetime import datetime
    import json
    
    # Check if user is a Report Owner
    if current_user.role not in ["Report Owner", "Report Owner Executive"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Report Owners can review scoping submissions"
        )
    
    # Get the latest submission
    submission_query = text("""
        SELECT submission_id 
        FROM cycle_report_scoping_submissions
        WHERE cycle_id = :cycle_id AND report_id = :report_id
        ORDER BY version DESC
        LIMIT 1
    """)
    
    result = await db.execute(submission_query, {
        "cycle_id": cycle_id,
        "report_id": report_id
    })
    
    submission = result.first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scoping submission found to review"
        )
    
    # Map review decision to approval status
    review_decision = review_data.get("review_decision", "")
    if review_decision == "Approved":
        approval_status = "Approved"
    elif review_decision == "Revision Required":
        approval_status = "Needs Revision"
    elif review_decision == "Declined":
        approval_status = "Declined"
    else:
        approval_status = "Pending"
    
    # Insert review
    insert_query = text("""
        INSERT INTO cycle_report_scoping_report_owner_reviews (
            cycle_id,
            report_id,
            submission_id,
            approval_status,
            review_comments,
            reviewed_by,
            created_at,
            resource_impact_assessment,
            risk_coverage_assessment,
            requested_changes
        ) VALUES (
            :cycle_id,
            :report_id,
            :submission_id,
            :approval_status,
            :review_comments,
            :reviewed_by,
            :created_at,
            :resource_impact_assessment,
            :risk_coverage_assessment,
            :requested_changes
        )
    """)
    
    await db.execute(insert_query, {
        "cycle_id": cycle_id,
        "report_id": report_id,
        "submission_id": submission[0],
        "approval_status": approval_status,
        "review_comments": review_data.get("review_comments"),
        "reviewed_by": current_user.user_id,
        "created_at": datetime.utcnow(),
        "resource_impact_assessment": review_data.get("resource_impact_assessment"),
        "risk_coverage_assessment": review_data.get("risk_coverage_assessment"),
        "requested_changes": json.dumps(review_data.get("requested_changes", {})) if review_data.get("requested_changes") else None
    })
    
    await db.commit()
    
    # Don't automatically advance workflow - this should be a manual step
    # The user needs to explicitly complete the phase after approval
    
    return {
        "status": "success",
        "message": f"Review submitted successfully: {review_data.get('review_decision')}"
    }