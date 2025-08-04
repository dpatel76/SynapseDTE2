"""
Enhanced Data Profiling Rules API with Individual Rule Approval/Decline
Supports attribute-level organization and versioning
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join
from sqlalchemy import and_, func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.data_profiling import ProfilingRule, ProfilingRuleStatus, ProfilingRuleType
from app.models.report_attribute import ReportAttribute
from app.schemas.data_profiling_rules import (
    ProfilingRuleResponse, 
    ProfilingRuleUpdate,
    RuleApprovalRequest,
    RuleRejectionRequest,
    AttributeRulesSummary
)

router = APIRouter()

@router.get("/attributes/{cycle_id}/{report_id}/rules-summary", response_model=List[AttributeRulesSummary])
async def get_attributes_rules_summary(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get attribute-level summary of profiling rules with approval counts"""
    
    try:
        from sqlalchemy import text
        from app.models.workflow import WorkflowPhase
        
        # First get the phase_id for Data Profiling phase
        workflow_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
        workflow_phase = workflow_query.scalar_one_or_none()
        
        if not workflow_phase:
            return []  # No data profiling phase found
        
        # Get planning phase to fetch attributes
        planning_phase_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        planning_phase = planning_phase_query.scalar_one_or_none()
        
        if not planning_phase:
            return []  # No planning phase found
        
        # Get all attributes for this phase using the correct table and phase_id
        attributes_query = await db.execute(
            text("""
            SELECT id as attribute_id, attribute_name, data_type, 
                   is_cde, is_primary_key, has_issues, version, line_item_number
            FROM cycle_report_planning_attributes 
            WHERE phase_id = :phase_id
                AND is_active = true
            """),
            {"phase_id": planning_phase.phase_id}
        )
        attributes = attributes_query.fetchall()
        
        summaries = []
        
        for attribute in attributes:
            # Get rule counts by status for this attribute using raw SQL
            rule_counts_query = await db.execute(
                text("""
                SELECT status, COUNT(*) as count
                FROM cycle_report_data_profiling_rules 
                WHERE phase_id = :phase_id AND attribute_id = :attribute_id
                GROUP BY status
                """),
                {"phase_id": workflow_phase.phase_id, "attribute_id": attribute.attribute_id}
            )
            rule_counts = rule_counts_query.fetchall()
            
            # Convert to dictionary
            status_counts = {status: count for status, count in rule_counts}
            
            # Get latest rule activity
            latest_rule_query = await db.execute(
                text("""
                SELECT updated_at 
                FROM cycle_report_data_profiling_rules 
                WHERE phase_id = :phase_id AND attribute_id = :attribute_id
                ORDER BY updated_at DESC
                LIMIT 1
                """),
                {"phase_id": workflow_phase.phase_id, "attribute_id": attribute.attribute_id}
            )
            latest_rule_result = latest_rule_query.fetchone()
            latest_updated = latest_rule_result[0] if latest_rule_result else None
        
            summary = AttributeRulesSummary(
                attribute_id=attribute.attribute_id,
                attribute_name=attribute.attribute_name,
                attribute_type=attribute.data_type or "Unknown",  # Handle null data_type
                mandatory=False,  # Default to false since mandatory_flag doesn't exist
                total_rules=sum(status_counts.values()),
                approved_count=status_counts.get('approved', 0),  # Use string status values
                rejected_count=status_counts.get('rejected', 0),
                pending_count=status_counts.get('pending', 0),
                needs_revision_count=status_counts.get('needs_revision', 0),
                last_updated=latest_updated,
                can_approve=True,  # Temporary for testing
                can_edit=True,  # Temporary for testing
                line_item_number=attribute.line_item_number or attribute.version,  # Use line_item_number if available
                is_cde=attribute.is_cde or False,
                is_primary_key=attribute.is_primary_key or False,
                has_issues=attribute.has_issues or False
            )
            
            summaries.append(summary)
        
        return summaries
        
    except Exception as e:
        # Log the error and return empty list for now
        print(f"Error in get_attributes_rules_summary: {e}")
        return []

