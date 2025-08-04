"""
Scoping submission endpoints with versioning support
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth import UserRoles, RoleChecker
from app.core.logging import get_logger
from app.core.exceptions import ValidationException, NotFoundException, BusinessLogicException
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.models.scoping import (
    ScopingSubmission, 
    TesterScopingDecision,
    ReportOwnerScopingReview,
    ScopingAuditLog
)

logger = get_logger(__name__)
router = APIRouter()

# Role-based access control
tester_roles = [UserRoles.TESTER]
report_owner_roles = [UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE]
all_roles = tester_roles + report_owner_roles + [UserRoles.TEST_EXECUTIVE, UserRoles.ADMIN]


@router.post("/cycles/{cycle_id}/reports/{report_id}/scoping-submission")
async def create_scoping_submission(
    cycle_id: int,
    report_id: int,
    submission_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create a new scoping submission with versioning"""
    
    # Check permissions - only testers can submit
    RoleChecker(tester_roles)(current_user)
    
    # Verify scoping phase is in progress
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Scoping"
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase or phase.status != "In Progress":
        raise BusinessLogicException("Scoping phase must be in progress to submit decisions")
    
    # Get previous submission if exists
    prev_query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id,
            ScopingSubmission.is_latest == True
        )
    )
    prev_result = await db.execute(prev_query)
    previous = prev_result.scalar_one_or_none()
    
    # Create new submission
    new_submission = ScopingSubmission(
        cycle_id=cycle_id,
        report_id=report_id,
        submitted_by=current_user.user_id,
        version=previous.version + 1 if previous else 1,
        previous_version_id=previous.submission_id if previous else None,
        total_attributes=submission_data["total_attributes"],
        scoped_attributes=submission_data["included_count"],
        skipped_attributes=submission_data["excluded_count"],
        submission_notes=submission_data.get("notes", ""),
        submission_status="pending_review",
        is_latest=True
    )
    
    # Mark previous as not latest
    if previous:
        previous.is_latest = False
        
        # Calculate changes from previous version
        changes = await calculate_version_changes(
            db, cycle_id, report_id, previous.submission_id, submission_data["decisions"]
        )
        new_submission.changes_from_previous = changes
    
    db.add(new_submission)
    await db.flush()  # Get submission_id
    
    # Create individual decisions
    for decision_data in submission_data["decisions"]:
        decision = TesterScopingDecision(
            cycle_id=cycle_id,
            report_id=report_id,
            attribute_id=decision_data["attribute_id"],
            decision=decision_data["decision"],
            final_scoping=decision_data["include"],
            tester_rationale=decision_data.get("rationale", ""),
            decided_by=current_user.user_id
        )
        db.add(decision)
    
    # Create audit log entry
    audit_log = ScopingAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        submission_id=new_submission.submission_id,
        action="submission_created",
        performed_by=current_user.user_id,
        previous_value=json.dumps({"version": previous.version if previous else 0}),
        new_value=json.dumps({"version": new_submission.version}),
        details=f"Created scoping submission version {new_submission.version}"
    )
    db.add(audit_log)
    
    await db.commit()
    
    logger.info(f"Created scoping submission version {new_submission.version} for cycle {cycle_id} report {report_id}")
    
    return {
        "submission_id": new_submission.submission_id,
        "version": new_submission.version,
        "status": "submitted_for_approval",
        "message": f"Scoping submission version {new_submission.version} created successfully"
    }


async def calculate_version_changes(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    previous_submission_id: int,
    current_decisions: List[Dict]
) -> Dict[str, Any]:
    """Calculate what changed between submission versions"""
    
    # Get previous decisions
    prev_decisions_query = select(TesterScopingDecision).where(
        and_(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id,
            # Note: Should link to submission_id when that column is added
        )
    )
    prev_result = await db.execute(prev_decisions_query)
    prev_decisions = prev_result.scalars().all()
    
    # Create lookup maps
    prev_map = {d.attribute_id: d for d in prev_decisions}
    curr_map = {d["attribute_id"]: d for d in current_decisions}
    
    changes = {
        "added": [],
        "removed": [],
        "modified": [],
        "summary": {
            "total_changes": 0,
            "included_to_excluded": 0,
            "excluded_to_included": 0
        }
    }
    
    # Find changes
    for attr_id, curr_decision in curr_map.items():
        if attr_id not in prev_map:
            changes["added"].append(attr_id)
        else:
            prev = prev_map[attr_id]
            if prev.final_scoping != curr_decision["include"]:
                changes["modified"].append({
                    "attribute_id": attr_id,
                    "previous": "included" if prev.final_scoping else "excluded",
                    "current": "included" if curr_decision["include"] else "excluded"
                })
                
                if prev.final_scoping and not curr_decision["include"]:
                    changes["summary"]["included_to_excluded"] += 1
                elif not prev.final_scoping and curr_decision["include"]:
                    changes["summary"]["excluded_to_included"] += 1
    
    # Find removed (shouldn't happen but check anyway)
    for attr_id in prev_map:
        if attr_id not in curr_map:
            changes["removed"].append(attr_id)
    
    changes["summary"]["total_changes"] = (
        len(changes["added"]) + 
        len(changes["removed"]) + 
        len(changes["modified"])
    )
    
    return changes


