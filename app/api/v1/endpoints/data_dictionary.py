"""
API endpoints for Regulatory Data Dictionary management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.permissions import require_permission
from app.models.data_dictionary import RegulatoryDataDictionary
from app.models.report_attribute import ReportAttribute
from app.models.user import User
from app.schemas.data_dictionary import (
    RegulatoryDataDictionaryResponse,
    RegulatoryDataDictionaryListResponse, 
    DataDictionaryFilter,
    DataDictionaryImportRequest,
    DataDictionaryImportResponse
)
from app.utils.data_dictionary_loader import load_fr_y14m_data_dictionary
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=RegulatoryDataDictionaryListResponse)
@require_permission("planning", "execute")
async def get_data_dictionary(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    report_name: Optional[str] = Query(None, description="Filter by report name"),
    schedule_name: Optional[str] = Query(None, description="Filter by schedule name"),
    line_item_name: Optional[str] = Query(None, description="Filter by line item name (contains)"),
    mandatory_or_optional: Optional[str] = Query(None, description="Filter by mandatory/optional"),
    static_or_dynamic: Optional[str] = Query(None, description="Filter by static/dynamic"),
    search: Optional[str] = Query(None, description="General search term"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get regulatory data dictionary with filtering and pagination"""
    
    try:
        # Build query
        query = select(RegulatoryDataDictionary).filter(
            RegulatoryDataDictionary.is_active == True
        )
        
        # Apply filters
        if report_name:
            query = query.filter(RegulatoryDataDictionary.report_name.ilike(f"%{report_name}%"))
        
        if schedule_name:
            query = query.filter(RegulatoryDataDictionary.schedule_name.ilike(f"%{schedule_name}%"))
        
        if line_item_name:
            query = query.filter(RegulatoryDataDictionary.line_item_name.ilike(f"%{line_item_name}%"))
        
        if mandatory_or_optional:
            query = query.filter(RegulatoryDataDictionary.mandatory_or_optional == mandatory_or_optional)
        
        if static_or_dynamic:
            query = query.filter(RegulatoryDataDictionary.static_or_dynamic == static_or_dynamic)
        
        # General search across multiple fields
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    RegulatoryDataDictionary.line_item_name.ilike(search_term),
                    RegulatoryDataDictionary.technical_line_item_name.ilike(search_term),
                    RegulatoryDataDictionary.description.ilike(search_term),
                    RegulatoryDataDictionary.mdrm.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * per_page
        items_query = query.offset(offset).limit(per_page)
        items_result = await db.execute(items_query)
        items = items_result.scalars().all()
        
        return RegulatoryDataDictionaryListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error retrieving data dictionary: {e}", exc_info=True)
        logger.error(f"Query parameters: report_name={report_name}, schedule_name={schedule_name}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data dictionary: {str(e)}"
        )


@router.get("/reports", response_model=List[str])
@require_permission("planning", "execute")
async def get_available_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of available report names from data dictionary"""
    
    try:
        query = select(RegulatoryDataDictionary.report_name).filter(
            RegulatoryDataDictionary.is_active == True
        ).distinct().order_by(RegulatoryDataDictionary.report_name)
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return [report for report in reports if report]
        
    except Exception as e:
        logger.error(f"Error retrieving available reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available reports"
        )


@router.get("/schedules", response_model=List[str])
@require_permission("planning", "execute")
async def get_available_schedules(
    report_name: Optional[str] = Query(None, description="Filter by report name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of available schedule names from data dictionary"""
    
    try:
        query = select(RegulatoryDataDictionary.schedule_name).filter(
            RegulatoryDataDictionary.is_active == True
        )
        
        if report_name:
            query = query.filter(RegulatoryDataDictionary.report_name == report_name)
        
        query = query.distinct().order_by(RegulatoryDataDictionary.schedule_name)
        result = await db.execute(query)
        schedules = result.scalars().all()
        
        return [schedule for schedule in schedules if schedule]
        
    except Exception as e:
        logger.error(f"Error retrieving available schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available schedules"
        )