@router.get("/attributes/{attribute_id}/rules", response_model=List[ProfilingRuleResponse])
async def get_attribute_rules(
    attribute_id: int,
    cycle_id: int,
    report_id: int,
    include_history: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all rules for a specific attribute with optional version history"""
    
    query = select(ProfilingRule).where(
        and_(
            ProfilingRule.attribute_id == attribute_id,
            ProfilingRule.cycle_id == cycle_id,
            ProfilingRule.report_id == report_id
        )
    )
    
    # Note: Version history is handled at the version level, not individual rules
    
    query = query.order_by(
        ProfilingRule.rule_name,
        desc(ProfilingRule.version_number)
    )
    
    rules_result = await db.execute(query)
    rules = rules_result.scalars().all()
    
    return [ProfilingRuleResponse.from_orm(rule) for rule in rules]

@router.put("/rules/{rule_id}/approve")
async def approve_profiling_rule(
    rule_id: str,  # Changed from int to str to handle UUIDs
    approval_request: RuleApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve an individual profiling rule"""
    
    rule_query = select(ProfilingRule).where(
        ProfilingRule.rule_id == rule_id
    )
    
    rule_result = await db.execute(rule_query)
    rule = rule_result.scalars().first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or not current version"
        )
    
    from app.models.data_profiling import Decision
    
    # Determine if user is tester or report owner based on role
    if current_user.role in ["Tester", "Test Executive"]:
        # Set tester approval
        rule.tester_decision = Decision.APPROVED
        rule.tester_decided_by = current_user.user_id
        rule.tester_decided_at = datetime.utcnow()
        rule.tester_notes = approval_request.notes
    elif current_user.role in ["Report Owner", "Report Owner Executive"]:
        # Set report owner approval
        rule.report_owner_decision = Decision.APPROVED
        rule.report_owner_decided_by = current_user.user_id
        rule.report_owner_decided_at = datetime.utcnow()
        rule.report_owner_notes = approval_request.notes
    else:
        # Admin can set either - default to tester
        rule.tester_decision = Decision.APPROVED
        rule.tester_decided_by = current_user.user_id
        rule.tester_decided_at = datetime.utcnow()
        rule.tester_notes = approval_request.notes
    
    # Update status based on approvals
    # If tester approves, mark as submitted (ready for report owner review)
    # Only mark as fully approved when both approve
    if rule.tester_decision == Decision.APPROVED and rule.report_owner_decision == Decision.APPROVED:
        rule.status = ProfilingRuleStatus.APPROVED
    elif current_user.role in ["Tester", "Test Executive"] and rule.tester_decision == Decision.APPROVED:
        rule.status = ProfilingRuleStatus.SUBMITTED  # Tester approved, awaiting report owner
    elif current_user.role in ["Report Owner", "Report Owner Executive"] and rule.report_owner_decision == Decision.APPROVED:
        # Report owner approved but tester hasn't - keep as pending
        rule.status = ProfilingRuleStatus.PENDING
    
    rule.updated_at = datetime.utcnow()
    rule.updated_by_id = current_user.user_id
    
    await db.commit()
    await db.refresh(rule)
    
    return {
        "success": True,
        "message": f"Rule '{rule.rule_name}' approved successfully",
        "rule_id": rule.rule_id,
        "status": rule.status
    }

