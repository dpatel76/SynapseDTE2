from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.models.user import User
from app.application.dtos.data_source import (
    DataSourceCreateDTO, DataSourceUpdateDTO, DataSourceDTO,
    DataSourceFilterDTO, DataSourceListDTO, DataSourceTestResultDTO,
    DataSourceStatsDTO
)
from app.application.use_cases.data_source import DataSourceUseCase

router = APIRouter(tags=["Data Sources"])


@router.post("/", response_model=DataSourceDTO, status_code=status.HTTP_201_CREATED)
@require_permission("data_sources", "create")
async def create_data_source(
    data_source_data: DataSourceCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new data source.
    
    Required permission: data_sources.create
    Required roles: Test Executive (Admin)
    """
    return await DataSourceUseCase.create_data_source(data_source_data, current_user, db)


@router.get("/", response_model=DataSourceListDTO)
@require_permission("data_sources", "read")
async def list_data_sources(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in data source name"),
    database_type: Optional[str] = Query(None, description="Filter by database type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List data sources with filtering and pagination.
    
    Required permission: data_sources.read
    """
    filter_dto = DataSourceFilterDTO(
        skip=skip,
        limit=limit,
        search=search,
        database_type=database_type,
        is_active=is_active
    )
    return await DataSourceUseCase.list_data_sources(filter_dto, current_user, db)


@router.get("/{data_source_id}", response_model=DataSourceDTO)
@require_permission("data_sources", "read")
async def get_data_source(
    data_source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data source by ID.
    
    Required permission: data_sources.read
    """
    return await DataSourceUseCase.get_data_source(data_source_id, current_user, db)


@router.put("/{data_source_id}", response_model=DataSourceDTO)
@require_permission("data_sources", "update")
async def update_data_source(
    data_source_id: int,
    data_source_data: DataSourceUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update data source information.
    
    Required permission: data_sources.update
    Required roles: Test Executive (Admin)
    """
    return await DataSourceUseCase.update_data_source(
        data_source_id, data_source_data, current_user, db
    )


@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("data_sources", "delete")
async def delete_data_source(
    data_source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete data source.
    
    Required permission: data_sources.delete
    Required roles: Test Executive (Admin)
    """
    await DataSourceUseCase.delete_data_source(data_source_id, current_user, db)


@router.post("/{data_source_id}/test", response_model=DataSourceTestResultDTO)
@require_permission("data_sources", "execute")
async def test_data_source_connection(
    data_source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test data source connection.
    
    Required permission: data_sources.execute
    Required roles: Test Executive (Admin)
    """
    return await DataSourceUseCase.test_connection(data_source_id, current_user, db)


@router.get("/stats/overview", response_model=DataSourceStatsDTO)
@require_permission("data_sources", "read")
async def get_data_source_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data source statistics overview.
    
    Required permission: data_sources.read
    Required roles: Test Executive (Admin)
    
    Returns:
    - Total number of data sources
    - Active vs inactive counts
    - Breakdown by database type
    - Recent connection test results
    """
    return await DataSourceUseCase.get_stats(current_user, db)