"""
RFI Data Source Management API endpoints
Handles data source creation, configuration, and query validation for Data Owners
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text, update
from datetime import datetime
import json
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.cycle_report_data_source import CycleReportDataSource
from app.models.universal_assignment import UniversalAssignment
from app.models.request_info import CycleReportTestCase
from app.schemas.rfi import (
    DataSourceCreateRequest,
    DataSourceResponse,
    DataSourceUpdateRequest,
    QueryValidationRequest,
    QueryValidationResponse,
    TestCaseQueryUpdate,
    DataSourceType
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/assignments/{assignment_id}/data-source", response_model=DataSourceResponse)
async def create_data_source_for_assignment(
    assignment_id: str,
    request_body: DataSourceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a data source configuration for an RFI assignment"""
    try:
        # Verify the assignment exists and belongs to the current user
        assignment = await db.execute(
            select(UniversalAssignment).where(
                and_(
                    UniversalAssignment.assignment_id == assignment_id,
                    UniversalAssignment.to_user_id == current_user.user_id,
                    UniversalAssignment.assignment_type == 'LOB Assignment',
                    UniversalAssignment.to_role == 'Data Owner'
                )
            )
        )
        assignment = assignment.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not authorized"
            )
        
        # Get the RFI phase ID from context
        context_data = assignment.context_data or {}
        phase_id = context_data.get('phase_id')
        
        if not phase_id:
            # Get RFI phase if not in context
            phase_query = await db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == context_data.get('cycle_id'),
                        WorkflowPhase.report_id == context_data.get('report_id'),
                        WorkflowPhase.phase_name == 'Request Info'
                    )
                )
            )
            phase = phase_query.scalar_one_or_none()
            if phase:
                phase_id = phase.phase_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RFI phase not found"
                )
        
        # Create the data source
        data_source = CycleReportDataSource(
            phase_id=phase_id,
            name=request_body.name,
            description=request_body.description,
            source_type=request_body.source_type,
            connection_config=request_body.connection_config.dict(),
            auth_config=request_body.auth_config.dict() if request_body.auth_config else None,
            is_active=True,
            created_by_id=current_user.user_id,
            updated_by_id=current_user.user_id
        )
        
        db.add(data_source)
        await db.flush()
        
        # Update assignment context with data source ID
        updated_context = assignment.context_data.copy()
        updated_context['data_source_id'] = data_source.id
        
        await db.execute(
            update(UniversalAssignment)
            .where(UniversalAssignment.assignment_id == assignment_id)
            .values(
                context_data=updated_context,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        # Convert enum to string value for response
        source_type_value = data_source.source_type
        if hasattr(source_type_value, 'value'):
            source_type_value = source_type_value.value
        # The database stores uppercase values
        source_type_value = source_type_value.upper() if isinstance(source_type_value, str) else source_type_value
        
        return DataSourceResponse(
            id=data_source.id,
            name=data_source.name,
            description=data_source.description,
            source_type=source_type_value,
            connection_config=data_source.connection_config,
            is_active=data_source.is_active,
            created_at=data_source.created_at,
            updated_at=data_source.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data source: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data source: {str(e)}"
        )


@router.get("/assignments/{assignment_id}/data-source", response_model=Optional[DataSourceResponse])
async def get_data_source_for_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the data source configuration for an assignment"""
    try:
        # Verify assignment and get data source ID
        assignment = await db.execute(
            select(UniversalAssignment).where(
                and_(
                    UniversalAssignment.assignment_id == assignment_id,
                    UniversalAssignment.to_user_id == current_user.user_id
                )
            )
        )
        assignment = assignment.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found or not authorized"
            )
        
        data_source_id = assignment.context_data.get('data_source_id') if assignment.context_data else None
        
        if not data_source_id:
            return None
        
        # Get the data source
        data_source = await db.execute(
            select(CycleReportDataSource).where(
                CycleReportDataSource.id == data_source_id
            )
        )
        data_source = data_source.scalar_one_or_none()
        
        if not data_source:
            return None
        
        # Convert enum to string value for response
        source_type_value = data_source.source_type
        if hasattr(source_type_value, 'value'):
            source_type_value = source_type_value.value
        # The database stores uppercase values
        source_type_value = source_type_value.upper() if isinstance(source_type_value, str) else source_type_value
        
        return DataSourceResponse(
            id=data_source.id,
            name=data_source.name,
            description=data_source.description,
            source_type=source_type_value,
            connection_config=data_source.connection_config,
            is_active=data_source.is_active,
            created_at=data_source.created_at,
            updated_at=data_source.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data source: {str(e)}"
        )


@router.put("/data-sources/{data_source_id}", response_model=DataSourceResponse)
async def update_data_source(
    data_source_id: int,
    request_body: DataSourceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a data source configuration"""
    try:
        # Get and verify data source ownership
        data_source = await db.execute(
            select(CycleReportDataSource).where(
                and_(
                    CycleReportDataSource.id == data_source_id,
                    CycleReportDataSource.created_by_id == current_user.user_id
                )
            )
        )
        data_source = data_source.scalar_one_or_none()
        
        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found or not authorized"
            )
        
        # Update fields
        if request_body.name is not None:
            data_source.name = request_body.name
        if request_body.description is not None:
            data_source.description = request_body.description
        if request_body.connection_config is not None:
            data_source.connection_config = request_body.connection_config.dict()
        if request_body.auth_config is not None:
            data_source.auth_config = request_body.auth_config.dict()
        if request_body.is_active is not None:
            data_source.is_active = request_body.is_active
        
        data_source.updated_at = datetime.utcnow()
        data_source.updated_by_id = current_user.user_id
        
        await db.commit()
        
        # Convert enum to string value for response
        source_type_value = data_source.source_type
        if hasattr(source_type_value, 'value'):
            source_type_value = source_type_value.value
        # The database stores uppercase values
        source_type_value = source_type_value.upper() if isinstance(source_type_value, str) else source_type_value
        
        return DataSourceResponse(
            id=data_source.id,
            name=data_source.name,
            description=data_source.description,
            source_type=source_type_value,
            connection_config=data_source.connection_config,
            is_active=data_source.is_active,
            created_at=data_source.created_at,
            updated_at=data_source.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating data source: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update data source: {str(e)}"
        )


@router.post("/data-sources/{data_source_id}/validate-query", response_model=QueryValidationResponse)
async def validate_query(
    data_source_id: int,
    request_body: QueryValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a SQL query against the data source"""
    try:
        # Get data source
        data_source = await db.execute(
            select(CycleReportDataSource).where(
                CycleReportDataSource.id == data_source_id
            )
        )
        data_source = data_source.scalar_one_or_none()
        
        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found"
            )
        
        # For now, we'll validate against the same database
        # In production, this would connect to the actual data source
        source_type_str = str(data_source.source_type)
        if hasattr(data_source.source_type, 'value'):
            source_type_str = data_source.source_type.value
        
        if source_type_str.upper() == "POSTGRESQL":
            try:
                # Execute query with LIMIT 1 to test
                test_query = f"SELECT * FROM ({request_body.query}) AS test_query LIMIT 1"
                result = await db.execute(text(test_query))
                row = result.first()
                
                # Get column names
                columns = list(result.keys())
                
                # Check if required columns exist
                missing_columns = []
                if request_body.required_columns:
                    for col in request_body.required_columns:
                        if col.lower() not in [c.lower() for c in columns]:
                            missing_columns.append(col)
                
                if missing_columns:
                    return QueryValidationResponse(
                        is_valid=False,
                        error=f"Missing required columns: {', '.join(missing_columns)}",
                        columns=columns,
                        sample_data=None
                    )
                
                # Get sample data if requested
                sample_data = None
                if request_body.return_sample and row:
                    sample_data = dict(row._mapping)
                    # Convert any non-serializable values
                    for key, value in sample_data.items():
                        if isinstance(value, datetime):
                            sample_data[key] = value.isoformat()
                
                return QueryValidationResponse(
                    is_valid=True,
                    error=None,
                    columns=columns,
                    sample_data=sample_data
                )
                
            except Exception as e:
                return QueryValidationResponse(
                    is_valid=False,
                    error=f"Query execution failed: {str(e)}",
                    columns=[],
                    sample_data=None
                )
        else:
            return QueryValidationResponse(
                is_valid=False,
                error=f"Validation not implemented for {data_source.source_type}",
                columns=[],
                sample_data=None
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate query: {str(e)}"
        )


@router.post("/test-cases/update-queries", response_model=Dict[str, Any])
async def update_test_case_queries(
    request_body: TestCaseQueryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update queries for multiple test cases"""
    try:
        updated_count = 0
        errors = []
        
        for update in request_body.updates:
            try:
                # Get test case - convert string ID to integer
                test_case_id = int(update.test_case_id)
                test_case = await db.execute(
                    select(CycleReportTestCase).where(
                        CycleReportTestCase.id == test_case_id
                    )
                )
                test_case = test_case.scalar_one_or_none()
                
                if not test_case:
                    errors.append(f"Test case {update.test_case_id} not found")
                    continue
                
                # Update query
                test_case.query_text = update.query_text
                test_case.updated_at = datetime.utcnow()
                
                updated_count += 1
                
            except Exception as e:
                errors.append(f"Error updating test case {update.test_case_id}: {str(e)}")
        
        await db.commit()
        
        return {
            "success": len(errors) == 0,
            "updated_count": updated_count,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Error updating test case queries: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update test case queries: {str(e)}"
        )


@router.get("/phases/{phase_id}/data-sources", response_model=List[DataSourceResponse])
async def get_phase_data_sources(
    phase_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all data sources for a phase"""
    try:
        data_sources = await db.execute(
            select(CycleReportDataSource).where(
                CycleReportDataSource.phase_id == phase_id
            )
        )
        data_sources = data_sources.scalars().all()
        
        result = []
        for ds in data_sources:
            # Convert enum to string value for response
            source_type_value = ds.source_type
            if hasattr(source_type_value, 'value'):
                source_type_value = source_type_value.value
            # The database stores uppercase values
            source_type_value = source_type_value.upper() if isinstance(source_type_value, str) else source_type_value
            
            result.append(DataSourceResponse(
                id=ds.id,
                name=ds.name,
                description=ds.description,
                source_type=source_type_value,
                connection_config=ds.connection_config,
                is_active=ds.is_active,
                created_at=ds.created_at,
                updated_at=ds.updated_at
            ))
        return result
        
    except Exception as e:
        logger.error(f"Error getting phase data sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get phase data sources: {str(e)}"
        )