@router.get("/cycles/{cycle_id}/reports/{report_id}/scoping-history")
async def get_scoping_submission_history(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """Get all scoping submission versions"""
    
    query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.version.desc())
    
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    return [
        {
            "submission_id": sub.submission_id,
            "version": sub.version,
            "submitted_at": sub.submitted_at.isoformat(),
            "submitted_by": sub.submitted_by,
            "total_attributes": sub.total_attributes,
            "included": sub.scoped_attributes,
            "excluded": sub.skipped_attributes,
            "status": sub.submission_status,
            "is_latest": sub.is_latest,
            "changes_from_previous": sub.changes_from_previous,
            "submission_notes": sub.submission_notes,
            "review_status": sub.review_status,
            "review_comments": sub.review_comments
        }
        for sub in submissions
    ]


@router.get("/cycles/{cycle_id}/reports/{report_id}/scoping-submission/{version}")
async def get_scoping_submission_details(
    cycle_id: int,
    report_id: int,
    version: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get detailed information about a specific submission version"""
    
    # Get submission
    sub_query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id,
            ScopingSubmission.version == version
        )
    )
    sub_result = await db.execute(sub_query)
    submission = sub_result.scalar_one_or_none()
    
    if not submission:
        raise NotFoundException(f"Scoping submission version {version} not found")
    
    # Get decisions for this submission
    # Note: This needs submission_id column in TesterScopingDecision table
    decisions_query = select(TesterScopingDecision).where(
        and_(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id,
            # TesterScopingDecision.submission_id == submission.submission_id
        )
    )
    dec_result = await db.execute(decisions_query)
    decisions = dec_result.scalars().all()
    
    # Get attribute details
    attr_ids = [d.attribute_id for d in decisions]
    attrs_query = select(ReportAttribute).where(
        ReportAttribute.attribute_id.in_(attr_ids)
    )
    attrs_result = await db.execute(attrs_query)
    attributes = {a.attribute_id: a for a in attrs_result.scalars().all()}
    
    return {
        "submission": {
            "submission_id": submission.submission_id,
            "version": submission.version,
            "submitted_at": submission.submitted_at.isoformat(),
            "submitted_by": submission.submitted_by,
            "total_attributes": submission.total_attributes,
            "included": submission.scoped_attributes,
            "excluded": submission.skipped_attributes,
            "status": submission.submission_status,
            "is_latest": submission.is_latest,
            "submission_notes": submission.submission_notes
        },
        "decisions": [
            {
                "attribute_id": d.attribute_id,
                "attribute_name": attributes[d.attribute_id].attribute_name if d.attribute_id in attributes else "Unknown",
                "decision": d.decision,
                "included": d.final_scoping,
                "rationale": d.tester_rationale
            }
            for d in decisions
        ],
        "changes_from_previous": submission.changes_from_previous
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/scoping-submission/{submission_id}/review")
async def review_scoping_submission(
    cycle_id: int,
    report_id: int,
    submission_id: int,
    review_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Report owner reviews a scoping submission"""
    
    # Check permissions - only report owners can review
    RoleChecker(report_owner_roles)(current_user)
    
    # Get submission
    sub_query = select(ScopingSubmission).where(
        ScopingSubmission.submission_id == submission_id
    )
    sub_result = await db.execute(sub_query)
    submission = sub_result.scalar_one_or_none()
    
    if not submission:
        raise NotFoundException("Scoping submission not found")
    
    # Create review record
    review = ReportOwnerScopingReview(
        submission_id=submission_id,
        cycle_id=cycle_id,
        report_id=report_id,
        reviewed_by=current_user.user_id,
        review_decision=review_data["decision"],  # Approved/Declined/Needs Revision
        review_comments=review_data.get("comments", ""),
        requested_changes=review_data.get("requested_changes", {}),
        resource_impact_assessment=review_data.get("resource_impact", ""),
        risk_coverage_assessment=review_data.get("risk_coverage", "")
    )
    db.add(review)
    
    # Update submission status
    submission.review_status = review_data["decision"]
    submission.review_comments = review_data.get("comments", "")
    
    # If approved, update workflow phase
    if review_data["decision"] == "Approved":
        submission.submission_status = "approved"
        
        # Update report attributes with final scoping decisions
        decisions_query = select(TesterScopingDecision).where(
            and_(
                TesterScopingDecision.cycle_id == cycle_id,
                TesterScopingDecision.report_id == report_id
            )
        )
        dec_result = await db.execute(decisions_query)
        decisions = dec_result.scalars().all()
        
        for decision in decisions:
            await db.execute(
                update(ReportAttribute)
                .where(ReportAttribute.attribute_id == decision.attribute_id)
                .values(is_scoped=decision.final_scoping)
            )
    else:
        submission.submission_status = "requires_revision"
    
    # Create audit log
    audit_log = ScopingAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        submission_id=submission_id,
        action="submission_reviewed",
        performed_by=current_user.user_id,
        previous_value=json.dumps({"status": "pending_review"}),
        new_value=json.dumps({"status": review_data["decision"]}),
        details=f"Submission reviewed: {review_data['decision']}"
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {
        "review_id": review.review_id,
        "decision": review_data["decision"],
        "message": f"Scoping submission {review_data['decision'].lower()}"
    }