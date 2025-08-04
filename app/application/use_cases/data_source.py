from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.data_source import DataSource
from app.services.data_source_service import DataSourceService
from app.core.exceptions import ValidationException, NotFoundException
from app.core.logging import audit_logger
from app.application.dtos.data_source import (
    DataSourceCreateDTO, DataSourceUpdateDTO, DataSourceDTO,
    DataSourceFilterDTO, DataSourceListDTO, DataSourceTestResultDTO,
    DataSourceStatsDTO
)


class DataSourceUseCase:
    """Use cases for data source management"""
    
    @staticmethod
    async def create_data_source(
        data_dto: DataSourceCreateDTO,
        current_user: User,
        db: AsyncSession
    ) -> DataSourceDTO:
        """Create a new data source"""
        # Check if data source name already exists
        existing_result = await db.execute(
            select(DataSource).where(DataSource.data_source_name == data_dto.data_source_name)
        )
        if existing_result.scalar_one_or_none():
            raise ValidationException("Data source name already exists")
        
        # Create data source using service
        service = DataSourceService(db)
        data_source = await service.create_data_source(data_dto)
        
        # Log creation
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="data_source_created",
            resource_type="data_source",
            resource_id=data_source.data_source_id,
            details={"data_source_name": data_source.data_source_name}
        )
        
        return DataSourceDTO.model_validate(data_source)
    
    @staticmethod
    async def list_data_sources(
        filter_dto: DataSourceFilterDTO,
        current_user: User,
        db: AsyncSession
    ) -> DataSourceListDTO:
        """List data sources with filtering and pagination"""
        service = DataSourceService(db)
        data_sources, total = await service.list_data_sources(
            skip=filter_dto.skip,
            limit=filter_dto.limit,
            search=filter_dto.search,
            database_type=filter_dto.database_type,
            is_active=filter_dto.is_active
        )
        
        return DataSourceListDTO(
            data_sources=[DataSourceDTO.model_validate(ds) for ds in data_sources],
            total=total,
            skip=filter_dto.skip,
            limit=filter_dto.limit
        )
    
    @staticmethod
    async def get_data_source(
        data_source_id: int,
        current_user: User,
        db: AsyncSession
    ) -> DataSourceDTO:
        """Get data source by ID"""
        service = DataSourceService(db)
        data_source = await service.get_data_source(data_source_id)
        
        if not data_source:
            raise NotFoundException(f"Data source with ID {data_source_id} not found")
        
        return DataSourceDTO.model_validate(data_source)
    
    @staticmethod
    async def update_data_source(
        data_source_id: int,
        data_dto: DataSourceUpdateDTO,
        current_user: User,
        db: AsyncSession
    ) -> DataSourceDTO:
        """Update data source information"""
        service = DataSourceService(db)
        data_source = await service.update_data_source(data_source_id, data_dto)
        
        # Log update
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="data_source_updated",
            resource_type="data_source",
            resource_id=data_source.data_source_id,
            details={"data_source_name": data_source.data_source_name}
        )
        
        return DataSourceDTO.model_validate(data_source)
    
    @staticmethod
    async def delete_data_source(
        data_source_id: int,
        current_user: User,
        db: AsyncSession
    ) -> None:
        """Delete data source"""
        service = DataSourceService(db)
        await service.delete_data_source(data_source_id)
        
        # Log deletion
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="data_source_deleted",
            resource_type="data_source",
            resource_id=data_source_id,
            details={}
        )
    
    @staticmethod
    async def test_connection(
        data_source_id: int,
        current_user: User,
        db: AsyncSession
    ) -> DataSourceTestResultDTO:
        """Test data source connection"""
        service = DataSourceService(db)
        result = await service.test_connection(data_source_id)
        
        # Log test
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="data_source_tested",
            resource_type="data_source",
            resource_id=data_source_id,
            details={"success": result.success}
        )
        
        return DataSourceTestResultDTO(
            success=result.success,
            message=result.message,
            connection_time_ms=result.connection_time_ms,
            error_details=result.error_details
        )
    
    @staticmethod
    async def get_stats(
        current_user: User,
        db: AsyncSession
    ) -> DataSourceStatsDTO:
        """Get data source statistics overview"""
        service = DataSourceService(db)
        stats = await service.get_stats()
        
        return DataSourceStatsDTO(
            total_data_sources=stats.get("total_data_sources", 0),
            active_data_sources=stats.get("active_data_sources", 0),
            inactive_data_sources=stats.get("inactive_data_sources", 0),
            sources_by_type=stats.get("sources_by_type", {}),
            recent_connection_tests=stats.get("recent_connection_tests", [])
        )