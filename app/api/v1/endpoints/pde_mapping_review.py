"""
API endpoints for PDE Mapping Review and Approval workflow
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth import RoleChecker, UserRoles
from app.core.logging import get_logger
from app.models.user import User
from app.models.planning import PlanningPDEMapping as PDEMapping
from app.models.pde_mapping_review import (
    PDEMappingReview, 
    PDEMappingReviewHistory,
    PDEMappingApprovalRule,
    ReviewStatus,
    ReviewActionType
)
from app.schemas.pde_mapping_review import (
    PDEMappingReviewResponse,
    PDEMappingReviewCreateRequest,
    PDEMappingReviewUpdateRequest,
    PDEMappingReviewHistoryResponse,
    ApprovalRuleResponse,
    ApprovalRuleCreateRequest,
    BulkReviewRequest,
    ReviewSummaryResponse
)

logger = get_logger(__name__)
router = APIRouter()

# Role checks
tester_or_above = RoleChecker([UserRoles.TESTER, UserRoles.TEST_EXECUTIVE, UserRoles.ADMIN])
report_owner_or_above = RoleChecker([UserRoles.REPORT_OWNER, UserRoles.REPORT_OWNER_EXECUTIVE, UserRoles.TEST_EXECUTIVE, UserRoles.ADMIN])
test_executive_or_above = RoleChecker([UserRoles.TEST_EXECUTIVE, UserRoles.ADMIN])


# ===================== Review Management =====================

@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/{mapping_id}/submit-for-review")
async def submit_mapping_for_review(
    cycle_id: int,
    report_id: int,
    mapping_id: int,
    request: PDEMappingReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PDEMappingReviewResponse:
    """Submit a PDE mapping for review"""
    tester_or_above(current_user)
    
    # Get the PDE mapping
    mapping_query = select(PDEMapping).where(
        and_(
            PDEMapping.id == mapping_id,
            PDEMapping.cycle_id == cycle_id,
            PDEMapping.report_id == report_id
        )
    )
    mapping_result = await db.execute(mapping_query)
    mapping = mapping_result.scalar_one_or_none()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="PDE mapping not found")
    
    # Check if already under review
    existing_review_query = select(PDEMappingReview).where(
        and_(
            PDEMappingReview.pde_mapping_id == mapping_id,
            PDEMappingReview.is_latest == True,
            PDEMappingReview.review_status == ReviewStatus.PENDING
        )
    )
    existing_review_result = await db.execute(existing_review_query)
    if existing_review_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Mapping is already under review")
    
    # Mark any previous reviews as not latest
    await db.execute(
        PDEMappingReview.__table__.update()
        .where(PDEMappingReview.pde_mapping_id == mapping_id)
        .values(is_latest=False)
    )
    
    # Create new review
    review = PDEMappingReview(
        pde_mapping_id=mapping_id,
        submitted_by_id=current_user.user_id,
        review_notes=request.review_notes,
        created_by_id=current_user.user_id,
        updated_by_id=current_user.user_id
    )
    
    # Check for auto-approval based on rules
    should_auto_approve = await check_auto_approval(mapping, db)
    if should_auto_approve:
        review.review_status = ReviewStatus.APPROVED
        review.reviewed_by_id = current_user.user_id  # System approval
        review.reviewed_at = datetime.utcnow()
        review.auto_approved = True
        review.review_notes = "Auto-approved based on configured rules and high LLM confidence"
    
    db.add(review)
    
    # Add to history
    history = PDEMappingReviewHistory(
        pde_mapping_id=mapping_id,
        review_id=review.id,
        action_type=ReviewActionType.SUBMIT_FOR_REVIEW if not should_auto_approve else ReviewActionType.AUTO_APPROVE,
        action_by_id=current_user.user_id,
        new_status=review.review_status,
        action_notes=request.review_notes,
        created_by_id=current_user.user_id,
        updated_by_id=current_user.user_id
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(review)
    
    return PDEMappingReviewResponse.from_orm(review)


@router.put("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/{mapping_id}/review")
async def review_mapping(
    cycle_id: int,
    report_id: int,
    mapping_id: int,
    request: PDEMappingReviewUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PDEMappingReviewResponse:
    """Review (approve/reject) a PDE mapping"""
    report_owner_or_above(current_user)
    
    # Get the latest review
    review_query = select(PDEMappingReview).where(
        and_(
            PDEMappingReview.pde_mapping_id == mapping_id,
            PDEMappingReview.is_latest == True
        )
    )
    review_result = await db.execute(review_query)
    review = review_result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="No review found for this mapping")
    
    if review.review_status != ReviewStatus.PENDING:
        raise HTTPException(status_code=400, detail="Review has already been completed")
    
    # Update review
    previous_status = review.review_status
    review.review_status = request.review_status
    review.reviewed_by_id = current_user.user_id
    review.reviewed_at = datetime.utcnow()
    review.review_notes = request.review_notes
    review.revision_requested = request.revision_requested
    review.updated_by_id = current_user.user_id
    
    # Determine action type
    action_type = ReviewActionType.APPROVE if request.review_status == ReviewStatus.APPROVED else \
                  ReviewActionType.REJECT if request.review_status == ReviewStatus.REJECTED else \
                  ReviewActionType.REQUEST_REVISION
    
    # Add to history
    history = PDEMappingReviewHistory(
        pde_mapping_id=mapping_id,
        review_id=review.id,
        action_type=action_type,
        action_by_id=current_user.user_id,
        previous_status=previous_status,
        new_status=request.review_status,
        action_notes=request.review_notes,
        created_by_id=current_user.user_id,
        updated_by_id=current_user.user_id
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(review)
    
    return PDEMappingReviewResponse.from_orm(review)


@router.get("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/reviews/pending")
async def get_pending_reviews(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[PDEMappingReviewResponse]:
    """Get all pending reviews for a cycle/report"""
    report_owner_or_above(current_user)
    
    query = select(PDEMappingReview).join(
        PDEMapping, PDEMappingReview.pde_mapping_id == PDEMapping.id
    ).where(
        and_(
            PDEMapping.cycle_id == cycle_id,
            PDEMapping.report_id == report_id,
            PDEMappingReview.is_latest == True,
            PDEMappingReview.review_status == ReviewStatus.PENDING
        )
    )
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return [PDEMappingReviewResponse.from_orm(review) for review in reviews]


@router.post("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/reviews/bulk")
async def bulk_review_mappings(
    cycle_id: int,
    report_id: int,
    request: BulkReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Bulk approve/reject multiple PDE mappings"""
    report_owner_or_above(current_user)
    
    processed = 0
    errors = []
    
    for mapping_id in request.mapping_ids:
        try:
            # Get the latest review
            review_query = select(PDEMappingReview).join(
                PDEMapping, PDEMappingReview.pde_mapping_id == PDEMapping.id
            ).where(
                and_(
                    PDEMapping.id == mapping_id,
                    PDEMapping.cycle_id == cycle_id,
                    PDEMapping.report_id == report_id,
                    PDEMappingReview.is_latest == True,
                    PDEMappingReview.review_status == ReviewStatus.PENDING
                )
            )
            review_result = await db.execute(review_query)
            review = review_result.scalar_one_or_none()
            
            if review:
                previous_status = review.review_status
                review.review_status = request.review_status
                review.reviewed_by_id = current_user.user_id
                review.reviewed_at = datetime.utcnow()
                review.review_notes = request.review_notes or f"Bulk {request.action}"
                review.updated_by_id = current_user.user_id
                
                # Add to history
                history = PDEMappingReviewHistory(
                    pde_mapping_id=mapping_id,
                    review_id=review.id,
                    action_type=ReviewActionType.APPROVE if request.action == 'approve' else ReviewActionType.REJECT,
                    action_by_id=current_user.user_id,
                    previous_status=previous_status,
                    new_status=request.review_status,
                    action_notes=f"Bulk {request.action}",
                    created_by_id=current_user.user_id,
                    updated_by_id=current_user.user_id
                )
                db.add(history)
                processed += 1
            else:
                errors.append(f"No pending review found for mapping {mapping_id}")
                
        except Exception as e:
            errors.append(f"Error processing mapping {mapping_id}: {str(e)}")
    
    await db.commit()
    
    return {
        "processed": processed,
        "errors": errors,
        "success": len(errors) == 0
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/reviews/summary")
async def get_review_summary(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReviewSummaryResponse:
    """Get summary of review statuses for all PDE mappings"""
    tester_or_above(current_user)
    
    # Count mappings by review status
    status_counts_query = select(
        PDEMappingReview.review_status,
        func.count(PDEMappingReview.id).label('count')
    ).join(
        PDEMapping, PDEMappingReview.pde_mapping_id == PDEMapping.id
    ).where(
        and_(
            PDEMapping.cycle_id == cycle_id,
            PDEMapping.report_id == report_id,
            PDEMappingReview.is_latest == True
        )
    ).group_by(PDEMappingReview.review_status)
    
    status_counts_result = await db.execute(status_counts_query)
    status_counts = {row.review_status: row.count for row in status_counts_result}
    
    # Count total mappings
    total_mappings_query = select(func.count(PDEMapping.id)).where(
        and_(
            PDEMapping.cycle_id == cycle_id,
            PDEMapping.report_id == report_id
        )
    )
    total_mappings_result = await db.execute(total_mappings_query)
    total_mappings = total_mappings_result.scalar()
    
    # Count mappings without reviews
    mappings_without_review = total_mappings - sum(status_counts.values())
    
    # Count auto-approved
    auto_approved_query = select(func.count(PDEMappingReview.id)).join(
        PDEMapping, PDEMappingReview.pde_mapping_id == PDEMapping.id
    ).where(
        and_(
            PDEMapping.cycle_id == cycle_id,
            PDEMapping.report_id == report_id,
            PDEMappingReview.is_latest == True,
            PDEMappingReview.auto_approved == True
        )
    )
    auto_approved_result = await db.execute(auto_approved_query)
    auto_approved_count = auto_approved_result.scalar()
    
    return ReviewSummaryResponse(
        total_mappings=total_mappings,
        pending=status_counts.get(ReviewStatus.PENDING, 0),
        approved=status_counts.get(ReviewStatus.APPROVED, 0),
        rejected=status_counts.get(ReviewStatus.REJECTED, 0),
        needs_revision=status_counts.get(ReviewStatus.NEEDS_REVISION, 0),
        not_submitted=mappings_without_review,
        auto_approved=auto_approved_count
    )


@router.get("/cycles/{cycle_id}/reports/{report_id}/pde-mappings/{mapping_id}/review-history")
async def get_review_history(
    cycle_id: int,
    report_id: int,
    mapping_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[PDEMappingReviewHistoryResponse]:
    """Get review history for a PDE mapping"""
    tester_or_above(current_user)
    
    query = select(PDEMappingReviewHistory).where(
        PDEMappingReviewHistory.pde_mapping_id == mapping_id
    ).order_by(PDEMappingReviewHistory.action_at.desc())
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    return [PDEMappingReviewHistoryResponse.from_orm(h) for h in history]


# ===================== Approval Rules =====================

@router.get("/cycles/{cycle_id}/reports/{report_id}/approval-rules")
async def get_approval_rules(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ApprovalRuleResponse]:
    """Get approval rules for a cycle/report"""
    test_executive_or_above(current_user)
    
    query = select(PDEMappingApprovalRule).where(
        or_(
            and_(
                PDEMappingApprovalRule.cycle_id == cycle_id,
                PDEMappingApprovalRule.report_id == report_id
            ),
            and_(
                PDEMappingApprovalRule.cycle_id.is_(None),
                PDEMappingApprovalRule.report_id.is_(None)
            )  # Global rules
        )
    ).order_by(PDEMappingApprovalRule.priority)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [ApprovalRuleResponse.from_orm(rule) for rule in rules]


@router.post("/cycles/{cycle_id}/reports/{report_id}/approval-rules")
async def create_approval_rule(
    cycle_id: int,
    report_id: int,
    request: ApprovalRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApprovalRuleResponse:
    """Create a new approval rule"""
    test_executive_or_above(current_user)
    
    rule = PDEMappingApprovalRule(
        cycle_id=cycle_id,
        report_id=report_id,
        rule_name=request.rule_name,
        rule_description=request.rule_description,
        is_active=request.is_active,
        min_llm_confidence=request.min_llm_confidence,
        require_data_source=request.require_data_source,
        require_business_metadata=request.require_business_metadata,
        auto_approve_cde=request.auto_approve_cde,
        auto_approve_primary_key=request.auto_approve_primary_key,
        auto_approve_public_classification=request.auto_approve_public_classification,
        max_risk_score_for_auto_approval=request.max_risk_score_for_auto_approval,
        priority=request.priority,
        created_by_id=current_user.user_id,
        updated_by_id=current_user.user_id
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return ApprovalRuleResponse.from_orm(rule)


# ===================== Helper Functions =====================

async def check_auto_approval(mapping: PDEMapping, db: AsyncSession) -> bool:
    """Check if a mapping qualifies for auto-approval based on rules"""
    
    # Get applicable rules
    rules_query = select(PDEMappingApprovalRule).where(
        and_(
            PDEMappingApprovalRule.is_active == True,
            or_(
                and_(
                    PDEMappingApprovalRule.cycle_id == mapping.cycle_id,
                    PDEMappingApprovalRule.report_id == mapping.report_id
                ),
                and_(
                    PDEMappingApprovalRule.cycle_id.is_(None),
                    PDEMappingApprovalRule.report_id.is_(None)
                )
            )
        )
    ).order_by(PDEMappingApprovalRule.priority)
    
    rules_result = await db.execute(rules_query)
    rules = rules_result.scalars().all()
    
    if not rules:
        # Default rule: auto-approve if LLM confidence >= 85
        return mapping.llm_confidence_score and mapping.llm_confidence_score >= 85
    
    # Check each rule
    for rule in rules:
        # Check LLM confidence
        if mapping.llm_confidence_score and mapping.llm_confidence_score < rule.min_llm_confidence:
            continue
            
        # Check data source requirement
        if rule.require_data_source and not mapping.data_source_id:
            continue
            
        # Check business metadata requirement
        if rule.require_business_metadata and not (mapping.business_process or mapping.business_owner):
            continue
            
        # Check attribute properties
        if mapping.attribute:
            # Auto-approve CDEs if configured
            if rule.auto_approve_cde and mapping.attribute.cde_flag:
                return True
                
            # Auto-approve primary keys if configured
            if rule.auto_approve_primary_key and mapping.attribute.is_primary_key:
                return True
                
            # Auto-approve public classification if configured
            if rule.auto_approve_public_classification and \
               mapping.attribute.information_security_classification == 'Public':
                return True
                
            # Check risk score
            if mapping.attribute.risk_score and \
               mapping.attribute.risk_score > rule.max_risk_score_for_auto_approval:
                continue
        
        # If we get here, all conditions are met
        return True
    
    return False