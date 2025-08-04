"""
Data Profiling Assignment endpoints using Universal Assignment Framework
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.core.logging import get_logger
from app.models.user import User
from app.models.report import Report
from app.models.workflow import WorkflowPhase
from app.services.universal_assignment_service import UniversalAssignmentService, create_data_upload_assignment
from app.services.email_service import EmailService
from app.api.v1.endpoints.universal_assignments import _format_assignment_response

logger = get_logger(__name__)
router = APIRouter()


class DataUploadAssignmentRequest(BaseModel):
    request_type: str = "Data Upload Request"
    description: str
    priority: str = "High"
    due_date: Optional[datetime] = None


@router.post("/cycles/{cycle_id}/reports/{report_id}/assign-report-owner")
@require_permission("data_profiling", "assign")
async def create_data_upload_assignment_endpoint(
    cycle_id: int,
    report_id: int,
    assignment_request: DataUploadAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a data upload assignment using the universal assignment framework"""
    
    try:
        email_service = EmailService()
        assignment = await create_data_upload_assignment(
            db=db,
            cycle_id=cycle_id,
            report_id=report_id,
            from_user_id=current_user.user_id,
            description=assignment_request.description,
            priority=assignment_request.priority,
            email_service=email_service
        )
        
        formatted_assignment = await _format_assignment_response(assignment, db)
        return {
            "success": True,
            "assignment_id": assignment.assignment_id,
            "message": "Data upload assignment created successfully",
            "assignment": formatted_assignment
        }
        
    except ValueError as e:
        logger.error(f"ValueError creating data upload assignment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating data upload assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")


@router.get("/cycles/{cycle_id}/reports/{report_id}/universal-assignments")
async def get_data_profiling_universal_assignments(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get universal assignments for data profiling phase"""
    
    try:
        service = UniversalAssignmentService(db)
        
        # Get assignments for this context
        assignments = await service.get_assignments_by_context(
            context_type="Report",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phase_name": "Data Profiling"
            }
        )
        
        # Filter assignments relevant to current user
        user_assignments = []
        for assignment in assignments:
            if (assignment.to_user_id == current_user.user_id or 
                assignment.from_user_id == current_user.user_id or
                current_user.role in ["Admin", "Test Executive"]):
                formatted = await _format_assignment_response(assignment, db)
                user_assignments.append(formatted)
        
        return user_assignments
        
    except Exception as e:
        logger.error(f"Error getting universal assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assignments: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/complete-assignment/{assignment_id}")
async def complete_data_profiling_assignment(
    cycle_id: int,
    report_id: int,
    assignment_id: str,
    completion_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete a data profiling assignment and update workflow status"""
    
    try:
        service = UniversalAssignmentService(db)
        
        # Complete the assignment
        assignment = await service.complete_assignment(
            assignment_id=assignment_id,
            user_id=current_user.user_id,
            completion_notes=completion_notes or f"Data files uploaded and validated for Report {report_id}",
            completion_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phase_name": "Data Profiling",
                "completed_by_role": current_user.role
            }
        )
        
        # Update workflow phase to mark "Upload Data Files" as completed
        await _update_workflow_upload_status(db, cycle_id, report_id, "Completed")
        
        logger.info(f"Data profiling assignment {assignment_id} completed by user {current_user.user_id}")
        
        return {
            "success": True,
            "message": "Assignment completed successfully",
            "assignment": _format_assignment_response(assignment)
        }
        
    except ValueError as e:
        logger.error(f"ValueError completing assignment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete assignment: {str(e)}")