@router.post("/import", response_model=DataDictionaryImportResponse)
@require_permission("planning", "create")
async def import_data_dictionary_entries(
    import_request: DataDictionaryImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import selected data dictionary entries as report attributes"""
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    messages = []
    created_attributes = []
    
    try:
        # Validate cycle and report exist
        from app.models.test_cycle import TestCycle
        from app.models.report import Report
        
        cycle_query = select(TestCycle).filter(TestCycle.cycle_id == import_request.cycle_id)
        cycle_result = await db.execute(cycle_query)
        cycle = cycle_result.scalar_one_or_none()
        if not cycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test cycle {import_request.cycle_id} not found"
            )
        
        report_query = select(Report).filter(Report.report_id == import_request.report_id)
        report_result = await db.execute(report_query)
        report = report_result.scalar_one_or_none()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {import_request.report_id} not found"
            )
        
        # Get selected dictionary entries
        dict_query = select(RegulatoryDataDictionary).filter(
            RegulatoryDataDictionary.dict_id.in_(import_request.selected_dict_ids)
        )
        dict_result = await db.execute(dict_query)
        dict_entries = dict_result.scalars().all()
        
        if not dict_entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No dictionary entries found for the selected IDs"
            )
        
        # Get the planning phase for this cycle/report
        from app.models.workflow import WorkflowPhase
        
        phase_query = select(WorkflowPhase).filter(
            and_(
                WorkflowPhase.cycle_id == import_request.cycle_id,
                WorkflowPhase.report_id == import_request.report_id,
                WorkflowPhase.phase_name == 'Planning'
            )
        )
        phase_result = await db.execute(phase_query)
        planning_phase = phase_result.scalar_one_or_none()
        
        if not planning_phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planning phase not found for cycle {import_request.cycle_id}, report {import_request.report_id}"
            )
        
        # Import each entry
        for dict_entry in dict_entries:
            try:
                # Check if attribute already exists (using phase_id)
                existing_query = select(ReportAttribute).filter(
                    and_(
                        ReportAttribute.phase_id == planning_phase.phase_id,
                        ReportAttribute.attribute_name == dict_entry.line_item_name
                    )
                )
                existing_result = await db.execute(existing_query)
                existing_attr = existing_result.scalar_one_or_none()
                
                if existing_attr:
                    messages.append(f"Skipped '{dict_entry.line_item_name}': Already exists")
                    skipped_count += 1
                    continue
                
                # Map mandatory_or_optional to enum value
                mandatory_flag = 'Optional'  # Default
                if dict_entry.mandatory_or_optional:
                    if dict_entry.mandatory_or_optional.lower() in ['mandatory', 'required']:
                        mandatory_flag = 'Mandatory'
                    elif dict_entry.mandatory_or_optional.lower() == 'conditional':
                        mandatory_flag = 'Conditional'
                
                # Determine data type from format
                data_type = 'String'  # Default to String if we can't determine
                if dict_entry.format_specification:
                    format_spec = dict_entry.format_specification.lower()
                    if 'date' in format_spec or 'yyyymmdd' in format_spec:
                        data_type = 'Date'
                    elif 'character' in format_spec or 'text' in format_spec or 'c' in format_spec:
                        data_type = 'String'
                    elif 'number' in format_spec or 'numeric' in format_spec or 'whole' in format_spec or 'n' in format_spec:
                        if 'decimal' in format_spec or '.' in format_spec:
                            data_type = 'Decimal'
                        else:
                            data_type = 'Integer'
                
                # Create new report attribute with phase_id
                new_attribute = ReportAttribute(
                    phase_id=planning_phase.phase_id,  # Use phase_id instead of cycle_id/report_id
                    attribute_name=dict_entry.line_item_name,
                    description=dict_entry.description,
                    data_type=data_type,
                    mandatory_flag=mandatory_flag,  # This is now an enum value
                    cde_flag=False,  # User can set this manually
                    historical_issues_flag=False,  # User can set this manually
                    is_scoped=False,
                    llm_generated=False,  # These are regulatory standard, not LLM generated
                    version_created_by=current_user.user_id,
                    
                    # Data dictionary import fields
                    line_item_number=dict_entry.line_item_number,
                    technical_line_item_name=dict_entry.technical_line_item_name,
                    mdrm=dict_entry.mdrm,
                    
                    # Store additional regulatory information
                    validation_rules=dict_entry.format_specification,
                    testing_approach=f"Regulatory requirement from {dict_entry.report_name} - {dict_entry.schedule_name}",
                    llm_rationale=f"MDRM: {dict_entry.mdrm}, Static/Dynamic: {dict_entry.static_or_dynamic}"
                )
                
                db.add(new_attribute)
                await db.flush()  # Get the ID
                
                created_attributes.append(new_attribute.id)
                imported_count += 1
                
                messages.append(f"Imported '{dict_entry.line_item_name}' successfully")
                
            except Exception as e:
                logger.error(f"Error importing dictionary entry {dict_entry.dict_id}: {e}", exc_info=True)
                messages.append(f"Error importing '{dict_entry.line_item_name}': {str(e)}")
                error_count += 1
                continue
        
        # Commit the transaction
        await db.commit()
        
        # Create a draft version if attributes were imported and no version exists
        if imported_count > 0:
            # Check if any version already exists for this planning phase
            from app.models.planning import PlanningVersion, VersionStatus
            import uuid
            from datetime import datetime
            
            existing_version_query = select(PlanningVersion).filter(
                PlanningVersion.phase_id == planning_phase.phase_id
            )
            existing_version_result = await db.execute(existing_version_query)
            existing_version = existing_version_result.scalar_one_or_none()
            
            if not existing_version:
                # Create initial draft version
                logger.info(f"Creating initial draft version for planning phase {planning_phase.phase_id}")
                
                # Get attribute counts for the version
                attr_count_query = select(func.count(ReportAttribute.id)).filter(
                    ReportAttribute.phase_id == planning_phase.phase_id
                )
                total_attributes = await db.scalar(attr_count_query)
                
                new_version = PlanningVersion(
                    version_id=uuid.uuid4(),
                    phase_id=planning_phase.phase_id,
                    version_number=1,
                    version_status=VersionStatus.DRAFT,
                    total_attributes=total_attributes or 0,
                    approved_attributes=0,
                    pk_attributes=0,
                    cde_attributes=0,
                    mandatory_attributes=0,
                    created_by_id=current_user.user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(new_version)
                await db.commit()
                
                logger.info(f"Created draft version {new_version.version_id} for planning phase")
                messages.append(f"Created draft version 1 for planning phase")
        
        success = error_count == 0
        
        return DataDictionaryImportResponse(
            success=success,
            imported_count=imported_count,
            skipped_count=skipped_count,
            error_count=error_count,
            messages=messages,
            created_attributes=created_attributes
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error during data dictionary import: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import data dictionary entries: {str(e)}"
        )


@router.post("/reload")
@require_permission("planning", "create")
async def reload_data_dictionary(
    clear_existing: bool = Query(False, description="Clear existing entries before reloading"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reload the data dictionary from the source file"""
    
    try:
        logger.info(f"User {current_user.user_id} requested data dictionary reload (clear_existing={clear_existing})")
        
        # Pass the session to the loader function
        stats = await load_fr_y14m_data_dictionary(clear_existing=clear_existing, session=db)
        
        return {
            "success": True,
            "message": "Data dictionary reloaded successfully",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error reloading data dictionary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload data dictionary: {str(e)}"
        )


@router.get("/stats")
@require_permission("planning", "execute")
async def get_data_dictionary_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about the data dictionary"""
    
    try:
        # Total entries
        total_query = select(func.count()).select_from(RegulatoryDataDictionary).filter(
            RegulatoryDataDictionary.is_active == True
        )
        total_result = await db.execute(total_query)
        total_entries = total_result.scalar()
        
        # Total reports
        reports_query = select(func.count(func.distinct(RegulatoryDataDictionary.report_name))).filter(
            RegulatoryDataDictionary.is_active == True
        )
        reports_result = await db.execute(reports_query)
        total_reports = reports_result.scalar()
        
        # Total schedules
        schedules_query = select(func.count(func.distinct(RegulatoryDataDictionary.schedule_name))).filter(
            RegulatoryDataDictionary.is_active == True
        )
        schedules_result = await db.execute(schedules_query)
        total_schedules = schedules_result.scalar()
        
        # Mandatory count
        mandatory_query = select(func.count()).select_from(RegulatoryDataDictionary).filter(
            and_(
                RegulatoryDataDictionary.is_active == True,
                RegulatoryDataDictionary.mandatory_or_optional == 'Mandatory'
            )
        )
        mandatory_result = await db.execute(mandatory_query)
        mandatory_count = mandatory_result.scalar()
        
        return {
            "total_entries": total_entries,
            "total_reports": total_reports,
            "total_schedules": total_schedules,
            "mandatory_count": mandatory_count,
            "optional_count": total_entries - mandatory_count
        }
        
    except Exception as e:
        logger.error(f"Error getting data dictionary stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data dictionary statistics"
        ) 