"""
Scoping phase endpoints for workflow management
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, exists
from sqlalchemy.orm import selectinload
import logging
import time
import json
import asyncio
from datetime import datetime
from pathlib import Path

from app.core.database import get_db
from app.core.dependencies import get_current_user
# RoleChecker import removed - using @require_permission decorator instead
from app.core.permissions import require_permission
from app.models.user import User
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport
from app.models.report import Report
from app.models.workflow import WorkflowPhase
from app.models.report_attribute import ReportAttribute
from app.models.scoping import (
    AttributeScopingRecommendation, TesterScopingDecision, 
    ScopingSubmission, ReportOwnerScopingReview, ScopingAuditLog
)
from app.schemas.scoping import (
    LLMScopingRequest, LLMScopingResponse, AttributeScopingRecommendation as AttributeScopingRecommendationSchema,
    TesterScopingDecision as TesterScopingDecisionSchema, TesterScopingSubmission,
    ReportOwnerScopingReview as ReportOwnerScopingReviewSchema,
    ScopingPhaseStatus, AttributeScopingStatus, ScopingPhaseStart, ScopingPhaseComplete,
    ScopingSummary, ScopingRecommendation, ScopingDecision, ApprovalStatus
)
from app.services.llm_service import get_llm_service
from app.core.background_jobs import job_manager
from app.models.lob import LOB

router = APIRouter()
logger = logging.getLogger(__name__)

def calculate_local_risk_score(attr, cde_attributes: List[str], historical_issue_attributes: List[str], llm_risk_score: Optional[float] = None) -> float:
    """
    Simplified risk scoring methodology using only 4 key factors:
    
    WHEN LLM SCORE IS AVAILABLE (0-100 scale):
    - LLM Recommendation: 50 points (highest weight)
    - CDE Status: 20 points 
    - Historical Issues: 20 points
    - Mandatory Flag: 10 points
    
    WHEN LLM SCORE IS NOT AVAILABLE (0-100 scale):
    - CDE Status: 40 points (scaled up)
    - Historical Issues: 40 points (scaled up)
    - Mandatory Flag: 20 points (scaled up)
    
    DATA SOURCES:
    ✅ FROM DATABASE: cde_flag, historical_issues_flag, mandatory_flag, risk_score
    """
    
    # Initialize scores
    llm_score = 0.0
    cde_score = 0.0
    historical_score = 0.0
    mandatory_score = 0.0
    
    # Check if LLM score is available and valid
    has_llm_score = llm_risk_score is not None and llm_risk_score > 0
    
    if has_llm_score:
        # WITH LLM SCORE: Use original weights
        # LLM RECOMMENDATION (0-50 points) - Highest weight
        if llm_risk_score >= 80:
            llm_score = 50.0  # Very high risk
        elif llm_risk_score >= 60:
            llm_score = 40.0  # High risk
        elif llm_risk_score >= 40:
            llm_score = 30.0  # Medium risk
        elif llm_risk_score >= 20:
            llm_score = 20.0  # Low risk
        else:
            llm_score = 10.0  # Very low risk
        
        # CDE STATUS (0-20 points)
        if attr.attribute_name in cde_attributes:
            cde_score = 20.0
        
        # HISTORICAL ISSUES (0-20 points)
        if attr.attribute_name in historical_issue_attributes:
            historical_score = 20.0
        
        # MANDATORY FLAG (0-10 points)
        if attr.mandatory_flag == 'Mandatory':
            mandatory_score = 10.0
        elif attr.mandatory_flag == 'Conditional':
            mandatory_score = 5.0
        else:  # Optional
            mandatory_score = 2.0
        
        logger.debug(f"WITH LLM - {attr.attribute_name}: LLM={llm_score}, CDE={cde_score}, Historical={historical_score}, Mandatory={mandatory_score}")
        
    else:
        # WITHOUT LLM SCORE: Scale up the other 3 factors
        # CDE STATUS (0-40 points) - Scaled up
        if attr.attribute_name in cde_attributes:
            cde_score = 40.0
        
        # HISTORICAL ISSUES (0-40 points) - Scaled up
        if attr.attribute_name in historical_issue_attributes:
            historical_score = 40.0
        
        # MANDATORY FLAG (0-20 points) - Scaled up
        if attr.mandatory_flag == 'Mandatory':
            mandatory_score = 20.0
        elif attr.mandatory_flag == 'Conditional':
            mandatory_score = 10.0
        else:  # Optional
            mandatory_score = 5.0
        
        logger.debug(f"WITHOUT LLM - {attr.attribute_name}: CDE={cde_score}, Historical={historical_score}, Mandatory={mandatory_score}")
    
    # Calculate final score
    total_score = llm_score + cde_score + historical_score + mandatory_score
    
    # Ensure score is within 0-100 range
    final_score = min(max(total_score, 0.0), 100.0)
    
    logger.info(f"Simplified risk scoring for {attr.attribute_name}: "
                f"LLM={llm_score}, CDE={cde_score}, Historical={historical_score}, "
                f"Mandatory={mandatory_score}, Final={final_score}")
    
    return final_score


def get_regulation_prompt_path(report) -> Path:
    """
    Map report to specific regulation prompt based on report metadata
    
    PROMPT MAPPING STRATEGY:
    1. Primary: report.regulation + report.schedule 
    2. Fallback: report.regulation only
    3. Default: FR Y-14M Schedule D.1
    
    SUPPORTED MAPPINGS:
    - FR Y-14M Schedule D.1 → fr_y_14m/schedule_d_1/scoping_recommendations.txt
    - FR Y-14M Schedule D.2 → fr_y_14m/schedule_d_2/scoping_recommendations.txt  
    - FR Y-14A Schedule A → fr_y_14a/schedule_a/scoping_recommendations.txt
    - CCAR → ccar/general/scoping_recommendations.txt
    """
    base_path = Path(__file__).parent.parent.parent.parent / "prompts" / "regulatory"
    
    logger.info(f"🗺️  REPORT-TO-PROMPT MAPPING:")
    logger.info(f"   📋 Report ID: {report.report_id}")
    logger.info(f"   📋 Report Name: {report.report_name}")
    logger.info(f"   📋 Regulation: {report.regulation}")
    
    # Normalize regulation string
    regulation = (report.regulation or "").strip().upper()
    schedule = getattr(report, 'schedule', None) or getattr(report, 'sub_schedule', None) or ""
    schedule = schedule.strip().upper()
    
    logger.info(f"   🏷️  Normalized Regulation: '{regulation}'")
    logger.info(f"   🏷️  Normalized Schedule: '{schedule}'")
    
    # REGULATION-SPECIFIC MAPPINGS
    prompt_mappings = {
        # FR Y-14M mappings
        ("FR Y-14M", "D.1"): "fr_y_14m/schedule_d_1/scoping_recommendations.txt",
        ("FR Y-14M", "D.2"): "fr_y_14m/schedule_d_2/scoping_recommendations.txt", 
        ("FR Y-14M", "SCHEDULE D.1"): "fr_y_14m/schedule_d_1/scoping_recommendations.txt",
        ("FR Y-14M", "SCHEDULE D.2"): "fr_y_14m/schedule_d_2/scoping_recommendations.txt",
        ("FR Y-14M", ""): "fr_y_14m/schedule_d_1/scoping_recommendations.txt",  # Default to D.1
        
        # FR Y-14A mappings  
        ("FR Y-14A", "A"): "fr_y_14a/schedule_a/scoping_recommendations.txt",
        ("FR Y-14A", "SCHEDULE A"): "fr_y_14a/schedule_a/scoping_recommendations.txt",
        ("FR Y-14A", ""): "fr_y_14a/schedule_a/scoping_recommendations.txt",
        
        # CCAR mappings
        ("CCAR", ""): "ccar/general/scoping_recommendations.txt",
        ("COMPREHENSIVE CAPITAL ANALYSIS AND REVIEW", ""): "ccar/general/scoping_recommendations.txt",
        
        # DFAST mappings
        ("DFAST", ""): "dfast/general/scoping_recommendations.txt",
        ("DODD-FRANK ACT STRESS TEST", ""): "dfast/general/scoping_recommendations.txt",
    }
    
    # Try exact match first
    mapping_key = (regulation, schedule)
    if mapping_key in prompt_mappings:
        prompt_file = prompt_mappings[mapping_key]
        prompt_path = base_path / prompt_file
        logger.info(f"   ✅ EXACT MATCH: {mapping_key} → {prompt_file}")
        
        if prompt_path.exists():
            logger.info(f"   ✅ PROMPT FILE EXISTS: {prompt_path}")
            return prompt_path
        else:
            logger.warning(f"   ⚠️  PROMPT FILE NOT FOUND: {prompt_path}")
    
    # Try regulation without schedule
    fallback_key = (regulation, "")
    if fallback_key in prompt_mappings:
        prompt_file = prompt_mappings[fallback_key]
        prompt_path = base_path / prompt_file
        logger.info(f"   🔄 FALLBACK MATCH: {fallback_key} → {prompt_file}")
        
        if prompt_path.exists():
            logger.info(f"   ✅ FALLBACK PROMPT EXISTS: {prompt_path}")
            return prompt_path
    
    # Try partial matches for common variations
    for (reg_pattern, sched_pattern), prompt_file in prompt_mappings.items():
        if reg_pattern in regulation or regulation in reg_pattern:
            if not schedule or sched_pattern in schedule or schedule in sched_pattern:
                prompt_path = base_path / prompt_file
                logger.info(f"   🔍 PARTIAL MATCH: '{regulation}' matches '{reg_pattern}' → {prompt_file}")
                
                if prompt_path.exists():
                    logger.info(f"   ✅ PARTIAL MATCH PROMPT EXISTS: {prompt_path}")
                    return prompt_path
    
    # Default fallback to FR Y-14M Schedule D.1
    default_path = base_path / "fr_y_14m/schedule_d_1/scoping_recommendations.txt"
    logger.info(f"   🎯 DEFAULT FALLBACK: {default_path}")
    
    if default_path.exists():
        logger.info(f"   ✅ DEFAULT PROMPT EXISTS: {default_path}")
        return default_path
    else:
        logger.error(f"   ❌ DEFAULT PROMPT NOT FOUND: {default_path}")
        available_prompts = list(base_path.rglob("*.txt"))
        logger.error(f"   📁 Available prompts: {[str(p.relative_to(base_path)) for p in available_prompts]}")
        raise FileNotFoundError(f"No regulation prompt found for {regulation} {schedule}")


# Create role checking dependency functions
async def require_tester(current_user: Any = Depends(get_current_user)) -> Any:
    """Require tester role"""
    if current_user.role != "Tester":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Tester role required."
        )
    return current_user

async def require_report_owner(current_user: Any = Depends(get_current_user)) -> Any:
    """Require report owner role"""
    if current_user.role != "Report Owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Report Owner role required."
        )
    return current_user

async def require_tester_or_report_owner(current_user: Any = Depends(get_current_user)) -> Any:
    """Require tester or report owner role"""
    if current_user.role not in ["Tester", "Report Owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Tester or Report Owner role required."
        )
    return current_user


@router.post("/{cycle_id}/reports/{report_id}/start", response_model=dict)
async def start_scoping_phase(
    cycle_id: int,
    report_id: int,
    request: ScopingPhaseStart,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester)
):
    """Start scoping phase for a report"""
    
    # Verify cycle report assignment and tester access
    cycle_report_query = select(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id,
            CycleReport.tester_id == current_user.user_id
        )
    )
    result = await db.execute(cycle_report_query)
    cycle_report = result.scalar_one_or_none()
    
    if not cycle_report:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report or report not assigned"
        )
    
    # Check if planning phase is complete
    planning_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == 'Planning'
        )
    )
    result = await db.execute(planning_phase_query)
    planning_phase = result.scalar_one_or_none()
    
    if not planning_phase or planning_phase.status != 'Complete':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planning phase must be completed before starting scoping"
        )
    
    # Check if scoping phase already exists
    scoping_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == 'Scoping'
        )
    )
    result = await db.execute(scoping_phase_query)
    scoping_phase = result.scalar_one_or_none()
    
    if scoping_phase and scoping_phase.status != 'Not Started':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scoping phase already started"
        )
    
    # Create or update scoping phase
    if not scoping_phase:
        scoping_phase = WorkflowPhase(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name='Scoping',
            status='In Progress',
            planned_start_date=request.planned_start_date.date() if request.planned_start_date else None,
            planned_end_date=request.planned_end_date.date() if request.planned_end_date else None,
            actual_start_date=datetime.utcnow()
        )
        db.add(scoping_phase)
    else:
        scoping_phase.status = 'In Progress'
        scoping_phase.actual_start_date = datetime.utcnow()
        if request.planned_start_date:
            scoping_phase.planned_start_date = request.planned_start_date.date()
        if request.planned_end_date:
            scoping_phase.planned_end_date = request.planned_end_date.date()
    
    # Log audit trail
    audit_log = ScopingAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        action="scoping_phase_started",
        performed_by=current_user.user_id,
        details={
            "notes": request.notes,
            "planned_start_date": request.planned_start_date.isoformat() if request.planned_start_date else None,
            "planned_end_date": request.planned_end_date.isoformat() if request.planned_end_date else None
        }
    )
    db.add(audit_log)
    
    await db.commit()
    
    logger.info(f"Scoping phase started for report {report_id} in cycle {cycle_id} by {current_user.email}")
    
    return {
        "message": "Scoping phase started successfully",
        "cycle_id": cycle_id,
        "report_id": report_id,
        "phase_status": "In Progress",
        "started_at": scoping_phase.actual_start_date.isoformat()
    }


@router.get("/{cycle_id}/reports/{report_id}/status", response_model=ScopingPhaseStatus)
async def get_scoping_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester_or_report_owner)
):
    """Get scoping phase status"""
    
    # Verify access
    if current_user.role == "Report Owner":
        # Verify report ownership
        report_query = select(Report).where(
            and_(
                Report.report_id == report_id,
                Report.report_owner_id == current_user.user_id
            )
        )
        result = await db.execute(report_query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    
    # Get scoping phase
    scoping_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == 'Scoping'
        )
    )
    result = await db.execute(scoping_phase_query)
    scoping_phase = result.scalar_one_or_none()
    
    if not scoping_phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoping phase not found"
        )
    
    # Get attribute counts
    total_attributes_query = select(func.count(ReportAttribute.attribute_id)).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id
        )
    )
    result = await db.execute(total_attributes_query)
    total_attributes = result.scalar() or 0
    
    # Get recommendations count
    recommendations_query = select(func.count(AttributeScopingRecommendation.recommendation_id)).where(
        and_(
            AttributeScopingRecommendation.cycle_id == cycle_id,
            AttributeScopingRecommendation.report_id == report_id
        )
    )
    result = await db.execute(recommendations_query)
    attributes_with_recommendations = result.scalar() or 0
    
    # Get decisions count
    decisions_query = select(func.count(TesterScopingDecision.decision_id)).where(
        and_(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id
        )
    )
    result = await db.execute(decisions_query)
    attributes_with_decisions = result.scalar() or 0
    
    # Get scoped attributes count
    scoped_query = select(func.count(TesterScopingDecision.decision_id)).where(
        and_(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id,
            TesterScopingDecision.final_scoping == True
        )
    )
    result = await db.execute(scoped_query)
    attributes_scoped_for_testing = result.scalar() or 0
    
    # Get submission status
    submission_query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.created_at.desc())
    result = await db.execute(submission_query)
    latest_submission = result.scalars().first()
    
    submission_status = "Not Submitted"
    approval_status = None
    
    if latest_submission:
        submission_status = "Submitted"
        
        # Get latest review
        review_query = select(ReportOwnerScopingReview).where(
            ReportOwnerScopingReview.submission_id == latest_submission.submission_id
        ).order_by(ReportOwnerScopingReview.created_at.desc())
        result = await db.execute(review_query)
        latest_review = result.scalar_one_or_none()
        
        if latest_review:
            approval_status = latest_review.approval_status
    
    # Determine capabilities
    can_generate_recommendations = (
        scoping_phase.status == 'In Progress' and 
        total_attributes > 0 and
        current_user.role == "Tester"
    )
    
    can_submit_for_approval = (
        scoping_phase.status == 'In Progress' and
        attributes_with_recommendations > 0 and  # LLM recommendations exist
        total_attributes > 0 and
        current_user.role == "Tester" and
        not latest_submission  # No submission exists yet (or allow resubmission if feedback exists)
    )
    
    # Check if tester can resubmit based on feedback
    can_resubmit = False
    if current_user.role == "Tester" and latest_submission and latest_review:
        can_resubmit = latest_review.approval_status in ['Declined', 'Needs Revision']
    
    can_complete_phase = (
        approval_status == ApprovalStatus.APPROVED and
        current_user.role == "Tester"
    )
    
    # Completion requirements
    completion_requirements = []
    if total_attributes == 0:
        completion_requirements.append("At least one attribute must exist")
    if attributes_with_decisions < total_attributes:
        completion_requirements.append(f"Scoping decisions are auto-saved as you select attributes. {attributes_with_decisions}/{total_attributes} attributes have decisions.")
    if not latest_submission:
        completion_requirements.append("Select at least 1 non-primary key attribute, then submit for Report Owner approval")
    elif can_resubmit:
        completion_requirements.append("Address Report Owner feedback and resubmit")
    elif approval_status != ApprovalStatus.APPROVED:
        completion_requirements.append("Report Owner approval required")
    
    return ScopingPhaseStatus(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_status=scoping_phase.status,
        total_attributes=total_attributes,
        attributes_with_recommendations=attributes_with_recommendations,
        attributes_with_decisions=attributes_with_decisions,
        attributes_scoped_for_testing=attributes_scoped_for_testing,
        submission_status=submission_status,
        approval_status=approval_status,
        can_generate_recommendations=can_generate_recommendations,
        can_submit_for_approval=can_submit_for_approval,
        can_complete_phase=can_complete_phase,
        completion_requirements=completion_requirements,
        can_resubmit=can_resubmit,
        latest_submission_version=latest_submission.version if latest_submission else None
    )


@router.post("/{cycle_id}/reports/{report_id}/recommendations", response_model=dict)
async def generate_llm_recommendations(
    cycle_id: int,
    report_id: int,
    request: LLMScopingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester)
):
    """Generate LLM scoping recommendations for existing attributes (non-blocking background job)"""
    
    logger.info("=== STARTING LLM SCOPING RECOMMENDATIONS (BACKGROUND) ===")
    
    # Verify cycle report assignment
    cycle_report_query = select(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id
        )
    )
    cycle_report = (await db.execute(cycle_report_query)).scalar_one_or_none()
    if not cycle_report:
        raise HTTPException(status_code=404, detail="Report not found in cycle")
    
    # Get report details for context
    report_query = select(Report).where(Report.report_id == report_id)
    report = (await db.execute(report_query)).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get all attributes for this report
    attributes_query = select(ReportAttribute).where(ReportAttribute.report_id == report_id)
    all_attributes = (await db.execute(attributes_query)).scalars().all()
    
    if not all_attributes:
        raise HTTPException(status_code=400, detail="No attributes found for this report")
    
    # Create background job
    job_id = job_manager.create_job(
        job_type="scoping_recommendations",
        metadata={
            "cycle_id": cycle_id,
            "report_id": report_id,
            "user_id": current_user.user_id,
            "total_attributes": len(all_attributes),
            "request_params": {
                "use_historical_data": request.use_historical_data,
                "include_cde_priority": request.include_cde_priority,
                "include_historical_issues": request.include_historical_issues,
                "additional_context": request.additional_context
            }
        }
    )
    
    logger.info(f"🚀 Created background job {job_id} for {len(all_attributes)} attributes")
    
    # Start the background job
    asyncio.create_task(_run_scoping_generation_job(
        job_id, cycle_id, report_id, request, current_user.user_id
    ))
    
    return {
        "job_id": job_id,
        "message": f"Scoping generation started for {len(all_attributes)} attributes",
        "total_attributes": len(all_attributes),
        "estimated_time": f"{len(all_attributes) // 20 + 1} batches"
    }


async def _run_scoping_generation_job(job_id: str, cycle_id: int, report_id: int, request: LLMScopingRequest, user_id: int):
    """Background job function for LLM scoping generation with progress tracking"""
    
    logger.info(f"🚀 STARTING BACKGROUND SCOPING JOB {job_id}")
    
    try:
        # Get database session for background job
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            
            # Update job status to running
            job_manager.update_job_progress(
                job_id,
                status="running",
                progress_percentage=5,
                current_step="Initializing",
                message="Loading attributes and preparing for LLM analysis"
            )
            
            # Get report and attributes
            report_query = select(Report).where(Report.report_id == report_id)
            report = (await db.execute(report_query)).scalar_one_or_none()
            
            attributes_query = select(ReportAttribute).where(ReportAttribute.report_id == report_id)
            all_attributes = (await db.execute(attributes_query)).scalars().all()
            
            if not all_attributes:
                job_manager.complete_job(job_id, error="No attributes found for this report")
                return
            
            logger.info(f"📊 Processing {len(all_attributes)} attributes for job {job_id}")
            
            # Build CDE and historical issue lists
            cde_attributes = [attr.attribute_name for attr in all_attributes if attr.cde_flag]
            historical_issue_attributes = [attr.attribute_name for attr in all_attributes if attr.historical_issues_flag]
            
            # Update progress - total steps includes both LLM analysis and result processing
            total_processing_steps = len(all_attributes) * 2  # LLM analysis + result processing
            job_manager.update_job_progress(
                job_id,
                progress_percentage=10,
                current_step="Starting LLM Analysis",
                message=f"Processing {len(all_attributes)} attributes in batches of 20",
                total_steps=total_processing_steps
            )
            
            # Get LLM service
            llm_service = get_llm_service()
            provider = await llm_service.get_analysis_provider()
            
            logger.info(f"🔄 Using {provider.model_name} for scoping analysis")
            
            # Process attributes in batches of 20 (reduced from 30)
            batch_size = 20
            all_llm_results = []
            total_batches = (len(all_attributes) + batch_size - 1) // batch_size
            
            for batch_num, batch_start in enumerate(range(0, len(all_attributes), batch_size), 1):
                batch_end = min(batch_start + batch_size, len(all_attributes))
                batch_attributes = all_attributes[batch_start:batch_end]
                
                # Update progress for current batch
                batch_progress = 10 + (batch_num - 1) * 70 // total_batches
                job_manager.update_job_progress(
                    job_id,
                    progress_percentage=batch_progress,
                    current_step=f"Processing Batch {batch_num}/{total_batches}",
                    message=f"Analyzing attributes {batch_start+1}-{batch_end} using {provider.model_name}",
                    completed_steps=batch_start
                )
                
                logger.info(f"🔄 Processing batch {batch_num}/{total_batches}: attributes {batch_start+1}-{batch_end}")
                
                # Build simplified scoping prompt for this batch
                scoping_prompt = f"""