async def _update_workflow_upload_status(db: AsyncSession, cycle_id: int, report_id: int, status: str):
    """Update workflow phase to mark upload status"""
    
    try:
        from sqlalchemy import select, update as sql_update
        
        # Find the data profiling workflow phase
        workflow_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
        workflow_phase = workflow_query.scalar_one_or_none()
        
        if workflow_phase:
            # Update the workflow metadata to mark upload as completed
            workflow_metadata = workflow_phase.metadata or {}
            workflow_metadata["upload_data_files_status"] = status
            workflow_metadata["upload_completed_at"] = datetime.utcnow().isoformat()
            
            await db.execute(
                sql_update(WorkflowPhase)
                .where(WorkflowPhase.phase_id == workflow_phase.phase_id)
                .values(metadata=workflow_metadata)
            )
            await db.commit()
            
            logger.info(f"Updated workflow phase {workflow_phase.phase_id} upload status to {status}")
        else:
            logger.warning(f"No workflow phase found for cycle {cycle_id}, report {report_id}, phase Data Profiling")
            
    except Exception as e:
        logger.error(f"Error updating workflow upload status: {str(e)}")
        # Don't fail the assignment completion if workflow update fails
        pass


@router.get("/cycles/{cycle_id}/reports/{report_id}/workflow-status")
async def get_data_profiling_workflow_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed workflow status for data profiling phase"""
    
    try:
        
        # Get workflow phase
        workflow_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
        workflow_phase = workflow_query.scalar_one_or_none()
        
        # Get assignments
        service = UniversalAssignmentService(db)
        assignments = await service.get_assignments_by_context(
            context_type="Report",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phase_name": "Data Profiling"
            }
        )
        
        # Check if data upload is completed
        upload_completed = False
        for assignment in assignments:
            if (assignment.assignment_type == "Data Upload Request" and 
                assignment.status in ["Completed", "Approved"]):
                upload_completed = True
                break
        
        # Determine if Generate Rules should be enabled
        can_generate_rules = (
            upload_completed and
            workflow_phase and 
            workflow_phase.status in ["In Progress", "Active"]
        )
        
        # Handle metadata safely
        workflow_metadata = {}
        if workflow_phase and hasattr(workflow_phase, 'metadata') and workflow_phase.metadata:
            if isinstance(workflow_phase.metadata, dict):
                workflow_metadata = workflow_phase.metadata
            else:
                logger.warning(f"workflow_phase.metadata is not a dict: {type(workflow_phase.metadata)}")
        
        # Get profiling rule stats using raw SQL since the model doesn't match the actual database schema
        phase_id = None
        if workflow_phase:
            phase_id = workflow_phase.phase_id
        
        if phase_id:
            # Get latest version
            version_query = await db.execute(
                text("""
                SELECT version_id FROM cycle_report_data_profiling_rule_versions 
                WHERE phase_id = :phase_id
                ORDER BY version_number DESC
                LIMIT 1
                """),
                {"phase_id": phase_id}
            )
            latest_version_id = version_query.scalar()
            
            if latest_version_id:
                # Query rules by tester decisions for the latest version
                decision_query = await db.execute(
                    text("""
                    SELECT 
                        COUNT(*) as total_rules,
                        COUNT(CASE WHEN tester_decision = 'approved' THEN 1 END) as tester_approved,
                        COUNT(CASE WHEN tester_decision = 'rejected' THEN 1 END) as tester_rejected,
                        COUNT(CASE WHEN tester_decision IS NULL THEN 1 END) as no_decision
                    FROM cycle_report_data_profiling_rules 
                    WHERE version_id = :version_id
                    """),
                    {"version_id": latest_version_id}
                )
                
                result = decision_query.mappings().fetchone()
                total_rules = result['total_rules'] or 0
                approved_rules = result['tester_approved'] or 0
                rejected_rules = result['tester_rejected'] or 0
                pending_rules = result['no_decision'] or 0
            else:
                total_rules = approved_rules = rejected_rules = pending_rules = 0
            
            # Get total attributes count from report
            attributes_query = await db.execute(
                text("""
                SELECT COUNT(DISTINCT ra.id) as count
                FROM cycle_report_planning_attributes ra
                WHERE ra.phase_id = :phase_id
                """),
                {"phase_id": phase_id}
            )
            total_attributes = attributes_query.scalar() or 0
        else:
            total_rules = approved_rules = rejected_rules = pending_rules = 0
            total_attributes = 0
        
        # Calculate overall completion percentage
        overall_completion = 0
        if workflow_phase:
            # Basic progress calculation based on completed activities
            # Start phase: 10%, Upload data: 20%, Generate rules: 50%, Approve rules: 80%, Execute: 100%
            if workflow_phase.status == "Completed":
                overall_completion = 100
            elif total_rules > 0:
                if approved_rules > 0:
                    # Have approved rules: 80-90%
                    overall_completion = 80 + min(10, int((approved_rules / total_rules) * 10))
                else:
                    # Have rules but not approved: 50-80%
                    overall_completion = 50 + min(30, int((total_rules / max(total_attributes, 1)) * 30))
            elif upload_completed:
                # Data uploaded: 20-50%
                overall_completion = 20
            elif workflow_phase.status in ["In Progress", "Active"]:
                # Phase started: 10%
                overall_completion = 10
        
        return {
            "phase_status": workflow_phase.status if workflow_phase else "Not Started",
            "upload_data_files_status": workflow_metadata.get("upload_data_files_status", "Not Started"),
            "upload_completed": upload_completed,
            "can_generate_rules": can_generate_rules,
            "can_upload_files": current_user.role in ["Report Owner", "Report Owner Executive", "Admin"],
            "can_request_data": current_user.role in ["Tester", "Test Executive", "Admin"],
            "assignments_count": len(assignments),
            "completed_assignments": len([a for a in assignments if a.status in ["Completed", "Approved"]]),
            "total_attributes": total_attributes,
            "total_rules": total_rules,
            "approved_rules": approved_rules,
            "rejected_rules": rejected_rules,
            "pending_rules": pending_rules,
            "needs_revision_rules": 0,  # Could be calculated if there's a needs_revision status
            "overall_completion_percentage": overall_completion
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


@router.get("/cycles/{cycle_id}/reports/{report_id}/status")
async def get_data_profiling_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data profiling status for a cycle/report (UI compatibility endpoint)"""
    # This endpoint reuses the workflow-status logic for UI compatibility
    return await get_data_profiling_workflow_status(cycle_id, report_id, db, current_user)


