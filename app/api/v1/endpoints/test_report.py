"""
Test Report Phase API endpoints - Unified Architecture
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, func, text, select
from datetime import datetime
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.models.test_report import TestReportSection, TestReportGeneration, STANDARD_REPORT_SECTIONS
from app.models.workflow import WorkflowPhase
from app.services.test_report_service import TestReportService
from app.services.report_generation_service import ReportGenerationService
from app.services.approval_workflow_service import ApprovalWorkflowService
from app.services.enhanced_report_generation_service import EnhancedReportGenerationService
from app.services.pdf_export_service import PDFExportService


router = APIRouter()


# Request/Response Models
class SectionApprovalRequest(BaseModel):
    approval_level: str
    notes: Optional[str] = None


class SectionRevisionRequest(BaseModel):
    revision_level: str
    notes: str


class ReportGenerationRequest(BaseModel):
    sections: Optional[List[str]] = None
    force_refresh: Optional[bool] = False


# Phase Management Endpoints
@router.get("/{cycle_id}/reports/{report_id}/data")
@require_permission("test_report", "read")
async def get_test_report_data(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get test report data for metrics"""
    service = TestReportService(db)
    
    try:
        # Get phase information
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Finalize Test Report"
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            return {
                "phase_status": "Not Started",
                "total_sections": len(STANDARD_REPORT_SECTIONS),
                "approved_sections": 0,
                "pending_sections": len(STANDARD_REPORT_SECTIONS),
                "sections": []
            }
        
        # Get sections with their status
        sections_result = await db.execute(
            select(TestReportSection).where(
                TestReportSection.phase_id == phase.phase_id
            )
        )
        sections = sections_result.scalars().all()
        
        approved_count = sum(1 for s in sections if s.approval_status == 'approved')
        pending_count = sum(1 for s in sections if s.approval_status in ['draft', 'review'])
        
        return {
            "phase_status": phase.status,
            "total_sections": len(sections) if sections else len(STANDARD_REPORT_SECTIONS),
            "approved_sections": approved_count,
            "pending_sections": pending_count,
            "sections": [
                {
                    "section_name": s.section_name,
                    "status": s.approval_status,
                    "version": s.version,
                    "last_updated": s.updated_at.isoformat() if s.updated_at else None
                }
                for s in sections
            ] if sections else []
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get test report data: {str(e)}"
        )


