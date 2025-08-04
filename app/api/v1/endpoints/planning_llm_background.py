"""
Enhanced Planning LLM endpoint with background job support
This module shows how the LLM attribute generation should be implemented
with proper background job processing for consistency.
"""

from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth import RoleChecker, UserRoles
from app.core.background_jobs import job_manager
from app.core.logging import get_logger
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.cycle_report_documents import CycleReportDocument as Document
from app.models.report_attribute import ReportAttribute
from app.schemas.planning import LLMAttributeGenerationRequest, LLMAttributeGenerationResponse
from app.services.llm_service import get_llm_service
from app.core.exceptions import NotFoundException

logger = get_logger(__name__)
router = APIRouter()

# Role-based access control
tester_roles = [UserRoles.TESTER]


@router.post("/cycles/{cycle_id}/reports/{report_id}/generate-attributes-llm-v2")
async def generate_attributes_with_llm_background(
    cycle_id: int,
    report_id: int,
    request_data: LLMAttributeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate attributes using LLM with background job processing.
    Returns immediately with job ID for progress tracking.
    """
    # Check permissions
    RoleChecker(tester_roles)(current_user)
    
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
    
    # Get planning phase
    phase_query = select(WorkflowPhase).where(
        and_(
            WorkflowPhase.cycle_id == cycle_id,
            WorkflowPhase.report_id == report_id,
            WorkflowPhase.phase_name == "Planning"
        )
    )
    phase_result = await db.execute(phase_query)
    phase = phase_result.scalar_one_or_none()
    
    if not phase:
        raise NotFoundException("Planning phase not found")
    
    # Create background job for LLM attribute generation
    job_id = job_manager.create_job("planning.llm.attributes", {
        "cycle_id": cycle_id,
        "report_id": report_id,
        "phase_id": phase.phase_id,
        "user_id": current_user.user_id,
        "report_name": report.report_name,
        "regulation": report.regulation_name,
        "auto_create": request_data.auto_create,
        "use_uploaded_documents": request_data.use_uploaded_documents
    })
    
    # Update initial progress
    job_manager.update_job_progress(
        job_id,
        status="running",
        total_steps=4,
        current_step="Initializing",
        progress_percentage=0,
        message="Starting LLM attribute generation..."
    )
    
    # Queue the Celery task
    from app.tasks.planning_tasks import generate_llm_attributes_task
    try:
        task = generate_llm_attributes_task.delay(
            job_id=job_id,
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=phase.phase_id,
            user_id=current_user.user_id,
            document_content=request_data.document_content,
            regulatory_context={
                "regulation": report.regulation,
                "report_name": report.report_name,
                "report_description": report.report_description
            }
        )
        logger.info(f"✅ Queued Celery task {task.id} for job {job_id}")
    except Exception as celery_error:
        logger.warning(f"Celery not available: {celery_error}, falling back to asyncio")
        # Fallback to asyncio if Celery not available
        import asyncio
        asyncio.create_task(
            run_llm_attribute_generation(
                job_id=job_id,
                cycle_id=cycle_id,
                report_id=report_id,
                phase_id=phase.phase_id,
                request_data=request_data,
                report=report,
                user_id=current_user.user_id,
                db=db
            )
        )
    
    # Return immediately with job info
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Attribute generation started in background",
        "poll_url": f"/api/jobs/{job_id}/status"
    }


async def run_llm_attribute_generation(
    job_id: str,
    cycle_id: int,
    report_id: int,
    phase_id: int,
    request_data: LLMAttributeGenerationRequest,
    report: Report,
    user_id: int,
    db: AsyncSession
):
    """Background task for LLM attribute generation"""
    try:
        # Step 1: Gather documents
        job_manager.update_job_progress(
            job_id,
            current_step="Gathering documents",
            progress_percentage=10,
            message="Loading uploaded documents...",
            completed_steps=0
        )
        
        document_contents = []
        if request_data.use_uploaded_documents:
            docs_query = select(Document).where(
                and_(
                    Document.cycle_id == cycle_id,
                    Document.report_id == report_id,
                )
            )
            
            docs_result = await db.execute(docs_query)
            documents = docs_result.scalars().all()
            
            for doc in documents:
                if doc.extracted_text:
                    document_contents.append({
                        "name": doc.document_name,
                        "type": doc.document_type,
                        "content": doc.extracted_text[:5000]  # Limit content
                    })
        
        job_manager.update_job_progress(
            job_id,
            current_step="Calling LLM service",
            progress_percentage=25,
            message=f"Processing {len(document_contents)} documents with LLM...",
            completed_steps=1
        )
        
        # Step 2: Generate attributes with LLM
        llm_service = get_llm_service()
        
        # Pass job_id to LLM service for progress updates
        result = await llm_service.generate_test_attributes(
            regulatory_context=request_data.regulatory_context or report.regulation_name,
            report_type=report.report_type,
            document_contents=document_contents,
            additional_context=request_data.additional_context,
            existing_attributes=request_data.existing_attributes,
            job_id=job_id  # Pass job ID for internal progress updates
        )
        
        job_manager.update_job_progress(
            job_id,
            current_step="Processing LLM response",
            progress_percentage=60,
            message=f"Generated {len(result.get('attributes', []))} attributes",
            completed_steps=2
        )
        
        # Step 3: Create attributes if requested
        created_attributes = []
        if request_data.auto_create and result.get("attributes"):
            job_manager.update_job_progress(
                job_id,
                current_step="Saving attributes",
                progress_percentage=75,
                message=f"Creating {len(result['attributes'])} attributes in database...",
                completed_steps=2
            )
            
            for idx, attr in enumerate(result["attributes"]):
                # Check if attribute already exists
                exists_query = select(ReportAttribute).where(
                    and_(
                        ReportAttribute.phase_id == phase_id,
                        ReportAttribute.attribute_name == attr["attribute_name"]
                    )
                )
                
                exists_result = await db.execute(exists_query)
                if not exists_result.scalar_one_or_none():
                    # Create new attribute
                    new_attr = ReportAttribute(
                        phase_id=phase_id,
                        attribute_name=attr["attribute_name"],
                        data_type=attr["data_type"],
                        is_primary_key=attr.get("is_key", False),
                        description=attr.get("description"),
                        validation_rules=attr.get("validation_rules"),
                        created_by_id=user_id,
                        created_at=datetime.utcnow(),
                        llm_generated=True,
                        llm_rationale=attr.get("rationale", "Generated by LLM"),
                        mandatory_flag=attr.get("mandatory_flag", "Optional"),
                        cde_flag=attr.get("cde_flag", False),
                        historical_issues_flag=attr.get("historical_issues_flag", False)
                    )
                    db.add(new_attr)
                    created_attributes.append(attr["attribute_name"])
                
                # Update progress periodically
                if idx % 5 == 0:
                    progress = 75 + int((idx / len(result["attributes"])) * 20)
                    job_manager.update_job_progress(
                        job_id,
                        progress_percentage=progress,
                        message=f"Created {idx + 1} of {len(result['attributes'])} attributes..."
                    )
            
            if created_attributes:
                await db.commit()
        
        # Step 4: Complete
        completion_result = {
            "attributes": result["attributes"],
            "total_generated": len(result["attributes"]),
            "total_created": len(created_attributes),
            "created_attributes": created_attributes,
            "generation_metadata": {
                "model": result.get("model", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "documents_used": len(document_contents)
            }
        }
        
        job_manager.complete_job(job_id, result=completion_result)
        
        logger.info(f"✅ Completed LLM attribute generation job {job_id}: "
                   f"{len(result['attributes'])} generated, {len(created_attributes)} created")
        
    except Exception as e:
        logger.error(f"❌ LLM generation failed for job {job_id}: {e}")
        job_manager.complete_job(job_id, error=str(e))


@router.get("/jobs/{job_id}/result")
async def get_llm_generation_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the result of an LLM generation job"""
    job_status = job_manager.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if job belongs to user
    if job_status.get("metadata", {}).get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if job_status["status"] == "completed":
        return {
            "status": "completed",
            "result": job_status.get("result", {})
        }
    elif job_status["status"] == "failed":
        return {
            "status": "failed",
            "error": job_status.get("error", "Unknown error")
        }
    else:
        return {
            "status": job_status["status"],
            "progress": job_status.get("progress_percentage", 0),
            "message": job_status.get("message", "Processing...")
        }