@router.get("/cycles/{cycle_id}/reports/{report_id}/results")
async def get_data_profiling_results(
    cycle_id: int,
    report_id: int,
    attribute_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get profiling results for a cycle/report"""
    # For now, return empty results - this would be populated by actual profiling execution
    return []


@router.get("/cycles/{cycle_id}/reports/{report_id}/assigned-rules")
async def get_assigned_rules_for_approval(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get rules assigned to current user for approval"""
    # For now, return empty list - this would be populated with rules assigned to the current user
    return []


@router.get("/cycles/{cycle_id}/reports/{report_id}/latest-job")
async def get_latest_profiling_job(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the latest profiling job for a cycle/report"""
    
    try:
        # Get workflow phase
        workflow_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
        workflow_phase = workflow_query.scalar_one_or_none()
        
        if not workflow_phase:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Import and use the data profiling service
        from app.services.data_profiling_service import DataProfilingService
        service = DataProfilingService(db)
        
        # Get the latest job for this phase
        job = await service.get_latest_job_for_phase(workflow_phase.phase_id)
        
        if not job:
            # No job exists yet
            return {
                "job_id": None,
                "status": "not_started",
                "created_at": None,
                "started_at": None,
                "completed_at": None,
                "progress": 0,
                "total_rules": 0,
                "completed_rules": 0,
                "failed_rules": 0,
                "message": "No profiling jobs have been executed for this cycle/report"
            }
        
        # Import job manager to get background job status
        from app.core.background_jobs import job_manager
        
        # Get background job status if available
        bg_job_status = job_manager.get_job_status(job.job_id)
        
        # Calculate progress
        progress = 0
        current_step = ""
        
        if bg_job_status:
            # Use background job progress if available
            progress = bg_job_status.get("progress_percentage", 0)
            current_step = bg_job_status.get("current_step", "")
            
            # Override status from background job if it's more current
            bg_status = bg_job_status.get("status", job.status)
            if bg_status in ["running", "failed", "completed"]:
                job.status = bg_status
        elif job.total_records and job.records_processed:
            # Fallback to database progress
            progress = int((job.records_processed / job.total_records) * 100)
        
        # Get rule execution counts from the job's configuration
        total_rules = 0
        completed_rules = 0
        failed_rules = 0
        
        if job.status == 'completed':
            # Query attribute results to get rule counts
            result_count_query = await db.execute(
                text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN anomaly_count > 0 THEN 1 ELSE 0 END) as with_anomalies
                FROM cycle_report_data_profiling_attribute_results
                WHERE profiling_job_id = :job_id
                """),
                {"job_id": job.id}
            )
            counts = result_count_query.fetchone()
            if counts:
                total_rules = counts[0] or 0
                completed_rules = counts[0] or 0
                failed_rules = 0  # All are considered completed for now
        
        # Build message
        message = current_step if current_step else f"Job {job.status}"
        if job.status == 'failed' and job.error_message:
            message = job.error_message
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "progress": progress,
            "current_step": current_step,
            "total_rules": total_rules,
            "completed_rules": completed_rules,
            "failed_rules": failed_rules,
            "total_records": job.total_records,
            "records_processed": job.records_processed,
            "records_failed": job.records_failed,
            "anomalies_detected": job.anomalies_detected,
            "data_quality_score": job.data_quality_score,
            "error_message": job.error_message,
            "message": message,
            "background_job_id": job.job_id  # Include for debugging
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest profiling job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get profiling job: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/start-profiling")
async def start_profiling_job(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a new profiling job for a cycle/report"""
    
    try:
        # Check permissions - only testers and admins can start profiling
        if current_user.role not in ["Tester", "Test Executive", "Admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to start profiling")
        
        # Get workflow phase
        workflow_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
        workflow_phase = workflow_query.scalar_one_or_none()
        
        if not workflow_phase:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Import and use the data profiling service
        from app.services.data_profiling_service import DataProfilingService
        service = DataProfilingService(db)
        
        # Check if there's already a running job
        existing_job = await service.get_latest_job_for_phase(workflow_phase.phase_id)
        if existing_job and existing_job.status in ['pending', 'queued', 'running']:
            raise HTTPException(
                status_code=400, 
                detail=f"A profiling job is already {existing_job.status} for this phase"
            )
        
        # Create or get configuration
        config = await service.get_or_create_configuration(
            phase_id=workflow_phase.phase_id,
            user_id=current_user.user_id,
            source_type='database_direct',  # Default to database
            profiling_mode='sample_based',  # Default to sample-based
            sample_size=10000  # Default sample size
        )
        
        # Start the profiling job
        job = await service.start_profiling_job(
            configuration_id=config.id,
            user_id=current_user.user_id,
            run_async=True  # Run asynchronously
        )
        
        return {
            "success": True,
            "job_id": job.job_id,
            "status": job.status,
            "message": "Profiling job started successfully",
            "created_at": job.created_at.isoformat() if job.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting profiling job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start profiling job: {str(e)}")


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a background profiling job"""
    from app.core.background_jobs import job_manager
    
    job_status = job_manager.get_job_status(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return job_status


@router.get("/cycles/{cycle_id}/reports/{report_id}/rules")
async def get_data_profiling_rules(
    cycle_id: int,
    report_id: int,
    status: Optional[str] = None,
    version_id: Optional[str] = None,
    tester_decision: Optional[str] = None,
    report_owner_decision: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all profiling rules for a cycle/report, optionally filtered by version"""
    
    try:
        
        # Get workflow phase for data profiling
        workflow_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Data Profiling"
            )
        )
        workflow_phase = workflow_query.scalar_one_or_none()
        
        if not workflow_phase:
            return []
        
        # Get planning phase to join with correct attributes
        planning_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == "Planning"
            )
        )
        planning_phase = planning_query.scalar_one_or_none()
        
        if not planning_phase:
            return []
        
        # Build query with optional status filter
        # Join with report_attributes to get sorting fields
        base_query = """
        SELECT 
            r.rule_id,
            r.version_id,
            r.attribute_id,
            r.attribute_name,
            r.rule_name,
            r.rule_type,
            r.rule_description,
            r.rule_code,
            r.rule_parameters,
            r.llm_provider,
            r.llm_rationale,
            r.llm_confidence_score,
            r.regulatory_reference,
            r.severity,
            r.is_executable,
            r.execution_order,
            r.tester_decision,
            r.tester_notes,
            r.tester_decided_by,
            r.tester_decided_at,
            r.report_owner_decision,
            r.report_owner_notes,
            r.report_owner_decided_by,
            r.report_owner_decided_at,
            r.status,
            r.last_execution_job_id,
            r.last_execution_at,
            r.created_at,
            r.updated_at,
            r.phase_id,
            a.is_primary_key,
            a.is_cde,
            a.has_issues,
            a.line_item_number
        FROM cycle_report_data_profiling_rules r
        JOIN cycle_report_planning_attributes a ON r.attribute_id = a.id AND a.phase_id = :planning_phase_id
        WHERE r.phase_id = :phase_id
        """
        
        params = {"phase_id": workflow_phase.phase_id, "planning_phase_id": planning_phase.phase_id}
        
        if status:
            base_query += " AND r.status = :status"
            params["status"] = status
            
        if version_id:
            base_query += " AND r.version_id = :version_id"
            params["version_id"] = version_id
            
        if tester_decision:
            if tester_decision.lower() == 'none':
                base_query += " AND r.tester_decision IS NULL"
            else:
                base_query += " AND LOWER(r.tester_decision::text) = LOWER(:tester_decision)"
                params["tester_decision"] = tester_decision
                
        if report_owner_decision:
            if report_owner_decision.lower() == 'none':
                base_query += " AND r.report_owner_decision IS NULL"
            else:
                base_query += " AND LOWER(r.report_owner_decision::text) = LOWER(:report_owner_decision)"
                params["report_owner_decision"] = report_owner_decision
            
        # Order by: Primary Keys first, then CDEs, then Issues, then by line item number
        base_query += """ 
        ORDER BY 
            a.is_primary_key DESC NULLS LAST,
            a.is_cde DESC NULLS LAST,
            a.has_issues DESC NULLS LAST,
            CASE 
                WHEN a.line_item_number ~ '^[0-9]+$' THEN LPAD(a.line_item_number, 10, '0')
                ELSE a.line_item_number
            END NULLS LAST,
            r.rule_id
        """
        
        rules_query = await db.execute(text(base_query), params)
        rules_rows = rules_query.fetchall()
        
        # Convert to list of dictionaries
        rules = []
        for row in rules_rows:
            rule_dict = dict(row._mapping)
            # Convert datetime objects to strings
            if rule_dict.get('tester_decided_at'):
                rule_dict['tester_decided_at'] = rule_dict['tester_decided_at'].isoformat()
            if rule_dict.get('report_owner_decided_at'):
                rule_dict['report_owner_decided_at'] = rule_dict['report_owner_decided_at'].isoformat()
            if rule_dict.get('last_execution_at'):
                rule_dict['last_execution_at'] = rule_dict['last_execution_at'].isoformat()
            if rule_dict.get('created_at'):
                rule_dict['created_at'] = rule_dict['created_at'].isoformat()
            if rule_dict.get('updated_at'):
                rule_dict['updated_at'] = rule_dict['updated_at'].isoformat()
            
            # Add permission flags based on user role
            rule_dict['can_approve'] = current_user.role in ["Report Owner", "Report Owner Executive", "Admin", "Tester", "Test Executive"]
            rule_dict['can_reject'] = current_user.role in ["Report Owner", "Report Owner Executive", "Admin", "Tester", "Test Executive"]
            rule_dict['can_revise'] = current_user.role in ["Report Owner", "Report Owner Executive", "Admin", "Tester", "Test Executive"]
            
            # Include the sorting fields from report_attributes
            rule_dict['is_primary_key'] = rule_dict.get('is_primary_key', False)
            rule_dict['is_cde'] = rule_dict.get('is_cde', False)
            rule_dict['has_issues'] = rule_dict.get('has_issues', False)
            rule_dict['line_item_number'] = rule_dict.get('line_item_number', '')
            
            rules.append(rule_dict)
        
        return rules
        
    except Exception as e:
        logger.error(f"Error getting data profiling rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get profiling rules: {str(e)}")