@router.put("/rules/{rule_id}/reject")
async def reject_profiling_rule(
    rule_id: str,  # Changed from int to str to handle UUIDs
    rejection_request: RuleRejectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject an individual profiling rule with feedback"""
    
    rule_query = select(ProfilingRule).where(
        ProfilingRule.rule_id == rule_id
    )
    
    rule_result = await db.execute(rule_query)
    rule = rule_result.scalars().first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or not current version"
        )
    
    from app.models.data_profiling import Decision
    
    # Update rule status
    rule.status = ProfilingRuleStatus.REJECTED
    
    # Determine if user is tester or report owner based on role
    if current_user.role in ["Tester", "Test Executive"]:
        # Set tester rejection
        rule.tester_decision = Decision.REJECTED
        rule.tester_decided_by = current_user.user_id
        rule.tester_decided_at = datetime.utcnow()
        rule.tester_notes = f"{rejection_request.reason}: {rejection_request.notes}"
    elif current_user.role in ["Report Owner", "Report Owner Executive"]:
        # Set report owner rejection
        rule.report_owner_decision = Decision.REJECTED
        rule.report_owner_decided_by = current_user.user_id
        rule.report_owner_decided_at = datetime.utcnow()
        rule.report_owner_notes = f"{rejection_request.reason}: {rejection_request.notes}"
    else:
        # Admin can set either - default to tester
        rule.tester_decision = Decision.REJECTED
        rule.tester_decided_by = current_user.user_id
        rule.tester_decided_at = datetime.utcnow()
        rule.tester_notes = f"{rejection_request.reason}: {rejection_request.notes}"
    
    rule.updated_at = datetime.utcnow()
    rule.updated_by_id = current_user.user_id
    
    await db.commit()
    await db.refresh(rule)
    
    return {
        "success": True,
        "message": f"Rule '{rule.rule_name}' rejected",
        "rule_id": rule.rule_id,
        "status": rule.status,
        "can_revise": rejection_request.allow_revision
    }

@router.put("/cycles/{cycle_id}/reports/{report_id}/rules/{rule_id}/report-owner-decision")
async def update_report_owner_decision(
    cycle_id: int,
    report_id: int,
    rule_id: str,
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update report owner decision for a profiling rule"""
    
    # Verify user is a report owner
    if current_user.role not in ["Report Owner", "Report Owner Executive"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only report owners can make report owner decisions"
        )
    
    # Get the rule
    rule_query = select(ProfilingRule).where(
        ProfilingRule.rule_id == rule_id
    )
    
    rule_result = await db.execute(rule_query)
    rule = rule_result.scalars().first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    # Verify rule belongs to the cycle/report
    if rule.phase.cycle_id != cycle_id or rule.phase.report_id != report_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found for this cycle/report"
        )
    
    from app.models.data_profiling import Decision
    
    # Get decision from request
    decision_str = request.get("decision", "").lower()
    reason = request.get("reason", "")
    notes = request.get("notes", "")
    
    # Map decision string to lowercase database enum values
    if decision_str == "approve" or decision_str == "approved":
        decision = "approved"
    elif decision_str == "reject" or decision_str == "rejected":
        decision = "rejected"
    elif decision_str == "request_changes":
        decision = "request_changes"
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid decision: {decision_str}. Must be 'approved', 'rejected', or 'request_changes'"
        )
    
    # Update report owner decision
    rule.report_owner_decision = decision
    rule.report_owner_decided_by = current_user.user_id
    rule.report_owner_decided_at = datetime.utcnow()
    rule.report_owner_notes = f"{reason}: {notes}" if reason else notes
    
    # Update overall status based on decisions
    if rule.tester_decision == "approved" and rule.report_owner_decision == "approved":
        rule.status = ProfilingRuleStatus.APPROVED
    elif rule.tester_decision == "rejected" or rule.report_owner_decision == "rejected":
        rule.status = ProfilingRuleStatus.REJECTED
    elif rule.tester_decision == "approved" and rule.report_owner_decision is None:
        rule.status = ProfilingRuleStatus.SUBMITTED  # Keep as submitted if tester approved but RO hasn't decided
    else:
        rule.status = ProfilingRuleStatus.PENDING
    
    rule.updated_at = datetime.utcnow()
    rule.updated_by_id = current_user.user_id
    
    await db.commit()
    await db.refresh(rule)
    
    # Check if all rules in this version are now approved by both tester and report owner
    if decision == "approved":
        # Get all rules in the same version
        version_rules_query = select(ProfilingRule).where(
            ProfilingRule.version_id == rule.version_id
        )
        version_rules_result = await db.execute(version_rules_query)
        all_rules = version_rules_result.scalars().all()
        
        # Check if all rules are fully approved
        all_approved = all(
            r.tester_decision == "approved" and r.report_owner_decision == "approved"
            for r in all_rules
        )
        
        if all_approved:
            # Auto-finalize the version
            from app.models.data_profiling import DataProfilingRuleVersion, VersionStatus
            
            version_query = select(DataProfilingRuleVersion).where(
                DataProfilingRuleVersion.version_id == rule.version_id
            )
            version_result = await db.execute(version_query)
            version = version_result.scalar_one()
            
            version.version_status = VersionStatus.APPROVED
            version.approved_by_id = current_user.user_id
            version.approved_at = datetime.utcnow()
            version.updated_at = datetime.utcnow()
            version.updated_by_id = current_user.user_id
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Report owner decision recorded. All rules approved - version finalized!",
                "rule_id": rule.rule_id,
                "decision": decision,
                "status": rule.status.value,
                "version_finalized": True,
                "version_status": "approved"
            }
    
    return {
        "success": True,
        "message": f"Report owner decision recorded for rule '{rule.rule_name}'",
        "rule_id": rule.rule_id,
        "decision": decision,
        "status": rule.status.value
    }