You are an expert regulatory compliance analyst. Analyze these {len(batch_attributes)} attributes for testing scope recommendations.

REPORT CONTEXT:
- Report: {report.report_name}
- Regulation: {report.regulation or 'FR Y-14M Schedule D.1'}
- Batch: {batch_start+1}-{batch_end} of {len(all_attributes)} total attributes

ATTRIBUTES TO ANALYZE:
{json.dumps([{
    "attribute_name": attr.attribute_name,
    "mdrm": attr.mdrm or "No MDRM code"
} for attr in batch_attributes], indent=2)}

SCOPING CONTEXT:
- CDE Attributes ({len(cde_attributes)}): {cde_attributes[:10]}{'...' if len(cde_attributes) > 10 else ''}
- Historical Issues ({len(historical_issue_attributes)}): {historical_issue_attributes[:10]}{'...' if len(historical_issue_attributes) > 10 else ''}
- Use Historical Data: {request.use_historical_data}
- Include CDE Priority: {request.include_cde_priority}
- Include Historical Issues: {request.include_historical_issues}
- Additional Context: {request.additional_context or 'None'}

TASK:
For each attribute, provide scoping recommendation in this exact JSON format:
[
  {{
    "attribute_name": "exact_attribute_name",
    "format": "String|Integer|Decimal|Date|DateTime|Boolean|JSON",
    "description": "Clear description of the field",
    "risk_score": 75,
    "rationale": "Specific rationale citing regulatory requirements",
    "validation_rules": "Format requirements, valid values, constraints",
    "typical_source_documents": "Credit card system, loan servicing platform",
    "keywords_to_look_for": "Account #, Card Number, Customer ID"
  }}
]