@router.get("/{cycle_id}/reports/{report_id}/phase")
@require_permission("test_report", "read")
async def get_test_report_phase(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get test report phase configuration"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    # Get generation status
    service = TestReportService(db)
    generation = await service.get_generation_by_phase(phase.phase_id)
    
    # Get approval status
    approval_service = ApprovalWorkflowService(db)
    approval_status = await approval_service.get_approval_status_summary(phase.phase_id)
    
    return {
        "phase_id": phase.phase_id,
        "cycle_id": phase.cycle_id,
        "report_id": phase.report_id,
        "phase_name": phase.phase_name,
        "status": phase.status,
        "state": phase.state,
        "started_at": phase.actual_start_date.isoformat() if phase.actual_start_date else None,
        "completed_at": phase.actual_end_date.isoformat() if phase.actual_end_date else None,
        "generation_status": {
            "id": generation.id if generation else None,
            "status": generation.status if generation else "not_started",
            "started_at": generation.generation_started_at.isoformat() if generation and generation.generation_started_at else None,
            "completed_at": generation.generation_completed_at.isoformat() if generation and generation.generation_completed_at else None,
            "total_sections": generation.total_sections if generation else 0,
            "sections_completed": generation.sections_completed if generation else 0,
            "error_message": generation.error_message if generation else None
        },
        "approval_status": approval_status
    }


@router.post("/{cycle_id}/reports/{report_id}/start")
@require_permission("test_report", "write")
async def start_test_report_phase(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start the test report phase"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    # Check if previous phases are complete
    # This would check observation management phase completion
    
    # Update phase to started
    phase.state = 'In Progress'
    phase.status = 'In Progress'
    phase.actual_start_date = datetime.utcnow()
    phase.started_by = current_user.user_id
    
    await db.commit()
    
    return {"message": "Test report phase started successfully"}


# Report Generation Endpoints
@router.post("/{cycle_id}/reports/{report_id}/generate")
@require_permission("test_report", "write")
async def generate_test_report(
    cycle_id: int,
    report_id: int,
    request: ReportGenerationRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate complete test report with all sections"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    if phase.state != 'In Progress':
        raise HTTPException(status_code=400, detail="Phase must be started before generating report")
    
    # Generate report
    service = TestReportService(db)
    try:
        generation = await service.generate_test_report(
            phase.phase_id, 
            current_user.user_id, 
            request.sections
        )
        
        return {
            "generation_id": generation.id,
            "status": generation.status,
            "total_sections": generation.total_sections,
            "sections_completed": generation.sections_completed,
            "output_formats": generation.output_formats_generated,
            "message": "Report generation completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{cycle_id}/reports/{report_id}/generate-comprehensive")
@require_permission("test_report", "write")
async def generate_comprehensive_test_report(
    cycle_id: int,
    report_id: int,
    request: ReportGenerationRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate comprehensive test report using enhanced services"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    if phase.state != 'In Progress':
        raise HTTPException(status_code=400, detail="Phase must be started before generating report")
    
    # Generate comprehensive report
    service = TestReportService(db)
    try:
        result = await service.generate_comprehensive_report(
            phase.phase_id,
            current_user.user_id,
            request.sections
        )
        
        return {
            "generation_id": result["generation"].id,
            "status": result["generation"].status,
            "total_sections": result["generation"].total_sections,
            "sections_completed": result["generation"].sections_completed,
            "output_formats": result["generation"].output_formats_generated,
            "comprehensive_data": result["comprehensive_data"],
            "sections": result["sections"],
            "generation_metadata": result["generation_metadata"],
            "message": "Comprehensive report generation completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cycle_id}/reports/{report_id}/comprehensive-data")
@require_permission("test_report", "read")
async def get_comprehensive_report_data(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive report data for display"""
    
    try:
        # Use enhanced service to collect data
        enhanced_service = EnhancedReportGenerationService(db)
        
        # Get phase ID
        result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Finalize Test Report'
                )
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Test report phase not found")
        
        # Generate comprehensive report data
        comprehensive_report = await enhanced_service.generate_comprehensive_report(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=phase.phase_id,
            user_id=current_user.user_id
        )
        
        return comprehensive_report["comprehensive_data"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cycle_id}/reports/{report_id}/download-pdf")
@require_permission("test_report", "read")
async def download_comprehensive_pdf(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """Download comprehensive test report as PDF"""
    
    try:
        # Generate PDF using PDF export service
        pdf_service = PDFExportService(db)
        pdf_path = await pdf_service.generate_comprehensive_pdf_report(cycle_id, report_id)
        
        # Read PDF file
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Clean up temporary file
        import os
        os.remove(pdf_path)
        
        # Return PDF response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=test_report_{cycle_id}_{report_id}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


@router.get("/{cycle_id}/reports/{report_id}/generation/status")
@require_permission("test_report", "read")
async def get_generation_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get report generation status"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    service = TestReportService(db)
    generation = await service.get_generation_by_phase(phase.phase_id)
    
    if not generation:
        return {"status": "not_started", "message": "Report generation not started"}
    
    return {
        "generation_id": generation.id,
        "status": generation.status,
        "started_at": generation.generation_started_at.isoformat() if generation.generation_started_at else None,
        "completed_at": generation.generation_completed_at.isoformat() if generation.generation_completed_at else None,
        "duration_ms": generation.generation_duration_ms,
        "total_sections": generation.total_sections,
        "sections_completed": generation.sections_completed,
        "completion_percentage": generation.get_completion_percentage(),
        "output_formats": generation.output_formats_generated,
        "error_message": generation.error_message,
        "phase_data_collected": generation.phase_data_collected
    }


# Section Management Endpoints
@router.get("/{cycle_id}/reports/{report_id}/sections")
@require_permission("test_report", "read")
async def get_report_sections(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get all report sections"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    service = TestReportService(db)
    sections = await service.get_sections_by_phase(phase.phase_id)
    
    return [
        {
            "id": section.id,
            "section_name": section.section_name,
            "section_title": section.section_title,
            "section_order": section.section_order,
            "status": section.status,
            "last_generated_at": section.last_generated_at.isoformat() if section.last_generated_at else None,
            "requires_refresh": section.requires_refresh,
            "approval_status": section.get_approval_status(),
            "next_approver": section.get_next_approver_level(),
            "is_fully_approved": section.is_fully_approved(),
            "data_sources": section.data_sources
        }
        for section in sections
    ]


@router.get("/{cycle_id}/reports/{report_id}/sections/{section_name}")
@require_permission("test_report", "read")
async def get_section_content(
    cycle_id: int,
    report_id: int,
    section_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get specific section content"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    # Get section
    section_result = await db.execute(
        select(TestReportSection).where(
            and_(
                TestReportSection.phase_id == phase.phase_id,
                TestReportSection.section_name == section_name
            )
        )
    )
    section = section_result.scalar_one_or_none()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return {
        "id": section.id,
        "section_name": section.section_name,
        "section_title": section.section_title,
        "section_order": section.section_order,
        "section_content": section.section_content,
        "markdown_content": section.markdown_content,
        "html_content": section.html_content,
        "status": section.status,
        "last_generated_at": section.last_generated_at.isoformat() if section.last_generated_at else None,
        "requires_refresh": section.requires_refresh,
        "data_sources": section.data_sources,
        "approval_status": section.get_approval_status(),
        "next_approver": section.get_next_approver_level(),
        "is_fully_approved": section.is_fully_approved(),
        "approvals": {
            "tester": {
                "approved": section.tester_approved,
                "approved_by": section.tester_approved_by,
                "approved_at": section.tester_approved_at.isoformat() if section.tester_approved_at else None,
                "notes": section.tester_notes
            },
            "report_owner": {
                "approved": section.report_owner_approved,
                "approved_by": section.report_owner_approved_by,
                "approved_at": section.report_owner_approved_at.isoformat() if section.report_owner_approved_at else None,
                "notes": section.report_owner_notes
            },
            "executive": {
                "approved": section.executive_approved,
                "approved_by": section.executive_approved_by,
                "approved_at": section.executive_approved_at.isoformat() if section.executive_approved_at else None,
                "notes": section.executive_notes
            }
        }
    }


@router.post("/{cycle_id}/reports/{report_id}/sections/{section_name}/regenerate")
@require_permission("test_report", "write")
async def regenerate_section(
    cycle_id: int,
    report_id: int,
    section_name: str,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Regenerate specific section"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    # Regenerate section
    service = TestReportService(db)
    try:
        section = await service.generate_section(phase.phase_id, section_name, current_user.user_id)
        
        return {
            "section_id": section.id,
            "section_name": section.section_name,
            "status": section.status,
            "last_generated_at": section.last_generated_at.isoformat() if section.last_generated_at else None,
            "message": "Section regenerated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Approval Workflow Endpoints
@router.post("/{cycle_id}/reports/{report_id}/sections/{section_id}/approve")
@require_permission("test_report", "approve")
async def approve_section(
    cycle_id: int,
    report_id: int,
    section_id: int,
    request: SectionApprovalRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Approve report section"""
    
    approval_service = ApprovalWorkflowService(db)
    try:
        section = await approval_service.approve_section(
            section_id, 
            current_user.user_id, 
            request.approval_level, 
            request.notes
        )
        
        return {
            "section_id": section.id,
            "section_name": section.section_name,
            "approval_level": request.approval_level,
            "approval_status": section.get_approval_status(),
            "next_approver": section.get_next_approver_level(),
            "is_fully_approved": section.is_fully_approved(),
            "message": f"Section approved at {request.approval_level} level"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cycle_id}/reports/{report_id}/sections/{section_id}/reject")
@require_permission("test_report", "approve")
async def reject_section(
    cycle_id: int,
    report_id: int,
    section_id: int,
    request: SectionApprovalRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reject report section"""
    
    if not request.notes:
        raise HTTPException(status_code=400, detail="Rejection notes are required")
    
    approval_service = ApprovalWorkflowService(db)
    try:
        section = await approval_service.reject_section(
            section_id, 
            current_user.user_id, 
            request.approval_level, 
            request.notes
        )
        
        return {
            "section_id": section.id,
            "section_name": section.section_name,
            "rejection_level": request.approval_level,
            "status": section.status,
            "message": f"Section rejected at {request.approval_level} level"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{cycle_id}/reports/{report_id}/sections/{section_id}/request-revision")
@require_permission("test_report", "approve")
async def request_section_revision(
    cycle_id: int,
    report_id: int,
    section_id: int,
    request: SectionRevisionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Request revision of report section"""
    
    approval_service = ApprovalWorkflowService(db)
    try:
        section = await approval_service.request_revision(
            section_id, 
            current_user.user_id, 
            request.revision_level, 
            request.notes
        )
        
        return {
            "section_id": section.id,
            "section_name": section.section_name,
            "revision_level": request.revision_level,
            "status": section.status,
            "message": f"Revision requested at {request.revision_level} level"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{cycle_id}/reports/{report_id}/approvals")
@require_permission("test_report", "read")
async def get_approval_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get approval status for all sections"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    approval_service = ApprovalWorkflowService(db)
    return await approval_service.get_approval_status_summary(phase.phase_id)


@router.get("/{cycle_id}/reports/{report_id}/pending-approvals")
@require_permission("test_report", "read")
async def get_pending_approvals(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get sections pending approval by current user"""
    
    approval_service = ApprovalWorkflowService(db)
    return await approval_service.get_pending_approvals(current_user.user_id)


@router.get("/{cycle_id}/reports/{report_id}/sections/{section_id}/approval-history")
@require_permission("test_report", "read")
async def get_approval_history(
    cycle_id: int,
    report_id: int,
    section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get approval history for a section"""
    
    approval_service = ApprovalWorkflowService(db)
    return await approval_service.get_approval_history(section_id)


# Final Report Generation
@router.post("/{cycle_id}/reports/{report_id}/final-report")
@require_permission("test_report", "write")
async def generate_final_report(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate final PDF report (requires all approvals)"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    # Generate final report
    service = TestReportService(db)
    try:
        pdf_path = await service.generate_final_report(phase.phase_id)
        
        return {
            "pdf_path": pdf_path,
            "message": "Final report generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{cycle_id}/reports/{report_id}/download")
@require_permission("test_report", "read")
async def download_report(
    cycle_id: int,
    report_id: int,
    format: str = "pdf",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the test report in specified format"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    service = TestReportService(db)
    generation = await service.get_generation_by_phase(phase.phase_id)
    
    if not generation or generation.status != 'completed':
        raise HTTPException(status_code=404, detail="Report not generated yet")
    
    if format == "pdf":
        # Generate PDF download
        try:
            pdf_path = await service.generate_final_report(phase.phase_id)
            # Return PDF file response (implementation depends on PDF service)
            return Response(
                content=b"PDF content placeholder",
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=test_report_{report_id}.pdf"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


# Phase Completion
@router.post("/{cycle_id}/reports/{report_id}/complete")
@require_permission("test_report", "write")
async def complete_test_report_phase(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Complete the test report phase"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    # Complete the phase using approval workflow service
    approval_service = ApprovalWorkflowService(db)
    try:
        await approval_service.complete_phase(phase.phase_id, current_user.user_id)
        return {"message": "Test report phase completed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Metrics and Analytics
@router.get("/{cycle_id}/reports/{report_id}/metrics")
@require_permission("test_report", "read")
async def get_report_metrics(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get report generation and approval metrics"""
    
    # Get the test report phase
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Finalize Test Report'
            )
        )
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(status_code=404, detail="Test report phase not found")
    
    # Get approval metrics
    approval_service = ApprovalWorkflowService(db)
    metrics = await approval_service.get_approval_metrics(phase.phase_id)
    
    return metrics