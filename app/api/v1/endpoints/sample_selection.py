"""
Sample Selection API Endpoints - Individual Samples Approach
Direct sample management without sample sets
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, update, delete, text, Integer
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
import uuid
from string import Template
import json
import os
import logging
import asyncio

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.sample_selection import (
    SampleSelectionSample, 
    SampleSelectionVersion,
    SampleDecision,
    # SampleApprovalHistory,  # Temporarily disabled - model not found
    sample_status_enum,
    VersionStatus
)
from app.models.test_cycle import TestCycle
from app.models.report import Report
from app.models.lob import LOB
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.models.cycle_report import CycleReport
from app.services.llm_service import get_llm_service
from app.services.sample_selection_table_service import SampleSelectionTableService
from app.models.audit import LLMAuditLog
from pydantic import BaseModel
# Removed unused imports - using SampleSelectionTableService instead
from app.models.cycle_report_data_source import CycleReportDataSource
from app.models.planning import PlanningPDEMapping
from app.core.background_jobs import job_manager, BackgroundJobManager
from app.core.database import AsyncSessionLocal
from app.tasks.sample_selection_tasks import execute_intelligent_sampling_task
from app.api.v1.utils.deprecation import deprecated_endpoint
from app.services.universal_assignment_service import UniversalAssignmentService
from app.api.v1.utils.sample_selection_adapters import (
    get_or_create_current_version,
    convert_submission_to_version,
    sync_submission_status_to_version,
    get_samples_for_version,
    update_sample_counts_for_version
)

router = APIRouter(tags=["sample-selection"])
logger = logging.getLogger(__name__)


@router.get("/cycles/{cycle_id}/reports/{report_id}/available-lobs")
async def get_available_lobs_for_report(
    cycle_id: int = Path(..., description="Test Cycle ID"),
    report_id: int = Path(..., description="Report ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get available LOBs for sample selection assignment.
    For a report, only the report's assigned LOB should be available.
    """
    try:
        # Get the report to find its LOB
        report_query = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = report_query.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        # Get the LOB details
        from app.models.lob import LOB
        available_lobs = []
        
        if report.lob_id:
            lob_query = await db.execute(
                select(LOB).where(LOB.lob_id == report.lob_id)
            )
            lob = lob_query.scalar_one_or_none()
            
            if lob:
                available_lobs.append({
                    "lob_id": lob.lob_id,
                    "lob_name": lob.lob_name
                })
        
        return {
            "report_id": report_id,
            "report_name": report.report_name,
            "report_lob_id": report.lob_id,
            "available_lobs": available_lobs,
            "total_count": len(available_lobs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available LOBs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available LOBs: {str(e)}"
        )


# Pydantic Models
class SampleGenerationRequest(BaseModel):
    sample_size: int
    sample_type: str = "Population CycleReportSampleSelectionSamples"
    regulatory_context: Optional[str] = None
    scoped_attributes: Optional[List[Dict[str, Any]]] = None
    strategy: Optional[str] = "basic"  # "basic", "intelligent", "enhanced"
    
class UnifiedSampleGenerationRequest(BaseModel):
    """Unified request model for all sample generation strategies"""
    sample_size: int
    strategy: str = "basic"  # "basic", "intelligent", "enhanced"
    # Basic strategy fields
    sample_type: Optional[str] = "Population CycleReportSampleSelectionSamples"
    regulatory_context: Optional[str] = None
    scoped_attributes: Optional[List[Dict[str, Any]]] = None
    # Intelligent strategy fields  
    use_data_source: Optional[bool] = True
    distribution: Optional[Dict[str, float]] = None
    include_file_samples: Optional[bool] = False
    # Enhanced strategy fields
    use_anomaly_insights: Optional[bool] = True
    sampling_strategy: Optional[str] = "intelligent"
    data_source_id: Optional[int] = None


class SampleDecisionRequest(BaseModel):
    decision: str  # 'approved' or 'rejected'
    notes: Optional[str] = None


class BulkDecisionRequest(BaseModel):
    sample_ids: List[str]
    decision: str


class BulkApproveRequest(BaseModel):
    sample_ids: List[str]
    notes: Optional[str] = None


class BulkRejectRequest(BaseModel):
    sample_ids: List[str]
    reason: str = "Does not meet criteria"
    notes: Optional[str] = None


class UnifiedBulkOperationRequest(BaseModel):
    """Unified request for all bulk operations"""
    sample_ids: List[str]
    action: str  # "approve", "reject", "decide"
    decision: Optional[str] = None  # For decide action
    notes: Optional[str] = None
    reason: Optional[str] = "Does not meet criteria"  # For reject action


class SubmitSamplesRequest(BaseModel):
    sample_ids: List[str]
    notes: Optional[str] = None


class ReviewSamplesRequest(BaseModel):
    decision: str  # 'approved', 'rejected', 'revision_required'
    feedback: Optional[str] = None
    individual_feedback: Optional[Dict[str, str]] = None  # sample_id -> feedback
    individual_decisions: Optional[Dict[str, str]] = None  # sample_id -> 'approved' or 'rejected'


class ReportOwnerReviewRequest(BaseModel):
    """Request for report owner review submission"""
    decision: str  # 'approved', 'rejected', 'revision_required'
    feedback: Optional[str] = None
    sample_decisions: Optional[Dict[str, Dict[str, Any]]] = None
    assignment_id: Optional[str] = None


class UploadSamplesRequest(BaseModel):
    samples: List[Dict[str, Any]]


class StartPhaseRequest(BaseModel):
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    notes: Optional[str] = None


class IntelligentSamplingRequest(BaseModel):
    target_sample_size: int
    use_data_source: bool = True  # Whether to use actual data source or generate mock samples
    distribution: Optional[Dict[str, float]] = None  # Custom distribution if needed
    include_file_samples: bool = False  # Whether to include uploaded file samples

class EnhancedSampleGenerationRequest(BaseModel):
    sample_size: int
    use_anomaly_insights: bool = True  # Whether to leverage data profiling anomaly insights
    sampling_strategy: str = "intelligent"  # "intelligent", "random", "stratified", "anomaly_focused"
    data_source_id: Optional[int] = None  # Specific data source to use


@router.get("/cycles/{cycle_id}/reports/{report_id}/versions")
async def get_sample_selection_versions(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions for sample selection"""
    try:
        # Get phase
        phase_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase_obj = phase_result.scalar_one_or_none()
        
        if not phase_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample Selection phase not found"
            )
        
        # Get versions from version tables
        from app.models.sample_selection import SampleSelectionVersion
        versions_result = await db.execute(
            select(SampleSelectionVersion)
            .where(SampleSelectionVersion.phase_id == phase_obj.phase_id)
            .order_by(SampleSelectionVersion.version_number.desc())
        )
        versions = versions_result.scalars().all()
        
        # Get user names for created_by
        user_ids = [v.created_by_id for v in versions if v.created_by_id]
        users_query = await db.execute(
            select(User).where(User.user_id.in_(user_ids))
        )
        users = {u.user_id: f"{u.first_name} {u.last_name}" for u in users_query.scalars().all()}
        
        # Format response
        formatted_versions = []
        current_approved_version = max(
            [v.version_number for v in versions if (v.version_status.value if hasattr(v.version_status, 'value') else v.version_status) == "approved"],
            default=0
        )
        
        for v in versions:
            # Skip sample counting for now to avoid recursion
            approved_samples = 0
            rejected_samples = 0
            pending_samples = 0
            
            version_info = {
                "version_id": str(v.version_id),
                "version_number": v.version_number,
                "version_status": v.version_status.value if hasattr(v.version_status, 'value') else v.version_status,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "created_by": v.created_by_id,
                "created_by_name": users.get(v.created_by_id, "Unknown"),
                "is_current": (v.version_status.value if hasattr(v.version_status, 'value') else v.version_status) == "approved" and v.version_number == current_approved_version,
                "total_samples": v.actual_sample_size,
                "approved_samples": approved_samples,
                "rejected_samples": rejected_samples,
                "pending_samples": pending_samples,
                "change_reason": v.distribution_metrics.get("change_reason") if v.distribution_metrics and isinstance(v.distribution_metrics, dict) else None,
                "generation_method": v.activity_name,
                "approved_at": v.approved_at.isoformat() if v.approved_at else None,
                "approved_by": v.approved_by_id,
                "approval_notes": v.approval_notes,
                "metadata": v.version_metadata or {},
                "distribution_metrics": v.distribution_metrics or {},
                "submitted_at": v.submitted_at.isoformat() if v.submitted_at else None,
                "submission_notes": v.submission_notes
            }
            
            # Add report owner decision fields directly from columns
            version_info['report_owner_decision'] = v.report_owner_decision
            version_info['report_owner_feedback'] = v.report_owner_feedback
            version_info['report_owner_reviewed_at'] = v.report_owner_reviewed_at.isoformat() if v.report_owner_reviewed_at else None
            version_info['report_owner_reviewed_by'] = v.report_owner_reviewed_by_id
            
            # Check if version was submitted and has report owner feedback
            if (v.version_status.value if hasattr(v.version_status, 'value') else v.version_status) in ["pending_approval", "approved", "rejected"]:
                version_info['was_submitted'] = True
                version_info['submission_status'] = v.version_status.value if hasattr(v.version_status, 'value') else v.version_status
                
                # Check for report owner feedback
                version_info['has_report_owner_feedback'] = bool(v.report_owner_decision)
            
            # Check if reviewed by report owner
            if v.distribution_metrics and isinstance(v.distribution_metrics, dict) and v.distribution_metrics.get('reviewed_by_report_owner'):
                version_info['has_report_owner_feedback'] = True
            
            formatted_versions.append(version_info)
        
        # Sort by version number descending
        formatted_versions.sort(key=lambda x: x["version_number"], reverse=True)
        
        return formatted_versions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sample selection versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get versions: {str(e)}"
        )

@router.post("/cycles/{cycle_id}/reports/{report_id}/start")
async def start_sample_selection_phase(
    cycle_id: int,
    report_id: int,
    request: StartPhaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start the sample selection phase"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to start phase")
    
    # Get the workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    if phase.status == "Complete":
        raise HTTPException(status_code=400, detail="Phase already completed")
    elif phase.status == "In Progress":
        return {
            "message": "Sample Selection phase already in progress",
            "phase_status": phase.status,
            "actual_start_date": phase.actual_start_date.isoformat() if phase.actual_start_date else None
        }
    
    # Update phase status from Not Started to In Progress
    phase.status = "In Progress"
    phase.state = "In Progress"
    phase.actual_start_date = datetime.utcnow()
    phase.started_by = current_user.user_id
    if request.planned_start_date:
        phase.planned_start_date = datetime.fromisoformat(request.planned_start_date.replace('Z', '+00:00'))
    if request.planned_end_date:
        phase.planned_end_date = datetime.fromisoformat(request.planned_end_date.replace('Z', '+00:00'))
    
    await db.commit()
    
    return {
        "message": "Sample Selection phase started successfully",
        "phase_status": phase.status,
        "actual_start_date": phase.actual_start_date.isoformat() if phase.actual_start_date else None
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/samples")
async def get_samples(
    cycle_id: int,
    report_id: int,
    include_feedback: bool = Query(True),
    version: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all samples for a report - uses version tables"""
    from app.services.sample_selection_table_service import SampleSelectionTableService
    
    # Verify access
    if current_user.role not in ["Tester", "Test Manager", "Report Owner", "Report Owner Executive"]:
        raise HTTPException(status_code=403, detail="Not authorized to view samples")
    
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    # Migrate from phase_data if needed (one-time operation)
    await SampleSelectionTableService.migrate_from_phase_data(db, phase, current_user.user_id)
    
    # Get samples from version tables
    samples, version_obj = await SampleSelectionTableService.get_samples_for_display(
        db, phase.phase_id, version_number=version
    )
    
    return {"samples": samples}


# ============= INTERNAL SAMPLE GENERATION FUNCTIONS =============
# These are the core functions that do the actual work, without decorators

async def _generate_samples_basic_internal(
    cycle_id: int,
    report_id: int,
    request: SampleGenerationRequest,
    db: AsyncSession,
    current_user: User
):
    """Internal function for basic sample generation - no decorators"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to generate samples")
    
    # This will contain the actual logic from generate_samples function
    # For now, we'll call the original function but this should be refactored
    # to avoid the deprecation wrapper
    return await generate_samples.__wrapped__(cycle_id, report_id, request, db, current_user)


async def _generate_samples_intelligent_internal(
    cycle_id: int,
    report_id: int,
    request: IntelligentSamplingRequest,
    db: AsyncSession,
    current_user: User
):
    """Internal function for intelligent sample generation - no decorators"""
    if current_user.role not in ["Tester", "Test Manager", "Test Executive"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Call the unwrapped version to bypass deprecation decorator
    return await generate_intelligent_samples.__wrapped__(cycle_id, report_id, request, db, current_user)


async def _generate_samples_enhanced_internal(
    cycle_id: int,
    report_id: int,
    request: EnhancedSampleGenerationRequest,
    db: AsyncSession,
    current_user: User
):
    """Internal function for enhanced sample generation - no decorators"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to generate samples")
    
    # Call the unwrapped version to bypass deprecation decorator
    return await generate_enhanced_samples.__wrapped__(cycle_id, report_id, request, db, current_user)


# ============= UNIFIED SAMPLE GENERATION ENDPOINT =============
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/generate-unified")
async def generate_samples_unified(
    cycle_id: int,
    report_id: int,
    request: UnifiedSampleGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified endpoint for all sample generation strategies.
    Supports basic, intelligent, and enhanced generation through strategy parameter.
    """
    # Map to appropriate internal function based on strategy
    if request.strategy == "basic":
        # Convert to basic request format
        basic_request = SampleGenerationRequest(
            sample_size=request.sample_size,
            sample_type=request.sample_type or "Population CycleReportSampleSelectionSamples",
            regulatory_context=request.regulatory_context,
            scoped_attributes=request.scoped_attributes
        )
        return await _generate_samples_basic_internal(cycle_id, report_id, basic_request, db, current_user)
    
    elif request.strategy == "intelligent":
        # Convert to intelligent request format
        intelligent_request = IntelligentSamplingRequest(
            target_sample_size=request.sample_size,
            use_data_source=request.use_data_source if request.use_data_source is not None else True,
            distribution=request.distribution,
            include_file_samples=request.include_file_samples if request.include_file_samples is not None else False
        )
        return await _generate_samples_intelligent_internal(cycle_id, report_id, intelligent_request, db, current_user)
    
    elif request.strategy == "enhanced":
        # Convert to enhanced request format
        enhanced_request = EnhancedSampleGenerationRequest(
            sample_size=request.sample_size,
            use_anomaly_insights=request.use_anomaly_insights if request.use_anomaly_insights is not None else True,
            sampling_strategy=request.sampling_strategy or "intelligent",
            data_source_id=request.data_source_id
        )
        return await _generate_samples_enhanced_internal(cycle_id, report_id, enhanced_request, db, current_user)
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy: {request.strategy}. Must be one of: basic, intelligent, enhanced"
        )


# ============= DEPRECATED GENERATION ENDPOINTS =============
@deprecated_endpoint(
    alternative="/api/v1/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/generate-unified",
    removal_version="4.0.0",
    message="Use unified endpoint with strategy='basic'"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/generate")
async def generate_samples(
    cycle_id: int,
    report_id: int,
    request: SampleGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate samples using LLM"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to generate samples")
    
    # Get report info
    report_query = await db.execute(
        select(Report).options(selectinload(Report.lob)).where(Report.report_id == report_id)
    )
    report = report_query.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get scoped attributes if not provided
    if not request.scoped_attributes:
        # First get the cycle_report to ensure we're working with the right cycle/report combination
        cycle_report_query = await db.execute(
            select(CycleReport).where(
                and_(
                    CycleReport.cycle_id == cycle_id,
                    CycleReport.report_id == report_id
                )
            )
        )
        cycle_report = cycle_report_query.scalar_one_or_none()
        if not cycle_report:
            raise HTTPException(status_code=404, detail="Cycle report not found")
        
        # Get Planning phase to find attributes
        planning_phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
        )
        planning_phase = planning_phase_query.scalar_one_or_none()
        if not planning_phase:
            raise HTTPException(status_code=404, detail="Planning phase not found")
        
        # Import models for scoping
        from app.models.scoping import ScopingVersion, ScopingAttribute
        from sqlalchemy import cast, String
        
        # Get approved scoping version
        scoping_version = await db.execute(
            select(ScopingVersion).where(
                and_(
                    ScopingVersion.phase_id == planning_phase.phase_id,
                    cast(ScopingVersion.version_status, String).in_(['approved', 'pending_approval'])
                )
            ).order_by(ScopingVersion.version_number.desc())
        )
        latest_version = scoping_version.scalar_one_or_none()
        
        if not latest_version:
            logger.warning("No approved scoping version found, using all non-PK attributes")
        
        # Get scoped attributes from ScopingAttribute
        scoping_attributes = []
        if latest_version:
            scoped_attrs = await db.execute(
                select(ScopingAttribute).where(
                    and_(
                        ScopingAttribute.version_id == latest_version.version_id,
                        cast(ScopingAttribute.decision, String) == 'approved'
                    )
                )
            )
            scoping_attributes = scoped_attrs.scalars().all()
        
        # Also get all attributes from Planning phase for PK info
        from app.models.report_attribute import ReportAttribute
        all_attrs = await db.execute(
            select(ReportAttribute).where(
                ReportAttribute.phase_id == planning_phase.phase_id
            )
        )
        all_attributes_dict = {attr.attribute_name: attr for attr in all_attrs.scalars().all()}
        
        # Build scoped attributes list with full info
        request.scoped_attributes = []
        
        if scoping_attributes:
            # Use scoping decisions
            for scoped_attr in scoping_attributes:
                if scoped_attr.attribute_name in all_attributes_dict:
                    planning_attr = all_attributes_dict[scoped_attr.attribute_name]
                    request.scoped_attributes.append({
                        "attribute_name": scoped_attr.attribute_name,
                        "is_primary_key": planning_attr.is_primary_key,
                        "data_type": planning_attr.data_type,
                        "mandatory_flag": getattr(planning_attr, 'is_mandatory', True)
                    })
                else:
                    # Fallback if attribute not found in planning
                    request.scoped_attributes.append({
                        "attribute_name": scoped_attr.attribute_name,
                        "is_primary_key": scoped_attr.is_primary_key,
                        "data_type": scoped_attr.data_type or "String",
                        "mandatory_flag": True
                    })
        else:
            # No scoping done - use all non-PK attributes 
            logger.info("No scoping attributes found, using all non-PK attributes from planning")
            for attr_name, attr in all_attributes_dict.items():
                if not attr.is_primary_key:
                    request.scoped_attributes.append({
                        "attribute_name": attr_name,
                        "is_primary_key": False,
                        "data_type": attr.data_type,
                        "mandatory_flag": getattr(attr, 'is_mandatory', True)
                    })
        
        # Always add primary key attributes
        for attr_name, attr in all_attributes_dict.items():
            if attr.is_primary_key:
                # Check if already added
                if not any(a['attribute_name'] == attr_name for a in request.scoped_attributes):
                    request.scoped_attributes.append({
                        "attribute_name": attr_name,
                        "is_primary_key": True,
                        "data_type": attr.data_type,
                        "mandatory_flag": True
                    })
        logger.info(f"Loaded {len(request.scoped_attributes)} scoped attributes from database")
    
    # Determine prompt path based on report's regulation
    regulatory_framework = None
    if report.regulation:
        # Convert regulation to file path format (e.g., "FR Y-14M Schedule D.1" -> "fr_y_14m/schedule_d_1")
        reg_parts = report.regulation.lower().replace(" ", "_").replace(".", "_")
        # Handle common patterns
        if "fr_y_14m" in reg_parts and "schedule_d_1" in reg_parts:
            regulatory_framework = "fr_y_14m/schedule_d_1"
        elif "fr_y_14q" in reg_parts:
            regulatory_framework = "fr_y_14q"
        # Add more mappings as needed
    
    # Check if we have a specific prompt for this regulation
    prompt_path = None
    if regulatory_framework:
        specific_prompt_path = f"app/prompts/regulatory/{regulatory_framework}/sample_generation.txt"
        if os.path.exists(specific_prompt_path):
            prompt_path = specific_prompt_path
    
    # Fallback to default prompt
    if not prompt_path:
        prompt_path = "app/prompts/regulatory/fr_y_14m/schedule_d_1/sample_generation.txt"
        if not os.path.exists(prompt_path):
            raise HTTPException(status_code=500, detail="CycleReportSampleSelectionSamples generation prompt not found")
    
    # Log which prompt is being used
    logger.info(f"Report regulation: {report.regulation}")
    logger.info(f"Using sample generation prompt: {prompt_path}")
    logger.info(f"Regulatory context from request: {request.regulatory_context}")
    
    with open(prompt_path, 'r') as f:
        prompt_template_str = f.read()
    
    # Prepare context for prompt
    attr_descriptions = []
    attribute_fields = []
    attribute_details = []
    
    for attr in request.scoped_attributes:
        # Default data type if None
        data_type = attr.get('data_type') or 'String'
        
        attr_descriptions.append(f"- {attr['attribute_name']} ({data_type})")
        attribute_fields.append(f'"{attr["attribute_name"]}": "<{data_type}>"')
        
        detail = f"- {attr['attribute_name']}: {data_type}"
        if attr.get('is_primary_key'):
            detail += " (Primary Key)"
        if attr.get('mandatory_flag') == 'Mandatory':
            detail += " - REQUIRED"
        attribute_details.append(detail)
    
    # Substitute variables in prompt using manual replacement
    prompt = prompt_template_str
    prompt = prompt.replace("{scoped_attributes}", "\n".join(attr_descriptions))
    prompt = prompt.replace("{sample_size}", str(request.sample_size))
    prompt = prompt.replace("{regulation_context}", request.regulatory_context or "FR Y-14M Schedule D.1")
    prompt = prompt.replace("{risk_focus_areas}", "credit risk, operational risk, market risk")
    prompt = prompt.replace("{attribute_fields}", ",\n    ".join(attribute_fields))
    prompt = prompt.replace("{attribute_details}", "\n".join(attribute_details))
    
    # Log the prompt for debugging
    logger.info(f"Scoped attributes: {request.scoped_attributes}")
    logger.info(f"Attr descriptions: {attr_descriptions}")
    logger.info(f"Prompt after substitution (first 1000 chars): {prompt[:1000]}...")
    logger.info(f"Full prompt length: {len(prompt)} characters")
    # Log the section with scoped attributes
    scoped_section_start = prompt.find("**Scoped Attributes to Include:**")
    if scoped_section_start > 0:
        logger.info(f"Scoped attributes section: {prompt[scoped_section_start:scoped_section_start+500]}...")
    
    # Check if template substitution worked
    if "{scoped_attributes}" in prompt:
        logger.error("Template substitution FAILED - {scoped_attributes} still in prompt")
    if "{sample_size}" in prompt:
        logger.error("Template substitution FAILED - {sample_size} still in prompt")
    
    # Call LLM service directly
    llm_service = get_llm_service()
    
    try:
        # Get Claude provider
        provider = None
        if hasattr(llm_service, 'providers') and 'claude' in llm_service.providers:
            provider = llm_service.providers['claude']
        
        if not provider:
            raise HTTPException(status_code=503, detail="Claude LLM provider not available")
        
        # Direct provider call
        llm_response = await provider.generate(
            prompt=prompt,
            system_prompt="You are an expert in FR Y-14M regulatory reporting. Generate realistic sample data for testing."
        )
        
        # Parse response
        response_text = llm_response["content"]
        
        # Log the response for debugging
        logger.info(f"LLM Response: {response_text[:500]}...")  # Log first 500 chars
        logger.info(f"LLM Response type: {type(response_text)}, length: {len(response_text)}")
        
        # Try to parse JSON from response
        try:
            # First try direct JSON parsing
            generated_samples = json.loads(response_text)
            
            # If it's wrapped in an object with sample_data, extract it
            if isinstance(generated_samples, dict) and "cycle_report_sample_selection_samples" in generated_samples:
                generated_samples = generated_samples["cycle_report_sample_selection_samples"]
            
            # Extract sample_data from each sample if present
            processed_samples = []
            for sample in generated_samples:
                if isinstance(sample, dict) and "sample_data" in sample:
                    processed_samples.append(sample["sample_data"])
                else:
                    processed_samples.append(sample)
            generated_samples = processed_samples
            
        except json.JSONDecodeError:
            # Try to extract JSON array from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    samples_json = response_text[json_start:json_end]
                    generated_samples = json.loads(samples_json)
                    
                    # Extract sample_data if present
                    processed_samples = []
                    for sample in generated_samples:
                        if isinstance(sample, dict) and "sample_data" in sample:
                            processed_samples.append(sample["sample_data"])
                        else:
                            processed_samples.append(sample)
                    generated_samples = processed_samples
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM response as JSON, using fallback")
                    # Fallback samples if parsing fails
                    generated_samples = []
                    for i in range(request.sample_size):
                        sample_data = {"sample_number": f"SAMPLE_{i+1}"}
                        for attr in request.scoped_attributes:
                            data_type = attr.get("data_type") or "String"
                            if attr.get("is_primary_key"):
                                sample_data[attr["attribute_name"]] = f"REF_{uuid.uuid4().hex[:8].upper()}"
                            elif data_type == "String":
                                sample_data[attr["attribute_name"]] = f"Value_{i+1}"
                            elif data_type in ["Decimal", "Number", "Integer"]:
                                sample_data[attr["attribute_name"]] = 1000.00 + (i * 100)
                            elif data_type == "Date":
                                sample_data[attr["attribute_name"]] = "2024-01-01"
                            else:
                                sample_data[attr["attribute_name"]] = f"Data_{i+1}"
                        generated_samples.append(sample_data)
            else:
                logger.warning("No JSON array found in LLM response, using fallback")
                # Use fallback
                generated_samples = []
                for i in range(request.sample_size):
                    sample_data = {"sample_number": f"SAMPLE_{i+1}"}
                    for attr in request.scoped_attributes:
                        data_type = attr.get("data_type") or "String"
                        if attr.get("is_primary_key"):
                            sample_data[attr["attribute_name"]] = f"REF_{uuid.uuid4().hex[:8].upper()}"
                        elif data_type == "String":
                            sample_data[attr["attribute_name"]] = f"Value_{i+1}"
                        elif data_type in ["Decimal", "Number", "Integer"]:
                            sample_data[attr["attribute_name"]] = 1000.00 + (i * 100)
                        elif data_type == "Date":
                            sample_data[attr["attribute_name"]] = "2024-01-01"
                        else:
                            sample_data[attr["attribute_name"]] = f"Data_{i+1}"
                    generated_samples.append(sample_data)
        
        # Store samples using the version tables
        # Get or create workflow phase record
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Sample Selection phase not found")
        
        # Migrate from phase_data if needed (one-time operation)
        await SampleSelectionTableService.migrate_from_phase_data(db, phase, current_user.user_id)
        
        # Get or create current version
        version = await SampleSelectionTableService.get_or_create_version(
            db, phase.phase_id, current_user.user_id
        )
        
        # Create new samples
        logger.info(f"Generated {len(generated_samples)} samples from LLM")
        samples_created = []
        for idx, sample_data in enumerate(generated_samples):
            # Find primary key value
            primary_key_value = None
            for attr in request.scoped_attributes:
                if attr.get("is_primary_key") and attr["attribute_name"] in sample_data:
                    primary_key_value = str(sample_data[attr["attribute_name"]])
                    break
            
            if not primary_key_value:
                primary_key_value = f"SAMPLE_{uuid.uuid4().hex[:8].upper()}"
            
            # Don't auto-assign LOB - let tester assign it
            # LOB assignment should be done by tester, not inherited from report
            
            # Create sample data record
            sample_record = {
                "primary_attribute_value": primary_key_value,
                "data_row_snapshot": sample_data,
                "sample_category": "clean",
                "sample_source": "tester",
                "risk_score": 0.5,
                "confidence_score": 0.85,
                "metadata": {
                    "generation_method": "LLM Generated",
                    "generated_at": datetime.utcnow().isoformat(),
                    "generated_by": f"{current_user.first_name} {current_user.last_name}"
                }
            }
            
            samples_created.append(sample_record)
        
        # Use table service to create samples
        created_samples = await SampleSelectionTableService.create_samples_from_generation(
            db, version.version_id, samples_created, current_user.user_id
        )
        
        # Update version metadata
        version.target_sample_size = request.sample_size
        version.selection_criteria = {
            "method": "LLM Generated",
            "regulatory_context": request.regulatory_context or "FR Y-14M Schedule D.1",
            "scoped_attributes": request.scoped_attributes
        }
        version.updated_at = datetime.utcnow()
        version.updated_by_id = current_user.user_id
        
        logger.info(f"Created {len(created_samples)} samples in version {version.version_number}")
        
        # Clear phase_data samples to prevent duplication
        if phase.phase_data and "cycle_report_sample_selection_samples" in phase.phase_data:
            phase.phase_data["cycle_report_sample_selection_samples"] = []
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(phase, 'phase_data')
        
        # Create audit log - DISABLED temporarily
        # audit_log = LLMAuditLog(
        #     cycle_id=cycle_id,
        #     report_id=report_id,
        #     llm_provider="claude",
        #     prompt_template=prompt_path,
        #     request_payload={
        #         "prompt": prompt[:500] + "...",  # Truncate for storage
        #         "sample_size": request.sample_size,
        #         "regulatory_context": request.regulatory_context or "FR Y-14M Schedule D.1"
        #     },
        #     response_payload={
        #         "samples_generated": len(samples_created),
        #         "success": True
        #     },
        #     execution_time_ms=1000,  # TODO: Track actual time
        #     token_usage={
        #         "total_tokens": llm_response.get("usage", {}).get("total_tokens", 0),
        #         "prompt_tokens": llm_response.get("usage", {}).get("prompt_tokens", 0),
        #         "completion_tokens": llm_response.get("usage", {}).get("completion_tokens", 0)
        #     },
        #     executed_at=datetime.utcnow(),
        #     executed_by=current_user.user_id
        # )
        # db.add(audit_log)
        
        await db.commit()
        
        return {
            "samples_generated": len(samples_created),
            "message": f"Successfully generated {len(samples_created)} samples"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generating samples: {str(e)}")


@router.put("/cycles/{cycle_id}/reports/{report_id}/samples/{sample_id}/lob")
async def update_sample_lob(
    cycle_id: int,
    report_id: int,
    sample_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update LOB assignment for a sample"""
    logger.info(f"Updating LOB for sample {sample_id} in cycle {cycle_id}, report {report_id}")
    logger.info(f"Request data: {request}")
    
    # Allow both Testers and Report Owners to update LOB assignments
    if current_user.role not in ["Tester", "Test Manager", "Report Owner", "Report Owner Executive"]:
        raise HTTPException(status_code=403, detail="Not authorized to update LOB assignments")
    
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    # Get the LOB name from request
    lob_name = request.get('lob_assignment')
    if not lob_name:
        raise HTTPException(status_code=400, detail="LOB assignment is required")
    
    # Get the LOB by name
    lob_result = await db.execute(
        select(LOB).where(LOB.lob_name == lob_name)
    )
    lob = lob_result.scalar_one_or_none()
    
    if not lob:
        raise HTTPException(status_code=404, detail=f"LOB '{lob_name}' not found")
    
    # Find and update the sample in the sample selection tables
    sample_result = await db.execute(
        select(SampleSelectionSample)
        .where(SampleSelectionSample.sample_id == uuid.UUID(sample_id))
    )
    sample = sample_result.scalar_one_or_none()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    # Update the LOB assignment
    sample.lob_id = lob.lob_id
    sample.updated_at = datetime.utcnow()
    sample.updated_by_id = current_user.user_id
    
    # Add sample to session to ensure it's tracked
    db.add(sample)
    
    await db.commit()
    
    logger.info(f"Successfully updated LOB assignment for sample {sample_id} to {lob_name}")
    
    return {
        "message": "LOB assignment updated successfully",
        "sample_id": sample_id,
        "lob_assignment": lob_name
    }


@router.put("/cycles/{cycle_id}/reports/{report_id}/samples/{sample_id}/decision")
async def update_sample_decision(
    cycle_id: int,
    report_id: int,
    sample_id: str,
    request: SampleDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update tester decision for a sample"""
    logger.info(f"update_sample_decision called - sample_id: {sample_id}, decision: {request.decision}, user: {current_user.email}, role: {current_user.role}")
    
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to update sample decision")
    
    try:
        # Parse UUID from sample_id string if needed
        import uuid
        if isinstance(sample_id, str) and not sample_id.startswith('C'):
            sample_uuid = uuid.UUID(sample_id)
        else:
            # Handle legacy sample IDs - this will be phased out
            raise HTTPException(status_code=400, detail="Legacy sample IDs not supported with version tables")
        
        # Get the sample to check its version
        sample_result = await db.execute(
            select(SampleSelectionSample).where(
                SampleSelectionSample.sample_id == sample_uuid
            )
        )
        sample = sample_result.scalar_one_or_none()
        
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        
        # Check if the version is editable
        version_result = await db.execute(
            select(SampleSelectionVersion).where(
                SampleSelectionVersion.version_id == sample.version_id
            )
        )
        version = version_result.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Sample version not found")
        
        # Only allow editing draft versions
        if version.version_status != VersionStatus.DRAFT:
            logger.warning(f"Attempt to edit non-draft version: {version.version_status}")
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot update sample decision. Version is {version.version_status}, only draft versions can be edited."
            )
        
        # Update using table service
        updated_sample = await SampleSelectionTableService.update_sample_decision(
            db,
            sample_uuid,
            request.decision,
            request.notes,
            current_user.user_id,
            current_user.role
        )
        
        await db.commit()
        
        logger.info(f"Successfully updated sample {sample_id} decision to {request.decision}")
        return {"message": f"Sample {request.decision} successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating sample decision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= UNIFIED BULK OPERATIONS ENDPOINT =============
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/bulk-operation")
async def bulk_sample_operation(
    cycle_id: int,
    report_id: int,
    request: UnifiedBulkOperationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified endpoint for all bulk sample operations.
    Supports approve, reject, and decide actions.
    """
    if request.action == "approve":
        # Convert to bulk approve request
        approve_request = BulkApproveRequest(
            sample_ids=request.sample_ids,
            notes=request.notes
        )
        return await bulk_approve_samples(cycle_id, report_id, approve_request, db, current_user)
    
    elif request.action == "reject":
        # Convert to bulk reject request
        reject_request = BulkRejectRequest(
            sample_ids=request.sample_ids,
            reason=request.reason or "Does not meet criteria",
            notes=request.notes
        )
        return await bulk_reject_samples(cycle_id, report_id, reject_request, db, current_user)
    
    elif request.action == "decide":
        # For decide action, directly update the samples based on decision
        if not request.decision:
            raise HTTPException(
                status_code=400,
                detail="Decision field is required for decide action"
            )
        
        # Reuse the logic based on decision type
        if request.decision == "approved":
            approve_request = BulkApproveRequest(
                sample_ids=request.sample_ids,
                notes=request.notes
            )
            return await bulk_approve_samples(cycle_id, report_id, approve_request, db, current_user)
        elif request.decision == "rejected":
            reject_request = BulkRejectRequest(
                sample_ids=request.sample_ids,
                reason=request.reason or "Does not meet criteria",
                notes=request.notes
            )
            return await bulk_reject_samples(cycle_id, report_id, reject_request, db, current_user)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision: {request.decision}. Must be 'approved' or 'rejected'"
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {request.action}. Must be one of: approve, reject, decide"
        )


# ============= DEPRECATED BULK OPERATION ENDPOINTS =============
@deprecated_endpoint(
    alternative="/api/v1/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/bulk-operation",
    removal_version="4.0.0",
    message="Use unified endpoint with action='approve'"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/bulk-approve")
async def bulk_approve_samples(
    cycle_id: int,
    report_id: int,
    request: BulkApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk approve multiple samples - handles both tester and report owner approvals based on user role"""
    
    try:
        # Parse UUIDs from sample IDs
        import uuid
        sample_uuids = []
        for sample_id in request.sample_ids:
            try:
                sample_uuids.append(uuid.UUID(sample_id))
            except ValueError:
                # Skip invalid UUIDs
                logger.warning(f"Invalid sample UUID: {sample_id}")
                continue
        
        if not sample_uuids:
            raise HTTPException(status_code=400, detail="No valid sample IDs provided")
        
        # Update samples using table service
        approved_count = 0
        for sample_uuid in sample_uuids:
            try:
                await SampleSelectionTableService.update_sample_decision(
                    db,
                    sample_uuid,
                    "approved",
                    request.notes,
                    current_user.user_id,
                    current_user.role
                )
                approved_count += 1
            except Exception as e:
                logger.error(f"Failed to update sample {sample_uuid}: {str(e)}")
                continue
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Bulk approved {approved_count} samples",
            "approved_count": approved_count,
            "sample_ids": request.sample_ids,
            "role": current_user.role
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in bulk approve: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@deprecated_endpoint(
    alternative="/api/v1/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/bulk-operation",
    removal_version="4.0.0",
    message="Use unified endpoint with action='reject'"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/bulk-reject")
async def bulk_reject_samples(
    cycle_id: int,
    report_id: int,
    request: BulkRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk reject multiple samples - handles both tester and report owner rejections based on user role"""
    
    try:
        # Parse UUIDs from sample IDs
        import uuid
        sample_uuids = []
        for sample_id in request.sample_ids:
            try:
                sample_uuids.append(uuid.UUID(sample_id))
            except ValueError:
                # Skip invalid UUIDs
                logger.warning(f"Invalid sample UUID: {sample_id}")
                continue
        
        if not sample_uuids:
            raise HTTPException(status_code=400, detail="No valid sample IDs provided")
        
        # Update samples using table service
        rejected_count = 0
        notes = request.notes
        if hasattr(request, 'reason') and request.reason:
            notes = f"{request.reason}\n{notes}" if notes else request.reason
        
        for sample_uuid in sample_uuids:
            try:
                await SampleSelectionTableService.update_sample_decision(
                    db,
                    sample_uuid,
                    "rejected",
                    notes,
                    current_user.user_id,
                    current_user.role
                )
                rejected_count += 1
            except Exception as e:
                logger.error(f"Failed to update sample {sample_uuid}: {str(e)}")
                continue
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Bulk rejected {rejected_count} samples",
            "rejected_count": rejected_count,
            "sample_ids": request.sample_ids,
            "role": current_user.role
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in bulk reject: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cycles/{cycle_id}/reports/{report_id}/samples/bulk-decision")
async def update_bulk_decisions(
    cycle_id: int,
    report_id: int,
    request: BulkDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update decisions for multiple samples"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to update sample decisions")
    
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    # Get samples from metadata
    if not phase.phase_data or "cycle_report_sample_selection_samples" not in phase.phase_data:
        raise HTTPException(status_code=404, detail="No samples found")
    
    samples = phase.phase_data["cycle_report_sample_selection_samples"]
    
    # Update matching samples
    updated_count = 0
    for i, sample in enumerate(samples):
        if sample.get('sample_id') in request.sample_ids:
            samples[i]['tester_decision'] = request.decision
            samples[i]['tester_decision_at'] = datetime.utcnow().isoformat()
            samples[i]['tester_decision_by_id'] = current_user.user_id
            samples[i]['tester_decision_by'] = f"{current_user.first_name} {current_user.last_name}"
            samples[i]['updated_at'] = datetime.utcnow().isoformat()
            updated_count += 1
    
    # Update phase metadata
    phase.phase_data["cycle_report_sample_selection_samples"] = samples
    phase.phase_data['last_updated'] = datetime.utcnow().isoformat()
    
    # Flag the object as modified for SQLAlchemy to track JSONB changes
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(phase, 'phase_data')
    
    await db.commit()
    
    return {
        "message": f"Updated {updated_count} samples",
        "samples_updated": updated_count
    }


@deprecated_endpoint(
    alternative="/api/v1/sample-selection/versions/{version_id}/submit",
    removal_version="4.0.0",
    message="Use version-based submit endpoint"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/submit")
async def submit_samples(
    cycle_id: int,
    report_id: int,
    request: SubmitSamplesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit samples for report owner approval using version tables.
    """
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to submit samples")
    
    try:
        # Get workflow phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Sample Selection phase not found")
        
        # Get the latest draft version for submission
        from app.models.sample_selection import VersionStatus
        latest_draft_result = await db.execute(
            select(SampleSelectionVersion)
            .where(
                and_(
                    SampleSelectionVersion.phase_id == phase.phase_id,
                    SampleSelectionVersion.version_status == VersionStatus.DRAFT
                )
            )
            .order_by(SampleSelectionVersion.version_number.desc())
            .limit(1)
        )
        current_version = latest_draft_result.scalar_one_or_none()
        
        if not current_version:
            raise HTTPException(
                status_code=404, 
                detail="No draft version found to submit. Create a new version first."
            )
        
        # Count approved samples
        from app.models.sample_selection import SampleSelectionSample, SampleDecision
        approved_count_result = await db.execute(
            select(func.count(SampleSelectionSample.sample_id)).where(
                and_(
                    SampleSelectionSample.version_id == current_version.version_id,
                    SampleSelectionSample.tester_decision == SampleDecision.APPROVED
                )
            )
        )
        approved_count = approved_count_result.scalar()
        
        if approved_count == 0:
            raise HTTPException(status_code=400, detail="No samples marked as 'approved' to submit")
        
        # Submit version for approval
        updated_version = await SampleSelectionTableService.submit_version_for_approval(
            db,
            current_version.version_id,
            current_user.user_id,
            request.notes
        )
        
        # Create Universal Assignment for Report Owner BEFORE committing
        try:
            from app.models.universal_assignment import UniversalAssignment
            from app.models.report import Report
            from app.models.user import User
            from app.models.test_cycle import TestCycle
            
            # Get report info with LOB relationship
            report_query = await db.execute(
                select(Report).options(selectinload(Report.lob)).where(Report.report_id == report_id)
            )
            report = report_query.scalar_one_or_none()
            
            # Get cycle info
            cycle = await db.get(TestCycle, cycle_id)
            
            if report and report.report_owner_id:
                # Get user info using query instead of get
                user_query = await db.execute(
                    select(User).where(User.user_id == current_user.user_id)
                )
                from_user = user_query.scalar_one_or_none()
                
                # Create assignment for report owner
                assignment = UniversalAssignment(
                    assignment_type="Sample Selection Approval",
                    from_role=from_user.role if from_user else "Tester",  # Role of the submitter
                    to_role="Report Owner",  # Fixed role for sample approval
                    from_user_id=current_user.user_id,
                    to_user_id=report.report_owner_id,
                    title="Review Sample Selection",
                    description=f"Please review and approve sample selection for {report.report_name}",
                    context_type="Report",  # Use enum value
                    context_data={
                        "cycle_id": cycle_id,  # Keep as integer
                        "report_id": report_id,  # Keep as integer
                        "phase_id": phase.phase_id,
                        "phase_name": "Sample Selection",
                        "version_id": str(updated_version.version_id),
                        "version_number": updated_version.version_number,
                        "submitted_by": current_user.user_id,
                        "submitted_at": datetime.utcnow().isoformat(),
                        "submission_notes": request.notes,
                        "total_samples": updated_version.actual_sample_size,
                        "included_samples": approved_count,  # Already calculated above
                        "report_name": report.report_name,
                        "cycle_name": cycle.cycle_name if cycle else None,
                        "lob": report.lob.lob_name if report.lob else "Unknown"
                },
                priority="High",
                due_date=datetime.utcnow() + timedelta(days=2),  # 2 day SLA
                created_by_id=current_user.user_id,
                    updated_by_id=current_user.user_id
                )
                db.add(assignment)
                logger.info(f"Created Sample Selection Approval assignment for Report Owner {report.report_owner_id}")
            else:
                logger.warning(f"No Report Owner found for report {report_id}")
        except Exception as e:
            logger.error(f"Failed to create UniversalAssignment: {str(e)}")
            logger.error(f"Assignment details - Type: Sample Selection Approval, From: {current_user.user_id}, To: {report.report_owner_id if 'report' in locals() and report else 'No report owner'}")
            # Don't fail the submission if assignment creation fails
            import traceback
            logger.error(traceback.format_exc())
        
        # Update workflow phase status
        if phase.status == "In Progress":
            phase.status = "Pending Approval"
        
        # Commit everything together
        await db.commit()
        
        return {
            "message": "Samples submitted for approval",
            "version_id": str(updated_version.version_id),
            "version_number": updated_version.version_number,
            "samples_submitted": approved_count
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error submitting samples: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cycles/{cycle_id}/reports/{report_id}/feedback")
async def get_report_owner_feedback(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Report Owner feedback for sample selection"""
    
    # Get completed assignments for this report
    from app.models.universal_assignment import UniversalAssignment
    
    feedback_query = await db.execute(
        select(UniversalAssignment).where(
            and_(
                UniversalAssignment.context_type == "Report",
                UniversalAssignment.status == "Completed",
                UniversalAssignment.context_data['cycle_id'].astext.cast(Integer) == cycle_id,
                UniversalAssignment.context_data['report_id'].astext.cast(Integer) == report_id,
                UniversalAssignment.completion_data.isnot(None)
            )
        ).order_by(UniversalAssignment.completed_at.desc())
    )
    
    assignments = feedback_query.scalars().all()
    
    feedback_list = []
    for assignment in assignments:
        completion_data = assignment.completion_data or {}
        decision = completion_data.get('decision')
        
        # Only include feedback from Report Owner reviews
        if decision in ['approved', 'rejected', 'revision_required']:
            # Get sample-specific feedback
            individual_decisions = completion_data.get('individual_decisions', {})
            individual_feedback = completion_data.get('individual_feedback', {})
            
            # Get the workflow phase to extract sample details
            phase_query = await db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Sample Selection"
                    )
                )
            )
            phase = phase_query.scalar_one_or_none()
            
            samples_feedback = []
            if phase:
                # Get samples from version tables
                version_id = assignment.context_data.get('version_id')
                if version_id:
                    from app.models.sample_selection import SampleSelectionSample
                    from app.models.lob import LOB
                    
                    # Get samples from this version
                    samples_result = await db.execute(
                        select(SampleSelectionSample, LOB)
                        .join(LOB, SampleSelectionSample.lob_id == LOB.lob_id)
                        .where(SampleSelectionSample.version_id == version_id)
                    )
                    samples_with_lobs = samples_result.all()
                    
                    # Get sample IDs from context
                    sample_ids = assignment.context_data.get('sample_ids', [])
                    
                    for sample, lob in samples_with_lobs:
                        if str(sample.sample_id) in sample_ids:
                            samples_feedback.append({
                                'sample_id': str(sample.sample_id),
                                'report_owner_decision': individual_decisions.get(str(sample.sample_id)),
                                'report_owner_feedback': individual_feedback.get(str(sample.sample_id)),
                                'sample_category': sample.sample_category.value.upper() if hasattr(sample.sample_category, 'value') else str(sample.sample_category).upper(),
                                'attribute_focus': "Customer ID",  # TODO: Get from config
                                'lob_assignment': lob.lob_name,
                                'tester_decision': sample.tester_decision.value if sample.tester_decision and hasattr(sample.tester_decision, 'value') else sample.tester_decision
                            })
            
            # Get user info
            user_query = await db.execute(
                select(User).where(User.user_id == assignment.completed_by_user_id)
            )
            reviewer = user_query.scalar_one_or_none()
            
            feedback_list.append({
                'submission_id': assignment.context_data.get('submission_id'),
                'version_number': assignment.context_data.get('version_number', 1),
                'decision': decision,
                'feedback': completion_data.get('feedback', ''),
                'reviewed_at': assignment.completed_at.isoformat() if assignment.completed_at else None,
                'reviewed_by': f"{reviewer.first_name} {reviewer.last_name}" if reviewer else "Unknown",
                'samples_feedback': samples_feedback
            })
    
    return {"feedback": feedback_list}


@router.get("/cycles/{cycle_id}/reports/{report_id}/sample-review/{version_id}")
async def get_report_owner_review(
    cycle_id: int,
    report_id: int,
    version_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get samples for report owner review - compatible with SampleReviewPage component"""
    if current_user.role not in ["Report Owner", "Report Owner Executive", "Admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # First get the phase_id for this cycle/report
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Sample Selection phase not found")
        
        # Get the version using phase_id
        version_query = await db.execute(
            select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == phase.phase_id,
                    SampleSelectionVersion.version_id == version_id
                )
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Get samples for this version that were approved by tester
        from sqlalchemy.orm import selectinload
        samples_query = await db.execute(
            select(SampleSelectionSample).options(
                selectinload(SampleSelectionSample.lob),
                selectinload(SampleSelectionSample.tester_decided_by),
                selectinload(SampleSelectionSample.created_by)
            ).where(
                and_(
                    SampleSelectionSample.version_id == version_id,
                    SampleSelectionSample.tester_decision == "approved"
                )
            ).order_by(
                SampleSelectionSample.sample_category,
                SampleSelectionSample.sample_identifier
            )
        )
        samples = samples_query.scalars().all()
        
        # Get report details
        report_query = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = report_query.scalar_one_or_none()
        
        # Format response compatible with SampleReviewPage
        return {
            "set_id": version_id,  # Use version_id as set_id
            "version_number": version.version_number,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
            "submission_notes": version.submission_notes,
            "status": version.version_status.value if hasattr(version.version_status, 'value') else version.version_status,
            "report_name": report.report_name if report else "Unknown Report",
            "total_samples": len(samples),
            "samples": [
                {
                    "sample_id": str(sample.sample_id),
                    "sample_identifier": sample.sample_identifier,
                    "sample_data": sample.sample_data,
                    "sample_category": sample.sample_category,
                    "tester_decision": sample.tester_decision,
                    "tester_decision_notes": sample.tester_decision_notes,
                    "tester_decision_at": sample.tester_decision_at.isoformat() if sample.tester_decision_at else None,
                    "tester_decision_by": f"{sample.tester_decided_by.first_name} {sample.tester_decided_by.last_name}" if sample.tester_decided_by else None,
                    "report_owner_decision": sample.report_owner_decision,
                    "report_owner_decision_notes": sample.report_owner_decision_notes,
                    "generation_metadata": sample.generation_metadata or {},
                    "lob_assignment": sample.lob.lob_name if sample.lob else None,
                    "generated_by": f"{sample.created_by.first_name} {sample.created_by.last_name}" if sample.created_by else "System",
                    # Map to expected fields for frontend compatibility
                    "primary_attribute_name": sample.sample_data.get("primary_attribute_name", "Unknown"),
                    "primary_attribute_value": sample.sample_data.get("primary_attribute_value", sample.sample_identifier),
                    "data_columns": sample.sample_data.get("data_columns", {}),
                    "attribute_focus": sample.generation_metadata.get("target_attribute") if sample.generation_metadata else None,
                    "rationale": sample.generation_metadata.get("rationale") if sample.generation_metadata else None,
                    "dq_rule_id": sample.generation_metadata.get("dq_rule_id") if sample.generation_metadata else None,
                    "dq_rule_result": sample.generation_metadata.get("dq_rule_result") if sample.generation_metadata else None
                }
                for sample in samples
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving samples for review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cycles/{cycle_id}/reports/{report_id}/sample-review/{version_id}/submit")
async def submit_report_owner_review(
    cycle_id: int,
    report_id: int,
    version_id: str,
    request: ReportOwnerReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit report owner review for samples"""
    if current_user.role not in ["Report Owner", "Report Owner Executive", "Admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # First get the phase_id for this cycle/report
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Sample Selection phase not found")
        
        # Get the version using phase_id
        version_query = await db.execute(
            select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == phase.phase_id,
                    SampleSelectionVersion.version_id == version_id
                )
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Update version status based on decision
        if request.decision == "approved":
            version.version_status = VersionStatus.APPROVED
            version.approved_at = datetime.utcnow()
            version.approved_by_id = current_user.user_id
            version.approval_notes = request.feedback
        elif request.decision == "rejected":
            version.version_status = VersionStatus.REJECTED
            version.submission_notes = request.feedback
        elif request.decision == "revision_required":
            version.version_status = VersionStatus.REJECTED  # Keep as rejected, tester will create new version
            version.submission_notes = request.feedback
        
        # Store report owner decision in proper columns
        version.report_owner_decision = request.decision
        version.report_owner_feedback = request.feedback
        version.report_owner_reviewed_at = datetime.utcnow()
        version.report_owner_reviewed_by_id = current_user.user_id
        
        # Update individual sample decisions if provided
        if request.sample_decisions:
            logger.info(f"Processing {len(request.sample_decisions)} sample decisions")
            for sample_id, decision_data in request.sample_decisions.items():
                logger.info(f"Processing sample {sample_id}: {decision_data}")
                sample_query = await db.execute(
                    select(SampleSelectionSample).where(
                        SampleSelectionSample.sample_id == sample_id
                    )
                )
                sample = sample_query.scalar_one_or_none()
                
                if sample and str(sample.version_id) == str(version_id):
                    logger.info(f"Updating sample {sample_id} with decision: {decision_data.get('decision')}")
                    sample.report_owner_decision = decision_data.get("decision")
                    sample.report_owner_decision_notes = decision_data.get("notes")
                    sample.report_owner_decision_at = datetime.utcnow()
                    sample.report_owner_decision_by_id = current_user.user_id
                    sample.updated_at = datetime.utcnow()
                    sample.updated_by_id = current_user.user_id
                    db.add(sample)  # Important: Add the modified object to the session
                else:
                    logger.warning(f"Sample {sample_id} not found or version mismatch. Sample version: {sample.version_id if sample else 'None'}, Expected: {version_id}")
        
        # Update workflow phase status
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if phase:
            if request.decision == "approved":
                phase.status = "Complete"
                phase.completed_at = datetime.utcnow()
            elif request.decision == "rejected":
                phase.status = "Pending Approval"  # Stay in pending for re-review
            else:
                phase.status = "In Progress"
            
            phase.updated_at = datetime.utcnow()
            phase.updated_by_id = current_user.user_id
        
        # Complete the assignment
        if request.assignment_id:
            assignment_service = UniversalAssignmentService()
            await assignment_service.complete_assignment(
                db=db,
                assignment_id=request.assignment_id,
                completed_by_user_id=current_user.user_id,
                completion_notes=request.feedback,
                completion_data={
                    "decision": request.decision,
                    "sample_decisions": request.sample_decisions
                }
            )
        
        await db.commit()
        
        return {
            "message": f"Review submitted: {request.decision}",
            "version_status": version.version_status.value if hasattr(version.version_status, 'value') else version.version_status,
            "phase_status": phase.status if phase else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting report owner review: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cycles/{cycle_id}/reports/{report_id}/samples/analytics")
async def get_sample_analytics(
    cycle_id: int,
    report_id: int,
    version_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics for sample selection phase"""
    try:
        # Use Universal Metrics Service like other pages do
        from app.services.universal_metrics_service import get_universal_metrics_service, MetricsContext
        
        context = MetricsContext(
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=current_user.user_id,
            user_role=current_user.role,
            phase_name="Sample Selection"
        )
        
        metrics_service = get_universal_metrics_service(db)
        universal_metrics = await metrics_service.get_metrics(context)
        
        # Map universal metrics to sample selection format
        metrics_dict = {
            "total_attributes": universal_metrics.total_attributes,
            "scoped_attributes_non_pk": universal_metrics.scoped_attributes_non_pk,
            "scoped_attributes_pk": universal_metrics.scoped_attributes_pk,
            "lobs_count": universal_metrics.lobs_count,
            "data_providers_count": universal_metrics.data_providers_count
        }
        
        # Get workflow phase for phase-specific data
        # Use text query to avoid enum issues
        phase_query = await db.execute(
            text("""
                SELECT * FROM workflow_phases 
                WHERE cycle_id = :cycle_id 
                AND report_id = :report_id 
                AND phase_name::text = 'Sample Selection'
            """),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        phase_row = phase_query.first()
        
        if phase_row:
            # Convert to object-like structure
            class PhaseObj:
                def __init__(self, row):
                    self.phase_id = row.phase_id
                    self.status = row.status
                    self.phase_data = row.phase_data
                    self.actual_start_date = row.actual_start_date
                    self.created_at = row.created_at
            phase = PhaseObj(phase_row)
        else:
            phase = None
        
        
        if not phase:
            return {
                "total_samples": 0,
                "included_samples": 0,
                "excluded_samples": 0,
                "pending_samples": 0,
                "submitted_samples": 0,
                "approved_samples": 0,
                "rejected_samples": 0,
                "revision_required_samples": 0,
                "phase_status": "Not Started",
                "can_complete_phase": False,
                "total_submissions": 0,
                "latest_submission": None,
                # Metrics from Universal Metrics Service
                "total_attributes": metrics_dict["total_attributes"],
                "scoped_attributes": metrics_dict["scoped_attributes_non_pk"],  # Non-PK for consistency
                "pk_attributes": metrics_dict["scoped_attributes_pk"],
                "total_lobs": metrics_dict["lobs_count"],
                "total_data_providers": metrics_dict["data_providers_count"],
                "started_at": None
            }
        
        # Calculate stats from samples table
        from app.models.sample_selection import SampleSelectionSample, SampleSelectionVersion
        
        # Get the latest approved version
        version_query = await db.execute(
            select(SampleSelectionVersion).where(
                and_(
                    SampleSelectionVersion.phase_id == phase.phase_id,
                    SampleSelectionVersion.version_status == VersionStatus.APPROVED
                )
            ).order_by(SampleSelectionVersion.version_number.desc()).limit(1)
        )
        approved_version = version_query.scalar_one_or_none()
        
        if not approved_version:
            # If no approved version, get the latest version
            version_query = await db.execute(
                select(SampleSelectionVersion).where(
                    SampleSelectionVersion.phase_id == phase.phase_id
                ).order_by(SampleSelectionVersion.version_number.desc()).limit(1)
            )
            approved_version = version_query.scalar_one_or_none()
        
        # Get samples from the specific version
        if approved_version:
            samples_query = await db.execute(
                select(SampleSelectionSample).where(
                    and_(
                        SampleSelectionSample.phase_id == phase.phase_id,
                        SampleSelectionSample.version_id == approved_version.version_id
                    )
                )
            )
            samples = samples_query.scalars().all()
        else:
            samples = []
        
        stats = {
            'total': len(samples),
            'included': sum(1 for s in samples if s.tester_decision == 'approved'),
            'excluded': sum(1 for s in samples if s.tester_decision == 'rejected'),
            'pending': sum(1 for s in samples if not s.tester_decision),
            'submitted': sum(1 for s in samples if s.report_owner_decision is not None),
            'approved': sum(1 for s in samples if s.report_owner_decision == 'approved'),  # Report owner approved samples
            'rejected': sum(1 for s in samples if s.report_owner_decision == 'rejected'),
            'revision_required': sum(1 for s in samples if s.report_owner_decision == 'revision_required')
        }
        
        # Get latest submission info
        submissions = phase.phase_data.get('submissions', []) if phase.phase_data else []
        latest_submission = None
        
        if submissions:
            # Sort by version number to get latest
            sorted_submissions = sorted(submissions, key=lambda x: x.get('version_number', 0), reverse=True)
            latest = sorted_submissions[0]
            latest_submission = {
                "submission_id": latest.get('submission_id'),
                "version": latest.get('version_number'),
                "status": latest.get('status', 'pending'),
                "submitted_at": latest.get('submitted_at'),
                "submitted_by": latest.get('submitted_by'),
                "included_samples": latest.get('included_samples', 0),
                "total_samples": latest.get('total_samples', 0)
            }
        
        # Determine if can complete phase
        can_complete = (
            phase.status == "Pending Approval" and
            stats['approved'] > 0 and
            latest_submission and
            latest_submission['status'] == 'approved'
        )
        
        return {
            "total_samples": stats['total'],
            "included_samples": stats['included'],
            "excluded_samples": stats['excluded'],
            "pending_samples": stats['pending'],
            "submitted_samples": stats['submitted'],
            "approved_samples": stats['approved'],
            "rejected_samples": stats['rejected'],
            "revision_required_samples": stats['revision_required'],
            "phase_status": phase.status,
            "can_complete_phase": can_complete,
            "total_submissions": len(submissions),
            "latest_submission": latest_submission,
            # Metrics from Universal Metrics Service
            "total_attributes": metrics_dict["total_attributes"],
            "scoped_attributes": metrics_dict["scoped_attributes_non_pk"],  # Non-PK for consistency
            "pk_attributes": metrics_dict["scoped_attributes_pk"],
            "total_lobs": metrics_dict["lobs_count"],
            "total_data_providers": metrics_dict["data_providers_count"],
            "started_at": phase.actual_start_date.isoformat() if phase.actual_start_date else None,
            # Add days elapsed
            "days_elapsed": (datetime.now(timezone.utc) - phase.created_at).days if phase.created_at else 0
        }
        
    except Exception as e:
        logger.error(f"Error in get_sample_analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/cycles/{cycle_id}/reports/{report_id}/samples/feedback")
async def get_sample_feedback(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report owner feedback for samples"""
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        return {"active_feedback": None, "unresolved_count": 0}
    
    # Get the latest version with report owner feedback
    from app.models.sample_selection import SampleDecision
    
    # Find versions that have report owner decisions
    versions_with_feedback_query = await db.execute(
        select(SampleSelectionVersion)
        .join(SampleSelectionSample, SampleSelectionSample.version_id == SampleSelectionVersion.version_id)
        .where(
            and_(
                SampleSelectionVersion.phase_id == phase.phase_id,
                SampleSelectionSample.report_owner_decision.isnot(None)
            )
        )
        .group_by(SampleSelectionVersion.version_id)
        .order_by(SampleSelectionVersion.version_number.desc())
    )
    versions_with_feedback = versions_with_feedback_query.scalars().all()
    
    if not versions_with_feedback:
        return {"active_feedback": None, "unresolved_count": 0}
    
    # Get the latest version with feedback
    latest_version = versions_with_feedback[0]
    
    # Get samples with report owner feedback from this version
    samples_query = await db.execute(
        select(SampleSelectionSample)
        .where(
            and_(
                SampleSelectionSample.version_id == latest_version.version_id,
                SampleSelectionSample.report_owner_decision.isnot(None)
            )
        )
    )
    samples = samples_query.scalars().all()
    
    feedback_items = []
    decisions = []
    
    for sample in samples:
        if sample.report_owner_decision_notes:
            decision_value = sample.report_owner_decision.value if hasattr(sample.report_owner_decision, 'value') else sample.report_owner_decision
            feedback_items.append({
                "sample_id": str(sample.sample_id),
                "feedback_text": sample.report_owner_decision_notes,
                "decision": decision_value,
                "created_at": sample.report_owner_decision_at.isoformat() if sample.report_owner_decision_at else '',
                "created_by": "Report Owner"
            })
            decisions.append(decision_value)
    
    # Determine overall decision based on individual decisions
    overall_decision = None
    overall_feedback = None
    
    if decisions:
        if all(d == 'approved' for d in decisions):
            overall_decision = 'approved'
        elif any(d == 'rejected' for d in decisions):
            overall_decision = 'rejected'
        elif any(d == 'revision_required' for d in decisions):
            overall_decision = 'revision_required'
        else:
            overall_decision = 'mixed'
    
    # Check version status for overall feedback
    version_status = latest_version.version_status.value if hasattr(latest_version.version_status, 'value') else latest_version.version_status
    if version_status == 'approved':
        overall_decision = 'approved'
        overall_feedback = latest_version.approval_notes or "Samples approved"
    
    active_feedback = None
    if overall_decision:
        active_feedback = {
            "version_id": str(latest_version.version_id),
            "version_number": latest_version.version_number,
            "feedback_text": overall_feedback or f"Version {latest_version.version_number} has been reviewed",
            "submitted_at": latest_version.submitted_at.isoformat() if latest_version.submitted_at else '',
            "status": overall_decision
        }
    
    return {
        "active_feedback": active_feedback,
        "unresolved_count": len(feedback_items),
        "feedback_items": feedback_items[:10]  # Limit to 10 items
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/upload")
async def upload_samples(
    cycle_id: int,
    report_id: int,
    request: UploadSamplesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload samples manually"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to upload samples")
    
    # Get scoped attributes for validation
    attr_query = await db.execute(
        select(ReportAttribute).where(
            and_(
                ReportAttribute.report_id == report_id,
                ReportAttribute.is_scoped == True
            )
        )
    )
    attributes = attr_query.scalars().all()
    primary_key_attr = next((attr for attr in attributes if attr.is_primary_key), None)
    
    if not primary_key_attr:
        raise HTTPException(status_code=400, detail="No primary key attribute found")
    
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    # Get existing samples from metadata
    existing_samples = []
    if phase.phase_data and "cycle_report_sample_selection_samples" in phase.phase_data:
        existing_samples = phase.phase_data["cycle_report_sample_selection_samples"]
    
    # Create new samples
    samples_created = []
    for sample_data in request.samples:
        # Extract primary key value
        primary_key_value = sample_data.get(primary_key_attr.attribute_name)
        if not primary_key_value:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing primary key '{primary_key_attr.attribute_name}' in sample data"
            )
        
        # Create sample record structure with meaningful ID
        # Find the highest existing sample number to avoid duplicates
        max_sample_num = 0
        for existing in existing_samples:
            if existing.get('sample_id', '').startswith(f"C{cycle_id:02d}_R{report_id}_S"):
                try:
                    num = int(existing['sample_id'].split('_S')[1])
                    max_sample_num = max(max_sample_num, num)
                except:
                    pass
        
        sample_number = max_sample_num + len(samples_created) + 1
        sample_id = f"C{cycle_id:02d}_R{report_id}_S{sample_number:03d}"
        
        sample_record = {
            "sample_id": sample_id,
            "primary_key_value": str(primary_key_value),
            "sample_data": sample_data,
            "generation_method": "Manual Upload",
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by_user_id": current_user.user_id,
            "generated_by": f"{current_user.first_name} {current_user.last_name}",
            "cycle_id": cycle_id,
            "report_id": report_id,
            "version_number": 1,
            "is_submitted": False,
            "tester_decision": None,
            "report_owner_decision": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        samples_created.append(sample_record)
        existing_samples.append(sample_record)
    
    # Update phase metadata
    if not phase.phase_data:
        phase.phase_data = {}
    phase.phase_data["cycle_report_sample_selection_samples"] = existing_samples
    phase.phase_data['last_updated'] = datetime.utcnow().isoformat()
    
    await db.commit()
    
    return {
        "samples_uploaded": len(samples_created),
        "message": f"Successfully uploaded {len(samples_created)} samples"
    }


@deprecated_endpoint(
    alternative="/api/v1/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/generate-unified",
    removal_version="4.0.0", 
    message="Use unified endpoint with strategy='intelligent'"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/generate-intelligent")
async def generate_intelligent_samples(
    cycle_id: int,
    report_id: int,
    request: IntelligentSamplingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate samples using intelligent 30/50/20 distribution with background job"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to generate samples")
    
    logger.info(f"Starting intelligent sample generation job for cycle {cycle_id}, report {report_id}")
    
    # Create background job
    job_id = job_manager.create_job(
        job_type="intelligent_sampling",
        metadata={
            "cycle_id": cycle_id,
            "report_id": report_id,
            "target_sample_size": request.target_sample_size,
            "use_data_source": request.use_data_source,
            "distribution": request.distribution,
            "initiated_by": f"{current_user.first_name} {current_user.last_name}",
            "initiated_by_id": current_user.user_id
        }
    )
    
    # Run the task using background thread (same pattern as data profiling)
    import threading
    
    def run_in_background():
        """Run the async sample generation in a background thread"""
        logger.info(f"🧵 Background thread started for job {job_id}")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            logger.info(f"📦 Importing execute_intelligent_sampling_task...")
            from app.tasks.sample_selection_tasks import execute_intelligent_sampling_task
            
            logger.info(f"🚀 Starting execute_intelligent_sampling_task for job {job_id}")
            loop.run_until_complete(execute_intelligent_sampling_task(
                job_id=job_id,
                cycle_id=cycle_id,
                report_id=report_id,
                target_sample_size=request.target_sample_size,
                use_data_source=request.use_data_source,
                distribution=request.distribution,
                include_file_samples=request.include_file_samples,
                current_user_id=current_user.user_id,
                current_user_name=f"{current_user.first_name} {current_user.last_name}"
            ))
            logger.info(f"✅ Background task completed for job {job_id}")
        except Exception as e:
            logger.error(f"❌ Background task failed for job {job_id}: {str(e)}", exc_info=True)
            job_manager.complete_job(job_id, error=str(e))
        finally:
            logger.info(f"🔚 Closing event loop for job {job_id}")
            loop.close()
    
    # Start the background thread
    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()
    
    logger.info(f"✅ Started background thread for intelligent sampling job {job_id}")
    
    return {
        "job_id": job_id,
        "message": "Intelligent sampling job started",
        "status_url": f"/api/v1/jobs/{job_id}/status"
    }


@deprecated_endpoint(
    alternative="/api/v1/sample-selection/versions/{version_id}/approve",
    removal_version="4.0.0",
    message="Use version-based approve endpoint"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/review")
async def review_samples(
    cycle_id: int,
    report_id: int,
    request: ReviewSamplesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report owner reviews submitted samples"""
    if current_user.role not in ["Report Owner", "Report Owner Executive"]:
        raise HTTPException(status_code=403, detail="Not authorized to review samples")
    
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    # Get latest pending submission from metadata
    submissions = phase.phase_data.get('submissions', []) if phase.phase_data else []
    pending_submission = None
    
    for submission in submissions:
        if submission.get('status') == 'pending':
            pending_submission = submission
            break
    
    if not pending_submission:
        raise HTTPException(status_code=404, detail="No pending submission found")
    
    # Update all samples in this submission
    samples = phase.phase_data.get("cycle_report_sample_selection_samples", []) if phase.phase_data else []
    updated_samples = []
    
    for i, sample in enumerate(samples):
        if sample.get('submission_id') == pending_submission['submission_id']:
            # Update submission status
            samples[i]['submission_status'] = request.decision
            samples[i]['report_owner_decision'] = request.decision
            samples[i]['reviewed_by_id'] = current_user.user_id
            samples[i]['reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
            samples[i]['reviewed_at'] = datetime.utcnow().isoformat()
            if request.feedback:
                samples[i]['review_feedback'] = request.feedback
                samples[i]['report_owner_feedback'] = request.feedback
            
            # Handle individual feedback
            if request.individual_feedback and sample['sample_id'] in request.individual_feedback:
                samples[i]['individual_feedback'] = request.individual_feedback[sample['sample_id']]
            
            samples[i]['updated_at'] = datetime.utcnow().isoformat()
            updated_samples.append(samples[i])
    
    # Update submission status in metadata
    for i, submission in enumerate(phase.phase_data['submissions']):
        if submission['submission_id'] == pending_submission['submission_id']:
            phase.phase_data['submissions'][i]['status'] = request.decision
            phase.phase_data['submissions'][i]['reviewed_at'] = datetime.utcnow().isoformat()
            phase.phase_data['submissions'][i]['reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
            if request.feedback:
                phase.phase_data['submissions'][i]['feedback'] = request.feedback
            break
    
    # Update phase metadata
    phase.phase_data["cycle_report_sample_selection_samples"] = samples
    phase.phase_data['last_updated'] = datetime.utcnow().isoformat()
    
    # If approved, update workflow phase status
    if request.decision == "approved":
        phase.status = "Complete"
        phase.actual_end_date = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": f"Samples {request.decision} successfully",
        "submission_id": pending_submission['submission_id'],
        "version_number": pending_submission['version_number']
    }


@router.post("/cycles/{cycle_id}/reports/{report_id}/complete")
async def complete_sample_selection(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete the sample selection phase"""
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to complete phase")
    
    # Verify phase can be completed
    analytics = await get_sample_analytics(cycle_id, report_id, db, current_user)
    
    if not analytics["can_complete_phase"]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot complete phase - samples must be approved by report owner"
        )
    
    # Update phase status
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if phase:
        phase.status = "Complete"
        phase.actual_end_date = datetime.utcnow()
        await db.commit()
    
    return {
        "message": "Sample Selection phase completed successfully",
        "phase_status": "Complete"
    }


# Report Owner specific endpoints
@router.get("/cycles/{cycle_id}/reports/{report_id}/submissions/{submission_id}")
async def get_submission_details(
    cycle_id: int,
    report_id: int,
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific submission for review"""
    if current_user.role not in ["Report Owner", "Report Owner Executive", "Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    # Find the submission
    if not phase.phase_data or 'submissions' not in phase.phase_data:
        raise HTTPException(status_code=404, detail="No submissions found")
    
    submission = None
    for sub in phase.phase_data['submissions']:
        if sub['submission_id'] == submission_id:
            submission = sub
            break
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Return submission with samples snapshot
    return {
        "submission": submission,
        "cycle_report_sample_selection_samples": submission.get('samples_snapshot', [])
    }


@deprecated_endpoint(
    alternative="/api/v1/sample-selection/versions/{version_id}/approve",
    removal_version="4.0.0",
    message="Use version-based approve endpoint"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/submissions/{submission_id}/review")
async def review_submission(
    cycle_id: int,
    report_id: int,
    submission_id: str,
    request: ReviewSamplesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review a submission (approve/reject)"""
    if current_user.role not in ["Report Owner", "Report Owner Executive"]:
        raise HTTPException(status_code=403, detail="Not authorized to review submissions")
    
    # Get workflow phase
    phase_query = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
    )
    phase = phase_query.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Sample Selection phase not found")
    
    # Find and update the submission
    if not phase.phase_data or 'submissions' not in phase.phase_data:
        raise HTTPException(status_code=404, detail="No submissions found")
    
    submission_found = False
    for i, sub in enumerate(phase.phase_data['submissions']):
        if sub['submission_id'] == submission_id:
            # Update submission status
            phase.phase_data['submissions'][i]['status'] = request.decision
            phase.phase_data['submissions'][i]['reviewed_at'] = datetime.utcnow().isoformat()
            phase.phase_data['submissions'][i]['reviewed_by_id'] = current_user.user_id
            phase.phase_data['submissions'][i]['reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
            phase.phase_data['submissions'][i]['review_feedback'] = request.feedback
            
            # Update submission with review data
            phase.phase_data['submissions'][i]['reviewed_at'] = datetime.utcnow().isoformat()
            phase.phase_data['submissions'][i]['reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
            phase.phase_data['submissions'][i]['review_feedback'] = request.feedback
            
            # Update the samples in the submission snapshot with decisions
            if 'samples_snapshot' in sub:
                for j, snapshot_sample in enumerate(sub['samples_snapshot']):
                    if snapshot_sample.get('tester_decision') == 'approved':
                        # Apply individual decision if provided, otherwise use overall decision
                        individual_decision = None
                        if request.individual_decisions and snapshot_sample['sample_id'] in request.individual_decisions:
                            individual_decision = request.individual_decisions[snapshot_sample['sample_id']]
                        
                        phase.phase_data['submissions'][i]['samples_snapshot'][j]['report_owner_decision'] = individual_decision or request.decision
                        phase.phase_data['submissions'][i]['samples_snapshot'][j]['report_owner_feedback'] = request.individual_feedback.get(snapshot_sample['sample_id']) if request.individual_feedback else None
                        phase.phase_data['submissions'][i]['samples_snapshot'][j]['report_owner_reviewed_at'] = datetime.utcnow().isoformat()
                        phase.phase_data['submissions'][i]['samples_snapshot'][j]['report_owner_reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
            
            # Also update the main samples array with the decisions
            if request.decision == 'approved':
                phase.status = "Complete"
                
                # Update the main samples with report owner decisions
                if 'samples_snapshot' in sub:
                    for snapshot_sample in sub['samples_snapshot']:
                        if snapshot_sample.get('tester_decision') == 'approved':
                            # Find and update the main sample
                            for j, main_sample in enumerate(phase.phase_data.get("cycle_report_sample_selection_samples", [])):
                                if main_sample['sample_id'] == snapshot_sample['sample_id']:
                                    # Use individual decision if provided, otherwise use overall decision
                                    individual_decision = None
                                    if request.individual_decisions and snapshot_sample['sample_id'] in request.individual_decisions:
                                        individual_decision = request.individual_decisions[snapshot_sample['sample_id']]
                                    
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_decision'] = individual_decision or 'approved'
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_feedback'] = request.individual_feedback.get(snapshot_sample['sample_id']) if request.individual_feedback else None
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_reviewed_at'] = datetime.utcnow().isoformat()
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['version_reviewed'] = sub['version_number']
                                    break
            
            elif request.decision == 'revision_required':
                phase.status = "In Progress"
                
                # UPDATE cycle_report_sample_selection_samples with individual decisions and feedback
                if 'samples_snapshot' in sub:
                    for snapshot_sample in sub['samples_snapshot']:
                        if snapshot_sample.get('tester_decision') == 'approved':
                            for j, main_sample in enumerate(phase.phase_data.get("cycle_report_sample_selection_samples", [])):
                                if main_sample['sample_id'] == snapshot_sample['sample_id']:
                                    # Use individual decision if provided
                                    individual_decision = None
                                    if request.individual_decisions and snapshot_sample['sample_id'] in request.individual_decisions:
                                        individual_decision = request.individual_decisions[snapshot_sample['sample_id']]
                                    
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_decision'] = individual_decision or 'revision_required'
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_feedback'] = request.individual_feedback.get(snapshot_sample['sample_id']) if request.individual_feedback else None
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['needs_revision'] = True
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_reviewed_at'] = datetime.utcnow().isoformat()
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['version_reviewed'] = sub['version_number']
                                    break
            
            elif request.decision == 'rejected':
                phase.status = "In Progress"
                
                # UPDATE cycle_report_sample_selection_samples with rejected status
                if 'samples_snapshot' in sub:
                    for snapshot_sample in sub['samples_snapshot']:
                        if snapshot_sample.get('tester_decision') == 'approved':
                            for j, main_sample in enumerate(phase.phase_data.get("cycle_report_sample_selection_samples", [])):
                                if main_sample['sample_id'] == snapshot_sample['sample_id']:
                                    # Use individual decision if provided
                                    individual_decision = None
                                    if request.individual_decisions and snapshot_sample['sample_id'] in request.individual_decisions:
                                        individual_decision = request.individual_decisions[snapshot_sample['sample_id']]
                                    
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_decision'] = individual_decision or 'rejected'
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_feedback'] = request.individual_feedback.get(snapshot_sample['sample_id']) if request.individual_feedback else None
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_reviewed_at'] = datetime.utcnow().isoformat()
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['report_owner_reviewed_by'] = f"{current_user.first_name} {current_user.last_name}"
                                    phase.phase_data["cycle_report_sample_selection_samples"][j]['version_reviewed'] = sub['version_number']
                                    break
            
            submission_found = True
            break
    
    if not submission_found:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Flag as modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(phase, 'phase_data')
    
    await db.commit()
    
    return {
        "message": f"Submission {request.decision}",
        "phase_status": phase.status
    }


@router.get("/cycles/{cycle_id}/reports/{report_id}/all-samples")
async def get_all_samples_across_versions(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all samples from approved versions only for a report"""
    try:
        # Get workflow phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            return {"samples": [], "total_samples": 0, "unique_samples": 0}
        
        # Get all samples from APPROVED versions only
        samples_query = await db.execute(
            select(
                SampleSelectionSample,
                SampleSelectionVersion.version_number,
                SampleSelectionVersion.version_status,
                LOB.lob_name.label('lob_name')
            ).join(
                SampleSelectionVersion,
                SampleSelectionSample.version_id == SampleSelectionVersion.version_id
            ).outerjoin(
                LOB,
                SampleSelectionSample.lob_id == LOB.lob_id
            ).where(
                and_(
                    SampleSelectionSample.phase_id == phase.phase_id,
                    SampleSelectionVersion.version_status == VersionStatus.APPROVED
                )
            ).order_by(
                SampleSelectionVersion.version_number.desc(),
                SampleSelectionSample.sample_id
            )
        )
        
        samples_with_version = samples_query.all()
        
        # Group samples by version
        samples_by_version = {}
        all_samples = []
        unique_sample_keys = set()
        
        for sample, version_number, version_status, lob_name in samples_with_version:
            if version_number not in samples_by_version:
                samples_by_version[version_number] = {
                    "version_number": version_number,
                    "version_status": version_status,
                    "samples": []
                }
            
            sample_dict = {
                "sample_id": str(sample.sample_id),
                "version_number": version_number,
                "version_status": version_status,
                "sample_identifier": sample.sample_identifier,
                "sample_data": sample.sample_data,
                "sample_category": sample.sample_category,
                "tester_decision": sample.tester_decision,
                "report_owner_decision": sample.report_owner_decision,
                "lob_assignment": lob_name,
                "created_at": sample.created_at.isoformat() if sample.created_at else None
            }
            
            samples_by_version[version_number]["samples"].append(sample_dict)
            all_samples.append(sample_dict)
            
            # Track unique samples by sample identifier
            unique_sample_keys.add(sample.sample_identifier)
        
        return {
            "samples_by_version": list(samples_by_version.values()),
            "all_samples": all_samples,
            "total_samples": len(all_samples),
            "unique_samples": len(unique_sample_keys),
            "versions_count": len(samples_by_version)
        }
        
    except Exception as e:
        logger.error(f"Error getting all samples: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending-reviews")
async def get_pending_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pending sample reviews for report owner"""
    if current_user.role not in ["Report Owner", "Report Owner Executive"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all cycle reports for the current user (where they are the report owner)
    cycle_reports_query = await db.execute(
        select(CycleReport)
        .join(CycleReport.report)
        .where(Report.report_owner_id == current_user.user_id)
        .options(selectinload(CycleReport.report))
    )
    cycle_reports = cycle_reports_query.scalars().all()
    
    pending_reviews = []
    
    # Check each cycle report for pending submissions
    for cr in cycle_reports:
        # Get workflow phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cr.cycle_id,
                    WorkflowPhase.report_id == cr.report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if phase and phase.phase_data and 'submissions' in phase.phase_data:
            # Check submissions for pending ones
            for submission in phase.phase_data['submissions']:
                if submission.get('status') == 'pending':
                    pending_reviews.append({
                        "submission_id": submission['submission_id'],
                        "cycle_id": cr.cycle_id,
                        "report_id": cr.report_id,
                        "report_name": cr.report.report_name,
                        "version_number": submission['version_number'],
                        "submitted_at": submission['submitted_at'],
                        "submitted_by": submission.get('submitted_by', 'Unknown'),
                        "sample_count": submission.get('included_samples', submission.get('sample_count', 0)),
                        "notes": submission.get('notes')
                    })
    
    # Sort by submitted_at descending
    pending_reviews.sort(key=lambda x: x['submitted_at'], reverse=True)
    
    return pending_reviews


@deprecated_endpoint(
    alternative="/api/v1/sample-selection/cycles/{cycle_id}/reports/{report_id}/samples/generate-unified",
    removal_version="4.0.0",
    message="Use unified endpoint with strategy='enhanced'"
)
@router.post("/cycles/{cycle_id}/reports/{report_id}/samples/generate-enhanced")
async def generate_enhanced_samples(
    cycle_id: int,
    report_id: int,
    request: EnhancedSampleGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate samples using enhanced pandas-based approach with data source integration.
    Leverages data profiling insights for anomaly-based sampling when available.
    """
    if current_user.role not in ["Tester", "Test Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to generate samples")
    
    try:
        # Get workflow phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Sample Selection phase not found")
        
        # Get scoped attributes
        attr_query = await db.execute(
            select(ReportAttribute).where(
                and_(
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.is_scoped == True
                )
            )
        )
        attributes = attr_query.scalars().all()
        
        if not attributes:
            raise HTTPException(status_code=400, detail="No scoped attributes found for sample generation")
        
        scoped_attributes = [
            {
                "attribute_name": attr.attribute_name,
                "is_primary_key": attr.is_primary_key,
                "data_type": attr.data_type,
                "mandatory_flag": attr.mandatory_flag
            }
            for attr in attributes
        ]
        
        # Get data source
        data_source = None
        if request.data_source_id:
            ds_query = await db.execute(
                select(CycleReportDataSource).where(
                    CycleReportDataSource.id == request.data_source_id
                )
            )
            data_source = ds_query.scalar_one_or_none()
        else:
            # Get default data source for this cycle/report
            ds_query = await db.execute(
                select(CycleReportDataSource).where(
                    and_(
                        CycleReportDataSource.cycle_id == cycle_id,
                        CycleReportDataSource.report_id == report_id
                    )
                ).limit(1)
            )
            data_source = ds_query.scalar_one_or_none()
        
        if not data_source:
            raise HTTPException(
                status_code=400, 
                detail="No data source found. Please configure a data source for this cycle/report."
            )
        
        # Initialize enhanced sample selection service
        enhanced_service = get_enhanced_sample_selection_service()
        
        # Generate samples using the enhanced service
        logger.info(f"Starting enhanced sample generation for cycle {cycle_id}, report {report_id}")
        logger.info(f"Using data source: {data_source.source_name} ({data_source.source_type})")
        logger.info(f"Sampling strategy: {request.sampling_strategy}")
        
        generation_result = await enhanced_service.generate_samples_from_source(
            cycle_id=cycle_id,
            report_id=report_id,
            data_source=data_source,
            scoped_attributes=scoped_attributes,
            sample_size=request.sample_size,
            use_anomaly_insights=request.use_anomaly_insights,
            db=db
        )
        
        # Get existing samples from phase metadata
        existing_samples = []
        if phase.phase_data and "cycle_report_sample_selection_samples" in phase.phase_data:
            existing_samples = phase.phase_data["cycle_report_sample_selection_samples"]
        
        # Add new samples to existing ones
        new_samples = generation_result["samples"]
        all_samples = existing_samples + new_samples
        
        # Update phase metadata with new samples
        if not phase.phase_data:
            phase.phase_data = {}
        
        phase.phase_data["cycle_report_sample_selection_samples"] = all_samples
        phase.phase_data["last_updated"] = datetime.utcnow().isoformat()
        phase.phase_data["enhanced_generation_stats"] = {
            "total_records_processed": generation_result["total_records"],
            "scoped_records": generation_result["scoped_records"],
            "generation_method": generation_result["method"],
            "data_source_type": generation_result["data_source_type"],
            "anomaly_insights_used": generation_result["anomaly_insights_used"],
            "samples_generated": len(new_samples),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Flag the object as modified for SQLAlchemy to track JSONB changes
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(phase, 'phase_data')
        
        # Update phase timestamps
        phase.updated_at = datetime.utcnow()
        phase.updated_by_id = current_user.user_id
        
        await db.commit()
        
        logger.info(f"Successfully generated {len(new_samples)} enhanced samples")
        
        return {
            "success": True,
            "message": f"Successfully generated {len(new_samples)} samples using enhanced pandas-based approach",
            "samples_generated": len(new_samples),
            "total_samples": len(all_samples),
            "generation_stats": generation_result,
            "sampling_strategy": request.sampling_strategy,
            "data_source_used": {
                "name": data_source.source_name,
                "type": data_source.source_type
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating enhanced samples: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate enhanced samples: {str(e)}"
        )


# Version Management Endpoints - Following Scoping Patterns

class VersionSubmissionCreate(BaseModel):
    submission_notes: Optional[str] = None


class VersionApprovalCreate(BaseModel):
    approved: bool
    approval_notes: Optional[str] = None


@router.post("/cycles/{cycle_id}/reports/{report_id}/versions")
async def create_sample_selection_version(
    cycle_id: int,
    report_id: int,
    carry_forward_all: bool = True,  # New parameter to control which samples to carry forward
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new sample selection version"""
    try:
        # Get the workflow phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample Selection phase not found"
            )
        
        # Use version table service to create new version
        from app.services.sample_selection_table_service import SampleSelectionTableService
        
        # Check if there's already a draft version
        current_version = await SampleSelectionTableService.get_current_version(db, phase.phase_id)
        
        if current_version and current_version.version_status == VersionStatus.DRAFT:
            # If there's already a draft version, return it instead of creating a new one
            new_version = current_version
            logger.info(f"Using existing draft version {new_version.version_number} instead of creating new one")
        else:
            # Check if we should carry forward samples with report owner feedback
            if carry_forward_all:
                # This is for "Make Changes" workflow - preserve report owner decisions
                new_version = await SampleSelectionTableService.create_version_from_feedback(
                    db=db,
                    phase_id=phase.phase_id,
                    user_id=current_user.user_id
                )
            else:
                # Regular new version creation
                new_version = await SampleSelectionTableService.create_version(
                    db=db,
                    phase_id=phase.phase_id,
                    user_id=current_user.user_id,
                    generation_method="manual",
                    change_reason="Created new version for sample selection"
                )
        
        # Get sample count for the new version
        samples_result = await db.execute(
            select(func.count(SampleSelectionSample.sample_id))
            .where(SampleSelectionSample.version_id == new_version.version_id)
        )
        sample_count = samples_result.scalar() or 0
        
        # Get decision counts
        decisions_result = await db.execute(
            select(
                SampleSelectionSample.tester_decision,
                func.count(SampleSelectionSample.sample_id)
            )
            .where(SampleSelectionSample.version_id == new_version.version_id)
            .group_by(SampleSelectionSample.tester_decision)
        )
        decision_counts = {row[0]: row[1] for row in decisions_result.all() if row[0]}
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Created sample selection version {new_version.version_number} with {sample_count} samples",
            "version": {
                "version_id": str(new_version.version_id),
                "version_number": new_version.version_number,
                "version_status": new_version.version_status.value,
                "created_at": new_version.created_at.isoformat(),
                "created_by": new_version.created_by_id,
                "created_by_name": f"{current_user.first_name} {current_user.last_name}",
                "total_samples": sample_count,
                "approved_samples": decision_counts.get('approved', 0),
                "rejected_samples": decision_counts.get('rejected', 0),
                "pending_samples": sample_count - sum(decision_counts.values()),
                "generation_method": new_version.metadata.get("generation_method", "manual") if new_version.metadata else "manual",
                "change_reason": new_version.metadata.get("change_reason", "Created new version") if new_version.metadata else "Created new version"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sample selection version: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.post("/versions/{version_id}/submit")
async def submit_version_for_approval(
    version_id: str,
    submission_data: VersionSubmissionCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit sample selection version for report owner approval"""
    try:
        # Find the phase containing this version
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
        phases = phase_query.scalars().all()
        
        phase = None
        version_metadata = None
        for p in phases:
            if p.phase_data and "versions" in p.phase_data:
                for v in p.phase_data["versions"]:
                    if v.get("version_id") == version_id:
                        phase = p
                        version_metadata = v
                        break
                if phase:
                    break
        
        if not phase or not version_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Check if version is in draft status
        if version_metadata.get("version_status") != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft versions can be submitted for approval"
            )
        
        # Update version status
        version_metadata["version_status"] = "pending_approval"
        version_metadata["submitted_at"] = datetime.utcnow().isoformat()
        version_metadata["submitted_by"] = current_user.user_id
        version_metadata["submitted_by_name"] = f"{current_user.first_name} {current_user.last_name}"
        version_metadata["submission_notes"] = submission_data.submission_notes
        
        # Update all samples of this version to submitted
        if "cycle_report_sample_selection_samples" in phase.phase_data:
            version_number = version_metadata["version_number"]
            for sample in phase.phase_data["cycle_report_sample_selection_samples"]:
                if sample.get("version_number") == version_number:
                    sample["is_submitted"] = True
                    # Reset report owner decisions on submission
                    sample["report_owner_decision"] = None
                    sample["report_owner_feedback"] = None
                    sample["report_owner_reviewed_at"] = None
                    sample["report_owner_reviewed_by"] = None
        
        # Flag the object as modified
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(phase, 'phase_data')
        
        # Update phase timestamps
        phase.updated_at = datetime.utcnow()
        phase.updated_by_id = current_user.user_id
        
        await db.commit()
        
        # Mark version as approved by tester
        try:
            from app.services.version_tester_approval import VersionTesterApprovalService
            await VersionTesterApprovalService.mark_sample_selection_approved_by_tester(
                db, version_id, current_user.user_id
            )
        except Exception as e:
            logger.error(f"Failed to mark version as approved by tester: {str(e)}")
            # Don't fail the submission if this fails
        
        # Create Universal Assignment for report owner review
        try:
            from app.services.universal_assignment_service import UniversalAssignmentService
            from app.services.email_service import EmailService
            
            email_service = EmailService()
            assignment_service = UniversalAssignmentService(db, email_service)
            
            # Get report and cycle info
            from app.models.report import Report
            from app.models.test_cycle import TestCycle
            report_query = await db.execute(
                select(Report).where(Report.report_id == phase.report_id)
            )
            report = report_query.scalar_one_or_none()
            
            cycle_query = await db.execute(
                select(TestCycle).where(TestCycle.cycle_id == phase.cycle_id)
            )
            cycle = cycle_query.scalar_one_or_none()
            
            if report:
                # Get LOB from report
                lob = report.lob if hasattr(report, 'lob') else 'Unknown'
                
                
                # Create assignment with correct parameters
                await assignment_service.create_assignment(
                    assignment_type="Sample Selection Approval",  # Use correct enum value
                    from_role="Tester",
                    to_role="Report Owner",
                    from_user_id=current_user.user_id,
                    to_user_id=None,  # Will be determined by role
                    title="Review Sample Selection",
                    description=f"Please review and approve sample selection version {version_metadata['version_number']} for {report.report_name}",
                    context_type="Report",
                    context_data={
                        "cycle_id": phase.cycle_id,
                        "report_id": phase.report_id,
                        "phase_id": phase.phase_id,  # Add phase_id for version metadata updates
                        "report_name": report.report_name,
                        "cycle_name": cycle.cycle_name if cycle else None,
                        "phase_name": "Sample Selection",
                        "version_id": version_id,
                        "version_number": version_metadata["version_number"],
                        "total_samples": version_metadata["total_samples"],
                        "included_samples": version_metadata.get("total_samples", 0),
                        "submission_notes": submission_data.submission_notes or "",
                        "submitted_at": version_metadata["submitted_at"],
                        "submitted_by": current_user.user_id,
                        "submission_id": version_id,  # Use version_id as submission_id
                        "lob": lob
                    },
                    task_instructions=f"Review the {version_metadata.get('total_samples', 0)} samples in version {version_metadata['version_number']} and provide your approval decision.",
                    priority="High",
                    due_date=None,
                    requires_approval=False,
                    approval_role=None,
                    assignment_metadata={
                        "version_id": version_id,
                        "version_number": version_metadata["version_number"]
                    }
                )
                logger.info(f"Created Universal Assignment for sample selection review of version {version_metadata['version_number']}")
        except Exception as e:
            logger.error(f"Failed to create Universal Assignment: {str(e)}")
            # Don't fail the submission if assignment creation fails
        
        return {
            "success": True,
            "message": f"Version {version_metadata['version_number']} submitted for approval",
            "version": version_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting version for approval: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit version: {str(e)}"
        )


@router.post("/versions/{version_id}/approve")
async def approve_version(
    version_id: str,
    approval_data: VersionApprovalCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject sample selection version"""
    try:
        # Verify user is report owner
        if current_user.role not in ["Report Owner", "Report Owner Executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Report Owners can approve versions"
            )
        
        # Find the phase containing this version
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
        phases = phase_query.scalars().all()
        
        phase = None
        version_metadata = None
        version_index = None
        for p in phases:
            if p.phase_data and "versions" in p.phase_data:
                for i, v in enumerate(p.phase_data["versions"]):
                    if v.get("version_id") == version_id:
                        phase = p
                        version_metadata = v
                        version_index = i
                        break
                if phase:
                    break
        
        if not phase or not version_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Check if version is pending approval
        if version_metadata.get("version_status") != "pending_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending approval versions can be approved"
            )
        
        # Update version status
        if approval_data.approved:
            version_metadata["version_status"] = "approved"
            
            # Mark all previous versions as superseded
            for v in phase.phase_data["versions"]:
                if v["version_id"] != version_id and v.get("version_status") == "approved":
                    v["version_status"] = "superseded"
            
            # Update phase status if all samples are reviewed
            phase.status = "Complete"
            phase.state = "Complete"
            phase.actual_end_date = datetime.utcnow()
        else:
            version_metadata["version_status"] = "rejected"
        
        version_metadata["approved_at"] = datetime.utcnow().isoformat()
        version_metadata["approved_by"] = current_user.user_id
        version_metadata["approved_by_name"] = f"{current_user.first_name} {current_user.last_name}"
        version_metadata["approval_notes"] = approval_data.approval_notes
        
        # Flag the object as modified
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(phase, 'phase_data')
        
        # Update phase timestamps
        phase.updated_at = datetime.utcnow()
        phase.updated_by_id = current_user.user_id
        
        await db.commit()
        
        # Mark Universal Assignment as complete if approved
        if approval_data.approved:
            try:
                from app.services.universal_assignment_service import UniversalAssignmentService
                assignment_service = UniversalAssignmentService(db)
                
                # Find and complete the assignment
                assignments = await assignment_service.get_assignments_by_filters(
                    assignment_type="sample_selection_review",
                    phase_id=phase.phase_id,
                    metadata_filters={"version_id": version_id}
                )
                
                for assignment in assignments:
                    if assignment.status not in ["completed", "cancelled"]:
                        await assignment_service.update_assignment_status(
                            assignment_id=assignment.assignment_id,
                            status="completed",
                            completed_by_id=current_user.user_id,
                            completion_notes=f"Version approved: {approval_data.approval_notes}"
                        )
                        logger.info(f"Marked assignment {assignment.assignment_id} as completed")
            except Exception as e:
                logger.error(f"Failed to update Universal Assignment: {str(e)}")
                # Don't fail the approval if assignment update fails
        
        return {
            "success": True,
            "message": f"Version {version_metadata['version_number']} {'approved' if approval_data.approved else 'rejected'}",
            "version": version_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving version: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve version: {str(e)}"
        )


@router.post("/cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback")
async def resubmit_after_feedback(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new version preserving report owner feedback (Make Changes workflow)"""
    try:
        # Get the workflow phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample Selection phase not found"
            )
        
        # Use version table service
        from app.services.sample_selection_table_service import SampleSelectionTableService
        
        try:
            # Check if there's already a draft version
            current_version = await SampleSelectionTableService.get_current_version(db, phase.phase_id)
            
            if current_version and current_version.version_status == VersionStatus.DRAFT:
                # If there's already a draft version, return it instead of creating a new one
                new_version = current_version
                logger.info(f"Using existing draft version {new_version.version_number} instead of creating new one")
            else:
                # Create new version from feedback
                new_version = await SampleSelectionTableService.create_version_from_feedback(
                    db=db,
                    phase_id=phase.phase_id,
                    user_id=current_user.user_id
                )
            
            # Update phase status back to In Progress
            phase.status = "In Progress"
            phase.state = "In Progress"
            phase.updated_at = datetime.utcnow()
            phase.updated_by_id = current_user.user_id
            
            # Only commit if we created a new version
            if new_version != current_version:
                await db.commit()
            
            # Get summary of preserved decisions
            samples_result = await db.execute(
                select(SampleSelectionSample)
                .where(SampleSelectionSample.version_id == new_version.version_id)
            )
            samples = samples_result.scalars().all()
            
            approved_count = sum(1 for s in samples if s.report_owner_decision == SampleDecision.APPROVED)
            rejected_count = sum(1 for s in samples if s.report_owner_decision == SampleDecision.REJECTED)
            pending_count = sum(1 for s in samples if s.report_owner_decision is None)
            
            return {
                "success": True,
                "message": f"Created new version {new_version.version_number} from report owner feedback",
                "version": {
                    "version_id": str(new_version.version_id),
                    "version_number": new_version.version_number,
                    "version_status": new_version.version_status.value,
                    "created_at": new_version.created_at.isoformat(),
                    "created_by": current_user.user_id,
                    "created_by_name": f"{current_user.first_name} {current_user.last_name}",
                    "total_samples": new_version.actual_sample_size,
                    "approved_samples": approved_count,
                    "rejected_samples": rejected_count,
                    "pending_samples": pending_count,
                    "change_reason": new_version.version_metadata.get("change_reason", "") if new_version.version_metadata else ""
                },
                "preserved_decisions": {
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "pending": pending_count
                }
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating version from feedback: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version from feedback: {str(e)}"
        )



@router.delete("/cycles/{cycle_id}/reports/{report_id}/samples/{sample_id}")
async def delete_sample(
    cycle_id: int,
    report_id: int,
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a sample (only allowed for Testers on draft versions)"""
    try:
        # Check user role
        if current_user.role != "Tester":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Testers can delete samples"
            )
        
        # Get the workflow phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample Selection phase not found"
            )
        
        # Get the current version
        from app.services.sample_selection_table_service import SampleSelectionTableService
        from app.models.sample_selection import VersionStatus
        
        current_version = await SampleSelectionTableService.get_current_version(db, phase.phase_id)
        
        if not current_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No sample selection version found"
            )
        
        # Check version status - can only delete from draft versions
        if current_version.version_status != VersionStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete samples from {current_version.version_status.value} version"
            )
        
        # Find and delete the sample
        sample_query = await db.execute(
            select(SampleSelectionSample).where(
                and_(
                    SampleSelectionSample.sample_id == sample_id,
                    SampleSelectionSample.version_id == current_version.version_id
                )
            )
        )
        sample = sample_query.scalar_one_or_none()
        
        if not sample:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample not found in current version"
            )
        
        # Store sample info for response
        sample_identifier = sample.sample_identifier
        
        # Delete the sample
        await db.delete(sample)
        
        # Update version sample count
        current_version.actual_sample_size -= 1
        current_version.updated_at = datetime.utcnow()
        current_version.updated_by_id = current_user.user_id
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Sample {sample_identifier} deleted successfully",
            "version": {
                "version_id": str(current_version.version_id),
                "version_number": current_version.version_number,
                "remaining_samples": current_version.actual_sample_size
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sample: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete sample: {str(e)}"
        )