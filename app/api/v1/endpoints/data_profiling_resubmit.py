"""
Data Profiling Resubmission API
Handles tester resubmissions after report owner feedback
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Dict, Any
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user, RoleChecker
from app.models.user import User
from app.models.data_profiling import (
    DataProfilingRuleVersion, ProfilingRule, Decision, 
    ProfilingRuleStatus, VersionStatus
)
from app.models.workflow import WorkflowPhase
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Define role groups
tester_roles = ["Tester", "Test Executive"]
report_owner_roles = ["Report Owner", "Report Owner Executive"]
management_roles = ["Data Executive", "Admin"]


@router.post("/cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback")
async def resubmit_after_feedback(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new version when tester resubmits after report owner feedback.
    This allows the tester to update decisions based on report owner feedback.
    """
    # Check permissions - only testers can resubmit
    RoleChecker(tester_roles)(current_user)
    
    try:
        # Get phase_id
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        if not phase:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Get latest version
        latest_version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase.phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        latest_version = latest_version_query.scalar_one_or_none()
        
        if not latest_version:
            raise HTTPException(status_code=404, detail="No data profiling version found")
        
        # Check if there's report owner feedback
        feedback_check_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == latest_version.version_id,
                    ProfilingRule.report_owner_decision.isnot(None)
                )
            )
        )
        feedback_count = feedback_check_query.scalar() or 0
        
        if feedback_count == 0:
            raise HTTPException(
                status_code=400, 
                detail="No report owner feedback found. Resubmission is only allowed after receiving feedback."
            )
        
        # Check if all report owner decisions are approved
        all_approved_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == latest_version.version_id,
                    ProfilingRule.report_owner_decision != "approved"
                )
            )
        )
        non_approved_count = all_approved_query.scalar() or 0
        
        if non_approved_count == 0:
            raise HTTPException(
                status_code=400,
                detail="All rules are already approved by report owner. No resubmission needed."
            )
        
        # Create new version
        new_version_number = latest_version.version_number + 1
        new_version = DataProfilingRuleVersion(
            phase_id=phase.phase_id,
            version_number=new_version_number,
            version_status=VersionStatus.DRAFT,
            parent_version_id=latest_version.version_id,
            created_by_id=current_user.user_id,
            created_at=datetime.utcnow(),
            updated_by_id=current_user.user_id,
            updated_at=datetime.utcnow()
        )
        db.add(new_version)
        await db.flush()
        
        # Copy rules from previous version, allowing tester to update decisions
        rules_query = await db.execute(
            select(ProfilingRule).where(
                ProfilingRule.version_id == latest_version.version_id
            )
        )
        rules = rules_query.scalars().all()
        
        for rule in rules:
            # For rules with report owner feedback, copy the rule but reset tester decision
            # This allows tester to make new decisions based on feedback
            new_rule = ProfilingRule(
                rule_id=uuid.uuid4(),
                version_id=new_version.version_id,
                phase_id=rule.phase_id,
                attribute_id=rule.attribute_id,
                attribute_name=rule.attribute_name,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                rule_description=rule.rule_description,
                rule_code=rule.rule_code,
                rule_parameters=rule.rule_parameters,
                severity=rule.severity,
                # LLM metadata
                llm_provider=rule.llm_provider,
                llm_rationale=rule.llm_rationale,
                llm_confidence_score=rule.llm_confidence_score,
                regulatory_reference=rule.regulatory_reference,
                # Rule configuration
                is_executable=rule.is_executable,
                execution_order=rule.execution_order,
                # Keep report owner decisions and feedback
                report_owner_decision=rule.report_owner_decision,
                report_owner_notes=rule.report_owner_notes,
                report_owner_decided_by=rule.report_owner_decided_by,
                report_owner_decided_at=rule.report_owner_decided_at,
                # Reset tester decision for rules that were rejected by report owner
                tester_decision=None if rule.report_owner_decision == "rejected" else rule.tester_decision,
                tester_notes=None if rule.report_owner_decision == "rejected" else rule.tester_notes,
                tester_decided_by=None if rule.report_owner_decision == "rejected" else rule.tester_decided_by,
                tester_decided_at=None if rule.report_owner_decision == "rejected" else rule.tester_decided_at,
                # Reset status for rejected rules
                status=ProfilingRuleStatus.PENDING if rule.report_owner_decision == "rejected" else rule.status,
                # Copy other fields
                created_by_id=current_user.user_id,
                created_at=datetime.utcnow(),
                updated_by_id=current_user.user_id,
                updated_at=datetime.utcnow()
            )
            db.add(new_rule)
        
        # Update previous version status to superseded
        latest_version.version_status = VersionStatus.SUPERSEDED
        latest_version.updated_at = datetime.utcnow()
        latest_version.updated_by_id = current_user.user_id
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Created new version {new_version_number} for updating decisions based on report owner feedback",
            "version_id": str(new_version.version_id),
            "version_number": new_version_number,
            "rules_to_update": non_approved_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating resubmission version: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cycles/{cycle_id}/reports/{report_id}/finalize-version")
async def finalize_version(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark version as final when report owner approves all rules.
    This is called automatically when all rules are approved by report owner.
    """
    # Check permissions - report owners and system can finalize
    if current_user.role not in report_owner_roles + management_roles:
        raise HTTPException(
            status_code=403,
            detail="Only report owners can finalize versions"
        )
    
    try:
        # Get phase_id
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Profiling"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        if not phase:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Get latest version
        latest_version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase.phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        latest_version = latest_version_query.scalar_one_or_none()
        
        if not latest_version:
            raise HTTPException(status_code=404, detail="No data profiling version found")
        
        # Check if all rules are approved by both tester and report owner
        unapproved_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == latest_version.version_id,
                    ~and_(
                        ProfilingRule.tester_decision == "approved",
                        ProfilingRule.report_owner_decision == "approved"
                    )
                )
            )
        )
        unapproved_count = unapproved_query.scalar() or 0
        
        if unapproved_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot finalize version. {unapproved_count} rules are not fully approved."
            )
        
        # Update version status to approved (final)
        latest_version.version_status = VersionStatus.APPROVED
        latest_version.approved_by_id = current_user.user_id
        latest_version.approved_at = datetime.utcnow()
        latest_version.updated_at = datetime.utcnow()
        latest_version.updated_by_id = current_user.user_id
        
        # Update all rules to final approved status
        await db.execute(
            update(ProfilingRule)
            .where(ProfilingRule.version_id == latest_version.version_id)
            .values(
                status=ProfilingRuleStatus.APPROVED,
                updated_at=datetime.utcnow(),
                updated_by_id=current_user.user_id
            )
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Version {latest_version.version_number} has been finalized as the approved version",
            "version_id": str(latest_version.version_id),
            "version_number": latest_version.version_number,
            "version_status": "approved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing version: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))