IMPORTANT: For the "format" field, use ONLY these exact values:
- "String" - for text, alphanumeric, IDs, codes
- "Integer" - for whole numbers, counts, flags (0/1)
- "Decimal" - for monetary amounts, percentages, rates, any decimal numbers
- "Date" - for dates only (YYYY-MM-DD)
- "DateTime" - for timestamps with time components
- "Boolean" - for true/false, yes/no values
- "JSON" - for complex objects or arrays

Return only the JSON array, no other text.
"""

                try:
                    # Make LLM call for this batch
                    llm_response = await provider.generate(
                        prompt=scoping_prompt,
                        system_prompt="You are an expert regulatory compliance analyst specializing in risk-based testing scope recommendations."
                    )
                    
                    # Extract content from LLM response
                    if isinstance(llm_response, dict) and "content" in llm_response:
                        response = llm_response["content"]
                    else:
                        response = str(llm_response)
                    
                    logger.info(f"✅ Batch {batch_num} LLM response: {len(response)} characters")
                    
                    # Parse batch LLM response
                    try:
                        import re
                        json_match = re.search(r'\[.*\]', response, re.DOTALL)
                        if json_match:
                            batch_llm_results = json.loads(json_match.group())
                        else:
                            batch_llm_results = json.loads(response)
                            
                        logger.info(f"📊 Batch {batch_num}: Parsed {len(batch_llm_results)} LLM recommendations")
                        all_llm_results.extend(batch_llm_results)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse batch {batch_num} LLM response: {e}")
                        # Continue with next batch
                        continue
                        
                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    # Continue with next batch
                    continue
                
                # Small delay between batches to avoid rate limiting
                await asyncio.sleep(0.5)
            
            # Update progress for processing results
            job_manager.update_job_progress(
                job_id,
                progress_percentage=85,
                current_step="Processing Results",
                message=f"Collected {len(all_llm_results)} LLM recommendations, generating final results",
                completed_steps=len(all_attributes)  # LLM analysis phase complete
            )
            
            logger.info(f"🎯 Total LLM results collected: {len(all_llm_results)} from {total_batches} batches")
            
            # Process results and match to existing attributes
            recommendations = []
            matched_count = 0
            
            for existing_attr in all_attributes:
                # Find matching LLM result from all batches
                matching_result = None
                attr_name_lower = existing_attr.attribute_name.lower()
                
                for llm_result in all_llm_results:
                    llm_name_lower = llm_result.get("attribute_name", "").lower()
                    if attr_name_lower == llm_name_lower:
                        matching_result = llm_result
                        matched_count += 1
                        break
                
                if matching_result:
                    # Use LLM result
                    risk_score = float(matching_result.get("risk_score", 50))
                    recommendation = "Test" if risk_score >= 50 else "Skip"  # Fixed enum values
                    rationale = matching_result.get("rationale", "LLM scoping analysis")
                    priority = "High" if risk_score >= 75 else "Medium" if risk_score >= 50 else "Low"
                    
                    # Handle source documents - convert to list if string
                    expected_docs_raw = matching_result.get("typical_source_documents", ["Source documents TBD"])
                    if isinstance(expected_docs_raw, str):
                        expected_docs = [expected_docs_raw] if expected_docs_raw.strip() else ["Source documents TBD"]
                    else:
                        expected_docs = expected_docs_raw if expected_docs_raw else ["Source documents TBD"]
                    
                    # Handle keywords - convert to list if string  
                    keywords_raw = matching_result.get("keywords_to_look_for", [existing_attr.attribute_name])
                    if isinstance(keywords_raw, str):
                        keywords = [kw.strip() for kw in keywords_raw.split(',')] if keywords_raw.strip() else [existing_attr.attribute_name]
                    else:
                        keywords = keywords_raw if keywords_raw else [existing_attr.attribute_name]
                    
                    # Additional LLM fields to save to database
                    testing_approach = matching_result.get("testing_approach", "LLM-recommended testing methodology")
                    validation_rules = matching_result.get("validation_rules", "Standard validation rules apply")
                    format_info = matching_result.get("format", None)  # New format field
                    description = matching_result.get("description", None)  # New description field
                else:
                    # Fall back to local scoring
                    risk_score = calculate_local_risk_score(
                        existing_attr, 
                        cde_attributes,
                        historical_issue_attributes
                    )
                    recommendation = "Test" if risk_score >= 50 else "Skip"  # Fixed enum values
                    rationale = "Local scoring used - LLM analysis unavailable for this attribute"
                    priority = "High" if risk_score >= 75 else "Medium" if risk_score >= 50 else "Low"
                    expected_docs = ["Source documents TBD"]
                    keywords = [existing_attr.attribute_name]
                    
                    # Fallback values for additional fields
                    testing_approach = "Standard testing approach for this data type"
                    validation_rules = "Standard validation rules apply"
                    format_info = None  # No format info available
                    description = None  # No description available
                
                # Create recommendation object
                recommendation_data = {
                    "attribute_id": existing_attr.attribute_id,
                    "attribute_name": existing_attr.attribute_name,
                    "recommendation_score": risk_score,
                    "recommendation": recommendation,
                    "rationale": rationale,
                    "expected_source_documents": expected_docs,
                    "search_keywords": keywords,
                    "priority_level": priority,
                    "testing_approach": testing_approach,
                    "validation_rules": validation_rules,
                    "format": format_info,
                    "description": description
                }
                
                recommendations.append(recommendation_data)
                
                # Update database with ALL LLM response fields
                existing_attr.risk_score = risk_score
                existing_attr.llm_rationale = rationale
                
                # Save additional LLM response fields to database
                if expected_docs and len(expected_docs) > 0:
                    existing_attr.typical_source_documents = "; ".join(expected_docs) if isinstance(expected_docs, list) else str(expected_docs)
                
                if keywords and len(keywords) > 0:
                    existing_attr.keywords_to_look_for = "; ".join(keywords) if isinstance(keywords, list) else str(keywords)
                
                if testing_approach:
                    existing_attr.testing_approach = testing_approach
                
                if validation_rules:
                    existing_attr.validation_rules = validation_rules
                
                # Save new format field to data_type if available and not already set
                if format_info and (not existing_attr.data_type or str(existing_attr.data_type).lower() in ['none', 'null', '']):
                    # Map format to valid data_type enum values
                    format_lower = format_info.lower()
                    if 'numeric' in format_lower or 'number' in format_lower or 'decimal' in format_lower or 'float' in format_lower:
                        existing_attr.data_type = 'Decimal'
                    elif 'integer' in format_lower or 'int' in format_lower or 'whole' in format_lower:
                        existing_attr.data_type = 'Integer'
                    elif 'text' in format_lower or 'string' in format_lower or 'varchar' in format_lower or 'char' in format_lower:
                        existing_attr.data_type = 'String'
                    elif 'datetime' in format_lower or 'timestamp' in format_lower:
                        existing_attr.data_type = 'DateTime'
                    elif 'date' in format_lower:
                        existing_attr.data_type = 'Date'
                    elif 'bool' in format_lower or 'flag' in format_lower or 'y/n' in format_lower:
                        existing_attr.data_type = 'Boolean'
                    elif 'json' in format_lower or 'object' in format_lower:
                        existing_attr.data_type = 'JSON'
                    else:
                        # If we can't map it to enum, store as String for now
                        existing_attr.data_type = 'String'
                
                # Update description if available - prioritize LLM descriptions over existing technical names
                if description and description.strip():
                    existing_attr.description = description
                    logger.debug(f"💬 Updated description for {existing_attr.attribute_name}: {description[:100]}...")
                
                # Set LLM-related flags
                existing_attr.llm_generated = True
                
                logger.debug(f"💾 Updated attribute {existing_attr.attribute_name} with LLM data: risk_score={risk_score}, docs={len(expected_docs) if expected_docs else 0}, keywords={len(keywords) if keywords else 0}")
            
            # Create or update AttributeScopingRecommendation records
            logger.info(f"🔄 Creating/updating {len(recommendations)} AttributeScopingRecommendation records...")
            
            for rec_data in recommendations:
                # Check if recommendation already exists
                existing_rec_query = select(AttributeScopingRecommendation).where(
                    and_(
                        AttributeScopingRecommendation.cycle_id == cycle_id,
                        AttributeScopingRecommendation.report_id == report_id,
                        AttributeScopingRecommendation.attribute_id == rec_data["attribute_id"]
                    )
                )
                existing_rec_result = await db.execute(existing_rec_query)
                existing_rec = existing_rec_result.scalar_one_or_none()
                
                if existing_rec:
                    # Update existing recommendation
                    existing_rec.recommendation_score = rec_data["recommendation_score"]
                    existing_rec.recommendation = rec_data["recommendation"]
                    existing_rec.rationale = rec_data["rationale"]
                    existing_rec.expected_source_documents = rec_data["expected_source_documents"]
                    existing_rec.search_keywords = rec_data["search_keywords"]
                    existing_rec.priority_level = rec_data["priority_level"]
                    logger.debug(f"📝 Updated existing recommendation for {rec_data['attribute_name']}")
                else:
                    # Create new recommendation
                    new_rec = AttributeScopingRecommendation(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        attribute_id=rec_data["attribute_id"],
                        recommendation_score=rec_data["recommendation_score"],
                        recommendation=rec_data["recommendation"],
                        rationale=rec_data["rationale"],
                        expected_source_documents=rec_data["expected_source_documents"],
                        search_keywords=rec_data["search_keywords"],
                        priority_level=rec_data["priority_level"],
                        llm_provider=provider.model_name,
                        processing_time_ms=0
                    )
                    db.add(new_rec)
                    logger.debug(f"➕ Created new recommendation for {rec_data['attribute_name']}")
            
            # Commit database changes
            await db.commit()
            
            # Update final progress - all processing complete
            job_manager.update_job_progress(
                job_id,
                progress_percentage=95,
                current_step="Finalizing Results",
                message=f"Completed processing {len(recommendations)} attributes",
                completed_steps=total_processing_steps  # Both phases complete
            )
            
            # Calculate summary
            test_count = sum(1 for r in recommendations if r["recommendation"] == "Test")
            skip_count = len(recommendations) - test_count
            
            # Complete the job with results
            job_result = {
                "success": True,
                "total_attributes": len(recommendations),
                "llm_matched": matched_count,
                "local_scored": len(recommendations) - matched_count,
                "test_recommendations": test_count,
                "skip_recommendations": skip_count,
                "recommendations": recommendations,
                "provider_used": provider.model_name,
                "total_batches": total_batches,
                "batch_size": batch_size
            }
            
            job_manager.complete_job(job_id, result=job_result)
            
            logger.info(f"✅ Background scoping job {job_id} completed successfully!")
            logger.info(f"📊 Results: {test_count} Test, {skip_count} Skip (LLM matched {matched_count}/{len(all_attributes)})")
            
    except Exception as e:
        logger.error(f"💥 Background scoping job {job_id} failed: {str(e)}")
        import traceback
        logger.error(f"💥 Traceback:\n{traceback.format_exc()}")
        job_manager.complete_job(job_id, error=str(e))


@router.get("/{cycle_id}/reports/{report_id}/recommendations", response_model=List[AttributeScopingRecommendationSchema])
async def get_recommendations(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester_or_report_owner)
):
    """Get existing scoping recommendations"""
    
    # Verify access
    if current_user.role == "Report Owner":
        # Verify report ownership
        report_query = select(Report).where(
            and_(
                Report.report_id == report_id,
                Report.report_owner_id == current_user.user_id
            )
        )
        result = await db.execute(report_query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    
    # Get recommendations with attributes
    recommendations_query = select(AttributeScopingRecommendation).options(
        selectinload(AttributeScopingRecommendation.attribute)
    ).where(
        and_(
            AttributeScopingRecommendation.cycle_id == cycle_id,
            AttributeScopingRecommendation.report_id == report_id
        )
    ).order_by(AttributeScopingRecommendation.recommendation_score.desc())
    
    result = await db.execute(recommendations_query)
    recommendations = result.scalars().all()
    
    return [
        AttributeScopingRecommendationSchema(
            attribute_id=rec.attribute_id,
            attribute_name=rec.attribute.attribute_name,
            recommendation_score=rec.recommendation_score,
            recommendation=ScopingRecommendation(rec.recommendation),
            rationale=rec.rationale,
            expected_source_documents=rec.expected_source_documents,
            search_keywords=rec.search_keywords,
            other_reports_using=rec.other_reports_using or [],
            risk_factors=rec.risk_factors or [],
            priority_level=rec.priority_level
        )
        for rec in recommendations
    ]


@router.post("/{cycle_id}/reports/{report_id}/decisions", response_model=dict)
async def submit_scoping_decisions(
    cycle_id: int,
    report_id: int,
    submission: TesterScopingSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester)
):
    """Submit tester scoping decisions"""
    
    # Verify cycle report assignment
    cycle_report_query = select(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id,
            CycleReport.tester_id == current_user.user_id
        )
    )
    result = await db.execute(cycle_report_query)
    cycle_report = result.scalar_one_or_none()
    
    if not cycle_report:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    
    # Check if there's already an approved submission - prevent new submissions after approval
    approved_submission_query = select(ScopingSubmission).join(
        ReportOwnerScopingReview,
        ReportOwnerScopingReview.submission_id == ScopingSubmission.submission_id
    ).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id,
            ReportOwnerScopingReview.approval_status == 'Approved'
        )
    )
    result = await db.execute(approved_submission_query)
    approved_submission = result.scalar_one_or_none()
    
    if approved_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit new version - Version {approved_submission.version} has already been approved by Report Owner"
        )
    
    # Validate all attributes have decisions
    attributes_query = select(ReportAttribute.attribute_id).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id
        )
    )
    result = await db.execute(attributes_query)
    all_attribute_ids = {row[0] for row in result.fetchall()}
    
    decision_attribute_ids = {decision.attribute_id for decision in submission.decisions}
    
    if all_attribute_ids != decision_attribute_ids:
        missing = all_attribute_ids - decision_attribute_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing decisions for attributes: {missing}"
        )
    
    # Check for existing submissions to determine version
    existing_submissions_query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.version.desc())
    result = await db.execute(existing_submissions_query)
    latest_submission = result.scalars().first()
    
    version = 1
    previous_version_id = None
    changes_from_previous = None
    revision_reason = None
    
    if latest_submission:
        version = latest_submission.version + 1
        previous_version_id = latest_submission.submission_id
        
        # Calculate changes if this is a revision
        if version > 1:
            # Get previous decisions for comparison
            prev_decisions_query = select(TesterScopingDecision).where(
                and_(
                    TesterScopingDecision.cycle_id == cycle_id,
                    TesterScopingDecision.report_id == report_id
                )
            )
            result = await db.execute(prev_decisions_query)
            prev_decisions = {d.attribute_id: d for d in result.scalars().all()}
            
            # Calculate what changed
            changes = {
                'added_attributes': [],
                'removed_attributes': [],
                'changed_decisions': [],
                'summary': {}
            }
            
            # Current decisions map
            current_decisions = {d.attribute_id: d for d in submission.decisions}
            
            # Find changes
            for attr_id, new_decision in current_decisions.items():
                if attr_id in prev_decisions:
                    old_decision = prev_decisions[attr_id]
                    if old_decision.final_scoping != new_decision.final_scoping:
                        changes['changed_decisions'].append({
                            'attribute_id': attr_id,
                            'old_decision': old_decision.final_scoping,
                            'new_decision': new_decision.final_scoping,
                            'old_rationale': old_decision.tester_rationale,
                            'new_rationale': new_decision.tester_rationale
                        })
                else:
                    changes['added_attributes'].append(attr_id)
            
            # Find removed attributes
            for attr_id in prev_decisions.keys():
                if attr_id not in current_decisions:
                    changes['removed_attributes'].append(attr_id)
            
            # Summary of changes
            changes['summary'] = {
                'total_changes': len(changes['changed_decisions']) + len(changes['added_attributes']) + len(changes['removed_attributes']),
                'newly_selected': len([c for c in changes['changed_decisions'] if c['new_decision'] and not c['old_decision']]),
                'newly_declined': len([c for c in changes['changed_decisions'] if not c['new_decision'] and c['old_decision']])
            }
            
            changes_from_previous = changes
            
            # Get the latest review to understand why revision was needed
            review_query = select(ReportOwnerScopingReview).where(
                ReportOwnerScopingReview.submission_id == latest_submission.submission_id
            ).order_by(ReportOwnerScopingReview.created_at.desc())
            result = await db.execute(review_query)
            latest_review = result.scalar_one_or_none()
            
            if latest_review and latest_review.approval_status == 'Needs Revision':
                revision_reason = f"Revision requested by Report Owner: {latest_review.review_comments}"
    
    # Clear existing decisions for this submission
    await db.execute(
        TesterScopingDecision.__table__.delete().where(
            and_(
                TesterScopingDecision.cycle_id == cycle_id,
                TesterScopingDecision.report_id == report_id
            )
        )
    )
    
    # Create new decisions
    scoped_count = 0
    skipped_count = 0
    
    for decision in submission.decisions:
        # Get recommendation if exists
        rec_query = select(AttributeScopingRecommendation.recommendation_id).where(
            and_(
                AttributeScopingRecommendation.cycle_id == cycle_id,
                AttributeScopingRecommendation.report_id == report_id,
                AttributeScopingRecommendation.attribute_id == decision.attribute_id
            )
        )
        result = await db.execute(rec_query)
        recommendation_id = result.scalar_one_or_none()
        
        tester_decision = TesterScopingDecision(
            cycle_id=cycle_id,
            report_id=report_id,
            attribute_id=decision.attribute_id,
            recommendation_id=recommendation_id,
            decision=decision.decision.value,
            final_scoping=decision.final_scoping,
            tester_rationale=decision.tester_rationale,
            override_reason=decision.override_reason,
            decided_by=current_user.user_id
        )
        db.add(tester_decision)
        
        if decision.final_scoping:
            scoped_count += 1
        else:
            skipped_count += 1
    
    # Create submission record if confirm_submission is True
    if submission.confirm_submission:
        scoping_submission = ScopingSubmission(
            cycle_id=cycle_id,
            report_id=report_id,
            version=version,
            previous_version_id=previous_version_id,
            submission_notes=submission.submission_notes,
            changes_from_previous=changes_from_previous,
            revision_reason=revision_reason,
            total_attributes=len(submission.decisions),
            scoped_attributes=scoped_count,
            skipped_attributes=skipped_count,
            submitted_by=current_user.user_id
        )
        db.add(scoping_submission)
        
        # Update workflow phase status
        await db.execute(
            update(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Scoping'
                )
            ).values(status='Pending Approval')
        )
    
    # Log audit trail
    audit_log = ScopingAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        action="scoping_decisions_submitted" if submission.confirm_submission else "scoping_decisions_saved",
        performed_by=current_user.user_id,
        details={
            "total_decisions": len(submission.decisions),
            "scoped_attributes": scoped_count,
            "skipped_attributes": skipped_count,
            "submitted_for_approval": submission.confirm_submission,
            "version": version,
            "is_revision": version > 1,
            "changes_summary": changes_from_previous.get('summary') if changes_from_previous else None
        }
    )
    db.add(audit_log)
    
    await db.commit()
    
    action = "submitted for approval" if submission.confirm_submission else "saved"
    version_info = f" (v{version})" if version > 1 else ""
    logger.info(f"Scoping decisions {action}{version_info} for report {report_id} in cycle {cycle_id}")
    
    return {
        "message": f"Scoping decisions {action} successfully{version_info}",
        "total_decisions": len(submission.decisions),
        "scoped_attributes": scoped_count,
        "skipped_attributes": skipped_count,
        "submitted_for_approval": submission.confirm_submission,
        "version": version,
        "is_revision": version > 1,
        "changes_summary": changes_from_previous.get('summary') if changes_from_previous else None
    }


@router.post("/{cycle_id}/reports/{report_id}/review", response_model=dict)
async def review_scoping_submission(
    cycle_id: int,
    report_id: int,
    review: ReportOwnerScopingReviewSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_report_owner)
):
    """Report Owner review of scoping submission"""
    
    # Verify report ownership
    report_query = select(Report).where(
        and_(
            Report.report_id == report_id,
            Report.report_owner_id == current_user.user_id
        )
    )
    result = await db.execute(report_query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this report"
        )
    
    # Get latest submission
    submission_query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.created_at.desc())
    result = await db.execute(submission_query)
    submission = result.scalars().first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scoping submission found for review"
        )
    
    # Create review record
    scoping_review = ReportOwnerScopingReview(
        submission_id=submission.submission_id,
        cycle_id=cycle_id,
        report_id=report_id,
        approval_status=review.approval_status.value,
        review_comments=review.review_comments,
        requested_changes=review.requested_changes,
        resource_impact_assessment=review.resource_impact_assessment,
        risk_coverage_assessment=review.risk_coverage_assessment,
        reviewed_by=current_user.user_id
    )
    db.add(scoping_review)
    
    # Update workflow phase status based on approval
    if review.approval_status == ApprovalStatus.APPROVED:
        new_status = 'Complete'
    elif review.approval_status == ApprovalStatus.DECLINED:
        new_status = 'In Progress'  # Tester can revise and resubmit
    elif review.approval_status == ApprovalStatus.NEEDS_REVISION:
        new_status = 'In Progress'  # Tester can revise and resubmit
    else:
        new_status = 'Pending Approval'  # Should not reach here with current enum values
    
    await db.execute(
        update(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Scoping'
            )
        ).values(
            status=new_status,
            actual_end_date=datetime.utcnow() if review.approval_status == ApprovalStatus.APPROVED else None
        )
    )
    
    # Log audit trail
    audit_log = ScopingAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        action="scoping_submission_reviewed",
        performed_by=current_user.user_id,
        details={
            "approval_status": review.approval_status.value,
            "review_comments": review.review_comments,
            "requested_changes": review.requested_changes
        }
    )
    db.add(audit_log)
    
    await db.commit()
    
    logger.info(f"Scoping submission reviewed for report {report_id} in cycle {cycle_id}: {review.approval_status.value}")
    
    return {
        "message": f"Scoping submission {review.approval_status.value.lower()} successfully",
        "approval_status": review.approval_status.value,
        "phase_status": new_status
    }


@router.get("/{cycle_id}/reports/{report_id}/attributes")
async def get_attribute_scoping_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester_or_report_owner)
):
    """Get scoping status for all attributes - returns full details for Report Owners"""
    
    # Verify access
    if current_user.role == "Report Owner":
        # Verify report ownership
        report_query = select(Report).where(
            and_(
                Report.report_id == report_id,
                Report.report_owner_id == current_user.user_id
            )
        )
        result = await db.execute(report_query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    
    # Get all attributes with their recommendations and decisions
    attributes_query = select(ReportAttribute).where(
        and_(
            ReportAttribute.cycle_id == cycle_id,
            ReportAttribute.report_id == report_id
        )
    ).order_by(ReportAttribute.attribute_name)
    
    result = await db.execute(attributes_query)
    attributes = result.scalars().all()
    
    # For Report Owners, return full attribute details for review
    if current_user.role == "Report Owner":
        attribute_details = []
        
        for attr in attributes:
            # Get recommendation
            rec_query = select(AttributeScopingRecommendation).where(
                and_(
                    AttributeScopingRecommendation.cycle_id == cycle_id,
                    AttributeScopingRecommendation.report_id == report_id,
                    AttributeScopingRecommendation.attribute_id == attr.attribute_id
                )
            )
            result = await db.execute(rec_query)
            recommendation = result.scalar_one_or_none()
            
            # Get decision
            decision_query = select(TesterScopingDecision).where(
                and_(
                    TesterScopingDecision.cycle_id == cycle_id,
                    TesterScopingDecision.report_id == report_id,
                    TesterScopingDecision.attribute_id == attr.attribute_id
                )
            )
            result = await db.execute(decision_query)
            decision = result.scalar_one_or_none()
            
            attribute_details.append({
                "attribute_id": attr.attribute_id,
                "attribute_name": attr.attribute_name,
                "mdrm": attr.mdrm,
                "description": attr.description,
                "data_type": attr.data_type,
                "mandatory_flag": attr.mandatory_flag,
                "is_primary_key": attr.is_primary_key,
                "cde_flag": attr.cde_flag,
                "historical_issues_flag": attr.historical_issues_flag,
                "llm_risk_score": recommendation.recommendation_score if recommendation else attr.risk_score,
                "llm_rationale": recommendation.rationale if recommendation else attr.llm_rationale,
                "has_llm_recommendation": recommendation is not None,
                "llm_recommendation": recommendation.recommendation if recommendation else None,
                "has_tester_decision": decision is not None,
                "tester_decision": decision.decision if decision else None,
                "final_scoping": decision.final_scoping if decision else None,
                "tester_rationale": decision.tester_rationale if decision else None,
                "override_reason": decision.override_reason if decision else None,
                "is_scoped_for_testing": decision.final_scoping if decision else False
            })
        
        return attribute_details
    
    # For Testers, return the original AttributeScopingStatus format
    attribute_statuses = []
    
    for attr in attributes:
        # Get recommendation
        rec_query = select(AttributeScopingRecommendation).where(
            and_(
                AttributeScopingRecommendation.cycle_id == cycle_id,
                AttributeScopingRecommendation.report_id == report_id,
                AttributeScopingRecommendation.attribute_id == attr.attribute_id
            )
        )
        result = await db.execute(rec_query)
        recommendation = result.scalar_one_or_none()
        
        # Get decision
        decision_query = select(TesterScopingDecision).where(
            and_(
                TesterScopingDecision.cycle_id == cycle_id,
                TesterScopingDecision.report_id == report_id,
                TesterScopingDecision.attribute_id == attr.attribute_id
            )
        )
        result = await db.execute(decision_query)
        decision = result.scalar_one_or_none()
        
        attribute_statuses.append({
            "attribute_id": attr.attribute_id,
            "attribute_name": attr.attribute_name,
            "is_primary_key": attr.is_primary_key,  # Add this field
            "has_llm_recommendation": recommendation is not None,
            "llm_recommendation": recommendation.recommendation if recommendation else None,
            "llm_score": recommendation.recommendation_score if recommendation else None,
            "has_tester_decision": decision is not None,
            "tester_decision": decision.decision if decision else None,
            "final_scoping": decision.final_scoping if decision else None,
            "is_scoped_for_testing": decision.final_scoping if decision else False
        })
    
    return attribute_statuses


@router.post("/{cycle_id}/reports/{report_id}/complete", response_model=dict)
async def complete_scoping_phase(
    cycle_id: int,
    report_id: int,
    request: ScopingPhaseComplete,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester)
):
    """Complete scoping phase"""
    
    # Verify cycle report assignment
    cycle_report_query = select(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id,
            CycleReport.tester_id == current_user.user_id
        )
    )
    result = await db.execute(cycle_report_query)
    cycle_report = result.scalar_one_or_none()
    
    if not cycle_report:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    
    # Check if scoping phase is approved
    scoping_phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == 'Scoping'
        )
    )
    result = await db.execute(scoping_phase_query)
    scoping_phase = result.scalar_one_or_none()
    
    if not scoping_phase or scoping_phase.status != 'Complete':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scoping phase must be approved by Report Owner before completion"
        )
    
    # Update report attributes with scoping decisions
    decisions_query = select(TesterScopingDecision).where(
        and_(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id
        )
    )
    result = await db.execute(decisions_query)
    decisions = result.scalars().all()
    
    for decision in decisions:
        await db.execute(
            update(ReportAttribute).where(
                ReportAttribute.attribute_id == decision.attribute_id
            ).values(is_scoped=decision.final_scoping)
        )
    
    # Log audit trail
    audit_log = ScopingAuditLog(
        cycle_id=cycle_id,
        report_id=report_id,
        action="scoping_phase_completed",
        performed_by=current_user.user_id,
        details={
            "completion_notes": request.completion_notes,
            "scoped_attributes": len([d for d in decisions if d.final_scoping])
        }
    )
    db.add(audit_log)
    
    await db.commit()
    
    logger.info(f"Scoping phase completed for report {report_id} in cycle {cycle_id}")
    
    return {
        "message": "Scoping phase completed successfully",
        "cycle_id": cycle_id,
        "report_id": report_id,
        "scoped_attributes": len([d for d in decisions if d.final_scoping]),
        "completed_at": datetime.utcnow().isoformat()
    }


@router.get("/{cycle_id}/reports/{report_id}/decisions")
async def get_scoping_decisions(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester_or_report_owner)
):
    """Get submitted scoping decisions for review"""
    
    # Verify access - tester can see their own, report owner can see for their reports
    if current_user.role == "Report Owner":
        # Verify report ownership
        report_query = select(Report).where(
            and_(
                Report.report_id == report_id,
                Report.report_owner_id == current_user.user_id
            )
        )
        result = await db.execute(report_query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this report's scoping decisions"
            )
    
    # Get scoping decisions with attribute details
    decisions_query = select(TesterScopingDecision).options(
        selectinload(TesterScopingDecision.attribute),
        selectinload(TesterScopingDecision.decided_by_user)
    ).where(
        and_(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id
        )
    )
    result = await db.execute(decisions_query)
    decisions = result.scalars().all()
    
    # Format response
    return [
        {
            "decision_id": decision.decision_id,
            "attribute_id": decision.attribute_id,
            "decision": decision.decision,
            "final_scoping": decision.final_scoping,
            "tester_rationale": decision.tester_rationale,
            "override_reason": decision.override_reason,
            "decided_by_name": f"{decision.decided_by_user.first_name} {decision.decided_by_user.last_name}" if decision.decided_by_user else "Unknown",
            "created_at": decision.created_at.isoformat() if decision.created_at else None
        }
        for decision in decisions
    ]


@router.get("/{cycle_id}/reports/{report_id}/submission")
async def get_scoping_submission(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester_or_report_owner)
):
    """Get latest scoping submission for review"""
    
    # Verify access
    if current_user.role == "Report Owner":
        # Verify report ownership
        report_query = select(Report).where(
            and_(
                Report.report_id == report_id,
                Report.report_owner_id == current_user.user_id
            )
        )
        result = await db.execute(report_query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this report's submission"
            )
    
    # Get latest submission
    submission_query = select(ScopingSubmission).options(
        selectinload(ScopingSubmission.submitted_by_user)
    ).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.created_at.desc())
    result = await db.execute(submission_query)
    submission = result.scalars().first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scoping submission found"
        )
    
    return {
        "submission_id": submission.submission_id,
        "cycle_id": submission.cycle_id,
        "report_id": submission.report_id,
        "submission_notes": submission.submission_notes,
        "total_attributes": submission.total_attributes,
        "scoped_attributes": submission.scoped_attributes,
        "skipped_attributes": submission.skipped_attributes,
        "submitted_at": submission.created_at.isoformat(),
        "submitted_by_name": f"{submission.submitted_by_user.first_name} {submission.submitted_by_user.last_name}" if submission.submitted_by_user else "Unknown"
    }


@router.get("/pending-reviews", response_model=List[dict])
async def get_pending_scoping_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_report_owner)
):
    """Get all pending scoping reviews for the current report owner"""
    
    # Get all reports owned by the current user that have pending scoping submissions
    pending_reviews_query = select(
        ScopingSubmission.cycle_id,
        ScopingSubmission.report_id,
        ScopingSubmission.submission_id,
        ScopingSubmission.total_attributes,
        ScopingSubmission.scoped_attributes,
        ScopingSubmission.created_at.label('submitted_at'),
        Report.report_name,
        LOB.lob_name,
        func.concat(User.first_name, ' ', User.last_name).label('submitted_by_name'),
        TestCycle.cycle_name
    ).select_from(
        ScopingSubmission.__table__.join(Report, ScopingSubmission.report_id == Report.report_id)
        .join(LOB, Report.lob_id == LOB.lob_id)
        .join(User, ScopingSubmission.submitted_by == User.user_id)
        .join(TestCycle, ScopingSubmission.cycle_id == TestCycle.cycle_id)
    ).where(
        and_(
            Report.report_owner_id == current_user.user_id,
            # Check that there's no review yet (approved, declined, or needs revision)
            ~exists().where(
                ReportOwnerScopingReview.submission_id == ScopingSubmission.submission_id
            )
        )
    ).order_by(ScopingSubmission.created_at.desc())
    
    result = await db.execute(pending_reviews_query)
    pending_submissions = result.fetchall()
    
    # Format the response
    pending_reviews = []
    for submission in pending_submissions:
        # Calculate priority based on submission age and completion percentage
        # Handle timezone-aware vs timezone-naive datetime comparison
        if submission.submitted_at.tzinfo is not None:
            # If submitted_at is timezone-aware, make utcnow timezone-aware too
            from datetime import timezone
            current_time = datetime.now(timezone.utc)
            days_since_submission = (current_time - submission.submitted_at).days
        else:
            # If submitted_at is timezone-naive, use utcnow
            days_since_submission = (datetime.utcnow() - submission.submitted_at).days
            
        completion_percentage = (submission.scoped_attributes / submission.total_attributes) * 100 if submission.total_attributes > 0 else 0
        
        # Priority logic: High if > 2 days old OR low completion rate, Medium if 1-2 days, Low if recent and good completion
        if days_since_submission > 2 or completion_percentage < 30:
            priority = 'High'
        elif days_since_submission > 0 or completion_percentage < 60:
            priority = 'Medium'
        else:
            priority = 'Low'
        
        pending_reviews.append({
            'cycle_id': submission.cycle_id,
            'report_id': submission.report_id,
            'submission_id': submission.submission_id,
            'report_name': submission.report_name,
            'lob': submission.lob_name or 'Unknown',
            'cycle_name': submission.cycle_name,
            'submitted_by': submission.submitted_by_name,
            'submitted_date': submission.submitted_at.isoformat(),
            'attributes_selected': submission.scoped_attributes,
            'total_attributes': submission.total_attributes,
            'completion_percentage': round(completion_percentage),
            'priority': priority,
            'days_pending': days_since_submission
        })
    
    return pending_reviews


@router.get("/{cycle_id}/reports/{report_id}/feedback")
async def get_latest_review_feedback(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester)
):
    """Get latest Report Owner feedback for tester"""
    
    # Verify cycle report assignment
    cycle_report_query = select(CycleReport).where(
        and_(
            CycleReport.cycle_id == cycle_id,
            CycleReport.report_id == report_id,
            CycleReport.tester_id == current_user.user_id
        )
    )
    result = await db.execute(cycle_report_query)
    cycle_report = result.scalar_one_or_none()
    
    if not cycle_report:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report"
        )
    
    # Get latest submission for context
    latest_submission_query = select(ScopingSubmission).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.created_at.desc())
    result = await db.execute(latest_submission_query)
    latest_submission = result.scalars().first()
    
    if not latest_submission:
        return {"has_feedback": False, "message": "No submissions found"}
    
    # Find the most recent submission that HAS feedback (not necessarily the latest submission)
    # This handles the case where user resubmitted but Report Owner hasn't reviewed the new version yet
    submission_with_feedback_query = select(ScopingSubmission).options(
        selectinload(ScopingSubmission.submitted_by_user)
    ).join(ReportOwnerScopingReview, 
           ReportOwnerScopingReview.submission_id == ScopingSubmission.submission_id
    ).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.version.desc())
    result = await db.execute(submission_with_feedback_query)
    submission_with_feedback = result.scalars().first()
    
    if not submission_with_feedback:
        return {
            "has_feedback": False, 
            "submission_version": latest_submission.version,
            "submission_status": "Pending Review",
            "message": "Submission is pending Report Owner review"
        }
    
    # Get the latest review for the submission that has feedback
    review_query = select(ReportOwnerScopingReview).options(
        selectinload(ReportOwnerScopingReview.reviewed_by_user)
    ).where(
        ReportOwnerScopingReview.submission_id == submission_with_feedback.submission_id
    ).order_by(ReportOwnerScopingReview.created_at.desc())
    result = await db.execute(review_query)
    latest_review = result.scalar_one_or_none()
    
    # Determine if user can resubmit based on:
    # 1. The feedback status (Declined/Needs Revision allows resubmit)
    # 2. Whether there's a newer submission without feedback (latest_submission.version > submission_with_feedback.version)
    # 3. Check if any version has been approved (approved versions should block resubmission)
    
    # Check if any version has been approved
    approved_version_query = select(ScopingSubmission).join(
        ReportOwnerScopingReview,
        ReportOwnerScopingReview.submission_id == ScopingSubmission.submission_id
    ).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id,
            ReportOwnerScopingReview.approval_status == 'Approved'
        )
    )
    result = await db.execute(approved_version_query)
    approved_version = result.scalar_one_or_none()
    
    can_resubmit = (
        not approved_version and  # No approved version exists
        latest_review.approval_status in ['Declined', 'Needs Revision'] and
        latest_submission.version >= submission_with_feedback.version
    )
    
    # If there's a newer submission than the one with feedback, show that this is outdated feedback
    is_outdated_feedback = latest_submission.version > submission_with_feedback.version
    
    return {
        "has_feedback": True,
        "submission_version": latest_submission.version,  # Latest submission version
        "feedback_version": submission_with_feedback.version,  # Version that has feedback
        "is_outdated_feedback": is_outdated_feedback,
        "has_approved_version": approved_version is not None,
        "approved_version": approved_version.version if approved_version else None,
        "review": {
            "approval_status": latest_review.approval_status,
            "review_comments": latest_review.review_comments,
            "requested_changes": latest_review.requested_changes,
            "resource_impact_assessment": latest_review.resource_impact_assessment,
            "risk_coverage_assessment": latest_review.risk_coverage_assessment,
            "reviewed_by": f"{latest_review.reviewed_by_user.first_name} {latest_review.reviewed_by_user.last_name}" if latest_review.reviewed_by_user else "Unknown",
            "reviewed_at": latest_review.created_at.isoformat(),
        },
        "can_resubmit": can_resubmit,
        "needs_revision": latest_review.approval_status == 'Needs Revision',
        "cannot_resubmit_reason": "Scoping has already been approved - no further changes allowed" if approved_version else None
    }


@router.get("/{cycle_id}/reports/{report_id}/versions")
async def get_submission_versions(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester_or_report_owner)
):
    """Get all submission versions for comparison"""
    
    # Verify access
    if current_user.role == "Report Owner":
        # Verify report ownership
        report_query = select(Report).where(
            and_(
                Report.report_id == report_id,
                Report.report_owner_id == current_user.user_id
            )
        )
        result = await db.execute(report_query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    else:
        # Verify tester assignment
        cycle_report_query = select(CycleReport).where(
            and_(
                CycleReport.cycle_id == cycle_id,
                CycleReport.report_id == report_id,
                CycleReport.tester_id == current_user.user_id
            )
        )
        result = await db.execute(cycle_report_query)
        cycle_report = result.scalar_one_or_none()
        
        if not cycle_report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    
    # Get all submissions with reviews
    submissions_query = select(ScopingSubmission).options(
        selectinload(ScopingSubmission.submitted_by_user)
    ).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id
        )
    ).order_by(ScopingSubmission.version.asc())
    result = await db.execute(submissions_query)
    submissions = result.scalars().all()
    
    versions = []
    for submission in submissions:
        # Get review for this submission
        review_query = select(ReportOwnerScopingReview).options(
            selectinload(ReportOwnerScopingReview.reviewed_by_user)
        ).where(
            ReportOwnerScopingReview.submission_id == submission.submission_id
        ).order_by(ReportOwnerScopingReview.created_at.desc())
        result = await db.execute(review_query)
        review = result.scalar_one_or_none()
        
        version_data = {
            "version": submission.version,
            "submission_id": submission.submission_id,
            "submitted_at": submission.created_at.isoformat(),
            "submitted_by": f"{submission.submitted_by_user.first_name} {submission.submitted_by_user.last_name}" if submission.submitted_by_user else "Unknown",
            "submission_notes": submission.submission_notes,
            "total_attributes": submission.total_attributes,
            "scoped_attributes": submission.scoped_attributes,
            "skipped_attributes": submission.skipped_attributes,
            "changes_from_previous": submission.changes_from_previous,
            "revision_reason": submission.revision_reason,
            "is_approved": review.approval_status == 'Approved' if review else False,
            "review": None
        }
        
        if review:
            version_data["review"] = {
                "approval_status": review.approval_status,
                "review_comments": review.review_comments,
                "requested_changes": review.requested_changes,
                "reviewed_by": f"{review.reviewed_by_user.first_name} {review.reviewed_by_user.last_name}" if review.reviewed_by_user else "Unknown",
                "reviewed_at": review.created_at.isoformat()
            }
        
        versions.append(version_data)
    
    return {
        "versions": versions,
        "total_versions": len(versions),
        "latest_version": versions[-1]["version"] if versions else 0
    }


@router.get("/{cycle_id}/reports/{report_id}/approved-version")
async def get_approved_version_details(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_tester_or_report_owner)
):
    """Get approved version details with selected attributes"""
    
    # Verify access
    if current_user.role == "Report Owner":
        report_query = select(Report).where(
            and_(
                Report.report_id == report_id,
                Report.report_owner_id == current_user.user_id
            )
        )
        result = await db.execute(report_query)
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    else:
        cycle_report_query = select(CycleReport).where(
            and_(
                CycleReport.cycle_id == cycle_id,
                CycleReport.report_id == report_id,
                CycleReport.tester_id == current_user.user_id
            )
        )
        result = await db.execute(cycle_report_query)
        cycle_report = result.scalar_one_or_none()
        
        if not cycle_report:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this report"
            )
    
    # Get approved submission
    approved_submission_query = select(ScopingSubmission).options(
        selectinload(ScopingSubmission.submitted_by_user)
    ).join(
        ReportOwnerScopingReview,
        ReportOwnerScopingReview.submission_id == ScopingSubmission.submission_id
    ).where(
        and_(
            ScopingSubmission.cycle_id == cycle_id,
            ScopingSubmission.report_id == report_id,
            ReportOwnerScopingReview.approval_status == 'Approved'
        )
    ).order_by(ScopingSubmission.version.desc())
    result = await db.execute(approved_submission_query)
    approved_submission = result.scalar_one_or_none()
    
    if not approved_submission:
        return {
            "has_approved_version": False,
            "message": "No approved version found"
        }
    
    # Get the review details
    review_query = select(ReportOwnerScopingReview).options(
        selectinload(ReportOwnerScopingReview.reviewed_by_user)
    ).where(
        and_(
            ReportOwnerScopingReview.submission_id == approved_submission.submission_id,
            ReportOwnerScopingReview.approval_status == 'Approved'
        )
    ).order_by(ReportOwnerScopingReview.created_at.desc())
    result = await db.execute(review_query)
    review = result.scalar_one_or_none()
    
    # Get the scoping decisions for the approved submission version
    # Note: We need to reconstruct what was submitted in that version
    # Since decisions are being cleared on each submission, we need to look at the changes_from_previous
    # For now, let's see if we can get decisions by looking at the submission data
    
    # Get the current scoping decisions (which should represent the approved state if no new submissions after approval)
    approved_decisions_query = select(TesterScopingDecision).options(
        selectinload(TesterScopingDecision.attribute)
    ).where(
        and_(
            TesterScopingDecision.cycle_id == cycle_id,
            TesterScopingDecision.report_id == report_id,
            TesterScopingDecision.final_scoping == True
        )
    ).order_by(TesterScopingDecision.attribute_id)
    result = await db.execute(approved_decisions_query)
    approved_decisions = result.scalars().all()
    
    # Format approved attributes
    approved_attributes = [
        {
            "attribute_id": decision.attribute_id,
            "attribute_name": decision.attribute.attribute_name,
            "mdrm": decision.attribute.mdrm,
            "is_primary_key": decision.attribute.is_primary_key,
            "mandatory_flag": decision.attribute.mandatory_flag,
            "tester_rationale": decision.tester_rationale
        }
        for decision in approved_decisions
    ]
    
    return {
        "has_approved_version": True,
        "approved_version": {
            "version": approved_submission.version,
            "submission_id": approved_submission.submission_id,
            "submitted_at": approved_submission.created_at.isoformat(),
            "submitted_by": f"{approved_submission.submitted_by_user.first_name} {approved_submission.submitted_by_user.last_name}" if approved_submission.submitted_by_user else "Unknown",
            "submission_notes": approved_submission.submission_notes,
            "total_attributes": approved_submission.total_attributes,
            "scoped_attributes": approved_submission.scoped_attributes,
            "skipped_attributes": approved_submission.skipped_attributes,
            "changes_from_previous": approved_submission.changes_from_previous,
        },
        "approval_details": {
            "approval_status": review.approval_status,
            "review_comments": review.review_comments,
            "approved_by": f"{review.reviewed_by_user.first_name} {review.reviewed_by_user.last_name}" if review.reviewed_by_user else "Unknown",
            "approved_at": review.created_at.isoformat(),
        } if review else None,
        "message": f"Version {approved_submission.version} was approved with {approved_submission.scoped_attributes} out of {approved_submission.total_attributes} attributes selected for testing",
        "approved_attributes": approved_attributes
    } 