@router.put("/rules/{rule_id}/reset-pending")
async def reset_rule_to_pending(
    rule_id: str,  # Changed from int to str to handle UUIDs
    db: AsyncSession = Depends(get_db)
):
    """Reset a rule back to pending status for re-review"""
    
    rule_query = select(ProfilingRule).where(
        ProfilingRule.rule_id == rule_id
    )
    
    rule_result = await db.execute(rule_query)
    rule = rule_result.scalars().first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found or not current version"
        )
    
    # Allow resetting from any status back to pending
    original_status = rule.status
    rule.status = ProfilingRuleStatus.PENDING
    
    # Clear approval/rejection fields
    rule.approved_by = None
    rule.approved_at = None
    rule.approval_notes = None
    rule.rejected_by = None
    rule.rejected_at = None
    rule.rejection_reason = None
    rule.rejection_notes = None
    
    rule.updated_at = datetime.utcnow()
    rule.updated_by = 1  # Test user ID
    
    await db.commit()
    await db.refresh(rule)
    
    return {
        "success": True,
        "message": f"Rule '{rule.rule_name}' reset to pending from {original_status}",
        "rule_id": rule.rule_id,
        "status": rule.status,
        "previous_status": original_status
    }

@router.put("/rules/{rule_id}/revise")
async def revise_profiling_rule(
    rule_id: str,  # Changed from int to str to handle UUIDs
    rule_update: ProfilingRuleUpdate,
    current_user: User = Depends(require_roles(['Tester', 'Test Executive'])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new version of a rejected rule (Tester workflow)"""
    
    original_rule_query = select(ProfilingRule).where(
        ProfilingRule.rule_id == rule_id
    )
    
    original_rule_result = await db.execute(original_rule_query)
    original_rule = original_rule_result.scalars().first()
    
    if not original_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original rule not found"
        )
    
    if original_rule.status != ProfilingRuleStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rule is not in a state that allows revision"
        )
    
    # Create new version using versioning mixin
    new_rule = original_rule.create_new_version(
        updated_by=current_user.user_id,
        **rule_update.dict(exclude_unset=True)
    )
    
    # Set new rule status
    new_rule.status = ProfilingRuleStatus.RESUBMITTED
    new_rule.revision_notes = rule_update.revision_notes
    new_rule.created_by = current_user.user_id
    new_rule.created_at = datetime.utcnow()
    
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    
    return {
        "success": True,
        "message": f"Rule '{new_rule.rule_name}' revised and resubmitted (v{new_rule.version_number})",
        "rule_id": new_rule.rule_id,
        "version": new_rule.version_number,
        "status": new_rule.status
    }

@router.get("/rules/{rule_id}/history", response_model=List[ProfilingRuleResponse])
async def get_rule_history(
    rule_id: str,  # Changed from int to str to handle UUIDs
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get version history for a specific rule"""
    
    # Get business key for this rule first
    business_key_query = select(ProfilingRule.business_key).where(
        ProfilingRule.rule_id == rule_id
    )
    business_key_result = await db.execute(business_key_query)
    business_key = business_key_result.scalar()
    
    if not business_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    # Get all versions of this rule
    rules_query = select(ProfilingRule).where(
        ProfilingRule.business_key == business_key
    ).order_by(desc(ProfilingRule.version_number))
    
    rules_result = await db.execute(rules_query)
    rules = rules_result.scalars().all()
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    return [ProfilingRuleResponse.from_orm(rule) for rule in rules]

@router.delete("/rules/{rule_id}")
async def delete_profiling_rule(
    rule_id: str,  # Changed from int to str to handle UUIDs
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a profiling rule (only for testers and admins)"""
    
    # Check permissions - only testers and admins can delete rules
    if current_user.role not in ['Tester', 'Test Executive', 'Admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only testers and admins can delete rules"
        )
    
    # Get the rule
    rule_query = select(ProfilingRule).where(
        ProfilingRule.rule_id == rule_id
    )
    
    rule_result = await db.execute(rule_query)
    rule = rule_result.scalars().first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )
    
    # Delete the rule
    await db.delete(rule)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Rule '{rule.rule_name}' deleted successfully",
        "rule_id": rule_id
    }

@router.post("/rules/bulk-approve")
async def bulk_approve_rules(
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk approve multiple rules"""
    
    from app.models.data_profiling import Decision
    
    rule_ids = request.get("rule_ids", [])
    notes = request.get("notes", "")
    
    if not rule_ids:
        raise HTTPException(status_code=400, detail="No rule IDs provided")
    
    rules_query = select(ProfilingRule).where(
        ProfilingRule.rule_id.in_(rule_ids)
    )
    
    rules_result = await db.execute(rules_query)
    rules = rules_result.scalars().all()
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No rules found with the provided IDs"
        )
    
    approved_count = 0
    for rule in rules:
        # Determine if user is tester or report owner based on role
        if current_user.role in ["Tester", "Test Executive"]:
            # Set tester approval
            rule.tester_decision = Decision.APPROVED
            rule.tester_decided_by = current_user.user_id
            rule.tester_decided_at = datetime.utcnow()
            rule.tester_notes = notes
        elif current_user.role in ["Report Owner", "Report Owner Executive"]:
            # Set report owner approval
            rule.report_owner_decision = Decision.APPROVED
            rule.report_owner_decided_by = current_user.user_id
            rule.report_owner_decided_at = datetime.utcnow()
            rule.report_owner_notes = notes
        else:
            # Admin can set either - default to tester
            rule.tester_decision = Decision.APPROVED
            rule.tester_decided_by = current_user.user_id
            rule.tester_decided_at = datetime.utcnow()
            rule.tester_notes = notes
        
        # Update status based on approvals
        # If tester approves, mark as submitted (ready for report owner review)
        # Only mark as fully approved when both approve
        if rule.tester_decision == Decision.APPROVED and rule.report_owner_decision == Decision.APPROVED:
            rule.status = ProfilingRuleStatus.APPROVED
        elif current_user.role in ["Tester", "Test Executive"] and rule.tester_decision == Decision.APPROVED:
            rule.status = ProfilingRuleStatus.SUBMITTED  # Tester approved, awaiting report owner
        elif current_user.role in ["Report Owner", "Report Owner Executive"] and rule.report_owner_decision == Decision.APPROVED:
            # Report owner approved but tester hasn't - keep as pending
            rule.status = ProfilingRuleStatus.PENDING
        
        rule.updated_at = datetime.utcnow()
        rule.updated_by_id = current_user.user_id
        approved_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Bulk approved {approved_count} rules",
        "approved_count": approved_count,
        "rule_ids": rule_ids
    }

@router.post("/rules/bulk-reject")
async def bulk_reject_rules(
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk reject multiple rules"""
    
    from app.models.data_profiling import Decision
    
    rule_ids = request.get("rule_ids", [])
    reason = request.get("reason", "")
    notes = request.get("notes", "")
    
    if not rule_ids:
        raise HTTPException(status_code=400, detail="No rule IDs provided")
    
    if not reason:
        raise HTTPException(status_code=400, detail="Reason is required for rejection")
    
    rules_query = select(ProfilingRule).where(
        ProfilingRule.rule_id.in_(rule_ids)
    )
    
    rules_result = await db.execute(rules_query)
    rules = rules_result.scalars().all()
    
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No rules found with the provided IDs"
        )
    
    rejected_count = 0
    for rule in rules:
        # Update rule status
        rule.status = ProfilingRuleStatus.REJECTED
        
        # Determine if user is tester or report owner based on role
        if current_user.role in ["Tester", "Test Executive"]:
            # Set tester rejection
            rule.tester_decision = Decision.REJECTED
            rule.tester_decided_by = current_user.user_id
            rule.tester_decided_at = datetime.utcnow()
            rule.tester_notes = f"{reason}: {notes}"
        elif current_user.role in ["Report Owner", "Report Owner Executive"]:
            # Set report owner rejection
            rule.report_owner_decision = Decision.REJECTED
            rule.report_owner_decided_by = current_user.user_id
            rule.report_owner_decided_at = datetime.utcnow()
            rule.report_owner_notes = f"{reason}: {notes}"
        else:
            # Admin can set either - default to tester
            rule.tester_decision = Decision.REJECTED
            rule.tester_decided_by = current_user.user_id
            rule.tester_decided_at = datetime.utcnow()
            rule.tester_notes = f"{reason}: {notes}"
        
        rule.updated_at = datetime.utcnow()
        rule.updated_by_id = current_user.user_id
        rejected_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Bulk rejected {rejected_count} rules",
        "rejected_count": rejected_count,
        "rule_ids": rule_ids
    }