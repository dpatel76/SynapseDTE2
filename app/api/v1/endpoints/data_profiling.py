"""
Data Profiling API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, distinct, update, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.core.database import get_db
from app.core.auth import get_current_user, RoleChecker
from app.models.user import User
from app.models.data_profiling import (
    DataProfilingRuleVersion, ProfilingRule, DataProfilingUpload, 
    DataProfilingConfiguration, DataProfilingJob, AttributeProfileResult, 
    ProfilingResult, VersionStatus, ProfilingRuleStatus, 
    ProfilingMode, Decision
)
from app.models.planning import PlanningPDEMapping
from app.models.report_attribute import ReportAttribute
from app.services.data_profiling_service import DataProfilingService
from app.core.exceptions import NotFoundException, BusinessLogicException
# TODO: Create these schemas if needed
# from app.schemas.data_profiling_schemas import (
#     DataProfilingStatusResponse, GenerateRulesRequest, ExecuteProfilingRequest,
#     RuleApprovalRequest, ProfilingResultsResponse
# )
from app.models.workflow import WorkflowPhase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data_profiling"])

# Create dependency injection function
def get_data_profiling_service(db: AsyncSession = Depends(get_db)) -> DataProfilingService:
    """Get data profiling service instance"""
    return DataProfilingService(db)

# Define role groups
tester_roles = ["Tester", "Test Executive"]
report_owner_roles = ["Report Owner", "Report Owner Executive"]
management_roles = ["Data Executive", "Admin"]

# Helper function to get phase_id
async def get_phase_id(db: AsyncSession, cycle_id: int, report_id: int, phase_name: str) -> Optional[int]:
    """Get the phase_id for a given cycle, report, and phase name"""
    phase_query = await db.execute(
        select(WorkflowPhase.phase_id).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == phase_name
            )
        )
    )
    result = phase_query.scalar_one_or_none()
    return result

# Helper functions for calculating anomaly metrics
async def _calculate_attributes_with_anomalies(db: AsyncSession, phase_id: int) -> int:
    """Calculate number of attributes with anomalies based on composite DQ score < 95%"""
    if not phase_id:
        return 0
    
    # Get workflow phase to extract cycle_id and report_id
    from app.models.workflow import WorkflowPhase
    phase_query = await db.execute(
        select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
    )
    phase = phase_query.scalar_one_or_none()
    if not phase:
        return 0
    
    # Get all unique attributes that have profiling results
    attr_query = await db.execute(
        select(distinct(ProfilingResult.attribute_id))
        .where(
            and_(
                ProfilingResult.phase_id == phase_id,
                ProfilingResult.attribute_id.isnot(None)
            )
        )
    )
    attribute_ids = [row[0] for row in attr_query.fetchall()]
    
    # Calculate composite DQ scores and count those below 95%
    from app.services.data_quality_service import DataQualityService
    anomaly_count = 0
    for attr_id in attribute_ids:
        dq_data = await DataQualityService.calculate_composite_dq_score(
            db, phase.cycle_id, phase.report_id, attr_id
        )
        if dq_data and dq_data.get('composite_score', 100) < 95:
            anomaly_count += 1
    
    return anomaly_count

async def _calculate_cdes_with_anomalies(db: AsyncSession, phase_id: int) -> int:
    """Calculate number of CDEs with anomalies based on composite DQ score < 95%"""
    if not phase_id:
        return 0
    
    # Get workflow phase to extract cycle_id and report_id
    from app.models.workflow import WorkflowPhase
    phase_query = await db.execute(
        select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
    )
    phase = phase_query.scalar_one_or_none()
    if not phase:
        return 0
    
    # Get all unique CDE attributes that have profiling results
    attr_query = await db.execute(
        select(distinct(ProfilingResult.attribute_id))
        .select_from(ProfilingResult)
        .join(ReportAttribute, ProfilingResult.attribute_id == ReportAttribute.id)
        .where(
            and_(
                ProfilingResult.phase_id == phase_id,
                ProfilingResult.attribute_id.isnot(None),
                ReportAttribute.is_cde == True
            )
        )
    )
    attribute_ids = [row[0] for row in attr_query.fetchall()]
    
    # Calculate composite DQ scores and count those below 95%
    from app.services.data_quality_service import DataQualityService
    anomaly_count = 0
    for attr_id in attribute_ids:
        dq_data = await DataQualityService.calculate_composite_dq_score(
            db, phase.cycle_id, phase.report_id, attr_id
        )
        if dq_data and dq_data.get('composite_score', 100) < 95:
            anomaly_count += 1
    
    return anomaly_count

@router.get("/cycles/{cycle_id}/reports/{report_id}/status")
async def get_data_profiling_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive data profiling status"""
    
    try:
        # Get phase_id using the helper function
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            # Return minimal status if phase doesn't exist
            return {
                "phase_id": None,
                "cycle_id": cycle_id,
                "report_id": report_id,
                "phase_status": "Not Started",
                "can_create_version": False,
                "can_execute": False,
                "total_attributes": 0,
                "attributes_with_rules": 0,
                "total_profiling_rules": 0,
                "rules_generated": 0,
                "files_uploaded": 0,
                "profiling_completed": False,
                "attributes_with_anomalies": 0,
                "cdes_with_anomalies": 0,
                "days_elapsed": 0,
                "completion_percentage": 0
            }
        
        # Get the workflow phase using the helper function result
        from app.models.workflow import WorkflowPhase
        workflow_query = await db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = workflow_query.scalar_one()
        
        # Get planning phase to count total attributes from planning phase
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
        
        if planning_phase:
            # Count total attributes from planning phase
            total_attributes_query = await db.execute(
                select(func.count()).select_from(ReportAttribute)
                .where(ReportAttribute.phase_id == planning_phase.phase_id)
            )
            total_attributes = total_attributes_query.scalar() or 0
        else:
            total_attributes = 0
            
        # Count attributes with rules from data profiling phase
        if phase_id:
            # Get latest version
            latest_version_query = await db.execute(
                select(DataProfilingRuleVersion)
                .where(DataProfilingRuleVersion.phase_id == phase_id)
                .order_by(DataProfilingRuleVersion.version_number.desc())
                .limit(1)
            )
            latest_version = latest_version_query.scalar_one_or_none()
            
            if latest_version:
                # Count distinct attributes from rules
                attributes_query = await db.execute(
                    select(func.count(distinct(ProfilingRule.attribute_id)))
                    .where(ProfilingRule.version_id == latest_version.version_id)
                )
                attributes_with_rules = attributes_query.scalar() or 0
            else:
                attributes_with_rules = 0
        else:
            attributes_with_rules = 0
        
        # Get latest version
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        current_version = version_query.scalar_one_or_none()
        
        # Get total rules count for the current version
        if current_version:
            total_rules_query = await db.execute(
                select(func.count(ProfilingRule.rule_id))
                .where(ProfilingRule.version_id == current_version.version_id)
            )
            total_profiling_rules = total_rules_query.scalar() or 0
        else:
            total_profiling_rules = 0
        
        # Calculate completion percentage
        completion_percentage = 0
        if total_attributes > 0:
            completion_percentage = int((attributes_with_rules / total_attributes) * 100)
        
        return {
            "phase_id": phase.phase_id,
            "cycle_id": cycle_id,
            "report_id": report_id,
            "phase_status": phase.status,
            "current_version": {
                "version_id": str(current_version.version_id) if current_version else None,
                "version_number": current_version.version_number if current_version else None,
                "status": current_version.version_status if current_version else None,
                "total_rules": current_version.total_rules if current_version else 0,
                "approved_rules": current_version.approved_rules if current_version else 0,
                "rejected_rules": current_version.rejected_rules if current_version else 0
            } if current_version else None,
            "can_create_version": phase.status == "In Progress" and not current_version,
            "can_submit": current_version and current_version.version_status == VersionStatus.DRAFT if current_version else False,
            "can_approve": current_version and current_version.version_status == VersionStatus.PENDING_APPROVAL if current_version else False,
            "can_execute": current_version and current_version.version_status == VersionStatus.APPROVED if current_version else False,
            # Add metrics fields expected by frontend
            "total_attributes": total_attributes,
            "attributes_with_rules": attributes_with_rules,
            "total_profiling_rules": total_profiling_rules,
            "rules_generated": total_profiling_rules,  # Same as total for now
            "attributes_with_anomalies": await _calculate_attributes_with_anomalies(db, phase_id),
            "cdes_with_anomalies": await _calculate_cdes_with_anomalies(db, phase_id),
            "days_elapsed": 1,  # TODO: Calculate from phase start date
            "completion_percentage": completion_percentage,
            "can_upload_files": True,  # Always true for now
            "can_generate_rules": total_attributes > 0,
            "can_execute_profiling": total_profiling_rules > 0,
            "can_complete": completion_percentage == 100,
            "files_uploaded": 0,  # TODO: Get from uploads table
            "profiling_completed": False,  # TODO: Check execution status
            "started_at": phase.created_at.isoformat() if hasattr(phase, 'created_at') and phase.created_at else None,
            "completed_at": None  # TODO: Calculate from execution completion
        }
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Error in get_data_profiling_status: {str(e)}\n{error_detail}")
        print(f"ERROR in status endpoint: {str(e)}")
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/cycles/{cycle_id}/reports/{report_id}/files")
async def get_data_files(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get uploaded data files for a cycle/report"""
    
    # Get phase_id
    phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
    if not phase_id:
        return []
    
    # TODO: Implement actual file listing from database
    # For now, return empty list to prevent 404 error
    return []

@router.delete("/cycles/{cycle_id}/reports/{report_id}/files/{file_id}")
async def delete_data_file(
    cycle_id: int,
    report_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete an uploaded data file"""
    
    # Get phase_id
    phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
    if not phase_id:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    # TODO: Implement actual file deletion
    # For now, return success
    return {"success": True, "message": "File deleted successfully"}

@router.get("/cycles/{cycle_id}/reports/{report_id}/rules")
async def get_profiling_rules(
    cycle_id: int,
    report_id: int,
    status: Optional[str] = None,
    version_id: Optional[str] = None,
    tester_decision: Optional[str] = None,
    report_owner_decision: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get profiling rules for a cycle/report with optional filters"""
    
    # Get phase_id
    phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
    if not phase_id:
        return []
    
    # Build query
    query = select(ProfilingRule).join(
        DataProfilingRuleVersion,
        ProfilingRule.version_id == DataProfilingRuleVersion.version_id
    ).where(
        DataProfilingRuleVersion.phase_id == phase_id
    )
    
    # Apply filters
    if version_id:
        query = query.where(ProfilingRule.version_id == version_id)
    else:
        # Get latest version by default
        latest_version_subq = select(DataProfilingRuleVersion.version_id).where(
            DataProfilingRuleVersion.phase_id == phase_id
        ).order_by(DataProfilingRuleVersion.version_number.desc()).limit(1).scalar_subquery()
        query = query.where(ProfilingRule.version_id == latest_version_subq)
    
    if status:
        query = query.where(ProfilingRule.status == status)
    
    if tester_decision:
        query = query.where(ProfilingRule.tester_decision == tester_decision)
        
    if report_owner_decision:
        query = query.where(ProfilingRule.report_owner_decision == report_owner_decision)
    
    # Join with planning attributes to get proper ordering
    from app.models.report_attribute import ReportAttribute
    from app.models.workflow import WorkflowPhase
    
    # Get planning phase for this cycle/report
    planning_phase_query = select(WorkflowPhase).where(
        WorkflowPhase.cycle_id == cycle_id,
        WorkflowPhase.report_id == report_id,
        WorkflowPhase.phase_name == "Planning"
    )
    planning_phase = await db.execute(planning_phase_query)
    planning_phase_obj = planning_phase.scalar_one_or_none()
    
    if planning_phase_obj:
        # Create a new query that selects both ProfilingRule and ReportAttribute
        # Join on attribute_name since attribute_id might not match between phases
        query = select(ProfilingRule, ReportAttribute).join(
            ReportAttribute,
            and_(
                ProfilingRule.attribute_name == ReportAttribute.attribute_name,
                ReportAttribute.phase_id == planning_phase_obj.phase_id
            )
        ).where(
            ProfilingRule.phase_id == phase_id
        )
        
        # Re-apply filters
        if version_id:
            query = query.where(ProfilingRule.version_id == version_id)
        else:
            # Get latest version by default
            latest_version_subq = select(DataProfilingRuleVersion.version_id).where(
                DataProfilingRuleVersion.phase_id == phase_id
            ).order_by(DataProfilingRuleVersion.version_number.desc()).limit(1).scalar_subquery()
            query = query.where(ProfilingRule.version_id == latest_version_subq)
        
        if status:
            query = query.where(ProfilingRule.status == status)
        
        if tester_decision:
            query = query.where(ProfilingRule.tester_decision == tester_decision)
            
        if report_owner_decision:
            query = query.where(ProfilingRule.report_owner_decision == report_owner_decision)
        
        # Order by: Primary Keys first, then CDEs, then issues, then line item number
        query = query.order_by(
            ReportAttribute.is_primary_key.desc(),  # Primary keys first
            ReportAttribute.cde_flag.desc(),         # Then CDEs (mapped from is_cde column)
            ReportAttribute.historical_issues_flag.desc(),  # Then attributes with issues (mapped from has_issues column)
            ReportAttribute.line_item_number.asc().nulls_last(),  # Then by line item number
            ProfilingRule.rule_name  # Finally by rule name within each attribute
        )
        
        # Execute query
        result = await db.execute(query)
        rules_with_attrs = result.all()
        
        # Debug logging
        if rules_with_attrs and len(rules_with_attrs) > 0:
            sample_row = rules_with_attrs[0]
            if hasattr(sample_row, 'ProfilingRule'):
                sample_rule = sample_row.ProfilingRule
                sample_attr = sample_row.ReportAttribute
            else:
                sample_rule = sample_row[0]
                sample_attr = sample_row[1]
            logger.info(f"Sample joined data - Rule: {sample_rule.attribute_name}, Attr line_item: {sample_attr.line_item_number if sample_attr else 'None'}")
    else:
        # Fallback to simple ordering if planning phase not found
        query = query.order_by(ProfilingRule.attribute_name, ProfilingRule.rule_name)
        
        # Execute query
        result = await db.execute(query)
        rules = result.scalars().all()
        rules_with_attrs = [(rule, None) for rule in rules]
    
    # Build result with attribute metadata
    result_list = []
    for row in rules_with_attrs:
        # Handle SQLAlchemy Row objects from joined queries
        if hasattr(row, '_mapping'):
            # This is a Row object from a joined query
            rule = row[0]  # ProfilingRule
            attr = row[1]  # ReportAttribute
        elif isinstance(row, tuple):
            rule = row[0]
            attr = row[1]
        else:
            # This is a single ProfilingRule object
            rule = row
            attr = None
        
        # Build the rule dictionary
        rule_dict = {
            "rule_id": str(rule.rule_id),
            "version_id": str(rule.version_id),
            "attribute_id": rule.attribute_id,
            "attribute_name": rule.attribute_name,
            "rule_name": rule.rule_name,
            "rule_type": rule.rule_type,
            "rule_description": rule.rule_description,
            "rule_code": rule.rule_code,
            "rule_parameters": rule.rule_parameters,
            "severity": rule.severity,
            "status": rule.status,
            "is_executable": rule.is_executable,
            "execution_order": rule.execution_order,
            "llm_provider": rule.llm_provider,
            "llm_rationale": rule.llm_rationale,
            "llm_confidence_score": float(rule.llm_confidence_score) if rule.llm_confidence_score else None,
            "regulatory_reference": rule.regulatory_reference,
            "tester_decision": rule.tester_decision,
            "tester_notes": rule.tester_notes,
            "tester_decided_by": rule.tester_decided_by,
            "tester_decided_at": rule.tester_decided_at.isoformat() if rule.tester_decided_at else None,
            "report_owner_decision": rule.report_owner_decision,
            "report_owner_notes": rule.report_owner_notes,
            "report_owner_decided_by": rule.report_owner_decided_by,
            "report_owner_decided_at": rule.report_owner_decided_at.isoformat() if rule.report_owner_decided_at else None,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
            "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
        }
        
        # Add attribute metadata if we have it
        if attr:
            rule_dict.update({
                "line_item_number": attr.line_item_number,
                "is_primary_key": attr.is_primary_key if hasattr(attr, 'is_primary_key') else False,
                "cde_flag": attr.cde_flag if hasattr(attr, 'cde_flag') else False,
                "historical_issues_flag": attr.historical_issues_flag if hasattr(attr, 'historical_issues_flag') else False
            })
        else:
            # Default values when no attribute metadata
            rule_dict.update({
                "line_item_number": None,
                "is_primary_key": False,
                "cde_flag": False,
                "historical_issues_flag": False
            })
        
        result_list.append(rule_dict)
    
    return result_list

@router.get("/cycles/{cycle_id}/reports/{report_id}/attribute-summary")
async def get_attribute_rules_summary(
    cycle_id: int,
    report_id: int,
    version_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of rules grouped by attribute"""
    
    # Get phase_id
    phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
    if not phase_id:
        return []
    
    # Get attributes and their rule counts
    query = """
        WITH latest_version AS (
            SELECT version_id 
            FROM cycle_report_data_profiling_rule_versions 
            WHERE phase_id = :phase_id 
            ORDER BY version_number DESC 
            LIMIT 1
        ),
        rule_counts AS (
            SELECT 
                r.attribute_id,
                r.attribute_name,
                COUNT(*) as total_rules,
                SUM(CASE WHEN r.status = 'approved' THEN 1 ELSE 0 END) as approved_count,
                SUM(CASE WHEN r.status = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
                SUM(CASE WHEN r.status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN r.status = 'needs_revision' THEN 1 ELSE 0 END) as needs_revision_count
            FROM cycle_report_data_profiling_rules r
            WHERE r.version_id = COALESCE(:version_id, (SELECT version_id FROM latest_version))
            GROUP BY r.attribute_id, r.attribute_name
        )
        SELECT 
            a.id as attribute_id,
            a.attribute_name,
            a.data_type as attribute_type,
            a.is_mandatory as mandatory,
            COALESCE(rc.total_rules, 0) as total_rules,
            COALESCE(rc.approved_count, 0) as approved_count,
            COALESCE(rc.rejected_count, 0) as rejected_count,
            COALESCE(rc.pending_count, 0) as pending_count,
            COALESCE(rc.needs_revision_count, 0) as needs_revision_count,
            a.line_item_number,
            pde.is_cde,
            pde.is_primary_key,
            CASE WHEN pde.has_issues = true THEN true ELSE false END as has_issues
        FROM cycle_report_planning_attributes a
        LEFT JOIN rule_counts rc ON a.id = rc.attribute_id
        LEFT JOIN cycle_report_planning_pde_mappings pde ON a.pde_mapping_id = pde.id
        WHERE a.phase_id = :phase_id
        ORDER BY a.line_item_number, a.attribute_name
    """
    
    result = await db.execute(
        text(query),
        {"phase_id": phase_id, "version_id": version_id}
    )
    
    return [
        {
            "attribute_id": row.attribute_id,
            "attribute_name": row.attribute_name,
            "attribute_type": row.attribute_type,
            "mandatory": row.mandatory,
            "total_rules": row.total_rules,
            "approved_count": row.approved_count,
            "rejected_count": row.rejected_count,
            "pending_count": row.pending_count,
            "needs_revision_count": row.needs_revision_count,
            "line_item_number": row.line_item_number,
            "is_cde": row.is_cde,
            "is_primary_key": row.is_primary_key,
            "has_issues": row.has_issues
        }
        for row in result
    ]

@router.get("/cycles/{cycle_id}/reports/{report_id}/versions")
async def get_rule_versions(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions of profiling rules"""
    
    # Get phase_id
    phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
    if not phase_id:
        return []
    
    query = select(DataProfilingRuleVersion).where(
        DataProfilingRuleVersion.phase_id == phase_id
    ).order_by(DataProfilingRuleVersion.version_number.desc())
    
    result = await db.execute(query)
    versions = result.scalars().all()
    
    return [
        {
            "version_id": str(version.version_id),
            "version_number": version.version_number,
            "version_status": version.version_status,
            "is_current": version.version_number == max([v.version_number for v in versions]),
            "parent_version_id": str(version.parent_version_id) if version.parent_version_id else None,
            "total_rules": version.total_rules,
            "approved_rules": version.approved_rules,
            "rejected_rules": version.rejected_rules,
            "submitted_by": version.submitted_by_id,
            "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
            "approved_by": version.approved_by_id,
            "approved_at": version.approved_at.isoformat() if version.approved_at else None,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "updated_at": version.updated_at.isoformat() if version.updated_at else None
        }
        for version in versions
    ]

@router.post("/phases/{phase_id}/start")
async def start_data_profiling_phase(
    phase_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start data profiling phase and create the first version if none exist.
    This is called when the phase transitions from "Not Started" to "In Progress".
    """
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get the phase
        phase_query = select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        phase_result = await db.execute(phase_query)
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(status_code=404, detail="Phase not found")
        
        if phase.phase_name != "Data Profiling":
            raise HTTPException(status_code=400, detail="This endpoint is only for Data Profiling phase")
        
        # Update phase status if needed
        if phase.status == "not_started":
            phase.status = "in_progress"
            phase.started_at = datetime.utcnow()
            phase.updated_at = datetime.utcnow()
            phase.updated_by_id = current_user.user_id
            await db.commit()
        
        # Check if any versions exist
        existing_version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase_id)
            .limit(1)
        )
        existing_version = existing_version_query.scalar_one_or_none()
        
        if existing_version:
            # Version already exists, just return success
            return {
                "success": True,
                "message": "Data profiling phase already started",
                "phase_id": phase_id,
                "phase_status": phase.status,
                "version_exists": True,
                "version_id": str(existing_version.version_id),
                "version_number": existing_version.version_number
            }
        
        # Create the first version
        new_version = DataProfilingRuleVersion(
            phase_id=phase_id,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            total_rules=0,
            approved_rules=0,
            rejected_rules=0,
            created_by_id=current_user.user_id,
            created_at=datetime.utcnow(),
            updated_by_id=current_user.user_id,
            updated_at=datetime.utcnow()
        )
        db.add(new_version)
        await db.commit()
        
        logger.info(f"Started data profiling phase {phase_id} and created version 1")
        
        return {
            "success": True,
            "message": "Data profiling phase started successfully",
            "phase_id": phase_id,
            "phase_status": phase.status,
            "version_exists": True,
            "version_id": str(new_version.version_id),
            "version_number": 1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting data profiling phase: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start data profiling phase: {str(e)}")


@router.post("/versions/{version_id}/execute")
async def execute_profiling_rules(
    version_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: DataProfilingService = Depends(get_data_profiling_service)
):
    """Execute all approved rules in a version"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        job_id = await service.execute_approved_rules(version_id)
        
        return {
            "success": True,
            "message": "Profiling execution started",
            "job_id": job_id,
            "version_id": version_id
        }
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessLogicException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing profiling rules: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to execute profiling rules: {str(e)}")


@router.post("/cycles/{cycle_id}/reports/{report_id}/execute-profiling")
async def execute_profiling_for_report(
    cycle_id: int,
    report_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: DataProfilingService = Depends(get_data_profiling_service),
    db: AsyncSession = Depends(get_db)
):
    """Execute profiling rules for the latest approved version"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get phase_id
        logger.info(f"Getting phase_id for cycle {cycle_id}, report {report_id}")
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        logger.info(f"Found phase_id: {phase_id}")
        
        # Get the latest approved version
        logger.info("Looking for approved version...")
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(
                and_(
                    DataProfilingRuleVersion.phase_id == phase_id,
                    DataProfilingRuleVersion.version_status == VersionStatus.APPROVED
                )
            )
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            logger.info("No approved version found, looking for any version...")
            # If no approved version, try to get the latest draft version
            version_query = await db.execute(
                select(DataProfilingRuleVersion)
                .where(DataProfilingRuleVersion.phase_id == phase_id)
                .order_by(DataProfilingRuleVersion.version_number.desc())
                .limit(1)
            )
            version = version_query.scalar_one_or_none()
            
        if not version:
            raise HTTPException(status_code=400, detail="No data profiling version found")
        
        logger.info(f"Found version {version.version_number} with status {version.version_status}")
        
        # Execute the version
        logger.info(f"Executing version {version.version_id}...")
        job_id = await service.execute_approved_rules(str(version.version_id))
        
        logger.info(f"Execution started with job_id: {job_id}")
        
        return {
            "success": True,
            "message": f"Profiling execution started for version {version.version_number}",
            "job_id": job_id,
            "version_id": str(version.version_id),
            "version_number": version.version_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing profiling rules: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to execute profiling rules: {str(e)}")

@router.get("/cycles/{cycle_id}/reports/{report_id}/results")
async def get_profiling_results(
    cycle_id: int,
    report_id: int,
    job_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get profiling execution results"""
    
    # Get phase_id
    phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
    if not phase_id:
        return {
            "success": False,
            "results": [],
            "total_rules": 0,
            "executed_rules": 0,
            "completed_rules": 0,
            "failed_rules": 0,
            "message": "Data profiling phase not found"
        }
    
    # Get the latest version for this phase
    version_query = await db.execute(
        select(DataProfilingRuleVersion)
        .where(DataProfilingRuleVersion.phase_id == phase_id)
        .order_by(DataProfilingRuleVersion.version_number.desc())
        .limit(1)
    )
    version = version_query.scalar_one_or_none()
    
    if not version or not version.execution_job_id:
        return {
            "success": True,
            "results": [],
            "total_rules": 0,
            "executed_rules": 0,
            "completed_rules": 0,
            "failed_rules": 0,
            "message": "No profiling jobs have been executed for this cycle/report"
        }
    
    # Get execution results from job manager
    from app.core.background_jobs import job_manager
    job = job_manager.get_job(version.execution_job_id)
    
    if not job or job.get("status") != "completed":
        return {
            "success": True,
            "results": [],
            "total_rules": 0,
            "executed_rules": 0,
            "completed_rules": 0,
            "failed_rules": 0,
            "message": "Profiling execution is still in progress or failed",
            "job_status": job.get("status") if job else "not_found"
        }
    
    # Get the summary from job results
    summary = job.get("result", {}).get("summary", {})
    
    # Get execution results from database with attribute details
    # Only get the latest execution result per rule
    from app.models.data_profiling import ProfilingResult
    from app.models.report_attribute import ReportAttribute
    from sqlalchemy import func, distinct
    
    # First, get the latest execution time per rule
    latest_executions_subquery = (
        select(
            ProfilingResult.rule_id,
            func.max(ProfilingResult.executed_at).label('max_executed_at')
        )
        .where(ProfilingResult.phase_id == phase_id)
        .group_by(ProfilingResult.rule_id)
        .subquery()
    )
    
    # Then get the full results for only the latest executions
    results_query = await db.execute(
        select(ProfilingResult, ProfilingRule, ReportAttribute)
        .join(ProfilingRule, ProfilingRule.rule_id == ProfilingResult.rule_id)
        .join(ReportAttribute, ReportAttribute.id == ProfilingRule.attribute_id)
        .join(
            latest_executions_subquery,
            and_(
                ProfilingResult.rule_id == latest_executions_subquery.c.rule_id,
                ProfilingResult.executed_at == latest_executions_subquery.c.max_executed_at
            )
        )
        .where(ProfilingResult.phase_id == phase_id)
        .order_by(
            # Sort by attribute importance first
            ReportAttribute.is_primary_key.desc(),  # PK attributes first
            ReportAttribute.cde_flag.desc(),  # Then CDE attributes
            ReportAttribute.historical_issues_flag.desc(),  # Then attributes with issues
            ReportAttribute.line_item_number.nulls_last(),  # Then by line item number
            ProfilingRule.attribute_name,  # Then by attribute name (keeps rules for same attribute together)
            ProfilingRule.rule_name  # Finally by rule name within each attribute
        )
    )
    db_results = results_query.all()
    
    # Format results for display
    results = []
    for result, rule, attribute in db_results:
        results.append({
            "result_id": result.result_id,
            "rule_id": str(rule.rule_id),
            "rule_name": rule.rule_name,
            "rule_type": rule.rule_type,
            "rule_code": rule.rule_code,  # Include the actual rule logic
            "attribute_id": rule.attribute_id,
            "attribute_name": rule.attribute_name,
            "line_item_number": attribute.line_item_number,
            "is_primary_key": attribute.is_primary_key,
            "is_cde": attribute.cde_flag,
            "has_issues": attribute.historical_issues_flag,
            "status": "passed" if result.execution_status == "success" else "failed",
            "execution_status": result.execution_status,
            "records_processed": result.total_count or 0,
            "records_passed": result.passed_count or 0,
            "records_failed": result.failed_count or 0,
            "passed_count": result.passed_count or 0,
            "failed_count": result.failed_count or 0,
            "total_count": result.total_count or 0,
            "pass_rate": result.pass_rate or 0.0,
            "execution_time_ms": result.execution_time_ms or 0,
            "quality_scores": result.result_summary or {},
            "executed_at": result.executed_at.isoformat() if result.executed_at else None,
            "severity": result.severity,
            "has_anomaly": result.has_anomaly,
            "anomaly_description": result.anomaly_description,
            "error": result.result_details if result.execution_status == "failed" else None
        })
    
    # Calculate totals from actual results
    total_processed = sum(r.total_count or 0 for r, _, _ in db_results)
    successful_rules = sum(1 for r, _, _ in db_results if r.execution_status == "success")
    failed_rules = sum(1 for r, _, _ in db_results if r.execution_status == "failed")
    
    return {
        "success": True,
        "results": results,
        "total_rules": len(results),
        "executed_rules": len(results),
        "completed_rules": successful_rules,
        "failed_rules": failed_rules,
        "total_records_processed": total_processed,
        "message": "Profiling execution completed successfully",
        "execution_time": job.get("result", {}).get("execution_time_seconds", 0),
        "overall_quality_score": version.overall_quality_score if version else None
    }

@router.post("/cycles/{cycle_id}/reports/{report_id}/start")
async def start_data_profiling_phase_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Legacy endpoint to start data profiling phase using cycle_id and report_id.
    This creates the first version if none exist.
    """
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Call the phase-based start endpoint logic
        return await start_data_profiling_phase(phase_id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting data profiling phase (legacy): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start data profiling phase: {str(e)}")

@router.post("/cycles/{cycle_id}/reports/{report_id}/generate-rules")
async def generate_profiling_rules(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    service: DataProfilingService = Depends(get_data_profiling_service)
):
    """Generate profiling rules using LLM for all attributes"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        phase_id = await get_phase_id(service.db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Create or get version and start generation
        version = await service.create_initial_version(
            phase_id=phase_id,
            user_id=current_user.user_id
        )
        
        return {
            "success": True,
            "message": "Rule generation started in background",
            "version_id": str(version.version_id),
            "version_number": version.version_number,
            "job_id": version.generation_job_id  # This contains the background job ID
        }
    except Exception as e:
        logger.error(f"Error generating profiling rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/rules/{rule_id}/tester-decision")
async def update_tester_decision(
    rule_id: str,
    decision: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update tester decision for a rule"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get the rule
        rule = await db.get(ProfilingRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Update tester decision
        rule.tester_decision = decision
        rule.tester_notes = notes
        rule.tester_decided_by = current_user.user_id
        rule.tester_decided_at = datetime.utcnow()
        
        # Update status based on decision
        if decision.lower() in ['approved', 'approve']:
            rule.status = ProfilingRuleStatus.APPROVED
        elif decision.lower() in ['rejected', 'reject']:
            rule.status = ProfilingRuleStatus.REJECTED
        
        rule.updated_at = datetime.utcnow()
        rule.updated_by_id = current_user.user_id
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Rule {decision}",
            "rule_id": rule_id,
            "status": rule.status
        }
        
    except Exception as e:
        logger.error(f"Error updating tester decision: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/rules/{rule_id}/report-owner-decision")
async def update_report_owner_decision(
    rule_id: str,
    decision: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update report owner decision for a rule"""
    RoleChecker(report_owner_roles + management_roles)(current_user)
    
    try:
        # Get the rule
        rule = await db.get(ProfilingRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Update report owner decision
        rule.report_owner_decision = decision
        rule.report_owner_notes = notes
        rule.report_owner_decided_by = current_user.user_id
        rule.report_owner_decided_at = datetime.utcnow()
        
        # Status remains as submitted until tester processes feedback
        rule.status = ProfilingRuleStatus.SUBMITTED
        
        rule.updated_at = datetime.utcnow()
        rule.updated_by_id = current_user.user_id
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Report owner {decision} rule",
            "rule_id": rule_id,
            "status": rule.status
        }
        
    except Exception as e:
        logger.error(f"Error updating report owner decision: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/cycles/{cycle_id}/reports/{report_id}/rules/{rule_id}/report-owner-decision")
async def update_report_owner_decision_with_context(
    cycle_id: int,
    report_id: int,
    rule_id: str,
    decision_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update report owner decision for a rule with cycle/report context"""
    RoleChecker(report_owner_roles + management_roles)(current_user)
    
    try:
        # Get the rule
        rule = await db.get(ProfilingRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Verify the rule belongs to the correct cycle/report by checking version
        from app.models.data_profiling import DataProfilingRuleVersion
        
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .join(WorkflowPhase, DataProfilingRuleVersion.phase_id == WorkflowPhase.phase_id)
            .where(
                and_(
                    DataProfilingRuleVersion.version_id == rule.version_id,
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="Rule not found for this cycle/report")
        
        # Update report owner decision
        from app.models.data_profiling import Decision
        
        decision = decision_data.get('decision', '').upper()
        if decision not in ['APPROVED', 'REJECTED']:
            raise HTTPException(status_code=400, detail="Invalid decision. Must be 'approved' or 'rejected'")
        
        rule.report_owner_decision = Decision.APPROVED if decision == 'APPROVED' else Decision.REJECTED
        rule.report_owner_notes = decision_data.get('notes', '')
        rule.report_owner_decided_by_id = current_user.user_id
        rule.report_owner_decided_at = datetime.utcnow()
        
        # If rejected, add reason to notes
        if decision == 'REJECTED' and decision_data.get('reason'):
            if rule.report_owner_notes:
                rule.report_owner_notes = f"{decision_data.get('reason')}. {rule.report_owner_notes}"
            else:
                rule.report_owner_notes = decision_data.get('reason')
        
        rule.updated_at = datetime.utcnow()
        rule.updated_by_id = current_user.user_id
        
        await db.commit()
        await db.refresh(rule)
        
        return {
            "success": True,
            "message": f"Report owner {decision.lower()} rule",
            "rule_id": rule_id,
            "decision": decision.lower(),
            "status": rule.status.value if hasattr(rule.status, 'value') else rule.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report owner decision: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a profiling rule"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get the rule
        rule = await db.get(ProfilingRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Delete the rule
        await db.delete(rule)
        await db.commit()
        
        return {
            "success": True,
            "message": "Rule deleted successfully",
            "rule_id": rule_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting rule: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cycles/{cycle_id}/reports/{report_id}/complete")
async def complete_data_profiling_phase(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark data profiling phase as complete"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Update phase status
        from sqlalchemy import update
        
        phase_query = await db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_query.scalar_one()
        
        if phase.status == "completed":
            return {
                "success": True,
                "message": "Data profiling phase already completed",
                "phase_status": phase.status
            }
        
        phase.status = "completed"
        phase.completed_at = datetime.utcnow()
        phase.updated_at = datetime.utcnow()
        phase.updated_by_id = current_user.user_id
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Data profiling phase completed successfully",
            "phase_status": phase.status,
            "completed_at": phase.completed_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error completing data profiling phase: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# For getting assignments for report owner
@router.get("/cycles/{cycle_id}/reports/{report_id}/assigned-rules")
async def get_assigned_rules_for_approval(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get rules assigned to report owner for approval"""
    # This endpoint is for report owners to see their assigned rules
    RoleChecker(report_owner_roles + management_roles)(current_user)
    
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            return {"rules": [], "message": "No data profiling phase found"}
        
        # Get the latest version
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            return {"rules": [], "message": "No version found"}
        
        # Get rules that have been approved by tester
        # Join with planning attributes to get proper ordering
        from app.models.report_attribute import ReportAttribute
        from app.models.workflow import WorkflowPhase as WP
        
        # Get planning phase
        planning_phase_query = select(WP).where(
            WP.cycle_id == cycle_id,
            WP.report_id == report_id,
            WP.phase_name == "Planning"
        )
        planning_phase = await db.execute(planning_phase_query)
        planning_phase_obj = planning_phase.scalar_one_or_none()
        
        rules_query = select(ProfilingRule).where(
            ProfilingRule.version_id == version.version_id,
            ProfilingRule.tester_decision == Decision.APPROVED
        )
        
        if planning_phase_obj:
            # Join with planning attributes for ordering
            rules_query = rules_query.join(
                ReportAttribute,
                ProfilingRule.attribute_id == ReportAttribute.id
            ).order_by(
                ReportAttribute.is_primary_key.desc(),  # Primary keys first
                ReportAttribute.cde_flag.desc(),         # Then CDEs
                ReportAttribute.historical_issues_flag.desc(),  # Then attributes with issues
                ReportAttribute.line_item_number.asc().nulls_last(),  # Then by line item number
                ProfilingRule.rule_name  # Finally by rule name within each attribute
            )
        else:
            # Fallback ordering
            rules_query = rules_query.order_by(ProfilingRule.attribute_name, ProfilingRule.rule_name)
        
        rules_result = await db.execute(rules_query)
        rules = rules_result.scalars().all()
        
        return {
            "rules": [
                {
                    "rule_id": str(rule.rule_id),
                    "version_id": str(rule.version_id),
                    "attribute_id": rule.attribute_id,
                    "attribute_name": rule.attribute_name,
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "rule_description": rule.rule_description,
                    "rule_code": rule.rule_code,
                    "severity": rule.severity,
                    "status": rule.status,
                    "tester_decision": rule.tester_decision,
                    "tester_notes": rule.tester_notes,
                    "tester_decided_at": rule.tester_decided_at.isoformat() if rule.tester_decided_at else None,
                    "report_owner_decision": rule.report_owner_decision,
                    "report_owner_notes": rule.report_owner_notes,
                    "llm_rationale": rule.llm_rationale,
                    "regulatory_reference": rule.regulatory_reference
                }
                for rule in rules
            ],
            "total_rules": len(rules),
            "version_id": str(version.version_id),
            "version_number": version.version_number
        }
        
    except Exception as e:
        logger.error(f"Error getting assigned rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cycles/{cycle_id}/reports/{report_id}/workflow-status")
async def get_workflow_status(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow status for data profiling"""
    
    # Use Universal Metrics Service for consistent metrics
    from app.services.universal_metrics_service import get_universal_metrics_service, MetricsContext
    
    metrics_service = get_universal_metrics_service(db)
    metrics_context = MetricsContext(
        cycle_id=cycle_id,
        report_id=report_id,
        user_id=current_user.user_id,
        user_role=current_user.role,
        phase_name="Data Profiling"
    )
    
    # Get universal metrics
    universal_metrics = await metrics_service.get_metrics(metrics_context)
    
    # Get phase_id
    phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
    if not phase_id:
        return {
            "total_attributes": universal_metrics.total_attributes,
            "total_rules": universal_metrics.all_dq_rules,
            "approved_rules": universal_metrics.approved_dq_rules,
            "rejected_rules": 0,  # Calculate separately if needed
            "pending_rules": universal_metrics.all_dq_rules - universal_metrics.approved_dq_rules,
            "needs_revision_rules": 0,
            "completion_percentage": int(universal_metrics.dq_rules_approval_rate),
            "can_proceed_to_execution": False
        }
    
    # Get latest version
    version_query = await db.execute(
        select(DataProfilingRuleVersion)
        .where(DataProfilingRuleVersion.phase_id == phase_id)
        .order_by(DataProfilingRuleVersion.version_number.desc())
        .limit(1)
    )
    version = version_query.scalar_one_or_none()
    
    if not version:
        return {
            "total_attributes": 0,
            "total_rules": 0,
            "approved_rules": 0,
            "rejected_rules": 0,
            "pending_rules": 0,
            "needs_revision_rules": 0,
            "completion_percentage": 0,
            "can_proceed_to_execution": False
        }
    
    # Get rule counts by status
    status_counts_query = await db.execute(
        select(
            ProfilingRule.status,
            func.count(ProfilingRule.rule_id).label('count')
        )
        .where(ProfilingRule.version_id == version.version_id)
        .group_by(ProfilingRule.status)
    )
    status_counts = {row.status: row.count for row in status_counts_query}
    
    # Get total attributes count from rules
    if version:
        attributes_count_query = await db.execute(
            select(func.count(distinct(ProfilingRule.attribute_id)))
            .where(ProfilingRule.version_id == version.version_id)
        )
        total_attributes = attributes_count_query.scalar() or 0
    else:
        total_attributes = 0
    
    total_rules = sum(status_counts.values())
    approved_rules = status_counts.get(ProfilingRuleStatus.APPROVED, 0)
    rejected_rules = status_counts.get(ProfilingRuleStatus.REJECTED, 0)
    pending_rules = status_counts.get(ProfilingRuleStatus.PENDING, 0)
    submitted_rules = status_counts.get(ProfilingRuleStatus.SUBMITTED, 0)
    
    # Calculate completion percentage
    completion_percentage = 0
    if total_rules > 0:
        processed_rules = approved_rules + rejected_rules
        completion_percentage = int((processed_rules / total_rules) * 100)
    
    # Can proceed if all rules have been processed (no pending rules)
    can_proceed = pending_rules == 0 and total_rules > 0
    
    # Calculate rejected rules from the status counts
    rejected_rules_count = status_counts.get(ProfilingRuleStatus.REJECTED, 0)
    
    # For backwards compatibility, maintain the same response structure
    # but use universal metrics where applicable
    return {
        "total_attributes": universal_metrics.total_attributes,  # From universal metrics
        "total_rules": universal_metrics.all_dq_rules,  # From universal metrics
        "approved_rules": universal_metrics.approved_dq_rules,  # From universal metrics
        "rejected_rules": rejected_rules_count,  # From local calculation
        "pending_rules": universal_metrics.all_dq_rules - universal_metrics.approved_dq_rules - rejected_rules_count,
        "needs_revision_rules": 0,  # Not used in data profiling
        "completion_percentage": int(universal_metrics.dq_rules_approval_rate),  # From universal metrics
        "can_proceed_to_execution": can_proceed
    }

@router.post("/cycles/{cycle_id}/reports/{report_id}/update-workflow-status")
async def update_workflow_status(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update workflow metadata for tracking progress"""
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Update workflow metadata
        from sqlalchemy import update
        
        phase_query = await db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_query.scalar_one()
        
        # Update workflow metadata
        if not phase.workflow_metadata:
            phase.workflow_metadata = {}
        
        # Update specific workflow step status
        current_step = request_data.get("current_step")
        next_step = request_data.get("next_step")
        status = request_data.get("status", "completed")
        
        if current_step:
            phase.workflow_metadata[f"{current_step}_status"] = status
            phase.workflow_metadata[f"{current_step}_completed_at"] = datetime.utcnow().isoformat()
            
        if next_step:
            phase.workflow_metadata["current_workflow_step"] = next_step
            phase.workflow_metadata["step_updated_at"] = datetime.utcnow().isoformat()
            
            await db.execute(
                update(WorkflowPhase)
                .where(WorkflowPhase.phase_id == phase_id)
                .values(workflow_metadata=phase.workflow_metadata)
            )
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Workflow status updated",
            "current_step": next_step or current_step
        }
        
    except Exception as e:
        logger.error(f"Error updating workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cycles/{cycle_id}/reports/{report_id}/send-to-report-owner")
async def send_to_report_owner(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send approved rules to report owner for review"""
    # Check permissions - only testers can send to report owner
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Get latest version
        from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule, Decision
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="No data profiling version found")
        
        # Check if there are tester-approved rules
        approved_count_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                ProfilingRule.version_id == version.version_id,
                ProfilingRule.tester_decision == Decision.APPROVED
            )
        )
        approved_count = approved_count_query.scalar() or 0
        
        if approved_count == 0:
            raise HTTPException(
                status_code=400, 
                detail="Cannot send to Report Owner. No rules have been approved by the tester."
            )
        
        # Check for pending rules
        pending_count_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                ProfilingRule.version_id == version.version_id,
                ProfilingRule.tester_decision.is_(None)
            )
        )
        pending_count = pending_count_query.scalar() or 0
        
        if pending_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot send to Report Owner. {pending_count} rules are still pending tester decision."
            )
        
        # Update all approved rules to "submitted" status
        await db.execute(
            update(ProfilingRule)
            .where(
                ProfilingRule.version_id == version.version_id,
                ProfilingRule.tester_decision == Decision.APPROVED
            )
            .values(
                status=ProfilingRuleStatus.SUBMITTED,
                updated_at=datetime.utcnow(),
                updated_by_id=current_user.user_id
            )
        )
        
        # Create universal assignment for report owner
        from app.services.universal_assignment_service import UniversalAssignmentService
        assignment_service = UniversalAssignmentService(db)
        
        # Get report owner for this report
        from app.models.workflow import WorkflowPhase
        phase_query = await db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_query.scalar_one()
        
        # Get report to find report owner
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        report_query = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = report_query.scalar_one_or_none()
        if not report or not report.report_owner_id:
            raise HTTPException(status_code=404, detail="Report or report owner not found")
        
        # Get cycle name
        cycle_query = await db.execute(
            select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        )
        cycle = cycle_query.scalar_one_or_none()
        
        # Create assignment
        assignment = await assignment_service.create_assignment(
            assignment_type="Rule Approval",  # Use the valid enum value
            from_role=current_user.role,
            to_role="Report Owner",
            from_user_id=current_user.user_id,
            to_user_id=report.report_owner_id,
            title="Review Data Profiling Rules",
            description=f"Review and approve {approved_count} data profiling rules that have been approved by the tester for cycle {cycle_id}, report {report_id}.",
            task_instructions="Please review the data profiling rules that have been approved by the tester. Approve, reject, or request changes as needed.",
            context_type="Report",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "report_name": report.report_name,
                "cycle_name": cycle.cycle_name if cycle else None,
                "phase": "data_profiling",  # Add the phase field that frontend expects
                "phase_name": "Data Profiling",
                "phase_id": phase_id,
                "version_id": str(version.version_id),
                "approved_rules_count": approved_count,
                "workflow_step": "tester_approved_rules_for_report_owner_review"
            },
            priority="High",
            due_date=datetime.utcnow() + timedelta(days=7),
            requires_approval=False
        )
        
        await db.commit()
        
        logger.info(f"Sent {approved_count} rules to report owner for review, assignment {assignment.assignment_id}")
        
        return {
            "success": True,
            "message": f"Successfully sent {approved_count} approved rules to Report Owner for review",
            "assignment_id": assignment.assignment_id,
            "approved_rules_count": approved_count,
            "version_id": str(version.version_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending to report owner: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cycles/{cycle_id}/reports/{report_id}/mark-execution-complete")
async def mark_execution_complete(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually mark execution as complete (for testing/demo purposes)"""
    RoleChecker(tester_roles + management_roles)(current_user)
    
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # For now, just return success
        # In a real implementation, this would update execution status
        return {
            "success": True,
            "message": "Profiling execution marked as complete",
            "results_count": 381  # Mock number matching the rules count
        }
        
    except Exception as e:
        logger.error(f"Error marking execution complete: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cycles/{cycle_id}/reports/{report_id}/resubmit-after-feedback")
async def resubmit_after_feedback(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new version from report owner feedback (Make Changes workflow).
    This preserves report owner decisions while allowing tester to make changes.
    """
    # Check permissions - only testers can resubmit
    RoleChecker(tester_roles)(current_user)
    
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Get latest version
        from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule, Decision, VersionStatus
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        current_version = version_query.scalar_one_or_none()
        
        if not current_version:
            raise HTTPException(status_code=404, detail="No data profiling version found")
        
        # Create new version
        new_version_number = current_version.version_number + 1
        new_version = DataProfilingRuleVersion(
            phase_id=phase_id,
            version_number=new_version_number,
            version_status=VersionStatus.DRAFT,
            parent_version_id=current_version.version_id,
            created_by_id=current_user.user_id,
            created_at=datetime.utcnow(),
            updated_by_id=current_user.user_id,
            updated_at=datetime.utcnow()
        )
        db.add(new_version)
        await db.flush()
        
        # Copy rules from the current version to the new version
        # Only copy rules that were approved by tester (as these are the ones that need revision based on RO feedback)
        rules_query = await db.execute(
            select(ProfilingRule)
            .where(
                ProfilingRule.version_id == current_version.version_id,
                ProfilingRule.tester_decision == Decision.APPROVED
            )
        )
        rules_to_copy = rules_query.scalars().all()
        
        copied_count = 0
        approved_count = 0
        
        for rule in rules_to_copy:
            # Create new rule in the new version
            new_rule = ProfilingRule(
                version_id=new_version.version_id,
                phase_id=phase_id,  # Required field
                attribute_id=rule.attribute_id,
                attribute_name=rule.attribute_name,  # Required field
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                rule_code=rule.rule_code,
                rule_description=rule.rule_description,
                rule_parameters=rule.rule_parameters,
                severity=rule.severity,  # Required field
                status=rule.status,  # Required field
                # LLM metadata
                llm_provider=rule.llm_provider,
                llm_rationale=rule.llm_rationale,
                llm_confidence_score=rule.llm_confidence_score,
                regulatory_reference=rule.regulatory_reference,
                # Rule configuration
                is_executable=rule.is_executable,
                execution_order=rule.execution_order,
                # Preserve tester decisions
                tester_decision=rule.tester_decision,
                tester_notes=rule.tester_notes,
                tester_decided_by=rule.tester_decided_by,
                tester_decided_at=rule.tester_decided_at,
                # PRESERVE report owner decisions (this is the "Make Changes" workflow)
                # They will be cleared when submitted for approval
                report_owner_decision=rule.report_owner_decision,
                report_owner_notes=rule.report_owner_notes,
                report_owner_decided_by=rule.report_owner_decided_by,
                report_owner_decided_at=rule.report_owner_decided_at,
                created_by_id=current_user.user_id,
                updated_by_id=current_user.user_id
            )
            db.add(new_rule)
            copied_count += 1
            if rule.tester_decision == Decision.APPROVED:
                approved_count += 1
        
        # Update the new version's rule counts
        new_version.total_rules = copied_count
        new_version.approved_rules = approved_count
        
        await db.flush()
        
        # Now create the assignment for report owner review (similar to send-to-report-owner)
        # Create universal assignment for report owner
        from app.services.universal_assignment_service import UniversalAssignmentService
        assignment_service = UniversalAssignmentService(db)
        
        # Get report owner for this report
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        report_query = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = report_query.scalar_one_or_none()
        if not report or not report.report_owner_id:
            raise HTTPException(status_code=404, detail="Report or report owner not found")
        
        # Get cycle name
        cycle_query = await db.execute(
            select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        )
        cycle = cycle_query.scalar_one_or_none()
        
        # Create assignment
        assignment = await assignment_service.create_assignment(
            assignment_type="Rule Approval",
            from_role=current_user.role,
            to_role="Report Owner",
            from_user_id=current_user.user_id,
            to_user_id=report.report_owner_id,
            title="Review Updated Data Profiling Rules",
            description=f"Review updated data profiling rules (Version {new_version_number}) that have been revised based on your feedback for cycle {cycle_id}, report {report_id}.",
            task_instructions="The tester has updated the rules based on your previous feedback. Please review the revised rules and approve or provide additional feedback.",
            context_type="Report",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "report_name": report.report_name,
                "cycle_name": cycle.cycle_name if cycle else None,
                "phase": "data_profiling",
                "phase_name": "Data Profiling",
                "phase_id": phase_id,
                "version_id": str(new_version.version_id),
                "version_number": new_version_number,
                "approved_rules_count": approved_count,
                "workflow_step": "tester_approved_rules_for_report_owner_review",
                "is_resubmission": True
            },
            priority="High",
            due_date=datetime.utcnow() + timedelta(days=5),  # Shorter deadline for resubmission
            requires_approval=False
        )
        
        # Update the previous version status to superseded
        current_version.version_status = VersionStatus.SUPERSEDED
        current_version.updated_at = datetime.utcnow()
        current_version.updated_by_id = current_user.user_id
        
        await db.commit()
        
        logger.info(f"Created new version {new_version_number} for resubmission with assignment {assignment.assignment_id}")
        
        return {
            "success": True,
            "message": f"Created new version {new_version_number} for resubmission after report owner feedback",
            "version_id": str(new_version.version_id),
            "version_number": new_version_number,
            "assignment": {
                "assignment_id": assignment.assignment_id,
                "to_user_id": assignment.to_user_id,
                "status": assignment.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating resubmission version with assignment: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cycles/{cycle_id}/reports/{report_id}/check-and-approve-version")
async def check_and_approve_version(
    cycle_id: int,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if all tester and report owner decisions match.
    If they match, automatically approve the version.
    """
    # Check permissions - testers and report owners can trigger this check
    RoleChecker(tester_roles + report_owner_roles + management_roles)(current_user)
    
    try:
        # Get phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Get latest version
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            raise HTTPException(status_code=404, detail="No data profiling version found")
        
        # Get all rules for this version
        rules_query = await db.execute(
            select(ProfilingRule)
            .where(ProfilingRule.version_id == version.version_id)
        )
        rules = rules_query.scalars().all()
        
        if not rules:
            raise HTTPException(status_code=400, detail="No rules found in version")
        
        # Check if all rules have both tester and report owner decisions
        rules_without_decisions = []
        mismatched_rules = []
        
        for rule in rules:
            # Check if both decisions exist
            if not rule.tester_decision or not rule.report_owner_decision:
                rules_without_decisions.append({
                    "rule_id": str(rule.rule_id),
                    "rule_name": rule.rule_name,
                    "tester_decision": rule.tester_decision,
                    "report_owner_decision": rule.report_owner_decision
                })
                continue
            
            # Check if decisions match (both approved or both rejected)
            tester_approved = rule.tester_decision.lower() in ['approved', 'approve']
            ro_approved = rule.report_owner_decision.lower() in ['approved', 'approve']
            
            if tester_approved != ro_approved:
                mismatched_rules.append({
                    "rule_id": str(rule.rule_id),
                    "rule_name": rule.rule_name,
                    "attribute_name": rule.attribute_name,
                    "tester_decision": rule.tester_decision,
                    "report_owner_decision": rule.report_owner_decision
                })
        
        # If there are any issues, return them
        if rules_without_decisions or mismatched_rules:
            return {
                "version_approved": False,
                "version_id": str(version.version_id),
                "version_number": version.version_number,
                "current_status": version.version_status,
                "rules_without_decisions": len(rules_without_decisions),
                "mismatches": len(mismatched_rules),
                "mismatched_rules": mismatched_rules[:10],  # Return first 10 mismatches
                "message": f"Cannot approve version: {len(rules_without_decisions)} rules without decisions, {len(mismatched_rules)} mismatched decisions"
            }
        
        # All decisions match! Approve the version
        version.version_status = VersionStatus.APPROVED
        version.approved_by_id = current_user.user_id
        version.approved_at = datetime.utcnow()
        version.updated_by_id = current_user.user_id
        version.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Version {version.version_id} automatically approved - all decisions match")
        
        return {
            "version_approved": True,
            "version_id": str(version.version_id),
            "version_number": version.version_number,
            "current_status": version.version_status,
            "total_rules": len(rules),
            "message": f"Version {version.version_number} approved! All {len(rules)} rules have matching tester and report owner decisions."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking and approving version: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a data profiling job"""
    try:
        from app.core.background_jobs import job_manager
        
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return {
            "job_id": job_id,
            "status": job.get("status", "unknown"),
            "progress": job.get("progress_percentage", 0),
            "current_step": job.get("current_step", ""),
            "message": job.get("message", ""),
            "result": job.get("result"),
            "error": job.get("error"),
            "metadata": job.get("metadata", {}),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at")
        }
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/attributes/{attribute_id}/dq-results")
async def get_attribute_dq_results(
    attribute_id: str,
    cycle_id: int = Query(..., description="Cycle ID"),
    report_id: int = Query(..., description="Report ID"),
    phase_name: str = Query("Data Profiling", description="Phase name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed DQ results showing latest results for each rule for an attribute in a given phase"""
    try:
        # Get the phase_id
        phase_id = await get_phase_id(db, cycle_id, report_id, phase_name)
        if not phase_id:
            raise HTTPException(
                status_code=404, 
                detail=f"Phase '{phase_name}' not found for cycle {cycle_id} and report {report_id}"
            )
        
        logger.info(f"Getting DQ results for attribute {attribute_id} in phase {phase_id}")
        
        # Convert UUID attribute_id to integer if needed
        # Check if attribute_id is a UUID string
        import uuid
        planning_attribute_id = None
        try:
            # Try to parse as UUID
            uuid.UUID(attribute_id)
            # It's a UUID, need to get the planning_attribute_id
            from app.models.scoping import ScopingAttribute
            scope_attr_query = await db.execute(
                select(ScopingAttribute.planning_attribute_id)
                .where(ScopingAttribute.attribute_id == attribute_id)
            )
            planning_attr_result = scope_attr_query.scalar_one_or_none()
            if planning_attr_result:
                planning_attribute_id = planning_attr_result
                logger.info(f"Converted UUID {attribute_id} to planning_attribute_id {planning_attribute_id}")
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Attribute with ID {attribute_id} not found in scoping attributes"
                )
        except ValueError:
            # Not a UUID, assume it's already an integer
            planning_attribute_id = int(attribute_id)
        
        # Use the integer attribute ID for querying profiling results
        query_attribute_id = planning_attribute_id
        
        # Get latest execution for each rule using window function
        latest_executions_cte = text("""
            WITH latest_executions AS (
                SELECT 
                    pr.result_id,
                    pr.rule_id,
                    pr.attribute_id,
                    pr.execution_status,
                    pr.executed_at,
                    pr.passed_count,
                    pr.failed_count,
                    pr.total_count,
                    pr.pass_rate,
                    pr.result_summary,
                    pr.failed_records,
                    pr.result_details,
                    pr.quality_impact,
                    pr.severity,
                    pr.execution_time_ms,
                    r.rule_name,
                    r.rule_description,
                    r.rule_type,
                    r.severity as criticality,
                    r.rule_code,
                    r.llm_rationale,
                    r.regulatory_reference,
                    ROW_NUMBER() OVER (PARTITION BY pr.rule_id ORDER BY pr.executed_at DESC) as rn
                FROM cycle_report_data_profiling_results pr
                JOIN cycle_report_data_profiling_rules r ON pr.rule_id = r.rule_id
                WHERE pr.phase_id = :phase_id 
                AND pr.attribute_id = :attribute_id
            )
            SELECT 
                result_id,
                rule_id,
                rule_name,
                rule_description,
                rule_type,
                criticality,
                rule_code,
                llm_rationale,
                regulatory_reference,
                execution_status,
                executed_at,
                passed_count,
                failed_count,
                total_count,
                pass_rate,
                result_summary,
                failed_records,
                result_details,
                quality_impact,
                severity,
                execution_time_ms
            FROM latest_executions
            WHERE rn = 1
            ORDER BY executed_at DESC
        """)
        
        result = await db.execute(
            latest_executions_cte,
            {"phase_id": phase_id, "attribute_id": query_attribute_id}
        )
        
        rows = result.fetchall()
        
        # Format the results
        dq_results = []
        total_passed = 0
        total_failed = 0
        total_count = 0
        
        for row in rows:
            # Extract failed records sample
            failed_records_sample = []
            if row.failed_records:
                # Take first 5 failed records as sample
                failed_records_sample = row.failed_records[:5] if isinstance(row.failed_records, list) else []
            
            dq_results.append({
                "result_id": row.result_id,
                "rule_id": str(row.rule_id),
                "rule_name": row.rule_name,
                "rule_description": row.rule_description,
                "rule_type": row.rule_type,
                "criticality": row.criticality,
                "rule_code": row.rule_code,
                "llm_rationale": row.llm_rationale,
                "regulatory_reference": row.regulatory_reference,
                "execution_status": row.execution_status,
                "executed_at": row.executed_at.isoformat() if row.executed_at else None,
                "passed_count": row.passed_count or 0,
                "failed_count": row.failed_count or 0,
                "total_count": row.total_count or 0,
                "pass_rate": round(row.pass_rate, 2) if row.pass_rate is not None else 0,
                "result_summary": row.result_summary,
                "failed_records_sample": failed_records_sample,
                "result_details": row.result_details,
                "quality_impact": row.quality_impact,
                "severity": row.severity,
                "execution_time_ms": row.execution_time_ms
            })
            
            # Accumulate totals
            if row.passed_count is not None:
                total_passed += row.passed_count
            if row.failed_count is not None:
                total_failed += row.failed_count
            if row.total_count is not None:
                total_count += row.total_count
        
        # Calculate composite score
        composite_score = 0
        if total_count > 0:
            composite_score = round((total_passed / total_count) * 100, 2)
        
        # Get attribute details
        from app.models.report_attribute import ReportAttribute
        attr_query = await db.execute(
            select(ReportAttribute).where(ReportAttribute.id == query_attribute_id)
        )
        attribute = attr_query.scalar_one_or_none()
        
        response = {
            "attribute_id": attribute_id,
            "attribute_name": attribute.attribute_name if attribute else "Unknown",
            "is_cde": attribute.cde_flag if attribute else False,
            "mdrm": attribute.mdrm if attribute else None,
            "phase_id": phase_id,
            "phase_name": phase_name,
            "total_rules": len(dq_results),
            "rules_executed": len(dq_results),
            "composite_score": composite_score,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_records": total_count,
            "results": dq_results,
            "summary": {
                "critical_rules": len([r for r in dq_results if r["criticality"] == "critical"]),
                "high_rules": len([r for r in dq_results if r["criticality"] == "high"]),
                "medium_rules": len([r for r in dq_results if r["criticality"] == "medium"]),
                "low_rules": len([r for r in dq_results if r["criticality"] == "low"]),
                "failed_critical": len([r for r in dq_results if r["criticality"] == "critical" and r["pass_rate"] < 100]),
                "failed_high": len([r for r in dq_results if r["criticality"] == "high" and r["pass_rate"] < 100])
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attribute DQ results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get DQ results: {str(e)}")


# Version Management Endpoints - Following Scoping Patterns

from pydantic import BaseModel
from fastapi import Body

class VersionSubmissionCreate(BaseModel):
    submission_notes: Optional[str] = None


class VersionApprovalCreate(BaseModel):
    approved: bool
    approval_notes: Optional[str] = None


@router.post("/cycles/{cycle_id}/reports/{report_id}/versions")
async def create_data_profiling_version(
    cycle_id: int,
    report_id: int,
    carry_forward_all: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new data profiling version"""
    try:
        # Check user role
        if current_user.role not in tester_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Testers can create new versions"
            )
        
        # Get phase
        phase_id = await get_phase_id(db, cycle_id, report_id, "Data Profiling")
        if not phase_id:
            raise HTTPException(status_code=404, detail="Data Profiling phase not found")
        
        # Get current version
        version_query = await db.execute(
            select(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == phase_id)
            .order_by(DataProfilingRuleVersion.version_number.desc())
            .limit(1)
        )
        current_version = version_query.scalar_one_or_none()
        
        # Check if current version is draft
        if current_version and current_version.version_status == VersionStatus.DRAFT:
            return {
                "success": True,
                "message": "Using existing draft version",
                "version": {
                    "version_id": str(current_version.version_id),
                    "version_number": current_version.version_number,
                    "version_status": current_version.version_status,
                    "created_at": current_version.created_at.isoformat(),
                    "total_rules": current_version.total_rules
                }
            }
        
        # Create new version
        new_version_number = (current_version.version_number + 1) if current_version else 1
        new_version = DataProfilingRuleVersion(
            phase_id=phase_id,
            version_number=new_version_number,
            version_status=VersionStatus.DRAFT,
            parent_version_id=current_version.version_id if current_version else None,
            total_rules=0,
            approved_rules=0,
            rejected_rules=0,
            created_by_id=current_user.user_id,
            created_at=datetime.utcnow(),
            updated_by_id=current_user.user_id,
            updated_at=datetime.utcnow()
        )
        db.add(new_version)
        await db.flush()
        
        # If carry_forward_all and we have a previous version, copy rules
        if carry_forward_all and current_version:
            rules_query = await db.execute(
                select(ProfilingRule)
                .where(ProfilingRule.version_id == current_version.version_id)
            )
            rules = rules_query.scalars().all()
            
            for rule in rules:
                new_rule = ProfilingRule(
                    version_id=new_version.version_id,
                    phase_id=phase_id,
                    attribute_id=rule.attribute_id,
                    attribute_name=rule.attribute_name,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    rule_code=rule.rule_code,
                    rule_description=rule.rule_description,
                    rule_parameters=rule.rule_parameters,
                    severity=rule.severity,
                    status=ProfilingRuleStatus.PENDING,
                    llm_provider=rule.llm_provider,
                    llm_rationale=rule.llm_rationale,
                    llm_confidence_score=rule.llm_confidence_score,
                    regulatory_reference=rule.regulatory_reference,
                    is_executable=rule.is_executable,
                    execution_order=rule.execution_order,
                    tester_decision=rule.tester_decision,
                    tester_decided_by=rule.tester_decided_by,
                    tester_decided_at=rule.tester_decided_at,
                    tester_notes=rule.tester_notes,
                    report_owner_decision=rule.report_owner_decision if carry_forward_all else None,
                    report_owner_decided_by=rule.report_owner_decided_by if carry_forward_all else None,
                    report_owner_decided_at=rule.report_owner_decided_at if carry_forward_all else None,
                    report_owner_notes=rule.report_owner_notes if carry_forward_all else None,
                    created_by_id=current_user.user_id,
                    created_at=datetime.utcnow(),
                    updated_by_id=current_user.user_id,
                    updated_at=datetime.utcnow()
                )
                db.add(new_rule)
            
            new_version.total_rules = len(rules)
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Created new version {new_version_number}",
            "version": {
                "version_id": str(new_version.version_id),
                "version_number": new_version_number,
                "version_status": new_version.version_status,
                "created_at": new_version.created_at.isoformat(),
                "created_by": current_user.user_id,
                "created_by_name": f"{current_user.first_name} {current_user.last_name}",
                "total_rules": new_version.total_rules,
                "approved_rules": new_version.approved_rules,
                "rejected_rules": new_version.rejected_rules
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data profiling version: {str(e)}")
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
    """Submit data profiling version for report owner approval"""
    try:
        # Verify user is tester
        if current_user.role not in tester_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Testers can submit versions for approval"
            )
        
        # Convert string version_id to UUID
        try:
            version_uuid = uuid.UUID(version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid version ID format"
            )
        
        # Get the version
        version_query = await db.execute(
            select(DataProfilingRuleVersion).where(
                DataProfilingRuleVersion.version_id == version_uuid
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Check if version is in draft status
        if version.version_status != VersionStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft versions can be submitted for approval"
            )
        
        # Get rules for this version
        rules_query = await db.execute(
            select(func.count(ProfilingRule.rule_id)).where(
                ProfilingRule.version_id == version_uuid
            )
        )
        rule_count = rules_query.scalar()
        
        if rule_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit version with no rules"
            )
        
        # Reset report owner decisions on all rules
        await db.execute(
            update(ProfilingRule)
            .where(ProfilingRule.version_id == version_uuid)
            .values(
                report_owner_decision=None,
                report_owner_notes=None,
                report_owner_decided_by=None,
                report_owner_decided_at=None
            )
        )
        
        # Update version status
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_at = datetime.utcnow()
        version.submitted_by_id = current_user.user_id
        version.submission_notes = submission_data.submission_notes
        version.updated_at = datetime.utcnow()
        version.updated_by_id = current_user.user_id
        
        await db.commit()
        await db.refresh(version)
        
        # Mark version as approved by tester
        try:
            from app.services.version_tester_approval import VersionTesterApprovalService
            await VersionTesterApprovalService.mark_data_profiling_approved_by_tester(
                db, str(version.version_id), current_user.user_id
            )
        except Exception as e:
            logger.error(f"Failed to mark version as approved by tester: {str(e)}")
            # Don't fail the submission if this fails
        
        # Create Universal Assignment for report owner review
        try:
            from app.services.universal_assignment_service import UniversalAssignmentService
            assignment_service = UniversalAssignmentService(db)
            
            # Get report info
            from app.models.report import Report
            from app.models.workflow import WorkflowPhase
            
            phase_query = await db.execute(
                select(WorkflowPhase).where(WorkflowPhase.phase_id == version.phase_id)
            )
            phase = phase_query.scalar_one_or_none()
            
            if phase:
                report_query = await db.execute(
                    select(Report).where(Report.report_id == phase.report_id)
                )
                report = report_query.scalar_one_or_none()
                
                if report:
                    await assignment_service.create_assignment(
                        assignment_type="Rule Approval",
                        from_role=current_user.role,
                        to_role="Report Owner",
                        from_user_id=current_user.user_id,
                        to_user_id=None,  # Will be determined by role
                        title=f"Review Data Profiling Rules for {report.report_name}",
                        description=f"Please review and approve data profiling rules version {version.version_number}",
                        context_type="Report",
                        context_data={
                            "cycle_id": phase.cycle_id,
                            "report_id": phase.report_id,
                            "phase_id": phase.phase_id,  # Add phase_id for version metadata updates
                            "phase_name": "Data Profiling",
                            "version_id": str(version.version_id),
                            "version_number": version.version_number,
                            "rule_count": rule_count,
                            "submission_notes": submission_data.submission_notes,
                            "report_name": report.report_name,
                            "lob": report.lob.lob_name if report.lob else "Unknown"
                        },
                        task_instructions=f"Review the {rule_count} data profiling rules in version {version.version_number} and provide your approval decision.",
                        priority="High",
                        due_date=None,
                        requires_approval=False,
                        approval_role=None,
                        assignment_metadata={
                            "version_id": str(version.version_id),
                            "version_number": version.version_number
                        }
                    )
                    logger.info(f"Created Universal Assignment for data profiling review")
        except Exception as e:
            logger.error(f"Failed to create Universal Assignment: {str(e)}")
            # Don't fail the submission if assignment creation fails
        
        logger.info(f"Submitted version {version_id} for approval")
        
        return {
            "success": True,
            "message": f"Version {version.version_number} submitted for approval",
            "version": {
                "version_id": str(version.version_id),
                "version_number": version.version_number,
                "version_status": version.version_status.value,
                "submitted_at": version.submitted_at.isoformat() if version.submitted_at else None,
                "submission_notes": version.submission_notes
            }
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
    """Approve or reject data profiling version"""
    try:
        # Verify user is report owner
        if current_user.role not in report_owner_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Report Owners can approve versions"
            )
        
        # Convert string version_id to UUID
        try:
            version_uuid = uuid.UUID(version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid version ID format"
            )
        
        # Get the version
        version_query = await db.execute(
            select(DataProfilingRuleVersion).where(
                DataProfilingRuleVersion.version_id == version_uuid
            )
        )
        version = version_query.scalar_one_or_none()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Check if version is pending approval
        if version.version_status != VersionStatus.PENDING_APPROVAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending approval versions can be approved"
            )
        
        # Update version status
        if approval_data.approved:
            version.version_status = VersionStatus.APPROVED
            
            # Mark all previous approved versions as superseded
            await db.execute(
                update(DataProfilingRuleVersion)
                .where(
                    and_(
                        DataProfilingRuleVersion.phase_id == version.phase_id,
                        DataProfilingRuleVersion.version_id != version_uuid,
                        DataProfilingRuleVersion.version_status == VersionStatus.APPROVED
                    )
                )
                .values(
                    version_status=VersionStatus.SUPERSEDED,
                    updated_at=datetime.utcnow(),
                    updated_by_id=current_user.user_id
                )
            )
            
            # Update phase status to complete
            phase_query = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.phase_id == version.phase_id
                )
            )
            phase = phase_query.scalar_one_or_none()
            if phase:
                phase.status = "Complete"
                phase.state = "Complete"
                phase.actual_end_date = datetime.utcnow()
                phase.updated_at = datetime.utcnow()
                phase.updated_by_id = current_user.user_id
        else:
            version.version_status = VersionStatus.REJECTED
        
        version.approved_at = datetime.utcnow()
        version.approved_by_id = current_user.user_id
        version.approval_notes = approval_data.approval_notes
        version.updated_at = datetime.utcnow()
        version.updated_by_id = current_user.user_id
        
        await db.commit()
        await db.refresh(version)
        
        # Mark Universal Assignment as complete regardless of approval/rejection
        try:
            from app.services.universal_assignment_service import UniversalAssignmentService
            assignment_service = UniversalAssignmentService(db)
            
            # Find and complete the assignment
            assignments = await assignment_service.get_assignments_by_filters(
                assignment_type="Rule Approval",
                to_user_id=current_user.user_id,
                status_filter=["Assigned", "Acknowledged", "In Progress"]
            )
            
            # Find the assignment for this specific version
            for assignment in assignments:
                # Check if this assignment is for the current version
                context_data = assignment.context_data or {}
                if (context_data.get("version_id") == str(version.version_id) and 
                    assignment.status not in ["Completed", "Cancelled"]):
                    await assignment_service.complete_assignment(
                        assignment_id=str(assignment.assignment_id),
                        user_id=current_user.user_id,
                        completion_notes=f"Version {'approved' if approval_data.approved else 'rejected'}: {approval_data.approval_notes or 'Decision by Report Owner'}",
                        completion_data={
                            "version_approved": approval_data.approved,
                            "approval_notes": approval_data.approval_notes,
                            "changes_requested": not approval_data.approved
                        }
                    )
                    logger.info(f"Completed assignment {assignment.assignment_id}")
        except Exception as e:
            logger.error(f"Failed to update Universal Assignment: {str(e)}")
            # Don't fail the approval if assignment update fails
        
        logger.info(f"Version {version_id} {'approved' if approval_data.approved else 'rejected'}")
        
        return {
            "success": True,
            "message": f"Version {version.version_number} {'approved' if approval_data.approved else 'rejected'}",
            "version": {
                "version_id": str(version.version_id),
                "version_number": version.version_number,
                "version_status": version.version_status.value,
                "approved_at": version.approved_at.isoformat() if version.approved_at else None,
                "approval_notes": version.approval_notes
            }
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